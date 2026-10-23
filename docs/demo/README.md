# Demo data

Fictional files for the two-user HiveMind demo. The generated files are tracked in git under `files/`, so a fresh checkout already has them.

| Folder | Owner | Count | Contents |
|---|---|---|---|
| `files/User1/Public/Falcon/` | User 1 | 32 | Contracts, governance, meetings, demos for the Falcon project |
| `files/User1/Private/` | User 1 | 42 | Initiatives, performance, career, firm policies, working files. Never published |
| `files/User2/Public/Falcon/` | User 2 | 30 | Finance, discovery, delivery, technical, handover for the Falcon project |

Falcon is a fictional engagement to build a knowledge-search platform (the Harborview Platform) for a fictional client. All people are roles. All content is fictional.

## Use

Add each user's `Public` folder as that user's shared folder and mark the files public. User 1 also adds the `Private` folder and keeps it private.

Demo questions that work:

- "What is the approved Falcon budget?" ($48,200, from User 1's SOW or User 2's memo)
- "How is the Phase 2 budget split by role?" (User 2's budget breakdown, a teammate answer for User 1)
- "When is the warehouse cutover?" (User 2's migration plan, a teammate answer for User 1)
- "What is the knowledge reuse pilot budget?" ($22,000, User 1's own private files only)

Teammate files are skipped when a question has no topic or has a date range, so name a topic and avoid dates.

## Regenerate

```bash
pip install python-docx python-pptx fpdf2
cd docs/demo
python generate_demo_data.py
python check_demo_data.py --rendered files
```

The generator overwrites `files/` with identical content. The check confirms 104 files, that each opens, that metadata dates match the manifest, that the planted facts are present, and that private and teammate-only facts have not leaked into the wrong files.

## How it fits together

- `facts.py`: shared money, dates, thresholds and the sprint calendar.
- `manifest.py`: the 104 files with folder, created date, revised date and author. The single source of truth for paths and dates.
- `content/`: one module per group of files, holding only the bodies. See `content/README.md` to add or change a file.
- `render.py`: writes DOCX, PPTX, PDF and TXT. Slide decks use the Deloitte palette and type (no logo). Created and modified dates are written into each file's metadata and the file modified time.
- `build.py`, `generate_demo_data.py`, `check_demo_data.py`: loading, generation and validation.

## Add a file

1. Add a row to `manifest.py` (path, created, revised, author or `None`).
2. Add the body to the matching module in `content/` (or a new module listed in `build.MODULES`).
3. Update the counts in `check_demo_data.py` if the totals change, then regenerate and check.
