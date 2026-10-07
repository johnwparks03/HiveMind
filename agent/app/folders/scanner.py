"""Folder add + scan. Feature_List 1.1/1.2 — initial scan plus content-hash change
detection so unchanged files aren't re-indexed. The continuous watcher (watchdog)
lives in watcher.py and calls back into scan_folder on any change.
"""
import uuid
from datetime import datetime, timezone

from app.db import session
from app.indexing.indexer import content_hash, index_file
from app.indexing.vector_store import delete_file
from app.sources.local_filesystem import LocalFilesystemSource


def add_folder(path: str) -> str:
    folder_id = str(uuid.uuid4())
    with session() as conn:
        conn.execute(
            "INSERT INTO folders (folder_id, path, added_at) VALUES (?, ?, ?)",
            (folder_id, path, datetime.now(timezone.utc).isoformat()),
        )
    scan_folder(folder_id, path)
    return folder_id


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

        for source_file in found:
            raw = source.get_file_bytes(source_file.source_path)
            new_hash = content_hash(raw)
            existing_row = existing.get(source_file.source_path)

            if existing_row and existing_row["content_hash"] == new_hash:
                stats["unchanged"] += 1
                continue

            file_id = existing_row["file_id"] if existing_row else str(uuid.uuid4())
            index_result = index_file(
                file_id=file_id,
                path=__import__("pathlib").Path(source_file.source_path),
                filename=source_file.filename,
                file_created_at=source_file.created_at,
                file_modified_at=source_file.modified_at,
            )

            if existing_row:
                conn.execute(
                    """UPDATE files SET content_hash=?, file_created_at=?, file_modified_at=?,
                       in_document_date=?, index_status=?, index_failure_reason=? WHERE file_id=?""",
                    (
                        new_hash,
                        source_file.created_at.isoformat(),
                        source_file.modified_at.isoformat(),
                        index_result["in_document_date"],
                        index_result["index_status"],
                        index_result["index_failure_reason"],
                        file_id,
                    ),
                )
                stats["reindexed"] += 1
            else:
                conn.execute(
                    """INSERT INTO files
                       (file_id, folder_id, path, filename, content_hash, file_created_at,
                        file_modified_at, in_document_date, index_status, index_failure_reason)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
