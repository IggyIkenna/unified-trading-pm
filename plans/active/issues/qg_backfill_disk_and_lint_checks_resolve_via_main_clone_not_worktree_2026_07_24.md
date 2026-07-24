---
doc_type: issue
title:
  At least two quality-gates.sh steps (check_backfill_vm_disk_provisioning.py, ruff LINT) can resolve target paths
  through the shared canonical MAIN clone instead of the calling worktree, so no worktree-based isolation reliably gets
  a green QG sentinel while any other agent has dirty/untracked issues in MAIN
summary: >-
  Originally surfaced during the sports_consolidated_closeout_2026_07_19 session (Track V): at least two
  `quality-gates.sh` steps — `check_backfill_vm_disk_provisioning.py` (deployment-service) and the ruff LINT step — were
  observed resolving their target paths via something that reaches back to the canonical
  `unified-trading-system-repos/<repo>` MAIN clone rather than respecting `cwd`/the calling worktree's own tree. Proven
  twice: (1) moving a file OUT of the MAIN clone flipped a previously-failing check clean, without touching anything in
  the worktree that was actually being gated; (2) a lint failure referenced a file path that existed only as another
  agent's untracked WIP sitting in the shared MAIN clone, never committed or present in the worktree under test.
  Practical effect: a worktree-isolated QG run cannot reliably produce a trustworthy green sentinel while ANY other
  agent has dirty/untracked lint- or disk-provisioning-relevant files sitting in the shared MAIN clone — this blocked 2
  of the source session's own verified-correct, parked changes and was independently hit by 4 sub-agents in that session
  alone.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, worktree-isolation, path-resolution, main-clone, multi-agent-safety, infra]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
  ]
created: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
source:
  "sports_consolidated_closeout_2026_07_19.md Track V (originally surfaced there, filed as its own doc per that plan's
  own outstanding [DATA] P3 todo, executed via sports_closeout_batch1_ao_ready_2026_07_24.md)"
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
---

# QG steps resolving through MAIN instead of the calling worktree

## What I found

Carrying forward a finding already surfaced (not re-derived here) during the `sports_consolidated_closeout_2026_07_19`
session, per that plan's own Track V:

> At least two `quality-gates.sh` steps (`check_backfill_vm_disk_provisioning.py` in deployment-service, and the ruff
> LINT step) resolve target paths via something that reaches back to the canonical `unified-trading-system-repos/<repo>`
> MAIN clone rather than respecting `cwd`/a worktree's own tree — proven by moving a file out of MAIN and watching the
> check flip clean, and by a lint failure referencing a file that exists only as another agent's untracked WIP in MAIN.

**Reproduction (already established, carried forward verbatim per this todo's own scope)**:

1. A `check_backfill_vm_disk_provisioning.py` (or ruff LINT) failure was observed inside a worktree-isolated QG run.
2. The failing content did not exist anywhere in that worktree's own tree (uncommitted or committed) — only as
   dirty/untracked content sitting in the shared bare `unified-trading-system-repos/<repo>` MAIN clone.
3. Moving/removing the offending file from the MAIN clone (not touching the worktree under test at all) flipped the
   check clean on the next run.
4. Separately, a ruff LINT failure's reported file path was traced to another agent's untracked WIP file that existed
   only in MAIN, never committed, never present in the worktree being gated.

**Practical effect**: no worktree-based isolation (the Path-B `git clone --reference` per-slot model —
`/codex/05-infrastructure/per-tab-worktrees.md`) can reliably produce a trustworthy green QG sentinel while ANY OTHER
agent has dirty/untracked lint- or disk-provisioning-relevant files sitting in the shared MAIN clone. This is a
correctness gap in the isolation guarantee the per-slot worktree model is supposed to provide, not a flaky/rare edge
case — it blocked 2 of the source session's own verified-correct, parked changes (see "Blocked work" below) and was
independently hit by 4 sub-agents within that one session.

**Root-cause candidate (not independently confirmed — flagged for whoever picks up the fix, not asserted as proven)**:
`check_backfill_vm_disk_provisioning.py` itself resolves its target directory via
`Path(__file__).resolve().parents[2] / "scripts" / "vm"` (worktree-correct on its own, since each Path-B slot clone
holds real files, not symlinks), and `deployment-service/scripts/quality-gates.sh` invokes it via
`"${WORKSPACE_ROOT}/deployment-service/scripts/quality_gates/check_backfill_vm_disk_provisioning.py"`, where
`WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}"` (same pattern in the shared
`unified-trading-pm/scripts/quality-gates-base/base-service.sh`, used for several other gate paths including the
version-alignment/dep-content-sync/lock-satisfies-pyproject checks). The `:-` fallback only computes a worktree-local
value when `WORKSPACE_ROOT` is UNSET in the calling shell — if any session/tooling exports `WORKSPACE_ROOT` pointing at
the bare MAIN root (e.g. an older bootstrap convention, a persistent tmux/profile export, or a VM-side script) and that
export outlives its original purpose, EVERY subsequent `quality-gates.sh` invocation in ANY worktree of that shell would
silently resolve every `${WORKSPACE_ROOT}/<repo>/...` gate path to the MAIN clone regardless of which worktree actually
invoked it. This was NOT reproduced independently in this session (a fresh check of `$WORKSPACE_ROOT` in this slot's own
shell found it unset, correctly deriving worktree-local via the fallback) — it is offered as the most plausible
mechanism given the codebase's own path-construction pattern, not a confirmed root cause. The ruff LINT step's exact
resolution path was not independently re-traced this session either (not found invoked directly in deployment-service's
own `quality-gates.sh`; it lives in the shared `base-service.sh` LINT phase via `$RUFF_CMD check $SOURCE_DIRS`, whose
`$SOURCE_DIRS` derivation needs the same scrutiny).

## Blocked work (from the source session)

Two verified-correct, unshipped changes were sitting parked specifically because of this QG path-resolution problem, not
because of their own content:

1. `deployment-service` — 3 launcher `START_DATE` clamp hardening edits + a new
   `launch-sports-league-id-relocation-vm.sh` launcher, in worktree `deployment-service-sports-wt`.
2. `market-tick-data-service` — a `--shard-of`/`--shard-index` filter on the relocation executor (verified correct but
   ultimately unneeded — data-partitioning achieved the same result), in worktree `market-tick-data-service-sports-wt`.

Both were re-verified correct as of 2026-07-22 and should ship via the normal path "once the shared MAIN clones quiet
down" (checking `git status` on each MAIN clone first) — a manual workaround, not a fix for the underlying isolation
gap.

## Why it matters

The Path-B per-slot worktree model (`/codex/05-infrastructure/per-tab-worktrees.md`) exists specifically so that
multiple agents can work concurrently without stepping on each other's state. A QG step that silently reaches into the
shared MAIN clone defeats that isolation guarantee for exactly the steps it's supposed to protect: a genuinely clean,
correct worktree can fail QG because of SOMEONE ELSE's untracked WIP in a completely different tree, and — the more
dangerous direction — a worktree WITH a real problem could conceivably read as clean if MAIN happens to be tidy at that
moment, since the check isn't actually looking at the tree it claims to be gating. Cross-cutting: any other QG step
following the same `${WORKSPACE_ROOT}/<repo>/...` construction (the version-alignment gate, dep-content-sync check,
lock-satisfies-pyproject check, and others in `base-service.sh` share this exact pattern) is a plausible sibling
instance of the same class of bug, not necessarily limited to the two steps caught so far.

## Recommended decision

- **Option A (recommended)**: audit every `${WORKSPACE_ROOT}/<repo>/...`-style path construction in `base-service.sh` +
  each repo's own `quality-gates.sh` and confirm each one derives from the CALLING repo's own
  `git rev-parse --show-toplevel` (or `$REPO_ROOT`), never a pre-exported `$WORKSPACE_ROOT` that could point elsewhere.
  If the root cause is confirmed to be a stale/persistent `WORKSPACE_ROOT` export surviving across worktree contexts,
  the fix is either derive it fresh every invocation (never trust an inherited env value for this specific computation)
  or an explicit worktree-identity assertion (fail loud if the derived MAIN-adjacent path doesn't match the calling
  repo's actual root) rather than silently resolving elsewhere.
- **Option B**: add a QG self-check step (cheap, early in the pipeline) that asserts every path a later QG step is about
  to touch is inside the CURRENT worktree's own root — a structural guard against this exact class of bug recurring in
  any future gate script, not just the two already caught.

## Todos

- [x] [DIAG] P2. ✅ **Root cause CONFIRMED via controlled before/after repro** — the `WORKSPACE_ROOT` pre-export
      hypothesis is correct, and the blast radius is WIDER than originally scoped (not just "reads MAIN's copy of the
      same repo" — under the failure condition, the whole shared QG framework can misidentify which REPO it's even
      targeting). Reproduction (in `.tabs/6/deployment-service`, seeded files relocated out of MAIN afterward via `mv`,
      not deleted — `rm`/`git clean`/`find -delete` are guardrail-blocked for autonomous workers): 1. **Baseline
      (WORKSPACE_ROOT unset, the default)**: seeded a download-heavy launcher
      (`scripts/vm/launch-qg-repro-test-backfill-vm.sh`, no `--boot-disk-type`, matching the `backfill` NAME_MARKER)
      directly in the bare MAIN `deployment-service` clone. Ran
      `python3 scripts/quality_gates/check_backfill_vm_disk_provisioning.py` from the WORKTREE — the seeded MAIN file
      was **NOT flagged**; the check correctly scoped to the worktree's own `scripts/vm/`. Same result for
      `ruff check deployment_service/` against an unused-import file seeded in MAIN. This matches the source session's
      own note that a fresh check of `$WORKSPACE_ROOT` found it unset — confirms the bug is NOT a universal
      default-condition failure. 2. **Explicit stale export**:
      `export WORKSPACE_ROOT=/home/ubuntu/unified-trading-system-repos` (the bare MAIN root, no `/deployment-service` or
      `.tabs/N` suffix), then ran the SAME check invoked exactly as `deployment-service/scripts/quality-gates.sh`
      invokes it
      (`python3 "${WORKSPACE_ROOT}/deployment-service/scripts/quality_gates/check_backfill_vm_disk_provisioning.py"`) —
      this time the seeded MAIN launcher WAS flagged (`download-heavy VM with NO --boot-disk-type` +
      `boot disk 100GB < 250GB minimum`), proving `${WORKSPACE_ROOT}/deployment-service/...` literally invokes **MAIN's
      copy of the check script itself** (not the worktree's), whose `Path(__file__).resolve().parents[2]` then naturally
      resolves to MAIN's own `scripts/vm/` — this is "wrong script binary gets executed", not a read-path leak from a
      correctly-invoked worktree script. 3. **Wider blast radius, found while tracing the LINT step**:
      `deployment-service/scripts/quality-gates.sh` SOURCES
      `${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh`, which in turn sources
      `qg-common.sh` via `${BASH_SOURCE[0]%/*}` (i.e., wherever ITS OWN sourced location was). Under the same stale
      `WORKSPACE_ROOT`, sourcing `qg-common.sh` derives `PROJECT_ROOT` via `_qg_walk_up_to_pyproject($QG_SCRIPT_DIR)`
      starting from MAIN's `unified-trading-pm/scripts/quality-gates-base` — which walks up to MAIN's
      **`unified-trading-pm`** root, not `deployment-service`'s. Empirically confirmed: the resulting banner prints
      `[quality-gates] unified-trading-pm @        .../unified-trading-system-repos/unified-trading-pm` — i.e., under
      this failure condition the shared QG framework doesn't just read MAIN instead of the worktree for the SAME repo,
      it can silently believe it is gating an entirely DIFFERENT repo (`unified-trading-pm` instead of
      `deployment-service`). `deployment-service`'s own `quality-gates.sh` never sets `PROJECT_ROOT` itself before
      sourcing `base-service.sh`, so there is no earlier value protecting against this fallback. **Conclusion**: the
      vulnerability is real and precisely characterized, but conditional — it requires `WORKSPACE_ROOT` to already be
      exported (stale/wrong) in the invoking shell BEFORE `quality-gates.sh` runs; the default (unset) path derives
      correctly per-invocation and is safe. No evidence found of anything in this workspace currently exporting
      `WORKSPACE_ROOT` persistently (checked `.bashrc`/`.profile`/shell-snapshots — none do). The original session's 2
      reproductions were therefore most likely caused by a stale export specific to that session's shell/tmux, not a
      structural per-invocation bug — but the underlying `${WORKSPACE_ROOT:-...}` / `${BASH_SOURCE[0]%/*}`-relative
      sourcing PATTERN remains a latent landmine: any future tooling, wrapper script, or persistent shell profile that
      exports `WORKSPACE_ROOT` (even for an unrelated reason) will silently reactivate this exact failure class
      workspace-wide, for every repo, for every QG step built on this pattern. Recommend **Option A** from this doc's
      own "Recommended decision": derive `PROJECT_ROOT`/`WORKSPACE_ROOT` fresh every invocation from
      `git rev-parse --show-toplevel` and NEVER honor an inherited env value for this specific computation, rather than
      Option B's after-the-fact self-check (prevention over detection). Left as todo 2 below (a CODE fix, out of this
      DIAG todo's scope).
- [ ] [CODE] P2. Once confirmed, fix the path derivation so every QG step is provably worktree-scoped — Option A or B
      above. (repo: unified-trading-pm, deployment-service)
