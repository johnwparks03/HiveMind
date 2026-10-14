"""Applies central/migrations/*.sql in order, once each. Runs inside the VPC because
the database is not reachable from outside. Invoked by a CDK custom resource on
deploy, or manually: aws lambda invoke --function-name <MigrateFn> out.json
From a CLI/CI against any Postgres: python migrate.py --dsn postgresql://user:pw@host/db
(or set HIVEMIND_DATABASE_URL)."""
import os

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def pending(applied, available):
    """Versions in `available` (sorted filenames) not yet in `applied`."""
    return [name for name in sorted(available) if name not in set(applied)]


def apply_migrations(cur):
    """Runs inside the caller's transaction; returns the names applied this call."""
    names = [n for n in os.listdir(MIGRATIONS_DIR) if n.endswith(".sql")]
    applied_now = []
    # Serialize concurrent deploys.
    cur.execute("SELECT pg_advisory_xact_lock(727274)")
    cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
    cur.execute("SELECT version FROM schema_migrations")
    applied = [row[0] for row in cur.fetchall()]
    for name in pending(applied, names):
        with open(os.path.join(MIGRATIONS_DIR, name), encoding="utf-8") as f:
            cur.execute(f.read())
        cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (name,))
        applied_now.append(name)
    return applied_now


def handler(event, context):
    from common import db

    with db.transaction() as cur:
        return {"applied": apply_migrations(cur)}


if __name__ == "__main__":
    import argparse

    import psycopg2

    parser = argparse.ArgumentParser(description="Apply HiveMind SQL migrations")
    parser.add_argument("--dsn", default=os.environ.get("HIVEMIND_DATABASE_URL"))
    args = parser.parse_args()
    if not args.dsn:
        parser.error("pass --dsn or set HIVEMIND_DATABASE_URL")
    conn = psycopg2.connect(args.dsn)
    try:
        with conn, conn.cursor() as cur:
            print({"applied": apply_migrations(cur)})
    finally:
        conn.close()
