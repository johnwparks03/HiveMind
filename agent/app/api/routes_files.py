import os

from fastapi import APIRouter, HTTPException

from app.db import session

router = APIRouter()


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
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "file not found"}})
    if not os.path.exists(row["path"]):
        raise HTTPException(status_code=404, detail={"error": {"code": "file_missing", "message": "file no longer on disk"}})
    os.startfile(row["path"])  # noqa: S606 - Windows-only MVP, launches default app
    return {}
