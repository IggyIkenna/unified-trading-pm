---
doc_type: issue
title:
  Review slot 2 sat genuinely dead for 23+ hours with zero trace of why — silent no-account respawn skip in
  `ensure_review_agents`, masked by an unrelated interactive session self-registering `role=review` with no real slot —
  fixed + hard-ruled + tested; scheduler/cicd/escalation generalization and dashboard tagging still open
summary: >-
  Operator asked "why is [the review badge] red" (screenshot) then, after I prematurely called slot 2's staleness
  "expected," pushed back: "ist emxempt for kill / reclaim btu tis that why hsitorically its gone away and nothgin
  brought it back? or thats another issue check the history." Investigation (distinct from the ALREADY-fixed
  `human_claim` bypass in `/plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md`) found slot 2's
  worktree was clean — not the git-conflict class of problem — but `ensure_review_agents()`
  (`server/autospawn.py`) had a bare, UNLOGGED `continue` whenever `select_account_for_spawn()` returned `None`
  (account exhaustion), so a tick could silently give up with zero signal in either the log stream or the Activity
  tab. Compounding this, an UNRELATED session had self-registered `role="review"` via `POST /api/agents/register`
  with no `tmux_session` at all (`has_rc_url=True` — the shape of an interactive/laptop session opting into dashboard
  presence, not an AO-spawned worker) — the dashboard read this as "review: healthy" the whole time, masking the real
  dead slot. Operator then generalized: "review agent shoudlnt run outside its configured slot hard rule with tests.
  just like scheduler agents, cice and escaltion agents for data pipeline all shoudl have configured slots so that
  worker agents take teh rest also configured and the tags inthe fleet oevrview and agents overview make this clear
  hard rule make tests to avoid regression." Fixed + tested + shipped the review-specific half; the generalization to
  other reserved-role agents and the dashboard-tagging half are still open (see Todos).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, review-agent, worker-lifecycle, slot-reservation, dispatch, dashboard]
related:
  [
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: "2026-08-17"
author: main (Claude Code, interactive session, operator-reported)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator@7df307a411 (partial — review-role half only)
locked_by:
source: >-
  Operator screenshot + live investigation, 2026-08-17, escalated into a generalized hard-rule request across
  scheduler/cicd/escalation agents plus dashboard tagging.
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/routes/agents.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/plan_health.py,
    /plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
---

# Review-slot hard rule: shipped for review; scheduler/cicd/escalation + dashboard tagging still open

## What shipped 2026-08-17 (`agent-orchestrator@7df307a411`)

1. `ensure_review_agents()` (`server/autospawn.py`): the account-selection-failure `continue` now logs
   `logger.warning(...)` AND posts an Activity-tab entry (`log_activity(..., "review_agent_spawn_skipped_no_account",
   slot_id=slot_id, details={"model": ..., "reason": ...})`) before continuing. `last_attempt` deliberately still NOT
   stamped on this path (so the next tick retries immediately rather than waiting out `cooldown_seconds`).
2. `server/routes/agents.py`: new `_reject_review_registration_outside_configured_slot()`, called at the top of
   `register_agent()` (`POST /api/agents/register`). HARD RULE: a `role="review"` registration is only accepted when
   `tmux_session` matches `orch-slot-N` for `N` in `config.review_slot_ids()`; anything else — no session, a session on
   a non-reserved slot, a malformed/non-fleet session name (e.g. the `orch-agent-{role}-{hash}` singleton shape) —
   gets `HTTPException(409)` plus a `review_agent_registration_rejected_wrong_slot` activity-log entry (captures the
   parsed `slot_id` when parseable, `None` otherwise, plus `configured_review_slots` for diagnosis). A genuine
   interactive-presence self-report is redirected in the error message to `POST /api/slots/{slot_id}/human-heartbeat`
   instead, which never claims to BE the review agent.
3. Regression tests: `tests/test_autospawn.py::test_ensure_review_agents_logs_and_retries_immediately_when_no_account_available`
   (asserts the log call, the activity-log call, AND that `last_attempt` is NOT stamped) and the new
   `tests/test_review_agent_slot_hard_rule.py` (7 tests covering: non-review roles are untouched; the configured slot
   passes; no-session/wrong-slot/malformed-session are all rejected with the right logged `slot_id`; a reconfigured
   `ORCHESTRATOR_REVIEW_SLOTS` is honored, not a hardcoded `2`; the route rejects BEFORE touching `ss.register_agent`).
   Full agent-orchestrator quality gate green (4021 passed, 7 skipped) before shipping.

## Why this is scoped to `role=review` only, for now

`register_agent()` is the self-registration path used by main + review agents specifically (typed one-shot workers —
cicd/escalation/scheduled — register via a completely different path,
`claim_slot_for_typed_agent()`/`_pick_free_slot()` in `server/escalation.py`/`server/plan_health.py`, out of this
function's reach). Extending the same "configured slot or reject" shape to those roles is Todo 1 below — it needs its
own design pass first (see Todo 2), not a copy-paste of this guard.

## Todos

- [ ] [BACKEND] P2. **Generalize the hard rule to scheduler/cicd/escalation agents**, per the operator's explicit
      instruction ("just like scheduler agents, cice and escaltion agents for data pipeline all shoudl have
      configured slots so that worker agents take teh rest also configured"). Concretely: audit whether
      `ci_escalation_reserved_slot_ids()`/`scheduled_task_reserved_slot_ids()` (or their current equivalents in
      `server/config.py` — names not yet confirmed, re-derive from `_pick_free_slot` call sites in
      `server/escalation.py` and `server/plan_health.py`) are already FIXED/explicit configured lists (mirroring
      `config.review_slot_ids()`) or are dynamically-derived top-N sets instead. If dynamic, decide (with the
      operator, this is a design fork not a mechanical fix) whether they should become fixed lists too. Then add the
      equivalent "reject a claim/registration for this role outside its configured slot" enforcement at whatever
      entry point(s) those roles actually use to bind to a slot (NOT `register_agent` — confirmed out of scope above),
      plus regression tests mirroring `test_review_agent_slot_hard_rule.py`'s shape.
- [ ] [BACKEND] P3. **Ordinary worker dispatch must be provably excluded from every reserved slot**, once Todo 1's
      configured-list question is settled — confirm `pick_next_task`'s slot-scope filters (`"review_slot"`,
      `"scheduled_reserve"`, and whatever CI/escalation's filter is named) cover the FULL current set of reserved
      roles, not just review + scheduled-reserve (the two already gated per
      `/plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md` and the scheduled-reserve fix in the
      Track 1 tracker). A missing filter for one reserved role is exactly this issue's root cause pattern repeating.
- [ ] [UI] P2. **Tag reserved-slot assignments visibly in Fleet Overview and Agents Overview**, per the operator's
      explicit instruction ("the tags inthe fleet oevrview and agents overview make this clear"). Concretely: both
      dashboard views should visibly distinguish a slot/agent that is a configured reserved role (review, scheduled,
      cicd, escalation — whatever Todo 1 settles on) from an ordinary worker slot, so an operator glancing at either
      tab can immediately tell "this IS the real review/cicd/escalation agent" vs. "this is an ordinary worker" —
      the exact ambiguity that let the masking self-registration in this issue go unnoticed for 23+ hours. Needs
      `[UI]` + `pw:L2` regression coverage per this workspace's UI testing hard rule
      (`/codex/06-coding-standards/ui-testing-layers.md`).
- [ ] [BACKEND] P3. **Design (with care — this touches the safety-critical branch-heal path) an auto-dispatch recovery
      agent for `REFUSED-kept-quarantined` git-conflict quarantines**, per the operator's explicit pushback on my
      framing this session: "i disagree i think it can alwasy be automated sure it can alerts in slack for trace but
      agents can always fix whether main or review." Today's slot-4 fix
      (`heal_dead_slot_branch_quarantine()` in `server/worktree_clean_check/_branch_state.py` deliberately refuses to
      auto-heal a dirty worktree, citing the `slot_branch_realign_discards_uncommitted_worktree_2026_07_17` incident)
      was resolved by hand this session (2 stash-pop conflicts in
      `plans/active/issues/sports_mdt_odds_captured_cells_not_found_rate_2026_08_16.md` +
      `plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md`, shipped `unified-trading-pm@33480f37d4`). The
      operator's position: this class of problem (content-aware conflict resolution on a quarantined worktree) should
      dispatch a recovery AGENT instead of waiting for a human to notice — with a Slack alert opened for traceability
      and a close bookend on resolution (per `/codex/04-architecture/agent-orchestrator-alerting.md`'s existing
      open/close pattern), not a permanent human-only escalation. Needs a proper design pass (what agent role runs
      it, what guardrails replace the dirty-worktree refusal's safety rationale, how it avoids repeating the exact
      2026-07-17 incident this refusal was built to prevent) before implementation — do not rush a change to this
      code path.
- [ ] [BLOCKED-OPERATOR-DECISION] P2. **Resume the interrupted IDE-compatible human-fleet heartbeat work** —
      **retagged 2026-08-19 (operator ruling, BLK-cf790dbf)**: the "operator-approved via AskUserQuestion" framing
      below is STALE. `ao_human_fleet_integration_2026_08_15.md` has an explicit design-decisions section that
      evaluated and REJECTED `UserPromptSubmit` as a heartbeat carrier, and per the operator's ruling that rejection
      STANDS — this todo needs a NEW operator ruling before proceeding, not a resumption of the prior approval.
      Original text preserved below for context if a future ruling does authorize it: before the `/autonomous`
      fleet-crisis pivot took over: `scripts/human_fleet/ao-statusline-heartbeat.sh`'s `statusLine`-based mechanism is
      confirmed terminal-only (does not fire in Cursor/VS Code IDE-extension mode — `COLUMNS`/`LINES` never populate);
      Claude Code's `UserPromptSubmit` hook is confirmed to fire identically across terminal/IDE/Desktop/web (official
      docs: "Hooks run wherever Claude Code runs... fire the same hook events"). Build a `UserPromptSubmit`-driven
      equivalent heartbeat sender reusing `scripts/human_fleet/ao_client.sh`'s existing IDE-agnostic bearer-token
      transport, so a Cursor-hosted session gets credited the same as a terminal one.
- [ ] [SCRIPT] P3. **Harden the human-fleet heartbeat setup into pre-commit**, same operator ask as above ("also
      harden that setup into pre commit so that people cant miss it with message as to the coddex docs that define
      setup"), deferred by the same pivot. Add a check (in `unified-trading-pm/scripts/pre-commit-templates/`, rolled
      out via `rollout-pre-commit-configs.sh` — never hand-edit a per-repo `.pre-commit-config.yaml`) that flags a
      missing/misconfigured heartbeat setup (`AO_SLOT_ID`/`AO_HUMAN_LABEL` env vars, `statusLine` config, and once
      Todo above lands, the `UserPromptSubmit` hook registration) with a message citing the codex SSOT(s) that define
      the setup. Model the WARN-only-by-default + env-var block-override shape on `check-quickmerge-provenance.sh`.

## Progress Log

- 2026-08-17: Filed after shipping `agent-orchestrator@7df307a411` (the review-role half of the operator's
  generalized hard-rule request). Corrected a stale Track 1 tracker line in
  `/plans/active/ao_open_work_consolidated_tracker_2026_08_14.md` that still read "NOT YET SHIPPED" for the
  already-landed `human_claim` fix (`agent-orchestrator@d13788ec2f`) — condensed in place, pointed here for the new
  work instead of duplicating.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries) -- kept the 4 source files this doc's
  own body names directly (the shipped fix + Todo 1's exact 2 generalization targets), swapped `server/config.py`
  and `dashboard/src` (lower-precision/single-todo-only) for the sibling reserved-slot-bypass issue doc Todo 2 cites
  by path and the worker-liveness codex SSOT, neither previously included.
- **na-eligibility-audit 2026-08-18 (ao tranche)**: RECLASSIFY (per-todo split) considered, then parked as CONFLICT — Todos 5-6 (UserPromptSubmit-driven IDE-compatible human-fleet heartbeat) individually read as bounded, but `ao_human_fleet_integration_2026_08_15.md` (the active, extensively-shipped plan owning this exact heartbeat mechanism) has an explicit "Design decisions... do not re-open without a new operator ruling" section that evaluated and REJECTED UserPromptSubmit as a heartbeat carrier (cites the same hook missing context-window/model/account fields). Whether Todo 5's "IDE-compatible" framing is a genuinely uncovered gap (statusline doesn't fire in Cursor/VS Code IDE mode) or re-litigates the rejected mechanism needs an operator call, not a worker read — parked, not extracted (see `ao_satellite_ao_dispatch_batch24_2026_08_18.md`'s "Explicitly excluded" section). Todos 1-4 confirmed KEEP-NA (explicit design fork, dependency-gated, or a safety-critical-path design-first requirement).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — reaffirmed. No content change since the
  2026-08-18 verdict. Todos 1-4 remain an explicit design fork (generalizing the review-slot hard rule to
  scheduler/cicd/escalation roles, gated on that same design decision), a dependency on it, and a safety-critical-
  path design-first requirement (the auto-heal-quarantine agent). Todos 5-6 (IDE-compatible heartbeat) stay parked
  as a genuine conflict against `ao_human_fleet_integration_2026_08_15.md`'s own explicit "do not re-open without a
  new operator ruling" rejection of the same carrier mechanism — still needs an operator call, not a worker read.
  Doc stays `assigned_vm: NA`.
