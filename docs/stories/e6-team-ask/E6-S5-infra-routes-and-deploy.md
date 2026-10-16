# E6-S5: Infra routes, sizing and deploy

- **Epic:** E6 Ask over teammates' documents
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E6-S3, E6-S4
- **Spec refs:** `infra/stack.py` (routes, Aurora, Lambdas), CLAUDE.md AWS section

## Story
As the team, I want the new endpoints deployed to the shared stack so that agents can use them.

## Acceptance criteria
- [ ] Routes for `PUT /files/{id}/chunks` (added in E6-S3) and `POST /retrieval/search` added with the JWT authorizer.
- [ ] Lambda memory, timeout and request-size settings fit batch ingest and vector search.
- [ ] Aurora capacity adjusted if E6-S2 found it necessary.
- [ ] `cdk diff` reviewed and the deploy coordinated with the team before `cdk deploy`.
- [ ] Integration tests (`-m integration`) pass against the deployed stack.

## Notes
_(add during implementation)_
