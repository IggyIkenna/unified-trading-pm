---
title:
  DeFi recursive-borrow archetypes — Family 1 (recursive lending arb) + Family 2 (long-funding-perp recursive-borrow)
  implementation
type: implementation
status: planned
created: 2026-05-10
author: ikenna
operator: ikenna
target_deadline: 2026-05-23
horizon: pre-cutover
companion_to: plans/active/master_to_live_defi_2026_05_23.md
spawned_from: plans/questions/defi_recursive_borrow_archetypes_2026_05_08.md
related_plans:
  - plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - plans/active/defi_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/issues/defi_archetypes_doc_plan_drift_2026_05_07.md
related_codex:
  - codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md
  - codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md
  - codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md
  - codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md
  - codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md
  - codex/04-architecture/flash-loan-receiver.md
  - codex/09-strategy/strategy-summary.md
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# DeFi recursive-borrow archetypes — Family 1 + Family 2 implementation

## Why this plan exists

Two recursive-borrow strategy families surfaced in
[`plans/questions/defi_recursive_borrow_archetypes_2026_05_08.md`](../questions/defi_recursive_borrow_archetypes_2026_05_08.md):
**Family 1** = pure-lending recursive arb (no perp leg) and **Family 2** = long-funding-perp recursive-borrow
(delta-neutral on share-class = underlying coin). Research on 2026-05-09 (4 parallel sub-agent streams: archetype audit,
MTDS rate coverage, web rate-sampling, on-chain flow-of-funds + workspace primitives) established that both families are
CONFIG VARIANTS of the existing `CARRY_RECURSIVE_STAKED` archetype — extending the 2026-05-07 operator precedent that
`leveraged_funding_arb` = config variant of `ARBITRAGE_PRICE_DISPERSION`. No new archetype enum; no new strategy-service
factory tree; no parallel codex docs.

The research also caught a framing gap in the original Q-doc: the user's spec ("borrow coin → short borrowed coin on
perp") is mechanically broken on Hyperliquid / Bybit / OKX (USDC-only margin). The correct shape: **recursion is purely
on the lending side**; the perp short is a single matched leg sized against cumulative spot-ETH exposure post-recursion,
with margin separately funded in USDC. Share-class accounting netted across (aETH + free-ETH + ETH-debt + perp-short) =
configurable target net delta (0 for pure carry, +N×base for "hold N ETH and earn carry").

Implementation is gated by a backfill prerequisite: lending-rate data (SUPPLY_APY / BORROW_APY / UTILISATION) is not yet
captured by MTDS due to 3 known bugs (Aave V3 Eth silent-zero / Compound V3 multi-chain subgraph / instruments-store
2022 metadata floor), per the `lending-indices DEFERRED` note in
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md).
Without that data, backtest is impossible and paper-trade smoke against historical funding regimes is impossible. Phase
1 ships the prerequisite; the rest of the plan compounds on top.

**Total budget**: ~17 AI-days end-to-end (Phase 1 backfill prerequisite + Phases 2-13 for both families). Family 1 alone
is ~11 AI-days (subset); Family 2 alone is ~14 AI-days. Combined plan reuses orchestrator + flash-receiver +
health-monitor across both, which is why the bundle is cheaper than the sum. This sits well within the May-23 cutover
window if Phase 1 starts immediately.

## Architectural decisions (locked from 2026-05-09 research)

> **AD-1 — FLIPPED 2026-05-10 cross-plan audit Q10 (Policy B larger-set-wins).** Both families = **NEW UAC
> `StrategyArchetype` enum members** (extending from 8 → 11 archetypes; was originally "config variants of
> `CARRY_RECURSIVE_STAKED`" — that approach REJECTED in favor of explicit enum members per the larger-set rule + to
> match codex doc Stream C "all 11 archetypes" language). UAC PR owned by
> [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
> Stream C (per Q10 most-comprehensive-owner ratification; Stream C already ships the codex doc backport for "all 11
> archetypes" so the enum-extension PR is the natural co-shipment). Strategy-service factory routing updates to dispatch
> per archetype enum member (not per config-variant lookup). Justification for the flip: explicit enum is clearer for
> downstream consumers (deployment-UI archetype dropdown, allocator subclass routing, kill-switch per-archetype scoping,
> archetype-readiness matrix per master plan); config-variant shape conflates orthogonal axes (`perp_leg_enabled` is a
> structural difference, not a config tuning knob). Justification for original AD-1: the recursion mechanics, share-class
> semantics, and kill-switch surface (drawdown 0.05 / breach 0.03 per
> [`archetype_config.py:169-177`](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_config.py#L169-L177))
> were thought identical — but Family 2's perp leg adds a distinct risk surface (funding-sign-flip, perp-venue outage,
> cross-venue delta drift) that warrants explicit enum-level visibility. Family 1 = new enum member
> `CARRY_RECURSIVE_BORROW_LENDING_ONLY`; Family 2 = new enum member `CARRY_RECURSIVE_BORROW_PERP_HEDGED`. Plus one more
> archetype TBD by Stream C (the third of the 8→11 expansion — TBD in Stream C UAC PR).

> **AD-2**. The recursion is **purely lending-side**. Perp leg (Family 2) is a single matched short, separately
> USDC-margined. Hyperliquid / Bybit / OKX are USDC-margin-only — borrowed ETH cannot be posted as perp margin without
> selling. The strategy-service config schema enforces this shape; the orchestrator never tries to bridge borrowed coin
> into perp margin.

> **AD-3**. Share class is configurable per instance via `target_net_delta` (in units of share-class coin).
> `target_net_delta=0` = full hedge, NAV-in-ETH; `target_net_delta=+1.0` = "hold 1 ETH and earn carry on top."
> `LeveragedLegController` (already in workspace per canonicalisation plan) abstracts the rebalance loop. Share-class
> coin defaults to the lending-side collateral asset (ETH for ETH-loops, BTC for BTC-loops, SOL for SOL-loops).

> **AD-4**. Two opening modes ship together: `mode="persistent"` (N tx, no flash fee, gas-bound) and `mode="flash"` (1
> tx, 0.05% Aave V3 flash fee, atomic). Persistent is the default below 5 ETH base capital; flash is the default at ≥5
> ETH (gas-cost crossover). Both modes share the same `RecursiveLoopOrchestrator` interface — only the inner driver
> differs.

> **AD-5**. **Multi-venue scope is explicitly bounded for May-23**. Lending side: Aave V3 only (Ethereum mainnet
> primary, Base secondary). Perp side: Hyperliquid (DEX) + Bybit (CeFi) — two venues only. Other lending protocols
> (Compound V3, Spark, Morpho, Maker DSR) and other perp venues (Binance, OKX, Deribit, Aster) are deferred to a
> post-cutover follow-up plan. Solana / Marginfi / Kamino is deferred entirely (separate plan, post-Family-2-on-EVM
> proves out the architecture).

> **AD-6**. **Backtest is the gate, not paper-trade**. Per `master_to_live_defi_2026_05_23.md` Group F item 18 (2-year
> batch backtest run) — Phase 1 backfill must finish before Phase 12 backtest can produce signal. Without backtest
> signal, paper-trade smoke is rate-limited (no historical funding-regime coverage). Phase 1 is therefore P0 and must
> start day-1.

## Cross-plan coordination banners

Add these banners (per CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE) to the top of the named plans BEFORE Phase
1 starts:

- [ ] **[BANNER]** `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` — top-of-file banner:
      `🟡 IN-FLIGHT REFACTOR — recursive-borrow plan     (defi_recursive_borrow_archetypes_2026_05_10.md) is consuming the lending-indices DEFERRED note as a P0 prerequisite. RE-VERIFY before flipping the     DEFERRED checkbox to ✅ — the recursive-borrow plan needs ≥1y of historical Aave V3 / Compound V3 lending data to backtest.`
- [ ] **[BANNER]** `master_to_live_defi_2026_05_23.md` — Group F item 18 (2-year batch backtest run) gets a sub-bullet
      pointing at this plan; Group F item 17 (real gas / matching engine / cost+yield precision) gets a sub-bullet
      pointing at Phase 9.
- [ ] **[BANNER]** `defi_master_2026_05_07.md` — top-of-file banner declaring this plan as the canonical implementation
      track for recursive-borrow archetypes.
- [ ] **[BANNER]** `alerting_service_live_rules_2026_05_07.md` — top-of-file banner pointing at Phase 8
      (HealthFactorMonitor + LiquidationProximityCircuit) as a new alerting consumer with kill-switch tier-up
      integration requirements.

Banner-removal owned by this plan when each phase ships; stale-banner sweep at end-of-plan.

## Pre-audit — full workspace impact surface

Per CLAUDE.md "Plans must capture full codebase impact upfront" + Citadel § 1 Pre-Audit. Every repo / file / SSOT
touched by this plan, enumerated.

| Repo / surface                     | Files touched                                                                                                                                                                                                                                                                                             | Phase     |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `unified-api-contracts`            | `internal/architecture_v2/archetype_config.py` (extend `CARRY_RECURSIVE_STAKED` config schema); `canonical/domain/market_data/data_types.py` (new `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` enums)                                                                                                      | 2, 1      |
| `unified-trading-library`          | (read-only consumer; no edits expected)                                                                                                                                                                                                                                                                   | -         |
| `market-tick-data-service`         | `adapters/aave_v3_lending_rates.py` (new); `adapters/compound_v3_lending_rates.py` (new); `adapters/morpho_blue_lending_rates.py` (NICE-TO-HAVE); fix Bug 1/2/3 per Phase 1                                                                                                                               | 1         |
| `instruments-service`              | catalog seed for lending-rate instruments per (protocol, chain, asset); 2022 metadata floor fix per Bug 3                                                                                                                                                                                                 | 1         |
| `execution-service`                | `defi_execution/protocols/aave.py` (already has supply/borrow/repay/withdraw/flash); `defi_execution/protocols/hyperliquid.py` (LIVE wire-up — currently simulation-only); new `RecursiveLoopOrchestrator`; new `PerpHedgeSizer`; new `HealthFactorMonitor`; matching-engine DeFi cost model              | 5,6,7,8,9 |
| `strategy-service`                 | `engine/strategies/v2/factory.py` (config-variant routing); `engine/strategies/v2/target_universe/catalog.py` (extend `_build_carry_recursive_staked` factory); `LeveragedLegController` extension                                                                                                        | 3         |
| `position-balance-monitor-service` | cross-venue netting verification (Aave aETH + Aave debt + perp short → share-class delta); no new code expected, just integration test                                                                                                                                                                    | 7         |
| `risk-and-exposure-service`        | concentration-risk handling for recursive positions; gross-notional vs net-delta per Q-doc G1                                                                                                                                                                                                             | 8         |
| `alerting-service`                 | new alert codes (`HEALTH_FACTOR_CRITICAL`, `LIQUIDATION_IMMINENT`, `FUNDING_SIGN_FLIP`); kill-switch tier-up rules                                                                                                                                                                                        | 8         |
| `deployment-service`               | extended `FlashLoanReceiver.sol` (or new `RecursiveLeverageReceiver.sol`); `scripts/vm/launch-defi-recursive-borrow-vm.sh` (new launcher per VM-launcher-SSOT rule)                                                                                                                                       | 4, 13     |
| `deployment-api`                   | `/data-status/recursive-borrow-coverage` endpoint; ArchetypeMatrix variant rendering                                                                                                                                                                                                                      | 11        |
| `deployment-ui`                    | ArchetypeMatrix entry for both variants; HealthFactorMonitor live tile; Recursive-Borrow data-status drilldown                                                                                                                                                                                            | 11        |
| `features-onchain-service`         | per-protocol rate-feature consumer; cross-protocol rate-spread feature                                                                                                                                                                                                                                    | 10        |
| `unified-config-interface`         | `testnet_contracts.yaml` (extended-receiver address per chain); RPC URL templates already in `_defi.py`                                                                                                                                                                                                   | 4         |
| `unified-trading-pm/codex/`        | new doc `codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked-config-variants.md`; update `codex/04-architecture/flash-loan-receiver.md`; update `carry-recursive-staked.md` to cite variants; update `codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` for new venue rows | 10        |
| `e2e-testing/scripts/defi/`        | new `recursive_borrow_paper_smoke.py` paper-trade harness (under primary-consumer QG of strategy-service per peripheral-script-dirs HARD RULE)                                                                                                                                                            | 12        |
| `unified-trading-pm/plans/active/` | this plan (durable record); flips on `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` + `master_to_live_defi_2026_05_23.md` Group F items                                                                                                                                                | all       |

## Phase 0 — Decision lock + Q-doc closeout (0.5 AI-days)

- [ ] [PM] P0. Update
      [`plans/questions/defi_recursive_borrow_archetypes_2026_05_08.md`](../questions/defi_recursive_borrow_archetypes_2026_05_08.md):
      set `status: closed-spawned-plan`, `spawned_plan: plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`,
      append a "Research summary 2026-05-09" section with the 4 sub-agent reports' headline findings + AD-1 through AD-6
      decision calls.
- [ ] [PM] P0. Add cross-plan coordination banners per the section above (4 banners).
- [ ] [operator-ratify] P0. Operator confirms AD-1 through AD-6. (Not gating Phase 1 — Phase 1 is the lending-indices
      fix that's needed regardless of archetype shape — but gating Phase 2 onwards.)

**Done definition:** Q-doc closed; banners landed; AD-1 through AD-6 ratified.

**Full-execution criterion:** Q-doc commit references AD-1 through AD-6; 4 banners visible at top of named plans;
operator ack visible in chat or commit co-authoring metadata.

## Phase 1 — Prerequisite: lending-rate backfill — REFRAMED 2026-05-10 cross-plan audit Q11

> **🔴 OWNERSHIP TRANSFERRED** to [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md)
> Phase 1 (UAC SSOT) + Phase 3 (MTDS adapter rewrites + Bug 1/2/3 fixes + production backfill VM). Catalogue plan is the
> comprehensive multi-protocol/multi-chain UAC + MTDS scope (most-comprehensive-owner rule); this plan was carrying
> duplicate scope. Phase 1 here becomes a **PASSIVE BLOCKER GATE**: recursive-borrow Phase 9 (backtest) blocks on
> defi_catalogue Phase 3 shipping. Banner the catalogue plan with
> `🔴 BLOCKER FOR recursive-borrow Phase 9 — lending-indices data must be backfilled ≥1y of historical Aave V3 + Compound V3 before recursive-borrow backtest can produce signal`.
> The original Phase 1 todo content below is RETAINED only as a checklist for the catalogue plan agent (who will fold
> these specific items into catalogue Phase 1/3) — but the todos themselves DO NOT execute here. Catalogue plan owns
> ship + verify; this plan consumes via Phase 9 backtest replay.

**Reframed Phase 1 done definition (this plan's POV)**: catalogue plan Phase 3 manifest reports `captured` for Aave V3
Ethereum + Compound V3 Ethereum/Arbitrum/Base SUPPLY_APY / BORROW_APY / UTILISATION across 2022-03-01 → present at
day-grain; sample parquet probe confirms non-zero rates per day; instruments-service catalog reports the corresponding
instrument-day rows as alive. **Then** this plan's Phase 2+ unblocks.

(Original Phase 1 detail retained below as spec hint for catalogue plan; do NOT execute these here.)

The `lending-indices DEFERRED` note in
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
blocks backtest. Three bugs + missing data_type enums + adapter rewrites + production backfill VM. Aave V3 Ethereum +
Compound V3 Ethereum/Arbitrum/Base are P0 for May-23 (Family 1 wedges + Family 2 borrow leg); Spark + Morpho + Maker DSR
are P1 (extends viable wedge set, not gating).

- [ ] [UAC] P0. Add `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` / `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` to
      `data_type` enum in `canonical/domain/market_data/data_types.py`. Update `BUNDLED_DATA_TYPES` if any of these are
      bundled per protocol (utilisation per pool may be). Wire into manifest schema column `data_type` validation.
- [ ] [MTDS] P0. **Bug 1 fix** — Aave V3 Ethereum silent-zero. Audit the Aave adapter: when subgraph returns zero rows,
      current behaviour writes `empty_confirmed`. Per CLAUDE.md "Honest absence vs fake placeholders" rule — should be
      `attempted_failed` if catalog says alive. Add
      `record_failed(UpstreamSubgraphZeroError(observed_dates, expected_day))` route + reason taxonomy entry.
- [ ] [MTDS] P0. **Bug 2 fix** — Compound V3 multi-chain subgraph schema. Diff the schema across chains (Ethereum /
      Arbitrum / Base / Polygon / Optimism); either normalise via per-chain query templates OR fail-fast with a typed
      `CompoundSubgraphSchemaMismatchError` per chain.
- [ ] [instruments-service] P0. **Bug 3 fix** — `instruments-store-defi` 2022 metadata floor. Backfill the missing
      pre-2022 metadata for Aave V3 + Compound V3 pool instruments. Verify via `record_captured` rows present for
      2020-01-01 onwards (Aave V3 launch ≈ 2022-03; pre-launch days
      `record_expected_empty(reason=EXPECTED_PRE_VENUE_LAUNCH)`).
- [ ] [MTDS] P0. New adapter: `aave_v3_lending_rates.py` — emits `SUPPLY_APY` + `BORROW_APY` + `UTILISATION` per (chain,
      asset) at minute / hour cadence. Sources: Aave V3 subgraph (primary) + Aavescan API (cross-check). Cluster
      validation per `(chain, day)` for bundled multi-asset reads.
- [ ] [MTDS] P0. New adapter: `compound_v3_lending_rates.py` — same shape, Compound V3 subgraph per chain.
- [ ] [MTDS] P1. New adapter: `morpho_blue_lending_rates.py` — per-market isolated rates. Morpho Blue is per-market, so
      the row_key is `(chain, market_id)`.
- [ ] [MTDS] P1. New adapter: `spark_lending_rates.py` — Spark is Aave fork; reuse Aave adapter shape with Spark
      subgraph endpoint.
- [ ] [MTDS] P2. New adapter: `maker_dsr_rate.py` — single rate stream from MakerDAO contract / subgraph. NICE-TO-HAVE;
      not blocking May-23.
- [ ] [SCRIPT] P0. Manifest reconciler one-shot: `instruments-service/scripts/reconcile_lending_indices_phantom.py` —
      apply CLAUDE.md manifest-phantom-audit pattern, classify any pre-existing `empty_confirmed` rows that should be
      `attempted_failed` post-Bug-1-fix.
- [ ] [VM] P0. Backfill VM: `deployment-service/scripts/vm/launch-defi-lending-indices-backfill-vm.sh` (per
      VM-launcher-SSOT rule). Per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true`). Window: 2022-03-01 → today, hourly
      granularity, Aave V3 (Eth/Base/Arb) + Compound V3 (Eth/Base/Arb) primary; Spark + Morpho + Maker DSR as P1
      follow-up VMs. Register VM-name prefix `defi-lending-` in `VM_PREFIX_TO_BUCKET` per zombie-watchdog rule.
- [ ] [VM] P0. Run-to-completion: launch the VM, monitor STARTED → progress → STOPPED via event stream
      (`gs://{pid}-events/events/mtds/...`), verify manifest `captured` rows for the full window via spot-check on a
      sampled `(protocol, chain, asset, day)` parquet (assert non-NaN supply_apy + borrow_apy populated). Per CLAUDE.md
      "Plans Run To Actual Completion" — not just launch + done; verify run-to-completion.

**Done definition:** UAC has the 4 new data_type enums; 3 bugs fixed; 2 P0 adapters shipped (Aave V3 + Compound V3); P1
adapters land in same phase or are explicitly deferred-to-named-successor-plan; reconciler runs and reports clean delta;
backfill VM run-to-completion with verified parquets; manifest shows `captured` for ≥1y of (Aave V3 Eth / Aave V3 Base /
Compound V3 Eth) × {USDC, USDT, ETH, wstETH, WBTC} hourly data.

**Full-execution criterion:**

- ✅ Backfill VM ran to STOPPED state with no `attempted_failed` rows beyond the Bug-1-fix-reclassified set.
  - **What ran**:
    `bash deployment-service/scripts/vm/launch-defi-lending-indices-backfill-vm.sh --start 2022-03-01 --end 2026-05-09`
    on a same-region GCE VM.
  - **Verification**: `gcloud storage ls gs://${PID}-events/events/mtds/2026-05-1*/defi-lending-*/` shows STARTED +
    STOPPED; manifest spot-check via
    `python -c "from market_tick_data_service.manifest import read_canonical; m = read_canonical(asset_group='defi'); print(m.coverage_pct(data_type='SUPPLY_APY'))"`
    returns ≥99% for the P0 protocol/chain/asset cube.

## Phase 2 — UAC config schema extension (1 AI-day)

- [ ] [UAC] P0. Extend `CARRY_RECURSIVE_STAKED` config in `internal/architecture_v2/archetype_config.py` with:
      `perp_leg_enabled: bool`, `perp_venue: PerpVenue | None`, `target_net_delta: Decimal` (units of share-class coin),
      `recursion_depth_max: int`, `safety_buffer_ltv: Decimal`, `opening_mode: Literal["persistent", "flash"]`,
      `usdc_margin_buffer_min: Decimal`, `lending_protocol: LendingProtocol` (Aave V3 / Compound V3 / etc.).
- [ ] [UAC] P0. New helper enum `LendingProtocol` (AAVE_V3 / COMPOUND_V3 / SPARK / MORPHO_BLUE / MAKER_DSR) in
      `canonical/crosscutting/defi.py`. Source-of- truth for which protocols a strategy can target.
- [ ] [UAC] P0. New helper enum `PerpVenue` extension or reuse existing `Venue` — pick one based on what's already
      there. Default: reuse `Venue` filtered by capability `SUPPORTS_PERP=True` per UAC capability_declarations.
- [ ] [UAC] P0. Backfill default values for existing `CARRY_RECURSIVE_STAKED` instances (set `perp_leg_enabled=True`,
      `perp_venue=Hyperliquid`, `target_net_delta=0`, `lending_protocol=AAVE_V3`, `opening_mode="persistent"`) so
      nothing breaks. Migration is a 1-line `model_config.populate_by_name` change + per-instance default in catalog.
- [ ] [UAC] P0. Schema test: round-trip `archetype_config.from_dict(json)` for both Family 1 (perp_leg_enabled=False)
      and Family 2 (perp_leg_enabled=True) configs.

**Done definition:** UAC schema accepts both Family-1 and Family-2 configs; existing CARRY_RECURSIVE_STAKED instances
continue to round-trip; QG green on UAC.

**Full-execution criterion:** UAC `bash scripts/quality-gates.sh` green on commit; round-trip test fixtures committed
under `tests/internal/unit/test_carry_recursive_staked_config_variants.py`.

## Phase 3 — strategy-service factory + target-universe catalog (2 AI-days)

- [ ] [strategy-service] P0. Extend `_build_carry_recursive_staked` in `engine/strategies/v2/target_universe/catalog.py`
      to consume the new config fields (Phase 2). Branch on `perp_leg_enabled`: when True, emit (lending_leg,
      perp_short_leg) tuple; when False, emit (lending_leg) only.
- [ ] [strategy-service] P0. `LeveragedLegController` extension: accept `target_net_delta` parameter and rebalance by
      trimming or extending the perp leg to match. Keep the existing `target_leverage` parameter for the lending side;
      the two parameters compose orthogonally.
- [ ] [strategy-service] P0. New target-universe variants: `CARRY_RECURSIVE_STAKED__lending_arb_pure` (Family 1) and
      `CARRY_RECURSIVE_STAKED__perp_funding_capture` (Family 2). Variant naming per existing precedent (`__` separator);
      each variant maps to a config preset.
- [ ] [strategy-service] P1. Tracer extension: `defi_carry_recursive_staked_decision_trace.py` already has
      `_net_apr_recursive(stake_apy, borrow_apy, ltv, n_loops)` at line 210 — reuse for Family 1; add
      `_net_apr_with_perp_funding(stake_apy, borrow_apy, perp_funding, ltv, n_loops, target_net_delta, usdc_idle_apy)`
      for Family 2.
- [ ] [strategy-service] P0. Strategy-service QG runs against `e2e-testing/scripts/defi/` (per peripheral-script-dirs
      HARD RULE) — verify the new variants type-check from there too.

**Done definition:** Both variants instantiable from strategy-service factory; tracer math available for batch P&L
attribution; strategy-service QG green including peripheral-script wiring.

**Full-execution criterion:** Strategy-service `bash scripts/quality-gates.sh` green; tracer CLI runs against synthetic
config and produces non-NaN expected-APR per variant.

## Phase 4 — Extended `FlashLoanReceiver.sol` (3 AI-days)

The current 35-LOC contract at `deployment-service/contracts/FlashLoanReceiver.sol` is a passthrough — it validates
POOL + initiator and approves repayment. For atomic recursive opening it must execute supply / borrow / swap calls
inside `executeOperation`. Two design options:

- [ ] [Solidity] P0. **Option A (preferred): generic action-encoder pattern.** New `RecursiveLeverageReceiver.sol`
      accepts an encoded action sequence `bytes[]` parameter; loops through and executes each (call to Aave Pool /
      Uniswap Router / WETH wrap). Modeled on DefiSaver / Instadapp. Trade-off: more flexible, slightly heavier gas,
      code-audit surface larger.
- [ ] [Solidity] P1. **Option B (alternative): hard-coded recursive-supply-borrow loop.** Inline N supply / borrow calls
      in the callback. Less flexible but smaller audit surface. Defer unless Option A audit takes >2 AI-days.
- [ ] [Solidity] P0. Solidity test suite: foundry tests for atomic open / atomic close / failed flash repayment /
      mid-callback revert / re-entrancy protection. Run via `forge test` in `deployment-service/contracts/`.
- [ ] [deployment-service] P0. Deploy via existing
      `bash deployment-service/scripts/deploy-flash-loan-receiver.sh --chain ethereum` + `--chain base` (script already
      exists per CLAUDE.md DeFi-execution section); registry update in `unified-config-interface/testnet_contracts.py`
      `PROTOCOL_SCHEMAS`. `eth_getCode` verification per existing `connect()` validation pattern.
- [ ] [security] P1. **Internal review** before mainnet deploy. Trinity of (re-entrancy guards / approval scoping /
      repayment correctness) audited by ikenna or harsh; full external audit deferred to post-MVP volume scaling.

**Done definition:** Contract compiled; foundry tests green; deployed to Ethereum + Base mainnet; address committed to
UAC `testnet_contracts.yaml`; execution-service `connect()` validates on-chain.

**Full-execution criterion:** Deployed contract address visible on Etherscan + Basescan; `forge test --gas-report`
green; round-trip flash-and-recurse test against forked mainnet (Tenderly fork fixture per workspace test convention)
succeeds with expected aETH balance + ETH debt at the end.

## Phase 5 — `RecursiveLoopOrchestrator` in execution-service (4 AI-days)

- [ ] [execution-service] P0. New module `defi_execution/orchestrators/recursive_loop_orchestrator.py`. Inputs:
      `(start_amount, share_class_coin, n_loops,     ltv_per_loop, slippage_tolerance, gas_buffer, opening_mode, perp_leg_config | None)`.
      Outputs: `RecursiveLoopResult` with per-loop tx receipts + final position state.
- [ ] [execution-service] P0. Persistent driver: orchestrates N sequential calls to existing Aave supply / borrow /
      Uniswap swap (when borrow asset ≠ collateral asset). Pre-check health-factor ≥ `safety_buffer_ltv`-implied
      threshold before each loop iteration; abort + emit `LOOP_ABORTED_HF_LOW` event if violated. Use
      `classify_venue_error` per workspace adapter convention.
- [ ] [execution-service] P0. Flash driver: encodes the action sequence + calls `RecursiveLeverageReceiver.sol` via Aave
      V3 `flashLoan(...)`. Returns the receipt of the single flash tx.
- [ ] [execution-service] P0. Unwind driver: symmetric inverse for closing the loop (persistent: N repay / withdraw
      cycles; flash: 1 atomic tx that flash-borrows the principal, repays Aave debt, withdraws collateral, sells excess
      to repay flash).
- [ ] [execution-service] P0. Event emission per loop iteration (`LOOP_ITER_STARTED`, `LOOP_ITER_COMPLETED` with row
      counts + position state) per CLAUDE.md "No fire-and-forget" rule — silent-success-with-zero-output is detectable
      from event stream.
- [ ] [execution-service] P0. Unit tests: 10+ tests covering (persistent open / persistent close / flash open / flash
      close / HF abort mid-loop / slippage revert / reverted iter mid-stream / re-attempt / Tenderly fork integration /
      cross-chain).

**Done definition:** Both drivers operational against Tenderly mainnet fork; event stream emits per-iter progress; unit
tests + integration tests green; HF abort works.

**Full-execution criterion:** Tenderly fork integration test runs the full open + unwind cycle for a 5x ETH/wstETH
e-mode loop and asserts the final position matches the expected math within ±0.1% of `_net_apr_recursive` prediction.

## Phase 6 — Hyperliquid LIVE perp connector (3 AI-days)

- [ ] [execution-service] P0. `defi_execution/protocols/hyperliquid.py` `place_order` is currently simulation-only per
      its docstring. Wire-up: EIP-712 signing per Hyperliquid docs, REST POST to `api.hyperliquid.xyz/exchange`,
      WebSocket subscription to `user_events` for fill confirmations. Existing `_hyperliquid_schemas.py` already has the
      request/response schemas — leverage those.
- [ ] [execution-service] P0. Live error classification — extend `DefiErrorCode` (per CLAUDE.md DeFi
      error-classification section) with Hyperliquid-specific codes (`HL_INSUFFICIENT_MARGIN`,
      `HL_REDUCE_ONLY_VIOLATION`, `HL_INVALID_TIF`, `HL_RATE_LIMITED`).
- [ ] [execution-service] P0. Replace simulation tests with actual integration tests against
      `api.hyperliquid-testnet.xyz/exchange` (testnet fork). Cassette tests for replayability per workspace test
      convention.
- [ ] [execution-service] P1. CeFi alternative path: ensure existing Bybit / OKX / Binance perp connectors are equally
      wired up for Family 2 (parallel hedge venue option, not new — verify they're not also simulation-only).

**Done definition:** Hyperliquid testnet integration test executes a place-order + cancel-order round trip; live mainnet
wire-up gated behind ENV flag until paper-smoke passes.

**Full-execution criterion:** Testnet integration test green in CI; sample testnet account places + cancels a 0.01
ETH-PERP order and the on-chain event stream reflects both actions.

## Phase 7 — `PerpHedgeSizer` + USDC margin top-up automation (2 AI-days)

- [ ] [execution-service] P0. New module `defi_execution/helpers/perp_hedge_sizer.py`. Reads current Aave position state
      via `getUserAccountData` (already in aave.py); reads current perp position via Hyperliquid (or other) connector;
      computes the perp-short delta needed to achieve `target_net_delta`; emits a `RebalanceInstruction` consumable by
      execution-service.
- [ ] [execution-service] P0. USDC margin top-up: when perp account `available_margin` drops below
      `usdc_margin_buffer_min` (Phase 2 config field), auto- bridge from a treasury USDC balance. In testnet: pre-funded
      USDC; in mainnet: Copper/CEFFU bridge per `master_to_live_defi_2026_05_23.md` Group F item 19.
- [ ] [position-balance-monitor-service] P0. Verify position aggregation correctly nets (aETH + free ETH − ETH debt +
      perp short) into share-class delta. No code change expected per audit; integration test.
- [ ] [execution-service] P0. Unit tests: 8+ tests covering hedge-up / hedge-down / over-hedge correction / under-hedge
      correction / margin-call top-up / bridge failure handling / target_net_delta=0 / target_net_delta=+1.

**Done definition:** Hedge sizer produces correct rebalance instructions; margin top-up runs on testnet without errors;
position-balance integration test green.

**Full-execution criterion:** End-to-end test against Tenderly fork + Hyperliquid testnet executes a 5x loop opening
with `target_net_delta=0` and asserts position-balance-monitor reports share-class delta within ±0.001 ETH of target
after rebalance.

## Phase 8 — `HealthFactorMonitor` + `LiquidationProximityCircuit` + alerting integration (2 AI-days)

- [ ] [execution-service] P0. New module `defi_execution/monitors/health_factor_monitor.py`. Polls Aave
      `getUserAccountData` per recursive-borrow position every block (Ethereum: 12s; Base: 2s). Emits
      `HEALTH_FACTOR_OBSERVED` event each block; raises `HEALTH_FACTOR_BELOW_THRESHOLD` event when HF < 1.10
      (configurable per archetype config).
- [ ] [alerting-service] P0. New alert codes: `HEALTH_FACTOR_CRITICAL` (HF < 1.10), `LIQUIDATION_IMMINENT` (HF < 1.05),
      `FUNDING_SIGN_FLIP` (perp funding crosses zero against the strategy direction),
      `RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (persistent driver halts mid-loop). Per
      `alerting_service_live_rules_2026_05_07.md` taxonomy + kill-switch tier-up.
- [ ] [strategy-service] P0. Kill-switch wiring: `LIQUIDATION_IMMINENT` triggers immediate unwind (flash close);
      `HEALTH_FACTOR_CRITICAL` triggers partial-unwind (reduce leverage by 1 loop level); `FUNDING_SIGN_FLIP` triggers
      position-pause (no new opens; existing positions evaluated against threshold). Per archetype-config
      `kill_switch_tier_*` fields (already in `archetype_config.py:169-177`).
- [ ] [risk-and-exposure-service] P1. Concentration-risk handling: a recursive-borrow position concentrates exposure in
      (chain × asset × protocol); should the existing concentration-limit subsystem treat gross notional or net delta?
      Add a per-archetype concentration multiplier (default 1.0 for non-recursive, 1.5 for recursive — penalises
      concentration).

**Done definition:** Monitor + circuit operational on Tenderly fork; alerts fire on synthetic HF degradation;
kill-switch unwind verified end-to-end.

**Full-execution criterion:** Tenderly-fork synthetic test triggers a price drop that pushes HF from 1.30 → 1.05;
monitor emits both threshold alerts; strategy-service receives alerts and triggers flash-close; final position state
shows 0 ETH debt + 0 aETH within 1 block of `LIQUIDATION_IMMINENT` event.

## Phase 9 — Matching-engine DeFi cost model (3 AI-days)

Per `master_to_live_defi_2026_05_23.md` Group F item 17 (real gas / matching engine / cost+yield precision).

- [ ] [execution-service] P0. New cost models in `execution_service/matching_engine/defi/`: `gas_cost_model.py`
      (per-action gas estimation per chain), `slippage_cost_model.py` (Uniswap V3 concentrated-liquidity slippage curve
      at depth + Curve / Balancer fallbacks), `flash_premium_cost_model.py` (Aave V3 0.05% per principal + Balancer
      alternative).
- [ ] [execution-service] P0. Wire into batch P&L attribution. Per existing CLAUDE.md "Execution alpha measurement"
      rule: batch matching-engine produces simulated fills with realistic costs; benchmark fills (always-fill at
      requested price) isolate strategy alpha.
- [ ] [execution-service] P0. Backtest replay: take Phase 1 lending-rate + perp-funding history; replay through the
      matching engine; produce per-day strategy P&L for both variants. Compare against `_net_apr_recursive` analytical
      prediction.

**Done definition:** Cost models calibrated against historical on-chain data (gas: per-day median; slippage: per-pool
depth at execution time; flash premium: flat 0.05%); batch P&L reconciles with analytical model within ±2% on a 1-year
window.

**Full-execution criterion:** Backtest replay run on the full Phase 1 backfill window for both variants; resulting P&L
curves committed under `unified-trading-pm/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md` (NEW
doc) with per-month attribution table.

## Phase 10 — Codex SSOT updates (1 AI-day, runs alongside other phases)

Per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — codex updates ride in the same logical unit as the code commits.

- [ ] [codex] P0. NEW `codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked-config-variants.md`.
      Documents the two variants (`lending_arb_pure` + `perp_funding_capture`), config fields, share-class semantics,
      kill-switch surface, batch=live symmetry status. Cross-refs the parent `carry-recursive-staked.md` doc.
- [ ] [codex] P0. UPDATE `codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md` with a new "Config
      variants" section pointing at the variants doc.
- [ ] [codex] P0. UPDATE `codex/04-architecture/flash-loan-receiver.md` with the extended-receiver design pattern
      (action-encoder vs hard-coded loops); reference the deployed `RecursiveLeverageReceiver` addresses per chain.
- [ ] [codex] P0. UPDATE `codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` with new venue rows for
      recursive-borrow eligibility (Aave V3 Eth / Aave V3 Base + Hyperliquid / Bybit perp pairings).
- [ ] [codex] P0. NEW `codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md` (Phase 9 deliverable;
      backtest results table per variant).
- [ ] [codex] P0. UPDATE `codex/09-strategy/strategy-summary.md` archetype index to cite the new variants.
- [ ] [codex] P0. UPDATE `codex/04-architecture/batch-live-architecture.md` § per-archetype symmetry status with the
      recursive-borrow row.

**Done definition:** All 7 codex doc touchpoints landed; cross-refs bidirectional;
`bash unified-trading-pm/scripts/codex-validate.sh` green.

**Full-execution criterion:** Codex commit shipped; PM QG green;
`grep -r "carry-recursive-staked-config-variants" unified-trading-pm/codex/` returns ≥3 cross-refs.

## Phase 11 — deployment-api + deployment-ui surface (2 AI-days)

- [ ] [deployment-api] P0. New endpoint `GET /data-status/recursive-borrow-coverage` — returns per-(protocol, chain,
      asset) lending-rate coverage status from the Phase 1 manifest. Pydantic models in
      `deployment_api/models/recursive_borrow.py`.
- [ ] [deployment-ui] P0. ArchetypeMatrix component renders both variants (`lending_arb_pure`, `perp_funding_capture`)
      per asset_group=defi row.
- [ ] [deployment-ui] P0. New tile: `HealthFactorMonitorTile` — live HF chart per active position, threshold lines at
      1.10 / 1.05.
- [ ] [deployment-ui] P0. Recursive-Borrow data-status drilldown: per-protocol coverage % + per-asset spread-history
      sparkline.
- [ ] [deployment-ui] P1. Backtest-results visualisation: Phase 9 P&L curves rendered in deployment-ui per variant.

**Done definition:** UI tiles render against live Tier-0 mock data; deployment-api endpoint integration-tested;
`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh` shows all components.

**Full-execution criterion:** Deployment stack restart shows the new tiles populated against the Phase 1 manifest; one
round-trip place-and-monitor test executed via the UI's manual-trade gate.

## Phase 12 — Backtest runs + paper-trade smoke (2 AI-days)

- [ ] [backtest] P0. Run 2-year batch backtest for both variants on Phase 1 backfill window. Produces per-day P&L curves
      committed to PM under `unified-trading-pm/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md`.
- [ ] [paper-smoke] P0. New `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` harness — runs both variants
      against live Aave V3 (Tenderly fork + live read) + Hyperliquid testnet for ≥7 continuous days. Wired into
      strategy-service's `scripts/quality-gates.sh` per peripheral-script-dirs HARD RULE.
- [ ] [reconciliation] P0. Batch-vs-live reconciliation per `master_to_live_defi_2026_05_23.md` Group F item 21. Delta <
      5bps over 7 days = green.
- [ ] [findings] P0. Capture any divergences as plan todos in this plan body or as
      `plans/active/issues/<slug>_2026_05_xx.md` per Findings Triage Discipline.

**Done definition:** 2-year backtest committed; 7-day paper-smoke green; batch-vs-live recon < 5bps.

**Full-execution criterion:** `gs://${PID}-events/events/strategy/recursive-borrow-paper-smoke-*/` shows STARTED + 7
daily progress events + STOPPED with non-empty per-day P&L metadata; reconciliation report committed under codex.

## Phase 13 — Live deploy (1 AI-day)

- [ ] [deployment-service] P0. New launcher `scripts/vm/launch-defi-recursive-borrow-vm.sh` per VM-launcher-SSOT rule.
      Singleton-lock pattern (refuses launch if same-prefix VM RUNNING). VM-name prefix `defi-recursive-` registered in
      `VM_PREFIX_TO_BUCKET`.
- [ ] [operator] P0. Treasury allocation: 1 ETH base capital per variant + 800 USDC perp-margin per Family 2 instance
      (testnet) → scale up post-validation. Custody (Copper / CEFFU) integration deferred per master plan Group F item
      19; testnet uses pre-funded wallet.
- [ ] [VM] P0. Launch + monitor for 7 continuous days per master plan target. Verify event stream + alerting +
      kill-switch + reconciliation.
- [ ] [PM] P0. Plan archival: status → complete; Phase 1-13 todos all `- [x]`; deferred items per "Plan Archival HARD
      RULE" migrate to active home (P1 lending protocols → follow-up plan; Solana / Marginfi → separate plan; full
      external Solidity audit → separate plan).

**Done definition:** Live VM running for ≥7 days; both variants emitting expected events; alerting + kill-switch active;
treasury rebalance reflects expected yield; plan archived per HARD RULE.

**Full-execution criterion:** ≥7 days of `gs://${PID}-events/events/strategy/defi-recursive-*/` events with daily P&L
metadata; reconciliation report green; operator sign-off in plan archival commit.

## Temporary states + canonical follow-up plans

- **P1 lending protocols (Spark / Morpho Blue / Maker DSR)** deferred from Phase 1; successor plan:
  `plans/active/defi_recursive_borrow_protocol_expansion_2026_06_xx.md` (TBD post-cutover).
- **Solana / Marginfi / Kamino** deferred entirely; successor plan:
  `plans/active/defi_recursive_borrow_solana_2026_06_xx.md` (TBD post-cutover).
- **Other perp venues (Binance / OKX / Deribit / Aster)** deferred from Phase 6; successor: same protocol-expansion plan
  above OR a venue-expansion plan.
- **Full external Solidity audit of `RecursiveLeverageReceiver.sol`** deferred from Phase 4; successor plan:
  `plans/active/defi_recursive_borrow_security_audit_2026_06_xx.md` (TBD post-MVP volume scaling).
- **Cross-asset Family 1 variants (USDC vs DAI on same venue, etc.)** marked P2 within Phase 1 / Phase 5; successor:
  protocol-expansion plan above.
- **Custody (Copper / CEFFU) bridge for live USDC margin top-up** per master plan Group F item 19; consumed by Phase 7
  in testnet via pre-funded wallet, fully wired in master plan Phase F.

Each successor plan landed before this plan archives, per "Plan Archival HARD RULE" 2026-05-08.

## Total budget + sequencing

- Phase 0 — 0.5d
- Phase 1 — 5d (P0 critical-path, gates 9 + 12)
- Phase 2 — 1d (parallel with 1)
- Phase 3 — 2d (after 2)
- Phase 4 — 3d (parallel with 1, 2, 3)
- Phase 5 — 4d (after 4)
- Phase 6 — 3d (parallel with 5)
- Phase 7 — 2d (after 5 + 6)
- Phase 8 — 2d (parallel with 7)
- Phase 9 — 3d (after 1 + 5)
- Phase 10 — 1d (rolling alongside)
- Phase 11 — 2d (after 9)
- Phase 12 — 2d (after 9 + 11)
- Phase 13 — 1d (after 12)

Sum sequential critical path: P1 (5) → P3 (2) → P5 (4) → P7 (2) → P9 (3) → P12 (2) → P13 (1) = 19 days. With
parallelisation (P2 || P1, P4 || P1+P2+P3, P6 || P5, P8 || P7, P10 rolling, P11 after P9): **~17 calendar AI-days**
end-to-end. Fits the May-23 cutover if started no later than 2026-05-12.
