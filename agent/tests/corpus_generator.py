"""Generate a varied DOCX/PPTX corpus for HiveMind indexing and search tests.

Deterministic: the same seed always produces the same files, so test assertions can
name specific files. Run directly to write a corpus you can browse by hand:

    python tests/corpus_generator.py <output folder>

Set file mtimes across 2026 so date-filtered search has something to match.
"""
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from docx import Document
from pptx import Presentation

SEED = 20261012
TOTAL_DOCX = 60
TOTAL_PPTX = 20
TODAY = datetime(2026, 10, 12, 9, 0)

rng = random.Random(SEED)

PEOPLE = ["Priya Shah", "Marcus Lee", "Dana Whitfield", "Tomás Ruiz", "Aisha Bello",
          "Jonah Park", "Helen Okafor", "Sam Carter", "Lena Novak", "Ravi Mehta"]
PROJECTS = ["Project Alpha", "Project Beacon", "Project Cobalt", "Project Delta", "Project Ember"]
CLIENTS = ["Northwind", "Contoso", "Fabrikam", "Tailspin", "Litware", "Adventure Works"]

# topic -> (folder, filename stem, heading, paragraph sentences)
TOPICS = {
    "meeting": ("Meetings", "Meeting notes", "Weekly sync notes", [
        "Reviewed progress against the milestone plan and agreed the next two deliverables.",
        "Action owners confirmed for the open risks; follow-ups are tracked in the shared board.",
        "Discussed the client feedback on the draft and what changes it implies for scope.",
        "Decided to defer the vendor integration until the security review is complete.",
    ]),
    "budget": ("Finance", "Budget plan", "Quarterly budget plan", [
        "Forecast spend is tracking slightly above plan, mostly driven by contractor hours.",
        "Headcount assumptions hold for the quarter; no new hires are included in the baseline.",
        "Software licence renewals move up by roughly eight percent at the next billing cycle.",
        "Contingency is held at five percent of the delivery budget until the scope is locked.",
    ]),
    "roadmap": ("Projects", "Roadmap", "Product roadmap", [
        "Phase one focuses on ingestion and metadata, with search following once tags are reliable.",
        "Dependencies on the identity service are the main schedule risk for the next release.",
        "Stretch items are listed separately and will be dropped first if the schedule slips.",
        "The success measures are time to find a file and the share of results users accept.",
    ]),
    "status": ("Projects", "Status report", "Project status", [
        "Overall status is amber: two workstreams are on track and one needs an extra week.",
        "Testing coverage has improved since last month, with integration tests now running nightly.",
        "The client has signed off the discovery findings and asked for a demo next sprint.",
        "No critical defects are open; three medium defects are scheduled for the next build.",
    ]),
    "proposal": ("Sales", "Proposal draft", "Client proposal", [
        "We propose a three-phase engagement covering discovery, build and handover support.",
        "Pricing follows the blended rate card, with a fixed fee for the discovery phase only.",
        "The team combines two senior consultants, a developer and a part-time delivery lead.",
        "Success criteria are agreed up front and reviewed at the end of each phase.",
    ]),
    "marketing": ("Marketing", "Campaign brief", "Campaign brief", [
        "The audience is families planning a first cruise, with a focus on shore excursions.",
        "Key messages stress ease of booking and the mix of relaxation and adventure on board.",
        "Creative should use bright daylight imagery of pool decks and destination views.",
        "Channels include paid social, email to past guests and a short run of display ads.",
    ]),
    "retro": ("Projects", "Retrospective", "Sprint retrospective", [
        "What went well: the demo was ready early and stakeholders engaged with it directly.",
        "What did not: estimates for the data migration were too optimistic by about a third.",
        "We will timebox spikes and record the decision in the story before writing code.",
        "Two improvements are agreed for next sprint, owned by the delivery lead.",
    ]),
    "risk": ("Projects", "Risk register", "Risk register", [
        "Risk one: third-party API limits could slow bulk processing; mitigation is batching.",
        "Risk two: key person dependency on the architecture; mitigation is pairing and docs.",
        "Risk three: data quality in the source system is uncertain; a sampling check is planned.",
        "Risk four: procurement timelines may delay the pilot; escalation path is agreed.",
    ]),
    "policy": ("HR", "Policy draft", "Working practices draft", [
        "This draft sets out expectations for remote working, core hours and travel approvals.",
        "Expense claims must be submitted within thirty days with receipts attached.",
        "Feedback is captured quarterly and summarised for the leadership team.",
        "The policy will be reviewed after the pilot period and adjusted as needed.",
    ]),
    "vendor": ("Finance", "Vendor evaluation", "Vendor evaluation summary", [
        "Three vendors were scored against security, cost, integration effort and support model.",
        "The preferred option scores well on integration but needs a data residency commitment.",
        "Reference calls raised concerns about onboarding time for large document libraries.",
        "Recommendation: proceed to a paid pilot with two vendors before final selection.",
    ]),
}

PPTX_TOPICS = {
    "kickoff": ("Projects", "Kickoff deck", ["Goals and scope", "Team and roles", "Plan and milestones", "Ways of working"]),
    "review": ("Sales", "Pipeline review", ["Pipeline by stage", "Top deals this quarter", "Forecast against target", "Next actions"]),
    "steering": ("Projects", "Steering committee", ["Status summary", "Decisions needed", "Risks and issues", "Budget position"]),
    "training": ("HR", "Onboarding session", ["Welcome", "Tools and access", "Team norms", "First two weeks"]),
    "brand": ("Marketing", "Brand guidelines", ["Purpose", "Colour and typography", "Imagery", "Do and do not"]),
}

EDGE_CASE_FOLDER = "Edge cases"


def random_date(i: int) -> datetime:
    """Spread files across Jan 2026 to today, with a cluster in the last two weeks."""
    if i % 5 == 0:
        return TODAY - timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 9))
    if i % 7 == 0:
        return TODAY - timedelta(days=rng.randint(7, 30))
    span = (TODAY - datetime(2026, 1, 5)).days
    return datetime(2026, 1, 5) + timedelta(days=rng.randint(0, span), hours=rng.randint(8, 17))


def body_text(sentences):
    picked = rng.sample(sentences, k=min(3, len(sentences)))
    return " ".join(picked)


def write_docx(path: Path, topic_key: str, when: datetime):
    _, _, heading, sentences = TOPICS[topic_key]
    doc = Document()
    doc.add_heading(heading, level=1)
    owner = rng.choice(PEOPLE)
    client = rng.choice(CLIENTS)
    project = rng.choice(PROJECTS)
    doc.add_paragraph(f"Date: {when:%d %B %Y}. Owner: {owner}. Project: {project}. Client: {client}.")
    for _ in range(rng.randint(2, 4)):
        doc.add_paragraph(body_text(sentences))
    doc.add_heading("Next steps", level=2)
    for _ in range(rng.randint(2, 4)):
        doc.add_paragraph(f"{rng.choice(PEOPLE)} to {rng.choice(['confirm', 'update', 'share', 'review'])} {rng.choice(['the plan', 'the budget', 'the timeline', 'the risks', 'the draft'])} by {(when + timedelta(days=rng.randint(3, 14))):%d %B}.", style="List Bullet")
    doc.save(path)


def write_pptx(path: Path, topic_key: str, when: datetime):
    _, title, bullets = PPTX_TOPICS[topic_key]
    prs = Presentation()
    title_layout, content_layout = prs.slide_layouts[0], prs.slide_layouts[1]
    slide = prs.slides.add_slide(title_layout)
    slide.shapes.title.text = title
    slide.placeholders[1].text = f"{rng.choice(PROJECTS)} · {when:%B %Y}"
    for heading in bullets:
        s = prs.slides.add_slide(content_layout)
        s.shapes.title.text = heading
        tf = s.placeholders[1].text_frame
        tf.text = rng.choice(["On track against the plan", "Needs a decision this week", "Data is being validated"])
        for _ in range(rng.randint(1, 3)):
            tf.add_paragraph().text = rng.choice([
                f"Owner: {rng.choice(PEOPLE)}",
                f"Client: {rng.choice(CLIENTS)}",
                "Next review booked for the coming week",
            ])
    prs.save(path)


def generate(out: Path) -> list[tuple[Path, datetime]]:
    """Writes the corpus under `out` and returns (path, intended modified time) for every file.

    Resets the random generator first, so repeated calls produce identical corpora.
    """
    global rng
    rng = random.Random(SEED)
    out.mkdir(parents=True, exist_ok=True)

    topic_keys = list(TOPICS)
    written = []

    for i in range(TOTAL_DOCX):
        topic = topic_keys[i % len(topic_keys)]
        folder, stem, _, _ = TOPICS[topic]
        when = random_date(i)
        target = out / folder
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{stem} {i + 1:03d} {when:%Y-%m-%d}.docx"
        write_docx(path, topic, when)
        written.append((path, when))

    pptx_keys = list(PPTX_TOPICS)
    for i in range(TOTAL_PPTX):
        topic = pptx_keys[i % len(pptx_keys)]
        folder, stem, _ = PPTX_TOPICS[topic]
        when = random_date(i + 100)
        target = out / folder
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{stem} {i + 1:03d} {when:%Y-%m-%d}.pptx"
        write_pptx(path, topic, when)
        written.append((path, when))

    # Edge cases the indexer should handle or report: an empty DOCX (no extractable text),
    # a file whose extension lies (not a real DOCX), and a DOCX with only a heading.
    edge = out / EDGE_CASE_FOLDER
    edge.mkdir(exist_ok=True)
    empty = edge / "Blank document.docx"
    Document().save(empty)
    written.append((empty, TODAY - timedelta(days=2)))
    broken = edge / "Corrupt export.docx"
    broken.write_bytes(b"this is not a real word document")
    written.append((broken, TODAY - timedelta(days=4)))
    headonly = edge / "Heading only.docx"
    d = Document()
    d.add_heading("Title only", level=1)
    d.save(headonly)
    written.append((headonly, TODAY - timedelta(days=9)))

    for path, when in written:
        ts = when.timestamp()
        os.utime(path, (ts, ts))

    return written


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ["USERPROFILE"]) / "HiveMind-test-corpus"
    print(f"Writing corpus to {out}")
    written = generate(out)
    print(f"Wrote {len(written)} files ({TOTAL_DOCX} docx, {TOTAL_PPTX} pptx, 3 edge cases)")


if __name__ == "__main__":
    main()
