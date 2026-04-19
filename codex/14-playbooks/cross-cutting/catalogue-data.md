# Data Catalogue

One of the four catalogues. See [catalogues.md](catalogues.md) for the umbrella pattern.

## Status: ⚠ SSOT exists; UI surface fragmented

Data SSOT lives in multiple services. UI exists as a data service with 13 pages, but has NOT been unified into a single
"catalogue" surface comparable to strategy-catalogue.

## Service SSOT

- [market-tick-data-service](https://) — availability manifest (`ManifestWriter` writes shard-partitioned availability
  rows)
- [instruments-service](https://) — instrument registry (reference data SSOT per
  [../../02-data/availability-manifest-and-data-status.md](../../02-data/availability-manifest-and-data-status.md))
- [unified-reference-data-interface](https://) — sports reference data sub-package

## UAC registry

- `unified_api_contracts/canonical/domain/` — domain schemas per data type
- `unified_api_contracts/registry/capability_declarations/` — per-venue capability declarations (spot, perp, options,
  dated-futures, sports, prediction markets)

## UI route (today)

13 pages under `/services/data/`:

- `overview`, `instruments`, `venues`, `coverage`, `completeness`, `missing`, `gaps`, `events`, `logs`, `processing`,
  `raw`, `valuation`, `markets/pnl`

Overlap: `completeness` + `missing` + `gaps` cover the same concept three ways. Phase 3 merges to `gaps` with tabs
inside.

## Gap vs canonical pattern

Comparing to the 4-catalogue parity goal:

| Parity feature        |           Strategy Catalogue            |                Data Catalogue                 |
| --------------------- | :-------------------------------------: | :-------------------------------------------: |
| Overview page         |    ✅ `/services/strategy-catalogue`    |         ✅ `/services/data/overview`          |
| Coverage matrix       | ✅ `/coverage` (archetype × cat × inst) |  ⚠ `/coverage` exists but flat, not matrix   |
| By-combination filter |                   ✅                    |                       —                       |
| Per-entry detail      |   ✅ `/strategies/[archetype]/[slot]`   | ⚠ `/instruments` has list but no detail page |
| Admin lock-state      |         ✅ `/admin/lock-state`          |                       —                       |
| Blocked               |         ✅ `/coverage/blocked`          |                       —                       |

## What to build for parity

1. **Move away from "data service" → "data catalogue"** — unify the 13 pages under a catalogue-pattern surface
2. **Coverage matrix**: instrument_type × venue × data_type × availability %
3. **Per-entry detail**: one page per (instrument, venue, data_type) triple showing its availability history, schema,
   sample rows
4. **Lock state**: reserved instruments (e.g. Odum-proprietary sports signals) shown only to admin/IM
5. **Blocked**: instruments we CANNOT ingest due to venue restrictions, licensing, etc. + remediation

Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Cross-playbook surface

- **pb1** — coverage stats teased on homepage (100+ venues, 100+ TB)
- **pb2b (DART briefing)** — deep-briefing content covers data catalogue scope
- **pb3c (DART demo)** — demo user sees full data catalogue with venue/instrument filters
- **pb3a/b (IM / Reg demo)** — data catalogue not surfaced (locked or hidden; IM prospects don't need to see data layer)

## Related

- Umbrella: [catalogues.md](catalogues.md)
- Availability manifest SSOT:
  [../../02-data/availability-manifest-and-data-status.md](../../02-data/availability-manifest-and-data-status.md)
- Contracts scope and layout: [../../02-data/contracts-scope-and-layout.md](../../02-data/contracts-scope-and-layout.md)
- Visibility slicing: [visibility-slicing.md](visibility-slicing.md)
