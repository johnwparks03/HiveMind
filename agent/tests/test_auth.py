import httpx
import pytest

from app.auth import keystore, session

CREDS = {"email": "a@firm.com", "password": "Passw0rd!x"}


def _login(client, auth):
    return client.post("/auth/login", headers=auth, json=CREDS)


def test_signup_created(client, auth, cognito_fake):
    resp = client.post("/auth/signup", headers=auth, json=CREDS)
    assert resp.status_code == 201 and resp.json() == {"status": "created"}
    assert cognito_fake.calls[0][0] == "SignUp"


@pytest.mark.parametrize("kind,status,code", [
    ("UsernameExistsException", 409, "user_exists"),
    ("InvalidPasswordException", 400, "password_policy"),
    ("SomethingElseException", 503, "service_unavailable"),
])
def test_signup_errors(client, auth, cognito_fake, kind, status, code):
    cognito_fake.error["SignUp"] = (400, kind, "Password must have symbols")
    resp = client.post("/auth/signup", headers=auth, json=CREDS)
    assert resp.status_code == status and resp.json()["error"]["code"] == code
    if code == "password_policy":
        assert resp.json()["error"]["details"]["message"] == "Password must have symbols"


def test_login_stores_refresh_token_and_session_shows_signed_in(client, auth, cognito_fake, keyring_fake):
    resp = _login(client, auth)
    assert resp.status_code == 200
    assert resp.json() == {"signed_in": True, "email": "a@firm.com"}  # no Cognito tokens
    assert "refresh-1" in next(iter(keyring_fake.store.values()))

    body = client.get("/session", headers=auth).json()
    assert body["signed_in"] is True and body["email"] == "a@firm.com"
    assert body["agent"] == "ok" and body["team"] is None and body["relay"] == "disconnected"


def test_login_invalid_credentials(client, auth, cognito_fake, keyring_fake):
    cognito_fake.error["InitiateAuth"] = (400, "NotAuthorizedException", "Incorrect username or password.")
    resp = _login(client, auth)
    assert resp.status_code == 401 and resp.json()["error"]["code"] == "invalid_credentials"
    assert keyring_fake.store == {}
    assert client.get("/session", headers=auth).json()["signed_in"] is False


def test_login_service_unreachable(client, auth, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr("app.auth.cognito.httpx.post", boom)
    resp = _login(client, auth)
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "service_unavailable"


def test_login_requires_configuration(client, auth, monkeypatch):
    monkeypatch.setattr("app.config.COGNITO_CLIENT_ID", "")
    assert _login(client, auth).status_code == 503


def test_logout_deletes_keychain_entry_and_clears_memory(client, auth, cognito_fake, keyring_fake):
    _login(client, auth)
    resp = client.post("/auth/logout", headers=auth)
    assert resp.status_code == 204
    assert keyring_fake.store == {}
    assert session.is_signed_in() is False and session.email() is None
    assert client.get("/session", headers=auth).json()["signed_in"] is False


def test_keychain_failure_falls_back_to_memory(client, auth, cognito_fake, keyring_fake):
    keyring_fake.broken = True
    assert _login(client, auth).status_code == 200
    assert keystore.persistent is False
    assert keystore.load() == ("a@firm.com", "refresh-1")
    assert client.post("/auth/logout", headers=auth).status_code == 204
    assert keystore.load() is None


def test_restore_from_keychain(cognito_fake, keyring_fake):
    keystore.save("a@firm.com", "refresh-1")
    session.restore_from_keychain()
    assert session.is_signed_in() and session.email() == "a@firm.com"
    assert cognito_fake.calls[-1][1]["AuthFlow"] == "REFRESH_TOKEN_AUTH"


def test_restore_without_stored_token(cognito_fake, keyring_fake):
    session.restore_from_keychain()
    assert not session.is_signed_in() and cognito_fake.calls == []


def test_restore_with_revoked_token_signs_out_and_clears_entry(cognito_fake, keyring_fake):
    keystore.save("a@firm.com", "revoked")
    cognito_fake.error["InitiateAuth"] = (400, "NotAuthorizedException", "Refresh Token has been revoked")
    session.restore_from_keychain()
    assert not session.is_signed_in() and keyring_fake.store == {}


def test_restore_keeps_entry_when_cognito_unreachable(cognito_fake, keyring_fake):
    keystore.save("a@firm.com", "refresh-1")
    cognito_fake.error["InitiateAuth"] = (500, "InternalErrorException", "")
    session.restore_from_keychain()
    assert not session.is_signed_in() and keyring_fake.store


@pytest.mark.parametrize("kind", ["TooManyRequestsException", "LimitExceededException"])
def test_login_rate_limit_is_429(client, auth, cognito_fake, keyring_fake, kind):
    cognito_fake.error["InitiateAuth"] = (400, kind, "Attempt limit exceeded")
    resp = _login(client, auth)
    assert resp.status_code == 429 and resp.json()["error"]["code"] == "too_many_attempts"


LONG_TOKEN = "r" * 2500  # real Cognito refresh tokens exceed one Credential Manager blob


def test_long_refresh_token_roundtrips_in_chunks(keyring_fake):
    keyring_fake.max_len = 1280
    keystore.save("a@firm.com", LONG_TOKEN)
    assert keystore.persistent is True
    assert keystore.load() == ("a@firm.com", LONG_TOKEN)
    keystore.delete()
    assert keyring_fake.store == {} and keystore.load() is None


def test_shrinking_token_removes_old_chunks(keyring_fake):
    keystore.save("a@firm.com", LONG_TOKEN)
    keystore.save("a@firm.com", "short")
    assert keystore.load() == ("a@firm.com", "short")
    assert len(keyring_fake.store) == 2  # one chunk plus the index


def test_stale_entry_is_replaced_when_keychain_save_fails_midway(keyring_fake):
    keystore.save("a@firm.com", "old-token")
    original = keyring_fake.set_password
    keyring_fake.set_password = lambda *a: (_ for _ in ()).throw(RuntimeError("full"))
    keystore.save("b@firm.com", "new-token")
    keyring_fake.set_password = original
    assert keystore.load() == ("b@firm.com", "new-token")  # memory wins over the old keychain entry
    assert keyring_fake.store == {}  # old user's entry was cleared
