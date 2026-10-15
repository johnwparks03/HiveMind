"""Relay WebSocket (Interface C): $connect, $disconnect and ping. One Lambda, dispatches on
routeKey. The caller's identity is the `user_id` the authorizer put in its context, never
anything the client sends. Users with no team may connect."""
import json

from common import db


def _user_id(event):
    return event["requestContext"]["authorizer"]["user_id"]


def on_connect(cur, event):
    # Upsert: API Gateway can deliver $connect twice for the same connection_id.
    cur.execute(
        "INSERT INTO connections (connection_id, user_id) VALUES (%s, %s) "
        "ON CONFLICT (connection_id) DO UPDATE SET user_id = EXCLUDED.user_id, connected_at = now()",
        (event["requestContext"]["connectionId"], _user_id(event)),
    )


def on_disconnect(cur, event):
    # Idempotent: a missing row (already purged or never stored) is fine.
    cur.execute("DELETE FROM connections WHERE connection_id = %s",
                (event["requestContext"]["connectionId"],))


def handler(event, context):
    route = event.get("requestContext", {}).get("routeKey")
    if route == "ping":
        # Sent back to the client as the route response; no database needed.
        return {"statusCode": 200, "body": json.dumps({"action": "pong"})}
    action = {"$connect": on_connect, "$disconnect": on_disconnect}.get(route)
    if action is None:
        return {"statusCode": 404}
    try:
        with db.transaction() as cur:
            action(cur, event)
    except Exception as exc:  # noqa: BLE001
        print(f"relay handler error: {type(exc).__name__}")  # never log events or values
        return {"statusCode": 500}
    return {"statusCode": 200}
