from app import config
from app.main import app


def _assert_envelope(resp, status, code):
    assert resp.status_code == status
    body = resp.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert "message" in body["error"] and isinstance(body["error"]["details"], dict)


def test_token_required(client):
    _assert_envelope(client.get("/session"), 401, "unauthorized")
    _assert_envelope(client.get("/session", headers={"X-HiveMind-Token": "wrong"}), 401, "unauthorized")


def test_token_endpoint_needs_no_token_but_checks_origin(client):
    ok = client.get("/auth/token", headers={"Origin": config.FRONTEND_ORIGIN})
    assert ok.status_code == 200 and ok.json()["token"]
    _assert_envelope(client.get("/auth/token", headers={"Origin": "http://evil.example"}), 403, "forbidden")
    _assert_envelope(client.get("/auth/token"), 403, "forbidden")


def test_cors_only_allows_frontend_origin(client):
    pre = client.options("/session", headers={
        "Origin": config.FRONTEND_ORIGIN,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-HiveMind-Token",
    })
    assert pre.headers["access-control-allow-origin"] == config.FRONTEND_ORIGIN
    bad = client.options("/session", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers


def test_not_found_uses_envelope(client, auth):
    _assert_envelope(client.get("/nope", headers=auth), 404, "not_found")


def test_validation_error_uses_envelope_and_omits_values(client, auth):
    resp = client.post("/auth/login", headers=auth, json={"email": "a@b.com", "password": 5})
    _assert_envelope(resp, 400, "invalid_request")
    assert resp.json()["error"]["details"] == {"fields": ["password"]}
    _assert_envelope(client.post("/auth/login", headers=auth, json={}), 400, "invalid_request")


def test_unhandled_error_uses_envelope(client, auth):
    @app.get("/_boom")
    def boom():
        raise RuntimeError("secret detail")

    resp = client.get("/_boom", headers=auth)
    _assert_envelope(resp, 500, "internal_error")
    assert "secret" not in resp.text


def test_binds_to_loopback():
    assert config.HOST == "127.0.0.1"


def test_cors_headers_present_on_token_rejection(client):
    resp = client.get("/session", headers={"Origin": config.FRONTEND_ORIGIN})
    assert resp.status_code == 401
    assert resp.headers["access-control-allow-origin"] == config.FRONTEND_ORIGIN
