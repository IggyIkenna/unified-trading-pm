---
title: "lending-indices canonical manifest has kebab-case + snake-case data_type drift (24,976 kebab + 21,044 snake)"
created: 2026-05-16
author: ikenna-slot-2
source:
  - gs://lending-indices-central-element-323112/_index/availability_index.parquet
  - market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py (constant _LENDING_INDICES_DATA_TYPE)
  - codex/02-data/availability-manifest-and-data-status.md (3K update — canonical type names)
severity: P1 — affects DEFI asset_group manifest queryability + the 3-LENDING.5 reconciler scope
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

Diagnostic read of `gs://lending-indices-central-element-323112/_index/availability_index.parquet` 2026-05-16
(46,020 manifest rows, 39,851 captured) shows **two values for `data_type`** coexisting in the same canonical
manifest:

| `data_type` value  | Row count  |
| ------------------ | ---------- |
| `lending-indices`  | **24,976** |
| `lending_indices`  | **21,044** |
| **Total**          | 46,020     |

Both values land in the same canonical manifest (same `_index/availability_index.parquet`), under the same hive
path (`category=defi/venue={PROTOCOL}/chain={CHAIN}/instrument_type=lending/data_type=lending_indices/`).

Other column distributions:

- **Venues** (3): AAVEV3 (28,512), COMPOUNDV3 (14,197), SPARK (3,311). Note `AAVEV3` not `AAVE_V3` (no underscore).
- **Chains** (10): ETHEREUM / OPTIMISM / BASE / ARBITRUM / POLYGON / AVALANCHE / BSC / LINEA / SCROLL / ZKSYNC.
- **capture_status**: 39,851 captured / 6,012 empty_confirmed / 157 attempted_failed.

## Why it matters

1. **Manifest-consumer queries break silently**: any downstream service / cron / data-status UI / dependency-checker
   filtering `data_type == "lending_indices"` sees only HALF the manifest. Filter on the other form → opposite half.
2. **3-LENDING.5 reconciler scope**: the in-flight slot-2 sub-agent (dispatch `a8d9a9f29f77e0c48`,
   `instruments-service/scripts/reconcile_lending_indices_phantom.py`) must accept BOTH forms in its row-key match
   logic. A naive `df.query("data_type=='lending_indices'")` filter would miss 24,976 rows (54% of manifest).
3. **3K codex update accuracy**: `codex/02-data/availability-manifest-and-data-status.md` § "Phase 1A DeFi bundled
   data_types" lists `lending_indices` (snake) as the canonical type. Operator should ratify which form is canonical
   so the drift can be reconciled in one direction.
4. **Hive path vs manifest column inconsistency**: the actual GCS hive segment is `data_type=lending_indices` (snake,
   confirmed via `gsutil ls`) — so the on-disk vocabulary is consistent. Only the manifest column carries both.

## Why this drift exists (root cause hypothesis)

The handler emits one form (likely `lending_indices` snake — line ~115 of `lending_indices_handler.py` has the
constant `_LENDING_INDICES_DATA_TYPE = "lending_indices"`). The other form (`lending-indices` kebab) may be:

- (a) **Legacy emission** from an older handler revision pre-canonicalisation (timeline check: 24,976 kebab rows
  span which date range? — answer in `written_at` column groupby).
- (b) **Cross-asset rescan** (`reconcile_phantom_manifest_rows_all.py` or related migration script) that wrote rows
  using a different convention.
- (c) **Manual operator-VM rebuild** that hardcoded the kebab form.

Quick diagnosis: `df.groupby('data_type').agg({'written_at': ['min', 'max']})` would show whether kebab rows are
pre-2026-05 (legacy) or contemporary (active drift).

## Recommended decision

**Option A (recommended — operator-acked taxonomy)**: declare `lending_indices` (snake) the canonical form per the
asset_group vocabulary rule pattern (CLAUDE.md § "Asset-group vocabulary"). Ship a one-shot migration script
`instruments-service/scripts/canonicalize_lending_indices_data_type_2026_05_16.py` that:

1. Reads the manifest
2. Flips all `data_type == "lending-indices"` → `data_type == "lending_indices"` (in-place column update)
3. Writes back with v8-tolerant `df.to_parquet`
4. Idempotent re-runs

This is ~30-min work; blocks the 3-LENDING.5 reconciler from having to handle both forms.

**Option B**: extend the 3-LENDING.5 reconciler to accept both forms in its `data_type` filter and leave the drift
in place (defer canonicalisation to post-cutover).

**Option C**: investigate root cause first — find which handler / migration emitted kebab — fix at source then
backfill-canonicalize.

## Suggested owner

ikenna-slot-2 (slot-2 already in this manifold this session) — pending operator nod on Option A vs B vs C.

## Cross-references

- 3-LENDING.5 reconciler in-flight: sub-agent `a8d9a9f29f77e0c48` writing
  `instruments-service/scripts/reconcile_lending_indices_phantom.py`
- Spec source: `plans/active/defi_catalogue_chain_primitives_2026_05_10.md` § Phase 3 todo `3-LENDING.5`
- 3K codex update: `codex/02-data/availability-manifest-and-data-status.md` (PM@`aab47b12`)

execution:
  owner: "operator decision on Option A/B/C; ikenna-slot-2 ships the migration once decided"
  cadence: "one-shot operator decision + one-shot migration"
  verifier: "lending-indices manifest groupby data_type returns 1 row (canonical form only)"
  last_executed: "NEVER (diagnostic only 2026-05-16)"
