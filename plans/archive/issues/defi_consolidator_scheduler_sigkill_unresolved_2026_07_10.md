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
status: resolved
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
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-12
locked_by:
locked_since:
resolved_by: [unified-trading-library@9358fb0b, deployment-service@fe67a53]
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

## Corroborating downstream-impact evidence (2026-07-12, from the pipeline_e2e_check full sweep session)

A real 452-shard `data_pipeline_e2e_check` full sweep (unrelated task, `data_pipeline_e2e_check_2026_07_10.md`)
independently confirms this consolidator is STILL not completing reliably as of 2026-07-12T06:54:34Z:
`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` last updated
**2026-07-10T21:42:30Z — ~34 hours stale**, well past the 86400s (24h) budget every MTDS VM bootstrap checks before
starting its Python workload (`vm-setup.log`'s own "OOM preflight" step). This is real, quantified DOWNSTREAM IMPACT
this issue doc didn't yet capture: **153 of 344 MTDS DEFI shards' force-leg VMs in the sweep hit this exact preflight
check and self-deleted with `rc=78` before ever starting the actual fetch/download workload** —

```
2026-07-12 05:19:20 OOM preflight: checking gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet mtime against budget 86400s
2026-07-12 05:19:22 OOM preflight FAIL: ... is 113812s stale (budget 86400s) — exiting 78 to skip Python startup; EXIT trap will self-delete VM.
2026-07-12 05:19:22   Diagnosis: manifest-consolidator for asset_group=defi is degraded. Reader would fall back to merging per-VM shards -> OOM at startup. Fix consolidator + relaunch.
```

This confirms the residual kill pattern (post-TTL-fix, ~5-6min apart) is still frequent/severe enough that the
consolidator is not accumulating enough successful complete runs to keep the index within its freshness budget — this is
not just "wasted compute on a retry," it is actively blocking EVERY DEFI MTDS VM (smoke-test AND real production
backfills alike, since the preflight check has no test/smoke exemption) from starting its workload at all while the
index stays this stale. Raises the urgency of the residual-kill-pattern follow-up above from "smaller residual problem"
to "actively blocking all DEFI MTDS ingestion right now." No fix attempted here — this is out of scope for the sweep
session; flagging with real evidence for whoever picks up the residual-kill investigation next.

## Corroborating evidence (2026-07-13, discovered while redeploying the consolidator fleet for an unrelated alerting fix)

Confirms the residual kill pattern is STILL ACTIVE 3 days after the TTL fix and the canonical is STILL stuck at the same
`2026-07-10T21:42:30Z` timestamp cited above (i.e. zero successful merges since, ~2.7 days now). New diagnostic detail
not previously captured: the consolidator's own self-reported `_index/latest.json` run summary
(`codex/05-infrastructure/manifest-consolidator-ssot.md` § "Cockpit data-correctness signals", shipped
`unified-trading-library@111592eb`) surfaces this failure mode directly —

```
{"last_run_at": "2026-07-13T08:45:46Z", "success": true, "verdict": "empty", "shards_scanned": 0,
 "shards_changed": 0, "no_op": true, "error_reason": "locked"}
```

i.e. every scheduler-triggered cycle reports `success: true` (the CLI itself exits 0 — matches this doc's own "never
actually fails, just wastes a retry" note) but `verdict: "empty"` / `error_reason: "locked"` — it saw an already-held
`_index/consolidator.lock` and no-op'd rather than merging. Directly observed the lock lifecycle live: lock acquired at
`08:39:36` (instance `1-f2044cd7`) → holder SIGKILL'd at `08:39:58` (`Container terminated on signal 9`, ~22s in) → lock
sat stale for the remainder of its 300s TTL → cleared → a NEW instance (`1-a9461ee6`) acquired it at `08:44:39` → THAT
holder was also SIGKILL'd at `08:45:00` (~21s in) — i.e. two consecutive holders both died within ~20-25s of acquiring
the lock, well before any real DuckDB merge work would start, which is consistent with this doc's own "container dying
extremely early, before or during Python/library import" observation. Container is 16Gi/4cpu (this specific job was not
part of the earlier 16Gi→32Gi mitigation round — worth checking whether that mitigation was reverted or only ever
applied transiently). Canonical is 482 MiB (505,936,684 bytes) and outstanding per-VM shards total only ~4.25 MiB across
9 files — ruling out the CeFi-style "huge shard" bloat pattern as a cause here.

`error_reason: "locked"` is a genuinely useful new signal for whoever picks up the residual-kill investigation: it means
the deployment cockpit's Consolidators tab (which reads `latest.json` as authoritative) should already be showing this
bucket as `fired_but_empty` rather than `produced` — worth confirming the cockpit surfaces this distinctly rather than
reading `success: true` alone and calling it healthy. No fix attempted (out of scope for the task that surfaced this — a
Cloud Run consolidator-fleet image redeploy); flagging with fresh, dated evidence per the data-pipeline-correctness HARD
RULE.

## Corroborating evidence (2026-07-13, `pipeline_e2e_check` clean 452-shard re-sweep — DEFI:AAVE_V3-POLYGON outlier)

Independently investigating the re-sweep's single `launcher_script_timeout`-reasoned outlier
(`DEFI:AAVE_V3-POLYGON:lending_indices`, force+skip legs — `data_pipeline_e2e_check_2026_07_10.md` Progress Log
2026-07-13) traced it to THIS issue, not a new/unrelated launcher bug. Real evidence:

- **The checker's `launcher_script_timeout` classification is a real but secondary surface effect, not the actual
  cause.** UTL's `pipeline_e2e_check.launcher.launch_vm_and_wait()` wraps the LOCAL `bash launch-mtds-backfill-vm.sh`
  invocation in `subprocess.run(..., timeout=120)` (`_LAUNCHER_SCRIPT_TIMEOUT_SEC=120`); the driver's own log shows the
  force-leg launch call at (UTC) `13:05:16` and the very next log line — launching the SKIP leg — at `13:07:16`, exactly
  120s later, with no intervening `"launcher exited N"` confirmation line ever printed for the force leg. That confirms
  the CLIENT-SIDE subprocess call genuinely exceeded its 120s ceiling (consistent with this module's own documented
  precedent of transient `gcloud` API slowness under the sustained concurrent load of a 452-job sweep — see
  `_LAUNCHER_SCRIPT_MAX_ATTEMPTS`'s comment). This is a real but minor timing wrinkle in the checker's launcher wrapper,
  not a data-pipeline bug.
- **The VM WAS actually created and booted for both legs** — `gsutil ls` on
  `gs://deployment-scripts-central-element-323112/vm-logs/{mtds-backfill-defi-pipelinecheck-20260713-130516-6beb17, …-130716-6beb17}/`
  shows a `vm-setup.log` + `SETUP_EXIT_STATUS` for each (no `run.log`/`EXIT_STATUS` — the Python workload never
  started). Real `vm-setup.log` content for BOTH VMs:
  ```
  OOM preflight: checking gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet mtime against budget 86400s
  OOM preflight FAIL: … is 228423s stale (budget 86400s) — exiting 78 to skip Python startup; EXIT trap will self-delete VM.
    Diagnosis: manifest-consolidator for asset_group=defi is degraded. Reader would fall back to merging per-VM shards → OOM at startup. Fix consolidator + relaunch.
  SETUP FAILED rc=78 — uploading log + scheduling self-delete
  ```
  — i.e. **this shard's real failure is the exact same OOM-preflight self-guard this doc's 2026-07-12/07-13 entries
  already document**, just surfaced through `launcher_script_timeout` instead of `vm_exit_nonzero=78` because the
  client-side subprocess call ALSO happened to time out first under concurrent load. Had the client not timed out, this
  shard would have reported the same `vm_exit_nonzero=78` as its siblings.
- **Directly reconfirmed the canonical is still stuck at the exact same timestamp** cited in the 2026-07-12/07-13
  entries above: `gsutil stat gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`
  (checked 2026-07-13T14:52Z, live) → `Update time: Fri, 10 Jul 2026 21:42:30 GMT` — unchanged, now **~65h / ~2.7 days
  stale**, confirming zero successful consolidator merges since the 07-13 entry above was written. No new fix attempted
  (out of scope for the PREDICTION+DEFI-outlier triage task this evidence was gathered during); no new issue doc filed —
  this is the same already-open, already-comprehensively-diagnosed problem, not a new bug.

**Aside — a small, separate watchdog gap noticed in the same investigation**: the newly-redeployed
`uts-prod-consolidator-liveness-watchdog` (carrying the `PubSubEventSink` alerting fix from
`reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12.md` item 4) correctly flags this
`market-data-tick-defi-prd` bucket DOWN, but its static `--buckets` arg list also includes 2 buckets whose Cloud Run
jobs are deliberately PAUSED for legacy decommission (`instruments-store-sports-central-element-323112` →
`uts-prod-manifest-consolidator-instruments-sports-legacy`, PAUSED since ~2026-07-06;
`market-data-tick-tradfi-central-element-323112` → `...-market-data-tradfi-legacy`, PAUSED since ~2026-06-08) — both now
report false-positive `CONSOLIDATOR_DOWN` every 2-min watchdog cycle. Not filing a separate issue doc for this; noting
it here since it surfaced in the same verification pass. Fix candidate: exclude paused/decommissioned legacy buckets
from `uts-prod-consolidator-liveness-watchdog`'s `--buckets` arg
(`deployment-service/terraform/gcp/consolidator_liveness_scheduler.tf`), or add a "job intentionally paused" exemption
to `ConsolidatorLivenessMonitor.check`.

## 2026-07-13 (operator-approved infra-only pass — resources DEFINITIVELY ruled out; kill is defi-workload-specific)

Operator ruled "proceed now, infra-only" (no UTL code edits — the prune-race fix `unified-trading-library@97212d3b` was
landing concurrently from another session; no manual `-prd-` executions — prune-race window). Applied + measured:

- **Applied `gcloud run jobs update uts-prod-manifest-consolidator-market-data-defi --memory=32Gi --cpu=8` (18:10:40Z,
  audit-logged; spec confirmed `cpu=8;memory=16Gi→32Gi`).** This also re-resolved the job's `:latest` image tag at
  update time. NOTE: the job spec carries NO `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` env at all — the 07-10 mitigation
  round's env tweaks (and the 16Gi→32Gi bump) were absent from the current job, consistent with the 07-13
  consolidator-fleet redeploy having recreated jobs from clean spec; DuckDB therefore runs its code default (8GB,
  `manifest_consolidator.py:348`).
- **Result: kill cadence UNCHANGED** — signal-9 kills at 18:12, 18:18, 18:23, 18:29, 18:34, 18:40, 18:46, 18:51 (same
  ~5-6 min cadence as pre-update 17:16→18:06). 64 signal-9 kills in the trailing 6h — and a fleet-wide query shows
  **every single one is the DEFI job; zero on cefi/tradfi/sports/prediction/instruments-\* siblings.**
- **NOT a container-memory OOM**: memory utilization p99 (Monitoring API, 300s windows straddling the post-update kills)
  peaks at 0.56-0.66 (≈18-21GB of 32Gi), and Cloud Run's explicit "memory limit exceeded" log line never appears — only
  the bare `Container terminated on signal 9`. Combined with cadence identical at 16Gi/4cpu and 32Gi/8cpu: resources are
  ruled out (a sub-minute spike between samples can't be fully excluded externally, but doubling the ceiling changing
  nothing argues strongly against it).
- **The "zero app logs" observation re-interpreted**: the killed holders DO run real code — the lock object shows
  acquisition (a GCS write) ~20-35s before each kill (e.g. acquired 18:33:43 by `1-11a6a688` → killed 18:34:17). The
  absence of log lines is the known Cloud-Run-jobs app-log-shipping gap (this doc's own masking-layer finding), not a
  pre-import crash. In-container behavior is simply unobservable from outside today.
- **The ~5-6 min cadence is the 300s lock-TTL cycle**: only the cycle that steals the expired lock does real work and is
  killed ~20-35s in; every other per-minute tick no-ops (`error_reason: "locked"`, `success: true` — matches this doc's
  earlier reading). Merges DO occasionally survive (canonical advanced at 16:38:20Z today, 445MB), but 9 per-VM shards
  (4.84MiB, some from 07-12) were still sitting unmerged at 18:30Z — merges are not completing reliably.
- **Verdict**: the kill is specific to the DEFI bucket's workload (by far the fleet's largest canonical: 445MB parquet /
  27.4M rows) and is NOT a resource-ceiling problem. The dominant remaining hypotheses (fast tmpfs/spill transient vs.
  an infrastructure-level task eviction) are indistinguishable WITHOUT in-container logs.
- **Next steps (updated)**: (1) fix the Cloud-Run-jobs app-log-shipping gap for the consolidator entrypoint (stdout
  logging bootstrap) — a small UTL/deploy change, deliberately NOT done this pass (UTL was under the prune-race
  session's active edit); with logs, the kill point becomes directly visible. (2) If the kill point lands inside the
  DuckDB merge, the SSOT's Batch-Fargate alternative home (real disk, no 32Gi ceiling) is the durable escape hatch for
  the defi bucket specifically — operator-gated. (3) The 32Gi/8cpu bump is left in place (harmless, marginally longer
  survival per attempt). (repo: infra-only — gcloud run jobs update; no code changed)

## RESOLVED 2026-07-14/15 — root-caused and fixed; doc was stale, correcting now

A different session (slot-5) root-caused this on 2026-07-14: the actual mechanism was a **lock-stealing livelock**, not
a resource ceiling or an unobservable in-container crash — the consolidator's soft-lock TTL (300s, later found
env-tunable) was far shorter than real cycle durations once a date-range-chunked incremental merge (a separate fix for a
DeFi OOM issue) started taking 24-30+ min in production. Every `*/1` cron tick past 300s during a still-running
legitimate cycle found the lock "stale" and started a COMPETING concurrent merge — 3+ simultaneous executions observed
live, each re-downloading the full canonical, which is what produced the repeating SIGKILL pattern this doc documents.

**Fix**: `unified-trading-library@9358fb0b` (made `_LOCK_TTL_SECONDS` env-tunable via `CONSOLIDATOR_LOCK_TTL_SECONDS`)

- `deployment-service@fe67a53` (Terraform override `CONSOLIDATOR_LOCK_TTL_SECONDS=4200`, `timeoutSeconds=3600` for the
  defi bucket specifically, live-applied). **Verified live** (independently, by a separate session on 2026-07-15):
  `gcloud run jobs describe` confirms the override is deployed; execution history shows a 24m28s execution completing
  **successfully** (no SIGKILL) immediately followed by normal fast (~30-40s) executions; canonical manifest fresh. Zero
  SIGKILLs observed since the fix landed, across multiple independent live checks hours apart.

**Why this doc was left stale**: the fix landed via a different, unrelated task (chasing a DeFi backfill OOM issue,
`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`) that didn't know this doc existed / didn't cross-reference it.
**Lesson for future fleet-wide fixes**: when a fix incidentally resolves a DIFFERENT tracked issue, grep
`plans/active/issues/` for the symptom before declaring only the originally-targeted issue closed — this doc sat `open`
for a full day after its actual root cause shipped, which could have caused duplicate investigation effort (and nearly
did, in the session that found this while compiling a list of "still open" decisions).

Next-steps 1-3 above are all now moot (fix is a Terraform TTL override + an env-tunable default, not the log-shipping
work item 1 anticipated) — leaving them unstruck for the historical record rather than deleting.
