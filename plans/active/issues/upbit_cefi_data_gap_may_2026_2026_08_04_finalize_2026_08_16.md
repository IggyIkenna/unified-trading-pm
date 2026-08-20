---
doc_type: issue
title: upbit_cefi_data_gap_may_2026_2026_08_04 — finalize
summary: >-
  Gated closeout for the 2026-08-16 na-eligibility-audit retroactive reclassification (NA -> planning) of
  upbit_cefi_data_gap_may_2026_2026_08_04.md. The 2026-08-16 audit pass falsified the doc's prior credential-gap
  premise by direct measurement and rewrote its sole open todo as a bounded config+relaunch+verify action; this
  finalize plan verifies the relaunch actually closed the gap (not just that a VM was started) and separately makes
  sure the newly-found silent-stall data-correctness flag does not evaporate if this todo alone resolves it.
status: open
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, reclassification, na-audit, finalize, data-correctness]
related:
  [/plans/active/issues/upbit_cefi_data_gap_may_2026_2026_08_04.md]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
effort: low
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [upbit_cefi_data_gap_may_2026_2026_08_04]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/issues/upbit_cefi_data_gap_may_2026_2026_08_04.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  by the cefi-tranche /na-eligibility-audit run (autonomous, dispatch agt-e26aea) in the same turn as the
  RECLASSIFY_WHOLE_DOC flip it finalizes. Priority kept at P1 (matching the source doc) because this closes a
  codex-MVP-venue data gap, not routine plan hygiene.
---

# upbit_cefi_data_gap_may_2026_2026_08_04 — finalize

> **Machine-gated on `/plans/active/issues/upbit_cefi_data_gap_may_2026_2026_08_04.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until that doc's relaunch todo is `done`.

## Todos

- [ ] [REVIEW] P1. Once the UPBIT relaunch todo in `upbit_cefi_data_gap_may_2026_2026_08_04.md` is `[x]`, verify the
      cited done-when for real: query live GCS (`raw_tick_data/by_date/.../venue=UPBIT/`) and confirm ≥3 consecutive
      recent days show trade+book_snapshot_5 object counts matching the historical ~600-608/day shape — not just that
      a VM was launched. Also confirm whether the relaunch correctly resumed from 2026-06-02 (accounting for the
      already-captured 2026-05-25/05-26/06-01 partial catch-up the 2026-08-16 audit found) rather than re-doing
      already-captured dates. Done when: the GCS query result (dates + object counts) is cited as evidence, not just
      a VM-launched claim.
- [ ] [REVIEW] P1. Independent of todo 1's resolution, confirm the 2026-08-16-flagged silent-stall mechanism (the
      undocumented 2026-08-06/07 partial catch-up that then re-stalled with zero alert/Progress-Log trace) has been
      diagnosed — check whether the VM that performed the partial catch-up crashed, was preempted without recovery,
      or was manually stopped, and whether `uts-prod-dp-heartbeat-watcher`/`uts-prod-dp-exit-code-monitor` should have
      paged on it and didn't. If the root cause is a genuine monitoring/alerting gap (not just this one VM's bad
      luck), file it as its own issue doc rather than letting it close silently alongside todo 1 — this is a
      distinct data-pipeline-correctness finding per `/codex/02-data/data-pipeline-correctness-hard-rule.md`, not
      merely a housekeeping detail of the UPBIT fix. Done when: either a root cause is cited, or a fresh issue doc
      tracks the open monitoring-gap question.
- [ ] [REVIEW] P2. Once both todos above are satisfied, run the standard 6-step archival ritual on
      `upbit_cefi_data_gap_may_2026_2026_08_04.md` (dated destination is flat `plans/archive/issues/` per its
      `doc_type: issue`) and archive this finalize plan alongside it. Done when: both docs are under
      `plans/archive/`, and `regenerate_active_plan_inventory.py` reports zero orphan referrers to either.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
