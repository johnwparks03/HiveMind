# HiveMind local agent

Local search plus sign-in: folder indexing + local search, and Cognito login with a shared
central API client. Teams, publish, central search and relay are not built yet.
Feature_List 1.1-1.5, 1.9, 1.11, 1.12 (local parts only).

## Setup (one-time)

```
cd agent
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

The first real search will download the embedding model (`all-MiniLM-L6-v2`, ~90MB)
from Hugging Face. That needs normal internet access and happens once; it's cached
under `%USERPROFILE%\.cache\huggingface` after that.

## Run

```
.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8420
```

The React chat UI (`frontend/`) talks to this automatically — run `npm run dev` there
and open `http://localhost:5173`.

**No internet access / testing without the real model:** set
`HIVEMIND_FAKE_EMBEDDINGS=1` before starting the agent to use a deterministic
hash-based stand-in instead of downloading `all-MiniLM-L6-v2`. Indexing and date
filtering work identically; semantic ranking doesn't (it only matches on exact text
reuse). Useful for quick smoke tests or CI — never use it for a real demo.

## Central service config

Login talks to Cognito and the central API. Copy `.env.example` to `.env` (gitignored,
never commit it) and fill in the CDK stack outputs:

```
copy .env.example .env
aws cloudformation describe-stacks --stack-name HiveMind --region us-east-1 --query "Stacks[0].Outputs" --output table
```

- `HIVEMIND_COGNITO_CLIENT_ID` = `UserPoolClientId`
- `HIVEMIND_CENTRAL_API_URL` = `HttpApiUrl`
- `HIVEMIND_COGNITO_REGION` (optional, default `us-east-1`)

Variables already set in the shell override `.env`. The values only change if the stack's
resources are recreated (destroy + deploy), so re-run the command above if login starts failing
after a teammate's deploy.

If they're unset or blank the agent still starts and local search works. `/auth/signup` and
`/auth/login` return 503 `service_unavailable` with `details.missing` naming the variable, and
`/session` reports `central_reachable: false`.

## Tests

```
.venv\Scripts\python -m pytest tests
```

## Try it (PowerShell)

```powershell
$token = (Invoke-RestMethod -Uri http://127.0.0.1:8420/auth/token -Headers @{Origin="http://localhost:5173"}).token
$headers = @{ "X-HiveMind-Token" = $token }

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/folders -Headers $headers -ContentType "application/json" `
  -Body (@{ path = "C:\Users\you\Documents\some-folder" } | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/search -Headers $headers -ContentType "application/json" `
  -Body (@{ query = "meeting notes from 3 days ago" } | ConvertTo-Json)
```

Login (after the headers above):

```powershell
$cred = @{ email = "you@firm.com"; password = "..." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/auth/signup -Headers $headers -ContentType "application/json" -Body $cred
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/auth/login  -Headers $headers -ContentType "application/json" -Body $cred
Invoke-RestMethod -Uri http://127.0.0.1:8420/session -Headers $headers
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/auth/logout -Headers $headers
```

## What's built

- `POST /auth/signup|login|logout` and `GET /session` (Cognito sign-in, refresh token in Windows Credential Manager, shared central API client in `app/central/client.py`)
- `Source` interface + `LocalFilesystemSource` (recursive, PDF/DOCX/PPTX/TXT)
- Folder add + scan: content-hash change detection, registers/re-indexes/removes files
- Extraction with in-document date detection (best-effort header scan)
- Chunking, local embeddings (sentence-transformers), Chroma storage with date metadata
- Local deterministic query parser (`dateparser` + regex) — no network call, no API key
- Local search: date filter first, then vector ranking, grouped to one result per file
- `POST /files/{id}/open` launches the file in its Windows default app
- Startup-token auth on every endpoint except `GET /auth/token`

## Not built yet

- Continuous file watcher (watchdog) — only initial/on-demand scan right now (`POST /folders/{id}/rescan`)
- Central service integration beyond sign-in: teams (E1-S4/S5), publish, central search, relay
  transfer, the optional `/llm/query` enhancement (Technical_Blueprint.md §03). `GET /session`
  returns `team: null` and `relay: "disconnected"` until then
- Native Windows folder-picker dialog — `POST /folders` takes a path string directly
- Frontend login page (E1-S6); the agent endpoints it needs exist

## Verified end-to-end (2026-10-05)

Folder add → scan/index → chat query → date-filtered search → no-results case →
open file, all exercised through the real React UI against a running agent.
Confirmed and fixed along the way: CORS preflight (`OPTIONS`) requests were being
rejected by the startup-token middleware, which would have broken every POST from
the browser.
