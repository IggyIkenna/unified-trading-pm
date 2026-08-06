---
doc_type: issue
title: >-
  TRADFI:volatility computes 0/10 groups — _resolve_spot_perp searches for PERPETUAL instrument_type in TRADFI MTDS, but
  FX underlyings (6A/6B/6C/6E/6J) have only FUTURE/futures_chain types
summary: >-
  TRADFI:volatility benchmark VM (features-e2e-tradfi-20260806-024229-40bb75) ran for 23 minutes, exit_code=0, but
  produced 0/10 feature group successes. Root cause: `VolatilityDataLoader._resolve_spot_perp` (data_loader.py:356)
  reads TRADFI MTDS availability_index filtered for `instrument_type == "PERPETUAL"` and `data_type == "trades"`. TRADFI
  MTDS contains no PERPETUAL records — only BOND, COMBO, EQUITY, FUTURE, INDEX, SPOT_PAIR, futures_chain, options_chain.
  The 10 groups use FX underlyings (6A=AUD/USD, 6B=GBP/USD, 6C=CAD/USD, 6E=EUR/USD, 6J=JPY/USD) discovered from IS
  catalogue — CME FX futures contracts that have no perpetual-swap equivalent. The code logs "No captured perp for %s on
  %s — skipping spot price" for all 145 underlyings, and honest-absence guard rejects all manifest writes without
  FetchEvidence. 0 features written, 0 manifest rows created — the honest right outcome, but the feature is broken for
  TRADFI.
status: open
nature: issue
asset_group: [tradfi]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [tradfi, volatility, spot-price, perp, code-gap, feature-gap, fx-underlyings]
related: [/plans/active/data_pipeline_check_mdps_features_2026_07_20.md]
created: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
source: >-
  slot-5 (data_engineering), 2026-08-06: post-VM log analysis for data_pipeline_check_mdps_features-056,
  TRADFI:volatility 0/10 outcome
---

## Finding summary

**VM**: `features-e2e-tradfi-20260806-024229-40bb75`, 7-day window, exit_code=0, **0/10 groups succeeded**

**Log**: "No captured perp for 6A on 2026-07-29 — skipping spot price" (× 145 underlyings × dates)

## Root cause

`VolatilityDataLoader._resolve_spot_perp` (features_service/volatility/core/data_loader.py:356-405):

```python
index = read_availability_index(self.bucket, columns=[...],
    filters=[("date", "==", date_str)])
# then: instrument_type.upper() == "PERPETUAL" and data_type == "trades"
```

It searches `self.bucket` (TRADFI MTDS: `market-data-tick-tradfi-prd-central-element-323112`) for records where
`instrument_type == PERPETUAL`. The TRADFI MTDS availability index contains:

```
instrument_type distribution (2026-08-01+):
  FUTURE: 725, COMBO: 266, futures_chain: 95, SPOT_PAIR: 33, EQUITY: 9, options_chain: 6, BOND: 6, INDEX: 6
```

**No PERPETUAL type exists in TRADFI.** The FX underlyings (6A, 6B, 6C, 6E, 6J) are CME FX futures contracts —
traditional finance has no perpetual swaps equivalent. In CEFI, the volatility feature uses perpetual swaps as a spot
proxy for options pricing. In TRADFI, the equivalent is the continuous front-month futures contract, which appears as
`instrument_type=futures_chain` (e.g., `CME:FUTURE:AUD` for the 6A underlying).

`options_chain` in TRADFI MTDS only contains `CME:OPTION:SP500` (6 rows), meaning FX options data is either not captured
by MTDS or uses a different path. The 10 feature groups that ran (all FX) had no options data either — the feature
groups likely enumerate underlyings from the IS catalogue (which DOES list FX options underlyings), then fail silently
when the spot price lookup returns None.

## Impact

- All TRADFI:volatility FX groups (6A/6B/6C/6E/6J): 0/10 feature groups computed
- Honest-absence guard correctly rejects empty manifest writes
- Root cause is a **code gap in `_resolve_spot_perp`** — it assumes all asset groups use perpetual swaps as the spot
  proxy. TRADFI FX needs a different lookup (futures_chain continuous contract)

## Resolution options

**Option A (code fix, recommended)**: Make `_resolve_spot_perp` asset-group-aware. For TRADFI, look for
`instrument_type in {"futures_chain", "FUTURE"}` instead of `"PERPETUAL"`, matching on `instrument_id` pattern (e.g.,
`CME:FUTURE:AUD` for underlying `6A` → AUD). Requires mapping from underlying code (6A, 6B, etc.) to TRADFI MTDS
instrument_id prefix.

**Option B (MTDS fix)**: Add synthetic PERPETUAL records to TRADFI MTDS for FX underlyings by re-writing their
continuous futures as a PERPETUAL data_type. Less recommended — changes MTDS semantics.

**Option C (descope)**: Mark TRADFI:volatility FX feature groups as `expected_unattempted` until the underlying code gap
is fixed. Unblocks the benchmark to report 0 throughput (honest absence), but doesn't fix the feature.

**Operator decision needed**: Confirm approach (Option A code fix is recommended). The fix requires:

1. IS catalogue mapping: which TRADFI MTDS `futures_chain` instrument corresponds to each FX underlying?
2. Code change in `_resolve_spot_perp` to handle TRADFI asset_group differently
3. QG + quickmerge

## Todos

- [ ] [OPERATOR] P1. **Confirm fix approach for TRADFI FX spot-price lookup** — Option A (make `_resolve_spot_perp`
      asset-group-aware, use futures_chain for TRADFI) is recommended. BLOCKED until operator confirms and provides the
      6A/6B/6C/6E/6J → CME:FUTURE:XXX instrument_id mapping convention.
- [ ] [DATA] P1. **Implement Option A and relaunch TRADFI:volatility benchmark** — once `_resolve_spot_perp` returns
      correct (venue, symbol) for TRADFI FX underlyings, relaunch
      `launch-features-vm.sh FAMILY=volatility ASSET_GROUP=TRADFI` to capture real throughput.

## Progress Log

- **2026-08-06 (slot-5, data_engineering)**: diagnosed from VM exit_code=0 / 0/10 groups log. Confirmed TRADFI MTDS has
  no PERPETUAL type (FUTURE/futures_chain exist instead). `_resolve_spot_perp` is CEFI-only in practice.
  BLOCKED-OPERATOR-DECISION for fix approach.
