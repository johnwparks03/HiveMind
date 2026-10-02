# E0-S6: Spike: keyring refresh-token storage

- **Epic:** E0 Foundations and risk spikes
- **Track:** Local agent
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E0-S1
- **Spec refs:** Feature_List 1.9

## Story
As a user, I want my login to survive an agent restart without storing passwords on disk.

## Acceptance criteria
- [ ] Given a stored token, when the agent restarts, then the token is read from Windows Credential Manager via `keyring`.
- [ ] If `keyring` is unavailable, the agent falls back to memory-only and says so.
- [ ] Deleting the entry works.

## Technical notes
- Use `keyring` with a fixed service name (e.g. `hivemind`) and the user's email as the username. Store **only** the Cognito refresh token.
- Access and ID tokens stay in memory. Never write tokens to disk; if `keyring` raises, fall back to memory-only and surface that in `GET /session`.

## Notes
_(add during implementation)_
