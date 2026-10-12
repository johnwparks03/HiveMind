def handler(event, context):
    # Auto-confirm every new user so no email verification is required (demo only).
    event["response"]["autoConfirmUser"] = True
    event["response"]["autoVerifyEmail"] = True
    return event
