---
doc_type: issue
title:
  "Mac slot 0 (un-slotted base checkout) has 3 genuinely-stuck dirty files — needs an operator commit-vs-discard call"
summary:
  "The AO Git-Health dashboard's 'slot 0' entry on the Mac host is the un-slotted base checkout
  (${WORKSPACE_ROOT}/<repo>/, one level above .tabs/ — NOT .tabs/0, which doesn't exist), IS cron-swept by
  slot-cron-ff-pull.sh --all-slots same as any numbered slot, and drifts because it carries 3 genuinely-stuck
  uncommitted files the FF-cron's narrow auto-clean allowlist won't touch, so it perpetually [skip:dirty]s: a
  staged-but-never-committed .github/workflows/notify-slack.yml (e2e-testing repo), a modified uv.lock
  (execution-service repo), and a modified quality-gates-v2.yml (system-integration-tests repo). Separately (cosmetic,
  not blocking FF since untracked-only): every repo root in the base checkout carries a stray untracked self-referential
  symlink (<repo>/<repo> -> ../../<repo>), created uniformly across all repos at 2026-08-09 15:28 — some
  workspace-tooling side effect, inflating the dashboard's dirty-file count but not causing drift. Found during a
  2026-08-11 fleet git-health investigation triggered by an operator report of persistent git: N warn badges on killed
  slots (a separate, already-fixed bug — see resolved_by note below); this specific finding was never resolved and never
  previously tracked."
status: open
nature: notes
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, git-health, base-checkout, dirty-state, operator-decision]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch19_2026_08_10.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh,
    scripts/workspace/link-claude-skills.sh,
  ]
created: 2026-08-11
last_updated: 2026-08-20
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  fleet git-health investigation, 2026-08-11 session (killed-slots git:N-warn incident, resolved separately via
  agent-orchestrator@a4531e1293)
archive_exempt:
---

# Mac slot 0 base checkout — 3 stuck dirty files + cosmetic stray symlinks

## What I found

`git status` on `${WORKSPACE_ROOT}/<repo>/` (one level above `.tabs/`, the un-slotted reference clone every numbered
slot's `git clone --reference` shares) reproduces the AO dashboard's "slot 0" dirty/behind figures exactly. It IS walked
by `slot-cron-ff-pull.sh --all-slots` every 5 minutes same as any numbered slot — the earlier hypothesis that nothing
crons it was wrong. It stays dirty forever because 3 specific files don't match the FF-cron's narrow auto-clean
allowlist:

- `e2e-testing`: a staged-but-never-committed `.github/workflows/notify-slack.yml`
- `execution-service`: a modified `uv.lock`
- `system-integration-tests`: a modified `quality-gates-v2.yml`

Separately, every repo root in the base checkout has a stray untracked self-referential symlink
(`<repo>/<repo> -> ../../<repo>`), all stamped `2026-08-09 15:28` — some workspace-tooling side effect (not identified),
inflating the "26 dirty" count the dashboard showed but not itself causing FF-cron drift (untracked files don't block a
fast-forward).

## What's still open

- [ ] [OPERATOR] P3. **Decide commit-vs-discard for the 3 stuck files** in the Mac base checkout
      (`e2e-testing/.github/workflows/notify-slack.yml`, `execution-service/uv.lock`,
      `system-integration-tests/.github/workflows/quality-gates-v2.yml`) — each needs a human look since none are
      obviously safe to auto-resolve (a staged-but-uncommitted workflow file, a lockfile drift, a gate-config edit).
      Once resolved, slot 0 should read clean on the next FF-cron tick. Repo: unified-trading-pm (base checkout is
      workspace-level, not repo-specific).
- [x] ✅ [SCRIPT] P3. **Identify + fix the source of the stray `<repo>/<repo>` self-referential symlinks** (2026-08-09
      15:28, uniform across every repo in the base checkout) and clean up the existing ones — cosmetic (doesn't block
      FF), but worth tracing to stop it recurring. Repo: unified-trading-pm. **SHIPPED —
      `unified-trading-pm@820984d53d`** (repo-level self-referential-link heal added to `link-claude-skills.sh`, the
      canonical self-healer every host runs on QG/setup/pm-pull; no committed generator found via `git log --all -S`, so
      healing-at-the-self-healer is the durable fix). Reconciled 2026-08-14 per
      `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` todo 1 (evidence from
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`).

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (2 entries).
- **context-scout 2026-08-17**: re-verified context_scope (2 entries), unchanged.
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:232a39505df4eaf3]: KEEP-NA, valid — sole open todo asks the operator to decide commit-vs-discard for 3 specific uncommitted files across 3 repos — genuine judgment about human intent behind pre-existing edits.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
