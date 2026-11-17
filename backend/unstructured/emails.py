"""Complaint-email parser (Developer A, task 4).

One record per file in data/docs/complaint_emails/. No LLM calls (regex + templates), so no API spend.
Record shape: docs/02-Design/contracts.md section 4. Traps referenced: docs/05-Reviews/trap_list.md.

What it does NOT do:
- Hide personal data. Records are UNMASKED on purpose (team decision, John, 16 Nov): B/C/D mask before the AI
  model or a customer sees anything. `pii_detected` counts what masking.mask_text would hide, to help them.
- Decide whether an order number is v1 or v2. That is B's candidate lookup (T-A01); this parser only passes on
  the number, the email date and any explicit V1/V2 prefix.
Records live in output/ (git-ignored). Never commit them.
"""
from __future__ import annotations

import hashlib
import re
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .masking import mask_text
from .paths import source_ref

PARSER_VERSION = "emails-1.0"
REQUIRED_HEADERS = ("From", "To", "Date", "Subject")
HEADER_RE = re.compile(r"^([A-Za-z-]+):[ \t]*(.*)$")

# Checked against the subject first, then the body. First match wins.
CATEGORY_RULES = [
    ("compliment", re.compile(r"\bcompliment", re.I)),
    ("wrong_address", re.compile(r"\bwrong (?:address|block)\b", re.I)),
    ("missing_item", re.compile(r"\bmissing\b", re.I)),
    ("where_is_parcel", re.compile(r"\bwhere is my (?:parcel|order)\b|\bIN_TRANSIT\b", re.I)),
    ("cod_wrong", re.compile(r"\bCOD\b", re.I)),
    ("late", re.compile(r"\blate\b", re.I)),
    ("thrown_over_gate", re.compile(r"\bthr(?:ew|own)\b.*\bgate\b", re.I | re.S)),
]
CATEGORIES = [name for name, _ in CATEGORY_RULES] + ["unclassified"]

# 5-digit order number, optional V1-/V2- prefix. Not part of a longer number, amount ($), unit (#) or code.
ORDER_RE = re.compile(r"(?<![\w$#/.-])(?:(V[12])-)?(\d{5})(?!\d)", re.I)
BLOCK_BEFORE_RE = re.compile(r"\b(?:blk|block)\s*$", re.I)
DRIVER_RE = re.compile(r"\bDRV\d{3}\b")
CORPORATE_RE = re.compile(r"\bMERL-C-\d{4}\b")
AND_OTHERS_RE = re.compile(r"\band others\b", re.I)
STAY_BLOCK_RE = re.compile(r"\b(?:stay|live)(?: at)?\s+(?:blk|block)\s*(\d{1,4}[A-Z]?)\b", re.I)
POD_BLOCK_RE = re.compile(r"\b(?:POD|photo)\b[^.!?\n]*?\b(?:blk|block)\s*(\d{1,4}[A-Z]?)\b", re.I)
DAYS_AGO_RE = re.compile(r"\b(\d{1,3})\s+days?\s+ago\b", re.I)
AMOUNT_EXTRA_RE = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)\s+extra\b", re.I)
STATUS_CLAIM_RE = re.compile(r"\b(IN_TRANSIT|DELIVERED|RETURNED|FAILED_ATTEMPT)\b")


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def _split_headers(text: str) -> Tuple[Dict[str, str], str, int, List[Dict[str, str]]]:
    """Headers run until the first blank line. Returns (headers, body, body_offset, issues)."""
    issues: List[Dict[str, str]] = []
    if "\n\n" not in text:
        return {}, "", len(text), [_issue("NO_BODY", "no blank line separating headers from body")]
    head, body = text.split("\n\n", 1)
    headers: Dict[str, str] = {}
    for line in head.split("\n"):
        m = HEADER_RE.match(line)
        if m:
            headers[m.group(1).title()] = m.group(2).strip()
        elif line.strip():
            issues.append(_issue("BAD_HEADER_LINE", f"unparsed header line ({len(line)} chars)"))
    return headers, body, len(head) + 2, issues


def classify(subject: str, body: str) -> str:
    for text in (subject, body):
        for name, pattern in CATEGORY_RULES:
            if pattern.search(text):
                return name
    return "unclassified"


def _span(m: "re.Match[str]", group: int = 0) -> str:
    return f"body:char:{m.start(group)}-{m.end(group)}"


def extract_order_numbers(body: str) -> Tuple[List[str], List[str], Optional[str]]:
    """Return (order_numbers, locators, system_hint). Block numbers are never taken as orders."""
    numbers: List[str] = []
    locators: List[str] = []
    hints = set()
    for m in ORDER_RE.finditer(body):
        if BLOCK_BEFORE_RE.search(body[: m.start()]):
            continue
        if m.group(2) in numbers:
            continue
        numbers.append(m.group(2))
        locators.append(_span(m, 2))
        if m.group(1):
            hints.add(m.group(1).lower())
    system_hint = hints.pop() if len(hints) == 1 else None
    return numbers, locators, system_hint


def parse_email_text(text: str, source_id: str, ref: str) -> Dict[str, Any]:
    """Parse one email's text. Never raises on bad content: problems go into status/issues."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    headers, body, body_offset, issues = _split_headers(text)
    record: Dict[str, Any] = {
        "source_id": source_id,
        "type": "document",
        "ref": ref,
        "parser_version": PARSER_VERSION,
        "status": "ok",
        "issues": issues,
        "received_at": None,
        "sender": headers.get("From"),
        "to": headers.get("To"),
        "subject": headers.get("Subject"),
        "category": "unclassified",
        "is_complaint": None,
        "order_numbers": [],
        "system_hint": None,
        "more_orders_unspecified": False,
        "claims": {"stay_block": None, "pod_block": None, "days_ago": None, "amount_extra": None,
                   "status_claimed": None},
        "driver_codes": [],
        "corporate_account": None,
        "pii_detected": mask_text(body)[1],
        "body": body,
        "locators": {"body_offset_in_file": body_offset},
    }

    missing = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing or not body.strip():
        if missing:
            issues.append(_issue("MISSING_HEADER", "missing: " + ", ".join(missing)))
        if not body.strip() and "\n\n" in text:  # NO_BODY already covers files with no separator
            issues.append(_issue("EMPTY_BODY", "no body text"))
        record["status"] = "failed"
        return record

    locators: Dict[str, Any] = {"received_at": "header:Date", "sender": "header:From", "subject": "header:Subject",
                                "body_offset_in_file": body_offset}
    try:
        received = parsedate_to_datetime(headers["Date"])
        if received.tzinfo is None:
            issues.append(_issue("DATE_NO_TIMEZONE", "Date header has no timezone; left as naive"))
        record["received_at"] = received.isoformat()
    except (TypeError, ValueError, IndexError):
        issues.append(_issue("BAD_DATE", "Date header could not be parsed"))

    category = classify(headers["Subject"], body)
    record["category"] = category
    record["is_complaint"] = None if category == "unclassified" else category != "compliment"
    if category == "unclassified":
        issues.append(_issue("UNCLASSIFIED", "subject/body matched no known category"))

    numbers, order_locs, hint = extract_order_numbers(body)
    record["order_numbers"], record["system_hint"] = numbers, hint
    if numbers:
        locators["order_numbers"] = order_locs
    elif record["is_complaint"]:
        issues.append(_issue("NO_ORDER_NUMBER", "complaint without a 5-digit order number"))
    record["more_orders_unspecified"] = bool(numbers and AND_OTHERS_RE.search(body))

    claims = record["claims"]
    claim_rules = [
        ("stay_block", STAY_BLOCK_RE, str),
        ("pod_block", POD_BLOCK_RE, str),
        ("days_ago", DAYS_AGO_RE, int),
        ("amount_extra", AMOUNT_EXTRA_RE, float),
        ("status_claimed", STATUS_CLAIM_RE, str),
    ]
    claim_locs: Dict[str, str] = {}
    for key, pattern, cast in claim_rules:
        m = pattern.search(body)
        if m:
            claims[key] = cast(m.group(1))
            claim_locs[key] = _span(m, 1)
    if claim_locs:
        locators["claims"] = claim_locs

    drivers = list(dict.fromkeys(m.group(0) for m in DRIVER_RE.finditer(body)))
    record["driver_codes"] = drivers
    corp = CORPORATE_RE.search(body)
    if corp:
        record["corporate_account"] = corp.group(0)
        locators["corporate_account"] = _span(corp)
    if len(numbers) > 1:
        issues.append(_issue("MULTIPLE_ORDER_NUMBERS", f"{len(numbers)} order numbers in one email"))

    record["locators"] = locators
    if issues:
        record["status"] = "partial"
    return record


def parse_email_file(path: Path, data_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (record, manifest_entry) for one file. Unreadable files give a failed record, not an exception."""
    raw = path.read_bytes()
    ref = source_ref(path, data_dir)
    source_id = f"email:{path.stem}"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        record = parse_email_text("", source_id, ref)
        record["issues"] = [_issue("NOT_UTF8", f"cannot decode as UTF-8 at byte {exc.start}")]
        record["status"] = "failed"
    else:
        record = parse_email_text(text, source_id, ref)
    entry = {
        "source_id": source_id,
        "kind": "email",
        "ref": ref,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "parser_version": PARSER_VERSION,
        "status": record["status"],
        "issues": record["issues"],
    }
    return record, entry


def parse_email_dir(email_dir: Path, data_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    records, entries = [], []
    for path in sorted(email_dir.glob("*.txt")):
        record, entry = parse_email_file(path, data_dir)
        records.append(record)
        entries.append(entry)
    return records, entries
