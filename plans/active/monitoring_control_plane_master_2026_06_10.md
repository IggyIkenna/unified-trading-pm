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
- [ ] [CODE] P2. **(N2) Last-green SHA + time column** on the `/repos` overview — per repo per branch, the most-recent
      SHA whose `quality-gates-v2` concluded success + its timestamp ("green as of <sha> · <age>"). Distinct from the
      current branch-head SHA (head may be red/pending). **UNBLOCKED 2026-06-11** — Ikenna's Actions-API conversion
      (below) removes the Checks:read dependency; the per-SHA v2 conclusion now comes from
      `/actions/workflows/quality-gates-v2.yml/runs?head_sha=`. Build N2 on `v2_conclusion_for_sha` once Ikenna's
      `_repo_ci_github.py` conversion lands on LDR. Repo: deployment-api + deployment-ui.

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
- [ ] [CODE] P3. **Version-coherence panel** — `assert_version_coherence.py` verdicts (VERSION_SPLIT /
      VESTIGIAL_SCALAR_DRIFT / DEP_FLOOR_UNSATISFIABLE) per repo on the dashboard. Repo: deployment-api (run/ingest) +
      deployment-ui.
- [ ] [CODE] P3. **Rollout-ratchet panels** — workflow-template drift (`detect_template_drift.py`) + Dockerfile
      digest-pin conversion status per repo. Repo: deployment-api + deployment-ui.
- [ ] [CODE] P3. **Runtime-level deploy signal (v2 of decision 4)** — resolve what is RUNNING (deployment registry /
      Cloud Run revisions / VM heartbeats) and diff its SHA vs `main` HEAD. Repo: deployment-api + deployment-ui.

### Operator enhancements (2026-06-11, Harsh + Ikenna)

- [x] ✅ [CODE] [UI] P1. DONE 2026-06-11 — deployment-api@0676afc (signal fields) + deployment-api@3c29dac
      (trigger-region fix) + deployment-api@98d0d40 (build-LIST region + REPO_NAME match — completes the fix) +
      deployment-ui@c984541 + deployment-ui@1ad86d5 (sha render) | pw:L2 ✓ | regression:
      tests/e2e/repos-promotion-blocked.spec.ts. **(B1) Image/build column — real status, not "unknown".** **ROOT CAUSE
      was a region mismatch in TWO places, fixed in two commits:** (1) `3c29dac` pinned
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
- [ ] [CODE] P1. **(B1-followup) `gcs_region=us-central1` prod-config anomaly — BIG FINDING** — the running prod
      deployment-api reports `gcs_region: us-central1` + `zones: us-central1-a/b/c` while ALL data + Cloud Build
      triggers + the Artifact Registry are in `asia-northeast1` (workspace SSOT: "all GCS data is in asia-northeast1;
      zone default asia-northeast1-c"). B1's Image-column fix is SCOPED (a dedicated `CLOUD_BUILD_REGION` constant, zero
      blast radius) so it didn't touch this — but `gcs_region`/`effective_region` defaulting to `us-central1`
      (`deployment_api_config.py:589` `self.gcs_region or "us-central1"`) is wrong for this workspace and could
      mislocate VM-launch zones / GCS region / cross-region-egress checks. Operator decision needed: fix the
      `effective_region` default + prod config to `asia-northeast1` (blast radius: VM zones, GCS) vs leave compute in
      us-central1 deliberately. Repo: deployment-api. **Surfaced to operator 2026-06-11.**
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-ui@f4a6d45 (on branch `feat/monitoring-slot26`, pending combined
      PR) | pw:L2 ✓ (full smoke 188/188 green) | regression: src/components/ServiceDetails.test.tsx +
      tests/smoke/stateful-flows.spec.ts. **(test-robustness) `DependenciesPanel` white-screen crash — FIXED.** Root
      cause was systemic: multiple service-detail tabs read `.length`/`.map` on partial/raced API payloads → root
      ErrorBoundary → whole-app white-screen → sibling tabs (Status) unreachable. Two-part durable fix: (1)
      `ServiceDetails.tsx` — `DependenciesPanel`/`DependencyDag` guard every array read (`?? []`), with a
      `ServiceDetails.test.tsx` partial-payload regression (3 cases); (2) `App.tsx` — a per-tab
      `<ErrorBoundary     key={activeTab}>` around the TabsContent region so ANY tab's render crash is contained (tab
      strip survives + recovers on switch) instead of nuking the app. Full smoke went 187/1 (flaky) → **188/188 green**.
      NOTE: this smoke suite does NOT run in deployment-ui CI (neither `quality-gates-v2` nor `ui-quality-gates-v2` runs
      `tests/smoke/`) — so it never blocked promotion; this fixes a real app-robustness bug + the flaky local test.
      **Leftover (slot 4): `tests/e2e/_diag_flow2.spec.ts` (inert `test.skip`) needs `rm` — sandbox-denied.** Repo:
      deployment-ui.
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-ui@1ad86d5 | pw:L2 ✓ | regression:
      tests/e2e/repos-promotion-blocked.spec.ts (B2 header test). **(B2) Repo drill-down build header** — opening a repo
      now renders a build-details header at the top: build **status** + **source** (Cloud Build/CodeBuild, derived from
      the log-URL host via `buildSourceLabel`) + **last build time** + **built commit sha** (→GitHub commit) + **build
      log link**. Shares the B1 image signal; honest-absent ("no Cloud Build / CodeBuild for this repo") when the repo
      has no build. UI-only — the detail endpoint already returned `image` (now populated by the B1 fix). Repo:
      deployment-ui (`RepoDetailPanel` build header + `buildSourceLabel` helper).
- [x] ✅ [CODE] [UI] P2. DONE 2026-06-11 — deployment-api@98d0d40 + deployment-ui@1ad86d5 | pw:L2 ✓ | regression:
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
      `{overallScore, isBlocked, score,     label, detail}` shape (omitting `blocking_items`), so
      `checklist.blocking_items.length` read undefined and crashed — same class as item 203's DependenciesPanel fix (the
      stateful-flows `page.route` fix is dead under `VITE_MOCK_API`, where the in-app mock wins). Two-part: (1)
      ReadinessTab guards `blocking_items`/`categories` with `?? []`; (2) `MOCK_CHECKLIST` rewritten to the
      `ChecklistResponse` contract (readiness_percent + counts + per-category display_name/percent +
      `blocking_items[]`). Repo: deployment-ui (ReadinessTab + mock-api).
- [ ] [CODE] P2. **(Ikenna issue — ADOPTED) Promotion-drain surface** — distinct from the breaking-cascade/SIT panel:
      per repo, last `ldr-to-staging-promote` + `ldr-to-main-promote` run outcome + age + standing-PR v2 conclusion;
      relabel the cascade panel "Breaking cascade / SIT" so the two are never conflated; P3 stall-surfacing when LDR
      content is ahead of staging/main but the drain is stale/failing (bug #11 class). Full spec + 3 sub-todos:
      `plans/active/issues/dashboard_promotion_drain_visibility_2026_06_11.md`. Repos: deployment-api + deployment-ui.
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
- [ ] [CODE] P2. **(G2) Semver-agent health has no standing state** — the bump-rate circuit-breaker (≥3 pending bumps/hr
      or consecutive-at-tip) + version-bump dispatch-failure are CRITICAL pages with no UI element AND they bypass the
      alert ledger (the inline-curl tail already filed in `ci_dashboard_deployment_ui` P3). Add a semver-agent health
      chip/panel (last bump, pending-bump count, breaker armed?) sourced from the manifest version-surface + the GitHub
      runs API for `semver-agent.yml`. Composes with the ledger-persist tail. Repos: deployment-api + deployment-ui.
- [ ] [CODE] P2. **(G3) Manifest consolidator health (`CONSOLIDATOR_DOWN`) is homeless** — the consolidator watchdog
      pages CRITICAL on a stale/missing `_index` while per-VM shards exist, but there is NO standing element on EITHER
      monitoring surface. Decide the home (it is data-pipeline, not CI/CD or fleet-git — candidates: a small
      consolidator-liveness chip on `/repos` header, or the data-status surface) + surface `assert_consolidator_healthy`
      state (last `_index` write age, per-VM shard count). Operator surface-decision needed. Repos: deployment-api +
      deployment-ui (or data-status owner).
- [ ] [CODE] P3. **(G4) Ruleset / branch-protection drift has no standing state** — `rules-alignment-agent` pages
      WARNING on per-repo ruleset misalignment; no UI. Fold into the planned **Rollout-ratchet panels** smart-extra
      (workflow-template drift + Dockerfile digest-pin) as a third ratchet column. Repos: deployment-api +
      deployment-ui.
- [ ] [CODE] P3. **(G5) Change-freeze window active has no standing banner** — `change-freeze-check` pages WARNING when
      a freeze blocks a scheduled/autonomous run; add a freeze-window banner on `/repos` (active? window? reason?).
      Repo: deployment-ui.
- [ ] [CODE] P3. **(G6) Promotion-lag AGE not explicit** — the overview shows the LDR↔staging↔main content-delta but
      not the **time-in-state** the lag monitor pages on (>60 min forward/backmerge lag). Add a lag-age chip (oldest
      unpromoted green commit age) so the page state matches what `promotion-lag-monitor` alerts on. Repo:
      deployment-api (compute age) + deployment-ui.
- [ ] [CODE] P3. **(G7) Worker-liveness watchdog activity has no dedicated standing panel** — slot
      working/paused/blocked states render, but the watchdog's kill / daily-cap-dormancy / autospawn-flap /
      respawn-escalation events are transition-only. Add a watchdog-health panel (kills today vs cap, dormant?, recent
      flap) to the orchestrator dashboard. Repo: agent-orchestrator.
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

### Orchestrator e2e control-plane validation + main-agent first-responder (2026-06-11, Harsh slot-5, local)

Charter line exercised: "Orchestrator side — make the agents **stable** and **picking up** work." Full local e2e run of
the orchestrator control plane from the slot-5 checkout (backend + dashboard on :8765/:5173, sandboxed state in
`.orch-e2e-sandbox/` — fake `ORCHESTRATOR_VM_ID=vm-local-e2e` + `ORCHESTRATOR_PM_REPO_PATH` sandbox PM clone, zero fleet
writes). **VALIDATED live end-to-end**: plan → PlanRegenLoop (assigned_vm-filtered) → backlog → manual spawn → /boot
dispatch → worker executed a real MTDS function-length audit (196 violations / 3,211 functions scanned, report artifact)
→ /done → same-second next-task dispatch → worker /blocked (A/B scoping question) → **main agent auto-answered it in 31
s with plan-grounded reasoning** → worker resumed on the queued answer → applied option B → final /done. Both tasks
`done` in state.db with sentinel SHAs.

- [x] ✅ [CODE] P1. DONE 2026-06-11 — agent-orchestrator@05be1e0 (keeper + lifespan wiring + 7 unit tests; suite 499
      passed) + agent-orchestrator@6b63a77 (main.md boot-template STEP 2.5 blocked-queue sweep: poll
      `/api/state.blocked[]` every tick; answer when plan/SSOT/worker-recommendation suffices via
      `POST /api/blocked/<id>/answer` from_role=main; defer ONLY genuinely operator-level calls — spend, creds,
      destructive, scope — and surface once in chat). **MainAgentKeeper — the main agent (fleet supervisor + /blocked
      FIRST responder per agents/main.md) is now auto-spawned at backend start + kept alive** (singleton tmux
      `orch-agent-main`, 60 s tick, autospawn-shared headroom gate, 5-min cooldown, 3/h flap guard → 1 h backoff,
      `ORCHESTRATOR_MAIN_AGENT_ENABLED` default ON). Previously NOTHING spawned it — the blocked-answer contract
      silently depended on an operator hand-pasting main.md (repro: a worker /blocked sat unanswered on a fresh
      backend). Live-verified: keeper spawn → register → `blocked_answered` (BLK-60790ca7) in 31 s. Repo:
      agent-orchestrator.

Unsolved findings from the run (each repro'd live or read in code; fix not yet shipped):

- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). Route now mirrors PlanRegenLoop env
      resolution (ORCHESTRATOR_VM_ID + REGEN_PRUNE_STALE + REGEN_DB_PATH). Was: **Manual `POST /api/backlog/regen`
      bypasses the `assigned_vm` filter + prune** — `routes/backlog.py:126` calls `regen()` with no args; `regen()`
      defaults `vm_id=None` = ingest-all (its docstring claims an `ORCHESTRATOR_VM_ID` env fallback that is NOT
      implemented — only `PlanRegenLoop.__init__` reads the env). Live repro: manual regen ingested 493 tasks from 53
      fleet plans into a vm-local-e2e backend; the next 120 s loop tick pruned all 491 foreign tasks (self-heal works,
      ≤30 min on fleet), but in that window AutoSpawn can dispatch foreign-VM tasks. Fix: route (or `regen()` itself,
      honouring its docstring) passes `vm_id=ORCHESTRATOR_VM_ID` + `ORCHESTRATOR_REGEN_PRUNE_STALE`. Repo:
      agent-orchestrator (`server/routes/backlog.py` + `server/regen_backlog_from_plan.py`). Found 2026-06-11.
- [x] ✅ [INFRA] P1. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). STEP 5.9 (install_pm_pull.sh → LDR) is now
      the ONLY installer; STEP 7.5c became a loud verifier; duplicate scripts/pm-pull.{service,timer} (origin-main
      pullers) DELETED. Was: **`bootstrap_vm.sh` installs pm-pull TWICE with DIFFERENT branches** — Step 5.9 runs PM's
      `install_pm_pull.sh` (merges `origin/live-defi-rollout`); Step 7.5c installs AO's own `scripts/pm-pull.service`
      (`git pull --ff-only origin main`) under the SAME systemd unit name. Whichever lands first wins (7.5c skips if 5.9
      enabled the timer; if 5.9 WARN-fails — PM clone absent — the main-puller installs into an LDR checkout where
      `--ff-only origin main` near-always fails → **plans silently freeze** with only a journald WARN). Which branch a
      VM's plan source tracks is nondeterministic per bootstrap path. Collapse to ONE installer + ONE branch (LDR per
      the regen/plan-freshness contract). Repo: agent-orchestrator (`scripts/bootstrap_vm.sh` +
      `scripts/pm-pull.service`). Found 2026-06-11.
- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). resolve_dirty_state() wired into the
      autospawn pre-spawn gate (same liveness-gated semantics as the kicker; protected_live_peer/quarantined refuse the
      spawn). Was: **AutoSpawn respawn path skips the FM2/FM3/FM8 dirty-state gate** — `autospawn.py:289-298` runs only
      `check_slot_branch_state` (FM5/FM7); manual `/spawn` (slots_ops.py:204), account rotation (server.py:416), and the
      kicker auto-respawn (worker_liveness.py:929) all call `resolve_dirty_state()`, but the dominant fleet path —
      **watchdog kill → AutoSpawn respawn — boots the new worker into the dead predecessor's dirty tree**, and the \*/5
      FF-cron then `[skip:dirty]`s the slot → stale clone. Also compose: a permanently-dead slot's dispatched task is
      recovered only by same-slot /boot resume (`already_in_progress`); there is no requeue-to-pool on slot death. Wire
      `resolve_dirty_state()` into the autospawn pre-spawn gate. Repo: agent-orchestrator (`server/autospawn.py`).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). verify_done now sets on_origin (git branch
      -r --contains, local remote-tracking refs — no network); /done emits sha_not_on_origin warning;
      ORCHESTRATOR_DONE_REQUIRE_ORIGIN=true hard-409s (warn-first ratchet). Was: **`/done` verifies the SHA locally only
      — no origin-push guarantee** — `verify.py` runs `git show` in the slot worktree (never `ls-remote`/merge-base vs
      `origin/live-defi-rollout`); sentinel SHAs (`audit-*`, `no-code-change`…) skip verification entirely;
      dirty-tree/plan-flip/scope checks are warnings, not blocks. A worker whose quickmerge silently failed
      (auth/network) still marks the task done with a local-only commit. Add an origin-existence check (warn → block
      ratchet). Repo: agent-orchestrator (`server/verify.py` + `server/routes/slots_worker.py`).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). tmux_spawn forwards the backend's
      WORKSPACE_ROOT into the spawn shell (exported before the account env file so it stays overridable). Was: **Spawned
      workers get no `WORKSPACE_ROOT`** — boot prompts carry `${WORKSPACE_ROOT}/...` paths but
      `tmux_spawn._start_session` sources only the account env file; the worker's shell expands it EMPTY (live repro:
      worker `cd`'d to a wrong guessed path, self-recovered after 2 probe commands). Export `WORKSPACE_ROOT` (+ any
      boot-prompt-referenced env) in the spawn `bash_cmd`. Repo: agent-orchestrator (`server/tmux_spawn.py`).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). GET /api/blocked/stats (unanswered + oldest
      age, answered_by split, median/p90 time-to-answer, repeat offenders) + BlockedPanel chip (N/M by main · median
      TTA) computed client-side. Was: **Blocked-queue telemetry missing** — `slot_blocked`/`blocked_answered` land in
      `activity_log` but nothing aggregates: no blocks-per-task counter, no repeated-block alert, no time-to-answer
      metric (now doubly relevant as the MainAgentKeeper SLA measure: main-answered vs operator-answered vs
      unanswered-age). Small rollup endpoint + dashboard chip. Repo: agent-orchestrator.
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). Watchdog Trigger-4: same task >4h + (ctx
      ≥80% OR ≥3 compactions) → context_burn_suspected activity + Slack page, deduped per (slot,task); kill opt-in via
      ORCHESTRATOR_CONTEXT_BURN_KILL (flag-first until fleet mileage). Was: **Execution-vs-context-burn detector
      missing** — nothing correlates time-on-task + context_pct / compactions with pushed output; a worker can heartbeat
      for hours with zero commits and no flag. Rule sketch:
      `dispatched > 4 h AND no done_sha AND (context_pressure high OR compactions climbing) → flag + respawn`. All
      inputs already in state.db (`slots.context_used_pct`, `compactions`, `tasks.dispatched_at`). Repo:
      agent-orchestrator (`server/worker_liveness_watchdog.py` or sibling check).
- [x] ✅ [CODE] P3. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). Dev default flipped to :8765
      (VITE_BACKEND_PORT still overrides). Was: **Orchestrator dashboard dev default still points at retired :8026** —
      `dashboard/src/App.tsx:73` (`devPort ?? "8026"`; backend binds 8765 since the port migration) → fresh local run =
      login "Failed to fetch" until `VITE_BACKEND_PORT=8765`. Flip the default. Repo: agent-orchestrator
      (`dashboard/src/App.tsx`).

- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@1c9b8c1 (4 tests; QG green; quickmerge --agent). **VM-test
      isolation: `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` strict per-VM plan scoping** (operator ask 2026-06-12 — "the test
      VM must not pick up any existing plan by default"). With the flag set, regen ingests ONLY plans whose
      `assigned_vm` EXACTLY matches `ORCHESTRATOR_VM_ID` — the "no assigned_vm ⇒ global, every VM takes it" fallback is
      disabled (a fresh vm-id alone still leaked the global plans, incl. `task_template.md`'s example todos), and with
      no vm_id configured strict mode ingests NOTHING (fail-closed). Env-resolved inside `regen()` so the PlanRegenLoop,
      the manual `POST /api/backlog/regen`, and the CLI all inherit it. The e2e test VM runs
      `ORCHESTRATOR_VM_ID=vm-e2e-test`
  - this flag → guaranteed-empty backlog until a plan explicitly targets it. Repo: agent-orchestrator.

Sandbox-only caveat (NOT a fleet bug — do not chase): repeated worker-session deaths during the local run were caused by
sharing the laptop's `~/.claude/.credentials.json` across concurrent claude sessions (refresh-token rotation conflict)
because no setup-token exists on this host — exactly the failure mode CLAUDE.md § "accounts auth via setup-tokens only"
bans. Fleet VMs (setup-token env files) are unaffected.

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

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Where tracked                                        | State                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------- |
| deployment-api/deployment-ui/e2e content → `main` (all v2 GREEN + draining). **deployment-api staging v2 was RED — ROOT-CAUSED + FIXED 2026-06-10**: the `grep -P` parity bug (base-service.sh deep-import check false-passed on macOS BSD grep → local 23 / CI 24); fixed `grep -P`→`rg --pcre2` (PM@7427ade8a) + budget 23→24 (deployment-api@3a579f1b) → staging v2 now GREEN (run 27309108373). NOT the file-size debt (that's a single in-budget V+1). | this plan + ci_local_qg_parity_2026_06_08.md         | ✅ UNBLOCKED (v2 green; draining)                  |
| Squash-body `[skip ci]` sanitization in Tier C promote                                                                                                                                                                                                                                                                                                                                                                                                      | cicd_contract_hardening § bug #7                     | ✅ DONE (live on PM main)                          |
| Failure-injection verification matrix (mock+pw + live obs; disruptive-live triggers scoped)                                                                                                                                                                                                                                                                                                                                                                 | this plan § matrix (outcomes table)                  | ✅ DONE (table filled)                             |
| Fleet git-health page (sub-plan B — backend + dashboard + reporter + deployment-ui /fleet tab)                                                                                                                                                                                                                                                                                                                                                              | fleet_git_health_orchestrator_2026_06_10.md          | ✅ SHIPPED (live cross-host verify gated on token) |
| GH_PAT `Checks: read` permission (ungrantable on fine-grained PATs)                                                                                                                                                                                                                                                                                                                                                                                         | RESOLVED via Actions-API repoint (Ikenna 2026-06-11) | ✅ NO LONGER BLOCKED                               |
| `ORCHESTRATOR_API_TOKEN` for the fleet-git-health proxy (live fleet data)                                                                                                                                                                                                                                                                                                                                                                                   | ci_dashboard + ikenna_orchestrator/pings/slot_3.md   | BLOCKED-CREDENTIALS                                |
| AWS/CodeBuild cloud-toggle parity for image signal                                                                                                                                                                                                                                                                                                                                                                                                          | ci_dashboard plan                                    | `- [ ]` P1                                         |
| `restart-deployment-stack.sh` must export GCP_PROJECT_ID (live 500 root cause on stack)                                                                                                                                                                                                                                                                                                                                                                     | quality_gates_speed_and_config_ssot (filed below)    | `- [ ]` P2                                         |
| sit-repo full-workspace-sit report-back is LDR-only (inert until its main promotion)                                                                                                                                                                                                                                                                                                                                                                        | cicd_contract_hardening conflict notes               | `- [ ]` P2                                         |

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

- **2026-06-11 (Harsh slot-5, local)** — orchestrator e2e control-plane VALIDATED live (sandboxed local backend+UI from
  the slot-5 checkout): plan→regen→dispatch→execute→done→blocked→**main-agent auto-answer (31 s)**→resume→done. SHIPPED
  agent-orchestrator@05be1e0+6b63a77+a658519: **MainAgentKeeper** (main agent auto-spawned at backend start — closes the
  "nobody answers /blocked on a fresh VM" gap) + main.md STEP 2.5 blocked-sweep duty + lock refresh. 7 new findings
  filed as todos in § "Orchestrator e2e control-plane validation" above (P1: manual-regen vm_id bypass · pm-pull
  dual-installer branch conflict · autospawn missing dirty-gate; P2: /done no-origin-verify · WORKSPACE_ROOT missing in
  spawns · blocked telemetry · context-burn detector; P3: dashboard :8026 default).
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
