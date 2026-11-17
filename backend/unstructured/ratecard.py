"""Rate-card extraction and lookup (Developer A). Record shape: docs/02-Design/contracts_2026-11-16.md section 3.

The model copies the table cell by cell; code parses prices, bands, surcharges and notes. What the image says is
never rewritten; the client's answers (16 Nov) are applied in lookup_rate and cited:
  Q06  no earlier card exists: the April 2026 card applies to every order in the package, marked
       "rate card applied retrospectively, per client". Only cards listed in RETROSPECTIVE_AUTHORITY get this;
       a future card is not back-dated automatically.
  Q07  upper weight limit inclusive: 0 < w <= 3, 3 < w <= 10, 10 < w <= 25. Over 25 kg is quoted by hand.
  Q08  every order is standard delivery (same-day is booked by phone, not in the data).
  Q03  pricing zones group the five ops zones: Central; East + North-East; North + West; Sentosa / Jurong Island.
       The ops zone comes from the town in the delivery address (B's lookup); this module maps it to the price row.
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
BOUNDARY_RULE = "upper limit inclusive: min < weight <= max (client Q07)"
RETROSPECTIVE_AUTHORITY = {
    "2026-04-01": "rate card applied retrospectively, per client (Q06, 16 Nov 2026): no earlier card exists and the "
                  "standard prices did not change",
}
STANDARD_ONLY = "standard delivery (client Q08: every order in the data is standard; same-day is not in the data)"
OPS_TO_PRICE_ZONE = {  # client Q03: ops zone -> price row label prefix
    "central": "central", "east": "east", "north-east": "east", "north east": "east", "northeast": "east",
    "north": "north", "west": "north", "sentosa": "sentosa", "jurong island": "sentosa",
}
SURCHARGE_LABEL_RE = re.compile(r"\b(ERP|surcharge|peak|hours?)\b", re.I)
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
    for band in bands:  # printed labels overlap at 3 and 10 kg; the client settled it (Q07)
        band["boundary_rule"] = BOUNDARY_RULE
    rows, surcharges = [], []
    for row in answer.get("rows") or []:
        label, cells = (row.get("label") or "").strip(), row.get("cells") or []
        prices = [_price(c) for c in cells]
        head = [p for p in prices[: len(bands)] if p]
        signed = bool(head) and all(p["is_surcharge"] for p in head)
        by_label = bool(SURCHARGE_LABEL_RE.search(label))
        if head and (signed or by_label):  # a surcharge row, e.g. "CBD ERP hours (0730-1900)" printed as "+$1.50"
            if by_label and not signed:  # seen 16 Nov: the model dropped the "+" on this row
                issues.append({"code": "SURCHARGE_SIGN_MISSING",
                               "message": f"row {label!r} read without '+'; treated as a surcharge by its label"})
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


def _envelope(status: str, data: Any = None, sources: Optional[List[str]] = None, **extra: Any) -> Dict[str, Any]:
    return {"ok": True, "status": status, "data": data, "sources": sources or [], "error": None, **extra}


def price_zone_for(zone: str, rows: List[Dict[str, Any]]) -> Optional[str]:
    """Accept a price-row label ("East / North-East") or an ops zone ("North-East", client Q03)."""
    wanted = (zone or "").strip().lower()
    labels = sorted({r["zone"] for r in rows})
    for label in labels:
        if label.lower() == wanted:
            return label
    prefix = OPS_TO_PRICE_ZONE.get(wanted)
    return next((label for label in labels if prefix and label.lower().startswith(prefix)), None)


def lookup_rate(cards: List[Dict[str, Any]], *, zone: str, weight_kg: float, on_date: str) -> Dict[str, Any]:
    """Standard price for one parcel, cited to the card cell. Applies client answers Q03, Q06, Q07, Q08."""
    day = datetime.fromisoformat(on_date).date()
    dated = [c for c in cards if c.get("effective_from")]
    usable = [c for c in dated if date.fromisoformat(c["effective_from"]) <= day
              and (not c.get("effective_to") or day <= date.fromisoformat(c["effective_to"]))]
    notes: List[str] = [STANDARD_ONLY]
    if usable:
        card = max(usable, key=lambda c: c["effective_from"])
    else:
        allowed = [c for c in dated if c["effective_from"] in RETROSPECTIVE_AUTHORITY]
        if not allowed:
            earliest = min((c["effective_from"] for c in dated), default=None)
            return _envelope("not_found", reason=f"no rate card on file for {day.isoformat()} "
                                                 f"(earliest card starts {earliest}; no client authority to back-date it)")
        card = min(allowed, key=lambda c: c["effective_from"])
        notes.append(RETROSPECTIVE_AUTHORITY[card["effective_from"]])
    if weight_kg is None or weight_kg <= 0:
        return _envelope("not_found", reason=f"invalid parcel weight {weight_kg!r}")
    top = max((r["max_kg"] for r in card["rows"]), default=0)
    if weight_kg > top:
        return _envelope("not_found", reason=f"{weight_kg} kg is over {top:g} kg: quoted by hand, not on the card (client Q07)")
    label = price_zone_for(zone, card["rows"])
    if label is None:
        return _envelope("not_found", reason=f"zone {zone!r} is not a pricing zone or ops zone on card {card['source_id']}")
    hits = [r for r in card["rows"] if r["zone"] == label and r["min_kg"] < weight_kg <= r["max_kg"]]
    if not hits:
        return _envelope("not_found", reason=f"no {label} price for {weight_kg} kg on card {card['source_id']}")
    data = [{"price": r["price"], "currency": card.get("currency", "SGD"), "gst_included": False, "band": r["band"],
             "price_zone": label, "zone_input": zone, "boundary_rule": BOUNDARY_RULE,
             "applied_retrospectively": not usable, "notes": notes,
             "citation": {"source_id": card["source_id"], "type": "image", "ref": card["image_ref"],
                          "locator": r["locator"], "record_key": None}} for r in hits]
    if len(hits) > 1:  # only if a future card has overlapping bands with no client rule
        return _envelope("ambiguous", data, [card["source_id"]], reason="weight matches more than one band")
    return _envelope("found", data[0], [card["source_id"]])