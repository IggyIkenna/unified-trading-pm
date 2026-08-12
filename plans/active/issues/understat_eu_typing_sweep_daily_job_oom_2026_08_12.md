---
doc_type: issue
title:
  "understat-eu-typing-sweep daily Cloud Run Job has OOM-crashed (signal 9) on every run for at least 3 consecutive days"
summary: >-
  While spot-checking FootyStats/Transfermarkt/SFI/Understat health (operator asked "how's it looking"), found the
  `understat-eu-typing-sweep-daily` Cloud Scheduler job (`0 3 * * *`) triggers a Cloud Run Job that has completed with
  `Completed: False` on every one of its last 3 executions (2026-08-09, 2026-08-10, 2026-08-12 UTC) — the other three
  sports enrichment sources checked in the same pass (FootyStats, Transfermarkt/SFI's `soccer-football-info`,
  Transfermarkt) are all genuinely healthy (`Completed: True` for 3+ days). This is a live, currently-recurring
  production failure with no open tracking doc.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, understat, oom, cloud-run-job, data-correctness]
related:
  [/codex/02-data/data-pipeline-correctness-hard-rule.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-08-12
author: claude-agent
priority: P1
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: interactive session, operator asked for a health check across sports enrichment sources (2026-08-12)
context_scope:
  [
    instruments-service/instruments_service/reference_data/adapters/sports/adapters/understat.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

## What was found

Checked the actual Cloud Run Job execution history (not just Cloud Scheduler's trigger-delivery status, which only
confirms the trigger fired, not that the job succeeded):

```
$ gcloud run jobs executions list --job=understat-eu-typing-sweep --region=asia-northeast1
understat-eu-typing-sweep-6pzt9  2026-08-11T03:00:06Z  2026-08-11T03:01:40Z  Completed  False
understat-eu-typing-sweep-qpqqj  2026-08-10T03:00:06Z  2026-08-10T03:02:36Z  Completed  False
understat-eu-typing-sweep-q6t6w  2026-08-09T03:00:07Z  2026-08-09T03:01:46Z  Completed  False
```

Cloud Logging for the most recent execution (`understat-eu-typing-sweep-6pzt9`) shows a clean, repeatable OOM signature:

```
2026-08-11T03:00:37Z INFO Reading live _index gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet
2026-08-11T03:00:51Z WARNING Container terminated on signal 9.
2026-08-11T03:01:22Z INFO Reading live _index gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet
2026-08-11T03:01:36Z WARNING Container terminated on signal 9.
2026-08-11T03:01:40Z ERROR
```

The job reads the full sports availability index (unprojected — same class of full-index read this workspace has hit OOM
on before elsewhere, e.g. the data-status rollup incident chain resolved earlier 2026-08-11/12), gets SIGKILLed, retries
once, gets SIGKILLed again, then gives up. The job's current resource allocation is `cpu=2` / `memory=8Gi`
(`gcloud run jobs describe understat-eu-typing-sweep`) — not yet confirmed whether 8Gi is genuinely insufficient for the
current index size or whether this is a recent regression (index growth, a code change reading more columns than before,
etc.) — not investigated further this pass.

**Not the same incident as the archived 2026-06-23 finding** in `data_completion_sports_2026_07_24.md` (todo
"XG/understat backfill is OOMing... instr-backfill-sports-xg-\* VMs") — that was a one-off backfill VM OOM, already
resolved (instruments-service@bd32424) and marked done. This is the **daily production Cloud Run Job**, a different
mechanism, currently and repeatedly failing.

## Why this matters

- Understat is one of only 4 sports enrichment sources actively verified this session (FootyStats, Transfermarkt,
  `soccer-football-info`/SFI all confirmed healthy in the same pass) — its daily refresh has been silently failing for
  at least 3 days with no alert observed to have fired (not independently confirmed against `data-pipeline-alerts` —
  worth checking as part of the fix, given this session's earlier finding that Cloud Build failures weren't reliably
  paging either).
- Matches the "Reading live _index... full unprojected read" pattern this workspace has hit OOM on repeatedly this month
  (rollup service, cell-grid builds) — worth checking whether this specific read site uses a column-projected read
  (`columns=`/`filters=`) or a bare full-index load.

## Todos

- [ ] [DIAG] P1. Confirm whether `memory=8Gi` on `understat-eu-typing-sweep` is genuinely insufficient for the current
      sports availability index size, or whether this is a recent regression (index growth vs. a code change). Check
      whether the Understat handler's index read is column-projected or a bare full-index load
      (`read_availability_index()` with no `columns=`/`filters=` — QG STEP 5.106 flags bare reads elsewhere in this
      codebase; worth checking if this call site is baselined or genuinely missing the projection). Repo:
      instruments-service. Done when: root cause (undersized memory vs. an unprojected-read regression) is identified
      with evidence, not guessed.
- [ ] [CODE/INFRA] P1. Fix based on the diagnosis above — either raise the Cloud Run Job's memory allocation (with a
      measured number, not a guess — same discipline as the rollup-service memory fix in the deploy-blocker incident
      chain) or add column projection to the index read. Repo: instruments-service / deployment-service (whichever owns
      the job's Cloud Run config). Done when: a real triggered execution of `understat-eu-typing-sweep` completes with
      `Completed: True`.
- [ ] [DATA] P2. Confirm whether this 3+ day gap paged `data-pipeline-alerts` or any other channel — if not, this may be
      a second instance of the same alerting-coverage gap class found in
      `cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md` (archived
      this session), applied to Cloud Run Job execution failures rather than Cloud Build failures. Not yet checked.

## Progress Log

- **2026-08-12 (interactive session)**: filed while spot-checking sports enrichment source health at the operator's
  request. Confirmed via `gcloud run jobs executions list` + Cloud Logging that this is a genuine, currently-live,
  repeatable OOM failure (not a one-off) distinct from the already-resolved June backfill-VM incident. Did not
  root-cause or fix — out of scope for the health-check task this was surfaced during; flagging per the workspace's "a
  big finding gets a tracked issue doc, not just a chat mention" rule so it isn't lost. FootyStats,
  `soccer-football-info` (SFI), and Transfermarkt were all confirmed healthy in the same pass — this is specific to
  Understat.
