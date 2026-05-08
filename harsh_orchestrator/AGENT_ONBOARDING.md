---
title: Agent Onboarding — read first if you are a spawned tab agent
type: onboarding-spec
status: active
created: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Agent Onboarding

> **You are a spawned tab agent.** Harsh just opened a fresh Claude Code tab and told you _"work on Tab N tasks"_.
> This doc is your boot context — read it once before doing anything else, then read everything in the
> "Reading order" below in sequence. Total bootstrap time: ~5 min.

## Your role in 3 sentences

You are **Tab N**, a scoped implementer spawned by Harsh's main orchestrator agent (Tab 1, a separate Claude
Code session on the SAME PC, sharing the SAME `.git/` + working tree as you). You execute one task end-to-end
against your assigned plan-of-record, ship it, and go quiet. You do NOT take on adjacent work, spawn sub-agents
of your own, push speculatively, or message Harsh directly — Tab 1 is your conversational dispatcher.

## Reading order (do this first, in sequence)

1. **THIS file** — confirm your role.
2. **`harsh_orchestrator/LEDGER.md`** — find your tab entry by tab number. Its spawn-prompt block is your full task brief
   (repos owned, behavioural contract, collision boundaries, done-definition).
3. **`cursor-configs/CLAUDE.md` § "Daily Work-Split Process (Ikenna ↔ Harsh, AI-paralleled)"** — full workspace
   spec for the Model A / Model B work-split, shared working tree, conditional push, plan-of-record + Q&A bus,
   ping ledger, polling cadence, sub-agent fan-out. **All the orchestration rules you need live there.** This
   onboarding doc is just the boot pointer.
4. **`cursor-configs/CLAUDE.md`** (the rest) — workspace coding standards: uv not pip, basedpyright not pyright,
   no `os.getenv()`, "Findings Triage Discipline (HARD RULE)", "Commit + Push + Flip Plan Checkboxes (HARD RULE)",
   "Two teammates × multiple parallel agents", per-asset-group shard-key matrix.
5. **`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`** — sub-agent inheritance rules (only relevant if YOU spawn
   `Task` sub-agents from inside your tab; for most tabs this is informational).
6. **Your plan-of-record** — the specific plan named in your tab entry (e.g.
   `cefi_master_2026_05_07.md` for `cefi-babysit-tab`). This is where your todos live + where you flip
   checkboxes + where you write `## Open questions` for blockers.

## The only 4 things you must internalise (everything else is in CLAUDE.md)

### 1. Communication bus

| What | Where | When |
|---|---|---|
| **Boot ack** | `harsh_orchestrator/_agent_pings.md` | At session start (one-line `STARTED Tab N` ping) |
| **Blocker / question for main** | Your plan-of-record's `## Open questions` § (status `🟡 BLOCKED`) + ping in `harsh_orchestrator/_agent_pings.md` | When you hit ambiguity / decision / push-race |
| **Done announcement** | `## DONE-<YYYY-MM-DD>` block at bottom of plan-of-record + ping in `harsh_orchestrator/_agent_pings.md` | When done-definition met |
| **Side findings** (case-1 to case-5) | Per Findings Triage Discipline in CLAUDE.md | Throughout |
| **Direct chat to Harsh** | NEVER — main is your dispatcher | Exception: case-5 BIG findings only |

Q&A format on plan-of-record:

```markdown
### Q1 — [your-agent-tag, YYYY-MM-DD HH:MM] — short title
**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what was tried, options considered>

#### A1 — [main, YYYY-MM-DD HH:MM]
**Status**: ✅ RESOLVED

<answer + reasoning + commit-sha of anything shipped meanwhile>
```

Main agent polls `_agent_pings.md` ~1 min cadence (faster while operator's active). Your A1 typically
lands within 1-5 min for technical Qs; longer if the Q escalates to operator.

### 2. Push discipline (the multi-agent safety valve)

Per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE — **commit per shippable unit always**. Then
before pushing:

```bash
git fetch origin <branch>
git log --oneline <branch>..origin/<branch>   # incoming commits, if any
```

- **Zero incoming → push freely.** Default path; no operator approval needed.
- **Any incoming → STOP, do NOT push.** Write a `🟡 BLOCKED` Q in your plan-of-record listing your local
  commits + the incoming ones. Ping the ledger. Continue with what you CAN do. Main + operator decide
  rebase / merge / cherry-pick.

### 3. Pre-commit check (catches the shared-working-tree foot-gun)

Before EVERY commit, in ANY repo:

```bash
git status                 # full picture: modified, staged, untracked
git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```

If anything in the staged set or working tree isn't yours, surgically un-stage (`git restore --staged
<file>`) or stash (`git stash --keep-index`) before committing. Use `git add -p` for your hunks if any
shared file has foreign edits. **Never `git add -A` / `git add .` / `git add <whole-shared-file>`.**

Reference incidents: PM@`961980db` / `611b9501` / `34075d84` (all from concurrent-agent overlap).

### 4. Plan-of-record curation duties

As you ship work:

- **Flip checkboxes per shippable unit.** `- [ ]` → `- [x]` with `<repo>@<sha>` evidence appended. In the same
  logical unit as the code commit, not at end of session.
- **Append progress notes** to relevant plan body sections if you find something worth recording (e.g.
  per-iteration sweep entries, per-bug investigation notes).
- **Document findings per Findings Triage Discipline** (case-1-to-5 routing per CLAUDE.md).
- **Final**: when done-definition met, append `## DONE-<YYYY-MM-DD>` block at bottom of plan body listing
  every code + plan-flip commit sha. Then go quiet — don't pick up new work autonomously.

## Boot ack template (paste this into `_agent_pings.md` after reading)

```text
[YYYY-MM-DD HH:MM UTC] <your-agent-tag> — STARTED Tab N (<plan-of-record-path>)
```

Main agent will see it on next 1-min poll, ack with a short note in your plan doc's `## Open questions` if
anything to flag, otherwise stays silent. Your STARTED ping is removed automatically once main confirms
clean boot.

## Differences from CLAUDE.md HARD RULE you should be aware of

The Daily Work-Split Process in CLAUDE.md is the SSOT for orchestration mechanics. This onboarding doc is
just the pointer + boot ack. If anything in this doc contradicts CLAUDE.md, **CLAUDE.md wins** — file an
issue doc flagging the drift.

## Useful cross-references

- **Workspace state right now**: [`harsh_orchestrator/LEDGER.md`](LEDGER.md) — today's tab registry, in-flight
  status, recent done, open questions across plans.
- **Active pings**: [`harsh_orchestrator/_agent_pings.md`](_agent_pings.md) — short doorbell-style log; one line per
  active blocker.
- **All workspace rules**: [`cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md).
- **Sub-agent inheritance**: [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../cursor-configs/SUB_AGENT_MANDATORY_RULES.md).
