---
doc_type: codex-ssot
title: Questionnaire Axes — Full Catalogue
summary: >-
  Questionnaire axes catalogue SSOT — the shared QuestionnaireResponse Pydantic/TS model (18 axis slots: 6 required base
  + 7 Reg-Umbrella + 5 strategy-preference), each axis's type / allowed-values / Firestore path / catalogue-filter
  dimension, the backwards-compat optional-default rule, and the model_validate validation rules; this is the schema
  (axis -> catalogue-filter derivation lives in the strategy-questionnaire-mapping doc).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-system-ui]
scope: [engineer, sales, admin]
tags: [uac, ui, questionnaire, onboarding, strategy]
related:
  [
    /codex/08-workflows/prospect-questionnaire-flow.md,
    /codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md,
    /codex/08-workflows/client-onboarding.md,
    /codex/04-architecture/commercial-service-families.md,
  ]
created: 2026-04-24
authoritative_for: [QuestionnaireResponse axis catalogue schema]
referenced_by:
  [
    /codex/08-workflows/client-onboarding.md,
    /codex/09-strategy/architecture-v2/instruments-resolver-architecture.md,
    /codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md,
    /codex/14-customer-journeys/demo-ops/staging-demo-setup.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Questionnaire Axes — Full Catalogue

> **Status:** canonical (2026-04-24) **Owner:** UI Architecture + UAC Architecture **SSOT for:**
> `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py::QuestionnaireResponse`,
> `unified-trading-system-ui/lib/questionnaire/types.ts::QuestionnaireResponse`. **Plans:**
> [`plans/archive/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md`](../../plans/archive/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md),
> [`plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md).
> **Companion docs:**
> [`/codex/08-workflows/prospect-questionnaire-flow.md`](/codex/08-workflows/prospect-questionnaire-flow.md) (form +
> admin playback + docs flow),
> [`/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md`](/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md)
> (axis → catalogue-filter derivation).

---

## §1 — Why one catalogue

`QuestionnaireResponse` is the single Pydantic model shared across UAC, UI, Firestore persistence, admin playback, and
demo-provider preseed. Any field you see on `/questionnaire` comes from here; any filter seeded from a response is
derived here. This doc is the authoritative catalogue of axes, types, allowed values, and storage paths.

Related but distinct:
[`strategy-questionnaire-mapping.md`](/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md) is the
derivation rules (axis → `StrategyCatalogueFilter`). This doc is the schema.

---

## §2 — Three axis groups

| Group               | Count | Required?                                                      | Landed     |
| ------------------- | ----- | -------------------------------------------------------------- | ---------- |
| Base                | 6     | ✓ (all required)                                               | original   |
| Reg-Umbrella        | 7     | — (surfaced only when `service_family ∈ {RegUmbrella, combo}`) | 2026-04-21 |
| Strategy-preference | 5     | — (optional for all service families)                          | 2026-04-24 |

Total = 18 axis slots. Typical DART prospect fills 11 (base + strategy-preference). Reg-Umbrella prospect fills 18. All
optional axes default to `None` (scalars) / `()` (tuples), so responses authored before an extension deserialise cleanly
— see §5.

---

## §3 — Base axes (6, required)

### 3.1 `categories: tuple[QuestionnaireCategory, ...]`

- **Python literal:** `Literal["CeFi", "DeFi", "TradFi", "Sports", "Prediction"]`
- **TS type:** `QuestionnaireCategory`
- **Allowed values:** `CeFi`, `DeFi`, `TradFi`, `Sports`, `Prediction`
- **Default on blank submit:** empty tuple (UAC overlay logic falls back to base profile)
- **Firestore path:** `/questionnaires/{id}/categories`
- **Filter dimension:** `venueCategories` (1:1 map to `VenueCategoryV2`)

### 3.2 `instrument_types: tuple[QuestionnaireInstrumentType, ...]`

- **Python literal:** `Literal["spot", "perp", "dated_future", "option", "lending", "staking", "lp", "event_settled"]`
- **TS type:** `QuestionnaireInstrumentType`
- **Firestore path:** `/questionnaires/{id}/instrument_types`
- **Filter dimension:** advisory only (not applied on Explore tab; surfaces in reports drill-down)

### 3.3 `venue_scope: Literal["all"] | tuple[str, ...]`

- **Python type:** `Literal["all"] | tuple[str, ...]`
- **TS type:** `readonly string[] | "all"`
- **Semantics:** `"all"` sentinel = no venue restriction; tuple of venue ids = explicit allowlist
- **Validation:** venue ids resolved against UAC venue registry on admin playback
- **Firestore path:** `/questionnaires/{id}/venue_scope`
- **Filter dimension:** advisory (not applied on Explore tab)

### 3.4 `strategy_style: tuple[QuestionnaireStrategyStyle, ...]`

- **Python literal:** 8 styles — `ml_directional`, `rules_directional`, `carry`, `arbitrage`, `market_making`,
  `event_driven`, `vol_trading`, `stat_arb`
- **TS type:** `QuestionnaireStrategyStyle`
- **Firestore path:** `/questionnaires/{id}/strategy_style`
- **Filter dimension:** `families` (1:1 map to 8-family enum — see
  [mapping doc §3.2](/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md))

### 3.5 `service_family: QuestionnaireServiceFamily`

- **Python literal:** `Literal["IM", "DART", "RegUmbrella", "combo"]`
- **TS type:** `QuestionnaireServiceFamily`
- **Default:** no default — required
- **Firestore path:** `/questionnaires/{id}/service_family`
- **Filter dimension:** no; controls **which tiles are visible** via rule 12 service-family scope
  ([`/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md`](/codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md))
  - triggers the Reg-Umbrella branch of the form when value is `RegUmbrella` or `combo`.

### 3.6 `fund_structure: tuple[QuestionnaireFundStructure, ...]`

- **Python literal:** `Literal["SMA", "Pooled", "NA"]` (UI also accepts `prop` for proprietary desks — mirrored in TS)
- **TS type:** `QuestionnaireFundStructure`
- **Firestore path:** `/questionnaires/{id}/fund_structure`
- **Filter dimension:** no; contract-shape axis used by onboarding.

---

## §4 — Reg-Umbrella axes (7, optional)

All default to `None` / empty tuple. Surfaced by the UI only when `service_family ∈ {RegUmbrella, combo}`; always
readable by admin playback.

| Axis                   | Python type                          | Allowed values                                                    |
| ---------------------- | ------------------------------------ | ----------------------------------------------------------------- |
| `licence_region`       | `QuestionnaireLicenceRegion \| None` | `EU_only`, `UK_only`, `EU_or_UK`, `EU_and_UK`, `other`, or `None` |
| `targets_3mo`          | `str \| None`                        | free text                                                         |
| `targets_1yr`          | `str \| None`                        | free text                                                         |
| `targets_2yr`          | `str \| None`                        | free text                                                         |
| `own_mlro`             | `bool \| None`                       | `True` (own MLRO) / `False` (consume Odum's) / `None` (unsure)    |
| `entity_jurisdiction`  | `str \| None`                        | ISO-2 country code OR free text                                   |
| `supported_currencies` | `tuple[str, ...]`                    | tuple of ISO-4217 codes (empty tuple allowed)                     |

None of the Reg-Umbrella axes feed the catalogue filter — they surface in the admin org detail view at
`/admin/organizations/[id]` for the sales handoff (see
[`/codex/08-workflows/prospect-questionnaire-flow.md`](/codex/08-workflows/prospect-questionnaire-flow.md) §4).

---

## §5 — Strategy-preference axes (5, optional, 2026-04-24)

Landed at UAC commit `c715109` + mirrored in UI `lib/questionnaire/types.ts`. All optional; all default to `None`. Feed
`seedFiltersFromQuestionnaire()` on the Explore tab (see
[mapping doc](/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md)).

| Axis                      | Python type                                         | Allowed values                                                                            |
| ------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `market_neutral`          | `Literal["neutral", "directional", "both"] \| None` | `neutral` blocks directional families (ML_DIRECTIONAL / RULES_DIRECTIONAL / EVENT_DRIVEN) |
| `share_class_preferences` | `tuple[QuestionnaireShareClassPreference, ...]`     | subset of `["btc_neutral", "eth_neutral", "usd_only", "any"]`                             |
| `risk_profile`            | `Literal["low", "medium", "high"] \| None`          | `low` → SUPPORTED coverage only; `high` → SUPPORTED + PARTIAL                             |
| `target_sharpe_min`       | `float \| None`                                     | informational only — not a hard filter                                                    |
| `leverage_preference`     | `Literal["none", "low", "medium", "any"] \| None`   | `none` excludes `option` from instrument types; other values apply no exclusion           |

Firestore paths: `/questionnaires/{id}/{axis_name}`.

**Note on axis name:** the field is `share_class_preferences` (plural, array-typed), mirroring the multi-select UX.
Earlier plan drafts used a singular `share_class_preference`; do not rename without a cross-repo migration.

---

## §6 — Backwards compatibility

The 5 strategy-preference axes (2026-04-24) and the 7 Reg-Umbrella axes (2026-04-21) were added non-breakingly:

- **Pydantic model:** every new field has `= None` or `= ()` default. Existing Firestore documents deserialise without
  modification.
- **TypeScript interface:** every new field is optional (`?` suffix) or tuple-valued with default empty. Existing
  responses in `localStorage` under `questionnaire-response-v1` pick up the new fields as `undefined` on the next load.
- **`_apply_questionnaire_override` overlay:** reads the 6 base axes only. New axes surface in admin UI + seed the
  catalogue filter, but don't affect persona resolution or tile-lock overlay.

Adding a new axis must follow the same pattern — optional with a conservative default (`None` / `()`), never required.
See [mapping doc §6](/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md) for the full extension
protocol.

---

## §7 — Validation rules

Enforced in `QuestionnaireResponse.model_validate`:

1. All 6 base axes present on submit (empty tuple is allowed, but the field must be set).
2. Values constrained by the Literal type annotations (Pydantic rejects unknown tokens).
3. `supported_currencies` items must be 3-letter ISO-4217 codes (soft-validated; 4-letter codes like "USDT" accepted for
   crypto currency codes).
4. `entity_jurisdiction` either empty string or 2-letter ISO country code or free text (not strictly validated —
   soft-validated for admin review).

---

## §8 — Cross-references

- [`/codex/08-workflows/prospect-questionnaire-flow.md`](/codex/08-workflows/prospect-questionnaire-flow.md) — form
  surface, access-code gate, admin playback, onboarding-docs flow.
- [`/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md`](/codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md)
  — derivation rules for the Explore tab filter.
- [`/codex/08-workflows/client-onboarding.md`](/codex/08-workflows/client-onboarding.md) — 7-step client sequence in
  which the questionnaire is step 3.
- [`/codex/14-customer-journeys/demo-ops/staging-demo-setup.md`](/codex/14-customer-journeys/demo-ops/staging-demo-setup.md)
  — demo provider preseeds questionnaire payloads by persona id for email-based login.
- [`/codex/04-architecture/commercial-service-families.md`](/codex/04-architecture/commercial-service-families.md) —
  `service_family` gates tile visibility via rule 12.
