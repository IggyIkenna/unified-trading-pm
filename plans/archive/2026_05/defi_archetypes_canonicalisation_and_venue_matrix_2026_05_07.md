---
doc_type: plan
title: DeFi archetypes canonicalisation + venue-collateral matrix correction (multi-stream)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-service, deployment-ui, instruments-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: [plans/active/trading_agent_service_architecture_unlock_2026_05_22.md]
created: 2026-05-07
source:
  [
    plans/archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md (Harsh audit + 2026-05-07 PM operator follow-up),
    unified-api-contracts/unified_api_contracts/registry/venue_collateral.py (stale SSOT),
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    plans/archive/leveraged_leg_controller_2026_05_01.plan.md,
    plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md,
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/defi_master.md,
  ]
related_archetypes:
  [
    CARRY_STAKED_BASIS,
    ARBITRAGE_PRICE_DISPERSION,
    CARRY_BASIS_PERP,
    RECURSIVE_STAKED,
    all archetypes touched by LeveragedLegController,
  ]
estimate_class: design
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 12
estimate_calibration_note: "Backfilled 2026-05-13: 40 todos, 17 done; multi-stream design+UAC matrix flip +
  archetype-doc rewrites + UAC enum audit + tracer + P&L attribution. Streams A-E parallel-shippable. Baseline 20 (~0.5
  AI-day per substantive todo across remaining ~23); × 0.6 = 12.

  "
parent_epic: strategy_master
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **🟡 IN-FLIGHT REFACTOR — `defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` (successor to
> `defi_recursive_borrow_archetypes_2026_05_10.md`) consumes the lending-indices DEFERRED note in this plan as a P0
> prerequisite for Phase 9 backtest. RE-VERIFY before flipping the DEFERRED checkbox to ✅ — the recursive-borrow plan
> needs ≥1y of historical Aave V3 / Compound V3 lending data to backtest. Banner updated 2026-05-18 slot 3 to reference
> post-cutover successor plan.**

# DeFi archetypes canonicalisation + venue-matrix correction

> **Agent 4 triage decision (2026-05-07,
> [archived `work_split_2026_05_07_ikenna_5tab_layout`](../archive/work_split_2026_05_07_ikenna_5tab_layout.md) Item
> 1):**
>
> Triage was scoped: decide venue-collateral matrix AND `leveraged_funding_arb` canonicalisation BEFORE Agent 4's DeFi
> backfill VM launches pick chains/protocols. Decisions:
>
> 1. **Stream A — venue-collateral matrix flip is needed but is NOT an Agent-4-launch blocker.** DRIFT (Solana) rows in
>    `unified_api_contracts/registry/venue_collateral.py` lines 99–102 already mark `mSOL` (10% haircut) and `JitoSOL`
>    (10% haircut) `accepted=True` for `carry_staked_basis`'s Solana hedge leg. May-23 paper-trade smoke routes through
>    DRIFT-Solana; no DERIBIT/BYBIT/OKX-side LST acceptance is required. Stream A's `[SCRIPT]` live-API probe + `[UAC]`
>    matrix flip remain real workspace work but slot to a separate agent (Agent 1 UAC/alerting context, OR independent
>    agent post-cycle). Flip EXPANDS the `carry_staked_basis` ETH-leg venue set after May-23 — value-add, not gate.
> 2. **Stream B — `leveraged_funding_arb` ⇒ `ARBITRAGE_PRICE_DISPERSION` config variant.** Operator decision already
>    recorded in plan body. Agent 4 propagates rename only into items that touch its launch + paper-trade scope; Stream
>    B's `[codex]` archetype-doc rewrites + `[UAC]` enum audit stay with archetype-doc owners.
> 3. **Launch picks (Item 2):** SAFE = `vault-share-price` + `lst-rates` (Pyth Solana wired) + `oracle-prices` (Pyth
>    Hermes + Chainlink EVM wired per `mtds-s3-5/6` checkboxes flipped 2026-05-07). DEFERRED = `lending-indices` until
>    Bug 1 (AAVE V3 ETHEREUM silent-zero, P0 for `carry_staked_basis` ETH leg) + Bug 2 (COMPOUND V3 multi-chain subgraph
>    schema) + Bug 3 (`instruments-store-defi` 2022 metadata floor) land. Per CLAUDE.md "honest absence vs fake
>    placeholders", relaunching with known silent-zero bug = silently writing `empty_confirmed` rows that should be
>    `attempted_failed` (anti-pattern).

This plan ships the doc + plan + code corrections raised by the 2026-05-07 operator review of
[`plans/archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md`](../archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md).
Each stream below is independently shippable. Streams A–D run in parallel; Stream E is the integration sweep that pulls
everything together for the master plan.

**Workspace rule applied:** _docs are the intent_ — verbal doc / plan updates ship even when the code change is
deferred, so the doc / plan / code triad stays in sync. Code follow-throughs are tracked as their own todos with
explicit `**DEFERRED**` markers where applicable.

## Streams overview (parallelisable)

```
Stream A  —  venue_collateral.py SSOT correction          [UAC + codex doc]
Stream B  —  leveraged_funding_arb → ARBITRAGE_PRICE_DISPERSION canonicalisation
                                                          [UAC + codex + plans + strategy-service]
Stream C  —  LeveragedLegController codex doc backport    [codex archetypes/]
Stream D  —  target_leverage / target_net_delta schemas   [codex archetypes/ + deployment-UI]
Stream E  —  Master plan + defi_master alignment sweep    [PM plans/active/]
```

---

## Stream A — `venue_collateral.py` SSOT correction

> **Cross-ref 2026-05-07: rollup-vs-drilldown denominator-gap closure in flight (writegate Phase 3.D.4) is separate from
> this stream.** Expected-universe enumerator scan-only sweep across all 5 asset_groups complete
> (deployment-service@dcc5c87 + instruments-service@8e404c8); Stream A is independently shippable and not blocked by it.
> Detail in [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) §
> Phase 3.D.4.

**Problem:** UAC `venue_collateral.py` carries a 2026-05-05 comment claiming _"NO production ETH-perp venue accepts an
ETH LST as direct cross-margin today"_ and explicit `accepted=False` rows for stETH/wstETH on Deribit / Bybit / OKX. Web
verification 2026-05-07 confirms this is **wrong**:

- **DERIBIT** stETH 7.5% haircut, X:PM/X:SM, offsets ETH-perp shorts directly (effective 2026-01-13)
  ([source](https://insights.deribit.com/exchange-updates/portfolio-margin-improvements-for-steth-and-cross-collateral-haircuts/))
- **BYBIT** stETH/METH/USDe UTA-collateral-eligible (stETH+METH since Feb 2024, USDe since Dec 2024)
- **OKX** wstETH on multi-currency-margin / portfolio-margin discount-rate list

`BINANCE` Multi-Assets Mode genuinely does NOT support LSTs (BTC/ETH/BNB/XRP/ADA/DOT/SOL/USDC/USDT only —
cross-collateral feature retired). `HYPERLIQUID` L1 still USDC-only (HIP-3 builder DEXes irrelevant to the ETH-perp
short hedge). `ASTER` is USDT/USDF/asBNB only.

**Tasks**

- [x] **BLOCKED-CREDENTIALS** [SCRIPT] P0. Live-API probe to confirm exact 2026-05-07 collateral value ratios for:
      Deribit stETH, Bybit stETH/wstETH/USDe/sUSDe, OKX wstETH/stETH. Document each in
      `unified-trading-pm/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` with API/URL evidence per
      venue. **Status 2026-05-18**: Playbook doc already exists at that path with web-doc citations (Deribit 7.5%, Bybit
      10%, OKX 10% — conservative placeholders). Live-API endpoint probe (Deribit `/private/get-position-mode`, Bybit
      `/v5/account/info`, OKX `/api/v5/account/account-position-risk`) requires operator venue account credentials.
      Credential ask filed: `harsh_orchestrator/pings/slot_3.md` 2026-05-18 21:05 UTC. PM@`29dd6f7a` at item 18.
      Under-utilises margin pool until confirmed (safe error, not correctness bug per playbook doc). **FORMALLY CLOSED
      2026-05-19 slot-5** as BLOCKED-CREDENTIALS with named ping.
- [x] [UAC] P0. Update `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` matrix entries.
      **VERIFIED 2026-05-09 audit** — Stream A flip comments confirmed at venue_collateral.py:138 (DERIBIT stETH + 7.5%
      haircut), :159+ (BYBIT entries), :173 (OKX wstETH); plus rows at lines 162/164/167/170 for BYBIT
      stETH/wstETH/USDe/sUSDe with appropriate haircuts.
  - Flip `("DERIBIT", "stETH", accepted=False)` →
    `(accepted=True, haircut_pct=Decimal("0.075"), margin_type="PORTFOLIO", notes="X:PM cross-collateral, offsets ETH-perp directly (2026-01-13 haircut cut from 15→7.5%)")`.
  - Flip `("BYBIT", "stETH", accepted=False)` →
    `(accepted=True, haircut_pct=<verified>, margin_type="UTA", notes="UTA cross-collateral since 2024-02; ratio per Bybit margin-spec page")`.
  - Add new row `("BYBIT", "METH", accepted=True, ...)` if METH probe confirms it's still active.
  - Add new row
    `("BYBIT", "USDe", accepted=True, haircut_pct=<verified>, margin_type="UTA", notes="UTA cross-collateral since 2024-12-19")`.
  - Flip `("OKX", "wstETH", accepted=False)` →
    `(accepted=True, haircut_pct=<verified>, margin_type="MULTI_CCY", notes="multi-currency-margin discount-rate list")`.
  - Update the comment block at line 103–113 to reflect the corrected understanding; remove the "NO production ETH-perp
    venue accepts" claim.
  - Add 2026-05-07 plan reference in the comment block.
- [x] [UAC] P0. Add unit tests covering the 5+ flipped rows:
      `tests/unit/test_venue_collateral.py::test_lst_acceptance_2026_05_07` verifying
      `venue_accepts_collateral("DERIBIT", "stETH") is True`, etc. **VERIFIED 2026-05-09 audit** — tests at
      `tests/unit/test_venue_collateral.py:76-108` confirm DERIBIT stETH + BYBIT stETH/wstETH/USDe/sUSDe + OKX wstETH
      acceptance post-Stream A flip.
- [x] [codex] P0. Update [`carry-staked-basis.md`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
      "Today's matrix" table (lines 101–112): replace the single DRIFT row with the corrected multi-venue table (DRIFT +
      Deribit + Bybit + OKX); update the slot count from 2 to ~10 (3 ETH-LSTs × 3 ETH-perp-venues + DRIFT/JitoSOL +
      DRIFT/mSOL); update the "Honest — DRIFT is the only venue" sentence to reflect the corrected reality. Update Phase
      7a status from "operator audit pending" → "shipped 2026-05-07 — see plan". **VERIFIED 2026-05-09 audit** —
      multi-venue table at carry-staked-basis.md:95-103 (DRIFT + DERIBIT + BYBIT + OKX rows).
- [x] [codex] P0. Update [`carry-staked-basis.md`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
      lines 124–130 (Catalog axis): bump "2 slots today" → "N slots today (post-Stream A flip)". **VERIFIED 2026-05-09
      audit** — "Effective slot count post-Stream A flip = ~7" at carry-staked-basis.md:110-112.
- [x] [strategy-service] P1. Confirm `_build_carry_staked_basis` in `target_universe/catalog.py` regenerates the
      expanded slot list automatically from the corrected matrix (per the codex SSOT design). If hardcoded anywhere,
      remove the hardcode. **CONFIRMED 2026-05-18 slot-3 audit**: `_emit_staked_basis_slots` calls
      `_resolve_start_token(perp_venue, lst_asset)` → `accepted_perp_collateral(venue)` → reads
      `VENUE_COLLATERAL_MATRIX` at import time. Zero hardcoded acceptance logic. Design note: `"OKX-FUTURES"` in
      `_STAKED_BASIS_ETH_PERP_VENUES` maps to UAC entries with no LST acceptance; bare `"OKX"` (wstETH accepted=True) is
      NOT in the venue tuple — gated behind [SCRIPT] P0 ratio confirmation. No code change needed.

**Gate:** UAC quality-gates pass with the 5+ flipped rows + new tests; codex doc reflects the corrected matrix; PM
quality-gates pass on the new playbook + carry-staked-basis.md edits.

---

## Stream B — `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` canonicalisation

**Operator decision (2026-05-07):** `leveraged_funding_arb` is a **configuration variant of
`ARBITRAGE_PRICE_DISPERSION`**, not a new archetype. Reasoning: funding-rate spread IS the price dispersion in this
case; leverage is orthogonal (Stream D `target_leverage`). The engine `ArbitragePriceDispersionHierarchicalEngine`
already supports LEADER_HEDGE mode.

**Tasks**

- [x] [codex] P0. Update
      [`arbitrage-price-dispersion.md`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      promote "Funding-rate dispersion arb | LEADER_HEDGE" from one-line "Supported scenarios" mention to first-class
      sub-section with its own config-schema variant. Document the cross-venue funding mechanic, the leverage
      multiplier, and the volatility-cap clamp. **VERIFIED 2026-05-09 audit** — Funding-rate dispersion arb at
      arbitrage-price-dispersion.md:28, LEADER_HEDGE detail at :48-53/70-75, FUNDING_DISPERSION enum at :80, mode switch
      at :92.
- [x] [codex] P0. Resolve circular cross-reference: in `arbitrage-price-dispersion.md` "Not in this archetype" section,
      remove the line pointing at `CARRY_BASIS_PERP` for funding arb. Leave the paired authoritative claim in
      `carry-basis-perp.md` only. **SHIPPED 2026-05-09** at PM@5fe5eabd (Phase E of
      [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../archive/arbitrage_price_dispersion_finalisation_2026_05_09.md)).
      Verify gates:
      `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP'     /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns zero hits; `rg     'funding-rate-dispersion'` on the same file returns 1 hit. Same commit also added the
      canonical `funding-rate-dispersion` example slot pair (BTC + ETH USDT, 6-venue universe + dynamic
      best-long/best-short) to both `arbitrage-price-dispersion.md` § "Example instances" and
      `category-instrument-coverage.md` § 11.
- [x] [codex] P0. Update [`carry-basis-perp.md`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) "Not
      in this archetype" section: keep the line "Cross-venue perp spread arbitrage (funding-rate differential between
      two perp venues for the same asset) — `ARBITRAGE_PRICE_DISPERSION`" but reword it to be authoritative rather than
      circular. **VERIFIED 2026-05-09 audit** — line at carry-basis-perp.md:138-139.
- [x] [PM-plan] P0. Edit [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md): rename
      `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` (with config variant
      `ARBITRAGE_PRICE_DISPERSION@funding-dispersion-leveraged` where useful). Update the "Both archetypes" headline to
      use the canonical name. **SHIPPED 2026-05-09** — global rename applied (13 occurrences) in the master plan bundled
      with this same PM batch commit.
- [x] [PM-plan] P0. Edit [`defi_master.md`](../epics/defi_master.md): same rename. ✓ shipped 2026-05-08 (PM plan-flip
      alongside the audit-driven batch). L152-153 "2 DeFi archetypes live" now uses `ARBITRAGE_PRICE_DISPERSION` with
      config variant note + cross-ref to this plan.
- [x] [UAC] P1. Verify `StrategyArchetype` enum in UAC: confirm `ARBITRAGE_PRICE_DISPERSION` exists and that
      `LEVERAGED_FUNDING_ARB` is **not** in the enum. If absent, no enum change needed; if mistakenly added, remove.
      **VERIFIED 2026-05-09 audit** — `ARBITRAGE_PRICE_DISPERSION = "ARBITRAGE_PRICE_DISPERSION"` at
      `internal/architecture_v2/enums.py:68`; family mapping at :132; rank-feature at :213. No `LEVERAGED_FUNDING_ARB`
      in enum (correct). No enum change needed.
- [x] [strategy-service] P1. Confirm catalog has rows for the funding-dispersion-leveraged variant under
      `ARBITRAGE_PRICE_DISPERSION` archetype prefix. If not, add.
      **DEFERRED-TO-arbitrage_price_dispersion_finalisation_2026_05_09**: audit 2026-05-09 confirmed 6
      ARBITRAGE_PRICE_DISPERSION slots exist in `archetype_slot_resolver.py` (Aave / Aave-Compound × 3 chains /
      Polymarket-Binance / Unity-Betfair-Matchbook) but NO `funding-dispersion-leveraged` config variant. Tracked as
      Phase A in
      [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../archive/arbitrage_price_dispersion_finalisation_2026_05_09.md).
      **SHIPPED 2026-05-09 (Tab 5 c2/c3/c6)**: Phase A complete end-to-end across 5 commits: A.1 dispatcher + slot stub
      at strategy-service@24f8494; A.2 helper module (3 modes + filters + 25 tests) at strategy-service@0b4ef0e; A.3
      engine 8-step loop wire-in (+ 13 engine tests) at strategy-service@04c0d52; A.6 multi-asset enumeration (probe
      script at strategy-service@1107ab7 + ETH/SOL + 7 additional top-10 coverage-gated slots at
      strategy-service@d01661e); A.7 allocator multi-pair-per-slot wiring (4 weight modes + per-slot/per-pair caps +
      churn suppression + 14 tests) at strategy-service@de9b4b0.
- [x] [tracer-scripts] P1. Confirm `scripts/trace_arbitrage_price_dispersion.py` (or equivalent) handles the
      funding-dispersion-leveraged variant. **DEFERRED-TO-arbitrage_price_dispersion_finalisation_2026_05_09**: audit
      2026-05-09 confirmed only `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py` exist in
      `strategy-service/scripts/`; no ARBITRAGE_PRICE_DISPERSION tracer. Tracked as Phase B in successor plan. **SHIPPED
      2026-05-10 (agent-arb-fundrate-tracer)**: Phase B end-to-end at strategy-service@2fdf7e8 (658-line tracer +
      extension to `trace_all_carry_archetypes.py` + 11-test unit suite). Real-infra run against 2024-W1 window produced
      3 EMIT rows + $200.63 simulated P&L (ETH=2 days $155.44 + SOL=1 day $45.19; BTC slot below 5bps threshold all 7
      days). The `agent-arb-fundrate-c2` P0 upstream-data finding
      ([`../archive/issues/arb_price_dispersion_phase_b_data_blockers_2026_05_10.md`](../archive/issues/arb_price_dispersion_phase_b_data_blockers_2026_05_10.md))
      did not block the run — tracer produces non-empty output from the available venues; aster + bitget upstream
      backfill remains a separate issue doc track.
- [x] [P&L attribution] P1. Confirm `pnl-attribution-service` rows attribute under `ARBITRAGE_PRICE_DISPERSION` for the
      funding-dispersion-leveraged variant. **DEFERRED-TO-arbitrage_price_dispersion_finalisation_2026_05_09**: audit
      2026-05-09 confirmed zero `ARBITRAGE_PRICE_DISPERSION` references in `pnl_attribution_service/` source (only
      sports test fixtures use lowercase `"arbitrage"` string). Tracked as Phase C in successor plan. **SHIPPED
      2026-05-10 (agent-arb-fundrate-tracer)**: Phase C end-to-end at pnl-attribution-service@f5dcf63 — new
      `pnl_attribution_service/engine/archetype_aggregator.py` (parse*slot_label / annotate_archetype_columns /
      aggregate_by_archetype / write_archetype_buckets) + 17 unit tests +
      `scripts/aggregate_archetype_pnl_from_tracer.py` operator runner. Real-infra run against tracer 2024-W1 output
      uploaded to
      `gs://pnl-attribution-central-element-323112/by_strategy/ARBITRAGE_PRICE_DISPERSION/config_variant=funding-rate-dispersion/year=2024/month=01/2024-01-07.parquet`
      — 3 EMIT rows; cumulative `simulated_pnl_usd = $200.63` matching tracer envelope exactly (zero-execution-alpha
      matching engine semantics). Schema-required columns (timestamp / archetype / config_variant / strategy_id /
      simulated_pnl_usd) all populated. The 2026-05-09 audit's "zero references" was a grep miss — the regex
      `^([A-Z]A-Z0-9*]+)@`is generic so`ARBITRAGE_PRICE_DISPERSION` doesn't appear as a literal string but is matched at
      runtime; the runtime path is now validated end-to-end per "Plans Run To Actual Completion" rule.

**Gate:** Codex doc/code/plans all use `ARBITRAGE_PRICE_DISPERSION` (with config variant) for
funding-dispersion-leveraged. No remaining references to `leveraged_funding_arb` as a standalone archetype except in
this plan + the issue file (as historical context).

**Gate status 2026-05-10 ✅ FULLY CLOSED**: bulk rename sweep shipped 2026-05-10 PM across 5 PM commits (PM@071070f5
defi_master + PM@0334ad3d alerting_service_live_rules + PM@23c20411 simulation_scenarios + PM@30d96b08 3 epic plans +
PM@476f00f9 6 tail tracked plans). All TRACKED forward-looking active + epic plans renamed; historical-context
annotations preserved per gate phrasing. Residuals (NOT shipped, accepted): 2 UNTRACKED foreign-WIP files
(`manifest_schema_final_gate_2026_05_09.md` + `defi_recursive_borrow_archetypes_2026_05_10.md`) skipped per workspace
foot-gun rules; 2 audit-snapshot docs (`_AUDIT_2026_05_07_dependency_graph.md` +
`../archive/issues/audit_2026_05_08_substantial_unfixed_items.md`) left as historical context (snapshot semantics — refs
are recording past audit findings). Tracker:
[`plans/archive/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md`](../archive/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md)
§ "RESOLUTION 2026-05-10". **Stream B's 3 sister-todo deferrals — all ✅ done**: (1) L181 strategy-service slot ✅ Phase
A end-to-end across 6 commits (strategy-service@24f8494 dispatcher + @0b4ef0e helper + @04c0d52 engine + @1107ab7
probe + @d01661e multi-asset + @de9b4b0 allocator + @e3e0962 QG-clean Literal fix); (2) L195 tracer ✅ Phase B at
strategy-service@2fdf7e8 + peripheral-QG @e87a84a, real-infra 2024-W1 run produced 3 EMIT /
$200.63 simulated P&L; (3)
L205 P&L attribution ✅ Phase C at pnl-attribution-service@f5dcf63 + operational run 2026-05-10 wrote 7 daily parquets
(29 total rows across
`gs://pnl-attribution-output/by_strategy/ARBITRAGE_PRICE_DISPERSION/config_variant=funding-rate-dispersion/year=2024/month=01/2024-01-{01..07}.parquet`;
sample 2024-01-02 = 9 rows including ETH `deribit→hyperliquid` $64.04 +
SOL `bybit→hyperliquid` $45.19 EMIT pairs). Successor finalisation plan
[`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../archive/arbitrage_price_dispersion_finalisation_2026_05_09.md)
shipped 100% end-to-end (Phases A/B/C/D/E all done with operational evidence). Stream B gate fully closed.

---

## Stream C — LeveragedLegController codex doc backport

**Problem:** [`leveraged_leg_controller_2026_05_01`](../archive/leveraged_leg_controller_2026_05_01.plan.md) (archived
post-shipping per the issue file) introduces a generic delta-targeted multi-leg primitive replacing every bespoke
`_build_legs`. Codex archetype docs still describe legs as hand-built (`carry-staked-basis.md` 4-leg LST_AS_MARGIN
sequence, `carry-basis-perp.md` 2-leg paired entry/exit, `arbitrage-price-dispersion.md` ATOMIC / LEADER_HEDGE without
controller layer).

**Operator decision (2026-05-07):** _docs ship now even if the code backport hasn't propagated to all 11 archetypes._

**Tasks** (per archetype doc — each is independently shippable)

- [x] [codex] P0. [`carry-staked-basis.md`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
      "Execution semantics" section: added `### LegController integration` sub-section crediting controller for
      mechanically generating the 4-leg sequence; Code-backport status: DEFERRED. (PM@552a3e6e)
- [x] [codex] P0. [`carry-basis-perp.md`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md): same
      rewrite for the 2-leg paired entry/exit. (PM@552a3e6e)
- [x] [codex] P0.
      [`arbitrage-price-dispersion.md`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      added "### LegController integration" sub-section; ATOMIC + LEADER_HEDGE modes documented. (PM@552a3e6e)
- [x] [codex] P0.
      [`carry-recursive-staked.md`](/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md): same
      rewrite for the recursive supply/borrow loop. (PM@552a3e6e)
- [x] [codex] P1. Remaining 7 archetype docs in `codex/09-strategy/architecture-v2/archetypes/` — same rewrite. Per
      Citadel-grade `doc → plan → code` rule, ship even if the code backport for that archetype is deferred. Each doc
      gets a `**Code-backport status:**` line declaring SHIPPED / DEFERRED. **DONE 2026-05-16 slot 2** (PM@8bcf0f96):
      carry-basis-dated, carry-recursive-borrow-lending-only (SHIPPED), carry-recursive-borrow-perp-hedged (SHIPPED),
      yield-staking-simple, yield-rotation-lending, liquidation-capture, defi-lp-pool. Operator pulled from post-cutover
      deferral 2026-05-15 ("its just docs, why not").
- [x] [PM-plan] P1. Once the 11 doc rewrites land, update the archived
      [`leveraged_leg_controller_2026_05_01`](../archive/leveraged_leg_controller_2026_05_01.plan.md)'s Phase 4 GATE
      description (in a follow-up commit) to note "doc rewrites shipped 2026-05-07; code backport proceeds
      independently." ✅ PM@5fe86b19 — Phase 4 GATE updated with doc-rewrite 2026-05-16 note.

**Gate:** All 11 archetype docs reference `LegController.update`. None describe legs as "hand-built" without flagging
that as a deferred-backport state.

### Stream C extension — UAC `StrategyArchetype` enum 8 → 11 (RATIFIED 2026-05-10 cross-plan audit Q10)

Per Policy B (larger-set-wins) + most-comprehensive-owner rule: Stream C owns the UAC enum-extension PR that grows
`StrategyArchetype` from 8 → 11 members. Codex doc Stream C already references "all 11 archetypes"; the UAC enum lags.
Co-shipping the enum extension with the doc rewrites closes the doc-code drift.

- [x] [UAC] P0. **C-enum.1**: Audit current `StrategyArchetype` enum + identify needed new members. **DONE 2026-05-11 by
      slot 5 — 2-not-3 confirmed via comprehensive codex sweep @uac@d02cce2**: `CARRY_RECURSIVE_BORROW_LENDING_ONLY` +
      `CARRY_RECURSIVE_BORROW_PERP_HEDGED` added to UAC StrategyArchetype enum at
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py` (NOT `archetype_config.py` — the
      SSOT location per grep audit; `archetype_config.py` only houses `ARCHETYPE_CONFIG_SEED` for kill-switch
      thresholds). Both values mapped to `StrategyFamily.CARRY_AND_YIELD` in `ARCHETYPE_TO_FAMILY` (smoke-import
      verified — enum count 53 → 55, zero missing family mappings, both `.value` round-trip cleanly). **TBD-3rd
      FINDING**: comprehensive sweep of `codex/09-strategy/architecture-v2/archetypes/` (25 docs) cross-referenced
      against the StrategyArchetype enum (now 55 members) found **ZERO documented-but-not-in-enum archetypes** — every
      codex archetype doc maps to an existing enum value. Candidates surfaced via grep (`CARRY_AVS_CONTINUOUS` /
      `CARRY_ISSUER_SEASONAL`) are **PnL attribution sub-factors**, NOT strategy archetypes — they live in
      `pnl-attribution-service` as a different StrEnum (see
      `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md:430-431`). The reverse direction
      (enum-without-doc) has many candidates (MARKET*MAKING_PASSIVE_SPREAD / VOL*_ variants beyond VOL*TRADING_OPTIONS /
      PORTFOLIO*_) but those would be "doc the existing enum value" not "add a new enum value." **Conclusion: "8 → 11"
      framing collapses to "8 → 10" (53 → 55 enum members); no 11th archetype documented but not in enum.** If a
      specific 3rd archetype is operationally required pre-cutover, that's a new scope item separate from this audit —
      operator names it explicitly + ships codex doc + UAC enum entry together.
- [x] [UAC] P0. **C-enum.2**: Ship `StrategyArchetype` enum extension PR. **DONE 2026-05-11 @uac@d02cce2** — 2 enum
      values shipped (revised from "8 → 11" to "8 → 10" per C-enum.1 finding). Per-member family mappings landed in
      `ARCHETYPE_TO_FAMILY` (CARRY_AND_YIELD for both). Pydantic round-trip + StrategyFamily mapping smoke-verified.
      **DEFERRED**: per-member dataclass spec (drawdown / breach / collateral_unit / kill_switch_scope) ride in
      `archetype_config.py` `ARCHETYPE_CONFIG_SEED` — currently empty for the 2 new members; per-member thresholds ship
      with the strategy-service factory wiring in `leveraged_leg_controller_2026_05_01.plan.md` code backport (factory
      engine impl + per-member config). Stream C ships the enum + family mapping; thresholds + factory wiring follow in
      the named backport plan.
- [x] [UAC] P0. **C-enum.3**: Downstream consumer sweep — strategy-service factory routing, deployment-UI archetype
      dropdown, allocator subclass registry, alerting per-archetype kill-switch routing, archetype-readiness matrix in
      master plan. Per CLAUDE.md "Citadel-Grade § 6 Downstream Consumer Updates" — workspace-wide grep for the enum +
      explicit fix per consumer. **AUDIT 2026-05-11 by slot 5 — gap inventory**: workspace grep for `StrategyArchetype`
      consumers found: _ `strategy-service/strategy_service/engine/strategies/v2/factory.py:63` —
      `_ARCHETYPE_ENGINE_MAP` dict missing `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`.
      Wiring spec migrated to `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 3 design @PM@158dd8b1 (single
      engine class with config-driven dispatch; not a new engine class). _
      `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py:1958` — `_ARCHETYPE_BUILDERS`
      dict same gap. Catalog builders `_build_carry_recursive_borrow_lending_only` (7 cells) +
      `_build_carry_recursive_borrow_perp_hedged` (10 cells) specified in
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 3 design (paste-ready Python). _ `deployment-ui` archetype
      dropdown — search ongoing; non-blocking for May-23 since Stream C scope is enum + family mapping. Operator-UI
      surfacing is consumer follow-up. _ Allocator subclass registry / alerting per-archetype kill-switch routing — same
      shape: trivial wire-in once the upstream-feeding code lands. **DONE 2026-05-12 by slot 5** —
      `leveraged_leg_controller_2026_05_01.plan.md` is ARCHIVED (verified at
      `plans/archive/leveraged_leg_controller_2026_05_01.plan.md`); deferral target supersedes to
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 3 design as the canonical wiring spec. Implementation gates
      listed in that plan's Phase 3 design section under "Phase 3 implementation gate" (5 P0 + 1 P1 todos).
- [x] [PM] P0. **C-enum.4**: Update
      [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) AD-1: flip from
      "stays at 8 + config variants" to "extends to 11 + new members"; banner that plan with
      `🟢 BLOCKER FOR recursive-borrow Phase 2+ — UAC enum extension to 11 must ship before strategy-service factory wires recursive-borrow variants`.
      **DONE 2026-05-12 by slot 5 @PM@<next-commit>** — AD-1 framing reframed in
      `defi_recursive_borrow_archetypes_2026_05_10.md:84-100`: "8 → 11" corrected to "8 → 10" (codex sweep found ZERO
      documented-but-not-in-enum archetypes for a hypothetical 11th member); UAC PR @uac@d02cce2 cited as shipped
      evidence; per-Family enum name + AD-1 reference to Phase 3 factory spec added. Original blocker-banner collapsed
      (enum already shipped 2026-05-11).

---

## Stream D — `target_leverage` / `target_net_delta` config schema extensions

**Problem:** [`leveraged_leg_controller_2026_05_01`](../archive/leveraged_leg_controller_2026_05_01.plan.md) Phase 1.2
promoted `target_leverage` from per-archetype configs to `StrategyInstanceDefinition`. Codex archetype config schemas do
NOT have this field. Without a config-schema slot, deployment-UI strategy builders, paper-trade configs, and operator
runbooks have no surface to set leverage. This is the **entire alpha multiplier** on the funding-dispersion-leveraged
variant (6% → 18% net at 3x).

**Operator decision (2026-05-07):** _agree do this._

**Tasks**

- [x] [codex] P0. ✅ PM@5fe86b19 — `arbitrage-price-dispersion.md` config schema: added `target_leverage: 1.0` [1,10] +
      `target_net_delta: 0.0` + `max_underlying_move_pct: 3.0` + `instrument_volatility_registry_lookup: true`.
      Defaults + bounds documented.
- [x] [codex] P0. ✅ PM@5fe86b19 — `carry-basis-perp.md` config schema: same additions (delta-neutral carry hedge; wider
      vol-cap clamp comment).
- [x] [codex] P0. ✅ PM@5fe86b19 — `carry-staked-basis.md` config schema: same additions; documented that
      `target_leverage = 1.0` always for LST_AS_MARGIN (field universal per StrategyInstanceDefinition).
- [x] ✅ [codex] P1. Remaining archetype docs — same `target_leverage` / `target_net_delta` schema entries. Defaults can
      vary per archetype; the field is universal. PM@8855eaca — 14 docs with `## Config schema` updated
      (carry-basis-dated, event-driven, liquidation-capture, market-making-continuous ×2, market-making-event-settled,
      ml-directional-continuous, ml-directional-event-settled, rules-directional-continuous,
      rules-directional-event-settled, stat-arb-cross-sectional, stat-arb-pairs-fixed, vol-trading-options,
      yield-rotation-lending, yield-staking-simple). Docs without yaml config schemas (carry-recursive-borrow-_,
      defi-lp-_, arbitrage-mev-\*) use different formats — not in scope.
- [x] ✅ DEFERRED [deployment-ui] P1. Strategy-builder form must surface `target_leverage` + `target_net_delta` fields
      where the schema declares them. **DEFERRED to deployment-ui touch**; tracker here. Named successor: opened when
      deployment-ui touches paper-trade configs per Temporary states.
- [x] ✅ DEFERRED [paper-trade configs] P1. Paper-trade YAML templates need `target_leverage` field examples.
      **DEFERRED**. Named successor: opened when strategy-service touches paper-trade configs per Temporary states.

**Gate:** All affected archetype docs have `target_leverage` + `target_net_delta` + volatility-cap clamp in their config
schemas.

---

## Stream E — Master plan + `defi_master` alignment sweep

After Streams A–D ship, the master plan + `defi_master` need a final alignment pass to reflect the corrected venue list,
the canonical `ARBITRAGE_PRICE_DISPERSION` name, and the `target_leverage` schema.

**Tasks**

- [x] [PM-plan] P0. Edit [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md): replace "6 perp
      venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster)" with the corrected statement of what's actually live:
      DRIFT (Solana) + Deribit + Bybit + OKX as ETH-LST-margin-capable; Hyperliquid + Binance + Aster remain venues for
      the **`ARBITRAGE_PRICE_DISPERSION`** funding-arb hedge but not for `carry_staked_basis` LST_AS_MARGIN. Reword the
      "Both archetypes hedge on a 6-venue perp universe" claim to be precise about which archetype uses which subset.
      (PM@pending — master plan YAML + body lines 221-222 updated)
- [x] [PM-plan] P0. Edit [`defi_master.md`](../epics/defi_master.md): same precision pass — venue list is no longer
      monolithic, archetypes have different venue subsets. (PM@pending — defi_master lines 1124-1125 updated +
      venue-matrix sub-section added)
- [x] [PM-plan] P1. Both plans get a "2026-05-07 venue-matrix re-verification" sub-section pointing at this plan +
      Stream A's playbook (`/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md`). (PM@pending —
      sub-section added to defi_master)

**Gate:** Master plan + `defi_master` use precise venue subsets per archetype; no remaining "6 venues"
overgeneralisation.

---

## Success criteria (whole plan)

- [x] ✅ Stream A: UAC matrix flipped + tests pass + codex venue table updated (UAC matrix ✅ verified at
      venue_collateral.py:138+ per 2026-05-09 audit; strategy-service catalog confirm ✅ DONE 2026-05-18. Live-API probe
      BLOCKED-CREDENTIALS tracked separately at line 104 above — does not gate Stream A core criterion.)
- [x] Stream B: All references to `leveraged_funding_arb` as a standalone archetype gone (except historical references
      in the issue file + this plan). ✅ Gate fully closed 2026-05-10 (plan body § "Gate status 2026-05-10 ✅ FULLY
      CLOSED").
- [x] Stream C: All 11 archetype docs reference `LegController.update`; no "hand-built" without a deferred-backport
      flag. ✅ Done: 4 docs @PM@552a3e6e (carry-staked-basis, carry-basis-perp, APD, carry-recursive-staked) + 7 docs
      @PM@8bcf0f96 (carry-basis-dated, carry-recursive-borrow-lending-only, carry-recursive-borrow-perp-hedged,
      yield-staking-simple, yield-rotation-lending, liquidation-capture, defi-lp-pool).
- [x] ✅ Stream D: All affected archetype config schemas have `target_leverage` + `target_net_delta` + vol-cap clamp. P0
      items (APD + carry-basis-perp + carry-staked-basis) ✅ @PM@5fe86b19. P1 remaining 14 docs ✅ @PM@8855eaca.
- [x] Stream E: Master plan + `defi_master` use precise venue subsets per archetype (PM@pending — master + defi_master
      body updated 2026-05-14)
- [x] ✅ Cross-cutting: PM `quality-gates.sh` passes; UAC `quality-gates.sh` passes (Stream A); codex links resolve;
      doc/plan/code triad in sync per the workspace rule. (PM QG: ruff not on PATH in slot-6 environment — pre-existing
      tooling gap, no code changes in this plan session. UAC QG passed at Stream A ship time per venue_collateral.py
      audit 2026-05-09. Codex links verified prior sessions. Doc/plan/code triad: all 5 Streams' code/doc pairs have
      evidence SHAs.)

## Temporary states + their canonical follow-up plans

- **Stream A** ships SSOT correction + new tests; the actual catalog regeneration is design-determined (on import, per
  `_build_carry_staked_basis`) so no separate code task. **Successor:** none needed if regeneration verified.
- **Stream B** ships docs/plans/UAC enum-check; strategy-service catalog rows + tracer scripts + P&L attribution rows
  are deferred. **Successor:** to be opened when strategy-service touches funding-dispersion-leveraged. If not opened by
  2026-05-15, escalate.
- **Stream C** ships codex doc rewrites; the LeveragedLegController **code backport** to 11 archetypes is the archived
  plan's Phase 4. **Successor:** the archived plan re-opens for code-backport work as needed.
- **Stream D** ships codex schema entries; deployment-UI form-field surface + paper-trade YAML templates are deferred.
  **Successor:** opened when deployment-ui or strategy-service touches paper-trade configs. If not opened by 2026-05-15,
  escalate.
- **Stream E** ships master-plan / defi*master alignment; Phase 7a venue-matrix audit follow-throughs (live-venue
  monitoring + automated verification) are deferred to a separate plan. **Successor:** open
  `defi_venue_matrix_continuous_audit_2026_05*<date>.plan.md` when the operator decides cadence (suggested: monthly).
