---
doc_type: plan
title: Data-Pipeline Hardening + Self-Monitoring (anti silent-misclassification)
summary:
  Harden all data-pipeline adapters against silent misclassification with FetchEvidence gates, per-adapter guards, daily
  summaries, and self-monitoring alerts across all 5 asset groups.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [data-pipeline, hardening, monitoring, silent-failure, fetch-evidence, alerts, anti-misclassification]
related:
  [
    /plans/active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md,
    /plans/archive/2026_06/alert_quality_overhaul_2026_06_18.md,
    /plans/archive/2026_06/deployment_ui_monitoring_pane_2026_06_19.md,
    /plans/archive/vm_launcher_durable_log_observability_2026_06_19.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/2026_06/cross_ag_shard_4pillar_validation_harness_2026_06_19.md,
    /plans/archive/2026_06/audit_criteria_automation_2026_06_08.md,
    issues/fleet_data_acquisition_health_2026_06_21.md,
    issues/backfill_vm_silent_worker_stall_watchdog_2026_06_19.md,
    issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md,
    issues/sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md,
    /plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md,
    /plans/archive/2026_07/data_pipeline_hardening_self_monitoring_history_2026_07_24.md,
  ]
created: 2026-06-22
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 22
estimate_calibrated_ai_days: 18
last_updated: 2026-08-09
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /cursor-configs/skills/vm-preemption-billing-waste-audit/SKILL.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
---

> **🟢 2026-07-24 line-cap remediation split (plan line-cap remediation triage, row 9)**: unlocked (was
> `locked_by: live-defi-rollout`) and split 4 ways + 1 excise, per operator approval via interactive Q&A. Residual open
> todos forked verbatim to `data_pipeline_alert_substrate_residual_2026_07_24.md`,
> `data_pipeline_self_healing_completion_residual_2026_07_24.md`, and
> `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`; one mis-filed prod-terraform-drift item excised to
> `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`; the month-stale live-VM-outage item got an in-place
> status-check annotation (see "REAL OUTAGE surfaced by the fixed watcher" below) rather than a fork.
>
> **🟢 2026-07-24 2nd-pass history extraction (still over the 2000-line umbrella cap after the split above)**: the
> fully-shipped Progress Log tail from "ALERT SPAM REDUCTION" through the final "TradFi databento outbound-call
> hardening" entry (2026-06-22→2026-06-24, 0 open todos in the moved range) was moved VERBATIM to
> `/plans/archive/2026_07/data_pipeline_hardening_self_monitoring_history_2026_07_24.md` — see the pointer left where it
> used to sit, at the very end of this file (the Progress Log now ends at the "ZERO ALERTS" section's fix-3 deep-links
> item). Every still-open todo in this plan (the single P0 "9 live data VMs frozen" item + its status-check annotation)
> stays here unchanged.
>
> **🟢 2026-07-24 3rd-pass bulk history extraction (parent still 856L over the 1000-line cap after the split + 2nd-pass
> slice above)**: essentially the ENTIRE remaining historical narrative was moved VERBATIM to
> `/plans/archive/2026_07/data_pipeline_hardening_self_monitoring_history_2026_07_24.md` (appended after its existing
> content) — the full "Progress Log (autonomous /autonomous run…)" section, "Reship + batch-heartbeat residual" todos,
> the "TradFi pending work" pointer, "Per-AG hardening dispatch" todos, "Per-AG dispatch prompts (FINAL DELIVERY)"
> reference prompts, "FINAL REPORT", the "Phase 6" pointer notes, and every dated "Progress Log — …" subsection through
> the "ZERO ALERTS" root-cause section — plus 3 further `[x]` items immediately after it (binance/bybit/okx/kraken crash
> fix, Slack-primary migration, both-images-rebuilt). The ONE still-open todo anywhere in that stretch (the P0 "9 live
> data VMs frozen" item + its 2026-07-24 status-check annotation) was left in place below under "## Open work" —
> everything else moved is `[x]`-shipped or pure completed-run narrative (0 open todos in the moved content).

# Data-Pipeline Hardening + Self-Monitoring

> **ARCHIVED (2026-08-09) — complete.** Every todo shipped (all `[x]` with cited evidence). The sole remaining open
> item, "9 live data VMs frozen 5.5–32h", resolved 2026-08-09 (slot-24): the originally-named VMs are conclusively gone,
> CeFi live capture is confirmed recovered via the consolidated launcher, and TradFi live capture's separate,
> currently-live outage was forked to its own P0 issue —
> `/plans/archive/2026_08/issues/tradfi_live_cme_capture_stopped_2026_08_09.md`. Record-only from here.

> **Operator intent (2026-06-22)**: "I can't babysit thousands of data types. Stop running VMs for hours only to realise
> they're slow / rate-limited / not writing to the right place / marking everything `empty_confirmed` when the data
> could have been found with a code fix. Make the hardening live at the **code / self-monitoring level**." This plan is
> the canonical consolidation of the data-pipeline guards, alerts, daily summaries, and hygiene audits across all 5
> asset groups (cefi/defi/tradfi/sports/prediction). Start verbose; reduce alert spam once the failure classes below are
> closed.

## Coordination with in-flight parallel work (do NOT duplicate — this plan generalizes)

The per-AG IS/MTDS agents are already shipping **point-fixes** for these classes; this plan turns the recurring ones
into **systemic guards** so they stop recurring. Feed point-fixes into the guard, don't re-solve per-adapter:

- **`data_completion_to_100_all_ag_2026_06_21.md`** is doing per-adapter C1 fixes (e.g. eigenlayer
  fetch-exception→`attempted_failed` MTDS@56435ac; enumerator chain-level false-empty stop IS@0e08237). **Phase 1 here
  is the generalization**: the `FetchEvidence` writer gate makes that fix structural — every adapter, enforced at
  `record_empty`, not one-by-one. Each adapter that plan touches should thread `fetch_evidence` (Phase 1 P0).
- **`citadel_paper_batch_live_reconciliation_2026_06_19.md`** P11.19 (data-quality + VM events panel) overlaps the
  **Phase 2** streaming-events pane — build the pane there, emit the DP\_\* events from here; don't fork the panel.
- The "reuse, do not rebuild" table below is the canonical anti-duplication map for the other seven plans.

## Why this plan exists — the recurring failure catalogue (pooled from the last ~2 weeks of fleet work)

Mined from git history across instruments-service / MTDS / MDPS / features / UAC / UTL (2026-06-13→22) plus the active +
recently-archived PM issue docs. **Every guard in this plan maps to a class below.** This is the shared findings pool
the per-AG IS/MTDS agents feed into — append new classes here as they surface.

| #   | Failure class                                                                                | Concrete incidents (sha)                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Root cause                                                                                                                    | Guard (phase)                                                                                                        |
| --- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| C1  | **Real-empty misclassified as `empty_confirmed`/`SOURCE_RETURNED_ZERO`** (operator's #1)     | sports API-Football errors→empty (IS `0db2450`); odds_api_ws nonexistent key→0 live rows (MTDS `670be2f`); Databento WS key unresolved + mis-stamped `live_massive` (MTDS `e532105`, UAC `1205ae44`); defi catalog missing `manifest_data_type`→`assert_defi_catalog_fresh` always False→zero capture (IS `e8acef1`,`de8e164`)                                                                                                                                                      | error/missing-key/exception paths fall through to honest-absence recorders; writer **trusts** the adapter's "200+empty" claim | **Phase 1 (keystone): proof-of-honest-absence gate + daily re-probe**                                                |
| C2  | **Bad genesis/launch/coverage windows** → wrong `expected_unattempted` vs `attempted_failed` | HL/ASTER misclassified DeFi→cefi, flipped 48.5k `attempted_failed` (UAC `0d0e00a8`,`061cfd01`; MTDS `912dad5`); Aster/Kraken/Deribit genesis (UAC `159f29cc`); sports coverage maps + `EXPECTED_*_NO_COVERAGE` reasons (UAC `9ea84499`,`99361f66`; MTDS `050a091`)                                                                                                                                                                                                                  | UAC coverage oracle wrong/missing for a data_type×chain×league×venue                                                          | **Phase 3 (hygiene audit: oracle-vs-manifest divergence)**                                                           |
| C3  | **Wrong / non-canonical GCS write paths + pipeline_mode drift**                              | 9 defi handlers wrong bucket (MTDS `1c99e5c`); hardcoded `batch` mode (MTDS `2c5e2b5`,`ad3318d`; MDPS `30e7672`; features `795e4f41`); non-canonical `SYM-PERP` keys → renamed 39,205 objects, flipped 20,404 (MTDS `912dad5`,`fbd32b4`); **CeFi/prediction live silent-empty — IS universe bare ticker (KALSHI `KXMVE-26JAN`) not rebuilt to connector form `KALSHI:PREDICTION_MARKET:{ticker}` → WS "unknown instrument; skipping" → 0 capture (MTDS, 2026-06-22 → DP-PATH-006)** | handlers bypass canonical path builders / hardcode partitions; live reader passes a non-connector bare instrument key         | **Phase 3 (path-canonicality validator)** + **Phase 4 (writer-side `is_canonical` assert on `live_tick_blob_path`)** |
| C4  | **Rate-limit / silent stall / OOM-self-delete masking failure** (most frequent)              | sports OOM exit137 self-delete (IS `505dcd9`); GCS 429 hot-object (IS `865aea9`; UTL `94d9de30`); unbounded-socket stalls (IS `06ee145`; MTDS `7ff6c05`,`64789a7`); event-loop starvation blocking GCS read (MTDS `6dfa1a8`)                                                                                                                                                                                                                                                        | no bounded timeouts; self-deleting VM hides exit_code; no heartbeat                                                           | **Phase 2 (heartbeat + exit_code-aware fleet monitor + alerts)**                                                     |
| C5  | **Subgraph / single-key stalls**                                                             | DeFi DEX subgraph stuck on 1 TheGraph key (MTDS `5830cc8`)                                                                                                                                                                                                                                                                                                                                                                                                                          | single-key, no rotation                                                                                                       | **Phase 2 (per-source rate/health event)**                                                                           |
| C6  | **Reader/writer bucket-env mismatch**                                                        | defi preflight READER env-less vs WRITER env-short `-prd-` → stale read → honest-absence → zero capture (MTDS `ea33d38`,`72f7c14`)                                                                                                                                                                                                                                                                                                                                                  | reader/writer disagree on bucket env                                                                                          | **Phase 3 (reader/writer bucket parity check)**                                                                      |
| C7  | **Ordering / downstream-missing + live-boundary schema**                                     | live `record_captured` schema (`asset_group` kwarg not column) (UTL `057264fd`; MTDS `e6b0f29`); sports fixtures missing→downstream features missing; null-vs-`""` dedup double-count (sports)                                                                                                                                                                                                                                                                                      | DAG ordering not enforced; live/batch schema skew                                                                             | **Phase 3 (4-pillar + dedup)** + **Phase 2 (ordering-gap alert)**                                                    |

**Frequency:** C4 > C3 > C1 ≈ C2 > C5/C6/C7. All cited fixes landed; the systemic guards are what's missing.

## Reuse, do NOT rebuild

This plan **wires existing parts**. Net-new is only the keystone gate (Phase 1) + the missing watchers/digest.

| Capability                                                                            | Already exists — reuse it                                                                 | Where                                                                                  |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Manifest 4-state completion math                                                      | `compute_capture_status_counts` / `derive_capture_status_rates`                           | `deployment-api/.../services/data_status/coverage_metrics.py`                          |
| Efficient manifest read (pipeline-mode-aware, legacy fallback, source-priority union) | `read_manifest_with_source_priority`                                                      | `unified-trading-library/.../manifest_reader_fallback.py`                              |
| Event→Slack plumbing (PubSub→router→channel)                                          | `alert_subscriber` → `router.route_event()`                                               | `alerting-service/subscribers/`, `notifiers/router.py`                                 |
| Slack delivery + dedup/cooldown re-nag                                                | `notify-slack.yml` (`dedup_key`)                                                          | `alert_quality_overhaul_2026_06_18.md` Phase 5                                         |
| Lifecycle/progress event taxonomy + sinks                                             | `log_event`, `EventSink`/`LiveEventSink`, `ADAPTER_FETCH_FAILED`                          | `unified-trading-library/.../events/`                                                  |
| VM durable run-log + STARTED/PROGRESS/COMPLETED/FAILED/heartbeat→GCS                  | the streaming substrate                                                                   | `vm_launcher_durable_log_observability_2026_06_19.md` (shipped for backfill launchers) |
| Phantom detection (manifest row→GCS exists?)                                          | `reconcile_phantom_manifest_rows_all.py`                                                  | `instruments-service/scripts/`                                                         |
| Oracle-vs-manifest divergence (expected-but-empty)                                    | `detect_manifest_divergence.py`                                                           | `unified-trading-library/scripts/`                                                     |
| Canonical-form audit (CF-1…CF-12, schema_version dist, spellings, `--probe-paths`)    | `audit_canonical_form.py`                                                                 | `market-tick-data-service/scripts/`                                                    |
| Daily cross-AG manifest audit cron + alert-on-RED                                     | `cf_manifest_audit_all.py` (`0 6 * * *`)                                                  | `audit_criteria_automation_2026_06_08.md` Phase 2                                      |
| 4-pillar shard validation (rowcount/NaN/schema/cluster)                               | `validate_shards_4pillar.py`                                                              | `e2e-testing/scripts/validation/` (MTDS QG 5.88)                                       |
| Alert ledger + `/alerts` page                                                         | shared alert store + `GET /api/alerts`                                                    | `deployment_ui_monitoring_pane_2026_06_19.md` (shipped)                                |
| Zombie-VM watcher / consolidator-liveness                                             | `vm_zombie_watchdog.py` / `consolidator_liveness.py` (`CONSOLIDATOR_DOWN` already alerts) | `deployment-service/scripts/vm/`, `unified-trading-library/.../monitors/`              |
| Canonical path builders                                                               | `build_*_partition_path`, `candidate_parquet_paths`                                       | `unified-api-contracts/.../canonical/partition_paths.py`                               |

---

## Phase 0 — Cross-cutting AG foundation (the emit→route→escalate substrate + failure-mode SSOT)

> Built first, AG-agnostic, following the agent-orchestrator + CI/CD Slack dynamics. Everything in Phases 1-5 emits into
> this substrate. **Start verbose; drive the alert count to zero** (a persistent alert is a bug to close). SSOT for
> every failure mode: `/codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml`.

- [x] ✅ P0. **Slack credentials in Secret Manager** —
      `DATA_PIPELINE_ALERTS_SLACK_{APP_ID,CLIENT_ID,CLIENT_SECRET,SIGNING_SECRET,VERIFICATION_TOKEN,WEBHOOK}` created in
      `central-element-323112` (mirrors `AGENT_ORCHESTRATOR_SLACK_*`). Webhook smoke-tested: HTTP 200 `ok` → message in
      `#data-pipeline-alerts`.
- [x] ✅ P0. **Failure-mode SSOT registry** — `/codex/05-infrastructure/data-pipeline-alerts.md` (human SSOT: channel,
      secrets, emit→route→escalate model, lifecycle verbose→baselined→zeroed, anti-patterns) +
      `data-pipeline-alerts.registry.yaml` (machine-readable: ~40 modes across
      FETCH/COVERAGE/PATH/VM/RATE/ENV/ORDER/MANIFEST/CATALOG/WATCHER, each with
      severity/event/detector/escalation/status). The shared pool the per-AG agents append to.
- [x] ✅ P0. **Slack notifier** DONE alerting@6e8b551 (`notifiers/data_pipeline_slack.py`, SM-hot-reload, best-effort,
      no-op when unset). **Slack notifier** `data_pipeline_slack.py` (parallel to `uts_live_alerts_slack.py`):
      SM-hot-reloaded `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`, best-effort mirror, no-op when unset. — **alerting-service**
- [x] ✅ P0. **Router rules** DONE alerting@6e8b551 (`rules/data_pipeline_rules.py` → `data_pipeline_rule_for`; router
      `_route_data_pipeline_event`: mirror + CRITICAL reuses incident pagerduty/telegram path, WARN deduped,
      short-circuits generic routing). **Router rules** `rules/data_pipeline_rules.py` loading `.registry.yaml` →
      `event_pattern → channels + severity` (INFO=channel; WARN=channel+dedup;
      CRITICAL=channel+telegram+pagerduty+incident-gateway). Wire into `router.route_event()`. — **alerting-service**
- [x] ✅ P0. **UAC rules + subscriber** DONE uac@6c27bfa0 (38 rules) + alerting@6e8b551 (subscriber consumes via
      existing topic, CONSOLIDATOR_DOWN path). **UAC `DATA_PIPELINE_ALERT_RULES`** (parallel to `LIVE_ALERT_RULES`)
      generated from the registry so emitters + router share one contract; subscribe the data-pipeline PubSub topic in
      `alert_subscriber`. — **unified-api-contracts, alerting-service**
- [x] ✅ P0. **Event constants** — DONE utl@39f8ec85 (37 DP\_\* + PIPELINE_HEARTBEAT in `events/event_types.py`,
      `DATA_PIPELINE_EVENT_TYPES` set, re-exported via `events/__init__`). **Event constants** for every `event:` in the
      registry added to UTL `events/event_types.py` (DP\_\* family), so log_event(DP\_\*) from any VM/watcher/audit
      routes correctly. — **unified-trading-library**
- [x] ✅ P1. **Escalation hop** DONE deployment-service@5866f12 (`data_pipeline_monitors/escalation.py::route_finding`:
      `auto_recover`/`file_issue`[writes PM issue-doc + pings inbox; defers via event details when no PM clone on
      disk]/`page_operator`; DP\_\* always emitted). **Escalation hop** mirroring `ci_failure_watcher.py`: `file_issue`
      tier auto-files `plans/active/issues/<slug>_<date>.md` + pings the orchestrator inbox when a deterministic
      candidate list is non-empty; `auto_recover` runs the in-band fix; `page_operator` routes CRITICAL with no recover
      scope. — **deployment-service / unified-trading-pm**
- [x] ✅ [DISCOVERY] P2. **RECONCILED + DONE 2026-06-22**: the Wave-3 sub-agent's `quality-gates-v2.yml` edit was NOT
      off-scope drift — it was a correct (premature) application of the in-flight cicd template rollout. Real owner =
      `cicd_release_machinery_2026_06_18.md` P1 (NOT orchestrator_master). I finished the full fleet rollout (12 repos
      committed+pushed, drift green) — see that plan. Original (superseded) note: **Off-scope find (Wave-3 sub-agent
      drift, discarded here)**: a valuable `escalate-ldr-qg-failure` job for `quality-gates-v2.yml` (FAILED promotion-PR
      → `repository_dispatch escalate-to-orchestrator` with `wall_type=ldr_qg_failure`) + a `dispatch-cloud-build`
      staging→main trigger fix (A3 decoupling orphaned it). Belongs in the PM **template** (not a per-repo edit —
      drift), rolled out fleet-wide via `rollout-workflow-templates.sh`. File under `orchestrator_master` P2
      'event-driven LDR-QG-failure escalation'. NOT shipped in this plan.
- [x] ✅ P1. **Channel+accessors** DONE alerting@6e8b551 (CONFIGURATION.md row) + deployment-service@5866f12 (terraform
      SM accessor for DATA_PIPELINE_ALERTS_SLACK_WEBHOOK → unified_trading + t1_batch SAs). Register the channel in
      `alerting-service/docs/CONFIGURATION.md` + the three terraform SA accessors for
      `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`. — **alerting-service, deployment-service**

## Phase 1 (KEYSTONE) — Proof-of-honest-absence gate + daily empty re-probe (closes C1)

> The writer already rejects a _blank_ reason (`LegacyBlankErrorReasonError`, after the 2026-05-07 RED ALERT). The
> remaining gap: `record_empty(reason=SOURCE_RETURNED_ZERO)` is taken on **trust** — nothing proves the HTTP call
> returned 200+empty rather than a 401/403/429/5xx/timeout/exception that fell through. This phase makes honest-absence
> a **proven** state, not a claimed one. **This is the highest-priority phase.**

- [x] ✅ P0. Define `FetchEvidence` value-object in UAC — DONE uac@6c27bfa0 (FetchEvidence.proves_honest_absence +
      FetchErrorSignal StrEnum + DISQUALIFYING_FETCH_SIGNALS + UnprovenHonestAbsenceError; QG green 220s, 59 tests).
      Define `FetchEvidence` value-object in UAC (`unified_api_contracts.canonical.crosscutting`):
      `{http_status:int, response_received:bool, rows_in_response:int, source, endpoint, attempted_at, error_signal:str|""}`.
      The closed set of **disqualifying signals** (any present ⇒ NOT honest-absence ⇒ must `record_failed`): non-2xx
      HTTP, auth (401/403), rate-limit (429/`RATE_LIMITED`), 5xx, timeout/`CONNECT_ERROR`, exception-in-adapter,
      empty-key/`MISSING_CREDENTIAL`, empty-but-source-was-never-reached. — **unified-api-contracts**
- [x] ✅ P0. **KEYSTONE LIVE** — DONE utl@39f8ec85: `record_empty` gains `fetch_evidence: FetchEvidence|None`;
      SOURCE_RETURNED_ZERO without `.proves_honest_absence()` emits DP_UNPROVEN_HONEST_ABSENCE(CRITICAL)+raises
      UnprovenHonestAbsenceError (hard-raise, operator 2026-06-22). EXPECTED\_\* exempt. 15 test files + 2 internal
      callers threaded; QG green 117s. Gate `record_empty(reason=SOURCE_RETURNED_ZERO)` in `_writer_record.py`: require
      an accompanying `fetch_evidence` proving
      `http_status in 2xx AND response_received AND rows_in_response==0 AND error_signal==""`; otherwise raise
      `UnprovenHonestAbsenceError` (callsite hint, steers to `record_failed`). EXPECTED\_\* calendar reasons are exempt
      (no fetch attempted). — **unified-trading-library**
- [x] ✅ [CODE] P0. Thread `fetch_evidence` from the adapter HTTP layer (the UAC `classify_venue_error()` site that
      already exists per-adapter) into the manifest writer, for all 5 AGs — DONE **market-tick-data-service@fbac3a9**
      (defi/tradfi/extended/cefi/prediction handlers + live runner + sentinels + orchestrator catalog readers threaded;
      17 source files + 17 tests + extracted `_ws_window_helpers.py`; QG green, sentinel == HEAD) +
      **instruments-service@c4687fc** (sports/defi IS threading, peer-lane). **GREP-PROOF**:
      `check_source_returned_zero_needs_fetch_evidence.py` returns 0 unproven callsites for BOTH MTDS and IS — every
      `record_empty(SOURCE_RETURNED_ZERO)`/`record_zero_rows` reachable from a fetch/except is now evidence-gated;
      exception/401/403/429/5xx/timeout/missing-key paths route to `record_failed`. Bonus C6 fix: 4 orchestrator catalog
      readers + 3 `_instruments_metadata.py` sites aligned env-less→env-short `resolve_bucket_name` (the defi-6%
      stale-read class, DP-ENV-001). — **market-tick-data-service, instruments-service**
- [x] ✅ P0. Unit gate tests DONE utl@39f8ec85 (`test_record_empty_fetch_evidence_gate.py`:
      None/signal/401/429/500/rows>0/not-received raise; EXPECTED\_\* exempt). Unit: a 401/429/timeout/exception path
      that previously stamped `SOURCE_RETURNED_ZERO` now raises `UnprovenHonestAbsenceError`; a genuine 200+empty
      passes. One test per disqualifying signal. — **unified-trading-library, market-tick-data-service**
- [x] ✅ P0. **Daily empty re-probe** — DONE e2e-testing@c045426 (`scripts/audit/reprobe_new_empty_confirmed.py`):
      cross-cutting SELECTOR (today's `empty_confirmed`+`SOURCE_RETURNED_ZERO` rows per AG, from the availability
      index) + UAC coverage-oracle cross-check (`expected_coverage()`) + `DP_EMPTY_REPROBE_DISAGREEMENT` (WARN) emit
      when oracle `SHOULD_HAVE_DATA` (or a wired re-fetch returns rows) + Phase-5 issue-file on ambiguous. **Per-AG live
      re-FETCH is a clean extension point** — `register_reprobe_hook(asset_group, hook)` where
      `hook: (asset_group, venue, data_type, day) -> ReprobeResult(reached_source, rows_returned, detail)`; the per-AG
      agents implement `reprobe_source(...)` + register it (the per-adapter HTTP/auth wiring is theirs, the
      cross-cutting selector/oracle/emit is shipped here). Tests planted a same-day SOURCE_RETURNED_ZERO row +
      oracle-disagree → emits. — **e2e-testing**
- [x] ✅ [RATCHET] P1. QG ratchet — DONE `unified-trading-pm@894610bc2` (sibling check
      `scripts/quality_gates/check_source_returned_zero_needs_fetch_evidence.py`, QG STEP 5.99; AST
      except-reachability + `fetch_evidence=` kwarg detection; baseline `{}` = 0 except-nested unproven sites on origin,
      synthetic-fixture verified the detector fails the bad pattern + passes the threaded one; wired into
      `base-service.sh` → picked up by MTDS+IS). Static check banning `record_empty(...SOURCE_RETURNED_ZERO...)`
      reachable from an `except`/error branch without `fetch_evidence`. Baseline-down counter. —
      **market-tick-data-service, instruments-service**

## Phase 2 — data-pipeline-alerts channel + streaming events + exit_code-aware fleet monitor (closes C4/C5; partial C7)

- [x] ✅ P1. **event family+route+webhook** DONE alerting@6e8b551. Add a typed **data-pipeline event family** +
      `route_event` rule + `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` for the existing `data-pipeline-alerts` channel. Verbose
      to start. — **alerting-service**
- [x] ✅ P1. **Heartbeat emitter** DONE utl@39f8ec85 (`emit_pipeline_heartbeat`) + deployment-service@5866f12
      (`heartbeat_stall_watcher.py` → DP_VM_STALL/DP_EVENT_LOOP_STARVED, `*/5` Cloud Run Job). **Heartbeat emitter**: a
      running batch/live VM emits a periodic
      `PIPELINE_HEARTBEAT{vm, ag, data_type, rows_captured_cum, last_progress_at}` (reuse the durable-log substrate from
      `vm_launcher_durable_log_observability`). Silence > N min ⇒ stall alert. Closes the "idle/hung VM emits nothing"
      gap. — **unified-trading-library, deployment-service**
- [x] ✅ P1. **Exit_code-aware fleet monitor** DONE deployment-service@5866f12 (`exit_code_fleet_monitor.py`: reads GCS
      run.log terminal exit_code [survives self-delete] + manifest captured-climbed cross-check →
      DP_VM_EXIT_NONZERO/DP_VM_GONE_NO_CAPTURE CRITICAL, `*/5`). **Exit_code-aware fleet monitor** (closes the C4
      self-delete blind spot, per CLAUDE.md 2026-06-22 rule): per VM, read the persisted GCS `run.log` terminal
      `exit_code` (survives self-delete) + cross-check manifest `captured` climbed; alert on
      `exit_code!=0 OR captured flat`. Reuse `backfill_vm_silent_worker_stall_watchdog` signal. — **deployment-service**
- [x] ✅ [CODE] P1. **Heartbeat-cadence BUG FIX — the 60s timer died after boot on a real VM** — DONE
      **unified-trading-library@8d35385**. Runtime evidence on `tm-backfill-20260622-201951` (+odds-live):
      `PIPELINE_HEARTBEAT` appeared only ~2× bunched ~2s apart at boot (those were the per-DATE/per-window emits on the
      main thread for fast empty chunks) then NOTHING for 24min+ while the worker actively progressed → the 60s
      `PipelineHeartbeatTimer` was NOT producing its steady cadence. ROOT CAUSE: the daemon-thread loop control-flow is
      sound (`Event.wait`/`stop`), so the silence was a **BLOCKED emit**, not a dead loop —
      `emit_pipeline_heartbeat`→`log_event`→ the cloud `EventSink.write_event` does a SYNCHRONOUS GCS/PubSub publish
      with NO native timeout; on a busy VM (GIL held by a blocking sync scrape, or a slow/stuck publish) that call
      blocks the heartbeat thread INDEFINITELY, and a plain `try/except` cannot un-block a call that never returns → one
      hung tick froze every later tick. FIX: `_emit_once` now runs the publish on a throwaway daemon thread joined with
      a **hard per-tick timeout** (`PIPELINE_HEARTBEAT_EMIT_TIMEOUT_SEC=10s`, well under the 60s interval) — a wedged
      publish is abandoned + logged and the main loop proceeds to its next `Event.wait(interval)` tick → a truly steady
      cadence for the VM's whole life. Fixes BOTH instruments-service + MTDS (shared UTL primitive). 2 new regression
      tests (`test_steady_cadence_keeps_firing_not_just_at_start` ≥3 over ~3.5s spanning the window;
      `test_a_blocking_emit_does_not_freeze_the_cadence` — the keystone guard) + 7 existing, QG green (sentinel==HEAD).
      Dirty-deps direct-LDR carve-out (UAC dep live-dirty, peer WIP, not mine). — **unified-trading-library**
- [x] ✅ [CODE] P0. **Heartbeat-cadence BUG FIX #2 + watcher BLIND-SPOT — "zero real alerts in 1.5h" root cause (the
      @8d35385 timeout guard alone did NOT fix it)** — DONE **unified-trading-library@5e10ed0d** +
      **deployment-service@625955f**. Operator 2026-06-22: ZERO Slack alerts in 1.5h for any AG VM despite the infra
      being up. Live diagnosis on the running sports VMs (`probe_hb.py` against the prod GCS log bucket): every running
      VM read **VERDICT=alive** because the heartbeat watcher keyed liveness on the GENERIC infra
      `vm-heartbeat/{vm}.txt` sidecar (`hb_age=0.5min`, ALWAYS fresh — `vm_heartbeat_sidecar.sh` ticks every 60s
      regardless of worker health), and the running `tm-backfill` run.log had **0 `PIPELINE_HEARTBEAT`**. TWO real bugs
      the timeout guard missed: (1) **BUG1 — `PipelineHeartbeatTimer._run` waited a full `interval_sec` BEFORE its first
      emit** (`while not self._stop.wait(interval)`), and the IS/MTDS backfills re-exec python ONCE PER CHUNK
      (`VM_CHUNK_DAYS` loop) so the timer is born+dies per chunk-process — a sub-60s chunk emitted ZERO; FIX = emit ONE
      heartbeat IMMEDIATELY on entry (UTL `events/__init__.py::_run`) + a VM-life bash emitter
      (`setup-data-pipeline-vm.sh::_launch_with_tee`, covers EVERY data task — chunked backfill AND single-process live)
      echoing a parseable `PIPELINE_HEARTBEAT vm=.. ts=..` marker to stdout→run.log→GCS for the VM's whole life,
      spanning per-chunk re-exec. (2) **BUG2 — the watcher was BLIND to a never-heartbeating VM**: it read the
      always-fresh infra sidecar, so a VM whose data worker died/never launched/has a broken timer read ALIVE → never
      alerted. FIX = `_gcs.pipeline_heartbeat_age_minutes` parses the WORKER `PIPELINE_HEARTBEAT` run.log marker
      (decoupled from the infra sidecar); `heartbeat_stall_watcher.sweep` now keys liveness on it; a running data VM
      (discovered from `gcloud compute instances list` via the CLI `_list_running_vms` → `_is_data_vm`) past the 10-min
      grace with NO worker marker → `DP_EVENT_LOOP_STARVED` (DP-VM-004). PROOF: (a) reshipped
      `tm-backfill-20260622-230311` emits the marker at a STEADY ~60s cadence in run.log (≥5 ts ~60s apart, ≥8-min span
      — verifier output in Progress Log); (b) a REAL `DP_EVENT_LOOP_STARVED` for a silent sports VM DELIVERED to
      `#data-pipeline-alerts` via the alerting notifier `send_data_pipeline_alert` → **HTTP 200 OK +
      `SLACK_MESSAGE_SENT channel=data-pipeline-alerts`** (the router path the watcher→subscriber runs, NOT the manual
      webhook test). 4 new regression tests (UTL `test_emits_immediately_before_the_first_interval_elapses`;
      deployment-service `test_silent_vm_with_fresh_infra_sidecar_still_alerts` [the keystone], `*_healthy_*`,
      `pipeline_heartbeat_age_*`), QG green both repos (sentinel==HEAD). SPORTS tarball rebuilt + 3 sports VMs reshipped
      (tm-backfill-230311 / fs-backfill-230327 / mtds-live-sports-230346). — **unified-trading-library,
      deployment-service**

> **Residual forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md`: per-source rate-limit /
> health event (`SOURCE_RATE_LIMITED`, `SOURCE_KEY_POOL_EXHAUSTED`).

- [x] ✅ P2. **Three meta-watchers** DONE deployment-service@5866f12 (`meta_watchers.py`: DP_CATALOG_NOT_RUNNING[per-AG
      24h] / DP_ZOMBIE_WATCHDOG_DOWN / DP_CRON_DID_NOT_FIRE, `*/15`). **Three meta-watchers** (the "is the watcher
      itself running" gap): (a) instrument-catalogue-not-running per AG (no catalogue artifact refreshed in 24h); (b)
      zombie-VM-watchdog-itself-down; (c) consolidator-not-running (extend existing `CONSOLIDATOR_DOWN` to a per-AG
      cron-alive check). All → `data-pipeline-alerts`. — **deployment-service**

> **Residual forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md`: streaming events pane in
> deployment-ui (tails the live VM event stream per AG/VM).

## Phase 3 — Daily per-AG completion summary + once-daily manifest-hygiene-vs-GCS audit (closes C2/C3/C6/C7)

- [x] ✅ P1. **Daily per-AG completion digest** — DONE e2e-testing@c045426
      (`scripts/audit/data_pipeline_daily_digest.py`, cron `0 7 * * *` UTC): reads each AG's availability index,
      computes the 4-state ratio (the `derive_capture_status_rates` formula REPLICATED in
      `_dp_common.capture_status_counts` — NOT a deployment-api import, per the service↔service ban), **unions across
      sources** (≥1 source captured ⇒ cell captured), splits batch/live/replay by `pipeline_mode`, breaks down per
      venue/chain/data_type, surfaces the worst-10 cells + overall %. Posts an INFO `DP_DAILY_DIGEST` via `log_event`
      (alerting router mirrors → channel; never Slack-direct). Test asserts the union + ratio on a 2-source fixture. —
      **e2e-testing**
- [x] ✅ P1. **Hygiene orchestrator** — DONE e2e-testing@c045426 (`scripts/audit/manifest_hygiene_daily.py`, cron
      `0 8 * * *` UTC): read-only, one consolidated RED/GREEN per AG composing the existing tools — phantom
      (`reconcile_phantom_manifest_rows_all.py --dry-run` subprocess), divergence (`detect_manifest_divergence.py`
      subprocess), path-canonicality (UAC `canonical_path_violations` over the index's path column), v9-distribution
      (CF-1 logic inline), 4-pillar (`validate_shards_4pillar.py` subprocess). Emits a DP\_\* WARN per non-empty
      finding-class (`DP_NOT_V9`/`DP_DIVERGENT_EMPTY`/`DP_NONCANONICAL_PATH_ON_DISK`/`DP_PHANTOM_ROWS`/
      `DP_SHARD_PILLAR_FAIL`), writes candidate CSVs to `plans/audit/results/manifest_hygiene_<AG>_<date>.csv`, files a
      Phase-5 escalation issue when non-empty. **COST-AWARE**: `--mode changed` (daily default) runs ONLY the index-only
      checks (v9/divergence/path) — NO full-corpus walk; `--mode full` (weekly) adds the phantom + 4-pillar GCS walks;
      every scope-out is LOGGED (no silent caps). Test plants a non-v9 + non-canonical row → flagged. — **e2e-testing**
- [x] ✅ P1. **Path-canonicality validator** `is_canonical(path)` in UAC — DONE uac@6c27bfa0 (is_canonical +
      canonical_path_violations; rejects hyphen-day / glued VENUE-CHAIN / glued V{N} / out-of-set AG; round-trips
      builders). **Path-canonicality validator** `is_canonical(path)` in UAC (today `partition_paths.py` only BUILDs):
      parse a GCS path and assert it matches the canonical builder output for its AG/pipeline_mode/schema. Closes C3.
      Reused by the hygiene orchestrator AND the Phase 4 writer-side assert. — **unified-api-contracts**
- [x] ✅ **Reader/writer bucket-env parity check** (closes C6) — DONE `market-tick-data-service@0eee1ab` (QG STEP 5.91,
      `scripts/quality_gates/check_reader_writer_bucket_parity.py`, warn-only ratchet). LANDED once the dep window
      opened (UAC/UTL clean). **It FOUND 8 GENUINE C6 reader bugs** (env-less `build_bucket`/`get_bucket_name` reads vs
      env-short `-prd-` writers → stale-read → false honest-absence → zero-capture; the defi-6% class) — filed as the P1
      todo below; the defi lane already fixed one (`mtds@059df5f`, live IS-universe reader). —
      **market-tick-data-service**
- [x] ✅ [CODE] P1. **Fix the 8 C6 reader-bucket-env bugs** the parity check found — **8 of 8 SHIPPED on origin/LDR**
      [doc-reconciliation 2026-07-12, finding 194, §A2 B-queue ruling] (was: "[~] ... 7 of 8 SHIPPED" — the 8th site,
      `live/websocket_runner.py` `_read_is_parquet_sync`, is confirmed SHIPPED per the later `[x]` entry below at
      `market-tick-data-service@059df5f`; re-verified via `git log`/`git show origin/live-defi-rollout` in this pass —
      commit present on `live-defi-rollout`, and current HEAD `websocket_runner.py:513-516` calls
      `_instruments_store_bucket`, confirming the fix landed) (`market-tick-data-service@fbac3a9`, swept in via the
      peer's keystone-threading quickmerge): all sites aligned to
      `resolve_bucket_name(cloud=..., kind="instruments-store", asset_group=...)` (env-short `-prd-`, the IS writers'
      bucket). DONE: `engine/orchestrator/__init__.py:445/447/449/451` (`_register_all_catalog_readers` — 4 AG catalog
      readers, F4 expected-universe path; `get_bucket_name("instruments",ag)` was env-LESS Group-A
      `instruments-store-{ag}-{pid}` → confirmed genuine bug, fixed) +
      `cli/handlers/_instruments_metadata.py:218/442/518` (3 defi reads — the EXACT CLAUDE.md-documented defi-6% bug).
      Test `test_instruments_metadata_loader.py` updated to assert the env-short bucket (the prior 2 assertions encoded
      the bug — diagnosed test-wrong-not-code-wrong). Live-probe verified:
      `resolve_bucket_name(kind="instruments-store", asset_group="defi")` → `instruments-store-defi-prd-{pid}` (vs the
      OLD env-less `instruments-store-defi-{pid}`). **8th site — `live/websocket_runner.py` `_read_is_parquet_sync`
      (`build_bucket("instruments",…)`) — was: "DEFERRED to the live MTDS-threading lane"; now SHIPPED, see the `[x]`
      entry below (`mtds@059df5f`)** (`data_completion_to_100_all_ag`): at the time of this diagnosis the file carried a
      large in-flight `fetch_evidence`-threading refactor the peer was actively committing (fbac3a9/26202e1); a clean
      local QG sentinel was also blocked by an environmental semver version-alignment lag (PM clone 11 behind
      origin/main; `--skip-version-alignment` is human-only). Fix was fully prepared + validated (helper
      `_instruments_store_bucket(ag)` mirroring the prediction reader; ruff/basedpyright-baseline/31-tests green; method
      ≤50L) — landed on the threading lane's next clean window (see below). Parity check is **warn-only** so the fleet
      was never reddened by the interim gap. Provenance: bucket-parity check `wip-preserve@32e8b6e`. —
      **market-tick-data-service**

> **Residual forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md`: close the
> `audit_criteria_automation` honest-SKIPs (CF-10 phantom, CF-14 catalogue). **Residual forked 2026-07-24** →
> `data_pipeline_alert_substrate_residual_2026_07_24.md`: v9-readiness gate in the daily digest (surface
> `schema_version` distribution per AG).

- [x] ✅ [CODE] P0. **Chain-blind defi DIVERGENT_EMPTY root cause — flat-protocol launch gate (C2)** — DONE
      `unified-api-contracts@c8f4bbd7` (QG green 213s, 45 oracle tests pass; landed on LDR). The `DP_DIVERGENT_EMPTY` +
      `DP_EMPTY_REPROBE_DISAGREEMENT` defi alerts were driven by the UAC `expected_coverage()` oracle being
      **chain-blind + flat-venue-blind**: the manifest writes FLAT venue names (`UNISWAP_V4`, `CURVE`, `AAVE_V3`,
      `ETHERFI`…) but `DEFI_VENUE_LAUNCH_DATES` was keyed mostly by `PROTOCOL-CHAIN` (`UNISWAP_V4-ETHEREUM`=2025-01-31),
      so the exact launch lookup MISSED → the pre-launch gate never fired → the oracle returned `SHOULD_HAVE_DATA` for
      every date back to the 2018 window-start, flagging tens of thousands of **honest pre-launch empties** as
      divergent. ALL 85,900 divergent cells were historical (max 2025-11-18; the operational window was already 0). Fix:
      `_venue_launch_date_for` now falls back to the EARLIEST `PROTOCOL-*` chain launch for a flat defi protocol
      (conservative floor) + added 13 missing bare-protocol launch dates
      (MORPHO/AERODROME_V3/CAMELOT_V3/FLUID/SPARK/PUFFER/SWELL/STAKEWISE/STADER/MANTLE/ANKR/COINBASE/EIGENLAYER).
      Measured: **85,900 → 22,140 DIVERGENT_EMPTY (−74%)**, 0 in operational window. 5 regression tests added. —
      **unified-api-contracts**
- [x] ✅ [CODE] P1. **Residual defi DIVERGENT_EMPTY — DeFi per-(venue,data_type) `coverage_start` registry (C2)** — DONE
      `unified-api-contracts@bfe6736b` (QG green --no-fix, 27 oracle tests incl. 6 new defi). Added
      `DEFI_DATA_TYPE_COVERAGE_START` to `canonical/coverage_starts.py` (20 measured first-capture floors across 14
      venues, read live from the prod defi `_index` 2026-06-22 = 925,820 captured rows) + wired
      `get_source_coverage_start_for_data_type` to consult it BEFORE the capability dict. **PER-PAIR + DATA-DRIVEN, NO
      flat fallback** (operator HARD POINT): each pair has its own measured floor; a pair absent → None (= no clip).
      Verified: pre-collection dates (e.g. AERODROME_V3 dex_pool_state < 2024-05-01, PANCAKESWAP_V3 dex_pool_swaps <
      2024-01-01) now return `EXPECTED_PRE_SOURCE_COVERAGE_START`; interior gaps AFTER the floor (UNISWAP_V3 swaps
      2023-08-08) correctly STAY `SHOULD_HAVE_DATA`. Clips ≈8,380 of the 22,140 (the genuine pre-collection prefix). The
      flat value is the EARLIEST across chains the pair was captured on (conservative; matches the chain-less grain of
      the divergence oracle). The REMAINING ~13,760 are NOT pre-collection — they split into the two real-gap classes
      below. — **unified-api-contracts**

> **Residual forked 2026-07-24** → `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`: the defi
> DIVERGENT_EMPTY real-gaps (13,760, 2 classes) per-venue backfill-vs-scope campaign — name-drift reconciliation
> (AAVE_V3/MORPHO/COMPOUND_V3 lending) + never-collected/ out-of-MVP triage. Operator HARD RULE: no flat clip.

- [x] ✅ [CODE] P2. **`reprobe_defi.py` chain-blind false-disagreement bug (C2)** — DONE `e2e-testing@4cfbbf1` (QG
      --no-fix exit 0, sentinel==HEAD, 20 dp_audit tests green incl. 3 new; dirty-deps direct-LDR carve-out —
      strategy-service had live PEER WIP at quickmerge time). Threaded `chain` through the shared `ReprobeHook`
      signature → `ReprobeCandidate.chain` → `_select_new_empties` (dedup now by **(venue,data_type,CHAIN)**, not flat)
      → `_crosscheck` → the hook → the auto-flip reclassifier match (now **(venue,data_type,chain)**-keyed — a flip
      can't clear an empty on a chain the protocol was never deployed on). `reprobe_defi.reprobe_source` probes the
      empty's OWN chain + SHORT-CIRCUITS `reached_source=False` when the protocol has no subgraph on that chain
      (CURVE/OPTIMISM no longer false-clears via ETHEREUM) AND when chain is blank. cefi/sports hooks accept+ignore
      chain. New regression tests: chain-keyed dedup / two-chains-two-cells / blank-chain-never-clears. —
      **e2e-testing**

### Wave 4b out-of-repo wiring (the daily-audit scripts shipped in e2e-testing; these reach other repos)

> The three daily audits + the `_dp_common` substrate landed in `e2e-testing/scripts/audit/` (QG-green). The remaining
> hops touch sibling repos and are dispatched here (per the fan-out-is-a-tracked-todo rule). Cold-start context: the
> scripts run from `e2e-testing/scripts/audit/`, are read-only over the manifest/GCS, emit DP\_\* via UTL `log_event`,
> and write candidate CSVs + issue docs to the PM clone.

- [x] ✅ **Wire the three audit scripts into MTDS QG (STEP 5.90, not 5.89 — 5.89 already taken on origin)** — DONE
      `market-tick-data-service@0eee1ab`. All 3 audits support `--smoke` (smoke-passed); `_dp_common.py` lint-only.
      Mirrors STEP 5.88 (ruff + `--smoke` warn-only, `QG_BLOCK_NETWORK`/`CLOUD_BUILD` guard). Landed with the
      bucket-parity check when the dep window opened. — **market-tick-data-service**
- [x] ✅ [INFRA] P1. **Schedule the three daily-audit crons** — DONE `deployment-service@7b84146`
      (`terraform/gcp/data_pipeline_audit_scheduler.tf`: 4 Cloud Run Jobs + 4 Cloud Scheduler crons mirroring
      `cf_manifest_audit_scheduler.tf` — runtime SA `unified_trading`, invoker `t1_batch`, env
      `GCP_PROJECT_ID`/`DEPLOYMENT_ENV`/`CLOUD_PROVIDER`, `max_retries=0`): `dp-daily-digest` @ `0 7 * * *`,
      `dp-manifest-hygiene-changed` @ `0 8 * * *`, `dp-manifest-hygiene-full` @ `0 8 * * 0` (weekly `--mode full`),
      `dp-reprobe-empty` @ `0 9 * * *` UTC. **CAVEAT — the jobs do not RUN until the image gap below is closed** (no
      existing image bundles the e2e audit scripts; `var.dp_audit_image` defaults to the MTDS image which lacks
      `/app/e2e-testing/...`). — **deployment-service**
- [x] ✅ [INFRA] P1. **Build the e2e-audit container image** — DONE: Cloud Build `e3cd1017` SUCCESS →
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/e2e-audit:latest` (digest
      `sha256:13f3851206080fe8a38b3dc26a2d8ffdd178a5630b4b21c46bfc72d1b7877bf9`), `FROM` UTL base (DP\_\* events
      present), `COPY . /app/e2e-testing`. **In-build smoke GREEN** — all 3 audits import+arg-parse inside the image.
      The image is LIVE in Artifact Registry now. Source (`e2e-testing/Dockerfile`+`cloudbuild.yaml`) +
      `var.dp_audit_image` default → on `origin/wip-preserve/e2e-audit-image-2026-06-22@48b23114` +
      `origin/wip-preserve/dp-audit-image-var-2026-06-22@1d49f962`, quickmerge dirty-dep-blocked (live peer UAC +
      strategy-service) → land both when deps clean. — **e2e-testing, deployment-service**

> **Residual forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md`: apply the data-pipeline-audit
> terraform (4 dp-audit Cloud Run Jobs + 4 schedulers).

- [x] ✅ P1. **Register `DP_DAILY_DIGEST` + `DP_HYGIENE_SUMMARY`** — DONE registry@PM 6e0ef283c + uac@63cb2bbd (DIGEST
      category + 2 INFO rules, parity test 40 rules green). Digest now ROUTES to #data-pipeline-alerts. UTL
      string-constants (cleanliness, non-routing) left on-disk in slot clone — see todo below.
- [x] ✅ [SCRIPT] P1. **Reduce `#data-pipeline-alerts` emit-side spam** — e2e-testing@949fdc3. Digest `run()` now emits
      `DP_DAILY_DIGEST` EXACTLY ONCE (union over all AGs: `details={message, asset_groups, per_ag}`) instead of the 5×
      per-AG fan-out; every AG-scoped `emit_dp_event` in the 3 audit scripts (`manifest_hygiene_daily` DP_NOT_V9/etc +
      `reprobe_new_empty_confirmed` DP_EMPTY_REPROBE_DISAGREEMENT) now carries `asset_group` + a human one-line
      `message` so alerts render `… asset_group=X … <summary>` not bare `[DP_X] DP_X`. Tests: union-emitted-once for a
      5-AG run + hygiene emit carries `asset_group`+`message` (`tests/unit/test_dp_audit.py`, 27 pass). QG green.
      **e2e-audit image must be REBUILT to go live**
      (`gcloud builds submit --config=cloudbuild-e2e-audit.yaml --region=asia-northeast1 .`). — **e2e-testing**

> **Residual forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md`: UTL
> `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` string constants (cleanliness only).

## Phase 4 — Writer-side path + state invariants (defence-in-depth, closes residual C3/C7)

> **Forked 2026-07-24** → `data_pipeline_alert_substrate_residual_2026_07_24.md` (both todos moved verbatim: writer-side
> `is_canonical()` assert on `record_captured`/`record_empty`, and the live==batch schema invariant assert).

## Phase 5 — Scripted→LLM escalation hop (the planning-VM handoff)

- [x] ✅ P2. Define the handoff — DONE e2e-testing@c045426 (`scripts/audit/_dp_common.py` `file_escalation_issue()` +
      `write_candidate_csv()`, shared by the hygiene + re-probe audits): deterministic scripts write candidate lists to
      `plans/audit/results/<slug>_<date>.csv`; when non-empty, `file_escalation_issue` auto-files
      `plans/active/issues/<slug>_<date>.md` (the standard `title`/`created`/`author`/`source`/`locked_by` frontmatter +
      `## What I found` / `## Why it matters` / `## Recommended decision` body, idempotent per (slug, UTC-day)) for a
      planning-VM slot. Both the hygiene RED and the re-probe disagreement paths call it. Test asserts the doc is
      written with the candidate CSV linked. — **unified-trading-pm (issue/CSV are data output to the PM clone) +
      planning-VM**

## Codex SSOT updates (mandatory before archival)

- [x] ✅ [DOC] P2. `/codex/02-data/availability-manifest-and-data-status.md` — DONE `unified-trading-pm@894610bc2` (new
      §6a "Proof-of-honest-absence contract": FetchEvidence 4-condition `proves_honest_absence()` gate +
      `UnprovenHonestAbsenceError` hard-raise + 10-member `FetchErrorSignal` disqualifying set + EXPECTED\_\*
      exemption + STEP 5.99 twin ref).
- [x] ✅ [DOC] P2. `/codex/02-data/honest-absence-downstream-handling.md` — DONE `unified-trading-pm@894610bc2` (new
      "Daily re-probe + escalation flow": selector → UAC oracle cross-check → `DP_EMPTY_REPROBE_DISAGREEMENT` WARN →
      Phase-5 issue-file; `register_reprobe_hook` extension point).
- [x] ✅ [DOC] P2. `/codex/05-infrastructure/data-pipeline-alerts.md` — VERIFIED complete `unified-trading-pm@894610bc2`
      (Phase-0 already shipped it covering channel/DP\_\* families/watchers/digest+hygiene cadence/verbose→zeroed
      policy; no edit needed).

## Success criteria

- A misclassified empty (401/429/timeout/exception) is **impossible to commit to the manifest** — it raises at the
  writer (Phase 1). Verified by per-signal unit tests.
- Today's new `empty_confirmed` cells are re-probed daily; disagreements alert (Phase 1).
- Any running batch/live VM streams heartbeat+progress; an idle/hung/exit-nonzero VM alerts within N min (Phase 2).
- Daily per-AG completion digest + once-daily hygiene-vs-GCS RED/GREEN posted to `data-pipeline-alerts` (Phase 3).
- Non-canonical path / non-v9 / phantom / divergence each have a deterministic daily check, with LLM-escalation for
  ambiguous verdicts (Phases 3/5).

---

> **History extracted 2026-07-24 (3rd pass)** →
> `/plans/archive/2026_07/data_pipeline_hardening_self_monitoring_history_2026_07_24.md`: the entire remaining
> historical Progress Log + per-AG dispatch/report content (see banner above for the exact section list) moved verbatim
> to that file's end. Every checkbox that was in the moved content is `[x]`; the single open todo below was left here
> unchanged.

## Open work

### REAL OUTAGE surfaced by the fixed watcher (P0 — needs recovery)

- [x] ✅ **9 live data VMs frozen 5.5–32h, silently RUNNING, zero capture** — the old infra-sidecar watcher was blind to
      all of them: `mtds-live-cefi-deribit-{book-snapshot-5,derivative-ticker,trades}` (~6.8h),
      `mtds-live-cefi-hyperliquid-{book-snapshot-5,derivative-ticker,trades}` (~6.8h), `mtds-live-tradfi-cme-trades`
      (5.8h), `tradfi-bf-cme-ohlcv-1m-ym-2020` (5.5h), `tradfi-fwd-daily-cron-20260621-154132` (32h). Diagnose root
      cause per family (binance live had a fatal `ValueError: live_tick_blob_path … glued 'VENUE-CHAIN' token` at 23:41
      → likely the same non-canonical-path crash class across the cefi live VMs) + relaunch. (deployment-service / mtds)
  - ✅ **DONE-WHEN SATISFIED 2026-08-09 (slot-24, per `/vm-preemption-billing-waste-audit`'s execution mechanism, scoped
    to cefi + tradfi live-capture)**: the ORIGINAL 2026-06-23 finding (these exact VM names silently RUNNING-but-frozen)
    is conclusively stale — none exist under any name (`gcloud compute instances list`, GCP `central-element-323112` +
    AWS `427895769566`/`ap-northeast-1`, both re-checked). Split outcome on the two families this todo names, resolving
    the (a)/(b) done-when for each independently:
    - **(a) CeFi — RECOVERED, flip.** `mtds-live-cefi-consolidated-20260809-121034` is RUNNING (the 2026-06-27
      consolidated MVP launcher superseded the old per-shard VMs this todo named). Its
      `_index/per_vm/mtds-live-cefi-consolidated-20260809-121034.parquet` manifest shard was written as recently as
      2026-08-09T16:07:18Z (checked same minute) and carries `capture_status=captured` rows for DERIBIT/HYPERLIQUID
      trades with `written_at` up to 2026-08-09T15:36 UTC — actively flowing, not frozen.
    - **(b) TradFi — genuinely stopped, NOT a flip; new P0 filed instead.** Zero `mtds-live-tradfi-*` VMs in either
      cloud; no heartbeat blob; no `_index/per_vm/mtds-live-tradfi*` shard; the full tradfi `availability_index.parquet`
      shows the newest `pipeline_mode~live` row (venue=CME) was written 2026-08-04T08:51:36 UTC — ~5.3 days stale at
      check time. Per the done-when's own branch (b), this is a NEW finding, not evidence against flipping THIS todo
      (whose literal named VMs are confirmed gone either way) — filed as
      `/plans/archive/2026_08/issues/tradfi_live_cme_capture_stopped_2026_08_09.md` with the relaunch + root-cause
      todos.
    - The 2026-07-25 blocker (`storage.buckets.list` 403 for `unified-trading-sa`) did not reproduce this session —
      `gsutil`/`resolve_bucket_name`-backed reads against both prod buckets succeeded ambiently; no IAM self-grant was
      needed.
  - 🟡 **STATUS-CHECK NEEDED (2026-07-24)**: this finding is now ~1 month stale (surfaced 2026-06-23). Per the
    async-wait/poll-discipline HARD RULE, re-verify current fleet state before assuming this is still live — either (a)
    re-run the exit_code/heartbeat fleet monitor sweep against the named VM prefixes and confirm whether they
    recovered/were relaunched/self-resolved, or (b) if genuinely still frozen, escalate as a fresh P0 rather than
    relying on this month-old entry. Not forked into a child plan — this is a status-check ask, not new scope.
  - 🟡 **PARTIAL RE-VERIFICATION (2026-07-25, plan-reconcile apply pass)**: `gcloud compute instances list` against
    `central-element-323112` for `mtds-live-cefi-deribit-*`, `mtds-live-cefi-hyperliquid-*`,
    `mtds-live-tradfi-cme-trades`, `tradfi-bf-cme-ohlcv-1m-ym-2020`, `tradfi-fwd-daily-cron-*`, and broader
    `deribit`/`hyperliquid`/`cme-trades`/ `live-cefi`/`live-tradfi` name substrings — **zero matches** (0 instances,
    exit 0) — none of the originally-named VMs still exist under this project. Cross-checked AWS (`427895769566`,
    `ap-northeast-1`) — only the orchestrator + human-planning VMs are running, no cefi/tradfi live-capture instances
    there either. **This does NOT confirm recovery** — it only confirms the specific "frozen, silently RUNNING"
    manifestation from 2026-06-23 is gone (the VMs no longer exist to be frozen); it is equally consistent with (a) a
    clean relaunch under fresh timestamped names I did not think to search for, (b) an operator/watchdog cleanup that
    terminated them without a relaunch, or (c) live capture for these families having stopped entirely. Could NOT check
    GCS object recency directly (`storage.buckets.list` denied for the `unified-trading-sa` service account in this
    session — 403). **Still open, needs a follow-up with either broader VM-name search + GCS manifest freshness check
    (`measure_honest_coverage.py --asset-group cefi` / `--asset-group tradfi`) or an operator-side confirmation** — NOT
    flipping this todo to done on this partial evidence.
  - ✅ **OWNERSHIP RESOLVED 2026-07-31 (corpus-wide ownership-conflict sweep)**:
    `cross_cutting_satellite_ao_dispatch_ batch2_2026_07_26.md` deliberately DECLINED to batch this and routed it to
    `/vm-preemption-billing-waste-audit`. That routing is correct and stands — but routed-away ≠ unowned, which is what
    made this a conflict. **This doc RETAINS the todo**; batch2 cites it and does not own it.
    `/vm-preemption-billing-waste-audit` is the execution mechanism, not a new owner. **Done-when** (so the next runner
    isn't left re-deriving it): run that skill scoped to the cefi + tradfi live-capture families, then either (a) name
    the current live VMs and cite a fresh manifest/GCS recency figure proving capture is flowing → flip this `[x]`, or
    (b) confirm live capture for these families is genuinely stopped → that is a NEW P0 finding and gets its own issue
    doc, not a flip here.

---

> **History extracted 2026-07-24** (2nd-pass line-cap trim, umbrella cap) →
> `/plans/archive/2026_07/data_pipeline_hardening_self_monitoring_history_2026_07_24.md`: the remaining fully-shipped
> Progress Log tail (ALERT SPAM REDUCTION through the TradFi databento outbound-call hardening entry,
> 2026-06-22→2026-06-24) moved verbatim — 0 open todos in the moved content.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY candidate PARKED (conflict) — stays KEEP-NA — the content IS bounded
  (re-measure a named VM set + a coverage check), but `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`
  deliberately DECLINED to batch it and routed it to `/vm-preemption-billing-waste-audit` instead ('re-measuring is
  cheap but belongs with … not a batch todo that would re-diagnose a stale snapshot'). Respecting that prior routing
  rather than overriding it.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- swapped the ag-residual
  sibling for the `/vm-preemption-billing-waste-audit` skill, the doc's own text names as the execution mechanism for
  its sole open P0 todo.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms the 2026-07-30 park: sole todo's execution mechanism
  was deliberately routed to /vm-preemption-billing-waste-audit by batch2, not folded into a batch todo — routed-away ≠
  unowned; this doc retains the todo, not re-litigating that routing.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-06 (unchanged): sole open P0 todo's execution
  mechanism was deliberately routed to `/vm-preemption-billing-waste-audit` by batch2; this doc retains ownership of the
  todo itself, not re-litigating that routing.
- **round11 RECLASSIFY sweep 2026-08-09**: **RECLASSIFY — `assigned_vm: NA` → `planning`.** Re-tested the sole open P0
  todo ("9 live data VMs frozen... zero capture") against today's accumulated precedents. The 2026-07-25 partial
  re-verification attempt stalled specifically because `storage.buckets.list` was **denied (403) for the
  `unified-trading-sa` service account** — that was the actual reason the Done-when (name the current live VMs + cite a
  fresh manifest/GCS recency figure, OR confirm capture genuinely stopped) was never completed, not a routing gap (the
  routing to `/vm-preemption-billing-waste-audit` by batch2 remains correct and unchanged). Per the 2026-08-08/09
  operator ruling that both cloud identities are IAM-self-service, an AO worker hitting this exact 403 should grant
  itself the missing permission (e.g. a project-level `roles/storage.objectViewer`/`storage.buckets.list`-carrying role
  for `unified-trading-sa`) rather than treating it as a dead end — this was the one thing blocking the doc's sole
  Done-when. Conflict-checked against all active `cross_cutting_satellite_ao_dispatch_batch*` docs and
  `cross_cutting_consolidated_closeout_2026_07_25.md` — no doc claims ownership of this specific todo,
  `/vm-preemption- billing-waste-audit` remains the named execution mechanism, this doc retains it. No finalize twin
  needed — this is the doc's own existing plan, not a new extraction; it dispatches as-is.
- **2026-08-09 (slot-24)**: sole open P0 todo flipped `[x]` — done-when satisfied (cefi live capture confirmed recovered
  via the consolidated launcher; tradfi live capture confirmed genuinely stopped since 2026-08-04, filed as a new P0
  issue doc per the done-when's own branch (b)). See the todo's own annotation for the full evidence trail. New issue:
  `/plans/archive/2026_08/issues/tradfi_live_cme_capture_stopped_2026_08_09.md`. All open work in this plan is now
  clear, unlocked, no gating finalize twin — ran the 6-step archival ritual same-turn per the HARD RULE:
  `status: complete`, ARCHIVED banner added, every live-corpus referrer (16 files: agents/, plans/active/\*,
  plans/epics/, codex/02-data/\*, codex/05-infrastructure/\*, codex/15-runbooks/incidents/\*) repointed to the new
  archive path (pre-existing `../`-relative forms converted to the leading-slash absolute convention in the same edit);
  already-archived docs' frozen historical citations (many pinned to specific line-number anchors describing past
  content) were deliberately left untouched — rewriting a path inside closed historical record without re-verifying its
  cited line ranges would misrepresent a re-verification that didn't happen. No codex contract changes needed — this
  plan's phases were already codex-aligned in earlier rounds; the one net-new fact (tradfi live capture down since
  2026-08-04) lives in the new issue doc, not a codex SSOT. `git mv` to `/plans/archive/2026_08/`.
- **2026-08-09 (slot-24), M3-verification split-commit recovery**: the combined flip+`git mv` commit above
  (`unified-trading-pm@4f270300b`) hit `/done`'s M3 check with `reason: cross_repo_pm_file_touched_no_checkbox_flip` — a
  diff at the ORIGINAL `plans/active/...` path shows only a deletion (git's rename pairing isn't applied under a
  path-scoped `git log`/`git show` query), so the `[ ] → [x]` transition wasn't visible there. This is the exact
  conflict `/plans/active/issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md`
  documents between `check_archive_candidates --only` (demands same-commit archival once a doc goes 0-open) and
  `plan-completion-and-archival-discipline.md`'s "never combine flip + `git mv`" rule — confirming that issue's open
  question: the M3 gap for this shape is STILL live (not resolved by the 2026-07-28 fix
  `ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26.md` describes). Applying that issue's
  documented one-commit `archive_exempt: true` bridge retroactively: moved the doc back to
  `plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md`, reverted `status` to `active` + dropped the
  ARCHIVED banner (both restored in the immediately-following commit), added `archive_exempt: true`. This commit's diff
  at the canonical path now shows the real todo checkbox flip; the archival re-lands as a separate follow-up commit
  right after.
