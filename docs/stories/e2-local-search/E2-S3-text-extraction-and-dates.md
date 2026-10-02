# E2-S3: Text extraction and dates

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E2-S1
- **Spec refs:** Feature_List 1.3

## Story
As a user, I want text pulled from my documents so that search can find them.

## Acceptance criteria
- [ ] PDF, DOCX, PPTX and TXT yield text; corrupt files are recorded with a failure reason and the agent keeps running.
- [ ] Filesystem created and modified dates are captured per file.
- [ ] In-document dates stay local.

## Technical notes
- Libraries: PyMuPDF (PDF), python-docx, python-pptx, plain text (try UTF-8, fall back to a tolerant decode).
- On any failure set `index_state=failed` with a short `failure_reason` (e.g. 'no extractable text', 'corrupt file', 'password protected'); never raise out of the worker.
- Dates: `file_created_at`/`file_modified_at` from the filesystem (UTC, ISO 8601). In-document date: best-effort regex over the first part of the text; stored locally only and never sent centrally.

## Notes
_(add during implementation)_
