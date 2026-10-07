"""Chroma wrapper. One collection, per-chunk date metadata stored as epoch seconds
so Chroma's `where` filter can do range queries (Technical_Blueprint.md section 04:
"filter first, then rank").
"""
from functools import lru_cache

import chromadb

from app.config import CHROMA_PATH

COLLECTION_NAME = "files"


@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(file_id: str, chunks: list[str], embeddings: list[list[float]], base_metadata: dict) -> None:
    if not chunks:
        return
    collection = get_collection()
    ids = [f"{file_id}::{i}" for i in range(len(chunks))]
    metadatas = [{**base_metadata, "chunk_index": i} for i in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)


def delete_file(file_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"file_id": file_id})


def field_bounds(field: str, date_from_ts: float | None, date_to_ts: float | None) -> dict:
    """A single field's $gte/$lte condition, Chroma-shaped. Chroma's `where` rejects
    a dict with two operator keys (e.g. {"$gte": a, "$lte": b}) unless each is wrapped
    in its own clause under `$and` — easy to get wrong once and then get wrong again
    in a second place, so every caller goes through this one function instead.
    """
    cond = {}
    if date_from_ts is not None:
        cond["$gte"] = date_from_ts
    if date_to_ts is not None:
        cond["$lte"] = date_to_ts
    return {field: cond} if len(cond) == 1 else {"$and": [{field: {k: v}} for k, v in cond.items()]}


def _date_range_where(date_from_ts: float | None, date_to_ts: float | None) -> dict | None:
    """A file matches if its created date, modified date, OR in-document date falls
    in the range (Technical_Blueprint.md section 04: "either-date matching," and
    section 04/09: the in-document date counts when present)."""
    if date_from_ts is None and date_to_ts is None:
        return None

    return {"$or": [
        field_bounds("file_created_at_ts", date_from_ts, date_to_ts),
        field_bounds("file_modified_at_ts", date_from_ts, date_to_ts),
        field_bounds("in_document_date_ts", date_from_ts, date_to_ts),
    ]}


def query(embedding: list[float], date_from_ts: float | None, date_to_ts: float | None, n_results: int = 50):
    collection = get_collection()
    where = _date_range_where(date_from_ts, date_to_ts)
    kwargs = {"query_embeddings": [embedding], "n_results": n_results}
    if where is not None:
        kwargs["where"] = where
    return collection.query(**kwargs)
