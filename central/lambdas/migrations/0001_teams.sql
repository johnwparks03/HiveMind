-- E1-S4: teams, memberships, invites, and the minimal access log (E5-S3 adds tests/gaps).
CREATE TABLE teams (
    id          uuid PRIMARY KEY,
    name        text NOT NULL,
    created_by  text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- One team per user: user_id is UNIQUE.
CREATE TABLE memberships (
    user_id    text NOT NULL UNIQUE,
    team_id    uuid NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    joined_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_memberships_team ON memberships(team_id);

CREATE TABLE invites (
    code        text PRIMARY KEY,
    team_id     uuid NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    created_by  text NOT NULL,
    expires_at  timestamptz NOT NULL,
    use_count   integer NOT NULL DEFAULT 0,
    max_uses    integer
);
CREATE INDEX idx_invites_team ON invites(team_id);

-- Ids only: never request bodies, names, queries or file content.
CREATE TABLE access_log (
    id       bigserial PRIMARY KEY,
    ts       timestamptz NOT NULL DEFAULT now(),
    event    text NOT NULL,
    user_id  text NOT NULL,
    team_id  uuid,
    file_id  text
);
