---
doc_type: codex-ssot
title: Runtime Topology — Decisions Log
summary:
  "Durable decision record for unified-trading-pm/configs/runtime-topology.yaml — the SSOT itself declares this doc as
  its decisions_doc (ssot.decisions_doc field) but it was never created; this file closes that gap. Records WHY a
  topology change was made (deployment_profile assignment, isolation_policy choice, sla_tier calibration), not just WHAT
  changed — the yaml diff already shows the what."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, strategy-service, deployment-service]
scope: [engineer, admin]
tags: [runtime-topology, deployment-profile, decisions-log, sla-tiers, archetype]
related:
  [
    unified-trading-pm/configs/runtime-topology.yaml,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    /plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md,
  ]
created: 2026-08-10
authoritative_for: [runtime-topology.yaml change rationale, deployment_profile decision history]
referenced_by: []
owner:
last_reviewed: 2026-08-10
code_refs: [unified-trading-pm/configs/runtime-topology.yaml]
---

# Runtime Topology — Decisions Log

**Purpose**: `runtime-topology.yaml`'s own `ssot.decisions_doc` field has pointed here since v7 (2026-07-19), but the
file was never created — this closes that gap. Append a dated entry per topology decision below; do not duplicate the
yaml's own content here, only the reasoning that isn't obvious from the diff.

## 2026-08-10 — archetype-family deployment_profile derivation

**Derivation rule** (from the audit plan's fixed rubric,
`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`):

- `Low` (sub-second E2E / ms-realm inter-leg execution gap) → `co_located_vm`
- `Medium` / `High` (seconds-to-minutes E2E) → `distributed`

**Latency categories sourced from** the now-populated `## Latency Requirements` sections in each family doc under
`codex/09-strategy/architecture-v2/families/*.md` (populated 2026-08-10 per the audit plan's todos 1–7).

### Per-archetype deployment_profile table

Each row maps one archetype enum value → its family doc's latency category → derived `deployment_profile`. The "Current
§6 row" column references `client-isolation-sla-and-runtime-profiles.md` §6's existing `topology_requirements` table — ✓
= row exists and is consistent with this derivation; ✗ = row exists but is INCONSISTENT (requires correction by the
execution plan); **MISSING** = no row exists yet (requires creation).

| Archetype                                                                                                                     | Family doc                | Latency Category     | Deployment Profile     | Current §6 row                              | Notes                                                                                                                                                                                                                                                                                |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------------- | ---------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Market Making (10 archetypes — all `Low`)**                                                                                 |
| `MARKET_MAKING_CONTINUOUS`                                                                                                    | `market-making.md`        | `Low`                | `co_located_vm`        | ✓ (co-loc yes, SLA premium)                 | Legacy catch-all; already correct.                                                                                                                                                                                                                                                   |
| `MARKET_MAKING_EVENT_SETTLED`                                                                                                 | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Sports exchange back/lay; needs new row.                                                                                                                                                                                                                                             |
| `MARKET_MAKING_PASSIVE_SPREAD`                                                                                                | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Symmetric two-sided quoting.                                                                                                                                                                                                                                                         |
| `MARKET_MAKING_INVENTORY_SKEW`                                                                                                | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Avellaneda-Stoikov; needs inventory-aware co-location.                                                                                                                                                                                                                               |
| `MARKET_MAKING_ML_LEAN`                                                                                                       | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | ML-tilted quotes; co-locate with inference.                                                                                                                                                                                                                                          |
| `MARKET_MAKING_QUEUE_MICROSTRUCTURE`                                                                                          | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Queue-position/VPIN toxicity; FIFO time-priority venues.                                                                                                                                                                                                                             |
| `MARKET_MAKING_PREDICTION`                                                                                                    | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Prediction CLOB MM (Polymarket, Kalshi).                                                                                                                                                                                                                                             |
| `DEFI_LP_CONCENTRATED`                                                                                                        | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Uniswap V3 range management; co-locate with on-chain features.                                                                                                                                                                                                                       |
| `DEFI_LP_POOL`                                                                                                                | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | Full-range pool LP.                                                                                                                                                                                                                                                                  |
| `DEFI_LP_VAULT`                                                                                                               | `market-making.md`        | `Low`                | `co_located_vm`        | MISSING                                     | ERC-4626 vault APY-gated deposit/redeem.                                                                                                                                                                                                                                             |
| **Arbitrage / Structural (7 archetypes — all `Low`)**                                                                         |
| `ARBITRAGE_STRUCTURAL`                                                                                                        | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA standard)             | **DISCREPANCY**: needs co-loc yes + SLA premium.                                                                                                                                                                                                                                     |
| `ARBITRAGE_PRICE_DISPERSION`                                                                                                  | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | Cross-venue same-instrument arb; leg-and-hedge gap is ms-realm.                                                                                                                                                                                                                      |
| `LIQUIDATION_CAPTURE`                                                                                                         | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | Capital-required liquidation bot; priority-fee race.                                                                                                                                                                                                                                 |
| `ARBITRAGE_MEV_BACKRUN`                                                                                                       | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | Post-swap DEX recovery; ATOMIC single-tx.                                                                                                                                                                                                                                            |
| `ARBITRAGE_MEV_SANDWICH`                                                                                                      | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | Theoretical only — no live engine.                                                                                                                                                                                                                                                   |
| `ARBITRAGE_MEV_JIT_LIQUIDITY`                                                                                                 | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | JIT LP mint-before-swap; 2-block ATOMIC.                                                                                                                                                                                                                                             |
| `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`                                                                                            | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | Flash-loan liquidation; ATOMIC single-tx.                                                                                                                                                                                                                                            |
| `ARBITRAGE_CROSS_DOMAIN_EVENT`                                                                                                | `arbitrage-structural.md` | `Low`                | `co_located_vm`        | MISSING                                     | Sports↔prediction↔CME cross-domain arb.                                                                                                                                                                                                                                              |
| **Carry & Yield (10 archetypes — 8 `Low`, 2 `Medium`)**                                                                       |
| `CARRY_BASIS_PERP`                                                                                                            | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA standard)             | **DISCREPANCY**: spot+perp leg-and-hedge gap is ms-realm.                                                                                                                                                                                                                            |
| `CARRY_BASIS_DATED`                                                                                                           | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | MISSING                                     | Spot+dated future basis; same inter-leg requirement.                                                                                                                                                                                                                                 |
| `CARRY_BASIS_DATED_INV`                                                                                                       | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | MISSING                                     | Inverse dated basis (short spot + long future).                                                                                                                                                                                                                                      |
| `CARRY_BASIS_PERP_INV`                                                                                                        | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | MISSING                                     | Inverse perp carry (borrow+sell spot, long perp).                                                                                                                                                                                                                                    |
| `CARRY_STAKED_BASIS`                                                                                                          | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA standard)             | **DISCREPANCY**: staked basis leg-and-hedge gap is ms-realm.                                                                                                                                                                                                                         |
| `CARRY_STAKED_BASIS_DATED`                                                                                                    | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | MISSING                                     | Staked dated basis; same inter-leg requirement.                                                                                                                                                                                                                                      |
| `CARRY_RECURSIVE_STAKED`                                                                                                      | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | MISSING                                     | Leveraged staking loop; liquidation cascade risk demands low-latency health-factor monitoring.                                                                                                                                                                                       |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY`                                                                                         | `carry-and-yield.md`      | `Low`                | `co_located_vm`        | MISSING                                     | Cross-venue borrow/lend APY arb; leg-and-hedge gap.                                                                                                                                                                                                                                  |
| `YIELD_ROTATION_LENDING`                                                                                                      | `carry-and-yield.md`      | `Medium`             | `distributed`          | MISSING                                     | Single-sided; no inter-leg gap. APY rotation is minutes-scale.                                                                                                                                                                                                                       |
| `YIELD_STAKING_SIMPLE`                                                                                                        | `carry-and-yield.md`      | `Medium`             | `distributed`          | MISSING                                     | Single-sided pure staking; no hedge leg.                                                                                                                                                                                                                                             |
| **ML Directional (2 archetypes — both `Low`)**                                                                                |
| `ML_DIRECTIONAL_CONTINUOUS`                                                                                                   | `ml-directional.md`       | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA standard)             | **DISCREPANCY**: options-synthetics delta-hedge gap is ms-realm; needs co-loc yes + SLA premium.                                                                                                                                                                                     |
| `ML_DIRECTIONAL_EVENT`                                                                                                        | `ml-directional.md`       | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA standard)             | **DISCREPANCY**: cross-venue best-odds freshness at event-settle; same correction.                                                                                                                                                                                                   |
| **Rules Directional (2 archetypes — both `Low`)**                                                                             |
| `RULES_DIRECTIONAL`                                                                                                           | `rules-directional.md`    | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA **basic**)            | **DISCREPANCY**: no model-inference leg = faster than ML Directional (features→rule→exec); needs co-loc yes + SLA premium. Currently the WEAKEST §6 row of any latency-relevant family.                                                                                              |
| `RULES_DIRECTIONAL_CONTINUOUS`                                                                                                | `rules-directional.md`    | `Low`                | `co_located_vm`        | MISSING (aliased under `RULES_DIRECTIONAL`) | Explicit continuous variant.                                                                                                                                                                                                                                                         |
| `RULES_DIRECTIONAL_EVENT_SETTLED`                                                                                             | `rules-directional.md`    | `Low`                | `co_located_vm`        | MISSING                                     | Sports rule-based in-play betting.                                                                                                                                                                                                                                                   |
| **Stat Arb / Pairs (2 archetypes — both `Low`)**                                                                              |
| `STAT_ARB_PAIRS`                                                                                                              | `stat-arb-pairs.md`       | `Low`                | `co_located_vm`        | ✗ (co-loc **no**, SLA standard)             | **DISCREPANCY**: cross-venue pairs leg-and-hedge gap is ms-realm; same-venue ATOMIC pairs bounded by atomic primitive.                                                                                                                                                               |
| `STAT_ARB_PAIRS_FIXED`                                                                                                        | `stat-arb-pairs.md`       | `Low`                | `co_located_vm`        | MISSING (aliased under `STAT_ARB_PAIRS`)    | Cointegration-tested fixed basket.                                                                                                                                                                                                                                                   |
| `STAT_ARB_CROSS_SECTIONAL`                                                                                                    | `stat-arb-pairs.md`       | `Low`                | `co_located_vm`        | MISSING                                     | Dynamic ranking-based basket; rank-update-driven cadence.                                                                                                                                                                                                                            |
| **Vol Trading (19 archetypes — all `Medium`, 2 intra-family edge cases)**                                                     |
| `VOL_TRADING` (all 19 variants)                                                                                               | `vol-trading.md`          | `Medium`             | `distributed`          | ✓ (co-loc no, SLA standard)                 | Family default is already correct. The 19 variants inherit `Medium` → `distributed`.                                                                                                                                                                                                 |
| `VOL_MARKET_MAKING` ⚠️                                                                                                        | `vol-trading.md`          | `Medium` (family)    | `distributed` (family) | (falls under `VOL_TRADING`)                 | **Intra-family edge case**: two-sided options quoting with vol edge; delta-hedge inter-leg gap is ms-realm. The execution plan should evaluate whether this archetype needs `co_located_vm` override despite the family's `Medium` default.                                          |
| `VOL_0DTE_GAMMA_SCALPING` ⚠️                                                                                                  | `vol-trading.md`          | `Medium` (family)    | `distributed` (family) | (falls under `VOL_TRADING`)                 | **Intra-family edge case**: intraday delta-hedge of 0DTE straddles; gamma-scalping frequency demands ms-realm execution. Same evaluation as `VOL_MARKET_MAKING`.                                                                                                                     |
| **Event Driven (1 archetype — `Medium`)**                                                                                     |
| `EVENT_DRIVEN`                                                                                                                | `event-driven.md`         | `Medium`             | `distributed`          | MISSING                                     | Seconds-scale decision; time-bounded post-event window. No §6 row exists — execution plan should add one at `distributed`-consistent settings.                                                                                                                                       |
| **Portfolio (4 archetypes — `High`)**                                                                                         |
| `PORTFOLIO_MULTI_STRATEGY`                                                                                                    | `portfolio.md`            | `High`               | `distributed`          | MISSING                                     | Minutes-to-daily cadence; allocation directives, not trades.                                                                                                                                                                                                                         |
| `PORTFOLIO_RISK_PARITY`                                                                                                       | `portfolio.md`            | `High`               | `distributed`          | MISSING                                     | Daily inverse-vol reweight.                                                                                                                                                                                                                                                          |
| `PORTFOLIO_FACTOR_ALLOCATION`                                                                                                 | `portfolio.md`            | `High`               | `distributed`          | MISSING                                     | Weekly factor-exposure rebalance.                                                                                                                                                                                                                                                    |
| `PORTFOLIO_TACTICAL_OVERLAY`                                                                                                  | `portfolio.md`            | `High`               | `distributed`          | MISSING                                     | Intraday-to-daily tactical multiplier; 10s budget.                                                                                                                                                                                                                                   |
| **Event Settled Sports (covered under ML_DIRECTIONAL_EVENT / RULES_DIRECTIONAL_EVENT_SETTLED / MARKET_MAKING_EVENT_SETTLED)** |
| `EVENT_SETTLED_SPORTS`                                                                                                        | (cross-cutting)           | _(varies by family)_ | _(varies by family)_   | ✗ (co-loc no, SLA standard)                 | This §6 row is a cross-cutting label, not an archetype enum. The underlying archetypes (`ML_DIRECTIONAL_EVENT`, `RULES_DIRECTIONAL_EVENT_SETTLED`, `MARKET_MAKING_EVENT_SETTLED`) are all `Low` → `co_located_vm`. The §6 row should be removed or split into the actual archetypes. |

### Summary of discrepancies vs current §6 topology_requirements

The current `client-isolation-sla-and-runtime-profiles.md` §6 table has **10 rows**. After this derivation:

- **1 row is already correct**: `MARKET_MAKING_CONTINUOUS` (co-loc yes, SLA premium) — requires no change.
- **1 row is correct but under-specified**: `VOL_TRADING` (co-loc no, SLA standard) — consistent with
  Medium→distributed, but the 2 intra-family edge cases (`VOL_MARKET_MAKING`, `VOL_0DTE_GAMMA_SCALPING`) need separate
  evaluation.
- **7 rows are INCONSISTENT** (all currently co-loc no, SLA standard or basic — should be co-loc yes, SLA premium):
  `ARBITRAGE_STRUCTURAL`, `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT`, `CARRY_BASIS_PERP`, `CARRY_STAKED_BASIS`,
  `RULES_DIRECTIONAL`, `STAT_ARB_PAIRS`
- **1 row is a cross-cutting label**: `EVENT_SETTLED_SPORTS` — should be resolved into the actual family archetypes (all
  Low→co_located_vm).
- **~37 archetypes have NO §6 row at all** — the execution plan should add rows for the missing archetypes at their
  derived `deployment_profile` + SLA tier.

### SLA tier implications

Per `runtime-topology.yaml`'s `sla_tiers`:

- `premium`: 40ms latency budget, `min_isolated_services` = [execution, strategy, PBM, risk] — required for ALL
  `co_located_vm` archetypes (the 40ms budget covers the fastest sub-100ms E2E paths).
- `standard`: 150ms — insufficient for Low-category archetypes (MM <100ms, arb <200-300ms).
- `basic`: 500ms — insufficient for ANY latency-sensitive archetype.

→ **Every `Low`→`co_located_vm` archetype requires `min SLA: premium`.** The execution plan must update the §6 table's
min SLA column from `standard`/`basic` to `premium` for all corrected rows.

### Decision latency vs. inter-leg execution gap

Per the operator's 2026-08-10 ruling (audit plan frontmatter `source:`): **"Low" for a multi-leg archetype means the
INTER-LEG execution timing budget, not necessarily the tick-to-signal decision budget.** The family docs now distinguish
these explicitly in their `### Decision latency vs. inter-leg execution gap` subsections. The deployment_profile
derivation above is driven by the inter-leg gap requirement — when two legs MUST execute within ms of each other
(spot+hedge for basis, leader+hedge for cross-venue arb, options+delta-hedge for ML/Rules directional), `co_located_vm`
is required even if the decision cycle (tick-to-signal) could tolerate seconds-scale latency.

### Decision record

This table is the **binding decision artifact** for
`/plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` (the paired execution plan, gated
on this audit plan's completion). The execution plan's todos wire these derivations into `runtime-topology.yaml`'s
`isolation_policies.strategy-service` per-archetype section + `client-isolation-sla-and-runtime-profiles.md` §6 +
strategy-service's archetype registry. No further architectural judgment should be required — the execution plan
implements against this table, not re-derives it.

## 2026-08-10 — SLA-tier latency budget vs Low-archetype requirements check (audit todo 8)

**Check**: does `isolation_policies.strategy-service`'s existing SLA-tier framework already account for `Low`-category
archetypes needing more than the `premium` tier's 40ms `latency_budget_ms` provides? **Verdict: NO — the premium tier's
40ms does not cover any `Low` family's real requirement, and the framework has no mechanism that would detect or enforce
the mismatch.** This is the real SLA-tier-vs-archetype-requirement gap the audit asked to surface.

Per-family comparison (requirement from the populated `families/*.md` `## Latency Requirements` sections vs premium
`latency_budget_ms: 40`):

| Family                | Category | Real requirement (E2E)                                                                    | vs premium 40ms                                                                                            |
| --------------------- | -------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| market-making         | `Low`    | <100ms (tick<50ms + signal<50ms + venue-dep. fill)                                        | **EXCEEDS 40ms** — even the audit brief's own "MM <100ms fits inside 40ms" example does not fit (100 > 40) |
| arbitrage-structural  | `Low`    | <200ms (stat-arb) / <300ms (cross-exchange) / <2s (sports)                                | **EXCEEDS 40ms**                                                                                           |
| carry-and-yield basis | `Low`    | inter-leg execution gap ms-realm (<500ms operating, <100ms achievable); decision E2E <40s | **EXCEEDS 40ms** (binding constraint is the inter-leg gap, not a total-E2E number)                         |
| ml-directional        | `Low`    | <200ms / <200ms / <1s                                                                     | **EXCEEDS 40ms**                                                                                           |
| rules-directional     | `Low`    | <200ms / <200ms / <1s                                                                     | **EXCEEDS 40ms**                                                                                           |
| stat-arb-pairs        | `Low`    | <200ms / <300ms                                                                           | **EXCEEDS 40ms**                                                                                           |
| vol-trading           | Medium   | <15s                                                                                      | within (requirement looser than premium)                                                                   |
| event-driven          | Medium   | <7s                                                                                       | within                                                                                                     |
| portfolio             | High     | <60s                                                                                      | within                                                                                                     |

Three consequences make this a genuine framework gap, not just a number mismatch:

1. **The 40ms total-E2E promise is physically unachievable for live venue trades.** The family docs themselves mark
   order-to-fill as venue-dependent and NOT controllable, with CeFi matching-engine floors of 20–70ms (Binance 20–50ms
   order submit / 10–30ms fill; Deribit 15–40ms / 10–25ms; Hyperliquid 20–60ms). Total E2E = tick-to-signal +
   signal-to-order + order-to-fill; with order-to-fill alone at 20–50ms+, premium's 40ms budget is breached before the
   decision segments are counted, on every venue trade.

2. **The 40ms metric does not address the binding constraint for the multi-leg Low families — the inter-leg execution
   gap.** The budget is defined as "end-to-end order latency target (for routing decisions)"; the ms-realm lead-leg→
   hedge-leg gap that drives basis/ML/rules/stat-arb toward `co_located_vm` is bounded by co-location (in-memory
   transport between exec+strategy), which no `sla_tiers.*.latency_budget_ms` number expresses.

3. **Runtime enforcement does not cross-check the budget.** `strategy-service/strategy_service/topology_enforcement.py`
   `enforce_topology_requirements()` verifies isolation, co-location, and `min_sla_tier` rank against the archetype
   doc's `topology_requirements` frontmatter — but the archetype's declared `latency_budget_ms` is parsed and logged
   only, never compared to the active SLA tier's `latency_budget_ms`. A premium client running a Low archetype whose
   requirement exceeds 40ms would never be flagged.

Related finding for the execution plan (audit todo 10 / the paired execution plan): the runtime-enforced archetype
frontmatter (`archetypes/*.md` `topology_requirements`) is STALE vs the newly-populated family docs for exactly the
operator-corrected Low families — `CARRY_BASIS_PERP` (150ms / `standard`, no co-location),
`RULES_DIRECTIONAL_CONTINUOUS` (500ms / `basic`), `ML_DIRECTIONAL_CONTINUOUS` (150ms / `standard`),
`STAT_ARB_PAIRS_FIXED` (150ms / `standard`), `ARBITRAGE_PRICE_DISPERSION` (150ms / `standard`) — so the runtime gate
currently PERMITS these on the wrong (looser) tier without co-location, directly contradicting the
Low→`co_located_vm`→premium derivation. Only the MM family's archetype docs (10/20/30/40ms, `premium`, co-located) match
the derivation. Additionally, 5 archetype docs declare `min_sla_tier` values outside the UAC `SLATier` enum (`high` ×4
arbitrage-mev-*, `ultra-premium` ×1 market-making-queue-microstructure) — `load_topology_requirements()` casts
`SLATier(str(...))`, which raises for these, so any of those archetypes would fail to boot under enforcement.

## 2026-08-10 — runtime consumption of `families/*.md` (audit todo 9)

**Check**: does `strategy-service`'s archetype registry or engine layer currently READ the
`codex/09-strategy/architecture-v2/families/*.md` docs at runtime? **Verdict: NO — the family docs are purely
human-readable documentation today (zero programmatic consumption of `families/`), but the enforcement layer the
execution plan needs is NOT greenfield: a runtime link already exists that reads the sibling `archetypes/*.md` tree.**

Evidence:

1. **`families/*.md` has zero runtime consumers.** `rg -F "families/"` across strategy-service, deployment-service,
   unified-api-contracts, unified-trading-library and execution-service runtime code (non-doc, non-test) returns no hits
   on the `codex/09-strategy/architecture-v2/families/` path. The only "families" hits in those repos are incidental
   English uses (venue families, HTTP-status families, strategy-data shard families). Nothing parses the
   `## Latency Requirements` sections this audit populated (todos 1–7).

2. **A runtime enforcement pipeline already exists — reading `archetypes/*.md`, NOT `families/`.** The sibling tree
   `codex/09-strategy/architecture-v2/archetypes/` (59 per-archetype docs) carries the runtime-enforced
   `topology_requirements` YAML frontmatter. `strategy_service/topology_enforcement.py::load_topology_requirements()`
   parses `isolation` / `co_location` / `latency_budget_ms` / `min_sla_tier`, and
   `cli/service_entry.py::_enforce_archetype_topology_from_env()` calls `enforce_topology_requirements()` as a Phase-5
   boot gate BEFORE ServiceBootstrap — raising `TopologyRequirementError` (service refuses to start) on any mismatch vs
   the deployed topology.

3. **`runtime-topology.yaml` is the runtime isolation source.**
   `unified_trading_library/topology/topology_reader.py:: get_isolation_policy()` reads
   `unified-trading-pm/configs/runtime-topology.yaml`; `topology_enforcement._check_isolation()` compares each
   archetype's required `isolation` against it.

4. **UAC's architecture-v2 references are code citations, not runtime file reads.** `archetype_leg_spec_seeds.py` and
   registry modules cite `archetypes/<kebab>.md` in docstrings as SSOT provenance for hand-authored registry data; the
   `openapi/prospectus/*.md` files are build-time machine-generated `[CODEX-DERIVED]` docs sourced from `archetypes/`.
   Neither path reads the `families/` docs at runtime.

**Implication for the execution plan**
(`/plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`): the derived per-archetype
`deployment_profile` must be wired into the RUNTIME-ENFORCED surface — the `archetypes/*.md` `topology_requirements`
frontmatter (+ `runtime-topology.yaml` isolation/SLA rows + `client-isolation-sla-and-runtime-profiles.md` §6) — which
the todo-8 section above already found STALE vs this derivation. The family docs stay the human-readable spec layer; no
family-doc→runtime parser exists and none needs building. If the execution plan wants the family docs themselves to be
runtime-read, that would be NEW work (nothing consumes them today) — the cheaper, already-machined path is updating the
existing `archetypes/*.md` frontmatter the boot gate already enforces.
