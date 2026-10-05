"""Config values. Per CLAUDE.md: these must be configuration, not literals scattered in code."""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SQLITE_PATH = DATA_DIR / "registry.db"
CHROMA_PATH = DATA_DIR / "chroma"

HOST = "127.0.0.1"
PORT = 8420

FRONTEND_ORIGIN = "http://localhost:5173"

# Embedding / chunking
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE_CHARS = 800
CHUNK_OVERLAP_CHARS = 100

# Search
# Collection uses cosine space, so distance = 1 - cosine_similarity; smaller is a
# better match. Tune against real files once there's a corpus to test with.
SIMILARITY_DISTANCE_THRESHOLD = 0.4
SEARCH_RESULT_LIMIT = 20

# Query parsing: how long the agent waits for the optional central /llm/query
# upgrade before keeping its own local parse (Technical_Blueprint.md section 03).
LLM_QUERY_TIMEOUT_SECONDS = 2.5

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}
