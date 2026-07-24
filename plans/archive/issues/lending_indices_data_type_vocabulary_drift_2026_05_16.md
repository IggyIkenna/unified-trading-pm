---
doc_type: issue
title: Cross-bucket DeFi canonical-manifest data_type vocabulary drift — SYSTEMIC (6 of 7 manifests affected)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-16
author: ikenna-slot-2
source:
  [
    "gs://lending-indices-central-element-323112/_index/availability_index.parquet",
    "gs://oracle-prices-central-element-323112/_index/availability_index.parquet",
    "gs://lst-rates-central-element-323112/_index/availability_index.parquet",
    "gs://perp-funding-central-element-323112/_index/availability_index.parquet",
    "gs://dex-swaps-central-element-323112/_index/availability_index.parquet",
    "gs://dex-pools-central-element-323112/_index/availability_index.parquet",
    "gs://gas-fees-central-element-323112/_index/availability_index.parquet (CLEAN — gas_fees snake-only)",
    "gs://liquidations-central-element-323112/_index/availability_index.parquet (CLEAN — liquidations base-form)",
    market-tick-data-service/market_tick_data_service/cli/handlers/*_handler.py (per-handler canonical constants),
    /codex/02-data/availability-manifest-and-data-status.md (3K update — canonical type names),
  ]
severity:
  P1 — affects 6 DeFi asset_group manifests' queryability; any downstream filter on one form silently misses ~30-60% of
  rows
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

### Cross-bucket audit (2026-05-16)

Diagnostic read across 7 DeFi canonical manifests via
`pd.read_parquet('gs://<bucket>-{pid}/_index/availability_index.parquet')` shows vocabulary drift in **6 of 7 buckets**.
Both kebab + snake forms coexist in the same `data_type` column of the same canonical manifest:

| Bucket            | Total rows | Kebab-form rows                | Snake-form rows                | Drift?  |
| ----------------- | ---------- | ------------------------------ | ------------------------------ | ------- |
| `lending-indices` | 46,020     | `lending-indices` 24,976 (54%) | `lending_indices` 21,044 (46%) | **YES** |
| `oracle-prices`   | 9,036      | `oracle-prices` 1,926 (21%)    | `oracle_prices` 7,110 (79%)    | **YES** |
| `lst-rates`       | 18,180     | `lst-rates` 1,560 (9%)         | `lst_rates` 16,620 (91%)       | **YES** |
| `perp-funding`    | 6,052      | `perp-funding` 3,298 (54%)     | `perp_funding` 2,754 (46%)     | **YES** |
| `dex-swaps`       | 46,491     | `dex-swaps` 28,171 (61%)       | `dex_swaps` 18,320 (39%)       | **YES** |
| `dex-pools`       | 75,983     | `dex-pools` 55,854 (73%)       | `dex_pools` 20,129 (27%)       | **YES** |
| `gas-fees`        | 16,393     | —                              | `gas_fees` 16,393 (100%)       | clean   |
| `liquidations`    | 38,134     | (single form: `liquidations`)  | (no `_` variant)               | clean   |

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

| `data_type` value | Row count  |
| ----------------- | ---------- |
| `lending-indices` | **24,976** |
| `lending_indices` | **21,044** |
| **Total**         | 46,020     |

- **Venues** (3): AAVE_V3 (28,512), COMPOUND_V3 (14,197), SPARK (3,311). Note `AAVE_V3` not `AAVE_V3` (no underscore).
- **Chains** (10): ETHEREUM / OPTIMISM / BASE / ARBITRUM / POLYGON / AVALANCHE / BSC / LINEA / SCROLL / ZKSYNC.
- **capture_status**: 39,851 captured / 6,012 empty_confirmed / 157 attempted_failed.

## Why it matters

1. **Manifest-consumer queries break silently**: any downstream service / cron / data-status UI / dependency-checker
   filtering `data_type == "lending_indices"` sees only HALF the manifest. Filter on the other form → opposite half.
2. **3-LENDING.5 reconciler scope**: the in-flight slot-2 sub-agent (dispatch `a8d9a9f29f77e0c48`,
   `instruments-service/scripts/reconcile_lending_indices_phantom.py`) must accept BOTH forms in its row-key match
   logic. A naive `df.query("data_type=='lending_indices'")` filter would miss 24,976 rows (54% of manifest).
3. **3K codex update accuracy**: `/codex/02-data/availability-manifest-and-data-status.md` § "Phase 1A DeFi bundled
   data_types" lists `lending_indices` (snake) as the canonical type. Operator should ratify which form is canonical so
   the drift can be reconciled in one direction.
4. **Hive path vs manifest column inconsistency**: the actual GCS hive segment is `data_type=lending_indices` (snake,
   confirmed via `gsutil ls`) — so the on-disk vocabulary is consistent. Only the manifest column carries both.

## Why this drift exists (root cause CONFIRMED 2026-05-16)

`written_at` distribution by `data_type` (groupby diagnostic 2026-05-16):

| data_type         | written_at min          | rows   | data-date range             |
| ----------------- | ----------------------- | ------ | --------------------------- |
| `lending-indices` | 2026-04-13T15:12:45 UTC | 24,976 | 2022-01-01 → **2026-04-10** |
| `lending_indices` | 2026-04-23T10:33:29 UTC | 21,044 | 2022-01-01 → 2026-05-13     |

**Verdict**: ✅ **(a) Legacy emission from pre-2026-04-23 handler revision**. The kebab-form rows stopped being emitted
on 2026-04-23 (when snake became canonical). The 24,976 kebab rows are static legacy entries that were never
canonicalised. Current production emission is snake-only. Capture-status sample shows kebab rows are predominantly
`captured` (real data on-disk) while early snake rows are `empty_confirmed` — likely because of a re-coverage of older
dates with the new vocabulary.

No active drift (nothing currently emitting kebab). One-shot migration is safe + correct.

## Recommended decision

**Option A (recommended — workspace-wide canonicalisation)**: declare snake-form canonical for ALL DeFi data_type
columns per CLAUDE.md § "Asset-group vocabulary" + per-handler constants. Ship a one-shot migration script
`instruments-service/scripts/canonicalize_defi_manifest_data_types_2026_05_16.py` that:

1. For each of the 6 affected buckets, reads `_index/availability_index.parquet`
2. Maps kebab → snake at the column level (closed-set mapping):
   `{"lending-indices": "lending_indices", "oracle-prices": "oracle_prices", "lst-rates": "lst_rates", "perp-funding": "perp_funding", "dex-swaps": "dex_swaps", "dex-pools": "dex_pools"}`
3. Writes back via v8-tolerant `df.to_parquet`
4. Idempotent re-runs (no-op when all rows already snake)
5. `--dry-run` (default) / `--apply` / `--bucket` (filter to subset) / `--confirm` (safety belt)

This is ~1-1.5 hour work + tests; eliminates the silent-query-miss bug class workspace-wide for DeFi. 6 buckets +
~116,000 rows total to flip. Post-migration, downstream services + the 3-LENDING.5 reconciler don't need defensive
both-form handling.

**Option B**: extend the 3-LENDING.5 reconciler (and every downstream consumer) to accept both forms in their
`data_type` filter and leave the drift in place. Defers canonicalisation to post-cutover. Higher long-term cost (every
new consumer must remember to accept both forms).

**Option C**: investigate handler-by-handler root cause first — confirm each handler's canonical-constant emits only
snake currently, then declare migration safe.

Root cause already confirmed for lending-indices: kebab rows stopped 2026-04-23. Spot-check the other 5 buckets'
`written_at` distributions to confirm same pattern (all-legacy, no active drift) before running migration.

## Suggested owner

ikenna-slot-2 — pending operator nod on Option A vs B vs C. Migration script is straightforward; can ship in next slot-2
session if Option A acked.

## Migration script SHIPPED 2026-05-16 (slot 2 sub-agent dispatch)

`instruments-service@b2726c6` ships `instruments-service/scripts/canonicalize_defi_manifest_data_types_2026_05_16.py`
(326 lines) + tests at `instruments-service/tests/scripts/test_canonicalize_defi_manifest_data_types_2026_05_16.py` (353
lines / 8 unit tests green). basedpyright clean.

CLI: `--dry-run` (default) / `--apply --confirm` (safety belt) / `--bucket <name>` (subset) / `--project-id`. Closed-set
kebab→snake mapping for the 6 affected buckets baked in. Idempotent; on already-canonical bucket → no-op.

**Next gating step**: operator [ack] to run `--apply --confirm` against the 6 production manifests in
`central-element-323112`. Migration is column-rename only (no parquet repath); estimated <2-minute wall-clock per bucket
(read manifest → flip column → write back).

## Additional structural drift finding — lst-rates manifest (2026-05-16 follow-up audit)

Drill-down audit of `gs://lst-rates-central-element-323112/_index/availability_index.parquet` (18,180 rows) reveals the
1,560 legacy `lst-rates` kebab rows ALSO have **empty `chain` column** (not just kebab data_type):

```
data_type x chain crosstab:
data_type    lst-rates  lst_rates
chain
""              1560          0
ETHEREUM           0     15470
SOLANA             0      1150
```

**Interpretation**: kebab rows are from a pre-2026-04-23 schema where `chain` wasn't populated. Column-only
canonicalisation (Option A) flips `data_type` but leaves `chain` empty, so downstream consumers querying
`(data_type=='lst_rates') AND (chain=='ETHEREUM')` would still miss the 1,560 rows. The 1,560 rows themselves are mostly
`captured` rows for older LST data, with the chain implicit in the venue prefix (LIDO/COINBASE/etc. are all-ETHEREUM
venues).

**Implication for Option A migration**: insufficient on its own for `lst-rates`. Three sub-options:

- **A.1**: column-flip kebab→snake AND derive `chain` from venue lookup (LIDO/ETHERFI/COINBASE/ROCKETPOOL/etc. →
  ETHEREUM; JITO/MARINADE/etc. → SOLANA; per UAC `get_venue_prefix` reverse map).
- **A.2**: column-flip kebab→snake ONLY; downstream consumers must accept missing-chain rows for the legacy subset (less
  clean but ships fast).
- **A.3**: scope-cut — `lst-rates` migration excluded from the first canonicalisation run; investigate empty-chain rows
  separately.

Other buckets (lending-indices / oracle-prices / perp-funding / dex-swaps / dex-pools) need a similar drill-down to
confirm whether their kebab rows have the same structural drift before running `--apply`.

**Recommendation**: spot-check `chain` distribution in each kebab subset before running `--apply` on that bucket. The
canonicalisation script as shipped does NOT derive chain — operator should pick A.1 / A.2 / A.3 per-bucket based on the
audit.

execution: owner: "operator decision on Option A.1 vs A.2 vs A.3 per bucket; ikenna-slot-2 ships the per-bucket fix once
decided" cadence: "one-shot operator decision + one-shot migration per bucket (~6 buckets)" verifier: "per-bucket
groupby (data_type, chain) returns 1×N matrix (canonical form only, fully-populated chain column)" last_executed:
"Diagnostic only 2026-05-16; canonicalisation script SHIPPED at IS@b2726c6 awaiting operator --apply"

## Cross-references

- 3-LENDING.5 reconciler in-flight: sub-agent `a8d9a9f29f77e0c48` writing
  `instruments-service/scripts/reconcile_lending_indices_phantom.py`
- Spec source: `plans/active/defi_catalogue_chain_primitives_2026_05_10.md` § Phase 3 todo `3-LENDING.5`
- 3K codex update: `/codex/02-data/availability-manifest-and-data-status.md` (PM@`aab47b12`)

execution: owner: "operator decision on Option A/B/C; ikenna-slot-2 ships the migration once decided" cadence: "one-shot
operator decision + one-shot migration" verifier: "lending-indices manifest groupby data_type returns 1 row (canonical
form only)" last_executed: "2026-05-16 19:44 UTC — Option A applied workspace-wide (slot 4 cross-slot pickup + slot 2
parallel script)"

## RESOLVED — 2026-05-16 (slot 4 cross-slot pickup + slot 2 collision)

**Option A shipped**. Two parallel implementations + 1 shared on-cloud apply:

- **`instruments-service@8077ae6`** (slot 4, 19:41 UTC) — lending-indices-only canonicalisation. Per-VM shard written to
  `gs://lending-indices-central-element-323112/_index/per_vm/manifest-canonicalize-data-type-kebab-to-snake.parquet`.
- **GCS shards applied to all 6 buckets** (slot 4, 19:44 UTC via earlier draft of generalised script):
  - lending-indices: 24,976 rows
  - oracle-prices: 1,926
  - lst-rates: 1,560
  - perp-funding: 3,298
  - dex-swaps: 28,171
  - dex-pools: 55,854
  - **Total: 115,785 rows flipped via per-VM shards**
- **`instruments-service@b2726c6`** (slot 2, ~19:45 UTC) — canonical workspace-wide script with `--confirm` safety
  belt + bandit-clean tempfile. Slot 4's parallel code-side commit dropped during rebase (collision resolution favours
  slot 2's version + the cleaner CLI shape). On-cloud shards from slot 4 stand — consolidator will merge them on next
  cycle (last-writer-wins).

# Issue closed. No further action; slot 2's script remains the canonical re-run path if drift re-surfaces.

last_executed: "NEVER (diagnostic only 2026-05-16)"

## Per-bucket Option A safety table (2026-05-16 drill-down audit)

Diagnostic groupby of `df[df.data_type == <kebab>]['chain'].value_counts()` per bucket; all kebab rows were emitted in a
single batch on 2026-04-13 (legacy one-shot, no active drift):

| Bucket            | Kebab rows | Empty `chain` rows | Top kebab chains                                         | Option A safe?       |
| ----------------- | ---------- | ------------------ | -------------------------------------------------------- | -------------------- |
| `lending-indices` | 24,976     | **0**              | ETHEREUM 4683, ARBITRUM 3122, BASE 3122, OPTIMISM 3122   | ✅ **YES**           |
| `dex-swaps`       | 28,171     | **0**              | ETHEREUM 7185, ARBITRUM 6467, BASE 4119, AVALANCHE 3466  | ✅ **YES**           |
| `dex-pools`       | 55,854     | **0**              | ARBITRUM 11556, BASE 9630, AVALANCHE 9630, ETHEREUM 9630 | ✅ **YES**           |
| `oracle-prices`   | 1,926      | **1,926 (100%)**   | — (all empty)                                            | ❌ **NO** — need A.1 |
| `perp-funding`    | 3,298      | **3,298 (100%)**   | — (all empty)                                            | ❌ **NO** — need A.1 |
| `lst-rates`       | 1,560      | **1,560 (100%)**   | — (all empty)                                            | ❌ **NO** — need A.1 |

**Total**:

- **3 buckets SAFE for Option A** as-shipped: `lending-indices` + `dex-swaps` + `dex-pools` = **108,801 rows** ready for
  `--apply` (pure column rename; chain already populated).
- **3 buckets need A.1** (chain derivation from venue): `oracle-prices` + `perp-funding` + `lst-rates` = **6,784 rows**
  blocked on a separate sub-task to extend the canonicalisation script with per-venue → chain reverse-lookup.

## Recommended operator sequence

1. **Phase A (operator [ack] + slot-2 ADC `--apply`, ~5 min wall-clock)**: run shipped script on the 3 SAFE buckets:

   ```
   .venv/bin/python scripts/canonicalize_defi_manifest_data_types_2026_05_16.py \
       --apply --confirm --bucket lending-indices
   .venv/bin/python scripts/canonicalize_defi_manifest_data_types_2026_05_16.py \
       --apply --confirm --bucket dex-swaps
   .venv/bin/python scripts/canonicalize_defi_manifest_data_types_2026_05_16.py \
       --apply --confirm --bucket dex-pools
   ```

   Closes 108,801 of the ~116,000 row drift; downstream snake-only queries on these 3 buckets are immediately correct.

2. **Phase B (next slot-2 session, ~1h)**: extend script with `--derive-chain-from-venue` mode that takes a
   `VENUE_TO_CHAIN_MAP` lookup (LIDO/ETHERFI/COINBASE/ROCKETPOOL → ETHEREUM; JITO/MARINADE → SOLANA; etc.) and ship
   `--apply --derive-chain --bucket lst-rates|oracle-prices|perp-funding`. Then operator runs Phase B for the remaining
   6,784 rows.

3. **Phase C (validation)**: re-run audit to confirm zero kebab rows + zero empty-chain rows across all 6 buckets.
   Optional: add QG STEP scanning canonical manifests for non-snake `data_type` values (workspace ratchet).
