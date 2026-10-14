import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

from common import bedrock  # noqa: E402

SECRET_PROMPT = "super secret excerpt text"


class FakeClient:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.calls = text, error, []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"output": {"message": {"content": [{"text": self.text}]}}}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model-id")

    def install(text=None, error=None):
        fake = FakeClient(text, error)
        monkeypatch.setattr(bedrock, "_get_client", lambda: fake)
        return fake

    return install


def test_returns_parsed_json_and_uses_configured_model(client):
    fake = client('{"tags": ["a"]}')
    assert bedrock.invoke_json("system", SECRET_PROMPT, max_tokens=50) == {"tags": ["a"]}
    call = fake.calls[0]
    assert call["modelId"] == "test-model-id"
    assert call["inferenceConfig"] == {"maxTokens": 50}  # Sonnet 5.5 rejects `temperature`
    assert call["system"] == [{"text": "system"}]
    assert call["messages"][0]["content"] == [{"text": SECRET_PROMPT}]


@pytest.mark.parametrize("text", ['```json\n{"a": 1}\n```', '```\n{"a": 1}\n```', '  {"a": 1}  '])
def test_strips_code_fences_and_whitespace(client, text):
    client(text)
    assert bedrock.invoke_json("s", "u") == {"a": 1}


@pytest.mark.parametrize("text", ["", "not json", "[1, 2]", '"just a string"', "null"])
def test_bad_replies_raise_bedrock_unavailable(client, text):
    client(text)
    with pytest.raises(bedrock.BedrockUnavailable):
        bedrock.invoke_json("s", "u")


def test_service_errors_raise_bedrock_unavailable(client):
    client(error=TimeoutError("read timeout"))
    with pytest.raises(bedrock.BedrockUnavailable):
        bedrock.invoke_json("s", "u")


def test_missing_model_id_is_unavailable_not_a_crash(client, monkeypatch):
    client('{"a": 1}')
    monkeypatch.delenv("BEDROCK_MODEL_ID")
    with pytest.raises(bedrock.BedrockUnavailable):
        bedrock.invoke_json("s", "u")


def test_nothing_from_the_prompt_or_reply_is_logged(client, capsys):
    client(error=RuntimeError(f"boom {SECRET_PROMPT}"))
    with pytest.raises(bedrock.BedrockUnavailable):
        bedrock.invoke_json("s", SECRET_PROMPT)
    client(f'not json {SECRET_PROMPT}')
    with pytest.raises(bedrock.BedrockUnavailable):
        bedrock.invoke_json("s", SECRET_PROMPT)
    out = capsys.readouterr()
    assert SECRET_PROMPT not in out.out + out.err
    assert "RuntimeError" in out.out


LLM_FN_TIMEOUT_SECONDS = 25  # LlmFn in infra/stack.py


def test_worst_case_call_time_fits_inside_the_lambda_timeout():
    worst = (bedrock.CONNECT_TIMEOUT + bedrock.READ_TIMEOUT) * (bedrock.RETRIES + 1)
    assert worst < LLM_FN_TIMEOUT_SECONDS


def test_the_client_uses_the_budgeted_timeouts(monkeypatch):
    import boto3

    seen = {}
    monkeypatch.setattr(bedrock, "_client", None)
    monkeypatch.setattr(boto3, "client", lambda service, config=None: seen.update(service=service, config=config))
    bedrock._get_client()
    assert seen["service"] == "bedrock-runtime"
    assert seen["config"].read_timeout == bedrock.READ_TIMEOUT
    assert seen["config"].connect_timeout == bedrock.CONNECT_TIMEOUT
    assert seen["config"].retries["max_attempts"] == bedrock.RETRIES
