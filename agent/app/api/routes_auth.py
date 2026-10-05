from fastapi import APIRouter, HTTPException, Request

from app.config import FRONTEND_ORIGIN

router = APIRouter()


@router.get("/auth/token")
def get_startup_token(request: Request):
    """The one unauthenticated endpoint (Feature_List 1.11). Returns the agent's
    random startup token only when the Origin header matches exactly.
    """
    from app.main import STARTUP_TOKEN

    if request.headers.get("origin") != FRONTEND_ORIGIN:
        raise HTTPException(status_code=401, detail={"error": {"code": "unauthorized", "message": "origin mismatch"}})
    return {"token": STARTUP_TOKEN}
