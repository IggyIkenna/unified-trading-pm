---
doc_type: plan
title: AO Death Diagnostics Consolidation, Compaction KPIs, and Sequential-Task Carve-out
summary:
  Operator-driven follow-up from a 2026-08-14 tmux_session_lost cluster investigation (see
  ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md's Progress Log) — consolidate death diagnostics into one event,
  distinguish benign session recycles from genuine losses, surface compaction/wedge KPIs on the live dashboard with
  plan-worker/escalation/scheduled visibility, and design (but not yet ship) a scoped carve-out to the 2026-08-04
  one_task_per_session ruling for sequential-plan continuations.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, observability, context-lifecycle, dashboard, tmux-pruner]
related:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /codex/15-runbooks/tmux-death-diagnostics.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
effort: high
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /codex/15-runbooks/tmux-death-diagnostics.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/fleet_kpis.py,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator-driven follow-up from an interactive session (2026-08-15) investigating a 2026-08-14
  tmux_session_lost cluster (see "Why this doc exists" below) — the operator confirmed all four
  follow-up asks as work to do, explicitly directing the KPI-dashboard piece stay a human plan.
assigned_role: infra
drift_direction: advance-code
---

# AO Death Diagnostics Consolidation, Compaction KPIs, and Sequential-Task Carve-out

## Why this doc exists

An interactive session investigated a 2026-08-14 23:33:47-48Z 5-slot `tmux_session_lost` cluster (full findings in
`/plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`'s Progress Log). The operator then asked
four follow-up questions and confirmed all four as work to do, plus explicitly asked for the KPI-dashboard piece to be a
**human plan** (this doc) rather than auto-dispatched. This is a LOCAL/human plan (`assigned_vm: NA`) — the operator is
driving it interactively, not the AO fleet.

## Operator's four asks (verbatim intent)

1. **Consolidation**: "was the task done" data was scattered across a separate pruner journal line and a second
   task-scoped `tmux_session_lost` row — consolidate it into the SAME event.
2. **Disambiguation**: `burst_size` conflated an ordinary `one_task_per_session` recycle-teardown with a genuine
   mid-task loss when several of each landed in the same pruner tick — distinguish them.
3. **KPI visibility**: no live-dashboard view of compaction/wedge rates (current vs. prior-24h baseline, by
   slot/role/day) — only a one-shot CLI readout existed. Also: plan-worker vs. escalation vs. scheduled craft
   compaction/wedge behavior was invisible — all three shared the generic `role=="worker"` label.
4. **Sequential-task carve-out**: sequential-plan tasks should NOT be torn down between steps the way
   `one_task_per_session_enabled` (default `True`, 2026-08-04 ruling) currently forces — instead run pre-compact→compact
   and continue in the same session when the next step is ready.

## What shipped this session (items 1-3)

- [x] 1. ✅ [INFRA] P1. Consolidate `current_task`/`task_runtime_seconds` into the `tmux_session_lost` event's own
      `details_json` (snapshotted BEFORE the requeue/resume mutation clears them), closing the "scattered across 3
      places" gap. `agent-orchestrator/server/tmux_pruner.py`'s slot-death loop. Done-when: a fresh `tmux_session_lost`
      row for a mid-task death shows non-null `current_task` + `task_runtime_seconds` without needing to cross-reference
      the journal or a second event row. — `agent-orchestrator@c46102b9b5`, `quality-gates.sh` green (3852 passed).
- [x] 2. ✅ [INFRA] P1. Add a `death_class` field (`"intentional_teardown"` vs `"unexplained"`) to the same event,
      computed by cross-referencing a curated set of already-logged, distinctly-named "intentional teardown"
      activity_log events (`worker_one_task_per_session_reset`, `context_wedge_recovered`, `watchdog_slot_killed`) for
      the same `slot_id` within a 90s lookback — this is the fix for
      `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`'s `[INFRA] P3` todo (burst_size conflation). `burst_size`
      itself is left unchanged (still "how many OTHER slots died this tick") — `death_class` is the per-row
      disambiguator a consumer filters on. **NOT exhaustive**: only covers kill_session call sites confirmed to log
      their own distinctly-named event; a plain `reason="manual"` reclaim with only a `logger.warning` line (no DB row)
      still reads as `"unexplained"`. `check-ao-recent-deaths.sh` updated to print it. Done-when: the 2026-08-14 23:33
      cluster, if re-queried, shows `death_class="intentional_teardown"` for slots 12/18/20 and `"unexplained"` for
      slots 10/11 (matches the hand-derived Progress Log analysis). — `agent-orchestrator@c46102b9b5`.
- [x] 3. ✅ [INFRA] P1. Tag every compaction-lifecycle event (`forced_precompact`, `forced_compact`,
      `forced_compact_ineffective`, `context_wedge_recovered`) with `craft_type` — `"plan_worker"` | `"main"` |
      `"review"` | an `agent_kind`/`lifecycle` value (`"cicd"`, `"one_shot"`, `"scheduled"`, etc.) — computed once per
      tick in `context_lifecycle.py`'s `_active_worker_slot_ids` via an `AgentRow.tmux_session` join (AgentRow has no
      direct `slot_id` FK). Purely additive — does NOT change which slots are swept into the unconditional worker
      force-compact path, only what gets logged. `_TargetState.craft_type` carries it through to every log site without
      touching any control-flow branch. Done-when: `/api/fleet-kpis`'s `compaction_by_craft_type` shows more than one
      bucket once escalation/scheduled crafts have run compaction events post-deploy. — `agent-orchestrator@c46102b9b5`.
- [x] 4. ✅ [INFRA] P1. Extend `/api/fleet-kpis` (`agent-orchestrator/server/fleet_kpis.py` + `server/routes/state.py`)
      with `compaction` / `compaction_baseline` (current-vs-prior-24h, mirroring the existing dispatch-efficiency shape
      exactly) and `compaction_by_craft_type` (the craft-type breakdown from the todo above). Scoped to current-window +
      baseline + craft-type breakdown for this pass — by-slot/by-day compaction breakdowns are NOT included (see the P3
      follow-up below) to keep the change bounded. — `agent-orchestrator@c46102b9b5`.
- [x] 5. ✅ [UI] P1. Render the new compaction KPIs on `FleetKpis.tsx` — two new tile panels (current window + baseline,
      same `TileBox`/`Panel` pattern as the existing efficiency tiles) and a "Compaction by craft type" breakdown panel.
      New pure mappers `compactionTiles`/`sortedByCraftType` vitest-covered in `FleetKpis.test.ts` (4 + 1 new tests),
      matching the existing `kpiTiles`/`sortedByRole` test pattern. — `agent-orchestrator@c46102b9b5`,
      `dashboard vitest` 360/360 passed, `tsc --noEmit` clean.

_(Also fixed in the same commit:
`tests/test_context_lifecycle.py::test_active_worker_slot_ids_excludes_review_and_non_working` updated for
`_active_worker_slot_ids`'s widened return contract, `list[int]` → `dict[int, str]` — a real, expected test-contract
update caught by the Pass-1 QG run, not a regression.)_

## Item 4 — CORRECTED: a DeepSeek-only carve-out already existed; extended to Claude (2026-08-15, later same session)

**This section's original text (below the line) was written before discovering `routes/slots_worker.py`'s
`_maybe_plan_switch_reset` already implements a `sequential: true` carve-out — just scoped to `provider == "deepseek"`
only, deliberately, because DeepSeek's disk-based cache survives hours-to-days while Claude's (~5min-1hr) does not
(skipping the reset for Claude risked a full cache-miss on the very next turn). The design-only text below is preserved
for its own record but is now SUPERSEDED by what actually shipped.**

- [x] 6. ✅ [INFRA] P0. Extend the existing DeepSeek-only carve-out to non-DeepSeek providers too, but ONLY when
      `req.context_used_pct` at `/done`-time is under a NEW, separate, conservative threshold
      (`sequential_carveout_max_context_pct_for_non_deepseek`, default 40 — well under
      `context_worker_force_compact_pct`'s 60) — leaving real headroom for context_lifecycle.py's existing ~60s
      unconditional worker force-compact tick to compact BEFORE the next big turn runs, closing the exact cache-miss
      risk the original DeepSeek-only scoping was written to avoid, without inventing any new synchronous compaction
      call inside the `/done` HTTP handler. `agent-orchestrator/server/config.py` (new tuning field) +
      `server/routes/slots_worker.py` (`_maybe_plan_switch_reset`). Two regression tests updated/added in
      `tests/test_task_lifecycle_done_gate_resume.py`: `..._still_resets_..._at_high_context` (65% — still resets, the
      safety boundary) and `..._skips_reset_..._at_low_context` (10% — now skips, the new behavior). —
      `agent-orchestrator@aebc1ea36a`.

<details><summary>Original design-only text (superseded, preserved for record)</summary>

Add a scoped carve-out so a `sequential: true` plan's next-ready task does NOT get torn down by
`one_task_per_session_enabled` (default `True`) — instead the SAME session runs pre-compact→compact (if
`context_used_pct` warrants it) and continues draining the next task, mirroring the PRE-2026-08-04 "case 1" path in
`/codex/04-architecture/agent-orchestrator-worker-liveness.md`'s dispatch-context-driven-lifecycle table. Explicit
conflict with the 2026-08-04/08-05 operator ruling noted; implementation sketch called for a NEW synchronous
pre-compact→compact call inside the `/done` handler — superseded by the simpler, safer headroom-gated approach actually
shipped above, which reuses the ALREADY-EXISTING tick-based compactor instead.

</details>

## Additional root-cause work, same extended session (2026-08-15) — triggered by two live operator questions

**"Can we retrospectively tell OOM from an external kill?"** — verified live (SSM) that the orchestrator's own service
user (`ubuntu`, group `adm`) can read both `journalctl -k` (kernel OOM-killer log) and `/var/log/audit/audit.log` (the
SAME auditd mechanism `ao_tmux_session_loss_mid_task_root_cause_2026_08_10` used to find the original `tmux kill-server`
root cause) WITHOUT any new privilege grant.

- [x] 7. ✅ [INFRA] P2. New `agent-orchestrator/server/death_forensics.py` — best-effort, never-raises
      `check_oom_kill`/`check_external_kill`/`classify_unexplained_death`, wired into `tmux_pruner.py` for every
      `death_class=="unexplained"` row, run AFTER the write session closes (this file's OWN documented precedent,
      `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26` — a subprocess call inside an open write transaction
      scales lock-hold time with fleet size). Logs a separate `unexplained_death_forensics` event per slot. 11 unit
      tests in `tests/test_death_forensics.py` (mocked subprocess, no live dependency). —
      `agent-orchestrator@aebc1ea36a`.

**"Slot #18 went 'stale' — the detail blob (`silence_seconds`/`threshold_seconds` only) doesn't say what/which slot/task
went stale, and diagnose+fix the root cause without a regression."** Live investigation (SSM) found: slot 18's account
got rate-limited ~07:31-07:34, then 20 consecutive `worker_kick_skipped_account_blocked` events over ~20min with NOTHING
recovering it faster — `mark_account_rate_limited` only steers FUTURE spawn decisions (`autospawn.py`'s headroom
picker), it does nothing for an ALREADY-running slot stuck on the now-blocked account. The slot sat silent until the
generic 25-30min staleness path eventually noticed independently, firing TWO separate pages 5 minutes apart for the same
root cause.

- [x] 8. ✅ [INFRA] P1. Enrich `slot_stale`/`slot_idle_stale` `details_json` with `current_task`/`tmux_session`/
      `account_id`/`last_msg` (previously silence_seconds/threshold_seconds only — self-contained now, no
      cross-referencing a separate column/UI chip needed). `server/health.py`. New test
      `test_slot_stale_detail_is_self_contained` in `tests/test_health_scheduled_lifecycle_exemption.py`. —
      `agent-orchestrator@aebc1ea36a`.
- [x] 9. ✅ [INFRA] P1. Root-cause fix: a NEW, SEPARATE escalation counter (`_consecutive_account_blocked_ticks`, own
      tuning field `account_blocked_kick_escalation_ticks` default 8) in
      `WorkerLivenessKicker._handle_account_blocked_pane` — after N consecutive blocked-pane ticks on a slot with a real
      `current_task`, **pages the operator** (`notify_slot_failed`, deduped once per episode) instead of silently
      waiting up to 25-30min for the generic staleness path. **Deliberately alert-only, NEVER a kill/respawn** — an
      earlier draft of this fix called `_maybe_auto_respawn_stuck_slot(force=True)` from this exact branch and was
      caught, before shipping, as a direct reproduction of `ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14`
      (7 slots sharing one blocked account force-killed within a 90s window) — this branch was deliberately carved OUT
      of the pane-classification escalation path specifically so account-blocked can never reach a force-kill; an
      N-slots-share-one-account scenario would tick every one of them up in lockstep and reproduce that exact incident,
      just delayed by N ticks instead of immediate. `server/worker_liveness/__init__.py` + `server/config.py`. 4 new
      regression tests in `tests/test_worker_liveness.py` (alerts at threshold / doesn't alert early / dedups within an
      episode / resets on recovery) — the first of these explicitly asserts `_maybe_auto_respawn_stuck_slot` is NEVER
      called, pinning the corrected design. — `agent-orchestrator@aebc1ea36a`.

**Lesson worth carrying forward**: the account-blocked branch's existing test
(`test_account_blocked_pane_skips_kick_and_marks_account_rate_limited`) already asserted
`mock_respawn.assert_not_called()` — a direct, named guard against exactly the mistake almost made here. Reading and
understanding an adjacent existing test BEFORE extending the code path it covers would have caught this without needing
to draft-then-catch it.

## Follow-ups not in scope for this doc (filed for later, not silently dropped)

- [ ] [INFRA] P3. Extend the compaction KPI breakdown to by-slot and by-day, same pattern as the existing dispatch
      efficiency breakdown in `fleet_kpis.py` — deliberately excluded from the P1 todos above to keep that change
      bounded; the exact same helper-function shape (`_fetch_compaction_rows` already exists) makes this a small
      follow-up once the P1 pass has been live long enough to be worth trend-viewing.
- [ ] [INFRA] P3. Extend the `death_class` intentional-teardown signal set beyond the 3 events currently checked
      (`worker_one_task_per_session_reset`, `context_wedge_recovered`, `watchdog_slot_killed`) to cover more
      `kill_session` call sites (`account_rotation_*`, `blocked_slot_timeout_release`, `usage_cap_resume`,
      `tier_realign`, `heartbeat_silent_resume`) — each of these already logs its OWN distinctly-named event near its
      kill_session call site; auditing which ones do and adding them to the tuple is mechanical, just not done in this
      pass to keep the initial change reviewable.

## Progress Log

- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (6 entries), still covers the 2 remaining P3 follow-ups (fleet_kpis.py breakdown extension, tmux_pruner.py death_class signal-set extension).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **2026-08-15 (interactive session)**: doc authored; items 1-3's five todos implemented + shipped
  (`agent-orchestrator@c46102b9b5` — `server/tmux_pruner.py`, `server/context_lifecycle.py`, `server/fleet_kpis.py`,
  `server/routes/state.py`, `dashboard/src/{FleetKpis.tsx,FleetKpis.test.ts,types.ts}`,
  `scripts/orchestrator/check-ao-recent-deaths.sh`, `tests/test_context_lifecycle.py`). Pass-1 `quality-gates.sh` caught
  one real, expected test-contract update (see above) and one `ruff format` violation in `fleet_kpis.py` (fixed with a
  scoped `ruff format` on that one file, not a tree-wide reformat) before going green (3852 passed, 6 skipped; dashboard
  360/360 passed; `tsc --noEmit` clean). Shipped via `quickmerge --agent`, landed on `live-defi-rollout`.
- **2026-08-15 (same extended session, later)**: operator confirmed "let's do item 4" — discovered a DeepSeek-only
  carve-out already existed and extended it to Claude instead (todo 6, see the corrected section above); operator then
  asked two more root-cause questions (OOM/kill forensics, slot-18 staleness), answered + fixed live (todos 7-9). All
  four shipped together: `agent-orchestrator@aebc1ea36a` (`server/config.py`, `server/health.py`,
  `server/routes/slots_worker.py`, `server/tmux_pruner.py`, `server/worker_liveness/__init__.py`,
  `server/death_forensics.py` [new], `tests/test_death_forensics.py` [new], `tests/test_health_alert_dedup.py`,
  `tests/test_health_scheduled_lifecycle_exemption.py`, `tests/test_task_lifecycle_done_gate_resume.py`,
  `tests/test_worker_liveness.py`). `quality-gates.sh` green (3861 passed after this batch's own fixes: an import-sort
  lint, a regex bug in the new forensics module, a leftover duplicate assertion in a test edit, and 8 test fixtures
  missing the `account_id` field the enriched `slot_stale` detail now reads). Plan doc itself picked up a real 3-way
  `git stash pop` conflict mid-checkpoint — stray triple-angle-bracket-style conflict marker lines from reconciling
  against a concurrent peer session's unrelated push, which duplicated the Item-4/root-cause sections three times over —
  resolved by keeping the latest (sha-complete) copy and discarding the two stale ones; verified via a full-file re-read
  before the final push, not just a marker grep.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:a357726d73c656a9]: KEEP-NA, valid — 9 of 9 numbered todos shipped; explicit operator direction that this KPI-dashboard piece stays a human-driven plan, not auto-dispatched; 2 remaining items are small deliberately-deferred P3 follow-ups.
