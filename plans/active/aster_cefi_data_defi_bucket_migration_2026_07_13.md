---
doc_type: plan
title: Migrate ASTER CeFi-labeled tick data out of the DeFi bucket into canonical CeFi location
summary: >-
  ASTER's asset_group=cefi derivative_ticker data (a legitimate hybrid CeFi/DeFi venue, same VENUE_TO_ASSET_GROUP=cefi
  classification as HYPERLIQUID) has been landing in the DeFi bucket instead of the CeFi bucket since 2023-11 —
  ~100-120K objects, ~65-70% with no canonical twin anywhere. Migrate with canonical InstrumentKey renaming, fix the
  write-path bucket-selection bug, verify parity, only then delete the DeFi-bucket-resident originals as a separate
  gated step.
status: active
nature: process
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [migration, bucket-placement, data-correctness, canonicalisation, cefi, defi, aster]
related:
  [
    bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md,
    defi_manifest_canonicalisation_2026_06_01.md,
    cefi_manifest_canonicalisation_2026_06_01.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
source:
  [
    "BQ external-table investigation 2026-07-13 (deployment-service bigquery_feature_external_tables.tf fix session) —
    discovered while diagnosing why defi__dex_swaps was unqueryable; confirmed via a dedicated classification sub-agent
    (object-count + symbol-name diffing across 20+ sample days, codebase grep of VENUE_TO_ASSET_GROUP).",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
---

# Migrate ASTER CeFi-labeled tick data out of the DeFi bucket

## Finding (2026-07-13, discovered while fixing `deployment-service` `bigquery_feature_external_tables.tf`)

`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/` contains
`pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/instrument_type=perpetual/data_type=derivative_ticker/` data —
~100,000-120,000 parquet objects, `day=2023-11-01` through `day=2026-06-05` (948 day-partitions; `batch_aster`
collection appears to have stopped after 2026-06-05, separate operational finding, see Deferred work below).

**ASTER's `asset_group=cefi` label is correct and intentional** — ASTER is a documented hybrid CeFi/DeFi venue
(`VENUE_TO_ASSET_GROUP == 'cefi'`, same registry entry as HYPERLIQUID:
`instruments-service/instruments_service/engine/orchestrator/writers.py:58`; confirmed Binance-compatible REST API per
UAC `SCHEMA_VERSIONS.md`). **The bug is bucket placement, not labeling**: HYPERLIQUID's cefi-shaped data correctly lands
in the CeFi bucket; ASTER's does not, for a large historical window. Root cause (not yet fixed): whatever batch/backfill
writer produced this data selected the destination bucket by the venue's DeFi/on-chain classification rather than by
each object's own `asset_group=cefi` label, unlike the codebase's standard `resolve_bucket_name(asset_group=...)`
pattern.

**Duplication status varies sharply by period** (confirmed via object-count + symbol-name diffing, 20+ sample days
spanning 2023-2026):

| Period                  | Days | Duplication (CeFi bucket has it too)                                                                                                                                  |
| ----------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2023-11-01 → 2023-12-31 | ~61  | **0%** — zero `batch_aster` data in CeFi bucket before 2024                                                                                                           |
| 2024-01-01 → 2025-06-30 | ~545 | **98-99%** — near-full parity, ~1 symbol/day gap                                                                                                                      |
| 2025-07-01 → 2026-06-05 | ~340 | **2-10%** — CeFi-bucket copy frozen at a ~9-symbol top-liquidity subset while DeFi-bucket copy kept growing with every new ASTER listing (443 symbols/day by 2026-06) |

Weighted estimate: **~65-70% of the ~100-120K objects have no canonical twin anywhere** — this is a majority-unique
dataset, not a redundant copy. Filename convention also differs: DeFi-bucket copy uses bare symbols (`BTCUSDT.parquet`);
CeFi-bucket copy uses canonical InstrumentKey naming (`ASTER:PERPETUAL:BTC-USDT@LIN.parquet`) — the existing
`migrate_onchain_perp_perpetual_canonical_2026_07_08.py` canonical-ID migration only targets
`resolve_bucket_name(asset_group="cefi")`, so it has never discovered or touched this DeFi-bucket-resident copy.

**This blocks** `deployment-service` `bigquery_feature_external_tables.tf`'s `defi__dex_swaps` external table (the mixed
asset_group=cefi/defi shapes under the same wildcarded prefix break BigQuery's uniform hive-partition-depth requirement)
— that plan's split-table workaround is independent of this migration and does not depend on it landing first, but once
this migration completes + the originals are deleted, the `defi__dex_swaps` table's remaining shape count drops from 3
to 2 (still needs the split/legacy-migrated-shape handling separately).

## Codex SSOTs

- `codex/02-data/pipeline-mode-partition.md` (source-aware `pipeline_mode` model)
- `codex/05-infrastructure/gcs-object-operations.md` (`gcs_copy_object`/`gcs_delete_object`, never subprocess
  `gcloud`/`gsutil`)
- `codex/02-data/availability-manifest-and-data-status.md` (manifest rewrite discipline, single-walk rule)

## Phase 1 — Confirm scope + build the migration script (P0)

- [x] ✅ [DATA] P0. Re-verify the full scope with a fresh, complete (not sampled) day-by-day object count + duplication
      check across all 948 `day=`/`pipeline_mode=batch_aster`/`asset_group=cefi` partitions in the DeFi bucket (the
      2026-07-13 finding above is from 20+ sample days, not a full walk) — write the result to
      `_index/audit/aster_cefi_in_defi_bucket_scope_2026_07_1X.parquet` (mirrors the existing
      `_index/audit/legacy_dup_delete_list_defi.parquet` convention). Confirm the 2023-11→2023-12 zero-duplication
      window and the 2025-07→2026-06 low-duplication window precisely (exact day boundaries, not "~"). — **DONE (audit +
      results), slot 14, market-tick-data-service@`c2244d5f`
      (`scripts/audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py`) — committed locally, SHIP BLOCKED as of this
      writing by an unrelated repo-wide QG regression (`migrate_sports_canonical_v9.py` crossed the 900-line ceiling in
      a different slot's commit `13c53dfa`); repo-blocker declared, will land + this SHA note update once the gate is
      green again.** Full 948-day walk (per-day scoped GCS prefix listing, not a whole-bucket scan — completed in ~5s
      via 20-way thread-pool parallelism over `raw_tick_data/by_date/day={D}/pipeline_mode=batch_aster/...`, both
      buckets). Output written to
      `gs://market-data-tick-defi-prd-central-element-323112/_index/audit/aster_cefi_in_defi_bucket_scope_2026_07_13.parquet`
      (115,110 rows, one per DeFi-bucket-resident object, with
      `day`/`defi_object_stem`/`canonical_target`/`duplicated_in_cefi_bucket`). **Exact totals**: 115,110 objects total
      (within the plan's ~100-120K estimate); **71,843 unique / no canonical twin (62.4%)**; 43,267 duplicated (37.6%) —
      refines the plan's "~~65-70%" weighted estimate with the true count. **Exact window boundaries** (refining the
      "~~" estimates above): - Zero-duplication: **2023-11-01 → 2023-12-31 exactly** (61 days) — matches the sampled
      estimate precisely. - Steady high-duplication (~98-99%, sometimes literally 100%): **2024-01-01 → 2025-06-15**. -
      Transition: **2025-06-16 is the first low-duplication day** (drops to 10.8%), with a single one-day reversion back
      to 98.8% on **2025-06-17**, then sustained low duplication from **2025-06-18** onward — this is ~2 weeks EARLIER
      than the plan's "~2025-07-01" estimate. - Low-duplication tail: **2025-06-18 → 2026-06-05** (the corpus's last
      day), steady 4-11% range, growing object count per day as ASTER listed more symbols (matches the "443 symbols/day
      by 2026-06" finding). - **NEW anomaly found**: a 5-day window, **2026-01-01 → 2026-01-05**, shows 100% duplication
      (every DeFi-bucket object that day has a canonical twin in the CeFi bucket) — a sharp, isolated spike inside the
      otherwise-steady low-duplication tail, immediately reverting to ~4.8% on 2026-01-06. Not investigated further (out
      of this todo's scope) — flagging for whoever runs Phase 2's migration script: this 5-day window may need a
      byte-parity check rather than a blind "skip if canonical target exists" (the existing script's idempotency check),
      since a genuine backfill/resync coincidence and a mis-attributed duplicate are hard to distinguish from object
      presence alone.
- [x] ✅ [DATA] P0. Extend `market-tick-data-service/scripts/migrate_onchain_perp_perpetual_canonical_2026_07_08.py` (or
      a new sibling script, if the source-bucket difference makes extension awkward — the existing script only reads
      from `resolve_bucket_name(asset_group="cefi")`) to ALSO source from the DeFi bucket's
      `pipeline_mode=batch_aster/asset_group=cefi/` prefix, applying the SAME canonical
      `ASTER:PERPETUAL:{BASE}-{QUOTE}@LIN.parquet` renaming logic, writing to the CeFi bucket. Idempotent (skip when the
      canonical target already exists in the CeFi bucket AND is byte-identical — do not blindly overwrite the
      ~98-99%-duplicated Jan-2024→Jun-2025 window without a parity check first, since a handful of per-day symbol gaps —
      **DONE, slot 8, `market-tick-data-service@ee343f76`.** Wrote a NEW sibling script
      (`scripts/migrate_aster_cefi_defi_bucket_2026_07_13.py` — the source-bucket difference made in-place extension of
      the existing rename-only script awkward, since it does a same-bucket rename while this needs a cross-bucket copy)
      that DUPLICATES (not imports) the existing script's ASTER canonicalization logic, reads via per-day TARGETED
      prefix listing across the known 948-day range (not a whole-corpus walk), and cross-bucket-copies via
      `gcs_copy_object` (confirmed natively cross-bucket-capable — splits src/dst URIs independently). Idempotency is a
      `(size, crc32c)` parity check, not existence-only — a pre-existing-but-mismatched CeFi-bucket target is logged as
      a conflict and never overwritten, matching the exact "per-day symbol gaps even in the 98-99% window" risk this
      todo flagged. Never deletes the DeFi-bucket source (Phase 4's separate, operator-gated step) and does not touch
      the manifest (Phase 3's separate todo). Smoke-tested in `--dry-run` against real GCS data (2023-11-01→11-03, 234
      objects, correct `ASTER:PERPETUAL:{BASE}-{QUOTE}@LIN` renaming + correct CeFi-bucket path targeting confirmed).
      Did NOT run `--apply` against production data — that is Phase 2's separate, sequenced-after-Phase-1-Todo-1
      execution step, out of this todo's scope. exist even there). DRY-RUN default, `--apply` to mutate — same
      convention as the script it extends.
- [ ] [DATA] P0. Root-cause the write-path bug: find the batch/backfill writer that produced this historical ASTER data
      and determine why it selected the DeFi bucket for cefi-labeled objects (likely a venue-level "primary asset_group"
      bucket selection instead of a per-object `asset_group` field read). Fix it so this does not recur for whatever
      collection job (if any) still runs — cross-reference with the "batch_aster appears to have stopped after
      2026-06-05" finding below; if the writer is confirmed fully decommissioned, this becomes a historical-only fix
      (document why, do not chase a dead code path).

## Phase 2 — Dry-run + apply (P0)

- [ ] [DATA] P0. Run the extended migration script in dry-run across the full 948-day range; verify the planned object
      count matches Phase 1's scope audit; spot-check 10+ planned renames for correctness (base/quote split, `@LIN`
      margin marker) against the existing 2026-07-08 script's validated logic.
- [ ] [DATA] P0. `--apply` the migration, sharded by date range if the full 948-day/100K-object run is too slow for one
      pass (mirrors this workspace's per-VM-shard convention for large migrations — launch on a VM per
      `codex/05-infrastructure/vm-launcher-runbook.md` if a local/interactive run proves too slow; SPOT provisioning per
      the backfill-VM default). No fire-and-forget — verify STARTED + periodic progress + terminal state per the
      VM-launcher runbook if dispatched to a VM.
- [ ] [DATA] P0. Post-apply verification: re-run the Phase 1 scope audit against the CeFi bucket, confirm 0 objects
      remain unmigrated (excluding any genuinely-still-running collection window) and spot-check row/byte parity (not
      just object presence) on 20+ migrated objects across the three duplication-period bands identified above.

## Phase 3 — Manifest + downstream (P1)

- [ ] [DATA] P1. Rewrite/extend the canonical CeFi `_index/availability_index.parquet` manifest rows for the
      newly-migrated ASTER objects (mirrors the 2026-07-08 script's manifest-rewrite step) — dedup any rows that
      collapse to the same canonical key, keeping the best `capture_status`.
- [ ] [DATA] P1. Confirm downstream readers (MDPS candle processing, features-service, deployment-api data-status
      drilldowns) correctly pick up the migrated data from its new canonical CeFi-bucket location — spot-check one
      drilldown query for an ASTER instrument/day that was previously only in the DeFi bucket.

## Phase 4 — Cleanup (gated, separate from migration — P1)

- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION** — only after Phase 2's parity verification is fully green: delete the
      DeFi-bucket-resident ASTER `asset_group=cefi` originals (version-aware, matching the same rigor as
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`'s Phase-7 decommission gate — snapshot first,
      verify canonical ≥ legacy via live-object counts, never a naive `ls`). This is explicitly NOT bundled with the
      migration apply step — do not delete until an operator confirms the parity verification evidence.

## Deferred work after 2026-07-13 (found this session, out of THIS plan's scope)

| Item                                                                | State                                                                                                                         | Next action                                                                                                                  |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `batch_aster` collection stopped after 2026-06-05                   | Found, unexplained                                                                                                            | Separate finding — confirm whether this is an intentional decommission or a silent collector failure; not this plan's scope. |
| BYBIT `futures_chain` write-shape bug (flat glued-symbol files)     | Found + partially fixed in code 2026-07-09, historical data not backfilled                                                    | Tracked separately — `plans/active/issues/bybit_futures_chain_write_shape_2026_07_13.md`.                                    |
| Legacy `ticks_migrated_*` shallow shape in DeFi bucket (5,332 objs) | Already tracked pre-existing — codex axis-7, archived plan F16/F29, 2026-06-18 delete-list audit MIGRATE-FIRST classification | No new work needed — do NOT re-scope here, it already has an owner.                                                          |
| `defi__dex_swaps` BQ external table split-table design              | Separate, independent fix in `deployment-service`                                                                             | Tracked in this session's direct commit to `bigquery_feature_external_tables.tf` — does not block or depend on this plan.    |
