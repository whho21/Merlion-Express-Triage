"""Try A's search by hand.  From the repo root:

    python -m backend.unstructured.ask                 # interactive: type a question, Enter; 'q' to quit
    python -m backend.unstructured.ask "parcel came 3 days late, refund?"

Shows the best-matching Resolution Guide rule and complaint emails, each with its source. Reads the cached
outputs in output/unstructured/ (run ingest first). No LLM call, no cost. Output is unmasked: local use only.
"""
from __future__ import annotations

import sys
from typing import Optional

from . import search


LABELS = {"late": "Late delivery", "cod_wrong": "COD amount wrong", "wrong_address": "Wrong address",
          "missing_item": "Item missing", "where_is_parcel": "Where is my parcel", "compliment": "Compliment",
          "thrown_over_gate": "Thrown over gate"}


def _short_source(ref: str, locator: str) -> str:
    name = ref.rsplit("/", 1)[-1]
    if locator.startswith("sheet:"):
        return f"{name}, {locator.split('|')[0][6:]} tab, row {locator.rsplit(':', 1)[-1]}"
    return name


def ask(question: str, order_number: Optional[str] = None) -> None:
    print("\n" + "=" * 72)
    print(f"Question: {question}")
    print("=" * 72)
    pol = search.search_policy(question, top_k=2)
    if pol["status"] == "found":
        best = pol["data"][0]
        f = best.get("fields") or {}
        print(f"\nCOMPANY RULE: {best['heading']}")
        print(f"  Check first : {f.get('Check first', '-')}")
        print(f"  What to do  : {f.get('Resolution', best['text'])}")
        print(f"  Who approves: {f.get('Limit / approval', '-')}")
        print(f"  Source      : {_short_source(best['citation']['ref'], best['citation']['locator'])}")
        if len(pol["data"]) > 1:
            print(f"  (next best match: {pol['data'][1]['heading']})")
    elif pol["status"] == "failed":
        print(f"\nCOMPANY RULE: not available ({pol['error']['code']})")
    else:
        print("\nCOMPANY RULE: no rule matches this question")

    em = search.search_emails(question, order_number=order_number, top_k=3)
    print(f"\nSearch method: {pol.get('retrieval') or em.get('retrieval')}")
    hits = em["data"] or []
    print(f"\nSIMILAR COMPLAINT EMAILS: {len(hits)} shown" if hits else "\nSIMILAR COMPLAINT EMAILS: none")
    for h in hits:
        date = (h.get("received_at") or "")[:10]
        orders = ", ".join(h["order_numbers"]) or "no order no."
        print(f"  - {date}  {LABELS.get(h['category'], h['category'])}  order {orders}")
        print(f"      \"{h['text'][:110]}{'...' if len(h['text']) > 110 else ''}\"")
        print(f"      file: {_short_source(h['citation']['ref'], h['citation']['locator'])}")


def main(argv) -> int:
    if argv:
        ask(" ".join(argv))
        return 0
    print("Type a question (or an order number) and press Enter. 'q' to quit.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("q", "quit", "exit"):
            break
        if q.isdigit() and len(q) == 5:
            ask(f"order {q}", order_number=q)
        elif q:
            ask(q)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
