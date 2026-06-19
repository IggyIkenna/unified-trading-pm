---
title: "Monitoring Surfaces Overhaul — agent-orchestrator dashboard + deployment-ui pane"
created: 2026-06-18
status: active
parent_epic: infrastructure_master
assigned_vm: planning
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
audit_ref: plans/audit/results/monitoring_surfaces_audit_2026_06_18.md
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
source:
  - 2026-06-18 operator design session — orchestrator UI = agents/orchestrator lens; deployment-ui =
    CICD/codebase/fleet/images
  - plans/audit/results/monitoring_surfaces_audit_2026_06_18.md (Opus audit, 4 background agents)
priority: P2
---

# Monitoring Surfaces Overhaul

## Why

Operator (2026-06-18): the orchestrator dashboard owns everything about AGENTS + the orchestrator; the deployment-ui
monitoring pane owns CI/CD + codebase + fleet + images; an alert clicks through to the right surface. Two tracks. Full
evidence + per-ask current-state/gap/change-list: `plans/audit/results/monitoring_surfaces_audit_2026_06_18.md`. Audit
reframe: CI/CD + image-build are already mature/planned; the real deployment-ui gaps are fleet-runtime +
alert-unification. The `agent_kind`/`lifecycle` data is already served — it's rendering + retention that's missing.

## Track A — agent-orchestrator dashboard (repo: agent-orchestrator; ALL `[UI]` → playwright/vitest gate, PLAN_FORMAT §9)

- [ ] [ORCHESTRATOR] P0. **Retain finished one-shot/scheduled agents** (load-bearing): stop hard-deleting on completion
      (`DELETE /api/agents/{id}` `routes/agents.py:703`); transition to a terminal status (`finished` +
      `finished_at`/`exit_reason` on AgentRow) + a retention prune (last N per kind / 7d). Without this "show past
      escalate/plan-health runs" is impossible. Repo: agent-orchestrator (server).
- [ ] [ORCHESTRATOR] P1. Filterable `GET /api/agents` — honor the dead-contract `status` param + add `kind`/`lifecycle`/
      `include_finished`/`limit`, pushed into `state_store.list_agents` (WHERE/ORDER BY). Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR][UI] P1. New `AgentTypesPanel` (one new tab, keyed on `agent_kind`, running+past) — `KINDS_ORDER` +
      reuse `RoleHolders`/`AGENT_KIND_LABEL`; per-kind online count + show-finished toggle; mount desktop + mobile. Keep
      role chat (`main/review/backup`) clean. Evidence: `— repo@sha | pw:L2 ✓ | regression: <spec>`. Repo:
      agent-orchestrator (dashboard).
- [ ] [ORCHESTRATOR] P1. Activity feed backend — push `slot`/`type`/category filters into SQL BEFORE the limit
      (`activity.py:86` / `routes/state.py:91-111`), add cursor pagination (`before_id`/offset + envelope), add a
      **denoise rollup** (`GROUP BY event_type[,slot] within window` → "×N in last 1h"; generalize
      `count_recent_activity`). The denoise is the "90% repeats" fix. Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR][UI] P1. Activity feed frontend — "Load older"/cursor append (decouple from the live poll),
      server-driven filter tabs, collapse duplicate rows with ×N badge + expand, smaller live poll (~25). Repo:
      agent-orchestrator (dashboard).
- [ ] [ORCHESTRATOR][UI] P1. Render the per-event FAILURE REASON in the activity feed + escalations surface (moved from
      `orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 7). Today a `escalation_dispatch_failed` row
      shows only the bare event name; the reason IS already persisted (`escalation_queue.last_error` +
      `activity_log.details_json.error`) — it just isn't rendered, so the operator can't see WHY a dispatch failed
      without DB access (incident 2026-06-18: a slot-1 branch-quarantine starved dispatch for hours, invisible in the
      UI). Surface `details_json.error` inline (expandable) on failure-class activity rows, and `last_error` on the
      escalations view. Repo: agent-orchestrator (`server/` read path already has it + `dashboard/`).
- [ ] [ORCHESTRATOR][UI] P2. Conditions tab collapsible (frontend-only): `COLLAPSED_COUNT=5`, sort OFF+`gates_queued>0`
      first, "Show N more ▾"/"Collapse ▴", keep the count chip. Repo: agent-orchestrator (dashboard).
- [ ] [ORCHESTRATOR][UI] P2. Message-delivery VISIBILITY chip (operator decision 2026-06-19: **NO messaging-layer
      rewrite** — no adaptive-cadence / long-poll / SSE; the poll model stays). The only real gap is not knowing whether
      a sent message landed → surface the already-computed `count_pending_to_agent`/`pending_count` as a per-agent
      "queued → delivered" chip in the chat UI (data already served; frontend-only). Repo: agent-orchestrator (dashboard).
      NOTE: the **wake-on-message tmux nudge IS in scope** — but it lives in the unified-AgentKeeper work
      (`orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 6), because the default loops are now long (review
      15 min, main up to 60 min) and the nudge is what makes a long idle loop responsive to a UI message. Live UI
      loop-interval control is the P3 nice-to-have there too.

## Track B — deployment-ui monitoring pane (repos: deployment-ui + deployment-api)

- [ ] [INFRA] P0. **Mint `ORCHESTRATOR_API_TOKEN` into Secret Manager (both clouds)** — cheapest high-value fix: lights
      up the already-built Fleet-Git page (currently degrades to unavailable, BLOCKED-CREDENTIALS). File as an operator
      credential ask if mint requires operator. Repo: deployment-service/deployment-api.
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

### Cloud Build visibility + build health (found 2026-06-18 operator Cloud Build smoke test)

Operator-directed GCP Cloud Build smoke test (central-element-323112 / asia-northeast1): `roles/editor` confirmed; 3
builds run via regional triggers — UTL base `590050dc` ✅ SUCCESS, mtds `4a7de34e` ✅ SUCCESS, mdps `40c74eab` ❌
FAILURE. Two build-VISIBILITY bugs (deployment-ui Cloud Build pane is non-functional today) + one BUILD break, all
root-caused:

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

## Out of scope here (already filed/blocked — coordinate, do NOT reimplement)

- Version-coherence panel, rollout-ratchet panels (template-drift + Dockerfile digest-pin), G4 ruleset-drift, G5
  change-freeze banner — blocked on the Firestore verdict-store (master plan); consolidator-health (G3) IN-PROGRESS
  (slot-3); runtime deploy-signal v2 already filed (master L212).

## Success criteria

- Every agent type (escalate/conflict-resolver/plan-health/plan-reconciler/monitor) is visible in the AO dashboard while
  running AND as past runs; activity feed is filterable + paginated + denoised; conditions collapse.
- An alert of ANY class opens its deployment-ui surface and shows the full picture (fleet-runtime + central-VM
  included).
- Fleet-Git page is LIVE (token minted).

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — AgentTypesPanel + agent-retention + messaging path.
- `codex/04-architecture/runtime-deployment-topology.md` — deployment-ui fleet-runtime + unified-alert-ledger surfaces.
