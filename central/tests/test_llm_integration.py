"""Integration tests for E3-S3 against the deployed HiveMind stack.

Run: pytest -m integration   (needs `aws login`; the stack must include LlmFn)
Creates a throwaway Cognito user (no team needed) and makes one real Bedrock call.
Tokens and excerpts are never printed.
"""
import re

import pytest

from test_auth_integration import cfg, cognito  # noqa: F401
from test_teams_integration import _call, _error_code, make_user  # noqa: F401

pytestmark = pytest.mark.integration

EXCERPT = (
    "Master Services Agreement renewal for Contoso, effective 1 January. Pricing schedule, "
    "service levels and termination clauses are updated for the new term. Legal review of "
    "the indemnification wording is outstanding before the client signs. " * 3
)


def test_tags_for_a_realistic_excerpt_without_a_team(cfg, make_user):  # noqa: F811
    token = make_user()  # a brand-new user with no team: /llm/tags requires login only
    status, body = _call(cfg, "POST", "/llm/tags", token,
                         {"filename": "Contoso_MSA_Renewal.docx", "excerpt": EXCERPT})
    assert status == 200
    tags = body["tags"]
    assert 5 <= len(tags) <= 8 and len(set(tags)) == len(tags)
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9 -]{0,39}", t) for t in tags)


def test_missing_excerpt_is_400_naming_the_field(cfg, make_user):  # noqa: F811
    token = make_user()
    status, body = _call(cfg, "POST", "/llm/tags", token, {"filename": "a.docx"})
    assert status == 400 and _error_code(body) == "invalid_request"
    assert body["error"]["details"]["fields"] == ["excerpt"]


def test_oversized_excerpt_is_400(cfg, make_user):  # noqa: F811
    token = make_user()
    status, body = _call(cfg, "POST", "/llm/tags", token,
                         {"filename": "a.docx", "excerpt": "word " * 7000})  # 35,000 > 30,000
    assert status == 400 and body["error"]["details"]["fields"] == ["excerpt"]


def test_requests_without_a_token_are_rejected(cfg):  # noqa: F811
    assert _call(cfg, "POST", "/llm/tags", "not-a-token", {"filename": "a", "excerpt": "b"})[0] == 401
