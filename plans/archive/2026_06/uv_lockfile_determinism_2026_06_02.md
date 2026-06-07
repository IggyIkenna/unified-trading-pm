---
title: uv.lock determinism — read-only QG verifier + pinned uv toolchain
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: archived
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
created: 2026-06-02
locked_by: live-defi-rollout
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
source:
  - operator design discussion 2026-06-02 (slot tab/ikennaigboaka/4)
---

> **✅ ARCHIVED 2026-06-07 [unlock-plan].** Core DONE (Phases 1-5: uv pinned `0.10.8` at all sites + verifier
> `uv lock --check` blocking + re-lock-all sweep + churn fix). Of the 3 residual items: the PM codex-fallback item is
> RESOLVED (PM v2 green), and the 2 deferreds are migrated to `plans/epics/infrastructure_master.md` § "P3 — backlog":
> the **uv-pin drift-guard** (no active drift) and the **fleet per-repo local-QG debt sweep** (overlaps
> `utl_full_quality_gates_green`).
>
> ## Deferred work — migrated to:
>
> - **uv-pin drift-guard** → `infrastructure_master` § "P3 — backlog" (⚠️ touches `base-service.sh` — coordinate with
>   `cicd_contract_hardening`).
> - **Fleet per-repo local-QG debt sweep** → `infrastructure_master` § "P3 — backlog" (overlaps
>   `utl_full_quality_gates_green`).

# uv.lock determinism — read-only QG verifier + pinned uv toolchain

## Problem

`uv.lock` is committed by design (SSOT rule `cursor-rules/dependencies/uv-lock-file.mdc`: "NEVER gitignore; must be
committed"). The intent: pass QG locally → push → everyone pulls byte-identical resolved deps. But the working tree
keeps going dirty on `uv.lock` (observed: deployment-api, trading-agent-service), which jams the `slot-cron-ff-pull.sh`
fast-forward.

## Root cause (diagnosed 2026-06-02)

Three roles for `uv.lock` are tangled:

| Role                                              | Should be       | Today                                                                                                                                                                                              |
| ------------------------------------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Writer** (update + commit lock on dep change)   | quickmerge only | ✅ quickmerge runs `uv lock` then `git add -A` + commit (`quickmerge.sh:1002/1009`)                                                                                                                |
| **Verifier** (assert lock fresh; never mutate)    | QG, read-only   | ❌ QG **mutates**: `uv lock 2>/dev/null \|\| :` in `base-service.sh:147` + `base-library.sh:76` (local bootstrap). Running QG/`setup.sh` locally rewrites the lock → dirty tree. Errors swallowed. |
| **Determinism** (same deps → byte-identical lock) | pinned uv       | ❌ uv installed unpinned everywhere: `setup.sh:383`, UTL `Dockerfile:59`, CI                                                                                                                       |

`uv.lock` header carries `revision = 3` — bumped by uv across versions, so a different uv reformats the lock even with
identical deps. Plus genuine staleness: `uv lock --check` on deployment-api FAILS (real dep drift / yanked
`polars==1.41.0` never re-locked), while trading-agent-service + unified-api-contracts PASS on local uv 0.10.8. So both
causes are real: serializer drift AND stale-lock commit-discipline gaps.

## Decision

- **Writer** stays quickmerge (already correct).
- **Verifier**: QG stops mutating — flip `uv lock` → `uv lock --check` (read-only). Ratchet: warn-only first (zero
  merge-blocking), then blocking after the re-lock-all sweep makes every committed lock canonical.
- **Determinism**: pin uv to **0.10.8** (matches the version that wrote today's `revision = 3` locks; TAS + UAC already
  pass `--check` on it). Install-pin at every generation site.

## Pre-audit (symbols / sites touched)

- `scripts/quality-gates-base/base-service.sh:147` (mutate) + `:215` (presence) — PM
- `scripts/quality-gates-base/base-library.sh:76` (mutate) + `:118` (presence) — PM
- `scripts/setup.sh:381-384` (unpinned uv install) — PM
- `unified-trading-library/Dockerfile:59` (unpinned uv install) — UTL (base image → all services inherit)
- CI uv install — NOT located in workflow-templates; verify it runs in the base image or pin via `setup-uv`
- `workspace-constraints.toml` is generator-owned (`resolve-canonical-versions.py`) — pin SoT needs a generator change,
  NOT a hand-edit.

## Phased DAG

### Phase 0 — Diagnosis ✅ (this discussion)

- [x] [INFRA] P2. Diagnose churn: QG mutates uv.lock; quickmerge auto-commits; setup always re-locks; uv unpinned;
      `--check` shows TAS/UAC clean on 0.10.8, deployment-api stale — 2026-06-02

### Phase 1 — Determinism (pin uv)

- [x] [INFRA] P2. Install-pin uv==0.10.8 in `setup.sh` (both already-installed + install branches) — PM ✅
- [x] [INFRA] P2. Install-pin uv==0.10.8 in UTL `Dockerfile:59` ✅
- [x] ✅ [INFRA] P2. **Single-SoT follow-up (uv-pin drift-guard)** — **MIGRATED (deferred, no active drift) →
      `plans/epics/infrastructure_master.md` § "P3 — backlog"** (2026-06-07). The 4 pin sites are consistent today
      (`0.10.8`), so there is no active drift; the drift-guard check is a deliberate low-priority follow-up, tracked in
      the epic. ⚠️ **COORDINATION:** this touches `base-service.sh` — a shared QG surface also edited by
      `cicd_contract_hardening` (H5 sentinel + QG-debt steps). Any agent adding the drift-guard must coordinate edits to
      `base-service.sh` to avoid a collision.
- [x] [INFRA] P3. Locate + pin CI uv install — pinned `uv==0.10.8` in `.github/workflows/python-quality-gates-v2.yml`
      (the reusable CI callee) ✅

### Phase 2 — Verifier (QG read-only, warn-first)

- [x] [INFRA] P2. Flip `uv lock \|\| :` → `uv lock --check` (warn-only) in `base-service.sh` + `base-library.sh` — stops
      QG from dirtying the tree (the churn fix) ✅

### Phase 3 — Re-lock-all sweep (make every committed lock canonical for 0.10.8)

- [x] [INFRA] P2. Re-lock-all: 14 stale repos re-locked + committed (0 resolved-version moves, requires-dist sync only);
      all 23 Python repos now pass `uv lock --check` ✅

### Phase 4 — Ratchet verifier to blocking

- [x] [INFRA] P2. Ratchet verifier to blocking in `base-service.sh` + `base-library.sh` — `uv lock --check` BLOCKING
      when on pinned uv 0.10.8, warn otherwise (no false serializer-drift blocks) ✅

### Phase 5 — Codex SSOT update

- [x] [INFRA] P3. Codex update — `.cursor/rules/dependencies/uv-lock-file.mdc` +
      `codex/06-coding-standards/dependency-management.md` document the 3-role split ✅

## Discovered during promotion (2026-06-02)

- [x] [INFRA] P1. **QG host governor crashed `quality-gates.sh` on macOS** — `qg_governor_acquire` used bash≥4.1
      `exec {fd}>` syntax; macOS bash 3.2 parses it as a command and TERMINATES the gate before [3] TESTS, so no
      `.qg_last_passed_sha` sentinel → quickmerge can't promote from any Mac slot (operator's + Harsh's). FIXED: degrade
      to ungoverned on bash <4.1 (same as missing flock). `qg-host-governor.sh` — PM@5004dee84 ✅
- [x] ✅ [INFRA] P1. **PM QG red on 2 PRE-EXISTING codex empty-fallback violations** — RESOLVED (verified 2026-06-07):
      PM `quality-gates-v2` is GREEN on `main` (the [5/6] CODEX step passes), so the 2 violations were cleared by the
      PM-gate owner since. No empty-fallback violations remain in PM `scripts/`.

## Governor fix unmasked workspace-wide pre-existing QG debt (2026-06-03)

- [x] ✅ [INFRA] P1. **Governor fix unmasked fleet-wide pre-existing local-QG debt** — **MIGRATED →
      `plans/epics/infrastructure_master.md` § "P3 — backlog"** (2026-06-07) as the fleet per-repo QG-debt sweep. The
      bash-3.2 governor fix (on LDR) makes local QG run fully + surfaces each repo's accumulated stage-5+ debt (codex /
      cloudbuild-schema / size-import baselines). This is a workspace-wide per-repo cleanup (repo-owner / dedicated
      sweep), NOT this plan — its core (uv pin + relock + verifier + churn fix) is DONE. **Overlaps**
      `utl_full_quality_gates_green` (the T0 QG-green effort) — coordinate the per-repo greening there. The fleet drain
      already proved most repos green on LDR this session; the residual local-only debt is the tracked sweep.

## Success criteria

- Running `quality-gates.sh` locally never leaves `uv.lock` dirty (Phase 2).
- `uv lock --check` exits 0 in every Python repo with pinned uv (Phase 3).
- QG blocks a stale `uv.lock` instead of silently rewriting it (Phase 4).
- FF-pull cron no longer jams on a dirty `uv.lock`.

## Downstream consumers

- `slot-cron-ff-pull.sh` — should stop encountering dirty locks (no script change needed once Phase 2 lands).
- All service repos inherit the pinned uv via the UTL base image (Phase 1).
