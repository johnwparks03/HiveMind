from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.central import teams

router = APIRouter()


class CreateTeam(BaseModel):
    name: str


class JoinTeam(BaseModel):
    code: str


@router.get("/team")
def get_team():
    return {"team": teams.get_team()}


@router.post("/team", status_code=201)
def create_team(body: CreateTeam):
    return teams.create_team(body.name)


@router.post("/team/invites", status_code=201)
def create_invite():
    return teams.create_invite()


@router.post("/team/join")
def join_team(body: JoinTeam):
    return teams.join_team(body.code)


@router.post("/team/leave", status_code=204)
def leave_team():
    teams.leave_team()
    return Response(status_code=204)
