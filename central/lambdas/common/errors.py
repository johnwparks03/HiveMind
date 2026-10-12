import json


class Unauthorized(Exception):
    """Raised when the request carries no verified caller identity."""


def error_response(status, code, message, details=None):
    """Build an API Gateway proxy response using the contract error envelope."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        }),
    }


def unauthorized_response():
    return error_response(401, "unauthorized", "Missing or invalid token")
