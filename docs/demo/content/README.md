# Writing demo content

Each module in this folder supplies the bodies for a group of demo files. Paths, dates and authors come from `../manifest.py`; shared facts and the timeline come from `../facts.py`. Do not edit those two files from a content module.

## Module shape

```python
from facts import PHASE2_BUDGET, APPROVAL_DATE, sprint_text   # import what you use

FILES = [
    {"file": "Statement of Work - Phase 2.pdf", "blocks": [...]},   # docx and pdf
    {"file": "Falcon Proposal Deck.pptx", "slides": [...]},         # pptx
    {"file": "Weekly Status Notes - Q2 2026.txt", "text": "..."},   # txt
]
```

`file` is the exact file name from the manifest. The loader fills in the folder, title (the file name without extension), author, created date and revised date.

## DOCX and PDF blocks

- `("h1", "Title")`: first block, always.
- `("p", "Summary paragraph")`: second block, always. It names the topic, the period it covers and the purpose of the file, because search tags come from the first ~3,000 characters.
- `("h2", "Heading")`, `("p", "Text")`
- `("bullets", ["item", "item"])`
- `("table", ["Col A", "Col B"], [["a1", "b1"], ["a2", "b2"]], [0.6, 0.4])`: the optional fourth item gives relative column widths (PDF only).

## PPTX slides

- First slide: `{"title": "Falcon Phase 2 Kickoff", "subtitle": "One line of context and date"}`.
- Other slides: `{"title": "Objectives", "bullets": ["...", "..."]}`.
- 6 to 10 slides in total, 2 to 5 bullets per slide, each bullet under 110 characters. The last word of each title is shown in the brand accent style, so choose it deliberately.

## TXT

A single string. The first line is an UPPERCASE title. Plain text, dated entries where the file is a log.

## Style rules

- 150 to 450 words per file (a txt log may use up to 700). Concrete detail: IDs, owners by role, dates, numbers, decisions, actions. Write like a real internal project document, not a template.
- Fictional only. Refer to people by role: Executive sponsor, Project lead (User 1), Delivery lead (User 2), Client sponsor, Client delivery lead, Finance business partner, engineers, analysts. The client is Brightwater Logistics. No real people, companies or products beyond generic technology names.
- Write as of the file's revised date. A document can mention later events only as plans. A document must not refer to something as done if it happens after the revised date.
- Use `facts.py` for money, dates and thresholds so every file agrees. Use `sprint_text(n)` for sprint dates. Do not invent other totals, budgets or dates that other files could contradict (for example another Phase 2 total, a different cutover date).
- ASCII punctuation (plain hyphens, straight quotes) in all files. Use "percent" instead of the percent sign in prose.
- User 1 files must not contain the teammate-only facts (the Phase 2 split amounts, the 2 November 2026 cutover date, the 98.5 percent threshold, the 4 seconds Ask target). They can mention the warehouse cutover without a date ("planned for early November" is fine).
- Public files must not contain the private facts ($22,000 pilot budget, 15 December 2026 go-live, "Knowledge Reuse").
- Do not mention User 3. There are two users.
- Series files (status notes, logs, trackers, burn reports) carry dated entries inside the text so the time frame is visible.

## Check your work

```bash
python check_demo_data.py --module user1_contracts
```

Run it from `docs/demo/` with Python that has `python-docx`, `python-pptx` and `fpdf2` installed. It lists every problem with the file name.
