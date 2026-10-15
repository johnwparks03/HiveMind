import json
import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import TAG_EXCERPT_MAX_CHARS
from app.db import session
from app.errors import ApiError
from app.extraction.extract import extract_text
from app.folders.scanner import exclude_files
from app.llm import bedrock
from app.llm.tags import generate_tags

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


@router.post("/files/{file_id}/tags/generate")
def post_generate_tags(file_id: str):
    """Tags are now generated automatically on add/rescan (scanner.py); this endpoint
    retags a single file by hand, e.g. to retry one that failed automatically."""
    with session() as conn:
        row = conn.execute("SELECT path, filename FROM files WHERE file_id = ?", (file_id,)).fetchone()
    if not row:
        raise ApiError(404, "not_found", "file not found")
    if not os.path.exists(row["path"]):
        raise ApiError(404, "file_missing", "file no longer on disk")

    result = extract_text(Path(row["path"]))
    if result.failure_reason:
        raise ApiError(409, "conflict", "file could not be read for tagging", {"reason": result.failure_reason})

    try:
        tags = generate_tags(row["filename"], result.text[:TAG_EXCERPT_MAX_CHARS])
    except bedrock.BedrockUnavailable:
        raise ApiError(503, "service_unavailable", "tag generation is unavailable") from None

    with session() as conn:
        conn.execute("UPDATE files SET tags = ? WHERE file_id = ?", (json.dumps(tags), file_id))
    return {"file_id": file_id, "tags": tags}


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
