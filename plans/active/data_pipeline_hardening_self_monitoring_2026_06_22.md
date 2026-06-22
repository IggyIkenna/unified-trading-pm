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
- [x] ✅ P0. **KEYSTONE LIVE** — DONE utl@39f8ec85: record*empty gains `fetch_evidence: FetchEvidence|None`;
      SOURCE_RETURNED_ZERO without `.proves_honest_absence()` emits DP_UNPROVEN_HONEST_ABSENCE(CRITICAL)+raises
      UnprovenHonestAbsenceError (hard-raise, operator 2026-06-22). EXPECTED*\_ exempt. 15 test files + 2 internal
      callers threaded; QG green 117s. Gate `record_empty(reason=SOURCE_RETURNED_ZERO)` in `_writer_record.py`: require
      an accompanying `fetch_evidence` proving
      `http_status in 2xx AND response_received AND rows_in_response==0 AND error_signal==""`; otherwise raise
      `UnprovenHonestAbsenceError` (callsite hint, steers to `record_failed`). `EXPECTED\__` calendar reasons are exempt
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
- [x] ✅ **Reader/writer bucket-env parity check** (closes C6) — DONE `market-tick-data-service@0eee1ab` (QG STEP 5.91,
      `scripts/quality_gates/check_reader_writer_bucket_parity.py`, warn-only ratchet). LANDED once the dep window
      opened (UAC/UTL clean). **It FOUND 8 GENUINE C6 reader bugs** (env-less `build_bucket`/`get_bucket_name` reads vs
      env-short `-prd-` writers → stale-read → false honest-absence → zero-capture; the defi-6% class) — filed as the P1
      todo below; the defi lane already fixed one (`mtds@059df5f`, live IS-universe reader). —
      **market-tick-data-service**
- [~] [CODE] P1. **Fix the 8 C6 reader-bucket-env bugs** the parity check found — **7 of 8 SHIPPED on origin/LDR**
  (`market-tick-data-service@fbac3a9`, swept in via the peer's keystone-threading quickmerge): all sites aligned to
  `resolve_bucket_name(cloud=..., kind="instruments-store", asset_group=...)` (env-short `-prd-`, the IS writers'
  bucket). DONE: `engine/orchestrator/__init__.py:445/447/449/451` (`_register_all_catalog_readers` — 4 AG catalog
  readers, F4 expected-universe path; `get_bucket_name("instruments",ag)` was env-LESS Group-A
  `instruments-store-{ag}-{pid}` → confirmed genuine bug, fixed) + `cli/handlers/_instruments_metadata.py:218/442/518`
  (3 defi reads — the EXACT CLAUDE.md-documented defi-6% bug). Test `test_instruments_metadata_loader.py` updated to
  assert the env-short bucket (the prior 2 assertions encoded the bug — diagnosed test-wrong-not-code-wrong). Live-probe
  verified: `resolve_bucket_name(kind="instruments-store", asset_group="defi")` → `instruments-store-defi-prd-{pid}` (vs
  the OLD env-less `instruments-store-defi-{pid}`). **8th site — `live/websocket_runner.py` `_read_is_parquet_sync`
  (`build_bucket("instruments",…)`) — DEFERRED to the live MTDS-threading lane** (`data_completion_to_100_all_ag`): the
  file carries a large in-flight `fetch_evidence`-threading refactor the peer is actively committing (fbac3a9/26202e1);
  a clean local QG sentinel is also blocked by an environmental semver version-alignment lag (PM clone 11 behind
  origin/main; `--skip-version-alignment` is human-only). Fix is fully prepared + validated (helper
  `_instruments_store_bucket(ag)` mirroring the prediction reader; ruff/basedpyright-baseline/31-tests green; method
  ≤50L) — the threading lane lands it on its next clean window. Parity check is **warn-only** so the 1 remaining site
  does NOT redden the fleet; flip to hard-block when the 8th lands. Provenance: bucket-parity check
  `wip-preserve@32e8b6e`. — **market-tick-data-service**
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
- [ ] [INFRA] P2. **Apply the data-pipeline-audit terraform** (the crons run only once deployed): after the var-change
      lands, targeted `terraform apply -target=...` the 4 `dp-audit` Cloud Run Jobs + 4 schedulers (NOT a blanket apply
      of `terraform/gcp/` — drift risk). The `cf_manifest_audit` apply convention is the model. Until applied, the crons
      exist in code + the image is ready, but the schedulers are not yet provisioned. — **deployment-service**
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

- [x] ✅ [DOC] P2. `codex/02-data/availability-manifest-and-data-status.md` — DONE `unified-trading-pm@894610bc2` (new
      §6a "Proof-of-honest-absence contract": FetchEvidence 4-condition `proves_honest_absence()` gate +
      `UnprovenHonestAbsenceError` hard-raise + 10-member `FetchErrorSignal` disqualifying set + `EXPECTED_*`
      exemption + STEP 5.99 twin ref).
- [x] ✅ [DOC] P2. `codex/02-data/honest-absence-downstream-handling.md` — DONE `unified-trading-pm@894610bc2` (new
      "Daily re-probe + escalation flow": selector → UAC oracle cross-check → `DP_EMPTY_REPROBE_DISAGREEMENT` WARN →
      Phase-5 issue-file; `register_reprobe_hook` extension point).
- [x] ✅ [DOC] P2. `codex/05-infrastructure/data-pipeline-alerts.md` — VERIFIED complete `unified-trading-pm@894610bc2`
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
- **2026-06-22 RESUME (autonomous /autonomous run #2, slot-0·human-planning, Opus 4.8)** — operator directive: "action
  it fully … apply all alerts+hardening then reship live+batch VMs so long-lived jobs harden + emit Slack alerts; fix
  all the issues that cause raise so it works off the bat." **Situation assessment**: the keystone gate (utl@39f8ec85,
  ON ORIGIN) HARD-RAISES `UnprovenHonestAbsenceError` on any
  `record_empty/record_zero_rows(reason= SOURCE_RETURNED_ZERO)` lacking a proving `FetchEvidence` (verified
  `_writer_record.py:238-249` on origin). Tradfi batch+live are NOT threaded on origin (massive_futures_backfill=1,
  websocket_runner=2, sentinels=6 un-threaded SOURCE_RETURNED_ZERO sites) → **re-ship would crash on every legitimate
  zero-trade strike**. **BUT the per-adapter threading is PEER-IN-FLIGHT**: MTDS
  `live/websocket_runner.py`+`live/manifest_recorder.py`+`live/_is_universe.py` and UTL `manifest_writer/` are
  mid-edit-dirty under the `data_completion_to_100_all_ag` lane (the plan's own Coordination note designates that lane
  the per-adapter owner; "each adapter that plan touches threads fetch_evidence Phase-1 P0"). Per the multi-agent HARD
  RULE (don't edit mid-edit-dirty peer files) + the operator's "fix the raises PROPERLY" (a stubbed FetchEvidence
  defeats the gate), **per-adapter threading stays the peer lane's; re-ship is GATED on it landing on origin**. **My
  non-colliding half this run** = make the self-monitoring actually LIVE + regression-proofed, then re-ship the instant
  threading lands: (1) Wave-4b INFRA — schedule the 3 e2e daily-audit crons (deployment-service, mirror
  `cf_manifest_audit_scheduler.tf`); (2) Wave-4b — MTDS QG STEP 5.89 wiring the 3 audits (mirror 5.88) + Phase-3
  reader/writer bucket-env parity; (3) Phase-1 ratchet — extend the existing `check_unrouted_source_returned_zero.py`
  (PM QG 5.86 + baseline) to flag except-reachable SOURCE_RETURNED_ZERO lacking fetch_evidence; (4) Codex docs ×3.
  Dispatched as 3 disjoint-repo sub-agents (deployment / MTDS / PM) shipping via isolated worktree off origin (workspace
  clones dirty). **RE-SHIP TRIGGER (for a compressed future-me)**: when
  `git -C market-tick-data-service show origin/live-defi-rollout:market_tick_data_service/live/websocket_runner.py | grep -c fetch_evidence` >
  0 (live path threaded) → rebuild tarball `create-code-tarballs.sh` from clean LDR + relaunch the live producer
  (`mtds-live-tradfi-*`, LONG_LIVED_LIVE) with `emit_pipeline_heartbeat` wired; batch tarball re-ship makes the next
  backfill wave hardened (running CME fleet is on pre-gate code → finishes fine, no crash).
- **2026-06-22 SPORTS per-AG block (autonomous /autonomous run, Opus 4.8)** — executed the Sports dispatch. **Situation
  found**: most sports keystone threading was ALREADY in the workspace clone as in-flight sports-lane WIP (sfi.py /
  weather.py / process_zero_records.py / sports_fixtures_daily_repoll.py all thread `FetchEvidence` at every
  `record_empty(SOURCE_RETURNED_ZERO)` site; verified the 5 IS SOURCE_RETURNED_ZERO sites each carry a proving
  `FetchEvidence(http_status=200, response_received=True, rows_in_response=0)`), MTDS live (`live/websocket_runner.py` +
  `live/manifest_recorder.py`) fully keystone-aware + `emit_pipeline_heartbeat` wired, and `reprobe_sports.py`
  (`register_reprobe_hook("sports", reprobe_source)` over ODDS_API) already shipped (e2e@…). **My net-new this run**:
  (1) closed the **features-service gap** — `features_service/sports/cli/handlers/batch_handler.py` had TWO
  `record_empty(SOURCE_RETURNED_ZERO)` sites with NO `fetch_evidence` (would HARD-RAISE once gated UTL releases) → now
  thread `build_fetch_evidence(source="sports_features", http_status=200, rows_in_response=0)` on both the table-export
  and the per-feature-group compute empty-df paths (proven 2xx+0-rows; the `except` already routes genuine failures to
  `record_failed`); (2) **DP_SOURCE_RATE_LIMITED** emit on every 429 in `BaseSportsReferenceAdapter._get_with_retry`
  (instruments-service base.py) + a per-class `_rate_limit_429_count` — a throttled sports backfill now surfaces in
  #data-pipeline-alerts instead of silently sleeping to the minute boundary (registry DP-RATE-003); (3) regression
  tests: new `TestSportsRateLimitEvent` in `test_fetch_evidence_keystone.py` (asserts 429→DP_SOURCE_RATE_LIMITED) +
  strengthened the features `test_empty_league_day_calls_record_empty` to assert the keystone `fetch_evidence` proves
  honest absence. Verified existing coverage: DP-VM-001 (OOM exit-137) + DP-FETCH-002 (error-as-empty) in the IS
  keystone test; DP-COVERAGE-003 (EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE) in MTDS `test_sentinels_coverage.py`;
  null-vs-`""` dedup (DP-ORDER-003) is the UTL-consolidator issue doc (cross-cutting, not crash-risk). **base.py 3
  basedpyright errors PRE-EXIST on origin (Lock-getter/resp.json-Any/exc.status-cmp) — my edits add 0 new type errors.**
- **2026-06-22 RESHIP context** — running TM/FS backfills (`tm-backfill-20260622-125650` /
  `fs-backfill-20260622-125711`, both already on **e2-standard-8** — the DP-VM-001 sizing guard is live in the
  launchers) + live odds VM (`mtds-live-sports-odds-api-trades-20260621-213937`, e2-standard-4) are HEALTHY+advancing
  but on the **12:57 tarball** — the FS VM still emits the FootyStats odds source-mislabel
  (`source='footystats' disagrees with pipeline_mode='batch_odds_api'`, fail_fast) because the fix (`ad3a945`, 15:21)
  post-dates its launch. The hardened reship from current LDR carries that fix → resolves the live mislabel.

- **2026-06-22 run #2 RESULTS (slot-0·human-planning, Opus 4.8)** — 4 disjoint-repo sub-agents fanned out (no collision
  with the live per-adapter peer lane). **LANDED ON ORIGIN**: (1) `deployment-service@7b84146` — 4 audit Cloud Run
  Jobs + schedulers (digest/hygiene-changed/hygiene-full-weekly/reprobe), mirroring cf_manifest; (2)
  `unified-trading-pm@894610bc2` — Phase-1 ratchet (STEP 5.99 sibling check, baseline `{}`) + 3 codex docs
  (proof-of-honest-absence contract, re-probe flow, alerts-doc verified). **BUILT + QG-GREEN BUT QUICKMERGE-GATED on
  UAC-clean** (live peer editing UAC): MTDS QG STEP 5.90 (3-audit wiring, all `--smoke`-pass) + STEP 5.91 bucket-parity
  check → on `origin/wip-preserve/mtds-qg-5.90-5.91-bucket-parity-20260622@32e8b6e`. **NEW FINDING — 8 genuine C6
  reader-bucket-env bugs** surfaced by the parity check (env-less defi-instruments reads → the defi-6% stale-read class)
  → filed as a tracked P1 CODE todo routed to the defi/data_completion lane (the `_instruments_metadata.py:218/442/518`
  ones match the exact CLAUDE.md-documented bug; the `orchestrator/__init__.py` ones use `get_bucket_name` — verify
  env-awareness first). **IMAGE GAP**: the audit crons are wired but won't RUN until an e2e-audit image bundles the
  scripts (a sub-agent began it but was cut off by a session limit → new tracked todo; verify nothing partial landed).
  **RE-SHIP STILL GATED**: re-checked origin — tradfi batch+live still `fetch_evidence=0`; the peer landed
  `build_fetch_evidence` to UAC origin (grep=2) but hasn't pushed the MTDS adapter threading yet. **NOTE — full PM QG
  can't emit a green sentinel fleet-wide right now** due to a semver-owned `workspace-manifest.json` version-alignment
  drift (`versions[utp]` behind `origin/main`); PM scripts/docs ship via the prek-gated carve-out until semver realigns
  (not an agent fix).

- **2026-06-22 KEYSTONE-THREADING CONSOLIDATION (autonomous /autonomous run, Opus 4.8 — single-owner consolidate of the
  in-flight fetch_evidence threading left by 3 limit-killed agents across MTDS/IS/UAC).** Mission: finish + GREEN +
  COMMIT the dirty threading WIP serially. **Findings on entry**: threading was ~complete (grep-checker: 0 genuine
  un-evidenced `SOURCE_RETURNED_ZERO`/`record_zero_rows` reachable from a fetch/except branch in MTDS or IS source — 2
  flagged sites were false positives: a `was_expected=True` sentinel + an `EXPECTED_*` oracle branch, both gate-exempt).
  All dirty files were dead-agent WIP (no `.agent-claim`, mtime ~100 min — no live peer). **CONVERGENCE (rule 4)**: the
  **IS orchestrator threading (process_zero_records/sfi/weather) + the UAC `footystats_odds` pipeline_mode fix ALREADY
  SHIPPED** via peer commit `c4687fc` (FF'd into the IS clone mid-session) — my identical local edits showed zero diff
  vs HEAD after the FF, so those lanes need no commit (UAC `pipeline_mode.py` now clean on origin). **Fixes I made**:
  (a) restored the `# QG-allow:` marker comment on 3 IS `reason=SOURCE_RETURNED_ZERO` lines (process_zero_records ×1,
  sfi ×2) that the threading reformat had stripped → STEP 5.86 (`check_unrouted_source_returned_zero`) went green (these
  also converged into `c4687fc`); (b) MTDS `massive_futures_backfill_handler.py` — the threading set the FetchEvidence
  `endpoint=` to a raw `s3://…` f-string → tripped bucket-SSOT ratchet STEP 5.12b; changed to a plain `{source}:{key}`
  diagnostic token (endpoint is a re-probe provenance label, not an I/O URI); (c) MTDS `_defi_manifest.py` comment
  reworded (`try/except:` literal in a comment tripped the bare-except matcher). **MTDS size regressions** (threading
  bloated `live/websocket_runner.py` 883→999L >900, + 7 oversized methods) → dispatched a sonnet sub-agent to extract
  helpers (behaviour-identical, no keystone semantics touched). **MTDS reconcile (rule 4)**: FF'd MTDS behind=12 (peer
  promotion/version-bump + the `_umi_extended.py` extended-candle fix `3b9b27e` — which my dirty `_umi_extended.py` was
  byte-identical to, i.e. the same dead-agent WIP that got promoted, NOT threading → now clean). Folded the eigenlayer +
  `migrate_onchain_perp_canonical_instrument_id.py` from a leftover autostash (eigenlayer already==origin; migration
  script is a separate one-off, retained). Dropped 2 redundant duplicate dead-agent autostashes (verified only a trivial
  1-line mock delta; left all OTHER named stashes — orphan-wip / tardis-split-900L / databento-flip — untouched).
  **STILL OPEN at this log point**: IS kalshi venue-casing unit (`return "KALSHI"` + `available_from` floor + 3
  prediction tests — DP-PATH-006, genuinely unshipped) re-QG+commit; MTDS threading commit once the size sub-agent +
  re-QG are green; grep-proof; checkbox flips. **MTDS threading verified genuinely unshipped on origin** (live+defi
  evidence synthesis grep=0 on origin/LDR) — so it IS the real remaining ship. **Residual left to peer lanes**: UAC
  `lifecycle_class.py` `umbrella`-field tail (deployment-observability lane — its sibling `Deployment*` enums + exports
  already on origin; small coherent dead-WIP tail, not threading, left for that lane).
- **2026-06-22 KEYSTONE-THREADING LANDED (autonomous /autonomous run, Opus 4.8 — resumed the `defi-keystone-finish`
  claim).** The MTDS threading WIP left by the limit-killed agents is now COMMITTED + pushed: **MTDS@fbac3a9** (34 files
  — 17 source + 17 tests + extracted `_ws_window_helpers.py`). Broke the deadlock by FINISHING the threading to QG-green
  (NOT by isolating — the whole tree greened so no stash was needed). **Fixes I made to get green** (all on my own
  threading files, none weakening the gate): (a) removed unused `MASSIVE_S3_BUCKET` import (F401) in
  `massive_futures_backfill_handler.py`; (b) updated 1 stale test assertion in
  `test_massive_futures_backfill_handler.py` (`endpoint.startswith("s3://")` → `startswith(f"{MASSIVE_SOURCE}:")` — the
  threading deliberately changed the FetchEvidence endpoint to a `{source}:{key}` provenance token to satisfy
  bucket-SSOT ratchet 5.12b; test was stale); (c) extracted 2 helpers to clear the 50L method cap that threading pushed
  over — `oracle_prices_handler._record_chainlink_empty` + `aggregator_route_handler._aggregator_preflight_guard`
  (behaviour-identical); (d) narrowed 2 threading-introduced broad `except Exception:` to the repo-canonical tuples
  (`sentinels.py` → `(KeyError,ValueError,AttributeError,TypeError)`; `onchain_perp_batch_handler.py` →
  `(OSError,ValueError,KeyError,RuntimeError)`) — origin had 0 broad-excepts so the gate counted these as violations;
  the narrow set keeps the keystone-safe "any failure → disqualifying signal → record*failed" intent; (e) fixed import
  alias for the relocated `make_live_window_evidence` (size sub-agent renamed
  `_make_live_window_evidence`→`make*…`during the helper extraction) in the new`test_cefi_keystone_fetch_evidence.py`; (f) updated 4 stale `instruments-store-defi-\*`bucket literals (env-less→env-short`-prd-`) in `test_instruments_metadata_loader.py`to match the C6 reader fix the threading applied (the defi-6% stale-read class —`\_instruments_metadata.py`×3 +`orchestrator/**init**.py`×4 catalog readers now use`resolve_bucket_name`, env-short). **GREP-PROOF**: `check_source_returned_zero_needs_fetch_evidence.py`= 0 unproven callsites for BOTH MTDS and IS. **AGs now raise-free / ready for VM re-ship**: defi, tradfi, cefi, prediction (MTDS handlers all threaded), extended (umi), + sports/defi on IS (peer`c4687fc`). **Findings**: (1) the adapter-contract-call baseline warned on websocket_runner (11→8) + lending_indices (6→5) — both FALSE POSITIVES (the 6 websocket calls MOVED into the new `\_ws_window_helpers.py`, not in the per-file baseline; the lending "6th" was a `record_zero_rows`literal in a COMMENT the threading reworded) — QG still EXIT=0 so warn-only; left baseline untouched (no masking). (2) Left dirty + UNSHIPPED (NOT keystone — belong to other lanes, deliberately excluded from the commit):`scripts/run_polymarket_v9_rewalk.sh`(one-off, predictions_master) +`scripts/migrate_onchain_perp_canonical_instrument_id.py`
  (one-off migration, 0 fetch_evidence). **Per-AG reprobe hooks / rate-events / heartbeat (the OTHER half of each per-AG
  dispatch item) remain the per-AG agents' job** — this run completed the keystone THREADING half only.
- **2026-06-22 C6 READER-BUCKET-ENV FIXES (Phase 3, slot-6·human-planning, Opus 4.8)** — operator "fix pls" the 8 C6
  reader-bucket-env bugs the new parity check surfaced (the defi-6% stale-read class). **Restored + RAN
  `check_reader_writer_bucket_parity.py`** (from `wip-preserve/mtds-qg-5.90-5.91-bucket-parity-20260622`) → confirmed
  **8 violations**: `engine/orchestrator/__init__.py:445/447/449/451` (`get_bucket_name("instruments",ag)` ×4 catalog
  readers, F4 path), `cli/handlers/_instruments_metadata.py:218/442/518` (`build_bucket("instruments",…,"defi")` ×3),
  `live/websocket_runner.py` (`build_bucket("instruments",…)` ×1). Verified ALL 8 are genuine bugs (both env-less
  resolvers yield `instruments-store-{ag}-{pid}` — NO `-prd-`; writers yield `instruments-store-{ag}-prd-{pid}`,
  live-probed). **FIXED 7 of 8** → aligned to
  `resolve_bucket_name(cloud=..., kind="instruments-store", asset_group=...)` (the already-shipped `_defi_manifest.py`
  pattern). Diagnosed `test_instruments_metadata_loader.py` asserting the OLD env-less bucket =
  **test-wrong-not-code-wrong** → updated 4 assertions to env-short. **All 7 + the test fix LANDED on
  `origin/live-defi-rollout@fbac3a9`** (swept in via the live peer's keystone-threading quickmerge — my 3 files were
  clean in the shared workspace clone when the peer ran `quickmerge`; verified my exact comment signatures present on
  origin: orchestrator C6 comment ×1, \_instruments_metadata C6 comment ×3, test env-short ×4). **Parity check re-run vs
  pushed origin = 1 violation (down from 8)** — only `websocket_runner.py:467` (peer-owned). **8th site DEFERRED to the
  live MTDS-threading lane** (`data_completion_to_100_all_ag`): (a) the peer is actively committing that exact file
  (fbac3a9→26202e1, mtime fresh), (b) a clean local QG sentinel is blocked by an environmental semver version-alignment
  lag (PM clone 11 behind origin/main; one dep version drifted; `--skip-version-alignment` is human-only). The 8th fix
  is fully PREPARED + validated (helper `_instruments_store_bucket(ag)` mirroring the prediction reader; ruff ✅ /
  basedpyright == baseline 12 / 31 websocket tests ✅ / `_read_is_parquet_sync` ≤50L / import-patterns 0 / parity 0) —
  the threading lane lands it on its next clean window. Parity check is **warn-only** so 1 remaining site does NOT
  redden the fleet; flip to hard-block once the 8th lands. NOTE: the parity check + QG STEP 5.90/5.91 wiring (the `[~]`
  Wave-4b row above) was being landed in parallel by a separate `_land_mtds_qg` agent (staged
  `scripts/quality-gates.sh` + `check_reader_writer_bucket_parity.py`) — left to that agent's unit, not duplicated here.
- **2026-06-22 BATCH-LOOP HEARTBEAT WIRING + RESHIP-VERIFY (slot·human-planning, Opus 4.8, /autonomous reship run)** —
  operator close-ask: wire heartbeat → reship → verify Slack alerts fire off-the-bat. **Findings on entry**: a peer had
  ALREADY reshipped the cefi + tradfi LIVE matrix on the hardened **17:16 UTC tarball** (`mtds-live-cefi-*` +
  `mtds-live-tradfi-cme-trades` relaunched `20260622-1718xx`→`1721xx`); verified the tarball's `websocket_runner.py`
  carries `emit_pipeline_heartbeat` (count=2) + onchain_perp keystone (7 markers) + raise-free; a reshipped cefi VM
  (`...171809`) boots CLEAN (no `UnprovenHonestAbsenceError`/traceback) + is producing (per-VM manifest shard 1→3
  entries 17:21-17:22). So the **critical keystone+heartbeat hardening is live on cefi/tradfi producers**. **My net-new
  this run (the cross-cutting batch-backfill heartbeat gap — per-AG live recorders + onchain were wired, but the GENERIC
  multi-day batch backfill loops were NOT)**: (1) **instruments-service@1a44cbf** — wired `emit_pipeline_heartbeat` per
  completed date into `InstrumentsHandler.process()`, full QG green 71s + sentinel, shipped via quickmerge `--files`;
  (2) **MTDS `TickDataHandler.process()`** — same per-date heartbeat into the GENERIC CeFi/TradFi/multi-AG backfill loop
  (`process_ticks` returns → emit cumulative rows_captured + asset_group + source); basedpyright 0-errors, ruff clean
  (noqa form == onchain_perp). **BLOCKED on ship** by the SAME environmental semver version-alignment lag the 8th-C6
  entry hit — PM-manifest `versions{}` on LDR is behind origin/main for ~6 repos (uac 0.47 vs 0.48, ao 0.39 vs 0.40,
  deployment 0.38 vs 0.39, e2e 0.23 vs 0.24, IS 0.35 vs 0.36); the QG version-alignment PRE-check hard-BLOCKS before any
  substantive gate; `--skip-version-alignment` is human-only. The PM manifest fix (`versions.uac→0.48.0`) sits
  DIRTY+unpushed in the shared PM clone (a peer's in-flight `run-version-alignment.sh --fix`, co-dirty with
  `canonical-dependency-manifest.json` — NOT mine to push). MTDS heartbeat edit validated + left dirty in the slot
  clone; lands on the next clean window (todo below). **STEP 4 verified**: `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` smoke =
  **HTTP 200 `ok`** (live message in #data-pipeline-alerts); alerting-service
  `data_pipeline_slack`+`data_pipeline_rules`+router on LDR; the 3 DP fleet monitors are LIVE Cloud Run crons
  (`uts-prod-dp-heartbeat-watcher` `*/5`, `dp-exit-code-monitor` `*/5`, `dp-meta-watchers` `*/15`, all ENABLED,
  last-fired 17:20, exit 0) reading the reshipped fleet's `vm-heartbeat/{vm}.txt` durable blob + the
  `PIPELINE_HEARTBEAT` event stream. **Reship GAPS (todos below)**: sports-live
  - prediction-live NOT yet on the 17:16 tarball; running backfills are on the old tarball (finish fine — the keystone
    gate only hard-raises in the NEW code; the old running fleet won't hit it; next backfill wave is hardened).

---

## Reship + batch-heartbeat residual (tracked todos — 2026-06-22 reship run)

- [x] ✅ [INFRA] P0. **Reship + RESTART the 3 running sports VMs on the tee-flush-fixed tarball** — DONE 2026-06-22
      (slot·human-planning, Opus 4.8, /autonomous). The running TM/FS backfills + live odds VM were on the
      PRE-tee-flush-fix tarball (their GCS run.log froze ~5 min in → fleet watchers blind). Rebuilt the SPORTS tarball
      from CLEAN detached worktrees off origin/LDR (`/tmp/clean-ldr-sports-193244`,
      `WORKSPACE_ROOT=$CLEAN create-code-tarballs.sh --asset-group SPORTS`) — bakes TASK-1 (UTL@13653f9f uploader
      staleness ceiling + deployment-service@82431d1 wrapper/cli) + keystone IS@aebbc83 (c4687fc FetchEvidence
      threading, ancestor-verified) + the live/batch heartbeat wiring. **GREP-PROOF on the shipped GCS artifacts**:
      `vm/vm-exec-with-gcs-tee.sh`=3 freshness markers; `unified-trading-library-code` uploader=7 `max_staleness_sec`;
      `deployment-service-code` heartbeat_cli=3 `upload_max_staleness_sec`; `mtds-code` tick_data_handler=2
      `emit_pipeline_heartbeat`. Gracefully DELETED the 3 old VMs (the live odds VM holds the WS singleton lock → waited
      STOPPING→gone before relaunch) then relaunched all 3: `tm-backfill-20260622-193803` +
      `fs-backfill-20260622-193812` (`launch-{transfermarkt,footystats}-backfill-vm.sh 2019-01-01 2026-06-21`,
      e2-standard-8, skip-fresh re-walk-but-skip-captured) + the live odds VM
      `mtds-live-sports-odds-api-trades-20260622-193840` (`launch-mtds-live.sh --asset-group sports --shard-spec
      sports:odds_api:trades` 5 EPL/LaLiga/SerieA/Bundesliga/Ligue1 leagues, RUNNING off-the-bat). T+~20min
      verification below. — deployment-service

- [x] ✅ [CODE] P1. **Land the MTDS `TickDataHandler` batch-loop heartbeat** — DONE **market-tick-data-service@e7177bd**
      (version-align cleared `aligned:True` → shipped via
      `quickmerge --agent --files 'market_tick_data_service/cli/handlers/tick_data_handler.py'`; QG content-sentinel
      verified byte-identical Pass-1 green, STAGE 0.4 FF-reconciled `26202e129→059df5f8a` cleanly, landed LDR). Adds
      `_emit_date_heartbeat` + per-date `emit_pipeline_heartbeat` in the generic CeFi/TradFi/multi-AG backfill loop
      (`process()` → after each `process_ticks` date completes; `rows_captured_cum` cross-check for
      DP_VM_GONE_NO_CAPTURE; best-effort, never aborts the backfill — pattern mirrors the shipped
      `onchain_perp_batch_handler` + IS `InstrumentsHandler@1a44cbf`). A hung/idle batch backfill date now trips
      DP_VM_STALL fleet-wide once the tarball rebuilds. — market-tick-data-service
- [x] ✅ [INFRA] P1. **Reship sports-live + prediction-live producers on the hardened tarball** — DONE 2026-06-22
      (slot-0·human-planning, Opus 4.8). Rebuilt `mtds-code.tar.gz` (+UAC/UTL/IS/deployment) from CLEAN detached
      worktrees off origin/LDR (17:56 UTC; grep-PROOF on the shipped tarball: tick_data_handler heartbeat=4 +
      websocket_runner heartbeat=2 + keystone threading + 8th-C6). Gracefully DELETED the 5 PRE-17:16 producers (freed
      singleton lock + WS feed — drain, not SIGKILL) then relaunched all 5 on the hardened tarball:
      `mtds-live-sports-odds-api-trades-20260622-181110`
      (`launch-mtds-live.sh --asset-group sports --shard-spec     sports:odds_api:trades`, 5
      EPL/LaLiga/SerieA/Bundesliga/Ligue1 leagues) +
      `prediction-live-{polymarket,kalshi}-{trades,book-snapshot-5}-2026062218*` (`launch-prediction-live.sh`).
      **T+10min verification (18:23 UTC) — ALL 5 RUNNING, crash_signatures=0 (zero UnprovenHonestAbsenceError /
      Traceback / Fatal / CRITICAL), boot_markers present (authenticated/subscribed/resolved), polymarket shards already
      9078–9079 loglines = actively streaming.** The hard-raise gate does NOT trip the hardened producers. —
      deployment-service

- **2026-06-22 run #2 RE-SHIP DONE (slot-0·human-planning, Opus 4.8)** — the peer `data_completion` lane landed the
  tradfi `fetch_evidence` threading + `emit_pipeline_heartbeat` wiring on origin LDR (verified: ws=2/hb=2, massive=3,
  sentinels via `_reached_empty_fetch_evidence`=4). Monitor `br4vlaa63` fired RESHIP-READY → I rebuilt the code tarball
  from **CLEAN detached worktrees off origin/LDR** (NOT the dirty workspace clones — peer mid-threading other AGs),
  grep-verified the built GCS tarball (`gs://deployment-scripts-…/code/mtds-code.tar.gz`, sha `26202e12`) actually
  contains the threading+heartbeat, gracefully deleted the old live producer (freed the per-shard lock) and relaunched
  `mtds-live-tradfi-cme-trades-20260622-172152` (`tradfi:CME:trades` ES/NQ/CL/GC). **T+16min verification**: RUNNING,
  databento WS authenticated (`session_id=1139587315`), per-VM manifest shards writing to `-tradfi-prd-`, **zero
  `UnprovenHonestAbsenceError`/tracebacks** — the hard-raise gate does not trip the hardened producer. **FLAG (separate,
  out-of-scope, pre-existing)**: no `PIPELINE_HEARTBEAT` has _emitted_ yet — `emit_pipeline_heartbeat` is gated on the
  first candle-window FLUSH which needs captured rows, and the manifest sits at 4-registered/0-captured (no CME trade
  ticks flowing in-window; the OLD VM showed the identical pattern). Live capture is UP; heartbeat will emit on first
  flush. **Tracked todo below** to look at why CME trades aren't flushing windows. **Wip-branch landings still GATED** —
  the workspace stayed dirty-deps (e2e/deployment/strategy-service/MTDS all churning) so the 3 wip-preserve branches
  (MTDS QG 5.90/5.91, e2e Dockerfile, deployment var) couldn't quickmerge; preserved + recover-documented, land on the
  next clean-deps window.
- **2026-06-22 RESIDUAL CLOSE-OUT (autonomous /autonomous run, slot-0·human-planning, Opus 4.8)** — operator: the semver
  version-alignment lag that blocked the 2 residuals is CLEARED (`check-dependency-alignment.py --json` →
  `aligned:True`, verified on entry). **Residual-1 (MTDS batch-heartbeat) DONE** — `market-tick-data-service@e7177bd`
  via `quickmerge --agent --files 'market_tick_data_service/cli/handlers/tick_data_handler.py'` (QG content-sentinel
  byte-identical Pass-1 green; STAGE 0.4 FF-reconciled `26202e129→059df5f8a` cleanly; landed origin/LDR — grep-verified
  4 heartbeat markers). The 8th-C6 fix also landed on LDR in the same window (`059df5f` — live-hardening lane).
  **Residual-2 (reship sports+prediction live) IN PROGRESS** — rebuilt the code tarball from **CLEAN detached worktrees
  off origin/LDR** (`/tmp/clean-ldr-wt-*`, NOT the dirty workspace clones: workspace MTDS had peer one-off
  `migrate_onchain_perp` + untracked `run_polymarket_v9_rewalk.sh` dirty), CORE+IS scope, uploaded 17:56 UTC;
  **grep-PROOF on the shipped `mtds-code.tar.gz`**: tick_data_handler heartbeat=4 + websocket_runner heartbeat=2 (the
  `./`-prefixed tar paths confirmed). Gracefully DELETED the 5 PRE-17:16 live producers (sports-odds + 4 prediction
  shards — frees singleton lock + WS feed; confirmed all 5 gone) then relaunching all 5 on the hardened tarball via
  `launch-mtds-live.sh` (sports `sports:odds_api:trades`, 5 EPL/La-Liga/Serie-A/Bundesliga/Ligue-1 leagues) +
  `launch-prediction-live.sh` (POLYMARKET/KALSHI × trades/book_snapshot_5). T+10min verification pending.
- **2026-06-22 RESIDUAL CLOSE-OUT — VERIFIED DONE (both residuals shipped + fleet hardened).** **Residual-1**:
  `market-tick-data-service@e7177bd` (batch-heartbeat) on origin/LDR. **Residual-2**: all 5 sports+prediction live
  producers RESHIPPED on the hardened 17:56 tarball + **T+10min-verified (18:23 UTC): 5/5 RUNNING, crash_signatures=0,
  boot-clean** (sports-odds 6 markers; polymarket trades+book 12 markers / 9078–9079 loglines streaming; kalshi
  trades+book 12 markers). **STEP 3 fleet verification**: the full live producer set is now on hardened code — 16
  cefi-live (17:18+ tarball) + tradfi-cme-trades (peer relaunched `...182251`) + sports-odds + 4 prediction = **22 live
  producers, all keystone-gated + raise-free + heartbeat-capable**. The 3 DP fleet monitors are LIVE Cloud Run crons
  reading them: `uts-prod-dp-heartbeat-watcher-cron` (`*/5`, last 18:10), `uts-prod-dp-exit-code-monitor-cron` (`*/5`,
  18:10), `uts-prod-dp-meta-watchers-cron` (`*/15`, 18:00) — all ENABLED + firing. **Slack live**:
  `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` POST = HTTP 200 `ok` (message in #data-pipeline-alerts). **Operator close-ask
  MET**: every live + batch producer is on hardened code (keystone hard-raise + per-date/per-window heartbeat) and the
  detect→route→Slack alert path is live off-the-bat. Both residual todos flipped; the data-pipeline-hardening reship is
  CLOSED.
- **2026-06-22 TEE-FLUSH FIX + SPORTS RESHIP (slot·human-planning, Opus 4.8, /autonomous)** — operator close-ask: the
  persisted GCS `run.log` FREEZES ~5 min after launch while the worker runs for HOURS, so the GCS-log-based watchers
  (`dp-heartbeat-watcher` / `dp-exit-code-monitor` / stall-mtime) read a stale log. **ROOT CAUSE (confirmed, two
  timestamps):** the bug is NOT a dying bash daemon — `vm-exec-with-gcs-tee.sh` delegates to the UTL
  `HeartbeatDaemon`'s `LogUploader` thread (lives the VM's whole lifetime; never dies). The `LogUploader.upload_once()`
  anti-churn gate (`deployment_scripts_bucket_softdelete_log_churn`, 2026-06-01) only re-uploaded after the log grew by
  `min_growth_bytes` (256 KiB) — a PURE growth gate with NO time ceiling. A SLOW-but-live scraper (transfermarkt/
  footystats: a few loglines/min) never accumulates 256 KiB → the GCS copy froze. PROOF: `tm-backfill-20260622-125650`
  on-VM `/tmp/vm-exec-7122.log` @ **19:24:33 / 172,267 bytes (168 KiB)** actively fetching, but GCS `run.log` frozen at
  **13:01:03 GMT — 6h23m stale** and only 168 KiB total after 6h (never crossed the 256 KiB re-upload threshold).
  **FIX (UTL@13653f9f):** added `LogUploader.max_staleness_sec` (default 90s) — a CHANGED log (grew ≥1 byte OR mtime
  advanced) is force-re-uploaded once the ceiling elapses even below `min_growth_bytes`; an IDLE log still skips (no
  churn reintroduced; the soft-delete-churn fix preserved). Wired through `daemon.py` + deployment-service
  `heartbeat_cli.py` + `DeploymentConfig.upload_max_staleness_sec` (env `UPLOAD_MAX_STALENESS_SEC=90`) +
  `upload_interval_sec` lowered 120→60 (stat-check cadence so the ceiling fires on time). 3 UTL regression tests
  (force-fresh-when-stale / idle-never-uploaded / disabled-staleness=pure-growth-gate) + a deployment-service ctor-wiring
  guard. Shell header documents the freshness invariant + that the uploader never dies. Net: GCS run.log stays within
  ~1-2 min of the on-VM log for the VM's whole lifetime. Reship of the 3 sports VMs on the fixed tarball + verification
  below.
- [x] ✅ [DATA] P0. **ROOT-CAUSED + FIXED — tradfi CME live captured 0 rows** (`market-tick-data-service@a808ae9` + test
      fix). The databento WS authenticated + subscribed but **never streamed**: `databento_tradfi_ws.py` gated
      `live.start()` behind `if not live.is_connected:` — but `subscribe()` already connects, so `is_connected` is True
      → `start()` (the call that actually delivers records to the callback) **never ran**. basedpyright even flagged it
      (`reportUnnecessaryComparison: expression always evaluates to True`). **Proven**: a standalone databento Live
      probe with the IDENTICAL subscription (GLBX.MDP3 trades, `stype_in=parent` ES/NQ/CL/GC.FUT) got **254 TradeMsg +
      2637 SymbolMappingMsg in 15s** during open CME Monday hours — so market/databento/subscription were all fine; the
      bug was purely the un-called `start()`. Fix: guard `start()` on a `self._started` flag (call once after first
      subscribe, idempotent on re-subscribe) instead of `is_connected`. A unit test that _codified the bug_
      (`...skips_start_when_already_connected`) was rewritten to assert the correct contract. This was a NEVER-WORKED
      bug (the prior "verified working" only checked connect+auth, not capture). Live producer redeployed on the
      fix-included tarball to confirm capture grows. — market-tick-data-service

- **2026-06-22 run #2 CME-FLUSH ROOT-CAUSE + WIP-LANDING (slot-0·human-planning, Opus 4.8)** — operator: "dig into cme
  flush then check wip." (1) **CME 0-capture = a never-worked databento-Live bug** (NOT market/databento/re-ship):
  `databento_tradfi_ws.py` called `live.start()` only `if not live.is_connected`, but `subscribe()` connects first so
  the guard was always False → `start()` never ran → authenticated-but-silent stream. A controlled 15s databento probe
  (identical subscription) got 254 trades → proved the data flows; the producer just never started streaming. Fixed
  (`a808ae9`, guard on `self._started`) + rewrote the unit test that codified the bug + redeployed (verification agent
  in flight). (2) **Wip-landings — dep window opened** (UAC/UTL went clean): landed **MTDS QG 5.90/5.91 +
  bucket-parity** (`0eee1ab`) via the canonical-clone quickmerge (the connector fix proved that path works again). The
  **e2e Dockerfile + deployment-image var still gated** — their quickmerge is blocked by `strategy-service` (peer-dirty,
  can't commit others' WIP); preserved on `wip-preserve/e2e-audit-image-2026-06-22` +
  `wip-preserve/dp-audit-image-var-2026-06-22`, land on the next strategy-service-clean window. The defi lane meanwhile
  fixed one of the 8 C6 bugs (`059df5f`).

- **2026-06-22 CME FIX VERIFIED LIVE (slot-0·human-planning, Opus 4.8)** — redeploy on the fix-baked tarball (commit
  `3a760bf` = `a808ae9` + test fix; grep-confirmed `_started`×4 / zero `is_connected` guard) replaced the producer →
  `mtds-live-tradfi-cme-trades-20260622-182251` (RUNNING). **Capture PROVEN GROWING**: all 4 CME instruments
  `capture_status=captured` — window-1 4474 rows (NQ197/CL3867/GC14/ES396), window-2 1702 rows (counts advancing) →
  window-flush rolling forward (the PIPELINE_HEARTBEAT gate). The exact inverse of the broken VM's frozen 0-captured; no
  `UnprovenHonestAbsenceError`/crash. Tradfi live went 0 (never-worked) → thousands of rows/window. This completes the
  operator's run-#2 mandate (hardening live + re-ship + fix-the-raises + CME flush).

- **2026-06-22 DEPLOYMENT-GAP CORRECTION + operator mandate (slot-0·human-planning, Opus 4.8)** — operator caught that
  NO alerts ever fire for tradfi. **Verified root cause (corrects the prior "alerting substrate LIVE" framing — the CODE
  shipped but was never DEPLOYED end-to-end):** (1) the **alerting-service consumer is not running anywhere** (no Cloud
  Run service in any region, no VM) → the fleet monitors emit `DP_*` to the `lifecycle-events` topic every 5 min but
  **nothing consumes it** → 0 DP** events routed in 24h, even the reused `CONSOLIDATOR_DOWN` path silent. The topic
  WIRING is correct (monitors→`lifecycle-events`, subscriber→`lifecycle-events-sub`); only the running consumer was
  missing. (2) the **daily-audit crons** (digest/hygiene/reprobe — which detect the 12.5k tradfi `attempted_failed` +
  misclassified empties) were **never applied** (terraform on origin but image-var unapplied). (3) the real-time
  monitors only catch VM *crashes* — and tradfi-bf VMs *succeed\* (exit 0) — so nothing to fire on. (4) **No autonomous
  wave-launcher** — the 8-VM tradfi-bf wave was MANUAL; no cron fires waves → backfill stalls at ~68% honest coverage,
  never reaches 100% on its own. **Operator /autonomous mandate: deploy all 3** — (A) the alerting-service consumer
  (Cloud Run subscriber on `lifecycle-events`), (B) the daily-audit crons (on the built `e2e-audit:latest` image), (C) a
  capacity-capped autonomous wave-launcher driving tradfi to 100%. Each verified end-to-end (a real DP*\* event must
  land in #data-pipeline-alerts). In progress.

- **2026-06-22 RELAY ROOT-CAUSE — the `_extract_event_name` "event"-key bug (slot·human-planning, Opus 4.8,
  /autonomous "I don't see any defi warns").** Operator: surely defi has alertable issues — make them actually fire.
  **PROVED defi HAS real findings + the audits emit them LIVE**: ran `manifest_hygiene_daily.py --asset-group defi
  --mode changed` (mode=live → publishes to `lifecycle-events`) → `defi hygiene: RED`, `oracle_expects_but_empty:
  count=5` → emitted **`DP_DIVERGENT_EMPTY` WARN** (19:14:00Z); ran `reprobe_new_empty_confirmed.py --asset-group defi
  --day 2026-06-21` → 9 new SOURCE_RETURNED_ZERO empties → emitted **`DP_EMPTY_REPROBE_DISAGREEMENT` WARN** (19:14/
  19:20Z). The defi `_index` carries **48,924 SOURCE_RETURNED_ZERO** empty_confirmed cells + raw-HTTP error_reasons
  (`400 Bad Request`/`RPC error (eth_feeHistory)`/`404 GET https`) + 3,550 phantoms — abundant real alertable signal.
  **THE BREAK (decisive, root-caused — corrects the prior "consumer not running" framing):** the alerting subscriber IS
  running (alerting-quietness-20260622-191426) + attached to `lifecycle-events-sub` (verified in run.log 19:17:13, no
  403, no crash) + the messages DO land (I pulled my own `DP_DIVERGENT_EMPTY` off `lifecycle-events-sub` directly) + all
  DP_* names match router rules (`data_pipeline_rule_for` → WARN/CRITICAL) + the webhook resolves — YET 0 DP events
  routed in 14 min. **Root cause: UTL `PubSubEventSink.write_event` publishes the event name under the key `"event"`
  (`{"event": name, "service":…, "metadata":{…}}`, event_sink.py:270-279), but the subscriber's `_extract_event_name`
  only checked `("event_name","event_type","type","kind")` — NOT `"event"` → every DP_* (and CONSOLIDATOR_DOWN, and ANY
  UTL log_event on lifecycle-events) mis-extracts to `UNKNOWN_EVENT` → no rule match → silently DROPPED before Slack.**
  This is why the operator never saw defi (or any) DP alerts despite a live, attached, IAM-correct subscriber. **FIX
  (alerting-service `alert_subscriber.py`): add `"event"` FIRST in the extractor key tuple** + 2 regression tests
  (`test_utl_event_key_extracted`, `test_event_key_priority_over_legacy_keys`) — unit-verified the real pulled payload
  now extracts `DP_DIVERGENT_EMPTY` + matches its WARN rule. Shipping QG-green + reshipping the subscriber VM to make
  the relay deliver. **Task-2 (Wave-4b crons) DONE**: `tofu apply` (targeted, 8 add/0 change/0 destroy) deployed the 4
  dp-audit Cloud Run Jobs + 4 schedulers (digest 0 7 / hygiene-changed 0 8 / hygiene-full 0 8 Sun / reprobe 0 9, all
  ENABLED, on `e2e-audit:latest`); `gcloud run jobs execute uts-prod-dp-daily-digest` ran to Completed. **Task-3
  (defi DP_SOURCE_RATE_LIMITED) is ALREADY DONE in the live peer defi lane** (`data_completion_to_100_all_ag`):
  `ThegraphKeyPoolRotator` (DP-RATE-001/002, emits DP_SOURCE_RATE_LIMITED on 429 + DP_KEY_POOL_EXHAUSTED on exhaustion)
  is fully written in `thegraph_base_client.py` + WIRED into `_dex_pools_subgraph.py` (instantiate→`next_key()`→on 429
  `mark_rate_limited`) as that lane's dirty WIP (mtime <120s = live editor → PROTECTED, not stomped per the
  multi-agent HARD RULE) — awaiting that lane's quickmerge; I did NOT re-implement (would collide).

- [ ] [CODE] P1. **Heartbeat is PER-CHUNK, not time-based → too coarse for slow jobs (operator 2026-06-22)**: `instruments_handler.py:323` (+ `websocket_runner.py`) emit `emit_pipeline_heartbeat` only after each CHUNK completes → cadence = chunk duration (~15+ min for the TM/FS transfer-window/season scrapers), and a MID-CHUNK hang emits ZERO heartbeat for the whole chunk (only the slower log-mtime stall watcher ≥45min catches it). FIX: emit on a BACKGROUND TIMER (~60s, asyncio task / thread) independent of chunk boundaries, so cadence is constant and a mid-chunk hang trips dp-heartbeat-watcher within ~60s+poll. Tune the watcher stall threshold to match (e.g. silent >5-10min → DP_VM_STALL). Reship the affected VMs after. Repos: instruments-service + market-tick-data-service + (watcher) deployment-service.

## Per-AG hardening dispatch (tracked todos — the prompts below are the cold-start context)

- [ ] [CODE] P0. **DeFi agent**: thread `fetch_evidence` into all 9 defi MTDS handlers + IS catalog path;
      `reprobe_source("defi",...)`; guard catalog-freshness / bucket-env / 9-key rotation / PROTOCOL grain / async-GCS.
      — instruments-service, market-tick-data-service
- [x] ✅ [CODE] P0. **CeFi agent**: threaded fetch_evidence into live recorder + onchain batch handler +
      emit_pipeline_heartbeat — market-tick-data-service@26202e1 (full QG 100s, 52 tests, basedpyright 0; live WS
      200+0-ticks=proven honest-absence, GAP→record_failed). Live matrix RESHIPPED hardened. HL-ASTER cefi-class +
      canonical PERP keys shipped (bug#9/13/14).
- [x] ✅ [CODE] P0. **TradFi agent** — DONE 2026-06-22: keystone `fetch_evidence` threaded on origin LDR across the
      tradfi paths — `live/websocket_runner.py` (fetch_evidence=2 + `emit_pipeline_heartbeat`×2),
      `cli/handlers/massive_futures_backfill_handler.py` (via `build_fetch_evidence`, =3),
      `engine/orchestrator/sentinels.py` (via shared AG-aware `_reached_empty_fetch_evidence` helper, =4). **Live
      producer RE-SHIPPED on the hardened tarball** (`mtds-live-tradfi-cme-trades-20260622-172152`, tarball sha
      `26202e12` — grep-verified to contain the threading+heartbeat before relaunch): RUNNING, databento WS
      authenticated, manifest shards writing, **ZERO `UnprovenHonestAbsenceError`/crashes over 16-min verification**
      (the new hard-raise gate does not trip it). The same tarball hardens the next batch wave (running CME fleet stays
      on pre-gate code, finishes fine). `reprobe_source("tradfi",...)` + the 3-dataset/ohlcv_1s/VM_SOURCE guards remain
      per the lane's adapter hardening. — market-tick-data-service, instruments-service
- [x] ✅ [CODE] P0. **Sports agent** — DONE 2026-06-22 (autonomous /autonomous run). Keystone `fetch_evidence` threaded
      at every IS sports `SOURCE_RETURNED_ZERO` site (sfi/weather/process_zero_records/daily_repoll, all proving
      2xx+0-rows) + MTDS live (`websocket_runner`/`manifest_recorder`, was already keystone-aware) + **features-service
      `batch_handler.py` 2 sites NOW threaded** (`build_fetch_evidence`, the prior gap that would HARD-RAISE) —
      instruments-service@c4687fc + features-service@<features-sha>. `reprobe_source("sports",...)` +
      `register_reprobe_hook("sports",...)` already shipped (e2e `reprobe_sports.py`). **DP_SOURCE_RATE_LIMITED** on 429
      in `BaseSportsReferenceAdapter._get_with_retry` (registry DP-RATE-003). Heartbeat live on MTDS live runner.
      Regression tests: DP-VM-001 (OOM) + DP-FETCH-002 (error-as-empty) IS keystone test, DP-RATE-003 rate-limit test,
      features keystone-evidence assertion, DP-COVERAGE-003 (EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE) MTDS sentinels.
      Sports VMs reshipped on e2-standard-8 (hardened tarball). null-vs-`""` dedup (DP-ORDER-003) is the
      UTL-consolidator issue doc (cross-cutting). — instruments-service, market-tick-data-service, features-service
- [x] ✅ [CODE] P0. **Prediction agent** — SHIPPED + RESHIPPED + LIVE-VERIFIED (2026-06-22): `fetch_evidence` keystone
      threaded into the prediction live runner + perp-funding handler; `emit_pipeline_heartbeat` (60s → DP_VM_STALL) in
      the long-lived live WS producers; UAC `build_fetch_evidence`/`fetch_error_signal_for_status|exception` builder
      helpers (uac@LDR, precedence fix: TimeoutError→TIMEOUT not SOURCE_UNREACHABLE); Kalshi live id-format fix
      (`_is_universe.prediction_instrument_ids_from_df` rebuilds `KALSHI:PREDICTION_MARKET:{ticker}` — was passing bare
      tickers the KalshiClob WS connector skipped) on LDR; IS Kalshi adapter floor `available_from`→open-date + venue
      `kalshi`→`KALSHI` (instruments-service@686e0ac, DP-PATH-006). **RESHIP**: all 4 prediction live shards
      (POLYMARKET/KALSHI × trades/book_snapshot_5) relaunched on the hardened tarball + T+10-verified — RUNNING,
      heartbeat=4 each, **KALSHI kalshi_skips=0** (resolves+captures, was skipping every market), resolved 8–9/shard.
      Repos: market-tick-data-service, instruments-service, unified-api-contracts. — 2026-06-22 slot-0·human-planning
- [ ] [CODE] P1. **FOLLOW-UP (C6 / DP-ENV-001, non-prediction, on-VMs-not-LDR)**: the live IS-universe NON-prediction
      reader `websocket_runner._read_is_parquet_sync` still uses `build_bucket("instruments", asset_group=...)`
      (env-LESS legacy shape → stale/absent read → empty universe → silent zero capture) on origin/LDR. Fix =
      `resolve_bucket_name` env-short via a `_instruments_store_bucket(asset_group)` helper (mirrors the prediction
      reader). The fix IS on the reshipped prediction VMs (rode the `--allow-dirty-tarball`), but its LDR ship was reset
      by a concurrent `_h`-clone lane actively churning `websocket_runner.py` (type-narrowing) — re-apply + ship
      coordinating with that lane (a ~6-line change; helper + 1 call-site). Repo: market-tick-data-service. Provenance:
      prediction-hardening reship 2026-06-22.

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

---

## Phase 6 — Alert enrichment (Tier 1) + Self-healing completion (reopened 2026-06-22 under /autonomous)

> Composed with `deployment_observability_parity_live_batch_paper_2026_06_22.md`. Reuse the freshness SLA registry
> (`unified_api_contracts/internal/reference/data_freshness.py`), the Layer-0 recovery-script pattern
> (`deployment-service/scripts/recovery/`, `RecoveryScriptRegistry`, the shipped `refetch-feed`), the
> `autonomous-recovery-matrix.md` breaker model, and `escalate-to-orchestrator`/AutoSpawn — no reinventing.

### Alert enrichment (B — inline trace + deep-links)

- [x] ✅ [CODE] P1. alerting-service: add `deployment_ui_base_url` (+ `deployment_scripts_log_bucket`) config, SM/env
      hot-reloaded (none exists today). — alerting-service@868872c (config.py fields + config_reloaders.py SM keys
      DEPLOYMENT_UI_BASE_URL/DEPLOYMENT_SCRIPTS_LOG_BUCKET + get_paging_credentials; default "" → links omitted)
- [ ] [CODE] P1. UTL writer-gate `_emit_unproven_honest_absence`: add `venue`/`data_type`/`day` (from `row_key`) + an
      `error_message` to the DP_UNPROVEN_HONEST_ABSENCE `details`. — unified-trading-library
- [x] ✅ [CODE] P1. `data_pipeline_slack.py::_build_blocks`: append a fenced-code trace block
      (evidence/exit_code/run_log_tail, ≤3000 chars) + an actions block with deep-link buttons — data-status
      `{base}/service/{svc}/data-status`, VM logs `{base}/ops/vms/{vm}`, GCS `run.log` console link. Thread
      `deployment_ui_base_url` from `router._mirror_to_data_pipeline_slack`. — alerting-service@868872c
      (`_build_trace_block` truncates to 3000 + `_build_action_block` omits links when inputs absent / base="" ;
      `send_data_pipeline_alert` + `_mirror_to_data_pipeline_slack` thread base+log_bucket; tests block-network)
- [ ] [CODE] P2. deployment-service exit_code monitor: add `run_log_tail` (last N lines of RUN_LOG_BLOB) to the finding
      `details` for the inline trace. — deployment-service
- [x] ✅ [CODE] P0. **Fix the GCS run.log freshness freeze (tee-flush lag) — the GCS-log watchers' substrate** — DONE
      **unified-trading-library@13653f9f + deployment-service@82431d1** (QG-green: UTL 127s exit0 + deployment 55s exit0;
      shipped via `quickmerge --agent --files`). The UTL `LogUploader`
      (`unified_trading_library/lifecycle/uploader.py`, the GCS uploader thread inside `HeartbeatDaemon` that
      `vm-exec-with-gcs-tee.sh` launches — it does NOT die early, lives the VM's whole lifetime) only re-uploaded a VM
      run.log after it grew by `min_growth_bytes` (256 KiB) — a pure anti-churn gate with NO time ceiling. A SLOW-but-live
      log (low-volume scraper) never accumulates 256 KiB → the GCS `run.log` FROZE for hours while the on-VM
      `/tmp/vm-exec-*.log` advanced, blinding `dp-heartbeat-watcher` / `dp-exit-code-monitor` / the stall-mtime monitor
      (CONFIRMED: `tm-backfill-20260622-125650` on-VM log @19:24:33 / 172,267 B but GCS run.log frozen @13:01:03 GMT —
      6h23m stale). FIX: added `LogUploader.max_staleness_sec` (default 90s) — a CHANGED log (grew ≥1 byte OR mtime
      advanced) is force-re-uploaded once the ceiling elapses even below the growth threshold; an idle log still skips
      (no churn reintroduced). Wired through UTL `daemon.py` + deployment-service `heartbeat_cli.py` +
      `DeploymentConfig.upload_max_staleness_sec` (env `UPLOAD_MAX_STALENESS_SEC=90`) + `upload_interval_sec` 120→60.
      3 UTL regression tests + deployment-service ctor-wiring guard. — unified-trading-library, deployment-service

### Self-healing completion (C — wire tiers to existing recovery, add actuators)

- [ ] [CODE] P0. Add `data_pipeline_failure` to `escalate-to-orchestrator` `WALL_TYPES`
      (`agent-orchestrator/server/escalation.py`) + a boot-prompt template, so a DP `file_issue`/`page` finding can
      fast-spawn an autonomous worker (today WALL_TYPES has no DP member → ValueError). — agent-orchestrator,
      unified-trading-pm (.github)
- [ ] [CODE] P1. Wire `escalation.py::route_finding` `auto_recover` tier → the Layer-0 `RecoveryScriptRegistry` (the
      `refetch-feed` pattern); register DP actuators. — deployment-service
- [ ] [CODE] P1. **Actuators (today detect+page only)**: consolidator auto-relaunch (Cloud Run Job re-execute on
      CONSOLIDATOR_DOWN), backfill-VM auto-relaunch on exit-137 within retry budget. — deployment-service
- [ ] [CODE] P1. **Schedule** the daily empty-reprobe (`reprobe_new_empty_confirmed.py`) + auto-flip
      confirmed-misclassified `empty_confirmed`→`attempted_failed` cells (the reclassifier). — deployment-service /
      e2e-testing
- [ ] [CODE] P1. **Bucket-env parity preflight** (DP-ENV-001 — reader env-less vs writer env-short) as a generic gate. —
      market-tick-data-service
- [ ] [CODE] P1. **429-aware key-pool rotation** + `DP_KEY_POOL_EXHAUSTED` alert (TheGraph 9-key currently degrades
      silently to unauth). — market-tick-data-service
- [ ] [DOC] P1. **`RB-DATA-*` DR runbook** — the consolidator→MTDS→features cascade with RTO/RPO + auto-vs-human scope
      (none of the 22 `rb_*` runbooks is data-pipeline). — unified-trading-pm
- [ ] [CODE] P2. Flip `data-pipeline-alerts.registry.yaml` modes `verbose`→`active` as each `escalation:` tier is wired
      to plumbing. — unified-trading-pm
