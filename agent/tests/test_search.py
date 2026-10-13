"""Local search over a corpus: date filtering, result limits, and the query parser.

Ranking quality is checked in test_search_quality.py (real model only). Everything here
works with fake embeddings, so it checks what search returns, not how well it ranks.
"""
from datetime import datetime, timedelta
from pathlib import Path
import shutil

import pytest

from app.config import SEARCH_RESULT_LIMIT
from app.folders.scanner import add_folder
from app.search.query_parser import parse_query_locally
from app.search.search_service import _filename_boost, search_local
from corpus_generator import TOTAL_DOCX, TOTAL_PPTX


@pytest.fixture
def searchable(isolated_store, corpus):
    root, written = corpus
    add_folder(str(root))
    return root, written


UNREADABLE_EDGE_CASES = {"Blank document.docx", "Corrupt export.docx"}


def readable_files(root: Path):
    return [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix in {".docx", ".pptx"} and p.name not in UNREADABLE_EDGE_CASES
    ]


def _mtime_in(path: Path, start: datetime, end: datetime) -> bool:
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return start.replace(tzinfo=None) <= modified <= end.replace(tzinfo=None)


def test_last_week_returns_only_files_from_that_week(searchable):
    _, written = searchable
    parsed = parse_query_locally("last week")
    assert parsed.topic is None
    assert parsed.date_from and parsed.date_to

    result = search_local("last week")
    expected = [
        p for p, _ in written
        if p.name not in UNREADABLE_EDGE_CASES and _mtime_in(p, parsed.date_from, parsed.date_to)
    ]

    returned = {r["filename"] for r in result["local_results"]}
    expected_names = {p.name for p in expected}
    assert returned <= expected_names, f"non-matching files returned: {returned - expected_names}"
    assert len(result["local_results"]) == min(SEARCH_RESULT_LIMIT, len(expected)), (
        f"{len(expected)} files fall in last week but {len(result['local_results'])} were returned"
    )


def test_most_recent_files_are_listed_first(searchable):
    result = search_local("")
    modified = [r["file_modified_at"] for r in result["local_results"]]
    assert modified == sorted(modified, reverse=True)
    assert len(modified) == SEARCH_RESULT_LIMIT


def test_result_limit_holds_for_broad_topic_search(searchable):
    result = search_local("project status update")
    assert len(result["local_results"]) <= SEARCH_RESULT_LIMIT
    ids = [r["file_id"] for r in result["local_results"]]
    assert len(ids) == len(set(ids)), "each file should appear once"


def test_every_result_carries_the_fields_the_ui_needs(searchable):
    result = search_local("budget plan")
    assert result["local_results"], "expected at least one result"
    for r in result["local_results"]:
        assert {"file_id", "filename", "path", "file_modified_at", "snippet"} <= r.keys()
        assert r["snippet"]
        assert Path(r["path"]).exists()


def test_search_response_shape(searchable):
    result = search_local("meeting notes from 3 days ago")
    assert set(result) == {"interpreted", "local_results", "teammate"}
    assert result["interpreted"]["topic"] == "meeting notes"
    assert result["interpreted"]["date_from"] is not None
    assert result["teammate"]["searched"] is False


def test_filename_boost_rewards_title_overlap():
    assert _filename_boost("Budget plan 012 2026-02-01.docx", "budget plan") == pytest.approx(0.3)
    assert _filename_boost("Roadmap 003 2026-02-05.docx", "budget plan") == 0.0
    assert _filename_boost("Budget plan.docx", "") == 0.0


# --- Query parser -----------------------------------------------------------------------
# Fixed clock so relative phrases are deterministic: Wednesday 14 October 2026, 09:00.
NOW = datetime(2026, 10, 14, 9, 0).astimezone()


@pytest.mark.parametrize(
    "query, topic",
    [
        ("budget plan from last week", "budget plan"),
        ("meeting notes from 3 days ago", "meeting notes"),
        ("roadmap deck from March", "roadmap deck"),
        ("status report", "status report"),
    ],
)
def test_topic_is_what_remains_after_date_words(query, topic):
    assert parse_query_locally(query, local_now=NOW).topic == topic


def test_last_week_spans_monday_to_sunday_of_the_previous_week():
    parsed = parse_query_locally("last week", local_now=NOW)
    assert parsed.date_from.date() == datetime(2026, 10, 5).date()  # Monday
    assert parsed.date_to.date() == datetime(2026, 10, 11).date()   # Sunday
    assert parsed.date_from.hour == 0 and parsed.date_to.hour == 23


def test_this_month_covers_the_whole_calendar_month():
    parsed = parse_query_locally("this month", local_now=NOW)
    assert parsed.date_from.date() == datetime(2026, 10, 1).date()
    assert parsed.date_to.date() == datetime(2026, 10, 31).date()


def test_n_days_ago_resolves_to_that_single_day():
    parsed = parse_query_locally("3 days ago", local_now=NOW)
    assert parsed.date_from.date() == datetime(2026, 10, 11).date()
    assert parsed.date_to.date() == datetime(2026, 10, 11).date()


def test_empty_query_has_no_topic_or_dates():
    parsed = parse_query_locally("   ", local_now=NOW)
    assert (parsed.topic, parsed.date_from, parsed.date_to) == (None, None, None)


# --- Scale ------------------------------------------------------------------------------
@pytest.fixture
def large_folder(isolated_store, corpus, tmp_path):
    """Three copies of the corpus (~250 files) in one folder. Enough chunks to get past
    the single-query limits that a 4-6 file test would never reach."""
    root, written = corpus
    big = tmp_path / "big"
    for copy in range(3):
        dest = big / f"copy {copy + 1}"
        shutil.copytree(root, dest)
    add_folder(str(big))
    return big


def test_large_folder_is_fully_registered(large_folder):
    from app.db import session
    with session() as conn:
        count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    assert count == 3 * (TOTAL_DOCX + TOTAL_PPTX + 3)


def test_recency_listing_at_scale_returns_the_newest_files(large_folder):
    """Without a topic, search lists by recency. Across ~250 files the newest files must still
    come back, not whichever files happened to be stored first."""
    newest = sorted(
        (p for p in readable_files(large_folder)),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:SEARCH_RESULT_LIMIT]
    expected_names = {p.name for p in newest}

    result = search_local("")
    returned = {r["filename"] for r in result["local_results"]}
    assert returned == expected_names


def test_last_week_at_scale_is_not_truncated(large_folder):
    parsed = parse_query_locally("last week")
    expected = [p for p in readable_files(large_folder) if _mtime_in(p, parsed.date_from, parsed.date_to)]
    result = search_local("last week")
    assert len(result["local_results"]) == min(SEARCH_RESULT_LIMIT, len(expected))
