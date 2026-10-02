# E1-S1: Cognito sign-up, login and JWT authorizer

- **Epic:** E1 Auth and teams
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E0-S3
- **Spec refs:** Feature_List 3.1
- **Flags:** verify-in-AWS

## Story
As a user, I want to create an account and log in so that I can use central features.

## Acceptance criteria
- [ ] Given valid credentials, when I sign up then log in, then I receive tokens including a refresh token.
- [ ] Duplicate email returns a clear error in the contract envelope.
- [ ] All Interface B routes except health require a valid JWT.

## Technical notes
- Central endpoints do not include sign-up/login: the **agent** calls Cognito directly (`SignUp`, `InitiateAuth` with `USER_PASSWORD_AUTH`, `REFRESH_TOKEN_AUTH`). This story provides the pool, client and authorizer wiring plus integration tests.
- Shared auth helper for Lambdas: read `sub` from the verified JWT claims; return `401 unauthorized` envelope on failure.
- Credentials are never logged.

## Notes
_(add during implementation)_
