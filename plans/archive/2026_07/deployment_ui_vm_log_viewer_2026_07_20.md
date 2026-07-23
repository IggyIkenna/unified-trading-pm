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
  - /plans/active/deployment_ui_observability_ux_tracker_2026_07_17.md
  - /plans/archive/2026_07/deployment_ui_cost_per_day_accuracy_2026_07_20.md
  - /plans/archive/2026_07/deployment_ui_date_range_filter_and_search_2026_07_20.md
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
- [x] ✅ [BACKEND] P0. Log metadata endpoint — size + last-modified via `gcs_describe_object` on whichever path
      resolved; response marks which location was used (live vs archive) so the UI can label it. —
      `deployment-api@32aad22`. New `GET /api/deployments/{name}/run-log/metadata` in `deployments_inventory.py`
      (`RunLogMetadataResponse`: `exists`/`location`/`uri`/`size_bytes`/`last_modified`). Real live-vs-archive
      resolution now lives in the new `deployment_api/routes/_run_log_resolution.py` (`resolve_run_log_location`): tries
      `vm_log_stream_uri` first via `gcs_describe_object`; on miss, describes `vm_run_log_final_uri` instead —
      `metadata=None` when neither exists (honest "no log available", never a fabricated hit). This is the per-VM,
      request-time GCS existence check the previous todo deliberately deferred out of the bulk census paths. Unit tests:
      `tests/unit/test_run_log_resolution.py` (resolver, mocked `gcs_describe_object`) + 2 endpoint tests added to
      `test_route_deployments_inventory.py`. `quality-gates.sh` green (4795 passed).
- [x] ✅ [BACKEND] P0. **Bounded tail endpoint** — byte-range read of only the last ~64–256KB, split to the last 200–500
      lines (cap configurable). Never load the full object into API memory or the response. —
      `unified-trading-library@e22e40f1` + `deployment-api@91fa66bd`. Added `gcs_read_object_range(uri, start, end)` to
      UTL's `cloud_interface/gcs_blob_ops.py` (wraps the existing `StorageClient.download_bytes_range` across
      gcp/aws/local, same URI-splitting convention as `gcs_describe_object`). New
      `GET /api/deployments/{name}/run-log/tail` in `deployments_inventory.py`: resolves the object via
      `resolve_run_log_location` (reused from the metadata endpoint, live-first/archive-fallback), then reads only the
      last `DeploymentApiConfig.run_log_tail_max_bytes` (default 256KB) via `gcs_read_object_range`, split to the last
      `run_log_tail_max_lines` (default 300, clampable per-request via a `lines=` query param). New
      `deployment_api/routes/_run_log_tail.py` isolates the byte-range-read + line-split logic (drops the partial
      leading-line fragment when the read doesn't start at byte 0) for credential-free unit testing. `exists=False`
      honest-absence when neither live nor archive object exists (no GCS read attempted). Unit tests:
      `tests/cloud_interface/unit/test_gcs_blob_ops.py` (UTL), `tests/unit/test_run_log_tail.py` +
      `tests/unit/test_route_deployments_inventory.py` (deployment-api). Both repos' `quality-gates.sh` green.
- [x] ✅ [BACKEND] P1. **Signed-URL download endpoint** (decision 4) — short-lived signed URL for the resolved log
      object; no server-side streaming of the object itself. — `deployment-api@e0b5edaa`. New
      `GET /api/deployments/{name}/run-log/download` in `deployments_inventory.py`: resolves the object via
      `resolve_run_log_location` (reused, live-first/archive-fallback), splits the resolved URI via UTL's
      `split_gcs_uri()`, and calls UTL's existing `generate_download_url(bucket, object_path, expiry_minutes=...)` — no
      new UTL code needed, the pre-signed-URL helper already existed. Expiry configurable via
      `DeploymentApiConfig.run_log_download_url_expiry_minutes` (default 15 min). Honest `exists=False` /
      `download_url=""` when neither live nor archive object exists (no signed URL generated). Unit tests added to
      `tests/unit/test_route_deployments_inventory.py`. `quality-gates.sh` green. (Note: this todo was found duplicated
      in the plan file — deduped to one entry as part of this flip.)
- [x] ✅ [UI] P0. New "Run log" panel on `DeploymentDetail` (decision 3) — separate component from the events panel;
      shows size (human units), the capped tail with a "last N lines of X MB" label, and a working Download button using
      the signed URL. Honest states — "no log yet", "log expired (14-day TTL), showing archive copy", errors surfaced,
      never swallowed. — `deployment-ui@cbc7adb`. New `RunLogPanel.tsx` component (data-testid `run-log-panel`), wired
      into `DeploymentDetail.tsx` as its own `Card`, separate from the existing "Live log tail" events panel. New
      `getRunLogMetadata`/`getRunLogTail`/`getRunLogDownload` client functions in `deploymentApi.ts` against the
      todo-3/4/5 endpoints. Honest states: `exists=false` → "no log available" message (`run-log-empty`, download
      disabled); `location=archive` → amber "Log expired (14-day TTL) — showing archive copy" banner
      (`run-log-archive-notice`); fetch errors surfaced via `role="alert"` (`run-log-error`/ `run-log-download-error`),
      never swallowed. Download opens the signed URL directly in a new tab — no server-side streaming. Added matching
      mock-api.ts handlers for `/run-log/{metadata,tail,download}` (keyed off `run_log_uri` presence in the inventory
      fixture; `sports-backfill-20260621` simulates the archive-fallback case for a real regression target) +
      `tests/smoke/run-log-panel.spec.ts` (live/archive/no-log/download states). `tsc`/ESLint clean, 1026 vitest unit
      tests green, all 4 new + 3 related Playwright specs pass; `deployment-ui`'s `quality-gates.sh` green. (Found the
      pre-existing `daily_costs_and_vm_detail.spec.ts` failures — confirmed unrelated + already tracked in
      `plans/active/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`, not re-filed.)
- [x] ✅ [UI] P1. Rename the existing `StreamingLogsPanel`/events timeline (decision 3) — label + any misleading copy
      updated to reflect it's lifecycle events, not log content. Functionality unchanged; update testids if renamed. —
      `deployment-ui@9717344`. Confirmed BOTH consumers of the shared `StreamingLogsPanel` are events, not log content,
      before renaming (the SSE `/api/logs/stream/{ref}` path used by the cockpit's `AlertsLogsTab` also converts
      `VMLifecycleEvent` → its `VmLogLine` envelope via `_event_to_log_line`, deployment-api `vm_events.py:587` — same
      mislabeling as the WS path). `DeploymentDetail.tsx`'s Card title renamed "Live log tail" → "Live event stream"
      with a "lifecycle events, not run.log content (see Run log above)" subtitle; component doc comment updated.
      `StreamingLogsPanel.tsx` internal copy fixed: placeholder "Search logs..." → "Search events...", "Connecting to
      log stream…" → "Connecting to event stream…", "No matching logs found" → "No matching events found", CSV download
      filename `logs-*` → `events-*`. No testids changed (none were keyed to the old copy). Left the cockpit's
      `AlertsLogsTab.tsx` own headings ("Live logs" / "Stream logs") untouched — a different page this plan's audit
      didn't scope, tracked as a candidate follow-up if the operator wants full consistency.
      `StreamingLogsPanel.test.tsx` updated to match; tsc/ESLint clean, full vitest suite green (1026 passed),
      `run-log-panel.spec.ts` + `deployments-page.spec.ts` Playwright specs pass (12/12); `deployment-ui`'s
      `quality-gates.sh` green.
- [x] ✅ [REVIEW] P1. Tests — (a) writer-side final-snapshot written on completion; (b) API prefers `vm-logs/` within
      TTL, falls back correctly to the final snapshot; (c) metadata endpoint returns correct size/location; (d) tail
      endpoint never reads past the byte-range cap; (e) signed-URL download works end to end; (f) the old
      rolling-date-guess code path is fully removed. `pw:L2 ✓` + cited regression spec for the UI panels.
      `bash scripts/quality-gates.sh` green in deployment-service, deployment-api, deployment-ui. — verified 2026-07-21
      (slot 3). (a) confirmed: `test_vm_run_log_final_uri_canonical_shape` + `test_complete_writes_final_log_snapshot`/
      `test_complete_without_final_log_uri_skips_snapshot_write` (UTL), `test_vm_event_emission.py`
      (deployment-service). (b) confirmed:
      `test_resolves_live_path_when_present`/`test_falls_back_to_archive_when_live_absent`/
      `test_honest_absence_when_neither_path_exists` (`test_run_log_resolution.py`) — read `_run_log_resolution.py`
      directly, live-first/archive-fallback/honest-absence logic is correct (2 `gcs_describe_object` calls worst case).
      (c) confirmed:
      `test_run_log_metadata_live_path_resolved`/`test_run_log_metadata_honest_absence_when_neither_path_exists`. (d)
      confirmed: `test_read_run_log_tail_large_object_reads_only_the_capped_tail` + read `_run_log_tail.py` —
      `start = max(0, size_bytes - max_bytes)` bounds every read, single `gcs_read_object_range` call. (e) confirmed:
      `test_run_log_download_live_path_resolved`/`test_run_log_download_honest_absence_when_neither_path_exists`. (f)
      confirmed for the read path (zero remaining imports/calls of the old `vm_run_log_rolling_uri` in deployment-api) —
      but found the UTL helper itself still existed with **zero production callers anywhere** (the daily archival cron
      builds its rolling-copy path inline, never called it) — deleted it from `unified-trading-library@a760fc93`
      (`deployment_registry.py` + `__init__.py` export) and fixed a stale cross-repo invariant assertion in
      `unified-api-contracts@21510159` (`test_deployment_service_cross_repo_invariant.py` asserted
      `vm_run_log_rolling_uri` as an expected UTL name/deployment-api import — updated to `vm_run_log_final_uri`, what
      deployment-api actually imports now). UI: confirmed `pw:L2` — `run-log-panel.spec.ts` (4 tests:
      live/archive-fallback/no-log/download) + `StreamingLogsPanel.test.tsx`. Re-ran `quality-gates.sh` fresh (post
      fresh-pull) in all 5 touched repos — deployment-service, deployment-api, deployment-ui, unified-trading-library,
      unified-api-contracts — all green.
- [x] ✅ [REVIEW] P1. Verify against real VMs from this audit (`af-backfill-20260627-151733`,
      `footystats-fwd-20260620-150001`) — confirm the new path resolves correctly going forward; for VMs that completed
      BEFORE this ships (no final snapshot ever written for them), confirm the UI shows the honest "no log available"
      state rather than a blank silent failure. — verified 2026-07-21 (slot 3) against live GCS (project
      `central-element-323112`), read-only, ADC creds. **Pre-writer VMs (honest-absence case)**: both
      `af-backfill-20260627-151733` and `footystats-fwd-20260620-150001` completed before the final-snapshot writer
      shipped (2026-07-21) and are well past the live path's 14-day TTL — confirmed via `gcs_describe_object` that
      NEITHER `vm-logs/{vm}/run.log` NOR `log-archive/final/{vm}/run.log` exists for either VM, so
      `resolve_run_log_location()` returns `metadata=None` and the metadata endpoint
      (`deployments_inventory.py::get_run_log_metadata`) correctly returns `exists=False` — the UI's `run-log-empty`/"no
      log available" state, not a blank panel. **Going-forward case (positive proof the writer is live in prod)**: found
      20 real `log-archive/final/{vm}/run.log` objects written today by the shipped
      `HeartbeatDaemon._write_final_log_snapshot()` (e.g. `canonical-migration-cefi-wp04s1-wpf07210859`, 42-53KB,
      timestamped 2026-07-21T12:34-13:21Z — real completed VMs, not synthetic). Ran `resolve_run_log_location()` +
      `read_run_log_tail()` end to end against two of them: both resolve via the live path (still within TTL) with real
      log content read back via the bounded byte-range tail (e.g. 52790 bytes read, last line
      `"2026-07-21 13:19:18,764 INFO Files discovered: 21684"`) — confirms the full read path works against real
      production data, not just mocked tests.
- [x] ✅ [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across the 4 repos — incl.
      `unified-trading-library` for the new path helper) + flip todos same turn (`docs(plans):`). — verified 2026-07-21
      (slot 5): all 5 touched repos already fully landed on `origin/live-defi-rollout` (ahead=0, behind=0, clean trees)
      — deployment-service@389a598, deployment-api@e3d283e, deployment-ui@3584da7, unified-trading-library@a760fc93,
      unified-api-contracts@21510159. No un-shipped WIP remained; this todo closes the shipping loop the prior REVIEW
      todos' verification already confirmed was green.
- [x] ✅ [REVIEW] P2. Post-phase codex audit — document the log-path resolution contract (live-first/archive-fallback,
      final-snapshot writer contract, no date-guessing), the size/tail/download endpoints, and the events-vs-logs panel
      distinction in `/codex/05-infrastructure/deployment-observability.md` +
      `/codex/05-infrastructure/gcs-object-operations.md`. — `unified-trading-pm@ae9151289`. Added a "Run.log viewer —
      resolution contract, endpoints, events-vs-logs distinction" section to `deployment-observability.md` (grounded in
      the actual shipped code: `_run_log_resolution.py`, `_run_log_tail.py`,
      `HeartbeatDaemon._write_final_log_snapshot`, the SIGKILL shell fallback, and the metadata/tail/download
      endpoints), updated its `code_refs`, and added `gcs_read_object_range` to `gcs-object-operations.md`'s function
      reference + `code_refs`/`last_reviewed`.

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
- **2026-07-21** (slot 3) — Shipped the bounded tail endpoint (todo 4), `unified-trading-library@e22e40f1` +
  `deployment-api@91fa66bd`: new `gcs_read_object_range()` UTL helper + `GET /run-log/tail` endpoint reusing
  `resolve_run_log_location` from todo 3, capped at 256KB/300 lines by default (both configurable via
  `DeploymentApiConfig`). While shipping, found + fixed a pre-existing, unrelated `cloud-providers.yaml` cross-copy
  drift (UAC's packaged copy + this PM mirror were both missing the `alerting-service` kind that
  `deployment-service@5f6d4e1` added to its authoring copy) that was failing `unified-trading-library`'s
  `test_sibling_copy_matches_packaged_uac_copy` parity gate for every downstream consumer — synced via
  `unified-api-contracts@83506de0` + this repo's `configs/cloud-providers.yaml`. Also found PM's own `quality-gates.sh`
  red on 2 unrelated pre-existing issues (plan-discipline ratchet 121 > baseline 120; `sports-2020-06-data-floor.md`
  missing `referenced_by` frontmatter key) — filed
  `plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md` rather than absorb that unscoped
  debt into this task.
- **2026-07-21** (slot 3) — Shipped the signed-URL download endpoint (todo 5), `deployment-api@e0b5edaa`: new
  `GET /run-log/download` reusing `resolve_run_log_location` (todo 3) + UTL's pre-existing `split_gcs_uri()` /
  `generate_download_url()` — no new UTL code needed. Expiry via
  `DeploymentApiConfig.run_log_download_url_expiry_minutes` (default 15 min). Found this todo duplicated (two identical
  `- [ ]` entries) in the plan file, likely from a concurrent-slot merge artifact — deduped to one flipped entry.
- **2026-07-21** (slot 4) — Shipped the new "Run log" panel (todo 6, the first `[UI]` todo), `deployment-ui@cbc7adb`:
  new `RunLogPanel.tsx` component wired into `DeploymentDetail.tsx` as its own `Card`, separate from the existing events
  panel below it. Client functions `getRunLogMetadata`/`getRunLogTail`/`getRunLogDownload` added to `deploymentApi.ts`
  against the metadata/tail/download endpoints from todos 3-5. Honest states implemented: no-log (`exists=false`),
  archive-fallback (`location=archive` → the 14-day-TTL banner), and surfaced fetch errors — never a silent blank panel.
  Download opens the signed URL directly in a new tab, no server-side streaming. Added matching `mock-api.ts` handlers
  (`sports-backfill-20260621` simulates the archive-fallback case for a real regression target) +
  `tests/smoke/run-log-panel.spec.ts` covering all four states. `deployment-ui`'s `quality-gates.sh` green (tsc/ESLint
  clean, 1026 vitest tests, new + related Playwright specs pass). While verifying the L2 gate, hit the pre-existing
  `daily_costs_and_vm_detail.spec.ts` failures (confirmed unrelated by re-running on a stashed clean tree) — already
  tracked in `plans/active/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`, not re-filed.
- **2026-07-21** (slot 4) — Shipped the honest rename (todo 7, the second `[UI]` todo), `deployment-ui@9717344`:
  verified BOTH `StreamingLogsPanel` consumers (the WS path here on `DeploymentDetail` and the cockpit's `AlertsLogsTab`
  SSE path) are lifecycle events under the hood before renaming — deployment-api's `/api/logs/stream/{ref}` also
  converts `VMLifecycleEvent` → `VmLogLine` (`vm_events.py::_event_to_log_line`), so the mislabeling was universal to
  the component, not just the WS usage. Renamed the `DeploymentDetail.tsx` Card title "Live log tail" → "Live event
  stream" (+ an honest subtitle pointing at the Run log panel above) and fixed `StreamingLogsPanel.tsx`'s internal copy
  (search placeholder, connecting/empty messages, CSV download filename) to say "events" throughout. Deliberately left
  `AlertsLogsTab.tsx`'s own headings untouched — outside this plan's audited scope. Full vitest suite + the
  run-log-panel/deployments-page Playwright specs green; `deployment-ui`'s `quality-gates.sh` green.
- **2026-07-21** (slot 3) — Shipped the REVIEW test-verification todo (todo 8): re-verified (a)-(f) against the actual
  code (not just re-reading prior flip claims) — read `_run_log_resolution.py` and `_run_log_tail.py` directly to
  confirm the live-first/archive-fallback and byte-range-cap logic is correct, not just tested. Found one residual: the
  old `vm_run_log_rolling_uri` date-guess helper in UTL had zero remaining production callers anywhere (the daily
  archival cron builds its rolling-copy write path inline and never called it) even though deployment-api's read-path
  call sites were already deleted in todo 2 — deleted the dead function from `unified-trading-library@a760fc93`
  (`deployment_registry.py` + `__init__.py` export) and fixed a stale cross-repo invariant assertion in
  `unified-api-contracts@21510159` that still expected deployment-api to import it by name (it actually imports
  `vm_run_log_final_uri` now). Re-ran `quality-gates.sh` fresh in all 5 touched repos (deployment-service,
  deployment-api, deployment-ui, unified-trading-library, unified-api-contracts) — all green.
- **2026-07-21** (slot 3) — Verified todo 9 (real-VM verification) against live GCS, read-only. The two audit VMs
  (`af-backfill-20260627-151733`, `footystats-fwd-20260620-150001`) completed before the final-snapshot writer shipped
  and are past the live-path TTL — confirmed both GCS paths genuinely absent for both, so the metadata endpoint honestly
  returns `exists=False` rather than a silent blank panel. Separately found 20 real `log-archive/final/` objects written
  TODAY by the shipped writer for real completed VMs (`canonical-migration-cefi-*`) — positive proof the writer is live
  in prod — and ran the full `resolve_run_log_location()` + `read_run_log_tail()` path against two of them, confirming
  real log content reads back correctly through the bounded byte-range tail.
- **2026-07-21** (slot 3) — Shipped the post-phase codex audit (todo 10, final todo), `unified-trading-pm@ae9151289`:
  read the actual shipped code (not just prior flip claims) — `_run_log_resolution.py`, `_run_log_tail.py`,
  `HeartbeatDaemon._write_final_log_snapshot`/`_archive_terminal_state`, the `vm-exec-with-gcs-tee.sh` SIGKILL fallback,
  the three endpoints in `deployments_inventory.py`, `RunLogPanel.tsx`, and confirmed `vm_run_log_rolling_uri` has zero
  remaining references anywhere in UTL — then wrote a new "Run.log viewer" section into `deployment-observability.md`
  covering the live-first/archive-fallback resolver, the writer contract (incl. the SIGKILL belt-and-braces path), the
  bounded metadata/tail/download endpoints (with their honest-absence contract), and the
  StreamingLogsPanel(events)-vs-RunLogPanel(logs) distinction; added `gcs_read_object_range` to
  `gcs-object-operations.md`'s function reference. Both docs' `code_refs`/`last_reviewed` updated. Ran `prek` on the two
  changed doc files (full `quality-gates.sh` skipped for this pure-doc change per the doc-commit convention — its one
  failure, `evidence-backed-completion` sub-rule B, is a pre-existing false positive already tracked in
  `plans/active/issues/pm_evidence_backed_completion_false_positive_2026_07_21.md`, confirmed unrelated via
  `git stash`). This closes the plan's final todo.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the log-path resolution
  contract and the final-snapshot writer contract.
- `/codex/05-infrastructure/gcs-object-operations.md` — GCS ops via UTL wrappers (`gcs_describe_object`, byte-range
  reads, signed URLs) — no subprocess `gcloud`/`gsutil` in application code.
- `/codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for both panels.
