---
title: "Monitoring control-plane master — CI dashboard (deployment-ui) + fleet git-health (orchestrator)"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
created: 2026-06-10
source:
  - operator direction 2026-06-10 ("our own GitHub UI — repo dropdown, SHA history across feature/staging/main,
    deployed-or-not; Slack alerts should be ALERTS, the dashboard is the look-inside-the-cycle monitoring surface; fleet
    crumbs — dirty local worktrees vs LDR remote from every machine — belong on the orchestrator site")
related_plans:
  - plans/active/ci_dashboard_deployment_ui_2026_06_10.md
  - plans/active/fleet_git_health_orchestrator_2026_06_10.md
  - plans/active/ci_status_firestore_side_store_2026_06_10.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
locked_by: live-defi-rollout
locked_since: 2026-06-10
---

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

**deployment-ui is THE devops surface — one host/port, fewer panes.** Supersedes the v1 split for the FRONTEND only:
fleet git-health (sub-plan B) still ingests/aggregates in the agent-orchestrator backend (it owns slot/host state), but
its primary OPERATOR view moves INTO deployment-ui (deployment-api proxies `/api/fleet/git-health`; the orchestrator
dashboard keeps its per-slot badges for worker-ops use). All CI/CD + fleet concerns in one app: Repos CI page
(`/repos`), per-service CI tab, fleet git-health page.

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

## Sub-plans (the execution units)

- [ ] [PLAN] P1. `ci_dashboard_deployment_ui_2026_06_10.md` — repo dropdown + fleet overview + per-repo branch×SHA
      matrix + QG/check status + promotion PRs + image-level deploy signal. Owner: slot-3 (laptop, playwright-capable).
- [ ] [PLAN] P1. `fleet_git_health_orchestrator_2026_06_10.md` — fleet-wide hosts×slots×repos git-health page +
      reporter/cron-liveness aggregation endpoint. Owner: orchestrator backlog (repo: agent-orchestrator).

## Smart extras (P2/P3 — tracked here so they are not chat-summary vapor; promote to sub-plans when picked up)

- [x] ✅ [CODE] P2→v1 DONE 2026-06-10 — SHIPPED as the Alerts tab: notify-slack.yml persists every alert to
      gs://unified-trading-cicd-events/cicd/alerts (PM@794b1e3a7); deployment-api@5bde81a GET /api/repo-ci/alerts
      derives (repo,workflow) lifecycle streams with CURRENT vs PREVIOUS state; deployment-ui@e71c2e0+c7407d7 Alerts
      home-shell tab (URL-synced /alerts) | pw:L2 ✓ 171/171 | regression: tests/smoke/alerts-page.spec.ts; live-verified
      (real ledger entry rendered). Was: **Alert-history mirror** — every Slack alert the watchers post
      (`ci-failure-watcher`, `promotion-lag-monitor`, git-health guard) also lands in a queryable store surfaced on the
      CI dashboard, so false-positive triage has a ledger and "did this alert before?" is answerable without Slack
      scrollback. Repo: unified-trading-pm (emit side) + deployment-api/deployment-ui (read side).
- [ ] [CODE] P2. **Promotion-pipeline visualization** — per-repo horizontal pipeline (LDR → staging PR → SIT → main →
      image) rendered from the overview payload; the v2-never-reported deadlock + `[skip ci]` jam states get explicit
      badges (data already in the PR panel of sub-plan A). Repo: deployment-ui.
- [ ] [CODE] P3. **Version-coherence panel** — `assert_version_coherence.py` verdicts (VERSION_SPLIT /
      VESTIGIAL_SCALAR_DRIFT / DEP_FLOOR_UNSATISFIABLE) per repo on the dashboard. Repo: deployment-api (run/ingest) +
      deployment-ui.
- [ ] [CODE] P3. **Rollout-ratchet panels** — workflow-template drift (`detect_template_drift.py`) + Dockerfile
      digest-pin conversion status per repo. Repo: deployment-api + deployment-ui.
- [ ] [CODE] P3. **Runtime-level deploy signal (v2 of decision 4)** — resolve what is RUNNING (deployment registry /
      Cloud Run revisions / VM heartbeats) and diff its SHA vs `main` HEAD. Repo: deployment-api + deployment-ui.
- [ ] [CODE] P2. **Repo detail ⇄ fleet worktree presence (operator add 2026-06-10)** — the CI dashboard's repo
      drill-down shows "is this repo dirty/checked-out in anyone's worktree" from the orchestrator's
      `/api/fleet/git-health` (sub-plan B endpoint) filtered by repo. v1 ships a deep-link; live data lands when B's
      endpoint exists. Repo: deployment-api (proxy or UI-direct read) + deployment-ui.
- [ ] [CODE] P3. **Alert-parity audit** — walk every watcher/alert class (`ci-failure-watcher`, `promotion-lag-monitor`,
      git-health guard, billing block, consolidator watchdog) and verify each has a paired live state element on one of
      the two surfaces; file gaps as todos here. Repo: unified-trading-pm (audit) + the owning surface.

## Failure-injection verification matrix (operator add 2026-06-10 — completion gate for this master)

**This master is NOT complete until every CI-failure type/possibility has been VERIFIED ON THE MONITOR** — observed
rendering correctly on the dashboard, initially driven by agents, even where the failure must be mock-generated or
fake-triggered (a throwaway small change, a synthetic breaking change, a deliberately-failing check). Mock-mode fixtures
pin the UI contract, but the completion bar is the LIVE signal path: trigger → watcher/state → dashboard.

- [ ] [VERIFY] P1. **Stuck-PR classes ×5** — fake-trigger each (`conflicting`: PR with a manufactured conflict;
      `v2_never_reported`: a `[skip ci]`-free head pushed by a suppressing token; `skip_ci_jammed`: a `[skip ci]` head
      on a gated PR; `failing_check`: a deliberately red check; `automerge_stuck`: armed auto-merge held past threshold)
      and verify each renders in the Stuck panel with the right class + age. Repo: throwaway branches on a low-traffic
      repo; tear down after.
- [ ] [VERIFY] P1. **SIT lifecycle** — fake breaking change (or replay a real one): verify lock chip flips ON with
      reason, SIT-run panel shows the dispatched run in-progress → per-repo jobs → conclusion, `sit-passed` unlock
      clears the chip + breaking_pending, AND the Slack lock/unlock bookends both post. (Partially proven live
      2026-06-10 during the exec-svc 0.6.0 jam — re-verify on a CLEAN synthetic cycle with no manual dispatches.)
- [ ] [VERIFY] P1. **Cascade failure path** — synthetic dependent-QG failure mid-cascade: verify
      `stuck_in_sit`/cascade-failed state renders, downstream invalidation (`STAGING_PENDING`) shows on the matrix, and
      the escalation fires once (not per-tick).
- [ ] [VERIFY] P2. **Promotion-lag + drift states** — hold a commit on LDR without promoting: verify content-delta
      badges + lag rendering; verify squash-skew shows "in sync (squash skew)" not a phantom delta.
- [ ] [VERIFY] P2. **Image staleness** — land a main commit without a rebuild: verify `image_stale` flips; then rebuild
      and verify it clears.
- [ ] [VERIFY] P2. **Fleet git-health states** (sub-plan B surface) — dirty worktree, behind-LDR clone, killed reporter
      cron (`reporter_stale`), killed FF-pull cron (`ff_cron_stale`), drift violation — each fake-triggered on one slot
      and observed on the fleet page.
- [ ] [VERIFY] P3. **Billing-block + rate-limit** — simulate (or replay logs of) the GitHub Actions billing freeze + a
      GH rate-limit exhaustion: verify the dashboard degrades honestly (503 with retry_after; no fabricated rows).
- [ ] [DOCS] P3. Record the matrix outcomes as a `| failure class | trigger used | verified on | date |` table here; a
      class without a row is NOT covered (silence is not success).

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

| Item                                                                                                                                      | Where tracked                                     | State                          |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------ |
| deployment-api/deployment-ui/e2e content → `main` (drain converging; mtds#177/features#36/exec#250 PRs open; dep-api waits on bump PR#44) | this plan + dashboard stuck panel                 | IN-FLIGHT (pipeline-automatic) |
| Squash-body `[skip ci]` sanitization in Tier C promote                                                                                    | cicd_contract_hardening § bug #7                  | `- [ ]` P1                     |
| Failure-injection verification matrix (every alert class fake-triggered + seen on monitor)                                                | this plan § matrix                                | `- [ ]` P1–P3                  |
| Fleet git-health page (sub-plan B)                                                                                                        | fleet_git_health_orchestrator_2026_06_10.md       | orchestrator backlog           |
| GH_PAT `Checks: read` permission                                                                                                          | ci_dashboard plan + pings/slot_3.md               | BLOCKED-CREDENTIALS            |
| AWS/CodeBuild cloud-toggle parity for image signal                                                                                        | ci_dashboard plan                                 | `- [ ]` P1                     |
| `restart-deployment-stack.sh` must export GCP_PROJECT_ID (live 500 root cause on stack)                                                   | quality_gates_speed_and_config_ssot (filed below) | `- [ ]` P2                     |
| sit-repo full-workspace-sit report-back is LDR-only (inert until its main promotion)                                                      | cicd_contract_hardening conflict notes            | `- [ ]` P2                     |

## Codex SSOT updates (post-phase audit obligations)

- NEW `codex/03-observability/monitoring-control-plane.md` — the division-of-surfaces contract above + data-source
  architecture (hybrid GitHub-API+manifest, cache TTLs, Firestore swap point).
- `codex/04-architecture/agent-orchestrator-overview.md` — fleet git-health page section.
- `codex/08-workflows/ci-cd-flow.md` — pointer: the CI dashboard is the read surface for promotion state.

## Out of scope (named)

- Replacing Slack alerting or changing watcher cadences — alerting stays as-is; this master only adds read surfaces.
- Write actions from the CI dashboard (re-trigger v2, merge PRs) — read-only v1; any write surface is a future plan with
  its own auth review.

## Progress log

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
