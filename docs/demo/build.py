"""Collect content modules and merge them with the manifest into full entries."""

import importlib
from pathlib import PurePosixPath

from manifest import MANIFEST, user_of

MODULES = [
    "user1_contracts", "user1_governance", "user1_meetings", "user1_demos",
    "user2_finance", "user2_discovery", "user2_delivery", "user2_technical", "user2_handover",
    "private_initiatives", "private_performance", "private_career", "private_firm", "private_working",
]

CONTENT_KEYS = ("blocks", "slides", "text")


def manifest_by_name():
    by_name = {}
    for path, created, revised, author in MANIFEST:
        by_name[PurePosixPath(path).name] = (path, created, revised, author)
    return by_name


def load_entries(modules=None):
    """Return (entries, problems). Entries are full dicts ready to render."""
    by_name = manifest_by_name()
    entries, problems, seen = [], [], set()
    for module_name in modules or MODULES:
        try:
            module = importlib.import_module(f"content.{module_name}")
        except ModuleNotFoundError as error:
            problems.append(f"{module_name}: cannot import ({error})")
            continue
        for item in getattr(module, "FILES", []):
            name = item.get("file")
            if name not in by_name:
                problems.append(f"{module_name}: '{name}' is not in the manifest")
                continue
            if name in seen:
                problems.append(f"{module_name}: '{name}' is defined twice")
                continue
            seen.add(name)
            present = [key for key in CONTENT_KEYS if key in item]
            if len(present) != 1:
                problems.append(f"{module_name}: '{name}' needs exactly one of {CONTENT_KEYS}")
                continue
            path, created, revised, author = by_name[name]
            entry = {
                "path": path,
                "title": PurePosixPath(name).stem,
                "author": author or user_of(path),
                "created": created,
                "revised": revised,
                present[0]: item[present[0]],
                "module": module_name,
            }
            entries.append(entry)
    if modules is None:
        for name in by_name:
            if name not in seen:
                problems.append(f"manifest file '{name}' has no content")
    return entries, problems
