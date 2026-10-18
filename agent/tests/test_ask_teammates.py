"""E6-S6, Ask side: answering from teammates' published files through central retrieval.
Chroma holds a few local chunks (fake embeddings); central retrieval and Bedrock are stubbed."""
import pytest

from app import config
from app.auth.security import STARTUP_TOKEN
from app.central import retrieval, teams
from app.errors import ApiError
from app.indexing import vector_store
from app.indexing.embeddings import embed
from app.search import ask_service
from app.search.query_parser import ParsedQuery
from test_publish import central  # noqa: F401  (fixture: signed-in agent, faked central HTTP)

TOPIC = "budget forecast"


def _local(file_id="local1", filename="Local notes.txt", text=TOPIC, index=0):
    vector_store.upsert_chunks(
        file_id, [text], embed([text]),
        {"file_id": file_id, "filename": filename, "file_modified_at_ts": 1.0, "chunk_index": index},
    )


def row(file_id="team1", filename="Team plan.docx", text="teammate text", distance=0.0, chunk_index=0):
    return {"file_id": file_id, "filename": filename, "chunk_index": chunk_index, "text": text,
            "distance": distance}


@pytest.fixture
def stubs(isolated_store, monkeypatch):
    """Topic parsing, central retrieval and Bedrock stubbed; returns what each was called with."""
    state = {"rows": [], "reason": None, "search_calls": [], "bedrock": [],
             "parsed": ParsedQuery(topic=TOPIC, date_from=None, date_to=None)}
    monkeypatch.setattr(ask_service, "parse_query_locally", lambda q: state["parsed"])

    def fake_search(embedding, limit=None):
        state["search_calls"].append(embedding)
        return state["rows"], state["reason"]

    monkeypatch.setattr(ask_service.retrieval, "search", fake_search)

    def fake_invoke(system, user, max_tokens):
        state["bedrock"].append({"system": system, "user": user})
        return "the answer", False

    monkeypatch.setattr(ask_service.bedrock, "invoke_text", fake_invoke)
    return state


def ask(question="what is in the budget forecast", **kwargs):
    return ask_service.ask(question, **kwargs)


# --- the default is unchanged --------------------------------------------------------------


def test_without_include_teammates_central_is_never_called_and_the_shape_is_unchanged(stubs):
    _local()
    result = ask()
    assert stubs["search_calls"] == []
    assert set(result) == {"answer", "sources"}
    assert result["sources"] == [{"file_id": "local1", "filename": "Local notes.txt", "source": "local"}]


# --- merging --------------------------------------------------------------------------------


def test_teammate_chunks_are_merged_labelled_and_flagged(stubs):
    _local(text="unrelated words entirely")
    stubs["rows"] = [row("t1", "Team plan.docx", "plan text", 0.0), row("t1", "Team plan.docx", "more", 0.1, 1)]
    result = ask(include_teammates=True)
    assert result["teammate_skipped_reason"] is None
    assert [(s["file_id"], s["source"]) for s in result["sources"]] == [("t1", "teammate"), ("local1", "local")]
    user = stubs["bedrock"][0]["user"]
    assert "### Team plan.docx (teammate)\nplan text\n\nmore" in user
    assert "### Local notes.txt\n" in user and "(teammate)" not in user.split("### Local notes.txt")[1]
    assert user.index("Team plan.docx") < user.index("Local notes.txt")  # nearest first


def test_a_closer_local_file_ranks_ahead_of_a_teammate_file(stubs):
    _local(text=TOPIC)  # identical to the topic: distance 0
    stubs["rows"] = [row("t1", distance=0.4)]
    result = ask(include_teammates=True)
    assert [s["source"] for s in result["sources"]] == ["local", "teammate"]


def test_the_same_vector_is_used_for_the_local_and_central_search(stubs):
    _local()
    ask(include_teammates=True)
    assert stubs["search_calls"] == [embed([TOPIC])[0]]


def test_the_per_file_caps_apply_to_teammate_files(stubs):
    stubs["rows"] = [row("t1", text="x" * (config.ASK_MAX_CHARS_PER_FILE * 2))]
    ask(include_teammates=True)
    body = stubs["bedrock"][0]["user"].split("### Team plan.docx (teammate)\n")[1].split("\n</excerpts>")[0]
    assert len(body) == config.ASK_MAX_CHARS_PER_FILE


def test_teammates_alone_can_answer_when_no_local_file_matches(stubs):
    stubs["rows"] = [row("t1", text="only a teammate knows this")]
    result = ask(include_teammates=True)
    assert result["answer"] == "the answer" and result["sources"][0]["source"] == "teammate"
    assert stubs["bedrock"]


def test_nothing_anywhere_is_a_no_match_answer_without_calling_the_model(stubs):
    result = ask(include_teammates=True)
    assert result == {"answer": ask_service.NO_MATCH, "sources": [], "teammate_skipped_reason": None}
    assert stubs["bedrock"] == []


def test_the_prompt_covers_teammate_text_and_still_calls_excerpts_untrusted(stubs):
    stubs["rows"] = [row()]
    ask(include_teammates=True)
    system = stubs["bedrock"][0]["system"]
    assert "(teammate)" in system and "untrusted" in system and "teammate files included" in system


# --- when teammates are left out -------------------------------------------------------------


def test_picked_files_narrow_only_the_local_side_teammates_are_still_searched(stubs):
    _local("local1", "Picked.txt")
    _local("local2", "Not picked.txt", text="other words")
    stubs["rows"] = [row("t1", "Team plan.docx", "plan text", 0.0)]
    result = ask(include_teammates=True, file_ids=["local1"])
    assert result["teammate_skipped_reason"] is None and len(stubs["search_calls"]) == 1
    assert {(s["file_id"], s["source"]) for s in result["sources"]} == {("t1", "teammate"), ("local1", "local")}


def test_picks_that_resolve_to_nothing_still_let_teammates_answer(stubs):
    stubs["rows"] = [row("t1", text="only a teammate knows this")]
    result = ask(include_teammates=True, folder_ids=["no-such-folder"])
    assert result["teammate_skipped_reason"] is None
    assert [s["source"] for s in result["sources"]] == ["teammate"] and stubs["bedrock"]


def test_picks_that_resolve_to_nothing_and_no_teammate_match_is_a_no_match(stubs):
    result = ask(include_teammates=True, folder_ids=["no-such-folder"])
    assert result == {"answer": ask_service.NO_MATCH, "sources": [], "teammate_skipped_reason": None}
    assert stubs["bedrock"] == []


def test_picks_that_resolve_to_nothing_without_teammates_never_embeds_or_calls_central(stubs):
    result = ask(include_teammates=False, folder_ids=["no-such-folder"])
    assert result == {"answer": ask_service.NO_MATCH, "sources": []}
    assert stubs["search_calls"] == [] and stubs["bedrock"] == []


def test_empty_picks_with_central_down_say_why(stubs):
    stubs["reason"] = "central_unavailable"
    result = ask(include_teammates=True, folder_ids=["no-such-folder"])
    assert result == {"answer": ask_service.NO_MATCH, "sources": [], "teammate_skipped_reason": "central_unavailable"}


def test_a_question_without_a_topic_skips_teammates(stubs):
    _local()
    stubs["parsed"] = ParsedQuery(topic=None, date_from=None, date_to=None)
    result = ask(include_teammates=True)
    assert result["teammate_skipped_reason"] == "no_topic" and stubs["search_calls"] == []


def test_a_question_with_a_date_range_skips_teammates(stubs):
    from datetime import datetime, timezone
    _local()
    stubs["parsed"] = ParsedQuery(topic=TOPIC, date_from=datetime(2026, 10, 1, tzinfo=timezone.utc), date_to=None)
    result = ask(include_teammates=True)
    assert result["teammate_skipped_reason"] == "date_filter" and stubs["search_calls"] == []


@pytest.mark.parametrize("reason", ["no_team", "central_unavailable"])
def test_a_central_failure_degrades_to_local_files_and_says_why(stubs, reason):
    _local()
    stubs["reason"] = reason
    result = ask(include_teammates=True)
    assert result["teammate_skipped_reason"] == reason
    assert result["answer"] == "the answer" and [s["source"] for s in result["sources"]] == ["local"]


# --- the central call ---------------------------------------------------------------------------


@pytest.fixture
def signed_in(central):  # noqa: F811
    central.reply("GET /teams/me", 200, {"team": {"team_id": "t1", "name": "Alpha"}})
    return central


def test_retrieval_sends_only_the_vector_and_limit_and_returns_the_rows(signed_in):
    signed_in.reply("POST /retrieval/search", 200, {"results": [row()]})
    rows, reason = retrieval.search([0.1, 0.2], limit=7)
    assert reason is None and rows == [row()]
    assert signed_in.calls[-1] == ("POST /retrieval/search", {"query_embedding": [0.1, 0.2], "limit": 7})


def test_retrieval_uses_the_configured_limit_by_default(signed_in):
    retrieval.search([0.1])
    assert signed_in.calls[-1][1]["limit"] == config.TEAMMATE_CHUNK_LIMIT


def test_retrieval_without_a_team_does_not_call_central(central):  # noqa: F811
    central.reply("GET /teams/me", 200, {"team": None})
    assert retrieval.search([0.1]) == ([], "no_team")
    assert not any(route == "POST /retrieval/search" for route, _ in central.calls)


def test_retrieval_maps_central_errors_to_a_skip_reason(signed_in):
    signed_in.reply("POST /retrieval/search", 403, {"error": {"code": "no_team", "message": "x"}})
    assert retrieval.search([0.1]) == ([], "no_team")
    signed_in.reply("POST /retrieval/search", 503, {"error": {"code": "service_unavailable", "message": "x"}})
    assert retrieval.search([0.1]) == ([], "central_unavailable")
    signed_in.reply("POST /retrieval/search", 400, {"error": {"code": "invalid_request", "message": "x"}})
    assert retrieval.search([0.1]) == ([], "central_unavailable")


def test_the_question_text_never_reaches_central(isolated_store, signed_in, monkeypatch):
    # The real retrieval.search against the faked central HTTP layer (no search stub here).
    signed_in.reply("POST /retrieval/search", 200, {"results": []})
    monkeypatch.setattr(ask_service, "parse_query_locally", lambda q: ParsedQuery(TOPIC, None, None))
    monkeypatch.setattr(ask_service.bedrock, "invoke_text", lambda *a: ("x", False))
    _local()
    ask_service.ask("SECRET-QUESTION about the budget forecast", include_teammates=True)
    sent = [body for route, body in signed_in.calls if route == "POST /retrieval/search"]
    assert sent and "SECRET-QUESTION" not in repr(sent) and TOPIC not in repr(sent)


# --- routes ----------------------------------------------------------------------------------------


@pytest.fixture
def api(isolated_store, client):
    client.headers.update({"X-HiveMind-Token": STARTUP_TOKEN})
    return client


def test_ask_route_passes_include_teammates_through(api, monkeypatch):
    seen = {}

    def fake(question, folder_ids=None, file_ids=None, include_teammates=False):
        seen.update(question=question, include_teammates=include_teammates)
        return {"answer": "a", "sources": [], "teammate_skipped_reason": "no_topic"}

    monkeypatch.setattr("app.api.routes_ask.ask", fake)
    resp = api.post("/ask", json={"question": "q", "include_teammates": True})
    assert resp.status_code == 200 and seen == {"question": "q", "include_teammates": True}
    assert resp.json()["teammate_skipped_reason"] == "no_topic"
    api.post("/ask", json={"question": "q"})
    assert seen["include_teammates"] is False


def test_chat_message_returns_the_skip_reason_and_saves_the_source_flags_but_not_the_reason(api, monkeypatch):
    sources = [{"file_id": "t1", "filename": "Team plan.docx", "source": "teammate"}]
    monkeypatch.setattr("app.api.routes_chats.ask", lambda q, folder_ids=None, file_ids=None, include_teammates=False: {
        "answer": "a", "sources": sources, "teammate_skipped_reason": "central_unavailable"})
    chat_id = api.post("/chats").json()["chat_id"]
    live = api.post(f"/chats/{chat_id}/messages", json={"question": "q", "include_teammates": True}).json()
    assert live["messages"][1]["teammate_skipped_reason"] == "central_unavailable"
    saved = api.get(f"/chats/{chat_id}").json()["messages"][1]
    assert saved["sources"] == sources and "teammate_skipped_reason" not in saved


def test_chat_message_without_teammates_has_no_skip_reason_key(api, monkeypatch):
    monkeypatch.setattr("app.api.routes_chats.ask", lambda q, folder_ids=None, file_ids=None, include_teammates=False: {
        "answer": "a", "sources": []})
    chat_id = api.post("/chats").json()["chat_id"]
    live = api.post(f"/chats/{chat_id}/messages", json={"question": "q"}).json()
    assert "teammate_skipped_reason" not in live["messages"][1]
