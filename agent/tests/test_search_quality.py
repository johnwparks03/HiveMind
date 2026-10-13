"""Ranking quality with the real embedding model (all-MiniLM-L6-v2).

Skipped unless HIVEMIND_TEST_REAL_EMBEDDINGS=1, because it needs the model downloaded or
cached and is slower. Each query has a known set of files (the corpus generator names
them by topic), and the test checks how many of those land in the top results.
"""
import os

import pytest

from app.folders.scanner import add_folder
from app.search.search_service import search_local

pytestmark = pytest.mark.skipif(
    os.environ.get("HIVEMIND_TEST_REAL_EMBEDDINGS") != "1",
    reason="set HIVEMIND_TEST_REAL_EMBEDDINGS=1 to run ranking tests with the real model",
)

# query -> (filename stem the generator uses, number of files with that stem)
QUERIES = {
    "budget plan": ("Budget plan", 6),
    "vendor evaluation": ("Vendor evaluation", 6),
    "retrospective": ("Retrospective", 6),
    "risk register": ("Risk register", 6),
    "campaign brief": ("Campaign brief", 6),
    "meeting notes": ("Meeting notes", 6),
    "steering committee": ("Steering committee", 4),
    "brand guidelines": ("Brand guidelines", 4),
}

# Share of a query's expected files that must appear in the top 10 results.
MIN_RECALL_AT_10 = 0.8


@pytest.fixture(scope="module")
def ranked_store(tmp_path_factory, corpus_template):
    """One indexed corpus shared by every ranking test in this module (real embeddings are slow)."""
    import shutil

    import app.db as db
    from app.indexing import vector_store

    root_src, _ = corpus_template
    base = tmp_path_factory.mktemp("ranked")
    root = base / "corpus"
    shutil.copytree(root_src, root)

    original_db, original_chroma = db.SQLITE_PATH, vector_store.CHROMA_PATH
    db.SQLITE_PATH = base / "registry.db"
    vector_store.CHROMA_PATH = base / "chroma"
    vector_store.get_collection.cache_clear()
    db.init_db()
    try:
        add_folder(str(root))
        yield root
    finally:
        vector_store.get_collection.cache_clear()
        db.SQLITE_PATH, vector_store.CHROMA_PATH = original_db, original_chroma


@pytest.mark.parametrize("query", list(QUERIES))
def test_topic_query_finds_its_files_near_the_top(ranked_store, query):
    stem, expected_count = QUERIES[query]
    result = search_local(query)
    top = [r["filename"] for r in result["local_results"][:10]]

    hits = sum(1 for name in top if name.startswith(stem + " "))
    recall = hits / min(10, expected_count)

    assert recall >= MIN_RECALL_AT_10, (
        f"'{query}': {hits} of the top 10 were '{stem}' files (need {MIN_RECALL_AT_10:.0%}). Top 10: {top}"
    )


def test_a_title_match_outranks_a_body_match(ranked_store):
    """A file named for the query should come before a file that only mentions it in its body."""
    result = search_local("budget plan")
    first = result["local_results"][0]["filename"]
    assert first.startswith("Budget plan "), f"top result was {first}"
