from fastapi import APIRouter

from app.auth import session
from app.central import client as central_client
from app.central import relay, teams

router = APIRouter()


@router.get("/session")
def get_session():
    reachable = central_client.is_reachable()
    return {
        "agent": "ok",
        "signed_in": session.is_signed_in(),
        "email": session.email(),
        "team": teams.current_team_or_none() if reachable and session.is_signed_in() else None,
        "relay": relay.state(),
        "central_reachable": reachable,
    }
