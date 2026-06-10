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
- [x] ✅ [CODE] P0. **GhRateLimitMonitor + Slack alert** — polls the free `rate_limit` endpoint every 120s, Slack-alerts
      (state-transition deduped, hysteresis-cleared at 25%) when `core`/`graphql` drops below 10% remaining
      (`notify_gh_rate_limit_low`). agent-orchestrator@bfe62fd | deployed vm-0 (running, interval=120s).
- [x] ✅ [CODE] P1. **`GET /api/gh-rate-limit`** snapshot endpoint + **FleetGit (Fleet Git-Health) tracker widget**
      (REST + GraphQL budget bars, red<10%/amber<25%). agent-orchestrator@bfe62fd | dashboard rebuilt on vm-0.

## Open todos (cross-repo fan-out + structural levers)

- [ ] [UI] P1. **Add the GitHub rate-budget tracker to the deployment-ui /repos page** (the v2 PRIMARY operator view per
      `fleet_git_health_orchestrator_2026_06_10.md`). Consume `GET /api/gh-rate-limit` (shape:
      `{fetched_at, alert_pct, alerted:[...], resources:{core:{limit,remaining,used,reset}, graphql:{...}}}`). Mirror
      the orchestrator-dashboard `FleetGit.tsx` `GhRateLimit` component + `rateBudgetTone` mapper. Target repo:
      `deployment-ui`. (pw:L2 + regression spec required per the UI playwright gate.)
- [ ] [UI] P2. **Same tracker in unified-trading-system-ui** wherever it surfaces repo/CI health. Target repo:
      `unified-trading-system-ui`.
- [ ] [INFRA] P1. **Evaluate a GitHub App installation token for the orchestrator's read-only pollers** — a GitHub App
      gets its OWN rate pool (separate from the user PAT), so moving CIReconcile + the rate monitor + promotion-lag
      reads onto an App token gives the fleet a second 5000+/hr budget without touching the workers' push PAT. Confirm
      the App can read Actions runs (the classic PAT could NOT read `checkSuites` via GraphQL —
      `Resource not accessible by personal access token`). Target repo: `agent-orchestrator` (+ deployment-service for
      the App creds/secret wiring).
- [ ] [INFRA] P2. **Audit the top REST burners across the fleet on the shared PAT** and ETag/cache them — the
      orchestrator poll is now cheap, but slot-worker `gh` usage + the `ci-failure-watcher` / `promotion-lag-monitor` /
      promote-bot crons still draw from the same pool. Confirm Actions-triggered work uses the per-repo `GITHUB_TOKEN`
      (separate 1000/hr/repo pool), not the PAT. Target repos: `agent-orchestrator`, `unified-trading-pm` (workflow
      templates).

- [ ] [CODE] P2. **Persist the CIReconcile ETag cache across restarts** (small JSON under `data/`). The cache is
      in-memory today, so a service restart while `core` is already at 0 can't make the first (un-conditioned) 200 to
      capture an ETag → that cold sweep 403s until the hourly reset (observed 2026-06-10 right after deploy). A
      disk-persisted cache survives restarts so 304s keep flowing even through an exhausted window. Target repo:
      `agent-orchestrator`.

## Recommended decision

The ETag win + free rate monitor are the big easy wins (shipped). The durable structural fix is the GitHub App token (a
genuinely separate budget) — recommend prioritising the INFRA P1 above; a same-account second PAT is a non-fix (shared
per-user pool).
