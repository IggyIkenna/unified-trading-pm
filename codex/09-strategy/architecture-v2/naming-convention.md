---
doc_type: codex-ssot
title: Canonical Strategy-ID Naming Convention (v2)
summary:
  Canonical strategy-ID naming SSOT — three interlocking forms (slot label
  ARCHETYPE@venue-asset-instrument-period-quote-env, fully-qualified FAMILY.ARCHETYPE.slot_id, bare slot id), the
  parse_strategy_id/format_strategy_id contract, and where each form is used across registry, records, URLs, and
  manifests.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, canonicalisation, uac, refactor, catalogue]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    README.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
  ]
created: 2026-04-21
authoritative_for: [canonical strategy-id naming grammar (slot-label / fully-qualified / bare-slot)]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/templates/strategy-description-template.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/value-betting-archetype-decision.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Canonical Strategy-ID Naming Convention (v2)

**SSOT for:** how a strategy is named across the platform — slot labels, fully-qualified ids, bare slot ids, URL paths,
registry keys, record stamps.

**Owning UAC module:** `unified_api_contracts/internal/architecture_v2/strategy_naming.py` (re-exported from the
`unified_api_contracts.strategy` facade as `parse_strategy_id` / `format_strategy_id` / `ParsedStrategyId`).

**Companion codex:**

- `strategy-registry-v2.md` — how the registry derives entries from the archetype capability matrix.
- `../architecture-v2/README.md` — v2 axes / families / archetypes overview.
- `../../06-coding-standards/README.md` — general coding standards.

---

## 1. Three identifier forms

The v2 architecture uses three interlocking identifiers:

| Form            | Grammar                                             | Example                                                           | Audience                                                                        |
| --------------- | --------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Slot label      | `ARCHETYPE@venue-asset-instrument-period-quote-env` | `CARRY_BASIS_PERP@binance-eth-perp-10m-usdt-prod`                 | Registry, records pipeline, strategy-service internals, availability manifests. |
| Fully-qualified | `FAMILY.ARCHETYPE.slot_id`                          | `CARRY_AND_YIELD.CARRY_BASIS_PERP.binance-eth-perp-10m-usdt-prod` | UI URLs, admin surfaces, codex cross-references, external docs.                 |
| Bare slot id    | `venue-asset-instrument-period-quote-env`           | `binance-eth-perp-10m-usdt-prod`                                  | Contexts where the archetype + family are already known (e.g. nested UI tabs).  |

The **family** is never stored inside the slot label — it is always derivable from the archetype via
`ARCHETYPE_TO_FAMILY` (in `enums.py`). The fully-qualified form duplicates the family purely for audit clarity.

---

## 2. Family axis (9 values)

```
ML_DIRECTIONAL
RULES_DIRECTIONAL
CARRY_AND_YIELD
ARBITRAGE_STRUCTURAL
MARKET_MAKING
EVENT_DRIVEN
VOL_TRADING
STAT_ARB_PAIRS
PORTFOLIO
```

SSOT: `unified_api_contracts.internal.architecture_v2.enums.StrategyFamily`. (`PORTFOLIO` added 2026-04-25 in Phase 9
for cross-category sleeves.)

## 3. Archetype axis (57 values)

The slot-label grammar is identical for every archetype; this section is the naming contract, not the catalogue. The
57-value enumeration grouped by family lives in [`README.md` § "57 Archetypes"](README.md) and the canonical SSOT is
`unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype`. The original 2026-04-17 baseline had 18; the
Phase 9 expansion (2026-04-25) and the 2026-05-18 taxonomy decision brought it to 57.

The archetype → family relation is declared in `ARCHETYPE_TO_FAMILY` (same module) — **never** hardcode the family;
always look it up. Archetype IDs carry no category prefix (no `CEFI_` / `DEFI_` / `SPORTS_` / `TRADFI_`).

## 4. Slot-id grammar

A slot id is a hyphen-separated 6-tuple that identifies a unique run configuration:

```
{venue}-{asset}-{instrument_type}-{period}-{quote_ccy}-{env}
```

Conventions:

- **Lower-case, hyphen-separated** — matches DNS / URL conventions.
- **No `@` anywhere inside the slot id** — the `@` is reserved as the slot-label separator.
- **Dots (`.`) are allowed** only in non-first positions, but must not appear before any `@` if the slot id is later
  wrapped into a slot-label form. The fully-qualified parser splits on the first two dots only; everything after the
  second dot is the slot id.
- **Env** should be `prod` / `staging` / `dev` / `demo` — environments for the same underlying run are tagged here.

## 5. Parser contract (`parse_strategy_id`)

```python
from unified_api_contracts.strategy import parse_strategy_id

# Slot-label form — family inferred from archetype
parsed = parse_strategy_id("CARRY_BASIS_PERP@binance-eth-perp-10m-usdt-prod")
# parsed.family == StrategyFamily.CARRY_AND_YIELD
# parsed.archetype == StrategyArchetype.CARRY_BASIS_PERP
# parsed.slot_id == "binance-eth-perp-10m-usdt-prod"
# parsed.source_form == "slot_label"

# Fully-qualified form — family explicit + cross-checked against archetype
parsed = parse_strategy_id(
    "CARRY_AND_YIELD.CARRY_BASIS_PERP.binance-eth-perp-10m-usdt-prod"
)
# parsed.source_form == "fully_qualified"
```

Raises `ValueError` on:

- Empty input
- No separator (neither `@` nor `.`)
- Unknown archetype or family token
- FQ form with family segment that doesn't match the archetype's declared family (e.g.
  `ML_DIRECTIONAL.CARRY_BASIS_PERP.slot-x` — `CARRY_BASIS_PERP` belongs to `CARRY_AND_YIELD`, not `ML_DIRECTIONAL`)
- Empty segments (`.A.`, `@`, etc.)

## 6. Formatter contract (`format_strategy_id`)

```python
from unified_api_contracts.strategy import (
    StrategyArchetype,
    format_strategy_id,
)

# Default: fully-qualified (for URLs / admin surfaces / docs)
format_strategy_id(
    StrategyArchetype.CARRY_BASIS_PERP,
    "binance-eth-perp-10m-usdt-prod",
)
# → "CARRY_AND_YIELD.CARRY_BASIS_PERP.binance-eth-perp-10m-usdt-prod"

# Slot-label form (for registry / records / manifests)
format_strategy_id(
    StrategyArchetype.CARRY_BASIS_PERP,
    "binance-eth-perp-10m-usdt-prod",
    fully_qualified=False,
)
# → "CARRY_BASIS_PERP@binance-eth-perp-10m-usdt-prod"
```

## 7. Where each form is used

| Surface                                                      | Form            | Rationale                                                                  |
| ------------------------------------------------------------ | --------------- | -------------------------------------------------------------------------- |
| `StrategyDefinition.strategy_id` (UAC registry)              | Slot label      | Historical — registry was seeded from the slot grammar; unchanged in v2.   |
| Record enricher `strategy_name` stamps                       | Slot label      | Matches registry id — records join against registry by exact id match.     |
| UI route `/services/strategy-catalogue/strategies/[id]`      | Fully-qualified | Family prefix is load-bearing — human readers see lineage in the URL.      |
| Admin strategy detail view                                   | Fully-qualified | Admin audit logs surface family + archetype explicitly.                    |
| Signal broadcast envelopes (`StrategySignalEmittedExternal`) | Fully-qualified | External counterparties benefit from family-level disambiguation.          |
| Availability manifest `strategy_id` column                   | Slot label      | Consistent with records pipeline; FQ derivation is one function call away. |

## 8. Testing

- Unit tests live in `tests/internal/unit/test_strategy_naming.py`.
- Every new archetype added to `enums.StrategyArchetype` MUST round-trip both slot-label and FQ forms via
  `format_strategy_id` + `parse_strategy_id` (`test_parse_slot_label_all_archetypes_roundtrip_via_format` +
  `test_parse_fq_all_archetypes_roundtrip_via_format` cover this automatically).
- Mismatch + malformed inputs: explicit negative tests in the same file.

## 9. Migration notes

- v1 lowercase family slugs (`basis-trade`, `mean-reversion`, `sports-arb`, `prediction-ml`) are **not** part of this
  convention and must not appear as route slugs / filter values / display labels. See
  `ui_unification_v2_sanitisation_2026_04_20.plan.md` § `p8-audit-legacy-family-strings` for the sweep.
- Legacy `basis-trade` route in `unified-trading-system-ui/app/(platform)/services/trading/strategies/` is renamed to
  `carry-basis` — the strategy ids under that page already cite the v2 canonical `CARRY_AND_YIELD.CARRY_BASIS_PERP`
  archetype.
- `V2` suffix was dropped from all v2 types on 2026-04-21 (`StrategyFamilyV2` → `StrategyFamily`, `StrategyArchetypeV2`
  → `StrategyArchetype`). See `strategy-registry-v2.md`.
