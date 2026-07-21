---
doc_type: plan
title: Harsh's main-agent orchestration ledger (2026-05-07 → cycle close)
summary:
status: active (rewritten 2026-05-07 PM — pivoted from fixed-5-tab to dynamic ledger model)
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, e2e-testing, features-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-07"
type: coordination-doc
companion_to: plans/active/work_split_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): the doc's own body
declares it "NOT a fixed 5-tab layout" but a daily-evolving sub-agent orchestration ledger; its open checkboxes are
template boilerplate quoted verbatim inside spawn-prompt code fences, not live tracked items — the real per-tab status
lives in prose headers above each fence, and all tabs (3-14) are marked `✅ DONE 2026-05-08` with cited commit SHAs. The
one item that read `🟢 IN FLIGHT` (cefi babysit) was absorbed into the cefi_master epic, itself long closed
(`cefi_consolidated_closeout_2026_07_18.md`). Nothing here is untracked.

# Harsh's main-agent orchestration ledger

> **This is NOT a fixed 5-tab layout** — different from Ikenna's
> [`work_split_2026_05_07_ikenna_5tab_layout.md`](work_split_2026_05_07_ikenna_5tab_layout.md). Harsh's working method
> is **one main agent + dynamic spawned tabs**. The main agent (Harsh's session) coordinates everything; tabs spawn as
> work clarifies. 2 tabs in the morning, 6 by afternoon, sometimes two agents on different phases of the same plan in
> parallel — fine. No fixed daily count.
>
> **Filename retained** for cross-doc references, but the body is now a daily-evolving orchestration ledger.

## Bootstrap — read first if you're a fresh main-agent chat

If this conversation just started — Harsh's previous main-agent chat died, ran out of context, or was reset — and you're
being asked to be the main orchestrator, **this doc is your boot context**. Read it end-to-end before answering Harsh's
first message of the new chat.

**Your role**: you are the **main orchestrator (Tab 1)**. You do NOT write service code or implement plan items
yourself. Your job is direction-setting, Q&A dispatch between Harsh + spawned tabs, plan-of-record curation, and
ping-ledger triage. Information gathering (reading plans, grepping, gcloud probes, git state inspection) is fine.
Implementation of plan items is NOT fine — that's spawned tabs' work.

**Boot checklist** (run after reading this doc once):

1. From `unified-trading-pm/`: `git status` + `git log --oneline origin/live-defi-rollout..HEAD` — see local commits
   ahead of origin (work spawned tabs have committed but not pushed) + any of your own uncommitted edits.
2. `cat plans/active/_agent_pings.md` — see active pings waiting for you.
3. Skim "Today's status" below for the tab registry, in-flight work, and queued spawns.
4. Ack to Harsh: _"Main agent online. State: N tabs in flight, M pings open, K local commits queued for push. Today's
   plan = X, Y, Z. Standing by."_

**Polling cadence**: check `_agent_pings.md` every **~1 minute** while Harsh is active. When tabs go quiet (no pings for
30+ min), stretch to 5 min. Spawned tabs work mostly autonomously; pings are the rare interrupt.

## Bootstrap — read first if you're a spawned tab (Tab 2+)

If Harsh just told you _"work on Tab N tasks"_ in a fresh Claude Code tab, you're a spawned tab. **This section is your
boot context.** Read it once before doing anything else, then read everything else in this order:

1. **THIS section** — confirm your role.
2. Find your **tab entry** in this doc's "Today's status → Tab registry" by tab number. The spawn prompt block under
   your tab entry is your full task brief — repos owned, behavioural contract, collision boundaries, done-definition.
   Read it carefully.
3. Sections **"How agents talk to each other"**, **"Shared working tree model"**, **"Push discipline"** — non-negotiable
   workflow rules. The Q&A flow + commit/push discipline differ from the workspace defaults while we're in
   figure-out-workflow phase; don't apply CLAUDE.md verbatim without reading these first.
4. **`unified-trading-pm/cursor-configs/CLAUDE.md`** — workspace rules (uv not pip, basedpyright, no os.getenv,
   shard-granularity SSOT, "Findings Triage Discipline (HARD RULE)", "Commit + Push + Flip Plan Checkboxes (HARD RULE)"
   — note the push half is deferred to main per "Push discipline" above).
5. **`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`** — sub-agent inheritance rules.
6. Your **plan-of-record** (the plan doc named in your tab entry — e.g. `cefi_master_2026_05_07.md` for
   `cefi-babysit-tab`, `deployment_api_work_stream_a_2026_05_07.md` for `deployment-api-phase2-tab`). This is where your
   todos live, where you flip checkboxes as you ship, where you write `## Open questions`, and where you append your
   final `DONE-<YYYY-MM-DD>` block.

**Your role**: you are Tab N, a SCOPED IMPLEMENTER. You execute a specific task end-to-end, ship it, and stop. You do
NOT take on adjacent work, spawn sub-agents of your own, or push to origin. The main agent (Tab 1) handles
direction-setting + Q&A dispatch + push approval.

**How to ask a question** (when you hit ambiguity / blocker / decision):

1. Write the full question in your **plan-of-record's `## Open questions` section** (NOT this orchestration ledger, NOT
   the work_split). Status `🟡 BLOCKED`. Format per "Plan doc Q&A format" below.
2. Append a one-liner to [`_agent_pings.md`](_agent_pings.md):
   `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <5-10 word summary>; see <plan-of-record>.md`.
3. Optionally commit both LOCALLY (don't stress; if commits happen great, if not also fine — Q&A clutter is more costly
   than Q&A loss).
4. Continue with anything you CAN do — don't block waiting. Main agent polls `_agent_pings.md` every ~1 min; answer
   typically lands within 1-5 min as `#### A1 — [main, ...]` block beneath your Q in the plan doc.
5. Re-read your plan-of-record periodically (shared working tree → no `git pull` needed); when you see the answer,
   continue.
6. **Do NOT message Harsh directly** in chat. Main agent is your conversational dispatcher. Exception: case-5 big
   finding per Findings Triage Discipline (data correctness, deadline-critical, cross-repo, SSOT contradiction,
   work-split changing, in-flight-VM contradicting) — those go to Harsh AND get an issue doc.

**How to update your plan-of-record as you ship work** (mandatory):

1. **Flip checkboxes per shippable unit.** As soon as a todo ships (committed locally + tests green), edit the plan doc:
   `- [ ] [SCRIPT] P0. Description...` → `- [x] [SCRIPT] P0. Description... (<repo>@<sha> — <evidence>)`. Per CLAUDE.md
   HARD RULE: do this in the same logical unit as the code commit, not at end of session.
2. **Append progress notes** to the relevant plan body section if you found something worth recording (e.g. "Day 2
   monitoring sweep" subsection in `cefi_master.md` is a good model — appended findings with a timestamp +
   observations).
3. **Document findings per Findings Triage Discipline** (CLAUDE.md). Case 1 (in-scope) → fix in the same commit; case 2
   (adjacent to your plan) → annotate your plan body; case 3-4 (someone else's plan) → annotate their plan body with
   owner pointer; case 5 (big) → notify Harsh in chat AND file an issue doc in `plans/active/issues/`.
4. **Final**: when your done-definition is met, append a `## DONE-<YYYY-MM-DD>` block at the bottom of the plan body
   listing every code + plan-flip commit sha. Then push per the conditional rule (fetch + zero incoming → push freely;
   any incoming → flag in `## Open questions` for main + operator). Then go quiet — don't pick up new work autonomously.
   Wait for main to spawn you for the next task or Harsh to explicitly close you out.

**Commit + push cadence rule** (per CLAUDE.md HARD RULE, with the multi-agent safety valve):

- Per shippable unit (helper + tests, one adapter migration, one wire-in, one plan-flip): **commit locally**.
- 5-6 small commits per session, NOT one mega-commit at end. Reviewable units, easy to revert.
- Before each push: `git fetch origin <branch>` + check for incoming. If zero incoming → push freely. If any incoming →
  DON'T push, write a `🟡 BLOCKED` entry in your plan-of-record's `## Open questions`, ping the ledger, continue with
  what you can do. Main + operator resolve the conflict path.
- Pre-commit check is mandatory before EVERY commit (catches accidental bundling of teammates' WIP from the shared
  working tree):
  ```bash
  git status                 # full picture
  git diff --cached --stat   # NO PATH ARGUMENT
  ```
  If anything in the staged set or working tree isn't yours, surgically un-stage (`git restore --staged <file>`) or
  stash (`git stash --keep-index`) before committing. Use `git add -p` for your hunks if any shared file has foreign
  edits.

**One-line ack to main agent on boot** (write this after you've read everything above):

Append to [`_agent_pings.md`](_agent_pings.md): `[<UTC>] <agent-tag> — STARTED Tab N (<plan-doc>)` — main agent will see
it on next 1-min poll, ack with a short note in your plan doc's `## Open questions` if there's anything to flag,
otherwise stays silent. Your STARTED ping gets removed automatically once main confirms your boot is clean.

## Tab numbering convention (codified 2026-05-08)

Tabs are addressed by integer slot. **Tab 1 = main orchestrator** (this session, always). Tab 2, 3, 4, … = spawned tabs
in spawn order. When the main agent queues a new spawn, it picks the next free tab number and files the entry under
"Today's status → Tabs queued" with that tab number as the heading. Harsh opens a fresh Claude Code tab and tells that
agent _"work on Tab N tasks"_ — the agent finds the matching entry in this doc and starts.

A tab's identity is the **integer slot**, not the agent-tag (e.g. `cefi-babysit-tab`). Agent-tag is descriptive; tab
number is addressable. Both go in the registry entry for clarity.

## Orchestration model — read once at session start

Harsh interacts with ONE main agent. That agent decides per-task:

| Task size                                                                                  | Where it goes                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **30s–1min** (verify a file, run one gcloud command, flip a checkbox)                      | Main agent does it in chat. No doc update.                                                                                                                                        |
| **~5min mechanical** (small audit, simple wire-up, single-file edit)                       | Main agent writes a 5-line inline task in this doc's "Ready to spawn" section. Harsh opens a fresh Claude Code tab + paste the task as the prompt; that agent runs it.            |
| **15min+ deep work** (multi-file, multi-hour, full plan execution)                         | Main agent writes a brief entry in "Ready to spawn" pointing at a self-contained sub-doc OR an existing `plans/active/` plan. Fresh tab agent reads the doc + runs independently. |
| **Audit / research / scan** the main agent needs answers from but doesn't want to block on | Main agent fans out a background `Task(run_in_background=true)` sub-agent. Returns 5-10 min later with a summary. Main agent stays responsive to Harsh in the meantime.           |
| **Existing plan in `plans/active/`**                                                       | Main agent points at it from "Ready to spawn". No rewrite needed — the plan IS the assignment.                                                                                    |

**Hard rule for the main agent**: never tied up >1 minute on a single thing. Anything longer either delegates (spawn
fresh tab via this doc) or backgrounds (`run_in_background=true` Task). Harsh wants the main agent always available for
direction-setting.

## How agents talk to each other (the bus)

**Plan docs are the message bus + a lightweight ping ledger is the doorbell.** No real-time messaging between agents —
async via the **shared working tree** (all tabs run on the same PC, same `.git/`, same files; see "Shared working tree
model" below). Main agent polls the ping ledger autonomously so Harsh doesn't have to be the relay.

### Two-tier design

- **[`_agent_pings.md`](_agent_pings.md) = ephemeral doorbell.** Always 5-10 lines (active pings only). Sub-agents
  append a one-liner when they need attention; main agent removes the line when handled. Zero history kept here.
- **Plan doc `## Open questions` = durable Q&A record, ON THE AGENT'S PLAN-OF-RECORD** (e.g. `cefi-babysit-tab` →
  [`cefi_master_2026_05_07.md`](cefi_master_2026_05_07.md); `deployment-api-phase2-tab` →
  [`deployment_api_work_stream_a_2026_05_07.md`](deployment_api_work_stream_a_2026_05_07.md)). Full question + answer +
  status marker. Never deleted — audit trail of "what did we ask + decide" lives here forever. **Do NOT write Qs into
  this orchestration ledger**
  ([`work_split_2026_05_07_harsh_5tab_layout.md`](work_split_2026_05_07_harsh_5tab_layout.md)) — that's main-agent-only
  writing surface. (Codified 2026-05-08 after `cefi-babysit-tab` initially put their Qs in the wrong doc.)

### Lifecycle

```
[T+0]    Spawned agent hits ambiguity
         ↓ writes Q1 in <agent's-plan-of-record>.md `## Open questions` (status 🟡 BLOCKED)
         ↓ appends one-liner to _agent_pings.md (with plan-doc pointer)
         ↓ optionally commits both LOCALLY — Q&A commits are not stressed; if they
           land in commits great, if not also fine. (Push follows the conditional
           rule in "Push discipline" below — fetch + check incoming + push iff zero.)
         ↓ continues with anything they CAN do (don't block waiting)

[T+ ~1m] Main agent's poll wakes (1-min cadence while Harsh is active)
         ↓ shared working tree → no `git pull` needed between tabs; HEAD + working tree
           already reflect the spawned agent's local edits/commits
         ↓ reads _agent_pings.md for new entries
         ↓ for each ping → opens the referenced plan doc, reads Q1
         ↓ EITHER answers autonomously (technical Qs I can resolve from context)
         ↓ OR surfaces to Harsh in chat (strategic decisions Harsh must make,
           or anything that contradicts a workspace SSOT)
         ↓ when answered: writes A1 block in plan doc beneath Q1, flips status 🟡 → ✅ RESOLVED
         ↓ removes the ping line from _agent_pings.md

[T+ later, when work is fully resolved] Either main or operator removes the Q1+A1 block
         entirely from the plan doc to keep it uncluttered. The audit trail of
         "what was asked + what was decided" can survive in commits if commits
         happened, OR in chat history, OR not at all — Q&A clutter is more costly
         than Q&A loss.

[T+ next-poll-cycle by spawned agent] Spawned agent re-reads its plan doc
         (file already updated in shared working tree), sees A1, continues work.
```

### Shared working tree model (codified 2026-05-08)

All agents on this team — main + every spawned tab — run as separate Claude Code sessions on the **same physical PC**,
against **the same VS Code workspace**, **the same `.git/` directory**, and **the same working tree**. There is no
inter-machine sync; coordination is local-first.

What this means in practice:

- **HEAD and refs are global.** A local commit by any tab moves HEAD for everyone immediately. There is no `git pull`
  step needed between tabs — they all see the same `.git/`.
- **Working-tree edits are visible immediately.** When a spawned agent writes a question into a plan doc and saves, the
  main agent sees it on the next file read — no commit, no push, no pull required.
- **Index (staged changes) is shared too.** If agent A runs `git add foo.py` and agent B runs `git status` one second
  later, agent B sees `foo.py` staged. This is a foot-gun: pre-commit check is mandatory (see below).
- **Pre-commit check is non-negotiable** before EVERY commit, in ANY repo:

  ```bash
  git status                 # full picture: modified, staged, untracked
  git diff --cached --stat   # NO PATH ARGUMENT — see the entire index
  ```

  If anything in the staged set or working tree isn't yours, surgically un-stage (`git restore --staged <file>`) or
  `git stash --keep-index` the foreign hunks before committing. **Never `git add <whole-file>` if anyone else has
  touched it** — use `git add -p` and stage only your hunks. Reference incidents: PM@`961980db` / `611b9501` /
  `34075d84` (all from concurrent-agent overlap).

- **Untracked files are someone else's WIP** by default. Don't sweep them in to clear a QG gate; ask main agent or
  operator first. Reference: PM@2026-05-06 `pipeline-coverage-matrix.md` clobber.

### Push discipline (revised 2026-05-08 — conditional push)

Workspace `CLAUDE.md` HARD RULE = "commit + push at every shippable unit." We **keep both halves** with one safety valve
for the multi-agent shared-`.git/` setup: push only when origin has no incoming commits; if incoming exists, escalate to
main + operator for collaborative resolution.

**Rule** (applies to every agent — main + spawned tabs alike):

1. Per shippable unit: **commit locally** (per CLAUDE.md HARD RULE cadence — small reviewable units, NOT end-of-session
   mega-commits). Pre-commit check is mandatory before EVERY commit:

   ```bash
   git status                 # full picture
   git diff --cached --stat   # NO PATH ARGUMENT
   ```

   If anything in the staged set or working tree isn't yours, surgically un-stage (`git restore --staged <file>`) or
   stash before committing. Use `git add -p` for your hunks if any shared file has foreign edits. Reference incidents:
   PM@`961980db` / `611b9501` / `34075d84`.

2. Before pushing, fetch + check for incoming on the target branch (every repo, every push):

   ```bash
   git fetch origin <branch>
   git log --oneline <branch>..origin/<branch>   # incoming commits, if any
   ```

3. **If zero incoming → push.** This is the workspace default; operator approval not needed.

4. **If any incoming → STOP. Do NOT push.** Flag to main agent + operator:
   - Write a one-line entry in your plan-of-record's `## Open questions` block: _"Push blocked on `<repo>`: N incoming
     commits on `origin/<branch>` (`<sha>`, `<sha>`...). My M local commits ready to push (`<sha>`...). Need rebase /
     merge / cherry-pick / drop decision."_ Status `🟡 BLOCKED`.
   - Append a one-liner ping in [`_agent_pings.md`](_agent_pings.md) per the standard format pointing at the plan doc.
   - Continue with anything you CAN do — don't block on the resolution.
   - Main agent + operator review the incoming together → decide rebase / merge / cherry-pick / drop → either main agent
     does the push, or instructs you to push after applying the resolution. Plan-doc `## Open questions` block flips 🟡
     → ✅ when resolved.

5. **Main agent has the same rule** — push only when no incoming, escalate to operator when conflict arises.

**Why the safety valve**: with multiple agents committing concurrently to the same `.git/` and pushing to the same
origin branch, "incoming on origin" almost always means another agent (or a teammate on a different PC) beat you to
push. Blind push by every agent forces a force-push race; routing the conflict path through main

- operator serialises it cleanly. The 99% common case (no incoming) needs no coordination — push freely.

**Mid-conflict during work** (incoming arrives while you're working): you'll discover this on your pre-push fetch. Same
path: don't push, flag, continue with what you can do, wait for resolution.

### Ping ledger format

One line per active ping, in [`_agent_pings.md`](_agent_pings.md):

```text
[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>
```

Examples:

```text
[2026-05-08 09:14 UTC] phase2-routes-tab — Q on subprocess.run timeout default; see deployment_api_work_stream_a_2026_05_07.md
[2026-05-08 09:32 UTC] dart-playwright-tab — done with personas 1-3, blocked on persona 4 fixture; see strategy_and_dart_master_2026_05_07.md
[2026-05-08 10:01 UTC] manifest-rescan-tab — silent-zero finding for prediction asset_group; see issues/prediction_silent_zero_2026_05_08.md
```

`<agent-tag>` = whatever short identifier the spawned agent picks for itself (typically based on its plan/scope).

### Plan doc Q&A format

In any plan doc, append to / create a `## Open questions` section near the top of the body:

```markdown
## Open questions

### Q1 — [agent-id, 2026-05-07 14:30] — short title

**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what you tried, what's ambiguous, what options you considered>

#### A1 — [main, 2026-05-07 14:42]

**Status**: ✅ RESOLVED

<answer + reasoning + any next-step pointers + commit-sha of anything shipped meanwhile>
```

Status badges in the heading make scan-for-open-questions instant: 🟡 = needs attention, ✅ = resolved. Sub-agents check
`## Open questions` before starting each new sub-todo + only act on 🟡 items they themselves asked.

### When the ping ledger overflows

- **5-10 active pings**: normal busy day, single main agent (this one) keeps up via 1-min polling.
- **15-20+ pings persistently**: signal Harsh to spawn a SECOND main agent (another Tab 1-equivalent — by convention
  call it Tab 1b). Two main agents divide the ledger — typically by repo or first-claim. Add a `[CLAIMED-BY: main-a]` /
  `[CLAIMED-BY: main-b]` marker to a ping when starting work on it so the other main doesn't double-handle.

### Daily ledger sweep

Each morning during boot, main agent:

1. Sweep all `plans/active/*.md` for `## Open questions` blocks. **Remove resolved Q&A entries entirely** (don't archive
   — Q&A clutter is more costly than Q&A loss; the trail survives in commits/chat if it survived at all).
2. Verify [`_agent_pings.md`](_agent_pings.md) has no stale entries (>24h without resolution = either re-prompt the
   sub-agent or escalate to Harsh as a stuck task).

## Spawned-agent prompt template

When main agent recommends a fresh tab, the prompt **must** include the orchestration rules below so the spawned agent
knows it's a delegate, not a peer. Copy this preamble into every spawn:

```text
You are Tab N — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1, a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  4. [PLAN-DOC-PATH] — your plan-of-record with todos + done-definition.

Your agent-tag for ping-ledger entries: [agent-tag-suggested-by-main].
Your tab number: N (matches the entry header in the orchestration ledger).

The boot section in the orchestration ledger covers everything you need on workflow:
shared working tree, push discipline (conditional — push iff zero incoming on origin;
flag for main + operator review otherwise), Q&A flow via plan-of-record + ping ledger,
plan-doc curation (checkbox flips per shippable unit, DONE block on completion),
findings triage. Read it once and follow.

ORCHESTRATION RULES:
1. **Shared working tree** — main agent's HEAD and your HEAD are identical (same .git/). No
   `git pull` needed between tabs; another agent's local commit is visible to you the moment
   it lands. BUT: pre-commit check is critical — before EVERY commit, run:
       git status                 # full picture
       git diff --cached --stat   # NO PATH ARG — see entire index
   If anything in the staged set or working tree isn't yours, surgically un-stage
   (`git restore --staged <file>`) or stash (`git stash --keep-index`) before committing.
   Never `git add <whole-file>` if anyone else touched it — use `git add -p` for your hunks.
2. If you hit ambiguity / a blocker / a decision that needs Harsh's strategic input:
   a. Write the full question in [PLAN-DOC-PATH]'s `## Open questions` section using the
      format in plans/active/work_split_2026_05_07_harsh_5tab_layout.md (status 🟡 BLOCKED).
      [PLAN-DOC-PATH] is YOUR plan-of-record (e.g. cefi_master, deployment_api_work_stream_a)
      — NOT work_split or this orchestration ledger. Main agent reads Qs on the plan-of-record.
   b. Append a one-liner to plans/active/_agent_pings.md with timestamp + your agent-tag
      + a 5-10 word summary + plan-doc pointer.
   c. Optionally commit both LOCALLY (don't stress; Q&A commits are nice-to-have, not required).
   d. Continue with anything you CAN do — don't block waiting. Main polls the ping ledger every
      ~1 min, will write A1 into the plan doc + flip 🟡 → ✅ + remove the ping line. You pick
      up the answer on your next read of the plan doc (shared working tree → no `git pull` needed).
   e. **Do not message Harsh directly** unless your finding is case-5 (big) per Findings
      Triage Discipline. The main agent is your conversational dispatcher.
3. Read unified-trading-pm/cursor-configs/CLAUDE.md for workspace rules — especially
   "Findings Triage Discipline", "Commit + Push + Flip Plan Checkboxes (HARD RULE)",
   "Two teammates × multiple parallel agents", and the per-asset-group shard-key matrix.
4. **Per shippable unit: commit (LOCALLY) + flip the matching plan checkbox in the same
   logical unit.** Push follows the conditional rule (see "Push discipline" in the
   orchestration ledger): before pushing, `git fetch origin <branch>` + check for incoming;
   if zero incoming → push freely; if any incoming → DON'T push, write a `🟡 BLOCKED` entry
   in your plan-of-record's `## Open questions` for collaborative resolution by main + operator.
   Commit cadence is unchanged (per CLAUDE.md HARD RULE — 5-6 small commits, NOT one mega-commit).
5. **Findings Triage Discipline (HARD RULE)** — any side-discovery during execution: classify
   case-1-to-5 per CLAUDE.md and route appropriately. Big findings (case 5) → write in chat
   summary IF you're conversing with Harsh, AND file an issue doc in plans/active/issues/.
   Small QG-failure findings on someone else's code are EXEMPT until ~2026-05-09 per the
   temporary exception in CLAUDE.md.

YOUR TASK:
<full self-contained context — what to ship, repos owned, collision boundaries with other
in-flight work, done-definition with verifiable bullet points>

REPORT-BACK:
- Per shippable unit: code commit + plan-flip commit. Push per the conditional rule
  (`git fetch` + zero-incoming → push; any incoming → flag in plan-of-record + ping main).
- Final: append a "DONE-<YYYY-MM-DD>" comment block at the bottom of [PLAN-DOC-PATH] body
  listing every code + plan-flip commit sha. Main agent sees your commits immediately via
  shared .git/ + `git log --oneline live-defi-rollout`.
```

---

## Today's status (2026-05-08 D2)

### Tab registry

#### Tab 1 — main orchestrator

- This session. Polling [`_agent_pings.md`](_agent_pings.md) every ~1 min while Harsh is active.

#### Tab 2 — `cefi-babysit-tab` 🟢 IN FLIGHT

- **Task**: Day-2 OPS babysit of the 24 RUNNING cefi VMs (bitfinex/bitget/kraken ×futures+spot, all `e2-highmem-8`,
  post-`UTL@68b3804a` blank-reason fix relaunch).
- **Plan-of-record**: [`cefi_master_2026_05_07.md`](cefi_master_2026_05_07.md).
- **Q&A**: Q1 raised 03:54 UTC, ✅ RESOLVED 04:05 UTC (4 clarifications + bonus answered in plan doc). Q&A removed on
  resolve once Tab 2 confirms the answer was sufficient.
- **Recent local commits** (queued for next operator-authorised push):
  - `17a21a0` (PM) — Day 2 monitoring sweep findings + sweep #1 baseline (zero blank-reason writes, asymmetric-shape
    resolved on relaunch fleet).
- **Cadence**: 10-min monitoring sweeps; appending findings into the plan body's "Day 2 monitoring sweep" subsection.

#### Tab 4 — `deploy-missing-tarball-refresh-tab` ✅ DONE 2026-05-08 (deploy_missing Phase 1, P0)

- **Verified by main 2026-05-08 05:55 UTC** — all 9 verification checks pass (3 todos flipped, both commits exist with
  cited files on disk, ruff clean, ruff format clean, basedpyright 0/0/0 on new file, 27/27 tests pass, Phase 0/2/3/4
  correctly left for operator gating, bonus IAM proposal deferred with sound rationale).
- **Code commits** (both pushed to origin per conditional rule — zero incoming at push time):
  - `deployment-service@a620e1f` — `refresh-tarballs-for-shard-key.sh` (CEFI/TRADFI/DEFI/SPORTS/PREDICTION/ALL
    - structured `TARBALLS_REFRESH_*` events) + `cloud-build/refresh-tarballs.cloudbuild.yaml` (REST-invokable Cloud
      Build trigger, 30-min timeout, E2_HIGHCPU_8).
  - `deployment-api@faac20a` — `services/tarball_staleness.py` (`TarballStalenessChecker` with `RefreshResult`
    dataclass; FRESH / STALE_NO_TRIGGER / REFRESHED / REFRESH_FAILED / POLL_TIMEOUT statuses; protocol-based indirection
    over GCS Blob + Cloud Build client for testability; naive datetime raises loud) + 27/27 unit tests covering bundle
    membership, mtime read, oldest-mtime aggregation, staleness compare, trigger-then-poll orchestration, and all gate
    states.
- **Plan-flip commit**: PM (this commit) flipping Tab 4 status + DONE-2026-05-08 block already in the plan body.
- **QG status**: deployment-api Pass 1 — 2406/2406 in-scope tests pass; coverage 70.94% (gate 70%); 1 pre-existing
  failure on `test_empty_reason_breakdown.py` (writegate Phase 4.A; not Tab 4's code) — exempt per CLAUDE.md temporary
  2026-05-07 → 2026-05-09 QG-failure exception.
- **What's next** (Phase 2 is gated on Phase 0 operator security review): Tab 4's `ensure_fresh()` API is intentionally
  generic so the eventual Phase 2 endpoint just calls it; no API churn expected.

**Scope clarifications** (read before opening the prompt):

- **Tab 4 ships Phase 1 only**: `refresh-tarballs-for-shard-key.sh` + Cloud Build trigger + deployment-api
  staleness-check helper. Phase 0 (security review) is operator-owned and Phase 2+ depend on Phase 0's IAM decision; do
  NOT proceed past Phase 1.
- **Bonus** (if time): draft a Phase 0 IAM-scope proposal doc in the plan body for operator review (don't sign off; just
  propose).

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 4 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1, a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  4. plans/active/deploy_missing_auto_launch_2026_05_07.md — your plan-of-record (full body).
  5. plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md — parent plan
     (Phase 3 ships the preview-mode Deploy-Missing button; Tab 4 builds toward the auto-launch
     successor).

Your agent-tag for ping-ledger entries: deploy-missing-tarball-refresh-tab (or shorter — pick).
Your tab number: 4.

The boot section in the orchestration ledger covers everything on workflow: shared working tree,
push discipline (conditional — push iff zero incoming on origin; flag for main + operator
review otherwise), Q&A flow via plan-of-record + ping ledger, plan-doc curation (checkbox
flips per shippable unit, DONE block on completion), findings triage. Read it once and follow.

YOUR TASK:

Implement Phase 1 (tarball-refresh wiring) of deploy_missing_auto_launch_2026_05_07.md.
Phase 0 (security review) is operator-owned and Phase 2+ are gated on Phase 0's IAM decisions
— do NOT proceed past Phase 1.

Phase 1 todos (3 P0 items per the plan):

1. **`deployment-service/scripts/vm/refresh-tarballs-for-shard-key.sh <asset_group>`**
   - New script that wraps `create-code-tarballs.sh --asset-group X`.
   - Emits a `TARBALLS_REFRESHED` event when complete (use the standard log_event helper from
     unified-trading-library).
   - Per CLAUDE.md "VM tarball deployment" rule: tarball naming follows
     `gs://deployment-scripts-${PID}/code/<tarball>.tar.gz`.

2. **Cloud Build trigger that runs the refresh script via REST**
   - Located in `deployment-service/cloud-build/` (or wherever existing Cloud Build configs
     live — investigate the repo first).
   - Returns the `build_id` so deployment-api can poll for success.
   - Should be invokable via the standard `cloudbuild.builds.create` RPC; auth via the existing
     deployment-api Cloud Run service account.

3. **deployment-api pre-launch check helper**
   - New helper in deployment-api: read the asset-group tarball's GCS object mtime, compare to
     `git rev-parse HEAD` of `live-defi-rollout` (use unified_cloud_interface for the GCS read).
   - If stale (tarball mtime < latest pushed commit timestamp), kick the Cloud Build via the
     trigger above and wait for completion (poll the build_id) before returning success.
   - Stub the actual gcloud-invoke for Phase 2 (Phase 1 just builds the staleness gate).
   - Standalone helper module — NOT wired into any route yet (Phase 2 will wire).

**Bonus** (only if time after Phase 1 + tests + plan flips ship clean): draft a Phase 0 IAM-scope
proposal doc as a new section in the deploy_missing plan body. Propose the minimal IAM scope for
the eventual Phase 2 endpoint (e.g. `roles/compute.instanceAdmin.v1` scoped to a specific zone +
image family + subnet, vs blanket). Operator reviews before Phase 2 ships.

REPOS OWNED (edit rights):
- deployment-service — new script under scripts/vm/, new Cloud Build trigger config.
- deployment-api — new helper module (not wired into any route).
- unified-trading-pm — plan flips on deploy_missing plan + bonus IAM proposal section.

READ-ONLY DEPS (do NOT edit):
- unified-trading-library — read log_event signature for the TARBALLS_REFRESHED emission;
  do NOT modify.
- unified-cloud-interface — read get_storage_client signature for GCS mtime read; do NOT modify.

COLLISION BOUNDARIES:
- Tab 2 (cefi-babysit-tab) is monitoring cefi VMs — only edits cefi_master.md. ZERO overlap.
- Ikenna's parallel work (writegate Phase 2.A residual on MDPS, alerting Phase 2 on
  alerting-service). ZERO overlap with deploy_missing surface.
- main.py in deployment-api is touched by Tab 3 (just landed) — your helper is standalone, NOT
  wired into routes yet, so no main.py edits needed in Tab 4.

DONE-DEFINITION (verifiable bullets):
- [ ] refresh-tarballs-for-shard-key.sh shipped + emits TARBALLS_REFRESHED event.
- [ ] Cloud Build trigger config shipped + invokable via REST returning build_id.
- [ ] deployment-api staleness-check helper shipped (mtime-vs-HEAD gate, kicks Cloud Build,
      waits for completion).
- [ ] Unit tests for the helper (mock the Cloud Build poll + GCS mtime read).
- [ ] `cd deployment-api && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] `cd deployment-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] Plan flips: plans/active/deploy_missing_auto_launch_2026_05_07.md Phase 1 todos
      `- [ ]` → `- [x]` with `<repo>@<sha>` evidence.
- [ ] Plan-flip commit in PM with message
      `plan(deploy-missing-auto-launch): flip Phase 1 checkboxes (...)`.
- [ ] Bonus (optional): Phase 0 IAM-scope proposal section in the plan body.

REPORT-BACK:
- Per shippable unit: code commit + plan-flip commit. Push per the conditional rule
  (`git fetch` + zero-incoming → push; any incoming → flag in plan-of-record + ping main).
- Final: append a "DONE-2026-05-08" comment block at the bottom of
  plans/active/deploy_missing_auto_launch_2026_05_07.md body listing every code +
  plan-flip commit sha. Main agent sees your commits immediately via shared .git/ +
  `git log --oneline live-defi-rollout`.
```

#### Tab 5 — `lending-indices-bugfix-tab` ✅ DONE 2026-05-08 (P0, MTDS + instruments-service)

- **Verified by main 2026-05-08 06:00 UTC** — all 3 cited commits exist + pushed to origin; issue doc has
  DONE-2026-05-08 block. P0 blocker for `carry_staked_basis` cleared ahead of Ikenna's D4 launches.
- **Code commits** (all pushed to origin per conditional rule):
  - `instruments-service@1a90185` — Bug 3 fix: `get_protocol_floor_date()` now uses UAC `PROTOCOL_LAUNCH_DATES` as SSOT
    (architectural fix — replaces hard-coded floor with cross-cutting source).
  - `mtds@d2f365e` — Bugs 1 + 2: lending-indices subgraph schema drift discipline (AAVE V3 ETH silent-zero + Compound V3
    schema drift).
  - `mtds@de9d5cf` — ruff format spacing fix on lending_indices_handler.
- **QG**: agent reports clean on Tab 5's own code; pre-existing failures on parallel agents' code exempt per CLAUDE.md
  temporary 2026-05-07 → 2026-05-09 exception.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 5 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. plans/active/issues/lending_indices_handler_bugs_2026_05_07.md — your plan-of-record
     (full bug evidence + suggested fixes).
  4. plans/active/defi_master_2026_05_07.md § "Lending-indices VM run-quality bugs" —
     parent context.

Your agent-tag: lending-indices-bugfix-tab. Your tab number: 5.

YOUR TASK: ship the 3 bug fixes documented in lending_indices_handler_bugs_2026_05_07.md:

* Bug 1 — AAVE V3 ETHEREUM silent-zero (subgraph routing config error in
  market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py).
* Bug 2 — Compound V3 schema drift (GraphQL query update).
* Bug 3 — instruments-service DeFi instrument-discovery launch-date floor handling
  (architectural — read the issue doc carefully before proposing the fix).

Bugs are independent — ship them in 3 separate commits. Per CLAUDE.md HARD RULE: commit per
shippable unit. Push per the conditional rule (fetch + zero incoming → push; any incoming →
flag in your plan-of-record's `## Open questions`).

REPOS OWNED: market-tick-data-service, instruments-service.

DONE-DEFINITION:
- [ ] All 3 bugs fixed with unit tests covering the regression cases.
- [ ] `cd market-tick-data-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] `cd instruments-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] Issue doc updated to RESOLVED with `<repo>@<sha>` evidence per bug.
- [ ] DONE-2026-05-08 block at the bottom of the issue doc.

REPORT-BACK: code commits + plan-flip commit per shippable unit; conditional push.
```

#### Tab 6 — `defi-988-audit-tab` ✅ DONE 2026-05-08 (diagnostic-only, PM only)

- **Verified by main 2026-05-08 06:02 UTC** — audit doc filed (17,298 bytes substantial output) + defi_master annotated;
  PM@fc52188 pushed.
- **Code commits**: `PM@fc52188` — `docs(defi-988-audit): file Tab 6 actionable breakdown + annotate defi_master`.
- **Output**: [`issues/defi_988_missing_dates_audit_2026_05_08.md`](issues/defi_988_missing_dates_audit_2026_05_08.md) —
  per-(chain, protocol, data_type) breakdown probed across 10 DeFi GCS manifest buckets (9 v5 + 1 legacy) cross-checked
  against UAC `CHAIN_GENESIS_DATES` + `PROTOCOL_LAUNCH_DATES` SSOTs. **Headline: 13,632 actionable rows of 1.3M
  non-captured** (the original "988 dates missing" framing was misleading — most non-captured rows are legitimate
  pre-genesis / pre-launch). Top-5 priority list for D4 backfill listed in the audit doc.
- **Implication for D4 manifest rescan**: Harsh-side cross-asset rescan can now target the 13,632 actionable rows
  specifically rather than blanket-rescanning DeFi.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 6 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. plans/active/defi_master_2026_05_07.md § "Tail-chain / mid-tier protocol coverage
     (DeFi data-status — 988 dates missing)" — your plan-of-record context.
  4. unified_api_contracts.canonical.crosscutting.chain_genesis SSOT (CHAIN_GENESIS_DATES).
  5. unified_api_contracts.canonical.domain.defi.protocol_launch SSOT (PROTOCOL_LAUNCH_DATES).

Your agent-tag: defi-988-audit-tab. Your tab number: 6.

YOUR TASK: produce a per-(chain, protocol, data_type) breakdown of the 988 missing DeFi dates,
ranked by relevance to the May-23 archetypes (carry_staked_basis lead, leveraged_funding_arb).

This is DIAGNOSTIC ONLY — no code changes. Output is a new markdown doc:
plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md (file an issue doc per the
Findings Triage Discipline issue-doc format in CLAUDE.md).

Approach (suggested):
1. Read the canonical DeFi manifest at gs://market-data-tick-defi-central-element-323112/
   _index/availability_index.parquet (use unified_cloud_interface).
2. Filter to capture_status ∈ {empty_confirmed, attempted_failed, expected_unattempted}.
3. Cross-check against CHAIN_GENESIS_DATES + PROTOCOL_LAUNCH_DATES — anything pre-genesis
   should be empty_confirmed[EXPECTED_PRE_GENESIS_CHAIN] (legitimate); anything else is
   actually-missing.
4. Group remaining missing rows by (chain, protocol, data_type), count, sort by relevance to
   carry_staked_basis (Ethereum + Solana + Arbitrum + Base, focus on AAVE V3 / Lido / Rocket
   Pool / Jito / Marinade / Pyth / Chainlink) and leveraged_funding_arb (perp DEXes).
5. Write the audit doc with the breakdown table + top-5 priority list for D4 backfill.

REPOS OWNED: unified-trading-pm (issue doc only).

DONE-DEFINITION:
- [ ] plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md filed with breakdown table.
- [ ] Top-5 priority list for D4 backfill action.
- [ ] Linked from defi_master plan body's "Tail-chain coverage" section (one-line annotation).
- [ ] DONE-2026-05-08 block at the bottom of the audit doc.

REPORT-BACK: 1 commit (issue doc) + 1 commit (defi_master annotation); conditional push.
```

#### Tab 7 — `mtds-databento-streaming-tab` ✅ DONE 2026-05-08 (pure-win refactor, MTDS only)

- **Verified by main 2026-05-08 06:08 UTC** — both cited commits exist + pushed; QG Pass 1 lint+tests green per agent
  report. Phases 2-4 correctly left unshipped per plan body's gate conditions.
- **Code commits** (both pushed to origin):
  - `mtds@d8358f9` — `feat(mtds): databento path-streaming + chunked to_df (Phase 1)` — replaces eager BytesIO
    - DBNStore.to_df() materialisation in `download_batch_df` with SDK-supported `path=<tempfile>` +
      `DBNStore.to_df(count=N)` chunked iteration. Bounds peak working-set memory for heavy CME GLBX.MDP3 ES.OPT days
      that previously spiked >1GB.
  - `PM@ace8d3f` — `plan(mtds-databento-path-streaming): flip Phase 1 checkbox + DONE-2026-05-08 block`.
- **Caveat per agent**: codex violations on untouched files are pre-existing (not Tab 7's code) — exempt per CLAUDE.md
  temporary 2026-05-07 → 2026-05-09 QG-failure exception.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 7 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. plans/active/mtds_databento_path_streaming_2026_05_07.md Phase 1 — your plan-of-record.

Your agent-tag: mtds-databento-streaming-tab. Your tab number: 7.

YOUR TASK: implement Phase 1 of mtds_databento_path_streaming_2026_05_07.md — chunked
streaming for Databento `get_range` responses to bound peak memory.

Refactor scope (per the plan body's 5 migration steps):
* market-tick-data-service/market_tick_data_service/adapters/databento_adapter.py — switch
  eager `to_df()` materialisation to `path=<tempfile>` + chunked `to_df(count=N)` iteration.
* Output is byte-identical to the current path (verify via parquet row-count + checksum tests
  on a fixture day).
* Tests: 5 unit tests covering the chunked iteration path (per plan body).

REPOS OWNED: market-tick-data-service.

DONE-DEFINITION:
- [ ] databento_adapter.py refactored to chunked streaming.
- [ ] 5 unit tests pass.
- [ ] `cd market-tick-data-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] Manual smoke: heavy-day fixture (or memory-profile run on a sample) shows bounded peak.
- [ ] Plan flips: Phase 1 todos `- [ ]` → `- [x]` with `<repo>@<sha>` evidence.
- [ ] DONE-2026-05-08 block at the bottom of the plan body.

REPORT-BACK: 5-6 small commits per CLAUDE.md cadence; conditional push.
```

#### Tab 8 — `audit-followups-tab` ✅ DONE 2026-05-08 (plan hygiene, PM only)

- **Verified by main 2026-05-08 05:56 UTC** — all 4 cited commits exist + are pushed to origin/live-defi-rollout; 16
  checkboxes flipped across the 6 anomalies + validation pass + follow-ups.
- **Code commits** (PM, all pushed to origin per conditional rule):
  - `PM@8286cf4` — fix anomaly #1 (stale defi_e2e_pipeline / leveraged_leg_controller / defi_pipeline_extension refs in
    master plan replaced with `defi_master_2026_05_07`).
  - `PM@8d33d97` — fix anomaly #3 (re-derive plan counts in master work-stream-G).
  - `PM@b9593b2` — fix anomaly #5 (reconcile infrastructure_master STALE count to actual + strategy_architecture_v2
    Phase 3 OPS items).
  - `PM@728a63f` — flip §1-§6 + validation checkboxes + DONE-2026-05-08 block in plan body.
- **Plan-flip**: handled in `728a63f` directly.
- **Going quiet** per spawn protocol — won't pick up new work autonomously.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 8 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. plans/active/audit_followups_2026_05_07.md items #1-#6 — your plan-of-record.

Your agent-tag: audit-followups-tab. Your tab number: 8.

YOUR TASK: ship the 6 line-edit fixes in audit_followups_2026_05_07.md (stale plan
references, archived plan listings, module path drifts, STALE markers). Each item has a
specific file:line + the exact fix described in the plan body. Pure mechanical work.

REPOS OWNED: unified-trading-pm (plan files + codex docs).

DONE-DEFINITION:
- [ ] All 6 items shipped.
- [ ] Each item's checkbox flipped `- [ ]` → `- [x]` in the plan body with `PM@<sha>` evidence.
- [ ] DONE-2026-05-08 block at the bottom of the plan body.
- [ ] Pre-commit prettier auto-format passes.

REPORT-BACK: 1-2 commits (small scope); conditional push.
```

#### Tab 3 — deployment-api Phase 2 endpoints ✅ DONE 2026-05-08 (P0, single repo)

**Status**: Spawned + completed in one session. Six checkboxes flipped + DONE-2026-05-08 block in plan body.

- **Code commits** (deployment-api, pushed to origin by operator):
  - `cade1e1` — POST /api/backfill/launch + 11 unit tests + main.py wire (work-stream-A 2.A)
  - `bae88fb` — GET /api/vm/events + 13 unit tests + main.py wire (work-stream-A 2.B)
  - `7f60c5c` — refactor: QG lint clean + workspace os.environ rule
  - `782cce5` — test: move work-stream-A tests to tests/unit/ + collection-order workarounds
- **Plan-flip commit** (PM, local-only): `d53fb09` — flips Phase 2 + Phase 3 checkboxes.
- **QG status**: lint clean, basedpyright clean, coverage 70.84% (gate 70%). 1 pre-existing failure on another agent's
  `data_status_service.py:1689` (UAC EMPTY_CONFIRMED_REASONS drift) — exempt per CLAUDE.md temporary 2026-05-07 →
  2026-05-09 QG-failure exception.

(Spawn prompt below preserved for the template / future re-spawn reference; Tab 3 itself is closed out.)

**Why this first today**: Harsh-D3 P0 pulled forward to D2 — UAC types (Phase 1 prerequisite) shipped early at
`UAC@a70b3f6`, so the path is unblocked. Lands the two new endpoints (`POST /api/backfill/launch`

- `GET /api/vm/events`) which (a) unblock Ikenna's D4 DeFi launches via the new API and (b) unblock Harsh's own D5 DART
  Playwright matrix verification. Critical-path multiplier.

**Agent-tag suggestion**: `deployment-api-phase2-tab` (use this in any `_agent_pings.md` entries).

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 3 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1, a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  4. plans/active/deployment_api_work_stream_a_2026_05_07.md Phase 2 — your plan-of-record.

Your agent-tag for ping-ledger entries: `deployment-api-phase2-tab`.
Your tab number: 3.

The boot section in the orchestration ledger covers everything on workflow: shared working tree,
push discipline (conditional — push iff zero incoming on origin; flag for main + operator
review otherwise), Q&A flow via plan-of-record + ping ledger, plan-doc curation (checkbox
flips per shippable unit, DONE block on completion), findings triage. Read it once and follow.

ORCHESTRATION RULES:
1. **Shared working tree** — main agent's HEAD and your HEAD are identical (same .git/). No
   `git pull` needed between tabs; another agent's local commit is visible to you the moment
   it lands. BUT: pre-commit check is critical — before EVERY commit, run:
       git status                 # full picture
       git diff --cached --stat   # NO PATH ARG — see entire index
   If anything in the staged set or working tree isn't yours, surgically un-stage
   (`git restore --staged <file>`) or stash (`git stash --keep-index`) before committing.
   Never `git add <whole-file>` if anyone else touched it — use `git add -p` for your hunks.
2. If you hit ambiguity / a blocker / a decision that needs Harsh's strategic input:
   a. Write the full question in plans/active/deployment_api_work_stream_a_2026_05_07.md's
      `## Open questions` section (status 🟡 BLOCKED). That plan doc is YOUR plan-of-record —
      NOT work_split or the orchestration ledger.
   b. Append a one-liner to plans/active/_agent_pings.md with timestamp + your agent-tag
      (deployment-api-phase2-tab) + a 5-10 word summary + plan-doc pointer.
   c. Optionally commit both LOCALLY (don't stress; Q&A commits are nice-to-have, not required).
   d. Continue with anything you CAN do — don't block waiting. Main polls the ping ledger every
      ~1 min, will write A1 into the plan doc + flip 🟡 → ✅ + remove the ping line. You pick up
      the answer on your next read of the plan doc (shared working tree → no `git pull` needed).
   e. Do NOT message Harsh directly unless your finding is case-5 (big) per Findings Triage
      Discipline. The main agent is your conversational dispatcher.
3. Read unified-trading-pm/cursor-configs/CLAUDE.md for workspace rules — especially
   "Findings Triage Discipline", "Commit + Push + Flip Plan Checkboxes (HARD RULE)",
   "Two teammates × multiple parallel agents", and the per-asset-group shard-key matrix.
4. **Per shippable unit: commit (LOCALLY) + flip the matching plan checkbox in the same
   logical unit.** Push follows the conditional rule: before pushing, `git fetch origin
   <branch>` + check for incoming. Zero incoming → push freely. Any incoming → DON'T push,
   write a `🟡 BLOCKED` entry in your plan-of-record's `## Open questions` for collaborative
   resolution (rebase / merge / cherry-pick) by main + operator. Commit cadence is unchanged
   (per CLAUDE.md HARD RULE — 5-6 small commits, NOT one mega-commit).
5. Findings Triage Discipline (HARD RULE) — any side-discovery during execution: classify
   case-1-to-5 per CLAUDE.md and route appropriately. Big findings (case 5) → file an issue
   doc in plans/active/issues/. Small QG-failure findings on someone else's code are EXEMPT
   until ~2026-05-09 per the temporary exception in CLAUDE.md.

YOUR TASK:

Implement Phase 2 of plans/active/deployment_api_work_stream_a_2026_05_07.md (lines 154+) —
two new deployment-api endpoints. Phase 1 (UAC types) shipped at UAC@a70b3f6 — verified
importable via:
  from unified_api_contracts.internal import (
      BackfillLaunchRequest, BackfillLaunchResult,
      VMLifecycleEvent, VMEventListResult, BackfillLaunchTaskKind,
  )

Read the plan body Phase 2 section in full before coding — it has the complete behavioural
contract for both routes. Summary below for orientation only:

1. POST /api/backfill/launch — deployment-api/deployment_api/routes/backfill_launch.py
   - Auth: verify_api_key (X-API-Key) via _authenticated_router in main.py.
   - Validate body via BackfillLaunchRequest (UAC).
   - Resolve task → launcher script via inline closed-set _TASK_TO_LAUNCHER dict. Unknown → 400.
   - vm_name = f"{prefix}-{run_ts}" (run_ts = UTC YYYYMMDD-HHMMSS). Validate prefix against
     VM_PREFIX_TO_BUCKET from deployment-service/scripts/vm/vm_zombie_watchdog.py:113 —
     unknown prefix → 400 with the registration instructions from CLAUDE.md
     "VM Naming Convention".
   - Build env / metadata: VM_NAME, MANIFEST_PER_VM_SHARDS=true (always — concurrency rule),
     VM_FORCE, SKIP_DEPENDENCY_CHECK, RUN_TS, VM_FORCE_WINDOW, plus task-specific (VM_VENUE,
     VM_START_DATE, VM_END_DATE, VM_DATA_TYPES, VM_INSTRUMENT_IDS, VM_ASSET_GROUP).
   - subprocess.run(argv, env=..., shell=False, capture_output=True, text=True, timeout=600).
     timeout → 504 with LAUNCH_TIMEOUT event.
   - Emit VM_LAUNCH_REQUESTED before shelling; VM_LAUNCHED / VM_LAUNCH_FAILED after.
   - Shard-level failure isolation: no raise inside the launcher loop. Errors classified via
     classify_venue_error (UAC) where applicable; non-classified subprocess errors →
     VM_LAUNCH_FAILED event + 5xx response.
   - Production guard: if _cfg.is_mock_mode() OR request.dry_run → return BackfillLaunchResult
     with dry_run=True and resolved argv reflected back, never calling subprocess.

2. GET /api/vm/events — deployment-api/deployment_api/routes/vm_events.py
   - Read events from gs://{gcp_project_id}-events/events/{service}/{YYYY-MM-DD}/{vm-name}/hour={H}/*.jsonl.
     SSOT for the bucket-name pattern: unified-trading-library/unified_trading_library/feature_service_base/base_service.py:159.
   - Query params: vm_name (required), service (required), date (default today UTC), from_hour
     / to_hour (default 0..23), severity_floor (INFO|WARNING|ERROR|CRITICAL — default INFO),
     page_size (default 1000, max 5000), next_page_token.
   - Return VMEventListResult with events: list[VMLifecycleEvent]. Honour truncated +
     next_page_token for pagination.
   - Use unified_cloud_interface.get_storage_client() — NEVER `from google.cloud import storage`.
   - In mock mode: read fixture JSONL from deployment-api/tests/fixtures/vm_events_sample.jsonl
     (sample taken verbatim from gs://central-element-323112-events/instruments-service/2026-05-07/
     af-backfill-20260507-002914/hour=00/*.jsonl per the plan's pre-audit footnote).

3. Wire both routes in deployment-api/deployment_api/main.py (lines 127-165 _authenticated_router):
     from .routes import backfill_launch, vm_events
     _authenticated_router.include_router(backfill_launch.router, prefix="/api/backfill", tags=["Backfill"])
     _authenticated_router.include_router(vm_events.router, prefix="/api/vm", tags=["VM"])

4. Integration tests:
   deployment-api/tests/integration/test_backfill_launch.py:
     - POST without X-API-Key → 401.
     - Bad task (enum mismatch OR unmapped) → 400.
     - Unknown vm-name prefix → 400 with helpful message.
     - Valid request dry-run → BackfillLaunchResult{dry_run=True, vm_name=prefix-run_ts, argv
       reflects all flags + env}.
     - subprocess.run monkeypatched in every test — gcloud is NEVER actually called.
   deployment-api/tests/integration/test_vm_events.py:
     - Missing vm_name → 400.
     - Valid query against fixture JSONL → VMEventListResult with all events parsed.
     - Pagination round-trip (page 1 → next_page_token → page 2) works.
     - Severity floor filters correctly.

REPOS OWNED (edit rights):
- deployment-api — all new files + main.py wire-in.

READ-ONLY DEPS (do NOT edit):
- unified-api-contracts — UAC types already shipped at a70b3f6; just import them.
- deployment-service — read scripts/vm/launch-*.sh and scripts/vm/vm_zombie_watchdog.py for
  VM_PREFIX_TO_BUCKET + launcher names. Do NOT modify any launcher.
- unified-trading-library — read feature_service_base/base_service.py:159 for events bucket
  name pattern. Do NOT modify.

COLLISION BOUNDARIES:
- Ikenna's parallel work today (per work_split): writegate Phase 2.A residual on MDPS +
  alerting Phase 2 on alerting-service. ZERO overlap with deployment-api source.
- main.py:127-165 _authenticated_router is shared — your include_router calls go after the
  existing block. If you spot a teammate's WIP added since you pulled, re-pull before pushing.
- Per CLAUDE.md mandatory pre-commit check: `git status` + `git diff --cached --stat` (no
  path arg) before EVERY commit — catches bundling teammates' staged work.

DONE-DEFINITION (verifiable bullets):
- [ ] backfill_launch.py + vm_events.py shipped behind verify_api_key; both routers wired.
- [ ] Integration tests green: auth, validation, dry-run, mock subprocess, fixture-based
      events, pagination round-trip.
- [ ] `cd deployment-api && bash scripts/quality-gates.sh` Pass 1 green (excluding pre-existing
      dirty-file failures from teammates — verify via git blame; YOUR new code must be green).
- [ ] Plan flips: plans/active/deployment_api_work_stream_a_2026_05_07.md Phase 2 todos
      `- [ ]` → `- [x]` with `<repo>@<sha>` evidence appended.
- [ ] Plan-flip commit in PM (LOCAL ONLY) with message
      `plan(deployment-api-work-stream-a): flip Phase 2 checkboxes (...)` referencing every
      code commit cited in the flips.
- [ ] 5-6 small commits per CLAUDE.md HARD RULE cadence (route 1 helpers, route 1
      + tests, route 2 helpers, route 2 + tests, main.py wire, plan flip), NOT one
      mega-commit. Push per the conditional rule (fetch + zero incoming → push;
      any incoming → flag in `## Open questions` for main + operator).

REPORT-BACK:
- Per shippable unit: code commit + plan-flip commit. Push per the conditional rule.
- Final: append a "DONE-2026-05-08" comment block at the bottom of
  plans/active/deployment_api_work_stream_a_2026_05_07.md body, listing every code +
  plan-flip commit sha. Main agent sees your commits immediately (shared .git/) via
  `git log --oneline live-defi-rollout`.
```

#### Tab 9 — `lending-indices-relaunch-tab` ✅ DONE 2026-05-08 — scope extended + validated end-to-end

- **Verified by main 2026-05-08 08:21 UTC** — VALIDATION-2026-05-08 block in
  [`issues/lending_indices_handler_bugs_2026_05_07.md`](issues/lending_indices_handler_bugs_2026_05_07.md); Tab 9 PM
  commit rebased + pushed as `e524ad7` to origin/live-defi-rollout. UAC + MTDS + IS fix commits also on origin
  (UAC@`6a64a56` + MTDS@`c6bdf96` + IS@`6ae50de`).
- **VM validation result at T+123min**: AAVE V3 ETH captured rows start exactly **2023-01-27** (53 captured rows over
  2023-01-27 → 2023-03-20). UAC fix end-to-end verified by real subgraph data — Bug 1 RESOLVED as a UAC SSOT
  misdiagnosis (NOT a code bug).
- **Going quiet** per spawn protocol.

(Original Tab 9 history preserved below for audit reference.)

#### Tab 9 (history) — scope extended to bug-fix (operational + code, ~30min + ~2-3h)

> **🟢 UAC `chain_env.py:146` FIX LANDED 2026-05-08 at UAC@`6a64a56`** — Tab 9's diagnosis shipped:
> `PROTOCOL_LAUNCH_DATES[("ETHEREUM", "AAVE_V3")]` `"2022-03-14"` → `"2023-01-27"`. **Coordination mirror in Ikenna's
> 5-tab layout § Cross-tab handshakes** (the gate is documented as a SHIPPED row there + an Agent 4 dependency note on
> the deferred lending-indices relaunch). **Pattern for future similar UAC SSOT fixes** (any `*_LAUNCH_DATES` /
> `*_GENESIS_DATES` / `SOURCE_COVERAGE_START` / `venue_trading_calendar`): any agent in flight on `chain_env.py` (or
> siblings) when a downstream tab is about to consume `PROTOCOL_LAUNCH_DATES` for VM launches MUST drop a top-of-file
> `🟡 IN-FLIGHT REFACTOR` banner per CLAUDE.md "Cross-Plan Coordination Banners" rule. Agent 4's deferred
> lending-indices relaunch + any future Agent 3 expected-universe enumerator re-runs that consume
> `PROTOCOL_LAUNCH_DATES` are now safe (corrected date is on `origin/live-defi-rollout`); operators MUST `git pull` UAC
> before relaunching.

- **Started**: 2026-05-08 06:12 UTC (STARTED ping ack'd by main; clean boot, no flags).
- **BLOCKED Q1 raised 06:43 UTC, RESOLVED 06:55 UTC** — operator approved scope extension.
- **Plan-of-record**:
  [`issues/lending_indices_handler_bugs_2026_05_07.md`](issues/lending_indices_handler_bugs_2026_05_07.md) Q1+A1.
- **Original scope**: refresh DEFI tarballs → relaunch VM → 90s STARTED + 10-15min progress + T+30min per-VM manifest
  spot-check → validate Bug 1 (AAVE V3 ETH) emits captured rows now. **Found Bug 1 still fires; root-caused to UAC SSOT
  being wrong (AAVE V3 ETH mainnet 2023-01-27, not 2022-03-14 as UAC says).**
- **Extended scope**: probe-verify UAC, correct chain_env.py:146 SSOT, add handler pre-floor-date short-circuit
  (writegate Phase 2.E taxonomy fix), re-frame Bug 1 as misdiagnosis, re-verify done-def.

**Why now**: Tab 5 fixed the 3 lending-indices P0 bugs this morning (instruments-service@1a90185 + mtds@d2f365e).
Relaunching the VM closes the loop with real data — proves Bug 1 reproducer (AAVE V3 ETHEREUM silent-zero) actually
emits non-zero rows now. Validates the fix end-to-end before Ikenna's D4 DeFi launches depend on lending-indices
working.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 9 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules, Q&A flow, plan-doc curation duties.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — esp. "No fire-and-forget VM launches"
     section (90s STARTED + 10-15min progress + STOPPED at exit, plus per-VM manifest shard
     spot-check for silent-zero detection).
  3. plans/active/issues/lending_indices_handler_bugs_2026_05_07.md — the 3 P0 bugs Tab 5
     just fixed (Bugs 1 + 2 + 3); this is what we're validating.
  4. plans/active/defi_master_2026_05_07.md § "Lending-indices VM run-quality bugs" —
     parent context.

Your agent-tag: lending-indices-relaunch-tab. Your tab number: 9.

YOUR TASK: relaunch the lending-indices backfill VM with Tab 5's fixes shipped, verify the
Bug 1 / Bug 2 / Bug 3 reproducers actually emit captured rows now (not silent-zeros).

STEPS:

1. Refresh tarballs for the relevant asset_groups (DEFI primarily):
     bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group DEFI
   This pulls Tab 5's instruments-service@1a90185 + mtds@d2f365e into the tarball that the
   VM will boot. Verify TARBALLS_REFRESHED event fires.

2. Relaunch the lending-indices VM:
     bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh
   (Same launcher as the failed run; check it's already singleton-locked so no concurrent
   relaunch. The previous VM mtds-lending-indices-20260507-140418 was stopped after diagnosis.)

3. 90-second STARTED check:
     gcloud storage ls gs://central-element-323112-events/events/market-tick-data-service/2026-05-08/<vm-name>/
   Confirm hour=H partition exists. Read first JSONL, assert event=="STARTED".

4. 10-15min progress check: read events under hour=H, look for INSTRUMENT_PROCESSED-class
   events with `rows_captured` > 0. Specifically:
   - AAVE V3 ETHEREUM (Bug 1 reproducer) — must show captured rows, not silent-zero.
   - Compound V3 (Bug 2 reproducer) — must show captured rows, not schema error.
   - Pre-launch-date filtering (Bug 3 reproducer) — must respect UAC PROTOCOL_LAUNCH_DATES.

5. Per-VM manifest shard spot-check at T+30min:
     gs://lending-indices-central-element-323112/_index/per_vm/<vm-name>.parquet
   Read with pyarrow; verify capture_status distribution: expect ≥ 90% captured for the
   ETHEREUM AAVE V3 + Compound V3 rows, NOT 100% empty_confirmed (the pre-fix shape).

DONE-DEFINITION:
- [ ] VM launched + STARTED event observed within 90s.
- [ ] AAVE V3 ETH writes captured rows (sample at T+15min from per-VM shard).
- [ ] Compound V3 writes captured rows (sample at T+15min).
- [ ] Pre-launch-date dates correctly empty_confirmed[EXPECTED_PRE_GENESIS_CHAIN] or
      record_expected_unattempted, NOT silent-zero captured.
- [ ] Status note appended to plans/active/issues/lending_indices_handler_bugs_2026_05_07.md
      below the existing DONE-2026-05-08 block: "VALIDATION-2026-05-08 — VM relaunched as
      <vm-name>; sample at T+30min confirms <N> captured rows for AAVE V3 ETH, <M> for
      Compound V3, all 3 bugs verified fixed end-to-end."
- [ ] If ANY reproducer still silent-zeros: write a 🟡 BLOCKED entry in the issue doc's
      `## Open questions` section + ping main; do NOT mark fixes as validated.

REPORT-BACK: 1 commit (validation note); push per conditional rule (fetch + zero incoming).
```

#### Tab 10 — `predictions-phase1-ingestion-tab` ✅ DONE 2026-05-08 (P1, instruments-service + MTDS)

- **Verified by main 2026-05-08 06:55 UTC** — all 5 cited commits exist + pushed to origin (instruments-service 0/0, PM
  0/0). Phase 2 (MTDS adapter migration + reader/feature/strategy) explicitly deferred per plan body's "Temporary
  states + their canonical follow-up plans" section — that's the durable state, not a punt.
- **Code commits** (all pushed to origin):
  - `instruments-service@98bb167` — Polymarket + Kalshi adapter `classify_lifecycle()` + `get_market_lifecycles()`
    returning per-market `MarketLifecycle` rows; `available_from_datetime` / `available_to_datetime` stamped on
    `InstrumentRecord` + 14 unit tests.
  - `instruments-service@b904785` — Orchestrator `_extract_prediction_canonical_group()` calls UAC classifier; writer at
    `engine/orchestrator.py:2128` bundles by `canonical_question_group`; manifest emits
    `data_type=prediction_canonical_question_group` + `underlying={GROUP}` per UAC `BUNDLED_DATA_TYPES` SSOT + 9 unit
    tests; full 2267-test suite green.
  - `PM@7343b93` + `PM@8526f99` — plan checkbox flips + DONE-2026-05-08 block + "Temporary states" section naming Phase
    2 follow-ups (MTDS Polymarket/Kalshi adapter lifecycle gating; data_type rename in `umi_tick_provider.py:225` +
    `orchestrator.py:1990-1995`; MARKET_LIFECYCLE separate parquet; per-market_id manifest rows + cluster-coverage
    gate).
  - `PM@8bd1991` — DONE ping in `_agent_pings.md`.
- **What's next** (Phase 2 — explicitly deferred):
  - MTDS Polymarket / Kalshi adapter lifecycle gating (skip ticks outside [created_at, settlement_time]).
  - UMI tick provider `data_type` rename to `prediction_canonical_question_group`.
  - Per-market_id manifest rows + cluster-coverage gate.
  - Reader / feature / strategy consumer migration.

**Why now**: Phase 1A scaffolding shipped 2026-05-07 — UAC `canonical_question_group` SSOT (UAC@af2bc9b), Polymarket
lifecycle aliases (UAC@58cc5f8), `DATA_TYPE_TO_CLUSTER_REGISTRY` (UAC@bb24aba). Phase 1 ships the actual ingestion.
Gates Phase 2 (adapter migration) + Phase 3 (reader/feature/strategy) of predictions_master entirely.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 10 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — esp. "Prediction market lifecycle timing"
     section (lifecycle bounds + cluster validation per canonical_question_group).
  3. plans/active/predictions_master_2026_05_07.md Phase 1 — your plan-of-record.
  4. UAC SSOTs already shipped (Phase 1A): UAC@af2bc9b (canonical_question_group SSOT +
     lifecycle wrapper modules), UAC@58cc5f8 (Polymarket aliases + edge-case tests),
     UAC@bb24aba (DATA_TYPE_TO_CLUSTER_REGISTRY + PREDICTION_GROUPS empty registry).

Your agent-tag: predictions-phase1-ingestion-tab. Your tab number: 10.

YOUR TASK: implement Phase 1 lifecycle ingestion of predictions_master Phase 1 — the actual
writer + orchestrator wiring (Phase 1A was scaffolding only).

REPOS OWNED:
- instruments-service (writer for prediction market lifecycle timestamps).
- market-tick-data-service (orchestrator shard-atom emit; Polymarket adapter lifecycle gating
  if shippable in Phase 1, else defer to Phase 2 per plan body).

Scope (read predictions_master Phase 1 body for the full contract):
- instruments-service Polymarket / Kalshi adapter writes per-market_id lifecycle timestamps
  (`market_created_at`, `resolution_time`, `settlement_time`) + canonical_question_group
  membership per the UAC SSOT.
- MTDS orchestrator reads the lifecycle metadata + emits shard-atom keyed on
  `(asset_group=prediction, venue, data_type, canonical_question_group, day)` per the
  CLAUDE.md "Per-asset-group shard-key matrix" section.
- Integration tests: a recurring HOURLY canonical group (e.g. BTC_UP_DOWN_HOURLY) cycling
  through 24 market_ids in a day asserts cluster validation (HOURLY → 24 clusters expected).
- Lifecycle bounds in MTDS CLOB capture: NO ticks before `market_created_at`, NO new ticks
  after `settlement_time` (per the CLAUDE.md rule).

Phase 2 + 3 are explicitly deferred per the work_split's "Defer post-May-23" + the plan's
phase ordering — do NOT proceed past Phase 1 lifecycle ingestion in this session.

DONE-DEFINITION:
- [ ] instruments-service writes per-market_id lifecycle timestamps + canonical_question_group
      membership; existing Polymarket / Kalshi adapter migrated.
- [ ] MTDS orchestrator emits shard-atom on the canonical_question_group axis (verified by
      reading the manifest shard and asserting `canonical_question_group` populated).
- [ ] Lifecycle bounds enforced at MTDS CLOB capture (no ticks outside [created, settlement]).
- [ ] Integration test: HOURLY canonical group cluster validation passes.
- [ ] `cd instruments-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] `cd market-tick-data-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] Plan flips: predictions_master Phase 1 todos `- [ ]` → `- [x]` with `<repo>@<sha>`.
- [ ] DONE-2026-05-08 block at the bottom of predictions_master plan body.

REPORT-BACK: 5-8 small commits per CLAUDE.md cadence; push per conditional rule.
```

#### Tab 11 — `launcher-consolidation-tab` ✅ DONE 2026-05-08 (mechanical, deployment-service + e2e-testing + features-sports-service)

- **Verified by main 2026-05-08 07:42 UTC** — all 14 cited commits exist + pushed to their respective origins
  (deployment-service 7, e2e-testing 6, features-sports-service 1); deployment-service repo at 0/0. Spawn target met (10
  launcher migrations shipped, with 3 helper wrappers = 13 new files under `scripts/vm/`).
- **Code commits** (all pushed to origin per conditional rule):
  - **deployment-service** `76f4ecc` (mtds), `fbb3673` (instruments), `0215086` (features-sports-parallel), `2e1d967`
    (mtds-sports-odds), `fc9211e` (sports-instruments-reference), `5778811` (3 DeFi launchers #6-8: dex-pools /
    eigenlayer-rewards / solana-drift), `ce99d43` (#9-10: cefi-migration + defi-backfill).
  - **e2e-testing** `8daba1a` `2da6867` `deff088` `db7ace3` `43d8e49` `4f1f92b` — deprecation banners on moved sources
    (10 banners across 6 commits).
  - **features-sports-service** `06f6b30` — deprecation banner on `launch_parallel_backfill.sh`.
  - **PM** `fc35b11` — Tab 11 audit + top-10 selection (Phase 0 flip).
- **Wave-flip status (honest, partial-by-design)**: Wave A ✅ (4 scripts, common/) + Wave E ✅ (1 script,
  features-sports/parallel-backfill); Waves B+D PARTIAL (top-10 selection cherry-picked from across these waves rather
  than completing waves in order — sensible since deferred items are mostly known-duplicates); Wave C DEFERRED (Tab 10
  collision-avoid on prediction surface).
- **Critical-path impact**: 2 of 3 missing-on-disk `_SERVICE_LAUNCHER_SCRIPTS` registry entries now backed by real
  launchers (market-tick-data-service + instruments-service). Deploy-Missing UI button no longer silently breaks for
  those two services.
- **Watchdog VM**: relaunched as `vm-zombie-watchdog-20260508-121344` after all 17 new prefix entries landed in
  `VM_PREFIX_TO_BUCKET`.
- **Smoke tests**: every migrated launcher with `--dry-run` smoke-tested (#1-#8, #10); #9 (cefi-migration) `bash -n`
  syntax check only (no `--dry-run` flag in source).
- **Deferred to follow-up cycles**: features-onchain launcher (no e2e-testing equivalent — needs fresh build, P1); 7
  DeFi launcher duplicates (delete-vs-merge reconciliation needed); 4 prediction launchers (Tab 10 collision-avoid); 8
  sports launchers (partially superseded by canonical equivalents); 1 intra-repo move; callsite-update sweep
  (deprecation banners cover transition window).

**Why now**: D4 P2 in the work_split. 30 ad-hoc VM launchers under `e2e-testing/scripts/` +
`features-*-service/scripts/` are technical debt (per CLAUDE.md "VM launcher script SSOT" rule — all launchers MUST live
under `deployment-service/scripts/vm/`). Migrating 10 of 30 in this cycle makes Deploy-Missing UI work for those
services + cleans up the workspace.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 11 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — esp. "VM launcher script SSOT (codified
     2026-05-07)" section (the SSOT rule + 4 ways scripts reach the VM + how to add a new
     launcher) + "VM Naming Convention" section (VM_PREFIX_TO_BUCKET registry).
  3. plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md —
     your plan-of-record.
  4. deployment-service/scripts/vm/vm_zombie_watchdog.py:113 — VM_PREFIX_TO_BUCKET dict (must
     be updated for every new launcher prefix).

Your agent-tag: launcher-consolidation-tab. Your tab number: 11.

YOUR TASK: migrate 10 of 30 ad-hoc launchers from `e2e-testing/scripts/` +
`features-*-service/scripts/` into `deployment-service/scripts/vm/`.

REPOS OWNED:
- deployment-service (target — new launchers under scripts/vm/ + VM_PREFIX_TO_BUCKET updates).
- e2e-testing, features-sports-service, features-onchain-service (source — read-only).

Selection rule (pick the 10 that matter most for May-23):
- Anything called by an active (running) backfill or audit operation today is HIGH priority.
- Anything referenced by a plan in plans/active/ critical-path is HIGH priority.
- Anything that hasn't been used in 7+ days is LOW priority (defer post-May-23).

For each migrated launcher:
1. Move the script into deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh.
2. Add the VM-name prefix to VM_PREFIX_TO_BUCKET in vm_zombie_watchdog.py:113 (with the right
   shard bucket, or None for heartbeat-only).
3. If it should be reachable from the Deploy-Missing UI button, register it in
   _SERVICE_LAUNCHER_SCRIPTS in deployment-api/deployment_api/services/deploy_missing.py.
4. Smoke-test via `bash deployment-service/scripts/vm/launch-X-vm.sh --dry-run` (or equivalent
   if the launcher doesn't have --dry-run).
5. Add a deprecation banner to the OLD location (NOT delete — leave a comment pointing at the
   new location for any operators with a tab open on the old path; deletion in next cycle).
6. After updating VM_PREFIX_TO_BUCKET: relaunch the watchdog VM per CLAUDE.md "VM Naming
   Convention" rule (the running watchdog only fetches the Python at boot).

Coordination — pre-commit check is critical here (you may share working tree with other agents):
- git status + git diff --cached --stat (no path arg) before EVERY commit.
- Use `git add -p` for any shared files (vm_zombie_watchdog.py is shared).

DONE-DEFINITION:
- [ ] 10 launchers migrated to deployment-service/scripts/vm/.
- [ ] VM_PREFIX_TO_BUCKET updated for each new prefix; vm_zombie_watchdog VM relaunched.
- [ ] _SERVICE_LAUNCHER_SCRIPTS updated for any launcher that should be reachable from the UI.
- [ ] Old locations have deprecation banner comments pointing at new paths.
- [ ] `cd deployment-service && bash scripts/quality-gates.sh` Pass 1 green.
- [ ] Plan flips: launcher_scripts_consolidation_into_deployment_service plan body — 10
      checkbox flips with `<repo>@<sha>` evidence.
- [ ] DONE-2026-05-08 block at the bottom of the plan body.

REPORT-BACK: 10 small commits per CLAUDE.md cadence (1 per launcher migration); push per
conditional rule.
```

#### Tab 12 — `ml-features-phase2a-tab` ✅ DONE 2026-05-08 — DEFERRED per features-repo-consolidation absorption

- **Resolved by main + operator 2026-05-08 ~10:30 UTC** — Tab 12's Q1 (scope ambiguity) escalated to operator during
  lunch; resolved with operator pick **(b) Defer**. See A1 in
  [`ml_and_features_master_2026_05_07.md`](ml_and_features_master_2026_05_07.md) `## Open questions` Q1 for full
  reasoning.
- **Why deferred (stronger than Tab 12's original (b))**: Ikenna's plan consolidation (PM@`78918e1`) shipped
  [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md) (P0, deadline 2026-05-13)
  which **restructures the per-service approach itself**. Phase 5 of consolidation lifts
  `assert_no_lookahead_for_feature_group` into UTL `feature_service_base/` at the consolidated `features-service` layer
  — single point, not 8 per-service wires.
- **Tab 12 deliverable preserved**: the per-service compute-boundary inventory map (what Tab 12 worked on during the
  lunch-break wait) is durable input for `features_repo_consolidation_2026_05_08` Phase 0 pre-audit + Phase 5 lift.
  Cross-reference from the consolidation plan to consume.
- **Started**: 2026-05-08 07:41 UTC; **Q1 raised**: 07:50 UTC; **Q1 resolved**: ~10:30 UTC. **Going quiet** per spawn
  protocol.

**How to start**: open a fresh Claude Code tab, tell that agent _"work on Tab 12 tasks"_.

**Why now**: UAC `feature_group → required_inputs` SSOT shipped 2026-05-07 (UAC@4a25b07). Phase 2A wires the 8
features-\* / MDPS / strategy services to consume it via UTL `assert_no_lookahead_for_feature_group` helper.
Workspace-wide ratchet — once shipped, every feature compute becomes lookahead-bias-checked at runtime.

**Caveat — collision risk on MDPS**: Ikenna's writegate Phase 2.A residual touches MDPS `batch_workers` /
cluster-coverage wiring / `_write_manifest_records` deletion (writer-layer files). Tab 12 touches MDPS feature compute
calculators (different layer, different files). **File-level overlap is expected to be zero**, but both are in MDPS — so
per-commit pre-commit check (`git status` + `git diff --cached --stat` no path arg + `git add -p` for any shared file)
is critical. If `git status` shows unexpected MDPS-writer-layer changes from Ikenna while you're staging, those are NOT
yours — surgically exclude with `git restore --staged <file>` before commit.

**Tab 11 (launcher consolidation) finished 07:42 UTC** — no longer a collision concern.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 12 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — esp. "Shard-granularity SSOT" section
     ([UAC] + [UTL] + [per-service] layer discipline) + "LookaheadBiasError raised loud at
     every features-* + MDPS compute, not warn-mode" rule.
  3. plans/active/ml_and_features_master_2026_05_07.md Phase 2A — your plan-of-record.
  4. UAC SSOT shipped (Phase 1A): UAC@4a25b07 (32 feature_groups + 5-service registry +
     6 onchain coverage_starts + 15 tests).
  5. UTL helper shipped: UTL@4354276 (assert_no_lookahead_for_feature_group helper + 9 tests).

Your agent-tag: ml-features-phase2a-tab. Your tab number: 12.

YOUR TASK: wire the 8 services that compute features into the UTL
`assert_no_lookahead_for_feature_group` helper, so every feature compute call validates inputs
against the UAC `feature_group → required_inputs` DAG at runtime.

REPOS OWNED (8 services):
- features-onchain-service
- features-sports-service
- market-data-processing-service (MDPS — features-cefi / features-tradfi compute lives here)
- strategy-service (strategy archetype compute consumes feature_groups)
- + 4 others per the plan body — read it for the full list.

For each service:
1. Identify the per-service feature compute entry point (typically `compute_<feature_group>` or
   a calculator class method).
2. Add a call to `assert_no_lookahead_for_feature_group(feature_group_name, inputs, target_ts)`
   at the top of the compute method, BEFORE any tick reads.
3. Strict-mode raise (per CLAUDE.md rule) — NOT log-and-continue.
4. Add a unit test that asserts the helper fires for a deliberately-stale input.

Pre-commit check is CRITICAL (you're touching 8 services in 1 tab):
- git status + git diff --cached --stat (no path arg) before EVERY commit.
- Commit per service (8 small commits, NOT one mega-commit).

DONE-DEFINITION:
- [ ] All 8 services wired with assert_no_lookahead_for_feature_group at compute entry.
- [ ] Per-service unit test asserting strict-mode raise on stale input.
- [ ] `cd <repo> && bash scripts/quality-gates.sh` Pass 1 green for each of 8 repos.
- [ ] Plan flips: ml_and_features_master Phase 2A todos `- [ ]` → `- [x]` with `<repo>@<sha>`.
- [ ] DONE-2026-05-08 block at the bottom of ml_and_features_master plan body.

REPORT-BACK: ≥8 small commits (1 per service); push per conditional rule.
```

#### Tab 13 — `deploy-missing-iam-proposal-tab` ✅ DONE 2026-05-08 (draft-only, PM only)

- **Verified by main 2026-05-08 07:35 UTC** — Tab 13's commits rebased onto origin cleanly (no file overlap with the 2
  incoming `98f1e16` + `6e952b6`). Tab 13's local-ahead SHAs after rebase: `6d44c73` + `fdc0bb9`. Push lands in main's
  next push (this commit).
- **Output** (no code changes — pure draft for operator review):
  - New section `### Phase 0 — IAM scope + audit log + rate limit proposal (DRAFT for operator review)` in
    deploy_missing plan body, between original Phase 0 todos and Phase 1.
  - **Proposal 1 (IAM scope)**: custom role `roles/customDeployMissingLauncher` with zone/subnet/
    image-family/runtime-SA scoping + per-launcher allow-list, vs blanket `roles/compute.instanceAdmin.v1`.
  - **Proposal 2 (audit-log shape)**: schema dataclass + storage backend recommendation + retention.
  - **Proposal 3 (rate-limit ceiling)**: per-operator-per-hour + project-wide numbers + 429 response shape.
- **Phase 0 todos correctly left unchecked** until operator signs off on the proposals.
- **Unblocks**: deploy_missing Phase 2 (auto-launch endpoint) once operator picks IAM granularity.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 13 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules.
  2. plans/active/deploy_missing_auto_launch_2026_05_07.md — your plan-of-record;
     focus on Phase 0 (lines 126-132) + the "Pre-audit blast radius" Security-boundary
     review section (lines 49-67).
  3. unified-trading-pm/cursor-configs/CLAUDE.md — esp. "DeFi Execution Architecture"
     interface-credential section (gives shape to least-privilege thinking).

Your agent-tag: deploy-missing-iam-proposal-tab. Your tab number: 13.

YOUR TASK: draft the Phase 0 security review proposals for operator review. 3 audit todos:

1. **IAM scope decision**: propose the minimal IAM role for the deployment-api Cloud Run
   service to invoke `gcloud compute instances create`. Compare:
   - Blanket `roles/compute.instanceAdmin.v1` (too broad).
   - Narrower custom role with only the specific permissions (compute.instances.create,
     compute.instances.get, compute.instances.list, etc.) scoped to a specific zone +
     image family + subnet.
   - Per-launcher allow-listing (cross-reference `_SERVICE_LAUNCHER_SCRIPTS`).
   Output: a proposed custom role spec (YAML stanza or equivalent) + blast-radius analysis
   for each.

2. **Audit-log shape decision**: propose the audit-log record shape for every
   Deploy-Missing launch. At minimum: operator_email (from auth context), shard_key,
   launch_timestamp, resulting_vm_name, launcher_script_path, asset_group, dry_run flag.
   Decide: BigQuery table vs append-only GCS object vs Cloud Logging structured log.
   Output: schema dataclass + storage backend recommendation + retention policy.

3. **Rate-limit ceiling decision**: propose per-operator-per-hour + project-wide ceilings.
   Cross-reference: how many real Deploy-Missing launches per day do we expect at steady
   state? (Sample from existing manual-backfill cadence.) Add cost-vector reasoning (a
   misbehaving operator could spawn N VMs/hr; what's the cost ceiling you're comfortable
   absorbing?). Output: numeric ceilings + 429 response shape.

Output landing zone: append a new section `## Phase 0 — IAM scope + audit log + rate limit
proposal (DRAFT for operator review)` to deploy_missing_auto_launch_2026_05_07.md
between the existing Phase 0 todos (line 132) and Phase 1 (line 134). Mark proposals as
`STATUS: DRAFT — operator review pending` so they don't get mistaken for shipped decisions.

REPOS OWNED:
- unified-trading-pm (plan body only — pure draft, no code).

DONE-DEFINITION:
- [ ] 3 proposals drafted with explicit options + recommendation + tradeoff analysis.
- [ ] Each proposal marked `STATUS: DRAFT — operator review pending`.
- [ ] Proposals cite blast-radius implications + cross-reference Phase 1's tarball-refresh
      wiring (Tab 4's work) where relevant.
- [ ] DONE-2026-05-08 block at the bottom of the plan body referencing the proposal section.

REPORT-BACK: 1 commit (proposal section); push per conditional rule.
```

#### Tab 14 — `defi-fork1-prep-audit-tab` ✅ DONE 2026-05-08 — case-5 BIG finding surfaced

- **Verified by main 2026-05-08 07:44 UTC** — PM@`c08f7a6` exists + pushed to origin. Audit doc filed at
  `plans/active/issues/defi_fork1_prep_audit_2026_05_08.md` (33,372 bytes — substantial output).
- **HEADLINE FINDING (case-5 BIG)**: **13 of 17 probed (chain, protocol) pairs in Fork 1 scope have UAC
  `PROTOCOL_LAUNCH_DATES` SSOT drift** — same shape as Tab 9's AAVE_V3-ETHEREUM finding, applied across the broader Fork
  1 surface. Includes carry_staked_basis lead-archetype legs (AAVE V3 OPTIMISM 142d data loss; UNISWAP V3 ARBITRUM 91d
  data loss). Plus: Pyth Hermes archive doesn't cover ~11 months of jitoSOL history (2022-11 → 2023-10) needed for
  carry_staked_basis Solana leg. bSOL is in Fork 1 brief but NOT in UAC `LST_TOKEN_GENESIS` — coverage gap.
- **What Tab 14 correctly did NOT do**: ship the UAC fix. Avoiding collision with Ikenna's writegate work
  - Tab 9's still-stacked PM commits + the parallel-agent rule. **Operator triage required** — Tab 14 recommends 4
    sequential fix tabs A/B/C/D (mirror Tab 9's AAVE_V3-ETHEREUM precedent).
- **Bug classes 1/2/3 results**: diagnostic-only, no findings flagged for those (silent-zero, schema drift, launch-date
  floor handling all clean across the audited surface).
- **Going quiet** per spawn protocol — won't pick up new work.

**Surfaced to operator** in chat at 07:44 UTC (case-5 escalation per Findings Triage Discipline).

**Why now**: Validates Tab 5's + Tab 9's lending-indices fixes end-to-end on the broader Fork 1 surface before Ikenna's
D4 DeFi launches. Tab 9 already proved the AAVE V3 ETH case + handler short-circuit; Tab 14 catches similar UAC SSOT
date drift pattern across the OTHER (chain, protocol) pairs.

**Spawn prompt — paste this entire block as the new tab's first message**:

```text
You are Tab 14 — a sub-agent spawned by Harsh's main orchestrator agent (Tab 1).

BEFORE doing anything else, read these in order:
  1. plans/active/work_split_2026_05_07_harsh_5tab_layout.md § "Bootstrap — read first if
     you're a spawned tab (Tab 2+)" — workflow rules.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — esp. "Honest absence vs fake placeholders"
     + "Four-category empty-output decision" sections.
  3. plans/active/defi_master_2026_05_07.md Fork 1 — your plan-of-record.
  4. plans/active/issues/lending_indices_handler_bugs_2026_05_07.md — the 3 bug shapes Tab 5
     just fixed; you're auditing for similar classes elsewhere in defi_master Fork 1.
  5. plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md — Tab 6's breakdown of
     13,632 actionable rows; cross-reference for known-broken paths.

Your agent-tag: defi-fork1-prep-audit-tab. Your tab number: 14.

YOUR TASK: run a diagnostic audit on every defi_master Fork 1 data source for **4 bug
classes** that Tab 5 + Tab 9 surfaced and partially fixed:

  Bug class 1: silent-zero (subgraph routing config error) — sample one day per chain per
    protocol; assert returned tick count > 0 if the chain × protocol × date is post-genesis.
  Bug class 2: schema drift (GraphQL or REST query out of date) — run each Fork 1 adapter's
    smoke method, assert no schema-mismatch errors.
  Bug class 3: launch-date floor handling — for each Fork 1 instrument, assert
    instruments-service's get_protocol_floor_date returns the UAC PROTOCOL_LAUNCH_DATES SSOT
    value, not a hard-coded floor.
  Bug class 4 (NEW — added per Tab 9 discovery 2026-05-08): **UAC PROTOCOL_LAUNCH_DATES
    date drift**. Tab 9 found `("ETHEREUM","AAVE_V3"): "2022-03-14"` in UAC chain_env.py was
    wrong — actual mainnet deploy was `2023-01-27` (11-month gap → 343 days of false-empty).
    Probe-verify this for EVERY (chain, protocol) pair in PROTOCOL_LAUNCH_DATES — query the
    matching subgraph for the earliest `*HistoryItems` event (or equivalent first-write
    indicator). If the UAC date is more than ~14 days before the earliest on-chain event,
    flag as a likely date-drift bug. Critical pairs to check first (high relevance to
    May-23 archetypes):
    * AAVE_V3 / BASE, LINEA, BSC, METIS, GNOSIS — multi-chain Aave V3 cohorts beyond Tab 9's
      already-fixed ETHEREUM.
    * COMPOUND_V3 / ETHEREUM, ARBITRUM, BASE, OPTIMISM — multi-chain Compound V3 (Bug 2
      surface).
    * SPARK / ETHEREUM — Maker-spinoff lending; UAC date suspect.
    * Any other (chain, protocol) pair in chain_env.py with a date that pre-dates the
      protocol's general-multi-chain rollout date.

Fork 1 scope (per defi_master plan body):
- Aave V3 (Ethereum + Polygon + Arbitrum + Base — the 4 EVM chains).
- Uniswap V3 swap fees (Ethereum + Arbitrum + Base + Polygon).
- LST yields (jitoSOL + mSOL + bSOL on Solana).
- Pyth Hermes (Solana on-chain price feeds — re-added 2026-05-06 per CLAUDE.md unbanning).
- Chainlink (EVM chains: Arbitrum + Base + Polygon).
- Lending-indices broader (Compound V3 across chains).

This is DIAGNOSTIC ONLY — no code changes. Output is an issue doc:
plans/active/issues/defi_fork1_prep_audit_2026_05_08.md per the Findings Triage Discipline
issue-doc format (CLAUDE.md).

If you find any new bugs (NOT Tab 5's already-fixed ones), file them as case-3 findings
(adjacent to defi_master plan, NOT your scope to fix) — annotate defi_master plan body
with explicit owner pointer (Ikenna for D4 launch fork; or main for triage).

DONE-DEFINITION:
- [ ] All Fork 1 data sources sampled for the **4 bug classes** (incl. Bug class 4 UAC date
      drift).
- [ ] Per-(chain, protocol) UAC date vs subgraph-earliest-event probe results tabulated.
- [ ] plans/active/issues/defi_fork1_prep_audit_2026_05_08.md filed with per-source results
      + per-(chain, protocol) UAC date drift verdict.
- [ ] Any new findings annotated in defi_master plan body with case-3 owner pointer.
- [ ] If Bug-class-4 drifts found: file a SEPARATE issue doc per pair (or one batched doc)
      so each can be tracked / fixed independently like Tab 9 did for AAVE V3 ETH. Do NOT
      ship the UAC fix yourself — flag for operator + main agent to spawn a follow-up tab
      (avoids collisions on UAC chain_env.py with Ikenna's writegate + Tab 9's PM stack).
- [ ] DONE-2026-05-08 block at the bottom of the audit doc.

REPORT-BACK: 1-3 commits (audit doc + per-pair issue docs if drifts found + defi_master
annotations); push per conditional rule.
```

### ⚪ Main agent (this session) doing now

- Tabs 9-14 queued (per operator request) — Tabs 9/10/11 to start now, Tabs 12/13/14 after review.
- Standing by to: (a) ack STARTED pings + flip QUEUED → IN FLIGHT, (b) verify DONE pings + flip IN FLIGHT → ✅ DONE, (c)
  answer any 🟡 BLOCKED Qs in plan-of-record docs, (d) field new direction.

### ✅ Done today

- Daily reset: incoming-commit summary across PM (45) + 12 sibling repos (~95 commits) reported to Harsh ✓
- Spawn 1 queued — deployment-api Phase 2 endpoints prompt drafted with full behavioural contract, repo ownership,
  collision boundaries, and done-definition ✓

### ❓ Open questions across active plans

- _(none flagged from spawned tabs yet — Spawn 1 not started)_
- **Open with operator (chat thread)**: sports-master D2 P1 reconcile-hook scope — whether to hook into features-sports
  backfill VM (architecturally clean) vs all 7 per-source raw backfill VMs (matches plan wording literally) vs
  both-chained. Deferred until writegate Phase 2.C lands on Ikenna's side anyway.

---

## Daily reset (each morning)

Main agent boots and:

1. `git fetch origin live-defi-rollout && git log --oneline -25 origin/live-defi-rollout` — summarize incoming commits
   for Harsh (so both have shared context). Do NOT auto-pull — operator does the pull explicitly when they want to sync
   local to remote (this avoids surprise rebases of in-flight local commits from spawned tabs).
2. Re-read [`work_split_2026_05_07.md`](work_split_2026_05_07.md) (the parent D1-D5 plan) + this ledger's "Today's
   status" + [`_agent_pings.md`](_agent_pings.md) for any overnight pings.
3. **Daily ledger sweep** — for every plan with `## Open questions`:
   - Identify ✅ RESOLVED Q&As older than 24h → collapse into a `### Q&A history (resolved)` subsection at the bottom of
     the same plan to declutter the top.
   - Verify no stale 🟡 BLOCKED Q&As (>24h without answer) — if any, either re-prompt the sub-agent or escalate to Harsh
     as a stuck task.
   - Verify `_agent_pings.md` has no orphan lines (lines whose plan-doc Q&A was already resolved but the ledger line
     wasn't removed).
4. Move yesterday's "Done today" entries into the "Historical log" section at the bottom of this doc.
5. Reset "Today's status" with the new date header + identify today's actionable items.
6. Re-arm the /loop polling the ping ledger (`/loop 10m check ping ledger and answer technical Qs`).
7. Report to Harsh: "Today's plan = X, Y, Z. I recommend doing X here, queuing Y for fresh tab, Z idle on prereq. Ping
   ledger has K entries open. Local commits ready to push: N (or zero)."
8. Wait for Harsh's direction. Push the daily-reset commit per the conditional rule (fetch + zero incoming → push; if PM
   has incoming, flag for review before pushing).

## Historical log

### 2026-05-07 (D1)

- D1 cefi VM monitor — offloaded to parallel monitoring agent (37 cefi VMs in flight from bitfinex/bitget/kraken
  ×futures+spot ×2020-2026; events flowing per main-agent spot-check at T+30min) ✓
- D1 UAC backfill-launch types Phase 1 — Ikenna shipped early `UAC@a70b3f6` (5 Pydantic models + 23-value StrEnum + 15
  unit tests pass) ✓
- Plan flips for D1 — `PM@fb7aefa` (work-split + work-stream-A Phase 1 checkboxes) ✓
- Findings Triage Discipline (HARD RULE) added to CLAUDE.md — `PM@c8e0e0f` ✓
- 3 issue docs filed retroactively per the new rule — `PM@becfe4a` (cefi tardis writegate findings + lending-indices
  handler bugs + audit_followups #7) ✓
- Temporary exemption added to Findings Triage Discipline for QG-failure findings on others' code — `PM@a86de35` ✓
- Pivoted layout doc from 5-tab to orchestration ledger — `PM@fc6b281` (and earlier) ✓

---

## Cross-references

- Parent split: [`work_split_2026_05_07.md`](work_split_2026_05_07.md) — the D1-D5 calendar split between Harsh and
  Ikenna.
- Ikenna's mirror layout: [`work_split_2026_05_07_ikenna_5tab_layout.md`](work_split_2026_05_07_ikenna_5tab_layout.md) —
  Ikenna's working method (fixed 5 thematic tabs). Different from this ledger's dynamic model. **Don't apply Ikenna's
  tab-1-to-5 ownership to Harsh's spawned tabs** — the items get assigned ad-hoc per-day, not by domain.
- Audit dependency graph: [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) — per-plan
  status + critical path.
- Workspace rules: [`../../cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) — read by every spawned tab.
- Findings discipline: CLAUDE.md § "Findings Triage Discipline (HARD RULE)" — case-1-to-5 routing for any issue surfaced
  mid-task.
