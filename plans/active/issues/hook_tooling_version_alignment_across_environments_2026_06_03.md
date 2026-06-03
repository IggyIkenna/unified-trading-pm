---
title:
  "pre-commit/prek hook tooling + formatter versions are NOT aligned across environments (laptop tabs/main worktrees vs
  orchestrator VM vs worker VMs) — worker VMs install neither prek nor pre-commit, so agent commits there bypass hooks +
  use a different prettier than laptop/CI → reformat-residue churn that jams FF-sync"
created: 2026-06-03
author: ikenna (slot 1)
source:
  - agent-orchestrator/scripts/bootstrap_vm.sh — installs apt base + Node 20 + uv + Claude CLI + an orchestrator .venv;
    greps for prek/pre-commit/workspace-bootstrap/.venv-workspace/install-hooks all return nothing → neither hook runner
    is installed and no `prek install`/`pre-commit install` is run on worker/orchestrator VMs
  - agent-orchestrator/scripts/worker-host-preflight.sh — no prek/pre-commit/quickmerge presence check
  - workspace-constraints.toml:70-71 — pins `pre-commit>=3.0,<4.0.0` + `prek>=0.3.0,<1.0.0`
  - laptop (this slot host) — system `pre-commit` 4.5.1 on PATH (OUTSIDE the <4.0.0 constraint); `prek` 0.3.8 in
    .venv-workspace
  - scripts/quickmerge.sh:1169,1174,1175 — hardcodes `npx prettier@3.6.2`; probes `command -v pre-commit` only (not
    prek)
  - .pre-commit-config.yaml:13 — prettier mirror rev `v3.2.0`; ruff `v0.15.0`
  - scripts/manifest/check-precommit-versions.py — aligns ruff + pre-commit-hooks REVS to workspace-constraints.toml via
    `pre-commit install` (not prek); does NOT cover prettier version; is not run on VMs
locked_by: live-defi-rollout
---

## What I found

Hook tooling and the formatters it runs are **not version-aligned across the environments that produce commits**, and
the worker VMs (where most background-agent commits happen) are missing the tooling entirely.

| Environment                    | prek                    | pre-commit                                 | hooks installed?                          | prettier used by quickmerge |
| ------------------------------ | ----------------------- | ------------------------------------------ | ----------------------------------------- | --------------------------- |
| Laptop tabs/main worktrees     | 0.3.8 (.venv-workspace) | **4.5.1 (system — violates `<4.0.0` pin)** | yes                                       | `npx prettier@3.6.2`        |
| Orchestrator VM                | not installed           | not installed                              | no `prek/pre-commit install` in bootstrap | `npx prettier@3.6.2`        |
| Worker VMs (background agents) | not installed           | not installed                              | no                                        | `npx prettier@3.6.2`        |

Three distinct misalignments:

1. **Worker/orchestrator VMs install neither prek nor pre-commit** (`bootstrap_vm.sh` never installs them, never runs
   `setup.sh`/`install-hooks`). So on the fleet: (a) quickmerge's pre-stage formatter always falls to the `npx prettier`
   branch (the `command -v pre-commit` probe is false), and (b) the on-commit hooks (prettier-autostage / gitleaks /
   branch-drift) are not installed, so agent commits there run with NO hook validation.
2. **`pre-commit` version drift**: workspace-constraints pins `<4.0.0`, the laptop's PATH `pre-commit` is `4.5.1`. The
   pin looks vestigial — the workspace runner is actually **prek**, so it is unclear pre-commit should still be pinned
   at all.
3. **prettier version drift**: quickmerge formats with `prettier@3.6.2`, `.pre-commit-config.yaml` pins the mirror at
   `v3.2.0`, and the prettier-autostage wrapper resolves repo-local/npx prettier (unpinned). Three potentially-different
   prettier versions reflow markdown/yaml/json differently → the reformat residue that jams `slot-cron-ff-pull.sh` (the
   2026-06-02 69-file-residue incident class).

## Why it matters

Mismatched formatter versions are a primary driver of the **reformat-residue / foreign-dirt churn** this workspace
already fights (prettier-autostage no-ops-when-behind; the quickmerge `--files`-scoping fix 2026-06-03). If the laptop
pre-formats with prettier 3.6.2 but CI/the hook checks with 3.2.0, every touched doc can ping-pong reflow. And worker
VMs committing without hooks installed means agent commits on the fleet skip gitleaks + the branch-drift gate + the
auto-stage safety entirely — a correctness + secrets-hygiene gap, not just cosmetic.

## Decisions (operator, 2026-06-03)

1. **Hook runner = prek (single runner).** Retire the `pre-commit` pin from `workspace-constraints.toml`; switch
   `check-precommit-versions.py` + quickmerge to prek. (Resolves the laptop 4.5.1-vs-`<4.0.0` drift by removing the dead
   pin.)
2. **Canonical prettier = `3.6.2`** (verified: `unified-trading-system-ui` + `deployment-ui` `package.json` both pin
   `^3.6.2`; quickmerge already uses `prettier@3.6.2`). The `.pre-commit-config.yaml` `v3.2.0` mirror rev is **DEAD**
   (replaced by the `prettier-autostage` wrapper, which resolves repo-local 3.6.2) — it is a stale-config landmine to
   clean up, not an active second version.
3. **VM bootstrap** — add prek + `prek install` to `bootstrap_vm.sh` + a prek assertion in `worker-host-preflight.sh`.

**Already aligned (no work needed):** quickmerge's `--files` path pre-formats with `npx prettier@3.6.2` scoped to
`--files` and re-stages only `--files` on retry (shipped 2026-06-03 PRs) — so the path agents actually use already
matches both decisions on every host (laptop + VM), independent of whether prek/pre-commit is installed.

## Actionable todos

- [ ] [SCRIPT] P1. `bootstrap_vm.sh`: install prek at the pinned version + run `prek install` (so on-commit hooks —
      gitleaks / branch-drift / prettier-autostage — actually run on worker+orchestrator VMs, not just laptop/CI);
      `worker-host-preflight.sh`: assert prek present + version-matches. **Highest impact** (VM commits currently bypass
      all hooks). Target: agent-orchestrator. NOTE: untestable from a laptop slot + AO is mid-migration (G6) — route to
      the AO/fleet owner.
- [ ] [SCRIPT] P1. Retire the `pre-commit` pin in `workspace-constraints.toml` (prek-only); re-derive via
      `resolve-canonical-versions.py`; switch `check-precommit-versions.py`'s `pre-commit install` → `prek install` and
      add a prettier-`3.6.2` rev assertion alongside the ruff one. Target: unified-trading-pm.
- [ ] [SCRIPT] P2. Clean up the dead `.pre-commit-config.yaml` prettier mirror `rev: v3.2.0` → `v3.6.2` (or remove the
      replaced mirror block) for clarity; roll out fleet-wide via `rollout-prettier-unified.py`. Target:
      unified-trading-pm + fleet.
- [ ] [SCRIPT] P3. quickmerge UNSCOPED-path probe (`--files`-absent) `pre-commit run prettier` → prek (cosmetic; the
      `--files` path is already canonical-npx). Target: unified-trading-pm.
