"""The folder watcher (app/folders/watcher.py): an edit in an added folder triggers a rescan once the
changes settle. The timing and filtering tests use a fake observer and short timers; the last tests use
the real watchdog observer on a temporary folder."""
import threading
import time
from types import SimpleNamespace

import pytest
from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileOpenedEvent,
)

from app import config, db
from app.auth.security import STARTUP_TOKEN
from app.folders import scanner, watcher
from app.folders.watcher import FolderWatcher


class FakeObserver:
    def __init__(self):
        self.scheduled = []
        self.unscheduled = []
        self.started = False
        self.stopped = False

    def schedule(self, handler, path, recursive=False):
        watch = SimpleNamespace(path=path)
        self.scheduled.append((handler, path, recursive, watch))
        return watch

    def unschedule(self, watch):
        self.unscheduled.append(watch)

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def join(self, timeout=None):
        pass


def wait_until(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


@pytest.fixture(autouse=True)
def fast_timers(monkeypatch):
    monkeypatch.setattr(config, "WATCH_DEBOUNCE_SECONDS", 0.05)
    monkeypatch.setattr(config, "WATCH_MAX_WAIT_SECONDS", 0.6)
    monkeypatch.setattr(config, "WATCH_SCAN_ON_START", False)


def add_folder_row(folder_id="f1", path="C:/docs"):
    with db.session() as conn:
        conn.execute("INSERT INTO folders (folder_id, path, added_at) VALUES (?, ?, '2026-01-01T00:00:00+00:00')",
                     (folder_id, path))


def make_watcher(scan=None):
    scans = []

    def default_scan(folder_id, path):
        scans.append((folder_id, path))
        return {"added": 0}

    watcher_ = FolderWatcher(scan=scan or default_scan, observer_factory=FakeObserver)
    return watcher_, scans


def handler_of(watcher_, index=0):
    return watcher_._observer.scheduled[index][0]


@pytest.fixture
def running(isolated_store):
    """A started watcher over one folder 'f1', plus its recorded scans. Stopped afterwards."""
    add_folder_row()
    watcher_, scans = make_watcher()
    watcher_.start()
    yield watcher_, scans
    watcher_.stop()


# --- what it watches ------------------------------------------------------------------------


def test_start_watches_every_added_folder_recursively(isolated_store):
    add_folder_row("f1", "C:/docs")
    add_folder_row("f2", "C:/notes")
    watcher_, _ = make_watcher()
    watcher_.start()
    watcher_.start()  # starting twice does not watch twice
    observer = watcher_._observer
    assert observer.started
    assert sorted((path, recursive) for _, path, recursive, _ in observer.scheduled) == [
        ("C:/docs", True), ("C:/notes", True)]
    watcher_.stop()


def test_watching_before_start_does_nothing(isolated_store):
    watcher_, _ = make_watcher()
    watcher_.watch("f1", "C:/docs")  # must not raise
    assert watcher_._watches == {}


def test_a_folder_that_cannot_be_watched_is_skipped_not_fatal(isolated_store):
    class Failing(FakeObserver):
        def schedule(self, handler, path, recursive=False):
            raise FileNotFoundError(path)

    add_folder_row()
    watcher_ = FolderWatcher(scan=lambda *a: {}, observer_factory=Failing)
    watcher_.start()  # must not raise
    assert watcher_._watches == {}
    watcher_.stop()


# --- when it rescans ------------------------------------------------------------------------


def test_an_edit_rescans_the_folder_once_it_has_settled(running):
    watcher_, scans = running
    handler_of(watcher_).on_any_event(FileModifiedEvent("C:/docs/plan.docx"))
    assert scans == []  # not immediately: it waits for the changes to settle
    assert wait_until(lambda: scans == [("f1", "C:/docs")])


def test_a_burst_of_changes_causes_one_rescan(running):
    watcher_, scans = running
    handler = handler_of(watcher_)
    for _ in range(10):
        handler.on_any_event(FileModifiedEvent("C:/docs/plan.docx"))
        time.sleep(0.01)
    assert wait_until(lambda: len(scans) >= 1)
    time.sleep(0.3)
    assert len(scans) == 1


def test_a_folder_that_never_goes_quiet_is_still_rescanned(running, monkeypatch):
    monkeypatch.setattr(config, "WATCH_DEBOUNCE_SECONDS", 0.3)
    monkeypatch.setattr(config, "WATCH_MAX_WAIT_SECONDS", 0.5)
    watcher_, scans = running
    handler = handler_of(watcher_)
    stop_at = time.monotonic() + 1.5
    first_scan_at = None
    while time.monotonic() < stop_at:
        handler.on_any_event(FileModifiedEvent("C:/docs/big.pdf"))  # keeps restarting the debounce
        if scans and first_scan_at is None:
            first_scan_at = time.monotonic()
        time.sleep(0.05)
    assert scans, "the max wait never forced a rescan while changes kept arriving"


@pytest.mark.parametrize("event", [
    FileCreatedEvent("C:/docs/new.txt"),
    FileDeletedEvent("C:/docs/gone.pptx"),
    FileMovedEvent("C:/docs/old.docx", "C:/docs/renamed.docx"),
    FileMovedEvent("C:/docs/~draft.tmp", "C:/docs/final.docx"),  # an editor's save: temp file renamed into place
    DirCreatedEvent("C:/docs/sub"),
    DirDeletedEvent("C:/docs/sub"),
])
def test_creating_deleting_and_moving_files_or_folders_rescans(running, event):
    watcher_, scans = running
    handler_of(watcher_).on_any_event(event)
    assert wait_until(lambda: len(scans) == 1)


@pytest.mark.parametrize("event", [
    FileModifiedEvent("C:/docs/picture.png"),          # a type HiveMind does not read
    FileModifiedEvent("C:/docs/~$plan.docx"),          # Word's lock file
    FileModifiedEvent("C:/docs/plan.docx.tmp"),
    FileCreatedEvent("C:/docs/download.pdf.part"),
    FileModifiedEvent("C:/docs/.~lock.plan.docx#"),
    DirModifiedEvent("C:/docs"),                       # fires for every file inside: the file event is what counts
    FileOpenedEvent("C:/docs/plan.docx"),              # reading a file is not a change
    FileMovedEvent("C:/docs/a.png", "C:/docs/b.png"),
])
def test_irrelevant_changes_never_cause_a_rescan(running, event):
    watcher_, scans = running
    handler_of(watcher_).on_any_event(event)
    time.sleep(0.3)
    assert scans == []


# --- keeping going --------------------------------------------------------------------------


def test_a_failed_rescan_is_logged_and_the_next_change_still_works(isolated_store, caplog):
    calls = []

    def flaky(folder_id, path):
        calls.append(path)
        if len(calls) == 1:
            raise RuntimeError("SECRET-FILENAME.docx exploded")
        return {}

    add_folder_row()
    watcher_, _ = make_watcher(scan=flaky)
    watcher_.start()
    handler = handler_of(watcher_)
    with caplog.at_level("WARNING", logger="app.folders.watcher"):
        handler.on_any_event(FileModifiedEvent("C:/docs/a.txt"))
        assert wait_until(lambda: len(calls) == 1)
        handler.on_any_event(FileModifiedEvent("C:/docs/a.txt"))
        assert wait_until(lambda: len(calls) == 2)
    assert "rescan after a change failed" in caplog.text and "RuntimeError" in caplog.text
    assert "SECRET-FILENAME" not in caplog.text  # only the error type, never its message or file names
    watcher_.stop()


def test_a_folder_removed_while_a_change_waits_is_not_scanned_and_is_unwatched(running):
    watcher_, scans = running
    handler_of(watcher_).on_any_event(FileModifiedEvent("C:/docs/a.txt"))
    with db.session() as conn:
        conn.execute("DELETE FROM folders WHERE folder_id = 'f1'")
    time.sleep(0.4)
    assert scans == []
    assert watcher_._observer.unscheduled  # the watch was dropped


def test_unwatch_cancels_a_pending_rescan(running):
    watcher_, scans = running
    handler_of(watcher_).on_any_event(FileModifiedEvent("C:/docs/a.txt"))
    watcher_.unwatch("f1")
    time.sleep(0.3)
    assert scans == [] and watcher_._pending == {}


def test_a_folder_added_after_start_is_watched(running):
    watcher_, scans = running
    add_folder_row("f2", "C:/more")
    watcher_.watch("f2", "C:/more")
    watcher_.watch("f2", "C:/more")  # twice is fine
    assert [p for _, p, _, _ in watcher_._observer.scheduled] == ["C:/docs", "C:/more"]
    handler_of(watcher_, 1).on_any_event(FileCreatedEvent("C:/more/new.txt"))
    assert wait_until(lambda: scans == [("f2", "C:/more")])


def test_stop_cancels_pending_rescans_and_stops_the_observer(isolated_store):
    add_folder_row()
    watcher_, scans = make_watcher()
    watcher_.start()
    observer = watcher_._observer
    handler = handler_of(watcher_)
    handler.on_any_event(FileModifiedEvent("C:/docs/a.txt"))
    watcher_.stop()
    handler.on_any_event(FileModifiedEvent("C:/docs/a.txt"))  # a late event after stop
    time.sleep(0.3)
    assert scans == [] and observer.stopped


def test_on_start_every_folder_is_rescanned_once_to_catch_up_when_enabled(isolated_store, monkeypatch):
    monkeypatch.setattr(config, "WATCH_SCAN_ON_START", True)
    add_folder_row("f1", "C:/docs")
    add_folder_row("f2", "C:/notes")
    watcher_, scans = make_watcher()
    watcher_.start()
    assert wait_until(lambda: sorted(scans) == [("f1", "C:/docs"), ("f2", "C:/notes")])
    watcher_.stop()


def test_there_is_no_catch_up_scan_when_it_is_switched_off(isolated_store):
    add_folder_row()
    watcher_, scans = make_watcher()
    watcher_.start()
    time.sleep(0.3)
    assert scans == []
    watcher_.stop()


# --- one scan of a folder at a time --------------------------------------------------------------


def test_scans_of_one_folder_never_overlap_but_different_folders_can(monkeypatch):
    active = {"now": 0, "max": 0}
    guard = threading.Lock()

    def slow_scan(folder_id, path):
        with guard:
            active["now"] += 1
            active["max"] = max(active["max"], active["now"])
        time.sleep(0.15)
        with guard:
            active["now"] -= 1
        return {}

    monkeypatch.setattr(scanner, "_scan_files", slow_scan)
    threads = [threading.Thread(target=scanner.scan_folder, args=("same", "p")) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert active["max"] == 1

    active["max"] = 0
    threads = [threading.Thread(target=scanner.scan_folder, args=(f"folder-{i}", "p")) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert active["max"] == 2


# --- wiring ---------------------------------------------------------------------------------------


@pytest.fixture
def api(isolated_store, client):
    client.headers.update({"X-HiveMind-Token": STARTUP_TOKEN})
    return client


def test_adding_and_removing_a_folder_starts_and_stops_watching_it(api, tmp_path, monkeypatch):
    watched, unwatched = [], []
    monkeypatch.setattr("app.api.routes_folders.watcher.watch_folder", lambda fid, path: watched.append((fid, path)))
    monkeypatch.setattr("app.api.routes_folders.watcher.unwatch_folder", lambda fid: unwatched.append(fid))
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("alpha")
    folder_id = api.post("/folders", json={"path": str(folder)}).json()["folder_id"]
    assert wait_until(lambda: watched == [(folder_id, str(folder))])  # the watch starts after the background scan
    assert watched == [(folder_id, str(folder))]
    assert api.delete(f"/folders/{folder_id}").status_code == 200
    assert unwatched == [folder_id]
    assert api.delete("/folders/missing").status_code == 404 and unwatched == [folder_id]  # no stray unwatch


def test_the_module_level_helpers_are_safe_before_the_watcher_starts():
    watcher.watch_folder("f1", "C:/docs")
    watcher.unwatch_folder("f1")
    watcher.stop()  # nothing running: must not raise


# --- the real observer, end to end ----------------------------------------------------------------


def test_a_real_edit_in_a_watched_folder_is_rescanned(isolated_store, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WATCH_DEBOUNCE_SECONDS", 0.4)
    folder = tmp_path / "docs"
    folder.mkdir()
    target = folder / "plan.txt"
    target.write_text("the budget is 100")
    folder_id = scanner.add_folder(str(folder))
    with db.session() as conn:
        before = conn.execute("SELECT file_id, content_hash FROM files").fetchone()
    real = FolderWatcher()  # the real scan_folder and the real watchdog observer
    real.start()
    try:
        target.write_text("the budget is 250, revised after the review")
        assert wait_until(
            lambda: _hash_of(before["file_id"]) not in (None, before["content_hash"]), timeout=30
        ), "the edited file was not re-indexed by the watcher"
        # And a brand new file in the folder is picked up too.
        (folder / "extra.txt").write_text("a new file")
        assert wait_until(lambda: _file_count() == 2, timeout=30)
        # And a deleted one is dropped.
        target.unlink()
        assert wait_until(lambda: _file_count() == 1, timeout=30)
    finally:
        real.stop()
    assert folder_id


def _hash_of(file_id):
    with db.session() as conn:
        row = conn.execute("SELECT content_hash FROM files WHERE file_id = ?", (file_id,)).fetchone()
    return row["content_hash"] if row else None


def _file_count():
    with db.session() as conn:
        return conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
