---
doc_type: plan
title: Handoff prompt — DeFi data + strategy code path (post-2026-05-07 sessions)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, execution-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-07"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Handoff prompt — DeFi data + strategy code path (post-2026-05-07 sessions)

You are the next agent. The prior 4 sessions shipped the carry-tracer Phase 9 foundation (UAC SSOT + features-onchain
canonical columns + paired_price_dispersion kernel + resolver + catalog adds + PREFLIGHT_SKIPPED visibility + dep CVE
bumps). Picking up from there.

## Scope this set of sessions

**In:** Code-side fixes + backfill verification + intent (smoke / e2e) testing along the way. Strategy-service and
beyond is in scope. Foundational data correctness (writegate, manifest migration, feature DAG SSOT) is in scope.

**Out (deferred):** AWS parity (work stream D in master_to_live_defi). Live- mode services (work stream E — alerting /
live deployment UI / DART terminal / Copper / CEFFU / batch-vs-live recon / circuit breakers as live-only). Live
deployment UI tab + UTS-UI ↔ DART integration. Group F + Group G live-only items. May 23 cutover work.

The two archetypes targeted for live cutover (`carry_staked_basis` lead + `leveraged_funding_arb`) need clean batch
e2e + real PnL attribution before ANY live-mode work makes sense — this set of sessions gets us there.

## Read first (before any action)

1. `unified-trading-pm/plans/active/defi_master_2026_05_07.md` — 35 open P0 todos, the asset-group umbrella.
2. `unified-trading-pm/plans/archive/carry_tracer_phase_9_catalog_paired_dispersion_2026_05_06.md` — Phase 9 closeout
   doc with the handoff section (kernel + resolver shipped, follow-ups in the "Handoff for next agent" section).
3. `unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` — Tier 1 + 2 writer migration
   done; remaining gates land in Phase 2.B / 4.
4. `unified-trading-pm/plans/active/infrastructure_master_2026_05_07.md`
5. `unified-trading-pm/plans/active/manifest_migration_master_2026_05_07.md`
6. `unified-trading-pm/plans/active/feature_dag_uac_ssot_and_features_coverage_2026_05_06.md`
7. `unified-trading-pm/plans/active/strategy_architecture_v2_finalization_2026_04_19.md`
8. `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md` — downstream-consumption SSOT for the
   writegate model.

## Suggested order — 4 phases (FOUNDATIONS → STRATEGY → BACKFILL → VERIFY)

The order is pragmatic, not strict. Items within a phase can run in parallel once their dependencies are satisfied. Each
phase ends with a verification gate.

### Phase A · Data foundations (code + propagation)

A1. **Phase 1.B propagation — features-onchain VM rerun.** Launch
`FORCE=1 SKIP_DEPENDENCY_CHECK=1 bash deployment-service/scripts/vm/launch-features-backfill-vm.sh onchain DEFI 2026-04-03 2026-04-09 full`.
Wait for STARTED → DATA_INGESTION_STARTED events; once VM completes, sample one `lending_rates` parquet + assert
`{protocol, chain, asset, supply_apy, borrow_apy}` populated. Required BEFORE Phase 3.E (tracer shim deletion). 1-2
hours wall-clock.

A2. **Catalog spec → PairSpec lookup helper** in features-cross-instrument- service. Reverse the UAC
`parse_futures_expiry` direction: given `(root, as_of_date)` return the front-month CME / DERIBIT contract symbol +
expiry. Tested standalone (no GCS reads). ~150 LOC + 10-15 tests covering quarterly rolls (M/U/Z), monthly rolls
(F/G/H/J/K/M/N/ Q/U/V/X/Z), DERIBIT crypto (last-Friday), NASDAQ ETFs (no expiry, pass-through). Deliverable:
`features_cross_instrument_service/app/     calculators/futures_roll_resolver.py` + tests + symbol-builder tied to UAC.

A3. **batch_handler paired-spec dispatch.** When `feature_group == "paired_price_dispersion"` is in the request, bypass
the standard `_ingest_delta_one` path; instead invoke the resolver from A2 +
`paired_spec_resolver.resolve_paired_specs` + the kernel calculator. Cross-asset-group pairs (CME=tradfi, DERIBIT=cefi)
need TWO bucket reads — wire that path. ~80 LOC + 5 tests.

A4. **Phase 3.E — delete tracer's `_TOKEN_TO_PROTOCOL_ASSET` shim** in
`strategy-service/scripts/trace_all_carry_archetypes.py`. After A1 confirms parquets have canonical columns, delete the
shim + its 4 helpers + the `aave_supply_apy → supply_apy → lending_apy` fallback chain. KEEP `_normalise_protocol_name`
(catalog↔parquet vocab translation, independent of calculator schema).

A5. **Operational — Deribit dated/options relaunch.** Run
`ONLY="DERIBIT:2026:light DERIBIT:2025:light" FORCE=1 bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`
with longer runtime so intra-Deribit + CME-DERIBIT cross-venue futures specs in CARRY_BASIS_DATED +
ARBITRAGE_PRICE_DISPERSION have data. Verify parquets via sampling.

**Phase A verification gate:** Run partial Stage 3 of carry tracer over 2026-04-03..04-09. Expect ALL 7 archetypes
(YIELD_STAKING_SIMPLE, CARRY_BASIS_PERP, CARRY_STAKED_BASIS, CARRY_BASIS_DATED, CARRY_RECURSIVE_STAKED,
YIELD_ROTATION_LENDING, ARBITRAGE_PRICE_DISPERSION) have non-empty `realised_apy_bps`. CARRY_BASIS_DATED + cross-venue
ARBITRAGE_PRICE_DISPERSION are the new ones lit by A2/A3/A5.

### Phase B · Honest-absence + manifest closeouts (code)

B1. **Writegate Phase 2.B — orchestrator pre-skip rewrite.** Per the writegate plan, lift the calendar-pre-skip logic
from being silent to emitting `record_expected_empty(reason=EXPECTED_<X>)` per the closed reason taxonomy. Audit each
adapter calling `record_expected_empty` vs. the existing 9-reason set; surface missing reasons as a UAC enum addition +
downstream consumer audit per `/codex/02-data/honest-absence-downstream-handling.md`.

B2. **Writegate Layer 4 — 5 reconcilers.** 2 of 5 done per memory (`d3be0ef` + `ba5423f`). Remaining 3: -
`reconcile_phantom_manifest_rows.py` (sports → multi-asset_group rollup) - reader-side fallback reconciler (manifest
hive vocab category= ↔ asset_group=) - expected-absence backfill reconciler per asset_group (5 instances:
cefi/defi/tradfi/sports/prediction) Each reconciler is dry-runnable + idempotent; run once on 1 asset_group in dry mode,
verify output, then promote.

B3. **Manifest v6 → v7 migration propagation.** Per `manifest_migration_master_2026_05_07.md`. Writer side mostly done;
reader side needs catch-up. Audit every reader (deployment-api, features-\*, strategy-service archetype runs) for v6
schema dependency + migrate to v7 superset.

B4. **UAC feature_group → required_inputs DAG SSOT.** Per `feature_dag_uac_ssot_and_features_coverage_2026_05_06.md`.
Currently per-service; the LookaheadBiasError check needs the DAG to fire workspace-wide. Lift to UAC; per-service
dispatchers consume the SSOT; QG step asserts no service has its own DAG copy.

**Phase B verification gate:** Workspace-wide manifest sweep — every asset_group's data-status panel shows reasons
populated for every empty/expected-empty cell. No `__legacy__` synthetic key bucket should have rows that should have a
reason. Run `reconcile_phantom_manifest_rows_all.py` across all 5 asset_groups; phantom count should be < real-residual
baseline from the 2026-05-04 incident (354).

### Phase C · Strategy + execution code path (the "and beyond")

C1. **strategy-service v2 finalization.** Per `strategy_architecture_v2_finalization_2026_04_19.md`. Phases shipped per
memory (signal-broadcast 8/8); remaining closeouts + archetype-by-archetype QG + tests. Land basedpyright clean.

C2. **DeFi e2e pipeline gates** (defi_master 4 service QGs). `quality-gates.sh` clean on: - strategy-service (v2
finalization unblocks this) - execution-service - risk-and-exposure-service - features-onchain-service (verify after A1
rerun) Plus basedpyright clean across all 4.

C3. **CARRY_RECURSIVE_STAKED batch e2e** (defi_master sub-block): - Synthetic feature tick injected into
`defi-onchain-features-ready` → fill on the harness path - PnL row in strategy-service output decomposes into base_apy +
restaking_apy + borrow_cost + gas attribution - Position snapshot reflects leveraged LST holding + WETH debt - Health
factor recorded ≥ configured `min_health_factor` - PBM emits position snapshot; pnl-attribution emits per-strategy
attribution row - R&E log shows RISK_PASS published before execution Then repeat the gate for the other 7 archetypes.

C4. **features-onchain Docker image rebuild** — Cloud Build emits new `:latest` tag with the Phase 9 canonical-column
code shipped earlier this thread. Required for live mode; dependency for Phase D backfill runs that pick up the new
tarball.

### Phase D · Backfill + intent testing (verification)

D1. **MTDS DeFi slice to 100%** per defi_master mtds-s4 todos. Per-chain MTDS coverage: - Ethereum 85% → 100% - Solana
~99.9% (basically done) - Arbitrum / Base / Polygon — assess current %, fill gaps Re-scan availability indexes after
each chain (`mtds-s4-10-rescan-all-manifests`).

D2. **Tail-chain protocol coverage** (defi_master 988-dates-missing): - Aurora / Celo / Fantom / Mantle / Metis /
Moonbeam — each has 1 mid-tier protocol; diagnose per-(chain, protocol, data_type) gaps, prioritize, fill. - Mid-tier
(Arb / Avax / Base / BSC / Linea / Op / Polygon) — 32/53 protocols; per-protocol audit.

D3. **Lighter / Extended / Pacifica historical replay** (3 new perp DEXs). Each needs: - Lighter (zkSync mainnet):
`Trade` event ABI parse + subgraph schema-parity check + `_fetch_lighter_history` in `umi_tick_provider.py` + backfill
VM `mtds-lighter-history-backfill-{ts}` - Extended (Starknet): `Settlement` event signature + Starknet RPC template +
`_fetch_extended_history` + backfill VM - Pacifica (Solana program ID + Anchor `emit!` decoder + Helius
`getSignaturesForAddress` + `_fetch_pacifica_history` + backfill VM Date range 2024-08-01 → today per spec.

D4. **Oracle / chain expansion** (defi_master mtds-s3): - Pyth Solana wiring (mtds-s3-5-pyth-oracle): Hermes HTTPS pull
for batch + PythNet for live. Solana-only price reads (jitoSOL / mSOL / bSOL) — Chainlink covers EVM. Pyth was unbanned
2026-05-06 per master plan Q&A. - Chainlink multi-chain EVM (mtds-s3-6-multi-chain-oracle): Extend oracle_prices to Arb
/ Base / Polygon.

**Phase D verification gate (the intent test):** Run carry tracer Stage 4 historical 2022-01-01..today across all 7
archetypes. Sample 10 random days from the 4-year window; for each day, the comparison.parquet should have:

- Non-empty `realised_apy_bps` for at least 5 of 7 archetypes (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION can be
  empty pre-databento-coverage / pre-Pacifica-launch dates — that's honest absence, not a bug)
- `flow_of_funds_legs` non-empty for the winning slot of each archetype
- No silent NaN-only days (every day must show either real data or manifest-recorded
  `record_expected_empty(reason=...)`)

## Don't

- Don't tackle AWS parity (work stream D) — explicitly deferred this cycle per the operator's decision 2026-05-07.
- Don't tackle live-mode services (work stream E — alerting-service new plan, PBM/R&E/P&L attribution/B-vs-L recon
  extensions) yet. All 4 batch-mode equivalents are in scope; live-mode wiring waits.
- Don't ship the DART manual-trade lane (master_to_live_defi work stream C) — also deferred.
- Don't relax the "no fire-and-forget VM launches" rule. Every VM pair includes event-stream verification per workspace
  SSOT.
- Don't quickmerge to main while dep repos are dirty. Commit + push to `live-defi-rollout` directly per the 2026-05-06
  rule update.

## Reference paths

- DeFi master plan: `unified-trading-pm/plans/active/defi_master_2026_05_07.md`
- Phase 9 archived: `unified-trading-pm/plans/archive/carry_tracer_phase_9_catalog_paired_dispersion_2026_05_06.md`
- Writegate plan: `unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`
- Honest-absence SSOT: `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md`
- Tracer script: `strategy-service/scripts/trace_all_carry_archetypes.py`
- Resolver:
  `features-cross-instrument-service/features_cross_instrument_service/app/calculators/paired_spec_resolver.py`
- Kernel:
  `features-cross-instrument-service/features_cross_instrument_service/app/calculators/paired_price_dispersion.py`
- Launcher (FORCE-aware): `deployment-service/scripts/vm/launch-features-backfill-vm.sh`
- PreflightSkip helper: `unified_trading_library.emit_preflight_skip` (UAC `PreflightSkipReason`)

---

## SUPERSEDED 2026-05-07 — all items folded into active PM plans (SSOT)

This original 4-phase handoff was the kickoff doc for the Phase 9 → live cutover work. Session 2's continuation is at
[`defi_data_to_strategy_4phase_handoff_2026_05_07_session2.md`](defi_data_to_strategy_4phase_handoff_2026_05_07_session2.md)
which contains the full mapping from this doc's phases (A/B/C/D) to active PM plans.

**New agents: read active PM plans as the source of truth, not these handoff docs.** Both handoff docs are
reference-only historical context.

Primary active SSOTs for this work:

- `unified-trading-pm/plans/active/defi_master_2026_05_07.md` — DeFi headline plan (DEX perp follow-ups, carry tracer
  verification gates, e2e pipeline, oracle, custody, tail-chain coverage, MTDS DeFi slice)
- `unified-trading-pm/plans/active/feature_dag_uac_ssot_and_features_coverage_2026_05_06.md` — UAC DAG SSOT + UTL
  helper + per-service wiring
- `unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` — honest-absence write side
- `unified-trading-pm/plans/active/manifest_migration_master_2026_05_07.md` — manifest v6→v7 reader migration +
  reconcilers
- `unified-trading-pm/plans/active/strategy_architecture_v2_finalization_2026_04_19.md` — strategy v2 closeouts
- `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md` — live cutover master + work-stream coordination

PM commit landing the consolidation: `2cd3bbaf` (plan: close session-2 handoff gaps in active plans).
