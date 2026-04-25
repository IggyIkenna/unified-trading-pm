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

3. **GCS and historical blob layout**
   - Path segments like **`category=cefi`** remain **on-object-store** facts. Renaming to `asset_group=…` in URIs is a
     **data migration** (new prefixes, backfill, readers), not a field rename in API code.
   - Code may use clearer local variable names (for example `asset_group_lower`) while still emitting legacy segment
     literals where buckets are unchanged.

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
validation alias**, deployment-ui and mocks updated. **GCS** path templates still pass a `category=` **format** argument
where bucket layout requires it; object-store URI migration remains a separate program.

## Related

- `unified-trading-pm/plans/active/venue_axis_asset_group_vocabulary_2026_04_25.plan.md` — venue-axis vocabulary in
  UAC/UTL/MDPS/MTDS.
- `unified-trading-pm/plans/active/shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` — global rename of shard
  dimension metadata and consumers.
- Implementation notes: `deployment-api` `DeployRequest` / `DeployMissingRequest` docstrings on the route models.
