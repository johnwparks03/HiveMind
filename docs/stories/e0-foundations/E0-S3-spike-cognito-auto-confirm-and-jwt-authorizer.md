# E0-S3: Spike: Cognito auto-confirm and JWT authorizer

- **Epic:** E0 Foundations and risk spikes
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E0-S2
- **Spec refs:** Feature_List 3.1; API_Contract Interface B
- **Flags:** verify-in-AWS

## Story
As a developer, I want to prove Cognito sign-up without email verification and JWT authorization so that auth stories are de-risked.

## Acceptance criteria
- [x] Given a Cognito User Pool with a pre sign-up Lambda trigger, when a user signs up, then they are auto-confirmed and can log in.
- [x] A JWT from login is accepted by the HTTP API authorizer; a missing or bad token returns 401 `unauthorized`.
- [x] Findings (client config, token lifetimes) are recorded in the story.

## Technical notes
- Cognito User Pool, app client with password login flow (`USER_PASSWORD_AUTH`) and **no client secret**.
- Pre sign-up Lambda trigger sets `autoConfirmUser = true` (and auto-verifies email if needed).
- HTTP API JWT authorizer: decide whether it accepts the access token or ID token and record it (answers API_Contract open item 3). Caller is identified by the token `sub`.
- Cognito password policy still applies; capture the exact error text for `password_policy`.

## Notes
- **Token decision (resolves API_Contract open item 3):** JWT authorizer uses the **access token**, not the ID token. The agent must pass the access token in `Authorization: Bearer`. The `sub` claim identifies the caller.
- **Auth flow:** `USER_PASSWORD_AUTH`, no client secret. Confirmed working.
- **Auto-confirm:** pre sign-up Lambda sets `autoConfirmUser = true` and `autoVerifyEmail = true`. Sign-up returns `UserConfirmed: true` immediately — no email step.
- **Password policy:** Cognito default — minimum 8 characters, requires uppercase, lowercase, and digit. No symbols required. Error code for policy violations: `InvalidPasswordException`.
- **Token lifetimes:** access token 1 hour, ID token 1 hour, refresh token 30 days.
- **Verified:** `GET /hello` with valid access token → 200; with missing token → 401; with garbage token → 401.
