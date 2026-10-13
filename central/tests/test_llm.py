import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import llm  # noqa: E402
from common import bedrock  # noqa: E402

SECRET = "CONFIDENTIAL-EXCERPT-MARKER"
GOOD = ["contracts", "renewal", "pricing", "client", "legal", "q3"]


@pytest.fixture(autouse=True)
def small_cap(monkeypatch):
    monkeypatch.setenv("EXCERPT_MAX_CHARS", "100")


@pytest.fixture
def model(monkeypatch):
    seen = {}

    def install(reply=None, error=None):
        def fake_invoke(system_prompt, user_text, max_tokens=300):
            seen["system"], seen["user"], seen["max_tokens"] = system_prompt, user_text, max_tokens
            if error:
                raise error
            return reply

        monkeypatch.setattr(llm.bedrock, "invoke_json", fake_invoke)
        return seen

    return install


def _event(body, route="POST /llm/tags", authed=True):
    event = {"routeKey": route, "body": json.dumps(body) if body is not None else None}
    if authed:
        event["requestContext"] = {"authorizer": {"jwt": {"claims": {"sub": "user-1"}}}}
    return event


def _call(body, **kwargs):
    return llm.handler(_event(body, **kwargs), None)


def _json(resp):
    return json.loads(resp["body"])


def test_happy_path_returns_tags_and_never_needs_a_team(model):
    seen = model({"tags": GOOD})
    resp = _call({"filename": "Q3 contracts.docx", "excerpt": "renewal terms"})
    assert resp["statusCode"] == 200 and _json(resp) == {"tags": GOOD}
    assert "Q3 contracts.docx" in seen["user"] and "renewal terms" in seen["user"]
    assert "untrusted" in seen["system"]


def test_excerpt_over_the_cap_is_truncated_before_the_model_sees_it(model):
    seen = model({"tags": GOOD})
    resp = _call({"filename": "a.txt", "excerpt": "Q" * 100 + "TAILMARKER" + "Z" * 400})
    assert resp["statusCode"] == 200
    assert "TAILMARKER" not in seen["user"] and seen["user"].count("Q") == 100
    assert "Z" not in seen["user"]


def test_excerpt_far_over_the_cap_is_400(model):
    model({"tags": GOOD})
    resp = _call({"filename": "a.txt", "excerpt": "x" * 1001})
    assert resp["statusCode"] == 400
    err = _json(resp)["error"]
    assert err["code"] == "invalid_request" and err["details"]["fields"] == ["excerpt"]


@pytest.mark.parametrize("body,fields", [
    ({"excerpt": "text"}, ["filename"]),
    ({"filename": "  ", "excerpt": "text"}, ["filename"]),
    ({"filename": 5, "excerpt": "text"}, ["filename"]),
    ({"filename": "a" * 300, "excerpt": "text"}, ["filename"]),
    ({"filename": "a.txt"}, ["excerpt"]),
    ({"filename": "a.txt", "excerpt": 7}, ["excerpt"]),
    ({}, ["filename", "excerpt"]),
])
def test_validation_names_fields_only(model, body, fields):
    model({"tags": GOOD})
    resp = _call(body)
    assert resp["statusCode"] == 400 and _json(resp)["error"]["details"]["fields"] == fields


def test_empty_excerpt_is_allowed(model):
    model({"tags": GOOD})
    assert _call({"filename": "a.txt", "excerpt": ""})["statusCode"] == 200


def test_malformed_json_is_400(model):
    model({"tags": GOOD})
    event = _event(None)
    event["body"] = "{nope"
    assert llm.handler(event, None)["statusCode"] == 400


def test_tags_are_lowercased_trimmed_deduplicated_and_capped_at_eight(model):
    model({"tags": ["  Contracts ", "contracts", "Renewal", "pricing", "client", "legal", "q3",
                    "finance", "extra-one", "extra-two", "bad_tag!", ""]})
    body = _json(_call({"filename": "a.txt", "excerpt": "t"}))
    assert body["tags"] == ["contracts", "renewal", "pricing", "client", "legal", "q3",
                            "finance", "extra-one"]


@pytest.mark.parametrize("reply", [
    {"tags": ["a", "b", "c", "d"]},           # too few
    {"tags": ["ok1", "ok2", "ok3", "ok4", "Bad_Chars!"]},  # only four valid
    {"tags": "contracts, renewal"},
    {"tags": [1, 2, 3, 4, 5]},
    {"tags": ["a"] * 10},                     # duplicates collapse to one
    {"other": []},
    {},
])
def test_unusable_model_output_is_503(model, reply):
    model(reply)
    resp = _call({"filename": "a.txt", "excerpt": "t"})
    assert resp["statusCode"] == 503 and _json(resp)["error"]["code"] == "service_unavailable"


def test_bedrock_failure_is_503(model):
    model(error=bedrock.BedrockUnavailable())
    resp = _call({"filename": "a.txt", "excerpt": "t"})
    assert resp["statusCode"] == 503 and _json(resp)["error"]["code"] == "service_unavailable"


def test_unauthenticated_is_401(model):
    model({"tags": GOOD})
    assert _call({"filename": "a.txt", "excerpt": "t"}, authed=False)["statusCode"] == 401


def test_unknown_route_is_404(model):
    model({"tags": GOOD})
    assert _call({}, route="POST /llm/other")["statusCode"] == 404


def test_the_excerpt_is_never_logged_or_echoed(model, capsys):
    model({"tags": ["a"]})  # rejected output exercises the logging path
    resp = _call({"filename": "a.txt", "excerpt": SECRET})
    model(error=RuntimeError(f"boom {SECRET}"))
    resp2 = _call({"filename": "a.txt", "excerpt": SECRET})
    out = capsys.readouterr()
    assert SECRET not in out.out + out.err + resp["body"] + resp2["body"]
