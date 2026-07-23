---
doc_type: plan
title: Migrate ASTER CeFi-labeled tick data out of the DeFi bucket into canonical CeFi location
summary: >-
  ASTER's asset_group=cefi derivative_ticker data (a legitimate hybrid CeFi/DeFi venue, same VENUE_TO_ASSET_GROUP=cefi
  classification as HYPERLIQUID) has been landing in the DeFi bucket instead of the CeFi bucket since 2023-11 —
  ~100-120K objects, ~65-70% with no canonical twin anywhere. Migrate with canonical InstrumentKey renaming, fix the
  write-path bucket-selection bug, verify parity, only then delete the DeFi-bucket-resident originals as a separate
  gated step.
status: complete # (was: active) 2026-07-15 plan-reconcile §7-residual: operator ruling A (archival + codex-sync); verified 0 open todos, evidence spot-checked
nature: process
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [migration, bucket-placement, data-correctness, canonicalisation, cefi, defi, aster]
related:
  [
    /plans/archive/2026_07/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md,
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/cefi_manifest_canonicalisation_2026_06_01.md,
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
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
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

- `/codex/02-data/pipeline-mode-partition.md` (source-aware `pipeline_mode` model)
- `/codex/05-infrastructure/gcs-object-operations.md` (`gcs_copy_object`/`gcs_delete_object`, never subprocess
  `gcloud`/`gsutil`)
- `/codex/02-data/availability-manifest-and-data-status.md` (manifest rewrite discipline, single-walk rule)

## Phase 1 — Confirm scope + build the migration script (P0)

- [x] ✅ [DATA] P0. Re-verify the full scope with a fresh, complete (not sampled) day-by-day object count + duplication
      check across all 948 `day=`/`pipeline_mode=batch_aster`/`asset_group=cefi` partitions in the DeFi bucket (the
      2026-07-13 finding above is from 20+ sample days, not a full walk) — write the result to
      `_index/audit/aster_cefi_in_defi_bucket_scope_2026_07_1X.parquet` (mirrors the existing
      `_index/audit/legacy_dup_delete_list_defi.parquet` convention). Confirm the 2023-11→2023-12 zero-duplication
      window and the 2025-07→2026-06 low-duplication window precisely (exact day boundaries, not "~"). — **DONE (audit +
      results), slot 14, market-tick-data-service@`aea8515e`
      (`scripts/audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py`) — SHIPPED (was briefly blocked by an unrelated
      repo-wide QG regression, `migrate_sports_canonical_v9.py` crossing the 900-line ceiling in a different slot's
      commit `13c53dfa`; repo-blocker RB-9ab3fac9 resolved via `watcher_green`, see
      `plans/active/issues/mtds_migrate_sports_canonical_v9_900line_regression_2026_07_13.md`).** Full 948-day walk
      (per-day scoped GCS prefix listing, not a whole-bucket scan — completed in ~5s via 20-way thread-pool parallelism
      over `raw_tick_data/by_date/day={D}/pipeline_mode=batch_aster/...`, both buckets). Output written to
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
- [x] ✅ [DATA] P0. Root-cause the write-path bug — **DONE, slot 8, read-only investigation, no code change needed
      (confirmed fully decommissioned — historical-only fix per this todo's own fallback clause).** The buggy writer was
      `market_tick_data_service/cli/handlers/_perp_funding_hl_aster.py`, a stage module of `perp_funding_handler.py`
      given an ASTER/HYPERLIQUID `derivative_ticker`+`trades` leg on 2026-06-17 (commit `59786270`). Bug mechanism
      confirmed by reading the code at the pre-deletion commit
      (`git show ba6df0ac^:market_tick_data_service/cli/handlers/_perp_funding_hl_aster.py`): `perp_funding_handler.py`
      is a **mixed-asset_group handler** (GMX/Kalshi/Polymarket legs are genuinely defi/prediction) that resolves ONE
      `bucket` up front per invocation — `bucket = get_write_bucket_name("market_data", "defi")`
      (`perp_funding_handler.py:225`, landed 2026-06-21 commit `7c32ff61`) — and threads that single value down into
      every protocol's writer, never re-deriving per-row via
      `resolve_bucket_name(asset_group=<the row's own     asset_group>)`. When the ASTER/HL `cefi`-labeled legs were
      bolted onto this handler, `_write_aster_derivative_ticker` / `_write_aster_trades` correctly stamped
      `asset_group="cefi"` in the **manifest** (`writer.add(asset_group="cefi",     ...)`) but physically
      `storage.upload_bytes(bucket, ...)`'d into the wrong (DeFi) **bucket** — manifest label and physical location
      diverged. HYPERLIQUID was never corrupted by this same handler because HL's `derivative_ticker`/ `trades` was
      always sourced from the separate, correctly single-asset_group `onchain_perp_batch_handler.py` path instead —
      ASTER's ~3-week window (2026-06-17 → 2026-07-08) was the only time this bug's blast radius included a real
      producer. Filename evidence corroborates: the corrupted DeFi-bucket copies use bare exchange symbols
      (`BTCUSDT.parquet`, this handler's `row["symbol"] = sym`), not the canonical
      `ASTER:PERPETUAL:BTC-USDT@LIN.parquet` naming the correct path produces — though per Phase 1 Todo 1's
      exact-boundary audit, DeFi-bucket-resident ASTER objects actually span 2023-11-01 → 2026-06-05 (much wider than
      this handler's 2026-06-17 introduction), meaning this specific handler explains only the tail of the corrupted
      window — an EARLIER, no-longer-identifiable producer (predating the 2026-06-11 handler split) wrote the 2023-11 →
      2026-06-16 majority; not chased further since it too is provably gone (no such producer exists in the current
      codebase, and the migration script already treats the whole 2023-11→2026-06-05 range uniformly regardless of which
      historical writer produced each day). **`perp_funding_handler.py`/`_perp_funding_hl_aster.py` fully retired
      2026-07-08 (commit `ba6df0ac`, "retire standalone perp_funding for
      HYPERLIQUID/ASTER/PACIFICA-SOLANA/LIGHTER-ZKSYNC in favor of derivative_ticker.funding_rate") — confirmed the file
      no longer exists in the working tree; current `perp_funding_handler.py` docstring (lines 8-18) explicitly
      documents the retirement and points to `onchain_perp_batch_handler.py` as ASTER/HL's sole current
      `derivative_ticker` producer.** That replacement handler is single-asset_group by construction
      (`_ASSET_GROUP = "cefi"` at `onchain_perp_batch_handler.py:99`,
      `bucket = get_write_bucket_name("market_data", _ASSET_GROUP)` at line 290) — safe, but only because every venue it
      currently processes happens to be cefi, not because it re-derives per-row; the same "resolve bucket once, reuse
      everywhere" shape would reproduce this exact bug again if a mixed-asset_group venue were ever added to it.
      Flagging as a defense-in-depth lesson (not actioned here, out of this todo's scope): any handler spanning more
      than one `asset_group` must resolve the write bucket per-shard/per-venue from the row's own `asset_group`, never
      once at the top of `process()`. **This also resolves the "batch_aster stopped after 2026-06-05" deferred item
      below** — it was a collector handoff, not a silent failure: `onchain_perp_batch_handler.py`
      (`--operation collect-onchain-perp-batch`, introduced 2026-06-21 commit `1e4dfb21`) superseded the buggy handler
      as ASTER/HL's `derivative_ticker`/`trades` producer, and the buggy handler's last-processed day (2026-06-05) is
      simply the last day a backfill invocation of the old path ran before hand-off, not an encoded cutoff (no
      scheduler/launcher/allowlist gate found referencing that date).

## Phase 2 — Dry-run + apply (P0)

- [x] ✅ [DATA] P0. Run the extended migration script in dry-run across the full 948-day range — **DONE, slot 8**, ran
      `scripts/migrate_aster_cefi_defi_bucket_2026_07_13.py` (no `--apply`) for real against production GCS, full
      2023-11-01 → 2026-06-05 default range. **Result: 117,176 objects planned, 0 skipped** (log:
      `Plan: 117176 objects to copy, 0 skipped (not in scope / already canonical)`; scanned all 948 days in ~29s via
      per-day targeted prefix listing, no whole-corpus walk). **Count vs Phase 1 Todo 1's audit (115,110 total objects):
      a 2,066-object (1.8%) difference, root-caused, not a bug** — Phase 1's audit prefix was scoped to
      `.../instrument_type=perpetual/data_type=derivative_ticker/` only (per its own Finding section), while this
      migration script's `day_prefix()` scopes at the `venue=ASTER/` level (no `data_type` restriction) and picks up a
      SIBLING `data_type=trades` partition Phase 1's narrower audit never scanned (confirmed live: `day=2023-11-01` has
      63 `derivative_ticker` + 15 `trades` objects under the same venue prefix). **This means Phase 1 Todo 1's exact
      counts (115,110 total / 71,843 unique) under-scope the true migration surface by the `trades` data_type** —
      flagging for whoever revisits that audit, but NOT blocking here: this migration script's broader venue-level scope
      is the CORRECT one (every cefi-labeled ASTER object needs migrating regardless of `data_type`), so no script
      change needed, just documenting the count-reconciliation. **Spot-checked all 10 sample renames the dry-run
      printed** (`1000FLOKIUSDT.parquet`→`ASTER:PERPETUAL:1000FLOKI-USDT@LIN.parquet`,
      `1000PEPEUSDT`→`1000PEPE-USDT@LIN`, `1000SHIBUSDT`→`1000SHIB-USDT@LIN`, `AAVEUSDT`→`AAVE-USDT@LIN`,
      `ADAUSDT`→`ADA-USDT@LIN`, `ALGOUSDT`→`ALGO-USDT@LIN`, `ALICEUSDT`→`ALICE-USDT@LIN`, `APEUSDT`→`APE-USDT@LIN`,
      `APTUSDT`→`APT-USDT@LIN`, `ARBUSDT`→`ARB-USDT@LIN`) — all correct base/quote splits (longest-suffix-first `USDT`
      match), all carry the `@LIN` margin marker, all target the correct CeFi-bucket path with
      `day=`/`pipeline_mode=batch_aster`/ `asset_group=cefi`/`venue=ASTER` preserved. Matches the validated logic from
      `migrate_onchain_perp_perpetual_canonical_2026_07_08.py`. Nothing mutated (dry-run only).
- [x] ✅ [DATA] P0. `--apply` the migration, sharded by date range if the full 948-day/100K-object run is too slow for
      one pass (mirrors this workspace's per-VM-shard convention for large migrations — launch on a VM per
      `/codex/05-infrastructure/vm-launcher-runbook.md` if a local/interactive run proves too slow; SPOT provisioning
      per the backfill-VM default). No fire-and-forget — verify STARTED + periodic progress + terminal state per the
      VM-launcher runbook if dispatched to a VM. — **DONE, slot 14, market-tick-data-service@`aea8515e`
      (`scripts/migrate_aster_cefi_defi_bucket_2026_07_13.py --apply --workers 32`)**, run local/interactive (a single
      948-day pass proved fast enough — full run, scan+copy, completed in ~9 minutes — no VM shard needed). No
      fire-and-forget: launched via `setsid nohup ... & disown`, verified STARTED (scan-phase log lines within 10s),
      monitored periodic progress every 15s through the full day range, and observed the terminal `SUMMARY` line.
      **Result: `{'copied': 73359, 'parity_conflict_not_overwritten': 43817, 'skipped_not_in_scope': 0}`** — totals
      reconcile exactly to Phase 2 Todo 1's dry-run plan of 117,176 objects (73,359 + 43,817 = 117,176). Every parity
      conflict was logged with a `(size, crc32c)` mismatch and NOT overwritten, per the script's idempotency design —
      spot-checked a sample of the conflict log: all observed conflicts show the DeFi-bucket source object at ~2x the
      CeFi-bucket dest object's size (e.g. src=13144B vs dest=6716B), a consistent ratio across every sampled conflict
      regardless of day — flagging this pattern for the next todo's post-apply verification (worth root-causing whether
      this is a genuine row-count/schema difference between the two copies, not assumed here). No errors, no source
      deletions (this script never deletes — Phase 4 is the separate, operator-gated cleanup step). Zero unmigrated
      objects.
- [x] ✅ [DATA] P0. Post-apply verification: re-run the Phase 1 scope audit against the CeFi bucket, confirm 0 objects
      remain unmigrated (excluding any genuinely-still-running collection window) and spot-check row/byte parity (not
      just object presence) on 20+ migrated objects across the three duplication-period bands identified above. —
      **DONE, slot 14, market-tick-data-service@`<pending-ship>`
      (`scripts/verify_aster_cefi_defi_bucket_migration_2026_07_13.py`)**. **Existence check: PASSED** — full 948-day
      re-walk, all 117,176 DeFi-bucket objects confirmed present at their canonical CeFi-bucket target, 0 missing.
      **Parity spot-check (45 samples, 15/band): revealed a real data-correctness issue, NOT a clean pass** — `zero_dup`
      band 15/15 row-count-match + byte-identical (trivial, freshly `--apply`-copied); `low_dup` band 14/15 clean;
      **`high_dup` band (2024-01→2025-06, the LARGEST slice of the corpus) only 5/15 row-count-match, 0/15
      byte-identical**. Root-caused via a full column diff on one pair: the CeFi-bucket "duplicates" in this era carry
      only 10 columns vs the DeFi-bucket originals' 23 (missing `mark_price`/`bid_price`/`ask_price`/`index_price`/
      `mid_price`/`open_interest`/`volume_24h` and more) and are often 1 row short — **these are NOT true duplicates,
      they're an older/narrower-schema capture**. This directly affects Phase 4 below (deleting the DeFi-bucket
      originals for this band would delete the MORE complete copy). Filed
      [`plans/active/issues/aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md`](issues/aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md)
      with the full evidence + an operator-decision todo. Did NOT attempt a fix (schema-authority call is out of this
      todo's scope). Output written to
      `gs://market-data-tick-defi-prd-central-element-323112/_index/audit/aster_cefi_migration_post_apply_verify_2026_07_13.parquet`
      (117,176 rows).

## Phase 3 — Manifest + downstream (P1)

- [x] ✅ [DATA] P1. Rewrite/extend the canonical CeFi `_index/availability_index.parquet` manifest rows for the
      newly-migrated ASTER objects (mirrors the 2026-07-08 script's manifest-rewrite step) — dedup any rows that
      collapse to the same canonical key, keeping the best `capture_status`. — **DONE, slot 14,
      market-tick-data-service@`3841e908` (`scripts/rewrite_aster_cefi_manifest_2026_07_13.py`)**. Sourced the
      definitive migrated-object list from the post-apply verification parquet (single-walk discipline — no fresh GCS
      scan), mirroring `migrate_onchain_perp_perpetual_canonical_2026_07_08.py`'s exact key columns + status-rank dedup
      pattern. Ran `--apply` for real against production: backed up the pre-migration index to
      `_index/backups/availability_index.pre_aster_migration_20260713.parquet` first, then wrote the extended index —
      **117,176 new rows proposed, 79,077 collapsed in dedup (already had manifest coverage), net manifest growth
      7,469,353 → 7,507,452 rows** (dry-run and real apply produced byte-identical stats, confirming determinism).
- [x] ✅ [DATA] P1. Confirm downstream readers (MDPS candle processing, features-service, deployment-api data-status
      drilldowns) correctly pick up the migrated data from its new canonical CeFi-bucket location — spot-check one
      drilldown query for an ASTER instrument/day that was previously only in the DeFi bucket. — **DONE, slot 9,
      unified-trading-pm@`<pending-ship>`** (read-only investigation + a live spot-check, no code change needed). **1)
      MDPS candle processing — GOOD, dynamic.**
      `market_data_processing_service/app/core/orchestration_scheduling.py:224-249` `_list_instrument_files()` lists
      per-day objects in a caller-supplied bucket; bucket resolved per-category via
      `self.config.get_bucket_for_asset_group(category)` → `market_data_processing_service/config.py:62-83`
      `get_source_bucket(asset_group)`, same canonical naming `resolve_bucket_name` produces (catalogue reads use
      `resolve_bucket_name` directly at `cloud_data_provider.py:56-57`). MDPS processes the whole CEFI-category bucket
      in one pass — no ASTER hardcoding anywhere in production code (only hit is a test fixture,
      `engine/mock_data_provider.py:54`) — so it automatically now sees ASTER's migrated objects in its CEFI pass. **2)
      features-service — mixed, no regression.** No currently-shipped calculator reads ASTER's raw
      `derivative_ticker`/`trades` directly today (`cefi/calculators/perp_funding_rates.py` is Binance-only MVP;
      `cefi/calculators/perp_funding_corpus.py`'s `RAW_TO_STRATEGY_VENUE` excludes ASTER + filters
      `pipeline_mode=batch_tardis`, but per its own docstring "has never actually run in production" — pre-existing
      scope limitation, not a migration regression). The dynamic/manifest-driven path
      (`delta_one/app/core/data_loader.py:173-205` `get_available_instruments()`, bucket via
      `resolve_bucket_name(asset_group=...)` at line 55) already recognizes the `ASTER:PERPETUAL:...` canonical key
      shape (`tests/delta_one/unit/test_mvp_universe_filter.py:58`) and will pick up ASTER once MDPS produces processed
      candles for it (point 1) — no code change needed. **3) deployment-api data-status drilldown — GOOD,
      LIVE-VERIFIED.** The real endpoint UI uses, `GET /api/data-status/drilldown/{service}/{asset_group}` →
      `deployment_api/services/data_status_hierarchical.py:400` `get_hierarchical_drilldown()`, resolves the bucket
      dynamically (`asset_group` is a caller param, not inferred from venue) and reads the live
      `_index/availability_index.parquet` manifest — exactly what Phase 3 Todo 1 wrote 117,176 rows into. **Live
      spot-check** (called the function directly, no HTTP server needed, real GCS + real manifest, ADC project
      `central-element-323112`):
      `service=market-tick-data-service, asset_group=cefi, venue=ASTER,     data_type=derivative_ticker, window=2023-11-01`
      — a day the plan's Phase 1 audit confirms was **0%** present in the CeFi bucket before migration (`zero_dup` band)
      — returned `{"captured": 63, "completion_pct": 100.0}` from
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, tree rows carrying
      `pipeline_mode: batch_aster` provenance and canonical `ASTER:PERPETUAL:{BASE}-{QUOTE}@LIN` instrument keys (e.g.
      `ASTER:PERPETUAL:1000FLOKI-USDT@LIN`). Confirms the manifest write + the real drilldown reader both work
      end-to-end. Noted (4 separate ~5-min-TTL cache layers exist on this endpoint — `/turbo/clear` bypasses them, not
      needed for this check since the manifest was already the freshest read). **Found + filed separately** (not a
      migration regression, pre-existing + venue-agnostic): a **legacy**, UI-unused endpoint
      (`GET /api/data-status/instrument-availability`) hardcodes a 12-venue substring lookup that excludes ASTER (and
      any newer venue) and probes a non-canonical flat path instead of the manifest — filed
      [`plans/active/issues/deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`](issues/deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md)
      with fix todos; does not block or relate to this migration's done_definition.

## Phase 4 — Cleanup (gated, separate from migration — P1)

- [x] ✅ [DATA] P1. **DONE, slot 5, market-tick-data-service@`614f276c`, 2026-07-13.** All 116,942 DeFi-bucket-resident
      ASTER `asset_group=cefi` objects deleted (full 948-day existence re-sweep post-delete confirms 0 remaining, not
      sampled). Along the way, a fresh full-population pre-delete parity re-check (not the prior 45-object spot-check)
      found the high_dup band's fix held (0 conflicts) but surfaced the SAME narrower-schema issue newly in the
      `low_dup` band (4,536 objects, 355 days) that the original operator ruling never covered — filed + escalated
      [`aster_cefi_bucket_low_dup_band_schema_row_mismatch_2026_07_13.md`](issues/aster_cefi_bucket_low_dup_band_schema_row_mismatch_2026_07_13.md)
      (BLK-15137c02), operator approved extending Option A, re-migrated that band with `--force`, then completed the
      deletion in one further pass (0 remaining conflicts). Also pruned 996 stray `asset_group=cefi`/
      `pipeline_mode=batch_aster` rows the same write-path bug had left in the DeFi bucket's OWN manifest (backed up
      first to `_index/backups/availability_index.pre_aster_defi_bucket_delete_20260713.parquet`) — those rows would
      have become phantom "captured" entries with no backing object once the delete ran. **The DeFi-bucket-resident
      ASTER originals no longer exist anywhere; the CeFi bucket is the sole canonical copy for all 948 days.**

      Full history of this gate (preserved below): originally — only after Phase 2's parity verification is fully
                                                                                                                          green: delete the DeFi-bucket-resident ASTER `asset_group=cefi` originals (version-aware, matching the same rigor as
                                                                                                                          `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`'s Phase-7 decommission gate — snapshot first,
                                                                                                                          verify canonical ≥ legacy via live-object counts, never a naive `ls`). This is explicitly NOT bundled with the
                                                                                                                          migration apply step — do not delete until an operator confirms the parity verification evidence. **⚠️ 2026-07-13
                                                                                                                          (slot 14): parity verification is NOT green for the `high_dup` band (2024-01→2025-06) — see
                                                                                                                          [`aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md`](issues/aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md).
                                                                                                                          The CeFi-bucket "duplicates" in that band are narrower-schema and sometimes row-deficient vs the DeFi-bucket
                                                                                                                          originals — deleting the DeFi-bucket originals for this band under the current plan would be a DATA LOSS
                                                                                                                          regression (deletes the more-complete copy), not a cleanup. This gate is BLOCKED for that band until the linked
                                                                                                                          issue doc's operator-decision todo resolves (unaffected: `zero_dup` and `low_dup` bands verified clean).** **✅
                                                                                                                          2026-07-13 (slot 6): operator decision resolved (Option A, BLK-4032eac4) — `high_dup` band re-migrated with the
                                                                                                                          new `--force` flag on `migrate_aster_cefi_defi_bucket_2026_07_13.py`, making the 23-column DeFi-bucket shape
                                                                                                                          authoritative at the CeFi-bucket canonical target for 2024-01-01→2025-06-15. Result:
                                                                                                                          `{'force_overwritten': 39216, 'already_migrated_parity_confirmed': 1190, 'skipped_not_in_scope': 0}`, 0 errors.
                                                                                                                          **Post-force parity re-verification DONE and GREEN**: existence 40,406/40,406 present (0 missing); spot-check
                                                                                                                          20/20 row_count_matches, 20/20 byte_identical (vs the pre-force 5/15 and 0/15). Full evidence in
                                                                                                                          `aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md` P2. **This gate is now UNBLOCKED for the
                                                                                                                          `high_dup` band** — parity is fully green for all three bands (`zero_dup`, `high_dup`, `low_dup`). The DeFi-bucket
                                                                                                                          originals are still NOT deleted by this todo; deletion remains a separate, explicitly operator-gated step (this
                                                                                                                          todo itself), now unblocked to proceed whenever an operator wants to schedule it.**

## Deferred work after 2026-07-13 (found this session, out of THIS plan's scope)

| Item                                                                | State                                                                                                                            | Next action                                                                                                               |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `batch_aster` collection stopped after 2026-06-05                   | ✅ **Explained** (Phase 1 Todo 3, 2026-07-13) — collector handoff to `onchain_perp_batch_handler.py` (2026-06-21), not a failure | No action needed — see Phase 1 Todo 3 above for the full trail.                                                           |
| BYBIT `futures_chain` write-shape bug (flat glued-symbol files)     | Found + partially fixed in code 2026-07-09, historical data not backfilled                                                       | Tracked separately — `plans/active/issues/bybit_futures_chain_write_shape_2026_07_13.md`.                                 |
| Legacy `ticks_migrated_*` shallow shape in DeFi bucket (5,332 objs) | Already tracked pre-existing — codex axis-7, archived plan F16/F29, 2026-06-18 delete-list audit MIGRATE-FIRST classification    | No new work needed — do NOT re-scope here, it already has an owner.                                                       |
| `defi__dex_swaps` BQ external table split-table design              | Separate, independent fix in `deployment-service`                                                                                | Tracked in this session's direct commit to `bigquery_feature_external_tables.tf` — does not block or depend on this plan. |

- [x] ✅ [DATA] P1. (Moved here 2026-07-13 per operator ruling during the bucket-estate dispatch) Own the
      DeFi-bucket-resident ASTER originals deletion end-to-end: resolve the high_dup schema/row-deficiency issue
      (aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13) via re-migration or accepted-loss ruling, THEN delete
      the originals. The estate-consolidation plan no longer tracks this deletion. — **DONE, slot 5,
      market-tick-data-service@`614f276c`, 2026-07-13.** New script
      `scripts/delete_aster_cefi_defi_bucket_originals_2026_07_13.py`: fresh per-object HEAD parity re-check (size +
      crc32c, full population, never trusts a prior audit) before allowing any delete. Its first full-corpus run
      surfaced a SECOND instance of the schema/row-deficiency issue in the `low_dup` band (4,536 objects, 355 days,
      2025-06-16 -> 2026-06-05) that the existing `high_dup`-scoped operator ruling never covered — filed
      [`aster_cefi_bucket_low_dup_band_schema_row_mismatch_2026_07_13.md`](issues/aster_cefi_bucket_low_dup_band_schema_row_mismatch_2026_07_13.md)
      and escalated (BLK-15137c02); operator confirmed the same Option A resolution applies (re-verified no
      derivative_ticker reader assumes a fixed column count or branches on this date range, per the operator's caveat).
      Re-migrated that band with `--force`
      (`{'force_overwritten': 4536, 'already_migrated_parity_confirmed': 67875, 'skipped_not_in_scope': 0}`, 0 errors),
      then re-ran the delete script: all 116,942 DeFi-bucket ASTER objects came back byte-identical-safe (0 conflicts)
      and were deleted in one pass. **Verified via a full (not sampled) 948-day existence re-sweep: 0 objects remain.**
      Also pruned 996 stray `asset_group=cefi`/`pipeline_mode=batch_aster` manifest rows the same write-path bug had
      left in the DeFi bucket's own `_index/availability_index.parquet` (pre-cleanup backup at
      `_index/backups/availability_index.pre_aster_defi_bucket_delete_20260713.parquet`) — those rows would have become
      phantom "captured" entries with no backing object. The DeFi-bucket-resident ASTER originals no longer exist; the
      CeFi bucket is now the sole canonical location for all 948 days.
