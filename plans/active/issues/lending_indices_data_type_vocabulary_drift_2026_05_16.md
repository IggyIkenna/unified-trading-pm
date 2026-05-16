---
title: "Cross-bucket DeFi canonical-manifest data_type vocabulary drift — SYSTEMIC (6 of 7 manifests affected)"
created: 2026-05-16
author: ikenna-slot-2
source:
  - gs://lending-indices-central-element-323112/_index/availability_index.parquet
  - gs://oracle-prices-central-element-323112/_index/availability_index.parquet
  - gs://lst-rates-central-element-323112/_index/availability_index.parquet
  - gs://perp-funding-central-element-323112/_index/availability_index.parquet
  - gs://dex-swaps-central-element-323112/_index/availability_index.parquet
  - gs://dex-pools-central-element-323112/_index/availability_index.parquet
  - gs://gas-fees-central-element-323112/_index/availability_index.parquet (CLEAN — gas_fees snake-only)
  - gs://liquidations-central-element-323112/_index/availability_index.parquet (CLEAN — liquidations base-form)
  - market-tick-data-service/market_tick_data_service/cli/handlers/*_handler.py (per-handler canonical constants)
  - codex/02-data/availability-manifest-and-data-status.md (3K update — canonical type names)
severity: P1 — affects 6 DeFi asset_group manifests' queryability; any downstream filter on one form silently misses ~30-60% of rows
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

### Cross-bucket audit (2026-05-16)

Diagnostic read across 7 DeFi canonical manifests via `pd.read_parquet('gs://<bucket>-{pid}/_index/availability_index.parquet')`
shows vocabulary drift in **6 of 7 buckets**. Both kebab + snake forms coexist in the same `data_type` column of
the same canonical manifest:

| Bucket            | Total rows | Kebab-form rows                  | Snake-form rows               | Drift? |
| ----------------- | ---------- | -------------------------------- | ----------------------------- | ------ |
| `lending-indices` | 46,020     | `lending-indices` 24,976 (54%)   | `lending_indices` 21,044 (46%) | **YES** |
| `oracle-prices`   | 9,036      | `oracle-prices` 1,926 (21%)      | `oracle_prices` 7,110 (79%)    | **YES** |
| `lst-rates`       | 18,180     | `lst-rates` 1,560 (9%)           | `lst_rates` 16,620 (91%)       | **YES** |
| `perp-funding`    | 6,052      | `perp-funding` 3,298 (54%)       | `perp_funding` 2,754 (46%)     | **YES** |
| `dex-swaps`       | 46,491     | `dex-swaps` 28,171 (61%)         | `dex_swaps` 18,320 (39%)       | **YES** |
| `dex-pools`       | 75,983     | `dex-pools` 55,854 (73%)         | `dex_pools` 20,129 (27%)       | **YES** |
| `gas-fees`        | 16,393     | —                                | `gas_fees` 16,393 (100%)       | clean  |
| `liquidations`    | 38,134     | (single form: `liquidations`)    | (no `_` variant)               | clean  |

**6 of 7 DeFi canonical manifests carry vocabulary drift.** Total affected rows: 25,976+1,926+1,560+3,298+28,171+55,854
= **~116,000 legacy kebab-form rows** that any naive snake-only query would silently miss.

### Per-handler canonical constants (workspace truth — should be the ONLY emission)

Per `market-tick-data-service/.../cli/handlers/*_handler.py` line annotations:
- `lending_indices_handler.py`: `_LENDING_INDICES_DATA_TYPE = "lending_indices"` (snake)
- `oracle_prices_handler.py`: similar snake constant
- `lst_rates_handler.py`: writes `lst_rates` (snake)
- `perp_funding_handler.py`: writes `perp_funding` (snake)
- `dex_swaps_handler.py` + `dex_pools_handler.py`: write snake forms

The on-disk hive vocabulary (`gs://<bucket>/.../data_type=<form>/...`) is consistent snake-only across all buckets,
confirmed via `gsutil ls`. **Only the manifest `data_type` column carries the kebab legacy.**

### lending-indices detail (initial finding)

| `data_type` value  | Row count  |
| ------------------ | ---------- |
| `lending-indices`  | **24,976** |
| `lending_indices`  | **21,044** |
| **Total**          | 46,020     |

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

## Why this drift exists (root cause CONFIRMED 2026-05-16)

`written_at` distribution by `data_type` (groupby diagnostic 2026-05-16):

| data_type         | written_at min                     | rows   | data-date range           |
| ----------------- | ---------------------------------- | ------ | ------------------------- |
| `lending-indices` | 2026-04-13T15:12:45 UTC            | 24,976 | 2022-01-01 → **2026-04-10** |
| `lending_indices` | 2026-04-23T10:33:29 UTC            | 21,044 | 2022-01-01 → 2026-05-13     |

**Verdict**: ✅ **(a) Legacy emission from pre-2026-04-23 handler revision**. The kebab-form rows stopped being
emitted on 2026-04-23 (when snake became canonical). The 24,976 kebab rows are static legacy entries that were
never canonicalised. Current production emission is snake-only. Capture-status sample shows kebab rows are
predominantly `captured` (real data on-disk) while early snake rows are `empty_confirmed` — likely because of a
re-coverage of older dates with the new vocabulary.

No active drift (nothing currently emitting kebab). One-shot migration is safe + correct.

## Recommended decision

**Option A (recommended — workspace-wide canonicalisation)**: declare snake-form canonical for ALL DeFi data_type
columns per CLAUDE.md § "Asset-group vocabulary" + per-handler constants. Ship a one-shot migration script
`instruments-service/scripts/canonicalize_defi_manifest_data_types_2026_05_16.py` that:

1. For each of the 6 affected buckets, reads `_index/availability_index.parquet`
2. Maps kebab → snake at the column level (closed-set mapping):
   `{"lending-indices": "lending_indices", "oracle-prices": "oracle_prices", "lst-rates": "lst_rates",
   "perp-funding": "perp_funding", "dex-swaps": "dex_swaps", "dex-pools": "dex_pools"}`
3. Writes back via v8-tolerant `df.to_parquet`
4. Idempotent re-runs (no-op when all rows already snake)
5. `--dry-run` (default) / `--apply` / `--bucket` (filter to subset) / `--confirm` (safety belt)

This is ~1-1.5 hour work + tests; eliminates the silent-query-miss bug class workspace-wide for DeFi. 6 buckets +
~116,000 rows total to flip. Post-migration, downstream services + the 3-LENDING.5 reconciler don't need defensive
both-form handling.

**Option B**: extend the 3-LENDING.5 reconciler (and every downstream consumer) to accept both forms in their
`data_type` filter and leave the drift in place. Defers canonicalisation to post-cutover. Higher long-term cost
(every new consumer must remember to accept both forms).

**Option C**: investigate handler-by-handler root cause first — confirm each handler's canonical-constant emits only
snake currently, then declare migration safe.

Root cause already confirmed for lending-indices: kebab rows stopped 2026-04-23. Spot-check the other 5 buckets'
`written_at` distributions to confirm same pattern (all-legacy, no active drift) before running migration.

## Suggested owner

ikenna-slot-2 — pending operator nod on Option A vs B vs C. Migration script is straightforward; can ship in next
slot-2 session if Option A acked.

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
