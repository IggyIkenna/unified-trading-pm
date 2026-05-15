---
title: Agent Onboarding — read first if you are a spawned tab agent (Ikenna side)
type: onboarding-spec
status: active
created: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Agent Onboarding (Ikenna side)

> **You are a spawned tab agent.** Ikenna just opened a fresh Claude Code tab and told you _"work on Tab N tasks"_. This
> doc is your boot context — read it once before doing anything else, then read everything in the "Reading order" below
> in sequence. Total bootstrap time: ~5 min.
>
> **Mirror doc on the Harsh side:**
> [`../harsh_orchestrator/AGENT_ONBOARDING.md`](../harsh_orchestrator/AGENT_ONBOARDING.md). Same shape, different
> orchestration surface — both report to the workspace-shared
> [`plans/active/_agent_pings.md`](../plans/active/_agent_pings.md) for cross-side comms only.

### LDR alignment cadence (HARD RULE — codified 2026-05-13 after repeated foot-gun #5)

**Three checkpoints, all required:**

1. **Boot — rebase every owned repo onto LDR.** Not just PM; for every repo in your work-split § "Slot N" "Repos owned":

   ```bash
   cd "${WORKSPACE_ROOT}/.tabs/2/<repo>" && git fetch origin --quiet && git rebase origin/live-defi-rollout
   ```

   Stale base → outdated assumptions + messy merges later.

2. **During work — FF-push per shippable unit, NOT end-of-session.** After every `git commit` on `tab/ikennaigboaka/2`,
   immediately push to LDR (conditional rebase first if behind). Do NOT batch 5-10 commits "to push at the end" — that
   IS foot-gun #5.

3. **Pre-shutdown — verify your work is on LDR.** Before ending your session for ANY reason (idle / lunch /
   context-window / operator-close), in each owned repo:
   ```bash
   git rev-list --count HEAD ^origin/live-defi-rollout    # must be 0
   ```
   Non-zero → push remaining commits per (2) before closing.

**Why this matters**: operator + Harsh run 5-10 parallel slots per side. Agents pick up work / unblock based on LDR
state. If you ship 3 plans in your first 2 hours but they sit on `tab/ikennaigboaka/2` only, every slot blocked on that
work waits unnecessarily. Worse: plan-flips `[x]` claim work is shipped while LDR lacks it. Reference: 2026-05-13 Harsh
slot 4 rescued by main cherry-picking Phase 8A-D after slot self-ack'd DONE with work invisible to LDR.

### Workspace-wide drift recognition (codified 2026-05-13)

If you find 10+ dirty files at boot that look like ruff format / unused-imports cleanup (function signature wrapping,
import reorders, tuple multi-line formatting), and the same pattern is dirty in other slots' worktrees, it's
**workspace-wide foreign drift** — NOT yours, NOT real WIP. Discard with `git checkout -- .` per repo. Don't try to
commit/integrate it. (2026-05-13: multiple slots had 20-30 dirty files in UAC/UTL — same diff, all discardable.)

## Your role in 3 sentences

You are **Tab N**, a scoped implementer spawned by Ikenna's main orchestrator agent (Tab 1, a separate Claude Code
session on the SAME PC, sharing the SAME `.git/` + working tree as you). You execute one task end-to-end against your
assigned plan-of-record, ship it, and go quiet. You do NOT take on adjacent work, push speculatively, or message Ikenna
directly — Tab 1 is your conversational dispatcher.

## Reading order (do this first, in sequence)

1. **THIS file** — confirm your role.
2. **`ikenna_orchestrator/LEDGER.md`** — find your tab entry by tab number. Its spawn-prompt block (or the linked
   work-split plan entry) is your full task brief: repos owned, behavioural contract, collision boundaries,
   done-definition.
3. **`cursor-configs/CLAUDE.md` § "Daily Work-Split Process (Ikenna ↔ Harsh, AI-paralleled)"** — full workspace spec
   for the Model A / Model B work-split, shared working tree, conditional push, plan-of-record + Q&A bus, ping ledger
   bifurcation, polling cadence, sub-agent fan-out. **All the orchestration rules you need live there.** This onboarding
   doc is just the boot pointer.
4. **`cursor-configs/CLAUDE.md`** (the rest) — workspace coding standards: uv not pip, basedpyright not pyright, no
   `os.getenv()`, "Findings Triage Discipline (HARD RULE)", "Commit + Push + Flip Plan Checkboxes (HARD RULE)", "Capture
   Discoveries As Plan Todos Immediately (HARD RULE)", "Cross-Plan Coordination Banners", "Two teammates × multiple
   parallel agents", per-asset-group shard-key matrix.
5. **`cursor-configs/SUB_AGENT_MANDATORY_RULES.md`** — sub-agent inheritance rules. Read if YOU spawn `Task` sub-agents
   from inside your tab; for most tabs this is informational.
6. **Your plan-of-record** — the specific plan named in your tab entry (e.g.
   [`plans/active/defi_master_2026_05_07.md`](../plans/active/defi_master_2026_05_07.md) for `defi-launch-tab`). This is
   where your todos live + where you flip checkboxes + where you write `## Open questions` for blockers.

## The 5 things you must internalise (everything else is in CLAUDE.md)

### 1. Communication bus (read carefully — bifurcated)

| What                                 | Where                                                                                                                           | When                                                                |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Boot ack**                         | [`ikenna_orchestrator/_agent_pings.md`](_agent_pings.md) (intra-side)                                                           | At session start (one-line `STARTED Tab N` ping)                    |
| **Blocker / question for main**      | Your plan-of-record's `## Open questions` § (status `🟡 BLOCKED`) + ping in [`_agent_pings.md`](_agent_pings.md) (intra-side)   | When you hit ambiguity / decision / push-race                       |
| **Done announcement**                | `## DONE-<YYYY-MM-DD>` block at bottom of plan-of-record + ping in [`_agent_pings.md`](_agent_pings.md) (intra-side)            | When done-definition met                                            |
| **Cross-side handshake**             | Workspace-shared [`../plans/active/_agent_pings.md`](../plans/active/_agent_pings.md) — **only for Ikenna ↔ Harsh signalling** | When a hard-gate item ships and the OTHER side needs to know        |
| **Side findings (case-1 to case-5)** | Per "Findings Triage Discipline (HARD RULE)" in CLAUDE.md (see #5 below)                                                        | Throughout                                                          |
| **Direct chat to Ikenna**            | NEVER — main is your dispatcher                                                                                                 | Exception: case-5 BIG findings only (per Findings Triage HARD RULE) |

**The bifurcation matters.** Intra-side pings (Ikenna's main ↔ Ikenna's spawned tabs) go in
[`ikenna_orchestrator/_agent_pings.md`](_agent_pings.md). Cross-side pings (signalling Harsh's main about a shared
dependency landing) go in [`../plans/active/_agent_pings.md`](../plans/active/_agent_pings.md). Don't mix them — the
cross-side ledger gets noisy fast and Harsh's main poll cadence assumes cross-side relevance.

Q&A format on plan-of-record:

```markdown
### Q1 — [your-agent-tag, YYYY-MM-DD HH:MM] — short title

**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what was tried, options considered>

#### A1 — [main, YYYY-MM-DD HH:MM]

**Status**: ✅ RESOLVED

<answer + reasoning + commit-sha of anything shipped meanwhile>
```

**Polling cadence (main agent)**: ~1 min while Ikenna is active; stretches to ~5 min when ledger empty for 30+ min. Your
A1 typically lands within 1-5 min for technical Qs; longer if the Q escalates to operator.

### 2. Push discipline (the multi-agent safety valve)

Per CLAUDE.md "Commit + Push + Flip Plan Checkboxes (HARD RULE)" — **commit per shippable unit always**. Then before
pushing:

```bash
git fetch origin <branch>
git log --oneline <branch>..origin/<branch>   # incoming commits, if any
```

- **Zero incoming → push freely.** Default path; no operator approval needed.
- **Any incoming → STOP, do NOT push.** Write a `🟡 BLOCKED` Q in your plan-of-record listing your local commits + the
  incoming ones. Ping the intra-side ledger. Continue with what you CAN do. Main + operator decide rebase / merge /
  cherry-pick.

For `live-defi-rollout` (the working branch) pushes do NOT trigger remote CI per CLAUDE.md "CI Verification After Every
Push (HARD RULE)" branch policy. Confirm push landed via `git rev-list --left-right --count HEAD...origin/<branch>`
returning `0 0` and stop. Local `bash scripts/quality-gates.sh` Pass 1 before push is the only quality gate.

### 3. Pre-commit check (catches the shared-working-tree foot-gun)

Before EVERY commit, in ANY repo:

```bash
git status                 # full picture: modified, staged, untracked
git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```

If anything in the staged set or working tree isn't yours, surgically un-stage (`git restore --staged <file>`) or stash
(`git stash --keep-index`) before committing. Use `git add -p` for your hunks if any shared file has foreign edits.
**Never `git add -A` / `git add .` / `git add <whole-shared-file>`.** After every `git mv` / `git rm` / `git add`, run
`git diff --cached --name-status` to verify YOUR entries are still in the index — a parallel reset can erase staged
renames without surfacing any error.

Reference incidents: PM@`961980db` (foreign content bundled IN), PM@`611b9501` (foreign rename bundled IN),
PM@`34075d84` (own staged work silently bundled OUT by parallel agent reset). All from concurrent-agent overlap on the
shared working tree.

### 4. Plan-of-record curation duties

As you ship work:

- **Flip checkboxes per shippable unit.** `- [ ]` → `- [x]` with `<repo>@<sha>` evidence appended. In the same logical
  unit as the code commit, not at end of session. Commit the flip as a separate commit in the PM repo with
  `docs(plans):` prefix (NOT `plan(...)` — conventional-commits hook rejects it).
- **Append progress notes** to relevant plan body sections if you find something worth recording (e.g. per-iteration
  sweep entries, per-bug investigation notes).
- **Capture mid-cycle findings as plan todos immediately** per CLAUDE.md "Capture Discoveries As Plan Todos Immediately
  (HARD RULE)" — never auto-memory only; the plan should always reflect ideal final solution shape.
- **Final**: when done-definition met, append `## DONE-<YYYY-MM-DD>` block at bottom of plan body listing every code +
  plan-flip commit sha. Then go quiet — don't pick up new work autonomously.

### 5. Findings Triage Discipline (HARD RULE — full case-1-to-5 routing in CLAUDE.md)

When you discover something mid-task that wasn't your todo, route it per CLAUDE.md:

| Where the finding sits                                                                                      | Action                                                                        |
| ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **In-scope** (your code / your edited file)                                                                 | Fix it yourself in the same commit                                            |
| **Adjacent to your plan**                                                                                   | Document + fix now or in next phase of YOUR plan                              |
| **Outside your plan, fits another active plan**                                                             | Annotate the right plan body with explicit owner pointer; don't fix yourself  |
| **Outside every active plan**                                                                               | File issue doc in [`plans/active/issues/`](../plans/active/issues/)           |
| **Big / cross-cutting** (data correctness / May-23 critical / ≥2 repos / SSOT contradiction / VM-affecting) | NOTIFY OPERATOR IMMEDIATELY in chat (case-5 dual-path) **AND** file issue doc |

**Big findings** (data correctness affecting an asset_group, in-flight VM bugs, SSOT contradictions, scope that would
change the work-split, anything blocking May-23) escalate through main → operator-chat in minutes, not the audit-cadence
plan annotation. The cost of one extra paragraph in main's chat summary is far lower than the cost of an operator
missing a P0 finding for hours.

**Cross-Plan Coordination Banners** (CLAUDE.md HARD RULE): when launching VMs or starting in-flight refactors (manifest
schema, file structure, UAC contract, parquet columns, hive-vocab, path templates, error-reason taxonomy), add a
top-of-file `> **🟢 VM RUNNING — ...**` or `> **🟡 IN-FLIGHT REFACTOR — ...**` banner to every other active plan whose
work is influenced. Banner-add is part of the launch / refactor-start logical unit; banner-removal owned by you when the
VM auto-shutdowns or the refactor lands.

### 6. External Data Is Always Available — Never Silently Defer Adapters (HARD RULE codified 2026-05-14)

If you're working an adapter, handler, or data-source client in `instruments-service` or MTDS (or anywhere else) and hit
a "no data available" wall — **the unblock is a credential ask to operator, NOT a scope cut**. Data exists for every
asset_group and every MVP archetype. Free-tier exhausted? Upgrade. No public API? There's a paid tier (Helius, Alchemy
paid, Glassnode, Kaiko, Tardis, Databento, Sportradar, etc.).

**Banned reasoning** (any of these leading to scope removal = rule violation): "no public API"; "free tier exhausted";
"no test data"; "subscription required"; "couldn't reproduce in sandbox".

**Required steps when you hit the wall**:

1. **Build the adapter scaffold anyway** — UAC contract, auth shape, retry/backoff, error classification, manifest
   emission. Unit tests against mocks (per vendor docs). Integration tests marked `@pytest.mark.requires_credentials`
   and skipped by default.
2. **File operator-credential request in `pings/slot_<N>.md`** with this exact shape:
   ```
   CREDENTIAL APPROVAL REQUEST — <adapter_name>
   Vendor: <name + tier + cost estimate>
   What I need: <API key | OAuth | account signup | hardware 2FA>
   Account: <existing operator email | new account needed>
   Unblocks: <asset_group × archetype combos + which May-23 gate>
   Without it: integration tests skip; adapter dormant
   ```
3. **Adapter stays ON the live list.** Status = `BLOCKED-CREDENTIALS` (closed-set), NOT `DEFERRED`, NOT `POST-CUTOVER`.
   Plan-flip: `- [ ] [BLOCKED-CREDENTIALS — pinging operator at <commit-sha>]`. NEVER move adapter to a post-cutover
   plan without explicit operator [ack] on the slot ping.
4. **Status taxonomy** (closed set): `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` / `BLOCKED-UPSTREAM-OUTAGE` /
   `DEFERRED` (only valid with named successor + operator ack). Ad-hoc "deferred" language is rejected.

**Full SSOT**: CLAUDE.md § "External Data Is Always Available — Never Silently Defer Adapters (HARD RULE)".

## Boot ack template (paste this into `_agent_pings.md` after reading)

```text
[YYYY-MM-DD HH:MM UTC] <your-agent-tag> — STARTED Tab N (<plan-of-record-path>)
```

Goes in [`ikenna_orchestrator/_agent_pings.md`](_agent_pings.md) (intra-side), NOT the workspace-shared ledger. Main
agent will see it on next 1-min poll, ack with a short note in your plan doc's `## Open questions` if anything to flag,
otherwise stays silent. Your STARTED ping is removed automatically once main confirms clean boot.

## Today's working model

Today (`2026-05-08`) Ikenna runs **Model A — fixed thematic 6-tab clustering** per
[`../plans/active/work_split_2026_05_08_ikenna.md`](../plans/active/work_split_2026_05_08_ikenna.md). Each tab runs Opus
at full window, owns its own done-definition, and fans out to sub-agents (Task tool / Explore / general-purpose) for
mechanical multi-file work the master can spec cleanly.

When Ikenna runs **Model B — 1-main + dynamic spawned tabs** on a different cycle, the LEDGER's "Today's status → Tab
registry" section becomes the live spawning surface; new tabs queue under `🟡 Ready to spawn` until Ikenna opens a fresh
chat for them. Both models obey the same universal mechanics above; the LEDGER shape adapts.

## Differences from CLAUDE.md HARD RULE you should be aware of

The Daily Work-Split Process in CLAUDE.md is the SSOT for orchestration mechanics. This onboarding doc is just the
pointer + boot ack. **If anything in this doc contradicts CLAUDE.md, CLAUDE.md wins** — file an issue doc flagging the
drift.

## Useful cross-references

- **Workspace state right now**: [`LEDGER.md`](LEDGER.md) — today's tab registry, in-flight status, recent done, open
  questions across plans (Ikenna side).
- **Active intra-side pings**: [`_agent_pings.md`](_agent_pings.md) — short doorbell-style log; one line per active
  blocker (Ikenna's main ↔ Ikenna's spawned tabs).
- **Active cross-side pings**: [`../plans/active/_agent_pings.md`](../plans/active/_agent_pings.md) — Ikenna ↔ Harsh
  signalling only.
- **All workspace rules**: [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md).
- **Sub-agent inheritance**:
  [`../cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../cursor-configs/SUB_AGENT_MANDATORY_RULES.md).
- **Master plan**:
  [`../plans/active/master_to_live_defi_2026_05_23.md`](../plans/active/master_to_live_defi_2026_05_23.md).
- **Today's work-split**:
  [`../plans/active/work_split_2026_05_08_ikenna.md`](../plans/active/work_split_2026_05_08_ikenna.md).
- **Mirror doc on Harsh side**:
  [`../harsh_orchestrator/AGENT_ONBOARDING.md`](../harsh_orchestrator/AGENT_ONBOARDING.md).
