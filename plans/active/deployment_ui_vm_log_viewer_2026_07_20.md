---
doc_type: plan
title: deployment-ui — VM run.log viewer (size, capped tail, working download) — WS-4
summary: >-
  Repro audit (2026-07-20) found the operator's "logs don't populate reliably" complaint understates the problem —
  run.log content is never fetched into the browser at all today. The "Live log tail" panel is actually a lifecycle
  EVENTS stream from a different GCS bucket entirely, and "Download" saves those events as CSV, not the log. The
  archive-path lookup that does exist is keyed by completed_at[:10] while the archiver actually writes daily rolling
  copies keyed by cron-run date — confirmed 404ing live for real VMs. This plan adds a writer-side durable final-
  snapshot on VM completion (removing date-guessing), a live-first/archive-fallback read path, size+capped-tail+
  signed-URL-download endpoints, a genuinely new log-viewer panel, and an honest rename of the existing events panel.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, deployment-service, deployment-api, deployment-ui]
scope: [engineer]
tags: [deployment-ui, logs, gcs, observability]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
  - deployment_ui_cost_per_day_accuracy_2026_07_20.md
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  split from deployment_ui_observability_ux_tracker_2026_07_17.md WS-4, repro audit + operator decisions 2026-07-20
---

# deployment-ui — VM run.log viewer

> **🟢 ACTIVE (operator 2026-07-21)** — second-wave dispatch to AO (throughput ramp, after WS-1/WS-2-3 progressed
> cleanly). Must-do review fixes applied before activation (`unified-trading-library` added to `repos:`; the writer todo
> now names the real completion hook — `HeartbeatDaemon` in UTL `lifecycle/daemon.py`, driven by `heartbeat_cli.py`, +
> the shell SIGKILL fallback — and specifies the `vm_run_log_final_uri` path). **Do NOT run concurrently with
> `deployment_durable_operational_data_bigquery_2026_07_21.md`** — both edit the UTL heartbeat daemon (same-file
> collision).

## Context — live repro audit findings (2026-07-20, read-only, no writes)

- **run.log content is never fetched into the browser today.** The "Durable run log" link on `DeploymentDetail`
  (`detail-run-log` testid) is a bare `<a>` to the GCS Console browser UI, only rendered when `completed_at` is set —
  it's a dead link, not a viewer.
- **"Live log tail" is not run.log.** `StreamingLogsPanel` polls `vm_events.py`, which reads structured lifecycle events
  from a completely different bucket/format (`gs://{project}-events/events/...`), not
  `gs://deployment-scripts-{project}/vm-logs/{vm}/run.log`. The panel is functionally an events timeline mislabeled as a
  log tail.
- **"Download" saves events, not logs.** `StreamingLogsPanel.handleDownload` builds a CSV Blob from the loaded events
  array client-side — no GCS interaction, no bucket, no auth. There is no download endpoint for `run.log` anywhere in
  deployment-api.
- **The archive-path lookup 404s for real VMs — live-confirmed.** `vm_run_log_rolling_uri(vm, completed_at[:10])`
  (`deployments_inventory.py:675-680`, `vm_deployments.py:133-143`) assumes the archiver wrote a copy dated by
  completion day. It doesn't — the archiver writes **daily rolling copies keyed by cron-run date**. Live check on
  `af-backfill-20260627-151733` (completed 2026-06-27): the code-computed path 404s; the object actually lives under
  `20260628`–`20260711` (14 consecutive daily folders). This is the concrete root cause of "logs don't populate."
- **`vm-logs/{vm}/run.log` (the live path) has a 14-day TTL from _last write_, not from VM start** — so it stays valid
  well past `completed_at` for any VM whose heartbeat kept updating it recently; it's not exclusively a "still running"
  signal.
- **No size/metadata endpoint exists.** `grep -rn "gcs_describe_object" deployment-api/routes/` = zero hits.
- Sizes observed in the wild: 362KB–13.4MB across 7 sampled VMs; 20-30MB is a plausible worst case, not typical.

## Decisions (operator, 2026-07-20)

1. **Archive-path root cause fix** — writer-side: the archiver (deployment-service) writes **one durable final
   snapshot** at actual VM completion to a fixed path, replacing the broken date-guessing entirely. No TTL on this final
   copy (same "plain replace, no soft-delete/versioning" convention as everything else log-like in this tracker).
2. **Read priority** — always try `vm-logs/{vm}/run.log` first (valid up to 14 days from last write) regardless of
   `completed_at`; fall back to the new final-snapshot archive path only on a miss.
3. **Panel scope** — leave the existing events panel functionally as-is, just **rename it honestly** (it was never
   broken, only mislabeled) — e.g. "Lifecycle events" instead of implying it's a log tail. Build a **new, separate**
   panel for the actual `run.log` viewer (size, capped tail, download).
4. **Download** — short-lived **signed URL**, client downloads directly from GCS; the API never streams the object
   through itself.

## Todos

- [x] ✅ [BACKEND] P0. **Writer-side final snapshot** (decision 1) — on VM completion write one durable copy of
      `run.log` to a fixed, deterministic path — `unified-trading-library@af1299d5` + `deployment-service@815e8f3`.
      Added `vm_run_log_final_uri(vm_name, project_id)` →
      `gs://deployment-scripts-{project}/log-archive/final/{vm}/run.log` (no date, no TTL, plain replace) in
      `unified_trading_library/deployment_registry.py`. `HeartbeatDaemon` gained a `final_log_uri` param +
      `_write_final_log_snapshot()`, called from `_archive_terminal_state()` (terminal-event emission) alongside the
      existing interval-uploader final flush — best-effort, shard-level-isolated. Wired in
      `deployment-service/deployment_service/vm/heartbeat_cli.py` via
      `final_log_uri=vm_run_log_final_uri(vm_name, project_id=config.gcp_project_id or None)`. SIGKILL fallback in
      `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` now also writes the final snapshot inline (bucket derived
      from `GCS_LOG_URI`, matching the Python helper's shape) so a hard-killed daemon still leaves a final copy. Unit
      tests added in both repos (`test_deployment_registry.py`, `test_daemon.py`, `test_vm_event_emission.py`); both
      repos' `quality-gates.sh` green.
- [x] ✅ [BACKEND] P0. **Read-path resolution** (decision 2) — deployment-api tries `vm-logs/{vm}/run.log` first for any
      VM (regardless of `completed_at`); on miss, falls back to the final-snapshot path (`vm_run_log_final_uri`, from
      the writer todo above — `sequential: true` guarantees it lands first). Removes the broken
      `completed_at[:10]`-keyed rolling-date guess (`deployments_inventory.py:675-680`, `vm_deployments.py:133-143`) —
      delete that dead logic, don't leave it as an unused fallback. — `deployment-api@8ec29f0`. `_vm_item()`
      (deployments_inventory.py) now always sets `run_log_uri = vm_log_stream_uri(entry.vm_name)` (the deterministic
      live path, regardless of `completed_at` — previously only computed via the broken rolling-date guess and only when
      completed). `_to_model()` (vm_deployments.py) keeps `log_uri` as the live path (already sourced from the registry
      entry) and replaces the broken `vm_run_log_rolling_uri(vm_name, date_stamp)` call with the deterministic
      `vm_run_log_final_uri(vm_name)` for `archive_run_log_uri` on completed entries — no date-guessing, no 404s from a
      wrong cron-run-date guess. The serial-console rolling-archive logic (a separate, still-correct mechanism) is
      untouched. Deliberately scoped to a pure deterministic-URI refactor with NO new GCS I/O in these two
      background-cached bulk census paths (`_load_inventory`/`_load_vm_deployments`, both 45s SWR-cached) — the actual
      live-vs-archive EXISTENCE check belongs in the size/metadata endpoint (next todo), which resolves for one VM at
      request time, not for the whole fleet on every cache refresh. Unit test updated
      (`test_route_deployments_inventory.py`); `deployment-api` `quality-gates.sh` green (4790 passed).
- [ ] [BACKEND] P0. Log metadata endpoint — size + last-modified via `gcs_describe_object` on whichever path resolved;
      response marks which location was used (live vs archive) so the UI can label it.
- [ ] [BACKEND] P0. Bounded tail endpoint — byte-range read of only the last ~64–256KB, split to the last 200–500 lines
      (cap configurable). Never load the full object into API memory or the response.
- [ ] [BACKEND] P1. Signed-URL download endpoint (decision 4) — short-lived signed URL for the resolved log object; no
      server-side streaming of the object itself.
- [ ] [UI] P0. New "Run log" panel on `DeploymentDetail` (decision 3) — separate component from the events panel; shows
      size (human units), the capped tail with a "last N lines of X MB" label, and a working Download button using the
      signed URL. Honest states — "no log yet", "log expired (14-day TTL), showing archive copy", errors surfaced, never
      swallowed.
- [ ] [UI] P1. Rename the existing `StreamingLogsPanel`/events timeline (decision 3) — label + any misleading copy
      updated to reflect it's lifecycle events, not log content. Functionality unchanged; update testids if renamed.
- [ ] [REVIEW] P1. Tests — (a) writer-side final-snapshot written on completion; (b) API prefers `vm-logs/` within TTL,
      falls back correctly to the final snapshot; (c) metadata endpoint returns correct size/location; (d) tail endpoint
      never reads past the byte-range cap; (e) signed-URL download works end to end; (f) the old rolling-date-guess code
      path is fully removed. `pw:L2 ✓` + cited regression spec for the UI panels. `bash scripts/quality-gates.sh` green
      in deployment-service, deployment-api, deployment-ui.
- [ ] [REVIEW] P1. Verify against real VMs from this audit (`af-backfill-20260627-151733`,
      `footystats-fwd-20260620-150001`) — confirm the new path resolves correctly going forward; for VMs that completed
      BEFORE this ships (no final snapshot ever written for them), confirm the UI shows the honest "no log available"
      state rather than a blank silent failure.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across the 4 repos — incl.
      `unified-trading-library` for the new path helper) + flip todos same turn (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the log-path resolution contract (live-first/archive-fallback,
      final-snapshot writer contract, no date-guessing), the size/tail/download endpoints, and the events-vs-logs panel
      distinction in `codex/05-infrastructure/deployment-observability.md` +
      `codex/05-infrastructure/gcs-object-operations.md`.

## Success criteria

- Clicking a VM shows its actual `run.log` — size, a capped ~200-500-line tail, and a working download — for any VM
  going forward, whether still live or completed.
- No more 404s from date-guessing; the archive path is a deterministic single write, not a 14-folder scan.
- The events panel is honestly labeled as events, not conflated with log content.
- Download never routes a 20-30MB object through the API process.
- VMs that completed before this ships degrade to an honest "no log available" state, not a silent blank panel.

## Progress Log

- **2026-07-20** — Split from `deployment_ui_observability_ux_tracker_2026_07_17.md` WS-4. Ran a live repro audit
  (read-only, ADC creds, project `central-element-323112`) that reframed the whole workstream: run.log was never
  actually fetched into the browser (the "live log tail" is a mislabeled events panel reading a different bucket
  entirely; "download" saves those events as CSV, not the log), and the archive-path lookup 404s live for real VMs
  because it guesses a date instead of matching the archiver's actual daily-rolling-folder key. Operator decided: fix at
  the writer (durable single final snapshot on completion, no more date-guessing), read `vm-logs/` first regardless of
  completion status (14-day TTL from last write, not from start), keep the events panel but rename it honestly, add a
  genuinely new run.log panel, and use a signed URL for download.
- **2026-07-21** (slot 3) — Shipped the writer-side final snapshot (todo 1): `vm_run_log_final_uri()` helper +
  `HeartbeatDaemon._write_final_log_snapshot()` in `unified-trading-library@af1299d5`, wired into `heartbeat_cli.py` +
  the `vm-exec-with-gcs-tee.sh` SIGKILL fallback in `deployment-service@815e8f3`. Read-path resolution (todo 2) can now
  consume this fixed path instead of the broken date-guessing rolling lookup.
- **2026-07-21** (slot 5) — Shipped read-path resolution (todo 2), `deployment-api@8ec29f0`: deleted the broken
  `completed_at[:10]`-keyed rolling-date guess in both `deployments_inventory.py::_vm_item` and
  `vm_deployments.py::_to_model`; replaced with the deterministic live path (`vm_log_stream_uri`, always populated
  regardless of `completed_at`) and the deterministic final-snapshot archive path (`vm_run_log_final_uri`, from todo 1).
  Scoped as a pure URI-construction fix — no new GCS existence-check I/O added to these two 45s-SWR-cached bulk census
  endpoints; the real live-vs-archive resolution (an actual `gcs_describe_object` existence check) belongs in the next
  todo's per-VM size/metadata endpoint, not the fleet-wide background walk.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the log-path resolution
  contract and the final-snapshot writer contract.
- `codex/05-infrastructure/gcs-object-operations.md` — GCS ops via UTL wrappers (`gcs_describe_object`, byte-range
  reads, signed URLs) — no subprocess `gcloud`/`gsutil` in application code.
- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for both panels.
