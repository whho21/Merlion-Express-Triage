# API catalog — handoff coverage review

**Reviewed:** 17 Nov 2026 (SGT). **Review count:** one manual coverage pass after the draft was written. **Artifact:** [API catalog](../02-Design/api-catalog_v0.9.0.md).

**Later implementation follow-up, 17 Nov:** the original coverage review below predates the complaint/session increment. HTTP-01–03, health and SQLite recovery are now implemented and checked locally; B's production provider, complete assessment/answer orchestration and weekly reporting remain pending. The catalog's implementation status has been updated. See the new [implementation plan](../03-Handoffs/John_2026-11-17-complaint-session-api-plan.md) and [verified consumer handoff](../03-Handoffs/John_2026-11-17-complaint-session-api.md); the original seven-handoff count and pending-implementation paragraphs below describe the earlier review snapshot.

## Result

All seven substantive Markdown handoffs in `03-Handoffs` have their API/design requirements represented in the catalog. The eighth file is an empty handoff template. Older superseded behaviour, historical test/spend claims and non-API delivery tasks are distinguished from current requirements; this is a documentation review, not acceptance of the implementation.

## Coverage by handoff

| Handoff | Catalog coverage | Disposition |
|---|---|---|
| [Client demo architecture](../03-Handoffs/Codex_2026-11-17-client-demo-architecture.md) | §§1–2, 4–7: hybrid SQL/JSONL release scope, three case tables/two views, raw lineage, published source versions, optional embeddings, six routes, SQLite recovery, masking, deterministic rules, recommendation boundary, telemetry and capstone checks. | Covered. Uses the renamed `architecture_v1` diagram paths. Existing handoff export/visual checks are historical evidence, not API implementation claims. |
| [Frontend mock UI](../03-Handoffs/Jeffrey_2026-11-17-frontend-mock-ui.md) | §§2–3, 7–8: three screens; triage/loading/error/retry, candidates, delivery/POD/GPS/rate cards, conflicts, approval, refusal, absence, citations, follow-up/recovery; complete weekly fields/charts/filter definitions and table equivalents. Draft routes, reporting semantics, null metrics, source visibility and real session checks remain explicit. | Covered. Mock scenarios/component/journey evals remain inputs to integrated checks. Lint/build and live verification remain pending. Router/form/test-library choices, visual palette, screenshots and pitch work do not add HTTP endpoints or change payload contracts. |
| [API/mock profiles and retry fixes](../03-Handoffs/John_2026-11-17-Jeffrey-api-mock-profiles.md) | §§2.4, 3.2, 7–8: all four API states in demo/live; per-feature readiness/source tags; failure isolation/stale data; same-origin empty base; four Vite scripts/mode files/string parsing/rebuild; 200+failed error flow with retryability; correct weeks-list and selected-week retries; empty weeks; unknown calculations; retained file tools; actual server recovery. | All eight numbered handoff points covered. Lint/two-profile builds and mixed-availability/retry checks are release work. Existing PR update/peer-review instructions are delivery workflow, not additional API operations. |
| [PR #11 findings](../03-Handoffs/John_2026-11-17-Ralph-pr11-review.md) | §§3.3, 4.1, 5–7: category lookup survives unrelated lexical queries; expired-card guard; dataset-based POD absence with later matching records accepted; explicit failures and source roots; regression/new-batch checks; no SQL evidence migration or paid rerun needed. | Covered as target behaviour and known unresolved fixes, not already-fixed code. Historical 70-test/9-pass/9-pending evidence is not promoted into a catalog or integrated pass. |
| [Extraction tools and evidence limits](../03-Handoffs/Ralph_2026-11-16-A-tools-evidence-limits.md) | §§3–6: existing functions/files, exact locators, composite identity, dates excluding later orders, cross-system POD prohibition, claim-versus-record and COD conflicts, uncertainty/filename identity, signature-not-identity/by-eye absence check, lexical limits, bounded extraction/cache/dry-run, safe telemetry, private unmasked outputs and API-boundary masking. | Covered. Missing guide, pre-April rejection and ambiguous 3/10 kg examples are superseded by the 17 Nov client clarifications; the current hybrid design defers SQL evidence loading. Reported extraction counts/prices/spend and synthetic test results remain source evidence, not new guarantees. |
| [Email parser](../03-Handoffs/Ralph_2026-11-16-email-parser.md) | §§1, 3.3, 4.1–6: unmasked source records; names not caught by regex; exact body offsets, received dates, order refs and system hints; source failure versus no rule; native guide support; source-root discovery; masking before embedding/answer exposure. | Covered. Early “not started”/unsupported-XLSX/missing-policy statements are superseded by later code/handoff. Existing historical parser counts and test evidence need not become API fields. |
| [Guide and client answers](../03-Handoffs/Ralph_2026-11-17-guide-and-client-answers.md) | §§3.3, 4.1–7: nine rules/three notes, category fields/guide authority, retrospective April card, inclusive 3/10/25 kg bands, standard delivery and zone mapping, missing-POD honesty, package/guide paths, category/no-rule distinction, lexical baseline and measured semantic promotion, candidate/contact-date evidence, CBD/holiday/calendar work and component eval consolidation. | Covered. Preserve the lexical tools; embeddings remain capability/evaluation-dependent. Reported 18/18 component results are distinct from pending independent image verification and integration checks. |
| [Handoff template](../03-Handoffs/Name_YYYY-MM-DD-topic.md) | No substantive content. | Not applicable; template only. |

## Corrections made during this pass

- Made the exact demo/live profile settings and rebuild requirement explicit, rather than listing only the script names.
- Explicitly required private handling of unmasked outputs and synthetic-only committed fixtures; kept telemetry free of prompt/query/image/answer text.
- Cross-checked the citation UI: it currently formats every record key as an order pair, while email/other tools can return source-specific keys. The catalog now records the required renderer support and verification case.

## Pending agreements and implementation

Catalog §8 lists contract freeze, validation/deadline/idempotency limits, reporting/gap/null definitions, session retention/isolation/concurrency, per-feature readiness, original-evidence viewing and semantic-retrieval capability/failure policy. New health fields, HTTP error mappings and proposed Python signatures are identified as proposals. These are recorded decisions/work items, not omitted requirements or implemented capabilities.

Known category-search, rate-expiry and POD messaging/failure issues remain implementation work. The six HTTP routes, live SQL/GPS/reporting orchestration, shared request telemetry and SQLite session recovery still need implementation. No application tests, paid extraction or deployment were performed for this documentation task.

## Verification

The review used every `03-Handoffs/*.md` file, all design Markdown, the native v1 draw.io labels and relevant frontend/backend source. Structural checks verify route coverage, referenced paths, existing tool signatures, numbered catalog sections, JSON example syntax and whitespace. These checks supplement the manual review; they do not prove runtime correctness or complete client acceptance.
