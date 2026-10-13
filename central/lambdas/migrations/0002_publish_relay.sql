-- E3-S1: published-file metadata, relay connections and transfers.
-- access_log (0001) keeps its ids-only shape; teams/memberships/invites are in 0001.

-- array_to_string is only STABLE, which a generated column rejects; this wrapper is
-- safe to mark IMMUTABLE because tags are plain text.
CREATE FUNCTION hm_tags_text(tags text[]) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $$ SELECT coalesce(array_to_string(tags, ' '), '') $$;

CREATE TABLE public_files (
    file_id           text PRIMARY KEY,
    owner_id          text NOT NULL,
    team_id           uuid NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    filename          text NOT NULL,
    tags              text[] NOT NULL DEFAULT '{}',
    file_created_at   timestamptz,
    file_modified_at  timestamptz,
    published_at      timestamptz NOT NULL DEFAULT now(),
    expires_at        timestamptz NOT NULL,
    last_confirmed    timestamptz,
    -- Underscores, dots and hyphens in the filename become spaces so "Q3_Client-Contracts.v2.docx"
    -- tokenizes into words.
    search_vector     tsvector GENERATED ALWAYS AS (
        to_tsvector('english',
                    regexp_replace(filename, '[-_.]+', ' ', 'g') || ' ' || hm_tags_text(tags))
    ) STORED
);
CREATE INDEX idx_public_files_search ON public_files USING GIN (search_vector);
CREATE INDEX idx_public_files_team_expiry ON public_files (team_id, expires_at);
CREATE INDEX idx_public_files_owner ON public_files (owner_id);

CREATE TABLE connections (
    connection_id  text PRIMARY KEY,
    user_id        text NOT NULL,
    connected_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_connections_user ON connections (user_id);

-- No FK to public_files: a purge mid-transfer must not delete the transfer row.
CREATE TABLE transfers (
    transfer_id   uuid PRIMARY KEY,
    file_id       text NOT NULL,
    requester_id  text NOT NULL,
    owner_id      text NOT NULL,
    status        text NOT NULL CHECK (status IN ('requested', 'uploading', 'ready', 'failed', 'expired')),
    s3_key        text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_transfers_requester ON transfers (requester_id, created_at);
CREATE INDEX idx_transfers_status_age ON transfers (status, updated_at);
