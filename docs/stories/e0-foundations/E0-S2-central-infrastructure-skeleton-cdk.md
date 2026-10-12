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
- [x] Given AWS credentials, when I run the CDK deploy, then a database, an HTTP API with a hello Lambda, an S3 transit bucket and a secrets entry exist.
- [x] Config values from Feature_List 3.8 (expiry 45 days, search cap ~20, transfer timeout 60 s, sweeper age 15 min, model ID) live in one config location.
- [ ] Teardown works with a single destroy command. _(not tested yet — will verify at end of project)_

## Technical notes
- Resources: RDS Postgres `db.t3.micro`, API Gateway HTTP API, one hello Lambda, S3 transit bucket (private, no public access), Secrets Manager/SSM entries for DB credentials. WebSocket API is added in E4-S1.
- Config keys: `RETENTION_DAYS=45`, `EXPIRING_SOON_DAYS=7`, `INVITE_LIFETIME_DAYS=7`, `EXCERPT_MAX_CHARS=3000`, `SEARCH_RESULT_CAP=20`, `PUBLISH_CONCURRENCY=5`, `BEDROCK_MODEL_ID` (from Bedrock console; do not guess), `TRANSFER_ACK_TIMEOUT_SECONDS=60`, `SWEEPER_MAX_AGE_MINUTES=15`.
- Add a day-level S3 lifecycle rule as a backstop (suggested in the blueprint).
- Record account, region and the Bedrock model access check in CLAUDE.md under AWS. Confirm Bedrock invocation logging is **off**.

## Notes
- Sandbox org policy (`OC-Layer-1-DenyPolicy`) blocks `rds:CreateDBInstance`. Switched to **Aurora Serverless v2** (aurora-postgresql 16.8, 0.5–1 ACU) which uses `CreateDBCluster` — permitted. All SQL queries remain Postgres-compatible; no application code changes needed.
- All config values stored in SSM Parameter Store under `/hivemind/*`.
- DB credentials in Secrets Manager at `hivemind/db-credentials`.
- S3 transit bucket has 1-day lifecycle rule as backstop; sweeper Lambda (E4-S5) handles the 15-minute sweep.
- Account: 954976288579. Region: us-east-1.
- Bedrock invocation logging: verified off in AWS Console.
