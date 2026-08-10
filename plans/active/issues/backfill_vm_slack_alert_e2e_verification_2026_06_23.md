---
doc_type: issue
title: Backfill-VM Slack-alert e2e verification — three gaps found 2026-06-23
summary: >-
  E2E verification of the backfill-VM Slack-alert path found four gaps: the heartbeat-stall watcher was OOM-killed every
  tick before writing its sentinel (fixed in code, not yet deployed), Python stdout/stderr isn't captured in Cloud
  Logging for fleet monitors/alerting, Slack delivery isn't end-to-end observable, and delivered alerts were generic
  because the UTL envelope was never unwrapped.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [monitoring, slack, observability, self-healing, backfill, spot-vm, data-pipeline, escalation]
related:
  [
    ../data_completion_to_100_all_ag_2026_06_21.md,
    /plans/epics/infrastructure_master.md,
    /plans/archive/issues/deadman_monitor_log_event_crash_2026_06_23.md,
  ]
created: "2026-06-23"
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  [
    "data_completion_to_100_all_ag_2026_06_21.md task [VERIFY] P0 line 2438",
    deployment-service fleet monitor code audit,
    GCS sentinel reads + Pub/Sub subscription metrics,
  ]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-27
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/epics/infrastructure_master.md,
    /plans/archive/issues/deadman_monitor_log_event_crash_2026_06_23.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/deployment-observability.md,
    alerting-service/alerting_service/notifiers/data_pipeline_slack.py,
  ]
---

## What I found

### Gap 1 — Heartbeat stall watcher OOM-killed before every execution (FIXED IN CODE, NOT YET DEPLOYED)

**Root cause (codified 2026-06-23):** `_gcs.pipeline_heartbeat_age_minutes()` and `_gcs.run_log_age_minutes()` each
independently download the full `run.log` blob per VM. With ~50 running VMs, that was 100 full `run.log` downloads per
5-min tick; long-running backfill VMs accumulate multi-MB logs → total memory exceeded the 2Gi Cloud Run job limit →
`Container terminated on signal 9` (OOM) on every execution.

**Evidence:** `vm-census/heartbeat-last-run.json` sentinel is **ABSENT** (the watcher has never written it — OOM-killed
before completion every tick). Both the exit-code and meta sentinels ARE present and fresh.

**Fix already shipped (deployment-service LDR):** `_gcs.RunLogSignals` dataclass + `_gcs.run_log_signals()` single-read
function; `heartbeat_stall_watcher.py` updated to call the combined reader; 3 new unit tests. QG passed. Shipped via
quickmerge.

**Still needed:** Rebuild the deployment-api Docker image from LDR and redeploy the `uts-prod-dp-heartbeat-watcher`
Cloud Run Job so the fix is live.

### Gap 2 — Python stdout/stderr not captured in Cloud Logging for fleet monitors or alerting service

**Observation:** Querying Cloud Logging for `resource.type="cloud_run_job"` with
`job_name="uts-prod-dp-exit-code-monitor"` returns ONLY system/audit entries (`cloudaudit.googleapis.com/system_event`,
`run.googleapis.com/varlog/system`). No Python application stdout entries exist for ANY Cloud Run Job in this project.
Same is true for the alerting service `dp-alerting-subscriber` Cloud Run Service (only stderr from old revisions
`00001`/`00002` from 2026-06-22 are visible).

**Impact:** The following are completely invisible in Cloud Logging:

- `"exit-code sweep: %d terminated, %d non-clean (%s)"` (logger.info in cli.py:332) → cannot see WHICH VMs were
  non-clean from a given run
- `"data-pipeline-alerts Slack POST ok (status %d)"` (logger.info in data_pipeline_slack.py:273) → cannot confirm Slack
  delivery from logs

**Root cause (SUSPECTED):** The Cloud Run job/service images may not be writing structured JSON logs to stdout (Cloud
Logging expects JSON with `severity`, `message` fields). The Python `logging` module emits plain text by default, which
is captured as raw text in `run.googleapis.com/stdout` — but that log name is missing entirely, suggesting stdout may be
suppressed or redirected.

**NOT the UTL event sink architecture:** `log_event()` correctly routes to `PubSubEventSink` (mode=live,
topic=lifecycle-events). The Python `logger.info()` calls are SEPARATE from `log_event()` and should still reach stdout.
The issue is that stdout itself is not reaching Cloud Logging.

### Gap 3 — Slack alert delivery confirmed indirectly, not end-to-end observable

**What is confirmed:**

- Exit-code fleet monitor runs every 5 min (Cloud Run Job scheduler) ✅
- Writes GCS sentinel `vm-census/exit-code-last-run.json` with `non_clean=2` ✅
- Events published to Pub/Sub `lifecycle-events` topic (undelivered count 3 → 18 at the 13:45 tick, then dropping back
  to 6 as alerting service consumes) ✅
- Alerting service `dp-alerting-subscriber` running (rev 00012, started 10:55 UTC, min=1 instance, no crashes since
  deployment) ✅
- Alerting service is consuming Pub/Sub messages (undelivered count decreasing) ✅
- UAC rules: `DP_VM_EXIT_NONZERO` → PAGE_OPERATOR (CRITICAL) → `data_pipeline_slack.py:send_data_pipeline_alert()` →
  `#data-pipeline-alerts` ✅

**What cannot be confirmed without Python logs:**

- Whether the Slack webhook POST actually succeeded (HTTP 2xx vs 4xx/5xx)
- Which specific VMs triggered `DP_VM_EXIT_NONZERO` in the 13:45 run
- Whether `DP_VM_STALL` / `DP_VM_NO_HEARTBEAT` alert paths are exercised (heartbeat watcher is OOM-killed, so those
  paths cannot fire at all today)

### Gap 4 — DELIVERED alerts were GENERIC: the UTL envelope was never unwrapped (ROOT CAUSE of the 16:48 useless alert; FIXED IN CODE 2026-06-23)

**Operator escalation 2026-06-23:** the `#data-pipeline-alerts` posts (e.g. the 16:48 `DP_VM_EXIT_NONZERO` /
`DP_CRON_DID_NOT_FIRE` / `DP_CATALOG_NOT_RUNNING` batch) carried ONLY `Event / Severity / Source` — NO VM name, NO exit
code, NO log link, NO error snippet, NO explanation. Gap 3 confirmed the chain reached Slack but never inspected the
alert CONTENT.

**Root cause (file:line):** `PubSubEventSink.write_event`
(`unified-trading-library/unified_trading_library/event_sink.py:270`) publishes every `log_event` as
`{"event": name, "service": ..., "metadata": {"severity": ..., "details": {<the emitter's real payload>}, "correlation_id": ...}}`.
The alerting subscriber `alert_subscriber._deserialize_message` returned the RAW top-level dict as `details`, so the
emitter's real payload sat TWO levels deep at `payload["metadata"]["details"]` and severity at
`payload["metadata"]["severity"]`. The router (`router._mirror_to_data_pipeline_slack`) + the formatter
(`data_pipeline_slack._build_blocks` / `_build_action_block`) look up `details.get("vm_name")` / `"exit_code"` /
`"error_message"` / `"run_log_tail"` / `"severity"` / `"umbrella"` at the TOP level → all `None` → generic alert. The
rich formatter + the emitter metadata both already existed; the metadata was lost in the unflattened envelope.

**Fix shipped (code):**

- alerting-service `alert_subscriber._unwrap_utl_envelope` — flattens `metadata.details` + promotes
  `metadata.severity`/`correlation_id` to the top level (flat legacy kill-switch/margin payloads pass through
  unchanged); + 2 regression tests.
- alerting-service `data_pipeline_slack` — per-event human "_What happened_ / _Recommended action_" explain block
  (DP_VM_EXIT_NONZERO / DP_VM_GONE_NO_CAPTURE / DP_CRON_DID_NOT_FIRE / DP_CATALOG_NOT_RUNNING / CONSOLIDATOR_DOWN) +
  renders an emitter-supplied `log_url` as the run.log deep-link.
- deployment-service `_gcs.error_snippet_from_run_log` + `run_log_console_url`; the exit-code fleet monitor attaches
  `run_log_tail` (error/warn lines + tail of the durable GCS-tee'd run.log, survives self-delete) + `log_url` to the
  finding; `escalation.route_finding` now carries the finding's human `summary` as `message` so the alert summary line
  is readable, not just the event name.

**Still needed:** rebuild + redeploy BOTH `dp-alerting-subscriber` (alerting-service:latest) AND
`uts-prod-dp-exit-code-monitor` (deployment-api:latest) Cloud Run units, then verify a real `DP_VM_EXIT_NONZERO` renders
VM name + exit code + log link + snippet

- explanation in `#data-pipeline-alerts`.

## Why it matters

1. **Heartbeat gap**: The hung-process detection contract (CLAUDE.md §Background-task honesty) is NOT operational. A VM
   running with a frozen `run.log` mtime (hung HTTP call) will NOT be detected. This was the Transfermarkt + FootyStats
   incident class. The fix is in code but not deployed.

2. **Logging gap**: Operator cannot perform post-incident triage using Cloud Logging to see which VMs triggered alerts,
   what their exit codes were, or whether Slack delivery succeeded. Any debugging of a missed alert requires reading GCS
   directly.

3. **Slack delivery confidence**: The alert chain appears functional based on Pub/Sub metrics (messages consumed), but
   cannot be formally verified without end-to-end logging. An operator spot-check of the `#data-pipeline-alerts` Slack
   channel is the definitive verification step.

## Recommended decision

### P0 — Rebuild and redeploy deployment-api image (unblocks heartbeat watcher fix)

```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh
# Then redeploy the Cloud Run Jobs from the new image
```

Owned by: deployment-service worker. Blocks heartbeat stall detection going live.

### P1 — Add structured JSON logging to Cloud Run jobs/services

Configure Python `logging` with a JSON formatter that writes `{"severity": "INFO", "message": "..."}` to stdout. Cloud
Logging natively parses this format. The fix lives in the deployment-api Docker image's entrypoint or in UTL's
`run_lifecycle` / `ServiceBootstrap` context manager.

File: `deployment-service/deployment_service/data_pipeline_monitors/cli.py` (add `logging.basicConfig` with JSON
formatter before `main()`) or add a structured log handler in `unified_trading_library/services/bootstrap.py`.

### P2 — Operator spot-check: verify `#data-pipeline-alerts` received alerts for the 2 non-clean VMs

The 2 VMs that terminated with non-zero exit codes around 13:45 UTC 2026-06-23 should have generated
`DP_VM_EXIT_NONZERO` (CRITICAL / PAGE_OPERATOR) Slack posts. Operator should check the `#data-pipeline-alerts` channel
for these messages to close the verification loop.

## Actionable todos for follow-up plan

> **2026-07-27 /plan-vintage-audit re-verification note**: the dispatch instructions for this pass characterized all 4
> Gap items as "live-verified... independently confirmed by `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`"
> — **that citation does NOT hold up**: the cited doc's own entry for this exact doc
> (`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md:522-525`) is a truncated, unfinished sentence ("Gap 1 (P0
> redeploy deployment-api heartbeat-watcher):..." with nothing after the colon) — it asserts a verdict without ever
> stating the evidence. Independently re-investigated each Gap below; only Gap 1 is solidly confirmed. **Flagging this
> per the findings-triage HARD RULE** rather than silently trusting the citation.

- [x] ✅ [DEPLOY] P0. **Rebuild deployment-api image from LDR and redeploy `uts-prod-dp-heartbeat-watcher` Cloud Run
      Job** — unblocks the `RunLogSignals` OOM fix going live (fix is already in code at LDR). (deployment-service) —
      **CONFIRMED LIVE 2026-07-27** via independent evidence in the freshly-filed
      `/plans/archive/issues/heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md` (a same-day,
      unrelated investigation that incidentally proves this): `uts-prod-dp-heartbeat-watcher-cron` fires the Job
      reliably, 10+ consecutive executions all `SUCCEEDED_COUNT=1` (no more OOM crash-before-completion), and its logs
      show real `WARNING heartbeat_stall_watcher: <vm> verdict=stall hb_age=...` output — the detection half genuinely
      works in production. (That doc found a SEPARATE, new bug — the auto-kill ACTION fails structurally — unrelated to
      this Gap 1's OOM/redeploy scope.)

- [x] ✅ [CODE] P1. **CONFIRMED FIXED + LIVE-VERIFIED 2026-07-28 (unified-trading-pm, verification pass)** — was: add
      structured JSON logging to Cloud Run job/service images so Python `logger.info()` calls appear in Cloud Logging.
      deployment-api Cloud Run JOBS side confirmed fixed (Gap 1 evidence above). The alerting-service
      `dp-alerting-subscriber` Cloud Run SERVICE side — the half that was still broken as of 2026-07-27 — is now fixed:
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s todo shipped (`alerting-service@62b850c` — root cause
      was a project-wide Cloud Logging sink `debug-filter` exclusion silently dropping plain-text/`DEFAULT`-severity
      stdout, not a code bug in this doc's own hypotheses; fixed by switching to UTL's
      `setup_cloud_logging(json_format=True)` so Cloud Run's agent honours the real Python level). **Independently
      re-confirmed live this session** (not just trusting the batch2 citation): `gcloud logging read` against
      `dp-alerting-subscriber` now returns real structured app-level entries (`Event: ALERT_SENT`,
      `Event: ALERT_ROUTED`, `Event: PERSISTENCE_COMPLETED`, etc.) — the "zero app logs" symptom this Gap originally
      reported is gone. Flipping per the todo's own instruction (all three source docs together): this doc +
      `dp_event_pubsub_delivery_gap_2026_06_22.md` (already archived, resolved) +
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` (already `[x]`) are now all consistent.

- [x] ✅ [VERIFY] P2. **RESOLVED 2026-08-08 (operator, NA-corpus blocker digest round 5, id=55)** — was: operator
      spot-check `#data-pipeline-alerts` channel for the 2 `DP_VM_EXIT_NONZERO` CRITICAL alerts from ~13:45 UTC
      2026-06-23. Superseded by better, hard evidence the operator provided directly: a real, current
      `DP_VM_EXIT_NONZERO` CRITICAL alert (VM `mtds-live-smoke-cefi-20260808-044733-0e32e9`, exit_code=1, 2026-08-08
      09:31 AM) pasted showing full delivery — this closes the original 2026-06-23 ask's underlying question (does Slack
      delivery for this alert class actually work) with a newer, directly-inspected occurrence rather than the stale
      6-week-old one. See the DEPLOY todo immediately below — same evidence closes both.

- [x] ✅ [DEPLOY] P0. **Rebuild + redeploy BOTH alerting-service (`dp-alerting-subscriber`) AND deployment-api
      (`uts-prod-dp-exit-code-monitor`) Cloud Run units** so the Gap-4 verbose/actionable-alert fix (UTL envelope
      unwrap + explain block + run.log snippet + log link) is live; then verify a real `DP_VM_EXIT_NONZERO` renders VM
      name + exit code + log link + error snippet + explanation in `#data-pipeline-alerts`. (alerting-service +
      deployment-service) to confirm end-to-end Slack delivery is working. (operator action) — **CODE confirmed shipped
      2026-07-27**: `alerting-service@ceed827` (confirmed real + ancestor of `main` via `git log`/
      `git merge-base --is-ancestor`) + `deployment-service@d2ddb23` (confirmed real via `git log`), both QG-green with
      new regression tests per `data_completion_sports_2026_07_24.md:220-227`, image builds `c2beac49`/`c0f6dc2f` cited
      there. **"Redeployed" half now CONFIRMED 2026-07-28 (unified-trading-pm, live check)**: ran a real
      `gcloud run services describe dp-alerting-subscriber --region asia-northeast1` — the currently-running revision
      (`dp-alerting-subscriber-00015-lcn`) is built from `alerting-service:diag-62b850c`, and
      `git merge-base --is-ancestor ceed827 62b850c` confirms `ceed827` IS an ancestor (62b850c is a later commit that
      also carries the Gap-2 logging fix). The Gap-4 code is genuinely live, not just merged. **Still NOT independently
      confirmable**: whether a real `DP_VM_EXIT_NONZERO` actually renders with full VM name/exit code/log link/snippet —
      checked `gcloud logging read` (30-day window) and the `alerting/history/` GCS partitions for any
      `DP_VM_EXIT_NONZERO`/`EXIT_NONZERO` occurrence; **none found** — no VM has exited non-zero in the observable
      window, so there is no real event to inspect yet. This is not a stale citation, it's a genuine "nothing to verify
      against" gap — same class as Gap 3 below (operator-only, and only actionable once/if a real occurrence happens to
      land in `#data-pipeline-alerts`). **RESOLVED 2026-08-08 (operator, NA-corpus blocker digest round 5, id=55)** — a
      real occurrence finally landed: the operator pasted a live `DP_VM_EXIT_NONZERO` CRITICAL alert (VM
      `mtds-live-smoke-cefi-20260808-044733-0e32e9`, exit_code=1, 2026-08-08 09:31 AM) showing full rendering — VM name,
      exit code, asset group, cloud, source, and a working `run.log` trace link with real log content. Confirms the
      Gap-4 render fix (envelope unwrap + explain block + run.log snippet + log link) actually renders correctly
      end-to-end in production, closing the render-verification half this todo was waiting on. No further action needed.

## Progress Log

- 2026-07-27 (`/plan-vintage-audit` June-2026 sweep, §2 execution): investigated all 4 Gaps against real evidence rather
  than trusting the dispatch instructions' "independently confirmed by
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`" citation, which turned out to be a truncated/unfinished
  sentence in that doc with no actual supporting evidence. Findings: **Gap 1 genuinely confirmed done+redeployed**
  (fresh same-day corroboration from an unrelated investigation doc). **Gap 2 genuinely still open** for the
  alerting-service Cloud Run Service specifically (confirmed via `dp_event_pubsub_delivery_gap_2026_06_22.md` + a live,
  dispatched, unexecuted todo in `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`) — only the deployment-api
  Cloud Run Jobs side is fixed. **Gap 3 genuinely still open** (operator-only action). **Gap 4's code is shipped +
  verified real, but the "redeployed to the currently-running revision" claim is unconfirmed** (no live GCP check run
  this session). **Did NOT archive this doc** — 3 of 4 items have genuine remaining work. Flagging the broken
  corroborating citation per CLAUDE.md's findings-triage HARD RULE.
- 2026-07-28 (unified-trading-pm, verification pass): **Gap 2 flipped** — independently re-confirmed via live
  `gcloud logging read` that `dp-alerting-subscriber` now emits real structured app logs (batch2's fix,
  `alerting-service@62b850c`, is genuinely live). **Gap 4's "redeployed" half flipped** — live
  `gcloud run services describe` + `git merge-base --is-ancestor` confirm the running revision is built from a
  `ceed827`-descendant image. **Gap 4's render-verification half and Gap 3 both stay open**: checked 30 days of Cloud
  Logging + GCS `alerting/history/` for any `DP_VM_EXIT_NONZERO` occurrence — none found, so there is currently nothing
  for anyone (agent or operator) to inspect. Doc stays open (Gap 3 + Gap 4's render-verification remain genuine,
  currently un-triggerable, operator-only work) — not archived.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — `locked_by: live-defi-rollout`; both remaining todos are
  operator-only by construction (a Slack-channel spot-check, and a render-verification with no real DP_VM_EXIT_NONZERO
  occurrence to inspect).
- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries — corrects the 2026-08-01 marker's stale count, the
  list itself already carried 6) — all still resolve; both remaining open todos (VERIFY spot-check + DEPLOY
  render-verification) are operator-only with no live occurrence to inspect yet, per the doc's own progress log.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-07-30 (unchanged):
  `locked_by: live-defi-rollout`; both remaining todos (VERIFY P2 Slack spot-check; DEPLOY P0 render-verification) are
  explicitly operator-only / no-live-occurrence-to-inspect-yet by construction.
- **operator ruling 2026-08-08** (NA-corpus blocker digest, cross-cutting round 5, id=55): RESOLVED with hard evidence —
  operator pasted a live, real `DP_VM_EXIT_NONZERO` CRITICAL alert (VM `mtds-live-smoke-cefi-20260808-044733-0e32e9`,
  exit_code=1, 2026-08-08 09:31 AM) showing full rendering (VM name, exit code, asset group, cloud, source, working
  run.log trace link with real content). Both remaining todos closed — this is now the newer, better occurrence that
  supersedes the stale 2026-06-23 spot-check ask and independently confirms the Gap-4 render fix works end-to-end in
  production. **All todos in this doc are now `[x]`.** Not archived this pass (`locked_by: live-defi-rollout` requires
  an explicit `[unlock-plan]` decision, not taken autonomously) — left for the next archive-candidates sweep to pick up.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
