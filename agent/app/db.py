"""SQLite file/folder registry. Feature_List 1.12."""
import sqlite3
from contextlib import contextmanager

from app.config import SQLITE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    folder_id   TEXT PRIMARY KEY,
    path        TEXT NOT NULL UNIQUE,
    added_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    file_id             TEXT PRIMARY KEY,
    folder_id           TEXT NOT NULL REFERENCES folders(folder_id),
    path                TEXT NOT NULL UNIQUE,
    filename            TEXT NOT NULL,
    content_hash        TEXT,
    file_created_at     TEXT,
    file_modified_at    TEXT,
    in_document_date     TEXT,
    index_status        TEXT NOT NULL DEFAULT 'pending',  -- pending | indexed | failed
    index_failure_reason TEXT,
    tags                TEXT,              -- JSON array, set at publish time (not used locally yet)
    public_state        TEXT NOT NULL DEFAULT 'private',  -- private | public (central features, not used yet)
    publish_state       TEXT,              -- pending | published | failed
    published_at        TEXT,
    expires_at           TEXT,
    last_confirmed       TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id);

-- Files the user removed from HiveMind. They stay on disk, but rescans skip these paths.
CREATE TABLE IF NOT EXISTS excluded_files (
    path        TEXT PRIMARY KEY,
    excluded_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
