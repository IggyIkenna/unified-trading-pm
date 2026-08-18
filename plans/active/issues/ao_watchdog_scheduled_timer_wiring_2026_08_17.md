---
doc_type: issue
title: Wire /ao-watchdog into the scheduled-job timer family (mode=ao_watchdog)
summary: >-
  The new `/ao-watchdog` skill (`unified-trading-pm/cursor-configs/skills/ao-watchdog/SKILL.md`,
  `unified-trading-pm@7683778b3e`) runs manually / via `/autonomous` today, matching every other scheduled-audit
  skill's own SSOT (`escalation-queue-reconcile`, `docs-reconcile`, etc.) BEFORE those got a systemd timer wired.
  This doc tracks the remaining backend work to give it the same standing cadence: a new `mode="ao_watchdog"`
  dispatch branch in `plan_health.py`, a thin role wrapper file, an installer script, and tests — mirroring the
  `escalation_reconcile` pattern exactly.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, ao-watchdog, scheduled-jobs, plan_health, follow-up]
related: [ao_consolidated_closeout_2026_08_12]
created: 2026-08-17
priority: P2
parent_epic: orchestrator_master
source: >-
  Session that authored the /ao-watchdog skill (2026-08-17) — the skill's own "Scheduling this skill" section
  named this as required follow-up work rather than half-wiring it without tests inline.
assigned_vm: planning
execution_scope: NA
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Wire /ao-watchdog into the scheduled-job timer family

## What's needed

Following the exact pattern `escalation_queue_reconciler` already established (see
`/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` and
`agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh` as the reference implementation):

- [x] ✅ [BACKEND] P2. **Add `mode="ao_watchdog"` to `agent-orchestrator/server/plan_health.py`'s dispatch handler** —
      a new entry in the mode→role mapping (mirroring `"escalation_reconcile": "escalation_queue_reconciler"`),
      plus whatever mode-specific branching the dispatch function needs (check lines ~648/653/666 in the current
      file for where `escalation_reconcile`'s exemptions/branches live and add the equivalent for `ao_watchdog`).
      — agent-orchestrator@e61d34737d. Mirrored `escalation_reconcile` into `_MODE_PROMPT_TEMPLATE`/
      `_MODE_AGENT_KIND`, the docstring mode list + force-exemption list, and the `smart_tier` tuple. Also had to
      add `"ao_watchdog"` to `server/models/_types.py`'s `AgentKind` Literal (`test_agent_kind_literal_coverage.py`
      caught this at QG Pass-1 — an omitted entry 500s `GET /api/agents`) and to `server/prompts.py`'s
      `_ONE_SHOT_ESCALATION_ROLES` frozenset (the exact gap that caused
      `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01` the last two times a plan_health mode was added
      without mirroring it there). Role wrapper file, install script, and tests are separate backlog todos below —
      not done by this item.
- [ ] [BACKEND] P2. **Add a thin role wrapper** `unified-trading-pm/agents/ao_watchdog.md` — mirror
      `agents/escalation_queue_reconciler.md`'s shape exactly (a THIN wrapper carrying only the scheduled-dispatch
      boot/completion contract; the full procedure stays the skill's own SSOT, this file must not duplicate it).
      One-shot lifecycle: `POST /api/slots/$SLOT_ID/done` with `one_shot_complete: true` at the end, no looping.
- [x] ✅ [SCRIPT] P2. **Write `agent-orchestrator/scripts/install-ao-watchdog-timer.sh`** — copy
      `install-escalation-queue-reconciler-timer.sh`'s structure (systemd `--user` timer + oneshot service,
      `ExecStartPre` health-gate, no sudo). Pick a cadence and an unused fire-minute offset — the existing minute
      table in `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` lists every taken slot (`:00, :05,
      :15, :20, :30, :40, :45, :52`); daily (matching this skill's own "daily health check" framing) is a
      reasonable starting cadence, open to revision once real dispatch data exists.
      — agent-orchestrator@6d48977f52. Copied the escalation-queue-reconciler standing-repeat shape (no
      `scheduled_job_already_ran.py` guard — a missed tick just waits for tomorrow's, same as the 3-hourly job)
      at a daily `OnCalendar=*-*-* 06:25:00 UTC` cadence (verified live minute defaults via
      `grep -H '^FIRE_MINUTE=' install-*.sh` rather than trusting the doc's table — live-taken minutes were
      `00, 05, 08, 12, 15, 30, 35, 40, 45, 52`; `:25` was free). Dispatches `{"mode": "ao_watchdog", "job_name":
      "ao_watchdog"}`. `bash -n` syntax-checked; full `quality-gates.sh` green on the committed HEAD.
- [ ] [BACKEND] P3. **Tests** for the new `plan_health.py` dispatch branch — mirror
      `test_plan_health.py`'s `escalation_reconcile`-mode test shapes (dispatch routes to the right role, mode
      exemptions behave correctly).
- [ ] [OPERATOR] P3. **Decide the cadence** once the skill has run manually a few times and its typical runtime /
      finding rate is known — daily is a starting guess, not a measured number.

## Why this wasn't done in the same session as the skill itself

Backend dispatch-mode wiring is real engineering (a new code path + tests), not something to half-wire inline
without verifying it — the skill itself is fully usable manually / via `/autonomous` in the meantime, exactly the
same bridge state `escalation-queue-reconcile` and `docs-reconcile` were in before they got their own timers.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` — the dispatch mechanism this wires into.
- `unified-trading-pm/cursor-configs/skills/ao-watchdog/SKILL.md` — the skill this schedules; its own "Scheduling
  this skill" section is the canonical statement of this gap, kept in sync with this doc.
