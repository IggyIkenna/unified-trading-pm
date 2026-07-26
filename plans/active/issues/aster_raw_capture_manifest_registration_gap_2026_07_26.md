---
doc_type: issue
title: ASTER raw-trade capture — manifest shows near-total expected_unattempted despite real files on disk
summary: >-
  Discovered while scoping cefi_satellite_ao_dispatch_batch1-001 (extend MDPS candle-building to the 4 on-chain-perp
  CeFi venues). The cefi manifest shows ASTER at 487,191 MTDS rows: 486,890 expected_unattempted, 300 attempted_failed
  (2026-07-24..07-25), and exactly 1 captured row (2026-07-11, one instrument) across the full 2024-01-01..2026-07-25
  range. This contradicts the archived aster_capture_broken_coverage_and_completeness_2026_07_20.md's "🟢 RESOLVED —
  verified with real data" banner. A direct GCS listing shows the opposite of what the manifest claims: real,
  many-instrument raw_tick_data parquet files exist for day=2026-07-20 (written 2026-07-20/21) under
  pipeline_mode=batch_aster, and derived processed_candles/ files (timeframe=15s/1m, unregistered — 0 MDPS manifest rows
  for ASTER at all) exist for the same day. So real trade data IS landing on disk; the manifest is not reflecting it as
  captured — a registration gap, not (necessarily) a fetch failure.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [aster, manifest, capture-status, phantom-registration, data-correctness]
related:
  [
    /plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    /plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-07-26 while working cefi_satellite_ao_dispatch_batch1-001 (slot 6). Direct manifest read
  (unified-trading-library read_availability_index over market-data-tick-cefi-prd-central-element-323112) + direct GCS
  listing (gcloud storage ls, scoped single-prefix reads, no whole-corpus walk) — evidence below.
locked_by:
locked_since:
resolved_by:
depends_on: []
---

# ASTER raw-trade capture — manifest registration gap

## What I found

1. **Manifest read** (`read_availability_index('market-data-tick-cefi-prd-central-element-323112', ...)`, filtered
   `service_name == 'market-tick-data-service'` + `venue == 'ASTER'`): 487,191 rows total —
   `expected_unattempted=486,890`, `attempted_failed=300` (dates 2026-07-24..2026-07-25 only), `captured=1` (date
   2026-07-11, `instrument_id=ASTER:PERPETUAL:BTC@LIN`, `written_at=2026-07-13T07:36:41Z`). The `expected_unattempted`
   rows span the full `2024-01-01..2026-07-21` range — i.e. per the manifest, ASTER's raw trade capture has essentially
   **never run** historically and has been failing outright for the last 2 days.
2. **Direct GCS listing** (scoped single-prefix reads, not a corpus walk) shows the opposite:
   - `raw_tick_data/by_date/day=2026-07-20/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/ instrument_type=perpetual/data_type=trades/`
     contains real per-instrument parquet files (verified ≥10 distinct instruments — `0G-USDT@LIN`, `1000BONK-USDT@LIN`,
     `1000FLOKI-USDT@LIN`, `1000PEPE-USDT@LIN`, etc.), 7-27KB each, `updated` timestamps 2026-07-20T21:06Z /
     2026-07-21T02:08Z — plausible real trade data, not empty placeholders.
   - `processed_candles/by_date/day=2026-07-20/pipeline_mode=batch_aster/` contains derived candles at `timeframe=15s`
     and `timeframe=1m` (data_type=trades, instrument_type=PERPETUAL, venue=ASTER) — someone/ something already ran MDPS
     candle-building against this raw data. **Zero of these candle rows are registered in the manifest either** (0
     `market-data-processing-service` rows for ASTER in the cefi index).
3. **This contradicts** `plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`'s own
   closing banner: "🟢 RESOLVED 2026-07-25 — ACKED-INTO-CODE — all fix items (A/B/C/D/GAP-4) shipped + verified with
   real data in all 3 repos". That doc's "verified with real data" claim does not match what the manifest shows today, 1
   day later.

## Why it matters

- Per-asset_group coverage/completeness reporting (data-status pages, the daily digest, any consumer keying off
  `capture_status`) is currently reading ASTER as ~0% captured when real data physically exists — an under-count, not an
  over-count, so it's less likely to trigger existing "empty/failed" alerting but will silently starve any downstream
  consumer that reads the MANIFEST rather than GCS directly (e.g. MDPS's own `_get_tradable_instruments` path, feature
  backfills gated on manifest freshness, the ADV reader scaffolded in
  `aster_and_cefi_rolling_adv_feature_2026_07_21.md`).
- It blocks `cefi_satellite_ao_dispatch_batch1-001`'s ASTER leg specifically: that todo's "Done when" requires "a
  manifest-verified backfill covers each venue's full already-captured raw-trade range" — for ASTER, the manifest does
  not currently reflect the real captured range, so a manifest-based scoping of the backfill range would be wrong (it
  would think almost nothing has been captured and either skip real data or attempt to re-capture already-present data).
- The un-registered `processed_candles/` output for ASTER (found already on disk, day=2026-07-20, 15s/1m only, no
  manifest rows) is orphaned work from an unknown prior run — worth registering (or re-running with the writer) rather
  than silently leaving as a manifest-invisible artifact.

## Recommended decision

- **[DATA] P0.** Root-cause why ASTER's `record_captured`/`record_failed` manifest writes for the raw-trade adapter are
  not landing (or are landing then being lost/overwritten) despite the adapter clearly writing real parquet to GCS.
  Candidate angles: a raw-write path that bypasses `ManifestWriter` entirely (a direct `upload_bytes` without the paired
  `record_captured` call), a per-VM shard whose manifest rows never got consolidated, or an exception swallowed after
  the GCS upload but before the manifest write. Repo: market-tick-data-service.
- **[DATA] P1.** Once the writer-path is fixed, either (a) re-run a manifest-only reconciliation pass that registers the
  ALREADY-WRITTEN 2026-07-20/21 raw files + their derived candles as `captured` (idempotent, no re-fetch), or (b) if
  root-causing shows the files are somehow suspect, re-run the fetch for that narrow window. Prefer (a) unless the
  root-cause investigation finds a correctness problem with the existing files.
- **[DATA] P2.** Once ASTER's manifest correctly reflects its real captured range,
  `cefi_satellite_ao_dispatch_ batch1-001`'s ASTER leg (MDPS candle backfill) can be scoped correctly and re-attempted;
  until then it is carved out of that todo's initial delivery (see that plan's Progress Log / evidence for the
  carve-out).

## Not yet checked (deliberately out of scope for this discovery pass)

- Whether the SAME registration gap affects other CeFi venues beyond the 4 on-chain-perp ones this session was scoped to
  (a broader per-venue capture_status sweep would need a dedicated audit pass, not a corpus walk from here).
- Whether the un-registered `processed_candles/` ASTER output (15s/1m only) was produced by a human/agent test run or a
  since-removed cron; no currently-running GCE VM was found producing it (checked `gcloud compute instances list` at
  discovery time — only unrelated `mdps-backfill-tradfi-*` VMs were running).
