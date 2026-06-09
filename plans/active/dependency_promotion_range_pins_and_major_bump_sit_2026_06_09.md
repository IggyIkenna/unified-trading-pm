---
title: "Dependency promotion — range pins absorb minor/patch, only MAJOR forces rebuild (full SIT in dep order)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
created: 2026-06-09
source:
  - operator design direction 2026-06-09 ("why are we locking to minor versions… ranges >0.0.1<1… only major bumps force uv lock changes… major bumps trigger full SIT in dep order else escalate to vm-planning")
  - plans/active/cicd_contract_hardening_2026_06_01.md § "CORRECTION + ADDENDUM 2026-06-09" (UAC 0.1.20-vs-0.2.1 split that surfaced this)
---

# Dependency promotion — range pins absorb minor/patch; only MAJOR forces a consumer rebuild

## The model (operator, 2026-06-09)

Internal-dep version churn currently cascades fleet-wide: a UAC `0.2.0→0.2.1` bump turns **every** consumer's
committed `uv.lock` stale → `uv lock --check` reds the consumer's QG (incident: MTDS), even though the dep is an
**editable path install** that resolves from source and ignores the locked version. That is pointless CI noise.

**Target dependency-promotion contract:**

- **Declared pins are RANGES** `>=0.x,<1.0.0` (already true fleet-wide — `pyproject.toml` + `workspace-constraints.toml`).
- **minor/patch bumps are backward-compatible BY DESIGN** → absorbed by the range → **NO consumer rebuild, NO CI noise**.
  A consumer picks up the newer dep only when IT next goes through its own promote workflow (and passes QG at that point).
  Downside accepted: a consumer's build can lag the latest dep; upside: prod is stable + intermediate builds don't
  thrash CI. The operator asks for a promote when they want the newer dep — promotion is pull, not push.
- **MAJOR bumps are breaking** → they violate the consumer's `<1.0.0` range → the consumer MUST deliberately update its
  pin → **rebuild is forced**. A major bump **triggers a full SIT in dependency order** to verify every dependent still
  passes QG against the new major; if SIT passes → promote proceeds; if the staging workflow gets **stuck**, **escalate
  to vm-planning** (the orchestrator) to resolve.
- **What counts as MAJOR vs MINOR is decided by the breaking-change matrix** — the AST public-surface differ
  (`scripts/cicd/detect_breaking_change.py`) + a plan-documented schema/API-contract matrix, refined deliberately
  (not a version-phase heuristic). SSOT for "breaking = public-surface change": `codex/08-workflows/ci-cd-flow.md`
  § "Breaking = public-surface change, NOT version phase".

**Clarification (technical):** `uv.lock` cannot hold ranges — it records EXACT resolved versions by design. So the lever
is NOT the lock format; it is (a) the declared range pin (done) + (b) making the `uv lock --check` gate **ignore internal
editable-dep drift** so minor/patch internal bumps never red a consumer. External deps stay exactly pinned (reproducibility).

## What's already in place (verified 2026-06-09)

- ✅ Declared pins are ranges: MTDS `unified-api-contracts>=0.1.0,<1.0.0` + `[tool.uv.sources] path = "../unified-api-contracts"` editable; `workspace-constraints.toml` matches.
- ✅ External dep-alignment check ALREADY exempts internal packages (`check_external_dependency_alignment.py`: "internal packages — never in PyPI — skip them").
- ✅ Breaking-change differ exists (`detect_breaking_change.py`) + SIT/cascade-lock fire on real public-surface change.
- ❌ The `uv lock --check` staleness gate (`scripts/quality-gates-base/base-service.sh:215` + `base-library.sh:105`) does NOT exempt internal editable drift → the minor-bump red.
- ❌ No "MAJOR bump → full SIT in dep order → else escalate to vm-planning" wiring.

## Phases

### Phase 1 — Lock gate ignores internal editable-dep drift (the immediate unblock) — P0

- [ ] [SCRIPT] P0. Write `scripts/cicd/check_lock_internal_only_drift.py` (PM): on `uv lock --check` failure, regenerate to
      a temp lock + diff; return 0 (PASS) if the ONLY changed `[[package]]` entries are internal editable deps (name in
      the workspace-manifest internal set AND `editable = "../…"`), return 1 (FAIL) if any EXTERNAL dep version changed.
      Never recommit the lock (avoid the re-lock churn the operator wants gone). Unit tests: internal-only drift → pass;
      external drift → fail; no drift → pass; mixed → fail.
- [ ] [SCRIPT] P0. Wire it into `base-service.sh` + `base-library.sh`: replace the raw `uv lock --check … || exit 1` with
      `uv lock --check || python3 <pm>/scripts/cicd/check_lock_internal_only_drift.py` (fail only on external drift).
      Keep the pinned-uv-only blocking behavior. Roll out via `rollout-*.sh` (NEVER hand-edit per-repo copies).
- [ ] [SCRIPT] P0. Verify MTDS (the incident repo) QG goes GREEN after UAC main=0.2.1 lands + this gate change; then flip
      the cicd_contract_hardening "MTDS consumer re-lock" P2 todo.

### Phase 2 — MAJOR bump triggers full SIT in dependency order — P1

- [ ] [SCRIPT] P1. When `detect_breaking_change.py` classifies a bump as MAJOR (public-surface break), the promotion path
      MUST trigger a **full-workspace SIT run in dependency (topological) order** before promoting the major to main —
      verifying every dependent still passes QG against the new major. Wire into semver-agent / the staging→main promoter.
- [ ] [SCRIPT] P1. minor/patch bumps DO NOT trigger SIT or consumer rebuilds (they ride the range) — assert the negative
      (no SIT fan-out on a non-breaking bump) so the CI-noise reduction actually holds.

### Phase 3 — Stuck-staging escalation to vm-planning — P1

- [ ] [SCRIPT] P1. If a MAJOR-bump SIT/staging workflow gets STUCK (e.g. the `[skip ci]`-version-bump-head deadlock, or a
      genuine SIT failure a worker must resolve), escalate to **vm-planning** (the orchestrator) via
      `escalate-to-orchestrator` to resolve the stuck staging workflow — do not leave it silently jammed. Compose with the
      ci-failure-watcher `--auto-recover` (mechanical deadlock) vs `--escalate` (genuine) split.

### Phase 4 — MAJOR/MINOR classification matrix refinement — P2

- [ ] [DOCS] P2. Refine the plan-documented major-vs-minor matrix based on **schemas + API contracts** (UAC public surface,
      manifest schema_version, event contracts) — what is a breaking (major) change vs a backward-compatible (minor/patch)
      one — so `detect_breaking_change.py` + semver-agent classify correctly. SSOT: `codex/08-workflows/ci-cd-flow.md`
      § "Breaking = public-surface change".

## Success criteria

- A UAC (or any internal lib) minor/patch bump reds ZERO consumer QGs and triggers ZERO consumer rebuilds.
- A MAJOR bump triggers a full SIT in dep order; on stuck staging it escalates to vm-planning (never silently jams).
- External-dep reproducibility unchanged (external drift still hard-fails `uv lock --check`).
- The major/minor boundary is matrix/contract-driven, not a version-phase heuristic.

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` (dependency-promotion model + the lock-gate internal-exemption), `codex/06-coding-standards/quality-gates.md` (uv.lock gate behavior), CLAUDE.md § Dependencies+builds (range pins absorb minor/patch; only major forces rebuild).
