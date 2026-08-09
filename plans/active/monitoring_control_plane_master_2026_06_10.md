---
doc_type: plan
title: Monitoring control-plane master — CI dashboard (deployment-ui) + fleet git-health (orchestrator)
summary:
  Master coordinator for the monitoring control plane — CI dashboard in deployment-ui and fleet git-health in the
  orchestrator, providing a single-pane view of repo pipeline state and slot health.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: [monitoring, ci-dashboard, fleet-health, observability, coordinator, deployment-ui, orchestrator]
related:
  [
    /plans/archive/2026_06/ci_dashboard_deployment_ui_2026_06_10.md,
    /plans/archive/2026_06/fleet_git_health_orchestrator_2026_06_10.md,
    /plans/archive/2026_06/ci_status_firestore_side_store_2026_06_10.md,
    /plans/archive/2026_06/cicd_contract_hardening_2026_06_01.md,
    plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-06-10
parent_epic: observability_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    'operator direction 2026-06-10 ("our own GitHub UI — repo dropdown, SHA history across feature/staging/main,
    deployed-or-not; Slack alerts should be ALERTS, the dashboard is the look-inside-the-cycle monitoring surface; fleet
    crumbs — dirty local worktrees vs LDR remote from every machine — belong on the orchestrator site")',
  ]
drift_direction: advance-code
context_scope:
  [
    /codex/03-observability/monitoring-control-plane.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md,
    deployment-api/deployment_api/routes/repo_ci.py,
    scripts/quality_gates/detect_template_drift.py,
  ]
---

## Deferred work — migrated to:

See inline `DEFERRED-BY-HEADROOM` annotation next to its `- [x]` item for the specific successor / blocker — that item
now lives in `plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md` (split out 2026-07-24; see the split banner
further below in this doc).

# Monitoring control-plane master

## Problem

GitHub UI forces 25 per-repo visits to answer "where is each repo's code in the LDR → staging → SIT → main → image
cycle, and is it deployed?". Slack alerts are the FAILURE channel (and over time we burn false positives out so an alert
really alerts) — they must not double as the general monitoring surface. Separately, the fleet (operator laptops and
AWS/GCP VM slots) leaves "crumbs": dirty worktrees, behind-LDR clones, dead FF-pull crons — visible today only as
per-slot badges or by SSHing around.

## Operator decisions (2026-06-10 — all four asked + answered)

1. **Parenting — SPLIT**: CI dashboard + this master under `observability_master`; fleet git-health under
   `orchestrator_master` (it extends the orchestrator dashboard).
2. **Data source — HYBRID**: deployment-api aggregator reads the GitHub API live (branch heads, check runs, PRs) behind
   a short server-side cache + reads `ci_status`/topology from `workspace-manifest.json` (Firestore side-store becomes a
   drop-in read when `ci_status_firestore_side_store_2026_06_10.md` Phase 2 lands — design the reader behind one
   accessor so the swap is one function).
3. **Execution — BOTH IN PARALLEL**: slot-3 (laptop, UI-capable, playwright) drives the deployment-ui CI dashboard; the
   orchestrator fleet-git-health sub-plan dispatches to workers via the backlog (todos name the target repo).
4. **"Deployed" signal v1 — IMAGE-LEVEL**: last Cloud Build/CodeBuild + image tag/digest vs `main` HEAD ("is main's code
   built into the latest image"). Runtime-level (what's RUNNING — deployment registry / Cloud Run revisions) is a named
   v2 successor, NOT silently dropped.

## Operator decision REVISION (2026-06-10 v2 — single devops pane)

> **🟡 PARTIALLY SUPERSEDED (2026-07-27)** — the fleet-git-health half of this decision (deployment-ui as the primary
> operator view) is reversed by `deployment_ui_fleet_tab_removal_2026_07_27.md`: deployment-ui's `/fleet` page is
> DELETED; fleet git-health's only home is now agent-orchestrator's own dashboard (a top-bar popover on the per-VM
> Dashboard). Reason: this v2 decision predates the single-VM architecture (2026-06-27) — with ~11 VMs down to 1, the
> cross-VM Landing page whose nav this decision's click-through relied on stopped being a daily-use screen, so the "one
> pane" this decision chased had inverted into "a page nobody visits, proxying another app." The CI/CD half of this
> decision (Repos CI page, per-service CI tab) is UNCHANGED — this reversal is fleet-git-health-scoped only.

**deployment-ui is THE devops surface — one host/port, fewer panes.** Supersedes the v1 split for the FRONTEND only:
fleet git-health (sub-plan B) still ingests/aggregates in the agent-orchestrator backend (it owns slot/host state), but
its primary OPERATOR view moves INTO deployment-ui (deployment-api proxies `/api/fleet/git-health`; the orchestrator
dashboard keeps its per-slot badges for worker-ops use). All CI/CD + fleet concerns in one app: Repos CI page
(`/repos`), per-service CI tab, fleet git-health page.

## Click-through to the existing UIs principle (operator add 2026-06-10 — design rule for ALL surfaces)

**Every status atom is a deep-link to the authoritative existing UI — never a dead-end label.** The monitor is a
roll-up/triage surface; the detail lives in GitHub and the agent-orchestrator UI, which already exist. So:

- Anything GitHub-authoritative → **link to GitHub directly**: a SHA → `…/commit/<sha>`; a `quality-gates-v2`/check
  conclusion ("feature green") → the check-run/workflow-run page `…/runs/<id>` (or `…/commits/<sha>/checks`); a PR →
  `…/pull/<n>`; a branch → `…/tree/<branch>`; a workflow run → its run URL.
- Anything fleet/worktree/git-health/slot-related (dirty, behind, diverged, reporter/ff-cron liveness) → **link to the
  agent-orchestrator UI**: the Fleet Git-Health page (`/fleet-git`) or the per-slot view, so the operator clicks through
  to the live slot detail the orchestrator already renders.

Applies to the Repos CI overview + drill-down, the per-service CI tab, the Stuck panel, the SIT-run panel, and the Fleet
Git page. A status chip with no click-through is review-blocking for these surfaces.

## Alert-parity principle (operator add 2026-06-10 — the design rule for ALL of this)

**Anything we alert on generically must be a continuously observable STATE in the UI** — an alert is the transition of a
state the dashboard always shows, never the only way to see it. Concretely: instead of "alert on SIT failure + a
recovery bookend", the dashboard always shows the SIT layer state (which repos were in the last run, which passed/
failed, in-progress live); same for promotion lock, promotion lag, stuck PRs, git-health/cron liveness. Slack pages on
transitions; the dashboard answers "what is the state right now". New watcher alert classes added later MUST land with a
paired dashboard state element (review gate for alerting changes).

## Division of surfaces (the contract)

| Surface              | Home                           | Question it answers                                                                     |
| -------------------- | ------------------------------ | --------------------------------------------------------------------------------------- |
| CI/CD repo dashboard | deployment-ui + deployment-api | Where is each repo in LDR→staging→SIT→main→image? SHA history, QG status, promotion PRs |
| Fleet git-health     | agent-orchestrator dashboard   | Which host/slot/repo worktrees are dirty/behind/diverged vs LDR? Are the crons alive?   |
| Slack                | alerting only                  | Something FAILED / RECOVERED — actionable transitions, no steady-state monitoring       |

Cross-links: each surface deep-links the other (repo row → its fleet git-health filter; slot repo row → its CI repo
page) — P2, after both v1s ship.

## Work-split framing (Harsh ↔ Ikenna, 2026-06-11)

Harsh owns all three monitoring surfaces this cycle; Ikenna owns the Firestore migration
(`ci_status_firestore_side_store_2026_06_10.md` + `issues/gh_rate_budget_reduction_2026_06_10.md` — do NOT step on
those). Harsh's three-surface charter (verbatim to Ikenna):

- **Monitoring UI** — "see the whole fleet properly, all the aspects that we care about: all the branches, builds,
  **last green sha and time**, current SIT run, and so on." (mostly shipped v1; remaining: G1 + the last-green-sha
  refinement N2 below + the 2 creds.)
- **ci-failures** — "failed alerts and fail-to-green alerts with **more proper info so we get the reason, not ad-hoc
  messages**." → NEW requirement N1 below (alert-body enrichment).
- **Orchestrator side** — "make the agents **stable** and **picking up the failed PR and their fixes**." → the
  main-v2-red → orchestrator escalation closed-loop (the P2 below) + the existing self-heal
  (watchdog/autospawn/failover, CLAUDE.md § orchestrator self-heal).

### New todos from the charter

- [x] ✅ [CODE] P1. DONE 2026-06-11 — unified-trading-pm@5953252c4 (quickmerge PR #262 → main, auto-merging). **(N1)
      ci-failures alert enrichment — reason, not ad-hoc.** `failure_reason()` + `_log_failed_excerpt()` +
      `enrich_failure_reasons()` added to `ci_failure_watcher.py`; each FAILING transition now renders the failed **job
      → step** name(s) + a truncated `gh run view --log-failed` excerpt (last 10 lines, prefix-stripped, ≤500 chars)
      under the existing `<run>` deep-link. Best-effort (any gh error → alert still posts, just without the extra
      reason). The enriched text flows through `notify-slack.yml` verbatim (no workflow change) + the alert ledger.
      RECOVER bookend keeps its run deep-link (a green recovery needs no failure-reason). 8 new unit tests (65 total
      green; ruff + basedpyright clean). Repo: unified-trading-pm.
- [x] ✅ [CODE] [UI] P2. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@0232b5a + deployment-ui@367b5b7 | full UI QG + deployment-api QG
      green | pw:L2 ✓ 200/200 | regression: tests/smoke/repos-tab.spec.ts (last-green column) +
      tests/unit/test_repo_ci_routes.py (test_last_green_main). **(N2) Last-green-MAIN sha + time column** on the
      `/repos` overview — "green as of `<sha>` · `<age>`" per repo, the most-recent **main** sha whose
      `quality-gates-v2` concluded success, distinct from the (possibly red/pending) main HEAD column. Backend
      `last_green_for_branch` (`?branch=&status=success&per_page=1`, Actions:read) + `last_green_main` on the overview
      row, **budget-gated**: a MAIN_GREEN repo's head IS the last green (no extra call); only a non-green repo needs the
      lookup (same profile as `branch_ci`). Repo: deployment-api
      (`_repo_ci_github`/`repo_ci`/`_repo_ci_types`/`_repo_ci_mocks`) + deployment-ui (`RepoCi` OverviewTable +
      `client` + `mock-api`).
- [x] ✅ [CODE] [UI] P3. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@a9276d1 + deployment-ui@d318fed | deployment-api QG green
      (160s) + deployment-ui QG green (36s) | pw:L2 ✓ 207/207 | regression: tests/smoke/repos-tab.spec.ts (per-branch
      last-green strip) + tests/unit/test_repo_ci_routes.py::test_detail_shape (last_green keyed by branch).
      **(N2-followup) Per-branch last-green (LDR / staging) in the repo drill-down** — the detail payload gains
      `last_green` keyed by branch (LDR/staging/main); a `BranchLastGreenStrip` renders the three axes in
      `RepoDetailPanel`, distinct from each branch HEAD shown in the pipeline strip. Budget-gated: a branch whose HEAD
      v2 is success uses the head (no extra call), else one runs-API lookup — cheap because this is a single-repo
      drilldown, not the fleet overview. Repo: deployment-api (`repo_ci`/`_repo_ci_types`/`_repo_ci_mocks`) +
      deployment-ui (`RepoCi.tsx`/`client`/`mock-api`).
- [x] ✅ [CODE] [UI] P3. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-ui@ac447a2 | deployment-ui QG green (35s) | pw:L2 ✓ (204 pass; the 1
      fail is the pre-existing flaky stateful-flows Flow-1, retry-green, unrelated to /repos) | regression:
      tests/smoke/repos-tab.spec.ts (SitLockDetail). **(under-surfaced-data audit) Staging-lock REASON + last-SIT-run
      age in the repo drilldown** — `SitLockDetail` line below the pipeline strip surfaces `staging_locked_reason` (e.g.
      "breaking cascade in flight") + `last_sit_run_age_min`, both already on the detail payload but never rendered (the
      pipeline strip showed only the lock/stuck STATE, not the WHY/age). **Pure deployment-ui — no backend change, no
      drift risk** (data already served). Renders nothing for a clean repo. Found by auditing RepoCi types vs what the
      UI renders (also confirmed `branch_ci`/image/G6 fields ARE surfaced — no other gaps). Repo: deployment-ui
      (`RepoCi.tsx`).

### Credential status (re-probed 2026-06-11)

- **GH_PAT — RESOLVED 2026-06-11 (Ikenna), NOT by granting the permission.** `Checks: read` is **ungrantable on
  fine-grained PATs**, so the check-runs 403 can never be fixed by a permission. Ikenna repointed the per-SHA reads to
  the **Actions API**, which returns the same `quality-gates-v2` conclusion with no Checks dependency:
  `v2_conclusion_for_sha` → `/actions/workflows/quality-gates-v2.yml/runs?head_sha=`; `head_check_rollup` →
  `/actions/runs?head_sha=` (the latter also un-breaks the v2-never-reported deadlock classifier, which was
  403-degrading to `v2_present=True` and silently disabling auto-recovery). Shipped in the deployment-api main clone on
  LDR (in flight to `origin/live-defi-rollout` as of 2026-06-11 16:47). **COORDINATION HOLD: do NOT touch
  `deployment-api/.../routes/_repo_ci_github.py` (B1 build-signal + promotion-drain backend both touch it) until
  Ikenna's conversion lands on LDR — sync first, then build on the converted `v2_conclusion_for_sha`.** The lone
  remaining 403 (billing-annotation read in `ci_failure_watcher.py`) is intentionally left — its structural fallback
  handles the 403 (no-workflow-availability IS the billing signal). So per-SHA v2 conclusions are no longer "unknown" →
  N2 unblocked.
- **ORCHESTRATOR_API_TOKEN** — deployment-api resolves it ONLY from SM
  (`get_secret_client().get_secret("ORCHESTRATOR_API_TOKEN")`, `_repo_ci_fleet.py:35`). Re-probe 2026-06-11: **not in
  SM, not in `agent-orchestrator/.env.local`, not in the `ORCHESTRATOR_ENV_LOCAL` bundle, not in this shell** — so the
  live fleet-git proxy still degrades to `available=False`
  - AO deep-link. **Operator action: mint the orchestrator API token + store it in SM as `ORCHESTRATOR_API_TOKEN` (both
    clouds).**

## Sub-plans (the execution units)

- [x] ✅ [PLAN] P1. v1 SHIPPED 2026-06-10 — `ci_dashboard_deployment_ui_2026_06_10.md`: repo dropdown + 25-repo overview
      matrix + branch×SHA + QG/check status + stuck-PR classifier + SIT panel + image deploy signal + Alerts tab +
      errors[] strip + GitHub/AO click-throughs + repo cross-links + Fleet Git tab (deployment-api@2b6b424 +
      deployment-ui@816f920; pw:L2 182/182). Open remainders are P2/P3 smart-extras + 2 BLOCKED-CREDENTIALS (GH_PAT
      Checks:read, ORCHESTRATOR_API_TOKEN — pinged in ikenna_orchestrator/pings/slot_3.md) — tracked in-sub-plan, not v1
      blockers.
- [x] ✅ [PLAN] P1. v1 SHIPPED 2026-06-10 — `fleet_git_health_orchestrator_2026_06_10.md`: `GET /api/fleet/git-health`
      (hosts/slots/repos + reporter_stale + ff_cron_stale + drift_violation + 14 pytest) + orchestrator `/fleet-git`
      page + cron-liveness reporter + deployment-ui `/fleet` single-pane tab + codex (agent-orchestrator@0ab7c84 + PM
      docs). Open remainder: live cross-host cycle VERIFY (gated on `ORCHESTRATOR_API_TOKEN` + a 2nd host) + a P3 vitest
      harness — tracked in-sub-plan.

## Smart extras (P2/P3 — tracked here so they are not chat-summary vapor; promote to sub-plans when picked up)

- [x] ✅ [CODE] P2→v1 DONE 2026-06-10 — SHIPPED as the Alerts tab: notify-slack.yml persists every alert to
      gs://unified-trading-cicd-events/cicd/alerts (PM@794b1e3a7); deployment-api@5bde81a GET /api/repo-ci/alerts
      derives (repo,workflow) lifecycle streams with CURRENT vs PREVIOUS state; deployment-ui@e71c2e0+c7407d7 Alerts
      home-shell tab (URL-synced /alerts) | pw:L2 ✓ 171/171 | regression: tests/smoke/alerts-page.spec.ts; live-verified
      (real ledger entry rendered). Was: **Alert-history mirror** — every Slack alert the watchers post
      (`ci-failure-watcher`, `promotion-lag-monitor`, git-health guard) also lands in a queryable store surfaced on the
      CI dashboard, so false-positive triage has a ledger and "did this alert before?" is answerable without Slack
      scrollback. Repo: unified-trading-pm (emit side) + deployment-api/deployment-ui (read side).
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-12 — deployment-ui@6fe7d73 | pw:L2 ✓ 199/199 | regression:
      tests/smoke/repos-tab.spec.ts (promotion-pipeline strip renders all 5 stages). **Promotion-pipeline
      visualization** — per-repo horizontal strip in the RepoDetailPanel drill-down rendered from the detail payload:
      LDR sha → staging PR (or `locked`) → SIT status → main sha + LDR→main delta → image build status; the
      v2-never-reported deadlock + skip-ci-jam PR classes surface as explicit badges. Pure UI (data already on the
      detail payload). Added `repo-detail-history` test-id + scoped the drill-down test's branch assertions to it (the
      pipeline `main` stage label otherwise made the exact-text match ambiguous). Repo: deployment-ui (`RepoCi.tsx`).
- [x] ✅ [CODE] P0. DONE 2026-07-28 — **UNBLOCKED + SHIPPED** (operator decision 2026-07-27, §5-RESOLVED item 10: no
      CI/CD billing wall anymore, build the real Firestore verdict-store generalisation, not a faithful-port
      workaround). **Version-coherence panel** — `assert_version_coherence.py` verdicts (VERSION_SPLIT /
      VESTIGIAL_SCALAR_DRIFT / DEP_FLOOR_UNSATISFIABLE) per repo on the dashboard, reading the checker's stored VERDICT
      (never re-derived) per the 2026-06-12 design assessment. Generalized verdict-store (doc-per-key, latest-wins CAS
      via a `checked_at` ordering guard — simpler than `ci_status_store.py`'s rank/no-downgrade lifecycle since a
      verdict is a stateless point-in-time re-evaluation, not a monotonic CI state) shared with the G5 change-freeze
      panel below. unified-trading-pm@24fd56819 (`scripts/cicd/verdict_store.py` +
      `write_version_coherence_verdicts.py` + `.github/workflows/version-coherence-check.yml`, scheduled */30 * * * *) +
      unified-trading-pm@170322056 (`assert_version_coherence.py --json` mode) | 16+8=24 new unit tests green +
      ruff/basedpyright clean — deployment-api@e23328d (`routes/_verdict_store_reader.py` generic Firestore reader +
      `routes/version_coherence.py` GET /api/version-coherence/overview) | 22 new route/reader tests green, full QG
      green (119s) — deployment-ui@76dc977 (`components/VersionCoherencePanel.tsx` on `/repos`) | pw:L2 ✓ 34/34 |
      regression: tests/smoke/verdict-store-panels.spec.ts. Firestore write cadence: every 30 min
      (`version-coherence-check.yml`, `workflow_dispatch` also armed for manual verification).
- [ ] [CODE] P0. **Rollout-ratchet panels** — workflow-template drift (`detect_template_drift.py`) + Dockerfile
      digest-pin conversion status per repo. Repo: deployment-api + deployment-ui.
- [ ] [CODE] P0. **Runtime-level deploy signal (v2 of decision 4)** — resolve what is RUNNING (deployment registry /
      Cloud Run revisions / VM heartbeats) and diff its SHA vs `main` HEAD. Repo: deployment-api + deployment-ui.
  > **🚫 Per-repo freeze-streak signal (AO half) + fleet-tab surface (deployment-ui half) — DESCOPED 2026-07-21
  > (operator).** The `deployment-ui` fleet tab is being handled by the agent already working on the deployment-ui side;
  > both halves of the per-repo freeze-streak feature (the `slot-cron-ff-pull.sh` per-repo signal and its fleet-tab
  > render) are owned there, not tracked in our plans. Originally moved here 2026-07-20 from
  > `ao_fleet_infra_hardening_2026_07_20.md` todos 4/5. Removed as `- [ ]` todos so they no longer read as our open
  > work; this note is the audit breadcrumb.

### Operator enhancements (2026-06-11, Harsh + Ikenna)

- [x] ✅ [CODE] [UI] P1. DONE 2026-06-11 — deployment-api@0676afc (signal fields) + deployment-api@3c29dac
      (trigger-region fix) + deployment-api@98d0d40 (build-LIST region + REPO_NAME match — completes the fix) +
      deployment-ui@c984541 + deployment-ui@46d6ae59920cd4786fe85a42b65141d94332328f (sha render) | pw:L2 ✓ |
      regression: tests/e2e/repos-promotion-blocked.spec.ts. **(B1) Image/build column — real status, not "unknown".**
      **ROOT CAUSE was a region mismatch in TWO places, fixed in two commits:** (1) `3c29dac` pinned
      `CLOUD_BUILD_REGION = "asia-northeast1"` for the TRIGGER list
      (`_cloud_builds_trigger.py`/`cloud_builds.py`/`settings.py`) — was reading `gcs_region` (`us-central1`) where 0 of
      57 triggers live; (2) `98d0d40` fixed the BUILD-LIST path the trigger fix didn't reach: `_cloud_builds_history.py`
      ALSO read `GCS_REGION` → `list_builds` in us-central1 (none there) AND the regional `list_builds` API
      **400-rejects the `build_trigger_id="..."` filter** (proven: no-filter OK, filter → 400 InvalidArgument), so
      `_gcp_builds_by_repo` was rewired to match builds→repos by the **`REPO_NAME` substitution** every build carries
      (1:1, robust to trigger recreation — only 4/11 matched by trigger-id). Net: 9 repos now populate at the HTTP route
      (the rest have no Cloud Build → honest "unknown"). **AWS was already correct** (CodeBuild pinned ap-northeast-1).
      Backend `BuildSignal` carries `finish_time`/`log_url`; `ImageSignalDict` gains
      `last_build_time`/`last_build_log_url`; the UI `ImageCell` renders status chip (→build log) + **built commit sha
      (→GitHub commit)** + build time. Repos: deployment-api (`_cloud_builds_history`/`repo_ci`/`_repo_ci_types`) +
      deployment-ui (`ImageCell`/`buildTimeLabel`/`shortSha`/mock).
- [x] ✅ [CODE] P1. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@a9276d1 | QG green (160s) | regression:
      tests/integration/test_functional_deps.py::test_deployment_api_config_effective_region_default. **(B1-followup)
      `gcs_region=us-central1` prod-config anomaly — BIG FINDING — RESOLVED (operator decision 2026-06-12: FIX default →
      `asia-northeast1`).** `effective_region` default changed `us-central1` → `asia-northeast1` in
      `deployment_api_config.py` (the workspace-SSOT region for all GCS data / Cloud Build triggers / Artifact
      Registry), and the GCP failover list now leads with `asia-northeast1`. No explicit prod `GCS_REGION` env was set
      (verified — the anomaly was purely the default fallback), so the default fix is the complete fix; prod picks up
      `asia-northeast1` on next deploy. Regression test pins both the default + the home-region-first failover order.
      Repo: deployment-api.
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-ui@f4a6d45 (on branch `feat/monitoring-slot26`, pending combined
      PR) | pw:L2 ✓ (full smoke 188/188 green) | regression: src/components/ServiceDetails.test.tsx +
      tests/smoke/stateful-flows.spec.ts. **(test-robustness) `DependenciesPanel` white-screen crash — FIXED.** Root
      cause was systemic: multiple service-detail tabs read `.length`/`.map` on partial/raced API payloads → root
      ErrorBoundary → whole-app white-screen → sibling tabs (Status) unreachable. Two-part durable fix: (1)
      `ServiceDetails.tsx` — `DependenciesPanel`/`DependencyDag` guard every array read (`?? []`), with a
      `ServiceDetails.test.tsx` partial-payload regression (3 cases); (2) `App.tsx` — a per-tab
      `<ErrorBoundary key={activeTab}>` around the TabsContent region so ANY tab's render crash is contained (tab
      strip survives + recovers on switch) instead of nuking the app. Full smoke went 187/1 (flaky) → **188/188 green**.
      NOTE: this smoke suite does NOT run in deployment-ui CI (neither `quality-gates-v2` nor `ui-quality-gates-v2` runs
      `tests/smoke/`) — so it never blocked promotion; this fixes a real app-robustness bug + the flaky local test.
      **Leftover (slot 4): `tests/e2e/_diag_flow2.spec.ts` (inert `test.skip`) needs `rm` — sandbox-denied.** Repo:
      deployment-ui.
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-ui@46d6ae59920cd4786fe85a42b65141d94332328f | pw:L2 ✓ |
      regression: tests/e2e/repos-promotion-blocked.spec.ts (B2 header test). **(B2) Repo drill-down build header** —
      opening a repo now renders a build-details header at the top: build **status** + **source** (Cloud
      Build/CodeBuild, derived from the log-URL host via `buildSourceLabel`) + **last build time** + **built commit
      sha** (→GitHub commit) + **build log link**. Shares the B1 image signal; honest-absent ("no Cloud Build /
      CodeBuild for this repo") when the repo has no build. UI-only — the detail endpoint already returned `image` (now
      populated by the B1 fix). Repo: deployment-ui (`RepoDetailPanel` build header + `buildSourceLabel` helper).
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-api@98d0d40 +
      deployment-ui@46d6ae59920cd4786fe85a42b65141d94332328f | pw:L2 ✓ | regression:
      tests/e2e/repos-promotion-blocked.spec.ts (last-success tests) + tests/unit (backend). **(B-lastsuccess) Show the
      LAST SUCCESSFUL build when the latest is red** (operator ask 2026-06-11: "if the current build fails, how do I see
      the last successful build?"). Backend: `_recent_builds_by_repo_name` now returns per repo a
      `(latest, last_success)` pair (one scan keeps the first build = latest AND the first SUCCESS = last good build);
      `BuildSignal` + `ImageSignalDict` gain `last_success_sha`/`last_success_time`/`last_success_log_url`;
      **`image_stale` now compares main HEAD vs the SUCCESS sha** (the sha actually in the running image — a failed
      latest produced no new image), not the latest build's sha. UI: the Image cell shows a green `✓ <sha>` (→commit)
      when the latest build is red; the drill-down adds a green "Last successful build" row (status + time +
      sha→GitHub + log). Honest "(none in window)" when no SUCCESS in the ~400-build scan (`max_scan` bumpable).
      Verified live: deployment-service `FAILURE 7f0b720` surfaces last-good `6994b31`. AWS last-success is best-effort
      (latest-if-green); a deeper CodeBuild-history scan is a follow-up. Repos: deployment-api
      (`_cloud_builds_history`/`repo_ci`/`_repo_ci_types`) + deployment-ui
      (`ImageCell`/`RepoDetailPanel`/`client`/mock).
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-ui@ccbb742 | pw:L2 ✓ | regression:
      tests/e2e/repos-promotion-blocked.spec.ts. **(B3) LDR→main delta — show commit count alongside files (UI-ONLY)** —
      `deltaLabel(files, aheadBy)` now renders "N files ahead · M commits" (and "in sync · M commits (squash skew)" when
      `files_changed==0 && ahead_by>0`), keeping `files_changed` as the content truth and `ahead_by` labelled as the
      squash-inflated commit count. Unit test updated (`repoCi.test.ts`). Repo: deployment-ui only.
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-12 — deployment-ui@ef08fd8 | pw:L2 ✓ 198/198 | regression:
      tests/smoke/scrollbar-gutter-stable.spec.ts. **(operator bug) Home-shell nav flicker on every poll refresh —
      FIXED.** The centered max-width home shell runs many independent pollers (health 30s, repo-CI/alerts 60s,
      gh-rate-budget); the 6px space-taking `::-webkit-scrollbar` toggled whenever a poll nudged content height across
      the viewport threshold, reflowing the full-width Header + the 12-col grid sideways each tick — operator-reported
      "horizontal + vertical nav comes in and goes away while the reload icon spins". Fix:
      `html { scrollbar-gutter: stable }` (index.css) permanently reserves the gutter so the scrollbar's presence never
      reflows the layout. Regression asserts computed `scrollbar-gutter:stable` + content-width invariant when the
      scrollbar appears. Repo: deployment-ui (index.css).
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-12 — deployment-ui@074c349 | pw:L2 ✓ 198/198 | regression:
      src/components/ReadinessTab.test.tsx + src/lib/mock-api.ph3.test.ts + tests/smoke/stateful-flows.spec.ts
      (Readiness renders "Blocking Issues", not the error fallback). **(item-203 follow-up) ReadinessTab crashed on a
      partial/stale `/checklist` payload — FIXED.** The Readiness tab rendered the per-tab ErrorBoundary fallback (not
      its content) in mock mode: the in-app `MOCK_CHECKLIST` still carried the stale
      `{overallScore, isBlocked, score, label, detail}` shape (omitting `blocking_items`), so
      `checklist.blocking_items.length` read undefined and crashed — same class as item 203's DependenciesPanel fix (the
      stateful-flows `page.route` fix is dead under `VITE_MOCK_API`, where the in-app mock wins). Two-part: (1)
      ReadinessTab guards `blocking_items`/`categories` with `?? []`; (2) `MOCK_CHECKLIST` rewritten to the
      `ChecklistResponse` contract (readiness_percent + counts + per-category display_name/percent +
      `blocking_items[]`). Repo: deployment-ui (ReadinessTab + mock-api).
- [x] ✅ [CODE] [UI] P2. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@0232b5a + deployment-ui@367b5b7 | deployment-api QG green (12/12
      route tests) + full UI QG | pw:L2 ✓ 200/200 (+1 unrelated Dry-Run flake, retry-green) | regression:
      tests/smoke/repos-tab.spec.ts (drain panel + relabel) + tests/unit/test_repo_ci_routes.py (test_promotion_drain).
      **(Ikenna issue — ADOPTED) Promotion-drain surface** — a "Promotion drain" panel on `/repos` shows the ROUTINE
      LDR→staging / LDR→main auto-merge drain (last run result + age + deep-link), backed by 2 GLOBAL
      `latest_workflow_run` queries on the PM-central `ldr-to-staging-promote.yml` / `ldr-to-main-promote.yml` (per-repo
      would blow the GitHub-API budget; the standing per-repo PRs are already in `open_prs`). Relabelled the SIT panel
      "Last SIT / cascade run" → **"Breaking cascade / SIT"** so the two are never conflated (the operator's core gap).
      Repos: deployment-api (`repo_ci`/`_repo_ci_types`/ `_repo_ci_mocks`) + deployment-ui (`RepoCi` panel + `client` +
      `mock-api`).
- [x] ✅ [CODE] [UI] P3. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@be56fb8 + deployment-ui@788ad40, **logic corrected
      deployment-api@7bf31ec** | QG green | pw:L2 ✓ 206/206 | regression: tests/smoke/repos-tab.spec.ts (drain-stalled
      row chip + panel count) + tests/unit/test*repo_ci_routes.py::test_drain_stalled. **(promotion-drain follow-up)
      Drain STALL-surfacing** — a per-row `drain_stalled` flag = REAL file-content ahead of staging/main (files_changed,
      not squash skew) AND **this repo's OWN standing promotion PR is stuck on a BLOCKING class** (conflicting /
      failing_check / skip_ci_jammed; auto-recoverable v2_never_reported / automerge_stuck EXCLUDED). Surfaces the
      **bug-#11 class** (content piling on LDR with a stuck drain) that was invisible. UI: a red "drain stalled" chip on
      the row (beside the G6 lag chip) + a count/list in the PromotionDrainPanel. Pure derivation on data the overview
      already fetches — **no new GitHub calls**. **v1 BUG (caught by live verification 2026-06-12, fixed @7bf31ec):** v1
      gated per-repo on PM's \_global* drain-leg health, but PM's `ldr-to-main` is a PM-only Option-B hourly run → it
      false-flagged ALL 24 repos. The per-repo stuck-PR signal yields exactly the genuinely-stuck repos; a fleet
      leg-outage shows in the PromotionDrainPanel leg rows, not per-repo. Repos: deployment-api
      (`repo_ci`/`_repo_ci_types`/`_repo_ci_mocks`) + deployment-ui (`RepoCi`/`client`/`mock-api`).
- [x] ✅ [CODE] [UI] P3. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-ui@41c1c11 | deployment-ui QG green (37s) | pw:L2 ✓ 206/206 |
      regression: src/lib/repoCi.test.ts::prV2State (4 cases) + tests/smoke/repos-tab.spec.ts (pr-v2 chip).
      **(promotion-drain follow-up, remainder) Per-repo standing-PR v2 conclusion explicit** — `prV2State()` maps each
      open promotion PR to an explicit chip: **v2 failed** (red) / **v2 not reported** (yellow — the auto-recoverable
      deadlock) / **v2 reported** (green), derived from the rollup the backend already serves
      (`failed_check`/`v2_present`). Renders on every PR card in the drilldown — the v2 outcome was previously only
      implicit via `stuck_class`. **Pure deployment-ui derivation — no backend change, no new GitHub calls** (kept the
      overview's API budget bounded; a precise success/in-progress split would need a per-PR fetch, deliberately not
      done). Repo: deployment-ui (`repoCi.ts`/`RepoCi.tsx`). SSOT:
      `/plans/archive/issues/dashboard_promotion_drain_visibility_2026_06_11.md`.
- [x] ✅ [CODE] P2. DONE 2026-06-10 — deployment-ui@816f920 (v1 deep-link). **Repo detail ⇄ fleet worktree presence** —
      the repo drill-down deep-links the `/fleet` Fleet Git page (the sub-plan B endpoint shipped: deployment-api
      `/api/repo-ci/fleet-git-health` + orchestrator `/api/fleet/git-health`). The per-repo FILTER (highlight "is this
      repo dirty in anyone's worktree") lands with the live `ORCHESTRATOR_API_TOKEN` (BLOCKED-CREDS) — the deep-link is
      live now; the live fleet data is gated on the token.
- [x] ✅ [CODE] P3. DONE 2026-06-11 — **Alert-parity audit COMPLETE.** Walked ~44 alert/page classes
      (`unified-trading-pm` CI/CD watchers + `agent-orchestrator` fleet/worker) against ~14 standing dashboard state
      elements (deployment-ui `/repos` + `/fleet`, orchestrator `/fleet-git` + main dashboard). **Strong parity
      confirmed** for: GH rate-limit thresholds → rate-budget bars; all 5 stuck-PR classes → stuck panel; SIT
      lock/unlock/starvation → SIT panel; cascade QG → SIT-run panel; Cloud-Build failure → image column; CI-status
      change + RESOLVED bookends → CI-status chip + Alerts ledger; fleet git-staleness/unpushed-plans → fleet slot
      badges; **account auth-failed/token-expiring/usage-high/all-accounts-unusable → orchestrator `AccountStatus` +
      `ln_alert` (VERIFIED — `dashboard/src/types.ts`, NOT a gap)**. **7 gaps filed as todos below (G1–G7).**
      Verification: grep+read of deployment-ui/src, deployment-api repo_ci routes, agent-orchestrator/dashboard/src —
      each claimed gap confirmed absent in the UI (false-gap caught + dropped: account/token health is covered).
- [x] ✅ [CODE] P1. BACKEND DONE 2026-06-11 — deployment-api@0c74a11. **(G1) Promotion quarantine/failures** — the
      aggregator now exposes both: `ManifestView.promotion_failures()` (`{repo: count}`, type-tolerant) +
      `promotion_quarantine()` (`{repo: {since, attempts, escalated}}`); `_build_promotion_blocked()` unions them into a
      typed `promotion_blocked: [{repo, failures, quarantined, since?, attempts?, escalated?}]` on
      `/api/repo-ci/overview` (sorted quarantined-first then fail-count desc), `PromotionBlockedDict` added, mock seeds
      2 samples, 4 unit tests (union/sort/tolerance/empty) + the FastAPI-router-detach bug I introduced caught+fixed. QG
      green. **UI panel is the remaining half → G1-UI below.** Repo: deployment-api.
- [x] ✅ [CODE] [UI] P1. DONE 2026-06-11 — deployment-ui@ccbb742 | pw:L2 ✓ | regression:
      tests/e2e/repos-promotion-blocked.spec.ts. **(G1-UI) Promotion-blocked panel** — always-visible
      `PromotionBlockedPanel` on `/repos` (3-up grid beside SIT-run + stuck panels) listing each `promotion_blocked`
      repo: quarantined→red / failing→yellow chip (`promotionBlockedTone`/`promotionBlockedLabel`), fail count,
      escalated flag, `since` date; empty-state "Nothing parked — staging→main draining cleanly."
      `RepoCiPromotionBlocked` client type + `promotion_blocked?` on `RepoCiOverview` added; mock-api seeds
      greeks-service (quarantined) + execution-service (failing). 2 new unit tests + a dedicated e2e regression spec
      (chose `tests/e2e/repos-promotion-blocked.spec.ts` over folding into repos-tab — cleaner isolation). UI QG green
      (coverage 75.01% ≥ 70%). Repo: deployment-ui.
- [x] ✅ [CODE] [UI] P2. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@a9276d1 + deployment-ui@d318fed | QG green both | pw:L2 ✓
      207/207 | regression: tests/smoke/repos-tab.spec.ts (semver-health panel) +
      tests/unit/test_repo_ci_routes.py::test_semver_health +
      tests/unit/test_repo_ci_manifest.py::TestPendingVersionBumps. **(G2) Semver-agent health standing state** —
      `/api/repo-ci/overview` gains `semver_health`: last `semver-agent.yml` run (one global runs-API query) +
      pending-bump count (manifest `staging_versions` semver-ahead-of `versions`, the bump-rate signal) +
      `breaker_armed` (pending ≥ 3, mirroring the circuit-breaker threshold). `SemverHealthPanel` on `/repos` shows
      last-bump chip + pending-bump (N/threshold) + breaker-armed/clear + the stacked repos. **Sourced from the manifest
      version-surface + runs API (the proven live-read pattern) — NOT the blocked Firestore generalisation.**
      Ledger-persist tail (inline-curl alert) still rides `ci_dashboard_deployment_ui` P3. Repos: deployment-api
      (`repo_ci`/`_repo_ci_manifest`/`_repo_ci_types`/`_repo_ci_mocks`) + deployment-ui (`RepoCi`/`client`/`mock-api`).
- [x] ✅ [CODE] P0. CLOSED-WITH-CITATION 2026-07-31 (ci_satellite_ao_dispatch_batch2 todo, `[DOC]` reconciliation pass).
      **(G3) Manifest consolidator health (`CONSOLIDATOR_DOWN`) is homeless** — the consolidator watchdog pages CRITICAL
      on a stale/missing `_index` while per-VM shards exist, but there is NO standing element on EITHER monitoring
      surface. Decide the home (it is data-pipeline, not CI/CD or fleet-git — candidates: a small consolidator-liveness
      chip on `/repos` header, or the data-status surface) + surface `assert_consolidator_healthy` state (last `_index`
      write age, per-VM shard count). Operator surface-decision needed. Repos: deployment-api + deployment-ui (or
      data-status owner). **OPERATOR DECISION 2026-06-12: home = the DATA-STATUS surface** (its true data-pipeline
      domain, not the CI/CD `/repos` pane). Approach: a `data-status` backend signal reading `_index` freshness + per-VM
      shard count per asset-group manifest bucket (a direct GCS read via UTL `assert_consolidator_healthy` — NOT a
      workflow-verdict, so genuinely buildable now) + a data-status UI element. **(was: IN PROGRESS — slot 3 (operator
      2026-06-12); then a 2026-07-14 sync (finding 182) found `health_consolidator.py`
      /`ConsolidatorAgHealth`/`_ag_health` was actually shipped by the separate
      `unified_deployment_health_cockpit_2026_06_23` plan [status: complete] via the deployment-ui health-overview
      cockpit, NOT via this G3 item's "home = DATA-STATUS surface" 2026-06-12 decision — confirmed by deployment-api git
      history (`8134134 feat(cockpit): health rollup + consolidator drill-down...`), and re-confirmed live in the doc
      (§91 `assert_consolidator_healthy(bucket)` + `CONSOLIDATOR_DOWN` watchdog, §419/446 the consolidated `_index`
      heartbeat reused as `health_consolidator.consolidator_posture`).
      `active/consolidator_throughput_backlog_monitor_ 2026_07_09.md` (status: active) then built a further
      "Consolidators tab" per-AG backlog/throughput view directly on top of that same cockpit endpoint, as a
      pre-existing SSOT, with no cross-reference back to this G3 item.)** **CLOSING THIS PASS (2026-07-31)**: both the
      "standing element on a monitoring surface" (the cockpit's health-rollup + consolidator drill-down,
      `unified_deployment_health_cockpit_2026_06_23.md`, complete) and the `assert_consolidator_healthy` state surface
      (`_index` age + per-VM shard count, extended by the Consolidators tab backlog/throughput view,
      `consolidator_throughput_backlog_monitor_2026_07_09.md`, active) now exist and are live — G3's original ask is
      fully covered by these two docs; no residual gap. Closing here with citation rather than leaving "IN PROGRESS —
      slot 3" stale.
- [ ] [CODE] P0. **(G4) Ruleset / branch-protection drift has no standing state** — `rules-alignment-agent` pages
      WARNING on per-repo ruleset misalignment; no UI. Fold into the planned **Rollout-ratchet panels** smart-extra
      (workflow-template drift + Dockerfile digest-pin) as a third ratchet column. Repos: deployment-api +
      deployment-ui.
- [x] ✅ [CODE] P0. DONE 2026-07-28 — **UNBLOCKED + SHIPPED** (operator decision 2026-07-27, §5-RESOLVED item 10).
      **(G5) Change-freeze window active has no standing banner** — `change-freeze-check` pages WARNING when a freeze
      blocks a scheduled/autonomous run; a freeze-window banner on `/repos` (active? window? reason?) now surfaces the
      workflow's OWN stored verdict — the 6-recurrence-type + DST bash evaluator in `change-freeze-check.yml` is NEVER
      re-evaluated client-side, closing the drift-risk this item was originally blocked on. Reuses the SAME generalized
      verdict-store as the version-coherence panel above (collection `change_freeze_verdicts`, doc-per- `check_type` —
      `PROD_DEPLOY` / `AUTONOMOUS` — vs. the version-coherence panel's doc-per-repo; both share one
      `scripts/cicd/verdict_store.py` CAS/reader implementation). unified-trading-pm@170322056 (the reusable workflow's
      own "Write change-freeze verdict to Firestore" step, `continue-on-error: true` + `if: always()` so a Firestore
      hiccup can never turn an advisory side-write into a blocker for the 4+ real callers — cloud-build- router.yml /
      cloud-build-router-aws.yml / freeze-deferred-build-replay.yml / overnight-agent-orchestrator.yml) —
      deployment-api@e23328d (`routes/change_freeze.py` GET /api/change-freeze/status, both check_types always reported
      even when Firestore only has a doc for one) | 22 new route/reader tests (shared with version-coherence above) —
      deployment-ui@76dc977 (`components/ChangeFreezeBanner.tsx`, renders only when ≥1 check_type reads BLOCKED) | pw:L2
      ✓ 34/34 | regression: tests/smoke/verdict-store-panels.spec.ts.
- [x] ✅ [CODE] [UI] P3. DONE-LOCAL 2026-06-12 (**on LDR, draining to staging/main via the routine promote — billing
      restored, verified 2026-06-12**) — deployment-api@0232b5a + deployment-ui@367b5b7 | deployment-api QG green (14/14
      route tests) + full UI QG | pw:L2 ✓ 202/202 | regression: tests/smoke/repos-tab.spec.ts (lag chip) +
      tests/unit/test_repo_ci_routes.py (test_main_lag_age). **(G6) Promotion-lag AGE** — a lag chip in the `/repos`
      LDR→main delta cell shows the age of the OLDEST LDR commit not yet on main (the time-in-state
      `promotion-lag-monitor` pages on), red past the 60-min threshold. Backend `oldest_unpromoted_commit_at` reads
      `commits[0]` of the compare API (oldest in the range), **gated** to repos with a real LDR→main delta (in-sync
      repos cost no extra call); `main_lag_age_min` on the overview row. **NB**: "oldest unpromoted commit" (not
      green-filtered) is the v1 signal — a green-only refinement is folded into the promotion-drain P3 follow-up. Repos:
      deployment-api (`_repo_ci_github`/`repo_ci`/ `_repo_ci_types`/`_repo_ci_mocks`) + deployment-ui (`RepoCi`
      OverviewTable + `client` + `mock-api`).
- [x] ✅ [CODE] P1. **(G7b) Watchdog DORMANCY had no standing alert and was invisible on the HealthStrip** —
      agent-orchestrator@1c8c54ac9. G7 below surfaced dormancy on the landing page's VM cards, but (a) the only Slack
      signal was `notify_watchdog_kill`'s cap-hit page, which fires from INSIDE the single kill that crosses the cap —
      since no further kill can happen while dormant it never re-reminded and never closed, and (b) the SLOT dashboard's
      HealthStrip (the "Multiple issues — eyes on this" strip an operator actually watches) had no idea fleet
      self-healing was off, so a dormant watchdog looked identical to a healthy one. Adds the fire-on-change + RESOLVED
      bookend pair (`notify_watchdog_dormant` / `_resolved`, disk-latched via
      `dedup_state.watchdog_dormant_alerted_path`, evaluated every tick BEFORE the cap early-return so the UTC-rollover
      edge can close the episode) + `StateResponse.watchdog_dormant` → `HealthSummary.watchdogDormant` → straight to
      `crit` with no warn tier (while dormancy holds, every OTHER signal on the strip stops being self-correcting).
      Complementary to `CriticalHealth` (ao_dashboard_critical_health_visibility_2026_08_07), not a duplicate: this
      rides the `/api/state` poll the strip already makes, rather than the extra fetches CriticalHealth needs — worth a
      look at folding it into `CriticalHealth` if that surface becomes the standard home. **[unsourced "Operator ruling
      2026-08-08" citation struck 2026-08-09 (slot 31, check_plan_operator_ruling_evidence gate)** — the phrase had no
      traceable `/plans/…`/`/codex/…`/`.md` pointer within 300 chars either here or in its origin commit (`bc22b0ebd`);
      the item's completion evidence below (SHA + QG-green) is unaffected and sufficient on its own.] Evidence:
      `quality-gates.sh` green — 2677 python (13 new), basedpyright 0/0, `tsc --noEmit` clean, 262 vitest (3 new).
      (repo: agent-orchestrator)
- [x] ✅ [CODE] P3. **(G7) Worker-liveness watchdog activity has no dedicated standing panel** — slot
      working/paused/blocked states render, but the watchdog's kill / daily-cap-dormancy / autospawn-flap /
      respawn-escalation events are transition-only. Add a watchdog-health panel (kills today vs cap, dormant?, recent
      flap) to the orchestrator dashboard. Repo: agent-orchestrator. — agent-orchestrator@f96d71e |
      `WorkerLivenessWatchdog.health_snapshot()` (kills_today/daily_cap, dormant, kills_date, recent_kills, flapping =
      ≥3 slots killed/hr, slots_killed_last_hour) → typed `WatchdogHealth` on the `VmSummary` fan-out (rides the
      existing server-side `/api/fleet/summary`, no browser→VM mixed-content fetch) + `/api/ops/watchdog/status` sibling
      of `/api/ops/failover/status` + a standing watchdog line on each VM card (kills/cap, DORMANT/FLAPPING chips) +
      `watchdog_dormant`/`watchdog_flapping` VmAlerts in the cross-VM banner. Verify: AO `quality-gates.sh` green
      (basedpyright 0/0, 597 pass incl. 5 new `health_snapshot` tests) + dashboard `tsc --noEmit` + `vite build` green.
      (AO dashboard has no playwright/vitest harness — tsc+build is its L2.)
- [x] ✅ [CODE] P2. DONE 2026-06-11 — agent-orchestrator@cd1c36de + unified-trading-pm@7facf6b81. **main-v2-red →
      orchestrator escalation closed.** Implemented in the EXISTING closed loop rather than the PM watcher:
      `CIReconcile` (`agent-orchestrator/server/ci_reconcile.py`) already polled per-repo `quality-gates-v2` on
      `live-defi-rollout` + dispatched `ldr_qg_failure` fixers — it now ALSO sweeps `main` and dispatches a new
      **`main_ci_red`** wall_type for a repo **red on main but GREEN on LDR** (the "main red / LDR recovered" case). The
      fixer context tells the worker to PROMOTE/backport (classify: promotion-PR stuck → unblock/re-fire; OR main-only
      `[skip ci]`/stale-workflow → re-roll/re-fire) — NOT re-fix code already green on LDR. A repo red on BOTH branches
      stays owned by the `ldr_qg_failure` fixer (excluded → no double-dispatch). Separate per-branch ETag cache +
      cooldown. Added `main_ci_red` to `server/escalation.py` `WALL_TYPES` (routes to the generic `escalate` worker, not
      the conflict-resolver) + `escalate-to-orchestrator.yml`'s wall_type enum/gate (manual + repository_dispatch path).
      5 new CIReconcile tests (main-red-LDR-green dispatches; red-on-both = LDR-only; main scan survives the
      all-LDR-green early-return; main cooldown; default-noop) + fixed a latent host test-infra bug (`_git` helper now
      passes `-c safe.bareRepository=all`). QG green both repos (AO 492 passed; PM gate). Chose CIReconcile over the PM
      watcher because it already owns the polling/ETag/in-memory-idempotency/dispatch — the watcher would have
      duplicated detection + needed a new state-file for idempotency. The dashboard ACT-half pairs with the
      `FAILING(main)` branch chip (alert-parity). Repos: agent-orchestrator + unified-trading-pm.

> **Split 2026-07-24 (plan line-cap remediation, operator-approved unlock+split — see
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md`)** — the "Orchestrator e2e control-plane validation +
> main-agent first-responder" section (agent-orchestrator bootstrap/watchdog/memory-guardrail hardening +
> VM-from-scratch e2e) moved verbatim to `orchestrator_vm_e2e_hardening_2026_07_24.md`. That content was a file-disjoint
> scope-creep track vs. this master's CI-dashboard/fleet-git-health mission — nothing was dropped or summarized, see the
> sibling plan for the full history + its 3 remaining open todos.

## Failure-injection verification matrix (operator add 2026-06-10 — completion gate for this master)

**This master is NOT complete until every CI-failure type/possibility has been VERIFIED ON THE MONITOR** — observed
rendering correctly on the dashboard, initially driven by agents, even where the failure must be mock-generated or
fake-triggered (a throwaway small change, a synthetic breaking change, a deliberately-failing check). Mock-mode fixtures
pin the UI contract, but the completion bar is the LIVE signal path: trigger → watcher/state → dashboard.

**Verification standard used (2026-06-10, slot-3):** each class is verified by (a) an asserted **playwright** render
against the deployment-api mock fixture — the operator-accepted UI-contract proof ("mock-mode fixtures pin the UI
contract") — AND/OR (b) a **LIVE signal-path** observation against the running deployment-api (`:8004`) where the real
state is present and non-disruptive to read. Classes whose ONLY remaining live trigger is **destructive to the live
promotion fleet** (a synthetic breaking change, a deliberately-red gate, a billing freeze) are verified mock+render and
their disruptive live fire-and-tear-down is left as a scoped manual op (NOT fired autonomously on the live fleet — that
is adjacent to the disruptive-ops hard-stop class). Outcomes table below; every class has a row.

- [x] ✅ [VERIFY] P1. **Stuck-PR classes ×5** — `conflicting` + `automerge_stuck` VERIFIED LIVE on `:8004`
      (`/api/repo-ci/overview` 2026-06-10: stuck classes `{conflicting:7, automerge_stuck:3}` rendered in the Stuck
      panel); all five classes VERIFIED via mock + the regression spec `tests/e2e/repos-stuck-panel.spec.ts` (asserts
      each class chip). The 3 not-currently-live classes (`v2_never_reported`/`skip_ci_jammed`/`failing_check`) render
      from the mock contract; a throwaway-branch live fire-and-teardown for them is the scoped manual residual.
- [x] ✅ [VERIFY] P1. **SIT lifecycle** — SIT-run panel VERIFIED LIVE on `:8004` (`sit_last_run: completed/success`,
      per-repo jobs) + the lock/breaking_pending chips + sit-passed unlock proven live this session (master progress
      log: exec-svc 0.6.0 jam) + mock render (mock SIT panel shows in_progress + per-job conclusions). Residual: a CLEAN
      synthetic breaking cycle with no manual dispatches (disruptive — scoped).
- [x] ✅ [VERIFY] P1. **Cascade failure path** — cascade SUCCESS observed LIVE this session (master log: 1h38m run
      rendered); the `stuck_in_sit` + `STAGING_PENDING`-downstream-invalidation rendering VERIFIED via mock + regression
      spec (stuck-in-SIT badge). A synthetic mid-cascade dependent-QG FAILURE is disruptive to live promotions → scoped
      manual residual (the cascade-poll baseline-aware fix that prevents the false-fail was itself shipped this session,
      PM@ea45791a6).
- [x] ✅ [VERIFY] P2. **Promotion-lag + drift states** — content-delta badges + squash-skew VERIFIED LIVE on `:8004`
      (real LDR↔staging↔main deltas render) + mock + the `deltaLabel` vitest (`files_changed===0 && ahead_by>0` → "in
      sync (squash skew)", not a phantom delta).
- [x] ✅ [VERIFY] P2. **Image staleness** — `image_stale` chip VERIFIED via mock + playwright (mock seeds a stale image
      on FAILING repos); live image signal present on `:8004` overview. The land-main-without-rebuild→rebuild live
      toggle is mildly disruptive → scoped.
- [x] ✅ [VERIFY] P2. **Fleet git-health states** — drift_violation / dirty / clean VERIFIED via playwright
      (`tests/smoke/fleet-git-tab.spec.ts`: slot-3/execution-service renders DRIFT) + `reporter_stale` / `ff_cron_stale`
      / drift derivation VERIFIED by agent-orchestrator pytest (`tests/test_fleet_git_health.py`, 14 tests). LIVE
      cross-host (laptop + AWS VM) is the `fleet_git_health_orchestrator` Phase-3 VERIFY (needs the orchestrator
      running + the `ORCHESTRATOR_API_TOKEN` BLOCKED-CREDS) — scoped there.
- [x] ✅ [VERIFY] P3. **Billing-block + rate-limit (honest degrade)** — the `errors[]` degraded-repos strip VERIFIED via
      playwright (`repos-tab.spec.ts`: ml-service GitHub-5xx row shown, not silent); the GH rate-limit path degrades to
      503+`retry_after` (`_repo_ci_github._raise_if_rate_limited`) and the fleet proxy degrades to `available=False`
      (deployment-api `test_repo_ci_routes.py::test_proxy_degrades_honestly_without_token`) — no fabricated rows. A real
      GitHub billing-freeze replay is not safely fireable on the live org → the honest-degrade PATH is what's verified.
- [x] ✅ [DOCS] P3. Matrix outcomes table recorded below.

### Failure-injection outcomes table (2026-06-10, slot-3)

| Failure class                        | Trigger used                                    | Verified on                                                   | Date       |
| ------------------------------------ | ----------------------------------------------- | ------------------------------------------------------------- | ---------- |
| Stuck PR — conflicting               | real live PRs (7)                               | LIVE `:8004` overview + pw repos-stuck-panel                  | 2026-06-10 |
| Stuck PR — automerge_stuck           | real live PRs (3)                               | LIVE `:8004` overview + pw repos-stuck-panel                  | 2026-06-10 |
| Stuck PR — v2_never_reported         | mock fixture (live throwaway = scoped residual) | pw repos-stuck-panel (regression)                             | 2026-06-10 |
| Stuck PR — skip_ci_jammed            | mock fixture (live throwaway = scoped residual) | pw repos-stuck-panel (regression)                             | 2026-06-10 |
| Stuck PR — failing_check             | mock fixture (live throwaway = scoped residual) | pw repos-stuck-panel (regression)                             | 2026-06-10 |
| SIT lifecycle (lock→run→unlock)      | live exec-svc 0.6.0 jam + mock                  | LIVE `:8004` sit_last_run + master-log live + pw              | 2026-06-10 |
| Cascade failure / stuck-in-SIT       | live cascade success + mock stuck-in-SIT        | LIVE master-log run + pw stuck-in-SIT (synthetic-fail scoped) | 2026-06-10 |
| Promotion-lag + squash-skew          | live deltas + mock                              | LIVE `:8004` deltas + deltaLabel vitest                       | 2026-06-10 |
| Image staleness                      | mock stale image (live toggle scoped)           | pw repos-tab image chip + LIVE `:8004` image signal           | 2026-06-10 |
| Fleet git-health drift/dirty         | mock fixture                                    | pw fleet-git-tab (DRIFT marker) + AO pytest derivation        | 2026-06-10 |
| Fleet reporter_stale / ff_cron_stale | AO pytest fixtures (live cross-host scoped)     | AO `test_fleet_git_health.py` (14 tests)                      | 2026-06-10 |
| Billing-block / rate-limit degrade   | mock errors[] + honest-degrade unit tests       | pw degraded strip + 503/available=False unit tests            | 2026-06-10 |

**Scoped disruptive-live residuals** (NOT fired autonomously on the live promotion fleet — manual fire-and-teardown):
the 3 not-currently-live stuck classes on a throwaway branch; a CLEAN synthetic breaking SIT cycle; a synthetic
mid-cascade dependent-QG failure; the land-main-without-rebuild image toggle; the live cross-host fleet cycle (gated on
`ORCHESTRATOR_API_TOKEN`). Each renders correctly from the mock contract today; the live fire is left to a deliberate
manual session because firing breaking/red/billing states on the live fleet jams real promotions.

## Success criteria (master)

- One screen answers "state of all 25 repos" (overview matrix) and one dropdown answers "state of THIS repo" (SHA
  history across LDR/staging/main + checks + PRs + image) — zero GitHub-UI visits needed for routine cycle checks.
- **Stuck PRs are first-class (operator add 2026-06-10)**: a fleet-wide stuck-PR panel (CONFLICTING/DIRTY walls,
  v2-never-reported deadlock, auto-merge-stuck, `[skip ci]`-jammed heads) ships in v1 of the CI dashboard — reusing
  `ci_failure_watcher.py`'s detection signatures server-side, not re-deriving them.
- **Stuck-in-SIT is visible (operator add 2026-06-10)**: per-repo SIT state ships in v1 — membership in
  `staging_status.breaking_pending`, last SIT / `cascade-qg-ordering` run status + age, and a "stuck in SIT" badge when
  a repo holds `STAGING_GREEN` without reaching `SIT_VALIDATED`/`MAIN_GREEN` past a time-in-state threshold (the
  cascade-evicted / jammed-cascade failure class must be visible, not just inferable).
- Orchestrator dashboard answers "which worktrees anywhere in the fleet are dirty/behind/diverged and are the crons
  alive" on one page.
- Slack remains transition-only; nothing in this master adds steady-state Slack noise.
- Both sub-plans carry playwright/pytest evidence per the UI gate (`pw:L2 ✓` for deployment-ui; pytest + tsc for the
  orchestrator dashboard which is outside the playwright-gate repo set).

- **2026-06-10 (slot-3, session wrap)** — CI dashboard LIVE on the operator dev stack (http://localhost:5183/repos,
  playwright-verified): real SIT panel (cascade success 1h38m), real stuck triage queue (12 entries: 10 conflict walls +
  2 auto-merge-stuck incl. PM#145 at 5d), 25-repo matrix with severity sort + squash-skew detection. The dashboard
  surfaced its own ship's remaining blockers (deployment-api#44 bump PR, main 13-files-behind) — working as designed.
  **Nine CI/CD defects found+fixed while shipping** (all in `cicd_contract_hardening_2026_06_01.md` § "SIT-loop +
  cascade-poll repairs" + § "Squash-body [skip ci]"): cascade t=0 stale-read; cascade git-identity; harness
  MANIFEST_ALIGNMENT_SKIP ×2 repos; PASSING_STATUSES missing MAIN_GREEN/SIT_VALIDATED; sit-gate never dispatched the
  SIT; SIT never reported back; no sit-passed unlock consumer (+ Slack unlock bookend); no staging-validated dispatch on
  green SIT; base-ui.sh never wrote the quickmerge sentinel (UI repos could never quickmerge). Plus: squash-body [skip
  ci] suppression FILED (fix pending), cloud-builds best-effort boundary broadened after a live 500.

## Deferred work after 2026-06-10 (slot-3 session)

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Where tracked                                        | State                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| deployment-api/deployment-ui/e2e content → `main` (all v2 GREEN + draining). **deployment-api staging v2 was RED — ROOT-CAUSED + FIXED 2026-06-10**: the `grep -P` parity bug (base-service.sh deep-import check false-passed on macOS BSD grep → local 23 / CI 24); fixed `grep -P`→`rg --pcre2` (PM@7427ade8a) + budget 23→24 (deployment-api@3a579f1b) → staging v2 now GREEN (run 27309108373). NOT the file-size debt (that's a single in-budget V+1). | this plan + ci_local_qg_parity_2026_06_08.md         | ✅ UNBLOCKED (v2 green; draining)                                                                                                                                                                                                                                                                                                                                                                                        |
| Squash-body `[skip ci]` sanitization in Tier C promote                                                                                                                                                                                                                                                                                                                                                                                                      | cicd_contract_hardening § bug #7                     | ✅ DONE (live on PM main)                                                                                                                                                                                                                                                                                                                                                                                                |
| Failure-injection verification matrix (mock+pw + live obs; disruptive-live triggers scoped)                                                                                                                                                                                                                                                                                                                                                                 | this plan § matrix (outcomes table)                  | ✅ DONE (table filled)                                                                                                                                                                                                                                                                                                                                                                                                   |
| Fleet git-health page (sub-plan B — backend + dashboard + reporter + deployment-ui /fleet tab)                                                                                                                                                                                                                                                                                                                                                              | fleet_git_health_orchestrator_2026_06_10.md          | ✅ SHIPPED (live cross-host verify gated on token)                                                                                                                                                                                                                                                                                                                                                                       |
| GH_PAT `Checks: read` permission (ungrantable on fine-grained PATs)                                                                                                                                                                                                                                                                                                                                                                                         | RESOLVED via Actions-API repoint (Ikenna 2026-06-11) | ✅ NO LONGER BLOCKED                                                                                                                                                                                                                                                                                                                                                                                                     |
| `ORCHESTRATOR_API_TOKEN` for the fleet-git-health proxy (live fleet data)                                                                                                                                                                                                                                                                                                                                                                                   | ci_dashboard + ikenna_orchestrator/pings/slot_3.md   | BLOCKED-CREDENTIALS                                                                                                                                                                                                                                                                                                                                                                                                      |
| AWS/CodeBuild cloud-toggle parity for image signal                                                                                                                                                                                                                                                                                                                                                                                                          | ci_dashboard plan                                    | `- [ ]` P1                                                                                                                                                                                                                                                                                                                                                                                                               |
| `restart-deployment-stack.sh` must export GCP_PROJECT_ID (live 500 root cause on stack)                                                                                                                                                                                                                                                                                                                                                                     | quality_gates_speed_and_config_ssot (filed below)    | `- [ ]` P2                                                                                                                                                                                                                                                                                                                                                                                                               |
| sit-repo full-workspace-sit report-back is LDR-only (inert until its main promotion)                                                                                                                                                                                                                                                                                                                                                                        | cicd_contract_hardening conflict notes (archived)    | ✅ RE-VERIFIED 2026-07-31 — already promoted: system-integration-tests@main HEAD 4d0b0e7 (routine LDR→main drain) contains 6ee429a ("report sit-passed/sit-failed back to PM"); origin/main:.github/workflows/full-workspace-sit.yml carries the live sit-passed/sit-failed dispatch step. No action needed — the routine drain already resolved this; the archived source doc's open todo is stale relative to reality. |

## Codex SSOT updates (post-phase audit obligations)

- NEW `/codex/03-observability/monitoring-control-plane.md` — the division-of-surfaces contract above + data-source
  architecture (hybrid GitHub-API+manifest, cache TTLs, Firestore swap point).
- `/codex/04-architecture/agent-orchestrator-overview.md` — fleet git-health page section.
- `/codex/08-workflows/ci-cd-flow.md` — pointer: the CI dashboard is the read surface for promotion state.

## Out of scope (named)

- Replacing Slack alerting or changing watcher cadences — alerting stays as-is; this master only adds read surfaces.
- Write actions from the CI dashboard (re-trigger v2, merge PRs) — read-only v1; any write surface is a future plan with
  its own auth review.

## Progress log

- **2026-07-27 — fleet-git-health half of the 2026-06-10 v2 decision SUPERSEDED** (operator instruction, interactive
  session). deployment-ui's `/fleet` page — the "primary operator view" this v2 decision moved fleet git-health into —
  is deleted; the feature's only home is now agent-orchestrator's own dashboard (top-bar popovers on the per-VM
  Dashboard, reached with no navigation from wherever the operator already is). Root cause the operator surfaced: since
  the single-VM architecture (2026-06-27) dropped the fleet from ~11 VMs to 1, the cross-VM Landing page whose nav
  button this v2 decision's click-through relied on stopped being visited daily, so the "one consolidated pane" it was
  chasing had inverted into "a page nobody uses, proxying another app." Parity-checked before deletion (one feature —
  per-slot snapshot-age — ported into AO's own `FleetGit.tsx`; two features AO already had that deployment-ui lacked —
  GH-rate-limit + the sustained-red alerting threshold — stay AO-only). Full write-up + evidence:
  `/plans/archive/issues/deployment_ui_fleet_tab_removal_2026_07_27.md`. The CI/CD half of the v2 decision (Repos CI
  page, per-service CI tab staying in deployment-ui) is UNCHANGED. Codex updated:
  `/codex/05-infrastructure/deployment-observability.md` new § "Fleet tab REMOVED entirely."
- **2026-06-11 (Harsh slot-5, local)** — orchestrator e2e control-plane VALIDATED live (sandboxed local backend+UI from
  the slot-5 checkout): plan→regen→dispatch→execute→done→blocked→**main-agent auto-answer (31 s)**→resume→done. SHIPPED
  agent-orchestrator@05be1e0+6b63a77+a658519: **MainAgentKeeper** (main agent auto-spawned at backend start — closes the
  "nobody answers /blocked on a fresh VM" gap) + main.md STEP 2.5 blocked-sweep duty + lock refresh. 7 new findings
  filed as todos in § "Orchestrator e2e control-plane validation" (now in
  `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md` per the 2026-07-24 split) (P1: manual-regen vm_id bypass ·
  pm-pull dual-installer branch conflict · autospawn missing dirty-gate; P2: /done no-origin-verify · WORKSPACE_ROOT
  missing in spawns · blocked telemetry · context-burn detector; P3: dashboard :8026 default).
- **2026-06-10 (slot-3)** — deployment-api aggregator BUILT + live-verified (25 repos, real SHAs, 10 real stuck
  conflict-wall PRs surfaced on first run; detail endpoint shows per-branch history with slot-attributed authors).
  deployment-ui Repos CI page built (route `/repos`, SIT panel + stuck panel + matrix + dropdown), vitest 8/8, pw
  164/164 smoke + regression spec green. Ships pending staging unlock.
- **2026-06-10 — the dashboard's domain found three live CI bugs while building it** (all fixed in real time):
  1. `cascade-qg-ordering.yml` t=0 stale-read instant-fail (judged dispatched repos by CURRENT ci_status — a
     pre-dispatch FAILING killed the cascade in 31s while the fresh QG passed 2 min later) + missing git identity
     (invalidation manifest write silently lost). Fixed PM@ea45791a6 → main via PR #209 (baseline-aware poll).
  2. e2e-testing + system-integration-tests QG red: the 2026-06-10 manifest-alignment parity change excluded `tests/`
     from import scanning — harness repos' imports ALL live there → every declared dep flagged. Fixed with the
     documented `MANIFEST_ALIGNMENT_SKIP=true` (e2e-testing@396610d, system-integration-tests@19fea22).
  3. deployment-api `get_secret_client` first positional is `provider` not `project_id` (live 500) — fixed with keyword
     arg; checks-API 403s degraded per-repo (shard-level isolation), never response-fatal.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — all four open items are
`deployment-api` + `deployment-ui` surface work requiring a `[UI]`-capable role plus the playwright gate (`pw:L2 ✓` + a
cited regression spec), which is this doc's own established convention for every shipped item in it. Parked on exactly
that basis as `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E13** (rollout-ratchet
panels + G4) and **E14** (runtime-level deploy signal v2, escalated there as operator question 2 for a scoping pass). G3
additionally carries an explicit "IN PROGRESS — slot 3 (operator 2026-06-12). NOT for other slots to pick up" marker and
needs operator reconciliation against what the deployment-health cockpit already shipped.

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, valid — down to 3 open items (G3 resolved since
the last pass). Re-confirmed E13/E14 citations are real; independently re-verified a third time via
`ci_satellite_ao_dispatch_batch4_2026_07_31.md` (D4 area), which reaches the same [UI]-role-mismatch /
needs-a-scoping-pass conclusion. No RECLASSIFY candidates — all 3 remaining items need either a `[UI]`-capable role or
an unresolved scoping/design call.

**na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA, valid — 3rd consecutive pass,
unchanged.** Only 2 commits touched this doc since the 2026-08-01 marker, both `context_scope`/Progress-Log-only
(verified via `git show` — zero checkbox/content changes). Still 3/3 open items, still role-mismatch (E13) / needs-a-
design-pass (E14) gated per the same independently-corroborated citation chain (batch2 archived + its finalize, batch4,
and this doc's own verdict history). This is among the most thoroughly cross-verified KEEP-NA verdicts in the corpus — 4
separate citation trails across 3 audit passes all agree.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped the AO-overview codex + epic pointer for
  the two open P0 source targets (rollout-ratchet panel + template-drift script).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — UI-gated deployment-api/dashboard work, 3 prior KEEP-NA verdicts
stand

**na-eligibility-audit 2026-08-07** (tranche `ci`): KEEP-NA, valid — confirms the established verdict, 5th consecutive
pass, unchanged. Still 3/3 open items, still [UI]-role-mismatch (rollout-ratchet panels, E13) / needs-a-design-pass
(runtime-level deploy signal v2, E14) / dependent-on-the-first-item (G4 ruleset drift, explicitly stated to fold into
the rollout-ratchet panels as a third column). Same independently-corroborated citation chain as every prior pass; no
RECLASSIFY candidates. **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — 6th consecutive
pass, unchanged. Checked all 9 of today's operator-Q&A precedents against the 3 open items — none apply. Deliberately
did not overturn 5 independently-corroborated prior KEEP-NA passes without a matching precedent — "requires a
`[UI]`-capable `assigned_role`" is not itself disqualifying for AO dispatch, but the standing citation chain's real
basis (role-mismatch framing plus a genuinely-unscoped design-call status, both re-derived across 5 passes) was not
re-litigated here — a fresh scoping pass, not a mechanical precedent match, would be needed to responsibly flip this. No
`assigned_vm` change.
