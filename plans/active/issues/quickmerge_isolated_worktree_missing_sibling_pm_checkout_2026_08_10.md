---
doc_type: issue
title: >-
  quickmerge.sh isolated-worktree mode fails every non-PM repo ship — missing sibling unified-trading-pm checkout
summary: >-
  quickmerge.sh's isolation execution (`scripts/quickmerge.sh` lines ~515-571) creates a `git worktree add --detach`
  for ONLY the repo being shipped (e.g. `deployment-service`), placed at `$TMPDIR/qm-iso-$$/<repo>`. But
  `quality-gates.sh` (via `base-service.sh`/`qg-environment.sh`, referenced at line 1617 as
  `${REPO_DIR}/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh`) expects `unified-trading-pm` to
  exist as a SIBLING directory next to the repo being gated — true in the normal `.tabs/N/` checkout layout, but
  never set up inside the isolated worktree's temp parent. Every isolated quickmerge for a non-PM repo therefore
  fails at STAGE 3 (Local Quality Gates) with `Missing base quality-gates script:
  .../qm-iso-<pid>/unified-trading-pm/scripts/quality-gates-base/base-service.sh`. Reproduced twice, identical error
  both times, on `deployment-service` — this is deterministic, not a race. Worked around this session via the
  documented `--no-isolated` escape hatch to ship a real fix; not patched directly here given the blast radius of
  hand-editing quickmerge.sh's shared isolation logic under time pressure (it's the ship path for every repo).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, isolated-worktree, quality-gates, infra-bug, ship-pipeline]
related:
  - /codex/05-infrastructure/per-tab-worktrees.md
  - /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
source: >-
  Found live while shipping an unrelated tradfi fix (deployment-service) — isolated quickmerge failed twice,
  identically, at the quality-gates sentinel step. Root-caused by reading quickmerge.sh's isolation block directly.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
---

# quickmerge.sh isolated-worktree mode missing sibling unified-trading-pm checkout

## Evidence

Two consecutive isolated quickmerge attempts on `deployment-service` (same commit, unchanged content between
attempts — ruling out a content/race explanation), both failing identically:

```
==========================================
STAGE 3: Local Quality Gates
==========================================
[deployment-service] ❌ Pass 1 quality-gates.sh sentinel missing — run: bash scripts/quality-gates.sh
[deployment-service] ⏳ sentinel invalid (HEAD moved — a peer likely pushed) — retry 1/3 in Ns
==========================================
STAGE 0.4: Not-Behind Gate (pull latest first)
==========================================
[deployment-service] detached HEAD — skipping not-behind gate
[deployment-service] re-gating (regenerating the Pass-1 sentinel for the current tree)...
Missing base quality-gates script: /private/var/folders/.../qm-iso-<pid>/unified-trading-pm/scripts/quality-gates-base/base-service.sh
[deployment-service] ❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race.
```

`ls` on the isolated worktree parent (`$TMPDIR/qm-iso-<pid>/`) after the failure confirms it contains ONLY the
shipped repo's worktree — no `unified-trading-pm` sibling directory at all.

## Root cause

`scripts/quickmerge.sh`'s isolation block:

```bash
_qm_iso_parent="${TMPDIR:-/tmp}/qm-iso-$$"
_qm_iso_wt="$_qm_iso_parent/$_qm_repo_name"
...
git worktree add --detach -q "$_qm_iso_wt" HEAD
```

only creates a worktree for `$_qm_repo_name` (the repo being shipped). `quality-gates.sh` for any non-PM repo
sources shared base scripts via a path relative to the repo root:

```bash
_QM_ENV_HELPER="${REPO_DIR}/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh"
```

In the normal (non-isolated) checkout, every repo lives as a sibling under `.tabs/N/`, so `../unified-trading-pm`
resolves correctly. Inside the isolated worktree, `$_qm_iso_wt`'s parent (`$_qm_iso_parent`) contains only the one
repo — `../unified-trading-pm` from there resolves to a path that was never created.

## Why this wasn't caught before shipping

Per `deployment-service/.claude/CLAUDE.md`'s 2026-08-09/10 update, isolated-worktree shipping was rolled out
"laptop-only in quickmerge" with a "measured 0/6→6/6" success claim — that measurement was presumably against the
PM repo itself (where `unified-trading-pm` IS the repo being shipped, so the sibling-path problem cannot occur) or
against a repo whose QG doesn't need the PM sibling. Any FIRST isolated ship of a genuinely non-PM service repo
(deployment-service, agent-orchestrator, market-tick-data-service, etc.) after this rollout should reproduce this
identically — worth confirming whether any such ship has actually succeeded yet, or whether this has been silently
broken since rollout with everyone either not hitting it or working around it via `--no-isolated` without filing it.

## Todo

- [ ] [SCRIPT] P1. **Fix quickmerge.sh's isolation setup to also make `unified-trading-pm` available as a sibling of
      the isolated worktree** — either (a) create a second `git worktree add --detach` for `unified-trading-pm` at
      `$_qm_iso_parent/unified-trading-pm` alongside the shipped repo's worktree (mirrors the existing pattern,
      but doubles the worktree-setup cost per isolated ship — for the PM repo case, guard against creating a
      worktree of itself), or (b) symlink the caller's real `../unified-trading-pm` into `$_qm_iso_parent/` (cheaper,
      but shares that checkout's content, which the isolation feature was partly built to avoid contention on — if
      QG only ever READS from `unified-trading-pm` and never writes, a symlink is safe; verify that's actually true
      before choosing this path). **Done when**: an isolated quickmerge on a non-PM repo (e.g. deployment-service)
      reaches STAGE 3 without the "Missing base quality-gates script" error, with a regression test/manual repro
      cited. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **Audit whether any isolated quickmerge on a non-PM repo has actually succeeded since the
      isolation feature's rollout** — if none have, this bug has been silently blocking (or silently
      `--no-isolated`-worked-around) every laptop ship on every non-PM repo since rollout, which is a bigger finding
      than "found once." Repo: unified-trading-pm.

## Progress Log

- 2026-08-10: doc created after reproducing twice live while shipping an unrelated deployment-service fix. Worked
  around via `--no-isolated` for that ship; this bug itself not fixed here (blast-radius risk of hand-patching the
  shared isolation logic under time pressure — deferred to a deliberate pass).
