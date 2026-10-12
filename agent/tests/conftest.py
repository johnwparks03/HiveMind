import os
import shutil
import sys
from pathlib import Path

# Must run before anything imports app.indexing.embeddings, which reads this at import time.
# Real-model tests opt in with HIVEMIND_TEST_REAL_EMBEDDINGS=1 (see test_search_quality.py).
if os.environ.get("HIVEMIND_TEST_REAL_EMBEDDINGS") != "1":
    os.environ["HIVEMIND_FAKE_EMBEDDINGS"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

import app.db as db  # noqa: E402
from app.indexing import vector_store  # noqa: E402
from corpus_generator import generate  # noqa: E402


@pytest.fixture(scope="session")
def corpus_template(tmp_path_factory):
    """The 83-file corpus, generated once per test run. Tests copy it before mutating."""
    root = tmp_path_factory.mktemp("corpus_template") / "corpus"
    written = generate(root)
    return root, written


@pytest.fixture
def corpus(tmp_path, corpus_template):
    """A fresh copy of the corpus for one test. Returns (root, intended mtimes)."""
    template_root, written = corpus_template
    root = tmp_path / "corpus"
    shutil.copytree(template_root, root)
    # Map each generated path onto the copy so tests can refer to files by the same names.
    relative = [(p.relative_to(template_root), when) for p, when in written]
    return root, [(root / rel, when) for rel, when in relative]


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Points the SQLite registry and Chroma store at a temp dir for this test only."""
    monkeypatch.setattr(db, "SQLITE_PATH", tmp_path / "registry.db")
    chroma_dir = tmp_path / "chroma"
    monkeypatch.setattr(vector_store, "CHROMA_PATH", chroma_dir)
    vector_store.get_collection.cache_clear()
    db.init_db()
    yield tmp_path
    vector_store.get_collection.cache_clear()
