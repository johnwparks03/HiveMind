"""One-off connectivity check for Bedrock model access. NOT part of the shipped
app — per CLAUDE.md, the agent never calls Bedrock or holds AWS credentials;
that only ever happens from the central service once it's built. This just
answers "does our sandbox account actually have access to the model" before
building the real /llm/query proxy (the E0/E3 "verify in AWS" open items).

Credential: reads AWS_BEARER_TOKEN_BEDROCK, BEDROCK_MODEL_ID, and BEDROCK_REGION
from scripts/.env (gitignored — copy scripts/.env.example to scripts/.env and
fill in real values there; never commit .env or paste the key into chat/code).

Usage:
    python scripts/test_bedrock.py
    # or override what .env has:
    python scripts/test_bedrock.py --model-id <id> --region us-west-2

The model ID comes from the Bedrock console (CLAUDE.md: "do not guess a region
or model ID") - copy the exact inference profile or model ID shown there.
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default=os.environ.get("BEDROCK_MODEL_ID"), help="Exact model/inference-profile ID from the Bedrock console")
    parser.add_argument("--region", default=os.environ.get("BEDROCK_REGION", "us-east-1"))
    args = parser.parse_args()

    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        print("AWS_BEARER_TOKEN_BEDROCK is not set.", file=sys.stderr)
        print("Copy scripts/.env.example to scripts/.env and fill in your key.", file=sys.stderr)
        sys.exit(1)
    if not args.model_id:
        print("No model ID. Set BEDROCK_MODEL_ID in scripts/.env or pass --model-id.", file=sys.stderr)
        sys.exit(1)

    import boto3

    client = boto3.client("bedrock-runtime", region_name=args.region)

    print(f"Calling {args.model_id} in {args.region} ...")
    response = client.converse(
        modelId=args.model_id,
        messages=[{"role": "user", "content": [{"text": "Reply with exactly: HiveMind Bedrock test OK"}]}],
        inferenceConfig={"maxTokens": 32, "temperature": 0},
    )

    text = response["output"]["message"]["content"][0]["text"]
    print("Model replied:", text)
    print("\nUsage:", response.get("usage"))


if __name__ == "__main__":
    main()
