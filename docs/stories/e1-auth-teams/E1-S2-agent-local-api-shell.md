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
- [ ] The agent binds to 127.0.0.1 only.
- [ ] A random startup token is generated; every endpoint except `GET /auth/token` requires `X-HiveMind-Token`.
- [ ] CORS allows only the React origin.
- [ ] Errors use the `{error:{code,message,details}}` envelope.

## Technical notes
- FastAPI app on `127.0.0.1:{port}` (port is config; choose a default and record it). Bind to loopback only, never 0.0.0.0.
- Startup token: generate with `secrets.token_urlsafe`, new on every start. Dependency/middleware checks `X-HiveMind-Token` on every route except `GET /auth/token`.
- `GET /auth/token` returns `{"token": "..."}` only if `Origin` exactly equals the configured React origin; otherwise `403`.
- CORS: allow only the React origin, with `X-HiveMind-Token` and `Content-Type` headers allowed.
- Global exception handler produces the `{error:{code,message,details}}` envelope.

## Notes
_(add during implementation)_
