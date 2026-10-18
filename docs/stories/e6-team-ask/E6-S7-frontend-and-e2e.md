# E6-S7: Frontend toggle and end-to-end verification

- **Epic:** E6 Ask over teammates' documents
- **Track:** Frontend + All tracks
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E6-S6
- **Spec refs:** `frontend/src/pages/AskPage.jsx`, Feature_List 2.x

## Story
As a user, I want to include teammates' files in Ask and see where answers came from.

## Acceptance criteria
- [x] "Include teammates' files" toggle on the Ask page.
- [x] Teammate sources show a "Request download" action (existing transfer flow) instead of Open.
- [x] Copy updated, including a note that published files' contents are readable by teammates.
- [ ] E2E: owner publishes a doc and goes offline; requester asks a question only that doc answers; the answer cites it.
- [ ] E2E: owner unpublishes; chunks are gone and no longer returned.
- [x] README and CLAUDE.md Commands/Known limitations in sync.

## Notes
Implemented (2026-10-17). Decisions confirmed with the user: the switch is off by default and remembered for the browser session (`sessionStorage`); consent is wording only, with no new dialog for single-file Make public.

**Frontend**
- `lib/ask.js` (+ tests): `isTeammateSource` (a missing `source` means local), `skippedReasonText` for `local_scope`, `no_topic`, `date_filter`, `no_team`, `central_unavailable`, `teammateScopeHint`, and the session-storage load/save for the switch.
- `lib/transfer.js` (+ tests): the download wording moved out of `TeammateResultCard`, now also covering `owner_offline` and `upload_timeout` failures and the `own_file` start error, which the old inline map missed.
- `components/TransferControl.jsx`: the download button and progress extracted from `TeammateResultCard` (same markup and behaviour; Search still greys it out for an offline owner). Ask sources use it too.
- `api/client.js` (+ tests): `askInChat` and `ask` send `include_teammates`; `askInChat` now resolves to `{ messages, teammateSkippedReason }`, because the reason is only on the live answer and the page refetches the saved chat.
- `pages/AskPage.jsx`: the switch, a hint when specific files are picked, the skip note under the latest answer (cleared on the next question, a new chat, another chat), teammate sources with a Teammate badge and Download instead of Open, and copy that mentions teammates' files.
- Consent wording (`lib/sharing.js` + tests): the folder and bulk "Make public" confirms say teammates can read the contents, including through Ask; unshare confirms say they can no longer read them; the single-file button has a tooltip; Files and Account page text corrected. The Team page text was already accurate and is unchanged.

**Checks run:** `node --test src` 63 passed (was 47 before this story); `npm run build` succeeds; `npm run lint` shows only older warnings in files this story does not change (`ScopePicker.jsx`, one in `FilesPage.jsx`). There are no component tests and I cannot click through the UI from here, so the visual behaviour and the Search download regression are covered by the manual check.

**Not yet done: the two end-to-end criteria.** `docs/e2e/README.md` has the 12-step two-person checklist, `docs/e2e/fixtures/` has the files (`falcon-budget.txt` 5 chunks, `long-handbook.txt` 300 chunks = three full 100-chunk batches) and `docs/e2e/mine.py` lists a user's published files with their `chunk_count` (not yet run against the live stack). Run it, record the result here, and tick the two E2E boxes. If it passes, also tick the open items in the E6-S5 notes (full-size batch through API Gateway) and E6-S6 notes (the real two-agent run).

No new endpoints, so no new Postman folder.

**Update 2026-10-18 (after the first end-to-end run):** the narrowed-scope rule (`local_scope`) was removed on request. Picking files or folders now narrows only the user's own files; teammates' files are searched whichever are picked. The skip reasons are now `no_topic`, `date_filter`, `no_team` and `central_unavailable`.

**Fixes after the first end-to-end run (2026-10-18)** - four things the run turned up:
1. **Downloads failed with "The upload didn't finish in time".** Cause (found by reading the code and sending the exact request to a local server): the owner's agent streamed the file with a bare generator, which httpx sends as `Transfer-Encoding: chunked` with no `Content-Length`; S3 refuses that for a presigned PUT (501 NotImplemented), the agent swallowed the error and reported `upload_error`, which central stores as `upload_failed`. This path had never run against real S3 (the relay tests replace `httpx.put`). Fix in `agent/app/central/relay.py`: send the file's exact `Content-Length` while still streaming in pieces, and log the HTTP status and S3 error code (never the URL, which carries credentials) when an upload fails. Tests send the real request to a local server and check it arrives with a length and not chunked. **Not yet confirmed against real S3** (the AWS login had expired, so no live probe); the re-run of the end-to-end download is the confirmation. The message `upload_failed` no longer says the upload "didn't finish in time", since it is also used when the owner's computer reports a failed upload.
2. **Narrowed scope removed.** Picking files or folders now narrows only the user's own files; teammates' files are searched whichever are picked. The `local_scope` reason, the hint on the Ask page and its tests are gone; the contract, feature list, blueprint, e2e checklist and the Postman request were updated.
3. **Folder watcher.** New `agent/app/folders/watcher.py` (watchdog): an edit, new file, move or delete in an added folder triggers a rescan after the folder has been quiet for 3 s (at most 30 s if changes keep coming). Only PDF/DOCX/PPTX/TXT count and Office/editor temp files are ignored. Scans of one folder are now serialized (the watcher, the Rescan button and add-folder could otherwise overlap). At startup each folder is rescanned once in the background to catch edits made while the agent was off (`WATCH_SCAN_ON_START`; switch it off if the Bedrock tagging of untagged files at startup is a concern). Folders are watched when added and unwatched when removed. 31 tests, including one with the real observer that edits, adds and deletes files in a temporary folder.
4. **Spinner on Download.** The button shows a spinner and "Requesting..." while the request starts, a spinner in the status pill while the owner sends the file (no blank moment before the first status), and an expired transfer now shows a message with Retry instead of nothing.

