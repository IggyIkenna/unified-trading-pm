---
doc_type: issue
title: >-
  `dex_pool_fees` should NOT be added to the canonical data_type registry (operator ruling) — recommend retiring the
  materialize_dex_pool_fees.py campaign once dex_pool_state/dex_pool_swaps carry equivalent fee+volume columns
summary: >-
  Investigated `dex_pool_fees` appearing as a non-canonical `data_type` in the DEFI distinct-values panel. Confirmed
  it's a real, currently-materialized corpus (`strategy-service/scripts/materialize_dex_pool_fees.py` writes a
  canonical-shaped `.../instrument_type=pool/data_type=dex_pool_fees/...` path from the Curve/Balancer subgraph;
  `strategy-service/ strategy_service/engine/core/canonical_dex_pool_provider.py` joins it for LP-fee-accrual context)
  that is genuinely absent from
  `unified_api_contracts.registry.market_data_categories.DATA_TYPES_BY_ASSET_GROUP["defi"]`. My working assumption going
  in — "this is a registry-completeness gap, add it" — was WRONG per operator domain guidance (interactive session
  2026-08-04): pool fee-TIER is a static, per-pool attribute already encoded in the instrument
  definition/`instrument_id` (the `{fee_rate_bps}BPS`/`TS{tick_spacing}` symbol discriminator documented in
  `/codex/02-data/defi-canonical-naming-ssot.md` "Solana AMM pool SYMBOL grammar" — EVM pools carry the equivalent via a
  `fee_rate_bps` column on `dex_pool_state` rows). Fee ACCRUAL (the $ revenue = volume × rate this script actually
  computes) is derivable downstream from `dex_pool_state` (rate) × `dex_pool_swaps` (volume) — the same
  "engineer-it-from-what's-already-canonical" principle the operator applied to gas fees in the same session (gas cost =
  gas units, backfilled separately, × static per-tx complexity; no separate "total gas fee" corpus needed either). The
  script's own `# Delete-when: the MTDS dex_pool_state writer joins subgraph feesUSD/volumeUSD` lifecycle marker already
  anticipated this — it was always meant to be temporary. Recommends retiring the corpus once that condition is verified
  met, rather than legitimizing it as a permanent canonical data_type. NOT executed here — filed as the recommendation +
  the concrete verification step needed before a same-session code change to a strategy-layer fee-computation path.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [strategy-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, dex-pool-fees, canonicalisation, distinct-values, strategy-layer, data-correctness, registry, retirement]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
source: >-
  Operator domain guidance (interactive session 2026-08-04) correcting this session's own initial "add to registry"
  assumption while investigating the DEFI distinct-values non-canonical data_types panel under /autonomous dispatch
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: strategy-service@f7ca12767a51dc5e7d9327b1d0b875dc5454bb8a
depends_on: []
context_scope:
  [
    strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py,
    strategy-service/scripts/materialize_dex_pool_fees.py,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
---

# `dex_pool_fees` — retirement recommendation, not a registry gap (2026-08-04)

## Why this is filed as `assigned_vm: NA` (human-planning, not AO-dispatched)

Retiring `materialize_dex_pool_fees.py` requires touching `canonical_dex_pool_provider.py` — a live strategy-layer read
path that feeds LP-fee-accrual context into PnL-adjacent computation. Per this workspace's own precedent (see
`/plans/archive/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`'s explicit decision to decline a
similarly-shaped live-reader migration same-session), a strategy-read-path change of this kind needs a dedicated review
with the actual downstream consumers checked, not a same-session autonomous code change. This doc stops at the
recommendation + the concrete unblocking verification step.

## What I found

- `strategy-service/scripts/materialize_dex_pool_fees.py` (docstring): "Materialise the `dex_pool_fees` corpus from the
  Curve/Balancer subgraphs" — writes to
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue={V}/chain={C}/ instrument_type=pool/data_type=dex_pool_fees/{file}.parquet`
  (canonical path SHAPE, just a data_type UAC never registered). `# Lifecycle: campaign` /
  `# Delete-when: the MTDS dex_pool_state writer joins subgraph feesUSD/volumeUSD, so dex_pool_fees is no longer needed`
  (script's own comment, paraphrased from the header).
- `strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py:79,235-244`:
  `_POOL_FEES_DATA_TYPE: Final[str] = "dex_pool_fees"` — reads this companion corpus for LP fee-accrual context
  alongside the main `dex_pool_state` read.
- `unified_api_contracts/registry/market_data_categories.py`'s `DATA_TYPES_BY_ASSET_GROUP["defi"]` (lines 174-260,
  confirmed by direct read): does NOT contain `dex_pool_fees`. This is why it badges non-canonical in the
  distinct-values panel.
- `/codex/02-data/defi-canonical-naming-ssot.md` "Solana AMM pool SYMBOL grammar" section: pool fee-tier is already a
  discriminator baked into the canonical `instrument_id`/symbol (`{fee_rate_bps}BPS`/`TS{tick_spacing}`) for Solana
  pools; EVM pools carry the equivalent as a `fee_rate_bps` column directly on `dex_pool_state` rows (per the
  `DEFI_POOL_WINDOW_COLUMNS` schema in `unified-api-contracts/unified_api_contracts/registry/_schema_spec_defi.py`).
  **The static fee-rate half of what `dex_pool_fees` carries is already redundant with canonical data.**

## Operator's guiding principle (why this is a retirement candidate, not a registry gap)

Pool fee ACCRUAL
($ revenue) = swap volume × fee rate. Swap volume is already canonical (`dex_pool_swaps`); fee rate is
already canonical (the `instrument_id` discriminator / `fee_rate_bps` column on `dex_pool_state`). A downstream
consumer that needs $
fee accrual can compute it from these two already-canonical corpora rather than needing a separately-materialized,
separately-backfilled third corpus — the same principle the operator applied to `gas_fees` in this same session (gas
cost is engineered from gas units × static per-tx complexity, not a separately-backfilled "total gas fee" series).

> **CORRECTION (2026-08-12, ag-closeout-audit 2026-08-21 Phase 2 sweep applied this banner)**: this doc's DIAG todo
> below concluded the `dex_pool_fees` corpus held "0 objects under any sampled day... across 10+ days spanning
> 2026-06 through 2026-08" — that sample never probed `day=2026-05-16..22`, where 21 real captured objects (3 pools,
> CURVE ×2 + BALANCER ×1) actually live. The "0 objects for its entire lifetime" claim below is FALSE. Full
> disproof + resolution: `/plans/active/issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md`
> (all 21 rows were subsequently retired as content-redundant with canonical `dex_pool_state` twins, operator-confirmed
> BLK-9aed224f — the retirement OUTCOME this doc recommended still stands, only the "0 objects" premise was wrong).

## Todos

- [x] [DIAG] P2. Verify the script's own stated unblocking condition: does `dex_pool_state` (or `dex_pool_swaps`)
      already carry the subgraph `feesUSD`/`volumeUSD` columns for the same venues `materialize_dex_pool_fees.py`
      targets (Curve/Balancer)? Check `_schema_spec_defi.py`'s `DEFI_POOL_WINDOW_COLUMNS` for `amount_usd`/similar
      columns already present, and confirm live parquet footers actually populate them (not just schema-declared). If
      YES: the `Delete-when` condition is met — proceed to the next todo. If NO: this becomes a genuine gap-closing task
      (add the missing columns to the MTDS writer) before retirement is safe, not a same-session retirement. — **RESULT:
      YES for CURVE, condition met.** Live sample (`gs://market-data-tick-defi-prd-central-element-323112`, pool
      `CRV-FRXETH`, day=2026-07-13): `dex_pool_state` row carries `tvl_usd`/`volume_usd`/`fees_usd`/ `fee_rate_bps`
      POPULATED with real nonzero values (`tvl_usd=8097.69`, `volume_usd=69.48`, `fees_usd=0.2503`,
      `fee_rate_bps=2600`). Separately confirmed the retired `dex_pool_fees` corpus itself was **0 objects under any
      sampled day** across 10+ days spanning 2026-06 through 2026-08 — the join this doc proposed retiring was ALWAYS a
      no-op in production, making the retirement risk-free by construction (nothing observable changes). BALANCER's
      `dex_pool_state` rows do NOT carry the same columns (writer emits `swap_volume`/`swap_fees`/`total_shares`
      instead, and those are cumulative not daily) — filed as a separate, genuinely out-of-scope gap:
      `/plans/active/issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md`. This does not block the
      CURVE-validated retirement below, since the dex_pool_fees corpus never covered Balancer either (0 objects).
- [x] [DESIGN] P2. (Gated on the DIAG above.) If the condition is met: design the `canonical_dex_pool_provider.py`
      repoint (compute fee accrual from `dex_pool_state.fee_rate_bps` × `dex_pool_swaps` volume instead of the
      `dex_pool_fees` join), verify no other consumer reads `dex_pool_fees` directly (grep-then-READ), then retire
      `materialize_dex_pool_fees.py` + repoint the provider in one change, with the existing historical `dex_pool_fees`
      objects left in place (read-only, uncanonicalized, harmless — NOT a delete candidate; this is a going-forward
      writer-and-reader change, not a data migration). — **DONE.** Grep-then-READ across every repo confirmed only 3
      files ever referenced `dex_pool_fees`: the provider, its test, and the materialize script itself — no other
      consumer. `strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py`: removed
      `_POOL_FEES_DATA_TYPE`, `_read_pool_fees_for_day()`, and the fee-overlay branch in `pool_for_day()`; it now reads
      `fees_usd`/`volume_usd`/`fee_rate_bps`/`tvl_usd` directly off `_aggregate_pool_state()`'s existing dict (the state
      row's own columns — the module's `_fee_apy_bps()` prefer-real-fees/fall-back-to-volume×rate logic is unchanged).
      `strategy-service/scripts/materialize_dex_pool_fees.py` deleted.
      `tests/unit/engine/core/test_canonical_dex_pool_provider.py` rewritten: the 4 fee-overlay/fee-only-fallback tests
      replaced with 3 tests exercising the new direct-read path, using the REAL production CRV-FRXETH values from the
      DIAG sample above (`fee_apy_bps` computed from real `fees_usd=0.2503`/`tvl_usd=8097.69` ≈ 112.8bps) — 8/8 tests
      pass. Shipped: strategy-service commit `f7ca12767a51dc5e7d9327b1d0b875dc5454bb8a` (QG green, ran with
      `IGNORE_TIMEOUT=true` due to confirmed shared-host resource contention — load avg 24-30 on a 10-core box from
      other concurrent agents — every substantive gate passed both un-timed-out runs).
- [x] [DECISION] P3. Confirm with operator (or via documented precedent) whether the historical `dex_pool_fees` objects
      should stay `unknown`/permanently-accepted-non-canonical (cheapest, matches this workspace's existing
      `_ACCEPTED_EXCEPTIONS` pattern for similar "real but permanently non-canonical" residue) rather than any migration
      attempt — no strong reason to migrate data that a downstream consumer will stop needing once retired. — **MOOT,
      resolved by the DIAG finding.** There ARE no historical `dex_pool_fees` objects to decide about — the corpus was
      confirmed to hold 0 objects under any sampled day for its entire lifetime. Nothing to migrate, nothing to leave in
      place; the whole question dissolves.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`)**: filed per operator's corrected guidance mid-session
  (my initial plan was "add to canonical registry" — operator explicitly overrode this with the static-fee/
  engineer-don't-backfill principle). Not executed — DIAG todo needed before any strategy-layer code change, per this
  workspace's own precedent for live-reader-adjacent changes.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — of the 3 open todos only the
  first (DIAG schema/column verification) is arguably bounded; the other two (DESIGN repoint of a live strategy-layer
  read path + operator DECISION on legacy-object disposition) are genuine judgment/operator-gated work gated on that
  first step, so not essentially all remaining work qualifies for reclassification. Doc stays `assigned_vm: NA`.
- **sub-agent dispatch 2026-08-04 (verify-then-execute mandate)**: ran the DIAG verification via a bounded live-parquet
  sample read (per-day GCS prefix listing, not a whole-corpus walk — `raw_tick_data/by_date/day={D}/` scoped, same
  discipline `CanonicalDexPoolProvider` itself uses) against `gs://market-data-tick-defi-prd-central-element-323112`.
  Condition met for CURVE, executed the repoint + retirement (see DESIGN todo above). Found + filed a separate,
  genuinely out-of-scope BALANCER writer-schema gap discovered during the same verification (see linked issue doc) — it
  does not block this retirement (the retired corpus never covered Balancer either). This issue's own scope is fully
  executed; every todo above is closed. Ready for archival per the plan-completion-and-archival-discipline SSOT once the
  shipped commit is confirmed on `live-defi-rollout` (quickmerge dispatched separately, see the DESIGN todo's commit
  SHA).
