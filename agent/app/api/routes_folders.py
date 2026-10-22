import asyncio
import logging
import threading

from fastapi import APIRouter
from pydantic import BaseModel

from app.central import teams
from app.db import session
from app.errors import ApiError
from app.folders import picker, share, watcher
from app.folders.scanner import list_folders, register_folder, remove_folder, scan_folder

router = APIRouter()
log = logging.getLogger(__name__)


def _folder_exists(folder_id: str) -> bool:
    with session() as conn:
        return conn.execute(
            "SELECT 1 FROM folders WHERE folder_id = ?", (folder_id,)
        ).fetchone() is not None


def _get_folder(folder_id: str) -> dict:
    with session() as conn:
        return dict(conn.execute("SELECT * FROM folders WHERE folder_id = ?", (folder_id,)).fetchone())


def _scan_then_watch(folder_id: str, path: str) -> None:
    """Runs the initial scan off the request, then starts the watcher. A failed scan is recorded on
    the folder (scan_state 'failed') and the folder is still watched, so later changes get picked up."""
    try:
        scan_folder(folder_id, path)
    except Exception:
        log.exception("initial scan failed for folder %s", folder_id)
    watcher.watch_folder(folder_id, path)


@router.post("/folders/pick")
async def post_pick_folder():
    """Opens the Windows folder dialog. Runs off the event loop so other requests keep working
    while it's open. Cancelling returns {"path": null}, not an error (API_Contract 2.3)."""
    path = await asyncio.to_thread(picker.pick_folder)
    return {"path": path}


class AddFolderRequest(BaseModel):
    path: str


@router.post("/folders", status_code=201)
def post_folder(body: AddFolderRequest):
    """Stand-in for the native Windows folder dialog (E0-S4) — takes a path string
    directly for now so local search is testable without the frontend.

    Returns at once with the folder in scan_state 'scanning'; the scan runs on a background thread
    and GET /folders reports its progress.
    """
    import os
    if not os.path.isdir(body.path):
        raise ApiError(400, "invalid_request", "not a directory")
    folder_id = register_folder(body.path)
    threading.Thread(target=_scan_then_watch, args=(folder_id, body.path), daemon=True).start()
    return _get_folder(folder_id)


@router.get("/folders")
def get_folders():
    return {"folders": list_folders()}


@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: str):
    """Drops the folder and everything indexed under it. Local-only today — there's
    no central metadata to unpublish yet (that's the E3/E5 cascade once it exists).
    """
    if not remove_folder(folder_id):
        raise ApiError(404, "not_found", "folder not found")
    watcher.unwatch_folder(folder_id)
    return {}


@router.post("/folders/{folder_id}/rescan")
def post_rescan(folder_id: str):
    with session() as conn:
        row = conn.execute("SELECT path FROM folders WHERE folder_id = ?", (folder_id,)).fetchone()
    if not row:
        raise ApiError(404, "not_found", "folder not found")
    stats = scan_folder(folder_id, row["path"])
    return {"stats": stats}


@router.get("/folders/{folder_id}/share-preview")
def get_share_preview(folder_id: str):
    if not _folder_exists(folder_id):
        raise ApiError(404, "not_found", "folder not found")
    return {"file_count": share.share_preview(folder_id)}


@router.post("/folders/{folder_id}/share", status_code=202)
def post_share_folder(folder_id: str):
    if not _folder_exists(folder_id):
        raise ApiError(404, "not_found", "folder not found")
    if teams.current_team_or_none() is None:
        raise ApiError(403, "no_team", "join a team before sharing")
    return {"queued": share.share_folder(folder_id)}


@router.post("/folders/{folder_id}/unshare", status_code=202)
def post_unshare_folder(folder_id: str):
    if not _folder_exists(folder_id):
        raise ApiError(404, "not_found", "folder not found")
    return {"queued": share.unshare_folder(folder_id)}
