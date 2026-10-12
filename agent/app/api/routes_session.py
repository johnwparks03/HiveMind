from fastapi import APIRouter

from app.auth import session
from app.central import client as central_client
from app.central import relay

router = APIRouter()


@router.get("/session")
def get_session():
    return {
        "agent": "ok",
        "signed_in": session.is_signed_in(),
        "email": session.email(),
        "team": None,  # until E1-S4 adds GET /teams/me on central
        "relay": relay.state(),
        "central_reachable": central_client.is_reachable(),
    }
