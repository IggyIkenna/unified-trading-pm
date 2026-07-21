---
doc_type: plan
title: One liveness contract for every agent — stop teaching each reaper about roles
summary:
  One-off agents (plan_reconciler, plan_health, escalation crafts) never call /boot, so their slot reads idle for their
  whole run and every liveness subsystem must be independently taught not to kill them. Three carve-outs exist and a
  fourth reaper would need a fifth. Replace them with one protocol every agent follows, where the backend answers
  role-appropriately instead of each reaper special-casing kinds.
status: draft # NOT ingested — operator review pending (2026-07-20). Flip to `active` to start.
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, liveness, boot-protocol, reaper, architecture]
related:
  [
    ao_dispatch_liveness_p0_2026_07_20.md,
    ao_scheduled_agent_hygiene_2026_07_20.md,
    ao_worker_lifecycle_reap_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo protocol change; the design decision is made below, execution is staged
thinking_tier: high # a live-fleet protocol migration — the staging order is the risky part
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# One liveness contract for every agent

> **Operator decision 2026-07-20**: of the two paths considered — (1) make each reaper role-aware, or (2) make every
> agent follow the same register/boot/heartbeat protocol with role-appropriate backend responses — **path 2 is chosen**.
> This plan implements it.

## ✅ UPDATE 2026-07-20 (slot-16 interactive) — the root cause IS now diagnosed; re-scope this plan accordingly

The root-cause investigation this plan was waiting on has landed (`ao_scheduled_agent_hygiene_2026_07_20.md`, the P0
todo — full evidence there). **Cause (airtight on the defect, ~90% on the fatal blow):** an UNGUARDED
`WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` reaped `agt-751738` at 07:32:30 (`kill_session`,
worker_liveness_watchdog.py:1212), because (A) its slot read `status=idle` while claude was demonstrably alive and
working (tick-1 ~07:31:25, a full minute before the transcript's last write) and (B) at that moment the idle-reclaimer
had **no typed-agent exemption** — the `f641968` guard was committed 1h38m LATER (09:10 UTC vs the 07:32:30 kill). A
reaper ticking down to kill a live typed agent is the confirmed bug; whether the 07:32:30 `kill_session` was the fatal
blow vs. reaped a ~1s-old corpse is ~90% (`remain-on-exit on` defeats the `has_session` proof, but the self-exit
alternative has no surviving cause — usage was 5h=5% 80s prior, no rate-limit/OOM/error). Either way this is a
**liveness-signalling** cause — squarely in this plan's domain, NOT an unrelated API/usage cutoff.

**Consequences for this plan:**

- The line below "the motivating bug is NOT diagnosed, so this plan must not be started" — the **first clause is now
  false**. The bug is diagnosed. But **do not big-bang-start this plan either**: the cheapest correct next move is to
  verify `f641968` (already deployed) actually fixes it on todo 4's next reconcile run. The claim (in this plan and the
  hygiene plan) that "`f641968` did NOT fix this" is **unsound** — it was inferred from a death that predates `f641968`
  by 1h38m. `f641968`'s AgentRow-keyed guard plausibly works; it is simply UNTESTED. **If that one live run confirms the
  guard exempts the reconciler, this plan reverts to exactly the "pure de-duplication refactor at much lower priority"
  case it already anticipated below** — the three carve-outs are real duplication worth removing, but the urgency is
  gone. If the guard is somehow defeated (e.g. restart clears the AgentRow), that failure mode feeds directly into this
  plan's uniform-contract design. Either way: **gate flipping this to `active` on that single live observation, not on
  new code.**
- **What is still true:** "typed agents get `status='working'` on claim" (plan_health.py:283) IS the code path — but the
  reconciler was nonetheless reaped as `idle`, which means the `working` status did NOT survive to kill time
  (empirically flipped to `idle` around the 07:30 restart; the exact line is unpinned — residual R1 in the hygiene
  plan). So the "their slot reads idle" framing this plan warns against is **not simply false** after all: for a typed
  one-off it can become true in flight. That nuance belongs in the contract design (todo 1).

## ⚠️ READ FIRST — the evidence this plan was built on has been RETRACTED (2026-07-20)

This plan originally opened with a confident mechanism: that one-off agents never call `/boot`, so their slot stays
`idle` and `_reclaim_idle_lingering_sessions` reaps them mid-work. **That was wrong and is withdrawn.** The
plan_reconciler demonstrably DOES call `/boot` (`slot_boot` 07:27:03) and DOES heartbeat (`slot_progress` 07:28:18); no
reclaim event ever fired; and `tmux_session_lost` is the TmuxPruner OBSERVING an already-dead session, not killing one.
Full disproven list + the live handoff: `ao_scheduled_agent_hygiene_2026_07_20.md`, the P0 root-cause todo.

**Consequence: the motivating bug is NOT diagnosed, so this plan must not be started as an implementation.** Its
destination may well still be right — three separate per-subsystem carve-outs for "typed agents are special" do exist
(`1e7fec0`, `f641968`, `5907317`), and that duplication is real and independently worth removing. But the _route_ and
the _urgency_ both depend on a root cause nobody has established yet.

**What is still independently true** (verified, not inferred):

- Typed agents already get `status="working"` on claim (`plan_health.py:283`, `escalation.py:476`) — so any future
  argument based on "their slot reads idle" is false and must not be reintroduced.
- Three carve-outs teach three different subsystems the same fact; a fourth reaper would need a fourth.
- `agent-orchestrator@f641968` was shipped on the retracted premise. It is defensively harmless and its regression test
  is real, but it did not fix the reconciler.

**Do not flip this to `active` until the root-cause investigation lands.** If the cause turns out to be unrelated to
liveness signalling (an API/usage cutoff, a crash), this plan becomes a pure de-duplication refactor at much lower
priority — and should be re-scoped accordingly rather than executed as written.

## What "uniform" means here — and what it does not

**It does not mean identical payloads.** It means one PROTOCOL — register → boot → heartbeat → finish — with
**role-appropriate responses**. A fleet worker's `/boot` returns a task; a one-off's returns "no task, you already know
your work". Same handshake, different answer. The backend keeps the role knowledge in ONE place (the boot response)
instead of scattering it across every reaper.

**The heartbeat is the load-bearing piece, not `/boot`.** What made the reconciler look dead was `last_msg: NULL` for
seven minutes. `/boot` matters because it moves the slot off `idle`; the heartbeat matters because it is the ongoing
proof of life. Get both uniform and the carve-outs become deletable.

## ⚠️ Migration risk — this is a live fleet

Changing every agent's boot prompt at once can wedge the entire fleet: an agent that fails the new handshake never
boots, and the fleet has no workers. **Stage it.** The backend accepts BOTH contracts first, roles migrate one at a
time, and the carve-outs come out LAST — only once every role is proven on the new path.

## Execution environment — LOCAL

Operator-assigned agents on this host (`assigned_vm: NA`, `execution_scope: local-only`). Tick checkboxes by hand. Code
and tests are local (`bash scripts/quality-gates.sh`). Live confirmation needs read-only SSM (pattern:
`scripts/orchestrator/check-ao-backlog-status.sh`). **Never restart the live service without asking.**

## Todos

- [x] ✅ [BACKEND] P1. **Write down the contract before changing any code.** — DRAFT written as the "## Design note
      (todo 1)" section below (slot-16 interactive, `unified-trading-pm@<this commit>`). Covers all six Gate items:
      states (§1), which call each class makes (§2), `/boot` per role (§3), heartbeat cadence (§4), what each subsystem
      concludes after the change naming every consumer — idle-reclaim, prereq reaper, heartbeat-silent, HealthMonitor
      working/idle-stale, stuck/context-full, TmuxPruner, AutoSpawn, `_pick_free_slot`, boot-gate (§5) — and the Gate
      answer "why won't a one-off be reaped?" without reading any reaper's source (§6). Subsystem inputs verified
      against live `agent-orchestrator@HEAD` (Explore map + direct reads). **Surfaced a plan-reframing finding (§0): the
      reconciler is exposed to ≥4 reaper paths, only 2 carry a carve-out — the 15-min heartbeat-silent trigger and
      25-min HealthMonitor working-stale flip are UNGUARDED — so `f641968` alone does NOT protect a run that goes >15
      min between heartbeats.** **⚠️ PENDING OPERATOR DESIGN REVIEW before todos 2-7 (code) start** — this todo is
      "write the contract first" precisely so the design is validated before implementation.
- [ ] [BACKEND] P1. **Make `/boot` role-aware and accept a task-less boot.** A one-off POSTs `/boot` like anyone else;
      the response carries no task and the slot transitions out of `idle` into a state that means "occupied and
      working". Do NOT invent a parallel endpoint — that is path 1 wearing a different hat. **Gate**: a
      plan_reconciler-shaped boot returns 200 with no task, the SlotRow leaves `idle`, and an existing fleet-worker boot
      is byte-for-byte unchanged in behaviour (regression-tested).
- [ ] [BACKEND] P1. **Backend accepts BOTH contracts during migration.** Old-style one-offs (no `/boot`) must keep
      working exactly as today — including the three carve-outs, still in place — while the new path is proven.
      **Gate**: a test matrix covering {old, new} × {fleet worker, one-off} all behaving correctly; nothing regresses
      for an agent that has not migrated.
- [ ] [BACKEND] P2. **Migrate the role docs one at a time, starting with `plan_reconciler`.** Add the STEP-0 liveness
      ping + `/boot` to its boot procedure, keeping its existing `/progress` heartbeat guidance. `plan_reconciler` first
      because it is the one measurably being killed and the easiest to observe. **Gate**: one full reconcile run
      observed booting, heartbeating, and surviving past the 420s window that used to kill it — cite the dispatch_id.
- [ ] [BACKEND] P2. **Migrate the remaining one-off roles** (`plan_health`, and the escalation crafts — `cicd`,
      `conflict_resolver`, `data_pipeline_failure`). One at a time, each verified live before the next. **Gate**: each
      role has a run observed on the new contract; none regressed.
- [ ] [BACKEND] P2. **Close the startup-latency gap that made this bite.** The reconciler's first heartbeat comes after
      a startup phase (reading role docs, running the hygiene sweep) that can exceed the grace window. Either require a
      STEP-0 ping before that phase, or make the grace window measure from first-contact rather than spawn. **Gate**: a
      one-off whose startup takes 10+ minutes still proves liveness throughout — test with a deliberately slow boot.
- [ ] [BACKEND] P1. **Delete all three carve-outs — the plan is not done until they are gone.** (a) the AgentRow guard
      in the prereq reaper (`1e7fec0`), (b) the AgentRow guard in `_reclaim_idle_lingering_sessions` (`f641968`), and
      (c) the typed-spawn recognition in the boot gate (`5907317`) if the uniform contract subsumes it. Each deletion
      must be accompanied by a test proving the uniform signal now protects that agent instead. **Gate**: `rg` finds no
      typed-agent special-case left in any reaper; the regression tests from those commits still pass, now protected by
      the contract rather than the carve-out.
- [ ] [DOC] P2. **Record the contract in codex and point the role docs at it.** This is a durable architectural rule, so
      its SSOT is a codex doc, not this plan. **Gate**: a codex doc describes the contract; every role doc references it
      rather than restating it; `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` links to it.
- [ ] [BACKEND] P1. **Define the terminal transition for a task-less one-off — "finished ⇒ the process EXITS."**
      (Discovered 2026-07-21 from the 15-agent JSONL post-mortem — see Progress Log 2026-07-21.) The contract as drafted
      has NO trigger that stops a one-off: §2 says Class B "never `/done`" and heartbeats ≤10 min, and §6 assumes its
      finish is "a real session death" — but nothing bridges the two, so a one-off that finishes its work keeps
      idle-polling forever. Measured live: `cicd`/`plan_health` agents ran 5 min–**19 h** AFTER completing, never
      reaped, each pinning a slot (the direct cause of the 07-21 reconciler `503 no free slot`). The live idle session
      keeps `has_session()==True` and the heartbeat keeps `SlotRow.last_ping` fresh, so all six paths in §0 are defeated
      at once. The role doc / `/boot` response for Class-B one-offs must make the agent EXIT the process after posting
      its result (not loop-poll), so `has_session()` goes False and the existing pruner/reclaim archive it cleanly.
      **Gate**: a finished one-off's `orch-slot-N` session dies on its own within one heartbeat interval of completion,
      the AgentRow archives `lifecycle-complete`, and the slot returns session-less — observed live, no manual kill.

## Design note (todo 1) — the uniform agent-liveness contract

> **Status: DRAFT for operator review (slot-16 interactive, 2026-07-20).** Written before any code, per the plan's
> "write down the contract first" rule. Subsystem inputs verified against live code (`agent-orchestrator@HEAD`); this is
> the design todos 2-7 implement and todo 8 promotes to `codex/04-architecture/agent-orchestrator-worker-liveness.md`.
> The Gate for this todo — "a reader can answer 'why won't a one-off be reaped?' without reading any reaper's source" —
> is met by §5 + §6 below.

### §0. The finding that reframes the whole plan — carve-outs are whack-a-mole (≥4 reaper paths, 2 guarded)

The reconciler is not killed by ONE reaper; it is exposed to **at least four independent kill/flip paths, and only two
carry a typed-agent carve-out today.** Every path keys off a per-slot silence/idle signal that a one-off does not
advance the way a fleet worker does:

| Subsystem (code)                                                      | Signal it reads                                           | Threshold                             | Action                                                              | Typed carve-out?                                     |
| --------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------- |
| `_reclaim_idle_lingering_sessions` (watchdog:1103)                    | `SlotRow.status ∈ {idle,stale}` + `has_session`           | boot-grace 300s + 2 ticks ≈ **7 min** | `kill_session` + reset                                              | ✅ `f641968` (AgentRow.tmux_session)                 |
| `_release_prereq_blocked_slots` (watchdog:1234)                       | `status ∈ {idle,stale}` + queue-prereq-blocked            | **1 h**                               | requeue + `kill_session`                                            | ✅ `1e7fec0` (same set)                              |
| **watchdog main loop `_tick_once` → heartbeat-silent (watchdog:801)** | `effective_silence(last_ping,spawned,assigned) > timeout` | **15 min**                            | `_resume_or_fresh_respawn` (kill)                                   | ❌ **NONE** (review-slot only)                       |
| **HealthMonitor working-slot stale-flip (health.py:186)**             | `status=='working'` + silence anchor                      | **25 min**                            | flip → `stale` (then reapable)                                      | ❌ **NONE** (agent-pass exempts, slot-pass does not) |
| watchdog main loop → stuck-at-prompt / context-full / session-gone    | pane regex / `has_session`                                | 180s / immediate / 90s                | `kill_session`                                                      | ❌ none (pane-shielded for thinking)                 |
| TmuxPruner (tmux_pruner.py)                                           | `has_session==False` on a set `tmux_session`              | 30s grace                             | OBSERVE: clear ref, archive one_shot/scheduled `lifecycle-complete` | n/a (archives, doesn't kill)                         |

**Consequence for `f641968` (corrects the root-cause plan's "plausibly fixes it"):** `f641968` closes only the 7-min
idle-reclaim. A reconciler that survives that then faces the **UNGUARDED** 15-min heartbeat-silent trigger and the
25-min working-stale flip. Its ONLY protection there is its role doc's mandate to post `/progress` every ≤10 min
(`agents/plan_reconciler.md:96`), which advances `last_ping` under the 15-min bar. That is discipline, not a contract —
**any run that goes >15 min between heartbeats (a long STEP-5/6 sub-agent phase) is killed by an unguarded reaper.**
(agt-751738 died at 7 min to the idle-reclaim before this mattered, and had heartbeated once at 07:28:18 — so the 07-20
root cause remains the unguarded idle-reclaim; this §0 is the DEEPER structural problem the contract must close.)

### §1. The protocol — one handshake, role-appropriate answers

Four states, each entered by an HTTP call every agent class makes; `blocked` is an orthogonal axis, not a state.

```
register ──/boot──▶ working ──/progress (heartbeat, load-bearing)──▶ … ──/done──▶ finished
                       │                                                    ▲
                       └───────────── /blocked (orthogonal) ────────────────┘  (watchdog never reaps status=blocked)
```

### §2. Which call each agent class makes (verified)

| Class                                                                                                    | `/boot`                                                                                                          | periodic `/progress`            | `/done`                                                                                      | Reaped by                              |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------- |
| **A — backlog worker**                                                                                   | yes (returns a task)                                                                                             | yes                             | yes (clean-tree+flip gated)                                                                  | normal lifecycle → idle → next         |
| **B — one-off** (`plan_reconciler`, `plan_health`, `cicd`, `conflict_resolver`, `data_pipeline_failure`) | **yes** (reconciler DOES `/boot` — `slot_boot` 07:27:03; the plan's original "never /boot" premise is retracted) | yes (role-doc mandated ≤10 min) | **no** (Class B never `/done`; TmuxPruner/`reap_orphan_agents` archive `lifecycle-complete`) | today: the 4 paths in §0               |
| **persistent** (`main`, review)                                                                          | yes                                                                                                              | yes                             | no                                                                                           | keeper respawns; review-slot exemption |

### §3. What `/boot` returns per role (todo 2)

Same endpoint, role-appropriate body — NOT a parallel endpoint (a parallel endpoint is path 1 wearing a hat):

- **Fleet worker** → `{task: <TaskRow>}`; slot `idle → working`, `current_task` set.
- **One-off** → `{task: null, ack: "no task — you already know your work from your role doc"}`; slot `idle → working`,
  `current_task` null, `spawn_base_role` set. The transition off `idle` is the point: it removes the one-off from BOTH
  idle-scanning reapers (idle-reclaim, idle-stale) without a carve-out.

### §4. Heartbeat cadence — the load-bearing signal

Every agent posts `/progress` at **≤ `watchdog_heartbeat_timeout`/2** (currently 15 min → **≤7.5 min**, so the role-doc
"≤10 min" should tighten to ≤7 min). `/progress` (`progress_slot` → `update_slot_ping`) advances `SlotRow.last_ping`,
which is the `max(last_ping, last_spawned_at, assigned_at, session_created)` anchor every silence-based reaper measures
from. **`/boot` moves the slot off `idle`; the heartbeat is the ongoing proof of life** — get both uniform and every
carve-out becomes deletable.

### §5. What each subsystem may conclude AFTER the contract (the invariant)

**Invariant: no reaper special-cases `agent_kind`/`lifecycle`.** Each trusts the same three uniform signals, so the role
knowledge lives in ONE place (the `/boot` response), not scattered across reapers:

- **idle-reclaim / idle-stale / prereq-release** (idle-scanners): a booted one-off is `status=working`, never `idle` →
  out of scope by construction. The `f641968`/`1e7fec0` `typed_agent_sessions` carve-outs become dead code → deleted
  (todo 7).
- **heartbeat-silent (watchdog) + working-stale (HealthMonitor)**: read `effective_silence` from `last_ping`. A one-off
  that heartbeats ≤ timeout/2 is never silent → never reaped. The carve-out these paths NEVER had is not needed, because
  the one-off now advances the same anchor a fleet worker does.
- **stuck-at-prompt / context-full**: pane-content triggers, kind-agnostic already — unchanged (a genuinely wedged
  one-off SHOULD be reaped).
- **TmuxPruner / `reap_orphan_agents`**: unchanged — on real session death they archive `lifecycle-complete`. Correct
  for a one-off that finished without `/done`.
- **AutoSpawn / `_pick_free_slot`**: "free" = session-less (not status) — unchanged; a `working` one-off holds a live
  session so it is never picked. **`_pick_free_slot` MUST stay session-based** (removing that is out of scope).
- **`/boot` read-gate**: keeps `spawn_base_role` (`5907317`) UNLESS the uniform boot subsumes it (todo 7c) — the gate is
  about which role-doc files were read, orthogonal to liveness; delete only if the uniform boot carries the base role.

### §6. Why a one-off will NOT be reaped (the Gate answer, no reaper source required)

A one-off boots like everyone else (→ `working`, so the two idle-scanning reapers can't see it), heartbeats ≤ timeout/2
like everyone else (so the two silence reapers never compute it as silent), and its finish is a real session death that
the pruner archives cleanly. The backend encodes "this is a task-less one-off" ONCE — in the `/boot` response that moves
it to `working` — instead of teaching each reaper to recognize its kind. A fourth reaper added tomorrow inherits the
protection for free, because it reads `status` + `last_ping` like the others, and a live one-off looks identical to a
live fleet worker on both.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Do not delete a carve-out before its replacement is proven live.** The carve-outs are currently the only thing
  keeping one-off agents alive; removing one early re-opens the exact bug this plan exists to close, on a live fleet.
- **Migrate one role at a time.** A big-bang boot-prompt change that fails leaves the fleet with no working agents and
  no easy way to notice, because the failure mode is silence.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — slot/worker/dispatch model this refines.
- `codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — the liveness
  subsystems whose inputs this changes.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured terminal verdicts for the live gates.

## Progress Log

- **2026-07-20 — plan created** after the transcript evidence settled the design question. Worth preserving: the earlier
  hypothesis was that the reconciler was dying on spawn (an account cap or bad opus/effort flags). The transcript
  disproved it in one read — 436 KB of productive work ending mid-task. **When an agent "fails silently", read its JSONL
  before theorising about why it died; it may not have died at all.**
- **2026-07-20 — root cause landed; "premise not diagnosed" banner updated (slot-16 interactive).** The blocking
  investigation (hygiene plan P0 todo) is closed: `agt-751738` was killed by the idle-lingering reclaimer at 07:32:30
  while unguarded (the `f641968` exemption postdates the kill by 1h38m). This is a liveness-signalling cause, in this
  plan's domain. Net effect on this plan: the motivating bug is diagnosed, but the correct next step is a single live
  verification of `f641968` (not new code) — if it confirms, this plan is a lower-priority de-dup refactor (as the plan
  itself anticipated). Left `status: draft`; the flip-to-active gate is now that one live observation, per the ✅ UPDATE
  section above. See `ao_scheduled_agent_hygiene_2026_07_20.md` P0 for the full evidence trail.
- **2026-07-21 — LIVE FLEET CLEAR + 15-agent JSONL post-mortem (slot-16 interactive).** The fleet had saturated: 15 of
  16 slots pinned by zombie typed-agent records (9 `cicd` one_shot + 6 `plan_health` scheduled), all `status=active`,
  which produced the reconciler's 07-21 `503 no free slot`. Cleared them live by killing the 15 lingering `orch-slot-N`
  sessions; the backend's own `tmux_pruner` archived all 15 `lifecycle-complete` within 45 s and recycled the slots
  (registry 16 → 3 non-archived: main + review [auto-relaunched] + one fresh cicd escalation; `/health` 200). All 15
  JSONLs preserved to scratchpad before the kill.
  - **The post-mortem overturns the "one-off gets killed" framing for THIS class — the opposite happened.** Reading all
    15 transcripts: **not one agent errored or crashed. Every one COMPLETED its task and then fell into an infinite
    idle-poll loop instead of exiting.** cicd agents resolved their escalation (mostly "stale — CI already green, no fix
    required") then polled `idle / new_task: null`; plan_health finished their sweep and did the same. Representative
    endings — agt-412d4a: "Idle, no new task (**179th poll**), unchanged"; agt-896605: "I'm not going to keep
    re-querying the same idle state — I've confirmed three times there's nothing dispatched"; agt-3526a5: "armed a
    15-minute check-in rather than busy-polling." Runtimes AFTER completion: cicd 5 min–18.5 h, plan_health **16–19 h**
    (agt-fac158 07-20 09:13 → 07-21 04:30, 499 assistant turns). These agents were **never reaped — they survived,
    heartbeating, for up to 19 h.**
  - **Why they were immortal — the empirical correction to §6.** §6 asserts a one-off's "finish is a real session death
    that the pruner archives cleanly." **That assumption is FALSE for this class.** The one-off finishes its work but
    the claude PROCESS never exits — it sits at an idle `❯` prompt and keeps posting `/progress`. Consequences, all
    measured live: (a) the heartbeat advances `SlotRow.last_ping` (§4) but NOT `AgentRow.last_ping` — verified: slot-2
    `last_ping=07-21 04:30` (fresh) while its bound `agt-59e680.last_ping=07-20 09:58` (frozen at claim) — so the two
    **silence** reapers (heartbeat-silent 15 min, working-stale 25 min) never fire, the slot looks alive; (b) the two
    **idle-scanning** reapers are carve-out-exempted (`f641968`/`1e7fec0`) while the AgentRow is non-archived; (c)
    `tmux_pruner` + `reap_orphan_agents` are `has_session==False`-gated → the live idle session means they never fire;
    (d) `_reclaim_idle_lingering_sessions` — the ONE reaper built to kill lingering-finished sessions — is the same
    reaper `f641968` disabled for typed agents, and because a one-off never `/done`s the carve-out cannot distinguish
    finished from working, so it protects finished ones forever. **Net: a FINISHED one-off is immortal under the current
    contract.** Proven the instant I killed each session — the pruner archived it in < 45 s (the cleanup path is
    correct; it simply never receives the session-death signal).
  - **The gap in the design (captured as the new P1 todo above).** The contract has no "**one-off is DONE → exit now**"
    trigger: §2 says Class B "never `/done`" and heartbeats ≤10 min; §6 assumes the finish is a real session death;
    nothing bridges them. The one-off heartbeats forever because nothing tells it to stop. Fix: the terminal transition
    for a task-less one-off must be a real **process exit** after it posts its result.
  - **Causal link — the reconciler 503 IS this bug's downstream (mode #1 ↔ mode #2).** The "survive-forever" mode
    directly caused the dispatch starvation: accumulated zombies pinned 15/16 slots → `_pick_free_slot` (session-based)
    found no session-less slot → `503 no free slot`. The plan's §0 "reconciler dies too early" and this "one-off
    survives forever" are two symptoms of the same missing contract, and they feed each other — finished one-offs that
    never exit starve the next one-off of a slot.
  - **Benign latent state noted (not actioned):** the killed-slot orphan-reclaim (`worker_liveness_watchdog.py:636-655`)
    only acts on `killed` slots whose session is still ALIVE; a `killed` slot whose session is GONE is left `killed`
    until AutoSpawn reuses it (`autospawn.py:678/739` treat `killed`/`stale` as spawnable). Cosmetic on the dashboard,
    not a dispatch blocker.
