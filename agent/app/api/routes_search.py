from fastapi import APIRouter
from pydantic import BaseModel

from app.search.search_service import search_local

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    include_teammates: bool = False


@router.post("/search")
def post_search(body: SearchRequest):
    return search_local(body.query, include_teammates=body.include_teammates)
