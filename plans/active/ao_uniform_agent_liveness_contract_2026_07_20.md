---
doc_type: plan
title: One liveness contract for every agent — stop teaching each reaper about roles
summary:
  One-off agents (plan_reconciler, plan_health, escalation crafts) never call /boot, so their slot reads idle for their
  whole run and every liveness subsystem must be independently taught not to kill them. Three carve-outs exist and a
  fourth reaper would need a fifth. Replace them with one protocol every agent follows, where the backend answers
  role-appropriately instead of each reaper special-casing kinds.
status: active # operator activated 2026-07-21 (slot-16). LOCAL execution (assigned_vm: NA) — this session works it, NOT AO-dispatched.
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
last_updated: 2026-07-21
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

## Status & history (activated 2026-07-21)

**ACTIVE as of 2026-07-21** — operator decided to start (slot-16 interactive). **LOCAL execution:** this session
implements it directly, NOT AO-dispatched (`assigned_vm: NA`, `execution_scope: local-only`) — a change to the AO's own
liveness code, on the live fleet it runs, is safer operator-supervised than auto-dispatched into a worker.

**How the scope settled** (the earlier "do-not-start" banners, now historical, condensed):

- **Original premise — RETRACTED (2026-07-20).** The plan first claimed one-offs never `/boot`, so their slot stays
  `idle` and `_reclaim_idle_lingering_sessions` reaps them mid-work. Wrong: the plan_reconciler DOES `/boot`
  (`slot_boot` 07:27:03) and DOES heartbeat. Typed agents already get `status="working"` on claim (`plan_health.py:283`,
  `escalation.py:476`) — so "their slot reads idle" must not be reintroduced as an argument.
- **Root cause — LANDED (2026-07-21).** Two failure modes, one missing contract. (1) **Reaped mid-work:** an unguarded
  `_reclaim_idle_lingering_sessions` could kill a live typed agent before the `f641968` guard existed (the 07-20
  diagnosis — `ao_scheduled_agent_hygiene_2026_07_20.md` P0). (2) **Finished-but-immortal — the dominant mode, measured
  07-21:** a one-off completes, "EXIT"s (ends its Claude _turn_ only), the session lingers at an idle prompt,
  `WorkerLivenessKicker` re-nudges it, and `has_session()==True` + a fresh heartbeat blind every reaper → the AgentRow
  stays `active` forever and pins its slot (15 zombies pinned 15/16 slots → reconciler `503 no free slot`). Full
  evidence: Progress Log 2026-07-21.
- **Design DECIDED (2026-07-21 operator).** Terminal transition for every `one_shot`/`scheduled` agent = complete → POST
  an explicit **role-aware `/done`** (archive `lifecycle-complete` + free slot + stop-nudge) → stop. That closes mode
  (2); the boot→`working` protocol (path 2) closes mode (1) and lets the carve-outs be deleted. Docs were reconciled to
  this contract BEFORE code (§2/§6 + the two codex SSOTs, `unified-trading-pm@468a7e67b`).

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
      min between heartbeats.** Operator design review: **DONE (2026-07-21)** — reconciled to the `/done`-then-stop
      decision; implementation restructured into the three workstreams below.

> **Restructured 2026-07-21 around the decided contract. Order = A → B → C.** **Workstream A (`/done` → archive → stop)
> is the leak fix and comes FIRST** — lowest risk, because it archives a FINISHED one-off without touching any carve-out
> (the carve-outs only protect MID-work agents, which A leaves untouched). B (boot→`working`) makes "working while
> working" a reliable signal; C deletes the now-redundant carve-outs LAST. Throughout: the backend accepts BOTH the old
> (never-`/done`) and new contracts, roles migrate one at a time, each verified live before the next.

### Workstream A — completion path (`/done` → archive → stop): the leak fix

- [x] [BACKEND] P1. **A1 — Extend `/done` to accept a task-less, role-aware completion.** ✅ CODE-COMPLETE (local,
      deploy-deferred) — `agent-orchestrator@31ef846` (unpushed); AO quality gate green (1543 passed) incl. 4 new
      `test_done_one_off` cases + Class-A `/done` unchanged; live-verify pending the coordinated deploy. Today `/done`
      hard-requires `task_id` + a plan-flip (`server/routes/slots_worker.py:616-767` → 404/409 for a task-less one-off).
      Add a Class-B completion path: no `task_id` / no plan-flip; it archives the AgentRow `lifecycle-complete`, frees
      the slot, and flags it so `WorkerLivenessKicker` stops nudging. Backend still accepts an un-migrated one-off that
      never `/done`s (existing pruner/reaper path unchanged). **Gate**: a task-less `/done` from a `plan_health`-shaped
      agent → 200, AgentRow archived, slot session-less/idle, no re-nudge; a fleet-worker `/done` (task + plan-flip)
      byte-for-byte unchanged (regression-tested); `quality-gates.sh` green.
- [x] [BACKEND] P1. **A2 — Rewrite the 5 role docs' non-functional "then EXIT" → "POST `/done` (completion) → stop."**
      ✅ CODE-COMPLETE (local, deploy-deferred) — all 5 role docs (`cicd`, `conflict_resolver`, `data_pipeline_failure`,
      `plan_health`, `plan_reconciler`) now POST `/done` with `one_shot_complete=true` then STOP; live-verify pending
      deploy. One role at a time, each verified live before the next: `cicd`, `conflict_resolver`,
      `data_pipeline_failure`, `plan_health`, `plan_reconciler`. Their "EXIT" today only ends the Claude turn; replace
      with the real completion call + stop. **Gate**: each role observed on completion → its `orch-slot-N` AgentRow
      archives `lifecycle-complete`, slot frees, no re-nudge, no manual `kill-session`. Cite the agent_id.
- [ ] [BACKEND] P2. **A3 — Add the completion step to the boot prompt** so it is uniform and an agent can't "forget" it.
      **Gate**: a freshly-booted one-off's rendered prompt carries the `/done`+stop step; a live run confirms it fires.

### Workstream B — boot → `working` (uniform liveness signal)

- [ ] [BACKEND] P1. **B1 — Make `/boot` role-aware + accept a task-less boot.** A one-off POSTs `/boot` like everyone;
      the response carries no task and the slot leaves `idle` for `working`. No parallel endpoint. Makes "working while
      working" reliable so idle-scanners skip one-offs by construction. **Gate**: a `plan_reconciler`-shaped boot → 200
      no task, SlotRow leaves `idle`; a fleet-worker boot byte-for-byte unchanged (regression-tested).
- [ ] [BACKEND] P2. **B2 — Close the startup-latency gap.** A one-off's first heartbeat comes after a startup phase
      (role-doc read, hygiene sweep) that can exceed the grace window. Require a STEP-0 ping before that phase, or
      measure grace from first-contact not spawn. **Gate**: a one-off with a deliberately slow (10+ min) boot proves
      liveness throughout.

### Workstream C — remove the duplication (LAST — only once A + B are proven live)

- [ ] [BACKEND] P1. **C1 — Delete the three carve-outs.** (a) prereq-reaper AgentRow guard (`1e7fec0`), (b)
      `_reclaim_idle_lingering_sessions` AgentRow guard (`f641968`), (c) boot-gate typed-spawn recognition (`5907317`)
      if the uniform contract subsumes it. Each deletion ships with a test proving the uniform signal
      (status=`working` + heartbeat, or archived-on-`/done`) now protects that agent instead. **Gate**: `rg` finds no
      typed-agent special-case in any reaper; the original regression tests still pass, protected by the contract.
- [ ] [DOC] P2. **C2 — Finish the codex / role-doc SSOT.** The two codex SSOTs are already reconciled (2026-07-21:
      `agent-orchestrator-single-vm-architecture.md` § Class B, `agent-orchestrator-worker-liveness.md` § completion
      contract). Remaining: every role doc references the codex SSOT rather than restating it, and the "being
      implemented / current pre-fix code" markers come out once the code lands. **Gate**: role docs point at codex; no
      in-flight markers remain; no plan↔codex drift.

## Design note (todo 1) — the uniform agent-liveness contract

> **Status: APPROVED (operator, 2026-07-21); reconciled to the `/done`-then-stop decision.** Written before any code,
> per the plan's "write down the contract first" rule. Subsystem inputs verified against live code
> (`agent-orchestrator@HEAD`); this is the design Workstreams A-C implement, and its codex SSOT
> (`codex/04-architecture/agent-orchestrator-worker-liveness.md`) is already reconciled (todo C2). The Gate for this
> todo — "a reader can answer 'why won't a one-off be reaped?' without reading any reaper's source" — is met by §5 + §6
> below.

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

| Class                                                                                                    | `/boot`                                                                                                          | periodic `/progress`            | `/done`                                                                                                                                                                                                                                                                  | Reaped by                              |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------- |
| **A — backlog worker**                                                                                   | yes (returns a task)                                                                                             | yes                             | yes (clean-tree+flip gated)                                                                                                                                                                                                                                              | normal lifecycle → idle → next         |
| **B — one-off** (`plan_reconciler`, `plan_health`, `cicd`, `conflict_resolver`, `data_pipeline_failure`) | **yes** (reconciler DOES `/boot` — `slot_boot` 07:27:03; the plan's original "never /boot" premise is retracted) | yes (role-doc mandated ≤10 min) | **yes** (2026-07-21 operator decision — role-aware task-less `/done` on completion → archive + free slot + stop-nudge, then stop; the next reap cleans the session. Supersedes the retracted "never `/done`, rely on session death" premise, measured broken 2026-07-21) | today: the 4 paths in §0               |
| **persistent** (`main`, review)                                                                          | yes                                                                                                              | yes                             | no                                                                                                                                                                                                                                                                       | keeper respawns; review-slot exemption |

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
like everyone else (so the two silence reapers never compute it as silent), and on finishing it POSTs an explicit
**role-aware `/done`** that archives it + frees the slot + flags it so `WorkerLivenessKicker` stops nudging it, then it
stops (the next reap cleans the now-dead session). The backend encodes "this is a task-less one-off" ONCE — in the
`/boot` response that moves it to `working` — instead of teaching each reaper to recognize its kind. A fourth reaper
added tomorrow inherits the protection for free, because it reads `status` + `last_ping` like the others, and a live
one-off looks identical to a live fleet worker on both.

> **⚠️ 2026-07-21 correction (operator decision).** This §6 originally read "its finish is a real session death that the
> pruner archives cleanly." **Measured false** on 2026-07-21: a finished one-off does NOT die — "EXIT" only ends the
> Claude turn, the session lingers at an idle `❯` prompt, the Kicker re-nudges it, and every session-death-gated reaper
> is blind → immortal (15 zombies pinned 15/16 slots → reconciler `503`). The terminal transition is therefore an
> **explicit role-aware `/done`**, not an inferred session death. See Progress Log 2026-07-21 and the codex updates
> (`agent-orchestrator-single-vm-architecture.md` § Class B, `agent-orchestrator-worker-liveness.md` § completion
> contract).

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
- **2026-07-21 (later) — operator decided the terminal-transition mechanism + docs-first reconciliation.** After the
  clear, a fresh escalation-drain wave produced 13 more finished `cicd` zombies (the same leak, refilling from a 32-deep
  `ldr_qg_failure` backlog, mostly resolving `qg_v2_green` = stale). The operator ruled: **do not keep clearing — fix
  the root cause.** Terminal transition for EVERY `one_shot` + `scheduled` agent = complete work → POST an explicit
  **role-aware `/done`** (backend archives `lifecycle-complete` + frees the slot + flags it so `WorkerLivenessKicker`
  stops nudging) → stop; the next reap cleans the session. This REVERSES the plan's original §2/§6 "Class B never
  `/done`" premise and the SAME premise in two codex docs. Per operator ordering (**docs before code**), reconciled now:
  (a) `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — Class-B banner + §Reap correction; (b)
  `codex/04-architecture/agent-orchestrator-worker-liveness.md` — new "one-off/scheduled completion contract" section
  (the 4th, finished-immortal failure mode); (c) this plan §2 row + §6 (above). **Code phase — NOT started, awaiting the
  operator's next audit:** extend `/done` to accept a task-less role-aware completion (today it hard-requires
  `task_id` + a plan-flip → 404/409 for a task-less one-off, verified in `server/routes/slots_worker.py:616-767`);
  archive + free + stop-nudge on it; rewrite all 5 role docs' non-functional "then EXIT" to the real `/done`+stop call
  (`cicd`, `conflict_resolver`, `data_pipeline_failure`, `plan_health`, `plan_reconciler`); add the completion step to
  the boot prompt; then delete the `f641968`/`1e7fec0` carve-outs.
