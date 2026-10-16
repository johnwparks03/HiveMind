"""Requester-side file download (docs/stories/BACKLOG.md E4-S4/S5,
API_Contract.md section 2.6). A durable SQLite-backed queue, same shape as the
publish queue (app/central/publish.py): a background asyncio worker polls central
every DOWNLOAD_POLL_SECONDS and streams the file to the download destination
folder once a transfer is ready, so a page refresh (or an agent restart) can
resume showing in-flight transfers instead of losing them.
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app import config, settings
from app.central import client as central_client
from app.db import session as db_session
from app.errors import ApiError
from app.platform_windows import downloads_folder as _real_downloads_folder

_worker_task: asyncio.Task | None = None

_TERMINAL_STATUSES = ("downloaded", "failed", "expired")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(transfer_id: str) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM downloads WHERE transfer_id = ?", (transfer_id,)).fetchone()
    return dict(row) if row else None


def list_downloads() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM downloads ORDER BY requested_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_download(transfer_id: str) -> dict | None:
    return _row(transfer_id)


def request_download(file_id: str, filename: str | None = None) -> dict:
    """POST /transfers centrally (API_Contract.md section 3.5). Central dedupes an
    in-flight transfer for the same (file, requester) pair itself and returns the
    existing one, so a double-click just updates (not duplicates) the local row.
    `filename` isn't part of central's request/response shape (it never stores or
    returns one) - the frontend already has it from the search result that offered
    the download, so it's passed through here purely for local display/save-as.
    """
    body = central_client.request_json("POST", "/transfers", json={"file_id": file_id}) or {}
    transfer_id, status = body["transfer_id"], body["status"]
    now = _now()
    with db_session() as conn:
        existing = conn.execute(
            "SELECT filename FROM downloads WHERE transfer_id = ?", (transfer_id,)
        ).fetchone()
        name = filename or (existing["filename"] if existing else "") or file_id
        conn.execute(
            "INSERT INTO downloads (transfer_id, file_id, filename, status, error_code, saved_path, "
            "requested_at, updated_at) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?) "
            "ON CONFLICT (transfer_id) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at",
            (transfer_id, file_id, name, status, now, now),
        )
    return _row(transfer_id)


def downloads_folder() -> Path:
    """Where downloaded files are saved: a user-chosen folder (PUT
    /settings/download-folder, picked with the same native Windows dialog used to
    add a folder to index) or, by default, the real Windows Downloads folder."""
    custom = settings.get(settings.DOWNLOAD_FOLDER_KEY)
    return Path(custom) if custom else _real_downloads_folder()


def _unique_path(folder: Path, filename: str) -> Path:
    """`" (1)"`/`" (2)"` suffixing on a name collision, never overwriting an
    existing file in Downloads."""
    candidate = folder / filename
    if not candidate.exists():
        return candidate
    stem, suffix = Path(filename).stem, Path(filename).suffix
    n = 1
    while True:
        candidate = folder / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _download_ready_file(transfer_id: str, filename: str, download_url: str) -> None:
    folder = downloads_folder()
    folder.mkdir(parents=True, exist_ok=True)
    dest = _unique_path(folder, filename)
    try:
        with httpx.stream("GET", download_url, timeout=config.CENTRAL_TIMEOUT_SECONDS) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=config.DOWNLOAD_CHUNK_BYTES):
                    f.write(chunk)
    except Exception:  # noqa: BLE001 - any failure here is reported, never crashes the worker
        dest.unlink(missing_ok=True)
        with db_session() as conn:
            conn.execute(
                "UPDATE downloads SET status='failed', error_code='download_failed', updated_at=? "
                "WHERE transfer_id=?", (_now(), transfer_id),
            )
        return
    with db_session() as conn:
        conn.execute(
            "UPDATE downloads SET status='downloaded', saved_path=?, updated_at=? WHERE transfer_id=?",
            (str(dest), _now(), transfer_id),
        )


def _poll_one(row: dict) -> None:
    transfer_id = row["transfer_id"]
    try:
        body = central_client.request_json("GET", f"/transfers/{transfer_id}") or {}
    except ApiError as exc:
        if exc.status == 404:  # purged or never ours; stop polling it forever
            with db_session() as conn:
                conn.execute(
                    "UPDATE downloads SET status='failed', error_code='download_failed', updated_at=? "
                    "WHERE transfer_id=?", (_now(), transfer_id),
                )
        return
    status = body.get("status")
    if status == "ready":
        with db_session() as conn:
            conn.execute(
                "UPDATE downloads SET status='downloading', updated_at=? WHERE transfer_id=?",
                (_now(), transfer_id),
            )
        _download_ready_file(transfer_id, row["filename"], body["download_url"])
    else:
        with db_session() as conn:
            conn.execute(
                "UPDATE downloads SET status=?, error_code=?, updated_at=? WHERE transfer_id=?",
                (status, body.get("error_code"), _now(), transfer_id),
            )


async def _worker_loop() -> None:
    while True:
        try:
            with db_session() as conn:
                placeholders = ", ".join("?" * len(_TERMINAL_STATUSES))
                rows = [
                    dict(r) for r in conn.execute(
                        f"SELECT * FROM downloads WHERE status NOT IN ({placeholders})", _TERMINAL_STATUSES
                    ).fetchall()
                ]
            for row in rows:
                await asyncio.to_thread(_poll_one, row)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - one bad row must not kill the whole worker
            pass
        await asyncio.sleep(config.DOWNLOAD_POLL_SECONDS)


def start() -> None:
    global _worker_task
    if _worker_task is None:
        _worker_task = asyncio.create_task(_worker_loop())


def stop() -> None:
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        _worker_task = None
