"""Check the demo data: structure, facts, privacy rules and (optionally) the rendered files.

Usage:
    python check_demo_data.py                 # check all content modules
    python check_demo_data.py --module NAME   # check one content module (partial)
    python check_demo_data.py --rendered DIR  # also open every rendered file under DIR

Exit code is 0 only when there are no problems.
"""

import argparse
import re
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

from build import MODULES, load_entries
from facts import (
    APPROVAL_DATE, ASK_TARGET, CUTOVER, EXPENSE_THRESHOLD, FORBIDDEN_PHRASES, PHASE2_BUDGET,
    PHASE2_SPLIT, PILOT_BUDGET, PILOT_GO_LIVE, PRIVATE_ONLY_TOKENS, QUALITY_THRESHOLD,
    SOW1_VALUE, TEAMMATE_ONLY_TOKENS, CO01_AMOUNT, money,
)
from manifest import MANIFEST, user_of, visibility_of
from render import render_entry, ts

TODAY = date(2026, 10, 22)
SLIDE_RANGE = (6, 10)
MIN_WORDS = {".docx": 120, ".pdf": 120, ".txt": 80}

# fact -> file names that must contain it
REQUIRED = {
    PHASE2_BUDGET: ["Statement of Work - Phase 2.pdf", "Kickoff Deck - Phase 2.pptx",
                    "Steering Minutes 2026-09-14.docx", "Phase 2 Budget Approval Memo.docx"],
    APPROVAL_DATE: ["Steering Minutes 2026-09-14.docx", "Phase 2 Budget Approval Memo.docx"],
    SOW1_VALUE: ["Statement of Work - Phase 1.pdf"],
    CO01_AMOUNT: ["Change Order 01 - CRM Integration.docx"],
    money(PHASE2_SPLIT["Engineering"]): ["Phase 2 Budget Breakdown.pdf", "Forecast vs Actual - Q3 2026.docx"],
    CUTOVER: ["Data Migration Plan.docx"],
    QUALITY_THRESHOLD: ["Data Migration Plan.docx", "Test Plan.docx"],
    "Sprint 14": ["Sprint 14 Planning.docx", "Sprint 14 Demo Script.docx"],
    ASK_TARGET: ["UAT Plan.docx", "Test Plan.docx"],
    PILOT_BUDGET: ["Knowledge Reuse Pilot - Charter.docx", "Knowledge Reuse Pilot - Business Case.pptx"],
    PILOT_GO_LIVE: ["Knowledge Reuse Pilot - Charter.docx"],
    EXPENSE_THRESHOLD: ["Expense Policy Summary FY27.pdf"],
}


def entry_text(entry):
    """All text of an entry as one string, for substring checks."""
    parts = []
    if "text" in entry:
        parts.append(entry["text"])
    for block in entry.get("blocks", []):
        for part in block[1:]:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, list):
                for item in part:
                    parts.extend(item if isinstance(item, list) else [item])
    for slide in entry.get("slides", []):
        parts.append(slide.get("title", ""))
        parts.append(slide.get("subtitle", ""))
        parts.extend(slide.get("bullets", []))
    return "\n".join(str(part) for part in parts)


def check_structure(entry, problems):
    name = Path(entry["path"]).name
    suffix = Path(entry["path"]).suffix.lower()
    tag = f"{entry['module']}/{name}"
    created, revised = ts(entry["created"]).date(), ts(entry["revised"]).date()
    if created > revised:
        problems.append(f"{tag}: created is after revised")
    if revised > TODAY:
        problems.append(f"{tag}: revised is in the future")
    text = entry_text(entry)
    if suffix == ".pptx":
        slides = entry.get("slides")
        if slides is None:
            problems.append(f"{tag}: pptx needs slides")
            return text
        low, high = SLIDE_RANGE
        if not low <= len(slides) <= high:
            problems.append(f"{tag}: {len(slides)} slides, expected {low} to {high}")
        if "subtitle" not in slides[0]:
            problems.append(f"{tag}: first slide needs a subtitle")
        for number, slide in enumerate(slides[1:], start=2):
            bullets = slide.get("bullets", [])
            if not 2 <= len(bullets) <= 5:
                problems.append(f"{tag}: slide {number} has {len(bullets)} bullets, expected 2 to 5")
            for bullet in bullets:
                if len(bullet) > 110:
                    problems.append(f"{tag}: slide {number} bullet is {len(bullet)} characters (max 110)")
    else:
        key = "text" if suffix == ".txt" else "blocks"
        if key not in entry:
            problems.append(f"{tag}: {suffix} needs {key}")
            return text
        words = len(text.split())
        if words < MIN_WORDS[suffix]:
            problems.append(f"{tag}: only {words} words (min {MIN_WORDS[suffix]})")
        if words > 700:
            problems.append(f"{tag}: {words} words (max 700, keep files short)")
        if suffix in (".docx", ".pdf"):
            blocks = entry["blocks"]
            if not blocks or blocks[0][0] != "h1":
                problems.append(f"{tag}: first block must be h1")
            elif len(blocks) < 2 or blocks[1][0] != "p":
                problems.append(f"{tag}: second block must be a summary paragraph (p)")
            for block in blocks:
                if block[0] == "table":
                    width = len(block[1])
                    if any(len(row) != width for row in block[2]):
                        problems.append(f"{tag}: table rows must match the header width")
        if suffix == ".txt" and not text.strip().splitlines()[0].isupper():
            problems.append(f"{tag}: first line of a txt file should be an UPPERCASE title")
    if suffix == ".pdf":
        bad = sorted({ch for ch in text if ord(ch) > 255})
        # Smart punctuation is converted by the renderer; anything else is flagged.
        bad = [ch for ch in bad if ch not in "‘’“”–—•… "]
        if bad:
            problems.append(f"{tag}: characters not supported in PDF: {''.join(bad)}")
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in text.lower():
            problems.append(f"{tag}: contains forbidden phrase '{phrase}'")
    return text


def check_privacy(entries, texts, problems):
    for entry in entries:
        path, name = entry["path"], Path(entry["path"]).name
        text = texts[path]
        owner, visibility = user_of(path), visibility_of(path)
        if visibility == "public":
            for token in PRIVATE_ONLY_TOKENS:
                if token.lower() in text.lower():
                    problems.append(f"{name}: public file contains private fact '{token}'")
        if owner == "User 1":
            for token in TEAMMATE_ONLY_TOKENS:
                if token.lower() in text.lower():
                    problems.append(f"{name}: User 1 file contains teammate-only fact '{token}'")


def check_required(entries, texts, problems):
    by_name = {Path(e["path"]).name: texts[e["path"]] for e in entries}
    for fact, names in REQUIRED.items():
        for name in names:
            if name in by_name and fact.lower() not in by_name[name].lower():
                problems.append(f"{name}: missing planted fact '{fact}'")


def check_manifest(problems):
    if len(MANIFEST) != 104:
        problems.append(f"manifest has {len(MANIFEST)} rows, expected 104")
    user1_public = sum(1 for p, *_ in MANIFEST if p.startswith("User1/Public/"))
    user2_public = sum(1 for p, *_ in MANIFEST if p.startswith("User2/Public/"))
    private = sum(1 for p, *_ in MANIFEST if "/Private/" in p)
    if (user1_public, user2_public, private) != (32, 30, 42):
        problems.append(f"manifest split is {user1_public}/{user2_public}/{private}, expected 32/30/42")
    names = [Path(p).name for p, *_ in MANIFEST]
    if len(set(names)) != len(names):
        problems.append("manifest has duplicate file names")


def check_rendered(entries, problems, root=None):
    """Render every entry and confirm the file opens and its dates match the manifest."""
    from docx import Document
    from pptx import Presentation

    with tempfile.TemporaryDirectory() as temp:
        base = Path(root) if root else Path(temp)
        for entry in entries:
            out = render_entry(entry, base) if root is None else base / entry["path"]
            name = out.name
            if not out.exists():
                problems.append(f"{name}: not found in {base}")
                continue
            created = entry["created"]
            try:
                if out.suffix == ".docx":
                    props = Document(out).core_properties
                    got = (props.created.strftime("%Y-%m-%d"), props.modified.strftime("%Y-%m-%d"))
                elif out.suffix == ".pptx":
                    presentation = Presentation(out)
                    props = presentation.core_properties
                    got = (props.created.strftime("%Y-%m-%d"), props.modified.strftime("%Y-%m-%d"))
                    if len(presentation.slides) != len(entry["slides"]):
                        problems.append(f"{name}: slide count mismatch")
                elif out.suffix == ".pdf":
                    data = out.read_bytes()
                    if not data.startswith(b"%PDF"):
                        problems.append(f"{name}: not a PDF")
                        continue
                    match = re.search(rb"/CreationDate \(D:(\d{8})", data)
                    got = (datetime.strptime(match.group(1).decode(), "%Y%m%d").strftime("%Y-%m-%d"), None)
                else:
                    got = (None, None)
                if got[0] and got[0] != created:
                    problems.append(f"{name}: created {got[0]} != manifest {created}")
                if got[1] and got[1] != entry["revised"]:
                    problems.append(f"{name}: modified {got[1]} != manifest {entry['revised']}")
                mtime = datetime.fromtimestamp(out.stat().st_mtime).strftime("%Y-%m-%d")
                if mtime != entry["revised"]:
                    problems.append(f"{name}: file mtime {mtime} != manifest {entry['revised']}")
            except Exception as error:  # noqa: BLE001 - report any failure to open
                problems.append(f"{name}: failed to open ({error!r})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", action="append", help="check only this content module")
    parser.add_argument("--rendered", help="check already-rendered files under this folder")
    args = parser.parse_args()

    problems = []
    check_manifest(problems)
    entries, load_problems = load_entries(args.module)
    problems.extend(load_problems)
    texts = {entry["path"]: check_structure(entry, problems) for entry in entries}
    check_privacy(entries, texts, problems)
    if not args.module:
        check_required(entries, texts, problems)
    check_rendered(entries, problems, args.rendered)

    scope = ", ".join(args.module) if args.module else f"all {len(MODULES)} modules"
    print(f"Checked {len(entries)} files ({scope}).")
    for problem in problems:
        print("PROBLEM:", problem)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
