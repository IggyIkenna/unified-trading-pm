---
doc_type: plan
title: Sports taxonomy P4 — backfill the derived layer to the 2020-06 floor and dispose of the pre-floor corpus
summary: >-
  Phase 4 of the sports canonicalisation chain — closing the coverage gap the 2026-08-08 audit measured. The sports
  derived layer covers 13 of ~2,250 days: `odds_snapshot` (16,521), `odds_movement` (16,470) and `arbitrage_opportunity`
  (16,441) all exist ONLY for 2026-07-25 to 2026-08-06, against six years of raw odds from the 2020-06-06 floor. It was
  never backfilled. This phase runs that backfill on SPOT VMs in-region against the FINAL post-migration contracts
  (which is why it is gated rather than run now — backfilling 2,250 days pre-migration and re-doing it after would be
  pure waste), and disposes of the 10,345-object pre-launch C3 corpus per the already- standing 2020-06 floor ruling
  rather than re-opening it as a fresh decision.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [sports, backfill, derived-layer, honest-coverage, data-floor, spot-vm, coverage-denominator]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 7
estimate_calibrated_ai_days: 5.6
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p2_migration_2026_08_08]
gate_on_depends: true
context_scope:
  [
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/02-data/honest-coverage-model.md,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — 27 operator rulings"]
locked_by:
locked_since:
---

# Sports taxonomy P4 — derived-layer backfill

> Gated on P2's migration (`gate_on_depends: true`). Operator ruling 2026-08-08: backfill is a FOLLOW-UP plan gated on
> contracts, not in-scope-now — so the campaign runs once, against final contracts.

## The gap (measured 2026-08-07/08, live prod manifest)

| data_type                 | captured | date span present       | days covered |
| ------------------------- | -------- | ----------------------- | ------------ |
| `odds` (raw, ex-`trades`) | 375,257  | 2020-06-06 → 2026-07-26 | ~2,250       |
| `odds_horizon_bucket`     | 135,980  | 2020-06-06 → 2026-08-06 | ~2,250       |
| `odds_snapshot`           | 16,521   | **2026-07-25 → 08-06**  | **13**       |
| `odds_movement`           | 16,470   | **2026-07-25 → 08-06**  | **13**       |
| `arbitrage_opportunity`   | 16,441   | **2026-07-25 → 08-06**  | **13**       |

For CLV training this means opening/closing-line features exist for 13 days of a six-year history — the single largest
constraint on the sports ML work.

## The C3 pre-launch corpus is NOT an open question

`/plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md`'s sole open todo offers a choice: extend
`SOURCE_COVERAGE_START["footystats"]` 2019→2018 (plus api_football sub-entity windows) and re-backfill 10,345 objects,
OR ratify the corpus as permanently outside-window. **That choice was already made.**
`/codex/02-data/sports-2020-06-data-floor.md` (operator ruling 2026-07-21) explicitly supersedes the 2018 amendment:
_"all sports `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` floors are clamped to `date(2020, 6, 6)`"_
(`unified-api-contracts@8cdf7808`), and pre-floor sports data is fabrication-by-construction — **delete, do not
backfill**. Confirmed by the operator 2026-08-08. The todo is stale, not open.

---

## Todos

- [ ] [SCRIPT] P0. **Size the backfill before launching it.** Compute shard-days needed per derived type across
      2020-06-06 → present against the FINAL post-migration axes, and project runtime + SPOT cost + parallelisation
      headroom. A backfill launched without a projected terminal state cannot be told apart from a stalled one.
- [ ] [SCRIPT] P0. **Backfill `odds_snapshot` to the 2020-06-06 floor** on SPOT VMs, in-region, per the VM-launcher
      runbook. Never run this locally. Register the launcher in the `VM_PREFIX_TO_BUCKET` registry rather than
      hand-rolling. Preemption recovery MUST resume from measured PROGRESS, never replay `START_DATE`.
- [ ] [SCRIPT] P0. **Backfill `odds_movement` to the floor**, same discipline. May run concurrently with `odds_snapshot`
      — different output shards, so no same-file overlap.
- [ ] [SCRIPT] P1. **Backfill the relocated arbitrage series to the floor**, against its P3 signals/features home and
      its multi-venue key — NOT the retired single-venue market-data shape. Must consume the corrected operator-group
      guard, so no all-one-operator "arb" enters the historical series.
- [ ] [SCRIPT] P1. **Backfill the `horizon` axis across the full history**, including the newly-promoted MODEL horizons
      T-2h and T-6h (P3), so the ML retrain has them over the whole period rather than only where they happen to exist
      today.
- [ ] [DATA] P1. **Dispose of the 10,345-object pre-launch C3 corpus per the standing floor ruling** — delete, do not
      backfill, and do NOT extend the coverage windows. Runs agent-autonomously via delete-safety §3a: a FRESH, same-run
      `gcs_bucket_soft_delete_retention_seconds()` >= 604800 check before any object delete; if the check fails, stop
      and say so rather than proceeding. Close out
      `/plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md` by citing this ruling.
- [ ] [REVIEW] P0. **Monitor on a PROGRESS metric, not activity.** Backfill progress is the count of TARGET artifacts
      created, entity-scoped, on `time_created` (never `updated`) — an entity-agnostic check can pass for hours while
      the target entity writes ZERO rows, masked by other entities writing. Arm an owned `run_in_background` heartbeat
      watchdog (<=30 min) in the SAME turn as the launch; a dispatched sub-agent is not a reliable wake.
- [ ] [REVIEW] P1. **Run `/vm-preemption-billing-waste-audit` over the campaign** — check for SPOT preemption without
      recovery, and for structurally non-retriable `attempted_failed` shards being re-attempted on every wave.
- [ ] [REVIEW] P0. **Terminal honest-coverage verdict.** After the campaign, every derived type reaches the floor with
      only `captured` / `empty_confirmed` — no `attempted_failed`, no `expected_unattempted` left unreconciled. This is
      the convergence bar `/plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` sets for
      sports; cite that doc and flip its state rather than duplicating its tracking.

## Codex SSOTs

- `/codex/02-data/sports-2020-06-data-floor.md` — the floor; governs both the backfill window and the C3 disposition.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — heavy I/O never local; no fire-and-forget; registry-named
  launchers.
- `/codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT default + progress-checkpoint resume.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — progress-metric monitoring, owned watchdog.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — §3a governs the C3 delete.

## Progress Log

- **2026-08-08** — Authored. Coverage gap measured against the live prod manifest. C3 disposition recorded as an
  ALREADY-RULED item (2026-07-21 floor ruling) rather than a fresh operator decision — the source todo is stale.
