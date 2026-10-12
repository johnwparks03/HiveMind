# E1-S2: Agent local API shell

- **Epic:** E1 Auth and teams
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E0-S1
- **Spec refs:** Feature_List 1.11; API_Contract Interface A

## Story
As a developer, I want a secured local API so that only the HiveMind UI can talk to the agent.

## Acceptance criteria
- [x] The agent binds to 127.0.0.1 only.
- [x] A random startup token is generated; every endpoint except `GET /auth/token` requires `X-HiveMind-Token`.
- [x] CORS allows only the React origin.
- [x] Errors use the `{error:{code,message,details}}` envelope.

## Technical notes
- FastAPI app on `127.0.0.1:{port}` (port is config; choose a default and record it). Bind to loopback only, never 0.0.0.0.
- Startup token: generate with `secrets.token_urlsafe`, new on every start. Dependency/middleware checks `X-HiveMind-Token` on every route except `GET /auth/token`.
- `GET /auth/token` returns `{"token": "..."}` only if `Origin` exactly equals the configured React origin; otherwise `403`.
- CORS: allow only the React origin, with `X-HiveMind-Token` and `Content-Type` headers allowed.
- Global exception handler produces the `{error:{code,message,details}}` envelope.

## Notes
- Port 8420, recorded in `agent/app/config.py`. `python -m app.main` binds `HOST` (127.0.0.1); the uvicorn CLI command in the README also passes `--host 127.0.0.1`.
- Startup token moved to `app/auth/security.py` (constant-time compare). Envelope handlers (ApiError, HTTP, validation, unhandled) live in `app/errors.py`. Validation errors report field names only, never submitted values.
- Wrong Origin on `GET /auth/token` now returns 403 `forbidden` per the contract (was 401).
- Tests: `agent/tests/test_shell.py` (`cd agent; .venv\Scripts\python -m pytest tests`).
