---
doc_type: issue
title:
  Sports features-layer findings sweep — a shape-mismatch normalizer silently zeroes 4 years of lineups/coaches, 116
  odds_features shards remain leaked behind a loss guard that cannot express "known-corrupt baseline", and the
  honest-coverage tooling is non-functional below group grain (calculator-grain mismatch + league_id namespace split)
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
    sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md,
    sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md,
  ]
created: 2026-07-18
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
---

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

- [ ] [CODE] P0. Fix `_normalize_fixture_lineups` to parse the flat one-row-per-player shape + emit `coach_*`; add a
      regression test pinning BOTH shapes (flat 40 rows -> 40 rows; legacy nested -> unchanged).
- [ ] [DATA] P0. Re-derive `fixture_lineups` (and dependent groups) across 2019-2026 from existing raw; verify per-year
      captured shard counts stop collapsing after 2023.

### A2. The four empty dimension tables are benign — delete + document — **P2**

Verified in BOTH registries: `unified_api_contracts/canonical/domain/features/required_inputs.py` +
`.../sports/feature_upstream.py` declare **zero** requirements on `PLAYERS` / `COACHES` / `REFEREES` / `ROUNDS`.
`manager_calculator.py:8-12` explicitly documents coaches as "optional — may be None or empty" with a fixture-history
fallback. `export_coaches` / `export_rounds` are unconditional stubs; `export_players` / `export_referees` read sources
that are structurally unpopulatable (`_fetched_players` is never appended to anywhere; see A3 for referees).

**Operator decision (2026-07-18): delete them and document where the real data lives** — four always-empty tables while
the data sits elsewhere is actively misleading (workspace rule: delete deprecated code, no shims; never silent
placeholders).

- [ ] [CODE] P2. Delete `export_players`/`export_coaches`/`export_referees`/`export_rounds` + their
      `PLAYERS_/COACHES_/REFEREES_/ROUNDS_COLUMNS`, and every registration (`cli/batch_write.py`,
      `cli/handlers/batch_handler.py`, `cli/handlers/_available_at_helpers.py`, `exporters/validation.py`,
      `schemas/output_schemas.py`, `docs/SCHEMA_VALIDATION.md`).
- [ ] [DOC] P2. Document the real homes in code: coach -> `fixture_lineups.coach_id/coach_name`; referee ->
      `fixtures.referee_id`; player identity -> `fixture_lineups` + `player_stats` (`player_id`/`player_name`); rounds
      -> genuinely absent upstream.
- [ ] [DATA] P2. Purge the resulting always-empty manifest rows / shards so they stop inflating the coverage denominator
      (4 groups x ~4,216 dates of `empty_confirmed`).

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

- [ ] [DATA] P1. Backup-then-rebuild the **113** fixable shards (116 minus the 3 in B2): copy each shard to a backup
      prefix, delete, re-derive, verify `steam@T-24h == 0`. Operator-approved 2026-07-18 (option A: keeps the guard
      fully protective rather than weakening it).

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

- [ ] [DIAG] P1. Confirm whether all raw observations for these 3 dates are post-kickoff; if yes, record
      `empty_confirmed` (honest absence) instead of `attempted_failed`, and delete the leaked legacy shadow.

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

- [ ] [CODE] P1. Change the `odds/derived/fixture_features` writer + manifest row_key atom from
      `(feature_group, date[, league])` to `(calculator, date[, league])`; keep writer/manifest/status/gate/UI identical
      (workspace hard rule). Reconcile the league_id namespace (C2) in the same change.

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

- [ ] [DIAG] P2. Root-cause the 708 `fixture_stats` failures; they dominate the entire sports failure budget.
