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
- [x] Given valid credentials, when `POST /auth/login` is called, then the refresh token is stored in the keychain and `GET /session` shows signed in.
- [x] Tokens are refreshed automatically and attached to every central call.
- [x] `POST /auth/logout` deletes the keychain entry and clears memory.

## Technical notes
- `POST /auth/signup` `{email,password}` -> `201 {"status":"created"}`; errors `400 password_policy` (details = Cognito message), `409 user_exists`, `503 service_unavailable`.
- `POST /auth/login` -> `200 {"signed_in":true,"email":...}`; errors `401 invalid_credentials`, `503`. No Cognito tokens returned to the frontend.
- `POST /auth/logout` -> `204`; deletes keychain entry, clears memory, closes the WebSocket (E4-S3).
- `GET /session` returns `{agent, signed_in, email, team, relay, central_reachable}`; `relay` is `connected|connecting|disconnected`; `team` is `null` if none.
- On startup, if a refresh token exists in the keychain, refresh silently. Provide one shared central-API client that adds the Bearer token and refreshes on expiry; all later stories use it.

## Notes
Implemented on branch `feature/e1-s2-s3-agent-auth`.
- **Verified 2026-10-13** against real Cognito, the deployed API and Windows Credential Manager (15/15 checks, throwaway user, deleted afterwards): signup 201; login returns only `{signed_in,email}`; `/session` signed in with `central_reachable: true`; Credential Manager held 3 entries (`HiveMind`, `refresh_token.0`, `refresh_token.1`); `POST /team` through the agent returned 201 (Bearer attached); a second agent started on another port restored the session from the keychain and called central successfully (refresh path); logout returned 204, all 3 entries were removed, `/session` showed signed out, and a central call afterwards returned 401. Near-expiry refresh while running is covered by unit tests only, not waited out live.
- Cognito is called with plain HTTPS (`app/auth/cognito.py`), so the agent holds no AWS credentials. Bearer token = access token.
- Config: `HIVEMIND_COGNITO_CLIENT_ID`, `HIVEMIND_CENTRAL_API_URL` (CDK outputs `UserPoolClientId`, `HttpApiUrl`), optional `HIVEMIND_COGNITO_REGION`. Loaded from gitignored `agent/.env` (template: `agent/.env.example`) or the environment. If unset, the agent still starts; the auth endpoints return 503 with `details.missing`.
- Keychain: one Credential Manager entry (service `HiveMind`) holding email + refresh token; falls back to memory only if keyring raises (`keystore.persistent`). This also covers the E0-S6 spike's code; its own story still needs the manual Credential Manager check.
- Shared central client: `app/central/client.py` `request()`; refreshes near expiry and once on a 401.
- `GET /session`: `team` is filled from central by E1-S5 (was `null` until then); `relay` is `disconnected` until E4-S3 (`app/central/relay.py` is a stub).
- Cognito error mapping: UsernameExists -> 409 user_exists; InvalidPassword -> 400 password_policy; NotAuthorized/UserNotFound -> 401 invalid_credentials; InvalidParameter -> 400 invalid_request; anything else -> 503.
- A revoked refresh token at startup clears the keychain entry; a network failure at startup leaves it in place.
- Keychain values are split into chunks (`KEYRING_CHUNK_CHARS`) because Credential Manager caps a blob at ~1,280 UTF-16 characters and Cognito refresh tokens can be longer. **verify-in-AWS:** confirm with a real login that a Credential Manager entry `HiveMind` (+ `.0`, `.1` chunks) appears and survives an agent restart.
- Cognito rate-limit errors map to `429 too_many_attempts`, which is not in API_Contract section 1; add it there.
- `GET /auth/token` wrong Origin returns `403 forbidden`; the contract gives the status but no code. Recorded here as the decision.
- `/session` caches the central health check for `CENTRAL_HEALTH_CACHE_SECONDS`.
- Known, deferred: startup restore is a single attempt (no retry if the network is down at launch; the user logs in again); small races in `session.py` between logout and an in-flight refresh; `central_client.request` re-sends the same kwargs on a 401 retry, so streamed bodies (relay upload) need their own handling; `pytest` sits in `requirements.txt` rather than a dev file.
