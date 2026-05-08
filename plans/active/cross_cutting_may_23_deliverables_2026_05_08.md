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

- [ ] [DESIGN+UAC] **Client model in UAC stable** — client + account-per-venue mapping schema. Owner: Ikenna T6.
- [ ] [DESIGN+UAC] **Capital allocation matrix declared** — per (client, archetype, venue) entry; respected at execution
      time. Owner: Ikenna T6.
- [ ] [SCRIPT] **Client-account-strategy tagging propagated** through every live trade + batch backtest result. Hooks
      into the strategy ID refactor sweep above. Owner: Harsh T6.

### #4 UI replication / DART manual-trade lane

- [ ] [DESIGN] **DART scope decision** — per-archetype list of operator-replicable manual surfaces. Operator-confirmed
      bar: every live archetype must have a manual fallback. Sports backtest exec validation manual surface acceptable
      (not live). Owner: Ikenna T6.
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
