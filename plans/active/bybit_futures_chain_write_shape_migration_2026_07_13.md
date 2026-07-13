---
doc_type: plan
title: Migrate BYBIT futures_chain historical data to the canonical underlying= hive shape
summary: >-
  BYBIT raw_tick_data instrument_type=futures_chain has at least 3 coexisting/sequential write shapes across ~2025-06
  through 2026-05 (flat glued base+quote files, bare-underlying flat siblings, and the correct underlying= hive form) —
  a regex bug fixed in code 2026-07-09 was never backfilled, and the true affected window is wider than first estimated.
  Audit the exact scope, then reshape/backfill to the single canonical underlying= form with parity verification before
  any cleanup of the non-canonical originals.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [migration, bucket-placement, data-correctness, canonicalisation, cefi, bybit, futures_chain]
related: [issues/bybit_futures_chain_write_shape_2026_07_13.md, aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
source:
  [
    "Follow-up to issues/bybit_futures_chain_write_shape_2026_07_13.md (filed during the deployment-service
    bigquery_feature_external_tables.tf fix session, 2026-07-13). Operator directed a real fix + AO dispatch after a
    same-day rescoping check found the affected window is wider than the issue doc's initial spot-check estimated
    (~2025-06 through ~2026-05, not just 2026-01; some days carry a THIRD shape — bare-underlying flat files, e.g.
    ETH.parquet, coexisting with the glued BTCUSDT-style files on the same day; no futures_chain data found for BYBIT at
    all June-July 2026, pre- or post the 2026-07-09 code fix — needs explanation).",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
---

# Migrate BYBIT futures_chain to the canonical underlying= shape

## Finding (2026-07-13, rescoped same day from the original issue doc)

`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`,
`pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT/instrument_type=futures_chain/` has AT LEAST 3 shapes,
confirmed via direct sampling (not yet a full day-by-day audit — that is this plan's Phase 1):

1. **Correct canonical hive form**: `.../data_type=trades/underlying={U}/ticks.parquet` — matches the SSOT
   (`market-tick-data-service/docs/GCS_PATHS.md`, `docs/canonical-write-conventions.md`), same shape DERIBIT uses
   correctly across its whole history (DERIBIT needs NO migration — its shape is already canonical, confirmed via
   codex + consistency across 2019-2026; do not touch it, per the same investigation that found this BYBIT issue).
2. **Bare-underlying flat siblings**: e.g. `ETH.parquet` coexisting with `ETHUSDT.parquet` in the SAME
   `data_type=trades/` folder on the same day (confirmed 2025-06-01, 2025-09-01).
3. **Glued base+quote flat files (the regex-bug window)**: `BTCUSDT.parquet`, `ETHUSDT.parquet`, etc., no `underlying=`
   segment. Root cause documented in `canonical-write-conventions.md` lines 212-217 (`_extract_underlying_for_chain`
   regex bug, captured `BTCUSDT` instead of `BTC`), **fixed in code 2026-07-09**.

**Rescoped date range** (wider than the issue doc's initial 2026-01 estimate): glued-shape files confirmed present on
sampled days from **2025-06-01 through 2026-05-01**; **no futures_chain data at all found for BYBIT from 2026-06-01
onward** (checked through 2026-07-13, both the flat and hive forms — needs explanation: did collection pause, move
venues, or change instrument_type classification? Phase 1 owns this).

## Codex SSOTs

- `market-tick-data-service/docs/GCS_PATHS.md`, `docs/canonical-write-conventions.md` (canonical `underlying=` hive
  shape for `futures_chain`/`options_chain`)
- `codex/02-data/availability-manifest-and-data-status.md` (manifest rewrite discipline, single-walk rule)
- `codex/05-infrastructure/gcs-object-operations.md` (`gcs_copy_object`/`gcs_delete_object`, never subprocess
  `gcloud`/`gsutil`)

## Phase 1 — Full scope audit (P0)

- [ ] [DATA] P0. Full (not sampled) day-by-day walk of
      `pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT/instrument_type=futures_chain/` across its entire history
      — classify EVERY day into shape (1)/(2)/(3)/mixed/absent. Write to
      `_index/audit/bybit_futures_chain_shape_scope_2026_07_1X.parquet` (mirrors the existing
      `_index/audit/legacy_dup_delete_list_defi.parquet` convention). Confirm the exact start of shape (3) (first
      glued-file day — do not assume 2025-06-01 is the start, that was just the earliest day sampled so far), the exact
      end (does it really stop dead after 2026-05-01, or is that a sampling gap?), and explain the June-July 2026
      absence (collection paused / moved / reclassified — check `market-tick-data-service` git log + any BYBIT-specific
      launcher/scheduler config around that window).
- [ ] [DATA] P0. For every day classified shape (2) or mixed (bare-underlying + glued coexisting): determine whether the
      two files are duplicates (same trades, different naming) or genuinely different data — sample a handful of (day,
      symbol) pairs, download + diff row counts/content. This determines whether shape (2) needs its own reshape logic
      or can be treated as a pre-existing duplicate of shape (3).

## Phase 2 — Build + dry-run the reshape (P0)

- [ ] [DATA] P0. Build a reshape/backfill script (new script under `market-tick-data-service/scripts/`,
      `# Epic: mtds_mdps_master`, `# Lifecycle: oneoff` header per `codex/06-coding-standards/script-homes.md`) that
      parses glued `{BASE}{QUOTE}.parquet` filenames back into `{underlying}/{quote}` using the SAME
      base/quote-splitting logic the 2026-07-09 code fix now uses going forward (do not reinvent — import/reuse it),
      server-side copies to the canonical `underlying={U}/ticks.parquet` path via UTL `gcs_copy_object`, and is
      idempotent (skip when the canonical target already exists and is verified byte/row-identical). Handle shape (2)
      per Phase 1's duplicate-vs-unique finding. DRY-RUN default, `--apply` to mutate.
- [ ] [DATA] P0. Dry-run across the full audited scope (Phase 1's day list); verify planned rename/copy count matches
      the audit; spot-check 10+ planned reshapes for correctness (base/quote split, target path).

## Phase 3 — Apply + verify (P0)

- [ ] [DATA] P0. `--apply` the reshape, sharded by date range if needed (VM launch per
      `codex/05-infrastructure/vm-launcher-runbook.md`, SPOT provisioning, no fire-and-forget — verify STARTED +
      progress + terminal state).
- [ ] [DATA] P0. Post-apply verification: re-run Phase 1's audit against the result, confirm 0 non-canonical shapes
      remain in the migrated window; spot-check row/byte parity (not just object presence) on 20+ migrated (day, symbol)
      pairs.
- [ ] [DATA] P1. Rewrite/extend the canonical `_index/availability_index.parquet` manifest rows for the reshaped objects
      (mirrors the pattern in `aster_cefi_data_defi_bucket_migration_2026_07_13.md` Phase 3) — dedup any rows that
      collapse to the same canonical key.

## Phase 4 — Cleanup (gated, separate from the reshape — P1)

- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION** — only after Phase 3's parity verification is fully green: delete the
      non-canonical (glued + bare-underlying) originals. Version-aware, snapshot first, same rigor as
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase-7. Explicitly NOT bundled with the reshape
      apply step.

## Success criteria

- Every BYBIT `futures_chain` object under the audited scope resolves to the single canonical
  `underlying={U}/ticks.parquet` shape — verified via a real BigQuery/query-style read, not just object presence.
- The June-July 2026 data absence is explained (documented finding, not a mystery left open).
- DERIBIT and all other `futures_chain` venues are untouched — this plan is BYBIT-scoped only.
