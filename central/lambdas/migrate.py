"""Applies central/migrations/*.sql in order, once each. Runs inside the VPC because
the database is not reachable from outside. Invoked by a CDK custom resource on
deploy, or manually: aws lambda invoke --function-name <MigrateFn> out.json"""
import os

from common import db

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def pending(applied, available):
    """Versions in `available` (sorted filenames) not yet in `applied`."""
    return [name for name in sorted(available) if name not in set(applied)]


def handler(event, context):
    names = [n for n in os.listdir(MIGRATIONS_DIR) if n.endswith(".sql")]
    applied_now = []
    with db.transaction() as cur:
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
    return {"applied": applied_now}
