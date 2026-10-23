"""User 1 public files: Meetings (steering, discovery, status notes, retrospectives)."""

from facts import (
    APPROVAL_DATE, CLIENT, CO01_AMOUNT, CO01_DATE, PHASE1_TOTAL, PHASE2_BUDGET, PHASE2_KICKOFF,
    SOW1_VALUE, sprint_text,
)

FILES = [
    {
        "file": "Steering Minutes 2026-06-15.docx",
        "blocks": [
            ("h1", "Falcon Steering Committee Minutes - 15 June 2026"),
            ("p", f"Minutes of the Falcon steering committee meeting held on 15 June 2026, the mid-Phase 1 "
                  f"review for {CLIENT}. The meeting reviewed progress against the Phase 1 plan, confirmed "
                  f"that Change Order 01 (CRM integration, approved {CO01_DATE}) is in effect, discussed "
                  f"risks and recorded decisions and actions."),
            ("h2", "Attendees"),
            ("table", ["Role", "Attendance"], [
                ["Executive sponsor", "Present (chair)"],
                ["Client sponsor", "Present"],
                ["Client delivery lead", "Present"],
                ["Project lead (User 1)", "Present"],
                ["Delivery lead (User 2)", "Present"],
                ["Finance business partner", "Present"],
            ]),
            ("h2", "Progress"),
            ("bullets", [
                f"Phase 1 (SOW value {SOW1_VALUE}, plus {CO01_AMOUNT} from Change Order 01, total {PHASE1_TOTAL}) "
                "is on budget with 44 percent of funds consumed.",
                f"{sprint_text(5)} started today; Sprints 1 to 4 delivered 31 of 36 committed stories.",
                "Nightly ingest of the shared drive is running for four of six source libraries.",
                "The CRM connector (CO01) passed its first read-only test on 9 June against the sandbox.",
            ]),
            ("h2", "Risks discussed"),
            ("bullets", [
                "R-04 Source permissions: two libraries have inconsistent access lists. Owner: Client delivery lead.",
                "R-07 Search relevance on scanned PDFs is below target. Owner: Delivery lead (User 2).",
                "R-09 Sandbox availability for the CRM system is limited to weekdays. Owner: Project lead (User 1).",
            ]),
            ("h2", "Decisions"),
            ("bullets", [
                "Continue with the current Phase 1 scope; no further scope changes are expected in Phase 1 delivery.",
                "Scanned PDFs will be handled by an OCR pass in Sprint 7 rather than excluded.",
                "The next steering meeting is set for July at the Executive sponsor's discretion.",
            ]),
            ("h2", "Actions"),
            ("table", ["ID", "Action", "Owner", "Due"], [
                ["A-21", "Reconcile access lists for the two libraries", "Client delivery lead", "26 June 2026"],
                ["A-22", "Publish OCR approach note", "Delivery lead (User 2)", "3 July 2026"],
                ["A-23", "Confirm sandbox hours with CRM vendor", "Project lead (User 1)", "22 June 2026"],
                ["A-24", "Circulate finance summary", "Finance business partner", "19 June 2026"],
            ]),
        ],
    },
    {
        "file": "Steering Minutes 2026-09-14.docx",
        "blocks": [
            ("h1", "Falcon Steering Committee Minutes - 14 September 2026"),
            ("p", f"Minutes of the Falcon steering committee meeting held on {APPROVAL_DATE}. The committee "
                  f"approved the Phase 2 budget of {PHASE2_BUDGET}, set the Phase 2 kickoff for "
                  f"{PHASE2_KICKOFF}, changed the steering cadence and recorded actions for the start of Phase 2 "
                  f"of the Harborview Platform for {CLIENT}."),
            ("h2", "Attendees"),
            ("table", ["Role", "Attendance"], [
                ["Executive sponsor", "Present (chair)"],
                ["Client sponsor", "Present"],
                ["Client delivery lead", "Present"],
                ["Project lead (User 1)", "Present"],
                ["Delivery lead (User 2)", "Present"],
                ["Finance business partner", "Present"],
            ]),
            ("h2", "Decisions"),
            ("bullets", [
                f"Phase 2 budget of {PHASE2_BUDGET} approved on {APPROVAL_DATE}, unanimously.",
                f"Phase 2 kickoff, and the start of {sprint_text(12)}, confirmed for {PHASE2_KICKOFF}.",
                "Monthly steering meetings move to the first Monday of each month, starting 5 October 2026.",
                "A contingency of 5 percent of the approved budget is held by the Executive sponsor and released "
                "only with written approval.",
            ]),
            ("h2", "Context"),
            ("p", f"The Phase 1 total was {PHASE1_TOTAL}. The bridge period (Sprints 9 to 11) ran at no added fee "
                  "under Change Order 02 and closes on 18 September 2026. The Finance business partner confirmed "
                  "that Phase 1 invoices are reconciled and that the Phase 2 budget is funded for the full period."),
            ("h2", "Risks noted"),
            ("bullets", [
                "Warehouse system cutover is planned for early November and depends on the data migration rehearsal.",
                "Pilot teams for Ask must be named by the Client sponsor by the end of September.",
            ]),
            ("h2", "Actions"),
            ("table", ["ID", "Action", "Owner", "Due"], [
                ["A-31", "Sign the Phase 2 Statement of Work", "Client sponsor", "16 September 2026"],
                ["A-32", "Issue the Phase 2 kickoff invitation", "Project lead (User 1)", "16 September 2026"],
                ["A-33", "Name two pilot teams", "Client sponsor", "30 September 2026"],
                ["A-34", "Set up contingency approval route", "Finance business partner", "25 September 2026"],
            ]),
        ],
    },
    {
        "file": "Client Workshop Notes - Discovery.docx",
        "blocks": [
            ("h1", "Client Workshop Notes - Discovery"),
            ("p", f"Notes from the discovery workshop held on 18 March 2026 with {CLIENT} at the start of "
                  "Phase 1. They capture how staff search for information today, the pain points raised, the "
                  "needs expressed and the priorities agreed, and they feed the Harborview Platform requirements."),
            ("h2", "Attendees"),
            ("p", "Client sponsor, Client delivery lead, six client analysts and operations staff, Project lead "
                  "(User 1) and Delivery lead (User 2). The session ran for three hours."),
            ("h2", "Current search pain points"),
            ("bullets", [
                "Documents live in six places (two shared drives, a wiki, email archives, a CRM and local laptops).",
                "Staff report spending about 4 hours a week looking for prior work, mostly by asking colleagues.",
                "Keyword search misses documents when the file name does not match the topic.",
                "Old versions are found more often than the current one.",
                "People do not know what teammates already hold on their own machines.",
            ]),
            ("h2", "Needs"),
            ("bullets", [
                "One search box across all sources, with results ranked by relevance and recency.",
                "Answers with a source, not just a file list.",
                "Respect for existing permissions; private files must stay private.",
                "A way to request a file from the owner when it is not centrally stored.",
            ]),
            ("h2", "Priorities agreed"),
            ("table", ["Priority", "Item", "Phase"], [
                ["1", "Cross-source search with permission checks", "Phase 1"],
                ["2", "Tagging of documents by topic", "Phase 1"],
                ["3", "Question answering over documents (Ask)", "Phase 2"],
                ["4", "CRM records in results", "To be assessed"],
            ]),
            ("h2", "Follow-ups"),
            ("bullets", [
                "Client delivery lead to share the inventory of sources by 27 March 2026.",
                "Delivery lead (User 2) to draft the current-state assessment by 2 April 2026.",
                "Project lead (User 1) to book stakeholder interviews follow-ups with the operations team.",
            ]),
        ],
    },
    {
        "file": "Stakeholder Interview Notes.txt",
        "text": """STAKEHOLDER INTERVIEW NOTES - DISCOVERY

Falcon stakeholder interviews held 9 to 13 March 2026 with Brightwater Logistics, ahead of the discovery workshop. Purpose: understand how people find information today, what they expect from the Harborview Platform and what worries them. Quotes are paraphrased and unattributed beyond role.

9 March 2026 - Client sponsor (30 minutes)
Wants a visible win within one quarter. Expects the platform to reduce duplicate effort between regional teams. Worried about cost creep and asked for a clear change-control route. Sees success as "people stop asking in chat before searching".

10 March 2026 - Client delivery lead (45 minutes)
Owns the source systems. Concerned that permissions differ between the two shared drives and that nobody has a full map. Offered an engineer for two days a week. Wants nightly refresh, not real time.

11 March 2026 - Operations analyst (30 minutes)
Searches daily. Keeps a personal spreadsheet of useful documents because search fails. Would use a tool that explained why a result matched. Dislikes tools that return forty results with no ranking.

11 March 2026 - Customer success manager (30 minutes)
Needs customer history fast before calls. Information sits in the CRM and in old proposals. Interested in CRM records appearing in search; unsure about data sensitivity.

12 March 2026 - Warehouse systems lead (45 minutes)
Runtime documents change during the warehouse system migration planned for later in the year. Wants to be sure search will not show retired procedures. Asked who owns freshness.

12 March 2026 - Finance analyst (30 minutes)
Looks for contract terms and past budgets. Often finds the draft rather than the signed version. Asked for signed documents to rank first.

13 March 2026 - Information security representative (45 minutes)
Requires that private files are never uploaded and that access is logged. Will review the design before anything touches client data. Prefers a short review early over a long one late.

Themes across interviews
- Trust: people need to see the source and the date.
- Freshness: retired and draft documents cause rework.
- Permissions: nobody wants a surprise exposure.
- Adoption: results must beat asking a colleague.

Next steps
Synthesis goes into the discovery workshop on 18 March 2026. Open question: who owns document freshness after go-live.
""",
    },
    {
        "file": "Weekly Status Notes - Q2 2026.txt",
        "text": """WEEKLY STATUS NOTES - Q2 2026

Falcon weekly status for Brightwater Logistics, 6 April to 26 June 2026. Written by the Project lead (User 1). Phase 1 runs from kickoff on 2 March 2026 to 7 August 2026. Sprint 1 starts 20 April 2026; sprints are two weeks.

06 Apr 2026
Discovery wrap-up. Current-state assessment in review. Environment access still pending for two libraries. Status: amber.

13 Apr 2026
Backlog drafted, 41 stories. Definition of done agreed. Architecture options reviewed with the Client delivery lead. Status: green.

20 Apr 2026 (Sprint 1, week 1)
Sprint 1 started. Goal: ingest one shared drive and return a first search result. Team of five engineers and analysts on site.

27 Apr 2026 (Sprint 1, week 2)
First end-to-end search working on sample data. Two stories slipped to Sprint 2. Status: green.

04 May 2026 (Sprint 2, week 1)
Sprint 1 demo to the client delivery lead went well. Relevance tuning starts. CRM integration request raised by the client sponsor.

11 May 2026 (Sprint 2, week 2)
Change Order 01 approved today: CRM integration, +$6,800, bringing Phase 1 to $38,300. Two engineer-weeks reallocated. Status: green.

18 May 2026 (Sprint 3, week 1)
Sprint 2 closed with 12 of 13 stories. Tagging prototype running on 300 documents.

25 May 2026 (Sprint 3, week 2)
Access list mismatch found on one library (risk R-04). Client delivery lead investigating. Status: amber.

01 Jun 2026 (Sprint 4, week 1)
Sprint 3 closed. Four of six libraries now ingest nightly. Test plan draft shared for comment.

08 Jun 2026 (Sprint 4, week 2)
CRM connector read-only test passed against the sandbox. Scanned PDFs flagged as a relevance risk (R-07).

15 Jun 2026 (Sprint 5, week 1)
Steering committee held. CO01 in effect, scope unchanged, spend 44 percent. Actions A-21 to A-24 logged. Status: green.

22 Jun 2026 (Sprint 5, week 2)
OCR approach drafted. Sandbox hours confirmed with the CRM vendor. Sprint 6 planning scheduled for 26 June.

26 Jun 2026 (end of Sprint 5)
Sprint 5 closed with 11 of 12 stories. Sprint 6 (29 June to 10 July) goal: tagging at scale and a demo. Q2 summary: three milestones met, one risk open (R-04).
""",
    },
    {
        "file": "Weekly Status Notes - Q3 2026.txt",
        "text": """WEEKLY STATUS NOTES - Q3 2026

Falcon weekly status for Brightwater Logistics, 3 July to 25 September 2026. Written by the Project lead (User 1). Covers the end of Phase 1 (7 August), the bridge period (Sprints 9 to 11, 10 August to 18 September) and the start of Phase 2.

03 Jul 2026 (Sprint 6, week 1)
Sprint 6 in progress. Tagging runs on 2,100 documents. OCR pass designed. Status: green.

10 Jul 2026 (end of Sprint 6)
Sprint 6 demo held today. Client sponsor asked for a retention view of stale documents. Status: green.

17 Jul 2026 (Sprint 7, week 1)
OCR pass live for scanned PDFs. Security review pack sent to the information security representative.

24 Jul 2026 (Sprint 7, week 2)
Sprint 7 closed. Relevance on the test set up to 81 percent for the first answer. Security review summary agreed.

31 Jul 2026 (Sprint 8, week 1)
Sprint 8 is the last Phase 1 sprint. Handover notes started. Phase 1 closure plan circulated.

03 Aug 2026 (Sprint 8, week 2)
Change Order 02 signed: a bridge period for Sprints 9 to 11 at no added fee, funded from Phase 1 contingency.

07 Aug 2026 (Sprint 8 ends)
Phase 1 ended. Sprint 8 retrospective held. Final Phase 1 total $38,300.

14 Aug 2026 (Sprint 9, week 1)
Executive readout held on 12 August. Phase 2 proposal well received. Lessons learned deck drafted.

21 Aug 2026 (Sprint 9, week 2)
Sprint 9 closed. Bridge team reduced to three people. Phase 2 statement of work drafting begins.

28 Aug 2026 (Sprint 10, week 1)
Phase 2 kickoff deck drafting. Sprint 10 demo prepared.

04 Sep 2026 (end of Sprint 10)
Sprint 10 demo held. Question answering prototype shown for the first time.

11 Sep 2026 (Sprint 11, week 1)
Steering pre-read issued. Budget request ready for approval.

14 Sep 2026
Steering committee approved the Phase 2 budget of $48,200. Kickoff set for 21 September.

18 Sep 2026 (end of Sprint 11)
Bridge period closed. Staffing plan updated for Phase 2.

25 Sep 2026 (Sprint 12, week 1)
Phase 2 kickoff held on 21 September and Sprint 12 started. Goal: ingest pipeline hardening and Ask chunk upload. Status: green.
""",
    },
    {
        "file": "Sprint 8 Retrospective.txt",
        "text": """SPRINT 8 RETROSPECTIVE

Retrospective for Sprint 8 (27 July to 7 August 2026), held on 7 August 2026. This was the last sprint of Phase 1 of the Falcon engagement for Brightwater Logistics, which ended the same day. Purpose: capture what worked, what to change and the actions for the bridge period and Phase 2.

Attendees: Project lead (User 1), Delivery lead (User 2), four engineers, two analysts, Client delivery lead (guest for the first half).

Sprint summary
- Committed 14 stories, completed 13. One story (retention view) moved to the bridge period.
- Defect count at close: 6 open, none severe.
- Phase 1 budget finished at $38,300, as planned after Change Order 01.

What went well
- Handover notes were written during the sprint, not after it.
- The OCR pass removed the main relevance complaint from the client.
- Pairing between data and engineering sped up the tagging fixes.
- The security review closed without rework.
- Change Order 02 gave the team a clear plan for the next five weeks.

What to improve
- Stories for the CRM connector were too large; two of them carried across three sprints.
- Test data refresh was manual and took half a day each time.
- Client feedback arrived late in the sprint, after the demo rather than before.
- Risk register updates lagged behind weekly status notes.
- Too many meetings in the last three days of the sprint.

Actions
A-41  Split any story over five points before planning. Owner: Delivery lead (User 2). Due: bridge Sprint 9.
A-42  Automate test data refresh. Owner: engineer. Due: 21 August 2026.
A-43  Share the demo build with the client two days early. Owner: Project lead (User 1). Due: every sprint.
A-44  Update the risk register on Fridays. Owner: Project lead (User 1). Due: weekly.
A-45  No new meetings in the last two days of a sprint. Owner: Delivery lead (User 2). Due: 10 August 2026.

Team mood: 4 out of 5. Next retrospective: Sprint 10, 4 September 2026.
""",
    },
    {
        "file": "Sprint 12 Retrospective.txt",
        "text": """SPRINT 12 RETROSPECTIVE

Retrospective for Sprint 12 (21 September to 2 October 2026), held on 2 October 2026. Sprint 12 was the first sprint of Phase 2 of the Falcon engagement for Brightwater Logistics. Purpose: record what went well and what to change before Sprint 13, and agree actions.

Attendees: Project lead (User 1), Delivery lead (User 2), five engineers, two analysts, one designer.

Sprint summary
- Goal: harden the ingest pipeline and upload chunks for Ask. Goal met.
- Committed 16 stories, completed 15. One deferred: dashboard export.
- Phase 2 kickoff took place on 21 September; the team grew from three (bridge) to eight.
- Phase 2 budget of $48,200 is tracked weekly by the Finance business partner.

What went well
- Kickoff was clear: every person knew the Sprint 12 goal on day one.
- The two new engineers were productive in the first week because of the environment guide.
- Chunk upload retries behaved correctly in failure tests.
- Daily stand-ups stayed at fifteen minutes.
- The client named pilot teams early, ahead of the 30 September action date.

What to improve
- Definition of done was applied unevenly for design stories.
- Staging environment was unavailable for most of Wednesday 30 September.
- Demo scope for Sprint 14 is still vague; two stakeholders hold different expectations.
- Backlog refinement happened too late in the week.
- Defects found in Sprint 11 were not triaged until Sprint 12.

Actions
A-51  Add a design checklist to the definition of done. Owner: designer. Due: 9 October 2026.
A-52  Agree a staging environment on-call rota. Owner: Delivery lead (User 2). Due: 6 October 2026.
A-53  Write a one-page scope for the Sprint 14 demo. Owner: Project lead (User 1). Due: 16 October 2026.
A-54  Move refinement to Tuesdays. Owner: Delivery lead (User 2). Due: 5 October 2026.
A-55  Triage defects within two days of discovery. Owner: engineer. Due: ongoing.

Team mood: 4 out of 5. Next retrospective: Sprint 13, 16 October 2026.
""",
    },
]
