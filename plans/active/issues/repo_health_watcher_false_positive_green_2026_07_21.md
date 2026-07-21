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
status: open
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
resolved_by:
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

- [ ] [INFRA] P2. Audit `RepoHealthWatcher`'s green-detection source (agent-orchestrator repo) against what
      `quality-gates.sh` actually checks; align or clearly document the gap. (repo: agent-orchestrator)

## Codex SSOTs

`codex/12-agent-workflow/async-wait-and-poll-discipline.md`.
