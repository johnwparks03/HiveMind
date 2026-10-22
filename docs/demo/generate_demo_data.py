"""Generate the fictional HiveMind demo files for the three demo users.

Usage:
    python generate_demo_data.py [output_root]

Default output root: <home>\\Documents\\HiveMind Demo (outside the repo).
Requires: python-docx, python-pptx, fpdf2.

Every planted fact and date lives in the constants and FILES tables below.
Re-running overwrites the demo files with the same content.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Pt, RGBColor
from fpdf import FPDF
from pptx import Presentation
from pptx.dml.color import RGBColor as PptxRGB
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt as PptxPt

# Deloitte brand palette (deloitte-brand skill, colors-typography reference)
GREEN = "86BC25"
NEON = "86EB22"
DARK = "282728"
BLACK = "000000"
WHITE = "FFFFFF"
HEADLINE_FONT = "Open Sans"
ACCENT_FONT = "Stix Two Text"

# Planted facts. Change a value here and every document that uses it changes.
FALCON_BUDGET = "$48,200"
FALCON_APPROVED = "14 September 2026"
SPRINT_14 = "19 to 30 October 2026"
CUTOVER_DATE = "2 November 2026"
QUALITY_THRESHOLD = "98.5 percent"
QUALITY_MEETING = "8 October 2026"
ASK_TARGET = "4 seconds"
PILOT_BUDGET = "$22,000"
PILOT_GO_LIVE = "15 December 2026"
EXPENSE_THRESHOLD = "$500"

# Each entry: path under the output root, created and revised dates (YYYY-MM-DD),
# the author label used in file metadata, and the content.
# Docx and PDF use "blocks"; PPTX uses "slides"; TXT uses "text".
FILES = [
    # ---- User 1, public: Falcon Phase 2 ------------------------------------
    {
        "path": "User1/Public/Projects/Falcon Phase 2/Falcon Steering Committee Minutes 2026-09-14.docx",
        "title": "Falcon Steering Committee Minutes 2026-09-14",
        "author": "User 1",
        "created": "2026-09-14",
        "revised": "2026-09-14",
        "blocks": [
            ("h1", "Falcon Steering Committee Minutes - 14 September 2026"),
            ("p", f"The steering committee met on 14 September 2026 to review Phase 2 scope, timeline and budget for the Falcon project. The committee approved the Phase 2 budget of {FALCON_BUDGET} and set the kickoff for 28 September 2026."),
            ("h2", "Attendees"),
            ("bullets", ["Executive sponsor (chair)", "Project lead (User 1, minutes)", "Finance business partner", "Client delivery lead", "Data Platform lead", "Frontend lead"]),
            ("h2", "Decisions"),
            ("bullets", [
                f"Phase 2 budget approved at {FALCON_BUDGET} (approved {FALCON_APPROVED})",
                "Phase 2 scope limited to the search and Ask pilot for two teams",
                "Harborview Platform sprint cadence stays at two weeks",
                "Monthly steering review moves to the first Monday of each month",
            ]),
            ("h2", "Discussion"),
            ("p", "Finance asked for a contingency line. The committee agreed that 5 percent is held outside the approved budget and released only by the sponsor."),
            ("p", "The client delivery lead raised a risk that stakeholder sign-off on the discovery pack may slip past 30 September. Mitigation: a shortened review with two reviewers."),
            ("h2", "Actions"),
            ("table", ["Action", "Owner", "Due"], [
                ["Circulate revised Phase 2 plan", "Project lead", "25 Sep 2026"],
                ["Confirm contingency release process", "Finance business partner", "25 Sep 2026"],
                ["Book kickoff room and dial-in", "Project lead", "28 Sep 2026"],
            ], [0.5, 0.3, 0.2]),
        ],
    },
    {
        "path": "User1/Public/Projects/Falcon Phase 2/Falcon Phase 2 Kickoff.pptx",
        "title": "Falcon Phase 2 Kickoff",
        "author": "User 1",
        "created": "2026-08-28",
        "revised": "2026-09-15",
        "slides": [
            {"title": "Falcon Phase 2 Kickoff", "subtitle": "Scope, timeline and budget - draft for steering review, revised 15 September 2026"},
            {"title": "Objectives", "bullets": [
                "Extend the search and Ask pilot to two delivery teams",
                f"Hold the Phase 2 budget at {FALCON_BUDGET}, approved {FALCON_APPROVED}",
                f"Deliver a working pilot for the sprint review on 30 October 2026",
                "Capture adoption and time-saved measures for the steering committee",
            ]},
            {"title": "Scope", "bullets": [
                "In: teammate-visible document search and Ask for two teams",
                "In: onboarding guide and runbook indexing",
                "Out: client-facing document sharing",
                "Out: integration with the document management system",
            ]},
            {"title": "Timeline", "bullets": [
                "Discovery complete: 4 September 2026",
                f"Phase 2 build: 28 September to 30 October 2026 (Sprint 14)",
                "Pilot with two teams: 9 to 27 November 2026",
                "Steering review: first Monday of each month",
            ]},
            {"title": "Budget summary", "bullets": [
                f"Approved Phase 2 budget: {FALCON_BUDGET}",
                "Contingency: 5 percent, held by the sponsor",
                "Largest cost: delivery team time, about 70 percent",
            ]},
            {"title": "Team roles", "bullets": [
                "Executive sponsor - steering chair",
                "Project lead - User 1",
                "Data Platform lead - User 2",
                "Frontend lead - User 3",
                "Finance business partner - budget control",
            ]},
            {"title": "Risks", "bullets": [
                "Sign-off on the discovery pack could slip",
                "Teammate uploads depend on laptops being online",
                "Two-person pilot needs both agents running",
            ]},
            {"title": "Next steps", "bullets": [
                "Confirm pilot teams by 25 September 2026",
                "Approve the kickoff agenda",
                "Schedule the monthly steering review",
            ]},
        ],
    },
    # ---- User 1, public: Harborview sprint and team ------------------------
    {
        "path": "User1/Public/Projects/Harborview Platform/Sprints/Harborview Platform - Sprint 14 Planning.docx",
        "title": "Harborview Platform - Sprint 14 Planning",
        "author": "User 1",
        "created": "2026-10-16",
        "revised": "2026-10-20",
        "blocks": [
            ("h1", "Harborview Platform - Sprint 14 Planning"),
            ("p", f"Sprint 14 runs {SPRINT_14}. The sprint goal is to pilot Ask for two teams, with teammate-visible answers working end to end on dev."),
            ("h2", "Sprint goal"),
            ("p", "Pilot Ask for two teams: a teammate's public files can answer a question, with the source and download working on the Ask page."),
            ("h2", "Capacity"),
            ("p", "Capacity is 42 points across the three streams (project lead, Data Platform, Frontend). Two members are on part-time availability in the week of 26 October."),
            ("h2", "Stories"),
            ("table", ["ID", "Story", "Owner", "Points"], [
                ["HM-214", "Publish public files and report chunk status", "Platform", "5"],
                ["HM-215", "Ask: teammate sources with download control", "Frontend", "8"],
                ["HM-216", "Retrieval search with query vector only", "Platform", "5"],
                ["HM-217", "Agent chunk upload retry and batch size", "Platform", "3"],
                ["HM-218", "Ask panel source chips and teammate label", "Frontend", "3"],
                ["HM-219", "Pilot runbook and two-person check", "Project lead", "2"],
                ["HM-220", "Dev smoke tests for search and Ask", "Data Platform", "5"],
                ["HM-221", "Empty-state copy for no matches", "Frontend", "1"],
            ], [0.12, 0.56, 0.2, 0.12]),
            ("p", "Committed 32 of 42 points. The rest is held for support and the cutover dependency."),
            ("h2", "Dependencies"),
            ("bullets", [
                f"Data cutover to the new warehouse on {CUTOVER_DATE} (Data Platform). Sprint 14 avoids schema changes.",
                "Ask panel design sign-off (Frontend, see Design Review - Ask Panel).",
            ]),
            ("h2", "Risks"),
            ("bullets", [
                "Embedding model download on fresh laptops can be slow; pre-cache on the pilot machines.",
                "Bedrock throughput limits during the pilot; keep question volume low for the demo.",
            ]),
            ("h2", "Sprint review"),
            ("p", f"Sprint review is 30 October 2026 at 14:00, with the steering sponsor invited."),
        ],
    },
    # ---- User 1, public: team --------------------------------------------
    {
        "path": "User1/Public/Team/Team Working Agreement.docx",
        "title": "Team Working Agreement",
        "author": "User 1",
        "created": "2026-01-12",
        "revised": "2026-08-03",
        "blocks": [
            ("h1", "Team Working Agreement"),
            ("p", "This agreement sets how the HiveMind team works together across all three streams. It is reviewed each quarter. Last revised 3 August 2026."),
            ("h2", "Meetings"),
            ("bullets", [
                "Daily stand-up at 09:15, 10 minutes, camera optional",
                "Sprint planning on day one of each sprint, two hours",
                "Sprint review and retrospective on the last day, 60 minutes each",
                "Weekly status notes posted to the team folder by Friday 12:00",
            ]),
            ("h2", "Definition of done"),
            ("bullets", [
                "Acceptance criteria ticked in the story file",
                "Tests added or updated and passing",
                "Frontend lint and build clean",
                "Demo-ready on the dev environment",
            ]),
            ("h2", "On-call"),
            ("p", "The on-call rota covers the pilot weeks. Contact the on-call engineer through the team channel first, then by phone. Ingest alerts follow the Nightly Ingest Runbook."),
            ("h2", "Working norms"),
            ("bullets", [
                "Write decisions into the minutes, not into chat only",
                "Raise blockers the same day",
                "Do not put client or personal data in shared content",
            ]),
            ("h2", "Revision history"),
            ("table", ["Date", "Change"], [
                ["12 Jan 2026", "First version"],
                ["14 Apr 2026", "Added on-call rota"],
                ["3 Aug 2026", "Definition of done updated for frontend"],
            ], [0.3, 0.7]),
        ],
    },
    {
        "path": "User1/Public/Team/Weekly Status Notes - October 2026.txt",
        "title": "Weekly Status Notes - October 2026",
        "author": "User 1",
        "created": "2026-09-28",
        "revised": "2026-10-16",
        "text": """WEEKLY STATUS NOTES - OCTOBER 2026
Owner: project lead (User 1)
Covers: 28 September to 16 October 2026
Format: one entry per week, newest at the bottom.

2026-09-28
 - Falcon Phase 2 plan revised after the 14 September steering committee; budget {budget} held.
 - Harborview: Sprint 13 closed with 36 of 38 points done.
 - Data Platform reports the warehouse cutover is on track for {cutover}.

2026-10-05
 - Ask pilot dry run with two laptops. Teammate source showed correctly; download blocked while the owner was offline (expected).
 - Sprint 14 planning booked for 19 October.
 - Frontend asked for a design review of the Ask panel, scheduled for 7 October.

2026-10-12
 - Ask panel design review done. Decisions: teammate label on every teammate source, download stays on the source chip.
 - Data Quality Review held {quality_meeting}: {threshold} threshold agreed for row-level checks.
 - Risk: embedding model download on new laptops. Pre-cache planned.

2026-10-16
 - Sprint 14 plan drafted: 32 of 42 points committed.
 - Pilot teams confirmed; the two teams start on 9 November 2026.
 - Weekly notes due Friday; this entry posted Friday 16 October.
""".format(budget=FALCON_BUDGET, cutover=CUTOVER_DATE, quality_meeting=QUALITY_MEETING, threshold=QUALITY_THRESHOLD),
    },
    {
        "path": "User1/Public/Team/Onboarding Guide - Harborview.pdf",
        "title": "Onboarding Guide - Harborview",
        "author": "User 1",
        "created": "2025-11-04",
        "revised": "2026-03-20",
        "blocks": [
            ("h1", "Onboarding Guide - Harborview"),
            ("p", "Welcome to the Harborview Platform team. This guide gets a new laptop ready for the agent, the frontend and the central tests. Revised 20 March 2026; some steps may have changed since."),
            ("h2", "Before you start"),
            ("bullets", [
                "Windows 11 laptop with rights to install software",
                "Git, Python 3.11 or later, Node.js 20 LTS",
                "Access to the team folder and the HiveMind team invite code",
            ]),
            ("h2", "Set up the agent"),
            ("bullets", [
                "Clone the repository and open a terminal in the agent folder",
                "Create the virtual environment and install the requirements",
                "Copy the example env file and fill in the Cognito client id and central API URL",
                "Start the agent on 127.0.0.1, port 8420",
            ]),
            ("h2", "Set up the frontend"),
            ("bullets", [
                "Open a terminal in the frontend folder and run npm install",
                "Run npm run dev and open http://localhost:5173",
            ]),
            ("h2", "First run"),
            ("p", "The first real search downloads the embedding model. This needs normal internet access once; after that it is cached."),
            ("h2", "Who to ask"),
            ("table", ["Topic", "Ask"], [
                ["Agent setup", "Platform engineer on rota"],
                ["Frontend", "Frontend lead"],
                ["Access and invites", "Project lead"],
            ], [0.4, 0.6]),
        ],
    },
    # ---- User 1, private: initiative --------------------------------------
    {
        "path": "User1/Private/Initiatives/Knowledge Reuse Pilot/Knowledge Reuse Pilot - Initiative Charter.docx",
        "title": "Knowledge Reuse Pilot - Initiative Charter",
        "author": "User 1",
        "created": "2026-07-06",
        "revised": "2026-10-10",
        "blocks": [
            ("h1", "Knowledge Reuse Pilot - Initiative Charter"),
            ("p", "Owner: User 1. Status: draft, revised 10 October 2026. Private working copy, not shared with the team."),
            ("h2", "Problem"),
            ("p", "Staff repeat searches for documents their colleagues already hold. Public files exist but are hard to find across teams."),
            ("h2", "Proposed pilot"),
            ("p", "Use HiveMind teammate search and Ask with two delivery teams, for four weeks after go-live."),
            ("h2", "Budget and timeline"),
            ("table", ["Item", "Amount or date"], [
                ["Pilot budget request", PILOT_BUDGET],
                ["Build time", "$12,000"],
                ["Hosting", "$4,000"],
                ["Support", "$6,000"],
                ["Go-live target", PILOT_GO_LIVE],
            ], [0.6, 0.4]),
            ("h2", "Success measures"),
            ("bullets", [
                "At least 50 percent of pilot users ask a question each week",
                "Median time saved reported at 3 hours per person per month",
            ]),
            ("h2", "Governance"),
            ("p", "Sponsor: executive sponsor from the Falcon steering committee. Reviewed monthly, alongside the steering review."),
            ("h2", "Open items"),
            ("bullets", [
                "Confirm pilot teams by 25 November 2026",
                "Agree data-handling sign-off with information security",
            ]),
        ],
    },
    {
        "path": "User1/Private/Initiatives/Knowledge Reuse Pilot/Knowledge Reuse Pilot - Business Case.pptx",
        "title": "Knowledge Reuse Pilot - Business Case",
        "author": "User 1",
        "created": "2026-09-29",
        "revised": "2026-09-29",
        "slides": [
            {"title": "Knowledge Reuse Pilot - Business Case", "subtitle": "FY27 - draft 29 September 2026 - private working copy"},
            {"title": "Problem", "bullets": [
                "Staff repeat searches for project documents",
                "Teams cannot see each other's public files today",
            ]},
            {"title": "Proposed pilot", "bullets": [
                f"Go-live target: {PILOT_GO_LIVE}",
                "Two teams, four weeks of measurement after go-live",
            ]},
            {"title": "Cost", "bullets": [
                f"Pilot request: {PILOT_BUDGET}",
                "Build time $12,000, hosting $4,000, support $6,000",
            ]},
            {"title": "Benefit", "bullets": [
                "Estimated 3 hours per person per month saved",
                "Break-even about 7 months at 14 pilot users, at $75 per hour",
            ]},
            {"title": "Risks", "bullets": [
                "Adoption falls below 50 percent of pilot users",
                "Data handling rules limit what teammates can share",
            ]},
            {"title": "Decisions asked", "bullets": [
                f"Approve the {PILOT_BUDGET} pilot budget",
                f"Confirm the {PILOT_GO_LIVE} go-live",
            ]},
        ],
    },
    # ---- User 1, private: performance ------------------------------------
    {
        "path": "User1/Private/Performance/2026 H2 Review/H2 2026 Self-Review - Draft.docx",
        "title": "H2 2026 Self-Review - Draft",
        "author": "User 1",
        "created": "2026-10-19",
        "revised": "2026-10-21",
        "blocks": [
            ("h1", "H2 2026 Self-Review - Draft"),
            ("p", "Covers July to October 2026. Draft for discussion at the year-end review. Last edited 21 October 2026."),
            ("h2", "Achievements"),
            ("bullets", [
                f"Led Falcon Phase 2 scope and budget through the steering committee on {FALCON_APPROVED}, approved at {FALCON_BUDGET}",
                "Ran the Harborview search and Ask pilot plan; Sprint 14 committed at 32 of 42 points",
                "Brought the Ask design review to a decision in October 2026",
                "Proposed the Knowledge Reuse Pilot and started the initiative charter",
            ]),
            ("h2", "Goals - progress"),
            ("table", ["Goal", "Status", "Evidence"], [
                ["Pilot Ask for two teams", "On track", "Sprint 14 goal, review 30 Oct"],
                ["Falcon Phase 2 plan", "Done", "Steering minutes 14 Sep"],
                ["Initiative charter", "In progress", "Revised 10 Oct 2026"],
            ], [0.4, 0.2, 0.4]),
            ("h2", "Development areas"),
            ("bullets", [
                "Delegation: hand over more facilitation to team members",
                "Written decisions: close actions in the minutes within 24 hours",
            ]),
            ("h2", "Looking ahead"),
            ("p", "Finish the initiative business case and charter before the end of the year. Build a short usability check with five staff before the pilot."),
        ],
    },
    {
        "path": "User1/Private/Performance/Tracker/Performance Review Tracker 2026.txt",
        "title": "Performance Review Tracker 2026",
        "author": "User 1",
        "created": "2026-01-05",
        "revised": "2026-10-18",
        "text": f"""PERFORMANCE REVIEW TRACKER 2026
Owner: User 1 (private)
Purpose: dated log of check-ins, goals and feedback for the 2026 cycle. Keep entries factual.

Goals for 2026
 G1 - Lead the Harborview search and Ask pilot to a working demo (in progress)
 G2 - Build the delivery plan for Falcon Phase 2 (on track)
 G3 - Complete firm data-handling training (done 2026-03-12)

Entries
2026-01-05 - Goal setting with manager. Agreed G1 to G3.
2026-02-18 - Weekly 1:1 notes. Asked for earlier steering access.
2026-03-12 - Completed data-handling training.
2026-04-08 - Mid-year feedback (manager): clear communication with stakeholders; develop delegation.
2026-05-20 - Handed sprint review facilitation to a team member. Went well.
2026-07-22 - Check-in: Falcon Phase 2 scope agreed in principle.
2026-08-14 - Feedback from delivery lead: strong on risk handling in steering.
2026-09-14 - Steering committee approved the Phase 2 budget (see Falcon minutes).
2026-10-02 - Self-note: finish the initiative business case before year end.
2026-10-18 - Progress update to manager: pilot on track for the 30 October sprint review.
""",
    },
    # ---- User 1, private: firm documentation ----------------------------
    {
        "path": "User1/Private/Firm/Policies/Expense Policy Summary FY27.pdf",
        "title": "Expense Policy Summary FY27",
        "author": "Firm Finance",
        "created": "2026-06-15",
        "revised": "2026-06-15",
        "blocks": [
            ("h1", "Expense Policy Summary - FY27"),
            ("p", "Effective 1 July 2026. Applies to all staff. This summary does not replace the full policy on the intranet. Prepared 15 June 2026."),
            ("h2", "Pre-approval"),
            ("bullets", [
                f"Spend above {EXPENSE_THRESHOLD} needs manager pre-approval before the purchase",
                f"Client-billable travel above {EXPENSE_THRESHOLD} also needs the engagement lead's approval",
            ]),
            ("h2", "Receipts"),
            ("bullets", [
                "Keep itemised receipts for any single item over $25",
                "Missing receipts need a signed declaration, limited to three per quarter",
            ]),
            ("h2", "Submission"),
            ("bullets", [
                "Submit within 30 days of the expense date",
                "Claims over 90 days old are not reimbursed without a finance exception",
            ]),
            ("h2", "Corporate cards"),
            ("p", "Corporate cards are for approved travel and client costs only. Personal purchases must be repaid within 14 days."),
            ("h2", "Contacts"),
            ("p", "Finance operations mailbox for queries. Exceptions go to the finance business partner."),
        ],
    },
    {
        "path": "User1/Private/Firm/Policies/Travel and Expenses Guide FY27.pdf",
        "title": "Travel and Expenses Guide FY27",
        "author": "Firm Finance",
        "created": "2026-06-15",
        "revised": "2026-07-01",
        "blocks": [
            ("h1", "Travel and Expenses Guide - FY27"),
            ("p", "Effective 1 July 2026. Covers booking, mileage and daily allowances for domestic travel. Revised 1 July 2026 for the new mileage rate."),
            ("h2", "Booking"),
            ("bullets", [
                "Book through the travel desk for flights over four hours",
                "Economy for flights under six hours; premium economy by exception",
                "Hotels from the preferred list where possible",
            ]),
            ("h2", "Mileage"),
            ("p", "Personal car mileage is reimbursed at $0.70 per mile from 1 July 2026. Log start point, end point and purpose."),
            ("h2", "Daily allowance"),
            ("table", ["Location type", "Meals per day"], [
                ["Standard city", "$55"],
                ["High-cost city", "$75"],
                ["Client site (own meals not claimed)", "$0"],
            ], [0.6, 0.4]),
            ("h2", "Rail and taxi"),
            ("bullets", [
                "Rail in standard class unless travelling with a client",
                "Taxis for airport transfers after 21:00 or with heavy luggage",
            ]),
        ],
    },
    {
        "path": "User1/Private/Firm/Policies/Client Confidentiality Reminder.txt",
        "title": "Client Confidentiality Reminder",
        "author": "Firm Information Security",
        "created": "2025-12-01",
        "revised": "2025-12-01",
        "text": """CLIENT CONFIDENTIALITY REMINDER
Issued 1 December 2025. Applies to all staff.

 - Do not store client documents in personal folders outside the firm's approved sites.
 - Mark client material "Confidential" in the file name when it leaves the engagement team.
 - Do not paste client names or figures into public AI tools.
 - Share with teammates only on the engagement's approved list.
 - Report possible data exposure to the information security team within 24 hours.

Questions: information security team.
""",
    },
    {
        "path": "User1/Private/Firm/Calendar/Practice Holiday Calendar 2027.txt",
        "title": "Practice Holiday Calendar 2027",
        "author": "Firm Operations",
        "created": "2026-10-01",
        "revised": "2026-10-01",
        "text": """PRACTICE HOLIDAY CALENDAR 2027
Published 1 October 2026. Office closed on the dates below.

1 January 2027 - New Year's Day
18 January 2027 - Martin Luther King Jr. Day
15 February 2027 - Presidents' Day
31 May 2027 - Memorial Day
5 July 2027 - Independence Day (observed)
6 September 2027 - Labor Day
25 November 2027 - Thanksgiving Day
26 November 2027 - Floating day (to be confirmed by team lead)
24 December 2027 - Christmas Day (observed)
""",
    },
    # ---- User 2, public: Data Platform -----------------------------------
    {
        "path": "User2/Public/Data Platform/Sprints/Data Platform - Sprint 14 Stories.docx",
        "title": "Data Platform - Sprint 14 Stories",
        "author": "User 2",
        "created": "2026-10-15",
        "revised": "2026-10-19",
        "blocks": [
            ("h1", "Data Platform - Sprint 14 Stories"),
            ("p", f"Sprint 14 for the Data Platform stream, {SPRINT_14}. The stories support the quality gate and the warehouse cutover on {CUTOVER_DATE}."),
            ("table", ["ID", "Story", "Points"], [
                ["DP-41", f"Threshold check in nightly job ({QUALITY_THRESHOLD})", "5"],
                ["DP-42", "Hold rejected feeds in staging", "3"],
                ["DP-43", "Fixed time zone for two source date fields", "3"],
                ["DP-44", "Parallel run comparison report", "5"],
                ["DP-45", "Update runbook alerts for cutover", "2"],
            ], [0.15, 0.7, 0.15]),
            ("p", "Committed 18 points. Capacity is 21 points after support time."),
            ("h2", "Dependencies"),
            ("bullets", [
                "DP-43 depends on source owners replying by 16 October 2026",
                "DP-44 needs the cutover window agreed with finance",
            ]),
            ("h2", "Definition of done"),
            ("bullets", [
                "Runbook updated",
                "Quality report reviewed by the data steward",
            ]),
        ],
    },
    {
        "path": "User2/Public/Data Platform/Quality/Data Quality Review 2026-10-08.docx",
        "title": "Data Quality Review 2026-10-08",
        "author": "User 2",
        "created": "2026-10-09",
        "revised": "2026-10-09",
        "blocks": [
            ("h1", f"Data Quality Review - {QUALITY_MEETING}"),
            ("p", f"Meeting held {QUALITY_MEETING} to review September row-level checks on the ingest feeds. Notes written by User 2 on 9 October 2026."),
            ("h2", "Attendees"),
            ("bullets", [
                "Data Platform lead (chair, User 2)",
                "Source system analyst",
                "Finance data steward",
                "Project lead (User 1), observing",
            ]),
            ("h2", "Findings"),
            ("bullets", [
                "September ingest had 1.4 percent of rows rejected by schema checks, mainly on a date field from one source",
                "Duplicate keys fell after the key change in August",
                "Two sources still send dates without a time zone",
            ]),
            ("h2", "Decisions"),
            ("bullets", [
                f"Quality threshold set at {QUALITY_THRESHOLD} of rows passing row-level checks before a feed is loaded",
                "Feeds below the threshold are held in staging, not dropped",
                f"Date fields from the two sources are cast with a fixed time zone from 1 November 2026",
            ]),
            ("p", f"The {QUALITY_THRESHOLD} threshold applies from the first night of October data onward."),
            ("h2", "Actions"),
            ("table", ["Action", "Owner", "Due"], [
                ["Add threshold check to nightly job", "Data Platform", "23 Oct 2026"],
                ["Contact the two sources about time zones", "Source analyst", "16 Oct 2026"],
                ["Share September rejection report", "Finance data steward", "12 Oct 2026"],
            ], [0.5, 0.3, 0.2]),
        ],
    },
    {
        "path": "User2/Public/Data Platform/Roadmap/Data Platform Roadmap Q4 2026.pptx",
        "title": "Data Platform Roadmap Q4 2026",
        "author": "User 2",
        "created": "2026-10-02",
        "revised": "2026-10-14",
        "slides": [
            {"title": "Data Platform Roadmap Q4 2026", "subtitle": "October to December 2026 - revised 14 October 2026"},
            {"title": "Priorities", "bullets": [
                f"Warehouse cutover on {CUTOVER_DATE}",
                f"Row-level quality gate live from October ({QUALITY_THRESHOLD})",
                "Retire the legacy staging job by December",
            ]},
            {"title": "Milestones", "bullets": [
                "2 October: quality gate design signed off",
                f"{CUTOVER_DATE}: warehouse cutover",
                "16 November: parallel run closed",
                "11 December: legacy staging job retired",
            ]},
            {"title": "Dependencies", "bullets": [
                "Frontend teammate search needs stable metadata from the warehouse",
                "Source time-zone fixes due before 1 November 2026",
                "Finance reporting moves after cutover",
            ]},
            {"title": "Capacity", "bullets": [
                "Two engineers on cutover, one on the quality gate",
                "Support rota held through the pilot weeks",
            ]},
            {"title": "Risks", "bullets": [
                "Source delays push the cutover date",
                "Parallel run doubles compute cost for two weeks",
            ]},
            {"title": "Asks", "bullets": [
                "Confirm the cutover window with finance by 23 October 2026",
                "Approve the parallel run budget",
            ]},
        ],
    },
    {
        "path": "User2/Public/Data Platform/Runbooks/Nightly Ingest Runbook.pdf",
        "title": "Nightly Ingest Runbook",
        "author": "User 2",
        "created": "2025-06-17",
        "revised": "2026-07-30",
        "blocks": [
            ("h1", "Nightly Ingest Runbook"),
            ("p", "Owner: Data Platform team. Applies to the nightly ingest job that loads source extracts into the warehouse staging area. Revised 30 July 2026."),
            ("h2", "Schedule"),
            ("p", "The job starts at 01:30 and should finish before 03:00. Completion is confirmed by the status file in the staging bucket."),
            ("h2", "Normal run checklist"),
            ("bullets", [
                "Confirm the job started in the scheduler log",
                "Check row counts against the previous night (within 2 percent)",
                "Confirm the status file is written",
                "Record the run in the ops log",
            ]),
            ("h2", "Alerts"),
            ("table", ["Alert", "Meaning", "First action"], [
                ["INGEST-ALERT-01", "Row count dropped over 5%", "Check the source extract, re-run once"],
                ["INGEST-ALERT-02", "Job not done by 03:00", "Page on-call; wait before re-running"],
                ["INGEST-ALERT-03", "Status file missing", "Check permissions on staging prefix"],
            ], [0.25, 0.35, 0.4]),
            ("h2", "Escalation"),
            ("p", "Page the Data Platform on-call engineer. If there is no response in 20 minutes, contact the Data Platform lead. Do not contact source system owners at night unless the on-call engineer asks."),
            ("h2", "Cutover note"),
            ("p", f"Before the warehouse cutover on {CUTOVER_DATE}, the nightly job runs in parallel with the new warehouse. Keep these steps unchanged until the cutover is signed off."),
        ],
    },
    {
        "path": "User2/Public/Data Platform/Research/Vendor Evaluation - Vector Store.txt",
        "title": "Vendor Evaluation - Vector Store",
        "author": "User 2",
        "created": "2026-05-11",
        "revised": "2026-05-11",
        "text": """VECTOR STORE - VENDOR EVALUATION (April to May 2026)
Author: Data Platform (User 2)
Status: draft, not revisited since May 2026.

Options considered:
 A. Managed vector index (separate service)
 B. Vector extension on the existing Postgres cluster
 C. Local index inside the local agent

Criteria: cost at expected chunk volume, operations effort, query latency,
data residency, team skills.

Notes:
 - Option A: fast, but adds a second store to keep in sync with file deletes.
 - Option B: keeps file deletes in one transaction through foreign keys; needs a version check on the extension.
 - Option C: good for the agent, not useful for teammate search across laptops.

Leaning: Option B. Decision not recorded. Revisit before the Phase 2 build.
""",
    },
    # ---- User 3, public: Frontend and UX ---------------------------------
    {
        "path": "User3/Public/Frontend/Sprints/Sprint 14 - Frontend and UX Plan.docx",
        "title": "Sprint 14 - Frontend and UX Plan",
        "author": "User 3",
        "created": "2026-10-14",
        "revised": "2026-10-17",
        "blocks": [
            ("h1", "Sprint 14 - Frontend and UX Plan"),
            ("p", f"Frontend stream plan for Sprint 14, {SPRINT_14}. Owner: frontend lead (User 3)."),
            ("h2", "Screens in scope"),
            ("bullets", [
                "Ask page: source chips with teammate label and download control",
                "Search page: teammate scope switch and empty-state copy",
                "Files page: error message live region",
                "Account page: no change",
            ]),
            ("h2", "Acceptance notes"),
            ("bullets", [
                f"First answer shown within {ASK_TARGET} on dev hardware (from the UX readout)",
                "Owner-offline download message uses the approved wording",
                "Keyboard focus reaches every source chip",
            ]),
            ("h2", "Dependencies"),
            ("bullets", [
                "Teammate search API from Platform (HM-216)",
                f"Stable warehouse metadata from {CUTOVER_DATE} (Data Platform)",
            ]),
            ("h2", "Test plan"),
            ("p", "Frontend unit tests with node --test, lint with npm run lint, build with npm run build. Manual check with two laptops during the pilot weeks."),
        ],
    },
    {
        "path": "User3/Public/Frontend/UX Research/UX Research Readout - Search Flow.txt",
        "title": "UX Research Readout - Search Flow",
        "author": "User 3",
        "created": "2026-10-13",
        "revised": "2026-10-13",
        "text": f"""UX RESEARCH READOUT - SEARCH FLOW
Author: Frontend (User 3)
Interviews 21 September to 2 October 2026.

Participants: five staff across two delivery teams (P1 to P5). Sessions were 45 minutes, remote.

Summary: teammates trust Ask when the answer names its source and shows the file date.
Search is used first; Ask is used when people already know roughly what they want.

Key findings
 1. Users expect the first answer in under {ASK_TARGET}. Two participants stopped waiting at about 6 seconds.
 2. Source labels must say whose file it is. Confusion came when a teammate's file looked like the user's own.
 3. Download is wanted, but only when the owner is online. The message must say so plainly.
 4. Empty results felt like a bug. Show what was searched (own files, teammates' public files).

Recommendations
 - Target a first answer in under {ASK_TARGET} on dev hardware
 - Teammate label on every teammate source chip
 - Plain message when the owner is offline
 - Show the search scope on empty results
""",
    },
    {
        "path": "User3/Public/Frontend/Design Reviews/Design Review - Ask Panel.pptx",
        "title": "Design Review - Ask Panel",
        "author": "User 3",
        "created": "2026-10-07",
        "revised": "2026-10-08",
        "slides": [
            {"title": "Design Review - Ask Panel", "subtitle": "Review held 7 October 2026 - decisions recorded 8 October 2026"},
            {"title": "Context", "bullets": [
                "Ask answers from own files and, when switched on, from teammates' public files",
                "Frontend lead presented three layout options",
            ]},
            {"title": "Options considered", "bullets": [
                "A. Sources list below the answer",
                "B. Source chips inline with the answer",
                "C. Side panel with full source preview",
            ]},
            {"title": "Decision", "bullets": [
                "Option B: source chips inline, with a Teammate label",
                "Download stays on the chip for teammate sources",
            ]},
            {"title": "Open points", "bullets": [
                "Wording of the owner-offline message",
                "Chunk count not shown to the asker for now",
            ]},
            {"title": "Accessibility notes", "bullets": [
                "Source chips reachable by keyboard",
                "Teammate label contrast checked against the palette",
            ]},
            {"title": "Next steps", "bullets": [
                "Build source chips in Sprint 14",
                "Usability check with five staff before the pilot",
            ]},
        ],
    },
    {
        "path": "User3/Public/Frontend/Accessibility/Accessibility Checklist - Release 1.pdf",
        "title": "Accessibility Checklist - Release 1",
        "author": "User 3",
        "created": "2026-09-02",
        "revised": "2026-09-30",
        "blocks": [
            ("h1", "Accessibility Checklist - Release 1"),
            ("p", "Owner: Frontend (User 3). Status as at 30 September 2026. Scope: Search, Ask, Files and Account pages."),
            ("table", ["Check", "Status", "Notes"], [
                ["Colour contrast, body text", "Pass", "Checked against palette"],
                ["Keyboard use of result lists", "Partial", "Ask chips added in Sprint 14"],
                ["Focus order on Ask page", "Pass", "Matches reading order"],
                ["Alt text for icons", "Pass", "Decorative icons hidden"],
                ["Errors announced to screen readers", "Open", "Live region needed on Files"],
                ["Reduced motion", "Pass", "Spinner respects preference"],
            ], [0.4, 0.15, 0.45]),
        ],
    },
]


def ts(date_text):
    return datetime.strptime(date_text, "%Y-%m-%d")


def set_heading_color(document):
    for style_name in ("Heading 1", "Heading 2"):
        document.styles[style_name].font.color.rgb = RGBColor.from_string(DARK)
        document.styles[style_name].font.name = HEADLINE_FONT


def render_docx(entry, out):
    document = Document()
    document.styles["Normal"].font.name = HEADLINE_FONT
    document.styles["Normal"].font.size = Pt(11)
    set_heading_color(document)
    props = document.core_properties
    props.title = entry["title"]
    props.author = entry["author"]
    props.last_modified_by = entry["author"]
    props.created = ts(entry["created"])
    props.modified = ts(entry["revised"])
    for block in entry["blocks"]:
        kind = block[0]
        if kind == "h1":
            document.add_heading(block[1], level=1)
        elif kind == "h2":
            document.add_heading(block[1], level=2)
        elif kind == "p":
            document.add_paragraph(block[1])
        elif kind == "bullets":
            for item in block[1]:
                document.add_paragraph(item, style="List Bullet")
        elif kind == "table":
            header, rows = block[1], block[2]
            table = document.add_table(rows=1, cols=len(header))
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.LEFT
            for index, text in enumerate(header):
                cell = table.rows[0].cells[index]
                cell.text = text
                cell.paragraphs[0].runs[0].font.bold = True
            for row in rows:
                cells = table.add_row().cells
                for index, text in enumerate(row):
                    cells[index].text = text
    document.save(out)


def add_headline(slide, text, dark, top, size):
    box = slide.shapes.add_textbox(Inches(0.6), top, Inches(10.6), Inches(1.4))
    frame = box.text_frame
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    words = text.split()
    body_color = PptxRGB.from_string(WHITE if dark else BLACK)
    if len(words) > 1:
        body_run = paragraph.add_run()
        body_run.text = " ".join(words[:-1]) + " "
        accent_run = paragraph.add_run()
        accent_run.text = words[-1]
        accent_run.font.name = ACCENT_FONT
        accent_run.font.italic = True
        accent_run.font.bold = True
        accent_run.font.color.rgb = PptxRGB.from_string(NEON if dark else BLACK)
        accent_run.font.size = PptxPt(size)
    else:
        body_run = paragraph.add_run()
        body_run.text = text
    body_run.font.name = HEADLINE_FONT
    body_run.font.bold = True
    body_run.font.size = PptxPt(size)
    body_run.font.color.rgb = body_color


def add_bullets(slide, bullets, top):
    box = slide.shapes.add_textbox(Inches(0.6), top, Inches(11.4), Inches(4.8))
    frame = box.text_frame
    frame.word_wrap = True
    for index, item in enumerate(bullets):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        run = paragraph.add_run()
        run.text = f"• {item}"
        run.font.name = HEADLINE_FONT
        run.font.size = PptxPt(20)
        run.font.color.rgb = PptxRGB.from_string(BLACK)
        paragraph.space_after = PptxPt(12)


def render_pptx(entry, out):
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    blank_layout = presentation.slide_layouts[6]
    presentation.core_properties.title = entry["title"]
    presentation.core_properties.author = entry["author"]
    presentation.core_properties.last_modified_by = entry["author"]
    presentation.core_properties.created = ts(entry["created"])
    presentation.core_properties.modified = ts(entry["revised"])
    for index, content in enumerate(entry["slides"]):
        slide = presentation.slides.add_slide(blank_layout)
        dark = index == 0
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = PptxRGB.from_string(DARK if dark else WHITE)
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(11.7), Inches(0.5), Inches(0.9), Inches(0.9))
        circle.fill.solid()
        circle.fill.fore_color.rgb = PptxRGB.from_string(GREEN)
        circle.line.fill.background()
        if dark:
            add_headline(slide, content["title"], dark=True, top=Inches(2.4), size=44)
            sub = slide.shapes.add_textbox(Inches(0.6), Inches(4.0), Inches(10.6), Inches(1.0))
            sub.text_frame.word_wrap = True
            run = sub.text_frame.paragraphs[0].add_run()
            run.text = content["subtitle"]
            run.font.name = HEADLINE_FONT
            run.font.size = PptxPt(18)
            run.font.color.rgb = PptxRGB.from_string(WHITE)
        else:
            add_headline(slide, content["title"], dark=False, top=Inches(0.6), size=32)
            add_bullets(slide, content["bullets"], top=Inches(2.0))
        footer = slide.shapes.add_textbox(Inches(0.6), Inches(6.9), Inches(8), Inches(0.4))
        footer_run = footer.text_frame.paragraphs[0].add_run()
        footer_run.text = "Fictional demo content"
        footer_run.font.name = HEADLINE_FONT
        footer_run.font.size = PptxPt(10)
        footer_run.font.color.rgb = PptxRGB.from_string(WHITE if dark else DARK)
    presentation.save(out)


def render_pdf(entry, out):
    pdf = FPDF()
    pdf.set_creation_date(ts(entry["created"]))
    pdf.set_author(entry["author"])
    pdf.set_title(entry["title"])
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(True, 20)
    pdf.add_page()
    for block in entry["blocks"]:
        kind = block[0]
        if kind == "h1":
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 8, block[1], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif kind == "h2":
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 7, block[1], new_x="LMARGIN", new_y="NEXT")
        elif kind == "p":
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, block[1], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif kind == "bullets":
            pdf.set_font("Helvetica", "", 11)
            for item in block[1]:
                pdf.multi_cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")
        elif kind == "table":
            header, rows = block[1], block[2]
            fractions = block[3] if len(block) > 3 else [1 / len(header)] * len(header)
            widths = [pdf.epw * fraction for fraction in fractions]
            pdf.set_font("Helvetica", "B", 9)
            for text, width in zip(header, widths):
                pdf.cell(width, 7, text, border=1)
            pdf.ln(7)
            pdf.set_font("Helvetica", "", 9)
            for row in rows:
                for text, width in zip(row, widths):
                    pdf.cell(width, 7, text, border=1)
                pdf.ln(7)
            pdf.ln(2)
    pdf.output(out)


def render_txt(entry, out):
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(entry["text"])


RENDERERS = {".docx": render_docx, ".pptx": render_pptx, ".pdf": render_pdf, ".txt": render_txt}


def main():
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        root = Path.home() / "Documents" / "HiveMind Demo"
    for entry in FILES:
        out = root / entry["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        suffix = out.suffix.lower()
        RENDERERS[suffix](entry, out)
        revised = ts(entry["revised"]).timestamp()
        os.utime(out, (revised, revised))
        print(out)
    print(f"Wrote {len(FILES)} files under {root}")


if __name__ == "__main__":
    main()
