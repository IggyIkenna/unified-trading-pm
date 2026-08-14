---
doc_type: issue
title: >-
  quickmerge.sh isolated-worktree mode fails every non-PM repo ship — missing sibling unified-trading-pm checkout
summary: >-
  quickmerge.sh's isolation execution (`scripts/quickmerge.sh` lines ~515-571) creates a `git worktree add --detach` for
  ONLY the repo being shipped (e.g. `deployment-service`), placed at `$TMPDIR/qm-iso-$$/<repo>`. But `quality-gates.sh`
  (via `base-service.sh`/`qg-environment.sh`, referenced at line 1617 as
  `${REPO_DIR}/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh`) expects `unified-trading-pm` to
  exist as a SIBLING directory next to the repo being gated — true in the normal `.tabs/N/` checkout layout, but never
  set up inside the isolated worktree's temp parent. Every isolated quickmerge for a non-PM repo therefore fails at
  STAGE 3 (Local Quality Gates) with `Missing base quality-gates script:
  .../qm-iso-<pid>/unified-trading-pm/scripts/quality-gates-base/base-service.sh`. Reproduced twice, identical error
  both times, on `deployment-service` — this is deterministic, not a race. Worked around this session via the documented
  `--no-isolated` escape hatch to ship a real fix; not patched directly here given the blast radius of hand-editing
  quickmerge.sh's shared isolation logic under time pressure (it's the ship path for every repo).
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
resolved_by: "N/A"
locked_by:
locked_since:
context_scope:
  [
    scripts/quickmerge.sh,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
source: >-
  Found live while shipping an unrelated tradfi fix (deployment-service) — isolated quickmerge failed twice,
  identically, at the quality-gates sentinel step. Root-caused by reading quickmerge.sh's isolation block directly.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
archive_exempt: true
drift_direction: advance-code
depends_on: []
---

# quickmerge.sh isolated-worktree mode missing sibling unified-trading-pm checkout

## Evidence

Two consecutive isolated quickmerge attempts on `deployment-service` (same commit, unchanged content between attempts —
ruling out a content/race explanation), both failing identically:

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

`ls` on the isolated worktree parent (`$TMPDIR/qm-iso-<pid>/`) after the failure confirms it contains ONLY the shipped
repo's worktree — no `unified-trading-pm` sibling directory at all.

## Root cause

`scripts/quickmerge.sh`'s isolation block:

```bash
_qm_iso_parent="${TMPDIR:-/tmp}/qm-iso-$$"
_qm_iso_wt="$_qm_iso_parent/$_qm_repo_name"
...
git worktree add --detach -q "$_qm_iso_wt" HEAD
```

only creates a worktree for `$_qm_repo_name` (the repo being shipped). `quality-gates.sh` for any non-PM repo sources
shared base scripts via a path relative to the repo root:

```bash
_QM_ENV_HELPER="${REPO_DIR}/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh"
```

In the normal (non-isolated) checkout, every repo lives as a sibling under `.tabs/N/`, so `../unified-trading-pm`
resolves correctly. Inside the isolated worktree, `$_qm_iso_wt`'s parent (`$_qm_iso_parent`) contains only the one repo
— `../unified-trading-pm` from there resolves to a path that was never created.

## Why this wasn't caught before shipping

Per `deployment-service/.claude/CLAUDE.md`'s 2026-08-09/10 update, isolated-worktree shipping was rolled out
"laptop-only in quickmerge" with a "measured 0/6→6/6" success claim — that measurement was presumably against the PM
repo itself (where `unified-trading-pm` IS the repo being shipped, so the sibling-path problem cannot occur) or against
a repo whose QG doesn't need the PM sibling. Any FIRST isolated ship of a genuinely non-PM service repo
(deployment-service, agent-orchestrator, market-tick-data-service, etc.) after this rollout should reproduce this
identically — worth confirming whether any such ship has actually succeeded yet, or whether this has been silently
broken since rollout with everyone either not hitting it or working around it via `--no-isolated` without filing it.

## Todo

- [x] ✅ [SCRIPT] P1. **Fix quickmerge.sh's isolation setup to also make `unified-trading-pm` available as a sibling of
      the isolated worktree** — unified-trading-pm@6b1346ff9b. Approach (b) symlink implemented via the "miniature
      workspace" loop at `scripts/quickmerge.sh:560-567`: every sibling repo (including `unified-trading-pm`) is
      symlinked into `$_qm_iso_parent/` next to the isolated worktree. Verified safe: QG base scripts only READ from
      `unified-trading-pm` (sourcing `base-service.sh`, `qg-environment.sh`, version-alignment-gate.sh, etc.); all
      writes (lint output, test results, ci-status manifests) target the repo being gated. The private cached venv
      (`~/.cache/qm-iso-venv/<repo>`) already prevents the `.venv` write-contention issue that was separately fixed in
      the same commit. E2E verification pending (isolation is currently opt-in, default-off for laptops per
      `_qm_should_isolate`; no non-PM isolated ship attempted since the fix). Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P3. **Audit whether any isolated quickmerge on a non-PM repo has actually succeeded since the
      isolation feature's rollout** — unified-trading-pm@6b1346ff9b. Audit result: ZERO non-PM isolated ships succeeded.
      Timeline: isolation was briefly default-ON (commit `55a43797a4`), then immediately reverted to opt-in for laptops
      (`c70ffa0bfe`) because the missing-sibling + missing-venv problems made every non-PM isolated ship a guaranteed QG
      failure. The miniature-workspace fix (`6b1346ff9b`, same session) added sibling symlinks + private cached venv,
      but isolation remains opt-in (`_qm_should_isolate` returns 1 unless `ISOLATED_MODE=force`). No `--isolated` flag
      has been passed since the fix was committed (~3h ago). Bottom line: the bug WAS silently blocking every non-PM
      isolated ship during the brief default-ON window, but the blast radius was small because default-ON was reverted
      within the same session. The fix is structurally correct; the next `--isolated` non-PM ship will be the first real
      E2E test. Repo: unified-trading-pm.

## Progress Log

- 2026-08-10: doc created after reproducing twice live while shipping an unrelated deployment-service fix. Worked around
  via `--no-isolated` for that ship; this bug itself not fixed here (blast-radius risk of hand-patching the shared
  isolation logic under time pressure — deferred to a deliberate pass).
- 2026-08-10 (slot-17 worker): verified the fix is already in place via commit `6b1346ff9b` ("miniature workspace +
  symlink-stable baseline key"). The sibling-symlink loop at `scripts/quickmerge.sh:560-567` creates a complete
  miniature workspace — every sibling repo (including `unified-trading-pm`) is symlinked into `$_qm_iso_parent/`. P1
  done (code fix verified). P3 audit done: zero non-PM isolated ships succeeded because isolation was reverted to opt-in
  before any non-PM repo could attempt it. Both checkboxes flipped. Isolation remains opt-in; the next `--isolated`
  non-PM ship will be the first real E2E test of the miniature-workspace fix. **archive_exempt**: E2E verification
  pending — isolation is opt-in (default-off) and no non-PM `--isolated` ship has been attempted since the fix. The
  issue stays open as a standing reference until the first real non-PM isolated ship confirms the fix works end-to-end.
- **context-scout 2026-08-14**: populated context_scope (3 entries).
