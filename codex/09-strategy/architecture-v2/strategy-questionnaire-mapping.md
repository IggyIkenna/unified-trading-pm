---
doc_type: codex-ssot
title: Strategy Questionnaire — Catalogue Filter Derivation
summary:
  SSOT for deriving a StrategyCatalogueFilter from the 11-axis prospect questionnaire — the categories→venueCategories
  and strategy_style→families 1-to-1 maps, the market_neutral rules-based family expansion (carry+neutral also surfaces
  structural arb), risk_profile→coverageStatuses, and leverage_preference option exclusion.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-system-ui]
scope: [engineer, sales, admin]
tags: [strategy, catalogue, questionnaire, uac, ui, mvp]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    ../../02-data/questionnaire-axes.md,
    /codex/09-strategy/architecture-v2/restriction-policy.md,
  ]
created: 2026-04-24
authoritative_for: [questionnaire-to-catalogue-filter derivation (11-axis mapping)]
referenced_by:
  [
    /codex/02-data/questionnaire-axes.md,
    /codex/08-workflows/client-onboarding.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Questionnaire — Catalogue Filter Derivation

> **Status:** canonical (2026-04-24) **Owner:** UI Architecture + Strategy Architecture v2 **SSOT for:**
> `unified-trading-system-ui/lib/questionnaire/resolve-persona.ts::seedFiltersFromQuestionnaire()`,
> `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py::QuestionnaireResponse`,
> `unified-trading-system-ui/lib/questionnaire/types.ts::QuestionnaireResponse`. **Plan:**
> [`plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
> **Companion docs:** [`../../02-data/questionnaire-axes.md`](../../02-data/questionnaire-axes.md),
> [`../../08-workflows/prospect-questionnaire-flow.md`](../../08-workflows/prospect-questionnaire-flow.md),
> [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md).

---

## §1 — Why this doc exists

The 11-axis questionnaire captures what a prospect cares about; the strategy catalogue expresses what the platform
offers along different axes (family, venue_category, share_class, coverage_status, instrument_type). The mapping between
these two vocabularies is non-trivial — some axes map 1:1, some cross-cut, some trigger rules-based expansion (e.g.
"carry + neutral" also surfaces structural arbitrage). This doc is the authoritative mapping.

Readers: UI engineers wiring new axes; sales trying to explain "why does my questionnaire filter show these strategies?"

---

## §2 — The 11 axes

Full axis catalogue (types, allowed values, validation, storage):
[`../../02-data/questionnaire-axes.md`](../../02-data/questionnaire-axes.md).

Quick classification here:

| Axis                            | Required? | Group               | Feeds filter?            |
| ------------------------------- | --------- | ------------------- | ------------------------ |
| `categories`                    | ✓         | Base                | ✓ → `venueCategories`    |
| `instrument_types`              | ✓         | Base                | Advisory only            |
| `venue_scope`                   | ✓         | Base                | Advisory only            |
| `strategy_style`                | ✓         | Base                | ✓ → `families`           |
| `service_family`                | ✓         | Base                | No — gates service route |
| `fund_structure`                | ✓         | Base                | No — contract shape      |
| `licence_region`                | —         | Reg-Umbrella        | No                       |
| `targets_3mo` / `_1yr` / `_2yr` | —         | Reg-Umbrella        | No                       |
| `own_mlro`                      | —         | Reg-Umbrella        | No                       |
| `entity_jurisdiction`           | —         | Reg-Umbrella        | No                       |
| `supported_currencies`          | —         | Reg-Umbrella        | No                       |
| `market_neutral`                | —         | Strategy-preference | ✓ → `families` expansion |
| `share_class_preferences`       | —         | Strategy-preference | ✓ → `shareClasses`       |
| `risk_profile`                  | —         | Strategy-preference | ✓ → `coverageStatuses`   |
| `target_sharpe_min`             | —         | Strategy-preference | Informational only       |
| `leverage_preference`           | —         | Strategy-preference | ✓ → excludes `option`    |

The 5 strategy-preference axes landed 2026-04-24 (UAC commit `c715109`). All are optional and `None`-defaulted, so any
response authored before 2026-04-24 deserialises cleanly.

Total = 16 axis slots, but Reg-Umbrella bundle (7 axes) only surfaces for `service_family ∈ {RegUmbrella, combo}` — a
typical DART prospect sees 11 active axes.

---

## §3 — Mapping detail

### 3.1 `categories` → `venueCategories`

```
CATEGORY_TO_VENUE = {
  "CeFi":       "CEFI",
  "DeFi":       "DEFI",
  "TradFi":     "TRADFI",
  "Sports":     "SPORTS",
  "Prediction": "PREDICTION",
}
```

Every selected category contributes one `VenueCategoryV2` to the filter. Empty selection → no category filter applied.

### 3.2 `strategy_style` → `families`

```
STYLE_TO_FAMILY = {
  "ml_directional":    "ML_DIRECTIONAL",
  "rules_directional": "RULES_DIRECTIONAL",
  "carry":             "CARRY_AND_YIELD",
  "arbitrage":         "ARBITRAGE_STRUCTURAL",
  "market_making":     "MARKET_MAKING",
  "event_driven":      "EVENT_DRIVEN",
  "vol_trading":       "VOL_TRADING",
  "stat_arb":          "STAT_ARB_PAIRS",
}
```

This is a clean 1:1 map over the 8 strategy families defined in [`README.md`](./README.md).

### 3.3 `market_neutral` → families expansion

`market_neutral` modifies the `families` filter, not a filter dimension of its own:

| `market_neutral` value | Rule                                                                                                                                                                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `"neutral"`            | If `families` already contains `CARRY_AND_YIELD`, also add `ARBITRAGE_STRUCTURAL` (structural arb is neutral by construction). If `families` is empty, seed with `[CARRY_AND_YIELD, ARBITRAGE_STRUCTURAL, MARKET_MAKING, STAT_ARB_PAIRS]`. |
| `"directional"`        | If `families` is empty, seed with `[ML_DIRECTIONAL, RULES_DIRECTIONAL, EVENT_DRIVEN]`. Leave existing non-empty selection untouched.                                                                                                       |
| `"both"` / `null`      | No modification.                                                                                                                                                                                                                           |

The "carry + neutral → also arb" rule is the canonical example of the rules-based expansion layer — it captures "user
doesn't know arb is a neutral-carry neighbour" without the user having to pick both styles explicitly.

### 3.4 `share_class_preferences` → `shareClasses`

`share_class_preferences` is an array (the UAC field is `QuestionnaireShareClassPreference[]`). Every preference maps to
a set of concrete share classes, and the final filter is the union:

```
SHARE_CLASS_MAP = {
  "usd_only":    ["USDT", "USDC", "USD", "GBP", "EUR"],
  "btc_neutral": ["BTC"],
  "eth_neutral": ["ETH"],
  # "any" intentionally unmapped → no filter applied
}
```

Empty array → no share-class filter. `["usd_only", "btc_neutral"]` → `["USDT", "USDC", "USD", "GBP", "EUR", "BTC"]`.

### 3.5 `risk_profile` → `coverageStatuses`

| `risk_profile` | `coverageStatuses`         | Semantics                                                |
| -------------- | -------------------------- | -------------------------------------------------------- |
| `"low"`        | `["SUPPORTED"]`            | Only fully-wired, production-proven instances.           |
| `"medium"`     | no filter                  | Default — shows SUPPORTED + PARTIAL + stubs.             |
| `"high"`       | `["SUPPORTED", "PARTIAL"]` | Willing to see venues / share-classes still rolling out. |
| `null`         | no filter                  | Same as medium.                                          |

### 3.6 `leverage_preference=none` → instrument-type exclusion

`leverage_preference` does not add a filter — it removes one. When the value is `"none"`, the UI post-processes the FOMO
feed to drop rows whose `instrument_type` is `option`. Other values (`"low"`, `"medium"`, `"any"`) apply no exclusion.

Note: `leverage_preference` is intentionally not wired into the `StrategyCatalogueFilter` shape — the surface-level
exclusion is a lighter intervention than a registry filter because we still want the archetype visible for the client to
see "you could unlock this by opting into leverage".

### 3.7 `target_sharpe_min` → informational

This axis captures the client's Sharpe threshold but does **not** hard-filter the catalogue. Rationale: Sharpe on
`odum-paper` + `odum-live` is noisy short-term; thresholding at questionnaire submit would prematurely hide candidates
that will clear the bar after more runtime. Sales uses this axis in step 6 of onboarding (see
[`../../08-workflows/client-onboarding.md`](../../08-workflows/client-onboarding.md)) to frame the conversation.

### 3.8 Axes not feeding the filter

- `instrument_types`, `venue_scope` — stored but not applied. The Explore tab shows archetype-level tiles; per-instance
  venue/instrument drill-downs happen on the reporting page after click-through.
- `service_family` — gates which service tiles are visible (see
  [`../../04-architecture/commercial-service-families.md`](../../04-architecture/commercial-service-families.md)), not
  the catalogue filter itself.
- `fund_structure` — contract-shape axis (SMA / Pooled / NA); affects onboarding, not catalogue.
- All Reg-Umbrella axes — regulatory framing; captured for sales handoff, not for filter derivation.

---

## §4 — Worked example: Desmond

Desmond H-W's pre-seeded questionnaire (see
[`../../14-customer-journeys/demo-ops/profiles/desmond-dart-full.yaml`](../../14-customer-journeys/demo-ops/profiles/desmond-dart-full.yaml)):

```yaml
categories: [CeFi, DeFi]
instrument_types: [perp]
venue_scope: all
strategy_style: [carry, arbitrage, stat_arb]
service_family: DART
fund_structure: [prop]
market_neutral: neutral
share_class_preferences: [] # any implied
risk_profile: low
target_sharpe_min: null
leverage_preference: low
```

Derived `StrategyCatalogueFilter`:

```
venueCategories:   [CEFI, DEFI]
families:          [CARRY_AND_YIELD, ARBITRAGE_STRUCTURAL, STAT_ARB_PAIRS]
                   // carry + neutral rule adds ARBITRAGE_STRUCTURAL explicitly;
                   // arb + stat_arb already included from styles.
shareClasses:      (no filter — share_class_preferences empty)
coverageStatuses:  [SUPPORTED]   // from risk_profile=low
// leverage_preference=low → no option exclusion; option would be excluded only at "none"
```

On `/services/strategy-catalogue?tab=explore&from=questionnaire&...`, Desmond sees the CeFi + DeFi subset of carry,
structural-arb, and pairs-arb families, gated to SUPPORTED coverage. With `NEXT_PUBLIC_AUTH_PROVIDER=demo`, the
`DemoPlanToggle` lets him flip to `desmond-signals-in` to preview the Signals-In universe (same catalogue; Research +
Promote locked).

Expected hits include: `CARRY_BASIS_PERP` on Binance / OKX / Hyperliquid perps; `CARRY_STAKED_BASIS` on Lido / Aave
compositions; `ARBITRAGE_PRICE_DISPERSION` across CEX pairs; `STAT_ARB_PAIRS_FIXED` on CeFi pair baskets.

---

## §5 — Related files

**UI (TypeScript):**

- Schema mirror: `unified-trading-system-ui/lib/questionnaire/types.ts::QuestionnaireResponse`.
- Seed function: `unified-trading-system-ui/lib/questionnaire/resolve-persona.ts::seedFiltersFromQuestionnaire()`.
- Filter shape: `unified-trading-system-ui/lib/architecture-v2/catalogue-filter.ts::StrategyCatalogueFilter`.
- Catalogue surface: `unified-trading-system-ui/components/strategy-catalogue/StrategyCatalogueSurface.tsx`.
- Questionnaire submit + redirect: `unified-trading-system-ui/app/(public)/questionnaire/page.tsx`.

**UAC (Python — canonical schema):**

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py::QuestionnaireResponse`.

---

## §6 — Extension protocol

Adding a new axis is a cross-repo change. Do all of these in one plan:

1. Add the field to `QuestionnaireResponse` in UAC with `None` / empty-tuple default (backwards-compat rule from
   [`prospect-questionnaire-flow.md`](../../08-workflows/prospect-questionnaire-flow.md) §2).
2. Mirror the field in UI `lib/questionnaire/types.ts` with the same optionality.
3. Add the corresponding question to `app/(public)/questionnaire/page.tsx`.
4. Decide: does it feed the filter? If yes, extend `seedFiltersFromQuestionnaire()` and declare the mapping below §3.
5. Update [`../../02-data/questionnaire-axes.md`](../../02-data/questionnaire-axes.md) with the full axis entry.
6. If it affects admin playback, surface it in `/admin/organizations/[id]` questionnaire card.
7. Update this doc's §3 with the new mapping row + §4 worked example if the axis materially reshapes a common shape.
