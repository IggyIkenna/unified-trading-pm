---
doc_type: issue
title:
  The "GIT STATUS RED" auto-nudge (heartbeat/boot messages) false-positives on unified-trading-ci by comparing
  its ahead-count against live-defi-rollout unconditionally, when that repo legitimately tracks main directly
summary: >-
  Boot/heartbeat responses carry a repeating "🟥 GIT STATUS RED... push to live-defi-rollout" nudge for
  unified-trading-ci claiming AHEAD=3 (later independently measured as ahead=1). Investigated: the repo's
  local HEAD is checked out on `main`, exactly matching `origin/main` (0 ahead/behind via `git status -b`) —
  it is a GATE-INFRA repo (CI/workflow tooling) that ships to `main` directly per the CLAUDE.md carve-out, not
  the live-defi-rollout LDR flow every other repo uses. The nudge's own ahead-count appears to be computed by
  comparing every repo's HEAD against `origin/live-defi-rollout` unconditionally, which is the WRONG upstream
  for this specific repo — there is nothing to push; the "ahead" content (an already-landed commit by a
  different slot, `ikennaigboaka [slot-2·laptop]`) is already on `origin/main`.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ci, agent-orchestrator, git-status-nudge, false-positive, unified-trading-ci]
related: [/plans/active/ci_consolidated_closeout_2026_07_25.md]
created: 2026-08-17
author: ui_developer (slot-1, interactive)
priority: P3
parent_epic: security_and_cross_cutting_master
source: >-
  Investigated after receiving the same nudge 3x in one boot/heartbeat cycle
  (message_ids 9106/9165/9201) on slot 1, 2026-08-17. Acked the messages as stale after confirming
  unified-trading-ci's tracked branch (main) was already in sync with its own origin.
assigned_vm: planning
execution_scope: orchestrator-agent
resolved_by:
locked_by:
context_scope:
  [
    agent-orchestrator/server/worker_liveness/_git_alerts.py,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
depends_on: []
drift_direction: advance-code
---

# GIT STATUS RED nudge false-positives on unified-trading-ci (wrong-branch comparison)

## What I found

`unified-trading-ci`'s local clone tracks `main` directly (confirmed: `git status --porcelain -b` reports
`## main...origin/main` with no ahead/behind annotation — i.e. 0/0). A `git log --oneline
origin/live-defi-rollout..HEAD` on that same clone DOES show 1 commit not reachable from
`live-defi-rollout` — but that's expected and harmless: this repo is CI/workflow tooling that ships to
`main` directly per the CLAUDE.md GATE-INFRA carve-out, not the normal LDR flow. The nudge appears to compute
its "AHEAD=N unpushed — push to live-defi-rollout" claim the same way (comparing against
`origin/live-defi-rollout` for every repo unconditionally), producing a false positive for this specific
repo. The reported count itself also drifted between two readings in the same session (3, then independently
measured 1) — consistent with a comparison that's measuring the wrong, moving target rather than a stable
real fact.

## Why it matters

Low severity (this repo is a narrow, known carve-out — likely the only repo in the fleet with this exact
shape), but every slot that has `unified-trading-ci` checked out will keep receiving this false-positive
nudge on every boot/heartbeat, training agents to either waste time re-investigating it each time or,
worse, to reflexively "fix" it by force-pushing/rebasing a repo that is actually fine and doesn't use the LDR
flow at all.

## Recommended decision

Whoever owns the git-status-nudge computation (likely in `agent-orchestrator`) should special-case
`unified-trading-ci` (or more generally, any repo whose CLAUDE.md-documented promotion model isn't
`ldr_main`/doesn't use `live-defi-rollout` as its integration branch) to compare against its OWN tracked
upstream branch rather than a hardcoded `live-defi-rollout` comparison.

## Todos

- [ ] [BACKEND] P3. Locate the git-status-nudge ahead-count computation (likely `agent-orchestrator`,
      whatever emits the "🟥 GIT STATUS RED" boot/heartbeat message) and confirm it hardcodes
      `origin/live-defi-rollout` as the comparison target for every repo. Repo: agent-orchestrator.
- [ ] [BACKEND] P3. Fix it to compare against each repo's own tracked branch (or explicitly skip
      `unified-trading-ci` / any repo not on the `ldr_main` promotion model) instead of a hardcoded
      `live-defi-rollout` target. Repo: agent-orchestrator.

## Progress Log

- **2026-08-17 (slot-1, interactive)**: filed after investigating + acking 3 stale nudge messages
  (message_ids 9106/9165/9201) this session. Did not touch unified-trading-ci itself — nothing there needs
  fixing, only the nudge's own comparison logic.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
