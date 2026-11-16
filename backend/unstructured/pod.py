"""Proof-of-delivery (POD) card extraction (Developer A, task 5).

The class vision model COPIES what is printed; code then normalises, scores confidence and validates against the
SQL reference. Record shape: docs/02-Design/contracts.md section 2. Traps: T-A05, T-A08..T-A14.

Confidence is decided by code, not by the model:
  high   = value matches the expected format exactly as printed
  medium = matches only after fixing look-alike characters (I/l/| -> 1, O/o -> 0), flagged (T-A13)
  low    = missing, unreadable or wrong format; value left null, never guessed
A signature means "card signed", not proof of who received it (T-A09). Records are unmasked (B/C/D mask).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .sqlref import Reference

PROMPT_VERSION = "pod-v1"
PROMPT = """You are reading a scanned Merlion Express proof-of-delivery card.
Copy every value EXACTLY as printed or handwritten. Do not correct spelling, do not convert formats,
do not guess. If a value is missing, blank or unreadable, use null and add its key to "unreadable".
Return one JSON object with these keys:
  "order_ref": text after "Order Ref:",
  "date_time": text after "Date/Time:",
  "driver": text after "Driver:",
  "delivered_to": the full address under "Delivered to:",
  "received_by": text after "Received by",
  "remarks": text after "Remarks:",
  "signature_present": true if any signature mark is drawn, false if the signature area is empty,
  "footer": the small line of text at the bottom of the card,
  "unreadable": list of keys you could not read with certainty,
  "notes": anything unusual about the card (stains covering text, crossed-out text), else null."""

ROLE_WORDS = ("mum", "mom", "mother", "dad", "father", "neighbour", "neighbor", "front desk", "reception",
              "security", "guard", "concierge", "helper", "maid", "colleague", "wife", "husband", "son",
              "daughter", "sister", "brother", "family", "tenant", "office")
LOOKALIKE_DIGITS = str.maketrans({"I": "1", "l": "1", "|": "1", "O": "0", "o": "0"})
ORDER_REF_RE = re.compile(r"^\s*V([12])-(\d{5})\s*$", re.I)
DATE_TIME_RE = re.compile(r"^\s*(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})\s*$")
DRIVER_RE = re.compile(r"^\s*(DRV\d{3})\s*$")
POSTAL_RE = re.compile(r"(?<!\d)(\d{6})(?!\d)")
BLOCK_RE = re.compile(r"\bBlk\s*(\d{1,4}[A-Z]?)\b", re.I)
COD_RE = re.compile(r"\bCOD\b[^$\d]*\$\s?(\d+(?:\.\d{1,2})?)", re.I)
LEFT_OUTSIDE_RE = re.compile(r"\bleft\b.*\b(outside|door|gate|riser)\b", re.I)


def _field(value: Any, confidence: str, **extra: Any) -> Dict[str, Any]:
    return {"value": value, "confidence": confidence, **extra}


def _parse_with_lookalikes(raw: Optional[str], pattern: "re.Pattern[str]") -> Tuple[Optional["re.Match[str]"], str]:
    """Return (match, confidence). Tries the raw text first, then a look-alike digit repair."""
    if not raw:
        return None, "low"
    m = pattern.match(raw)
    if m:
        return m, "high"
    m = pattern.match(raw.translate(LOOKALIKE_DIGITS))
    return (m, "medium") if m else (None, "low")


def receiver_kind(text: Optional[str]) -> Tuple[str, Optional[str]]:
    if not text or not text.strip() or text.strip() in {"-", "—", "N/A"}:
        return "blank", None
    lowered = text.lower()
    for word in ROLE_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            return "role", word
    return "name", None


def _template(footer: Optional[str]) -> str:
    footer = (footer or "").lower()
    if "hotline" in footer:
        return "hotline_footer"
    if "thank you" in footer:
        return "thankyou_footer"
    return "unknown"


def normalise(answer: Dict[str, Any], file_system: str, file_order_id: int) -> Dict[str, Any]:
    """Turn the model's raw answer into contract fields + flags. No SQL involved here."""
    unreadable = set(answer.get("unreadable") or [])
    flags: List[str] = []
    fields: Dict[str, Any] = {}

    m, conf = _parse_with_lookalikes(answer.get("order_ref"), ORDER_REF_RE)
    system, order_id = (f"v{m.group(1)}", int(m.group(2))) if m else (None, None)
    fields["order_ref"] = _field(f"V{m.group(1)}-{m.group(2)}" if m else None, conf, raw=answer.get("order_ref"))
    if m and (system, order_id) != (file_system, file_order_id):
        flags.append("order_ref_differs_from_file_name")

    m, conf = _parse_with_lookalikes(answer.get("date_time"), DATE_TIME_RE)
    value = None
    if m:
        dd, mm, yyyy, hh, mi = (int(g) for g in m.groups())
        try:  # day-first, as printed on the cards (T-A12)
            value = datetime(yyyy, mm, dd, hh, mi).strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            conf = "low"
    fields["delivered_at"] = _field(value, conf if value else "low", raw=answer.get("date_time"),
                                    tz="Asia/Singapore (assumed)")

    m, conf = _parse_with_lookalikes(answer.get("driver"), DRIVER_RE)
    fields["driver_code"] = _field(m.group(1) if m else None, conf, raw=answer.get("driver"))

    address = answer.get("delivered_to")
    postal = POSTAL_RE.findall(address or "")
    block = BLOCK_RE.search(address or "")
    fields["delivered_to"] = _field(address, "high" if address and "delivered_to" not in unreadable else "low")
    fields["postal_code"] = _field(postal[-1] if postal else None, "high" if postal else "low")
    fields["block"] = _field(block.group(1) if block else None, "high" if block else "low")

    received = answer.get("received_by")
    kind, role = receiver_kind(received)
    fields["received_by"] = _field(received, "low" if "received_by" in unreadable else "high", kind=kind, role=role)

    signed = answer.get("signature_present")
    # "absent" is never trusted on the model's word: SQL can't confirm it, and the 16 Nov run missed one short stroke
    sig_conf = "high" if signed is True else ("medium" if signed is False else "low")
    fields["signature"] = _field({True: "present", False: "absent"}.get(signed), sig_conf)
    if signed is False:
        flags.append("signature_absent_verify_by_eye")

    remarks = answer.get("remarks")
    fields["remarks"] = _field(remarks, "low" if "remarks" in unreadable else "high")
    cod = COD_RE.search(remarks or "")
    fields["cod_on_card"] = _field(float(cod.group(1)) if cod else None, "high" if cod else "n/a", currency="SGD")

    if remarks and LEFT_OUTSIDE_RE.search(remarks) and signed is True:
        flags.append("remark_contradicts_signature")
    # Only a ROLE that clashes counts (e.g. remark "neighbour take", receiver "mum"); a name could be the neighbour's.
    if remarks and re.search(r"\bneighbou?r\b", remarks, re.I) and kind == "role" and role not in ("neighbour", "neighbor"):
        flags.append("remark_contradicts_receiver")
    for name, f in fields.items():
        if f["confidence"] == "medium" and name != "signature":
            flags.append(f"lookalike_repaired:{name}")
        elif f["confidence"] == "low" and name not in ("received_by", "remarks", "delivered_to", "block"):
            flags.append(f"low_confidence:{name}")
    for name in sorted(unreadable):
        flags.append(f"model_unreadable:{name}")
    return {"source_system": system or file_system, "order_id": order_id or file_order_id, "fields": fields,
            "template": _template(answer.get("footer")), "flags": sorted(set(flags)), "notes": answer.get("notes")}


def validate(record: Dict[str, Any], ref: Optional[Reference]) -> Dict[str, Any]:
    """Compare against SQL. True/False per field; None when there is nothing to compare."""
    if ref is None:
        return {"matches_sql": None, "reason": "no SQL reference loaded"}
    key = (record["source_system"], record["order_id"])
    order, deliveries = ref.orders.get(key), ref.deliveries.get(key, [])
    f = record["fields"]
    result: Dict[str, Any] = {"order": order is not None}
    if order is None:
        return {"matches_sql": result, "reason": f"no {key[0]} order {key[1]} in SQL"}
    times = {(d["delivered_time"] or "")[:16].replace(" ", "T") for d in deliveries}
    drivers = {d["driver_code"] for d in deliveries}
    result["delivered_at"] = f["delivered_at"]["value"] in times if f["delivered_at"]["value"] else None
    result["driver"] = f["driver_code"]["value"] in drivers if f["driver_code"]["value"] else None
    result["postal_code"] = f["postal_code"]["value"] == order["postal_code"] if f["postal_code"]["value"] else None
    result["block"] = (f["block"]["value"] or "").upper() == (order["block"] or "").upper() if f["block"]["value"] else None
    card_cod, sql_cod = f["cod_on_card"]["value"], order["cod_amount"]
    cod = {"card": card_cod, "sql": sql_cod}
    if card_cod is not None and sql_cod is not None and abs(card_cod - sql_cod) > 0.005:
        cod["conflict"] = True
    elif card_cod is None and sql_cod:
        cod["conflict"] = "sql_cod_not_on_card"
    return {"matches_sql": result, "cod": cod}


def build_record(answer: Optional[Dict[str, Any]], *, source_id: str, image_ref: str, image_sha256: str,
                 file_system: str, file_order_id: int, ref: Optional[Reference], extraction: Dict[str, Any]
                 ) -> Dict[str, Any]:
    record: Dict[str, Any] = {"source_id": source_id, "type": "image", "image_ref": image_ref,
                              "image_sha256": image_sha256, "source_system": file_system, "order_id": file_order_id,
                              "fields": {}, "template": None, "flags": [], "validation": None,
                              "extraction": extraction, "status": "failed"}
    if answer is None:  # model call failed: still emit the record so the failure is visible
        return record
    record.update(normalise(answer, file_system, file_order_id))
    record["validation"] = validate(record, ref)
    key_fields = ("order_ref", "delivered_at", "driver_code", "postal_code")
    low = [k for k in key_fields if record["fields"][k]["confidence"] == "low"]
    mismatches = [k for k, v in ((record["validation"] or {}).get("matches_sql") or {}).items() if v is False]
    for k in mismatches:
        record["flags"].append(f"sql_mismatch:{k}")
    if (record["validation"].get("cod") or {}).get("conflict"):
        record["flags"].append("cod_conflict_with_sql")  # T-A08: show both, never pick one silently
    record["flags"] = sorted(set(record["flags"]))
    record["status"] = "failed" if len(low) == len(key_fields) else ("partial" if low or mismatches else "ok")
    return record


def find_pod(records: List[Dict[str, Any]], source_system: str, order_id: int) -> Dict[str, Any]:
    """Look up an extracted POD record. A v2 order never gets a v1 card (T-A05)."""
    hits = [r for r in records if r["source_system"] == source_system.lower() and r["order_id"] == int(order_id)]
    if not hits:
        return {"ok": True, "status": "not_found", "data": None, "sources": [], "error": None,
                "reason": f"no POD scan on file for {source_system.lower()} order {order_id}"}
    r = hits[0]
    return {"ok": True, "status": "found" if r["status"] == "ok" else "partial", "data": r, "sources": [r["source_id"]],
            "error": None}
