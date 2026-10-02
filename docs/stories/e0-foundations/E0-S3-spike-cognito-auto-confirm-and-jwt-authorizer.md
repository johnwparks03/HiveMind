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
- [ ] Given a Cognito User Pool with a pre sign-up Lambda trigger, when a user signs up, then they are auto-confirmed and can log in.
- [ ] A JWT from login is accepted by the HTTP API authorizer; a missing or bad token returns 401 `unauthorized`.
- [ ] Findings (client config, token lifetimes) are recorded in the story.

## Technical notes
- Cognito User Pool, app client with password login flow (`USER_PASSWORD_AUTH`) and **no client secret**.
- Pre sign-up Lambda trigger sets `autoConfirmUser = true` (and auto-verifies email if needed).
- HTTP API JWT authorizer: decide whether it accepts the access token or ID token and record it (answers API_Contract open item 3). Caller is identified by the token `sub`.
- Cognito password policy still applies; capture the exact error text for `password_policy`.

## Notes
_(add during implementation)_
