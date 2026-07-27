---
doc_type: issue
title:
  CI-failure escalations + scheduled dispatch never checked fleet_worker_cap — headroom for them was accidental, not
  guaranteed
summary:
  escalation.py (CI-failure escalations) and plan_health.py (scheduled plan_reconciler/ag-closeout-audit dispatch) grab
  any genuinely idle slot via their own _pick_free_slot without ever checking fleet_worker_cap(). That only worked
  because the cap has historically sat below the total non-review slot count, leaving a few idle by accident — raising
  the cap toward the total slot count would silently erase that headroom and starve time-sensitive work behind a full
  regular-backlog queue. Fixed with an explicit, structural reserve.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, autospawn, fleet-cap, escalation, scheduled-dispatch, starvation]
related: [/plans/active/issues/ci_escalation_wall_type_mismatch_silent_human_only_2026_07_27.md]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
  interactive session, 2026-07-27, agent-orchestrator (ORCHESTRATOR_ESCALATION_SLOT_RESERVE added, _apply_fleet_cap
  clamps the effective cap; QG green including 2 new regression tests, shipped via quickmerge)
locked_by:
supersedes:
superseded_by:
source:
  Operator directive, 2026-07-27, immediately after the fleet-worker-cap raise (8 to 12) — "escalations of ci failures
  and scheduled jobs should override the max slots so that they always can run even if the plan workers are at 12 limit"
  — "fix and implement that in full too."
---

# Escalation + scheduled-dispatch slot starvation — 2026-07-27

## What I found

`server/autospawn.py::_apply_fleet_cap` bounds how many CONCURRENT regular-backlog workers `AutoSpawnLoop` will spawn,
via `fleet_worker_cap()` (`ORCHESTRATOR_FLEET_WORKER_CAP`, just raised operator-side from 8 to 12). Neither
`escalation.py` (CI-failure escalations, `_pick_free_slot`) nor `plan_health.py` (scheduled
`plan_reconciler`/`ag-closeout-audit` dispatch, also `_pick_free_slot`) reference this cap at all — they simply grab any
genuinely idle slot. With 17 total slots and 1 review slot (default), that leaves 16 non-review slots; at cap=8 (the
prior value) that left ~8 idle by arithmetic accident, at cap=12 it leaves ~4. Nothing GUARANTEED that gap stays open —
raising the cap further (or simply running a smaller fleet) could silently consume every slot with regular backlog work,
leaving escalations/scheduled dispatch with nothing to grab.

## The fix

Added `ORCHESTRATOR_ESCALATION_SLOT_RESERVE` (`server/config.py`, default 2) and threaded it into `_apply_fleet_cap`:
the effective cap is now `min(fleet_worker_cap(), total_non_review_slots - reserve)` — but ONLY when `reserve > 0`, so
an explicit `reserve=0` override reproduces the pre-existing arithmetic bit-for-bit (several existing test fixtures
deliberately configure an oversized cap specifically so slot count never gates them; skipping the clamp entirely at
reserve=0 keeps those tests meaningful without touching their assumptions).

Two new regression tests in `tests/test_autospawn.py` cover: (1) a raised-to-the-total cap still leaves the reserve
idle, (2) an explicit `reserve=0` disables the clamp and returns the raw cap unchanged. All existing tests pass
unchanged (5 pre-existing tests using tiny 1-2 slot fixtures now explicitly set `reserve=0`, since they test unrelated
budget arithmetic and predate this concept).

Also applied operator-side: `ORCHESTRATOR_FLEET_WORKER_CAP` raised 8→12 on the live orchestrator VM (`.env.local` +
`systemctl restart orchestrator.service`, verified active post-restart with no regression beyond the already-tracked
TmuxPruner-class transient noise — see `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`).

## Known limitation (not fixed, by design)

A reserve of 2 is a modest guarantee, not an unlimited one. `ag-closeout-audit` can dispatch up to 9 concurrent tranche
workers in its `all` mode — a reserve of 2 does not guarantee all 9 get a slot instantly under heavy regular-backlog
load; that burst may have to wait for slots to free up. That's genuine finite-capacity queuing, not starvation — raising
the reserve further to fully cover a 9-way burst would trade away meaningfully more regular-backlog throughput, a
tradeoff not requested here.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — fleet sizing / AutoSpawn model.
