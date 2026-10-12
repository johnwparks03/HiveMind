from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.auth import cognito, session
from app.auth.security import STARTUP_TOKEN
from app.central import relay
from app.config import FRONTEND_ORIGIN
from app.errors import ApiError

router = APIRouter()


class Credentials(BaseModel):
    email: str
    password: str


@router.get("/auth/token")
def get_startup_token(request: Request):
    """The one unauthenticated endpoint (Feature_List 1.11). Returns the agent's
    random startup token only when the Origin header matches exactly.
    """
    if request.headers.get("origin") != FRONTEND_ORIGIN:
        raise ApiError(403, "forbidden", "origin mismatch")
    return {"token": STARTUP_TOKEN}


@router.post("/auth/signup", status_code=201)
def signup(body: Credentials):
    cognito.sign_up(body.email, body.password)
    return {"status": "created"}


@router.post("/auth/login")
def login(body: Credentials):
    session.login(body.email, body.password)
    return {"signed_in": True, "email": body.email}


@router.post("/auth/logout", status_code=204)
def logout():
    relay.close()
    session.logout()
    return Response(status_code=204)
