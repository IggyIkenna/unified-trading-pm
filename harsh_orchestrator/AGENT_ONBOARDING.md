---
title: Agent Onboarding — read first if you are a spawned tab agent
type: onboarding-spec
status: active
created: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Agent Onboarding

> **You are a spawned tab agent.** Harsh just opened a fresh Claude Code tab and told you _"work on Tab N tasks"_. This
> doc is your boot context — read it once before doing anything else, then read everything in the "Reading order" below
> in sequence. Total bootstrap time: ~5 min.

## Git discipline under per-slot worktrees (codified 2026-05-11 — supersedes the 2026-05-08 "operator-auth-for-all-git-ops" rule)

You run in your **own worktree** at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/hk/<N>` — a separate `.git/index` +
working tree from every other slot (see [`../codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md)).
The shared-working-tree foot-guns — a `pull`/`rebase` in one tab auto-stashing another tab's uncommitted WIP — are
**unrepresentable across slots** now. So the pre-worktree HARD RULE ("no push/pull/rebase without operator
authorization") is **lifted**: you push your own work per shippable unit, no authorization ping needed.

### The merge model — direct-to-`live-defi-rollout`, rebase-on-push (no batch-merge step)

Per shippable unit (a green, self-contained slice — helper+tests / one adapter migration / one reconciler):

1. **Pre-commit check** — `git status` + `git diff --cached --stat` (NO path arg). Confirm only YOUR files are staged.
   Within your slot, sub-agents you spawned share your `.git/index`, so this check still matters. Stage by name or
   `git add -p`; **never `git add -A` / `git add .` / `git add <whole-shared-file>`.**
2. `git commit` on your branch `tab/hk/<N>`.
3. `git fetch origin live-defi-rollout`.
4. **Conditional push:**
   - **If incoming commits touch files YOU also edited in unmerged commits** → STOP. Write a `🟡 BLOCKED` Q in your
     plan-of-record `## Open questions` listing your commits + the incoming ones; ping your `pings/slot_<N>.md`; continue with
     what you CAN do. Slot 1 / operator resolves.
   - **Else** → `git rebase origin/live-defi-rollout` (auto-resolves non-overlapping changes). If the rebase surfaces a
     conflict, apply the **plan-aware-merge-resolution** protocol
     ([`../codex/05-infrastructure/plan-aware-merge-resolution.md`](../codex/05-infrastructure/plan-aware-merge-resolution.md)):
     checkbox-flip / append-section shapes → keep both, `git rebase --continue`; paragraph-rewrite or code conflict →
     escalate to slot 1 (don't guess). Then `git push origin HEAD:live-defi-rollout`.
5. **Flip the plan-of-record checkbox in the same logical unit** as the code commit (see § "Plan-of-record curation
   duties").
6. **After the rebase, check for inbound messages** — re-read your `harsh_orchestrator/pings/slot_<N>.md` for new
   `[main → slot N]` lines (slot 1 reaches you here — acks, scope changes, pointers) + your plan-of-record `## Open
   questions` for new `A1` answers to anything you flagged. This is the bidirectional half of the per-slot ping file
   (see [`pings/README.md`](pings/README.md) § "Bidirectional comms").

Nobody does a batch-merge step — each slot self-lands its work as it finishes. The only residual is a rebase conflict
in PM when two slots flip checkboxes in the same plan file; mitigated by (a) **only slot 1 writes PM plan/codex bodies**
— you flip ONLY your own plan-of-record's checkboxes with `git add -p`; (b) the plan-aware-merge protocol auto-resolves
trivial shapes; (c) the scheduling rule (slot 1 keeps same-repo tasks out of the same parallel wave).

### What's still operator/slot-1 territory (don't do without a ping)

- `git push --force` / `--force-with-lease` to `live-defi-rollout` — **never.**
- Merging another slot's branch into `live-defi-rollout` — that's slot 1's job in dependency order, not yours.
- `git reset --hard` past commits you didn't make; `git stash pop`/`apply` of a stash you didn't create.
- `git checkout origin/<branch> -- .` or any wildcard remote-overwrite of the working tree — **never** (the "Two
  teammates × multiple parallel agents" rule still applies to any foreign-owned dirty file you find at boot — leave it
  alone).

### Why the change

The 2026-05-08 "operator-auth-for-all-git-ops" rule existed because the shared working tree meant Tab A's `git pull
--rebase` would auto-stash Tab B's uncommitted edits (the 2026-05-08 PM incident — Tab 5's rebase auto-stashed Tab 1's
LEDGER + AGENT_ONBOARDING WIP — that drove it). Per-slot worktrees eliminate that by construction. With the foot-gun
gone, centralizing every push through the operator just adds latency for no safety gain, so we're back to the standard
conditional-push model.

### LDR alignment cadence (HARD RULE — codified 2026-05-13 after repeated foot-gun #5)

**Three checkpoints, all required:**

1. **Boot — rebase every owned repo onto LDR.** Not just PM; for every repo in your work-split § "Slot N" "Repos owned":
   ```bash
   cd "${WORKSPACE_ROOT}/.tabs/<N>/<repo>" && git fetch origin --quiet && git rebase origin/live-defi-rollout
   ```
   Stale base → outdated assumptions + messy merges later.

2. **During work — FF-push per shippable unit, NOT end-of-session.** After every `git commit` on `tab/hk/<N>`, immediately push to LDR (conditional rebase first if behind). Do NOT batch 5-10 commits "to push at the end" — that IS foot-gun #5.

3. **Pre-shutdown — verify your work is on LDR.** Before ending your session for ANY reason (idle / lunch / context-window / operator-close), in each owned repo:
   ```bash
   git rev-list --count HEAD ^origin/live-defi-rollout    # must be 0
   ```
   Non-zero → push remaining commits per (2) before closing.

**Why this matters**: operator + Ikenna run 5-10 parallel slots per side. Agents pick up work / unblock based on LDR state. If you ship 3 plans in your first 2 hours but they sit on `tab/hk/<N>` only, every slot blocked on that work waits 2 hours unnecessarily. Worse: plan-flips `[x]` claim work is shipped while LDR lacks it — readers see "shipped" and find nothing, treating the flip as a false claim. Reference: 2026-05-13 slot 4 had to be rescued by main cherry-picking Phase 8A-D off `tab/hk/4` after slot self-ack'd DONE with the work invisible to LDR (execution-service@38b3e8a5).

### Workspace-wide drift recognition (codified 2026-05-13)

If you find 10+ dirty files at boot that look like ruff format / unused-imports cleanup (function signature wrapping, import reorders, tuple multi-line formatting), and the same pattern is dirty in other slots' worktrees (`git -C ${WORKSPACE_ROOT}/.tabs/<other-N>/<same-repo> status`), it's **workspace-wide foreign drift** — NOT yours, NOT real WIP. Discard with `git checkout -- .` per repo. Don't try to commit/integrate it. (2026-05-13: slot 3 had 23 such files in UAC, slot 6 had 30 in UTL, slot 7 had 26 in UTL — all the same diff, all discardable.)

## Your role in 3 sentences

You are **slot N**, a scoped implementer spawned by Harsh's main orchestrator agent (slot 1, a separate Claude Code
session on the SAME PC). You work in your **own worktree** at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/hk/<N>` —
an isolated `.git/index` + working tree from every other slot — and you execute one task end-to-end against your
assigned plan-of-record, shipping it incrementally (commit + conditional-push per shippable unit per the git-discipline
section above), then go quiet. You do NOT take on adjacent work, push speculatively, merge another slot's branch, or
message Harsh directly — slot 1 is your conversational dispatcher; you CAN spawn `Task` sub-agents per your LEDGER slot
entry's "Sub-agent fan-out" hint, but only for mechanical / audit work, never cross-cutting design, and you MUST paste
the full ruleset at the top of every Task prompt (see § "Sub-agent fan-out — discipline" below).

## Lever 1 + 2 — autonomous slot pivoting + auto-poll (codified 2026-05-14)

**New orchestration model** reduces main-orchestrator burden by ~80%. Two mechanisms:

### Lever 1 — Multi-item continuation prompts (autonomous pivoting)

If today's session uses a `plans/active/continuation_prompts_harsh_<YYYY_MM_DD>.md` doc (template at
[`CONTINUATION_PROMPTS_TEMPLATE.md`](CONTINUATION_PROMPTS_TEMPLATE.md)), your slot section lists **3-5 items in priority
order** + a "SCOPE EXTENSION reserve" list.

**Auto-pivot rule**: ship items in order. After DONE-pinging item 1, **immediately START item 2** without waiting for
main dispatch. If you finish all priority items, pull from SCOPE EXTENSION reserve. Main reads your DONE pings on its
own cadence — no acknowledgment delay.

**Stop conditions** (drop a BLOCKED ping + stand by — do NOT pivot):
1. Cross-side handshake required (Ikenna ACK on UAC change, etc.)
2. Ambiguous design decision (when fix could go either way)
3. Foreign-file collision (untracked / unfamiliar files in your scope)
4. Plan-of-record says "AWAITING USER DIRECTION"

### Lever 2 — Mechanical auto-poller

Script: [`../scripts/agents/harsh_auto_poll.sh`](../scripts/agents/harsh_auto_poll.sh). Runs every ~3 min (cron or
`--watch` self-loop), unattended. Handles **only mechanical orchestrator work** (no judgment):

- New STARTED ping → flips LEDGER row to 🟢 IN FLIGHT, commits + pushes
- DONE / BLOCKED / 🚨 BIG-finding ping → appends to `harsh_orchestrator/auto_poll_log/operator_alerts.log` for next main wake-up
- Cross-side Ikenna → Harsh ping → appends to alerts log
- FF-only pull (won't auto-rebase if local diverges — alerts operator)
- Exit codes: 0 = clean, 1 = mechanical edits, 2 = needs main, 3 = error
- New BACKLOG dispatch picks remain main's job (judgment work — Prereq+Repos fit check)

Companion: [`THEMATIC_CLUSTERS.md`](THEMATIC_CLUSTERS.md) — stable per-slot theme map across cycles.

**Implication for slots**: ping-format consistency matters more than before. Use the standard tags:
- `slot-N — STARTED <theme>` for STARTED pings
- `slot-N — ✅ DONE <theme>: <sha-list>` for DONE pings
- `[slot N → main] — BLOCKED: <what>` for BLOCKED pings

The auto-poller pattern-matches these. Non-standard phrasing won't escalate properly.

### Lever 3 — Model A migration (future, when work-split predictable)

Not active yet. See `CONTINUATION_PROMPTS_TEMPLATE.md` § "Migration to Model A" for readiness criteria.

## Reading order (do this first, in sequence)

1. **THIS file** — confirm your role + the git discipline (the "Git discipline under per-slot worktrees" section above).
2. **[`../codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md)** — the 3-tier
   isolation model. You are tier 2 (a slot); sub-agents you spawn are tier 3 (they share your slot's worktree).
3. **`harsh_orchestrator/LEDGER.md`** — find your **Slot N** entry under "Today's status → Tab registry". It has theme /
   plan-of-record / worktree+branch / gate status + a pointer to the work-split § "Slot N".
4. **`plans/active/work_split_<today>_harsh.md` § "Slot N"** — your **full task brief**: scope items + priorities +
   repos owned + collision boundaries + done-definition + full-execution criterion. (The work-split's § "Spawn prompts"
   is just the minimal per-slot prompt your operator pasted — the substance is in § "Slot N".)
5. **`cursor-configs/CLAUDE.md` § "Daily Work-Split Process" + § "Per-Tab Worktrees"** — the workspace orchestration
   spec (Model A/B work-splits, conditional push, plan-of-record + Q&A bus, ping ledger, polling cadence, sub-agent
   fan-out, the 3-tier worktree model).
6. **`cursor-configs/CLAUDE.md`** (the rest) — workspace coding standards: uv not pip, basedpyright not pyright, no
   `os.getenv()`, "Findings Triage Discipline (HARD RULE)", "Commit + Push + Flip Plan Checkboxes (HARD RULE)", "Two
   teammates × multiple parallel agents", per-asset-group shard-key matrix, etc.
7. **[`../codex/05-infrastructure/plan-aware-merge-resolution.md`](../codex/05-infrastructure/plan-aware-merge-resolution.md)**
   — the conflict-resolution protocol for when your `git rebase origin/live-defi-rollout` surfaces a conflict (classify
   shape → auto-resolve trivial → escalate paragraph-rewrites to slot 1).
8. **`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`** — symlinked to `CLAUDE.md` since 2026-05-08 PM, so it contains the
   full CLAUDE.md ruleset. **You MUST paste its contents at the top of every `Task` sub-agent prompt you spawn**
   (sub-agents do NOT inherit CLAUDE.md). See § "Sub-agent fan-out — discipline" below.
9. **Your plan-of-record** — the specific plan named in your Slot N entry. Where your todos live + where you flip
   checkboxes + where you write `## Open questions` for blockers.

## The only 4 things you must internalise (everything else is in CLAUDE.md)

### 1. Communication bus

| What                                           | Where                                                                                                                                                       | When                                             |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **Boot ack**                                   | `harsh_orchestrator/pings/slot_<N>.md`                                                                                                                        | At session start (one-line `STARTED Tab N` ping) |
| **Blocker / question for main**                | Your plan-of-record's `## Open questions` § (status `🟡 BLOCKED`) + ping in `harsh_orchestrator/pings/slot_<N>.md`                                            | When you hit ambiguity / decision / push-race    |
| **Done announcement**                          | `## DONE-<YYYY-MM-DD>` block at bottom of plan-of-record + ping in `harsh_orchestrator/pings/slot_<N>.md`                                                     | When done-definition met                         |
| **Side findings** (case-1 to case-5)           | Per Findings Triage Discipline in CLAUDE.md — case-5 BIG findings ALSO go through plan-of-record + ping (NOT direct chat); main agent escalates to operator | Throughout                                       |
| **Direct chat to Harsh from your tab session** | NEVER — main is your dispatcher                                                                                                                             | NO EXCEPTIONS — see "Routing rule" below         |

#### Routing rule (clarified 2026-05-08 PM after agents started bypassing main)

**Every question, blocker, decision request, scope concern, finding, status escalation, or operator-direction ask MUST
go through the plan-of-record + ping ledger.** Even case-5 BIG findings. Even "I think the work-split underestimated my
scope." Even "my plan looks blocked on something outside my scope." Even "I think I should defer Plan X." All of it.

Routing flow:

1. Write the question / finding into your plan-of-record's `## Open questions` § using the format below.
2. Append a one-line ping to `harsh_orchestrator/pings/slot_<N>.md` pointing at the plan-of-record.
3. Continue with anything you CAN do (don't block waiting).
4. **Main agent** reads the ping (~1 min cadence), reads your Q in the plan-of-record, writes A1 in the plan- of-record
   (sometimes after escalating to operator on your behalf), removes the ping line.

**Why this rule is strict.** The operator runs many spawned-tab Cursor / Claude Code sessions in parallel. If every
spawned tab streams questions into its own session text, the operator has to switch tabs and read every one to keep up.
The plan-of-record + ping bus centralizes routing through the main agent, who is purpose-built for triage + escalation.
This is the entire reason main exists.

**What "direct chat to Harsh" actually means.** Your tab session text is visible to Harsh — every response you write is
something he CAN read. That's fine for status updates ("now running QG", "Phase 0 sub-agent fan-out complete"), progress
notes, and completion confirmations. **It is NOT fine for: questions, blockers, decisions, ambiguity-resolutions, scope
concerns, "should I do X or Y", "is this in scope", or any other ask-for-direction.** Those go in plan-of-record + ping
ledger ONLY. If you find yourself typing a question into your tab session, stop and write it in the plan-of-record
instead.

**What if it's truly time-critical and the operator needs to see it within seconds?** Still go through the ping ledger.
Use the `🔴 P0` priority marker in your ping line:

```text
[YYYY-MM-DD HH:MM UTC] <agent-tag> — 🔴 P0: <one-line> ; see <plan-of-record>
```

Main agent treats P0 pings as immediate-escalation-to-operator. The latency is ~1-2 min, not seconds, but that's the
cost of the centralized model — and the operator's attention is preserved for the cases that actually warrant it.

#### Q&A format on plan-of-record

```markdown
### Q1 — [your-agent-tag, YYYY-MM-DD HH:MM] — short title

**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what was tried, options considered, recommendation if you have one>

#### A1 — [main, YYYY-MM-DD HH:MM]

**Status**: ✅ RESOLVED

<answer + reasoning + commit-sha of anything shipped meanwhile>
```

Main agent polls `harsh_orchestrator/pings/*.md` (+ the transition stub `_agent_pings.md`) ~1 min cadence (faster while operator's active). Your A1 typically lands within 1-5
min for technical Qs; longer if the Q escalates to operator.

#### End-to-end workflow example (a typical Q lifecycle)

Concrete walk-through of a question moving from "spawned tab realises something is unclear" all the way to "answer
received, work resumes." Use this as the reference pattern.

**Scenario**: Tab 3 (`deployment-ui-tab`) is shipping deployment-UI lifecycle tabs Phase A (UAC SSOT for lifecycle
column). They discover the plan-of-record names ~37 todos across 8 phases, but the work-split estimated only ~10 AI-days
for this tab. Tab 3 needs operator direction on whether to ship full scope or trim.

**Step 1 — Tab 3 writes the question into the plan-of-record's `## Open questions` section** (creating the section if it
doesn't exist yet):

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

Work-split estimated ~10 AI-days for this tab; current scope projects to ~16-18 AI-days at single-agent throughput,
~12-14 with 5 parallel sub-agents at boot.

**Options**: (a) Ship full scope (~37 todos) over 2-3 cycles. Risks: pushes Phase D auth re-shape past 2026-05-23
cutover; Ikenna Tab 5 audit-log integration unblock-date slips. (b) Trim to highest-priority phases A + B + D (lifecycle
tabs + UAC SSOT + auth re-shape, ~25 todos). Defers C/E/F/G/H to a follow-up cycle. Auth re-shape unblocks Ikenna Tab 5
in cycle. Fits ~10 AI-day work-split estimate. (c) Trim further to A + D only (UAC SSOT + auth re-shape, ~13 todos).
Defers all UI tab refactors to a follow-up cycle.

**Recommendation**: (b) — preserves the cross-side Ikenna handshake (auth re-shape Phase D) + delivers the UAC SSOT that
Tab 1 depends on for instruments-live UI tab content.
```

**Step 2 — Tab 3 appends a one-line ping to `harsh_orchestrator/pings/slot_<N>.md`**:

```text
[2026-05-08 13:22 UTC] deployment-ui-tab — Q on plan scope (37 todos vs ~10 AI-day est) — full-ship vs trim;
  see plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md
```

**Step 3 — Tab 3 continues working on what they CAN do** (e.g. starts Phase A UAC SSOT — that work is in-scope under any
of the three options, so it doesn't block on the answer).

**Step 4 — Main agent polls your `pings/slot_<N>.md` (~1 min later)**, sees the ping, opens the plan-of-record, reads Q1,
decides this is a scope decision that requires operator input. Main agent writes back in chat to operator with a
summary:

> "Tab 3 hit case-5 BIG: plan-of-record scope ~37 todos vs work-split ~10 AI-day estimate. Options (a) full-ship, (b)
> trim to A+B+D ~25 todos preserving Ikenna handshake, (c) trim to A+D ~13 todos. Tab 3 recommends (b). What's your
> call?"

Operator picks (b) in chat.

**Step 5 — Main agent writes A1 in the plan-of-record**:

```markdown
#### A1 — [main, 2026-05-08 13:34 UTC]

**Status**: ✅ RESOLVED — operator picked (b) trim to A + B + D

Operator decision in chat 13:34 UTC: ship Phase A UAC SSOT + Phase B 4 tab refactors + Phase D auth re-shape this cycle
(~25 todos). Defer Phases C / E / F / G / H to follow-up cycle (next 2-3 days). Auth re-shape Phase D ships first →
unblocks Ikenna Tab 5 audit-log integration per cross-side handshake. Check off C/E/F/G/H todos with
`**DEFERRED → follow-up cycle**` annotation; do not delete.
```

**Step 6 — Main agent removes the ping line from your `pings/slot_<N>.md`** (the doorbell job is done; full Q&A history lives
durably in the plan-of-record).

**Step 7 — Tab 3 sees the A1** (next time they touch the plan-of-record, e.g. flipping a checkbox after shipping a
sub-todo). They drop scope to A + B + D, mark deferred phases with `**DEFERRED → follow-up cycle**`, and continue. No
further operator interaction needed for this question.

**Total operator attention spent**: ~30 seconds in chat to read main's summary + answer. **Spawned tab attention**:
focused, in-scope. **Audit trail**: fully captured in the plan-of-record's `## Open questions` § (durable; survives
ledger sweeps + main-agent context resets).

#### Anti-patterns (what NOT to do — these break the model)

- ❌ **Type the question into your tab session text**: _"Hey Harsh, I'm looking at the plan and I see ~37 todos. Should
  I ship all of them or trim?"_ — operator now has to switch tabs and read context. Multiply by 5 spawned tabs and the
  operator's day is gone.
- ❌ **Ping ledger without writing the question in the plan-of-record**: _"Tab 3 — quick Q on scope, can you answer?"_ —
  main agent has no context, has to ping back asking for the question, latency doubles, no durable record.
- ❌ **Write the question only in the plan-of-record without a ping**: main agent's ~1 min poll is on your `pings/slot_<N>.md`,
  not on every plan body. Question may sit unread for hours.
- ❌ **Bypass main and DM operator on a separate channel** (Telegram, Slack, etc.): main agent doesn't see it; the
  operator's coordination model breaks; A1 won't land in the plan-of-record's audit trail.
- ❌ **Ask three questions about the same scope concern across three different turns** in your tab session text: each
  one is a tax on operator attention. Bundle into one Q with a clear options list.
- ❌ **Use the ping ledger for status updates**: ledger is for blockers and questions only. Status updates go in your
  tab session text (operator can read at their own pace) or in the plan-of-record body as iteration-log entries (e.g.
  _"sweep #37: 16/24 alive, no actions"_).

### 2. Push discipline — see "Git discipline under per-slot worktrees" above

The full rule is the **"Git discipline under per-slot worktrees"** section near the top of this doc. In short: commit
per shippable unit on your branch `tab/hk/<N>` → `git fetch origin live-defi-rollout` → if incoming touches files you
also edited, STOP + flag (`🟡 BLOCKED` Q in plan-of-record + ping); else `git rebase origin/live-defi-rollout` (apply
the plan-aware-merge protocol on conflict) → `git push origin HEAD:live-defi-rollout`. No operator authorization needed
per push — the per-slot worktree makes the old shared-tree foot-gun unrepresentable. `--force` pushes + merging another
slot's branch stay operator/slot-1 territory.

### 3. Pre-commit check (within-slot — sub-agents share your `.git/index`)

Cross-slot bundling is unrepresentable now (each slot has its own index). But **within your slot**, any `Task`
sub-agents you spawned write to the same `.git/index` as you — so the check still matters. Before EVERY commit, in ANY
repo:

```bash
git status                 # full picture: modified, staged, untracked
git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```

If anything in the staged set or working tree isn't from the unit you're committing, surgically un-stage
(`git restore --staged <file>`) or stash (`git stash --keep-index`) first. Use `git add -p` for your hunks if a shared
file has another sub-agent's edits. **Never `git add -A` / `git add .` / `git add <whole-shared-file>`.** Also: if you
find a *foreign-owned* dirty file at boot (untracked file you didn't create, or a tracked file with edits that aren't
yours), leave it alone — per CLAUDE.md "Two teammates × multiple parallel agents."

Reference incidents: PM@`961980db` / `611b9501` / `34075d84` (all from concurrent-agent overlap, pre-worktree model).

### 4. Plan-of-record curation duties

As you ship work:

- **Flip checkboxes per shippable unit.** `- [ ]` → `- [x]` with `<repo>@<sha>` evidence appended. In the same logical
  unit as the code commit, not at end of session.
- **Append progress notes** to relevant plan body sections if you find something worth recording (e.g. per-iteration
  sweep entries, per-bug investigation notes).
- **Document findings per Findings Triage Discipline** (case-1-to-5 routing per CLAUDE.md).
- **Final**: when done-definition met, append `## DONE-<YYYY-MM-DD>` block at bottom of plan body listing every code +
  plan-flip commit sha. Then go quiet — don't pick up new work autonomously.

### External Data Is Always Available — Never Silently Defer Adapters (HARD RULE codified 2026-05-14)

If you're working an adapter, handler, or data-source client in `instruments-service`, MTDS, or anywhere else and hit
a "no data available" wall — **the unblock is a credential ask to operator, NOT a scope cut**. Data exists for every
asset_group and every MVP archetype. Free-tier exhausted? Upgrade. No public API? There's a paid tier (Helius, Alchemy
paid, Glassnode, Kaiko, Tardis, Databento, Sportradar, etc.).

**Banned reasoning** (any of these leading to scope removal = rule violation): "no public API"; "free tier exhausted";
"no test data"; "subscription required"; "couldn't reproduce in sandbox".

**Required steps**:

1. Build the adapter scaffold anyway (UAC contract + auth shape + retry/backoff + error classification + manifest
   emission). Unit tests against mocks; integration tests marked `@pytest.mark.requires_credentials`.
2. File operator-credential request in `harsh_orchestrator/pings/slot_<N>.md`:
   ```
   CREDENTIAL APPROVAL REQUEST — <adapter_name>
   Vendor: <name + tier + cost estimate>
   What I need: <API key | OAuth | account signup>
   Unblocks: <asset_group × archetype + May-23 gate>
   ```
3. Adapter stays ON the live list. Status = `BLOCKED-CREDENTIALS` (closed-set), NOT `DEFERRED`, NOT `POST-CUTOVER`.
   Plan-flip: `- [ ] [BLOCKED-CREDENTIALS — pinging operator at <commit-sha>]`. Never move to a post-cutover plan
   without explicit operator [ack] on the slot ping.
4. **Status taxonomy** (closed set): `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` / `BLOCKED-UPSTREAM-OUTAGE` /
   `DEFERRED` (only valid with named successor + operator ack).

**Full SSOT**: CLAUDE.md § "External Data Is Always Available — Never Silently Defer Adapters (HARD RULE)".

## Boot ack template (append to `harsh_orchestrator/pings/slot_<N>.md` after reading)

```text
[YYYY-MM-DD HH:MM UTC] <your-agent-tag> — STARTED slot N (<plan-of-record-path>)
```

> **Timestamp = real UTC.** This machine's clock is **IST (UTC+5:30)**, not UTC. Do NOT run `date` and slap "UTC" on
> the output — that's wrong by 5h30m (e.g. `11:35 IST` is `06:05 UTC`). Get the timestamp with **`date -u +'%Y-%m-%d
> %H:%M UTC'`** for every ping-ledger entry, plan-of-record `## Open questions` heading, and `## DONE-<date>` block.
> Reference miss: 2026-05-11 slot 2's STARTED ack wrote `11:35 UTC` when it was actually `~06:05 UTC`.

Main agent will see it on next 1-min poll, ack with a short note in your plan doc's `## Open questions` if anything to
flag, otherwise stays silent. Your STARTED ping is removed automatically once main confirms clean boot.

## Sub-agent fan-out — discipline (codified 2026-05-08 PM by operator direction)

When YOUR tab spawns `Task` sub-agents (e.g. per the "Sub-agent fan-out hint" in your LEDGER tab entry — "7 parallel
sub-agents, one per plan", "5 parallel per asset_group", etc.), the sub-agents you spawn do **NOT** inherit CLAUDE.md.
They start with fresh context and only see what you paste into the Task prompt. Per CLAUDE.md "Sub-Agents & Autonomous
Agents: Full Rules Required (MANDATORY)", you MUST inject the full rules into every Task prompt. The mitigation Ikenna
shipped 2026-05-08 PM:

- **`cursor-configs/SUB_AGENT_MANDATORY_RULES.md` is now a symlink to `CLAUDE.md`**. So pasting "the contents of
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`" gives sub-agents the FULL CLAUDE.md ruleset (closes the ~70% gap that
  previously existed between the two files).

### What sub-agents are FOR

Sub-agents must not perform any action that could violate workspace rules. They are scoped to audit and mechanical
parallelisation only, with the relevant rules pasted into every Task prompt so they cannot drift.

Use `Task` sub-agents for:

1. **Audit / read-only investigation** — "find every callsite of X across the codebase; report file:line + surrounding 5
   lines"; "compare schema-A vs schema-B and list divergences"; "verify N invariants hold across N modules."
2. **Parallel application of a known-shape mechanical transformation** — "for each of these 30 files, run `rg X` and
   replace with Y, then run `quality-gates.sh` to verify"; "for each of these 8 source repos, apply the same
   import-rewrite recipe."
3. **Batch operations where each unit is fully spec'd** — "launch these 5 backfill VMs (one per asset_group) with these
   exact env vars + post-launch event-stream verification."

Do NOT use `Task` sub-agents for:

1. ❌ **Cross-cutting design** — UAC schema design, UTL helper signature decisions, multi-repo architecture choices.
   These are main-agent / operator territory; sub-agents lack workspace context to make these calls correctly.
2. ❌ **Anything ambiguous** — if the task description requires the sub-agent to make architectural decisions
   ("implement Phase X", "fix the imports"), it's too vague. Spec it tighter or do it yourself.
3. ❌ **Cross-file invariant changes** — if changing one file requires changing 3 others in coordinated fashion,
   sub-agents can't see across their isolated context windows. Master agent integrates.
4. ❌ **Decisions that require consulting plan-of-record `## Open questions` or pinging operator** — those decisions go
   through your tab's main flow, not through sub-agent fan-out.

### How to spawn a Task sub-agent (the canonical pattern)

```
Task(
  subagent_type="general-purpose",
  description="Short task description for telemetry (3-5 words)",
  prompt="""[PASTE THE FULL CONTENTS OF cursor-configs/SUB_AGENT_MANDATORY_RULES.md HERE]

==========================================================
YOUR TASK
==========================================================

[Tight, fully-spec'd task — what to do, what to verify, what to return]

CONSTRAINTS:
- [Specific files / repos in scope]
- [What NOT to touch]
- [What format to return findings in]

DONE-DEFINITION:
- [Verifiable bullets — "X is true", "Y file exists with property Z"]

REPORT BACK: [structured shape of the response — table / sha list / file:line list / etc.]
"""
)
```

### Sub-agents do NOT commit, push, or flip plan checkboxes

Sub-agents **return findings** (file:line lists, diffs to apply, audit tables) — they do not `git commit` / `git push` /
`git rebase` / flip plan checkboxes / write to the LEDGER, plan-of-records, or your `pings/slot_<N>.md`. The **spawning slot**
integrates the findings into its own worktree, commits per shippable unit, conditional-pushes to `live-defi-rollout`,
and flips the plan checkbox — all per the "Git discipline under per-slot worktrees" section above. (The slot itself
pushes freely per shippable unit; only `--force` pushes + merging another slot's branch are operator/slot-1 territory.)

### Anti-patterns (sub-agent foot-guns operator has already seen)

- 🚫 **Forgetting to paste SUB_AGENT_MANDATORY_RULES.md at top of Task prompt** → sub-agent has no rules, goes rogue,
  may use `pip install` / `os.getenv()` / `git push` / etc.
- 🚫 **Spawning a sub-agent on architecturally-vague work** → sub-agent makes decisions outside their context; result
  needs to be re-done by main.
- 🚫 **Spawning sub-agents in series instead of one parallel batch** → wasted parallelism. Send all N Task blocks in ONE
  message so they run concurrently.
- 🚫 **Letting sub-agent decide commit messages / push timing** → not their authority.
- 🚫 **Spawning a sub-agent to spawn its own sub-agents recursively** → context explosion; main agent loses thread.

### Cross-reference

CLAUDE.md § "Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)" is the workspace SSOT for this rule. This
onboarding section is the spawned-tab-agent-friendly summary + sub-agent-fan-out playbook.

## Differences from CLAUDE.md HARD RULE you should be aware of

The Daily Work-Split Process in CLAUDE.md is the SSOT for orchestration mechanics. This onboarding doc is just the
pointer + boot ack. If anything in this doc contradicts CLAUDE.md, **CLAUDE.md wins** — file an issue doc flagging the
drift.

## Useful cross-references

- **Workspace state right now**: [`harsh_orchestrator/LEDGER.md`](LEDGER.md) — today's tab registry, in-flight status,
  recent done, open questions across plans.
- **Active pings**: [`harsh_orchestrator/pings/slot_<N>.md`](pings/) — short doorbell-style log; one line per
  active blocker.
- **All workspace rules**: [`cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md).
- **Sub-agent inheritance**:
  [`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../cursor-configs/SUB_AGENT_MANDATORY_RULES.md).
