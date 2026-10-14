# E3-S3: Bedrock proxy: tag generation

- **Epic:** E3 Publish and central search
- **Track:** Central service
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** E2-S6
- **Spec refs:** Feature_List 3.4; `POST /llm/tags`

## Story
As an agent, I want tags suggested from an excerpt so that published files are discoverable.

## Acceptance criteria
- [x] Given an excerpt up to 3,000 characters, when `/llm/tags` is called, then tags are returned.
- [x] Oversized excerpts return 400 `invalid_request`.

## Technical notes
- `POST /llm/tags` request `{filename, excerpt}` -> `{tags:[...]}`: 5 to 8 lowercase keyword strings.
- Truncate the excerpt server-side to `EXCERPT_MAX_CHARS` (3,000). Validate count (5-8), length per tag, plain strings; invalid output or Bedrock error -> `503 service_unavailable`.
- Never store or log the excerpt.

## Notes
- **Status:** done. `LlmFn` deployed to the dev stack with model ID `us.anthropic.claude-sonnet-5-5`; offline tests (108) pass, and live calls returned 8 valid lowercase tags for three realistic 1,500-1,800 character excerpts (proposal, meeting notes, design doc). The Postman folder "Test LLM Tags" (12 requests) was created for manual runs.
- **Shared helper (E2-S6 dependency):** E2-S6 (`/llm/query`) is not built, so this story builds `central/lambdas/common/bedrock.py` (`invoke_json`, `BedrockUnavailable`). E2-S6 only needs to add `"POST /llm/query"` to `ROUTES` in `central/lambdas/llm.py` plus its prompt and validation.
- **Code:** `central/lambdas/llm.py` (route `POST /llm/tags`, login required, no team, no DB); `LlmFn` and `LlmRole` in `infra/stack.py`.
- **Infra:** `LlmFn` is outside the VPC (the VPC subnets have no NAT so they cannot reach Bedrock, and this function needs no DB). Its own role has only `bedrock:InvokeModel` on `anthropic.*` foundation models and on inference profiles in this account and region, plus basic logging. Environment is limited to `BEDROCK_MODEL_ID` and `EXCERPT_MAX_CHARS`. Timeout 25 s. Bedrock client budget (found in code review): 3 s connect, 8 s read, one retry, so the worst case is 22 s and a slow Bedrock becomes a 503 from us instead of a killed Lambda. (botocore's `max_attempts` counts retries after the first try, so the earlier 20 s read with `max_attempts: 2` could run about 75 s.)
- **Oversized excerpts:** the AC says 400, the notes and contract say truncate. Resolved as: truncate to `EXCERPT_MAX_CHARS` (3,000), and return `400 invalid_request` (`details.fields: ["excerpt"]`) only above `10 x EXCERPT_MAX_CHARS` (`EXCERPT_HARD_LIMIT_FACTOR` in `llm.py`).
- **Tag validation:** tags are lowercased, trimmed and de-duplicated; each must match `^[a-z0-9][a-z0-9 -]{0,39}$`. Fewer than 5 valid tags, or a reply that is not a list of strings, returns `503 service_unavailable`. More than 8 are trimmed to the first 8 rather than failing.
- **Privacy:** prompt, excerpt, filename and model reply are never logged or stored; only exception class names are printed. No access-log event (the contract leaves `/llm/*` logging undecided). **Invocation logging:** `aws bedrock get-model-invocation-logging-configuration` returns no configuration, so it is off.
- **Prompt injection:** the system prompt marks the filename and excerpt as untrusted document text; output is validated, and tags only go back to the caller.
- **verify-in-AWS (done):** `aws bedrock-runtime converse` with the bare `anthropic.claude-sonnet-5-5` fails with an on-demand-throughput `ValidationException`. `BEDROCK_MODEL_ID` is now the US inference profile `us.anthropic.claude-sonnet-5-5` (also available: `global.anthropic.claude-sonnet-5-5`); a Converse call with it returned a reply. The IAM policy already covers inference profiles and `anthropic.*` foundation models in any region.
- **`temperature` is deprecated for Sonnet 5.5:** Converse returns a `ValidationException` if it is sent, so `invoke_json` sends only `maxTokens`. Output determinism is not guaranteed, which is why tags are validated and normalized.
- **Postman:** folder "Test LLM Tags" in the HiveMind collection calls central directly with a Cognito access token; two of its requests make real Bedrock calls.
