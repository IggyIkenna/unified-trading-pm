---
title: uv.lock determinism — read-only QG verifier + pinned uv toolchain
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
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
- [ ] [INFRA] P2. **Single-SoT follow-up**: add `UV_PINNED` to `resolve-canonical-versions.py` output + a sourced
      constant so setup.sh / Dockerfile / QG read one value instead of 3 hardcodes. **DEFERRED** until the 3 sites are
      pinned and proven.
- [ ] [INFRA] P3. Locate + pin CI uv install (confirm base-image path or add `astral-sh/setup-uv@v5 version: 0.10.8`)

### Phase 2 — Verifier (QG read-only, warn-first)

- [x] [INFRA] P2. Flip `uv lock \|\| :` → `uv lock --check` (warn-only) in `base-service.sh` + `base-library.sh` — stops
      QG from dirtying the tree (the churn fix) ✅

### Phase 3 — Re-lock-all sweep (make every committed lock canonical for 0.10.8)

- [ ] [INFRA] P2. With pinned uv, run `uv lock` in every Python repo; commit only repos that actually change (fixes
      deployment-api stale lock + yanked polars). Verify `uv lock --check` exits 0 workspace-wide.

### Phase 4 — Ratchet verifier to blocking

- [ ] [INFRA] P2. After Phase 3 green workspace-wide, change Phase-2 warn → `exit 1` (blocking gate). Add a one-line
      `uv --version == 0.10.8` assertion next to it so a mis-provisioned slot fails fast. **Blocked on Phase 3.**

### Phase 5 — Codex SSOT update

- [ ] [INFRA] P3. Update `cursor-rules/dependencies/uv-lock-file.mdc` +
      `codex/06-coding-standards/dependency-management.md`: document the 3-role split (quickmerge=writer, QG=read-only
      verifier, pinned uv=determinism).

## Success criteria

- Running `quality-gates.sh` locally never leaves `uv.lock` dirty (Phase 2).
- `uv lock --check` exits 0 in every Python repo with pinned uv (Phase 3).
- QG blocks a stale `uv.lock` instead of silently rewriting it (Phase 4).
- FF-pull cron no longer jams on a dirty `uv.lock`.

## Downstream consumers

- `slot-cron-ff-pull.sh` — should stop encountering dirty locks (no script change needed once Phase 2 lands).
- All service repos inherit the pinned uv via the UTL base image (Phase 1).
