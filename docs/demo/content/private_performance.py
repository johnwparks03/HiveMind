"""User 1 private files: performance (10 files). Content covers User 1 only."""

from facts import APPROVAL_DATE, PHASE2_BUDGET, PILOT_BUDGET, sprint_text

FILES = [
    {
        "file": "Performance Review Tracker 2026.txt",
        "text": f"""PERFORMANCE REVIEW TRACKER 2026

My running log for the 2026 performance year, kept from 5 January to 18 October 2026. It records my three goals, check-ins and feedback worth remembering, so the year-end review does not rely on memory.

GOALS
G1 Lead the Harborview search and Ask pilot to a working demo.
G2 Build the Falcon Phase 2 delivery plan.
G3 Complete the firm data-handling training.

5 JAN
Goals agreed with my manager. G1 and G2 are the core of the year; G3 is mandatory.

14 JAN
First check-in. Manager asked for a written plan for G1 by the end of the month.

2 MAR
Falcon Phase 1 kicked off. Noted the team structure for later evidence.

12 MAR
G3 done. Completed the firm data-handling training today and saved the certificate.

11 MAY
Change order for the CRM integration signed. Good example of scope control for the self-review.

15 JUN
Steering committee went well. Client sponsor said the roadmap was clear.

25 JUN
H1 self-review submitted. Rated myself strong on delivery, developing on delegation.

10 JUL
Sprint 6 demo delivered. Feedback from the client delivery lead was positive.

12 AUG
Phase 1 executive readout presented. Started the Phase 2 plan the same week.

{APPROVAL_DATE.upper().replace("SEPTEMBER", "SEP")}
Steering approved the Phase 2 budget of {PHASE2_BUDGET}. G2 is substantially done; the plan now needs to be delivered.

21 SEP
Phase 2 kicked off. Sprint 12 started.

9 OCT
Feedback from manager: strong on structure, should hand off more day-to-day tracking.

18 OCT
Sprint 14 is about to start with the goal of piloting Ask for two teams. G1 is on track for the demo, not yet complete. Draft of the H2 self-review begins next week.
""",
    },
    {
        "file": "Goal Tracking.docx",
        "blocks": [
            ("h1", "Goal Tracking 2026"),
            ("p", "This document tracks my three 2026 performance goals, how each is measured and where it stood at the last revision "
                  "on 1 September 2026. It was created on 5 January 2026 and is the reference I use when preparing check-ins "
                  "and self-reviews."),
            ("table", ["Goal", "Measure", "Status at 1 Sep", "Next step"], [
                ["G1 Lead the Harborview search and Ask pilot to a working demo",
                 "Working demo accepted by the Client sponsor; pilot with two teams scheduled",
                 "On track. Phase 1 demos delivered; Ask in test", "Prepare the two-team pilot plan"],
                ["G2 Build the Falcon Phase 2 delivery plan",
                 "Plan agreed with client and approved by steering",
                 "Plan drafted and in review; budget decision expected mid-month", "Support the steering meeting"],
                ["G3 Complete firm data-handling training",
                 "Certificate on the learning record", "Complete (12 March 2026)", "None, renew next year"],
            ]),
            ("h2", "Evidence collected"),
            ("bullets", [
                "Sprint 6 demo deck and the positive client feedback that followed.",
                "Change Order 01 and the bridge period change order, both agreed without dispute.",
                "Phase 1 executive readout with a clear Phase 2 recommendation.",
                "Certificate for the data-handling training.",
            ]),
            ("h2", "Risks to the goals"),
            ("bullets", [
                "Phase 2 approval timing could compress the plan before Sprint 12.",
                "My own time is split between delivery and the initiative work I started in July.",
            ]),
            ("h2", "Notes"),
            ("p", "I will revisit the measures after the steering meeting in September. If the pilot date moves, G1 stays valid "
                  "but its target date needs agreeing with my manager."),
        ],
    },
    {
        "file": "Feedback Log.txt",
        "text": """FEEDBACK LOG

Feedback I have received in 2026, logged from 12 January to 9 October with the source role and theme. I record the substance, not exact wording.

12 JAN | Manager | Theme: planning
Strong first week of planning. Asked me to write down assumptions earlier.

9 FEB | Executive sponsor | Theme: communication
Status updates are clear but arrive late on Mondays. Move them to Friday afternoon.

17 MAR | Client delivery lead | Theme: collaboration
Appreciated that I involved their team in the discovery workshop rather than presenting at them.

22 APR | Delivery lead | Theme: delegation
Suggested I let engineers own sprint review notes. I tend to rewrite them.

20 MAY | Client sponsor | Theme: stakeholder management
Praised the handling of the CRM change order. Wants advance warning of any scope question.

16 JUN | Executive sponsor | Theme: leadership
Steering committee preparation was thorough. Encouraged me to be more direct about risks.

10 JUL | Client delivery lead | Theme: delivery
The Sprint 6 demo showed real progress. Asked for a shorter version for their leadership.

13 AUG | Manager | Theme: strategy
Readout was well structured. Next step is showing commercial thinking beyond the plan.

22 SEP | Finance business partner | Theme: budgeting
Budget packs are easy to review. Wants a variance line by role in future packs.

9 OCT | Manager | Theme: delegation
Strong on structure, but should hand off day-to-day tracking so I have time for the initiative.

PATTERNS
- Delegation appears three times and is my main development theme.
- Clear structure and calm client handling appear most often as strengths.
- Commercial thinking is a newer theme and links to my promotion case.
""",
    },
    {
        "file": "1-1 Notes With Manager 2026.txt",
        "text": """1-1 NOTES WITH MANAGER 2026

Dated notes from my one-to-one meetings with my manager, 14 January to 14 October 2026. Used to track agreed actions and what was said about my goals, development and workload.

14 JAN
- Reviewed goals. G1 and G2 confirmed as priority.
- Action (me): write a plan for G1 by 30 January.

11 FEB
- Discussed utilisation. Target is 80 percent for the quarter.
- Manager suggested I find a mentor outside the project.

18 MAR
- Data-handling training done. Manager asked about my interest in the cloud certification.
- Action (manager): check the learning budget.

15 APR
- Talked about the Sprint 1 plan. Concern about my team's capacity.
- Action (me): propose a staffing change.

27 MAY
- Talked about the CRM change order as a good example for my review.
- Manager asked about my longer-term plans; I said I want to move toward leading engagements.

24 JUN
- Reviewed the H1 self-review before submission. Manager suggested adding numbers to the achievements.

22 JUL
- Development plan updated. Added presentation skills.
- Manager mentioned the promotion cycle opens in the autumn.

26 AUG
- Discussed starting a promotion case draft. Evidence needed on commercial impact.

16 SEP
- Phase 2 approval celebrated. Manager asked how I will staff the pilot work.
- Action (me): bring a draft initiative proposal in October.

14 OCT
- Talked about the pilot idea and its funding request. Manager supportive but wants the sponsor conversation to happen first.
- Reminded me to delegate more of the status tracking.
- Action (me): share the H2 self-review draft by the end of October.
""",
    },
    {
        "file": "Development Plan.docx",
        "blocks": [
            ("h1", "Development Plan 2026"),
            ("p", "This plan sets out the skills I want to build in 2026, the actions that will build them and when each is due. "
                  "It was written on 8 January 2026 and revised on 15 July 2026, and I review it with my manager and mentor "
                  "during the year."),
            ("table", ["Skill", "Action", "Timeline", "Status at 15 Jul"], [
                ["Delegation", "Hand over sprint review notes and tracking to engineers", "From April", "In progress"],
                ["Commercial thinking", "Join budget reviews with the Finance business partner", "Q2 to Q4", "Started"],
                ["Cloud fundamentals", "Study for the cloud practitioner style certification", "March to May", "Done; exam passed"],
                ["Presentation skills", "Give a talk to the practice on a delivery lesson", "Q3", "Proposed"],
                ["Data handling", "Complete firm data-handling training", "By March", "Done 12 March"],
            ]),
            ("h2", "Why these skills"),
            ("p", "Delegation and commercial thinking appear in feedback and are the gaps most likely to block a move toward leading "
                  "engagements. Cloud fundamentals and presentation skills support the Harborview work and my wish to speak "
                  "more broadly about how teams reuse knowledge."),
            ("h2", "Support needed"),
            ("bullets", [
                "Time protected for study, agreed with my manager.",
                "Learning budget for the certification fee.",
                "Regular sessions with my mentor.",
            ]),
            ("h2", "July revision"),
            ("p", "Added presentation skills after my manager's feedback. Moved delegation to the top because it came up in three "
                  "separate check-ins. Removed a planned course on estimation because the Falcon work covers it in practice."),
        ],
    },
    {
        "file": "Utilisation and Hours Notes.txt",
        "text": """UTILISATION AND HOURS NOTES

Weekly notes on my target and actual utilisation, kept from February to 16 October 2026, with the reasons for any gap. Target is stated as a percentage of available hours.

WEEK OF 2 FEB - Target 80 percent, actual 62 percent. Waiting for Falcon contract paperwork. Used time for proposal clean-up.

WEEK OF 16 FEB - Target 80, actual 75. Prepared Phase 1 plan.

WEEK OF 2 MAR - Target 80, actual 88. Phase 1 kickoff week; long days.

WEEK OF 23 MAR - Target 80, actual 84. Discovery workshops.

WEEK OF 20 APR - Target 80, actual 82. Sprint 1 started.

WEEK OF 11 MAY - Target 80, actual 90. CRM change order and extra planning. Flagged to manager.

WEEK OF 8 JUN - Target 80, actual 78. Two days used for the self-review and training.

WEEK OF 29 JUN - Target 80, actual 83. Sprint 6 demo preparation.

WEEK OF 3 AUG - Target 80, actual 70. Between phases; started the Phase 1 readout.

WEEK OF 10 AUG - Target 80, actual 77. Bridge period began.

WEEK OF 14 SEP - Target 80, actual 85. Phase 2 approval and kickoff preparation.

WEEK OF 21 SEP - Target 80, actual 86. Phase 2 kickoff and Sprint 12.

WEEK OF 5 OCT - Target 80, actual 81. Sprint 13 steady; started drafting the initiative proposal after hours, not billed.

WEEK OF 12 OCT - Target 80, actual 84. Go-live readiness work ahead of Sprint 14.

16 OCT SUMMARY
- Average actual over the logged weeks is about 80 percent, in line with the target.
- Peaks in kickoff and change-order weeks; dips between phases.
- Initiative work is not counted in utilisation and I should keep it separate.
""",
    },
    {
        "file": "H1 2026 Self-Review.docx",
        "blocks": [
            ("h1", "H1 2026 Self-Review"),
            ("p", "This self-review covers my work from January to June 2026 and was written between 2 and 25 June 2026 for the "
                  "mid-year review with my manager. It lists my achievements, progress against goals and development areas."),
            ("h2", "Achievements"),
            ("bullets", [
                "Led the Falcon Phase 1 kickoff on 2 March 2026 and set up the team and governance.",
                "Managed Change Order 01 for the CRM integration, agreed on 11 May 2026 without delay to the plan.",
                "Facilitated the discovery workshop with the Brightwater Logistics team.",
                "Prepared and ran the steering committee on 15 June 2026.",
                "Completed the firm data-handling training on 12 March 2026.",
            ]),
            ("h2", "Progress against goals"),
            ("p", "G1 is on track: sprints began on 20 April and the first demo is planned for July. G2 has started as the Phase 2 "
                  "outline, and G3 is complete. I do not yet have a Phase 2 budget agreed."),
            ("h2", "Development areas"),
            ("bullets", [
                "Delegation. I rewrite engineers' notes and should let them own more.",
                "Commercial thinking. I want to understand margin and pricing in more detail.",
                "Visibility. Share more of the team's work with the wider practice.",
            ]),
            ("h2", "Plans for H2"),
            ("p", "Deliver the Sprint 6 demo, close Phase 1, present the readout and secure the Phase 2 plan. I also want to "
                  "build a case for reuse of project knowledge across teams."),
        ],
    },
    {
        "file": "H2 2026 Self-Review - Draft.docx",
        "blocks": [
            ("h1", "H2 2026 Self-Review - Draft"),
            ("p", "This is a draft self-review covering July to October 2026, written between 19 and 21 October 2026 ahead of the "
                  "year-end review. It lists achievements, current goal status and development areas, and is not final."),
            ("h2", "Achievements"),
            ("bullets", [
                "Delivered the Sprint 6 demo on 10 July 2026 and the Phase 1 executive readout on 12 August 2026.",
                f"Secured approval of the Falcon Phase 2 budget of {PHASE2_BUDGET} on {APPROVAL_DATE}, and kicked off Phase 2 on 21 September.",
                f"Committed the team to {sprint_text(14)}, with the goal of piloting Ask for two teams.",
                f"Drafted the Knowledge Reuse Pilot charter and a business case requesting {PILOT_BUDGET}; the decision is still pending.",
            ]),
            ("h2", "Goals"),
            ("p", "G1 remains in progress: the demo to the Client sponsor and the pilot with two teams are still ahead. G2 is complete "
                  "in the sense that the plan was approved, though delivery continues. G3 was finished in March."),
            ("h2", "Development areas"),
            ("bullets", [
                "Delegation: improved on sprint notes, still holding on to status tracking.",
                "Commercial thinking: joined budget reviews; need to show it in the initiative case.",
                "Balancing the initiative against delivery without letting utilisation drop.",
            ]),
            ("h2", "Open points before submitting"),
            ("bullets", [
                "Add numbers to each achievement as my manager asked.",
                "Do not claim pilot results; the pilot has not started.",
                "Check wording with my mentor.",
            ]),
        ],
    },
    {
        "file": "FY25 Annual Review Summary.pdf",
        "blocks": [
            ("h1", "FY25 Annual Review Summary"),
            ("p", "This summary records my annual performance review for the 2025 financial year, completed on 18 August 2025. It "
                  "sets out my rating, strengths, development areas and the goals proposed for FY26, and I keep it as a "
                  "baseline for later reviews."),
            ("table", ["Area", "Summary"], [
                ["Overall rating", "Meets expectations, strong in delivery"],
                ["Manager comment", "Reliable, clear communicator, ready for more scope"],
                ["Peer feedback", "Easy to work with; calm under pressure"],
            ], [0.3, 0.7]),
            ("h2", "Strengths"),
            ("bullets", [
                "Structured planning and clear written updates.",
                "Calm handling of client questions.",
                "Good judgement on when to escalate.",
            ]),
            ("h2", "Development areas"),
            ("bullets", [
                "Delegation: take on a wider role rather than doing the work personally.",
                "Commercial awareness: understand pricing and margin.",
                "Visibility beyond the project.",
            ]),
            ("h2", "Goals for FY26"),
            ("bullets", [
                "Lead a client engagement from kickoff to demo.",
                "Complete the firm data-handling training.",
                "Build a first mentoring relationship.",
            ]),
            ("p", "These goals became the starting point for the 2026 goal setting in January."),
        ],
    },
    {
        "file": "Promotion Case Draft.docx",
        "blocks": [
            ("h1", "Promotion Case Draft"),
            ("p", "This draft makes the case for my promotion at the next cycle. It was started on 25 August 2026 and last revised "
                  "on 12 October 2026. It sets out the structure of the case, evidence by competency and the gaps I still need "
                  "to close before submitting."),
            ("h2", "Case structure"),
            ("p", "Three parts: scope of the role I already perform, impact on clients and the practice, and readiness for the next "
                  "level. Each uses specific examples from 2026 only."),
            ("table", ["Competency", "Evidence", "Strength"], [
                ["Delivery", "Phase 1 delivered to plan; Sprint 6 demo and readout", "Strong"],
                ["Client relationships", "Steering committee; change order handled without friction", "Strong"],
                ["Commercial", f"Phase 2 budget of {PHASE2_BUDGET} approved on {APPROVAL_DATE}", "Medium"],
                ["Leadership", "Led a team through two phases; mentoring one junior colleague", "Medium"],
                ["Innovation", "Knowledge reuse initiative; practice pitch in April", "Developing"],
            ]),
            ("h2", "Gaps"),
            ("bullets", [
                "Commercial impact is thin: I need evidence of margin or revenue effect, not only budget approval.",
                "Delegation: the 9 October feedback says I still hold on to tracking.",
                "The initiative has no results yet; it cannot be used as evidence of impact until measured.",
            ]),
            ("h2", "Next steps"),
            ("bullets", [
                "Ask the Finance business partner for a view on the Phase 2 margin.",
                "Hand over tracking and record the outcome.",
                "Share a draft with my mentor before the manager.",
            ]),
        ],
    },
]
