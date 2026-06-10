---
title:
  "CI/CD repo dashboard — deployment-ui repo dropdown + branch×SHA matrix + stuck PRs + SIT state + image deploy signal"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only # slot-3 laptop — playwright-gated UI work; VMs have no dev server (BLOCKED-PLAYWRIGHT)
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
created: 2026-06-10
source:
  - operator direction 2026-06-10 (parent: plans/active/monitoring_control_plane_master_2026_06_10.md)
  - operator adds 2026-06-10 — stuck PRs first-class; stuck-in-SIT visible
related_plans:
  - plans/active/monitoring_control_plane_master_2026_06_10.md
  - plans/active/ci_status_firestore_side_store_2026_06_10.md
locked_by: live-defi-rollout
locked_since: 2026-06-10
---

# CI/CD repo dashboard (deployment-ui + deployment-api)

## Scope

A "Repos" surface in deployment-ui replacing 25 GitHub-UI visits: fleet overview matrix + per-repo drill-down (repo
dropdown) with SHA history across `live-defi-rollout`/`staging`/`main`, `quality-gates-v2` status, promotion PRs with
stuck detection, SIT state, and the image-level deploy signal. Read-only v1.

**Data architecture (operator decision — HYBRID)**: deployment-api aggregator = GitHub API (branch heads, compare, check
runs, PRs; `GH_PAT` from Secret Manager via `get_secret_client()`, never `os.environ`) behind a short TTL cache (60–120
s, mirroring the existing `TTL_BUILD_INFO` pattern in `_cloud_builds_trigger.py`) **+** `workspace-manifest.json` for
repo registry / `ci_status` (9-state) / `staging_status.breaking_pending` / `staging_commits` / `main_commits` /
`deployed_versions` / `promotion_failures` / `promotion_quarantine`. The manifest reader goes behind ONE accessor module
so the Firestore side-store (Phase 2 of `ci_status_firestore_side_store_2026_06_10.md`) is a one-function swap.

## Phase 1 — deployment-api aggregator (`deployment_api/routes/repo_ci.py` + `_repo_ci_*.py` helpers)

- [ ] [CODE] P1. `_repo_ci_manifest.py` — the single manifest accessor: repo registry (25 repos, type/tier/github_url),
      `ci_status`, `staging_status`, `staging_commits`/`main_commits`, `deployed_versions`, `promotion_failures`/
      `promotion_quarantine`. Fetches the manifest from the PM repo raw URL (origin `main`) with TTL cache; typed
      (TypedDict/pydantic — no `Any`), basedpyright-clean.
- [ ] [CODE] P1. `_repo_ci_github.py` — GitHub REST client (aiohttp; `GH_PAT` via `get_secret_client()`; TTL cache;
      honest rate-limit handling → 503 with `retry_after`, never silent stale): branch heads for LDR/staging/main, 3-way
      compare (ahead/behind + **changed-file count** — content delta, never squash-skewed commit counts per the LDR-SSOT
      rule), commit history per branch (limit N) with per-SHA `quality-gates-v2` check-run conclusion, open PRs
      targeting staging/main/LDR with state + mergeable + check rollup.
- [ ] [CODE] P1. `GET /api/repo-ci/overview` — fleet matrix: per repo {ci_status, branch heads (3×sha), content deltas
      LDR↔staging↔main, open promotion-PR count + worst stuck state, SIT state, last build status, deployed_version}.
      One response drives the overview table.
- [ ] [CODE] P1. `GET /api/repo-ci/{repo}/detail` — drill-down: commit history per branch (sha, msg, author [slot·host],
      time, v2 conclusion), open PRs (full stuck classification), SIT state + age, image signal.
- [ ] [CODE] P1. **Stuck-PR classification (operator add)** — port `ci_failure_watcher.py`'s signatures into a shared
      helper consumed by both endpoints: `v2_never_reported` (BLOCKED + no failed check + v2 absent from rollup),
      `conflicting` (CONFLICTING/DIRTY), `automerge_stuck` (auto-merge on, green, unmerged > threshold),
      `skip_ci_jammed` (head commit msg carries `[skip ci]`/`[ci skip]` + required check missing). Do NOT re-derive —
      lift the exact conditions from `unified-trading-pm/scripts/repo-management/ci_failure_watcher.py`.
- [ ] [CODE] P1. **SIT state (operator add)** — per repo: `in_breaking_pending` (manifest `staging_status`), staging
      lock state (`locked`/`locked_since`/`locked_reason`), last `cascade-qg-ordering`/SIT workflow run (status + age
      via GitHub runs API on unified-trading-pm), and `stuck_in_sit: true` when `ci_status == STAGING_GREEN` and
      time-in-state > threshold (default 2 h) without `SIT_VALIDATED`/`MAIN_GREEN`.
- [ ] [CODE] P1. **Live SIT run panel (operator add 2026-06-10 — alert-parity)** — the LAST cascade/SIT run's per-repo
      job breakdown, always visible (not just on failure):
      `sit_last_run {url, status, conclusion, age_min,     jobs: [{name, status, conclusion}]}` from the GitHub jobs API
      on the newest `cascade-qg-ordering` run — answers "which repos were in the last SIT run, which passed/failed,
      what's in progress" continuously.
- [ ] [CODE] P2. **Repo drill-down cross-links (operator add 2026-06-10 — don't redo existing tabs)** — repo detail
      panel deep-links the EXISTING surfaces for the same repo: data-status tab (domain/service), deployments/monitor
      tab (is it running), VM logs tab, and the orchestrator fleet git-health page filtered to the repo ("is this repo
      in anyone's worktree" — live data when sub-plan B's endpoint ships).
- [ ] [CODE] P1. **Image deploy signal (image-level v1)** — reuse `_cloud_builds_*` plumbing: last build per repo
      (status, sha, branch) + manifest `deployed_versions`; flag
      `image_stale: main_head_sha != last_successful_build_sha`.
- [ ] [CODE] P1. **AWS/GCP cloud-toggle parity for the build signal (operator add 2026-06-10)** — the image/build half
      of the aggregator must follow the deployment-ui cloud toggle like the existing Cloud Builds tab: GCP path reuses
      `_cloud_builds_trigger/_cloud_builds_history`; AWS path reuses `_code_builds_aws.py` (CodeBuild). The
      GitHub/manifest half is cloud-agnostic (no toggle). `_latest_builds_by_repo` returns honestly-unknown (None) for
      the inactive/unavailable provider — never fabricated.
- [ ] [TEST] P1. Unit tests: manifest accessor (fixture manifest), stuck-PR classifier (one case per signature),
      SIT-state derivation (pending/locked/stuck threshold), mocked-GitHub branch/compare shapes. Credential-free
      (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`); `pytest --block-network`.

## Phase 2 — deployment-ui "Repos" page

- [ ] [CODE] P1. [UI] API client additions in `src/api/client.ts` (typed: `RepoCiOverview`, `RepoCiDetail`,
      `StuckPrInfo`, `SitState` — no `any`).
- [ ] [CODE] P1. [UI] `ReposTab` route + nav entry: **fleet overview table** (25 rows: repo, ci_status chip, LDR/
      staging/main short-SHAs with content-delta badges, SIT chip, stuck-PR badge, build/deploy chip) with sort/filter;
      **repo dropdown** → drill-down panel: per-branch SHA history list (v2 conclusion icons), promotion PR cards (stuck
      class + age + link out to GitHub), SIT panel, image panel.
- [ ] [CODE] P1. [UI] **Stuck panel (operator add)** — fleet-wide "Stuck" section above the table listing every stuck
      PR + every stuck-in-SIT repo across all repos (the triage queue view), each with its classification + age.
- [ ] [TEST] P1. [UI] Vitest unit tests for the stuck/SIT chip logic + data mappers; `tsc --noEmit` + ESLint zero
      warnings; `NEXT_PUBLIC_MOCK_API`-equivalent mock-mode build smoke.

## Phase 3 — playwright gate (pw:L2 — HARD, deployment-ui is in the gated repo set)

- [ ] [TEST] P1. [UI] Smoke spec `tests/smoke/repos-tab.spec.ts` — tab renders, overview table populates (mock API),
      dropdown drill-down renders SHA history + PR cards. `npx playwright test --project=chromium tests/smoke/` exit 0.
- [ ] [TEST] P1. [UI] Regression spec `tests/e2e/repos-stuck-panel.spec.ts` — stuck-PR panel renders all four stuck
      classes + stuck-in-SIT badge from fixture data (guards reverting the operator-add features).

## Phase 4 — verify + ship

- [ ] [VERIFY] P1. Live run against real GitHub + manifest on the dev stack (`restart-deployment-stack.sh`): overview
      shows 25 repos; spot-check 3 repos' SHAs vs `gh api`; confirm current `breaking_pending` repos render the SIT
      chip; runtime-verified per the runtime-verification rule (run, wait, read logs, grep errors).
- [ ] [DOCS] P2. Codex: write `codex/03-observability/monitoring-control-plane.md` (master-plan obligation; this plan
      contributes the CI-dashboard + data-architecture sections); pointer line in `codex/08-workflows/ci-cd-flow.md`.

## Success criteria

- Repo dropdown + overview matrix answer branch/SHA/CI/PR/SIT/deploy state for all 25 repos without GitHub UI.
- All four stuck-PR classes + stuck-in-SIT render and are covered by a regression spec.
- QG green both repos; pw:L2 evidence on every UI tick (`— repo@sha | pw:L2 ✓ | regression: tests/...`).
- No new Slack emission (read-only surface).

## Out of scope (named successors)

- Runtime-level deploy signal, alert-history mirror, pipeline visualization, version-coherence + ratchet panels — master
  plan "Smart extras".
- Write actions (re-trigger v2, close/reopen PRs) — future plan with auth review.
