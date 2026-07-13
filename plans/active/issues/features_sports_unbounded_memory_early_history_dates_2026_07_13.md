---
doc_type: issue
title:
  features-service sports compute — unbounded memory growth on specific early-history dates (OOM regardless of VM RAM)
summary:
  Sports features compute for date 2018-06-17 (400-day historical lookback, 167 snapshots, 30,447 unique fixtures)
  OOM-kills the features-service process twice in a row — once on e2-standard-4 (16GB, anon-rss 15.7GB) and again on
  e2-standard-8 (32GB, anon-rss 32.1GB) after doubling RAM. Memory consumption scales to consume whatever is available
  rather than being bounded by the actual data size, indicating a real leak/unbounded-growth bug in the compute path
  (likely the historical-fixtures join or a per-team/per-league rolling calculator), not a capacity problem. The wrapper
  script's EXIT trap records EXIT_STATUS=0 (false success) even though only 1 of 421 assigned dates completed — a
  silent-success signal masking a hard crash.
status: open
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, oom, memory-leak, backfill, honest-absence, data-correctness]
related:
  [
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    codex/02-data/feature-formula-versioning.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-13
parent_epic: sports_master
priority: P1
source: sports_p2_features_history_to_ml_ready-002 dispatch, slot 6, 2026-07-13 (full-history features backfill fleet)
assigned_vm: planning
resolved_by:
locked_by:
audited_scope: data-correctness
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
---

# features-service sports compute — unbounded memory growth on early-history dates

## What I found

While babysitting the 10-VM full-history (2015→present) sports features backfill fleet for
`sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1, I found 2 of 10 shards dead:

- **`fss-backfill-vm-4`** (assigned range 2018-06-17→2019-08-11, a gap-fill relaunch of a shard preempted earlier
  today): `features-servic` process **OOM-killed** by the kernel (`dmesg`:
  `Out of memory: Killed process 5516 (features-servic) total-vm:20589072kB, anon-rss:15701340kB` on an `e2-standard-4`,
  16GB RAM) after completing only its FIRST assigned date (2018-06-17). No process running, load average 0.00, confirmed
  via SSH.
- **`fss-backfill-vm-5`** (assigned range 2019-08-12→2020-10-05): initially appeared unresponsive (SSH timed out twice,
  serial console stopped emitting at the same point); turned out to be genuinely alive, just slow on a memory-heavy
  `odds` feature-group step for its own first date (2019-08-12) — 87.7% CPU, 12.6GB/32GB RSS, NOT a duplicate of the
  vm-4 issue. No action needed on vm-5.

**Reproduced the vm-4 OOM on a doubled-RAM instance**: relaunched vm-4 on `e2-standard-8` (32GB) reusing the exact same
staged codebase tarball (`gs://features-sports-central-element-323112/_vm_staging/fss_backfill/`, SHA matching today's
fleet). It OOM'd again at the **identical point in the log** (right after `Calculator advanced_stats: 62 columns added`,
processing the same date 2018-06-17) — this time `total-vm:38578912kB, anon-rss:32125532kB` (kernel `dmesg`). Memory
consumption scaled to consume ~32GB instead of failing at some fixed, bounded working-set size — strong evidence of
unbounded growth (a leak, or an accidental O(n²)/cartesian join over the historical lookback data) rather than a genuine
large-but-bounded working set that just needs more RAM.

**Context from the log** (both runs, identical): for 2018-06-17, the compute reads a **400-day historical lookback**:
`Reading 167 fixture files from 400-day lookback` → `Historical fixtures: 30447 unique fixtures from 167 snapshots` →
`Combined fixtures: 30596 (today: 149 + historical: 30447)` →
`Team history: 60894 rows from completed fixtures before 2018-06-17`. The date also hits the
`_read_per_league_subpartitions` fallback path in `features_service/sports/data/gcs_reader.py:195-239` (33 separate
per-league `standings` shard reads + `pd.concat`) because no consolidated `standings.parquet` exists for
`day=2018-06-16`. I did not have time to pin the exact allocation site (candidates: the historical-fixtures join
building `30596`-row combined frames repeatedly across calculators without releasing; one of the per-team/per-league
rolling calculators — `team_form`, `team_goals`, `team_xg`, `h2h`, `promoted_team` — doing an unbounded
groupby/rolling-window computation over the full 30k+-row historical frame per fixture instead of a windowed subset; or
the per-league fallback concat pattern generalizing badly when the historical lookback itself needs many prior-day
fallbacks).

**Silent false-success signal**: despite the OOM kill, `EXIT_STATUS` for vm-4 both times read `0` (success) — the
`lc_log_upload_trap_block` EXIT trap fires and uploads a "0" exit code even when the actual workload process was killed
asynchronously by the OOM killer (the trap captures the wrapper shell's own exit code, not the killed subprocess's).
This matches this SAME plan's earlier root-caused finding (`e2e-testing@f2487e4`, 2026-07-13 slot 9, stdin-siphon bug)
in shape if not in mechanism: **a crashed shard reports `EXIT_STATUS=0`**, so an automated "all shards report 0 → done"
check would wrongly treat 2018-06-17 as successfully processed for the rest of history, when in fact it was never
computed and the manifest likely has no captured row for it (or a partial one).

## Why it matters

- Blocks `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1 (full-history compute) and, transitively, Todo 3
  (features manifest clean over history — needs 0 blank-reason, 0 un-evidenced-failed) — any date the compute never
  actually captures will show up as `EXPECTED_UNATTEMPTED` (or missing entirely) rather than `captured`, and Todo 3's
  gate cannot be honestly closed while a known-reproducible crash is silently reported as success.
- Per `codex/02-data/data-pipeline-correctness-hard-rule.md`, a data-correctness defect is fixed in full, not deferred —
  this is exactly that class: a genuine compute failure that would otherwise be invisible to any monitor that only
  checks `EXIT_STATUS`.
- Other early-history dates with similarly dense historical-snapshot lookbacks (many prior years, many league shards)
  may hit the same unbounded-growth path — 2018-06-17 is the one instance confirmed twice; it is very likely not unique.

## What I did (mitigation, not a fix)

- Relaunched `fss-backfill-vm-4` a third time on `e2-standard-4` (reverted to standard size — bigger RAM does not help)
  with `--start 2018-06-18 --end 2019-08-11`, **excluding** the poison date 2018-06-17 so the rest of the shard's range
  can proceed without crash-looping. Verified booting past the install phase.
- Left `fss-backfill-vm-5` untouched — confirmed genuinely alive and progressing.
- Did NOT attempt to fix the memory growth itself — root-causing an unbounded-growth bug inside the calculator pipeline
  needs profiling (e.g. `tracemalloc`/`memray` across the historical-join + calculator chain for exactly this date),
  which is a real investigation, not a quick patch; rushing a guess-fix risks masking the actual bug.

## Recommended decision

1. **Profile the 2018-06-17 compute path** (`--start 2018-06-17 --end 2018-06-17 --force`, single date, under
   `memray run` or `tracemalloc`) to pin the exact allocation site among the historical-fixtures join and the
   per-team/per-league rolling calculators (`team_form`, `team_goals`, `team_xg`, `h2h`, `promoted_team`).
2. **Bound the historical lookback** — cap the working set the 400-day lookback join builds (e.g. filter to the specific
   teams/leagues in play that day before the join, rather than joining against the full 30k+-row historical frame), or
   release/free intermediate frames between calculators.
3. **Fix the false-success EXIT_STATUS**: `lc_log_upload_trap_block` (or its callers) should capture the actual workload
   subprocess's exit code, not just the wrapper shell's — an OOM-killed child should propagate as a non-zero terminal
   status so a fleet monitor can distinguish "crashed" from "completed." Cross-cutting (same helper backs ~80
   launchers), so scope carefully — may already be handled correctly for a `set -e`-visible failure and only wrong for
   an OOM-killed child that dies asynchronously without the parent shell's own exit code reflecting it.
4. Once fixed, re-run `--start 2018-06-17 --end 2018-06-17 --force` to backfill the excluded date, then re-verify Todo
   3's manifest-cleanliness gate for the full 2015→present range.

## Todos

- [ ] [DATA] P1. Profile the features-service sports compute for date 2018-06-17 (`memray`/`tracemalloc`) to find the
      exact unbounded-memory allocation site among the historical-fixtures join and rolling calculators. (repo:
      features-service)
- [ ] [DATA] P1. Bound/fix the identified allocation site so this date (and any date with a similarly dense
      historical-snapshot lookback) computes within a fixed, reasonable memory ceiling (e.g. under 16GB). (repo:
      features-service)
- [ ] [INFRA] P2. Fix `lc_log_upload_trap_block`'s EXIT_STATUS to reflect an OOM-killed/crashed workload subprocess's
      real exit code, not just the wrapper shell's — so a crashed shard is never reported as `EXIT_STATUS=0`. (repo:
      deployment-service)
- [ ] [DATA] P2. After the fix lands, `--force`-recompute 2018-06-17 (and audit for other similarly-shaped
      dense-lookback dates) then re-run `check_pipeline_completeness.py` / the manifest-cleanliness query for the full
      2015→present range. (repo: features-service)
