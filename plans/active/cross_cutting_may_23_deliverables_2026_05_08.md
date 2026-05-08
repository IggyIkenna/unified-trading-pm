---
type: plan
plan_type: meta
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
deadline: 2026-05-23
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: cross-cutting-may-23-deliverables-2026-05-08
parent: cross_cutting_may_23_2026
related_plans:
  - master_to_live_defi_2026_05_23
  - cross_cutting_may_23_2026
  - strategy_and_dart_master_2026_05_07
  - defi_master_2026_05_07
  - cefi_master_2026_05_07
---

# Cross-cutting May-23 deliverables — catalogue / IDs / clients / DART (2026-05-08)

## Why this plan exists

The [`cross_cutting_may_23_2026`](../epics/cross_cutting_may_23_2026.epic.md) epic lists 5 non-negotiable deliverables
for the May-23 cutover. Today's daily splits cover **#5 Infrastructure** (across Ikenna T2/T4/T5 + Harsh T3) but DO NOT
cover deliverables **#1 Strategy catalogue, #2 Strategy IDs, #3 Clients + Accounts, #4 UI replication / DART
manual-trade lane**. With 15 days to cutover and "non-negotiable + hard requirement" framing, those 4 deliverables need
a dedicated tab on each side starting today.

This plan is the **shared plan-of-record** for the 4 gap deliverables. Ikenna T6 owns design (UAC SSOTs + scope
decisions); Harsh T6 owns implementation (consumer wiring + DART UI). Hard cross-side ordering: Ikenna ships UAC SSOTs
first; Harsh consumes after Ikenna's `## Open questions` resolved.

## End-state at May 23 (success criteria)

Mirrors the cross_cutting epic's checkbox set — when this plan flips DONE, those 4 epic deliverables flip too.

### #1 Strategy catalogue (HARD)

- [ ] [DESIGN+UAC] **Catalogue UAC schema declared** — archetype × venue × instrument-type matrix shape; per-archetype
      config schema (collateral, hedge ratios, position caps, kill-switch thresholds). Owner: Ikenna T6. **🟡 BLOCKED
      2026-05-08 by uac-strategy-catalogue-ids-tab6a** — every plan-body symbol already exists in UAC under
      `internal/architecture_v2/` + `internal/domain/strategy_service/` in a richer 9-family / 46-archetype shape, and
      `unified_api_contracts/strategy.py` root facade is already 207 lines. Greenfield `canonical/domain/strategy/`
      would create parallel SSOTs + collide with the live facade. Operator triage required — see
      [`issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md`](issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md)
      for full mapping table + Option A (extend v2, recommended) / B (deprecate-and-migrate) / C (parallel-SSOT, NOT
      recommended) recommendation.
- [ ] [SCRIPT] **Catalogue rows populated** for every archetype family known to be in scope: carry (3 sub-types:
      staked-basis / vanilla-basis / cross-venue), price-arb (3 sub-types: same-day-expiry / ETF↔future / cross-venue),
      ML prediction (per-asset-group: CeFi-ML / S&P-prediction / sports-ML), prediction-markets (4 sub-types: Polymarket
      / Kalshi / Opinion-Trade / CME-event-arb), and any others surfaced from
      [`codex/09-strategy/strategy-summary.md`](../../codex/09-strategy/strategy-summary.md). Owner: Harsh T6.
- [ ] [SCRIPT] **Per-archetype venue matrix populated** — every (archetype, venue, instrument-type) combination known to
      be feasible is a row, even if not launching this cycle. Owner: Harsh T6.
- [ ] [SCRIPT] **Per-archetype config parameters declared** (collateral, hedge ratios, position caps, kill-switch
      thresholds). Owner: Harsh T6.
- [ ] [BUILD] **Strategy catalogue UI** reflects the full universe (filter by asset_group / archetype / venue /
      live-vs-backtest). Owner: Harsh T6.

### #2 Strategy IDs

- [ ] [DESIGN+UAC] **Strategy ID schema in UAC** — canonical naming convention + versioning + (archetype, venue,
      instrument-type, client) → ID derivation function. Owner: Ikenna T6. **🟡 BLOCKED 2026-05-08 by
      uac-strategy-catalogue-ids-tab6a** — `parse_strategy_id` + `format_strategy_id` already shipped (UAC@5083d65
      "feat(strategy): add parse_strategy_id + format_strategy_id canonical naming helpers") with the canonical 6-axis
      slot grammar `archetype@venue-asset-instrument-period-quote-env` + FQ form `FAMILY.ARCHETYPE.slot_id`. Plan-body's
      proposed 4-axis `<archetype>.<venue>.<instrument_type>.v<N>` is a regression (drops period / quote / env axes).
      Operator triage required — same issue doc as #1 above.
- [ ] [SCRIPT] **Strategy ID registry populated** for every catalogue row. Owner: Harsh T6.
- [ ] [SCRIPT] **Strategy ID refactor sweep** — every code-path that creates a trade/fill/signal/model-inference uses
      strategy IDs (not free-form strings). Mechanical sweep across execution-service, strategy-service,
      ml-inference-service, pnl-attribution-service, batch-live-reconciliation-service, position-balance-monitor,
      alerting-service, deployment-api. Owner: Harsh T6.

### #3 Clients + Accounts

- [x] [DESIGN+UAC] **Client model in UAC stable** — client + account-per-venue mapping schema. Owner: Ikenna T6.
      (uac@3591037 — `canonical/domain/client/model.py` + `client.py` facade + 36 unit tests; Client + VenueAccount
      frozen dataclasses; ClientId / AccountId TypeAliases; CLIENTS_SEED with 4 live CeFi venues + 3 DeFi chains;
      secret-manager naming convention documented per onboarding-checklist Phase 1.2.)
- [x] [DESIGN+UAC] **Capital allocation matrix declared** — per (client, archetype, venue) entry; respected at execution
      time. Owner: Ikenna T6. (uac@3591037 — CapitalAllocation frozen dataclass with **post_init** bounds checks;
      AllocationViolationError + validate_allocation_respect for execution-service fail-loud at order time;
      is_within_allocation advisory for UI gates; CAPITAL_ALLOCATION_SEED for May-23 archetype slice;
      get_capital_allocation + is_allocation_declared lookups; ArchetypeRef TypeAlias widens to StrategyArchetype | str
      when 6.A's catalogue lands, single-edit migration.)
- [ ] [SCRIPT] **Client-account-strategy tagging propagated** through every live trade + batch backtest result. Hooks
      into the strategy ID refactor sweep above. Owner: Harsh T6.

### #4 UI replication / DART manual-trade lane

- [x] [DESIGN] **DART scope decision** — per-archetype list of operator-replicable manual surfaces. Operator-confirmed
      bar: every live archetype must have a manual fallback. Sports backtest exec validation manual surface acceptable
      (not live). Owner: Ikenna T6. **DONE 2026-05-08 (Tab 6.C)** — `unified-trading-pm@ab595616` shipped
      [`codex/09-strategy/cross-cutting/dart-manual-trade-spec.md`](../../codex/09-strategy/cross-cutting/dart-manual-trade-spec.md)
      (8 sections: scope decision matrix for all 11 StrategyInstruction action types · per-archetype manual-fallback map
      covering all 18 codex archetypes · 5 BUILDs Harsh T6 ships · strategy_id attribution discipline · capital
      allocation respect · post-May-23 deferrals). Cross-link added to peer doc `operational-modes-matrix.md` via
      `unified-trading-pm@2a0d105d` (parallel-agent commit, content correct). Plan open questions #2 + #4 resolutions
      captured.
- [ ] [BUILD] **DART manual DeFi swap / lend / borrow / stake** for the carry-staked-basis archetype across enabled
      chains. Owner: Harsh T6.
- [ ] [BUILD] **DART manual CeFi order placement** across the 4 live CeFi venues (Bybit / Deribit / Binance / OKX).
      Owner: Harsh T6.
- [ ] [BUILD] **DART manual ML training trigger** (pause-resume model retraining for any in-flight ML archetype). Owner:
      Harsh T6.
- [ ] [BUILD] **DART manual sports bet placement** for sports backtest exec validation. Owner: Harsh T6.
- [ ] [BUILD] **DART manual prediction-market trade** for Polymarket / Kalshi / Opinion-Trade / CME-event-arb backtest.
      Owner: Harsh T6.

## Execution DAG

```
Ikenna T6 (DESIGN — UAC SSOTs + scope decisions)
   │
   ├─ #1 Catalogue UAC schema  ─┐
   ├─ #2 Strategy ID schema    ─┤
   ├─ #3 Client model + matrix ─┼─►  Harsh T6 (BUILD — consumer wiring + DART UI)
   └─ #4 DART scope decision   ─┘       │
                                         ├─ #1 Catalogue rows + UI
                                         ├─ #2 ID registry + refactor sweep
                                         ├─ #3 Tagging propagation
                                         └─ #4 5 DART manual surfaces
```

**Hard cross-side ordering**: Ikenna T6 ships UAC SSOTs (#1-#3 schemas + #4 spec) first; Harsh T6 consumes after.
Mitigation: Harsh T6 can start mechanical scaffolding (e.g. strategy ID refactor IDENTIFIES every callsite to update
without touching them yet) while Ikenna T6 finalizes UAC schema.

## Estimated AI-days

- Ikenna T6: ~10 AI-days (catalogue UAC ~3 + ID schema ~2 + client model ~2 + DART scope ~2 + catalogue UI scope ~1)
- Harsh T6: ~12 AI-days (catalogue rows ~3 + ID refactor ~3 + client tagging ~2 + 5 DART surfaces ~4)
- Total: ~22 AI-days across 15 days to cutover ≈ 1.5 days of solo work for one operator with parallel agent leverage on
  each side.

## Open questions

- [ ] **Strategy catalogue completeness — bar for "complete"?** Every (archetype, venue, instrument-type) combination,
      or archetype-level completeness with venue/instrument lookups deferred? **Default**: full enumeration including
      not-launching-this-cycle archetypes (per cross_cutting epic deliverable #1 framing — "the universe is visible").
      Confirm before Ikenna T6 starts populating catalogue rows.
- [ ] **DART manual-trade lane scope**: is operator-only manual sufficient, or do we need a third-party broker-style
      DART for external operators? **Default**: operator-only this cycle; external operators post-May-23.
- [ ] **Strategy ID versioning rule**: hash-based / sequential / semver-style? Used for batch-vs-live reconciliation
      attribution. **Default**: `<archetype>.<venue>.<instrument_type>.v<N>` semver-style with N incremented when config
      changes materially.
- [ ] **DART manual prediction-market trade scope**: backtest-only or include live wiring (even if disabled by default)?
      **Default**: backtest-only to match the prediction_markets epic scope.

## Sub-plans this plan coordinates

This plan owns the 4 cross-cutting deliverables; downstream consumers reference these once shipped:

- [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.md) Group F + G — once strategy IDs land, every
  Group F item (PBM / R&E / pnl-attribution / batch-live-recon / alerting) gates on ID-attribution wiring. Group G item
  23 (DART manual-trade gate) is THIS plan's deliverable #4.
- [`strategy_and_dart_master_2026_05_07`](../epics/strategy_and_dart_master_2026_05_07.md) — folds in this plan's
  catalogue + ID + client scope; this plan is the May-23 critical-path slice.
- [`defi_master_2026_05_07`](defi_master_2026_05_07.md) — Fork 1 paper-trade smoke uses strategy IDs once shipped.
- [`cefi_master_2026_05_07`](../epics/cefi_master_2026_05_07.md) — CeFi ML live archetype tagged with strategy IDs.
- [`alerting_service_live_rules_2026_05_07`](alerting_service_live_rules_2026_05_07.md) — alerting rules emit strategy
  ID per fired alert (per cross_cutting epic #2 use-case "alerting (which strategy fired)").

## See also

- [`plans/epics/cross_cutting_may_23_2026.epic.md`](../epics/cross_cutting_may_23_2026.epic.md) — parent epic
- [`codex/09-strategy/strategy-summary.md`](../../codex/09-strategy/strategy-summary.md) — 8-family / 18-archetype
  catalogue baseline (existing SSOT this plan extends)
- [`codex/09-strategy/cross-cutting/onboarding-checklist.md`](../../codex/09-strategy/cross-cutting/onboarding-checklist.md)
  — strategy onboarding flow that needs ID-attribution wiring
- [`codex/09-strategy/cross-cutting/operational-modes-matrix.md`](../../codex/09-strategy/cross-cutting/operational-modes-matrix.md)
  — DART manual-trade lane SSOT

## DONE-2026-05-08 (Tab 6.B) — Client model + capital allocation

Sub-agent 6.B shipped deliverable #3 [DESIGN+UAC] tier:

- **uac@3591037** `feat(uac): client model + capital allocation matrix SSOT — cross_cutting #3` —
  `unified_api_contracts/canonical/domain/client/model.py` + `unified_api_contracts/client.py` facade +
  `tests/unit/test_client_model.py` (36 unit tests passing, basedpyright clean, ruff clean).
- Pushed to `live-defi-rollout` (verified `0 0` ahead/behind via `git rev-list --left-right --count HEAD...origin/...`).

The [SCRIPT] **Client-account-strategy tagging propagated** sub-todo (Harsh T6) consumes this UAC and remains pending.

## Strategy catalogue UI route — scope assignment (2026-05-08, Tab 6.C)

**Decision** (resolves plan open question #1 default + cross_cutting epic deliverable #1 [BUILD] subitem):

- **Route**: existing `/api/trading/strategies/catalog` endpoint in
  [`unified-trading-api/unified_trading_api/routes/trading_analytics.py`](../../../unified-trading-api/unified_trading_api/routes/trading_analytics.py)
  (line 369) returns the full catalogue from UAC `STRATEGY_REGISTRY`. UI consumer surface lives in
  [`unified-trading-system-ui/lib/architecture-v2/catalogue-filter.ts`](../../../unified-trading-system-ui/lib/architecture-v2/catalogue-filter.ts)
  - the architecture-v2 page set under `unified-trading-system-ui/app/(platform)/services/`. **Not a new deployment-ui
    route** — the strategy catalogue is a trading-domain surface, not a deployment-ops surface, so it belongs in the
    trading UI (where the DART terminal already lives).
- **Filter axes (4)**: `asset_group` × `archetype` × `venue` × `live_vs_backtest`. Map to UAC v2 enum surface as:
  - `asset_group`: per `MarketAssetGroup` enum (cefi / defi / tradfi / sports / prediction).
  - `archetype`: per `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` (currently 46 members
    after the 2026-04-25 PORTFOLIO + MEV + VOL expansions; codex `strategy-summary.md` 18-archetype baseline is stale
    per
    [`plans/active/issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md`](issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md)).
  - `venue`: per `STRATEGY_REGISTRY` row's venue field (per-venue rows already populated).
  - `live_vs_backtest`: derived from `archetype_capability.CoverageStatus` (`SUPPORTED` = live; `PARTIAL` / `BLOCKED` =
    backtest-only this cycle).
- **Data source**: UAC `STRATEGY_REGISTRY` (already populated via `ARCHETYPE_CAPABILITY_REGISTRY` + per-cell
  `representative_slot_labels`). For the per-archetype operational risk knobs (collateral / hedge_ratio /
  position_cap_usd / kill_switch_drawdown_pct / kill_switch_position_breach_pct), the genuine gap (per Tab 6.A issue doc
  Option A) is `ArchetypeConfig` not yet in UAC — this consumer reads it from the registry once Tab 6.A's triage
  produces the schema. UAC `client.py` facade + `CAPITAL_ALLOCATION` per Tab 6.B's deliverable #3 is consumed at the
  per-row drilldown for active client allocations.
- **Owner**: Harsh Tab 6 (cross_cutting plan deliverable #1 [BUILD] subitem). Implementation = enrichment of existing
  trading-UI `/services/<archetype>` routes + the `catalogue-filter.ts` filter helpers, NOT greenfield. Per-row click
  drilldown = `CatalogueRow` config view + derived `strategy_id` (via `format_strategy_id`) + active `CapitalAllocation`
  cells (per client × archetype × venue) from UAC `client.py`.
- **Acceptance**: every catalogue row visible in UI; per-row drilldown shows config + strategy_id + allocations; filter
  axes operate orthogonally; live archetypes for May-23 (carry_staked_basis, carry_basis_perp,
  ml_directional_continuous, carry_basis_dated) are visually distinct from backtest-only archetypes.

> **Why not deployment-ui**: the cross*cutting plan defaulted to "filter by asset_group / archetype / venue /
> live-vs-backtest" without specifying \_which* UI. Audit 2026-05-08 found the existing `STRATEGY_REGISTRY` consumer is
> `unified_trading_api.routes.trading_analytics` + `unified-trading-system-ui/lib/architecture-v2/`; no surface in
> deployment-ui. Deployment-ui owns operational ops (deploy / monitor / data-status / readiness / config) per
> [`deployment_ui_lifecycle_tabs_2026_05_08`](deployment_ui_lifecycle_tabs_2026_05_08.md). Strategy catalogue is a
> trading-domain artifact — putting it in deployment-ui would split the architecture-v2 surface across two UIs and break
> the OpenAPI / UI generation pipeline (`unified_trading_pm.scripts.openapi.generate_ui_reference_data`).

**Cross-link banner** to Harsh Tab 3's `deployment_ui_lifecycle_tabs_2026_05_08` lands in same logical unit as this
section (1-line append-only banner).

## DONE-2026-05-08 (Tab 6.C) — DART spec + UI scope

Sub-agent 6.C shipped deliverable #4 [DESIGN] tier + deliverable #1 [DESIGN] (UI scope assignment) tier:

- **unified-trading-pm@ab595616** `docs(codex): add DART manual-trade-spec — per-archetype scope for May-23 cutover` —
  NEW
  [`codex/09-strategy/cross-cutting/dart-manual-trade-spec.md`](../../codex/09-strategy/cross-cutting/dart-manual-trade-spec.md)
  (314 lines, 8 sections covering all 11 StrategyInstruction action types + 18 codex archetypes + 5 BUILDs Harsh T6
  ships + strategy_id attribution + capital allocation respect + post-May-23 deferrals).
- **unified-trading-pm@2a0d105d** (parallel-agent commit, content correct) — cross-link to peer doc
  `operational-modes-matrix.md` Related-documents section.
- **unified-trading-pm@<this-flip-commit>** — plan flip + UI scope assignment section + 1-line cross-reference banner
  appended to `deployment_ui_lifecycle_tabs_2026_05_08.md`.

**Foot-guns encountered**: parallel-agent index hijacking foot-gun #1 incident — `ab595616` accidentally bundled 2
foreign files (`plans/active/alerting_service_live_rules_2026_05_07.md` + `plans/archive/cefi_ml_may_23_2026.epic.md`)
because parallel agents were re-staging files into my index between my `git restore --staged` and my `git commit` calls.
Workspace rule "ship work + accept muddled attribution + document via auto-memory" applied; revert would lose the DART
codex doc. The 2 foreign-file diffs are still semantically correct (parallel agents' WIP — not destructive edits) and
pass prettier/QG.

The [BUILD] subitems for deliverables #1 (catalogue UI build) + #4 (5 DART manual surfaces) remain pending — owned by
Harsh T6 per cross-side handshake. The strategy_id grammar this spec consumes is owned by Tab 6.A (currently 🟡 BLOCKED
pending operator triage of
[`plans/active/issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md`](issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md)).

## DONE-2026-05-08 (Tab 6 main) — cycle close

Tab 6 main agent dispatched 3 parallel sub-agents per work-split plan
[`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) § "TAB 6 — Cross-cutting design". Cycle outcome:

| Sub-agent      | Scope                                                      | Status                                | Commits                                                                                                                                              |
| -------------- | ---------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **6.A**        | UAC strategy catalogue + IDs (#1+#2)                       | 🟡 BLOCKED — case-5 BIG finding filed | `pm@6ab7a0d8` (issue doc); zero UAC code shipped (intentional)                                                                                       |
| **6.B**        | UAC client model + cap allocation (#3)                     | ⚠️ SHIPPED with parallel-SSOT debt    | `uac@3591037` + `pm@366c66a4`                                                                                                                        |
| **6.C**        | DART codex doc + UI scope (#4 + #1 [DESIGN] BUILD subitem) | ✅ SHIPPED clean                      | `pm@ab595616` (DART doc) + `pm@2a0d105d` (peer-doc cross-link, parallel-agent commit) + `pm@b6a93b25` (plan flip + UI scope assignment + DONE block) |
| **Tab 6 main** | Issue-doc consolidation + this DONE block                  | ✅ SHIPPED                            | `pm@<this-commit>` (issue doc 6.B addendum + Tab 6 main DONE block)                                                                                  |

**Done-definition vs work-split plan TAB 6 § "Done-definition":**

- ☐ **All 4 UAC schemas merged: catalogue, IDs, client model, capital allocation** — _partial._ Catalogue + IDs (6.A's
  scope) BLOCKED on operator Option A/B/C call (the work was already shipped under existing UAC v2 SSOTs; net-new code
  would have created parallel-SSOT debt). Client model (6.B's scope) shipped as parallel SSOT to existing
  `ClientDefinition` + `TradingAccount` — needs partial revert per Option A. Capital allocation (genuine gap) shipped
  cleanly + needs migration to `internal/architecture_v2/capital_allocation.py` per Option A.
- ✅ **DART scope codex doc shipped (operator-confirmed) + Harsh T6 has executable spec** — `pm@ab595616` (314 lines, 8
  sections, all 11 StrategyInstruction action types + all 18 codex archetypes). Plan open questions #2 + #4 resolved per
  defaults.
- ✅ **Strategy catalogue UI scope assigned** — refined: route is in **trading-UI**
  (`unified-trading-system-ui/lib/architecture-v2/`), NOT deployment-UI. Plan open question #1 resolved.
- ◐ **Plan-of-record `## Open questions` resolved or escalated** — Q1 + Q2 + Q4 resolved by 6.C; Q3 (versioning rule)
  remains BLOCKED on Tab 6.A operator triage; new findings raised (none — all surfaced into the issue doc instead).
- ✅ **DONE block appended to plan-of-record citing every UAC + codex commit sha** — 6.B + 6.C wrote their own DONE
  blocks; this Tab 6 main DONE block consolidates the cycle outcome.

**Cross-side handoff status (Ikenna T6 → Harsh T6):**

- Deliverable #1 [SCRIPT] catalogue rows / [SCRIPT] per-archetype venue matrix / [SCRIPT] per-archetype config
  parameters (Harsh T6) — **BLOCKED** until operator triages Option A; right shape becomes "audit existing
  `STRATEGY_REGISTRY` + `ARCHETYPE_CAPABILITY_REGISTRY` for May-23 live archetype rows; add missing rows + the new
  `ArchetypeConfig` operational risk knobs."
- Deliverable #2 [SCRIPT] strategy ID registry populated / [SCRIPT] strategy ID refactor sweep (Harsh T6) — **BLOCKED**
  on same operator call; under Option A the existing `format_strategy_id` / `parse_strategy_id` 6-axis grammar is the
  target.
- Deliverable #3 [SCRIPT] client-account-strategy tagging propagated (Harsh T6) — partially unblocked: tagging schema
  consumes existing `ClientDefinition` + `TradingAccount` (per Option A migration), and `CapitalAllocation` once
  re-exported from `strategy.py` facade. Pending Option A migration per issue doc addendum.
- Deliverable #4 [BUILD] 5 DART manual surfaces (Harsh T6) — UNBLOCKED. Spec lives at
  [`codex/09-strategy/cross-cutting/dart-manual-trade-spec.md`](../../codex/09-strategy/cross-cutting/dart-manual-trade-spec.md).
  Strategy ID attribution per spec § 5 defers to whichever grammar Option A produces (existing 6-axis grammar expected).
- Deliverable #1 [BUILD] strategy catalogue UI (Harsh T6) — UNBLOCKED in scope (route + filter axes + acceptance
  criteria declared above § "Strategy catalogue UI route — scope assignment"); the consumer-side data shape depends on
  Option A's `ArchetypeConfig` schema landing.

**Operator action requested (Tab 6 main):** triage
[`plans/active/issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md`](issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md)
with Option A vs B vs C call. Recommended: **Option A — extend existing v2 SSOTs**. Under Option A the cycle's remaining
work is well-bounded: ship `ArchetypeConfig` in `internal/architecture_v2/archetype_config.py` (1-2 AI-days); migrate
Tab 6.B's `CapitalAllocation` to `internal/architecture_v2/capital_allocation.py` + revert `Client` + `VenueAccount` (1
AI-day); refresh codex `strategy-summary.md` to 9-family / 46-archetype (0.5 AI-days); audit `STRATEGY_REGISTRY` for
May-23 live archetype completeness (1 AI-day). Total ~3-4 AI-days to fully close cross_cutting deliverables #1 + #2 + #3
— well within the May-23 deadline if Option A picked promptly.

Tab 6 main going quiet.
