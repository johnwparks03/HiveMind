import json


def handler(event, context):
    # Open route: no auth, no identity, no config exposed.
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"service": "hivemind-central", "status": "ok"}),
    }
