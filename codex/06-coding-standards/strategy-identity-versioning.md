---
doc_type: codex-ssot
title: Coding Standard — Strategy Identity + Versioning
summary: >-
  Strategy identity + versioning rules — the 5-layer identity (family→archetype→instance→config→derived categories),
  archetype-ID structural-descriptor rules, the three interlocking naming forms (slot label / fully-qualified /
  bare-slot id) with the parse_strategy_id/format_strategy_id contract, config content-hash + monotonic version, the -vN
  slot suffix, the full event-tag tuple, and the QG enforcement checks. MERGED 2026-07-30 from
  /codex/09-strategy/architecture-v2/naming-convention.md (operator ruling, docs_reconcile_autonomous_sweep_2026_07_30
  P0-B — two status:current SSOTs both claimed authoritative_for "slot-label grammar" and disagreed on the archetype
  enum size).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, versioning, canonicalisation, uac, quality-gates, execution, refactor, catalogue]
related:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
    /codex/06-coding-standards/strategy-display-conventions.md,
    /codex/06-coding-standards/artifact-naming.md,
    /codex/04-architecture/artifact-versioning.md,
  ]
created: 2026-04-17
authoritative_for:
  [
    "strategy identity + versioning (5-layer identity, archetype-ID rules)",
    canonical strategy-id naming grammar (slot-label / fully-qualified / bare-slot),
  ]
referenced_by:
  [
    /codex/02-data/feature-formula-versioning.md,
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/data-flow-map.md,
    /codex/04-architecture/schema-versioning.md,
    /codex/04-architecture/shadow-deployment-pattern.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/artifact-naming.md,
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/templates/strategy-description-template.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/value-betting-archetype-decision.md,
  ]
owner:
last_reviewed:
code_refs:
  [unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py, unified_api_contracts.strategy]
---

# Coding Standard — Strategy Identity + Versioning

> **What it is:** Mandatory naming + versioning rules for strategies. Every strategy in the system has a 5-layer
> identity (family → archetype → instance → config → derived categories), three interlocking naming forms (slot label,
> fully-qualified id, bare slot id), version tuples, and full event tags. These rules are enforced at QG.

**Owning UAC module:** `unified_api_contracts/internal/architecture_v2/strategy_naming.py` (re-exported from the
`unified_api_contracts.strategy` facade as `parse_strategy_id` / `format_strategy_id` / `ParsedStrategyId`), plus
`enums.py` for `StrategyFamily` / `StrategyArchetype` / `ARCHETYPE_TO_FAMILY`.

## The 5 layers

| Layer              | Values                           | Change semantics                     |
| ------------------ | -------------------------------- | ------------------------------------ |
| Family             | 9 enum                           | Never (new family = new code domain) |
| Archetype          | 60 enum                          | Build version bumps on code change   |
| Instance           | slot_label                       | Created once; retired later          |
| Config             | content hash + monotonic version | Any config change bumps              |
| Derived categories | multi-valued lists               | Derived from venues; never stored    |

### Family axis (9 values)

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

### Archetype axis (60 values — VERIFIED, code ground truth)

The archetype count has moved twice since this doc's creation: 18 at the 2026-04-17 baseline → 57 after the Phase 9
expansion (2026-04-25) and the 2026-05-18 taxonomy decision → **60**, measured directly against
`unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` on 2026-07-30 (both a member count and an AST
count agree). **Do not hardcode this number anywhere else** — count the enum at the point of use; it will move again as
new archetypes are added.

The archetype → family relation is declared in `ARCHETYPE_TO_FAMILY` (same module) — **never** hardcode the family;
always look it up.

## Archetype ID rules

Archetype IDs:

- **MUST use structural descriptors**: `CONTINUOUS`, `EVENT_SETTLED`, `PAIRS_FIXED`, `CROSS_SECTIONAL`, `BASIS_DATED`,
  `BASIS_PERP`
- **MUST NOT encode execution category**: no `CEFI_`, `DEFI_`, `TRADFI_`, `SPORTS_`, `PREDICTION_` prefixes
- **MUST be stable** — once published, never renamed; new logic = new archetype ID

### Valid

```
ML_DIRECTIONAL_CONTINUOUS
ML_DIRECTIONAL_EVENT_SETTLED
RULES_DIRECTIONAL_CONTINUOUS
CARRY_BASIS_DATED
CARRY_STAKED_BASIS
ARBITRAGE_PRICE_DISPERSION
MARKET_MAKING_CONTINUOUS
VOL_TRADING_OPTIONS
STAT_ARB_PAIRS_FIXED
STAT_ARB_CROSS_SECTIONAL
```

### Invalid

```
CEFI_ML_DIRECTIONAL              # category prefix forbidden
ML_DIRECTIONAL                   # missing structural axis (continuous vs event-settled)
TRADFI_OPTIONS_ML                # category + non-structural
SPORTS_MM                        # category prefix + truncation
```

## Three identifier forms

The v2 architecture uses three interlocking identifiers:

| Form            | Grammar                                             | Example                                                           | Audience                                                                        |
| --------------- | --------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Slot label      | `ARCHETYPE@venue-asset-instrument-period-quote-env` | `CARRY_BASIS_PERP@binance-eth-perp-10m-usdt-prod`                 | Registry, records pipeline, strategy-service internals, availability manifests. |
| Fully-qualified | `FAMILY.ARCHETYPE.slot_id`                          | `CARRY_AND_YIELD.CARRY_BASIS_PERP.binance-eth-perp-10m-usdt-prod` | UI URLs, admin surfaces, codex cross-references, external docs.                 |
| Bare slot id    | `venue-asset-instrument-period-quote-env`           | `binance-eth-perp-10m-usdt-prod`                                  | Contexts where the archetype + family are already known (e.g. nested UI tabs).  |

The **family** is never stored inside the slot label — it is always derivable from the archetype via
`ARCHETYPE_TO_FAMILY`. The fully-qualified form duplicates the family purely for audit clarity.

### Slot-id grammar

A slot id is a hyphen-separated 6-tuple that identifies a unique run configuration, optionally carrying a `-v{N}` slot
version suffix before the env segment:

```
{venue}-{asset}-{instrument_type}-{period}-{quote_ccy}[-v{N}]-{env}
```

Conventions:

- **Lower-case, hyphen-separated** — matches DNS / URL conventions.
- **No `@` anywhere inside the slot id** — the `@` is reserved as the slot-label separator.
- **Dots (`.`) are allowed** only in non-first positions, but must not appear before any `@` if the slot id is later
  wrapped into a slot-label form. The fully-qualified parser splits on the first two dots only; everything after the
  second dot is the slot id.
- `venue`/`asset` may be multi-token (e.g. multi-venue uses `-` — `binance-okx`).
- `period` (timeframe) is optional when the archetype implies it (e.g. cross-sectional daily); included when
  strategy-specific.
- `quote_ccy` (share class) lowercased (usdt, usdc, usd, eth, btc, sol, gbp, eur).
- `-v{N}` is an optional slot version (`-v2`, `-v3`) for a material dependency change warranting distinction (see "Slot
  version" below) — absent from the slot-id form unless the strategy actually has one.
- **Env** ∈ {prod, paper, canary, dev, staging, demo} — environments for the same underlying run are tagged here.

### Examples (valid)

```
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod
CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
YIELD_ROTATION_LENDING@aave-multichain-usdc-prod
ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod
VOL_TRADING_OPTIONS@deribit-btc-vol-usdt-prod
MARKET_MAKING_EVENT_SETTLED@betfair-epl-mm-gbp-prod
```

### Examples (invalid)

```
ml-directional@btc                     # missing venue, share class, env
CEFI_ML_DIRECTIONAL@binance-btc-5m-usdt-prod        # category prefix on archetype
ML_DIRECTIONAL_CONTINUOUS@BINANCE-BTC-5m-USDT-prod   # caps inconsistent
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt    # missing env
```

## Parser contract (`parse_strategy_id`)

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

## Formatter contract (`format_strategy_id`)

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

## Where each form is used

| Surface                                                      | Form            | Rationale                                                                  |
| ------------------------------------------------------------ | --------------- | -------------------------------------------------------------------------- |
| `StrategyDefinition.strategy_id` (UAC registry)              | Slot label      | Historical — registry was seeded from the slot grammar; unchanged in v2.   |
| Record enricher `strategy_name` stamps                       | Slot label      | Matches registry id — records join against registry by exact id match.     |
| UI route `/services/strategy-catalogue/strategies/[id]`      | Fully-qualified | Family prefix is load-bearing — human readers see lineage in the URL.      |
| Admin strategy detail view                                   | Fully-qualified | Admin audit logs surface family + archetype explicitly.                    |
| Signal broadcast envelopes (`StrategySignalEmittedExternal`) | Fully-qualified | External counterparties benefit from family-level disambiguation.          |
| Availability manifest `strategy_id` column                   | Slot label      | Consistent with records pipeline; FQ derivation is one function call away. |

## Config hash + version

### Config hash

- Computed from config content (JSON-serialized, deterministic key order)
- Hash algorithm: SHA-256 truncated to 16 hex chars (e.g., `a7f3b2e1c9d4f8a0`)
- Any content change → new hash

### Config version

- Monotonic integer, scoped to `(slot_label)`
- Increments on every content change
- Persisted per-slot in config registry

### Content hash vs version

Content hash is identity; version is ordinal. Two configs with identical content have same hash regardless of order; but
versions within a slot are always increasing.

## Slot version (optional suffix)

Slot version bumps when a dependency change is material enough to warrant a human-visible distinction:

- Model family swap (CatBoost → XGBoost)
- Feature group major-version bump
- Venue swap (Binance → OKX primary)
- Staking method swap (fractional Kelly → Risk Parity)

Config version alone is insufficient because the new slot is materially a "different strategy" for observability +
reporting purposes. Example:

```
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod       (v1, CatBoost model)
ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod    (XGBoost model)
```

These run in parallel (shadow), compared, and eventually one retires.

## Event tag (full tuple)

Every fill, instruction, PnL row, audit entry carries:

```
(
  family,
  archetype_id,
  archetype_build_version,
  strategy_instance_id,
  slot_version,
  config_hash,
  config_version,
  client_id,
  share_class
)
```

`strategy_instance_id` encodes the slot label. `slot_version` is the integer after `-v` in the slot label (default 1 if
no suffix).

## Archetype build version

- Git-SHA based: `{semver}-{git_sha[:7]}`
- Semver from release tag of strategy-service
- Incremented on every strategy-service release

Example: `1.4.2-a7f3b2e`

## Category derivation (multi-valued)

Never hardcode category on the strategy. Derive from venues:

```python
def derive_execution_categories(config):
    return sorted(set(
        venue_registry.get(v).category
        for v in config.execution_venues
    ))

def derive_data_categories(config):
    return sorted(set(
        venue_registry.get(v).category
        for v in config.all_data_subscriptions
    ))
```

For UI + reporting only; never for code routing.

## Instance registration

At creation, the slot is registered with:

```yaml
strategy_instance_id: "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
archetype_id: ML_DIRECTIONAL_CONTINUOUS
family: ML_DIRECTIONAL
client_id: "client_A_fund"
capital_budget_share_class_amount: 2_500_000
capital_budget_share_class: USDT
risk_budget:
  max_daily_loss_bps: 200
  max_drawdown_bps: 500
share_class: USDT
env: prod
created_at_utc: "2026-04-17T00:00:00Z"
created_by: operator@firm
```

Registered in the strategy registry (UAC SSOT) — not hand-maintained per CLAUDE.md memory.

## QG enforcement

The following are checked at quality gates:

1. `archetype_id` ∈ archetype enum (no freeform strings)
2. `slot_label` matches grammar regex
3. No category prefix in archetype ID
4. `share_class` lowercase
5. `env` ∈ {prod, paper, canary, dev, staging, demo}
6. `venue_scope` tokens all in venue registry
7. `share_class` compatible with venue set per share-class axis rules
8. Config hash computed and matches declared hash
9. Config version monotonic (greater than last-persisted version for this slot)
10. Every event carries full event tag
11. Every new archetype added to `enums.StrategyArchetype` MUST round-trip both slot-label and FQ forms via
    `format_strategy_id` + `parse_strategy_id` (`test_parse_slot_label_all_archetypes_roundtrip_via_format` +
    `test_parse_fq_all_archetypes_roundtrip_via_format` cover this automatically). Unit tests live in
    `tests/internal/unit/test_strategy_naming.py`; mismatch + malformed inputs get explicit negative tests in the same
    file.

## Retirement

To retire an instance:

1. Kill switch: `DISABLED`
2. Unwind positions (via `AccountInstruction.CLOSE_ALL_FOR_STRATEGY`)
3. Mark instance status `RETIRED` with timestamp
4. Audit log retained permanently
5. Slot label NEVER re-used — if rebirth needed, use `-v2` suffix

## Migration notes

- v1 lowercase family slugs (`basis-trade`, `mean-reversion`, `sports-arb`, `prediction-ml`) are **not** part of this
  convention and must not appear as route slugs / filter values / display labels. See
  `ui_unification_v2_sanitisation_2026_04_20.plan.md` § `p8-audit-legacy-family-strings` for the sweep.
- Legacy `basis-trade` route in `unified-trading-system-ui/app/(platform)/services/trading/strategies/` is renamed to
  `carry-basis` — the strategy ids under that page already cite the v2 canonical `CARRY_AND_YIELD.CARRY_BASIS_PERP`
  archetype.
- `V2` suffix was dropped from all v2 types on 2026-04-21 (`StrategyFamilyV2` → `StrategyFamily`, `StrategyArchetypeV2`
  → `StrategyArchetype`). See `strategy-registry-v2.md`.
- v1 `StrategyFamily` (17 values) was deleted 2026-04-21 per `ui_unification_v2_sanitisation_2026_04_20`.

## Anti-patterns

- **Renaming an archetype** — never; make a new one
- **Re-using a slot label** — never; pick a new instance id or bump `-v`
- **Hardcoding category in archetype ID** — forbidden
- **Hardcoding the archetype/family enum size anywhere** — count the enum at the point of use (this doc has been wrong
  about the count twice; do not add a third stale number)
- **Skipping config version** — always monotonic
- **Emitting events without full tag** — rejected at QG
- **Strategy code reading `strategy_instance_id` to branch behavior** — violates archetype-as-code-path; if branching
  needed, separate archetype

## Testing

- Unit tests live in `tests/internal/unit/test_strategy_naming.py`.
- Every new archetype added to `enums.StrategyArchetype` MUST round-trip both slot-label and FQ forms (see QG
  enforcement item 11 above).
- Mismatch + malformed inputs: explicit negative tests in the same file.

## Cross-references

- Full architecture: [/codex/09-strategy/architecture-v2/README.md](/codex/09-strategy/architecture-v2/README.md)
- Strategy registry: [strategy-registry-v2.md](/codex/09-strategy/architecture-v2/strategy-registry-v2.md) — how the
  registry derives entries from the archetype capability matrix.
- Strategy-execution protocol:
  [/codex/04-architecture/strategy-execution-protocol.md](/codex/04-architecture/strategy-execution-protocol.md)
- Artifact versioning: [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md)
- Schema versioning: [/codex/04-architecture/schema-versioning.md](/codex/04-architecture/schema-versioning.md)
- Artifact naming: [artifact-naming.md](artifact-naming.md)

## Not in this doc

- **Per-artifact naming** — [artifact-naming.md](artifact-naming.md)
- **Code module layout** — contribution-guide.md
- **CI/CD release flow** — deployment-service
- **UI naming conventions** — UI repos
