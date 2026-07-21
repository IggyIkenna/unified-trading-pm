---
doc_type: plan
title: deployment-ui — Deployments tab date-range filter, kind multi-select, service filter, target search (WS-2 + WS-3)
summary: >-
  "What was running between date A and B" on the Deployments tab. Live audit (2026-07-20) confirmed VM/registry rows
  carry a real start/end interval but ~95% of "running" rows are heartbeat-stale zombies, not truly live — the overlap
  formula must account for that. The archive read path is capped at 7 days server-side even though GCS retains 30; Cloud
  Run SERVICES carry no timestamp at all (an asymmetry vs their AWS ECS twin); several kinds (Job/Scheduler/Disk) have
  only a single timestamp or none. Also folds in the kind filter becoming multi-select, plus the previously-scoped
  service dropdown + target search box (WS-3) since they share the same filter bar.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-trading-library]
scope: [engineer]
tags: [deployment-ui, filters, search, date-range, observability]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
  - deployment_ui_cost_per_day_accuracy_2026_07_20.md
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  split from deployment_ui_observability_ux_tracker_2026_07_17.md WS-2+WS-3, audit run + operator decisions 2026-07-20
---

# deployment-ui — date-range filter, kind multi-select, service filter, target search

> **🟢 ACTIVE (operator 2026-07-21)** — flipped `active` as one of the first two plans dispatched to AO to test its
> reliability (the other is `deployment_ui_cost_per_day_accuracy_2026_07_20.md`). Must-do review fixes applied before
> activation (`unified-trading-library` added to `repos:` for the `deployment_registry.py` reference; `onHeaderClick`
> line ref corrected to `:821`). **This plan owns the `Deployments.tsx` shared-primitive extraction** that WS-5B
> consumes — so it is the correct one to run first. Remaining observability plans stay `draft` until these two complete
> and AO looks stable.

## Context — live audit findings (2026-07-20, read-only, no writes)

Full audit transcript available on request; the load-bearing facts:

- **VM/registry rows** — `started_at` is 100% populated at register time; `completed_at` is stamped at archive.
  **Live-measured**: 11,458 objects across `deployments/archive/` (2026-06-20 → 2026-07-20). **Correctness gap found**:
  219 registry rows currently read `status=running` (i.e. `completed_at: null`), but only **12** GCE instances are
  actually `RUNNING` right now — most "running" rows are heartbeat-stale zombies not yet reaped (reap threshold = 6h
  heartbeat-age, `deployment_registry.py:521-564`). Treating `completed_at: null` as "still running" for overlap math
  would badly overcount. **Design**: a row counts as "still running" for overlap purposes only while its heartbeat is
  fresh (<6h, matching the existing reap threshold); once stale, its `last_heartbeat_at` becomes the effective end for
  overlap math and the row is marked `basis=approx` — **reusing the same colour-only "approx" convention already decided
  for WS-1's partial-day figure and this plan's own last-run fallback rows**, so the whole table gets one consistent
  visual language for "this data point is uncertain."
- **Archive retention** — GCS lifecycle rule on `deployments/archive/` = 30-day TTL (**live-confirmed**: earliest
  day-prefix is exactly 30 days before latest). **But** the live inventory endpoint currently caps its own archive read
  at 7 days (`_ARCHIVE_WINDOW_DAYS=7`, `deployments_inventory.py:282`) — a date-range query needs its own direct
  day-partitioned read (bounded listing, single-walk discipline preserved) up to the real 30-day floor, not the existing
  7-day cap.
- **Unmanaged/adhoc VMs** — 0% lifecycle coverage; once terminated they leave no trace at all (only `creation_timestamp`
  while currently `RUNNING`). This is a hard limitation, not a bug to fix here — document it.
- **CLOUD_RUN_SERVICE** — carries **no timestamp field at all** today, unlike its AWS twin `ECS_SERVICE` (which has
  `last_run_at = updated_at or created_at`, `_aws_deployments.py:284`). This is a real asymmetry the audit surfaced.
- **CLOUD_RUN_JOB / AWS Batch** — the list endpoint only carries one `last_run_at` timestamp; a true start/end interval
  exists only on the per-job `/detail` `run_history`, too expensive to pull for every list row.
- **SCHEDULER** — single fire time (`last_attempt_at`), not an interval. **DISK/STATIC_IP** — no timestamp at all.
  **LAMBDA/CLOUD_FUNCTION** — `last_run_at` always `None`; only `last_modified_at` (deploy time) exists.
- **Kind filter today** — single-`<select>`, URL-backed (`?kind=`) but **client-side only** (unlike umbrella/cloud/
  status/asset_group/region, which are server params) — `Deployments.tsx:1209-1226`. 9 allowed values; only 6 are in the
  canonical UAC `DeploymentKind` enum (`SCHEDULER`/`DISK`/`STATIC_IP` are inventory-only literals).

## Decisions (operator, 2026-07-20)

1. **Scope** — one combined plan for WS-2 (date-range) + WS-3 (service filter, target search), audit run inline rather
   than as a separate gating plan.
2. **Cloud Run SERVICES (and any other always-on/no-interval kind)** — use last-deployed/last-updated as a proxy
   timestamp; sort them **last** in date-range-filtered results; keep them visible regardless of range with a clear
   "always-on" visual signal so it's obvious why they don't obey the filter like interval-backed rows do.
3. **`kind` filter** — becomes **multi-select** (currently single-select) so multiple kinds can be shown at once — this
   is how the operator will hide/show always-on services rather than the date filter silently dropping them.
4. **Approximate/fallback rows** (no lifecycle data, or heartbeat-stale zombies) — colour-only marker, same convention
   as WS-1's partial-day cost figure. No text label.
5. **Out-of-range requests** (range predates the 30-day archive floor) — explicit "no data before `<date>`" banner, not
   a silent partial result.

## Todos

- [x] ✅ [BACKEND] P0. VM/registry overlap query — `date_from`/`date_to` params on the inventory endpoint; overlap =
      `started_at ≤ B AND (completed_at ≥ A OR effective_end ≥ A)` where `effective_end` = `completed_at` if set, else
      `last_heartbeat_at` when heartbeat-stale (>6h, matching the existing reap constant), else open-ended (truly live).
      Heartbeat-derived rows get `basis: "approx"`. — deployment-api@ff5bb06 (`_vm_overlap_basis`/`_apply_date_range` in
      `deployments_inventory.py`; `DeploymentItem` gained `started_at`/`completed_at`/`last_heartbeat_at`/`basis`; 12
      new unit tests incl. route-level date_from/date_to wiring; `quality-gates.sh` green)
- [x] ✅ [BACKEND] P0. Archive range-read — bypass the existing 7-day `_ARCHIVE_WINDOW_DAYS` cap for date-range queries
      specifically; read day-partitioned `deployments/archive/<day>/` prefixes directly for the requested range (bounded
      listing only, no whole-corpus walk) up to the real 30-day GCS floor. Beyond 30 days → structured out-of-range
      response. — deployment-api@42191d9 (`_load_registry_entries_for_date_range`/`_archive_floor_date`; route merges
      the extra range-scoped VM rows, deduped against the cached 7-day census; response carries `archive_floor` +
      `date_range_out_of_range` for the UI banner; 8 new unit tests; `quality-gates.sh` green)
- [x] ✅ [BACKEND] P1. Unmanaged VMs + Cloud Run Job/AWS Batch/Scheduler — match via their single available timestamp
      (`last_run_at`/`last_attempt_at`) where no true interval exists, marked `basis: "approx"`. Document the per-kind
      support matrix (interval / single-timestamp / none) on the field. — deployment-api@fbb5ac9
      (`_single_timestamp_overlaps`/`_SINGLE_TIMESTAMP_KINDS` in `deployments_inventory.py`; covers unmanaged/AWS-EC2
      VMs + CLOUD_RUN_JOB (GCP + AWS Batch share the wire kind) + SCHEDULER; support matrix documented on
      `DeploymentItem.last_run_at`; kinds with no timestamp signal at all pass through unfiltered; 10 new unit tests;
      `quality-gates.sh` green)
- [x] ✅ [BACKEND] P1. Add a `last_deployed_at` field to the `CLOUD_RUN_SERVICE` list item (revision create_time) —
      closes the asymmetry vs `ECS_SERVICE` found in the audit; needed so always-on services can be sorted/labelled per
      decision 2. — deployment-api@1ff8699 (`CloudRunServiceStatus.last_deployed_at` in `_cloud_run_services.py`,
      sourced from the service's own `update_time`/`create_time` — a Tier-0 free win off the already-fetched list call,
      no extra RPC; mapped onto the EXISTING `DeploymentItem.last_modified_at` field in `_cloud_run_service_item` rather
      than a duplicate field, since it already carries "deploy time, distinct from last-invoke" for AWS Lambda; 6 new
      unit tests; `quality-gates.sh` green)
- [x] ✅ [UI] P0. Date-range picker on `/deployments`, URL-backed (`?date_from=&date_to=`), wired to the new backend
      params. — deployment-ui@31d862c (`DateRangeFilter` in `Deployments.tsx`; `date_from`/`date_to` added to
      `DeploymentInventoryFilters`/`getDeploymentInventory` in `deploymentApi.ts`; mock API filters on `last_run_at`
      with signal-less rows always passing through, honest-absence; both bounds independently clearable via one atomic
      `✕` — two sequential URL-param updates were found to race and clobber each other) | pw:L2 ✓ | regression:
      tests/smoke/deployments-page.spec.ts
- [x] ✅ [UI] P0. `kind` filter → multi-select (decision 3), URL-backed, same client-side filter model as today. —
      deployment-ui@234130a (`KindFilterChips` toggle-chip group replaces the single `<select>`; comma-separated
      `?kind=` URL, old single-value deep-link still works as a 1-element set; `cockpit.spec.ts`'s `.selectOption(...)`
      updated to click the chip) | pw:L2 ✓ | regression: tests/smoke/deployments-page.spec.ts
- [x] ✅ [UI] P1. Approx-row colour marker (decision 4) — reuse the WS-1 partial-day colour convention for any
      `basis: "approx"` row (heartbeat-stale VMs, unmanaged fallback, single-timestamp kinds). One consistent visual
      language across the whole table. — deployment-ui@e4f893e (`LastRunCell` in `Deployments.tsx` wraps the existing
      Last-Run column; amber `text-amber-400` when `item.basis === "approx"`, colour only, no text label, mirroring
      `CostCell`'s `cost_basis === "partial"` convention exactly;
      `DeploymentItem.started_at/completed_at/     last_heartbeat_at/basis` added to `deploymentApi.ts` — the backend
      shipped these fields (deployment-api@ff5bb06) but the UI type never declared them; mock fixture
      `funding-ensemble-paper-week` (a single-timestamp CLOUD_RUN_JOB) marked `basis: "approx"`) | pw:L2 ✓ | regression:
      tests/smoke/deployments-approx-marker.spec.ts
- [ ] [UI] P1. Always-on rows (CLOUD_RUN_SERVICE, any other no-interval kind) sort **last** in date-range-filtered
      results and stay visible regardless of range, with a distinct "always-on" visual treatment (decision 2) — visibly
      different from the approx marker, since this means "not applicable," not "uncertain."
- [ ] [UI] P1. Out-of-range "no data before `<date>`" banner (decision 5).
- [ ] [UI] P2. Service dropdown filter (WS-3) — options from distinct `service` values in the loaded inventory,
      URL-backed (`?service=`), client-side.
- [ ] [UI] P2. Target search box (WS-3) — free-text substring match on the Target column (`item.name`),
      case-insensitive, URL-backed (`?q=`), debounced, clears with an ✕.
- [ ] [UI] P1. **Extract the shared filter/sort primitives** — `FilterSelect` (`Deployments.tsx:878-908`),
      `StatusFilterChips` (`:924-961`), and the column-sort machinery (`SortKey` / `columnSortValue` / `compareByColumn`
      at `:256-320`, plus `onHeaderClick` at `:821` — note it lives in the table component, NOT co-located with the pure
      sort fns) are currently LOCAL to `Deployments.tsx` and not exported. Lift them into shared components (e.g.
      `src/components/filters/`) as part of this work, preserving behaviour, and re-consume them here. **This plan owns
      the extraction** — the WS-5 alerts-page rebuild (`deployment_ui_alerts_page_rebuild_2026_07_20.md`) declares
      `depends_on` this plan and consumes the extracted primitives rather than duplicating or re-editing this file
      (operator decision 2026-07-20 — one agent owns `Deployments.tsx`, no same-file collision, no divergent filter
      bars).
- [ ] [REVIEW] P1. Tests — overlap formula (fresh-running / heartbeat-stale / completed cases); archive bounded-read +
      30-day floor behaviour; out-of-range banner trigger; per-kind `basis` assignment; kind-multi-select +
      service/search URL param round-trip. `pw:L2 ✓` + cited regression spec for the UI pieces;
      `bash     scripts/quality-gates.sh` green in both deployment-api and deployment-ui.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'`) + flip todos same turn (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the per-kind date-filter support matrix, the approx-colour
      convention reuse, the always-on-service treatment, and the 7-day-cap-bypass/30-day-floor behaviour in
      `codex/05-infrastructure/deployment-observability.md`.

## Success criteria

- Date-range filter on `/deployments` returns correct overlap results for VM rows, honestly marks heartbeat-stale /
  fallback rows as approximate (colour only), and clearly banners requests older than the 30-day archive floor.
- Always-on kinds (Cloud Run services, etc.) never silently vanish from a date-filtered view — they sort last with a
  distinct "always-on" treatment, and the multi-select `kind` filter lets the operator hide them entirely if wanted.
- `kind` filter supports multiple simultaneous values.
- Service dropdown + target search box both work, URL-backed, deep-linkable.
- No new whole-corpus GCS walk introduced (day-partitioned archive reads stay bounded to the requested range).
- The filter/sort primitives are extracted into shared components and consumed here — so the WS-5 alerts rebuild can
  reuse them without editing `Deployments.tsx` or duplicating the UI.

## Progress Log

- **2026-07-20** — Split from `deployment_ui_observability_ux_tracker_2026_07_17.md` WS-2+WS-3, combined into one plan
  per operator decision. Ran the accuracy audit live (read-only, ADC creds, project `central-element-323112`) rather
  than gating on a separate audit plan — found the archive is 30-day-TTL'd (not 7, which is only the current endpoint's
  self-imposed cap), found the 219-running-vs-12-actually-running heartbeat-staleness gap that the naive
  `completed_at: null ⇒ still running` formula would have gotten wrong, and found `CLOUD_RUN_SERVICE` has no timestamp
  field at all (asymmetric vs its AWS `ECS_SERVICE` twin). Operator confirmed: always-on kinds get last-deployed as a
  proxy timestamp, sort last, visibly marked as always-on; `kind` filter becomes multi-select; approx rows use the same
  colour-only convention as WS-1; out-of-range requests get an explicit banner.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the per-kind date-filter
  support matrix, approx-colour convention, always-on-service treatment.
- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for the date-picker, multi-select,
  and filter additions.
- `codex/02-data/availability-manifest-and-data-status.md` — single-walk discipline (bounded day-partitioned archive
  reads only).
