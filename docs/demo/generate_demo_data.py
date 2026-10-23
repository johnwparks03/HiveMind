"""Generate the fictional HiveMind demo files (104 files, two users).

Usage:
    python generate_demo_data.py [output_root]

Default output root: docs/demo/files next to this script (tracked in git).
Requires: python-docx, python-pptx, fpdf2.

Paths, dates and authors come from manifest.py. Bodies come from content/*.py.
Facts and the timeline live in facts.py. Re-running overwrites the files with
identical content. Run check_demo_data.py afterwards.
"""

import sys
from pathlib import Path

from build import load_entries
from render import render_entry


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "files"
    entries, problems = load_entries()
    if problems:
        for problem in problems:
            print("PROBLEM:", problem)
        sys.exit("Fix the problems above before generating.")
    for entry in entries:
        print(render_entry(entry, root))
    print(f"Wrote {len(entries)} files under {root}")


if __name__ == "__main__":
    main()
