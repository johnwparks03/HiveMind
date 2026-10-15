import json
import os
import sys
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import ws_authorizer  # noqa: E402

POOL = "us-east-1_TestPool"
CLIENT = "client-123"
ISSUER = f"https://cognito-idp.us-east-1.amazonaws.com/{POOL}"
METHOD_ARN = "arn:aws:execute-api:us-east-1:111:abc/dev/$connect"

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwk(key, kid):
    data = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    return {**data, "kid": kid, "alg": "RS256", "use": "sig"}


def _token(key=KEY, kid="k1", **overrides):
    claims = {"sub": "user-1", "iss": ISSUER, "token_use": "access", "client_id": CLIENT,
              "exp": int(time.time()) + 300}
    claims.update(overrides)
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key,
                      algorithm="RS256", headers={"kid": kid})


def _event(token=None, header="Authorization"):
    headers = {header: f"Bearer {token}"} if token else {}
    return {"headers": headers, "methodArn": METHOD_ARN}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("USER_POOL_ID", POOL)
    monkeypatch.setenv("USER_POOL_CLIENT_ID", CLIENT)
    monkeypatch.setattr(ws_authorizer, "_jwks", None)
    fetches = []

    def fake_fetch():
        fetches.append(1)
        return [_jwk(KEY, "k1")]

    monkeypatch.setattr(ws_authorizer, "_fetch_jwks", fake_fetch)
    return fetches


def _effect(result):
    return result["policyDocument"]["Statement"][0]["Effect"]


def test_valid_token_allows_and_passes_sub():
    result = ws_authorizer.handler(_event(_token()), None)
    assert _effect(result) == "Allow"
    assert result["context"] == {"user_id": "user-1"}
    assert result["policyDocument"]["Statement"][0]["Resource"] == METHOD_ARN


def test_header_name_is_case_insensitive():
    assert _effect(ws_authorizer.handler(_event(_token(), header="authorization"), None)) == "Allow"


@pytest.mark.parametrize("event", [
    {"headers": {}, "methodArn": METHOD_ARN},
    {"headers": None, "methodArn": METHOD_ARN},
    {"headers": {"Authorization": "Bearer"}, "methodArn": METHOD_ARN},
    {"headers": {"Authorization": "Basic abc"}, "methodArn": METHOD_ARN},
    {"headers": {"Authorization": "Bearer not.a.jwt"}, "methodArn": METHOD_ARN},
])
def test_missing_or_malformed_header_denies(event):
    assert _effect(ws_authorizer.handler(event, None)) == "Deny"


@pytest.mark.parametrize("token", [
    _token(exp=int(time.time()) - 10),
    _token(iss="https://cognito-idp.us-east-1.amazonaws.com/other"),
    _token(client_id="someone-else"),
    _token(token_use="id"),
    _token(key=OTHER_KEY),
    _token(kid="unknown-kid"),
    _token(sub=None),
], ids=["expired", "wrong-issuer", "wrong-client", "id-token", "bad-signature", "unknown-kid",
        "no-sub"])
def test_invalid_tokens_deny(token):
    result = ws_authorizer.handler(_event(token), None)
    assert _effect(result) == "Deny"
    assert result["context"] == {}


def test_jwks_failure_denies(monkeypatch):
    def boom():
        raise OSError("network down")

    monkeypatch.setattr(ws_authorizer, "_fetch_jwks", boom)
    assert _effect(ws_authorizer.handler(_event(_token()), None)) == "Deny"


def test_jwks_is_cached_across_calls(env):
    ws_authorizer.handler(_event(_token()), None)
    ws_authorizer.handler(_event(_token()), None)
    assert len(env) == 1


def test_unknown_kid_refetches_once_for_key_rotation(monkeypatch, env):
    ws_authorizer.handler(_event(_token()), None)
    monkeypatch.setattr(ws_authorizer, "_fetch_jwks",
                        lambda: [_jwk(KEY, "k1"), _jwk(OTHER_KEY, "k2")])
    assert _effect(ws_authorizer.handler(_event(_token(key=OTHER_KEY, kid="k2")), None)) == "Allow"


def test_denial_log_never_contains_the_token(capsys):
    token = _token(token_use="id")
    ws_authorizer.handler(_event(token), None)
    out = capsys.readouterr().out
    assert token not in out and "Bearer" not in out
