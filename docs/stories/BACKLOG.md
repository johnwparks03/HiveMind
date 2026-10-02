# HiveMind Backlog

3 developers, 3 weeks. Tracks: **Local agent**, **Central service** (AWS), **Frontend** (React).
Estimates: S ~0.5 day, M ~1-2 days, L ~3 days. Stories marked *stretch* are dropped first if the schedule slips.
Feature freeze: start of day 3, week 3.

## Build order

### E0: Foundations and risk spikes (Week 1 (days 1-3))

| Story | Title | Track | Size | Depends on |
|---|---|---|---|---|
| [E0-S1](e0-foundations/E0-S1-repo-scaffolding.md) | Repo scaffolding | All tracks | S | - |
| [E0-S2](e0-foundations/E0-S2-central-infrastructure-skeleton-cdk.md) | Central infrastructure skeleton (CDK) | Central service | M | E0-S1 |
| [E0-S3](e0-foundations/E0-S3-spike-cognito-auto-confirm-and-jwt-authorizer.md) | Spike: Cognito auto-confirm and JWT authorizer | Central service | M | E0-S2 |
| [E0-S4](e0-foundations/E0-S4-spike-native-windows-folder-dialog.md) | Spike: native Windows folder dialog | Local agent | S | E0-S1 |
| [E0-S5](e0-foundations/E0-S5-spike-relay-path-end-to-end.md) | Spike: relay path end to end | Local agent + Central service | L | E0-S2, E0-S3 |
| [E0-S6](e0-foundations/E0-S6-spike-keyring-refresh-token-storage.md) | Spike: keyring refresh-token storage | Local agent | S | E0-S1 |
| [E0-S7](e0-foundations/E0-S7-resolve-api-contract-open-items.md) | Resolve API contract open items | All tracks | S | - |

### E1: Auth and teams (Week 1)

| Story | Title | Track | Size | Depends on |
|---|---|---|---|---|
| [E1-S1](e1-auth-teams/E1-S1-cognito-sign-up-login-and-jwt-authorizer.md) | Cognito sign-up, login and JWT authorizer | Central service | M | E0-S3 |
| [E1-S2](e1-auth-teams/E1-S2-agent-local-api-shell.md) | Agent local API shell | Local agent | M | E0-S1 |
| [E1-S3](e1-auth-teams/E1-S3-agent-auth-proxy-and-session.md) | Agent auth proxy and session | Local agent | M | E1-S1, E1-S2, E0-S6 |
| [E1-S4](e1-auth-teams/E1-S4-teams-api.md) | Teams API | Central service | M | E1-S1 |
| [E1-S5](e1-auth-teams/E1-S5-agent-team-endpoints.md) | Agent team endpoints | Local agent | S | E1-S3, E1-S4 |
| [E1-S6](e1-auth-teams/E1-S6-login-page-and-status-indicator.md) | Login page and status indicator | Frontend | M | E1-S2, E1-S3 |

### E2: Local indexing and search (Weeks 1-2)

| Story | Title | Track | Size | Depends on |
|---|---|---|---|---|
| [E2-S1](e2-local-search/E2-S1-sqlite-registry-and-source-interface.md) | SQLite registry and Source interface | Local agent | M | E1-S2 |
| [E2-S2](e2-local-search/E2-S2-folder-management-and-initial-scan.md) | Folder management and initial scan | Local agent | M | E2-S1, E0-S4 |
| [E2-S3](e2-local-search/E2-S3-text-extraction-and-dates.md) | Text extraction and dates | Local agent | M | E2-S1 |
| [E2-S4](e2-local-search/E2-S4-chunking-embeddings-and-chroma.md) | Chunking, embeddings and Chroma | Local agent | L | E2-S3 |
| [E2-S5](e2-local-search/E2-S5-change-detection.md) | Change detection | Local agent | M | E2-S2, E2-S4 |
| [E2-S6](e2-local-search/E2-S6-bedrock-proxy-query-parsing.md) | Bedrock proxy: query parsing | Central service | M | E1-S1 |
| [E2-S7](e2-local-search/E2-S7-local-search-and-open-file.md) | Local search and open file | Local agent | M | E2-S4, E2-S6 |
| [E2-S8](e2-local-search/E2-S8-search-and-files-pages-local.md) | Search and Files pages (local) | Frontend | L | E1-S6, E2-S2, E2-S7 |

### E3: Publish and central search (Week 2)

| Story | Title | Track | Size | Depends on |
|---|---|---|---|---|
| [E3-S1](e3-publish-search/E3-S1-postgres-schema-and-migrations.md) | Postgres schema and migrations | Central service | M | E0-S2, E1-S4 |
| [E3-S2](e3-publish-search/E3-S2-metadata-api.md) | Metadata API | Central service | M | E3-S1, E1-S4 |
| [E3-S3](e3-publish-search/E3-S3-bedrock-proxy-tag-generation.md) | Bedrock proxy: tag generation | Central service | S | E2-S6 |
| [E3-S4](e3-publish-search/E3-S4-tag-generation-pipeline.md) | Tag generation pipeline | Local agent | M | E3-S3, E2-S4 |
| [E3-S5](e3-publish-search/E3-S5-publish-queue-worker.md) | Publish queue worker | Local agent | L | E3-S2, E3-S4 |
| [E3-S6](e3-publish-search/E3-S6-folder-share-and-unshare.md) | Folder share and unshare | Local agent | M | E3-S5 |
| [E3-S7](e3-publish-search/E3-S7-central-search.md) | Central search | Central service | M | E3-S2 |
| [E3-S8](e3-publish-search/E3-S8-merged-results-and-fallback.md) | Merged results and fallback | Local agent | M | E3-S7, E2-S7 |
| [E3-S9](e3-publish-search/E3-S9-publish-and-teammate-ui.md) | Publish and teammate UI | Frontend | L | E3-S5, E3-S6, E3-S8 |

### E4: Relay and download (Weeks 2-3)

| Story | Title | Track | Size | Depends on |
|---|---|---|---|---|
| [E4-S1](e4-relay/E4-S1-websocket-api-and-connections.md) | WebSocket API and connections | Central service | M | E3-S1, E0-S5 |
| [E4-S2](e4-relay/E4-S2-transfer-api.md) | Transfer API | Central service | L | E4-S1, E3-S2 |
| [E4-S3](e4-relay/E4-S3-relay-client-owner-side.md) | Relay client: owner side | Local agent | L | E4-S1, E0-S5 |
| [E4-S4](e4-relay/E4-S4-requester-side-download.md) | Requester side download | Local agent | M | E4-S2 |
| [E4-S5](e4-relay/E4-S5-sweeper-lambda.md) | Sweeper Lambda | Central service | S | E4-S2 |
| [E4-S6](e4-relay/E4-S6-download-ui.md) | Download UI | Frontend | M | E4-S4, E3-S9 |

### E5: Retention and hardening (Week 3)

| Story | Title | Track | Size | Depends on |
|---|---|---|---|---|
| [E5-S1](e5-hardening/E5-S1-nightly-purge-and-45-day-retention-stretch.md) | Nightly purge and 45-day retention (stretch) | Central service | S | E3-S2 |
| [E5-S2](e5-hardening/E5-S2-expiry-tracking-and-re-confirm-stretch.md) | Expiry tracking and re-confirm (stretch) | Local agent + Frontend | M | E5-S1 |
| [E5-S3](e5-hardening/E5-S3-access-log.md) | Access log | Central service | S | E3-S7, E4-S2 |
| [E5-S4](e5-hardening/E5-S4-leave-team-and-remove-folder-cascades-stretch.md) | Leave-team and remove-folder cascades (stretch) | Local agent + Central service | M | E3-S5, E1-S4 |
| [E5-S5](e5-hardening/E5-S5-integration-tests-and-demo-script.md) | Integration tests and demo script | All tracks | L | E4-S6 |
| [E5-S6](e5-hardening/E5-S6-verify-in-aws-checklist.md) | Verify-in-AWS checklist | Central service | M | E4-S5 |
| [E5-S7](e5-hardening/E5-S7-setup-and-run-instructions.md) | Setup and run instructions | All tracks | S | - |

## Critical path

E0-S3 -> E1-S1 -> E1-S4 -> E3-S2 -> E3-S5 -> E3-S7 -> E4-S2 -> E4-S4 -> E4-S6 -> E5-S5

## Deferred (out of scope for 3 weeks)

Multiple teams, SSO/MFA, Teams/SharePoint sources, WebRTC/TURN, usage limits, desktop wrapper.

## Feature_List coverage

| Feature_List section | Stories |
|---|---|
| 1.1 Sources and folders | E2-S1, E2-S2, E0-S4 |
| 1.2 Change detection | E2-S5 |
| 1.3 Extraction and dates | E2-S3 |
| 1.4 Indexing | E2-S4 |
| 1.5 Search | E2-S6, E2-S7, E3-S8 |
| 1.6 Publish/unpublish | E3-S4, E3-S5, E3-S6, E5-S4 |
| 1.7 Expiry | E5-S2 |
| 1.8 Relay client | E4-S3, E4-S4 |
| 1.9 Auth | E1-S3, E0-S6 |
| 1.10 Team endpoints | E1-S5 |
| 1.11 Local API | E1-S2 |
| 1.12 SQLite registry | E2-S1 |
| 2.1 Login page | E1-S6 |
| 2.2 Search page | E2-S8, E3-S9, E4-S6 |
| 2.3 Files and folders page | E2-S8, E3-S9, E5-S2 |
| 2.4 Status indicator | E1-S6 |
| 2.5 Technical notes (polling) | E2-S8 |
| 3.1 Auth and teams | E1-S1, E1-S4, E4-S1 |
| 3.2 Metadata API | E3-S1, E3-S2 |
| 3.3 Search endpoint | E3-S7 |
| 3.4 Bedrock proxy | E2-S6, E3-S3 |
| 3.5 Relay | E4-S1, E4-S2 |
| 3.6 Scheduled jobs | E4-S5, E5-S1 |
| 3.7 Access log | E5-S3 |
| 3.8 Infrastructure/config | E0-S2, E5-S6 |
