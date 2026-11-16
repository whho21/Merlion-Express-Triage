"""Run A's image extraction: POD cards + rate cards (tasks 5-6).  From the repo root:

    python -m backend.unstructured.extract_images --dry-run     # free: counts what WOULD be sent, no API call
    python -m backend.unstructured.extract_images --limit 2     # paid smoke test on 2 POD cards + rate cards
    python -m backend.unstructured.extract_images               # everything not already cached

Uses the TEAM key (team repo .env, see llm.py). Cached answers are reused, so a rerun costs nothing unless an
image, the prompt version or the model changed. Writes to output/unstructured/ (git-ignored, unmasked data):
    pod_records.jsonl, rate_cards.jsonl, image_manifest.json (one outcome per image), telemetry.jsonl, cache/
Exit code: 0 all ok · 1 some images failed/partial · 2 setup problem (no key, no data).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import llm, pod, ratecard
from .cache import ExtractionCache, cache_key
from .sqlref import Reference

POD_DIR = Path("images") / "proof_of_delivery"
RATE_DIR = Path("images") / "rate_cards"
POD_NAME_RE = re.compile(r"^POD_(v[12])_(\d+)$", re.I)
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Extractor:
    """Wraps cache + model call so every image goes through the same path."""

    def __init__(self, out_dir: Path, cfg: Dict[str, Optional[str]], call: Optional[Callable[..., Any]] = None):
        self.cache = ExtractionCache(out_dir / "cache")
        self.telemetry = out_dir / "telemetry.jsonl"
        self.cfg = cfg
        self.call = call or llm.vision_json
        self.counts = Counter()

    def read(self, path: Path, *, prompt: str, prompt_version: str, tool: str, source_id: str):
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        model = self.cfg["model"]
        key = cache_key(sha, prompt_version, model)
        meta = {"method": "vision", "model": model, "prompt_version": prompt_version}
        cached = self.cache.get(key)
        if cached is not None:
            self.counts["cache_hit"] += 1
            llm.log_telemetry(self.telemetry, tool=tool, source_id=source_id, model=model, prompt_version=prompt_version,
                              status="ok", cache="hit", attempts=0, latency_ms=0, prompt_tokens=0, completion_tokens=0)
            return cached["answer"], sha, {**meta, "extracted_at": cached["extracted_at"], "cache": "hit",
                                           "status": "ok", "usage": cached.get("usage")}
        mime = MIME.get(path.suffix.lower())
        if mime is None:
            return None, sha, {**meta, "extracted_at": _now(), "cache": "miss", "status": "failed",
                               "error": {"code": "UNSUPPORTED_FORMAT", "message": path.suffix, "retryable": False}}
        try:
            answer, usage = self.call(raw, mime, prompt, api_key=self.cfg["api_key"], model=model,
                                      base_url=self.cfg["base_url"], tool=tool, source_id=source_id,
                                      prompt_version=prompt_version, telemetry_path=self.telemetry)
        except llm.LLMError as exc:
            self.counts["failed_call"] += 1
            return None, sha, {**meta, "extracted_at": _now(), "cache": "miss", "status": "failed", "error": exc.as_dict()}
        self.counts["paid_call"] += 1
        self.counts["prompt_tokens"] += usage["prompt_tokens"]
        self.counts["completion_tokens"] += usage["completion_tokens"]
        stamp = _now()
        self.cache.put(key, {"answer": answer, "usage": usage, "extracted_at": stamp, "source_id": source_id,
                             "model": model, "prompt_version": prompt_version})
        return answer, sha, {**meta, "extracted_at": stamp, "cache": "miss", "status": "ok", "usage": usage}


def _ref(data_dir: Path, path: Path) -> str:
    return "data/" + path.relative_to(data_dir).as_posix()


def list_images(data_dir: Path, limit: Optional[int]) -> Dict[str, List[Path]]:
    pods = sorted(p for p in (data_dir / POD_DIR).glob("*") if p.is_file())
    rates = sorted(p for p in (data_dir / RATE_DIR).glob("*") if p.is_file())
    return {"pod": pods[:limit] if limit else pods, "ratecard": rates}


def run(data_dir: Path, out_dir: Path, *, limit: Optional[int] = None, only: Optional[str] = None,
        cfg: Optional[Dict[str, Optional[str]]] = None, call: Optional[Callable[..., Any]] = None,
        reference: Optional[Reference] = None) -> Dict[str, Any]:
    images = list_images(data_dir, limit)
    out_dir.mkdir(parents=True, exist_ok=True)
    ex = Extractor(out_dir, cfg or llm.settings(Path.cwd()), call)
    entries: List[Dict[str, Any]] = []
    pods: List[Dict[str, Any]] = []
    cards: List[Dict[str, Any]] = []

    if only in (None, "pod"):
        for path in images["pod"]:
            m = POD_NAME_RE.match(path.stem)
            system, order_id = (m.group(1).lower(), int(m.group(2))) if m else ("unknown", 0)
            source_id = f"pod:{system}:{order_id}" if m else f"pod:unknown:{path.stem}"
            answer, sha, meta = ex.read(path, prompt=pod.PROMPT, prompt_version=pod.PROMPT_VERSION,
                                        tool="pod_extract", source_id=source_id)
            record = pod.build_record(answer, source_id=source_id, image_ref=_ref(data_dir, path), image_sha256=sha,
                                      file_system=system, file_order_id=order_id, ref=reference, extraction=meta)
            if not m:
                record["flags"].append("file_name_not_POD_vN_order")
            pods.append(record)
            entries.append({"source_id": source_id, "kind": "pod", "ref": record["image_ref"], "sha256": sha,
                            "status": record["status"], "flags": record["flags"], "cache": meta["cache"],
                            "error": meta.get("error"), "output": "pod_records.jsonl"})

    if only in (None, "ratecard"):
        for path in images["ratecard"]:
            source_id = f"ratecard:{path.stem}"
            answer, sha, meta = ex.read(path, prompt=ratecard.PROMPT, prompt_version=ratecard.PROMPT_VERSION,
                                        tool="ratecard_extract", source_id=source_id)
            if answer is None:
                card = {"source_id": source_id, "type": "image", "image_ref": _ref(data_dir, path), "image_sha256": sha,
                        "effective_from": None, "rows": [], "status": "failed", "issues": [meta.get("error")],
                        "extraction": meta}
            else:
                card = ratecard.normalise(answer, source_id=source_id, image_ref=_ref(data_dir, path),
                                          image_sha256=sha, extraction=meta)
                if card["effective_from"]:  # contract id: ratecard:<effective_from>
                    card["source_id"] = f"ratecard:{card['effective_from']}"
            cards.append(card)
            entries.append({"source_id": card["source_id"], "kind": "ratecard", "ref": card["image_ref"], "sha256": sha,
                            "status": card["status"], "issues": card.get("issues"), "cache": meta["cache"],
                            "error": meta.get("error"), "output": "rate_cards.jsonl"})

    for kind, name, rows in (("pod", "pod_records.jsonl", pods), ("ratecard", "rate_cards.jsonl", cards)):
        if only in (None, kind):  # --only keeps the other file from an earlier run
            with (out_dir / name).open("w", encoding="utf-8", newline="\n") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    validated = [r for r in pods if isinstance((r.get("validation") or {}).get("matches_sql"), dict)]
    summary = {
        "pod": {"images": len(pods), "status": dict(Counter(r["status"] for r in pods)),
                "all_key_fields_match_sql": sum(1 for r in validated if all(
                    r["validation"]["matches_sql"].get(k) for k in ("order", "delivered_at", "driver", "postal_code"))),
                "flags": dict(Counter(f.split(":")[0] for r in pods for f in r["flags"]))},
        "ratecard": {"images": len(cards), "status": dict(Counter(c["status"] for c in cards)),
                     "effective_from": [c.get("effective_from") for c in cards]},
        "calls": dict(ex.counts),
        "model": ex.cfg["model"],
        "spend": record_spend(out_dir, ex.cfg["model"], ex.counts),
    }
    manifest = {"run_at": _now(), "prompts": {"pod": pod.PROMPT_VERSION, "ratecard": ratecard.PROMPT_VERSION},
                "summary": summary, "files": entries}
    (out_dir / "image_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")
    return manifest


def record_spend(out_dir: Path, model: str, counts: Counter) -> Dict[str, Any]:
    """Append this run to spend_log.jsonl and return this run's and the running total cost (estimates)."""
    run_cost = llm.estimate_cost(model, counts["prompt_tokens"], counts["completion_tokens"])
    entry = {"run_at": _now(), "tool": "extract_images", "model": model, "paid_calls": counts["paid_call"],
             "failed_calls": counts["failed_call"], "cache_hits": counts["cache_hit"],
             "prompt_tokens": counts["prompt_tokens"], "completion_tokens": counts["completion_tokens"],
             "est_cost_usd": run_cost}
    log = out_dir / "spend_log.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    total = round(sum(r.get("est_cost_usd") or 0 for r in rows), 6)
    return {"this_run_usd": run_cost, "a_total_usd": total, "team_budget_usd": llm.TEAM_BUDGET_USD,
            "budget_used_pct": round(100 * total / llm.TEAM_BUDGET_USD, 3)}


def dry_run(data_dir: Path, out_dir: Path, limit: Optional[int], only: Optional[str], cfg: Dict[str, Optional[str]]) -> Dict[str, Any]:
    images = list_images(data_dir, limit)
    cache = ExtractionCache(out_dir / "cache")
    plan = Counter()
    for kind, version in (("pod", pod.PROMPT_VERSION), ("ratecard", ratecard.PROMPT_VERSION)):
        if only not in (None, kind):
            continue
        for path in images[kind]:
            key = cache_key(hashlib.sha256(path.read_bytes()).hexdigest(), version, cfg["model"])
            plan[f"{kind}_{'cached' if cache.get(key) is not None else 'to_send'}"] += 1
    return {"dry_run": True, "model": cfg["model"], "team_key_found": bool(cfg["api_key"]), **plan}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract POD cards and rate cards with the class vision model.")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("output") / "unstructured")
    parser.add_argument("--limit", type=int, default=None, help="only the first N POD cards (smoke test)")
    parser.add_argument("--only", choices=["pod", "ratecard"], default=None)
    parser.add_argument("--sql", type=Path, default=None, help="SQL dump for validation (default data/sql/merlion_ops.sql)")
    parser.add_argument("--dry-run", action="store_true", help="count what would be sent; no API call, no cost")
    args = parser.parse_args(argv)

    if not (args.data / POD_DIR).is_dir() and not (args.data / RATE_DIR).is_dir():
        print(f"ERROR: no images under {args.data}", file=sys.stderr)
        return 2
    cfg = llm.settings(Path.cwd())
    if args.dry_run:
        print(json.dumps(dry_run(args.data, args.out, args.limit, args.only, cfg), indent=2))
        return 0
    if not cfg["api_key"]:
        print("ERROR: no OPENAI_API_KEY in the environment or in this repo's .env (the TEAM key, not the class key).",
              file=sys.stderr)
        return 2
    sql_path = args.sql or args.data / "sql" / "merlion_ops.sql"
    reference = Reference.from_sql(sql_path) if sql_path.is_file() else None
    manifest = run(args.data, args.out, limit=args.limit, only=args.only, cfg=cfg, reference=reference)
    print(json.dumps(manifest["summary"], indent=2))
    statuses = Counter(e["status"] for e in manifest["files"])
    return 0 if set(statuses) <= {"ok"} else 1


if __name__ == "__main__":
    sys.exit(main())
