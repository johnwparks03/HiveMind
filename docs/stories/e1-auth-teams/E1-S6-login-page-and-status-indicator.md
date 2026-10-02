# E1-S6: Login page and status indicator

- **Epic:** E1 Auth and teams
- **Track:** Frontend
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E1-S2, E1-S3
- **Spec refs:** Feature_List 2.1, 2.4

## Story
As a user, I want a login/create-account page and a status indicator so that I know whether I'm connected.

## Acceptance criteria
- [ ] The page supports login and create-account modes and shows API errors.
- [ ] The UI fetches the startup token from `GET /auth/token` and sends it on every call.
- [ ] A global indicator shows agent reachable, signed in and relay connected.

## Technical notes
- On load: `GET /auth/token` (from the allowed origin), store token in memory, send `X-HiveMind-Token` on every call. Then `GET /session`; if `signed_in`, skip the login page.
- Login page: email/password, 'Create account' toggle. Sign-up calls `/auth/signup` then `/auth/login`. Show errors: wrong credentials, password policy (display Cognito message from `details`), service unavailable.
- Status indicator in the shared layout: agent reachable (request succeeds), signed in, relay state from `GET /session`. Poll slowly when idle.
- TanStack Query suggested; component library is the builder's choice.

## Notes
_(add during implementation)_
