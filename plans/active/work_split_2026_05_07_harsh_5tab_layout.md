---
title: Harsh's main-agent orchestration ledger (2026-05-07 → cycle close)
type: coordination-doc
status: active (rewritten 2026-05-07 PM — pivoted from fixed-5-tab to dynamic ledger model)
companion_to: plans/active/work_split_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Harsh's main-agent orchestration ledger

> **This is NOT a fixed 5-tab layout** — different from Ikenna's
> [`work_split_2026_05_07_ikenna_5tab_layout.md`](work_split_2026_05_07_ikenna_5tab_layout.md).
> Harsh's working method is **one main agent + dynamic spawned tabs**. The main agent (Harsh's session)
> coordinates everything; tabs spawn as work clarifies. 2 tabs in the morning, 6 by afternoon, sometimes
> two agents on different phases of the same plan in parallel — fine. No fixed daily count.
>
> **Filename retained** for cross-doc references, but the body is now a daily-evolving orchestration ledger.

## Orchestration model — read once at session start

Harsh interacts with ONE main agent. That agent decides per-task:

| Task size                                                             | Where it goes                                                                                                                                                                                                                                  |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **30s–1min** (verify a file, run one gcloud command, flip a checkbox) | Main agent does it in chat. No doc update.                                                                                                                                                                                                     |
| **~5min mechanical** (small audit, simple wire-up, single-file edit)  | Main agent writes a 5-line inline task in this doc's "Ready to spawn" section. Harsh opens a fresh Claude Code tab + paste the task as the prompt; that agent runs it.                                                                          |
| **15min+ deep work** (multi-file, multi-hour, full plan execution)    | Main agent writes a brief entry in "Ready to spawn" pointing at a self-contained sub-doc OR an existing `plans/active/` plan. Fresh tab agent reads the doc + runs independently.                                                              |
| **Audit / research / scan** the main agent needs answers from but doesn't want to block on | Main agent fans out a background `Task(run_in_background=true)` sub-agent. Returns 5-10 min later with a summary. Main agent stays responsive to Harsh in the meantime.                          |
| **Existing plan in `plans/active/`**                                  | Main agent points at it from "Ready to spawn". No rewrite needed — the plan IS the assignment.                                                                                                                                                 |

**Hard rule for the main agent**: never tied up >1 minute on a single thing. Anything longer either delegates
(spawn fresh tab via this doc) or backgrounds (`run_in_background=true` Task). Harsh wants the main agent always
available for direction-setting.

## How agents talk to each other (the bus)

**Plan docs are the message bus + a lightweight ping ledger is the doorbell.** No real-time messaging between
agents — async via PM commits + git pull, but the main agent polls the ping ledger autonomously so Harsh
doesn't have to be the relay.

### Two-tier design

- **[`_agent_pings.md`](_agent_pings.md) = ephemeral doorbell.** Always 5-10 lines (active pings only). Sub-agents
  append a one-liner when they need attention; main agent removes the line when handled. Zero history kept here.
- **Plan doc `## Open questions` = durable Q&A record.** Full question + answer + status marker. Never deleted —
  the audit trail of "what did we ask + decide" lives here forever.

### Lifecycle

```
[T+0]   Spawned agent hits ambiguity
        ↓ writes Q1 in <relevant-plan>.plan.md `## Open questions` (status 🟡 BLOCKED)
        ↓ appends one-liner to _agent_pings.md
        ↓ commits + pushes both

[T+10m] Main agent's /loop wakes
        ↓ git pull --ff-only origin live-defi-rollout
        ↓ reads _agent_pings.md for new entries
        ↓ for each ping → opens the referenced plan doc, reads Q1
        ↓ EITHER answers autonomously (technical Q's I can resolve from context)
        ↓ OR surfaces to Harsh in chat (strategic decisions Harsh must make)
        ↓ when answered: writes A1 in plan doc, flips Q1 status to ✅ RESOLVED
        ↓ removes the line from _agent_pings.md
        ↓ commits + pushes

[T+12m] Spawned agent pulls, reads A1 in plan doc, continues work.
```

### Ping ledger format

One line per active ping, in [`_agent_pings.md`](_agent_pings.md):

```text
[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>
```

Examples:

```text
[2026-05-08 09:14 UTC] phase2-routes-tab — Q on subprocess.run timeout default; see deployment_api_work_stream_a_2026_05_07.plan.md
[2026-05-08 09:32 UTC] dart-playwright-tab — done with personas 1-3, blocked on persona 4 fixture; see strategy_and_dart_master_2026_05_07.plan.md
[2026-05-08 10:01 UTC] manifest-rescan-tab — silent-zero finding for prediction asset_group; see issues/prediction_silent_zero_2026_05_08.md
```

`<agent-tag>` = whatever short identifier the spawned agent picks for itself (typically based on its plan/scope).

### Plan doc Q&A format

In any plan doc, append to / create a `## Open questions` section near the top of the body:

```markdown
## Open questions

### Q1 — [agent-id, 2026-05-07 14:30] — short title
**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what you tried, what's ambiguous, what options
you considered>

#### A1 — [main, 2026-05-07 14:42]
**Status**: ✅ RESOLVED

<answer + reasoning + any next-step pointers + commit-sha of anything shipped meanwhile>
```

Status badges in the heading make scan-for-open-questions instant: 🟡 = needs attention, ✅ = resolved.
Sub-agents check `## Open questions` before starting each new sub-todo + only act on 🟡 items they themselves
asked.

### When the ping ledger overflows

- **5-10 active pings**: normal busy day, single main agent (this one) keeps up via /loop.
- **15-20+ pings persistently**: signal Harsh to spawn a SECOND main agent (another tab with this orchestration
  doc). Two main agents divide the ledger — typically by repo or first-claim. Add a `[CLAIMED-BY: main-1]` marker
  to a ping when starting work on it so the other main doesn't double-handle.

### Daily ledger sweep

Each morning during boot, main agent:

1. Sweep all `plans/active/*.plan.md` for `## Open questions` containing ✅ RESOLVED Q&As older than 24h —
   collapse them into a `### Q&A history (resolved)` subsection at the bottom of the same plan to declutter.
2. Verify [`_agent_pings.md`](_agent_pings.md) has no stale entries (>24h without resolution = either re-prompt
   the sub-agent or escalate to Harsh as a stuck task).

## Spawned-agent prompt template

When main agent recommends a fresh tab, the prompt **must** include the orchestration rules below so the spawned
agent knows it's a delegate, not a peer. Copy this preamble into every spawn:

```text
You are a sub-agent spawned by Harsh's main orchestrator agent (a separate Claude Code session).
Your task is documented in [PLAN-DOC-PATH] — read it first.

ORCHESTRATION RULES:
1. `git fetch origin live-defi-rollout && git pull --ff-only origin live-defi-rollout` before
   the first edit. Re-pull before every commit (other agents are pushing in parallel).
2. If you hit ambiguity / a blocker / a decision that needs Harsh's strategic input:
   a. Write the full question in [PLAN-DOC-PATH]'s `## Open questions` section using the
      format in `plans/active/work_split_2026_05_07_harsh_5tab_layout.md` (status 🟡 BLOCKED).
   b. Append a one-liner to `plans/active/_agent_pings.md` with timestamp + your agent-tag
      + a 5-10 word summary + plan-doc pointer.
   c. Commit + push both.
   d. Continue with anything you CAN do — don't block waiting. The main agent's /loop polls
      the ping ledger every ~10 min, will answer in the plan doc + remove the ping line. You
      pick up the answer on your next git pull.
   e. **Do not message Harsh directly** unless your finding is case-5 (big) per Findings
      Triage Discipline. The main agent is your conversational dispatcher.
3. Read `unified-trading-pm/cursor-configs/CLAUDE.md` for workspace rules — especially
   "Findings Triage Discipline", "Commit + Push + Flip Plan Checkboxes (HARD RULE)",
   "Two teammates × multiple parallel agents", and the per-asset-group shard-key matrix.
4. Per shippable unit: commit + push + flip the matching plan checkbox in the same logical
   unit. Don't batch.
5. **Findings Triage Discipline (HARD RULE)** — any side-discovery during execution: classify
   case-1-to-5 per CLAUDE.md and route appropriately. Big findings (case 5) → write in chat
   summary IF you're conversing with Harsh, AND file an issue doc in `plans/active/issues/`.
   Small QG-failure findings on someone else's code are EXEMPT until ~2026-05-09 per the
   temporary exception in CLAUDE.md.

YOUR TASK:
<full self-contained context — what to ship, repos owned, collision boundaries with other
in-flight work, done-definition with verifiable bullet points>

REPORT-BACK:
- Per shippable unit: code commit + plan-flip commit + push.
- Final: comment in [PLAN-DOC-PATH] body marking the done-definition met.
- Main agent will sweep your status on demand via `git log --oneline live-defi-rollout`.
```

---

## Today's status (2026-05-07 D1)

### 🟢 Spawned tabs in flight
- _(none yet today)_

### 🟡 Ready to spawn (open a fresh tab + paste the prompt)
- _(none queued — main agent is awaiting Harsh's direction on Phase 2 routes; see "Main agent doing now" below)_

### ⚪ Main agent (this session) doing now
- Pivoting this doc from fixed-5-tab to orchestration-ledger model (in progress, ~5 min remaining)
- Awaiting Harsh's direction on whether to:
  - **(a)** Pull D3 deployment-api Phase 2 routes forward — write a self-contained prompt + queue under
    "Ready to spawn", Harsh opens a fresh tab to execute it (~4-6 hours independent work)
  - **(b)** Do D2 P0 verify+flip feature_dag SSOT here in this session (~5 min) + then queue Phase 2 for spawn
  - **(c)** Stop here for the day — D1 already done, pick up D2 fresh tomorrow

### ✅ Done today
- D1 cefi VM monitor — offloaded to parallel monitoring agent (37 cefi VMs in flight from bitfinex/bitget/kraken
  ×futures+spot ×2020-2026; events flowing per main-agent spot-check at T+30min) ✓
- D1 UAC backfill-launch types Phase 1 — Ikenna shipped early `UAC@a70b3f6` (5 Pydantic models + 23-value
  StrEnum + 15 unit tests pass) ✓
- Plan flips for D1 — `PM@fb7aefa` (work-split + work-stream-A Phase 1 checkboxes) ✓
- Findings Triage Discipline (HARD RULE) added to CLAUDE.md — `PM@c8e0e0f` ✓
- 3 issue docs filed retroactively per the new rule — `PM@becfe4a` (cefi tardis writegate findings + lending-indices
  handler bugs + audit_followups #7) ✓
- Temporary exemption added to Findings Triage Discipline for QG-failure findings on others' code —
  `PM@a86de35` ✓
- Pivoted layout doc from 5-tab to orchestration ledger — _(this commit)_ ✓

### ❓ Open questions across active plans
_(synced by main agent on demand — none flagged today; the main agent has been the only Harsh-side agent in flight
this session, so no inter-agent Q&A yet)_

---

## Daily reset (each morning)

Main agent boots and:

1. `git fetch origin live-defi-rollout && git log --oneline -25 origin/live-defi-rollout` — summarize incoming
   commits for Harsh (so both have shared context).
2. `git pull --ff-only origin live-defi-rollout` (if no local commits ahead) or `git rebase` if there are.
3. Re-read [`work_split_2026_05_07.md`](work_split_2026_05_07.md) (the parent D1-D5 plan) + this ledger's
   "Today's status" + [`_agent_pings.md`](_agent_pings.md) for any overnight pings.
4. **Daily ledger sweep** — for every plan with `## Open questions`:
   - Identify ✅ RESOLVED Q&As older than 24h → collapse into a `### Q&A history (resolved)` subsection at the
     bottom of the same plan to declutter the top.
   - Verify no stale 🟡 BLOCKED Q&As (>24h without answer) — if any, either re-prompt the sub-agent or
     escalate to Harsh as a stuck task.
   - Verify `_agent_pings.md` has no orphan lines (lines whose plan-doc Q&A was already resolved but the ledger
     line wasn't removed).
5. Move yesterday's "Done today" entries into the "Historical log" section at the bottom of this doc.
6. Reset "Today's status" with the new date header + identify today's actionable items.
7. Re-arm the /loop polling the ping ledger (`/loop 10m check ping ledger and answer technical Qs`).
8. Report to Harsh: "Today's plan = X, Y, Z. I recommend doing X here, queuing Y for fresh tab, Z idle on
   prereq. Ping ledger has K entries open."
9. Wait for Harsh's direction.

## Historical log

### 2026-05-07 (D1)
_(populated at EOD)_

---

## Cross-references

- Parent split: [`work_split_2026_05_07.md`](work_split_2026_05_07.md) — the D1-D5 calendar split between Harsh
  and Ikenna.
- Ikenna's mirror layout: [`work_split_2026_05_07_ikenna_5tab_layout.md`](work_split_2026_05_07_ikenna_5tab_layout.md)
  — Ikenna's working method (fixed 5 thematic tabs). Different from this ledger's dynamic model. **Don't apply
  Ikenna's tab-1-to-5 ownership to Harsh's spawned tabs** — the items get assigned ad-hoc per-day, not by domain.
- Audit dependency graph: [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) — per-plan
  status + critical path.
- Workspace rules: [`../../cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) — read by every spawned tab.
- Findings discipline: CLAUDE.md § "Findings Triage Discipline (HARD RULE)" — case-1-to-5 routing for any issue
  surfaced mid-task.
