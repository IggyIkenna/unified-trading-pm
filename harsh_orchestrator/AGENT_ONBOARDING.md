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

## 🚨 HARD RULE — git pull / rebase / push require operator authorization (codified 2026-05-08 PM)

**Effective immediately for every spawned tab agent.** You must NOT run any of the following git operations
unless Harsh explicitly asks you via [`_agent_pings.md`](_agent_pings.md) (or directly in your tab session):

- `git pull` (any variant: `--ff-only`, `--rebase`, plain)
- `git rebase` (interactive or otherwise; including `git pull --rebase`)
- `git push` (to any remote; any branch; any flag including `--force-with-lease`)
- `git stash pop` / `git stash apply` of stashes you didn't create yourself
- `git checkout origin/<branch> -- .` or any wildcard remote-overwrite of working tree
- `git reset --hard` or any destructive reset

### What you CAN still do

- **Commit locally per shippable unit** (HARD RULE per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" still
  applies). Local commits accumulate on `live-defi-rollout` until operator authorizes a push.
- **Read git state**: `git status`, `git log`, `git fetch` (read-only — fetch downloads but doesn't merge),
  `git diff`, `git stash list`, `git stash show`.
- **`git stash push` your OWN dirty work** if you need a clean tree to do something specific (then restore
  via `git stash pop` when done — and only if the stash was YOURS).
- **Edit files, run tests, run quality gates, run scripts.**

### What to do when you'd previously have pulled / rebased / pushed

| Old behaviour                                        | New behaviour                                                         |
| ---------------------------------------------------- | --------------------------------------------------------------------- |
| Commit done → push to share with workspace           | Commit locally → ping `_agent_pings.md` "Tab N: commit `<sha>` ready for push, see plan-of-record" → wait for operator authorization |
| Incoming commits on origin → pull/rebase to update   | Do NOT pull. `git fetch` to inspect; ping "Tab N: N commits on origin since my last fetch, request sync" → wait |
| Local conflicts with origin → rebase to resolve      | Stop. Ping "Tab N: BLOCKED — local commits diverge from origin" + list both sides → wait for operator decision |
| Foreign dirty files on disk during rebase / pull     | This situation should NOT arise anymore (no pulls/rebases). If you find foreign dirty files at boot, leave them alone (per "Two teammates × multiple parallel agents" rule) |

### Why this rule exists

A pull/rebase by one tab when another tab has uncommitted work in the shared working tree silently stashes
the other tab's edits (as we just experienced — Tab 5's rebase auto-stashed Tab 1's main-orchestrator-LEDGER
+ AGENT_ONBOARDING WIP on 2026-05-08 PM). The auto-stash is technically correct git behaviour, but it
breaks the "shared working tree, no pull needed between tabs" assumption the workspace runs on. The fix is
to centralize all pull/push/rebase operations through operator authorization — pinged via `_agent_pings.md`
or stated directly in the tab session.

### Operator-authorized git operations format

When operator wants you to pull/rebase/push, they'll write a directive in `_agent_pings.md` like:

```text
[YYYY-MM-DD HH:MM UTC] OPERATOR → tab-N — AUTHORIZED git pull --rebase + push for commit <sha>
```

Or directly in your tab session: _"Tab N — go ahead and push your commit, then pull origin"_.

Either form is sufficient authorization. Until you see one, your local commits stay local.

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
| **Side findings** (case-1 to case-5) | Per Findings Triage Discipline in CLAUDE.md — case-5 BIG findings ALSO go through plan-of-record + ping (NOT direct chat); main agent escalates to operator | Throughout |
| **Direct chat to Harsh from your tab session** | NEVER — main is your dispatcher | NO EXCEPTIONS — see "Routing rule" below |

#### Routing rule (clarified 2026-05-08 PM after agents started bypassing main)

**Every question, blocker, decision request, scope concern, finding, status escalation, or operator-direction
ask MUST go through the plan-of-record + ping ledger.** Even case-5 BIG findings. Even "I think the work-split
underestimated my scope." Even "my plan looks blocked on something outside my scope." Even "I think I should
defer Plan X." All of it.

Routing flow:

1. Write the question / finding into your plan-of-record's `## Open questions` § using the format below.
2. Append a one-line ping to `harsh_orchestrator/_agent_pings.md` pointing at the plan-of-record.
3. Continue with anything you CAN do (don't block waiting).
4. **Main agent** reads the ping (~1 min cadence), reads your Q in the plan-of-record, writes A1 in the plan-
   of-record (sometimes after escalating to operator on your behalf), removes the ping line.

**Why this rule is strict.** The operator runs many spawned-tab Cursor / Claude Code sessions in parallel.
If every spawned tab streams questions into its own session text, the operator has to switch tabs and read
every one to keep up. The plan-of-record + ping bus centralizes routing through the main agent, who is
purpose-built for triage + escalation. This is the entire reason main exists.

**What "direct chat to Harsh" actually means.** Your tab session text is visible to Harsh — every response
you write is something he CAN read. That's fine for status updates ("now running QG", "Phase 0 sub-agent
fan-out complete"), progress notes, and completion confirmations. **It is NOT fine for: questions, blockers,
decisions, ambiguity-resolutions, scope concerns, "should I do X or Y", "is this in scope", or any other
ask-for-direction.** Those go in plan-of-record + ping ledger ONLY. If you find yourself typing a question
into your tab session, stop and write it in the plan-of-record instead.

**What if it's truly time-critical and the operator needs to see it within seconds?** Still go through the
ping ledger. Use the `🔴 P0` priority marker in your ping line:

```text
[YYYY-MM-DD HH:MM UTC] <agent-tag> — 🔴 P0: <one-line> ; see <plan-of-record>
```

Main agent treats P0 pings as immediate-escalation-to-operator. The latency is ~1-2 min, not seconds, but
that's the cost of the centralized model — and the operator's attention is preserved for the cases that
actually warrant it.

#### Q&A format on plan-of-record

```markdown
### Q1 — [your-agent-tag, YYYY-MM-DD HH:MM] — short title
**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what was tried, options considered, recommendation if you have one>

#### A1 — [main, YYYY-MM-DD HH:MM]
**Status**: ✅ RESOLVED

<answer + reasoning + commit-sha of anything shipped meanwhile>
```

Main agent polls `_agent_pings.md` ~1 min cadence (faster while operator's active). Your A1 typically
lands within 1-5 min for technical Qs; longer if the Q escalates to operator.

#### End-to-end workflow example (a typical Q lifecycle)

Concrete walk-through of a question moving from "spawned tab realises something is unclear" all the way to
"answer received, work resumes." Use this as the reference pattern.

**Scenario**: Tab 3 (`deployment-ui-tab`) is shipping deployment-UI lifecycle tabs Phase A (UAC SSOT for
lifecycle column). They discover the plan-of-record names ~37 todos across 8 phases, but the work-split
estimated only ~10 AI-days for this tab. Tab 3 needs operator direction on whether to ship full scope or
trim.

**Step 1 — Tab 3 writes the question into the plan-of-record's `## Open questions` section** (creating the
section if it doesn't exist yet):

```markdown
## Open questions

### Q1 — [deployment-ui-tab, 2026-05-08 13:21 UTC] — Plan scope larger than work-split estimate

**Status**: 🟡 BLOCKED — waiting for direction on full-ship vs trim

Plan body lists ~37 todos across 8 phases / 6 repos:
- Phase A UAC SSOT (5 todos)
- Phase B 4 tab refactors (12 todos)
- Phase C cloud-toggle (4 todos)
- Phase D auth flow (8 todos)
- Phase E env-resolution (3 todos)
- Phase F (...) ...
- Phase G (...) ...
- Phase H deploy_missing wrap-up (5 todos — Phase 2 already blocked on Ikenna IAM)

Work-split estimated ~10 AI-days for this tab; current scope projects to ~16-18 AI-days at single-agent
throughput, ~12-14 with 5 parallel sub-agents at boot.

**Options**:
(a) Ship full scope (~37 todos) over 2-3 cycles. Risks: pushes Phase D auth re-shape past 2026-05-23
    cutover; Ikenna Tab 5 audit-log integration unblock-date slips.
(b) Trim to highest-priority phases A + B + D (lifecycle tabs + UAC SSOT + auth re-shape, ~25 todos).
    Defers C/E/F/G/H to a follow-up cycle. Auth re-shape unblocks Ikenna Tab 5 in cycle. Fits ~10 AI-day
    work-split estimate.
(c) Trim further to A + D only (UAC SSOT + auth re-shape, ~13 todos). Defers all UI tab refactors to
    a follow-up cycle.

**Recommendation**: (b) — preserves the cross-side Ikenna handshake (auth re-shape Phase D) + delivers the
UAC SSOT that Tab 1 depends on for instruments-live UI tab content.
```

**Step 2 — Tab 3 appends a one-line ping to `harsh_orchestrator/_agent_pings.md`**:

```text
[2026-05-08 13:22 UTC] deployment-ui-tab — Q on plan scope (37 todos vs ~10 AI-day est) — full-ship vs trim;
  see plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md
```

**Step 3 — Tab 3 continues working on what they CAN do** (e.g. starts Phase A UAC SSOT — that work is
in-scope under any of the three options, so it doesn't block on the answer).

**Step 4 — Main agent polls `_agent_pings.md` (~1 min later)**, sees the ping, opens the plan-of-record,
reads Q1, decides this is a scope decision that requires operator input. Main agent writes back in chat
to operator with a summary:

> "Tab 3 hit case-5 BIG: plan-of-record scope ~37 todos vs work-split ~10 AI-day estimate. Options
> (a) full-ship, (b) trim to A+B+D ~25 todos preserving Ikenna handshake, (c) trim to A+D ~13 todos.
> Tab 3 recommends (b). What's your call?"

Operator picks (b) in chat.

**Step 5 — Main agent writes A1 in the plan-of-record**:

```markdown
#### A1 — [main, 2026-05-08 13:34 UTC]
**Status**: ✅ RESOLVED — operator picked (b) trim to A + B + D

Operator decision in chat 13:34 UTC: ship Phase A UAC SSOT + Phase B 4 tab refactors + Phase D auth
re-shape this cycle (~25 todos). Defer Phases C / E / F / G / H to follow-up cycle (next 2-3 days). Auth
re-shape Phase D ships first → unblocks Ikenna Tab 5 audit-log integration per cross-side handshake.
Check off C/E/F/G/H todos with `**DEFERRED → follow-up cycle**` annotation; do not delete.
```

**Step 6 — Main agent removes the ping line from `_agent_pings.md`** (the doorbell job is done; full Q&A
history lives durably in the plan-of-record).

**Step 7 — Tab 3 sees the A1** (next time they touch the plan-of-record, e.g. flipping a checkbox after
shipping a sub-todo). They drop scope to A + B + D, mark deferred phases with `**DEFERRED → follow-up
cycle**`, and continue. No further operator interaction needed for this question.

**Total operator attention spent**: ~30 seconds in chat to read main's summary + answer. **Spawned tab
attention**: focused, in-scope. **Audit trail**: fully captured in the plan-of-record's `## Open
questions` § (durable; survives ledger sweeps + main-agent context resets).

#### Anti-patterns (what NOT to do — these break the model)

- ❌ **Type the question into your tab session text**: _"Hey Harsh, I'm looking at the plan and I see ~37
  todos. Should I ship all of them or trim?"_ — operator now has to switch tabs and read context. Multiply
  by 5 spawned tabs and the operator's day is gone.
- ❌ **Ping ledger without writing the question in the plan-of-record**: _"Tab 3 — quick Q on scope, can you
  answer?"_ — main agent has no context, has to ping back asking for the question, latency doubles, no
  durable record.
- ❌ **Write the question only in the plan-of-record without a ping**: main agent's ~1 min poll is on
  `_agent_pings.md`, not on every plan body. Question may sit unread for hours.
- ❌ **Bypass main and DM operator on a separate channel** (Telegram, Slack, etc.): main agent doesn't see
  it; the operator's coordination model breaks; A1 won't land in the plan-of-record's audit trail.
- ❌ **Ask three questions about the same scope concern across three different turns** in your tab session
  text: each one is a tax on operator attention. Bundle into one Q with a clear options list.
- ❌ **Use the ping ledger for status updates**: ledger is for blockers and questions only. Status updates
  go in your tab session text (operator can read at their own pace) or in the plan-of-record body as
  iteration-log entries (e.g. _"sweep #37: 16/24 alive, no actions"_).

### 2. Push discipline (UPDATED 2026-05-08 PM — operator authorization required for all pushes/pulls/rebases)

> **⚠️ This subsection is SUPERSEDED on the push-trigger condition.** Read the HARD RULE block at the top of
> this doc ("🚨 HARD RULE — git pull / rebase / push require operator authorization") for the current rule.
> The "zero incoming → push freely" path is no longer in effect. All pushes/pulls/rebases require explicit
> operator authorization via `_agent_pings.md` or direct tab-session direction.

Per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE — **commit per shippable unit always**.
Local commits accumulate; do NOT push them. To request push:

```bash
git status                                       # confirm only your files
git log --oneline origin/<branch>..HEAD          # list local commits ready
```

Then ping `_agent_pings.md`:

```text
[YYYY-MM-DD HH:MM UTC] <your-agent-tag> — Tab N: <count> commits ready for push (sha-list); see <plan-of-record>
```

Wait for operator authorization. Until then, keep working — local commits don't block your tab from making
the next commit.

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
