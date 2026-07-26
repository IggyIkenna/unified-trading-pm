---
doc_type: issue
title: Reconcile MDPS cefi candle-manifest rows orphaned by pre-fix-era OOM crashes (real files, zero manifest row)
summary: >-
  Extracted from `mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` (archived, resolved) before archival so its
  still-open P2 follow-up survives as its own tracked, AO-eligible unit rather than being silently buried inside a
  resolved doc. That doc's root-cause trace confirmed MDPS's candle-manifest emission logic is correct TODAY, but found
  a genuine PAST (already-fixed-going-forward) gap: any `processed_candles/` parquet file written by a backfill VM that
  OOM-crashed mid-run BEFORE `market-data-processing-service@335e9cc` landed (the per-date memory-scaling OOM fix) may
  have lost its in-flight `ManifestWriter.record_captured` write, leaving real file content on disk with zero manifest
  row — confirmed for BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03` specifically. The corpus-wide
  extent of this orphan set is unknown.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, unified-trading-library]
scope: [engineer]
tags: [mdps, candle, manifest, cefi, reconciliation, backfill, oom]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Extracted 2026-07-26 (cicd plan_health wall-clear, escalation agt-37cd1c) from
  `/plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`'s unresolved P2 todo, at archival time,
  per CLAUDE.md issue-doc-lifecycle (never archive a doc while leaving real open work stranded inside it).
locked_by:
locked_since:
resolved_by:
depends_on: []
---

# MDPS cefi candle-manifest: reconcile pre-fix-era orphaned rows

## What I found

See the parent doc's "Root cause (found 2026-07-26, slot-12 `data_engineering`)" section for the full trace. Summary:
MDPS's candle-manifest emission path is correct today (live-verified for both `pipeline_mode=batch_hyperliquid` and
`batch_tardis`), but candle files written by a backfill VM that OOM-killed mid-run BEFORE
`market-data-processing-service@335e9cc` (the per-date memory-scaling OOM fix) may have lost their in-flight
`ManifestWriter.record_captured` write — real file, zero manifest row, forever, unless reconciled. Confirmed for
BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03`; the full extent across dates/venues is unmeasured.

## Recommended fix path

- [ ] [DATA] P2. **Reconcile the manifest for candle files orphaned by PAST OOM crashes (before the
      `market-data-processing-service@335e9cc` OOM fix landed).** An unknown-but-potentially-large set of existing
      `processed_candles/` parquet files across the corpus (any date/venue processed by a backfill VM that OOM'd mid-run
      before 2026-07-26) may have zero manifest rows despite real file content on disk — the SAME class of gap confirmed
      for BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03`. Scope this as its OWN single-walk-compliant
      run (do NOT re-walk the whole corpus ad hoc): (1) use the launcher's own documented reconciliation helper,
      `unified_trading_library.manifest_writer.rebuild_manifest_from_canonical_paths(bucket, service_name="market-data-processing-service", prefix="processed_candles/by_date")`
      (printed by `launch-mdps-backfill-vm.sh` itself as the post-backfill reminder), which walks canonical GCS paths
      and backfills missing manifest rows without re-deriving data; (2) run it on a Tier-2 SPOT VM per the workspace's
      heavy-I/O rule, never in-session; (3) verify before/after row counts for a sample of known-orphaned shards (e.g.
      the BITGET-FUTURES `day=2026-05-03` shard above) to confirm the walk actually closes the gap. Repo:
      market-data-processing-service (consumer of the UTL helper) + unified-trading-library (the helper itself, if it
      needs any fixes). **Done when**: `rebuild_manifest_from_canonical_paths` run completes over the CEFI candle
      corpus, a sample of previously-orphaned shards (including the `day=2026-05-03` BITGET/BITFINEX/KRAKEN ones) show
      real manifest rows, and the launch is evidenced (VM name + log). **Safe-idempotent justification (VM-launch
      gating)**: `rebuild_manifest_from_canonical_paths` only ADDS missing `captured` manifest rows derived from objects
      that already exist on disk — it never deletes/mutates GCS objects and never re-derives/rewrites candle data, so
      re-running it is a no-op on shards that already have a manifest row. No `[OPERATOR]` tag needed per
      `task_template.md` finding O's safe-idempotent carve-out.
