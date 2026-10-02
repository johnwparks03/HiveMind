# E0-S5: Spike: relay path end to end

- **Epic:** E0 Foundations and risk spikes
- **Track:** Local agent + Central service
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E0-S2, E0-S3
- **Spec refs:** Feature_List 1.8, 3.5; API_Contract Interface C
- **Flags:** verify-in-AWS

## Story
As a team, we want a thin hardcoded relay (WebSocket, presigned PUT, presigned GET) so the highest technical risk is retired in week 1.

## Acceptance criteria
- [ ] Given two agents connected over WebSocket, when agent B requests a hardcoded file from agent A, then A receives `upload_request`, uploads to the presigned PUT URL and B downloads from the presigned GET URL.
- [ ] Works across two different networks (or at least two machines).
- [ ] WebSocket idle timeout, auth token passing and PUT header behaviour are noted for the API_Contract open items.

## Technical notes
- Throwaway prototype is fine, but keep it reusable: API Gateway WebSocket API with `$connect`, `$disconnect` and an `action`-routed default route; connections table (`connection_id`, `user_id`, `connected_at`).
- Server sends `upload_request` via `apigatewaymanagementapi.post_to_connection`; handle `GoneException` by deleting the stale row.
- Owner streams file to presigned PUT (stream, do not read into memory); requester polls then GETs presigned URL. Test a large file (e.g. 100+ MB) and a different network.
- Record: how the token is passed on `$connect` (header vs query string; open item 5), idle timeout and ping interval, and whether the PUT needs `Content-Type`/`Content-Length` (open item 7).

## Notes
_(add during implementation)_
