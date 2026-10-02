# E4-S3: Relay client: owner side

- **Epic:** E4 Relay and download
- **Track:** Local agent
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E4-S1, E0-S5
- **Spec refs:** Feature_List 1.8

## Story
As an owner, I want my agent to serve file requests automatically.

## Acceptance criteria
- [ ] The agent keeps a WebSocket with reconnect and pings.
- [ ] On `upload_request` it verifies the file is public and exists, acks, streams to the presigned PUT, and reports completion over HTTP.
- [ ] Failures call `fail` with a reason.

## Technical notes
- Connect after login (and after token refresh) to the WebSocket with the Bearer token; reconnect with backoff; send `{"action":"ping"}` at an interval below the API Gateway idle timeout (value from E0-S5). Expose state as `relay: connected|connecting|disconnected` in `GET /session`.
- On `upload_request`: check file is still public and exists on disk; if not, `POST /transfers/{id}/fail` with `not_public` or `file_not_found`; else `POST /transfers/{id}/ack`, stream the file to `upload_url` with HTTP PUT (chunked streaming, no full read into memory), then `POST /transfers/{id}/complete`; on any error `POST .../fail` with `upload_error`.
- Ack/complete/fail go over HTTP, not the WebSocket.
- Must close the connection on logout.

## Notes
_(add during implementation)_
