# E0-S2: Central infrastructure skeleton (CDK)

- **Epic:** E0 Foundations and risk spikes
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E0-S1
- **Spec refs:** Feature_List 3.8; Blueprint (AWS)
- **Flags:** verify-in-AWS

## Story
As a developer, I want the AWS skeleton deployed from code so that central stories have somewhere to land.

## Acceptance criteria
- [ ] Given AWS credentials, when I run the CDK deploy, then an RDS Postgres (db.t3.micro), an HTTP API with a hello Lambda, an S3 transit bucket and a secrets entry exist.
- [ ] Config values from Feature_List 3.8 (expiry 45 days, search cap ~20, transfer timeout 60 s, sweeper age 15 min, model ID) live in one config location.
- [ ] Teardown works with a single destroy command.

## Technical notes
- Resources: RDS Postgres `db.t3.micro`, API Gateway HTTP API, one hello Lambda, S3 transit bucket (private, no public access), Secrets Manager/SSM entries for DB credentials. WebSocket API is added in E4-S1.
- Config keys: `RETENTION_DAYS=45`, `EXPIRING_SOON_DAYS=7`, `INVITE_LIFETIME_DAYS=7`, `EXCERPT_MAX_CHARS=3000`, `SEARCH_RESULT_CAP=20`, `PUBLISH_CONCURRENCY=5`, `BEDROCK_MODEL_ID` (from Bedrock console; do not guess), `TRANSFER_ACK_TIMEOUT_SECONDS=60`, `SWEEPER_MAX_AGE_MINUTES=15`.
- Add a day-level S3 lifecycle rule as a backstop (suggested in the blueprint).
- Record account, region and the Bedrock model access check in CLAUDE.md under AWS. Confirm Bedrock invocation logging is **off**.

## Notes
_(add during implementation)_
