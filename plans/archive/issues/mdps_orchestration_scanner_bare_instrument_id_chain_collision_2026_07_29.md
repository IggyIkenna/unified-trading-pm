---
doc_type: issue
title:
  MDPS `orchestration_scanner.py`'s `existing_outputs` dedup set keys on bare `(timeframe, instrument_id)` — same
  cross-chain pool-address collision class already fixed on the MTDS side
summary: >-
  Split off `defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`'s combined MTDS+MDPS todo after the MTDS half
  shipped (`market-tick-data-service@5bf8a3c7`, colon-prefixes `chain` into the preflight atom string). The MDPS half —
  `market_data_processing_service/app/core/orchestration_scanner.py`'s `existing_outputs` dedup set, keyed on bare
  `(timeframe, instrument_id)` with no `chain` component — was never independently verified or fixed; the 2026-07-26
  audit's own scoped GCS check (whether MDPS output filenames already embed `chain`, which would make this a non-issue
  at this specific site) timed out before completing. Filed as its own MDPS-scoped todo so it does not silently
  disappear now that the sibling MTDS fix is done.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [defi, chain-collision, dedup, mdps, orchestration-scanner, cross-chain]
related:
  [
    /plans/active/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-29"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "confirmed-moot (no code change) -- live GCS evidence, see body"
source: >-
  Split from defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md's combined MTDS+MDPS todo (2026-07-29, MTDS
  CODE_QUICK backlog closeout pass) after the MTDS half shipped independently.
---

> **🟢 ARCHIVED 2026-07-29 — ACKED-AS-INVALID (confirmed non-issue, not a false positive of the finding itself, just not
> live at this specific site).** The scoped GCS read this doc asked for (timed out on the prior attempt) completed
> cleanly this pass: real MDPS `processed_candles/` output filenames for CURVE (2 of the 6 known collision addresses,
> both `dex_pool_swaps` and `dex_pool_state`) are always the FULL canonical chain-embedded id
> (`CURVE-AVALANCHE:POOL:USDC-USDT.parquet`), never the bare pool address — so `chain` is already baked into the
> `existing_outputs` dedup key and can never collide across chains here. No code change needed. Evidence folded back
> into `defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`'s "MDPS half" note.

# MDPS `orchestration_scanner.py` bare-instrument_id chain-collision gap

## Finding (inherited from the parent doc's 2026-07-26 investigation)

`market_data_processing_service/app/core/orchestration_scanner.py` (~L680-693) builds an `existing_outputs` dedup set
via `extract_instrument_id_from_blob_path(blob_metadata.name)` — keyed on bare `instrument_id`, no `chain` component.
Same risk shape as the MTDS preflight bug already fixed (`defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`):
if MDPS's output-existence check ever extracts the bare pool address as the per-instrument key (rather than a
chain-embedded canonical form), two chains' candle outputs for the same address could shadow each other in this dedup
set — an already-materialized shard for one chain would make the OTHER chain's genuinely-missing shard look
already-covered, silently skipping its (re)computation.

**Not fully confirmed empirically** as of 2026-07-26 — a scoped `gcloud storage ls` under a real captured day's prefix
(to check whether the actual output filename embeds `chain` or not) was attempted but the manifest reader was in a slow
degraded per-VM-shard fallback mode at the time and the check did not complete. The static evidence (file/line above)
stands on its own as a credible risk finding regardless.

## Todos

- [x] ✅ [DATA] P2. **CONFIRMED MOOT 2026-07-29 — non-issue at this site, cited evidence, no code change needed.** Ran
      the scoped GCS read the todo asked for (not a corpus walk): sampled real
      `market-data-tick-defi-prd-central-element-323112/processed_candles/.../venue=CURVE/` output for `day=2026-07-25`
      across both `dex_pool_swaps` and `dex_pool_state` data_types (2 of the 6 known collision rows' shape,
      CURVE-AVALANCHE + CURVE-ETHEREUM both present that day). Every real output filename is the FULL canonical
      chain-embedded id (e.g. `CURVE-AVALANCHE:POOL:USDC-USDT.parquet`, `CURVE-ETHEREUM:POOL:CBBTC-WBTC.parquet`) —
      never the bare `pool_address.lower()`. Since `extract_instrument_id_from_blob_path` just takes the filename stem,
      it already returns this chain-embedded string for every real MDPS candle output — `chain` is baked directly into
      the id itself, so `existing_outputs`'s `(timeframe, instrument_id)` key can never collide across chains at this
      site (unlike the MTDS raw-tick side, which reads the catalogue's bare `instrument_id` verbatim by design). This
      matches the todo's own stated resolution path ("if so, this is a non-issue at this specific site"). Folded back
      into the parent doc — see `defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`'s "MDPS half" note, updated
      in the same session. No code change; no `quality-gates.sh` run needed (no diff).

## Progress Log

- 2026-07-29: filed by the MTDS CODE_QUICK backlog closeout pass, splitting this off from
  `defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md`'s combined todo after shipping the MTDS half
  (`market-tick-data-service@5bf8a3c7`) — this MDPS half was out of that dispatch's repo scope.
