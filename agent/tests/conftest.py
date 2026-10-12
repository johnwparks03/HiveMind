import os

os.environ.setdefault("HIVEMIND_FAKE_EMBEDDINGS", "1")

import httpx
import pytest
from fastapi.testclient import TestClient

from app import config
from app.auth import keystore, session
from app.auth.security import STARTUP_TOKEN
from app.main import app


class FakeKeyring:
    def __init__(self):
        self.store = {}
        self.broken = False
        self.max_len = None  # simulate Credential Manager's blob size limit

    def _check(self):
        if self.broken:
            raise RuntimeError("keychain unavailable")

    def set_password(self, service, user, value):
        self._check()
        if self.max_len is not None and len(value) > self.max_len:
            raise RuntimeError("credential too large")
        self.store[(service, user)] = value

    def get_password(self, service, user):
        self._check()
        return self.store.get((service, user))

    def delete_password(self, service, user):
        self._check()
        self.store.pop((service, user), None)


class FakeCognito:
    """Stands in for httpx.post in app.auth.cognito. Records calls; replies per target."""

    def __init__(self):
        self.calls = []
        self.error = {}  # target -> (status, exception type, message)
        self.expires_in = 3600

    def __call__(self, url, json=None, headers=None, timeout=None):
        target = headers["X-Amz-Target"].rsplit(".", 1)[-1]
        self.calls.append((target, json))
        if target in self.error:
            status, kind, message = self.error[target]
            return httpx.Response(status, json={"__type": kind, "message": message})
        if target == "SignUp":
            return httpx.Response(200, json={"UserConfirmed": True})
        result = {"AccessToken": f"access-{len(self.calls)}", "IdToken": "id", "ExpiresIn": self.expires_in}
        if json["AuthFlow"] == "USER_PASSWORD_AUTH":
            result["RefreshToken"] = "refresh-1"
        return httpx.Response(200, json={"AuthenticationResult": result})


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(config, "COGNITO_CLIENT_ID", "test-client")
    monkeypatch.setattr(config, "CENTRAL_API_URL", "https://central.test")
    monkeypatch.setattr(config, "CENTRAL_HEALTH_CACHE_SECONDS", 0)
    yield
    session._email = session._refresh_token = session._access_token = None
    session._expires_at = 0.0
    keystore._memory.clear()
    keystore.persistent = True


@pytest.fixture
def keyring_fake(monkeypatch):
    fake = FakeKeyring()
    monkeypatch.setattr(keystore, "keyring", fake)
    return fake


@pytest.fixture
def cognito_fake(monkeypatch):
    fake = FakeCognito()
    monkeypatch.setattr("app.auth.cognito.httpx.post", fake)
    return fake


@pytest.fixture
def client():
    # No `with`: skips the lifespan (DB init and keychain restore).
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth():
    return {"X-HiveMind-Token": STARTUP_TOKEN}
