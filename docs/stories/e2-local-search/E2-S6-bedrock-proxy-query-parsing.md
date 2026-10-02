# E2-S6: Bedrock proxy: query parsing

- **Epic:** E2 Local indexing and search
- **Track:** Central service
- **Estimate:** M
- **Priority:** MVP
- **Depends on:** E1-S1
- **Spec refs:** Feature_List 3.4; Interface B `POST /llm/query`
- **Flags:** verify-in-AWS

## Story
As an agent, I want a natural-language query turned into topic plus date range so that I can filter by date first.

## Acceptance criteria
- [ ] Given a query and the client's local date and timezone, when `/llm/query` is called, then it returns topic and date range (format per E0-S7).
- [ ] Only the central service calls Bedrock; model ID comes from config.
- [ ] Bedrock failure returns 503 `service_unavailable`.

## Technical notes
- Interface B `POST /llm/query` request `{query, local_date, timezone}`; response `{topic, date_from, date_to}` (all nullable). Example: 'meeting notes from 3 days ago' on 2026-10-02 America/New_York gives topic 'meeting notes', 2026-09-29 00:00:00-04:00 to 23:59:59-04:00.
- Prompt Claude (Bedrock Converse/InvokeModel API) for JSON only. Validate: JSON parses, dates parse, `date_from` <= `date_to`. Topic is a few plain keywords. Any invalid output or Bedrock error -> `503 service_unavailable`.
- Requires login but not a team. Do not store or log the query or response bodies. Use the date-range format decided in E0-S7.

## Notes
_(add during implementation)_
