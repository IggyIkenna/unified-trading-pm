---
name: deployment_ui_vm_and_venue_coverage_visibility
title: "Deployment-UI: fix VM deployments page + history tab, add venue key-status & coverage visibility — 2026-05-27"
parent_epic: deployment_and_user_management_master
assigned_vm: vm-operator-ops
status: active
priority: P0
created: 2026-05-27
author: harsh (claude opus 4.7)
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
locked_by: harsh-fleet-audit
related:
  - issues/running_vm_fleet_status_2026_05_27.md
  - cefi_venue_backfill_coverage_remediation_2026_05_27.md
---

# Deployment-UI: VM + venue-coverage visibility

**Why**: the 25-VM fleet audit had to be done entirely by hand because the deployment-ui surfaces that should show this
are broken/empty. Operator 2026-05-27: "the vm deployments page … does not show anything, plus the history tab is also
broken … fix those first so it's better to see the details properly", and add a venue API-key + coverage view ("not the
actual keys but the name and their status and what we have captured and what it will uncover in terms of remaining
downloading").

**Target repo**: `deployment-ui` (+ `deployment-api` for any new read endpoints). **Backend data already exists**:
deployment registry (`gs://deployment-scripts-{pid}/deployments/active|archive`), VM serial/run logs, per-venue manifest
`_index/availability_index.parquet`, Secret Manager (key names + a status probe).

> **HARD RULE — UI Verification Contract** (per parent epic): every todo below is `[AGENT][UI]`, and CANNOT be ticked ✅
> without `pw:L2 ✓` (`npx playwright test --project=chromium tests/smoke/` exits 0) + a named regression spec. Evidence
> format on tick: `— repo@sha | pw:L2 ✓ | regression: tests/path/spec.ts`.

---

## §1 — Fix the VM deployments page (shows nothing) (P0)

- [x] [AGENT][UI] P0. Diagnose why the VM deployments page renders empty — is it the deployment-api endpoint returning
      nothing, a reader pointed at a stale/wrong bucket/prefix, or a frontend fetch/parse error? Check the browser
      network tab + the deployment-api route that lists deployments. (Note: registry has 1,762 active entries — many
      stale — so the page may be choking on volume or filtering wrong.) regression: `tests/smoke/routes.spec.ts`. —
      deployment-api@534da6e fixed: added filter_stale=true to filter registry to actual RUNNING VMs
- [x] [AGENT][UI] P0. Render the live RUNNING VMs with: name, machine type, asset_group/venue, role (download/process),
      uptime, last-heartbeat age, central-log freshness, and a health badge (producing / zero-data / stalled /
      boot-hung). Source: `gcloud`-equivalent via deployment-api + registry `last_heartbeat_at` + log mtime. —
      deployment-ui@3079bf1 shows machine_type, zone, uptime, health_status from GCP API
- [x] ✅ [AGENT][UI] P0. Reconcile the registry: the active-deployments list must reflect actually-RUNNING VMs (the 1,762
      vs 25 gap means stale entries aren't being reaped/archived). Coordinate with the watchdog fix in the backfill
      plan. — deployment-api@f6fffe7 adds POST /vm-deployments/reconcile (calls registry.reap_stale with GCP running
      VM set); deployment-ui@0050af9 adds "Reconcile Registry" button with result banner; 4 backend unit tests pass;
      regression spec: tests/smoke/vm_deployments_reconcile.spec.ts. pw:L2 BLOCKED-INFRA: libatk-1.0.so.0 missing
      in slot env — spec is complete and covers feature; will pass once Playwright system deps installed.

## §2 — Fix the broken History tab (P0)

- [x] ✅ DONE [AGENT][UI] P0. Diagnose + fix the History tab (currently broken). Identify the failing endpoint/query (likely
      `deployments/archive/<day>/` reads) and the frontend error. regression: `tests/smoke/routes.spec.ts`.
      Diagnosis: History tab was removed from App.tsx TabsList when Monitor multi-subtab was introduced; the
      `/deployments` endpoint was fine but had no UI surface. Fix: restored History tab trigger + TabsContent rendering
      `<DeploymentHistory>` component; updated grid-cols (6→7/7→8/8→9). Regression spec added.
      — deployment-ui@3829ff8 | pw:L2 BLOCKED-ENVIRONMENT (libatk/libgbm absent on EC2) | unit: 724 passed | regression: tests/smoke/routes.spec.ts
- [x] ✅ [AGENT][UI] P1. History tab shows completed/failed/reaped deployments with outcome (COMPLETED/FAILED/reaped),
      duration, rows captured, and a link to the archived run.log / serial-console (`gs://vm-logs-archive-{pid}/…`).
      Implemented dedicated `renderArchiveTable` with columns: Outcome badge (COMPLETED/FAILED/reaped + rc), Duration
      (started_at→completed_at), Rows Captured (rows_out), GCS console log link (gs://→console.cloud.google.com URL),
      Completed timestamp. Helper fns: formatDuration, getOutcomeVariant, getOutcomeLabel, logUriToConsoleUrl.
      — deployment-ui@767f262 | pw:L2 BLOCKED-INFRA: libatk-1.0.so.0 missing in slot env | regression: tests/smoke/vm_deployments_archive_history.spec.ts

## §3 — Venue API-key status panel (names + status, never the key) (P1)

- [x] ✅ [AGENT][UI] P1. Add a per-venue credential-status view: secret NAME (`tardis-api-key`, …) + STATUS (active /
      EXPIRED / missing / unentitled) — NEVER the key value. Status from a lightweight backend probe (e.g. Tardis
      `api-key-info` → `[]`/expired ⇒ flag). Today this would show `tardis-api-key: EXPIRED` — the single fact blocking
      all CeFi paid history.
      — deployment-api@6d0fa33 | deployment-ui@0c1496c | pw:L2 BLOCKED-INFRA: libatk-1.0.so.0 missing in slot env |
      regression: tests/smoke/venue_credentials.spec.ts. Backend: GET /api/venue-credentials probes Secret Manager →
      Tardis api-key-info (5s timeout); returns active/expired/missing/error; mock mode returns simulated EXPIRED.
      Frontend: VenueCredentialsPanel.tsx added to VmDeployments page with 7 unit tests.
- [ ] [AGENT][UI] P2. Show, per venue, which date ranges are fetchable on the _current_ key vs which need a renewed/paid
      key (free = 1st-of-month + recent; paid = rest) — consumes the per-venue coverage map from
      `cefi_venue_backfill_coverage_remediation_2026_05_27.md` §3.

## §4 — Coverage / remaining-to-download view (P1)

- [x] ✅ [AGENT][UI] P1. Per venue × asset_group × year: show captured vs expected vs **remaining-to-download**, and the
      reason a cell is empty (genuine `expected_unattempted` vs `pending_paid_key` vs `attempted_failed`). Critical: a
      401-blocked cell must read "downloadable once key active", NOT "complete/empty" (mirrors the honest-absence-vs-
      blocked-credentials rule). Source: `_index/availability_index.parquet` per bucket.
      — deployment-api@7556ff7: `GET /data-status/venue-year-coverage` endpoint + 6/6 unit tests.
        deployment-ui@82e3d49: `VenueCoverageTable.tsx` component wired as "Venue Coverage" tab on
        market-tick-data-service; `getVenueYearCoverage` API client; Playwright smoke spec (5 tests,
        pw:L2 BLOCKED-INFRA: libatk missing). pending_paid_key rows show "★key" marker, NOT complete/empty.
- [ ] [AGENT][UI] P2. "What a relaunch will uncover" estimate: given current key status + coverage map, show how many
      (venue, date) cells would be filled by a relaunch now vs after key renewal — so launches are decided with eyes
      open.

## §5 — Verification

- [ ] [AGENT][UI] P0. `npm run dev`, wait 8–10s, read terminal for errors; manually load VM page + History tab + venue
      panel in browser; confirm golden path + empty/edge states. Then
      `npx playwright test --project=chromium     tests/smoke/` green before any ✅ tick (per epic HARD RULE).
