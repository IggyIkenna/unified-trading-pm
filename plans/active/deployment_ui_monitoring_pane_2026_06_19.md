---
title: "Deployment-UI Monitoring Pane — CI/CD · codebase · fleet · images · alerts"
created: 2026-06-19
status: active
parent_epic: infrastructure_master
assigned_vm: planning
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
audit_ref: plans/audit/results/monitoring_surfaces_audit_2026_06_18.md
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
source:
  - 2026-06-18 operator design session — deployment-ui = CICD/codebase/fleet/images lens
  - 2026-06-19 operator decision — split monitoring_surfaces_overhaul into two single-surface plans (deployment-ui here;
    agent-orchestrator dashboard → agent_orchestrator_dashboard_monitoring_2026_06_19.md)
  - plans/audit/results/monitoring_surfaces_audit_2026_06_18.md (Opus audit, 4 background agents)
priority: P2
---

# Deployment-UI Monitoring Pane

> **Split 2026-06-19** from `monitoring_surfaces_overhaul_2026_06_18.md` (operator: two single-surface plans so the
> deployment-ui side and the agent-orchestrator side can be worked by separate agents without collision). The
> agent-orchestrator dashboard track moved to `agent_orchestrator_dashboard_monitoring_2026_06_19.md`. This plan owns
> the **deployment-ui + deployment-api** surface only.

## Why

Operator (2026-06-18): the deployment-ui monitoring pane owns CI/CD + codebase + fleet + images; an alert clicks through
to the right surface. Audit reframe: CI/CD + image-build are already mature/planned; the real deployment-ui gaps are
fleet-runtime + alert-unification. Full evidence + per-ask current-state/gap/change-list:
`plans/audit/results/monitoring_surfaces_audit_2026_06_18.md`.

## Deployment-UI monitoring pane (repos: deployment-ui + deployment-api)

- [x] ✅ [INFRA] P0. **Mint `ORCHESTRATOR_API_TOKEN` into Secret Manager (both clouds)** — cheapest high-value fix: lights
      up the already-built Fleet-Git page (currently degrades to unavailable, BLOCKED-CREDENTIALS). File as an operator
      credential ask if mint requires operator. Repo: deployment-service/deployment-api.
      **DONE 2026-06-19**: HS256 JWT minted (sub=deployment-api, role=operator, exp=2036-06-16); stored as version 2 in
      GCP SM (`central-element-323112/ORCHESTRATOR_API_TOKEN`) + AWSCURRENT in AWS SM (`ap-northeast-1/427895769566`).
      Token validates against `ORCHESTRATOR_JWT_SECRET` on this host. Fleet-Git page should now degrade→live on next
      deployment-api cold-start / SM read.
- [ ] [INFRA] P1. Central/infra-VM health: `GET /api/fleet/infra-vm-health` (proxy AO `/api/fleet/summary`) +
      `GET /api/fleet/vm-census` (render `vm_zombie_watchdog.py` running-vs-expected-vs-zombie). Repo: deployment-api.
- [ ] [UI] P1. deployment-ui central/infra-VM status tile + VM census/zombie surface (the vm-0 OOM class is invisible
      today) — chip click-throughs to AO (not a rebuild; honors division-of-surfaces). `pw:L2 ✓` + regression. Repo:
      deployment-ui.
- [ ] [INFRA] P1. **Unify the alert ledger across domains** — non-CI watchers (VM-down, consolidator-down,
      git-health-guard, worker-liveness, data-pipeline) write to a shared store; add `GET /api/alerts` superset of
      `/api/repo-ci/alerts`. This is what makes "alert → open deployment-ui → full picture" work for ALL classes. Repo:
      deployment-api (+ the watcher emitters). Composes with `alert_quality_overhaul_2026_06_18.md`.
- [ ] [UI] P1. deployment-ui `/alerts` page consumes the unified ledger (not just `cicd/alerts`). `pw:L2 ✓` +
      regression. Repo: deployment-ui.
- [ ] [UI] P2. Unified single-glance fleet/infra landing tile (6th LandingTab: N VMs running · central-VM up ·
      consolidator fresh · fleet-git clean · CI green — each click-through). Repo: deployment-ui.
- [ ] [UI] P2. Codebase-health matrix column on `/repos` (fleet-wide coverage% / QG-red-reason / file-size-debt, not
      per-service-tab-only). Repo: deployment-ui (+ a deployment-api roll-up if needed).
- [ ] [UI] P2. Confirm `GhRateBudget` is placed as a standing element on `/repos`. Repo: deployment-ui.

## Cloud Build visibility + build health (found 2026-06-18 operator Cloud Build smoke test)

Operator-directed GCP Cloud Build smoke test (central-element-323112 / asia-northeast1): `roles/editor` confirmed; 3
builds run via regional triggers — UTL base `590050dc` ✅ SUCCESS, mtds `4a7de34e` ✅ SUCCESS, mdps `40c74eab` ❌
FAILURE. Two build-VISIBILITY bugs (deployment-ui Cloud Build pane was non-functional) + one BUILD break, all
root-caused and FIXED 2026-06-19:

- [x] ✅ [INFRA] P1. DONE 2026-06-19 — deployment-api@5bf7165c. **deployment-api build history shows nothing (current
      build + history) — regional-vs-global `list_builds`.** `get_build_history` (`routes/cloud_builds.py:387`) queries
      `ListBuildsRequest(project_id=...)` (GLOBAL scope; the inline "regional parent 400s on REST" comment is STALE) but
      every build runs regionally in `asia-northeast1`, so it always returns `builds:[]` (confirmed empty for both mtds
      `-live-defi-rollout` and mdps `-build`). Fix: use the regional parent `projects/{p}/locations/asia-northeast1`,
      mirroring the proven `_find_recent_build_sync` / `_get_recent_builds_for_triggers` helpers (which already use it).
      Secondarily map service → ACTUAL live trigger (`-live-defi-rollout` where present, else `-build`;
      `cloud_builds.py:346`) so LDR-built repos appear. Repo: deployment-api. **Shipped**: extracted
      `_build_history_for_repo` (regional parent + REPO_NAME substitution, trigger-agnostic) into
      `_cloud_builds_history.py`; `get_build_history` delegates; dead single-trigger_id plumbing removed. QG green
      (135s); regression `tests/unit/test_cloud_builds_helpers.py::TestBuildHistoryForRepo` (3 tests).
- [x] ✅ [INFRA] P1. DONE 2026-06-19 — deployment-api@5bf7165c. **deployment-api `/api/cloud-builds/triggers` 500s when
      Redis is down (the triggers pane + last_build is dead).** `list_triggers` wraps its fetch in `cache.get_or_fetch`
      (Redis-backed); `RedisCache.get/set/...` (`utils/cache.py`) catch only `(OSError, ValueError, RuntimeError)`, but
      redis-py raises `redis.exceptions.RedisError` (subclasses `Exception`, NOT `OSError`) on a dropped/unreachable
      connection → it propagates → 500. (History is unaffected because it skips the cache — which is why it's 200-empty,
      not 500.) Fix: make the cache best-effort — add `RedisError` to the caught set so a Redis outage degrades to a
      cache-miss (falls through to live fetch), never a 500. Fleet-wide resilience: this fixes EVERY cached endpoint,
      not just triggers. Repo: deployment-api. **Shipped**: added `RedisError` to the
      `RedisCache.connect/get/set/delete/clear_pattern` except tuples (`utils/cache.py`) — a Redis outage now degrades
      to a cache-miss. Regression `tests/unit/test_unified_cache.py::test_rediscache_get_degrades_on_redis_error`.
- [x] ✅ [DOCKER] P1. DONE 2026-06-19 — market-data-processing-service@8025264d | Cloud Build 3c501b1f SUCCESS (full
      green: image built + in-image QG passed + pushed). **mdps image build was broken — THREE stacked causes, peeled
      back one Cloud Build at a time:** (1) `Dockerfile:57` `uv sync --frozen --no-dev` needed the editable
      `../unified-api-contracts` absent from the GCP context → switched to `uv pip install --system -e . --no-sources`
      (mdps@bffb9df3; mirrors features-service — `--no-sources` keeps external deps numba/polars, unlike mtds's
      `--no-deps`). (2) That exposed a STALE `BASE_IMAGE_DIGEST` pin `e939b4ee` (base UTL 0.11.0 / UAC 0.15.0) vs mdps
      floors UTL ≥0.12.0 / UAC ≥0.19.0 → uv re-resolved from the registry & failed → refreshed to current `:latest`
      `2baa8551` (UTL 0.13.0 / UAC 0.19.0) (mdps@317ab425); build `6798472f` then proved Step #5 (image build) green.
      (3) That exposed Step #6 (in-image QG): `scripts/quality-gates.sh` resolved `WORKSPACE_ROOT` via
      `git rev-parse --show-toplevel` which is empty in-image → sourced `//unified-trading-pm/.../base-service.sh` (404)
      → added the fleet-canonical mtds `CLOUD_BUILD=true` guard (skip in-image gate when the PM base script is absent)
      (mdps@8025264d). Build `3c501b1f` green end-to-end. Repo: market-data-processing-service.
- [ ] [INFRA] P1. **Audit the fleet for STALE `BASE_IMAGE_DIGEST` pins + add a warn-level QG/cron drift check.** mdps's
      pin had drifted to `e939b4ee` (base UTL 0.11.0 / UAC 0.15.0) while its own floors require UTL ≥0.12.0 / UAC
      ≥0.19.0 → the build re-resolved from the registry and failed; the digest-refresh fan-out
      (`update-dependency-version.yml`) evidently never landed for mdps. A stale pin is **silent** until someone runs
      the build (red build, never a warning). Sweep every repo's `Dockerfile` `ARG BASE_IMAGE_DIGEST`, compare against
      the current `unified-trading-library:latest` digest, and flag any whose pinned base ships libs OLDER than that
      repo's `pyproject.toml` floors (the actual break condition — a merely-not-`:latest` pin is fine if it still
      satisfies). Add it as a warn-level signal (PM post-gate or the digest-pin ratchet panel already in "Out of scope")
      so drift surfaces before it becomes a red build. Repos: all service Dockerfiles + PM (the check). Provenance:
      2026-06-19 mdps build fix.

## Repo-CI table clarity + authoritative source (operator review 2026-06-19)

Operator walked the Repo-CI overview table live and surfaced three confusions, all traceable to the table design + a
stale-cache data source (full diagnosis in the 2026-06-19 session): (1) the single `CI status` lifecycle token
conflates promotion-PROGRESS with branch-FAILURE — e.g. `STAGING_GREEN` reads as "stuck" when it means "furthest-green
= staging"; (2) the dep-order HOLD that lags main is INVISIBLE — empty triage queue + empty breaking cascade while
`last green (main)` sits days stale; (3) the UI reads `ci_status` from the committed `workspace-manifest.json` cache,
NOT the authoritative Firestore side-store the promoter gate actually reads, so the dashboard can show a different
status than what gates promotions.

- [ ] [UI] P1. **Drop the `CI status` column; color-code the LDR/staging/main SHA cells per-branch** (green = that
      branch's last `quality-gates-v2` succeeded · red = failed · gray = unknown) from `branch_ci`. The 9-state
      `ci_status` token is noise — per-branch green/red is the simpler at-a-glance model. Needs the backend to populate
      `branch_ci` for ALL repos (today `deployment_api/routes/repo_ci.py` bounds it to the red repos to save GitHub API
      budget) — derive green branches from SHA-equality / `ci_status` where a live fetch is skipped, or widen the fetch.
      Repos: deployment-ui + deployment-api. `pw:L2 ✓` + regression. Provenance: 2026-06-19 operator review.
- [ ] [UI] P1. **Promotion-state surface — make the dep-order HOLD visible.** A repo can sit `STAGING_GREEN` with main
      days behind and NOTHING in the triage queue / breaking cascade, because the staging→main STAGE 1.8 dep-order gate
      is a silent designed HOLD (incident 2026-06-19: fleet blocked behind `unified-api-contracts` not yet
      `MAIN_GREEN`). Add a per-repo surface: "main behind staging by N files · last promoted <when> · blocked-by:
      <dep / lag>", sourced from the deltas already in the overview + the STAGE-1.8 block reason. Repos: deployment-ui +
      deployment-api (expose the dep-order block reason). `pw:L2 ✓` + regression. Provenance: 2026-06-19 operator review.
- [ ] [INFRA] P1. **deployment-ui must read `ci_status` from the AUTHORITATIVE Firestore side-store, not the committed
      `workspace-manifest.json` cache.** `deployment_api/routes/_repo_ci_manifest.py` reads the committed manifest's
      `ci_status` (a CI-written cache, 120s TTL) — but the promoter gate overlays the LIVE `ci_status/{repo}` Firestore
      store, so the dashboard can show a DIFFERENT status than what actually gates promotions. Do the pending Phase-2
      one-function swap (`ManifestView.ci_status_for` → `ci_status_store.resolve_ci_status_map`), adding
      `google-cloud-firestore` to deployment-api. SSOT: `ci_status_firestore_side_store_2026_06_10.md`. Repo:
      deployment-api. Provenance: 2026-06-19 operator review.
- [ ] [PROMOTION] P2. **(track-3 cross-ref — do NOT implement in the UI track)** Forward staging→main promotion lags
      fleet-wide (services ~2 days behind main while libs promote): STAGE 1.8 dep-order tiered-drain + a possible
      `staging_versions` registration gap for `unified-api-contracts`. Diagnosed 2026-06-19; owned by the
      CI-escalation / promotion track (`cicd_promotion_pipeline_2026_06_18.md`) — surfaced here only because it is what
      makes the UI read "stuck". Repo: unified-trading-pm (promotion machinery).

## Out of scope here (already filed/blocked — coordinate, do NOT reimplement)

- Version-coherence panel, rollout-ratchet panels (template-drift + Dockerfile digest-pin), G4 ruleset-drift, G5
  change-freeze banner — blocked on the Firestore verdict-store (master plan); consolidator-health (G3) IN-PROGRESS
  (slot-3); runtime deploy-signal v2 already filed (master L212).

## Success criteria

- An alert of ANY class opens its deployment-ui surface and shows the full picture (fleet-runtime + central-VM
  included).
- Fleet-Git page is LIVE (token minted).
- deployment-ui Cloud Build pane shows the current build + history for every repo (regional + REPO_NAME-keyed); the
  triggers pane survives a Redis outage.

## Codex SSOT updates

- `codex/04-architecture/runtime-deployment-topology.md` — deployment-ui fleet-runtime + unified-alert-ledger surfaces.
