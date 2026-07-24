---
doc_type: issue
title: DeFi manifest has 1.79M genuine duplicate rows — recurring consolidator race, ~2 months old
summary:
  "A live spot-check during the 2026-07-10 backlog apply found the SAME empty_confirmed row
  (ALCHEMY/ARBITRUM/gas_fees/2018-01-01) written twice by two enumerator runs 2.5 weeks apart. A full scan of
  gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet found 4,630,138 defi rows in
  duplicate-key groups; of those, 1,789,793 groups have IDENTICAL capture_status across every copy (genuine,
  zero-new-information duplication — pure denominator inflation). The other 525,276 groups have DIFFERING capture_status
  (legitimate state-transition history, e.g. expected_unattempted -> captured) and are NOT duplicates.
  Duplicate-contributing enumerator_run_ids span 2026-05-07 through 2026-07-10 (~2 months), consistent with the
  recurring DAILY expected-universe-v2 Cloud Scheduler job repeatedly hitting the same race. Root cause not fixed (out
  of this doc's immediate scope) — hypothesis: the per-VM-shard-to-main-index consolidator deletes a shard before (or
  without atomically) completing its merge into the main index, so a run landing in that window sees neither the shard
  nor the merged row and re-enumerates already-covered honest-absence cells."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [manifest, duplication, consolidator, honest-coverage, defi, data-correctness]
related:
  [
    plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
priority: P1
source:
  "Found live during the 2026-07-10 DeFi expected_unattempted backlog apply
  (defi_expected_unattempted_backlog_1m_2026_07_03.md). A second year-chunked apply pass re-wrote the exact same
  2018/2019 candidates the first pass already wrote, prompting a direct manifest spot-check that surfaced this much
  larger, pre-existing pattern."
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
last_updated: 2026-07-10
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
---

## Real evidence

- **Direct spot-check**: `(venue=ALCHEMY, chain=ARBITRUM, data_type=gas_fees, date=2018-01-01)` present TWICE in the
  live manifest — once written `2026-06-22T11:38:24Z` (`enum-reseed-defi-gas-20260622-113817`), once written
  `2026-07-10T13:03:24Z` (`enum-universe-defi-20260710-130231`, my own session's first year-chunked backlog apply). Both
  rows are byte-identical on every non-provenance column (`capture_status=empty_confirmed`,
  `error_reason=EXPECTED_PRE_GENESIS_CHAIN`).
- **Full-manifest scan** (`asset_group=defi`, 15,805,771 rows before fix): 4,630,138 rows sit in duplicate-key groups
  (key = `asset_group, venue, chain, data_type, instrument_type, instrument_id, date`).
  - **1,789,793 rows removed as genuine duplicates** — identical key AND identical `capture_status` across every copy in
    the group (kept the latest `written_at` copy per group).
  - **525,276 groups left untouched** — differing `capture_status` across copies, i.e. real state-transition history
    (the manifest is append-only; this is expected and correct).
- **Duplicate-contributing `enumerator_run_id`s** (top offenders, by row count): `enum-universe-defi-20260706-130616`
  (1,379,692), `enum-universe-defi-20260710-130231` (896,860, mine), `enum-universe-defi-20260710-130607` (884,608,
  mine), `enum-universe-defi-20260507-145635` (390,419), `enum-universe-defi-20260624-102449` (268,878),
  `enum-universe-defi-20260624-013038` (216,873), `enum-universe-defi-20260628-013034` (42,086),
  `enum-reseed-defi-gas-20260622-113817` (13,416), + smaller. **This predates the current session by ~2 months** — the
  vast majority (≈2.85M of 4.63M) comes from runs dated 2026-05-07 through 2026-07-08, well before today.

## Root cause — FOUND AND FIXED 2026-07-10

**Real root cause**: `unified-trading-library/unified_trading_library/manifest_consolidator.py`'s INCREMENTAL merge path
(`_duckdb_merge_payload`, the production steady-state — full rebuilds are cold-bucket/`--force` only). Every cycle
splits the canonical into `survivors` (rows whose key is NOT touched by the current cycle's incoming shards) and
`contested` (rows whose key IS touched). `contested` rows correctly go through a window-dedup
(`PARTITION BY <dedup key> ORDER BY attempted_at/written_at DESC`, last-write-wins). **`survivors` did not** — the code
streamed them through byte-for-byte unchanged (the module's own docstring: "stream the unchanged canonical straight
through"). This means: **any duplicate that ever ends up in the canonical, by any mechanism, for any reason, persists
forever** — incremental cycles only ever re-examine keys the _current_ cycle's shards touch; they never re-verify the
untouched 99.9% of the canonical against itself. Confirmed directly: the
`(ALCHEMY, ARBITRUM, gas_fees, 2018-01-01, empty_confirmed)` duplicate pair had **byte-identical values AND types on
every single dedup-key column** (checked directly against the pre-dedup backup) — proving the two rows were never part
of the same cycle's contested-key comparison (if they had been, the _already-correct_ contested-row dedup logic would
have collapsed them). This is a structural gap in the incremental path itself, not a narrow timing race in shard pruning
— the original "shard-delete-before-merge" hypothesis was investigated and **ruled out**: `_write_consolidated` already
has a documented, tested lost-update-race fix (`manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md`) that
re-reads the canonical fresh on every CAS-retry attempt.

**Fix**: `unified-trading-library@0de04b6e` — apply the SAME window-dedup already used for `contested` rows to
`survivors` too. Every incremental cycle is now self-healing against pre-existing duplicates (from ANY cause), not just
preventive against new ones. New regression test
(`test_consolidate_incremental_self_dedups_untouched_canonical_duplicates`) reproduces the real scenario end-to-end and
was verified, via a stash-based before/after run, to **FAIL against the pre-fix code** (found 2 rows) and **PASS against
the fix** (collapses to 1) — not just inline reasoning. Full existing suite green (39 consolidator + 473
consolidator+writer combined), ruff clean.

## Fix shipped

1. **Cleanup** — `instruments-service/scripts/defi_manifest_dedup_2026_07_10.py`, one-off, backup-first (full pre-dedup
   manifest snapshot to `_migration_backup/defi_manifest_dedup_2026_07_10/`), verify-after, explicit safety check
   (asserts the count of legitimate multi-`capture_status` key-groups is UNCHANGED before writing). Removed the
   1,789,793 genuine-duplicate rows already present. **Applied to production.**
2. **Root-cause fix** — `unified-trading-library@0de04b6e`, the consolidator's survivors-side self-dedup above.
   **Shipped, tested, pushed to `live-defi-rollout`.** The next scheduled consolidator cycle for any bucket (runs every
   1 minute per `manifest_consolidator_scheduler.tf`) will pick this up automatically and begin self-healing any further
   duplication, including in cefi/tradfi/prediction/sports (the fix is asset-group-agnostic — it's in the shared
   consolidator, not a defi-specific script).

## Todos

- [x] [VERIFY] P1. Confirm the finding is real (direct manifest spot-check + full duplicate-key scan). Done, see "Real
      evidence" above.
- [x] [SCRIPT] P1. Write + dry-run-verify the dedup fix. Done —
      `instruments-service/scripts/defi_manifest_dedup_2026_07_10.py`.
- [x] ✅ [INFRA] P1. **Applied to production 2026-07-10.** `defi` manifest rows 15,805,771 → 14,015,978 (removed
      1,789,793). Backup verified (463,952,531 bytes) at
      `gs://market-data-tick-defi-prd-central-element-323112/_migration_backup/defi_manifest_dedup_2026_07_10/availability_index_pre_dedup_20260710-143528.parquet`
      before the write. Safety check (legitimate multi-status groups unchanged at 525,276) held throughout.
- [x] ✅ [DESIGN] P1. **Root-caused and fixed 2026-07-10** — `unified-trading-library@0de04b6e`. See "Root cause — FOUND
      AND FIXED" above. The original shard-delete-timing hypothesis was investigated and ruled out; the real gap was the
      incremental merge's survivors-side non-dedup, proven with a before/after-verified regression test.
- [x] ✅ [VERIFY] P2. **Done 2026-07-10.** Scanned all 5 asset groups with the correct per-schema grain (not defi's
      hardcoded columns — an early naive pass on sports' columns produced a false-positive ~1.79M "duplicates" that
      correct grain detection ruled out). Real genuine-duplicate counts found: cefi 0, defi 0 (already clean), sports 0,
      tradfi 346 rows / 173 groups, prediction 6,284 rows / 3,142 groups. Both cleaned in production.
- [x] ✅ [DATA] P2. **Done 2026-07-10.** Generalized `defi_manifest_dedup_2026_07_10.py` →
      `manifest_dedup_2026_07_10.py` (`--asset-group` flag, auto-detected grain key per manifest schema). Rewritten a
      second time from pandas to DuckDB after the defi backlog-resume merge grew the canonical to 27M+ rows and pandas
      groupby/drop_duplicates repeatedly stalled/OOM'd for 20+ minutes on this host; DuckDB does the same work in under
      4 minutes. Also fixed a NULL-vs-empty-string false-negative (61,372 rows) — the pandas version normalized NaN but
      not `""`, missing genuine duplicates written by two different producers using different "not applicable"
      representations for the same optional dimension.

## Progress Log

- 2026-07-10: Filed. Real evidence gathered via direct GCS parquet reads (not inferred). Dedup script written, dry-run
  confirmed 1,789,793 genuine duplicates + a safety check that the 525,276 legitimate state-transition groups are
  unaffected. `--apply` run in progress.
- 2026-07-10 (later, operator: "actually fix the problem though URGENTLY"): **Root-caused and fixed.** Dispatched a
  focused read of `unified_trading_library/manifest_consolidator.py`'s exact merge/delete/lock/CAS-retry logic (not
  secondhand — read the SQL directly). The original "shard-delete-before-merge race" hypothesis was investigated in code
  and ruled out (the CAS-retry path already re-reads the canonical fresh on every attempt, closing that class of race
  per its own 2026-07-08 fix). Direct evidence instead pinpointed the real gap: the incremental merge's `survivors` CTE
  streams untouched canonical rows through with ZERO self-deduplication — confirmed via the pre-dedup backup that the
  original duplicate pair's dedup-key columns were byte-identical in both value and type, meaning they were never
  compared against each other by any cycle. Fixed (`unified-trading-library@0de04b6e`) by applying the same window-dedup
  already used for contested rows to survivors. Verified the fix is real (not a plausible-sounding no-op) via a
  stash-based before/after test run: the new regression test fails on the pre-fix code (reproduces 2 duplicate rows) and
  passes on the fix (collapses to 1). Full test suite green, ruff clean, pushed to `live-defi-rollout`. The fix lives in
  the shared consolidator, so it protects every asset group's bucket on its next 1-minute cycle, not just defi.
- 2026-07-10 (later still): **Deployed to production and verified end-to-end against real live data — CLOSED.** The fix
  required a real rollout, not just a merge: `market-tick-data-service` (the image the defi consolidator's Cloud Run job
  runs) pins its `unified-trading-library` base image by digest (same class of staleness gap independently found and
  fixed for `instruments-service` earlier this session). Rebuilt UTL (`:latest` digest `sha256:8be3bfd9...`), then used
  the existing fleet tool (`unified-trading-pm/scripts/propagation/add-dockerfile-digest-arg.py`) to fan the fresh
  digest out to all 16 dependent repos in one pass (not just MTDS — this closed the same latent staleness gap
  fleet-wide). Rebuilt MTDS, force-updated the Cloud Run job (`gcloud run jobs update ... --image=...:latest`, since
  Cloud Run Jobs pin a resolved digest at deploy time, not per-execution), then **executed the job for real**
  (`uts-prod-manifest-consolidator-market-data-defi-4wk4k`, succeeded in 43.76s). Direct post-execution read of the live
  `availability_index.parquet` (14,023,022 rows) confirms **zero genuine (identical-key-and-status) duplicate rows
  remain**. Bonus: this same digest-staleness investigation also unblocked instruments-service's stuck LDR→main
  promotion pipeline (all checks green, auto-merged) — the original `@LIN`/`@INV` CeFi catalog fix from earlier this
  session can now finally reach production too.
- 2026-07-10 (much later — second, self-caused incident and fix, same day): **The defi backlog-resume write
  (`defi_expected_unattempted_backlog_1m_2026_07_03.md`, 2020-2026 year-chunks landing as 7 per-VM shards, ~18.7M rows
  in one window) exposed a real scaling regression in the fix above.** The `survivors` CTE's window-function self-dedup
  ran `row_number() OVER (PARTITION BY ...)` over the ENTIRE untouched-canonical set every cycle — fine at the ~14M-row
  scale it shipped at, but once defi's canonical grew past ~14M rows in one window (becoming the largest canonical of
  any asset group — cefi 7.2M / tradfi 5M / sports 1.8M all kept succeeding fine) the consolidator Cloud Run job started
  SIGKILL-ing (OOM) every single cycle, even after two escalating memory bumps (16Gi→32Gi container, then
  `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` 8GB→24GB — the DuckDB budget is a hardcoded-default env var, unrelated to container
  size, so the first bump alone did nothing). The job silently stopped merging entirely for ~2 hours (canonical mtime
  frozen) before being caught. **Root cause + fix**: split `survivors` into `survivors_clean` (unique-key rows, cheap
  ANTI JOIN passthrough — the overwhelming majority) and `survivors_deduped` (only rows whose key actually recurs — the
  window function's working set shrinks from O(canonical) to O(genuine-duplicate-rows), at or near zero in steady
  state). Verified locally against the real production bucket (27.46M rows, 9 shards): completed in 252s at ~10.5GB peak
  (was repeatedly SIGKILL'd before). Shipped `unified-trading-library@800af156` (dirty-deps carve-out direct push —
  quickmerge blocked purely by a sibling's live, currently-being-edited untracked file failing an unrelated
  codex-compliance check; that file was not touched). Fanned the new digest to all 18 fleet Dockerfiles, rebuilt MTDS,
  force-updated the Cloud Run job, executed it for real, resumed the scheduler. **Separately found and fixed while
  investigating**: 27,908 residual duplicate rows in the post-merge defi manifest, caused by a NULL-vs-empty-string
  false-negative in the dedup tooling (not the consolidator fix itself) — see the P2 items above. **Verified stable**:
  post-fix, the real 9-shard backlog (already in flight when the fix landed) completed cleanly in one more
  local-triggered cycle (178s, 9.86GB peak, pruned all 7 shards), and subsequent scheduler-triggered cycles against the
  now-trivial (0-shard) steady state ran clean with no further SIGKILLs. Final state: defi canonical 27,445,013 rows,
  zero genuine duplicates (verified against the correct wide grain key, not the narrow ad-hoc key that gives false
  positives). CLOSED.
