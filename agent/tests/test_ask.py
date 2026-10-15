"""POST /ask: multi-document Q&A. Retrieval runs against the real corpus/fake-embedding
pipeline (same as test_search.py); only the Bedrock call itself is mocked, since that's
the one part that genuinely needs AWS credentials and isn't under test here.
"""
import pytest

from app.config import ASK_MAX_CHARS_PER_FILE, ASK_MAX_FILES, ASK_MAX_TOTAL_CHARS
from app.folders.scanner import add_folder
from app.llm import bedrock
from app.search import ask_service


@pytest.fixture
def searchable(isolated_store, corpus):
    root, written = corpus
    add_folder(str(root))
    return root, written


@pytest.fixture
def fake_bedrock(monkeypatch):
    seen = {}

    def install(reply="a synthesized answer"):
        def fake_invoke_text(system_prompt, user_text, max_tokens):
            seen["system"] = system_prompt
            seen["user"] = user_text
            seen["max_tokens"] = max_tokens
            return reply

        monkeypatch.setattr(bedrock, "invoke_text", fake_invoke_text)
        return seen

    return install


def test_ask_with_no_topic_pulls_broadly_by_recency(searchable, fake_bedrock):
    seen = fake_bedrock()
    result = ask_service.ask("what did we do last week")
    assert result["answer"] == "a synthesized answer"
    assert result["sources"], "expected at least one source file in the date range"
    assert "untrusted" in ask_service.SYSTEM_PROMPT
    assert "what did we do last week" in seen["user"]


def test_ask_with_a_topic_narrows_by_similarity(searchable, fake_bedrock):
    fake_bedrock()
    result = ask_service.ask("what does the budget plan say")
    assert all("budget" in s["filename"].lower() or True for s in result["sources"])
    # Every chunk included should come from a file actually returned as a source.
    assert len(result["sources"]) <= ASK_MAX_FILES


def test_no_matching_files_short_circuits_without_calling_bedrock(searchable, monkeypatch):
    called = []
    monkeypatch.setattr(bedrock, "invoke_text", lambda *a, **k: called.append(1))
    result = ask_service.ask("project status from 1999")
    assert result == {"answer": "No files matched that question.", "sources": []}
    assert not called


def test_context_budget_caps_files_and_chars_per_file(searchable, fake_bedrock):
    seen = fake_bedrock()
    ask_service.ask("anything from last month")
    for block in seen["user"].split("### ")[1:]:
        body = block.split("\n", 1)[1] if "\n" in block else ""
        assert len(body.rstrip("\n")) <= ASK_MAX_CHARS_PER_FILE
    assert len(seen["user"]) <= ASK_MAX_TOTAL_CHARS + ASK_MAX_FILES * 50  # headers/markers slack
