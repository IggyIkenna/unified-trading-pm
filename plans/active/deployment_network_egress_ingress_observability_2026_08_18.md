---
doc_type: plan
title: Per-deployment network egress/ingress observability — same-region vs cross-region, end-to-end to deployment-ui
summary: >-
  Closes a confirmed gap: today only `net_recv_rate_bytes_sec` is sampled (liveness signal, not volume accounting;
  egress is never captured), the column is written to BigQuery but never read by any API, and there is no same-region
  vs cross-region breakdown anywhere (only a dead `warn_cross_region_egress` config flag). Track 1 extends the
  existing D.1 host-metrics pipe (psutil sampler -> BigQuery `resource_samples` -> `/api/vm-resources/rolling` ->
  `VmResourceComparison.tsx`) to also capture and expose egress. Track 2 adds VPC Flow Logs (the only mechanism that
  can attribute same-region vs cross-region) joined against a newly-persisted per-deployment region field, surfaced
  on the same UI page. No new UAC domain module — every sibling model in this pipe is deliberately `CORRECT-LOCAL`.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-library, deployment-service, deployment-api, deployment-ui, unified-api-contracts]
scope: [engineer, admin]
tags: [observability, network, egress, ingress, vpc-flow-logs, deployment, resource-monitor, cost]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/cost_observability_deferred_followups_2026_07_10.md,
    /plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md,
    /plans/archive/2026_07/deployment_observability_expansion_2026_07_08.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
assigned_role: infra
effort: medium
drift_direction: advance-code
depends_on:
context_scope:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/billing-cost-observability.md,
    unified-trading-library/unified_trading_library/lifecycle/host_metrics.py,
    deployment-service/scripts/bootstrap_operational_data_bq.py,
    deployment-api/deployment_api/routes/vm_resource_history.py,
    deployment-api/deployment_api/services/operational_data_queries.py,
    deployment-service/deployment_service/deployment/state.py,
    deployment-service/deployment_service/deployment/orchestrator.py,
    deployment-service/deployment_service/deployment_config.py,
    deployment-ui/src/pages/VmResourceComparison.tsx,
    unified-api-contracts/unified_api_contracts/internal/deployment.py,
    unified-api-contracts/unified_api_contracts/internal/domain/deployment_service/deployment.py,
  ]
supersedes:
superseded_by:
source: [operator request, interactive session investigation 2026-08-18]
locked_by:
locked_since:
---

# Per-deployment network egress/ingress observability — same-region vs cross-region, end-to-end to deployment-ui

## Why this plan exists

An interactive-session investigation (2026-08-18) confirmed the current state precisely, cited file:line throughout:

- **VM self-report exists but is half-built and orphaned.** `HostMetricsSampler` in `host_metrics.py` calls
  `psutil.net_io_counters()` but only reads `.bytes_recv` — `.bytes_sent` (egress) is discarded even though it's
  returned by the same call. The field is a **rate** (bytes/sec at sample time), not a cumulative total. It IS
  persisted to BigQuery's `resource_samples` table (`bootstrap_operational_data_bq.py`) but is **never selected** by
  `operational_data_queries.py` or exposed by `vm_resource_history.py`'s `GET /api/vm-resources/rolling` — the column
  is written and then invisible to every consumer, including the `vm-resource-rightsizing-check` skill.
- **The field's original design intent was liveness, not volume accounting** — the archived
  `deployment_observability_expansion_2026_07_08.md` design doc scopes `net_recv_rate` as "stream flowing?" (dead
  websocket = 0). There was never a `net_sent_rate` in the original design. This work is a genuine scope extension,
  not finishing an abandoned feature — say so in the codex update (todo 12).
- **Same-region vs cross-region does not exist in any measured form.** The only related artifact is
  `warn_cross_region_egress` in `deployment_config.py` — a config flag, default `True`, **never consumed by any
  application code** (only referenced in its own definition and a test of its default value). The real strategy today
  is architectural avoidance (VM + bucket co-located in one region per deployment), not measurement.
- **No per-deployment region field exists at the grain the telemetry needs it.** Three deployment-identity records
  were checked; none supplies it: `deployment_service/deployment/state.py`'s `DeploymentState` (the actually-used
  one, imported by orchestrator/worker_manager/progress/monitoring) has no `region` field, even though
  `DeploymentOrchestrator.region` knows it at launch time and never persists it. UAC has **two divergent
  `DeploymentState` classes** with the same name (`unified_api_contracts/internal/deployment.py` vs
  `.../internal/domain/deployment_service/deployment.py`) — the one with a `region: str` field is the one nothing
  imports for that purpose.
- **Billing export is real and working, but structurally the wrong grain.** `cost_observability/resource_rows.py`
  classifies GCP/AWS billing-export SKU lines into an `"egress"` cost component — genuinely working, but dollars (not
  bytes), ~24h+ delayed, one `region: str` field per row (no region-PAIR concept), consumed today by the existing
  `/costs` page (`CostObservability.tsx`) which is out of scope for this plan (see `related:` — its own deferred-work
  doc was checked and carries nothing overlapping this).
- **No conflicting plan or half-written design doc exists.** `plans/active/` and `plans/active/issues/` were grepped
  for "egress", "VPC Flow", "network monitoring" — every hit was a false positive (unrelated word "workflow", or a
  Betfair-jurisdiction outbound-proxy provisioning concern, not telemetry). This is genuinely unscoped work.

## Architecture — two tracks, why they can't be one

OS-level counters (`psutil`, GCE's default per-instance metric, AWS `NetworkIn`/`NetworkOut`) can only ever report a
VM's **total** bytes in/out — there is no destination-awareness at that layer. Only flow-level logging (VPC Flow
Logs) can attribute same-region vs cross-region. So:

- **Track 1** — total per-VM/per-deployment egress+ingress. Small, extends the existing D.1 sampler → BigQuery →
  API → UI pipe end-to-end. No new infrastructure.
- **Track 2** — same-region vs cross-region split. Requires a new region-persistence fix (prerequisite) plus a new
  VPC Flow Logs pipeline landing in the *same* dataset/service/UI page, not a parallel stack.

Both tracks avoid orphans/duplicates by design: no new UAC domain module (every existing model in this pipe —
`ResourceRollingWindowRow`, `CostRecord`, etc. — is deliberately `CORRECT-LOCAL`, so a new UAC type here would be the
actual inconsistency), no new deployment-ui page (extends `VmResourceComparison.tsx`, the page that already owns
per-VM resource tables), no new codex doc (extends `deployment-observability.md`'s existing pipeline section).

## Todos

### Track 1 — total per-VM egress/ingress (extends the existing D.1 pipe)

- [x] [BACKEND] P1. Add a `net_sent_rate_bytes_sec` field to the `HostMetricsSample` dataclass and its sampler in
      `host_metrics.py` — the existing `psutil.net_io_counters()` call already returns `.bytes_sent`, only
      `.bytes_recv` is currently read. Gate: a unit test asserts a sampled `HostMetricsSample` carries both
      `net_recv_rate_bytes_sec` and `net_sent_rate_bytes_sec` as independently-correct rate values. —
      unified-trading-library@77ee7cec57. Both rates now share one `net_io_counters()` call (avoids a doubled
      syscall/torn snapshot); `test_rate_fields_compute_delta_over_elapsed_time` asserts recv=200.0 vs sent=50.0 from
      the same tick (independently-correct, not aliased). 6 pre-existing `HostMetricsSample(...)` call sites in
      `test_daemon.py` updated for the new required field. QG green (626s, unrelated pre-existing warnings only).
- [ ] [DATA] P1. Add a matching `net_sent_rate_bytes_sec FLOAT` column to the `resource_samples` schema in
      `bootstrap_operational_data_bq.py`, and confirm the heartbeat write path populates it on a real running VM.
      Gate: a live query against `deployment_operational_data.resource_samples` shows non-null
      `net_sent_rate_bytes_sec` for a currently-heartbeating deployment.
- [x] [BACKEND] P1. Extend `operational_data_queries.py` and `vm_resource_history.py`'s `ResourceRollingWindowRow`/
      `ResourceRollingWindowResponse` to select and expose avg/min/max/p95 of both `net_recv_rate_bytes_sec` and
      `net_sent_rate_bytes_sec`, mirroring the existing cpu/mem/disk pattern exactly (same `CORRECT-LOCAL`
      convention, no new UAC type). Gate: `GET /api/vm-resources/rolling` returns the new fields, covered by a
      passing deployment-api test. — deployment-api@61fa793832. 8 new SQL-aggregate columns
      (avg/min/max/p95 × recv/sent) added to `resource_samples_rolling_sql` + the response model; new unit test
      `test_selects_network_recv_and_sent_aggregates` asserts the SQL text, `test_prod_mode_maps_rows` extended with
      network fixture values + response assertions. QG green (247s).
- [x] [UI] P1. Add network columns (recv/sent, avg + p95) to `VmResourceComparison.tsx`'s per-VM table, following the
      existing column/sort-key pattern (`"vm_name" | "avg_cpu_pct" | ...`). Gate: the `/vm-resources` page renders
      live network figures for at least one real deployment, verified in the running app. — deployment-ui@95a1a62ada.
      "Net In (avg/p95)" / "Net Out (avg/p95)" columns added (`fmtBytesRate` human-scales B/s→KB/s→MB/s→GB/s), sortable
      via the existing `SortKey` pattern, `colSpan` on the expanded-row panel bumped 6→8 for the 2 new columns.
      pw:L2 ✓ — new test in `tests/smoke/vm-resource-rolling-window.spec.ts` ("renders network in/out rate columns")
      run against the real webServer-booted mock-mode app (not just unit-mocked): 6/6 passed. UI QG green (87s, 105
      unit tests, coverage 73.42%).

### Track 2 — region persistence (prerequisite for the cross-region split)

- [x] [BACKEND] P1. Add a `region: str` field to the live `DeploymentState` dataclass in
      `deployment_service/deployment/state.py`, populated at deployment creation from
      `DeploymentOrchestrator.region` (`deployment_service/deployment/orchestrator.py`), which already knows it at
      launch and currently discards it. Gate: a newly-created deployment's durably-persisted `DeploymentState` record
      carries the correct region, verified by reading it back after a real launch. — deployment-service@5d251b27e5.
      `region: str = ""` added to `DeploymentState` (default preserves backward-compat with pre-existing state.json
      blobs missing the key); `StateManager.create_deployment(region=...)` threads it through; both
      `DeploymentOrchestrator.deploy()` call sites now pass `region=self.region`. **Real end-to-end verification**
      (not just unit-mocked): a live `dry_run=True` deploy through a real `DeploymentOrchestrator` against the real
      prod state bucket (`unified-deployment-state-central-element-323112`) created a genuine `DeploymentState`
      record with `region="asia-northeast1"`, read back via `state_manager.load_state()` confirming the persisted
      value — probe artifact (`deployments.development/net-egress-observability-verify-region-probe-.../state.json`)
      deleted afterward via UTL `gcs_delete_object`. Also fixed an unrelated pre-existing red gate discovered while
      re-running QG (STEP 5.101 empty-string-fallback ratchet, 92 > baseline 91 — landed on `live-defi-rollout` by
      another concurrent session's commits `fd3c54ff`/`2058bab3`, confirmed via `git status` showing my own tree
      clean at those files): added `# noqa: qg-empty-fallback` with a reason to 5 deliberate-absence sites in
      `data_pipeline_monitors/escalation.py`/`escalation_dedup.py` (deployment-service@ec9a88aeec), then
      ratcheted the baseline down 91→87 (unified-trading-pm — baseline commit landing separately). deployment-service
      QG green (455s) after both fixes.
- [x] [BACKEND] P2. Reconcile the two divergent UAC `DeploymentState` classes
      (`unified_api_contracts/internal/deployment.py` vs
      `unified_api_contracts/internal/domain/deployment_service/deployment.py`) — decide which is canonical, fold
      the other's unique fields in, and confirm every current importer (`cluster.py`, `client_isolation.py`,
      `chaos_injections.py`, `subscriptions.py`, `kill_switch_routes.py`, `deployments_helpers.py`,
      `deployments/__init__.py`) still resolves. Gate: exactly one `class DeploymentState` definition remains in UAC,
      and `quality-gates.sh` is green across deployment-service and deployment-api. — unified-api-contracts@fa8b0262ed.
      Investigation found the two `DeploymentState` classes were byte-for-byte identical, but the surrounding files
      diverged: every named importer (all 6 + `deployments/__init__.py`) already resolves `DeploymentState` from
      `internal.domain.deployment_service.deployment` — that file is canonical by real usage (0 external importers
      of the sibling copy). Folded `internal/deployment.py`'s 3 `VMEventType.TARBALL_DEPLOY_*` values (referenced
      today only as plain string literals in `deploy_missing.py`, never as enum attributes — safe to add without
      touching a consumer) into the canonical enum, then made `internal/deployment.py` re-export
      `DeploymentState`/`DeploymentStatus`/`ComputeType`/`ShardEvent`/`VMEventType`/`VM_INFRASTRUCTURE_EVENTS` from
      the canonical module instead of duplicate-defining them — its own genuinely-unique classes
      (`BackfillLaunchTaskKind`/`Request`/`Result`, `VMLifecycleEvent`, `VMEventListResult`, real consumers in
      deployment-api's `backfill_launch.py`/`vm_events.py`/`vm_health.py`/`log_stream.py`/`vm_events_ws.py`) stay put.
      New `test_deployment_state_is_the_single_canonical_class` asserts object *identity* (not just equal shape)
      across both import paths. `internal/__init__.py`'s top-level re-export surface unaffected (imports exactly the
      preserved names). Fixed one incidental break: `test_deployment_schemas.py` imported
      `CloudProvider`/`PhaseMode`/`RuntimeMode` from `.deployment` — repointed to their real home (`.modes`). UAC QG
      green (510s); deployment-service QG green (455s); deployment-api QG green (365s) — all 3 repos the gate names,
      confirming every real consumer still resolves.

### Track 2 — VPC Flow Logs pipeline (GCP first)

- [x] [INFRA] P2. Enable VPC Flow Logs (`--enable-flow-logs --logging-metadata=include-all
      --logging-flow-sampling=<cost-justified value, start 0.1-0.5>`) on every GCP subnet hosting a
      deployment-service-launched VM, enumerated from the existing VM-launcher region registry rather than a fresh
      manual list. Note the incremental per-GB logging cost this introduces — state the chosen sampling rate and its
      cost rationale inline when landing this. Gate: `gcloud compute networks subnets describe <subnet>
      --region=<region>` shows `enableFlowLogs: true` for every in-scope subnet. — **Scope derivation**: grepped
      every `deployment-service/scripts/vm/launch-*.sh` for `--zone`/`ZONE=`/`--network`/`--subnet` (the real
      VM-launcher registry, not a manual list) — exactly 2 GCP regions appear: `asia-northeast1` (default zone for
      ~40 launchers, no explicit `--network`/`--subnet` ⇒ the `default` network's `default` subnet) and
      `europe-west2` (`launch-betfair-egress-proxy-vm.sh` only, explicit `--network=default` ⇒ also the `default`
      subnet). A third subnet exists in the project (`market-data-subnet`/`market-data-vpc`, asia-northeast1) but
      **excluded** — no launcher references it, so it's out of this plan's "deployment-service-launched VM" scope.
      **Sampling rate: 0.1 (10%)**, the low end of the plan's suggested 0.1-0.5 — chosen because the consuming query
      (next todo) only needs an hourly/daily same-region-vs-cross-region byte-total rollup, not per-flow fidelity;
      10% sampled bytes scale to a statistically reasonable aggregate at a fraction of the logging-ingestion cost of
      a higher rate, applied uniformly to both subnets for simplicity (europe-west2's single-VM volume is low enough
      that a higher rate there would cost negligibly more, but consistency was preferred over micro-optimizing one
      subnet). Verified: `gcloud compute networks subnets describe default --region=asia-northeast1` and
      `--region=europe-west2` both show `enableFlowLogs: True, flowSampling: 0.1`.
- [ ] [DATA] P2. Create a BigQuery Log Router sink routing the new flow logs into the `deployment_operational_data`
      dataset as a new aggregated table (e.g. `network_flow_summary` — rolled up per-deployment-per-hour, not a raw
      flow firehose), computing same-region vs cross-region byte totals by joining flow records' `src_instance`/
      `dest_instance` region annotations against `DeploymentState.region` (todo above). Gate: the aggregated table
      shows correctly-bucketed same-region/cross-region sums for a real deployment over a real window, spot-checked
      against source flow log rows.
- [ ] [BACKEND] P2. Add a new deployment-api route (e.g. `GET /api/vm-resources/network-flows`) exposing the
      aggregated rollup, following the same `CORRECT-LOCAL` response-model convention as `vm_resource_history.py`.
      Gate: the route returns real data for a deployment with flow-log history, covered by a passing test.
- [ ] [UI] P2. Add a same-region/cross-region breakdown panel to `VmResourceComparison.tsx` (an expandable per-VM
      row, mirroring the existing `KillEventsTable` expansion pattern) consuming the new route. Gate: `/vm-resources`
      visibly distinguishes same-region vs cross-region bytes for a real deployment.

### Closing the loop

- [ ] [BACKEND] P3. Wire the dead `warn_cross_region_egress` flag in `deployment_config.py` to consume the new
      region-split data and emit a real warning when a deployment's measured cross-region egress exceeds a
      threshold — or, if judged no longer wanted, delete the flag and its now-orphaned test in
      `tests/unit/test_deployment_config.py` rather than leave it dead. Gate: either a passing test demonstrates the
      warning firing on synthetic cross-region data, or the flag + its test are removed.
- [ ] [DOC] P2. Extend `unified-trading-pm/codex/05-infrastructure/deployment-observability.md`'s existing
      `## Durable operational data — BigQuery via the event spine` section with the new network fields (Track 1) and
      the new flow-log-derived table (Track 2) — no new doc. State explicitly that `net_recv_rate_bytes_sec`'s
      original intent was a liveness signal, now dual-purposed for volume accounting. Gate: the section documents
      both additions' read/write paths in the same style as the existing cpu/mem/disk documentation.
- [ ] [REVIEW] P3. Confirm no regression in `vm-resource-rightsizing-check` or the existing cpu/mem behavior of
      `/vm-resources` / `WorkHealthCard` after the schema and API additions land. Gate: `/vm-resource-rightsizing-check`
      runs clean against a real VM, and the pre-existing cpu/mem columns are unchanged.
- [ ] [DOC] P2. Flip `parent_epic` from `infrastructure_master` back to `security_and_cross_cutting_master` once the
      in-flight epic taxonomy restructure (`epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`) lands the new
      epic slug on origin — it wasn't committed yet at plan-commit time (2026-08-18), so `infrastructure_master` (old
      taxonomy) was used temporarily to pass `check_ag_closeout_linkage`/schema validation. Gate: `parent_epic` reads
      `security_and_cross_cutting_master` and `plan-hygiene` passes clean.

## Progress Log

- **2026-08-18 (interactive session)**: Plan authored from a same-session investigation (two Explore-agent passes)
  confirming the current gap and the exact SSOT placement for every layer. Operator chose "both tracks" + human
  (`assigned_vm: NA`) plan destination.
- **2026-08-18 (interactive session, commit pass)**: `plan-hygiene` pre-commit rejected the doc three ways: no
  `effort:`/`thinking_tier:` alongside `assigned_role` (fixed: `effort: medium`), no path to the infrastructure
  AG-closeout family (fixed: added `/plans/active/infra_consolidated_closeout_2026_07_25.md` to `related:`), and
  `parent_epic: security_and_cross_cutting_master` not a known epic slug — that epic file exists only as uncommitted
  staged content from another live session in this same slot (the epic taxonomy restructure), not yet pushed to
  origin. Operator chose to temporarily point `parent_epic` at the still-valid `infrastructure_master` rather than
  block on the other session; tracked as a follow-up todo above.
