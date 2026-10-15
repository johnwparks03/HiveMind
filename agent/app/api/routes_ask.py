from fastapi import APIRouter
from pydantic import BaseModel

from app.search.ask_service import ask

router = APIRouter()


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def post_ask(body: AskRequest):
    return ask(body.question)
