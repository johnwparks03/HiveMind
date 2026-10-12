from fastapi import APIRouter
from pydantic import BaseModel

from app.errors import ApiError
from app.folders.scanner import add_folder, list_folders, remove_folder, scan_folder

router = APIRouter()


class AddFolderRequest(BaseModel):
    path: str


@router.post("/folders")
def post_folder(body: AddFolderRequest):
    """Stand-in for the native Windows folder dialog (E0-S4) — takes a path string
    directly for now so local search is testable without the frontend.
    """
    import os
    if not os.path.isdir(body.path):
        raise ApiError(400, "invalid_request", "not a directory")
    folder_id = add_folder(body.path)
    return {"folder_id": folder_id}


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
    return {}


@router.post("/folders/{folder_id}/rescan")
def post_rescan(folder_id: str):
    from app.db import session
    with session() as conn:
        row = conn.execute("SELECT path FROM folders WHERE folder_id = ?", (folder_id,)).fetchone()
    if not row:
        raise ApiError(404, "not_found", "folder not found")
    stats = scan_folder(folder_id, row["path"])
    return {"stats": stats}
