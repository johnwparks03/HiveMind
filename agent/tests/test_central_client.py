import httpx
import pytest

from app.auth import session
from app.central import client as central_client
from app.errors import ApiError


class FakeCentral:
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.auth_headers = []

    def __call__(self, method, url, headers=None, timeout=None, **kw):
        self.auth_headers.append(headers["Authorization"])
        return httpx.Response(self.statuses.pop(0), json={})


@pytest.fixture
def signed_in(cognito_fake, keyring_fake):
    session.login("a@firm.com", "Passw0rd!x")


def test_not_signed_in_raises_unauthorized():
    with pytest.raises(ApiError) as e:
        central_client.request("GET", "/hello")
    assert e.value.status == 401


def test_attaches_bearer_token(signed_in, monkeypatch):
    fake = FakeCentral([200])
    monkeypatch.setattr("app.central.client.httpx.request", fake)
    central_client.request("GET", "/hello")
    assert fake.auth_headers == ["Bearer access-1"]


def test_refreshes_when_token_near_expiry(cognito_fake, keyring_fake, monkeypatch):
    cognito_fake.expires_in = 30  # inside the refresh margin
    session.login("a@firm.com", "Passw0rd!x")
    fake = FakeCentral([200])
    monkeypatch.setattr("app.central.client.httpx.request", fake)
    central_client.request("GET", "/hello")
    assert cognito_fake.calls[-1][1]["AuthFlow"] == "REFRESH_TOKEN_AUTH"
    assert fake.auth_headers == ["Bearer access-2"]


def test_retries_once_after_401(signed_in, cognito_fake, monkeypatch):
    fake = FakeCentral([401, 200])
    monkeypatch.setattr("app.central.client.httpx.request", fake)
    assert central_client.request("GET", "/hello").status_code == 200
    assert fake.auth_headers == ["Bearer access-1", "Bearer access-2"]


def test_second_401_raises(signed_in, monkeypatch):
    monkeypatch.setattr("app.central.client.httpx.request", FakeCentral([401, 401]))
    with pytest.raises(ApiError) as e:
        central_client.request("GET", "/hello")
    assert e.value.code == "unauthorized"


def test_unreachable_central_is_503(signed_in, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr("app.central.client.httpx.request", boom)
    with pytest.raises(ApiError) as e:
        central_client.request("GET", "/hello")
    assert e.value.status == 503


def test_session_central_reachable(client, auth, monkeypatch):
    monkeypatch.setattr("app.central.client.httpx.get", lambda *a, **k: httpx.Response(200, json={}))
    assert client.get("/session", headers=auth).json()["central_reachable"] is True

    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr("app.central.client.httpx.get", boom)
    assert client.get("/session", headers=auth).json()["central_reachable"] is False


def test_health_check_is_cached(monkeypatch):
    from app import config

    monkeypatch.setattr(config, "CENTRAL_HEALTH_CACHE_SECONDS", 60)
    monkeypatch.setattr("app.central.client._health", (0.0, False))
    calls = []

    def fake_get(*a, **k):
        calls.append(1)
        return httpx.Response(200, json={})

    monkeypatch.setattr("app.central.client.httpx.get", fake_get)
    assert central_client.is_reachable() and central_client.is_reachable()
    assert len(calls) == 1
