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
- [ ] [CODE] P0. **Slack notifier** `data_pipeline_slack.py` (parallel to `uts_live_alerts_slack.py`): SM-hot-reloaded
      `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`, best-effort mirror, no-op when unset. — **alerting-service**
- [ ] [CODE] P0. **Router rules** `rules/data_pipeline_rules.py` loading `.registry.yaml` →
      `event_pattern → channels + severity` (INFO=channel; WARN=channel+dedup;
      CRITICAL=channel+telegram+pagerduty+incident-gateway). Wire into `router.route_event()`. — **alerting-service**
- [ ] [CODE] P0. **UAC `DATA_PIPELINE_ALERT_RULES`** (parallel to `LIVE_ALERT_RULES`) generated from the registry so
      emitters + router share one contract; subscribe the data-pipeline PubSub topic in `alert_subscriber`. —
      **unified-api-contracts, alerting-service**
- [x] ✅ P0. **Event constants** — DONE utl@39f8ec85 (37 DP_* + PIPELINE_HEARTBEAT in events/event_types.py, DATA_PIPELINE_EVENT_TYPES set, re-exported via events/__init__). **Event constants** for every `event:` in the registry added to UTL `events/event_types.py` (DP*\*
      family), so `log_event(DP*\*)` from any VM/watcher/audit routes correctly. — **unified-trading-library**
- [ ] [CODE] P1. **Escalation hop** mirroring `ci_failure_watcher.py`: `file_issue` tier auto-files
      `plans/active/issues/<slug>_<date>.md` + pings the orchestrator inbox when a deterministic candidate list is
      non-empty; `auto_recover` runs the in-band fix; `page_operator` routes CRITICAL with no recover scope. —
      **deployment-service / unified-trading-pm**
- [ ] [DOC] P1. Register the channel in `alerting-service/docs/CONFIGURATION.md` + the three terraform SA accessors for
      `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`. — **alerting-service, deployment-service**

## Phase 1 (KEYSTONE) — Proof-of-honest-absence gate + daily empty re-probe (closes C1)

> The writer already rejects a _blank_ reason (`LegacyBlankErrorReasonError`, after the 2026-05-07 RED ALERT). The
> remaining gap: `record_empty(reason=SOURCE_RETURNED_ZERO)` is taken on **trust** — nothing proves the HTTP call
> returned 200+empty rather than a 401/403/429/5xx/timeout/exception that fell through. This phase makes honest-absence
> a **proven** state, not a claimed one. **This is the highest-priority phase.**

- [x] ✅ P0. Define `FetchEvidence` value-object in UAC — DONE uac@6c27bfa0 (FetchEvidence.proves_honest_absence + FetchErrorSignal StrEnum + DISQUALIFYING_FETCH_SIGNALS + UnprovenHonestAbsenceError; QG green 220s, 59 tests). Define `FetchEvidence` value-object in UAC (`unified_api_contracts.canonical.crosscutting`):
      `{http_status:int, response_received:bool, rows_in_response:int, source, endpoint, attempted_at, error_signal:str|""}`.
      The closed set of **disqualifying signals** (any present ⇒ NOT honest-absence ⇒ must `record_failed`): non-2xx
      HTTP, auth (401/403), rate-limit (429/`RATE_LIMITED`), 5xx, timeout/`CONNECT_ERROR`, exception-in-adapter,
      empty-key/`MISSING_CREDENTIAL`, empty-but-source-was-never-reached. — **unified-api-contracts**
- [x] ✅ P0. **KEYSTONE LIVE** — DONE utl@39f8ec85: record_empty gains `fetch_evidence: FetchEvidence|None`; SOURCE_RETURNED_ZERO without `.proves_honest_absence()` emits DP_UNPROVEN_HONEST_ABSENCE(CRITICAL)+raises UnprovenHonestAbsenceError (hard-raise, operator 2026-06-22). EXPECTED_* exempt. 15 test files + 2 internal callers threaded; QG green 117s. Gate `record_empty(reason=SOURCE_RETURNED_ZERO)` in `_writer_record.py`: require an accompanying
      `fetch_evidence` proving `http_status in 2xx AND response_received AND rows_in_response==0 AND error_signal==""`;
      otherwise raise `UnprovenHonestAbsenceError` (callsite hint, steers to `record_failed`). `EXPECTED_*` calendar
      reasons are exempt (no fetch attempted). — **unified-trading-library**
- [ ] [CODE] P0. Thread `fetch_evidence` from the adapter HTTP layer (the UAC `classify_venue_error()` site that already
      exists per-adapter) into the manifest writer, for all 5 AGs. Adapters that today call
      `record_empty(SOURCE_RETURNED_ZERO)` on an exception path are exactly the C1 bugs — they will now fail loudly at
      the writer and route to `record_failed`. — **market-tick-data-service, instruments-service**
- [x] ✅ P0. Unit gate tests DONE utl@39f8ec85 (test_record_empty_fetch_evidence_gate.py: None/signal/401/429/500/rows>0/not-received raise; EXPECTED_* exempt). Unit: a 401/429/timeout/exception path that previously stamped `SOURCE_RETURNED_ZERO` now raises
      `UnprovenHonestAbsenceError`; a genuine 200+empty passes. One test per disqualifying signal. —
      **unified-trading-library, market-tick-data-service**
- [ ] [SCRIPT] P0. **Daily empty re-probe** (`scripts/audit/reprobe_new_empty_confirmed.py`, e2e-testing → wired to MTDS
      QG primary-consumer): select rows that became `empty_confirmed` with `SOURCE_RETURNED_ZERO` **today** (per AG),
      re-hit the live source/endpoint for a sample, and cross-check against source docs/coverage oracle. Emit
      `EMPTY_REPROBE_DISAGREEMENT` (the source returned data → the empty was a bug) to `data-pipeline-alerts`.
      Scriptable for the re-fetch; **escalate the ambiguous verdicts to a planning-VM slot** (Phase 5). —
      **e2e-testing**
- [ ] [RATCHET] P1. QG ratchet (extends `fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md`): static
      check banning `record_empty(...SOURCE_RETURNED_ZERO...)` reachable from an `except`/error branch without
      `fetch_evidence`. Baseline-down counter. — **market-tick-data-service, instruments-service**

## Phase 2 — data-pipeline-alerts channel + streaming events + exit_code-aware fleet monitor (closes C4/C5; partial C7)

- [ ] [CODE] P1. Add a typed **data-pipeline event family** + `route_event` rule + `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`
      for the existing `data-pipeline-alerts` channel. Verbose to start. — **alerting-service**
- [ ] [CODE] P1. **Heartbeat emitter**: a running batch/live VM emits a periodic
      `PIPELINE_HEARTBEAT{vm, ag, data_type, rows_captured_cum, last_progress_at}` (reuse the durable-log substrate from
      `vm_launcher_durable_log_observability`). Silence > N min ⇒ stall alert. Closes the "idle/hung VM emits nothing"
      gap. — **unified-trading-library, deployment-service**
- [ ] [CODE] P1. **Exit_code-aware fleet monitor** (closes the C4 self-delete blind spot, per CLAUDE.md 2026-06-22
      rule): per VM, read the persisted GCS `run.log` terminal `exit_code` (survives self-delete) + cross-check manifest
      `captured` climbed; alert on `exit_code!=0 OR captured flat`. Reuse `backfill_vm_silent_worker_stall_watchdog`
      signal. — **deployment-service**
- [ ] [CODE] P1. Per-source **rate-limit / health event** `SOURCE_RATE_LIMITED{source, venue, http_429_count}` and
      `SOURCE_KEY_POOL_EXHAUSTED` (C5: TheGraph 9-key pool, Databento, etc.) → `data-pipeline-alerts`. —
      **market-tick-data-service**
- [ ] [CODE] P2. **Three meta-watchers** (the "is the watcher itself running" gap): (a) instrument-catalogue-not-running
      per AG (no catalogue artifact refreshed in 24h); (b) zombie-VM-watchdog-itself-down; (c) consolidator-not-running
      (extend existing `CONSOLIDATOR_DOWN` to a per-AG cron-alive check). All → `data-pipeline-alerts`. —
      **deployment-service**
- [ ] [UI] P2. **Streaming events pane** in deployment-ui that tails the live VM event stream (not just the alert
      ledger) per AG/VM. `[UI]` + `pw:L2 ✓` + regression spec required. Extend `deployment_ui_monitoring_pane`. —
      **deployment-ui**

## Phase 3 — Daily per-AG completion summary + once-daily manifest-hygiene-vs-GCS audit (closes C2/C3/C6/C7)

- [ ] [SCRIPT] P1. **Daily per-AG completion digest** → `data-pipeline-alerts`: reuse `derive_capture_status_rates()`
      per AG/day, **union across sources** where >1 source exists for the same data, split batch vs live; breakdown per
      venue/chain/data_type. Thin wrapper over deployment-api readers + `notify-slack.yml`. — **e2e-testing /
      deployment-service** (cron `0 7 * * *`)
- [ ] [SCRIPT] P1. **Hygiene orchestrator** (`scripts/audit/manifest_hygiene_daily.py`): runs read-only, parallel
      (workers=32 via `gcs_blob_ops`), per AG, composing the existing tools — phantom
      (`reconcile_phantom_manifest_rows_all.py --dry-run`), divergence (`detect_manifest_divergence.py`), canonical-form
      (`audit_canonical_form.py --probe-paths`), 4-pillar (`validate_shards_4pillar.py`). One consolidated RED/GREEN
      report. **Note the cost**: full 7.4M-row GCS existence walk ≈ many hours — use prefix-bulk-listing (list once per
      `(date,venue,data_type)`), and scope incrementally (changed-since-yesterday) for the daily run; full walk weekly.
      — **e2e-testing**
- [x] ✅ P1. **Path-canonicality validator** `is_canonical(path)` in UAC — DONE uac@6c27bfa0 (is_canonical + canonical_path_violations; rejects hyphen-day / glued VENUE-CHAIN / glued V{N} / out-of-set AG; round-trips builders). **Path-canonicality validator** `is_canonical(path)` in UAC (today `partition_paths.py` only BUILDs):
      parse a GCS path and assert it matches the canonical builder output for its AG/pipeline_mode/schema. Closes C3.
      Reused by the hygiene orchestrator AND the Phase 4 writer-side assert. — **unified-api-contracts**
- [ ] [SCRIPT] P1. **Reader/writer bucket-env parity check** (closes C6): assert every preflight READER resolves the
      same env-short bucket the WRITER uses, per AG. Static + live probe. — **market-tick-data-service**
- [ ] [SCRIPT] P2. Close the `audit_criteria_automation` honest-SKIPs: wire CF-10 (phantom) and CF-14 (catalogue ⊇
      present-set) from SKIP to real checks inside `cf_manifest_audit_all.py`. — **market-tick-data-service**
- [ ] [SCRIPT] P2. **v9-readiness gate** in the daily digest: surface `schema_version` distribution per AG (target
      100%==9, read actual rows not the constant) and alert on any AG <100%. Reuse `audit_canonical_form.py` CF-1. —
      **e2e-testing**

## Phase 4 — Writer-side path + state invariants (defence-in-depth, closes residual C3/C7)

- [ ] [CODE] P2. `record_captured`/`record_empty` assert the resolved GCS path `is_canonical()` (Phase 3 validator)
      before write — a non-canonical write fails loudly at the writer, not days later in an audit. —
      **unified-trading-library**
- [ ] [CODE] P2. Live==batch schema invariant assert at the live `record_captured` boundary (C7: `asset_group`
      kwarg-not-column class). — **unified-trading-library**

## Phase 5 — Scripted→LLM escalation hop (the planning-VM handoff)

- [ ] [DESIGN] P2. Define the handoff: deterministic scripts (Phases 1/3) produce **candidate lists** (suspicious
      empties, divergences, non-canonical spellings, reprobe disagreements) as `plans/audit/results/<slug>_<date>.csv`.
      Ambiguous verdicts — "is this `empty_confirmed` a real gap or a code bug?", "is this spelling a legacy straggler
      or an intentional new venue?" — escalate to a **planning-VM slot** via the standard audit→issue→plan flow (write a
      `plans/active/issues/<name>_<date>.md`, not chat). Wire the daily digest to auto-file the issue doc when the
      candidate list is non-empty. — **unified-trading-pm + planning-VM**

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

- **2026-06-22 T0 foundation (slot-0·human-planning, Opus 4.8)**: Phase-0 design shipped — SM secrets `DATA_PIPELINE_ALERTS_SLACK_*` (webhook smoke 200 ok), codex SSOT `data-pipeline-alerts.md` + `.registry.yaml` (~40 modes), plan @ PM `6c4f01b2b`/`a5942dec3`. Coordination note added: `data_completion_to_100_all_ag` does per-adapter C1 point-fixes → Phase-1 gate generalizes; citadel P11.19 owns VM-events panel.
- **Build order (rule 8, T0→leaves)**: Wave1 UAC (FetchEvidence VO + UnprovenHonestAbsenceError + DISQUALIFYING_FETCH_SIGNALS + DATA_PIPELINE_ALERT_RULES from registry + is_canonical(path)) → Wave2 UTL (DP_* events + record_empty FetchEvidence hard-raise gate + heartbeat primitive + tests) → Wave3 alerting-service (data_pipeline_slack notifier + data_pipeline_rules loader + subscriber + config) → Wave4 deployment-service/e2e (exit_code fleet monitor, heartbeat watcher, daily per-AG digest, hygiene orchestrator, empty re-probe, escalation hop) → Final per-AG aggregation prompts.
- Per-AG `fetch_evidence` threading in MTDS/IS adapters is the per-AG half → goes to the AG agents via the final prompts (not built cross-cutting here).
- **2026-06-22 Wave 1 (UAC T0) SHIPPED** `unified-api-contracts@6c27bfa0` — QG green (220s, exit 0), 59 new tests. Exports `FetchEvidence`/`FetchErrorSignal`(10 members: HTTP_NON_2XX,AUTH_401,AUTH_403,RATE_LIMITED_429,SERVER_5XX,TIMEOUT,CONNECT_ERROR,ADAPTER_EXCEPTION,MISSING_CREDENTIAL,SOURCE_UNREACHABLE)/`DISQUALIFYING_FETCH_SIGNALS`/`UnprovenHonestAbsenceError(callsite_hint, evidence)`/`is_canonical`/`canonical_path_violations`/`DATA_PIPELINE_ALERT_RULES`(38, parity-tested vs registry yaml)/`DataPipelineAlertRule`. Decision: DP_* events aren't `AlertCode` members → built parallel `DataPipelineAlertRule` (mirrors AlertRule shape) not reusing the AlertCode-validated AlertRule. `is_canonical(require_pipeline_mode=False)` default (bare builder output stays canonical; opt-in strict for hygiene walk).
- **2026-06-22 Wave 2 (UTL T0) SHIPPED** `unified-trading-library@39f8ec85` — QG green (117s). KEYSTONE gate live in `manifest_writer/_writer_record.py::record_empty` (+ `record_zero_rows`, `_core` stub, `manifest_writer_normalising`): `fetch_evidence` kw; SOURCE_RETURNED_ZERO hard-raises `UnprovenHonestAbsenceError` + emits `DP_UNPROVEN_HONEST_ABSENCE` unless `.proves_honest_absence()`. Heartbeat: `unified_trading_library.events.emit_pipeline_heartbeat(vm_name,asset_group,data_type,rows_captured_cum,source,extra)` → `log_event(PIPELINE_HEARTBEAT)`. 37 DP_* + PIPELINE_HEARTBEAT in `events.event_types`. **Blast-radius note (operator hard-raise choice)**: MTDS/IS adapters calling SOURCE_RETURNED_ZERO without evidence will now raise at runtime + their QG goes red until they thread `fetch_evidence` — that per-AG threading is the per-AG agents' job (final prompts), the cross-cutting gate is intentionally strict.
