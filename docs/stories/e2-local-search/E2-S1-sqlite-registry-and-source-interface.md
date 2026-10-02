# E2-S1: SQLite registry and Source interface

- **Epic:** E2 Local indexing and search
- **Track:** Local agent
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E1-S2
- **Spec refs:** Feature_List 1.1, 1.12; Blueprint (Source interface)

## Story
As a developer, I want a local registry and a Source abstraction so that later sources can be added.

## Acceptance criteria
- [ ] Tables exist for files, folders and publish queue with migrations.
- [ ] `Source` defines `list_files()` and `get_file_bytes(id)`; `LocalFilesystemSource` implements it.
- [ ] Folder shared status is derived from its files, not stored.

## Technical notes
- SQLite file (path under the user's app data dir; configurable). Use migrations from the start.
- `files`: `file_id` (UUID), `folder_id`, `path`, `content_hash`, `file_created_at`, `file_modified_at`, `doc_date` (in-document, local only), `index_state` (`pending|indexed|failed|missing`), `failure_reason`, `tags` (JSON), `tag_step_state`, `visibility` (`private|public`), `publish_state` (`NULL|pending|published|failed`), `publish_error`, `published_at`, `expires_at`, `last_confirmed`.
- `folders`: `folder_id`, `path`, `scan_state` (`scanning|ready`). `publish_queue`: `file_id`, `op` (`publish|unpublish|resync|confirm`), `attempts`, `next_attempt_at`, `last_error`, `created_at`; one row per file (latest intent wins).
- Folder 'shared' is **derived**: total > 0 and every file public. Never stored.
- `Source` is an abstract class with `list_files()` and `get_file_bytes(id)`; the indexer must go through it.

## Notes
_(add during implementation)_
