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
- [x] ✅ [INFRA] P1. **Create a GitHub App installation token for the read-only pollers** — `uts-ci-poller` GitHub App
      (App ID 4025197, installation 139531741) registered + installed on IggyIkenna account. Credentials stored in GCP
      SM (`gh-app-ci-poller-{app-id,private-key,installation-id}` in `central-element-323112`) and in GitHub Actions
      secrets on `unified-trading-pm`, `agent-orchestrator`, `deployment-api`. `promotion-lag-monitor.yml` switched to
      App pool via `actions/create-github-app-token@v1` (unified-trading-pm@9f3510c06 — push pending rate-limit reset).
      `agent-orchestrator` extended: `GhRateLimitMonitor(label="app")` second instance + `make_app_fetch_fn` (RS256
      JWT→installation token with 5-min-before-expiry cache) + `/api/gh-rate-limit` returns `app:{}` sub-object.
      `pyjwt[cryptography]` declared explicitly. agent-orchestrator@16924e2 — QG 487 passed | push pending rate-limit
      reset. **Deployment**: vm-0 needs `GH_APP_CI_POLLER_{APP_ID,PRIVATE_KEY,INSTALLATION_ID}` from SM to activate App
      monitor.
- [x] ✅ [PERF] P2. **ETag `promotion_lag_monitor.py` + persist via actions/cache** — the safe, high-value realization
      of the burn-reduction below: the lag monitor compares **25 repos × 4 directions = ~100 `gh api compare` calls/run
      × 3 runs/hr = ~300 PAT calls/hr** (a bigger burner than CIReconcile, and a pure read-only monitor = low blast
      radius). Added `If-None-Match` to the single `_gh_json` chokepoint (304 = free) + `actions/cache` (rolling key) to
      persist the ETag cache across the ephemeral runs → unchanged branch-pairs cost ~0. unified-trading-pm@3b249db (PR
      #240→main) | 8 ETag tests | basedpyright clean. (`ci_failure_watcher` mixes `gh pr list` CLI calls that don't take
      If-None-Match directly — left for a dedicated conversion-to-`gh api` change.)
- [ ] [INFRA] P2 (residual). **Token-pool split for the promotion/monitor Actions** — `ldr-to-main-promote.yml` /
      `ldr-to-staging-promote.yml` / `ci-failure-watcher` still run `GH_TOKEN: ${{ secrets.GH_PAT }}`. **NOT a safe
      blind swap**: the built-in `GITHUB_TOKEN` is (a) **repo-scoped** (cross-repo monitors/promoters need the PAT) and
      (b) **can't trigger downstream workflows** (a `GITHUB_TOKEN`-opened promotion PR won't fire `quality-gates-v2`).
      Safe subset: switch ONLY same-repo READ-only `gh` calls to `GITHUB_TOKEN`; keep the PAT for cross-repo reads + the
      PR-create/merge that must trigger v2. Target: `unified-trading-pm` (workflow templates). High blast radius —
      dedicated, tested change, not a drive-by.
- [ ] [DEPS] P2. **Ship the features-service `pyyaml>=6.0.0 → >=6.0.1` alignment** (surfaced 2026-06-11 while shipping
      the above): features-service was the **lone fleet outlier** vs the canonical `>=6.0.1` (every other repo + both
      `workspace-constraints.toml` + `canonical-dependency-manifest.json`), which **red-gates all PM scripts pushes**
      via the alignment check. The 1-line fix (pyproject + uv.lock, no resolved-version change → no cascade) is
      **staged + QG-green in slot-1** but its quickmerge is **BLOCKED**: a live concurrent session is mid-edit on UAC
      `external/databento` (`__init__.py` + new `databento_classifier.py`) in slot-1's UAC clone, and features-service
      quickmerge correctly refuses to ship a consumer with a dirty dep — I won't stomp the foreign WIP. Ship once UAC
      commits:
      `cd features-service && bash scripts/quality-gates.sh --no-fix && bash scripts/quickmerge.sh "fix(deps): align pyyaml floor to canonical >=6.0.1" --agent --files 'pyproject.toml uv.lock'`.
      Target repo: `features-service`.
- [x] N/A [UI] P2. ~~Same tracker in unified-trading-system-ui~~ — **dropped**: uts-ui has **no** repo/CI/git-health
      surface (verified 2026-06-10, 0 matches) → no natural home. The repos surface lives in deployment-ui (above) + the
      orchestrator dashboard (shipped). Re-open only if uts-ui gains a CI/repos view.

## Firebase read-cache strategy (operator direction 2026-06-11)

Write GitHub state to Firestore on every scheduled poll; all UI/dashboard reads hit Firestore instead of calling the
GitHub API. Firebase is free-tier generous + a separate quota domain — zero PAT/App REST calls for reads. The pattern
extends the existing `resolve_ci_status_map` Firestore-authoritative path (Phase-2 primitive landed in PM@6b1ece9e1).

- [x] ✅ [INFRA] P2. DONE 2026-06-11 (slot-1) — **Firestore write-through for `promotion-lag-monitor`**: added
      `_write_firestore_promotion_lag()` to `scripts/cicd/promotion_lag_monitor.py`; writes 25-repo × 4-direction
      structured lag dict to `repo_state/{repo}/promotion_lag` in Firestore. Added GCP auth + Firestore SDK install
      steps to `promotion-lag-monitor.yml`; `GOOGLE_CLOUD_PROJECT` env var gating. unified-trading-pm@ca095c7b0.
- [x] ✅ [INFRA] P2. DONE 2026-06-11 (slot-1) — **Firestore write-through for `ci-failure-watcher`**: added
      `_write_firestore_ci_watcher()` to `scripts/repo-management/ci_failure_watcher.py`; writes per-repo transitions +
      stuck PR lists to `repo_state/{repo}/ci_watcher` in Firestore. Added GCP auth + Firestore SDK install steps to
      `ci-failure-watcher.yml`; `GOOGLE_CLOUD_PROJECT` env var gating. unified-trading-pm@ca095c7b0.
- [ ] [INFRA] P3. **Firestore write-through for `reconcile-release-tags`** — persist latest tag per repo to Firestore;
      downstream tag-readers query Firestore instead of GitHub API. Target: `unified-trading-pm`.

**Architecture note**: Firestore write happens in the scheduled GHA runner (has PAT budget, writes once per cycle); all
read consumers (orchestrator API, deployment-api, UIs) query Firestore (zero GitHub quota, fast, free). The App token
pool covers the remaining read-only GHA runners. This is the durable structural fix beyond ETag caching.

## Recommended decision

The ETag win + free rate monitor are the big easy wins (shipped). The durable structural fix is the GitHub App token (a
genuinely separate budget, shipped 2026-06-11) + Firebase read-cache for polling consumers (direction set 2026-06-11).
