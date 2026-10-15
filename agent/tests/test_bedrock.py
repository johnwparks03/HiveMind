"""agent/app/llm/bedrock.py. Covers a real bug found verifying /ask live against the
actual Bedrock API (2026-10-15): Sonnet 5.5 can return a `reasoningContent` block
before the `text` block, so content[0] isn't always the reply.
"""
import pytest

from app.llm import bedrock


@pytest.fixture(autouse=True)
def has_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")


class FakeClient:
    def __init__(self, content):
        self.content = content

    def converse(self, **kwargs):
        return {"output": {"message": {"content": self.content}}}


def test_text_block_found_even_after_a_reasoning_block(monkeypatch):
    client = FakeClient([{"reasoningContent": {"text": "thinking..."}}, {"text": "the real answer"}])
    monkeypatch.setattr(bedrock, "_get_client", lambda: client)
    assert bedrock.invoke_text("system", "user", 100) == "the real answer"


def test_text_block_found_when_it_is_first(monkeypatch):
    client = FakeClient([{"text": "the real answer"}])
    monkeypatch.setattr(bedrock, "_get_client", lambda: client)
    assert bedrock.invoke_text("system", "user", 100) == "the real answer"


def test_no_text_block_at_all_raises_unavailable(monkeypatch):
    client = FakeClient([{"reasoningContent": {"text": "thinking..."}}])
    monkeypatch.setattr(bedrock, "_get_client", lambda: client)
    with pytest.raises(bedrock.BedrockUnavailable):
        bedrock.invoke_text("system", "user", 100)


def test_invoke_json_parses_through_a_reasoning_block_too(monkeypatch):
    client = FakeClient([{"reasoningContent": {"text": "thinking..."}}, {"text": '{"tags": ["a", "b"]}'}])
    monkeypatch.setattr(bedrock, "_get_client", lambda: client)
    assert bedrock.invoke_json("system", "user") == {"tags": ["a", "b"]}


def test_missing_credentials_raises_before_touching_the_client(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)

    def _should_not_be_called():
        raise AssertionError("must not create a client without credentials")

    monkeypatch.setattr(bedrock, "_get_client", _should_not_be_called)
    with pytest.raises(Exception) as exc_info:
        bedrock.invoke_text("system", "user", 100)
    assert exc_info.value.details["missing"] == "AWS_ACCESS_KEY_ID"
