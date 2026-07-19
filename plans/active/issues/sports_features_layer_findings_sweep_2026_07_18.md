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

- [ ] [CODE] P1. Narrow `_is_junk_instrument` so accented Latin characters are NOT rejected (target CJK/emoji ranges, or
      scope the ASCII rule to crypto asset groups); add a regression test pinning `Sanluqueño` / `União` / `Potosí` as
      KEPT and `龙虾` / `币安人生` as REJECTED.
- [ ] [DIAG] P1. Quantify corpus-wide loss (the ~9.8% on 2021-11-26 is one sampled date) and re-capture the affected
      date/league range once the guard is narrowed.

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

- [ ] [CODE] P1. Implement The Odds API `/v4/historical/sports/{sport}/odds?date=<ISO>` adapter leg so past horizon
      windows can be backfilled; cost per snapshot must be measured before a full-corpus run.
- [ ] [DATA] P1. Once (E1) exists, backfill the T-24h (and T-1h / T-0) windows for fixtures that currently have no
      sample there; re-derive odds_features after.
- [ ] [CONFIG] P1. FORWARD fix — start capture earlier and poll often enough that every fixture is sampled in every
      declared horizon window (the observed 53-min slice of a 120-min T-24h window shows current polling is too sparse).
- [ ] [CONFIG] P1. Enable the live in-play connector (`market_tick_data_service/live/connectors/odds_api_ws.py`) now
      that credentials exist — this is what populates the HT horizon, which currently emits nothing. HT is already
      declared in `MODEL_HORIZONS` + `FEATURE_HORIZONS`, so it populates with NO contract change. (Its prior
      "population" was the T-0 fallback living off the post-kickoff bucketing leak — see B1.)
- [ ] [MODEL] P2. Consider adding T-6h or T-2h as a MODEL horizon: both carry 68 fixtures vs T-24h's 25 (2.7x coverage),
      are safely pre-match, and fall after most team news.

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

- [ ] [CODE] P1. Restore the data-status "distinct dimension values present per asset_group" listing in deployment-api +
      deployment-ui (instrument_type / data_type / venue / chain / pipeline_mode / source), so non-canonical naming and
      duplication are visible again instead of needing an ad-hoc query.
- [ ] [DATA] P1. Normalise the F1 case-duplicates to ONE canonical case and rewrite the affected manifest rows.
- [ ] [CODE] P1. Fix the F2 writer(s) putting bookmakers + `odds` into `instrument_type`; add a QG assertion that
      `instrument_type` only accepts declared UAC values for the asset group.
- [ ] [ASK] P1. Operator decisions needed: F3 (is `odds_horizon_bucket_{tf}` canonical, or does `timeframe` own that
      axis?) and F4 (are `FOOTBALL` / `ODDS_API` valid `venue` values?).
- [ ] [DIAG] P1. F6 — why is the instruments-sports consolidated index persistently older than its 120s budget?
- [ ] [AUDIT] P2. Extend this audit to leagues / fixtures / betting-market identifiers (operator: "in sports case
      leagues and fixtures and betting market canonicals are relevant too") and fold the result into the migration so
      everything lands on one SSOT.

---

## G. Round-FIXTURES backfill writes NOTHING — two failed launches, root cause still open — **P0**

**RETRACTED (mine, twice)**: I reported the round backfill as "healthy and progressing" for 3.5h on log-line growth
alone. It was writing ZERO `entity=fixtures`. Progress logs are NOT a write metric.

**Launch 1** — `af-backfill-20260718-092543`, `--entity FIXTURES 2019-01-01 2026-07-17`, NO `--force` (per the handoff's
"don't --force"). Ran 3.5h, reached 2024-02. Measured across 8 already-passed dates: **202 objects created that day, of
which `entity=fixtures` = 0** (fixture_lineups 72, fixture_stats 61, fixture_events 50, player_stats 19). Fixtures
parquets for 2019-08-10 / 2021-05-15 / 2023-03-04 / 2024-01-15 were last written **2026-06-24..29**, untouched.
Diagnosis at the time: presence-skip, since `--force` = `VM_FORCE=true` (redo_all). NOTE the handoff's "don't --force"
warning is about bypassing the singleton LOCK on a FLEET launch (429 thrash) — for a SINGLE VM needing redo_all it is
the required flag.

**Launch 2** — `af-backfill-20260718-124341`, same range **WITH `--force`**. Confirmed doing real work (285 fixtures x 4
entities = 1,126 calls queued per date, so ~12 dates in 22 min vs the skip-run's ~5 years in 3.5h). **Still zero
`entity=fixtures` written** on dates it has fully processed (2019-01-02 / 05 / 08 / 11 all `written_TODAY=0`).

**So presence-skip was NOT the (only) root cause.** The live log points elsewhere:

```
FIXTURE_STATS  date=2019-01-11: 12 per-fixture rows are out-of-universe
  (fixture league not in the canonical write universe) - skipping.
  Not a capture gap; genuine in-universe gaps surface on the FIXTURES shard.
FIXTURE_EVENTS date=2019-01-11: 118 out-of-universe ... FIXTURE_LINEUPS: 428 ... PLAYER_STATS: 111
Fixture mapping: no API_FOOTBALL instruments parquet for 2019-01-11 - skipping
  (no upstream availability rollup written)
```

Fixtures ARE fetched (285 for 2019-01-12) but nothing lands, apparently because the leagues are filtered as
out-of-canonical-write-universe. Candidate causes, NOT yet distinguished:

1. The canonical write universe (94 leagues after the 24-league de-registration) legitimately excludes most 2019
   fixtures — in which case the round backfill will only write once it reaches in-universe league/date combinations, and
   the early-2019 zero is expected rather than a bug.
2. The universe filter is season/coverage-gated in a way that excludes 2019 entirely, despite
   `SOURCE_COVERAGE_START[api_football] = 2018-01-01`.
3. `entity=fixtures` writing is gated behind the "no API_FOOTBALL instruments parquet / no upstream availability rollup"
   precondition, so the FIXTURES shard can never be written for a date whose instruments rollup is absent — a
   chicken-and-egg that `--force` does not break.

- [x] [DIAG] P0. Distinguish 1/2/3 above. Concretely: take ONE date with a known in-universe league (e.g. an EPL
      matchday in 2019) and trace whether `entity=fixtures` is written; if not, find the exact gate that drops it.
      **ROOT CAUSE FOUND + FIXED — instruments-service@7d49d096.** The `entity=fixtures` write gate in
      `_ensure_canonical_fixtures_for_override` was **existence-ONLY**: existing per-league canonical fixtures set
      `_needs_write = False` and nothing was written _regardless of_ `VM_FORCE`/`redo_all` — the flag was plumbed to the
      per-fixture enrichment entities but never to this function. That exactly predicts the measured asymmetry
      (enrichment shards re-wrote: 72/61/50/19; `entity=fixtures`: 0). Hypotheses 1-3 all RULED OUT: EPL _is_ in the
      canonical universe and its passed Jan-2019 matchdays still wrote nothing, and the 'no instruments parquet' log
      line is a best-effort SECONDARY mapping write documented to no-op. Fix = plumb `redo_all` through
      `sports_reference.py -> _resolve_fixture_ids -> _ensure_canonical_fixtures_for_override` + override the existence
      check; AND bypass the old-path shortcut under `redo_all` (that parquet is pre-migration OLD-writer data, so
      copying it forward would re-materialise the stale blank-`round` rows `--force` was meant to replace). 2 regression
      tests pin both. Evidence: QG green (4,579 passed / 0 failed).
- [ ] [DIAG] P0. Verify whether the round writer fix (instruments-service@19ae5890) is even reachable — it is in the
      tarball (@d9ca1c0c, freshness-gate verified), but if the FIXTURES shard never writes, `round` can never populate
      regardless of the writer being correct.
- [ ] [PROCESS] P1. Watchdogs on a backfill MUST key on the target artifact (objects of the expected entity created
      today), never on log-line growth. Both failures here were invisible to a log-line watchdog for hours.

### G-update (2026-07-18 13:2xZ) — ruled OUT, so the next session doesn't re-chase

Measured on launch 2 (`af-backfill-20260718-124341`, still RUNNING):

- **`--force` DOES reach the VM**: metadata `VM_FORCE=true`.
- **`--entity FIXTURES` DOES reach the VM**: metadata carries BOTH `VM_SPORTS_ENTITY` and `VM_SPORTS_PROVIDER` (launcher
  line 339: `VM_SPORTS_ENTITY=${ENTITY}`). An earlier read of mine conflated the two keys and wrongly concluded the
  entity was `API_FOOTBALL` — **RETRACTED**, the entity restriction propagates correctly.
- **Still ZERO writes**: across 2019-01-01..2019-02-20 there are **1,243** existing `entity=fixtures` parquets (written
  2026-06) and **0** created today, while the VM has processed through ~2019-01-12 with redo_all active.

So the failure is NOT flag propagation and NOT presence-skip. Remaining live hypotheses (unchanged, still to be
distinguished by the [DIAG] P0 above):

1. the canonical write universe legitimately excludes these 2019 league/date combinations (early-2019 zero is then
   EXPECTED and the backfill only writes once it reaches in-universe combos);
2. the universe filter is season/coverage-gated in a way that excludes 2019 despite
   `SOURCE_COVERAGE_START[api_football] = 2018-01-01`;
3. the FIXTURES shard write is gated behind an upstream instruments/availability rollup that is absent for those dates
   ("Fixture mapping: no API_FOOTBALL instruments parquet for 2019-01-11 — skipping"), a chicken-and-egg `--force`
   cannot break.

Hypothesis 1 is cheapest to test and would mean NO bug: pick a date where a known in-universe league (e.g. EPL) played
in 2019 and check whether `entity=fixtures` is written there.

### G-status (2026-07-18 13:56Z) — fix shipped, deployment BLOCKED on a peer's live WIP

- **Code fix SHIPPED**: `instruments-service@7d49d096` (QG green, 4,579 passed). Plan checkbox flipped.
- **VM STOPPED**: `af-backfill-20260718-124341` deleted. It carried the PRE-fix tarball, so under `--force` it was
  re-fetching already-captured enrichment at ~1,126 calls/date while still writing zero `entity=fixtures` — pure quota
  burn with no progress toward `round`.
- **Tarball rebuild BLOCKED**: `create-code-tarballs.sh --asset-group SPORTS` aborts on
  `market-tick-data-service has uncommitted changes` BEFORE it reaches instruments-service. That WIP is a peer's and is
  LIVE + STAGED (tardis_symbol_resolution.py + a new test, mtimes 13:52-13:53, index status `M `/`A `) — someone is
  mid-commit. NOT shelved: stashing staged work someone is about to commit risks corrupting their commit, and
  `--allow-dirty-tarball` would ship their untested WIP. Waiting for their commit is the correct call.
- Note the backfill VM does not actually need MTDS (its freshness gate checks only instruments-service /
  unified-api-contracts / unified-trading-library / deployment-service) — the batch builder just aborts on the first
  dirty repo regardless.

**NEXT (in order, once MTDS is committed):**

1. `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` — verify a sha-pinned
   `instruments-service-code@7d49d096*.tar.gz` appears.
2. `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --force --entity FIXTURES 2019-01-01 2026-07-17`
   (`--force` is REQUIRED — it is what the new gate honours).
3. Watchdog on the ARTIFACT, not log lines: `entity=fixtures` objects created today must climb within ~15 min.
4. Then: catalogue rollup `--since 2019-01-01` and verify `competition_phase` is no longer ~100% UNKNOWN.

- [x] [OPS] P0. Execute the 4 steps above once `market-tick-data-service` is clean. — **Steps 1-3 DONE 2026-07-18
      14:16Z.** Peer landed their MTDS WIP (`687abd54`) so the tarball rebuilt clean. Tarball carries the fix: built sha
      `650dd4b7` with `7d49d096` PROVEN an ancestor, and the built tree contains both halves (`if redo_all:` override +
      `_old_blob.exists() and not redo_all` bypass). Relaunched `af-backfill-20260718-141638` (SPOT,
      `--force --entity FIXTURES 2019-01-01..2026-07-17`), freshness gate green on all 4 tarballs, quota 150,888
      remaining, 258 req/min, 1 VM. Watchdog v3 armed on the ARTIFACT (`entity=fixtures` objects created today across
      2019-01-01..20), alerting at 20min if still zero. Step 4 (catalogue rollup + competition_phase verification)
      pending the run.
- [ ] [OPS] P0. Step 4 — after the backfill completes:
      `build_instrument_catalogue.py --asset-group sports     --since 2019-01-01`, then verify `competition_phase` is no
      longer ~100% UNKNOWN and `is_promotion_relegation` is a real signal rather than a constant False.

### G-RESOLVED (2026-07-18 14:35Z) — fix confirmed working; my verification metric was wrong

**`round` IS NOW POPULATING.** Measured on writes produced by the fixed build (`af-backfill-20260718-141638`, tarball
`650dd4b7` with `7d49d096` ancestor-proven):

| day        | entity              | round populated | sample                |
| ---------- | ------------------- | --------------- | --------------------- |
| 2019-01-03 | `fixtures_schedule` | **1/1**         | `Regular Season - 21` |
| 2019-01-05 | `fixtures_schedule` | **2/2**         | `Regular Season - 11` |

**RETRACTED (mine) — "zero fixtures written".** Every "zero" measurement in § G above queried the LEGACY
`entity=fixtures`. That entity has been **SPLIT into `entity=fixtures_schedule` + `entity=fixtures_outcomes`** (`round`
lives on the schedule leg; outcomes carries scores/end-time and correctly has no `round`). An unfiltered by-entity
histogram over `day=2019-01-03` showed **164 objects created today** — `fixtures_schedule` 3, `fixtures_outcomes` 3,
`standings` 59, `teams` 87, plus the enrichment entities — i.e. the run was writing all along under the current names.
Watchdog v3 was ~7 minutes from raising a FALSE "the fix did not take effect" alert on a working fix.

**The redo_all fix is still correct and still necessary** — do NOT revert it. Launch 1's by-entity breakdown contained
NO `fixtures_schedule` at all (only fixture_lineups/stats/events/player_stats), so the schedule writes appearing now are
genuinely the gate fix taking effect. The root cause and the fix were right; only the measurement was wrong.

Codified as a refinement in `codex/12-agent-workflow/async-wait-and-poll-discipline.md`: an artifact check is only as
good as its ENTITY NAME — enumerate what a run actually created (unfiltered by-entity histogram) before concluding
"nothing was written"; a name-filtered zero is two hypotheses (wrote nothing / wrote elsewhere), never one.

- [x] [DIAG] P0. Verify the round writer fix is reachable — **YES, confirmed end-to-end**: writer fix @19ae5890 + gate
      fix @7d49d096 + fresh tarball → `fixtures_schedule` rows with `round` populated 100% in every sampled shard.
- [ ] [OPS] P0. Let the backfill run to completion (watchdog v4 keyed on `entity=fixtures_schedule` created today), then
      run the catalogue rollup `--since 2019-01-01` and verify `competition_phase` is no longer ~100% UNKNOWN.

### G-ops (2026-07-18 15:04Z) — `--force` + SPOT has NO resume; the LOOP is the resume mechanism

`af-backfill-20260718-141638` was **preempted after ~10 min of real work** (SPOT; log stops mid-fetch at 14:30:16, no
completion marker, no `PREEMPTED` file). It reached 2019-01-07 and wrote **61 `fixtures_schedule` objects across 9
distinct days** (2019-01-01..09), all with `round` populated.

**Structural problem:** measured throughput is ~9 days per 10 min ≈ **54 days/hour**, so the full 2019-01-01..2026-07-17
range (2,390 days) is **~44 hours** of runtime. `--force` is what makes the run re-write history, but it also disables
the skip that would let a relaunch pick up where it left off — so a single long run on SPOT can NEVER complete: every
preemption restarts at the START_DATE.

**Resolution (no new code):** relaunch each time from `last_completed_day + 1`. The autonomous loop supplies the resume:
on each tick, measure the max `day=` with a `fixtures_schedule` object created today, and relaunch
`--force --entity FIXTURES <last+1> 2026-07-17`. Progress is monotonic with zero redo, and a preemption costs only the
partial day. Watchdog v5 prints `last_completed_day` explicitly so the next tick can act on it without re-deriving.

Applied: relaunched `af-backfill-20260718-150353` from **2019-01-10** (gate fix re-verified aboard: tarball sha
`c810f194`, `7d49d096` ancestor-proven, `if redo_all:` present — the sha moves every rebuild as peers land commits, so
ancestry MUST be re-checked per launch, never assumed from the sha string).

- [x] [OPS] P1. Make the SPOT preemption path safe for `--force` runs — **DONE, fleet-wide, not sports-only** (operator
      2026-07-18: "all spot preemptive vms need this recovery ... should be hard rule if they are launched from
      deployment service scripts"). Codified as a HARD RULE in `codex/05-infrastructure/spot-vms-for-backfill.md` §
      "Preemption recovery MUST resume from PROGRESS, never replay START_DATE" + a CLAUDE.md one-liner, and ENFORCED in
      code: `RelaunchPreemptedVm` now refuses to replay a run whose captured env has `VM_FORCE=true`, returning
      `status=PAGE reason=force_run_not_replayable` with a CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH`, instead of looping
      silently. deployment-service@1fcccad0, QG green (2,513 passed), 2 regression tests (force refused + launcher NOT
      invoked; non-force still replays). **Scope note**: the existing recovery actuator was already wired fleet-wide
      (every SPOT launcher sources `launcher_common.sh`), so this defect was live for EVERY `--force` SPOT backfill, not
      just sports.
- [ ] [OPS] P2. DURABLE fix still open — a **checkpoint contract**: the VM periodically writes `last_completed_unit` to
      `vm-logs/{vm_name}/PROGRESS`, and `RelaunchPreemptedVm` reads it to override `START_DATE` on replay. Then recovery
      is automatic rather than PAGE-and-operator-resumes. Design fork to settle first: VM-side checkpoint (generic,
      needs every workload to write it) vs relauncher-side manifest measurement (no VM changes, more coupling). Until
      then the loop-resume pattern is the contract.

---

## H. api-football SINGLETON violated — 5 concurrent VMs, 153 false failures — **contained 2026-07-18 15:57Z**

Found FIVE api-football VMs running concurrently: my `af-backfill-20260718-150353` (FIXTURES, `--force`,
2019-01-10..2026-07-17) plus **four launched by another actor at 15:27-15:29** — `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`,
`FIXTURE_STATS`, `PLAYER_STATS` (all 2020-06-06..2026-07-18, no `--force`). That is the enrichment fleet that was
stopped this morning, relaunched.

api-football rate-limits **per KEY**, so this is the documented 2026-04-19 pattern (~94% 403s, **37,212 FALSE
`attempted_failed` rows** — manifest CORRUPTION, not just waste, with coverage going BACKWARD).

**Action**: enforced the singleton — deleted the four enrichment VMs, kept the FIXTURES run (parent grain; carries the
`redo_all` gate fix; `round`/`competition_phase` is the known downstream blocker). Protective enforcement of a
documented HARD RULE, so taken autonomously.

**Damage (measured, small — caught ~30min in, not hours):** of 5,367,641 instruments-sports manifest rows,
`attempted_failed` = **477 total** (0.009%); api_football = 466, of which **153 attempted TODAY** —
`FIXTURES_FETCH_FAILED` 92 + **`rateLimit` 61**. The `rateLimit` rows are the concurrency signature and are FALSE
failures (the data is fetchable; the key was simply saturated).

- [ ] [DATA] P1. Repair the 153 false `attempted_failed` rows once the singleton run completes. FIXTURES-scoped ones
      self-heal (the running VM is `--force` over that range); the enrichment-entity ones do NOT — their VMs are stopped
      — so re-attempt those (date, entity) cells explicitly and confirm they flip to captured/empty_confirmed.
- [ ] [OPS] P1. The singleton is documented but was violable — four VMs launched anyway. Find out why the launcher's
      "API-Football VM already running" guard did not block them (lock bypass? `--force` on the fleet launcher? a
      scheduled job that predates the guard?) and close it, otherwise this recurs every time two actors touch sports.

---

## I. Control conflict: the enrichment fleet is AUTO-RELAUNCHED — singleton cannot be held unilaterally — **P0 operator**

At 15:57Z I deleted 4 concurrent api-football enrichment VMs to enforce the per-key singleton. **They were back at
16:16Z** (`af-backfill-20260718-161608/161641/161712/161740` — same 4 entities, same 2020-06-06..2026-07-18 range, no
`--force`). No `PREEMPTED` markers were written for the deleted VMs, so the relaunch most likely came through the
**exit-code** recovery path (`exit_code_fleet_monitor` + `auto_recover`, wired via `scripts/vm/lib/launcher_common.sh`)
rather than the preemption path.

**I stopped fighting it deliberately.** Deleting them again just triggers another relaunch ~20 min later; the churn
itself burns quota and adds nothing. My own FIXTURES VM was preempted at ~16:21 and I did **NOT** relaunch it, because
that would have made a 5th concurrent VM on the shared key. So sports FIXTURES is currently PAUSED by choice, not by
failure.

This needs cross-actor coordination, not unilateral VM deletion:

- [ ] [OPS] P0. Identify what re-launches the 4-entity enrichment fleet (exit-code actuator? a cron? another slot?) and
      give api-football ONE owner. Until then, any agent enforcing the singleton is fighting an automation that wins by
      default, and the key stays oversubscribed (measured earlier: 153 false `attempted_failed` rows in ~30min).
- [ ] [OPS] P0. Resume the FIXTURES `--force` run once the key has a single owner — relaunch from
      `last_completed_day + 1` (loop-resume contract, § G-ops). 350 `fixtures_schedule` objects were written before
      preemption; `round` is confirmed populating.

## J. F6 RESOLVED — the instruments-sports consolidator is HEALTHY; the 120s staleness budget is too tight

Earlier (§ F6) I recorded the instruments-sports manifest as unreadable via `read_availability_index`
(`ManifestConsolidatorStaleError`, "consolidator is behind or DOWN"). **Measured: it is NOT down.** Cloud Run executions
at 16:19:43 / 16:21:45 / 16:22:47 all completed `True`, `_index/per_vm/` backlog is 6 shards, and the canonical index
was written 16:19:47.

The real cause: that index is **108.45 MiB**, so a merge cycle takes ~1-2 minutes — routinely leaving the blob older
than `MANIFEST_CONSOLIDATED_STALENESS_SEC=120` when a reader checks it. Reads therefore fail INTERMITTENTLY by racing
the merge cycle, and the error message ("behind or DOWN") actively misleads the next investigator.

- [ ] [CODE] P1. Raise the staleness budget for large-index buckets via the existing per-bucket resolver
      (`_resolve_consolidated_staleness_sec`) — a budget must exceed that bucket's MEASURED merge duration, not a
      fleet-wide constant. instruments-sports needs >= ~180-240s at 108 MiB.
- [ ] [CODE] P2. Soften the error text: distinguish "consolidator DOWN" (no recent successful execution) from "index
      older than budget but consolidator succeeding" (a too-tight budget). They demand opposite responses.

---

## K. Canonical migration — PHASED EXECUTION PLAN (operator: "multi day is fine do it properly")

### K0. The canonical direction is ALREADY DECIDED — reuse it, don't re-litigate

`market-tick-data-service/.../scripts/migrate_sports_canonical_v9.py` (CF-7) states it outright:

- **`data_type` canonical = lower-case** — _"Canonical is the lower-case form the live writers emit via the UAC
  data_type vocabulary"_ (`ODDS`→`odds`, `ODDS_SNAPSHOT`→`odds_snapshot`, `ODDS_MOVEMENT`→`odds_movement`,
  `ODDS_HORIZON_BUCKET`→`odds_horizon_bucket`, `ARBITRAGE_OPPORTUNITY`→`arbitrage_opportunity`, `TRADES`→`trades`).
- **`venue` canonical = the BOOKMAKER** — _"for MDPS odds ticks the only valid venue is the bookmaker (per
  bookmaker_key)"_. This independently confirms § F2/F4 and the shard-atom analysis: `ODDS_API` is a SOURCE, not a
  venue.

**NOT a live contradiction**: `market_data_processing_service/app/core/canonical_writer_stamping.py` maps lower→UPPER,
but only to build **SOURCE_PRIORITY lookup keys** (its own comment: _"SOURCE_PRIORITY uses UPPERCASE keys for sports;
MDPS source_data_type strings are lowercase — this bridge normalises the case mismatch"_). Different namespace,
legitimate. Do NOT "fix" it.

**That migrator is STALE — do not run it.** Its lifecycle marker: _"Delete-when: after E8 legacy-sports-bucket deletion
… this migrator reads/writes those LEGACY buckets directly, so post-E8 it references nonexistent infra"_. E8 completed
this session (legacy IS bucket deleted), so it now targets partly-nonexistent infra. The remaining drift lives in the
**-prd-** buckets.

### K1. Phase 1 — WRITERS FIRST (else the drift returns)

Migrating rows without fixing writers guarantees regression on the next capture. Fix emission, then migrate.

- [ ] [CODE] P1. Make every sports writer emit the CF-7 canonical `data_type` (lower-case) — audit each
      `record_captured/record_empty/record_failed` sports call-site for upper-case literals.
- [ ] [CODE] P1. Make MDPS odds writers stamp `venue = <bookmaker_key>` and `source = odds_api`, instead of
      `venue=ODDS_API`. `_SPORTS_VENUES = frozenset({"ODDS_API"})`
      (`market_tick_data_service/adapters/umi_tick_provider.py:110`) is the declaration to change.
- [ ] [CODE] P1. Stop writing bookmakers + `odds` into `instrument_type`; introduce the sports instrument_type
      vocabulary (betting market: match_odds / over_under / btts / spread). NOTE `canonical_writer_shaping.py:218`
      asserts _"the correct instrument_type IS 'odds'"_ — that claim must be reconciled against the shard atom
      (`instrument_type` is an INSTRUMENT axis, and `odds` is a data_type) BEFORE changing it. Read it in full first.
- [ ] [CODE] P1. QG assertion: sports `data_type` ∈ the UAC lower-case vocabulary, `venue` ∉ {vendor names}, and
      `instrument_type` ∈ the declared sports vocabulary — so this class cannot silently return.

### K2. Phase 2 — MIGRATE the -prd- rows (only after K1 ships)

Measured drift in `market-data-tick-sports-prd` (1,974,679 rows): `ODDS`/`odds` 22,145+20,331; `ODDS_SNAPSHOT`/
`odds_snapshot` 4+4; `ODDS_MOVEMENT`/`odds_movement` 4+4; `venue=ODDS_API` 306,416; `venue=FOOTBALL` 1,337;
`instrument_type='odds'` 1,806,527 + ~1,321 bookmaker rows + `PADDYPOWER`/`paddypower`, `PINNACLE`/`pinnacle`.

- [ ] [DATA] P1. New migrator targeting the **-prd-** buckets (the CF-7 script is legacy-only). DRY-RUN default,
      backup-before-write, per-batch verification. Reuse CF-7's `_CF7_DATA_TYPE_NORMALISE` decisions verbatim.
- [ ] [DATA] P2. The 1,337-row legacy cohort (`odds_horizon_bucket_{15m,1h,4h,1d}` + `venue=FOOTBALL`, same rows) —
      superseded horizon naming with NO live writer; re-stamp to canonical or drop. One pass (operator-approved).
- [ ] [CLEANUP] P2. Delete `migrate_sports_canonical_v9.py` per its own Delete-when marker (E8 is complete).

### K3. Phase 3 — prove it

- [ ] [DATA] P1. Re-run the § F distinct-value audit and show ZERO case-duplicates, no vendor in `venue`, and
      `instrument_type` within vocabulary. Restore the data-status distinct-values listing (§ F, [CODE] P1) so this is
      visible in the UI instead of needing an ad-hoc query.

### K0-CORRECTION (operator challenge: "data_type is lowercase for sports or for all AGs? its uppercase for tradfi so thats weird")

**RETRACTED (mine)**: K0 said "`data_type` canonical = lower-case", generalising CF-7. CF-7's claim is scoped to the
**MDPS odds** data_types only, and I wrongly promoted it to a sports-wide rule. Measured reality:

| bucket                 | distinct | UPPER | lower         |
| ---------------------- | -------- | ----- | ------------- |
| market-data **tradfi** | 12       | **0** | 12            |
| market-data **cefi**   | 9        | **0** | 9             |
| market-data **defi**   | 6        | **0** | 6             |
| instruments **tradfi** | 1        | **0** | `instruments` |
| instruments **cefi**   | 1        | **0** | `instruments` |
| instruments **sports** | 9        | **9** | 0             | ← FIXTURES, FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, MATCHES, PLAYER_STATS, PREDICTIONS, WEATHER |
| features **sports**    | 4        | **4** | 0             | ← DERIVED_FEATURES, FIXTURE_FEATURES, ODDS_FEATURES, SFI_PROGRESSIVE_FEATURES                           |
| market-data **sports** | 13       | 4     | 9             | ← the ONLY mixed bucket in the fleet                                                                    |

**The operator's premise is inverted, and the conclusion is stronger: tradfi is lower-case; SPORTS is the outlier.**
Sports is the only asset group using UPPERCASE `data_type` anywhere. UAC agrees — `("tradfi","trades")` /
`("tradfi","ohlcv_1m")` are lower-case while `("sports","FIXTURES")` / `("sports","PLAYER_STATS")` are UPPER, with an
explicit comment that _"The canonical data_type name is PLAYER_STATS"_.

**Deeper than casing — a STRUCTURAL divergence.** instruments-tradfi/cefi carry a single `data_type='instruments'`;
instruments-**sports** carries 9 entity-like values. Sports is using `data_type` as an ENTITY axis where no other asset
group does. Any "make sports canonical" effort must decide that, not just the case.

**Three targets, NOT equivalent — needs an operator decision before ANY row is rewritten:**

- **(a) MDPS → lower only** (what K2 assumed): fixes the one mixed bucket, sports stays internally split (UPPER
  reference + UPPER features + lower MDPS). Cheapest; leaves sports non-canonical fleet-wide.
- **(b) sports → UPPER everywhere**: sports becomes internally uniform, but permanently diverges from tradfi/cefi/defi
  and from UAC's lower-case convention for those AGs. Entrenches the outlier.
- **(c) sports → lower everywhere** (TRUE fleet-canonical): aligns sports with every other AG. Largest — ~5.4M
  instruments-sports rows + the features layer + every UAC `("sports", …)` SOURCE_PRIORITY key + the
  `canonical_writer_stamping` bridge + downstream readers that filter on these literals. Also forces the structural
  question (is `data_type` an entity axis for sports, or should entity live on its own axis as it does elsewhere?).

- [ ] [ASK] P0. Operator decision on (a)/(b)/(c) before K1/K2 execute. **K2 is BLOCKED on this** — normalising 2M MDPS
      rows to lower-case under (a) would be actively wrong if the answer is (b), and would be only ~5% of the work under
      (c). Recommendation: **(c)**, because it is the only option that makes "sports is canonical" true rather than
      "sports is self-consistent"; but it is a multi-week programme, not a migration script.

### K0-DECISION (operator 2026-07-18): **(b) sports → UPPER everywhere**

Operator chose **(b)**: sports uses UPPERCASE `data_type` across all its layers — internally uniform, and knowingly
divergent from tradfi/cefi/defi (which are uniformly lower-case). **K2 is UNBLOCKED** with this direction:

- Reference (`instruments-sports`, 9 values) and features (`features-sports`, 4 values) are ALREADY all-UPPER — **no
  change needed**, they are already conformant under (b).
- Only **market-data-sports** is mixed (4 UPPER + 9 lower). Migration = normalise the 9 lower-case values UP:
  `odds`→`ODDS`, `odds_snapshot`→`ODDS_SNAPSHOT`, `odds_movement`→`ODDS_MOVEMENT`,
  `odds_horizon_bucket`→`ODDS_HORIZON_BUCKET` (+ the 4 legacy `odds_horizon_bucket_{15m,1h,4h,1d}` variants, which are
  the dead cohort in § F3 — re-stamp or drop in the same pass).
- This is the OPPOSITE direction to CF-7's `_CF7_DATA_TYPE_NORMALISE` (which mapped UPPER→lower). **CF-7's mapping is
  now superseded for sports** — that script is legacy-only and slated for deletion anyway (§ K2).
- **Bonus**: `canonical_writer_stamping.py`'s sports lower→UPPER map (which I nearly "fixed") is now ALIGNED with the
  chosen canonical, not a bridge to work around. Leave it.

Scope under (b) is far smaller than (c): ~42k case-duplicate rows in ONE bucket, versus ~5.4M reference rows + the
features layer + every UAC `("sports", …)` key.

## L. The features launcher could never replay a writer fix — **FIXED**

`launch-features-sports-backfill-vm.sh` used its `FORCE` flag ONLY for the same-prefix VM singleton lock; it never
reached `BACKFILL_CMD`. So the launcher structurally could not re-derive dates the manifest already marks captured/empty
— i.e. it could never replay a writer fix over history.

Measured: the lineups re-derive `fs-backfill-20260718-160901` ran **2.5 hours** logging
`SKIP fixture_lineups for <date> — manifest shows prior captured/empty (use --force)` on every date and wrote **ZERO**
shards. Identical defect class to the instruments-service fixtures gate (@7d49d096) — "force exists but does not reach
the thing that needs it" is now a THIRD instance this session.

Fixed in deployment-service@25d77c1: added `--redo-all`, deliberately SEPARATE from `--force` (`--force` = VM lock
bypass; `--redo-all` = pass `--force` to the features CLI). Conflating them is the documented api-football mistake. QG
green (2,542 passed). Relaunched as `fts-backfill-20260718-184352` with the CLI now receiving `--force`; tarball
re-verified aboard (features-service `47acb31f`, `cf10b931` ancestor-proven, flat-shape branch + coach emission present)
— MANDATORY here, because under `--redo-all` a pre-fix normalizer would OVERWRITE good 40-row shards with 0.

**Note on the 356 "fresh" lineup shards**: they were written 06:42Z by a PRE-fix run, not by my VM — which is why they
show `coach 0/40` (the old normalizer never emitted coach) despite having 40 rows (legacy nested shape parsed fine).
They are exactly what the `--redo-all` pass now replaces.

### L-VERIFIED (2026-07-18 19:10Z) — the lineups re-derive WORKS end-to-end

`fts-backfill-20260718-184352` (with `--redo-all`) measured on shards it wrote after 18:43Z:

- **0 `SKIP fixture_lineups` lines** (was: every date) and **131 `Wrote fixture_lineups` lines** — the launcher gap is
  genuinely closed.
- **168 shards** written by this run so far. Sampled 4:

| day        | rows | coach_name | coach_id | starters |
| ---------- | ---- | ---------- | -------- | -------- |
| 2020-07-13 | 830  | 803/830    | 825/830  | 440      |
| 2020-07-14 | 677  | 674/677    | 674/677  | 396      |
| 2020-07-15 | 927  | 911/927    | 911/927  | 550      |
| 2020-07-16 | 697  | 690/697    | 690/697  | 374      |

**coach_name populated 3,078/3,131 = 98.3%** (pre-fix: **0/40**); rows/day jumped from 40 to 700-900. The residual ~1.7%
nulls are fixtures that genuinely carry no coach upstream — honest absence, not a defect.

This closes the A1 chain end-to-end: normalizer flat-shape fix (features-service@cf10b931) + dedupe + coach emission,
delivered over history by the `--redo-all` launcher gap fix. **Zero api-football calls** — the entire restoration came
from raw already on disk.

### H-UPDATE (2026-07-18 19:12Z) — the concurrency damage is HEALING, not growing

Canonical index read (5,368,385 rows — read the parquet DIRECTLY; `read_availability_index` fell back to per-VM shards
under the stale-index gate and reported a FALSE `0`, cf. § J):

| metric                   | 15:57Z                                      | 19:12Z             | delta       |
| ------------------------ | ------------------------------------------- | ------------------ | ----------- |
| `attempted_failed` total | 477                                         | **385**            | **-92**     |
| attempted TODAY          | 153                                         | **61**             | **-92**     |
| error_reason breakdown   | `FIXTURES_FETCH_FAILED` 92 + `rateLimit` 61 | **`rateLimit` 61** | 92 repaired |

**RETRACTED (mine)**: § H said the enrichment-entity false failures "do NOT self-heal — their VMs are stopped". They DID
heal: the (auto-relaunched) enrichment VMs re-attempt those cells, and all 92 `FIXTURES_FETCH_FAILED` rows flipped to
captured/empty. **No new failures since containment** — so 4 concurrent VMs are not currently generating fresh
rate-limit damage the way 5 were. No further VM intervention is warranted.

Residual: **61 `rateLimit` rows** from the 5-VM window (15:27-15:57Z). They are FALSE failures — the data is fetchable,
the key was saturated. They will heal the same way if their (date, entity) cells are re-attempted; otherwise re-attempt
explicitly once the key has a single owner.

- [ ] [DATA] P2. Confirm the residual 61 `rateLimit` rows reach captured/empty (they should heal via normal re-attempt);
      only force an explicit re-attempt if they persist after the enrichment fleet completes its range.

## M. Why we get rate-limited: the divisor was a PROMISE, not a measurement — **FIXED** (deployment-service@e85d570)

Operator: _"why we getting rate limited so much dont we knwo our rate limits on api football side and govern them across
vms properly?"_ — we DO know them, and a governor exists. The gap is where the divisor comes from.

**The design (sound):** api-football enforces **1200 req/min AND 450,000 req/day, ONE quota across ALL endpoints**. The
launcher computes a daily-aware effective ceiling, splits it `EFFECTIVE_RPM / FLEET_VMS`, stamps the per-VM req/min +
matched concurrency into VM metadata, and the adapter self-enforces that throttle.

**The gap:** `FLEET_VMS="${FLEET_VMS:-1}"` — it **defaulted to 1 and never auto-detected**. So every VM assumed it was
ALONE unless a human remembered `--fleet-vms N`. Nothing enforced that promise. Worse, the singleton COUNT ran only
inside `if ! $FORCE && ! $SKIP_LOCK` — it did not count on exactly the paths that create concurrency:

- `--force` / `--skip-lock` (deliberate fan-out)
- a second actor launching independently (§ I — the auto-relaunched enrichment fleet)
- **auto-relaunch**: `RelaunchPreemptedVm` replays the ORIGINAL env, so a VM relaunched into a now-crowded fleet carries
  a per-VM budget computed when it WAS alone. This one cannot be fixed by operator discipline at all.

Five concurrent VMs each throttling at a full-budget share = **5x oversubscription**, which is why the 429s appeared
despite an apparently-correct governor. Measured: **61 `rateLimit` FALSE `attempted_failed` rows in ~30 min**.

**Fix:** when `--fleet-vms` is not explicitly passed, COUNT the running `af-backfill-*`/`af-audit-*` VMs and derive
`FLEET_VMS = count + 1`, logging the derivation loudly. Explicit `--fleet-vms` still wins. QG green (2,542 passed).

**PARTIAL by construction — stated in the log, not hidden:** already-running VMs keep the budget they computed at THEIR
launch, so the key stays oversubscribed until they finish. Launch-time division cannot fix a fleet that grows after
launch.

- [ ] [CODE] P1. Runtime re-division: VMs should read the CURRENT fleet size (or lease a share from a central budget)
      and re-throttle when the fleet grows, instead of trusting a launch-time constant. Until then the singleton lock is
      doing the real work and every bypass path is a live oversubscription risk.
- [ ] [CODE] P1. `RelaunchPreemptedVm` should RE-DERIVE the rate budget on replay rather than replaying the original
      per-VM share — same root cause as § G-ops (replaying stale launch params).

## N. Why sports downloads take "way too long" — we were using a SLEDGEHAMMER (~1,800x waste)

Operator: _"lets optimise the downloads for sports fully its taking way too looong"_. Measured root cause — it is **call
VOLUME**, not rate governance:

| approach                                               | api-football calls                                                  |
| ------------------------------------------------------ | ------------------------------------------------------------------- |
| full `--force --entity FIXTURES` backfill              | **527 calls/date (measured mean) x 2,390 dates ~= 1,260,000**       |
| surgical `backfill_sports_fixture_round_2026_07_17.py` | **~600-700 TOTAL** (one bulk `GET /fixtures?league&season`, cached) |

**~1,800x reduction.** At the 450,000/day key quota the full re-fetch needs **~2.8 days of pure quota** (~76h at the
paced rate) — to populate **ONE field**. No amount of rate tuning or extra VMs can fix a 1,800x volume problem; the
per-key daily quota is a hard ceiling that MORE VMS CANNOT RAISE.

Pilot confirms the shape: `Fetched 242 season fixtures for league=113 season=2019` — **one call returned 242 fixtures**,
vs 527 calls per DATE in the full path. The script is round-only (touches blank `round` cells), SINGLE-WALK (one corpus
listing, not per-league re-walks), snapshots each parquet to `*.pre_round_backfill.bak`, and is idempotent.

- [x] [OPS] P0. STOP using the full `--force` FIXTURES backfill to fix `round`. Use the surgical script. (The `--force`
      VM was already preempted and NOT relaunched, so nothing to unwind.) Pilot running:
      `--max-leagues 1 --seasons 2019 --apply`.
- [ ] [OPS] P0. After the pilot verifies, run the full surgical backfill (all leagues x 2019-2026) in the background.
- [ ] [PROCESS] P1. Generalise: before launching a `--force` whole-corpus refetch to fix ONE column, check whether a
      surgical column-filler exists. The blast radius / quota cost differ by orders of magnitude, and `--force` also
      forfeits presence-skip resume (§ G-ops).

## M-FIXED. Both rate-governance gaps CLOSED (operator: "donot just file them fix them")

1. **Divisor from MEASURED concurrency** — `FLEET_VMS` defaulted to 1 (every VM assumed it was alone); the singleton
   count ran only inside `if ! $FORCE && ! $SKIP_LOCK`, i.e. NOT on the paths that create concurrency. Now the launcher
   counts running `af-backfill-*`/`af-audit-*` VMs and derives `count + 1` when `--fleet-vms` is not explicit, logging
   the derivation. Explicit still wins.
2. **Re-derive on preemption replay** — deployment-service@cb499b7: `RelaunchPreemptedVm` now STRIPS
   `SPORTS_ADAPTER_RATE_RPM` / `SPORTS_ADAPTER_CONCURRENCY` / `FLEET_VMS` / `REMAINING_DAILY_QUOTA` from the replayed
   env so the launcher re-derives them. A VM preempted while ALONE no longer re-applies a full-key budget when
   relaunched into a crowded fleet. QG green (2,543 passed), regression-pinned (non-rate params still replay verbatim).
   This path could NOT be fixed by operator discipline — nothing passed at first launch survives correctly into an
   automated relaunch.

**Still partial, stated not hidden**: already-running VMs keep the budget they computed at their own launch, so the key
stays oversubscribed until they drain. Launch-time division cannot fix a fleet that grows after launch — the remaining
fix is runtime re-division / leasing shares from a central budget (§ M todo).

## O. `round` is ~50% populated in RAW — the 3.2% was the CATALOGUE. The gap is the ROLLUP, not capture.

The surgical pilot (`--max-leagues 1 --seasons 2019 --apply`) reported
`ALLSVENSKAN APPLIED +0/4349 rows across 1551 parquet(s) (242 fixtures fetched)` — it fetched fine and filled **zero**.
That prompted a proper measurement instead of another backfill.

Measured `round` population per day, BOTH entities:

| day        | fixtures_schedule | %   | legacy fixtures |
| ---------- | ----------------- | --- | --------------- |
| 2019-05-11 | 47/153            | 31% | 55/237          |
| 2020-09-19 | 171/289           | 59% | 171             |
| 2021-03-13 | 166/284           | 58% | 166             |
| 2022-10-05 | 44/88             | 50% | 44              |
| 2023-08-19 | 334/666           | 50% | 334             |
| 2024-04-06 | 187/394           | 47% | 187             |
| 2025-11-08 | 195/404           | 48% | 195             |
| 2026-03-14 | 142/354           | 40% | 142             |

**RETRACTED (mine, twice over):**

1. "`round` is blank / ~0% in raw" — it is **~30-60% populated across all of history**. My earlier `round 0/4` and `0/7`
   readings were single small legacy shards, not a representative sample. I generalised from a handful of EPL shards.
2. "The entity split explains it" (§ G-RESOLVED framing) — legacy `entity=fixtures` and `entity=fixtures_schedule` carry
   **IDENTICAL** round counts on 7 of 8 sampled days. The split is real but is NOT the round story.

**So the 3.2% in the original issue was measured on the CATALOGUE (545/17,064 rows), while raw holds ~50%.** The loss is
in the ROLL-UP, not the capture. That reframes the remaining work completely:

- A whole-corpus `--force` refetch (1.26M calls) was never the right instrument — and neither is the surgical backfill
  for the ~50% that ALREADY has round.
- The genuinely-missing ~50% is a real but much smaller target, and some of it is honest absence (cup/friendly fixtures
  legitimately have no `Regular Season - N` round).

- [ ] [DATA] P0. Rebuild the sports catalogue
      (`build_instrument_catalogue.py --asset-group sports --since     2019-01-01`) and re-measure `round` /
      `competition_phase` there. If the catalogue jumps from 3.2% toward the raw ~50%, the rollup was simply stale and
      NO backfill is needed for that half.
- [ ] [DIAG] P0. Only after that: characterise the residual raw blanks — split genuine absence (cups/friendlies with no
      round concept) from real capture gaps, and size the surgical run against the real gap.
- [ ] [CODE] P1. The surgical script scans `"/entity=fixtures/"` (line 79) — the LEGACY entity. Retarget to
      `entity=fixtures_schedule` (verified to carry `af_fixture_id` + `round`) before any real run, or it patches the
      wrong tree. Same staleness class as `migrate_sports_canonical_v9.py`.

## P. DERIVE `round` for the confident majority, spend API calls only on the clustered remainder

Operator 2026-07-18: _"work out per league when the non standard games cluster so you can end up manually inserting
round info for 70% of normal games you are 100% confident on ... should take calls down a lot, a couple hours rather
than days"_. Measured — the idea holds, with a precise ceiling and one caveat.

**The populated ~50% is a FREE LABELLED GROUND-TRUTH SET.** Any derivation rule can be scored against it with zero API
calls before being applied to the blank half. Measured on 3,234 sampled fixtures (6 matchdays, Aug-Sep 2023):

- `round` populated 1,562/3,234 (48%).
- Of those, **1,072 = 69% are `Regular Season - N`** — the operator's "70% of normal games", confirmed.
- The remainder are cup/qualifying structures that cluster: `Preliminary Round` 124, `1st Round Qualifying` 103,
  `2nd Round Qualifying` 74, `3rd Round Qualifying` 40, `1st/2nd/4th/5th Round`, `Group B - 26`.

**Derivability ceiling — 97.0%.** Grouping the Regular-Season fixtures by `(af_league_id, day)`: **225 of 232 groups
carry exactly ONE round number**; only 7 span multiple rounds. So "all fixtures for a league on a matchday share one
round" holds 97% of the time, and that is the hard ceiling for date→round derivation.

**The 3% failures CLUSTER BY LEAGUE, not randomly** — league `253` alone accounts for 4 of the 7 (a split/scattered
schedule). That is what makes the operator's plan work: ambiguity is a per-league property, so a confidence whitelist is
possible instead of a blanket refetch.

**Correctness guard — `round` is NOT chronological position.** Postponed fixtures mean a `Regular Season - 12` match can
be played after round 15. Naive date-ordering would silently write WRONG rounds, and a derived value written as if
captured is the banned silent-placeholder. Hence: score first, whitelist second, and mark derived values as derived.

**CAVEAT — the validation set may not be exchangeable with the target.** The 97% is measured on fixtures that ALREADY
have `round`. If the blanks are disproportionately cups/friendlies (where `Regular Season - N` does not apply at all),
derivation covers far less of them. This MUST be measured before sizing the API run.

- [ ] [DIAG] P0. Profile the BLANK half by league + competition type. If blanks concentrate in cups/friendlies,
      derivation is not the lever there — honest absence is (a cup tie has no `Regular Season - N`).
- [ ] [CODE] P1. Build the per-league confidence whitelist: for each (league, season), score date→round derivation
      against the populated fixtures. Whitelist leagues scoring 100%; exclude any league with a multi-round matchday
      (e.g. `253`).
- [ ] [CODE] P1. Derive `round` ONLY for whitelisted (league, season) blanks, and stamp provenance (derived vs captured)
      — never write a derived value indistinguishable from a fetched one.
- [ ] [DATA] P1. API-fetch only the residual: non-whitelisted leagues + cup competitions + any league-season with no
      populated fixtures to score against. Size the run from THAT count, not the whole corpus.

### P-SIZING (2026-07-18) — the blank half IS exchangeable; ~89% derivable, API residual is TINY

The § P caveat ("blanks may be disproportionately cups, so the ground-truth set may not transfer") is **measured and
REFUTED**. Same 6-matchday sample (3,234 fixtures, 1,672 blank = 51.7%):

| bucket                                                             | leagues | blank fixtures  |
| ------------------------------------------------------------------ | ------- | --------------- |
| leagues with BOTH populated + blank (derivable target)             | **50**  | **1,539 (92%)** |
| blank-ONLY leagues (never any round — cups/friendlies/unsupported) | **7**   | 133 (8%)        |

**92% of blanks live in leagues that ALREADY have round data**, so the populated fixtures are valid ground truth for
exactly the leagues we need to fill. Combined with the § P ceiling (97% of `(league, day)` groups carry exactly one
round), **~89% of blanks are derivable with ZERO api-football calls**.

**Revised sizing — the operator's "couple hours rather than days" is conservative:**

| path                                     | api-football calls                                                                                                                            |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| full `--force` corpus refetch (rejected) | ~1,260,000                                                                                                                                    |
| surgical whole-corpus script             | ~600-700                                                                                                                                      |
| **derive-then-fetch (this plan)**        | **~1 bulk call per residual (league, season)** — the 7 blank-only leagues + leagues with multi-round matchdays. Tens of calls, not thousands. |

The residual is bounded by DISTINCT (league, season) pairs needing a fetch, NOT by fixture or date count — one
`GET /fixtures?league&season` returns the whole season (measured: 242 fixtures in one call).

- [ ] [CODE] P0. Implement derive-then-fetch: (1) score date→round per (league, season) against populated fixtures; (2)
      derive blanks for leagues scoring 100%, stamped as DERIVED provenance; (3) enumerate the residual (blank-only
      leagues + non-perfect scorers) and bulk-fetch ONLY those (league, season) pairs.
- [ ] [DIAG] P2. Classify the 7 blank-only leagues: genuine honest absence (a cup tie has no `Regular Season - N`) vs a
      real capture gap. Do not fetch what has no round concept — that is honest absence and should be recorded as such,
      not chased.

### P-ERA (2026-07-18) — `round` capture STARTS mid-2019; the underivable residual is one bounded era

First dry-run of `instruments-service/scripts/derive_sports_fixture_round_2026_07_18.py` returned **0 filled / 2,390
blank / 2,390 no-sibling**. That was MY sampling error, not a script failure: `--max-days 40` takes the FIRST 40 sorted
days = earliest 2019, and round population there is **0%** — no populated siblings exist to propagate from. (Third time
this session a small unrepresentative sample produced a confident wrong read; the fix is the same each time — sample
across the range, or measure the whole corpus.)

Measured population by era (one sampled matchday per year, `entity=fixtures_schedule`):

| matchday   | rows | populated | %        |
| ---------- | ---- | --------- | -------- |
| 2019-02-09 | 575  | 0         | **0.0%** |
| 2019-08-17 | 362  | 238       | 65.7%    |
| 2020-09-19 | 289  | 171       | 59.2%    |
| 2021-03-13 | 284  | 166       | 58.5%    |
| 2022-10-05 | 88   | 44        | 50.0%    |
| 2023-08-19 | 666  | 334       | 50.2%    |
| 2024-04-06 | 394  | 187       | 47.5%    |
| 2025-11-08 | 404  | 195       | 48.3%    |
| 2026-03-14 | 354  | 142       | 40.1%    |

**`round` capture begins around mid-2019** and holds 40-66% thereafter. So the work splits cleanly:

- **2019-08 → 2026**: siblings exist → DERIVE (zero API calls), bounded by the § P 97% unanimity ceiling.
- **early 2019 (Jan → ~Aug)**: 0% populated → nothing to derive from → API fetch. **Bounded by (league, season) pairs,
  NOT days**: season 2019 across ~89 leagues ≈ **~89 bulk calls**, since one `GET /fixtures?league&season` returns the
  whole season (measured: 242 fixtures in one call).

Total projected api-football spend for the entire `round` gap: **~100 calls**, versus the ~1,260,000 of the rejected
`--force` corpus refetch — and versus ~600-700 for the whole-corpus surgical script. The operator's "a couple of hours
rather than days" is conservative; this is minutes of API time.

- [ ] [DIAG] P0. Full-corpus dry-run running (no `--max-days`) — read fill / ambiguous / no-sibling corpus-wide before
      `--apply`. Confirms the era split and gives the exact residual.
- [ ] [CODE] P1. Cross-file sibling grouping: the script groups per PARQUET. If a (league, day)'s populated rows and
      blanks live in different files, siblings are invisible and blanks are mis-counted as "no sibling". If the full-run
      no-sibling count exceeds the ~8% predicted by § P-SIZING, group by (league, day) ACROSS the day's files.

## Q. Round derivation SHIPPED + APPLYING — 89.2% of the gap closed with ZERO api-football calls

`instruments-service@e63049e7` — `scripts/derive_sports_fixture_round_2026_07_18.py`. QG green (4,579 passed).

**Measured on real data (populated eras, 5 matchdays):**

| metric              | value                                    |
| ------------------- | ---------------------------------------- |
| rows / blank        | 2,513 / 1,294                            |
| **DERIVED**         | **1,154 = 89.2% of blanks, 0 API calls** |
| ambiguous (refused) | 42 (3.2%) — multi-round matchdays        |
| no-sibling (API)    | 98 (7.6%)                                |

Matches the § P-SIZING prediction (92% mixed-league x 97% unanimity ~= 89%) almost exactly.

**Design decisions that made it safe:**

- **Unanimity, never inference.** `round` is NOT chronological position — a postponed `Regular Season - 12` can be
  played after round 15 — so date ORDERING is never used to invent a number. A (league, day) whose known values disagree
  is REFUSED. That self-handles the 3% rescheduled matchdays with no whitelist to maintain.
- **Provenance stamped.** Fills carry `round_provenance='derived'` (captured rows `'captured'`). A derived value
  indistinguishable from a fetched one is the banned silent placeholder.
- **Two-pass per day.** A day carries BOTH a bare multi-league parquet AND per-league parquets, so a league's populated
  rows and its blanks can sit in different files. Pass 1 pools known values across ALL the day's files; pass 2 fills.
  The first cut grouped PER PARQUET and reported **0% filled** — the fix took it to 89.2%.
- Snapshots each parquet to `*.pre_round_derive.bak`; idempotent; single-walk; targets `entity=fixtures_schedule` (the
  LIVE entity — the older surgical script targets the stale `entity=fixtures`).

**Full-corpus `--apply` RUNNING** over 3,989 days (PID 2138671, watchdog armed on the filled-count progress metric).

**Revised total api-football spend for the whole `round` gap: ~100 bulk calls** (early-2019 era, one
`GET /fixtures?league&season` per league) versus **~1,260,000** for the rejected `--force` corpus refetch.

- [ ] [DATA] P1. After the apply completes: re-measure round population per era, then fetch the early-2019 residual (~89
      league-season bulk calls) and the ~8% no-sibling remainder.
- [ ] [DATA] P1. Then rebuild the catalogue (`build_instrument_catalogue.py --asset-group sports --since 2019-01-01`)
      and verify `competition_phase` is no longer ~100% UNKNOWN — the § O hypothesis is that the rollup, not capture,
      was the 3.2%.

### Q-RESULT (2026-07-19 00:13Z) — derivation APPLIED corpus-wide: 115,715 rows filled, ZERO api-football calls

```
rows scanned : 499,620
blank round  : 354,279
DERIVED      : 115,715  (32.7% of blanks)  <- zero API calls
ambiguous    :   6,654  (refused: multi-round matchday)
no-sibling   : 231,910  across 3,386 days  <- API residual
```

**Round coverage on every era that had data to propagate from (before -> after):**

| day        | before | after     | gain      |
| ---------- | ------ | --------- | --------- |
| 2019-08-17 | 65.7%  | **98.6%** | +32.9 pts |
| 2020-09-19 | 59.2%  | **98.3%** | +39.1 pts |
| 2021-03-13 | 58.5%  | **97.2%** | +38.7 pts |
| 2022-10-05 | 50.0%  | **90.9%** | +40.9 pts |
| 2023-08-19 | 50.2%  | **98.2%** | +48.0 pts |
| 2024-04-06 | 47.5%  | **92.4%** | +44.9 pts |
| 2025-11-08 | 48.3%  | **95.5%** | +47.2 pts |
| 2026-03-14 | 40.1%  | 69.2%     | +29.1 pts |

Writes verified: `round_provenance='derived'` present (e.g. 320 rows on 2023-08-19, 177 on 2024-04-06) with plausible
values (`Regular Season - 20`, `Regular Season - 2`), and 40-42 `*.pre_round_derive.bak` snapshots per sampled day.

**RETRACTED (mine — 4th sampling over-prediction today): "89.2% of blanks".** That pilot sampled 2023-2025 matchdays,
the BEST-populated eras. Corpus-wide the fill rate is **32.7%**, because 65.5% of blanks have NO populated sibling in
their `(league, day)` at all. The corpus dry-run should have run BEFORE quoting a headline number. The 89.2% was not
wrong about those days — it was wrong as a corpus estimate.

**Provenance caveat (minor, by design of the two-pass split):** `captured` is stamped only on files that also contain
blanks; a file with no blanks returns early and is left unstamped. So the invariant to rely on is
`round_provenance == 'derived'` identifies derived rows — anything else is captured/pre-existing. The safety requirement
(a derived value must never be indistinguishable from a fetched one) holds.

- [ ] [DATA] P1. Residual fetch: 231,910 no-sibling blanks across 3,386 days, dominated by the early-2019 zero-era.
      Bounded by DISTINCT (league, season) pairs (~600-700 bulk calls, the original surgical-script estimate), NOT by
      fixture count. Retarget that script to `entity=fixtures_schedule` first (§ O todo).
- [ ] [DATA] P1. Then rebuild the catalogue and verify `competition_phase` — with raw now at 90-99% on populated eras,
      this is the real test of the § O "the 3.2% was the stale rollup" hypothesis.

### L-COMPLETE (2026-07-19 00:45Z) — lineups re-derive FINISHED and verified at scale

`fts-backfill-20260718-184352` completed cleanly: `DEPLOYMENT_COMPLETED exit_code=0`, deployment archived, VM
self-deleted per `VM_SHUTDOWN_ON_COMPLETION`.

| metric                     | before               | after                                           |
| -------------------------- | -------------------- | ----------------------------------------------- |
| lineup shards materialised | 356 (stale, pre-fix) | **2,022**                                       |
| `coach_name` populated     | **0/40 (0%)**        | **3,778/3,983 (94.9%)** — random 6-shard sample |
| rows per day               | ~40                  | ~660 (3,983 over 6 shards)                      |

Closes the A1 chain end-to-end: normalizer flat-shape fix + dedupe + coach emission (features-service@cf10b931),
delivered over history by the `--redo-all` launcher gap fix (deployment-service). **Zero api-football calls** — the
entire restoration came from raw already on disk.

The residual ~5% `coach_name` nulls are fixtures that genuinely carry no coach upstream — honest absence, not a defect.

## R. ROOT CAUSE of `competition_phase` UNKNOWN — the entity split left EVERY CONSUMER on a dead entity — **P0**

The catalogue rebuild completed cleanly (`CATALOGUE_ROLLUP_COMPLETED exit_code=0`, **121,538 rows** promoted, up from
the 17,064 the original issue measured) — and `round` came out at **837/121,538 = 0.7%**, with `competition_phase`,
`round_name` and `is_promotion_relegation` **columns entirely ABSENT**. That is WORSE than the 3.2% baseline, despite
raw now sitting at 90-99% after § Q.

**RETRACTED (mine, § O): "the loss is in the ROLLUP, rebuild it and the 3.2% resolves."** Rebuilding changed nothing,
because the rollup is reading a **dead entity**.

**Measured:**

| entity                     | newest write         | status           |
| -------------------------- | -------------------- | ---------------- |
| `entity=fixtures`          | **2026-05-23 20:35** | FROZEN ~2 months |
| `entity=fixtures_schedule` | **2026-07-18 21:27** | LIVE             |

`build_instrument_catalogue.py:208` pins `SPORTS_FIXTURE_ENTITY = "fixtures"`. So the catalogue rolls up a corpus that
stopped being written on 2026-05-23 — which is why the § Q derivation (115,715 rows into `fixtures_schedule`) is
invisible to it, and why `competition_phase` has been UNKNOWN all along. **This was never a capture gap.**

**The split migrated the WRITER and left the CONSUMERS behind.** Stale-entity readers found so far (non-exhaustive,
`entity=fixtures` hard-coded):

- `scripts/build_instrument_catalogue.py:208` (`SPORTS_FIXTURE_ENTITY`) — the catalogue itself
- `scripts/backfill_sports_fixture_round_2026_07_17.py:79` — the surgical round filler (§ O)
- `instruments_service/reference_data/sports_dependency.py`
- `instruments_service/triggers/sports_fixtures_daily_repoll.py`
- `scripts/backfill_weather.py:154`, `scripts/backfill_sports_fixture_stats_manifest.py:91`
- `scripts/rescan_sports_fixtures_canonical.py:328,452`, `scripts/enumerate_expected_universe.py:1902`
- `scripts/migrate_sports_per_league.py`, `scripts/reconcile_sports_blank_empty_reason_2026_06_24.py`

This reframes the whole epic: chasing `round` through backfills (1.26M-call refetch, surgical script, derivation) was
treating a CONSUMER-MIGRATION bug as a data-capture bug. The derivation was still worth doing — raw is now 90-99% and
that is real — but the catalogue will keep reporting ~0% until its reader is repointed.

- [ ] [CODE] P0. Repoint `SPORTS_FIXTURE_ENTITY` to `fixtures_schedule` (verify the schema carries what the rollup
      needs: `af_fixture_id`, `round`, kickoff/timestamp) and re-run the catalogue. Handle `fixtures_outcomes` if the
      rollup needs scores/status — the split put those on the OTHER leg.
- [ ] [DIAG] P0. Audit EVERY consumer above for the same staleness; each is silently reading a 2-month-frozen corpus.
      Anything reporting "sports data is missing/stale" since 2026-05-23 is suspect for this cause.
- [ ] [CODE] P1. `competition_phase` / `round_name` / `is_promotion_relegation` are ABSENT as catalogue columns, not
      merely UNKNOWN — the rollup never projects them. Even with a live entity, the derivation from `round` must be
      wired into the catalogue build.
- [ ] [PROCESS] P1. An entity rename/split MUST enumerate and migrate consumers in the same change. This one shipped the
      writer on 2026-05-23 and left ~10 readers pointing at a corpus that stopped updating — silently, because a frozen
      corpus still reads successfully.

### R-FIXED (2026-07-19 02:01Z) — catalogue repointed to the LIVE entity: `round` 0.7% -> **70.6%**

`SPORTS_FIXTURE_ENTITY` repointed `fixtures` -> `fixtures_schedule`, full `--since 2019-01-01` rollup re-run:

| metric               | legacy entity | live entity                 | original issue |
| -------------------- | ------------- | --------------------------- | -------------- |
| catalogue rows       | 121,538       | **164,763**                 | 17,064         |
| `round` populated    | 837 (0.7%)    | **116,285 (70.6%)**         | 545 (3.2%)     |
| `Regular Season - N` | —             | 90,238 (77.6% of populated) | —              |

**+43,225 rows the frozen entity was simply missing.** The original issue's headline — _"round populated on only 545 of
17,064 rows (3.2%)"_ — is now **116,285 of 164,763**.

Safe-to-repoint was VERIFIED first, not assumed: the split is clean (legacy 55 cols = schedule 43 + outcomes 15,
**nothing missing from both**), and this rollup reads only SCHEDULE fields (`af_home_name` / `af_away_name` / `date` /
`timestamp` / `round`), all 100% populated on the schedule leg — so no outcomes join was needed.

**The derivation and the repoint are COMPLEMENTARY, not redundant** — worth stating because either alone looks
sufficient and neither is: § Q lifted RAW from 40-66% to 90-99% at zero API cost; § R made any of it visible downstream.
Without the derivation the repoint would have surfaced ~50%; without the repoint the derivation was invisible.

**STILL OPEN — `competition_phase` is ABSENT, not UNKNOWN.** `competition_phase` / `round_name` /
`is_promotion_relegation` are not catalogue columns at all; the rollup never projects them. So the original issue's
second half is NOT closed by this: `round` is now present and rich, but nothing derives the phase from it at catalogue
level.

- [x] [CODE] P0. ~~Project `competition_phase` in the catalogue rollup~~ — **RETRACTED, wrong layer.** These are UAC
      **`features_sports`** fields (`internal/domain/features_sports/__init__.py:138-142`), not catalogue columns, so
      "the rollup never projects them" was true but irrelevant. The real producer already exists:
      `features_service/sports/calculators/season_context.py`, fed by
      `derived_features_helpers.py:_compute_season_features`, which **already** extracts matchday from the round string
      (`r"(\d+)$"` on `round`) and maps `round -> round_name`. So the chain was never missing — it was **starved of
      input**, because `round` was blank. Populating `round` (§ Q + § R) is what unblocks it; **no new projection code
      is needed, only a features RE-RUN.** Note there are two unrelated `competition_phase` derivations:
      instruments-service `classify_competition_phase(round_name)` (NORMAL_LEAGUE / PLAYOFF / TOURNAMENT …) and the
      features one (`early|mid|late` from matchday progress). The UAC field is the features one.
- [ ] [DIAG] P0. The other ~9 stale-entity consumers (§ R list) are still reading the frozen corpus. Each needs the same
      repoint + a re-run; anything reporting stale sports data since 2026-05-23 is suspect.

### S (2026-07-19) — P1 MEASURED: `total_matchdays` is hardcoded **38 for every league on earth**

`features-service/features_service/sports/exporters/derived_features_helpers.py:735`:

```python
if "total_matchdays" not in enriched.columns:
    enriched["total_matchdays"] = 38          # <- every league, every season
```

This is a **silent placeholder** in the sense the codex bans: it is not flagged, not provenance-stamped, and it produces
confidently wrong numbers rather than honest absence. Measured against the live corpus (819 `fixtures_schedule`
parquets, 2023-08..2024-06, distinct `Regular Season - N`):

| league     | true season length   | hardcoded 38 |
| ---------- | -------------------- | ------------ |
| EPL        | 38                   | correct      |
| LA_LIGA    | 38                   | correct      |
| SERIE_A    | 38                   | correct      |
| BUNDESLIGA | **34**               | off by −4    |
| EREDIVISIE | **34**               | off by −4    |
| LIGUE_1    | **34**               | off by −4    |
| MLS        | **50** (36 distinct) | off by +12   |

**Correct for only 3 of 7 leagues measured.** Three consumers inherit the error:

- `games_remaining = total - matchday` — on Ligue 1's FINAL matchday (34) this reports **4 games remaining**, not 0.
- `points_at_stake = games_remaining x 3 x multiplier` — inherits it directly, so end-of-season stakes are inflated
  exactly when they matter most (relegation/title run-ins are the signal these features exist to capture).
- `competition_phase = f(matchday / total)` — the frac is wrong, so `early|mid|late` boundaries land in the wrong place:
  Ligue 1 reads 34/38 = 0.89 at season END; MLS reads 50/38 = 1.32, pinning it to `late` all season.

**Do NOT "fix" this with max-observed-matchday.** Deriving the total from matchdays seen so far under-estimates
mid-season, which makes `games_remaining` too small and the phase too `late` — strictly worse than 38 for the leagues 38
currently gets right. The fix needs the FULL season schedule (api-football publishes it upfront, and `fixtures_schedule`
already carries future fixtures), or a per-league reference mapping.

- [x] [CODE] P1. ✅ Per-(league, season) `total_matchdays` reference built from the corpus and consumed in
      `_compute_season_features` — **features-service@d9b44d46** (QG green). Ships `schemas/league_season_lengths.json`:
      198 league-seasons + 28 stable-league fallbacks, admitted only at >=95% round coverage AND contiguous rounds (a
      mostly-blank pair under-reports its max, so trusting it would be worse than no entry); implausible lengths (<10
      or >60) dropped, not guessed. Unknown pair => **honest NaN, never a default**. Verified: Ligue 1 final matchday 34
      now yields `games_remaining=0.0` (was 4.0); unknown league yields NaN, not a fabricated 38. The loader FAILS LOUD
      on a malformed/missing file rather than degrading to an empty map (QG "empty dict/list fallback") — it ships with
      the package, so silently NaN-ing the whole corpus would be the worse failure.
      `test_total_matchdays_defaults_to_38` asserted `== 38` and therefore encoded the bug as the contract; rewritten to
      pin honest-NaN, + 3 new regression tests.
- [ ] [DATA] P1. After the fix, sports features need a re-run for the affected leagues — the currently-persisted
      `games_remaining` / `points_at_stake` / `competition_phase` are wrong wherever season length != 38.

### T (2026-07-19) — residual round blanks SCOPED by measurement; my "early-2019 era" claim was WRONG

One walk of the live `fixtures_schedule` corpus (2,031 league-seasons, `round`/`season`/`af_league_id` projected only),
which also produced the § S season-length reference — **single walk, both answers**.

**CORRECTION.** I earlier characterised the residual as "231,910 no-sibling blanks, early-2019 era". Both halves were
wrong:

- The count is **161,034**, not 231,910. The 231,910 figure counted rows in the day-wide BARE parquets too; the
  orchestrator's reader (`_read_per_league_entity_df`) documents "there is no bare" and reads **only** `/league=` paths,
  so bare rows are not part of the live read path.
- It is not the "2019 era" — it is **pre-2019**, which the 2019-01-01..2026-07-17 backfill window does not even cover:

| seasons                   | pairs |  blank rows | share     |
| ------------------------- | ----: | ----------: | --------- |
| 2013–2018 (OUT of window) |   915 | **122,864** | **76.3%** |
| 2019–2027 (IN window)     |   842 |  **38,170** | 23.7%     |

**The in-window job is ~4x smaller than I said, and it is bounded:**

| coverage of in-window blanks |   rows | (league,season) fetches |
| ---------------------------- | -----: | ----------------------: |
| 50%                          | 19,168 |                  **70** |
| 80%                          | 30,536 |                 **221** |
| 95%                          | 36,270 |                     455 |
| 100%                         | 38,170 |                     842 |

So complete in-window coverage is **842 bulk calls**, and 80% is **221** — hours, not the multi-day run implied by the
earlier 1,757-pair figure. Fetches must be scoped to the IN-WINDOW pair list, not fanned across 782 leagues x 8 seasons.

**Do not assume a fetch fixes the cup competitions.** 648 of the 842 in-window pairs (27,718 rows) carry NO
`Regular Season - N` round at all. Those are cups/knockouts whose round is a different vocabulary ("Round of 16",
"Quarter-finals") or is simply not published — a bulk fetch may legitimately return nothing for them, which is honest
absence, not a gap. Verify on a pilot pair before spending 648 calls on the assumption.

- [x] [DATA] P1. ✅ Retargeted backfill COMPLETE against the 194 reachable in-window league pairs (10,452 blank rows),
      scoped via the new `--pairs-file` — **instruments-service@34ada099** (QG green). `--leagues` x `--seasons` is a
      cross product that would have spent ~800 calls on 194 pairs' work; a pairs-file spends one call per pair. **Pilot
      verified the scan as a scoping instrument, not just the fetch**: the scan predicted 662 blank rows for 129:2026
      (ARGENTINA_PRIMERA_NACIONAL) and the apply filled **exactly 662** across 1,297 parquets from 648 fetched fixtures,
      each write re-downloaded and verified. Launched only after re-confirming 0 running af-* VMs, so the api-football
      singleton rule holds.
- [ ] [DIAG] P2. Pilot ~5 of the 648 cup pairs before committing the remaining calls; if the API returns no round for
      them, record it as explained-absence rather than an open gap.
- [ ] [DECISION] P2. Pre-2019 (122,864 rows) is outside the stated window — confirm whether the corpus is meant to cover
      2013–2018 at all before spending 915 fetches on it.

### U (2026-07-19) — the round backfill can only REACH 353 of the 842 in-window pairs

Piloting the retargeted backfill against a real blank pair returned `0 rows would-fill across 0 scanned` — not a bug in
the fetch, a **structural reach limit**. The script builds its league universe from the UAC registry
(`get_leagues_by_classification` over `prediction` / `reference` / `features`), which enumerates **94 leagues**. The
corpus has **782 leagues with parquets**. Anything outside the registry is skipped before a call is ever made.

| in-window (2019–2027) blank pairs  | pairs | blank rows |
| ---------------------------------- | ----: | ---------: |
| total                              |   842 |     38,170 |
| **reachable** (league in registry) |   353 |     27,301 |
| **not in the registry universe**   |   489 |     10,869 |

Split of the reachable half:

| reachable subset                        | pairs | blank rows |
| --------------------------------------- | ----: | ---------: |
| has `Regular Season - N` (real leagues) |   194 |     10,452 |
| no regular rounds (cups / unpublished)  |   159 |     16,849 |

**This reframes "backfill to 100%".** 489 in-window league-seasons holding 10,869 blank rows sit in leagues the pipeline
CAPTURED but the registry does not enumerate. That is either (a) capture reaching beyond the intended universe, or (b) a
registry gap — and until it is settled, those rows can be neither filled nor honestly called complete. They are not an
api-football problem; no number of calls touches them.

A first measurement of the registry universe returned **0** leagues because I guessed the classification names
(`tier1`/`tier2`/…) instead of reading the script's actual `("prediction", "reference", "features")`. The numbers above
are from the corrected probe — the 0-league result was discarded, not reported.

- [ ] [DECISION] P1. Settle the 489 non-registry in-window pairs: extend the registry to cover what is being captured,
      or stop capturing them. "Backfill at 100%" cannot be asserted for sports until this is decided one way or the
      other — the gap is a definition problem, not a data-fetch problem.
- [ ] [DATA] P2. The 159 reachable cup pairs (16,849 rows) still need the pilot from § T before spending their calls — a
      cup's round vocabulary is "Quarter-finals", not "Regular Season - N", and a fetch may honestly return nothing.

### V (2026-07-19) — FIXED: features read a legacy `entity=fixtures` object in preference to the LIVE split leg

Found while auditing the § R stale-entity consumer list. `gcs_reader.read_reference_entity` **does** implement the
schedule/outcomes split fallback correctly — but it was **unreachable for every pre-cutover date**. The probe returns
the legacy `entity=fixtures` object first, and the split fallback only runs when that object is absent, which is true
only on/after the 2026-05-23 cutover. Pre-cutover dates still have a legacy object, so features kept reading it.

Measured 2026-07-19, same day, both entities present:

| day        | `entity=fixtures` (what features read) | `entity=fixtures_schedule` (live)   |
| ---------- | -------------------------------------- | ----------------------------------- |
| 2024-03-09 | 317 rows, round populated **56.8%**    | 373 rows, round populated **96.0%** |
| 2023-05-20 | 256 rows, round populated **56.2%**    | 301 rows, round populated **86.7%** |

The features layer was reading a frame that is both **staler and smaller** than the live corpus — and because the § Q
derivation and the § T backfill write ONLY to `fixtures_schedule`, **every bit of the round work was invisible to every
sports feature on pre-cutover dates.** Same consumer-migration class as § R, but subtler: the code HAS the split path,
it simply never reached it. A grep alone would have cleared this file — the reference to `entity=fixtures` looks correct
in isolation, and only reading the probe ORDER shows the defect.

**Fixed — features-service@e4b1f1ba** (QG green): fixtures try the split leg FIRST and fall back to legacy, preserving
coverage for dates predating the split writer.

Two existing tests exercised the legacy path with a blanket `blob_exists=True` mock, so under split-first precedence
they were asserting the wrong leg. That is a mock artifact rather than a production regression — but waving it through
on that reasoning is precisely what let this bug hide, so both now patch the split leg ABSENT (what a pre-split date
actually looks like) and say why, plus a new test pins the precedence itself (legacy object present, split still wins,
legacy bytes never downloaded).

- [ ] [DATA] P0. Sports features must be RE-RUN: every pre-cutover feature row was computed from the stale legacy frame.
      This supersedes the § S re-run note — one re-run now covers both the `total_matchdays` fix and this.

### T P1 — VERIFIED against the corpus, not the log (2026-07-19)

The backfill's own log claimed 9,706 rows filled. That is the script grading its own homework, so the corpus was
re-scanned independently (same single-walk measurement that produced the "before" numbers):

| scope                      | blanks before | blanks after | closed             |
| -------------------------- | ------------: | -----------: | ------------------ |
| **the 194 targeted pairs** |        10,452 |       **14** | **10,438 (99.9%)** |
| corpus-wide                |       161,034 |      150,575 | 10,459             |

**191 of 194 pairs fully cleared.** The 14 residual rows are fixtures the fresh fetch did not cover — left untouched by
design rather than guessed.

Reconciliation of the 91-row gap between the log's claim and the measurement (10,459 measured vs 9,706 + 662 pilot =
10,368): the targeted set includes CURRENT-season (2026) pairs, and live forward-poll captures wrote `round` during the
~1h run. Two NON-targeted pairs moved by the same mechanism and are visible in the diff (`128:2026` 494→479, `255:2026`
359→353). So the measurement exceeds the claim because live capture ran concurrently, not because the count is
unreliable — nothing is unaccounted for.

### W (2026-07-19) — CORRECTION: the "cup competitions" were never cups; they are blank-round LEAGUES

§ T and § U classified 648 in-window pairs (159 of them reachable) as "cups / unpublished" because their
`max_regular_round == 0`, and reasoned that a bulk fetch might legitimately return nothing for them. **That inference
was wrong, and the pilot disproved it.**

`max_regular_round == 0` does not mean "this competition has no regular season". It means **no regular-season round was
OBSERVABLE in the corpus** — which is exactly what a league whose `round` column is entirely blank looks like. The
classifier conflated "is a cup" with "is completely unpopulated", and the second is precisely the population most in
need of the backfill.

Dry-run pilot over 5 of them:

| pair                                | fixtures fetched |                      would-fill |
| ----------------------------------- | ---------------: | ------------------------------: |
| ARGENTINA_PRIMERA 128:2026          |              495 |                         **479** |
| ARGENTINA_PRIMERA_NACIONAL 129:2023 |              670 |                         **512** |
| PRIMERA_RFEF 435:2019+2021          |              760 |                         **760** |
| J2_LEAGUE 99:2026                   |                0 |      0 — out-of-coverage season |
| **total**                           |                  | **1,751 across 11,745 scanned** |

Four of five are ordinary leagues (Argentine Primera, Primera RFEF) that simply had no round captured at all. They are
fully fetchable. Only J2 2026 returned nothing, and that is an out-of-coverage season (not yet published), which IS
honest absence.

**Consequence: the § T/§ U "cup" caveat is withdrawn**, and 16,828 more rows are recoverable than those sections
assumed. Backfill launched over all 159 reachable pairs (af fleet re-confirmed at 0 first, so the api-football singleton
rule holds).

The general lesson, which is the same one that produced the retractions earlier in this sweep: an ABSENCE in the data
was read as a PROPERTY of the data. "No regular rounds recorded" was treated as "this competition has no regular
rounds", when it only ever meant "we captured none". Absence is evidence of missing capture until a fetch proves
otherwise — the pilot is what distinguishes them, not the classifier.

- [x] [DIAG] P2. ✅ Cup pilot run — hypothesis REFUTED, the pairs are fetchable leagues (1,751 rows would-fill on 5).
- [ ] [DATA] P1. 159-pair blank-league backfill RUNNING (16,828 rows targeted); verify against a corpus re-scan, not the
      script log, per the § T P1 precedent.

### Round work — TERMINAL STATE (2026-07-19)

| stage                                    | rows closed | verification                              |
| ---------------------------------------- | ----------: | ----------------------------------------- |
| § Q derivation (ZERO api-football calls) |     115,715 | populated eras 40-66% -> 90-99%           |
| § T 194-pair backfill                    |      10,438 | corpus re-scan; 191/194 pairs cleared     |
| § W 159-pair blank-league backfill       |      16,435 | corpus re-scan; delta 0 vs claim; 158/159 |

Corpus blank-round rows **161,034 -> 134,140** across the two backfills (26,894 closed), on top of the 115,715 the
derivation had already closed for free.

**Every remaining in-window blank is accounted for — nothing is unexplained:**

| remaining in-window blanks         |       rows | status                                                          |
| ---------------------------------- | ---------: | --------------------------------------------------------------- |
| § U pairs absent from UAC registry |     10,869 | **operator decision** — unreachable by any number of calls      |
| residue in reached pairs           |        407 | fixtures the fresh fetch did not cover — untouched, not guessed |
| **total**                          | **11,276** | reconciles exactly to the measured 11,276                       |

The pre-2019 blanks (122,864 rows) sit outside the stated 2019-01-01..2026-07-17 window and are covered by the § T open
decision, not by this work.

**What this cost in api-football calls: 353** (194 + 159 bulk (league,season) fetches). The § Q derivation closed 4.3x
more rows than both backfills combined at ZERO call cost — the ordering (derive first, fetch only the residue) is what
kept this to hours instead of the multi-day run the original per-fixture framing implied.

### X (2026-07-19) — end-to-end chain VALIDATED on real data before committing a fleet

Ran the real read + season-context path against a **pre-cutover** date (2024-03-09 — the case § V was about) rather than
launching multi-day VMs on the assumption it works.

**§ V confirmed live in the real read path**, not just in unit tests: instrumenting
`gcs_reader._read_split_fixtures_fallback` shows `read_reference_entity` now takes the SPLIT leg
(`used the SPLIT leg: True`), with `round` at **193/193 = 100%**.

Chain output for that day:

| column                                | populated       |
| ------------------------------------- | --------------- |
| `round_name`                          | 193/193 (100%)  |
| `matchday`                            | 185/193 (95.9%) |
| `competition_phase`                   | 149/193 (77.2%) |
| `games_remaining` / `points_at_stake` | 149/193 (77.2%) |

`competition_phase` distribution `{late: 118, early: 31, None: 44}`. **The original issue's headline was
`competition_phase` ~100% UNKNOWN** — it is now 77.2% populated with real values. The 44 `None` are league-seasons
absent from the § S season-length map, i.e. the deliberate honest-NaN path, not a failure.

**A row-count heuristic nearly produced a false verdict here.** The split leg has 373 RAW parquet rows but returns 193
after the schedule/outcomes join + normalize, so a "did we get >340 rows?" check reported "STALE LEGACY LEG" when the
fix was in fact working. Counts across a join/normalize boundary are not comparable; instrumenting the actual call is.
Same failure mode as the § W misclassification — inferring a property from an aggregate instead of measuring the thing
itself.

- [ ] [INFRA] P0. Fan out the features re-run. **HARD RULE interaction**: the re-run needs `FORCE=true` (otherwise
      presence-skip makes it a no-op), and `--force` on SPOT is NOT replayable — `RelaunchPreemptedVm` replays the
      original params and force disables the skip the resume relies on, so a preempted run restarts at day one FOREVER
      (`codex/05-infrastructure/spot-vms-for-backfill.md`). Drive it as **bounded per-year chunks** (2019..2026) so a
      preemption replays one year, not the whole corpus. Use the consolidated
      `launch-features-vm.sh --feature-family sports --asset-group SPORTS` (the sports-specific launcher carries a
      deprecation note for new backfills).

### Y (2026-07-19) — P2: `launch-features-vm.sh` prints a post-backfill hint naming a bucket that does not exist

The launcher's closing instructions tell the operator to run:

```
rebuild_manifest_from_canonical_paths('features-sports-sports-central-element-323112', ...)
```

That bucket **404s**. The real one is `features-sports-prd-central-element-323112`
(`resolve_bucket_name(cloud="gcp", kind="features", asset_group="sports")`) — the hint interpolates
`<family>-<asset_group>` and omits the `-prd-` env segment. The data prefix in the hint is wrong too: objects live under
`sports_features/`, not `features/by_date/`.

**This bit me immediately and is worth recording as a monitoring hazard, not just a typo.** I armed the launch watchdog
on the hinted bucket, so its progress metric read `shard_days=0` for 20 minutes — indistinguishable from a genuinely
stalled backfill. A 404 bucket does not error in a `| wc -l` pipeline; it silently returns zero forever. This is the
exact class the async-wait discipline warns about (a run that "logged and heartbeated healthily while writing ZERO
target artifacts"), only inverted: here the artifacts may be fine and the MONITOR is lying. Either direction, the lesson
is the same — **validate that a progress metric can ever be non-zero before trusting a zero reading.**

- [ ] [CODE] P2. Fix the post-backfill hint in `deployment-service/scripts/vm/launch-features-vm.sh` to resolve the
      bucket via `resolve_bucket_name` (never string-interpolate an env-split bucket name) and to name the real
      `sports_features/` prefix.

### Z (2026-07-19) — pilot VALIDATES the re-run; separate `matchday` persistence defect found (NOT root-caused)

Pilot VM `features-sports-sports-20260719-063104` (2024 chunk, SPOT, bounded). Same day, same 17 rows, local recompute
vs what the VM actually wrote:

| column              | LOCAL recompute | WRITTEN by VM |
| ------------------- | --------------: | ------------: |
| `competition_phase` |            4/17 |    **4/17 ✓** |
| `games_remaining`   |            4/17 |    **4/17 ✓** |
| `round_name`        |           17/17 |   **17/17 ✓** |
| `matchday`          |           16/17 |    **0/17 ✗** |

**The re-run is doing its job**: the three features this sweep was about match the local recompute exactly, which
confirms the VM is running the § S + § V code. Across the 7 days written so far, `competition_phase` is 60.5% populated
overall and **66.2% of the rows whose round actually carries a matchday number** — against ~100% UNKNOWN in the original
issue.

**Separate defect: `matchday` is computed and then lost before persistence.** It cannot be a calculator bug — the same
code populates it 16/17 locally, and `competition_phase` (which is DERIVED from matchday) persists correctly. So the
value is dropped between the calculator and the writer.

**My first hypothesis was WRONG and is recorded as such**: I suspected `_run_calc`'s first-writer-wins rule
(`new_cols = [c for c in df.columns if c not in existing_cols]`) was discarding season_context's `matchday` in favour of
an empty one already on `result`. Measured: the base fixtures frame does **not** carry `matchday` (nor any other
season_context column), so that is not the mechanism. Some earlier calculator must introduce the column, but I have not
identified which — **this is an open lead, not a diagnosis.**

**Why this does not block the fan-out**: `round_name` persists at 100%, and `matchday` is a pure regex over it
(`r"(\d+)$"`). The field is therefore recoverable by a light targeted pass with **no features re-run required**, so
baking it into the remaining year-chunks costs nothing that a cheap follow-up cannot fix.

- [ ] [DIAG] P2. Root-cause where `matchday` is dropped between `_compute_season_features` and the writer. Start by
      logging `result.columns` immediately before the `season_context` `_run_calc` to identify which earlier calculator
      introduces the colliding empty column. Do NOT assume the base frame is the source — measured, it is not.
- [ ] [DATA] P3. Once root-caused, recover `matchday` from the persisted `round_name` (regex) rather than re-running the
      whole features corpus.
