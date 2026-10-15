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
from app.llm import bedrock
from app.llm.tags import generate_tags

_worker_task: asyncio.Task | None = None


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


def retry(file_id: str) -> bool:
    """Re-enqueues a file whose publish_state is 'failed'. The files table doesn't
    separately record which direction failed, so public_state is the tell: still
    private means the publish attempt never succeeded (retry publish); still public
    means an unpublish attempt failed (retry unpublish). Returns False if there's
    nothing to retry."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT public_state, publish_state FROM files WHERE file_id = ?", (file_id,)
        ).fetchone()
    if not row or row["publish_state"] != "failed":
        return False
    enqueue(file_id, "unpublish" if row["public_state"] == "public" else "publish")
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
            "published_at=?, expires_at=?, last_confirmed=? WHERE file_id=?",
            (json.dumps(tags), body.get("published_at"), body.get("expires_at"),
             body.get("last_confirmed"), file_id),
        )


def _unpublish(file_id: str) -> None:
    central_client.request_json("DELETE", f"/files/{file_id}")  # idempotent centrally
    with db_session() as conn:
        conn.execute(
            "UPDATE files SET public_state='private', publish_state=NULL, "
            "published_at=NULL, expires_at=NULL, last_confirmed=NULL WHERE file_id=?",
            (file_id,),
        )


def _handle_failure(file_id: str, attempts: int, error: str) -> None:
    attempts += 1
    if attempts >= config.PUBLISH_MAX_ATTEMPTS:
        with db_session() as conn:
            conn.execute("UPDATE files SET publish_state='failed' WHERE file_id=?", (file_id,))
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
    except ApiError as exc:
        _handle_failure(file_id, attempts, exc.message)
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


def _reconcile() -> None:
    """Catches a crash mid-publish, or a file still public centrally after being
    deleted/moved locally. Best-effort: central being unreachable just skips this
    round, same as any other optional background sync. Simplification: fetches one
    page of GET /files/mine rather than following `next_cursor` — fine at demo
    scale, worth revisiting for a team with hundreds of published files.
    """
    try:
        body = central_client.request_json("GET", "/files/mine") or {}
    except ApiError:
        return
    mine = {f["file_id"]: f for f in body.get("files", [])}
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
