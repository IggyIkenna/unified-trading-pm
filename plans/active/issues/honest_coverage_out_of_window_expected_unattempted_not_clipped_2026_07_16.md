---
doc_type: issue
title:
  Honest-coverage out-of-window exclusion — VERIFIED already correct (out-of-life cells are `empty_confirmed` →
  clipped); no fleet-wide change needed
summary:
  "Investigated 2026-07-16 on operator request while root-causing the 2019 CME OHLCV false-CRITICAL
  DP_VM_GONE_NO_CAPTURE alerts ('what about honest coverage… outside window not a gap, else the denominator looks larger
  than needed'). Conclusion: the coverage denominator ALREADY correctly excludes out-of-coverage-window cells.
  Out-of-life cells (pre-genesis-chain / pre-venue-launch / pre-source-coverage / not-listed / delisted /
  pre/post-season) are written as `capture_status=empty_confirmed` with the OUT_OF_COVERAGE_WINDOW reason (the
  instruments-service `enumerate_expected_universe.py` enumerator + `record_expected_empty`, which delegates to
  `record_empty` → `empty_confirmed`), and `compute_honest_coverage` CLIPS them from both numerator and denominator via
  `out_of_window` (operator direction 2026-06-23). The `expected_unattempted` rows carry BLANK reasons (`pending_fetch`,
  the real backlog); `record_expected_unattempted` takes no reason arg, so `expected_unattempted_known_empty` (which the
  compute numerator-credits) is effectively empty in practice — there is no live inflation from out-of-window cells. A
  candidate compute-layer fix (clip the out-of-window subset of `expected_unattempted_known_empty`) was drafted and then
  reverted as unnecessary once the write-path was traced. NOTE: initial framing in this session incorrectly assumed
  `record_expected_empty` writes `expected_unattempted`; it writes `empty_confirmed` — which is exactly why the existing
  clip already covers these cells."
source:
  [
    "operator request 2026-07-16 (honest-coverage out-of-window question, raised while root-causing the 2019 CME OHLCV
    false-CRITICAL DP_VM_GONE_NO_CAPTURE alerts)",
  ]
resolved_by: "VERIFIED-ALREADY-CORRECT 2026-07-16 — write-path traced; no code change needed"
locked_by:
status: resolved
nature: process
asset_group: [cefi, tradfi, defi, sports, prediction]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, deployment-api, instruments-service]
scope: [engineer, admin]
tags: [honest-coverage, data-correctness, denominator, out-of-window, verification]
related: [codex/02-data/honest-coverage-model.md, codex/02-data/tradfi-databento-sourcing-ssot.md]
created: 2026-07-16
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data-pipeline
drift_direction: none
depends_on: []
---

# Out-of-window exclusion is already correct — write-path traced, no fix needed

## Question (operator, 2026-07-16)

> "what about honest coverage for data status and manifest — surely that's needing update to outside window, not a gap
> rather than empty confirmed. Same for defi/cefi/sports/prediction — the outside gaps [are] known by UAC already, else
> the denominator looks larger than needed."

## Answer: already handled — out-of-life cells are `empty_confirmed` and clipped

Two mechanisms exclude out-of-window cells from the completion-% denominator, and both are live:

1. **Layer-1 expected matrix** — the denominator is windowed by the UAC floor
   (`listing_window = [max(get_instrument_discovery_start(venue), instrument_listed_from) … listed_to]`), so below-floor
   dates are never in the expected universe.
2. **`compute_honest_coverage` `out_of_window` clip** — out-of-life cells carry a reason in
   `OUT_OF_COVERAGE_WINDOW_REASONS` and are subtracted from BOTH numerator and denominator, so they read as a BLANK, not
   a coverage success (operator direction 2026-06-23).

The key write-path fact (traced this session): **out-of-life cells are written as `empty_confirmed`, not
`expected_unattempted`.**

- `record_expected_empty(reason=EXPECTED_*)` is a thin wrapper over `record_empty` → `capture_status="empty_confirmed"`
  (UTL `manifest_writer/_writer_record.py:343`).
- The enumerator `instruments-service/scripts/enumerate_expected_universe.py` writes not-listed / delisted /
  pre-venue-launch cells as `empty_confirmed` (lines 1060-1061, 1004-1038), keyed to the OUT_OF_COVERAGE_WINDOW reason.
- `record_expected_unattempted` takes **no** `reason` argument — it always writes `error_reason=""` → `pending_fetch`
  (the real fetch backlog, correctly in the denominator as a gap).

Therefore `expected_unattempted_known_empty` (`expected_unattempted` + an `EXPECTED_` reason) — the only bucket the
compute numerator-credits — is effectively unpopulated in practice, so there is **no out-of-window inflation** to fix.
`read_capture_status_counts`'s `out_of_window` (a subset of `empty_confirmed`) already catches every out-of-life cell.

## Why the initial "systemic bug" framing was wrong

Earlier in the session I assumed `record_expected_empty` writes `expected_unattempted` (→ `known_empty` →
numerator-credited → inflation). It does not — it writes `empty_confirmed`, which the existing `out_of_window` clip
already excludes. A drafted compute-layer parity-clip (a new `out_of_window_expected_unattempted` field across
UAC/UTL/deployment-api) was reverted once the write-path was traced; it would have been a harmless no-op, not a fix.

## Residual (optional, operator's call — NOT a bug)

`compute_honest_coverage` (the reachable-style number the UI shows) clips out-of-window. The separate **`all_shards`
completeness view** deliberately INCLUDES `empty_confirmed` (so the honest trailing-lag dip is visible) — so out-of-life
cells still appear in that view's denominator by design (honest-coverage-model.md § "Coverage formula"). If the operator
wants out-of-window excluded from the all-shards view too, that is a small deliberate model change, not a correctness
bug. No action taken pending operator direction.

## Related shipped work (the actual 2019 CME fix)

- `deployment-service@d912670` — TradFi OHLCV launchers clamp `--start-floor` to the per-venue UAC discovery floor
  (`ohlcv_clamp_floor_to_venue`), so below-floor VMs are never launched.
- `market-tick-data-service@c85af5b2` — below-floor `process_ticks` writes NO manifest row (out-of-window, excluded by
  Layer-1 windowing) and logs a `HONEST_ABSENCE` run.log signal so a processed below-floor date classifies benign
  instead of a false-CRITICAL `DP_VM_GONE_NO_CAPTURE`.
