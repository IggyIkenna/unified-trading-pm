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
  FIXED: the TmuxPruner now archives one_shot/scheduled agents (exit_reason=`lifecycle-complete`) in the same pass it
  clears the dead chip, mirroring the reaper so whichever daemon observes the death first agrees.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, reaper, tmux-pruner, agent-lifecycle, one-shot, cicd-escalator, fleet-view, dashboard]
related:
  [
    ../../codex/04-architecture/agent-orchestrator-overview.md,
    ../../codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: orchestrator_master
priority: P1
assigned_vm: NA
execution_scope: local-only
resolved_by:
  - "agent-orchestrator@a21ccba — TmuxPruner archives terminal-lifecycle agents on session death + regression test"
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

> **✅ RESOLVED 2026-07-16 — `agent-orchestrator@a21ccba`.** The TmuxPruner now archives one_shot/scheduled agents on
> session death, so a finished cicd escalator is reaped within one prune tick (~60s) of its session dying instead of
> waiting out the 6h `stale_grace`. Full AO quality gate green (1333 passed); 4 new pruner tests + the 52-test reaper
> suite pass, including `test_multi_instance_cicd_not_deduped_as_singleton` (the reaper's isolated multi-instance
> contract is unchanged — the fix is in the pruner). Existing terminal ghosts on the live VM drain naturally: the
> retention prune (`prune_finished_agents`) caps the archived roster, and the next prune tick after each ghost's session
> is confirmed dead now archives it.

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

## Verification

- `bash scripts/quality-gates.sh` → **PASSED** (ruff + basedpyright + `1333 passed, 1 skipped` + dashboard tsc/vitest).
- New `tests/test_tmux_pruner_agent_reap.py` (4 cases): dead-session cicd → archived `lifecycle-complete`; dead-session
  scheduled (plan_health) → archived; dead-session persistent (review) → chip nulled but stays active; live-session
  one_shot → untouched.
- `tests/test_reap_orphan_agents.py` (52 cases) unchanged and green — the reaper's contracts are untouched.

## Todos

- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@a21ccba`.** TmuxPruner archives one_shot/scheduled agents
      on session death; regression test added; full AO quality gate green.
- [ ] [BACKEND] P3. **Optional cleanup — retire the misleading "stays active" assertion.**
      `test_multi_instance_cicd_not_deduped_as_singleton` still documents the pre-fix end-state in its docstring. Its
      PRIMARY assertion (`not superseded-cicd`) is a real reaper contract and must stay; only the incidental "stays
      active via the stale_grace fallback" wording now describes a state the pruner no longer allows end-to-end. Left as
      a follow-up so the fix ships without touching an otherwise-green reaper test. **Gate**: docstring reworded, test
      still green.

## Progress Log

- **2026-07-16** — Operator flagged the FleetView pile-up ("many cicd escalators registered, only one live, why aren't
  the dead ones pruned"). Traced through `escalation.escalate` (registration) → `reap_orphan_agents` (three archival
  signals, two gated on non-null `tmux_session`) → `TmuxPruner.prune_once` (nulls the field, leaves status active) →
  `_SINGLETON_AGENT_KINDS` (cicd excluded). Root cause: the pruner nulling the field before the reaper's instant-reap
  fires, dropping the record onto the 6h cloud-agent `stale_grace`. Fixed in the pruner (archive terminal-lifecycle
  agents on session death); regression test added; full AO quality gate green.
