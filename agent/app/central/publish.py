"""Durable publish/unpublish queue (docs/stories/BACKLOG.md E3-S4/E3-S5). Lives in
SQLite (`publish_queue`), not memory, so a crash mid-publish doesn't lose the
intent. A background asyncio worker (start()/stop(), hooked into main.py's
lifespan) drains it continuously; enqueue()/retry()/cancel_all() are called from
the request-handling routes.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import config
from app.central import client as central_client
from app.db import session as db_session
from app.errors import ApiError
from app.extraction.extract import extract_text
from app.indexing import vector_store
from app.llm import bedrock
from app.llm.tags import generate_tags

_worker_task: asyncio.Task | None = None

# Central answers that retrying cannot fix (bad chunk body, not our file, file purged
# centrally): fail the file at once instead of burning every attempt.
_PERMANENT_STATUSES = (400, 403, 404)


class _PermanentFailure(ApiError):
    """A central rejection of the chunk upload that retrying will not change."""


def _as_aware_iso(value: str | None) -> str | None:
    """file_created_at/file_modified_at are stored as naive local-time ISO strings
    (filesystem stat times have no timezone concept at all) — confirmed live
    2026-10-15: central's validator rejects a timestamp with no tzinfo as
    invalid_request, which was silently failing every publish attempt. Attaching
    the system's actual local offset (not assuming UTC) keeps the represented
    moment correct, it just makes the existing offset explicit.
    """
    if value is None:
        return None
    return datetime.fromisoformat(value).astimezone().isoformat()


def enqueue(file_id: str, intent: str) -> None:
    """intent: 'publish' or 'unpublish'. Overwrites any existing queued row for this
    file_id ('latest intent wins' — toggling publish/unpublish quickly just replaces
    the pending work instead of queuing contradictory steps) and resets backoff."""
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO publish_queue (file_id, intent, attempts, next_attempt_at, last_error) "
            "VALUES (?, ?, 0, ?, NULL)",
            (file_id, intent, now),
        )


def enqueue_sync(file_id: str, intent: str) -> None:
    """enqueue() plus marking the file 'pending', for callers outside the request
    routes (a re-index or a delete found while scanning). Call it after the caller's own
    database transaction has closed: SQLite allows one writer at a time."""
    with db_session() as conn:
        conn.execute("UPDATE files SET publish_state='pending' WHERE file_id=?", (file_id,))
    enqueue(file_id, intent)


def retry(file_id: str) -> bool:
    """Re-enqueues a file whose publish_state is 'failed', in the direction that failed
    (publish_failed_intent). Older rows without it fall back to the original guess from
    public_state: still private means a publish never succeeded, still public means an
    unpublish failed. Returns False if there's nothing to retry."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT public_state, publish_state, publish_failed_intent FROM files WHERE file_id = ?",
            (file_id,),
        ).fetchone()
    if not row or row["publish_state"] != "failed":
        return False
    intent = row["publish_failed_intent"] or ("unpublish" if row["public_state"] == "public" else "publish")
    enqueue(file_id, intent)
    return True


def cancel_all() -> None:
    """Called on leave-team: a queued publish would otherwise just keep retrying
    into 403 no_team forever."""
    with db_session() as conn:
        conn.execute("DELETE FROM publish_queue")


def _publish(file_id: str) -> None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()
    if row is None:
        return  # removed locally since being queued; nothing to publish
    if row["index_status"] != "indexed":
        raise ApiError(409, "file_unavailable", "file is not indexed")

    tags = json.loads(row["tags"]) if row["tags"] else None
    if tags is None:
        # Already-tagged files (the common case now that tagging runs automatically
        # at scan time) skip straight to the central call, per the contract's
        # "existing tags skip generation" decision.
        result = extract_text(Path(row["path"]))
        if result.failure_reason:
            raise ApiError(409, "file_unavailable", "file could not be read")
        try:
            tags = generate_tags(row["filename"], result.text[: config.TAG_EXCERPT_MAX_CHARS])
        except bedrock.BedrockUnavailable:
            # Publish anyway rather than block forever on Bedrock being down — the
            # file is just flagged with no tags, same as the central contract's
            # documented "no_tags" behavior.
            tags = []

    body = central_client.request_json(
        "PUT", f"/files/{file_id}",
        json={
            "filename": row["filename"],
            "tags": tags,
            "file_created_at": _as_aware_iso(row["file_created_at"]),
            "file_modified_at": _as_aware_iso(row["file_modified_at"]),
        },
    ) or {}
    with db_session() as conn:
        conn.execute(
            "UPDATE files SET tags=?, public_state='public', publish_state='published', "
            "publish_failed_intent=NULL, published_at=?, expires_at=?, last_confirmed=? WHERE file_id=?",
            (json.dumps(tags), body.get("published_at"), body.get("expires_at"),
             body.get("last_confirmed"), file_id),
        )
    _upload_chunks(file_id)


def _upload_chunks(file_id: str) -> None:
    """Sends the file's chunk text and embeddings to central (PUT /files/{id}/chunks) so
    teammates' Ask can use them, in batches that central swaps in atomically on the final
    one. Every attempt starts at batch 1: central's retry rule, and the queue keeps one
    row per file with no per-batch progress. An empty file uploads an empty set, which
    also clears chunks a previous version of the file left behind."""
    chunks = vector_store.get_file_chunks(file_id)[: config.MAX_CHUNKS_PER_FILE]
    if [index for index, _, _ in chunks] != list(range(len(chunks))):
        # Chroma is mid re-index (delete then upsert): a partial set must not be committed.
        raise ApiError(503, "service_unavailable", "the file is being re-indexed")
    size = config.CHUNK_UPLOAD_BATCH_SIZE
    total = max(1, -(-len(chunks) // size))
    for number in range(total):
        batch = chunks[number * size:(number + 1) * size]
        body = {
            "chunks": [{"chunk_index": i, "text": text, "embedding": embedding} for i, text, embedding in batch],
            "batch": number + 1,
            "total_batches": total,
        }
        try:
            central_client.request_json(
                "PUT", f"/files/{file_id}/chunks", json=body, timeout=config.CHUNK_UPLOAD_TIMEOUT_SECONDS
            )
        except ApiError as exc:
            if exc.status in _PERMANENT_STATUSES:
                raise _PermanentFailure(exc.status, exc.code, exc.message, exc.details) from None
            raise


def _unpublish(file_id: str) -> None:
    central_client.request_json("DELETE", f"/files/{file_id}")  # idempotent centrally
    with db_session() as conn:
        conn.execute(
            "UPDATE files SET public_state='private', publish_state=NULL, publish_failed_intent=NULL, "
            "published_at=NULL, expires_at=NULL, last_confirmed=NULL WHERE file_id=?",
            (file_id,),
        )


def _handle_failure(
    file_id: str, attempts: int, error: str, intent: str | None = None, permanent: bool = False
) -> None:
    attempts += 1
    if permanent or attempts >= config.PUBLISH_MAX_ATTEMPTS:
        with db_session() as conn:
            conn.execute(
                "UPDATE files SET publish_state='failed', publish_failed_intent=? WHERE file_id=?",
                (intent, file_id),
            )
            conn.execute("DELETE FROM publish_queue WHERE file_id=?", (file_id,))
        return
    delay = config.PUBLISH_BACKOFF_BASE_SECONDS * (2 ** (attempts - 1))
    next_attempt_at = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()
    with db_session() as conn:
        conn.execute(
            "UPDATE publish_queue SET attempts=?, next_attempt_at=?, last_error=? WHERE file_id=?",
            (attempts, next_attempt_at, error, file_id),
        )


async def _process_row(row: dict) -> None:
    file_id, intent, attempts = row["file_id"], row["intent"], row["attempts"]
    try:
        if intent == "publish":
            await asyncio.to_thread(_publish, file_id)
        else:
            await asyncio.to_thread(_unpublish, file_id)
    except _PermanentFailure as exc:
        _handle_failure(file_id, attempts, exc.message, intent=intent, permanent=True)
    except ApiError as exc:
        _handle_failure(file_id, attempts, exc.message, intent=intent)
    else:
        with db_session() as conn:
            conn.execute("DELETE FROM publish_queue WHERE file_id = ?", (file_id,))


async def _process_due_rows() -> None:
    with db_session() as conn:
        rows = [
            dict(r) for r in conn.execute(
                "SELECT * FROM publish_queue WHERE next_attempt_at <= ?",
                (datetime.now(timezone.utc).isoformat(),),
            ).fetchall()
        ]
    if not rows:
        return
    semaphore = asyncio.Semaphore(config.PUBLISH_CONCURRENCY)

    async def _bounded(row: dict) -> None:
        async with semaphore:
            await _process_row(row)

    await asyncio.gather(*(_bounded(r) for r in rows))


_MAX_MINE_PAGES = 200


def _fetch_mine() -> list[dict]:
    """Every page of GET /files/mine (the page size is central's default)."""
    files: list[dict] = []
    cursor = None
    for _ in range(_MAX_MINE_PAGES):
        kwargs = {"params": {"cursor": cursor}} if cursor else {}
        body = central_client.request_json("GET", "/files/mine", **kwargs) or {}
        files.extend(body.get("files", []))
        cursor = body.get("next_cursor")
        if not cursor:
            break
    return files


def _reconcile() -> None:
    """Catches a crash mid-publish, or a file still public centrally after being
    deleted/moved locally, and backfills chunks (E6-S6) for files published before
    chunk upload existed. Best-effort: central being unreachable just skips this round,
    same as any other optional background sync.
    """
    try:
        remote_files = _fetch_mine()
    except ApiError:
        return
    mine = {f["file_id"]: f for f in remote_files}
    with db_session() as conn:
        local_public_ids = {
            r["file_id"] for r in conn.execute(
                "SELECT file_id FROM files WHERE public_state = 'public'"
            ).fetchall()
        }
        for file_id, remote in mine.items():
            conn.execute(
                "UPDATE files SET public_state='public', publish_state='published', tags=?, "
                "published_at=?, expires_at=?, last_confirmed=? "
                "WHERE file_id=? AND public_state != 'public'",
                (json.dumps(remote.get("tags") or []), remote.get("published_at"),
                 remote.get("expires_at"), remote.get("last_confirmed"), file_id),
            )
        for file_id in local_public_ids - mine.keys():
            conn.execute(
                "UPDATE files SET public_state='private', publish_state=NULL, published_at=NULL, "
                "expires_at=NULL, last_confirmed=NULL WHERE file_id=?",
                (file_id,),
            )
        backfill = _chunks_to_backfill(conn, mine)
    for file_id in backfill:
        enqueue(file_id, "publish")


def _chunks_to_backfill(conn, mine: dict[str, dict]) -> list[str]:
    """Published files central holds no chunks for (chunk_count 0): published before chunk
    upload existed, or an upload that was lost. Only indexed, public, un-failed files with
    local chunks and nothing already queued, so a reconcile never resets a backoff and an
    empty file is not re-sent forever."""
    queued = {r["file_id"] for r in conn.execute("SELECT file_id FROM publish_queue").fetchall()}
    wanted = []
    for file_id, remote in mine.items():
        if remote.get("chunk_count") != 0 or file_id in queued:
            continue
        row = conn.execute(
            "SELECT public_state, publish_state, index_status FROM files WHERE file_id=?", (file_id,)
        ).fetchone()
        if (row and row["public_state"] == "public" and row["index_status"] == "indexed"
                and row["publish_state"] != "failed" and vector_store.has_chunks(file_id)):
            wanted.append(file_id)
    return wanted


async def _worker_loop() -> None:
    last_reconcile = 0.0
    while True:
        try:
            await _process_due_rows()
            now = time.monotonic()
            if now - last_reconcile >= config.PUBLISH_RECONCILE_INTERVAL_SECONDS:
                await asyncio.to_thread(_reconcile)
                last_reconcile = now
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - a bad row must not kill the whole worker
            pass
        await asyncio.sleep(config.PUBLISH_WORKER_POLL_SECONDS)


def start() -> None:
    global _worker_task
    if _worker_task is None:
        _worker_task = asyncio.create_task(_worker_loop())


def stop() -> None:
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        _worker_task = None
