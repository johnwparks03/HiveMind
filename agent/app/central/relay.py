"""Relay WebSocket client, owner side (docs/stories/BACKLOG.md E4-S3,
API_Contract.md section 4). A background asyncio task (start()/stop(), hooked into
main.py's lifespan) keeps one connection open while signed in: pings well under API
Gateway's unconfigured 10-minute idle timeout (infra/stack.py sets no override -
confirmed 2026-10-16, running on raw WebSocket API defaults), and reconnects
proactively before the 2-hour hard connection cap rather than waiting to be dropped.
On an upload_request it acks within the deadline, streams the file to the presigned
S3 PUT, then reports complete/fail.
"""
import asyncio
import json
import logging
import re
import time
from pathlib import Path

import httpx
import websockets

from app import config
from app.auth import session
from app.central import client as central_client
from app.db import session as db_session
from app.errors import ApiError

log = logging.getLogger(__name__)

_task: asyncio.Task | None = None
_loop: asyncio.AbstractEventLoop | None = None
_current_ws = None
_state = "disconnected"  # connected | connecting | disconnected


def state() -> str:
    return _state


def _file_for_transfer(file_id: str) -> dict | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT path, public_state FROM files WHERE file_id = ?", (file_id,)
        ).fetchone()
    return dict(row) if row else None


def _fail(transfer_id: str, reason: str) -> None:
    try:
        central_client.request_json("POST", f"/transfers/{transfer_id}/fail", json={"reason": reason})
    except ApiError:
        pass  # best-effort: nothing more to do if central can't be told


def _iter_file(path: Path):
    with open(path, "rb") as f:
        while chunk := f.read(config.TRANSFER_UPLOAD_CHUNK_BYTES):
            yield chunk


def _describe_upload_error(exc: Exception) -> str:
    """What to log about a failed upload: the exception type, or for a refusal the HTTP status and S3's
    error code. Never the URL (a presigned URL carries credentials) or any file content."""
    if isinstance(exc, httpx.HTTPStatusError):
        code = re.search(r"<Code>([^<]+)</Code>", exc.response.text or "")
        return f"HTTP {exc.response.status_code}" + (f" {code.group(1)}" if code else "")
    return type(exc).__name__


def _handle_upload_request(payload: dict) -> None:
    """Runs off the event loop (asyncio.to_thread) since it does blocking file IO
    and sync HTTP calls; never load the whole file into memory (large PPTX/PDF)."""
    transfer_id = payload["transfer_id"]
    file = _file_for_transfer(payload["file_id"])
    if file is None:
        _fail(transfer_id, "file_not_found")
        return
    path = Path(file["path"])
    if file["public_state"] != "public":
        _fail(transfer_id, "not_public")
        return
    if not path.exists():
        _fail(transfer_id, "file_not_found")
        return
    try:
        central_client.request_json("POST", f"/transfers/{transfer_id}/ack")
    except ApiError:
        return  # the ack deadline will fail this transfer centrally; nothing else to do
    try:
        size = path.stat().st_size
        # S3 refuses a chunked upload (no Content-Length) to a presigned URL with 501 NotImplemented, which
        # is what httpx sends for a bare generator. Declare the exact size and still stream in pieces.
        httpx.put(
            payload["upload_url"], content=_iter_file(path), headers={"Content-Length": str(size)},
            timeout=config.CENTRAL_TIMEOUT_SECONDS,
        ).raise_for_status()
    except Exception as exc:  # noqa: BLE001 - any upload failure reports upload_error, never crashes the relay
        log.warning("relay upload failed: %s", _describe_upload_error(exc))
        _fail(transfer_id, "upload_error")
        return
    try:
        central_client.request_json("POST", f"/transfers/{transfer_id}/complete", json={"size_bytes": size})
    except ApiError:
        pass


async def _connect_and_serve() -> None:
    global _state, _current_ws
    headers = {"Authorization": f"Bearer {session.access_token()}"}
    async with websockets.connect(config.RELAY_WS_URL, additional_headers=headers, open_timeout=10) as ws:
        _current_ws = ws
        _state = "connected"
        connected_at = time.monotonic()
        last_ping = connected_at
        # Poll more often than the ping interval so a logout (close(), see below) or
        # the proactive-reconnect deadline is noticed quickly, without sending an
        # actual ping more often than RELAY_PING_INTERVAL_SECONDS.
        poll_seconds = min(config.RELAY_PING_INTERVAL_SECONDS, 5)
        try:
            while True:
                if not session.is_signed_in():
                    return
                if time.monotonic() - connected_at >= config.RELAY_RECONNECT_BEFORE_SECONDS:
                    return
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=poll_seconds)
                except asyncio.TimeoutError:
                    if time.monotonic() - last_ping >= config.RELAY_PING_INTERVAL_SECONDS:
                        await ws.send(json.dumps({"action": "ping"}))
                        last_ping = time.monotonic()
                    continue
                try:
                    message = json.loads(raw)
                except ValueError:
                    continue
                action = message.get("action")
                if action == "upload_request":
                    asyncio.create_task(asyncio.to_thread(_handle_upload_request, message))
                # "pong" and anything else: no-op.
        finally:
            _current_ws = None


async def _run() -> None:
    global _state
    backoff = config.RELAY_RECONNECT_BACKOFF_BASE_SECONDS
    while True:
        if not session.is_signed_in() or not config.RELAY_WS_URL:
            _state = "disconnected"
            await asyncio.sleep(config.RELAY_RECONNECT_BACKOFF_BASE_SECONDS)
            continue
        try:
            _state = "connecting"
            await _connect_and_serve()
            backoff = config.RELAY_RECONNECT_BACKOFF_BASE_SECONDS  # a clean disconnect isn't a failure
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - any connection error just triggers a retry with backoff
            pass
        _state = "disconnected"
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, config.RELAY_RECONNECT_BACKOFF_MAX_SECONDS)


def start() -> None:
    global _task, _loop
    if _task is None:
        _loop = asyncio.get_running_loop()
        _task = asyncio.create_task(_run())


def stop() -> None:
    global _task, _state
    if _task is not None:
        _task.cancel()
        _task = None
    _state = "disconnected"


def close() -> None:
    """Called on logout (a sync route, so no event loop of its own) to force-close
    the live connection now rather than wait for the loop's own sign-in check to
    notice. The background task itself keeps running so a later login can
    reconnect - only stop() (agent shutdown) cancels it."""
    if _current_ws is not None and _loop is not None:
        asyncio.run_coroutine_threadsafe(_current_ws.close(), _loop)
