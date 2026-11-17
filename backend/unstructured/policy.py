"""Resolution Guide / policy parser (Developer A).

The guide arrived 16 Nov as the "Resolution Guide" tab of the client's case-log workbook (client Q01/Q02):
v2, updated 2 Mar 2026, applies to EVERY case whatever its date; if an agent's action differs, the guide is right
and the gap must be shown. Each rule row becomes one chunk cited as `sheet:<tab>|row:<excel row>`, tagged with the
email categories it covers. The "Case Log" tab is B's and is not read here.

Files are found under <package>/tabular/ or <package>/docs/: by name (guide / policy / resolution), or an .xlsx
with a tab named that way. Supported: .xlsx (guide tab), .md / .txt (by heading, else paragraph), .csv (by row).
Other formats get a visible UNSUPPORTED_FORMAT outcome. No guide at all -> one SOURCE_MISSING outcome, and
search_policy says so instead of inventing a rule.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .paths import source_ref
from .xlsx import XlsxError, read_workbook

PARSER_VERSION = "policy-1.1"
NAME_HINTS = ("guide", "policy", "resolution")
SEARCH_DIRS = ("tabular", "docs")
SKIP_DIRS = ("complaint_emails",)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
VERSION_RE = re.compile(r"\bv(\d+)\b", re.I)
UPDATED_RE = re.compile(r"updated\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", re.I)
AUTHORITY = "Client Q02 (16 Nov 2026): one guide version in use; apply it to every case whatever the complaint date"

# Email category (emails.py) -> start of the guide's "Complaint type" cell. "corporate" = any MERL-C-* account.
CATEGORY_TO_GUIDE = {
    "late": "late delivery",
    "where_is_parcel": "parcel not received",
    "thrown_over_gate": "damaged / thrown parcel",
    "wrong_address": "wrong address",
    "cod_wrong": "cod overcharge",
    "missing_item": "item missing",
    "corporate": "corporate account",
}


def _has_hint(text: str) -> bool:
    return any(hint in text.lower() for hint in NAME_HINTS)


def _guide_tabs(path: Path) -> List[str]:
    try:
        return [name for name in read_workbook(path) if _has_hint(name)]
    except XlsxError:
        return []


def find_policy_files(data_dir: Path) -> List[Path]:
    found = []
    for sub in SEARCH_DIRS:
        root = data_dir / sub
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
                continue
            if _has_hint(path.name) or (path.suffix.lower() == ".xlsx" and _guide_tabs(path)):
                found.append(path)
    return found


def _chunk(source_id: str, ref: str, locator: str, text: str, heading: str = "", **extra: Any) -> Dict[str, Any]:
    """Text is kept as written (unmasked; B/C/D mask — John, 16 Nov)."""
    return {"source_id": source_id, "type": "document", "ref": ref, "locator": locator,
            "heading": heading, "text": text.strip(), **extra}


def _chunk_markdown(text: str, source_id: str, ref: str) -> List[Dict[str, Any]]:
    lines = text.split("\n")
    has_headings = any(HEADING_RE.match(line) for line in lines)
    chunks: List[Dict[str, Any]] = []
    heading, start, buf = "", 1, []

    def flush(end: int) -> None:
        body = "\n".join(buf).strip()
        if body:
            where = f"section:{heading}" if heading else "section:(preamble)"
            chunks.append(_chunk(source_id, ref, f"{where}|line:{start}-{end}", body, heading))

    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line) if has_headings else None
        new_paragraph = not has_headings and not line.strip()
        if m or new_paragraph:
            flush(i - 1)
            heading = m.group(2) if m else heading
            start, buf = i + 1, []
        else:
            buf.append(line)
    flush(len(lines))
    return chunks


def _chunk_csv(text: str, source_id: str, ref: str) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    chunks = []
    for n, row in enumerate(reader, start=1):
        parts = [f"{k}: {v}" for k, v in row.items() if k and v and v.strip()]
        if parts:
            chunks.append(_chunk(source_id, ref, f"row:{n}", "; ".join(parts)))
    return chunks


def _categories_for(complaint_type: str) -> List[str]:
    lowered = complaint_type.lower()
    return [cat for cat, start in CATEGORY_TO_GUIDE.items() if lowered.startswith(start)]


def _chunk_guide_sheet(tab: str, rows: List[Tuple[int, List[str]]], source_id: str, ref: str
                       ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Rule table: a header row starting 'Complaint type', one rule per row; then an optional 'Notes' block."""
    meta: Dict[str, Any] = {"tab": tab, "title": None, "version": None, "updated": None, "authority": AUTHORITY}
    header_i = next((i for i, (_, cells) in enumerate(rows)
                     if cells and cells[0].strip().lower().startswith("complaint type")), None)
    for _, cells in rows[: header_i if header_i is not None else len(rows)]:
        line = " ".join(c for c in cells if c).strip()
        if not line:
            continue
        meta["title"] = meta["title"] or line
        if meta["version"] is None and VERSION_RE.search(line):
            meta["version"] = "v" + VERSION_RE.search(line).group(1)
        if meta["updated"] is None and UPDATED_RE.search(line):
            try:
                meta["updated"] = datetime.strptime(UPDATED_RE.search(line).group(1), "%d %b %Y").date().isoformat()
            except ValueError:
                meta["updated"] = UPDATED_RE.search(line).group(1)
    if header_i is None:
        return [], meta
    headers = [h.strip() for h in rows[header_i][1]]
    common = {"guide_version": meta["version"], "guide_updated": meta["updated"], "authority": AUTHORITY}
    chunks: List[Dict[str, Any]] = []
    in_notes = False
    for row_no, cells in rows[header_i + 1:]:
        values = [c.strip() for c in cells]
        if not any(values):
            continue
        locator = f"sheet:{tab}|row:{row_no}"
        if values[0].lower() == "notes" and not any(values[1:]):
            in_notes = True
            continue
        if in_notes:
            note = values[0].lstrip("•·-* ").strip()
            chunks.append(_chunk(source_id, ref, locator, note, "Notes", email_categories=[], **common))
            continue
        fields = {headers[i] if i < len(headers) and headers[i] else f"col{i + 1}": v for i, v in enumerate(values) if v}
        text = ". ".join(f"{k}: {v}" for k, v in fields.items())
        chunks.append(_chunk(source_id, ref, locator, text, values[0], fields=fields,
                             email_categories=_categories_for(values[0]), **common))
    return chunks, meta


def parse_policy_file(path: Path, data_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw = path.read_bytes()
    ref = source_ref(path, data_dir)
    source_id = f"policy:{path.stem}"
    entry: Dict[str, Any] = {"source_id": source_id, "kind": "policy", "ref": ref,
                             "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                             "parser_version": PARSER_VERSION, "status": "ok", "issues": []}
    suffix = path.suffix.lower()

    def fail(code: str, message: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        entry["status"] = "failed"
        entry["issues"].append({"code": code, "message": message})
        return [], entry

    if suffix == ".xlsx":
        try:
            book = read_workbook(path)
        except XlsxError as exc:
            return fail("BAD_XLSX", str(exc))
        tabs = [name for name in book if _has_hint(name)] or (list(book)[:1] if _has_hint(path.name) else [])
        chunks: List[Dict[str, Any]] = []
        slug = lambda tab: re.sub(r"[^a-z0-9]+", "_", tab.lower()).strip("_")  # noqa: E731
        for tab in tabs:
            tab_chunks, meta = _chunk_guide_sheet(tab, book[tab], f"policy:{path.stem}:{slug(tab)}", ref)
            chunks.extend(tab_chunks)
            entry.setdefault("guide", []).append(meta)
        entry["source_id"] = f"policy:{path.stem}:{slug(tabs[0])}" if len(tabs) == 1 else source_id
        entry["tabs_skipped"] = [name for name in book if name not in tabs]  # e.g. "Case Log" belongs to B
    elif suffix in (".md", ".txt", ".csv"):
        try:
            text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError as exc:
            return fail("NOT_UTF8", f"cannot decode as UTF-8 at byte {exc.start}")
        chunks = _chunk_csv(text, source_id, ref) if suffix == ".csv" else _chunk_markdown(text, source_id, ref)
    else:
        return fail("UNSUPPORTED_FORMAT", f"no parser for {suffix or 'no extension'}")
    if not chunks:
        entry["status"] = "failed"
        entry["issues"].append({"code": "EMPTY_SOURCE", "message": "no rule text found to index"})
    entry["chunks"] = len(chunks)
    return chunks, entry


def missing_entry() -> Dict[str, Any]:
    return {"source_id": "policy:resolution_guide", "kind": "policy", "ref": None, "sha256": None,
            "bytes": 0, "parser_version": PARSER_VERSION, "status": "failed",
            "issues": [{"code": "SOURCE_MISSING",
                        "message": "Resolution Guide not found under <package>/tabular/ (client sent it with Q01 as "
                                   "the 'Resolution Guide' tab of CS_case_log_Oct25-Jun26.xlsx; copy it there)"}]}


def ingest_policy(data_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    files = find_policy_files(data_dir)
    if not files:
        return [], [missing_entry()]
    chunks: List[Dict[str, Any]] = []
    entries = []
    for path in files:
        file_chunks, entry = parse_policy_file(path, data_dir)
        chunks.extend(file_chunks)
        entries.append(entry)
    return chunks, entries
