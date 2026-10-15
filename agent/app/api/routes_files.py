import json
import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.central import publish, teams
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


class SetTagsRequest(BaseModel):
    tags: list[str]


def _get_file(file_id: str) -> dict | None:
    with session() as conn:
        row = conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()
    return dict(row) if row else None


@router.post("/files/remove")
def post_remove_files(body: RemoveFiles):
    """Removes files from HiveMind only. They stay on disk, and rescans skip them."""
    return {"removed": exclude_files(body.file_ids)}


@router.get("/files")
def get_files():
    with session() as conn:
        rows = conn.execute("SELECT * FROM files ORDER BY file_modified_at DESC").fetchall()
        return {"files": [dict(r) for r in rows]}


@router.put("/files/{file_id}/tags")
def put_file_tags(file_id: str, body: SetTagsRequest):
    """User-edited tags are used as-is (central's publish flow never regenerates
    them once set). If the file is already public, queues a metadata re-sync —
    this never extends expires_at, only POST /files/{id}/confirm does that."""
    file = _get_file(file_id)
    if not file:
        raise ApiError(404, "not_found", "file not found")
    with session() as conn:
        conn.execute("UPDATE files SET tags = ? WHERE file_id = ?", (json.dumps(body.tags), file_id))
    if file["public_state"] == "public":
        publish.enqueue(file_id, "publish")
    return _get_file(file_id)


@router.post("/files/{file_id}/publish", status_code=202)
def post_publish_file(file_id: str):
    if teams.current_team_or_none() is None:
        raise ApiError(403, "no_team", "join a team before publishing")
    file = _get_file(file_id)
    if not file:
        raise ApiError(404, "not_found", "file not found")
    if file["index_status"] != "indexed":
        raise ApiError(409, "file_unavailable", "file is not indexed")
    with session() as conn:
        conn.execute("UPDATE files SET publish_state = 'pending' WHERE file_id = ?", (file_id,))
    publish.enqueue(file_id, "publish")
    return _get_file(file_id)


@router.post("/files/{file_id}/unpublish", status_code=202)
def post_unpublish_file(file_id: str):
    file = _get_file(file_id)
    if not file:
        raise ApiError(404, "not_found", "file not found")
    with session() as conn:
        conn.execute("UPDATE files SET publish_state = 'pending' WHERE file_id = ?", (file_id,))
    publish.enqueue(file_id, "unpublish")
    return _get_file(file_id)


@router.post("/files/{file_id}/retry", status_code=202)
def post_retry_publish(file_id: str):
    """Re-queues a file whose last publish/unpublish attempt failed."""
    if not publish.retry(file_id):
        raise ApiError(409, "conflict", "nothing to retry for this file")
    with session() as conn:
        conn.execute("UPDATE files SET publish_state = 'pending' WHERE file_id = ?", (file_id,))
    return _get_file(file_id)


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
