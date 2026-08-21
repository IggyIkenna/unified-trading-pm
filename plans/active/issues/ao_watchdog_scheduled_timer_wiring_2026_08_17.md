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
related: [/plans/active/ao_consolidated_closeout_2026_08_12.md]
created: 2026-08-17
priority: P2
parent_epic: orchestrator_master
source: >-
  Session that authored the /ao-watchdog skill (2026-08-17) — the skill's own "Scheduling this skill" section
  named this as required follow-up work rather than half-wiring it without tests inline.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    cursor-configs/skills/ao-watchdog/SKILL.md,
    agent-orchestrator/server/plan_health.py,
    agents/ao_watchdog.md,
    agent-orchestrator/scripts/install-ao-watchdog-timer.sh,
  ]
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
- [x] ✅ [BACKEND] P2. **Add a thin role wrapper** `unified-trading-pm/agents/ao_watchdog.md` — mirror
      `agents/escalation_queue_reconciler.md`'s shape exactly (a THIN wrapper carrying only the scheduled-dispatch
      boot/completion contract; the full procedure stays the skill's own SSOT, this file must not duplicate it).
      One-shot lifecycle: `POST /api/slots/$SLOT_ID/done` with `one_shot_complete: true` at the end, no looping.
      — unified-trading-pm@16ab4aa117. Mirrored `escalation_queue_reconciler.md`'s frontmatter shape (role:
      ao_watchdog, model: sonnet, sonnet_variant: default, thinking: high, lifecycle: scheduled) and STEP 0-2 body
      structure exactly — STEP 1 points at `cursor-configs/skills/ao-watchdog/SKILL.md` as the SSOT (Steps 0-12),
      STEP 2 is the standard one-shot `/done` completion contract. Also updated the SKILL.md's own "Scheduling this
      skill" section (previously stale — it claimed the role wrapper "already has a sibling" before this file
      existed) to state the wiring is now live, and corrected its `_MODE_TO_ROLE` reference to the actual
      `_MODE_PROMPT_TEMPLATE`/`_MODE_AGENT_KIND` dict names.
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
- [x] ✅ [BACKEND] P3. **Tests** for the new `plan_health.py` dispatch branch — mirror
      `test_plan_health.py`'s `escalation_reconcile`-mode test shapes (dispatch routes to the right role, mode
      exemptions behave correctly).
      — agent-orchestrator@a404d74303. `escalation_reconcile` itself turned out to have no dedicated named test in
      `test_plan_health.py` (checked — 0 hits); mirrored the closest actual reference shape instead, the
      `forces_smart_tier`/`never_calls_report_gate`/`registers_<kind>_kind` trio used by
      `context_scout`/`na_eligibility`/`docs_reconcile` (every mode in `plan_health.py`'s `smart_tier` tuple, which
      `ao_watchdog` is also in, unlike its opt-out sibling `data_pipeline_alerts_reconcile`). Added
      `test_dispatch_ao_watchdog_mode_forces_smart_tier`, `test_dispatch_ao_watchdog_mode_never_calls_report_gate`,
      `test_dispatch_ao_watchdog_registers_ao_watchdog_kind` — all 3 pass; full repo `quality-gates.sh` green
      (4123 passed, 9 skipped, 0 failed) run in an isolated worktree at `origin/live-defi-rollout` HEAD to sidestep
      unrelated concurrent WIP in the shared slot checkout.
- [x] ✅ [OPERATOR] P3. **DECIDED 2026-08-18** — confirmed daily, run around midnight UTC, staggered against the
      existing `ci_reconciler`/`plan_reconciler` nightly timers (not simultaneous with them) with enough buffer for
      one retry before morning — supersedes the doc's earlier 06:25 UTC placeholder. Operator's own framing: a
      later manual re-check (e.g. Harsh on his laptop) should be able to see that the scheduled midnight run
      already did a "pre-audit" and only need to check the delta since then, rather than redoing the full sweep —
      worth keeping in mind when the actual dispatch-mode wiring (todo above) designs how this run's output/state
      gets persisted for a later run to diff against, not just posted to Slack and discarded.
- [x] ✅ [SCRIPT] P2. **Update the already-installed timer's cadence to match the operator's decision above** — the
      shipped `install-ao-watchdog-timer.sh` (`agent-orchestrator@6d48977f52`) still fires at
      `OnCalendar=*-*-* 06:25:00 UTC`, which the operator's 2026-08-18 decision explicitly supersedes (midnight
      UTC, staggered against `ci_reconciler`/`plan_reconciler`, retry buffer before morning). Re-check the live
      minute-table (`grep -H '^FIRE_MINUTE=' install-*.sh`, per the original installer todo's own method — don't
      trust a stale doc table) for a free near-midnight offset, update the script's `OnCalendar`.
      — agent-orchestrator@a404d74303. `FIRE_HOUR="00"`/`FIRE_MINUTE="47"` (`OnCalendar=*-*-* 00:47:00 UTC`),
      re-checked against the LIVE per-hour minute table at hour 0 specifically (several jobs recur every
      hour/every-N-hours and land on midnight too, not just their headline offset — occupied minutes at hour 0:
      `00,05,08,12,15,23,27,30,35,38,40,42,52,53,57`; `:47` sits in the open gap after local-ratchet's `:42` and
      before context-scout's `:52`, untaken by any job at any hour). Full rationale + the minute-by-minute
      derivation is now inline in the script's header comment, and
      `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md`'s "The 10 timers" table gained the missing
      `ao-watchdog` row (codex-alignment check per the archival ritual). **Scope note**: this laptop dev session
      had no central-VM access, so only the repo-side script change is done here — the live orchestrator-VM
      systemd timer re-run + verification is split out as its own todo below rather than silently left undone.
- [ ] [OPERATOR] P2. **Re-run `install-ao-watchdog-timer.sh` on the central orchestrator VM** (needs VM access —
      SSH or an AO-dispatched worker running ON the VM, neither available to this laptop dev session) so the live
      systemd timer actually picks up the new `00:47 UTC` cadence shipped in `agent-orchestrator@a404d74303` (the
      live unit still fires at the old `06:25 UTC` until this runs). Verify via `systemctl --user list-timers` —
      confirm `ao-watchdog.timer` shows the new next-trigger time.

## Why this wasn't done in the same session as the skill itself

Backend dispatch-mode wiring is real engineering (a new code path + tests), not something to half-wire inline
without verifying it — the skill itself is fully usable manually / via `/autonomous` in the meantime, exactly the
same bridge state `escalation-queue-reconcile` and `docs-reconcile` were in before they got their own timers.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` — the dispatch mechanism this wires into.
- `unified-trading-pm/cursor-configs/skills/ao-watchdog/SKILL.md` — the skill this schedules; its own "Scheduling
  this skill" section is the canonical statement of this gap, kept in sync with this doc.

## Progress Log

- **context-scout 2026-08-19**: populated context_scope (5 entries).
