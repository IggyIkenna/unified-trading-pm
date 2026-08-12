---
doc_type: codex-ssot
title: Coding Standard — Strategy Display Conventions
summary: >-
  UI strategy-display conventions — never render raw UNDERSCORE_IDs to clients; every
  family/archetype/slot-label/venue-scope identifier pipes through the 7-function API in lib/strategy-display.ts; covers
  the 18 bespoke archetype + 8 family display names, the full-only vs both plan-tier classification, and acronym
  preservation.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [strategy, ui, terminology, defi, cefi, tradfi]
related:
  [
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/04-architecture/commercial-service-families.md,
  ]
created: 2026-04-24
authoritative_for: [strategy display conventions (client-facing strategy-identifier formatting rules)]
referenced_by:
  [
    /codex/04-architecture/commercial-service-families.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /codex/06-coding-standards/terminology-ssot.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Coding Standard — Strategy Display Conventions

> **What it is:** Canonical rules for how strategy identifiers (family, archetype, slot label, venue scope, instrument
> type, share class) render in the UI. Enforces "no raw UNDERSCORE_IDs to clients" + "acronym preservation" + "bespoke
> display names for every archetype + family". Enforced at code review; formatters live in one file.
>
> **Status:** canonical (2026-04-24) **Owner:** UI Architecture **SSOT for:**
> `unified-trading-system-ui/lib/strategy-display.ts`. **Plan:**
> [`../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
> **Companion docs:** [`strategy-identity-versioning.md`](./strategy-identity-versioning.md) (naming of the underlying
> IDs), [`/codex/09-strategy/architecture-v2/README.md`](/codex/09-strategy/architecture-v2/README.md) (the families and
> archetypes this formats — counts deliberately omitted, they were "8 families + 18 archetypes" against a live enum of 9
> and 60; read `StrategyFamily` / `StrategyArchetype`).

---

## §1 — The two rules

1. **Never render raw UNDERSCORE_IDs to clients.** Every client-visible surface (FOMO card, Reality card,
   family-archetype picker, reports page, briefing, marketing material) must pipe the identifier through the bespoke
   formatter. `CARRY_BASIS_PERP` is a code identifier; a client sees "Basis Carry — Funding Rate (Perp)".
2. **Admin exception: ID as hover / subtitle, never as primary label.** Admin surfaces (`admin-universe`,
   `admin-editor`) may render the monospace slot label (`CARRY_BASIS_PERP@binance-btc-usdt-prod`) as a
   copy-paste-friendly tooltip or greyed subtitle under the formatted primary. The primary label is still the formatted
   string.

Both rules are enforced by funnelling every ID through `lib/strategy-display.ts`. Direct template-string rendering of
raw IDs in JSX is a review-blocker.

---

## §2 — The 7-function API

SSOT: `unified-trading-system-ui/lib/strategy-display.ts`.

| Function                                                 | Input example                              | Output                                                   |
| -------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------- |
| `formatFamily(family: string): string`                   | `"ML_DIRECTIONAL"`                         | `"ML Directional"`                                       |
| `formatArchetype(archetype: string): string`             | `"CARRY_BASIS_PERP"`                       | `"Basis Carry — Funding Rate (Perp)"`                    |
| `formatSlotLabel(slotLabel: string): string`             | `"CARRY_BASIS_PERP@binance-btc-usdt-prod"` | `"Basis Carry — Funding Rate (Perp) · Binance BTC USDT"` |
| `formatVenueScope(scope: string): string`                | `"hyperliquid+binance"`                    | `"Hyperliquid + Binance"`                                |
| `formatInstrumentType(type: string): string`             | `"dated_future"`                           | `"Dated Future"`                                         |
| `formatShareClass(cls: string): string`                  | `"usdt"`                                   | `"USDT"`                                                 |
| `getArchetypePlanTier(archetype): "both" \| "full-only"` | `"ML_DIRECTIONAL_CONTINUOUS"`              | `"full-only"`                                            |

`formatSlotLabel` strips environment suffixes (`prod` / `paper` / `backtest` / `smoke`) and version suffixes (`-v2`)
before formatting. For labels without an `@`, it falls back to `formatArchetype`.

`getArchetypePlanTier` classifies an archetype into the two plan tiers — see §5 below.

---

## §3 — Bespoke archetype display names (18 archetypes)

| Archetype ID                      | Display name                            |
| --------------------------------- | --------------------------------------- |
| `ML_DIRECTIONAL_CONTINUOUS`       | ML Directional — Continuous             |
| `ML_DIRECTIONAL_EVENT_SETTLED`    | ML Directional — Event Settled          |
| `RULES_DIRECTIONAL_CONTINUOUS`    | Rules Directional — Continuous          |
| `RULES_DIRECTIONAL_EVENT_SETTLED` | Rules Directional — Event Settled       |
| `CARRY_BASIS_DATED`               | Basis Carry — Dated Futures             |
| `CARRY_BASIS_PERP`                | Basis Carry — Funding Rate (Perp)       |
| `CARRY_STAKED_BASIS`              | Staked Basis Carry                      |
| `CARRY_RECURSIVE_STAKED`          | Recursive Staked Carry                  |
| `YIELD_ROTATION_LENDING`          | Lending Yield Rotation                  |
| `YIELD_STAKING_SIMPLE`            | Simple Staking Yield                    |
| `ARBITRAGE_PRICE_DISPERSION`      | Price Dispersion Arbitrage              |
| `LIQUIDATION_CAPTURE`             | Liquidation Capture                     |
| `MARKET_MAKING_CONTINUOUS`        | Market Making — Continuous              |
| `MARKET_MAKING_EVENT_SETTLED`     | Market Making — Event Settled           |
| `EVENT_DRIVEN`                    | Event Driven                            |
| `VOL_TRADING_OPTIONS`             | Volatility Trading — Options            |
| `STAT_ARB_PAIRS_FIXED`            | Statistical Arbitrage — Fixed Pairs     |
| `STAT_ARB_CROSS_SECTIONAL`        | Statistical Arbitrage — Cross-Sectional |

Names reviewed + locked with Ikenna 2026-04-24. Updating requires a new review + this table updated alongside
`ARCHETYPE_DISPLAY_NAMES` in source.

---

## §4 — Bespoke family display names

> **`PORTFOLIO` was missing from this table until 2026-08-12.** The heading said "(8 families)" and the table had eight
> rows, so the stale count concealed a genuinely absent row — the family added 2026-04-25 in Phase 9 had **no
> display-name convention at all**, meaning any UI or report formatting a `PORTFOLIO` strategy had nothing defined to
> render. The name `Portfolio` was not invented here: it is already the de-facto rendering in
> [`strategy-summary.md`](/codex/09-strategy/strategy-summary.md) and
> [`architecture-v2/README.md`](/codex/09-strategy/architecture-v2/README.md). **Count removed rather than corrected** —
> one row per `StrategyFamily` member is the rule; read the enum.

| Family ID              | Display name          |
| ---------------------- | --------------------- |
| `ML_DIRECTIONAL`       | ML Directional        |
| `RULES_DIRECTIONAL`    | Rules Directional     |
| `CARRY_AND_YIELD`      | Carry & Yield         |
| `ARBITRAGE_STRUCTURAL` | Structural Arbitrage  |
| `MARKET_MAKING`        | Market Making         |
| `EVENT_DRIVEN`         | Event Driven          |
| `VOL_TRADING`          | Volatility Trading    |
| `STAT_ARB_PAIRS`       | Statistical Arbitrage |
| `PORTFOLIO`            | Portfolio             |

---

## §5 — Plan-tier classification

`ARCHETYPE_PLAN_TIER` classifies each archetype into `"full-only"` (requires `strategy-full` + `ml-full` entitlements,
because of dependency on the ML training pipeline or event-model authoring workflow) or `"both"` (available on
Signals-In and Full).

**Full-only (4 archetypes):**

- `ML_DIRECTIONAL_CONTINUOUS`
- `ML_DIRECTIONAL_EVENT_SETTLED`
- `EVENT_DRIVEN`
- `VOL_TRADING_OPTIONS`

**Both tiers (14 archetypes):** everything else. `getArchetypePlanTier` returns `"both"` for any unknown archetype —
this is a conservative default so new archetypes default to "visible to both tiers" until the table is explicitly
updated.

Consumers of this classification:

- `<FomoTearsheetCard>` — emerald "Full + Signals-In" vs amber "DART Full only" tier badge.
- `<StrategyCatalogueSurface>` — Signals-In upgrade banner ("N/M strategies available").
- `/briefings/dart-signals-in` — `DartTierComparisonTable` feature matrix.

SSOT for the wider DART Full vs Signals-In feature matrix:
[`/codex/04-architecture/commercial-service-families.md`](/codex/04-architecture/commercial-service-families.md).

---

## §6 — Acronym preservation

Title-casing a tokenised string naively produces "Btc" / "Usdt" / "Defi". The formatters preserve known acronyms via an
explicit set. The canonical list (keep in sync with the `ACRONYMS` set in source):

```
ML  BTC  ETH  SOL  USD  USDT  USDC  GBP  EUR
DeFi  CeFi  TradFi
LP  IV  DEX  CEX  OKX  ERC20  AAVE  IBKR
CME  CBOE  ICE  SPY  ES  NQ
```

Three entries are **mixed-case** acronyms rather than all-caps: `DeFi`, `CeFi`, `TradFi`. The mixed-case set overrides
the upper-case match so that `defi` tokenises to `DeFi`, not `DEFI`.

Add new acronyms to `ACRONYMS` (all-caps) or `MIXED_CASE_ACRONYMS` (case-preserving) in `lib/strategy-display.ts`. Do
not inline-lookup acronyms at call sites — formatter is the only owner.

---

## §7 — Where formatters are applied

Every client-visible strategy identifier must pipe through these functions. Current call sites:

- `components/strategy-catalogue/FomoTearsheetCard.tsx` — `formatFamily`, `formatArchetype`, `formatSlotLabel` on card
  header; `getArchetypePlanTier` for tier badge.
- `components/strategy-catalogue/RealityPositionCard.tsx` — same formatters for subscribed-strategy cards.
- `components/strategy-catalogue/family-archetype-picker.tsx` — archetype dropdown shows `formatArchetype` as the
  primary label; strategy-ID dropdown shows `formatSlotLabel` with the raw slot as a `title` hover for copy-paste.
- `app/(public)/briefings/[slug]/page.tsx` — DART tier comparison table + archetype lists.

Admin surfaces (`admin-universe`, `admin-editor`) render formatted primary + raw monospace subtitle — the subtitle is
the admin-exception carve-out from §1 rule 1.

---

## §8 — Non-goals

- **Not i18n.** These formatters produce English-only display names. Localisation is a separate concern — if we ever
  need it, the formatter contract changes (pass in a locale) but the SSOT location doesn't.
- **Not a source of truth for the archetypes themselves.** The 18-archetype enum lives in UAC
  (`unified_api_contracts/internal/domain/strategy_service/`). This doc only governs _how_ they render; what they are
  lives in [`strategy-identity-versioning.md`](./strategy-identity-versioning.md) + the architecture-v2 README.
