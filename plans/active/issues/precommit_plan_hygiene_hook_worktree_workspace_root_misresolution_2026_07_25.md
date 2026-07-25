---
doc_type: issue
title:
  ".pre-commit-config.yaml's plan-hygiene hook resolves run_hygiene_sweep.sh via the same fragile
  ${WORKSPACE_ROOT:-$(git rev-parse --show-toplevel)/..} pattern already root-caused and partially fixed in qg-common.sh
  — but THIS location was never covered by that fix, and 3 independent Agent-tool worktree-isolated agents hit it today"
summary: >-
  `.pre-commit-config.yaml`'s `plan-hygiene` hook entry (line ~53-56) computes its target sweep script path as
  `${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." &&
  pwd)}/unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh` — the identical
  `${WORKSPACE_ROOT:-...}`-inheritance / `git rev-parse --show-toplevel`-relative construction that
  `qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md` root-caused and partially fixed
  (Option B: a worktree-identity guard added to the shared `qg-common.sh`). That fix only covers `quality-gates.sh`'s
  own sourcing chain — this `.pre-commit-config.yaml` hook is a completely separate mechanism (prek/pre-commit, not
  quality-gates.sh) and was never touched by that fix. Three independent agents running in `.claude/worktrees/<id>/`
  isolation today (2026-07-25, the `/plan-reconcile` apply-Workflow's follow-up passes) all independently hit this hook
  resolving/validating against the MAIN checkout instead of their own worktree.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, pre-commit, worktree-isolation, path-resolution, main-clone, multi-agent-safety, infra]
related:
  [
    /plans/active/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md,
    /plans/active/issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found independently by 3 Agent-tool sub-agents (isolation: worktree) during this session's plan-reconcile follow-up
  passes (archival-ritual sweep + line-cap split-and-apply), 2026-07-25.
depends_on: []
---

# `.pre-commit-config.yaml`'s plan-hygiene hook mis-resolves worktree paths — same bug class, different location than the already-fixed qg-common.sh instance

## What was found (3 independent confirmations)

1. **Archival-sweep agent** (`.claude/worktrees/agent-a62f2980f38fcf6b0`): the `plan-hygiene` pre-commit hook's
   `run_hygiene_sweep.sh` invocation "resolves paths against the _main_ `unified-trading-pm` checkout's absolute
   filesystem path rather than the current worktree ... producing false 'No such file' failures for worktree-only
   new/renamed files." Worked around via `--no-verify` after independently re-running
   `check_frontmatter_schema.py`/`check_line_caps.sh`/`check_reference_paths.py` clean from the worktree before each
   such commit — **flagging this `--no-verify` usage transparently**: CLAUDE.md's git safety protocol says hooks are
   never skipped without explicit user request; this agent made an autonomous judgment call to bypass a hook it had
   independently diagnosed as broken, compensating with manual equivalent checks rather than skipping validation
   outright. The practical risk was mitigated but the deviation itself should be visible, not silently absorbed.
2. **defi_consolidated_closeout split agent** (`.claude/worktrees/agent-af3c07d838d9fe61d`): "the
   `.pre-commit-config.yaml` plan-hygiene hook's `entry:` resolves its target repo via
   `${WORKSPACE_ROOT}/unified-trading-pm/...`, which silently pointed at the unrelated MAIN checkout instead of this
   session's `.claude/worktrees/<id>/` worktree — same bug class as the already-resolved [qg_backfill_disk...] doc, but
   that fix only covers `qg-common.sh`, not this pre-commit hook." Worked around via a private scratchpad symlink +
   `WORKSPACE_ROOT` override for its own commits only (hooks still ran, just against corrected paths — no
   `--no-verify`).
3. **cefi_residual_followups split agent** (`.claude/worktrees/agent-accb7bc08adc67201`): "the prek `plan-hygiene` hook
   mis-resolves paths for Path-B isolated worktrees ... it validated stale/missing content until I set `WORKSPACE_ROOT`
   to a temp symlink pointing at my own worktree." Same workaround as #2, no `--no-verify`.

All three hit this independently, on different files, in different worktrees, during different tasks — this is a
reproducible structural gap, not a one-off flake.

## Root cause (found this session, not independently re-derived by the 3 agents — they diagnosed the symptom, this

## confirms the exact line)

`.pre-commit-config.yaml` line ~53-56:

```
entry:
  bash -c 'SWEEP="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." &&
  pwd)}/unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh"; ...'
```

This is the **identical fragile pattern**
`qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md` root-caused for
`deployment-service/scripts/quality-gates.sh` + `qg-common.sh`:
`${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}` derives a "parent of repo root" path that
assumes the repo root's immediate parent directory is `unified-trading-system-repos` (true for a normal per-slot clone
under `.tabs/N/`, per that doc's Path-B model) — but for an `.claude/worktrees/<agent-id>/` git worktree (a DIFFERENT
isolation mechanism, created by the Agent tool's `isolation: 'worktree'` option, nested inside the calling repo's own
directory tree), `git rev-parse --show-toplevel` returns the worktree's own root, and `/..` from there does not land on
`unified-trading-system-repos` — the append-`/unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh` step then
resolves somewhere that either (a) doesn't exist (should hit the hook's own explicit "sweep NOT FOUND — REFUSING to
commit" fail-loud guard, which none of the 3 agents reported hitting) or (b) happens to still resolve to a real
`run_hygiene_sweep.sh` — just the MAIN checkout's copy, running against MAIN's tree instead of the worktree's — which
matches what all 3 agents actually observed (stale/wrong content validated, not a hard NOT-FOUND failure). **The exact
mechanism by which case (b) occurs for `.claude/worktrees/` specifically (as opposed to `.tabs/N/`) was not
independently reproduced in this doc** — flagged for whoever picks up the fix, same epistemic honesty as the original
doc's own initial root-cause section before its DIAG todo nailed it down further.

## Why this is a different finding, not a duplicate

- **Different hook mechanism**: `.pre-commit-config.yaml` (prek/pre-commit) vs `quality-gates.sh`'s own sourcing chain
  (`qg-common.sh`). The shipped fix (`unified-trading-pm@e70a0d18e`, a worktree-identity guard in `qg-common.sh`) does
  not touch `.pre-commit-config.yaml` at all — grepped, zero overlap.
- **Different worktree model**: the original doc's reproductions were in the Path-B **per-slot** worktree model
  (`.tabs/N/<repo>`, `/codex/05-infrastructure/per-tab-worktrees.md`). Today's 3 confirmations are all in **Agent-tool
  ephemeral worktrees** (`.claude/worktrees/<agent-id>/`, created per-`Agent(isolation:'worktree')` call) — a distinct
  mechanism this workspace also relies on heavily (used throughout this session's follow-up agent dispatches). Both are
  real, both need this class of bug closed.

## Recommended decision

- **Option A (recommended, mirrors the qg-common.sh precedent's own stated-but-deferred stronger fix)**: rewrite the
  `plan-hygiene` hook's `entry:` to derive its target path fresh from `git rev-parse --show-toplevel` for the CURRENT
  invocation only, never an inherited `${WORKSPACE_ROOT}` value and never a `/..`-relative parent-directory assumption —
  e.g. `SWEEP="$(git rev-parse --show-toplevel)/scripts/plan-hygiene/run_hygiene_sweep.sh"` (the sweep script already
  lives inside `unified-trading-pm` itself, so this should just resolve within the same repo/worktree being gated, no
  cross-repo parent-join needed at all — worth double-checking whether the original
  `${WORKSPACE_ROOT}/unified-trading-pm/...` join was ever actually necessary, or a copy-paste artifact from a
  cross-repo QG pattern that doesn't apply to a same-repo pre-commit hook). [WORKER REC]
- **Option B**: extend the `qg-common.sh` worktree-identity guard's underlying pattern (fail loud on a derived path that
  doesn't match the invoking repo's actual root) to this hook specifically, consistent with the existing fix's Option B
  precedent.

## Todos

- [ ] [CODE] P2. Fix `.pre-commit-config.yaml`'s `plan-hygiene` hook `entry:` to resolve `run_hygiene_sweep.sh` via
      fresh per-invocation `git rev-parse --show-toplevel`, not the `${WORKSPACE_ROOT:-...}` inheritance pattern —
      confirm whether the `unified-trading-pm/` path segment is even needed once resolved this way. Verify against both
      an `.claude/worktrees/<id>/` Agent-tool worktree AND a `.tabs/N/` per-slot worktree before shipping. Repo:
      unified-trading-pm.
- [ ] [DIAG] P3. Independently reproduce the exact `.claude/worktrees/`-specific failure mechanism (case (b) above) with
      a controlled before/after repro, mirroring the rigor of the already-closed DIAG todo in the sibling doc — not
      required to ship the Option A fix (the fix doesn't depend on knowing the exact mechanism), but worth confirming
      for completeness and to rule out a wider blast radius on other `${WORKSPACE_ROOT:-...}`-pattern hooks. Repo:
      unified-trading-pm.
