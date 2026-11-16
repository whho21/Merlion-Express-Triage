"""Resolution Guide / policy parser (Developer A, task 4).

The guide is MISSING from the package (no tabular/ folder; client question A-Q1, trap T-A18). Until it arrives,
ingest records one failed outcome with code SOURCE_MISSING, and search_policy must say "policy not available"
instead of inventing a rule.

When a file arrives it is found by name (guide / policy / resolution) under data/tabular/ or data/docs/.
Supported now: .md / .txt (split by headings, else paragraphs) and .csv (one chunk per row).
Anything else (e.g. .pdf, .xlsx, .docx) gets a visible UNSUPPORTED_FORMAT outcome, so we know to extend it.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .masking import mask_text

PARSER_VERSION = "policy-1.0"
NAME_HINTS = ("guide", "policy", "resolution")
SEARCH_DIRS = ("tabular", "docs")
SKIP_DIRS = ("complaint_emails",)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def find_policy_files(data_dir: Path) -> List[Path]:
    found = []
    for sub in SEARCH_DIRS:
        root = data_dir / sub
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if (path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
                    and any(hint in path.name.lower() for hint in NAME_HINTS)):
                found.append(path)
    return found


def _chunk(source_id: str, ref: str, locator: str, text: str, heading: str = "") -> Dict[str, Any]:
    masked, _ = mask_text(text.strip())
    return {"source_id": source_id, "type": "document", "ref": ref, "locator": locator,
            "heading": heading, "text": masked}


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


def parse_policy_file(path: Path, data_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw = path.read_bytes()
    ref = "data/" + path.relative_to(data_dir).as_posix()
    source_id = f"policy:{path.stem}"
    entry: Dict[str, Any] = {"source_id": source_id, "kind": "policy", "ref": ref,
                             "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                             "parser_version": PARSER_VERSION, "status": "ok", "issues": []}
    suffix = path.suffix.lower()
    if suffix not in (".md", ".txt", ".csv"):
        entry["status"] = "failed"
        entry["issues"].append({"code": "UNSUPPORTED_FORMAT", "message": f"no parser for {suffix or 'no extension'}"})
        return [], entry
    try:
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        entry["status"] = "failed"
        entry["issues"].append({"code": "NOT_UTF8", "message": f"cannot decode as UTF-8 at byte {exc.start}"})
        return [], entry
    chunks = _chunk_csv(text, source_id, ref) if suffix == ".csv" else _chunk_markdown(text, source_id, ref)
    if not chunks:
        entry["status"] = "failed"
        entry["issues"].append({"code": "EMPTY_SOURCE", "message": "file has no text to index"})
    entry["chunks"] = len(chunks)
    return chunks, entry


def missing_entry() -> Dict[str, Any]:
    return {"source_id": "policy:resolution_guide", "kind": "policy", "ref": None, "sha256": None,
            "bytes": 0, "parser_version": PARSER_VERSION, "status": "failed",
            "issues": [{"code": "SOURCE_MISSING",
                        "message": "Resolution Guide not in package (no data/tabular/); client question A-Q1"}]}


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
