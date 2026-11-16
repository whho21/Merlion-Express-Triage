"""Rate-card extraction and lookup (Developer A, task 5). Record shape: docs/02-Design/contracts.md section 3.

The model copies the table cell by cell; code parses prices, bands, surcharges and notes.
Traps enforced here:
  T-A15  a date before the card's effective_from -> not_found (never falls back to the April card silently)
  T-A16  a weight exactly on a shared band edge (3 kg, 10 kg) -> ambiguous, both candidates returned
Zone and service type are NOT in the orders table (client question A-Q4): the caller must supply them.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

PROMPT_VERSION = "ratecard-v1"
PROMPT = """You are reading a scanned courier rate card.
Copy every value EXACTLY as printed. Do not calculate, convert or guess. Use null for anything unreadable
and list it in "unreadable".
Return one JSON object with these keys:
  "title": the company line at the top,
  "effective_text": the line that says when the card is effective, exactly as printed,
  "columns": the table header cells, left to right, exactly as printed,
  "rows": one object per table row, top to bottom: {"label": first cell, "cells": [the other cells, left to right]},
  "notes": every line of text below the table, one string per line, exactly as printed,
  "unreadable": list of anything you could not read with certainty."""

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], start=1)}
EFFECTIVE_RE = re.compile(r"effective\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", re.I)
PRICE_RE = re.compile(r"^\s*(\+)?\s*\$\s?(\d+(?:\.\d{1,2})?)\s*$")
BAND_RE = re.compile(r"^\s*(?:<=|≤|up to)\s*(\d+(?:\.\d+)?)\s*kg\s*$|^\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*kg\s*$",
                     re.I)


def _effective_from(text: Optional[str]) -> Optional[str]:
    m = EFFECTIVE_RE.search(text or "")
    if not m or m.group(2).lower() not in MONTHS:
        return None
    try:
        return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
    except ValueError:
        return None


def _band(label: str) -> Optional[Dict[str, Any]]:
    m = BAND_RE.match(label or "")
    if not m:
        return None
    if m.group(1):
        return {"band": label.strip(), "min_kg": 0.0, "max_kg": float(m.group(1))}
    return {"band": label.strip(), "min_kg": float(m.group(2)), "max_kg": float(m.group(3))}


def _price(cell: Optional[str]) -> Optional[Dict[str, Any]]:
    m = PRICE_RE.match(cell or "")
    return {"amount": float(m.group(2)), "is_surcharge": bool(m.group(1))} if m else None


def _notes(lines: List[str]) -> Dict[str, Any]:
    text = " ".join(lines)
    parsed: Dict[str, Any] = {"raw": lines}
    m = re.search(r"COD handling:?\s*([\d.]+)%.*?min\s*\$?([\d.]+)", text, re.I)
    if m:
        parsed["cod_handling"] = {"pct": float(m.group(1)), "min": float(m.group(2))}
    m = re.search(r"re-?attempt:?\s*\$([\d.]+)\s*from\s*(\d+)", text, re.I)
    if m:
        parsed["reattempt_fee"] = {"amount": float(m.group(1)), "from_attempt": int(m.group(2))}
    m = re.search(r"before GST\s*\((\d+(?:\.\d+)?)%\)", text, re.I)
    parsed["gst_included"] = False if m else None
    if m:
        parsed["gst_pct"] = float(m.group(1))
    m = re.search(r"rebate\s*(\d+(?:\.\d+)?)%\s*above\s*([\d,]+)", text, re.I)
    if m:
        parsed["corporate_rebate"] = {"pct": float(m.group(1)), "above_parcels_per_month": int(m.group(2).replace(",", ""))}
    ph = [line for line in lines if "holiday" in line.lower()]
    if ph:
        parsed["public_holiday_rule"] = ph[0]
    return parsed


def normalise(answer: Dict[str, Any], *, source_id: str, image_ref: str, image_sha256: str,
              extraction: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, str]] = []
    columns = answer.get("columns") or []
    bands = [b for b in (_band(c) for c in columns[1:]) if b]
    surcharge_col = next((i for i, c in enumerate(columns[1:]) if "same" in (c or "").lower()), None)
    for a, b in zip(bands, bands[1:]):
        if a["max_kg"] >= b["min_kg"]:
            a["boundary_rule"] = b["boundary_rule"] = "UNRESOLVED (client A-Q4)"
    rows, surcharges = [], []
    for row in answer.get("rows") or []:
        label, cells = (row.get("label") or "").strip(), row.get("cells") or []
        prices = [_price(c) for c in cells]
        head = [p for p in prices[: len(bands)] if p]
        if head and all(p["is_surcharge"] for p in head):  # a "+$" row, e.g. "CBD ERP hours (0730-1900)"
            for band, p in zip(bands, prices):
                if p:
                    surcharges.append({"name": label, "band": band["band"], "amount": p["amount"]})
            continue
        for i, band in enumerate(bands):
            p = prices[i] if i < len(prices) else None
            if p is None:
                issues.append({"code": "PRICE_UNREADABLE", "message": f"row {label!r}, band {band['band']!r}"})
            rows.append({"zone": label, **band, "price": p["amount"] if p else None, "locator": f"row:{label}/col:{band['band']}"})
        if surcharge_col is not None and surcharge_col < len(cells):
            cell = cells[surcharge_col]
            p = _price(cell)
            surcharges.append({"name": "same_day", "zone": label, "amount": p["amount"] if p else None,
                               "available": p is not None, "raw": cell})
    effective_from = _effective_from(answer.get("effective_text"))
    if effective_from is None:
        issues.append({"code": "NO_EFFECTIVE_DATE", "message": "effective date not found on the card"})
    if not rows:
        issues.append({"code": "NO_RATES", "message": "no price rows read"})
    for name in answer.get("unreadable") or []:
        issues.append({"code": "MODEL_UNREADABLE", "message": str(name)})
    status = "failed" if not rows else ("partial" if issues else "ok")
    return {"source_id": source_id, "type": "image", "image_ref": image_ref, "image_sha256": image_sha256,
            "title": answer.get("title"), "effective_from": effective_from, "effective_to": None,
            "supersedes_previous": "supersede" in (answer.get("effective_text") or "").lower(),
            "currency": "SGD", "bands": bands, "rows": rows, "surcharges": surcharges,
            "notes": _notes(answer.get("notes") or []), "status": status, "issues": issues, "extraction": extraction}


def lookup_rate(cards: List[Dict[str, Any]], *, zone: str, weight_kg: float, on_date: str) -> Dict[str, Any]:
    """Price for one parcel. Returns the team's tool envelope with a citation per candidate."""
    day = datetime.fromisoformat(on_date).date()
    usable = [c for c in cards if c.get("effective_from") and date.fromisoformat(c["effective_from"]) <= day
              and (not c.get("effective_to") or day <= date.fromisoformat(c["effective_to"]))]
    if not usable:
        earliest = min((c["effective_from"] for c in cards if c.get("effective_from")), default=None)
        return {"ok": True, "status": "not_found", "data": None, "sources": [], "error": None,
                "reason": f"no rate card on file for {day.isoformat()} (earliest card starts {earliest}; client A-Q2)"}
    card = max(usable, key=lambda c: c["effective_from"])
    hits = [r for r in card["rows"] if r["zone"].lower() == zone.lower() and r["min_kg"] <= weight_kg <= r["max_kg"]]
    if not hits:
        return {"ok": True, "status": "not_found", "data": None, "sources": [], "error": None,
                "reason": f"no rate for zone {zone!r} at {weight_kg} kg on card {card['source_id']}"}
    data = [{"price": r["price"], "band": r["band"], "citation": {"source_id": card["source_id"], "type": "image",
             "ref": card["image_ref"], "locator": r["locator"], "record_key": None}} for r in hits]
    if len(hits) > 1:
        return {"ok": True, "status": "ambiguous", "data": data, "sources": [card["source_id"]], "error": None,
                "reason": f"{weight_kg} kg sits on a shared band edge; boundary rule unresolved (client A-Q4)"}
    return {"ok": True, "status": "found", "data": data[0], "sources": [card["source_id"]], "error": None}
