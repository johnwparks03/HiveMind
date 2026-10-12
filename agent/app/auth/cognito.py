"""Unauthenticated Cognito calls (SignUp, InitiateAuth). Plain HTTPS, so the agent
holds no AWS credentials (CLAUDE.md architecture rules). Never log bodies or tokens.
"""
import httpx

from app import config
from app.errors import ApiError

_CONTENT_TYPE = "application/x-amz-json-1.1"


def _post(target: str, payload: dict) -> dict:
    if not config.COGNITO_CLIENT_ID:
        raise ApiError(503, "service_unavailable",
                       "sign-in is not configured: set HIVEMIND_COGNITO_CLIENT_ID in agent/.env",
                       {"missing": "HIVEMIND_COGNITO_CLIENT_ID"})
    url = f"https://cognito-idp.{config.COGNITO_REGION}.amazonaws.com/"
    headers = {"Content-Type": _CONTENT_TYPE, "X-Amz-Target": f"AWSCognitoIdentityProviderService.{target}"}
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=config.CENTRAL_TIMEOUT_SECONDS)
    except httpx.HTTPError:
        raise ApiError(503, "service_unavailable", "could not reach the sign-in service") from None
    if resp.status_code == 200:
        return resp.json()
    try:
        body = resp.json()
    except ValueError:
        body = {}
    raise _map_error(str(body.get("__type", "")).split("#")[-1], str(body.get("message", "")))


def _map_error(kind: str, message: str) -> ApiError:
    if kind == "UsernameExistsException":
        return ApiError(409, "user_exists", "an account with this email already exists")
    if kind == "InvalidPasswordException":
        return ApiError(400, "password_policy", "password does not meet the policy", {"message": message})
    if kind in ("NotAuthorizedException", "UserNotFoundException"):
        return ApiError(401, "invalid_credentials", "incorrect email or password")
    if kind in ("TooManyRequestsException", "LimitExceededException", "TooManyFailedAttemptsException"):
        return ApiError(429, "too_many_attempts", "too many attempts, try again later")
    if kind in ("UserNotConfirmedException", "PasswordResetRequiredException"):
        return ApiError(401, "invalid_credentials", "this account cannot sign in yet", {"reason": kind})
    if kind in ("InvalidParameterException", "UserLambdaValidationException"):
        return ApiError(400, "invalid_request", "sign-in service rejected the request", {"message": message})
    return ApiError(503, "service_unavailable", "sign-in service unavailable")


def sign_up(email: str, password: str) -> None:
    _post("SignUp", {
        "ClientId": config.COGNITO_CLIENT_ID,
        "Username": email,
        "Password": password,
        "UserAttributes": [{"Name": "email", "Value": email}],
    })


def password_login(email: str, password: str) -> dict:
    """Returns the AuthenticationResult (AccessToken, IdToken, RefreshToken, ExpiresIn)."""
    out = _post("InitiateAuth", {
        "ClientId": config.COGNITO_CLIENT_ID,
        "AuthFlow": "USER_PASSWORD_AUTH",
        "AuthParameters": {"USERNAME": email, "PASSWORD": password},
    })
    result = out.get("AuthenticationResult")
    if not result:
        raise ApiError(503, "service_unavailable", "unexpected sign-in response")
    return result


def refresh(refresh_token: str) -> dict:
    """Returns the AuthenticationResult (no new RefreshToken)."""
    out = _post("InitiateAuth", {
        "ClientId": config.COGNITO_CLIENT_ID,
        "AuthFlow": "REFRESH_TOKEN_AUTH",
        "AuthParameters": {"REFRESH_TOKEN": refresh_token},
    })
    result = out.get("AuthenticationResult")
    if not result:
        raise ApiError(503, "service_unavailable", "unexpected sign-in response")
    return result
