Consolidated from the design discussion. Items marked **(suggested)** are my recommendations that you haven't explicitly confirmed. Items marked **(verify)** rely on my understanding of AWS behavior that should be checked against the docs.

## Overview

HiveMind is a team knowledge-finding tool. A user searches their own files first. If nothing matches well, it searches metadata of files teammates have made public, and the user can download a match directly from the owner's laptop via a short-lived S3 relay.

|Component|Stack|Role|
|---|---|---|
|Local agent|Python, FastAPI, SQLite, Chroma, watchdog|Indexes files, searches locally, publishes, relays transfers|
|React frontend|React, Vite (dev server on a fixed origin, e.g. `localhost:5173`)|UI that talks **only** to the local agent|
|Central service|AWS: Cognito, API Gateway (HTTP + WebSocket), Lambda, RDS Postgres, S3, EventBridge, Bedrock|Teams, public-file metadata, search, LLM proxy, transfer relay|

**Platform:** Windows only for the MVP.

**Data flow summary**

- Frontend → Local agent → Central service. The frontend never calls the central service.
- Bedrock is never called by the agent directly. It goes agent → central proxy → Bedrock.
- File bytes touch AWS only as a short-lived S3 transit object.

---

## 1. Local Agent

### 1.1 Sources and folders

- `Source` interface with `list_files()` and `get_file_bytes(id)`
- `LocalFilesystemSource` as the only v1 implementation (Teams/SharePoint is a later addition)
- Add and remove watched folders (recursive, subfolders included)
- Native Windows folder dialog opened by the agent, exposed through an async endpoint so it doesn't block other work
- Initial scan of a newly added folder

### 1.2 Change detection

- File watcher (watchdog) for new, changed, moved, and deleted files
- Content-hash comparison so unchanged files aren't re-indexed
- Work queue so bulk folder adds don't block the agent

### 1.3 Extraction and dates

- Text extraction: PDF (PyMuPDF), DOCX (python-docx), PPTX (python-pptx), TXT
- Extraction failures recorded in the registry with a reason (e.g. "no extractable text"), never crashing the agent
- Created and modified dates from the filesystem
- In-document date extraction (local-only, never sent centrally)

### 1.4 Indexing

- Chunking and local embedding with all-MiniLM-L6-v2
- Chroma upsert with per-chunk date metadata
- Chunk removal when a file is changed, moved, or deleted
- No tag generation at index time (tags are generated at publish time)

### 1.5 Search

- Query understanding via the central LLM proxy: returns a topic and an absolute date range
- Agent sends its local date and timezone with the query
- Date filter first, then vector ranking over local Chroma
- "Comes up short" = no local result above a configurable similarity threshold (tuned during development)
- On "comes up short", call central search with the topic and date range (no second LLM call)
- Merge results, labeled local vs. teammate
- If the proxy is unreachable: return "service unavailable" (no degraded fallback)
- Open a local result in its default program via an agent endpoint

### 1.6 Publish and unpublish

- **Mark file public:** per file, with immediate publish (no tag preview; tags are editable afterward)
- **Share folder (one-time action):** publishes the files currently in the folder and its subfolders. Later additions stay private.
- **Unshare folder:** makes all files under it private
- Per-file pipeline: generate tags (excerpt + filename sent to proxy), then send metadata
    - Tag call retried a few times, then publish with empty tags
    - Step state stored per file so a retry doesn't repeat a finished tag call
- Metadata sent: file ID (agent-generated UUID), filename, tags, created date, modified date. `expires_at` is set by the server.
- Re-sync metadata when a public file's metadata changes or the user edits tags (existing tags are **not** regenerated when file content changes)
- Unpublish or flag a public file that is deleted or moved
- **Persistent publish queue** (SQLite):
    - Covers publish, unpublish, re-sync, and confirm
    - Exponential backoff with a retry cap
    - Survives agent restarts
    - Keeps only the latest intent per file (publish then quickly unpublish doesn't replay both)
    - Idempotent operations
    - Throttled sending, starting at 5 concurrent requests (tune during development)
- Per-file `publish_state`: `pending`, `published`, `failed`
- **Reconciliation:** periodically call `GET /files/mine` and correct the registry when files were purged, expired, or removed (e.g. after leaving a team)

### 1.7 Expiry

- Track `expires_at`, `published_at`, `last_confirmed` per public file
- Surface "expiring soon" (within 7 days, configurable)
- Re-confirm action calls the central service; `expires_at` resets to 45 days from confirmation

### 1.8 Relay client

- Authenticated outbound WebSocket after login, with automatic reconnect and periodic pings (interval depends on the API Gateway idle timeout, **verify**)
- Handle incoming `upload_request`:
    - Verify the file is still public and on disk
    - Acknowledge to start the transfer
    - **Stream** the file to the presigned PUT URL (no loading it all into memory)
    - Report completion over HTTP (not the WebSocket)
- Request a teammate's file: call `POST /transfer/request`, poll `GET /transfer/{id}` every 1 to 2 seconds until `ready` or `failed`, then download from the presigned GET URL
- Downloads go to the Windows Downloads folder, with a suffix added on filename collisions
- Duplicate-click protection (reuse the in-flight transfer)
- Show "owner offline" when the central service reports the owner isn't connected

### 1.9 Auth

- Login and sign-up endpoints that accept credentials from the React form and call Cognito
- Credentials are never stored or logged
- Refresh token stored in Windows Credential Manager via `keyring`; access and ID tokens held in memory only
- If the keychain is unavailable, fall back to memory-only (re-login required) rather than writing to disk
- Logout deletes the keychain entry
- Token refresh and attachment to all central calls and the WebSocket connection

### 1.10 Team endpoints (proxying the central service)

- Create team, create invite code, join with code, leave team, get my team

### 1.11 Local API (for the frontend)

- FastAPI, bound to `127.0.0.1` only
- CORS limited to the React dev server origin
- Random startup token required on every request
- `GET /auth/token` is the one unauthenticated endpoint, and returns the token only when the `Origin` header matches exactly; the token changes on each restart
- Endpoints for: login/sign-up/logout, session state, team operations, folders (add via dialog, remove, share, unshare), files (list, filter, tags edit, public/private), indexing progress, publish status, search, open local file, expiring files and confirm, transfer request and status, connection state

### 1.12 Local registry (SQLite)

- One row per file: path, content hash, created/modified/in-document dates, index status and failure reason, tags, step state for tag generation, public state, `publish_state`, `published_at`, `expires_at`, `last_confirmed`
- Folder table for watched folders
- Publish queue table
- Folder "shared" status is **derived** (every file under it is public), not stored

---

## 2. React Frontend

Three pages plus a global status indicator.

### 2.1 Login page

- Email and password form
- "Create account" mode (self sign-up, no email verification)
- Error states: wrong credentials, password policy errors, service unavailable
- On startup: fetch the startup token from `GET /auth/token`, check for an existing session, and skip the page if one exists

### 2.2 Search page

- Query box and results list
- Local results: filename, dates, tags if any, **Open** action
- Teammate results: filename, tags, created/modified dates, expiry, **Download** button
    - No owner name or ID shown (deliberately omitted for now)
    - "Owner offline" state shown before the user tries to download
- Download progress and saved path shown on the result row
- States: searching, no results, service unavailable, owner offline, transfer failed

### 2.3 Files and folders page

- **Create or join a team** panel, shown whenever the user has no team (needed before sharing or searching teammates)
- Team info and invite code generation
- Leave team action
- **Add folder** button (opens the native dialog through the agent)
- Per folder: indexing progress (indexed / pending / failed), "X of Y public", **Share current files** (with confirmation, e.g. "Share 142 files with your team?"), **Make all private**, remove
- Bulk share progress ("37 of 142 published")
- File list with status filters: all, public, private, failed, expiring soon
- Per file: tags (editable), public/private control, publish status (`pending` / `published` / `failed`) with retry visibility, failure reason, "no tags" flag, re-confirm action when expiring
- File detail as a side panel on this page (not a separate page)

### 2.4 Global status indicator (every page)

- Agent reachable, signed in, relay connected

### 2.5 Technical notes

- Vite + React
- Polling for live updates, faster while indexing or publishing is in progress and slower when idle
- **(suggested)** TanStack Query for polling and loading/error states; component library left to whoever builds it

---

## 3. Central Service (AWS)

### 3.1 Auth and teams

- Cognito User Pool with an app client that has the password login flow enabled and no client secret (**verify**)
- Pre sign-up Lambda trigger to auto-confirm users, so there is no email verification (**verify**)
- API Gateway JWT authorizer on HTTP routes; callers identified by the token's `sub`
- Lambda authorizer for the WebSocket connect step (**verify**)
- Postgres tables:
    - `teams`: id, name, created_by, created_at
    - `memberships`: user_id (unique, so one team per user), team_id, joined_at
    - `invites`: code, team_id, created_by, expires_at, use_count, optional `max_uses` (no cap for MVP)
- Endpoints: create team, create invite, join with code, get my team, leave team
- Rules:
    - One team per user
    - Any user can create a team; any member can create invites for their own team
    - Invites expire after 7 days (config) and are multi-use
    - Leaving a team removes the user's public files and their WebSocket connection record
    - If the last member leaves, the team and its invites are deleted
- Membership lives in Postgres, not Cognito Groups
- Server derives `team_id` from membership; the agent never sends it

### 3.2 Metadata API

- `public_files` table: `file_id`, `owner_id`, `team_id`, `filename`, `tags`, `file_created_at`, `file_modified_at`, `published_at`, `expires_at`, `last_confirmed`
- Endpoints:
    - `PUT /files/{file_id}`: upsert (publish and re-sync; one row per file even if retried)
    - `DELETE /files/{file_id}`: unpublish
    - `POST /files/{file_id}/confirm`: re-confirmation
    - `GET /files/mine`: caller's published files, for reconciliation
- Server-enforced rules:
    - Users can modify or delete only their own rows
    - All queries scoped to the caller's team
    - Server sets `expires_at` (45 days from publish or confirm, config)
- Bulk share is one `PUT` per file; no batch endpoint

### 3.3 Search endpoint

- Input: topic string and absolute date range (already resolved by the proxy), so no LLM call here
- Filters: caller's team only, exclude the caller's own files, exclude rows past `expires_at`
- Date filter matches if **either** created or modified date falls in the range
- Matching: Postgres full-text search over filename plus tags, with a generated `tsvector` column and GIN index
    - Looser query form (e.g. `websearch_to_tsquery` or OR-ing terms) rather than all-words-must-match **(suggested)**
    - Normalize underscores, dots, and hyphens in filenames to spaces before indexing **(suggested)**
- Empty topic: return all files in the date range, ordered by recency
- Empty date range: search all non-expired team files by topic only
- Ordered by text relevance, falling back to recency; capped result count (e.g. 20, config)
- Response per result: `file_id`, `filename`, `tags`, created/modified dates, `expires_at`, owner online flag. No owner identity.
- Access-log entry per search

### 3.4 Bedrock proxy

- `POST /llm/query`: input is raw query, local date, timezone; output is `topic` (a few plain keywords), `date_from`, `date_to`
    - JSON-only output validated before returning (dates parse, `date_from` not after `date_to`)
    - Invalid output returns an error, and the agent shows "service unavailable"
    - Requires login but not a team
- `POST /llm/tags`: input is excerpt and filename; output is 5 to 8 lowercase keyword tags
    - Excerpt capped server-side (starting at 3,000 characters, config)
    - Output validated for count, length, and plain strings
- Model: Claude Sonnet 5.5; the exact Bedrock model ID or inference profile is a config value
- Excerpts and queries are never stored, and request bodies are never logged
- No per-user usage limits for the demo

### 3.5 Relay (WebSocket and S3 transfer)

- API Gateway WebSocket API; `connections` table (`connection_id`, `user_id`, `connected_at`) updated on connect and disconnect
- Stale connection cleanup when sending fails with "gone"
- If an owner has multiple connections, send to the most recent
- `transfers` table: `transfer_id`, `file_id`, `requester_id`, `owner_id`, `status`, `s3_key`, `created_at`, `updated_at`
- Statuses: `requested`, `uploading`, `ready`, `failed`, `expired`
- Endpoints:
    - `POST /transfer/request`: checks the file exists, isn't expired, is on the caller's team, and the owner is online (otherwise "owner offline"); reuses an in-flight transfer for duplicate requests; creates a presigned PUT URL; sends `upload_request` to the owner
    - Owner acknowledgment and completion endpoints (HTTP)
    - `GET /transfer/{id}`: status; issues the presigned GET URL only when status is `ready`
- No owner approval step (marking public is the consent)
- No file size cap
- Failure handling: if the owner doesn't acknowledge within 60 seconds, the transfer is marked `failed`. Uploads in progress may finish within the presigned URL lifetime.
- S3 objects use random keys (the transfer ID), not filenames
- Short presigned URL lifetimes

### 3.6 Scheduled jobs (EventBridge Scheduler → Lambda)

- **Transfer sweeper**, every minute: delete S3 objects older than 15 minutes, mark stale transfers `expired`
    - Effective lifetime is up to about 16 minutes
    - Day-level S3 lifecycle rule as a backstop **(suggested)**
- **Nightly purge:** delete `public_files` rows past `expires_at`, expired invites, and stale `connections` rows

### 3.7 Access log

- Append-only `access_log` table: `log_id`, `timestamp`, `user_id`, `event_type`, `details` (JSON)
- Events: `search`, `transfer_request`, `publish`, `unpublish`, `confirm`, `team_create`, `team_join`, `team_leave`
- Stores identifiers, counts, and matched `file_id`s only. No filenames, content, or excerpts.
- Database role has `INSERT` only on this table
- Indefinite retention for the MVP (open policy item for legal)
- Viewed by direct database query; no admin screen

### 3.8 Infrastructure and config

- RDS Postgres (db.t3.micro), Lambda behind API Gateway, S3 transit bucket, Secrets Manager or SSM for credentials
- Config values: expiry days (45), expiring-soon window (7), invite lifetime (7 days), excerpt size (3,000), search result cap, publish concurrency, model ID, transfer timeout (60 seconds), sweeper age (15 minutes)

---

## 4. To Verify in AWS Before Building

- Cognito app client with password login flow and no secret
- Pre sign-up Lambda trigger for auto-confirm
- WebSocket authorizer approach and how the agent passes the token on connect
- Bedrock model ID for Sonnet 5.5, and that the sandbox account has model access
- Bedrock model invocation logging is off
- S3 lifecycle granularity (days), which is the reason for the sweeper
- API Gateway WebSocket idle timeout (sets the agent's ping interval)
- API Gateway and Lambda throttling limits (to tune the publish concurrency)

## 5. Tune During Development

- Local similarity threshold for "comes up short"
- Full-text search behavior on real tags and filenames
- Excerpt size
- Publish concurrency

## 6. Prototype Early (Risk)

- Native Windows folder dialog from the agent (blocking behavior, window appearing behind the browser)
- Full relay path: WebSocket → presigned PUT → presigned GET → sweeper
- Windows Credential Manager via `keyring`

## 7. Known Limitations

- Startup-token endpoint is protected only by CORS and origin checks, which doesn't stop a local process
- SSO and MFA out of scope
- No email verification on sign-up
- No Bedrock usage caps
- Transfer works only while the owner's agent is online
- Central search is metadata-only; untagged files are findable only by filename and date
- Tags reflect only the first part of a file
- Either-date matching means a file created long ago but edited recently matches recent date queries
- 15-minute S3 expiry is approximate
- Access log keeps file IDs only, so history is not readable after a file is purged
- One team per user
- Excerpts pass through the central service (not stored or logged)

## 8. Blueprint Updates Needed

- Retention: 90 days → 45 days
- S3 expiry: sweeper Lambda instead of a lifecycle rule
- Bedrock proxied through the central service, not called by the agent
- Membership in Postgres, not Cognito Groups
- Central dates: created, modified, `expires_at`, plus `published_at` and `last_confirmed`
- Add the React frontend and the local SQLite registry
- Add the LLM proxy, transfer tracking, and `connections` tables