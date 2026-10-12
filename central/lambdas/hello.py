import json
import os

from common.auth import get_caller_sub
from common.errors import Unauthorized, unauthorized_response


def handler(event, context):
    try:
        sub = get_caller_sub(event)
    except Unauthorized:
        return unauthorized_response()
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "service": "hivemind-central",
            "status": "ok",
            "sub": sub,
            "bucket": os.environ.get("TRANSIT_BUCKET", ""),
        }),
    }
