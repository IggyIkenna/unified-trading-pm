---
doc_type: issue
title: >-
  TRADFI:volatility `options_iv`/`options_term_structure` feature groups call `record_empty(SOURCE_RETURNED_ZERO)`
  without FetchEvidence — honest-absence guard rejects the write, masking a possible real fetch failure as absence
summary: >-
  Found live during the `features-volatility-tradfi-20260817-020551` relaunch verifying the `_resolve_spot_perp`
  TRADFI fix (`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`). After that fix, spot-price
  resolution now genuinely succeeds for TRADFI FX underlyings (6A/6B/6C/6E/6J), so the run progresses past the
  previous total 0/10 failure into real per-group feature computation. Two of the ten feature groups —
  `options_iv` and `options_term_structure` — each log exactly one WARNING per full-window run:
  `empty_confirmed manifest write failed for <group> date=2026-07-23: record_empty(reason=SOURCE_RETURNED_ZERO)
  requires FetchEvidence proving a clean 200+empty fetch (http_status in 2xx AND response_received AND
  rows_in_response == 0 AND error_signal == ""). The supplied evidence does NOT prove honest absence (no
  FetchEvidence supplied). This is most likely an auth / rate-limit / 5xx / timeout / exception / missing-credential
  path masquerading as honest absence`. The manifest write is correctly REJECTED by the honest-absence guard (no
  silent placeholder written) but the caller only logs a WARNING and moves on — it never surfaces a `record_failed`
  fallback, so the row is simply never recorded either way for that date. Root cause not yet located (the failing
  call site is somewhere in the options-group feature calculators, not `VolatilityDataLoader` itself, which this
  session did not read). Plausible root cause: TRADFI MTDS has essentially no options data for FX underlyings (per
  the sibling doc's own finding — `options_chain` only has 6 `CME:OPTION:SP500` rows), so the calculator IS hitting
  genuine absence but is calling `record_empty` without first obtaining/threading a `FetchEvidence` object through —
  a wiring gap, not necessarily a masked real failure, but per this workspace's honest-absence discipline that must
  be PROVEN (not assumed) before treating it as benign.
status: open
nature: issue
asset_group: [tradfi]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [tradfi, volatility, options, honest-absence, fetch-evidence, feature-gap]
related:
  [
    /plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-17"
author: slot-33 (data_engineering)
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  slot-33 (data_engineering), 2026-08-17: found while relaunching features-volatility-tradfi-20260817-020551 to
  verify tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md todo 2 (real-throughput capture).
context_scope:
  [
    features-service/features_service/volatility/engine/feature_group_service.py,
    /plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
---

## What I found

Live VM run `features-volatility-tradfi-20260817-020551` (7-day window, 2026-07-23..29, TRADFI, `--feature-group
ALL`): after the `_resolve_spot_perp`/`_resolve_ohlcv_underlying_tradfi` fix landed, the run progresses through each
of the 10 volatility feature groups for real (spot price resolution genuinely succeeds now — confirmed via direct
log evidence, e.g. `Loaded 4301 CME/AUD OHLCV candles (ohlcv_1m)` for underlying `6A`). Two groups each hit exactly
one rejected manifest write:

```
2026-08-17 02:36:49,505 WARNING empty_confirmed manifest write failed for options_iv date=2026-07-23:
  record_empty(reason=SOURCE_RETURNED_ZERO) requires FetchEvidence proving a clean 200+empty fetch
  (http_status in 2xx AND response_received AND rows_in_response == 0 AND error_signal == "").
  The supplied evidence does NOT prove honest absence (no FetchEvidence supplied). This is most likely an
  auth / rate-limit / 5xx / timeout / exception / missing-credential path masquerading as honest absence —
  call record_failed instead. [row_key={'date': '2026-07-23', 'feature_group': 'options_iv'}]

2026-08-17 03:02:42,878 WARNING empty_confirmed manifest write failed for options_term_structure date=2026-07-23:
  (same message, feature_group=options_term_structure)
```

Only ONE date (2026-07-23, the first date of the window) triggered this per group across the whole 7-day run —
consistent with a group-level aggregate write attempted once per group, not per-day.

## Why it matters

The honest-absence guard is doing its job (refusing to silently write a placeholder), but the caller swallows the
rejection as a bare WARNING and moves on — the row is never written as either `captured`, `attempted_failed`, nor a
correctly-evidenced `empty_confirmed`. This is exactly the "auth/rate-limit/5xx/timeout/missing-credential path
masquerading as honest absence" pattern the guard's own error message warns about — it has NOT been verified whether
these two groups are genuinely data-absent (TRADFI has ~6 real options rows total, so plausible) or hitting a silent
fetch failure. Per this workspace's honest-absence + data-pipeline-correctness rules, this must be proven, not
assumed.

## Recommended decision

- [ ] [DIAG] P2. Locate the `options_iv`/`options_term_structure` feature-group calculator call site in
      `features-service` that calls `record_empty(reason=SOURCE_RETURNED_ZERO)` without threading a `FetchEvidence`
      through, and determine whether the underlying fetch is genuinely a clean 200+empty (real TRADFI options-data
      scarcity, matching `options_chain`'s ~6-row population noted in the sibling doc) or a masked real failure.
      **Repo: features-service.**
- [ ] [CODE] P2. Once diagnosed: either thread proper `FetchEvidence` through so `record_empty` succeeds
      (genuine absence case), or switch the call to `record_failed` with the correct `RecordFailedReason` (masked
      failure case). **Repo: features-service.**

## Progress Log

- **context-scout 2026-08-17**: populated context_scope (3 entries) — swapped the originally-listed `data_loader.py`
  (the doc's own text explicitly says this session did not read it and the bug is not there) for
  `engine/feature_group_service.py`, confirmed via grep to be the actual `record_empty(...)` call site that
  dispatches to `_calculate_options_iv`/`_calculate_options_term_structure`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
