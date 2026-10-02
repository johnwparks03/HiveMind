# E0-S1: Repo scaffolding

- **Epic:** E0 Foundations and risk spikes
- **Track:** All tracks
- **Estimate:** S
- **Priority:** MVP
- **Depends on:** none
- **Spec refs:** Technical_Blueprint (dev/infra)

## Story
As a developer, I want a scaffolded monorepo so that all three tracks can start work without conflicts.

## Acceptance criteria
- [ ] Given a fresh clone, when I follow the repo instructions, then `agent/`, `frontend/` and `infra/` exist and each starts with a single command.
- [ ] Docker Compose brings up local Postgres for development.
- [ ] Lint/format config and a basic CI workflow run on every pull request.
- [ ] Branching and PR conventions are written down in the repo.

## Technical notes
- Proposed layout: `agent/` (Python package, FastAPI app), `frontend/` (Vite + React), `infra/` (CDK app) and the central Lambda code (location chosen here; document it in CLAUDE.md).
- Pin Python version and dependency manager (pip + requirements or uv/poetry); record it.
- Docker Compose: Postgres only (central code is tested locally against it).
- Must update the **Commands** section of the root `CLAUDE.md` with run/test/lint/deploy commands. Do not leave it as 'not set up yet'.

## Notes
_(add during implementation)_
