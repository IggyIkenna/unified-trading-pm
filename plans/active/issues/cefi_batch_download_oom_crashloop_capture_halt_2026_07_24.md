---
doc_type: issue
title:
  "CeFi raw-tick batch capture appears HALTED since >=2026-07-21 -- Cloud Run job
  uts-prod-market-tick-data-service-cefi-t1-recon crash-looping on signal 9 (SIGKILL/OOM) since >=2026-07-23, before any
  venue download begins"
summary: >-
  Found via the /data-pipeline-reconciliation --asset-group cefi run's own Phase-0 manifest read: `capture_status` by
  `date` collapses from a steady ~1,000-1,200 captured/day baseline (through 2026-07-20) to 5 (2026-07-21) then ZERO
  captured AND zero attempted_failed for three straight days (2026-07-22/23/24) -- zero of both means no write attempt
  landed at all, not merely that attempts are failing. The corpus-wide `attempted_at` maximum across the full
  9,045,162-row cefi manifest is 2026-07-24T01:31:59Z, ~23h stale at probe time. Followed up with read-only `gcloud
  scheduler/run/logging` checks against central-element-323112: the primary cefi triggers (0600/0900 UTC crons) are
  ENABLED and firing on schedule, but the Cloud Run Job they invoke (`uts-prod-market-tick-data-service-cefi-t1-recon`,
  4 CPU / 8Gi memory) logs "Container terminated on signal 9" (SIGKILL, consistent with OOM) within ~10-40s of every
  execution since at least 2026-07-23, before any per-venue download work begins -- confirmed on both the 06:00 and
  09:00 UTC executions for 07-23 and 07-24. The 07-21/22 failures show a different, earlier-stage signature (a single
  bare ERROR log with no INFO bootstrap output at all) that was NOT confirmed to be the same regression. This is NOT
  documented anywhere in the actively-worked cefi migration issue docs reviewed this run
  (`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` discusses OOM kills of a SEPARATE manifest-dedup
  script on a shared operator dev host and, separately, on a dedicated e2-standard-8 VM -- both explicitly different
  infrastructure from this isolated, 8Gi-limited Cloud Run Job). Filed per the workspace's data-pipeline-correctness
  HARD RULE (a live production capture outage is a BIG finding requiring operator notification, which this run also did
  in its final chat response).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, capture-halt, oom, cloud-run, data-pipeline-correctness, manifest, crash-loop]
related:
  [
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_07_24.md,
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_07_20.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-07-24
parent_epic: cefi_master
priority: P0
source: >-
  /data-pipeline-reconciliation --asset-group cefi (raw-tick layer) dispatched sub-agent run, 2026-07-24/25 -- an
  anomaly this run's own Phase-0 manifest read surfaced (not something it was dispatched to look for), followed up with
  a read-only, targeted GCP infra check per the skill's own "grep-then-READ, not grep-then-conclude" discipline.
resolved_by:
locked_by:
assigned_vm:
code_refs:
  [
    market-tick-data-service (op=download mode=batch handler,
    service unclear which module -- not identified this run),
    deployment-service/scripts/vm/ (not applicable -- this is a Cloud Run Job,
    not a VM),
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# CeFi raw-tick batch capture appears HALTED since >=2026-07-21 -- Cloud Run job crash-looping on signal 9

## What is measured, and how confident each part is

### (a) HIGH CONFIDENCE -- the manifest shows the estate has stopped growing

Full-corpus cefi manifest read (`read_availability_index`, filters=[("asset_group","==","cefi")], 9,045,162 rows,
fully-consolidated index, 28.6s old at read time -- not a stale fallback):

| date       | attempted_failed | captured | empty_confirmed | expected_unattempted |
| ---------- | ---------------- | -------- | --------------- | -------------------- |
| 2026-07-18 | 127              | 1,204    | 1,765           | 16,606               |
| 2026-07-19 | 112              | 1,203    | 1,789           | 16,581               |
| 2026-07-20 | 118              | 1,227    | 1,745           | 16,571               |
| 2026-07-21 | **0**            | **5**    | 1,193           | 17,481               |
| 2026-07-22 | **0**            | **0**    | 1,182           | 17,484               |
| 2026-07-23 | **0**            | **0**    | 1,182           | 17,484               |
| 2026-07-24 | **0**            | **0**    | 1,182           | 17,484               |

Corpus-wide `attempted_at` maximum (across all 8,901,202 non-blank values): **`2026-07-24T01:31:59.195992+00:00`** --
~23h stale at probe time (`~2026-07-25T00:41Z`). `_index/per_vm/` (the per-VM staging area a healthy capture writer
continuously deposits shards into for the consolidator to merge) contains exactly **1 file**, and that file
(`_legacy_seed.parquet`) is the Surface-C dedup migration script's own output artifact, not a live writer's shard.

### (b) HIGH CONFIDENCE -- the crons are enabled and firing, so the trigger layer is not the problem

```
gcloud scheduler jobs list --project=central-element-323112 --location=asia-northeast1
```

`uts-prod-market-tick-data-service-cefi-t1-schedule` (`0 6 * * *`, ENABLED, lastAttemptTime=2026-07-24T06:00:01Z) and
`market-tick-daily-trigger` (`0 9 * * *`, ENABLED, lastAttemptTime=2026-07-24T09:00:06Z) both fired on schedule through
2026-07-24. (A differently-named job, `market-tick-cefi-daily-download`, is `PAUSED` since `2026-07-16T07:46:21Z` --
over a week before the cliff started; almost certainly a pre-existing/superseded job, not implicated -- worth a 5-minute
check to confirm it's genuinely dead code, but not the cause of THIS incident.)

### (c) HIGH CONFIDENCE -- the invoked Cloud Run Job is crash-looping on apparent OOM, at least since 2026-07-23

```
gcloud run jobs executions list --job=uts-prod-market-tick-data-service-cefi-t1-recon --region=asia-northeast1
```

`FAILED_COUNT=1` on every execution from at least 2026-07-15 through 2026-07-24 (20 checked) -- **this specific count is
NOT new** and by itself does not explain the cliff (captures were healthy through 07-20 despite it; treat it as a
chronic, non-blocking partial failure baseline, not the smoking gun).

```
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-market-tick-data-service-cefi-t1-recon"'
```

For 2026-07-24T09:00-09:04Z and 2026-07-24T06:00-06:03Z, and again for 2026-07-23 at both trigger times: the container
logs ~15 lines of normal bootstrap --

```
ServiceRuntime: op=download mode=batch provider=gcp env=production data=real testnet=mainnet dry_run=False
ApiKeyReloader started: 24 venues, refresh every 300s
API keys validated for 3 data source(s): ['aster', 'hyperliquid', 'tardis']
```

-- and then **`WARNING: Container terminated on signal 9.`**, TWICE per execution window (a retry also gets killed),
**before any per-venue download work begins** (no log line after `API keys validated` ever appears). Signal 9 = SIGKILL,
consistent with an OOM kill. Configured resources (`gcloud run jobs describe`): **4 CPU / 8Gi memory**.

### (d) LOWER CONFIDENCE -- whether 07-21/07-22 share this exact cause

Searched explicitly for `signal 9` in the 2026-07-20/21/22 logs for this job: **not found**. Those days' failures show
only a single bare `ERROR`-severity log entry per execution with **no INFO bootstrap output preceding it at all** --
qualitatively different from 07-23/24's ~15-line-then-OOM pattern. This could mean: (i) an even earlier-stage failure
(e.g. image pull / cold-start) that predates the in-process OOM regression, (ii) a logging/routing gap that simply
didn't capture the INFO lines for those days, or (iii) a genuinely different, unrelated failure mode. **Not resolved
this run** -- whoever picks this up should pull the full log payload (not just severity>=WARNING) for 07-21 and 07-22
specifically.

## What is NOT established (do not assume)

1. **The code/config change that pushed this job's memory footprint past 8Gi**, and when it landed. Would need a
   `market-tick-data-service` commit-log / deploy-history read around 07-21..07-23 -- not done this run (out of the
   reconciliation skill's scope; this issue doc is the handoff).
2. **Whether this is causally related to** the Surface-C manifest-dedup script's OOMs documented in
   `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 6 -- that doc's OOMs happened on (i) a
   **shared operator dev host** (`earlyoom`, SIGTERM/143) and (ii) a **dedicated e2-standard-8 VM** (SIGKILL/137) --
   both explicitly DIFFERENT infrastructure from this **isolated Cloud Run Job's own container memory limit**. They may
   be coincidental (same general week of heavy cefi migration activity) rather than one root cause. Worth checking
   whether the two share a common code path (e.g. both import the same heavy pandas/canonicalization module at startup)
   before assuming either way.
3. Whether `market-tick-cefi-daily-download`'s week-old PAUSE (item (b) above) is dead/superseded code or a second,
   independent gap.

## Why this is filed as a BIG finding, not folded into an existing doc

Per `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` and `CLAUDE.md`'s findings-triage rule: a data-correctness finding
outside every currently-open plan's stated scope goes to `plans/active/issues/<slug>_<date>.md`, and a **big finding**
(data-correctness, live production) additionally requires operator notification in-chat. This is a live capture OUTAGE,
categorically different from the canonicalisation/migration-shape work the currently-open cefi docs
(`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`,
`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`) are tracking -- none of those docs mention this Cloud Run
job or its crash-loop. Every day this continues is a permanent gap in the historical record for that day's
live/near-real-time capture window (a later backfill can fill `expected_unattempted`/`attempted_failed` cells
retroactively for BATCH-sourced data, but not for anything that was only ever available live/near-real-time).

## Recommended next steps (not executed this run -- read-only reconciliation)

1. Pull full (not severity-filtered) Cloud Logging output for the 2026-07-21 and 2026-07-22 executions of
   `uts-prod-market-tick-data-service-cefi-t1-recon` to determine if they share the signal-9 OOM pattern or are a
   distinct, earlier failure.
2. Identify the `market-tick-data-service` deploy/commit that shipped around 2026-07-21..23 and check for anything that
   would increase this job's steady-state or peak memory (new import, larger in-memory universe/catalogue load,
   accidental `columns=None` full-schema read analogous to the dedup script's own documented OOM cause).
3. Either raise the Cloud Run Job's memory allocation (mirroring the dedup-VM precedent's "bump to a bigger
   machine/allocation" fix) as an immediate mitigation, or fix the underlying memory growth -- operator's call which
   comes first.
4. Once fixed, verify recovery the same way this issue found the problem: `capture_status` by `date` should show
   `captured` counts return to the ~1,000-1,200/day baseline, and `attempted_at` max should advance past
   `2026-07-24T01:31:59Z`.
5. Confirm whether `market-tick-cefi-daily-download` (PAUSED since 2026-07-16) is dead code; if so, consider removing it
   to reduce future investigation noise.
