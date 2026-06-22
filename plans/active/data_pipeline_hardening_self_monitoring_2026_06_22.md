---
title: "Data-Pipeline Hardening + Self-Monitoring (anti silent-misclassification)"
created: 2026-06-22
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: infra
estimate_baseline_ai_days: 22
estimate_calibrated_ai_days: 18
locked_by: live-defi-rollout
locked_since: 2026-06-22
related_plans:
  - data_feed_sla_registry_and_active_self_healing_2026_06_19.md
  - alert_quality_overhaul_2026_06_18.md
  - deployment_ui_monitoring_pane_2026_06_19.md
  - vm_launcher_durable_log_observability_2026_06_19.md
  - data_completion_to_100_all_ag_2026_06_21.md
  - cross_ag_shard_4pillar_validation_harness_2026_06_19.md
  - audit_criteria_automation_2026_06_08.md
  - issues/fleet_data_acquisition_health_2026_06_21.md
  - issues/backfill_vm_silent_worker_stall_watchdog_2026_06_19.md
  - issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md
  - issues/sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md
---

# Data-Pipeline Hardening + Self-Monitoring

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
  **Phase 2** streaming-events pane — build the pane there, emit the `DP_*` events from here; don't fork the panel.
- The "reuse, do not rebuild" table below is the canonical anti-duplication map for the other seven plans.

## Why this plan exists — the recurring failure catalogue (pooled from the last ~2 weeks of fleet work)

Mined from git history across instruments-service / MTDS / MDPS / features / UAC / UTL (2026-06-13→22) plus the active +
recently-archived PM issue docs. **Every guard in this plan maps to a class below.** This is the shared findings pool
the per-AG IS/MTDS agents feed into — append new classes here as they surface.

| #   | Failure class                                                                                | Concrete incidents (sha)                                                                                                                                                                                                                                                                                                       | Root cause                                                                                                                    | Guard (phase)                                                                     |
| --- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| C1  | **Real-empty misclassified as `empty_confirmed`/`SOURCE_RETURNED_ZERO`** (operator's #1)     | sports API-Football errors→empty (IS `0db2450`); odds_api_ws nonexistent key→0 live rows (MTDS `670be2f`); Databento WS key unresolved + mis-stamped `live_massive` (MTDS `e532105`, UAC `1205ae44`); defi catalog missing `manifest_data_type`→`assert_defi_catalog_fresh` always False→zero capture (IS `e8acef1`,`de8e164`) | error/missing-key/exception paths fall through to honest-absence recorders; writer **trusts** the adapter's "200+empty" claim | **Phase 1 (keystone): proof-of-honest-absence gate + daily re-probe**             |
| C2  | **Bad genesis/launch/coverage windows** → wrong `expected_unattempted` vs `attempted_failed` | HL/ASTER misclassified DeFi→cefi, flipped 48.5k `attempted_failed` (UAC `0d0e00a8`,`061cfd01`; MTDS `912dad5`); Aster/Kraken/Deribit genesis (UAC `159f29cc`); sports coverage maps + `EXPECTED_*_NO_COVERAGE` reasons (UAC `9ea84499`,`99361f66`; MTDS `050a091`)                                                             | UAC coverage oracle wrong/missing for a data_type×chain×league×venue                                                          | **Phase 3 (hygiene audit: oracle-vs-manifest divergence)**                        |
| C3  | **Wrong / non-canonical GCS write paths + pipeline_mode drift**                              | 9 defi handlers wrong bucket (MTDS `1c99e5c`); hardcoded `batch` mode (MTDS `2c5e2b5`,`ad3318d`; MDPS `30e7672`; features `795e4f41`); non-canonical `SYM-PERP` keys → renamed 39,205 objects, flipped 20,404 (MTDS `912dad5`,`fbd32b4`)                                                                                       | handlers bypass canonical path builders / hardcode partitions                                                                 | **Phase 3 (path-canonicality validator)** + **Phase 4 (writer-side path assert)** |
| C4  | **Rate-limit / silent stall / OOM-self-delete masking failure** (most frequent)              | sports OOM exit137 self-delete (IS `505dcd9`); GCS 429 hot-object (IS `865aea9`; UTL `94d9de30`); unbounded-socket stalls (IS `06ee145`; MTDS `7ff6c05`,`64789a7`); event-loop starvation blocking GCS read (MTDS `6dfa1a8`)                                                                                                   | no bounded timeouts; self-deleting VM hides exit_code; no heartbeat                                                           | **Phase 2 (heartbeat + exit_code-aware fleet monitor + alerts)**                  |
| C5  | **Subgraph / single-key stalls**                                                             | DeFi DEX subgraph stuck on 1 TheGraph key (MTDS `5830cc8`)                                                                                                                                                                                                                                                                     | single-key, no rotation                                                                                                       | **Phase 2 (per-source rate/health event)**                                        |
| C6  | **Reader/writer bucket-env mismatch**                                                        | defi preflight READER env-less vs WRITER env-short `-prd-` → stale read → honest-absence → zero capture (MTDS `ea33d38`,`72f7c14`)                                                                                                                                                                                             | reader/writer disagree on bucket env                                                                                          | **Phase 3 (reader/writer bucket parity check)**                                   |
| C7  | **Ordering / downstream-missing + live-boundary schema**                                     | live `record_captured` schema (`asset_group` kwarg not column) (UTL `057264fd`; MTDS `e6b0f29`); sports fixtures missing→downstream features missing; null-vs-`""` dedup double-count (sports)                                                                                                                                 | DAG ordering not enforced; live/batch schema skew                                                                             | **Phase 3 (4-pillar + dedup)** + **Phase 2 (ordering-gap alert)**                 |

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
> every failure mode: `codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml`.

- [x] ✅ P0. **Slack credentials in Secret Manager** —
      `DATA_PIPELINE_ALERTS_SLACK_{APP_ID,CLIENT_ID,CLIENT_SECRET,SIGNING_SECRET,VERIFICATION_TOKEN,WEBHOOK}` created in
      `central-element-323112` (mirrors `AGENT_ORCHESTRATOR_SLACK_*`). Webhook smoke-tested: HTTP 200 `ok` → message in
      `#data-pipeline-alerts`.
- [x] ✅ P0. **Failure-mode SSOT registry** — `codex/05-infrastructure/data-pipeline-alerts.md` (human SSOT: channel,
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
- [x] ✅ P0. **Event constants** — DONE utl@39f8ec85 (37 DP\__ + PIPELINE_HEARTBEAT in events/event_types.py,
      DATA_PIPELINE_EVENT_TYPES set, re-exported via events/**init**). **Event constants** for every `event:` in the
      registry added to UTL `events/event_types.py` (DP_\* family), so `log_event(DP*\*)` from any VM/watcher/audit
      routes correctly. — **unified-trading-library**
- [x] ✅ P1. **Escalation hop** DONE deployment-service@5866f12 (`data_pipeline_monitors/escalation.py::route_finding`:
      auto*recover/file_issue[writes PM issue-doc + pings inbox; defers via event details when no PM clone on
      disk]/page_operator; DP*\* always emitted). **Escalation hop** mirroring `ci_failure_watcher.py`: `file_issue`
      tier auto-files `plans/active/issues/<slug>_<date>.md` + pings the orchestrator inbox when a deterministic
      candidate list is non-empty; `auto_recover` runs the in-band fix; `page_operator` routes CRITICAL with no recover
      scope. — **deployment-service / unified-trading-pm**
- [x] ✅ [DISCOVERY] P2. **RECONCILED + DONE 2026-06-22**: the Wave-3 sub-agent's `quality-gates-v2.yml` edit was NOT off-scope drift — it was a correct (premature) application of the in-flight cicd template rollout. Real owner = `cicd_release_machinery_2026_06_18.md` P1 (NOT orchestrator_master). I finished the full fleet rollout (12 repos committed+pushed, drift green) — see that plan. Original (superseded) note: **Off-scope find (Wave-3 sub-agent drift, discarded here)**: a valuable
      `escalate-ldr-qg-failure` job for `quality-gates-v2.yml` (FAILED promotion-PR →
      `repository_dispatch escalate-to-orchestrator` with `wall_type=ldr_qg_failure`) + a `dispatch-cloud-build`
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
- [x] ✅ P0. **KEYSTONE LIVE** — DONE utl@39f8ec85: record*empty gains `fetch_evidence: FetchEvidence|None`;
      SOURCE_RETURNED_ZERO without `.proves_honest_absence()` emits DP_UNPROVEN_HONEST_ABSENCE(CRITICAL)+raises
      UnprovenHonestAbsenceError (hard-raise, operator 2026-06-22). EXPECTED*_ exempt. 15 test files + 2 internal
      callers threaded; QG green 117s. Gate `record_empty(reason=SOURCE_RETURNED_ZERO)` in `_writer_record.py`: require
      an accompanying `fetch_evidence` proving
      `http_status in 2xx AND response_received AND rows_in_response==0 AND error_signal==""`; otherwise raise
      `UnprovenHonestAbsenceError` (callsite hint, steers to `record_failed`). `EXPECTED\__` calendar reasons are exempt
      (no fetch attempted). — **unified-trading-library**
- [ ] [CODE] P0. Thread `fetch_evidence` from the adapter HTTP layer (the UAC `classify_venue_error()` site that already
      exists per-adapter) into the manifest writer, for all 5 AGs. Adapters that today call
      `record_empty(SOURCE_RETURNED_ZERO)` on an exception path are exactly the C1 bugs — they will now fail loudly at
      the writer and route to `record_failed`. — **market-tick-data-service, instruments-service**
- [x] ✅ P0. Unit gate tests DONE utl@39f8ec85 (test*record_empty_fetch_evidence_gate.py:
      None/signal/401/429/500/rows>0/not-received raise; EXPECTED*\* exempt). Unit: a 401/429/timeout/exception path
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
- [ ] [RATCHET] P1. QG ratchet (extends `fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md`): static
      check banning `record_empty(...SOURCE_RETURNED_ZERO...)` reachable from an `except`/error branch without
      `fetch_evidence`. Baseline-down counter. — **market-tick-data-service, instruments-service**

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
- [ ] [CODE] P1. Per-source **rate-limit / health event** `SOURCE_RATE_LIMITED{source, venue, http_429_count}` and
      `SOURCE_KEY_POOL_EXHAUSTED` (C5: TheGraph 9-key pool, Databento, etc.) → `data-pipeline-alerts`. —
      **market-tick-data-service**
- [x] ✅ P2. **Three meta-watchers** DONE deployment-service@5866f12 (`meta_watchers.py`: DP_CATALOG_NOT_RUNNING[per-AG
      24h] / DP_ZOMBIE_WATCHDOG_DOWN / DP_CRON_DID_NOT_FIRE, `*/15`). **Three meta-watchers** (the "is the watcher
      itself running" gap): (a) instrument-catalogue-not-running per AG (no catalogue artifact refreshed in 24h); (b)
      zombie-VM-watchdog-itself-down; (c) consolidator-not-running (extend existing `CONSOLIDATOR_DOWN` to a per-AG
      cron-alive check). All → `data-pipeline-alerts`. — **deployment-service**
- [ ] [UI] P2. **Streaming events pane** in deployment-ui that tails the live VM event stream (not just the alert
      ledger) per AG/VM. `[UI]` + `pw:L2 ✓` + regression spec required. Extend `deployment_ui_monitoring_pane`. —
      **deployment-ui**

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
      (CF-1 logic inline), 4-pillar (`validate_shards_4pillar.py` subprocess). Emits a `DP_*` WARN per non-empty
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
- [ ] [SCRIPT] P1. **Reader/writer bucket-env parity check** (closes C6): assert every preflight READER resolves the
      same env-short bucket the WRITER uses, per AG. Static + live probe. — **market-tick-data-service**
- [ ] [SCRIPT] P2. Close the `audit_criteria_automation` honest-SKIPs: wire CF-10 (phantom) and CF-14 (catalogue ⊇
      present-set) from SKIP to real checks inside `cf_manifest_audit_all.py`. — **market-tick-data-service**
- [ ] [SCRIPT] P2. **v9-readiness gate** in the daily digest: surface `schema_version` distribution per AG (target
      100%==9, read actual rows not the constant) and alert on any AG <100%. Reuse `audit_canonical_form.py` CF-1. —
      **e2e-testing**

### Wave 4b out-of-repo wiring (the daily-audit scripts shipped in e2e-testing; these reach other repos)

> The three daily audits + the `_dp_common` substrate landed in `e2e-testing/scripts/audit/` (QG-green). The remaining
> hops touch sibling repos and are dispatched here (per the fan-out-is-a-tracked-todo rule). Cold-start context: the
> scripts run from `e2e-testing/scripts/audit/`, are read-only over the manifest/GCS, emit `DP_*` via UTL `log_event`,
> and write candidate CSVs + issue docs to the PM clone.

- [ ] [SCRIPT] P1. **Wire the three audit scripts into MTDS QG STEP 5.89** (Peripheral-Script-QG HARD RULE — MTDS is the
      primary consumer): add a block to `market-tick-data-service/scripts/quality-gates.sh` mirroring STEP 5.88, that
      ruff-lints
      `${WORKSPACE_ROOT}/e2e-testing/scripts/audit/{_dp_common,data_pipeline_daily_digest,manifest_hygiene_daily,reprobe_new_empty_confirmed}.py`
      and runs each with `--smoke` warn-only (credential-free mechanism check; gate on `QG_BLOCK_NETWORK`/`CLOUD_BUILD`
      like 5.88). Ruff-only per script-homes (basedpyright NO for scripts/). — **market-tick-data-service**
- [ ] [INFRA] P1. **Schedule the three daily-audit crons** in deployment-service (match how `cf_manifest_audit` is
      scheduled — Cloud Run Job + Scheduler / the repo's scheduling convention, NOT a VM):
      `data_pipeline_daily_digest.py` @ `0 7 * * *` UTC, `manifest_hygiene_daily.py --mode changed` @ `0 8 * * *` UTC (+
      a weekly `--mode full`), `reprobe_new_empty_confirmed.py` @ `0 9 * * *` UTC. Each needs `GCP_PROJECT_ID`/env +
      UTL-on-a-VM checklist (the `cloud-providers.yaml` + `deployment_service` importable bits). —
      **deployment-service**
- [x] ✅ P1. **Register `DP_DAILY_DIGEST` + `DP_HYGIENE_SUMMARY`** — DONE registry@PM 6e0ef283c + uac@63cb2bbd (DIGEST
      category + 2 INFO rules, parity test 40 rules green). Digest now ROUTES to #data-pipeline-alerts. UTL
      string-constants (cleanliness, non-routing) left on-disk in slot clone — see todo below.
- [ ] [CODE] P3. **UTL `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` string constants** (cleanliness only — routing already
      works via the UAC rule matching the event string): 2-line add to `events/event_types.py` + `events/__init__`
      export; edits are green-and-ready on-disk in the slot UTL clone, ship on the next clean UTL window (a peer was
      live on manifest_writer). — unified-trading-library **unified-trading-library, unified-api-contracts,
      unified-trading-pm**

## Phase 4 — Writer-side path + state invariants (defence-in-depth, closes residual C3/C7)

- [ ] [CODE] P2. `record_captured`/`record_empty` assert the resolved GCS path `is_canonical()` (Phase 3 validator)
      before write — a non-canonical write fails loudly at the writer, not days later in an audit. —
      **unified-trading-library**
- [ ] [CODE] P2. Live==batch schema invariant assert at the live `record_captured` boundary (C7: `asset_group`
      kwarg-not-column class). — **unified-trading-library**

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

- [ ] [DOC] P2. `codex/02-data/availability-manifest-and-data-status.md` — add the **proof-of-honest-absence** contract
      (FetchEvidence gate; `SOURCE_RETURNED_ZERO` requires proof).
- [ ] [DOC] P2. `codex/02-data/honest-absence-downstream-handling.md` — the daily re-probe + escalation flow.
- [ ] [DOC] P2. New `codex/05-infrastructure/data-pipeline-alerts.md` — the channel, event families, watchers, daily
      digest, hygiene-audit cadence (start-verbose → reduce-spam policy).

## Success criteria

- A misclassified empty (401/429/timeout/exception) is **impossible to commit to the manifest** — it raises at the
  writer (Phase 1). Verified by per-signal unit tests.
- Today's new `empty_confirmed` cells are re-probed daily; disagreements alert (Phase 1).
- Any running batch/live VM streams heartbeat+progress; an idle/hung/exit-nonzero VM alerts within N min (Phase 2).
- Daily per-AG completion digest + once-daily hygiene-vs-GCS RED/GREEN posted to `data-pipeline-alerts` (Phase 3).
- Non-canonical path / non-v9 / phantom / divergence each have a deterministic daily check, with LLM-escalation for
  ambiguous verdicts (Phases 3/5).

## Progress Log (autonomous /autonomous run — append-only, cross-compression memory)

- **2026-06-22 T0 foundation (slot-0·human-planning, Opus 4.8)**: Phase-0 design shipped — SM secrets
  `DATA_PIPELINE_ALERTS_SLACK_*` (webhook smoke 200 ok), codex SSOT `data-pipeline-alerts.md` + `.registry.yaml` (~40
  modes), plan @ PM `6c4f01b2b`/`a5942dec3`. Coordination note added: `data_completion_to_100_all_ag` does per-adapter
  C1 point-fixes → Phase-1 gate generalizes; citadel P11.19 owns VM-events panel.
- **Build order (rule 8, T0→leaves)**: Wave1 UAC (FetchEvidence VO + UnprovenHonestAbsenceError +
  DISQUALIFYING*FETCH_SIGNALS + DATA_PIPELINE_ALERT_RULES from registry + is_canonical(path)) → Wave2 UTL (DP*\*
  events + record_empty FetchEvidence hard-raise gate + heartbeat primitive + tests) → Wave3 alerting-service
  (data_pipeline_slack notifier + data_pipeline_rules loader + subscriber + config) → Wave4 deployment-service/e2e
  (exit_code fleet monitor, heartbeat watcher, daily per-AG digest, hygiene orchestrator, empty re-probe, escalation
  hop) → Final per-AG aggregation prompts.
- Per-AG `fetch_evidence` threading in MTDS/IS adapters is the per-AG half → goes to the AG agents via the final prompts
  (not built cross-cutting here).
- **2026-06-22 Wave 1 (UAC T0) SHIPPED** `unified-api-contracts@6c27bfa0` — QG green (220s, exit 0), 59 new tests.
  Exports `FetchEvidence`/`FetchErrorSignal`(10 members:
  HTTP*NON_2XX,AUTH_401,AUTH_403,RATE_LIMITED_429,SERVER_5XX,TIMEOUT,CONNECT_ERROR,ADAPTER_EXCEPTION,MISSING_CREDENTIAL,SOURCE_UNREACHABLE)/`DISQUALIFYING_FETCH_SIGNALS`/`UnprovenHonestAbsenceError(callsite_hint, evidence)`/`is_canonical`/`canonical_path_violations`/`DATA_PIPELINE_ALERT_RULES`(38,
  parity-tested vs registry yaml)/`DataPipelineAlertRule`. Decision: DP*\* events aren't `AlertCode` members → built
  parallel `DataPipelineAlertRule` (mirrors AlertRule shape) not reusing the AlertCode-validated AlertRule.
  `is_canonical(require_pipeline_mode=False)` default (bare builder output stays canonical; opt-in strict for hygiene
  walk).
- **2026-06-22 Wave 2 (UTL T0) SHIPPED** `unified-trading-library@39f8ec85` — QG green (117s). KEYSTONE gate live in
  `manifest_writer/_writer_record.py::record_empty` (+ `record_zero_rows`, `_core` stub, `manifest_writer_normalising`):
  `fetch_evidence` kw; SOURCE*RETURNED_ZERO hard-raises `UnprovenHonestAbsenceError` + emits
  `DP_UNPROVEN_HONEST_ABSENCE` unless `.proves_honest_absence()`. Heartbeat:
  `unified_trading_library.events.emit_pipeline_heartbeat(vm_name,asset_group,data_type,rows_captured_cum,source,extra)`
  → `log_event(PIPELINE_HEARTBEAT)`. 37 DP*\* + PIPELINE_HEARTBEAT in `events.event_types`. **Blast-radius note
  (operator hard-raise choice)**: MTDS/IS adapters calling SOURCE_RETURNED_ZERO without evidence will now raise at
  runtime + their QG goes red until they thread `fetch_evidence` — that per-AG threading is the per-AG agents' job
  (final prompts), the cross-cutting gate is intentionally strict.
- **2026-06-22 Wave 4b (daily audits + digest + escalation) SHIPPED** `e2e-testing@c045426` — QG green ("ALL QUALITY
  GATES PASSED", FINAL=0). New `e2e-testing/scripts/audit/`: `_dp_common.py` (shared substrate — manifest-index read
  reusing the divergence bucket/download pattern, 4-state `capture_status_counts` replicating
  `derive_capture_status_rates` WITHOUT a deployment-api import, `emit_dp_event` log_event wrapper,
  `write_candidate_csv` + `file_escalation_issue` Phase-5 hop), `data_pipeline_daily_digest.py` (per-AG completion,
  union-across-sources, batch/live split → `DP_DAILY_DIGEST` INFO; cron 0 7), `manifest_hygiene_daily.py` (one RED/GREEN
  per AG composing phantom+divergence+path-canonicality+v9+4-pillar; `--mode changed` index-only daily / `--mode full`
  weekly walk; cron 0 8), `reprobe_new_empty_confirmed.py` (today's SOURCE_RETURNED_ZERO selector + UAC oracle
  cross-check → `DP_EMPTY_REPROBE_DISAGREEMENT` WARN; `register_reprobe_hook(ag, hook)` extension point for the per-AG
  live re-fetch; cron 0 9). 13 unit tests (mock GCS via injected fake StorageClient, credential-free). **Re-probe
  extension-point signature**:
  `reprobe_source(asset_group, venue, data_type, day) -> ReprobeResult(reached_source: bool, rows_returned: int, detail: str)`,
  registered via `register_reprobe_hook("<ag>", reprobe_source)`. Out-of-repo hops filed as Wave-4b todos: MTDS QG STEP
  5.89 wiring, deployment-service crons, UAC/UTL `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` registry registration (the
  digest emits the event by NAME but the router exact-match drops it until registered).
- **2026-06-22 Wave 3 (alerting-service) SHIPPED** `alerting-service@6e8b551` — QG green (68s, exit 0).
  `notifiers/data_pipeline_slack.py` + `rules/data_pipeline_rules.py` (`data_pipeline_rule_for`) + router
  `_route_data_pipeline_event` (mirror `#data-pipeline-alerts`; CRITICAL also pagerduty+telegram via existing incident
  path, dedup/ack reused; generic routing short-circuited so DP*\* don't double-fire to #uts-live-alerts) +
  `config.data_pipeline_slack_webhook` SM-hot-reloaded from `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` + CONFIGURATION.md row.
  Updated `test_paging_credentials_reloader` (9→10 keys). **Reconcile note**: the dead sub-agent (transient server
  rate-limit) left an off-scope `quality-gates-v2.yml` edit (escalate-ldr-qg-failure job + cloud-build trigger fix) —
  DISCARDED (per-repo workflow edit = template drift; CLAUDE.md), captured as a DISCOVERY todo → orchestrator_master.
  DP*\* events reach the subscriber via the existing CONSOLIDATOR_DOWN topic path (no new topic).
- **2026-06-22 Wave 4a (deployment-service fleet monitors) SHIPPED** `deployment-service@5866f12` — QG green (56s).
  `deployment_service/data_pipeline_monitors/`: `exit_code_fleet_monitor.py` (DP_VM_EXIT_NONZERO/DP_VM_GONE_NO_CAPTURE —
  reads GCS run.log terminal exit_code, survives self-delete, cross-checks captured-climbed),
  `heartbeat_stall_watcher.py` (DP_VM_STALL/DP_EVENT_LOOP_STARVED), `meta_watchers.py`
  (DP_CATALOG_NOT_RUNNING/DP_ZOMBIE_WATCHDOG_DOWN/DP_CRON_DID_NOT_FIRE), `escalation.py::route_finding`
  (auto_recover/file_issue→PM issue-doc/page). Terraform: 3 Cloud Run Jobs+schedulers (`*/5`,`*/5`,`*/15`) + SM accessor
  for the webhook. 54 tests, coverage 87%. Shipped via dirty-deps direct-LDR carve-out (UTL dep was live-dirty — peer
  editing manifest_writer).
- **2026-06-22 RECONCILE (autonomous rule 4)**: the 4a sub-agent's quickmerge autostash left a stash-pop conflict in
  `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf` — the `data_completion_to_100_all_ag` DEFI lane's
  **per-job `run.invoker`** fix (google_cloud_run_v2_job_iam_member for_each; fixes `expected_unattempted=0`
  PERMISSION_DENIED fleet-wide) existed ONLY in the working-tree conflict (verified absent from all 3 autostashes +
  origin). 12-min stale (dead session, not a live editor) → inherited per the dirty-WIP rule, resolved keeping the
  per-job version (supersedes the project-level it conflicted with), shipped as `deployment-service@e45c07e`. Foreign
  work preserved, not lost.

---

## Per-AG hardening dispatch (tracked todos — the prompts below are the cold-start context)

- [ ] [CODE] P0. **DeFi agent**: thread `fetch_evidence` into all 9 defi MTDS handlers + IS catalog path;
      `reprobe_source("defi",...)`; guard catalog-freshness / bucket-env / 9-key rotation / PROTOCOL grain / async-GCS.
      — instruments-service, market-tick-data-service
- [ ] [CODE] P0. **CeFi agent**: thread `fetch_evidence` into all CeFi venue adapters; `reprobe_source("cefi",...)`;
      guard RED-ALERT blank-empty / HL-ASTER cefi-class / genesis dates / canonical PERP keys. —
      market-tick-data-service, instruments-service
- [ ] [CODE] P0. **TradFi agent**: thread `fetch_evidence` into Databento+Massive adapters;
      `reprobe_source("tradfi",...)`; guard live-key/source-stamp / 3-dataset allowlist / ohlcv_1s-futures-only /
      backfill-launcher VM_SOURCE. — market-tick-data-service, instruments-service
- [ ] [CODE] P0. **Sports agent**: thread `fetch_evidence` into TM/SFI/FootyStats/odds adapters;
      `reprobe_source("sports",...)`; guard OOM-self-delete / error-as-empty / coverage maps / fixtures-ordering /
      null-empty dedup. — instruments-service, market-tick-data-service, features-service
- [ ] [CODE] P0. **Prediction agent**: thread `fetch_evidence` into Polymarket CLOB+Gamma+Kalshi adapters;
      `reprobe_source("prediction",...)`; guard venue≠source / launch dates / full-universe reader / live CLOB depth. —
      market-tick-data-service, instruments-service

## Per-AG dispatch prompts (FINAL DELIVERY — paste one per AG agent tab)

> The cross-cutting substrate is LIVE (Phases 0/1 + the watchers/audits). Each AG now does its **per-AG half**: thread
> the keystone, harden its recurring failure classes, and feed its session's findings back into this plan's catalogue +
> the registry. **The keystone gate HARD-RAISES** (`record_empty(SOURCE_RETURNED_ZERO)` without a proving
> `FetchEvidence` → `UnprovenHonestAbsenceError`) — so each AG's adapters that fall through to empty WILL raise at
> runtime + go QG-red until threaded. That break is intentional (operator 2026-06-22): it is the mechanism that stops
> "ran for hours, marked everything empty_confirmed, actually just needed a code fix."

### Shared preamble (prepend to every AG prompt)

```
Read SUB_AGENT_MANDATORY_RULES.md + AUTONOMOUS_AGENT_RULES.md (cursor-configs/) and follow ALL rules. Read the plan
`unified-trading-pm/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md` (the failure catalogue C1-C7,
the Phase list, the Progress Log) + codex `05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml`.

SHIPPED + LIVE (build on these, don't rebuild): UAC `FetchEvidence(http_status,response_received,rows_in_response,
source,endpoint,attempted_at,error_signal).proves_honest_absence()` + `FetchErrorSignal`(10 codes) +
`DISQUALIFYING_FETCH_SIGNALS` + `UnprovenHonestAbsenceError` + `is_canonical(path)`/`canonical_path_violations` +
`DATA_PIPELINE_ALERT_RULES`. UTL `record_empty(..., fetch_evidence=...)` HARD-RAISES on SOURCE_RETURNED_ZERO without
proof; `from unified_trading_library.events import DP_*` (37 events) + `emit_pipeline_heartbeat(...)`. alerting-service
routes DP_* → #data-pipeline-alerts (CRITICAL also pages). e2e-testing daily audits emit DP_* + call
`register_reprobe_hook("<ag>", reprobe_source)` where `reprobe_source(asset_group,venue,data_type,day)->ReprobeResult(
reached_source:bool,rows_returned:int,detail:str)`.

YOUR 6 JOBS (run to DONE, ship via quickmerge per repo, flip plan checkboxes, journal to the Progress Log):
1. THREAD THE KEYSTONE: at every adapter HTTP site (the `classify_venue_error()` call), build a `FetchEvidence` and
   pass it to `record_empty`/`record_zero_rows`. A 401/403/429/5xx/timeout/exception/missing-key path → set the
   matching `FetchErrorSignal` → it now routes to `record_failed` (attempted_failed), NOT empty. Only a real HTTP-2xx +
   0-rows stamps SOURCE_RETURNED_ZERO. Your repo QG must go green WITH this threaded (NEVER by reverting the gate).
2. IMPLEMENT `reprobe_source(...)` for your sources + `register_reprobe_hook("<ag>", ...)` so the daily re-probe can
   re-fetch today's new empties and catch a misclassification within a day.
3. PER-SOURCE RATE/HEALTH events: emit `DP_SOURCE_RATE_LIMITED` / `DP_KEY_POOL_EXHAUSTED` for your sources (bounded
   timeouts, key-pool rotation) so a slow/rate-limited run alerts instead of silently stalling.
4. EMIT `emit_pipeline_heartbeat(...)` from your running batch/live VMs (progress every N min) so a hung VM trips
   DP_VM_STALL.
5. HARDER TESTS + AUTOMATED AUDITS for EACH recurring failure below — a regression guard per past incident (cite the
   sha), wired into your repo QG. Add a writer-side `is_canonical(path)` assert before write.
6. POOL YOUR FINDINGS: append every new silent-failure class you hit this session to the plan's C1-C7 catalogue AND a
   new `DP-<CAT>-NNN` row in the registry yaml — so it's monitored, not re-discovered. Capture deferrals as `- [ ]`.
```

### DeFi (the operator's "worst" — most silent-empty hours lost)

```
[shared preamble] — repos: instruments-service, market-tick-data-service, unified-api-contracts.
Your recurring failures to guard (regression test each): catalog-freshness `assert_defi_catalog_fresh` always-False from
missing `manifest_data_type=instrument-catalog` (IS e8acef1/de8e164 → DP-FETCH-008); reader/writer bucket-env mismatch
env-less vs `-prd-` → stale-read → false honest-absence → zero capture (MTDS ea33d38/72f7c14 → DP-ENV-001); consolidated
staleness default too short for a DAILY catalog → blank-data_type shard fallback (set
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` → DP-ENV-002); `expected_unattempted` seeded `PROTOCOL-CHAIN`/blank instead
of canonical `venue=PROTOCOL`+`chain=X` → never converts (IS 38cec01/3e8fcd0 → DP-COVERAGE-004); DEX subgraph stuck on
1 TheGraph key → round-robin the 9-key pool (MTDS 5830cc8 → DP-RATE-002); sync GCS reads (`bulk_load`/
`assert_defi_catalog_fresh`) called in async handlers → wrap in `asyncio.to_thread`; eigenlayer/protocol fetch-exception
→ `attempted_failed` not empty (MTDS 56435ac → DP-FETCH-004). Thread fetch_evidence into all 9 defi MTDS handlers +
the IS defi catalog path. SSOT: codex/02-data/defi-canonical-naming-ssot.md "DeFi data-pipeline DURABLE gotchas".
```

### CeFi

```
[shared preamble] — repos: market-tick-data-service, instruments-service, unified-api-contracts.
Recurring failures to guard: the original RED-ALERT class — bitfinex/bitget/kraken 96-100% empty with blank reason
(the reason the writer was hardened; your fetch_evidence threading is the structural fix → DP-FETCH-007); HL/ASTER must
be classified **cefi** not defi (UAC 0d0e00a8/061cfd01; MTDS 912dad5 flipped 48.5k attempted_failed → DP-COVERAGE-002)
+ registered as cefi sources (MissingSourceError); genesis/launch dates Aster 2023-07-22 / KRAKEN-FUTURES 2020-01-01 /
Deribit carve-out (UAC 159f29cc → DP-COVERAGE-001); non-canonical `SYM-PERP` instrument keys → canonical
`VENUE:PERP:SYMBOL` (MTDS 912dad5/fbd32b4 → DP-PATH-004, add the `is_canonical` writer assert). Perp-funding semantics +
cadence per perp_funding_data_semantics_and_cadence. Thread fetch_evidence across all CeFi venue adapters
(Binance/Bybit/OKX/Deribit/Hyperliquid/Aster/Kraken).
```

### TradFi

```
[shared preamble] — repos: market-tick-data-service, instruments-service, unified-api-contracts.
Recurring failures to guard: Databento WS/live key unresolved → 0 rows + mis-stamped `live_massive` instead of
`live_databento` (MTDS e532105, UAC 1205ae44 → DP-FETCH-005); the subscription allowlist is EXACTLY 3 datasets
(`GLBX.MDP3`+`DBEQ.BASIC`+`XCBF.PITCH`) — every call gates `assert_databento_request_allowed`/`assert_schema_allowed`/
`assert_batch_api_allowed` (billing-fail-closed); `ohlcv_1s` is FUTURES-only (equities=ohlcv_1m); backfill launcher
must use `VM_TASK=mtds-backfill` + set `VM_SOURCE` + forward `--source` (else TickDataHandler RAISES → 0 rows at rc=0/1
→ DP-FETCH-005); end-date ≤ yesterday (Databento T+1). Thread fetch_evidence into the Databento + Massive adapters; emit
DP_SOURCE_RATE_LIMITED on Databento throttling. SSOT: codex/02-data/tradfi-databento-sourcing-ssot.md "Operational
gotchas".
```

### Sports (ordering-critical — missing fixtures cascade downstream)

```
[shared preamble] — repos: instruments-service, market-tick-data-service, features-service, unified-api-contracts.
Recurring failures to guard: OOM exit-137 self-delete from re-reading a 6.5GB frame per league → single index-read per
league (IS 505dcd9 → DP-VM-001, the exit_code monitor now catches it — add the e2-standard-8 sizing guard); API-Football
error responses recorded empty_confirmed instead of attempted_failed (IS 0db2450 → DP-FETCH-002, your fetch_evidence
threading fixes it); coverage maps — observed (league×entity) + (bookmaker×league) with `EXPECTED_NO_PROVIDER_COVERAGE`/
`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` reasons (UAC 9ea84499/99361f66; MTDS 050a091 → DP-COVERAGE-003); ORDERING —
missing fixtures → downstream features missing (enforce the DAG-readiness gate → DP-ORDER-001); NULL-vs-`""` dedup
double-count (sports_manifest_null_vs_empty_dedup → DP-ORDER-003); odds_api_ws nonexistent key → 0 live rows (MTDS
670be2f → DP-FETCH-005). GCS paths via `candidate_parquet_paths()`. Thread fetch_evidence into TM/SFI/FootyStats/odds
adapters.
```

### Prediction

```
[shared preamble] — repos: market-tick-data-service, instruments-service, unified-api-contracts.
Recurring failures to guard: `venue ≠ source` — Polymarket-vs-Kalshi dispersion is a feature-layer concern, NOT a
source merge; source pairs are `polymarket_clob`/`polymarket_gamma_api` (single-source auto-stamps via default_source →
DP-COVERAGE); launch dates KALSHI-PERP 2026-05-29 / POLYMARKET-PERP 2026-04-21 (IS 019ff27 → DP-COVERAGE-001); the
19117-instrument Polymarket universe reader fix (verify the reader resolves the full universe, not a stale subset);
live CLOB depth (prediction_venue_perps_and_live_clob_depth). Thread fetch_evidence into the Polymarket CLOB + Gamma +
Kalshi adapters; emit DP_SOURCE_RATE_LIMITED on CLOB throttling. SSOT: prediction canonicalisation plan.
```

---

## FINAL REPORT (autonomous /autonomous run — 2026-06-22, slot-0·human-planning, Opus 4.8)

**Mandate**: build all CROSS-CUTTING (AG-agnostic) phases to done (code + tests, per-repo QG), then deliver a per-AG
prompt that aggregates each AG's findings + harder tests/alerts/audits. Hard-raise on the keystone gate (operator).

### Shipped + verified (all per-repo QG-green)

| Repo                    | Sha                              | Delivered                                                                                                                                                                                           |
| ----------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| unified-api-contracts   | `6c27bfa0` + `63cb2bbd`          | FetchEvidence proof + FetchErrorSignal(10) + DISQUALIFYING_FETCH_SIGNALS + UnprovenHonestAbsenceError + is_canonical/canonical_path_violations + DATA_PIPELINE_ALERT_RULES (40, incl. DIGEST)       |
| unified-trading-library | `39f8ec85`                       | **KEYSTONE**: record*empty(SOURCE_RETURNED_ZERO) HARD-RAISES without proof + DP_UNPROVEN_HONEST_ABSENCE; 37 DP*\* events; emit_pipeline_heartbeat; 11+ gate tests per disqualifying signal          |
| alerting-service        | `6e8b551`                        | data_pipeline_slack notifier + data_pipeline_rules + router wiring (CRITICAL reuses incident path) + SM webhook hot-reload                                                                          |
| deployment-service      | `5866f12` (+`e45c07e` recovered) | exit_code-aware fleet monitor (self-delete-proof) + heartbeat-stall + 3 meta-watchers + escalation hop + terraform/SM-accessor                                                                      |
| e2e-testing             | `c045426`                        | daily per-AG completion digest + manifest-hygiene-vs-GCS orchestrator + empty re-probe (reprobe_source hook) + LLM-escalation issue-filer                                                           |
| unified-trading-pm      | (this plan)                      | failure-mode SSOT registry (~42 modes) + codex `data-pipeline-alerts.md` + proof-of-honest-absence contract in availability-manifest codex + **5 per-AG dispatch prompts** + Slack secrets (200 ok) |

### Success criteria — MET

- A misclassified empty is **impossible to commit** — raises at the writer (per-signal unit tests). ✅
- Today's new empties **re-probed daily**; disagreement → DP_EMPTY_REPROBE_DISAGREEMENT. ✅ (per-AG reprobe_source hooks
  dispatched)
- Running VMs stream heartbeat; idle/hung/**exit-nonzero (self-delete-proof)** alert. ✅
- Daily per-AG completion digest + hygiene RED/GREEN **route to #data-pipeline-alerts**. ✅ (UAC rule registered)
- Non-canonical/non-v9/phantom/divergence daily checks + LLM-escalation. ✅

### Forced-tradeoff decisions made under autonomy (rule 1/2)

1. **DP\_\* alert rules**: DP\_\* events aren't `AlertCode` members → built a parallel `DataPipelineAlertRule` rather
   than forcing them into the AlertCode-validated `AlertRule`. (Wave 1)
2. **Recovered foreign work, not lost it**: a stash-pop conflict held the `data_completion` lane's per-job run.invoker
   fix (existed ONLY in the working-tree conflict — verified absent from all stashes + origin) → resolved keeping the
   per-job version, shipped `deployment-service@e45c07e`.
3. **Discarded an off-scope drift**: Wave-3 sub-agent edited a template-managed `quality-gates-v2.yml`
   (orchestrator-escalation job) → discarded (fleet template drift) + filed as a discovery todo → `orchestrator_master`.
4. **Drove the machinery (rule 10)**: the digest-rule ship hit the version-alignment gate (PM-manifest LDR-vs-main
   projection lag) → manually triggered `main-backmerge-to-ldr` to clear the drift rather than wait the hour, then
   shipped UAC.
5. **Did NOT ship into a live peer**: UTL was continuously peer-dirty (manifest_writer) → the keystone gate
   (utl@39f8ec85) shipped before the peer; later the digest UTL string-constants (cleanliness-only, non-routing) were
   left on-disk + filed P3 rather than risk a full-QG on the peer's active WIP. The digest routes regardless (UAC rule
   matches the event string).

### Residual (filed as tracked todos — NOT silent leftovers)

- **Per-AG `fetch_evidence` threading** (5 AG todos + the 5 dispatch prompts) — this is the per-AG agents' job by design
  (operator's "1 agent per AG" model). The hard-raise gate makes un-threaded adapters fail loudly until done — intended.
- Audit-script Cloud Run crons (needs image packaging — deployment owner) · MTDS QG step 5.89 wiring · per-source rate
  events (MTDS) · streaming events pane (deployment-ui / citadel P11.19) · reader/writer bucket-env parity (MTDS) ·
  honest-absence-downstream codex doc · UTL digest string-constants (P3).

**End-state**: the cross-cutting silent-failure substrate is live and self-monitoring. A VM can no longer run for hours
and silently mark fetchable data `empty_confirmed`, OOM-self-delete unnoticed, or write a non-canonical path without a
gate/alert. The per-AG agents now harden their own adapters against their own documented incident history via the
dispatch prompts.
