---
doc_type: plan
title: Data-Pipeline Alert Substrate — Residual Hardening (forked from the hardening/self-monitoring plan)
summary:
  The residual alert-substrate + hygiene-digest + writer-invariant hardening items forked out of
  data_pipeline_hardening_self_monitoring_2026_06_22.md's Phase 2/3/4/6-B sections during the 2026-07-24 line-cap
  remediation split. Everything here is small, independent tail work left after that plan's emit→route→escalate
  substrate, daily digest, hygiene audit, and writer-side path/state invariants shipped — no new design, pure residual
  execution.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [data-pipeline, hardening, monitoring, alerts, fetch-evidence, plan-split, residual]
related:
  [
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-24 from data_pipeline_hardening_self_monitoring_2026_06_22.md per the plan line-cap remediation
    triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 9, 'alert substrate' fork) — operator
    approved unlock+split via interactive Q&A.",
  ]
locked_by:
locked_since:
---

# Data-Pipeline Alert Substrate — Residual Hardening

> **Forked 2026-07-24** from
> [`data_pipeline_hardening_self_monitoring_2026_06_22.md`](/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md)
> as 1 of a 4-way split (+ 1 excise) approved by the operator via the plan line-cap remediation triage
> (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 9). The parent plan's Phase 0/1/5 fully shipped
> and stay there as historical record; this plan carries ONLY the still-open alert-substrate / hygiene-digest /
> writer-invariant tail items, moved **verbatim** (todo text + evidence untouched) from their original sections. Sibling
> forks: `data_pipeline_self_healing_completion_residual_2026_07_24.md` (Phase 6-C),
> `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md` (TradFi/DeFi AG-specific residuals). See the parent plan
> for the full failure-catalogue (C1-C7), the "reuse, do NOT rebuild" table, and all shipped Phase 0-5 history.

## Residual from Phase 2 (data-pipeline-alerts channel + streaming events + exit_code-aware fleet monitor)

- [ ] [CODE] P0. Per-source **rate-limit / health event** `SOURCE_RATE_LIMITED{source, venue, http_429_count}` and
      `SOURCE_KEY_POOL_EXHAUSTED` (C5: TheGraph 9-key pool, Databento, etc.) → `data-pipeline-alerts`. —
      **market-tick-data-service**

- [x] ✅ [UI] P0. **Streaming events pane** in deployment-ui that tails the live VM event stream (not just the alert
      ledger) per AG/VM. `[UI]` + `pw:L2 ✓` + regression spec required. Extend `deployment_ui_monitoring_pane`. —
      **deployment-ui@7da69bf** — extended the cockpit's existing Alerts & Logs "Live logs" pane (`AlertsLogsTab.tsx`,
      shipped by `deployment_ui_monitoring_pane_2026_06_19.md`) rather than rebuilding: added asset-group → VM dropdowns
      sourced from the same `GET /api/deployments/inventory` census `Deployments.tsx` already reads for its own filters
      (client-side option-derivation, no new backend endpoint), so an operator can find + tail a VM's event stream
      without already knowing its exact name — the pre-existing free-text box stays as a manual override for live
      clusters not in the VM inventory. `pw:L2 ✓` — new regression
      `tests/smoke/cockpit-alerts-logs-ag-vm-picker.spec.ts` (2 tests, AG-select populates VM options + streams;
      switching AG resets VM selection) against the mock backend's real fixture data; full existing `cockpit.spec.ts` +
      `deployments-page.spec.ts` suites (49 tests) reconfirmed green, no regressions. Full QG green (typecheck/lint/101
      unit tests · 74% cov/build).

## Residual from Phase 3 (Daily per-AG completion summary + hygiene audit) + Wave 4b out-of-repo wiring

- [x] ✅ [SCRIPT] P0. Close the `audit_criteria_automation` honest-SKIPs: wire CF-10 (phantom) and CF-14 (catalogue ⊇
      present-set) from SKIP to real checks. — `unified-trading-library@fb63477a` (the real edit location; the module
      moved out of `market-tick-data-service`'s `cf_manifest_audit_all.py` 2026-07-10). CF-10 real GREEN/RED via
      `--mode full` (cost-scoped, honest SKIP by default); CF-14 already computed real verdicts, now with test coverage.
      See `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` for full detail.

- [x] ✅ [SCRIPT] P0. **v9-readiness gate** in the daily digest: surface `schema_version` distribution per AG (target
      100%==9, read actual rows not the constant) and alert on any AG <100%. — `e2e-testing@98d499a`. Reused (not
      re-derived) via a new shared `_dp_common.schema_version_readiness()`, also backing `manifest_hygiene_daily.py`'s
      CF-1/`DP_NOT_V9` check.

- [x] ✅ [INFRA] P0. **Apply the data-pipeline-audit terraform** (the crons run only once deployed): after the
      var-change lands, targeted `terraform apply -target=...` the 4 `dp-audit` Cloud Run Jobs + 4 schedulers (NOT a
      blanket apply of `terraform/gcp/` — drift risk). The `cf_manifest_audit` apply convention is the model. Until
      applied, the crons exist in code + the image is ready, but the schedulers are not yet provisioned. — DONE
      2026-07-26 (`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` todo 5). **Already fully provisioned** —
      verified live via `gcloud run jobs describe` (all 4: `uts-prod-dp-daily-digest`, `-dp-manifest-hygiene-changed`,
      `-dp-manifest-hygiene-full`, `-dp-reprobe-empty` exist and have been executing daily, confirmed via
      `gcloud run jobs executions list`) and `gcloud scheduler jobs list --location=asia-northeast1` (all 4:
      `uts-prod-dp-daily-digest-cron`, `-dp-manifest-hygiene-changed-cron`, `-dp-manifest-hygiene-full-cron`,
      `-dp-reprobe-empty-cron` present). Note: the `github-actions-deploy` SA lacks
      `cloudscheduler.jobs.list`/`run.jobs.list` IAM — use
      `--account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com` to verify. Nothing further needed
      here; the only remaining gap in this area was the OOM memory bump, tracked + shipped separately in
      `data_pipeline_self_healing_completion_residual_2026_07_24.md`. — deployment-service

- [x] ✅ [CODE] P0. **UTL `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` string constants** (cleanliness only — routing already
      works via the UAC rule matching the event string): 2-line add to `events/event_types.py` + `events/__init__`
      export. — DONE unified-trading-library@0f851fd6 (`DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` added to the DP-DIGEST
      family in `events/event_types.py` + `DATA_PIPELINE_EVENT_TYPES`, exported from `events/__init__.py`;
      quality-gates.sh green, shipped via quickmerge)

## Phase 4 — Writer-side path + state invariants (defence-in-depth, closes residual C3/C7)

- [x] ✅ [CODE] P0. `record_captured`/`record_empty` assert the resolved GCS path `is_canonical()` (Phase 3 validator)
      before write — a non-canonical write fails loudly at the writer, not days later in an audit. — DONE
      unified-trading-library@d7b3ed7d (`_assert_canonical_write_path` in `manifest_writer/_rows.py`, wired into both
      `record_captured` + `record_empty`; STRUCTURAL-only, scoped to the 4 UAC-covered asset_groups with resolvable
      dimensions — every other write shape is a resolution skip, never a false block; `NonCanonicalWritePathError`)
- [x] ✅ [CODE] P0. Live==batch schema invariant assert at the live `record_captured` boundary (C7: `asset_group`
      kwarg-not-column class). — DONE unified-trading-library@d7b3ed7d (`LiveCapturedAssetGroupInvariantError` raised
      when `record_captured(validate=False)` — the live bookkeeping boundary — resolves no `asset_group` for a
      market-data cell; scoped to that boundary only, fleet-wide self-heal-else-blank behaviour unchanged elsewhere)

## Residual from Phase 6 (Alert enrichment, Tier 1)

### Alert enrichment (B — inline trace + deep-links)

- [x] ✅ [CODE] P1. alerting-service: add `deployment_ui_base_url` (+ `deployment_scripts_log_bucket`) config, SM/env
      hot-reloaded (none exists today). — alerting-service@868872c (config.py fields + config_reloaders.py SM keys
      DEPLOYMENT_UI_BASE_URL/DEPLOYMENT_SCRIPTS_LOG_BUCKET + get_paging_credentials; default "" → links omitted)
- [x] ✅ [CODE] P0. UTL writer-gate `_emit_unproven_honest_absence`: add `venue`/`data_type`/`day` (from `row_key`) + an
      `error_message` to the DP_UNPROVEN_HONEST_ABSENCE `details`. — DONE unified-trading-library@d7b3ed7d
- [x] ✅ [CODE] P1. `data_pipeline_slack.py::_build_blocks`: append a fenced-code trace block
      (evidence/exit_code/run_log_tail, ≤3000 chars) + an actions block with deep-link buttons — data-status
      `{base}/service/{svc}/data-status`, VM logs `{base}/ops/vms/{vm}`, GCS `run.log` console link. Thread
      `deployment_ui_base_url` from `router._mirror_to_data_pipeline_slack`. — alerting-service@868872c
      (`_build_trace_block` truncates to 3000 + `_build_action_block` omits links when inputs absent / base="" ;
      `send_data_pipeline_alert` + `_mirror_to_data_pipeline_slack` thread base+log_bucket; tests block-network)
- [x] ✅ [CODE] P2. deployment-service exit_code monitor: add `run_log_tail` (last N lines of RUN_LOG_BLOB) to the
      finding `details` for the inline trace. — deployment-service@d2ddb23ca (`exit_code_fleet_monitor.py` calls
      `_gcs.error_snippet_from_run_log(...)` and sets `finding.details["run_log_tail"] = snippet`)
- [x] ✅ [CODE] P0. **Fix the GCS run.log freshness freeze (tee-flush lag) — the GCS-log watchers' substrate** — DONE
      **unified-trading-library@13653f9f + deployment-service@82431d1** (QG-green: UTL 127s exit0 + deployment 55s
      exit0; shipped via `quickmerge --agent --files`). The UTL `LogUploader`
      (`unified_trading_library/lifecycle/uploader.py`, the GCS uploader thread inside `HeartbeatDaemon` that
      `vm-exec-with-gcs-tee.sh` launches — it does NOT die early, lives the VM's whole lifetime) only re-uploaded a VM
      run.log after it grew by `min_growth_bytes` (256 KiB) — a pure anti-churn gate with NO time ceiling. A
      SLOW-but-live log (low-volume scraper) never accumulates 256 KiB → the GCS `run.log` FROZE for hours while the
      on-VM `/tmp/vm-exec-*.log` advanced, blinding `dp-heartbeat-watcher` / `dp-exit-code-monitor` / the stall-mtime
      monitor (CONFIRMED: `tm-backfill-20260622-125650` on-VM log @19:24:33 / 172,267 B but GCS run.log frozen @13:01:03
      GMT — 6h23m stale). FIX: added `LogUploader.max_staleness_sec` (default 90s) — a CHANGED log (grew ≥1 byte OR
      mtime advanced) is force-re-uploaded once the ceiling elapses even below the growth threshold; an idle log still
      skips (no churn reintroduced). Wired through UTL `daemon.py` + deployment-service `heartbeat_cli.py` +
      `DeploymentConfig.upload_max_staleness_sec` (env `UPLOAD_MAX_STALENESS_SEC=90`) + `upload_interval_sec` 120→60. 3
      UTL regression tests + deployment-service ctor-wiring guard. — unified-trading-library, deployment-service

## Later-surfaced alert-substrate bugs (triaged 2026-06-23, still open)

- [x] ✅ [CODE] P0. **`get_paging_credentials` batch-fetch is fragile — one missing secret zeroes ALL paging creds** —
      `config_reloaders._fetch` does `SecretManagerClient.get_secrets(_ALL_PAGING_SM_KEYS)` as ONE batch; 6 Twilio
      secrets + `DEPLOYMENT_SCRIPTS_LOG_BUCKET` are absent in SM → the batch raises → `except` returns empty → EVERY
      paging cred (incl. the #uts-live-alerts webhook) reads blank, so the SM-hot-reload path is dead (worked around by
      the `UTS_LIVE_ALERTS_SLACK_WEBHOOK` env secret on the service). Fix: make `_fetch` tolerate missing secrets
      (per-secret get, skip-missing) OR create the absent secrets as empty placeholders (the `if val:` mapping already
      skips empties). Then SM-hot-reload works without the env fallback. (alerting-service) — RE-DIAGNOSED + CLOSED
      2026-07-27: this diagnosis is STALE against the current code — traced the full call chain
      (`GCPSecretClient.get_secret` → `SecretManagerClient.get_secret`/`get_secrets`) and confirmed via `git blame` that
      `get_secrets()` has been a per-secret loop since the module's creation (2025-11-06); each `get_secret()` call
      independently catches `NotFound`/`GoogleAPIError` and returns `None`, so a missing secret was NEVER able to raise
      and wipe the whole batch. No production fix needed. Added a regression test that drives the REAL
      `SecretManagerClient.get_secrets()` (not a full mock) to lock this in — alerting-service@545799c.

- [x] ✅ [CODE] P0. **DP telemetry events route through the generic incident path (Telegram→Slack-fallback) — should
      not** — diagnosis refined 2026-06-23: there is NO `alerting-slack-webhook-url` secret, but
      `alerting-telegram-bot-token` + `alerting-telegram-chat-id` DO exist → the generic path's PRIMARY is Telegram; the
      Slack-fallback secret only fires when Telegram is unconfigured (my local test lacked Telegram → hit the miss; in
      prod the generic path uses Telegram). ~~So this is NOT a missing-secret blocker.~~ **[doc-reconciliation
      2026-07-12, finding 191, §A2 B-queue ruling] STALE PREMISE (was: "in prod the generic path uses Telegram" as the
      current-state claim above)** — the same-day P1 item below (alerting-service@`1be4fe0`, 2026-06-23 10:10:40Z,
      verified via `git log`/`git show` on `live-defi-rollout`) shipped Slack-only delivery: `send_telegram` was removed
      and `router.py`'s `_deliver_to_channels` now treats any `"telegram"` channel name as an alias that delivers via
      Slack only (confirmed on current HEAD, `router.py:775-777`, comment "2026-06-23; Telegram RETIRED"). Telegram is
      no longer a live transport in prod, generic-path included. The underlying ask — a DP-telemetry routing rule so
      routine `DP_FLEET_MONITOR_RUN_STARTED`/`_COMPLETED` don't fall through to the generic INCIDENT path at all — is
      still open/unshipped (no evidence found of it landing) and stays unchecked; only the Telegram-primary diagnosis is
      stale. The real refinement: routine DP telemetry (`DP_FLEET_MONITOR_RUN_STARTED`/ `_COMPLETED`) should NOT fall
      through to the generic INCIDENT path at all — they should mirror to #data-pipeline-alerts as INFO only (or be
      suppressed), not page Telegram/Slack via the incident path. Add a DP-telemetry routing rule so only genuine DP\_\*
      findings (DP_VM_STALL / DP_EVENT_LOOP_STARVED / CONSOLIDATOR_DOWN) reach the incident path. DP\_\* ALERTS already
      work via the data-pipeline mirror (`DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`). Non-fatal (per-message isolation skips
      it). (alerting-service) — FIXED 2026-07-27: confirmed this real bug lives in `unified-api-contracts`, not
      alerting-service — `DATA_PIPELINE_ALERT_RULES` never registered `DP_FLEET_MONITOR_RUN_STARTED`/`_COMPLETED`/
      `_FAILED` (emitted by deployment-service's `dp-fleet-monitor` CLI via
      `run_lifecycle(service_name="dp-fleet-monitor")`), so `data_pipeline_rule_for()`'s exact-match lookup missed and
      all three fell through to the generic catch-all (`LIVE_ALERT_RULES` `event_pattern="*"`), paging
      `#uts-live-alerts` instead of mirroring to `#data-pipeline-alerts`. Registered `DP-DIGEST-003`/`DP-DIGEST-004`
      (STARTED/COMPLETED → INFO, mirror-only) + `DP-WATCHER-003` (`_FAILED` → CRITICAL, pages — a crashed monitor is
      meta like `DP_ZOMBIE_WATCHDOG_DOWN`) — unified-api-contracts@92e068ea (yaml/md human-doc mirror updated
      alongside), router-level regression tests in alerting-service@545799c.

- [x] ✅ [CODE] P0. **Verify the deployment-service heartbeat-stall watcher emit carries
      `vm_name`+`asset_group`+`message`** so the per-VM DP_VM_STALL alerts render distinguishably (the 13× batch came
      from the OLD alerting revision 00005 @01:38 pre-base-url; confirm the current path renders vm_name). Repo:
      deployment-service `data_pipeline_monitors/heartbeat_stall_watcher.py`. — MEASURED VERDICT 2026-07-27: RENDERS
      CORRECTLY today. Traced `heartbeat_stall_watcher._finding_for()` (stamps `vm_name`/`asset_group` into
      `PipelineFinding.details`) → `escalation.route_finding()` (`event_details = dict(finding.details)`, then injects
      `message = finding.summary` when absent — `finding.summary` already embeds `vm_name`, e.g. "VM {vm_name} stalled —
      {reason}") — all three fields reach the emitted event details the alerting-service router consumes. No code fix
      needed; the 13× batch was confirmed to be from the OLD alerting revision. Added a regression test proving it —
      deployment-service@c7150e0.

## Success criteria

- All open todos above ticked `- [x]` with evidence (commit sha / QG sentinel / deploy verification per PLAN_FORMAT.md §
  8b for any runtime-infra claim).
- `bash scripts/plan-hygiene/check_line_caps.sh` no longer flags this file, and
  `bash scripts/plan-hygiene/run_hygiene_sweep.sh` shows 0 hard failures across the 4-way split.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — the 3 remaining todos are bounded code/UI work
  (SOURCE_RATE_LIMITED/SOURCE_KEY_POOL_EXHAUSTED event, deployment-ui streaming-events pane, the 2-line UTL
  DP_DAILY_DIGEST string constants); batch2's overlapping claims land only on items already `[x]` here.
- **2026-07-30 (slot-6)**: Shipped the deployment-ui streaming-events pane todo — deployment-ui@7da69bf. 1 todo remains
  open (SOURCE_RATE_LIMITED/SOURCE_KEY_POOL_EXHAUSTED, market-tick-data-service) — plan stays active.
