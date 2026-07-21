---
doc_type: plan
title: Data Status UI Phase 2F — deployment-api/UI gap fixes
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-14"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-19** — 100% complete (5/5 items); deferred follow-ups migrated to named issue docs; preserved for
> archaeology.

---

title: Data Status UI Phase 2F — deployment-api/UI gap fixes (4 gaps from 6C smoke) created: 2026-05-14 author:
harsh-slot-7 type: active-plan status: active estimate_class: design estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8 locked_by: live-defi-rollout locked_since: 2026-05-14 migrated_from:
cross_asset_group_catalogue_audit_2026_05_10.md Phase 6C carry-forward

---

# Data Status UI Phase 2F — deployment-api/UI gap fixes

> **Source**: 4 gaps found during 6C UI-drilldown smoke (2026-05-14 slot 7 Day-3 Wave 1). Stack: deployment-api
> (port 8004) + deployment-ui (port 5183). Owned repos: `deployment-api` + `deployment-ui` + `unified-trading-pm`.

## Context

Phase 6C smoke confirmed the Data Status panel renders, all 5 asset groups visible in turbo breakdown, but 4 gaps
remain:

| GAP   | Description                                               | Status                                               |
| ----- | --------------------------------------------------------- | ---------------------------------------------------- |
| GAP-1 | `GET /api/data-status/honest-coverage` → 404              | ✅ UI graceful 404 shipped (Wave 2) — see below      |
| GAP-2 | `cross_asset` absent from breakdown/filter buttons        | ⬜ see § analysis (deferred to cross-service design) |
| GAP-3 | SPORTS/PREDICTION absent from Asset Groups filter buttons | ✅ DONE — see below                                  |
| GAP-4 | Asset group breakdown rows not interactive (no drilldown) | ✅ DONE — see below                                  |

## Gap analysis (pre-implementation read)

### GAP-1 — honest-coverage 404

**Finding**: Endpoint EXISTS at `deployment-api/deployment_api/routes/data_status.py:2218` — correctly mounted at
`/api/data-status/honest-coverage`. Returns 404 when no GCS file exists at
`gs://central-element-323112-honest-coverage/{date}/coverage.json`. The 404 from the smoke was EXPECTED — the cron VM
(`launch-measure-honest-coverage-vm.sh`) hasn't run yet for today's date in dev/staging. The endpoint implementation is
complete.

**Resolution**: No backend code change needed (endpoint correct as-is). Operational cron VM scheduling deferred to issue
doc. **Wave 2 follow-up (2026-05-14)**: shipped UI-side graceful handling at `deployment-ui@365c32f` —
`HonestCoverageCard.tsx` now renders neutral info card "Coverage data not yet computed for {date}." (Info icon, muted
text) instead of silently unmounting. Closes UI half of
`plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md`; cron VM scheduling half remains operator/Ikenna
territory.

### GAP-2 — cross_asset absent from filter

**Finding**: The Asset Groups filter buttons come from `GET /capabilities/service-asset-groups/{service}` which reads
`deployment-api/pm-configs/sharding.{service}.yaml`. For `instruments-service`, the sharding config (line 24) lists
`[CEFI, TRADFI, DEFI]`. The breakdown shows all groups from the API manifest response (5 groups when data exists).

`instruments-service` processes: CEFI, TRADFI, DEFI, SPORTS, PREDICTION (confirmed via
`deployment-ui/src/components/ServiceList.tsx:145`). It does NOT process `cross_asset` as a standalone shard dimension.
Adding a `CROSS_ASSET` filter button for instruments-service would be misleading (always returns 0 data). The
cross_asset group requires a dedicated service or an instruments-service extension that processes cross-asset instrument
definitions.

**Resolution**: File issue doc for cross-service design. Do NOT add CROSS_ASSET to instruments-service sharding config.
See `plans/active/issues/cross_asset_instruments_service_scope_2026_05_14.md`.

### GAP-3 — SPORTS/PREDICTION absent from filter

**Finding**: `sharding.instruments-service.yaml:24` has `values: [CEFI, TRADFI, DEFI]` but instruments-service also
processes SPORTS and PREDICTION (confirmed via `ServiceList.tsx:145` + UAC assets). Fix: add SPORTS, PREDICTION to
values list. No backend allowlist to update (data-status API accepts any asset_group string).

**Fix**: One-line YAML edit + QG run. ✅ DONE.

### GAP-4 — breakdown rows not interactive

**Finding**: Turbo view breakdown rows at `DataStatusTab.tsx:3718-3858` are plain `<div>` elements. Clicking a row
should select that asset group in the filter (equivalent to clicking the filter button). This allows operator to drill
into venue breakdown for that asset group.

**Fix**: Add `onClick={() => setSelectedCategories([catName])}` + `cursor-pointer` styling to the row header div at
line 3720. ✅ DONE.

## Plan todos

- [x] [AGENT] P0. **GAP-3** — Add SPORTS + PREDICTION to `sharding.instruments-service.yaml` values. **DONE 2026-05-14**
      PM@`a59d1571` — line 24: `[CEFI, TRADFI, DEFI, SPORTS, PREDICTION]`. pnpm build green.

- [x] [AGENT] P0. **GAP-4** — Add onClick to turbo breakdown rows in `DataStatusTab.tsx`. **DONE 2026-05-14**
      deployment-ui@`dd6c1cc` — row header div onClick + cursor-pointer + hover bg. Also fixed pre-existing TS errors:
      feature_families in DataTypeCheckResponse.venues inner type (client.ts) + DeployLiveClusterButton.test.tsx tuple
      cast. pnpm build green.

- [x] [AGENT] P1. **GAP-1** — File issue doc: honest-coverage 404 is expected (cron VM not yet scheduled). **DONE
      2026-05-14** PM@`a59d1571` — `plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md`.

- [x] [AGENT] P1. **GAP-2** — File issue doc: cross_asset not in instruments-service scope; needs design call. **DONE
      2026-05-14** PM@`a59d1571` — `plans/active/issues/cross_asset_instruments_service_scope_2026_05_14.md`.

## Temporary states + their canonical follow-up plans

None — all gaps resolved (2 code fixes, 2 issue docs).

## Deferred / follow-up

- Honest-coverage cron VM scheduling → `plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md`
- cross_asset instruments-service scope → `plans/active/issues/cross_asset_instruments_service_scope_2026_05_14.md`
- [x] ✅ [INFRA] P2. Wire cron VM launcher for the data-status refresh job: create a singleton-locked launcher under
      `deployment-service/scripts/vm/`, register prefix in `VM_PREFIX_TO_BUCKET` (vm_zombie_watchdog.py), launch with
      `DEPLOYMENT_ENV` set. **DONE 2026-05-18** — deployment-service@2026-05-15 (slot-2 shipped):
      `launch-honest-coverage-vm.sh` + `launch-measure-honest-coverage-vm.sh` + `setup-honest-coverage-scheduler.sh` all
      exist. Watchdog has `honest-coverage-` + `measure-honest-coverage-` prefixes registered. `DEPLOYMENT_ENV` handled
      via `DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"`. Cloud Scheduler activation requires Ikenna owner account — see
      `setup-honest-coverage-scheduler.sh` comment; Cloud Run Job `honest-coverage-daily-launcher` was created
      2026-05-15.

## DONE-2026-05-18 — Plan close (slot-7)

All 5 todos resolved:

- GAP-3 SPORTS/PREDICTION filter: deployment-api PM@a59d1571
- GAP-4 breakdown rows interactive: deployment-ui@dd6c1cc
- GAP-1 honest-coverage 404 issue doc: PM@a59d1571
- GAP-2 cross_asset scope issue doc: PM@a59d1571
- INFRA cron VM launcher: deployment-service@2026-05-15 (slot-2); Cloud Scheduler activation = Ikenna operator task
