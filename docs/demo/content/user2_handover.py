"""User 2 public files: Handover (training, guides, support, checklist)."""

from facts import (
    CLIENT, PLATFORM, ASK_TARGET, PILOT_WINDOW, ROLE_DELIVERY_LEAD,
    ROLE_PROJECT_LEAD, ROLE_CLIENT_DELIVERY, sprint_text,
)

FILES = [
    {
        "file": "End-User Training Deck.pptx",
        "slides": [
            {"title": "Harborview Platform Training",
             "subtitle": "For the two pilot teams, October 2026"},
            {"title": "What You Will Learn",
             "bullets": [
                 "Search your own files and your teammates' public files",
                 "Ask a question and read an answer with sources",
                 "Choose which files are public or private",
                 "Know where to get help during the pilot",
             ]},
            {"title": "How Search Works",
             "bullets": [
                 "Your own files are searched first, on your laptop",
                 "If nothing matches well, teammates' public file details are searched",
                 "Results show the file name, owner and tags",
                 "Use Download to request a teammate's file",
             ]},
            {"title": "How Ask Works",
             "bullets": [
                 "Type a question that names a topic, for example a project or a document",
                 "Answers draw on your files and on teammates' public documents",
                 "Every answer lists its sources so you can check it",
                 "Avoid date ranges in the question; they narrow the search to your own files",
             ]},
            {"title": "Public And Private",
             "bullets": [
                 "Private files never leave your laptop",
                 "Public files: teammates can find them and read their text through Ask",
                 "Unpublish a file at any time; its stored text is removed",
                 "Publish only what you are happy for your team to read",
             ]},
            {"title": "Downloading Files",
             "bullets": [
                 "Download works while the owner's laptop is online",
                 "The file passes through a short-lived transfer that is cleared within minutes",
                 "If the owner is offline, try again later or message them",
             ]},
            {"title": "Pilot Support",
             "bullets": [
                 f"The pilot runs {PILOT_WINDOW}",
                 "First line: the support analyst, 08:00 to 17:00 on working days",
                 "Raise issues through the help desk form; never paste document text",
                 "Read the User Guide and FAQ before you ask",
             ]},
            {"title": "Next Steps",
             "bullets": [
                 "Complete the practice exercises after this session",
                 "Mark your first public folder with your team lead",
                 "Send feedback after the first week of the pilot",
             ]},
        ],
    },
    {
        "file": "User Guide.pdf",
        "blocks": [
            ("h1", "Harborview Platform User Guide"),
            ("p", f"This guide explains how to use the {PLATFORM} for the pilot with two teams at {CLIENT}, version of 19 October 2026. "
                  "It covers search, Ask, managing files, publishing and privacy, and is written for pilot users and the support analyst."),
            ("h2", "Search"),
            ("bullets", [
                "Type what you are looking for in plain words and press Enter.",
                "Your own files are searched first. If nothing matches well, details of teammates' public files are searched.",
                "Each result shows the file name, owner, tags and last updated date.",
            ]),
            ("h2", "Ask"),
            ("bullets", [
                "Ask is for questions, such as \"What is the Sprint 14 goal?\".",
                "Name the topic in your question. Questions with no topic, or with a date range, search only your own files.",
                f"The first answer should appear in under {ASK_TARGET}. If it takes longer, tell the support analyst.",
                "Each answer shows its sources. Open the source to check it before you rely on it.",
            ]),
            ("h2", "Your files"),
            ("bullets", [
                "Add a folder in the Files page; supported types are PDF, DOCX, PPTX and TXT.",
                "Files are read in the background. A spinner shows a folder that is still being read.",
                "Select several files and mark them public or private in one step.",
            ]),
            ("h2", "Publishing and privacy"),
            ("table", ["Setting", "What teammates can do", "What leaves your laptop"], [
                ["Private", "Nothing; they cannot see the file", "Nothing"],
                ["Public", "Find it, Ask over its text, request a download", "File details, tags and text chunks"],
            ], [0.2, 0.4, 0.4]),
            ("p", "Public files expire 45 days after publishing and show a warning in the last 7 days. Unpublishing removes the stored text."),
            ("h2", "Getting help"),
            ("p", "See the FAQ first. For problems, use the help desk form; the support analyst answers within the times in the Support Model."),
        ],
    },
    {
        "file": "FAQ.txt",
        "text": """HARBORVIEW PLATFORM FAQ

Frequently asked questions for the two pilot teams. First written 12 October 2026, last updated 20 October 2026. The pilot runs 9 to 27 November 2026. Dated notes at the end record changes.

Q: What can I search?
A: Your own files in the folders you added, and the details of teammates' public files. Supported types are PDF, DOCX, PPTX and TXT.

Q: Who can see my files?
A: Nobody, unless you mark a file public. Private files never leave your laptop.

Q: What happens when I make a file public?
A: Teammates can find it by name and tags, ask questions that use its text, and request a download. The text of the file is stored centrally while it is public.

Q: How do I stop sharing a file?
A: Mark it private or unpublish it. The stored text is removed.

Q: Why did Ask not use my teammate's document?
A: Teammates' files are skipped when the question has no topic, or when it contains a date range. Rephrase the question to name the topic and drop the dates.

Q: How fast should Ask be?
A: The first answer should appear in under 4 seconds. If it is slower, note the time and the question topic and send it to the support analyst.

Q: Why can I not download a file?
A: Downloads need the owner's laptop to be online. Try again later. Ask still works when the owner is offline.

Q: How long do public files stay?
A: 45 days. A warning shows in the last 7 days. Publish again to renew.

Q: A folder is still showing a spinner. Is something wrong?
A: No. The folder is still being read. Large folders take a few minutes.

Q: Where do I report a problem?
A: Use the help desk form. Include the time, what you did and what you saw. Do not paste document text.

Q: Can I use the platform on a phone or Mac?
A: Not in the pilot. Windows laptops only.

UPDATE NOTES
- 2026-10-12: First version written from user interview questions.
- 2026-10-15: Added the question about Ask skipping teammates' documents after pilot rehearsal feedback.
- 2026-10-19: Added the spinner question after the Files page update in the release notes.
- 2026-10-20: Reviewed with the support analyst; wording on downloads clarified.
""",
    },
    {
        "file": "Support Model.docx",
        "blocks": [
            ("h1", "Support Model - Harborview Platform Pilot"),
            ("p", f"This document defines the support model for the Harborview Platform during the pilot with two teams ({PILOT_WINDOW}) and the "
                  "handover period before it, drafted between 28 September and 7 October 2026. It sets out the support tiers, hours, escalation path "
                  "and service levels, and is for the support analyst, engineers and the client delivery team."),
            ("h2", "Tiers"),
            ("table", ["Tier", "Who", "Handles"], [
                ["1", "Support analyst", "How-to questions, access, known issues, defect logging"],
                ["2", "Engineers", "Defects, agent and central service faults, data issues"],
                ["3", ROLE_DELIVERY_LEAD, "Outages, design decisions, anything affecting the cutover or pilot plan"],
            ], [0.10, 0.30, 0.60]),
            ("h2", "Hours"),
            ("bullets", [
                "Tier 1: 08:00 to 17:00 on working days.",
                "Tier 2: 09:00 to 17:00 on working days; one engineer on call outside those hours for severity 1 only.",
                "No weekend cover during the pilot.",
            ]),
            ("h2", "Service levels"),
            ("table", ["Severity", "Example", "Response", "Target fix or workaround"], [
                ["1", "Service down for a whole team", "30 minutes", "4 hours"],
                ["2", "Search or Ask failing for several users", "2 hours", "1 working day"],
                ["3", "A single user cannot publish a file", "1 working day", "3 working days"],
                ["4", "Question or wording change", "2 working days", "Next release"],
            ], [0.12, 0.42, 0.20, 0.26]),
            ("h2", "Escalation"),
            ("bullets", [
                "Tier 1 escalates to Tier 2 when a fix is not known after 30 minutes.",
                "Tier 2 escalates to Tier 3 for any severity 1 not resolved in 2 hours.",
                f"The {ROLE_CLIENT_DELIVERY} is told of every severity 1 and 2 within the response time.",
            ]),
            ("p", "Tickets must not contain document text; use file identifiers. Weekly ticket review happens in the pilot status meeting."),
        ],
    },
    {
        "file": "Handover Checklist.docx",
        "blocks": [
            ("h1", "Handover Checklist - Pilot Readiness"),
            ("p", f"This checklist tracks what must be in place to hand the Harborview Platform to the support team and the two pilot teams, "
                  f"status as of 8 October 2026, during {sprint_text(13).split(':')[0]} planning ahead of the pilot ({PILOT_WINDOW}). "
                  "It lists each item with an owner and status."),
            ("h2", "Checklist"),
            ("table", ["ID", "Item", "Owner", "Status"], [
                ["H-01", "Support Model agreed", ROLE_DELIVERY_LEAD, "Done"],
                ["H-02", "Support analyst onboarded and has dev access", ROLE_DELIVERY_LEAD, "Done"],
                ["H-03", "User Guide first draft", "Analysts", "In progress"],
                ["H-04", "FAQ first draft", "Analysts", "In progress"],
                ["H-05", "End-user training deck", "Analysts", "In progress"],
                ["H-06", "Nightly ingest runbook reviewed with support", "Engineers", "Not started"],
                ["H-07", "Help desk form set up", ROLE_CLIENT_DELIVERY, "In progress"],
                ["H-08", "Pilot user accounts created for both teams", "Engineers", "Not started"],
                ["H-09", "Training sessions booked for both teams", ROLE_PROJECT_LEAD, "Done"],
                ["H-10", "Known issues list published", "Engineers", "Not started"],
            ], [0.09, 0.48, 0.26, 0.17]),
            ("h2", "Notes"),
            ("bullets", [
                "H-03 to H-05 depend on the Sprint 13 build; screenshots will be updated before the training sessions.",
                "H-08 waits for the final list of pilot users from the client delivery lead.",
                "Items not Done by the end of Sprint 14 move to the pilot risk list.",
            ]),
            ("p", f"Checklist owner: {ROLE_DELIVERY_LEAD}. Reviewed weekly until the pilot starts."),
        ],
    },
]
