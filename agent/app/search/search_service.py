"""Local search orchestration. Technical_Blueprint.md section 04:
"Filter first, then rank" and "comes up short" -> central (not built today;
the agent track is being built standalone per docs/stories/BACKLOG.md's E2 note).
"""
from datetime import datetime

from app.config import SEARCH_RESULT_LIMIT, SIMILARITY_DISTANCE_THRESHOLD
from app.indexing.embeddings import embed
from app.indexing.vector_store import get_collection, query as vector_query
from app.search.query_parser import ParsedQuery, parse_query_locally


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
    collection = get_collection()
    where = None
    if date_from_ts is not None or date_to_ts is not None:
        bounds = {}
        if date_from_ts is not None:
            bounds["$gte"] = date_from_ts
        if date_to_ts is not None:
            bounds["$lte"] = date_to_ts
        where = {"file_modified_at_ts": bounds}
    got = collection.get(where=where, limit=500)
    seen: dict[str, dict] = {}
    for metadata, document in zip(got["metadatas"], got["documents"]):
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
