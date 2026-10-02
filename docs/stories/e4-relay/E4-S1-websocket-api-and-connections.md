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
- [ ] The WebSocket authorizer validates the JWT.
- [ ] Connect/disconnect update the connections table; `ping` returns `pong`.
- [ ] Owner-online status is available to search.

## Technical notes
- WebSocket API with `$connect` (Lambda authorizer validates the Cognito JWT; token passing method from E0-S5), `$disconnect`, and an `action`-routed `ping` -> `{"action":"pong"}`.
- On connect insert `(connection_id, user_id, connected_at)`; on disconnect delete. Users with no team may connect. If an owner has several connections, use the most recent; delete stale ones when `post_to_connection` raises `GoneException`.
- `owner_online` for search = row exists in `connections`.

## Notes
_(add during implementation)_
