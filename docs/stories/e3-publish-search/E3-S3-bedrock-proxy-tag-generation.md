# E3-S3: Bedrock proxy: tag generation

- **Epic:** E3 Publish and central search
- **Track:** Central service
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E2-S6
- **Spec refs:** Feature_List 3.4; `POST /llm/tags`

## Story
As an agent, I want tags suggested from an excerpt so that published files are discoverable.

## Acceptance criteria
- [ ] Given an excerpt up to 3,000 characters, when `/llm/tags` is called, then tags are returned.
- [ ] Oversized excerpts return 400 `invalid_request`.

## Technical notes
- `POST /llm/tags` request `{filename, excerpt}` -> `{tags:[...]}`: 5 to 8 lowercase keyword strings.
- Truncate the excerpt server-side to `EXCERPT_MAX_CHARS` (3,000). Validate count (5-8), length per tag, plain strings; invalid output or Bedrock error -> `503 service_unavailable`.
- Never store or log the excerpt.

## Notes
_(add during implementation)_
