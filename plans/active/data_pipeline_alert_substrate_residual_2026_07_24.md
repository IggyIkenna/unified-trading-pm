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
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: observability_master
assigned_vm: NA
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

- [ ] [UI] P0. **Streaming events pane** in deployment-ui that tails the live VM event stream (not just the alert
      ledger) per AG/VM. `[UI]` + `pw:L2 ✓` + regression spec required. Extend `deployment_ui_monitoring_pane`. —
      **deployment-ui**

## Residual from Phase 3 (Daily per-AG completion summary + hygiene audit) + Wave 4b out-of-repo wiring

- [ ] [SCRIPT] P0. Close the `audit_criteria_automation` honest-SKIPs: wire CF-10 (phantom) and CF-14 (catalogue ⊇
      present-set) from SKIP to real checks inside `cf_manifest_audit_all.py`. — **market-tick-data-service**

- [ ] [SCRIPT] P0. **v9-readiness gate** in the daily digest: surface `schema_version` distribution per AG (target
      100%==9, read actual rows not the constant) and alert on any AG <100%. Reuse `audit_canonical_form.py` CF-1. —
      **e2e-testing**

- [ ] [INFRA] P0. **Apply the data-pipeline-audit terraform** (the crons run only once deployed): after the var-change
      lands, targeted `terraform apply -target=...` the 4 `dp-audit` Cloud Run Jobs + 4 schedulers (NOT a blanket apply
      of `terraform/gcp/` — drift risk). The `cf_manifest_audit` apply convention is the model. Until applied, the crons
      exist in code + the image is ready, but the schedulers are not yet provisioned. — **deployment-service**

- [ ] [CODE] P0. **UTL `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` string constants** (cleanliness only — routing already
      works via the UAC rule matching the event string): 2-line add to `events/event_types.py` + `events/__init__`
      export; edits are green-and-ready on-disk in the slot UTL clone, ship on the next clean UTL window (a peer was
      live on manifest_writer). — unified-trading-library **unified-trading-library, unified-api-contracts,
      unified-trading-pm**

## Phase 4 — Writer-side path + state invariants (defence-in-depth, closes residual C3/C7)

- [ ] [CODE] P0. `record_captured`/`record_empty` assert the resolved GCS path `is_canonical()` (Phase 3 validator)
      before write — a non-canonical write fails loudly at the writer, not days later in an audit. —
      **unified-trading-library**
- [ ] [CODE] P0. Live==batch schema invariant assert at the live `record_captured` boundary (C7: `asset_group`
      kwarg-not-column class). — **unified-trading-library**

## Residual from Phase 6 (Alert enrichment, Tier 1)

### Alert enrichment (B — inline trace + deep-links)

- [x] ✅ [CODE] P1. alerting-service: add `deployment_ui_base_url` (+ `deployment_scripts_log_bucket`) config, SM/env
      hot-reloaded (none exists today). — alerting-service@868872c (config.py fields + config_reloaders.py SM keys
      DEPLOYMENT_UI_BASE_URL/DEPLOYMENT_SCRIPTS_LOG_BUCKET + get_paging_credentials; default "" → links omitted)
- [ ] [CODE] P0. UTL writer-gate `_emit_unproven_honest_absence`: add `venue`/`data_type`/`day` (from `row_key`) + an
      `error_message` to the DP_UNPROVEN_HONEST_ABSENCE `details`. — unified-trading-library
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

- [ ] [CODE] P0. **`get_paging_credentials` batch-fetch is fragile — one missing secret zeroes ALL paging creds** —
      `config_reloaders._fetch` does `SecretManagerClient.get_secrets(_ALL_PAGING_SM_KEYS)` as ONE batch; 6 Twilio
      secrets + `DEPLOYMENT_SCRIPTS_LOG_BUCKET` are absent in SM → the batch raises → `except` returns empty → EVERY
      paging cred (incl. the #uts-live-alerts webhook) reads blank, so the SM-hot-reload path is dead (worked around by
      the `UTS_LIVE_ALERTS_SLACK_WEBHOOK` env secret on the service). Fix: make `_fetch` tolerate missing secrets
      (per-secret get, skip-missing) OR create the absent secrets as empty placeholders (the `if val:` mapping already
      skips empties). Then SM-hot-reload works without the env fallback. (alerting-service)

- [ ] [CODE] P0. **DP telemetry events route through the generic incident path (Telegram→Slack-fallback) — should not**
      — diagnosis refined 2026-06-23: there is NO `alerting-slack-webhook-url` secret, but
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
      it). (alerting-service)

- [ ] [CODE] P0. **Verify the deployment-service heartbeat-stall watcher emit carries
      `vm_name`+`asset_group`+`message`** so the per-VM DP_VM_STALL alerts render distinguishably (the 13× batch came
      from the OLD alerting revision 00005 @01:38 pre-base-url; confirm the current path renders vm_name). Repo:
      deployment-service `data_pipeline_monitors/heartbeat_stall_watcher.py`.

## Success criteria

- All open todos above ticked `- [x]` with evidence (commit sha / QG sentinel / deploy verification per PLAN_FORMAT.md §
  8b for any runtime-infra claim).
- `bash scripts/plan-hygiene/check_line_caps.sh` no longer flags this file, and
  `bash scripts/plan-hygiene/run_hygiene_sweep.sh` shows 0 hard failures across the 4-way split.
