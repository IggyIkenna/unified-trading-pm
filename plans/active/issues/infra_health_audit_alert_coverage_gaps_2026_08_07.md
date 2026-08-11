---
doc_type: issue
title:
  "Alert-coverage cross-reference for the 2026-08-07 infra-health audit — Cloud Run Service/Job compute failures have no
  per-target alerting pathway at all; the alerting-service's own GCS-429 misroutes past an existing DP rule; AWS IAM/STS
  failures have zero AlertCode coverage"
summary: >-
  Cross-referenced all 11 non-excluded findings from the 2026-08-07 3-agent infra health audit
  (`/plans/archive/2026_08/infra_health_audit_findings_fix_2026_08_07.md` todo 2) against `#data-pipeline-alerts` Slack
  history (8-day + 8h pulls via `scripts/dev/slack-read-channel.py`) and both
  `codex/05-infrastructure/data-pipeline-alerts.registry.yaml` and
  `unified-api-contracts/.../crosscutting/alerting/{codes,rules}.py`. Zero of the 11 fired a Slack alert. Three clean,
  structural coverage gaps, none previously tracked:

  **(A) Cloud Run Service/Job compute-failure blind spot** — the entire DP-VM registry class (DP-VM-001..011) is either
  GCE-VM-specific (`run.log` exit-code convention, confirmed via `exit_code_fleet_monitor.py`) or narrowly wired to ONE
  named Cloud Run Job family (`manifest-consolidator-{ag}`, `consolidator_oom_watcher.py` — explicitly out of this doc's
  scope per the operator). No registry, rule, or native GCP monitoring policy exists for Cloud Run **Services** at all
  (confirmed: no `cloud_run_service_registry.py` equivalent exists; `critical_service_uptime.tf` covers exactly 5 named
  services, none of the audit's 3 broken services among them). For Cloud Run **Jobs** outside the consolidator family,
  the only signal is the once-daily, INFO-severity, channel-only `DEPLOYMENT_DIGEST`
  (`deployment-api/routes/deployment_digest.py`) — which names just ONE "last fail" example per umbrella (never a full
  per-job breakdown) and itself only fired 2 of the last 8 days in the pulled window. This blind spot covers findings 1
  (`market-data-query-service`), 2 (`client-reporting-batch`), 3 (`uts-prod-data-status-rollup-svc`), 5
  (`vm-serial-capture-prd`), 6 (`tardis-data-loader`/`check-missing-cloud-storage`/`gen-inst-defs` — not even in the
  classified `cloud_run_job_registry.py` inventory), 7 (`live-event-log-compactor` — root cause already fixed today in a
  separate doc, see below), and 11 (`central-market-data-tardis-loader`).

  **(B) The alerting-service's own GCS 429 misroutes past an existing rule** — `dp-alerting-subscriber`'s
  `write_config_snapshot()` (`alerting_service/persistence/storage_store.py`) catches its GCS exception via the generic
  `classify_and_emit_error()` → `SERVICE_ERROR` (WARN, Telegram-only per `LIVE_ALERT_RULES`, never routed to any Slack
  channel) instead of the dedicated `DP_GCS_429_THRASH` rule (DP-VM-006, CRITICAL, pages) that already exists for
  exactly this failure class — that rule is wired only into VM-side shard-write detectors, not the alerting-service's
  own internal writes. Covers finding 9.

  **(C) AWS IAM/STS failures have zero AlertCode coverage** — grepped the full closed `AlertCode` set
  (`unified-api-contracts/.../alerting/codes.py`) and all ~90 `LIVE_ALERT_RULES` entries: no AWS/IAM/STS/AssumeRole code
  exists. `cost_snapshot_worker.py`'s per-cloud failure path emits `SERVICE_FAILED` (also not a registered AlertCode —
  falls to the generic `*` catch-all at best) and, since the worker treats clouds independently (`successes > 0` → exit
  0), the job's own Cloud Run execution status stays green even when AWS fails every day. Covers finding 10.

  Findings 4 (`mtds-dex-swaps-backfill-2` idle VM) and 8 (`mtds-backfill-odds-401-retry` self-recovering OOM) are
  DIFFERENT: a conceptually-matching rule DOES exist (DP-VM-003 stall / DP-VM-001 OOM) but it did NOT fire. Root-caused
  in todo 4 (2026-08-11): BOTH are benign-by-design, NOT wiring bugs — neither rule uses the `MissTracker`
  (meta-sweep-only; `vm-census/dp-miss-counters.json` has 54 keys, ZERO `DP_VM_*`), and each VM's detection conditions
  were genuinely unmet (finding 4 kept emitting a fresh PIPELINE_HEARTBEAT → `classify_vm_liveness` reads ALIVE;
  finding 8's OOMs were IN-VM subprocess kills — the GCE instance never terminated nonzero). Two NEW coverage-gap
  classes surfaced (capture-complete-but-not-exited VMs; in-VM degraded-but-running backfills) — filed as follow-up
  todos below.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api, alerting-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags:
  [alerting, cloud-run, monitoring, observability, slack, aws, iam, gcs, rate-limit, data-pipeline, infra-health-audit]
related:
  [
    /plans/archive/2026_08/infra_health_audit_findings_fix_2026_08_07.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md,
    /plans/active/issues/data_status_rollup_ml_service_full_blob_missing_2026_07_26.md,
    /plans/archive/2026_08/issues/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07.md,
    /plans/active/issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md,
  ]
created: 2026-08-07
last_updated: 2026-08-07
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: "infra_health_audit_findings_fix_2026_08_07.md todo 2 (alert-coverage cross-reference)"
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/data-pipeline-alerts.registry.yaml,
    deployment-service/deployment_service/cloud_run_job_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/stale_image_watcher.py,
    deployment-service/terraform/gcp/critical_service_uptime.tf,
    deployment-api/deployment_api/routes/deployment_digest.py,
    alerting-service/alerting_service/persistence/storage_store.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py,
  ]
---

# Alert-coverage cross-reference — 2026-08-07 infra-health audit findings

## Method

For each finding, checked (1) `#data-pipeline-alerts` Slack history —
`scripts/dev/slack-read-channel.py data-pipeline-alerts 192 --json-only` (8 days, 2026-07-30→08-07, 17,748 messages)
plus a fresh `... 8 --json-only` pull to cover up to the present, both rendered to flat text and grepped per finding's
exact resource name; (2) the DP-* registry (`data-pipeline-alerts.registry.yaml` + its `rules.py` mirror) for a matching
`event`/detector; (3) for findings older than ~50 days, registry/code-only (no Slack pull) per the task's own guidance,
since an absent rule makes any window moot. `#uts-live-alerts` could NOT be checked — the reader bot returns
`not_in_channel` for that channel (Slack app membership gap, out of scope to fix here; noted as a residual verification
gap, not treated as a negative result).

## Findings table

| #   | Finding                                                                                             | Alert fired?                          | Evidence                                                                                                                                                                                                                                                                                                                                       |
| --- | --------------------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `market-data-query-service` crash-loop (wrong bucket, since 2025-10-20)                             | **no-rule-exists**                    | No Cloud Run Service registry/monitor exists anywhere in the fleet; `DP-PATH-005`/`DP_WRONG_BUCKET` only covers a WRITE handler's `resolve_bucket_name()` assert, not a hardcoded string in a query service. ~9.5mo old — registry-only check per task guidance.                                                                               |
| 2   | `client-reporting-batch` OOM (512Mi, hourly since 2026-08-06T10:05Z)                                | **no**                                | Zero hits for the job name in 8-day + 8h Slack pulls. Only appears as the anonymous "last fail" name in ONE `DEPLOYMENT_DIGEST` INFO message (2026-08-05, predates the stated onset). No Cloud Run Job OOM detector exists outside the consolidator family.                                                                                    |
| 3   | `uts-prod-data-status-rollup-svc` OOM at 32Gi/8vCPU ceiling                                         | **no**                                | Zero Slack hits either window. Root cause already found + accepted as a structural gap in `data_status_rollup_ml_service_full_blob_missing_2026_07_26.md` (discovered via manual `gcloud logging read`, NOT an alert) — that doc never wired Slack notification, only made the failure loud in logs. Not in `critical_service_uptime_targets`. |
| 4   | `mtds-dex-swaps-backfill-2` idle/hung VM (finished ~07:50:33Z today)                                | **no**                                | Zero Slack hits for the VM name. Root-caused (todo 4, 2026-08-11): DP_VM_STALL did NOT fire because the VM kept emitting a fresh PIPELINE_HEARTBEAT every 60s + fresh sidecar after shard-complete — `classify_vm_liveness` gates every STALL branch on heartbeat/sidecar staleness, so an idle-after-complete-but-still-heartbeating VM reads ALIVE by design. No MissTracker on DP-VM-003 (meta-sweep-only). Benign, not a wiring bug; new coverage-gap todo added below. |
| 5   | `vm-serial-capture-prd` dead 19d (`ContainerMissing`)                                               | **no-rule-exists (by design)**        | `stale_image_watcher.py` (DP-VM-007) explicitly SKIPS when the image digest is unresolvable ("fail toward NO false alert" — its documented behavior) — a fully-missing container is exactly this case. Zero Slack hits over 8 days too.                                                                                                        |
| 6   | `tardis-data-loader`/`check-missing-cloud-storage`/`gen-inst-defs` (europe-west1, since 2026-06-19) | **no-rule-exists**                    | None of the 3 names appear in `cloud_run_job_registry.py`'s classified inventory at all — invisible to the DP registry, the daily digest, AND the deployment-observability UI. ~50d old — registry-only check.                                                                                                                                 |
| 7   | `live-event-log-compactor` daily OOM (2026-08-01→08-07)                                             | **no**                                | Zero hits across the FULL 8-day window (fully covers the incident). Root cause already root-caused + fix shipped TODAY in `cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md` (Terraform 4Gi/2CPU + NDJSON parsing fix) — do not duplicate that work, only the alert-gap is new here.                                     |
| 8   | `mtds-backfill-odds-401-retry` self-recovering OOM (every 7-9min today)                             | **no**                                | Zero Slack hits for the VM name. Root-caused (todo 4, 2026-08-11): the OOMs were IN-VM subprocess OOM-kills (CHUNK_SIZE=250 root cause) — the GCE instance never terminated nonzero (`read_terminal_exit_code`=None); it ran + heartbeated until SPOT-preemption (→ DP_VM_PREEMPTED, not EXIT_NONZERO). DP_VM_EXIT_NONZERO fires only on instance termination. No MissTracker on DP-VM-001. Benign, not a wiring bug; new coverage-gap todo added below. |
| 9   | `dp-alerting-subscriber` GCS 429 storm (479x today, `write_config_snapshot`/`routing_rules.yaml`)   | **no (rule exists, wrong code path)** | Zero hits for "429"/`routing_rules`/`write_config_snapshot`. Code-confirmed: routes through generic `SERVICE_ERROR` (Telegram-only) instead of the existing `DP_GCS_429_THRASH` (DP-VM-006) rule, which is wired only to VM-side shard writers.                                                                                                |
| 10  | `uts-shared-deployment-api` AWS cost-snapshot `AssumeRoleWithWebIdentity` AccessDenied              | **no-rule-exists**                    | Grepped the full `AlertCode` closed set + all `LIVE_ALERT_RULES` — zero AWS/IAM/STS/AssumeRole entries. Emitted event `SERVICE_FAILED` isn't even a registered AlertCode. Per-cloud isolation also keeps the job's own exit code green.                                                                                                        |
| 11  | `central-market-data-tardis-loader` never-started 19mo (`minScale=2`)                               | **no-rule-exists**                    | Same as #1 — no Cloud Run Service monitoring exists; not in `critical_service_uptime_targets`. ~19mo old — registry-only check.                                                                                                                                                                                                                |

## Why it matters

Zero of 11 real, currently-active production failures produced a Slack alert — three of them (1, 5, 11) have been
silently broken for **9.5 to 19 months**. The common root cause isn't a broken detector, it's a missing CLASS of
detector: the entire self-monitoring investment (`data-pipeline-alerts.registry.yaml`, ~40 DP-* modes) was built
data-pipeline-first (backfill VMs + the manifest consolidator) and never extended to the general Cloud Run Service/Job
estate that `deployment-digest`/`cloud_run_job_registry.py` already know how to enumerate — the inventory exists, the
failure-detection + paging does not.

## Recommended decision

Don't raise `client-reporting-batch`'s memory limit blind (todo 3 in the parent plan already covers root-cause fixes
per-finding) — that's tracked separately. This doc's scope is alerting infrastructure only:

1. A generic Cloud Run Service liveness class (health-endpoint OR `container/memory/utilizations` OR execution
   `failed_count`) for every service in a to-be-built registry, mirroring `critical_service_uptime.tf`'s pattern but
   fleet-wide instead of 5 hand-picked names.
2. A generic Cloud Run Job per-execution failure detector reading `run_v2` execution status for every job in
   `cloud_run_job_registry.py` (not just the consolidator family) — same shape as `consolidator_oom_watcher.py`,
   generalized.
3. Route `write_config_snapshot`'s (and any other alerting-service internal GCS write's) exceptions through
   `DP_GCS_429_THRASH`/the DP-VM-006 detector when the underlying error is a 429, instead of the generic `SERVICE_ERROR`
   path.
4. Register an `AlertCode` family for cross-cloud IAM/STS failures (AWS AssumeRole, GCP impersonation) so
   `cost_snapshot_worker.py` and any future AWS-side caller has somewhere real to route.

## Todos

- [x] ✅ [INFRA] P1. Build a generic Cloud Run Service liveness/OOM registry + detector (item 1 above) covering at
      minimum `market-data-query-service`, `central-market-data-tardis-loader`, `uts-prod-data-status-rollup-svc` —
      extend `critical_service_uptime.tf`'s pattern or the DP-VM registry, whichever integrates cleaner with the
      existing escalation spine. Repo: deployment-service. — deployment-service@fa07db64d —
      `terraform/gcp/cloud_run_service_liveness.tf`: 3-service Terraform registry with memory-high (>85%/5m), crash-loop
      (2+ restarts/15m), and instance-zero (EVALUATION_MISSING_DATA_ACTIVE) alert policies; QG green, quickmerge landed
      on LDR.
- [x] ✅ [INFRA] P1. Build a generic Cloud Run Job per-execution failure detector (item 2 above) reading every
      `cloud_run_job_registry.py` entry's real execution history, not just `manifest-consolidator-{ag}`. Repo:
      deployment-service. — deployment-service@302dcef33 — `cloud_run_job_failure_watcher.py` (DP-WATCHER-006): iterates
      all non-consolidator GCP Cloud Run Jobs in `CLOUD_RUN_JOBS`, reads most-recent `run_v2` execution, emits
      `DP_CLOUD_RUN_JOB_FAILED` (CRITICAL, PAGE_OPERATOR) when `failed_count > 0` for N consecutive sweeps via
      MissTracker; wired into `cli.py` meta sweep; 19 unit tests; QG green.
- [x] ✅ [CODE] P2. Route `write_config_snapshot`'s GCS exceptions through the `DP_GCS_429_THRASH` event when the
      underlying error classifies as rate-limit (429/RESOURCE_EXHAUSTED), instead of the generic `SERVICE_ERROR` path.
      Repo: alerting-service. — alerting-service@773bb55c2 — `_is_gcs_rate_limit()` + `DP_GCS_429_THRASH` routing in all
      4 write methods (`write_config_snapshot`, `write_alert_history`, `write_quietness_report`,
      `write_cooldown_state`) + 16 unit tests; QG green, quickmerge landed on LDR.
- [x] ✅ [CODE] P2. Register an `AlertCode` family (e.g. `CLOUD_AUTH_FAILED` or similar) for cross-cloud IAM/STS
      failures + wire `cost_snapshot_worker.py`'s per-cloud failure path to emit it instead of the unregistered
      `SERVICE_FAILED`. Repo: unified-api-contracts + deployment-api. — unified-api-contracts@da3941692 +
      deployment-api@faad8437b; `CLOUD_AUTH_FAILED` AlertCode + AlertRule (HIGH, PagerDuty+Telegram) + runbook
      (cloud_auth_failed.md) + 4 unit tests; `_is_auth_error()` helper routes IAM/STS errors to `CLOUD_AUTH_FAILED`,
      others to `SERVICE_ERROR`; QG green, both quickmerged to LDR.
- [ ] [DIAG] P3. For findings 4 and 8 (mtds-dex-swaps-backfill-2 idle VM; mtds-backfill-odds-401-retry self-recovering
      OOM): check the live `MissTracker` state for DP-VM-003/DP-VM-001 against these two VM names to confirm whether the
      conceptually-matching rule genuinely didn't cross its consecutive-miss threshold (benign) vs. a real wiring bug
      (same class as findings A/B/C above). Repo: deployment-service.

## Progress Log

- **2026-08-07**: Filed following `infra_health_audit_findings_fix_2026_08_07.md` todo 2. Full findings table +
  root-cause classification above; cross-referenced against 3 already-open, same-day docs to avoid duplicating in-flight
  root-cause work (compactor OOM fix, rollup 32Gi structural-gap acceptance, dp-alerting-subscriber dual-consumer bug) —
  this doc's scope is deliberately narrowed to the alerting-coverage gap only.
- **2026-08-07 (item 2)**: DP-WATCHER-006 shipped — `cloud_run_job_failure_watcher.py` + CLI wiring + 19 unit tests.
  deployment-service@302dcef33. QG green.
- **2026-08-07 (item 3)**: GCS 429 routing fix shipped — `_is_gcs_rate_limit()` helper + `DP_GCS_429_THRASH` routing in
  all 4 AlertStorageStore write methods + 16 unit tests. alerting-service@773bb55c2. QG green.
- **context-scout 2026-08-09**: populated/refreshed context_scope (9 entries).
