# Demo data generator

Creates the fictional files for the three-user HiveMind demo. User 1 has public and private files; User 2 and User 3 have public files only.

## Run

```bash
python generate_demo_data.py
```

This writes 23 files to `Documents\HiveMind Demo` in your home folder, outside the repo. Pass a different folder as the first argument to write somewhere else.

Requires `python-docx`, `python-pptx` and `fpdf2`:

```bash
pip install python-docx python-pptx fpdf2
```

## What it produces

- Folders split by subject, then by information type (see the layout in the demo plan).
- Created and modified dates set in each file's metadata. The file modified time matches the revised date.
- Planted facts (budget, sprint dates, cutover date, quality threshold, pilot budget) live in the constants at the top of the script. Change a value there and every file that uses it changes.
- Slide decks use the Deloitte brand palette and type (green circle motif, Open Sans headlines, one Stix Two Text italic word per headline). The logo lockup is not applied: the content is fictional and internal.

## Demo rules

- Teammates see only User 1's public files. The private folder is never published.
- Teammate Ask skips files when the question has no topic or has a date range. Name a topic and leave out dates in demo questions.
- Re-running overwrites the files with identical content.
