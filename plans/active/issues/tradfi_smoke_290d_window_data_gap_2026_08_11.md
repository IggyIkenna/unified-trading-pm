---
doc_type: issue
title: >-
  TradFi honest-coverage slice is INSUFFICIENT for the 290-day smoke window because of a REAL data gap (KRX zero
  captured rows; CME ~2/3 of in-window days) — not a harness bug; decision: backfill vs accept
summary: >-
  Found while fixing the tradfi atom construction in the honest-coverage smoke harness (`e2e-testing@37e7563`, archived
  `/plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md`). After the fix, the tradfi slice
  re-runs in 16s / 14 shards and EVERY shard is `INSUFFICIENT_HISTORY` — which is now verified HONEST, not a lookup bug.
  The exact-id lookup previously matched ~nothing because the tradfi manifest records coverage at (date, venue,
  data_type) CELL grain (instrument_id empty on most rows) while the harness was expanding each cell to one atom per
  instrument (~919k). With cell-grain atoms the verdicts are real: CME ohlcv_1m has 214/290 in-window days captured +
  22,996 in-window attempted_failed; CME ohlcv_1s 196/290 + 112,246 attempted_failed; NASDAQ ohlcv_1m 195/290 + 3,972
  attempted_failed; KRX ohlcv_1m has ZERO captured rows (2,564 rows, all empty_confirmed). So the harness is CORRECT and
  the honest signal is "tradfi data does not yet cover the 290-calendar-day window required by driver
  `tradfi_vol_regime_24h_200p`."
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [e2e-testing, market-tick-data-service]
scope: [engineer]
tags: [honest-coverage, smoke-harness, data-gap, tradfi, operator-decision, verify, data-correctness]
related:
  [
    /plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-11
parent_epic: infrastructure_master
priority: P3
source: honest_coverage_smoke_harness_4ag_verify-06809dbd31f9
assigned_vm: NA
resolved_by:
locked_by:
---

## Finding

Measured 2026-08-10 on the PROD manifest (11,397,262 rows; window 2025-10-25..2026-08-10 = 290 days) via the corrected
cell-grain smoke harness + a transient read-only probe (probe deleted; numbers reproduced in the archived plan's
Progress Log):

| (venue, data_type) | captured days in-window                       | in-window attempted_failed | verdict      |
| ------------------ | --------------------------------------------- | -------------------------- | ------------ |
| CME ohlcv_1m       | 214 / 290                                     | 22,996                     | INSUFFICIENT |
| CME ohlcv_1s       | 196 / 290                                     | 112,246                    | INSUFFICIENT |
| NASDAQ ohlcv_1m    | 195 / 290                                     | 3,972                      | INSUFFICIENT |
| KRX ohlcv_1m       | **0** / 290 (2,564 rows, all empty_confirmed) | 0                          | INSUFFICIENT |

The harness change that made this measurable: `MdpsUniverseProvider` now yields per-CELL atoms (instrument_id=None,
deduped to distinct (venue, data_type)) for `tradfi` via `cell_grain_asset_groups`, matching the manifest's own grain —
see `/plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` and `e2e-testing@37e7563`. Unit tests
added (`test_cell_grain_asset_group_yields_one_atom_per_venue_data_type`, `test_cell_grain_is_opt_in...`).

This is NOT a harness defect — it is the honest-coverage system doing its job: the tradfi data estate does not yet cover
the 290-day window. KRX is the stark case (zero captured). The KRX gap is already owned by
`/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`; the 100% honest-coverage drive is owned by
`/plans/active/data_completion_to_100_all_ag_2026_06_21.md`. Neither the smoke harness nor this issue duplicates that
tracked work — the only thing NOT yet tracked anywhere is the cross-cutting product decision below.

## BLOCKED-OPERATOR-DECISION

Whether to spend data-pipeline investment closing the tradfi 290-day window — and how — is an operator-owned product
decision, not a worker fix. Options:

1. **Accept INSUFFICIENT for tradfi until the tracked data work lands (RECOMMENDED).** The harness is now correct and
   reports the honest status; downstream consumers see a truthful gate. No harness or window change needed. The smoke
   slice will flip to RUNNABLE automatically once tradfi coverage closes the window via the existing data-completion
   plans. Cost: tradfi smoke verification stays RED in the interim.
2. **Prioritize/accelerate tradfi backfill** (esp. KRX, which has zero captured rows, and the in-window attempted_failed
   mass ~140k). This is real data work already tracked in the two plans above; the operator decides its priority
   relative to other asset groups.
3. **Adjust the smoke window** for tradfi (or the driver) below 290 days to force RUNNABLE. NOT recommended: it would
   mask a genuine coverage shortfall and defeat the honest-coverage guarantee.

Do NOT adjust the harness or window without the operator picking among these. Until then the correct state is: tradfi
smoke slice = `INSUFFICIENT_HISTORY` (honest), harness shipped and verified.
