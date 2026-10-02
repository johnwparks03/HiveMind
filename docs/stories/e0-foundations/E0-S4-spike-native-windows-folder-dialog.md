# E0-S4: Spike: native Windows folder dialog

- **Epic:** E0 Foundations and risk spikes
- **Track:** Local agent
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E0-S1
- **Spec refs:** Feature_List 1.1; API_Contract `POST /folders/pick`

## Story
As a user, I want to pick a folder with the normal Windows dialog so that I don't type paths.

## Acceptance criteria
- [ ] Given the agent is running, when `POST /folders/pick` is called, then the Windows folder dialog opens without blocking other requests.
- [ ] Selecting a folder returns its path; cancelling returns an empty result, not an error.
- [ ] Approach (thread/process used) is documented for E2-S2.

## Technical notes
- `POST /folders/pick` (API_Contract 2.3) returns `{"path": "C:\\..."}` or `{"path": null}` if cancelled. No error on cancel.
- Must not block the FastAPI event loop: run the dialog in a worker thread/process. Likely tkinter `askdirectory` (or Win32 `IFileDialog`).
- Known risk: the dialog window may appear behind the browser; set it topmost and test. Record the working approach.

## Notes
_(add during implementation)_
