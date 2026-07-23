---
doc_type: issue
title: RepoHealthWatcher signals "GREEN again" while a fresh local quality-gates.sh still fails deterministically
summary: >-
  Twice in one session, a repo-blocker's watcher_green resolution message ("repo is GREEN again — resume") arrived while
  a fresh git pull --rebase to the exact same origin/live-defi-rollout tip + a full local quality-gates.sh run still
  failed the SAME pre-existing issue deterministically: unified-trading-pm (RB-221f6114, archetype-count 60 vs 59 —
  issue doc capability_verdict_matrix_archetype_count_60_vs_59_regression_2026_07_21.md, still status:open) and
  unified-trading-system-ui (RB-96829ed8, lib/chart-theme.ts still absent, slot-5's local fix not yet pushed). Both
  false positives were independently corroborated: slot 2 hit the SAME already-open PM blocker moments after my "GREEN
  again" ping (RB-d34c1d03), and I directly confirmed the UI file is still missing on origin after a fresh fetch. Acting
  on the ping without re-verifying would have shipped against a red tree.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, repo-health-watcher, false-positive, coordination, quality-gates]
related: []
created: "2026-07-21"
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
parent_epic: agent_operating_framework_master
source: [unified_trading_system_ui_codex_violations_far_exceed_estimate-004]
resolved_by: agent-orchestrator@5bf0ccf
locked_by:
depends_on: []
---

## What I found

`RepoHealthWatcher`'s green-detection appears to check something other than a genuine full local `quality-gates.sh` pass
(possibly a narrower/different CI signal, or a stale/cached read) — twice this session it announced a repo green while
the exact same pre-existing failure reproduced deterministically on a fresh pull to the same tip.

## Why it matters

A worker that trusts the ping without re-verifying would ship a commit and ask quickmerge to stamp a sentinel against a
red tree, or waste a cycle discovering the ping was wrong. Multiple waiters (slot 2, slot 4, slot 6, slot 9) are piling
up on the same 2 blockers, so a false "clear" signal fans out.

## Recommended decision

Whoever owns `agent-orchestrator`'s `RepoHealthWatcher` should confirm what signal it polls (full local QG vs a narrower
CI check) and, if it's not re-running the actual `quality-gates.sh` a waiter would run, either switch it to that or
document clearly that "green" is a weaker signal a waiter must still re-verify before shipping.

## Todos

- [x] [INFRA] P2. Audit `RepoHealthWatcher`'s green-detection source (agent-orchestrator repo) against what
      `quality-gates.sh` actually checks; align or clearly document the gap. (repo: agent-orchestrator) — ✅
      `agent-orchestrator@5bf0ccf`. **Root cause confirmed**: `RepoHealthWatcher.tick_once()` reads
      `server.ci_status.ci_status()` → `ci_reconcile.repo_ldr_qg_conclusion()`, which is the latest _completed_
      `quality-gates-v2` run's conclusion on `live-defi-rollout` — NOT a fresh re-run of `quality-gates.sh`. Confirmed
      via the repo's own `.github/workflows/quality-gates-v2.yml` trigger surface (`push:[main]` + PRs to
      `[main, staging]` + `workflow_dispatch` only — **no** `push:[live-defi-rollout]` trigger), matching
      `ci_reconcile.py`'s own "Stale-failure gate" comment: "LDR never runs server QG on push... the runs on
      live-defi-rollout are hourly workflow_dispatch runs." So the latest completed run can describe a commit HEAD has
      since moved past, **in either direction**: `ci_reconcile.py` already shipped a fix for the false-RED direction
      same-day (`failing_run_is_current()` requires the failing run's `head_sha` to equal current branch HEAD before
      escalating) — but `RepoHealthWatcher`'s green path had no equivalent gate, so a hold-over SUCCESS from before a
      since-landed regression would still read "green" and resolve blockers against a red-but-untested HEAD. This is
      exactly the false-positive mechanism this issue reports. **Fix (not just documentation)**:
      `RepoHealthWatcher.tick_once()` now reuses `ci_reconcile.failing_run_is_current()` (conclusion-agnostic despite
      its name — it only checks `run.head_sha == branch HEAD`) to gate every green verdict the same way it already gates
      red verdicts: an unverifiable or stale run leaves the blocker OPEN (fail-safe), mirroring the existing
      conservative philosophy ("fail-open: blocker survives a poll error"). Updated the module docstring to correct the
      prior overclaim ("this poll is the guarantee") — it's now accurate but still notes `quality-gates-v2` green (even
      with a fresh head match) is a WEAKER guarantee than a waiter's own local `quality-gates.sh` run (different
      runner/baseline state), so a waiter should still spot-check before shipping a red-adjacent change. Added
      `test_watcher_stale_green_run_keeps_blocker_open` + patched the 2 existing green-path tests to inject the new
      dependency. Full `quality-gates.sh` green (ruff lint/format clean, basedpyright 0 errors, 1575 tests passed —
      `.venv` didn't exist yet in this worktree, built via `uv sync --extra dev` first).

## Codex SSOTs

`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`.
