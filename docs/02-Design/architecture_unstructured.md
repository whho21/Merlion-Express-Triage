# Release 1 client demo architecture

![Hybrid SQL, JSONL and RAG architecture for the client demo](merlion-express-technical-architecture-codex-20261117-114201.drawio.svg)

[Open editable SVG](merlion-express-technical-architecture-codex-20261117-114201.drawio.svg) · [Edit in draw.io](merlion-express-technical-architecture-codex-20261117-114201.drawio)

MySQL holds operational facts, canonical complaints and weekly views; Ralph's evidence stays in JSONL files. Email/guide chunks feed semantic retrieval, while SQL and code resolve identities, calculate charges and enforce policy.

This is the intended release design. Dashed components are pending implementation; React screens currently use mocks. The footer records [client clarifications](../00-Biz_Requirements/client_qa_v02.xlsx) and demo acceptance checks.

<details>
<summary>Ralph's original unstructured design and Mermaid source</summary>

# Architecture

- Cleaned-schema ER diagram and architecture proposal
- Architecture plus Mermaid data flow, cleaned ER and complaint sequence
- C compiles; A/B/D supply their areas

---

## A — Unstructured sources: data flow (Ralph, 17 Nov 2026)

How emails, POD scans, the rate card and the Resolution Guide become cited evidence. Code: `backend/unstructured/`
(standard library only). Record shapes and tool envelopes: `contracts_2026-11-16.md` §1–§6.

```mermaid
flowchart LR
  subgraph SRC["Client package - data/, git-ignored"]
    E["90 complaint emails<br/>docs/complaint_emails/*.txt"]
    P["80 POD scans<br/>images/proof_of_delivery/*.jpg"]
    R["1 rate card<br/>images/rate_cards/*.jpg"]
    G["Resolution Guide tab<br/>tabular/CS_case_log_Oct25-Jun26.xlsx"]
    S[("SQL dump<br/>sql/merlion_ops.sql")]
  end

  subgraph OFF["Offline - run once, cached in output/unstructured/, git-ignored"]
    I1["ingest<br/>emails + guide parsers<br/>regex, no LLM, US$0"]
    I2["extract_images<br/>class vision model, team key<br/>cache key: image hash + prompt + model"]
    V["validate each card vs SQL<br/>read-only, order + time + driver + postal"]
    EJ[("emails.jsonl")]
    PJ[("policy_chunks.jsonl")]
    PR[("pod_records.jsonl")]
    RJ[("rate_cards.jsonl")]
    M[("manifests, telemetry,<br/>spend_log")]
  end

  subgraph ON["At question time - every result carries status + citation"]
    T1["search_emails<br/>query, order_number"]
    T2["search_policy<br/>query, category"]
    T3["find_pod<br/>system, order_id"]
    T4["lookup_rate<br/>zone, weight, date"]
  end

  B["B: MySQL + order lookup<br/>get_pod, get_rate"]
  C["C: agent + guardrails<br/>masks PII, checks citations"]
  U["CS user<br/>cited answer"]

  E --> I1
  G --> I1
  I1 --> EJ
  I1 --> PJ
  P --> I2
  R --> I2
  S --> V
  I2 --> V
  V --> PR
  I2 --> RJ
  I1 --> M
  I2 --> M
  EJ --> T1
  PJ --> T2
  PR --> T3
  RJ --> T4
  T3 --> B
  T4 --> B
  T1 --> C
  T2 --> C
  B --> C
  C --> U
```

| Stage | What happens | Cost | Rerun |
|---|---|---|---|
| ingest | Emails parsed into 7 categories with order numbers and exact `body:char` locators; guide tab parsed into 9 rules + 3 notes cited `sheet:Resolution Guide\|row:n` | US$0 | `python -m backend.unstructured.ingest` |
| extract_images | Vision model copies each card; code sets confidence, fixes look-alikes (flagged), validates against SQL | US$0.32 once (81 images) | `python -m backend.unstructured.extract_images` — cached, so free unless an image, prompt or model changes |
| tools | Read the cached files when C asks; never call the model | US$0 | — |

Where the client's answers (16 Nov) apply: guide v2 applies to every case (Q02) → `search_policy`; no POD after 1 Feb
(Q04) → `find_pod`; April card for all orders (Q06), upper weight limit inclusive (Q07), standard delivery only (Q08),
ops zone → price row (Q03) → `lookup_rate`. Records are unmasked by team decision; C masks before the model or a
customer sees anything.

</details>
