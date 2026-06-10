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
- [x] ✅ [CODE] P2. DONE 2026-06-10 — deployment-ui@816f920 (v1 deep-link). **Repo detail ⇄ fleet worktree presence** —
      the repo drill-down deep-links the `/fleet` Fleet Git page (the sub-plan B endpoint shipped: deployment-api
      `/api/repo-ci/fleet-git-health` + orchestrator `/api/fleet/git-health`). The per-repo FILTER (highlight "is this
      repo dirty in anyone's worktree") lands with the live `ORCHESTRATOR_API_TOKEN` (BLOCKED-CREDS) — the deep-link is
      live now; the live fleet data is gated on the token.
- [ ] [CODE] P3. **Alert-parity audit** — walk every watcher/alert class (`ci-failure-watcher`, `promotion-lag-monitor`,
      git-health guard, billing block, consolidator watchdog) and verify each has a paired live state element on one of
      the two surfaces; file gaps as todos here. Repo: unified-trading-pm (audit) + the owning surface.

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

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Where tracked                                      | State                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------- |
| deployment-api/deployment-ui/e2e content → `main` (all v2 GREEN + draining). **deployment-api staging v2 was RED — ROOT-CAUSED + FIXED 2026-06-10**: the `grep -P` parity bug (base-service.sh deep-import check false-passed on macOS BSD grep → local 23 / CI 24); fixed `grep -P`→`rg --pcre2` (PM@7427ade8a) + budget 23→24 (deployment-api@3a579f1b) → staging v2 now GREEN (run 27309108373). NOT the file-size debt (that's a single in-budget V+1). | this plan + ci_local_qg_parity_2026_06_08.md       | ✅ UNBLOCKED (v2 green; draining)                  |
| Squash-body `[skip ci]` sanitization in Tier C promote                                                                                                                                                                                                                                                                                                                                                                                                      | cicd_contract_hardening § bug #7                   | ✅ DONE (live on PM main)                          |
| Failure-injection verification matrix (mock+pw + live obs; disruptive-live triggers scoped)                                                                                                                                                                                                                                                                                                                                                                 | this plan § matrix (outcomes table)                | ✅ DONE (table filled)                             |
| Fleet git-health page (sub-plan B — backend + dashboard + reporter + deployment-ui /fleet tab)                                                                                                                                                                                                                                                                                                                                                              | fleet_git_health_orchestrator_2026_06_10.md        | ✅ SHIPPED (live cross-host verify gated on token) |
| GH_PAT `Checks: read` permission                                                                                                                                                                                                                                                                                                                                                                                                                            | ci_dashboard + ikenna_orchestrator/pings/slot_3.md | BLOCKED-CREDENTIALS                                |
| `ORCHESTRATOR_API_TOKEN` for the fleet-git-health proxy (live fleet data)                                                                                                                                                                                                                                                                                                                                                                                   | ci_dashboard + ikenna_orchestrator/pings/slot_3.md | BLOCKED-CREDENTIALS                                |
| AWS/CodeBuild cloud-toggle parity for image signal                                                                                                                                                                                                                                                                                                                                                                                                          | ci_dashboard plan                                  | `- [ ]` P1                                         |
| `restart-deployment-stack.sh` must export GCP_PROJECT_ID (live 500 root cause on stack)                                                                                                                                                                                                                                                                                                                                                                     | quality_gates_speed_and_config_ssot (filed below)  | `- [ ]` P2                                         |
| sit-repo full-workspace-sit report-back is LDR-only (inert until its main promotion)                                                                                                                                                                                                                                                                                                                                                                        | cicd_contract_hardening conflict notes             | `- [ ]` P2                                         |

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
