"""Folder add + scan. Feature_List 1.1/1.2 — initial scan plus content-hash change
detection so unchanged files aren't re-indexed. The continuous watcher (watchdog)
lives in watcher.py and calls back into scan_folder on any change.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import TAG_EXCERPT_MAX_CHARS
from app.db import session
from app.errors import ApiError
from app.extraction.extract import extract_text
from app.indexing.indexer import content_hash, index_file
from app.indexing.vector_store import delete_file
from app.llm import bedrock
from app.llm.tags import generate_tags
from app.sources.local_filesystem import LocalFilesystemSource


def _generate_tags_best_effort(filename: str, excerpt: str | None) -> str | None:
    """Tags are generated automatically on add/rescan (explicit product decision,
    2026-10-15 — cost/latency accepted). Never lets a Bedrock problem fail the scan:
    AWS credentials missing, Bedrock unreachable, or a rejected model reply all just
    mean this file stays untagged until the next scan, same as any other file that
    hasn't been tagged yet.
    """
    if not excerpt:
        return None
    try:
        return json.dumps(generate_tags(filename, excerpt))
    except (bedrock.BedrockUnavailable, ApiError):
        return None


def add_folder(path: str) -> str:
    folder_id = str(uuid.uuid4())
    with session() as conn:
        conn.execute(
            "INSERT INTO folders (folder_id, path, added_at) VALUES (?, ?, ?)",
            (folder_id, path, datetime.now(timezone.utc).isoformat()),
        )
    scan_folder(folder_id, path)
    return folder_id


def exclude_files(file_ids: list[str]) -> int:
    """Removes files from HiveMind: drops their index entries and remembers their paths so
    rescans skip them. Nothing is deleted from disk. Returns how many were removed."""
    removed = 0
    with session() as conn:
        for file_id in file_ids:
            row = conn.execute("SELECT path FROM files WHERE file_id = ?", (file_id,)).fetchone()
            if not row:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO excluded_files (path, excluded_at) VALUES (?, ?)",
                (row["path"], datetime.now(timezone.utc).isoformat()),
            )
            delete_file(file_id)
            conn.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
            removed += 1
    return removed


def list_folders() -> list[dict]:
    with session() as conn:
        rows = conn.execute("SELECT * FROM folders ORDER BY added_at").fetchall()
        return [dict(r) for r in rows]


def remove_folder(folder_id: str) -> bool:
    """Drops the folder and every file registered under it, local index included.
    Returns False if the folder didn't exist."""
    with session() as conn:
        row = conn.execute("SELECT folder_id FROM folders WHERE folder_id = ?", (folder_id,)).fetchone()
        if not row:
            return False
        file_ids = [r["file_id"] for r in conn.execute(
            "SELECT file_id FROM files WHERE folder_id = ?", (folder_id,)
        ).fetchall()]
        for file_id in file_ids:
            delete_file(file_id)
        conn.execute("DELETE FROM files WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE folder_id = ?", (folder_id,))
    return True


def scan_folder(folder_id: str, path: str) -> dict:
    """Walks the folder, registers new files, re-indexes changed ones, skips
    unchanged ones (by content hash), and marks missing ones as removed.
    """
    source = LocalFilesystemSource(path)
    found = source.list_files()
    found_paths = {f.source_path for f in found}

    stats = {"added": 0, "reindexed": 0, "unchanged": 0, "failed": 0, "removed": 0}

    with session() as conn:
        existing = {
            row["path"]: dict(row)
            for row in conn.execute("SELECT * FROM files WHERE folder_id = ?", (folder_id,)).fetchall()
        }
        excluded = {row["path"] for row in conn.execute("SELECT path FROM excluded_files").fetchall()}

        for source_file in found:
            if source_file.source_path in excluded:
                continue  # removed from HiveMind by the user; leave it out until they add it back
            raw = source.get_file_bytes(source_file.source_path)
            new_hash = content_hash(raw)
            existing_row = existing.get(source_file.source_path)

            if existing_row and existing_row["content_hash"] == new_hash:
                stats["unchanged"] += 1
                # Content didn't change, so re-extracting/re-chunking/re-embedding would be
                # wasted work — but a file added before AWS credentials existed (or whose
                # tagging failed last time) should still get tagged on the next rescan,
                # without a full re-index.
                if not existing_row["tags"] and existing_row["index_status"] == "indexed":
                    excerpt_result = extract_text(Path(source_file.source_path))
                    tags = _generate_tags_best_effort(
                        source_file.filename, excerpt_result.text[:TAG_EXCERPT_MAX_CHARS]
                    )
                    if tags:
                        conn.execute("UPDATE files SET tags=? WHERE file_id=?", (tags, existing_row["file_id"]))
                continue

            file_id = existing_row["file_id"] if existing_row else str(uuid.uuid4())
            index_result = index_file(
                file_id=file_id,
                path=Path(source_file.source_path),
                filename=source_file.filename,
                file_created_at=source_file.created_at,
                file_modified_at=source_file.modified_at,
            )
            tags = _generate_tags_best_effort(source_file.filename, index_result["excerpt"])

            if existing_row:
                conn.execute(
                    """UPDATE files SET content_hash=?, file_created_at=?, file_modified_at=?,
                       in_document_date=?, index_status=?, index_failure_reason=?, tags=? WHERE file_id=?""",
                    (
                        new_hash,
                        source_file.created_at.isoformat(),
                        source_file.modified_at.isoformat(),
                        index_result["in_document_date"],
                        index_result["index_status"],
                        index_result["index_failure_reason"],
                        tags,
                        file_id,
                    ),
                )
                stats["reindexed"] += 1
            else:
                conn.execute(
                    """INSERT INTO files
                       (file_id, folder_id, path, filename, content_hash, file_created_at,
                        file_modified_at, in_document_date, index_status, index_failure_reason, tags)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_id,
                        folder_id,
                        source_file.source_path,
                        source_file.filename,
                        new_hash,
                        source_file.created_at.isoformat(),
                        source_file.modified_at.isoformat(),
                        index_result["in_document_date"],
                        index_result["index_status"],
                        index_result["index_failure_reason"],
                        tags,
                    ),
                )
                stats["added"] += 1

            if index_result["index_status"] == "failed":
                stats["failed"] += 1

        # Anything in the registry but no longer on disk: drop it and its chunks.
        for path_, row in existing.items():
            if path_ not in found_paths:
                conn.execute("DELETE FROM files WHERE file_id = ?", (row["file_id"],))
                delete_file(row["file_id"])
                stats["removed"] += 1

    return stats
