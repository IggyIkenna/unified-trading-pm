---
doc_type: issue
title:
  Sports canonical RAW is a truncated copy of the legacy raw for early dates (14.2x on the measured day) — every
  `--force` re-derive is a DATA-LOSS event, and the same pathology repeats one layer down (odds_features holds 13
  fixtures where its MDPS upstream holds 1)
summary:
  "Discovered 2026-07-16 while executing the T-0 lookahead-leak recompute
  (./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md). **The sports lineage can no longer rebuild itself: each layer is
  RICHER than its own upstream.** Measured on day=2022-04-16: canonical raw
  (`market-data-tick-sports-prd-.../raw_tick_data/.../pipeline_mode=batch_odds_api/`) holds **5,626 rows** while the
  legacy bucket (`market-data-tick-sports-central-element-323112/raw_tick_data/.../asset_group=sports/`, no
  `pipeline_mode=`, `data_source=ODDS_API`) holds **79,773** — **14.2x** more, from the SAME 207 objects (the canonical
  objects are truncated, not missing). Consequence: `reprocess_sports_odds.py --force` for that day re-derives ONLY
  T-24h (317 rows) where the processed corpus holds 8 horizons / 5,369 rows, and — with the new stale-shard reconcile
  (MDPS@e2ec8ce) — DELETES the 105 shards it can no longer produce. Measured live: **4,741 legitimate pre-match rows
  destroyed on one day**, fully restored from GCS soft-delete (byte-exact, verified). **The existing corpus is NOT
  mis-bucketed** — falsified rather than assumed: every non-T-0 shard on that day is 100% inside its own staleness cap
  (T-10m bm 5.6-14.9, T-12h 706.7-744.1, T-6h 343.4-380.4); only T-0 was contaminated (21% valid). Later dates are
  intact (2025-04-12: 168,653 raw rows; 2024-11-09: 147,110) and re-derive EXACTLY (every non-T-0 horizon delta 0), so
  this is a bounded, date-dependent carve-out — not universal. **Same pathology at the features layer**: day=2024-01-01
  `odds_features` holds 13 fixtures while MDPS bucketed holds 1; a 31-date evenly-spaced sample shows **4/31 dates
  (13%)** would lose fixtures on recompute (18 fixtures). Until the legacy->canonical raw recovery (OR-5b(b) option-D G1
  read-split-merge) lands, ANY `--force` re-derive at any sports layer is destructive and must be guarded by a per-date
  loss check."
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, features-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [sports, odds, data-correctness, bucket-canonicalisation, migration, re-derive, data-loss, raw-truncation, cutover]
related:
  [
    ./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    ./sports_legacy_canonical_row_gap_2026_07_16.md,
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ./sports_odds_stale_fixture_reinjection_2026_07_14.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "T-0 lookahead-leak recompute leg, 2026-07-16 — measured while piloting `reprocess_sports_odds.py --force`",
    "./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md",
  ]
---

# Sports canonical raw is truncated — `--force` re-derive destroys the corpus

> # 🟢 THE SYMPTOM IS FIXED 2026-07-17 on the days it existed — `market-tick-data-service@75f226e8`.
>
> The split population was **merged into the canonical `batch_odds_api` cells** on the **199 days** where it changes the
> derive (exhaustively scoped: all 1,815 migrated days probed, 0 errors; 1,336 were pure duplicates). **6,304,585 rows
> added, 0 lost.** This doc's measured day, `day=2022-04-16`, now re-derives through the **UNCHANGED** MDPS reader as
> **raw 5,626 → 83,916** and reproduces the corpus grid: T-12h=896 · T-6h=898 · T-4h=896 · T-2h=884 · T-1h=270 ·
> T-10m=870 **all EXACT**, T-24h=894 (richer than 317), T-0=27 (the leak-filtered valid rows per MDPS@3bf56ff). **⇒
> `--force` on those 199 dates is no longer a data-loss event** — the derive now yields strictly MORE per horizon
> (measured: 0 derive rows lost on 1,815/1,815 days).
>
> **What still stands**: **fix direction (b) — the per-date loss guard — is STILL P0 and has NOT landed.** The merge
> removes the known starvation; the guard is what stops the _next_ unknown one from deleting a corpus. Do not read this
> banner as "historical `--force` is now globally safe": the 1,616 non-merged days were never starved by _this_
> mechanism, but nothing yet proves they cannot starve by another. **Fix direction (a) remains REFUSED** (the legacy
> bucket holds nothing unique on those days).
>
> _(Superseded banner retained for provenance:)_
>
> **🔴 CAUSE CORRECTED 2026-07-16 by
> [`sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`](./sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md)
> — the SYMPTOM below is real and every number reproduces; the DIAGNOSIS and fix direction (a) are wrong.**
>
> **Canonical raw is NOT truncated. It is SPLIT, and MDPS only reads one half.** The OR-5b G1 recovery leg re-measured
> `day=2022-04-16` and reproduced this doc's 5,626-vs-79,773 exactly — then found the missing **79,773 rows already
> inside the canonical bucket**, at
> `raw_tick_data/by_date/day=2022-04-16/pipeline_mode=batch_footystats/asset_group=sports/venue=ODDS_API/instrument_type=/data_type=odds/league=*/ticks_migrated_20260505T160406Z.parquet`
> (17 objects). `reprocess_sports_odds.py` cannot see them: it lists only `pipeline_mode={batch_odds_api,live_odds_api}`
> and its `_is_consumable_trades_blob` excludes `_migrated_`. **The 207 "truncated copies" are a different population,
> not a truncation of the same one.**
>
> - **16,969** canonical `_migrated_` objects across **1,815** days are **100% `venue=ODDS_API` + `data_type=odds`** yet
>   **100% stamped `pipeline_mode=batch_footystats`** — **zero are footystats data** (an SSOT violation of
>   `{mode}_{source}`, `codex/02-data/pipeline-mode-partition.md`).
> - **30/30** sampled legacy G1 objects are **row-identical and tick-key-identical** to their canonical migrated twin (0
>   legacy-only, 0 canon-only keys; `source == ODDS_API` both sides). Canonical migrated (1,815 days) is a **SUPERSET**
>   of legacy G1 (386 days).
> - The migrated schema carries **every adapter-required column** and differs from the consumable shape by exactly one
>   column (`data_source`). It is fully consumable — not the coarse `ODDS_API:SPORT:*` meta shape.
>
> **⇒ Fix direction (a) below — "recover the raw first via the OR-5b(b) option-D G1 read-split-merge" — is REFUSED.**
> The legacy bucket holds nothing unique on those days; that merge would write ~15.7M duplicate rows. **The features
> recompute is unblocked by a ~4-line MDPS change** (add the `batch_footystats` prefix, union the `_migrated_`
> population, delete the false "redundant" comment at `reprocess_sports_odds.py:117-120`) — **no GCS migration, no
> legacy recovery.** Fix direction (b) — the per-date loss guard — **stands and is still P0**.
>
> **What survives unchanged**: the destructive `--force` behaviour, the 4,741-row loss measurement, the falsification
> that the old corpus is correctly bucketed, the features-layer pathology, and the ban on historical `--force` until the
> guard lands. **`market-data-tick-sports` remains NOT delete-eligible** — but on a **32-day / 550,062-key** residue
> (canonical capture outage 2022-09-07…2022-10-01), not on this doc's raw-truncation reasoning.

> **NOTIFY-OPERATOR (data-correctness, cross-repo, blocks the cutover's delete-gate reasoning).** Nothing is currently
> lost: the one day damaged during the pilot was restored byte-exact from GCS soft-delete and re-verified (121 shards /
> 5,369 rows / 311 post-kickoff — identical to the pre-pilot census). This issue exists to stop the NEXT agent running
> the same command fleet-wide.

## The finding in one line

**Every sports layer is richer than the upstream it derives from, so the pipeline can no longer reproduce its own
outputs — and `--force` makes the output match the impoverished upstream by deleting the difference.**

## Evidence (measured live 2026-07-16, zero inherited numbers)

### Layer 1 — canonical raw vs legacy raw

| day        | canonical raw rows | legacy raw rows | ratio     |
| ---------- | ------------------ | --------------- | --------- |
| 2022-04-16 | **5,626**          | **79,773**      | **14.2x** |
| 2025-04-12 | 168,653            | —               | intact    |
| 2024-11-09 | 147,110            | —               | intact    |

Canonical prefix: `raw_tick_data/by_date/day=<D>/pipeline_mode=batch_odds_api/asset_group=sports/` (207 objects on the
measured day). Legacy prefix: `raw_tick_data/by_date/day=<D>/asset_group=sports/` in
`market-data-tick-sports-central-element-323112` (207 objects, `data_source=ODDS_API` segment). **Same object count,
14.2x the rows** — the canonical objects are TRUNCATED copies, not a partial migration.

Both raw generations agree that raw `day=` is the **kickoff** day (all `kickoff_utc` on `day=D`, `fetch_utc` spanning
`D-1..D` across 34–36 hourly waves) — so a day legitimately carries the multi-wave snapshots that produce all 8
horizons.

### Layer 2 — what a re-derive does to the processed corpus

`reprocess_sports_odds.py --start-date 2022-04-16 --end-date 2022-04-16 --force` (run live, then reverted):

| timeframe | corpus rows    | re-derived rows | verdict           |
| --------- | -------------- | --------------- | ----------------- |
| T-24h     | 317            | **317**         | reproduces        |
| T-12h     | 896            | **0**           | DESTROYED         |
| T-6h      | 898            | **0**           | DESTROYED         |
| T-4h      | 896            | **0**           | DESTROYED         |
| T-2h      | 884            | **0**           | DESTROYED         |
| T-1h      | 270            | **0**           | DESTROYED         |
| T-10m     | 870            | **0**           | DESTROYED         |
| T-0       | 338 (27 valid) | 0               | (leak — expected) |

**105 shards / 4,741 legitimate pre-match rows deleted.** Restored from soft-delete; re-censused byte-exact.

### The corpus is genuinely correct — this was FALSIFIED, not assumed

The tempting explanation ("the old corpus is itself a mis-assigned derive, so losing it is fine") is **WRONG**. Checking
every old shard against its own `TIER1_HORIZONS` cap on 2022-04-16:

| tf    | rows | inside its cap | bm range      |
| ----- | ---- | -------------- | ------------- |
| T-10m | 870  | **870 (100%)** | 5.6 … 14.9    |
| T-12h | 896  | **896 (100%)** | 706.7 … 744.1 |
| T-6h  | 898  | **898 (100%)** | 343.4 … 380.4 |
| T-24h | 317  | **317 (100%)** | 1433.7 … 1487 |
| T-0   | 338  | 71 (21%)       | −108.0 … 2.4  |

Only T-0 was contaminated. The other seven are real, correctly-bucketed, irreplaceable data.

### Layer 3 — the same pathology at the features layer

`odds_features` is richer than the MDPS bucketed layer it reads:

- **day=2024-01-01**: `odds_features` holds **13 fixtures**; MDPS bucketed holds **1** (167 rows / 16 shards). A
  recompute rewrote it 52 rows → 3 before it was restored from soft-delete.
- **31-date evenly-spaced sample**: **4/31 dates (13%)** would lose fixtures; **18 fixtures** total. Bounded, not
  universal — 87% of dates recompute safely.

## Why this matters beyond the leak recompute

1. **The delete-gate reasoning in the cutover runbook rests on canonical being a faithful superset.** For raw odds on
   early dates it is measurably NOT — the legacy bucket holds 14.2x the rows. Deleting the legacy bucket on those dates
   would make the truncation permanent and unrecoverable.
2. **Any scheduled re-derive is a live hazard.** `mdps_odds_horizon_scheduler.tf` runs a rolling 3-day recon window; it
   is currently PAUSED (sports frozen). On resume it only touches recent dates (whose raw is intact), so it is not an
   immediate threat — but a backfill/gap-fill over historical dates would be.
3. **GCS soft-delete is the only reason this was recoverable.** It is enabled on both buckets and saved this session
   twice. Do not assume it is retained forever (default 7 days).

## Fix direction (not implemented here)

- **(a) Recover the raw first** — OR-5b(b) option-D G1 read-split-merge, extended to cover the ODDS_API raw truncation,
  not just the reference entities. This is the real fix: restore canonical raw to a genuine superset, after which
  `--force` becomes safe and the T-0 lineage can be re-derived properly rather than surgically filtered.
- **(b) Until then, guard the tool.** `reprocess_sports_odds.py` should refuse to write/delete a date when the derive
  produces materially FEWER valid rows than the corpus already holds for that date (per-horizon comparison), recording a
  loud skip rather than silently reconciling downward. The stale-shard reconcile (MDPS@e2ec8ce) is correct and needed —
  it is precisely what makes the unguarded case destructive rather than merely incomplete, so the guard must land with
  it.
- **(c) Same guard for the features recompute** — compare `event_id` count vs fixtures reachable from MDPS per date.

## Todos

- [x] [DATA] P0. ✅ **Quantify the raw truncation across the full corpus** — DONE 2026-07-17 on the CORRECT axis
      (consumable-vs-migrated **within** canonical, not canonical-vs-legacy — this todo's original framing was on the
      wrong axis). Exhaustive: all 1,815 migrated days, real reads + real adapter, **0 errors**. **1,336 (73.6%) fully
      redundant · 280 (15.4%) add raw keys but 0 derive rows · 199 (11.0%) a real derive gain (742,504 rows) · 0 lose.**
      Gain window 2020-06-14…2024-08-03 (2022: 112 days · 2023: 48 · 2024: 34) — so "2022 truncated / 2024-25 intact" is
      close but not exact. All 199 merged: `market-tick-data-service@75f226e8`.
- [ ] [CODE] P0. **Add the per-date loss guard to `reprocess_sports_odds.py`** — refuse to write/delete a date whose
      re-derive yields fewer valid rows per horizon than the corpus holds; emit a loud, countable skip. Must land before
      any historical sports re-derive is run again by anyone.
- [x] [DATA] P0. ✅ **Extend the recovery to the ODDS_API raw truncation** — DONE, but NOT via the G1 legacy recovery
      (refused 3x: the legacy bucket holds nothing unique on those days). The rich rows were already INSIDE canonical
      under `pipeline_mode=batch_footystats`; they are now merged into the canonical `batch_odds_api` cells on the 199
      days that needed it — `market-tick-data-service@75f226e8`. **The MDT delete gate is UNAFFECTED**: it still rests
      on the genuine 32-day / 550,062-key residue (canonical capture outage 2022-09-07…2022-10-01), which this merge
      does not touch. MDT remains NOT delete-eligible.
- [ ] [DOCS] P1. **Correct the cutover runbook's canonical-is-a-superset premise** for raw odds on early dates, and
      cross-reference this issue from the delete-gate section.
