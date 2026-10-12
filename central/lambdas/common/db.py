"""Postgres access for Lambdas. Credentials come from Secrets Manager (cached per
container); the connection is reused across warm invocations."""
import json
import os
from contextlib import contextmanager

_credentials = None
_conn = None


def _load_credentials():
    global _credentials
    if _credentials is None:
        import boto3

        secret = boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])
        _credentials = json.loads(secret["SecretString"])
    return _credentials


def _connect():
    import psycopg2

    creds = _load_credentials()
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "hivemind"),
        user=creds["username"],
        password=creds["password"],
        connect_timeout=5,
    )


def get_connection():
    global _conn
    if _conn is None or _conn.closed:
        _conn = _connect()
    return _conn


@contextmanager
def transaction():
    """Yields a cursor; commits on success, rolls back on any exception."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
