"""Local embeddings. Technical_Blueprint.md section 01/03: free, no API key, no network call.
Loaded lazily and once — the model load is the slow part (a couple seconds on CPU).
"""
import hashlib
import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL

# Set HIVEMIND_FAKE_EMBEDDINGS=1 to skip the real model entirely and use a
# deterministic hash-based stand-in instead. For automated tests and for dev
# environments with no path to huggingface.co — never set this for real use,
# since it has no actual semantic meaning (it only matches on exact text reuse).
_FAKE = os.environ.get("HIVEMIND_FAKE_EMBEDDINGS") == "1"
_FAKE_DIM = 32


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def _fake_embed(texts: list[str]) -> list[list[float]]:
    return [[b / 255.0 for b in hashlib.sha256(t.encode()).digest()[:_FAKE_DIM]] for t in texts]


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if _FAKE:
        return _fake_embed(texts)
    model = get_model()
    return model.encode(texts, normalize_embeddings=True).tolist()
