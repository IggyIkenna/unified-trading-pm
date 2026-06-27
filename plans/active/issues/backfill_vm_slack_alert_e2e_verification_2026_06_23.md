---
title: "Backfill-VM Slack-alert e2e verification — three gaps found 2026-06-23"
created: "2026-06-23"
source:
  - "data_completion_to_100_all_ag_2026_06_21.md task [VERIFY] P0 line 2438"
  - "deployment-service fleet monitor code audit"
  - "GCS sentinel reads + Pub/Sub subscription metrics"
assigned_vm: NA
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
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

- [ ] [DEPLOY] P0. **Rebuild deployment-api image from LDR and redeploy `uts-prod-dp-heartbeat-watcher` Cloud Run Job**
      — unblocks the `RunLogSignals` OOM fix going live (fix is already in code at LDR). (deployment-service)

- [ ] [CODE] P1. **Add structured JSON logging to Cloud Run job/service images** so Python `logger.info()` calls appear
      in Cloud Logging. Investigate whether stdout is suppressed, then add a JSON log formatter in the entrypoint or UTL
      bootstrap. (deployment-service + unified-trading-library)

- [ ] [VERIFY] P2. **Operator spot-check `#data-pipeline-alerts` channel** for the 2 `DP_VM_EXIT_NONZERO` CRITICAL
      alerts from ~13:45 UTC 2026-06-23

- [ ] [DEPLOY] P0. **Rebuild + redeploy BOTH alerting-service (`dp-alerting-subscriber`) AND deployment-api
      (`uts-prod-dp-exit-code-monitor`) Cloud Run units** so the Gap-4 verbose/actionable-alert fix (UTL envelope
      unwrap + explain block + run.log snippet + log link) is live; then verify a real `DP_VM_EXIT_NONZERO` renders VM
      name + exit code
  - log link + error snippet + explanation in `#data-pipeline-alerts`. (alerting-service + deployment-service) to
    confirm end-to-end Slack delivery is working. (operator action)
