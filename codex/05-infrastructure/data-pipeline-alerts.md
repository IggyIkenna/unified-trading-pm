# Data-Pipeline Alerts — SSOT (failure-mode registry + emit→route→escalate model)

> **Purpose.** A running batch/live VM, a watcher, or a daily audit should be _incapable_ of failing silently. This doc
> is the SSOT for **every way the data pipeline can go wrong** and how each surfaces in the `#data-pipeline-alerts`
> Slack channel. Modeled on the agent-orchestrator and CI/CD alert dynamics: **start verbose** (every failure mode
> emits), then **drive the alert count to zero** by fixing root causes — a persistent alert is a bug to close, not noise
> to mute. Companion plan: `plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md` (parent epic
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
                 ├─ incident gateway       # dedup / ack / re-nag / recovery-verify  (CRITICAL only)
                 └─ escalation             # auto-recover  ▸  file plans/active/issues/<slug>_<date>.md  ▸  page
```

- **Severity → routing** (mirror agent-orchestrator/CI): `INFO` = channel only; `WARN` = channel + dedup; `CRITICAL` =
  channel + PagerDuty/Telegram + incident gateway (ack SLA + re-nag + recovery-verify).
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

| ID           | Sev | Fires when                                                                                                                   | Detector                                                  | Escalation                             | Status  |
| ------------ | --- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------- | ------- |
| DP-FETCH-001 | 🔴  | `record_empty(SOURCE_RETURNED_ZERO)` without valid `FetchEvidence` (http 2xx + response_received + 0 rows + no error_signal) | [S] writer gate `UnprovenHonestAbsenceError` (hard-raise) | file issue + page if fleet-wide        | verbose |
| DP-FETCH-002 | 🔴  | adapter hit a disqualifying signal (401/403 auth) but did not `record_failed`                                                | [S] writer gate / `classify_venue_error`                  | file issue                             | verbose |
| DP-FETCH-003 | 🟠  | adapter hit 429 / rate-limit and fell through to empty                                                                       | [S] writer gate + DP-RATE cross-ref                       | auto-recover (backoff) then file issue | verbose |
| DP-FETCH-004 | 🔴  | adapter hit 5xx / timeout / connect-error → empty                                                                            | [S] writer gate                                           | file issue                             | verbose |
| DP-FETCH-005 | 🔴  | missing/unresolved credential (empty key) → 0 rows (e.g. `odds_api_key`, Databento WS key)                                   | [S] preflight key-resolve assert + writer gate            | page (BLOCKED-CREDENTIALS)             | verbose |
| DP-FETCH-006 | 🟠  | **daily re-probe** of today's new `empty_confirmed` cells: live source returned data ⇒ the empty was a bug                   | [S] re-fetch sample; [L] ambiguous verdict                | file issue → planning-VM slot          | verbose |
| DP-FETCH-007 | 🔴  | a VM's run ends with ≥X% of its cells `empty_confirmed` (the RED-ALERT shape: 96-100% empty)                                 | [S] post-run manifest scan                                | page                                   | verbose |
| DP-FETCH-008 | 🔴  | catalog-freshness assert always-False masking zero capture (defi `assert_defi_catalog_fresh`)                                | [S] preflight assert emits not just raises                | file issue                             | verbose |

### DP-COVERAGE — genesis / launch / coverage-oracle wrong (class C2)

| ID              | Sev | Fires when                                                                                              | Detector                                             | Escalation                       | Status  |
| --------------- | --- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------- | ------- |
| DP-COVERAGE-001 | 🟠  | manifest has `attempted_failed` for a (venue,date) **before** the UAC genesis/launch date               | [S] oracle-vs-manifest divergence                    | file issue                       | verbose |
| DP-COVERAGE-002 | 🟠  | data_type×chain×league×venue classified to the wrong asset_group (HL/ASTER defi-vs-cefi class)          | [S] UAC capability cross-check; [L] new-venue intent | file issue → planning-VM         | verbose |
| DP-COVERAGE-003 | 🔵  | a venue/league/bookmaker present in data has **no** UAC coverage map entry                              | [S] present-set ⊄ oracle                             | file issue                       | verbose |
| DP-COVERAGE-004 | 🟠  | `expected_unattempted` seeded in non-canonical grain (`PROTOCOL-CHAIN`/blank) so captures never convert | [S] enumerator grain check                           | auto-fix re-seed then file issue | verbose |

### DP-PATH — non-canonical GCS path / pipeline_mode / bucket (class C3)

| ID          | Sev | Fires when                                                                           | Detector                                 | Escalation               | Status  |
| ----------- | --- | ------------------------------------------------------------------------------------ | ---------------------------------------- | ------------------------ | ------- |
| DP-PATH-001 | 🔴  | resolved write path fails UAC `is_canonical(path)` (writer-side assert)              | [S] writer assert                        | block write + file issue | verbose |
| DP-PATH-002 | 🟠  | manifest row implies a non-canonical path on the daily hygiene walk                  | [S] `audit_canonical_form --probe-paths` | file issue               | verbose |
| DP-PATH-003 | 🟠  | `pipeline_mode` hardcoded `batch` on a live run / missing `pipeline_mode=` partition | [S] QG static + manifest scan            | file issue               | verbose |
| DP-PATH-004 | 🟠  | legacy `day-YYYY-MM-DD` hyphen / `VENUE-CHAIN` / glued-`V{N}` spelling               | [S] `no_malformed_by_date_paths` + audit | file issue               | verbose |
| DP-PATH-005 | 🔴  | handler writes to the wrong bucket (defi 9-handler class)                            | [S] writer bucket-resolve assert         | block + page             | verbose |

### DP-VM — VM lifecycle / stall / OOM / heartbeat (class C4, most frequent)

| ID        | Sev | Fires when                                                                                | Detector                          | Escalation                              | Status  |
| --------- | --- | ----------------------------------------------------------------------------------------- | --------------------------------- | --------------------------------------- | ------- |
| DP-VM-001 | 🔴  | VM `run.log` terminal `exit_code != 0` (incl. 137 OOM) — survives self-delete             | [S] exit_code-aware fleet monitor | page                                    | verbose |
| DP-VM-002 | 🔴  | VM gone/drained but manifest `captured` did **not** climb (self-delete masking 0-row run) | [S] fleet monitor cross-check     | page                                    | verbose |
| DP-VM-003 | 🟠  | no `PIPELINE_HEARTBEAT` / progress for > N min (silent stall)                             | [S] heartbeat watcher             | auto-kill + respawn then file issue     | verbose |
| DP-VM-004 | 🟠  | event-loop starvation (blocking GCS read on async loop) — no logs for > N min             | [S] heartbeat watcher             | file issue                              | verbose |
| DP-VM-005 | 🔵  | VM STARTED but no PROGRESS within first N min                                             | [S] launch verifier (T+10min)     | file issue                              | verbose |
| DP-VM-006 | 🔴  | GCS 429 hot-object thrash (per-VM shard / team_mapping rewrite storm)                     | [S] 429-rate event                | auto-recover (debounce) then file issue | verbose |

### DP-RATE — rate-limit / key-pool (class C5)

| ID          | Sev | Fires when                                                              | Detector                        | Escalation                    | Status  |
| ----------- | --- | ----------------------------------------------------------------------- | ------------------------------- | ----------------------------- | ------- |
| DP-RATE-001 | 🟠  | sustained 429s from a source/venue above threshold                      | [S] `SOURCE_RATE_LIMITED` event | auto-recover (backoff/rotate) | verbose |
| DP-RATE-002 | 🔴  | key pool exhausted (TheGraph 9-key, Databento, etc.) — stuck on one key | [S] `SOURCE_KEY_POOL_EXHAUSTED` | page (BLOCKED-CREDENTIALS)    | verbose |

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

| ID              | Sev | Fires when                                                                           | Detector                                                | Escalation                                         | Status  |
| --------------- | --- | ------------------------------------------------------------------------------------ | ------------------------------------------------------- | -------------------------------------------------- | ------- |
| DP-MANIFEST-001 | 🔴  | consolidator not running / stale `_index` while per-VM shards exist                  | [S] `assert_consolidator_healthy` (already alerts)      | auto-recover (re-merge) then page                  | active  |
| DP-MANIFEST-002 | 🟠  | schema_version distribution for an AG < 100% v9 (read actual rows, not the constant) | [S] `audit_canonical_form` CF-1                         | file issue                                         | verbose |
| DP-MANIFEST-003 | 🟠  | phantom rows: `captured` cell with no GCS parquet                                    | [S] `reconcile_phantom_manifest_rows_all --dry-run`     | file issue (false-positive-guard before `--apply`) | verbose |
| DP-MANIFEST-004 | 🟠  | divergence: UAC oracle expects data but 0 captured                                   | [S] `detect_manifest_divergence`; [L] gap-vs-oracle-bug | file issue → planning-VM                           | verbose |
| DP-MANIFEST-005 | 🟠  | 4-pillar shard validation fails (rowcount/NaN/schema/cluster)                        | [S] `validate_shards_4pillar`                           | file issue                                         | verbose |
| DP-CATALOG-001  | 🔴  | instrument catalogue for an AG not refreshed in 24h (no enumerator run)              | [S] catalogue-freshness watcher                         | page                                               | verbose |
| DP-WATCHER-001  | 🔴  | the zombie-VM watchdog itself is down (meta-watcher)                                 | [S] watchdog-liveness probe                             | page                                               | verbose |
| DP-WATCHER-002  | 🔴  | a scheduled audit/consolidator/digest cron did not fire on schedule                  | [S] cron-alive probe                                    | page                                               | verbose |

## Daily digests (also posted to the channel, INFO)

- **Per-AG completion digest** (`0 7 * * *` UTC): per AG, batch vs live, completion % per venue/chain/data_type, **union
  across sources** where >1 source covers the same data. Reuses
  `deployment-api/.../data_status/coverage_metrics.derive_capture_status_rates`.
- **Hygiene-vs-GCS RED/GREEN** (`0 8 * * *` UTC, parallel workers=32): composes phantom + divergence + canonical-form +
  4-pillar + v9-distribution into one report; full-corpus walk weekly, changed-since-yesterday daily.

## Anti-patterns (banned)

- Muting a persistent alert instead of fixing its root cause (the alert IS the work item — drive to zero).
- A watcher that infers "VM gone ⇒ success" (DP-VM-002 exists because self-delete masks OOM — check `exit_code`).
- A new silent-failure class fixed as a point-bug without an `append` to this registry (then it recurs unmonitored).
- Routing a code-fixable mechanical alert to a human when an auto-recover tier exists (mirror CI auto-recover).
