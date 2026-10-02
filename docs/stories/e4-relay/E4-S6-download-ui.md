# E4-S6: Download UI

- **Epic:** E4 Relay and download
- **Track:** Frontend
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E4-S4, E3-S9
- **Spec refs:** Feature_List 2.2

## Story
As a user, I want to download a teammate's file with clear status.

## Acceptance criteria
- [ ] Download button shows progress and completion.
- [ ] 'Owner offline' is shown when the owner is not connected.
- [ ] The download button is disabled while a request is in flight.

## Technical notes
- Teammate result row: **Download** button calls `POST /transfers`; poll `GET /transfers/{id}` (about every 1-2 s) and show status, progress and saved path.
- States: owner offline (shown from `owner_online=false` before clicking), requested/uploading/downloading, downloaded (show `saved_path`), transfer failed with a message per `error_code`. Disable the button while a request is in flight.
- On page refresh, use `GET /transfers` to resume displaying active transfers.

## Notes
_(add during implementation)_
