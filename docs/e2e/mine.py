"""Lists the files a user has published centrally, with each file's chunk_count (GET /files/mine).

Used by the end-to-end checklist (README.md) to see that chunks reached central, without touching
the Postman collection's variables. Standard library only.

    set HIVEMIND_CLIENT_ID=<Cognito app client id>      (CDK output UserPoolClientId)
    set HIVEMIND_API_URL=<https://....execute-api.us-east-1.amazonaws.com>   (CDK output HttpApiUrl)
    set HIVEMIND_EMAIL=you@example.com
    set HIVEMIND_PASSWORD=...
    python docs/e2e/mine.py

Prints file names and counts only. It never prints the password or any token.
"""
import json
import os
import sys
import urllib.error
import urllib.request

REGION = os.environ.get("AWS_REGION", "us-east-1")


def need(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"Set {name} first (see the top of this file).")
    return value


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
        sys.exit(f"Sign-in failed ({exc.code}). Check HIVEMIND_EMAIL, HIVEMIND_PASSWORD and HIVEMIND_CLIENT_ID.")


def main():
    token = login(need("HIVEMIND_CLIENT_ID"), need("HIVEMIND_EMAIL"), need("HIVEMIND_PASSWORD"))
    api_url = need("HIVEMIND_API_URL").rstrip("/")
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
