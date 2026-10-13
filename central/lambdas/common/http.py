"""Request/response helpers shared by the Interface B Lambdas."""
import datetime
import json

from .errors import ApiError


def parse_body(event):
    raw = event.get("body")
    if not raw:
        return {}
    try:
        body = json.loads(raw)
    except ValueError:
        raise ApiError(400, "invalid_request", "body must be valid JSON") from None
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_request", "body must be a JSON object")
    return body


def json_response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}


def iso(dt):
    """ISO 8601 in UTC with a trailing Z, as in the contract examples; None stays None."""
    if dt is None:
        return None
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def get_membership(cur, user_id):
    """(team_id, team_name) for the caller's team, or None."""
    cur.execute("SELECT t.id, t.name FROM memberships m JOIN teams t ON t.id = m.team_id "
                "WHERE m.user_id = %s", (user_id,))
    return cur.fetchone()
