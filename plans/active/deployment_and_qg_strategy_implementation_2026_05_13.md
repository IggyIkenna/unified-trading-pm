---
title: Deployment + QG strategy implementation — env-locking, act pre-flight, retention, 99%-repo pipeline
type: plan
status: active
created: 2026-05-13
deadline: 2026-05-23
priority: P0
parent_epic: cross_cutting_may_23_2026.epic.md
spawned_from: codex/05-infrastructure/deployment-and-qg-strategy.md (codified 2026-05-13 from Ikenna + Harsh design discussion 17:05-17:18 UTC)
related_plans:
  - plans/active/promote_workflow_may23_cli_path_2026_05_10.md
  - plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md
  - plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md
  - plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md
related_codex:
  - codex/05-infrastructure/deployment-and-qg-strategy.md
  - codex/05-infrastructure/vm-tarball-deployment.md
  - codex/05-infrastructure/launcher-script-ssot.md
  - codex/08-workflows/cutover-window-dependency-order.md
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
estimate_calibration_note: |
  Infra class — mix of scripting (audit scripts) + service wiring (deployment-api env-locking) + UI guards
  (deployment-ui toggle) + ratchet (QG STEPs). 7 distinct work units below averaging ~1.5 baseline-days each.
  Baseline 12 × 0.8 (infra multiplier) = 9.6 calibrated.
---

# Deployment + QG strategy implementation

> **Spawned from** [`codex/05-infrastructure/deployment-and-qg-strategy.md`](../../codex/05-infrastructure/deployment-and-qg-strategy.md) codified 2026-05-13. That doc is the architectural SSOT; this plan is the work to ship it.

## Why this plan exists

Operator + Ikenna + Harsh discussion 2026-05-13 17:05-17:18 UTC agreed on a deployment + QG strategy combining (a) image-only for staging/prod (immutability + rollback), (b) tarball as dev escape valve with QG-enforcement layering, (c) `act + docker` pre-flight to catch QG failures before slow image push, (d) 99%-repo pipelining so non-blocker repos go on image-build path while laggards catch up.

This plan ships the 7 work-units that operationalize that strategy by 2026-05-23.

## Pre-audit — current state (per QG sweep 2026-05-13)

- All repos pulled from `live-defi-rollout` for clean baseline (in flight per parallel sub-agent sweep).
- 99%-repo criterion: 5+ days QG green + zero P0 issues + no in-flight refactor banner. Identification + tracking surface NOT yet shipped.
- `act` not currently part of any workflow. Workflow files exist at `.github/workflows/quality-gates.yml` per repo but vary in completeness.
- Env-locking guards on deployment-api + deployment-ui: NOT shipped. Tarball is currently selectable for any env via UI/CLI.
- Image base-pin audit script + Artifact Registry retention policy + tarball SHA manifest discipline: NOT shipped.

## Phased execution

### Phase 1 — Env-locking enforcement on deployment-api + UI (2 cal-AI-days)

- [ ] [AGENT] P0. **`deployment-api/.../deploy_endpoint.py`** — add env-aware validation: reject tarball method for `staging`/`prod` with HTTP 400 + explicit error referencing this codex SSOT. Allow `--override-tarball-block` flag for emergency hotfix path but require audit log entry. Unit tests: dev allows both, staging+prod reject tarball without override, override succeeds with audit row.
- [ ] [AGENT] P0. **`deployment-ui/.../DeploymentForm.tsx`** — env-aware UI guard: greys out tarball toggle for staging/prod; selecting it shows tooltip "Tarball blocked in {env} — use image build via Promote Workflow". Operator override = explicit checkbox + reason text. Playwright e2e covers all 6 env × method cells.
- [ ] [AGENT] P0. **Audit log wire-in** — every tarball-deploy attempt (success, reject, override) writes a `DeploymentEvent` row via UTL `RequestAuditMiddleware` per CLAUDE.md audit-records discipline.

**Owner**: deployment-api + deployment-ui slots (parallel; both reads from same env config).
**Dependencies**: None — UAC schemas already shipped.

### Phase 2 — `act + docker` pre-flight workflow (2 cal-AI-days)

- [ ] [AGENT] P0. **Author `unified-trading-pm/scripts/dev/act-preflight.sh`** — wraps `act` invocation against the repo's `.github/workflows/quality-gates.yml` in a pinned `act-runner-image`. Accepts `--repo <name>` arg; resolves repo path; runs `act -j quality-gates --container-architecture linux/amd64`. Captures EXIT_CODE + summary; writes report to `/tmp/act-preflight-{repo}-{sha}.log`.
- [ ] [AGENT] P0. **Per-workflow coverage test** — run `act-preflight.sh` against each repo's QG workflow. Document per-repo coverage matrix: which workflows act fully covers, which need OIDC/WIF tweaks, which need secret-injection workarounds. Output: `codex/05-infrastructure/act-preflight-coverage.md` (NEW).
- [ ] [AGENT] P1. **Optional pre-push git hook** (`.git/hooks/pre-push.sample`) — opt-in via `scripts/dev/install-act-precommit.sh`. Refuses push if act-preflight fails. Documented as opt-in, not mandatory.

**Owner**: deployment-service slot (one slot owns this end-to-end).
**Dependencies**: None — but Phase 2's value is highest on the 99%-repos identified in Phase 4.

### Phase 3 — Tarball SHA pinning + manifest discipline (1 cal-AI-day)

- [ ] [AGENT] P0. **Update `deployment-service/scripts/vm/create-code-tarballs.sh`** — name tarballs `<repo>@<commit-sha>.tar.gz`; write sibling `<repo>@<commit-sha>.manifest.json` containing `{repo, commit_sha, pyproject_version, git_status_clean, created_at, created_by}`. Refuses to upload if `git status` is dirty (override flag `--allow-dirty-tarball` with audit log).
- [ ] [AGENT] P0. **Update VM launcher scripts** at `deployment-service/scripts/vm/` — at boot, read manifest.json sibling of the tarball; assert `commit_sha` matches expected; fail loud on drift via UAC `ManifestShaDriftError` (NEW in `unified_api_contracts.canonical.crosscutting.deployment.errors`).
- [ ] [AGENT] P0. **Async image-build trigger** — tarball write fires `cloud-build` on same commit-sha. Wired in `create-code-tarballs.sh` POST upload step. So when promoting dev→staging, image already exists.

**Owner**: deployment-service slot.
**Dependencies**: UAC schema additions need shipping (`ManifestShaDriftError`) — root-dep slot.

### Phase 4 — 99%-repo identification + tracking surface (1.5 cal-AI-days)

- [ ] [AGENT] P0. **Author `unified-trading-pm/scripts/quality_gates/snapshot.sh`** — walks all repos in workspace; runs `bash scripts/quality-gates.sh --quick` (skips slow integration tests); writes `quality_gates_snapshot_YYYY_MM_DD.parquet` to GCS path `gs://${PROJECT_ID}-deployment-events/quality_gates_snapshot/`. Schema: `repo, pull_sha, qg_status, failing_step, first_error_line, duration_seconds, snapshot_at`. Cron VM daily via existing `deployment-service/scripts/vm/launch-...` pattern.
- [ ] [AGENT] P0. **99%-repo criterion logic** — service-side (deployment-api new endpoint `/api/repos/deploy-ready`): walks last 5 daily snapshots per repo; returns `deploy_ready: true` if all 5 are green + zero P0 issue docs + no `🟡 IN-FLIGHT REFACTOR` banner on the repo's owning plan.
- [ ] [AGENT] P0. **Tracking surface in deployment-ui** — new `DeploymentReadinessTab.tsx` shows per-repo: pull SHA / QG green-streak days / blocking issues / promote-eligible badge. Extends `deployment_ui_lifecycle_tabs_2026_05_08.md`.

**Owner**: deployment-api + deployment-ui slots (parallel after Phase 1 lands).
**Dependencies**: Phase 1 env-locking shipped (uses same UI patterns); UAC `DeploymentReadiness` schema.

### Phase 5 — Image base-pin audit + retention policy (1 cal-AI-day)

- [ ] [AGENT] P0. **Author `deployment-service/scripts/audit/dockerfile-base-pin.sh`** — walks all `Dockerfile`s in workspace; flags any using `:tag` instead of `@sha256:digest` for production-bound services (skip dev-only utilities). Output: per-Dockerfile remediation list. Add to QG STEP as a P1 (warn) ratchet; flip to P0 (error) at 2026-05-15 freeze gate.
- [ ] [AGENT] P0. **Pin all production Dockerfile base images to digest** — apply remediation list. Per-repo PRs; serialize through root-dep slot.
- [ ] [AGENT] P0. **Artifact Registry retention policy** — `deployment-service/scripts/audit/artifact-registry-retention.sh` (NEW): configures GCP Artifact Registry cleanup policies. Keep-forever: release tags. Keep-14d: commit-SHA images. Keep-3d: branch-feature images. Delete-on-PR-close: PR-specific images. Run as Cloud Scheduler weekly cron.

**Owner**: deployment-service + governance slots.
**Dependencies**: None.

### Phase 6 — QG ratchet for deployment discipline (1.5 cal-AI-days)

> **PULLED-FORWARD COMPANION** with `governance_qg_automation_gaps_post_cutover_2026_05_12.md` (deadline pulled to 2026-05-23 per operator direction 2026-05-13).

- [ ] [AGENT] P0. **New QG STEPs** in `unified-trading-pm/scripts/quality_gates/`:
  - **STEP X.N1**: `dockerfile-base-pin` — fail if production-bound Dockerfile uses `:tag` not `@sha256:digest`. Ratchet starting 2026-05-15.
  - **STEP X.N2**: `tarball-manifest-present` — fail if tarball upload missing sibling manifest.json. Ratchet starting 2026-05-15.
  - **STEP X.N3**: `tarball-env-block` — fail if deployment-api code allows tarball for staging/prod without explicit override. Ratchet starting 2026-05-17.
  - **STEP X.N4**: `image-build-on-staging-merge` — fail if staging-branch merge doesn't trigger cloud-build. Ratchet starting 2026-05-17.
- [ ] [AGENT] P0. **Wire ratchets via `quality_gates/base-service.sh` registration** — per CLAUDE.md QG ratchet pattern.

**Owner**: governance slot (single owner — these touch the QG script registry).
**Dependencies**: Phase 1 + Phase 3 + Phase 5 shipped.

### Phase 7 — Coverage raise across leaf services (mechanical parallel sub-agents, 0.5 cal-AI-day)

- [ ] [AGENT] P1. **Coverage-raise spawn prompt template** at `unified-trading-pm/cursor-configs/coverage-raise-spawn.md` — paste-ready prompt for spawning per-leaf-service sub-agents. Each sub-agent: identifies coverage gaps via `pytest --cov`, writes snapshot tests + per-branch unit tests, raises coverage by ≥5% per service.
- [ ] [AGENT] P1. **Per-tab worktrees discipline** — coverage spawn prompts MUST cite per-tab-worktree setup (CLAUDE.md `setup-tab-worktrees.sh` infra) to avoid index contention when multiple agents touch same root deps (PM / UAC / deployment-service).

**Owner**: slot 1 main spawns + monitors; leaf-service slots execute.
**Dependencies**: None — independent of deployment work.

## Done definition

**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion"):

- ✅ Tarball deploy attempt to `staging` from CLI returns HTTP 400 with explicit error message (Phase 1 wire-in).
- ✅ UI shows tarball toggle greyed out in `staging`/`prod` env selectors (Phase 1).
- ✅ `act-preflight.sh quality_gates_workflow` runs successfully on ≥75% of repos; coverage matrix doc shipped (Phase 2).
- ✅ Tarball uploaded to GCS has sibling `<repo>@<sha>.manifest.json`; VM launcher asserts SHA on boot (Phase 3).
- ✅ Daily `quality_gates_snapshot_*.parquet` written to GCS by cron VM; `/api/repos/deploy-ready` endpoint returns valid list of 99%-repos (Phase 4).
- ✅ All production-bound Dockerfiles pinned to `@sha256:digest`; Artifact Registry retention policy active (Phase 5).
- ✅ 4 new QG STEPs registered in base-service.sh + enforced on PRs (Phase 6).
- ✅ Per-service coverage ≥5% increase across leaf services (Phase 7).

**Handoff exception**: none — this plan owns the full deployment-and-QG strategy ship.

## Slot allocation suggestion (for Ikenna slot 1 main)

7 phases × ~1-2 cal-AI-days each = ~9.6 cal-AI-days (calibrated). At measured workspace throughput ~200/day, fits in 0.5-1 calendar day of focused slot effort. Recommend distribution:

- **Phase 1 + 4** (env-locking + 99%-repo tracking) → deployment-api + deployment-ui paired slot (2 sub-agents in one slot; same env config, same UI patterns)
- **Phase 2** (act pre-flight) → deployment-service slot (single sub-agent; workflow-level)
- **Phase 3** (tarball SHA pinning) → deployment-service slot (can be same as Phase 2 if sequential; ~1 cal-day)
- **Phase 5** (image base-pin + retention) → governance slot
- **Phase 6** (QG ratchet) → governance slot (after Phases 1/3/5)
- **Phase 7** (coverage raise) → slot 1 main dispatches; ~10 leaf-service spawn calls

**Total**: ~4 distinct slots × ~0.5-1 day each = fits the cutover-window parallel-track capacity.

## Cross-plan handshakes

- **`promote_workflow_may23_cli_path_2026_05_10`** — wires the env-locking enforcement at the deployment-api layer; Phase 1 of this plan adds the validation logic.
- **`promote_workflow_post_cutover_ui_pipeline_2026_05_10`** — full UI pipeline build extends Phase 4 tracking surface.
- **`governance_qg_automation_gaps_post_cutover_2026_05_12`** — Phase 6 ratchets compose with that plan's governance HARD RULE automation.
- **`deployment_ui_lifecycle_tabs_2026_05_08`** — Phase 4 `DeploymentReadinessTab` is a new tab in the existing tab structure.
- **`cutover-window-dependency-order.md`** — this plan's deliverables land Day 1-6 of the cutover-window timeline.

## Risk + mitigation

| Risk | Mitigation |
|---|---|
| `act` doesn't cover OIDC/WIF for deploy-auth workflows in some repos | Phase 2 coverage matrix doc identifies per-repo coverage; treat as 80% pre-flight, not certainty |
| 99%-repo criterion blocks too many repos (none qualify) | Adjust criterion to "3+ days QG green" if needed by 2026-05-15; criterion is a tuning lever |
| Image build cost balloons | Phase 5 retention policy caps storage; ~$70/month worst-case is acceptable for live trading capital protection |
| Coverage raise introduces flaky tests | Phase 7 spawn template explicitly requires deterministic tests; reject any test using `time.time()`, real network, real disk fixtures |
| Tarball manifest discipline breaks existing VM workflows | Phase 3 wires fallback: if manifest missing, log WARN + continue (post-cutover ratchets to ERROR via Phase 6 STEP X.N2) |
