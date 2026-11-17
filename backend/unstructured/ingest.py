"""Run A's text ingestion: complaint emails + policy/guide.  From the repo root:

    python -m backend.unstructured.ingest            # reads data/, writes output/unstructured/
    python -m backend.unstructured.ingest --data data --out output/unstructured

Writes (all under output/, which git ignores — never commit them; they hold UNMASKED personal data):
    emails.jsonl          one record per email, unmasked (contracts.md section 4)
    policy_chunks.jsonl   one chunk per guide section/row (empty until the guide arrives)
    manifest.json         one outcome per input file: sha256, parser version, status, issues
Prints a summary with no personal data. Exit code 1 only if the email folder is missing or any email failed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import emails, policy
from .paths import default_data_dir

EMAIL_SUBDIR = Path("docs") / "complaint_emails"


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(data_dir: Path, out_dir: Path) -> Dict[str, Any]:
    email_dir = data_dir / EMAIL_SUBDIR
    if not email_dir.is_dir():
        raise FileNotFoundError(f"email folder not found: {email_dir}")
    records, email_entries = emails.parse_email_dir(email_dir, data_dir)
    chunks, policy_entries = policy.ingest_policy(data_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out_dir / "emails.jsonl", records)
    _write_jsonl(out_dir / "policy_chunks.jsonl", chunks)
    for entry in email_entries:
        entry["output"] = "emails.jsonl"
    for entry in policy_entries:
        entry["output"] = "policy_chunks.jsonl" if entry["status"] != "failed" else None

    summary = {
        "emails": {
            "files": len(records),
            "status": dict(Counter(r["status"] for r in records)),
            "category": dict(Counter(r["category"] for r in records)),
            "with_order_number": sum(1 for r in records if r["order_numbers"]),
            "with_system_prefix": sum(1 for r in records if r["system_hint"]),
            "corporate": sum(1 for r in records if r["corporate_account"]),
            "pii_detected": dict(sum((Counter(r["pii_detected"]) for r in records), Counter())),
            "issues": dict(Counter(i["code"] for r in records for i in r["issues"])),
        },
        "policy": {
            "files": sum(1 for e in policy_entries if e["ref"]),
            "chunks": len(chunks),
            "status": dict(Counter(e["status"] for e in policy_entries)),
            "issues": dict(Counter(i["code"] for e in policy_entries for i in e["issues"])),
        },
    }
    manifest = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parsers": {"emails": emails.PARSER_VERSION, "policy": policy.PARSER_VERSION},
        "summary": summary,
        "files": email_entries + policy_entries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest complaint emails and the policy/guide (Developer A).")
    parser.add_argument("--data", type=Path, default=None,
                        help="package folder (default: data/team2_merlion_express_package if present, else data)")
    parser.add_argument("--out", type=Path, default=Path("output") / "unstructured",
                        help="output folder, git-ignored (default: output/unstructured)")
    args = parser.parse_args(argv)
    args.data = args.data or default_data_dir()
    try:
        manifest = run(args.data, args.out)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest["summary"], indent=2))
    print(f"Wrote {args.out / 'emails.jsonl'}, {args.out / 'policy_chunks.jsonl'}, {args.out / 'manifest.json'}")
    return 1 if manifest["summary"]["emails"]["status"].get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
