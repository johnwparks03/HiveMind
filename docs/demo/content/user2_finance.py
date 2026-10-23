"""User 2 (Delivery lead) public finance files for the Falcon demo."""

from facts import (
    APPROVAL_DATE, BRIDGE_PERIOD, CLIENT, CO01_AMOUNT, CO02_DATE, PHASE1_END, PHASE1_TOTAL,
    PHASE2_BUDGET, PHASE2_KICKOFF, PHASE2_SPLIT, SOW1_VALUE, SOW1_SIGNED, money, sprint_text,
)

# By-month view of the Phase 2 budget (roles x Sep, Oct, Nov 2026). Each row sums to its role total.
MONTHS = {
    "Engineering": (4400, 12000, 10000),
    "Data": (1800, 4000, 4000),
    "Design": (1400, 2400, 1400),
    "Project management": (800, 1800, 1700),
    "Quality assurance": (300, 900, 1300),
}
for _role, _row in MONTHS.items():
    assert sum(_row) == PHASE2_SPLIT[_role], _role
assert sum(PHASE2_SPLIT.values()) == 48200
MONTH_TOTALS = tuple(sum(row[i] for row in MONTHS.values()) for i in range(3))
assert sum(MONTH_TOTALS) == 48200

SPLIT_ROWS = [[role, money(amount)] for role, amount in PHASE2_SPLIT.items()]
SPLIT_ROWS.append(["Total", PHASE2_BUDGET])
MONTH_ROWS = [[role] + [money(v) for v in row] + [money(PHASE2_SPLIT[role])] for role, row in MONTHS.items()]
MONTH_ROWS.append(["Total"] + [money(v) for v in MONTH_TOTALS] + [PHASE2_BUDGET])

# Phase 2 September actuals by role (21 to 30 September).
SEP_PLAN = {role: row[0] for role, row in MONTHS.items()}
SEP_ACTUAL = {"Engineering": 4550, "Data": 1700, "Design": 1400, "Project management": 800, "Quality assurance": 300}
SEP_ROWS = []
for _role in MONTHS:
    _var = SEP_ACTUAL[_role] - SEP_PLAN[_role]
    SEP_ROWS.append([_role, money(SEP_PLAN[_role]), money(SEP_ACTUAL[_role]), f"{_var:+,}"])
SEP_ROWS.append(["Total", money(sum(SEP_PLAN.values())), money(sum(SEP_ACTUAL.values())),
                 f"{sum(SEP_ACTUAL.values()) - sum(SEP_PLAN.values()):+,}"])
assert sum(SEP_PLAN.values()) == MONTH_TOTALS[0] == 8700 and sum(SEP_ACTUAL.values()) == 8750

FORECAST_ROWS = [
    [role, money(PHASE2_SPLIT[role]), money(SEP_ACTUAL[role]), money(PHASE2_SPLIT[role]), "0"]
    for role in PHASE2_SPLIT
]
FORECAST_ROWS.append(["Total", PHASE2_BUDGET, money(sum(SEP_ACTUAL.values())), PHASE2_BUDGET, "0"])

FILES = [
    {"file": "Phase 2 Budget Approval Memo.docx", "blocks": [
        ("h1", "Phase 2 Budget Approval Memo"),
        ("p", f"This memo records the approval of the Falcon Phase 2 budget of {PHASE2_BUDGET} by the steering committee on "
              f"{APPROVAL_DATE}, covering the Harborview Platform work for {CLIENT} from {PHASE2_KICKOFF} to the end of November 2026. "
              "It is written by the Delivery lead (User 2) so that finance and delivery work from the same approved figures."),
        ("h2", "Decision"),
        ("p", f"The steering committee approved a Phase 2 budget of {PHASE2_BUDGET} on {APPROVAL_DATE}. Phase 2 follows the close of Phase 1 "
              f"on {PHASE1_END} (total {PHASE1_TOTAL}) and the bridge period that ran Sprints 9 to 11 at no added fee. Phase 2 kicks off with "
              f"{sprint_text(12)}."),
        ("h2", "Approved split by role"),
        ("table", ["Role", "Approved amount"], SPLIT_ROWS, [0.6, 0.4]),
        ("h2", "Conditions of approval"),
        ("bullets", [
            "Spend is tracked monthly against the by-month plan in the Phase 2 Budget Breakdown, with a burn report issued by the third working day of each month.",
            "Any move of more than 10 percent between role lines needs written agreement from the Client sponsor and the Executive sponsor.",
            "A contingency of up to 5 percent of the total (up to $2,410) may be requested above the approved amount; only the Executive sponsor can release it.",
            "The Ask pilot for two teams must be reviewed at the November steering meeting before any further spend is committed.",
        ]),
        ("h2", "Approvers"),
        ("bullets", [
            "Executive sponsor (chair of the steering committee)",
            "Client sponsor",
            "Finance business partner (budget owner for Brightwater Logistics)",
            "Project lead (User 1) and Delivery lead (User 2) for the delivery team",
        ]),
        ("h2", "Next steps"),
        ("p", "The Delivery lead issues the by-month plan to finance, opens the Phase 2 cost codes before kickoff, and reports the first month of actuals "
              "in the September burn report."),
    ]},
    {"file": "Phase 2 Budget Breakdown.pdf", "blocks": [
        ("h1", "Phase 2 Budget Breakdown"),
        ("p", f"This breakdown shows how the approved Falcon Phase 2 budget of {PHASE2_BUDGET} is split by role and by month (September to November 2026). "
              f"It was prepared by the Delivery lead (User 2) between 8 and 14 September 2026 ahead of the steering approval on {APPROVAL_DATE}."),
        ("h2", "Budget by role"),
        ("table", ["Role", "Phase 2 budget"], SPLIT_ROWS, [0.65, 0.35]),
        ("h2", "Budget by month"),
        ("p", f"Phase 2 starts on {PHASE2_KICKOFF}, so September covers only the last ten days of the month. Rows add up to the role totals above and the columns add up to {PHASE2_BUDGET}."),
        ("table", ["Role", "Sep 2026", "Oct 2026", "Nov 2026", "Role total"], MONTH_ROWS, [0.28, 0.15, 0.15, 0.15, 0.27]),
        ("h2", "Assumptions"),
        ("bullets", [
            "Rates follow the agreed Rate Card; the split is expressed in dollars, not hours.",
            "Engineering carries the Ask work, the central retrieval service and the warehouse extract integration, and peaks in October.",
            "Data covers ingest, embeddings and the warehouse cutover quality checks, and is flat in October and November.",
            "Design is front loaded for the Ask page refresh and returns in November for pilot feedback changes.",
            "Quality assurance ramps up in November for pilot support and regression runs.",
            "No contingency is included in these figures; contingency is requested separately from the Executive sponsor.",
        ]),
        ("h2", "Open points"),
        ("p", "The Finance business partner asked for the same split to be reported monthly. The September, October and November burn reports will use these exact role lines."),
    ]},
    {"file": "Monthly Burn Report - August 2026.pdf", "blocks": [
        ("h1", "Monthly Burn Report - August 2026"),
        ("p", f"This report covers Falcon spend for August 2026 (1 to 31 August), written on 3 September 2026 by the Delivery lead (User 2). "
              f"It shows the last week of Phase 1, which closed on {PHASE1_END}, and the first weeks of the bridge period ({BRIDGE_PERIOD}), "
              f"which Change Order 02 ({CO02_DATE}) funds from Phase 1 contingency at no added fee."),
        ("h2", "Summary"),
        ("bullets", [
            "August actual spend was $13,150 against a plan of $13,400, which is $250 under plan.",
            f"Phase 1 closed on {PHASE1_END} with no overrun against the {PHASE1_TOTAL} total.",
            "Bridge weeks drew $7,100 of contingency against a plan of $7,200; no new fees were invoiced to the client.",
        ]),
        ("h2", "Burn against plan"),
        ("table", ["Period", "Scope", "Plan", "Actual", "Variance"], [
            ["1 to 7 Aug", "Phase 1 close-out (Sprint 8)", "$6,200", "$6,050", "-$150"],
            ["10 to 14 Aug", "Bridge, Sprint 9 week 1", "$2,400", "$2,250", "-$150"],
            ["17 to 21 Aug", "Bridge, Sprint 9 week 2", "$2,400", "$2,500", "+$100"],
            ["24 to 28 Aug", "Bridge, Sprint 10 week 1", "$2,400", "$2,350", "-$50"],
            ["August total", "", "$13,400", "$13,150", "-$250"],
        ], [0.18, 0.37, 0.15, 0.15, 0.15]),
        ("h2", "Commentary"),
        ("p", "The Sprint 9 second week ran $100 over plan because an engineer covered a production fix for the CRM integration. The Sprint 8 close-out and the "
              "executive readout on 12 August were delivered with less review time than planned, which accounts for the Phase 1 saving."),
        ("h2", "Looking ahead"),
        ("p", "The bridge continues through Sprint 11 and ends on 18 September 2026. The week beginning 31 August is reported in the September burn report. "
              "Phase 2 spending is tracked from the approved budget once the steering committee decides on 14 September."),
    ]},
    {"file": "Monthly Burn Report - September 2026.pdf", "blocks": [
        ("h1", "Monthly Burn Report - September 2026"),
        ("p", f"This report covers Falcon spend for September 2026, written on 2 October 2026 by the Delivery lead (User 2). It covers the end of the bridge period "
              f"(18 September), the start of Phase 2 on {PHASE2_KICKOFF}, and burn against the Phase 2 September plan."),
        ("h2", "Summary"),
        ("bullets", [
            "Bridge weeks beginning 31 August, 7 September and 14 September cost $6,950 against a plan of $7,200, which is $250 under plan.",
            "Phase 2 September actuals (21 to 30 September) were $8,750 against a plan of $8,700, which is $50 over plan.",
            "Total September spend was $15,700 against a plan of $15,900.",
        ]),
        ("h2", "Bridge period weeks"),
        ("table", ["Week beginning", "Plan", "Actual", "Variance"], [
            ["31 Aug (Sprint 10 week 2)", "$2,400", "$2,300", "-$100"],
            ["7 Sep (Sprint 11 week 1)", "$2,400", "$2,450", "+$50"],
            ["14 Sep (Sprint 11 week 2)", "$2,400", "$2,200", "-$200"],
            ["Bridge total", "$7,200", "$6,950", "-$250"],
        ], [0.46, 0.18, 0.18, 0.18]),
        ("p", "Across the whole bridge (Sprints 9 to 11) contingency use was $14,050 against a plan of $14,400."),
        ("h2", "Phase 2 burn by role (21 to 30 September)"),
        ("table", ["Role", "Sep plan", "Sep actual", "Variance"], SEP_ROWS, [0.4, 0.2, 0.2, 0.2]),
        ("h2", "Commentary"),
        ("p", "Engineering was $150 over plan because the Sprint 12 environment baseline needed an extra day, offset by Data finishing the extract mapping spike "
              "$100 under plan. Quality assurance, design and project management landed on plan. No budget transfers between roles were needed."),
        ("p", "The October burn report will be issued in the first week of November against the October plan in the Phase 2 Budget Breakdown."),
    ]},
    {"file": "Forecast vs Actual - Q3 2026.docx", "blocks": [
        ("h1", "Forecast vs Actual - Q3 2026"),
        ("p", f"This document compares Falcon actual spend for Q3 2026 (July to September) with the forecast, and restates the Phase 2 forecast by role against the "
              f"approved budget of {PHASE2_BUDGET}. Prepared by the Delivery lead (User 2), created 5 October and revised 9 October 2026, for the Finance business partner and the Client sponsor."),
        ("h2", "Q3 actuals against forecast"),
        ("table", ["Month", "Scope", "Forecast", "Actual", "Variance"], [
            ["July", "Phase 1, Sprints 7 and 8", "$18,600", "$18,700", "+$100"],
            ["August", "Phase 1 close-out and bridge", "$13,400", "$13,150", "-$250"],
            ["September", "Bridge and Phase 2 start", "$15,900", "$15,700", "-$200"],
            ["Q3 total", "", "$47,900", "$47,550", "-$350"],
        ]),
        ("p", f"Q3 closed $350 under forecast. Phase 1 stayed within the {PHASE1_TOTAL} total ({SOW1_VALUE} signed {SOW1_SIGNED}, plus {CO01_AMOUNT} for Change Order 01), "
              "and the bridge period used less contingency than planned."),
        ("h2", "Phase 2 forecast by role"),
        ("p", "Spend to 2 October covers only the last days of September. The forecast at completion is unchanged from the approved budget."),
        ("table", ["Role", "Approved budget", "Spent to 2 Oct", "Forecast at completion", "Variance"], FORECAST_ROWS),
        ("h2", "Variance commentary"),
        ("bullets", [
            f"Engineering ({money(PHASE2_SPLIT['Engineering'])}) is $150 ahead of the September plan; October carries the heaviest load for the Ask pilot, so no saving is assumed.",
            f"Data ({money(PHASE2_SPLIT['Data'])}) is $100 under for September and the warehouse quality checks are still forecast at the planned effort.",
            f"Design ({money(PHASE2_SPLIT['Design'])}), project management ({money(PHASE2_SPLIT['Project management'])}) and quality assurance ({money(PHASE2_SPLIT['Quality assurance'])}) are on plan.",
        ]),
        ("h2", "Risks to the forecast"),
        ("p", "A slip in the warehouse cutover would move data and quality assurance effort into November. Any resulting overspend would be raised as a contingency request "
              "to the steering committee; no request has been made."),
    ]},
    {"file": "Invoice Summary - Phase 1.pdf", "blocks": [
        ("h1", "Invoice Summary - Phase 1"),
        ("p", f"This summary lists every invoice raised for Falcon Phase 1 (March to August 2026) and its payment status as of 31 August 2026. The invoices add up to the Phase 1 total of {PHASE1_TOTAL}: "
              f"the {SOW1_VALUE} Statement of Work signed {SOW1_SIGNED} plus {CO01_AMOUNT} for Change Order 01. Prepared by the Delivery lead (User 2) for the Finance business partner."),
        ("h2", "Invoices"),
        ("table", ["Invoice", "Date", "Basis", "Amount", "Status"], [
            ["FAL-INV-001", "2 Mar 2026", "SOW milestone 1: kickoff", "$10,500", "Paid 27 Mar 2026"],
            ["FAL-INV-002", "30 Apr 2026", "SOW milestone 2: discovery complete", "$10,500", "Paid 28 May 2026"],
            ["FAL-INV-003", "15 Jun 2026", "Change Order 01: CRM integration", "$6,800", "Paid 10 Jul 2026"],
            ["FAL-INV-004", "31 Jul 2026", "SOW milestone 3: Phase 1 delivery", "$10,500", "Paid 25 Aug 2026"],
            ["Total", "", "", "$38,300", "All paid"],
        ], [0.17, 0.15, 0.32, 0.13, 0.23]),
        ("p", "The SOW milestones total $31,500 (three invoices of $10,500) and the change order invoice is $6,800, so the four invoices sum to $38,300."),
        ("h2", "Notes"),
        ("bullets", [
            f"No invoice was raised for the bridge period. Change Order 02 ({CO02_DATE}) funds Sprints 9 to 11 from Phase 1 contingency at no added fee.",
            "Payment terms are 30 days from the invoice date; all four invoices were paid inside terms.",
            "There are no outstanding credits, disputes or retentions on Phase 1.",
            f"Phase 2 invoicing will follow the Phase 2 Statement of Work against the approved budget of {PHASE2_BUDGET}.",
        ]),
    ]},
]
