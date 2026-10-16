from fastapi import APIRouter
from pydantic import BaseModel

from app.central import download
from app.errors import ApiError

router = APIRouter()


class CreateTransfer(BaseModel):
    file_id: str
    # Not part of API_Contract.md's central request shape - see download.py's
    # request_download() docstring for why the agent accepts it anyway.
    filename: str | None = None


@router.post("/transfers", status_code=202)
def post_transfer(body: CreateTransfer):
    return download.request_download(body.file_id, body.filename)


@router.get("/transfers")
def get_transfers():
    return {"transfers": download.list_downloads()}


@router.get("/transfers/{transfer_id}")
def get_transfer(transfer_id: str):
    row = download.get_download(transfer_id)
    if not row:
        raise ApiError(404, "not_found", "transfer not found")
    return row
