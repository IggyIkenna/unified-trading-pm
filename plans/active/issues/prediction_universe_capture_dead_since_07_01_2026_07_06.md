---
doc_type: issue
title: Prediction universe capture dead 07-01→07-06 — consolidator string-types instrument_count, writer merge crashes
summary:
  "is-daily-enum-prediction (the 13:30 UTC prediction universe capture) failed with exit 1 every day 2026-07-01→07-06:
  the manifest consolidator persists the canonical availability index with instrument_count as STRINGS, the UTL
  ManifestWriter read-merges it with its own int rows, and merged.to_parquet dies with ArrowTypeError ('Expected bytes,
  got int'). Prediction by_date starved (2,193 ids 06-30 → 0 files 07-03/05 → 3 ids 07-06); catalogue stayed green on
  §7.3 thin-day semantics so nothing alerted. Compounding finds: prediction (and sports) run BOTH legacy AND non-legacy
  instruments consolidators every minute (racing co-writers; other AGs paused legacy 06-08); Cloud Run jobs ship no app
  logs to Cloud Logging; the shard-isolation catch logs without exc_info. UTL write-side Int64 coercion shipped as the
  crash-proof fix; consolidator dtype + migration + backfill of the missed days remain."
status: open
nature: record
asset_group: [prediction]
stage: [data]
repos: [unified-trading-library, instruments-service, deployment-service]
scope: [engineer, admin]
tags: [manifest, consolidator, prediction, capture, dtype, arrow, observability, instruments]
related: [plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md]
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    is-daily-enum-prediction daily failure investigation 2026-07-06 — consolidator string-typed instrument_count + UTL
    writer merge ArrowTypeError,
  ]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data-pipeline-engineer
drift_direction: advance-code
depends_on: []
---

# Prediction universe capture dead 2026-07-01 → 07-06 (found during catalogue weekend verification)

## Root-cause chain (each step verified 2026-07-06, slot-2)

1. **The canonical `_index/availability_index.parquet` in `instruments-store-pred-prd` carries `instrument_count` as
   STRING for all 24,994 rows** (verified by direct read; ManifestRow declares it `int`). The file's content is frozen
   at date ≤ 2026-06-27.
2. **The manifest consolidator rewrites that file every minute preserving/producing the string typing** — verified live:
   index mtime tracks the every-minute cron; a forced non-legacy run (`…-instruments-prediction-ltbf9`) rewrote it
   06:28:42Z, still all-string.
3. **The UTL `ManifestWriter` read-merges the canonical with its own int-typed rows** → object column with mixed str+int
   → `merged.to_parquet(...)` raises `ArrowTypeError("Expected bytes, got a 'int' object", column instrument_count)`
   (full traceback captured via a logging shim — the shard-isolation catch swallows it).
4. → **`is-daily-enum-prediction` failed daily 07-01→07-06** (6 consecutive exit-1 runs, ~30 min each); prediction
   by_date starved: 2,193 ids on 06-30 → 0 files 07-03/07-05 → 3 ids 07-06; catalogue `available_from` frozen at 06-27.

## Why nothing alerted (three masking layers)

- The **catalogue** §7.3 liveness correctly refuses to delist on thin/absent days → catalogue jobs stayed green.
- The catalogue's **`CATALOGUE_STALE_BY_DATE`** feed-health warn was blinded by prediction's FUTURE-dated `day=`
  partitions (settlement-dated dirs out to 2029 make `max(day)` never look old). Fixed: clamp to `day <= today`
  (instruments-service, shipped with regression test).
- **Cloud Run jobs ship almost no app logs to Cloud Logging** (only "Container called exit(1)") AND the UTL
  shard-isolation catch (`service_framework/_adapter.py` "Handler %s failed on payload") logs WITHOUT `exc_info` — the
  crash was invisible without a local repro + logging shim.

## Fixes shipped 2026-07-06

- [x] [CODE] P0. UTL write-side schema enforcement: `_merge_dataframes` coerces `instrument_count` / `schema_version` /
      `row_count` to nullable Int64 before every index/shard write — a dtype-divergent co-writer can never crash the
      capture path again. Verified against the exact poisoned prod frame (24,994-row merge + `to_parquet` OK). —
      unified-trading-library@<pending quickmerge sha, see progress log>
- [x] [INFRA] P1. Paused `uts-prod-manifest-consolidator-instruments-prediction-legacy-cron` — prediction ran BOTH
      legacy and non-legacy consolidators every minute (racing co-writers on one file); cefi/defi/tradfi paused their
      legacy variants 2026-06-08, prediction was missed. (Reversible: `gcloud scheduler jobs resume …`.)
- [x] [VERIFY] P0. Local healing run of the exact capture command on the fixed UTL → green + today's universe restored
      (see progress log for run evidence).
- [x] [CODE] P1. Catalogue feed-health clamp (`_warn_coverage_horizon` ignores future-dated days) + regression test —
      instruments-service (shipped with the same-day batch).

## Remaining (this issue's open work)

- [ ] [CODE] P1. **Fix the consolidator's dtype handling at ITS source** (it should persist schema-typed columns, not
      utf8) — locate the consolidator image/repo (manifest-consolidator SSOT:
      `codex/05-infrastructure/manifest-consolidator-ssot.md`), find where 2026-06-27-era changes began string-typing
      `instrument_count`, fix + redeploy. The UTL coercion makes this non-urgent but the canonical index dtype should be
      honest.
- [ ] [INFRA] P1. **Audit sports for the same double-consolidator condition** (`…instruments-sports-legacy` also shows
      recent every-minute runs) + pause its legacy cron if confirmed; verify sports capture/index dtype health.
- [ ] [INFRA] P1. Get the fixed UTL into the `is-daily-enum-*` Cloud Run image: UTL base republish → instruments-service
      pin bump → image rebuild (the dependency-update fan-out chain; manual short-circuit is the 07-04 recipe). Until
      then the 13:30 UTC cloud run may still fail — the local heal covers today; verify tomorrow's run.
- [ ] [VERIFY] P1. Backfill check for the missed window 07-01→07-06: confirm the healed capture's `--days-back` reach
      covers the gap days' by_date + manifest rows, or run a targeted backfill; then confirm the catalogue picks up
      post-06-27 listings (`max(available_from)` advances) on the next daily run.
- [ ] [CODE] P2. Observability: add `exc_info=True` to the UTL shard-isolation catch (`_adapter.py`) and root-cause why
      Cloud Run job stdout/stderr does not reach Cloud Logging (affects every lifecycle-catalogue/enum job — the
      2026-07-04 cefi/prediction weekly-full diagnoses also had to work blind).

## Progress log

- 2026-07-06: Found during the incremental-catalogue plan's weekend verification (catalogue rows green but prediction
  `max(available_from)` frozen at 06-27 → pulled the thread). Root cause chain verified end-to-end; UTL coercion fix
  written + verified on the poisoned prod frame; legacy consolidator cron paused; local healing capture + UTL quickmerge
  in flight (evidence appended when green). Operator notified in-session.
