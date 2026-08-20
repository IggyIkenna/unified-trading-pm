---
doc_type: plan
title: Infra satellite — na-eligibility-audit RECLASSIFY extraction batch (batch 20, single-todo)
summary: >-
  Single-todo extraction from the infra tranche's 2026-08-18 `/na-eligibility-audit` run (dispatch agt-80fafa, slot
  29) — closes the loop on `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`'s
  `launch-defi-forward-poll.sh` consolidator-watchdog-coverage todo, which that doc's own prior same-day
  na-eligibility-audit marker (dispatch agt-6a3d46) tagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` pending a second look.
  Confirmed bounded on this pass: its 3 already-completed sibling watchdog-wiring items (ml_service,
  compound-VM_SERVICE, bespoke `*_daily_cron`) were all resolved without an operator decision once the real launcher
  code was investigated — same "confirm real write target, then wire" shape here, no design fork. Conflict-checked
  clear (see Progress Log).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [infra, ao-dispatch, satellite, batch-20, na-eligibility-audit, plan-hygiene, consolidator-watchdog, close-the-loop]
related:
  [
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "na-eligibility-audit, infra tranche, 2026-08-18 (dispatch agt-80fafa, slot 29) — RECLASSIFY extraction from
    manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md's launch-defi-forward-poll.sh watchdog-
    coverage todo, closing the loop on that doc's own prior-same-day MISCLASSIFIED_LIKELY_AO_ELIGIBLE tag",
  ]
assigned_role: infra
effort: medium
drift_direction: advance-code
context_scope:
  [
    deployment-service/scripts/vm/launch-defi-forward-poll.sh,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
    deployment-service/tests/unit/test_consolidator_watchdog_vm_wiring.py,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
  ]
---

# Infra satellite — `launch-defi-forward-poll.sh` consolidator-watchdog coverage (batch 20, single-todo)

> **Fresh carve-out, single-todo, no finalize twin** (same single-todo carve-out precedent as batch4/batch5/batch19).
> Extracted from `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`'s open
> `launch-defi-forward-poll.sh` watchdog-coverage todo — read that doc's Progress Log (2026-08-16/-17 entries on the
> 3 already-completed sibling watchdog-wiring items) for the proven investigate-then-wire pattern before starting;
> this todo is a pointer + extraction provenance, not a re-derivation.

## Todo

- [ ] [INFRA] P3. **`launch-defi-forward-poll.sh` watchdog coverage** — extracted verbatim from
      `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`'s open todo (newly discovered 2026-08-17
      while resolving that doc's continuous/live watchdog todo): "its `VM_OPERATION` is a variable `--operation`
      flag (default `collect-lst-rates`, seen values likely include other `collect-*` operations), never
      `download`, so it falls through §5b's exact-match gate despite being
      `VM_SERVICE=market_tick_data_service`. Confirm each real `--operation` value's actual write target before
      wiring (same 'confirm real write target' caution as the bespoke `*_daily_cron` launchers)." Follow the same
      investigate-then-wire pattern its 3 completed siblings used (ml_service watchdog wiring, compound-VM_SERVICE
      watchdog coverage, bespoke `*_daily_cron` watchdog coverage — all resolved via direct launcher-code
      investigation, none turned out to be a real judgment call once investigated): read every caller of
      `launch-defi-forward-poll.sh` to enumerate its real `--operation` values, confirm each value's actual GCS
      write target (does it share `market-data-tick-defi` with the already-covered `download` path, or write
      somewhere else — do not assume), then extend `setup-data-pipeline-vm.sh`'s watchdog resolver (§5b/§5c/§5d
      pattern) to export `CONSOLIDATOR_WATCHDOG_BUCKET` for the confirmed target(s), adding test coverage matching
      `test_consolidator_watchdog_vm_wiring.py`'s existing per-family pattern. If any `--operation` value's write
      target turns out to be genuinely ambiguous or undocumented (not just uninvestigated), file it as its own small
      issue doc rather than guessing, and wire whatever values ARE confirmed. Done-when: every real `--operation`
      value used by a live caller of `launch-defi-forward-poll.sh` has an explicit watchdog-wiring disposition
      (wired, or filed as an ambiguous follow-up with reasoning) — `quality-gates.sh`-green, shipped via
      `quickmerge.sh --agent --files`. Flip this todo AND the source doc's own todo in the same commit citing this
      batch's completion evidence. Repos: deployment-service.

## Progress Log

- **na-eligibility-audit 2026-08-18** (infra tranche, dispatch agt-80fafa, slot 29): drafted. RECLASSIFY (per-todo
  split) extraction from `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`'s open
  `launch-defi-forward-poll.sh` watchdog-coverage todo — closing the loop on that doc's own prior same-day
  na-eligibility-audit marker (dispatch agt-6a3d46), which tagged this item `MISCLASSIFIED_LIKELY_AO_ELIGIBLE`
  pending a second look once its boundedness could be confirmed (per SKILL.md's "close the loop" rule — a tag from a
  prior run is a mandatory Phase-1 input on the next run, not a dead end). Confirmed bounded on this pass: the 3
  sibling watchdog-wiring items (ml_service, compound-VM_SERVICE, bespoke `*_daily_cron`) were ALL resolved without
  an operator decision once the actual launcher code was investigated — this item's own framing carries the
  identical "confirm real write target, then wire" shape, no design fork evident in the source doc's own text.
  **Conflict-check (clear)**: grepped every active `assigned_vm: planning` doc in `parent_epic: infrastructure_master`
  for `defi-forward-poll`/`defi_forward_poll` — 2 hits, both non-overlapping: `data_completion_to_100_all_ag_2026_06_21.md`
  is about running/deploying the live forward-poll VM itself (2026-06-21, scheduler cadence, data backfill), not
  consolidator-watchdog wiring; `infra_satellite_ao_dispatch_batch17_2026_08_16.md` fixed an unrelated, already-shipped
  duplicated-`lc_verify_tarball_freshness`-block/stale-dry-run-string bug in the same script file — different claim,
  no overlap with this todo's actual scope. No `status: draft` legacy satellite doc references it either. First
  dispatch of this item.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
