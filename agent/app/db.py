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
    publish_failed_intent TEXT,            -- publish | unpublish: which direction failed, so retry() redoes it
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

-- Durable publish/unpublish queue (agent/app/central/publish.py). One row per
-- file_id: a repeat enqueue with a new intent overwrites the row ("latest intent
-- wins" instead of queuing contradictory work), and survives an agent restart
-- mid-publish. No foreign key to files: a queued unpublish must outlive the local
-- row of a file that was deleted, removed with its folder, or found missing (E6-S6),
-- so the file's chunk text does not stay readable centrally.
CREATE TABLE IF NOT EXISTS publish_queue (
    file_id         TEXT PRIMARY KEY,
    intent          TEXT NOT NULL CHECK (intent IN ('publish', 'unpublish')),
    attempts        INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT NOT NULL,
    last_error      TEXT
);

-- Saved Ask conversations. Local to this computer; only the question and the excerpts
-- needed for an answer leave it (the Bedrock call), never the chat history itself.
CREATE TABLE IF NOT EXISTS chats (
    chat_id    TEXT PRIMARY KEY,
    title      TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    chat_id    TEXT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    sources    TEXT,              -- JSON list of {file_id, filename, source}; source is 'local' or
                              -- 'teammate' (absent on older rows: treat as local); null for user messages
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_chat ON chat_messages(chat_id);

-- Requester-side download tracking (agent/app/central/download.py). One row per
-- transfer_id so a page refresh can resume showing in-flight transfers
-- (API_Contract.md section 2.6: GET /transfers lists "this session's transfers").
CREATE TABLE IF NOT EXISTS downloads (
    transfer_id   TEXT PRIMARY KEY,
    file_id       TEXT NOT NULL,
    filename      TEXT NOT NULL,
    status        TEXT NOT NULL,  -- requested|uploading|ready|downloading|downloaded|failed|expired
    error_code    TEXT,
    saved_path    TEXT,
    requested_at  TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

-- Local agent settings (app/settings.py), e.g. a user-chosen download destination
-- folder in place of the default (real Windows Downloads folder).
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_publish_queue(conn: sqlite3.Connection) -> None:
    """E6-S6: databases created before this had a foreign key from publish_queue to files,
    which would block queueing an unpublish for a file whose row is being deleted. SQLite
    cannot drop a constraint, so rebuild the table once. Idempotent: a table without the
    foreign key is left alone, and queued rows are kept."""
    if not conn.execute("PRAGMA foreign_key_list(publish_queue)").fetchall():
        return
    conn.executescript("""
        BEGIN;
        CREATE TABLE publish_queue_new (
            file_id         TEXT PRIMARY KEY,
            intent          TEXT NOT NULL CHECK (intent IN ('publish', 'unpublish')),
            attempts        INTEGER NOT NULL DEFAULT 0,
            next_attempt_at TEXT NOT NULL,
            last_error      TEXT
        );
        INSERT INTO publish_queue_new SELECT file_id, intent, attempts, next_attempt_at, last_error
            FROM publish_queue;
        DROP TABLE publish_queue;
        ALTER TABLE publish_queue_new RENAME TO publish_queue;
        COMMIT;
    """)


def _migrate_files_columns(conn: sqlite3.Connection) -> None:
    """E6-S6: remember which direction of a publish failed. Idempotent ADD COLUMN for
    databases created before the column existed."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(files)").fetchall()}
    if "publish_failed_intent" not in columns:
        conn.execute("ALTER TABLE files ADD COLUMN publish_failed_intent TEXT")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _migrate_files_columns(conn)
        _migrate_publish_queue(conn)


@contextmanager
def session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
