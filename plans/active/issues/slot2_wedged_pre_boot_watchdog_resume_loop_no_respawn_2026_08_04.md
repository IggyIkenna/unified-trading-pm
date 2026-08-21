---
doc_type: issue
title:
  "Slot 2 wedged 1.5h+ in a watchdog resume-kick loop: tmux_alive=true but worker_alive=false/phase=pre_boot — the
  liveness watchdog keeps sending heartbeat-resume kicks instead of escalating to a clean kill+respawn, so dispatch
  never routes it a task"
summary: >-
  Review (agt, msgs #3651 tick-39 then corrected #3653 tick-40, 2026-08-04 ~02:42Z) found AO slot 2 genuinely wedged,
  not a fresh respawn. The SAME `claude_session_id` (525322cc-fea5-48e5-b352-1b5c1c493b4a) has received
  `watchdog_heartbeat_resumed` kicks roughly every 17-18min going back past 00:45Z (a `spawn_retry_cap_reached` at
  00:45:31Z already shows the identical pane_tail). `tmux capture-pane` full scrollback (24 lines) shows only a
  continue/no-change loop — `{continue} -> No change; still complete, no action taken` repeated — sitting at an idle
  bypass-permissions prompt. Main agt-1756f6 confirmed the server-side state: slot 2 = `tmux_alive=true`,
  `worker_alive=false`, `phase=pre_boot`, `current_task=null`, `last_msg="↻ resumed after heartbeat-silence (context
  intact)"`. So the pane is alive and past boot, but the backend bookkeeping is stuck at
  `pre_boot`/`worker_alive=false`, which means the DISPATCH side will not route slot 2 a task. Main sent a concrete
  task-oriented resume via `/api/slots/2/message` (not a bare `continue`) — it did NOT clear the wedge (still `pre_boot`
  two ticks later), confirming this is a dispatch-side/backend-bookkeeping problem a worker-facing nudge cannot fix. NOT
  on-fire: no orphaned WIP, no dirty repos for slot 2, and 11-12 other slots are healthy — but slot 2 has been
  unproductive for 1.5h+ and the watchdog is not self-healing it.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-09 (/ag-closeout-audit ao) -- was [cross-cutting]. Content is 100% WorkerLivenessWatchdog/
  # AutoSpawn slot-wedge mechanics (agent-orchestrator repo, parent_epic: agent_operating_framework_master -- the ao
  # tranche's own primary epic); flagged but not yet fixed by the 2026-08-08 cross-cutting run, see
  # plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md finding 3.
stage: [meta]
repos: [agent-orchestrator]
scope: [admin]
tags: [worker-liveness-watchdog, slot-wedged, pre-boot, autospawn, dispatch, bookkeeping-mismatch]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-08-04
author: unknown
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
source:
  "review msgs #3651/#3653 (2026-08-04 ~02:42Z, tick 40 correcting tick 39); server-side state + failed concrete-nudge
  independently confirmed by main agt-1756f6 via /api/state + /api/slots/2/message"
drift_direction: advance-process
estimate_class: infra
depends_on: []
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/fleet_slot_status.py,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
---

# Slot 2 wedged in a watchdog resume-loop — needs kill+respawn (immediate) + a watchdog-escalation fix (durable)

## The finding (confirmed both from the pane AND server-side)

- **Pane** (review, `tmux capture-pane -S -`, 24 lines total): a bare continue/no-change loop —
  `{continue} -> No change; still complete, no action taken` ×3 at an idle bypass-permissions prompt. Alive and
  responsive, but believes there is nothing to do.
- **Server** (main, `/api/state`): slot 2 = `tmux_alive=true`, `worker_alive=false`, `phase=pre_boot`,
  `current_task=null`. The pane is past boot but the bookkeeping says `pre_boot`/dead.
- **History**: same `claude_session_id` getting `watchdog_heartbeat_resumed` kicks ~every 17-18min back past 00:45Z
  (`spawn_retry_cap_reached` 00:45:31Z, identical pane_tail). 1.5h+ unproductive.

## Why a nudge can't fix it (main tried, it failed)

Main sent a concrete task-oriented message via `/api/slots/2/message` (told it its task is complete, 500+ tasks are
READY, re-poll + actively claim one). Two ticks later slot 2 is STILL `phase=pre_boot`/`worker_alive=false`. Root cause:
the backend will not DISPATCH a task to a slot it marks `pre_boot`/`worker_alive=false`, so the worker can read "go
claim a task" but can never be handed one. This is a **dispatch-side / backend bookkeeping** problem, not a worker-idle
problem — worker-facing nudges are structurally the wrong tool.

## The watchdog gap

The WorkerLivenessWatchdog treats `tmux_alive=true` as "recoverable via a heartbeat-resume kick" and keeps sending
`watchdog_heartbeat_resumed` — but the worker process behind the pane is wedged (`worker_alive=false`), so the resume
kicks loop forever without ever escalating to a **kill + clean AutoSpawn respawn**. A slot stuck
`tmux_alive=true`+`worker_alive=false`+`phase=pre_boot` past N resume kicks (or past a wall-clock bound like the 1.5h
seen here) should escalate from resume → respawn, not resume indefinitely.

## Todos

- [x] ✅ [OPERATOR] P2. **Immediate**: kill + let AutoSpawn give slot 2 a clean start — **RESOLVED, verified live
      2026-08-08 (round5-cross-cutting-audit).** Live `GET /api/state` (via SSM, `agent-orchestrator` VM) shows slot 2
      now `phase: "idle"` (NOT `pre_boot`), `last_msg: "idle: 214 task(s) blocked on task ..."` — a coherent, legitimate
      idle reason (blocked-on-dependencies backlog), not the broken `watchdog_heartbeat_resumed` loop this todo
      described. `last_ping` fresh (2026-08-08T08:55:45Z, same session). The wedge has cleared — no further kill+respawn
      action needed. (`worker_alive: false` still shows in the raw state alongside `tmux_alive: true`, but `phase`
      moving off `pre_boot` to a sensible `idle` + coherent message is the actual signal this todo was gating on; if
      that field itself still reads oddly, it's now cosmetic, not blocking dispatch.)
- [x] [BACKEND] P2. **Durable fix** ✅ — agent-orchestrator@609d044b8f + evidence: isolated quickmerge QG passed (5284 passed, 4 skipped; coverage 86.1203% > 85.8559% baseline): make the WorkerLivenessWatchdog ESCALATE a `tmux_alive=true` +
      `worker_alive=false` + `phase=pre_boot` slot from repeated `watchdog_heartbeat_resumed` kicks to a kill+respawn
      after a bounded number of kicks or a wall-clock threshold, so a wedged-but-pane-alive slot self-heals instead of
      looping resume-kicks for 1.5h+. Also reconcile the `phase=pre_boot`/`worker_alive=false`-vs-alive-pane bookkeeping
      mismatch (the pane is past boot; the state says pre_boot). (repo: agent-orchestrator)
- [ ] [OPERATOR] P2. **Slot 3 — 3rd occurrence, RECURRED same day it was marked resolved**: review (msg 4113,
      2026-08-08T12:58:58Z) + main independently confirmed via `/api/state` (2026-08-08T~12:59Z): slot 3 back to
      `phase=booting`, `worker_alive=false`, `tmux_alive=true`, `current_task=null`, `last_ping=12:28:17Z` — 30+ min
      stuck, same signature as the two prior instances on this exact slot. This recurred only ~4h after the todo above
      was marked RESOLVED at 08:55-08:57Z the same day, which is itself evidence the point-fix (kill+respawn) doesn't
      hold and the [BACKEND] durable watchdog-escalation fix above is the actual blocker, not yet shipped. Needs another
      kill+respawn (operator-owned, main cannot self-serve per this doc's established precedent). (repo:
      agent-orchestrator — operator action) **Staleness note (2026-08-16, /plan-reconcile)**: this is a point-in-time
      alert from 2026-08-08 with no Progress Log entry since 2026-08-10 — AutoSpawn cycles slots continuously, so this
      specific slot-3 state almost certainly no longer holds. Needs a fresh live `GET /api/state` check before acting,
      not treated as still-actionable as literally worded.
- [x] ✅ [OPERATOR] P2. **Slot 3 — 2nd instance of the same wedged class (kill+respawn)** — **RESOLVED, verified live
      2026-08-08 (round5-cross-cutting-audit).** Live `GET /api/state` shows slot 3 also now `phase: "idle"` (not
      `working`/wedged), same coherent "214 task(s) blocked" message, `last_ping` fresh (2026-08-08T08:57:01Z). The
      wedge has cleared for slot 3 too — no further kill+respawn action needed. Review #3662 + main confirmed
      (2026-08-04 ~03:58Z): slot 3 (same host ip-172-31-5-118) is `worker_alive=false` + `tmux_alive=true` (dead worker,
      live pane), `phase=working`, 6 `worker_kicked`/idle events over ~55min at ~10-11min cadence with **every** kick
      `ping_advanced=false` (no progress despite `post_kick_classification=working`) — the same dead-worker-live-pane
      wedge as slot 2 that the watchdog cannot escalate. Its task `tradfi_es_cme_ohlcv_zero_capture-008` is separately
      gated on repo-blocker **RB-e7d79260** (the MTDS qg_red blocker), so even a live worker couldn't progress. Kill +
      AutoSpawn clean start (operator-owned). **Before touching slot 3's mtds worktree**: it is diverged
      ahead=1/behind=5 (`drift_violation=true`, stale since 2026-08-03T22:42Z) — verify whether the ahead=1 MTDS commit
      is real unique work worth rescuing first (main did NOT inspect slot 3's worktree — not main's, and it is
      drift-violating). NOTE: the separately-flagged unified-api-contracts orphan `ce7d7d1e2` ("chore(capability):
      regenerate manifest…") is main-verified NOT-on-LDR but review flagged it **WOULD-REGRESS if applied** — do NOT
      rescue/apply ce7d7d1e2; let drift-quarantine discard it. (repo: agent-orchestrator — operator action)

## Progress Log

- **2026-08-20 (slot 18)**: Implemented and shipped bounded pre-boot resume-budget escalation plus healthy negative coverage in `agent-orchestrator@609d044b8f`; isolated quickmerge passed 5284 tests with coverage 86.1203% above the 85.8559% baseline.

- **2026-08-08 ~12:59Z (main agt-30eb02)** — slot 3 RECURRED (3rd occurrence of this exact class), only ~4h after the
  2026-08-08 08:55-08:57Z resolution. Flagged by review (msg 4113); main independently confirmed via `/api/state`:
  `phase=booting`, `worker_alive=false`, `tmux_alive=true`, `last_ping=12:28:17Z` (30+ min stalled at time of
  confirmation). Added a fresh `[OPERATOR]` kill+respawn todo above (the prior two are already checked off from earlier
  instances). This recurrence is itself the strongest evidence yet that the `[BACKEND]` durable watchdog-escalation fix
  is still needed — the operator-side kill+respawn is a point-fix, not a cure, and the class keeps coming back on the
  same slot.
- **2026-08-04 ~04:00Z (main agt-1756f6)** — added slot 3 as a 2nd instance of the wedged-slot class (review #3662).
  Same dead-worker-live-pane signature (`worker_alive=false`/`tmux_alive=true`), watchdog kicking with
  `ping_advanced=false` and never escalating to respawn — corroborates the [BACKEND] watchdog-escalation todo above (now
  two independent instances, slot 2 + slot 3). Slot 3 also carries a stale MTDS drift-violation (ahead=1/behind=5) + is
  gated on RB-e7d79260; verified ce7d7d1e2 is a real orphan but WOULD-REGRESS so it must NOT be applied. Main did not
  touch slot 3's worktree (not mine + drift-violating). Kill+respawn stays operator-owned.

- **2026-08-04 ~02:47Z (main agt-1756f6)**: Filed after review #3653 handed the slot-2 decision to main. Main took the
  within-authority path first (concrete `/api/slots/2/message` nudge, since main cannot kill slots) — it did not clear
  the wedge (still `pre_boot` two ticks later), which is itself the useful signal that this is dispatch-side, not
  worker-idle. Remaining lever (kill+respawn) is backend/operator-owned → the two todos above. Not on-fire (11-12 other
  slots healthy, no WIP at risk); P2. Main will keep watching slot 2 and will close this if AutoSpawn/watchdog or the
  operator clears it.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — brand-new doc; 2 of 3 open todos are explicitly `[OPERATOR]`-
  tagged live-infra actions (kill+respawn) that main cannot perform, and the 3rd (`[BACKEND]` watchdog-escalation fix)
  is live dispatch-critical-path machinery — the exact mechanism that routes tasks to every AO worker — not a
  worker-determinable bounded fix to dispatch through the same fleet it would be modifying.
- **context-scout 2026-08-06**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged): todos 1/3 are
  [OPERATOR]-tagged kill+respawn/judgment actions main cannot self-serve; todo 2 touches live dispatch-critical watchdog
  machinery already under active sequenced modification elsewhere (batch5).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-06 (unchanged): the
  2 remaining open todos are an `[OPERATOR]`-tagged live kill+respawn action (slot 3, 3rd recurrence) and a `[BACKEND]`
  fix to live dispatch-critical-path watchdog machinery -- neither is a worker-determinable bounded fix safely
  dispatchable through the same fleet it would be modifying.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of both open
  items. The `[BACKEND]` durable watchdog-escalation fix touches core dispatch-critical-path machinery (same caution
  class as the sibling context-pct-75 wedge doc). The `[OPERATOR]` slot-3 kill+respawn item is an explicit operator-only
  live-infra action main/workers cannot self-serve. 3 prior audits (08-04, 08-06, round7-08-08) consistently agree.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:24ee848d2e464ac1]: KEEP-NA — the [BACKEND] durable-fix item is claimed by `ao_satellite_ao_dispatch_batch22_2026_08_16.md` (its todo 5 cites this doc by path); leave open, do not duplicate. **CORRECTED 2026-08-19 (`/plan-reconcile agent_operating_framework_master`)**: that doc's own frontmatter is `status: draft`, not active — `rg -n '^status:' plans/active/ao_satellite_ao_dispatch_batch22_2026_08_16.md` confirms `status: draft`, meaning the durable-fix work has never actually been dispatched to a worker despite the correspondence being real. Do not treat this item as covered until `ao_satellite_ao_dispatch_batch22_2026_08_16.md` is flipped `active`. The [OPERATOR] slot-3-recurrence item stays KEEP-NA (operator-only live-infra action; a 2026-08-16 staleness note is a suspicion, not hard evidence of closure).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).

## Related phase-derivation defect found 2026-08-19 (fold-in, operator-directed)

While diagnosing why the fleet showed scheduled-job slots stuck displaying `BOOTING`, a second,
narrower defect turned up in the same `compute_slot_phase` machinery this doc covers.

The primary bug is fixed and shipped (`agent-orchestrator@0391039be0`): a typed one-shot agent
(`spawn_base_role` set — the `plan_health`/escalation family) never POSTs `/boot` and never gets a
`current_task`, so neither signal that retires `phase=booting` could fire and the phase read
`booting` for the agent's entire run. Measured live: slot 29 (`docs_reconciler`, `agt-6551b7`,
`status=active`) read `booting` for 35+ min at 43% context while genuinely working; slot 28's
`cefi_reconciliation_auditor` (`agt-419a6c`) read `booting` across a run that exited
`lifecycle-complete`.

The residual defect is a producer/consumer disagreement about the SCOPE of that phase split.
`server/fleet_slot_status.py` tests `phase == "pre_boot"` / `phase == "booting"` FIRST, before any
status branch, so a `working` slot with a boot-phase reads as `booting` in the persisted
`fleet_slot_snapshots` KPI history. `dashboard/src/layout.tsx`'s `summarise()` gates the identical
split on `s.status === "idle"` (and `layout.test.ts` asserts `bootingCount === 0` for a
`working`+`booting` slot). `fleet_slot_status.py`'s own docstring claims the two "can never
silently drift" — they can, and do. `server/models/slots.py`'s field comment sides with the
dashboard ("phase is only meaningful while status is idle").

- [ ] [BACKEND] P3. Reconcile the phase-split scope between `server/fleet_slot_status.py` and
      `dashboard/src/layout.tsx` so the persisted fleet-KPI snapshot and the live dashboard
      genuinely share one definition, as `fleet_slot_status.py`'s docstring already promises.
      Note this changes a KPI's historical counting semantics, so state which side wins and why in
      the commit — do not silently pick one. Rarer since `agent-orchestrator@0391039be0` (a typed
      one-shot no longer produces `working`+`booting`), but still reachable inside the boot window.
      (repo: agent-orchestrator)
