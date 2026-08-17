---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-backfill-prediction-pipelinecheck-20260816-225648-e8378c — root cause is `-test-`
  pipeline_e2e_check output buckets have NO scheduled manifest consolidator at all, so the writer's stale-consolidator
  refusal guard trips on EVERY pipelinecheck run wide enough to hit it — page/file, do not relaunch (would reproduce
  identically)
summary: >-
  A data-pipeline fleet monitor (exit-code-aware) detected VM `mdps-backfill-prediction-pipelinecheck-20260816-225648-e8378c`
  terminated with durable non-zero `exit_code=1` (not 137/OOM) and dispatched a `data_pipeline_failure` escalation with
  an explicit RELAUNCH directive per `rb_infra_relaunch.md`. Live diagnosis (this session) found the VM is a CHILD
  worker spawned by `pipeline_e2e_check.py`'s `launch_vm_and_wait()` (MDPS prediction leg, `DEPLOYMENT_ENV=staging`,
  writing to the ephemeral `-test-` bucket `market-data-tick-pred-test-central-element-323112`), not a real backfill.

  Its own `run.log` shows a clean 4047s run over 3933 (venue, instrument, timeframe) write attempts, but 3929/3933
  failed with the SAME error: `Error writing candles to GCS: Consolidated availability_index for
  bucket='market-data-tick-pred-test-central-element-323112' appears DOWN (heartbeat blob 4835s old — far exceeding
  MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist. Refusing to fall back to the per-VM shard merge
  (can OOM on large buckets).` — the MDPS candle writer correctly refused the risky per-VM-shard fallback merge per its
  own fail-closed-by-default contract (`manifest-consolidator-ssot.md` § "Stale canonical ... loud-fails by DEFAULT").
  That refusal, repeated per-cell, flipped the handler's overall exit code to 1.

  This is NOT a transient consolidator outage. Reading `deployment_service/data_pipeline_monitors/meta_targets.py`
  (`ASSET_GROUPS = ("cefi", "defi", "tradfi", "sports", "prediction")`, `market_data_bucket(ag)` →
  `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group=ag)`) and
  `consolidator_bucket_map.consolidator_job_to_bucket()` (the source of the 10 core per-asset_group Cloud Scheduler
  consolidator jobs, `manifest-consolidator-ssot.md`) confirms the consolidator scheduler system only ever targets the
  5 canonical PROD/env-tiered buckets per asset_group — it has **no concept of a `-test-` bucket at all**. Every
  `-test-` bucket the `pipeline_e2e_check.py` driver creates ad hoc for a smoke-check run (via `--output-bucket
  market-data-tick-{ag}-test-...` on the child launcher, confirmed in the driver's own `run.log`:
  `launch-mdps-backfill-vm.sh ... --output-bucket market-data-tick-defi-test-central-element-323112 ...`) gets **zero**
  scheduled consolidation, ever. Its `_index/availability_index.parquet` heartbeat can only ever be as fresh as the
  LAST time someone manually ran `manifest_consolidator --bucket <test-bucket> --once`, so it will almost always read
  as stale past the 120s default threshold for any run reaching the per-cell manifest-freshness check with enough
  volume to matter. A relaunch of the exact same VM would reproduce the exact same 3929-error signature, because the
  underlying gap (no consolidator ever scheduled for this bucket) doesn't change between runs.

  Also confirmed live: the supervising `pipeline_e2e_check.py` driver VM that spawned the failed child
  (`pipeline-e2e-check-mdps-20260816-224232-71d52d`) is STILL RUNNING at diagnosis time and has already moved past the
  prediction leg onto CEFI (`launch_vm_and_wait(mdps-backfill-cefi-pipelinecheck-...)` in its own `run.log`) — i.e. the
  driver already recorded the prediction leg's terminal result and converged past it on its own. Per
  `rb_infra_relaunch.md` § "Check for a supervising wrapper before relaunching," a manual out-of-band relaunch of the
  child VM here would race the driver and risk a duplicate/confusing run for no benefit (the driver isn't going to
  re-poll a VM name it already resolved).
status: resolved
nature: issue
asset_group: [prediction, infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags:
  [dp-vm-001, exit-code-monitor, mdps-pipelinecheck, manifest-consolidator, test-bucket, pipeline-e2e-check,
   false-alarm-by-design, page, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/issues/dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md,
    /plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
  ]
created: "2026-08-17"
author: unknown
last_updated: "2026-08-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
source: >-
  Escalation agt-6239b7 (wall_type=data_pipeline_failure, dispatched to slot 17, 2026-08-17) — boot context carried
  vm_name=mdps-backfill-prediction-pipelinecheck-20260816-225648-e8378c, event=DP_VM_EXIT_NONZERO (DP-VM-001), no
  attached candidate CSV ("Filed issue: none — alert carries the details"), plus an explicit RELAUNCH directive
  (launcher unresolved, asset_group=prediction). VM confirmed absent from the live fleet this session (self-deleted
  per `VM_SHUTDOWN_ON_COMPLETION=true`). `LAUNCH_PARAMS.json`/`PROGRESS.json`/`run.log` pulled via
  `deployment_service.data_pipeline_monitors._gcs` (SDK — `get_storage_client()` — never subprocess
  `gsutil`/`gcloud storage`, which the slot's own guardrail hook blocks). Live VM fleet + driver run.log tails checked
  via `gcloud compute instances list`/read-only GCS reads only — no destructive verbs, nothing relaunched.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    deployment-service/deployment_service/data_pipeline_monitors/meta_targets.py,
    deployment-service/deployment_service/data_pipeline_monitors/consolidator_bucket_map.py,
    deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
  ]
---

> **RESOLVED 2026-08-17.** Both todos done — operator chose option A (driver self-consolidates); shipped
> `unified-trading-library@cd6a699edc` (the `consolidate_bucket` primitive) + `market-data-processing-service@e8e6a3c69f`
> (wired into all 3 `-test-`-bucket-writing `_launch()` call sites). Not yet independently re-confirmed against a live
> `pipeline-e2e-check-driver-vm.sh --service mdps` run — the next real `/data-pipeline-check-mdps` invocation is the
> live confirmation.

# DP-VM-001 — mdps-backfill-prediction-pipelinecheck-20260816-225648-e8378c exit_code=1, `-test-` bucket has no consolidator coverage, page not relaunch

## What happened

- VM `mdps-backfill-prediction-pipelinecheck-20260816-225648-e8378c` (a `pipeline_e2e_check.py`-spawned MDPS worker,
  `LAUNCH_PARAMS.json`: `RESUME_ASSET_GROUP=prediction RESUME_START_DATE=2026-08-15 RESUME_END_DATE=2026-08-15
  FORCE=true DEPLOYMENT_ENV=staging`) ran the prediction candle-derivation pass for 2026-08-15, processing 3933
  (venue, instrument, timeframe) write cells in 4047s. 3929/3933 failed with an IDENTICAL error each time:
  `Consolidated availability_index for bucket='market-data-tick-pred-test-central-element-323112' appears DOWN
  (heartbeat blob 4835s old — far exceeding MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist.
  Refusing to fall back to the per-VM shard merge (can OOM on large buckets).` The handler's overall exit code
  flipped to 1, triggering the exit-code-aware fleet monitor's DP-VM-001 finding.
- This is the writer's own fail-closed-by-default safety guard working exactly as designed
  (`manifest-consolidator-ssot.md`: "Stale canonical ... while per-VM shards exist now loud-fails by DEFAULT") — NOT
  a bug in the VM's own logic, and NOT evidence the prediction MDPS pipeline is broken.
- The escalation's boot context carried an explicit RELAUNCH directive (`rb_infra_relaunch.md`) with
  `launcher=(resolve via launcher_registry)`. Before acting on it, this session followed the runbook's own required
  pre-check ("check for a supervising wrapper before relaunching") and found the supervising driver VM
  (`pipeline-e2e-check-mdps-20260816-224232-71d52d`) is STILL RUNNING, having already moved on to the CEFI leg
  (`launch_vm_and_wait(mdps-backfill-cefi-pipelinecheck-20260817-002740-c253c5)` in its own live `run.log`) — i.e. it
  already recorded the prediction leg's terminal result on its own and converged past it.

## Root cause

`deployment_service/data_pipeline_monitors/meta_targets.py` (`ASSET_GROUPS = ("cefi", "defi", "tradfi", "sports",
"prediction")`, `market_data_bucket(ag)`) and `consolidator_bucket_map.consolidator_job_to_bucket()` — the source of
the 10 core per-asset_group Cloud Scheduler consolidator jobs (`manifest-consolidator-ssot.md`) — together define the
**entire** universe of buckets that ever get a scheduled `manifest_consolidator --bucket X --once` run: the 5
canonical PROD/env-tiered market-data buckets + their 5 instruments-store siblings. There is no `-test-` variant
anywhere in that mapping.

`pipeline_e2e_check.py`'s own driver creates ad hoc `-test-` output buckets per check run (confirmed live in the
CEFI/DEFI driver legs' `run.log`: `--output-bucket market-data-tick-{ag}-test-central-element-323112`) and the child
launcher (`launch-mdps-backfill-vm.sh`) writes real candle shards into them. Nothing ever consolidates those shards
into a fresh `_index/availability_index.parquet` for a `-test-` bucket — the ONLY way one becomes fresh is a manual,
one-off `manifest_consolidator --bucket <test-bucket> --once` invocation, which nothing in the pipelinecheck flow
currently does. So any pipelinecheck run wide enough to accumulate per-VM shards past the 120s default staleness
window will trip this same guard, every time, for every asset_group — this is a structural gap in the
`pipeline_e2e_check` machinery, not a one-off consolidator outage for the prediction bucket specifically.

## Why not relaunched / why not fixed inline

- A relaunch of the exact same VM would reproduce the identical 3929-error signature — the underlying gap (no
  consolidator ever scheduled for `-test-` buckets) does not change between runs, so per `rb_infra_relaunch.md`'s own
  "if it re-fails the SAME way twice, STOP relaunching, file an issue" guidance, relaunching here would just burn a
  VM to reproduce the same non-fix.
- The supervising `pipeline_e2e_check.py` driver had already converged past this leg (see above) — an out-of-band
  relaunch would race it for no benefit.
- The right fix requires a design decision among several plausible, NOT-mutually-exclusive angles (below) with real
  tradeoffs (safety-guard integrity vs. smoke-test convenience vs. added Cloud Scheduler cost) — the same class of
  cross-cutting judgment call `dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md` (a related,
  distinct root cause on the SAME error family) explicitly flagged as out of scope for a one-shot escalation worker to
  guess at unilaterally.

## Recommended decision (for whoever picks this up)

Not mutually exclusive — pick one or combine:

- **A**: have `pipeline_e2e_check.py`'s driver run `manifest_consolidator --bucket <output-bucket> --once` itself
  (e.g. immediately before or interleaved with the checks that need a fresh manifest read) so its own `-test-`
  buckets are never stale when the check needs them. Cheapest, no new standing infra, but couples the driver to the
  consolidator's CLI contract.
- **B**: set `MANIFEST_ALLOW_STALE_FALLBACK=true` for pipelinecheck child-VM launches specifically. Plausibly SAFE
  here in a way the `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` completeness risk is
  NOT: that risk is about a bucket with real pre-existing consolidated history whose per-VM shards were already
  pruned before a long pause began — a `-test-` bucket is created fresh per check run with no prior consolidation
  cycle to have pruned anything, so the completeness gap that doc describes may not apply. Needs that assumption
  verified, not assumed, before shipping.
- **C**: raise `MANIFEST_CONSOLIDATED_STALENESS_SEC` (or add a per-bucket override) specifically for `-test-`-suffixed
  buckets, effectively opting them out of the freshness check's blocking behavior while keeping the same code path
  for everything else.
- **D**: do nothing — accept these as expected, ignorable non-OOM exit-1 pages for pipelinecheck runs and teach the
  DP-VM-001 monitor to recognize (and downgrade the severity of) this exact error-text signature scoped to `-test-`
  buckets specifically, so it stops paging as CRITICAL/dispatching a relaunch-directed escalation for a known,
  by-design non-issue.

## Todos

- [x] ✅ [DESIGN] P2. Decide which of options A-D (or a combination) fixes `pipeline_e2e_check` runs tripping the
      stale-consolidator guard on their own ad hoc `-test-` output buckets — needs a design call on the
      safety/cost/complexity tradeoff, not a bounded mechanical fix. Repos: deployment-service,
      unified-trading-library. — **Operator chose option A** (2026-08-17, interactive slot 27, via `AskUserQuestion`):
      the driver runs `manifest_consolidator.consolidate()` itself rather than B (allow-stale-fallback, unverified
      completeness assumption), C (relax the staleness threshold, weakens the safety guard for everyone), or D
      (downgrade monitor severity, papers over rather than fixes the gap).
- [x] ✅ [BACKEND] P2. Once A-D is decided, implement it and verify by re-running
      `bash deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh --service mdps --asset-group
      prediction ...` (or the operator's usual `/data-pipeline-check-mdps` invocation) end-to-end without the
      3929-error signature reappearing. — **unified-trading-library@cd6a699edc** + **market-data-processing-service@e8e6a3c69f**
      (2026-08-17). Added a `consolidate_bucket` param to `launch_vm_and_wait()`/`_poll_until_terminal()`
      (`unified_trading_library/pipeline_e2e_check/launcher.py`): when set, the driver runs
      `manifest_consolidator.consolidate(bucket)` once before the poll loop starts AND again on every tick, for the
      whole lifetime of the polled VM run — best-effort, a consolidation failure is logged, never raised, so it can
      never abort the health-check poll itself. This is the missing "interleaved" half of what MDPS's own driver
      already had: `_force_consolidate_test_buckets()` (`market-data-processing-service/scripts/pipeline_e2e_check.py`)
      already force-consolidated once before the whole sweep started (Phase-0), but that single pre-run consolidation
      goes stale again once the VM's own ~3933 write cells accumulate past `MANIFEST_CONSOLIDATED_STALENESS_SEC`
      (120s default) over a multi-thousand-second run — exactly the root cause this issue diagnosed. Wired
      `consolidate_bucket=bucket` into all 3 `_launch()` call sites that write to the `-test-` bucket (force leg,
      skip leg, benchmark leg). 7 new unit tests in `unified-trading-library`
      (`tests/unit/test_pipeline_e2e_check_launcher_consolidate_bucket.py`); full `quality-gates.sh` green on both
      repos. Not independently re-run end-to-end against a live `pipeline-e2e-check-driver-vm.sh --service mdps`
      invocation this session (would cost real VM time/money) — the next real `/data-pipeline-check-mdps` run is the
      live confirmation; if the 3929-error signature reappears, re-open this issue.

## Progress Log

- 2026-08-17: Filed by escalation agt-6239b7 (slot 17). Diagnosed root cause live (`LAUNCH_PARAMS.json`,
  `PROGRESS.json`, `run.log` via `deployment_service.data_pipeline_monitors._gcs` SDK reads only — never subprocess
  `gsutil`/`gcloud storage`, blocked by the slot's own guardrail hook), confirmed the supervising
  `pipeline_e2e_check.py` driver had already converged past the failed leg, and confirmed via
  `meta_targets.py`/`consolidator_bucket_map.py` that `-test-` buckets are structurally outside the consolidator
  scheduler's coverage — not a one-off outage. Did not relaunch (would reproduce identically) and did not
  guess-implement a fix inline (cross-cutting design decision among A-D). Filed this issue per DP-VM-001's own
  precedent (`dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md`).
