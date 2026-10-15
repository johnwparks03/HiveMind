"""Folder-level share/unshare (docs/stories/BACKLOG.md E3-S6). A one-time
snapshot: shares every file currently indexed in the folder. Files added to the
folder later are NOT auto-shared — the folder has to be shared again to pick
them up, matching the story's explicit decision.
"""
from app.central import publish
from app.db import session


def share_preview(folder_id: str) -> int:
    """Counts indexed, not-yet-public files in the folder. No side effects — lets
    the UI confirm ("Share N files with your team?") before committing."""
    with session() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM files WHERE folder_id = ? AND index_status = 'indexed' "
            "AND public_state != 'public'",
            (folder_id,),
        ).fetchone()
    return row["n"]


def _eligible_file_ids(folder_id: str, where: str) -> list[str]:
    with session() as conn:
        rows = conn.execute(
            f"SELECT file_id FROM files WHERE folder_id = ? AND {where}", (folder_id,)
        ).fetchall()
    return [r["file_id"] for r in rows]


def _mark_pending_and_enqueue(file_ids: list[str], intent: str) -> int:
    if not file_ids:
        return 0
    with session() as conn:
        placeholders = ",".join("?" * len(file_ids))
        conn.execute(f"UPDATE files SET publish_state='pending' WHERE file_id IN ({placeholders})", file_ids)
    for file_id in file_ids:
        publish.enqueue(file_id, intent)
    return len(file_ids)


def share_folder(folder_id: str) -> int:
    file_ids = _eligible_file_ids(folder_id, "index_status = 'indexed' AND public_state != 'public'")
    return _mark_pending_and_enqueue(file_ids, "publish")


def unshare_folder(folder_id: str) -> int:
    file_ids = _eligible_file_ids(folder_id, "public_state = 'public'")
    return _mark_pending_and_enqueue(file_ids, "unpublish")
