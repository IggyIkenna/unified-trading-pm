---
doc_type: issue
title: >-
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (defi cron) — new root cause, distinct from prior recurrences: a stuck
  100+min Cloud Run execution + an unexplained, unprotected pause the liveness watchdog couldn't see (2026-08-21)
summary: >-
  Escalation triage (escalation agt-12d9a1, wall_type=data_pipeline_failure) for a CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-004) page on `uts-prod-manifest-consolidator-market-data-defi-cron`.
  UNLIKE the four prior recurrences (tradfi/prediction 2026-07-29, tradfi/prediction 2026-07-31, defi 2026-08-07 — all
  a plan-tracked VM deliberately pausing the cron via raw `gcloud` to protect its own in-flight canonical rewrite), this
  pause has NO correlated live protective work: no maintenance window was ever registered AND no running VM/plan claims
  it. Root cause is two independent things landing together: (1) a Cloud Run Job execution
  (`uts-prod-manifest-consolidator-market-data-defi-p6hrc`, started 2026-08-21T18:57:05Z) reclaimed an EARLIER stale
  lock (age 9048.7s > the defi 9000s TTL) at 18:57:39Z, found the canonical index missing its
  `consolidator_content_write_at` marker ("out-of-band rewrite?"), and is consequently running a full non-pruned
  106-chunk merge over the entire 2018-01-01..2026-08-21 range instead of a normal ~35s incremental merge — genuinely
  still in flight per Cloud Run's own execution status ("Waiting for execution to complete") 100+ minutes later,
  suppressing the consolidator-liveness watchdog's auto-resume (defi's own generous 9000s in-flight horizon reads the
  still-fresh lock as proof-of-life, not staleness) — a real gap but NOT itself the page; (2) separately, an unexplained
  raw pause/resume flapping cycle (all via `unified-trading-sa`, 5 pause/resume round-trips between 19:02-19:11Z) ended
  with the cron left PAUSED at 19:11:56Z with no window ever registered — the actual DP-WATCHER-004 trigger. Because the
  in-flight merge is a Cloud Run Job execution independent of the Cloud Scheduler's enable/pause state (the scheduler
  only gates FUTURE HTTP-triggered invocations, not an already-running execution), resuming the cron could not race
  the in-flight merge — every run trigged while the lock is still fresh (<9000s) just no-ops (confirmed: 15 such
  30-42s skip-cycles observed 19:00-19:11 while the earlier stale lock predecessor was held). Resumed the cron directly
  (no maintenance window needed — nothing legitimately depends on the pause).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [deployment-service, unified-trading-library, market-tick-data-service]
scope: [engineer]
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
tags:
  [
    data_pipeline_failure,
    dp-alerts,
    consolidator,
    scheduler,
    stuck-lock,
    stale-lock,
    liveness-watchdog-blind-spot,
    canonical-index-metadata-loss,
  ]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_defi_recurrence_2026_08_07.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md,
  ]
created: 2026-08-21
parent_epic: manifest_master
assigned_vm: planning
locked_by:
priority: P2
source: >-
  data_pipeline_failure escalation agt-12d9a1 (dp-fleet-monitor -> slot-31), CONTEXT: "CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-004) -- manifest-consolidator scheduler
  'uts-prod-manifest-consolidator-market-data-defi-cron' is PAUSED (not -legacy-)."
resolved_by: slot-31 (dp_consolidator_scheduler_paused_defi_stuck_lock-001, 2026-08-21)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-21
---

> **🟢 ARCHIVED 2026-08-22 (slot-9).** The scheduler-state watchdog follow-up and its regression coverage shipped in
> `unified-trading-library@9956271a9`; the issue is resolved with zero open todos.

# DP_CONSOLIDATOR_SCHEDULER_PAUSED — defi cron, stuck lock + unprotected pause (2026-08-21)

## What I found

1. **Live GCP state at escalation time**: `uts-prod-manifest-consolidator-market-data-defi-cron` (`asia-northeast1`) =
   `PAUSED`, `userUpdateTime: 2026-08-21T19:11:55.938445Z`. `scheduler_maintenance status` on
   `market-data-tick-defi-prd-central-element-323112` read "no live window — safe to pause/resume freely" — no
   maintenance window ever registered for this pause.
2. **Cloud Audit Logs** (`protoPayload.resourceName:"...market-data-defi-cron"`, last 2h) showed 5 rapid pause/resume
   round-trips between 19:02:41Z and 19:11:56Z, all by `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`
   (every call doubled ~200-500ms apart — consistent with the Cloud Scheduler client's own transient-error retry, not a
   second actor), ending on PAUSED at 19:11:56Z with nothing since (verified stable for 90+ minutes through
   escalation-resolution time).
3. **consolidator-liveness watchdog reported `market-data-tick-defi-prd-central-element-323112 -> ok` continuously**
   through 20:36Z despite the cron being paused since 19:11:56Z and the job's last real execution having started at
   18:57:05Z (90+ min prior) — confirmed via a read-only diagnostic against the live UTL functions:
   `heartbeat_age_sec=5941.6` (`_consolidator_heartbeat_age_sec`, ~99min stale — far past the fast-tier 300s DOWN
   threshold), `per_vm_shards_exist=True` (not a genuinely-empty bucket), but `consolidator_cycle_in_flight=True` — the
   held consolidator lock (`_index/consolidator.lock`, `started_at=2026-08-21T18:57:39Z`, `instance=1-5995396f`) reads
   as younger than defi's own 9000s in-flight horizon (`consolidator_inflight_horizon_for_bucket`), so `check()` never
   escalates to `STATUS_DOWN` and the Terraform-enabled `--auto-resume` actuator (`consolidator_liveness_scheduler.tf`
   fast tier) never gets a chance to fire. This is a genuine, if narrow, watchdog blind spot: as long as a single
   execution holds the lock for up to its full 9000s TTL, an ACCIDENTALLY-paused cron looks indistinguishable from a
   legitimately slow merge, no matter how long the scheduler itself has been paused.
4. **Root-caused the held lock to a real, still-in-flight execution, not a crashed/orphaned one**:
   `uts-prod-manifest-consolidator-market-data-defi-p6hrc` (started `2026-08-21T18:57:05Z`) is Cloud Run's own reported
   status `Waiting for execution to complete` (i.e. not Failed/Cancelled) — its logs show it reclaimed an EARLIER stale
   lock at 18:57:39 (`age=9048.7s > TTL=9000.0s`), then hit
   `WARNING: canonical for market-data-tick-defi-prd-central-element-323112 has NO consolidator_content_write_at marker
   (out-of-band rewrite?) — merge cutoff UNPROVABLE: merging all 2 shard(s), pruning NOTHING this cycle`, then
   `phase=shards_downloaded rows_in=162470515` and `phase=duckdb_merge_start ... chunk_days=30 chunks=106
   date_range=2018-01-01..2026-08-21` at 18:59:37Z. A full non-pruned 106-chunk DuckDB merge over the ENTIRE 2018-2026
   history (vs. the normal ~35s incremental merge every other cycle this hour ran) genuinely explains a 100+ minute
   runtime on a 24GB/4-thread Cloud Run Job — not necessarily a hang. Every scheduled run between 19:00-19:11 (15
   executions, all 30-42s) correctly took the lock-held skip branch and no-op'd rather than racing this merge.
5. **Because Cloud Scheduler's pause/resume only gates FUTURE HTTP-triggered invocations — it has no effect on an
   ALREADY-RUNNING Cloud Run Job execution** — resuming the cron cannot race `p6hrc`'s in-flight merge: any newly
   triggered run will hit the exact same lock-held skip branch the 19:00-19:11 executions already demonstrated, until
   either `p6hrc` finishes and releases the lock, or the 9000s TTL genuinely expires. This is what makes a plain resume
   (rather than registering a maintenance window, as the four prior recurrences did) the correct, safe fix here: unlike
   those incidents, nothing here is legitimately relying on the pause to prevent a race.

## Why it matters

Distinct root cause from the four prior DP-WATCHER-004 recurrences — those were all a plan-tracked VM's deliberate,
unregistered `gcloud scheduler jobs pause` to protect its OWN in-flight canonical rewrite (fix: register a retroactive
maintenance window, don't resume). This one has no such correlated protective purpose: the pause looks like an
unexplained flap (5 rapid pause/resume round-trips, all `unified-trading-sa`, likely an interrupted/retried
maintenance-adjacent script — not identified further; out of scope to trace the exact caller for a one-shot escalation)
that happened to land on PAUSED and then simply sat there, unprotected, for 90+ minutes with no self-healing path,
because the SEPARATE stuck-lock condition blinded the liveness watchdog's own auto-resume actuator. Two real,
independent gaps surfaced:

- **Liveness-watchdog blind spot (not fixed here, scope too broad for one-shot)**: `consolidator_cycle_in_flight`'s
  "held lock younger than the in-flight horizon = proof-of-life" heuristic cannot distinguish "legitimately slow merge"
  from "accidentally-paused cron whose last execution happens to still be mid-merge" — as designed, a paused scheduler
  with an in-flight-but-long-running execution is invisible to DOWN detection for up to the FULL horizon (9000s for
  defi), during which auto-resume can never fire even though the actual page condition (PAUSED, no window) is already
  known via the separate DP-WATCHER-004 detector. A future fix could have the liveness watchdog ALSO check scheduler
  state directly (like DP-WATCHER-004 already does) rather than relying solely on heartbeat/lock proxies, but that
  overlaps two detectors' scope and needs a design call, not a reactive one-shot patch.
- **Canonical index metadata loss (not fixed here, scope too broad + no confirmed writer)**: the
  `NO consolidator_content_write_at marker (out-of-band rewrite?)` warning means SOMETHING rewrote
  `_index/availability_index.parquet` for the defi bucket without carrying forward the required custom metadata,
  forcing this cycle into an expensive full non-pruned merge. Candidate recent defi-bucket writers (canonical-migration
  VMs, the N5r/N6r venue/itype-canon swap apply step, `defi_track01_per_instrument_and_canon_id`) were not confirmed as
  the actual culprit within this escalation's scope — tracked as a todo below rather than guessed at.

## What I did

1. Diagnosed via the sanctioned UTL primitives (read-only: `_consolidator_heartbeat_age_sec`,
   `_per_vm_shards_exist`, `consolidator_cycle_in_flight`, `read_consolidator_lock_age_sec`'s underlying lock blob) plus
   `gcloud scheduler jobs describe` / `gcloud logging read` / `gcloud run jobs executions list` — no writes until the
   resume action below.
2. Confirmed the in-flight execution (`p6hrc`) is a real, still-active (per Cloud Run's own status) full-history merge,
   not a crashed/orphaned process — did NOT delete the lock or kill/cancel the execution.
3. Resumed the cron directly (`gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron
   --location=asia-northeast1 --project=central-element-323112`) — no maintenance window needed since nothing
   legitimately depends on the pause. Verified: `state=ENABLED`, `userUpdateTime=2026-08-21T20:48:43Z`.
4. No code shipped — this was a pure live-infra remediation (a scheduler resume), mirroring the prior recurrences'
   own "no code change, no git push" precedent for this alert class.

## Recommended decision

No further paging-remediation action needed for THIS occurrence — cron is `ENABLED`, and the in-flight merge is
unaffected by the resume (any new run will safely no-op until the lock clears). Two follow-ups worth tracking (not
fixed here, scope too broad for a one-shot escalation):

## Todos

- [x] ✅ [OPS] P1. **Resumed the defi cron — DONE live 2026-08-21T20:48:43Z.** No code shipped; pure infra action
      (`gcloud scheduler jobs resume`). Verified `state=ENABLED`. Confirmed safe against the in-flight
      `p6hrc` merge (scheduler pause/resume only gates future triggers, not an already-running execution; a fresh
      lock still blocks any newly-triggered run from racing it). (repo: NA)
- [x] ✅ [SCRIPT] P3. **Identified + retrofitted — market-tick-data-service@d1cc2c4b7b.** Confirmed candidate:
      `market_tick_data_service/scripts/defi_manifest_venue_itype_canon_swap.py` (N5r/N6r) is the only currently-live
      script matching this todo's candidate list that rewrites `_index/availability_index.parquet` directly — REMOVE
      via a raw `client.conditional_upload_bytes()` CAS write, ADD via `ManifestWriter(per_vm_shards=False)`. Traced
      both write paths: neither `conditional_upload_bytes` (gcp.py) nor `ManifestWriter.write()`'s underlying
      `client.upload_bytes()` call (`_writer_io.py`) passes a `metadata=` kwarg, so either write strips the canonical
      blob's existing custom GCS metadata (incl. `consolidator_content_write_at`) unconditionally — reproduces the
      exact "out-of-band rewrite?" symptom. **Caveat (measured, not assumed)**: this swap's own `defi_manifest_venue_
      itype_canon_swap_execution_2026_08_10.md` todo (e) apply was still `[ ]` unexecuted against prod as of its last
      Progress Log entry (2026-08-17) — I could NOT confirm this swap is what fired the 2026-08-21T18:57:39Z marker
      loss specifically (no audit-log trace attempted this session); `defi_track01_per_instrument_and_canon_id` and
      `canonical-migration-defi-rebuild-*` VMs named in this todo's original candidate list were grepped and found to
      have no live script/launcher matching those names any more (likely archived after their migration completed).
      Fixed preemptively regardless: added `read_preserved_metadata()`/`restamp_preserved_metadata()` (best-effort,
      native-GCS `blob.patch()` metadata-only restamp, mirrors `manifest_consolidator.py`'s own Tier-2 touch pattern)
      wired into `apply()`'s snapshot→REMOVE→ADD sequence, so the swap now carries the pre-write
      `consolidator_content_write_at`/`consolidator_run_at` markers forward whenever it does eventually run against
      prod. 8 new unit tests (`read_preserved_metadata`/`restamp_preserved_metadata`: key-filtering, no-native-client
      no-op, merge+patch, empty-preserved no-op, patch-failure-never-raises), full `quality-gates.sh` green, SHA
      ancestry-verified on `live-defi-rollout`. (repo: market-tick-data-service)
- [x] ✅ [SCRIPT] P3. The consolidator-liveness watchdog now reads the live scheduler state when a stale heartbeat
      coincides with an in-flight merge, so an accidentally-paused cron is reported DOWN instead of remaining
      invisible for the full in-flight horizon (9000s for defi). Existing lock-based protection remains for ENABLED or
      unknown scheduler state. Shipped `unified-trading-library@9956271a9`; added regression coverage for the
      stale-heartbeat + fresh-lock + PAUSED-cron case. Evidence: `bash scripts/quality-gates.sh` — 7,256 tests passed,
      basedpyright 0 errors/0 warnings, all quality gates passed. (repo: unified-trading-library)
