"""Build A's vector index (SQLite + FAISS) from the ingest outputs.  From the repo root, after ingest:

    python -m backend.unstructured.build_index

Embeds only new or changed chunks (cache in SQLite), so a rebuild is usually free. Uses the TEAM key and
A_EMBED_MODEL (default text-embedding-3-small). Masked text only is sent. Appends the run to spend_log.jsonl.
Exit code: 0 ok · 2 setup problem (no faiss, no key, no ingest output, endpoint error).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional

from . import vector_index
from .extract_images import record_spend


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build A's SQLite + FAISS vector index.")
    parser.add_argument("--out", type=Path, default=Path("output") / "unstructured")
    args = parser.parse_args(argv)
    embedder, model = vector_index.make_embedder(args.out, tool="embed_index")
    try:
        summary = vector_index.build(args.out, model=model, embedder=embedder)
    except vector_index.VectorUnavailable as exc:
        print(f"ERROR {exc.code}: {exc}", file=sys.stderr)
        return 2
    counts = Counter(paid_call=1 if summary["embedded_now"] else 0, prompt_tokens=summary["prompt_tokens"],
                     cache_hit=summary["reused_from_cache"])
    summary["spend"] = record_spend(args.out, model, counts, tool="build_index")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
