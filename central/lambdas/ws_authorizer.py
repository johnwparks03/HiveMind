"""Lambda authorizer for the relay WebSocket's $connect route (Interface C).

Validates the Cognito ACCESS token sent as `Authorization: Bearer <token>` and passes the
`sub` to $connect as authorizer context. Runs outside the VPC (it must reach Cognito's JWKS
URL and the VPC subnets have no NAT). Never logs the event, headers or token.
"""
import json
import os
import urllib.request

import jwt

_jwks = None


def _issuer():
    return (f"https://cognito-idp.{os.environ['AWS_REGION']}.amazonaws.com/"
            f"{os.environ['USER_POOL_ID']}")


def _fetch_jwks():
    with urllib.request.urlopen(_issuer() + "/.well-known/jwks.json", timeout=5) as resp:
        return json.load(resp)["keys"]


def _signing_key(token):
    """The pool's public key for this token's `kid`. The JWKS is cached per container and
    refetched once if the kid is unknown (key rotation)."""
    global _jwks
    kid = jwt.get_unverified_header(token).get("kid")
    for attempt in range(2):
        if _jwks is None or attempt:
            _jwks = _fetch_jwks()
        for key in _jwks:
            if key.get("kid") == kid:
                return jwt.PyJWK(key).key
    raise jwt.InvalidTokenError("unknown signing key")


def validate(token):
    """Return the token's `sub`, or raise jwt.InvalidTokenError."""
    claims = jwt.decode(
        token, _signing_key(token), algorithms=["RS256"], issuer=_issuer(),
        options={"require": ["exp", "iss", "sub"], "verify_aud": False},
    )
    # Access tokens carry client_id, not aud; an ID token must not open a connection.
    if claims.get("token_use") != "access" or claims.get("client_id") != os.environ["USER_POOL_CLIENT_ID"]:
        raise jwt.InvalidTokenError("wrong token type or client")
    return claims["sub"]


def _policy(effect, method_arn, context=None):
    return {
        "principalId": (context or {}).get("user_id", "anonymous"),
        "policyDocument": {"Version": "2012-10-17", "Statement": [
            {"Action": "execute-api:Invoke", "Effect": effect, "Resource": method_arn}]},
        "context": context or {},
    }


def handler(event, context):
    header = (event.get("headers") or {})
    value = next((v for k, v in header.items() if k.lower() == "authorization"), "")
    scheme, _, token = value.partition(" ")
    try:
        if scheme.lower() != "bearer" or not token:
            raise jwt.InvalidTokenError("no bearer token")
        return _policy("Allow", event["methodArn"], {"user_id": validate(token)})
    except (jwt.InvalidTokenError, OSError, ValueError, KeyError) as exc:
        # Fail closed. Log only the exception type: messages can echo token fragments.
        print(f"ws authorizer denied: {type(exc).__name__}")
        return _policy("Deny", event["methodArn"])
