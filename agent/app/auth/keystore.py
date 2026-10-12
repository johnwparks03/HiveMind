"""Refresh-token storage in Windows Credential Manager via `keyring`. If the
keychain is unavailable we fall back to memory only (Feature_List 1.9): the user
stays signed in for this run but must log in again after a restart.

Credential Manager caps a credential blob at 2,560 bytes and keyring stores it as
UTF-16 (~1,280 characters), while a Cognito refresh token can be longer. So the
value is split across several entries ("<name>.0", "<name>.1", ...) with an index
entry that records the email and chunk count; the index is written last.
"""
import logging

import keyring

from app import config

log = logging.getLogger(__name__)

_INDEX = "refresh_token"
_MEMORY_KEY = "refresh_token"
_memory: dict[str, str] = {}
persistent = True


def _chunks(value: str) -> list[str]:
    size = config.KEYRING_CHUNK_CHARS
    return [value[i:i + size] for i in range(0, len(value), size)] or [""]


def _chunk_name(i: int) -> str:
    return f"{_INDEX}.{i}"


def _stored_count() -> int | None:
    """Chunk count from the index entry, or None if there is no usable entry."""
    raw = keyring.get_password(config.KEYRING_SERVICE, _INDEX)
    if not raw or "\n" not in raw:
        return None
    try:
        return int(raw.rsplit("\n", 1)[1])
    except ValueError:
        return None


def save(email: str, refresh_token: str) -> None:
    global persistent
    chunks = _chunks(refresh_token)
    try:
        old_count = _stored_count() or 0
        for i, chunk in enumerate(chunks):
            keyring.set_password(config.KEYRING_SERVICE, _chunk_name(i), chunk)
        keyring.set_password(config.KEYRING_SERVICE, _INDEX, f"{email}\n{len(chunks)}")
        _delete_chunks(len(chunks), old_count)
        persistent = True
        _memory.pop(_MEMORY_KEY, None)
    except Exception as exc:  # keyring raises backend-specific errors
        log.warning("keychain unavailable, keeping refresh token in memory only: %s", type(exc).__name__)
        persistent = False
        _memory[_MEMORY_KEY] = f"{email}\n{refresh_token}"
        # Don't leave a previous user's entry to be restored on the next start.
        _delete_stored()


def _delete_chunks(start: int, end: int) -> None:
    for i in range(start, end):
        try:
            keyring.delete_password(config.KEYRING_SERVICE, _chunk_name(i))
        except Exception:
            pass


def _delete_stored() -> None:
    try:
        count = _stored_count() or 0
        keyring.delete_password(config.KEYRING_SERVICE, _INDEX)
        _delete_chunks(0, count)
    except Exception as exc:
        log.warning("could not clear keychain entry: %s", type(exc).__name__)


def load() -> tuple[str, str] | None:
    # The in-memory value (set when the keychain failed) is always the newer one.
    mem = _memory.get(_MEMORY_KEY)
    if mem and "\n" in mem:
        email, token = mem.split("\n", 1)
        return email, token
    try:
        count = _stored_count()
        if count is None:
            return None
        email = keyring.get_password(config.KEYRING_SERVICE, _INDEX).split("\n", 1)[0]
        parts = [keyring.get_password(config.KEYRING_SERVICE, _chunk_name(i)) for i in range(count)]
    except Exception as exc:
        log.warning("keychain read failed: %s", type(exc).__name__)
        return None
    if any(p is None for p in parts):
        return None
    return email, "".join(parts)


def delete() -> None:
    _memory.pop(_MEMORY_KEY, None)
    _delete_stored()
