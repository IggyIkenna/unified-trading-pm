---
doc_type: plan
title:
  DeFi consolidated close-out — one ordered pass (canonical target → residual canon walk → denominator → coverage →
  forward) mirroring the cefi/tradfi close-outs
summary:
  Single coordination plan that AGGREGATES (references, does NOT duplicate) every open defi + defi-touching IS/MTDS
  plan/issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md /
  tradfi_consolidated_closeout_2026_07_18.md. Authored 2026-07-18 from a 6-agent audit (7 active defi plans + ~35 issues
  + live GCS bucket audit + live manifest distinct-values query) plus direct operator rulings. UNLIKE cefi/tradfi the
  DeFi FOUNDATIONAL migration already ran (canonical-migration-defi-20260618-180603 → v9 + asset_group=defi +
  pipeline_mode + source; dedicated→shared bucket consolidation done) — so what remains is a RESIDUAL canon walk, a
  now-RESOLVED POOL-id policy, a large genuinely-open coverage/denominator effort, a culled-venue purge, and restoring
  the removed data-status enumeration view. The operator-decided canonical target (id grammar, SPOT_ASSET vs SPOT_PAIR
  vs POOL, the two-id model, empty_confirmed vs out-of-scope) is captured here as the target; the actual code+data
  changes are THIS plan's scope (cefi/tradfi findings are passed to their sibling plans).
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    defi,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    pool,
    lending,
    spot-asset,
    manifest,
    empty-confirmed,
    denominator,
    coverage,
    backfill,
    bucket,
    enumeration,
    venue-purge,
  ]
related:
  [
    /plans/active/defi_strategy_pnl_axis_index_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    /plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    issues/estate_orphan_assessment_2026_07_21.md,
    issues/defi_five_never_captured_venues_fix_2026_07_22.md,
    issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md,
    issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md,
    issues/e2e_testing_collateral_validation_dead_import_2026_07_23.md,
    issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    archive/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md,
    archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
    issues/phantom_captures_defi_2026_06_28.md,
    issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md,
    issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: 2026-07-18
last_updated: "2026-08-18"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
depends_on: [defi_track01_per_instrument_and_canon_id_2026_07_24, defi_lending_writer_retire_prerequisite_2026_07_20]
gate_on_depends:
  true # Tracks 5/8 and the "Resume paused DeFi crons" items are repeatedly gated in prose on "Track 1"
  # (R1-R8, now forked out to defi_track01_per_instrument_and_canon_id_2026_07_24) and on the LENDING migration
  # prerequisite in defi_lending_writer_retire_prerequisite_2026_07_20 — real, un-machine-enforced cross-plan gates
  # found by the 2026-07-24 AO-flip-safety audit; encoded here so a future `assigned_vm: planning` flip can't dispatch
  # gated tracks before their real prerequisites land.
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  Operator, 2026-07-18 — after directing the cefi + tradfi consolidated close-outs, asked for the same one-pass DeFi
  close-out that aggregates ALL defi IS/MTDS plans+issues, audits the GCS buckets for the canonical path, states the
  canonical target (paths, instrument uids) from buckets+UAC+code+plans, defines the empty_confirmed vs out-of-scope
  basis, and reconciles SPOT_ASSET vs SPOT_PAIR vs POOL — reconciled in code AND backfilled data AND forward data.
  Authored + ground-truth-verified from a 6-agent audit (slot-4, 2026-07-18) with live GCS reads + operator rulings.
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /codex/02-data/honest-coverage-model.md,
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
  ]
---

# DeFi consolidated close-out — one pass to canonical, honestly-covered, forward-clean

> **Purpose.** ONE place that aggregates every open defi + defi-touching IS/MTDS plan/issue into a single ordered pass.
> This plan **references** the source docs; it does not duplicate them. Close a track by closing its source doc(s), then
> tick it here. Mirrors the cefi/tradfi consolidated close-outs. **Ownership (operator 2026-07-18)**: THIS plan is the
> target for the actual DeFi code + data changes; the audit's cefi/tradfi findings + operator decisions are passed to
> the two sibling plans.

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 3447 lines and forked 3 ways**, per the operator-approved split in
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 11: "Extract Strategy/PnL index + 1800-line
> historical log") plus an additional fork (Track 1) needed to actually land the doc under 1000 lines. Every todo and
> every Progress Log line was moved **verbatim** to its destination — nothing was summarized, rewritten, or silently
> dropped; every still-open item surfaced by the historical Progress Log's two "Deferred work after ..." tables was
> converted into a proper todo under "Open follow-ups" below rather than archived away.
>
> | Child doc                                                                                                                                                    | Carries                                                                                                                                                                                |
> | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | [`defi_strategy_pnl_axis_index_2026_07_24.md`](/plans/active/defi_strategy_pnl_axis_index_2026_07_24.md)                                                     | The **strategy/PnL/backtest-engine axis** (`strategy-service`) — a genuinely different set of tracks from this doc's data/canonicalization axis; entry point for that whole thread.    |
> | [`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)                             | The **per-instrument re-architecture (R1-R8)** + **Track 1 residual canon walk** — the single largest, most gating body of work (⛔ gates Half-B historical canonicalisation).         |
> | [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md) (archived, `status: complete`) | The 2026-07-18 canonical-target **contradiction-resolution audit** (75 findings, verbatim) + the full **chronological Progress Log** (2026-07-18 → 2026-07-23, ~2090 lines, verbatim). |
> | [`defi_track5_coverage_mvp_backfill_2026_07_24.md`](/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md)                                           | **Track 5 (COVERAGE)** — backfill to MVP-100%, incl. the MVP-universe gap-audit + the mvp-defi backlog unpark flipper note; C-GREEN gated on Track 1 → Track 3.                        |
> | [`defi_consolidated_closeout_aggregated_sources_2026_07_24.md`](/plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md)          | The **discoverability index** of every other defi-relevant plan/issue with its open-todo digest — read this to find a doc not directly linked from this plan.                          |
> | [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md) (`status: complete`)                   | **Track 6 (RENDER) + Track 7 (CULL)**, plus (2nd pass, 2026-07-25) every closed item from Tracks 2/3/4/8 + Open-follow-ups + the full 2026-07-24→2026-07-25 session Progress Log tail. |
>
> **Open-todo counts per child (2026-07-24, so a fresh session doesn't have to open each one to see what's live)**:
>
> - `defi_strategy_pnl_axis_index_2026_07_24.md` — **0 own top-level todos** (it's an entry-point index that references
>   other plans rather than carrying its own checkboxes; most of what it points to is already indexed in this doc's
>   "Aggregated source docs" § Strategy/PnL/backtest axis below).
> - `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — **13 open** (5 P0, 3 P1, 5 P2 — 11 plain-open + 2 `[~]`
>   partial; re-verified LIVE 2026-07-25 via `grep -c '^- \[ \]'` + the 2 partials, corrects the earlier stale "18 open
>   (6 P0, 7 P1, 5 P2)" count, which pre-dated several checkbox flips incl. both of that count's own cited "Top P0s" —
>   the legacy `dex_pools/`/`lending_indices/` fold and the legacy GLUED-VENUE flat-tree investigation are now BOTH
>   `[x]` done). Top P0s as of 2026-07-25: (1) the R3-run full-corpus per-instrument migration VM is still applying
>   (2022+ years + `rebuild_defi_manifest` remain, ~8-12h); (2) the catalogue-venue gap fix is SHIPPED but its
>   re-enum/re-rollup is DEPLOY-GATED, not yet run; (3) the ~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN Wave-D migration (code
>   done, data migration open); (4) the residual canon walk C2-C12 (6 sub-items, data-side read pending); (5)
>   eliminating the address/UUID fallback in `canonical_instrument_id` for POOL/LENDING (operator ruling 2026-07-21).
> - `defi_consolidated_closeout_history_2026_07_18.md` (archived) — **0 open todos**, confirmed via `grep -c '^- \[ \]'`
>   — it is a `status: complete` record doc (audit findings + historical Progress Log), not a live work tracker.
>
> **Retained here**: the Canonical target spec + Operator rulings (foundational context every fork depends on), Tracks
> 2-8 (the remaining open work), the "Open follow-ups" list (every still-open item recovered from the historical
> Progress Log's deferred-work tables), the aggregated source-doc index, and a condensed pointer replacing the full
> tick-by-tick Progress Log (see the archive doc for full historical detail).

## Headline verdict — how DeFi differs from cefi/tradfi

- **The DeFi FOUNDATIONAL migration already ran.** `canonical-migration-defi-20260618-180603` (C0d in
  `data_completion_defi_2026_07_15.md`) took every DeFi object to v9 + `asset_group=defi` + `pipeline_mode=` + a
  `source` column; the dedicated→shared bucket consolidation (`defi_dedicated_bucket_shared_migration_2026_07_13.md`) is
  done (all kinds resolve `kind="tick-data"` on the single `market-data-tick-defi-prd-central-element-323112`). So the
  cefi/tradfi "0% canonical, migrate everything" starting point does NOT apply.
- **What remains is different in kind:** (1) a RESIDUAL canon walk the big migration didn't finish (C2–C12); (2) a
  now-RESOLVED POOL-id policy contradiction; (3) a culled-venue purge; (4) a large genuinely-open coverage/denominator
  effort (the ~63.9M `expected_unattempted` seed, the DRIFT/Velocity backfill, Morpho never wired, a dead Curve/Optimism
  subgraph); (5) restoring the removed data-status "what exists" enumeration view. DeFi's biggest open track is
  **coverage**, not id-canonicalisation.

## Strategy/PnL/backtest-side DeFi tracking — SECOND axis, moved out 2026-07-24

> This doc's scope (below) is the DeFi **data/canonicalization** axis (IS/MTDS-touching) only. The **strategy/PnL/
> backtest engine** axis (`strategy-service`) — a genuinely different set of tracks (LST rate coverage, DeFi interest
> PnL correctness, the orphaned-archetype tick-builder wiring program, collateral-validation dead-import) — now has its
> own entry-point index:
> **[`defi_strategy_pnl_axis_index_2026_07_24.md`](/plans/active/defi_strategy_pnl_axis_index_2026_07_24.md)**. Both
> plans are parallel, not sequential — a fresh session should read both to pick up all open DeFi work.

## Per-instrument re-architecture + Track 1 — CANON (instrument-ID canonicalization)

> **Forked out 2026-07-24** (line-cap remediation) to
> [`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)
> — the single largest, most gating body of work in this close-out (⛔ gates Half-B historical canonicalisation). Read
> that plan for the R1-R8 per-instrument writer re-architecture + the full Track 1 residual canon walk. The Canonical
> target spec + Operator decisions immediately below are the shared context both this fork and Tracks 2-8 depend on.

### Track 1 roll-up todo — factory-address capture gap (206,107 bare-venue rows)

- **[DATA] P2. DECISION DONE + EXECUTION EXTRACTED 2026-08-09 — no longer a checkbox here, per this entry's own "Close
  both together" instruction.** Land factory-address capture + register the missing UAC SushiSwap-Arbitrum venues — the
  bare `SUSHISWAP`/`UNISWAP` venue-version resolver shipped (`_dex_factory_registry.py`) but measured **resolved=0 /
  residual=206,107 (100%)** against the live prod manifest on 2026-07-21. The Option A-vs-B fork is now RULED (operator,
  2026-08-08): option (b), on-chain RPC `factory()` lookup — bounded, no live-schema-probe risk, scope explicitly
  extended to also migrate the 206,107-row historical residual (not just forward capture). The Track-1 roll-up decision
  todo itself is `[x]` DONE in
  [`/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)
  (the `[DATA] P2` "NEW 2026-07-21 — actually start capturing factory addresses" todo, citing the ruling verbatim). The
  resulting EXECUTION work (RPC `factory()` lookup, UAC venue registration, historical GCS/manifest migration + purge)
  was itself further extracted 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md` (`[SCRIPT] P1`,
  assigned_vm: planning, active) — that is the live dispatch path, not a second copy here. Source:
  [`/plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`](/plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md)
  (measured-residual table + full Option A/B writeup; that issue doc's own sole checkbox is a KEEP_NA_STALE_DUPLICATE of
  the same batch11 item, per na-eligibility-audit 2026-08-09).

## Canonical target (operator-decided 2026-07-18 — the thing we converge all four surfaces on)

The four surfaces that must agree post-migration: **(1) GCS parquet path**, **(2) parquet
`instrument_id`/`canonical_instrument_id` columns**, **(3) manifest `_index` key**, **(4) data-status render**. For DeFi
**TARGET (operator 2026-07-18): DeFi is FLAT-PER-INSTRUMENT** — one parquet per instrument, filename = the symbolic
canonical id (`filename == instrument_id == manifest key`), exactly like cefi/tradfi. The old multi-instrument
capture-batch (`{venue}_{CHAIN}_{capture_ts}.parquet`) model is **RETIRED** — see the "Per-instrument re-architecture"
section above. The address stays a content column + the IS-definition/join key.

### Path template (operator-locked; forward writer already emits it)

```
gs://market-data-tick-defi-{prd|test}-central-element-323112/raw_tick_data/by_date/day={YYYY-MM-DD}/
  pipeline_mode={mode}_{source}/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/
  instrument_type={itype_lower}/data_type={dt}/{leaf}.parquet
```

Segment order is **venue BEFORE chain** (locked in `/codex/02-data/defi-canonical-naming-ssot.md`; the code + live GCS
confirm it). `instrument_type` in the PATH is lowercase.

> **CORRECTED 2026-08-12 (/plan-reconcile)**: the prior claim that `per-asset-group-bucket-layouts.md` and
> `GCS_PATHS.md` were "STALE the other way" is itself now stale. `GCS_PATHS.md` does not exist in `codex/`
> (`find codex -iname GCS_PATHS.md` → no hits; likely renamed/consolidated). `per-asset-group-bucket-layouts.md:143`
> already states the canonical DeFi path as `venue={v}/chain={chain}` (venue before chain), explicitly noting the
> chain-before-venue form is legacy/coexisting-during-migration, not canonical — it agrees with this doc, not
> contradicts it. No further codex correction needed; this doc's own 3+-week-unresolved flag can be dropped.

### Instrument-uid grammar per DeFi type (real `build_canonical_instrument_id` output; UPPER type-segment, case-PRESERVED symbol)

Base = `VENUE-CHAIN:TYPE:SYMBOL` (DeFi is the only AG whose venue segment carries a `-CHAIN` suffix; on-chain token case
is preserved — `aUSDC`, `stETH`).

| type                                                                                                                                                     | grammar                                                                                                        | example                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `SPOT_ASSET`                                                                                                                                             | `VENUE-CHAIN:SPOT_ASSET:SYM`                                                                                   | `UNISWAP_V3-ETHEREUM:SPOT_ASSET:WETH`                                           |
| `POOL`                                                                                                                                                   | `VENUE-CHAIN:POOL:TOKEN0-TOKEN1[-FEE_BPS]` — **3-segment, fee INSIDE the symbol (operator ruling 2026-07-18)** | `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`                                        |
| `A_TOKEN` / `DEBT_TOKEN`                                                                                                                                 | supply / borrow leg (isolated markets append `marketId[:8]`)                                                   | `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC` · `MORPHO-BASE:A_TOKEN:AUSDC-EURC-<marketId8>` |
| `LST` / `YIELD_BEARING` / `STAKING`                                                                                                                      | staking token / vault share                                                                                    | `LIDO-ETHEREUM:LST:stETH` · `ETHENA-ETHEREUM:YIELD_BEARING:sUSDe`               |
| `PERPETUAL` (on-chain, DeFi lane — GMX was the example venue, **REMOVED 2026-07-25**, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) | `VENUE:PERPETUAL:SYM` — **NO chain suffix** (routes cefi-simple branch)                                        | `GMX:PERPETUAL:BTC-USD` (historical example; venue removed)                     |
| `SOLANA_AMM_POOL` / `SOLANA_LENDING`                                                                                                                     | Solana grains                                                                                                  | `ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC`                                          |

### The two-id model (operator ruling 2026-07-18 — "that's fine as long as downstream uses what it needs the right way")

Every address-identified DeFi row carries TWO ids and this is INTENTIONAL — **do NOT mass-rewrite the 22.3M
address-keyed rows**:

- **`canonical_instrument_id` (the canonical/human id)** = the symbolic `VENUE-CHAIN:TYPE:SYMBOL` above. Carries the
  instrument_type; carries NO raw addresses. This is the operator's "type-in-id, symbol-in-id, addresses live in the
  definition" ruling.
- **`instrument_id` (the machine/operational key)** = the address-anchored form (POOL→`pool_address.lower()`,
  SPOT_ASSET→`spot_asset:{chain}:{token_addr}`). Used as the manifest join key + MTDS content-join. The pool/token
  CONTRACT ADDRESS lives HERE and in the instrument DEFINITION (catalogue) — NEVER inside the canonical id.
- **POOL-id policy = Option A (test wins)**: POOL rows legitimately DIVERGE (`instrument_id`=address,
  `canonical_instrument_id`=symbolic key). For SPOT_ASSET the two CONVERGE by construction. Fix the backfill-script
  docstring that wrongly asserts convergence "pool or not"; ensure every consumer reads the RIGHT one (join→address,
  display/canonical→symbolic).

### SPOT_ASSET vs SPOT_PAIR vs POOL — the decision rule

1. CeFi order-book two-token quoted market (or any two-token quoted price) → **`SPOT_PAIR`** (asset_group=cefi, no
   chain).
2. A single on-chain token you want oracle-price / transfers / gas / bridge / gov / MEV data for → **`SPOT_ASSET`**
   (defi, address-keyed; `canonical_instrument_id := instrument_id` so the two CONVERGE). Carries the
   `DEFI_SPOT_ASSET_*` data_types.
3. An AMM/DEX liquidity-pool contract (two legs + fee + pool address) → **`POOL`** (defi, pool-address-keyed; DIVERGE).
   Its two legs are each individually a `SPOT_ASSET`; the pool is a distinct instrument. Solana spot-DEX
   orderbook/quote/per-swap shards use **`DEX_POOL`**/`SOLANA_AMM_POOL`.

### Lending — ONE SSOT (operator ruling 2026-07-18)

`A_TOKEN` (supply) + `DEBT_TOKEN` (borrow) IS the canonical split (net_value = supply − borrow needs both legs). The
legacy flat **`LENDING`** type is retired: its ~16.7M enumerated rows migrate to the split, and the split is baked into
`build_instrument_catalogue.py` row-construction (not a catalog-only patch a `--mode full` rebuild reverts). The
enumeration audit's stray "fold a_token→lending" is BACKWARD — a_token/debt_token are canonical; `lending` migrates.

### empty_confirmed vs out-of-scope (the denominator basis)

Discriminator = **does a manifest row exist**.

- **`empty_confirmed`** — a cell INSIDE the could-exist universe, attempted, source PROVABLY returned 0 rows (typed
  `EmptyConfirmedReason` + `FetchEvidence` or UTL hard-raises `UnprovenHonestAbsenceError`). A materialized row
  (`row_count=0`, blank id). **EXCLUDED from `reachable_coverage`, RETAINED in `all_shards`.** Stays visible. DeFi-legit
  reasons only: `EXPECTED_PRE_GENESIS_CHAIN`, `EXPECTED_PRE_VENUE_LAUNCH`, `EXPECTED_PROTOCOL_PAUSED`,
  `EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED`, `SOURCE_RETURNED_ZERO`, proposed `EXPECTED_SUBGRAPH_DEINDEXED`
  (Curve/Optimism). An instrument-day source-zero on an ALIVE day = `attempted_failed`, NOT silent empty.
- **out-of-scope** — a `(venue, itype, data_type)` tuple that should NEVER generate → **NO manifest row**
  (`ExpectedState.NOT_IN_SCOPE` / `is_valid_shard_key=False` / `is_mvp()=False`). **Clipped from BOTH numerator and
  denominator.** Removed venues leave the registries entirely.
- **The trap (why the denominator lies today):** ~63.9M could-exist cells were never materialized as
  `expected_unattempted` by the writer → no row → they silently masquerade as out-of-scope and UNDERSTATE the
  denominator. Honest only after a fresh single-walk seeds them (gated on the phantom+duplicate purge first).

## Operator decisions applied (2026-07-18)

- **POOL canonical key = 3-segment, fee inside symbol** (`UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`) — the
  `canonical_id_builder` SSOT form, not the 4-segment `DefiPoolIdentity.glued_pair_id` (`…:POOL:USDC-WETH:500`). The
  4-segment form is retired.
- **Two-id model kept** (Option A) — no mass address→symbol rewrite; ensure symbolic `canonical_instrument_id` coexists
  on every row + downstream reads the right id.
- ~~**Retire legacy `LENDING`** → migrate ~16.7M rows to the A_TOKEN/DEBT_TOKEN split + bake into the catalogue
  builder.~~ **SUPERSEDED (session-3, 2026-07-26)** — WON'T-DO; flat `LENDING`/`SOLANA_LENDING` is now permanent for
  market/event lending, replaced by the `resolve_lending_underlying` read-side resolver. See
  `defi_lending_writer_retire_prerequisite_2026_07_20.md` session-3 entry +
  `/codex/02-data/defi-canonical-naming-ssot.md`.
- **instrument_type case**: **⛔ corrected 2026-07-20, operator ruling D1 — ~~"lowercase in the PATH + manifest COLUMN
  (writer grain), UPPER stays only in the id SEGMENT"~~.** Three separate legs: manifest **COLUMN → UPPERCASE**
  (catalogue wins, ruling D1) · GCS **path segment → lowercase** (unchanged) · **id middle segment → UPPER**
  (unchanged). Do not bundle path and column into one case. SSOT: `/codex/02-data/cross-asset-canonical-target-ssot.md`
  §7. **⛔ FURTHER REFINED 2026-08-02 fold-in, operator directive 2026-07-24
  (`/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) — the
  blanket-manifest-COLUMN-UPPERCASE framing above does NOT apply to DeFi.** DeFi's corpus was separately flagged as
  genuinely mixed (not close-to-one-direction), so its manifest-COLUMN casing is decided PER `instrument_type` value on
  a least-migration-cost basis (whichever casing is already dominant for that value wins; the minority migrates to
  match) — DeFi is the sole asset_group with this per-value freedom, the other four (tradfi/cefi/prediction/sports)
  target uniform UPPERCASE. **RESOLVED as a no-op 2026-07-24**:
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s "Manifest instrument_type case + venue-spelling unify" todo
  ran the required per-value census live and found every one of the 11 live `instrument_type` values already 100% one
  casing — lowercase, zero uppercase rows anywhere — so no migration was needed; that casing IS the ratified target now.
  The GCS path segment (lowercase) and id middle segment (UPPER) legs remain unchanged by any of this.
- **Culled-venue purge = dead-only, snapshot-first, keep LIGHTER + EXTENDED** (see Track 7).
- **Combos = leg-aware signed-weight spec** (cross-AG) — see Track 1 + the cefi/tradfi hand-offs.
- **Restore the removed data-status enumeration** (raw distinct-values audit view) — Track 6.

---

## Track 2 — STORE: path authority + bucket hygiene (⛔ flat-vs-hive must be pinned) · P0

- **Sources**: `defi_dedicated_bucket_shared_migration_2026_07_13.md` (2 open P2/P3 + C0f),
  `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`,
  `issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md`,
  `issues/features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15.md`,
  `/plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`,
  `issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md`.
- **Close-out criterion**: one pinned path shape; zero dedicated-bucket refs; TF state matches live estate;
  lending-indices legacy bucket deleted (snapshot-first).

> **⛔ corrected 2026-07-20 — the DELETE clause in the first todo below is STALE and executing it DESTROYS DATA.
> Disposition is now FOLD-not-delete.** The "dead prefixes" premise was **overturned by R5 in this same plan**
> (`:254-262`) — content-verify found PARTIAL-OVERLAP, not duplication: legacy=98 pools, canon=99, **intersection only
> 66**, with **32 legacy-only high-TVL raydium pools ABSENT from canon** (XMR/USDC $47M, BNB/USDC $18M, USD1/USDC
> $9.9M,
> ZEC/USDC $7.5M). A live GCS probe on 2026-07-20 corroborates and sharpens this: on `day=2026-04-14` the
> canonical twin **does** exist for ORCA (14,094 objs) / RAYDIUM (100 objs) / KAMINO lending_indices (47 objs) under
> `instrument_type=solana_amm_pool`, but **KAMINO `dex_pool_state` = 0 and SOLEND = 0** — for those two cells the legacy
> objects are the **only copy in existence**. A snapshot-first delete is NOT adequate protection. **Required order: (1)
> content-UNION the 32 legacy-only pools + the 2 twin-less cells into canon; (2) repoint
> `execution-service/execution_service/providers/solana_amm_depth_provider.py:41` — which STILL READS this legacy shape
> at runtime — to the canonical `data_type=dex_pool_state` path AND fix its broken `resolve_bucket_name` call at
> `:248-254` (`kind="market-data-tick-defi"` is a bucket-name FRAGMENT with no yaml key, and `env=`/`project_id=` are
> not parameters, so it RAISES uncaught); (3) ONLY THEN consider the delete.** Full evidence + resolution criteria:
> `/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`.

> **2 closed items extracted 2026-07-25** (line-cap remediation, 2nd pass) — the path-shape-pin code fix (dexpool
> writer-order bug) + the stale-codex-docs correction, both done; full text verbatim in
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

- **[DATA] P1. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Retagged from `[OPERATOR]`
  (2026-07-28 gate-cleanup pass) — operator ruling 2026-07-28
  (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, extended): whole-bucket destroys are now
  reversibility-qualified the same way plain object deletes already were, PROVIDED a fresh
  `gcs_bucket_soft_delete_retention_seconds()` check on the target bucket clears (>=604800s) — the "never
  reversibility-qualified regardless of soft-delete config" line below is now stale/historical, superseded by this
  ruling. **Delete the lending-indices legacy bucket (C0f)** + resolve TF estate drift
  (`market_data_defi_lending_indices_prd` still declared) + the bare `features-onchain` vs asset-group bucket.
  **Dispatch as**: run a FRESH `gcs_bucket_soft_delete_retention_seconds(bucket)` check on the target bucket right now
  and cite the actual returned value; if >=604800s, execute the bucket delete via the sanctioned UTL helpers per §3a —
  no operator step needed. If <604800s (or the check errors), this stays gated — fall back to §3a's approve-executes
  flow: stage the exact command + snapshot evidence, open a structured BLOCKED question recommending "approve — execute
  now"; a FINAL operator answer then authorizes the SAME worker session to run it immediately (no second agent, no
  manual operator execution) — not the old "an agent must never run it, a human runs it separately" framing. (repos:
  deployment-service, market-tick-data-service)
- [x] [BACKEND] P0. **NEW 2026-07-24 — `write_defi_rows()` writes the bare SYMBOL as the filename leaf, not the ruled
      canonical_instrument_id, AND DeFi batch capture is actively writing (NOT stopped as the codex/plan text assumes) —
      so this is a growing defect, not frozen residue.** 13/13 sampled objects fail the UAC id-form oracle
      (`canonical_path_violations`, `_ID_FORM_CHECKED_ASSET_GROUPS={cefi,defi}`); `canonical-cutover-register.md` §5 +
      `defi-canonical-naming-ssot.md`'s WRITE-MODEL banner both incorrectly state capture is fully stopped — measured
      new objects with `time_created=2026-07-24` (same day as probe). Full evidence + repro:
      `/plans/archive/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`.
      **Done when** a fresh `canonical_path_violations()` id-form sample against `write_defi_rows()` output across a
      multi-day window returns 0 violations. (repos: market-tick-data-service, unified-api-contracts,
      unified-trading-pm) — DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
      defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 36 for full evidence: fixed via a new colon-preserving
      sanitizer (`_sanitize_defi_instrument_id_leaf`) so filename stem == the `instrument_id` column == the manifest
      key; shipped `market-tick-data-service@0fddb95e`, `quality-gates.sh` green.

## Track 3 — DENOM: empty_confirmed / denominator honesty · P1

- **Sources**: `/plans/archive/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (measured 63.9M via the v2 enumerator),
  `issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md`, `defi-completeness-oracle.md`,
  `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`,
  `issues/defi_catalogue_available_to_false_delisting_2026_07_20.md`.
- **Close-out criterion**: fresh single-walk yields zero silent-`M` rows; denominator honest.

- [ ] [DATA] P0. **PURGE first, then seed.** **[OPERATOR] delete-safety note (plan_reconciler 2026-08-18,
      re-flagging na-eligibility-audit 2026-08-16's "worth a follow-up look")**: this todo performs a real prod-GCS
      purge (1.79M duplicate + ~219.5K phantom rows) before an AO worker may execute it — unlike its sibling delete
      todo below (line ~681, which cites a verified 7-day soft-delete retention as its safe-idempotent
      justification), this todo has neither an operator sign-off nor a delete-safety-protocol citation yet. Get one
      of the two (`[OPERATOR]` sign-off + `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a citation,
      OR an equivalent stated safe-idempotent justification) before dispatching. Purge the 1.79M duplicate + ~219.5K
      phantom rows (re-verify the 219,529
      detected vs 219,632 flipped delta), THEN apply the ~63.9M `expected_unattempted` seed (operator write-volume gate;
      incl. 812,055 solana-pool-vocab rows + 215,864 non-POOL EU rows). The "1M" framing is the old safety-cap slug —
      the real target is 63.9M. **Sequence AFTER the glued-id manifest rebuild** (both touch the same consolidated
      index). **Re-verify `spot_pair`/`spot_asset` counts against the CURRENT catalogue before applying** — the 63.9M
      figure (incl. `spot_pair` 143K) was measured 2026-07-10 against a catalogue snapshot that predates the 2026-07-16
      SPOT_ASSET population backfill + the 2026-07-21 reference-only reclassification; live re-measurement 2026-07-24
      shows catalogue SPOT_ASSET=1,390 (well-populated, 17 venues, 0 DRIFT) and catalogue SPOT_PAIR=56
      (CHAINLINK/PYTH/EIGENLAYER only, 0 DRIFT) with 0 `spot_pair` rows in the live consolidated manifest index — the
      143K figure is stale/never-applied, not a live target. (repos: market-tick-data-service)
- [x] ✅ [BACKEND] P1. **Add the `EXPECTED_SUBGRAPH_DEINDEXED` reason** to reclassify the 952 false Curve/Optimism
      `attempted_failed` → honest-empty; reconcile `spot_asset` absence from the enumerated catalogue (the v2 corpus
      predates SPOT_ASSET population; `spot_pair` 143K is partly the culled DRIFT SPOT leak). **All 4 sub-items now
      DONE** (repos: unified-api-contracts, instruments-service) — **DONE (na-eligibility-audit 2026-08-03)**: the
      `--apply` sub-item below (previously the sole pending piece) shipped via
      `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md`'s Todo 1 (DONE 2026-07-28, slot-13) —
      see that todo + this doc's own nested `--apply` checkbox below for the evidence.
  - [x] Reason SHIPPED `unified-api-contracts@e893e5c9`.
  - [x] Reclassification script SHIPPED `instruments-service@73100d4e`
        (`scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`), dry-run verified against live prod
        — found **144** matching rows today, not 952 (count shrank over the 9 intervening days of pipeline activity). A
        bug in the first script version (matching the full 45-char subgraph id) initially found 0 because the manifest's
        `error_reason` column truncates at 80 chars; fixed to match the untruncated message prefix, then confirmed
        against an independent raw pandas count of the same 144 rows.
  - [x] ✅ `--apply` **DONE (na-eligibility-audit 2026-08-03)** —
        `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md`'s Todo 1 (DONE 2026-07-28, slot-13):
        fixed the `cd` bug (see the follow-up item below, also closed by the same evidence), then ran the `--apply` on a
        fresh `e2-highmem-16` VM (`canonical-migration-defi-curve-optm-reclass-20260728-061053`, exit_code=0):
        reclassified **420** rows total (346 in `_index/availability_index.parquet` + 74 in a per-VM shard), backups
        preserved. Post-run manifest spot-check confirmed `EXPECTED_SUBGRAPH_DEINDEXED` CURVE/OPTIMISM rows = 346
        (matches the log) and rows still `attempted_failed` matching the dead-subgraph cascade signature = 0. **Was**:
        NOT YET RUN — 2 VM-launch attempts 2026-07-24 both FAILED differently; stopped (stall-safety) rather than
        blind-retry a 3rd time. **Attempt 1** rc=2 file-not-found — root cause: `setup-data-pipeline-vm.sh`'s
        `canonical-migration` branch (`:1187`) hardcodes `cd "$WORKSPACE/mtds"` regardless of `VM_SERVICE`, so this
        instruments-service script can't be found; a real launcher bug (new follow-up below), not user error. **Attempt
        2** (workaround: `bash -c 'cd .../instruments && python ...'`): `run.log` never got created at all — likely the
        nested quoting breaking the startup script's own `python`→venv-python substitution. Full detail:
        `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`.
- [x] ✅ [INFRA] P2. **NEW 2026-07-24 — fix the `canonical-migration` `VM_TASK` mtds-hardcoded `cd` bug** found above
      (the canonical-migration `VM_TASK` case branch's hardcoded `cd` path in `setup-data-pipeline-vm.sh`) — mirror the
      `VM_SERVICE`-keyed instruments branch other cases already use. (repo: deployment-service) **na-eligibility-audit
      2026-08-01: already claimed elsewhere — this exact fix is IN PROGRESS in
      `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md`'s Track-1 Progress Log (2026-07-26/27,
      slot-4): code-complete, blocked on shipping by a shared-host `pytest` I/O stall, not abandoned. Not re-drafted;
      stays here pending that plan's own completion — check there first before starting fresh work on this item.**
      **DONE (na-eligibility-audit 2026-08-03)** —
      `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md`'s Progress Log (2026-07-28, slot-13):
      confirmed ALREADY SHIPPED on `live-defi-rollout` (`deployment-service@0ed2ca6`, "derive canonical-migration
      workspace dir from VM_SERVICE") — a different slot landed it after the shared-host stall above; independently
      re-verified rather than assumed.
  - [x] `spot_asset`/`spot_pair` reconciliation investigated + resolved via live re-measurement (see the P0 item's
        footnote above) — both were stale/non-issues, not a coding task.

> **2 closed items extracted 2026-07-25** (line-cap remediation, 2nd pass) — the `available_to` false-delisting fix
>
> - the non-POOL EU terminal-state decision, both done; full text verbatim in
>   [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

## Track 4 — CAP: zero-capture protocols · P2

- **Sources**: `mtds_defi_dex_zero_capture_protocols_2026_07_14.md` (folded in + archived 2026-07-21, consolidation pass
  — all 6 wiring todos shipped incl. an 8/8-shard-combo smoke test; 2 residual todos folded below),
  `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`,
  `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`.
- **Close-out criterion**: every MVP protocol/data_type captures or is honestly `empty_confirmed`.

- [ ] [BACKEND] P2. **Wire the remaining zero-capture protocols** (uniswap_v2/v4, trader_joe_v2, velodrome_v2 DONE —
      wired + smoke-tested 2026-07-14; Morpho lending indices — **CORRECTED 2026-08-12 (/plan-reconcile): wired
      2026-07-12** per `issues/defi_morpho_lending_indices_never_wired_2026_07_12.md` (live production evidence,
      independently re-verified through 2026-08-09; only 1 open todo remains there — re-run the
      `mvp_backfill_defi_onchain_v10` G2 gate — not a zero-capture protocol anymore); Solana ORCA/RAYDIUM swap indexer
      as a new capability — still open per the sibling issue). (repos: market-tick-data-service)

> **2 closed items extracted 2026-07-25** (line-cap remediation, 2nd pass) — the OOM-crash-loop-fixed coverage
> verification + the protocol-dispatch-list codex audit, both done; full text verbatim in
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

## Track 5 — COVERAGE: backfill → MVP-100% — FORKED 2026-07-24

**Forked verbatim to
[`defi_track5_coverage_mvp_backfill_2026_07_24.md`](/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md)**
(the prose-only "C-GREEN gated on T1→T3" dependency is now a real `depends_on` + `gate_on_depends: true` on that child,
per task_template.md finding I — the SAME edit that forked this section). Includes the MVP-universe §14 gap-audit
sub-section and the mvp-defi backlog unpark flipper note, moved there unedited. Track this track's progress in that
file, not here.

## Track 6 — RENDER: data-status surface #4 + RESTORE the enumeration view · P1 — CLOSED, extracted 2026-07-25

> **Both todos in this track are done, extracted verbatim (line-cap remediation) to**
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md):
> (1) `instruments-service@64a58cc1`+`deployment-api@0d2f6e6`+`deployment-ui@4afcfd8` — restored the
> `GET /api/data-status/distinct-values/{asset_group}` enumeration view; (2) `deployment-api@427ede5`+
> `deployment-ui@83ec561` — fixed the turbo-API HYPERLIQUID/ASTER hide bug + pruned the capability-bundle DRIFT residue.
> **Close-out criterion note (kept live here, not archived)**: the doc's own criterion is NOT fully met yet — a fresh
> distinct-values census must return zero `is_canonical=false` entries; that drive-to-0 work is tracked in
> `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, not as its own todo here or in the history child.

## Track 7 — CULL: purge the removed venues everywhere (dead-only, snapshot-first) · P1 — CLOSED, extracted 2026-07-25

> **The 1 todo in this track is done, extracted verbatim (line-cap remediation) to**
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md)
> — `market-tick-data-service@f6176e8b` purged the culled Solana-perp venues' DeFi-side residue (architecture_v2 leg
> specs already dropped, `mvp-scope-canonical.md` already fixed, one genuine residue script deleted); the operator
> ruling (KEEP `KALSHI-PERP`/`POLYMARKET-PERP`/`LIGHTER-ZKSYNC`/`EXTENDED-STARKNET`, cull everything else, GCS deletes
> snapshot-first) and the load-bearing exclusions (`DECOMMISSIONED_VENUE_BASES`, `QUARANTINE_REGISTRY`, the DRIFT
> token-ticker, 2 historical migration-utility mappings) are preserved verbatim in the history child, not repeated here.

## Track 8 — INFRA / forward-data: resume steady-state (⛔ for forward honesty) · P1

- **Sources**: `issues/defi_scheduled_collection_outage_paused_crons_2026_07_16.md` (11 collect + 3 fwd crons paused
  since 2026-06-08), `issues/defi_consolidator_cron_left_paused_2026_07_15.md`,
  `issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`,
  `archive/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`,
  `issues/defi_code_codex_drift_2026_05_27.md`.
- **Close-out criterion**: forward crons running; consolidator race/pause fixed; codex↔code drift closed.

> **⛔ correction 2026-07-22 (scoping-only sub-agent, read-only `gcloud scheduler jobs list/describe`
> `central-element-323112`/`asia-northeast1`, nothing written/resumed) — the "11 collect + 3 forward, all paused"
> framing below is IMPRECISE.** Actual live state: only **4 of the 11** `uts-prod-mtds-collect-*` daily-batch crons are
> PAUSED (`dex-pools`, `oracle-prices`, `evm-defi`, `solana-defi` — all 4
> `userUpdateTime=2026-07-18T19:15:2[6-9|31|34|36]Z`, one coordinated action matching the "re-armed 2026-07-18"
> per-instrument-refactor banner above, `:114-121`, even though that banner's prose names only 2 of the 4). The other
> **7 are ENABLED and running today** (`perp-funding`, `gas-fees`, `dex-swaps`, `lending-indices`, `lst-rates`,
> `liquidations`, `eigenlayer-rewards`) — safe, because the forward per-instrument writer fix (R1, `mtds@4ca2640d`)
> already shards every one of them by real `instrument_id` (0 new glued objects across 8 consecutive live days — see the
> deferred-work table's "Forward write-path fix" row). All **3** `defi-fwd-*` live-poll crons remain PAUSED. **Net: 7
> schedulers paused, not 14** — a scoped pause on exactly the data types (dex_pools/oracle_prices/evm_defi/solana_defi)
> the still-RUNNING `canonical-migration-defi-per-instrument-*` VM is migrating, not a blanket outage. The manifest
> consolidator (`uts-prod-manifest-consolidator-market-data-defi-cron` + `instruments-defi`/`features-defi`) is ENABLED,
> running every 1 minute, unaffected. Of this todo's own close-out criterion: **consolidator duplicate-race is CLOSED
> (2026-07-10)** and **scheduler SIGKILL is RESOLVED (2026-07-14/15)** — both archived
> (`plans/archive/issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md`,
> `plans/archive/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`); only "right-size the
> honest-coverage nightly" and the codex↔code drift doc remain open (both `status: open` as of this check). Full
> derivation: this plan's Progress Log, 2026-07-22 sub-agent entry.

- [ ] [INFRA] P1. **Resume the paused DeFi crons NOT scoped to `dex_pool_state`** (oracle-prices, evm-defi, solana-defi
      collectors + their forward-poll counterparts — of the 4 collect + 3 forward = 7 schedulers currently paused per
      the correction above, this is every one EXCEPT the dex-pools-scoped collect + forward-poll pair split into the
      next todo) AFTER Track-1/2 land so they write the canonical shape; fix the consolidator duplicate-race + SIGKILL
      (**both already CLOSED, see correction above** — only the honest-coverage nightly right-size + codex-drift-doc
      sub-clauses remain). **UPDATE 2026-08-03 (finalize task, slot-2 review craft): the honest-coverage-nightly
      right-size sub-clause is now DONE**, closed by
      `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md`'s todos 2-3 — the `_compute_coverage`
      per-asset_group streaming refactor (`instruments-service@12825e81`) plus the machine-type downsize verified
      holding on `e2-standard-4` (16GB) with zero OOM across a live control-vs-test comparison
      (`deployment-service@fec7946`/`d880de3`). This todo itself (the cron-resume action) stays OPEN — still gated on
      Track-1/2 + the migration-VM finishing, as below; only the right-size sub-clause is closed. The codex-drift-doc
      sub-clause remains open. **Because live=batch, no live-only DeFi data_type needs separate reconciliation** — the
      forward writer is already canonical (Half-A done); the open work is Half-B (migrate the historical corpus) then
      resume forward. Do not resume before the currently-running per-instrument migration VM finishes (it is actively
      migrating exactly the 4 paused collectors' data types — resuming now races live writes against it).
      `uts-prod-mtds-collect-solana-defi-cron` needed the Solana AMM symbol-collision fix before resuming — **the fix
      has since SHIPPED** (`market-tick-data-service@0d83a8a9`, ancestor of `origin/live-defi-rollout`; see the
      Solana-symbol-collision item above), so this specific pre-resume condition is now satisfied; the cron still waits
      on the Track-1/2 + migration-VM gates above like the rest. (repos: deployment-service, market-tick-data-service)
- [ ] [INFRA] P1. **Resume the `dex_pool_state` collect + forward-poll schedulers ONLY AFTER
      `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` lands** (operator ruling
      2026-07-25, task_template.md finding P) — these serve TRADER_JOE_V2/VELODROME_V2/CURVE, the exact venues that
      plan's subgraph-query-missing-`inputTokens{symbol}` fix targets; resuming before it ships would resume writing the
      same symbol-less rows that plan exists to stop. Same Track-1/2 + migration-VM gates as the item above ALSO apply
      here — this is an additional gate, not a replacement. A 2026-07-23 GCS sample (every 3 days, both venues) had
      found ZERO `dex_pool_state` objects for ORCA/RAYDIUM, confirming the (separate, already-fixed) Solana
      symbol-collision bug hadn't yet corrupted data before ITS fix landed. (repos: deployment-service,
      market-tick-data-service) **UPDATE 2026-08-02 (finalize task, slot-13 review craft): THIS specific sub-gate is now
      satisfied — `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s all 5 todos
      shipped/verified (query fix `market-tick-data-service@63199601`, live-verified against all 4 real subgraphs;
      backfill + purge independently verified — see the passage below for full evidence). The Track-1/2 + migration-VM
      gates named above are a SEPARATE, unverified condition this task did not check — not claiming the cron is actually
      resumable, only that the symbol-fix prerequisite specifically is done.

## Open follow-ups (carried forward from the pre-2026-07-24 Progress Log's "Deferred work after 2026-07-22/23" tables)

> Full narrative + evidence for every row below lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md)
> ("Deferred work after 2026-07-22" / "…-07-23" sections) — condensed to actionable todos here so nothing genuinely open
> got silently archived. Items already marked DONE/SHIPPED/RESOLVED in that history are NOT repeated here.

> **6 more closed items extracted 2026-07-25** (line-cap remediation, 2nd pass): the stale-duplicate Solana-writer note,
> the `is_defi_force_include_pool` wiring, orphan-sweep VM monitoring, the fake-history relabel + TRUE-final-scope pair,
> the cefi/prediction timestamp-provenance audit, and the `dex_pools_handler.py` parallel-writer resolution — all done;
> full text verbatim in
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).
> The FLAGGED-marker remediation decision record and the Solana AMM symbol-collision fix stayed here (also done) because
> open todos below point at them directly.

> **Linkage note (2026-08-02, ag-closeout-audit defi Phase 0 Orthogonality HARD CHECK)**:
> [`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`](/plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)
> was retagged `asset_group: [cross-cutting]` → `[defi]` (a pattern-3 fork-inherits-parent-tag mistag — content is 100%
> defi-specific staked-basis/LST collateral sizing + wizard parameterization work, previously invisible to this
> tranche's membership test). Citing it here so it registers as covered-by-itself in the linkage check rather than a
> newly-orphaned doc within this tranche.

- [ ] [SCRIPT] P3. **Root-cause `quickmerge.sh` silently resetting an unpushed commit** (observed 2026-07-22, 2
      hypotheses ruled out, cause not confirmed, non-reproducible on retry). Needs a `bash -x`/`set -x` trace the next
      time it recurs. (repo: unified-trading-pm)
- [x] ✅ [BACKEND] P2. **Audit defi adapters for dead code, runtime-fallback masking, and duplicate implementations**
      (gate-audit §1, 2026-07-24) across instruments-service `.../adapters/defi/`, MTDS
      `market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/`, and execution-service
      `adapters/defi_adapter.py`, per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Definition of
      done: a written finding per module (kept/fixed/removed + reason). (repos: instruments-service,
      market-tick-data-service, execution-service) — DONE 2026-08-01, closed by citation via
      `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md` todo 1: the full per-module audit already
      existed at `issues/defi_adapter_dead_code_audit_2026_07_24.md`, incrementally re-verified (§ 7 addendum) for the
      files added since.
- [x] ✅ [CONFIG] P2. **Retagged 2026-07-29 (corpus hygiene pass): reframed as a code-only extension task, not
      credential-blocked — verified `curve_adapter.py` already has a fully-wired `_query_curve_pool_at_block`
      (~line 617) / `_ensure_alchemy_client` (~line 217-228) RPC-fallback path using the same already-provisioned
      `alchemy-api-key`; UAC (`_defi.py` `SUBGRAPH_IDS["curve"]`) already carries live Curve subgraph IDs for
      ETHEREUM/OPTIMISM/AVALANCHE (only ARB/POLY lack one, per the UAC comment "ARB/POLY only on hosted service
      (deprecated)"), and Alchemy already supports Arbitrum/Polygon (`_defi_chain_data.py` chain configs) — so the
      remaining work is wiring the adapter's RPC path to the correct per-chain Alchemy URL (it currently hardcodes
      `eth-mainnet.g.alchemy.com` in `_ensure_web3`) for ARB/POLY, not a new credential.** F4 (rehomed from
      `/plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md`, was falsely cited "0 open todos"
      there — corrected 2026-07-27) — Curve DEX pools dead: decommissioned subgraph. `mtds-dex-pools-backfill` VM:
      `curve_adapter.py`'s hosted-service subgraph URL was decommissioned by The Graph; the gateway subgraph ID returns
      "no allocations" (no indexers serve it). Curve REST (`api.curve.finance`) is alive but current-snapshot-only, not
      historical `dex_pool_state`. ~~**BLOCKED-CREDENTIALS**: needs either a current indexer-allocated Curve subgraph ID
      (The Graph gateway API key) or an RPC key (`_query_curve_pool_at_block`, Alchemy) for historical block-level
      state~~ — the RPC-fallback path is already built and keyed; extend it to ARB/POLY (code-only), or accept
      honest-absence for Curve pools on those 2 chains until wired. (repo: market-tick-data-service)
      **na-eligibility-audit 2026-08-01: extracted to
      `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md` (conflict-check cleared) — track
      completion there, close this checkbox by citation once its batch-7 todo lands.** **DONE 2026-08-01 (slot-8),
      closed by citation — `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md`'s batch-7 todo 2**:
      `curve_adapter.py`'s `_ensure_web3` now resolves the RPC URL per-chain via
      `AlchemyBaseClient(chain=self.chain, project_id=self.project_id).get_rpc_url()` instead of hardcoding
      `eth-mainnet.g.alchemy.com`, wiring ARB/POLY through UAC `CHAIN_CONFIGS`/`CHAIN_TO_ALCHEMY_NETWORK` as this todo
      specified. 3 regression tests added (`TestCurveAdapter::test_ensure_web3_resolves_per_chain_rpc_url_for_arbitrum`,
      `..._for_polygon`, `test_ensure_web3_unsupported_chain_leaves_web3_none`); full `quality-gates.sh` green. Shipped
      `market-tick-data-service@1f58a127`. correction) — DeFi lending-indices: heavy instruments-store fallback, ~39%
      zero-row writes.** `mtds-lending-indices-20260628` VM: instruments-store-defi parquet missing for
      `{aave_v3,compound_v3}`/`<chain>`/`<date>` combos → falls back to subgraph discovery, yields little (aave
      OPTIMISM/LINEA, compound mostly empty). Confirm whether this is an instruments-service backfill gap (if so,
      backfill it) or legit venue-not-deployed-in-period absence — not a quick MTDS code fix either way. (repos:
      instruments-service, market-tick-data-service)

> **VM status** (full narrative archived 2026-07-25, 2nd extraction pass — see
> [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md)):
> check
> `gcloud compute instances describe canonical-migration-defi-marker-cleanup-20260724-182226 --zone=asia-northeast1-c` —
> SPOT + shutdown-on-completion, so TERMINATED/absent likely means done; the resume-logs at
> `gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/resume-seed/` are the proof
> either way, they don't need the VM alive to read.

- [ ] [SCRIPT] P1. **Run `delete_migrated_defi_markers_2026_07_23.py --apply`** — CODE-SHIP HALF DONE
      (`market-tick-data-service@a65117eb`, confirmed on `origin/live-defi-rollout` — the blocking flaky-test issue was
      worked around via the serial-pytest mitigation, not fixed at root; see
      `issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`, reopened 2026-07-24). Exact
      command:
      `cd market-tick-data-service && .venv/bin/python scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py --apply`.
      **Gated on the "glued-id rows" todo below (19 as of 2026-08-01, was 21)** — re-verify 0 glued ids before running
      (a content-correctness prerequisite, independent of the reversibility check below). **Still blocked**: that todo's
      2026-08-01 update confirmed all 19 remaining rows are phantom (fixable only by the `:401` P0 purge, not by this
      delete-markers script — markers and manifest rows are different surfaces). **Reversibility-verified, no
      `[OPERATOR]` gate needed** (finding T, `task_template.md`): object-level delete only (per-marker, never the
      bucket), target `market-data-tick-defi-prd-central-element-323112` —
      `gcs_bucket_soft_delete_retention_seconds(...)` returned `604800` (7 days) fresh-checked 2026-07-26 per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. Re-query fresh before running, not from this
      citation.
- [x] 1. ✅ [DATA] P1. **Remediate FLAGGED `_migrated_*` markers — ROOT-CAUSED + DECIDED 2026-07-25.** Full analysis in
      `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` (live parquet inspection, not guessed).
      Operator decided all three clusters same day; execution now tracked in two dedicated plans (not here, to keep this
      plan from re-growing): - **GMX perp_funding** (~1,896 markers) — confirmed via direct parquet inspection across
      the FULL 2022-2023 range that every single row is a synthetic OI-imbalance proxy
      (`funding_rate_long == -funding_rate_short` exactly, `market="all"`), not real captured funding data — the native
      subgraph query never worked for this venue's whole history. Combined with GMX's narrow/unverified usage in
      strategy-service (`staked_basis.py`'s own "GMX-V2 rows pending verification" comment), **operator decided: remove
      GMX entirely** — `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`'s all 8 todos SHIPPED
      (2026-07-25/26): `unified-api-contracts@18d53d63`, `market-tick-data-service@68407ae5`,
      `instruments-service@0214bb3c` (+`2de3418e` residual cleanup), `execution-service@2b75f21d`,
      `strategy-service@ca818ff8`, `unified-trading-library@f22e516f`, the `[OPERATOR]`-run prod-bucket GCS+manifest
      purge (5,374 `venue=GMX` manifest rows dropped, zero objects remain), and the docs update
      (`unified-trading-pm@bfda5df5b`). - **TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state** (~944+ markers) —
      root-caused to a real, ACTIVE code bug: `dex_pools_handler.py`'s `messari_basic` subgraph query never requests
      `inputTokens { symbol }` (verified byte-for-byte against the working sibling query), starving symbol resolution
      for these venues even in CURRENT/live captures (see
      `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`). **Operator decided: delete the bad
      data, fix the query, re-backfill** —
      `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (5 todos, sequential: fix →
      live-test recoverability → backfill → purge superseded data). - **lst_rates** (COINBASE/MAKER/SWELL/ETHENA) —
      root-caused: legitimate single-row/day snapshots, re-derivable on demand from the current canonical RPC-based
      `lst_rates_handler.py` (queries a historical block number directly, so nothing is actually lost by deleting the
      old copy); MAKER/ETHENA additionally obsolete (sDAI/sUSDe already reclassified out of `lst_rates` by a 2026-07-23
      fix). **Operator decided: purge as orphaned artifacts** — folded into
      `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s first todo. Evidence:
      `unified-trading-pm@83c31fc87` (refined root-cause), `@184387872` (GMX removal plan), `@781b98eea`
      (fix+backfill+purge plan). The underlying dry-run (banner above) continues independently — once it completes,
      re-run it to confirm these clusters clear per the two plans' own done-when criteria, before any `--apply`.

      **UPDATE 2026-08-02 (finalize task `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md`, slot-13
          review craft): all 5 todos of `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` SHIPPED and independently
          re-verified — no longer forward-looking.** Query fix: `market-tick-data-service@63199601` (verified an ancestor
          of `origin/live-defi-rollout`; live-tested against all 4 real subgraphs, all returned populated
          `inputTokens`/`fees`). Live-test recoverability: `market-tick-data-service@0f40a69f` (curve/OPTIMISM confirmed
          DEINDEXED; curve/ETHEREUM+AVALANCHE, sushiswap/ARBITRUM, trader_joe_v2/AVALANCHE, velodrome_v2/OPTIMISM all
          RECOVERABLE). Backfill: `mtds-dex-pools-symbolfix-batch1c`/`batch2` completed cleanly across the full
          confirmed-recoverable range, manifest spot-checked (symbol-named leaves, creation-timestamp-verified against
          each VM's run window). Purge (both categories — lst_rates `_migrated_*` markers AND the old dex_pool_state
          address-keyed leaves): independently re-verified complete, zero SAFE markers remain (only the irreducible
          FLAGGED floor — `FLAGGED_ROWCOUNT_SHORTFALL: 1287` + `FLAGGED_NO_SIBLINGS_NO_BACKUP: 977`, ZERO SAFE, an exact
          match to the corpus's known FLAGGED ceiling). Full evidence trail (VM names, spot-checks, preemption-recovery
          log) lives in that plan's own Progress Log — not duplicated here. Sibling issue doc
          `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md` flipped `status: open` → `status:
          resolved` accordingly in this same commit.

- [x] ✅ [DATA] P2. **19 glued-id rows (was 21) — ALL CONFIRMED PHANTOM 2026-08-01, folds into the `:401` P0 purge, NOT
      fixable by retry/rebuild.** Writer fix SHIPPED (`market-tick-data-service@f2e3ad41`/`70b9a81a`). The 9 ORCA/SOLANA
      `dex_pool_state` cells' migration retry completed 2026-07-24 (0 residual errors) but the manifest still shows the
      OLD glued rows — confirmed root cause: `rebuild_defi_manifest.py`'s append/upsert-only `ManifestWriter.add()`
      never retracts a row whose source object was renamed away (skipped by the R3 defect-A `_`-prefix guard). The 10
      `liquidations` rows (was 12; 2 cleared on their own) are the SAME class, NOT a separately-fixable "rerun the
      single-day rebuild" case as previously believed — direct GCS check
      (`plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md`, slot-11, 2026-08-01) confirms all 10
      source markers are ALREADY retired to `_migrated_*` with no per-instrument twins (genuine 0-row empty markers), so
      a rebuild pass can never rediscover them. **Both sub-populations now require the `:401` P0 phantom-row purge —
      this verification is that todo's own "sequence AFTER the glued-id manifest rebuild" precondition, now satisfied,
      so `:401` is unblocked.** Literal 0 not reached; `delete_migrated_defi_markers --apply` stays gated/blocked until
      the P0 purge lands and a fresh verify reports 0. Closed by citation —
      `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md`'s batch-7 todo 3 carries the full
      evidence.
- [x] ⛔ [DATA] P1. **WON'T-DO (session-3, 2026-07-26, operator present) — closed, not deferred.** Was: the ~16.7M-row
      LENDING→A_TOKEN/DEBT_TOKEN migration, gated on lending-writer-retire todos 7/8/10/11.
      `defi_lending_writer_retire_prerequisite_2026_07_20.md`'s own investigation found the flip needs 4 tightly-coupled
      legs incl. an instruments-service `expected_unattempted` re-seed, on top of a migration already reversed once.
      Session-3 decided to stop pursuing the physical retire permanently — flat `LENDING`/ `SOLANA_LENDING` stays the
      canonical form for market/event lending data_types, and a new read-side resolver
      (`unified_api_contracts.internal.domain.defi.resolve_lending_underlying`, shipped
      `unified-api-contracts@1d01a911`) gives canonical A_TOKEN/DEBT_TOKEN instrument_ids a rate lookup without any
      physical re-key. See `defi_lending_writer_retire_prerequisite_2026_07_20.md`'s session-3 Progress Log entry (todos
      15-18) and `/codex/02-data/defi-canonical-naming-ssot.md`'s instrument_type row for the full decision + rationale.
- [ ] [DATA] P1. **Residual canon walk C2-C12 — corrected 2026-07-25, the bundled title was stale-drift.** 6 items still
      SCOPED not executed (C2/C3/C4/C9/C11/C12), code-side verified GREEN for C2/C3/C9/C12; ALL SIX need a data-side
      read of the live `_index` once the 2 canonical-migration VMs reach a terminal state, then
      `audit_canonical_form.py --probe-paths` against the single consolidated bucket. Same open item, tracked verbatim
      at `defi_track01_per_instrument_and_canon_id_2026_07_24.md:310` — avoid duplicating the work across both docs.
      **Two stale-drift corrections**: (1) the old title's "+ instrument_type case/venue-spelling unify" bundling is now
      WRONG — that half is a SEPARATE item that RESOLVED 2026-07-24 as its own todo
      (`defi_track01_per_instrument_and_canon_id_2026_07_24.md:316`, live census found zero case or spelling drift
      anywhere in the manifest, a clean no-op — not part of the still-open C2-C12 walk). (2) "Also surfaced but not
      filed: `staking_yields_handler.py`'s `collect-staking-yields` CLI op has zero Cloud Scheduler jobs (dead code?);
      `lst_rates_handler.py` writes to a non-canonical, non-hive path" is also stale — it HAS since been filed as its
      own open todo (`defi_track01_per_instrument_and_canon_id_2026_07_24.md:744`, `[DATA] P2`), not left un-filed.
- [x] ✅ [BACKEND] P2. **DONE — duplicate of the Track 5 item above, resolved there with full evidence
      (na-eligibility-audit 2026-08-09).** Async fan-out + executor-offload for the DeFi write path (same 4 upload
      sites, same design sketch). `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s own copy (line ~105) is `[x]` DONE
      citing `mtds@ff1b5d51` ("feat(defi): MTDS DeFi perf bundle -- concurrency knobs + async fan-out +
      executor-offload") and `mtds@4cf0ea3d` (`defi_max_concurrent_fetches` semaphore fix), both confirmed ancestors of
      `origin/live-defi-rollout`. (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. **DONE 2026-07-29 (slot-5) — duplicate of `defi_mvp_backfill_optimization_ready_2026_07_20.md`'s
      canary todo, resolved there with full evidence.** Summary: SATISFIED by existing production evidence rather than a
      fresh launch — `mtds-dex-swaps-backfill-1`/`-2` have been running concurrently against TheGraph for 6 days (since
      2026-07-23) with 0 genuine HTTP 429s and 0 `attempted_failed` shard corruption across 92,317+43,913 run.log lines,
      proving the shared TheGraph key pool holds at N=2. Full evidence + the companion pagination-fix re-backfill
      validation (which also surfaced an unrelated COMPOUND_V3 regression, filed separately) in
      `plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md`'s corresponding todo.
- [ ] [DATA] P1. **Resume paused DeFi crons NOT scoped to `dex_pool_state`** + fix the honest-coverage-nightly
      right-size + codex-drift doc — gated on Track 1 (LENDING migration + canon walk above) + Track 2 (path-shape-pin
      code half) + the currently-running per-instrument migration VM finishing first (resuming now would race live
      writes against the exact data types it's mid-migrating). **Duplicate of the Track 8 resume-crons item above** —
      same split, same gates; the `dex_pool_state` (TRADER_JOE_V2/VELODROME_V2/CURVE) half stays gated on
      `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` too (operator ruling 2026-07-25,
      task_template.md finding P).
- [ ] [DATA] P1. **DeFi MVP backfill to 100%** — C-GREEN gated on Track 1 (LENDING migration + canon walk, above) +
      Track 2 (path-shape-pin) + Track 3 (`catalogue_pool_ids_for_shard` generalization, execution work not a decision).
      Backlog task `mvp_backfill_defi_onchain_v10-001` stays parked (`priority: 999`) until
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` flips true.
- [x] ✅ [BACKEND] P2. **Solana AMM symbol-collision code fix — SHIPPED 2026-07-24 (checkbox was stale — this todo's
      text describing the fix as "unwritten" was overtaken by events, never flipped).**
      `market-tick-data-service@0d83a8a9` wires the fee/tick-spacing discriminator into `solana_defi_handler.py`,
      confirmed ancestor of `origin/live-defi-rollout`. Full remaining scope (already-shipped fix,
      migration-of-existing-data check DONE clean, manifest-impact doc note, naming-doc update, and the SEPARATE cruder
      `dex_pools_handler.py` writer's own collision exposure) tracked in
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (§ "Per-instrument re-architecture", the Solana
      pool-symbol todo) — not duplicated here.
- [ ] [REVIEW] P3. **Decide whether the DeFi writers should stop emitting PHYSICAL zero-row absence-marker parquets at
      all, in favour of manifest-only absence** (`record_empty()` as the sole SSOT, per
      `/codex/02-data/honest-absence-downstream-handling.md:101-102`). **Migrated here 2026-07-31** from
      `/plans/archive/issues/defi_lst_empty_marker_hardcoded_venue_2026_07_27.md` (archival ritual step 1 — it was
      prose-only there, so it would have evaporated with the archive). That doc's own fix was correctly narrower
      (eliminate the hardcoded/fallback `venue=LST`, `mtds@5bf8a3c7`); this is the remaining, genuinely-open
      architectural question it explicitly left out of scope. **Why `[REVIEW]`/NA, not AO-dispatchable**: the blocker is
      a real unknown — `_write_empty_lst_marker`'s docstring claims a GCS-scan consumer depends on the physical marker
      existing. Done-when: either that consumer is identified (→ keep the marker, record why) or proven not to exist (→
      file the removal as its own bounded todo).

## Contradiction resolution (pre-SSOT) — archived, 95% closed

> The 2026-07-18 canonical-target audit's 75-finding contradiction-resolution log (1 blocking · 35 high · 31 medium · 8
> low; 53 doc · 17 code · 5 plan) lives verbatim in
> [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md).
> **95% closed** (7 of 9 tracked todos shipped); the 2 still-open findings were relocated live into Track 1 above (the
> "Cross-AG — PREDICTION canonicalisation" subsection + the UTL `_derive_instrument_id.py` dispatch-key decision note)
> rather than left stranded in the archive.

## Codex SSOTs (read before touching a track)

`/codex/02-data/defi-canonical-naming-ssot.md`, `/codex/02-data/defi-data-pipeline.md`,
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/honest-coverage-model.md`,
`/codex/02-data/honest-absence-downstream-handling.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/02-data/defi-completeness-oracle.md`, `/codex/05-infrastructure/manifest-consolidator-ssot.md`,
`/codex/05-infrastructure/vm-launcher-runbook.md`, `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`.

## Progress Log — condensed (2026-07-24, replaces the pre-split ~2145-line tick-by-tick log)

- **na-eligibility-audit 2026-08-01**: MIXED — re-read end to end (18 open items). 4 items extracted to
  `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md` after conflict-check clear (adapter dead-code
  audit, Alchemy ARB/POLY RPC wiring, glued-id ORCA re-verify, — plus a 4th from a sibling doc). 1 item (`VM_TASK` `cd`
  bug) found already in-progress on `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md` — not
  extracted, cited in place. Doc stays `assigned_vm: NA` overall — the remaining ~13 items are genuine
  `gate_on_depends`-cited (Track1 still 13-open), operator/judgment-gated, or same-doc-prose-gated work. No stale-done
  items found this pass.
- **2026-07-24 (session 3, `/autonomous`, orchestration pass)** — triaged ~50 open todos across 3 docs, flipped 4
  stale-done checkboxes, fanned out 9 parallel background agents; found the 15.87M-row defi orphan-sweep completed
  (largest of any AG, likely-test-artifact-leak caveat); session interrupted mid-flight by an infra migration. Full
  session narrative extracted 2026-07-25 (2nd pass) to
  [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

> **The full tick-by-tick history was NOT deleted.** The 2026-07-18→2026-07-23 detail (contradiction-resolution audit
>
> - the complete Progress Log + the "Deferred work after 2026-07-22/23" tables) lives verbatim in
>   [`defi_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md).
>   The 2026-07-24 session-3 → 2026-07-25 8h-mark-checkpoint detail (both full session write-ups condensed in this log,
>   the deferred-work table, lessons, and the interim cluster-breakdown report) lives verbatim in
>   [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md)
>   (2nd extraction pass, 2026-07-25). Every genuinely-open item from every deferred-work table now has a canonical todo
>   under "Open follow-ups" above or the relevant Track — nothing was silently archived.

- **2026-07-18** — Plan authored from a 6-agent audit + live GCS/manifest reads; operator-decided canonical target set
  (id grammar, SPOT_ASSET/SPOT_PAIR/POOL, two-id model); Tracks 1-8 scoped.
- **2026-07-18/19** — Per-instrument re-architecture superseded the batch-model tracks (DeFi capture stopped, migrated
  to per-instrument writers); the 75-finding contradiction-resolution audit run + mostly closed (see the archived
  section above).
- **2026-07-20/21** — Non-POOL EU terminal-state decision + oracle dead-venue handling shipped; `available_at` broader
  ~20-handler fix shipped; path-shape-pin (code portion) + second dexpool writer kill shipped both halves (MTDS + UAC).
- **2026-07-22** — SPOT preemption contract shipped for DeFi backfill launchers; residual canon walk C2-C12 scoped (not
  executed, gated on 2 running migration VMs); checker collect-\* fleet-wide real-VM-launch verification DONE.
- **2026-07-23** — Glued-id manifest rebuild verify + `_migrated_` marker delete tooling shipped (dry-run default, human
  `--apply`-gated); 6th orphan-sweep VM launched; dex_pools fake-history recurrence found + disposition ruled
  (relabel-forward, script not yet written); a live Solana AMM symbol-collision bug verified clean (paused, gated); a
  documentation gap closed (22 open defi plans/issues + this plan's own related-doc list made mutually discoverable —
  the seed of this 2026-07-24 line-cap remediation).
- **2026-07-24** — Plan line-cap remediation: `defi_strategy_pnl_axis_index_2026_07_24.md` extracted (Strategy/PnL
  axis), full history + 75-finding audit extracted to `defi_consolidated_closeout_history_2026_07_18.md` (archived),
  Progress Log condensed to this summary, every still-open "Deferred work" item converted to a canonical todo above, and
  the Aggregated source docs index (below) enriched to cover every active defi + defi-touching plan/issue.
- **2026-07-24** — cefi/prediction `available_at` timestamp-provenance audit (line-761 todo) executed. Checked whether
  prediction/cefi's write paths share DeFi's resolved "stamp a deterministic timestamp then discard it for wall-clock"
  bug class. Prediction (kalshi_adapter.py/polymarket_adapter.py) and cefi's primary path (ccxt_adapter.py) are already
  correct. Found 2 real gaps + 1 weaker candidate in smaller cefi batch handlers (`deribit_volatility_index_handler.py`,
  `book_microstructure_handler.py`, `deribit_options_chain_handler.py`). Filed
  `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`, cross-referenced into
  `cefi_consolidated_closeout_2026_07_18.md` Track 6 as the owning plan for the code fix (out of scope for this
  defi-plan audit todo). No production code touched this session.
- **2026-07-25 (`/autonomous`, operator stepped away for ~8h)** — ran the `delete_migrated_defi_markers_2026_07_23.py`
  dry-run on 2 parallel VM shards (~6 markers/sec combined); root-caused the FLAGGED-marker clusters via direct parquet
  inspection (not guessed) — GMX (removed entirely), TRADER_JOE_V2/VELODROME_V2/CURVE (real subgraph query bug),
  lst_rates (orphaned) — see the FLAGGED-marker remediation item above for the operator-decided disposition of each.
  `--apply` stays human-only, queued regardless of report cleanliness. Full session narrative + the 8h-mark interim
  report extracted 2026-07-25 (2nd pass) to
  [`defi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/defi_consolidated_closeout_history_2026_07_25.md).

> Moved verbatim to `/plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md` (2026-07-24
> line-cap trim, 2nd pass — the umbrella:true exemption was removed same-day). Read that doc for the full
> discoverability index of every other defi-relevant plan/issue with its open-todo digest.

**Missing digest entry (gate-audit §12, 2026-07-24)**: `defi_track01_per_instrument_and_canon_id_2026_07_24.md` is
referenced by "tracked under X below" prose in `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` but never
appears there as a linked entry — recorded here pending the fix below. (The gate audit's hardcoded "3x" was recounted
live 2026-07-26 by `/plan-reconcile defi`: the real figure is **2** — `…aggregated_sources_2026_07_24.md:379` and
`:398`. Count deliberately not re-hardcoded here; grep the file rather than trusting a restated number.)

- **[`defi_track01_per_instrument_and_canon_id_2026_07_24.md`](/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md)**
  — 13 open (5 P0, 3 P1, 5 P2 — 11 plain-open + 2 `[~]` partial; re-verified LIVE 2026-07-25, corrects the stale "18
  open" count above); top P0s: R3-run full-corpus migration VM still applying, catalogue-venue-gap re-enum/re-rollup
  deploy-gated, ~16.7M-row LENDING→A_TOKEN/DEBT_TOKEN Wave-D migration, residual canon walk C2-C12, address/UUID
  fallback elimination in `canonical_instrument_id`.
- [x] ✅ [DOC] P1. **Add the digest entry above into `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`** and
      fix every dangling "tracked under X below" reference there to point at it (bold digest style, task_template.md
      finding H) — re-grep the file for the live set rather than trusting a restated count; as of 2026-07-26 there are
      exactly 2, at `…aggregated_sources_2026_07_24.md:379` and `:398`. (repo: unified-trading-pm) — 2026-07-28 (slot
      8): digest bullet added at `…aggregated_sources_2026_07_24.md:533`; both dangling refs converted to real links.
      Tracked in `/plans/archive/2026_07/defi_consolidated_native_ao_extract_2026_07_25.md`.

- **2026-07-27** — Discoverability fix (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 4): 5
  defi-tagged docs reclassified `assigned_vm: NA → planning` this session were not mentioned anywhere in this hub — the
  "orphan invisible to sweep" bug class fixed twice before. Added here for future tranche-sweep discoverability:
  `issues/defi_instrument_availability_duplicate_instrument_key_rows_2026_07_26.md`,
  `archive/issues/defi_maker_vault_share_price_29day_gap_2026_07_26.md` (RESOLVED, archived 2026-07-28),
  `archive/issues/defi_plasma_chain_onboarding_gap_2026_07_26.md` (RESOLVED, archived 2026-08-01),
  `archive/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md` (RESOLVED, archived 2026-08-02, defi/cefi
  dual-tagged), `issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` (multi-AG tagged, defi among them). None
  were tracked in any Track above; all are now `assigned_vm: planning` and live in the AO backlog.

- **2026-07-30 (cicd worker, slot 16)**: this doc's `last_updated:` frontmatter field had been silently corrupted into a
  multi-date runaway YAML plain-scalar (root cause: `fix_frontmatter.py`'s `last_updated` auto-fill never stripped stale
  multiline-folded continuation lines — fixed in the same push, see
  `plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md`). Recovering the buried
  note text here verbatim before the frontmatter cleanup, since it isn't duplicated elsewhere in this doc:
  _"AO-readiness pass: related: reachability (6 new docs), 2 stale line-number cross-refs -> content refs, defi.2
  resume-crons split (operator ruling, task_template.md finding P), write_defi_rows DoD, Split-notice table +2 rows, 2nd
  extraction pass into the history doc -- was: "2026-07-24"; "2026-07-27" session-3 lending-resolver close-out (todo
  18)"_. Whoever wrote this most likely intended it for this Progress Log and it landed in the frontmatter by accident
  during an editing session; if any of it describes work not otherwise reflected above, re-verify and fold it into the
  relevant Track section.

- **context-scout 2026-08-03**: trimmed context_scope from 9 to 6 entries (dropped 3 narrower/archived pointers —
  `defi_track5_coverage_mvp_backfill_2026_07_24.md`, the archived
  `defi_consolidated_closeout_aggregated_sources_ 2026_07_24.md` digest, and the archived
  `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` — to stay within the intended 2-6 MVI range; kept the
  canonical-naming/delete-safety/coverage-model codex SSOTs + the gating Track0-1 child plan).
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).

## Progress Log

- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-08-01 MIXED verdict
  re-affirmed) — re-scoped because of a 2026-08-02 content change and re-read: 18 open items (a Track-1 factory- address
  roll-up todo was ADDED 2026-08-02; the adapter dead-code item was closed by citation to batch7). The new item needs no
  fresh assessment — it self-declares "The Option A-vs-B fork is an undecided design call — operator- gated, NOT
  AO-dispatchable until ruled" and "Single execution site — do not fork the work here" (it is the roll-up view of the
  executable todo in the forked Track-1 child), citing this skill's own 2026-07-30 KEEP-NA verdict on the source issue.
  Everything else is unchanged from the 2026-08-01 full read, whose 4 extractions already went to batch7. No new
  RECLASSIFY-eligible items; no stale-done items. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- swapped in the `build_canonical_instrument_id`
  source path (`canonical_id_builder.py`), the actual id-grammar target this doc's Canonical target section defines.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — 13 open items judgment/gated, re-verified live; no
  new extractable work beyond batch7's prior extraction.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries) -- the 2026-08-06 commit was a
  referrer-path fix only (an archived sibling's path updated in prose), no new reference target.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid, on citation alone — this doc's own
  frontmatter carries
  `depends_on: [defi_track01_per_instrument_and_canon_id_2026_07_24, defi_lending_writer_retire_prerequisite_2026_07_20]`
  with `gate_on_depends: true` (Half-B historical canonicalisation is machine-held on Track 1 landing). Per the HARD
  RULE (an explicit `depends_on`+`gate_on_depends` gate = KEEP-NA on citation alone, never re-litigated), the
  whole-doc-flip question doesn't reach individual-todo assessment. Not re-read line-by-line this round. Doc stays
  `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09** (tranche=defi): **KEEP-NA, stale items closed.** Gate citation re-verified live
  (read `defi_track01_per_instrument_and_canon_id_2026_07_24.md` end to end: the named prerequisite is genuinely still
  open, 4 todos + 1 in-flight partial) — doc correctly stays `assigned_vm: NA` on that citation, not re-litigated. Full
  read (966 lines) found 2 stale open checkboxes with hard evidence, independent of the gate question, both closed this
  pass: (1) the Track-1 roll-up factory-address item — decision now `[x]` DONE in `defi_track01...md` (operator ruling
  2026-08-08) and its execution further extracted 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`;
  converted from checkbox to a prose pointer, matching this doc's own established C0f-item precedent; (2) the async
  fan-out/executor-offload item — flipped `[x]` DONE citing `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s already
  -shipped twin (`mtds@ff1b5d51`, `mtds@4cf0ea3d`). 12 open todos remain (grep-verified). Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-15**: refreshed context_scope (6 entries), still accurate.
- **na-eligibility-audit 2026-08-16** [body-hash:cb8821f06e1e74fd]: KEEP-NA, stale items (citation-fix flagged, not applied this run) -- 983-line doc read end to end (2 Read calls), 10 open todos grep-confirmed matching Phase-0 (the docs own last marker self-reports 12 -- a stale count in that prior entry, not an under-read here: fence-aware grep, one fenced block contains no checkboxes). Doc-level depends_on+gate_on_depends gate (defi_track01 + defi_lending_writer_retire_prerequisite) reaffirmed live 2026-08-08/09 -- never-re-litigate citation respected. Two item-level findings, both flagged not applied: (1) the Residual canon walk C2-C12 item (line ~767) self-cites defi_track01_per_instrument_and_canon_id_2026_07_24.md:310 as the canonical tracking location -- same 3-way overlap with data_completion_defi_2026_07_15.md this run also found, needs one coordinated citation-fix pass across both docs, not a piecemeal edit; (2) the Resume-paused-DeFi-crons item (line ~792) is explicitly self-labeled a duplicate of the Track-8 resume-crons item above (line ~572) -- should be collapsed, not applied this run. Separately noted: the Track-3 PURGE-then-seed item (line ~436, a ~63.9M-row prod GCS purge+reseed) lacks an explicit [OPERATOR]/delete-safety citation unlike its sibling delete item (line ~681) -- worth a follow-up look, not a RECLASSIFY blocker since the doc stays NA on the frontmatter gate regardless. Doc stays NA.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17 (defi tranche, dispatch agt-f4fef7)**: KEEP-NA, valid — re-confirmed independently;
  no substantive content change since the 2026-08-16 verdict (context-scout metadata touch only, per this doc's own
  tail). Doc-level `depends_on`+`gate_on_depends` gate re-verified live this pass (`defi_track01_per_instrument_and_canon_id_2026_07_24.md`
  frontmatter `status: active`, prerequisite still open) — citation still real, not re-litigated. Doc stays
  `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-18** (agt-2c8a26): KEEP-NA, valid — 10 open todos match Phase 0; `depends_on`+`gate_on_depends` gate re-verified live (defi_track01 freshly re-read same run, still 2 open, infra-gated). Content change since 08-17 was plan_reconciler's `[OPERATOR]` note on the Track-3 PURGE todo only. No new RECLASSIFY/stale-done items. Doc stays `assigned_vm: NA`.
- **ci-reconcile 2026-08-18** (agt-d23e6a): AG-closeout-linkage QG flagged
  `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08` (gated HYPERLIQUID forward-write finalize) as an unlinked orphan — citation added here to close the gate, no content change to the finalize doc.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, stale items (flagged, not applied this run) — re-read end to end (2 Read calls); open-todo set unchanged since the 2026-08-18 verdict (only a ci-reconcile citation-fix landed since). The two previously-flagged citation-consolidation opportunities (Residual canon walk C2-C12 3-way overlap with data_completion_defi_2026_07_15.md + defi_track01_per_instrument_and_canon_id_2026_07_24.md; the duplicate resume-paused-crons item) still stand — not applied this pass either, same reasoning as prior rounds (needs one coordinated cross-doc pass, not a piecemeal edit). Doc stays `assigned_vm: NA`.
