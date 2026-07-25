---
doc_type: issue
title:
  "`.pre-commit-config.yaml`'s local hooks (plan-hygiene, fix-commit-identity, check-branch-drift, ...) resolve their
  target script via the same stale-`WORKSPACE_ROOT`-reaches-MAIN-clone pattern already diagnosed for quality-gates.sh —
  confirmed live from a `.claude/worktrees/agent-<hash>` session, not yet fixed for these hooks"
summary:
  'Live-reproduced 2026-07-25 while shipping an unrelated docs split: `git commit` from a
  `.claude/worktrees/agent-<hash>` worktree (this session''s own launch mechanism) ran the `plan-hygiene` pre-commit
  hook against the shared bare MAIN clone''s copy of `plan_reconciliation_operator_decisions_2026_07_11.md` (reporting
  the stale 3927L pre-split content and ''file not found'' for the 4 new history-part files that only existed in the
  worktree) instead of the worktree''s own staged/working content — because `WORKSPACE_ROOT` was pre-exported to the
  bare `unified-trading-system-repos` root in this session''s shell, and `.pre-commit-config.yaml`''s local-hook
  `entry:` lines (plan-hygiene, fix-commit-identity, check-branch-drift, and likely every other `bash -c
  ''...${WORKSPACE_ROOT:-...}...''` entry in that file) resolve their target script via that same env var,
  unconditionally trusting it over the calling repo''s own `git rev-parse --show-toplevel`. This is a confirmed sibling
  instance of the exact bug class already diagnosed and partially fixed (Option B, qg-common.sh only) in
  `qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md` — but that fix covers
  `quality-gates.sh`''s shared base scripts, NOT `.pre-commit-config.yaml`''s own local-hook `entry:` lines, which carry
  an independent copy of the same vulnerable `${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}`
  construction and remain unpatched. Worked around locally (session-scoped symlink + explicit WORKSPACE_ROOT override
  for the commit invocation only — no shared file touched) to ship the actual docs work; not fixed here.'
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [quality-gates, pre-commit, worktree-isolation, path-resolution, main-clone, multi-agent-safety, infra, plan-hygiene]
related:
  [
    /plans/archive/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md,
    /plans/active/issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md,
    /plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md,
    /plans/archive/issues/precommit_plan_hygiene_hook_worktree_workspace_root_misresolution_2026_07_25.md,
  ]
created: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
source:
  "side-finding while executing plan_reconciliation_operator_decisions_2026_07_11.md's line-cap split, this session
  (2026-07-25); WORKSPACE_ROOT confirmed pre-exported to /home/ubuntu/unified-trading-system-repos in this shell"
resolved_by: >-
  unified-trading-pm@2283828a7 -- fixes the plan-hygiene hook (the one that actually blocked every commit this session
  hit, since it's the only one of the three gated on files: ^(plans/|codex/)) by deriving SWEEP fresh from `git
  rev-parse --show-toplevel` unconditionally, dropping both the WORKSPACE_ROOT inheritance and the /unified-trading-pm/
  parent-join entirely -- matches this doc's own Recommended-decision Option A exactly. fix-commit-identity and
  check-branch-drift (both always_run: true, not gated on plans/codex) still carry the unpatched pattern -- left as a
  residual P3 todo below since their blast radius is meaningfully smaller (they resolve to a rarely-edited HELPER SCRIPT
  file, not a content-validation sweep reading staged doc content, so a stale MAIN copy of the script is far less likely
  to diverge from the worktree's copy than staged plan/codex content is).
locked_by:
drift_direction: advance-code
depends_on: []
---

# `.pre-commit-config.yaml` local hooks resolve via MAIN clone under a stale `WORKSPACE_ROOT` (worktree sessions)

> **🟢 ARCHIVED 2026-07-25** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (terminal_status_archival_backlog_sweep_2026_07_25.md).

## What I found

Shipping an unrelated line-cap split (see `related:`), `git commit` from this session's
`.claude/worktrees/agent-a952e9eb0d190210f` worktree failed the `plan-hygiene` pre-commit hook with output that made no
sense against my actual staged diff: it reported the target parent file at **3927 lines** (the PRE-split size — my
staged version was 370L) and "No such file or directory" for all 4 newly-created history-part files.
`printenv WORKSPACE_ROOT` confirmed it was pre-exported to `/home/ubuntu/unified-trading-system-repos` (the bare root
one level above every repo's MAIN clone) in this session's shell.

**Root cause, directly traced** (not inferred): `.pre-commit-config.yaml`'s `plan-hygiene` hook (and at least
`fix-commit-identity`, `check-branch-drift` — a `grep -c 'WORKSPACE_ROOT'` over the file finds more) resolves its target
script via
`bash -c 'HOOK="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}/unified-trading-pm/...'`. With
`WORKSPACE_ROOT` exported, `${WORKSPACE_ROOT:-...}` always wins over the fresh-derived fallback — so `HOOK` points at
`/home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/...` (the bare MAIN clone) regardless of which
worktree actually invoked `git commit`. The script that then runs reads/globs relative to **its own** `dirname "$0"`, so
every downstream check (line caps, frontmatter schema, todo format) operates on MAIN's on-disk files, not the calling
worktree's staged/working content.

This is the same bug class already diagnosed in
`qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07-24.md` (there: `quality-gates.sh` /
`qg-common.sh`, fixed via a worktree-identity guard — Option B). That fix does **not** cover `.pre-commit-config.yaml`'s
own local-hook `entry:` lines, which carry an independent, still-unpatched copy of the identical
`${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}` construction.

**Neither state works for a `.claude/worktrees/agent-<hash>` layout**: confirmed both ways — `WORKSPACE_ROOT` unset →
the fallback computes `<worktree-parent>/unified-trading-pm/...`, which does not exist for this layout (the worktree dir
is named `agent-<hash>`, not `unified-trading-pm`) → hard "sweep NOT FOUND — REFUSING to commit". `WORKSPACE_ROOT` set
to the bare root → resolves to MAIN's copy, wrong content (this session's actual failure). There is no correct value of
`WORKSPACE_ROOT` for this launch mechanism without either fixing the resolution logic or faking a
`unified-trading-pm`-named path component (a symlink) — confirmed as a working, non-destructive, session-local
mitigation (see below) but not a real fix.

**Workaround used to ship** (this session only, nothing shared touched): created a symlink
`<scratchpad>/wsroot/unified-trading-pm -> <this worktree's real path>`, exported `WORKSPACE_ROOT=<scratchpad>/wsroot`
for the single `git commit`/`git push` invocations. Verified this correctly routes the hook through the worktree's own
scripts against the worktree's own staged content (re-ran `run_hygiene_sweep.sh --precommit` directly first to confirm
before trusting it inside the real commit). No `.pre-commit-config.yaml`, hook script, or shared file was modified.

## Merged in: 3 more independent confirmations (from a near-duplicate issue doc filed in parallel, merged 2026-07-25)

A sibling agent working a different part of this same session's follow-up work independently filed
`precommit_plan_hygiene_hook_worktree_workspace_root_misresolution_2026_07_25.md` (now superseded by this doc) after 3
OTHER agents hit the identical symptom on 3 OTHER files, in 3 OTHER `.claude/worktrees/agent-<hash>` worktrees, before
this doc's own directly-confirmed root cause (the exported `WORKSPACE_ROOT`) was known — i.e. 4 independent
worktree-isolated agents hit this in the same session, on different files, at different times. Two used a
`WORKSPACE_ROOT`-override symlink workaround (same mitigation as this doc's own "Workaround used to ship" section); one
used `--no-verify` after manually re-running `check_frontmatter_schema.py`/`check_line_caps.sh`/
`check_reference_paths.py` clean from its own worktree first — **flagging that transparently**: CLAUDE.md's git safety
protocol says hooks are never skipped without explicit user request, and this agent made an autonomous judgment call to
bypass a hook it had independently diagnosed as broken rather than working around the resolution (as the other 3 did).
The practical risk was mitigated by the manual compensating checks, but the deviation itself should stay visible rather
than being silently absorbed into a "problem solved" narrative.

## Recommended decision

Same as the sibling doc's Option A, applied to `.pre-commit-config.yaml` specifically: every local-hook `entry:` using
`${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}` should derive fresh from
`git rev-parse --show-toplevel` unconditionally (never honor an inherited `WORKSPACE_ROOT` for this specific
computation), or add the same fail-loud worktree-identity assertion used in `qg-common.sh`. Given this fires on every
single `git commit` touching `plans/`/`codex/` (not just QG runs), and this session's launch mechanism
(`.claude/worktrees/agent-<hash>`, not the Path-B slot-clone model the sibling doc's fix was verified against) has NO
working `WORKSPACE_ROOT` value at all, this is plausibly wider-blast-radius than the already-fixed QG-only instance.

## Todos

- [ ] [DIAG] P1. Confirm whether any `.claude/worktrees/agent-<hash>` session currently has a persistently-exported
      `WORKSPACE_ROOT` (check the launcher/bootstrap for this session type — was it set intentionally for a different,
      slot-based convention and just doesn't apply here, or is it leaking from a parent shell/profile?). Bumped to P1
      given 4 independent agents hit this in a single session — this blocks/corrupts precommit validation for
      essentially every Agent-tool `isolation: worktree` session doing plan/codex commits, not a rare edge case.
- [x] [CODE] P1. ✅ Apply the same fix pattern as
      `qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`'s todo 2 to the
      `plan-hygiene` hook's `entry:` — `unified-trading-pm@2283828a7`. Fixed by a sub-agent (`aea58a35150f61601`) that
      independently hit the same bug during this session's line-cap split follow-up work; shipped directly since the fix
      doesn't touch `plans/`/`codex/` and isn't gated by the hook it fixes.
- [ ] [CODE] P3. **Residual**: `fix-commit-identity` and `check-branch-drift` (`.pre-commit-config.yaml` lines ~23-38)
      still carry the identical unpatched `${WORKSPACE_ROOT:-...}` pattern. Lower priority than the plan-hygiene fix was
      — both are `always_run: true` (every commit, not gated on plans/codex) but resolve to a rarely-edited HELPER
      SCRIPT file rather than a content-validation sweep reading staged doc content, so the practical divergence risk
      (stale MAIN copy vs worktree copy) is much smaller. Apply the identical fresh `git rev-parse --show-toplevel`
      derivation for completeness/consistency.
