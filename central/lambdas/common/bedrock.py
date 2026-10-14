"""The only place Bedrock is called. The model ID comes from BEDROCK_MODEL_ID; the Lambda's
execution role supplies credentials. Never log prompts, excerpts, filenames or replies."""
import json
import os
import re

# Time budget: botocore's max_attempts counts retries after the first try, so the worst case is
# (CONNECT_TIMEOUT + READ_TIMEOUT) * (RETRIES + 1) = 22 s. That must stay below LlmFn's timeout
# (25 s, infra/stack.py) so a slow Bedrock becomes a 503 from us, not a killed Lambda.
CONNECT_TIMEOUT = 3
READ_TIMEOUT = 8
RETRIES = 1

_client = None
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class BedrockUnavailable(Exception):
    """Bedrock failed, timed out, or returned something that is not a JSON object."""


def _get_client():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        _client = boto3.client(
            "bedrock-runtime",
            config=Config(read_timeout=READ_TIMEOUT, connect_timeout=CONNECT_TIMEOUT,
                          retries={"max_attempts": RETRIES}),
        )
    return _client


def invoke_json(system_prompt, user_text, max_tokens=300):
    """Ask the model for a JSON object and return it parsed. Raises BedrockUnavailable
    on any service error or if the reply is not a JSON object."""
    try:
        response = _get_client().converse(
            modelId=os.environ["BEDROCK_MODEL_ID"],
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            inferenceConfig={"maxTokens": max_tokens},  # Sonnet 5.5 rejects `temperature`
        )
        text = response["output"]["message"]["content"][0]["text"].strip()
        fenced = _FENCE_RE.match(text)
        parsed = json.loads(fenced.group(1) if fenced else text)
    except Exception as exc:  # noqa: BLE001
        print(f"bedrock call failed: {type(exc).__name__}")  # class name only, never content
        raise BedrockUnavailable() from None
    if not isinstance(parsed, dict):
        print("bedrock call failed: reply was not a JSON object")
        raise BedrockUnavailable()
    return parsed
