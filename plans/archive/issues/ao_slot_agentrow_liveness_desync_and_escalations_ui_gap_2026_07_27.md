---
doc_type: issue
title:
  AO's SlotRow-only liveness computation silently misreported the persistent main/review agents as dead/stale; CI
  escalations had no dashboard surface at all
summary: >-
  Operator asked why CPU looked idle with 15 slots, then asked for a review of the main + review agents and CI
  escalations. Live investigation (AWS SSM into the planning VM's /api/state, /api/agents, /api/escalations/active, plus
  reading agent-orchestrator's server code) found three things. (1) `_slot_to_view()` (server/routes/state.py) computed
  `worker_alive`/`last_ping`/`last_msg` purely from `SlotRow`, but the mandatory main (slot 0) and review (slot 1 on
  this VM) agents heartbeat via a completely separate `AgentRow` (register_agent / touch_main_agent_heartbeat / the
  review agent's own /poll) — they never go through the normal task-worker /heartbeat|/progress|/done lifecycle that
  keeps a regular SlotRow current. Result: slot 0's SlotRow was frozen at a 2026-07-06 last_ping (paused status,
  21-day-old last_msg) while the real main agent (`agt-4d8de7`) was alive and actively working (last_ping essentially
  real-time, "idle, watching ops + blocked-queue", 575/637 historical blocked-queue questions answered). Any consumer of
  `/api/state` (this investigation included) would misdiagnose main/review as dead. (2) `/api/escalations/active`
  existed on the backend (server/routes/agents.py) but had zero consumers anywhere in `dashboard/src` — CI-failure and
  scheduled-dispatch escalations were only visible via direct API/SSM access, never in the AO dashboard UI. (3)
  Separately verified as NOT bugs: the review agent's apparent "hasn't reviewed in a while" read was a stale snapshot —
  its tmux log showed sweeps at 18:19 (4 shas) and 18:34 (6 shas), exactly on its configured 900s cadence; slot 16's
  `worker_alive: False` reading was the same SlotRow-staleness artifact as (1), not a real stuck slot — its live log
  showed active, correct work seconds before the check; and the VM's CPU load (uptime 7.8-9.0, vmstat run-queue bursts
  to 21 on 16 vCPUs) supports keeping the current 16-core sizing, not reverting to 8-10.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, observability, liveness, escalations, ci, bug]
related: []
created: 2026-07-27
priority: P2
parent_epic: orchestrator_master
source:
  "operator interactive session, slot 3 — asked why CPU was idle with 15 slots, to review the orchestrator/review agent
  and CI escalations before deciding whether to spawn 10 more workers"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
  slot-3 (interactive), agent-orchestrator@b94e585, @6f81da4 (escalation-card liveness join), @e901151 (real
  resolved/unresolved verdict)
locked_by:
---

> **🟢 RESOLVED 2026-07-27, extended 2026-07-28** — fixed `_slot_to_view` to compute main/review liveness from
> `AgentRow`, not just `SlotRow` (`agent-orchestrator@b94e585`); shipped the Escalations panel (same commit); joined
> escalation cards against the live agent registry to stop showing finished one-shot workers as still-dispatched
> (`@6f81da4`); then gave the escalation queue a REAL resolved/unresolved/abandoned verdict end-to-end, superseding the
> agent-liveness proxy (`@e901151`, see § Update 2026-07-28 below).

# AO slot liveness desync (SlotRow vs AgentRow) + missing escalations UI

## What I found

### 1. `_slot_to_view` misreported main/review liveness (real bug, fixed)

`server/routes/state.py::_slot_to_view` computed the `worker_alive` flag (and the `last_ping`/`last_msg` fields shown to
any caller of `/api/state`) purely from the slot's own `SlotRow.last_ping`/`last_msg`. Main (slot 0) and review
(`ORCHESTRATOR_REVIEW_SLOTS`, slot 1 on the planning VM) are the two MANDATORY persistent agents
(`server/main_agent_keeper.py`), but they heartbeat through a structurally different path — `AgentRow`
(`register_agent`, `touch_main_agent_heartbeat`, the review agent's own `/poll`) — never through the regular task-worker
`/heartbeat|/progress|/done` calls that keep a normal `SlotRow` current. Their `SlotRow` rows therefore freeze at
whatever they were before the slot became a persistent main/review host and never update again.

Observed live: slot 0's `SlotRow` read `status=paused`, `last_ping=2026-07-06T07:55:21Z` (21 days stale), `last_msg` =
an old one-off task's completion message — computed `worker_alive=False`. The real main agent (`agt-4d8de7`, via
`/api/agents`) was alive the entire time: `last_ping` essentially real-time,
`last_msg="idle, watching ops + blocked-queue"`, and had answered 575 of 637 historical blocked-queue questions. Same
pattern on slot 1 (review) and, transiently, on slot 16 while it held a one-shot cicd escalation agent.

**Fix** (`server/routes/state.py`, `agent-orchestrator@b94e585`): for `kind in ("main", "review")`, `_slot_to_view` now
looks up the live `AgentRow` bound to the slot's tmux session (`state_store.find_active_agent_for_session`) and overlays
its `last_ping`/`last_msg` before computing `worker_alive`. Regular worker slots are unaffected
(`find_active_agent_for_session` returns `None` for them — autospawned task workers have no bound `AgentRow`). Verified:
existing slot-view test suite (16 tests) green, `basedpyright`/`ruff` clean, full repo `quality-gates.sh` green, shipped
via quickmerge to `live-defi-rollout`.

### 2. CI escalations had no dashboard surface (gap, fixed)

`GET /api/escalations/active` (`server/escalation.py::list_active_escalations`) has existed as a read signal (originally
for the deployment-ui Repos-CI board), but `dashboard/src` had zero consumers of it — no fetch, no panel, no tab. The
only "escalation"-adjacent thing in the AO dashboard was an unrelated `escalation_to` column in the static Roles
registry table. Operationally, the only way to see an active CI escalation was direct API access (or SSM into the VM),
never the dashboard the operator actually looks at.

**Fix**: added `EscalationView` (`dashboard/src/types.ts`), `api.escalations()` (`dashboard/src/api.ts`), and an
`EscalationsPanel` component (`dashboard/src/layout.tsx`, mirrors `BlockedPanel`'s card layout — repo#PR, wall_type,
queued/dispatched state, relative age) wired into the existing dashboard page's rail (both the desktop layout's two
branches and `MobileTriage`'s alerts tab) — no new route/page, per operator instruction to keep the same page. Verified:
`tsc --noEmit` clean, full `vitest` suite (154 tests) green, `prettier --check` clean, full repo `quality-gates.sh`
green.

### 3. Checked and NOT bugs

- **Review agent cadence**: appeared to not have reviewed "in a while" from a single snapshot read. Its raw tmux log
  showed sweeps completing at 18:19 ("4 new slot_done shas reviewed ok") and 18:34 ("6 new slot_done shas reviewed ok"),
  15 minutes apart — exactly its configured `ORCHESTRATOR_REVIEW_LOOP_SECONDS=900` cadence. Also independently
  cross-checking anomalies each sweep (e.g., diagnosed slot 11/15 git dirty/ahead state via `/api/fleet/git-health` +
  `/api/state`, concluded correctly "alive+working, nothing to escalate"). Not behind.
- **Slot 16 `worker_alive: False`**: same SlotRow-staleness pattern as finding 1, not a stuck slot — it was
  transitioning between two one-shot escalation agents (`agt-7ee36f` PR#1685, finished; `agt-450bba` PR#1686, picked up
  next). Its live tmux log showed real, current commit/push work seconds before the check.
- **CPU sizing (8 vs 16 cores)**: `uptime` showed load average 7.79-9.02 (1/5/15-min) on 16 vCPUs; `vmstat 1 5` showed
  the run-queue (`r`) column at 6-21 (momentarily exceeding the 16 available cores) with 34-51% user CPU; zero D-state
  (disk-wait) processes. This is real, if moderate, CPU contention from 15 concurrent Claude Code worker sessions
  running subprocess-heavy work (git, QG runs, hygiene sweeps), not just idle API-wait — a single `top -bn1` snapshot
  earlier in the session undercounted it. Recommendation: keep the current 16-core sizing; reverting to 8-10 cores would
  likely push load average over the core count during the same bursty moments that motivated the original 8→16 upgrade.
  No VM resize was performed — this is a reported recommendation only pending operator confirmation, since resizing this
  VM requires stopping it (live main-agent supervision + 15 active workers + escalation dispatch all in flight).

## Evidence

- `agent-orchestrator@b94e585` — commit landing both fixes, pushed to `live-defi-rollout` via quickmerge
  (`--agent --files 'server/routes/state.py dashboard/src/App.tsx dashboard/src/api.ts dashboard/src/layout.tsx dashboard/src/types.ts'`).
- Full repo `bash scripts/quality-gates.sh`: server (ruff lint + format, basedpyright, pytest) and dashboard (tsc,
  vitest) both green — `✅ agent-orchestrator quality gate PASSED`.
- Live VM checks (AWS SSM, `i-0c9b283b31d6b5ca7`, read-only): `/api/state`, `/api/agents`, `/api/escalations/active`,
  `/api/fleet/summary`, `/api/repo-blockers`, `/api/blocked/stats`, `uptime`, `vmstat 1 5`, `ps -eo stat`, review
  agent's raw tmux log (`/api/slots/1/log`), slot 16's raw tmux log (`/api/slots/16/log`).

## Follow-ups

None open — both findings were fixed in the same session. No further action needed unless the operator wants the
CPU-core recommendation acted on (resize) or wants the same fix pattern audited for other AO backend surfaces that might
read `SlotRow` for a main/review slot (not checked beyond `_slot_to_view`, which is the only place `/api/state`'s
`worker_alive` is computed).

## Update 2026-07-28 — real terminal verdict, not just a liveness proxy

Operator reported the shipped Escalations panel showed "dispatched to slot 10" for a card while the Fleet table already
showed slot 10 on an unrelated task — a live contradiction. Root cause: `list_active_escalations()` keeps a `dispatched`
row "active" for up to 2h post-dispatch regardless of whether the one-shot worker already finished (documented as
intentional — "escalation workers are one-shot with no completion callback"). Fixed (`agent-orchestrator@6f81da4`) by
joining each dispatched card against the live `/api/agents` registry (`agent_id == escalation_id` by construction,
`server/escalation.py`'s own 1:1 join) so the card reads "working — slot N" only while genuinely live, else "slot N
freed — worker no longer active."

That fix was flagged to the operator as a **workaround, not the real fix** — process-liveness can't distinguish success
from failure. Operator asked for the real fix under `/autonomous`. Investigation found the real mechanism **already
existed and was already running**, just never exposed via the API:

- `EscalationQueueRow` (`server/orm.py`) already has `resolved_at`/`resolution`/`reescalations` columns, with a
  documented lifecycle `queued → dispatched → resolved | unresolved | abandoned`.
- `verify_dispatched_escalations()` (`server/escalation.py`) — called every AutoSpawnLoop tick — polls each dispatched
  wall's REAL terminal signal (PR merged/closed, or the repo's `quality-gates-v2` going green) via
  `_poll_wall_resolution`, and writes a genuine verdict via `_mark_resolved` (`resolution` e.g. `"qg_v2_green"` /
  `"pr_merged"`) or `_mark_unresolved_and_maybe_reescalate` (`"still_red_past_deadline"`, capped re-escalation), each
  with Slack bookends. This is materially better than a worker-liveness proxy — it answers "did the CI failure actually
  get fixed," not "is the process still running."
- The only real gap: `list_active_escalations()` (backing `GET /api/escalations/active`, the dashboard's only read path)
  filtered to `queued`/`dispatched-within-2h` only and never returned `resolved_at`/`resolution`, or any terminal-status
  row at all — so this whole working mechanism was invisible to any dashboard consumer. My earlier characterization to
  the operator ("no completion callback... would need a bigger backend change") was **wrong on the backend half** — the
  backend piece already existed; only the API surface + UI were missing.

**Fix** (`agent-orchestrator@e901151`):

- `list_active_escalations()` gains an opt-in `include_resolved_within_hours` param that additionally returns
  recently-terminal rows with their real `resolved_at`/`resolution`, **without changing the default (no-arg) contract**
  deployment-ui's Repos-CI board depends on — verified via a dedicated test
  (`test_list_active_escalations_default_excludes_terminal_rows`).
- `GET /api/escalations/active` exposes it as `?include_resolved_within_hours=` (FastAPI `Query`, default `None`).
- 4 new tests in `tests/test_escalation.py` (there was zero prior coverage of `list_active_escalations`): default
  excludes terminal rows, opt-in includes them with real verdicts, the recency window is respected (an old resolved row
  stays excluded even when opted in), and a still-open dispatched row reports `resolved_at`/`resolution` as `null`
  rather than omitting the keys.
- Dashboard: `EscalationView.status` extended to `resolved | unresolved | abandoned`; `api.escalations()` requests a 2h
  window; `EscalationsPanel` now renders a real resolved (green, `var(--status-working)`) / unresolved (red,
  `var(--status-stale)`) / abandoned (muted, `var(--status-idle)`) verdict + its timestamp, and distinguishes
  "dispatched, worker finished, verdict pending" (still no live agent, but no terminal status yet — the watchdog hasn't
  polled it since the worker exited) from a row still genuinely in-flight.

**Evidence**: `agent-orchestrator@e901151`; full repo `quality-gates.sh` green (1813 server tests + 154 dashboard tests,
`basedpyright`/`ruff`/`tsc`/`prettier` all clean); shipped via quickmerge to `live-defi-rollout`.

**Follow-ups**: none open. Not checked (future audit candidate if the operator wants it): whether every non-dashboard
consumer of `/api/escalations/active` (deployment-ui) would actually benefit from the same terminal-verdict surface, or
whether it's deliberately scoped to only the pending/in-progress signal it already uses.
