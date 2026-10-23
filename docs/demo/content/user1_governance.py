"""User 1 public files: Falcon governance (9 files)."""

from facts import (
    CLIENT, PLATFORM, SOW1_VALUE, SOW1_SIGNED, PHASE1_KICKOFF, CO01_AMOUNT, CO01_DATE,
    PHASE1_TOTAL, CO02_DATE, PHASE1_END, PHASE1_READOUT, BRIDGE_PERIOD, STEERING_JUNE,
    APPROVAL_DATE, PHASE2_BUDGET, PHASE2_KICKOFF, PILOT_WINDOW, sprint_text,
)

FILES = [
    {
        "file": "Project Charter.docx",
        "blocks": [
            ("h1", "Falcon Project Charter"),
            ("p", f"This charter sets out the purpose, objectives, scope, governance and success measures for "
                  f"Phase 1 of the Falcon project, which builds the {PLATFORM} for {CLIENT}. It was prepared in "
                  f"February 2026 and confirmed at the kickoff on {PHASE1_KICKOFF}."),
            ("h2", "Purpose"),
            ("p", "Staff at the client spend too much time finding documents that already exist. Falcon gives "
                  "them one place to search and ask questions, with answers that show their sources."),
            ("h2", "Objectives"),
            ("bullets", [
                "Deliver a working search and question-answering platform by 7 August 2026",
                "Cover PDF, DOCX, PPTX and TXT documents from the agreed repositories",
                "Show measurable improvement in time to find a document in user tests",
                "Leave the client with a clear recommendation and plan for Phase 2",
            ]),
            ("h2", "Scope"),
            ("p", f"In scope: discovery, architecture, ingestion, search, question answering, testing and a "
                  f"readout, as defined in the statement of work signed on {SOW1_SIGNED} for {SOW1_VALUE}. Out "
                  "of scope at charter date: CRM integration, mobile access and non-English documents."),
            ("h2", "Governance"),
            ("table", ["Body", "Members", "Cadence"],
             [["Steering committee", "Executive sponsor, client sponsor, project lead", "Monthly"],
              ["Delivery meeting", "Project lead, delivery lead, client delivery lead", "Weekly"],
              ["Sprint review", "Team and client users", "Every second sprint"]]),
            ("h2", "Success measures"),
            ("bullets", [
                "Phase 1 delivered inside the approved fee, with change orders as the only route to more scope",
                "Client sponsor accepts all five Phase 1 deliverables",
                "Positive user feedback in the demo sessions",
            ]),
        ],
    },
    {
        "file": "Kickoff Deck - Phase 1.pptx",
        "slides": [
            {"title": "Falcon Phase 1 Kickoff",
             "subtitle": f"{CLIENT} - kickoff meeting, {PHASE1_KICKOFF}"},
            {"title": "Why We Are Here",
             "bullets": [
                 "Staff lose time searching for documents across several repositories",
                 "Phase 1 builds the first working version of the Harborview Platform",
                 "The statement of work was signed on 12 February 2026",
             ]},
            {"title": "Objectives",
             "bullets": [
                 "Complete discovery and agree the priority use cases by early April",
                 "Build search and question answering in eight two-week sprints from 20 April",
                 "Hold a Phase 1 readout and recommend next steps in August",
             ]},
            {"title": "Scope and Fee",
             "bullets": [
                 f"Fixed fee of {SOW1_VALUE} covering five deliverables, D1 to D5",
                 "CRM integration is excluded and would need a change order",
                 "Changes to scope are agreed in writing by both sponsors",
             ]},
            {"title": "Team and Roles",
             "bullets": [
                 "Executive sponsor and client sponsor own decisions and escalations",
                 "Project lead owns plan, risks and the budget",
                 "Delivery lead owns sprints, quality and the technical approach",
                 "Client delivery lead owns access, users and review of deliverables",
             ]},
            {"title": "Ways of Working",
             "bullets": [
                 "Weekly delivery meeting and written status note each Friday",
                 "Monthly steering committee, first meeting in April",
                 "Risks and decisions logged in shared files visible to the client",
             ]},
            {"title": "First 30 Days",
             "bullets": [
                 "Repository access granted by the client within two weeks",
                 "Stakeholder interviews and a discovery workshop",
                 "Current-state assessment and findings report drafted",
                 "Environment set up and security review started",
             ]},
            {"title": "Questions and Next Steps",
             "bullets": [
                 "Confirm the meeting calendar and steering dates",
                 "Client delivery lead to send the repository access list",
             ]},
        ],
    },
    {
        "file": "Kickoff Deck - Phase 2.pptx",
        "slides": [
            {"title": "Falcon Phase 2 Kickoff",
             "subtitle": f"{CLIENT} - kickoff on {PHASE2_KICKOFF}, deck updated 18 September 2026"},
            {"title": "Where We Are",
             "bullets": [
                 f"Phase 1 ended on {PHASE1_END} and was reviewed at the readout on {PHASE1_READOUT}",
                 f"The bridge period covered {BRIDGE_PERIOD}",
                 "Search, ingestion and question answering work for the Phase 1 document set",
             ]},
            {"title": "Approved Budget",
             "bullets": [
                 f"The steering committee approved the Phase 2 budget of {PHASE2_BUDGET} on {APPROVAL_DATE}",
                 "The budget is not-to-exceed; any increase needs a signed change order",
                 "Budget tracked monthly and reported to the steering committee",
             ]},
            {"title": "Phase 2 Objectives",
             "bullets": [
                 "Improve search quality against an agreed set of test questions",
                 "Let a team ask questions across documents its teammates share",
                 "Migrate the warehouse document store, planned for early November",
                 "Run a pilot with two client teams",
             ]},
            {"title": "Sprint Plan",
             "bullets": [
                 f"{sprint_text(12)}: kickoff, backlog and quality baseline",
                 f"{sprint_text(13)}: question answering across shared documents",
                 f"{sprint_text(14)} - goal: pilot Ask for two teams",
             ]},
            {"title": "Pilot",
             "bullets": [
                 f"Pilot with two teams runs {PILOT_WINDOW}",
                 "Client names the two teams and releases time for training",
                 "Closing report and handover follow in December",
             ]},
            {"title": "Risks to Watch",
             "bullets": [
                 "Warehouse migration timing and data quality",
                 "Pilot team availability around the November period",
                 "Search quality on older scanned documents",
             ]},
            {"title": "Next Steps",
             "bullets": [
                 "Sprint 12 planning on the kickoff day",
                 "Client to confirm pilot teams by the end of Sprint 12",
                 "First Phase 2 steering update in October",
             ]},
        ],
    },
    {
        "file": "RACI Matrix.docx",
        "blocks": [
            ("h1", "Falcon RACI Matrix"),
            ("p", "This RACI matrix assigns who is responsible, accountable, consulted and informed for the main "
                  "Falcon activities. It was created in February 2026 and revised on 10 August 2026 after Phase 1 "
                  "to reflect the bridge period team."),
            ("p", "R = responsible, A = accountable, C = consulted, I = informed. Each task has exactly one A."),
            ("table", ["Task", "Exec sponsor", "Project lead", "Delivery lead", "Client sponsor", "Client delivery"],
             [["Approve scope and change orders", "A", "R", "C", "A", "C"],
              ["Maintain plan and budget", "I", "A", "R", "I", "C"],
              ["Run sprints and backlog", "I", "C", "A", "I", "R"],
              ["Architecture decisions", "I", "C", "A", "I", "C"],
              ["Access to repositories", "I", "C", "C", "A", "R"],
              ["Test and acceptance", "I", "R", "R", "A", "C"],
              ["Steering reporting", "C", "A", "R", "C", "I"],
              ["Risk and issue log", "I", "A", "R", "I", "C"],
              ["Training and handover", "I", "C", "A", "I", "R"]]),
            ("h2", "Notes"),
            ("bullets", [
                "Where two roles hold A, both sponsors must agree before a decision is final",
                "The delivery lead acts for the project lead during absence",
                "Escalations go to the sponsors within two working days",
            ]),
        ],
    },
    {
        "file": "Communications Plan.docx",
        "blocks": [
            ("h1", "Falcon Communications Plan"),
            ("p", f"This plan sets out how the Falcon team shares progress, decisions and risks with {CLIENT} and "
                  "with each other. It was drafted in February 2026 and last updated on 9 June 2026, ahead of "
                  f"the steering committee on {STEERING_JUNE}."),
            ("h2", "Channels and cadence"),
            ("table", ["Communication", "Audience", "Frequency", "Owner"],
             [["Weekly status note", "Client delivery lead, sponsors", "Fridays", "Project lead"],
              ["Delivery meeting", "Core team and client delivery lead", "Weekly", "Delivery lead"],
              ["Sprint demo", "Client users and sponsors", "Every second sprint", "Delivery lead"],
              ["Steering committee", "Sponsors and project lead", "Monthly", "Project lead"],
              ["Risk register update", "Core team", "Weekly", "Project lead"]]),
            ("h2", "Principles"),
            ("bullets", [
                "Bad news travels the same day, by phone or message, before it is written up",
                "Decisions are recorded in the decision log within one working day",
                "Status notes use the same headings each week: progress, risks, next week",
                "Client documents are shared through the agreed folder, never by personal email",
            ]),
            ("h2", "Escalation"),
            ("p", "Issues that threaten a milestone or the budget go to the project lead the same day. If they "
                  "are not resolved in two working days, they go to the executive sponsor and the client sponsor."),
        ],
    },
    {
        "file": "Risk Register.docx",
        "blocks": [
            ("h1", "Falcon Risk Register"),
            ("p", "This living register tracks the open and closed risks for the Falcon project from March to "
                  "October 2026. Each entry has an owner and a status, and the register was last reviewed on "
                  "12 October 2026."),
            ("table", ["ID", "Risk", "Impact", "Owner", "Status"],
             [["R01", "Client repository access delayed", "High", "Client delivery lead", "Closed 20 March 2026"],
              ["R02", "CRM data not in scope but wanted by users", "Medium",
               "Project lead", f"Closed, change order approved {CO01_DATE}"],
              ["R03", "Search quality too low on scanned PDFs", "High", "Delivery lead", "Open, mitigation in test"],
              ["R04", "Phase 2 budget not approved in time", "High", "Executive sponsor",
               f"Closed {APPROVAL_DATE}"],
              ["R05", "Loss of engineers during the bridge period", "Medium", "Project lead",
               "Closed 21 September 2026"],
              ["R06", "Warehouse migration overruns its window", "High", "Delivery lead",
               "Open, cutover planned for early November"],
              ["R07", "Pilot teams unavailable for training", "Medium", "Client delivery lead", "Open"],
              ["R08", "Answer speed too slow for pilot users", "Medium", "Delivery lead", "Open, being measured"]]),
            ("h2", "Recent entries"),
            ("bullets", [
                "5 October 2026: R03 rated down from High to Medium after the Sprint 12 retest",
                "12 October 2026: R07 raised after the client asked to move one training session",
                "12 October 2026: R06 reviewed; rehearsal planned before the cutover",
            ]),
        ],
    },
    {
        "file": "Assumptions and Dependencies Log.txt",
        "text": """ASSUMPTIONS AND DEPENDENCIES LOG - FALCON

This log records the assumptions the Falcon plan relies on and the dependencies on the client and on other teams, with dated entries from March to September 2026. It was last updated on 30 September 2026.

04 March 2026 - A01 (assumption): documents are in PDF, DOCX, PPTX or TXT only. Owner: Project lead. Status: confirmed in discovery.

04 March 2026 - D01 (dependency): client provides read access to the shared drives within two weeks of kickoff. Owner: Client delivery lead. Status: met 20 March 2026.

18 March 2026 - A02 (assumption): between five and eight business users are available for interviews and testing. Owner: Client delivery lead. Status: confirmed.

08 April 2026 - D02 (dependency): the client security team reviews the architecture before any production connection. Owner: Delivery lead. Status: review completed in July 2026.

11 May 2026 - A03 (assumption): the CRM vendor interface stays stable during Sprints 3 to 5. Owner: Delivery lead. Status: held; Change Order 01 approved.

15 June 2026 - D03 (dependency): the client names a business owner for the platform before the end of Phase 1. Owner: Client sponsor. Status: met 3 July 2026.

03 August 2026 - A04 (assumption): the Phase 1 contingency is enough to fund the bridge period, Sprints 9 to 11. Owner: Project lead. Status: confirmed in Change Order 02.

14 September 2026 - A05 (assumption): the Phase 2 budget of $48,200 is not-to-exceed and holds without a further change order. Owner: Project lead. Status: open, reviewed monthly.

21 September 2026 - D04 (dependency): the client names two pilot teams and releases their time. Owner: Client sponsor. Status: open, due end of Sprint 12.

21 September 2026 - D05 (dependency): the warehouse system owner supports the migration window planned for early November. Owner: Delivery lead. Status: open.

30 September 2026 - A06 (assumption): the pilot runs from 9 to 27 November 2026 with two teams. Owner: Project lead. Status: open.

30 September 2026 - D06 (dependency): the client support team joins the handover sessions in October. Owner: Client delivery lead. Status: open.
""",
    },
    {
        "file": "Delivery Roadmap.pptx",
        "slides": [
            {"title": "Falcon Delivery Roadmap",
             "subtitle": "Phases and milestones for the Harborview Platform - revised 16 September 2026"},
            {"title": "Roadmap at a Glance",
             "bullets": [
                 "Phase 1: 2 March to 7 August 2026, discovery and core build",
                 "Bridge period: 10 August to 18 September 2026, Sprints 9 to 11",
                 "Phase 2: 21 September to 30 October 2026 build, then pilot in November",
             ]},
            {"title": "Phase 1 Milestones",
             "bullets": [
                 f"2 March: kickoff; 12 February statement of work signed for {SOW1_VALUE}",
                 "20 April: Sprint 1 starts, eight sprints to 7 August",
                 f"11 May: Change Order 01 approved, Phase 1 total {PHASE1_TOTAL}",
                 f"12 August: executive readout of Phase 1",
             ]},
            {"title": "Bridge Period",
             "bullets": [
                 f"Change Order 02 on {CO02_DATE} funds Sprints 9 to 11 from contingency",
                 "Sprint 10 demo on 4 September shows improved search ranking",
                 "Phase 2 plan and budget request prepared in Sprint 11",
             ]},
            {"title": "Phase 2 Milestones",
             "bullets": [
                 f"{APPROVAL_DATE}: steering committee approves {PHASE2_BUDGET}",
                 f"{PHASE2_KICKOFF}: kickoff and Sprint 12 start",
                 f"{sprint_text(14)}: pilot Ask for two teams",
                 "Early November: warehouse cutover (planned)",
             ]},
            {"title": "Pilot and Close",
             "bullets": [
                 f"Pilot with two teams: {PILOT_WINDOW}",
                 "Training and handover to the client support team during October and November",
                 "Closing report in December 2026",
             ]},
            {"title": "Dependencies",
             "bullets": [
                 "Pilot teams named by the client by the end of Sprint 12",
                 "Warehouse system owner confirms the migration window",
                 "Search quality target agreed before the pilot starts",
             ]},
        ],
    },
    {
        "file": "Decision Log.txt",
        "text": """DECISION LOG - FALCON

This log records the key decisions on the Falcon project from kickoff on 2 March 2026 to 20 October 2026: contract changes, approvals, dates and governance. Each entry has an ID, the decision, the decider and the reason.

02 March 2026 - DEC-001: Phase 1 kickoff held; project cadence set as a weekly delivery meeting and a status note every Friday. Decided by: Project lead and Client delivery lead.

02 March 2026 - DEC-002: steering committee meets monthly. Decided by: Executive sponsor and Client sponsor. Reason: enough oversight without slowing the team.

18 March 2026 - DEC-003: build sprints are two weeks, Monday start, with Sprint 1 on 20 April 2026. Decided by: Delivery lead. Reason: leaves seven weeks for discovery and design first.

11 May 2026 - DEC-004: Change Order 01 approved, adding the CRM integration for $6,800 and raising the Phase 1 total from $31,500 to $38,300. Decided by: Client sponsor and Executive sponsor. Reason: discovery showed the CRM holds the notes users want most.

15 June 2026 - DEC-005: steering committee asks for an early Phase 2 outline by the end of July. Decided by: Client sponsor.

10 July 2026 - DEC-006: after the Sprint 6 demo, Ask answers must show the source document for every answer. Decided by: Client sponsor.

03 August 2026 - DEC-007: Change Order 02 approved. A bridge period covering Sprints 9 to 11 runs at no added fee, funded from the Phase 1 contingency. Decided by: Client sponsor and Executive sponsor. Reason: keep the team and momentum while the Phase 2 budget is decided.

07 August 2026 - DEC-008: Phase 1 declared complete; executive readout set for 12 August 2026. Decided by: Project lead.

14 September 2026 - DEC-009: steering committee approved the Phase 2 budget of $48,200. Decided by: Client sponsor and Executive sponsor. Reason: Phase 1 results and the Phase 2 plan met the agreed conditions.

14 September 2026 - DEC-010: Phase 2 kickoff set for 21 September 2026, together with the start of Sprint 12. Decided by: Executive sponsor and Project lead.

21 September 2026 - DEC-011: pilot will run with two client teams from 9 to 27 November 2026. Decided by: Client sponsor.

05 October 2026 - DEC-012: a short written update is added between monthly steering meetings during the pilot build. Decided by: Executive sponsor.

12 October 2026 - DEC-013: warehouse cutover stays planned for early November; a rehearsal is added before it. Decided by: Delivery lead.

20 October 2026 - DEC-014: Sprint 14 goal confirmed as pilot Ask for two teams. Decided by: Project lead and Delivery lead.
""",
    },
]
