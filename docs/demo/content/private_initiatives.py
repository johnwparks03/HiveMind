"""User 1 private files: initiatives (7 files)."""

from facts import PILOT_BUDGET, PILOT_GO_LIVE

FILES = [
    {
        "file": "Knowledge Reuse Pilot - Charter.docx",
        "blocks": [
            ("h1", "Knowledge Reuse Pilot - Charter"),
            ("p", "This charter defines the Knowledge Reuse Pilot, my own initiative to help delivery teams find and reuse "
                  "each other's work. It was started on 6 July 2026 and last revised on 10 October 2026. It records the "
                  f"problem, the pilot scope, the {PILOT_BUDGET} budget request, the timeline to a {PILOT_GO_LIVE} go-live, "
                  "success measures, governance and open items."),
            ("h2", "Problem"),
            ("p", "Delivery teams rebuild proposals, status formats and estimates that a neighbouring team already wrote. "
                  "Searching shared drives by file name finds little, and people rarely know which colleague holds the "
                  "right document. My Falcon work on the Harborview Platform showed the same pattern, so I want to test "
                  "whether a search and question-answering tool changes how often work is reused."),
            ("h2", "The pilot"),
            ("p", "Two delivery teams, 14 pilot users in total, use the tool for their own and teammates' shared documents. "
                  "We measure for four weeks after go-live and compare against a baseline survey taken beforehand."),
            ("h2", "Budget and timeline"),
            ("table", ["Item", "Amount or date", "Notes"], [
                ["Build time", "$12,000", "Configuration, connectors, test data"],
                ["Hosting", "$4,000", "Environment for the pilot period"],
                ["Support", "$6,000", "Help desk cover and training"],
                ["Total request", PILOT_BUDGET, "Sum of the three lines"],
                ["Go-live target", PILOT_GO_LIVE, "Subject to sponsor decision"],
                ["Measurement", "Four weeks after go-live", "Baseline survey taken first"],
            ]),
            ("h2", "Success measures"),
            ("bullets", [
                "Estimated time saved of 3 hours per person per month, valued at $75 per hour.",
                "Break-even at about 7 months on those assumptions.",
                "At least 10 of 14 users report finding a document they would not otherwise have found.",
                "Repeat use by 10 of 14 users in each of the four measured weeks.",
            ]),
            ("h2", "Governance"),
            ("p", "I sponsor the work day to day as initiative owner. The Executive sponsor decides funding. The Finance "
                  "business partner reviews the budget lines. Weekly checkpoints run for the four measurement weeks, "
                  "with a results summary to the sponsor after the last one."),
            ("h2", "Open items"),
            ("bullets", [
                "Sponsor decision on funding is still pending.",
                "Choice of the two pilot teams is not final.",
                "Data-handling review of which document types may be shared.",
            ]),
        ],
    },
    {
        "file": "Knowledge Reuse Pilot - Business Case.pptx",
        "slides": [
            {"title": "Knowledge Reuse Pilot", "subtitle": "Business case for the Executive sponsor - 29 September 2026"},
            {"title": "The Problem", "bullets": [
                "Teams rebuild documents a colleague already wrote because they cannot find them.",
                "File-name search misses most relevant work held on other people's laptops.",
                "Nobody measures how often work is reused, so the cost stays invisible.",
            ]},
            {"title": "The Pilot", "bullets": [
                "Two delivery teams and 14 users use search and question answering over shared documents.",
                "Private files stay private; only files a user shares are visible to teammates.",
                "Four weeks of measurement after go-live, compared with a baseline survey.",
            ]},
            {"title": "The Cost", "bullets": [
                f"Total request: {PILOT_BUDGET}.",
                "Build time $12,000, hosting $4,000, support $6,000.",
                "No spend before the sponsor signs off the request.",
            ]},
            {"title": "The Benefit", "bullets": [
                "Assumption: 3 hours saved per person per month at $75 per hour.",
                "14 users give about $3,150 of time value per month.",
                "Break-even in about 7 months; the pilot tests whether the assumption holds.",
            ]},
            {"title": "The Risks", "bullets": [
                "Low adoption if the tool is slower than asking a colleague.",
                "Sensitive documents shared by mistake; mitigated by a clear publish step.",
                "Hours-saved estimate rests on self-reported survey data.",
            ]},
            {"title": "Decisions Asked", "bullets": [
                f"Approve the {PILOT_BUDGET} budget request.",
                f"Agree a go-live target of {PILOT_GO_LIVE}.",
                "Nominate the two pilot teams.",
            ]},
        ],
    },
    {
        "file": "Pilot Pitch Talking Points.txt",
        "text": """PILOT PITCH TALKING POINTS

Prepared 5 to 8 October 2026 for my conversation with the Executive sponsor about the Knowledge Reuse Pilot. These are my own prompts, not a script.

5 OCTOBER - POINTS TO MAKE
- Open with the problem in one sentence: teams rebuild work that already exists elsewhere in the practice.
- Link it to Falcon. The Harborview Platform showed what search over shared work looks like, and Phase 2 is already moving toward a two-team Ask pilot in Sprint 14.
- The ask is small and bounded: a $22,000 pilot, two teams, 14 users, four weeks of measurement.
- Lead with the numbers: 3 hours saved per person per month at $75 per hour, break-even around 7 months.
- Stress privacy. Private files are never uploaded; users choose what to share.
- Close with the decision: approve the budget and a go-live target of 15 December 2026.

6 OCTOBER - LIKELY OBJECTIONS AND ANSWERS
Objection: Three hours a month is a guess.
Answer: Agreed. That is why the pilot has a baseline survey and four measured weeks. If the real figure is lower we stop.

Objection: Why not wait until Falcon Phase 2 finishes?
Answer: The pilot uses the same technology but a different audience, and the lessons arrive sooner if we start in December.

Objection: Is this a distraction from the client work?
Answer: The effort is separate from Falcon staffing. Build time is charged to the pilot budget, not the engagement.

Objection: What if people share the wrong files?
Answer: Sharing is a deliberate step per folder, and the data-handling review is an open item I will close before go-live.

7 OCTOBER - PREPARATION
- Rehearsed the cost slide with the Finance business partner; the three budget lines add to the total.
- Need one concrete story of a reused document. Pull an example from my own notes.

8 OCTOBER - AFTER A DRY RUN
- Cut the risks to three. Lead with adoption, not technology.
- Do not promise a date before the funding decision.
- Follow up in writing the same day with the one-page charter.
""",
    },
    {
        "file": "Stakeholder Map.docx",
        "blocks": [
            ("h1", "Stakeholder Map - Knowledge Reuse Pilot"),
            ("p", "This map lists the people and groups whose support the Knowledge Reuse Pilot needs, drafted from 12 August "
                  "to 22 September 2026. For each stakeholder, identified by role only, it records interest, influence and "
                  "my planned approach. I use it to decide whom to brief first and what each person will ask."),
            ("table", ["Stakeholder (role)", "Interest", "Influence", "Approach"], [
                ["Executive sponsor", "Return on spend, practice reputation", "High", "Short business case, decision meeting, written follow-up"],
                ["Finance business partner", "Clean budget lines, approval route", "Medium", "Walk through cost table before the sponsor sees it"],
                ["Delivery lead (User 2)", "Team capacity, Falcon priorities", "Medium", "Explain that pilot work sits outside Falcon staffing"],
                ["Client sponsor", "Confidentiality of client material", "Medium", "Keep client documents out of scope; share the data-handling rules"],
                ["Practice lead for learning", "Reuse of methods and templates", "High", "Offer pilot results for the practice knowledge programme"],
                ["Candidate pilot team leads", "Time cost for their teams", "Medium", "Keep onboarding under one hour per person"],
                ["Information security contact", "Where data is stored and who sees it", "High", "Share architecture note and the publish model early"],
                ["Engineers on Falcon", "Technical credibility", "Low", "Invite informal feedback"],
            ]),
            ("h2", "Notes from 22 September"),
            ("bullets", [
                "The information security contact and the Executive sponsor are the two gates; brief them first.",
                "The Finance business partner prefers to see numbers before the meeting, not in it.",
                "Two candidate teams are interested; neither has confirmed.",
                "Revisit influence ratings after the sponsor conversation.",
            ]),
        ],
    },
    {
        "file": "Draft Pilot Results Summary.docx",
        "blocks": [
            ("h1", "Draft Pilot Results Summary - Template"),
            ("p", "This is a template for the Knowledge Reuse Pilot results summary, prepared on 21 October 2026. The pilot has "
                  "not run yet, so every value in square brackets is a placeholder to be filled in after the four "
                  "measurement weeks. It exists so the reporting structure is agreed before any data arrives."),
            ("h2", "Headline"),
            ("p", "[Insert one sentence: did teams reuse more work, and was the 3 hours per person per month assumption met?]"),
            ("h2", "Participation"),
            ("table", ["Measure", "Baseline", "Result"], [
                ["Pilot users active in week 1", "[n/a]", "[number] of 14"],
                ["Pilot users active in week 4", "[n/a]", "[number] of 14"],
                ["Searches per user per week", "[baseline survey]", "[value]"],
                ["Documents reused from a teammate", "[baseline survey]", "[value]"],
            ]),
            ("h2", "Time saved"),
            ("bullets", [
                "Self-reported hours saved per person per month: [value] against an assumption of 3.",
                "Value at $75 per hour: [value] per month for 14 users.",
                "Revised break-even against the original estimate of about 7 months: [value].",
            ]),
            ("h2", "What worked and what did not"),
            ("bullets", [
                "[Top three things users liked, with quotes if permitted.]",
                "[Top three problems, each with a proposed fix.]",
            ]),
            ("h2", "Recommendation"),
            ("p", "[Choose one: extend, expand to more teams, adjust and re-run, or stop. Give the reason and the cost.]"),
            ("h2", "Sign-off"),
            ("p", "[Initiative owner, date] and [Executive sponsor decision, date]."),
        ],
    },
    {
        "file": "Initiative Idea Backlog.txt",
        "text": """INITIATIVE IDEA BACKLOG

My running list of ideas for improving how the practice works, kept from 20 January to 15 October 2026. One line per idea, with a note on why it matters or what stopped it.

20 JAN
- Reusable proposal answer library. Note: the same five questions appear in every bid.
- Shared glossary of client terms. Note: new joiners ask the same things in week one.

3 FEB
- Template for a one-page decision log. Note: Falcon will need one; maybe it becomes the standard.

24 FEB
- Lunch-and-learn on estimation mistakes. Note: ask the Delivery lead whether they would present.

30 MAR
- Practice innovation pitch about searching past project work. Note: started drafting the deck, see Practice Innovation Proposal.

14 APR
- Pitched the idea to the practice. Feedback was positive, no budget. Parked until there is evidence from real use.

19 MAY
- Demo day where teams show unfinished work. Note: low cost, needs a sponsor.

6 JUL
- Started the Knowledge Reuse Pilot charter. Note: the Falcon search tool is the obvious test bed.

11 AUG
- Retrospective summary format that links lessons to the next sprint backlog. Note: borrowed from Falcon's Sprint 8 session.

12 AUG
- Stakeholder map for the pilot. Started today.

16 SEP
- Onboarding checklist for new project leads. Note: write it from my own first month.

29 SEP
- Business case deck done. Idea: add a one-page FAQ for sceptics.

8 OCT
- Short note on what a data-handling review for shared files should cover. Note: needed before go-live.

15 OCT
- Personal rule: no new ideas until the pilot decision is made. Keep this list for after.
""",
    },
    {
        "file": "Practice Innovation Proposal.pptx",
        "slides": [
            {"title": "Searching Past Work", "subtitle": "Practice innovation proposal - drafted 30 March, presented 14 April 2026"},
            {"title": "The Opportunity", "bullets": [
                "Each project produces documents that later projects could reuse.",
                "Most of it sits in personal folders and is hard to find by name alone.",
                "A search tool across shared work could shorten the start of every engagement.",
            ]},
            {"title": "What We Heard", "bullets": [
                "Informal chats with six colleagues; five said they had rebuilt something that already existed.",
                "Typical reason given: I did not know who had it.",
                "Teams want control over what they share.",
            ]},
            {"title": "The Idea", "bullets": [
                "Search my own files first, then metadata of files colleagues choose to share.",
                "Ask questions and get answers with a link to the source document.",
                "Keep private files on the owner's machine.",
            ]},
            {"title": "A Small Proof", "bullets": [
                "Use the Falcon engagement as the first real set of documents.",
                "Show three example searches in a ten minute demo.",
                "No new budget; use existing project time to prepare the demo.",
            ]},
            {"title": "Risks", "bullets": [
                "People may not trust a tool with their documents.",
                "Poor search results would hurt credibility quickly.",
                "Effort could compete with client delivery.",
            ]},
            {"title": "Next Steps", "bullets": [
                "Collect questions from the practice after the pitch.",
                "Agree two volunteer teams for a later trial.",
                "Return with evidence from Falcon once Phase 1 closes.",
            ]},
        ],
    },
]
