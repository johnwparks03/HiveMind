# E5-S5: Integration tests and demo script

- **Epic:** E5 Retention and hardening
- **Track:** All tracks
- **Estimate:** L
- **Priority:** MVP
- **Depends on:** E4-S6
- **Spec refs:** All

## Story
As a team, we want an end-to-end test and a demo script so the MVP is demonstrable.

## Acceptance criteria
- [ ] Two-machine flow works: sign up, create/join team, add folder, publish, teammate search, download.
- [ ] Automated tests cover the critical API paths.
- [ ] A written demo script exists.

## Technical notes
- Automated: API tests for each interface's happy paths and key errors (`no_team`, `owner_offline`, `forbidden`, `invite_expired`).
- Manual two-machine script: sign up both users, user 1 creates a team and invite, user 2 joins, user 1 adds a folder and publishes, user 2 searches 'meeting notes from 3 days ago', downloads, confirms file contents match.
- Prepare sample files (PDF, DOCX, PPTX, TXT) with known dates for the demo. Tune the 'comes up short' threshold and full-text search against them.

## Notes
_(add during implementation)_
