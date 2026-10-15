"""Saved Ask conversations in the local registry (chats + chat_messages tables).

Chats live on this computer only. A chat's title is taken from its first question, so the
sidebar stays readable without asking the model for a title.
"""
import json
import uuid
from datetime import datetime, timezone

from app.config import CHAT_TITLE_MAX_CHARS
from app.db import session


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _title_from(question: str) -> str:
    text = " ".join(question.split())
    if len(text) <= CHAT_TITLE_MAX_CHARS:
        return text
    return text[: CHAT_TITLE_MAX_CHARS - 1].rstrip() + "…"


def create_chat() -> dict:
    chat_id = str(uuid.uuid4())
    now = _now()
    with session() as conn:
        conn.execute(
            "INSERT INTO chats (chat_id, title, created_at, updated_at) VALUES (?, NULL, ?, ?)",
            (chat_id, now, now),
        )
    return {"chat_id": chat_id, "title": None, "created_at": now, "updated_at": now}


def list_chats() -> list[dict]:
    with session() as conn:
        rows = conn.execute(
            "SELECT chat_id, title, created_at, updated_at FROM chats ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_chat(chat_id: str) -> dict | None:
    with session() as conn:
        chat = conn.execute(
            "SELECT chat_id, title, created_at, updated_at FROM chats WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        if not chat:
            return None
        rows = conn.execute(
            "SELECT message_id, role, content, sources, created_at FROM chat_messages "
            "WHERE chat_id = ? ORDER BY rowid",
            (chat_id,),
        ).fetchall()
    messages = []
    for r in rows:
        message = dict(r)
        message["sources"] = json.loads(message["sources"]) if message["sources"] else None
        messages.append(message)
    return {**dict(chat), "messages": messages}


def delete_chat(chat_id: str) -> bool:
    with session() as conn:
        cursor = conn.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
        return cursor.rowcount > 0


def add_exchange(chat_id: str, question: str, answer: str, sources: list[dict]) -> list[dict]:
    """Saves one question and its answer. Sets the chat's title from the first question."""
    now = _now()
    user_message = {
        "message_id": str(uuid.uuid4()),
        "role": "user",
        "content": question,
        "sources": None,
        "created_at": now,
    }
    assistant_message = {
        "message_id": str(uuid.uuid4()),
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "created_at": now,
    }
    with session() as conn:
        conn.execute(
            "UPDATE chats SET title = COALESCE(title, ?), updated_at = ? WHERE chat_id = ?",
            (_title_from(question), now, chat_id),
        )
        for message in (user_message, assistant_message):
            conn.execute(
                "INSERT INTO chat_messages (message_id, chat_id, role, content, sources, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    message["message_id"],
                    chat_id,
                    message["role"],
                    message["content"],
                    json.dumps(message["sources"]) if message["sources"] is not None else None,
                    message["created_at"],
                ),
            )
    return [user_message, assistant_message]
