"""Orchestrates one file end to end: extract -> chunk -> embed -> store -> registry update."""
import hashlib
from datetime import datetime
from pathlib import Path

from app.extraction.extract import extract_text
from app.indexing.chunking import chunk_text
from app.indexing.embeddings import embed
from app.indexing.vector_store import delete_file, upsert_chunks


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def index_file(
    file_id: str,
    path: Path,
    filename: str,
    file_created_at: datetime,
    file_modified_at: datetime,
) -> dict:
    """Returns a dict of fields the caller should persist to the registry row:
    index_status, index_failure_reason, in_document_date.
    """
    result = extract_text(path)
    if result.failure_reason:
        return {
            "index_status": "failed",
            "index_failure_reason": result.failure_reason,
            "in_document_date": None,
        }

    chunks = chunk_text(result.text)
    embeddings = embed(chunks)

    # Re-indexing a changed file: clear its old chunks first.
    delete_file(file_id)

    base_metadata = {
        "file_id": file_id,
        "filename": filename,
        "path": str(path),
        "file_created_at_ts": file_created_at.timestamp(),
        "file_modified_at_ts": file_modified_at.timestamp(),
    }
    if result.in_document_date:
        base_metadata["in_document_date_ts"] = result.in_document_date.timestamp()

    upsert_chunks(file_id, chunks, embeddings, base_metadata)

    return {
        "index_status": "indexed",
        "index_failure_reason": None,
        "in_document_date": result.in_document_date.isoformat() if result.in_document_date else None,
    }
