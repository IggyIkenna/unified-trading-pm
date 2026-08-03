---
doc_type: issue
title: >-
  Sports manifest 2026-vs-2025 per-data_type cell-seeding ratio still 2.2x-16.6x (not resolved) — root cause is the v2
  expected_unattempted enumerator's static 120-day bounded window (start_date=2026-02-20, never bumped), not the
  originally-diagnosed Cause A over-seeding
summary: >-
  Re-measured (2026-07-27) whether the 2026-06-23-diagnosed "~10x-class" 2026-vs-prior-year sports manifest
  enumeration-grain inconsistency still persists, per `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s DIAG todo.
  Read the live `instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` manifest ONCE
  (6,847,192 rows, single read, columns projected to `date`/`data_type`/`capture_status`/`league_id`/`source` only) and
  counted total manifest rows ("cells seeded", every capture_status) per `data_type` for a matched H1 window (2025-01-01
  to 2025-06-30 vs 2026-01-01 to 2026-06-30). RESULT: the inconsistency has NOT resolved to ~1x. Overall H1 ratio is
  3.13x (363,842 -> 1,137,706 cells); per-data_type ratios range 2.2x-3.6x for the great majority of data_types, with 3
  outliers — `FIXTURES` 16.6x (3,264 -> 54,045), `FIXTURES_OUTCOMES` 15.7x (3,444 -> 54,154), `ODDS` 6.0x (8,765 ->
  52,754). ROOT CAUSE (verified by code read, not the originally-diagnosed Cause A): every 2025 H1 sample shows ZERO
  `capture_status=expected_unattempted` rows for every data_type checked (FIXTURES/FIXTURES_OUTCOMES/ODDS/WEATHER/
  MATCHES all 100% `captured`+`empty_confirmed` in 2025), while 2026 H1 rows are a genuine 3-way split including a large
  `expected_unattempted` share (e.g. FIXTURES 2026: 37,693 expected_unattempted + 9,937 empty_confirmed + 6,415
  captured). This is exactly the behavior of `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`'s
  documented "bounded recent window" design (lines 29-33, 68-71): the v2 enumerator's `--start-date` is
  `var.expected_universe_start_date`, a Terraform variable with a STATIC default `"2026-02-20"` and no override anywhere
  in `terraform/` (grepped) — the file's own comment says the window "slides forward each day" but that is
  aspirational/conceptual, not implemented; nothing re-derives or bumps the literal default without a fresh `terraform
  apply` changing it. Since all of 2025-01-01..2025-06-30 falls entirely BEFORE the frozen 2026-02-20 window start, the
  v2 enumerator structurally NEVER seeds `expected_unattempted` cells for 2025 dates — the 2025 denominator is missing
  an entire capture_status class by design, not because 2026 is over-seeded. The `FIXTURES`/`FIXTURES_OUTCOMES`/`ODDS`
  outlier ratios additionally reflect real league-universe growth (distinct `league_id` count: FIXTURES 88 -> 924,
  FIXTURES_OUTCOMES 88 -> 926, ODDS 51 -> 384, vs a flatter ~94->388 for WEATHER/MATCHES), which may be legitimate
  coverage expansion, a duplicate-seeding artifact, or a mix — NOT independently verified in this todo's read-only
  scope. Practical implication: any coverage-% comparison across the 2026-02-20 boundary (e.g. "is 2025 completion %
  better/worse than 2026") is comparing two different denominator regimes and will read as artificially inflated
  coverage for pre-2026-02-20 dates purely because those dates never got the could-exist universe seeded. This is a
  SPORTS-SCOPED re-verification only — cefi/defi/tradfi/prediction use the SAME scheduler + the SAME static-default
  pattern (`expected_universe_v2_asset_groups` in the same .tf file) and were NOT re-measured here.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, manifest, expected-unattempted, honest-coverage, enumeration-grain, bounded-window, data-completeness]
related:
  [
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
context_scope:
  [
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf,
    instruments-service/scripts/sports_manifest_enumeration_grain_check_2026_07_27.py,
  ]
resolved_by:
source: >-
  sports_satellite_ao_dispatch_batch3_2026_07_25.md's "[DIAG] P1. Verify whether the sports manifest's
  2026-vs-prior-year enumeration-grain inconsistency ... still persists" todo (source of THAT todo:
  data_completion_sports_2026_07_24.md's 2026-06-23 "concentrated in 2026-H1 (~120k/data_type vs ~8-30k/prior-year)"
  finding).
depends_on: []
---

# Sports manifest 2026-vs-2025 cell-seeding ratio still 2.2x-16.6x — driven by the v2 enumerator's static bounded window, not Cause A

## What I found

Ran `instruments-service/scripts/sports_manifest_enumeration_grain_check_2026_07_27.py` (read-only, single download of
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 6,847,192 rows, 136MB)
against the live prod manifest, grouping total row counts ("cells seeded" — every `capture_status`, not just `captured`)
by `data_type` for two matched H1 windows: `2025-01-01..2025-06-30` and `2026-01-01..2026-06-30`.

**Overall**: 363,842 cells (2025 H1) -> 1,137,706 cells (2026 H1) = **3.13x**.

**Per-data_type** (full 30-row table in the script's JSON output): the majority of data_types (FIXTURES_SCHEDULE,
FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, INJURIES, MATCHES, PLAYER_STATS, PLAYER_VALUES, PREDICTIONS,
SFI_PROGRESSIVE_STATS, STANDINGS, WEATHER, XG, XG_SHOTS, TEAMS) cluster tightly around **2.4x-3.6x**. Three data_types
are well outside that band:

| data_type         | 2025 H1 | 2026 H1 | ratio  |
| ----------------- | ------- | ------- | ------ |
| FIXTURES          | 3,264   | 54,045  | 16.56x |
| FIXTURES_OUTCOMES | 3,444   | 54,154  | 15.72x |
| ODDS              | 8,765   | 52,754  | 6.02x  |

A handful of small-count catalogue-style data_types (LEAGUES, VENUES, SFI_LEAGUES, TRANSFERMARKT_LEAGUES, SFI_STANDINGS)
show ratios <1 (shrinking, consistent with the 2026-06-23 B1 retired-data_type reclassification program already having
run against those).

### Root cause (verified by code read + a targeted follow-up query, not re-derived from the retracted 2026-06-23 diagnosis)

A follow-up query (distinct `league_id`/`source` counts + `capture_status` breakdown per window) on
FIXTURES/FIXTURES_OUTCOMES/ODDS/WEATHER/MATCHES showed:

- **Every 2025 H1 row, for every data_type checked, is `capture_status` in `{captured, empty_confirmed}` only — ZERO
  `expected_unattempted` rows.** E.g. FIXTURES 2025: `{'captured': 3264}` (100%). WEATHER 2025:
  `{'empty_confirmed': 16220, 'captured': 975}`.
- **2026 H1 rows carry a real 3-way (sometimes 4-way) split including a large `expected_unattempted` share.** E.g.
  FIXTURES 2026: `{'expected_unattempted': 37693, 'empty_confirmed': 9937, 'captured': 6415}` — 70% of the 2026 FIXTURES
  total is `expected_unattempted` alone, a state that is entirely absent from the 2025 sample.

This matches `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf` exactly: the v2 enumerator
(`instruments-service/scripts/enumerate_expected_universe.py --enumerator-version v2 --apply-write`) is invoked daily
(01:30 UTC) with `--start-date var.expected_universe_start_date` (line 153). That variable (lines 68-71) declares:

```
variable "expected_universe_start_date" {
  description = "Bounded recent window start (YYYY-MM-DD) for the v2 expected_unattempted enumeration. ..."
  type        = string
  default     = "2026-02-20" # ~120 days before the 2026-06-19 wiring; slides forward conceptually each rebuild
}
```

`grep -rn expected_universe_start_date terraform/` finds only this one declaration and its one usage — **no `.tfvars` or
module call overrides it**, so the live value is the static literal `"2026-02-20"`. The comment's "slides forward
conceptually each rebuild" is describing an _intent_ (re-running `terraform apply` with a bumped default periodically
would slide it), not a live/automatic mechanism — nothing in this repo recomputes the default from `today() - 120d`.
Since the entire 2025-01-01..2025-06-30 window is chronologically before 2026-02-20, the v2 enumerator has, by this
design, **never had a --start-date that reaches back into 2025** — those dates structurally cannot receive
`expected_unattempted` seeding regardless of any other fix. This is a DIFFERENT mechanism from the originally-diagnosed
"Cause A" (out-of-scope league x source cells wrongly seeded as `expected_unattempted` instead of
`EXPECTED_NO_PROVIDER_COVERAGE`, fixed 2026-06-23 by instruments-service@0bcf727) — that fix governs how a cell is
CLASSIFIED once it's inside the enumerator's window; it does not touch WHICH dates are inside the window at all.

**FIXTURES/FIXTURES_OUTCOMES/ODDS' extra elevation above the ~3x baseline** additionally correlates with much larger
distinct-`league_id` growth than the other data_types: FIXTURES 88 -> 924 leagues (10.5x), FIXTURES_OUTCOMES 88 -> 926
(10.5x), ODDS 51 -> 384 (7.5x; ODDS also gained a second `source` in 2026, was 1 in 2025), vs a flatter ~94 -> 388
(4.1x) for WEATHER and 102 -> 406 (4.0x) for MATCHES. Whether this specific league-count delta is a genuine coverage
expansion (more leagues actually being tracked in 2026), a duplicate/near-duplicate league_id seeding artifact specific
to those 3 data_types, or some mix, was **not** independently investigated — flagged as an open question for the
follow-up todo below rather than guessed at.

## Why it matters

Any comparison of sports honest-coverage % across the 2026-02-20 boundary (e.g. "is coverage improving/degrading
year-over-year") is silently comparing two different denominator regimes: pre-2026-02-20 dates have a systematically
UNDER-seeded denominator (missing the entire `expected_unattempted` class), which will read as inflated coverage % for
older dates purely as a measurement artifact, not real data quality. The `data_completion_sports_2026_07_24.md`
2026-06-23 diagnosis's own "~120k/data_type vs ~8-30k/prior-year, concentrated in 2026-H1" language already named the
symptom; this re-verification confirms it is still live today (2026-07-27) and pins the mechanism precisely to the
static Terraform default rather than to the Cause A bug that plan believed was the (now-fixed) explanation.

## Recommended decision

No code fix implemented in this todo (per its own scope — DIAG/investigation only). Two independent follow-ups, left for
operator/plan triage rather than actioned here. Neither is a data-correctness emergency (no phantom/mislabeled captured
data — every affected row is an honest `expected_unattempted`/`empty_confirmed`/`captured` state, just asymmetrically
distributed by date) — both are P2/P3-appropriate follow-ups, not a foundation-gate freeze trigger.

- [x] [OPERATOR] P2. Decide whether `expected_universe_v2_scheduler.tf`'s `expected_universe_start_date` (currently a
      static, never-overridden default `"2026-02-20"`, verified via `grep -rn expected_universe_start_date terraform/`
      finding only the one declaration) should be widened/refreshed (e.g. to a genuinely rolling `today - 120d`, or a
      much earlier fixed floor if a wider historical `expected_unattempted` denominator is wanted for pre-2026-02-20
      honest-coverage comparisons). This is a resourcing tradeoff — the .tf file's own comment cites an unbounded
      full-history v2 universe as ~190M rows fleet-wide, "tracked as a gated follow-up, NOT materialised by this
      recurring job" — so it needs an explicit operator call, not a silent default. Same static-default pattern likely
      affects cefi/defi/tradfi/prediction too (same `expected_universe_v2_asset_groups` map, same `.tf` file) — NOT
      independently re-measured for those AGs by this sports-scoped todo. (repo: deployment-service)

  > **RESOLVED — operator ruling 2026-07-27** (main agt-4d8de7 msg 2440/2441). Two distinct jobs, per operator's own
  > 2020-06 sports data-floor ruling (`/codex/02-data/sports-2020-06-data-floor.md`, which makes 2020-06-06 the base
  > month for ALL sports honest-coverage denominators AND fixture expectations — the `expected_unattempted` universe IS
  > the fixture-expectation denominator):
  >
  > 1. **Recurring scheduler** → flip `expected_universe_start_date` from the static `"2026-02-20"` to a genuinely
  >    rolling `today - 120d`. Cheap, matches the .tf's documented "slides forward each day" intent, stops the forward
  >    seeding artifact. This is the operator's pick for the ongoing job.
  > 2. **One-time historical denominator** → floor at **2020-06-06** (the sports data floor), NOT 2026. Running the
  >    historical `expected_unattempted` backfill from just 2026 would reproduce this exact artifact one boundary over
  >    (2020-06..2025 would still carry ZERO `expected_unattempted`, so their honest-coverage % keeps reading
  >    artificially inflated). This is the gated follow-up the .tf comment flags (~190M rows fleet-wide; the
  >    sports-scoped subset is smaller) — a deliberate gated backfill, separate from the cheap recurring window.

- [ ] [SCRIPT] P2. Implement job (1): flip `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`'s
      `expected_universe_start_date` from the static default `"2026-02-20"` to a genuinely rolling `today - 120d`
      (computed at plan/apply time, not a frozen literal — the current default never bumps without a fresh
      `terraform apply`). Verify the recurring v2 enumerator then seeds `expected_unattempted` for the trailing 120-day
      window on every run. Keep the sports-scoped change minimal; the same-pattern cefi/defi/tradfi/prediction AGs are a
      separate follow-up (see below). (repo: deployment-service)
- [ ] [DATA] P2. Implement job (2): the gated one-time historical `expected_unattempted` denominator backfill floored at
      **2020-06-06** (sports). Gated + resource-bounded (heavy — run on a VM per the heavy-I/O rule, never locally);
      scope to sports first. Done-when: 2020-06-06..present sports dates carry a seeded `expected_unattempted` universe
      so cross-year honest-coverage comparisons share one denominator regime. (repo: deployment-service)
- [ ] [DATA] P3. Re-measure the same static-default `expected_universe_start_date` pattern for
      cefi/defi/tradfi/prediction (same `expected_universe_v2_asset_groups` map, same `.tf`) — NOT covered by this
      sports-scoped issue; likely the same boundary artifact. Read-only measurement first; widen/backfill per the same
      two-job model if confirmed. (repo: deployment-service)
- [ ] [DATA] P3. Investigate the FIXTURES/FIXTURES_OUTCOMES/ODDS-specific distinct-`league_id` growth (88->924, 88->926,
      51->384 respectively vs the ~4x baseline other sports data_types show, e.g. WEATHER 94->388, MATCHES 102->406) to
      determine whether it is genuine coverage expansion (more leagues legitimately tracked in 2026) or a
      duplicate/near-duplicate league_id seeding artifact isolated to those 3 data_types. Read-only classification; no
      manifest write. (repo: instruments-service)
