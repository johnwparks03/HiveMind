import json


class Unauthorized(Exception):
    """Raised when the request carries no verified caller identity."""


class ApiError(Exception):
    """Raised by handlers; `error_response_for` turns it into the contract envelope."""

    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


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
