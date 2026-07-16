---
doc_type: issue
title:
  Half-time odds — SFI's derived half-time DOES carry half-time ODDS (not just match state), and it is the DENSER
  source; the 746,928 legacy in-play rows are per-bookmaker FULL-TIME-market prices on a coarse grid, of which only
  ~3.1% are PIT-usable half-time-break quotes — and the HT-RESULT market exists in NEITHER source
summary:
  'Read-only investigation answering the operator''s 2026-07-16 question ("we want half time odds — is there knowledge
  of this from SFI derived half time?"), commissioned to settle OR-5b(c) before the `market-data-tick-sports` delete.
  **The premise that SFI is match-STATE-only is FALSE.** The captured SFI contract `sfi_progressive_stats` (entity
  `progressive_stats`) declares **12 odds/PRICE columns** (`odds_1x2_home/draw/away`, `odds_ou_over/under/line`,
  `odds_ah_home/away/line`, `odds_asian_corner_over/under/line`) plus `ht_start_timer`/`ht_end_timer`, and they are
  **live and populated**: measured on real parquets, `odds_1x2_home` is 90% non-null overall and **100% non-null inside
  the half-time break** (2550-2999s), with **31/31 sampled fixtures (100%) across 2021→2026 and 5 leagues carrying 1X2
  odds quoted DURING the HT break**. They are genuine repriced in-play quotes, not a frozen pre-match price (28-41
  distinct values per match; one fixture drifts 3.3 at kickoff → 36.0 at HT → 301 late). SFI covers 2020→2026 over a
  **superset** of the 10 leagues that have legacy in-play rows. **What SFI does NOT give**: bookmaker identity (one
  anonymous consensus series — no `bookmaker` column), no exchange lay side, no cross-book dispersion. **The 746,928
  in-play rows** (69-object sample, 2020-2026, 300,194 rows / 14,876 in-play = 4.96%) are **per-bookmaker** (23 books:
  pinnacle, matchbook, betfair_ex_uk/eu, …) but carry **only full-time markets** — `h2h`/`totals`/`spreads`/`h2h_lay`,
  **zero HT-specific markets, in-play OR pre-match** — on a **coarse grid** (+5/+15/+30/+45/+60/+75/+90/+120), not
  continuous. Against the features-service HT odds PIT gate (`_apply_ht_odds_pit_gate`, default cutoff `bm_mtk >= -55`):
  **only 3.1% (+45..55) is PIT-usable HT-break data**; 20.3% (+56..62) and 25.7% (2nd half) and 17.0% (post-match) are
  **actively REJECTED as 2nd-half leakage**. **The horizon ladder has NO HT bucket** — `TIER1_HORIZONS` is 8 pre-match
  buckets T-24h…T-0 (the "T-0/HT" framing in circulation is wrong). **BIG FINDING**: `assign_horizon_buckets_vectorised`
  applies `nearest_idx[vals < 0] = N_BUCKETS - 1` **AFTER** the staleness rejection, resurrecting dropped post-kickoff
  rows into T-0 — measured **184/282 (65%) of sampled canonical T-0 rows are post-kickoff, bm down to −71.1 min**
  (lookahead leakage; adjacent to `sports_odds_stale_fixture_reinjection_2026_07_14`). **The HT-RESULT market
  (first-half 1X2) is captured NOWHERE** — `ht_odds_home_implied` reads `first_half_*_odds` from the **dormant,
  never-captured** `CanonicalProgressiveOdds`; SFI''s provider API serves it (`h1_*` in `SFMatchProgressiveOddsRaw`) but
  the adapter''s `_extract_odds` never reads it → **re-fetchable from SFI, NOT recoverable from the legacy bucket**.
  Recommendation: **OR-5b(c) → B-REFINED** — recover the in-play rows as a ~zero-marginal-cost rider on the already-
  recommended OR-5b(b) option-D G1 read-split-merge, into a DISTINCT population quarantined from the pre-match bucketing
  path (never merged into the T-0 lineage, which is already 65% contaminated).'
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    unified-api-contracts,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags:
  [
    sports,
    odds,
    halftime,
    soccer-football-info,
    in-play,
    bucket-canonicalisation,
    data-correctness,
    lookahead-bias,
    investigation,
    read-only,
  ]
related:
  [
    ./mdt_legacy_canonical_row_gap_2026_07_16.md,
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ./sports_odds_stale_fixture_reinjection_2026_07_14.md,
    ./sports_odds_horizon_bucket_malformed_tick_field_2026_07_15.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    'operator question 2026-07-16 — "we want helf time odds is there knowledge of this from sfi derived half time?"',
    "OR-5b(c) — disposition of the 746,928 post-kickoff / in-play rows",
    "./mdt_legacy_canonical_row_gap_2026_07_16.md",
  ]
---

# Half-time odds: does SFI's derived half-time already give us them?

> **READ-ONLY investigation. Zero mutations** — no writes, no copies, no manifest changes, no bucket changes. Every
> number below is measured live against the real buckets on 2026-07-16.

## THE ANSWER — one sentence

**Yes — SFI's derived half-time already carries half-time ODDS, not merely half-time state: the captured
`sfi_progressive_stats` contract has 12 populated price columns and 100% of sampled fixtures have 1X2 odds quoted
_during_ the half-time break at 30-second granularity — so the half-time market LEVEL survives the bucket delete; what
dies with the bucket is the _per-bookmaker_ half-time dispersion (~3.1% of the 746,928 rows, ~23k quotes), and the
HT-RESULT market (first-half 1X2) is in NEITHER source and must be re-fetched from SFI regardless.**

## The hypothesis this investigation was given — and why it is WRONG

The commissioning brief asserted a clean split: _"SFI tells you the STATE (score, stats); only the odds rows tell you
the PRICE."_ **That is false at the schema level and at the data level.** SFI's progressive endpoint returns a nested
`odds` object alongside the stats, and the adapter has extracted it since inception (`_extract_odds`,
`instruments-service/instruments_service/reference_data/adapters/sports/adapters/soccerfootball_info.py:399`). The
docstring of `_normalize_sfi_progressive_stat` says so in as many words: _"SFI progressive data includes per-team stats
at 30-second intervals: xG, dominance index, **and in-play odds**."_

The one place SFI genuinely does not serve odds is the separate `get_odds()` reference path
(`soccerfootball_info.py:271`, _"SoccerFootball.info does not provide odds data"_) — that is the **bookmaker-odds
data_type**, a different surface. Reading that line alone (and stopping) is almost certainly how the "SFI = state only"
belief formed.

---

## 1. SFI column inventory — ARE there price fields? **YES — 12 of them**

**Captured contract** `SPORTS_SFI_PROGRESSIVE_STATS`
(`unified-api-contracts/unified_api_contracts/internal/schemas/_sports_contracts.py:521`),
`data_type=sfi_progressive_stats`, entity folder `progressive_stats`, layout `PER_DAY_PER_LEAGUE`:

| Group             | Columns                                                                                                  | Nature       |
| ----------------- | -------------------------------------------------------------------------------------------------------- | ------------ |
| Identity / timing | `fixture_id`, `timer_seconds`, `team`, `available_at`, `match_end_time`                                  | —            |
| **HT timing**     | **`ht_start_timer`**, **`ht_end_timer`**, `ft_timer`                                                     | **HT state** |
| Match state       | `goals`, `possession_pct`, `attacks*`, `shots*`, `corners`, `fouls`, cards, `dominance*`, `xg_home/away` | state        |
| **PRICE / ODDS**  | **`odds_1x2_home`**, **`odds_1x2_draw`**, **`odds_1x2_away`**                                            | **PRICE**    |
| **PRICE / ODDS**  | **`odds_ou_over`**, **`odds_ou_under`**, **`odds_ou_line`**                                              | **PRICE**    |
| **PRICE / ODDS**  | **`odds_ah_home`**, **`odds_ah_away`**, **`odds_ah_line`**                                               | **PRICE**    |
| **PRICE / ODDS**  | **`odds_asian_corner_over`**, **`odds_asian_corner_under`**, **`odds_asian_corner_line`**                | **PRICE**    |

**Verified against LIVE data, not just the contract** (`trust the actual distribution, not the constant`) —
`gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day=2024-05-11/pipeline_mode=batch_soccer_football_info/entity=progressive_stats/league=EPL/progressive_stats.parquet`:
**46 columns, 1,663 rows, 8 fixtures**, all 12 odds columns present and populated.

### Odds population BY MATCH PHASE (real parquet, EPL 2024-05-11)

| Phase               | `timer_seconds` | Rows | `odds_1x2_home` non-null |
| ------------------- | --------------- | ---- | ------------------------ |
| Pre-kickoff (t=0)   | 0               | 224  | 137 (61.2%)              |
| 1st half            | 1–2549          | 671  | 648 (96.6%)              |
| **HALF-TIME BREAK** | **2550–2999**   | 120  | **120 (100.0%)**         |
| 2nd half            | 3000+           | 648  | 595 (91.8%)              |

### Breadth — not a one-file fluke

| File                        | Fixtures | HT-break rows | HT-break 1X2 non-null | HT AH | HT OU |
| --------------------------- | -------- | ------------- | --------------------- | ----- | ----- |
| `sfi_EPL_2021-08-14`        | 7        | 105           | 100/105               | 105   | 105   |
| `sfi_BUNDESLIGA_2022-04-16` | 5        | 73            | 35/73                 | 35    | 35    |
| `sfi_EPL_2023-03-15`        | 2        | 30            | 28/30                 | 28    | 28    |
| `sfi_EPL_2024-05-11`        | 8        | 120           | 120/120               | 120   | 120   |
| `sfi_LA_LIGA_2025-04-12`    | 4        | 60            | 60/60                 | 60    | 58    |
| `sfi_SERIE_A_2026-05-10`    | 5        | 75            | 74/75                 | 71    | 74    |

> **31/31 fixtures (100.0%) across 2021→2026 and 5 leagues carry 1X2 odds quoted DURING the half-time break.**

### Falsification test — are these real in-play prices, or a frozen pre-match quote repeated?

**They are real.** Per fixture, `odds_1x2_home` takes **28–41 distinct values** across a match and reprices hard through
the break:

| Fixture            | Kickoff (t=0) | HT break        | Late  |
| ------------------ | ------------- | --------------- | ----- |
| `2c502fa4346f4359` | 1.62          | 2.75 → 1.727    | 17.0  |
| `35c97fc9b5a900c1` | 3.30          | **36.0 → 29.0** | 301.0 |
| `523db4a621f8132`  | 2.06          | 2.60 → 2.625    | 8.0   |

A home price moving 3.30 → 36.0 by half-time is a market that has _seen the first half_. This is genuine half-time
market knowledge.

### Coverage — 2020→2026, a SUPERSET of the in-play leagues

SFI `progressive_stats` is present from **2020** (floor `("soccer_football_info","SFI_PROGRESSIVE_STATS") = 2020-01-01`,
`league_data.py`) through **2026-05-10**, e.g. day=2020-10-17 carries 26 leagues (ALLSVENSKAN, BUNDESLIGA, BUNDESLIGA_2,
DANISH_SUPERLIGA, EKSTRAKLASA, ELITESERIEN, ENG_CHAMPIONSHIP, EPL, EREDIVISIE, JUPILER_PRO, LIGUE_1/2, MLS, SERIE_A/B,
SUPER_LIG, …). **Every one of the 10 leagues that has legacy in-play rows has SFI progressive coverage** (naming
differs: `2._BUNDESLIGA`→`BUNDESLIGA_2`, `CHAMPIONSHIP`→`ENG_CHAMPIONSHIP`, `FIRST_DIVISION_A`→`JUPILER_PRO`).

### What SFI does NOT give

1. **No bookmaker identity** — there is no `bookmaker`/`venue` column. SFI is **one anonymous consensus price series**.
2. **No exchange lay side** (`h2h_lay`), no back/lay spread, no cross-book dispersion or best-price surface.
3. **No HT-RESULT market** — see §4. The captured columns are **full-time** markets (1X2/OU/AH/corners) _priced during_
   the break, not "who wins the first half".
4. **Contract dtype drift (finding)** — `timer_seconds`/`ht_start_timer`/`ht_end_timer`/odds columns are declared
   `int64`/`float64` but land as **strings** in the parquet; `ht_end_timer` is **100% NULL** (1,663/1,663) while
   `ht_start_timer` is uniformly stamped. `detect_halftime_window()` sets both, so the writer or normaliser is dropping
   `ht_end_timer`.

---

## 2. The 746,928 in-play rows — anatomy

**Sample**: 69 objects from the legacy bucket `market-data-tick-sports-central-element-323112`, spread over 14 days
across **2020→2026**. **300,194 rows, of which 14,876 (4.96%) are in-play** (`minutes_to_kickoff < 0`) — consistent with
the exact-pass figure of 5.59% in `mdt_legacy_canonical_row_gap_2026_07_16.md`.

### They ARE per-bookmaker — this is their unique property

**23 distinct bookmakers** carry in-play rows: `pinnacle` (1,825), `matchbook` (1,576), `unibet` (1,336), `casumo`
(854), `paddypower` (849), `betfair_ex_eu` (756), `betfair_ex_uk` (744), `draftkings` (729), `fanduel` (702),
`unibet_uk` (698), `coral` (663), `betsson` (583), … **This is the one thing SFI cannot supply.**

### But the market universe is FULL-TIME ONLY — there are NO HT markets, in-play or pre-match

| Market key | All rows | In-play rows | Meaning                     |
| ---------- | -------- | ------------ | --------------------------- |
| `h2h`      | 196,611  | 9,840        | full-time 1X2               |
| `totals`   | 57,988   | 2,686        | full-time over/under        |
| `h2h_lay`  | 25,233   | 1,434        | full-time 1X2, exchange lay |
| `spreads`  | 20,362   | 916          | full-time handicap          |

> **The answer to "are there HT markets present pre-match too?" is NO.** The odds-api capture only ever requested
> `h2h`/`totals`/`spreads`/`h2h_lay`. **No HT-result, no HT over/under, no HT-FT — anywhere in the corpus, at any
> horizon.** Nothing of that kind is lost by deleting the bucket, because it was never there.

### The in-play rows sit on a COARSE GRID, not a continuous in-play feed

Minutes after kickoff (rows, % of in-play): **+5** (1,031, 6.9%) · +15 (1,510, 10.2%) · +29/30 (1,923, 12.9%) · +45
(343, 2.3%) · +50 (158, 1.1%) · **+60 (2,093, 14.1%)** · +75 (442, 3.0%) · +89/90 (2,606, 17.5%) · **+120 (1,342,
9.0%)** · plus a long tail to +140.

Compare SFI: **30-second** snapshots continuously across the break. **SFI is ~30× denser through half-time than the
legacy grid, which has at most 1–2 points anywhere near the break.**

### Against the features-service HT odds PIT gate — the decisive cut

`features_service/sports/exporters/odds_features_exporter.py:_apply_ht_odds_pit_gate` rejects
`bm_minutes_to_kickoff < -(ht_actual_minute + 10)`; with HT unknown the **default cutoff is −55**.

| Phase                             | Rows    | %        | PIT verdict                        |
| --------------------------------- | ------- | -------- | ---------------------------------- |
| 1st half (+1..44)                 | 4,976   | 33.4%    | passes gate, but **not HT** data   |
| **HT BREAK, PIT-VALID (+45..55)** | **457** | **3.1%** | **the only usable HT-break slice** |
| HT break, PIT-REJECTED (+56..62)  | 3,017   | 20.3%    | **rejected — 2nd-half leakage**    |
| 2nd half (+63..95)                | 3,829   | 25.7%    | **rejected**                       |
| Post-match (+96 and later)        | 2,524   | 17.0%    | **rejected** — match already over  |

> **63.2% of the in-play rows are exactly what the HT odds pipeline actively throws away**, and 17% are quotes on a
> finished match. The single biggest grid point (+60, 14.1%) sits just past the cutoff — it is the **second-half
> restart**, not the break.
>
> **Extrapolated to the 746,928**: ~**23,000 rows** (3.1%) are per-bookmaker quotes inside the PIT-valid half-time-break
> window. That — and only that — is the genuinely irreplaceable half-time odds content in the legacy bucket.

---

## 3. Does canonical already hold in-play / HT odds? **There is NO HT horizon — and T-0 is 65% contaminated**

**The horizon ladder has no HT bucket.** `TIER1_HORIZONS`
(`market-data-processing-service/.../adapters/sports/bucket_assignment_adapter.py:50`) is **8 pre-match buckets**:
`T-24h, T-12h, T-6h, T-4h, T-2h, T-1h, T-10m, T-0`. Confirmed on the live processed layer — the timeframes present for
`league_id=ELITESERIEN/day=2024-05-11` are exactly `T-0 T-10m T-12h T-1h T-24h T-2h T-4h T-6h`. **Any framing that
speaks of an "HT" horizon bucket (including the brief that commissioned this work) is wrong.**

### BIG FINDING — post-kickoff rows are force-fed into T-0, defeating the staleness cap

```python
nearest_idx[min_diffs > caps] = -1        # staleness rejection
nearest_idx[vals < 0] = N_BUCKETS - 1     # ← post-kickoff → T-0, runs AFTER, RESURRECTS rejected rows
```

The post-kickoff override executes **after** the staleness rejection, so a row at `bm = −71` — which the T-0 cap (±5
min) had already marked `-1` (drop) — is **restored into T-0**. T-0 nominally means "the price at kickoff, ±5 min".

**Measured on the live canonical processed layer** (6 sampled `timeframe=T-0/bucketed.parquet`):

| File                           | T-0 rows | post-kickoff (`bm<0`) | `bm` range      |
| ------------------------------ | -------- | --------------------- | --------------- |
| `t0_2022-04-16_BUNDESLIGA`     | 33       | **33 (100%)**         | −49.2 … −33.1   |
| `t0_2023-03-15_PREMIER_LEAGUE` | 35       | 0                     | 4.7 … 4.8       |
| `t0_2023-09-23_EREDIVISIE`     | 53       | **40**                | −42.7 … 4.9     |
| `t0_2024-05-11_ELITESERIEN`    | 7        | 0                     | 4.4 … 4.4       |
| `t0_2024-11-09_BUNDESLIGA`     | 91       | **70**                | −55.1 … 4.5     |
| `t0_2025-04-12_LA_LIGA`        | 63       | **41**                | **−71.1** … 4.8 |
| **Σ**                          | **282**  | **184 (65.2%)**       |                 |

> **65% of sampled canonical T-0 rows are post-kickoff prices mislabeled as kickoff prices**, some from 71 minutes into
> the match. Anything training on the T-0 horizon is consuming second-half information (goals, red cards, momentum) as a
> pre-kickoff feature. **This is live lookahead leakage.**
>
> **Not a duplicate**: `sports_odds_stale_fixture_reinjection_2026_07_14.md` already identifies the same locus and the
> `bm_minutes < 0 → T-0` rule, from the **zombie/frozen-board** angle (staleness never checked). **New here**: (a) the
> ordering bug — the override _undoes_ the staleness rejection; (b) the quantification — **65% of T-0**; (c) that the
> leakage arrives from **genuine, fresh in-play rows**, not only stale boards. Folded into that issue rather than filed
> twice.

**So: canonical DOES already hold in-play/HT odds — as a defect, not a feature.** They are not addressable as half-time
data; they are silently pretending to be kickoff prices.

---

## 4. What do the FEATURES consume for half-time?

Three distinct things, and only one of them is odds:

| Feature family                                                | Consumes                                                                    | Source                                             |
| ------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------- |
| **HT state** (`ht_state`, `ht_delta_goals`, `ht_*_home/away`) | SFI `ht_stats` + api-football `FIXTURE_STATS`                               | `regenerate_feature_definitions.py:44` → **state** |
| **HT timing** (`ht_break_minutes`, `ht_actual_minute`)        | SFI progressive → `compute_ht_break_minutes()` / `detect_halftime_window()` | **SFI — gates the odds**                           |
| **HT ODDS** (`ht_odds_home_implied/draw/away`)                | **`first_half_*_odds` from `CanonicalProgressiveOdds`**                     | **NOTHING — see below**                            |

### The HT odds feature has a consumer but NO producer

`ht_odds_home_implied` is real and consumed — it is in `LIVE_FEATURE_SUBSET` (`live/live_feature_subset.py:26`) and it
is the field that decides `capture_status` at emit time (`app/pubsub/subscriber.py:68`, `_FSS_IMPLIED_PROB_KEYS`). Its
calculator (`calculators/ht_features.py:200 compute_ht_features_from_odds`) reads **`first_half_home_odds` /
`first_half_draw_odds` / `first_half_away_odds`** — i.e. the **HT-RESULT market**, mirroring
`CanonicalProgressiveOdds.first_half_*`.

**Nothing in the persisted corpus populates those fields:**

- `CanonicalProgressiveOdds` (`uac/canonical/domain/sports/progressive.py:104`) has **no `data_type`, no entity folder
  in `SPORTS_DATA_TYPE_TO_FOLDER`, no `CONTRACT_REGISTRY` entry**. Only tests and the UI context mirror reference it. It
  is **dormant** — modelled, never captured.
- The captured `sfi_progressive_stats` carries **full-time** markets only — `_extract_odds()` reads `1X2`, `over_under`,
  `asian_handicap`, `asian_corner` and **never the first-half keys**, even though SFI's provider schema serves them
  (`SFMatchProgressiveOddsRaw.h1_home_win / h1_draw / h1_away_win / h1_ah_* / h1_ou_* / h1_ac_*`,
  `soccer_football_info/schemas.py:551`).
- The legacy MDT bucket has **no HT market at all** (§2).
- The only live path (`sports/engine/orchestrator.py:114`) **falls back to mapping generic `home`/`draw`/`away` odds
  into `first_half_*_odds`** — a full-time price relabelled as a first-half price. **That is a semantic mislabel and its
  own finding**; the other producer is `mock_data_provider.py:74`.

> **Consequence: `ht_odds_home_implied` is structurally NULL in batch, and semantically WRONG in live.** And critically
> — **the HT-RESULT market is missing from BOTH sides of the OR-5b(c) decision.** Deleting the legacy bucket loses none
> of it, because it never held any. It is **re-fetchable from SFI** (the provider serves `h1_*`; the adapter must be
> extended) — a capture gap, not a deletion loss.

---

## 5. VERDICT

### (i) Is SFI-derived half-time knowledge a SUBSTITUTE for half-time odds?

**For the half-time market LEVEL — YES, and it is the strictly better source.** SFI carries populated 1X2/OU/AH/corner
prices at 30-second granularity through the entire break, on 100% of sampled fixtures, 2020→2026, across a superset of
the affected leagues, and those prices demonstrably reprice on first-half information. The legacy bucket offers at most
1–2 coarse grid points near the break, and its densest in-play point (+60) is past the leakage cutoff.

**For per-bookmaker half-time microstructure — NO.** SFI is one anonymous consensus series. It cannot answer "what did
Pinnacle price at half-time", cross-book dispersion, the exchange lay side, or best-price/execution modelling. Only the
legacy rows can.

**For the HT-RESULT market — NEITHER source qualifies.** Not captured anywhere; re-fetch from SFI.

### (ii) Do the 746,928 in-play rows contain genuine HT odds that exist NOWHERE else?

**Yes, but a thin slice: ~3.1% ≈ 23,000 rows** — per-bookmaker quotes inside the PIT-valid half-time-break window
(+45..55), across 23 bookmakers. That per-bookmaker HT dispersion is genuinely non-reproducible from SFI.

The other ~96.9% is **not** unique half-time data: 33.4% first-half, 20.3% break-but-PIT-rejected, 25.7% second-half,
17.0% post-match — and the market LEVEL those rows express is already held, denser, by SFI. **63.2% is precisely what
the HT odds PIT gate exists to discard.**

### (iii) Recover / park / discard — and what is irreversibly lost by each?

**RECOVER — but quarantined. OR-5b(c) → B-REFINED** (a refinement of runbook option **B**, not option A).

The decisive economics: `mdt_legacy_canonical_row_gap_2026_07_16.md` already recommends **OR-5b(b) option D** — one
schema-aware read-split-merge over the **3,816 G1 objects** (0.23 GB), which are a strict superset (`G3 ⊂ G2 ⊂ G1`) and
**already contain these in-play rows**. So the in-play rows are **already being read**. Preserving them is a **filter
decision inside an operation that is happening anyway** — marginal cost ≈ 0. The real question is not _whether to spend
effort recovering them_, but _whether to actively drop them mid-flight_.

- **REJECT A (recover pre-match only, document the exclusion)** — it pays nothing to discard ~23,000 non-reproducible
  per-bookmaker HT-break quotes plus the full in-play trajectory, on an irreversible basis, when the objects are already
  open on the table. The "preserves canonical's pre-match-only property" rationale **does not survive measurement**:
  that property **is already false** — canonical's T-0 is 65% post-kickoff (§3). There is no purity to protect.
- **REJECT C (prove the mechanism first)** — **the mechanism is now proven, so (c) is spent.** The exclusion is **not**
  a deliberate lookahead-bias policy: no adapter filter exists, and the processed layer **actively force-feeds**
  post-kickoff rows into T-0. It is an artifact of the June campaign's snapshot grid, and the pre-match-only appearance
  is an accident, not a guarantee.
- **ADOPT B-REFINED**:
  1. **Carry the in-play rows through the option-D G1 recovery** (no extra read; they are in the same objects).
  2. **Land them in a DISTINCT population** — own `data_type` / `pipeline_mode` (e.g. an explicit in-play marker),
     **never merged into the pre-match `data_type=odds` lineage that MDPS buckets**. This is mandatory, not stylistic:
     `assign_horizon_buckets_vectorised` would sweep every recovered in-play row into **T-0** and deepen a 65%
     contamination into a much worse one. **Merging them into the pre-match path would be a data-correctness
     regression.**
  3. **Delete-gate unchanged** — the bucket becomes delete-eligible only after the recovered cells are crc/row-verified
     at the OBJECT layer (T4.1), per the parent issue.

**What each option irreversibly loses:**

| Option                     | Irreversibly lost on delete                                                                               |
| -------------------------- | --------------------------------------------------------------------------------------------------------- |
| **B-REFINED [WORKER REC]** | **Nothing.** HT market level (SFI) + per-bookmaker HT dispersion (recovered) both survive.                |
| A (pre-match only)         | ~23,000 PIT-valid per-bookmaker HT-break quotes + the entire in-play trajectory across 23 books, forever. |
| C (prove first)            | Nothing yet — but the mechanism is already proven here, so C only delays the same decision.               |
| Discard / delete now       | As A, plus the 6,372,806 genuine pre-match rows the parent issue already ruled must be recovered.         |

> **The half-time odds question does NOT block the delete on its own** — SFI independently holds the half-time market
> level, denser and better. **But the bucket is already blocked by OR-5b(b)** (6.37M genuine pre-match quotes), and
> since the G1 objects must be opened anyway, the in-play rows should ride along rather than be dropped for free.

---

## Cross-checks

- **`mdt_legacy_canonical_row_gap_2026_07_16.md` (parent)** — its class-2 verdict ("REAL but policy-ambiguous, mechanism
  unproven") is now **resolved**: mechanism = June-campaign snapshot-grid artifact, **not** a deliberate pre-match-only
  policy; its cited "`assert_available_at_present`/lookahead guarantee that may rest on it" **does not exist in the
  processed layer** (T-0 is 65% post-kickoff). Its OR-5b(c) recommendation of **A [WORKER REC]** should be **superseded
  by B-REFINED**.
- **`sports_odds_stale_fixture_reinjection_2026_07_14.md`** — same locus, complementary angle; this doc adds the
  ordering bug + the 65% quantification + the fresh-in-play (non-zombie) leakage class. **No duplicate filed.**
- **The 68.6% ML-readiness cluster / horizon framing** — the "T-24h/T-1h/T-0/**HT**" ladder does **not exist**. Any
  diagnosis resting on an HT horizon bucket needs re-reading against the real 8-bucket pre-match ladder.

## Loose ends / follow-ups (not fixed here — read-only investigation)

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                 | Triage                                                                        |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1   | ~~**T-0 is 65% post-kickoff prices** (to −71 min) — `nearest_idx[vals<0]=N_BUCKETS-1` runs AFTER the staleness rejection and resurrects dropped rows. **Live lookahead leakage into a training feature.**~~ **FIXED — MDPS@3bf56ff** (2026-07-16). Full-census re-measure: **39.83%**, not 65%; worst **−374.6 min**. See Progress Log 2026-07-16 (lookahead-leak fix). | **BIG FINDING → operator; fixed in MDPS; recompute + HT-horizon todos below** |
| 2   | **`ht_odds_home_implied` has a consumer but no producer** — reads `first_half_*` from the dormant `CanonicalProgressiveOdds`; structurally NULL in batch.                                                                                                                                                                                                               | New issue / feature-gap todo — sports_master                                  |
| 3   | **Live HT odds are semantically mislabelled** — `orchestrator.py:114` maps generic `home`/`draw`/`away` into `first_half_*_odds`, presenting a full-time price as a first-half price.                                                                                                                                                                                   | **Data-correctness → own issue doc**                                          |
| 4   | **SFI serves `h1_*` first-half markets we never capture** — `_extract_odds()` reads only 1X2/OU/AH/corner. The HT-RESULT market is a **re-fetchable capture gap**, not a deletion loss.                                                                                                                                                                                 | Capture-gap todo — sports_master (P1)                                         |
| 5   | **SFI contract dtype drift** — `timer_seconds`/`ht_*`/odds declared int64/float64, land as **strings**; **`ht_end_timer` 100% NULL** though `detect_halftime_window()` sets it.                                                                                                                                                                                         | Feeds the sports contract-drift lane (T2.9)                                   |
| 6   | **`sfi_progressive_stats` odds columns appear to have no downstream consumer** — a populated, live, 30s in-play price series (incl. the HT break) that no feature reads.                                                                                                                                                                                                | **Opportunity → operator; sports_master**                                     |

## Progress Log

**2026-07-16** — Read-only investigation executed to answer the operator's half-time-odds question and settle OR-5b(c).
**The commissioning hypothesis ("SFI = state, not price") is DISPROVEN** at both schema and data level: the captured
`sfi_progressive_stats` contract carries **12 odds columns**, measured **100% non-null inside the HT break** on real
parquets, **31/31 fixtures across 2021→2026 / 5 leagues**, with genuine repricing (28–41 distinct values/match; 3.30 →
36.0 kickoff→HT). SFI covers **2020→2026** over a **superset** of the 10 in-play leagues. The 746,928 in-play rows
(69-object sample, 300,194 rows, 14,876 in-play = 4.96%) are **per-bookmaker (23 books)** but **full-time markets only**
(`h2h`/`totals`/`spreads`/`h2h_lay` — **zero HT markets, in-play or pre-match**) on a **coarse grid**; against the HT
PIT gate only **3.1% (+45..55) is usable**, **63.2% is actively rejected as 2nd-half leakage**, 17.0% is post-match.
**No HT horizon exists** (`TIER1_HORIZONS` = 8 pre-match buckets, confirmed on the live processed layer). **BIG
FINDING**: the post-kickoff override runs after the staleness rejection → **184/282 (65%) of sampled canonical T-0 rows
are post-kickoff, to −71.1 min** — live lookahead leakage (folded into the existing stale-reinjection issue, not
duplicated). **The HT-RESULT market is captured NOWHERE** — `ht_odds_home_implied` reads the dormant
`CanonicalProgressiveOdds.first_half_*`; SFI's API serves `h1_*` but `_extract_odds()` never reads it → re-fetchable,
not a deletion loss. **Verdict: half-time market LEVEL is safe without the bucket (SFI is denser and better); what dies
is ~23,000 per-bookmaker PIT-valid HT-break quotes. OR-5b(c) → B-REFINED** — carry the in-play rows through the
already-required option-D G1 read-split-merge (marginal cost ≈ 0) into a **distinct population quarantined from the
pre-match bucketing path**, because merging them into `data_type=odds` would sweep them into T-0 and deepen the existing
65% contamination. Options A and C are superseded: A's "pre-match-only property" is already false; C's mechanism is now
proven (June snapshot-grid artifact, not policy). Zero mutations; scratch data deleted.

---

## Todos (opened 2026-07-16 by the lookahead-leak fix leg)

- [x] [CODE] P0. **Fix the bucketing ordering so post-kickoff rows stay rejected** —
      `market-data-processing-service/.../adapters/sports/bucket_assignment_adapter.py`. **DONE — MDPS@3bf56ff**:
      `bm_minutes_to_kickoff < 0` now returns `-1` (REJECT) in BOTH `assign_horizon_bucket` (scalar — it hardcoded
      `return N_BUCKETS - 1` before any staleness check) and `assign_horizon_buckets_vectorised`; all three rejection
      classes (staleness / post-kickoff / NaN) write the same terminal `-1`, so ordering can no longer resurrect a
      dropped row. A wholly in-play shard records `empty_confirmed` (honest absence), never a false `attempted_failed`.
      Evidence: QG green (1978 passed, 1 skipped); 21 new regression tests in `TestPostKickoffRowsRejected`; measured
      OLD admitted 5/5 post-kickoff values into T-0, NEW admits 0/5, pre-match assignment byte-identical.
- [ ] [DATA] P0. **RECOMPUTE the canonical T-0 lineage + its features descendants (sports is FROZEN — do NOT run this
      until the cutover completes).** Measured scope, full census, zero misses: - **MDPS canonical**:
      `data_type=odds_horizon_bucket`, `timeframe=T-0` — **11,373 shards / 368,366 rows** (2020-06-06→2026-06-19, 38
      leagues). **146,738 rows (39.83%) are post-kickoff** and disappear on re-derive; **7,101/11,373 shards (62.4%)**
      carry ≥1. Affects **17,899/27,465 fixtures (65.2%)** across **1,316/1,795 days**. The other 7 timeframes are
      **PROVEN CLEAN — 0/4,151,352 rows** post-kickoff across 97,631 shards (each timeframe's worst value sits exactly
      inside its own cap: T-10m 5.0, T-1h 50, T-2h 105, T-4h 220, T-6h 330.2, T-12h 675, T-24h 1380) → **recompute scope
      is T-0 ONLY**, not the whole ladder. - **features-service**: on those 1,316 dates — **1,275 `ODDS_FEATURES` +
      15,415 `DERIVED_FEATURES` shards** (the 559-col matrix) must re-derive. `FIXTURE_FEATURES` (26,942 shards) are not
      odds-derived → out of scope.
- [ ] [CODE] P0. **The features `HT` model horizon loses its odds source when the leak is fixed — it is fed BY the
      bug.** `MODEL_HORIZONS = ["T-24h","T-1h","T-10m","HT"]` and `FEATURE_HORIZONS["HT"]` ends `[…, "T-0", "HT"]`; MDPS
      never emits `horizon_name="HT"`, so `_find_best_snapshot` falls back to the **MDPS T-0 bucket** (verified by
      running the real code). T-0 was the only bucket carrying `bm<0` **because the bug put them there** — so the HT
      horizon was silently living off the leak. Post-fix, `_find_best_snapshot` still returns T-0, now pre-match-only →
      **HT feature rows become kickoff prices mislabelled `horizon="HT"`** (conservative — no lookahead — but
      semantically wrong). Correct fix = point the HT horizon at the **quarantined in-play population** from OR-5b(c)
      B-REFINED, or drop the HT odds horizon until that population exists. **This invalidates the "there is no HT
      horizon" framing in §3 of this doc — true of MDPS's `TIER1_HORIZONS`, FALSE of features-service, which has a real,
      specified HT model boundary** (`features_service/sports/docs/specs/halftime_data_architecture.md`: predict the 2nd
      half at half-time from actual HT scores + progressive stats). At that boundary post-kickoff odds are **correct PIT
      data, not leakage** — the defect was always the CONTAINER (a pre-match bucket), never the rows themselves.
- [ ] [CODE] P0. **BIG FINDING (new, independent of the ordering bug) — the horizon gate does not gate the
      T-0-closing-derived columns.** `compute_clv_features` defines closing as `horizon_name == "T-0"` and
      `compute_opening_odds` computes movement vs that closing; `_compute_aux_features` merges
      `clv_df`/`opening_df`/`velocity_df`/`steam_df` into **every** model horizon's rows — including the pre-match
      T-24h/T-1h/T-10m — which already contradicts the exporter's own stated design
      (`FEATURE_HORIZONS["T-24h"] = ["T-24h"]`, _"Model 2A (T-24h) only sees T-24h snapshot features"_). Measured: **all
      27** T-0-closing-derived columns (`clv_*`, `sharp_clv_*`, `clv_direction_*`, `odds_movement_*`, `opening_*`,
      `velocity_*`, `steam_*`) declare `min_horizon = FeatureHorizon.T_24H` and **survive `apply_horizon_gate` at EVERY
      horizon, T-24h included (27/27)**. So a T-24h pre-match model can see the closing (kickoff) line — **lookahead by
      construction, even with a perfectly clean T-0**. The ordering bug made it strictly worse (the "closing" line was a
      post-kickoff price for 65.2% of fixtures), but fixing T-0 does **not** close this. Needs its own decision: either
      `min_horizon` for the closing-derived block moves to `T_10M`/`HT`, or the aux merge respects
      `FEATURE_HORIZONS[model_horizon]`.
- [ ] [CODE] P1. **`_apply_ht_odds_pit_gate`'s default-cutoff branch is unreachable in production.** The only caller
      guards with `if ht_break_minutes:` (`odds_features_exporter.py:232`), so the `if not ht_break_minutes:` default
      `-55` branch (lines 65–83) can never run outside tests → **when HT break times are unknown, NO PIT gate is applied
      at all** and post-kickoff odds flow into HT features ungated (measured: 12,463 T-0 rows at `bm < -55`, 1,406 at
      `bm < -110`, worst −374.6 = 6.2h after kickoff / well after full time). Either call the gate unconditionally
      (letting it apply its documented default) or delete the dead branch.

## Progress Log — 2026-07-16 (lookahead-leak fix leg)

**SHIPPED: MDPS@3bf56ff** — the ordering bug is fixed and regression-tested; the blast radius is measured by **full
census, not sampling**.

**The fix.** Post-kickoff rows are now REJECTED, not bucketed. The scalar `assign_horizon_bucket` was the worse of the
two — it `return N_BUCKETS - 1`'d on `bm < 0` **before even computing** the staleness diff. Both paths now agree
row-for-row (test-enforced). Direct push under the dirty-deps carve-out (precedent `instruments-service@a771e3e2`):
quickmerge pre-flight blocked solely by **LIVE foreign WIP** in `unified-api-contracts` (`sports/progressive.py`,
`soccer_football_info/schemas.py`, `_sports_contracts.py` — mtime <30s, another agent's `h1_*`/HT-capture leg, i.e.
loose-end #4 of this doc). Those files were not staged or touched.

**RE-MEASURED, did not inherit — and the inherited number was wrong.** Per the standing lesson (4 audits in a row got
this class wrong), the 65% figure was re-derived rather than carried: it rested on 6 sampled files / 282 rows. **Full
census of all 11,373 captured T-0 shards (zero misses, zero read failures)**: **368,366 rows, 146,738 post-kickoff =
39.83%** — not 65%. The 65% survives only as a _fixture_-level statistic (17,899/27,465 fixtures = 65.2% have ≥1
contaminated T-0 row), which is what the small sample was accidentally measuring. Worst row is **−374.6 min**,
materially worse than the −71.1 previously reported. Band split of the 146,738: **134,275 (36.45%)** in `[-55, 0)`
(HT-break window — would PASS the default HT PIT gate); **12,463 (3.38%)** at `bm < -55` (2nd half / post-match — would
be REJECTED); **1,406 (0.38%)** at `bm < -110`.

**Falsified "T-0 only" instead of assuming it.** Censused all 7 other timeframes — **0 post-kickoff rows in 4,151,352
rows / 97,631 shards**, and every timeframe's extreme value sits exactly inside its own staleness cap (T-10m 5.0 = 10−5,
T-1h 50 = 60−10, T-2h 105, T-4h 220, T-6h 330.2, T-12h 675, T-24h 1380 = 1440−60). The caps always worked; the override
breached **only** T-0. Recompute scope is therefore **T-0 alone** — a 1/8 slice of the ladder, not the whole thing.

**Does it reach features/ML? YES — by two distinct paths, and the second is the bigger finding.** (1) The features
**`HT` model horizon is fed by the MDPS T-0 bucket** via `_find_best_snapshot` fallback (verified by executing the real
code) — so the HT horizon was living off the bug, and the fix silently degrades it to pre-match prices mislabelled `HT`
(conservative, but wrong → P0 todo). (2) **The CLV/closing block leaks into the pre-match models**:
`compute_clv_features` defines closing as `horizon_name == "T-0"`, and `_compute_aux_features` merges those columns into
**every** horizon's rows; **all 27** closing-derived columns survive `apply_horizon_gate` at **T-24h (27/27)**. So the
contaminated "closing line" reached `clv_*` / `odds_movement_*` / `velocity_*_1h_to_0` on **pre-match T-24h/T-1h/T-10m
rows** for 65.2% of fixtures. Features recompute scope: **1,275 `ODDS_FEATURES` + 15,415 `DERIVED_FEATURES` shards over
1,316 dates** (`FIXTURE_FEATURES` are not odds-derived → excluded). **Not recomputed here — sports is FROZEN
mid-cutover; filed as the P0 recompute todo above.**

**Correction to this doc's own §3 framing.** "There is no HT horizon, so a post-kickoff row in T-0 is pure lookahead
into a pre-match feature" is **half right**. It is true of MDPS (`TIER1_HORIZONS` = 8 pre-match buckets) and **false of
features-service**, which has a specified HT model boundary where post-kickoff odds are _correct_ PIT data. The rows
were never the defect — the **container** was. This is exactly why §5's B-REFINED verdict (recover in-play rows into a
**distinct population quarantined from the pre-match bucketing path**) is the right call, and MDPS@3bf56ff implements
its first half: T-0 is now genuinely pre-match-only. The second half — giving the in-play population a home the HT
horizon can read — remains open above. Zero deletions; zero manifest/index writes; scratch data removed.
