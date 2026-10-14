"""Local deterministic query parser. Technical_Blueprint.md section 03: this is the
required baseline for local search — no network call, no API key. The central
/llm/query enhancement (when/if built) only ever replaces this result opportunistically;
it is never required for a local search to succeed.
"""
import calendar
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
    r"(?:on\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}\b(?:st|nd|rd|th)?(?:,?\s+\d{4})?"
    r")\b",
    re.IGNORECASE,
)

# "last week" / "this month" etc. name a *range*, not a single day — handled
# explicitly below instead of through dateparser, which was collapsing these to
# one anchor point (so "anything from last week" only ever matched whatever
# happened to fall on that one specific day, instead of the whole week).
_RANGE_PHRASE = re.compile(r"\b(last|past|this)\s+(week|month)\b", re.IGNORECASE)

# "2 months ago" / "3 weeks ago" are also ranges, not a single anchor day — same bug
# as _RANGE_PHRASE above, just with a number instead of last/past/this.
_N_UNITS_AGO = re.compile(r"\b(\d+)\s+(week|month)s?\s+ago\b", re.IGNORECASE)

_MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_WORD = (
    r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
    r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
# A month name with a specific day ("September 5", "on Mar 3rd") names one day, not a
# range — handled by the existing single-day path below, so _MONTH_RANGE must not also
# claim it.
_MONTH_DAY_SPECIFIC = re.compile(
    rf"(?:on\s+)?{_MONTH_WORD}\s+\d{{1,2}}\b(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?",
    re.IGNORECASE,
)
# A bare month name only reads as a date range ("notes from September", "September 2026")
# when it's clearly being used that way — after a preposition, or paired with a year.
# Without that guard, an ordinary word like "may" in running text ("documents that may
# need updating") would wrongly turn into a date filter.
_MONTH_AFTER_TRIGGER = re.compile(
    rf"\b(?:in|during|for|from)\s+{_MONTH_WORD}(?:\s+(\d{{4}}))?\b", re.IGNORECASE
)
_MONTH_WITH_YEAR = re.compile(rf"\b{_MONTH_WORD}\s+(\d{{4}})\b", re.IGNORECASE)
# The whole query being just a month name ("September", "September 2025") is
# unambiguous on its own — no trigger word needed, unlike a month name buried in a
# longer sentence where "may" etc. could just be an ordinary word.
_MONTH_WHOLE_QUERY = re.compile(rf"^\s*{_MONTH_WORD}(?:\s+(\d{{4}}))?\s*$", re.IGNORECASE)

# A query like "anything from last week" strips down to the literal word "anything"
# as the topic, which then gets embedded and searched for — instead of being
# recognized as a placeholder meaning "no topic, just list by date" (Technical_
# Blueprint.md section 04: null topic with dates means list by recency).
_GENERIC_TOPIC = re.compile(
    r"^(?:any|every|some|all|my)?\s*(?:thing|file|document|stuff)s?$", re.IGNORECASE
)


def _drop_if_generic(topic: str | None) -> str | None:
    if topic and _GENERIC_TOPIC.match(topic):
        return None
    return topic


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


def _add_months(d: datetime, delta: int) -> datetime:
    month_index = d.month - 1 + delta
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def _parse_n_units_ago(query: str, local_now: datetime) -> tuple[datetime, datetime] | None:
    match = _N_UNITS_AGO.search(query)
    if not match:
        return None
    n, unit = int(match.group(1)), match.group(2).lower()
    if unit == "month":
        return _month_bounds(_add_months(local_now, -n))
    return _week_bounds(local_now - timedelta(weeks=n))


def _parse_month_only(query: str, local_now: datetime) -> tuple[tuple[datetime, datetime], re.Match] | None:
    """A bare month name ('September', 'in September', 'September 2026') names a
    whole calendar month, not one day — same bug as _parse_range_phrase, just for an
    explicit month instead of a relative one.
    """
    if _MONTH_DAY_SPECIFIC.search(query):
        return None
    match = (
        _MONTH_WHOLE_QUERY.match(query)
        or _MONTH_AFTER_TRIGGER.search(query)
        or _MONTH_WITH_YEAR.search(query)
    )
    if not match:
        return None
    month = _MONTH_NAMES[match.group(1)[:3].lower()]
    year = int(match.group(2)) if match.group(2) else local_now.year
    anchor = local_now.replace(year=year, month=month, day=1)
    return _month_bounds(anchor), match


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
        topic = _drop_if_generic(topic)
        return ParsedQuery(topic=topic, date_from=date_from, date_to=date_to, source="local")

    n_units_bounds = _parse_n_units_ago(query, local_now)
    if n_units_bounds is not None:
        date_from, date_to = n_units_bounds
        topic = _RELATIVE_HINTS.sub("", query, count=1)
        topic = re.sub(r"\b(from|on|for)\b", "", topic, flags=re.IGNORECASE)
        topic = re.sub(r"\s+", " ", topic).strip(" ,.-") or None
        topic = _drop_if_generic(topic)
        return ParsedQuery(topic=topic, date_from=date_from, date_to=date_to, source="local")

    month_only = _parse_month_only(query, local_now)
    if month_only is not None:
        (date_from, date_to), match = month_only
        topic = query[: match.start()] + query[match.end():]
        topic = re.sub(r"\b(from|on|for|in|during)\b", "", topic, flags=re.IGNORECASE)
        topic = re.sub(r"\s+", " ", topic).strip(" ,.-") or None
        topic = _drop_if_generic(topic)
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
    topic = _drop_if_generic(topic)

    return ParsedQuery(topic=topic, date_from=date_from, date_to=date_to, source="local")
