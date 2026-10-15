"""Saved Ask conversations: create, ask inside a chat, title, delete. The model call is stubbed,
so these run offline and never touch Bedrock."""
import pytest

from app.auth.security import STARTUP_TOKEN
from app.config import CHAT_TITLE_MAX_CHARS
from app.errors import ApiError


@pytest.fixture
def api(isolated_store, client):
    client.headers.update({"X-HiveMind-Token": STARTUP_TOKEN})
    return client


@pytest.fixture
def fake_ask(monkeypatch):
    calls = []

    def fake(question, folder_ids=None, file_ids=None):
        calls.append(question)
        return {
            "answer": f"Answer to: {question}",
            "sources": [{"file_id": "f1", "filename": "Roadmap 023 2026-10-06.docx"}],
        }

    monkeypatch.setattr("app.api.routes_chats.ask", fake)
    return calls


def test_a_new_chat_appears_in_the_list_and_starts_empty(api):
    created = api.post("/chats")
    assert created.status_code == 201
    chat_id = created.json()["chat_id"]

    assert chat_id in [c["chat_id"] for c in api.get("/chats").json()["chats"]]
    opened = api.get(f"/chats/{chat_id}").json()
    assert opened["messages"] == []
    assert opened["title"] is None


def test_asking_saves_the_question_and_the_answer_with_sources(api, fake_ask):
    chat_id = api.post("/chats").json()["chat_id"]

    response = api.post(f"/chats/{chat_id}/messages", json={"question": "what did we do last week"})
    assert response.status_code == 201
    roles = [m["role"] for m in response.json()["messages"]]
    assert roles == ["user", "assistant"]

    opened = api.get(f"/chats/{chat_id}").json()
    assert [m["role"] for m in opened["messages"]] == ["user", "assistant"]
    assert opened["messages"][0]["content"] == "what did we do last week"
    assert opened["messages"][1]["content"] == "Answer to: what did we do last week"
    assert opened["messages"][1]["sources"] == [{"file_id": "f1", "filename": "Roadmap 023 2026-10-06.docx"}]
    assert opened["messages"][0]["sources"] is None
    assert opened["title"] == "what did we do last week"


def test_a_second_question_appends_and_the_title_stays_the_same(api, fake_ask):
    chat_id = api.post("/chats").json()["chat_id"]
    api.post(f"/chats/{chat_id}/messages", json={"question": "first question"})
    api.post(f"/chats/{chat_id}/messages", json={"question": "second question"})

    opened = api.get(f"/chats/{chat_id}").json()
    assert [m["content"] for m in opened["messages"]][::2] == ["first question", "second question"]
    assert len(opened["messages"]) == 4
    assert opened["title"] == "first question"


def test_long_first_questions_are_shortened_for_the_title(api, fake_ask):
    chat_id = api.post("/chats").json()["chat_id"]
    long_question = "explain " + "every single thing in detail " * 10
    api.post(f"/chats/{chat_id}/messages", json={"question": long_question})

    title = api.get(f"/chats/{chat_id}").json()["title"]
    assert len(title) <= CHAT_TITLE_MAX_CHARS
    assert title.endswith("…")


def test_the_list_is_most_recently_used_first(api, fake_ask):
    older = api.post("/chats").json()["chat_id"]
    newer = api.post("/chats").json()["chat_id"]
    api.post(f"/chats/{older}/messages", json={"question": "older chat"})
    api.post(f"/chats/{newer}/messages", json={"question": "newer chat"})
    api.post(f"/chats/{older}/messages", json={"question": "older chat again"})

    ids = [c["chat_id"] for c in api.get("/chats").json()["chats"]]
    assert ids[0] == older


def test_deleting_a_chat_removes_it_and_its_messages(api, fake_ask):
    chat_id = api.post("/chats").json()["chat_id"]
    api.post(f"/chats/{chat_id}/messages", json={"question": "to be deleted"})

    assert api.delete(f"/chats/{chat_id}").status_code == 204
    assert api.get(f"/chats/{chat_id}").status_code == 404
    assert chat_id not in [c["chat_id"] for c in api.get("/chats").json()["chats"]]
    assert api.delete(f"/chats/{chat_id}").status_code == 204


def test_a_blank_question_is_rejected_and_nothing_is_saved(api, fake_ask):
    chat_id = api.post("/chats").json()["chat_id"]

    response = api.post(f"/chats/{chat_id}/messages", json={"question": "   "})
    assert response.status_code == 400
    assert fake_ask == []
    assert api.get(f"/chats/{chat_id}").json()["messages"] == []


def test_unknown_chats_are_404(api, fake_ask):
    assert api.get("/chats/no-such-chat").status_code == 404
    response = api.post("/chats/no-such-chat/messages", json={"question": "hello"})
    assert response.status_code == 404
    assert fake_ask == []


def test_a_failed_answer_saves_nothing_so_the_question_can_be_retried(api, monkeypatch):
    def broken(question, folder_ids=None, file_ids=None):
        raise ApiError(503, "service_unavailable", "model unavailable")

    monkeypatch.setattr("app.api.routes_chats.ask", broken)
    chat_id = api.post("/chats").json()["chat_id"]

    response = api.post(f"/chats/{chat_id}/messages", json={"question": "will fail"})
    assert response.status_code == 503
    assert api.get(f"/chats/{chat_id}").json()["messages"] == []
