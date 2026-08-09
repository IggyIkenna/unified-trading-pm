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
author: unknown
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: advance-code
sequential: true
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

> **🟡 IN-FLIGHT 2026-08-08 ~03:01 UTC — slot-3 running in tmux `orch-slot-3:backfill` (harness-kill-proof). Rolling
> boundary 2026-04-10 (7 chunks: 2020-06-06..2026-04-09). Chunk 1/7 VM `expected-universe-v2-sports-20260808-030132`
> RUNNING (2020-06-06..2020-12-31). Prior state: chunk 1 previously EXIT_STATUS=0, chunk 2 partial (~8M rows across 2
> prior-session VMs 024458+025019 both EXIT_STATUS=5), chunks 3-7 not started. LC_TARBALL_FRESHNESS=warn (UTL tarball
> slightly stale but benign — all critical fixes in DS+IS tarballs which are current). Resume:
> `tmux capture-pane -t "orch-slot-3:backfill" -p -S -20` or
> `gcloud compute instances list --filter='name~"expected-universe-v2-sports"'`. If tmux window gone: re-run
> `tmux new-window -t orch-slot-3 -n backfill && tmux send-keys -t orch-slot-3:backfill "cd /home/ubuntu/unified-trading-system-repos/.tabs/3/deployment-service && LC_TARBALL_FRESHNESS=warn bash scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh sports 2>&1 | tee /tmp/backfill-slot3.log" Enter`.**

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

- [x] ✅ [SCRIPT] P2. Implement job (1): flip `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`'s
      `expected_universe_start_date` from the static default `"2026-02-20"` to a genuinely rolling `today - 120d`
      (computed at plan/apply time, not a frozen literal — the current default never bumps without a fresh
      `terraform apply`). Verify the recurring v2 enumerator then seeds `expected_unattempted` for the trailing 120-day
      window on every run. Keep the sports-scoped change minimal; the same-pattern cefi/defi/tradfi/prediction AGs are a
      separate follow-up (see below). (repo: deployment-service) — deployment-service@1d8ede9. `timestamp()`/
      `formatdate()` aren't allowed inside a variable's own `default` (Terraform requires plan-time-constant variable
      defaults — confirmed via an isolated sandbox `terraform validate`), so the rolling computation moved into
      `local.expected_universe_start_date = coalesce(var.expected_universe_start_date, formatdate("YYYY-MM-DD",     timeadd(timestamp(), "-2880h")))`;
      `var.expected_universe_start_date` now defaults to `null` and stays available as an explicit override (e.g. for
      job (2)'s gated historical backfill). Verified in the sandbox: applying the expression on 2026-08-03 computed
      `2026-04-05`, exactly matching `date -u -d "-120 days"`. `terraform fmt -check` clean; full
      `terraform validate`/`plan` against the real GCS backend not run in-session (requires
      `terraform init -reconfigure` against prod state — out of this todo's scope; next `terraform apply` on this repo
      picks up the change and the recurring job's next 01:30 UTC run will carry the live rolling `--start-date`,
      verifiable via `gcloud run jobs executions list --job expected-universe-v2-sports` post-apply per the file's own
      "NOT fire-and-forget" verification note).
- [x] ✅ [DATA] P2. Implement job (2): the gated one-time historical `expected_unattempted` denominator backfill floored
      at **2020-06-06** (sports). Gated + resource-bounded (heavy — run on a VM per the heavy-I/O rule, never locally);
      scope to sports first. Done-when: 2020-06-06..present sports dates carry a seeded `expected_unattempted` universe
      so cross-year honest-coverage comparisons share one denominator regime. (repo: deployment-service) —
      deployment-service@e903189. New `scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh` chunks
      floor-date..(rolling-boundary − 1 day) into calendar-year windows and launches
      `launch-expected-universe-v2-vm.sh --apply-write` per chunk sequentially (waits for each chunk's VM to reach a
      terminal state before the next — respects the child launcher's own singleton lock, no `--force`), with
      `ENUM_START_DATE`/`ENUM_END_DATE` per chunk (env hooks the child launcher already supported). Sports defaults
      `--floor-date` to `2020-06-06` (/codex/02-data/sports-2020-06-data-floor.md); every other asset_group requires an
      explicit `--floor-date` (no codified floor yet — that's job (3) below). Rolling boundary is computed live
      (`today - 120d`, mirroring job (1)'s fix) so a re-run correctly narrows to only the still-uncovered range. Safe to
      re-run: the enumerator only ADDS `expected_unattempted` rows to cells with no existing capture_status row, and
      each chunk writes its own per-VM shard. Verified via `--dry-run` against the real 2026-08-03 clock: sports
      produces 7 chunks (2020-06-06..2020-12-31 through 2026-01-01..2026-04-04); the non-dry-run sequential launch+wait
      loop verified against a stubbed child-launcher + stubbed `gcloud` (new
      `tests/test_launch_expected_universe_v2_historical_backfill.sh`, 9/9 pass). The actual production launch (7 real
      GCE VMs sequentially against the live sports manifest bucket) was NOT run in this session — each chunk's real run
      is comparable in scale to the recurring job's own 120-day window (which needs a 3600s Cloud Run Job timeout for
      ~1/15th the span), so a full 7-chunk sequential run is a multi-hour-to-multi-day real backfill, outside a single
      worker-session's scope; kicking it off is the operator's/a dedicated follow-up run's call. Also fixed a
      pre-existing `set -e` leak in the sibling `test_launch_expected_universe_v2.sh`'s `_run` test helper (found while
      modeling this task's new harness on it — it broke that file's own non-verbose mode).
- [x] [DATA] P2. Launch + verify the real production run of job (2)'s new — launched by slot 6, chunk 1 done (636K),
      chunk 2 at 42M rows (harness-killed at 10.5h), post-run ratio re-check transferred to slot 8 entry (open todo)
      `scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh sports` (deployment-service@e903189) — 7
      sequential calendar-year VM chunks, 2020-06-06..2026-04-04 (recompute the rolling boundary live at launch time,
      don't reuse this fixed date). Launch chunk 1 (2020-06-06..2020-12-31) first as a validation slice; confirm it
      completes clean (no OOM — sports isn't on the defi memory-bump stopgap tier, verify e2-standard-4/16GB is actually
      sufficient for sports' catalogue size before trusting the remaining 6 chunks to the same default) and writes a
      sane row count to its per-VM shard before letting the rest run. NOT fire-and-forget: verify each chunk's STARTED
      event <60s, monitor progress, verify STOPPED/FAILED at completion (script already blocks sequentially and prints
      each chunk's VM name + log paths). Done-when: all 7 chunks TERMINATED with no FAILED lifecycle event, per-VM
      shards visible in `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/`, and a post-run
      cell-seeding ratio re-check (same method as this issue's own read-only measurement) shows the 2025-vs-2026 H1
      ratio has moved toward ~1x. (repo: deployment-service)
- [x] ✅ [DATA] P3. Re-measure the same static-default `expected_universe_start_date` pattern for
      cefi/defi/tradfi/prediction (same `expected_universe_v2_asset_groups` map, same `.tf`) —
      instruments-service@94838ad5. **defi: BOUNDARY ARTIFACT CONFIRMED** (8 data_types, governance_events 425x,
      flash_loan_events 36.7x, zero expected_unattempted in 2025 H1). **tradfi: BOUNDARY ARTIFACT CONFIRMED** (3
      data_types, trades 140.6x, tbbo 34.0x, ohlcv_15m 9.4x). **cefi: ELEVATED (3.43x) but NOT boundary-artifact** —
      expected_unattempted present in both years; book_snapshot_5 at 5.5x is genuine growth, not a denominator artifact.
      **prediction: ELEVATED (34.04x) but NOT boundary-artifact** — trades grew 48.4x via captured/empty_confirmed, not
      expected_unattempted (zero expected_unattempted in both 2025 AND 2026 H1). Measurement script shipped at
      instruments-service/scripts/cross_ag_manifest_enumeration_grain_check_2026_08_05.py. Follow-up: defi and tradfi
      need the same two-job model (rolling window + historical backfill) that sports already got; cefi/prediction have a
      different root cause (genuine growth, not the static-default window) and need separate diagnosis. (repo:
      instruments-service, deployment-service)
- [x] ✅ [DATA] P3. Investigate the FIXTURES/FIXTURES_OUTCOMES/ODDS-specific distinct-`league_id` growth —
      instruments-service@7fc96c90. **Verdict: GENUINE COVERAGE EXPANSION, not an artifact.** Original 88→924 figure was
      manifest ROW COUNTS, not distinct league_ids. Actual distinct league_id growth: FIXTURES 88→438 (4.98x),
      FIXTURES_OUTCOMES 88→439 (4.99x), ODDS 50→383 (7.66x) — consistent with control data_types WEATHER 94→384 (4.09x)
      and MATCHES 94→383 (4.07x). 84-100% cross-data_type overlap confirms the same league_ids appear across data_types.
      Zero case-insensitive duplicates found; all 83 near-duplicate candidates are false positives (different
      countries/divisions with similar naming conventions). 70%+ of new leagues have actual captured data. One possible
      real near-duplicate noted: KENYA_FKF_PREMIER_LEAGUE vs KENYA_PREMIER_LEAGUE. Script:
      `scripts/sports_league_id_growth_investigation_2026_08_05.py` (+ report at
      `/tmp/sports_league_id_growth_report_2026_08_05.json`).

## Progress Log

- **data_engineering worker (slot 4) 2026-08-08**: split the single "Complete remaining chunks 3-7" follow-up todo into
  6 bounded per-chunk todos (one launch+verify todo per chunk 3-7, plus a final gated ratio-recheck todo) +
  `sequential: true` in frontmatter to preserve required 3→4→5→6→7→recheck ordering. Direct instruction from main
  (bypasses backlog, BLK-free, 2026-08-08): the prior monolithic todo had wedge-killed 6x in ~3h across 5 slots
  (9@00:14, 5@00:37, 7@01:44, 9@01:59, 10@02:51, 3@03:14 UTC, all `slot_wedged_killed_for_resume`/kick-failed-idle) with
  zero forward progress on chunks 3-7 — root cause is a dispatch-model mismatch (one interactive session cannot reliably
  babysit a multi-hour, multi-VM, high-friction backfill start-to-finish, compounded by the two related open issues
  cited in each new todo), not a context-tuning problem. Each new chunk todo cites the two already-shipped/open guidance
  docs (`dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`,
  `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`) inline so a worker hitting either symptom
  mid-chunk treats it as expected/tracked rather than a fresh incident.
- **context-scout 2026-08-03**: re-read in full; existing context_scope (5 entries) still accurate — no new source
  target or SSOT surfaced beyond what's already listed. Refreshed marker only.
- **data_engineering worker (slot 3) 2026-08-03**: shipped job (1) — deployment-service@1d8ede9. Rolling `today - 120d`
  window now lives in a `locals` block (Terraform disallows `timestamp()`/`formatdate()` in a variable's own `default`);
  `var.expected_universe_start_date` kept as an optional override, default `null`. Full `terraform plan` against the
  real GCS backend not run (needs `terraform init -reconfigure`, out of scope); syntax + computed-value correctness
  verified in an isolated sandbox instead. Jobs (2)/(3)/(4) remain open.
- **data_engineering worker (slot 14) 2026-08-03**: launched the real production run of job (2)'s
  `launch-expected-universe-v2-historical-backfill-vm.sh sports` and found + fixed 3 real bugs in the launcher itself
  (the script as shipped by job (2) could never have completed):
  1. **deployment-service@f399619** — the launcher only waited for VM-terminal compute status, never checked the
     enumerator's own exit code. Every sports chunk (448K+-instrument catalog) trips `enumerate_expected_universe.py`'s
     `--max-writes-per-run` halt-safety (default 1M) almost immediately, so the unfixed script would have silently
     "finished" 7 partially-seeded chunks. Now reads the VM's durable `EXIT_STATUS` marker and retries the SAME window
     on a `5` (max_writes_exceeded) — safe/idempotent, the enumerator dynamically globs already-written per-VM shards
     and excludes them from the next attempt's candidates, so it converges. Hard-aborts on any other/missing status
     (before fix 3, below).
  2. **deployment-service@b64e4a7** — `LAUNCH_OUTPUT="$(child_launcher ...)"` under `set -e` aborted the whole script AT
     THE ASSIGNMENT when the child launcher failed, before the `echo` line that would have shown the real error — so a
     genuine failure (e.g. a `PERMISSION_DENIED`) died with zero diagnostics. Hit live: a sibling slot's
     `gcloud config set account` clobbered this shared host's active gcloud identity mid-run (`~/.config/gcloud` is
     host-global, not slot-isolated) and the retry died silently. Now captures the exit code explicitly and always
     echoes the captured output before deciding whether to abort.
  3. **deployment-service@3d70522** — a missing `EXIT_STATUS` was an unconditional hard-abort, which is correct for a
     genuine unknown failure but wrong for the routine case: every backfill VM defaults to SPOT (HARD RULE), and a
     preempted VM also leaves `EXIT_STATUS` unwritten. Confirmed live: a chunk-2 retry VM was preempted ~2 min after
     creation with zero logs (`compute.instances.preempted`, verified via `gcloud compute operations list`) — the
     unfixed script would have aborted the entire 7-chunk backfill over a routine SPOT reclaim. Now checks the
     operations log and retries on confirmed preemption; still hard-aborts if there's no preemption evidence. All 3
     fixes have shell-test coverage (15/15 pass, `tests/test_launch_expected_universe_v2_historical_backfill.sh`),
     shipped via the normal QG→quickmerge flow, and verified on `origin/live-defi-rollout`. Real production run
     relaunched after each fix; as of this log entry chunk 1/7 (2020-06-06..2020-12-31) completed clean
     (`EXIT_STATUS=0`), chunk 2/7 (2021-01-01..2021-12-31) is in progress with a notably large candidate backlog for a
     single calendar year (13+ retry attempts observed, a mix of genuine `max_writes_exceeded` halts and an elevated
     SPOT preemption rate in asia-northeast1-c for `e2-standard-4` — all safely converging within the
     `MAX_CHUNK_ATTEMPTS=50` bound, no runaway signal). Did not raise `--max-writes-per-run` unilaterally — that's
     operator-review-gated per the enumerator's own error message and RULES.md. Chunks 3-7 (2022..2026-04-04) not yet
     reached. This todo (`[DATA] P2. Launch + verify the real production run of job (2)'s new script`) stays
     open/in-progress; will flip once all 7 chunks TERMINATE clean and the post-run cell-seeding ratio re-check (same
     method as this issue's own read-only measurement) is done.
- **data_engineering worker (slot 14) 2026-08-04 (continued)**: found + fixed a 4th real bug and filed a 5th (separate
  issue doc, cross-cutting — not part of the numbered fix list since it's an environment issue, not a launcher-code
  bug): 4. **deployment-service@16e8de3 + @e7c9510** — the shared-host `gcloud` active identity (`~/.config/gcloud` is
  HOST-WIDE, not per-slot — see `/codex/05-infrastructure/per-tab-worktrees.md` § "On-demand artifact pattern") got
  clobbered by a sibling slot's `gcloud config set account` call THREE separate times during this run, each time
  aborting the backfill with `PERMISSION_DENIED` on `compute.instances.create` (caught cleanly each time only because of
  fix 2 above — the error surfaced instead of dying silently). Both `launch-expected-universe-v2-vm.sh` and the
  historical-backfill wrapper now
  `export CLOUDSDK_CORE_ACCOUNT=unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (overridable) at the
  top of the script, pinning the identity per-invocation without touching the shared config file. Verified live:
  launched successfully with the shared active account deliberately set to a DIFFERENT, unprivileged identity, and
  confirmed the shared config was left untouched afterward. 16/16 shell tests pass (added a test asserting the pin, plus
  fixed 2 pre-existing hardcoded rolling-boundary date literals that broke when the wall-clock date rolled over
  2026-08-03->2026-08-04 mid-session — both now computed dynamically).
  - Filed **`plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`** (P2,
    cross-cutting) recommending the broader fix (audit ALL `deployment-service/scripts/vm/` launchers for the same
    ambient-identity dependency, or give each slot its own named gcloud configuration) — only the 2 scripts this
    backfill actually touches were fixed here; the rest of the launcher family is that issue's own follow-up scope, not
    absorbed into this todo.
  - **Live status as of this entry**: backfill relaunched with all 4 fixes (5th relaunch overall, background task still
    running in-session). Chunk 1/7 re-confirmed `EXIT_STATUS=0` (idempotent no-op, already fully seeded). Chunk 2/7
    (2021-01-01..2021-12-31) is on its ~8th cumulative retry attempt across relaunches (present-set has grown from 6.1M
    rows post-chunk-1 to 8.8M+ mid-chunk-2, confirmed via `Manifest present-set`/`Augmented manifest sets` log lines) —
    converging correctly, no error signal, well within `MAX_CHUNK_ATTEMPTS=50` per invocation. The elevated SPOT
    preemption rate observed throughout this session (roughly 5-6 preemptions across ~20 total launch attempts) is NOT
    this campaign's own issue — a sibling slot independently confirmed a fleet-wide, ongoing `asia-northeast1-c` SPOT
    preemption storm (151 preemptions/5h across sports/tradfi/cefi simultaneously) and filed
    `plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md` as its own P1/big-finding; every
    preemption hitting THIS backfill was correctly absorbed by fix 3, so this campaign stays unblocked regardless of
    that storm's own resolution timeline. **If this todo is picked up cold by a fresh session**: check
    `gcloud compute instances list --filter='name~"expected-universe-v2-sports-"'` for a currently-RUNNING VM first
    (idempotent-safe either way, but tells you whether a relaunch is needed or one is already in flight); the per-VM
    shards + main manifest already hold real progress from this session, so a fresh
    `bash launch-expected-universe-v2-historical-backfill-vm.sh sports` naturally resumes rather than restarting. Not
    yet reached: rest of chunk 2, chunks 3-7 (2022-01-01 through the then-current rolling boundary), and the final
    post-run cell-seeding ratio re-check that this todo's done-when requires.
- **data_engineering worker (slot 14) 2026-08-04 (checkpoint before /compact)**: two more developments since the entry
  above, both confirming the design is working as intended, not new bugs:
  1. **Investigated an apparent stall** (present-set base metric looked nearly flat for ~2h despite many successful
     halt-safety writes) — ruled out via a direct read-only manifest query (single download, column-projected, same
     pattern as this issue's own original measurement): 2021 currently carries **785,398 genuine `expected_unattempted`
     rows** (0 before this backfill), and per-attempt file content hashes differ across consecutive writes (ruling out
     "rewriting the same rows" as a bug). The flat-looking metric was a red herring — it reads a
     periodically-consolidated base snapshot, not the live augmented total the enumerator actually uses for exclusion.
     No code change needed; documenting so a future session doesn't re-chase the same false alarm.
  2. **The 5th relaunch (v5) exhausted its own `MAX_CHUNK_ATTEMPTS=50` on chunk 2** — hit the hard-abort I designed for
     a suspected runaway (`"still hit the max-writes-per-run halt-safety after 50 attempts ... STOPPING"`), but this was
     overwhelmingly preemption-storm-driven (the fleet-wide `asia-northeast1-c` storm from finding above intensified
     sharply late in this invocation — several consecutive back-to-back preemptions with zero writes in between), not a
     genuine runaway-candidate bug (already ruled out per point 1). Correct response per my own design: relaunch fresh
     rather than raise the cap — each invocation's `MAX_CHUNK_ATTEMPTS` counter is per-invocation only, real progress
     persists in GCS regardless of how many times the script itself has been relaunched. **6th relaunch (v6) in
     progress** as of this checkpoint, chunk 1/7 re-confirmed clean, chunk 2/7 resuming. **If a future relaunch ALSO
     exhausts its cap purely from consecutive preemptions**: this is expected under the ongoing storm, not a signal to
     raise `--max-writes-per-run` — just relaunch again; only escalate/pause if a `would-write` count from a SINGLE
     attempt is ever anomalously large (e.g. 10x+ the prior norm), which would be the actual runaway-bug signature, not
     repeated exhaustion from preemption alone.
- **data_engineering worker (slot 8) 2026-08-04 (in progress)**: launched a fresh production run of
  `launch-expected-universe-v2-historical-backfill-vm.sh sports`. All 4 fixes from slot 14 verified present at
  deployment-service HEAD (f399619, b64e4a7, 3d70522, 16e8de3, e7c9510 all ancestors of 5c9d673). No pre-existing
  RUNNING VMs at launch time (all TERMINATED from prior runs). The backfill script is running as a background tracked
  task with a 2-min event monitor and a 15-min stall watchdog (per-VM shard count as progress metric). **Status at 18:00
  UTC**: chunk 1/7 (2020-06-06..2020-12-31) completed clean — 636,632 rows, EXIT_STATUS=0, 3 per-VM shard parts, 20.5s.
  Chunk 2/7 (2021-01-01..2021-12-31) is on retry 9/50 — 9M rows written across 9 attempts, each hitting EXIT_STATUS=5
  (max-writes-per-run halt-safety). Per-VM shard exclusion verified working: retry 6's run.log confirmed it correctly
  loads prior per-VM shards (retries 3-5: 3M rows) and the main manifest base reflects consolidated shards from earlier
  retries. The 2021 window genuinely has >10M expected_unattempted cells (consistent with the original issue's finding
  of 10.5x FIXTURES league growth: 88→924). Each retry writes exactly 1M rows and converges — the script handles this
  automatically (MAX_CHUNK_ATTEMPTS=50). No SPOT preemption observed in this session so far (0 preemption events in
  asia-northeast1-c during ~1h of VM launches). Chunks 3-7 (2022 through 2026-04-05) not yet reached. The backfill is a
  multi-hour operation — at ~7 min/retry with 10+ retries expected for the larger full-year chunks, total runtime is
  estimated at 2-4 hours. **If picked up by a fresh session**: the backfill may still be running (check
  `gcloud compute instances list` for a RUNNING `expected-universe-v2-sports-*` VM); if no VM is running, re-launch with
  `bash launch-expected-universe-v2-historical-backfill-vm.sh sports` (idempotent). Per-VM shards + main manifest
  already hold real progress — the enumerator naturally resumes rather than restarting. Post-run cell-seeding ratio
  re-check (same method as this issue's original measurement) is the done-when gate.
- **data_engineering worker (slot 6) 2026-08-04 (in progress)**: launched a fresh production run of
  `launch-expected-universe-v2-historical-backfill-vm.sh sports`. All 4 prior fixes verified present. No RUNNING VMs at
  launch time (all TERMINATED). The backfill script is running as a background tracked task with a 60-min monitor +
  stall watchdog. **Status at ~20:50 UTC**: chunk 1/7 (2020-06-06..2020-12-31) completed clean — 636,632 rows,
  EXIT_STATUS=0, 3 per-VM shard parts, ~20s. Chunk 2/7 (2021-01-01..2021-12-31) is on retry 14/50 — **14M+ rows written
  across 15 attempts** (initial + 14 retries), each hitting EXIT_STATUS=5 (max-writes-per-run halt-safety). The 2021
  window is significantly larger than slot 8's estimate of 9-10M — this is consistent with the original issue's finding
  of 10.5x FIXTURES league growth (88→924), which produces proportionally more expected_unattempted cells across 365
  days. Each retry writes exactly 1M rows and converges correctly (per-VM shard exclusion verified working across all
  attempts). **No SPOT preemptions observed** (0 preemption events — the fleet-wide asia-northeast1-c SPOT preemption
  storm from slot 8/14's sessions has subsided). No errors — script auto-cycling correctly, all retries within
  MAX_CHUNK_ATTEMPTS=50. Per-attempt cycle time ~7 min (4-6 min bootstrap + 60-90s enumeration + 1-2 min teardown).
  Chunks 3-7 (2022 through 2026-04-05) not yet reached. The stale tarball warnings (deployment-service,
  unified-api-contracts) are benign — the existing GCS tarballs contain all needed fixes. **Measurement trap**: the
  consolidated manifest count (`availability_index.parquet`) is a lagging indicator — the consolidator runs periodically
  (~5 min intervals) and per-VM shards may not be folded for 10-30 min. Rely on per-VM shard counts and enumerator
  run.logs, not the consolidated manifest, for real-time progress. **If picked up cold**: check
  `gcloud compute instances list --filter='name~"expected-universe-v2-sports-"'` for a RUNNING VM; if none, re-launch
  with `bash scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh sports` (idempotent — per-VM shards +
  manifest already hold real progress). Script PID this session: 2560979. Post-run cell-seeding ratio re-check (same
  method as this issue's original measurement) is the done-when gate.
- **data_engineering worker (slot 9) 2026-08-05**: re-measured the static-default `expected_universe_start_date`
  boundary artifact for cefi/defi/tradfi/prediction (P3 cross-AG measurement). Used a new generalized script
  `cross_ag_manifest_enumeration_grain_check_2026_08_05.py` (instruments-service@94838ad5) that reads each AG's live
  `_index/availability_index.parquet` once. Results: **defi** — BOUNDARY ARTIFACT CONFIRMED: 8 data_types,
  governance_events 425x, flash_loan_events 36.7x, plus 6 more (74.4M-row manifest, overall 1.89x but heavy outliers).
  **tradfi** — BOUNDARY ARTIFACT CONFIRMED: 3 data_types, trades 140.6x, tbbo 34.0x, ohlcv_15m 9.4x (6.4M rows, 1.57x).
  **cefi** — ELEVATED (3.43x) but NOT boundary-artifact: `expected_unattempted` present in both years. **prediction** —
  ELEVATED (34.04x) but NOT boundary-artifact: trades grew 48.4x via captured/empty_confirmed with zero
  `expected_unattempted` in BOTH years. Follow-up: defi/tradfi need the same rolling-window fix + historical backfill;
  cefi/prediction have a different root cause and need separate diagnosis. Full JSON reports at
  `/tmp/{ag}_enum_grain_report_2026_08_05.json`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **data_engineering worker (slot-15) 2026-08-07 (second pass, context compacted)**: Fresh parent run started ~23:31 UTC
  in tmux `orch-slot-15:backfill`. Chunk 1/7 (2020-06-06..2020-12-31) VM `expected-universe-v2-sports-20260807-233155`
  EXIT_STATUS=0 in ~4 min (fast — rows already consolidated into main manifest; enumerator found no new candidate
  cells). Chunk 2/7 (2021-01-01..2021-12-31) VM `expected-universe-v2-sports-20260807-233626` RUNNING as of 23:36 UTC.
  Chunks 3-7 not started (first-ever seed). Background watchdog `bvflynvzt` (20-min) and state-change watcher
  `b6fbst7gj` armed. Compacting to preserve context; backfill continues in tmux.
- **data_engineering worker (slot-15) 2026-08-07**: Full session history — Chunk 1/7 (VM `214049`) EXIT_STATUS=0
  (638,521 rows). Chunk 2/7: retries 1-11 (VMs `214629`..`223801`) each EXIT_STATUS=5 (+1M rows/retry = ~11M seeded this
  session from scratch; consolidator cleaned prior-session shards at start). Retry 12 (VM `224305`) EXIT_STATUS=0
  (637,267 final rows) — chunk 2 complete first pass. **Consolidator behavior**: manifest consolidator deleted per-VM
  shards between parent restarts; subsequent runs re-find the same rows as candidates (~637K for chunk 1, full chunk for
  chunk 2) because expected_unattempted rows written to per-VM shards are only excluded while shards exist in GCS. After
  consolidation, rows ARE in main manifest but `present=9974285` count appears stable (possibly the "present" set
  reflects captured+expected_unattempted only for the non-date-filtered portion, not the window being enumerated). **Key
  discovery**: both chunk 1 and chunk 2 re-seed on each parent restart (~637K rows each, rc=0) — convergence requires
  per-VM shards to survive until the post-run ratio check. **Parent dying**: parent script (PID 1397101 then 3298329
  then 3507556) kept dying during `sleep 60` in polling loop (SIGTERM from harness session reset). **Fix**: moved to
  tmux `orch-slot-15:backfill` (`tmux new-window -t orch-slot-15 -n backfill bash`) which survives harness kills. Chunk
  2 needs further retries in current tmux run (consolidator cleared ~11M of prior-session shards). Chunks 3-7 have never
  been seeded — each will need multiple retries (similar to chunk 2). **Resume point**: check
  `tmux capture-pane -t "orch-slot-15:backfill" -p -S -10` or `tail -f backfill-tmux.output` (path in tasks dir). If
  tmux window gone, re-run: `tmux new-window -t orch-slot-15 -n backfill bash` then same launch command. All 7 chunks
  must complete EXIT_STATUS=0 in a single parent run (no intervening restarts), then run post-run ratio re-check.
  **Instruments-service tarball updated mid-session**: from `f4fce7cc27bb` → `27e29a914616`.
- **infra worker (slot-9) 2026-08-08**: slot-15 session/tmux gone; no competing VMs; per-VM shards from slot-15's last
  session (3 chunks from 20260807-233155 [chunk 1] and 233626/234049/234713 [chunk 2 partial, ~3M rows]) still in GCS.
  Found and fixed the prior session's launch blocker: `LC_TARBALL_FRESHNESS` defaulted to `auto`, which tried to
  republish the deployment-service tarball (stale at `27fd5779` vs HEAD `52bf0840`), but `gcs_upload_via_adc.py` failed
  with `ModuleNotFoundError: No module named 'deployment_service'` (venv issue on slot-9). Set
  `LC_TARBALL_FRESHNESS=warn` to proceed with the existing GCS tarballs — IS tarball is current (9e96f5f3),
  deployment-service tarball is slightly behind but benign (all the critical launch fixes are in `27fd5779`). Relaunched
  in tmux `orch-slot-9:backfill` (harness-kill-proof). Chunk 1/7 VM `expected-universe-v2-sports-20260808-000138`
  RUNNING as of 00:01 UTC; background monitor (`bcz22sw1y`/`bsl5zwnd7`) sending heartbeats every 5 min.
- **data_engineering worker (slot-7) 2026-08-08**: slot-9 and slot-5 sessions gone; no competing VMs. Assessed state:
  chunk 1/7 (VM `000138`) EXIT_STATUS=0 and chunk 1 re-run (VM `003059`) EXIT_STATUS=0 confirm chunk 1 fully seeded.
  Chunk 2/7 last attempt (VM `003520`) EXIT_STATUS=5 with `would-write 1000001 > max_writes_per_run 1000000` — 1M rows
  written this attempt, ~1 row still remaining. Per-VM shards from all prior runs consolidated into main manifest.
  Launched fresh parent run in tmux `orch-slot-7:backfill` (~01:38 UTC). Chunk 1/7 VM
  `expected-universe-v2-sports-20260808-013813` RUNNING. Tarballs all fresh (no LC_TARBALL_FRESHNESS=warn needed). Will
  monitor all 7 chunks; post-run ratio re-check runs once all EXIT_STATUS=0.
- **data_engineering worker (slot-10) 2026-08-08**: slot-7 session gone, no competing VMs. Relaunched in tmux
  `orch-slot-10:backfill` (~02:40 UTC). Chunk 1/7 VM `expected-universe-v2-sports-20260808-024035` EXIT_STATUS=0 in ~3
  min (fast — rows already consolidated into main manifest). Chunk 2/7 VM `expected-universe-v2-sports-20260808-024458`
  RUNNING (2021-01-01..2021-12-31) as of ~02:44 UTC. All 4 tarballs fresh (IS 9e96f5f3, UAC fa383493, UTL 28a9160d, DS
  f3063b98). LC_TARBALL_FRESHNESS=warn set as safety precaution (no actual republish needed). Background 30-min
  heartbeat monitor armed (sends /progress every 5 min). Chunks 3-7 (2022..2026-04-09) not yet reached — this entry
  captures the start state; will update on completion.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **infra worker (slot 33) 2026-08-09**: picked up chunk 3/7 (2022-01-01..2022-12-31). Found + fixed a real, unrelated
  launcher bug blocking every tarball auto-republish (`create-code-tarballs.sh`'s `GCS_UPLOAD_PY` fell back to bare
  `python3` — missing `deployment_service` — whenever `deployment-service/.venv` didn't already exist on the slot; now
  resolves via `uv run --project`) — shipped + verified on origin: deployment-service@0f4e22fa5482. After the fix, ran
  10 consecutive successful launcher attempts (all `EXIT_STATUS=5`, the documented halt-safety trip) but then discovered
  via direct per-VM shard content comparison that the retries are **NOT converging** — every attempt wrote the exact
  same 1,000,000-row set (100% key overlap across 2 independent attempt-pairs, verified at the enumerator's own
  present-set grain). Root-caused to a structural livelock in the sports v2 generator (several deterministic
  empty_confirmed branches never check `present_set` before yielding, so they regenerate identically every run and
  consume the entire `max_writes_per_run` cap before any new candidate is ever reached) — filed as its own issue with
  full evidence + 3 candidate fix directions, left for operator triage:
  `/plans/active/issues/sports_expected_universe_v2_halt_safety_livelock_no_present_set_gate_2026_08_09.md`. Chunk 3's
  own done-when (EXIT_STATUS=0) is **not reachable** under the current code without one of that issue's fixes — did not
  flip chunk 3's todo below; converting it to a blocked state instead (see banner). Did not touch chunks 4-7 pending the
  operator's fix-direction decision.
- **infra worker (slot 33) 2026-08-09 (continued, post BLK-30815e45 answer)**: operator picked fix (B). Implemented at
  the write/count boundary rather than the generator (a generator-level gate broke the pre-existing
  `test_oscillation_guard_drops_season_gate_empty_over_captured_atom` regression test — that test proves the recurring
  daily cron + the oscillation guard, a SEPARATE `captured_set`-keyed mechanism, both rely on the deterministic branches
  re-yielding every run regardless of `present_set`). `_stream_write_v2_absent_rows` now accepts
  `present_set`/`present_cols` and skips a candidate already recorded before counting it toward `max_writes_per_run` or
  writing it — shipped + verified on origin: instruments-service@0d66cb926e0b (234/234 existing tests pass unmodified
  - 2 new regression tests, full `quality-gates.sh` green). Re-ran chunk 3: converged in ONE attempt, `EXIT_STATUS=0`,
    17.6s, 144,586 genuinely-new rows (present-set of 11.79M correctly excluded the duplicate rows accumulated from the
    pre-fix attempts) — flipped chunk 3's todo below. Chunks 4-7 no longer blocked; next worker should proceed normally.

## Follow-ups

> **✅ RESOLVED 2026-08-09 (slot 33)**: operator picked fix (B) on `BLK-30815e45` — gate the write/count boundary on
> `present_set` (see `sports_expected_universe_v2_halt_safety_livelock_no_present_set_gate_2026_08_09.md`, shipped
> instruments-service@0d66cb926e0b). Chunk 3 re-run converged in ONE attempt (`EXIT_STATUS=0`, 17.6s, 144,586
> genuinely-new rows — present-set correctly excluded the ~11.8M rows accumulated from the pre-fix duplicate-writing
> attempts). Chunks 4-7 should now converge normally too — no longer blocked.

- [x] ✅ [DATA] P2. Launch + verify chunk 3/7 (2022-01-01..2022-12-31) of the job (2) historical `expected_unattempted`
      backfill: invoke the child launcher directly
      (`deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh     --apply-write sports`,
      `ENUM_START_DATE=2022-01-01 ENUM_END_DATE=2022-12-31`) in a harness-kill-proof tmux window
      (`tmux new-window -t orch-slot-<N> -n backfill bash`), not a bare backgrounded shell. Retry the SAME chunk until
      it reaches EXIT_STATUS=0 — if a run exits EXIT_STATUS=5 (`would-write X > max_writes_per_run`), that is the
      enumerator's own known, self-managed max-writes-per-run halt-safety trip: expected and retriable, not a new
      incident (`dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md` already routes this exit-code class
      to WARN/FILE_ISSUE, never a page — just relaunch the same chunk). If `gcloud compute instances create` fails with
      `PERMISSION_DENIED` on `compute.instances.create` even though nothing in this task changed the active account,
      that is the known shared-host `gcloud config set account` cross-slot clobber
      (`shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`) — check `gcloud config get-value account`,
      restore/pin to the correct identity (prefer a per-invocation `--account=` override per that doc's recommended
      fix), then retry; this is not a real IAM gap. Done-when: chunk 3 reaches EXIT_STATUS=0, its per-VM shard is
      visible under `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/`. Update this doc's
      Progress Log with the VM name(s) + final status before flipping. (repo: deployment-service) — ✅ VM
      `expected-universe-v2-sports-20260809-161551`, `EXIT_STATUS=0`, per-VM shard at
      `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/expected-universe-v2-sports-20260809-161551-part00001.parquet`
      (144,586 rows). Required the halt-safety livelock fix (instruments-service@0d66cb926e0b) first — see the resolved
      banner above.
- [ ] [DATA] P2. Launch + verify chunk 4/7 (2023-01-01..2023-12-31) of the same backfill — same launcher invocation,
      halt-safety/gcloud-clobber handling, and done-when as chunk 3's todo above, with
      `ENUM_START_DATE=2023-01-01 ENUM_END_DATE=2023-12-31`. (repo: deployment-service)
- [ ] [DATA] P2. Launch + verify chunk 5/7 (2024-01-01..2024-12-31) of the same backfill — same launcher invocation,
      halt-safety/gcloud-clobber handling, and done-when as chunk 3's todo above, with
      `ENUM_START_DATE=2024-01-01 ENUM_END_DATE=2024-12-31`. (repo: deployment-service)
- [ ] [DATA] P2. Launch + verify chunk 6/7 (2025-01-01..2025-12-31) of the same backfill — same launcher invocation,
      halt-safety/gcloud-clobber handling, and done-when as chunk 3's todo above, with
      `ENUM_START_DATE=2025-01-01 ENUM_END_DATE=2025-12-31`. (repo: deployment-service)
- [ ] [DATA] P2. Launch + verify chunk 7/7 (2026-01-01..rolling-boundary−1day, i.e. `today − 120d` computed LIVE at
      launch time — do NOT reuse the stale `2026-04-04`/`2026-04-09` dates recorded earlier in this doc's Progress Log)
      of the same backfill — same launcher invocation, halt-safety/gcloud-clobber handling, and done-when as chunk 3's
      todo above, with `ENUM_START_DATE=2026-01-01` and `ENUM_END_DATE` set to the freshly-computed rolling boundary.
      (repo: deployment-service)
- [ ] [DATA] P2. Once chunks 3-7 above are ALL done: run the post-run cell-seeding ratio re-check (same read-only method
      as this issue's own H1 measurement — single manifest read, columns projected to
      `date`/`data_type`/`capture_status`/`league_id`/`source`, count total rows per `data_type` for the matched H1
      windows `2025-01-01..2025-06-30` vs `2026-01-01..2026-06-30`) and record whether the ratio has moved toward ~1x.
      This is the done-when gate for job (2)'s production run. (repo: instruments-service)

> **2026-08-06 archive-candidate audit**: Todo 4 is flipped [x] but its own text says 'post-run ratio re-check
> transferred to slot 8 entry (open todo)', and Progress Log (slot 8 + slot 6, 2026-08-04) confirms 'Chunks 3-7 not yet
> reached' and the done-when ratio re-check never ran — false-completion on an incomplete multi-hour backfill.
