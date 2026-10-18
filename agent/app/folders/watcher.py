"""Watches the added folders for edits (watchdog) and rescans a folder once its changes settle, so
an edited, new, moved or deleted file is picked up without anyone pressing Rescan. A rescan is the
same `scan_folder` that `POST /folders/{id}/rescan` runs: it re-indexes only changed files, queues the publish
re-sync for a public file, and unpublishes one that was deleted.

Editors rarely write a file in one step (a temp file, then a rename, then a touch), so a change only
starts a short timer, and further changes in the same folder restart it (WATCH_DEBOUNCE_SECONDS). A
folder that never goes quiet, such as a long copy, is still rescanned every WATCH_MAX_WAIT_SECONDS.
Only the file types HiveMind reads count, and Office/editor temp files are ignored. Nothing but the
folder id and counts is logged, never file names or content.
"""
import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app import config
from app.db import session
from app.folders import scanner

log = logging.getLogger(__name__)

_CHANGES = {"created", "modified", "deleted", "moved"}
_DIRECTORY_CHANGES = {"created", "deleted", "moved"}  # a folder "modified" fires for every file inside it
_TEMP_PREFIXES = ("~$", ".~lock")
_TEMP_SUFFIXES = (".tmp", ".temp", ".crdownload", ".part")


def _relevant_path(path: str) -> bool:
    """A file HiveMind reads, and not an editor's temporary file."""
    name = Path(path).name
    if name.startswith(_TEMP_PREFIXES) or name.lower().endswith(_TEMP_SUFFIXES):
        return False
    return Path(path).suffix.lower() in config.SUPPORTED_EXTENSIONS


class _Handler(FileSystemEventHandler):
    def __init__(self, on_change):
        self._on_change = on_change

    def on_any_event(self, event):
        if event.event_type not in _CHANGES:
            return
        if event.is_directory:
            if event.event_type in _DIRECTORY_CHANGES:
                self._on_change()  # files may have come, gone or moved with the folder
            return
        paths = [event.src_path]
        if getattr(event, "dest_path", ""):
            paths.append(event.dest_path)
        if any(_relevant_path(p) for p in paths):
            self._on_change()


class FolderWatcher:
    def __init__(self, scan=None, observer_factory=Observer):
        self._scan = scan or scanner.scan_folder
        self._observer_factory = observer_factory
        self._observer = None
        self._watches = {}  # folder_id -> the observer's watch handle
        self._pending = {}  # folder_id -> (timer, when the first unscanned change arrived)
        self._lock = threading.Lock()
        self._stopping = threading.Event()

    def start(self) -> None:
        """Watches every folder already added, and (optionally) rescans each once in the background to
        catch edits made while the agent was not running."""
        if self._observer is not None:
            return
        self._stopping.clear()
        self._observer = self._observer_factory()
        self._observer.start()
        with session() as conn:
            folders = [(r["folder_id"], r["path"]) for r in conn.execute("SELECT folder_id, path FROM folders")]
        for folder_id, path in folders:
            self.watch(folder_id, path)
        if config.WATCH_SCAN_ON_START and folders:
            threading.Thread(target=self._catch_up, args=([f for f, _ in folders],), daemon=True,
                             name="hivemind-watch-catchup").start()

    def stop(self) -> None:
        self._stopping.set()
        with self._lock:
            for timer, _ in self._pending.values():
                timer.cancel()
            self._pending.clear()
            self._watches.clear()
            observer, self._observer = self._observer, None
        if observer is not None:
            observer.stop()
            observer.join(timeout=5)

    def watch(self, folder_id: str, path: str) -> None:
        """Start watching a folder (and everything under it). No-op if the watcher is not running or
        already watches it; a folder that cannot be watched right now is just skipped."""
        with self._lock:
            if self._observer is None or folder_id in self._watches:
                return
            try:
                handler = _Handler(lambda fid=folder_id: self._changed(fid))
                self._watches[folder_id] = self._observer.schedule(handler, str(path), recursive=True)
            except OSError as exc:
                log.warning("not watching folder %s: %s", folder_id, type(exc).__name__)

    def unwatch(self, folder_id: str) -> None:
        with self._lock:
            pending = self._pending.pop(folder_id, None)
            if pending:
                pending[0].cancel()
            watch = self._watches.pop(folder_id, None)
            observer = self._observer
        if watch is not None and observer is not None:
            try:
                observer.unschedule(watch)
            except (KeyError, OSError):
                pass

    def _changed(self, folder_id: str) -> None:
        now = time.monotonic()
        with self._lock:
            if self._observer is None:
                return
            timer, first = self._pending.get(folder_id, (None, now))
            if timer is not None:
                timer.cancel()
            delay = min(config.WATCH_DEBOUNCE_SECONDS, max(0.0, first + config.WATCH_MAX_WAIT_SECONDS - now))
            timer = threading.Timer(delay, self._fire, args=(folder_id,))
            timer.daemon = True
            self._pending[folder_id] = (timer, first)
            timer.start()

    def _fire(self, folder_id: str) -> None:
        with self._lock:
            self._pending.pop(folder_id, None)
        self._rescan(folder_id)

    def _catch_up(self, folder_ids: list[str]) -> None:
        for folder_id in folder_ids:
            if self._stopping.is_set():
                return
            self._rescan(folder_id)

    def _rescan(self, folder_id: str) -> None:
        with session() as conn:
            row = conn.execute("SELECT path FROM folders WHERE folder_id = ?", (folder_id,)).fetchone()
        if row is None:
            self.unwatch(folder_id)  # removed from HiveMind while the change was waiting
            return
        try:
            stats = self._scan(folder_id, row["path"])
        except Exception as exc:  # noqa: BLE001 - a failed rescan must never take the watcher down
            log.warning("rescan after a change failed for folder %s: %s", folder_id, type(exc).__name__)
            return
        log.info("rescanned folder %s after a change: %s", folder_id, stats)


# The agent runs one watcher, started and stopped with it (app/main.py).
_watcher = FolderWatcher()


def start() -> None:
    _watcher.start()


def stop() -> None:
    _watcher.stop()


def watch_folder(folder_id: str, path: str) -> None:
    _watcher.watch(folder_id, path)


def unwatch_folder(folder_id: str) -> None:
    _watcher.unwatch(folder_id)
