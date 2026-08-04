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
status: open
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
resolved_by:
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
`/plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`'s explicit decision to decline a
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

## Todos

- [ ] [DIAG] P2. Verify the script's own stated unblocking condition: does `dex_pool_state` (or `dex_pool_swaps`)
      already carry the subgraph `feesUSD`/`volumeUSD` columns for the same venues `materialize_dex_pool_fees.py`
      targets (Curve/Balancer)? Check `_schema_spec_defi.py`'s `DEFI_POOL_WINDOW_COLUMNS` for `amount_usd`/similar
      columns already present, and confirm live parquet footers actually populate them (not just schema-declared). If
      YES: the `Delete-when` condition is met — proceed to the next todo. If NO: this becomes a genuine gap-closing task
      (add the missing columns to the MTDS writer) before retirement is safe, not a same-session retirement.
- [ ] [DESIGN] P2. (Gated on the DIAG above.) If the condition is met: design the `canonical_dex_pool_provider.py`
      repoint (compute fee accrual from `dex_pool_state.fee_rate_bps` × `dex_pool_swaps` volume instead of the
      `dex_pool_fees` join), verify no other consumer reads `dex_pool_fees` directly (grep-then-READ), then retire
      `materialize_dex_pool_fees.py` + repoint the provider in one change, with the existing historical `dex_pool_fees`
      objects left in place (read-only, uncanonicalized, harmless — NOT a delete candidate; this is a going-forward
      writer-and-reader change, not a data migration).
- [ ] [DECISION] P3. Confirm with operator (or via documented precedent) whether the historical `dex_pool_fees` objects
      should stay `unknown`/permanently-accepted-non-canonical (cheapest, matches this workspace's existing
      `_ACCEPTED_EXCEPTIONS` pattern for similar "real but permanently non-canonical" residue) rather than any migration
      attempt — no strong reason to migrate data that a downstream consumer will stop needing once retired.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`)**: filed per operator's corrected guidance mid-session
  (my initial plan was "add to canonical registry" — operator explicitly overrode this with the static-fee/
  engineer-don't-backfill principle). Not executed — DIAG todo needed before any strategy-layer code change, per this
  workspace's own precedent for live-reader-adjacent changes.
