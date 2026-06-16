---
scope: [engineer, admin]
---

# Local Slot Host = VM Slot Host — Symmetric Worker Model (HARD RULE)

> **CLAUDE.md anchor**: "Local slot host = VM slot host — symmetric worker model (HARD RULE codified 2026-05-20)".
>
> Codified 2026-05-20 per operator directive: "aren't we still pinging locally to the same server the UI and API sees so
> that locally we can act like we are just another slot in the pipeline — that's what Harsh is doing or supposed to do,
> no? Should be fixed, documented, tested, in CLAUDE.md."

## The Rule

**Every host that owns slot worktrees follows the same contract**, regardless of whether it's the VM, the operator's
laptop, or Harsh's laptop.

## Host Behaviour Matrix

| Behavior                                  | VM  | Operator laptop | Harsh laptop       |
| ----------------------------------------- | --- | --------------- | ------------------ |
| `slot-cron-ff-pull.sh` every 5 min        | ✓   | ✓               | ✓ (post-migration) |
| `slot-git-status-report.sh` every 5 min   | ✓   | ✓               | ✓ (post-migration) |
| Per-slot worktree on `tab/<operator>/<N>` | ✓   | ✓               | ✓                  |
| Commit + Push + Flip same-turn HARD RULE  | ✓   | ✓               | ✓                  |
| Spawn workers via `/api/slots/<N>/spawn`  | ✓   | optional        | optional           |
| Interactive Claude Code chat as a slot    | ✓   | ✓               | ✓                  |

## Interactive Sessions Count as Slots

**Operator's interactive session counts as a slot.** When the operator works in `.tabs/<N>/<repo>/` from a Cursor /
Claude Code window, they ARE slot N for the purposes of:

- The slot's branch convention (`tab/<operator>/<N>`)
- The Commit + Push + Flip plan checkbox HARD RULE (no 9-hour-old uncommitted WIP; ship per shippable unit)
- The git-status reporter (their dirty state shows on the dashboard alongside spawned workers)
- The FF-pull cron (their worktree gets FF-pulled the same as a worker's)

## Orchestrator Symmetry

**The orchestrator does NOT differentiate** between "interactive operator session" and "spawned tmux worker" for these
purposes. Both are slots. Both show on the Fleet tab. Both follow the same rules. The only operational difference is
whether the slot is `paused` (interactive — operator controls it) or `working` (orchestrator dispatches tasks to it).

## Verification (mandatory on every host setup)

```bash
bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh
```

Returns exit 0 if both crons are installed + last run within 10 min + last report posted to backend OK.

## Why This Matters

A local 9-hour-old dirty WIP on the operator's own slot is the same anti-pattern as a worker sitting on uncommitted code
for 9 hours. Both violate Commit+Push+Flip. Both block downstream FF-pulls. Both create the "stale code" problem the
whole worktree model exists to prevent. The orchestrator can't tell the difference, which is the point: same model, same
rules, same accountability.

## Setup and Scripts

### FF-pull cron

`unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh` — works on macOS + Linux

### Drift reporter

`unified-trading-pm/scripts/dev/slot-git-status-report.sh` — cross-platform

The drift reporter runs every 5 minutes and posts repo state to `/api/slots/<N>/git-status`. In addition to standard
dirty/ahead/behind detection, it **also detects unpushed plan files**:

- Any dirty or untracked path matching `plans/active/*.md` or `plans/active/issues/*.md` in a `unified-trading-pm`
  worktree is collected into an `unpushed_plans` field in the JSON payload.
- The `WorkerLivenessKicker` reads this field on every liveness tick and fires a Slack alert **immediately** (no
  15-minute threshold) when any plan file is unpushed. Throttled to 1 alert per slot per 30 min.
- Alert text: `:warning: Slot N has unpushed plan(s): X.md, Y.md`

**Rule**: a dirty plan file is always operator-actionable. The 15-minute staleness grace that applies to code repos does
not apply to plan files — a plan edit left unpushed is invisible to every other VM and breaks the regen loop (see
`codex/12-agent-workflow/canonical-plan-flow.md`).

### Verification

`unified-trading-pm/scripts/verify-slot-host-symmetry.sh` — test new hosts

## SSOTs

- `codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md` — Harsh's host onboarding recipe
- `agent-orchestrator/agents/worker.md` — the slot-as-worker contract (applies to interactive sessions too)

## Composes With

- `codex/12-agent-workflow/commit-push-flip-rule.md` — the rule that applies to ALL slots
- `codex/05-infrastructure/per-tab-worktrees.md` — the worktree model this builds on
- `codex/12-agent-workflow/daily-work-split-process.md` — orchestrator mechanics
