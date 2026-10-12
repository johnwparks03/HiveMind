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
- [x] Given valid credentials, when I sign up then log in, then I receive tokens including a refresh token.
- [x] Duplicate email returns a clear error in the contract envelope. (Cognito raises `UsernameExistsException`, verified by integration test; the agent maps it to `409 user_exists` in E1-S3.)
- [x] All Interface B routes except health require a valid JWT.

## Technical notes
- Central endpoints do not include sign-up/login: the **agent** calls Cognito directly (`SignUp`, `InitiateAuth` with `USER_PASSWORD_AUTH`, `REFRESH_TOKEN_AUTH`). This story provides the pool, client and authorizer wiring plus integration tests.
- Shared auth helper for Lambdas: read `sub` from the verified JWT claims; return `401 unauthorized` envelope on failure.
- Credentials are never logged.

## Notes
- **Built:** shared helpers `central/lambdas/common/auth.py` (`get_caller_sub`, fails closed with `Unauthorized` if claims are missing) and `common/errors.py` (`error_response`, `unauthorized_response`, contract envelope). `/hello` uses them; `/health` has its own open handler (`health.py`). `infra/stack.py` has `add_authed_route()` so the JWT authorizer is the default for every route; `/health` is the only route registered without it.
- **Tests:** `central/tests/test_auth_helpers.py` (offline) and `test_auth_integration.py` (deployed stack, `-m integration`, creates and deletes its own users). Needs `boto3[crt]` when credentials come from `aws login`.
- **Cognito errors the agent must map (E1-S3):** `UsernameExistsException` -> `409 user_exists`; `InvalidPasswordException` -> `400 password_policy` (exact message seen: `Password did not conform with policy: Password not long enough`); `NotAuthorizedException` on login -> `401 invalid_credentials`.
- **Gateway 401 body is not the contract envelope.** Verified: a missing or bad token gets `401 {"message":"Unauthorized"}` from API Gateway, and HTTP APIs cannot customize it. Decision: accept this for gateway-level rejections; the agent treats any 401 from central as `unauthorized`. Lambda-raised 401s use the envelope.
- **Correction to E0-S3:** the authorizer accepts the **ID token as well as the access token**. It matches its audience against `aud` (ID token) or `client_id` (access token), and both equal the app client ID. "Agent sends the access token" is a convention, not enforced by the gateway. No security impact (same user and pool). Covered by `test_authorizer_also_accepts_id_token`.
- **Deployed** to the shared `HiveMind` stack on 2026-10-12; all 8 integration tests passed.
