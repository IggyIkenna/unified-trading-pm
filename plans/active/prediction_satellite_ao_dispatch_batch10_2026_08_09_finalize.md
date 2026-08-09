---
doc_type: plan
title: Prediction satellite AO batch 10 — finalize (verify evidence + operator handoff + archive)
summary: >-
  Gated closeout for `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until that plan's todos are done. Re-verifies Deferral (b)'s shipped evidence, confirms
  Deferral (a)'s operator handoff was actually posted (that todo's own "done" is a walk-plan + handoff, not the
  `--apply` itself — this finalize does NOT wait on a human to run the apply, only on the agent-side prep landing), then
  runs the standard archival ritual.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer, admin]
tags: [prediction, ao-dispatch, close-out, batch-10, archival]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_satellite_ao_dispatch_batch10_2026_08_09]
gate_on_depends: true
sequential: true
source: >-
  Paired finalize for prediction_satellite_ao_dispatch_batch10_2026_08_09 per task_template.md §4 finalize-plan-coverage
  rule; drafted alongside the parent per the operator's BLK-0d9d2799 ruling, 2026-08-09.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Prediction satellite AO batch 10 — finalize

> **Machine-gated on `prediction_satellite_ao_dispatch_batch10_2026_08_09.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until both todos in that plan are `done`. **Note on Deferral (a)'s
> "done"**: that todo's own done-when is a re-measured walk-plan + a posted `[OPERATOR]` handoff — NOT the actual
> `--apply` (permanent human-only per workspace policy). This finalize gates on the AGENT-SIDE prep landing, not on a
> human executing the walk.

## Todos

- [ ] [REVIEW] P2. **Verify Deferral (b)'s shipped evidence.** Confirm the cited `<repo>@<sha>` for the POLYMARKET
      re-enum + `book_snapshot_5` backfill is a real ancestor of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor`), and that the cited row-count evidence is independently reproducible (re-run the
      same count query, don't just trust the citation). **Done when**: an independently-reverified evidence line is
      recorded, or the todo is reopened with the discrepancy stated if evidence doesn't hold up. Repo:
      market-tick-data-service.

- [ ] [REVIEW] P3. **Confirm Deferral (a)'s operator handoff actually landed.** Check the parent plan's Deferral (a)
      Progress Log for: re-measured live counts (not the 2026-08-07 stale ones), a written walk-plan (which rows, target
      canonical shape), and a posted `[OPERATOR]` handoff (dashboard escalation or equivalent). **Done when**: all three
      are confirmed present with citations, or the todo is reopened naming what's missing. This does NOT require the
      human `--apply` to have run — only that the agent-side prep is complete and handed off. Repo: unified-trading-pm.

- [ ] [DOCS] P3. **Archive the parent plan per the 6-step ritual, but ONLY the archivable parts.** Deferral (a) may
      legitimately stay open indefinitely pending human execution — that is not a blocker for archiving THIS batch doc
      if (a)'s agent-side prep is done and handed off (per the todo above) and (b) is genuinely shipped. In order: (1)
      confirm Deferral (b) is `[x]` with verified evidence and Deferral (a)'s prep+handoff is confirmed (both todos
      above done); (2) if Deferral (a) itself is still open pending human execution, do NOT block archival on it —
      instead migrate it to a durable operator-tracking home (e.g. a dedicated `plans/active/issues/<slug>.md` or the
      standing manifest-delete-safety operator queue, per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "MIGRATED FROM" convention) so the
      permanent-hard-stop item isn't lost when this batch archives; (3) add the archival banner + set `status: complete`
      on the batch doc itself once its own scope (both todos) is done or migrated; (4) confirm no codex doc needs an
      update; (5) update every referrer's path corpus-wide (grep `prediction_satellite_ao_dispatch_batch10_2026_08_09`
      and repoint each hit); (6) clear the lock if any was set; (7) run
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` to confirm no new dangling reference above
      baseline. Then physically move the parent plan under `plans/archive/2026_08/`. **Done when**: the hygiene sweep is
      0 hard and `regenerate_active_plan_inventory.py` reports 0 orphans for this doc, AND Deferral (a)'s
      permanent-hard-stop status has a durable home if it wasn't fully executed. Repo: unified-trading-pm.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual + the "MIGRATED
  FROM" convention for genuinely-still-open work that shouldn't block a doc's archival.

## Progress Log

- 2026-08-09 (slot 13, plan_reconciler, dispatch agt-c3a27f): drafted alongside the parent batch, same session, per the
  operator's `BLK-0d9d2799` ruling. `status: active` immediately (no-double-gate precedent — `gate_on_depends`
  machine-holds every todo above until the parent's 2 todos land).
