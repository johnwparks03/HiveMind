"""Server-to-agent messages over the relay WebSocket (Interface C). The VPC has no route to the
WebSocket management API (calls through an execute-api endpoint get ForbiddenException), so the
send goes through the non-VPC notify Lambda, reached over a Lambda interface endpoint."""
import json
import os

from . import db

_client = None


def _lambda():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        # No retries: a retried invoke could deliver the same upload_request twice.
        _client = boto3.client("lambda", config=Config(retries={"max_attempts": 1}, connect_timeout=5,
                                                       read_timeout=20))
    return _client


def connections_for(cur, user_id):
    """The user's connection ids, most recent first."""
    cur.execute("SELECT connection_id FROM connections WHERE user_id = %s "
                "ORDER BY connected_at DESC, connection_id", (user_id,))
    return [row[0] for row in cur.fetchall()]


def send_to_user(user_id, message):
    """Send `message` to the user's most recent live connection. Connections API Gateway no
    longer knows are deleted and the next is tried (inside the notify Lambda). Returns True if one
    accepted the message, False if the user has no live connection. Commits its own cleanup,
    so it must not be called inside the caller's transaction."""
    with db.transaction() as cur:
        connection_ids = connections_for(cur, user_id)
    if not connection_ids:
        return False
    response = _lambda().invoke(
        FunctionName=os.environ["NOTIFY_FUNCTION_NAME"], InvocationType="RequestResponse",
        Payload=json.dumps({"connection_ids": connection_ids, "message": message}).encode())
    if response.get("FunctionError"):
        raise RuntimeError("notify function failed")  # payload may echo values: never include it
    result = json.loads(response["Payload"].read())
    if result["gone"]:
        with db.transaction() as cur:
            cur.execute("DELETE FROM connections WHERE connection_id = ANY(%s)", (result["gone"],))
    return result["delivered"] is not None
