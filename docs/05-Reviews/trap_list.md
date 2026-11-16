# Data traps and unresolved assumptions

**Updated:** 16 Nov 2026. Aggregate evidence: [data audit](data_audit.md). Findings below are observed or explicitly unresolved; no source record contents are committed.

| ID | Evidence / status | Required handling and regression expectation | Owner |
|---|---|---|---|
| T01 | 11,499 order IDs repeat across v1/v2; composite keys unique | Join by system and order; ambiguous input asks for clarification, never chooses a system blindly | B/C |
| T02 | Raw orders declares no primary key | Enforce validated composite key in cleaned schema; reruns do not duplicate orders | B |
| T03 | CS case log and Resolution Guide absent locally; Q01/Q02 unsent | Missing-source response; no invented policy or authoritative complaint totals | A/B/C |
| T04 | 17,195 orders precede the only supplied rate card | Date-sensitive selection; abstain when no applicable rate is available | A/B/C |
| T05 | 1,031 orders lack a delivery record | Distinguish absent record, failed attempt and failed query | B/C |
| T06 | All supplied POD filenames identify v1 | Use system-aware image linkage; missing scan does not prove non-delivery | A/B/C |
| T07 | Six duplicate driver-name groups | Identify by IDs/codes; weekly counts do not merge namesakes | B |
| T08 | GPS epoch versus timezone-free delivery timestamps; offset unproven | Preserve raw values, document timezone evidence and test windows before correction | B |
| T09 | Postal codes all pass six-digit numeric check; brief warning unresolved | Investigate semantic validity; do not pad or change already valid-looking values without evidence | B |
| T10 | No explicit SQL zone/service tier and at most one delivery row per order | Unknown zones and surcharge inputs remain explicit; do not invent attempt counts or reporting rules | B/C |
| T11 | Images decode; OCR accuracy not yet established | Track uncertainty and per-file failures; unreadable fields cannot become asserted facts | A |

Each owner supplies checkable normal/trap cases and fixes their component. E maintains the shared runner; C reviews safety/identity assertions. Do not mark regressions passed until executed.
