# E3-S4: Tag generation pipeline

- **Epic:** E3 Publish and central search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E3-S3, E2-S4
- **Spec refs:** Feature_List 1.6

## Story
As a user, I want tags generated when I publish so that teammates can find my file.

## Acceptance criteria
- [ ] Each step (excerpt, tags, publish) records state and retries on failure.
- [ ] User-edited tags are used as-is.
- [ ] A file with no tags is flagged 'no tags'.

## Technical notes
- Excerpt = first `EXCERPT_MAX_CHARS` characters of extracted text (config). Send with the filename via the shared central client.
- Step state per file in SQLite (e.g. `tag_step_state`: `none|tagged`), so a retry doesn't repeat a finished tag call. Retry the tag call a few times (suggest 3, record it), then continue with empty tags and flag `no_tags`.
- If the file already has tags (generated earlier or user-edited), skip the tag call and send them as-is (API_Contract settled item 3).
- `PUT /files/{id}/tags` `{tags}` -> `200 File`; if public, queue a `resync`. Editing tags does not extend expiry.

## Notes
_(add during implementation)_
