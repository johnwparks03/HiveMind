"""Unset Cognito / central settings must fail gracefully (503), never crash the agent."""
import pytest

from app import config
from app.auth import keystore, session
from app.central import client as central_client
from app.errors import ApiError


@pytest.fixture
def unconfigured(monkeypatch):
    monkeypatch.setattr(config, "COGNITO_CLIENT_ID", "")
    monkeypatch.setattr(config, "CENTRAL_API_URL", "")


@pytest.mark.parametrize("path", ["/auth/signup", "/auth/login"])
def test_auth_endpoints_return_503_naming_the_variable(client, auth, unconfigured, path):
    resp = client.post(path, headers=auth, json={"email": "a@firm.com", "password": "x"})
    assert resp.status_code == 503
    err = resp.json()["error"]
    assert err["code"] == "service_unavailable"
    assert err["details"] == {"missing": "HIVEMIND_COGNITO_CLIENT_ID"}


def test_logout_and_session_still_work(client, auth, unconfigured):
    assert client.post("/auth/logout", headers=auth).status_code == 204
    body = client.get("/session", headers=auth).json()
    assert body["agent"] == "ok" and body["signed_in"] is False and body["central_reachable"] is False


def test_central_request_returns_503_when_url_unset(unconfigured):
    with pytest.raises(ApiError) as e:
        central_client.request("GET", "/hello")
    assert e.value.status == 503 and e.value.details == {"missing": "HIVEMIND_CENTRAL_API_URL"}


def test_startup_restore_does_not_crash_or_drop_the_stored_token(unconfigured, keyring_fake):
    keystore.save("a@firm.com", "refresh-1")
    session.restore_from_keychain()
    assert not session.is_signed_in()
    assert keyring_fake.store  # still there once the config is fixed


def test_blank_values_are_treated_as_unset(monkeypatch):
    import importlib

    monkeypatch.setenv("HIVEMIND_COGNITO_CLIENT_ID", "  ")
    monkeypatch.setenv("HIVEMIND_CENTRAL_API_URL", "")
    monkeypatch.setenv("HIVEMIND_COGNITO_REGION", "")
    try:
        reloaded = importlib.reload(config)
        assert reloaded.COGNITO_CLIENT_ID == "" and reloaded.CENTRAL_API_URL == ""
        assert reloaded.COGNITO_REGION == "us-east-1"
    finally:
        monkeypatch.undo()
        importlib.reload(config)
