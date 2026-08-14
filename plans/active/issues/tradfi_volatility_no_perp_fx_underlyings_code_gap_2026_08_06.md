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
context_scope:
  [
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    features-service/features_service/volatility/core/data_loader.py,
  ]
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

- [ ] [CODE] P1. **RULED 2026-08-06 (operator), option A: approved.** `[CODE]` tag (was `[OPERATOR]`) — make
      `_resolve_spot_perp` asset-group-aware, use `futures_chain`/`FUTURE` instrument_type for TRADFI. **Mapping
      convention — standard CME FX futures underlyings** (widely-known market convention, not fabricated): 6A =
      Australian Dollar, 6B = British Pound, 6C = Canadian Dollar, 6E = Euro, 6J = Japanese Yen — each maps to its
      corresponding CME FX futures contract. **`instrument_id` STRING format VERIFIED 2026-08-14** (code + live
      catalogue, see Progress Log) — `CME:FUTURE:<PRODUCT_ROOT>-USD@LIN-YYYYMMDD`, e.g.
      `CME:FUTURE:AUD-USD@LIN-20200113` for 6A. Product roots: 6A→AUD, 6B→GBP, 6C→CAD, 6E→EUR, 6J→JPY. Note it is
      PER-EXPIRY (dated), not one static id per underlying — the fix needs to select the correct/current-front-month
      expiry, not a fixed string. **Confirm fix approach for TRADFI FX spot-price lookup** — Option A (make
      `_resolve_spot_perp` asset-group-aware, use futures_chain for TRADFI) is recommended.
- [ ] [DATA] P1. **Implement Option A and relaunch TRADFI:volatility benchmark** — once `_resolve_spot_perp` returns
      correct (venue, symbol) for TRADFI FX underlyings, relaunch
      `launch-features-vm.sh FAMILY=volatility ASSET_GROUP=TRADFI` to capture real throughput.

## Progress Log

- **2026-08-06 (slot-5, data_engineering)**: diagnosed from VM exit_code=0 / 0/10 groups log. Confirmed TRADFI MTDS has
  no PERPETUAL type (FUTURE/futures_chain exist instead). `_resolve_spot_perp` is CEFI-only in practice.
  BLOCKED-OPERATOR-DECISION for fix approach.
- **na-eligibility-audit 2026-08-06** (tradfi tranche, dispatch agt-e38653): **KEEP-NA, valid — operator-gated by
  construction (first pass on this 2026-08-06 doc).** Both open todos re-read end-to-end; count reconciled (2/2). Todo 1
  IS the operator decision itself (confirm fix approach A/B/C + provide the 6A/6B/6C/6E/6J → `CME:FUTURE:XXX`
  instrument_id mapping convention); todo 2 is explicitly gated "once `_resolve_spot_perp` returns correct ..." on the
  operator's ruling. Fails the bounded-outcome bar by design — nothing a worker can determine alone. Nothing to
  reclassify.
- **na-eligibility-audit 2026-08-07** (tradfi tranche, dispatch agt-aca83b): **KEEP-NA — reason updated, still NOT
  reclassify-eligible.** The 2026-08-06 marker above is stale: the operator has since ruled on the fix approach same-day
  (`unified-trading-pm@001112aaf`, option A approved, todo 1's tag flipped `[OPERATOR]`→`[CODE]`), so "operator-gated by
  construction" no longer holds. But todo 1's CME `instrument_id`-format verification sub-task is a near-verbatim
  duplicate of the `[DIAG] P2` todo already tracked in
  `/plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md` (that doc's own filed conflict-check item
  5/6: "dispatching both risks two workers independently verifying the same thing"). Per the shared conflict-check
  protocol (`ao-dispatch-batch-naming-and-conflict-check.md` § 3), this is a live CONFLICT, not a clear RECLASSIFY —
  staying NA until that already-filed conflict resolves (reclassify/dedupe/re-affirm), rather than re-filing a duplicate
  conflict record here.
- **context-scout 2026-08-07**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, confirmed -- re-verified,
  unchanged.** 2 open todos re-read end-to-end; count reconciled (2/2). Independently re-checked the 08-07 marker's
  conflict citation: `governance_sweep_deferred_followups_2026_08_06.md`'s item 5/6 (naming this exact doc) and its
  target `[DIAG] P2` todo are both still present and still open. Per the never-re-litigate-a-cited-conflict rule,
  preserved KEEP-NA rather than re-deriving. Todo 2 remains sequenced behind todo 1. Nothing to reclassify.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:24f6096f8fd0df18]: **KEEP-NA,
  confirmed -- confirmed unchanged.** Phase-0 flagged this doc as "changed since the 08-08 marker" (git-date fallback),
  but `git diff <08-08-marker-sha>..HEAD` shows the ONLY intervening change is the context-scout line above -- zero
  todo/verdict content changed. Reaffirming the 08-08 verdict without a fresh full re-read; see
  `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` for the underlying false-positive class
  this run found and filed.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:c56bf43b9d580dfe]: **KEEP-NA,
  valid -- fresh full read.** Independently re-verified the live CONFLICT citation by reading
  `governance_sweep_deferred_followups_2026_08_06.md` directly: its `[DIAG] P2` todo ("Verify the exact CME
  instrument_id string format before implementing this doc's ruled fix") is still open (`- [ ]`), and both docs still
  cross-cite each other -- the conflict is live and current, not stale. Also cross-checked against
  `tradfi_databento_account_billing_suspended_2026_08_09.md`, which lists this doc as "left ungated" (features-VM
  relaunch reads existing data). `assigned_vm` unchanged.
- **cross_cutting_satellite_ao_dispatch_batch13 2026-08-14 (slot 26, infra)**: resolved the conflict this doc's own todo
  1 was gated on — `governance_sweep_deferred_followups_2026_08_06.md`'s `[DIAG] P2` todo is now flipped (verified
  2026-08-14). CME FUTURE `instrument_id` format confirmed via 3 convergent code sites (canonical_id_builder, the
  databento catalogue-writer adapter, MTDS's `derive_tradfi_row_instrument_id`) AND a bounded live read of
  `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`:
  `CME:FUTURE:<PRODUCT_ROOT>-USD@LIN-YYYYMMDD` (per-expiry-dated, not one static id per underlying). Live examples:
  `CME:FUTURE:AUD-USD@LIN-20200113` (6A), `CME:FUTURE:GBP-USD@LIN-20200113` (6B), `CME:FUTURE:CAD-USD@LIN-20200114`
  (6C), `CME:FUTURE:EUR-USD@LIN-20200113` (6E), `CME:FUTURE:JPY-USD@LIN-20200113` (6J). Todo 1's format text updated
  above with this confirmation. Todo 1 itself stays open (the actual `_resolve_spot_perp` code change + mapping-table
  implementation is separate, unblocked, in-scope work) and todo 2 stays sequenced behind it.
