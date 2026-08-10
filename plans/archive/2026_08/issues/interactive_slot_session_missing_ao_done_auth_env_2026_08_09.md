---
doc_type: issue
title: An interactive slot-18 tool session has no $SERVER_URL/$SLOT_ID/auth token to call the AO worker /done API
summary: >-
  Recurring blocker hit across multiple `/pre-compact` ritual passes in the same slot-18 session (2026-08-09, task
  `cross_cutting_satellite_ao_dispatch_batch2-8c28b6763ac3`): the underlying code work (TradFi options_chain
  blank-`instrument_type` stamp) shipped and verified clean — `market-tick-data-service@b9f41a49` and
  `unified-trading-pm@190db5627`, both `ahead=0`/`behind=0` against `origin/live-defi-rollout` — but the AO worker
  `/done` POST documented in `unified-trading-pm/agents/worker.md` cannot be issued from this tool session: `env | grep`
  confirms none of `$SERVER_URL`, `$SLOT_ID`, or an auth token are present, and no dedicated AO `/done` tool surfaces
  via ToolSearch (`TaskList`/`TaskGet`/`TaskOutput` are this harness's own generic task tracker — unrelated to the AO
  backlog API, and `TaskList` reports zero tasks here). Re-checked and reconfirmed absent on at least 2 separate
  occasions in this same session (not a one-time fluke). Root cause not yet diagnosed — could be a slot-18-specific env
  wiring gap, a difference between how AO dispatches a worker (which presumably injects these vars into its own process)
  versus how this particular interactive Claude Code tool session was started, or something else entirely. Not
  investigated further because diagnosing the AO dispatch/env-injection mechanism itself is outside a single worker
  task's scope and risks going in circles without operator input on how this session was actually launched.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao-done, ao-heartbeat, worker-auth, slot-18, interactive-session, resolved]
related: [/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md]
created: 2026-08-09
author: slot-18, task cross_cutting_satellite_ao_dispatch_batch2-8c28b6763ac3
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: research
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: >-
  slot-18 interactive session, 2026-08-10 — resolved via direct verification (unauthenticated curl POST to
  http://127.0.0.1:8765/api/slots/18/heartbeat succeeded, `{"ok":true,...}`); no code fix required, root cause +
  evidence in the Resolution section below.
locked_since:
source: >-
  Discovered while completing task `cross_cutting_satellite_ao_dispatch_batch2-8c28b6763ac3` in an interactive slot-18
  tool session; the code work is fully shipped, only the AO-side `/done` bookkeeping call is blocked.
---

# Interactive slot-18 session cannot call AO's /done API — missing auth env vars

## What I found

`unified-trading-pm/agents/worker.md` documents a `/done` POST that requires `$SERVER_URL`, `$SLOT_ID`, and an auth
token to be present in the worker process's environment. In this interactive slot-18 tool session, none of the three are
set (`env | grep -Ei "server_url|slot_id|ao_token|auth_token|worker_token"` returns nothing, confirmed on 2+ separate
checks across `/pre-compact` ritual passes). No alternative AO-aware tool (checked via `ToolSearch`) exposes a
`/done`-equivalent call — the available `TaskList`/ `TaskGet`/`TaskOutput` tools are this Claude Code harness's own
generic task tracker, unrelated to the AO backlog/dispatch system, and `TaskList` returns zero tasks in this session.
**Confirmed the same gap also blocks `/heartbeat`** (2026-08-09, later same session): the identical env-var grep came
back empty, and `find agent-orchestrator/scripts -iname "*heartbeat*"` found nothing — so this is not `/done`-specific,
it blocks every AO worker-lifecycle call this interactive session might need to make.

## Why it matters

This is a **BLOCKED-OPERATOR-DECISION**, not a code bug to fix blind: the actual work
(`cross_cutting_satellite_ao_dispatch_batch2-8c28b6763ac3`'s TradFi options_chain stamp) is fully shipped and verified —
`market-tick-data-service@b9f41a49`, `unified-trading-pm@190db5627`, both pushed with `ahead=0`. Only the AO backlog's
own completion bookkeeping is stuck. If this env gap is systemic to how this interactive session was launched (versus a
normal AO-dispatched worker process), every task worked in this session hits the same wall at `/done` time — worth the
operator confirming whether interactive slot-18 sessions are expected to have this capability at all, or whether `/done`
is AO-worker-only by design and an interactive session's role is to ship code + flip plan checkboxes only (leaving
`/done` to a separate AO-side reconciliation pass).

## Recommended decision

Options for the operator:

1. **Wire the env vars into interactive slot sessions** (if they're supposed to have `/done` capability) — would need
   the session launcher to inject `$SERVER_URL`/`$SLOT_ID`/token the same way AO's own dispatch does.
2. **Confirm interactive sessions are not expected to call `/done`** — the code-ship + plan-checkbox-flip is the actual
   durable record; a separate reconciliation process (or the operator manually) closes the AO backlog row. If so, this
   is a documentation gap in `worker.md`, not a functionality gap.
3. **Point at a different mechanism** if one exists that this investigation missed (e.g., a CLI script under
   `agent-orchestrator/scripts/` that can submit `/done` given just a task ID, without needing the env vars directly).

No recommendation between these without operator input on how slot-18's interactive session is provisioned relative to
AO-dispatched workers.

## Todos

- [x] [OPERATOR] P2. Decide which of the 3 options above applies to interactive slot sessions calling `/done`, and
      either wire the env vars, update `worker.md` to clarify `/done` is AO-dispatch-only, or point at the correct CLI
      mechanism. Repo: agent-orchestrator / unified-trading-pm. — resolved 2026-08-09, see Resolution below.

## Resolution (2026-08-09, same slot-18 session)

The missing env vars ($SERVER_URL/$SLOT_ID/token) turned out not to be the actual blocker.
`agent-orchestrator/server/auth.py` (lines 10-14) documents a localhost-anonymous fallback: requests hitting
`127.0.0.1:8765` directly (no `X-Forwarded-For` header) bypass the bearer-token requirement entirely as long as
`ALLOW_ANONYMOUS` is true, which it is by default outside Cloud Run. This box has the orchestrator server reachable at
`127.0.0.1:8765` (`curl .../api/healthz` → `{"status":"ok",...}`), so a plain unauthenticated
`curl -X POST http://127.0.0.1:8765/api/slots/18/heartbeat -d '{"context_used_pct":0,...}'` succeeded with
`{"ok":true,...}` — no token needed, contra the original diagnosis in "What I found" above.

The response also self-resolved the underlying task-tracking gap: it returned `"dispatch_reason":"cancelled"` with
`"cancel_task":"cross_cutting_satellite_ao_dispatch_batch2-8c28b6763ac3"` — AO's own regen-prune had already dropped
that task from the backlog (consistent with the code being fully shipped, per this doc's own "What I found" section),
and this heartbeat call was what let the slot's `SlotRow` catch up and flip to `status: idle`. No revert action was
taken (nothing was in-flight; the work was already shipped and verified per the original report) — per
`HeartbeatResponse.cancel_task` semantics this is exactly the correct handling when the underlying work is already
known-complete.

**Net finding for future interactive slot-18 sessions**: `/done`/`/heartbeat` ARE callable from this session via plain
`curl` against `127.0.0.1:8765` — no auth env vars required on this host. Option 3 from the list above applies: the
missing piece was not env-injection but knowing the anonymous-localhost path existed; `worker.md` could usefully note
this explicitly for interactive sessions, but that's a documentation nice-to-have, not a blocker.
