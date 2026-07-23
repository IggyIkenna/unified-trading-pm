---
doc_type: codex-ssot
title: DART Terminal vs. DART Research — Tile Split + Instrument-Type View Gating (SSOT)
summary:
  DART splits into two dashboard tiles — DART Terminal (execution-basic/full) and DART Research (strategy-full AND
  ml-full, padlocked for Signals-In); defines instrument-type view gating (reality vs FOMO derivation from
  strategy_instruments.json), TERMINAL_TABS/RESEARCH_TABS sub-route ownership, and the persona test matrix.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [dart, ui, entitlements, personas, instrument-type-gating, view-gating, research]
related:
  [
    /codex/14-customer-journeys/dart/mode-toggle.md,
    ../demo-ops/staging-demo-setup.md,
    ../demo-ops/demo-restriction-profiles.md,
  ]
created: 2026-04-28
authoritative_for: [DART Terminal vs DART Research tile split, DART instrument-type view gating]
referenced_by:
  [/codex/14-customer-journeys/dart/mode-toggle.md, /codex/14-customer-journeys/demo-ops/staging-demo-setup.md]
owner:
last_reviewed:
code_refs:
  [
    unified-trading-system-ui/lib/config/services.ts,
    unified-trading-system-ui/lib/auth/personas.ts,
    unified-trading-system-ui/lib/architecture-v2/user-instrument-types.ts,
    unified-trading-system-ui/components/shell/service-tabs.tsx,
    unified-trading-system-ui/components/platform/page-entitlement-gate.tsx,
  ]
---

# DART Terminal vs. DART Research — Tile Split + Instrument-Type View Gating (SSOT)

**Status:** Active (2026-04-28) **Implementation plan:**
[`plans/ai/dart_terminal_research_split_2026_04_28.plan.md`](../../../plans/ai/dart_terminal_research_split_2026_04_28.plan.md)
**Repo:** `unified-trading-system-ui` **Branch:** `live-defi-rollout`

## Why this exists

DART used to render as **one dashboard tile** with chip-level navigation (Terminal, Research, Promote, Observe, Strategy
Catalogue, Signal Intake, Data). Research and Promote chips were padlocked-visible for Signals-In users with an upgrade
CTA. Three problems compounded:

1. **Brand confusion.** Signals-In users saw seven chips with two greyed out instead of seeing two distinct products.
   The customer-facing framing was always "DART Terminal" + "DART Research" as separate offerings.
2. **No instrument-type view gating.** Trading sub-routes (`/services/trading/{options,sports,defi,predictions}`) showed
   to anyone with `trading-common` tier, regardless of whether the user's entitled strategies actually used those
   instrument types. A carry-only client saw the Sports tab.
3. **Hidden research surfaces.** `/services/research/signals` exists on disk but is not in any nav export — orphaned.

This SSOT codifies the two-tile split, the instrument-type derivation chain, and the persona matrix for testing.

## Two tiles

| Tile              | id              | Required entitlements                 | Signals-In                               | DART Full | Admin   |
| ----------------- | --------------- | ------------------------------------- | ---------------------------------------- | --------- | ------- |
| **DART Terminal** | `dart-terminal` | `execution-basic` OR `execution-full` | visible                                  | visible   | visible |
| **DART Research** | `dart-research` | `strategy-full` AND `ml-full`         | padlocked-visible (feature-preview card) | visible   | visible |

Padlocked DART Research tile renders a feature-preview card showing 3 sample research surfaces with locks + "Upgrade to
DART Full" CTA. **No internal links exposed** — clicking the tile shows the upgrade CTA, not a nav drill-down.

## Sub-route ownership

### DART Terminal (TERMINAL_TABS)

Trading-day surfaces — visible to Signals-In + DART-Full + admin.

| Chip                | Route                                                                                                        | Notes                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| Terminal            | `/services/trading/terminal`                                                                                 | live trading orders, positions, P&L            |
| Observe             | `/services/observe/risk`                                                                                     | risk + alerts + circuit breakers               |
| Strategy Catalogue  | `/services/strategy-catalogue`                                                                               | read-only for Signals-In, manage for DART-Full |
| Signal Intake       | `/services/signals/dashboard`                                                                                | Signals-In webhooks                            |
| Trading sub-domains | `/services/trading/{options,sports,defi,predictions,markets,book,orders,pnl,positions,risk,alerts,accounts}` | instrument-type gated (see below)              |

### DART Research (RESEARCH_TABS) — DART-Full + admin only

Organised by lifecycle stage. Strategy lists within each stage use **family → archetype → asset_group** hierarchy
(research lens; quants think family-first).

| Stage                   | Routes                                                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Overview**            | `/services/research/overview`                                                                                                                     |
| **Develop**             | `/services/research/features`, `/services/research/feature-etl`, `/services/research/quant`, `/services/research/strategies`                      |
| **Train**               | `/services/research/ml/{training,analysis,registry,grid-config,monitoring,governance,config}`                                                     |
| **Validate**            | `/services/research/strategy/{backtests,compare,results,heatmap}`, `/services/research/signals` (orphan surfaced), `/services/research/execution` |
| **Allocate (Research)** | `/services/research/allocate` (NEW — restored from `dfc8c5ba^`, distinct from operational `/services/investment-management/allocator`)            |
| **Promote**             | `/services/research/strategy/{candidates,handoff}`                                                                                                |

### Public catalogue (unchanged)

`/services/strategy-catalogue` remains **asset_group → family → archetype → instance** (per
`feedback_primary_category_first_class_axis.md` — that ordering drove 3.3× envelope uplift). Research-side family-led
hierarchy is a different lens for a different audience; do not unify.

## Instrument-type view gating

### Derivation chain

```
user.assigned_strategies   (slot labels, e.g. "ML_DIRECTIONAL_CONTINUOUS@CEFI-BTC-1h")
   │
   ▼
strategy_instruments.json  (GCS proxy at /api/catalogue/envelope?file=strategy_instruments.json)
   │
   ▼
StrategyInstrumentsSlot[]  { archetype_id, category, instrument_type, venue, instruments[] }
   │
   ▼
{ instrumentTypes: Set<string>, assetGroups: Set<StrategyCategory> }
```

**Implementation:** `lib/architecture-v2/user-instrument-types.ts` (new) exports:

```ts
export type DerivationMode = "reality" | "fomo";

export async function instrumentTypesForUser(
  user: AuthPersona,
  mode: DerivationMode = "reality"
): Promise<{ instrumentTypes: Set<string>; assetGroups: Set<StrategyCategory> }>;
```

- **Admin** (`entitlements.includes("*")`): early bypass — returns ALL instrument types + ALL asset groups.
- **Reality mode**: filter `strategy_instruments.json` slots by `user.assigned_strategies`, collect distinct
  `instrument_type` + `category`.
- **FOMO mode**: reality + teaser-strategy slots (deterministic-stable subset from Strategy Catalogue Explore tab).

### Gate consumer

`PageEntitlementGate` (extended in `components/platform/page-entitlement-gate.tsx`) accepts:

```ts
requiredInstrumentTypes?: string[];
requiredAssetGroups?: StrategyCategory[];
```

If user lacks ALL required instrument types/asset groups → render frosted-glass FOMO overlay + upsell CTA. Admin bypass
via existing `isAdmin()` check.

### Mode selection per route

| Route                                                                       | Mode                        | Reason                                                                  |
| --------------------------------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------- |
| Trading sub-domains (`/services/trading/{options,sports,defi,predictions}`) | `"fomo"`                    | Signals-In + Explore-tab teaser strategies expand views to drive upsell |
| DART Research tile + sub-routes                                             | tile-level entitlement only | Research is a tier gate, not instrument-type gate                       |
| Strategy Catalogue Explore tab                                              | already implemented         | Reality vs Explore — Explore = teaser source                            |

## Persona matrix (test scope)

Drawn from `lib/auth/personas.ts` + `lib/auth/tier-override.ts`. Bold = primary test personas for tier-override flip.

| Persona id                                                      | Email                                      | Tier                          | DART Terminal         | DART Research           | Notes                                      |
| --------------------------------------------------------------- | ------------------------------------------ | ----------------------------- | --------------------- | ----------------------- | ------------------------------------------ |
| `admin`                                                         | admin@odum.internal                        | `["*"]`                       | visible               | visible                 | sees everything                            |
| `internal-trader`                                               | trader@odum.internal                       | `["*"]`                       | visible               | visible                 |                                            |
| `im-desk-operator`                                              | desk@odum.internal                         | `["*"]`                       | visible               | visible                 |                                            |
| `admin-odum`                                                    | admin@odum-research.co.uk                  | `["*"]`                       | visible               | visible                 |                                            |
| **`desmond-dart-full`**                                         | **desmondhw@gmail.com**                    | DART Full                     | visible               | visible                 | tier-override target — flips to Signals-In |
| **`desmond-dart-full` + tier-override → Signals-In**            | desmondhw@gmail.com                        | Signals-In                    | visible               | padlocked               | identity unchanged, only entitlements      |
| **`elysium-defi-full`**                                         | **patrick@bankelysium.com**                | DeFi Full                     | DeFi views only       | visible (DeFi research) | tier-override target                       |
| **`elysium-defi`**                                              | patrick@bankelysium.com                    | DeFi Base                     | DeFi views only       | padlocked               |                                            |
| `client-full`                                                   | pm@alphacapital.com                        | DART Full multi-asset         | all 5 asset_groups    | visible                 | reference DART-Full client                 |
| `client-premium`                                                | cio@vertex.com                             | Premium (no ml/strategy-full) | basic trading domains | padlocked               |                                            |
| `client-data-only`                                              | analyst@betafund.com                       | data-basic                    | locked tile           | padlocked               |                                            |
| `prospect-dart-full`                                            | prospect-dart-full@odum-research.com       | DART Full                     | visible               | visible                 |                                            |
| `prospect-dart-signals-in`                                      | prospect-dart-signals-in@odum-research.com | Signals-In                    | visible               | padlocked               |                                            |
| `prospect-dart` (sarah.quant)                                   | sarah.quant@examplehedge.com               | DART Full                     | visible               | visible                 |                                            |
| `demo-signals-client`                                           | demo-signals@odum-research.co.uk           | Signals-In basic              | visible               | padlocked               |                                            |
| `client-regulatory`                                             | fm@emergingmgr.com                         | reporting only                | hidden                | hidden                  | reg-only — no DART tiles                   |
| `prospect-im` / `prospect-odum-signals` / `prospect-regulatory` | various                                    | non-DART                      | hidden                | hidden                  |                                            |
| `investor` / `advisor`                                          | investor@odum-research.co.uk               | full demo                     | visible               | visible                 |                                            |

## FOMO behavior (no third tier)

FOMO is **not a separate tier**. It is the gating mode used by trading-route gates: every Signals-In user has FOMO
behavior automatically — teaser strategies from the Strategy Catalogue Explore tab expand the user's effective
`instrumentTypesForUser()` set. The tier-override toggle stays a 2-state DART-Full ↔ Signals-In flip. Admins always
bypass.

## Source-of-truth files

| File                                                                      | Role                                                   |
| ------------------------------------------------------------------------- | ------------------------------------------------------ |
| `unified-trading-system-ui/lib/config/services.ts`                        | DashboardTileId enum + SERVICE_REGISTRY                |
| `unified-trading-system-ui/lib/auth/personas.ts`                          | PERSONAS list (entitlements per persona)               |
| `unified-trading-system-ui/lib/auth/persona-dashboard-shape.ts`           | PERSONA_TILE_SHAPES + PERSONA_SUBROUTE_SHAPES          |
| `unified-trading-system-ui/lib/auth/tier-override.ts`                     | TIER_BUNDLES (Desmond + Patrick)                       |
| `unified-trading-system-ui/lib/architecture-v2/envelope-loader.ts`        | strategy_instruments.json schema + slotsForArchetype   |
| `unified-trading-system-ui/lib/architecture-v2/user-instrument-types.ts`  | (NEW) instrumentTypesForUser + teaserStrategiesForUser |
| `unified-trading-system-ui/components/platform/page-entitlement-gate.tsx` | gate component (extended with requiredInstrumentTypes) |
| `unified-trading-system-ui/components/shell/service-tabs.tsx`             | TERMINAL_TABS + RESEARCH_TABS exports                  |
| `unified-trading-system-ui/app/(platform)/dashboard/page.tsx`             | two-tile renderer                                      |

## Cross-references

- Catalogue UX SSOT (asset_group → family → archetype): see `MEMORY.md` index entry
  `feedback_primary_category_first_class_axis.md`
- Tier-override design: `/codex/14-customer-journeys/demo-ops/staging-demo-setup.md`
- Catalogue artefacts SSOT: `feedback_catalogue_gcs_artefacts.md`
- Allocator G2.10 split: commit `dfc8c5ba` (operational allocator moved to `/services/investment-management/`);
  research-side allocator is a separate workbench restored under `/services/research/allocate`
