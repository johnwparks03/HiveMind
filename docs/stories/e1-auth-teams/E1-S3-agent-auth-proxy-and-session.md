# E1-S3: Agent auth proxy and session

- **Epic:** E1 Auth and teams
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E1-S1, E1-S2, E0-S6
- **Spec refs:** Feature_List 1.9; `POST /auth/signup|login|logout`, `GET /session`

## Story
As a user, I want to log in once and stay logged in so that I don't re-enter credentials.

## Acceptance criteria
- [ ] Given valid credentials, when `POST /auth/login` is called, then the refresh token is stored in the keychain and `GET /session` shows signed in.
- [ ] Tokens are refreshed automatically and attached to every central call.
- [ ] `POST /auth/logout` deletes the keychain entry and clears memory.

## Technical notes
- `POST /auth/signup` `{email,password}` -> `201 {"status":"created"}`; errors `400 password_policy` (details = Cognito message), `409 user_exists`, `503 service_unavailable`.
- `POST /auth/login` -> `200 {"signed_in":true,"email":...}`; errors `401 invalid_credentials`, `503`. No Cognito tokens returned to the frontend.
- `POST /auth/logout` -> `204`; deletes keychain entry, clears memory, closes the WebSocket (E4-S3).
- `GET /session` returns `{agent, signed_in, email, team, relay, central_reachable}`; `relay` is `connected|connecting|disconnected`; `team` is `null` if none.
- On startup, if a refresh token exists in the keychain, refresh silently. Provide one shared central-API client that adds the Bearer token and refreshes on expiry; all later stories use it.

## Notes
_(add during implementation)_
