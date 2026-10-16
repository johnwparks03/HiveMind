from pathlib import Path

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app import settings
from app.central.download import downloads_folder
from app.errors import ApiError

router = APIRouter()


class SetDownloadFolder(BaseModel):
    path: str


@router.get("/settings/download-folder")
def get_download_folder():
    return {"path": str(downloads_folder())}


@router.put("/settings/download-folder")
def put_download_folder(body: SetDownloadFolder):
    if not Path(body.path).is_dir():
        raise ApiError(400, "invalid_request", "not a folder", {"fields": ["path"]})
    settings.set(settings.DOWNLOAD_FOLDER_KEY, body.path)
    return {"path": body.path}


@router.delete("/settings/download-folder", status_code=204)
def reset_download_folder():
    """Back to the default: the real Windows Downloads folder."""
    settings.clear(settings.DOWNLOAD_FOLDER_KEY)
    return Response(status_code=204)
