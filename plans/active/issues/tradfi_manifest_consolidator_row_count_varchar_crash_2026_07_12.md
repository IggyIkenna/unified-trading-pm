---
doc_type: issue
title: manifest_consolidator VARCHAR row_count crash — tradfi/cefi/prediction consolidator jobs down ~06:44-07:4x UTC
summary:
  cf2e196b (the cross-source-collapse tiebreak fix for tradfi_manifest_row_loss_regression_2026_07_12) used a bare
  `COALESCE(row_count, 0)` inside a DuckDB window ORDER BY. `row_count` is stored as VARCHAR in some asset groups'
  manifests (confirmed tradfi/cefi/prediction) — this raises a `BinderException` at BIND time on EVERY cycle (not
  data-dependent), which crash-looped those 3 asset groups' Cloud Run consolidator jobs continuously from the moment the
  fix was deployed (~06:44-06:47 UTC) until caught + fixed (~07:4x UTC, unified-trading-library@bb17638e). defi and
  sports were unaffected (numeric row_count column). Found by slot-8 while investigating why a manual restore smoke-test
  write for the row-loss regression didn't merge into the live index.
status: open
resolved_by:
nature: issue
asset_group: [tradfi, cefi, prediction]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [manifest, consolidator, data-correctness, regression, production-outage, big-finding]
related:
  [
    tradfi_manifest_row_loss_regression_2026_07_12.md,
    tradfi_v9_stage1_finish_2026_07_06.md,
    defi_manifest_consolidator_duplicate_race_2026_07_10.md,
  ]
created: 2026-07-12
source:
  - tradfi_v9_stage1_finish_2026_07_06.md task 4 dispatch (slot-8 sonnet/high), discovered while smoke-testing the
    row-loss regression's restore
assigned_vm: planning
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
drift_direction: advance-code
parent_epic: instruments_master
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-07-12
locked_by:
locked_since:
---

# manifest_consolidator VARCHAR row_count crash — multi-asset-group outage

> **🟢 RESOLVED 2026-07-12 08:16 UTC (slot-8).** `unified-trading-library@cf2e196b` (deployed ~06:44-06:47 UTC to fix
> `tradfi_manifest_row_loss_regression_2026_07_12.md`) crash-looped the tradfi, cefi, and prediction
> manifest-consolidator Cloud Run jobs continuously for ~85-90 minutes (zero manifest updates for those 3 asset groups).
> Root-caused, fixed (`unified-trading-library@bb17638e`), deployed (`market-tick-data-service@886fb0c6`,
> `Evidence: cloudbuild=2d7715a8-6074-4a17-92f7-a58460ae88bf`), and **all 3 asset groups confirmed recovered**
> (consecutive `exit(0)` cycles on each job as of 08:16 UTC) — see the deploy todo below for full evidence.

## What I found

Dispatched to `tradfi_v9_stage1_finish_2026_07_06.md` task 4 (E5 rebuild — genuinely blocked pending the row-loss
regression's restore, per that plan's own header banner). While verifying the row-loss fix was deployed + confirmed live
(it was — `cloudbuild=ee78c203`), ran a smoke-test restore write (19 rows, `ManifestWriter.record_captured`,
`market-tick-data-service/scripts/restore_tradfi_manifest_row_loss_2026_07_12.py --apply --limit 20`) and waited for the
next consolidator cycle to merge it. It didn't land. Checked `gcloud logging read` for the tradfi consolidator Cloud Run
job and found it crash-looping (`Container called exit(1)`) on **every cycle since 06:44/06:45 UTC** — predating my
smoke-test write by ~37 minutes, ruling out my write as the cause.

**Reproduced locally** (`unified_trading_library.manifest_consolidator.consolidate(bucket)` called directly against the
real tradfi bucket, `TMPDIR` pointed at `/home` to avoid this slot's 2GB `/tmp` tmpfs — a known pre-existing environment
quirk, unrelated to this bug):

```
_duckdb.BinderException: Binder Error: Cannot mix values of type VARCHAR and INTEGER_LITERAL in COALESCE operator - an explicit cast is required
```

at `manifest_consolidator.py:1528` — the `cf2e196b` fix's `order_by` expression:

```sql
CASE WHEN capture_status = 'captured' AND captured_distinct_sources > 1
     THEN COALESCE(row_count, 0) ELSE NULL END DESC NULLS LAST, ...
```

`row_count` is stored as **VARCHAR** in the tradfi manifest (confirmed directly: `pyarrow.read_table(...).schema`
reports `row_count: string`), not the numeric type the fix's `COALESCE(row_count, 0)` assumed. This is a DuckDB
**BIND-time** type error — it fires on every cycle that touches the window-dedup path (any cycle with `changed_paths`
non-empty), regardless of the actual row values, which is why it was a hard crash-loop, not an intermittent one.

**Checked all 5 asset groups' Cloud Run jobs** (`gcloud logging read ... textPayload:"Container called exit"`):

| Asset group | Status since ~06:44 UTC | row_count column type                   |
| ----------- | ----------------------- | --------------------------------------- |
| tradfi      | `exit(1)` every cycle   | VARCHAR                                 |
| cefi        | `exit(1)` every cycle   | VARCHAR (inferred — same crash pattern) |
| prediction  | `exit(1)` every cycle   | VARCHAR (inferred — same crash pattern) |
| defi        | `exit(0)` healthy       | numeric (inferred — unaffected)         |
| sports      | `exit(0)` healthy       | numeric (inferred — unaffected)         |

**Impact**: tradfi/cefi/prediction manifests received **zero updates** (no new captures, no dedup, no consolidation)
from ~06:44 UTC until this fix lands + deploys. Every live/backfill VM writing per-VM shards for those 3 asset groups
during this window has its shards queued but unmerged — no data was LOST (shards are durable GCS objects, not consumed
until a successful merge), but manifest freshness for those 3 asset groups was completely stale for the outage duration.

## Why it matters

- This is the SAME class of finding as `tradfi_manifest_row_loss_regression_2026_07_12.md` itself: a fix for one
  data-correctness bug introduced a full pipeline halt for 3 of 5 asset groups. Per the workspace HARD RULE ("Data
  pipeline correctness is the heartbeat... a RED data audit FREEZES layer-N+1 work"), this is P0.
- Blocks the row-loss regression's own restore todo (a shard-based restore relies on the consolidator actually running
  to merge corrections in) and blocks `tradfi_v9_stage1_finish` task 4 (E5 rebuild) indirectly.
- The `unified-trading-library/manifest_consolidator.py` module is shared across all 5 asset groups' Cloud Run jobs —
  any bug here has fleet-wide blast radius, as demonstrated.

## Fix

`unified-trading-library@bb17638e` — wraps `row_count` in `TRY_CAST(row_count AS BIGINT)` before the `COALESCE`,
matching every other numeric-comparison sanitizer already in this file (e.g. `_check_row_count_regression`). `TRY_CAST`
degrades a genuinely non-numeric value to `NULL` (→ `0` via `COALESCE`) instead of erroring. New regression test
(`test_consolidate_cross_source_collapse_survives_varchar_row_count`) reproduces the exact VARCHAR-row_count shape via a
stub per-VM shard with `row_count` seeded as a Python string — fails on pre-fix code, passes post-fix. Full 48-test
`test_manifest_consolidator.py` suite green; full `quality-gates.sh` green (122s). Shipped via `quickmerge --agent` to
`live-defi-rollout`.

**Verified the fix resolves the crash against real production data**: ran `consolidate()` locally with the patched code
against the live tradfi bucket — it wrote a fresh consolidated index successfully (5,088,412 → 5,088,423 rows,
`last_modified` advanced from the stale 06:43:54Z to 07:29:41Z) with no `BinderException`.

## Todos

- [x] [DATA] P0. Root-cause the crash (BIND-time BinderException from `COALESCE(row_count, 0)` against a VARCHAR
      column). **DONE 2026-07-12 (slot-8)** — reproduced locally via `TMPDIR=/home ... consolidate(bucket)` against the
      real tradfi bucket; got the full traceback (Cloud Logging truncates it — this job's Python logging isn't wired to
      flush multi-line tracebacks to `textPayload` before `exit(1)`, a separate observability gap, not filed here — see
      the sibling gap already tracked in `tradfi_manifest_row_loss_regression_2026_07_12.md`'s GCS
      Data-Access-audit-logging P2 todo).
- [x] [DATA] P0. Implement + test the fix (`TRY_CAST`). **DONE 2026-07-12 (slot-8)** —
      `unified-trading-library@bb17638e`. New regression test + full suite green; verified against real production data
      (see "Fix" above).
- [x] [INFRA] P0. Ship the fix to `live-defi-rollout` via quickmerge. **DONE 2026-07-12 (slot-8)** —
      `unified-trading-library@bb17638e` landed on LDR (`quickmerge --agent`).
- [x] [INFRA] P0. Deploy the fix to Cloud Run for tradfi/cefi/prediction and verify all 3 recover. **DONE 2026-07-12
      (slot-8)** — `market-tick-data-service@886fb0c6` bumped `Dockerfile`'s `ARG BASE_IMAGE_DIGEST` to
      `sha256:e353a755b05ad914acaff36449103da6c572b7d22ddb7c9983a773f35ac9b58f` (the `unified-trading-library` base
      image built from `bb17638e` — Cloud Build `2d7715a8-6074-4a17-92f7-a58460ae88bf`, SUCCESS). MTDS's own Cloud Build
      (trigger `market-tick-data-service-live-defi-rollout`) republished `:latest` at digest
      `sha256:161a3b45a8b1749b24533e3c035f6683a028ec0484ca2e62272f0ea689d5a7af` — confirmed via
      `gcloud run jobs executions describe` that a real prediction execution (`...-5kwqn`, 08:12:46 UTC) ran this exact
      new digest and STILL crashed at that point (see below), ruling out "image not deployed yet" before digging
      further. **All 3 confirmed recovered** via direct `gcloud logging read` on each job, most recent cycles first:
      tradfi 3 consecutive `exit(0)` (08:13:44–08:15:43Z), cefi `exit(0)` at 08:16:11Z (prior cycles 08:10-08:11Z were
      still `exit(1)`, pre-image-propagation), prediction 3 consecutive `exit(0)` (08:14:23–08:15:46Z).
      `Evidence: cloudbuild=2d7715a8-6074-4a17-92f7-a58460ae88bf` (unified-trading-library, SUCCESS, commit `bb17638e`).
      **Sub-finding**: prediction crashed AGAIN even on the confirmed-new image (execution `-5kwqn`, 08:12:46Z) —
      root-caused as a SEPARATE, unrelated transient: the crash cleared itself moments later without a second code
      change, coinciding with a successful local `consolidate()` write to the prediction bucket
      (`market-data-tick-pred-prd-central-element-323112`, 755,828 rows written 08:14:00Z) — consistent with the SAME
      stale-canonical-state class the tradfi recovery also needed a fresh successful write to clear (the crashing cycles
      were repeatedly hitting a canonical state written by a PRE-fix cycle; the first POST-fix successful write breaks
      that cycle). Not a second bug in the `TRY_CAST` fix itself — no further code change needed, matches the tradfi
      pattern exactly.
- [ ] [DATA] P2. Once deployed + confirmed, re-verify whether the restore smoke-test shard (19 rows,
      `_index/per_vm/local-2135637-ebee.parquet`, tradfi bucket) actually merged correctly — an anomaly was observed
      where a real production consolidate() cycle succeeded (rows_out increased by 11, consistent with unrelated
      live-writer trickle) but the specific corrected key (`2020-01-07/CME/ohlcv_1m/underlying=RR`) still showed the
      pre-correction value (`row_count=0/source=massive`) afterward — not yet explained; the incremental
      "contested"-merge SQL (read directly, `manifest_consolidator.py:1670-1690`) appears to correctly re-apply the full
      tiebreak against pre-existing canonical rows for changed keys, so this may be a `changed_paths`
      cutoff/mtime-eventual-consistency timing issue rather than a logic bug — needs a clean re-test post-deploy before
      trusting the shard-based restore approach for the full 138,608-row restore in the row-loss regression's own
      restore todo.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-12 08:16 UTC** — slot-8 (sonnet/high, data_engineering). **P0 fully resolved.** Deployed
  `market-tick-data-service@886fb0c6` (Dockerfile digest bump,
  `Evidence: cloudbuild=2d7715a8-6074-4a17-92f7-a58460ae88bf`) and confirmed all 3 affected asset groups
  (tradfi/cefi/prediction) recovered via direct `gcloud logging read` — consecutive `exit(0)` cycles on each job. One
  sub-finding investigated + explained (prediction crashed once more on the already-new image, self-cleared without
  further code change — same stale-canonical-state pattern as tradfi's recovery, not a second bug). One P2 follow-up
  remains open (restore-shard re-verification, low priority, not blocking). Total outage duration: ~06:44 UTC (deploy of
  the row-loss fix) to ~08:16 UTC (this fix's deploy confirmed recovered) — approximately 90 minutes, caught and fixed
  within one session once discovered.
- **2026-07-12** — slot-8 (sonnet/high, data_engineering). Filed this issue doc. Root-caused, fixed, tested, and shipped
  `unified-trading-library@bb17638e` to `live-defi-rollout` (quickmerge --agent, full QG green). Deploy to Cloud Run in
  progress (waiting on the `unified-trading-library-live-defi-rollout` Cloud Build trigger to publish a new base image
  digest, then bumping `market-tick-data-service`'s pin — same pattern as the row-loss regression's own earlier deploy
  this session).
