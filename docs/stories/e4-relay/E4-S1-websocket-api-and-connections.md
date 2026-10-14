# E4-S1: WebSocket API and connections

- **Epic:** E4 Relay and download
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E3-S1, E0-S5
- **Spec refs:** Feature_List 3.1, 3.5; Interface C
- **Flags:** verify-in-AWS

## Story
As an agent, I want a authenticated persistent connection so the server can reach me.

## Acceptance criteria
- [x] The WebSocket authorizer validates the JWT.
- [x] Connect/disconnect update the connections table; `ping` returns `pong`.
- [x] Owner-online status is available to search.

## Technical notes
- WebSocket API with `$connect` (Lambda authorizer validates the Cognito JWT; token passing method from E0-S5), `$disconnect`, and an `action`-routed `ping` -> `{"action":"pong"}`.
- On connect insert `(connection_id, user_id, connected_at)`; on disconnect delete. Users with no team may connect. If an owner has several connections, use the most recent; delete stale ones when `post_to_connection` raises `GoneException`.
- `owner_online` for search = row exists in `connections`.

## Notes
**Implemented on `feature/e4-s1-websocket-api`, deployed, and verified in AWS (2026-10-14): `pytest -m integration tests/test_relay_integration.py` -> 5 passed.**

- `central/lambdas/ws_authorizer.py`: validates the Cognito access token (RS256 via cached JWKS, `iss`, `exp`, `token_use=access`, `client_id`) and passes `user_id` in authorizer context. Runs outside the VPC (needs Cognito's JWKS URL; subnets have no NAT). PyJWT + cryptography ship in a second layer (`infra/auth_layer`, built by `build_layer.py`).
- `central/lambdas/relay.py`: `$connect` upserts a `connections` row, `$disconnect` deletes it, `ping` returns `{"action":"pong"}` as a route response (`return_response=True`), so S1 needs no `post_to_connection` and no `execute-api` VPC endpoint.
- Token passing: `Authorization: Bearer` header via REQUEST authorizer identity source `route.request.header.Authorization`.
- `owner_online` already comes from `connections` in `search.py`; `test_relay_integration.py` covers it.
- `cdk synth` succeeds; 165 offline tests pass.
- **Deferred to E4-S2:** `execute-api` VPC endpoint, `execute-api:ManageConnections` grant, `post_to_connection` helper with `GoneException` cleanup, latest-connection lookup.
- **Verified in AWS:** the `Authorization: Bearer` header is honoured on `$connect` (no query-string fallback needed); `ping` -> `pong` works as a route response; a missing token is rejected at the handshake with 401, a garbage token with 403, and an ID token is rejected; `owner_online` flips true on connect and back to false after disconnect.
- **Not tested, documentation only:** idle timeout (documented 10 min) and max connection duration (documented 2 h). Agent (E4-S3) should ping about every 5 min and reconnect after 2 h; confirm when S3 runs against the real API.