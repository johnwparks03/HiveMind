"""User 1 private files: personal working files in the project lead's own voice."""

from facts import APPROVAL_DATE, PHASE2_BUDGET, EXPENSE_THRESHOLD, sprint_text

# Draft expense report items: (date, description, category, amount in cents, receipt status)
_EXPENSE_ITEMS = [
    ("7 Oct", "Flight to client site", "Airfare", 21240, "Receipt attached"),
    ("9 Oct", "Return flight", "Airfare", 19860, "Receipt attached"),
    ("7-9 Oct", "Hotel, 2 nights at $168.00", "Lodging", 33600, "Receipt attached"),
    ("7 Oct", "Taxi, airport to hotel", "Ground transport", 3850, "Receipt attached"),
    ("9 Oct", "Taxi, hotel to airport", "Ground transport", 4120, "Receipt attached"),
    ("7 Oct", "Dinner", "Meals", 4275, "Receipt attached"),
    ("8 Oct", "Dinner", "Meals", 4410, "Receipt attached"),
    ("8 Oct", "Working lunch with client delivery lead", "Client meal", 8640, "Receipt attached"),
    ("8 Oct", "Airport parking, one day", "Parking", 2400, "No receipt needed (under $25)"),
    ("7 Oct", "Airport shuttle", "Ground transport", 1450, "Receipt missing, requested"),
]


def _dollars(cents):
    return f"${cents / 100:,.2f}"


_TOTAL = sum(item[3] for item in _EXPENSE_ITEMS)
_LARGEST = max(item[3] for item in _EXPENSE_ITEMS)
assert _LARGEST < 50000, "every draft item must stay under the pre-approval threshold"

FILES = [
    {
        "file": "Town Hall Notes - September 2026.txt",
        "text": """TOWN HALL NOTES - SEPTEMBER 2026

My notes from the firm town hall on Thursday 24 September 2026. I took these for my own reference and to brief the team on Monday. Topics: the firm's year so far, the new practice structure, the learning allowance, and Q and A.

OPENING (managing partner)
- Revenue and utilisation are slightly ahead of plan for the first half of FY27. Pipeline for the second half looks healthy, especially in data and analytics work.
- Thanked delivery teams for steady quality through the summer. Client satisfaction scores are up on last year.

PRACTICE STRUCTURE
- The Data and analytics team is now its own team, reporting to the Data director. The org chart was updated on 14 September. Our analysts do not change engagement, only reporting line.
- A new Quality and testing lead starts in October. Quality reviews will be lighter touch but more regular.

ANNOUNCEMENTS
- Learning allowance stays at $2,000 per person for FY27. Reminder to get manager approval before booking anything big and to log it in the development plan.
- Practice holiday calendar for 2027 will be published on 1 October.
- Open enrolment for benefits starts in November. HR will send a guide.
- A refresh of the expense tool is planned for the new year. No date yet.

PEOPLE MATTERS
- Promotion cycle opens in the new year. Managers will share timelines in November.
- Staffing guide is being updated. Roll-off notice period stays at two weeks.

QUESTIONS FROM THE FLOOR
- Q: Will remote days be reduced? A: No change planned. Client on-site requirements still come first.
- Q: Is there budget for internal tools? A: Small pilots can be proposed through the practice leader.
- Q: Will there be more cross-team projects? A: Yes, the practice leader wants more reuse of knowledge between engagements.

MY TAKEAWAYS
- Raise the reporting-line change with the Falcon analysts on Monday so nobody is surprised.
- Check with Finance whether the new expense tool affects the October claim process.
- Follow up with the practice leader about the reuse theme, since it fits what I want to propose next.
""",
    },
    {
        "file": "Weekly Planning Notes.txt",
        "text": f"""WEEKLY PLANNING NOTES

My own weekly planning notes for 31 August to 19 October 2026: priorities, meetings and reminders, written each Monday morning. They are for me, not the team, and are not a status report.

WEEK OF 31 AUGUST
- Priority: finish the Phase 2 statement of work draft and send the pricing assumptions to Finance.
- Meetings: Sprint 10 demo prep on Wednesday. One-to-one with the Delivery lead on Thursday.
- Reminder: submit August timesheet by the Friday deadline.

WEEK OF 7 SEPTEMBER
- Sprint 11 starts today. Priority: get steering committee materials ready for 14 September.
- Meetings: Finance business partner on Tuesday to check the Phase 2 budget numbers. Dry run with the Executive sponsor on Friday.
- Reminder: book travel for the October client visit.

WEEK OF 14 SEPTEMBER
- Steering committee today at 10 am. The goal is approval of the {PHASE2_BUDGET} Phase 2 budget.
- After approval, send thanks to the client sponsor and confirm the kickoff date for next Monday.
- Reminder: update the Staffing Plan once the budget is approved ({APPROVAL_DATE} is the approval date).

WEEK OF 21 SEPTEMBER
- {sprint_text(12)} starts today, and Phase 2 kickoff meeting is this morning.
- Priority: walk the Phase 2 team through scope and ways of working.
- Reminder: town hall on Thursday, and take notes.

WEEK OF 28 SEPTEMBER
- Priority: agree acceptance criteria for migration quality with the Delivery lead.
- Meetings: risk register review on Wednesday.
- Reminder: mid-year learning log is due to my manager by Friday.

WEEK OF 5 OCTOBER
- {sprint_text(13)} starts today.
- Client-site trip on Wednesday to Friday (see the itinerary). Leave Monday and Tuesday clear for prep.
- Reminder: Sprint 12 retrospective notes need to be filed.

WEEK OF 12 OCTOBER
- Priority: Go-Live readiness deck first draft. Review the risk register.
- Meetings: one-to-one with my manager on Wednesday. Weekly sync with the client delivery lead on Thursday.
- Reminder: file the expense report for the October trip before the end of the week or early next week.

WEEK OF 19 OCTOBER
- {sprint_text(14)} starts today, with the goal of piloting Ask for two teams.
- Priority: finish the Sprint 14 demo script and rehearse with the Delivery lead.
- Reminder: the pilot with two teams runs 9 to 27 November, so confirm both teams' leads this week.
""",
    },
    {
        "file": "Meeting Prep Notes - Steering.txt",
        "text": f"""MEETING PREP NOTES - STEERING

My preparation notes for the steering committee on Monday 14 September 2026, written between 10 and 13 September. Topic: the Phase 2 funding request of {PHASE2_BUDGET}, the likely questions and the answers I want to give. Audience: the client sponsor, the client delivery lead, the Executive sponsor and me.

THE ASK (10 SEPTEMBER)
- Request approval of a Phase 2 budget of {PHASE2_BUDGET} for the Harborview Platform, covering the period from kickoff on 21 September.
- Show that Phase 1 is complete and delivered what was promised. Phase 1 ended 7 August and the bridge period (Sprints 9 to 11) is nearly over.
- Ask for a decision in the meeting, not a follow-up.

STORY TO TELL (11 SEPTEMBER)
1. What we delivered in Phase 1, in plain terms.
2. What the bridge period has shown so far, particularly search quality.
3. What Phase 2 adds, and what it costs.
4. What we need from the client: sign-off, data access, test users.

EXPECTED QUESTIONS AND ANSWERS (12 SEPTEMBER)
- Q: Why {PHASE2_BUDGET}? A: It is built bottom-up from the Phase 2 scope and team plan, and sits within what the client sponsor told us was available.
- Q: What if scope grows? A: Changes go through the change order process. Nothing is added without written agreement.
- Q: Can the pilot start earlier? A: No. The platform needs Sprints 12 to 14 to reach pilot quality.
- Q: What are the main risks? A: Data quality in the warehouse migration and the availability of client test users. Both are on the risk register with owners.
- Q: What do we get at the end? A: A working search and Ask capability, training and a support model.

LOGISTICS (13 SEPTEMBER)
- Slides to the Executive sponsor on Sunday evening for review.
- Print a one-page budget summary for the client sponsor.
- Arrive 20 minutes early to check the room and the screen.
- Have the signed Change Order 02 and the Phase 1 readout to hand.

IF THEY HESITATE
Offer a staged release of funds, with a checkpoint after Sprint 12. Do not offer a price reduction.
""",
    },
    {
        "file": "Hiring Interview Notes.txt",
        "text": """HIRING INTERVIEW NOTES

My personal notes from interviews for the engineer role on the Falcon team, held 8 to 19 June 2026. Three candidates, labelled A, B and C. These are scored and rough, and only I should see them. The panel decision was made with HR, so this file is for recall only.

SCORING SCALE
1 to 5 on each of technical skill, problem solving, communication and fit. Scores are mine, out of 20 in total.

CANDIDATE A (interview 8 June)
- Strong backend experience. Built search services in a previous role and talked clearly about trade-offs between speed and quality.
- Technical 5, problem solving 4, communication 4, fit 4. Total 17.
- Impression: confident, a bit quick to give a solution before asking questions. Would work well with minimal supervision.
- Concern: asked a lot about career progression and less about the work itself.

CANDIDATE B (interview 11 June)
- Solid generalist with front-end and API experience. Good in the pair-programming exercise, narrated their thinking well.
- Technical 4, problem solving 4, communication 5, fit 5. Total 18.
- Impression: warm, curious, asked good questions about the client. Needs a little time to learn the data side.
- Concern: has not worked on a data-heavy platform yet.

CANDIDATE C (interview 15 June)
- Early-career engineer with strong fundamentals. Struggled with the system design question but recovered after a hint.
- Technical 3, problem solving 3, communication 4, fit 4. Total 14.
- Impression: eager to learn. Better suited to a junior role later in the year.
- Concern: would need close mentoring, which the team cannot give in Phase 2.

DEBRIEF (19 June)
- Panel agreed Candidate B is the strongest fit for the team as it is today, with Candidate A as the second choice.
- Next steps: HR to prepare an offer to B and keep A warm. Send a kind decline to C with feedback.
- Reminder: give feedback within a week and record the scores in the hiring tool.
""",
    },
    {
        "file": "Client Relationship Notes.txt",
        "text": """CLIENT RELATIONSHIP NOTES

My private notes on the Brightwater Logistics client sponsor and client delivery lead, kept from 2 March to 16 October 2026. They record preferences, sensitivities and things to remember, by role only. They are for my own preparation before meetings and are not shared with the client or the team.

2 MARCH 2026 - KICKOFF
- Client sponsor: senior, values brevity. Likes decisions framed with two options and a recommendation. Does not like surprises in front of their leadership.
- Client delivery lead: practical and detail oriented. Wants dates and owners for everything.

18 MARCH 2026 - DISCOVERY WORKSHOP
- Client delivery lead was guarded about legacy systems. Sensitive about the old search tool, because their team built it. Frame improvement as building on it.
- Sponsor asked for one-page summaries after each meeting.

11 MAY 2026 - CRM CHANGE ORDER
- Sponsor was quick to approve the change order once the benefit was clear. Delivery lead worried about integration risk. Agreed to a short design review.

15 JUNE 2026 - STEERING
- Both were happy with progress. Sponsor praised the demos. Delivery lead wants fewer surprises in sprint scope.

7 AUGUST 2026 - END OF PHASE 1
- Sponsor wants a clear story for their own leadership. Offered a short executive readout. Delivery lead is tired, so avoid adding meetings.

14 SEPTEMBER 2026 - PHASE 2 APPROVAL
- Sponsor decisive and positive. Delivery lead asked about test user availability. Promised a plan by the end of the month.

1 OCTOBER 2026
- Sponsor prefers calls to email on difficult topics. Delivery lead prefers written follow-ups with actions. Do both.

8 OCTOBER 2026 - ON SITE
- Working lunch with the delivery lead. They mentioned pressure from their own manager about the November timeline. Reassure, and keep dates firm.

16 OCTOBER 2026
- Sponsor asked about the pilot with two teams. Keep answers simple: dates, who is involved, what we need.
- Reminder: send the delivery lead a short note thanking their team for the site visit.

GENERAL
- Never discuss one client contact's comments with the other. Keep the tone warm and factual.
""",
    },
    {
        "file": "Draft Expense Report.docx",
        "blocks": [
            ("h1", "Draft Expense Report - October 2026 Client Visit"),
            ("p", "This is my draft expense claim for the client-site visit on 7 to 9 October 2026, prepared on 15 and 16 October 2026 before I submit it in the expense tool. It lists each item with its category and receipt status so I can check the total and make sure nothing needs pre-approval."),
            ("h2", "Items"),
            ("table", ["Date", "Description", "Category", "Amount", "Receipt"], [
                [d, desc, cat, _dollars(amount), receipt]
                for d, desc, cat, amount, receipt in _EXPENSE_ITEMS
            ], [0.1, 0.34, 0.16, 0.12, 0.28]),
            ("h2", "Totals"),
            ("p", f"Total claim: {_dollars(_TOTAL)} across {len(_EXPENSE_ITEMS)} items. The largest single item is {_dollars(_LARGEST)}."),
            ("h2", "Pre-approval check"),
            ("p", f"No single item is above the {EXPENSE_THRESHOLD} manager pre-approval threshold, so no pre-approval was needed for any line. The hotel is shown as one line for two nights, at $168.00 a night, which is still under the threshold. The trip was agreed with my manager on 1 October."),
            ("h2", "Receipts and deadlines"),
            ("bullets", [
                "All items over $25 have a receipt except the airport shuttle ($14.50), which is under the limit but I am requesting a copy anyway.",
                "The parking charge is under $25 and needs only a description.",
                "Submit by 6 November 2026, which is within 30 days of the trip.",
            ]),
            ("h2", "Open points"),
            ("p", "Confirm the client lunch is non-billable to the client. Check the nightly rate against the preferred hotel rate. Attach the boarding passes to the claim."),
        ],
    },
    {
        "file": "Travel Itinerary - October 2026.pdf",
        "blocks": [
            ("h1", "Travel Itinerary - October 2026"),
            ("p", "This is my itinerary for the client-site trip to Brightwater Logistics on 7 to 9 October 2026, put together between 1 and 5 October 2026. It lists flights, hotel and meetings in order so I can keep everything in one place while travelling. All times are local and fictional."),
            ("h2", "Flights"),
            ("table", ["Day", "Flight", "Depart", "Arrive"], [
                ["Wed 7 Oct", "Outbound, morning flight", "07:10 from home airport", "09:05 at client city"],
                ["Fri 9 Oct", "Return, evening flight", "18:40 from client city", "20:35 at home airport"],
            ], [0.2, 0.3, 0.25, 0.25]),
            ("h2", "Hotel"),
            ("p", "Harborside Hotel, two nights, 7 and 8 October, check-out Friday morning. Booked through the firm portal at the preferred rate. Ten minutes by car from the client site."),
            ("h2", "Schedule"),
            ("table", ["Day and time", "Meeting", "Who"], [
                ["Wed 7 Oct, 11:00", "Arrive and walk the site", "Client delivery lead"],
                ["Wed 7 Oct, 14:00", "Sprint 13 check-in", "Delivery lead and client team"],
                ["Thu 8 Oct, 09:30", "Phase 2 working session", "Client sponsor and client delivery lead"],
                ["Thu 8 Oct, 12:30", "Working lunch", "Client delivery lead"],
                ["Thu 8 Oct, 15:00", "Test user planning", "Client delivery lead and analysts"],
                ["Fri 9 Oct, 10:00", "Wrap-up and actions", "Client delivery lead"],
            ], [0.28, 0.4, 0.32]),
            ("h2", "Reminders"),
            ("bullets", [
                "Bring laptop, charger, badge and printed agenda.",
                "Keep receipts for the expense claim.",
                "Lock the laptop screen whenever I leave the meeting room.",
            ]),
        ],
    },
]
