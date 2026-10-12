from .errors import Unauthorized


def get_caller_sub(event):
    """Return the Cognito `sub` from the claims the API Gateway JWT authorizer verified.

    Raises Unauthorized if the claims are absent, so a route accidentally wired
    without an authorizer fails closed instead of running anonymously.
    """
    try:
        sub = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except (KeyError, TypeError):
        raise Unauthorized() from None
    if not sub:
        raise Unauthorized()
    return sub
