"""User 2 (Delivery lead) public discovery files for the Falcon demo."""

from facts import CLIENT

FILES = [
    {"file": "Current-State Assessment.docx", "blocks": [
        ("h1", "Current-State Assessment"),
        ("p", f"This assessment describes how {CLIENT} staff find documents and past project knowledge today, based on fieldwork from 12 March to 2 April 2026. "
              "It records the tools in use, the gaps we observed and the baseline we will measure the Harborview Platform against. Prepared by the Delivery lead (User 2)."),
        ("h2", "Scope and method"),
        ("p", "We observed 14 staff across operations, customer service, finance, IT and the warehouse office, shadowed six real searches and reviewed the shared drive structure "
              "with the Client delivery lead. Fieldwork ran from 12 March; findings were confirmed with the Client sponsor on 2 April 2026."),
        ("h2", "Where documents live"),
        ("bullets", [
            "Departmental shared drives with folder trees that differ by team and have no naming standard.",
            "Email attachments and personal mailbox folders, which hold the only copy of many quotes and customer letters.",
            "A chat tool where files are posted in channels and quickly buried.",
            "The CRM, which holds account notes and some contracts but is searched by customer name only.",
            "Individual laptops: downloads folders and desktop files that nobody else can see.",
        ]),
        ("h2", "How people search today"),
        ("p", "Staff first ask a colleague, then browse the shared drive, then use the drive search box, which matches file names only. Several people keep personal bookmarks "
              "or spreadsheets of useful file locations. Nobody can search inside documents across more than one system at a time."),
        ("h2", "Gaps"),
        ("table", ["Gap", "Evidence", "Impact"], [
            ["No content search across sources", "All six shadowed searches crossed two or more tools", "Repeat work and slow answers"],
            ["Inconsistent naming and versions", "Nine of 14 staff keep their own copies", "Out-of-date documents reused"],
            ["Knowledge held by individuals", "Staff named the same four colleagues as the people to ask", "Single points of failure"],
            ["No sharing control by choice", "Staff avoid shared folders for drafts", "Useful drafts stay hidden"],
        ], ),
        ("h2", "Baseline"),
        ("p", "Staff reported spending about 3 hours a week looking for documents, and an average of 22 minutes for a search that crosses more than one tool. "
              "These self-reported figures are the baseline for Phase 1 acceptance."),
    ]},
    {"file": "Discovery Findings Report.pdf", "blocks": [
        ("h1", "Discovery Findings Report"),
        ("p", f"This report presents the discovery findings and recommendations for the Falcon knowledge-search platform for {CLIENT}, covering the discovery period "
              "from 3 to 10 April 2026. It combines the current-state assessment, 14 stakeholder interviews and benchmarking of generic search approaches, "
              "and was prepared by the Delivery lead (User 2) for the Client sponsor and steering committee."),
        ("h2", "Key findings"),
        ("bullets", [
            "Knowledge is spread over five sources (shared drives, email, chat, CRM, laptops) and no single search covers them.",
            "Staff spend about 3 hours a week finding documents; the cost is highest in operations and customer service.",
            "Most people trust a document they can open and read more than a ranking score; they want to see why a result matched.",
            "Staff share only finished work today. They said they would share drafts if they could choose per file and withdraw it later.",
            "File names are the main way people recognise a document, so name-based matching must stay in the first release.",
        ]),
        ("h2", "Recommendations"),
        ("table", ["Ref", "Recommendation", "Priority"], [
            ["R1", "Search the user's own files first, then teammates' shared files", "High"],
            ["R2", "Let each user mark files public or private per folder and per file", "High"],
            ["R3", "Generate short tags from file content to improve matching", "Medium"],
            ["R4", "Add question answering over shared documents after search is trusted", "Medium"],
            ["R5", "Integrate the CRM for account notes after the core search works", "Low"],
        ], [0.1, 0.7, 0.2]),
        ("h2", "Risks"),
        ("bullets", [
            "Adoption: staff may not publish files unless sharing is easy and reversible.",
            "Content quality: duplicate and outdated files will surface unless age is visible in results.",
            "Client data: private files must never leave the user's laptop without an explicit choice.",
        ]),
        ("h2", "Next steps"),
        ("p", "The steering committee will confirm scope for Phase 1 in the Statement of Work. Delivery will start sprint planning for the Harborview Platform "
              "with Sprint 1 beginning on 20 April 2026."),
    ]},
    {"file": "User Interview Synthesis.docx", "blocks": [
        ("h1", "User Interview Synthesis"),
        ("p", f"This synthesis groups what we heard in 14 discovery interviews with {CLIENT} staff between 20 March and 1 April 2026, organised by theme and by role. "
              "It supports the Current-State Assessment and the Discovery Findings Report and was prepared by the Delivery lead (User 2) with two analysts."),
        ("h2", "Who we interviewed"),
        ("table", ["Role group", "Interviews", "Main need"], [
            ["Operations planners", "4", "Find past route and carrier agreements quickly"],
            ["Customer service", "3", "Find the last letter or quote sent to a customer"],
            ["Finance and procurement", "3", "Locate contracts, rate sheets and approvals"],
            ["IT and data", "2", "Find system documentation and runbooks"],
            ["Warehouse office", "2", "Find site procedures and safety documents"],
        ]),
        ("h2", "Theme 1: finding things takes too long"),
        ("p", "Nine interviewees described a search that starts in one tool and ends by asking a colleague. Operations planners said the same document exists in three versions."),
        ("h2", "Theme 2: trust and freshness"),
        ("bullets", [
            "People want to see the owner and the last modified date before they open a result.",
            "Customer service staff will not reuse a letter unless they know it is the current one.",
        ]),
        ("h2", "Theme 3: control over sharing"),
        ("p", "Eleven of 14 said they would share more if they could keep some files private and remove a shared file at any time. Finance staff were the most cautious."),
        ("h2", "Theme 4: answers, not only files"),
        ("p", "Several managers asked whether the tool could answer a question in plain words and point to the source document. Interviewees were clear that "
              "an answer without a source would not be trusted."),
        ("h2", "Implications"),
        ("bullets", [
            "Show owner, date and location with every result.",
            "Per-file public and private control is a core requirement, not an extra.",
            "Plan question answering as a second step after search.",
        ]),
    ]},
    {"file": "Benchmarking Notes - Search Tools.txt", "text": """BENCHMARKING NOTES - SEARCH TOOLS

Topic: comparison of generic search approaches for the Falcon knowledge-search discovery. Period 24 March to 8 April 2026. Kept by the Delivery lead (User 2). No named products are compared; we looked at approach types only.

APPROACHES COMPARED
A. File-name search (what the shared drive offers today)
B. Keyword full-text index over document content
C. Semantic (embedding) search over document content
D. Hybrid: keyword plus semantic with a name boost

24 MARCH 2026
Set up a sample set of 120 documents from the shared drive (contracts, procedures, letters). Wrote 20 test questions with known answers, agreed with the Client delivery lead.

27 MARCH 2026
Approach A found the right file in the first five results for 6 of 20 questions. File names are often generic ("Final v3"). Approach B scored 12 of 20; it misses questions phrased differently from the document.

31 MARCH 2026
Approach C scored 15 of 20. It handles paraphrased questions well but sometimes ranks a general document above a specific one. Embeddings are cheap to compute on a laptop for a few thousand files.

2 APRIL 2026
Approach D scored 17 of 20. A boost for matches on the file name fixed most of the cases where C ranked a general document first. Notes from interviews say people recognise files by name, which supports D.

6 APRIL 2026
Looked at privacy implications. Searching content on the user's own laptop avoids sending private files anywhere. For teammates' files, searching names and short tags only is the least invasive starting point.

8 APRIL 2026
Summary for the findings report:
- Name-only search is not enough; semantic plus name boost gave the best results on the sample.
- Content search should run where the files are, and only metadata is searched centrally.
- Question answering should be treated as a separate feature after search.

OPEN QUESTIONS
- How many chunks per document are needed for long PDFs?
- What age and owner details should be shown with results?
- How to rank a teammate's file against the user's own file on the same topic?
"""},
    {"file": "Vendor Evaluation - Vector Store.txt", "text": """VENDOR EVALUATION - VECTOR STORE

STATUS: DRAFT, 11 MAY 2026. Not reviewed by the Client delivery lead. Decision not recorded.

Topic: options for storing and searching document embeddings for the Harborview Platform. Prepared by the Delivery lead (User 2) while Change Order 01 (CRM integration) was being approved. This draft has not been updated since the options were first written down.

OPTIONS
A. Managed vector index: a separate hosted vector search service.
B. Vector extension on the existing Postgres cluster: add vector columns to the database the platform already uses.
C. Local index in the agent: each laptop keeps its own embedding index and nothing is stored centrally.

CRITERIA
1. Cost at demo scale (a few thousand files, a handful of teams)
2. Operational effort for a small team
3. Fit with the existing database and security model
4. Support for per-team access control
5. Ability to answer questions over teammates' documents
6. Time to build

NOTES
A. Managed vector index
- Scales well and has good tooling, but adds a new service, a new bill and a second place to apply team access rules.
- Extra effort to keep it in step with the file registry (publish, unpublish, delete).

B. Vector extension on the existing Postgres cluster
- Reuses the cluster, backups and access control we already run. Deleting a file can remove its vectors in the same transaction.
- Fine for this scale; would need review if the data grows by a factor of 100.
- Needs the extension enabled and tested on the chosen database version.

C. Local index in the agent
- Strongest privacy and no central cost. Already needed on each laptop for the user's own files.
- Cannot answer from teammates' documents unless the laptop is online, which does not meet criterion 5.

SCORING (1 low, 5 high, rough)
A: cost 2, effort 2, fit 2, access control 3, team answers 4, time 2
B: cost 4, effort 4, fit 5, access control 5, team answers 4, time 4
C: cost 5, effort 4, fit 3, access control 2, team answers 1, time 5

LEANING
Option B looks the best fit. Keep option C for each user's own files.

TO DO
- Confirm extension support on the database version.
- Review with the Client delivery lead and the Project lead (User 1).
- Record the decision in the Decision Log.
"""},
]
