---
doc_type: issue
title:
  Sports features-layer findings sweep — PART 1 of 3 (§ A-F — lineups/coaches shape-mismatch, odds leakage,
  honest-coverage tooling gaps, junk-symbol guard, early-horizon sparsity, canonical-naming audit) — a shape-mismatch
  normalizer silently zeroes 4 years of lineups/coaches, 116 odds_features shards remain leaked behind a loss guard that
  cannot express "known-corrupt baseline", and the honest-coverage tooling is non-functional below group grain
  (calculator-grain mismatch + league_id namespace split)
summary:
  Consolidated, measured findings from the 2026-07-18 sports investigation sweep. Headline — the raw sports corpus is
  far richer than the features layer reflects - lineups exist on 364-365 days/year 2022-2025 (+179 days into 2026) with
  coach_id/coach_name 100% populated, yet `_normalize_fixture_lineups` parses only the LEGACY nested api-football shape
  while instruments-service now writes a FLAT one-row-per-player shape, silently converting real rows to zero (measured
  40x13 -> 0x0). That single function explains the "3,234 empty" lineup days, coach 0/120, and features materialization
  collapsing after 2023 (2024:11 days, 2025:1, 2026:0) - fixing it backfills four years of lineups AND coaches from data
  already on disk with ZERO api-football calls. Separately the odds leak remediation is derive-complete but
  consumer-incomplete (116 of 1,916 odds_features day-shards still carry steam/odds_movement at T-24h), and the fix is
  blocked by a loss guard whose premise (existing shard is trustworthy) is false for known-corrupt baselines. Finally,
  sports honest-coverage is unmeasurable below group grain - the per-calculator CLI filters `feature_group == calc_name`
  against a manifest that collapses 31 calculators into `derived_features`, and the expected-vs-captured join is broken
  by a league_id namespace split (manifest numeric api-football IDs/None vs canonical symbolic slugs like EPL).
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data, features]
repos: [features-service, market-data-processing-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags:
  [
    sports,
    features,
    lineups,
    coaches,
    normalizer,
    leakage,
    loss-guard,
    honest-coverage,
    manifest-grain,
    data-correctness,
    big-finding,
  ]
related:
  [
    /plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md,
    /plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    /plans/archive/issues/sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
  ]
created: 2026-07-18
author: unknown
source:
  - Operator questions 2026-07-18 ("so this is ultimately gonna solve leakage looking back for all sports related stuff?
    not just going forward?") - which forced a backward-completeness audit rather than accepting "the code is fixed" as
    the answer, and surfaced the 116 stale consumer-layer shards.
  - Operator challenge on the four always-empty dimension groups ("for coaches/players/referees/ im confused you saying
    we never have these? we dont know the linup for gaems and the coaches and the players?") - this is what surfaced the
    normalizer shape-mismatch. The initial framing ("4 always-empty stub groups") was imprecise and nearly buried a
    data-destroying bug as a benign stub.
  - Operator design input on shard grain ("we only need a shard per calculator rather than per features? same as we do
    on instruments bundles like options and instrument service venue level sharding same concept?") - correct, and it
    retroactively explains why the per-calculator honest-coverage CLI has never worked.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
drift_direction: advance-code
parent_epic: infrastructure_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-18
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md,
    features-service/features_service/sports/data/gcs_normalizers.py,
  ]
---

> **✅ OPERATOR RULING 2026-08-08 — add BOTH T-2h and T-6h as MODEL horizons.** The open todo asks whether to add T-6h
> _or_ T-2h. Ruled: **both.** Current model set is `['T-10m','T-1h','T-24h']`; both new horizons already have captured
> data (measured on the live prod manifest 2026-08-08: T-2h **14,209** shards, T-6h **14,217**), carry ~2.7x the fixture
> coverage of T-24h, and fall safely pre-match. Taking both lets the model learn the T-6h→T-2h movement as its own
> signal. The retrain must report a **measured** coverage and performance delta — do not assume the richer set is an
> improvement. Implemented by `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`.

# Sports features-layer findings sweep (2026-07-18)

All findings below are **measured**, not inferred. Where a number was retracted during the sweep it is marked
**RETRACTED** with the reason, so nobody re-derives a false conclusion from it.

## A. Lineups / coaches / players / referees / rounds — the verdict table

Operator's fear was "we don't know the lineups/coaches/players". **We do.** The gap is a features-layer normalizer, not
capture.

| Entity                    | Underlying data captured?                                                                      | Standalone dim empty? Depended on?                                              | Real gap or benign?                                          |
| ------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Lineups**               | **YES** — 2022:365, 2023:365, 2024:364, 2025:364, 2026:179 days                                | `fixture_lineups` is per-game, not a dim. 4 calculators consume it              | **REAL gap in FEATURES layer** (normalizer zeroes real rows) |
| **Per-game player stats** | **YES** — 2022:358, 2023:361, 2024:359, 2025:354, 2026:164 days; 38 real columns               | Not a dim. `injury_impact`, `player_lineup` consume it                          | **Mostly honest absence** (see A5)                           |
| **Referee**               | **YES at fixture grain** — features `fixtures.referee_id` **161/170 = 94.7%** populated        | `referees` dim 100% empty; **nothing depends on it**                            | **Benign dim** + cosmetic wiring bug (A3)                    |
| **Coach**                 | **YES, via lineups** — raw carries `coach_id`/`coach_name`, **100%** in samples (72/72, 40/40) | `coaches` dim 100% empty (hard stub); `manager_calculator` needs FIXTURES+TEAMS | **REAL but narrow** — captured then dropped by normalizer    |
| **Rounds**                | **NO — genuinely absent upstream** (`fixtures.round` present but empty strings)                | `rounds` dim empty; **no calculator requires it**                               | **Benign**; the `round` FIELD is fixed separately (see A6)   |

### A1. `_normalize_fixture_lineups` shape mismatch silently destroys real rows — **P0**

`features_service/sports/data/gcs_normalizers.py:358` parses only the **legacy nested** api-football payload (`startXI`
/ `substitutes` JSON lists), but instruments-service now writes a **flat one-row-per-player** shape. Measured at runtime
against a real 2026 file:

```
INPUT (flat raw): shape (40, 13)  ->  OUTPUT: shape (0, 0)   # 40 rows -> 0
```

**Blast radius** — this ONE function explains all of:

- `fixture_lineups` reading "3,234 empty days" while raw has lineups on ~every fixture day.
- Features materialization collapsing after 2023: per-year captured shards 2019:89, 2020:173, 2021:235, 2022:213,
  2023:214, **2024:11, 2025:1, 2026:0** (sums to exactly the 936 captured).
- `coach_name` 0/120 in features while raw is 72/72 — the normalizer never emits `coach_id`/`coach_name`
  (`gcs_normalizers.py:386-396`), so `_align_columns` re-adds them as None.
- 4 starved calculators: `player_lineup`, `formation`, `bench_sub`, `transfer_window`.

**Fix**: handle the flat shape (keep legacy parsing for any old shards), and emit `coach_id`/`coach_name`. Then
re-derive `fixture_lineups` across history — **no api-football calls needed**, the corpus is already on disk.

**2026-07-27 corroboration + open question (slot-3, todo-10 benchmark work,
`/plans/active/data_pipeline_check_mdps_features_2026_07_20.md`)**: running the `/data-pipeline-check-features`
benchmark leg for `SPORTS:sports` (day=2026-07-19, both a 7-day and a 30-day window, 13 distinct days observed total),
the `player_lineup` calculator still emits 74/74 all-zero columns every day tested — consistent with, not contradicting,
the "starved calculator" finding above. **Open question, not independently diagnosed**: the 2026-07-18 re-derive's
window was `2019-01-01..2026-07-17` — day=2026-07-19 falls 2 days PAST that window's end. Worth checking whether this is
(a) normal expected data-capture lag for a day only ~8 days old relative to when it was tested, or (b) the forward/live
`fixture_lineups` capture path was never wired to keep pace after the one-time historical re-derive (i.e. new days
landing after 2026-07-17 never get the flat-shape fix applied going forward). Flagging rather than guessing — did not
trace the live/forward capture path this session.

- [x] [CODE] P0. Fix `_normalize_fixture_lineups` to parse the flat one-row-per-player shape + emit `coach_*`; add a
      regression test pinning BOTH shapes (flat 40 rows -> 40 rows; legacy nested -> unchanged). —
      features-service@cf10b931 + 7 regression tests. Evidence: QG green (17,689 passed / 0 failed, ALL QUALITY GATES
      PASSED). Verified on real shards, all four on-disk conditions now yield exactly 11 starters per XI with coach 100%
      populated: 2024-09-01 flat+dup 160->80, 2026-05-15 flat clean 40->40, 2023-03-04 flat+dup 240->120, 2022-04-16
      legacy 8->160. Also dedupes on (fixture_id, team_id, player_id) — the 2x-duplicated historical window would
      otherwise have doubled every lineup on re-derive.
- [x] [DATA] P0. Re-derive `fixture_lineups` (and dependent groups) across 2019-2026 from existing raw; verify per-year
      captured shard counts stop collapsing after 2023. **DONE 2026-07-18 16:09Z — deployment-service@d0d0522 +
      fs-backfill-20260718-160901.** The sports features launcher hardcoded `--tables fixture_features`, so NO other
      sports feature table had a VM path at all; added a backward-compatible `--tables` override (QG green, 2,513
      passed). Launched the lineups re-derive over 2019-01-01..2026-07-17 reading EXISTING raw — **zero api-football
      calls**, so it does NOT contend for the per-key singleton and runs alongside the FIXTURES backfill. Tarball
      VERIFIED to carry the fix before launch (features-service `2f187a4e`, `cf10b931` ancestor-proven, flat-shape
      branch present) — the launcher emits a generic 'may fetch pre-fix code' warning, and running the OLD normalizer
      here would have overwritten existing lineups with zeros. Watchdog keyed on ROWS>0 + coach populated, because the
      bug wrote EMPTY shards so shard existence proves nothing.

### A2. The four empty dimension tables are benign — delete + document — **P2**

Verified in BOTH registries: `unified_api_contracts/canonical/domain/features/required_inputs.py` +
`.../sports/feature_upstream.py` declare **zero** requirements on `PLAYERS` / `COACHES` / `REFEREES` / `ROUNDS`.
`manager_calculator.py:8-12` explicitly documents coaches as "optional — may be None or empty" with a fixture-history
fallback. `export_coaches` / `export_rounds` are unconditional stubs; `export_players` / `export_referees` read sources
that are structurally unpopulatable (`_fetched_players` is never appended to anywhere; see A3 for referees).

**Operator decision (2026-07-18): delete them and document where the real data lives** — four always-empty tables while
the data sits elsewhere is actively misleading (workspace rule: delete deprecated code, no shims; never silent
placeholders).

- [x] [CODE] P2. Delete `export_players`/`export_coaches`/`export_referees`/`export_rounds` + their
      `PLAYERS_/COACHES_/REFEREES_/ROUNDS_COLUMNS`, and every registration (`cli/batch_write.py`,
      `cli/handlers/batch_handler.py`, `cli/handlers/_available_at_helpers.py`, `exporters/validation.py`,
      `schemas/output_schemas.py`, `docs/SCHEMA_VALIDATION.md`). **DONE — features-service@d564bf6f.** QG green (17,682
      passed / 0 failed, ALL QUALITY GATES PASSED). Also updated the tests pinning the old contract
      (`test_returns_14_tables` -> `test_returns_10_tables`, the expected-names set, and the `players`/`referees`
      `available_at` parametrize).
- [x] [DOC] P2. Document the real homes in code: coach -> `fixture_lineups.coach_id/coach_name`; referee ->
      `fixtures.referee_id`; player identity -> `fixture_lineups` + `player_stats` (`player_id`/`player_name`); rounds
      -> genuinely absent upstream. **DONE — features-service@d564bf6f.** Recorded as a block comment at the foot of
      `exports.py` plus the `exporters/__init__.py` docstring, including the verification that nothing depends on them.
- [x] [DATA] P2. Purge the resulting always-empty manifest rows / shards so they stop inflating the coverage denominator
      (4 groups x ~4,216 dates of `empty_confirmed`). **DONE — features-service@bf088de1 (2026-07-24T21:09Z).**
      Re-verified 2026-07-26 (checkbox-drift fixup via `sports_satellite_ao_dispatch_batch5_2026_07_26.md`): pre-purge
      backup shows 16,864 rows, 100% `empty_confirmed`, zero real captured; current live index shows 0 remaining across
      all four `feature_group` values.

### A3. Referee wiring bug (cosmetic) — **P3**

`_FIXTURE_COL_MAP` (`gcs_normalizers.py:133`) maps `referee_name` -> **`referee_id`**, but `_fetch_runner.py:186` reads
`fx.get("referee")`. Proven at runtime:

```
raw referee_name:      ['R. Jones', 'J. Gillett', 'A. Taylor']
fx.get("referee")   -> [None, None, None]
fx.get("referee_id")-> ['R. Jones', 'J. Gillett', 'A. Taylor']
=> _fetched_referees collects: []
```

Cosmetic only — `referee_features` reads `target_fixtures.referee_id` directly and is NOT starved (94.7% populated).
Resolves naturally with A2 (the dim is being deleted); fix the key read if the dim is ever revived.

### A4. `players` dim is structurally unpopulatable — folded into A2

`_fetched_players` is declared, reset to `[]`, and **never appended to**; `"players"` is not in `REFERENCE_ENTITY_TYPES`
(`gcs_reader.py:108`) and never a `gcs_data` key. Harmless — player identity comes from `FIXTURE_LINEUPS` +
`PLAYER_STATS`.

### A5. `player_stats` sparsity is largely honest absence — **no action**

`instruments_service/engine/orchestrator/sports_reference_fixtures.py:431`: ~57% of `/fixtures/players` calls return 0;
**729 of 790 leagues never yield PLAYER_STATS**, already recorded as `EXPECTED_NO_PROVIDER_COVERAGE`. Correct behavior.

### A6. `rounds` dim vs the `round` FIELD — do not conflate

The empty `rounds` **dimension table** (benign, being deleted) is distinct from the fixture **`round` field**, which
drives `competition_phase` / `is_promotion_relegation` and is being backfilled separately — see
`sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md`.

---

## B. Odds leakage — derive-complete, consumer-incomplete

### B1. Backward-completeness verdict (measured)

| Layer                        | Status                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| **Derive (odds buckets)**    | **backward-COMPLETE** — 1,931/1,934 days reprocessed, **0** post-kickoff rows        |
| **Consumer (odds_features)** | **NOT complete** — **116 of 1,916** day-shards (6.1%) still leaked                   |
| **ML artifacts**             | **clean** — no persisted training set; 3 CLV models QUARANTINED, `promotion_blocked` |

The 116 were derived **2026-07-12..15, before their clean canonical upstream existed** (recompute ran 07-16..18 and
never revisited them). By data-year: **2022:87, 2023:26, 2025:3**. Leak signature measured in-data: `steam_detected` /
`odds_movement` populated at **T-24h** plus an HT horizon in a pre-match set. Derived independently twice (agent census

- direct GCS creation-time scan) — both returned exactly 116.

**Proof the removal is justified, not data loss** (day=2022-04-16):

| Measure                              | Value                                                |
| ------------------------------------ | ---------------------------------------------------- |
| Canonical clean bucket               | 5,058 rows, **0 post-kickoff**                       |
| Canonical **genuine** T-24h fixtures | **25**                                               |
| `bm_minutes_to_kickoff` @T-24h range | **1433.7 – 1487.0** min (genuinely ~24h pre-kickoff) |
| Old leaked shard claims @T-24h       | **68** fixtures                                      |
| Old shard `steam` populated @T-24h   | **29** (impossible 24h pre-match)                    |

The 43-fixture difference had **no genuine ~24h-pre-kickoff observation** — mis-bucketed post-kickoff data. The clean
re-derive produced exactly 25, matching canonical.

- [x] [DATA] P1. Backup-then-rebuild the **113** fixable shards (116 minus the 3 in B2): copy each shard to a backup
      prefix, delete, re-derive, verify `steam@T-24h == 0`. Operator-approved 2026-07-18 (option A: keeps the guard
      fully protective rather than weakening it). — **DONE 2026-07-18 12:16Z: 113/113 rebuilt (pilot 2022-04-16 + batch
      OK=112 EMPTY=0 FAIL=0)**. Every shard copied to
      `gs://features-sports-prd-central-element-323112/_leak_remediation_backup_20260718/` BEFORE deletion (soft-delete
      was unverifiable — the SA lacks `storage.buckets.get`, a 403 not a 404). Guard verdict on each rebuild:
      `LOSS_GUARD_PASS [no_existing_shard]` — the guard stayed fully protective, it simply had no corrupt baseline to
      defend. Evidence (8-date sample, all CLEAN): horizons are exactly `['T-10m','T-1h','T-24h']` (leaked HT gone) and
      steam/odds_movement/clv at T-24h are ALL zero — e.g. 2022-04-16 199 rows -> 121, T-24h fixtures 68 -> 25 matching
      canonical genuine, steam@T-24h 29 -> 0.

### B2. Three dates cannot be reprocessed — `ADAPTER_RETURNED_EMPTY_OUTPUT` — **P1**

`2025-12-18`, `2025-12-24`, `2025-12-31` have **no canonical odds bucket at all** and a re-run reproduces the failure:

```
Read 18,480 rows from canonical ODDS_API for 2025-12-18 (468 parquet files)
Adapter returned empty bucketed df for 2025-12-18
Day 2025-12-18: raw data present but ADAPTER_RETURNED_EMPTY_OUTPUT -> recording attempted_failed
```

Raw is abundant (~18k rows each) but zero rows bucket. Their legacy shadows are **100% post-kickoff** (51/51, 63/63,
62/62, down to **-271.5 min**), so the empty output is very likely **correct** — every observation is legitimately
rejected by the `bm<0` guard. If so this is **honest absence mis-recorded as `attempted_failed`** (should be
`empty_confirmed`), which also wrongly depresses the coverage denominator.

- [x] [DIAG] P1. ✅ MEASURED — **the hypothesis is REFUTED, and the proposed remediation would have HIDDEN a real bug.**
      Raw is overwhelmingly _pre_-kickoff, not post: 96.7% of observations have `minutes_to_kickoff > 0`. The dominant
      disqualifier is a different one entirely — the observations sit **>24h before kickoff**, i.e. outside every
      `TIER1_HORIZONS` bucket (which spans T-24h..T-0), median ~4,590 min (~3.2 days) out.

| date       | >24h out (unbucketable) | **bucketable (0–24h)** | post-kickoff | verdict                                      |
| ---------- | ----------------------: | ---------------------: | -----------: | -------------------------------------------- |
| 2025-12-18 |          25,180 (95.4%) |                **360** |          866 | **REAL BUG** — rows were droppable-but-valid |
| 2025-12-24 |          24,738 (96.0%) |                  **0** |        1,035 | honest absence — empty IS correct            |
| 2025-12-31 |          26,557 (95.1%) |                **362** |        1,007 | **REAL BUG** — same as 12-18                 |

**The three dates are NOT one case.** Only 2025-12-24 has genuinely nothing to bucket. 12-18 and 12-31 each hold ~360
observations inside the bucketable window that the adapter nonetheless dropped — so `attempted_failed` on those two is
an HONEST signal of a genuine failure, and rewriting them to `empty_confirmed` (the original remediation) would have
**suppressed a live bug and marked a real data gap as confirmed-empty**. That is the precise failure mode the
honest-absence rule exists to prevent, arrived at from the wrong direction.

A second hypothesis was also eliminated on the way: that the 18,480 rows were the RECOGNIZED-BUT-UNCONSUMABLE
`venue=ODDS_API` meta shape (`instrument_type=sport`). Measured — the raw is 468+ files of `instrument_type=odds` under
real bookmaker venues (BOVADA/PINNACLE/LADBROKES_UK/…), i.e. the fully consumable shape.

- [x] [DIAG] P1. ✅ ROOT-CAUSED 2026-07-30 (`/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`
      todo 1) — **NOT a fixture-mapping join drop and NOT a hidden secondary guard.** Pulled the real raw
      `batch_odds_api` parquet for all 3 dates from `market-data-tick-sports-prd-central-element-323112` and replayed
      the adapter's exact guard chain (`_materialise_fixture_identity` → causality → 48h zombie-staleness cap → 7-day
      kickoff-past cap → `assign_horizon_buckets_vectorised`). Every one of the 316 (2025-12-18) / 310 (2025-12-31)
      in-window (`0<=bm_minutes_to_kickoff<=1440`) rows survives ALL secondary guards intact (0 dropped by
      causality/staleness/ kickoff-past on either date) and reaches the per-bucket horizon-cap check — where 0/316 and
      0/310 get assigned a valid `horizon_idx`. Root mechanism: on BOTH dates `fetch_utc` has exactly **1 distinct
      value** (2025-12-18 12:00 UTC / 2025-12-31 12:00 UTC — a single daily fetch, confirmed live), and the ONLY
      fixtures kicking off within the following 24h are exactly **2 A-League (`A_LEAGUE`/`SOCCER_AUSTRALIA_ALEAGUE`)
      matches per date** (12-18: Macarthur FC v Brisbane Roar ko 2025-12-19T07:00Z + Western Sydney Wanderers v Auckland
      FC ko 2025-12-19T09:00Z; 12-31: Auckland FC v Newcastle Jets FC ko 2026-01-01T04:00Z + Western Sydney Wanderers v
      Macarthur FC ko 2026-01-01T08:00Z). Their `bm_minutes_to_kickoff` clusters at **~1144.5-1146.4 / ~1264.5-1266.4**
      (12-18) and **~964.7-967 / ~1204.7-1206.7** (12-31) — all squarely inside the **615-minute dead zone (765-1380
      min) between `TIER1_HORIZONS`' T-12h window `[675,765]` and T-24h window `[1380,1500]`**
      (`bucket_assignment_     adapter.py` `TIER1_HORIZONS`/`_HORIZON_CAPS` — 8 narrow accept-windows totaling ~235 of
      the 1440 pre-match minutes, by design). Control date 2025-12-20 (working, 83.6% raw-bucketable) has **114 distinct
      `fetch_utc` values** spread across the day vs these 2 dates' single noon snapshot — with many more
      snapshots-per-fixture, far more land inside SOME target's narrow cap by chance. So the "REAL BUG" framing holds
      exactly as originally measured: real, valid pre-match odds WERE captured for those A-League fixtures, but the
      single-fetch cadence on these 2 quiet dates combined with `TIER1_HORIZONS`' sparse target grid means literally
      none of it could ever land in a bucket — a genuine capture-cadence/target-density interaction, not a join bug or
      an extra guard. **Manifest-state correction**: queried the live availability manifest directly in BOTH candidate
      buckets (`market-data-tick-sports-prd-...` `odds_horizon_bucket` data_type, and `features-sports-prd-...`) for
      `A_LEAGUE`/`SOCCER_AUSTRALIA_ALEAGUE` on all 3 dates — **no row of ANY capture_status exists** (not `captured`,
      not `attempted_failed`, not `empty_confirmed`); the shard is simply unregistered.
      `scripts/reprocess_sports_     odds.py` only writes `attempted_failed` to the manifest `if not dry_run:` (script
      L958/L980) and its own docstring's usage example (L40) is a `--dry-run` invocation — so the `attempted_failed`
      state quoted in this doc's §B2 repro log was very likely a **dry-run diagnostic that was never persisted**, not a
      live manifest row. There is therefore currently nothing live to relabel for EITHER date — see the P2 item below.
- [x] [DATA] P2. ✅ 2026-07-30 — **premise revisited, not executed.** The plan was to relabel 2025-12-24 alone to
      `empty_confirmed` once the bucketing question above was understood. Live-checked both candidate manifests
      (`market-data-tick-sports-prd`'s `odds_horizon_bucket` + `features-sports-prd`) for an `A_LEAGUE`/
      `SOCCER_AUSTRALIA_ALEAGUE` row on 2025-12-24: **none exists** (see the DIAG finding above — the shard was never
      registered, `attempted_failed` or otherwise, for any of the 3 dates). There is nothing live to relabel today. If
      `reprocess_sports_odds.py` is next run for real (non-dry-run) against these dates: 2025-12-24 has **0** in-window
      rows at all (genuinely nothing to bucket — honest absence, `empty_confirmed` is correct) while
      2025-12-18/2025-12-31 have 316/310 in-window rows that are legitimately `attempted_failed`-worthy per the root
      cause above (real data existed but landed in the T-12h/T-24h dead zone) — so the ORIGINAL guidance (2025-12-24
      only, never 12-18/12-31) still stands as the correct rule for whenever that real run happens; it just doesn't
      apply to any manifest state that exists right now.
- [x] [DESIGN] P3. ~~~95% of captured odds are unbucketable~~ **RETRACTED — I generalised from three anomalous dates.**
      Operator challenged the number as implausible ("seems weird thats data corruption? we need to refetch odds!?").
      They were right that it did not add up. Measured against normal match days:

| date       | status  |    rows | **bucketable (0–24h)** | fixtures |
| ---------- | ------- | ------: | ---------------------: | -------: |
| 2025-12-17 | working |  10,680 |      **7,956 (74.5%)** |        4 |
| 2025-12-20 | working | 307,168 |    **256,895 (83.6%)** |       69 |
| 2025-12-18 | failing |  26,406 |             360 (1.4%) |        2 |
| 2025-12-31 | failing |  27,926 |             362 (1.3%) |        2 |

      **A normal match day is ~84% bucketable.** The three B2 dates are quiet holiday fixture lists (Thu 18 Dec,
      Christmas Eve, New Year's Eve — 2 fixtures each vs 69 on Sat 20 Dec), so their raw is dominated by far-future
      forward-book quotes with almost no imminent kickoffs. Reading them as the pipeline norm was a sampling error of
      exactly the kind this sweep has hit repeatedly (§ W, § X): **an aggregate from a pathological subset generalised
      to the population.** There is no T-48h/T-72h bucket gap and no capture-cadence crisis.

      **NO data corruption, and NO odds refetch is warranted** — the operator's two explicit hypotheses were tested and
      both refuted: (a) kickoff defaulted to midnight / wrong day → **0.0%** of kickoffs are at 00:00:00, hours cluster
      realistically at 20/17/15/14 UTC; (b) wrong kickoff assignment → `bm_minutes_to_kickoff == (kickoff_utc -
      bm_time)` for **100%** of rows, arithmetic exact.

      One genuine observation survives, but it is a NOTE not a defect: capture is a **single daily fetch at 12:00 UTC**
      (`fetch_utc` has exactly 1 distinct value per day), so a given fixture can only populate whichever TIER1 bucket
      its noon-to-kickoff distance falls in. That is sufficient for the far horizons and is why busy days still bucket
      84%, but near-kickoff buckets depend on fixtures kicking off shortly after noon. Worth knowing before anyone
      reads thin T-10m coverage as a capture bug.

      **Methodological note on my own error**: I first measured `minutes_to_kickoff` (computed from `fetch_utc`) when
      the adapter uses `bm_minutes_to_kickoff` (computed from `bm_time`). The two differ on 100% of rows (median 4.9
      min). It happened not to change the bucket counts, but I reported a number from the wrong column and only caught
      it because the conclusion was challenged.

### B3. Loss guard cannot express "known-corrupt baseline" — **P2**

`evaluate_loss_guard` allows a write only if the re-derive reproduces every fixture the existing shard holds, per
horizon. Its only exemption lever is `intentionally_dropped_horizons` (per-HORIZON, currently `{HT}`) — which does not
apply when the loss is **inside** a retained horizon (T-24h). So a legitimate leak fix that must shrink a date is
**blocked by design**:

```
LOSS_GUARD_BLOCKED odds_features for 2022-04-16 [fixture_loss] — Re-derive would lose 43 fixture-horizon rows
({'T-24h': 43}); fixtures 68 -> 68. Upstream is thinner than its own descendant — refusing to shrink the date.
```

The guard's premise (existing shard is trustworthy/richer) is **false for known-corrupt shards**. Chosen remediation is
backup-then-rebuild (guard sees `old=None`), which keeps the guard fully protective everywhere else. A durable mechanism
is still worth considering if leak fixes recur.

### B4. Loss guards are forward-only — **document, no action**

Both `odds_loss_guard.evaluate_odds_loss_guard` and `features loss_guard.evaluate_loss_guard` are **pure per-date write
gates**. They never scan or re-derive history; the scheduled job default is a rolling `[today-2, today]` window.
Backward cleanup happens ONLY via an explicit backfill run — which is exactly why the 116 survived. Worth stating
plainly in the codex so "the guard is in place" is never mistaken for "history is clean".

---

## C. Honest-coverage tooling is non-functional below group grain

### C1. Per-calculator CLI grain mismatch — **P1**

`features-service/scripts/sports/honest_coverage_report.py:181` filters `manifest_df["feature_group"] == calc_name`, but
the manifest only ever carries `fixture_features` / `derived_features` / `odds_features` (+ `sfi_progressive` and 14
reference tables) — all 31 calculators collapse into `derived_features`. Result: **0.0% for 34 of 37 calculators**; only
`sfi_progressive` matches (because it happens to BE a manifest group). The CLI was written expecting **calculator-grain
shards the writer never emits**.

### C2. league_id namespace split breaks expected-vs-captured — **P1**

| Side                          | league_id values                                                        |
| ----------------------------- | ----------------------------------------------------------------------- |
| manifest (`derived_features`) | numeric api-football IDs `'1','10','100',…` — and **None** on many rows |
| expected universe             | canonical symbolic slugs `'EPL','LA_LIGA','BUNDESLIGA'`                 |

No shared values -> the join collapses. **RETRACTED**: an earlier expected-universe pass produced
`derived_features 20.4% / fixture_features 29.7% / odds_features 0.0%`. Those numbers are **artifacts of this namespace
split, not coverage** — do not cite them.

**Consequence**: the only trustworthy sports-features number today is **group-grain materialized coverage ~99.5%**
((captured+empty)/total over 197,890 manifest rows). A true expected-universe honest-coverage figure is **not currently
computable**.

### C3. Move the manifest atom to per-calculator grain — **P1 (operator design decision)**

Operator 2026-07-18: the shard should fail if anything in the calculator fails, so the atom is the **calculator**, not
the individual feature — the same principle as instruments **venue-level sharding** and **options bundles** (the atom is
the natural unit of work that succeeds/fails together). ~31 calculator atoms instead of 3 group atoms or 1,163 feature
atoms. This also **retroactively fixes C1** by aligning the writer with what the CLI already assumes, and surfaces
dependency cascades (topo-sorted `depends_on`) that group grain hides entirely.

- [x] [CODE] P1. Change the `odds/derived/fixture_features` writer + manifest row_key atom from
      `(feature_group, date[, league])` to `(calculator, date[, league])`; keep writer/manifest/status/gate/UI identical
      (workspace hard rule). Reconcile the league_id namespace (C2) in the same change. — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` ("Honest-coverage atom regrade to per-calculator grain
      (already operator-decided, implementation pending)"; see that doc for execution).

### C4. Feature-grain = within-shard column check, NOT a manifest dimension — **P2**

1,163 registered feature columns (`FIXTURE=28 + DERIVED=993 + ODDS=142`, `schemas/feature_catalog.py`); each carries a
horizon + NaN policy (`engine/feature_expectations.py`), and the WriteGate already computes per-column non-null
fractions. So per-feature coverage is a **cheap column-presence/non-null check inside the existing shards** — attach it
to the `horizon_schema.json` sidecar the writer already emits, plus a read-time reconciler diffing
`BuilderEntry.columns` vs actual. A manifest row per feature would 1,163x the row count and is **not** warranted.
Prerequisite: promote the currently-inferable per-calculator grain (match vs day/season, derivable from
`required_inputs`) to an explicit declared field.

### C5. `read_availability_index` swallows config errors into "empty" — **P3 footgun, not a prod bug**

The client is constructed inside a `try` whose handler is
`except (FileNotFoundError, OSError, ValueError, …): return _empty`. With `GCP_PROJECT_ID` unset, `get_storage_client()`
raises `ValueError` -> the reader returns an **empty frame**, indistinguishable from "nothing processed yet". This
produced a false "manifest empty / 0% coverage" scare during this sweep. Production consumers set the env and read
correctly (verified: 197,890 rows). **RETRACTED**: any suggestion that the sports-features manifest was wiped or that
the data-status UI shows 0% — the manifest is healthy and the consolidator is live (successful run every ~60s). Still
worth distinguishing a config error from empty data.

### C6. `fixture_stats` is the coverage outlier — **P2**

Per-group materialized coverage is ~100% everywhere except **`fixture_stats` 83.2%**, which holds **708 of the fleet's
942 total `attempted_failed` rows**. Remaining failures: `injuries` 136, `fixture_lineups` 46, `fixture_player_stats`
34, `fixture_events` 17, `fixture_features` 1.

- [x] [DIAG] P2. Root-cause the 708 `fixture_stats` failures; they dominate the entire sports failure budget. — already
      covered by `plans/active/sports_consolidated_closeout_2026_07_19.md` (same line item as the C3 atom-regrade todo
      above: "+ `fixture_stats` 708-failure root-cause"; see that doc for execution).

---

## D. Junk-symbol guard deletes real non-ASCII sports fixtures — **P1, cross-asset-group**

`instruments-service/instruments_service/engine/orchestrator/venue_core.py:408` rejects any instrument whose
`base_asset` / `raw_symbol` / `instrument_key` contains a non-ASCII character:

```python
if field and not field.isascii():
    return True, f"non-ascii ({field!r})"
```

The rule is **crypto-motivated** — its own docstring cites the 2026-06-24 audit finding CJK/meme test bases
(龙虾 / 币安人生 / 我踏马来了) on BINANCE/BITGET/ASTER. But `reject_junk_instruments` is **"Applied to EVERY asset group
right after the date filter, so junk symbols never reach `by_date/` (and therefore never reach the catalogue roll-up /
coverage / MTDS)"**. In SPORTS, non-ASCII is not junk — it is ordinary Latin-script team naming.

Measured live in the round-FIXTURES backfill run (`af-backfill-20260718-092543`, day=2021-11-26):

```
Junk-symbol guard 2021-11-26: 225 -> 203 instruments (rejected 22)   # ~9.8% of the date's universe
  BOLIVIA_PRIMERA_DIVISION:NACIONAL_POTOSI_v_SAN_JOSE        — non-ascii ('Nacional Potosí vs San José')
  BOLIVIA_NACIONAL_B:UNIVERSITARIO_DE_VINTO_v_VACA_DIEZ      — non-ascii ('Universitario de Vinto vs Vaca Díez')
  PORTUGAL_LIGA_3:UNIAO_DE_LEIRIA_v_UNIAO_SANTAREM           — non-ascii ('União de Leiria vs União Santarém')
  SPAIN_PRIMERA_DIVISION_RFEF_GROUP_1:UD_LOGRONES_v_…        — non-ascii ('UD Logroñés vs Real Valladolid II')
  SPAIN_PRIMERA_DIVISION_RFEF_GROUP_2:SANLUQUENO_v_ALBACETE  — non-ascii ('Sanluqueño vs Albacete')
  MEXICO_LIGA_PREMIER_SERIE_A:DEPORTIVO_ZAP_v_CANONEROS_…    — non-ascii ('Deportivo Zap vs Cañoneros Marina')
```

These are **real fixtures**. The loss is systematic and biased by geography (Iberian + Latin American leagues), it
happens at CAPTURE time so the rows never exist downstream, and it is invisible in coverage because the rejected
instruments never enter the denominator either — the date simply looks smaller.

**Fix direction**: the junk test must not be "any non-ASCII". Narrow it to the actual junk classes (CJK / emoji / symbol
ranges), or make the ASCII rule crypto-only and exempt sports. Latin-1/Latin-Extended accented characters are legitimate
identity, not noise.

- [x] [CODE] P1. ✅ Narrowed `_is_junk_instrument` so accented Latin characters are NOT rejected (target CJK/emoji
      ranges); added a regression test pinning `Sanluqueño` / `União` / `Potosí` as KEPT and `龙虾` / `币安人生` as
      REJECTED — `instruments-service@453e76f1`, 7/7 tests green 2026-07-30. Tracked in
      `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`, cross-referencing
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md`'s G1.4 (whose "not implemented" framing is itself
      stale — live-verified the guard already exists in code).
- [x] ✅ [DIAG] P1. Quantify corpus-wide loss (the ~9.8% on 2021-11-26 is one sampled date) and re-capture the affected
      date/league range once the guard is narrowed. **2026-07-30**: split into its own tracked todo (a single-date
      recapture takes >180s of real API-Football quota — VM-backfill-shaped, not an interactive call) in
      `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`. — **DONE THERE 2026-07-31; closed here
      2026-08-02 by `/na-eligibility-audit` (sports tranche) as a KEEP-NA-STALE citation fix, not new work.**
      [`/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`](/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md)'s
      `[DIAG] P1` is `[x]` and names this doc §D as its own `Source:`. Evidence there: 2021-11-26 re-validated **225 →
      225 instruments, 0 rejected** (was 225 → 203) against the live
      `instruments-store-sports-prd-central-element-323112`; a 2nd sample date (2021-11-20) surfaced a NEW residual
      non-Latin-script gap (Vietnamese `Công An Nhân Dân`, Azerbaijani `Səbail`) now carried as that same doc's own OPEN
      `[CODE] P2` — the residual is owned there, not dropped here. Side-discovery fixed en route:
      `instruments-service@627fd31c` (`--venues` case-mismatch silently returning 0 URDI records).

---

## E. Early-horizon sparsity is CAPTURE coverage, not market availability — **P1**

**RETRACTED (mine, 2026-07-18)**: I first attributed thin early buckets to "bookmakers haven't priced fixtures 24h out".
Operator challenged it ("could also be because we fetched odds on less fixtures earlier then added fixtures on narrower
time buckets"). Measurement says the operator is right.

Per-horizon fixture counts for day=2022-04-16 are NON-MONOTONIC, which market availability cannot explain (coverage
would rise steadily toward kickoff):

| horizon | fixtures | rows | observed bm window (min) | declared window |
| ------- | -------- | ---- | ------------------------ | --------------- |
| T-24h   | **25**   | 317  | 1433.7 – 1487.0          | (1380, 1500)    |
| T-12h   | 68       | 896  | 706.7 – 744.1            | (660, 780)      |
| T-6h    | 68       | 898  | 343.4 – 380.4            | (330, 390)      |
| T-4h    | 68       | 896  | 224.5 – 256.4            | (210, 270)      |
| T-2h    | 68       | 884  | 110.0 – 134.7            | (90, 150)       |
| T-1h    | **29**   | 270  | 50.5 – 70.0              | (45, 75)        |
| T-10m   | 67       | 870  | 5.6 – 14.9               | (5, 15)         |
| T-0     | **8**    | 27   | 0.0 – 2.4                | (-5, 5)         |

**Decisive test** — of the 43 fixtures present at T-6h but absent at T-24h, their EARLIEST observation is:

```
min=728  median=735  max=741 minutes before kickoff
observed earlier than 1440 min (24h): 0 of 43
```

A **13-minute spread across 43 fixtures** is a SINGLE capture event, not 43 bookmakers independently deciding to open a
market. Those fixtures entered our capture ~12.25h before kickoff and were never sampled at 24h. Note also that every
horizon samples only a NARROW SLICE of its declared window (T-24h declares 120 min wide, observed span is 53 min),
consistent with a small number of discrete polls rather than continuous coverage.

**Consequence**: the T-24h model row — the only horizon whose input scope is `["T-24h"]` alone — is built on the
THINNEST and most capture-biased sample we hold (25 of 68 fixtures, ~37%). Any model trained at T-24h is silently fitted
to whichever fixtures our poller happened to reach early.

**Capability gap**: there is **no `/v4/historical` support anywhere in the codebase** (grep-verified across
market-tick-data-service / instruments-service / unified-api-contracts). The Odds API exposes point-in-time snapshots,
but we cannot currently refetch a past T-24h window. The only odds cron is `uts-prod-mdps-odds-horizon-bucket-daily`
(`15 1 * * *`), which BUCKETS already-captured ticks — it does not capture.

**Operator 2026-07-18: credentials are available for BOTH live and batch**, so the remaining work is code + config, not
a credential ask.

- [x] ✅ [CODE] P1. **DONE 2026-07-31 — was ALREADY DONE, since 2026-04-11.** This finding's own "no `/v4/historical`
      support anywhere in the codebase" claim was WRONG even when written (2026-07-18) —
      `git log -S     "historical/sports"` on
      `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` shows the historical-endpoint
      calls (`_discover_fixtures` + `_run_league_fetch_loop`, both hitting `/v4/historical/sports/{sport}/odds`) landed
      in commit `76c920ba` (2026-04-11), 3+ months before this finding — and it's wired into production via
      `market_tick_data_service/adapters/umi_tick_provider.py:658` (`download_batch(date=date, data_types=data_types)`),
      not orphaned code. `sports_satellite_ao_dispatch_batch8_     2026_07_30.md`'s own triage repeated the same wrong
      "confirmed still absent... 2026-07-30" claim — a grep that somehow missed this file, propagated forward rather
      than caught. **Cost-per-snapshot, genuinely not previously measured (only formula-derived:
      `_CREDITS_PER_CALL = 60` = "10 × 3 markets × 2 implicit regions") — now EMPIRICALLY measured**: one real
      `/v4/historical/sports/soccer_epl/odds` call, `x-requests-remaining` delta before/after = exactly 60 credits,
      confirming the formula. (repo: market-tick-data-service, verification only — no code shipped, none needed)
- [x] ✅ [DATA] P1. **DONE 2026-07-31 — backfill + re-derivation already complete, verified via the existing
      `verify_ml_readiness.py` tool this codebase already has for exactly this check.** `day=2022-04-16` (this finding's
      own sample date, originally 25/68 fixtures at T-24h / 29/68 at T-1h / 8/68 at T-0) now reads 100% non-NULL at both
      target horizons (`T-24h`, `T-1h`; 594/594 cells, gate met). Broadened to an 11-day window
      (2022-04-10..2022-04-20): 10/10 real matchdays 100% ready; the 1 "missing" date (2022-04-12) has ZERO raw odds
      tick data at all (confirmed via `gcloud storage ls` — genuinely no fixtures that day, honest absence per the
      adapter's own documented "non-matchday skip" behavior, not a gap). No indication of WHEN/HOW this backfill ran (no
      commit/plan doc found citing it) — it simply happened, and this checkbox was never flipped to reflect it. (repo:
      features-service + market-tick-data-service, verification only — data already correct, no re-derivation needed)
- [x] ✅ [CONFIG] P1. **CLOSED 2026-08-04 — Tier-3 design verified, partially closes the gap; residual tracked as new
      [CONFIG] P2 below.** DIAG (`sports_satellite_ao_dispatch_batch8-004`, slot-5): (a) The Tier-3 config
      (`deployment-service/configs/sports-trigger-tiers.yaml`) defines 3 fixture-proximate snapshot triggers:
      `odds_t24h` (T-24h ±30min), `odds_t6h` (T-6h ±30min), `odds_t1h` (T-1h ±15min), each firing per-fixture via the
      Cloud Run `uts-prod-market-tick-data-service-fast-t1-recon` job → `OddsApiAdapter.download_batch()`. This replaces
      the single daily 12:00 UTC poll (the root cause) with per-fixture, per-horizon snapshots, which would give 100%
      fixture coverage at those 3 horizons (vs. the original 25/68 at T-24h). (b) However, the config explicitly names
      only 3 of the 8 declared `MODEL_HORIZONS` — T-12h, T-4h, T-2h, T-10m, and T-0 have NO dedicated forward trigger.
      The T-10m/T-0 near-kickoff horizons are partially covered by the live in-play WS connector
      (`mtds-live-sports-odds-api-trades` VM, RUNNING, 60s poll per `odds_api_ws.py`), but T-12h/T-4h/T-2h are a genuine
      forward-capture gap. (c) The historical backfill adapter (`/v4/historical`, `OddsApiAdapter._discover_fixtures` /
      `_run_league_fetch_loop`, live since 2026-04-11) CAN retroactively fill any horizon for any past date — so the
      combined forward + backfill path IS complete, but the forward-only path is not. (d) The `sports-scheduler-*` VM
      that executes the Tier-3 triggers is NOT currently running (confirmed via `gcloud compute instances list` in
      `asia-northeast1-c` — zero matches for the singleton-lock pattern `sports-scheduler-*`), so even the 3 named
      horizons are not being proactively captured right now. (repo: market-tick-data-service, deployment-service —
      read-only inspection, no code change). Evidence: `unified-trading-pm@<sha>` (this edit).
  - [ ] [CONFIG] P2. **Residual gap — add T-12h/T-4h/T-2h snapshot triggers + relaunch the sports-scheduler VM.** (a)
        Add `odds_t12h`, `odds_t4h`, `odds_t2h` entries to `deployment-service/configs/sports-trigger-tiers.yaml`'s
        `pre_match.triggers` list (follow the existing `odds_t24h`/`t6h`/`t1h` pattern — each with
        `cloud_run_job_name: "uts-prod-market-tick-data-service-fast-t1-recon"` and appropriate tolerances: ±30min for
        T-12h, ±15min for T-4h/T-2h). (b) Relaunch the sports-scheduler VM via
        `bash deployment-service/scripts/vm/launch-sports-scheduler-vm.sh` (the singleton lock confirms no running
        instance; SPOT OK per the scheduler's GCS-state-backed resume design). (c) Verify via a sample day's manifest
        that all 6 forward horizons (T-24h/T-12h/T-6h/T-4h/T-2h/T-1h) show full per-fixture coverage. (repo:
        deployment-service). Source: this DIAG's residual finding, 2026-08-04. **Already extracted — see
        `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s `[CONFIG] P2` todo (line ~85, `assigned_vm: planning`,
        still `- [ ]` open there too as of 2026-08-09) — not duplicating here.** Round-9 sweep flag (2026-08-09), for
        whoever picks up batch10's copy: `sports_satellite_ao_dispatch_batch11_2026_08_09.md`'s Deferred section
        found this todo's "relaunch the sports-scheduler VM" premise may be stale — 3 independent, more current active
        docs (`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`,
        `sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`,
        `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`) establish `sports-scheduler` actually
        runs as the Cloud Run Job `uts-prod-sports-scheduler` via `uts-prod-sports-scheduler-cron` (`*/5 * * * *`), not
        a standalone VM, and that exact job is under active OOM investigation right now — verify the real launch
        mechanism before executing step (b) as literally written.
- [x] [CONFIG] P1. Enable the live in-play connector (`market_tick_data_service/live/connectors/odds_api_ws.py`) now
      that credentials exist — this is what populates the HT horizon, which currently emits nothing. HT is already
      declared in `MODEL_HORIZONS` + `FEATURE_HORIZONS`, so it populates with NO contract change. (Its prior
      "population" was the T-0 fallback living off the post-kickoff bucketing leak — see B1.) — **STALE, superseded,
      resolved 2026-07-30 batch8 triage**: live-verified already shipped + running (`mtds-live-sports-odds-api-trades`
      VM, 60s poll) per `sports_live_availability_and_source_latency_2026_07_24.md`'s LIVE_ODDS row and
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md`'s 2026-07-29 update. No action needed here.
- [ ] [MODEL] P2. Consider adding T-6h or T-2h as a MODEL horizon: both carry 68 fixtures vs T-24h's 25 (2.7x coverage),
      are safely pre-match, and fall after most team news. **Resolved by the dated `✅ OPERATOR RULING 2026-08-08`
      banner at the top of this doc** (add BOTH, not either/or) — implemented by
      `sports_taxonomy_p3_consumers_2026_08_08.md`'s `[CODE] P0` todo (line ~125, `assigned_vm: planning`, reconfirmed
      still open/active 2026-08-09). Not duplicating here.

---

## F. Canonical-naming audit of the sports manifests — **P1**

Operator 2026-07-18: data-status in deployment-ui/api used to LIST every instrument_type / data_type / chain present in
the GCS data + manifest per asset group — the way non-canonical naming and duplication got caught. **That listing was
removed and needs to come back.** In the meantime the same list is queryable directly. First pass below (read via
`read_availability_index`) already finds real violations.

### F1. CASE-duplication — the same value stored twice in two cases

`market-data-sports` `data_type` (13 distinct) contains **three duplicate pairs**:

| canonical?      | also present as |
| --------------- | --------------- |
| `ODDS`          | `odds`          |
| `ODDS_MOVEMENT` | `odds_movement` |
| `ODDS_SNAPSHOT` | `odds_snapshot` |

`instrument_type` (15 distinct) contains two more: `PADDYPOWER`/`paddypower`, `PINNACLE`/`pinnacle`.

Every case-pair silently splits the same logical shard set into two manifest identities — coverage, dedupe and any
group-by are wrong wherever this occurs.

### F2. DIMENSION POLLUTION — `instrument_type` is holding venues

Live `instrument_type` values:
`PADDYPOWER, PINNACLE, SPORT, betmgm, betway, bovada, coral, fanduel, ladbrokes_uk, odds, paddypower, pinnacle, skybet, unibet_uk, williamhill`.

Only `SPORT` is plausibly an instrument type. Eleven are **bookmakers** (belong in `venue`) and `odds` is a **data
type**. So three different dimensions are being written into one column.

### F3. Timeframe baked into `data_type`

`odds_horizon_bucket` also appears as `odds_horizon_bucket_15m` / `_1h` / `_4h` / `_1d`. A `timeframe` column already
exists in the v9 schema, so the suffixed variants look like a second SSOT for the same axis. **OPERATOR QUESTION — which
is canonical?**

### F4. Suspect `venue` values

`venue` (37) is mostly uppercase-canonical bookmakers, but includes `FOOTBALL` (a sport, not a venue) and `ODDS_API` (a
source/vendor — `source` already carries `odds_api`). **OPERATOR QUESTION — are these intended?**

### F5. features-sports still carries the 4 deleted dimension groups

`feature_group` (18) still lists `coaches` / `players` / `referees` / `rounds`. The CODE is deleted (A2) but the
manifest rows remain — this is the outstanding A2 DATA purge.

### F6. instruments-sports manifest is UNREADABLE via the standard reader

`read_availability_index("instruments-store-sports-prd-…")` raised `ManifestConsolidatorStaleError` ("consolidated blob
age 173.4s > 120s threshold — falling back to per-VM shards"). The instruments-sports consolidator is running behind its
own staleness budget, so the audit could not enumerate that bucket at all. Needs its own check — a manifest nobody can
read is a coverage blind spot.

- [x] [CODE] P1. Restore the data-status "distinct dimension values present per asset_group" listing in deployment-api +
      deployment-ui (instrument_type / data_type / venue / chain / pipeline_mode / source), so non-canonical naming and
      duplication are visible again instead of needing an ad-hoc query. — **clear duplicate, resolved 2026-07-30 batch8
      triage**: already an open, properly-scoped todo in `prediction_phase_c_data_status_ui_2026_07_24.md` Phase C (same
      feature, generic per-asset_group, explicitly "mirrors the identical tradfi Phase-C todo") — sports is covered
      automatically once that ships. No separate todo needed here.
- [x] [DATA] P1. Normalise the F1 case-duplicates to ONE canonical case and rewrite the affected manifest rows. —
      already covered by `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C's casing reconciliation work
      supersedes this; see that doc for execution).
- [x] [CODE] P1. Fix the F2 writer(s) putting bookmakers + `odds` into `instrument_type`; add a QG assertion that
      `instrument_type` only accepts declared UAC values for the asset group. — already covered by
      `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C's writer-fix work, e.g.
      market-tick-data-service@7ffabf77; see that doc for execution).
- [x] [ASK] P1. Operator decisions needed: F3 (is `odds_horizon_bucket_{tf}` canonical, or does `timeframe` own that
      axis?) and F4 (are `FOOTBALL` / `ODDS_API` valid `venue` values?). **F3 answered elsewhere**: `timeframe` owns
      that axis — bare `odds_horizon_bucket` + populated `timeframe` is canonical (F3 timeframe migration DONE per
      `sports_consolidated_audit_2026_07_19.md` § 1.3). **F4 answered 2026-07-27**
      (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Phases 0-4, cross-referenced against the parent OOM issue
      doc's own Update 5 investigation): NEITHER is valid as a per-row `venue` value on a candle/manifest row where a
      real bookmaker is knowable. **`FOOTBALL`**: a genuine BUG, not a valid venue — the sport token
      (`FOOTBALL:{BOOKMAKER}:{MARKET}:...`) was being misread as `venue` by a generic (non-sports-aware) instrument-id
      splitter; fixed `unified-trading-library@bcd73241` (`mdps_t1_recon...` Update 5). **`ODDS_API`**: valid ONLY (a)
      as a UAC registry-level vendor/aggregate-class venue entry (`VENUES_BY_ASSET_GROUP["sports"]`, "Multi-bookmaker
      odds aggregator (raw tick data source)" — see `/codex/02-data/venue-availability.md`) and (b) as the
      `reprocess_sports_odds.py` manifest's COARSE per-day AGGREGATE SENTINEL row (deliberate, unchanged). It is
      **invalid** as a FINE per-shard/per-row venue stand-in wherever the real bookmaker is already present in the data
      — that was a genuine, now-fixed conflation in `reprocess_sports_odds.py`'s fine manifest rows
      (`market-data-processing-service@6f7422e` forward fix + `@a047b29` backfill migration).
- [x] [DIAG] P1. F6 — why is the instruments-sports consolidated index persistently older than its 120s budget? —
      **clear duplicate, resolved 2026-07-30 batch8 triage**: already fully root-caused in
      `plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md` (no per-AG staleness-budget
      override for sports while the consolidator cadence is ~11 min vs. the 120s generic default). No new diagnosis
      needed here; see that issue doc for the fix.
- [x] [AUDIT] P2. Extend this audit to leagues / fixtures / betting-market identifiers (operator: "in sports case
      leagues and fixtures and betting market canonicals are relevant too") and fold the result into the migration so
      everything lands on one SSOT. **2026-07-30 batch8 triage**: extracted as a tracked todo in
      `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`. — **DE-DUPLICATED here 2026-08-02 by
      `/na-eligibility-audit` (sports tranche), KEEP-NA-STALE citation fix. ⚠️ This `[x]` means "no longer tracked
      HERE", NOT "done"** — the work is still genuinely OPEN as
      [`/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`](/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md)'s
      `[ ] [AUDIT] P2`, which restates this item verbatim (all 3 identifier classes + the fold-into-Track-C step) and
      names this doc §F as its own `Source:`. That doc is `status: active`, `assigned_vm: planning`, so the item is live
      in the AO backlog; leaving it open here as well double-counted one piece of work in the NA corpus. Same convention
      as the 5 sibling items above (lines ~450/642/648/651/670) already closed as tracked-elsewhere.

---

## Continues in PART 2 and PART 3

**This doc was split 2026-07-26 (line-cap remediation — was 1,843L, over the `plans/active/` 1,000L hard cap; see
`check_line_caps.sh` / precedent `sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md`) into 3 files by
section boundary, verbatim, byte-for-byte, in original order. No content was moved between open/closed status — each
part carries whatever mix of `[x]`/`[ ]` items fell in its line range.** Total open checkboxes: 73 (18 here in Part 1 §
A-F, 24 in Part 2 § G-N, 31 in Part 3 § O-AA) — unchanged from the pre-split count.

- **PART 2** — `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`: § G (round-
  FIXTURES backfill operational log), § H (api-football singleton violation), § I (control conflict — enrichment fleet
  auto-relaunch), § J (F6 resolved — consolidator staleness budget), § K (canonical migration phased plan), § L
  (features launcher replay), § M (rate-limiting divisor bug), § N (sledgehammer waste).
- **PART 3** — `/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md`: § O (round
  RAW vs catalogue gap), § P (derive-then-fetch round backfill), § Q (round derivation shipped/applied), § R
  (competition_phase root cause — stale entity), § S-AA (dated 2026-07-19 findings/corrections: total_matchdays
  hardcoded, round-blank scoping, legacy-entity read, cup-competition correction, end-to-end validation, launcher hint
  bug, matchday persistence defect, monitoring-metric lesson).

Any todo count/citation elsewhere in the corpus referencing "this doc" as one 1,843-line file with 73 open todos is
still accurate in aggregate (same 73 total, now split across 3 files) — only the file path for a specific finding may
have moved; use the section index above to locate it.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — MIXED, left NA: 10 of the 12 open todos are
  bounded engineering, but `[MODEL] P2` ('consider adding T-6h or T-2h as a MODEL horizon') is a modelling judgment call
  and `[AUDIT] P2` ('extend this audit to leagues / fixtures / betting-market identifiers and fold the result into the
  migration') is open-ended by construction — neither has an outcome a worker can settle alone
- **na-eligibility-audit 2026-08-02**: re-read (in scope again — 3 substantive commits landed after the 07-30 marker:
  `03d0ef7c7`, `425366f35`, `26c07e337`, which closed 8 of the 12 then-open todos). **KEEP-NA stands; 4 open → 2 after
  this pass.** Verdicts: **2 × KEEP-NA-STALE** (closed here as citation fixes — §D `[DIAG] P1`, already DONE in batch8
  2026-07-31; §F `[AUDIT] P2`, extracted verbatim into batch8 and still open THERE, so keeping it open here too was
  double-counting one item in the NA corpus). **2 × KEEP-NA valid**: §E `[CONFIG] P1` is explicitly gated on batch8's
  still-open `[DIAG] P2` by its own text ("Leave open until that todo resolves it one way or the other" — gate
  re-verified, that todo is still `[ ]`), and §E `[MODEL] P2` remains the modelling judgment call the 07-30 marker
  named. No RECLASSIFY: the doc's own remaining work is a gated item plus a design call, and every bounded piece has
  already been extracted to `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`
  (`assigned_vm: planning`) — flipping this doc would dispatch duplicates of that batch
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped `honest_coverage_report.py` (§C tooling
  gaps, already resolved/tracked in `sports_consolidated_closeout_2026_07_19.md`) for
  `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md`, which now holds the gating todo for this
  doc's one genuinely open item (§E's `[CONFIG] P1`).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 2 open items: 1 dependency-blocked, 1 genuine work.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, both open items now cited elsewhere, doc stays
  NA. (1) §E `[CONFIG] P2` (trigger-tier residual gap — add `odds_t12h`/`odds_t4h`/`odds_t2h` + relaunch the
  sports-scheduler VM) — **KEEP-NA-STALE, already-duplicated**: extracted verbatim (same source cited) into
  `/plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md` todo 2 (`assigned_vm: planning`, status: active).
  (2) §E `[MODEL] P2` (consider T-6h/T-2h as MODEL horizons) — resolved by the dated `✅ OPERATOR RULING 2026-08-08`
  banner at the top of this doc ("add BOTH T-2h and T-6h") and is already being implemented by
  `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`'s "ML" section, which names this doc's open todo verbatim.
  Neither item is dispatchable from this doc without duplicating an already-active plan in the same `parent_epic` — no
  reclassification, citation-only.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA-STALE, valid — verdict unchanged from 2026-08-08, added
  inline citations at both open todos (§E `[CONFIG] P2` line ~611, §E `[MODEL] P2` line ~627) rather than only here.
  New this pass: `sports_satellite_ao_dispatch_batch11_2026_08_09.md`'s Deferred section (dated yesterday/today)
  flagged the `[CONFIG] P2` item's "relaunch the sports-scheduler VM" premise may be stale (real mechanism is the
  Cloud Run Job `uts-prod-sports-scheduler`, not a VM script) and conflicts with an active OOM investigation
  (`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`) — flagged inline at the todo itself for whoever
  executes batch10's copy; not re-extracted here (already `assigned_vm: planning` there, still open). `[MODEL] P2`
  reconfirmed still tracked and active in `sports_taxonomy_p3_consumers_2026_08_08.md`. Doc stays `assigned_vm: NA`.