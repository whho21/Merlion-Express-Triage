"""A's retrieval tools for C (task 7): search_emails and search_policy. Signatures from team plan v0.4.

Keyword ranking (TF-IDF style) over the ingest output — no embeddings, no API spend. 90 short emails do not need
a vector index; revisit only if the Resolution Guide turns out to be long prose (plan: "embed only where useful").
Results use the common envelope {ok, status, data, sources, error}; every hit carries a citation whose locator
points at the exact characters quoted. Text is UNMASKED (John, 16 Nov): C masks before the model/customer.
Each call logs one telemetry line (tool, status, hit count, latency) — never the query text.
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm import log_telemetry

DEFAULT_OUT = Path("output") / "unstructured"
TOKEN_RE = re.compile(r"[a-z0-9_]+")
STOPWORDS = set("a an and are as at be but by for from has have i in is it its me my not of on or our so the "
                "this to was we with you your".split())
SNIPPET_CHARS = 240
# Everyday words -> the wording the guide/emails use. Query side only, so source text and citations never change.
# Added from measured misses on 17 Nov ("wrong block" vs "Wrong address", "cash on delivery" vs "COD").
QUERY_SYNONYMS = {
    "cash": "cod", "blk": "address", "block": "address", "unit": "address", "threw": "thrown", "throw": "thrown",
    "broke": "damaged", "broken": "damaged", "never": "received", "overcharged": "overcharge", "extra": "overcharge",
    "charged": "chargeable", "attempt": "attempts", "holiday": "ph", "corporate": "merl",
}


def _envelope(status: str, data: Any = None, sources: Optional[List[str]] = None,
              error: Optional[Dict[str, Any]] = None, **extra: Any) -> Dict[str, Any]:
    return {"ok": status != "failed", "status": status, "data": data, "sources": sources or [], "error": error, **extra}


def _tokens(text: str) -> List[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOPWORDS and len(t) > 1]


def _load_jsonl(path: Path) -> Optional[List[Dict[str, Any]]]:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _rank(query: str, docs: List[Dict[str, Any]], text_of) -> List[tuple]:
    """Return [(score, doc, first_hit_offset)] sorted best first, score > 0 only."""
    q = _tokens(query)
    if not q:
        return []
    q += [QUERY_SYNONYMS[t] for t in q if t in QUERY_SYNONYMS and QUERY_SYNONYMS[t] not in q]
    doc_tokens = [Counter(_tokens(text_of(d))) for d in docs]
    n = len(docs)
    idf = {t: math.log(1 + n / (1 + sum(1 for c in doc_tokens if t in c))) for t in set(q)}
    ranked = []
    for d, counts in zip(docs, doc_tokens):
        length = sum(counts.values()) or 1
        score = sum(idf[t] * counts[t] / (counts[t] + 1.2 * (0.25 + 0.75 * length / 40)) for t in q)
        if score > 0:
            text = text_of(d).lower()
            first = min((text.find(t) for t in q if t in text), default=0)
            ranked.append((round(score, 4), d, max(first, 0)))
    ranked.sort(key=lambda x: (-x[0], x[1].get("source_id", "")))
    return ranked


def _snippet(body: str, around: int) -> tuple:
    """Return (text, start, end) where body[start:end] == text exactly, so the locator can be checked."""
    start = max(0, min(around - 60, len(body) - SNIPPET_CHARS))
    end = min(len(body), start + SNIPPET_CHARS)
    raw = body[start:end]
    start += len(raw) - len(raw.lstrip())
    end -= len(raw) - len(raw.rstrip())
    return body[start:end], start, end


def search_emails(query: str = "", order_number: Optional[str] = None, *, top_k: int = 5,
                  out_dir: Path = DEFAULT_OUT) -> Dict[str, Any]:
    started = time.monotonic()
    result = _search_emails(query, order_number, top_k, out_dir)
    log_telemetry(out_dir / "telemetry.jsonl", tool="search_emails", status=result["status"],
                  hits=len(result["data"] or []), latency_ms=int((time.monotonic() - started) * 1000),
                  filtered_by_order=order_number is not None)
    return result


def _search_emails(query: str, order_number: Optional[str], top_k: int, out_dir: Path) -> Dict[str, Any]:
    records = _load_jsonl(out_dir / "emails.jsonl")
    if records is None:
        return _envelope("failed", error={"code": "INDEX_MISSING", "retryable": False,
                                          "message": "emails.jsonl not found; run python -m backend.unstructured.ingest"})
    usable = [r for r in records if r.get("status") != "failed"]
    if order_number is not None:
        wanted = str(order_number).strip()
        usable = [r for r in usable if wanted in r.get("order_numbers", [])]
    text_of = lambda r: f"{r.get('subject') or ''} {r.get('category') or ''} {r.get('body') or ''}"  # noqa: E731
    if query.strip():
        ranked = _rank(query, usable, text_of)
    else:  # order filter only: newest first
        ranked = [(1.0, r, 0) for r in sorted(usable, key=lambda r: r.get("received_at") or "", reverse=True)]
    hits = []
    for score, r, first in ranked[:top_k]:
        body = r.get("body") or ""
        offset_in_body = max(0, first - len(f"{r.get('subject') or ''} {r.get('category') or ''} "))
        text, start, end = _snippet(body, offset_in_body)
        hits.append({"text": text, "score": score, "category": r.get("category"), "is_complaint": r.get("is_complaint"),
                     "received_at": r.get("received_at"), "order_numbers": r.get("order_numbers"),
                     "citation": {"source_id": r["source_id"], "type": "document", "ref": r["ref"],
                                  "locator": f"body:char:{start}-{end}",
                                  "record_key": {"order_numbers": r.get("order_numbers")}}})
    if not hits:
        return _envelope("not_found", data=[])
    return _envelope("found", data=hits, sources=[h["citation"]["source_id"] for h in hits])


def search_policy(query: str = "", effective_date: Optional[str] = None, *, category: Optional[str] = None,
                  top_k: int = 5, out_dir: Path = DEFAULT_OUT) -> Dict[str, Any]:
    """Cited Resolution Guide rules.

    category: an email category from emails.py (late, wrong_address, cod_wrong, missing_item, thrown_over_gate,
    where_is_parcel) or "corporate" for MERL-C-* accounts; returns that complaint type's rule row directly.
    effective_date is accepted for the agreed signature but does not filter: the client says the one guide version
    (v2, 2 Mar 2026) applies to every case whatever its date (Q02). Each hit carries that authority.
    """
    started = time.monotonic()
    result = _search_policy(query, category, top_k, out_dir)
    log_telemetry(out_dir / "telemetry.jsonl", tool="search_policy", status=result["status"],
                  hits=len(result["data"] or []), latency_ms=int((time.monotonic() - started) * 1000),
                  by_category=category is not None, error=(result["error"] or {}).get("code"))
    return result


def _search_policy(query: str, category: Optional[str], top_k: int, out_dir: Path) -> Dict[str, Any]:
    manifest_path = out_dir / "manifest.json"
    chunks = _load_jsonl(out_dir / "policy_chunks.jsonl")
    if chunks is None or not manifest_path.is_file():
        return _envelope("failed", error={"code": "INDEX_MISSING", "retryable": False,
                                          "message": "policy index not built; run python -m backend.unstructured.ingest"})
    if not chunks:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        codes = [i["code"] for f in manifest.get("files", []) if f.get("kind") == "policy" for i in f.get("issues", [])]
        code = "SOURCE_MISSING" if "SOURCE_MISSING" in codes else (codes[0] if codes else "EMPTY_SOURCE")
        return _envelope("failed", data=[], error={
            "code": code, "retryable": False,
            "message": "Resolution Guide not available here, so no policy-based recommendation can be made. "
                       "Do not invent a policy. (The client sent it with Q01; copy the workbook into tabular/.)"})
    pool = chunks
    if category is not None:
        pool = [c for c in chunks if category in (c.get("email_categories") or [])]
        if not pool:
            return _envelope("not_found", data=[], reason=f"the Resolution Guide has no rule for category {category!r}")
    if query.strip():
        ranked = _rank(query, pool, lambda c: f"{c.get('heading') or ''} {c.get('text') or ''}")
    else:
        ranked = [(1.0, c, 0) for c in pool]
    hits = [{"text": c["text"][:SNIPPET_CHARS * 2], "score": score, "heading": c.get("heading"),
             "fields": c.get("fields"), "guide_version": c.get("guide_version"), "authority": c.get("authority"),
             "citation": {"source_id": c["source_id"], "type": "document", "ref": c["ref"], "locator": c["locator"],
                          "record_key": None}} for score, c, _ in ranked[:top_k]]
    if not hits:
        return _envelope("not_found", data=[])
    return _envelope("found", data=hits, sources=sorted({h["citation"]["source_id"] for h in hits}))