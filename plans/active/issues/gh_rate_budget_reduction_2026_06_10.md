---
title: GitHub API rate-budget reduction + low-budget alerting/visibility (shared-PAT exhaustion)
created: 2026-06-10
source:
  - chat/2026-06-10 operator: "how can we use less gh rates without hurting functionality" + "slack alert when approaching rate limits" + "tracker inside the /repos page in the deployment UIs"
  - live probe 2026-06-10: gh core REST remaining=0/5000 (fleet-exhausted) → CIReconcile 403-blinded
locked_by: live-defi-rollout
priority: P1
status: active
---

## What I found

The whole fleet authenticates `gh` as **one** GitHub user (a classic PAT). GitHub's primary REST limit (5000 req/hr) is
**per user** — every PAT for that user draws from the SAME pool — so the orchestrator's CI-reconcile poll, the promotion
bots, and each slot worker's `gh` calls all compete for one 5000/hr REST budget. Live probe 2026-06-10:
`core remaining=0/5000` (fully exhausted) → CIReconcile's per-repo `gh run list` 403s and goes blind ("no failing
repos"). GraphQL is a **separate** 5000-point pool (3327 remaining at probe time); the `rate_limit` endpoint itself is
**free** (does not count against any pool).

## Why it matters

A blinded CIReconcile silently stops routing `ldr_qg_failure` fixers — LDR test breaks sit red unnoticed. Per-user
budgeting means a second PAT for the same account does **not** help (it correlates to the same pool).

## Shipped 2026-06-10 (agent-orchestrator)

- [x] ✅ [CODE] P0. **ETag conditional requests in CIReconcile** — `repo_ldr_qg_conclusion` now uses `gh api -i` with
      `If-None-Match`; a `304 Not Modified` (unchanged run, the common case between 15-min sweeps) is **free**
      (verified: 3× 304 cost 0 rate, 1× 200 cost 1). ~90%+ fewer _counted_ REST calls, identical freshness.
      agent-orchestrator@481232d | QG 465 passed.
- [x] ✅ [CODE] P0. **GhRateLimitMonitor + GRADUATED Slack alerts** — polls the free `rate_limit` endpoint every 120s
      and fires escalating alerts as `core`/`graphql` crosses **50% (NOTICE) / 80% (WARNING) / 95% (HIGH) / 100%
      (CRITICAL) used**, each **with the reset time**. Fires once per crossing; re-arms when usage drops below a level
      (5-pt hysteresis); a budget reset re-arms all levels (`notify_gh_rate_limit_threshold`, `USED_THRESHOLDS`).
      agent-orchestrator@60c2035 (graduated; was bfe62fd single-threshold) | deployed vm-0
      (used-thresholds=[50,80,95,100]%).
- [x] ✅ [CODE] P1. **`GET /api/gh-rate-limit`** snapshot endpoint + **FleetGit (Fleet Git-Health) tracker widget**
      (REST + GraphQL budget bars, red<10%/amber<25%). agent-orchestrator@bfe62fd | dashboard rebuilt on vm-0.

## Open todos (cross-repo fan-out + structural levers)

- [x] ✅ [CODE] P2. **Persist the CIReconcile ETag cache across restarts** (`data/state/ci_reconcile_etag_cache.json`,
      gitignored runtime). A cold in-memory cache couldn't make the first un-conditioned 200 to capture an ETag while
      `core` was already at 0 → 403 until the hourly reset (observed right after the first deploy). Disk-backed now via
      `load_etag_cache`/`save_etag_cache` (guarded to the real poll path — no disk I/O under an injected conclusion_fn).
      agent-orchestrator@6a78f1c | deployed vm-0.
- [x] ✅ [UI] P1. **GitHub rate-budget tracker in deployment-ui** (the v2 PRIMARY operator view) — renders on the
      **Repos-CI page** (`/repos`, `RepoCiContent` header — the dedicated repos+CI dashboard; relocated from the
      Coverage tab where the first pass landed it): REST+GraphQL budget bars, `rateBudgetTone` red<10%/amber<25%, polls
      the deployment-api `/api/repos/gh-rate-limit` every 60s. `src/api/ghRateLimit.ts` +
      `src/components/GhRateBudget.tsx` (+ mock handler). deployment-ui@a4f61e8 (relocated; built on 1ef784c) | tsc
      clean | vitest 8/8 | **pw:L2 ✓** regression: `tests/smoke/gh_rate_budget.spec.ts` (navigates to /repos).
- [x] ✅ [PERF] P1. **ETag `deployment-api/deployment_api/routes/_repo_ci_github.py`** — the **biggest** fleet REST
      burner (~8 GitHub calls × ~25 repos per coverage refresh). `If-None-Match` added to the shared `gh_get_json` (304
      = free; TTL-cache extended to hold the ETag + last body) + the free `GET /api/repos/gh-rate-limit` route
      (mock-mode aware). deployment-api@061a1b5f | QG green (170s) | 5 ETag tests. This is the dominant REST reduction.
- [ ] [INFRA] P1 (**BLOCKED-OPERATOR-DECISION**). **Create a GitHub App installation token for the read-only pollers** —
      a GitHub App gets its OWN rate pool (separate from the user PAT), giving the fleet a second 5000+/hr REST budget
      without touching the workers' push PAT. **Operator-gated**: the current PAT lacks app-management scope
      (`admin:public_key, gist, read:org, repo`) + App registration needs the GitHub UI/manifest flow — an agent cannot
      create it. Decision: register an App (recommended) vs. live with the shared PAT + the ETag wins. Once it exists,
      point CIReconcile + the rate monitor + deployment-api reads at it. Target repos: `agent-orchestrator` +
      `deployment-api` (+ `deployment-service` secret wiring).
- [ ] [INFRA] P2. **The promotion/monitor Actions burn the shared PAT, not the free per-repo `GITHUB_TOKEN`** (verified
      2026-06-10): `ldr-to-main-promote.yml` / `ldr-to-staging-promote.yml` / `ci-failure-watcher` /
      `promotion-lag-monitor.yml` all run `runs-on: ubuntu-latest` with `GH_TOKEN: ${{ secrets.GH_PAT }}` (+ checkout
      `token: GH_PAT`). At `*/15`–`*/20` across the fleet this is a **major** continuous draw on the same 5000/hr pool
      that CIReconcile competes for. **NOT a safe blind swap** (this is why it's P2, not a quick fix): the built-in
      `GITHUB_TOKEN` (a) is **repo-scoped** — a PM-run workflow can't read OTHER repos' runs with it, so cross-repo
      monitors/promoters genuinely need the PAT; and (b) **cannot trigger downstream workflows** — a promotion PR opened
      with `GITHUB_TOKEN` won't fire `quality-gates-v2`, which is the whole point of the PAT here. Safe subset to pursue
      in a dedicated, tested change: switch ONLY the same-repo READ-only `gh` calls (run lists / compares / rate checks)
      to `GITHUB_TOKEN`, keep the PAT for the cross-repo reads + the PR-create/merge that must trigger v2. Target repos:
      `unified-trading-pm` (workflow templates → `rollout-workflow-templates.sh`). High blast radius (promotion
      pipeline) — own change + verification, not a drive-by edit.
- [x] N/A [UI] P2. ~~Same tracker in unified-trading-system-ui~~ — **dropped**: uts-ui has **no** repo/CI/git-health
      surface (verified 2026-06-10, 0 matches) → no natural home. The repos surface lives in deployment-ui (above) + the
      orchestrator dashboard (shipped). Re-open only if uts-ui gains a CI/repos view.

## Recommended decision

The ETag win + free rate monitor are the big easy wins (shipped). The durable structural fix is the GitHub App token (a
genuinely separate budget) — recommend prioritising the INFRA P1 above; a same-account second PAT is a non-fix (shared
per-user pool).
