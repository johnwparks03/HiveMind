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
# How long GET /session reuses the team it last fetched from central.
TEAM_CACHE_SECONDS = 5
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
# How many chunks to read per page when listing by recency. Chroma's get() returns at most
# this many per call, so the listing pages through instead of stopping at the first page.
CHROMA_PAGE_SIZE = 500

# Filename boost: whole-chunk embeddings dilute a strong title match once it's
# pooled together with unrelated body text (confirmed 2026-10-07 — "meeting
# notes" scored 0.72 similarity alone, but only 0.16 once embedded as part of a
# full document about something else). A literal word overlap with the filename
# is a cheap, reliable signal vector similarity alone misses.
FILENAME_BOOST_PER_WORD = 0.15
FILENAME_BOOST_MAX = 0.3

# Format-word boost: a word describing a file's *format* ("slides", "notes") has weak
# semantic content on its own — no chunk text ever says "this is a slide deck," so
# embedding similarity alone misses it. Measured 2026-10-13: "slides" scored 0.80-0.86
# against every candidate, including an actual .pptx modified that same week — nowhere
# close to the 0.65 threshold, and the filename boost above doesn't help either since
# "slides" isn't literally in that file's name. A deterministic word-to-extension
# mapping is a second cheap signal alongside the filename boost. Query expansion
# (query_expansion.py) was tried for this kind of gap and made things worse, not
# better — this is a narrower, explainable fix for the specific case it was for.
FORMAT_WORD_BOOST = 0.25
FORMAT_WORDS = {
    ".pptx": {"slide", "slides", "deck", "presentation"},
    ".docx": {"doc", "document", "memo", "report"},
    ".pdf": {"pdf"},
    ".txt": {"note", "notes", "transcript", "log"},
}
# Filename boost and format boost can both apply to the same result; cap their
# combined effect so a coincidental double-match can't drag a genuinely unrelated
# file under the threshold.
TOTAL_BOOST_MAX = 0.35

# Query parsing: how long the agent waits for the optional central /llm/query
# upgrade before keeping its own local parse (Technical_Blueprint.md section 03).
LLM_QUERY_TIMEOUT_SECONDS = 2.5

# Query expansion: WordNet synonyms added to the topic before embedding, to close
# vocabulary gaps between a short query and a document's actual wording (e.g. "seed
# round" vs "fundraising") that semantic similarity alone can still miss. Entirely
# offline (WordNet is a static local corpus, not a network call) — no Bedrock
# involved. Measured against the real test corpus (2026-10-13) and disabled: it made
# every sample query's match distance worse, not better (e.g. "seed round" -> "round"
# expanded to its ammunition/geometry sense: "elevation, lift, unit of ammunition, one
# shot"). MiniLM's own semantic embedding already handles this better than word-by-word
# dictionary lookup. Left in place, off, in case someone wants to try a different
# source (a curated domain thesaurus instead of raw WordNet) rather than redoing this
# measurement from scratch.
QUERY_EXPANSION_ENABLED = False
QUERY_EXPANSION_MAX_SYNONYMS_PER_WORD = 2
QUERY_EXPANSION_MAX_TOTAL_WORDS = 6

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}

# Local Bedrock (decided 2026-10-15, demo/MVP only — see CLAUDE.md). Credentials come
# from the standard AWS env vars (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY /
# AWS_DEFAULT_REGION), set in agent/.env alongside the Cognito values; boto3 reads
# them automatically, no custom loading needed. Blank counts as unset, same as the
# Cognito/central config above — the features that need it return 503 instead of a
# confusing boto3 exception.
BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-5-5"
BEDROCK_CONNECT_TIMEOUT_SECONDS = 5
BEDROCK_READ_TIMEOUT_SECONDS = 20
BEDROCK_RETRIES = 1

# POST /ask: multi-document Q&A. No offline fallback — unlike /search's optional
# central LLM upgrade, there is no local generative model, so this endpoint is
# honestly online-only. Caps below bound Bedrock cost/latency regardless of corpus
# size: files are added in recency order until the total budget is hit.
ASK_MAX_FILES = 8
ASK_MAX_CHARS_PER_FILE = 1200
ASK_MAX_TOTAL_CHARS = 8000
# Verified live 2026-10-15: a detailed multi-file breakdown hit 800 and was cut off
# mid-word with no indication anything was missing (stopReason: max_tokens, usage.
# outputTokens: 800 exactly). Raised; ask_service.py also now detects and flags
# truncation explicitly so this fails visibly instead of silently, if it recurs.
ASK_MAX_ANSWER_TOKENS = 2000

# Tag generation (agent/app/folders/scanner.py): runs automatically on add/rescan for
# every newly indexed file (explicit product decision, 2026-10-15 — cost/latency
# accepted). Best-effort: a Bedrock problem leaves a file untagged, never fails the
# scan. POST /files/{id}/tags/generate (routes_files.py) also exists for retagging a
# single file by hand. Same validation shape as central/lambdas/llm.py's tag
# generation (mirrored, not imported — agent and central are separate deployables).
TAG_EXCERPT_MAX_CHARS = 3000
TAG_MIN_COUNT = 5
TAG_MAX_COUNT = 8
TAG_MAX_GENERATION_TOKENS = 200

# Tag boost: a third deterministic signal alongside the filename and format-word
# boosts above — word overlap between the query topic and a file's (model-generated)
# tags. Same reasoning as those two: a short, exact keyword match is a cheap signal
# that whole-chunk embedding similarity alone can miss.
TAG_BOOST_PER_WORD = 0.15
TAG_BOOST_MAX = 0.3
