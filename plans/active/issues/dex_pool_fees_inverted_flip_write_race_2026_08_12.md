---
doc_type: issue
title: >-
  Dispatch overlap + wrong-vocabulary CURVE-twin probe caused two slots to write conflicting
  dex_pool_fees flips; a transient re-capture was corrected, final state = all 21 retired
summary: >-
  On 2026-08-12 two AO slots executed overlapping `dex_pool_fees` retirements against the
  same canonical defi availability index (the plan's P2 todo and the phantom-premise
  issue-doc todos). Slot 32 correctly content-verified that ALL 21 rows (7 BALANCER +
  14 CURVE) are redundant with the canonical `dex_pool_state` corpus and, per operator
  BLK-9aed224f, retired the 14 CURVE rows (the 7 BALANCER were retired by slot 14 per
  BLK-b118f150). Slot 14 then probed the CURVE `dex_pool_state` twins at ADDRESS-named
  paths and found "phantom" objects -- but CURVE state objects are SYMBOL-named
  (`CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet`), a wrong-vocabulary false negative (the exact
  trap the reconciliation SSOT warns about). On that false premise slot 14 applied a
  "corrective" restore re-capturing the 14 CURVE rows (its error, reversed slot 32's
  correct retirement). Content re-verification of the symbol-named objects (volume/tvl/fees
  EXACTLY cross-matching) confirmed slot 32's finding; slot 14 then re-retired the 14 CURVE
  rows. FINAL state: `dex_pool_fees` captured=0 / attempted_failed=21 -- the verified +
  operator-authorized disposition. Root causes: (1) dispatch overlap (two AO-eligible
  todos for the same logical retirement), (2) the wrong-vocabulary probe. Both now
  documented; no data lost at any point (status flips only, fully reversible).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, dex-pool-fees, retirement, data-correctness, write-race, coordination, wrong-vocabulary]
related:
  [
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
created: "2026-08-12"
last_updated: "2026-08-12"
source: >-
  Live finding by AO slot 14 (data_engineering) 2026-08-12 while executing plan todo 7
  (dex_pool_fees verify+retire). Overlapping dispatch of the plan todo and the issue-doc
  disposition todo caused two concurrent writers to the same canonical index; a
  wrong-vocabulary twin probe on slot 14 produced a transient re-capture.
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Dispatch overlap + wrong-vocabulary CURVE-twin probe on `dex_pool_fees` (2026-08-12)

## What happened (corrected record of 2026-08-12)

Two AO slots executed overlapping `dex_pool_fees` retirements on the same canonical index
(`_index/availability_index.parquet`, `market-data-tick-defi-prd-central-element-323112`):

1. **Slot 32** (issue-doc todo 2, `dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md`)
   discovered the CURVE `dex_pool_state` objects are **SYMBOL-named**
   (`CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet`, `DAI-USDC.parquet`) and content-verified the
   14 CURVE `dex_pool_fees` rows are redundant (volume/tvl/fees EXACTLY cross-match; the
   `fees_usd` == `daily_supply_revenue_usd`). Operator confirmed **BLK-9aed224f = A
   (retire-as-superseded)**. Slot 32 retired the 14 CURVE rows (~17:1xZ).

2. **Slot 14 (this slot, plan todo 7)** retired the 7 BALANCER rows per BLK-b118f150
   (content-verified address-named twin `swap_fees`, all 7 days) at ~17:12Z. Then, probing
   the CURVE `dex_pool_state` twins at **ADDRESS-named paths** (`{instrument_id}.parquet`
   where the manifest `instrument_id` is the bare address), found 0/14 objects and
   concluded "phantom" / "only copy". **This was a wrong-vocabulary false negative** --
   CURVE state objects are symbol-named; the manifest `instrument_id` is the bare address
   but the object filename is the symbol. The SSOT warns of exactly this class of error
   ("a wrong-vocabulary probe already produced one false 'twin absent' verdict").

3. On that false premise, slot 14 applied `fix_dex_pool_fees_inverted_flip_2026_08_12.py`
   (approved via BLK-332dbe10) which RESTORED the 14 CURVE rows to `captured` -- **slot
   14's error**, it reversed slot 32's correct retirement.

4. Independent content re-verification of the symbol-named objects (slot 14,
   `USDC-CRVUSD.parquet`: `pool_id=0x4dece678..`, `tvl_usd=23,787,340.92`,
   `volume_usd=7,426,451.36`, `daily_supply_revenue_usd=371.32` -- identical to the
   `dex_pool_fees` object) CONFIRMED slot 32's finding. Slot 14 then re-retired the 14
   CURVE rows (`retire_dex_pool_fees_all_captured_rows_2026_08_12.py`).

**FINAL state (verified)**: `dex_pool_fees` `captured`=0 / `attempted_failed`=21.

## Why it matters

- **No data was lost at any point** (all flips are status-only, fully reversible, no
  rows/objects deleted). But the ping-pong caused transient honest-coverage mislabels and
  exposed two process gaps.
- **Dispatch overlap**: two AO-eligible `- [ ]` todos (the plan's P2 + the issue-doc
  disposition) for the SAME logical retirement were both dispatched; nothing gated them on
  each other, so two slots wrote the same manifest index concurrently.
- **Wrong-vocabulary probe**: the reconciliation SSOT's standing warning; the address-named
  probe missed symbol-named CURVE objects. Slot 14's corrective restore was a real (if
  reversible) data-correctness error on top.
- The final disposition (all 21 retired as content-verified superseded duplicates) is
  consistent and operator-authorized (BLK-b118f150 + BLK-9aed224f).

## Recommended decision

1. **CLOSED (execution)**: final state is 0 captured / 21 attempted_failed, independently
   verified. No further retirement needed.
2. **Reconcile the remaining issue-doc todo 1** (`dex_pool_fees_phantom_premise_...-1119d9d2c3d8`,
   still dispatched): its "content-verify + retire the 7 BALANCER rows" is ALREADY DONE (slot
   14, BLK-b118f150). Mark it done / stop its worker so it does not re-run.
3. **Process gap (tracked)**: add a coordination gate (depends_on / gate_on_depends, or a
   shared-condition) when a plan todo's execution is split into an issue doc, so the two
   retirement todos never dispatch concurrently to the same manifest index. Also note the
   wrong-vocabulary trap for CURVE `dex_pool_state` (symbol-named objects) in the
   reconciliation SSOT.

## Todos

- [x] ✅ [DATA] P1. Retire all remaining captured `dex_pool_fees` rows (final: 0 captured /
      21 attempted_failed), verified. (repo: market-tick-data-service) — slot 14
- [ ] [DATA] P1. Reconcile issue-doc todo 1 (`dex_pool_fees_phantom_premise_...-1119d9d2c3d8`):
      the 7 BALANCER retirement is already done; stop/re-scope its worker. (repo:
      agent-orchestrator) — operator/main
- [ ] [DATA] P2. Add the coordination gate so plan + issue-doc retirement todos never
      dispatch concurrently to the same manifest, and document the CURVE `dex_pool_state`
      symbol-named-object vocabulary in the reconciliation SSOT. (repo: market-tick-data-service)

## Progress Log

- **2026-08-12 (slot 14, data_engineering)**: Initial incident write-up (now corrected above)
  mis-attributed slot 32's correct CURVE retirement as an inverted flip, based on slot 14's
  wrong-vocabulary address-named probe. Corrected after independent re-verification of the
  symbol-named CURVE `dex_pool_state` objects. The real root causes are dispatch overlap +
  the wrong-vocabulary probe; the final state (0 captured / 21 attempted_failed) is the
  verified + operator-authorized disposition. Slot 14's corrective restore was an error,
  now reverted.
