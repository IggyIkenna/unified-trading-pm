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
    plans/active/issues/sports_venue_id_numeric_coercion_data_loss_2026_07_13.md,
    codex/02-data/feature-formula-versioning.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-13
parent_epic: sports_master
priority: P1
source:
  sports_p2_features_history_to_ml_ready-002 dispatch, slot 6, 2026-07-13 (full-history features backfill fleet);
  reopened same day by slot 12 after the shipped fix (features-service@b05f48ad) failed to reproduce-fix on real data
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

## Additional finding (independent concurrent investigation, slot-8, 2026-07-13)

**A dispatcher collision happened on this issue's Todo 1**: slot-10 picked up the same todo and shipped
`features-service@b05f48ad` (`shot_quality_calculator` fix) at 10:40 UTC while I was independently profiling the same
date using REAL production GCS data (not a synthetic repro). My investigation found a **separate, chronologically
EARLIER unbounded-growth site** that slot-10's fix does not touch — flagging this because, if correct, the pipeline
never reaches `shot_quality_calculator` (deep inside `run_new_calculators`, Phase-4) on this date: it OOMs first in
`venue_context`, which runs several calculator-groups earlier (right after `advanced_stats`, matching BOTH original
`dmesg` OOM logs' exact crash point).

**Method**: built a tracemalloc/RSS-instrumented harness (`scripts/sports/profile_2018_06_17_memory.py`) that
monkeypatches the real pipeline functions in `derived_features_exporter` (no production-code changes) and ran it against
real 2018-06-17 GCS data end-to-end, protected by an external RSS-polling watchdog (RLIMIT_AS was tried first and
rejected — it caps virtual address space, not RSS, and false-triggers on numpy/grpc/BLAS mmap arenas long before real
memory grows). Confirmed `team_form`/`team_xg`/`team_goals`/`h2h`/`promoted_team` all complete with negligible memory
deltas (flat ~5.3GB RSS baseline) — ruling out the original 5 suspects named in "What I found" above. The crash
reproduced twice at the identical point: immediately after `Calculator advanced_stats: 62 columns added`, RSS jumping
from ~5.3GB to 11.5GB+ within seconds (first run, 10GB watchdog kill) confirming the crash site is the very next
calculator group.

**Root cause, pinned exactly** via a cached-input bisection script (`scripts/sports/profile_venue_context_bisect.py`,
run under a hard Docker `--memory` cgroup cap — the only reliable stop, since the explosion is too fast for userspace
RSS polling to catch):

1. `read_venues()` (`features_service/sports/data/gcs_mappings.py`) returns `venue_id=""` (empty string) for **all 591
   rows** — confirmed via direct inspection of the cached pipeline DataFrame (`venues['venue_id'].nunique() == 1`, value
   is `''`). This is a genuine bug: the RAW source parquet
   (`gs://instruments-store-sports-prd-central-element-323112/sports_reference/venues/venues.parquet`) has 591 correctly
   distinct real venue names (`OLD_TRAFFORD`, `ST_JAMES_PARK`, etc.) when read directly — `read_venues()`'s own
   column-mapping/normalization is discarding them.
2. Separately, `fixtures`/`fixtures_all`'s `venue_id` column is **also** `""` for 100% of both today's (149) and
   historical (30,447) rows — a second, independent upstream normalization gap (not yet traced to its exact source file
   — likely `gcs_normalizers.py` or the fixtures reader).
3. `_compute_venue_features` (`features_service/sports/exporters/derived_features_helpers.py:501-699`) does THREE
   `pd.merge(..., on="venue_id"/"away_venue_id", how="left")` calls against `venues`-derived tables with **no
   duplicate-key guard** — unlike the sibling `compute_weather_for_fixtures`
   (`features_service/sports/exporters/_weather_fetcher.py:42`), which already has a
   `.drop_duplicates(subset=["venue_id"])` with an explicit comment:
   `"Dedup venues by venue_id — duplicates cause combinatorial explosion in merge"` (i.e. this exact bug class was
   already hit and patched once, just not in this sibling function).
4. Because BOTH sides of the merge share the identical constant empty-string key, every venue merge becomes a full
   CARTESIAN PRODUCT. Confirmed via row-count bisection with exact arithmetic:
   - `venue_coords` merge (`derived_features_helpers.py:527`): `149 (target_fixtures) × 591 (venues) = 88,059` rows —
     confirmed exactly (bisection printed `88059`, and `149 * 591 == 88059`).
   - `away_coords` merge (`derived_features_helpers.py:572`): `88,059 × 591 ≈ 52,038,869` rows — this second cartesian
     multiplication is what actually exhausts memory (the crash happens between these two merges in every reproduction:
     full-pipeline runs died right after this point at 11.5GB/41GB RSS depending on the run; the bisection script died
     between printing `[3] after home_venues merge: 88059 rows` and `[4]`, i.e. during the `away_coords` merge, under
     both a 6GB and 10GB hard memory cap).

**Fix needed** (not yet implemented — flagging per the "capture discoveries as plan todos immediately" rule, see new
Todo below): (a) defensive guard — add `.drop_duplicates(subset=["venue_id"])` /
`.drop_duplicates(subset=["away_venue_id"])` before each venue merge in `_compute_venue_features`, mirroring the sibling
weather-fetcher's existing pattern, so a degenerate/duplicate-key venues table can never cartesian-explode a merge
again; (b) root-cause fix — `read_venues()` and the fixtures normalizer both need to stop collapsing `venue_id` to an
empty string (investigate the actual column mapping/normalizer logic; the raw source data has real values).

**Safety note for whoever verifies this**: reproducing this bug against real GCS data is dangerous on a shared host —
the cartesian join explodes from ~1.4GB to 40GB+ RSS in low single-digit seconds, too fast for a userspace RSS-polling
watchdog to reliably catch (confirmed: mine missed it once). Use a REAL kernel-enforced memory cap (e.g.
`docker run --memory=<N>g --memory-swap=<N>g`) around any repro/verification run, not `RLIMIT_AS` (caps virtual memory,
not RSS — false-triggers on numpy/grpc) and not a polling watchdog (too slow for this specific explosion).

Profiling scripts committed as reusable evidence/tooling (all `Lifecycle: temporary`, delete once this issue closes):
`scripts/sports/profile_2018_06_17_memory.py`, `scripts/sports/profile_cache_inputs.py`,
`scripts/sports/profile_venue_context_bisect.py`.

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

- [x] ✅ [DATA] P1. Profile the features-service sports compute for date 2018-06-17 (`memray`/`tracemalloc`) to find the
      exact unbounded-memory allocation site among the historical-fixtures join and rolling calculators. (repo:
      features-service) — features-service@b05f48ad. Built a synthetic repro at the incident's exact reported scale
      (30,447 historical fixtures / 60,894 team-history rows / 149 today-fixtures / 94 leagues) and measured RSS per
      calculator stage. `team_form`/`team_xg`/`team_goals`/`h2h`/`promoted_team`/`venue_context` all stayed flat (~437MB
      total, no growth). Found the real site: `shot_quality_calculator._get_team_shots` re-copied and re-merged the FULL
      `xg_shots` x `fixtures_all` frames INSIDE a per-fixture x per-side loop (298 full merges for a 149-fixture batch,
      called from `compute_shot_quality_batch` via `run_new_calculators`, downstream of the last log line the incident
      report could see — buffered stdout on the OOM-killed process). No join-cardinality guard existed, so a duplicate
      `fixture_id` surviving upstream dedup (this codebase has a documented history of str/int64 dtype-mismatch dedup
      gaps) could additionally explode the join into a cartesian product.
- [x] ⚠️ REOPENED (2026-07-13, slot 12) [DATA] P1. Bound/fix the identified allocation site so this date (and any date
      with a similarly dense historical-snapshot lookback) computes within a fixed, reasonable memory ceiling (e.g.
      under 16GB). (repo: features-service) — features-service@b05f48ad shipped this precompute-once fix
      (`_build_team_shots_index` + `validate="many_to_one"` dedup guard) and it was marked done on a SYNTHETIC-scale
      benchmark. **Confirmed on real production data the same day the fix landed: the OOM is NOT resolved.** See the
      "Update — production re-test" section below for full evidence. Leaving the original checkmark + evidence in place
      (the profiling + the precompute-once change are real, verified improvements) but the completion claim itself does
      NOT hold — treat this todo as still open pending a second investigation.
- [ ] [INFRA] P2. Fix `lc_log_upload_trap_block`'s EXIT_STATUS to reflect an OOM-killed/crashed workload subprocess's
      real exit code, not just the wrapper shell's — so a crashed shard is never reported as `EXIT_STATUS=0`. (repo:
      deployment-service) — NOW CONFIRMED WORSE than originally scoped: the 2026-07-13 re-test found the OOM killer can
      take down the entire `google-startup-scripts.service` systemd unit (wrapper shell + tee + python child all
      killed), not just the workload subprocess — so the existing trap may not even get a chance to run. Verify the
      trap's EXIT-signal path survives a whole-unit OOM kill, not only a clean subprocess non-zero exit.
- [x] ✅ [DATA] P0. **NEW (2026-07-13, slot 12) — real root-cause investigation needed, the b05f48ad fix is insufficient
      on production data.** Re-profile (`memray`/`tracemalloc`) against the REAL 2018-06-17 GCS data (not a synthetic
      repro) end-to-end through `run_new_calculators`, because the shot_quality precompute fix did not stop the OOM.
      Also profile 2018-06-18 (a `--force` single-date run) — RSS climbed steadily past 13GB and was still rising when
      killed, on a date with only 24 target fixtures (vs 149 on -17), which points at the 400-day HISTORICAL LOOKBACK
      itself (independent of today's fixture count) as the dominant cost, not (only) shot_quality. Suspect candidates:
      another per-fixture/per-team full-frame merge elsewhere in `run_new_calculators`'s calculator chain that the
      synthetic benchmark's calculator list didn't cover (the synthetic repro checked
      `team_form`/`team_xg`/`team_goals`/`h2h`/`promoted_team`/`venue_context` — NOT the full calculator set actually
      invoked for these two dates), or the `_read_per_league_subpartitions` 33-shard-concat fallback path scaling badly
      when repeated across the historical lookback window rather than just once for today. (repo: features-service)
      **UPDATE (slot-8, same day): this todo is ANSWERED** — see "Additional finding" above + the two new todos
      immediately below. `venue_context` (via `_compute_venue_features`) DOES explode on real data despite the synthetic
      benchmark showing it flat — the synthetic repro used clean, distinct `venue_id` values, so it never exercised the
      degenerate all-empty-string `venue_id` the real GCS data actually has. This also explains the 2018-06-18
      (24-fixture) case: `24 × 591 = 14,184` rows, then re-multiplied by 591 again ≈ 8.4M rows — smaller than -17's ~52M
      but still large enough to explain the observed steady multi-minute RSS climb toward the OOM ceiling. The
      `_read_per_league_subpartitions` fallback was considered and ruled out as the dominant cost — it's a same-day,
      one-time 33-shard read, not something repeated across the 400-day historical window. **CHECKBOX FLIPPED (slot 10,
      2026-07-13)**: the literal ask here (re-profile 2018-06-17/2018-06-18 against real GCS data, find the root cause)
      was fully carried out and answered in-body the same day (slot-8's "Additional finding" section above) and
      independently verified by the shipped fix (`features-service@c3e3ebfe`) — todo below ("After the above two todos
      land, re-verify...") confirms both dates now complete cleanly against real production data (149/24 rows, ~617MB
      peak RSS each), already `[x]`. Leaving this unflipped any longer was the "done-but- unchecked" pattern, not a live
      gap. **Does NOT close this issue doc** — the "THIRD recurrence" section further down found a DIFFERENT,
      still-unresolved crash site (`compute_shot_quality_batch`, 3 unrelated poison dates: 2018-01-06 / 2019-08-17 /
      2025-08-10), tracked by its own still-open P0 todo at the bottom of this list. No code change in this commit — the
      fix was already shipped; this is a documentation-only correction of a stale checkbox.
- [x] ✅ [DATA] P0. Add a duplicate-key merge guard to `_compute_venue_features`
      (`features_service/sports/exporters/derived_features_helpers.py:501-699`) —
      `.drop_duplicates(subset=["venue_id"])` before the `venue_coords` merge (line ~516-527) and
      `.drop_duplicates(subset=["away_venue_id"])` before the `away_coords` merge (line ~561-572), mirroring the
      existing dedup pattern already in the sibling `compute_weather_for_fixtures`
      (`features_service/sports/exporters/_weather_fetcher.py:42`). Without this, a degenerate `venue_id` value (see
      next todo) turns these `pd.merge(..., how="left")` calls into a cartesian product — confirmed 149×591=88,059 rows
      then 88,059×591≈52M rows, exhausting host memory. Add `validate="many_to_one"` too so any future recurrence fails
      loudly instead of silently ballooning. (repo: features-service) — **DONE, slot 14, features-service@c3e3ebfe.**
      Shipped a `_dropna_key()` guard instead of plain `.drop_duplicates(subset=["venue_id"])`: a blank/NaN join key is
      now dropped from the merge's right side entirely (never matches, same as pandas' native NaN behavior), which is
      strictly safer than dedup-to-one-row — dedup-to-one-row would still let 149/24 target fixtures all silently match
      the SAME arbitrary `""` venue (bounded rows, but wrong data); `_dropna_key` makes them honestly non-matching
      (NaN-filled venue columns) instead. Applied at all 4 vulnerable merge/groupby sites in the function (venue_coords,
      away_coords, the home_win_pct venue_stats groupby, and the clean-sheet-rate venue_hist groupby), not just the 2
      named here. See "Update — real root cause confirmed + fix shipped (slot 14)" below for full verification evidence.
- [ ] [DATA] P0. Root-cause + fix `venue_id` collapsing to an empty string: (1) `read_venues()`
      (`features_service/sports/data/gcs_mappings.py`) returns `venue_id=""` for all 591 rows even though the raw source
      parquet (`gs://instruments-store-sports-prd-central-element-323112/sports_reference/venues/venues.parquet`) has
      591 correctly distinct real venue names — find and fix the column-mapping/normalization bug; (2) separately,
      `fixtures`/`fixtures_all`'s `venue_id` is ALSO `""` for 100% of rows (today's + historical) — trace this to its
      normalizer (likely `gcs_normalizers.py` or the fixtures reader) and fix it too. **CAUTION when reproducing**: this
      cartesian join explodes from ~1.4GB to 40GB+ RSS in low single-digit seconds — too fast for a userspace
      RSS-polling watchdog; use a real kernel-enforced cap (`docker run --memory=<N>g --memory-swap=<N>g`), not
      `RLIMIT_AS` (caps virtual memory, not RSS — false-triggers on numpy/grpc before real growth). (repo:
      features-service) — **EXACT SITES NOW PINNED (slot 14, 2026-07-13):** both call sites named here plus a THIRD
      (`travel_calculator.py:182-184`) all carry the identical pattern —
      `pd.to_numeric(df["venue_id"], errors="coerce")` then `str(int(v)) if notna else ""`. The comments at all 3 sites
      say this normalizes a numeric id (`"173.0 → '173'"`) — but the real production `venue_id` is a non-numeric string
      code (`"OLD_TRAFFORD"` etc, confirmed 591/591 unique via direct raw-parquet read), so `pd.to_numeric` returns NaN
      for every row → collapses to `""` everywhere. This is NOT a quick fix I could take unilaterally: it's ambiguous
      whether the string code is now the sole canonical venue_id (delete the numeric round-trip) or whether a real
      numeric↔string id-space crosswalk is missing (bigger fix). Filed as a separate issue doc with the
      operator-decision framed as 3 options:
      `plans/active/issues/sports_venue_id_numeric_coercion_data_loss_2026_07_13.md`. The OOM-crash risk this todo
      partly motivated is CLOSED regardless (see Todo above) — this remaining piece is a correctness-only gap (venue
      features silently NaN, not a crash risk) tracked in the new issue doc, not blocking here.
- [x] ✅ [DATA] P1. After the above two todos land, re-verify the 2018-06-17 AND 2018-06-18 OOMs are actually resolved
      end-to-end (not just the `shot_quality_calculator` site fixed in Todo 2) — the pipeline must reach and complete
      `shot_quality_calculator` without first OOM-ing in `venue_context`, since venue_context runs several
      calculator-groups earlier in `export_derived_features`. Use `scripts/sports/profile_2018_06_17_memory.py` (this
      issue's committed profiling harness). Then `--force`-recompute both dates plus audit for other similarly-shaped
      dense-lookback dates across the full 2015-2019 era (not just these two — the 2018-06-18 finding suggests this is
      endemic to the era), and re-run `check_pipeline_completeness.py` / the manifest-cleanliness query for the full
      2015→present range. (repo: features-service) — **OOM-resolution half DONE (slot 14, features-service@c3e3ebfe)**:
      both `export_derived_features("2018-06-17")` and `("2018-06-18")` now complete fully against REAL production GCS
      data (149 rows × 578 cols and 24 rows × 578 cols respectively, ~620MB peak RSS each, reaching `shot_quality` and
      every other calculator with no crash). The `--force`-recompute-to-manifest half (actually running this against the
      live backfill fleet + the 2015-2019 era-wide dense-lookback audit + `check_pipeline_completeness.py`) is **NOT
      done** — that's real infra execution, tracked as a fresh todo below rather than silently implied by this
      checkmark.
- [ ] [DATA] P1. ~~NEW (slot 14, 2026-07-13) — now that the OOM-crash risk is closed (features-service@c3e3ebfe verified
      against real GCS data for both poison dates), resume `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo
      1's full-history 2015→present compute fleet (excluded/killed shards can re-include 2018-06-17/06-18), let it run
      to completion, then re-run `check_pipeline_completeness.py` / the manifest-cleanliness query for the full range to
      confirm no other dense-lookback date still crashes. This is the actual infra-execution half of the todo above.~~
      **THIS CLAIM WAS WRONG — see "Update — THIRD recurrence, 2 more independent poison dates found (2026-07-13, slot
      14 continued)" below.** The OOM-crash risk is NOT closed; c3e3ebfe (venue_context fix) was necessary but not
      sufficient. (repo: features-service, deployment-service for the VM relaunch)
- [ ] [DATA] P0. **NEW (slot 14, 2026-07-13, continued session)** — root-cause the STILL-LIVE OOM site. Strong new
      evidence points at `compute_shot_quality_batch` (`features_service/sports/exporters/derived_new_calculators.py`
      `run_new_calculators`), the step immediately after `advanced_stats` in the Phase-4 calculator chain — see the
      "Update" section below for 3 independent same-signature crashes (2018-01-06, 2019-08-17, 2025-08-10) all dying at
      that exact log position, on the ALREADY-FIXED (c3e3ebfe) codebase. Profile `compute_shot_quality_batch` against
      real GCS data for at least one of these 3 dates (memray/tracemalloc, real kernel-enforced memory cap per this
      doc's own earlier caution — `docker run --memory=<N>g`, not `RLIMIT_AS`). This directly answers what todo #207
      (REOPENED) already flagged as unconfirmed-fixed. (repo: features-service)

## Update — production re-test (2026-07-13, slot 12, same day the b05f48ad fix landed)

Picked up `sports_p2_features_history_to_ml_ready-002` (Todo 3 gate). Found `fss-backfill-vm-3`/`fss-backfill-vm-4` (of
the running 10-VM fleet) both OOM-killed — `fss-backfill-vm-3` cleanly (process gone, `dmesg` OOM at 2018-01-06, within
its own 2017-04-22→2018-06-16 range, unrelated poison date); `fss-backfill-vm-4` at 2018-06-18, the FIRST date of its
post-exclusion range (2018-06-17 had already been excluded by an earlier dispatch). Both crashes were at **10:08-10:09
UTC — 31 minutes BEFORE `features-service@b05f48ad` landed at 10:40:04 UTC** — i.e. both shards were still running the
pre-fix codebase when they died, so this was not yet evidence against the fix.

Repackaged the VM tarball fresh from a local checkout confirmed to have `b05f48ad` in `HEAD`, and gap-filled both shards
with their ORIGINAL full ranges (`--skip-existing` default):

- **`fss-backfill-vm-3`**: relaunched clean, ran the fixed codebase, completed 49+ dates with no issue (2017-04-22
  onward, past the earlier poison point) — this shard's earlier crash looks unrelated to the shot_quality bug (or was
  incidentally fixed as a side effect).
- **`fss-backfill-vm-4`**: relaunched on the fixed codebase (`b05f48ad` confirmed present in the packaged tarball),
  range 2018-06-17→2019-08-11 (re-including the previously-excluded date since the fix was supposed to resolve it,
  matching this issue doc's own Todo 4 recommendation). **OOM'd again on 2018-06-17 at 11:25:58 UTC** — same
  `total-vm:20572684kB, anon-rss:15810800kB` signature as the original pre-fix incident, i.e. the exact allocation
  ceiling was unchanged by the fix. Worse than the original incident: this time `dmesg`/`journalctl` show the OOM killer
  took down the ENTIRE `google-startup-scripts.service` systemd unit (wrapper shell PID 4510, `tee`, AND the python
  child) — `Consumed 2min 12.990s CPU time, 15.1G memory peak` — not just the workload subprocess, so the shard's own
  per-date retry loop never got a chance to run and move to the next date; the VM was a permanent zombie (GCE `RUNNING`,
  zero live processes) until manually recreated.

Relaunched `fss-backfill-vm-4` a second time excluding 2018-06-17 again (range 2018-06-18→2019-08-11) to test whether
the bug was specific to that one date. **It was not**: on 2018-06-18 (only 24 target fixtures, vs 149 on -17) the
`features-servic` process climbed steadily — 12.5GB → 12.6GB → 13.05GB RSS over ~5 minutes, state `R` (actively
computing, not hung/deadlocked), CPU time climbing in step — a slower but qualitatively identical unbounded-growth
trajectory clearly heading toward the same OOM ceiling. Killed the VM manually after confirming this rather than waiting
for a second OOM (no value in burning more SPOT compute reproducing the same signature a third time).

**Conclusion**: the shipped fix's own synthetic benchmark was scoped to the specific calculator set it profiled
(`team_form`/`team_xg`/`team_goals`/`h2h`/`promoted_team`/`venue_context` + the shot_quality site itself) and to ONE
date's exact data shape — it does not generalize to the real GCS data for this era, and the fact that an ADJACENT date
with 6x fewer target fixtures shows the same growth pattern strongly suggests the dominant cost is the shared 400-day
historical-lookback build itself (done once per date regardless of today's fixture count), not the per-fixture
shot_quality loop that was fixed. **Did not attempt a second inline fix** — this needs the same rigor as the first
profiling pass (memray/tracemalloc against REAL data, not synthetic), which is a real investigation, not a quick patch;
guessing again risks another false "fixed" claim. Todo 3 of the parent plan (`sports_p2_features_history_to_ml_ready`)
remains genuinely blocked — full-history compute cannot be honestly called clean while a confirmed-reproducible,
whole-shard-killing OOM sits unresolved in the 2015-2019 era. Not attempting `/skip-current-task` yet — filing this
update first per FINDINGS CLOSURE (§4.5), since the previous "done" claim needs correcting before another dispatch
trusts it.

**Cross-reference (slot-8, same day)**: this production re-test's "Conclusion" hypothesis (dominant cost is the shared
400-day historical-lookback build, independent of today's fixture count) is CONFIRMED, but not via the historical-read
itself (that step's tracemalloc/RSS delta measured flat and small in the "Additional finding" profiling above) — the
actual mechanism is `_compute_venue_features`'s cartesian-join explosion, which scales with `target_fixtures × 591` (not
with the 400-day lookback's row count directly), fully explaining why 24-fixture 2018-06-18 also climbs toward the same
ceiling as 149-fixture 2018-06-17. See "Additional finding" above for the exact root cause and the two new P0 todos for
the fix.

## Update — fix shipped + verified against real GCS data (slot 14, 2026-07-13)

Independently reproduced slot-8's root cause via a different method (in-process instrumentation of the real
`_run_calc`/merge call sites rather than a Docker-memory-capped bisection script — no repo scripts committed, kept as
scratchpad-only tooling since the finding itself is what matters) and confirmed the identical numbers: real-pipeline
`venues['venue_id'].nunique()==1` (value `''`), `target_fixtures['venue_id']` `''` for all rows, `home_venues` merge
14,184 rows exactly (`24 × 591` for the -18 date), `away_coords` merge 8,382,744 rows exactly (`14,184 × 591`) —
matching slot-8's `149 × 591 = 88,059` then `88,059 × 591 ≈ 52M` for -17 (both are the same mechanism, just scaled by
the date's target-fixture count).

**Traced the venue_id corruption to its exact root**, extending slot-8's "not yet traced to its exact source file" note
on the fixtures side: THREE call sites (`gcs_normalizers.py:188-190` `normalize_fixtures`, `gcs_mappings.py:158-160`
`read_venues`, `travel_calculator.py:182-184`) all force `venue_id` through `pd.to_numeric(errors="coerce")` →
`str(int(v)) if notna else ""`, with comments assuming venue_id is numeric (`"173.0 → '173'"`). Real production venue_id
is a non-numeric string code (`OLD_TRAFFORD` etc, confirmed 591/591 unique via direct raw-parquet read bypassing all
three normalizers) — `pd.to_numeric` returns NaN for every row, so every site collapses venue_id to `""`. This is the
root of BOTH slot-8's findings #1 (`read_venues`) and #2 (fixtures normalizer) — same bug, same shape, three sites.

**Shipped a fix scoped to the OOM-crash risk** (`features-service@c3e3ebfe`, quickmerged to `live-defi-rollout`): added
`_dropna_key()` to `_compute_venue_features` so a blank/NaN join key is dropped from a merge's right side before joining
— the merge behaves the way pandas' native NaN join-key semantics already do (never matches), making every
`venue_id`/`away_venue_id` merge in the function cartesian-proof **independent of whether the upstream normalization bug
is ever fixed**. This is deliberately NOT the same as slot-8's suggested `.drop_duplicates(subset=["venue_id"])` —
dedup-to-one-row would still let every fixture silently match the single arbitrary `""`-keyed venue row (bounded, but
wrong data); dropping the blank key entirely gives honest-absence NaN instead, consistent with
`codex/02-data/honest-absence-downstream-handling.md`. Also fixed two secondary allocation sites the same profiling pass
surfaced in the same function: two `.groupby().apply(lambda...)` calls (home_win_pct, clean_sheet_rate) and a
raw-GroupBy-iteration dict comprehension (`_away_games_cache`) — all replaced with vectorized groupby aggregations.

**Verified against real production GCS data** (not synthetic): `export_derived_features()` now completes fully for BOTH
poison dates —

- `2018-06-17` (149 target fixtures, the original incident date): 149 rows × 578 columns, final peak RSS 617.7MB.
- `2018-06-18` (24 target fixtures, the "still climbs with 6x fewer fixtures" date): 24 rows × 578 columns, final peak
  RSS 616.6MB.

Both previously never completed at all — unbounded RSS growth past 12GB (-18) and past 32GB confirmed OOM-killed on both
e2-standard-4 and e2-standard-8 (-17). 101/101 existing `test_derived_features_helpers.py` unit tests still pass; full
`quality-gates.sh` green on the shipped commit (sentinel-verified).

**The deeper venue_id normalization defect is NOT fixed** — `_dropna_key()` makes the crash impossible regardless, but
venue-context features (`home_win_pct`, `home_venue_clean_sheet_rate`, `travel_distance_km`, etc. — the
`VENUE_CONTEXT_COLUMNS` set) are still silently NaN for every date, not just these two, since the join key is still
blank. This is a genuine correctness defect (likely present since whenever `venues.parquet` moved to string codes, not
just for 2018 dates) that needs an architecture decision on the canonical venue_id format before a real fix — filed as
`plans/active/issues/sports_venue_id_numeric_coercion_data_loss_2026_07_13.md` per the CLAUDE.md big-finding rule
(data-correctness, cross-cutting, silent). The OOM this issue doc tracks is resolved; the venue_id correctness gap is
tracked separately so it isn't lost, but is not this issue's remaining blocker.

**Secondary noise finding** (not investigated further, flagged for whoever picks up the venue_id issue): while
re-verifying on 2018-06-17, the `elo`/`manager`/`travel` calculator group printed a large volume of full
`Traceback (most recent call last):` output for
`Skipping fixture row N: Cannot compare tz-naive and tz-aware timestamps` — caught and skipped per-row (not a crash),
but logging the full traceback on every occurrence instead of a one-line warning is noisy/expensive at scale and could
mask real errors in the same log stream.

## Update — THIRD recurrence, 2 more independent poison dates found (2026-07-13, slot 14 continued session, several hours after the "OOM-crash risk is closed" claim above)

**This session's own prior claim (the now-struck-through todo above) was WRONG.** Picked up
`sports_p2_features_history_to_ml_ready-001` (Todo 1) for a routine fast re-verify of the 10-VM fleet launched
~09:18-09:25 UTC today (per that plan's slot-11 entry) — a fleet that launched AFTER `features-service@c3e3ebfe` (the
venue_context fix) was already on `live-defi-rollout`, so every shard in it started with the fix already present. Found
**3 of the (by then) 3 still-nominally-running shards were ALL OOM-zombies** (GCE status `RUNNING`, but no
`features_service` process, idle load average, confirmed via `dmesg`):

| shard (original)     | assigned range          | died on date                                     | anon-rss at kill | era                                                                    |
| -------------------- | ----------------------- | ------------------------------------------------ | ---------------- | ---------------------------------------------------------------------- |
| `fss-backfill-vm-10` | 2025-05-17 → 2026-07-13 | **2025-08-10** (86th date, 85 completed clean)   | ~15.8GB          | **modern, non-history**                                                |
| `fss-backfill-vm-3`  | 2017-04-22 → 2018-06-16 | **2018-01-06** (260th date, 259 completed clean) | ~15.8GB          | early history, but NOT one of the two previously-profiled poison dates |
| `fss-backfill-vm-5`  | 2019-08-12 → 2020-10-05 | **2019-08-17** (6th date after a fresh restart)  | ~32GB            | mid-history                                                            |

All 3 had EXIT_STATUS unwritten (the known `lc_log_upload_trap_block` gap, todo above) and were genuine zombies (VM
`RUNNING`, GCE billing continuing, zero live work) — not caught by any automated watchdog. `vm-3`'s poison date
(2018-01-06) is the SAME date a much earlier dispatch (slot-12, same day) found this exact shard OOM-killed on,
gap-filled once ("clean relaunch... progressing normally"), and which then progressed 254 MORE dates before dying at the
identical date again — i.e. this is a second, independent, reproducible crash at that date, not a fluke.

**Critical new evidence — all 3 crashes share an IDENTICAL log position**, immediately after the exact log line
`Calculator advanced_stats: 62 columns added (... all-zero)`, with nothing further logged before the kill. Per
`features_service/sports/exporters/derived_new_calculators.py::run_new_calculators`, the calculator chain is
`_run_phase4_history_calculators` → `_run_phase4_provider_calculators` (which includes `advanced_stats`) →
**`compute_shot_quality_batch`** (shot-quality). None of these 3 dates ever produced a `shot_quality`-related log line,
meaning the crash consistently happens inside or immediately upon entering `compute_shot_quality_batch` — the exact
function the ALREADY-REOPENED todo above (b05f48ad, `_build_team_shots_index` precompute-once fix) targeted and which
this doc's todo #207 already flagged as "confirmed on real production data the same day the fix landed: the OOM is NOT
resolved." This session's 3 new same-signature crashes, spanning 3 unrelated eras (2018/2019/2025) that share no obvious
"dense historical lookback" characteristic in common (2025-08-10 has only ~8.5k combined fixtures vs the original
2018-06-17 incident's ~30k), is strong evidence the b05f48ad precompute fix did not actually bound the allocation, or a
different unbounded site exists in the same function. **Not investigated further this session** (needs real profiling
per this doc's own established rigor bar, not a guess-fix) — see the new P0 todo above.

**Recovery action taken** (not a fix, just restoring forward progress on the unaffected 2015→present compute): deleted
all 3 zombie VMs, gap-filled each shard's remaining range EXCLUDING its poison date via the collision-free
`launch-features-vm.sh` (all 5 code tarballs confirmed fresh at launch, including `features-service@208516e6` — ahead of
c3e3ebfe): `features-sports-sports-20260713-200043` (2025-08-11→2026-07-13), `-200456` (2018-01-07→2018-06-16),
`-200525` (2019-08-18→2020-10-05). All 3 confirmed genuinely computing (not just booted) via log tail within minutes of
launch. The 3 poison dates (2018-01-06, 2019-08-17, 2025-08-10) remain uncaptured pending the new P0 root-cause todo.

**What I did NOT do**: did not attempt to guess-fix `compute_shot_quality_batch` inline (this doc's own established
precedent is that guessed fixes here don't hold — see the b05f48ad history). Did not exhaustively scan the rest of the
full-history fleet beyond the 3 shards this dispatch's fast re-verify covered (vm-1/2/6/7/8/9 all show clean
`EXIT_STATUS=0` completions this session, so are not part of this finding). Given 3 independent, unrelated-era
recurrences in one session alone, flagging as a **big finding per CLAUDE.md** (data-correctness, cross-cutting,
contradicts a same-day "resolved" claim already acted on by other dispatches) — escalating to the operator via
`/blocked` rather than silently re-closing this loop a third time.
