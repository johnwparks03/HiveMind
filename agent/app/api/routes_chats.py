from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.chats import store
from app.errors import ApiError
from app.search.ask_service import ask

router = APIRouter()


class ChatQuestion(BaseModel):
    question: str
    folder_ids: list[str] | None = None
    file_ids: list[str] | None = None


@router.get("/chats")
def get_chats():
    return {"chats": store.list_chats()}


@router.post("/chats", status_code=201)
def post_chat():
    return store.create_chat()


@router.get("/chats/{chat_id}")
def get_chat(chat_id: str):
    chat = store.get_chat(chat_id)
    if chat is None:
        raise ApiError(404, "not_found", "chat not found")
    return chat


@router.delete("/chats/{chat_id}", status_code=204)
def delete_chat(chat_id: str):
    # Idempotent, like the central DELETEs: a chat that's already gone is still a 204.
    store.delete_chat(chat_id)
    return Response(status_code=204)


@router.post("/chats/{chat_id}/messages", status_code=201)
def post_chat_message(chat_id: str, body: ChatQuestion):
    question = body.question.strip()
    if not question:
        raise ApiError(400, "invalid_request", "question is empty")
    if store.get_chat(chat_id) is None:
        raise ApiError(404, "not_found", "chat not found")

    # Ask first: if the model call fails, nothing is saved and the question can be retried.
    answer = ask(question, folder_ids=body.folder_ids, file_ids=body.file_ids)
    messages = store.add_exchange(chat_id, question, answer["answer"], answer["sources"])
    return {"messages": messages}
