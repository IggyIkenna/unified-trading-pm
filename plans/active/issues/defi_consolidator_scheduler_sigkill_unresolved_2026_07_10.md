---
doc_type: issue
title:
  defi manifest consolidator — scheduler-triggered Cloud Run executions still SIGKILL every ~2min after the OOM/scaling
  fix; manual executions succeed cleanly
summary:
  "UPDATE 2026-07-12: root-caused and partially fixed. The consolidator's soft-lock TTL (90s) was shorter than real
  cycle durations (93-121s observed), letting overlapping 60s-interval scheduler ticks treat a still-running cycle's
  lock as stale and start a redundant concurrent merge — wasted compute and the leading suspect for the kills (no data
  corruption risk; the canonical write's CAS already protects against that). Fixed (TTL 90s->300s,
  unified-trading-library@d3c36842), deployed to the defi Cloud Run job specifically. Measured result: kill frequency
  dropped ~2.5-3x (from ~2min to ~5-6min between kills) and execution durations dropped from 93-121s to 32-95s — real,
  verified improvement, but NOT fully eliminated; a lower-frequency residual kill pattern persists and needs a follow-up
  pass. Original problem statement below for context: after root-causing and fixing a real window-function scaling
  regression in manifest_consolidator.py (unified-trading-library@800af156) and fully consolidating the defi backlog
  (verified: 27,445,013 rows, zero genuine duplicates, all pending shards merged+pruned), the defi consolidator Cloud
  Run job's SCHEDULER-triggered executions were SIGKILLing roughly every ~2 minutes with zero application logs before
  the kill; manual `gcloud run jobs execute --wait` runs of the identical job/image/config succeeded cleanly every time;
  3 memory mitigations (container 16Gi→32Gi, DuckDB budget 8GB→24GB→14GB) did not stop it."
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [consolidator, cloud-run, oom, sigkill, scheduler, defi, unresolved]
related:
  [
    plans/active/issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
source: [autonomous session, 2026-07-10, discovered while verifying the consolidator scaling fix deploy]
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data-pipeline-engineer
drift_direction: unknown
depends_on: []
last_updated: 2026-07-12
locked_by:
locked_since:
resolved_by:
---

# Scheduler-triggered defi consolidator executions still fail after the scaling-regression fix

## What's confirmed working

- The actual data-correctness problem (window-function scaling regression, root-caused earlier the same session — see
  `defi_manifest_consolidator_duplicate_race_2026_07_10.md`'s second incident) is genuinely fixed and deployed
  (`unified-trading-library@800af156`, fanned to all 18 fleet Dockerfiles, MTDS rebuilt, Cloud Run job updated).
- The real backlog (9 per-VM shards, ~18.7M rows from the defi expected-universe backlog resume) is fully merged and
  pruned. Live manifest verified: 27,445,013 defi rows, zero genuine duplicates (checked against the correct full grain
  key, not a narrow ad-hoc one that gives false positives).
- **Manual executions succeed reliably**:
  `gcloud run jobs execute uts-prod-manifest-consolidator-market-data-defi --wait` and direct local CLI runs
  (`python -m unified_trading_library.manifest_consolidator --bucket ...`) both complete cleanly against the exact same
  bucket/data/image/config, multiple times, with sensible memory profiles (9.86GB and 10.5GB peak, well within the 32Gi
  container).

## What's still broken

- **Scheduler-triggered (`*/1 * * * *` Cloud Scheduler → Cloud Run Jobs `:run` API) executions SIGKILL roughly every ~2
  minutes**, observed repeatedly after the fix deployed: 21:46:06, 21:48:05, 21:49:55, 21:53:58, 21:56:14, 21:58:10 UTC
  (2026-07-10) — a suspiciously consistent ~2min period regardless of the exact memory config in place at the time.
- **Zero application log output before every kill** — not even the Python logging module's own startup line
  (`Event logging initialized: mode=batch, service=manifest-consolidator`), which appears reliably on every successful
  run (manual or scheduled). This means the container is dying extremely early — before or during Python/library import,
  not partway through the actual merge logic.
- **Cloud Monitoring showed real memory pressure once**: `run.googleapis.com/container/memory/utilizations` hit a mean
  of ~0.80 (≈25.5GB of the 32Gi limit) in the one-minute bucket containing a kill — but lowering the DuckDB budget from
  24GB→14GB (which should reduce DuckDB's own ceiling well below that observed peak) did **not** stop the kills, which
  is the strongest evidence this may not be a pure DuckDB-driven OOM.
- **Mitigations tried, none resolved it**: container memory 16Gi→32Gi; `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` 8GB→24GB; then
  24GB→14GB. The kill pattern and ~2min cadence persisted through all three configurations.

## Working hypotheses (none confirmed)

1. **Cold-start/import-time spike unrelated to the merge logic** — `duckdb`, `pandas`/`pyarrow`, and the UTL/UAC
   dependency graph are heavy imports; if the container's baseline (pre-any-real-work) memory footprint is itself large,
   and Cloud Scheduler's `attemptDeadline: 180s` HTTP call to the Jobs `:run` API is somehow interacting with container
   provisioning under load, that could explain a kill before any application code runs. Not verified.
2. **Node-level resource contention, not container-level OOM** — the ~2min period doesn't obviously track any config
   change, which is more consistent with an external/shared factor (e.g. GCE node pool pressure from other concurrent
   jobs in this project) than a self-contained memory ceiling in this one job. Not verified — would need node-level
   metrics, which weren't checked.
3. **Scheduler-vs-manual-execute code path difference** — `gcloud run jobs execute` and the Scheduler's `:run` API call
   are supposed to be equivalent, but the manual path consistently works while the scheduled path consistently doesn't.
   Worth diffing the exact request Cloud Scheduler sends (`--log-http` or Cloud Trace) against a manual `execute` call
   to rule out a genuine difference (e.g. a stale/cached execution environment revision).

## Why this wasn't chased further

No data-correctness risk right now — with the real backlog already fully merged, there is nothing new pending for these
failing cycles to lose; the manifest is verified complete and duplicate-free independent of whether the scheduler runs
cleanly. Given diminishing returns after 3 escalating mitigation attempts and multiple diagnostic passes (Cloud Logging
structured queries, Cloud Monitoring memory metrics, scheduler config inspection), this was parked as an
honestly-documented open issue rather than continuing indefinite trial-and-error. The scheduler was left **enabled**
(not re-paused) — a failing-but-harmless cycle is safer than a paused consolidator that would silently miss a REAL
future shard drop.

## Next steps for whoever picks this up

- Compare a Cloud Trace / `--log-http` capture of a Scheduler-triggered `:run` call against a manual
  `gcloud run jobs execute` call — look for any difference in headers, revision pinning, or timing.
- Check GCE/Cloud Run node-pool-level memory metrics (not just this job's own container metric) during a kill window, to
  rule out cross-job contention.
- Consider temporarily setting `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` very low (e.g. 4GB) as a diagnostic (not a fix) — if
  kills STILL happen at that budget with zero app logs, that's strong evidence the crash is pre-DuckDB (import/startup),
  redirecting the investigation away from merge-logic memory sizing entirely.

## Progress log

- 2026-07-10: Filed after 3 escalating memory mitigations failed to stop scheduler-triggered SIGKILLs, despite the real
  underlying data-correctness bug being confirmed fixed and the manifest confirmed fully consolidated and
  duplicate-free. Scheduler left enabled. No data risk currently.
- 2026-07-11/12: **Root cause found and partially fixed.** Cloud Run execution history
  (`gcloud run jobs executions list`) showed real cycle durations of 93-121s while the scheduler
  (`uts-prod-manifest-consolidator-market-data-defi-cron`) fires every 60s (`*/1 * * * *`) — this causes frequent
  overlapping executions (confirmed directly from execution start/completion timestamps, e.g. two executions both in
  flight for 30-60s+ stretches). The consolidator's own soft-lock (`_index/consolidator.lock`, `_LOCK_TTL_SECONDS=90.0`)
  was SHORTER than several observed real cycle durations, so a still-running cycle's lock aged past the TTL before
  finishing, letting the next overlapping tick treat it as stale, clear it, and start its OWN concurrent DuckDB merge —
  wasted redundant compute and the leading suspect for the kill pattern (the canonical write's generation-match CAS
  already prevents any resulting data corruption; this was a performance/reliability bug, not a correctness one).
  - **Fix**: widened `_LOCK_TTL_SECONDS` 90.0→300.0 (comfortable headroom above the observed 93-121s worst case, well
    under the job's 1800s task timeout). 39 existing unit tests pass, full QG green. Shipped
    `unified-trading-library@d3c368428ed1823682754b1e77331f4ace50ba19`.
  - **Deployed to prod**: UTL's base-image auto-rebuilt on push (Cloud Build `1fed22b7`, digest
    `sha256:e94bdf68754f60193f013583c4df6b66ec259c181bbde0629a17c046d5e3e916`); bumped
    `market-tick-data-service/Dockerfile`'s `ARG BASE_IMAGE_DIGEST` via
    `scripts/propagation/add-dockerfile-digest-arg.py` (shipped
    `market-tick-data-service@a1361fc9e5f18b365749ffcaaff2f6ea23c56126`); MTDS image rebuilt (Cloud Build `df8ebb2e`,
    digest `sha256:015e79114a6ca8d47104789572703cd93ce23b540e3dfbb6bb09c6665c49f643`); **explicitly updated the Cloud
    Run job** via
    `gcloud run jobs update uts-prod-manifest-consolidator-market-data-defi --image=...@sha256:015e7911...` — the job's
    image reference is a resolved digest cached at job-update time, NOT re-resolved per-execution from the `:latest`
    tag, so this explicit update step was required (confirmed: an execution that started before the update still ran the
    OLD digest).
  - **Measured result (real production evidence, ~20min observation window straddling the deploy)**: kill-to-kill gaps
    were ~2min09s and ~2min09s BEFORE the fix (02:56:02, 02:58:11 UTC — consistent with the originally-documented ~2min
    pattern), then ~5min18s and ~5min41s AFTER the fix (03:03:29, 03:09:10 UTC) — roughly a **2.5-3x reduction in kill
    frequency**. Execution durations also dropped from the pre-fix 93-121s range to a consistent 32-95s post-fix,
    consistent with overlapping ticks now hitting the fast lock-skip path instead of contending for CPU/memory with a
    second full concurrent merge.
  - **Not fully resolved**: kills still occur, just less often (~5-6min apart instead of ~2min). This means either (a)
    the lock-TTL/overlap mechanism was A cause but not the ONLY one, or (b) there is a second, lower-frequency,
    still-unidentified source of task-attempt-level SIGKILLs independent of the execution-overlap issue (each surviving
    execution shows `status.conditions[0].status=True` /`Completed`, meaning `maxRetries: 1` is successfully masking
    whatever gets killed — the overall job never actually fails, just wastes a retry). Worth a follow-up pass with the
    residual next-steps below, but this is now real, meaningfully-improved, and honestly a much smaller residual problem
    than at filing time.
  - **Scope note**: this fix (lock TTL) lives in shared `unified_trading_library.manifest_consolidator`, used by every
    `uts-prod-manifest-consolidator-*-cron` job (cefi, tradfi, sports, prediction, etc.), not just defi. Only the
    **defi** Cloud Run job was explicitly updated to the new image in this pass (matching this issue's documented scope)
    — the other consolidator jobs still run the OLD image/TTL and likely have the same latent overlap risk if their own
    cycle durations exceed 90s. Fast-follow candidate: roll the same image-digest update out to the rest of the
    `uts-prod-manifest-consolidator-*` fleet.

## Updated next steps for whoever picks this up

- Investigate the residual ~5-6min-interval kill pattern now that the dominant overlap cause is fixed — check whether
  it's task-attempt-level (survives via `maxRetries: 1`, so the job never truly fails) and whether Cloud Trace /
  `--log-http` diffing (original next-step #1, still not done) would distinguish scheduler-vs-manual triggering as a
  residual factor.
- Roll the same `BASE_IMAGE_DIGEST` bump + `gcloud run jobs update --image=...` to the other
  `uts-prod-manifest-consolidator-*-cron` jobs (cefi, tradfi, sports, prediction, ml-training, gas-fees, etc.) if their
  own execution histories show cycle durations approaching or exceeding the (now-fixed) 300s TTL headroom — same latent
  bug, not yet fixed there.
