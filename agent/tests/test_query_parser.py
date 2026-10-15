"""Date-range parsing added 2026-10-14/15: generic placeholders, format words don't
belong here (that's search_service's job), but the trailing-window / spelled-out
number handling is pure parser logic, worth pinning directly.
"""
from datetime import datetime

from app.search.query_parser import parse_query_locally

NOW = datetime(2026, 10, 15, 14, 30)


def test_trailing_window_spans_from_n_units_back_to_now():
    result = parse_query_locally("the last two weeks", local_now=NOW)
    assert result.topic is None
    assert result.date_from.date() == datetime(2026, 10, 1).date()
    assert result.date_to.date() == NOW.date()


def test_trailing_window_accepts_digits_too():
    digits = parse_query_locally("the past 3 months", local_now=NOW)
    words = parse_query_locally("the past three months", local_now=NOW)
    assert digits.date_from == words.date_from
    assert digits.date_to == words.date_to


def test_n_units_ago_is_a_specific_past_unit_not_a_trailing_window():
    # "2 weeks ago" names that one week back, not a span from then to now — a
    # different meaning from "the last 2 weeks" above, even though both use "2 weeks".
    ago = parse_query_locally("two weeks ago", local_now=NOW)
    trailing = parse_query_locally("the last two weeks", local_now=NOW)
    assert (ago.date_to - ago.date_from).days == 6
    assert ago.date_from != trailing.date_from
    assert ago.topic is None


def test_topic_survives_around_the_trailing_window_phrase():
    result = parse_query_locally("give me a breakdown of what we did the last two weeks", local_now=NOW)
    assert result.topic == "give me a breakdown of what we did"
    assert result.date_from.date() == datetime(2026, 10, 1).date()


def test_bare_month_name_is_the_whole_month():
    result = parse_query_locally("September", local_now=NOW)
    assert result.topic is None
    assert result.date_from.date() == datetime(2026, 9, 1).date()
    assert result.date_to.date() == datetime(2026, 9, 30).date()


def test_generic_placeholder_topic_is_dropped():
    result = parse_query_locally("anything from last week", local_now=NOW)
    assert result.topic is None
    assert result.date_from is not None
