"""Local embeddings. Technical_Blueprint.md section 01/03: free, no API key, no network call.
Loaded lazily and once — the model load is the slow part (a couple seconds on CPU).
"""
import hashlib
import os
from functools import lru_cache
from pathlib import Path


def _model_is_cached(model_name: str) -> bool:
    """Checked with a plain path lookup, deliberately *before* importing
    huggingface_hub/sentence_transformers below — huggingface_hub reads
    HF_HUB_OFFLINE into a module-level constant the moment it's imported, so
    setting the env var any later (e.g. inside a function called after the
    top-of-file import) has no effect. This has to happen first, or not at all.
    """
    hf_home = os.environ.get("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
    repo_dir = "models--sentence-transformers--" + model_name if "/" not in model_name else "models--" + model_name.replace("/", "--")
    return (Path(hf_home) / "hub" / repo_dir).exists()


from app.config import EMBEDDING_MODEL  # noqa: E402

# If the model's already cached, go fully offline — this is what CLAUDE.md's
# "no network call" actually requires, and it also sidesteps corporate
# SSL-inspection proxies that break huggingface_hub's version-check requests
# (they still fall back to cache, but only after ~45s of retries on every
# single startup). Left unset on a machine that's never downloaded the model
# yet, so the first run anywhere can still do a real download.
if _model_is_cached(EMBEDDING_MODEL):
    os.environ["HF_HUB_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer  # noqa: E402

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
