---
title: "Unified Deployment & Health Observability Cockpit (live/paper/batch + fleet health)"
created: 2026-06-23
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 13
locked_by: live-defi-rollout
locked_since: 2026-06-23
related_plans:
  - deployment_observability_parity_live_batch_paper_2026_06_22.md
  - deployment_ui_monitoring_pane_2026_06_19.md
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
  - vm_launcher_durable_log_observability_2026_06_19.md
  - data_feed_sla_registry_and_active_self_healing_2026_06_19.md
  - issues/dp_event_pubsub_delivery_gap_2026_06_22.md
  - issues/github_actions_billing_wall_2026_06_11.md
---

# Unified Deployment & Health Observability Cockpit

> **Operator intent (2026-06-23)**: "Last-step monitoring system like we built for CI — for live, paper, and batch — so
> we can see current status of everything: live/batch deployment, paper, AND health-related (manifest aggregators, VM
> zombie detection, every VM accounted for in GCP+AWS, agent-orchestrator + GitHub health, billing). **deployment-ui is
> the right place.** Take what's already there rather than blind builds — just separate paper/batch/live overviews as
> slightly different dynamics; Cloud Run + VM + AWS comparable. Force every deployable service to identify itself for
> monitoring or it fails to deploy / fails quality gates. The premise: Slack alerts surface an issue → operator clicks
> into the deployment-UI monitoring → drills into logs → can click through to the existing deploy page to redeploy."

## Reuse-first: what ALREADY EXISTS (do NOT rebuild — extend)

This initiative is ~70% wiring of shipped primitives. Pre-audit (2026-06-23, two fan-out surveys):

**deployment-ui (Vite + React 19 + React Router + Radix + Recharts + SSE):**

- `/deployments` — **LIVE/BATCH/PAPER umbrella tabs + GCP/AWS cloud toggle** + per-umbrella summary headers
  (`Deployments.tsx`)
- `/vm-deployments` + `/vm-deployments/:id` — VM inventory + per-VM events/logs
- `/deployments/:name` — per-target event timeline drill-down
- `/ops/live-deployments`, `/ops/vms/:vm`, `/ops/costs`, `/safety-ops`, `/chaos`
- `/repos` (RepoCi), `/alerts`, `/fleet/infra`, `/fleet/git`
- Deploy console: `DeployForm.tsx` + `DeployTrigger.tsx` (`POST /api/deployments`, dry_run, shard filtering)
- **SSE log streaming EXISTS**: `useDeployEventStream.ts` (EventSource, auto-reconnect, 60s heartbeat) +
  `StreamingLogsPanel.tsx` + `useVmWebSocket.ts`
- Tests: `tests/{smoke,e2e,visual}` (Playwright, mock port 5199) + `tests/{unit,integration}` (Vitest) — **the UI
  playwright gate applies**

**deployment-api (FastAPI :8004):**

- `GET /api/deployments/inventory` + `/api/deployments/umbrella/{u}/summary` — backed by `DeploymentsRegistry` (GCS VM
  state) + `CLOUD_RUN_JOBS` + `classify_deployment_target` + Cloud Run execution enrichment + **AWS census (EC2 + Batch
  Fargate, Phase 5 wired)**
- `GET /api/deployments/{id}/events` + `/stream` (SSE) — backfill VM event stream
- Health: `/api/health/detailed`, `/api/vm/{vm}/health`, `/api/fleet/vm-census` (running/expected/zombie/OOM/stopped),
  `/api/fleet/infra-vm-health` (proxy to agent-orchestrator), `/api/alerts` (unified ledger: CI + vm_down +
  consolidator_down + git_health + worker_liveness)
- CI: `/api/repo-ci/overview`, `/api/repo-ci/fleet-git-health`, `/api/repo-ci/alerts`
- Cost/budget: `/api/costs/daily`, `/api/repos/gh-rate-limit`
- Log stream: `GET /api/logs/stream/{target_ref}` — **backfill VMs only; live clusters (Cloud Run/GKE) return 501**

**deployment-service primitives:**

- Registries: `cloud_run_job_registry.CLOUD_RUN_JOBS`, `deployments_registry.DeploymentsRegistry` (GCS active+archive,
  full BoM/exit_code/heartbeat), `launcher_registry.resolve_launcher_for_vm`, `classify_deployment_target` (raises
  `UnclassifiedDeploymentError`)
- Monitors: `vm_zombie_watchdog.py` (+ `_aws.py`), `heartbeat_stall_watcher.py`, `exit_code_fleet_monitor.py`,
  `data_pipeline_monitors/{escalation,meta_watchers,deadman_poster}.py`
- Consolidator health: `assert_consolidator_healthy(bucket)` + `CONSOLIDATOR_DOWN` watchdog
- QG guard: `tests/unit/test_cloud_run_job_registry_guard.py` — every scheduler-tf job + VM prefix classifies
  (CI-failing). STEP 5.61/5.62 in `base-service.sh` enforce `ServiceBootstrap` + `make_health_router`.

## The REAL gaps (this plan's scope — net-new only)

1. **No single health rollup.** Zombie census, consolidator staleness, data-status coverage, CI alerts, GH budget,
   billing each live behind a different endpoint/page. Nothing answers "is everything healthy right now?" in one
   call/pane.
2. **Umbrella tabs are one matrix shape** — live/paper/batch are surfaced but not as their _distinct dynamics_ (live =
   uptime/heartbeat-freshness/positions-feed health; batch = run progress/coverage %/exit-code distribution; paper =
   reconciliation/determinism drift).
3. **Live-cluster log streaming is 501** — operator wants to stream+drill logs for live/long-lived services, not just
   backfill VMs.
4. **No cross-cloud "every VM accounted for" reconciliation** — per-cloud watchdogs run independently; nothing asserts
   every running GCP+AWS instance maps to a known/registered/expected deployment (unknown instance = its own alert
   class).
5. **Agent-orchestrator + GitHub + billing not first-class health tiles** — partial endpoints exist but aren't
   consolidated; no GH Actions minutes / GCP billing wall surface (issue `github_actions_billing_wall_2026_06_11.md`).
6. **No service self-registration-for-monitoring enforcement** — the guard covers scheduler-tf jobs + VM prefixes, but a
   **long-lived deployable service** can ship without declaring itself to the monitoring inventory. Operator wants:
   declare-or-fail-QG/deploy.

## Phased Execution DAG

> **Sequencing override (operator 2026-06-23)**: **UI-SCAFFOLD-FIRST.** Build the FULL page/pane/tab information
> architecture in deployment-ui with placeholder data FIRST — so the operator sees the format + where everything lives —
> THEN drill into completion (real backend wiring) pane-by-pane. So Phase 0 (scaffold) precedes the backend phases; each
> later phase REPLACES a pane's placeholder with its real endpoint. Each phase is independently shippable + QG-green.

### Phase 0 — Full cockpit scaffold with placeholders (the IA the operator approves first) — deployment-ui

- [x] ✅ [UI] P1. New top-level **`/cockpit`** section (nav entry) — the monitoring landing `HealthOverview` with the
      full tile grid as PLACEHOLDERS: Live / Batch / Paper deployment summaries, Fleet VMs (GCP+AWS census), Manifest
      consolidators, Data coverage, CI/repos, Agent-orchestrator, GitHub health, Billing/cost, Alerts. Each tile is a
      color-coded card with placeholder status + a working drill-down link. — deployment-ui@be04198 | pw:L2 ✓ |
      regression: tests/smoke/cockpit.spec.ts (`Cockpit.tsx` Overview tab + Header `nav-cockpit` link).
- [x] ✅ [UI] P1. Three umbrella **dynamics overview** panes with their distinct column presets as placeholder tables
      (live=uptime/heartbeat/feed-health; batch=progress/coverage/exit-code; paper=recon-drift/determinism-ε).
      Implemented as deep-linkable `?tab={live,batch,paper}` query-param tabs (matches the existing `/deployments`
      URL-param pattern — cleaner than path sub-routes, same deep-link). — deployment-ui@be04198 | pw:L2 ✓ | regression:
      tests/smoke/cockpit.spec.ts.
- [x] ✅ [UI] P1. **Drill panes** scaffold (placeholder): Fleet (`?tab=fleet`, every-VM-accounted-for reconciliation
      table + 3 alarm cards), Consolidators (`?tab=consolidators`, per-AG cards), Health (`?tab=health`,
      orchestrator/github/billing cards) — each a titled pane cross-linking to the EXISTING `/deployments`,
      `/fleet/infra`, `/alerts`, `/ops/costs`, `/repos` pages rather than duplicating them. — deployment-ui@be04198 |
      pw:L2 ✓ | regression: tests/smoke/cockpit.spec.ts. (The per-row "Stream logs"/"Redeploy" affordances land with the
      real table rows in Phase 2/3 — see next item.)
- [ ] [UI] P1. Wire the alert→cockpit→logs→redeploy NAV path end-to-end on placeholders (the per-target "Stream logs" +
      "Redeploy" buttons route correctly even before data is real), so the operator can walk the whole flow.
      **Partial**: cockpit is reachable + every tile drills to its source page; the Stream-logs/Redeploy buttons attach
      to the dynamics table rows in Phase 2/3. `[UI]` — pw:L2 + regression covering the route walk.
- [x] ✅ [UI] P1. **IA reshape per operator review (2026-06-23)**: Overview→**Health** (the landing tile grid IS the
      health home; removed the redundant standalone Health tab); new **Deploy** tab (batch/live/**paper** entry points —
      `DeployForm` already supports paper via `runtime_profile` × GCP/AWS; embedded form in Phase 2); **Fleet** now
      accounts for the agent-orchestrator control-plane VMs (Purpose column) per "fold orchestrator into Fleet";
      **Billing** tile is tri-cloud **GitHub+GCP+AWS**. Tabs: Health · Deploy · Live · Batch · Paper · Fleet ·
      Consolidators. — deployment-ui@b9be2da | pw:L2 ✓ | regression: tests/smoke/cockpit.spec.ts.
- [ ] [UI] P1. **Make `/cockpit` the DEFAULT page of the deployment UI (operator 2026-06-23).** A bare `/`→`/cockpit`
      redirect is NOT viable as-is — it broke 81 smoke specs that assume `/` renders the home shell (ServiceList +
      LandingTabs default Overview tab). Do it as a migration: give the home shell its own explicit path (e.g. `/home`),
      redirect `/`→`/cockpit`, and migrate the ~handful of landing-assumption specs (app.spec / routes.spec /
      url-sync.spec + the goto("/") service-item specs) to the new home path. `[UI]` — pw:L2 (FULL `tests/smoke/`
      green) + regression.

### Phase 0.7 — Consolidate the deployment UI into the cockpit (cockpit = the app) — deployment-ui

> **Operator review (2026-06-23)**: "The top bar is doing two jobs. The cockpit is the landing — so the Cockpit nav
> button is redundant; Deployments is already in the cockpit; fold the rest in too. The top bar should stay GENERIC:
> DEV/STAGING/PROD badge · LIVE/MOCK DATA · Clear Cache · API status · GCP/AWS · version. And stream all alerts + VM
> logs (the stuff already going to Slack + coming out of the VMs) in ONE place inside the cockpit." Operator confirmed
> ALL wired surfaces fold in (Repos CI, Chaos, Research-launch ML/Strategy/Exec-BT, Safety-Ops) — nothing dropped.
> Ordering is FOLD-FIRST, then strip the nav (never orphan a surface).
> `the data badge "LIVE" means live-vs-MOCK DATA, not trading-live` → relabel.

> **🧭 CURRENT STATE — START HERE (fresh-agent handoff, 2026-06-23, deployment-ui@52c9f18)**: The cockpit SHELL is done
> — `/cockpit` is the default page, top bar is pure-utility, badge relabeled, and every surface is reachable from the
> cockpit (Health tiles + a "Consoles & tools" link strip on the Health landing). **What's left is turning the cockpit
> from a NAV HUB into an embedded APP**: the cockpit tabs (Live/Batch/Paper/Fleet/Consolidators) + the Consoles links
> currently NAVIGATE AWAY to the existing pages; the remaining todos fold those pages' COMPONENTS _inside_ cockpit tabs
> (render in-place, not navigate) + replace the placeholder tables with real data, + build the net-new unified "Alerts &
> Logs" stream. Then the Phase 1+ backend (`/api/health/overview` rollup, consolidator drill-down, fleet reconciliation,
> live-cluster log streaming, hard-fail monitoring-registration QG). **Gotchas the next agent MUST know**: (1) the UI
> playwright gate (`pw:L2`) flakes under multi-worker load on the venue\_\* tests — verify with
> `npx playwright test --project=chromium tests/smoke/ --workers=1 --retries=2` (CI parity → green); a default-worker
> run shows false venue flakes. (2) **NEVER `prettier --write src/ tests/`** tree-wide — it reformats ~150 foreign files
> (version drift) and you'll spend a cycle reverting; prettier ONLY your named files. (3) embedding a full-page
> component as a tab: watch nested `<main>` + the `useSearchParams` `?tab=` collision (the cockpit owns `?tab=`). (4)
> ship via `quickmerge --agent --files '<your files>'` — there's a foreign-dirty
> `.github/workflows/quality-gates-v2.yml` in the tree that is NOT yours, never stage it.

- [x] ✅ [UI] P1. **Relabel the data-mode badge** `LIVE`→`LIVE DATA` (MOCK chips already say MOCK) so it can't read as a
      deployment/trading mode. — deployment-ui@99863af | pw:L2 ✓ (app.spec + nav_and_header green) | regression:
      tests/smoke/nav_and_header.spec.ts. (Note: the playwright suite runs in MOCK mode so the Header shows "MOCK (UI)";
      the "LIVE DATA" label shows in real cloud-data mode.)
- [x] ✅ [UI] P1. **Make `/cockpit` the default landing + give the per-service home shell its own path** (`/home`):
      `/`→`/cockpit` redirect (App.tsx `<Navigate>`); the home shell (ServiceList + deploy/monitor tabs) lives at
      `/home` (`ServiceUrlSync` LANDING_PATHS + `LandingTabs` overview route + cockpit DeployTab link);
      `/repos /alerts /epics     /fleet /service/*` unchanged. The **header logo is now the way home** (`nav-cockpit`)
      so the redundant "Cockpit" button is removed — top bar is PURE utility. Migrated ~30 landing specs
      (`goto("/")`→`goto("/home")`) + App.test (`beforeEach` /home) + repos-tab/url-sync URL assertions. —
      deployment-ui@52c9f18 | pw:L2 ✓ (FULL tests/smoke 270 green at CI parity: `--workers=1 --retries=2`; multi-worker
      shows ~7 venue-test flakes, untouched by this change) | orphan-audit green | regression:
      tests/smoke/cockpit.spec.ts (`/`→`/cockpit` redirect test).
- [ ] [UI] P1. **Fold Deployments + VM Deployments + Live Ops into the cockpit** Live/Batch/Paper/Fleet tabs with REAL
      data (replace the placeholder tables with the existing `Deployments`/`VmDeployments` inventory + the Live-Ops WS
      log tail). `[UI]` — pw:L2 + regression.
- [ ] [UI] P1. **Fold Repos CI** → cockpit **CI** tab (reuse `RepoCi`). `[UI]` — pw:L2 + regression.
- [ ] [UI] P1. **Fold Alerts → cockpit "Alerts & Logs" tab + build the UNIFIED STREAM** (operator: one place streaming
      Slack-bound alerts + VM logs). Net-new: the Alerts page today is CI-only 60s-poll; add the non-CI alert classes
      (vm_down/consolidator_down/git_health/worker_liveness — the DP\_\* Slack alerts) + a live VM-log tail, in one
      timeline. `[UI]` — pw:L2 + regression.
- [ ] [UI] P2. **Fold Chaos** → cockpit tab (failure-injection / resilience testing, non-prod). `[UI]` — pw:L2 +
      regression.
- [ ] [UI] P2. **Fold Research-launch (ML/Strategy/Exec-BT)** → a cockpit **"Launch"** tab. `[UI]` — pw:L2 + regression.
- [ ] [UI] P2. **Fold Safety Ops** → cockpit tab (UI exists; backend is a STUB — wire `/safety-ops/*` routes later).
      `[UI]` — pw:L2 + regression.
- [x] ✅ [UI] P1. **Strip the top bar to UTILITY-ONLY**: top bar is now DEV/STAGING/PROD badge · LIVE/MOCK DATA · Clear
      Cache · API status · GCP/AWS toggle · version + a single **Cockpit** entry. The 10 page-nav links (VM-Deps,
      Deployments, Chaos, Live-Ops, Repos-CI, Alerts, Safety-Ops, ML, Strategy, Exec-BT) moved into the cockpit (status
      tiles + a "Consoles & tools" section), so every surface stays reachable (orphan-audit green); the nav-click specs
      were migrated to navigate via the cockpit. — deployment-ui@7e698d6 | pw:L2 ✓ (FULL tests/smoke 269 green) |
      regression: tests/smoke/{nav_and_header,alerts-page,deployments-page,repos-tab,url-sync,cockpit}.spec.ts. (The
      lone-remaining "Cockpit" button is removed when the cockpit becomes the literal default page — the next todo.)

### Phase 1 — Health rollup backend (foundation, pure reuse) — deployment-api

- [ ] [API] P1. Add `GET /api/health/overview` to deployment-api aggregating the EXISTING signals into one envelope:
      fleet vm-census (running/zombie/OOM/stopped), consolidator staleness per asset_group, data-status coverage % per
      AG, open-alert counts by class (from `/api/alerts`), GH rate-limit budget, today's cost. Reuse the existing route
      helpers — NO new data sources. Shape:
      `{ overall: ok|degraded|critical, tiles: [{ id, label, status, value, detail_href }] }`. (deployment-api
      `routes/health_overview.py`)
- [ ] [API] P1. Add `GET /api/health/consolidator` — manifest-consolidator health drill-down per AG (index age, per-VM
      shard fallback active?, last successful run) via `assert_consolidator_healthy` internals. Replaces today's binary
      up/down. (deployment-api)
- [ ] [TEST] P1. Unit tests for both endpoints with mocked registry/census/alert sources; degraded/critical rollup logic
      covered. (deployment-api `tests/unit/`)

### Phase 2 — Live/paper/batch dynamics + Health pane — deployment-ui

- [ ] [UI] P1. New `/health` route + `HealthOverview` page rendering the Phase-1 rollup tiles (color-coded, each links
      to its drill-down). Reuse `ApiClient` + existing card/badge components. `[UI]` — pw:L2 + regression spec required.
- [ ] [UI] P1. Give the existing `/deployments` umbrella tabs **dynamics-specific columns** per umbrella (reuse
      `DeploymentItem`): LIVE → uptime / heartbeat-age / feed-health; BATCH → captured_progress / coverage% / exit-code;
      PAPER → recon-drift / determinism-ε / last-recon. One inventory source, three column presets. `[UI]` — pw:L2 +
      regression.
- [ ] [UI] P2. Wire Slack-alert deep-link landing: alert deep-links already point at `/deployments/{name}` — ensure the
      drill-down page surfaces the alert context + a "Stream logs" button + a "Redeploy" button that routes to the
      EXISTING `DeployForm` prefilled for that target. `[UI]` — pw:L2 + regression.

### Phase 3 — Live-cluster log streaming (close the 501) — deployment-api + deployment-ui

- [ ] [API] P2. Implement live/long-lived-cluster log tail in `routes/log_stream.py` (currently 501): stream Cloud Run
      execution + service logs via `gcloud logging` tail / Cloud Logging API (cloud-agnostic via UCI; AWS → CloudWatch
      Logs). SSE, same envelope as the backfill path so the UI hook is unchanged. (deployment-api)
- [ ] [UI] P2. Point `StreamingLogsPanel` / `useDeployEventStream` at the unified log-stream endpoint for any target
      kind (VM backfill / Cloud Run job / live service), with a target-type switch. `[UI]` — pw:L2 + regression.

### Phase 4 — Cross-cloud reconciliation + self-registration enforcement (gated)

- [ ] [API] P2. Add `GET /api/fleet/reconciliation` to deployment-api — cross-cloud: every RUNNING GCP+AWS instance/job
      reconciled against `DeploymentsRegistry` ∪ `CLOUD_RUN_JOBS` ∪ expected-from-launcher set. Surface UNKNOWN (running
      but unregistered) + EXPECTED-MISSING (registered/scheduled but not running) as distinct rows. (deployment-api,
      reuses both watchdog censuses)
- [x] ✅ [SCRIPT] P2. **Monitoring-registration declaration**: define the machine-readable "this deployable service
      registers for monitoring" surface (the natural home: a `DeploymentTarget`/service entry the inventory already
      classifies + a required `make_health_router(data_freshness=...)` self-report). Decide minimal marker that proves a
      long-lived service is inventory-visible. (deployment-service + UAC if a registry entry is needed) —
      deployment-service@0ad6b81: new `deployment_service/monitored_services.py` (`MONITORED_SERVICES` of 14 long-lived
      services — all 12 data-plane svcs `data_freshness=True` + deployment-api/unified-trading-api gateways `False`;
      each LIVE-classified via `classify_deployment_target`; accessors `is_service_monitored` +
      `monitored_service_names`) + `tests/unit/test_monitored_services_registry_guard.py` (8 tests, GREEN on arrival —
      every service/api-service/api repo registered). QG green (`--no-fix`, sentinel c66b5b3). batch-service repos
      register as Cloud Run JOBS, not here.
- [ ] [SCRIPT] P3. **QG enforcement = HARD-FAIL (operator 2026-06-23)**: extend `base-service.sh` (new STEP) + a guard
      test parallel to `test_cloud_run_job_registry_guard.py` so a deployable service lacking the
      monitoring-registration marker **fails QG/deploy outright** (not a ratchet). **Land green, not red**: in the SAME
      unit, register every existing deployable service so the check passes fleet-wide on arrival — the hard-fail then
      only bites NEW unregistered services. (Registering-all-first is the discipline; the operator wants the END state
      to be hard-fail, not a fleet-redding flip.) Rollout via `base-service.sh` (fleet-wide). (PM
      `quality-gates-base/base-service.sh` + deployment-service guard test)
- [ ] [API] P3. GH Actions minutes / billing wall tile: surface GH Actions usage + GCP billing threshold in
      `/api/health/overview` (extends `gh-rate-limit` + `costs/daily`; ref issue
      `github_actions_billing_wall_2026_06_11.md`). (deployment-api)

### Phase 5 — Codex SSOT + plan close

- [ ] [DOC] P2. Update `codex/05-infrastructure/deployment-observability.md`: add the health-rollup endpoint,
      live/paper/batch dynamics presets, live-cluster log streaming, cross-cloud reconciliation, and the
      monitoring-registration enforcement contract. Add `codex/05-infrastructure/data-pipeline-alerts.md` cross-ref for
      the alert→cockpit→logs→redeploy flow.
- [ ] [DOC] P3. Master-plan continuous-verification column entry + archive readiness scan.

## Success Criteria (per phase)

- **P1**: both endpoints return real aggregated data on the live deployment-api; unit tests green; QG green
  (deployment-api).
- **P2**: `/health` + dynamics columns render against real endpoints; `pw:L2 ✓` + regression specs cited; no
  `any`/`@ts-ignore`.
- **P3**: live-service log tail streams in the UI (proven on one live Cloud Run service); backfill path unchanged.
- **P4**: reconciliation endpoint flags a deliberately-unregistered test instance; QG ratchet lands at warn (baseline
  captured), fleet count trends to zero before any hard-fail flip.
- **P5**: codex reflects shipped reality; no orphan `parent_epic`; archive scan clean.

## Anti-patterns (banned)

- Re-deriving umbrella anywhere instead of `classify_deployment_target` (existing rule).
- A second inventory/registry — there is ONE (`DeploymentsRegistry` + `CLOUD_RUN_JOBS`); the cockpit READS it.
- Hard-failing the fleet QG on self-registration before the ratchet baseline is zero.
- Blind UI rebuild — every pane extends an existing component/route + reuses `ApiClient`.
- A `*_SUMMARY.md`/handoff doc — progress lives in this plan's todos + Progress Log.

## Interim (operator-stated)

Until this ships (~couple of days), **Slack alerts are the live monitoring surface** — fix issues as they arrive. The
DP\_\* → Slack delivery is live end-to-end (issue `dp_event_pubsub_delivery_gap_2026_06_22.md` resolved 2026-06-22).

## Progress Log (autonomous finish dispatch — 2026-06-23)

> Append-only journal (rule 6). This IS the handoff doc — no `*_SUMMARY.md`. A compressed future-me resumes from here.

- **2026-06-23 — boot.** Autonomous finish dispatch started (Opus 4.8 1M). Read both rules files + plan. State at boot:
  cockpit SHELL done (deployment-ui@52c9f18); the remaining work = (a) turn cockpit from NAV-HUB → EMBEDDED APP (fold
  Deployments/VM/Live-Ops/CI/Alerts/Chaos/Launch/SafetyOps page components INTO cockpit tabs with REAL data + build the
  unified "Alerts & Logs" stream), (b) Phase-1 backend health rollup (`/api/health/overview` +
  `/api/health/consolidator`), (c) Phase-2 dynamics columns + alert-deep-link, (d) Phase-3 live-cluster log streaming
  (close the `log_stream.py` 501), (e) Phase-4 `/api/fleet/reconciliation` + monitoring-registration HARD-FAIL QG
  (register-all-first → land green) + GH/GCP/AWS billing tile, (f) Phase-5 codex + master-plan flip.
- **Parallelization plan**: deployment-api backend → background sub-agent (own repo); deployment-ui folds → main agent
  (single `Cockpit.tsx` + one playwright suite, can't safely parallelize same-file); deployment-service+PM enforcement →
  handled near the end (high blast-radius, rule 11). pw:L2 CI parity = `--workers=1 --retries=2`. Never
  `prettier --write` tree-wide. Foreign-dirty `.github/workflows/quality-gates-v2.yml` in deployment-ui — never stage
  it.
- **2026-06-23 — OPERATOR INTERRUPT (higher priority, fixed first): `uv.lock` drift jamming the ff-pull crons.** Root
  cause: every repo pins siblings as editable path sources; `uv sync` (quality-gates/setup) rewrites each sibling's
  `version =` field to the sibling's current pyproject version every run → tracked `uv.lock` shows dirty → the ff-pull
  crons `[skip:dirty]` the clone → it falls behind LDR ("loads of commits not flowing"; worst for
  `system-integration-tests` which pins ALL siblings). HARD RULE forbids committing this internal-version drift, and
  `uv.lock` is correctly NOT gitignored (it's the `--frozen` install SSOT) → the fix is to auto-restore the spurious
  drift in the ff-pull dirty-gate. **Shipped**: (1) peer `PM@4f4742cf5` already added it to `slot-cron-ff-pull.sh` (the
  `.tabs/` slot sweep, auto-propagates fleet-wide via the script self-update); (2) **`PM@a01df43fc` (mine)** adds the
  SAME conservative discriminator to the `main-clone-ff-pull` cron emitted by `install-slot-cron-ff-pull.sh` — the
  inline cron that FFs the TOP-LEVEL build clones (where `uv sync` runs during QG), which the peer fix missed.
  Discriminator restores ONLY pure `version =` drift; a genuine lock edit (non-version lines, e.g. an external dep add)
  is preserved. Unit-tested (pure-drift→RESTORE, firestore-add→PRESERVE), `bash -n` clean, live crontab re-installed,
  and a manual run **FF-pulled every stranded clone level** (15 repos incl. system-integration-tests; 0 repos behind LDR
  after).
- [ ] [SCRIPT] P2. **Propagate the `main-clone-ff-pull` cron fix to other interactive hosts** — the `install-*` SSOT is
      on LDR (`PM@a01df43fc`) and the `.tabs/` slot fix auto-propagates, but the LIVE main-clone crontab LINE only
      updates when `install-slot-cron-ff-pull.sh --include-main-clones` is re-run on a host. Re-run it on the
      human-planning VM (`ssh human-planning-vm`) and any other interactive dispatch host that uses main-clones.
      (deployment-service/PM — ff-pull infra; this host already done.)
