# Handoff — API/mock behaviour and retry fixes

**From:** John Phang (C) → **To:** Jeffrey Kong (D)

**Date:** 17 Nov 2026, SGT. **Timing:** Implement at the next code push opportunity.

**Reference:** [PR #9](https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express/pull/9), reviewed head `9f5b1c9`. **Status:** Implementation pending.

| API state | Demo (`use_mock=true`) | Live (`use_mock=false`) |
|---|---|---|
| Endpoint unconfigured | Use fixture; prominent **Demo Data** tag | Block call; **Not connected** empty state |
| API succeeds | Real response; optional **Live** tag | Real response; optional **Live** tag |
| API fails | Error/empty state; no mock fallback | Error/empty state; no mock fallback |
| API returns no records | **No data found**; no fixture | **No data found**; no fixture |

1. **Per-feature behaviour:** Apply the matrix to each call so real and demo features can coexist. Source tags must reflect the displayed data.

2. **Failure isolation:** Block only the affected call and keep other features usable. Clear or distinguish stale results when showing empty/error states.

3. **Endpoint configuration / Issue #1:** Distinguish an unconfigured endpoint from an empty API base, since relative paths such as `/api/weekly` support same-origin calls. Agree per-endpoint readiness with C, and ensure badges reflect the displayed data rather than one global mock setting.

4. **npm profiles:** Add `dev:demo`, `dev:live`, `build:demo` and `build:live` using Vite `--mode demo` / `--mode live`, with `VITE_USE_MOCK=true` in `.env.demo` and `false` in `.env.live`. Parse the strings explicitly, document configuration in the frontend README, keep secrets out of `VITE_` variables, and restart/rebuild after changes.

```JSON
{
  "dev:demo": "vite --mode demo",
  "dev:live": "vite --mode live",
  "build:demo": "vite build --mode demo",
  "build:live": "vite build --mode live"
}
```

- Set VITE_USE_MOCK=false live mode. 
- demo mode permits fallback; it does not force mock responses.

5. **Issue #2 — Body-level failure:** HTTP 200 with `status: failed` must enter the error flow instead of ordinary success. Preserve `error.retryable` and show a working Retry action only when appropriate.

6. **Issue #3 — Weekly Retry:** If loading available weeks fails, Retry must repeat that initial sequence rather than request `week_start=null`. An empty week list shows a no-data state; a failed selected-week request retries that valid week without misleading stale results.

7. **Integration:** Confirm API shapes with C and weekly definitions with B; unavailable calculations remain unknown rather than zero. Retain Ralph’s file-backed evidence tools, and verify real session recovery against C’s backend rather than treating mock storage as persistence evidence.

8. **Checks and next push:** Run lint, both profile builds, and checks covering mixed availability, source tags, same-origin calls, empty/failing responses and both retry fixes; record actual results. Update PR #9 if open, otherwise raise a follow-up PR, with John reviewing API behaviour and Wai Hong incorporating the cases into the shared suite.
