"""Chroma wrapper. One collection, per-chunk date metadata stored as epoch seconds
so Chroma's `where` filter can do range queries (Technical_Blueprint.md section 04:
"filter first, then rank").
"""
from functools import lru_cache
from typing import Iterator

import chromadb

from app.config import CHROMA_PAGE_SIZE, CHROMA_PATH

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


def with_file_scope(where: dict | None, file_ids: set[str] | None) -> dict | None:
    """Combines an existing `where` clause with an optional file_id allowlist (the
    /ask folder/file scope picker). Filtering at the Chroma level instead of after
    retrieval matters for recall: a narrow scope (one small folder in a big corpus)
    could otherwise lose real matches to the n_results cutoff before they're ever
    checked against the scope.
    """
    if file_ids is None:
        return where
    scope_clause = {"file_id": {"$in": list(file_ids)}}
    if where is None:
        return scope_clause
    return {"$and": [where, scope_clause]}


def iter_chunks(where: dict | None) -> Iterator[tuple[dict, str]]:
    """Yields (metadata, document) for every chunk matching `where`, one page at a time."""
    collection = get_collection()
    offset = 0
    while True:
        page = collection.get(where=where, limit=CHROMA_PAGE_SIZE, offset=offset)
        for metadata, document in zip(page["metadatas"], page["documents"]):
            yield metadata, document
        if len(page["ids"]) < CHROMA_PAGE_SIZE:
            return
        offset += CHROMA_PAGE_SIZE


def has_chunks(file_id: str) -> bool:
    return bool(get_collection().get(where={"file_id": file_id}, limit=1)["ids"])


def get_file_chunks(file_id: str) -> list[tuple[int, str, list[float]]]:
    """Every chunk of one file as (chunk_index, text, embedding), in chunk order. Used to
    upload a published file's chunks to central (E6-S6). Sorted explicitly because
    Chroma's get() does not guarantee an order."""
    collection = get_collection()
    rows: list[tuple[int, str, list[float]]] = []
    offset = 0
    while True:
        page = collection.get(
            where={"file_id": file_id}, limit=CHROMA_PAGE_SIZE, offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        for metadata, document, embedding in zip(page["metadatas"], page["documents"], page["embeddings"]):
            rows.append((int(metadata["chunk_index"]), document, [float(x) for x in embedding]))
        if len(page["ids"]) < CHROMA_PAGE_SIZE:
            break
        offset += CHROMA_PAGE_SIZE
    rows.sort(key=lambda r: r[0])
    return rows


def query(
    embedding: list[float],
    date_from_ts: float | None,
    date_to_ts: float | None,
    n_results: int = 50,
    file_id_scope: set[str] | None = None,
):
    collection = get_collection()
    where = with_file_scope(_date_range_where(date_from_ts, date_to_ts), file_id_scope)
    kwargs = {"query_embeddings": [embedding], "n_results": n_results}
    if where is not None:
        kwargs["where"] = where
    return collection.query(**kwargs)
