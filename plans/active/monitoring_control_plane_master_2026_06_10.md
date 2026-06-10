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

- [ ] [CODE] P2. **Alert-history mirror** — every Slack alert the watchers post (`ci-failure-watcher`,
      `promotion-lag-monitor`, git-health guard) also lands in a queryable store surfaced on the CI dashboard, so
      false-positive triage has a ledger and "did this alert before?" is answerable without Slack scrollback. Repo:
      unified-trading-pm (emit side) + deployment-api/deployment-ui (read side).
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

## Codex SSOT updates (post-phase audit obligations)

- NEW `codex/03-observability/monitoring-control-plane.md` — the division-of-surfaces contract above + data-source
  architecture (hybrid GitHub-API+manifest, cache TTLs, Firestore swap point).
- `codex/04-architecture/agent-orchestrator-overview.md` — fleet git-health page section.
- `codex/08-workflows/ci-cd-flow.md` — pointer: the CI dashboard is the read surface for promotion state.

## Out of scope (named)

- Replacing Slack alerting or changing watcher cadences — alerting stays as-is; this master only adds read surfaces.
- Write actions from the CI dashboard (re-trigger v2, merge PRs) — read-only v1; any write surface is a future plan with
  its own auth review.
