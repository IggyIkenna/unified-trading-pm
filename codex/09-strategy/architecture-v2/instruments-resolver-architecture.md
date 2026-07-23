---
doc_type: codex-ssot
title: Strategy → Instruments Resolver Architecture
summary:
  SSOT for joining the strategy catalogue (capability declaration) to instruments-service concrete records — stub vs
  real (--with-real-instruments) resolver modes, the catalogue-venue→parquet-venue mapping, per-slot instrument
  resolution, and universal persona instrument hydration via assigned_strategies.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [strategy, instruments, catalogue, uac, ui, single-walk]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    ../../02-data/questionnaire-axes.md,
    ../../05-infrastructure/bucket-isolation-model.md,
  ]
created: 2026-04-25
authoritative_for: [strategy-catalogue to instruments-service resolver join]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Strategy → Instruments Resolver Architecture

> **Status:** canonical (2026-04-25) **Owner:** UAC + UI Architecture **SSOT for:**
> `unified-api-contracts/scripts/enumerate_strategy_instruments.py`,
> `unified-api-contracts/scripts/enumerate_envelope.py`, `unified-api-contracts/scripts/enumerate_availability.py`,
> `unified-trading-system-ui/lib/architecture-v2/envelope-loader.ts`.

The strategy catalogue is a _capability declaration_: archetype × category × `instrument_type` × venue. The
instruments-service writes \_concrete records\* of what's actually tradable today: per-(category, day, venue) parquet
rolls. This doc describes how the two are joined and surfaced to UI / terminal / admin consumers.

---

## §1 — Source artefacts

### 1.1 Catalogue envelope (UAC-side, generated)

`scripts/enumerate_envelope.py` outputs the full combinatoric envelope.

| Artefact         | Path on GCS                                                               | Format                                   |
| ---------------- | ------------------------------------------------------------------------- | ---------------------------------------- |
| Markdown summary | `gs://strategy-store-cefi-central-element-323112/catalogue/envelope.md`   | grouped by category → family → archetype |
| Structured JSON  | `gs://strategy-store-cefi-central-element-323112/catalogue/envelope.json` | `EnvelopeJson` schema (see §3)           |

Run: `python scripts/enumerate_envelope.py --upload`

### 1.2 Availability rules (UAC-side, generated)

`scripts/enumerate_availability.py` outputs per-archetype access rules.

| Artefact          | Path on GCS                                                                   | Format                    |
| ----------------- | ----------------------------------------------------------------------------- | ------------------------- |
| Availability JSON | `gs://strategy-store-cefi-central-element-323112/catalogue/availability.json` | `AvailabilityJson` schema |

Contains: `allowed_categories`, `bespoke_capable`, `tenor_buckets`, `venue_combo_policy`, `forbidden_combinations` (the
negative space).

### 1.3 Instrument records (instruments-service, daily writes)

instruments-service writes per-day per-venue parquet rolls.

| Bucket                                                | Path                                                                               |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `instruments-store-cefi-central-element-323112`       | `instrument_availability/by_date/day=YYYY-MM-DD/venue={VENUE}/instruments.parquet` |
| `instruments-store-defi-central-element-323112`       | same shape                                                                         |
| `instruments-store-sports-central-element-323112`     | same shape                                                                         |
| `instruments-store-prediction-central-element-323112` | same shape                                                                         |
| (no TRADFI bucket today)                              | future: `instruments-store-tradfi-...`                                             |

Schema (`InstrumentDefinition` in `unified_api_contracts/internal/reference/instrument_definition.py`):

| Column                                              | Type           | Note                                                                         |
| --------------------------------------------------- | -------------- | ---------------------------------------------------------------------------- |
| `instrument_key`                                    | string         | canonical id, e.g. `BINANCE-FUTURES:PERP:BTCUSDT`                            |
| `venue`                                             | string         | uppercase parquet venue token                                                |
| `instrument_type`                                   | string         | `PERPETUAL` / `SPOT_PAIR` / `OPTION` / `LENDING` / `STAKING` / `POOL` / etc. |
| `raw_symbol`                                        | string         | venue-native symbol                                                          |
| `base_asset` / `quote_asset` / `settle_asset`       | string         |                                                                              |
| `status`                                            | string         | `active` / `delisted` / etc.                                                 |
| `tick_size` / `min_size` / `contract_size`          | decimal        |                                                                              |
| `expiry` / `strike` / `option_type` / `underlying`  | optional       | for options + dated futures                                                  |
| `available_from_datetime` / `available_to_datetime` | timestamp[UTC] | listing window                                                               |

Categories (lowercase: `cefi` / `defi` / `tradfi` / `sports`) — **not** the same as the catalogue's primary categories
(uppercase: `CEFI` / `DEFI` / `TRADFI` / `SPORTS` / `PREDICTION` / `CROSS_CATEGORY`). Mapping in
`enumerate_strategy_instruments.py::_CATEGORY_TO_INSTRUMENT_BUCKET`.

### 1.4 Resolver output (UAC-side, joined)

`scripts/enumerate_strategy_instruments.py` performs the join.

| Artefact                   | Path on GCS                                                                           | Format                           |
| -------------------------- | ------------------------------------------------------------------------------------- | -------------------------------- |
| Strategy → instruments map | `gs://strategy-store-cefi-central-element-323112/catalogue/strategy_instruments.json` | `StrategyInstrumentsJson` schema |

Two resolver modes:

- **stub**: emits venue tokens as instrument proxies. Fast, credential-free, ~600 KB output. Default mode for CI.
- **real (`--with-real-instruments`)**: walks each `instruments-store-*` bucket once via `fs.find()`, builds a
  `parquet_venue → latest_day_path` index, then per-slot reads parquet and filters by `instrument_type`. ~17 MB output.
  Cached per (category, parquet_venue) pair. Run takes ~1–2 min.

---

## §2 — Join logic

For each `(archetype, category, instrument_type, venue)` slot in the envelope, the resolver:

1. **Maps catalogue venue → parquet venue.** Catalogue uses lowercase tokens (`binance`, `okx`, `uniswap_v3@ethereum`);
   parquet uses uppercase with variant suffixes (`BINANCE-SPOT`, `BINANCE-FUTURES`, `UNISWAP_V3-ETH`).
   `_CATALOGUE_VENUE_TO_PARQUET` is the SSOT map.
2. **Resolves category bucket.** `_CATEGORY_TO_INSTRUMENT_BUCKET` — uppercase catalogue category → GCS bucket name.
3. **Picks latest parquet.** Bucket-level `fs.find()` returns all parquet paths; deepest `day=YYYY-MM-DD` per venue
   wins.
4. **Filters by instrument_type.** Catalogue → parquet vocabulary mapping in `_INSTRUMENT_TYPE_TO_PARQUET`
   (`perp ↔ {PERPETUAL, PERP}`, `spot ↔ {SPOT_PAIR, SPOT, SPOT_ASSET}`, etc.).
5. **Filters by status = active.**
6. **Collects unique `instrument_key` values.**

---

## §3 — Consumer schemas

UI consumers go through `lib/architecture-v2/envelope-loader.ts`, which fetches from
`/api/catalogue/envelope?file=<file>` (server-side GCS proxy with ADC).

```ts
loadEnvelope(): Promise<EnvelopeJson>
loadStrategyInstruments(): Promise<StrategyInstrumentsJson>
loadAvailability(): Promise<AvailabilityJson>

instrumentsForSlot(slotKey): Promise<string[]>
slotsForArchetype(archetype): Promise<StrategyInstrumentsSlot[]>
slotsForCategory(category): Promise<StrategyInstrumentsSlot[]>
archetypesAllowedInCategory(category): Promise<string[]>
isBespokeCapable(archetype): Promise<boolean>
tenorsForArchetype(archetype): Promise<string[] | null>
```

Cached in-memory per page load. The `/api/catalogue/envelope` route adds a 5-minute `cache-control` header.

### 3.1 Universal persona hydration (2026-04-25)

Demo personas (and, in production, real users provisioned with `AdminStrategyAssignment` records) carry an
`assigned_strategies: readonly string[]` field — the closed list of catalogue slot labels routed to the org. At login,
`DemoAuthProvider.personaToAuthUser()` (in `lib/auth/demo-provider.ts`) calls a single helper:

```ts
derivePersonaInstruments(persona): Promise<readonly string[]>
```

This helper fans out over `persona.assigned_strategies`, calls `instrumentsForSlot(slot)` for each, deduplicates, and
returns the union. The result lands on `AuthUser.instruments` — the **single source of truth** for "which instruments
can this user trade". Same code path runs at login AND at session restore so a catalogue regen between visits propagates
without stale localStorage.

**Design rule:** any new demo persona is a single append to `lib/auth/personas.ts` with an `assigned_strategies` array.
**Never** add a hardcoded mock instrument list per persona — the universal hydration covers it. Empty
`assigned_strategies` → empty `instruments` array; consumers fall through to entitlement-level gating.

**Layered with `useStrategyScopedInstruments(slotKey, baseList)`:** the per-slot hook (in
`lib/architecture-v2/use-strategy-scoped-instruments.ts`) narrows a base list to ONE slot's allowed instruments at the
component level (e.g. when the user picks a strategy in `<ManualTradingPanel>`). `user.instruments` is the ALL-slots
union for surfaces that show the prospect's full tradeable universe (e.g. portfolio overview, watchlists). Both read
from the same `instrumentsForSlot()` SSOT — no drift.

---

## §4 — Refresh cadence

| Layer                                    | Cadence         | Mechanism                                       |
| ---------------------------------------- | --------------- | ----------------------------------------------- |
| Catalogue envelope (md + json)           | On code change  | `enumerate_envelope.py --upload` (manual or CI) |
| Availability JSON                        | On code change  | `enumerate_availability.py --upload`            |
| Strategy → instruments (real)            | Daily (planned) | Cloud Scheduler nightly cron (Phase 10 N2 todo) |
| Instrument parquet (instruments-service) | Daily           | instruments-service backfill / forward-poll VMs |

Local dev refresh: `bash unified-trading-pm/scripts/dev/regen-catalogue.sh`
([`../../scripts/dev/regen-catalogue.sh`](../../scripts/dev/regen-catalogue.sh)).

---

## §5 — Adding a new venue / archetype

1. Add the venue to `enumerate_envelope.py::_category_venues()` for the relevant `(category, instrument_type)`.
2. If the venue is in instruments-service: add an entry to `_CATALOGUE_VENUE_TO_PARQUET` mapping the catalogue token to
   the parquet venue variants.
3. Run `bash unified-trading-pm/scripts/dev/regen-catalogue.sh` to refresh GCS.
4. UI picks up the new venue automatically on next load (5-min cache).

For new archetypes: same pattern, plus add to `_BESPOKE_CAPABLE` if bespoke, `_TENOR_BUCKETS_BY_ARCHETYPE` if a VOL
archetype, and `_ARCHETYPE_ALLOWED_CATEGORIES` to express category restrictions.

---

## §6 — Known limitations

- **TRADFI**: no `instruments-store-tradfi-*` bucket today. The resolver falls back to venue tokens for TRADFI slots.
  UAC universe registry (`tradfi_instrument_universe.py`) is the eventual source of truth — needs a bridge to GCS
  parquet.
- **CROSS_CATEGORY**: portfolio archetypes have no per-venue instrument mapping (sleeves are themselves strategies).
  Resolver returns the canonical sleeve labels.
- **MEV venue mapping**: MEV archetypes use venue tokens that don't necessarily appear in instruments-service parquet
  (MEV operates on pending-mempool transactions, not listed instruments).

---

## §7 — Cross-references

- DART UI plan addendum:
  [`../../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
- Catalogue 3-tier model: [`./strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md)
- Questionnaire axes: [`../../02-data/questionnaire-axes.md`](../../02-data/questionnaire-axes.md)
- Bucket isolation model:
  [`../../05-infrastructure/bucket-isolation-model.md`](../../05-infrastructure/bucket-isolation-model.md)
