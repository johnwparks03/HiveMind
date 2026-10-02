# E5-S6: Verify-in-AWS checklist

- **Epic:** E5 Retention and hardening
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E4-S5
- **Spec refs:** Technical_Blueprint section 11
- **Flags:** verify-in-AWS

## Story
As a team, we want the unverified AWS assumptions confirmed or fixed.

## Acceptance criteria
- [ ] Each blueprint section 11 item is marked verified, or has a fix or documented workaround.
- [ ] Includes Cognito client config, WebSocket authorizer, Bedrock model ID and logging, S3 lifecycle granularity, WebSocket idle timeout and throttling.

## Technical notes
- Checklist (Blueprint section 11): Cognito client with password flow and no secret; pre sign-up trigger; WebSocket authorizer and token passing; Bedrock model ID and access; Bedrock invocation logging off; S3 lifecycle granularity; WebSocket idle timeout; API Gateway/Lambda throttling vs publish concurrency.
- Record each result in this story's Notes and update CLAUDE.md AWS section.

## Notes
_(add during implementation)_
