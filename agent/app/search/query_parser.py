"""Local deterministic query parser. Technical_Blueprint.md section 03: this is the
required baseline for local search — no network call, no API key. The central
/llm/query enhancement (when/if built) only ever replaces this result opportunistically;
it is never required for a local search to succeed.
"""
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta

import dateparser
from dateparser.search import search_dates

# Phrases dateparser resolves well on their own; stripping the matched span from the
# query leaves the topic behind ("meeting notes from 3 days ago" -> "meeting notes").
_RELATIVE_HINTS = re.compile(
    r"\b("
    r"today|yesterday|tomorrow|"
    r"\d+\s+(?:day|week|month)s?\s+ago|"
    r"(?:last|past|this)\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"(?:on\s+)?\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?|"
    r"(?:on\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?"
    r")\b",
    re.IGNORECASE,
)

# "last week" / "this month" etc. name a *range*, not a single day — handled
# explicitly below instead of through dateparser, which was collapsing these to
# one anchor point (so "anything from last week" only ever matched whatever
# happened to fall on that one specific day, instead of the whole week).
_RANGE_PHRASE = re.compile(r"\b(last|past|this)\s+(week|month)\b", re.IGNORECASE)


@dataclass
class ParsedQuery:
    topic: str | None
    date_from: datetime | None
    date_to: datetime | None
    source: str = "local"


def _day_bounds(d: datetime) -> tuple[datetime, datetime]:
    start = datetime.combine(d.date(), time.min, tzinfo=d.tzinfo)
    end = datetime.combine(d.date(), time.max, tzinfo=d.tzinfo)
    return start, end


def _week_bounds(d: datetime) -> tuple[datetime, datetime]:
    """Monday through Sunday of the calendar week containing `d`."""
    monday = d - timedelta(days=d.weekday())
    start = datetime.combine(monday.date(), time.min, tzinfo=d.tzinfo)
    end = datetime.combine((monday + timedelta(days=6)).date(), time.max, tzinfo=d.tzinfo)
    return start, end


def _month_bounds(d: datetime) -> tuple[datetime, datetime]:
    """The 1st through the last day of the calendar month containing `d`."""
    first = d.replace(day=1)
    next_first = first.replace(year=first.year + 1, month=1) if first.month == 12 else first.replace(month=first.month + 1)
    start = datetime.combine(first.date(), time.min, tzinfo=d.tzinfo)
    end = datetime.combine((next_first - timedelta(days=1)).date(), time.max, tzinfo=d.tzinfo)
    return start, end


def _parse_range_phrase(query: str, local_now: datetime) -> tuple[datetime, datetime] | None:
    match = _RANGE_PHRASE.search(query)
    if not match:
        return None
    modifier, unit = match.group(1).lower(), match.group(2).lower()
    anchor = local_now
    if modifier in ("last", "past"):
        anchor = (local_now.replace(day=1) - timedelta(days=1)) if unit == "month" else local_now - timedelta(weeks=1)
    return _month_bounds(anchor) if unit == "month" else _week_bounds(anchor)


def parse_query_locally(query: str, local_now: datetime | None = None) -> ParsedQuery:
    """Splits `query` into a topic and an absolute date range, entirely offline.

    `local_now` anchors relative phrases ("3 days ago") to the agent's own clock,
    matching Technical_Blueprint.md's "resolved against the agent's local date and
    timezone so results near midnight are not off by a day."
    """
    local_now = local_now or datetime.now().astimezone()
    query = query.strip()
    if not query:
        return ParsedQuery(topic=None, date_from=None, date_to=None)

    date_from = date_to = None
    topic = query

    range_bounds = _parse_range_phrase(query, local_now)
    if range_bounds is not None:
        date_from, date_to = range_bounds
        topic = _RELATIVE_HINTS.sub("", query, count=1)
        topic = re.sub(r"\b(from|on|for)\b", "", topic, flags=re.IGNORECASE)
        topic = re.sub(r"\s+", " ", topic).strip(" ,.-") or None
        return ParsedQuery(topic=topic, date_from=date_from, date_to=date_to, source="local")

    settings = {
        "RELATIVE_BASE": local_now.replace(tzinfo=None),
        "PREFER_DATES_FROM": "past",
    }

    found = search_dates(query, settings=settings, languages=["en"])

    if found:
        matched_text, parsed_dt = found[0]
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=local_now.tzinfo)
        date_from, date_to = _day_bounds(parsed_dt)
        topic = _RELATIVE_HINTS.sub("", query, count=1)
        # search_dates can match a phrase the stripping regex doesn't cover ("from March");
        # whatever it matched must come out of the topic too.
        topic = re.sub(re.escape(matched_text), "", topic, count=1, flags=re.IGNORECASE)

    topic = re.sub(r"\b(from|on|for)\b", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip(" ,.-") or None

    return ParsedQuery(topic=topic, date_from=date_from, date_to=date_to, source="local")
