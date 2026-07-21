---
doc_type: issue
title:
  Calendar-guard early returns in understat/weather/footystats orchestrators call record_expected_empty() but never
  .write() — silently discarded honest-absence writes
summary:
  "Diagnosed while re-running the understat blank-reason EU residual closer (sports_p2 item #4): the closer processed
  413 dates cleanly (0 raised exceptions) yet the manifest showed zero change even after a forced full consolidation.
  Traced to a missing `.write()` call on 2 early-return guard paths per function in understat.py, weather.py, and
  footystats.py — record_expected_empty() buffers records on a per-call ManifestWriter instance, but without an explicit
  .write() the buffered records are never moved into the module-level flush buffer and are lost when the function
  returns and the instance is discarded."
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [manifest, honest-absence, data-correctness, sports, understat, weather, footystats, silent-write-loss]
related:
  [
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md,
    plans/active/issues/manifest_atexit_drain_races_asyncio_shutdown_2026_07_09.md,
  ]
created: 2026-07-09
parent_epic: sports_master
priority: P0
source: [plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-09
---

## What I found

Task `sports_p2_history_reference_and_odds_2015_to_present-016` (item #4) was blocked on a 190 XG / 2,065 XG_SHOTS
blank-`error_reason` `expected_unattempted` residual for understat big-5 native leagues. The existing closer script
(`scripts/backfill/understat_eu_residual_closer_2026_07_08.py`) force-refetches exactly those dates via the real
per-date capture path (`_fetch_understat_xg` / `_run_understat_shots_date`, `force=True`), which correctly resolves each
date to either real captured data or a typed `empty_confirmed` reason.

Ran it (v3): `processed=413 raised=0`, "ALL DATES RESOLVED". Re-verified via a **fresh Python process** reading the
canonical index directly (not the closer's own in-process self-shard-overlay read, which is unreliable per the prior
CAS-race incident) — **byte-identical to pre-run counts**, even after a manually forced full consolidation
(`python -m unified_trading_library.manifest_consolidator --force`, `shards=2` processed, neither matching the closer's
per-VM shard). The closer's shard file never existed in `_index/per_vm/` at all.

**Root cause** — a single-date reproduction (`_fetch_understat_xg(date="2026-06-01", force=True)` +
`flush_all_live_writers()`) showed `flush_all_live_writers() == {}` (nothing pending) even though the function had just
executed the season-window guard and called `record_expected_empty()` in a per-league loop. Reading
`ManifestWriter.write()`'s docstring (`unified_trading_library/manifest_writer/_writer_io.py:213-253`) confirmed:
`record_*()` calls only append to the INSTANCE's local `_records` list; `.write()` is what moves those records into the
MODULE-LEVEL pending buffer (`_add_to_write_buffer`). Reading `instruments_service/engine/orchestrator/understat.py`
line-by-line confirmed both early-return guard blocks per function — (1) the coverage-start/known-gap guard and (2) the
season-window guard — call `record_expected_empty()` in a loop then `return counts` with **no** `.write()` call, unlike
every OTHER exit path in the same functions (which all call `.write()` before returning, e.g. lines 258/316/348 in the
pre-fix `_fetch_understat_xg`). Since a fresh `ManifestWriter` instance is created per function call
(`xg_manifest = _orch.ManifestWriter(...)` at the top of the function) and never retained past the early return, the
buffered records are simply discarded — never reaching even the module buffer, let alone GCS.

**This bug has existed since these guard blocks were introduced** (season-window guard commit history predates this
session) — every calendar-pre-skip write through these 2 paths, for understat, has been silently lost for its entire
lifetime. Dispatched a follow-up scan (Explore sub-agent) across the sibling sports orchestrators:

| File            | Function                        | Missing-`.write()` sites                                                                      | Status                 |
| --------------- | ------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------- |
| `understat.py`  | `_fetch_understat_xg`           | 2 (coverage-start/known-gap; season-window)                                                   | **FIXED** this session |
| `understat.py`  | `_run_understat_shots_date`     | 2 (same 2 guards)                                                                             | **FIXED** this session |
| `weather.py`    | `_fetch_weather_data`           | 2 (same 2 guards)                                                                             | **FIXED** this session |
| `footystats.py` | `_fetch_footystats_predictions` | 2 (same 2 guards)                                                                             | **FIXED** this session |
| `footystats.py` | `_fetch_footystats_matches`     | 2 (same 2 guards)                                                                             | **FIXED** this session |
| `sfi.py`        | `_fetch_sfi_data`               | 0 — guards set a flag instead of early-returning, single trailing `.write()` covers all paths | Clean, no bug          |
| `footystats.py` | `_fetch_footystats_odds`        | 0 — no calendar-guard blocks in this function                                                 | Clean, no bug          |

All 10 confirmed sites fixed in `instruments-service@920b303` by adding the missing `.write()` call (matching the
pattern already used by every other exit path in the same functions).

**Verified end-to-end**: re-ran the understat closer (v5, with the fix + the pre-exit-drain fix from the sibling issue
doc) against prod GCS. `ManifestWriter: per-VM shard updated (4130 total entries, 4125 new, process_final=True)` —
confirms the fix causes records to actually reach a shard now (v3/v4 runs, pre-fix, never produced this log line after
the very first entry). Post forced-consolidation, independently re-verified in a fresh process: understat XG/XG_SHOTS
blank-reason `expected_unattempted` for big-5 native leagues dropped from **185/2,065 → 0/0**, `attempted_failed = 0`
(no over-broad-404). Item #4's gate is now genuinely met.

## Why it matters

1. **Silent data loss, not just a stale-looking manifest.** This is the same failure class the whole plan has been
   hunting (blank-reason `expected_unattempted` residuals) — except the root cause here isn't upstream enumerator noise,
   it's the FIX PATH itself silently no-op'ing. Every attempt to close these residuals via the real per-date capture
   path for understat/weather/footystats was doomed to appear to succeed (0 raised, "ALL DATES RESOLVED") while writing
   nothing.
2. **Not sports-specific in shape.** The `ManifestWriter(...).record_*(...); ...; return` (no `.write()`) anti-pattern
   is a generic footgun for ANY orchestrator with an early-return guard — worth a lint/QG check (see recommended
   decision) rather than relying on per-file code review to catch it.
3. **Understated the true severity of already-parked items.** Items #1 (weather) and #2 (SFI) in this same plan already
   flipped ✅ — SFI is clean (confirmed above), but weather's bug means any historical attempt to close a weather
   blank-reason residual via its per-date fetch path may have silently failed the same way. Re-verification of weather's
   flipped gate is a recommended follow-up, not yet done this session (out of this task's scope — filed as a todo
   below).

## Recommended decision

- [x] ✅ [CODE] P0. Fix the 10 confirmed missing-`.write()` sites in understat.py (4), weather.py (2), footystats.py (4)
      (repo: instruments-service). — `instruments-service@920b303` (slot-2 sonnet/high, this session).
- [x] ✅ [VERIFY] P1. Re-verify weather's already-flipped gate (item #1 in
      `sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md`) now that its early-return write-loss bug is
      fixed — confirm no blank-reason residual was silently masked by a prior "fix" that never persisted. (repo:
      unified-trading-pm) — **CONFIRMED HOLDS.** Live read of `read_availability_index` (shard-merged, single-walk-safe)
      for `(data_type=WEATHER)`: **0** blank-reason (`capture_status=expected_unattempted`, `error_reason=""`) rows
      within the original flip window (2019-03-02→2026-06-27) — the 2026-06-27 flip's `pending_fetch=0` claim was NOT
      corrupted by this bug. In-window breakdown: `empty_confirmed=244,662`, `captured=12,036`, `attempted_failed=51`
      (matches the flip's cited `attempted_failed=51` exactly). **Side finding (adjacent, not this todo's scope to
      fix)**: ALL 379 current blank-reason WEATHER rows fall AFTER the flip window (dates 2026-06-30→2026-07-09) — this
      is the same residual the sibling plan's item #6 attributed to an unverified "daily-pipeline-lag" hypothesis. Given
      weather.py's season-window guard resolves via `record_expected_empty()`→typed `empty_confirmed` (not a
      blank-reason write itself) and the missing `.write()` was live through 2026-07-09 01:27 UTC, a dropped
      guard-resolution leaves the enumerator's `expected_unattempted` seed row stuck exactly at this signature — far
      more consistent with this SAME write-loss bug (guard firing for dates where weather's full expected-league set is
      off-season, e.g. northern-hemisphere summer break) than with "lag." Not independently re-verified post-fix (the
      fix landed 920b303 same day as most of these dates — the daily forward-poll needs to re-run against the fixed code
      to resolve them); flagged in the plan's Progress Log for whoever next picks up item #6. — unified-trading-pm (this
      doc, no code change needed; 920b303 already shipped by the prior session). Slot-4, 2026-07-09.
- [x] ✅ [SCRIPT] P2. Add a QG lint check (or extend an existing one, e.g. STEP 5.7x in
      `codex/06-coding-standards/quality-gates.md`) that flags a `ManifestWriter`/`record_*()` call followed by a
      `return` with no `.write()`/`.flush()` on that variable before the function exits, when OTHER exit paths in the
      same function DO call it — generalizes this fix into a standing guard instead of relying on manual review. (repo:
      unified-trading-pm) — Wired as **STEP 5.102** (new checker, not an extension of 5.7x — those steps are unrelated
      `pipeline_mode=`/other checks). `scripts/quality_gates/check_manifest_writer_missing_write_before_return.py`: AST
      block-scoped scan (function-scoped, non-nested) tracking per-variable "unflushed record pending" state across
      sequential statements per block; flags a `return` where a `record_*()`-called var has no preceding
      `.write()`/`.flush()` in the SAME block, gated to only report when another exit path in the SAME function DOES
      write (avoids flagging helpers that never flush on any path). Validated against ground truth: run against the
      pre-fix (920b303~1) understat.py/weather.py/footystats.py/sfi.py — found the exact 10 known sites (0 false
      positives/negatives vs. the hand-diagnosis), correctly silent on sfi.py (confirmed clean). Wired
      `scripts/quality-gates-base/base-service.sh` STEP 5.102 (same per-repo-scope shape as STEP 5.70) +
      `manifest_writer_missing_write_baseline.yaml` (0-entry bootstrap — a full workspace sweep found 0 remaining
      occurrences) + doc section in `codex/06-coding-standards/quality-gates.md` +
      `test_check_manifest_writer_missing_write_before_return.py` (10 unit tests). — unified-trading-pm (this session,
      slot-4, 2026-07-09).
- [x] ✅ [INVESTIGATE] P2. Audit whether the same early-return-no-write anti-pattern exists in non-sports orchestrators
      (TradFi/DeFi/CeFi calendar-guard paths) — the pattern is generic, not sports-specific; this session only scanned
      the sports orchestrator files named in the sibling plan. (repo: instruments-service) — **CLEAN, no bug found.**
      Audited every `engine/orchestrator/*.py` function that OWNS a `ManifestWriter` instance (created it directly, not
      received one as a parameter) in the TradFi/DeFi/CeFi paths — `grep -rl "ManifestWriter("` across the package found
      instantiation sites in `catalogue.py`, `process_completeness.py`, `process_write.py`, `process_zero_records.py`,
      `process_fetch.py`, `process_preflight.py`, `process_enrichment.py` (+ the sports files already
      fixed/confirmed-clean in the sibling session). For each, traced every exit path against every `record_*()` call
      site: `catalogue.py:_write_catalogue_record` (single-exit, `.write()` unconditional);
      `process_completeness.py:_finalize_completeness` (`_failed_manifest`/`_thin_manifest` each call `.close()` inside
      the SAME conditional block before any return), `:_completeness_and_retry` (`_empty_ok_manifest.close()`
      same-block), `:_retry_missing_venues` (`retry_manifest.close()` same-block, loop `continue`/`break` never skip
      it); `process_write.py:_write_all_venues` (single-exit — the ONLY return is the final line, reached after
      `manifest.close()`/`_extra_manifest.close()` for every lazily-created per-bucket writer in `_extra_manifests`);
      `process_zero_records.py:_zero_records_non_sports` (`manifest.write()` at line 536 precedes its only early return
      at 552-555; the function's other exit is a `raise RuntimeError` — loud failure, not the silent-discard failure
      mode this bug class is about). **Root-cause reason the bug didn't reproduce here**: every non-sports
      owning-function in this codebase either (a) is single-exit (one return, always past the flush), or (b) creates the
      writer AND flushes it within the same tight conditional block before branching to any early return — unlike
      understat.py/weather.py/footystats.py, which created a writer near the TOP of a long multi-branch function then
      only flushed on some of the LATER branches. `defi.py` (DeFi venue-universe assembly) doesn't own a
      `ManifestWriter` at all — DeFi manifest rows are written through the shared `_write_all_venues` path (confirmed
      clean above), not a DeFi-specific calendar guard. **Scope note**: this audit covered
      `instruments_service/engine/orchestrator/*.py` (the live per-date orchestrator — the direct structural analogue of
      the fixed sports files) but did NOT re-audit the `scripts/` one-off backfill scripts that also call
      `ManifestWriter(` (e.g. `aggregate_legacy_es_opt_trades.py`, `full_polymarket_dump.py`,
      `patch_prediction_shards.py`) — those are TEMPORARY one-offs per `codex/06-coding-standards/script-homes.md`, not
      the standing calendar-guard orchestrator path this bug class targets, so out of this todo's scope. Slot-12,
      2026-07-09.

## Progress Log

### 2026-07-09 — slot-12: audited non-sports orchestrators for the same anti-pattern — CLEAN, no bug found

**Task**: `manifest_early_return_missing_write_loss-003` (the P2 INVESTIGATE todo above).

Grepped `engine/orchestrator/*.py` for every `ManifestWriter(` instantiation site (13 files own an instance), then for
each non-sports (TradFi/DeFi/CeFi) owning function traced every `record_*()` call against every exit path looking for
the same shape: a writer created, `record_*()` called in a loop, then a `return` with no `.write()`/`.close()`/
`.flush()` while OTHER exit paths in the same function DO flush. Found none. The non-sports owning functions are
structurally different from the buggy sports ones in a way that happens to avoid this bug class: they're either
single-exit (the flush is the only path to `return`) or they create-and-flush the writer within one tight conditional
block, never spanning it across multiple later branches the way `understat.py`'s per-function writer did. Full
per-function trace + scope note (didn't re-audit `scripts/` one-off backfills — out of scope, temporary code) is in the
checkbox item above. No code changes — this is a negative-result audit, nothing to ship in instruments-service.

### 2026-07-09 ~02:1x UTC — slot-4: re-verified weather's item #1 gate — holds; found likely explanation for item #6's "daily lag" residual

**Task**: `manifest_early_return_missing_write_loss-001` (the P1 VERIFY todo above).

Read the live consolidated sports `availability_index` once (`read_availability_index`, shard-merged, single-walk-safe —
no whole-corpus GCS list) for `(data_type=WEATHER)`, split by the original item #1 flip window (2019-03-02→2026-06-27,
the `weather-backfill-20260627-160501` VM's range) vs. after it. **0** blank-reason `expected_unattempted` rows within
the original window — the flip holds; the write-loss bug (920b303) did not retroactively invalidate it. In-window
`attempted_failed=51` matches the flip's cited evidence exactly.

All 379 CURRENT blank-reason WEATHER rows sit outside that window (dates 2026-06-30→2026-07-09) — this is the residual
`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md`'s item #6 has been carrying since 2026-07-08 as an
unverified "maybe daily-pipeline-lag" hypothesis (open_meteo `pending_fetch=264` at the time, now grown to 379 as more
days accumulated). Traced why: weather.py's season-window guard resolves a cell via `record_expected_empty()` → typed
`empty_confirmed`, never a blank-reason write itself — so a cell stuck at `expected_unattempted`/blank `error_reason` is
exactly what you'd see when the guard's resolution write is silently dropped (the missing-`.write()` bug, live through
2026-07-09 01:27 UTC) for a date where weather's full expected-league set is off-season (plausible for this 06-30→07-09
window — northern-hemisphere summer break). This is a materially better explanation than "lag": lag would clear as the
poll catches up; a dropped resolution write does NOT clear on its own — it needs the daily forward-poll to re-run
against the now-fixed code.

**Not fixed in this task** (out of the VERIFY todo's scope — item #6 is a separate, already-open item covering 6
sources, several still blocked on unrelated code gaps). Left as a pointer for whoever next re-verifies item #6: check
whether the 379-row weather residual (and probably SFI's parallel ~264-379 row residual, item #2) clears once the daily
forward-poll next touches those dates post-920b303; if it doesn't clear on its own, a targeted re-fetch (same
closer-script pattern as the understat fix) should resolve it now that the guard's write actually persists.

No code changed this session — 920b303 (prior session) already shipped the fix. This is a pure manifest re-verification;
checkbox flipped in this same doc with full counts.

### 2026-07-09 ~01:25 UTC — slot-2: root-caused, fixed, verified end-to-end, shipped

Diagnosed via single-date reproduction (`flush_all_live_writers() == {}` after a season-window-guard call), confirmed
the missing `.write()` pattern by reading `understat.py` line-by-line against `ManifestWriter.write()`'s docstring, then
an Explore sub-agent confirmed the identical pattern in weather.py + footystats.py (SFI clean). Fixed all 10 sites,
shipped `instruments-service@920b303` via `quality-gates.sh` (green) + `quickmerge --agent --files '<4 files>'` (landed
on `live-defi-rollout`, 0 ahead/0 behind confirmed post-push). Re-ran the understat closer end-to-end (v5, paired with
the sibling atexit-drain-race fix) and independently re-verified in a fresh process: understat XG/XG_SHOTS blank-reason
residual for big-5 native leagues resolved 185/2,065 → 0/0. Filed this doc + the sibling atexit-race doc with the
remaining follow-up todos (weather gate re-verification, QG lint, non-sports audit) since fixing those is outside this
task's scope (item #4 checkbox flip).
