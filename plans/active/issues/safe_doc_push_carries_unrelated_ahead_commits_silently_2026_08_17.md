---
doc_type: issue
title:
  safe-doc-push.sh silently pushes ANY commits sitting ahead of origin on the caller's branch tip, not just the
  named doc file — a worker with unrelated QG-blocked code commits queued locally can accidentally ship them
  through the pure-docs fast path, bypassing quickmerge's quality-gates.sh + --agent sentinel entirely
summary: >-
  Live-hit 2026-08-17: while genuinely blocked shipping a code change (a pre-existing, unrelated repo-wide
  quality-gates.sh failure), used safe-doc-push.sh — correctly, per CLAUDE.md's own "pure doc/plan-flip ->
  safe-doc-push.sh" guidance — to push an issue doc about that exact blocker. safe-doc-push.sh's own
  `pull --rebase --autostash` + `git push` pushes the CURRENT BRANCH TIP, which included 2 unrelated local code
  commits that had never passed quality-gates.sh (queued behind the blocker). Those commits reached
  origin/live-defi-rollout as a side effect, without ever going through quickmerge's QG-verified `--agent`
  sentinel path — a real, if unintentional, violation of the "CODE reaches the integration branch ONLY via
  quickmerge" HARD RULE. The docs themselves were fine; the risk is generic to ANY worker in the same
  shape (code blocked + needs to push an unrelated doc).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, quickmerge, safe-doc-push, ship-discipline, repo-blocker, process-gap]
related:
  [
    /plans/active/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md,
    /plans/archive/issues/unified_trading_pm_empty_string_fallback_baseline_stale_2026_08_17.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-17
author: backend_engineer (slot-1, interactive)
priority: P2
parent_epic: infrastructure_master
source: >-
  Discovered live while shipping the detect_template_drift.py wiring follow-up
  (rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md) — see that doc's Progress Log for the
  full incident narrative.
assigned_vm: planning
execution_scope: orchestrator-agent
resolved_by:
locked_by:
context_scope: [scripts/dev/safe-doc-push.sh, /codex/05-infrastructure/per-tab-worktrees.md]
depends_on: []
drift_direction: advance-code
---

# safe-doc-push.sh silently carries unrelated ahead-of-origin commits

## What I found

`safe-doc-push.sh` is the CLAUDE.md-sanctioned fast path for "pure doc/plan-flip" pushes — it stages ONLY the
caller-named files, but its final `git push` sends the CURRENT BRANCH TIP, not a synthetic commit containing
just the named files. If the caller's local branch has OTHER, unrelated commits sitting ahead of origin
(e.g. real code commits that were about to ship via quickmerge but got stuck behind a repo-wide QG-red), those
commits ride along and land on `origin/live-defi-rollout` too — WITHOUT ever passing through
`quality-gates.sh` (safe-doc-push never runs it, by design — "skipping quickmerge/quality-gates.sh entirely
for speed") or quickmerge's `--agent` sentinel check.

Live sequence that hit this: 2 code commits (the `detect_template_drift.py` systemd-wiring follow-up) were
sitting locally, queued because Pass-1 `quality-gates.sh` failed on a PRE-EXISTING, unrelated repo-wide ratchet
(`unified_trading_pm_empty_string_fallback_baseline_stale_2026_08_17.md`). Filed an issue doc about that exact
blocker and pushed it via `safe-doc-push.sh` (the correct tool for a pure-docs change) — its reconciliation
pushed the doc commit AND the 2 queued code commits underneath it. Verified via `git merge-base --is-ancestor`
that the code landed on origin; the code itself was otherwise clean (ruff/format/gitleaks/py_compile all
passed at commit time, and the only failing gate was the unrelated pre-existing one) — but the SHIP PATH
itself skipped the quickmerge gate, which is the actual HARD RULE violation, independent of whether this
particular payload happened to be safe.

## Why it matters

This is not a one-off — it's a structural gap any worker can hit in the SAME shape: (1) code commits blocked
behind a real or perceived QG-red, (2) the worker needs to push an unrelated PURE-DOCS change (very often —
as here — the exact issue doc ABOUT that same blocker), (3) `safe-doc-push.sh` is the CLAUDE.md-mandated tool
for that docs push, and (4) it has no awareness of, or guard against, unrelated non-doc commits already
sitting on the branch tip. The `Commit + Push + Flip` HARD RULE and the "CODE reaches the integration branch
ONLY via quickmerge" HARD RULE both assume ship paths are mutually exclusive per-commit; this shows they can
silently compose in a way neither rule anticipated.

## Recommended decision

Give `safe-doc-push.sh` a guard: before pushing, check whether HEAD has any commit ahead of origin that is
NOT purely the just-created doc commit (i.e., `git log origin/<branch>..HEAD~1` is non-empty) and, if so,
either (a) refuse and tell the caller to resolve the ahead commits first (safest — but could false-positive
on a caller who has ALREADY legitimately QG-passed code queued for a completely independent reason and
happens to also need a docs push), or (b) warn loudly and require an explicit override flag naming what's
being carried along. Option (a) is the safer default given the HARD RULE this protects; a worker with
genuinely QG-green code queued should be shipping it via quickmerge anyway, not leaving it to ride along on a
docs push.

## Todos

- [ ] [SCRIPT] P2. Add a pre-push guard to `scripts/dev/safe-doc-push.sh`: before the final push, check for any
      local commit ahead of origin that isn't the doc commit(s) this invocation just created; refuse (or warn
      + require an explicit `--i-know-this-carries-other-commits` style override) rather than silently pushing
      them. Repo: unified-trading-pm.
- [ ] [DOC] P3. Add a one-line warning to `safe-doc-push.sh`'s own header docstring about this exact risk, so a
      future reader auditing the script (not just a QG-checker) sees it without needing this issue doc. Repo:
      unified-trading-pm.

## Progress Log

- **2026-08-17 (slot-1, interactive)**: filed after the live incident described above. Did not attempt the
  fix myself in this session (script-behavior-change to a widely-used shared ship tool warrants its own
  focused session + testing, not a rushed addition while already mid-way through an unrelated task).
