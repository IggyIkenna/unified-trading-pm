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

- [x] ✅ [BACKEND] P3. Locate the git-status-nudge ahead-count computation — **found in the wrong repo than
      guessed**: not `agent-orchestrator`, but `unified-trading-pm/scripts/dev/slot-git-status-report.sh`, the
      actual data source both the Slack-paging alert and the in-session boot/heartbeat nudge read from.
- [x] ✅ [BACKEND] P3. Fix it to compare against each repo's own tracked branch — **already shipped 6 days
      BEFORE this doc was even filed**: `unified-trading-pm@b92d9ba52fe` ("fix: unified-trading-ci false
      git-health ahead warning", 2026-08-11), `scripts/dev/slot-git-status-report.sh:312-326` — special-cases
      `unified-trading-ci` → compare against `main`. Live-verified still present. Both todos flipped by
      plan_reconciler 2026-08-19 after independently confirming the commit + live code.
- [ ] [BACKEND] P2. **NEW (2026-08-19) — a separate, still-open false-positive mechanism, distinct from the
      2 todos above.** This run's own boot heartbeat received a false-positive `unified-trading-pm: AHEAD=1
      unpushed` nudge that this doc's diagnosed mechanism does NOT explain — PM carries no `integration_branch`
      override (confirmed in `workspace-manifest.json`), so comparing it against `live-defi-rollout` is
      correct; the fix above would not have prevented it. Real gap:
      `agent-orchestrator/server/worker_liveness/_git_alerts.py:532-534` (`maybe_nudge_on_red_repos`) fires on
      the "ahead" branch with **zero age/sustain threshold** — independently confirmed by direct code read:
      the sibling `dirty` branch 3 lines later gates on `age_s > 3600`, and the sibling Slack-paging function
      `maybe_alert_git_staleness` enforces a 90-min sustain (`GIT_RED_SUSTAIN_S`) for its own "ahead" case, but
      `maybe_nudge_on_red_repos`'s "ahead" branch has no equivalent gate at all — only a 30-min RE-nudge
      throttle exists, which doesn't stop the FIRST fire. A momentary ahead=1 reading (e.g. a commit landing
      slightly before its push in the normal two-pass ship flow) can fire this nudge on the very next
      ~5-min-cadence tick. Fix: add an age/sustain threshold to the "ahead" branch of `maybe_nudge_on_red_repos`,
      mirroring its own sibling branches. Repo: agent-orchestrator.

## Progress Log

- **2026-08-17 (slot-1, interactive)**: filed after investigating + acking 3 stale nudge messages
  (message_ids 9106/9165/9201) this session. Did not touch unified-trading-ci itself — nothing there needs
  fixing, only the nudge's own comparison logic.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **plan_reconciler 2026-08-19 (dispatch agt-f212cb, ci tranche)**: flipped both original todos with HARD
  evidence (fix shipped 2026-08-11 in a different repo than guessed). Filed a NEW todo for a genuinely separate,
  still-open false-positive mechanism discovered via this run's own live boot-heartbeat occurrence (slot 1,
  2026-08-19) — see todo 3. `context_scope` needs a follow-up add of `scripts/dev/slot-git-status-report.sh`
  (the actual fix site for todos 1-2) — not yet added this pass, left for the next context-scout run.
