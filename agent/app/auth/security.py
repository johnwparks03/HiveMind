import secrets

# Random per-restart token (Feature_List 1.11 / API_Contract 2.1). GET /auth/token
# is the only endpoint that doesn't require it.
STARTUP_TOKEN = secrets.token_urlsafe(32)


def token_matches(candidate: str | None) -> bool:
    if not candidate:
        return False
    return secrets.compare_digest(candidate.encode(), STARTUP_TOKEN.encode())
