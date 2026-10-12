# HiveMind — Central Infrastructure (CDK)

Deploys the AWS skeleton for the HiveMind central service.

## What gets created

| Resource | Details |
|---|---|
| Cognito User Pool | Password auth, auto-confirm via pre-signup Lambda, no email verification |
| API Gateway HTTP API | JWT authorizer (access token), `/hello` (auth required), `/health` (open) |
| RDS Postgres | db.t3.micro, private subnet, credentials in Secrets Manager |
| S3 transit bucket | Private, 1-day lifecycle backstop, auto-deleted on stack destroy |
| SSM Parameters | All config values under `/hivemind/*` |

## Prerequisites

- Node.js (for CDK CLI): `npm install -g aws-cdk`
- Python 3.11+
- AWS credentials configured: `aws configure`

## First deploy

```powershell
cd infra
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cdk bootstrap   # once per account/region
cdk deploy
```

`cdk deploy` prints the HTTP API URL, User Pool ID, and App Client ID — copy these into the agent config.

## Teardown

```powershell
cdk destroy
```

Destroys all resources including the database and S3 bucket.

## Notes

- The JWT authorizer uses the **access token** (not the ID token). The agent must pass the access token in `Authorization: Bearer`.
- Bedrock invocation logging must be confirmed off in the AWS Console before use.
- Record the account ID and region in CLAUDE.md after first deploy.
