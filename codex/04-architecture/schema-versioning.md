---
doc_type: codex-ssot
title: Schema Versioning
summary:
  How UAC versions its schemas — semver rules (patch/minor/major = breaking), the 60-day parallel-publish deprecation
  window, consumer major-version pinning, and how internal vs external canonical schemas differ.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [uac, schema, versioning, contracts, migration, semver]
related:
  [
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/schema-placement.md,
    /codex/02-data/contracts-scope-and-layout.md,
  ]
created: 2026-04-17
authoritative_for:
  [UAC schema semver rules (patch/minor/major), UAC schema deprecation window + consumer major-version pinning]
referenced_by:
  [
    /codex/03-services/venue-capability-registry.md,
    /codex/04-architecture/artifact-versioning.md,
    /codex/04-architecture/schema-placement.md,
    /codex/04-architecture/shadow-deployment-pattern.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/06-coding-standards/artifact-naming.md,
    /codex/06-coding-standards/semver.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Schema Versioning

> **What it is:** How UAC (`unified-api-contracts`) versions its schemas; how consumers pin to major versions; how
> deprecation windows work; how internal schemas (`unified_api_contracts.internal`) differ from external canonical
> schemas.

## UAC scope recap

| Package path                              | Contents                                                                                          | Versioning    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------- |
| `unified_api_contracts` (facades)         | Consumer-facing domain facades (`market`, `execution`, `strategy`, `risk`, `reference_data`, ...) | Semver on UAC |
| `unified_api_contracts.canonical.*`       | **UAC-internal** — normalized canonical types; not for direct import                              | Internal      |
| `unified_api_contracts.external.{source}` | **UAC-internal** — per-source wire schemas (Binance, Pinnacle, SharpAPI, etc.)                    | Internal      |
| `unified_api_contracts.internal`          | Cross-service internal types (instructions, events, directives)                                   | Semver on UAC |
| `unified_api_contracts.normalize_utils`   | **UAC-internal** — normalization helpers; not for direct import                                   | Internal      |

**Rule (Citadel):** Consumer repos import from domain facades only:

```python
from unified_api_contracts.execution import StrategyInstruction
from unified_api_contracts.market import Tick
from unified_api_contracts.strategy import StrategyConfig
from unified_api_contracts.internal import AllocationDirective, InstructionId
```

NOT:

```python
from unified_api_contracts.canonical.execution import StrategyInstruction  # WRONG
from unified_api_contracts.external.binance import BinanceOrder             # WRONG
from unified_api_contracts.normalize_utils import normalize_price           # WRONG
```

See `imports/uac-import-surface-enforcement.mdc`.

## Semver rules

### Patch (1.4.2 → 1.4.3)

- Docstring / comment changes
- Bug fix without behavior change
- Test additions
- No schema content changes

### Minor (1.4 → 1.5)

- **Backward-compatible** field additions
- New types added to a facade
- Adding enum values at end (with explicit handling of unknown values in consumers)
- Adding optional fields

Consumers unchanged; can adopt new fields lazily.

### Major (1.x → 2.0)

- **Breaking change**
- Field rename
- Field type change
- Field removal
- Enum reordering
- Semantic meaning change

Requires migration.

## Deprecation window

Major bumps enter a **60-day deprecation window** by default:

- Both UAC 1.x and 2.x available in parallel
- Consumer repos migrate on their schedule
- After 60 days, 1.x dropped from latest
- Historical event data serialized with 1.x remains replayable via UAC archive

## Consumer pinning

Consumer repos pin a UAC major version in `pyproject.toml`:

```toml
[project]
dependencies = [
    "unified-api-contracts>=1.4.0,<2.0.0",  # pinned to UAC 1.x
]
```

Per CLAUDE.md: **flat deps only**, no optional-dependencies, no dev extras. The version floor is automation-managed
(semver-agent); never edit manually.

## Breaking change protocol

1. **RFC**: propose breaking change; PR review
2. **Parallel publish**: UAC publishes both old and new forms
3. **Migration scripts**: for historical data in affected service stores
4. **Staged rollout**: UI → API gateways → services (staging first)
5. **Workspace sweep**: every consumer updated in same PM plan
6. **Remove old form**: after 60 days
7. **Audit old events**: remain replayable via UAC archive

## Schema evolution patterns

### Adding a field (minor)

UAC 1.4 → 1.5: add `urgency` to `StrategyInstruction`

```python
# 1.4
class StrategyInstruction(BaseModel):
    instruction_id: str
    ...

# 1.5
class StrategyInstruction(BaseModel):
    instruction_id: str
    urgency: UrgencyEnum = UrgencyEnum.MEDIUM     # optional with default
    ...
```

Old consumers ignore the new field. New consumers use it.

### Renaming a field (major)

UAC 1.x → 2.0: rename `notional_usd` → `notional_in_share_class_unit`

```python
# 1.x
class StrategyInstruction(BaseModel):
    notional_usd: Decimal

# 2.0
class StrategyInstruction(BaseModel):
    notional_in_share_class_unit: Decimal
```

Parallel publish as UAC 1 and UAC 2 side-by-side. Consumers migrate.

### Changing semantics (major)

UAC 1.x → 2.0: `target_position_units` semantics change from "absolute" to "signed-by-side"

```python
# 1.x: target=10, side=BUY → long 10
# 2.0: target=+10 → long 10; target=-10 → short 10
```

Major bump required. Migration script converts stored 1.x instructions to 2.0 semantics.

### Adding an enum value (minor)

Adding `HYPERLIQUID` to `VenueEnum`:

```python
# 1.4
class VenueEnum(str, Enum):
    BINANCE = "BINANCE"
    OKX = "OKX"

# 1.5
class VenueEnum(str, Enum):
    BINANCE = "BINANCE"
    OKX = "OKX"
    HYPERLIQUID = "HYPERLIQUID"
```

Consumers handle unknown enum values gracefully (skip with warning, not crash).

### Removing an enum value (major)

Removing a venue enum member (example: `RETIRED_CEFI_SLOT`):

- Major bump
- Parallel 1.x serves existing consumers
- New events don't emit the removed member
- Historical data retains the old value in 1.x archived form

## Archive of historical schemas

For replay / audit, UAC maintains:

- All historical minor + major versions
- Migration utilities (1.x → 2.0 where defined)
- Fixture data for conformance testing across versions

## Internal schemas

`unified_api_contracts.internal` covers types that don't cross external boundaries:

- `AllocationDirective`
- `InstructionId`
- Internal events
- Cross-service coordination types

Same semver rules. Same consumer pinning.

## Generated OpenAPI

UAC schemas are source-of-truth for OpenAPI generation. API gateways and UI fetch hooks derive from UAC. See the
existing pipeline in PM memory `openapi_sync_and_ui_wiring`.

When a schema changes:

- UAC publishes new version
- OpenAPI regenerated
- UI hooks / types regenerated
- Breakages caught at QG

## Strategy registry via UAC

Strategy registry (archetypes, instance metadata) is in UAC (per memory `strategy_registry_ssot_in_uac`). UI's old
`strategy-registry.ts` should be replaced with auto-generated code from UAC.

## Event tag stability

The event tag tuple
`(family, archetype_id, archetype_build_version, strategy_instance_id, slot_version, config_hash, config_version, client_id, share_class)`
is a stable contract. Adding fields is a minor bump. Renaming or reordering is major.

## Migration tooling

- **Schema-diff tool**: compare two UAC versions; report breaking / non-breaking changes
- **Migration script**: for per-field transformations on historical event stores
- **Conformance tests**: run for every UAC version against fixture data

## QG enforcement

Per CLAUDE.md:

- `basedpyright` must pass on all consumer repos after any UAC update
- Cassette parity tests in UAC run every commit
- Consumer auto-update via `update-dependency-version.yml` workflow

## Cross-references

- UAC Citadel architecture: [/codex/02-data/contracts-scope-and-layout.md](/codex/02-data/contracts-scope-and-layout.md)
- Import rules: `imports/uac-import-surface-enforcement.mdc` (in workspace root)
- Artifact versioning (separate axis): [artifact-versioning.md](artifact-versioning.md)
- Semver agent: workflow `semver-agent.yml`
- Strategy identity:
  [/codex/06-coding-standards/strategy-identity-versioning.md](/codex/06-coding-standards/strategy-identity-versioning.md)

## Not in this doc

- **Per-schema content** — UAC itself
- **OpenAPI generation pipeline** — UAC docs + existing `generate_ui_reference_data.py`
- **UI codegen** — UI repos + hooks generator
- **Database migrations** — per-service infra
- **Event store schema evolution** — event-store architecture (not schemas themselves)
