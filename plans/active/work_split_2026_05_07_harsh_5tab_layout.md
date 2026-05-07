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

**Plan docs are the message bus.** No real-time messaging between agents. Async via PM commits.

When a spawned agent is blocked / has a clarifying question / surfaces a decision-needed:

1. Spawned agent writes the question in their **plan doc's `## Open questions` section** (near the top of the
   plan body, after the frontmatter).
2. Spawned agent commits + pushes.
3. Harsh sees the question (either by checking the tab directly OR by asking the main agent "go check
   `<plan-name>.plan.md`, an agent has been asking questions").
4. Main agent reads the plan + writes an answer in the same `## Open questions` section.
5. Spawned agent reads the answer on its next iteration + continues.
6. Harsh can ALSO answer directly in the tab if main agent isn't around.

### Q&A entry format

In any plan doc, append to / create a `## Open questions` section near the top of the body:

```markdown
## Open questions

### Q1 — [agent-id, 2026-05-07 14:30] — short title
<full question with file:line context, what you tried, what's ambiguous, what options
you considered>
**Status**: BLOCKED / waiting for answer.

#### A1 — [main, 2026-05-07 14:42]
<answer + reasoning + any next-step pointers + commit-sha-of-anything-shipped-meanwhile>
```

After answering, main agent flips status to `RESOLVED` (or leaves the Q&A as a historical record + adds a
RESOLVED tag). Sub-agent confirms by reading on its next iteration.

**Sub-agents check `## Open questions` before starting each new todo.** Main agent sweeps these on every
"what's everyone doing?" audit.

## Spawned-agent prompt template

When main agent recommends a fresh tab, the prompt **must** include the orchestration rules below so the spawned
agent knows it's a delegate, not a peer. Copy this preamble into every spawn:

```text
You are a sub-agent spawned by Harsh's main orchestrator agent (a separate Claude Code session).
Your task is documented in [PLAN-DOC-PATH] — read it first.

ORCHESTRATION RULES:
1. `git fetch origin live-defi-rollout && git pull --ff-only origin live-defi-rollout` before
   the first edit. Re-pull before every commit (other agents are pushing in parallel).
2. If you hit ambiguity / a blocker, write a question in [PLAN-DOC-PATH]'s `## Open questions`
   section using the format in `plans/active/work_split_2026_05_07_harsh_5tab_layout.md`,
   commit + push, and continue with anything you CAN do. The main agent will answer there;
   you read the answer on your next iteration. **Do not block waiting in chat** — the main
   agent isn't your conversational peer.
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
   "Today's status" + any plan with `## Open questions` flagged.
4. Move yesterday's "Done today" entries into the "Historical log" section at the bottom.
5. Reset "Today's status" with the new date header + identify today's actionable items.
6. Surface any unanswered Q&A questions still pending from previous days.
7. Report to Harsh: "Today's plan = X, Y, Z. I recommend doing X here, queuing Y for fresh tab, Z idle on
   prereq."
8. Wait for Harsh's direction.

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
