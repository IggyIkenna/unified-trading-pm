---
doc_type: issue
title:
  "Sports api-football fixture-dependency check does per-date live GCS probes instead of a manifest slice — measured
  60-130x slower for backfills"
summary: >-
  check_api_football_dependency() checks raw hardcoded GCS paths (list_blobs + .exists()) per date instead of consulting
  the sports availability manifest, which already carries every column needed to answer the same question. Measured real
  numbers: a single prefix-probe costs ~1.8s, a blob-exists probe ~0.26s — for a 1-year backfill that's ~11-25 minutes
  of pure network latency before any real fixture-dependent work runs. A manifest-slice approach (one-time ~10s
  full-file download + a sub-second in-process filter) would do the same job in well under 15 seconds. Separately, the
  hardcoded path templates have zero shared source with whatever the writer actually uses, so a future path migration
  could silently desync the checker from reality.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [performance, manifest, sports, backfill, gcs, p2]
related:
  [
    ../instruments_service_docs_consolidation_2026_07_08.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P2
source:
  'Operator, reviewing instruments-service/docs/ADAPTER_ARCHITECTURE.md''s sports fixture-dependency description
  (check_api_football_dependency): ''shouldn''t it just check the manifest? Isn''t that quicker?... The manifest is
  supposed to be canonical availability... The file paths could migrate. If the code doesn''t [migrate too], but the
  manifest is consistent, then we''re not looking at the manifest.'' Then asked for real numbers on whether a
  manifest-slice approach would meaningfully speed up a year-long backfill ("which can waste half an hour") — confirmed
  with real measurements below.'
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
---

## The finding

`instruments-service/instruments_service/reference_data/sports_dependency.py::check_api_football_dependency()` never
touches the sports manifest (`_index/availability_index.parquet`) — it does live GCS calls
(`_prefix_has_object`/`_blob_exists`) against hardcoded path templates
(`_CANONICAL_FIXTURES_PREFIX_TEMPLATE`/`_LEGACY_FIXTURES_PREFIX_TEMPLATE`/etc.), once per date, every time a
fixture-dependent adapter (footystats/understat/transfermarkt/soccer_football_info/open_meteo/betfair) is created. This
is called from `sports/factory.py:89-90` at adapter-creation time.

**The manifest already has everything needed to answer the same question** — confirmed by reading it directly
(`instruments-store-sports-prd`, real `_index/availability_index.parquet`): columns include `venue`, `data_type`,
`league_id`, `date`, `capture_status`. A `venue == "API_FOOTBALL"` + date + non-empty `capture_status` filter answers
the identical dependency question the current path-probe answers.

## Real measured numbers (2026-07-08)

- **Per-call GCS latency**: a `list_blobs` prefix probe (the first thing the current check tries) = **~1.8s**. A direct
  `.exists()` blob probe = **~0.26s**.
- **1-year backfill cost at current per-date-probe rate**: 365 dates × ~1.8s (best case, canonical prefix hits every
  time) ≈ **11 minutes** of pure network round-trip latency, before any real work happens. Historical dates that fall
  through to the legacy-path fallback (up to 4 sequential calls) push this toward **20-25 minutes**.
- **Manifest file**: `_index/availability_index.parquet`, 72.6 MB compressed, 4,918,507 rows, 2014→2026. One-time full
  download+parse-to-bytes: ~10s (7s download + 3s parse). **Row groups are NOT date-clustered** (every row group spans
  the full 12-year range — write-order-appended, not date-sorted) — so row-group-level predicate pushdown gives zero
  download savings; you must download the full compressed file regardless of how narrow the date window is.
- **But post-download filtering is cheap**: naively loading the WHOLE file into a pandas DataFrame costs **8.77 GB** in
  memory — a real problem for a memory-constrained VM. But filtering via
  `pyarrow.parquet.read_table(..., filters=[...])` on the already-downloaded bytes, BEFORE pandas materialization,
  pulled one full year (596,641 rows) in **0.66s using only 233 MB**.
- **Net for a 1-year backfill**: current approach ≈ 11-25 minutes. Manifest-slice approach ≈ ~10s one-time download
  - ~0.7s filter ≈ **under 11 seconds total** — roughly **60-130x faster**, with bounded, small memory use as long as
    the slice (not the full corpus) is what gets materialized into pandas.

## The separate path-drift risk

Independent of the performance question: `sports_dependency.py`'s path templates have no shared source-of-truth with
whatever the real writer uses to construct fixture output paths. If the write path ever migrates (this workspace has
done exactly this kind of migration more than once), the writer + manifest could stay perfectly consistent while this
checker's independently-hardcoded templates silently go stale, producing false "fixtures missing" errors on a pipeline
that's actually working correctly. A manifest-based check would be structurally immune to this — the manifest is
supposed to be the canonical, path-agnostic answer to "did this availability event happen."

## Todos

- [ ] [DATA] P2. **Design a manifest-slice-based replacement for `check_api_football_dependency()`** — load+filter once
      per backfill run (or per reasonable chunk, e.g. per year) rather than per-date network calls; keep the current
      direct-GCS path as a fallback ONLY if a genuine same-run consolidation-lag risk is confirmed real (the manifest
      consolidator cron runs every 1 minute — `codex/05-infrastructure/manifest-consolidator-ssot.md` — so there's a
      real but small lag window worth explicitly deciding how to handle, not silently ignoring).
- [ ] [DATA] P2. **Share path-template constants between the real fixtures writer and this checker** (or derive the
      checker's expectations FROM the manifest instead of independent path literals) so a future path migration can't
      silently desync them — this fixes the path-drift risk regardless of the manifest-vs-GCS decision above.
- [ ] [VERIFY] P2. **Confirm real backfill speedup** against a real multi-month or full-year backfill run, before vs.
      after, not just the isolated per-call measurements above.
- [ ] [SCRIPT] P2. **Ship via quickmerge**, quality-gates green.

## Progress Log

- **2026-07-08** — Filed after the operator questioned why the sports fixture-dependency check uses direct GCS path
  probes instead of the manifest, then asked for real numbers to confirm whether a manifest-based approach would
  meaningfully help. Measured directly against real production data (see numbers above) — confirmed a real, substantial
  (60-130x) speedup opportunity for backfills, plus an independent path-drift robustness concern. No fix applied yet —
  this issue holds the scope.
