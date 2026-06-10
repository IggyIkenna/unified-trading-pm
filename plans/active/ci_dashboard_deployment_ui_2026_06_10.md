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

- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a (ManifestView accessor; ci_status_for = Firestore swap
      point; 7 unit tests). Was: `_repo_ci_manifest.py` — the single manifest accessor: repo registry (25 repos,
      type/tier/github_url), `ci_status`, `staging_status`, `staging_commits`/`main_commits`, `deployed_versions`,
      `promotion_failures`/ `promotion_quarantine`. Fetches the manifest from the PM repo raw URL (origin `main`) with
      TTL cache; typed (TypedDict/pydantic — no `Any`), basedpyright-clean.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a (aiohttp + SM GH_PAT + TTL cache + honest 503;
      content-delta compare). Was: `_repo_ci_github.py` — GitHub REST client (aiohttp; `GH_PAT` via
      `get_secret_client()`; TTL cache; honest rate-limit handling → 503 with `retry_after`, never silent stale): branch
      heads for LDR/staging/main, 3-way compare (ahead/behind + **changed-file count** — content delta, never
      squash-skewed commit counts per the LDR-SSOT rule), commit history per branch (limit N) with per-SHA
      `quality-gates-v2` check-run conclusion, open PRs targeting staging/main/LDR with state + mergeable + check
      rollup.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a; live-verified: 25 repos, 13.9 s cold / TTL-cached after.
      Was: `GET /api/repo-ci/overview` — fleet matrix: per repo {ci_status, branch heads (3×sha), content deltas
      LDR↔staging↔main, open promotion-PR count + worst stuck state, SIT state, last build status, deployed_version}.
      One response drives the overview table.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a; live-verified on greeks-service (3-branch history,
      slot-attributed authors). Was: `GET /api/repo-ci/{repo}/detail` — drill-down: commit history per branch (sha, msg,
      author [slot·host], time, v2 conclusion), open PRs (full stuck classification), SIT state + age, image signal.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a (`_repo_ci_stuck.py` ports watcher signatures; first live
      run surfaced 10 real conflict-wall PRs). Was: **Stuck-PR classification (operator add)** — port
      `ci_failure_watcher.py`'s signatures into a shared helper consumed by both endpoints: `v2_never_reported`
      (BLOCKED + no failed check + v2 absent from rollup), `conflicting` (CONFLICTING/DIRTY), `automerge_stuck`
      (auto-merge on, green, unmerged > threshold), `skip_ci_jammed` (head commit msg carries `[skip ci]`/`[ci skip]` +
      required check missing). Do NOT re-derive — lift the exact conditions from
      `unified-trading-pm/scripts/repo-management/ci_failure_watcher.py`.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a (derive_sit_state; breaking_pending five rendered live).
      Was: **SIT state (operator add)** — per repo: `in_breaking_pending` (manifest `staging_status`), staging lock
      state (`locked`/`locked_since`/`locked_reason`), last `cascade-qg-ordering`/SIT workflow run (status + age via
      GitHub runs API on unified-trading-pm), and `stuck_in_sit: true` when `ci_status == STAGING_GREEN` and
      time-in-state > threshold (default 2 h) without `SIT_VALIDATED`/`MAIN_GREEN`.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a (sit_last_run via runs+jobs API; showed the live cascade
      in-progress during verify). Was: **Live SIT run panel (alert-parity)** — the LAST cascade/SIT run's per-repo job
      breakdown, always visible (not just on failure):
      `sit_last_run {url, status, conclusion, age_min,     jobs: [{name, status, conclusion}]}` from the GitHub jobs API
      on the newest `cascade-qg-ordering` run — answers "which repos were in the last SIT run, which passed/failed,
      what's in progress" continuously.
- [ ] [CODE] P2. **Repo drill-down cross-links (operator add 2026-06-10 — don't redo existing tabs)** — repo detail
      panel deep-links the EXISTING surfaces for the same repo: data-status tab (domain/service), deployments/monitor
      tab (is it running), VM logs tab, and the orchestrator fleet git-health page filtered to the repo ("is this repo
      in anyone's worktree" — live data when sub-plan B's endpoint ships).
- [x] ✅ [CODE] P1. DONE 2026-06-10 — deployment-api@093f80a (trigger-list + latest-builds reuse, 300 s cache,
      image*stale; AWS side = honest-unknown pending cloud-toggle todo). Was: **Image deploy signal (image-level v1)** —
      reuse
      `\_cloud_builds*\*`plumbing: last build per repo     (status, sha, branch) + manifest`deployed_versions`; flag     `image_stale:
      main_head_sha != last_successful_build_sha`.
- [ ] [CODE] P1. **AWS/GCP cloud-toggle parity for the build signal (operator add 2026-06-10)** — the image/build half
      of the aggregator must follow the deployment-ui cloud toggle like the existing Cloud Builds tab: GCP path reuses
      `_cloud_builds_trigger/_cloud_builds_history`; AWS path reuses `_code_builds_aws.py` (CodeBuild). The
      GitHub/manifest half is cloud-agnostic (no toggle). `_latest_builds_by_repo` returns honestly-unknown (None) for
      the inactive/unavailable provider — never fabricated.
- [x] ✅ [TEST] P1. DONE 2026-06-10 — deployment-api@093f80a (31 tests across test_repo_ci_stuck/manifest/routes.py;
      mock fixtures pin every stuck class). Was: Unit tests: manifest accessor (fixture manifest), stuck-PR classifier
      (one case per signature), SIT-state derivation (pending/locked/stuck threshold), mocked-GitHub branch/compare
      shapes. Credential-free (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`); `pytest --block-network`.

### Live-verify findings (2026-06-10, slot-3)

- [ ] [CREDS] P2. **BLOCKED-CREDENTIALS — GH_PAT lacks `Checks: read`**: live run returns 403 "Resource not accessible
      by personal access token" on `/commits/{sha}/check-runs` → per-SHA `quality-gates-v2` conclusions degrade to
      unknown (handled gracefully — shard-level isolation, never response-fatal). Operator ask: add **Checks: read** to
      the fine-grained GH_PAT (Secret Manager `GH_PAT`, both clouds). Ping: `ikenna_orchestrator/pings/slot_3.md`
      2026-06-10.
- [ ] [CODE] P3. Overview response surfaces per-repo aggregation errors (an `errors[]` block) instead of silently
      dropping a degraded row — found during live verify (rows degrade on per-repo GitHub 5xx; currently log-only).

## Phase 2 — deployment-ui "Repos" page

- [x] ✅ [CODE] P1. [UI] DONE 2026-06-10 — deployment-ui@3998a4d | pw:L2 ✓ (164/164 smoke) | regression:
      tests/e2e/repos-stuck-panel.spec.ts. Was: API client additions in `src/api/client.ts` (typed: `RepoCiOverview`,
      `RepoCiDetail`, `StuckPrInfo`, `SitState` — no `any`).
- [x] ✅ [CODE] P1. [UI] DONE 2026-06-10 — deployment-ui@3998a4d (`/repos` RepoCi page + 'Repos CI' nav) | pw:L2 ✓
      (164/164 smoke) | regression: tests/smoke/repos-tab.spec.ts. Was: `ReposTab` route + nav entry: **fleet overview
      table** (25 rows: repo, ci_status chip, LDR/ staging/main short-SHAs with content-delta badges, SIT chip, stuck-PR
      badge, build/deploy chip) with sort/filter; **repo dropdown** → drill-down panel: per-branch SHA history list (v2
      conclusion icons), promotion PR cards (stuck class + age + link out to GitHub), SIT panel, image panel.
- [x] ✅ [CODE] P1. [UI] DONE 2026-06-10 — deployment-ui@3998a4d | pw:L2 ✓ (164/164 smoke) | regression:
      tests/e2e/repos-stuck-panel.spec.ts. Was: **Stuck panel (operator add)** — fleet-wide "Stuck" section above the
      table listing every stuck PR + every stuck-in-SIT repo across all repos (the triage queue view), each with its
      classification + age.
- [x] ✅ [TEST] P1. [UI] DONE 2026-06-10 — deployment-ui@3998a4d (repoCi.test.ts 8/8; full suite 774; tsc + eslint
      zero-warning; build smoke green). Was: Vitest unit tests for the stuck/SIT chip logic + data mappers;
      `tsc --noEmit` + ESLint zero warnings; `NEXT_PUBLIC_MOCK_API`-equivalent mock-mode build smoke.

- [ ] [CODE] P1. [UI] **Per-service "CI" tab (operator add 2026-06-10)** — reuse the repo drill-down panel inside the
      home per-service tab system (next to Builds/Data Status), so a selected service shows its branches/PRs/SIT without
      leaving the service context. Note: some deployment service names ≠ repo names (e.g. features-delta-one-service vs
      features-service) — map or degrade honestly.
- [ ] [CODE] P1. **Fleet git-health INTO deployment-ui (operator decision v2)** — deployment-api proxy of the
      orchestrator's `/api/fleet/git-health` (server-side token) + a deployment-ui page rendering hosts×slots×repos;
      lands when sub-plan B's endpoint ships. Repo: deployment-api + deployment-ui (+ cross-ref
      fleet_git_health_orchestrator_2026_06_10.md Phase 2 note).

## Phase 3 — playwright gate (pw:L2 — HARD, deployment-ui is in the gated repo set)

- [x] ✅ [TEST] P1. [UI] DONE 2026-06-10 — deployment-ui@3998a4d | pw:L2 ✓ (164/164 smoke) | regression:
      tests/smoke/repos-tab.spec.ts. Was: Smoke spec — tab renders, overview table populates (mock API), dropdown
      drill-down renders SHA history + PR cards. `npx playwright test --project=chromium tests/smoke/` exit 0.
- [x] ✅ [TEST] P1. [UI] DONE 2026-06-10 — deployment-ui@3998a4d | pw:L2 ✓ (164/164 smoke) | regression:
      tests/e2e/repos-stuck-panel.spec.ts (all five stuck classes + stuck-in-SIT + SIT-run jobs). Was: Regression spec —
      stuck-PR panel renders all four stuck classes + stuck-in-SIT badge from fixture data (guards reverting the
      operator-add features).

## Phase 4 — verify + ship

- [x] ✅ [VERIFY] P1. DONE 2026-06-10 — slot-3 :8014 live run: overview 25 repos (source=live), detail greeks-service,
      breaking_pending five render SIT chips, 10 real stuck PRs surfaced; runtime-verified (logs grepped, errors fixed:
      get_secret_client kwarg, 403 shard-isolation). Was: Live run against real GitHub + manifest on the dev stack
      (`restart-deployment-stack.sh`): overview shows 25 repos; spot-check 3 repos' SHAs vs `gh api`; confirm current
      `breaking_pending` repos render the SIT chip; runtime-verified per the runtime-verification rule (run, wait, read
      logs, grep errors).
- [x] ✅ [DOCS] P2. DONE 2026-06-10 — unified-trading-pm@8b23c4745 (+ ci-cd-flow.md cascade/SIT-loop updates
      @197b4373a). Was: Codex: write `codex/03-observability/monitoring-control-plane.md` (master-plan obligation; this
      plan contributes the CI-dashboard + data-architecture sections); pointer line in
      `codex/08-workflows/ci-cd-flow.md`.

## Success criteria

- Repo dropdown + overview matrix answer branch/SHA/CI/PR/SIT/deploy state for all 25 repos without GitHub UI.
- All four stuck-PR classes + stuck-in-SIT render and are covered by a regression spec.
- QG green both repos; pw:L2 evidence on every UI tick (`— repo@sha | pw:L2 ✓ | regression: tests/...`).
- No new Slack emission (read-only surface).

## Out of scope (named successors)

- Runtime-level deploy signal, alert-history mirror, pipeline visualization, version-coherence + ratchet panels — master
  plan "Smart extras".
- Write actions (re-trigger v2, close/reopen PRs) — future plan with auth review.
