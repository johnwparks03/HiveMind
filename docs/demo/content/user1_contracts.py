"""User 1 public files: Falcon contracts (9 files)."""

from facts import (
    CLIENT, PLATFORM, MSA_SIGNED, SOW1_VALUE, SOW1_SIGNED, PHASE1_KICKOFF, CO01_AMOUNT,
    CO01_DATE, PHASE1_TOTAL, CO02_DATE, PHASE1_END, BRIDGE_PERIOD, APPROVAL_DATE,
    PHASE2_BUDGET, PHASE2_KICKOFF, PILOT_WINDOW, sprint_text,
)

FILES = [
    {
        "file": "Falcon Proposal Deck.pptx",
        "slides": [
            {"title": "Falcon Proposal",
             "subtitle": f"Knowledge search for {CLIENT} - proposal deck, January 2026"},
            {"title": "The Problem",
             "bullets": [
                 "Operations, sales and support documents sit in shared drives, inboxes and a CRM",
                 "Staff report spending about a quarter of their week looking for existing material",
                 "Answers differ by team because nobody can see the latest approved version",
                 "Keyword search misses documents that use different words for the same idea",
             ]},
            {"title": "Our Approach",
             "bullets": [
                 f"Build the {PLATFORM}: one place to search and ask questions across documents",
                 "Combine keyword and meaning-based search so near matches are found",
                 "Keep source files where they are; index content and metadata only",
                 "Deliver in two-week sprints with a demo to the client at every second sprint",
             ]},
            {"title": "Proposed Team",
             "bullets": [
                 "Executive sponsor: accountable for outcomes and the client relationship",
                 "Project lead and delivery lead: scope, plan, risks and day-to-day delivery",
                 "Engineers and a data analyst: ingestion, search relevance and the user interface",
                 "Client sponsor and client delivery lead: decisions, access and acceptance",
             ]},
            {"title": "Pricing Outline",
             "bullets": [
                 f"Phase 1 proposed as a fixed fee of {SOW1_VALUE} under the Master Services Agreement",
                 "Fee covers discovery, design, build of the core platform and a readout",
                 "Hourly rates follow the Rate Card; changes handled by written change order",
                 "Phase 2 priced separately once Phase 1 learning is known",
             ]},
            {"title": "Indicative Timeline",
             "bullets": [
                 "February 2026: statement of work agreed and team mobilised",
                 "March 2026: kickoff, discovery and current-state assessment",
                 "April to July 2026: eight two-week build sprints, starting 20 April",
                 "August 2026: Phase 1 readout and a recommendation on Phase 2",
             ]},
            {"title": "Risks We Will Manage",
             "bullets": [
                 "Data access and document permissions need client approval early",
                 "Source systems change during the project, so integration scope is kept explicit",
                 "Adoption depends on training and a named business owner for the platform",
             ]},
            {"title": "Next Steps",
             "bullets": [
                 "Client review of this proposal and the draft statement of work",
                 "Confirm the client sponsor and the client delivery lead",
                 "Agree the kickoff week and the access needed for discovery",
             ]},
        ],
    },
    {
        "file": "RFP Response.docx",
        "blocks": [
            ("h1", f"{CLIENT} RFP Response - Knowledge Search Platform"),
            ("p", f"This document records our written answers to the {CLIENT} request for proposal for a "
                  "knowledge-search platform, prepared in January 2026 and last updated on 20 January 2026. "
                  "It supports the Falcon proposal and the draft statement of work."),
            ("h2", "Q1. How will you approach discovery?"),
            ("p", "We run a four-week discovery with interviews across operations, sales and support, a review of "
                  "the main document repositories and a current-state assessment. The output is a findings report "
                  "that ranks use cases by value and effort."),
            ("h2", "Q2. How is document security handled?"),
            ("p", "Search results respect the permissions of the source system. Documents are not copied to "
                  "personal devices. Access is logged, and the client security team reviews the design before "
                  "any production connection is made."),
            ("h2", "Q3. What is your delivery method?"),
            ("p", "Two-week sprints with a planning session, a mid-sprint check and a demo. A steering committee "
                  "meets monthly to review progress, budget and risks."),
            ("h2", "Q4. How do you price the work?"),
            ("p", f"Phase 1 is offered as a fixed fee of {SOW1_VALUE}. Extra scope is added only through a signed "
                  "change order priced from the Rate Card. We do not bill for rework caused by our own defects."),
            ("h2", "Q5. What do you need from us?"),
            ("bullets", [
                "A client sponsor with authority to make scope and budget decisions",
                "A client delivery lead available for at least half a day each week",
                "Read access to the agreed document repositories within two weeks of kickoff",
                "Five to eight business users for interviews and user testing",
            ]),
            ("h2", "Q6. How will you measure success?"),
            ("p", "Agreed measures are the share of test questions answered with a correct source, the time to "
                  "find a document in user tests and the number of weekly active users after launch."),
        ],
    },
    {
        "file": "Statement of Work - Phase 1.pdf",
        "blocks": [
            ("h1", "Statement of Work - Phase 1"),
            ("p", f"This statement of work defines the scope, deliverables, fee and acceptance terms for Phase 1 "
                  f"of the Falcon engagement with {CLIENT}. It was signed on {SOW1_SIGNED} under the Master "
                  f"Services Agreement dated {MSA_SIGNED}."),
            ("h2", "Scope"),
            ("p", f"The firm will discover requirements, design and build the core of the {PLATFORM}: document "
                  "ingestion from the agreed repositories, search across file names, tags and content, and a "
                  "question-answering view that cites its sources."),
            ("h2", "Deliverables"),
            ("bullets", [
                "D1 Current-state assessment and discovery findings report",
                "D2 Solution architecture and security review summary",
                "D3 Working platform covering ingestion, search and question answering",
                "D4 Test plan and test results for the core release",
                "D5 Executive readout and a recommendation for Phase 2",
            ]),
            ("h2", "Fee and Payment"),
            ("p", f"The fixed fee is {SOW1_VALUE}, invoiced in three equal instalments at kickoff, at the end of "
                  "discovery and on acceptance of D5. Payment terms follow the Master Services Agreement."),
            ("h2", "Timeline"),
            ("p", f"Kickoff is planned for {PHASE1_KICKOFF}. Build runs in eight two-week sprints from 20 April "
                  "2026, with Phase 1 ending in early August 2026."),
            ("h2", "Assumptions"),
            ("bullets", [
                "The client provides repository access within two weeks of kickoff",
                "Documents are in PDF, DOCX, PPTX or TXT format",
                "Integration with the customer relationship system is out of scope",
                "The client reviews each deliverable within five business days",
            ]),
            ("h2", "Acceptance"),
            ("p", "A deliverable is accepted when the client sponsor confirms in writing that it meets its "
                  "description. Silence for ten business days after delivery counts as acceptance."),
        ],
    },
    {
        "file": "Statement of Work - Phase 2.pdf",
        "blocks": [
            ("h1", "Statement of Work - Phase 2"),
            ("p", f"This statement of work defines Phase 2 of the Falcon engagement with {CLIENT}: scope, "
                  f"deliverables, budget and timeline for the build from {PHASE2_KICKOFF} to 30 October 2026 and "
                  f"the pilot in November 2026. The steering committee approved the Phase 2 budget of "
                  f"{PHASE2_BUDGET} on {APPROVAL_DATE}."),
            ("h2", "Scope"),
            ("p", "Phase 2 takes the Phase 1 platform to a working pilot. It adds improved search quality, "
                  "question answering across a team's shared documents, migration of the warehouse document "
                  "store, user acceptance testing, training and handover to the client support team."),
            ("h2", "Deliverables"),
            ("bullets", [
                "D6 Search quality improvements measured against an agreed question set",
                "D7 Question answering that cites documents shared by teammates",
                "D8 Migration of the warehouse document store, planned for early November 2026",
                "D9 User acceptance test plan and results",
                "D10 End-user training, user guide and support model",
                "D11 Pilot with two client teams and a closing report",
            ]),
            ("h2", "Budget"),
            ("p", f"The total Phase 2 budget is {PHASE2_BUDGET}, approved on {APPROVAL_DATE}. It is a "
                  "not-to-exceed amount billed on time and materials against the Rate Card. Any increase needs "
                  "a signed change order."),
            ("h2", "Timeline"),
            ("bullets", [
                f"Build: {PHASE2_KICKOFF.replace(' 2026', '')} to 30 October 2026, Sprints 12 to 14",
                f"Pilot with two teams: {PILOT_WINDOW}",
                "Closing report and handover: December 2026",
            ]),
            ("h2", "Assumptions"),
            ("bullets", [
                "Phase 1 deliverables are accepted and the platform stays in the agreed environment",
                "The client names two pilot teams and releases their time for training and feedback",
                "The warehouse system owner supports the migration window",
            ]),
            ("h2", "Acceptance"),
            ("p", "The client sponsor accepts each deliverable in writing within five business days of "
                  "delivery. The pilot closes when the closing report is accepted."),
        ],
    },
    {
        "file": "Change Order 01 - CRM Integration.docx",
        "blocks": [
            ("h1", "Change Order 01 - CRM Integration"),
            ("p", f"Change Order 01 adds an integration with the {CLIENT} customer relationship system to Phase 1 "
                  f"of Falcon for an additional {CO01_AMOUNT}. It was approved on {CO01_DATE} and raises the "
                  f"Phase 1 total from {SOW1_VALUE} to {PHASE1_TOTAL}."),
            ("h2", "Reason for the change"),
            ("p", "Discovery showed that account notes and proposals that staff need most live in the CRM, not "
                  "in the document repositories. The original statement of work excluded the CRM. The client "
                  "sponsor asked for it to be included."),
            ("h2", "Added scope"),
            ("bullets", [
                "Read-only connector to CRM accounts, opportunities and attached documents",
                "Mapping of CRM account names to document tags",
                "Nightly refresh of CRM metadata into the search index",
                "Two additional test cycles for the connector",
            ]),
            ("h2", "Cost and schedule"),
            ("table", ["Item", "Amount"],
             [["Original fixed fee, Phase 1", SOW1_VALUE],
              ["Change Order 01", f"+{CO01_AMOUNT}"],
              ["Revised Phase 1 total", PHASE1_TOTAL]]),
            ("p", "The integration is built in Sprints 3 to 5 alongside existing work. The end date of Phase 1 "
                  "does not change."),
            ("h2", "Assumptions"),
            ("bullets", [
                "The client provides a CRM service account with read access by 18 May 2026",
                "The CRM vendor interface is stable during the build",
            ]),
            ("h2", "Approval"),
            ("p", f"Approved by the client sponsor and the executive sponsor on {CO01_DATE}."),
        ],
    },
    {
        "file": "Change Order 02 - Bridge Period.docx",
        "blocks": [
            ("h1", "Change Order 02 - Bridge Period"),
            ("p", f"Change Order 02, dated {CO02_DATE}, funds a bridge period for Falcon covering "
                  f"{BRIDGE_PERIOD}, between the end of Phase 1 and the start of Phase 2. It carries no added "
                  "fee and is paid from the Phase 1 contingency."),
            ("h2", "Reason for the change"),
            ("p", f"Phase 1 ends on {PHASE1_END}, but the Phase 2 budget will not be decided until the steering "
                  "committee meets in September. Stopping would lose the team and the momentum, so both parties "
                  "agreed to keep a reduced team working on low-risk items."),
            ("h2", "Work in the bridge period"),
            ("bullets", [
                f"{sprint_text(9)}: stabilise ingestion and fix open Phase 1 defects",
                f"{sprint_text(10)}: improve search ranking and show it in the Sprint 10 demo",
                f"{sprint_text(11)}: prepare the Phase 2 plan, backlog and budget request",
            ]),
            ("h2", "Funding"),
            ("p", f"No additional fee is charged. The effort is drawn from the Phase 1 contingency, so the "
                  f"Phase 1 total stays at {PHASE1_TOTAL}. Hours above the contingency are absorbed by the firm."),
            ("h2", "What does not change"),
            ("bullets", [
                "Terms of the Master Services Agreement",
                "Acceptance of Phase 1 deliverables",
                "The rule that new scope needs a written change order",
            ]),
            ("h2", "Approval"),
            ("p", f"Approved by the client sponsor and the executive sponsor on {CO02_DATE}."),
        ],
    },
    {
        "file": "Rate Card and Pricing Assumptions.pdf",
        "blocks": [
            ("h1", "Rate Card and Pricing Assumptions"),
            ("p", "This rate card lists the fictional hourly rates by role used to price Falcon work for "
                  f"{CLIENT}, with the assumptions behind them. It was prepared in November 2025 and revised on "
                  "5 January 2026 for use in the proposal and statements of work."),
            ("h2", "Hourly rates by role"),
            ("table", ["Role", "Hourly rate", "Notes"],
             [["Executive sponsor", "$320", "Oversight, not billed to the fixed fee"],
              ["Project lead", "$210", "Plan, risks, client management"],
              ["Delivery lead", "$195", "Sprint planning and quality"],
              ["Senior engineer", "$180", "Architecture and core build"],
              ["Engineer", "$150", "Build and test"],
              ["Data analyst", "$140", "Search quality and evaluation"],
              ["Designer", "$135", "Interface and research"],
              ["Quality analyst", "$120", "Testing and defects"]],
             [0.35, 0.2, 0.45]),
            ("h2", "Pricing assumptions"),
            ("bullets", [
                "Rates are fixed for the 2026 calendar year and are in US dollars",
                "A working day is eight hours and a sprint is ten working days",
                "Fixed fees are built from the rates plus a contingency of about 10 percent",
                "Travel is billed at cost and only with client approval",
                "Change orders are priced from these rates with the same contingency",
            ]),
            ("h2", "Out of the rates"),
            ("p", "Cloud hosting, licences for third-party tools and client-side staff time are not included "
                  "and are quoted separately where needed."),
        ],
    },
    {
        "file": "Master Services Agreement Summary.pdf",
        "blocks": [
            ("h1", "Master Services Agreement Summary"),
            ("p", f"This internal digest summarises the umbrella terms of the Master Services Agreement between "
                  f"the firm and {CLIENT}, signed on {MSA_SIGNED}. It is a working summary for the Falcon team "
                  "and does not replace the signed agreement."),
            ("h2", "Key terms"),
            ("table", ["Topic", "Summary"],
             [["Term", "Three years from signature, renewable by written agreement"],
              ["Payment", "Invoices due 30 days from receipt; late amounts accrue modest interest"],
              ["Liability cap", "Fees paid in the 12 months before the claim"],
              ["Intellectual property", "Client owns deliverables; the firm keeps its pre-existing tools"],
              ["Confidentiality", "Mutual, in force for five years after the agreement ends"],
              ["Termination", "Either party on 60 days notice; immediate for material breach"]],
             [0.3, 0.7]),
            ("h2", "How work is ordered"),
            ("p", "Each piece of work is agreed in a statement of work signed under this agreement. Changes to a "
                  "statement of work need a written change order approved by both sponsors."),
            ("h2", "Points the team should remember"),
            ("bullets", [
                "Client data stays in the agreed environment and is not used to train outside models",
                "Subcontractors need prior written consent from the client",
                "Disputes go first to the two sponsors, then to mediation",
                "Insurance certificates are renewed each year by the firm's legal team",
            ]),
        ],
    },
    {
        "file": "Staffing Plan.docx",
        "blocks": [
            ("h1", "Falcon Staffing Plan"),
            ("p", f"This staffing plan shows the roles and monthly allocation for the Falcon team from March to "
                  f"December 2026. It was first drafted on 20 February 2026 and revised on 18 September 2026 "
                  f"for the Phase 2 roles that start on {PHASE2_KICKOFF}."),
            ("h2", "Allocation by month (full-time equivalent)"),
            ("table", ["Role", "Mar-Jul", "Aug-Sep", "Oct-Nov", "Dec"],
             [["Executive sponsor", "0.1", "0.1", "0.1", "0.1"],
              ["Project lead", "0.8", "0.6", "0.8", "0.5"],
              ["Delivery lead", "1.0", "0.8", "1.0", "0.5"],
              ["Engineering", "2.5", "1.5", "3.0", "1.0"],
              ["Data analyst", "1.0", "0.5", "1.0", "0.5"],
              ["Designer", "0.5", "0.3", "0.5", "0.2"],
              ["Quality analyst", "0.5", "0.3", "1.0", "0.3"]]),
            ("h2", "Phase 2 roles"),
            ("bullets", [
                "Engineering: ingestion, search and question answering, and the warehouse migration",
                "Data analyst: search quality measurement and the evaluation question set",
                "Designer: pilot feedback and refinements to the interface",
                "Quality analyst: test plan, user acceptance testing and defect triage",
                "Project lead and delivery lead: plan, budget tracking and steering reporting",
            ]),
            ("h2", "Notes"),
            ("p", "Aug-Sep reflects the reduced bridge-period team under Change Order 02. Allocation in December "
                  "supports the pilot closing report and handover. Dollar amounts by role are held in the "
                  "finance files, not in this plan."),
        ],
    },
]
