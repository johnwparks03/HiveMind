"""User 2 (Delivery lead) public delivery files for the Falcon demo."""

from facts import (
    ASK_TARGET, CUTOVER, PHASE2_KICKOFF, PILOT_WINDOW, QUALITY_AGREED, QUALITY_THRESHOLD,
    SPRINT_14_GOAL, sprint_text,
)

S14_STORIES = [
    ["HM-241", "Ask pilot setup: access list for two pilot teams", "3", "Project management"],
    ["HM-242", "Ask first-answer speed tuning", "8", "Engineering"],
    ["HM-243", "Show teammate source names and owners in Ask answers", "5", "Engineering"],
    ["HM-244", "Warehouse extract quality check against threshold", "5", "Data"],
    ["HM-245", "Pilot feedback form and usage counts", "3", "Design"],
    ["HM-246", "Ask regression pack and pilot smoke test", "3", "Quality assurance"],
    ["HM-247", "Pilot team onboarding sessions and quick guide", "5", "Project management"],
]
assert sum(int(row[2]) for row in S14_STORIES) == 32

S12_STORIES = [
    ["HM-201", "Phase 2 environment baseline", "5", "Engineering"],
    ["HM-202", "Publish queue retry for failed uploads", "2", "Engineering"],
    ["HM-203", "Ask answers over several documents", "8", "Engineering"],
    ["HM-204", "Warehouse extract field mapping", "8", "Data"],
    ["HM-205", "Ask page layout refresh", "5", "Design"],
    ["HM-206", "Test plan update for Ask", "3", "Quality assurance"],
    ["HM-207", "Release readiness checklist", "2", "Project management"],
    ["HM-208", "Folder scan progress indicator", "3", "Engineering"],
]
assert sum(int(row[2]) for row in S12_STORIES) == 36

FILES = [
    {"file": "Sprint 12 Planning.docx", "blocks": [
        ("h1", "Sprint 12 Planning"),
        ("p", f"This document records planning for {sprint_text(12)}, the first sprint of Falcon Phase 2, written between 18 and 21 September 2026 by the Delivery lead (User 2). "
              f"It covers the sprint goal, committed stories, team capacity and risks, ahead of the Phase 2 kickoff on {PHASE2_KICKOFF}."),
        ("h2", "Sprint goal"),
        ("p", "Stand up the Phase 2 environment and deliver the first version of Ask answering from several documents, with the warehouse extract mapped so cutover work can start."),
        ("h2", "Committed stories"),
        ("table", ["ID", "Story", "Points", "Owner role"], S12_STORIES),
        ("p", "Total committed: 36 points."),
        ("h2", "Capacity"),
        ("bullets", [
            "Team capacity is 40 points: 6 engineers and analysts at 8 productive days each, less one day of kickoff activity.",
            "Velocity from Sprints 9 to 11 averaged 34 points during the bridge period; the extra points reflect the added Phase 2 team members.",
            "We leave 4 points of capacity for support and defects.",
        ]),
        ("h2", "Risks"),
        ("bullets", [
            "HM-204 depends on sample extracts from the Client delivery lead by 22 September; without them mapping slips to Sprint 13.",
            "HM-203 depends on the retrieval service responding within agreed limits; a spike is planned on day 2.",
            "Two people are on leave in the second week; capacity above already allows for this.",
        ]),
        ("h2", "Ceremonies"),
        ("p", "Daily stand-up at 09:15, mid-sprint refinement on 28 September, sprint review and retrospective on 2 October 2026."),
    ]},
    {"file": "Sprint 14 Planning.docx", "blocks": [
        ("h1", "Sprint 14 Planning"),
        ("p", f"This document records planning for {sprint_text(14)}, written between 16 and 20 October 2026 by the Delivery lead (User 2). The sprint goal is to {SPRINT_14_GOAL}. "
              f"It lists committed stories, capacity, and the dependency on the warehouse cutover on {CUTOVER}."),
        ("h2", "Sprint goal"),
        ("p", f"Pilot Ask for two teams. The pilot itself runs {PILOT_WINDOW}; this sprint gets the product, the access list and the checks ready and runs a dry run with the two teams."),
        ("h2", "Committed stories"),
        ("table", ["ID", "Story", "Points", "Owner role"], S14_STORIES),
        ("h2", "Capacity"),
        ("bullets", [
            "Capacity is 42 points; 32 points are committed, leaving 10 points for defects from Release v0.9, review feedback and leave cover.",
            "Engineering has 13 points committed, data 5, design 3, quality assurance 3 and project management 8.",
        ]),
        ("h2", "Targets"),
        ("bullets", [
            f"First Ask answer in under {ASK_TARGET} (HM-242).",
            f"Warehouse extract quality at or above {QUALITY_THRESHOLD}, the threshold agreed on {QUALITY_AGREED} (HM-244).",
        ]),
        ("h2", "Dependencies and risks"),
        ("bullets", [
            f"Warehouse cutover on {CUTOVER}: the pilot teams use warehouse data after cutover, so HM-244 must pass before then. A slip moves the start of the pilot.",
            "Pilot team availability for the onboarding sessions in the last week of the sprint.",
            "Retrieval response times under load are not yet measured with two teams (HM-242 includes the first load test).",
        ]),
        ("h2", "Sprint review"),
        ("p", "Sprint review is on 30 October 2026 with the Client sponsor and the Client delivery lead. The demo shows Ask with teammate sources and the pilot feedback form."),
    ]},
    {"file": "Backlog Prioritisation Notes.txt", "text": f"""BACKLOG PRIORITISATION NOTES

Topic: how the Falcon backlog was ordered between 22 June and 14 October 2026, with the reasons for each change. Kept by the Delivery lead (User 2) after each refinement session. Ordering rule: value to the pilot first, then risk reduction, then effort.

22 JUNE 2026
Refinement before Sprint 5 ended. CRM integration items stay on top because Change Order 01 is funded and dated. Moved the folder-level public/private toggle above tag tuning: users told us in discovery that control over sharing comes first.

13 JULY 2026
Sprint 7 start. Pulled the file download relay forward; the Executive sponsor wants it in the Sprint 10 demo. Deferred PowerPoint slide-text extraction: PDF and DOCX cover most of the sample files.

27 JULY 2026
Sprint 8 start, last sprint of Phase 1. Cut three polish items (result sorting, dark theme, keyboard shortcuts) to a later phase. Defects from the Sprint 6 demo take the first 4 points.

3 AUGUST 2026
Change Order 02 signed. Bridge period (Sprints 9 to 11) holds capacity for defects, the Phase 1 readout follow-ups and discovery of Phase 2 scope. No new features above 5 points are accepted during the bridge.

24 AUGUST 2026
Sprint 10 start. Ask over several documents moved to the top of the Phase 2 candidate list. Warehouse extract mapping ranked second because the cutover has a fixed date.

14 SEPTEMBER 2026
Steering approved the Phase 2 budget. Ordered the first Phase 2 sprint: environment baseline (HM-201), Ask answers over several documents (HM-203), extract mapping (HM-204).

28 SEPTEMBER 2026
Mid-Sprint 12 refinement. The Client delivery lead asked for faster first answers; added a speed target of {ASK_TARGET} as a pilot gate and created HM-242. The data quality threshold of {QUALITY_THRESHOLD} was agreed on {QUALITY_AGREED}, so the extract quality check (HM-244) moves above all new Ask features.

9 OCTOBER 2026
Release v0.9 shipped. Three known issues went into the backlog: slow first answer on long PDFs, duplicate results after a file is renamed, and a missing progress message on large folders.

14 OCTOBER 2026
Refinement for {sprint_text(14)}. Order for the pilot sprint: speed tuning, extract quality check, teammate source names in answers, pilot setup, feedback form, regression pack. Held back: Ask export to document and saved questions; both go after the pilot.

RULES WE KEEP USING
- Anything the pilot depends on outranks anything it does not.
- Defects found in a demo are fixed in the next sprint, not queued.
- A story over 8 points is split before it is committed.
"""},
    {"file": "Definition of Done.docx", "blocks": [
        ("h1", "Definition of Done"),
        ("p", "This document is the Falcon Definition of Done: the checklist a story must satisfy before the team marks it done. First written 13 April 2026 before Sprint 1 and revised on 3 August 2026, "
              "at the end of Phase 1, to add security and documentation checks. Owned by the Delivery lead (User 2) and agreed by the Project lead (User 1)."),
        ("h2", "Code and build"),
        ("bullets", [
            "Code is reviewed by one other engineer and merged to the main branch.",
            "Unit tests cover new behaviour and all tests pass in the build.",
            "No new lint errors; configuration values are not hard coded.",
        ]),
        ("h2", "Quality assurance"),
        ("bullets", [
            "Acceptance criteria in the story are each checked and ticked off.",
            "The regression pack runs clean on the test environment.",
            "Defects found are fixed or logged with a severity and an owner.",
        ]),
        ("h2", "Security and privacy"),
        ("bullets", [
            "Request bodies, credentials, tokens and file content are never written to logs.",
            "Private files are not uploaded; the test for this still passes.",
            "Secrets stay in the approved store, never in the repository.",
        ]),
        ("h2", "Documentation"),
        ("bullets", [
            "The API contract or user guide is updated when a behaviour changes.",
            "Release notes carry a line for the story.",
            "Runbook steps are updated for any change to operations.",
        ]),
        ("h2", "Product acceptance"),
        ("bullets", [
            "The story is shown to the Delivery lead or the product owner and accepted in the sprint review.",
            "A story that fails any item returns to the board, not to the next sprint by default.",
        ]),
        ("h2", "Change history"),
        ("table", ["Date", "Change"], [
            ["13 Apr 2026", "First version for Sprint 1"],
            ["12 Jun 2026", "Added regression pack requirement"],
            ["3 Aug 2026", "Added security and privacy checks and the documentation section"],
        ]),
    ]},
    {"file": "Release Notes - v0.9.txt", "text": f"""RELEASE NOTES - V0.9

Topic: Harborview Platform release v0.9, published 9 October 2026 by the Delivery lead (User 2). It contains the work from {sprint_text(12)} and the fixes made in the first week of Sprint 13. Sprint 13 is still running.

WHAT IS NEW
- HM-203 Ask can now answer a question from several of your documents and name its sources.
- HM-205 The Ask page has a new layout with the answer on the left and the sources on the right.
- HM-204 The warehouse extract mapping is in place for the first three tables; the rest follow before the cutover.
- HM-201 The Phase 2 environment is the single environment used for the demo and the pilot.
- HM-207 The release checklist is now part of every build.

IMPROVEMENTS
- HM-202 Failed uploads of public files are retried automatically with a limit.
- HM-208 The Files page shows a spinner next to a folder that is still being read.
- Search results now show the file owner and last modified date.

FIXES
- A renamed file no longer appears twice in your own results until the next scan.
- Opening a file whose name contains an ampersand now works.
- The tag list on the Files page no longer cuts off long tags.

KNOWN ISSUES
- The first answer for a question over very long PDFs can take longer than we want. Tracked as HM-242 and planned for {sprint_text(14)}.
- After a file is renamed in the shared folder, a teammate may still see the old name for up to one scan.
- A very large folder can show no progress message for the first few seconds.
- Ask does not yet cover PowerPoint slide notes.

UPGRADE NOTES
- No action needed. The agent updates the local database on first start.
- Re-run the folder scan if you want tags regenerated for older files.

NEXT
Release v0.10 is planned after Sprint 14 with the pilot features. The pilot with two teams runs {PILOT_WINDOW}.
"""},
]
