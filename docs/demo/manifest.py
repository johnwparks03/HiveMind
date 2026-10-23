"""Single source of truth for the 104 demo files: path, dates and author.

Content modules supply the body for each path. Titles come from the file name.
Folder layout: User1/Public/Falcon, User1/Private, User2/Public/Falcon.
"""

F1 = "User1/Public/Falcon"
F2 = "User2/Public/Falcon"
PRIV = "User1/Private"

# (path under files root, created, revised, author or None for the user label)
MANIFEST = [
    # ---- User 1 public: Contracts (9) ---------------------------------------
    (f"{F1}/Contracts/Falcon Proposal Deck.pptx", "2026-01-14", "2026-02-02", None),
    (f"{F1}/Contracts/RFP Response.docx", "2026-01-08", "2026-01-20", None),
    (f"{F1}/Contracts/Statement of Work - Phase 1.pdf", "2026-02-12", "2026-02-12", None),
    (f"{F1}/Contracts/Statement of Work - Phase 2.pdf", "2026-09-02", "2026-09-14", None),
    (f"{F1}/Contracts/Change Order 01 - CRM Integration.docx", "2026-05-11", "2026-05-11", None),
    (f"{F1}/Contracts/Change Order 02 - Bridge Period.docx", "2026-08-03", "2026-08-03", None),
    (f"{F1}/Contracts/Rate Card and Pricing Assumptions.pdf", "2025-11-18", "2026-01-05", None),
    (f"{F1}/Contracts/Master Services Agreement Summary.pdf", "2025-10-06", "2025-10-06", None),
    (f"{F1}/Contracts/Staffing Plan.docx", "2026-02-20", "2026-09-18", None),
    # ---- User 1 public: Governance (9) --------------------------------------
    (f"{F1}/Governance/Project Charter.docx", "2026-02-16", "2026-03-02", None),
    (f"{F1}/Governance/Kickoff Deck - Phase 1.pptx", "2026-02-27", "2026-03-02", None),
    (f"{F1}/Governance/Kickoff Deck - Phase 2.pptx", "2026-08-28", "2026-09-18", None),
    (f"{F1}/Governance/RACI Matrix.docx", "2026-02-24", "2026-08-10", None),
    (f"{F1}/Governance/Communications Plan.docx", "2026-02-24", "2026-06-09", None),
    (f"{F1}/Governance/Risk Register.docx", "2026-03-04", "2026-10-12", None),
    (f"{F1}/Governance/Assumptions and Dependencies Log.txt", "2026-03-04", "2026-09-30", None),
    (f"{F1}/Governance/Delivery Roadmap.pptx", "2026-03-10", "2026-09-16", None),
    (f"{F1}/Governance/Decision Log.txt", "2026-03-02", "2026-10-20", None),
    # ---- User 1 public: Meetings (8) ----------------------------------------
    (f"{F1}/Meetings/Steering Committee/Steering Minutes 2026-06-15.docx", "2026-06-15", "2026-06-16", None),
    (f"{F1}/Meetings/Steering Committee/Steering Minutes 2026-09-14.docx", "2026-09-14", "2026-09-14", None),
    (f"{F1}/Meetings/Discovery/Client Workshop Notes - Discovery.docx", "2026-03-18", "2026-03-19", None),
    (f"{F1}/Meetings/Discovery/Stakeholder Interview Notes.txt", "2026-03-09", "2026-03-13", None),
    (f"{F1}/Meetings/Status Notes/Weekly Status Notes - Q2 2026.txt", "2026-04-06", "2026-06-26", None),
    (f"{F1}/Meetings/Status Notes/Weekly Status Notes - Q3 2026.txt", "2026-07-03", "2026-09-25", None),
    (f"{F1}/Meetings/Retrospectives/Sprint 8 Retrospective.txt", "2026-08-07", "2026-08-10", None),
    (f"{F1}/Meetings/Retrospectives/Sprint 12 Retrospective.txt", "2026-10-02", "2026-10-05", None),
    # ---- User 1 public: Demos (6) -------------------------------------------
    (f"{F1}/Demos/Sprint 6 Demo Deck.pptx", "2026-07-06", "2026-07-10", None),
    (f"{F1}/Demos/Sprint 10 Demo Deck.pptx", "2026-08-31", "2026-09-04", None),
    (f"{F1}/Demos/Sprint 14 Demo Script.docx", "2026-10-20", "2026-10-22", None),
    (f"{F1}/Demos/Executive Readout - Phase 1.pptx", "2026-08-05", "2026-08-12", None),
    (f"{F1}/Demos/Go-Live Readiness Deck.pptx", "2026-10-19", "2026-10-21", None),
    (f"{F1}/Demos/Lessons Learned Deck.pptx", "2026-08-14", "2026-08-19", None),
    # ---- User 2 public: Finance (6) -----------------------------------------
    (f"{F2}/Finance/Phase 2 Budget Approval Memo.docx", "2026-09-14", "2026-09-15", None),
    (f"{F2}/Finance/Phase 2 Budget Breakdown.pdf", "2026-09-08", "2026-09-14", None),
    (f"{F2}/Finance/Burn Reports/Monthly Burn Report - August 2026.pdf", "2026-09-03", "2026-09-03", None),
    (f"{F2}/Finance/Burn Reports/Monthly Burn Report - September 2026.pdf", "2026-10-02", "2026-10-02", None),
    (f"{F2}/Finance/Forecast vs Actual - Q3 2026.docx", "2026-10-05", "2026-10-09", None),
    (f"{F2}/Finance/Invoice Summary - Phase 1.pdf", "2026-08-20", "2026-08-31", None),
    # ---- User 2 public: Discovery (5) ---------------------------------------
    (f"{F2}/Discovery/Current-State Assessment.docx", "2026-03-12", "2026-04-02", None),
    (f"{F2}/Discovery/Discovery Findings Report.pdf", "2026-04-03", "2026-04-10", None),
    (f"{F2}/Discovery/User Interview Synthesis.docx", "2026-03-20", "2026-04-01", None),
    (f"{F2}/Discovery/Benchmarking Notes - Search Tools.txt", "2026-03-24", "2026-04-08", None),
    (f"{F2}/Discovery/Vendor Evaluation - Vector Store.txt", "2026-05-11", "2026-05-11", None),
    # ---- User 2 public: Delivery (5) ----------------------------------------
    (f"{F2}/Delivery/Sprint Planning/Sprint 12 Planning.docx", "2026-09-18", "2026-09-21", None),
    (f"{F2}/Delivery/Sprint Planning/Sprint 14 Planning.docx", "2026-10-16", "2026-10-20", None),
    (f"{F2}/Delivery/Backlog Prioritisation Notes.txt", "2026-06-22", "2026-10-14", None),
    (f"{F2}/Delivery/Definition of Done.docx", "2026-04-13", "2026-08-03", None),
    (f"{F2}/Delivery/Release Notes - v0.9.txt", "2026-10-09", "2026-10-09", None),
    # ---- User 2 public: Technical (9) ---------------------------------------
    (f"{F2}/Technical/Architecture/Architecture Overview.pdf", "2026-04-14", "2026-09-11", None),
    (f"{F2}/Technical/Architecture/Data Model Description.docx", "2026-04-20", "2026-08-27", None),
    (f"{F2}/Technical/Integration/Integration Specification.docx", "2026-05-12", "2026-07-08", None),
    (f"{F2}/Technical/Security/Security Review Summary.pdf", "2026-07-20", "2026-07-29", None),
    (f"{F2}/Technical/Testing/Test Plan.docx", "2026-06-15", "2026-10-06", None),
    (f"{F2}/Technical/Testing/UAT Plan.docx", "2026-09-21", "2026-10-13", None),
    (f"{F2}/Technical/Migration/Data Migration Plan.docx", "2026-08-24", "2026-10-14", None),
    (f"{F2}/Technical/Operations/Nightly Ingest Runbook.pdf", "2025-06-17", "2026-07-30", None),
    (f"{F2}/Technical/Operations/Environment Setup Guide.pdf", "2025-11-04", "2026-03-20", None),
    # ---- User 2 public: Handover (5) ----------------------------------------
    (f"{F2}/Handover/Training/End-User Training Deck.pptx", "2026-10-14", "2026-10-19", None),
    (f"{F2}/Handover/Guides/User Guide.pdf", "2026-10-12", "2026-10-19", None),
    (f"{F2}/Handover/Guides/FAQ.txt", "2026-10-12", "2026-10-20", None),
    (f"{F2}/Handover/Support/Support Model.docx", "2026-09-28", "2026-10-07", None),
    (f"{F2}/Handover/Support/Handover Checklist.docx", "2026-10-08", "2026-10-08", None),
    # ---- User 1 private: Initiatives (7) ------------------------------------
    (f"{PRIV}/Initiatives/Knowledge Reuse Pilot/Knowledge Reuse Pilot - Charter.docx", "2026-07-06", "2026-10-10", None),
    (f"{PRIV}/Initiatives/Knowledge Reuse Pilot/Knowledge Reuse Pilot - Business Case.pptx", "2026-09-29", "2026-09-29", None),
    (f"{PRIV}/Initiatives/Knowledge Reuse Pilot/Pilot Pitch Talking Points.txt", "2026-10-05", "2026-10-08", None),
    (f"{PRIV}/Initiatives/Knowledge Reuse Pilot/Stakeholder Map.docx", "2026-08-12", "2026-09-22", None),
    (f"{PRIV}/Initiatives/Knowledge Reuse Pilot/Draft Pilot Results Summary.docx", "2026-10-21", "2026-10-21", None),
    (f"{PRIV}/Initiatives/Ideas/Initiative Idea Backlog.txt", "2026-01-20", "2026-10-15", None),
    (f"{PRIV}/Initiatives/Practice Innovation/Practice Innovation Proposal.pptx", "2026-03-30", "2026-04-14", None),
    # ---- User 1 private: Performance (10) -----------------------------------
    (f"{PRIV}/Performance/2026/Performance Review Tracker 2026.txt", "2026-01-05", "2026-10-18", None),
    (f"{PRIV}/Performance/2026/Goal Tracking.docx", "2026-01-05", "2026-09-01", None),
    (f"{PRIV}/Performance/2026/Feedback Log.txt", "2026-01-12", "2026-10-09", None),
    (f"{PRIV}/Performance/2026/1-1 Notes With Manager 2026.txt", "2026-01-14", "2026-10-14", None),
    (f"{PRIV}/Performance/2026/Development Plan.docx", "2026-01-08", "2026-07-15", None),
    (f"{PRIV}/Performance/2026/Utilisation and Hours Notes.txt", "2026-02-02", "2026-10-16", None),
    (f"{PRIV}/Performance/Reviews/H1 2026 Self-Review.docx", "2026-06-02", "2026-06-25", None),
    (f"{PRIV}/Performance/Reviews/H2 2026 Self-Review - Draft.docx", "2026-10-19", "2026-10-21", None),
    (f"{PRIV}/Performance/Reviews/FY25 Annual Review Summary.pdf", "2025-08-18", "2025-08-18", None),
    (f"{PRIV}/Performance/Promotion/Promotion Case Draft.docx", "2026-08-25", "2026-10-12", None),
    # ---- User 1 private: Career (6) -----------------------------------------
    (f"{PRIV}/Career/Learning/Certification Study Notes.txt", "2026-03-02", "2026-05-26", None),
    (f"{PRIV}/Career/Learning/Training Transcript.pdf", "2026-09-30", "2026-09-30", "Firm Learning"),
    (f"{PRIV}/Career/Learning/Reading Notes.txt", "2026-01-25", "2026-10-03", None),
    (f"{PRIV}/Career/Mentoring/Mentor Meeting Notes.txt", "2026-02-10", "2026-09-17", None),
    (f"{PRIV}/Career/Profile/Resume and Bio.docx", "2025-11-20", "2026-06-01", None),
    (f"{PRIV}/Career/Speaking/Conference Talk Outline.pptx", "2026-08-04", "2026-09-09", None),
    # ---- User 1 private: Firm (12) ------------------------------------------
    (f"{PRIV}/Firm/Policies/Expense Policy Summary FY27.pdf", "2026-06-15", "2026-06-15", "Firm Finance"),
    (f"{PRIV}/Firm/Policies/Travel and Expenses Guide FY27.pdf", "2026-06-15", "2026-07-01", "Firm Finance"),
    (f"{PRIV}/Firm/Policies/Client Confidentiality Reminder.txt", "2025-12-01", "2025-12-01", "Firm Information Security"),
    (f"{PRIV}/Firm/Policies/Timekeeping Guidelines.pdf", "2025-09-02", "2026-01-05", "Firm HR"),
    (f"{PRIV}/Firm/Policies/Remote Work Policy.pdf", "2025-11-10", "2026-04-01", "Firm HR"),
    (f"{PRIV}/Firm/Policies/IT Security Policy Summary.pdf", "2026-02-03", "2026-08-05", "Firm Information Security"),
    (f"{PRIV}/Firm/Policies/Code of Conduct Summary.pdf", "2025-07-15", "2025-07-15", "Firm HR"),
    (f"{PRIV}/Firm/Policies/Learning Budget Policy.pdf", "2026-07-01", "2026-07-01", "Firm HR"),
    (f"{PRIV}/Firm/HR/Benefits Summary.pdf", "2026-01-02", "2026-01-02", "Firm HR"),
    (f"{PRIV}/Firm/Organisation/Firm Org Chart.pdf", "2026-05-04", "2026-09-14", "Firm Operations"),
    (f"{PRIV}/Firm/Organisation/Staffing and Resourcing Guide.pdf", "2025-12-08", "2026-03-16", "Firm Operations"),
    (f"{PRIV}/Firm/Calendar/Practice Holiday Calendar 2027.txt", "2026-10-01", "2026-10-01", "Firm Operations"),
    # ---- User 1 private: Working Files (7) ----------------------------------
    (f"{PRIV}/Working Files/Town Hall Notes - September 2026.txt", "2026-09-24", "2026-09-24", None),
    (f"{PRIV}/Working Files/Weekly Planning Notes.txt", "2026-08-31", "2026-10-19", None),
    (f"{PRIV}/Working Files/Meeting Prep Notes - Steering.txt", "2026-09-10", "2026-09-13", None),
    (f"{PRIV}/Working Files/Hiring Interview Notes.txt", "2026-06-08", "2026-06-19", None),
    (f"{PRIV}/Working Files/Client Relationship Notes.txt", "2026-03-02", "2026-10-16", None),
    (f"{PRIV}/Working Files/Draft Expense Report.docx", "2026-10-15", "2026-10-16", None),
    (f"{PRIV}/Working Files/Travel Itinerary - October 2026.pdf", "2026-10-01", "2026-10-05", None),
]


def user_of(path):
    return "User 1" if path.startswith("User1/") else "User 2"


def visibility_of(path):
    return "private" if "/Private/" in path else "public"
