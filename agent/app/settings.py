"""Local agent settings: a plain key/value table (app/db.py's `settings`). Currently
just the one key below (download.py's user-chosen download destination folder), but
kept generic rather than a single dedicated column, in case a second setting shows up.
"""
from app.db import session as db_session

DOWNLOAD_FOLDER_KEY = "download_folder"


def get(key: str) -> str | None:
    with db_session() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set(key: str, value: str) -> None:
    with db_session() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def clear(key: str) -> None:
    with db_session() as conn:
        conn.execute("DELETE FROM settings WHERE key = ?", (key,))
