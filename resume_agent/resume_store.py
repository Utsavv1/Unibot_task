"""
resume_store.py
----------------
Single source of truth for the resume state.

The resume is loaded ONCE from resume.json (see RESUME_PATH below) into an
in-memory dict. All tools read and write through this module, so the schema
stays consistent no matter what the LLM does.

>>> To use a different resume, simply replace resume.json in this folder. <<<
"""

import json
import os
from typing import Any, Dict

# ---- The ONE place the resume comes from --------------------------------
RESUME_PATH = os.path.join(os.path.dirname(__file__), "resume.json")

_RESUME: Dict[str, Any] = {}


def load_resume() -> Dict[str, Any]:
    """Load resume.json from disk into the in-memory store."""
    global _RESUME
    with open(RESUME_PATH, "r", encoding="utf-8") as f:
        _RESUME = json.load(f)
    return _RESUME


def get_state() -> Dict[str, Any]:
    """Return the live in-memory resume dict (loading it on first access)."""
    if not _RESUME:
        load_resume()
    return _RESUME


# ---- ID helpers ----------------------------------------------------------
def next_id(prefix: str, items: list) -> str:
    """Generate a fresh unique id like 'skill5' that does not collide."""
    existing = {item.get("id") for item in items}
    i = 1
    while f"{prefix}{i}" in existing:
        i += 1
    return f"{prefix}{i}"


def find_by_id(items: list, item_id: str):
    """Return (index, item) for a given id, or (None, None) if not found."""
    for idx, item in enumerate(items):
        if item.get("id") == item_id:
            return idx, item
    return None, None


def resolve_index(items: list, ref: str):
    """
    Resolve a section item from a flexible reference string.

    Accepts:
      - an exact id           -> "exp2"
      - an ordinal word       -> "first", "second", "last"
      - a 1-based number       -> "1", "2"
    Returns (index, item) or (None, None).
    """
    if ref is None:
        return None, None
    ref = str(ref).strip().lower()

    ordinals = {
        "first": 0, "1st": 0,
        "second": 1, "2nd": 1,
        "third": 2, "3rd": 2,
        "fourth": 3, "4th": 3,
        "fifth": 4, "5th": 4,
    }

    # exact id match first
    idx, item = find_by_id(items, ref)
    if item is not None:
        return idx, item

    if ref == "last" and items:
        return len(items) - 1, items[-1]

    if ref in ordinals and ordinals[ref] < len(items):
        i = ordinals[ref]
        return i, items[i]

    if ref.isdigit():
        i = int(ref) - 1  # 1-based -> 0-based
        if 0 <= i < len(items):
            return i, items[i]

    return None, None
