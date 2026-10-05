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
    r"last\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"this\s+(?:week|month)|"
    r"(?:on\s+)?\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?|"
    r"(?:on\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?"
    r")\b",
    re.IGNORECASE,
)


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

    settings = {
        "RELATIVE_BASE": local_now.replace(tzinfo=None),
        "PREFER_DATES_FROM": "past",
    }

    found = search_dates(query, settings=settings, languages=["en"])
    date_from = date_to = None
    topic = query

    if found:
        matched_text, parsed_dt = found[0]
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=local_now.tzinfo)
        date_from, date_to = _day_bounds(parsed_dt)
        topic = _RELATIVE_HINTS.sub("", query, count=1)
        if matched_text.lower() not in topic.lower():
            # search_dates matched a phrase our stripping regex doesn't fully cover;
            # fall back to removing the exact matched substring instead.
            topic = query.replace(matched_text, "", 1)

    topic = re.sub(r"\b(from|on|for)\b", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip(" ,.-") or None

    return ParsedQuery(topic=topic, date_from=date_from, date_to=date_to, source="local")
