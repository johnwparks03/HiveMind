"""Lists the files a user has published centrally, with each file's chunk_count (GET /files/mine).

Used by the end-to-end checklist (README.md) to see that chunks reached central, without touching
the Postman collection's variables. Standard library only.

Setup: copy docs/e2e/.env.example to docs/e2e/.env (gitignored) and fill in the email and password of
the person whose published files you want to list. Then:

    python docs/e2e/mine.py                  # reads docs/e2e/.env
    python docs/e2e/mine.py path/to/other.env   # or another env file, e.g. for the second person

The Cognito client id and the central API URL are taken from agent/.env when they are not in your
e2e .env, since the agent already needs the same two values. Variables set in the shell win over any
file. Prints file names and counts only. It never prints the password or any token.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REGION = os.environ.get("AWS_REGION", "us-east-1")
HERE = Path(__file__).resolve().parent
DEFAULT_ENV = HERE / ".env"
AGENT_ENV = HERE.parent.parent / "agent" / ".env"

# The names the agent already uses, plus the shorter ones this script used before it read a file.
CLIENT_ID_NAMES = ("HIVEMIND_COGNITO_CLIENT_ID", "HIVEMIND_CLIENT_ID")
API_URL_NAMES = ("HIVEMIND_CENTRAL_API_URL", "HIVEMIND_API_URL")


def load_env_file(path):
    """KEY=VALUE lines. Blank lines and # comments are skipped, `export ` is allowed, and a value wrapped
    in matching quotes is unwrapped. No inline comments: a password may contain a #. A missing file is
    just empty."""
    values = {}
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def first(values, names):
    for name in names:
        if values.get(name):
            return values[name]
    return None


def settings(env_path=DEFAULT_ENV, agent_env_path=AGENT_ENV, environ=None):
    """Sign-in details and connection settings. Precedence: the shell, then the e2e .env, then agent/.env
    (which only supplies the client id and API URL)."""
    environ = os.environ if environ is None else environ
    agent = load_env_file(agent_env_path)
    mine = load_env_file(env_path)
    merged = {**agent, **mine, **{k: v for k, v in environ.items() if k.startswith("HIVEMIND_")}}
    return {
        "client_id": first(merged, CLIENT_ID_NAMES),
        "api_url": first(merged, API_URL_NAMES),
        "email": merged.get("HIVEMIND_EMAIL"),
        "password": merged.get("HIVEMIND_PASSWORD"),
    }


def require(config, env_path):
    labels = {
        "client_id": "HIVEMIND_COGNITO_CLIENT_ID (or set it in agent/.env)",
        "api_url": "HIVEMIND_CENTRAL_API_URL (or set it in agent/.env)",
        "email": "HIVEMIND_EMAIL",
        "password": "HIVEMIND_PASSWORD",
    }
    missing = [labels[key] for key in labels if not config[key]]
    if missing:
        sys.exit(f"Missing: {', '.join(missing)}.\nPut them in {env_path} (copy docs/e2e/.env.example) "
                 "or set them in the shell.")


def login(client_id, email, password):
    body = json.dumps({
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": client_id,
        "AuthParameters": {"USERNAME": email, "PASSWORD": password},
    }).encode()
    request = urllib.request.Request(
        f"https://cognito-idp.{REGION}.amazonaws.com/", data=body, method="POST",
        headers={"Content-Type": "application/x-amz-json-1.1",
                 "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"})
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)["AuthenticationResult"]["AccessToken"]
    except urllib.error.HTTPError as exc:
        sys.exit(f"Sign-in failed ({exc.code}). Check the email, password and client id in your .env.")


def main():
    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ENV
    config = settings(env_path)
    require(config, env_path)
    token = login(config["client_id"], config["email"], config["password"])
    api_url = config["api_url"].rstrip("/")
    files, cursor = [], None
    while True:
        url = f"{api_url}/files/mine" + (f"?cursor={cursor}" if cursor else "")
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(request) as response:
            page = json.load(response)
        files.extend(page.get("files", []))
        cursor = page.get("next_cursor")
        if not cursor:
            break
    if not files:
        print("No published files.")
    for f in files:
        print(f"{f.get('chunk_count', '?'):>5} chunks  {f['file_id']}  {f['filename']}")


if __name__ == "__main__":
    main()
