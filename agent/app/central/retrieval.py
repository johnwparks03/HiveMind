"""Central retrieval for Ask over teammates' documents (E6-S6): POST /retrieval/search.
The agent embeds the question locally and sends only the vector, so the question text
never reaches central. Same error handling as search_service's central call: any failure
degrades to local-only with a reason, it never fails the answer."""
from app import config
from app.central import client as central_client
from app.central import teams
from app.errors import ApiError


def search(query_embedding: list[float], limit: int | None = None) -> tuple[list[dict], str | None]:
    """Returns (chunk rows nearest first, skipped_reason). A row is
    {file_id, filename, chunk_index, text, distance}. The reason is None when central
    was searched, else 'no_team' or 'central_unavailable'."""
    if teams.current_team_or_none() is None:
        return [], "no_team"
    body = {"query_embedding": query_embedding, "limit": limit or config.TEAMMATE_CHUNK_LIMIT}
    try:
        response = central_client.request_json("POST", "/retrieval/search", json=body)
    except ApiError as exc:
        return [], "no_team" if exc.code == "no_team" else "central_unavailable"
    return (response or {}).get("results", []), None
