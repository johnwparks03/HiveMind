from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.folders.scanner import add_folder, list_folders, scan_folder

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
        raise HTTPException(status_code=400, detail={"error": {"code": "invalid_request", "message": "not a directory"}})
    folder_id = add_folder(body.path)
    return {"folder_id": folder_id}


@router.get("/folders")
def get_folders():
    return {"folders": list_folders()}


@router.post("/folders/{folder_id}/rescan")
def post_rescan(folder_id: str):
    from app.db import session
    with session() as conn:
        row = conn.execute("SELECT path FROM folders WHERE folder_id = ?", (folder_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "folder not found"}})
    stats = scan_folder(folder_id, row["path"])
    return {"stats": stats}
