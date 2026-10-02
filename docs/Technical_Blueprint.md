
A concrete, AWS-mapped build plan for the core loop: check your own files first, then your teammates' public files, with date-aware queries and transfer that works across separate networks. This is the real demo condition, not a same-Wi-Fi shortcut. Teams/SharePoint as a source is a later addition, not v1.

**Platform:** Windows only for the MVP.

## Change log from v1

|Area|v1|v2|
|---|---|---|
|Retention|90-day default|**45 days**, server-set, re-confirm resets to 45 days from confirmation|
|S3 expiry|Lifecycle rule (~15 min)|**Sweeper Lambda** every minute deleting objects older than 15 minutes; day-level lifecycle rule as a backstop|
|Bedrock / Claude|Direct Claude API or Bedrock, undecided|**Bedrock, Claude Sonnet 5.5, proxied by the central service.** The agent never calls Bedrock directly.|
|Team membership|Cognito Groups|**Postgres** (`teams`, `memberships`, `invites`); one team per user|
|Central dates|`published_at`, `expires_at`, `last_confirmed`|`file_created_at`, `file_modified_at`, `expires_at`, plus `published_at` and `last_confirmed`|
|Central search|Not specified|**Metadata only** (filename, tags, dates) using Postgres full-text search|
|Frontend|Not in blueprint|**React + Vite** app that talks only to the local agent|
|Local state|Chroma only|Chroma **plus a SQLite file registry** and a persistent publish queue|
|Tag generation|Not specified|**Bedrock call at publish time** through the proxy, using an excerpt and filename|
|Transfer notification|Not specified|Requester **polls** transfer status; WebSocket carries only owner `upload_request` messages|
|Accounts|Cognito accounts|Self sign-up, **no email verification** (demo only)|

Items marked **(verify)** are AWS behaviors I believe are correct but have not checked against the docs. They are collected in section 11.

---

## 01 Tech stack, component by component

Everything here either runs free-tier on your AWS sandbox or costs nothing to start (open-source, local compute). The one paid line item is Bedrock calls, which are made once per search and once per published file.

|Component|Technology|Why|
|---|---|---|
|Local agent runtime|Python + FastAPI, bound to `127.0.0.1`|Runs on each person's laptop; same stack as the central service, so one team can read all the code|
|Local file registry|SQLite|One row per file for path, hash, dates, index status, tags, publish state; shared by the watcher, indexer, publish flow, and relay client|
|Local file extraction|PyMuPDF (PDF), python-docx, python-pptx, plain text|General knowledge-transfer coverage (meeting notes, decks, docs)|
|Change detection|watchdog + content hashing|Detects new, changed, moved, and deleted files; hashing avoids re-indexing untouched files|
|Embeddings|sentence-transformers (all-MiniLM-L6-v2), local|Free, no API key, no network call; file content is not sent anywhere just to be indexed|
|Local vector store|Chroma (embedded, file-backed) with per-chunk date metadata|Zero infrastructure; metadata filters make "3 days ago" queries filter by date rather than hoping recency ranks well|
|Credential storage|Windows Credential Manager via `keyring`|Stores only the Cognito refresh token; falls back to memory-only if unavailable|
|Frontend|React + Vite dev server (fixed origin, e.g. `localhost:5173`)|UI for login, search, and file/folder management; talks only to the local agent|
|Natural-language query understanding|Claude Sonnet 5.5 on Amazon Bedrock, called by the central proxy|Splits a request like "meeting notes from 3 days ago" into a topic plus a date range|
|Tag generation|Same Bedrock model, via the proxy|Generates 5 to 8 lowercase keyword tags per file at publish time|
|Central service runtime|Python + FastAPI on AWS Lambda behind API Gateway (HTTP API)|Serverless; scales to zero between demo sessions|
|Agent signaling|API Gateway WebSocket API|Each agent holds a persistent outbound connection, which lets the relay reach a laptop with no public IP|
|File transit|S3 bucket, presigned URLs, random object keys|The only place file bytes touch AWS, and only briefly|
|Central metadata store|RDS Postgres (db.t3.micro), 12-month free tier|Teams, memberships, invites, public-file metadata, connection registry, transfers, access log|
|Auth|Cognito User Pool (no Groups)|Accounts and JWT issuance; team membership is kept in Postgres|
|Sign-up handling|Cognito pre sign-up Lambda trigger **(verify)**|Auto-confirms users so there is no email verification step|
|Scheduled jobs|EventBridge Scheduler → Lambda|Transfer sweeper (every minute) and nightly purge|
|Secrets|Secrets Manager / SSM Parameter Store|DB credentials and config never sit in code|
|Dev / infra|GitHub, Docker Compose for local dev, boto3 / CDK|Reproducible across machines|
|Teams/SharePoint connector (later)|Microsoft Graph API, Entra ID app registration (OAuth delegated)|Not v1; see section 08|

---

## 02 AWS architecture

Everything central lives in AWS, including the brief transit hop for file bytes, since the demo runs across separate networks and laptop-to-laptop is not reachable. The central search below fires only after the local agent's own index comes up short. The central service is step two, not step one.

```
Your laptop                                   Teammate's laptop
┌──────────────────────────┐                 ┌──────────────────────────┐
│ React UI (Vite)          │                 │ React UI (Vite)          │
│   ↕ localhost only       │                 │   ↕ localhost only       │
│ Local agent              │                 │ Local agent              │
│  SQLite · Chroma         │                 │  SQLite · Chroma         │
└───────────┬──────────────┘                 └───────────┬──────────────┘
            │ HTTPS + outbound WebSocket                 │
            ▼                                            ▼
┌─────────────────────────────── AWS SANDBOX ──────────────────────────────┐
│ Cognito (user pool)                                                      │
│ API Gateway: HTTP API + WebSocket API                                    │
│ Lambda: /teams · /files · /search · /llm · /transfer · WS handlers       │
│ Bedrock (Claude Sonnet 5.5), called only by the /llm Lambdas             │
│ RDS Postgres: teams · memberships · invites · public_files ·             │
│               connections · transfers · access_log                       │
│ S3 transit bucket: presigned URLs, 15-minute sweep                       │
│ EventBridge Scheduler → sweeper Lambda (1 min) · purge Lambda (nightly)  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Transfer sequence**

1. Requester's agent: auth + search (or the local search came up short)
2. Requester calls `POST /transfer/request`; server sends `upload_request` over the owner's WebSocket
3. Owner's agent streams the file to a presigned PUT URL
4. Requester polls, sees `ready`, and downloads from a presigned GET URL
5. The sweeper deletes the object after 15 minutes regardless of whether it was downloaded

File bytes pass through S3 only in transit. The metadata store and connection registry never see them.

---

## 03 Model and API key strategy

### Embeddings: spend nothing

Every file chunk is embedded once, on the owner's own laptop, with a free local model (all-MiniLM-L6-v2). No network call, no key, no per-token cost, and file content is not sent anywhere just to be indexed.

### Bedrock: query understanding and tags

All LLM use goes through the central service, which calls Claude Sonnet 5.5 on Bedrock. Laptops need only their Cognito token, not AWS credentials.

- `POST /llm/query` takes the raw query plus the agent's local date and timezone, and returns a topic and an absolute date range.
- `POST /llm/tags` takes a file excerpt and filename, and returns 5 to 8 lowercase keyword tags.

**Content handling**

- The agent sends an excerpt only (starting at 3,000 characters, configurable), with the cap also enforced server-side.
- Excerpts and queries are never stored, and request bodies are never logged.
- File text may be sent to the proxy for tagging. This is a deliberate change from "content never leaves the machine," which now applies to embeddings only.

**Output validation**

- JSON output is validated before it is returned (dates parse, `date_from` is not after `date_to`).
- Invalid output returns an error, and the agent shows "service unavailable."
- Tag output is validated for count, length, and plain strings.

**Usage limits:** none for the demo. Cost is bounded only by default API Gateway and Lambda throttling.

**Configuration:** the Bedrock model ID or inference profile is a config value, copied from the Bedrock console. Confirm that the sandbox account has access to the model, and that Bedrock model invocation logging is off **(verify)**.

---

## 04 Date-aware, general-purpose search

The target query is "pull up the meeting notes from 3 days ago," which is a topic and a time window over whatever file type that meeting produced.

### Local search

- **Extract real dates, not just filenames.** Index the file's created and modified timestamps and, where present, a date written inside the content (a meeting doc's header date often differs from when it was last saved). The in-document date stays local.
- **One call does two jobs.** The proxy returns a topic string and an absolute `date_from` / `date_to` pair, resolved against the agent's local date and timezone so results near midnight are not off by a day.
- **Filter first, then rank.** Chroma metadata filters narrow candidates to the date range before vector similarity ranks within that set.
- **"Comes up short."** If no local result clears a configurable similarity threshold, the agent calls central search. The threshold is tuned during development against real files.
- If the proxy is unreachable, search returns "service unavailable." There is no degraded fallback.

### Central search

- The agent sends the already-resolved topic and date range. Central search does not call the model again.
- **Metadata only:** filename, tags, and dates. Content and embeddings are never searched centrally.
- Scope: the caller's team only, excluding the caller's own files and any rows past `expires_at`.
- **Date match:** a file matches if either its created date or its modified date falls in the range.
- **Matching:** Postgres full-text search over filename plus tags, using a generated `tsvector` column with a GIN index. Use a looser query form (such as `websearch_to_tsquery` or OR-ing terms) and normalize underscores, dots, and hyphens in filenames before indexing. Behavior against realistic tags is untested.
- **Empty topic:** return all files in the date range, ordered by recency.
- **Empty date range:** search all non-expired team files by topic only.
- **Ordering and limit:** text relevance, falling back to recency, capped at a configurable number (e.g. 20).
- **Result fields:** `file_id`, `filename`, `tags`, created and modified dates, `expires_at`, and whether the owner is online. Owner identity is not shown.
- Untagged files are findable only by filename and date.
- A possible later feature: if metadata matching proves too weak, the central service could ask each teammate's agent to run an embedding search.

---

## 05 Cross-network transfer via relay

Pull-through-owner means the owner's laptop must be reachable by a teammate's laptop, and the demo runs on separate networks, so plain LAN reachability is not available. This is the actual MVP mechanism, not a stretch goal.

### Signaling: outbound-only WebSocket

- Each local agent opens an outbound persistent connection to an API Gateway WebSocket API after login.
- The central service pushes an `upload_request` down that existing connection rather than dialing the laptop, using the same reverse-tunnel idea as tools like ngrok.
- WebSocket APIs likely need a Lambda authorizer on connect to validate the Cognito token **(verify)**.
- The agent sends periodic pings. The interval depends on the API Gateway idle timeout **(verify)**.
- A `connections` table holds `connection_id`, `user_id`, and `connected_at`. If an owner has several connections, the most recent is used; stale ones are removed when sending fails with a "gone" error.

### Bytes: presigned S3, auto-expiring

- The owner's agent **streams** the file to a short-lived presigned PUT URL (no loading the whole file into memory).
- The requester downloads from a presigned GET URL, issued only when the requester polls and sees `ready`.
- Objects use random keys (the transfer ID), not filenames.
- **Sweeper Lambda** (EventBridge Scheduler, every minute) deletes objects older than 15 minutes and marks stale transfers `expired`. Because it runs once a minute, the effective lifetime is up to about 16 minutes.
- S3 lifecycle rules work in whole days to my knowledge **(verify)**, which is why a sweeper is used. A day-level lifecycle rule is kept as a backstop in case the sweeper fails.

### Transfer flow and states

1. Requester's agent calls `POST /transfer/request` with a `file_id`.
2. Server checks that the file exists, has not expired, and belongs to the requester's team, then checks that the owner has a live connection. Otherwise it returns "owner offline."
3. If a transfer for the same file and requester is in flight, it is reused.
4. Server creates a `transfers` record, generates a presigned PUT URL, and sends `upload_request` to the owner.
5. Owner's agent checks that the file is still public and still on disk, acknowledges, streams it, then reports completion over HTTP.
6. Requester's agent polls `GET /transfer/{id}` every 1 to 2 seconds until `ready` or `failed`, then downloads.

`transfers` statuses: `requested`, `uploading`, `ready`, `failed`, `expired`.

**Rules**

- No owner approval step. Marking a file public is the consent.
- No file size cap.
- If the owner does not acknowledge within 60 seconds, the transfer is marked `failed`. An upload already in progress may finish within the presigned URL's lifetime.
- Transfers work only while the owner's agent is online.
- Downloads land in the Windows Downloads folder, with a suffix added on filename collisions.

### The trade-off, stated plainly

This is a real change from "AWS never touches file bytes." Bytes now make a brief, auto-deleted stop in S3 instead of staying fully peer-to-peer, which is necessary once you cannot assume both laptops share a network. The mitigation is that the stop is transient and never written to the permanent metadata store. A true end-to-end peer channel (WebRTC + TURN) is the more correct long-term answer but carries real setup risk for a live demo on a fixed deadline.

---

## 06 Auth, teams, and the local trust boundary

### Identity

- Cognito User Pool with an app client that has the password login flow enabled and no client secret **(verify)**.
- Self sign-up with no email verification for the MVP, using a pre sign-up Lambda trigger **(verify)**. Cognito's password policy still applies.
- API Gateway JWT authorizer on HTTP routes. Lambdas identify the caller by the token's `sub`.
- The React login form posts credentials to the local agent, which calls Cognito. Credentials are never stored or logged.
- The agent stores only the refresh token, in Windows Credential Manager. Access and ID tokens stay in memory.

### Teams (Postgres)

- `teams`: id, name, created_by, created_at
- `memberships`: user_id (unique, so one team per user), team_id, joined_at
- `invites`: code, team_id, created_by, expires_at, use_count, optional `max_uses` (no cap for the MVP)

**Rules**

- Any user can create a team. Any member can create invite codes for their own team.
- Invite codes expire after 7 days (configurable) and are multi-use.
- A user in a team cannot join or create another until they leave.
- Leaving a team removes the user's public files from central metadata and drops their connection record.
- If the last member leaves, the team and its invites are deleted.
- The server derives `team_id` from membership. The agent never sends it.
- Membership is kept in Postgres rather than Cognito Groups, because group membership is baked into the token and changes would not take effect until it refreshes.

### Frontend-to-agent trust

- The agent binds to `127.0.0.1` only.
- CORS allows only the React dev server's origin.
- The agent generates a random token at startup and requires it on every request. It is served from one unauthenticated endpoint, `GET /auth/token`, which returns the token only when the `Origin` header matches exactly.
- **Known limitation:** CORS is enforced by browsers, so this blocks a malicious webpage but not another local process, which can set any `Origin` header.
- SSO and MFA are out of scope for the MVP.

---

## 07 Local agent and React frontend

### Local agent responsibilities

- **Folders:** add and remove watched folders through a native Windows folder dialog opened by the agent (recursive).
- **Indexing:** extract, chunk, embed, and store in Chroma, with registry updates for status and failures.
- **Search:** local search, central fallback, merged results labeled local vs. teammate.
- **Publish:** per-file and per-folder, through the pipeline and persistent queue described below.
- **Relay:** WebSocket client, upload handler, and download flow.
- **Open file:** launch a local result in its default program via an agent endpoint.

### Publish pipeline and queue

- **Tags are generated at publish time**, not at indexing time, so Bedrock is called only for files someone actually shares.
- Per file: generate tags, then send metadata. If tagging fails, retry a few times, then publish with empty tags.
- When a public file's content changes, metadata is re-synced but existing tags are **not** regenerated.
- A persistent SQLite queue covers publish, unpublish, re-sync, and confirm. It uses exponential backoff with a retry cap, survives restarts, keeps only the latest intent per file, and relies on idempotent central operations.
- Sending is throttled, starting at 5 concurrent requests, to avoid API Gateway and Lambda throttling during bulk shares.
- Each file has a `publish_state` of `pending`, `published`, or `failed`.
- **Reconciliation:** the agent periodically calls `GET /files/mine` and corrects its registry when files were purged, expired, or removed (for example after leaving a team).

### Folder sharing

- "Share current files" is a **one-time action** that publishes the files currently under the folder, including subfolders, after a confirmation ("Share 142 files with your team?"). Files added later stay private.
- A folder displays as "shared" only when every file under it is public (derived, not stored). Turning it off makes all files under it private.
- Files with no tags are published anyway and flagged "no tags" in the UI.

### Frontend (React + Vite)

Three pages plus a global status indicator.

1. **Login:** email and password, a "Create account" mode, and error states (wrong credentials, password policy, service unavailable). Skipped if the agent already has a valid session.
2. **Search:** query box and results. Local results have an **Open** action. Teammate results have **Download**, with "owner offline," download progress, and the saved path shown on the row. The owner is not displayed.
3. **Files and folders:**
    - A "Create or join a team" panel shown whenever the user has no team, with invite code generation and leave-team actions
    - Add folder, per-folder indexing progress, "X of Y public," share and unshare actions, bulk-share progress
    - A file list with status filters (all, public, private, failed, expiring soon), editable tags, publish status, failure reasons, and re-confirm for expiring files
    - File detail in a side panel
4. **Global status indicator** on every page: agent reachable, signed in, relay connected.

The frontend uses polling for live updates (faster while indexing or publishing is active, slower when idle).

---

## 08 Teams/SharePoint as a source (later)

A lot of what people mean by "meeting notes" lives in a Teams drive or SharePoint, not a local folder. This is real value but not v1. Skip building it for the MVP and design the indexer so adding it later is additive, not a rewrite.

### Design now, build whenever you pick it up

Give the indexer a single `Source` interface (`list_files()` and `get_file_bytes(id)`) with the local filesystem as its only v1 implementation. A `SharePointSource` (via Microsoft Graph) becomes a second implementation later, authenticated with its own OAuth token. Nothing in the sync, broker, or transfer logic needs to change when that happens.

- **v1:** local filesystem only, with watchdog for change detection and direct file reads.
- **When you pick it up:** the real risk is approval, not code. A `SharePointSource` needs an Entra ID app registration with Microsoft Graph permissions (delegated `Files.Read` at minimum), which typically needs IT or admin consent. That approval can take longer than the integration itself, so submit the request as soon as you decide to build it.

---

## 09 Data retention and expiry

Anything HiveMind stores centrally, even just metadata, needs a shelf life. Indefinite sharing by default is the kind of thing that fails a compliance review at a firm like this one.

### `public_files` (central metadata table)

```
file_id           text primary key      -- UUID generated by the local agent
owner_id          text
team_id           text                  -- derived server-side from membership
filename          text
tags              text[]
file_created_at   timestamp
file_modified_at  timestamp
published_at      timestamp
expires_at        timestamp             -- set by server: published_at + 45 days
last_confirmed    timestamp             -- re-confirm sets expires_at to now + 45 days
```

The 45-day default is a placeholder. Swap it for whatever the firm's actual retention policy requires.

### Metadata API

- `PUT /files/{file_id}`: upsert, used for publish and re-sync
- `DELETE /files/{file_id}`: unpublish
- `POST /files/{file_id}/confirm`: expiry re-confirmation
- `GET /files/mine`: the caller's published files, for reconciliation

The server enforces that users modify only their own rows and that every query is scoped to the caller's team.

### Enforcement

- **Nightly purge:** an EventBridge-scheduled Lambda deletes `public_files` rows past `expires_at`, expired invites, and stale `connections` rows. Search already excludes expired rows, so a file ages out on its own even before the purge runs.
- **Active re-consent:** files within 7 days of expiry (configurable) appear as "expiring soon" in the UI, and the owner re-confirms rather than silently extending. Continued visibility is always a recent, deliberate choice.

### Access log

A separate, append-only table that a real compliance review will ask for.

```
access_log: log_id, timestamp, user_id, event_type, details (JSON)
```

- **Events:** `search`, `transfer_request`, `publish`, `unpublish`, `confirm`, `team_create`, `team_join`, `team_leave`. Sign-in events live in Cognito and are not duplicated here.
- Stores identifiers, counts, and matched `file_id`s only. **No filenames, file content, or query excerpts.** After a file is purged, its logged `file_id` can no longer be resolved to a name.
- The Lambda's database role has `INSERT` only on this table.
- Retention is indefinite for the MVP. This is a policy decision for legal, not engineering.
- Viewed by direct database query. There is no admin screen.

---

## 10 What to build now vs. design for later

|Decision|MVP (4 weeks)|Fast-follow / designed for later|
|---|---|---|
|File types|PDF, DOCX, PPTX, TXT|Additional types as needed|
|Date-aware search|Built in week 1, part of core search from day one|Not specified|
|File sources|Local filesystem only|`Source` interface ready now; Teams/SharePoint via Graph API is the priority next connector|
|Networking|WebSocket relay + presigned S3 transit, cross-network from day one|True peer-to-peer (WebRTC/TURN) if bytes-via-AWS proves unacceptable|
|Central search|Metadata only (filename, tags, dates)|Ask each teammate's agent to run an embedding search if metadata matching is too weak|
|Teams|One team per user|Multiple teams|
|Sign-up|Self sign-up, no email verification|Verified accounts, SSO, MFA|
|LLM cost control|None|Per-user usage limits|
|Owner identity in results|Omitted|Name or email lookup|
|Frontend|React + Vite dev server|Packaged desktop wrapper (not discussed; listed only as a possibility)|

_Note: the last row of the v1 blueprint's table was cut off in the PDF text I received, so I could not carry it over. If it contained a decision, please add it back._

---

## 11 Open items

### Verify in AWS before building

- Cognito app client with the password login flow and no secret
- Pre sign-up Lambda trigger for auto-confirm
- WebSocket authorizer approach, and how the agent passes the token on connect
- Bedrock model ID for Claude Sonnet 5.5, and that the sandbox has model access
- Bedrock model invocation logging is off
- S3 lifecycle granularity (days), which is why the sweeper exists
- API Gateway WebSocket idle timeout (sets the agent's ping interval)
- API Gateway and Lambda throttling limits (to tune the 5-concurrent publish throttle)

### Tune during development

- Local similarity threshold for "comes up short"
- Full-text search behavior on real tags and filenames
- Excerpt size (3,000 characters to start)
- Publish concurrency

### Prototype early (risk)

- Native Windows folder dialog from the agent (blocking behavior, window appearing behind the browser)
- The full relay path: WebSocket → presigned PUT → presigned GET → sweeper
- Windows Credential Manager via `keyring`

### Known limitations

- The startup-token endpoint is protected only by CORS and origin checks, which does not stop a local process
- SSO and MFA out of scope; no email verification on sign-up
- No Bedrock usage caps
- Transfer works only while the owner's agent is online
- Central search is metadata-only; untagged files are findable only by filename and date
- Tags reflect only the excerpt, not the whole file
- Either-date matching means a file created long ago but edited recently matches recent date queries
- The 15-minute S3 expiry is approximate (up to about 16 minutes)
- The access log keeps `file_id`s only, so history is not readable after a purge
- File excerpts pass through the central service for tagging (not stored or logged)
- One team per user
- Access log retention is an open policy item for legal