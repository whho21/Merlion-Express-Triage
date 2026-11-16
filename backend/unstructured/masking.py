"""Shared PII masking helper for B/C/D (PDPA, trap T-A19). C may move it into its guardrail module.

Team decision (John, 16 Nov): A's records are UNMASKED; B/C/D mask before the AI model or a customer sees
anything. A only uses mask_text() to COUNT personal data (emails.pii_detected), never to change records.

Rules are applied in order; earlier rules win (an 8-digit phone is masked before the 6-digit postal rule runs).
Order numbers (5 digits) and driver codes (DRV000) are deliberately left visible.

Limitation: personal names inside free text are NOT detected by these rules; the guardrail must check names
(e.g. the POD received_by field and email sender addresses, which are name-based).
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

MASK_RULES: List[Tuple[str, "re.Pattern[str]", str]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    ("nric", re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.I), "[NRIC]"),
    # Singapore numbers: 8 digits starting 3/6/8/9, optional +65 and one space/dash in the middle.
    ("phone", re.compile(r"(?<![\w$])(?:\+65[\s-]?)?[3689]\d{3}[\s-]?\d{4}(?!\d)"), "[PHONE]"),
    ("unit", re.compile(r"#\s?\d{1,3}-\d{1,5}[A-Z]?\b"), "[UNIT]"),
    ("postal", re.compile(r"(?<![\w$])(?:S(?:ingapore)?\s?)?\d{6}(?!\d)"), "[POSTAL]"),
    ("block", re.compile(r"\b(?:blk|block)\s*\d{1,4}[A-Z]?\b", re.I), "blk [BLOCK]"),
]


def mask_text(text: str) -> Tuple[str, Dict[str, int]]:
    """Return (masked_text, counts per rule). Counts only include rules that matched."""
    counts: Dict[str, int] = {}
    for name, pattern, replacement in MASK_RULES:
        text, n = pattern.subn(replacement, text)
        if n:
            counts[name] = n
    return text, counts
