import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_auth, routes_files, routes_folders, routes_search
from app.config import FRONTEND_ORIGIN
from app.db import init_db

# Random per-restart token (Feature_List 1.11 / API_Contract 2.1). GET /auth/token
# is the only endpoint that doesn't require it.
STARTUP_TOKEN = secrets.token_urlsafe(32)

init_db()

app = FastAPI(title="HiveMind Local Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

_EXEMPT_PATHS = {"/auth/token", "/docs", "/openapi.json", "/redoc"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # API_Contract.md section 1: every error is {"error": {...}} at the top level. FastAPI would
    # otherwise nest a dict `detail` under "detail", which the frontend can't read.
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    else:
        content = {"error": {"code": "http_error", "message": str(exc.detail), "details": {}}}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.middleware("http")
async def require_startup_token(request: Request, call_next):
    # CORS preflight requests never carry custom headers — let CORSMiddleware
    # handle them, or every browser POST/DELETE would fail before it even starts.
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path not in _EXEMPT_PATHS:
        if request.headers.get("x-hivemind-token") != STARTUP_TOKEN:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "unauthorized", "message": "missing or invalid token"}},
            )
    return await call_next(request)


app.include_router(routes_auth.router)
app.include_router(routes_folders.router)
app.include_router(routes_files.router)
app.include_router(routes_search.router)
