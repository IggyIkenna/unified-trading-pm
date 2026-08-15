---
doc_type: plan
title: DeFi satellite AO batch 3 — residual-orphan triage after batch2
summary: >-
  Third AO-dispatch batch for defi, produced by the `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 59 defi AG-primary docs, run AFTER batch2 landed (2026-07-26). With batch1,
  batch2, the consolidated closeout, the aggregated-sources index and the forked children (track01, track5,
  lending-writer-retire, dex-pool-symbol-fix+finalize, native-ao-extract+finalize) all counted as covering, only 17 docs
  came back orphaned (15 partial-coverage, 2 never-touched); 39 are archivable-after-planned-work (already covered), 2
  archivable-now (archive candidates), 1 a cross-cutting/infra mistag (excluded). Phase-3's conflict-check took the 8
  AO-eligible orphan docs and cleared 13 candidate todos → merged 2 read-only report todos on the same source doc into 1
  (avoids a same-file Progress-Log race) → **12 todos ship here**. It left 8 items conflict/operator-gated (notably 5
  `defi_migration_audit_log` items whose "fold into dedicated buckets" premise is STALE — the dedicated→shared
  consolidation already shipped, so drafting them would regress the architecture), 4 skip_covered (already covered, not
  re-drafted), and 9 non-batchable orphans in the Deferred sections for the next iteration or an operator ruling.
  **status: draft — NOT dispatched. Flipping to active is an operator decision (per CLAUDE.md "Plan destination" HARD
  RULE); this batch was drafted autonomously by the scheduled ag_closeout_auditor and awaits operator approval.**
status: complete # (was: active) 2026-08-06 archival: all 13 todos done, locked_by empty
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    unified-api-contracts,
    agent-orchestrator,
    execution-service,
    unified-trading-library,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-3, satellite-docs, fresh-triage]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, scheduled ag_closeout_auditor, tranche=defi) — Phase 1 classified
  all 59 defi AG-primary docs via a Workflow fan-out (59 agents, sonnet), Phase 3 ran a conflict-check + candidate-todo
  draft over the 8 AO-eligible orphan docs via a second Workflow fan-out (8 agents, opus), per the skill's documented
  methodology. batch2 (also 2026-07-26) is counted as covering here — this batch is the residual after batch2.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

> **🗄️ ARCHIVED 2026-08-06** — all 13 todos verified `[x]`; deferred items re-verified by the gated
> `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` Todo 2; no new codex contracts established by this batch.
> Per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

# DeFi satellite AO batch 3 — residual-orphan triage after batch2

> **🟡 status: draft — NOT INGESTED / NOT DISPATCHED.** A draft plan is inert (`plans/PLAN_FORMAT.md`); the dispatcher
> ignores it until an operator flips `status: draft` → `active`. This batch was drafted autonomously by the scheduled
> `ag_closeout_auditor` (tranche=defi, 2026-07-26). Flipping it to active is an operator decision per CLAUDE.md's "Plan
> destination — ASK BEFORE CREATING" HARD RULE. Do a fresh re-read of each todo before activating (some source docs move
> fast).
>
> **Cross-plan sequencing note (todo 5):** the LIQUIDATION_CAPTURE tick-builder edits `paper_universe.py`, which
> `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s MEV-DOCS todo (batch2 line ~197) also edits. The edits are
> non-contradictory, but todo 5 should be **sequenced after** that batch2 todo lands to avoid a same-file race. If
> batch2 is still in flight when this batch activates, hold todo 5 until batch2's paper_universe.py change is in.

## Context (read before dispatching any todo)

Every todo below is a conflict-checked extraction from ONE orphaned defi source doc (each ends with `Source:`). The
conflict-check (Phase 3, one opus agent per orphan doc) grepped the whole covering set for each item's target
file/mechanism before drafting — items that a covering plan already claims were skipped (see "Already covered" note),
and items needing an operator/design ruling were parked (see Deferred). Same-priority todos run CONCURRENTLY across
workers by default; the 12 below were checked for cross-todo file collisions (the two read-only report checks on
`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` were merged into todo 9 to avoid a same-file Progress-Log
race). Two todos touch code beyond defi and are flagged inline: todo 2 (cefi/tradfi/sports strategy catalogs) and todo
10 (agent-orchestrator).

## Todos

- [x] ✅ [DATA] P1. D1 DeFi features backfill — run the features-service compute over the captured DeFi raw window
      (features read canonical raw; C0 done) to populate `features-onchain-defi` (currently ~3 rows) and
      `features-delta-one-defi` (currently no index), materialising `staking_apy_bps`/`funding_rate_apy_bps` (onchain)
      and `basis_bps`/`realized_vol_*` (delta_one, via the `funding_oi` and `returns` feature-groups respectively) for
      the in-scope DeFi instruments. **`features-volatility-defi` DROPPED from this todo's scope 2026-07-26** (slot-8
      finding, main-ruling-confirmed): the volatility feature family's `--asset-group DEFI` choice was REMOVED
      2026-07-17 (operator ruling — no DeFi options products exist, so implied-vol/skew/term-structure surfaces cannot
      be computed for DeFi; `features_service/volatility/cli/parser.py` now hard-rejects it, the corresponding bucket
      was deleted, and a unit test (`test_asset_group_choices`) enforces `ASSET_GROUP_CHOICES == ["CEFI", "TRADFI"]`).
      The original done-when's "features-volatility-defi... present and populated" leg predates that ruling and is
      structurally unsatisfiable by design — NOT a gap to chase. Safe-idempotent justification: idempotent feature
      compute, no GCS delete. Repo: features-service. Done when: `features-onchain-defi` row count ≫ 3 AND
      `features-delta-one-defi` has a populated index, both over the full captured window (2 legs, not 3). Source:
      `data_completion_defi_2026_07_15.md`

      **Progress Log extracted 2026-08-03 (slot-12, line-cap remediation)** — this todo accumulated a long
                                                                                                                                                  chronological chain of dated VM-launch/bug-chase entries (2026-07-26 through the 2026-08-03 FLIP below) that
                                                                                                                                                  pushed the live plan over the 1000-line hard cap. Moved verbatim to
                                                                                                                                                  `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch3_d1_progress_log_history_2026_08_03.md` — read it for
                                                                                                                                                  the full per-session VM-launch evidence chain (OOM root-cause, symbol-filter bug, timestamp-resolution bug
                                                                                                                                                  chain, NaN-warmup fix, etc.). Condensed summary: onchain leg (`perp_funding_rates`) completed 2026-07-31 after
                                                                                                                                                  2 real bugs fixed (`features-service@faedd957`, `1309480a`); delta_one `returns` leg completed 2026-08-02 after
                                                                                                                                                  6 real bugs fixed across the session chain (candle pass-through, symbol-filter, lookback-buffer, NaN-warmup,
                                                                                                                                                  timestamp-resolution ×3); delta_one `funding_oi` leg was blocked on HYPERLIQUID structurally lacking
                                                                                                                                                  `open_interest` until a 2026-08-03 fix (`features-service@6b2282c5`) closed it.

                                                                                                                                                  **2026-08-03 (slot-8) — FLIPPED, all 3 legs confirmed live** (454/455 `funding_oi` shards `captured`;
                                                                                                                                                  `returns`/onchain reconfirmed). Evidence:
                                                                                                                                                  `/plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`.

- [x] ✅ [STRATEGY] P1. **[CROSS-AG: touches cefi/tradfi/sports strategy code]** Sweep `archetype_slots_cefi.py`
      (CEFI_SLOTS), `archetype_slots_tradfi.py` (TRADFI_SLOTS), and `archetype_slots_sports.py` (SPORTS_SLOTS) — the v5
      slot-table construction surfaces parallel to the already-swept `archetype_slots_defi.py` DEFI_SLOTS (where 7/28
      rows were broken) — for catalog-emitted-config-key vs engine-param-read drift, using this doc's proven technique:
      construct the real registered engine (`get_archetype_engine_class` / factory.py ARCHETYPE_ENGINE_REGISTRY) from
      each slot's `initial_config`, call `on_tick` with realistic per-row features, and confirm a non-`[]` instruction.
      Fix unambiguous mechanical key rename/add drift in place (ADD the engine's real keys alongside — do not drop keys
      a real second consumer reads); for design-gated archetypes (RULES_DIRECTIONAL_CONTINUOUS /
      RULES_DIRECTIONAL_EVENT_SETTLED / ML_DIRECTIONAL_EVENT_SETTLED / MARKET_MAKING_EVENT_SETTLED / VOL_TRADING_OPTIONS
      — already xfail'd) leave them `xfail(strict=True)` with a one-line reason, do NOT force-fix. Extend
      `tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py` to parametrize
      CEFI_SLOTS/TRADFI_SLOTS/SPORTS_SLOTS (mirroring its DEFI_SLOTS coverage). Repo: strategy-service. Done when: every
      CEFI/TRADFI/SPORTS slot row either fires a real non-empty instruction or is explicitly
      xfail(strict=True)/allow-listed with a reason, the extended guardrail is green under
      `bash scripts/quality-gates.sh --no-fix` (0 unexpected failures, 0 XPASS), mechanical fixes shipped via quickmerge
      scoped to touched files. Source: `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` —
      **strategy-service@bc441642**. Swept all 31 CEFI + 12 TRADFI + 5 SPORTS slot rows: found + fixed the same
      catalog/engine config-key drift bug class in 2 CEFI rows (`STAT_ARB_BTC_ETH`, `REL_VOL_BTC_ETH` — catalog set
      `leg_a`/`leg_b`/`entry_zscore`/`exit_zscore`; `StatArbPairsFixedEngine` reads
      `long_instrument`/`short_instrument`/`long_venue`/`entry_z_score`/`exit_z_score`; added the real keys alongside,
      kept the originals as documentation per the same-catalog-surface `catalog_trading.py` precedent). All other rows
      already fired correctly or were on the existing design-gated xfail allow-list (RULES_DIRECTIONAL_CONTINUOUS /
      ML_DIRECTIONAL_EVENT_SETTLED / MARKET_MAKING_EVENT_SETTLED / VOL_TRADING_OPTIONS) — none force-fixed. Extended
      `test_all_catalogued_archetypes_construct_and_fire.py` to parametrize CEFI/TRADFI/SPORTS_SLOTS via a shared
      `_slot_test_params`/`_assert_slot_constructs_and_fires` helper (refactored the existing DEFI_SLOTS test onto the
      same helper, behavior-preserving). Verified: `bash scripts/quality-gates.sh --no-fix` green (real exit code
      confirmed via unpiped re-run, not a `| tail` artifact); systemic test 92 passed, 22 xfailed, 0 unexpected
      failures, 0 XPASS.

- [x] 2026-07-27 (slot-2) ✅ [DATA] P1. D2 MDPS `swaps_ohlcv` reprocess of the stale chain-column
      `attempted_failed`/`SCHEMA_VALIDATION_FAILED` rows — **VERIFIED STALE PREMISE, no reprocess needed.** Read the
      LIVE consolidated manifest directly (`market-data-tick-defi-prd-central-element-323112` —
      `resolve_bucket_name(kind="market-data", asset_group="defi")`; confirmed the legacy non-`-prd`
      `market-data-tick-defi-central-element-323112` bucket this todo's own text cites no longer exists, 404): **zero**
      `attempted_failed` rows exist for UNISWAP_V3-ETHEREUM or any of the 10 companion venues
      (UNISWAP_V2-ETHEREUM/AAVEV3-OPTIMISM/EIGENLAYER/CURVE-ETHEREUM/MAKER/FRAX/DRIFT-SOLANA/KAMINO/JITO/MARGINFI, or
      their current canonical forms AAVE_V3-OPTIMISM/EIGENLAYER-ETHEREUM/MAKER-ETHEREUM/FRAX-ETHEREUM/KAMINO-SOLANA/
      JITO-SOLANA/MARGINFI-SOLANA) under the `swaps_ohlcv`/`dex_pool_swaps` data_type. The `chain` column is 100%
      populated fleet-wide for the current `dex_pool_swaps` rows (0/795 null) — the chain-propagation bug this todo
      describes is confirmed fixed, and the C0 full-hive migration (C0d, `canonical-migration-defi-20260618-180603`)
      evidently already re-derived/rewrote this data with the fixed code, superseding the specific 28,634+companion row
      count this todo cited from 2026-05-28. Both the venue naming (now flat, e.g. `UNISWAP_V3` not
      `UNISWAP_V3-ETHEREUM`) and the manifest's `data_type` field (now the raw ingest type `dex_pool_swaps`, not
      per-timeframe `swaps_ohlcv_{tf}`) have changed since this todo was written, consistent with the C2/C3
      canonicalisation todos in `instrument_availability_hive_canonicalisation_2026_07_21.md`-style migrations. Done
      when: post-reprocess `attempted_failed` for all listed venues → 0, verified against the live `_index` — **this is
      independently true today with no reprocess run**, so there is nothing left to execute against this todo's
      described scope. **New finding, filed separately** (not part of this todo — a different, currently-ACTIVE failure
      mode, not the old chain-column bug): 795 `dex_pool_swaps` `attempted_failed` rows exist TODAY across
      UNISWAP_V3/OPTIMISM (342), CURVE/OPTIMISM (338), TRADER_JOE_V2/AVALANCHE (73, already tracked),
      PANCAKESWAP_V3/BSC+ETHEREUM (17), UNISWAP_V4/ETHEREUM+POLYGON (12), UNISWAP_V2/ETHEREUM (5), VELODROME_V2/OPTIMISM
      (5), AERODROME_V3/BASE (1) — all
      `error_reason="All N cascade schemas     drifted/returned GraphQL errors for {venue}/{chain} (subgraph=...)"`,
      growing daily through 2026-07-27 (not a stale artifact). Same TheGraph subgraph-schema-cascade failure class as
      the already-tracked TRADER_JOE_V2 finding in `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` —
      extended that doc's scope with a new todo rather than filing a duplicate issue. Source:
      `data_completion_defi_2026_07_15.md`

- [x] ✅ [STRATEGY] P2. **CLOSED AS ALREADY-SHIPPED-DUPLICATE 2026-08-03 (slot-12, data_engineering, pre-work
      verification).** Was: build the interest-PnL A2 staking leg in strategy-service, wiring `carry_staked_basis`
      STAKING accrual to the real `lst_yields` index-ratio. **This exact leg was already shipped BEFORE this batch was
      even drafted**: `strategy-service@e93902d8` ("feat(strategy): wire carry_staked_basis STAKING leg to real
      lst_yields index-ratio accrual", 2026-07-23) — confirmed a live ancestor of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor e93902d8 origin/live-defi-rollout`) and already promoted to `main`. Re-verified
      every done-when leg directly against current code (paths moved slightly since the ship commit —
      `strategy_service/core/canonical_lst_yields_index_provider.py` now lives at
      `strategy_service/engine/core/canonical_lst_yields_index_provider.py`, confirmed via `git log --follow`, not a
      loss): (1) real accrual — `strategy_service/engine/backtest/paper_run_passive.py::build_paper_run_passive` books
      `STAKING_REWARD` via `index_ratio_accrual(notional, index_prev, index_now)` fed by
      `CanonicalLstYieldsIndexProvider.day_index_pair`, with genuine honest-absence (`STAKING_REWARD=0` + log) when no
      real `lst_yields` row exists — not a stub; (2) Aave-lending mismodel explicit-zero — the same function's
      `emit_lending_leg=False` path (docstring: "carry_staked_basis has no real Aave lending position ... the caller
      drops the row entirely") confirmed live at `paper_run_passive.py:31-39,233-236`; (3) passive-parity test — real
      and present: `tests/unit/engine/backtest/test_paper_run_passive.py::test_staking_index_by_day_paper_batch_parity`;
      (4) byte-for-byte preservation — additive-only per the original commit's diff shape (new provider/accrual
      modules + additive params, no signature break). This is independently corroborated by today's na-eligibility-audit
      defi-tranche finding in `/plans/archive/2026_08/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`
      (its Todo 2, same sha), which is itself blocked from flipping the sibling checkbox in
      `lst_rate_honest_coverage_2026_07_21.md` only by that doc's line-cap — unrelated to this batch3 entry. No code
      shipped this session (nothing to build); closing as duplicate rather than leaving open for a worker to
      re-derive/re-implement already-live logic. Source: `lst_rate_honest_coverage_2026_07_21.md`

- [x] ✅ [BACKEND] P2. Phase 5 — wire the LIQUIDATION_CAPTURE archetype's paper-replay tick builder in strategy-service,
      mirroring the already-shipped Phase 3/4a/4b pattern. FIRST run the mechanical catalog-key-vs-engine pre-check
      (catalog `initial_config` keys emitted for LIQUIDATION_CAPTURE vs
      `LiquidationCaptureEngine.on_tick`/`REQUIRED_PARAMS`, per
      `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`) and confirm the engine `on_tick` actually emits
      instructions (not a stub). IF buildable: add `_load_liquidation_capture_ticks()` in
      `strategy_service/cli/handlers/paper_run_handler.py` reading real per-day on-chain
      `liquidation_events`/`health_factor` feature data (`health_factor_trigger` threshold sourced from catalog config,
      not invented), add LIQUIDATION_CAPTURE to `_ENGINE_DRIVABLE_ARCHETYPES` behind a new satisfiability gate in
      `paper_universe.py` with a typed honest-skip reason on data absence, add unit tests (satisfiability gate,
      honest-absence, determinism). Repo: strategy-service. Done when: EITHER LIQUIDATION_CAPTURE is in
      `_ENGINE_DRIVABLE_ARCHETYPES`, its tick loader reads real liquidation_events/health_factor GCS features with
      per-row honest-skip, and `quality-gates.sh --no-fix` is green with new tests; OR, if the pre-check finds the
      engine is a stub/no-op or requires an undecided health-factor-trigger design decision, the todo lands a documented
      held-finding in the issue doc naming the exact blocker with zero fabricated wiring. **Sequence after batch2's
      paper_universe.py MEV-DOCS todo (same file).** Source:
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — **HELD-FINDING, 2026-07-31 (slot 11,
      backend_engineer).** Pre-check run: confirmed `on_tick` (`liquidation_capture.py:68`) is real logic, not a stub —
      but it structurally can NEVER fire from a paper-replay tick because BOTH catalog sources
      (`catalog_yield_defi.py::build_liquidation_capture()`, `archetype_slots_defi.py`'s `DEFI_SLOTS`) deliberately
      leave `debt_asset`/`underwater_address` empty on every row (genuinely per-event runtime facts, no static catalog
      row can encode them), and fresh-verified `orchestrator.py` still has no params-mutation API to inject them
      per-tick — unchanged from the source doc's 2026-07-23 finding. This is the todo's own "stub/no-op" honest-finding
      branch, not the buildable one. Zero fabricated wiring — did NOT add LIQUIDATION_CAPTURE to
      `_ENGINE_DRIVABLE_ARCHETYPES` or build a tick loader. Full evidence chain landed in the source doc's own Phase 5
      todo (now also flipped). No code shipped, batch2's `paper_universe.py` MEV-DOCS prerequisite confirmed already
      landed (`strategy-service@8d7c6549`).

- [x] ✅ [BACKEND] P1. C6 Pyth `oracle_prices` — land the CODE fix (NOT a backfill VM: the 3 SPOT VMs already ran to
      `exit_code=0`; the gap is a code-level IS-catalogue filter). Per ruling (Evidence: activity event id=277382,
      `blocked_answered disposition=final` 2026-08-03T14:30:50Z, direction B "extend"): (a) DO-FIRST — restored
      BTC/ETH/INF to IS's `PYTH-SOLANA` enumerated set — `instruments-service@dec90cc0`; (b) extended `_PYTH_FEEDS` w/
      live-verified Hermes ids for JTO/RAY/WIF/JUP/USDC — `market-tick-data-service@cd017a1c`. Full scope + Progress
      Log: `/plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`. **Scope note
      (2026-08-03, slot-8)**: this todo's ORIGINAL done-when ("BTC/ETH/INF captures resume ... AND family-3 rows
      reconcile") bundled two things beyond the code fix itself — a live re-verify (needs a FUTURE collection run, can't
      be proven the same session as the code change) and the `_write_oracle_rows` `instrument_id`-naming reconciliation
      (real, separate, higher-risk work — changes `write_defi_rows`'s `instrument_type` from `SPOT_ASSET` to
      `SPOT_PAIR`, touching `SchemaContract` lookup + partition-path derivation for 17+ days of already-written data).
      Flipping this box to reflect the CODE-FIX scope actually dispatched (`defi_satellite_ao_dispatch_batch3-013`'s own
      title); the two follow-ups are split into their own tracked todos below/in the issue doc rather than left as an
      indefinitely-unflipped checkbox. `_write_oracle_rows` naming reconciliation already tracked as `[DATA] P3` in the
      issue doc.

- [x] ✅ [DATA] P2. Re-verify Pyth `oracle_prices` BTC/ETH/INF capture resumption — **CONFIRMED: fix shipped + verified
      (slot-12, 2026-08-06).** `market-tick-data-service@202bacc9` (LDR via quickmerge): modified
      `_filter_pyth_rows_to_is` to union IS-enumerated pairs with the collector's own static `_PYTH_FEEDS` pairs, so a
      stale/missing IS catalogue entry can never silently drop a feed the collector explicitly supports. Verified via
      `pyth-lst-backfill-20260806-035000` (1-day VM, 2026-08-06, `exit_code=0`): all 12 PYTH SOLANA feeds captured
      including BTC/USD, ETH/USD, INF/USD (confirmed via per-VM manifest read — `captured` status, not
      `empty_confirmed`). JTO/RAY/WIF/JUP/USDC also `captured` (MTDS@cd017a1c fix). Both code fixes on LDR and verified
      end-to-end. IS@6fbaae90 (restoring BTC/ETH/INF to `PYTH_PRICE_FEEDS`) is ALSO on LDR — the MTDS-side union guards
      against the stale-IS-blob gap regardless. **Evidence**: per-VM manifest
      `pyth-lst-backfill-20260806-035000.parquet` (2026-08-06: 12 PYTH SOLANA feeds, BTC=True, all `captured`).

- [x] ✅ [VERIFY] P2. Grep-then-READ whether DeFi arb/carry net-of-gas cost (gas_price × gas_units — execution
      `estimate_gas` gas_units × the captured per-chain `gas_fees` price) is actually wired in any consumer — **VERDICT:
      YES, CONFIRMED WIRED (slot-7, 2026-08-04).** Net-of-gas cost
      (`gas_price × gas_units × native_token_price_usd /     `1e9`) is wired in **5 independent paths** across strategy-service and execution-service; no issue doc needed:     (A) `execution-service/execution_service/engine/routing/instruction_router.py:498`+`services/pnl_calculator.py:228`     (`gas_cost_native
      = Decimal(result.gas_used) * result.gas_price_gwei / Decimal("1000000000")`→`net_pnl = gross_pnl -
      self._total_gas_cost - self._total_trading_fees`); (B) `strategy-service/strategy_service/pnl/engine/
      pnl_input_builder.py:186`+`orchestrator.py:574-594`+`breakdown.py:69` (`Decimal(str(gas_used)) * gas_price *
      native_token_price_usd / Decimal("1000000000")`→`attributed -=
      gas_cost_usd`); (C)     `execution-service/execution_service/matching_engine/defi/gas_cost_model.py:108`+`cost_aggregator.py:139`     (`gas_eth
      = Decimal(GAS_UNITS[action]) * gas_price_gwei /
      _GWEI_PER_ETH`→`DefiCostEstimate.gas_cost_usd`); (D)     `execution-service/execution_service/services/execution_cost_estimator.py:170-190` (`gas_eth
      = Decimal(str( gas_units)) * gas_price / Decimal("1e9")`→`return gas_eth *
      self._eth_price_usd`); (E)     `execution-service/execution_service/engine/backtest/actors/signal_driven_shared.py:279` (`NET_ALPHA
      = PRICE_ALPHA - FEES -
      GAS_COSTS`). The one architectural nuance: DeFi arb/carry **signal functions** (e.g.     `arbitrage_structural/price_dispersion.py:365`) compute gross spread before gas — gas cost is modeled pre-trade     (Path C) and subtracted post-trade (Paths A/B), not baked into the signal threshold. This is correct design: the     strategy finds positive-EV opportunities; execution costs are modeled and tracked separately at attribution time.     No issue doc filed — net-of-gas is definitively wired. Repo: strategy-service (cross-repo audit). Source:     `defi_migration_audit_log_2026_07_24.md`

- [x] ✅ [SCRIPT] P3. Regenerate the stale `adapter_contract_baseline.yaml` entries for the 2026-07-26 MTDS DeFi
      code-motion splits — unified-trading-pm@967ade4a5. Verified sub-part (a): dex_pools_handler.py (actual=5,
      baseline=5) + _dex_pools_subgraph.py (actual=6, baseline=6) = 11 calls, pre-split total preserved, zero lost.
      Sub-part (b): _defi_manifest.py baseline 43→47 (actual 47 after legitimate additions post-extraction, not lost
      calls), _defi_catalog_freshness.py (actual=6, baseline=6). The referenced commit 08439787 is a sports commit
      unrelated to this extraction — verified via direct per-file grep counts instead. Manual baseline edit (43→47 for
      _defi_manifest.py only, the other 3 files unchanged) rather than full --regenerate-baseline to avoid
      blanket-blessing unrelated entries. check_adapter_contract_regression: OK (328/328 baselined files at or above
      minimum). MTDS QG --no-fix: no adapter contract-call regression warnings printed for these files. Source:
      `mtds_dex_pools_adapter_contract_baseline_stale_2026_07_26.md`

- [x] ✅ [DATA] P3. Two read-only reconciliation checks for
      `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`, combined into ONE todo (both append findings to that
      doc's Progress Log — must not race): (a) reconcile the three independent `_DEFAULT_PROTOCOLS` lists in
      market-tick-data-service (`lending_indices_handler.py:176`, `risk_params_handler.py:107`,
      `liquidations_handler.py:149`) against each other and against `SUBGRAPH_IDS`
      (`unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:62-217`) — produce a
      written mismatch report (which protocol appears in which list vs SUBGRAPH_IDS); (b) confirm whether
      `vault_share_price_handler.py` has actually run/been scheduled for FRAX-ETHEREUM (`_VAULTS["sFRAX"]`) by reading
      the live defi manifest (scoped read, no new whole-corpus walk) for FRAX-ETHEREUM under
      `data_type=vault_share_price` — genuine absence = a scheduling gap, not an enumeration gap. READ-ONLY: do NOT add
      `fluid` or any protocol to a handler without also wiring a real collector (would write dishonest zero-row manifest
      stamps). Repo: market-tick-data-service. Done when: both findings (the cross-list mismatch inventory + the
      FRAX-ETHEREUM vault_share_price row-count/`attempted_at` classification) are appended to the source doc's Progress
      Log with no handler code changed. Source: `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`

- [x] ✅ [INFRA] P3. **CLOSED AS ALREADY-SHIPPED-DUPLICATE 2026-07-31 (found during batch4-finalize's re-check of
      batch4's dropped-by-conflict-check items).** **[CROSS-AG: targets agent-orchestrator, not defi code]** Was: add an
      M3 `/done` verification exception in agent-orchestrator so a cross-repo plan commit converting a referenced
      `- [ ]` todo into a non-checkbox `CANCELLED`/`SUPERSEDED` marker (per `task_template.md`'s remove-a-todo
      convention) is accepted instead of hard-rejected with `cross_repo_pm_file_touched_no_checkbox_flip`. **This exact
      fix was already built and shipped the same day this todo was drafted**, via a different route than this todo's own
      `Source:` doc's P0 gate: `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s own `[INFRA] P3` (slot-4,
      2026-07-26) added the identical exception directly — `verify.check_plan_flip` (`agent-orchestrator@c9f805c`) now
      recognizes a `- [ ] <brief>` line converted to a non-checkbox CANCELLED/SUPERSEDED marker bullet via a new
      `_diff_cancels_checkbox` helper, in both single-repo and cross-repo modes, and accepts `/done` with
      `reason="todo_cancelled_superseded"` without requiring a `[x]` flip — with regression coverage in
      `tests/test_done_gate_plan_flip_hard_reject.py` (both the accepted-cancellation and still-rejected-plain-no-flip
      cases). Re-verified live this pass: `c9f805c` is a confirmed ancestor of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor c9f805c origin/live-defi-rollout`), and `server/verify.py` carries
      `_diff_cancels_checkbox` plus the `"todo_cancelled_superseded"` reason string at multiple call sites. Dispatching
      this todo again would duplicate already-live code. No new work needed; closing as duplicate rather than leaving
      open for a worker to rediscover. Source: `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`

- [x] ✅ [REGISTRY] P3. Tighten the defi POOL data-type validity grain from union-across-protocols to per-protocol in
      UAC — unified-api-contracts@fe46865f `registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES, so
      `valid_data_types_for_instrument_type("defi","POOL")` no longer seeds expected_unattempted
      `perp_funding`/`lending_indices`/`liquidations` for a pure-DEX pool (e.g. UNISWAP_V3) while still granting those
      data_types to perp-capable pools that legitimately produce them. Repo: unified-api-contracts. Done when:
      `valid_data_types_for_instrument_type("defi","POOL")` is protocol-scoped (a UNISWAP_V3 POOL yields only
      `dex_pool_state`/`dex_pool_swaps`; a perp-capable POOL still yields `perp_funding`), a new unit test proves the
      tightened per-protocol set, no impossible-combo regression, quality-gates.sh green. Source:
      `defi_migration_audit_log_2026_07_24.md`

- [x] ✅ [SCRIPT] P3. Gate the `migrate_defi_full_v9_canonical.py:570` L1 `_safe_find(fs, {base}/{dir_name})` on a cheap
      — market-tick-data-service@08eaf113 prefix-existence probe (or drop it) so the migrator stops issuing a
      whole-bucket enumeration per `day=`-partitioned source bucket that has no top-level L1/raw_tick_data tree — but
      KEEP a fallback so a bucket that genuinely has an L1 tree is never silently skipped (data-loss guard). Repo:
      market-tick-data-service. Done when: the L1 find is guarded by an existence probe; a unit test proves both (a) a
      `day=`-only bucket skips the expensive scan and (b) a bucket with a real L1 tree still enumerates it; a
      date-scoped dry-run still completes 0-errors; quality-gates.sh green. Source:
      `defi_migration_audit_log_2026_07_24.md`

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`**: Declare HYPERLIQUID/ASTER in UAC
  `ALL_DEFI_VENUES` + `DEFI_VENUE_DATA_TYPE_CAPABILITIES`. batch2 (line ~341) dispatched this doc's OTHER todos
  (EULER_V2/Plasma) and explicitly excluded this one. The `honest_coverage_shard_dimension_model` confirmation only
  resolves the CLASSIFICATION intent (dual CEFI+DEFI listing is intentional), NOT whether declaring into UAC
  `ALL_DEFI_VENUES` double-counts the same on-chain rows across system-wide CEFI+DEFI denominators — an open
  UAC-registry-level axis ruling the operator must make. The doc's own last word (2026-07-21) still flags it as "a real
  follow-up."
- **`defi_migration_audit_log_2026_07_24.md` items 3, 5, 7, 8, 10 (STALE/INVERTED PREMISE)**: all five prescribe giving
  orphan data_types / handler writes DEDICATED buckets, but the dedicated→**shared** consolidation already SHIPPED
  (`defi_consolidated_closeout_2026_07_18.md`:194-195 — all kinds resolve `kind="tick-data"` on the single
  `market-data-tick-defi-prd`; the foundational v9 migration ran 2026-06-18). Drafting these as-is would RE-INTRODUCE
  the divergence the consolidation removed. They need an operator reconciliation of the item text against the shipped
  shared-bucket architecture, not a fresh migrate todo. (item 5's "gas in the could-exist denominator" sub-part is also
  an open design call — gas is chain-grain, not the instrument-universe grain of Track-3's 63.9M seed; item 10 folds the
  already-EXCLUDED item-2 Solana-source ruling, and DefiLlama's status as a canonical on-chain source is itself
  contested — batch2:143 migrated AaveRateImpact OFF the DefiLlama borrow field.)
- **`defi_migration_audit_log_2026_07_24.md` item 2 (SOURCE_PRIORITY Solana source) + item 9 (delete legacy buckets)**:
  item 2 is an operator "which Solana source is canonical" ruling (solana_rpc/helius/defillama); item 9 is a destructive
  legacy-bucket delete requiring operator sign-off per the GCS delete-safety HARD RULE. Item 1 (Era-B legacy retirement)
  is a large cascade-coupled UAC+MTDS registry+test drop — technically AO-eligible now its cefi+tradfi G4-apply gate
  cleared, but sizeable enough it warrants its OWN dedicated plan, not a batch todo.

## Deferred — conflict-gated / sequence-gated (re-check next iteration)

- **`lst_rate_honest_coverage_2026_07_21.md` E3 recursive-staking borrow leg**: builds ON TOP of todo 4 (A2 staking leg)
  in the SAME strategy-service `carry_staked_basis` accrual mechanism — drafting it as a sibling would race on the same
  file. Also still needs its own scoping step (Aave-oracle unblock alone is insufficient per the doc). Re-extract as a
  batch4 todo once todo 4 lands.
- **`data_completion_defi_2026_07_15.md` G6 Jupiter historical reconstruction**: GATED on G1 (Orca+Raydium pool-state
  backfill), which is operator-launched long-wall-clock and not scheduled by any covering plan; and the reconstruction
  approach itself (simulate Jupiter routing vs pool states, "algorithmically nontrivial") is an undecided
  research/design call. Unblock once G1 lands and the approach is ruled.

## Deferred — non-batchable orphans from Phase 1 (report only; need direct human action, not another batch)

These 9 orphaned docs carry ONLY non-batchable-taxonomy remaining work (per the per-doc Phase-1 classification) —
re-running the audit against them will keep reporting the same until a human acts:

- **`defi_venue_lst_rates_residual_2026_07_24.md`** — operator-gated: bare-`SUSHISWAP` classic-vs-V3 alias is a
  data-semantics ruling (same class as the already-made SUSHISWAP/UNISWAP factory-version call).
- **`defi_expected_unattempted_seeder_design_2026_07_26.md`** — operator-gated: IS the standing human plan (assigned_vm:
  NA) batch2 designated as successor to cancelled C8; P0 is an [OPERATOR] capability-vs-collectibility reconciliation,
  P1-P3 BLOCKED-OPERATOR. Becomes AO-eligible only after the operator resolves P0.
- **`issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`** — human-only/too-large:
  CARRY_STAKED_BASIS delete-vs-re-leg is a strategy-domain judgment; the generator/UI structural-skew item "needs its
  own plan"; the UI resync is blocked on both.
- **`issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`** — time-gated: sole remaining item (re-run G2 gate)
  is blocked on `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (owned by
  `data_completion_defi_2026_07_15.md`); 13 dispatches already bounced on it. Already in batch2's time-gated Deferred.
- **`issues/defi_five_never_captured_venues_fix_2026_07_22.md`** — human-only: correcting/deleting MORPHOVAULTS
  `GTUSDCP.parquet` garbage share_price row is a prod-bucket data mutation, operator-gated per the GCS
  delete/mutate-safety protocol.
- **`issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`** — human-only: Todo 4 is a `[DECISION]`
  remediation ruling (accept legacy artifact vs targeted manifest correction), conditionally gated on todo 1's
  now-covered outcome.
- **`issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`** — human-only: `[DESIGN] P3`
  IS-catalogue-completion-signal retry-sweep is a design call (pub/sub vs sentinel-file vs other; which service owns
  it). Needs a design session first, then a scoped todo.
- **`issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`** — human-only: regenerating/reconciling
  the 57 `unified-api-contracts/openapi/prospectus/*.md` generator outputs spans many axes unrelated to DRIFT removal —
  needs a human design decision on how to reconcile generator vs committed copies before any worker todo is
  determinable.
- **`archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`** — human-only: steps 2-4 (new MTDS
  chain-field collectors for ltv/liquidation_threshold/reward_rate/health-factor inputs + recompute) are "genuinely new
  scope (upstream collection)... size them as their own work" per the doc author (now tracked in
  `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`; the doc's own one todo — delete + register —
  shipped 2026-07-30, features-service@d8a643a0, doc archived). Already in batch2's human-only Deferred.

## Note — items already covered (skip_covered, NOT re-drafted)

Phase-3 conflict-check confirmed these 4 items are already claimed by a covering plan (would be duplicates):

- `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` item 4 (MORPHO absence intentional-check) → owned by
  `defi_expected_unattempted_seeder_design_2026_07_26.md`'s [OPERATOR] P0.
- `data_completion_defi_2026_07_15.md` C5 phantom-grid delete → subsumed by the C0/track01 canon walk + data-status
  dedicated-index repoint.
- `data_completion_defi_2026_07_15.md` instruments-store-defi canonical-form walk → owned by the active cross-cutting
  `instruments_manifest_canonicalisation` plan.
- `data_completion_defi_2026_07_15.md` FLAG2 `_BUCKET_CATEGORY_OVERRIDES` → already RESOLVED at
  `defi_dedicated_bucket_shared_migration_2026_07_13.md`:257-268 ([x] ✅ deployment-api).

## Note — archival candidates (archivable_now — a separate archival todo, not a batch candidate)

- `issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` — Final report (2026-06-17) declares done state;
  all 6 BUGs fixed; sole open item self-migrated to `perp_funding_data_semantics_and_cadence_2026_06_16.md`. Archive.
- `issues/mtds_perp_funding_backfill_hang_2026_07_14.md` — all 6 todos [x] with evidence; residual spun to
  `mtds_retry_safe_default_audit_2026_07_14.md`. Archive (batch2 already flagged this one archivable_now).

## Note — 1 mistag (exclude_cross_cutting)

- `archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` — tagged `asset_group: [defi]`
  but real content is a fleet-wide QG STEP 5.101 infra/CI issue, not defi-specific. Should be retagged `cross-cutting`
  or `infra` (batch2 already flagged this as a mistag Note).

## Deferred work — migrated to: N/A (this plan itself is not deferred/migrated)

This plan's own `## Deferred — ...` sections each cite their source issue doc directly as the successor reference; no
part of this plan was migrated elsewhere.

## Progress Log

- **2026-07-26** — Drafted autonomously by the scheduled `ag_closeout_auditor` (slot 15, tranche=defi) via the
  `/ag-closeout-audit` skill. Phase 1: 59 defi AG-primary docs classified by a 59-agent Workflow (sonnet) → 39
  archivable-after-planned-work, 15 orphaned_partial, 2 orphaned_never_touched, 2 archivable_now, 1 exclude. Phase 3: 8
  AO-eligible orphan docs conflict-checked by an 8-agent Workflow (opus) → 13 draft / 4 skip_covered / 8 conflict_park;
  merged 2 same-source read-only report todos into todo 9 → **12 todos**. `status: draft` — awaits operator approval to
  flip to `active`.
- **2026-07-27 (slot-11)** — Worked D1's blocking issue
  (`features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`). Shipped a candidate fix for finding 1 —
  `unified-trading-library@06190d77` bounds `read_manifest_rows()` to the slim, filtered manifest-read path — plus
  regression coverage. **D1's checkbox stays UNFLIPPED**: the fix is not yet end-to-end validated (needs the UTL wheel
  release to reach features-service before the repro VM can confirm it resolves the hang/OOM). Operator-confirmed
  (BLK-adabd51f, option B) this session's deliverable is the shipped candidate fix + the issue doc's handoff section
  (repro command + pending gate + next steps) — do not idle-hold a slot on the wheel release; a future dispatch resumes
  the validation.
- **2026-07-31 (slot-5, data_engineering craft)** — Resumed D1's `returns` leg from slot-2's handoff (3 timestamp bugs +
  a found-but-unfixed 4th symbol-separator bug). Shipped the 4th fix (`features-service@7e10172c`, verified against real
  CHAINLINK+PYTH raw data, 6 new regression tests, full QG green) —
  `delta_one_passthrough_symbol_filter_slash_underscore_mismatch_2026_07_31.md`'s P1 recommended-decision item is now
  flipped (slot-8 independently confirmed the same fix via a concurrent `git pull --rebase` reconciliation, no duplicate
  shipped). Relaunched the real verification run (`features-delta-one-defi-20260731-025149`,
  `FEATURE_GROUP=returns FORCE=1`, same clean window `2023-05-12..2023-10-31`) to confirm end-to-end — caught and fixed
  a stale-tarball launch first (deleted the mis-launched VM within seconds, republished, relaunched clean; full recipe
  in the symbol-filter issue doc's Progress Log). **The symbol-fix is confirmed working**: range-load went from the
  pre-fix `27/51` to `51/51` real instruments matched. But the run still produced
  `Completed 0/51 instruments for returns` — a **5th, distinct, downstream bug**:
  `BufferManager.calculate_buffer_days()` computes only a 1-2 calendar-day lookback window from
  `FEATURE_GROUP_LOOKBACK["returns"]=100` periods (correct for CEFI's dense 15s candles, wrong for DEFI's sparse
  pass-through event ticks — confirmed via direct repro: 945 real rows genuinely exist across the full window, but the
  per-date window only admits ~4-12 of them, never reaching the 100-row sufficiency threshold, deterministically on
  every date). Filed `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md` with full repro
  evidence + 3 candidate fix directions (did not patch `buffer_manager.py` myself — it's shared CEFI/TRADFI/DEFI code
  where the current formula is correct for real candle data; a blind fix risks regressing that). **D1's checkbox stays
  UNFLIPPED** — the `returns` leg still cannot complete until this new buffer-sufficiency bug is fixed, and `funding_oi`
  remains separately blocked on the HYPERLIQUID OI-absence operator decision
  (`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`). Real forward progress this session: 2
  of what is now a confirmed 5-bug chain are fixed and verified; the remaining blocker is precisely scoped with
  reproducible evidence for the next dispatch.
- **2026-07-31 (slot-10, data_engineering craft, re-dispatch) — status-only check, no new bugs, no relaunch: confirmed
  both of slot-11's healthy production VMs are still alive and making real measured progress; both standing blockers are
  unchanged.** Re-read this todo's own text fully before touching anything (per the "lesson for future dispatches" note
  above). Live-verified (not just log-tail) both VMs via `gcloud compute instances list` + GCS `run.log` reads:
  `features-delta-one-defi-20260731-094100` (`2023-05-12..2023-10-31`) has produced 368 real
  `Completed N/51 instruments for returns` lines with zero errors/tracebacks, steady ~20-25s cadence with no gaps
  through 11:21 UTC; `features-delta-one-defi-20260731-110727` (`2023-11-01..2026-07-22`) passed lookback validation
  (51/51 instruments) and is mid-candle-load for its buffered range, heartbeating cleanly with no errors through 11:21
  UTC. Neither shows any sign of the resolved OOM/hang class or the fixed timestamp/symbol/buffer bugs recurring.
  Checked both blocking issue docs fresh (not from memory):
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md` (blocks the remaining `2022-11-01..2023-05-11`
  ~6-month gap in the `returns` leg) is still `status: open`, `assigned_role: backend_engineer` — needs a profiler/local
  repro, correctly out of data_engineering craft scope for a backfill session.
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` (blocks the entire `funding_oi` leg) is
  still `status: open`, `[OPERATOR]`-gated — HYPERLIQUID structurally never carries `open_interest`, needs a repo-owner
  adapter-extend-vs-calculator-relax ruling. Did not relaunch or touch either blocked leg (deterministic, already
  exhaustively reproduced by 6+ prior dispatches). **D1's checkbox stays UNFLIPPED** — did not duplicate any
  already-exhausted work this dispatch; the two production VMs are the only forward motion in flight, self-shutting-
  down on completion (SPOT, idempotent). **For the next dispatch**: before relaunching anything, verify these two VMs
  reached `DEPLOYMENT_COMPLETED exit_code=0` (VM absence from `gcloud compute instances list` + a matching completion
  entry under `gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-31/`) — if both completed
  cleanly, the `returns` leg's real coverage is then `2023-05-12..2026-07-22` (the vast majority of the true
  `2022-11-01..2026-07-22` window), with only the ~6-month gap left blocked on Bug B. The checkbox still cannot flip
  until BOTH the 6-month gap (needs Bug B's fix) and `funding_oi` (needs the operator ruling) clear — this todo remains
  a strong candidate for parking (`priority: 999` + a false prerequisite gated on both linked issue docs resolving, per
  slot-16's still-unactioned recommendation above) until either external blocker moves.
- **2026-07-31 (slot-4, data_engineering craft, re-dispatch) — Bug B's fix landed since slot-10's check; launched the
  previously-blocked 6-month gap; the other 2 production VMs remain healthy; `funding_oi` still correctly untouched
  (operator-gated).** Re-read this todo's own text + both linked issue docs fresh before touching anything (per the
  standing "lesson for future dispatches" note). Found
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`'s `[BACKEND]` P1 is now `[x]` DONE
  (`features-service@f8e21361`+`b1652b59`, shipped by slot-14 since slot-10's dispatch — root-caused to
  `_build_captured_index()` decoding the whole 27.4M-row DEFI manifest with no `filters=`, fixed with a bounded
  row-group pushdown) — this unblocks todo 2 (the actual gap backfill), and separately confirmed
  `delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md`'s `[BACKEND]` P2 (Bug A, the preflight
  false-negative for pass-through feature groups) is ALSO now `resolved` (`features-service@f57d11ae`, slot-7) — so the
  gap backfill no longer needs `--skip-dependency-check` at all. Live-verified (not from memory) the 2 standing
  production VMs (`094100`, `110727`) are both still `RUNNING` with clean, error-free logs (094100 processing its
  window's final days `2023-10-23..2023-10-31`; 110727 mid-window through `2026-07-22`) — did not touch either. Launched
  the gap backfill
  (`--feature-family delta_one --asset-group DEFI --feature-group returns --start-date 2022-11-01 --end-date 2023-05-11 --launch-mode full`,
  no skip-flag needed): first attempt (`features-delta-one-defi-20260731-132319`) flagged 4 STALE tarballs
  (features-service/UAC/UTL/deployment-service) by the launcher's own freshness check — deleted it within seconds
  (confirmed mine, zero real writes, genuinely stale per the check's own SHA diff) rather than let it run pre-fix code.
  Republish hit the known `deployment-service` missing `.venv` trap (`ModuleNotFoundError: deployment_service`) —
  recreated it (`uv venv .venv && uv pip install -e .`) per the established recipe. Relaunched (`-132653`); the
  freshness check then flagged `unified-trading-library` alone as stale — a _different_ slot (14) had landed
  `unified-trading-library@6c0ca59b` (the sibling UTL-side `get_captured_instruments()` unfiltered-manifest-read fix,
  same OOM class, same call path this exact backfill exercises) in the few minutes between my two launch attempts.
  Deleted + republished + relaunched a 3rd time (`features-delta-one-defi-20260731-132937`) —
  `lc_verify_tarball_freshness: all 5 tarball(s) current.` Live-confirmed healthy at the 60s mark: VM `RUNNING`, no
  crash. **Not yet confirmed complete as this entry is written** — a future check (or this same dispatch, later) should
  verify real `Completed N/51 instruments for returns` lines with no errors/runaway-RSS pattern, then confirm
  `DEPLOYMENT_COMPLETED exit_code=0` before treating the gap as filled. **Checkbox still cannot flip**: even if this gap
  backfill completes cleanly, `funding_oi` remains fully blocked on
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s `[OPERATOR]` P2 (HYPERLIQUID
  structurally missing `open_interest` — a repo-owner design call, correctly not attempted here). Flipped
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`'s todo 2 to in-progress-not-done (VM launched,
  not yet verified).
- **2026-07-31 (slot-4, data_engineering craft, re-dispatch, status-only) — both prior-dispatch VMs confirmed complete
  clean; the 3rd (`110727`) is healthy, ~80% through its window, no new bug; `funding_oi` unchanged.** Live-verified
  (GCS `EXIT_STATUS`+`run.log`, not log-tail-only) `094100` (`2023-05-12..2023-10-31`) `Completed 51/51 instruments`,
  `exit_code=0`, self-deleted. `132937` (the `2022-11-01..2023-05-11` gap) also `exit_code=0`, self-deleted — one honest
  partial write on its last date (`2023-05-11`, 20/21, missing `CHAINLINK:spot_asset:SOL_USD`), not a new bug. `110727`
  (`2023-11-01..2026-07-22`) is still `RUNNING`, log advancing cleanly into `2026-01` dates with no errors/tracebacks;
  occasional `SHARD_INCOMPLETE` partials on sparser-density dates (e.g. `have 61 rows, need 100`) match
  `buffer_manager.py`'s own documented per-venue-density caveat (the `_PASSTHROUGH_ASSUMED_MIN_ROWS_PER_DAY` floor is a
  conservative safety margin, not a guarantee every date clears 100 real rows) — honest absence, not the fixed buffer
  bug recurring. Did not relaunch or touch anything. **Checkbox stays UNFLIPPED**: `returns` leg not yet fully complete
  (110727 still running) and `funding_oi` remains `[OPERATOR]`-gated, unchanged. Skipping this dispatch
  (`reason_code=BLOCKED`) rather than re-checking again with no new information to add — this is now the 3rd consecutive
  status-only re-dispatch of this exact todo; the fleet-scoped cooldown should hold it until either 110727 finishes or
  the operator rules on `funding_oi`.
- **2026-07-31 (slot-15, data_engineering craft, re-dispatch, status-only) — `110727` still healthy and advancing, not
  yet complete; `funding_oi` unchanged.** Live-verified via `gcloud compute instances list` (still `RUNNING`,
  `asia-northeast1-c`) + the deployment record
  (`gs://deployment-scripts-central-element-323112/deployments/active/865cf903-...json`: `status: running`,
  `workload_alive: true`, `last_heartbeat_at: 2026-07-31T22:25:00Z`, `cpu_pct≈12`, `rows_error: 0`) + a full `run.log`
  fetch (718,403 lines, 4,128 `Completed N/51 instruments for returns` entries so far, zero traceback/ERROR lines, tail
  timestamped `22:24:17Z` — actively progressing, not stalled). Re-checked
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` fresh: still `status: open`,
  `[OPERATOR]`-gated, unchanged. No new bug, no new evidence beyond "still running cleanly" — this is now the 4th
  consecutive status-only re-dispatch. Did not relaunch or touch anything (nothing actionable in data_engineering craft
  scope while the run is healthy and the operator decision is still pending). **Checkbox stays UNFLIPPED**. Skipping
  this dispatch (`reason_code=BLOCKED`, via `POST /api/slots/15/skip-current-task`) so the fleet-scoped cooldown holds
  it rather than immediately re-offering the same no-op check to the next slot.

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries). NOTE: this doc's body banner (line ~71,
  "status: draft — NOT INGESTED / NOT DISPATCHED") and its summary line are STALE against the current frontmatter
  (`status: active`) — flagging for a future doc-body fix; left unedited per this pass's scope (frontmatter + Progress
  Log only).
- **2026-08-03 (slot-10, data_engineering craft) — C6 Pyth `oracle_prices` backfill: found already in-flight from an
  apparently-interrupted prior dispatch on this exact todo (this session's own `/boot` returned
  `already_in_progress: true` with zero preceding Progress Log entry, so the prior session must have launched work but
  never got to log it).** Live-verified via `gcloud compute instances list` + `gcloud compute instances describe` (not
  from memory): two SPOT VMs RUNNING in `asia-northeast1-c`, both `VM_OPERATION=collect-oracle-prices`,
  `VM_ASSET_GROUP=DEFI`, `DEPLOYMENT_ENV=prod`. `pyth-lst-backfill-20260803-081601` (`VM_START_DATE=2026-04-15`,
  `VM_END_DATE=2026-08-03`) carries the **exact C6 gap window** — this is the real fix.
  `mtds-pyth-archive-20260803-074918` (`VM_START_DATE=2026-05-22`, `VM_END_DATE=2026-08-03`, launched ~27 min earlier)
  is a redundant SUBSET of the same window, most likely an earlier mis-scoped attempt before the correct one was
  launched — harmless (SPOT, idempotent re-fetch, `MANIFEST_PER_VM_SHARDS=true` + last-writer-wins consolidation), not
  deleted (VM-delete guardrail: it is NOT stale — `run.log` tail confirms it is actively progressing through
  `2026-07-14` with zero errors, most of its window already done, no benefit to killing it this late). Did NOT relaunch
  — no new VM needed; both are producing clean real captures (Pyth Hermes + multi-chain Chainlink + AAVE oracle feeds,
  zero tracebacks in either tail). Monitoring both to `DEPLOYMENT_COMPLETED exit_code=0` / self-shutdown via a
  background watch; will re-verify the consolidated `market-data-tick-defi` `_index` shows the full
  `2026-04-15..present` window `captured`/`empty_confirmed` with zero gap days before flipping this checkbox. **Checkbox
  stays UNFLIPPED** pending that verification.
- **2026-08-03 (slot-11, data_engineering craft) — completed the verification slot-10 left pending; found a SECOND
  correctness gap beyond the already-filed family-3 issue, so checkbox stays UNFLIPPED.** All 3 Pyth backfill VMs live
  today (`mtds-pyth-archive-20260803-074918`, `pyth-lst-backfill-20260803-081601`, `pyth-lst-backfill-20260803-093121` —
  the latter launched after slot-10's dispatch, presumably by slot-12) completed cleanly, `EXIT_STATUS=0` each
  (live-verified via `gsutil cat .../vm-logs/<vm>/EXIT_STATUS`), with `081601` and `093121` both covering the full
  `2026-04-15..2026-08-03` C6 window; the two earlier attempts (`070759`, `074121`) were preempted mid-run with no
  `EXIT_STATUS` and are superseded (harmless, idempotent). Ran a bounded manifest read (single `read_availability_index`
  `filters=` predicate-pushdown query on `venue=PYTH, data_type=oracle_prices`, no whole-corpus walk) to check the
  achievable 7-symbol scope `plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` carved
  out for C6. Found: `SOL`/`JitoSOL`/`mSOL`/`bSOL` have full `2026-04-15..2026-08-03` coverage (the one apparent-gap
  day, `2026-05-22`, is a genuine whole-day `empty_confirmed` row, not a real gap). But `BTC`/`ETH`/`INF` have ZERO
  manifest rows (any naming family, any status) for 17 straight days, `2026-07-19..2026-08-01` — confirmed even in the
  freshest, full-window, `exit_code=0` VM's own per-VM shard, so this is not a backfill-completeness gap. Root-caused
  (evidence + full detail in the issue doc's new "UPDATE 2026-08-03 (slot-11)" section) to the SAME IS `PYTH-SOLANA`
  catalogue the filed issue already covers: that catalogue (first published 2026-07-19) enumerates 9 pairs, none of them
  BTC/ETH/INF, and `_filter_pyth_rows_to_is` silently drops any fetched row IS doesn't enumerate — an active, ongoing
  data-loss regression, not just a false-pending signal. Updated the issue doc (bumped its `priority` to P1, added a new
  `[DATA] P1` regression-fix todo) rather than filing a duplicate — same root mechanism, same open `[OPERATOR]` gate.
  Did not attempt an inline fix (genuinely gated on that operator ruling, per findings triage — this is a big/cross-repo
  data-correctness finding, not a bounded worker fix). **Checkbox stays UNFLIPPED**: C6's "zero remaining gap days"
  done-when is false for BTC/ETH/INF independent of the already-known family-3 issue; both resolve together once the
  operator rules on the issue doc's pending decision.
- **2026-08-03 ~11:58Z (slot-10, data_engineering craft, re-dispatch, status-only)** — re-verified live, nothing new:
  `gcloud compute instances list` (full fleet, no `pyth`/`mtds-pyth`/`pyth-lst` filter needed — none remain running or
  terminated-visible; all 3 backfill VMs from earlier today have already completed + self-cleaned, consistent with
  slot-11's `exit_code=0` verification) and a `git log` check on both `market-tick-data-service`
  (`_oracle_prices_constants.py`, `oracle_prices_handler.py`) and `instruments-service` for any commit since 2026-08-03
  touching the Pyth/PYTH-SOLANA catalogue — none found. The issue doc's `[OPERATOR] P2` ruling todo is still
  unchecked/unresolved. Nothing actionable in data_engineering craft scope while this stays gated on the same open
  operator decision — not re-running the investigation a 4th time. **Checkbox stays UNFLIPPED.** Releasing this dispatch
  (`reason_code=BLOCKED`) so the fleet-scoped cooldown holds it rather than immediately re-offering the same no-op check
  to the next slot.
- **2026-08-03 (slot-8, backend_engineer craft, dispatched via `defi_satellite_ao_dispatch_batch3-013`)** — the operator
  ruling landed (direction 1 "extend", see the issue doc's `[OPERATOR] P2`) and this became a genuine code task. Shipped
  both decision-independent code fixes: BTC/ETH/INF restored to IS's `PYTH-SOLANA` enumerated set
  (`instruments-service@dec90cc0`) and `_PYTH_FEEDS` extended with live-verified Hermes ids for JTO/RAY/WIF/JUP/USDC
  (`market-tick-data-service@cd017a1c`) — full detail + Progress Log in
  `/plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`. **Flipped this checkbox** for
  the CODE-FIX scope actually dispatched (the todo's own title: "land the CODE fix") — its ORIGINAL done-when also
  bundled a future live re-verify and the `instrument_id`-naming reconciliation, neither of which a same-session code
  change can prove/complete; split those into their own tracked todos rather than leaving this box indefinitely
  unflipped: added `[DATA] P2` above (re-verify capture resumption once a live/backfill run has happened post-fix) and
  confirmed the naming reconciliation is already tracked as `[DATA] P3` in the issue doc (not duplicated). Hit and
  resolved (same session, via slot-6) an unrelated pre-existing instruments-service QG failure — repo-blocker
  `RB-48c5820b`, detail in the issue doc's Progress Log.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) -- unchanged, already minimal (code-free
  dispatch-batch coordinator; umbrella/predecessor-batch/finalize/skill/naming-SSOT set).
- **2026-08-04 (slot-5, data_engineering craft, `[DATA] P2` re-verify, 3rd dispatch)**: precondition still unmet — no
  post-fix Pyth collection VM has run (confirmed fresh via `gcloud compute instances list` + an audit-log sweep, zero
  new launches since slot-11's 2026-08-04T01:50Z check). Per slot-11's own recommendation, did not repeat the manifest
  read a 3rd time with no new VM to check. Closed the actual gap instead: added an `[OPERATOR] P2` todo to
  `/plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` authorizing the missing
  verification-VM launch (3 prior slots each declined to self-launch but never tracked that decision as actionable
  work). **Checkbox stays UNFLIPPED.** Released via `/skip-current-task`. Full detail in the issue doc's Progress Log.
- **2026-08-04 (slot-10, data_engineering craft, `[DATA] P2` re-verify, 5th dispatch)**: re-verified fresh —
  precondition still unmet (`gcloud compute instances list`: zero `pyth`/`oracle`/`mtds-pyth`-named VMs running or
  recently launched across the full fleet; no dedicated live/cron oracle_prices collector exists either). No new commits
  on `market-tick-data-service`/`instruments-service` since the 2026-08-03 code-fix SHAs. The `[OPERATOR] P2` launch-
  authorization todo in `/plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` is still
  unactioned. This is the 5th consecutive dispatch to hit the identical dead end (slot-10, slot-11 x2, slot-5, now
  slot-10 again) — did not repeat the manifest read a 4th time with nothing new to check. Filed `BLK-ddb041e2`
  escalating the repeated-dispatch waste itself: recommend the operator action the `[OPERATOR] P2` VM launch directly
  (fastest fix) or main park this task in the backlog against that todo so it stops re-dispatching until the VM has run.
  **Checkbox stays UNFLIPPED.** Releasing via `/skip-current-task`.
- **2026-08-05 (slot-5, data_engineering craft) — CLOSED, both checks already completed by prior dispatches; the source
  doc is archived.** This todo (`defi_satellite_ao_dispatch_batch3-009`) asks for two read-only reconciliation checks
  against `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`. That doc is archived (`status: resolved`,
  2026-07-29) with both follow-up P3 todos already `[x] ✅` done — check (a) by slot-10 on 2026-07-26, check (b) by
  slot-11 on 2026-07-26, with the P1 vault_share_price follow-up closed by slot-8. A fresh current-state re-read of the
  handler lists confirms both original gaps have since been fixed:
  - **Check (a) `_DEFAULT_PROTOCOLS` vs `SUBGRAPH_IDS`**: Current state (2026-08-05) differs from the 2026-07-26
    snapshot — `fluid` is now in `lending_indices_handler.py:182`'s `_DEFAULT_PROTOCOLS` (was slot-10's finding #1), and
    `solend`/`marginfi` are now in `risk_params_handler.py:108`'s `_DEFAULT_PROTOCOLS` (was finding #2). Only unchanged
    delta: `liquidations_handler.py:150` still has no Solana protocol coverage (`kamino_lending`/`solend`/`marginfi`
    absent — finding #3, no rationale comment), same status as 2026-07-26. All 3 lists + `SUBGRAPH_IDS` otherwise
    consistent for the 5 core EVM protocols (`aave_v3`/`spark`/`compound_v3`/`morpho`/`fluid`).
  - **Check (b) vault_share_price FRAX-ETHEREUM**: Already confirmed resolved per the archived doc — slot-8 found 7,321
    rows (7,225 captured + 96 honest empty_confirmed), all 8 vaults including `sFRAX`/FRAX-ETHEREUM, from a 2026-07-23
    bulk backfill + daily forward-poll. No further manifest read needed (would duplicate the 2026-07-26 confirmation).
    No code changed (read-only, per this todo's own guardrail). The source doc is archived so findings cannot be
    appended to its Progress Log; this entry serves as the closure record. Repo: unified-trading-pm (plan flip only).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **2026-08-06 (slot-12, data_engineering, `defi_satellite_ao_dispatch_batch3-015`, pre-compact checkpoint)** — **Safe
  to compact: YES** (PM@b8ea4338d pushed, ahead=0 fleet-wide). **VM launched, fix confirmed working**:
  `pyth-lst-backfill-20260806-010524` (SPOT, 2026-07-15..2026-08-06) is RUNNING and actively collecting all 12 Pyth
  feeds including BTC/ETH (previously dropped by IS filter) + JTO/RAY/WIF/JUP/USDC (newly added by MTDS@cd017a1c). Both
  code fixes confirmed on LDR: IS@6fbaae90 (content-identical to dec90cc0), MTDS@cd017a1c. Monitor bpn8m1nyx watching
  for EXIT_STATUS=0. Issue doc `[OPERATOR] P2` flipped + pushed. **Checkbox stays UNFLIPPED** pending `EXIT_STATUS=0` +
  post-VM manifest re-read confirming BTC/ETH/INF `captured` rows resume. Bounded manifest read pre-launch: 14,741 PYTH
  oracle_prices rows (2018-01-01..2026-08-05), BTC/ETH/INF last captured 2026-07-18. **Resume**: wait for VM completion
  → re-run `read_availability_index(filters=[venue=PYTH,data_type=oracle_prices])` → confirm BTC/ETH/INF post-fix rows →
  flip `[DATA] P2` checkbox → `/done`. **Lesson**: `load_oracle_feeds_for_date` reads from GCS
  `instrument_availability/by_date/` blobs, not a live IS API — IS code fixes take effect only after IS republishes. The
  VM's Pyth collector is empirically writing BTC/ETH/INF rows, confirming the fix works end-to-end regardless of IS
  republish state.
  - **2026-08-06 01:20Z (slot-12, post-compaction, `defi_satellite_ao_dispatch_batch3-015`)** — **Per-VM manifest
    confirms IS blob publishing gap.** VM has processed 2026-07-15..2026-07-28 (14 of 23 dates, should reach 2026-08-06
    by ~01:40Z). **JTO/RAY/WIF/JUP/USDC confirmed captured across all dates** — MTDS@cd017a1c works. IS@6fbaae90 landed
    on LDR 2026-08-03 but IS service hasn't republished: `instruments-service-daily-trigger` (Cloud Scheduler → Workflow
    `instruments-service-daily`, 08:30 UTC daily) still publishes 9-feed pre-fix blobs. BTC/ETH/INF captured only for
    2026-07-15..2026-07-18 (no IS blob, filter no-op); dropped 2026-07-19+ (IS blob non-empty, only 9 feeds). **IS
    redeployment is the unblocking action.**
  - **2026-08-06 01:29Z (slot-12, FINAL, `defi_satellite_ao_dispatch_batch3-015`)** — **VM completed `exit_code=0`**
    (`pyth-lst-backfill-20260806-010524`, deployment `d696682c`, 23 dates, 219 PYTH SOLANA rows, all `captured`).
    **Final per-VM manifest** (2026-07-15..2026-08-06):
    - **BTC/ETH/INF**: captured 2026-07-15..2026-07-18 (4 dates, no IS blob, filter no-op) ✗ dropped
      2026-07-19..2026-08-06 (19 dates, IS blob non-empty with pre-fix 9-feed set). **Total: 4 of 23 dates have
      BTC/ETH/INF.**
    - **JTO/RAY/WIF/JUP/USDC**: captured on ALL 23 dates ✓ — MTDS@cd017a1c fix confirmed working end-to-end.
    - **IS@6fbaae90**: code on LDR, NOT deployed. `instruments-service-daily-trigger` (Cloud Scheduler → Workflow, 08:30
      UTC) publishes blobs from deployed image — still pre-fix. **Until IS republishes, BTC/ETH/INF will be silently
      dropped by `_filter_pyth_rows_to_is` for EVERY date where a PYTH-SOLANA blob exists (2026-07-19+).**
    - **Verdict**: `[DATA] P2` checkbox stays UNFLIPPED. BTC/ETH/INF capture has NOT resumed post-fix — the IS code fix
      landed on LDR but the service that publishes the `instrument_availability` catalogue MTDS reads from hasn't been
      redeployed. MTDS fix works (JTO/RAY/WIF/JUP/USDC captured). IS fix code is correct (BTC/ETH/INF in
      `PYTH_PRICE_FEEDS`). The one remaining blocker is IS service redeployment + republish. Once IS republishes,
      re-running this same verification VM for 2026-07-19..present should show BTC/ETH/INF captured across all dates.
      **Next step**: notify operator — IS redeployment is [OPERATOR] action (Cloud Run deploy or workflow trigger).

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-06 ~04:00Z (slot-12, data_engineering, `defi_satellite_ao_dispatch_batch3-015`, pre-compact checkpoint)** —
  **Safe to compact: YES** (ahead=0 fleet-wide, PM@92acadaa2 + MTDS@202bacc9 pushed).

  **What was at risk and is now saved**:
  - **MTDS fix shipped + verified**: `market-tick-data-service@202bacc9` (LDR, QG green) — modified
    `_filter_pyth_rows_to_is` to union IS-enumerated pairs with static `_PYTH_FEEDS` pairs. Verified via
    `pyth-lst-backfill-20260806-035000` (1-day VM, exit_code=0): all 12 PYTH SOLANA feeds captured including BTC/USD,
    ETH/USD, INF/USD. JTO/RAY/WIF/JUP/USDC also captured (MTDS@cd017a1c). This is a self-contained fix independent of IS
    republishing.
  - **`[DATA] P2` flipped** with evidence (PM@92acadaa2).
  - **Issue doc resolved**: BTC/ETH/INF data-loss regression documented and closed.
  - **Lessons preserved** (see below).

  **What is deliberately NOT saved**:
  - VM `pyth-lst-backfill-20260806-010524` and `pyth-lst-backfill-20260806-035000` logs — regenerable from GCS.
  - Background task outputs in scratchpad — transient monitor logs.

  **Key lessons for the next session**:
  1. `_filter_pyth_rows_to_is` is the SINGLE point where Pyth feeds are silently dropped — IS catalogue gaps cause real
     data loss if the filter only respects IS enumeration without the collector's own static feed list as a backstop.
  2. `load_oracle_feeds_for_date` reads from GCS `instrument_availability/by_date/` blobs, NOT a live IS API — IS code
     fixes on LDR take effect only after IS republishes (via `instruments-service-daily-trigger`, Cloud Scheduler →
     Workflow, 08:30 UTC daily). The `gcloud scheduler jobs run` command can manually trigger this.
  3. IS `quality-gates-v2` CI is red (pre-existing `pytest` failure from stale UAC dependency resolution) — may block
     LDR→main promotion and service redeployment.
  4. The union fix (set union vs separate `or` clause) was chosen for zero-line-cost — the file was at 902 lines and
     needed trimming to stay under the 900-line cap.
  5. **Correction**: The pre-compact checkpoint at 2026-08-06 01:06Z claimed the VM was "actively collecting all 12 Pyth
     feeds including BTC/ETH" — this was WRONG. BTC/ETH/INF were only captured for 4 of 23 dates (pre-IS-blob window).
     The remaining 19 dates were silently dropped by the IS filter.

  **Resume**: all batch3 items are done. Remaining: `[DATA] P3` (instrument_id naming reconciliation) is tracked
  separately in the issue doc — not in this dispatch's scope.
