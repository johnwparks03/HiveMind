"""Config values. Per CLAUDE.md: these must be configuration, not literals scattered in code."""
import os
from pathlib import Path

from dotenv import load_dotenv

AGENT_DIR = Path(__file__).resolve().parent.parent

# agent/.env (gitignored; see .env.example). Variables already set in the shell win.
load_dotenv(AGENT_DIR / ".env")

DATA_DIR = AGENT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SQLITE_PATH = DATA_DIR / "registry.db"
CHROMA_PATH = DATA_DIR / "chroma"

HOST = "127.0.0.1"
PORT = 8420

FRONTEND_ORIGIN = "http://localhost:5173"

# Central service / Cognito. The IDs are CDK outputs (UserPoolClientId, HttpApiUrl)
# and are not committed; set them in agent/.env or the environment (see agent/README.md).
# Blank counts as unset; the endpoints that need them return 503 instead of crashing.
COGNITO_REGION = os.environ.get("HIVEMIND_COGNITO_REGION", "").strip() or "us-east-1"
COGNITO_CLIENT_ID = os.environ.get("HIVEMIND_COGNITO_CLIENT_ID", "").strip()
CENTRAL_API_URL = os.environ.get("HIVEMIND_CENTRAL_API_URL", "").strip().rstrip("/")
CENTRAL_TIMEOUT_SECONDS = 10
# How long GET /session reuses the last central /health result.
CENTRAL_HEALTH_CACHE_SECONDS = 5
# Refresh the access token this long before it expires.
TOKEN_REFRESH_MARGIN_SECONDS = 60
# Windows Credential Manager entry for the refresh token.
KEYRING_SERVICE = "HiveMind"
# Credential Manager blobs max out at 2,560 bytes (~1,280 UTF-16 characters), so long
# refresh tokens are split into chunks of this many characters.
KEYRING_CHUNK_CHARS = 1000

# Embedding / chunking
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE_CHARS = 800
CHUNK_OVERLAP_CHARS = 100

# Search
# Collection uses cosine space, so distance = 1 - cosine_similarity; smaller is a
# better match. First real calibration point (2026-10-07, all-MiniLM-L6-v2): a
# document titled "Q4 Budget Plan" against the query "budget plan" scored 0.56;
# unrelated documents in the same small test set scored 0.75-0.91. 0.65 sits in
# that gap. Revisit once there's a bigger, messier real corpus to test against —
# this is one data point, not a tuned value.
SIMILARITY_DISTANCE_THRESHOLD = 0.65
SEARCH_RESULT_LIMIT = 20

# Filename boost: whole-chunk embeddings dilute a strong title match once it's
# pooled together with unrelated body text (confirmed 2026-10-07 — "meeting
# notes" scored 0.72 similarity alone, but only 0.16 once embedded as part of a
# full document about something else). A literal word overlap with the filename
# is a cheap, reliable signal vector similarity alone misses.
FILENAME_BOOST_PER_WORD = 0.15
FILENAME_BOOST_MAX = 0.3

# Query parsing: how long the agent waits for the optional central /llm/query
# upgrade before keeping its own local parse (Technical_Blueprint.md section 03).
LLM_QUERY_TIMEOUT_SECONDS = 2.5

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}
