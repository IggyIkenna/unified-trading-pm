---
doc_type: codex-ssot
title: Deployment Observability — live/batch/paper × GCP/AWS at /repos grade (SSOT)
summary:
  SSOT for classifying every compute unit (VM or Cloud Run job) into a DeploymentUmbrella (LIVE / BATCH / PAPER /
  EXPERIMENT) × cloud × kind and surfacing it at /repos grade in deployment-ui /deployments + /cockpit + Slack —
  classify_deployment_target resolver, the CLOUD_RUN_JOBS registry, CI guard tests, and the 3-layer out-of-band deadman
  monitoring.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-api, deployment-service, deployment-ui, unified-trading-system-ui]
scope: [engineer, admin]
tags: [observability, monitoring, deployment, self-healing, ui, cost, billing]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
    /codex/05-infrastructure/live-deployment-monitoring.md,
    /plans/archive/2026_07/deployment_ui_cost_per_day_accuracy_2026_07_20.md,
    /plans/archive/2026_07/deployment_ui_fleet_tab_consolidation_2026_07_21.md,
    /plans/archive/issues/deployment_ui_fleet_tab_removal_2026_07_27.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md,
    /plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md,
  ]
created: 2026-06-22
authoritative_for:
  [
    DeploymentUmbrella classification (live/batch/paper/experiment) + deployment-target inventory API + health/cockpit
    rollup,
    deployment-api bounded-cache architecture + manifest live-build OOM guard,
  ]
referenced_by:
  [
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /codex/04-architecture/cross-venue-prediction-arb-detection.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/archive/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md,
    /plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md,
    /plans/archive/issues/terminated_vm_disk_orphan_no_reaper_2026_06_30.md,
  ]
owner:
last_reviewed: 2026-08-05
code_refs:
  [
    deployment-api/deployment_api/services/cost_observability/service.py,
    deployment-api/deployment_api/services/cost_observability/models.py,
    deployment-api/deployment_api/routes/deployments_inventory.py,
    deployment-api/deployment_api/routes/_run_log_resolution.py,
    deployment-api/deployment_api/routes/_run_log_tail.py,
    deployment-api/deployment_api/utils/bounded_cache.py,
    deployment-api/deployment_api/utils/worker_identity.py,
    deployment-api/deployment_api/health_routes.py,
    unified-trading-library/unified_trading_library/deployment_registry.py,
    unified-trading-library/unified_trading_library/lifecycle/daemon.py,
    deployment-ui/src/pages/Deployments.tsx,
    deployment-ui/src/pages/DeploymentDetail.tsx,
    deployment-ui/src/pages/Cockpit.tsx,
    deployment-ui/src/components/RunLogPanel.tsx,
    deployment-ui/src/components/StreamingLogsPanel.tsx,
    deployment-ui/src/components/NavMenu.tsx,
    deployment-ui/src/components/filters,
    deployment-ui/src/hooks/useColumnSort.ts,
    deployment-ui/src/lib/columnSort.ts,
  ]
---

# Deployment Observability — live/batch/paper × GCP/AWS at /repos grade (SSOT)

> Every compute unit (a **VM** or a **Cloud Run job**) is a **classified deployment target** tracked under a
> live/batch/paper umbrella, surfaced in deployment-ui `/deployments` + Slack at the same grade the CI/CD `/repos` page
> gives repos. GCP is complete; AWS rides the same contract (Phase 5). Plan:
> `plans/archive/2026_07/deployment_observability_parity_live_batch_paper_2026_06_22.md` (parent epic
> `observability_master`).

## The umbrella model (the classification everything reads)

`DeploymentUmbrella` (UAC `canonical/crosscutting/lifecycle_class.py`, StrEnum): **LIVE / BATCH / PAPER / EXPERIMENT**.
Each target classifies to exactly one umbrella × `DeploymentCloud{GCP,AWS}` × `DeploymentKind{VM,CLOUD_RUN_JOB}` ×
service × asset_group, materialised as a frozen `DeploymentTarget`.

| Umbrella       | Derives from                                                                                                                                                                                                   | Examples                                                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **LIVE**       | `lifecycle_class = LONG_LIVED_LIVE`                                                                                                                                                                            | live capture / trading / risk VMs                                                                                                     |
| **BATCH**      | `lifecycle_class ∈ {EPHEMERAL_BATCH, SCHEDULED_RECURRING}`                                                                                                                                                     | backfill VMs (`cefi-*`, `defi-backfill-*`, `api-football-*`) + the Cloud Run audits/consolidator/catalogue/expected-universe/monitors |
| **PAPER**      | **explicit override** (no single lifecycle_class — a paper cron is SCHEDULED_RECURRING): VM prefix `defi-paper-`/`funding-ensemble-paper-`/`strategy-paper-` or `is_paper`, carried on `VmPrefixSpec.umbrella` | paper-trading VMs + the `blrs-daily-determinism`/paper-week Cloud Run jobs                                                            |
| **EXPERIMENT** | `lifecycle_class = EPHEMERAL_EXPERIMENT`                                                                                                                                                                       | `exp-{ml,strategy,execution}-*` (folded under Batch in the UI by default)                                                             |

`UMBRELLA_FOR_LIFECYCLE_CLASS` (UAC) is the lifecycle→umbrella map; PAPER is absent from it (always an override).

## The classification SSOT (one resolver, one registry — never re-derive per surface)

- **`classify_deployment_target(name, *, lifecycle_class=None, cloud=GCP, kind=VM, is_paper=None, asset_group=None, service=None) -> DeploymentTarget`**
  — `deployment-service/deployment_service/deployment_classification.py`. PAPER if `is_paper`/a paper-prefix match; else
  `UMBRELLA_FOR_LIFECYCLE_CLASS[lifecycle_class]`; **raises `UnclassifiedDeploymentError` — never a silent default**.
  service/asset_group derive from the VM prefix (`VM_PREFIX_TO_BUCKET`) or job name.
- **`CLOUD_RUN_JOBS: Final[tuple[DeploymentTarget, ...]]`** —
  `deployment-service/deployment_service/cloud_run_job_registry.py`. **61 classified jobs** (58 BATCH / 3 PAPER)
  covering every `terraform/gcp/*_scheduler.tf`. A guard test (`test_every_scheduler_tf_job_is_registered`) **fails CI
  if a scheduler tf has no registry entry** — the "added a Cloud Run job, forgot to classify" catch (mirrors the
  VM_PREFIX_TO_BUCKET guard).
- **`VmPrefixSpec.umbrella`** (the override field) is set on the 3 paper prefixes in `vm_zombie_watchdog.py`.

## The API contract (deployment-api — the /repos-grade inventory)

deployment-api **depends on deployment-service** (sanctioned editable path dep — "deployment-api → deployment-service is
the real dependency direction"), so it imports the resolver + registry directly. Routes
(`routes/deployments_inventory.py`):

- **`GET /api/deployments/inventory?umbrella=&cloud=&service=&asset_group=&status=`** →
  `DeploymentInventoryResponse{items[], total, vm_count, cloud_run_job_count}`. Each
  `DeploymentItem = {name, kind, umbrella, cloud, service, asset_group, status, last_run_at, exit_code, heartbeat_age_seconds, captured_progress, run_log_uri}`.
  VMs come from the `DeploymentsRegistry` (same source as `/api/vm-deployments`); Cloud Run jobs come from
  `CLOUD_RUN_JOBS` enriched with their latest execution status via the GCP `run_v2` client
  (`routes/_cloud_run_executions.py`, the sanctioned `_gcp_sdk` seam). Status: `succeeded`(exit 0) / `failed`(non-zero
  incl. 137 OOM) / `running` / `stale`(heartbeat >15min) / `unknown`(GCP error → honest-degrade).
- **`GET /api/deployments/umbrella/{umbrella}/summary`** →
  `UmbrellaSummaryResponse{umbrella, total, counts_by_status, stale_count, last_failure}` — the /repos-overview
  equivalent.

(Note: bare `/api/deployments` was already owned by service-version deploys; the inventory lives at
`/api/deployments/inventory`.)

## The UI surface (deployment-ui `/deployments`)

`src/pages/Deployments.tsx` — **Live / Batch / Paper umbrella tabs** at RepoCi grade: a status-tone matrix of VMs +
Cloud Run jobs (kind icon, GCP/AWS cloud badge, status badge, exit_code with `137 (OOM)`/non-zero red,
captured-progress), a per-umbrella summary header, and URL-param-backed cloud/status/asset_group filters
(`useSearchParams` → deep-linkable). Drill-down `/deployments/:name` reuses `VmEventsTimeline` + `StreamingLogsPanel`
(live log tail + event timeline) + the GCS `run.log` link. pw:L2-gated (`tests/smoke/deployments-page.spec.ts`).

## Fleet-tab consolidation — Deployments owns inventory, Fleet is git-health-only (2026-07-21)

Plan: `deployment_ui_fleet_tab_consolidation_2026_07_21.md`. Fleet (`/fleet`) used to stack FIVE sections built before
Deployments existed as a dedicated tab; each capability now lives at its ONE real home instead of two divergent copies:

- **Deployments (`/deployments`) additionally owns idle-disk-spend** (merged from the removed `FleetOrphans.tsx`, not
  dropped): rollup cards (Stopped VMs / Reapable / Idle disk $/mo / Reclaimable $/mo, `deployments-idle-spend-cards`),
  per-row reap-verdict + stopped-age (`OrphanVerdictCell`, reusing
  `OrphanEntry.reap_verdict`/`stopped_age_hours`/`monthly_disk_usd` fields the backend joins into `DeploymentItem` for
  STOPPED/SUSPENDED/TERMINATED rows only — a running row honestly reports all four as `None`), a dry-run-first bulk reap
  (`POST /api/fleet/reap`) and per-instance delete (`DELETE /api/fleet/instances/{name}`), all ported verbatim (same
  testids/labels, `deployments-` prefixed) rather than rebuilt. Also owns the **folded `/vm-deployments` archive
  history** (`VmRunHistoryCard` on `DeploymentDetail.tsx` — Outcome/Duration/Rows Captured/Completed + archive log
  links, scoped per target).
- **Fleet (`/fleet`) is now git-health-only** — `FleetTab` renders exactly `FleetGitContent` (per-slot dirty-repo
  state + a `reported_at` snapshot-freshness timestamp, relative age + absolute-time tooltip, next to the existing
  `reporter_stale` badge). REMOVED (not merged — judged genuinely redundant): the VM-census embed, the cross-cloud
  reconciliation cards (endpoint unchanged, see the correction note above), `FleetInfra.tsx` in full (orchestrator/
  infra tiles — AO's own dashboard owns that surface), and the `FleetOrphans.tsx` embed (its capability moved to
  Deployments per the bullet above, so the Fleet-side copy was deleted, not just hidden).
- **`/vm-deployments` is RETIRED from the canonical nav but stays a LIVE route** (operator decision BLK-7cb5bbbc) —
  quarantined into a `legacy: true` `NAV_GROUPS` entry (off the canonical dropdown/top-bar), NOT redirected, because its
  non-compact render mode was the only reachable home for 4 venue-config panels
  (`VenueCredentialsPanel`/`VenueDateRangePanel`/`VenueRelaunchEstimatePanel`/`VenueTardisWindowsPanel`) the
  consolidation audit never accounted for. Those 4 panels were subsequently given their own canonical `/venue-config`
  route, closing that gap properly rather than leaving them stranded behind the legacy quarantine.

Anti-pattern this closes: a capability existing on TWO surfaces with divergent feature-completeness (Deployments could
SEE idle spend but not ACT on it; Fleet could act but wasn't the inventory-of-record) — the fix is always
MERGE-then-remove-the-duplicate, never a blind delete of the less-complete side without checking what it uniquely
offered.

## Fleet tab REMOVED entirely — supersedes the 2026-06-10 v2 decision (2026-07-27)

Issue: `deployment_ui_fleet_tab_removal_2026_07_27.md`. Deployment-ui's `/fleet` page (git-health-only since the
2026-07-21 consolidation above) is now DELETED — route, nav entry, `FleetGit.tsx`, the `getFleetGitHealth()` API
client + its types, the deployment-api proxy route (`GET /repo-ci/fleet-git-health`, `_repo_ci_fleet.py`,
`_mock_fleet_git_health`), all gone. **This explicitly REVERSES, for fleet git-health specifically, the "operator
decision v2" (2026-06-10, `monitoring_control_plane_master_2026_06_10.md`) that made deployment-ui the primary pane** —
that decision predates the single-VM architecture (2026-06-27); with only one orchestrator VM left (was ~11), the
cross-VM Landing page nobody navigates to anymore was the only place the AO-side page's nav lived, so the "consolidated
single pane" the v2 decision was chasing had already inverted into "a page nobody uses, proxied through another app."
Fleet git-health's only home now is agent-orchestrator's own dashboard — surfaced as a **top-bar popover**
(`FleetKpisMenu`/`FleetGitMenu` in `agent-orchestrator/dashboard/src/layout.tsx`) on the per-VM Dashboard page itself
(no navigation needed from wherever the operator already is), not a page reachable only via the retired Landing
click-path.

**Parity check before deletion** (the reason this wasn't a blind delete): deployment-ui's copy had exactly one thing
AO's own `FleetGit.tsx` lacked — per-slot snapshot-age (`reported_at` rendered as "Xm ago" + an absolute-time tooltip).
Ported into `agent-orchestrator/dashboard/src/FleetGit.tsx`'s `SlotRow` (a `snap:` chip next to the existing `ff:`
cron-result chip) before removal, so nothing regressed. AO's own copy already had two things deployment-ui's page lacked
(a GH-rate-limit widget and the `git_red_sustain_secs`-gated red/amber sustain threshold matching the Slack pager
exactly, which deployment-ui's copy never read off the wire despite it being present in the proxied payload) — those
stay AO-only, no reason to duplicate them into a page that no longer exists.

`RepoCi.tsx`'s repo-detail "Fleet Git" cross-link now points externally to
`https://agent-orchestrator.odum-research.com/` (was an internal `<Link to="/fleet">`) — same
`data-testid="repo-detail-fleet-link"`, so nothing else in the corpus needs to change to find it. The CockpitHealth
landing tile labeled "Fleet VMs (GCP+AWS)" (VM-census framing, not git-health) now points at `/deployments` instead of
the deleted `/fleet` — its own metric text (running/zombie/OOM/ unknown) already described data that lived at
`/deployments` since the 2026-07-21 consolidation above, so this was a stale link fixed in passing, not a new decision.

## Date-range filter, kind multi-select, always-on treatment (WS-2/WS-3, 2026-07-21)

Plan: `deployment_ui_date_range_filter_and_search_2026_07_20.md`. "What was running between date A and B" on
`/deployments`, plus the `kind` filter becoming multi-select and a service dropdown + target search box sharing the same
filter bar.

**Per-kind date-filter support matrix** (`_apply_date_range`, `deployment-api/routes/deployments_inventory.py`) — every
kind is either interval-backed, single-timestamp, or has no timestamp signal at all:

| Kind(s)                                                                                  | Signal                                                    | Overlap test                                                                                                                                                     | `basis`                                                                |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| VM / registry rows                                                                       | `started_at` + `completed_at`/`last_heartbeat_at`         | `started_at ≤ date_to` AND `effective_end ≥ date_from`, where `effective_end` = `completed_at` if terminal, else `last_heartbeat_at` once stale, else open-ended | `"approx"` only on the stale-heartbeat branch; `None` otherwise        |
| `CLOUD_RUN_JOB` (GCP **and** AWS Batch/Fargate — share the wire kind) / `SCHEDULER`      | one timestamp (`last_run_at`/`last_attempt_at`)           | point-in-range: `date_from ≤ ts ≤ date_to`                                                                                                                       | always `"approx"` on a match — one instant standing in for an interval |
| Unmanaged VMs with no registry `started_at`                                              | `last_run_at` (falls into the same single-timestamp path) | same point-in-range test                                                                                                                                         | `"approx"`                                                             |
| `CLOUD_RUN_SERVICE` / `ECS_SERVICE` / `LAMBDA` / `CLOUD_FUNCTION` / `DISK` / `STATIC_IP` | none                                                      | always passes through unfiltered — **"always-on"**                                                                                                               | n/a — not scoped by the filter at all                                  |

A row with `started_at`/`last_run_at` missing entirely is never filtered out (honest-absence: no signal ⇒ don't guess).
**Heartbeat-stale threshold: `_REAP_STALE_HOURS = 6`**, deliberately reused from `DeploymentsRegistry.reap_stale`'s own
6h reap constant (UTL `deployment_registry.py`) — the same audit finding that motivated this whole workstream (219 rows
read `status=running` while only 12 GCE instances actually were).

**Always-on kinds never silently vanish from a date-filtered view.** `ALWAYS_ON_KINDS`
(`deployment-ui/src/pages/Deployments.tsx`) is the frontend's exact complement of the backend's
`_SINGLE_TIMESTAMP_KINDS ∪ {VM}` — `{CLOUD_RUN_SERVICE, ECS_SERVICE, LAMBDA, CLOUD_FUNCTION, DISK, STATIC_IP}`. These
rows sort **last** and carry a distinct cyan "always-on" badge (`LastRunCell`) whenever a date range is active —
deliberately NOT the amber `basis === "approx"` tone reused from the Cost/day convention above: amber means "this data
point is uncertain," cyan means "not applicable — this row was never scoped by the filter at all." Two different
meanings, two different colours, same page.

**Archive range-read bypasses the 7-day cheap-census cap.** The live inventory endpoint's default cold-path caps its own
archive read at `_ARCHIVE_WINDOW_DAYS = 7` days, but GCS actually retains `deployments/archive/` for 30 days
(live-confirmed 2026-07-20). A date-range query reads the requested `deployments/archive/<day>/` day-partitions
**directly** (still bounded, single-walk discipline preserved — never a whole-corpus walk), clipped to the real floor:
`_archive_floor_date = now − (_ARCHIVE_RETENTION_DAYS − 1) days` = **29 days back** (a 30-day inclusive window). A
request whose `date_from` predates that floor sets `date_range_out_of_range: true`

- `archive_floor: "<ISO date>"` on `DeploymentInventoryResponse`, rendered as an explicit **amber** banner
  (`AlertTriangle`, testid `deployments-date-range-out-of-range`) — distinct from the **red** fetch-error banner
  (`AlertCircle`, testid `deployments-error`) and mutually exclusive with it — never a silently-clipped partial result.

**`kind` filter is multi-select**, client-side only (not a server param, unlike umbrella/cloud/status/asset_group) —
`KindFilterChips`, comma-separated `?kind=`, URL-backed. An old single-value deep link (`?kind=VM`) still parses as a
1-element set, so no deep-link breakage.

**`CLOUD_RUN_SERVICE` timestamp asymmetry (found in the 2026-07-20 audit) — closed.** It previously carried NO timestamp
field at all, unlike its AWS twin `ECS_SERVICE` (`last_run_at = updated_at or created_at`). Fix: `last_deployed_at`
sourced from the Cloud Run **Service** resource's own `update_time` (falls back to `create_time`) off the
already-fetched list call — a free win, deliberately NOT a per-service `GetRevision` RPC. Lands on the **existing**
`DeploymentItem.last_modified_at` field (reused, not a duplicate — that field already meant "deploy/modify time,
distinct from last-invoke" for AWS Lambda).

**Date-range URL params**: `?date_from=&date_to=` (`DateRangeFilter`), both bounds independently clearable via their own
`✕`; a separate atomic clear-both action exists because two sequential single-param URL updates were found to race
against the same stale `searchParams` snapshot and clobber each other.

## Cost/day attribution contract (per-target cost cell)

The Deployments table's Cost/day column (`CostCell`, `deployment-ui/src/pages/Deployments.tsx`) reads real GCP BigQuery
resource-level billing export + AWS Athena CUR data via `deployment-api`'s
`CostObservabilityService.per_resource_daily()` (`deployment_api/services/cost_observability/service.py`) — **no rate
card, no fabrication**. It attaches three USD figures per deployment target by joining on billing
`resource_id == item.name`. Fixed 2026-07-21 (`plans/archive/2026_07/deployment_ui_cost_per_day_accuracy_2026_07_20.md`)
after all three figures were individually correct in source but wrong in aggregation.

**The three definitions** (`ResourceDailyCost`, `cost_observability/models.py`) — net = cost + credit, USD (GCP already
converted from GBP at query time):

| Field               | Definition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `actual_usd`        | Net cost on the most recent **COMPLETE** billing day (a day strictly before UTC-today); falls back to the latest (still-accruing) day only if no complete day exists yet.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `avg_7d_usd`        | Total net over the trailing window ÷ **the count of days the resource actually has billing rows** (`len(day_net)`) — NOT the fixed window length. A 1-day-old resource averages over its 1 day, so it reads `$4.4 · 7d ~$4.4`, not `$4.4 · 7d $0.63` (the reported symptom — divided by the fixed `days=7` even when the resource only had 1 billing day).                                                                                                                                                                                                                                                         |
| `projected_24h_usd` | The same most-recent COMPLETE day's net (so `actual_usd == projected_24h_usd` is expected + correct for any resource with a complete day); falls back to **partial-day normalisation** (`day_cost / hours_billed × 24`) only when no complete day exists — `hours_billed` = wall-clock hours elapsed since UTC midnight (floored at 1h to avoid a runaway multiplier in the first minutes of a new UTC day). Not a new hourly billing query — the billing snapshot stays daily-grained. Previously `max(daily)` (peak observed day), which silently overstated any resource whose peak day wasn't its most recent. |
| `cost_basis`        | `"complete"` when a complete billing day exists (both figures above derive from it); `"partial"` when no complete day exists yet and both fall back to the latest, still-accruing day. Carried onto `DeploymentItem.cost_basis: str \| None` (`None` = no billing row yet, honest absence) — never fabricated.                                                                                                                                                                                                                                                                                                     |

**Active-days average, not fixed-window** is the core fix: `per_resource_daily(days=N)` GROUP BYs `(resource_id, day)`
over the window, then divides each resource's sum by however many distinct days THAT resource has rows for, not `N`. A
resource billed on only 1 of the last 7 days no longer reads as if it cost 1/7th of what it actually cost.

**GCP-name / AWS-ARN join** (`_attach_costs`, `deployment_api/routes/deployments_inventory.py`): a GCP VM's billing
`resource.name` already equals its instance name (== `item.name`), so GCP rows join directly. AWS Athena CUR's
`line_item_resource_id` is an ARN or bare instance-id (`arn:aws:ec2:<region>:<acct>:instance/i-...`), which won't match
a friendly name — `_load_aws_items` builds `{instance_id: Name tag}` from the EC2 census
(`deployment-service/backends/aws_census.py` `AwsInstanceCensus` / `list_ec2_census()`) and threads it into
`_attach_costs` as `aws_instance_id_by_name`. `_aws_instance_id_from_resource_id` parses the trailing `instance/i-…`
segment off the ARN (or accepts a bare `i-…`), resolves it through the map, and re-keys the cost record under the
friendly name before the by-name join runs. No mapping found (unmapped instance, non-EC2 AWS resource) → the item's cost
fields stay `None` — **never a fabricated `$0`**.

**Cost enrichment is best-effort and never breaks the census**: `_attach_costs` wraps the `per_resource_daily()` call in
a try/except — a billing-source failure (Athena/BigQuery down) logs a warning and leaves every item's cost fields
`None`; the inventory itself still returns.

**UI colour convention (no text label)**: `CostCell` renders `cost_actual_usd` in `text-amber-400` when
`item.cost_basis === "partial"`, else the normal `text-[var(--color-text-primary)]` tone — colour is the ONLY signal
distinguishing a still-accruing partial-day figure from a settled complete-day one (operator decision 2026-07-20;
refines an earlier tooltip proposal). The same `text-amber-400` convention is reused elsewhere on the page for
"estimated, not billing-derived" figures (e.g. the unmanaged-VM cost fallback) — one consistent amber = "approximate /
provisional" signal across the table, not cost-specific. pw:L2 regression: `tests/smoke/deployments-cost-cell.spec.ts`
(complete-day renders the normal tone; partial-day renders amber with no added text).

## Slack parity + alert enrichment

- **Deployment lifecycle** (`DEPLOYMENT_STARTED/COMPLETED/FAILED`, UTL events, plus the `DP_*` data-pipeline family)
  routes via `alerting-service/rules/deployment_rules.py` → `_route_data_pipeline_event`
  (`alerting_service/notifiers/router.py`) with a **`/deployments/{name}` deep-link** (FAILED=CRITICAL pages;
  STARTED/COMPLETED=INFO). **The Slack CHANNEL itself is umbrella-driven (operator 2026-06-23,
  `alerting-service@f94b3b5`)**, not a single fixed channel: `_is_live_umbrella()` reads the payload's `umbrella` field
  (case-insensitive leading-`live` match) — `LIVE` → `#uts-live-alerts`, everything else (`BATCH`/`PAPER`/`EXPERIMENT`
  or no umbrella) → `#data-pipeline-alerts` (the fail-safe default). CRITICAL severity ALSO pages via the existing
  incident path (PagerDuty/Telegram) for BOTH umbrellas — only the Slack channel mirror differs. **Emitter
  umbrella-stamping contract** (`deployment-service@94dfcfc`): the payload's `umbrella`+`cloud` fields are stamped by
  the SSOT resolver `umbrella_for_vm_name()` (`deployment_classification.py`, longest-prefix match via
  `VM_PREFIX_TO_BUCKET` → `classify_deployment_target`), wired into `deployment_heartbeat._emit`,
  `exit_code_fleet_monitor`, and `heartbeat_stall_watcher` — every VM/Cloud-Run-job event that reaches the router
  already carries the umbrella; an emitter that omits it defaults to the batch channel.
- **Daily estate digest** (`DEPLOYMENT_DIGEST`, UTL event, INFO): a once-a-day per-umbrella rollup (LIVE up / BATCH
  completions+failures / PAPER status + the last-failure per umbrella) so operators get one morning glance instead of
  watching the lifecycle stream. Built by deployment-api `routes/deployment_digest.py` off `_load_inventory` +
  `build_umbrella_summary` (loaded once), emitted via UTL `log_event("DEPLOYMENT_DIGEST", INFO, details={message,…})` →
  the `lifecycle-events` Pub/Sub topic → the ni-service subscriber → `deployment_rule_for` → `#data-pipeline-alerts`
  (channel-only, never pages; the digest text rides in `details["message"]`). Cron: an isolated daily Cloud Run Job
  (`scripts/deployment_digest_worker.py`) via `deployment-service/terraform/gcp/deployment_digest_scheduler.tf`, off the
  live service's request path. **Same relay as the lifecycle events above — no HTTP URL to configure.** On-demand /
  dry-run preview: `POST /api/deployments/digest/run`.
- **Every DP\_\*/deployment alert is self-sufficient** (`notifiers/data_pipeline_slack.py`): a fenced-code **trace
  block** (the FetchEvidence dict / exit_code+run_log_tail / error_message, truncated to 3000 chars) + **deep-link
  buttons** — VM logs `{base}/ops/vms/{vm}`, Deployment `{base}/deployments/{vm}`, Data status
  `{base}/service/{svc}/data-status?asset_group={ag}`, and the GCS `run.log` console link. Base from config
  `deployment_ui_base_url` (SM/env `DEPLOYMENT_UI_BASE_URL`, hot-reloaded; `""` → links omitted, never broken).

## Durable logs (the substrate every surface reads)

Every GCP VM launcher streams run.log + heartbeat + `EXIT_STATUS` to `gs://deployment-scripts-{pid}/vm-logs/{VM_NAME}/`
(self-delete-proof) via `vm-exec-with-gcs-tee.sh` / `setup-data-pipeline-vm.sh` / `lc_log_upload_trap_block`. A coverage
guard (`tests/unit/test_vm_launcher_scripts.py::TestDurableLogStreamerCoverage`) **fails if a GCP `launch-*.sh` doesn't
stream** (whitelist for long-lived/systemd-logged service VMs + AWS + fan-out wrappers, each with a reason).

## Run.log viewer — resolution contract, endpoints, events-vs-logs distinction (WS-4, 2026-07-21)

Repro audit finding: before this workstream, `run.log` content was **never fetched into the browser** — the "Live log
tail" panel was actually `StreamingLogsPanel` reading lifecycle EVENTS (`vm_events.py`, a different bucket entirely),
and the archive-path lookup 404d live because it guessed a date (`completed_at[:10]`) instead of matching the archiver's
actual write key. Plan: `plans/archive/2026_07/deployment_ui_vm_log_viewer_2026_07_20.md`.

**Final-snapshot writer contract** (the fix at the source): `HeartbeatDaemon._write_final_log_snapshot()`
(`unified_trading_library/lifecycle/daemon.py`) writes ONE durable copy of the local run.log to
`vm_run_log_final_uri(vm_name, project_id)` → `gs://deployment-scripts-{project}/log-archive/final/{vm}/run.log` (no
date component, no TTL, plain replace) — called from `_archive_terminal_state()` at actual VM completion (alongside the
existing interval-uploader's final flush), best-effort and shard-level-isolated (a write failure logs + never blocks the
terminal-event emission that already happened). Wired in `deployment-service`'s `heartbeat_cli.py` via
`final_log_uri=vm_run_log_final_uri(vm_name, project_id=...)`. The **SIGKILL fallback**
(`deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`) writes the same fixed path inline (bucket parsed from
`GCS_LOG_URI`) so a hard-killed daemon still leaves a final copy — the only remaining writer for that case. The old
`vm_run_log_rolling_uri` (date-guessing) helper had **zero production callers** anywhere (the daily archival cron builds
its rolling-copy path inline) and was deleted outright from UTL, not left as dead code.

**Read-path resolution — live-first, archive-fallback**: `resolve_run_log_location(vm_name, project_id)`
(`deployment-api/deployment_api/routes/_run_log_resolution.py`) always tries `vm_log_stream_uri` (the live streaming
path, 14-day TTL **from last write, not from VM start**) first, for ANY vm regardless of `completed_at`; on a miss,
falls back to `vm_run_log_final_uri` (the archive above). At most 2 `gcs_describe_object` calls (1 on a live hit).
`metadata is None` on both misses ⇒ honest "no log available", never a fabricated hit — this is the state for any VM
that completed before the writer shipped. **Deliberately per-VM/request-time only** — the bulk 45s-SWR-cached whole-
fleet census endpoints (`deployments_inventory.py::_vm_item`, `vm_deployments.py::_to_model`) do NOT call this resolver;
they only compute the two deterministic URIs (no existence-check I/O) so the fleet-wide background refresh stays pure.

**Size/tail/download endpoints** (`deployment-api/routes/deployments_inventory.py`), each reusing
`resolve_run_log_location` and returning `location: "live"|"archive"|None` so the UI can label which copy resolved:

- **`GET /api/deployments/{name}/run-log/metadata`** → size + last-modified (`gcs_describe_object` metadata already
  fetched by the resolver).
- **`GET /api/deployments/{name}/run-log/tail?lines=`** → bounded byte-range read of only the last
  `DeploymentApiConfig.run_log_tail_max_bytes` (default 256KB, `unified_trading_library.gcs_read_object_range`), split
  to the last `run_log_tail_max_lines` (default 300, clampable via `lines=`) — never loads the full object (observed
  362KB–13.4MB in the wild, 20-30MB a plausible worst case). A read that doesn't start at byte 0 drops its leading
  partial line (`_run_log_tail.py::tail_lines_from_bytes`).
- **`GET /api/deployments/{name}/run-log/download`** → short-lived signed URL (`generate_download_url`, expiry via
  `DeploymentApiConfig.run_log_download_url_expiry_minutes`, default 15 min) — the client downloads directly from GCS;
  the API never streams the object through itself.

All three return `exists=False` (no `download_url`/no `lines`) when neither path resolves — an honest empty state, not a
dead link or blank panel.

**Events-vs-logs panel distinction** (`deployment-ui`, `DeploymentDetail.tsx`): the pre-existing `StreamingLogsPanel` is
genuinely lifecycle EVENTS under the hood (both its WS path here and the cockpit `AlertsLogsTab`'s SSE path convert
`VMLifecycleEvent` → a `VmLogLine` envelope) — renamed to "Live event stream" with a subtitle pointing at the new panel,
rather than rebuilt, since its functionality was never broken, only mislabeled. The genuinely new `RunLogPanel.tsx` is
the actual run.log viewer: size + capped tail + working download, with honest states — `run-log-empty` (`exists=false`),
an amber `run-log-archive-notice` banner when `location=archive` (14-day-TTL expired, showing the archive copy), and
surfaced (never swallowed) `run-log-error`/`run-log-download-error` alerts.

## Coverage status

- **GCP: COMPLETE** — every VM prefix + every Cloud Run job + every GCP launcher is classified/tracked/streamed,
  enforced by 3 guard tests (VM-prefix classify, scheduler-tf registry, launcher durable-log). 0 unclassified / 0
  untracked is a CI invariant, not a one-time audit.
- **AWS: Phase 5** — EC2 backfill VMs + Batch Fargate ride the same `DeploymentTarget`/`cloud=AWS` contract;
  `/api/deployments/inventory` returns `cloud=aws` items once the AWS census is wired.

## AWS backend activation (deployment-registry DynamoDB)

The deployment-registry `DeploymentRegistryStore` (UTL `cloud_interface`) has a DynamoDB backend implementing the SAME
Protocol as the GCP Firestore backend — provisioned now (Phase 4 of
`plans/archive/2026_07/deployment_registry_firestore_p4_dynamodb_2026_07_14.md`) but **inactive**: the store factory
selects the backend from the active cloud (mirrors `resolve_bucket_name`'s GCS/S3 selection) and defaults to Firestore
on GCP.

- **Table**: `unified-trading-{environment}-deployments` (terraform
  `deployment-service/terraform/aws/deployment_registry_dynamodb.tf`) — partition key `deployment_id`, GSI
  `status-index` on `status` (the DynamoDB analogue of the Firestore `query_by_status` query). `PAY_PER_REQUEST` billing
  by default (`deployment_registry_dynamodb_billing_mode` var toggles to the 25-WCU/25-RCU free-tier `PROVISIONED`
  mode). Server-side encryption enabled.
- **Activation is one line**: flip the active-cloud selector to AWS — the store factory then instantiates
  `DynamoDbDeploymentRegistryStore` instead of `FirestoreDeploymentRegistryStore`; no caller changes. Until that flip,
  the table sits provisioned + empty (no writes, negligible cost).

## The cockpit + health rollup + per-deployment freshness (2026-06-24)

The unified **`/cockpit`** is the deployment-ui DEFAULT page (`src/pages/Cockpit.tsx`): one place to answer "is
everything OK right now?" across live/batch/paper deployments + fleet/consolidators/CI/alerts/billing, plus
deploy/launch and stream logs without leaving. 12 tabs (Health · Deploy · Live · Batch · Paper · Fleet · Consolidators ·
CI · Alerts&Logs · Launch · Chaos · Safety); top bar is pure-utility (env badge · LIVE/MOCK DATA · GCP/AWS · API status
· version). The **Health TAB is the landing** — a tile grid wired to the rollup endpoints (no placeholders); each
per-domain tab folds the existing page COMPONENT in-place (never a rebuild) + reads the real inventory.

**Health rollup endpoints (deployment-api `routes/health_overview.py` + `health_consolidator.py`):**

- **`GET /api/health/overview`** →
  `{generated_at, overall: ok|degraded|critical, tiles:[{id, label, status, value, detail_href}]}` — aggregates the
  EXISTING signals into one envelope (fleet vm-census, consolidator staleness, coverage, open alerts by class, GH
  rate-limit, today's cost). Pure reuse — no new data sources. The cockpit Health tiles overlay this rollup + the 3
  umbrella summaries (live/batch/paper) + repo-ci overview (ci) → all 10 landing tiles show real data.
- **`GET /api/health/consolidator`** →
  `{overall, asset_groups:[{asset_group, bucket, status, index_age_seconds, staleness_budget_seconds, per_vm_shard_fallback_active, last_successful_run_at, detail}]}`
  — per-AG manifest-index freshness (the consolidated `_index` heartbeat age + whether the per-VM shard recovery-merge
  fallback is active). Honest per-AG degrade to `unknown` on a read failure, never a 5xx. **Bucket kind is per-AG**:
  cefi/defi/tradfi/sports use `market-data`; prediction uses the dedicated `market-data-tick-prediction` key (a guard
  test keeps the map complete so an unmapped AG fails at test-time, never 5xx in prod).

**Per-deployment data freshness ≠ health (a liveness ping) — manifest-derived per OWNED shard (Phase 4.5):** the binding
_deployment → the shard-set it owns_ is the deployment-service resolver
`deployment_cluster_registry.responsibility_for_deployment(target) -> ShardResponsibility` (a PURE derivation off the
classified `service`+`asset_group`+`umbrella` — never a hand-dict; raises rather than silently `NONE` for a data
service). `ShardResponsibility` (UAC `canonical/crosscutting/lifecycle_class`) has
`kind ∈ {asset_group_capture, manifest_consolidation, strategy_shard, none}`. **`GET /api/deployments/{id}/freshness`**
(`routes/deployment_freshness.py`) classifies the deployment → resolves its responsibility → for a data obligation reads
the owned asset_group's **consolidated availability-index posture** (REUSES `consolidator_posture` — the index heartbeat
IS the manifest-derived freshness for the AG's owned shards; no new manifest walk) →
`{responsibility, asset_group, mode, freshness_status: fresh|stale|liveness_only|unknown, index_age_seconds, staleness_budget_seconds, per_vm_shard_fallback_active, oldest_available_at, detail}`.
**`NONE` (gateway/control-plane) → `liveness_only`** — never a false "fresh". The availability **manifest** stays the
per-shard freshness SSOT; this endpoint attributes it PER deployment instead of guessing from the in-memory health-ping
callback. (Known gap: the resolver keys off canonical SERVICE names, so VM rows whose `_derive_service` stem is a
launcher family — `strategy-live-*`, `cefi-binance-spot-*` — currently resolve `liveness_only` until the resolver maps
launcher families; tracked in the cockpit plan.)

**Inventory perf — the cockpit Live/Batch/Paper tabs are fast (2026-06-24):** `GET /api/deployments/inventory` read the
~hundreds of per-VM registry JSONs SEQUENTIALLY over a transpacific GCS hop (291-VM census + 7-day archive) → >100s,
timing out the tabs. Fixed (`routes/deployments_inventory.py`) with (1) **parallel per-object GCS reads**
(`_download_entries_parallel`, 32-worker ThreadPool — the GCS-object-ops pattern; GCS REST releases the GIL) + the 4
coarse calls run concurrently, and (2) a **stale-while-revalidate short-TTL cache** (45s): a fresh snapshot serves
instantly, a stale one serves instantly + kicks a single background refresh, a cold burst collapses to ONE census under
a lock. Measured: cold ~10s (one-time) → warm <0.2s.

**Cross-cloud reconciliation — "every RUNNING instance accounted for" (Phase 4):** `GET /api/fleet/reconciliation`
(`routes/fleet_reconciliation.py`) reconciles the live RUNNING set (the GCE aggregated-list) against the REGISTERED set
(the parallel active-registry read `active_registry_vm_names` plus `CLOUD_RUN_JOBS`) plus a control-plane prefix
allowlist — surfacing **UNKNOWN** (running but unregistered → classify-or-kill, its own alert class) and
**EXPECTED-MISSING** (registered/active but not running) as distinct `classify_vm_target`-classified rows. Rows are
capped at 200/cloud for a responsive payload while `unknown_count`/`expected_missing_count` carry the EXACT totals. AWS
rides the same shape and degrades to empty without creds (never blocks GCP). NOTE: a large `expected_missing` is
dominated by un-reaped STALE active entries (registry-hygiene debt — the zombie-watchdog's reap job), a real signal the
reconciliation surfaces. The reconciliation reads the full active registry (~2.4k entries) per call → ~13s cold; a
stale-while-revalidate cache (the inventory pattern) is a tracked perf follow-up. **UI wiring REMOVED 2026-07-21**
(Fleet-tab consolidation, below) — the cockpit Fleet tab no longer renders the accounted/unknown/expected-missing cards
(judged redundant with Deployments' own per-row status); the endpoint itself is UNCHANGED and still callable, just no
longer UI-consumed.

**Monitoring-registration enforcement — declare-or-fail-QG (Phase 4):** every long-lived deployable service MUST
self-register in `MONITORED_SERVICES` (`deployment_service/monitored_services.py`) — each entry carries its resolved
`ShardResponsibility` (data-plane producers own their asset_group capture shards; gateways/control-plane are
`NONE`/liveness-only). The **guard test**
`tests/unit/test_monitored_services_registry_guard.py::test_every_long_lived_service_repo_is_registered` asserts every
`service`/`api-service`/`api` repo in `workspace-manifest.json` has a `MONITORED_SERVICES` entry — a NEW unregistered
deployable service **fails deployment-service's `quality-gates-v2`** ("fails QG"), the parallel-to-
`test_cloud_run_job_registry_guard.py` enforcement. (A per-repo `base-service.sh` STEP is deliberately NOT added — a
per-repo bash check cannot read a CENTRALISED Python registry, so the centralised guard is the SSOT; `batch-service`
repos register as Cloud Run JOBS, not here.)

## deployment-api cache & memory architecture (2026-07-13/14 OOM remediation)

`uts-shared-deployment-api` OOM-crash-looped repeatedly the week of 2026-07-13 (20 kills in 75 min on a 4GiB container).
Full incident record, cache-island inventory (B1–B18), and the joint operator walkthrough that decided the fixes below
live in
[`deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md`](/plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md)
— this section is the durable architecture summary, not a duplicate of that narrative.

**Root cause, in one line**: every in-process cache is per-gunicorn-worker (×4 by default), several were unbounded with
lazy-only expiry, and the data-status manifest cell-grid compute path could allocate tens of GB in a single request — no
worker-count or RAM-limit tuning fixes an unbounded allocator.

**Bounded-cache primitive** — `deployment-api/deployment_api/utils/bounded_cache.py`: a `cachetools.TTLCache`-backed
`BoundedCache` (max-entries + TTL + evict-on-set), registered by name in a process-wide registry so every cache's stats
are enumerable via `GET /api/debug/cache-stats` (`health_routes.py`), plus a single periodic sweeper
(`start_sweeper`/`stop_sweeper`, wired into `deployment_api.lifespan`) that proactively expires cold keys — a `TTLCache`
only expires lazily on next-touch, so an unrepeated key would otherwise sit on expired memory forever between touches.
Every previously-unbounded cache site was migrated onto this primitive in one commit (`deployment-api@0702aa3`): the
data-status mega-cache now stores gzipped bytes (not live dicts) keyed without the `freshness_date` churn and serves a
pre-truncated variant (killing the per-hit `deepcopy`), the drilldown/log/GitHub response caches gained bounds, one dead
unbounded twin was deleted, and the in-memory tier of `UnifiedCache` was bounded while its unused GCS whole-blob-rewrite
tier was deleted outright (confirmed zero callers) rather than fixed.

**Manifest live-build OOM guard** (`deployment-api@030779f`) — the data-status cell-grid build is the actual memory
elephant (measured 18GB for instruments-service / 81GB for MTDS / 56GB for a 3-month MDPS window — no RAM tier survives
an unbounded compute of it). Two-layer defense on the live-build fallback path (the precomputed `full.json.gz` rollup
blob is still the fast/cheap path when fresh — see the rollup-worker note below): (1) a pre-flight byte-budget estimator
refuses or serves-stale before attempting a build sized to blow the container; (2) any build that passes the estimate
still runs inside a `resource.setrlimit(RLIMIT_AS, ...)`-bounded child process, so an underestimate raises a catchable
error in the child instead of OOM-killing the parent worker (and therefore every other in-flight request on it).

**`/api/vm-deployments` SWR snapshot** (`deployment-api@3f1fc66`) — this endpoint was the single worst offender (94s
avg, uncached, a full GCS registry + per-VM Compute API walk on every poll). Given the same 45s stale-while-revalidate
single-flight pattern already proven on the inventory/umbrella endpoints: instant-after-first-load instead of a 94s
wait, and concurrent first-pollers collapse onto one in-flight refresh rather than each firing their own walk.

**Background sync — single loop, not one per worker** (`deployment-api@6d5a225` + `deployment-service@650e418`) —
`auto_sync_running_deployments` used to start once per gunicorn worker (×4 duplicate GCS list+read loops per instance,
contending on per-deployment locks). Now leader-elected via `worker_identity.py` (one loop per instance) plus an
idle-skip when the scanned prefix is empty.

**Worker count + container sizing** — `WORKERS=2` is applied via the `cloudbuild.yaml` deploy step's `--update-env-vars`
(survives redeploys; not a manual live `gcloud` mutation) — halves the per-worker cache-copy baseline (~2.48GB → ~1.24GB
idle at 4 workers → 2). **⚠️ SUPERSEDED note on the plan's own D2 decision** ("keep 4GiB"): the deployed container was
bumped to **16Gi / 4CPU on 2026-07-17**, after this remediation landed — the data-status page mounts several heavy
pandas/pyarrow-class dependencies on cold start, and a first-mount burst still packed multiple of them onto one 8Gi
instance and OOM'd it (measured live; Cloud Run gen2 caps memory at 8Gi for 2 CPU, so 16Gi required bumping to 4 CPU
too). The bounded-cache + OOM-guard work above is still what makes the _steady-state_ footprint small; 16Gi is headroom
for the cold-start burst, not evidence the steady-state fixes didn't work.

**Rollup-worker cost-stop** (`deployment-api@8d260ad` + `deployment-service@08d29b0`) — the separate
`uts-prod-data-status-rollup-svc` (writes the `full.json.gz` blobs the fast path above reads) processed all 12 monitored
services sequentially in one process; one service's build OOM-killed the whole container, so everything queued after it
in the list never got a chance to write its blob. Fixed by giving each service's compute+write its own
`multiprocessing.get_context("spawn")` child bounded by `RLIMIT_AS` — one oversized service now raises a catchable
`MemoryError` in its own throwaway child instead of taking the other 11 down with it.

**Debug + alerting** — `GET /api/debug/cache-stats` (entries/estimated-bytes per named `BoundedCache`) is the
human-facing surface for the architecture above; the memory-utilization alert this feeds is documented in the alerting
layer below.

## Out-of-band liveness + data-pipeline self-monitoring (2026-06-24)

Three layers, each independent of the one it watches (so a dead watcher is never invisible):

- **Layer 1 — the dp-\* fleet monitors** (`deployment_service.data_pipeline_monitors`, 3 Cloud Run jobs on
  `deployment-api:latest` via `data_pipeline_fleet_monitor_scheduler.tf`): `exit-code` (`*/5`) + `heartbeat` (`*/5`) +
  `meta` (`*/15`). Each reads durable GCS artifacts and emits `DP_*` → #data-pipeline-alerts. **8Gi/cpu2** (they read
  the whole RUNNING fleet's per-VM shards — OOM at 2/4Gi → stale sentinel → false deadman page). Each writes
  `vm-census/{mode}-last-run.json` at end-of-sweep.
  - **Heartbeat liveness is SIDECAR-authoritative** (REVISED 2026-06-24, supersedes the 2026-06-22 run.log-primary
    BUG2): `heartbeat_age_min` = the fresh infra **sidecar blob** (`vm-heartbeat/{vm}.txt`, 60s direct-GCS channel) — it
    goes stale ONLY when the VM **host/network** wedges. The GCS-tee'd run.log `PIPELINE_HEARTBEAT` marker lags 42-78m,
    so keying STALL/auto-kill on it false-flagged every healthy-slow VM. run.log-frozen (generous **90m** bound, above
    the max tee lag) is now the hung-WORKER-on-a-live-host **alert-only** corroborator. Per-VM shard mtime stays the
    best signal while capturing.
  - **Auto-kill is sidecar-gated** (`should_auto_kill`, default-on): a fresh sidecar ⇒ `is_vm_progressing` True ⇒ NEVER
    reaped; only a sidecar stale ≥ `kill_minutes` (45m, host wedged) + not-capturing + backfill + not-live is deleted to
    reclaim its wave-launcher slot (cap 5/sweep).
  - **LIVE-VM exemption from `DP_VM_GONE_NO_CAPTURE` (2026-06-27)**: for LIVE VMs (`umbrella == "live"`) the manifest
    `captured` count is the INSTRUMENT COUNT (~15, stable) — it never climbs like a batch instrument-days counter. Flat
    captured on a live VM is benign by design; `DP_VM_GONE_NO_CAPTURE` is **suppressed** (verdict →
    `EXPECTED_NO_CAPTURE`). A live crash (exit != 0) is still caught by `DP_VM_EXIT_NONZERO`. Live capture health (VM
    alive, stream dead) is owned by `live_stream_watcher.py` DP-LIVE-001/002, not the exit-code sweep. Gated on
    `umbrella_for_vm` resolver returning `"live"` — absent it the check falls back to batch behaviour (fail-safe
    conservative).
  - **Host-cron freshness**: the TradFi wave-launcher (a Cloud Run job, `0 */3`) writes
    `vm-census/wave-launcher-last-run.json` each tick (`wave_launcher._write_last_run_sentinel`); the meta sweep probes
    its freshness (budget 360m) with NO Cloud-Run cross-check.
  - **RESOLVED bookend** (`meta_watchers.reconcile_resolved`, all 3 sweeps): a `DP_*` that fired last sweep but not this
    one posts a `:white_check_mark: RESOLVED` INFO. Per-mode active-alert blobs
    (`vm-census/active-dp-alerts-{mode}.json`) so the disjoint-event sweeps don't clobber each other.
- **Layer 2 — the out-of-band deadman** (`uts-prod-monitoring-deadman`, `deadman_poster.py`): probes the Layer-1
  sentinels + the watchdog census DIRECTLY (read-only GCS) and posts to its OWN Slack webhook — **never** `log_event` /
  PubSub / the alerting-service (it must be independent of the path it watches); exits 0 always. **Freshness reads the
  blob CONTENT `ts`**, not the storage-client `last_modified` (which is bare on `deployment-scripts-*` — a JSON sentinel
  reads `age=None` → false "missing (never ran)" otherwise; the epoch-sidecar shape still parses its first-line epoch).
- **Layer 3 — critical-service uptime** (`critical_service_uptime.tf`): 5 GCP-native `uptime_check_config` + alert
  policies (deployment-api / agent-orchestrator / **alerting-service** / deployment-dashboard /
  unified-trading-system-ui) every 5 min → the deadman **email** channel — fully independent of the Slack relay + the
  alerting-service SPOF, so they page even when the alerting path itself is down. `/health` returns 2xx
  (alerting-service is auth-gated → accept 403 = alive-but-protected). **No `notification_rate_limit`** (API rejects it
  for metric-threshold policies).
- **deployment-api memory (2026-07-14, `deployment_api_memory_alert.tf`)** — `uts-shared-deployment-api`
  OOM-crash-looped twice this week (4GiB container, unbounded per-worker caches — see § "deployment-api cache & memory
  architecture" above for the full remediation); uptime checks (Layer 3 above) only fire AFTER the service is already
  down, i.e. post-crash-loop. Closes that gap one step earlier:
  `google_monitoring_alert_policy.deployment_api_memory_high` fires on
  `run.googleapis.com/container/memory/utilizations` &gt;85% sustained 300s, reusing the SAME `monitoring_deadman_email`
  channel as the uptime alert above (deliberately not a new channel). Applied live via targeted `tofu apply` 2026-07-14
  (policy `projects/central-element-323112/alertPolicies/10817162460883602732`) — remember **no auto-apply pipeline
  exists for `terraform/gcp/`** (see the box below), a shipped `.tf` here is not live until someone runs `tofu apply`.

> **No terraform-apply pipeline for `terraform/gcp/`** — there is NO auto-apply. New infra there (uptime checks,
> schedulers) needs a deliberate `tofu apply` (remote GCS state `uts-terraform-state-{pid}`, prefix
> `terraform/state/prod` — a `-target`ed apply is safe + lock-protected). A shipped `.tf` is NOT live until applied.

## Durable operational data — BigQuery via the event spine (2026-07-27)

The live/current Resources column above (Firestore, `host_metrics_window` — last ~10 samples) is unchanged and stays the
source for point-in-time reads. Alongside it, `deployment_operational_data` (BigQuery, `central-element-323112`,
`asia-northeast1`) is the DURABLE side — full detail + design rationale in
`/plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md`; this section is the short
reference.

**Tables** (all partitioned `DATE(ts)`/`DATE(completed_at)`, clustered): `resource_samples` (per-VM cpu/mem/disk,
~1/min), `run_ledger` (one row per completed/failed run — the durable answer past the 30-day `deployments/archive/` GCS
TTL), `idle_spend` (daily rollup + per-resource idle rows), `reap_events` (one row per reaped VM),
`watchdog_kill_events` (one row per resource-watchdog kill/violation —
`ts, vm_name, pid, slot_id, command, reason, rss_mb, limit_mb, pressure_level, killed`; written by the AO host's
`resource-watchdog.sh` via `POST /api/fleet/watchdog/kill-events` →
`operational_data_writer.write_watchdog_kill_event()`; read via `GET /api/watchdog/kill-events` and deployment-ui's
`VmResourceComparison.tsx` per-VM expandable-row panel; shipped 2026-08-05 per
`/plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md`), `process_samples` (per-process
category breakdown — worker_agent/orchestrator/ci/ao_plan_work/other — scoped to genuinely multi-tenant hosts only;
**table exists, nothing publishes into it yet** as of 2026-07-27).

**Write path**: dedicated Pub/Sub topics (`resource-samples`, `run-ledger`) + NATIVE BigQuery subscriptions
(`--use-table-schema --drop-unknown-fields`) — a flat JSON payload matching the target table's columns exactly,
deliberately bypassing the generic `log_event()`/`PubSubEventSink` nested envelope (which cannot produce typed BQ
columns). `unified_trading_library.lifecycle.daemon.HeartbeatDaemon` stays consumer-agnostic — callers pass
`resource_sample_publisher`/`run_summary_publisher` (implementing `events.flat_event_publisher.FlatEventPublisher`)

- their own payload builders; deployment-service's `heartbeat_cli.py` and the standalone
  `scripts/vm/deployment_heartbeat.py` both wire this. Idle-spend/reap-event writes go through deployment-api's
  `operational_data_writer.py` (UTL `insert_rows`, never raw `google.cloud.bigquery`).

**Read path**: `deployment-api` `GET /api/vm-resources/rolling` (avg/min/max/p95 per VM per window, 1h/4h/24h/1wk; omit
`vm_name` for the cross-VM view) and `GET /api/vm-resources/process-category`; `deployment-ui`'s `WorkHealthCard`
(window selector alongside the live snapshot) and the `/ops/vm-resources` comparison page consume them.

> **Scope note (confirmed live via `bq query` 2026-08-05)**: `resource_samples` only has rows for
> deployment-service-launched VMs (backfill/live-data workers heartbeating through `HeartbeatDaemon`) — it has ZERO rows
> for the central agent-orchestrator API host (`i-0c9b283b31d6b5ca7`), which isn't a deployment-service target. For that
> host's own RAM/CPU/disk history (and its separate resource-watchdog kill-audit log), see
> `/codex/05-infrastructure/agent-orchestrator-api-host.md` § "Resource history sampler".
>
> **`watchdog_kill_events` is the first `deployment_operational_data` table with AO-host coverage** — shipped 2026-08-05
> per `/plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md`. The resource-watchdog
> (`resource-watchdog.sh`) dual-writes each kill event to both the AO-internal API (existing) and
> `POST /api/fleet/watchdog/kill-events` (new), so kill events from the AO host now appear in this table and in
> deployment-ui's `VmResourceComparison.tsx` per-VM panel. See `/codex/05-infrastructure/agent-orchestrator-api-host.md`
> § "Resource watchdog — Dual-write to deployment-api" for the watchdog-side write path and table schema.
> `resource_samples`/`run_ledger` still have zero AO-host rows (those tables remain
> deployment-service-launched-VM-only); extending them to the AO host is a separate, future scope decision.

**Known gaps** (tracked in the plan, not repeated here; updated 2026-07-28 — TTL + process-category publishing both
shipped since the paragraph above was first written): the cross-VM comparison page filters by service-name text only,
not the full service×asset_group×mode facet set; the `process_category_sampler.py` systemd timer failed to start
unattended on first install (manual invocation proven, the bridge cron `resource-monitor.sh` stays the safety net until
that's root-caused).

## Analysis path — DuckDB over `bq extract` (ad-hoc, power-user)

Alongside the UI's rolling 1h/4h/24h/1wk views (above), the FIVE `deployment_operational_data` tables
(`resource_samples`, `run_ledger`, `idle_spend`, `reap_events`, `process_samples`) are also directly queryable ad-hoc —
no server-side snapshot worker for this path (unlike `billing-cost-observability.md`'s automated 12h
`cost_snapshot_worker.py`; this data is small/cheap enough that BigQuery itself is a fine live query surface, so this
path exists for offline/local/bulk analysis the UI doesn't expose, not because BigQuery is too slow).

**Flow** (mirrors the `bq extract` → parquet → DuckDB pattern already proven for cost snapshots —
`deployment_api/scripts/cost_snapshot_worker.py` / `services/cost_observability/snapshot.py`):

1. Extract the table (or a query result materialized via `bq query --destination_table`) to GCS as parquet:

   ```bash
   bq extract --destination_format=PARQUET \
     central-element-323112:deployment_operational_data.resource_samples \
     gs://<scratch-bucket>/duckdb-extracts/resource_samples/*.parquet
   ```

2. Query it locally (or directly off GCS) with DuckDB — no BigQuery slot cost per query, no Python row materialization:

   ```bash
   duckdb -c "
     INSTALL httpfs; LOAD httpfs;
     SELECT vm_name, DATE(ts) AS day, avg(cpu_pct) AS avg_cpu
     FROM read_parquet('gs://<scratch-bucket>/duckdb-extracts/resource_samples/*.parquet')
     GROUP BY 1, 2 ORDER BY 2 DESC;
   "
   ```

   (GCS creds via `gcloud auth application-default login`, or a service-account key exported to
   `GOOGLE_APPLICATION_CREDENTIALS` — the same ADC path DuckDB's `httpfs` extension reads.)

**When to use this vs. the UI panel**: the UI's rolling-window view is the default surface for "what has this VM's
utilization been recently" (fast, no setup). This path is for questions the UI doesn't answer — a custom multi-VM join,
a longer-than-1wk historical query, exporting for a spreadsheet/notebook, or a one-off cross-table analysis (e.g.
`resource_samples` joined to `run_ledger` to correlate CPU spikes with run completions). Full design rationale + the
FOUR-signal schema: `/plans/archive/2026_07/deployment_durable_operational_data_bigquery_2026_07_21.md`.

## Anti-patterns (banned)

- A surface re-deriving umbrella/service/asset_group instead of reading `classify_deployment_target` / `CLOUD_RUN_JOBS`.
- A new Cloud Run scheduler tf or GCP launcher without a registry entry / durable-log streamer (the guards catch it —
  don't whitelist to dodge).
- A silent default umbrella (`classify_deployment_target` raises `UnclassifiedDeploymentError` — fix the classification,
  don't swallow).
