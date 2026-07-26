---
doc_type: plan
title: CeFi Track-2 coverage backfill — resume + MID/POST checkpoints
summary: >-
  Resumes the CeFi Tardis COVERAGE backfill (reversing the archived "honest-done 50.79%" verdict — the throughput
  ceiling was a ~350x code bug, now fixed and measured live) and brackets it with the MID/POST
  `data-pipeline-check-is`/`data-pipeline-check-mtds` checkpoints. Forked from
  cefi_consolidated_closeout_2026_07_18.md's Track 2 (2026-07-25 split). Gated on
  cefi_migration_cutover_and_track8_completion_2026_07_25.md finishing (launching before the Track-1 drain re-enables
  would fight the consolidator). The 2 PRE-BACKFILL baseline checkpoints are deliberately NOT here — already drafted,
  ungated, as candidates 3/4 of cefi_consolidated_native_ao_extract_2026_07_25.md.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, coverage, backfill, track-2, checkpoint]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_migration_cutover_and_track8_completion_2026_07_25]
gate_on_depends: true
source: >-
  Forked from cefi_consolidated_closeout_2026_07_18.md's Track 2 ("CeFi backfill COVERAGE reopened") + its checkpoint
  cadence subsection, 2026-07-25 split — path 2 of that parent's 4 reachability paths, the coverage-backfill path. The
  "Launch AFTER the Track-1 Phase-D re-enable" ordering constraint (previously prose-only in the parent) is now a real
  machine gate via depends_on + gate_on_depends.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi Track-2 coverage backfill — resume + checkpoints

> **Machine-gated on `cefi_migration_cutover_and_track8_completion_2026_07_25.md`** (`depends_on` +
> `gate_on_depends: true`) — none of this plan's todos dispatch until every task in that plan is `done`. This makes the
> parent's previously prose-only "Launch AFTER the Track-1 Phase-D re-enable (else the drain kills it)" constraint a
> real dispatcher-enforced gate. **`sequential: true`**: the backfill must actually launch before either MID checkpoint
> is meaningful, and both MID checkpoints logically precede both POST checkpoints — this plan's own 5 todos are a single
> temporal chain. **Ruling context**: the archived "honest-done 50.79%" verdict rested on a ~350x code-bug throughput
> collapse (`run_in_executor(None,…)` default-pool + a date-serial barrier), not a physical Tardis ceiling — the bug is
> now fixed and measured live @~14 MB/s, and the 2.89M-cell gap is ~1-2 days of work at June rates (autonomous ruling,
> 2026-07-18, within documented intent — operator can reverse; see `cefi_consolidated_closeout_2026_07_18.md`'s Headline
> verdict + Track 2 for the full ruling record). Companion gated finalize:
> `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`.

## Todos

- [ ] [DATA] P1. **Resume the cefi Tardis COVERAGE backfill on the fixed code.** **N=1 Tardis cap, both clouds** — count
      the live fleet with `tardis-concurrency-guard.sh` FIRST; scale on the one IP via `SINGLE_VM_QUEUE=1` +
      `TARDIS_MAX_CONCURRENT_DOWNLOADS`, NEVER more VMs. SPOT (idempotent backfill — preemption-safe per the
      PROGRESS-checkpoint contract). Repos: deployment-service, market-tick-data-service. **Done when**: the backfill VM
      is launched, confirmed running (progress climbing on 2+ successive checks, not flat), and the N=1 concurrency
      guard is confirmed satisfied throughout the launch.
- [ ] [DATA] P1. **Run `/data-pipeline-check-is` for cefi as the MID-BACKFILL SPOT-CHECK**, partway through the coverage
      backfill launched in the todo above. Repo: instruments-service (skill run, no code change). **Done when**: the
      skill's report path + run date is cited in this plan's Progress Log.
- [ ] [DATA] P1. **Run `/data-pipeline-check-mtds` for cefi as the MID-BACKFILL SPOT-CHECK**, partway through the
      coverage backfill launched above (a real dated run, distinct from any prior skill-upgrade-only todo). Repo:
      market-tick-data-service (skill run, no code change). **Done when**: the skill's report path + run date is cited
      in this plan's Progress Log.
- [ ] [DATA] P1. **Run `/data-pipeline-check-is` for cefi as the POST-BACKFILL FINAL GATE**, after the coverage backfill
      completes. Repo: instruments-service (skill run, no code change). **Done when**: the report path + run date, plus
      a PASS verdict for every MVP (asset_group, venue) shard, is cited in this plan's Progress Log.
- [ ] [DATA] P1. **Run `/data-pipeline-check-mtds` for cefi as the POST-BACKFILL FINAL GATE**, after the coverage
      backfill completes; re-measure coverage and supersede the archived 50.79% with the new number. Repo:
      market-tick-data-service (skill run, no code change). **Done when**: the report path + run date, a PASS verdict (0
      false `attempted_failed`, every MVP shard genuinely captured-vs-skipped), and the new coverage % are all cited in
      this plan's Progress Log and in `cefi_consolidated_closeout_2026_07_18.md`'s Track 2.

## Reconciliation

Once this plan's todos ship, flip Track 2's resume-backfill checkbox and the 4 MID/POST checkpoint checkboxes in
`cefi_consolidated_closeout_2026_07_18.md`, citing this plan's evidence (report paths, run dates, the new coverage %).
Gated via the companion `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`
(`depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]` — `gate_on_depends: true`).

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md` (Tardis cap + the throughput-fix ruling),
`/codex/02-data/availability-manifest-and-data-status.md`. No new durable contract is created by this plan — every todo
executes an already-decided spec from the parent doc.
