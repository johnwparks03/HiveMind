# HiveMind local agent

Local-only slice today: folder indexing + local search, no central service, no auth.
Feature_List 1.1-1.5, 1.11, 1.12 (local parts only).

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

## Try it (PowerShell)

```powershell
$token = (Invoke-RestMethod -Uri http://127.0.0.1:8420/auth/token -Headers @{Origin="http://localhost:5173"}).token
$headers = @{ "X-HiveMind-Token" = $token }

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/folders -Headers $headers -ContentType "application/json" `
  -Body (@{ path = "C:\Users\you\Documents\some-folder" } | ConvertTo-Json)

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8420/search -Headers $headers -ContentType "application/json" `
  -Body (@{ query = "meeting notes from 3 days ago" } | ConvertTo-Json)
```

## What's built

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
- Central service integration: auth, teams, publish, central search, relay transfer, the
  optional `/llm/query` enhancement (Technical_Blueprint.md §03)
- Native Windows folder-picker dialog — `POST /folders` takes a path string directly
- Tests

## Verified end-to-end (2026-10-05)

Folder add → scan/index → chat query → date-filtered search → no-results case →
open file, all exercised through the real React UI against a running agent.
Confirmed and fixed along the way: CORS preflight (`OPTIONS`) requests were being
rejected by the startup-token middleware, which would have broken every POST from
the browser.
