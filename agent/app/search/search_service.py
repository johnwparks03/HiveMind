"""Local search orchestration. Technical_Blueprint.md section 04:
"Filter first, then rank" and "comes up short" -> central (not built today;
the agent track is being built standalone per docs/stories/BACKLOG.md's E2 note).
"""
import re
from datetime import datetime

from app.config import (
    FILENAME_BOOST_MAX,
    FILENAME_BOOST_PER_WORD,
    SEARCH_RESULT_LIMIT,
    SIMILARITY_DISTANCE_THRESHOLD,
)
from app.indexing.embeddings import embed
from app.indexing.vector_store import _date_range_where, iter_chunks, query as vector_query
from app.search.query_parser import ParsedQuery, parse_query_locally

_WORD_RE = re.compile(r"[a-z0-9]+")


def _words(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _filename_boost(filename: str, topic: str) -> float:
    """A literal word overlap between the query and the filename is a cheap,
    reliable signal that whole-chunk vector similarity alone can miss — a short,
    exact-match title gets diluted once it's pooled together with an unrelated
    body (see config.py for the measurement that motivated this)."""
    if not topic:
        return 0.0
    matches = _words(topic) & _words(filename)
    return min(len(matches) * FILENAME_BOOST_PER_WORD, FILENAME_BOOST_MAX)


def _group_best_per_file(ids, documents, metadatas, distances) -> list[dict]:
    best: dict[str, dict] = {}
    for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        file_id = metadata["file_id"]
        if file_id not in best or distance < best[file_id]["score"]:
            best[file_id] = {
                "file_id": file_id,
                "filename": metadata["filename"],
                "path": metadata["path"],
                "file_created_at": datetime.fromtimestamp(metadata["file_created_at_ts"]).isoformat(),
                "file_modified_at": datetime.fromtimestamp(metadata["file_modified_at_ts"]).isoformat(),
                "snippet": document[:280],
                "score": distance,
            }
    return sorted(best.values(), key=lambda r: r["score"])


def _list_by_recency(date_from_ts, date_to_ts) -> list[dict]:
    """Empty topic -> list by recency within the date range (mirrors the central
    search behavior in Technical_Blueprint.md section 04 for the local case).
    """
    where = _date_range_where(date_from_ts, date_to_ts)
    seen: dict[str, dict] = {}
    for metadata, document in iter_chunks(where):
        file_id = metadata["file_id"]
        if file_id in seen:
            continue
        seen[file_id] = {
            "file_id": file_id,
            "filename": metadata["filename"],
            "path": metadata["path"],
            "file_created_at": datetime.fromtimestamp(metadata["file_created_at_ts"]).isoformat(),
            "file_modified_at": datetime.fromtimestamp(metadata["file_modified_at_ts"]).isoformat(),
            "snippet": document[:280],
            "score": None,
        }
    return sorted(seen.values(), key=lambda r: r["file_modified_at"], reverse=True)[:SEARCH_RESULT_LIMIT]


def search_local(raw_query: str) -> dict:
    parsed: ParsedQuery = parse_query_locally(raw_query)
    date_from_ts = parsed.date_from.timestamp() if parsed.date_from else None
    date_to_ts = parsed.date_to.timestamp() if parsed.date_to else None

    if not parsed.topic:
        results = _list_by_recency(date_from_ts, date_to_ts)
    else:
        [embedding] = embed([parsed.topic])
        raw = vector_query(embedding, date_from_ts, date_to_ts, n_results=SEARCH_RESULT_LIMIT * 3)
        ids = raw["ids"][0]
        results = []
        if ids:
            results = _group_best_per_file(ids, raw["documents"][0], raw["metadatas"][0], raw["distances"][0])
            for r in results:
                r["score"] = max(0.0, r["score"] - _filename_boost(r["filename"], parsed.topic))
            results.sort(key=lambda r: r["score"])
            results = [r for r in results if r["score"] <= SIMILARITY_DISTANCE_THRESHOLD][:SEARCH_RESULT_LIMIT]

    return {
        "interpreted": {
            "topic": parsed.topic,
            "date_from": parsed.date_from.isoformat() if parsed.date_from else None,
            "date_to": parsed.date_to.isoformat() if parsed.date_to else None,
            "source": parsed.source,
        },
        "local_results": results,
        # Central/teammate search isn't built yet — see docs/stories/BACKLOG.md E2 note.
        "teammate": {"searched": False, "skipped_reason": "central_not_built", "results": []},
    }
