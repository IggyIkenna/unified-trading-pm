---
doc_type: issue
title:
  A stored AgentRow.agent_kind not in the AgentView Pydantic Literal 500'd GET /api/agents on every call, taking the
  whole AO dashboard down (stuck on "Loading…" indefinitely) — 4 real, already-in-use kinds were missing
summary: >-
  Operator reported the AO dashboard stuck on "LOADING… Fetching dashboard state" indefinitely, right after two earlier
  fixes shipped this session (SlotRow/AgentRow liveness desync, the escalation-verdict feature). Root cause was
  unrelated to either: a live AgentRow existed with agent_kind='data_pipeline_failure' — a real, intentionally- wired
  escalation kind (dedicated boot prompt agents/data_pipeline_failure.md, routed via server/escalation.py's
  _DATA_PIPELINE_WALLS) — but that value was never added to AgentView's AgentKind Literal (server/models/_types.py). GET
  /api/agents therefore raised a pydantic ValidationError on every single call; the dashboard's refresh() polls
  /api/agents inside the same Promise.all as /api/state, so one permanently-failing call meant `state` never got set and
  the page never left the loading screen — for every operator, indefinitely, until this was found and fixed. While
  verifying the fix, live-caught the SAME bug already firing for a second, different value (ag_closeout_auditor,
  confirmed via a live 500 on GET /api/agents?include_finished=true) — investigation found 3 MORE real, already-in-use
  agent_kind values missing from the same Literal (docs_reconciler, ag_closeout_auditor, na_eligibility_auditor — all
  from server/plan_health.py's _MODE_AGENT_KIND map), meaning this exact outage was one scheduled cron firing away from
  recurring, repeatedly, regardless of the first fix. Fixed all 4 gaps, then closed the underlying architectural hole
  permanently: AgentView.agent_kind now coerces any future-unrecognized value to "custom" (logged loudly) instead of
  raising — including the genuinely open-ended server/routes/slots_worker.py `agent_kind=req.slot_role` path (arbitrary
  caller-supplied string, never closable by enumeration alone) — plus a QG-level regression test cross-validating every
  known agent_kind-producing source dict against the Literal, so the next person who adds a new scheduled-audit kind
  without updating the Literal fails CI instead of production. A third, unrelated bug (slot 0's SlotRow/AgentRow
  liveness fix from earlier this session silently not applying to main specifically, due to a tmux-session-name
  mismatch) was found and fixed while re-verifying live state during this investigation — see the Fix section.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, outage, pydantic, agent_kind, bug, hardening]
related:
  [
    ao_slot_agentrow_liveness_desync_and_escalations_ui_gap_2026_07_27,
    ao_scheduled_job_observability_and_slack_alerting_2026_07_28,
  ]
created: 2026-07-28
priority: P0
parent_epic: orchestrator_master
source:
  "operator interactive session, slot 3 — reported the AO dashboard stuck on LOADING indefinitely, right after two prior
  fixes shipped in the same session"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by: slot-3 (interactive), agent-orchestrator@aeccec0, @ce206d0, @b182f82
locked_by:
---

> **🟢 RESOLVED 2026-07-28** — `agent-orchestrator@aeccec0`, `@ce206d0`, `@b182f82`: added the 4 missing `AgentKind`
> Literal values, hardened `AgentView.agent_kind` to coerce any future-unrecognized value to `"custom"` instead of
> raising, added a QG regression test cross-validating every known `agent_kind`-producing source against the Literal,
> and fixed the unrelated main-session liveness gap found while re-verifying. Live-verified: `GET /api/agents` and
> `?include_finished=true` both `200` (were `500`). No open follow-ups.

# AO dashboard outage — AgentKind Literal gap + fail-soft hardening

## What I found

### The outage

`GET /api/agents` (`server/routes/agents.py::list_agents` → `_agent_to_view` → `AgentView(...)`) crashed with a pydantic
`ValidationError` on every single call:

```
Input should be 'orchestrator', 'worker', 'review', 'cicd', 'conflict_resolver', 'plan_health', 'plan_reconciler',
'monitor' or 'custom' [type=literal_error, input_value='data_pipeline_failure', input_type=str]
```

`data_pipeline_failure` is a real, already-wired escalation kind (`agents/data_pipeline_failure.md`, routed via
`server/escalation.py`'s `_DATA_PIPELINE_WALLS`) — some prior commit added the routing logic and started producing this
`agent_kind` value without ever adding it to `AgentKind` (`server/models/_types.py`). The dashboard's polling loop
(`App.tsx::refresh()`) fetches `/api/state` and `/api/agents` inside the SAME `Promise.all` — one permanently- failing
call means the batch never resolves, `state` never gets set, and the page never leaves
`LOADING… Fetching dashboard state`. Confirmed live via `journalctl -u orchestrator.service` on the planning VM
(`i-0c9b283b31d6b5ca7`, read-only SSM).

### It was not an isolated gap

While re-verifying `GET /api/agents?include_finished=true` (the "Show finished" toggle's endpoint) after the first fix,
that variant STILL 500'd — this time on `agent_kind='ag_closeout_auditor'`. Investigation
(`server/plan_health.py::_MODE_AGENT_KIND`) found 3 more real, currently-scheduled kinds with the identical gap:
`docs_reconciler`, `ag_closeout_auditor`, `na_eligibility_auditor` — all 4 of the daily-scheduled planning-cleanup jobs'
kinds (see `ao_scheduled_job_observability_and_slack_alerting_2026_07_28.md` for what those jobs are). This meant the
SAME outage was one cron firing away from recurring indefinitely, regardless of fixing only the first symptom.

### A third, unrelated bug found while re-verifying

Re-checking slot 0 (main)'s live state during this investigation found the EARLIER session fix
(`ao_slot_agentrow_liveness_desync_and_escalations_ui_gap_2026_07_27.md`) had never actually taken effect for main
specifically: `_slot_to_view`'s tmux-session fallback used the generic `orch-slot-N` formula for every kind, but main's
real tmux session is the hardcoded singleton `main_agent_keeper.MAIN_SESSION_NAME` ("orch-agent-main") — never
"orch-slot-0". `worker_alive` and the `AgentRow` liveness overlay both silently missed main because
`find_active_agent_for_session(session, "orch-slot-0")` correctly returns `None` (no `AgentRow` is ever bound to that
literal string) — confirmed live: `worker_alive` still read `False`, `last_ping` still the 21-day-stale value, hours
after the original fix shipped. Review was unaffected (it boots through the normal `/boot` flow that DOES set
`AgentRow.tmux_session = "orch-slot-1"`, matching the generic formula) — which is exactly why the original fix's 4 test
files (all green) never caught this: none exercised main's special-cased session name.

## Fix

- **`agent-orchestrator@aeccec0`**: added `data_pipeline_failure` to `AgentKind` (`server/models/_types.py`) + matching
  frontend `AgentKind` union/`KINDS_ORDER`/`AGENT_KIND_LABEL`. Also fixed, found in passing: this checkout's `.venv` had
  `fastapi==0.136.3` installed against a `pyproject.toml` pin of `>=0.137.0` — a stale-venv/`uv sync` gap unrelated to
  any code, but it was failing `pytest` collection at `conftest.py` import time for the entire suite.
- **`agent-orchestrator@ce206d0`**: added the 3 remaining live gaps (`docs_reconciler`, `ag_closeout_auditor`,
  `na_eligibility_auditor`). The real, durable fix: `AgentView.agent_kind` gained a `field_validator` that coerces ANY
  value not in `AgentKind` to `"custom"` (logged loudly) instead of raising — this is the actual backstop, since it also
  covers `server/routes/slots_worker.py`'s `agent_kind=req.slot_role` path (arbitrary caller-supplied input, no enum
  check at all, can never be closed by enumeration). Refactored `server/escalation.py`'s inline
  prompt-template→agent_kind dict to a named module constant so a test could import it. NEW
  `tests/test_agent_kind_literal_coverage.py` (4 tests): cross-validates every known agent_kind-producing dict
  (`_MODE_AGENT_KIND`, the escalation map) against the Literal — the actual QG hardening; the next person who adds a new
  scheduled-audit kind without updating `AgentKind` now fails CI instead of production.
- **`agent-orchestrator@b182f82`**: `server/routes/state.py`'s `candidate_session` now resolves to
  `main_agent_keeper.MAIN_SESSION_NAME` when `kind == "main"`, instead of the generic per-slot formula. NEW
  `tests/test_slot_view_main_session_liveness.py` (2 tests): main resolves liveness correctly via the singleton session
  name (regression for this exact gap); review still resolves correctly via the generic formula (proves no regression on
  the case that already worked).

## Verification

- Full repo `bash scripts/quality-gates.sh` after each of the 3 commits: 1813 → 1820 → 1824 → 1826 server tests
  (climbing as tests were added; the jump from 1813→1820 includes the unrelated `uv sync` picking up 7 more collected
  tests) + 154 dashboard tests, all green each time.
- Live-verified on the VM after each deploy (AWS SSM, read-only): `GET /api/agents` and
  `GET /api/agents?include_finished=true` both `200` (were `500`); `GET /api/state` slot 0 now reports
  `worker_alive: true`, `tmux_alive: true`, real-time `last_ping`, and its actual current `last_msg` (was `false`/
  21-day-stale/an old task's message).

## Follow-ups

None open. Not checked (future audit candidate if the operator wants it): whether any OTHER Pydantic response model in
this codebase has the same open-Literal-fed-by-unconstrained-write-path risk pattern — only `AgentKind` was audited and
hardened here, because it's the one that actually broke production.
