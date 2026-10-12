"""In-memory sign-in state. The refresh token lives in the keychain (keystore);
Cognito tokens are never returned to the frontend.
"""
import threading
import time

from app import config
from app.auth import cognito, keystore
from app.errors import ApiError

_lock = threading.Lock()
_email: str | None = None
_refresh_token: str | None = None
_access_token: str | None = None
_expires_at: float = 0.0


def _set_tokens(result: dict) -> None:
    global _access_token, _expires_at
    _access_token = result["AccessToken"]
    _expires_at = time.time() + int(result.get("ExpiresIn", 3600))


def login(email: str, password: str) -> None:
    global _email, _refresh_token
    result = cognito.password_login(email, password)
    with _lock:
        _email = email
        _refresh_token = result["RefreshToken"]
        _set_tokens(result)
    keystore.save(email, _refresh_token)


def logout() -> None:
    global _email, _refresh_token, _access_token, _expires_at
    with _lock:
        _email = _refresh_token = _access_token = None
        _expires_at = 0.0
    keystore.delete()


def restore_from_keychain() -> None:
    """Silent sign-in at startup. Any failure leaves the agent signed out."""
    global _email, _refresh_token
    stored = keystore.load()
    if not stored:
        return
    email, refresh_token = stored
    try:
        result = cognito.refresh(refresh_token)
    except ApiError as exc:
        if exc.status == 401:  # refresh token revoked or expired
            keystore.delete()
        return
    with _lock:
        _email = email
        _refresh_token = refresh_token
        _set_tokens(result)


def is_signed_in() -> bool:
    return _refresh_token is not None


def email() -> str | None:
    return _email


def access_token() -> str:
    """A valid access token, refreshing if it is near expiry."""
    if not is_signed_in():
        raise ApiError(401, "unauthorized", "not signed in")
    if time.time() >= _expires_at - config.TOKEN_REFRESH_MARGIN_SECONDS:
        refresh_now()
    return _access_token


def refresh_now() -> None:
    if not is_signed_in():
        raise ApiError(401, "unauthorized", "not signed in")
    try:
        result = cognito.refresh(_refresh_token)
    except ApiError as exc:
        if exc.status == 401:
            logout()
            raise ApiError(401, "unauthorized", "session expired, sign in again") from None
        raise
    with _lock:
        _set_tokens(result)
