---
doc_type: plan
title:
  Cross-cutting closeout — observability, self-monitoring, data-status + alerting family (forked from the closeout,
  2026-08-09)
summary: >-
  Forked from `cross_cutting_consolidated_closeout_2026_07_25.md`'s 2026-08-09 line-cap trim (the parent had grown to
  1007 lines, over the 1000L hard cap) — mirrors the split pattern already used by tradfi/sports/prediction's
  consolidated-closeout docs. Carries the 6 still-open, observability/self-monitoring-themed Tracks verbatim in
  substance (nothing summarized, rewritten, or dropped): Track 14 (scheduled-job reliability + concurrency/OOM defects +
  manifest reprocessing tooling), Track 18 (manifest-consolidator throughput + data-feed SLA/self-healing), Track 19
  (data-pipeline hardening/self-monitoring family), Track 20 (data-status family), Track 21 (data-pipeline
  alert/monitoring bugs), Track 22 (manifest-hygiene/phantom-capture monitor instances). The parent retains these
  Tracks' headers as short pointer stubs (mirroring how Track 24 was already extracted 2026-07-26) so existing
  cross-references by Track number stay valid.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    cross-cutting,
    close-out,
    observability,
    self-monitoring,
    data-status,
    alerting,
    manifest,
    manifest-hygiene,
    plan-hygiene,
  ]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md,
    /plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md,
    /plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md,
    /plans/archive/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md,
    /plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md,
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: medium
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
depends_on: []
gate_on_depends:
  false # tracking-only fork — none of the parent's remaining Tracks (1-13, 16-17, 23-24) depend on
  # this child's open work landing first; this just documents provenance per task_template.md finding I.
source: >-
  2026-08-09 line-cap trim of `cross_cutting_consolidated_closeout_2026_07_25.md` (1007 lines, over the 1000L hard cap;
  target ~700L after the trim). This fork carries Tracks 14/18-22 verbatim in substance, dispatched via
  `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch4_2026_08_09.md` todo 2.
---

# Cross-cutting closeout — observability, self-monitoring, data-status + alerting family

> **Forked from**
> [`cross_cutting_consolidated_closeout_2026_07_25.md`](/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md)'s
> 2026-08-09 line-cap trim. This doc carries the parent's Tracks 14 and 18-22 verbatim — see the parent's own "Split
> notice" section for the full fork rationale. Close a track by closing its source doc(s), then tick it off in the
> parent's Reachability map (this doc does not duplicate that map).

## Track 14 — Scheduled-job reliability + concurrency/OOM defects + manifest reprocessing tooling · P1/P2

**Sources**: `issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md` (fully open, unresolved — the
`uts-prod-cf-manifest-audit` Cloud Run Job has never successfully produced output, failing daily since 2026-07-04;
affects all 5 AGs' daily CF-audit) + `issues/pipeline_smoke_sweep_findings_2026_07_20.md` (mostly done — 3 tooling
false-green defects fixed, a 15h CeFi outage caught + a watchdog added; residual: prediction/sports staleness
re-checks) + `issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md` (3 of 4+ findings fixed
same-day; open: DeFi handlers have zero concurrency at any level, needs an `asyncio.gather`+`Semaphore` refactor, plus
per-site verification across ~12 DeFi handlers — not a mass edit, needs care) +
`issues/manifest_index_read_oom_ canonical_cache_2026_06_24.md` (operationally mitigated; the durable fix — bound
`_CANONICAL_CACHE` per bucket — is undone, touches the LIVE cefi/sports/tradfi manifest path, validate carefully) +
`issues/manifest_reprocessing_ generic_utility_2026_07_07.md` (fully open, 4 todos — design → implement
`select_shards_for_reprocess()` → wire as an IS CLI subcommand → optionally retire 13 near-identical one-off scripts;
concrete design already specified) +
[issues/vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md](/plans/archive/issues/vm_exec_stall_watchdog_checkpoint_regex_mismatch_2026_08_03.md)
(self-dispatched, `assigned_vm: planning` — `vm-exec-with-gcs-tee.sh`'s `STALL_PROGRESS_REGEX=checkpoint` self-kills any
real backfill VM across all 20 launchers using that wrapper; regex fix identified, VM relaunch/verify in flight).

**Close-out criterion**: the CF-manifest-audit job green for all 5 AGs with cited evidence; the smoke-sweep residuals
re-verified (not re-fixed if already resolved elsewhere); the DeFi concurrency refactor shipped; the manifest-OOM bound
implemented (Option A minimum) and measured to not regress the sports warm-cache win; the generic reprocessing utility
designed+implemented+wired.

## Track 18 — Manifest-consolidator throughput + data-feed SLA/self-healing · P1/P2

**Sources**:
[consolidator_throughput_backlog_monitor_2026_07_09.md](/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md)
(per-AG manifest-consolidator backlog/throughput + "did the run produce its expected data" verdict; open: the v2
truthful merged-per-tick histogram, currently DESCOPED pending WS-H's structured-progress spine, + the deployments-page
split) +
[data_feed_sla_registry_and_active_self_healing_2026_06_19.md](/plans/active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md)
(open: build the single declarative SLA registry consolidating scattered freshness thresholds, plus active
re-fetch-on-stale self-healing).

**Close-out criterion**: both open items ship or are explicitly re-deferred to WS-H's spine landing first.

## Track 19 — Data-pipeline hardening/self-monitoring family · P0/P1

**Sources**:
[data_pipeline_hardening_self_monitoring_2026_06_22.md](/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md)
(the canonical anti-silent-misclassification hardening doc, explicitly "across all 5 asset groups" — an otherwise-
shipped detect→auto_recover→file_issue→page loop) + its 3 residual forks (all 2026-07-24):
[data_pipeline_ag_residual_backfill_decisions_2026_07_24.md](/plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md)
(tradfi `attempted_failed` retries, a UAC image-packaging bug, tradfi `ohlcv_15s` spurious-aggregation bug, defi
DIVERGENT_EMPTY backfill-vs-scope campaign) ·
[data_pipeline_alert_substrate_residual_2026_07_24.md](/plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md)
(alert-substrate/digest/writer-invariant residuals, alerting-service app-log visibility) ·
[data_pipeline_self_healing_completion_residual_2026_07_24.md](/plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md)
(Phase 6-C self-heal actuator wiring/packaging/scheduling).

**Close-out criterion**: all 3 forks' residual items closed; the parent's detect→recover→file→page loop verified live
end-to-end for all 5 AGs.

## Track 20 — Data-status family · P1

**Sources**:
[data_status_catalogue_true_source_phase2_2026_07_24.md](/plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md)
(Phase-2 true-catalogue/expected-universe source via instruments-service) ·
[data_status_cell_grid_rearchitecture_2026_07_18.md](/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md)
(bound/stream/precompute cell-grid rewrite to kill a deployment-api OOM reading the whole manifest) ·
[data_status_page_ux_and_canonicalisation_2026_07_16.md](/plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md)
(honest-coverage fix + P1-P8 UX/canonicalisation: instrument-type canonicalisation, catalogue explorer, cefi chain-axis
drift, sports league-drilldown) ·
[data_status_tab_and_downloads_remediation_2026_06_16.md](/plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md)
(data-status tab bugs + instruments CSV download regressions, gated on the v9 manifest migration) ·
[/plans/archive/2026_07/deployment_redesign_cherrypicks_2026_07_20.md](/plans/archive/2026_07/deployment_redesign_cherrypicks_2026_07_20.md)
(cherry-picks from a superseded branch: triage panel, dark-theme default, `reason_summary`/`reason_category`, mock-mode
coverage-summary, flat `capture_status` matrix endpoint — all data-status/API items).

**Close-out criterion**: all 5 docs' open P1/P2 items ship; the v9-migration gate on `_tab_and_downloads_remediation`
re-checked before dispatch (do not surface pre-migration data through the UI, per the data-pipeline-correctness rule).

## Track 21 — Data-pipeline alert/monitoring bugs · P1

**Sources**:
[/plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md](/plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md)
(DP_NOT_V9/rate-limit alert false-positives tied to the manifest schema v9 migration + consolidation lag) ·
[/plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md](/plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md)
(DP_* events have no PubSub→subscriber→router path to `#data-pipeline-alerts`) ·
[archive/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md](/plans/archive/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md)
(nightly cron VM undersized + launcher SSOT drift across 4 conflicting launcher artifacts → partial `coverage.json`) ·
[issues/live_mode_event_sink_topic_missing_2026_06_21.md](/plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md)
(fleet-wide latent bug: live-mode lifecycle event sink publishes to non-existent PubSub topics, MTDS/MDPS).

**Close-out criterion**: all 4 alerting bugs fixed + verified live (the false-positive fix, the missing PubSub route,
the cron launcher-SSOT reconcile, the missing `{service_name}-events` topic creation for live-mode launches).

## Track 22 — Manifest-hygiene / phantom-capture monitor instances · P2

**Sources**: dated outputs of 2 standing cross-cutting monitors —
[issues/manifest_hygiene_red_2026_06_27.md](/plans/archive/issues/manifest_hygiene_red_2026_06_27.md) (defi instance) +
[issues/manifest_hygiene_red_2026_06_29.md](/plans/archive/issues/manifest_hygiene_red_2026_06_29.md) (cefi instance) —
both from `manifest_hygiene_daily.py`;
[issues/phantom_captures_prediction_2026_06_28.md](/plans/archive/issues/phantom_captures_prediction_2026_06_28.md) from
the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py`). (`phantom_captures_tradfi_2026_06_28.md`
retagged `[tradfi]` 2026-08-07 — see cross-reference below, no longer claimed here.)

**Close-out criterion**: each candidate CSV triaged (real gap → backfill, code bug → fix adapter/writer, intentional new
venue → extend the UAC oracle); the prediction/tradfi phantom rows reconciled via `--apply` flips to `attempted_failed`.

**Cross-reference**:
[issues/phantom_captures_tradfi_2026_06_28.md](/plans/archive/issues/phantom_captures_tradfi_2026_06_28.md) — same G3
phantom-manifest monitor as the 3 docs above, but tradfi-owned (`asset_group: [tradfi]`) since 2026-08-07; tracked in
`tradfi_consolidated_closeout_2026_07_18.md`'s own aggregated-source list, not this Track. Listed here only because it
shares the monitor, not as a Track-22 close-out obligation.

**Ownership note (resolved `autonomous_session_operator_decisions_2026_07_25.md` entry #20, 2026-07-26; PARTIALLY
OVERRIDDEN 2026-08-07)**: the remaining 3 docs (2× `manifest_hygiene_red`, `phantom_captures_prediction`) stay tagged
`[cross-cutting]` because the underlying MONITOR (`manifest_hygiene_daily.py` /
`reconcile_phantom_manifest_rows_all.py`) is shared fleet-wide, even though each instance's content/fix is single-AG
(defi/cefi/prediction respectively). **Kept `[cross-cutting]` deliberately for these 3, NOT retagged** — retagging
during concurrent per-tranche audits is still the greater hazard (a standing condition, not a one-time rollout risk,
since the audits run on a permanent cron). **The 4th, `phantom_captures_tradfi_2026_06_28.md`, was retagged `[tradfi]`
2026-08-07** — operator explicitly overrode the 2026-07-26 ruling for this one doc after seeing the rationale (see
`tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 6 for the override record); its prior double-claim
(also named in tradfi's own batch2 Deferred section) is now resolved — tradfi is its sole home, this Track no longer
claims it. `phantom_captures_prediction_2026_06_28.md`'s 1 remaining open todo (the 15-month re-fetch/backfill) was
**SUPERSEDED 2026-07-29 (BLK-eb3f4765, main Option A) and the doc archived** — extracted into the operator-driven
(`assigned_vm: NA`), gated plans that own it: `/plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`
(P0 MVP-backfill-readiness gate, only after A–D smoke-green) + `/plans/active/data_completion_prediction_2026_07_15.md`.
No open todo remains under this Track for it; nothing was launched (running it ahead of the canonical-migration +
smoke-green foundation gate would be premature).

## Progress Log

- **2026-08-09**: forked verbatim from `cross_cutting_consolidated_closeout_2026_07_25.md`'s 2026-08-09 line-cap trim
  (parent had grown to 1007 lines, over the 1000L hard cap). No content changes beyond the move itself.
- **2026-08-10 (prose-findings formalization sweep)**: full read for unconverted actionable prose — none found. This
  doc's own design is a pure pointer/index layer: each Track's "Sources"/"Close-out criterion" prose describes
  aggregate close-out conditions over OTHER docs' own tracked `- [ ]` checkboxes, and the doc explicitly states "this
  doc does not duplicate that map" (see header note). There is no orphaned action item here that isn't already a real
  checkbox in one of the 15 `related:` source docs. 0 prose findings converted, 0 already-resolved citations needed —
  no genuinely-actionable content of THIS doc's own to formalize.
