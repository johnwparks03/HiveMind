"""Shared facts and timeline for the fictional Falcon demo data.

Every content module imports from here, so a changed value changes everywhere.
All content is fictional. Dates follow the timeline spine in the demo plan.
"""

from datetime import date, timedelta

FIRM = "the firm"
CLIENT = "Brightwater Logistics"
PROJECT = "Falcon"
PLATFORM = "Harborview Platform"

# ---- Contract and budget facts ---------------------------------------------
MSA_SIGNED = "6 October 2025"
SOW1_VALUE = "$31,500"
SOW1_SIGNED = "12 February 2026"
PHASE1_KICKOFF = "2 March 2026"
CO01_AMOUNT = "$6,800"
CO01_DATE = "11 May 2026"
PHASE1_TOTAL = "$38,300"          # SOW1_VALUE + CO01_AMOUNT
CO02_DATE = "3 August 2026"
PHASE1_END = "7 August 2026"
PHASE1_READOUT = "12 August 2026"
BRIDGE_PERIOD = "Sprints 9 to 11 (10 August to 18 September 2026)"
STEERING_JUNE = "15 June 2026"

APPROVAL_DATE = "14 September 2026"
PHASE2_BUDGET = "$48,200"
PHASE2_KICKOFF = "21 September 2026"
PHASE2_SPLIT = {
    "Engineering": 26400,
    "Data": 9800,
    "Design": 5200,
    "Project management": 4300,
    "Quality assurance": 2500,
}   # sums to 48,200


def money(amount):
    return f"${amount:,}"


# ---- Delivery facts ----------------------------------------------------------
SPRINT_14_GOAL = "pilot Ask for two teams"
CUTOVER = "2 November 2026"
QUALITY_THRESHOLD = "98.5 percent"
QUALITY_AGREED = "29 September 2026"
ASK_TARGET = "4 seconds"
PILOT_WINDOW = "9 to 27 November 2026"

# ---- Private facts (User 1 only; never in a public file) ----------------------
PILOT_BUDGET = "$22,000"
PILOT_GO_LIVE = "15 December 2026"
EXPENSE_THRESHOLD = "$500"

# ---- Sprint calendar ------------------------------------------------------------
SPRINT_1_START = date(2026, 4, 20)   # Monday; two-week sprints, no gaps


def long_date(day):
    return f"{day.day} {day.strftime('%B %Y')}"


def sprint_start(number):
    return SPRINT_1_START + timedelta(days=14 * (number - 1))


def sprint_end(number):
    """Friday of the second week."""
    return sprint_start(number) + timedelta(days=11)


def sprint_text(number):
    """For example 'Sprint 14: 19 to 30 October 2026'."""
    start, end = sprint_start(number), sprint_end(number)
    if start.month == end.month:
        span = f"{start.day} to {end.day} {end.strftime('%B %Y')}"
    else:
        span = f"{start.day} {start.strftime('%B')} to {long_date(end)}"
    return f"Sprint {number}: {span}"


# ---- Roles (fictional; no real people) ------------------------------------------
ROLE_SPONSOR = "Executive sponsor"
ROLE_PROJECT_LEAD = "Project lead (User 1)"
ROLE_DELIVERY_LEAD = "Delivery lead (User 2)"
ROLE_CLIENT_SPONSOR = "Client sponsor"
ROLE_CLIENT_DELIVERY = "Client delivery lead"
ROLE_FINANCE = "Finance business partner"

# Strings that only User 2's files may contain (teammate-only demo answers).
TEAMMATE_ONLY_TOKENS = [
    "$26,400", "$9,800", "$5,200", "$4,300", "$2,500",
    "2 November 2026", "2 Nov 2026", "98.5", "4 seconds",
]

# Strings that only User 1's private files may contain.
PRIVATE_ONLY_TOKENS = ["$22,000", "15 December 2026", "Knowledge Reuse"]

# Phrases that contradict the timeline and must never appear.
FORBIDDEN_PHRASES = [
    "Sprint 13 closed",
    "28 September 2026 kickoff",
    "kickoff on 28 September",
    "14 June 2026",
]
