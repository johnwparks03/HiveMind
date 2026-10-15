"""Sends one message to an agent's WebSocket connection (Interface C). Runs OUTSIDE the VPC:
calls to the WebSocket management API from inside the VPC through an execute-api interface
endpoint were refused (ForbiddenException), while the same call from a non-VPC Lambda works.
Holds no DB access: the transfers Lambda passes the connection ids and cleans up the dead ones.

Event: {"connection_ids": [newest first], "message": {...}}
Returns: {"delivered": <connection_id or None>, "gone": [connection ids API Gateway dropped]}
"""
import json
import os

_client = None


def _management_api():
    global _client
    if _client is None:
        import boto3

        _client = boto3.client("apigatewaymanagementapi", endpoint_url=os.environ["WS_MANAGEMENT_URL"])
    return _client


def handler(event, context):
    client = _management_api()
    data = json.dumps(event["message"]).encode()
    gone = []
    for connection_id in event["connection_ids"]:
        try:
            client.post_to_connection(ConnectionId=connection_id, Data=data)
            return {"delivered": connection_id, "gone": gone}
        except client.exceptions.GoneException:
            gone.append(connection_id)
    return {"delivered": None, "gone": gone}
