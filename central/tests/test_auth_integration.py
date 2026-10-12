"""Integration tests for E1-S1 against the deployed HiveMind stack.

Run: pytest -m integration
Needs AWS credentials for account 954976288579 / us-east-1. Pool ID, client ID
and API URL come from HIVEMIND_USER_POOL_ID / HIVEMIND_CLIENT_ID / HIVEMIND_API_URL,
or are read from the `HiveMind` CloudFormation stack outputs.
Test users are deleted afterwards. Passwords and tokens are never printed.
"""
import json
import os
import urllib.error
import urllib.request
import uuid

import boto3
import pytest

pytestmark = pytest.mark.integration

REGION = os.environ.get("AWS_REGION", "us-east-1")
STACK_NAME = "HiveMind"
PASSWORD = "Test-Passw0rd-" + uuid.uuid4().hex[:8]


@pytest.fixture(scope="session")
def cfg():
    env = {
        "pool_id": os.environ.get("HIVEMIND_USER_POOL_ID"),
        "client_id": os.environ.get("HIVEMIND_CLIENT_ID"),
        "api_url": os.environ.get("HIVEMIND_API_URL"),
    }
    if not all(env.values()):
        stack = boto3.client("cloudformation", region_name=REGION).describe_stacks(
            StackName=STACK_NAME)["Stacks"][0]
        out = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
        env["pool_id"] = env["pool_id"] or out["UserPoolId"]
        env["client_id"] = env["client_id"] or out["UserPoolClientId"]
        env["api_url"] = env["api_url"] or out["HttpApiUrl"]
    env["api_url"] = env["api_url"].rstrip("/")
    return env


@pytest.fixture(scope="session")
def cognito():
    return boto3.client("cognito-idp", region_name=REGION)


@pytest.fixture
def new_email(cfg, cognito):
    """Yields a unique email; deletes the user afterwards if it was created."""
    email = f"e1s1-{uuid.uuid4().hex[:12]}@example.com"
    yield email
    try:
        cognito.admin_delete_user(UserPoolId=cfg["pool_id"], Username=email)
    except cognito.exceptions.UserNotFoundException:
        pass


def _sign_up(cognito, cfg, email, password=PASSWORD):
    return cognito.sign_up(ClientId=cfg["client_id"], Username=email, Password=password)


def _login(cognito, cfg, email, password=PASSWORD):
    return cognito.initiate_auth(
        ClientId=cfg["client_id"],
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": email, "PASSWORD": password},
    )["AuthenticationResult"]


def _get(url, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_signup_then_login_returns_tokens_including_refresh(cognito, cfg, new_email):
    assert _sign_up(cognito, cfg, new_email)["UserConfirmed"] is True
    tokens = _login(cognito, cfg, new_email)
    assert tokens["AccessToken"] and tokens["IdToken"] and tokens["RefreshToken"]

    refreshed = cognito.initiate_auth(
        ClientId=cfg["client_id"],
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={"REFRESH_TOKEN": tokens["RefreshToken"]},
    )["AuthenticationResult"]
    assert refreshed["AccessToken"]


def test_duplicate_email_raises_username_exists(cognito, cfg, new_email):
    # The agent (E1-S3) maps this exception to 409 `user_exists`.
    _sign_up(cognito, cfg, new_email)
    with pytest.raises(cognito.exceptions.UsernameExistsException):
        _sign_up(cognito, cfg, new_email)


def test_weak_password_raises_invalid_password(cognito, cfg, new_email):
    # The agent maps this to 400 `password_policy`, details = Cognito's message.
    with pytest.raises(cognito.exceptions.InvalidPasswordException) as exc:
        _sign_up(cognito, cfg, new_email, password="short")
    print("Cognito password policy message:", exc.value.response["Error"]["Message"])


def test_wrong_password_raises_not_authorized(cognito, cfg, new_email):
    # The agent maps this to 401 `invalid_credentials`.
    _sign_up(cognito, cfg, new_email)
    with pytest.raises(cognito.exceptions.NotAuthorizedException):
        _login(cognito, cfg, new_email, password="Wrong-Passw0rd-x")


def test_protected_route_accepts_access_token_and_returns_sub(cognito, cfg, new_email):
    _sign_up(cognito, cfg, new_email)
    tokens = _login(cognito, cfg, new_email)
    expected_sub = cognito.admin_get_user(
        UserPoolId=cfg["pool_id"], Username=new_email
    )["UserAttributes"]
    expected_sub = next(a["Value"] for a in expected_sub if a["Name"] == "sub")

    status, body = _get(f"{cfg['api_url']}/hello", tokens["AccessToken"])
    assert status == 200
    assert body["sub"] == expected_sub


def test_protected_route_rejects_missing_and_garbage_token(cfg):
    url = f"{cfg['api_url']}/hello"

    assert _get(url)[0] == 401
    assert _get(url, "not-a-jwt")[0] == 401


def test_authorizer_also_accepts_id_token(cognito, cfg, new_email):
    # Documents actual gateway behavior: the JWT authorizer matches its audience
    # against `aud` (ID token) or `client_id` (access token), so BOTH pass.
    # "Agent sends the access token" (E0-S3) is a convention, not enforced here.
    _sign_up(cognito, cfg, new_email)
    tokens = _login(cognito, cfg, new_email)
    status, _ = _get(f"{cfg['api_url']}/hello", tokens["IdToken"])
    assert status == 200


def test_health_is_open(cfg):
    status, body = _get(f"{cfg['api_url']}/health")
    assert status == 200
    assert body["status"] == "ok"
