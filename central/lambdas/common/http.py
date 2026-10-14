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


def invalid_request(*fields):
    """400 invalid_request naming the bad fields only, never their values."""
    return ApiError(400, "invalid_request", "invalid request", {"fields": list(fields)})


def optional_timestamp(body, field):
    """A nullable ISO 8601 timestamp that must carry a timezone; raises on anything else."""
    value = body.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise invalid_request(field)
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError:
        raise invalid_request(field) from None
    if parsed.tzinfo is None:
        raise invalid_request(field)
    return parsed


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
