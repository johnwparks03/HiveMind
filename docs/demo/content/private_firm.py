"""User 1 private files: generic firm policy and reference documents."""

from facts import EXPENSE_THRESHOLD

FILES = [
    {
        "file": "Expense Policy Summary FY27.pdf",
        "blocks": [
            ("h1", "Expense Policy Summary - FY27"),
            ("p", "This summary sets out the firm's expense rules for financial year 2027, effective 1 July 2026 and prepared by Firm Finance on 15 June 2026. It explains what needs approval before you spend, what receipts to keep, how quickly to submit a claim and when a late claim needs an exception."),
            ("h2", "Pre-approval"),
            ("p", f"Any single purchase or expense above {EXPENSE_THRESHOLD} needs written manager pre-approval before the money is spent. Approval is requested by email or in the expense tool and must name the amount, the purpose and the engagement code. Client-billable spend above {EXPENSE_THRESHOLD} also needs the engagement lead to confirm the client has agreed to reimburse it."),
            ("h2", "Receipts and submission"),
            ("bullets", [
                "A receipt or itemised invoice is required for every item over $25.",
                "Items of $25 or less need a short description but no receipt.",
                "Claims must be submitted within 30 days of the expense date.",
                "Claims submitted more than 90 days after the expense date need a finance exception approved by the Finance business partner before they can be paid.",
            ]),
            ("h2", "Corporate cards"),
            ("p", "Corporate cards are issued to staff who travel regularly. Use the card for travel, accommodation and client meals only, never for personal items. Card transactions still need a receipt and must be matched to a claim within 30 days of the statement date. Lost or stolen cards must be reported to Firm Finance on the same day."),
            ("h2", "What is not reimbursed"),
            ("bullets", [
                "Alcohol, except where a client host has agreed to it as part of a hosted meal.",
                "Fines, penalties and parking tickets.",
                "Personal entertainment, gifts above the firm gift limit and family travel.",
            ]),
            ("h2", "Questions"),
            ("p", "Contact the Finance business partner for your engagement. Exceptions are recorded and reviewed each quarter. This summary does not replace the full Travel and Expenses Guide, which covers booking, mileage and daily allowances."),
        ],
    },
    {
        "file": "Travel and Expenses Guide FY27.pdf",
        "blocks": [
            ("h1", "Travel and Expenses Guide - FY27"),
            ("p", "This guide covers how to book and claim business travel in financial year 2027: booking channels, mileage, daily allowances, rail and taxi use. It was issued on 15 June 2026 and revised on 1 July 2026 for the new mileage rate, and applies to all staff travelling for client or firm business."),
            ("h2", "Booking"),
            ("bullets", [
                "Book flights, rail and hotels through the firm travel portal at least 14 days ahead where possible.",
                "Economy class applies to all domestic flights. Flights over 6 hours may use premium economy with manager approval.",
                "Hotels must be on the preferred list unless none is within reasonable distance of the client site.",
                "Spend above the pre-approval threshold in the Expense Policy Summary still needs manager approval before booking.",
            ]),
            ("h2", "Mileage"),
            ("p", "Personal car mileage is reimbursed at $0.70 per mile from 1 July 2026. Record the start point, end point, purpose and miles driven for each trip. Commuting from home to your usual office is not claimable."),
            ("h2", "Daily allowance"),
            ("table", ["Meal or item", "Domestic rate", "Notes"], [
                ["Breakfast", "$18", "Only if not provided by the hotel"],
                ["Lunch", "$22", "Per working day away from base"],
                ["Dinner", "$45", "Overnight stays only"],
                ["Incidentals", "$10", "Per night away"],
            ], [0.3, 0.25, 0.45]),
            ("h2", "Rail and taxi"),
            ("p", "Standard class rail is the default. Use taxis or ride share only when public transport is unavailable, when travelling with heavy equipment, or after 9 pm. Keep the receipt and note the reason on the claim. Airport transfers should use rail or the shuttle where one exists."),
            ("h2", "Claiming"),
            ("p", "Submit travel claims within 30 days of return. Attach receipts for every item over $25 and a mileage log where applicable."),
        ],
    },
    {
        "file": "Client Confidentiality Reminder.txt",
        "text": """CLIENT CONFIDENTIALITY REMINDER

Issued 1 December 2025 by Firm Information Security. This reminder explains what the firm expects of every employee when handling client information, in the office, at the client site and while working remotely. It applies to all engagements and to everyone who works on them, including contractors.

WHAT COUNTS AS CONFIDENTIAL
Anything you learn about a client through your work is confidential unless the client has said otherwise in writing. That includes contracts and pricing, project plans, data extracts, system details, organisation charts, people matters and the existence of the engagement itself where the client has asked for discretion.

WHAT TO DO
- Store client material only in approved firm or client-provided locations. Do not use personal email, personal cloud storage or removable drives.
- Share files on a need-to-know basis. Check the recipient list before you send, especially when replying to a group.
- Lock your screen whenever you step away. Do not discuss client matters in lifts, cafes, trains or other public places.
- Label documents with the client sensitivity marking given in the engagement kickoff pack.
- Use only approved collaboration tools for calls and chat with client staff.

WHAT NOT TO DO
- Do not reuse one client's material in work for another client without the engagement lead's written approval, even if the content has been anonymised.
- Do not post about client work on social media, including the fact that you work with a named client.
- Do not take client data off the client network unless the contract allows it and the data is encrypted.

SEPARATING ENGAGEMENTS
Where one team works for clients who compete with each other, the engagement lead sets up information barriers. Follow them and raise any doubt early.

IF SOMETHING GOES WRONG
Report a lost device, a misdirected email or any suspected leak to Firm Information Security within one hour of noticing. Early reporting protects you and the client. Nobody is penalised for reporting a mistake promptly; concealing one is a conduct matter.

OBLIGATIONS CONTINUE
Your duty of confidentiality continues after an engagement ends and after you leave the firm. Questions go to your engagement lead or the Information Security desk.
""",
    },
    {
        "file": "Timekeeping Guidelines.pdf",
        "blocks": [
            ("h1", "Timekeeping Guidelines"),
            ("p", "These guidelines explain how staff record time against client and internal work. They were first issued on 2 September 2025 and revised on 5 January 2026 and cover entry deadlines, time codes and how to correct an entry after it has been submitted."),
            ("h2", "Weekly entry"),
            ("bullets", [
                "Enter your time daily where you can. The weekly timesheet must be complete by 5 pm on the Friday of each week.",
                "A standard week is 40 hours. Record actual hours, including overtime, rather than rounding to 40.",
                "Time is recorded in quarter-hour units against an engagement code and a task code.",
                "Managers approve submitted timesheets by noon on the following Tuesday.",
            ]),
            ("h2", "Time codes"),
            ("table", ["Code type", "Example", "Use for"], [
                ["Client", "Engagement code from the kickoff pack", "Billable and non-billable client work"],
                ["Internal", "INT-ADMIN", "Firm administration, expenses, timesheets"],
                ["Development", "INT-LEARN", "Training and certification study"],
                ["Business development", "INT-BD", "Proposals and pitch preparation"],
                ["Leave", "LV-ANNUAL", "Annual leave, public holidays, sick leave"],
            ], [0.2, 0.4, 0.4]),
            ("h2", "Corrections"),
            ("p", "Corrections before manager approval can be made directly in the timesheet. After approval, raise a correction request with the reason and the engagement lead's agreement. Corrections to a closed month need approval from the Finance business partner and are logged for audit."),
            ("h2", "Late timesheets"),
            ("p", "Late entries delay client invoicing. Repeated late submission is raised with your manager and may affect utilisation reporting. If you are on leave on the deadline, submit the week before you go."),
            ("h2", "Accuracy"),
            ("p", "Entering time you did not work, or entering work against the wrong client, is a conduct matter. If you are unsure which code applies, ask your engagement lead before you submit."),
        ],
    },
    {
        "file": "Remote Work Policy.pdf",
        "blocks": [
            ("h1", "Remote Work Policy"),
            ("p", "This policy describes when and how employees may work away from a firm or client office. It was issued on 10 November 2025 by Firm HR and revised on 1 April 2026, and covers eligibility, core hours, equipment, security expectations and working from another location."),
            ("h2", "Eligibility and approach"),
            ("p", "Most roles may work remotely up to three days a week, agreed with the engagement lead and the line manager. Client contracts can require on-site days; those requirements come first. Remote arrangements are reviewed at least once a year."),
            ("h2", "Core hours and availability"),
            ("bullets", [
                "Core hours are 10 am to 3 pm local time, when you should be reachable for meetings.",
                "Keep your calendar current and mark when you are away from your desk.",
                "Attend team ceremonies and client meetings with camera on unless the organiser says otherwise.",
            ]),
            ("h2", "Equipment and workspace"),
            ("p", "The firm provides a laptop, a monitor on request and a one-off home office allowance of $250 for new remote workers. Use a private space for calls so client matters cannot be overheard. Do not use public wifi without the firm VPN."),
            ("h2", "Working from another location"),
            ("table", ["Situation", "Rule"], [
                ["Another city, same country", "Up to 10 days a year with manager approval"],
                ["Another country", "Needs HR and tax review at least 30 days ahead"],
                ["Client site abroad", "Follow the Travel and Expenses Guide and client rules"],
            ], [0.4, 0.6]),
            ("h2", "Security"),
            ("p", "All remote work must follow the IT Security Policy Summary and the Client Confidentiality Reminder. Report a lost or stolen device immediately."),
        ],
    },
    {
        "file": "IT Security Policy Summary.pdf",
        "blocks": [
            ("h1", "IT Security Policy Summary"),
            ("p", "This summary sets out the minimum security practices every employee must follow when using firm systems and devices. It was issued by Firm Information Security on 3 February 2026 and revised on 5 August 2026, and covers passwords, devices, reporting incidents and approved tools."),
            ("h2", "Passwords and sign-in"),
            ("bullets", [
                "Use a passphrase of at least 14 characters. Never reuse a firm password elsewhere.",
                "Multi-factor authentication is required for email, the VPN and all client systems.",
                "Store passwords only in the approved password manager. Never share them, even with a manager.",
            ]),
            ("h2", "Devices"),
            ("p", "Firm laptops are encrypted and managed. Install operating system updates within 7 days of release and restart when prompted. Do not disable antivirus or the firewall. Personal devices may be used only for email and calendar through the approved mobile app, never for client files."),
            ("h2", "Approved tools"),
            ("table", ["Purpose", "Approved tool"], [
                ["Email and calendar", "Firm email service"],
                ["Chat and calls", "Firm collaboration suite"],
                ["File storage", "Firm file store and client-provided storage"],
                ["Source code", "Firm code repository"],
                ["AI assistants", "Only firm-approved assistants; never paste client data into public tools"],
            ], [0.4, 0.6]),
            ("h2", "Reporting incidents"),
            ("p", "Report a lost device, phishing click, misdirected message or suspected breach to the Information Security desk within one hour of noticing. Do not try to fix it yourself or delete evidence. Reports can be made by phone at any time."),
            ("h2", "Phishing"),
            ("p", "Check the sender and the link before opening attachments. Use the report button in your mail client for anything suspicious. Quarterly phishing tests are run, and results are used for training, not discipline."),
        ],
    },
    {
        "file": "Code of Conduct Summary.pdf",
        "blocks": [
            ("h1", "Code of Conduct Summary"),
            ("p", "This summary, issued by Firm HR on 15 July 2025, describes the standards of behaviour the firm expects from every employee and contractor in dealings with colleagues, clients and the public. It is a short guide to the full Code of Conduct and applies on engagements and in the office."),
            ("h2", "Our principles"),
            ("bullets", [
                "Act with integrity: be honest in your work, your time entries and your expense claims.",
                "Respect others: no harassment, discrimination or bullying, in person or online.",
                "Protect information: keep client and firm information confidential.",
                "Be professional: represent the firm well at the client site and in public.",
                "Speak up: raise concerns early and without fear of retaliation.",
            ]),
            ("h2", "Conflicts of interest"),
            ("p", "Declare any personal, financial or family interest that could affect your judgement on an engagement. Declarations go to your manager and are recorded by the Ethics office. Do not accept gifts from clients or suppliers worth more than $100 without approval."),
            ("h2", "Working with clients"),
            ("p", "Be accurate about what the firm can deliver. Do not promise scope, price or dates without the engagement lead's agreement. Treat client staff with the same respect you expect from colleagues."),
            ("h2", "Raising concerns"),
            ("table", ["Route", "Contact"], [
                ["Your manager", "First option for most concerns"],
                ["Firm HR", "Conduct, behaviour or workplace issues"],
                ["Ethics line", "Anonymous reporting, available all day, every day"],
            ], [0.4, 0.6]),
            ("h2", "Consequences"),
            ("p", "Breaches of the Code are handled under the disciplinary procedure and can lead to dismissal. Retaliation against anyone who raises a concern in good faith is itself a breach. Everyone confirms the Code each year."),
        ],
    },
    {
        "file": "Learning Budget Policy.pdf",
        "blocks": [
            ("h1", "Learning Budget Policy"),
            ("p", "This policy, issued by Firm HR on 1 July 2026, explains the annual learning allowance available to every employee in financial year 2027: how much you can spend, what is covered, how to get approval and how to claim. It applies from 1 July 2026 to 30 June 2027."),
            ("h2", "Allowance"),
            ("p", "Each full-time employee has a learning allowance of $2,000 per financial year. Part-time staff receive the allowance pro rata. Unused allowance does not carry over. Staff who join part-way through the year receive a prorated amount."),
            ("h2", "What is covered"),
            ("bullets", [
                "Courses, workshops and conference fees, including online programmes.",
                "Professional certification exams and one retake where the first attempt is unsuccessful.",
                "Books and learning subscriptions related to your role or development plan.",
                "Travel to a learning event, under the Travel and Expenses Guide.",
            ]),
            ("h2", "What is not covered"),
            ("bullets", [
                "Degree programmes, which follow the separate education assistance process.",
                "Memberships that are not tied to a certification.",
                "Equipment, hardware and software licences.",
            ]),
            ("h2", "Approval and claiming"),
            ("p", "Agree the learning with your manager and record it in your development plan. Spend above $500 needs manager pre-approval in line with the Expense Policy Summary. Submit the receipt within 30 days. Time spent on learning is booked to the development code and is limited to 40 hours a year unless your manager agrees more."),
            ("h2", "Repayment"),
            ("p", "If you leave within 12 months of the firm paying for a certification or course over $1,000, part of the cost may be recovered. The Learning team confirms the amount before you enrol."),
        ],
    },
    {
        "file": "Benefits Summary.pdf",
        "blocks": [
            ("h1", "Benefits Summary"),
            ("p", "This summary, issued by Firm HR on 2 January 2026, outlines the main benefits for full-time employees in calendar year 2026: health cover, leave and retirement savings. All figures are illustrative and the plan documents govern if there is any difference."),
            ("h2", "Health and wellbeing"),
            ("table", ["Benefit", "Employee cost", "Firm contribution"], [
                ["Medical plan, individual", "$95 per month", "$520 per month"],
                ["Medical plan, family", "$310 per month", "$900 per month"],
                ["Dental and vision", "$18 per month", "$30 per month"],
                ["Employee assistance programme", "No cost", "Fully paid"],
                ["Wellbeing allowance", "No cost", "$300 per year"],
            ], [0.4, 0.3, 0.3]),
            ("h2", "Leave"),
            ("bullets", [
                "Annual leave: 20 days a year, rising to 25 days after five years.",
                "Public holidays: the firm holiday calendar, plus one floating day.",
                "Sick leave: up to 10 paid days a year; longer absences follow the medical leave policy.",
                "Parental leave: 16 weeks at full pay for the primary carer and 6 weeks for the second carer.",
                "Volunteering: 2 paid days a year.",
            ]),
            ("h2", "Retirement savings"),
            ("p", "The firm matches your retirement contributions dollar for dollar up to 5 percent of base salary. Contributions vest immediately. Enrolment is automatic at 3 percent after 30 days of service, and you can change your rate at any time in the benefits portal."),
            ("h2", "Enrolment and changes"),
            ("p", "Open enrolment runs each November for the following year. Life events such as marriage or a new child allow a change within 30 days. Questions go to the HR benefits desk."),
        ],
    },
    {
        "file": "Firm Org Chart.pdf",
        "blocks": [
            ("h1", "Firm Org Chart"),
            ("p", "This document shows how the firm is organised into practices and teams, who leads each by role, and approximate headcount ranges. It was prepared by Firm Operations on 4 May 2026 and revised on 14 September 2026 to reflect the new Data and Analytics practice structure. No individual names are listed."),
            ("h2", "Practice structure"),
            ("table", ["Practice or team", "Led by", "Headcount range"], [
                ["Executive office", "Managing partner", "5 to 10"],
                ["Consulting practice", "Practice leader", "120 to 160"],
                ["Technology delivery team", "Delivery director", "60 to 80"],
                ["Data and analytics team", "Data director", "30 to 45"],
                ["Design and experience team", "Design director", "15 to 25"],
                ["Project management office", "PMO director", "10 to 20"],
                ["Quality and testing team", "Quality lead", "10 to 15"],
            ], [0.4, 0.3, 0.3]),
            ("h2", "Shared services"),
            ("table", ["Function", "Led by", "Headcount range"], [
                ["Finance", "Finance director", "15 to 25"],
                ["Human resources", "HR director", "10 to 20"],
                ["Information security and IT", "Chief information security officer", "15 to 25"],
                ["Operations and staffing", "Operations director", "10 to 15"],
                ["Learning", "Learning lead", "3 to 6"],
            ], [0.4, 0.3, 0.3]),
            ("h2", "Reporting lines"),
            ("p", "Every employee has a line manager, a counselor for career guidance and one or more engagement leads for client work. Engagement leads report on delivery to a practice leader. Changes in the September 2026 revision moved analytics roles from the Technology delivery team into a separate Data and analytics team."),
            ("h2", "Using this chart"),
            ("p", "For questions on staffing, contact Operations. For policy questions, contact the function named above."),
        ],
    },
    {
        "file": "Staffing and Resourcing Guide.pdf",
        "blocks": [
            ("h1", "Staffing and Resourcing Guide"),
            ("p", "This guide from Firm Operations explains how engagements request people, how roll-offs are handled and how utilisation targets are set. It was issued on 8 December 2025 and revised on 16 March 2026, and is written for engagement leads, managers and staff planning their next assignment."),
            ("h2", "Staffing requests"),
            ("bullets", [
                "Engagement leads raise a staffing request in the resourcing tool at least 3 weeks before the start date.",
                "Each request names the role, grade, skills, start and end dates and the percentage of time required.",
                "Operations proposes candidates within 5 working days and the engagement lead confirms within 3 working days.",
                "Requests for named individuals are considered but not guaranteed.",
            ]),
            ("h2", "Roll-offs"),
            ("p", "Staff roll off an engagement when their planned end date is reached or when scope changes. The engagement lead gives at least 2 weeks notice of a roll-off and updates the resourcing tool the same day. Staff with no assignment are placed on a short bench list and offered internal work first."),
            ("h2", "Utilisation targets"),
            ("table", ["Grade", "Annual target"], [
                ["Analyst", "80 percent"],
                ["Consultant", "78 percent"],
                ["Senior consultant", "75 percent"],
                ["Manager", "70 percent"],
                ["Senior manager", "55 percent"],
            ], [0.5, 0.5]),
            ("p", "Utilisation is billable hours divided by available hours, after leave and public holidays. Hours on internal initiatives and learning are not billable but are tracked."),
            ("h2", "Planning and conflicts"),
            ("p", "Staffing conflicts are resolved by the practice leader. Raise concerns about overallocation with your manager early. Reviews of the resourcing forecast take place every two weeks."),
        ],
    },
    {
        "file": "Practice Holiday Calendar 2027.txt",
        "text": """PRACTICE HOLIDAY CALENDAR 2027

Published 1 October 2026 by Firm Operations. This calendar lists the firm holidays for calendar year 2027 so that engagement leads and staff can plan leave, sprints and client commitments well ahead. All dates are firm-wide unless a client contract says otherwise.

FIRM HOLIDAYS IN 2027
- 1 January, Friday: New Year's Day
- 18 January, Monday: Martin Luther King Jr. Day
- 15 February, Monday: Presidents' Day
- 31 May, Monday: Memorial Day
- 5 July, Monday: Independence Day (observed)
- 6 September, Monday: Labor Day
- 25 November, Thursday: Thanksgiving Day
- 26 November, Friday: Floating day (the firm closes for the day after Thanksgiving)
- 24 December, Friday: Christmas Day (observed)

NOTES
- Independence Day falls on Sunday 4 July in 2027, so the firm observes it on Monday 5 July.
- Christmas Day falls on Saturday 25 December in 2027, so the firm observes it on Friday 24 December.
- New Year's Day 2028 falls on a Saturday. The firm does not observe it on 31 December 2027, so there is no additional closure at year end.
- The floating day is fixed for 2027 as 26 November. Staff also receive one personal floating day each year, booked through the leave tool.

WORKING ON A HOLIDAY
Client-site support rotas may require work on a firm holiday. Time worked is booked as normal and a day in lieu is agreed with your manager within the same quarter. Do not schedule releases, cutovers or demos on a firm holiday without the engagement lead's approval.

PLANNING TIPS
- Several Monday holidays create long weekends: January, February, May, July and September. Expect fewer people at client sites in the week of those holidays.
- The last week of November is short because of Thanksgiving and the floating day. Plan sprint demos and steering meetings accordingly.
- Submit leave requests at least 2 weeks ahead for holiday weeks.

CHANGES
Any change to this calendar is announced by Firm Operations by email and updated on the intranet. Questions go to the Operations desk.
""",
    },
]
