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

- [ ] [OPS] P1. Consider making `redo_all` resume-aware in code (skip days whose `round` is already populated), so the
      operator/loop isn't the resume mechanism. Until then, the loop-resume pattern above is the contract.
