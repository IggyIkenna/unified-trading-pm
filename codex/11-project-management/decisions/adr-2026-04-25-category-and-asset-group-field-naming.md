---
scope: [engineer, admin]
status: accepted
date: 2026-04-25
---

# ADR: `category` vs `asset_group` in deployment APIs and shard naming

## Context

The trading **venue axis** (CeFi / DeFi / TradFi / Sports / …) is referred to in code and product language as **asset
group**. Parallel legacy names (`category`, `VENUES_BY_CATEGORY`, …) still exist in data-registry SSOT, and
**object-store layout** has used hive-style path segments such as `category=cefi` for a long time.

Workstreams have normalized **JSON field names and public query parameters** to `asset_group` in several surfaces (data
status, drilldowns, VM listings). The **general create-deployment** path and **service sharding config** still use the
dimension key **`category`** in places. Confusion arises when the same business concept is labeled `category` in one API
and `asset_group` in another, or when “rename everything” is proposed without separating **wire names**, **config
dimension names**, and **GCS key segments**.

## Decision

1. **General deployment create (`DeployRequest` in deployment-api)**
   - Request body field and `extra_filters` key: **`asset_group`**. Legacy clients may still send **`category`**; it is
     accepted via Pydantic validation alias and maps to the same field. Sharding configs use dimension
     `name: asset_group`.

2. **Deploy-missing (`DeployMissingRequest`)**
   - JSON field **`asset_group`** (same semantic as general deploy); passed through to `DeployRequest.asset_group`.

3. **GCS and historical blob layout (updated 2026-05-01)**
   - **`asset_group=`** is **canonical** for new MTDS writes (per
     `market_tick_data_service/raw_tick_hive.RAW_TICK_ASSET_GROUP_HIVE_KEY`). All writers added or refreshed after
     2026-04 emit this form via the constant.
   - **`category=`** is the **legacy** on-disk form (`RAW_TICK_ASSET_GROUP_HIVE_KEY_LEGACY`) preserved in production GCS
     without a re-keying migration. The two vocabularies coexist on disk; **no bulk re-key** of historical `category=`
     paths is performed.
   - Readers must try canonical first then fall back to legacy. `market_tick_data_service.reader` does this directly;
     `deployment-api/utils/storage_facade.list_objects` transparently fans out to both vocabularies for any prefix
     matching `(?:category|asset_group)=(cefi|defi|tradfi|sports|prediction)/`.
   - Manifest pre-flight is hive-key-agnostic — it indexes by `(date, venue, chain, instrument_type, data_type)` only,
     so legacy `category=` parquets on disk are correctly skipped iff the manifest has a captured row for the shard.

4. **Service dimension metadata (mock services, deploy UI, shard configs)**
   - Dimension name in sharding YAML and service-dimension lists: **`asset_group`**. UI copy may still say “Category”
     where it helps operators; that is presentation-only.

## Consequences

- **Positive:** One primary name (`asset_group`) for the trading venue axis in APIs and shard configs; legacy `category`
  in JSON still works during client rollouts.
- **Negative:** Accepting both keys requires discipline in new clients (prefer `asset_group` only).

## Implementation (2026-04-25)

The coordinated pass **landed**: sharding YAML `name: category` → `asset_group` (deployment-service +
`unified-trading-pm/configs` copies), deployment-service `extra_filters` / shard dicts use `asset_group` with legacy
`category` coalescing in `DimensionProcessor`, `DeployRequest` JSON field `asset_group` with `category` as **Pydantic
validation alias**, deployment-ui and mocks updated.

**GCS hive vocabulary follow-up (2026-05-01):**

- MTDS writers (`tardis_shared`, `defi/canonical_write`, `tradfi_shared`, orchestrator `PartitionedTickWriter`) emit
  canonical `asset_group=` via `RAW_TICK_ASSET_GROUP_HIVE_KEY`.
- MTDS `CanonicalParquetReader` falls back to `category=` when canonical prefix is empty.
- deployment-api `storage_facade.list_objects` adds dual-vocab fan-out: any prefix matching
  `(?:category|asset_group)=(cefi|defi|tradfi|sports|prediction)/` is listed under both variants and merged.
- deployment-api `shard_detail._mtds_shard_path` lists the venue+data_type prefix and matches by leaf suffix to return
  the actual existing path under either vocabulary.
- `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` probes both vocabularies and tolerates schema-v4
  empty `instrument_type` rows + casing drift (`PERPETUAL` vs `perpetual`) when classifying phantoms.

**Object-store URI migration is intentionally NOT performed.** The two vocabularies coexist on disk; readers handle the
fan-out transparently. Only forward-bound rewrites (DeFi bare `venue=…/` → `asset_group=defi/venue=…/`) and
instrument-type case-normalization remain as separate small-scope follow-ups.

## Related

- `unified-trading-pm/plans/archive/venue_axis_asset_group_vocabulary_2026_04_25.plan.md` — venue-axis vocabulary in
  UAC/UTL/MDPS/MTDS.
- `unified-trading-pm/plans/archive/shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` — global rename of shard
  dimension metadata and consumers.
- Implementation notes: `deployment-api` `DeployRequest` / `DeployMissingRequest` docstrings on the route models.
