"""Run Developer A's eval cases (task 8) against the local outputs.  From the repo root:

    python -m backend.unstructured.evals                      # uses evals/developer_a_cases.json
    python -m backend.unstructured.evals --out output/unstructured

PASS / FAIL / PENDING per case. PENDING means the output a case needs is not built yet (e.g. pod_records.jsonl
before the paid image run). Exit code 1 if any case FAILs. Prints ids and verdicts only, no record contents.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import pod, ratecard, search

DEFAULT_CASES = Path("evals") / "developer_a_cases.json"
DEFAULT_OUT = Path("output") / "unstructured"
_MISSING = object()


def _get(obj: Any, path: str) -> Any:
    for part in path.split("."):
        if isinstance(obj, list) and part.isdigit():
            obj = obj[int(part)] if int(part) < len(obj) else _MISSING
        elif isinstance(obj, dict):
            obj = obj.get(part, _MISSING)
        else:
            return _MISSING
        if obj is _MISSING:
            return _MISSING
    return obj


def _check(value: Any, rule: Dict[str, Any]) -> bool:
    if value is _MISSING:
        return False
    if "equals" in rule:
        return value == rule["equals"]
    if "contains" in rule:
        return isinstance(value, (list, str)) and rule["contains"] in value
    if "startswith" in rule:
        return isinstance(value, str) and value.startswith(rule["startswith"])
    if "length" in rule:
        return hasattr(value, "__len__") and len(value) == rule["length"]
    raise ValueError(f"unknown rule {rule}")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _by_id(rows: List[Dict[str, Any]], source_id: str) -> Any:
    return next((r for r in rows if r.get("source_id") == source_id), _MISSING)


def _run_call(call: str, args: Dict[str, Any], out: Path) -> Any:
    if call == "search_emails":
        return search.search_emails(out_dir=out, **args)
    if call == "search_policy":
        return search.search_policy(out_dir=out, **args)
    if call == "email_record":
        return _by_id(_load_jsonl(out / "emails.jsonl"), args["source_id"])
    if call == "pod_record":
        return _by_id(_load_jsonl(out / "pod_records.jsonl"), args["source_id"])
    if call == "find_pod":
        return pod.find_pod(_load_jsonl(out / "pod_records.jsonl"), args["source_system"], args["order_id"])
    if call == "lookup_rate":
        return ratecard.lookup_rate(_load_jsonl(out / "rate_cards.jsonl"), **args)
    if call == "ingest_manifest":
        return json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if call == "image_manifest":
        return json.loads((out / "image_manifest.json").read_text(encoding="utf-8"))
    raise ValueError(f"unknown call {call}")


def run_cases(cases_path: Path, out: Path) -> List[Dict[str, Any]]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    results = []
    for case in cases:
        if not (out / case["needs"]).is_file():
            results.append({"id": case["id"], "verdict": "PENDING", "why": f"{case['needs']} not built yet"})
            continue
        try:
            value = _run_call(case["call"], case.get("args", {}), out)
            failed = [r["path"] for r in case["expect"] if not _check(_get(value, r["path"]), r)]
        except Exception as exc:  # a crashing case is a failing case, not a crashed runner
            failed = [f"error: {type(exc).__name__}: {exc}"]
        results.append({"id": case["id"], "verdict": "FAIL" if failed else "PASS",
                        "why": ("failed: " + ", ".join(failed)) if failed else ""})
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run Developer A eval cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    results = run_cases(args.cases, args.out)
    for r in results:
        print(f"{r['id']}  {r['verdict']:<7} {r['why']}")
    totals = {v: sum(1 for r in results if r["verdict"] == v) for v in ("PASS", "FAIL", "PENDING")}
    print(f"\n{totals['PASS']} pass · {totals['FAIL']} fail · {totals['PENDING']} pending · {len(results)} cases")
    return 1 if totals["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
