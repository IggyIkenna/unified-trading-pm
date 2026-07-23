---
doc_type: codex-ssot
title: Value-Betting Archetype Decision (2026-04-21)
summary: >-
  Decision (2026-04-21): value-betting is NOT a separate archetype — it is the EdgeMethod.VALUE_PROB_VS_IMPLIED axis
  value on ML_DIRECTIONAL_EVENT_SETTLED when that archetype runs on sports / prediction event markets. Resolves the
  Wave-5 GAP for the v1 UI rows SPORTS_NFL_VALUE_BET_EVT_GAME + SPORTS_MLB_VALUE_BET_EVT_GAME with no new archetype and
  no code change.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, sports, prediction, ml, odds, archetype, ssot-audit]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/naming-convention.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
    archetypes/ml-directional-event-settled.md,
  ]
created: 2026-04-21
authoritative_for: [value-betting archetype decision (VALUE_PROB_VS_IMPLIED edge-method, not a separate archetype)]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Value-Betting Archetype Decision (2026-04-21)

**Context:** Audit driver for this decision — `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` Wave 6
Task B. The v1 strategy registry (`unified-trading-system-ui/lib/strategy-registry.ts`) had two entries —
`SPORTS_NFL_VALUE_BET_EVT_GAME` + `SPORTS_MLB_VALUE_BET_EVT_GAME` — that the Wave 5 equivalency audit flagged as **GAP
(semantics)** because v2 lacks a dedicated `VALUE_BETTING` archetype.

This note resolves that gap **without** introducing a new archetype.

---

## 1. Decision

**Value-betting is NOT a separate archetype. It is an `EdgeMethod` axis value (`VALUE_PROB_VS_IMPLIED`) attached to the
existing `ML_DIRECTIONAL_EVENT_SETTLED` archetype when the archetype runs on sports or prediction event markets.**

v2 already models value-betting cleanly at the **edge-method** layer, not the archetype layer. See:

- `unified_api_contracts.internal.architecture_v2.enums.EdgeMethod.VALUE_PROB_VS_IMPLIED` — the canonical enum value for
  "positive EV vs bookmaker-implied probability" edge detection.
- `strategy-service/strategy_service/engine/strategies/v2/migration/legacy_strategy_mapping.py` lines 304-382 — every
  archived v1 sports value-betting strategy (`SPORTS_VALUE_BETTING_PINNACLE_1X2`, `SPORTS_KELLY_PINNACLE_1X2`,
  `SPORTS_ML_PINNACLE_1X2`, `SPORTS_HALFTIME_ML_PINNACLE_EPL`, `SPORTS_1H_PREDICTION_EPL`) is already mapped to
  `archetype=StrategyArchetype.ML_DIRECTIONAL_EVENT_SETTLED` with
  `initial_config={"edge_method": "VALUE_PROB_VS_IMPLIED", ...}`.

The v1 UI registry's `SPORTS_NFL_VALUE_BET_EVT_GAME` + `SPORTS_MLB_VALUE_BET_EVT_GAME` rows were deemed GAP in Wave 5
because the audit looked only at archetype-level coverage. They're not gaps — they're operationally identical to the
strategy-service v2 mappings above, just for different leagues (NFL / MLB instead of EPL / NBA).

## 2. Rationale

### 2.1 Why not add a `VALUE_BETTING_EVENT_SETTLED` archetype?

- **Single-Source-of-Truth rule** (`SUB_AGENT_MANDATORY_RULES.md` §7). v2 already has a canonical home for value-betting
  semantics: `EdgeMethod.VALUE_PROB_VS_IMPLIED`. Adding a separate archetype would introduce a second SSOT for the same
  concept.
- **strategy-service has been running v2 value-betting this way since Phase 2** of
  `strategy_architecture_v2_finalization_2026_04_19`. Changing the taxonomy now would orphan production mappings for
  five archived strategies.
- **Every value-bet strategy uses a probability model** (bookmaker-implied vs model-implied). That makes them
  ML-directional by construction. `ML_DIRECTIONAL_EVENT_SETTLED` is the correct archetype;
  `edge_method=VALUE_PROB_VS_IMPLIED` is the discriminator.
- **The risk-profile concern raised in Wave 5** ("value-betting is a single-side positive-EV wager with real drawdown
  risk, distinct from riskless arb") is correct but is handled by the `StakingMethod` axis (`FRACTIONAL_KELLY`,
  `CONFIDENCE_SCALED`, `FIXED_PCT`) — not by a separate archetype. Archetype-level separation would force duplication of
  the entire sports engine.

### 2.2 Why not fold into `RULES_DIRECTIONAL_EVENT_SETTLED` instead?

Rules-directional means deterministic-threshold signals (`EdgeMethod.THRESHOLD_CROSSED`, `SURPRISE_DIRECTION`).
Value-betting requires a calibrated probability model to compare against bookmaker-implied probability — that's ML by
definition. Rules-directional for sports is reserved for things like odds-drift / steam-detection / rest-days-rules (see
`SPORTS_ODDS_DRIFT_CLV_EPL` → `RULES_DIRECTIONAL_EVENT_SETTLED` at `legacy_strategy_mapping.py:386-403`).

## 3. Implementation

No code change required. UAC `enums.py` already exports `EdgeMethod.VALUE_PROB_VS_IMPLIED`. UAC
`archetype_capability_manifest.json` already declares `ML_DIRECTIONAL_EVENT_SETTLED × SPORTS × event_settled` as
SUPPORTED on Unity / Betfair / Smarkets / Matchbook with `signal_variants: ["odds"]`.

The Wave-6 Task B code change is **representative-slot-label discoverability** — add NFL / MLB / value-bet example slot
labels under the existing SUPPORTED SPORTS cell so operators scanning the matrix can find these strategies without
reading this note. See `archetype_capability_manifest.json` delta in this wave.

## 4. Consumer-side mapping

v1 UI registry rows retire with the rest of Wave 6 Task E. Their v2 equivalents:

| v1 strategy_id                  | v2 archetype                   | v2 category | v2 instrument_type | v2 venue                   | v2 edge_method          |
| ------------------------------- | ------------------------------ | ----------- | ------------------ | -------------------------- | ----------------------- |
| `SPORTS_NFL_VALUE_BET_EVT_GAME` | `ML_DIRECTIONAL_EVENT_SETTLED` | `SPORTS`    | `event_settled`    | `unity` / `betfair_direct` | `VALUE_PROB_VS_IMPLIED` |
| `SPORTS_MLB_VALUE_BET_EVT_GAME` | `ML_DIRECTIONAL_EVENT_SETTLED` | `SPORTS`    | `event_settled`    | `unity` / `betfair_direct` | `VALUE_PROB_VS_IMPLIED` |

Slot labels (v2 canonical):

- `ML_DIRECTIONAL_EVENT_SETTLED@unity-nfl-moneyline-value-usd-prod`
- `ML_DIRECTIONAL_EVENT_SETTLED@unity-mlb-moneyline-value-usd-prod`

## 5. Cross-references

- `/codex/09-strategy/architecture-v2/strategy-registry-v2.md` — v2 registry overview.
- `/codex/09-strategy/architecture-v2/naming-convention.md` — slot label grammar.
- `/codex/09-strategy/architecture-v2/legacy-family-migration.md` § 2.2 — v1→v2 equivalency audit (post-Wave-6 zero-gap
  state).
