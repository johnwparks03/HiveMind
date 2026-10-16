"""Local search orchestration. Technical_Blueprint.md section 04:
"Filter first, then rank" and "comes up short" -> central (docs/stories/BACKLOG.md
E3-S8: the merge was built 2026-10-16, once central search itself existed).
"""
import json
import re
from datetime import datetime
from pathlib import Path

from app.central import client as central_client
from app.central import teams
from app.config import (
    FILENAME_BOOST_MAX,
    FILENAME_BOOST_PER_WORD,
    FORMAT_WORD_BOOST,
    FORMAT_WORDS,
    QUERY_EXPANSION_ENABLED,
    SEARCH_RESULT_LIMIT,
    SIMILARITY_DISTANCE_THRESHOLD,
    TAG_BOOST_MAX,
    TAG_BOOST_PER_WORD,
    TOTAL_BOOST_MAX,
)
from app.db import session
from app.errors import ApiError
from app.indexing.embeddings import embed
from app.indexing.vector_store import _date_range_where, iter_chunks, query as vector_query
from app.search.query_expansion import expand_topic
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


def _format_boost(filename: str, topic: str) -> float:
    """A query naming the file's *format* ("slides", "notes") rather than its
    content has nothing for embedding similarity to match against — see config.py
    for the measurement that motivated this. Deterministic word-to-extension
    mapping, same spirit as the filename boost above."""
    if not topic:
        return 0.0
    trigger_words = FORMAT_WORDS.get(Path(filename).suffix.lower())
    if not trigger_words:
        return 0.0
    return FORMAT_WORD_BOOST if _words(topic) & trigger_words else 0.0


def _tags_by_file_id(file_ids: list[str]) -> dict[str, list[str]]:
    if not file_ids:
        return {}
    with session() as conn:
        placeholders = ",".join("?" * len(file_ids))
        rows = conn.execute(
            f"SELECT file_id, tags FROM files WHERE file_id IN ({placeholders})", file_ids
        ).fetchall()
    return {row["file_id"]: json.loads(row["tags"]) if row["tags"] else [] for row in rows}


def _tag_boost(tags: list[str], topic: str) -> float:
    """A third deterministic signal alongside the filename/format boosts above —
    word overlap between the query and a file's (model-generated, on-demand) tags.
    Most files won't have tags at all yet, since generation is on-demand; this is a
    no-op for those, not a penalty."""
    if not topic or not tags:
        return 0.0
    matches = _words(topic) & _words(" ".join(tags))
    return min(len(matches) * TAG_BOOST_PER_WORD, TAG_BOOST_MAX)


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


def _central_search(topic: str | None, date_from: datetime | None, date_to: datetime | None):
    """Returns (results, skipped_reason) — skipped_reason is None on success. Dates
    must stay timezone-aware (central's validator rejects naive ones outright, the
    same gotcha that silently broke every publish attempt earlier this build)."""
    if teams.current_team_or_none() is None:
        return [], "no_team"
    body = {
        "topic": topic,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    try:
        resp = central_client.request_json("POST", "/search", json=body)
    except ApiError as exc:
        return [], "no_team" if exc.code == "no_team" else "central_unavailable"
    return (resp or {}).get("results", []), None


def list_team_files() -> list[dict]:
    """Everything your team has shared, most recent first — central's no-topic
    search mode (see search() above: topic=None skips the tsquery join entirely
    and just orders by recency). Backs the Groups page's browse view."""
    results, skipped_reason = _central_search(None, None, None)
    if skipped_reason == "no_team":
        raise ApiError(403, "no_team", "you are not in a team")
    if skipped_reason == "central_unavailable":
        raise ApiError(503, "service_unavailable", "central is unavailable")
    return results


def search_local(raw_query: str, include_teammates: bool = False) -> dict:
    parsed: ParsedQuery = parse_query_locally(raw_query)
    date_from_ts = parsed.date_from.timestamp() if parsed.date_from else None
    date_to_ts = parsed.date_to.timestamp() if parsed.date_to else None

    if not parsed.topic:
        results = _list_by_recency(date_from_ts, date_to_ts)
    else:
        embed_input = expand_topic(parsed.topic) if QUERY_EXPANSION_ENABLED else parsed.topic
        [embedding] = embed([embed_input])
        raw = vector_query(embedding, date_from_ts, date_to_ts, n_results=SEARCH_RESULT_LIMIT * 3)
        ids = raw["ids"][0]
        results = []
        if ids:
            results = _group_best_per_file(ids, raw["documents"][0], raw["metadatas"][0], raw["distances"][0])
            tags_by_id = _tags_by_file_id([r["file_id"] for r in results])
            for r in results:
                boost = (
                    _filename_boost(r["filename"], parsed.topic)
                    + _format_boost(r["filename"], parsed.topic)
                    + _tag_boost(tags_by_id.get(r["file_id"], []), parsed.topic)
                )
                r["score"] = max(0.0, r["score"] - min(boost, TOTAL_BOOST_MAX))
            results.sort(key=lambda r: r["score"])
            results = [r for r in results if r["score"] <= SIMILARITY_DISTANCE_THRESHOLD][:SEARCH_RESULT_LIMIT]

    # Central is only asked when local came up short, or the user explicitly asked
    # to include teammates — never as a matter of course (Technical_Blueprint.md
    # section 04).
    if include_teammates or not results:
        teammate_results, skipped_reason = _central_search(parsed.topic, parsed.date_from, parsed.date_to)
        teammate = {
            "searched": skipped_reason is None,
            "skipped_reason": skipped_reason,
            "results": teammate_results,
        }
    else:
        teammate = {"searched": False, "skipped_reason": "local_sufficient", "results": []}

    return {
        "interpreted": {
            "topic": parsed.topic,
            "date_from": parsed.date_from.isoformat() if parsed.date_from else None,
            "date_to": parsed.date_to.isoformat() if parsed.date_to else None,
            "source": parsed.source,
        },
        "local_results": results,
        "teammate": teammate,
    }
