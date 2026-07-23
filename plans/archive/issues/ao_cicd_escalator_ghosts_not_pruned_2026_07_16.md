---
doc_type: issue
title:
  Dead cicd escalator agents linger "active" for up to 6h — the TmuxPruner nulls their session chip before the reaper's
  instant-reap can fire, so they pile up in the fleet view
summary: |
  The FleetView showed ~13 `cicd` 1-SHOT escalator agents all status=ACTIVE with an EMPTY tmux column and last
  heartbeats 5m–4h old, while only ONE was genuinely live. Root cause: the TmuxPruner clears a dead agent's
  `tmux_session` field (so the UI chip does not lie) but leaves `status="active"`. That strips `reap_orphan_agents` of
  its TWO fast archival signals — dead-session and session-reused — because BOTH are gated on `tmux_session` being
  non-null, which the pruner just nulled. The record then falls through to the reaper's LAST branch, the 6h
  `stale_grace` fallback that exists for PERSISTENT cloud agents (review) with no tmux — directly contradicting the
  stated design intent ("tmux-backed agents are reaped the instant their session dies", main_agent_keeper.py). cicd is
  also deliberately absent from `_SINGLETON_AGENT_KINDS`, so the sessionless-singleton fast-reap never covers it either.
  Net: a finished one-shot escalator (which never calls `/done`, so cleanup depends entirely on the reaper/pruner)
  lingers "active" up to 6h; with frequent CI walls, ~6h of accumulation is the dozen-plus ghosts the operator saw.
  FIXED IN TWO PARTS. (1) `a21ccba` — the TmuxPruner now archives one_shot/scheduled agents
  (exit_reason=`lifecycle-complete`) in the same pass it clears the dead chip, mirroring the reaper so whichever daemon
  observes the death first agrees. (2) `a22c0d7` — REOPENED when the operator saw ghosts STILL listed after (1) was
  live: the pruner's query filters on `tmux_session IS NOT NULL`, so it can never retire a row that is ALREADY
  sessionless, which all 11 measured ghosts were. The sessionless case had NO fast path at all. The reaper now splits
  its grace in two — terminal-lifecycle (one_shot/scheduled) sessionless agents reap on
  `one_shot_stale_grace_minutes` (default 15), persistent cloud agents keep the 6h — making the outcome
  order-independent regardless of which daemon wins or how the row reached the sessionless state. VERIFIED LIVE
  2026-07-16 16:03 UTC: sessionless ghost count 11 -> 0 on the central VM, 13 rows archived `lifecycle-complete`, with
  no hand DB edit.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, reaper, tmux-pruner, agent-lifecycle, one-shot, cicd-escalator, fleet-view, dashboard]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-17
parent_epic: orchestrator_master
priority: P1
assigned_vm: NA
execution_scope: local-only
resolved_by:
  - "agent-orchestrator@a21ccba — TmuxPruner archives terminal-lifecycle agents on session death + regression test"
  - "agent-orchestrator@a22c0d7 — reaper reaps SESSIONLESS one_shot/scheduled on a short grace (the 11 measured ghosts
    a21ccba could not reach); 7 tests incl. live-review + mid-task guards"
locked_by:
locked_since:
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
source:
  - "Operator FleetView screenshot 2026-07-16 — ~13 cicd 1-SHOT agents ACTIVE, tmux column empty, only one live"
  - "Static read of server/tmux_pruner.py + server/state_store/agents.py::reap_orphan_agents on live-defi-rollout"
---

# Dead cicd escalator agents are not pruned — they linger "active" for up to 6h

> **📦 ARCHIVED 2026-07-17 (operator session) — resolution INDEPENDENTLY RE-VERIFIED live ~24h on before archival**: the
> doc's own runtime-verdict query re-run via read-only SSM at ~15:45 UTC returned **`sessionless_terminal_ghosts=0`**
> (held since the 16:03 UTC drain), and both fix commits (`a21ccba`, `a22c0d7`) verified as ancestors of
> `origin/live-defi-rollout`. The one open P3 (docstring reword) closed at archival time — `ao@6a30e45`, full QG green.
> Zero open todos remain.

> **✅ RESOLVED 2026-07-16 — in TWO parts (`a21ccba` + `a22c0d7`), the second VERIFIED LIVE at 16:03:20 UTC: sessionless
> ghost count on the central VM went `11 → 0`, 13 rows archived `lifecycle-complete`, no hand DB edit.** `a21ccba` alone
> was necessary but NOT sufficient — it was reopened when the operator saw the ghosts still listed while it was already
> live and running.
>
> **Part 1 — `agent-orchestrator@a21ccba`** (verified correct, deployed, live): the TmuxPruner archives
> one_shot/scheduled agents on session death, so a finished cicd escalator is reaped within one prune tick (~60s) of its
> session dying instead of waiting out the 6h `stale_grace`. Independently re-verified 2026-07-16: 56 tests green, and
> bug-injection confirms the 2 positive cases FAIL when the archival is removed (the tests are load-bearing).
>
> **Part 2 — `agent-orchestrator@a22c0d7`**: the operator observed ghosts STILL listed 6 minutes after Part 1 went live.
> That was **not** Part 1 failing — it was Part 1 being unable to reach them. See § "Why a21ccba could not retire the
> existing ghosts" below. This part gives the sessionless case its own short grace.
>
> **Correction to this doc's original claim.** It stated existing ghosts "drain naturally… the next prune tick after
> each ghost's session is confirmed dead now archives it." That is **false** for an already-sessionless row: the pruner
> selects on `tmux_session IS NOT NULL`, so it never looks at one again. Those rows drained only on the 6h `stale_grace`
> — up to 5 more hours of the exact pile-up the fix was written to stop.

## Symptom (operator FleetView, 2026-07-16)

| Observation                        | Value                                                                         |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| `cicd` `1-SHOT` rows shown         | ~13, **all status=ACTIVE**                                                    |
| Their `TMUX` column                | **empty (`—`)** for all but the single freshest — i.e. `tmux_session` is NULL |
| Their `LAST HEARTBEAT`             | `5m ago` → `4h ago` (spread across hours; none recent)                        |
| Genuinely live agents              | only `orchestrator` (main) + `review` + the one cicd on `orch-slot-2`         |
| `CONTEXT` column for the dead cicd | `0%` — no live session behind them                                            |

The rows are dead one-shot workers that finished minutes-to-hours ago, yet the dashboard still lists them as ACTIVE.

## Root cause — a pruner/reaper handoff gap

A cicd escalation worker is registered by `escalation.escalate()` with `lifecycle="one_shot"`, `agent_kind="cicd"`, and
`tmux_session="orch-slot-N"` (server/escalation.py, `_register_agent(...)`). It resolves its CI wall, pushes the fix,
pings the authoring slot, and **exits — it never calls `/done`** (the `/done` reap in routes/slots_worker.py is for
backlog task workers; escalators grab a free slot via `_pick_free_slot` and bypass it). So the ONLY thing that can
retire its record is the reaper (`reap_orphan_agents`) or the TmuxPruner.

Two independent daemon threads, both on a ~60s cadence, race to observe the dead session:

1. **`reap_orphan_agents`** (called first thing in every `MainAgentKeeper.tick_once`) has three archival signals for a
   one_shot agent:
   - **dead-session** — `if a.tmux_session and not is_session_live(a.tmux_session): archive("lifecycle-complete")`
   - **session-reused** — `tmux_session` live but re-created after the agent last acted → archive
   - **stale-no-session fallback** — `a.tmux_session is None and now - recency(a) > stale_grace` → archive The first two
     — the FAST ones — are **both gated on `a.tmux_session` being non-null.**

2. **`TmuxPruner.prune_once()`** iterates every `AgentRow` with a `tmux_session` and, when the session is dead, sets
   **`agent.tmux_session = None`** and logs `tmux_session_lost` — **but leaves `status="active"`.**

**When the pruner wins the race (it usually does — nulling dead session fields is its whole job), it destroys the
reaper's fast-path signal.** The reaper can no longer use dead-session or session-reused (both need the now-null field),
so the record falls to the **6h `stale_grace` fallback** — a grace explicitly designed for PERSISTENT cloud agents
(review) that legitimately have no tmux session and self-ping for days. A finished one-shot worker is the opposite case.

This directly contradicts the code's own stated intent (`server/main_agent_keeper.py`):

> "A cloud agent (no tmux session — e.g. review) silent longer than the configured grace … is reaped from the dashboard.
> **tmux-backed agents are reaped the instant their session dies.**"

They are not — once the pruner nulls the field, a tmux-backed one-shot agent is reaped on the SAME 6h clock as a cloud
agent.

### Why cicd is hit hardest

`cicd` is **deliberately excluded** from `_SINGLETON_AGENT_KINDS` (`= {review, plan_health, plan_reconciler}`) because
parallel escalators are legitimately multi-instance. That exclusion means the `_sessionless_singleton_duplicates`
fast-reap — which DOES catch a session-nulled straggler for review/plan_health — never applies to cicd. So for a
session-nulled cicd ghost the 6h `stale_grace` fallback is the **only** remaining reap path.

The existing unit test `test_multi_instance_cicd_not_deduped_as_singleton` even encodes the buggy end-state as if
intended: _"a fresh sessionless one stays active via the stale_grace fallback."_ That "stays active" for a dead one-shot
worker is exactly the pile-up.

### Severity nuance (honest scope)

This is a **lingering / pile-up bug, not an unbounded leak** — the ghosts DO get archived once they cross the 6h
`stale_grace` (their `last_ping` freezes at the worker's final `/progress` heartbeat). But CI walls fire often, so ~6h
of accumulation is the dozen-plus rows observed. The retention prune (`prune_finished_agents`) then bounds the archived
roster; the leak was in the ACTIVE roster, which is what the operator sees.

## The fix (`agent-orchestrator@a21ccba`)

`TmuxPruner.prune_once()` — in the agent loop, when a dead session is detected, if the agent's `lifecycle` is `one_shot`
or `scheduled` (the reaper's own `_expected_end` set), **archive the record in the same transaction**
(`archive_agent(..., exit_reason="lifecycle-complete")`) instead of only nulling the chip. Now whichever daemon — pruner
or reaper — observes the death first agrees on the outcome, and the intent "tmux-backed agents are reaped the instant
their session dies" holds regardless of ordering.

- **Persistent agents (main/review) are unchanged** — the pruner still only nulls their chip; the reaper's singleton /
  stale_grace logic governs their respawn (a persistent session dying is not an expected end).
- **Provably correct, no false positives** — the pruner acts only on an agent that HAD a live-then-dead session
  (`has_session(name) == False` for a session it owned), not on the sessionless-from-birth case; and a rare transient
  `has_session` miss self-heals via `update_agent_ping`'s restore-on-ping if the agent is in fact alive.
- Chosen over a reaper-side change (reap sessionless one_shot agents promptly) because that would falsely reap a
  one_shot craft worker that momentarily registers without a session while booting, and would contradict the reaper's
  isolated multi-instance-cicd contract.

## Why `a21ccba` could not retire the existing ghosts (the reopen, 2026-07-16)

Operator, ~6 min after Part 1 went live: _"the ci agents are still not pruned… the backend should be able to detect them
and remove them… we shouldn't have to change the db by hand. it should be done by backend so that it doesn't recur."_

**Measured on the central VM (`i-0c9b283b31d6b5ca7`, live DB, 15:51 UTC)** — not inferred:

| Fact                                                     | Value                                                   |
| -------------------------------------------------------- | ------------------------------------------------------- |
| `active`/`stale` agent rows total                        | 14                                                      |
| of those, `cicd` `one_shot` with **`tmux_session=NULL`** | **11**                                                  |
| their ages (last_ping → now)                             | **0.98h – 4.95h** — every one INSIDE the 6h grace       |
| genuinely live rows                                      | 3 (orchestrator 0.01h, review 0.03h, plan_health 0.05h) |
| VM clone HEAD / behind origin                            | `a21ccba` / **0** — Part 1 WAS deployed and running     |
| `orchestrator.service` last start                        | 15:45:15 UTC (6.5 min before the measurement)           |

The decisive detail: **all 11 ghosts were already `tmux_session=NULL`.** The pruner's loop selects
`AgentRow.tmux_session.is_not(None)` and acts inside `if name and not has_session(name)`. A row that is already
sessionless is never selected, so Part 1 — correct as it is — was structurally incapable of retiring a single one of
them. They were on the 6h `stale_grace`, and would have kept showing "active" for up to ~5 more hours.

The general hole Part 1 left open: **a sessionless terminal-lifecycle agent had no fast reap path at all.** The pruner
needs a non-null session; the reaper's two fast signals need a non-null session; `cicd` is excluded from
`_SINGLETON_AGENT_KINDS` so the sessionless-singleton fast-reap skips it. Anything that nulls the field before archival
(a pre-`a21ccba` prune, `routes/agents.py`, or `update_agent_ping`'s restore-on-ping resurrecting an archived worker)
drops the record onto a 6h grace designed for a persistent cloud agent. Part 1 closed the RACE; it did not close the
CLASS.

## The fix, part 2 (`agent-orchestrator@a22c0d7`) — split the grace

`reap_orphan_agents` now takes `terminal_stale_grace` alongside `stale_grace`, and the sessionless branch picks by
lifecycle:

```python
elif now - _recency(a) > (terminal_stale_grace if _expected_end else stale_grace):
```

- New knob `one_shot_stale_grace_minutes` (default **15**, env `ORCHESTRATOR_ONE_SHOT_STALE_GRACE_MINUTES`). For a
  one_shot worker, sessionless+silent IS the end of its life; the 6h benefit-of-the-doubt belongs to a `review` agent
  that self-pings for days.
- **Order-independent** — whichever daemon observes the death first, and however the row became sessionless, it retires
  within ~15 min. That is the "doesn't recur" the operator asked for, and it drains the existing 11 with **no hand DB
  edit**.
- The reaper keeps its injected-grace seam (`state_store/agents.py` imports no config) — the keeper passes
  `_one_shot_stale_grace()`.

**Why this is safe** (the branch is narrower than it looks): it can only fire on `tmux_session IS NULL`. A live
escalator holds a session and takes the dead-session / session-reused branches instead, and pings while it works, so its
recency never crosses the grace. `lifecycle=None` keeps the conservative 6h. A false reap self-heals via restore-on-ping
(`agents.py`), and `archive_agent` touches the RECORD only — it never kills a session or releases a task. Blast radius
checked: only `health.py:300` reads the archived state, and `prune_finished_agents` retains 7 days.

**This is the reaper-side change the original doc rejected** ("would falsely reap a one*shot craft worker that
momentarily registers without a session while booting"). That objection holds against an \_immediate* reap; it does not
hold against a _15-minute_ one — a boot window is seconds, and restore-on-ping covers the residual.

## Verification

**Part 2 (`a22c0d7`)** — `bash scripts/quality-gates.sh --no-fix` → **exit 0** (ruff + `basedpyright 0 errors` +
`1340 passed, 1 skipped` + dashboard tsc/vitest 90). 7 new tests in `tests/test_reap_orphan_agents.py`. Proven by **bug
injection**: reverting the branch to the single grace fails exactly the 2 positive tests while the 5 guards stay green.
Guards pinned: a sessionless `review` silent 1h is NOT reaped (else the fix would kill the live review agent every 15
min); a one_shot that pinged 5 min ago is NOT reaped; a live one_shot holding its session is untouched even at 5h;
`lifecycle=None` keeps the 6h. One test pins the regression directly — the youngest measured ghost (0.98h) survives
under the old semantics and dies under the new.

**Part 1 (`a21ccba`)** — independently re-verified, not taken on report:

- `bash scripts/quality-gates.sh` → **PASSED** (ruff + basedpyright + `1333 passed, 1 skipped` + dashboard tsc/vitest).
- New `tests/test_tmux_pruner_agent_reap.py` (4 cases): dead-session cicd → archived `lifecycle-complete`; dead-session
  scheduled (plan_health) → archived; dead-session persistent (review) → chip nulled but stays active; live-session
  one_shot → untouched.
- `tests/test_reap_orphan_agents.py` (52 cases) unchanged and green — the reaper's contracts are untouched.

## Todos

- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@a21ccba`.** TmuxPruner archives one_shot/scheduled agents
      on session death; regression test added; full AO quality gate green. Independently re-verified 2026-07-16 (56
      tests green + bug-injection proves the tests are load-bearing) — correct, but see P0 below: necessary, not
      sufficient.
- [x] [BACKEND] P0. ✅ **DONE 2026-07-16 — `agent-orchestrator@a22c0d7`.** REOPEN: ghosts still listed 6 min after
      `a21ccba` went live. Measured the live DB — 11 sessionless one_shot rows, 0.98h-4.95h, all inside the 6h grace;
      `a21ccba` cannot reach a row whose `tmux_session` is already NULL. Split the reaper's grace so terminal-lifecycle
      sessionless agents reap on `one_shot_stale_grace_minutes` (default 15) while persistent agents keep 6h. QG exit 0
      (1340 passed, basedpyright 0 errors); bug-injection verified.
- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 16:03:20 UTC — MEASURED on the central VM, not inferred.** Runtime verdict for
      `a22c0d7`: `sha=a22c0d7 deployed=yes ghosts=0 drained_30m=13`. The sessionless one_shot/scheduled count went **11
      → 0**, and 13 rows carry `exit_reason='lifecycle-complete'` within the 30 min window (the 11 ghosts + 2 that
      finished normally). Deploy needed no human step: the `slot-cron-ff-pull` (5-min cadence) pulled LDR and the
      service's `--reload --reload-dir server` restarted uvicorn on its own — the same path that carried `a21ccba`.
      **The backend drained them; no row was touched by hand.**
- [x] [BACKEND] P3. ✅ **DONE 2026-07-17 — `agent-orchestrator@6a30e45` (quickmerge, full AO QG green).** Docstring now
      states the post-`a22c0d7` semantics: the 6-min-old sessionless cicd survives the tick only because it is inside
      the 15-min `one_shot_stale_grace_minutes` terminal grace — past it, reaped `lifecycle-complete`, never via the 6h
      persistent `stale_grace` it used to ride. The PRIMARY `not superseded-cicd` assertion untouched. **Gate MET**:
      reword shipped; test file green (59 passed) inside the full QG. ~~**Optional cleanup — retire the misleading
      "stays active" assertion**~~ in `test_multi_instance_cicd_not_deduped_as_singleton`.

## Progress Log

- **2026-07-16** — Operator flagged the FleetView pile-up ("many cicd escalators registered, only one live, why aren't
  the dead ones pruned"). Traced through `escalation.escalate` (registration) → `reap_orphan_agents` (three archival
  signals, two gated on non-null `tmux_session`) → `TmuxPruner.prune_once` (nulls the field, leaves status active) →
  `_SINGLETON_AGENT_KINDS` (cicd excluded). Root cause: the pruner nulling the field before the reaper's instant-reap
  fires, dropping the record onto the 6h cloud-agent `stale_grace`. Fixed in the pruner (archive terminal-lifecycle
  agents on session death); regression test added; full AO quality gate green.
- **2026-07-16 (later)** — **REOPENED.** Operator: _"the ci agents are still not pruned… it should be done by backend so
  that it doesn't recur."_ Verified `a21ccba` on the VM first (`HEAD=a21ccba`, behind=0, clean, service up 15:45:15 UTC)
  — it WAS live, so the ghosts were not a deploy gap. Measured the live DB: 11 sessionless one_shot rows, 0.98h-4.95h.
  Diagnosis: the pruner's `tmux_session IS NOT NULL` filter makes an already-sessionless row unreachable, and the
  sessionless terminal-lifecycle case had no fast path anywhere. Shipped `a22c0d7` (split grace). Two process notes
  worth keeping: (1) a first SSM probe reported `NO-NOT-DEPLOYED` — a **false verdict** caused by git aborting on
  `dubious ownership` under root, with the `else` branch firing on the failure rather than on an answer; re-run under
  `sudo -u ubuntu` gave the true `YES-DEPLOYED`. Probes must distinguish "the check failed" from "the answer is no". (2)
  The QG's own exit code (`0`) is the verdict, never `tail`'s — the first run showed a green vitest tail while the gate
  had exited 1 on RUF002.
- **2026-07-16 16:03:20 UTC — RUNTIME VERDICT: PASS.** `sha=a22c0d7 deployed=yes ghosts=0 drained_30m=13`. Polled the
  live VM on a progress metric (deployed sha + ghost count) rather than a fixed sleep. The `slot-cron-ff-pull` +
  `--reload` carried the fix to the box with no human step, and the first reaper tick after the reload archived all 11
  at once (every one was already far past the 15-min grace). Doc flipped to `resolved`. **Standing caution**: `a21ccba`
  looked complete by every static signal — correct code, green gate, deployed, load-bearing tests — and still left the
  operator's symptom fully intact. Only the live count settled it.
- **Runtime verdict query** (kept for reuse — no `sqlite3` CLI on the VM, use the venv python; the table is `agents`; DB
  `/var/lib/orchestrator/state.db`; read via `file:…?mode=ro`):

  ```sql
  SELECT COUNT(*) FROM agents
  WHERE status IN ('active','stale') AND lifecycle IN ('one_shot','scheduled') AND tmux_session IS NULL;
  -- expect 0 within ~15 min of the reload; the drained rows carry exit_reason='lifecycle-complete'
  ```
