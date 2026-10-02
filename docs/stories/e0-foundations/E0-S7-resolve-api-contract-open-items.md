# E0-S7: Resolve API contract open items

- **Epic:** E0 Foundations and risk spikes
- **Track:** All tracks
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** none
- **Spec refs:** API_Contract section 7

## Story
As a team, we want the 8 open items decided so that the contract can be frozen and tracks don't diverge.

## Acceptance criteria
- [ ] Each open item (date range format, `POST /transfers/{id}/open`, startup-token header/port, pagination, WebSocket token passing, team-removal notification, presigned PUT headers, tags-as-is UI hint) has a recorded decision.
- [ ] API_Contract.md is updated and marked frozen for MVP.
- [ ] Optional: an OpenAPI YAML is generated from it.

## Technical notes
- Decisions needed (see API_Contract section 7 'Still open'): 1 date range format (ISO date-times with offset vs plain dates), 2 keep `POST /transfers/{id}/open` or drop it, 3 header name/port/token type, 4 pagination (cursors on `GET /files` and `GET /files/mine`; may drop for demo), 5 WebSocket token passing (from E0-S5), 6 team-removal notification (currently none), 7 presigned PUT headers (from E0-S5), 8 UI hint that pre-set tags are used as-is.
- Move resolved items from 'Still open' to 'Settled' in the doc and mark the contract frozen. Changes after freeze need all three tracks to agree.

## Notes
_(add during implementation)_
