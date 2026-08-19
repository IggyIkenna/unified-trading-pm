---
doc_type: codex-ssot
title: Data-Pipeline Alerts — SSOT (failure-mode registry + emit→route→escalate model)
summary:
  SSOT for every way the data pipeline can fail and how each surfaces in the data-pipeline-alerts Slack channel — the
  DP-<CATEGORY>-<NNN> failure-mode registry (FETCH / COVERAGE / PATH / VM / RATE / ENV / ORDER / MANIFEST / WATCHER),
  the emit → route → escalate spine (auto-recover → file-issue → page), the self-heal actuator layer, and the
  watch-the-watchers out-of-band deadman.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-api, deployment-service, e2e-testing, strategy-service]
scope: [engineer, admin]
tags: [data-pipeline, monitoring, observability, self-healing, slack, escalation]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
created: 2026-06-22
authoritative_for:
  [data-pipeline failure-mode registry (DP-* alert IDs) + emit-route-escalate model + self-heal actuator layer]
referenced_by:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/archive/2026_08/alerting_service_escalation_ladder_centralization_2026_08_18.md,
    plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md,
  ]
owner:
last_reviewed: 2026-06-22
code_refs:
---

# Data-Pipeline Alerts — SSOT (failure-mode registry + emit→route→escalate model)

> **Purpose.** A running batch/live VM, a watcher, or a daily audit should be _incapable_ of failing silently. This doc
> is the SSOT for **every way the data pipeline can go wrong** and how each surfaces in the `#data-pipeline-alerts`
> Slack channel. Modeled on the agent-orchestrator and CI/CD alert dynamics: **start verbose** (every failure mode
> emits), then **drive the alert count to zero** by fixing root causes — a persistent alert is a bug to close, not noise
> to mute. Companion plan: `/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md` (parent epic
> `observability_master`).

## Channel + credentials

- **Slack channel**: `#data-pipeline-alerts` (App ID `A0BC4KY825B`, created 2026-06-22).
- **Secret Manager** (`central-element-323112`, mirrors the `AGENT_ORCHESTRATOR_SLACK_*` convention):
  `DATA_PIPELINE_ALERTS_SLACK_{APP_ID,CLIENT_ID,CLIENT_SECRET,SIGNING_SECRET,VERIFICATION_TOKEN,WEBHOOK}`. Outbound
  posting needs only `…_WEBHOOK`; the signing/verification secrets are for any future inbound Slack app.
- **Delivery**: SM-hot-reloaded webhook (like `alerting-uts-live-alerts-slack-webhook`), mirrored by a notifier
  `alerting_service/notifiers/data_pipeline_slack.py` parallel to `uts_live_alerts_slack.py`. CI/QG events keep their
  own `notify-slack.yml` carrier; runtime data-pipeline events route via the alerting-service router.

## Emit → route → escalate (follows the existing alerting-service spine — reuse, do not fork)

```
running VM / watcher / daily audit
  └─ log_event(<DP_EVENT>, …)            # UTL events; batch→EventSink(GCS), live→LiveEventSink(PubSub)
       └─ alert_subscriber               # alerting-service subscribes the topic
            └─ router.route_event()       # fnmatch rule → channels + severity   (rules/data_pipeline_rules.py)
                 ├─ data_pipeline_slack   # mirror to #data-pipeline-alerts  (verbose)
                 ├─ incident gateway       # dedup / ack / re-nag / recovery-verify  (execution/strategy incidents only — see caveat below)
                 └─ escalation             # auto-recover  ▸  file plans/active/issues/<slug>_<date>.md  ▸  page
```

> **Wiring caveat (found 2026-07-15, `plans/active/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`):** the
> "incident gateway" box (`IncidentStateMachine`/`RecoveryVerifier`/`gateway/dedup.py`) is reached ONLY via
> `route_legacy_alert()` → `route_incident()`, keyed on `service/component/problem_type/strategy_id/venue/instrument_id`
> — a scope tuple used for execution/strategy incidents, NOT the DP_\* family. `_route_data_pipeline_event` mirrors
> DP_\* events to Slack + fires PagerDuty/Telegram directly and returns, bypassing the gateway entirely. DP_\* CRITICAL
> events instead rely on `router.py`'s generic `AlertDeduplicator` (`ttl_seconds=60.0` default) plus a per-event
> cooldown map (`_RECURRING_ALERT_COOLDOWNS`, event → cooldown seconds, ≥ that event's detector cadence) for any event
> that opts in — e.g. `DP_RUN_MOSTLY_EMPTY` at 1800s. An event NOT in that map still only gets the 60s default dedup,
> which does not bridge a `*/15`-or-slower detector cadence — a re-scanned-every-tick CRITICAL alert not yet in the map
> will still repeat on every detector tick. Either wire DP_\* through the real incident gateway, or treat the cooldown
> map as the DP_\* family's de facto dedup layer and keep it current as new manifest-scan-derived CRITICAL alerts are
> added.

- **Severity → routing** (mirror agent-orchestrator/CI): `INFO` = channel only; `WARN` = channel + dedup; `CRITICAL` =
  channel + PagerDuty/Telegram, deduped via the cooldown-map mechanism above (not the incident gateway — see caveat).
- **Escalation tiers** (mirror CI-failure-watcher's auto-recover-vs-escalate):
  1. **auto-recover** — deterministic, in-band (e.g. consolidator restart, key-pool rotate, stale-shard re-merge).
  2. **file issue** — a non-empty deterministic candidate list auto-files `plans/active/issues/<slug>_<date>.md` and
     pings the orchestrator inbox (the standard audit→issue→plan flow). The **LLM-judgment** verdicts (Phase 5 of the
     plan) escalate to a **planning-VM slot** from here.
  3. **page operator** — protective/safety only (CRITICAL with no auto-recover scope).
- **Lifecycle of a failure mode** (the "million → zero" discipline): `verbose` (emits every occurrence) → `baselined`
  (count ratcheted, only-down, like the QG ratchets) → `zeroed` (root cause fixed; alert becomes a regression tripwire).
  The `status` column below tracks this per mode.

## The registry — every data-pipeline failure mode

IDs are stable (`DP-<CATEGORY>-<NNN>`). `Detector` marks **[S]** scriptable/deterministic vs **[L]** needs-LLM.
Severity: 🔴 CRITICAL / 🟠 WARN / 🔵 INFO. This is the canonical list; the machine-readable copy is
`data-pipeline-alerts.registry.yaml` (same dir) which the router rules + watchers load. **Append here as new
silent-failure classes surface** — this is the shared pool the per-AG IS/MTDS agents feed into.

### DP-FETCH — adapter fetch / honest-absence misclassification (failure class C1, keystone)

| ID           | Sev | Fires when                                                                                                                                                                                                                                                                                                                                    | Detector                                                   | Escalation                             | Status  |
| ------------ | --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------- | ------- |
| DP-FETCH-001 | 🔴  | `record_empty(SOURCE_RETURNED_ZERO)` without valid `FetchEvidence` (http 2xx + response_received + 0 rows + no error_signal)                                                                                                                                                                                                                  | [S] writer gate `UnprovenHonestAbsenceError` (hard-raise)  | file issue + page if fleet-wide        | verbose |
| DP-FETCH-002 | 🔴  | adapter hit a disqualifying signal (401/403 auth) but did not `record_failed`                                                                                                                                                                                                                                                                 | [S] writer gate / `classify_venue_error`                   | file issue                             | verbose |
| DP-FETCH-003 | 🟠  | adapter hit 429 / rate-limit and fell through to empty                                                                                                                                                                                                                                                                                        | [S] writer gate + DP-RATE cross-ref                        | auto-recover (backoff) then file issue | verbose |
| DP-FETCH-004 | 🔴  | adapter hit 5xx / timeout / connect-error → empty                                                                                                                                                                                                                                                                                             | [S] writer gate                                            | file issue                             | verbose |
| DP-FETCH-005 | 🔴  | missing/unresolved credential (empty key) → 0 rows (e.g. `odds_api_key`, Databento WS key)                                                                                                                                                                                                                                                    | [S] preflight key-resolve assert + writer gate             | page (BLOCKED-CREDENTIALS)             | verbose |
| DP-FETCH-006 | 🟠  | **daily re-probe** of today's new `empty_confirmed` cells: live source returned data ⇒ the empty was a bug                                                                                                                                                                                                                                    | [S] re-fetch sample; [L] ambiguous verdict                 | file issue → planning-VM slot          | verbose |
| DP-FETCH-007 | 🔴  | a VM's run ends with ≥X% of its cells `empty_confirmed` (the RED-ALERT shape: 96-100% empty)                                                                                                                                                                                                                                                  | [S] post-run manifest scan                                 | page                                   | active  |
| DP-FETCH-008 | 🔴  | catalog-freshness assert always-False masking zero capture (defi `assert_defi_catalog_fresh`)                                                                                                                                                                                                                                                 | [S] preflight assert emits not just raises                 | file issue                             | verbose |
| DP-FETCH-009 | 🔴  | `attempted_failed` cell high for a (asset_group, data_type): `abs>=500` or (count above a floor AND `ratio>=10%`) — a distinct ATTEMPTED_FAILED-ratio detector reusing the `DP_RUN_MOSTLY_EMPTY` event name (DP-FETCH-007 is the EMPTY_CONFIRMED-ratio variant; both emit the same event, `registry_id` distinguishes them in the alert body) | [S] `check_high_attempted_failed` (post-run manifest scan) | page                                   | active  |

### DP-COVERAGE — genesis / launch / coverage-oracle wrong (class C2)

| ID              | Sev | Fires when                                                                                              | Detector                                             | Escalation                       | Status  |
| --------------- | --- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------- | ------- |
| DP-COVERAGE-001 | 🟠  | manifest has `attempted_failed` for a (venue,date) **before** the UAC genesis/launch date               | [S] oracle-vs-manifest divergence                    | file issue                       | verbose |
| DP-COVERAGE-002 | 🟠  | data_type×chain×league×venue classified to the wrong asset_group (HL/ASTER defi-vs-cefi class)          | [S] UAC capability cross-check; [L] new-venue intent | file issue → planning-VM         | verbose |
| DP-COVERAGE-003 | 🔵  | a venue/league/bookmaker present in data has **no** UAC coverage map entry                              | [S] present-set ⊄ oracle                             | file issue                       | verbose |
| DP-COVERAGE-004 | 🟠  | `expected_unattempted` seeded in non-canonical grain (`PROTOCOL-CHAIN`/blank) so captures never convert | [S] enumerator grain check                           | auto-fix re-seed then file issue | verbose |

### DP-PATH — non-canonical GCS path / pipeline_mode / bucket (class C3)

| ID          | Sev | Fires when                                                                                                                                                                                                | Detector                                  | Escalation               | Status  |
| ----------- | --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------ | ------- |
| DP-PATH-001 | 🔴  | resolved write path fails UAC `is_canonical(path)` (writer-side assert)                                                                                                                                   | [S] writer assert                         | block write + file issue | verbose |
| DP-PATH-002 | 🟠  | manifest row implies a non-canonical path on the daily hygiene walk                                                                                                                                       | [S] `audit_canonical_form --probe-paths`  | file issue               | verbose |
| DP-PATH-003 | 🟠  | `pipeline_mode` hardcoded `batch` on a live run / missing `pipeline_mode=` partition                                                                                                                      | [S] QG static + manifest scan             | file issue               | verbose |
| DP-PATH-004 | 🟠  | legacy `day-YYYY-MM-DD` hyphen / `VENUE-CHAIN` / glued-`V{N}` spelling                                                                                                                                    | [S] `no_malformed_by_date_paths` + audit  | file issue               | verbose |
| DP-PATH-005 | 🔴  | handler writes to the wrong bucket (defi 9-handler class)                                                                                                                                                 | [S] writer bucket-resolve assert          | block + page             | verbose |
| DP-PATH-006 | 🔴  | IS universe bare ticker (e.g. `KALSHI KXMVE-26JAN`) not rebuilt to connector form `KALSHI:PREDICTION_MARKET:{ticker}` → WS "unknown instrument; skipping" → 0 capture (cefi/prediction live silent-empty) | [S] `live_universe_connector_key_rebuild` | file issue               | verbose |

### DP-VM — VM lifecycle / stall / OOM / heartbeat (class C4, most frequent)

| ID        | Sev | Fires when                                                                                                                                                                                                                                    | Detector                          | Escalation                                                             | Status  |
| --------- | --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------- | ------- |
| DP-VM-001 | 🔴  | VM `run.log` terminal `exit_code != 0` (incl. 137 OOM) — survives self-delete                                                                                                                                                                 | [S] exit_code-aware fleet monitor | OOM: auto-recover (resize-up relaunch) then file issue · non-OOM: page | active  |
| DP-VM-002 | 🔴  | VM gone/drained but manifest `captured` did **not** climb (self-delete masking 0-row run)                                                                                                                                                     | [S] fleet monitor cross-check     | page                                                                   | active  |
| DP-VM-003 | 🟠  | no `PIPELINE_HEARTBEAT` / progress for > N min (silent stall)                                                                                                                                                                                 | [S] heartbeat watcher             | auto-kill + respawn then file issue                                    | active  |
| DP-VM-004 | 🟠  | event-loop starvation (blocking GCS read on async loop) — no logs for > N min                                                                                                                                                                 | [S] heartbeat watcher             | file issue                                                             | active  |
| DP-VM-005 | 🔵  | VM STARTED but no PROGRESS within first N min                                                                                                                                                                                                 | [S] launch verifier (T+10min)     | file issue                                                             | verbose |
| DP-VM-006 | 🔴  | GCS 429 hot-object thrash (per-VM shard / team_mapping rewrite storm)                                                                                                                                                                         | [S] 429-rate event                | auto-recover (debounce) then file issue                                | verbose |
| DP-VM-007 | 🟠  | Cloud Run job running an image older than the latest Artifact Registry build for its service                                                                                                                                                  | [S] `stale_cloud_run_image_alert` | file issue                                                             | active  |
| DP-VM-008 | 🔵  | durable `PREEMPTED` marker present (GCE SPOT reclaim) — benign, routine                                                                                                                                                                       | [S] exit_code-aware fleet monitor | auto-recover (checkpoint-resume relaunch)                              | verbose |
| DP-VM-009 | 🔴  | a preempted VM's relaunch could NOT proceed (no launcher binding / budget exhausted / launcher guard refusal / launcher error / unresolvable tarball pin / non-monotonic force-run checkpoint) — the backfill would otherwise silently vanish | [S] `relaunch_preempted_vm`       | page                                                                   | verbose |
| DP-VM-010 | 🟠  | terminated VM has NO durable exit marker (`exit_code is None`) but manifest `captured` climbed — ambiguous between a genuine finish whose terminal write raced teardown and a premature kill with real partial progress                       | [S] exit_code-aware fleet monitor | auto-recover (checkpoint-resume relaunch) then file issue              | verbose |
| DP-VM-011 | 🔵  | resolved-bookend for `DP_VM_PREEMPTED` — the relaunch subprocess exited 0 and the preempted backfill is running again                                                                                                                         | [S] `relaunch_preempted_vm`       | file issue                                                             | verbose |

### DP-RATE — rate-limit / key-pool (class C5)

| ID          | Sev | Fires when                                                                                                                                                                                                  | Detector                                                                | Escalation                    | Status  |
| ----------- | --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------- | ------- |
| DP-RATE-001 | 🟠  | sustained 429s from a source/venue above threshold                                                                                                                                                          | [S] `SOURCE_RATE_LIMITED` event                                         | auto-recover (backoff/rotate) | verbose |
| DP-RATE-002 | 🔴  | key pool exhausted (TheGraph 9-key, Databento, etc.) — stuck on one key                                                                                                                                     | [S] `SOURCE_KEY_POOL_EXHAUSTED`                                         | page (BLOCKED-CREDENTIALS)    | verbose |
| DP-RATE-003 | 🟠  | sports REST adapter (api_football/SFI/transfermarkt/footystats) hit a 429 + slept to the minute boundary — surfaces a throttled backfill instead of a silent stall (the TM/FootyStats 6.5h-hang blind spot) | [S] `sports_adapter_429` (`BaseSportsReferenceAdapter._get_with_retry`) | auto-recover (backoff)        | verbose |

### DP-ENV — reader/writer bucket-env mismatch (class C6)

| ID         | Sev | Fires when                                                                                                                       | Detector                                             | Escalation                   | Status  |
| ---------- | --- | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ---------------------------- | ------- |
| DP-ENV-001 | 🔴  | preflight READER resolves a different (env-less vs env-short `-prd-`) bucket than the WRITER → stale read → false honest-absence | [S] reader/writer parity check (static + live probe) | file issue                   | verbose |
| DP-ENV-002 | 🟠  | consolidated-manifest staleness default too short for a daily-cadence catalog → falls back to blank-`data_type` per-VM shards    | [S] staleness-vs-cadence check                       | auto-fix env then file issue | verbose |

### DP-ORDER — DAG ordering / live==batch schema (class C7)

| ID           | Sev | Fires when                                                                                       | Detector                           | Escalation               | Status  |
| ------------ | --- | ------------------------------------------------------------------------------------------------ | ---------------------------------- | ------------------------ | ------- |
| DP-ORDER-001 | 🟠  | downstream (features) ran before upstream (fixtures/instruments) complete → derived rows missing | [S] DAG-readiness gate vs manifest | hold + file issue        | verbose |
| DP-ORDER-002 | 🔴  | live `record_captured` schema skew vs batch (`asset_group` kwarg-not-column class)               | [S] writer live==batch invariant   | block + file issue       | verbose |
| DP-ORDER-003 | 🟠  | NULL-vs-`""` dedup double-count in manifest aggregation                                          | [S] dedup check                    | auto-fix then file issue | verbose |

### DP-MANIFEST / DP-CATALOG / DP-WATCHER — infra meta (the "is the checker itself alive")

| ID              | Sev | Fires when                                                                                                                                                                                                                                                                                                                                                        | Detector                                                                 | Escalation                                         | Status  |
| --------------- | --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------- | ------- |
| DP-MANIFEST-001 | 🔴  | consolidator not running / stale `_index` while per-VM shards exist                                                                                                                                                                                                                                                                                               | [S] `assert_consolidator_healthy` (already alerts)                       | auto-recover (re-merge) then page                  | active  |
| DP-MANIFEST-002 | 🟠  | schema_version distribution for an AG < 100% v9 (read actual rows, not the constant)                                                                                                                                                                                                                                                                              | [S] `audit_canonical_form` CF-1                                          | file issue                                         | verbose |
| DP-MANIFEST-003 | 🟠  | phantom rows: `captured` cell with no GCS parquet                                                                                                                                                                                                                                                                                                                 | [S] `reconcile_phantom_manifest_rows_all --dry-run`                      | file issue (false-positive-guard before `--apply`) | verbose |
| DP-MANIFEST-004 | 🟠  | divergence: UAC oracle expects data but 0 captured                                                                                                                                                                                                                                                                                                                | [S] `detect_manifest_divergence`; [L] gap-vs-oracle-bug                  | file issue → planning-VM                           | verbose |
| DP-MANIFEST-005 | 🟠  | 4-pillar shard validation fails (rowcount/NaN/schema/cluster)                                                                                                                                                                                                                                                                                                     | [S] `validate_shards_4pillar`                                            | file issue                                         | verbose |
| DP-MANIFEST-006 | 🔴  | drilldown-correctness ε=0 reconciliation guard (§2.3): a sampled raw shard's real row_count != the manifest's own recorded row_count for the same captured cell — the coverage cockpit disagrees with GCS ground-truth. Reuses `DP_PHANTOM_ROWS` (`registry_id` in the alert details disambiguates from a true existence-phantom, per the DP-FETCH-009 precedent) | [S] `drilldown_reconciliation_guard` (bounded sample, not a corpus walk) | file issue                                         | verbose |
| DP-CATALOG-001  | 🔴  | instrument catalogue for an AG not refreshed in 24h (no enumerator run)                                                                                                                                                                                                                                                                                           | [S] catalogue-freshness watcher                                          | page                                               | active  |
| DP-CATALOG-002  | 🔴  | monotonic-guard rejected a catalogue promotion whose row count shrank vs. current canonical (previous good catalogue kept)                                                                                                                                                                                                                                        | [S] `promote_catalogue/evaluate_monotonic_guard`                         | page                                               | verbose |
| DP-WATCHER-001  | 🔴  | the zombie-VM watchdog itself is down (meta-watcher)                                                                                                                                                                                                                                                                                                              | [S] watchdog-liveness probe                                              | page                                               | active  |
| DP-WATCHER-002  | 🔴  | a scheduled audit/consolidator/digest cron did not fire on schedule                                                                                                                                                                                                                                                                                               | [S] cron-alive probe                                                     | page                                               | active  |
| DP-WATCHER-003  | 🔴  | `dp-fleet-monitor`'s own `run_lifecycle()` terminal-failure event (meta)                                                                                                                                                                                                                                                                                          | [S] `run_lifecycle(service_name="dp-fleet-monitor")`                     | page                                               | verbose |
| DP-WATCHER-004  | 🔴  | a non-`-legacy-` manifest-consolidator Cloud Scheduler job is PAUSED with no live maintenance window covering it (accidental pause)                                                                                                                                                                                                                               | [S] `check_consolidator_scheduler_paused`                                | page                                               | active  |
| DP-WATCHER-005  | 🔴  | an OOM-killed consolidator — reaches `CONSOLIDATOR_DOWN` (DP-MANIFEST-001's condition) by a different route than DP-WATCHER-004 (OOM vs staleness); same dependent action                                                                                                                                                                                         | [S] `meta_watchers` OOM classification                                   | auto-recover (re-merge) then page                  | active  |
| DP-WATCHER-006  | 🔴  | generic per-execution Cloud Run Job failure, fired across the whole job registry — registered so the identity resolves to an explicit no-op rather than an unregistered-id silent drop; no per-job dependent action exists yet                                                                                                                                    | [S] fleet-wide Cloud Run Job execution-failure sweep                     | page                                               | active  |
| DP-VM-012       | 🔴  | a Cloud Run Service's `terminal_condition` entered `CONDITION_FAILED` — the service is not serving                                                                                                                                                                                                                                                                | [S] Cloud Run Service condition probe                                    | page                                               | active  |

### DP-LIVE — live-VM data-stream blindspots (`deployment_service/data_pipeline_monitors/live_stream_watcher.py`, `producer_lifecycle.py`)

| ID          | Sev | Fires when                                                                                                                                                                                                                                    | Detector                                                            | Escalation                                                                  | Status |
| ----------- | --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------ |
| DP-LIVE-001 | 🔴  | "VM alive, data dead" — a live shard has stopped ATTEMPTING entirely (no fresh `attempted_at`); shares DP-WATCHER-002's shape (never even attempted, downstream would read absence as honest)                                                 | [S] `live_stream_watcher.check_live_capture_productivity`           | page                                                                        | active |
| DP-LIVE-002 | 🔴  | "manifest captured, GCS empty" sink mismatch — manifest asserts data that does not exist on GCS; DP-LIVE-001 misses this because `attempted_at` stays fresh even though the sink silently discarded rows                                      | [S] `live_stream_watcher` GCS-vs-manifest cross-check               | page                                                                        | active |
| DP-LIVE-003 | 🔴  | a registered `LONG_LIVED_LIVE` producer prefix has ZERO running instances — nothing is producing (the condition that hid a 5-week CME capture gap, deleted 2026-06-30, found 2026-08-09)                                                      | [S] `producer_lifecycle` must-be-running set vs live instance count | page                                                                        | active |
| DP-LIVE-004 | 🟠  | "shard alive, zero recent captures" productivity gap, ALL asset groups — a live shard is still actively attempting but never captured a row within its staleness budget; a productivity gap, not a correctness one (nothing false is written) | [S] `live_stream_watcher.check_live_capture_productivity`           | auto-recover (visibility only — see 2026-08-17 dedup-defeat incident below) | active |

> **2026-08-15/16 registry-gap fix**: DP-WATCHER-005/006, DP-VM-012, DP-LIVE-001/002/003/004 were emitting live
> (`registry_id=` resolves in `unified_api_contracts.DP_FAILURE_MODE_ACTIONS`, per the "third anti-inertness class"
> note above) but were never transcribed into this table — this doc's own staleness note flagged the gap; this edit
> closes it. See `unified_api_contracts/canonical/crosscutting/_dependency_revocation_policies.py` for the full
> per-id revocation-policy rationale (each id's `DependentAction` + reasoning).
>
> **2026-08-17 incident, RESOLVED (`plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`,
> `plans/archive/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md`)**: two independent bugs
> stacked, both now fixed and live-confirmed. **Bug 1**: DP-LIVE-004 emits `details={"attempted_age_hours": ...}`, a
> value recomputed every sweep; this defeated `AlertDeduplicator`'s identity-hash dedup (the differing value changed
> the hash every sweep), making the registered 1800s `DP_CRON_DID_NOT_FIRE` cooldown a no-op for this detector
> specifically. Fixed (`alerting-service@cd60a3e595`): `attempted_age_hours` + a generic
> `*_age_hours/days/minutes/seconds` suffix added to `AlertDeduplicator._VOLATILE_DETAIL_KEYS`. **Bug 2** (why the
> storm persisted after Bug 1 shipped — the deploy chain was clean the whole time): `router._route_data_pipeline_event`
> routes on `dp_rule.severity` (the registry's STATIC CRITICAL for `DP_CRON_DID_NOT_FIRE`), not the emitted event's
> actual severity — so a `resolved=True` INFO bookend from `meta_watchers.reconcile_resolved()` still hit the
> CRITICAL-paging branch, and its `details` shape (`resolved`/`label`/`registry_id="DP-RESOLVED"`) is unrelated to a
> real fire's identity, so the 1800s dedup never caught it either: every detector flap produced a fresh, un-deduped
> CRITICAL page. Fixed (`alerting-service@166f291f44`): `_route_data_pipeline_event` now forces `severity =
AlertSeverity.INFO` whenever `details.get("resolved")` is truthy, before the CRITICAL-page branch — mirrors the
> existing STATIC BACKLOG downgrade in the same function. **Live-confirmed** (2026-08-17 09:36Z): deploy chain
> reverified clean (fix content on `origin/main`, Cloud Build `d6ab1c6f`, live revision
> `dp-alerting-subscriber-00105-bkq` @ 100% traffic running that exact image digest); the sampled identity
> (`mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES) fired at 09:06Z, was correctly suppressed at the
> 09:20/21Z sweep, and fired again exactly 30min later at 09:36Z — the 1800s cooldown is now genuinely respected.
> A known, separate, lower-priority quirk was found but deliberately left unfixed (see the archived issue doc): a
> CRITICAL DP_\* event runs through two independent `AlertDeduplicator.is_duplicate()` calls with different hashes,
> causing a double `ALERT_ROUTED`/`ALERT_SENT` per genuine fire — each state is still correctly TTL'd on its own key,
> so this does not reproduce the cooldown-defeat symptom, just a cosmetic double-log.
>
> **2026-08-18 REGRESSION, OPEN — new root cause, not either bug above**
> (`plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md`): the 09:36Z-confirmed-good
> identity was re-sampled ~16.5h later and found firing every 15-17min again, alongside DP-LIVE-003 and DP-WATCHER-002
> (same event name, different detectors) — a fleet-wide symptom, not one detector's `details` shape. Root cause:
> `AlertDeduplicator._seen` is a plain in-process dict; `dp-alerting-subscriber` (`minScale=1, maxScale=1`, ruling out
> horizontal fragmentation) still redeploys far more often than the 1800s cooldown window (5 revisions in 3.25h
> observed, one gap only 17min) — every redeploy is a fresh process that silently wipes `_seen`, defeating every
> `_RECURRING_ALERT_COOLDOWNS` entry fleet-wide, not just `DP_CRON_DID_NOT_FIRE`. Recommended fix: GCS-persist the
> `_RECURRING_ALERT_COOLDOWNS` subset of dedup state, mirroring `RenagTracker` (`deployment_service.data_pipeline_
monitors.renag_tracker`) — not yet implemented, see the issue doc. Source-side defense-in-depth shipped for
> DP-LIVE-003 (`deployment-service@9abb2d20e4`, `RenagTracker`/`apply_cooldown` wired into
> `missing_live_producer_watcher`); DP-LIVE-004/DP-WATCHER-002 already have source-side renag_tracker wiring, so their
> repeat-firing depends entirely on the alerting-service fix landing.

### DP-DIGEST — routine INFO telemetry (never the incident path)

| ID            | Sev | Fires when                                      | Detector                                             | Escalation | Status  |
| ------------- | --- | ----------------------------------------------- | ---------------------------------------------------- | ---------- | ------- |
| DP-DIGEST-001 | ⚪  | daily per-AG completion digest                  | [S] `daily_completion_digest`                        | file issue | verbose |
| DP-DIGEST-002 | ⚪  | daily manifest-hygiene-vs-GCS RED/GREEN summary | [S] `manifest_hygiene_orchestrator`                  | file issue | verbose |
| DP-DIGEST-003 | ⚪  | routine `dp-fleet-monitor` sweep start          | [S] `run_lifecycle(service_name="dp-fleet-monitor")` | file issue | verbose |
| DP-DIGEST-004 | ⚪  | routine `dp-fleet-monitor` sweep completion     | [S] `run_lifecycle(service_name="dp-fleet-monitor")` | file issue | verbose |

> **2026-07-27 fix**: DP-DIGEST-003/004 (`DP_FLEET_MONITOR_RUN_STARTED`/`_COMPLETED`) and DP-WATCHER-003
> (`DP_FLEET_MONITOR_RUN_FAILED`) were previously UNREGISTERED in `DATA_PIPELINE_ALERT_RULES` even though
> `deployment-service`'s `dp-fleet-monitor` CLI (`data_pipeline_monitors/cli.py`) already emitted them via
> `run_lifecycle(service_name="dp-fleet-monitor")`. An unregistered DP\_\* event misses the router's exact-match
> `data_pipeline_rule_for()` short-circuit and falls through to the generic catch-all rule (`LIVE_ALERT_RULES`
> `event_pattern="*"`), which pages `#uts-live-alerts` (the incident channel) instead of mirroring to
> `#data-pipeline-alerts` — every routine fleet-monitor sweep was silently paging the wrong channel, and a genuine
> fleet-monitor crash (`_RUN_FAILED`) wasn't triggering an incident page at all.

> **2026-07-31 fix**: `DP_CONSOLIDATOR_SCHEDULER_PAUSED` (`consolidator_scheduler_watcher.py`) was emitting with
> `registry_id="DP-WATCHER-003"` — the id DP-WATCHER-003 above already owns for the DISTINCT
> `DP_FLEET_MONITOR_RUN_FAILED` event. Same failure class as the 2026-07-27 fix note above: the collision meant
> `DP_CONSOLIDATOR_SCHEDULER_PAUSED` had no exact-match `DATA_PIPELINE_ALERT_RULES` entry of its own, risking the
> generic-catch-all fallthrough. Assigned its own id, DP-WATCHER-004 (table row above).

> **Known gap, OPEN (found 2026-07-31)**: DP-WATCHER-004 detects an accidental pause, but nothing detects the
> INVERSE — a plan-tracked, INTENTIONAL pause (e.g. a backfill's own pause/apply/resume sequence) getting silently
> RESUMED before its owning plan's own resume step. A triage agent responding to a DP-WATCHER-004 page has no
> automated signal distinguishing "genuinely accidental, safe to resume" from "deliberately paused by an in-flight
> plan, resuming this races it" beyond manually finding the owning plan doc — **confirmed recurred twice in one day
> (2026-07-31)**: the prediction and tradfi manifest-consolidator crons were both paused as part of
> `/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s tracked pause/apply/resume sequence (raw
> `gcloud`, not the sanctioned `scheduler_maintenance` CLI, so no maintenance window was registered), and in the
> tradfi case a triage agent actually RESUMED the cron directly before finding the owning plan — a mistake
> self-corrected ~3 minutes later with zero consolidator ticks having fired in between (verified via the bucket's
> `consolidator_run_at` custom field staying pinned across the window), so no data-correctness harm landed this time
> — but the near-miss is real: a slower catch, or a busier consolidator tick, would have raced the backfill's own
> snapshot/pause invariant. The fix applied both times was reactive (retroactively register a maintenance window)
> plus a source-side retrofit (`market-tick-data-service@99b3c953` — the plan's OWN pause action now calls
> `pause_for_maintenance()` at pause time, not only at resume time) — but no STANDING detector exists that would page
> if a plan-tracked pause is resumed out of band by anyone/anything else. **Needed detector class**: alert when a
> `MaintenanceWindow`-covered scheduler job transitions PAUSED→ENABLED before the window's own `locked_by` plan
> releases it. Full incidents:
> `/plans/archive/issues/dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md`,
> `/plans/archive/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md`.

## Self-heal actuator layer (Layer-0 recovery — `auto_recover` tier)

An `auto_recover` escalation does not just label — it dispatches a real actuator. The map is
`deployment_service.data_pipeline_monitors.escalation._DP_RECOVERY_ACTIONS` (`event → actuator`):

| Event (DP\_\*)                  | Actuator (`deployment-service/scripts/recovery/`) | Bound                             |
| ------------------------------- | ------------------------------------------------- | --------------------------------- |
| `DP_MANIFEST_CONSOLIDATOR_DOWN` | `relaunch_consolidator.py`                        | idempotent; re-execs the Run job  |
| `DP_VM_EXIT_NONZERO` (137 OOM)  | `relaunch_backfill_vm.py` (resize-up on OOM)      | ≤2 / (vm-prefix, day)             |
| `DP_VM_STALL` / hung            | `relaunch_stalled_vm.py`                          | ≤2 / (vm-prefix, day); idempotent |

The actuator resolves **which launcher** to re-run from `data_pipeline_monitors/launcher_registry.py` —
`resolve_launcher_for_vm(vm_name)` does a **longest-prefix** match over `LAUNCHER_FOR_VM_PREFIX` (**243 VM prefixes**
measured 2026-08-14, correcting a stale "~189" — 178 → a `deployment-service/scripts/vm/launch-*.sh` (104 distinct
scripts, 102 confirmed drain-capable per the revocation census below), 65 → `None` + a typed reason so an unrecoverable
prefix is explicit, not a silent miss). A prefix with no entry fails the guard test (every launchable VM-prefix must map
or be explicitly `None`). Never fire-and-forget — the actuator verifies STARTED at T+60s (the no-fire-and-forget rule).

> **PACKAGING — load-safe lazy import (2026-06-23 incident + fix; HARD RULE):** the actuator classes live in the
> top-level `deployment-service/scripts/recovery/` dir, which is **NOT in the installed `deployment_service` wheel** —
> the deployment-api Cloud Run image (where the monitors run) installs the package then DROPS the source, and
> `scripts/vm/` launchers are absent too. A **module-level** `from scripts.recovery… import` in `escalation.py`
> therefore crashed `data_pipeline_monitors/__init__.py` at load → **every monitor job (and the deadman) died at
> import** (caught 2026-06-23 by EXECUTING a job — a digest-only "deploy check" had missed it). Fix: `escalation.py`
> capability-checks
> `_ACTUATORS_AVAILABLE = importlib.util.find_spec("scripts.recovery.relaunch_consolidator") is not None` at load (a
> probe, not a try/except fallback) and loads the actuator via `importlib.import_module(...)` **inside** the dispatch fn
> (a dynamic call, not an `import` statement — passes the no-imports-inside-functions gate AND ruff). When the actuators
> are absent the `auto_recover` tier returns `status=UNAVAILABLE` → **degrades to `file_issue`, never a crash**.
>
> **GAP CLOSED (was "OPEN GAP (P1)" here until 2026-08-12) — `deployment-api@a01e2a5b`.** The runtime host is
> **deployment-api** (its Dockerfile vendors `deployment-service` at build time via `_deployment-service/` +
> `--no-deps`; `data_pipeline_fleet_monitor_scheduler.tf` pins `data_pipeline_monitor_image = ".../deployment-api"`) —
> NOT `deployment-service`'s own image, which always shipped the whole `scripts/` dir and was never the gap. Two
> half-fixes were needed: `scripts.recovery` (the import-probe half) landed earlier via
> `heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md`, but that fix COPYed a SINGLE file from
> `scripts/vm/`, so `RelaunchBackfillVm`/`RelaunchStalledVm` — which subprocess-exec `scripts/vm/launch-*.sh` at
> ACTUATION time, not import time — stayed dead even after `_ACTUATORS_AVAILABLE` went green: every real relaunch hit an
> internal `FileNotFoundError`, was caught, and degraded to `file_issue`, so it never crashed and never actually
> relaunched. Fixed by COPYing the whole `scripts/vm/` directory. Regression guard:
> `deployment-api/tests/unit/test_dockerfile_zombie_watchdog_packaging.py` asserts the COPY source is the directory
> root, not a filename. Residual tail tracked in
> `/plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`.
>
> **REGRESSION (2026-07-13, fixed `deployment-service@b3826fea`) — `find_spec()` on a DOTTED name is itself a raising
> call.** Same packaging class, new mechanism: `data_pipeline_monitors/cli.py::_zombie_watchdog` probed
> `importlib.util.find_spec("scripts.vm.vm_zombie_watchdog")` **outside** its `try/except`, assuming it returns `None`
> when unavailable. But `find_spec` **imports the parent package** to resolve a dotted name — so when the image has
> `scripts` importable but `scripts.vm` absent from the wheel, it **RAISES**
> `ModuleNotFoundError: No module named 'scripts.vm'` (it does NOT return `None`). The uncaught raise crashed EVERY
> exit-code/heartbeat/meta fleet sweep the instant it processed a terminated/stalled VM (via `_umbrella_for_vm` /
> `_kill_stalled_vm`) → no sentinel written → the out-of-band deadman paged every 15 min for ~8h (triggered when the
> `sports-v9-migration` VMs terminated `exit_code=2`). It never reproduced locally because `scripts.vm` IS on disk in
> the repo — only the packaged image lacks it. Fix: wrap the `find_spec` probe so a missing parent degrades to
> unavailable (`return None`), matching the documented intent. **Rule: a `find_spec()` probe on a dotted name must be
> `try/except`-guarded — checking its return value is not enough.**

When `auto_recover` is exhausted or N/A, the tier escalates: **`file_issue`** writes an _actionable_ plan-todo
(frontmatter `assigned_vm` + `parent_epic` + a `- [ ] [CODE] P1` naming the target repo) → `PlanRegenLoop` → backlog →
`AutoSpawn` picks up a fix agent; the **fast path** is a `repository_dispatch escalate-to-orchestrator`
(`wall_type=data_pipeline_failure`, auth via SM `GH_PAT`) — the same escalation spine CI-failure uses.
**`page_operator`** is the terminal tier (CRITICAL → Slack page).

> **RESOLVED (was "PARTIAL" 2026-06-23, corrected 2026-08-18 — the note had gone stale):** both actionable-frontmatter
> halves shipped long ago (deployment-service's `escalation.py::_write_issue_doc` + e2e-testing's
> `_dp_common.file_escalation_issue`, the latter landing `e2e-testing@821b73a` 2026-06-23). What was NOT resolved: the
> e2e-testing half filed its doc by writing + `git commit`/`push`-ing directly from inside its own ephemeral Cloud Run
> Job — no quality gates, no agent — which silently dropped a genuine RED finding three separate times in one week
> (git identity, frontmatter drift, same-day filename collision;
> `/plans/archive/issues/dp_audit_sibling_repo_cli_paths_and_escalation_commit_identity_2026_08_16.md`). See the new
> subsection immediately below for the fix in flight.

### Never raw-`git commit` a finding from an ephemeral/untracked runner (2026-08-18)

An emitter with no durable, already-git-managed checkout (a Cloud Run Job container, any ephemeral runner) must never
attempt to write + commit + push a PM issue doc itself — there is no real git identity, no quality gate, and no
recovery if the commit silently fails when the container exits. Two correct shapes, both already precedented:

- **A durable checkout IS available** (a real slot/agent session) — write the doc locally; normal slot git discipline
  (or `scripts/dev/safe-doc-push.sh` for a pure doc push) commits it. No explicit "commit this finding" step needed —
  it's just a file in an already-managed repo.
- **No durable checkout** — skip the local write entirely (mirrors
  `deployment_service.data_pipeline_monitors.escalation.route_finding`'s `no_pm_clone_on_disk` branch: it never even
  tries), emit the event with the full finding/candidate payload, and fire the same `repository_dispatch
escalate-to-orchestrator` (`wall_type=data_pipeline_failure`) fast path described above so a real dispatched worker
  files the doc from the payload instead. The dispatched `data_pipeline_failure` boot prompt
  (`unified-trading-pm/agents/data_pipeline_failure.md`) now handles both cases — a pre-filed slug, or a bare
  candidate payload it must file itself before diagnosing.

Full design + the incident history that motivated it: `/plans/active/dp_audit_escalation_agent_backed_filing_2026_08_18.md`.

## Alert-driven dependency revocation (2026-08-14, `alert_driven_dependency_revocation_2026_08_12.md`)

An alert firing changes nothing for a unit's DEPENDENTS by default — the self-heal actuators above
(`_DP_RECOVERY_ACTIONS`) act on the FAILING unit itself (restart, relaunch), not on the VMs/jobs reading its output.
Revocation closes that gap:
`unified_api_contracts.dependency_revocation.evaluate_revocation(alert_identity, upstream_entity=, drain_capable=)` is
the single policy SSOT (151 alert identities, measured 2026-08-16: 61 DP registry ids + 90 AlertCode members across
`DP_FAILURE_MODE_ACTIONS` + `ALERT_CODE_ACTIONS` — re-count before quoting, this has grown twice already since the 142
baseline), returning a `DependentAction`. The module itself now lives split across `_dependency_revocation_types.py`
(enums/records) + `_dependency_revocation_policies.py` (the two policy tables) + a thin `dependency_revocation.py`
re-export shim (file-size-ratchet split, 2026-08-16) — import from `dependency_revocation` or the top-level
`unified_api_contracts` namespace, never the two internal `_dependency_revocation_*` modules directly:

| Action         | Meaning                                                                               |
| -------------- | ------------------------------------------------------------------------------------- |
| `NONE`         | No dependent action.                                                                  |
| `SELF_RETRY`   | The failing unit retries; dependents unaffected.                                      |
| `SELF_RESTART` | The failing unit restarts; dependents unaffected.                                     |
| `SELF_DRAIN`   | The failing unit drains itself; no dependent-side action.                             |
| `DEPS_HOLD`    | Block admission — a held dependent never STARTS. Running work is left alone.          |
| `DEPS_DRAIN`   | Request a running dependent finish its current shard, flush, then exit.               |
| `FLEET_HALT`   | Pause the target's Cloud Scheduler jobs — admission-scoped, not per-VM.               |
| `KILL_SWITCH`  | Halts TRADING via the existing kill-switch bus — does not touch a data-pipeline unit. |

**Drain-only ruling (operator decision, 2026-08-12): `DependentAction` deliberately has no `DEPS_KILL`.** Revocation
never terminates a running unit — the strongest action is "finish your shard and exit cleanly." This removed the
per-prefix checkpoint-resume audit as a prerequisite: a drain-blind prefix (no `record_captured` checkpoint) simply
degrades `DEPS_DRAIN` to `DEPS_HOLD` (the evaluator clamps it, recording `clamped_from` on the outcome) rather than
being a blocking special case.

**Delivery is two independent paths, not one.**
`deployment_service.data_pipeline_monitors.revocation_actuator. RevocationActuator` is the PUSH path — it consults the
evaluator and writes a marker (`vm-logs/{target}/ DRAIN_REQUESTED.json` or `vm-census/admission-hold/{target}.json`); it
carries no policy of its own (the anti-drift test `test_actuator_verdict_matches_the_evaluator_for_every_alert` iterates
every identity in the current population to prove it). `deployment_service.data_pipeline_monitors.revocation_gate` is the fail-closed BACKSTOP
— a running VM's heartbeat polls `drain_requested(target)` every tick
(`unified_trading_library.lifecycle.HeartbeatDaemon(drain_check=...)`), and a launcher preflight / Cloud Run entrypoint
calls `admission_blocked(target)` before starting work. A revocation survives even if the actuator never runs, dies
mid-sweep, or is never scheduled.

**Where it fires — record this, and check it still holds.** `escalation.route_finding()` calls `actuate()` for EVERY
finding, independent of tier: a `DEPS_DRAIN` applies whether the finding is `auto_recover`, `file_issue` or
`page_operator`. The close half is `meta_watchers.reconcile_resolved()`, which calls `release()` once an alert stops
re-firing. Both call sites are asserted by AST guards (`test_actuate_has_a_production_caller`,
`test_release_has_a_production_caller`), because this mechanism shipped across SIX green phases with **no production
caller at all** — every component complete, tested, and unreachable, which checkbox-level completeness could not see.
The guards exist so that state fails the gate instead of passing review.

Two constraints discovered the hard way, which must not be undone. The actuator takes its FLEET_HALT visibility as an
**injected callable**: importing `escalation` for `PipelineFinding` was the single edge that stopped `escalation` from
importing back, and that edge is why the mechanism sat uncalled. And the announcement emits `log_event` **directly**,
never `meta_watchers.emit_finding` — that calls `route_finding`, and the announcement runs INSIDE `route_finding`, so
routing it through would re-enter the escalation hop and re-run revocation against the announcement itself.

**Every drain flushes through the UTL drain registry first**
(`unified_trading_library.lifecycle.drain_registry. drain_all()`) — see the flush-contract convention in
`/codex/06-coding-standards/README.md` and the full contract in `/codex/05-infrastructure/spot-vms-for-backfill.md` §
"The graceful-flush contract". A drained partial shard is recorded as bytes written, never `captured` — the resume
re-attempts it.

**Retry attempt counts are a registry, not a convention** — `unified_api_contracts.RETRY_BUDGETS` (Phase 3), replacing
the "3 attempts" prose that used to live only in `/codex/04-architecture/autonomous-recovery-matrix.md`. See the
coding-standards pointer above for the batch-vs-live scope distinction.

| ID                | Sev | Fires when                                                                                          | Detector                                   | Escalation                                                                 | Status |
| ----------------- | --- | --------------------------------------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------- | ------ |
| DP-REVOCATION-001 | 🔵  | `RevocationActuator` delivers `FLEET_HALT` — Cloud Scheduler jobs paused for a target's asset group | [S] `RevocationActuator._pause_schedulers` | auto-recover (visibility only, never pages — the actuator IS the recovery) | active |

**Known gap, CLOSED 2026-08-17**: a `FLEET_HALT` pause previously registered no `MaintenanceWindow`, so `DP-WATCHER-004`
(above) could treat it as an ACCIDENTAL pause rather than a deliberate one. Fixed via
`/plans/archive/2026_08/infra_satellite_ao_dispatch_batch18_2026_08_16.md` item 2 (`deployment-service@ae49548487`):
both prod call sites (`escalation.py`'s `_apply_revocation` and `meta_watchers.py`'s release bookend) now pass the
`consolidator_bucket_resolver`, so `_register_maintenance_windows()` registers a `pause_for_maintenance()` window
(surface-scoped-per-target, `ttl_minutes=1440`) before every FLEET_HALT pause. Suppression is live.

**A third anti-inertness class, found live 2026-08-15/16: an identity that is EMITTED but never REGISTERED.** The
"built but not called" failure mode above (actuator with no caller) and "no dependent target resolves" (the
self-scoped `asset_group`-only targeting fix) both have AST guards. This third shape — a `registry_id=` literal an
emitter passes to `emit_finding()` that `evaluate_revocation()` doesn't recognize — silently raises
`UnknownAlertIdentityError`, is caught by `_apply_revocation`, logged as a `WARNING`, and dropped; the revocation
layer never sees it. Measured 2026-08-15: 7 already-live identities (`DP-WATCHER-005/006`, `DP-VM-012`,
`DP-LIVE-001/002/003/004`) had been emitting into this gap, 56 rejections in one 2h window alone. Now closed by TWO
layers: (1) the 7 (+ `DP-VM-013`, caught the next day) are registered in `DP_FAILURE_MODE_ACTIONS`; (2)
`deployment-service/tests/unit/test_registry_id_closed_set.py` is a standing two-arm CI guard — arm 1 AST-walks every
`registry_id=` literal in `data_pipeline_monitors/` and asserts it resolves; arm 2 asserts no module talks to UTL's
bare `log_event()` without also reaching `route_finding()`/`emit_finding()` somewhere in the same file (the shape of
the ORIGINAL `DP-MANIFEST-001` bug, before this session's fix — a bare `log_event()` call has no `registry_id=`
literal for arm 1 to see at all). This guard already caught `DP-VM-013` live, on its first run, before it shipped.

**GAP CLOSED 2026-08-17**: the 8 ids named above (DP-WATCHER-005/006, DP-VM-012, DP-LIVE-001/002/003/004, DP-VM-013)
are now transcribed into this file's table above and into `data-pipeline-alerts.registry.yaml` (same dir) — closed by
the `data_pipeline_alerts_reconciler` 6-hourly sweep. `DP_FAILURE_MODE_ACTIONS`
(`unified_api_contracts/canonical/crosscutting/_dependency_revocation_policies.py`) remains the code-level SSOT for
the per-id `DependentAction` policy itself; this doc's table is the human-readable failure-mode registry. Re-run
`test_registry_id_closed_set.py` (deployment-service) after adding any NEW `registry_id=` literal to catch the next
drift before it accumulates.

## Watching the watchers — meta-monitoring coverage + the KNOWN SPOF (2026-06-23)

The monitoring watches the **data pipeline** AND parts of **itself**: `DP-CATALOG-001` (enumerator stale > 24h),
`DP-WATCHER-001` (`meta_watchers.check_zombie_watchdog_alive` — the zombie-watchdog's GCS census blob fresh < 30 min →
CRITICAL/page), `DP-WATCHER-002` (`check_cron_fired` — per-AG `_index/availability_index.parquet` fresh < 180 min, a
proxy for the consolidator firing). So the consolidator + the zombie-watchdog + the catalogue enumerator each have a
dead-man's-switch above them.

> **SPOF CLOSED (code + terraform shipped 2026-06-23; `tofu apply` operator-gated):** two layers now watch the watchers
> themselves.
>
> **Layer 1 — cron-watches-cron (in-band, no creds).** Each fleet-monitor sweep (`exit-code` / `heartbeat` / `meta`)
> writes a `vm-census/<mode>-last-run.json` sentinel at end-of-sweep (`_gcs.write_monitor_last_run`, UTC ts + ok +
> per-sweep counts). The meta sweep runs `meta_watchers.check_monitor_crons_fired` — a `FreshnessTarget` per sentinel
> (`monitor_cron_targets`; budget = **2× cadence**, so 10 min for the `*/5` exit-code/heartbeat, 30 min for the `*/15`
> meta) — and a stale/absent sentinel emits **`DP_CRON_DID_NOT_FIRE` (DP-WATCHER-002, CRITICAL/page)**. The meta sweep
> CANNOT detect its OWN death this way (it must be running to probe its own sentinel) — that is Layer 2's job.
>
> **Layer 2 — out-of-band dead-man's-switch (the top-of-chain watcher).**
> `deployment_service.data_pipeline_monitors.deadman_poster` runs as its OWN Cloud Run job `uts-prod-monitoring-deadman`
> (`monitoring_deadman_scheduler.tf`, `*/15`, `retry_count=2`). Each tick it (a) reads every monitor sentinel's
> freshness (same `monitor_cron_targets`), (b) reads `lifecycle-events-sub` `oldest_unacked_message_age` via the Cloud
> Monitoring API (>30 min ⇒ the alerting subscriber / Slack relay is down — events piling up), and (c) on ANY staleness
> posts **DIRECTLY** to a SEPARATE Slack webhook (SM `MONITORING_DEADMAN_SLACK_WEBHOOK`, app `monitoring-deadman`). It
> is **deliberately independent** — it does NOT import the alerting-service / PubSub publish / `log_event` / the
> `#data-pipeline-alerts` webhook, so the same failure can't swallow its own death-alert (a namespace-level unit test
> enforces this).
>
> **Terminal bedrock.** A `google_monitoring_alert_policy` on the deadman job's OWN execution-failure → a
> `google_monitoring_notification_channel` of type **email** (`iggy2london@gmail.com`) — a deliberately DIFFERENT
> mechanism from Slack = true defense-in-depth (a native-Slack channel needs a one-time interactive OAuth that can't be
> provisioned non-interactively; `# TODO(operator): optionally swap to native Slack`). The fleet-monitor scheduler jobs
> also gained `retry_count=2` so a transient invocation failure never drops a tick. SSOT:
> `/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md` § "Watch-the-watchers SPOF".

**Fleet-monitor job memory sizing (live as of 2026-08-14)**: `uts-prod-dp-exit-code-monitor` 16Gi/4cpu/1800s,
`uts-prod-dp-heartbeat-watcher` 16Gi/4cpu/900s, `uts-prod-dp-meta-watchers` 32Gi/8cpu/900s
(`terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`, deployment-service repo) — each already bumped once or twice
from an original smaller ceiling as the fleet/manifest corpus grew. **Confirmed OOM root-cause class (2026-08-14,
`deployment-service@f425eb12b3`)**: `meta_watchers`' `check_high_attempted_failed` read the FULL unfiltered
`capture_status` row set via `pandas.DataFrame.to_pandas()` before filtering — `.to_pandas()` materializes every
projected column as individual Python objects regardless of relevance, so a checker that only ever consumes 2 of 4
canonical `capture_status` values (`captured`/`attempted_failed`; `expected_unattempted`/`empty_confirmed` contribute
nothing) was paying full memory cost for the 75%+ of rows it never uses. Fix pattern: filter to the relevant
`capture_status` allow-list INSIDE pyarrow (`table.filter(...)`) or via a pandas `.isin()` mask immediately after read,
BEFORE any `.to_pandas()`/full-DataFrame conversion — never bump the Cloud Run memory ceiling as the first response to
an OOM on one of these jobs without first checking whether a checker is materializing rows it doesn't need. Full
incident: `/plans/archive/2026_08/issues/dp_meta_watchers_oom_at_32gi_2026_08_13.md`.

### Revocation cascade stays local to deployment-service (2026-08-18 ruling)

The escalation-ladder centralization work
(`/plans/archive/2026_08/alerting_service_escalation_ladder_centralization_2026_08_18.md`) moved the `FILE_ISSUE`/
`PAGE_OPERATOR` dispatch DECISION into alerting-service (its Phase 2-3), but `_apply_revocation()`/
`RevocationActuator` (`deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py`)
deliberately did NOT move with it — revocation stays fully in deployment-service, unmigrated, for the SAME
independence reason `AUTO_RECOVER` stays local under that plan's Option C. This mirrors the DP-WATCHER independence
ruling directly above (2026-06-23): "routing it back through the alerting spine it exists to backstop would
re-couple them." Revocation is the same shape of risk — a drain/hold decision that depends on alerting-service's
availability is a worse trade than the visibility it would gain — so it stays in the "fast, local, must-work-even-
if-alerting-service-is-down" tier, not the "already-can't-self-heal, judgment-shaped" tier the escalation ladder
targets. Revocation is not dark to alerting-service either way: `_fleet_halt_visibility()` already emits
`DP_REVOCATION_FLEET_HALT` via the same `log_event()` path every other `DP_*` finding uses, so alerting-service (and
Slack) has READ-ONLY visibility into every revocation action without owning any control over it. **Revisit
condition**: only once deployment-service's live-deployment surface genuinely splits into multiple independent
services should full migration be reconsidered — only then does a single deployment-service process stop being able
to see the whole dependency graph locally, which is what makes local revocation correct today.

## Daily digests (also posted to the channel, INFO)

- **Per-AG completion digest** (`0 7 * * *` UTC): per AG, batch vs live, completion % per venue/chain/data_type, **union
  across sources** where >1 source covers the same data. Reuses
  `deployment-api/.../data_status/coverage_metrics.derive_capture_status_rates`.
- **Hygiene-vs-GCS RED/GREEN** (`0 8 * * *` UTC, parallel workers=32): composes phantom + divergence + canonical-form +
  4-pillar + v9-distribution into one report; full-corpus walk weekly, changed-since-yesterday daily.
- **Empty re-probe + auto-flip** (`0 9 * * *` UTC): re-fetches today's new `SOURCE_RETURNED_ZERO` empties; on a
  `REPROBE_RETURNED_ROWS` verdict (a live re-fetch PROVED data exists) auto-flips the cell
  `empty_confirmed → attempted_failed` (cron arg `--reclassify-apply`) so the orchestrator re-captures it.
  Oracle-only/ambiguous verdicts are NEVER flipped (proof-gated). Closes the detect→prove→flip→re-capture self-healing
  loop.

## Runtime — the audit-cron runner image (IMAGE GAP closed 2026-06-22)

The three daily audits run as **Cloud Run jobs** (`deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`)
on a **dedicated runner image** `…/unified-trading-library/e2e-audit:latest` — built by `e2e-testing/Dockerfile` (FROM
the UTL base, `COPY . /app/e2e-testing`) + `e2e-testing/cloudbuild-e2e-audit.yaml` (build → `--smoke` each script →
push). **This is a SEPARATE cloudbuild from the repo's template-generated CI `cloudbuild.yaml`** —
`rollout-cloudbuild.py` manages only `cloudbuild.yaml`, so `cloudbuild-e2e-audit.yaml` is hand-maintained and won't be
clobbered. The image MUST contain `/app/e2e-testing/scripts/audit/*.py` (the prior gap: the MTDS image's `COPY . .` only
copied MTDS, so the audit jobs failed at the script PATH). `var.dp_audit_image` defaults to this image; rebuild it when
an audit script changes. **Verified 2026-06-22**: Cloud Build `286913a2` SUCCESS; in-image smoke = 7 audit scripts
present + UTL/UAC/pandas import.

## Anti-patterns (banned)

- Muting a persistent alert instead of fixing its root cause (the alert IS the work item — drive to zero).
- A watcher that infers "VM gone ⇒ success" (DP-VM-002 exists because self-delete masks OOM — check `exit_code`).
- Bumping a fleet-monitor job's Cloud Run memory ceiling as the first OOM response without checking whether a checker
  materializes (`.to_pandas()`/full-DataFrame read) rows it never consumes — see "Fleet-monitor job memory sizing"
  above.
- A new silent-failure class fixed as a point-bug without an `append` to this registry (then it recurs unmonitored).
- Routing a code-fixable mechanical alert to a human when an auto-recover tier exists (mirror CI auto-recover).
