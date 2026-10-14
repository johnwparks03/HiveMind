import os

from fastapi import APIRouter
from pydantic import BaseModel

from app.db import session
from app.errors import ApiError
from app.folders.scanner import exclude_files

router = APIRouter()


class RemoveFiles(BaseModel):
    file_ids: list[str]


@router.post("/files/remove")
def post_remove_files(body: RemoveFiles):
    """Removes files from HiveMind only. They stay on disk, and rescans skip them."""
    return {"removed": exclude_files(body.file_ids)}


@router.get("/files")
def get_files():
    with session() as conn:
        rows = conn.execute("SELECT * FROM files ORDER BY file_modified_at DESC").fetchall()
        return {"files": [dict(r) for r in rows]}


@router.post("/files/{file_id}/open")
def post_open_file(file_id: str):
    with session() as conn:
        row = conn.execute("SELECT path FROM files WHERE file_id = ?", (file_id,)).fetchone()
    if not row:
        raise ApiError(404, "not_found", "file not found")
    if not os.path.exists(row["path"]):
        raise ApiError(404, "file_missing", "file no longer on disk")
    os.startfile(row["path"])  # noqa: S606 - Windows-only MVP, launches default app
    return {}
