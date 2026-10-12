import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

from common.auth import get_caller_sub  # noqa: E402
from common.errors import Unauthorized, error_response, unauthorized_response  # noqa: E402


def _event(claims):
    return {"requestContext": {"authorizer": {"jwt": {"claims": claims}}}}


def test_get_caller_sub_returns_sub():
    assert get_caller_sub(_event({"sub": "abc-123"})) == "abc-123"


@pytest.mark.parametrize("event", [
    {},
    {"requestContext": {}},
    {"requestContext": {"authorizer": {}}},
    _event({}),
    _event({"sub": ""}),
    {"requestContext": None},
])
def test_get_caller_sub_fails_closed(event):
    with pytest.raises(Unauthorized):
        get_caller_sub(event)


def test_error_response_uses_contract_envelope():
    resp = error_response(409, "conflict", "msg", {"k": "v"})
    assert resp["statusCode"] == 409
    assert resp["headers"]["Content-Type"] == "application/json"
    assert json.loads(resp["body"]) == {
        "error": {"code": "conflict", "message": "msg", "details": {"k": "v"}}
    }


def test_error_response_details_default_to_empty_object():
    body = json.loads(error_response(400, "invalid_request", "bad")["body"])
    assert body["error"]["details"] == {}


def test_unauthorized_response_is_401_unauthorized():
    resp = unauthorized_response()
    assert resp["statusCode"] == 401
    assert json.loads(resp["body"])["error"]["code"] == "unauthorized"
