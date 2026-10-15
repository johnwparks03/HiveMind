from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_ask,
    routes_auth,
    routes_files,
    routes_folders,
    routes_search,
    routes_session,
    routes_team,
)
from app.auth import session
from app.auth.security import token_matches
from app.central import publish
from app.config import FRONTEND_ORIGIN, HOST, PORT
from app.db import init_db
from app.errors import envelope, install_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    session.restore_from_keychain()  # silent sign-in if a refresh token is stored
    publish.start()
    try:
        yield
    finally:
        publish.stop()


app = FastAPI(title="HiveMind Local Agent", lifespan=lifespan)
install_error_handlers(app)

_EXEMPT_PATHS = {"/auth/token", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def require_startup_token(request: Request, call_next):
    # CORS preflight requests never carry custom headers — let CORSMiddleware
    # handle them, or every browser POST/DELETE would fail before it even starts.
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path not in _EXEMPT_PATHS:
        if not token_matches(request.headers.get("x-hivemind-token")):
            return envelope(401, "unauthorized", "missing or invalid token")
    return await call_next(request)


# Added last so it is the outermost layer: the token check's 401 and 500s still need
# CORS headers, or the browser hides them behind an opaque network error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["X-HiveMind-Token", "Content-Type"],
)

app.include_router(routes_auth.router)
app.include_router(routes_session.router)
app.include_router(routes_team.router)
app.include_router(routes_folders.router)
app.include_router(routes_files.router)
app.include_router(routes_search.router)
app.include_router(routes_ask.router)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
