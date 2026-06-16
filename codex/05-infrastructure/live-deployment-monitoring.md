---
scope: [engineer, admin]
title: Live Deployment Monitoring
status: stable
created: 2026-05-07
last_reviewed: 2026-05-12
authoritative_for:
  Per-archetype event cadence + heartbeat thresholds + cross-cloud event-stream parity expectations for live (non-batch)
  trading deployments. Defines the contract between a running VM/Cloud Run service and the unified-events-interface so
  silent stalls are visible within minutes.
referenced_by:
  - plans/active/master_to_live_defi_2026_05_23.md
related:
  - codex/05-infrastructure/vm-tarball-deployment.md
  - codex/05-infrastructure/launcher-script-ssot.md
  - codex/04-architecture/service-infrastructure-requirements.md
  - codex/02-data/honest-absence-downstream-handling.md
---

# Live Deployment Monitoring

> **Status refresh 2026-05-12** — promoted from `planned` stub to `stable` with body content lifted from existing
> VM-observability SSOTs (`vm-tarball-deployment.md` + `launcher-script-ssot.md` + the alerting / honest-absence rules
> in CLAUDE.md). Owners: alerting-service + governance.

## Purpose

SSOT for "what does a healthy live deployment look like in the event stream?" Codifies STARTED / progress / STOPPED /
FAILED cadence per archetype, heartbeat thresholds, the cross-cloud parity expectation (GCP and AWS both emit the same
events to the same downstream consumers via the unified-events-interface), and the correlated-validation contract that
prevents the 2026-05-05 silent-1440-NaN class of incident.

## Surfaces in scope

Every live deployment emits to **four** observability surfaces in lockstep. Operators rely on all four; a green signal
on any one alone is NOT sufficient.

1. **GCS event-stream** — per-correlation_id JSONL append at
   `gs://{pid}-events-{env}/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`. Cloud-agnostic via UTL
   `setup_events()` (GCP path; AWS S3 mirror under `s3://{aws_pid}-events-{env}/...`). Consumer: deployment-UI events
   tab (UEI archived per CLAUDE.md "System-First Architecture"); ad-hoc CLI consumer via UTL helpers.
2. **VM heartbeat daemon** — `deployment-service/deployment_service/vm/heartbeat_daemon.py` (forked at boot from
   `setup-data-pipeline-vm.sh`). Heartbeats every ~60s into the **deployment registry** at
   `gs://deployment-scripts-{pid}/deployments/active/<deployment_id>.json` (live VMs) → archived to
   `deployments/archive/<YYYY-MM-DD>/<deployment_id>.json` on `DEPLOYMENT_COMPLETED` / `DEPLOYMENT_FAILED`. Programmatic
   surface: deployment-api route `vm_deployments.py` (`GET /api/vm-deployments?status=running`). SSOT:
   `vm-tarball-deployment.md` § "Observability & Lifecycle" + § "Three guarantees".
3. **Streaming GCS log** — heartbeat daemon uploads `/home/{user}/logs/<task>.log` to
   `gs://deployment-scripts-{pid}/vm-logs/<vm-name>/run.log` on a ~30s cadence. Sibling `EXIT_STATUS` file written on
   workload exit (`[vm-exec] command exited rc=<N>`). Absent `EXIT_STATUS` + truncated `run.log` = OOM signature (rc=137
   path, see `vm-tarball-deployment.md` § "Exit codes").
4. **VM zombie watchdog** — `deployment-service/scripts/vm/vm_zombie_watchdog.py` matches running VMs against
   `VM_PREFIX_TO_BUCKET` registry every ~5min; unregistered prefixes are invisible to the watchdog (silent money burn).
   SSOT: CLAUDE.md "VM Naming Convention" + `launcher-script-ssot.md`.

## Lifecycle events every live service emits

Every adapter / service / strategy / VM workload emits the same closed set of lifecycle events via UTL
`log_event(event_type=..., correlation_id=..., ...)`. Closed set defined in UAC
`unified_api_contracts.canonical.crosscutting.lifecycle_events` (consumed by `setup_events()`):

| Event                    | Severity | Expected cadence                                     | Stall trigger                                         |
| ------------------------ | -------- | ---------------------------------------------------- | ----------------------------------------------------- |
| `STARTED`                | INFO     | Once per `correlation_id` at process boot            | Missing within 60s of VM provisioning = launcher fail |
| `PROCESSING` / per-shard | INFO     | Every shard / batch / iteration the workload owns    | No `PROCESSING` for `max_gap_seconds` = stall         |
| `ADAPTER_FETCH_FAILED`   | WARN     | Per-adapter classified-error emission                | High rate = upstream venue degradation                |
| `DEPENDENCY_DEGRADED`    | WARN     | Manifest gap / upstream API slow / RPC node failover | Persistent = data-correctness risk                    |
| `STOPPED`                | INFO     | Once per `correlation_id` at clean exit              | Pair with prior `STARTED` for run-completeness sweep  |
| `FAILED`                 | CRITICAL | Once per `correlation_id` at exception exit          | Auto-pages via alerting-service                       |
| `PREFLIGHT_SKIPPED`      | INFO     | Once per `correlation_id` when honest-absence skip   | Expected on holiday / weekend / pre-source-coverage   |

Every adapter MUST classify errors via UAC `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED` (shard-level failure
isolation rule, SSOT `codex/04-architecture/shard-level-failure-isolation.md`).

## Per-archetype heartbeat matrix

Live trading archetypes per the May-23 master plan (extensible to future archetypes; each archetype owner registers
their entry):

| Archetype                   | Expected heartbeat event    | `max_gap_seconds` | Notes                                                                   |
| --------------------------- | --------------------------- | ----------------- | ----------------------------------------------------------------------- |
| `carry_staked_basis`        | `LST_YIELD_REFRESHED`       | 300               | Lead archetype; LST yields refresh per UAC `LST_REFRESH_CADENCE`        |
| `leveraged_funding_arb`     | `PERP_FUNDING_TICK`         | 60                | 6-perp-venue fan-out; per-venue tick stream                             |
| `live_mtds_per_asset_group` | `OHLCV_BAR_WRITTEN`         | 90                | Per-asset-group live ingest; 60s cadence + 30s grace                    |
| `live_features_per_family`  | `FEATURE_BATCH_EMITTED`     | 180               | features-service consolidated dispatcher per FeatureFamily              |
| `live_execution_router`     | `ORDER_LIFECYCLE_TICK`      | 30                | Order book + fill ack; tight loop                                       |
| `live_position_monitor`     | `POSITION_SNAPSHOT_WRITTEN` | 60                | position-balance-monitor-service per-venue snapshot                     |
| `vm_heartbeat_default`      | (heartbeat daemon)          | 600               | Universal VM-level fallback; `STALL_TIMEOUT_SEC=600` log-mtime watchdog |

Per-archetype thresholds live in UAC `unified_api_contracts.canonical.crosscutting.live_heartbeat_thresholds`
(authoritative). Adding a new archetype: extend the dict, add a row above, ship the alerting-service rule in the same
logical unit.

## Cross-cloud parity expectation

Live = batch (CRITICAL workspace rule). Both clouds emit identical events to identical schemas — only the SOURCE for a
given `(asset_group, data_type)` may differ between clouds. Concretely:

- **GCP path**: events bucket `gs://{gcp_pid}-events-{env}/...`, deployment-api Cloud Run (`asia-northeast1`).
- **AWS path**: events bucket `s3://{aws_pid}-events-{env}/...`, deployment-api ECS (`ap-northeast-1`).
- **Consumer contract**: `setup_events()` from UTL is cloud-agnostic — same call shape works on both clouds. The
  deployment-UI events tab reads from BOTH event streams; the cloud-toggle in the header switches which stream is
  visualised but both are always live.

**Cross-cloud reconciliation drill**: weekly cron VM (per "Runbook Execution-Owner SSOT") spot-checks that for a sampled
set of `correlation_id` values, both clouds saw the same `STARTED+STOPPED+PROCESSING` cadence within tolerance. Drift
triggers alerting-service `CrossCloudEventStreamDriftAlert`. Today this is reviewer-discipline (post-cutover backlog
tracked in `plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` Sweep 3).

## Stall-detection alerting

The alerting-service consumes the event stream + emits `AlertCode` on heartbeat-miss. Closed set of stall codes (extend
in UAC `AlertCode`):

- `LIVE_HEARTBEAT_MISS_{archetype}` — no expected heartbeat event for archetype within `max_gap_seconds` × 1.5.
- `LIVE_DEPLOYMENT_FAILED` — `DEPLOYMENT_FAILED` event observed in registry; pages on-call.
- `LIVE_VM_ZOMBIE_DETECTED` — VM exists in `gcloud compute instances list` but no event in event-stream for > 1h AND VM
  age > 1h. Surface: vm-zombie-watchdog VM logs.
- `LIVE_STARTED_WITHOUT_STOPPED_EMPTY_OUTPUT` — STARTED+STOPPED pair recorded but manifest sample shows zero captured
  rows OR 1440-NaN-bar signature. This is the **correlated-validation guarantee** (next section).

## Correlated-validation contract (CRITICAL)

The three guarantees (streaming log + deployment registry + self-delete) answer "did the VM run + complete + clean up?"
They do NOT answer "did the VM produce real captured rows, or empty placeholders?" Reference incident 2026-05-05: 21
MDPS VMs all emitted STARTED+STOPPED+self-deleted cleanly, but output was 1440 NaN OHLC bars per day for years (caught
only by hand-inspection).

The correlated-validation guarantee is supplied by the alerting-service + `unified-events-interface` consumption: a
`STARTED`+`STOPPED` pair MUST be correlated against a manifest spot-check (sample parquet OHLC populated; cluster
validation passing per writegate Phase 1A) **before** the run is treated as operationally complete. The audit-log
emission for the validation passes through `_publish_emission_check` per the writegate slice (b)+(c) emission policy
(SSOT: `codex/02-data/service-output-emission-semantics.md`).

This is the bright-line workspace rule "no fire-and-forget VM launches" — every VM launch MUST be paired with active
event-stream verification (STARTED + progress + STOPPED) + correlated manifest spot-check. SSH-tailing logs is a dev
crutch; production runs through deployment-UI events tab + alerting-service.

SSOTs: `vm-tarball-deployment.md` § "Three guarantees are NOT sufficient" callout + CLAUDE.md "No fire-and-forget VM
launches" + `codex/02-data/honest-absence-downstream-handling.md` (1440-NaN incident framing).

## Watchdog dict registration (required step at every launcher add)

Every new launcher's VM-name prefix MUST be registered in
[`VM_PREFIX_TO_BUCKET`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py) — CLAUDE.md "VM Naming Convention".
After the dict edit, **relaunch the watchdog VM** so it picks up the new prefix. Without registration, the new VM is
invisible to the zombie watchdog (silent money burn). Reference incident 2026-05-05 (5 prefixes silently un-watched).

This is also the surface monitored by the launcher-governance QG checks (O-7 + O-8 per
`plans/archive/issues/codex_audit_ops_2026_05_12.md`); see `launcher-script-ssot.md` § "QG check policy" for the
warning-with-baseline scaffolding pattern.

## Pre-launch verification protocol

Per "No fire-and-forget VM launches", every VM launch is paired with:

1. **STARTED check** — within 60s of `gcloud compute instances create`, the `STARTED` event MUST appear in
   `gs://{pid}-events-{env}/events/{service}/{date}/{correlation_id}/hour={H}/*.jsonl`. Absence = launcher failed before
   workload boot; check VM serial console + setup-script output.
2. **Progress check** — at least one `PROCESSING` / per-shard event per hour. Absence = workload hung.
3. **Exit check** — `STOPPED` or `FAILED` at process exit. Absence + VM gone = OOM (rc=137 signature, see
   `vm-tarball-deployment.md` § "Exit codes").
4. **Manifest correlation** — for ingestion VMs, the manifest sample MUST show `captured` rows with populated OHLC /
   bundle clusters (per writegate Phase 1A cluster validation). Empty + STARTED+STOPPED = 1440-NaN class incident.

The four-step protocol is enforceable via the alerting-service rules above; today it's reviewer-discipline for ad-hoc
launches and codified-discipline (alerting rules + correlated-validation) for live archetypes.

## Cross-references

- **Plan(s) implementing this**:
  [`master_to_live_defi_2026_05_23`](../../plans/active/master_to_live_defi_2026_05_23.md) work-stream B.
- **Related codex SSOTs**: [`vm-tarball-deployment`](./vm-tarball-deployment.md) — VM tarball mechanics + three
  guarantees + exit codes. [`launcher-script-ssot`](./launcher-script-ssot.md) — launcher SSOT + watchdog dict
  registration + QG check policy.
  [`../04-architecture/service-infrastructure-requirements`](../04-architecture/service-infrastructure-requirements.md)
  — `ServiceBootstrap` (STARTED/STOPPED/FAILED) + `make_health_router` requirements every service inherits.
  [`../02-data/honest-absence-downstream-handling`](../02-data/honest-absence-downstream-handling.md) — 1440-NaN
  reference framing + reason taxonomy for `record_empty`.
- **Code**: `unified-trading-library/events/` (event emission helpers + `setup_events()` cloud-agnostic dispatcher);
  `deployment-service/deployment_service/vm/heartbeat_cli.py` + `heartbeat_daemon.py` (per-VM heartbeat); deployment-UI
  events tab + Monitor sub-tabs (`deployment-ui-architecture.md`); alerting-service (heartbeat-rule consumers); UAC
  `unified_api_contracts.canonical.crosscutting.{lifecycle_events,live_heartbeat_thresholds,alert_codes}` (closed sets
  for event types + per-archetype thresholds + alert taxonomy).

## Open questions (deferred / post-cutover refinements)

- Cross-cloud event-stream drift reconciliation drill — codified above, weekly cadence; cron VM owner TBD post-cutover
  (tracked in `plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` Sweep 3).
- Heartbeat thresholds UAC dict vs per-service config — UAC `live_heartbeat_thresholds` is the SSOT today; per-service
  overrides via `--max-gap-seconds` CLI flag are an authorized exception when the service has asset-group-specific
  cadence.
- Intentional-idle distinction (e.g. between trading windows) — handled today by `PREFLIGHT_SKIPPED` event +
  per-archetype "expected silence window" annotation in the alerting rule; no false-positive `LIVE_HEARTBEAT_MISS` fires
  during scheduled idle.
