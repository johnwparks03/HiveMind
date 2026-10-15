from fastapi import APIRouter
from pydantic import BaseModel

from app.search.ask_service import ask

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    # Optional scope picker (folders and/or individual files). Omitted/empty means
    # search everything, same as before this existed.
    folder_ids: list[str] | None = None
    file_ids: list[str] | None = None


@router.post("/ask")
def post_ask(body: AskRequest):
    return ask(body.question, folder_ids=body.folder_ids, file_ids=body.file_ids)
