import os
import re
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))

import migrate  # noqa: E402

MIGRATION_FILES = sorted(n for n in os.listdir(migrate.MIGRATIONS_DIR) if n.endswith(".sql"))


def _sql(name):
    with open(os.path.join(migrate.MIGRATIONS_DIR, name), encoding="utf-8") as f:
        return f.read()


def test_migration_files_are_numbered_in_order():
    numbers = [int(re.match(r"(\d{4})_", n).group(1)) for n in MIGRATION_FILES]
    assert numbers == list(range(1, len(numbers) + 1))


def test_0002_defines_publish_and_relay_tables():
    sql = _sql("0002_publish_relay.sql")
    for table in ("public_files", "connections", "transfers"):
        assert f"CREATE TABLE {table} " in sql
    assert "GENERATED ALWAYS AS" in sql and "tsvector" in sql
    assert re.search(r"CREATE INDEX \w+ ON public_files USING GIN \(search_vector\)", sql)
    for status in ("requested", "uploading", "ready", "failed", "expired"):
        assert f"'{status}'" in sql


def test_all_acceptance_tables_exist_across_migrations():
    sql = "\n".join(_sql(n) for n in MIGRATION_FILES)
    for table in ("teams", "memberships", "invites", "public_files", "connections",
                  "transfers", "access_log"):
        assert f"CREATE TABLE {table} " in sql


DSN = os.environ.get("HIVEMIND_TEST_DATABASE_URL")


@pytest.fixture
def fresh_db():
    import psycopg2

    conn = psycopg2.connect(DSN)
    schema = "mig_" + uuid.uuid4().hex[:10]
    with conn, conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {schema}")
    conn.close()
    conn = psycopg2.connect(DSN, options=f"-c search_path={schema}")
    yield conn
    conn.close()
    cleanup = psycopg2.connect(DSN)
    with cleanup, cleanup.cursor() as cur:
        cur.execute(f"DROP SCHEMA {schema} CASCADE")
    cleanup.close()


@pytest.mark.skipif(not DSN, reason="set HIVEMIND_TEST_DATABASE_URL to run against a real Postgres")
def test_migrations_apply_to_a_fresh_database_and_are_idempotent(fresh_db):
    with fresh_db, fresh_db.cursor() as cur:
        assert migrate.apply_migrations(cur) == MIGRATION_FILES
    with fresh_db, fresh_db.cursor() as cur:
        assert migrate.apply_migrations(cur) == []


@pytest.mark.skipif(not DSN, reason="set HIVEMIND_TEST_DATABASE_URL to run against a real Postgres")
def test_filename_and_tags_are_searchable_and_status_is_constrained(fresh_db):
    import psycopg2

    team_id = str(uuid.uuid4())
    with fresh_db, fresh_db.cursor() as cur:
        migrate.apply_migrations(cur)
        cur.execute("INSERT INTO teams (id, name, created_by) VALUES (%s, 'T', 'u1')", (team_id,))
        cur.execute(
            "INSERT INTO public_files (file_id, owner_id, team_id, filename, tags, expires_at) "
            "VALUES ('f1', 'u1', %s, 'Q3_Client-Contracts.v2.docx', ARRAY['renewal','pricing'], "
            "now() + interval '45 days')", (team_id,))
        for query in ("contracts", "client", "renewal"):
            cur.execute("SELECT file_id FROM public_files "
                        "WHERE search_vector @@ websearch_to_tsquery('english', %s)", (query,))
            assert cur.fetchall() == [("f1",)], query
        cur.execute("SELECT file_id FROM public_files "
                    "WHERE search_vector @@ websearch_to_tsquery('english', 'spreadsheet')")
        assert cur.fetchall() == []
    with pytest.raises(psycopg2.errors.CheckViolation):
        with fresh_db, fresh_db.cursor() as cur:
            cur.execute("INSERT INTO transfers (transfer_id, file_id, requester_id, owner_id, status) "
                        "VALUES (%s, 'f1', 'u2', 'u1', 'bogus')", (str(uuid.uuid4()),))


def test_0003_adds_transfer_api_columns_and_the_in_flight_index():
    sql = _sql("0003_transfers_api.sql")
    assert "ALTER TABLE transfers ADD COLUMN error_code text, ADD COLUMN size_bytes bigint" in sql
    assert re.search(r"CREATE UNIQUE INDEX uq_transfers_in_flight ON transfers \(file_id, requester_id\)\s+"
                     r"WHERE status IN \('requested', 'uploading', 'ready'\)", sql)
    assert "ALTER TABLE access_log ADD COLUMN transfer_id uuid, ADD COLUMN outcome text" in sql


def test_0004_adds_swept_at_and_the_sweeper_index():
    sql = _sql("0004_transfer_sweeper.sql")
    assert "ALTER TABLE transfers ADD COLUMN swept_at timestamptz" in sql
    assert re.search(r"CREATE INDEX idx_transfers_unswept ON transfers \(created_at\)\s+WHERE swept_at IS NULL", sql)


def test_0005_adds_the_membership_email_column():
    assert "ALTER TABLE memberships ADD COLUMN email text" in _sql("0005_membership_email.sql")


def test_in_flight_statuses_are_defined_once_and_match_the_index_predicate():
    from common.transfer_state import IN_FLIGHT

    predicate = re.search(r"WHERE status IN (\([^)]*\))", _sql("0003_transfers_api.sql")).group(1)
    assert predicate == IN_FLIGHT
