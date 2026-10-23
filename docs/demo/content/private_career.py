"""User 1 private files: career and learning (6 files)."""

FILES = [
    {
        "file": "Certification Study Notes.txt",
        "text": """CERTIFICATION STUDY NOTES

My dated notes for a cloud practitioner style certification, studied from 2 March to 26 May 2026. They cover the main topics I revised and the practice scores I recorded along the way.

2 MAR
Plan: 45 minutes on weekday mornings, a longer block on Saturday. Exam booked for late May. Started with the shared responsibility model: the provider secures the infrastructure, the customer secures what they put on it.

9 MAR
Compute basics. Virtual machines, containers, and functions that run on demand. Remember when each fits: steady load versus spiky load.

16 MAR
Storage types: object, block and file. Object storage for documents and backups, block for disks, file for shared folders. Lifecycle rules move old data to cheaper tiers.

30 MAR
Networking. Private networks, subnets, and how traffic is allowed or blocked. Practice test 1: 62 percent. Weak on networking.

13 APR
Security and identity. Least privilege, multi-factor sign-in, roles instead of long-lived keys. Linked to the firm data-handling training I finished in March.

27 APR
Databases. Relational for structured data with joins, key-value for fast lookups, and why managed services reduce operations work.

11 MAY
Pricing and support. On-demand versus reserved pricing, budgets and alerts, free tiers. Practice test 2: 78 percent.

18 MAY
Full revision of weak areas: networking and pricing. Practice test 3: 84 percent.

25 MAY
Last review. Rested the evening before.

26 MAY
Sat the exam and passed. Plan: add the certificate to my profile and tell my manager. Next topic to study: something on data and analytics, later in the year.
""",
    },
    {
        "file": "Training Transcript.pdf",
        "blocks": [
            ("h1", "Training Transcript"),
            ("p", "This transcript lists the training courses I have completed through the firm's learning system, as at "
                  "30 September 2026. It shows each course, the completion date and the hours credited, and it is kept for "
                  "performance reviews and the promotion case."),
            ("table", ["Course", "Completed", "Hours"], [
                ["Firm data-handling training", "12 March 2026", "3"],
                ["Client confidentiality refresher", "20 January 2026", "1"],
                ["Information security awareness", "4 February 2026", "2"],
                ["Agile delivery for project leads", "24 April 2026", "8"],
                ["Cloud practitioner exam preparation", "26 May 2026", "20"],
                ["Presenting with impact", "14 July 2026", "6"],
                ["Commercial acumen for delivery leaders", "9 September 2026", "7"],
            ], [0.55, 0.3, 0.15]),
            ("h2", "Totals"),
            ("bullets", [
                "Courses completed in 2026: 7.",
                "Total hours credited: 47.",
                "Mandatory courses: all complete.",
            ]),
            ("h2", "In progress"),
            ("p", "No courses are in progress at this date. A data and analytics foundation course is planned for the "
                  "last quarter, subject to the learning budget."),
            ("p", "Issued by Firm Learning. This transcript is a personal record and is not an official certificate."),
        ],
    },
    {
        "file": "Reading Notes.txt",
        "text": """READING NOTES

Notes on articles and books I have read between 25 January and 3 October 2026, with the points I want to remember and what I might apply at work.

25 JAN - Book: a guide to running effective retrospectives
Main idea: keep the format simple and always follow up on one action. Apply: Falcon retrospectives; pick one change per sprint.

14 FEB - Article: why estimates slip
Teams forget integration and review time. Apply: add a line for integration in each sprint plan.

8 MAR - Book: managing technical projects
Useful chapter on stakeholders: map interest against influence. Apply: early version of my stakeholder map idea.

2 APR - Article: writing a decision log
Short entries with the date, decision, reason and owner. Apply: propose the format for Falcon.

19 MAY - Book: making learning stick
Spaced repetition beats cramming; relevant for my cloud study. Apply: weekly review.

30 JUN - Article: how consulting teams lose their own knowledge
Most lessons live in people's heads and leave with them. Apply: link to my reuse idea.

21 JUL - Book: leading without doing everything
Delegation means agreeing outcomes, not tasks. Apply: let engineers own sprint review notes.

15 AUG - Article: pricing change orders fairly
Separate the change from the original scope and show the effect on the plan. Apply: confirmed my approach on the CRM change order.

12 SEP - Article: measuring productivity gains from search tools
Self-reported time savings are noisy; use a baseline survey. Apply: the pilot measurement plan.

3 OCT - Book: telling a story with numbers
One message per slide. Apply: cut the business case to one claim per slide.
""",
    },
    {
        "file": "Mentor Meeting Notes.txt",
        "text": """MENTOR MEETING NOTES

Notes from my sessions with my mentor, a senior leader in another practice, from 10 February to 17 September 2026. Each entry records the advice and any actions for me.

10 FEB - First session
Mentor asked what I want from the relationship. I said confidence leading engagements. Agreed to meet every six weeks.
Action: write down three things I want to be known for.

24 MAR - Second session
Talked about my first month on a large client. Advice: spend time with the client's delivery team informally, not only in meetings.
Action: set up fortnightly coffee with the Client delivery lead.

5 MAY - Third session
Discussed the change order. Advice: bring the client a recommendation, not just options.
Action: rehearse the recommendation before the call.

16 JUN - Fourth session
Reviewed my H1 self-review. Advice: lead with outcomes and numbers.
Action: add figures to each achievement.

28 JUL - Fifth session
Talked about delegation. Advice: write down what good looks like and hand it over once, then review.
Action: delegate sprint review notes by the end of August.

17 SEP - Sixth session
Talked about a possible initiative to help teams reuse documents. Mentor said to test the idea with a small group and measure, not argue it. Also suggested speaking at a practice event.
Actions: draft a talk outline; look for a sponsor before asking for money.

Overall: the mentor repeatedly pushes me to quantify results and to ask for decisions earlier.
""",
    },
    {
        "file": "Resume and Bio.docx",
        "blocks": [
            ("h1", "Resume and Bio"),
            ("p", "This document holds my current resume and a short professional bio. It was created on 20 November 2025 and last "
                  "updated on 1 June 2026, and I use it for internal profiles, proposals and conference submissions."),
            ("h2", "Short bio"),
            ("p", "I am a project lead at the firm with a background in delivery of data and search platforms for logistics and "
                  "professional services clients. I lead cross-functional teams from discovery through demo, and I care about "
                  "helping teams reuse what they already know."),
            ("h2", "Experience"),
            ("bullets", [
                "Project lead, the firm (2026 to present): lead the Falcon engagement for Brightwater Logistics, delivering the "
                "Harborview Platform in two phases.",
                "Senior consultant, the firm (2022 to 2025): delivered analytics and integration work for several clients.",
                "Consultant, the firm (2019 to 2022): joined as a graduate; worked on reporting and process projects.",
            ]),
            ("h2", "Skills"),
            ("bullets", [
                "Delivery planning, steering committee reporting, change control.",
                "Search and retrieval concepts, data handling practice.",
                "Cloud fundamentals (practitioner level certification, May 2026).",
            ]),
            ("h2", "Education and training"),
            ("p", "Bachelor's degree in information systems. Firm training in data handling, agile delivery and presenting."),
        ],
    },
    {
        "file": "Conference Talk Outline.pptx",
        "slides": [
            {"title": "Reusing Team Knowledge", "subtitle": "Talk outline for a practice event - drafted 4 August to 9 September 2026"},
            {"title": "Why This Talk", "bullets": [
                "Every consulting team writes documents that another team later needs.",
                "Most reuse depends on knowing the right person.",
                "The talk shows small steps that make reuse easier.",
            ]},
            {"title": "Where Knowledge Gets Lost", "bullets": [
                "Documents sit in personal folders and project drives.",
                "People leave or move on and take context with them.",
                "Search by file name misses work with unhelpful titles.",
            ]},
            {"title": "What Helps", "bullets": [
                "Short summaries at the top of documents so they can be found.",
                "Consistent file names and a shared place for finished work.",
                "Clear rules on what is shared and what stays private.",
            ]},
            {"title": "A Story From Delivery", "bullets": [
                "A project team reused a change order structure from another engagement.",
                "It saved a day of drafting and avoided known pitfalls.",
                "Nobody recorded the saving, so no one could count it.",
            ]},
            {"title": "How To Measure", "bullets": [
                "Baseline survey before any change.",
                "Count searches, shared documents and documents reused.",
                "Treat self-reported time savings with care.",
            ]},
            {"title": "Takeaways", "bullets": [
                "Start small with one or two teams.",
                "Make sharing a choice, never a default.",
                "Measure before you claim a benefit.",
            ]},
        ],
    },
]
