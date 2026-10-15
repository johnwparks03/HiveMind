"""Local Bedrock client (decided 2026-10-15, demo/MVP only — see CLAUDE.md). Modeled
directly on central/lambdas/common/bedrock.py's converse() shape, but called straight
from the agent process instead of a central Lambda. Never log prompts, excerpts or
replies.
"""
import json
import os
import re

from app.config import (
    BEDROCK_CONNECT_TIMEOUT_SECONDS,
    BEDROCK_MODEL_ID,
    BEDROCK_READ_TIMEOUT_SECONDS,
    BEDROCK_RETRIES,
)
from app.errors import ApiError

_client = None
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class BedrockUnavailable(Exception):
    """Bedrock failed, timed out, or (for invoke_json) returned something that is
    not a JSON object."""


def _require_credentials() -> None:
    if not os.environ.get("AWS_ACCESS_KEY_ID", "").strip():
        raise ApiError(
            503, "service_unavailable",
            "this feature needs AWS credentials: set AWS_ACCESS_KEY_ID, "
            "AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION in agent/.env",
            {"missing": "AWS_ACCESS_KEY_ID"},
        )


def _get_client():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        _client = boto3.client(
            "bedrock-runtime",
            config=Config(
                read_timeout=BEDROCK_READ_TIMEOUT_SECONDS,
                connect_timeout=BEDROCK_CONNECT_TIMEOUT_SECONDS,
                retries={"max_attempts": BEDROCK_RETRIES},
            ),
        )
    return _client


def _converse(system_prompt: str, user_text: str, max_tokens: int) -> str:
    _require_credentials()
    try:
        response = _get_client().converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            inferenceConfig={"maxTokens": max_tokens},  # Sonnet 5.5 rejects `temperature`
        )
        return response["output"]["message"]["content"][0]["text"].strip()
    except ApiError:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"bedrock call failed: {type(exc).__name__}")  # class name only, never content
        raise BedrockUnavailable() from None


def invoke_text(system_prompt: str, user_text: str, max_tokens: int) -> str:
    """Freeform text reply (e.g. the /ask answer)."""
    return _converse(system_prompt, user_text, max_tokens)


def invoke_json(system_prompt: str, user_text: str, max_tokens: int = 300) -> dict:
    """Ask the model for a JSON object and return it parsed. Raises BedrockUnavailable
    on any service error or if the reply is not a JSON object."""
    text = _converse(system_prompt, user_text, max_tokens)
    try:
        fenced = _FENCE_RE.match(text)
        parsed = json.loads(fenced.group(1) if fenced else text)
    except json.JSONDecodeError:
        print("bedrock call failed: reply was not valid JSON")
        raise BedrockUnavailable() from None
    if not isinstance(parsed, dict):
        print("bedrock call failed: reply was not a JSON object")
        raise BedrockUnavailable()
    return parsed
