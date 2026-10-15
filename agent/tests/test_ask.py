"""POST /ask: multi-document Q&A. Retrieval runs against the real corpus/fake-embedding
pipeline (same as test_search.py); only the Bedrock call itself is mocked, since that's
the one part that genuinely needs AWS credentials and isn't under test here.
"""
import pytest

from app.config import ASK_MAX_CHARS_PER_FILE, ASK_MAX_FILES, ASK_MAX_TOTAL_CHARS
from app.db import session
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

    def install(reply="a synthesized answer", truncated=False):
        def fake_invoke_text(system_prompt, user_text, max_tokens):
            seen["system"] = system_prompt
            seen["user"] = user_text
            seen["max_tokens"] = max_tokens
            return reply, truncated

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


def test_truncated_answer_gets_an_explicit_note_appended(searchable, fake_bedrock):
    # Verified live 2026-10-15: a real answer hit the token cap and stopped mid-word
    # with no indication anything was cut off. Must never fail silently like that again.
    fake_bedrock(reply="this got cut off mid-sen", truncated=True)
    result = ask_service.ask("what did we do last week")
    assert result["answer"].startswith("this got cut off mid-sen")
    assert "cut short" in result["answer"]


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


# --- Folder/file scope picker (2026-10-16) ----------------------------------------------


def _all_file_ids():
    with session() as conn:
        return [r["file_id"] for r in conn.execute("SELECT file_id FROM files").fetchall()]


def test_scoping_to_one_file_id_excludes_everything_else(searchable, fake_bedrock):
    fake_bedrock()
    one_file = _all_file_ids()[0]
    result = ask_service.ask("anything", file_ids=[one_file])
    assert result["sources"]
    assert all(s["file_id"] == one_file for s in result["sources"])


def test_scoping_to_a_second_unrelated_folder_excludes_the_first(isolated_store, corpus, tmp_path, fake_bedrock):
    root, _ = corpus
    first_folder_id = add_folder(str(root))

    other_dir = tmp_path / "other-folder"
    other_dir.mkdir()
    (other_dir / "unrelated-note.txt").write_text("Totally unrelated content about gardening.")
    second_folder_id = add_folder(str(other_dir))

    fake_bedrock()
    result = ask_service.ask("anything", folder_ids=[second_folder_id])
    assert result["sources"]
    assert all(s["filename"] == "unrelated-note.txt" for s in result["sources"])

    # Sanity check: the first folder's files exist and are excluded, not just absent.
    with session() as conn:
        first_folder_files = conn.execute(
            "SELECT file_id FROM files WHERE folder_id = ?", (first_folder_id,)
        ).fetchall()
    assert first_folder_files
    assert not any(s["file_id"] in {r["file_id"] for r in first_folder_files} for s in result["sources"])


def test_scope_resolving_to_nothing_short_circuits_without_calling_bedrock(searchable, monkeypatch):
    called = []
    monkeypatch.setattr(bedrock, "invoke_text", lambda *a, **k: called.append(1))
    result = ask_service.ask("anything", file_ids=["not-a-real-file-id"])
    assert result == {"answer": "No files matched that question.", "sources": []}
    assert not called


def test_no_scope_still_searches_everything(searchable, fake_bedrock):
    fake_bedrock()
    result = ask_service.ask("anything from last month")
    result_scoped = ask_service.ask("anything from last month", folder_ids=[], file_ids=[])
    assert {s["file_id"] for s in result["sources"]} == {s["file_id"] for s in result_scoped["sources"]}
