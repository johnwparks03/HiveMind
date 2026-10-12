import json
import os


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "service": "hivemind-central",
            "status": "ok",
            "bucket": os.environ.get("TRANSIT_BUCKET", ""),
        }),
    }
