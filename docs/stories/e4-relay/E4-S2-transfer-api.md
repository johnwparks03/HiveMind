# E4-S2: Transfer API

- **Epic:** E4 Relay and download
- **Track:** Central service
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E4-S1, E3-S2
- **Spec refs:** Feature_List 3.5; Interface B `/transfers*`

## Story
As a requester, I want to request a teammate's file and get a download link.

## Acceptance criteria
- [x] `POST /transfers` creates a transfer and sends `upload_request` to the owner's socket; offline owner returns a clear error.
- [x] `ack`, `complete` and `fail` update state; no ack within 60 seconds fails the transfer.
- [x] `GET /transfers/{id}` returns a presigned GET URL when ready.
- [x] Every request writes an access log entry.

## Technical notes
- `POST /transfers` `{file_id}` -> `202 {transfer_id,status:'requested'}`. Checks: file exists and not expired, same team, caller is not owner (`400 own_file`), owner has a live connection (`409 owner_offline`), no team (`403 no_team`), else `404 not_found`. Reuse an in-flight transfer for the same file and requester.
- Create `transfers` row, S3 key = transfer ID (random, no filename), short-lived presigned PUT, send `upload_request` `{action,transfer_id,file_id,upload_url,upload_url_expires_at,ack_deadline_seconds:60}` to the owner's connection.
- `GET /transfers/{id}` (requester only; others get 404) -> `{transfer_id,file_id,status,download_url?,download_url_expires_at?,error_code?}`; issue the presigned GET only when status is `ready`. `error_code`: `owner_unresponsive|file_unavailable|upload_failed`.
- Owner endpoints (owner only): `POST /transfers/{id}/ack` -> 204 (`uploading`), `/complete` `{size_bytes?}` -> 204 (`ready`), `/fail` `{reason: file_not_found|not_public|upload_error}` -> 204 (`failed`).
- No ack within 60 s -> `failed` with `owner_unresponsive` (also enforced by the sweeper). No owner approval step, no size cap. Write `transfer_request` access-log events.

## Notes
**Implemented on `feature/e4-s2-transfer-api`, deployed, and verified in AWS (2026-10-15): `pytest -m integration tests/test_transfers_integration.py` -> 7 passed in 144 s (full relay path with byte-identical download, owner offline, validation, no team, duplicate reuse, owner failure, 60 s ack timeout). Postman `Test Transfers` folder (29 requests) also passed.**

- `central/lambdas/transfers.py`: `POST /transfers`, `GET /transfers/{id}`, owner `ack` / `complete` / `fail`. `POST /transfers` is three-phase (commit the row, notify the owner, then undo on failure) so the owner can never ack an uncommitted transfer and a failed send never loses the audit entry.
- Reuse of an in-flight transfer is concurrency-safe via a partial unique index (`0003_transfers_api.sql`), which also adds `error_code`, `size_bytes`, and `access_log.transfer_id` / `outcome`.
- `common/relay.py` + `notify.py`: send to the owner's most recent connection; a `GoneException` drops that connection and tries the next. `common/transit.py`: presigned PUT/GET signing only bucket and key.
- **First deploy finding (2026-10-14):** calling the WebSocket management API from the VPC Lambda through an `execute-api` interface endpoint failed with `ForbiddenException` on every call, although the endpoint was healthy (private DNS on, allow-all policy), the role's `execute-api:ManageConnections` grant was correct (IAM simulation: allowed, no permissions boundary), and the same API accepted the call from outside the VPC. The root cause inside API Gateway is not proven. Fix: the send now runs in a small non-VPC `NotifyFn` (own role with `ManageConnections`, no DB access), invoked by `TransfersFn` through a Lambda interface VPC endpoint. Invoke retries are off so a retry cannot deliver an `upload_request` twice.
- Infra: `NotifyFn`, Lambda interface VPC endpoint (the VPC has no NAT), five authed HTTP routes, and `UPLOAD_URL_EXPIRY_SECONDS` / `DOWNLOAD_URL_EXPIRY_SECONDS` config.
- Decisions: non-owner and non-requester get `404`; invalid transitions get `409 conflict`; validation failures (400/403/404) are not access-logged because they identify no file; the central `GET /transfers` list is not built (contract 2.6 puts it in the agent).
- Tests: 217 offline tests pass; `cdk synth` succeeds. Integration tests in `central/tests/test_transfers_integration.py` (run with `-m integration`; the ack-timeout test is `slow`, about 65 s). Postman folder `Test Transfers` added to the HiveMind collection (HTTP-only cases; the connected happy path needs a WebSocket and stays in pytest).
- **After the notify fix:** all 7 integration tests pass against the redeployed stack, and the S1 relay tests still pass. The notify path (NotifyFn over the Lambda VPC endpoint) works.
- **First deploy results:** the 3 integration tests that need no online owner passed (owner offline 409, validation errors, no team). The 4 that need an online owner failed with 503 until the notify change above. **Verified after redeploy:** the notify path, presigned PUT/GET with an arbitrary Content-Type, and the real 60 s ack timeout.
- **Review follow-up (2026-10-15):** (1) an unclear owner notification (the send raised after possibly delivering) now keeps the transfer `requested` and returns `202` with access-log outcome `send_unconfirmed`, instead of failing it with `503`; only a failure before sending (presigning) still fails the transfer with `503`. If the owner never got the message, the 60 s ack timeout fails it. (2) A transfer stuck in `uploading` fails as `upload_failed` after `TRANSFER_UPLOAD_TIMEOUT_SECONDS` (600) from the ack, applied lazily on create/get/owner calls (`common/transfer_state.apply_timeouts`) and by the sweeper. Trade-off: an upload still running at 10 minutes is failed and the owner's `complete` gets `409`. (3) `IN_FLIGHT` now lives in `common/transfer_state.py`, with a test tying it to the migration's index predicate; `log_event` is a single INSERT.
- **For E4-S5:** the VPC has no S3 gateway endpoint, so the sweeper Lambda needs one (free) or must run outside the VPC to delete objects.
