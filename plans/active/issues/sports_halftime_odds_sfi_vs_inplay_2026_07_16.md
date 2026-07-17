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
- [~] [DATA] P0. **PARTIALLY DONE 2026-07-16 — MDPS T-0 leg COMPLETE (146,738 → 0, verified); features leg BLOCKED (see
  § "T-0 recompute executed" below).** The MDPS canonical T-0 lineage is clean: 146,738 post-kickoff rows removed,
  full-census verified 0 remaining, zero collateral loss. The `ODDS_FEATURES` recompute is **NOT run** — the prescribed
  `--force` re-derive is DESTRUCTIVE against the current corpus (upstream is thinner than its own descendants: measured
  13 fixtures → 1 on day=2024-01-01). Needs the per-date guard in the sub-todo below. Original scope text retained:
  **RECOMPUTE the canonical T-0 lineage + its features descendants (sports is FROZEN — do NOT run this until the cutover
  completes).** Measured scope, full census, zero misses: - **MDPS canonical**: `data_type=odds_horizon_bucket`,
  `timeframe=T-0` — **11,373 shards / 368,366 rows** (2020-06-06→2026-06-19, 38 leagues). **146,738 rows (39.83%) are
  post-kickoff** and disappear on re-derive; **7,101/11,373 shards (62.4%)** carry ≥1. Affects **17,899/27,465 fixtures
  (65.2%)** across **1,316/1,795 days**. The other 7 timeframes are **PROVEN CLEAN — 0/4,151,352 rows** post-kickoff
  across 97,631 shards (each timeframe's worst value sits exactly inside its own cap: T-10m 5.0, T-1h 50, T-2h 105, T-4h
  220, T-6h 330.2, T-12h 675, T-24h 1380) → **recompute scope is T-0 ONLY**, not the whole ladder. -
  **features-service**: on those 1,316 dates — **1,275 `ODDS_FEATURES` + 15,415 `DERIVED_FEATURES` shards** (the 559-col
  matrix) must re-derive. `FIXTURE_FEATURES` (26,942 shards) are not odds-derived → out of scope. - **RECOMPUTE DELTA
  (2026-07-16, closing-line-leak leg — features-service@bf6fc2f4).** The horizon-gate fix **widens the ODDS_FEATURES
  scope from 1,275 to the FULL 1,812-shard census** and changes the _reason_. The T-0 ordering bug only touched the
  **1,316 dates** that actually had post-kickoff rows; the closing-line leak is **unconditional — it affects every date
  that has any T-0 bucket at all**, because the aux merge broadcast the closing line into the pre-match rows regardless
  of whether T-0 was clean. Full census (single walk,
  `gs://features-sports-prd-central-element-323112/sports_features/by_date/**`): **1,812 `ODDS_FEATURES` shards over
  2020-06-07→2026-06-20** carry the leak — **+537 shards beyond the ordering-bug scope**. Measured on a 91-date
  evenly-spaced sample: **1,365/1,914 T-24h rows (71.32%)** carry ≥1 non-NULL closing-derived column, across **78/91
  dates (85.7%)**; the residual 28.7% are fixtures with no T-0 bucket (honest absence), not clean rows.
  `DERIVED_FEATURES` (15,415 shards) are **NOT** widened — they carry no odds columns (`derived_features_exporter` runs
  no odds calculator), so their recompute stays driven by the T-0 ordering fix alone. **Contaminated column set is also
  wider than the 27**: + **22 tier** columns
  (`sharp_consensus_*`/`soft_consensus_*`/`exchange_price_*`/`sharp_soft_delta_*`/`*_disagreement_*`/
  `bookmaker_count_*`) and + **38 prob-space** columns — all pooled over every horizon incl T-0 (`bookmaker_count_total`
  = **164** in a T-24h row vs **21** genuine T-24h quotes). Recompute must therefore re-derive ODDS_FEATURES on **all
  1,812 shards**, not the 1,275 subset. Still **NOT recomputed here — sports is FROZEN mid-cutover.**
- [x] [CODE] P0. **DONE — features-service@c57cc753** (2026-07-16): HT now emits **honest absence** rather than
      pre-match prices mislabelled `horizon="HT"`. `_find_best_snapshot` gained `EXACT_SNAPSHOT_HORIZONS = {"HT"}`: HT
      requires a snapshot captured AT the horizon and returns `None` (logging a typed reason) instead of falling back
      down `FEATURE_HORIZONS["HT"]` to the pre-match T-0 bucket. The slot stays declared in
      `MODEL_HORIZONS`/`FEATURE_HORIZONS`, so the OR-5b(c) B-REFINED in-play population (or the odds-api in-play capture
      leg) populates it with **no contract change**. Ruling applied: honest absence over a mislabelled row
      (`codex/02-data/honest-absence-downstream-handling.md`). **Verified on real data, not just unit tests**: the claim
      that HT is fed by the bug is CONFIRMED — shipped HT rows on day=2020-06-07 sit at `minutes_to_kickoff = -18.2`
      (post-kickoff, i.e. the leak), and on day=2020-06-09 HT resolved to a **T-10m** price (+10.0) — already
      mislabelled TODAY, before any fix. Evidence: 4 new regression tests (`TestHTHorizonHonestAbsence`) + a live batch
      run logging `Horizon HT: no snapshot captured at this horizon —     emitting nothing (honest absence)`; QG green
      (17,611 passed, 209 skipped). Original finding text retained: **The features `HT` model horizon loses its odds
      source when the leak is fixed — it is fed BY the bug.** `MODEL_HORIZONS = ["T-24h","T-1h","T-10m","HT"]` and
      `FEATURE_HORIZONS["HT"]` ends `[…, "T-0", "HT"]`; MDPS never emits `horizon_name="HT"`, so `_find_best_snapshot`
      falls back to the **MDPS T-0 bucket** (verified by running the real code). T-0 was the only bucket carrying `bm<0`
      **because the bug put them there** — so the HT horizon was silently living off the leak. Post-fix,
      `_find_best_snapshot` still returns T-0, now pre-match-only → **HT feature rows become kickoff prices mislabelled
      `horizon="HT"`** (conservative — no lookahead — but semantically wrong). Correct fix = point the HT horizon at the
      **quarantined in-play population** from OR-5b(c) B-REFINED, or drop the HT odds horizon until that population
      exists. **This invalidates the "there is no HT horizon" framing in §3 of this doc — true of MDPS's
      `TIER1_HORIZONS`, FALSE of features-service, which has a real, specified HT model boundary**
      (`features_service/sports/docs/specs/halftime_data_architecture.md`: predict the 2nd half at half-time from actual
      HT scores + progressive stats). At that boundary post-kickoff odds are **correct PIT data, not leakage** — the
      defect was always the CONTAINER (a pre-match bucket), never the rows themselves.
- [x] [CODE] P0. **BIG FINDING (new, independent of the ordering bug) — the horizon gate does not gate the
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
      `FEATURE_HORIZONS[model_horizon]`. — **DONE — features-service@bf6fc2f4 + ml-service@c0603cb** (2026-07-16).
      **VERIFIED, not inherited** (the standing 4-audits lesson). Both proposed remedies were evaluated; **both were
      needed, and neither was sufficient alone** — see § "Closing-line leak — verification, classification, fix" below.
      Headline: leak **CONFIRMED** (71.32% of T-24h rows carried non-NULL closing-derived values; `clv_home` identical
      across all 4 horizons for **1365/1365** fixtures); the blast radius is **BIGGER than the 27** (tier + prob-space
      were pooled over all 8 horizons incl T-0); and **a shipped model is invalidated**
      (`CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417164033`, val_accuracy **0.9936**, `clv_home` gain **494x** the next
      feature). Recompute delta added to the P0 recompute todo above — **no duplicate filed**.
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

## Progress Log — 2026-07-16 (SFI `h1_*` capture-gap leg)

**LOOSE ENDS #2/#3/#4 CLOSED IN CODE: the SFI first-half capture gap is fixed, `ht_odds_*_implied` now populates in
BATCH, and the live mislabel is gone.** Shipped: **uac@96cdfc4f** · **instruments-service@1f7c51cf** ·
**features-service@5a8684ed** (all three verified `merge-base --is-ancestor origin/live-defi-rollout`; QG `--no-fix`
green per repo, features-service 17,569 passed).

**TWO CLAIMS IN THIS DOC WERE WRONG — re-measured at the payload layer, per the never-inherit-a-classification rule:**

1. **The API does NOT serve `h1_*`.** §4 cited `SFMatchProgressiveOddsRaw.h1_home_win / h1_draw / h1_away_win`
   (`soccer_football_info/schemas.py:551`) as evidence of the provider contract. That model **mirrors the legacy
   `sf_match_progressive_odds` BULK-DUMP TABLE**, not the RapidAPI response — the same trap as OR-5b's `updated`-vs-
   `generation`: a plausible field list read as ground truth. Measured against the **live API** 2026-07-16
   (`GET /matches/view/progressive/`), the real keys are nested on the `odds` object and spelled differently again:
   **`1h_result` (1/X/2) · `1h_asian_handicap` (1/2/v) · `1h_goalline` (o/u/v) · `1h_asian_corner` (o/u/v)**. Note
   `goalline`, not `over_under`. A **third** spelling (`h1_odds_1/x/2`) exists in `migrate_local_sfi_to_canonical.py`'s
   dump mapping — **three inconsistent shapes in-repo, none of them the API's.** `SFMatchProgressiveOddsRaw` now carries
   a warning naming the adapter as the authority on the real payload.
2. **The HT-RESULT market is NOT "captured nowhere" for want of a provider** — it is served, richly. Measured on **8
   fixtures / 2022→2026 / 4 leagues**: all four `1h_*` markets populate **~90-97% of a fixture's snapshots** (e.g.
   200/212). We simply never read them. Re-fetchable exactly as §4 concluded — but the gap was **ours**, not SFI's.

**THE DECISIVE NEW FINDING — `1h_result` SETTLES at halftime, so "half-time odds" cannot mean "odds AT half-time".**
Measured per fixture, pre-HT vs post-HT distinct home prices: **11-26 distinct (live forecast) → 1-2 distinct
(frozen)**. Once the half ends the quote freezes at a degenerate settled price that **encodes the realised HT
scoreline** (a 1-1 first half pins the draw at ~1.055; one fixture sat at `{15.0, 1.055, 15.0}` unchanged from t=46:00
to t=90:00). **Sampling `1h_result` at or after the break would leak the very result the feature predicts.** The genuine
half-time-odds signal is therefore the **last quote strictly BEFORE halftime starts** — which is what shipped. This
independently re-justifies `_apply_ht_odds_pit_gate`: that gate was right all along.

### What shipped

- **uac@96cdfc4f** — `CanonicalProgressiveStats` +12 `odds_h1_*` fields; `SPORTS_SFI_PROGRESSIVE_STATS` +12 ColumnSpecs
  carrying the PIT semantics on the contract itself; `SFMatchProgressiveOddsRaw` docstring corrected.
- **instruments-service@1f7c51cf** — `_extract_odds()` reads all four `1h_*` markets (null **and** the `"-"` string
  sentinel → `None`, never a fabricated price). **Proven on a real payload**: h1 captured 200/212 rows, and
  `odds_h1_result_home != odds_1x2_home` on **192/192** rows — the first-half price is genuinely distinct from the
  full-time 1X2, not a copy of it.
- **features-service@5a8684ed** — `sfi_progressive_calculator` +3 features (`ht_odds_{home,draw,away}_implied`) gated on
  the already-derived `ht_start`. **Proven end-to-end in BATCH** on real fixture `27d6186eeb9c24aa` (Brazil Serie A,
  2026-05-10): `ht_odds_home_implied = 0.900` from the last pre-HT quote (1.111), implied-prob sum **1.069** (6.9%
  overround — a sane book, i.e. these are real traded prices), and **≠** the settled 15.0. Loose end #3 fixed: the live
  orchestrator no longer relabels a full-time price as first-half — it now **prefers an explicitly first-half
  container** and only maps a generic `home/draw/away` spelling inside a container that _declares_ itself first-half.

### Bonus finding, fixed in the same commits — the stoppage-time timer bug

`_parse_timer_to_seconds` only understood `"MM:SS"`. SFI also emits **`"MM:SS+MM:SS"` for stoppage time** — **31/212
rows (15%)** on a real fixture — which fell through to `return 0`, **collapsing every stoppage snapshot onto the genuine
`00:00` pre-kickoff row**. That is the run-up to the halftime whistle: the most PIT-valuable window for first-half odds,
silently zeroed. Now parsed (`45:00+02:30` → 2850); unparseable → `None` and the row is dropped rather than fabricating
a `0` that masquerades as pre-kickoff. Measured on a real payload: `timer_seconds==0` rows **32 → 1**. A **second copy**
of the same buggy parser in `uac/external/soccer_football_info/normalize.py` was fixed too.

### Backfill — scoped, not run

Correctly OUT OF SCOPE while sports is frozen. Scoped as `- [ ]` todos on `plans/epics/sports_master.md` § "Half-time
odds (SFI `1h_*`)": **2020-01-01→present × 33 SFI-mapped leagues ≈ 115,000 fixtures**, **$0 marginal API spend**
(RapidAPI Ultra is flat-rate) ≈ **1.1 quota-days / ~10.6 h single-stream**, one SPOT VM. The volume is from a **10-day
mixed weekend+midweek+off-season sample** (mean 47.9 fixtures/day, min 0, max 125); a **weekend-only sample reads
100.2/day and would have overstated by 2.1×** — the same sampling-bias class this issue's own lesson warns about.

### Still open (logged as todos, not silently dropped)

Loose end **#1** (T-0 65% post-kickoff — owned by the stale-reinjection issue + the MDPS leg above; untouched here) ·
**#5** (contract dtype drift / `ht_end_timer` 100% NULL) · **#6** (the full-time SFI odds columns still have no consumer
— and the three non-`1h_result` first-half markets now join them: captured + contract-declared but unread, P3 todo).
HT-detection accuracy is a new P2 todo: `_detect_halftime` returned 40:00 vs a real HT of ~45:00+ on the verification
fixture, so the quote is sampled ~5 min early — the **safe** direction (strictly less information, no leakage), and a
pre-existing property of `_detect_halftime` rather than of the odds gate.

**The OR-5b(c) B-REFINED verdict is unaffected**: this closes the re-fetchable HT-RESULT gap, but the ~23,000
per-bookmaker PIT-valid HT-break quotes in the legacy bucket remain non-reproducible from SFI and still ride the
option-D recovery. Zero deletions; zero manifest/index writes; scratch data removed.

---

## Closing-line leak — verification, classification, fix (2026-07-16)

> **Shipped**: features-service@bf6fc2f4 · ml-service@c0603cb. **Sports stayed FROZEN** — code only, no recompute, no
> scheduler/consolidator resumed.

### 1. Empirical verification — the leak is REAL (re-measured, not inherited)

Read real canonical parquets from `gs://features-sports-prd-central-element-323112/sports_features/by_date/` (91-date
evenly-spaced sample of the 1,812-shard census, 2020-06-07→2026-06-20):

| measurement                                                    | result                       |
| -------------------------------------------------------------- | ---------------------------- |
| T-24h rows carrying ≥1 non-NULL closing-derived column         | **1,365 / 1,914 (71.32%)**   |
| dates affected                                                 | **78 / 91 (85.7%)**          |
| fixtures where `clv_home` is IDENTICAL across all 4 horizons   | **1,365 / 1,365 (100%)**     |
| per-snapshot control (`odds_home_win`, `home_implied_prob`, …) | 199 / 7,784 identical (2.6%) |

The 100%-vs-2.6% split is the proof: the aux frames are **fixture-level and broadcast** into every horizon row, while
the genuine per-snapshot features vary per horizon. A T-24h row literally carried `clv_home = 0.065217`, the same value
as its own HT row.

**The leak is WIDER than the reported 27.** `compute_tier_features(bucketed)` and
`compute_prob_space_features(bucketed)` were handed the **whole** bucketed frame (all 8 horizons incl. T-0) and grouped
by `fixture_id`, so the T-24h row's "consensus" pooled closing quotes. Proven by recomputing both ways against the
shipped value:

|                              | shipped T-24h value matches |                  |
| ---------------------------- | --------------------------- | ---------------- |
| all-horizon-pooled recompute | **13 / 13**                 | ← what shipped   |
| T-24h-only recompute         | **0 / 13**                  | ← what is honest |

`bookmaker_count_total` = **164** in a T-24h row (all 8 horizons' quotes) vs **21** genuine T-24h quotes.

### 2. Per-column classification — 27 columns, three classes

Earliest horizon at which each column is honestly knowable. **`opening_*` is NOT gated** — it is the OPENING line, i.e.
past information at T-24h; gating it would destroy real signal.

| #     | column(s)                      | earliest honest horizon | evidence (calculator)                                                           |
| ----- | ------------------------------ | ----------------------- | ------------------------------------------------------------------------------- |
| 1-3   | `opening_home/draw/away_odds`  | **T-24h** (unchanged)   | `compute_opening_odds` — median at the EARLIEST horizon rank per fixture        |
| 4-6   | `odds_movement_home/draw/away` | **HT**                  | `compute_opening_odds` — `closing(T-0) / opening - 1`                           |
| 7-9   | `clv_home/draw/away`           | **HT**                  | `compute_clv_features` — `close/open - 1`; returns empty without a T-0 leg      |
| 10-12 | `sharp_clv_home/draw/away`     | **HT**                  | `compute_clv_features` — same ratio on the Pinnacle leg                         |
| 13-15 | `clv_direction_home/draw/away` | **HT**                  | `compute_clv_features` — `(clv > 0).astype(int)`                                |
| 16-17 | `velocity_home/away_1h_to_0`   | **HT**                  | exporter `velocity_pairs` — the `("T-1h", "T-0")` leg                           |
| 18-19 | `velocity_home/away_24h_to_6h` | **T-1h**                | window ENDS at T-6h; `FEATURE_HORIZONS["T-24h"] == ["T-24h"]` only              |
| 20-21 | `velocity_home/away_6h_to_1h`  | **T-1h**                | window ends at T-1h                                                             |
| 22-23 | `acceleration_home/away`       | **T-1h**                | `v(6h→1h) − v(24h→6h)`; T-0 fallback removed (was unreachable, latent leak)     |
| 24-25 | `steam_detected_home/away`     | **T-1h**                | `_compute_steam_features` — Pinnacle move **T-24h → T-1h**, NOT closing-derived |
| 26-27 | `steam_magnitude_home/away`    | **T-1h**                | same                                                                            |

**Totals: 3 legitimately-T-24h (kept) · 14 closing-only → HT · 10 window-dependent → T-1h.** "HT" is correct (not FT):
it is the first `FEATURE_HORIZONS` bucket containing `T-0`, so at HT the closing line is legitimate PIT data.

**Corrections to the reported finding** (both re-measured): (a) `steam_*` is **not** closing-derived — it is a
T-24h→T-1h Pinnacle move, so gating it to HT would have destroyed real pre-match signal; (b) `opening_*` is legitimately
T-24h-knowable and must stay.

**Additional (outside the 27):** `velocity_*_1h_to_10m` was emitted and written to the parquet but **absent from
`ODDS_COLUMNS`** → no `FeatureExpectation` → **never gated at any horizon** (an unregistered column is invisible to
`apply_horizon_gate`). Registered at **T-10m**.

### 3. The fix — both remedies were needed; neither sufficed alone

- **Input scoping** (`_restrict_to_visible_horizons`, exporter): aux features are recomputed **per model horizon** from
  only `FEATURE_HORIZONS[model_horizon]`. Fixes the **values**, and is the only remedy that works for tier/prob-space —
  those are honest signal once scoped, so gating them out would have destroyed them.
- **`min_horizon` registry** (`_COLUMN_HORIZON_OVERRIDES`): fixes the **declared contract** that `apply_horizon_gate` /
  `validate_pit_compliance` / the ml-service sidecar all consume. Without it the PIT validator could never catch a
  regression.
- **ml-service alias strip**: the shield stripped only literal `clv_*`, but `odds_movement_* == clv_*` **exactly on
  5,329/5,329 real rows** and `clv_direction_* == sign(clv_*)` on 5,329/5,329 — aliases, not correlates.

**Runtime verification on REAL production data** (day=2024-01-01, 2,114 bucketed rows across 8 horizons):

| column                  | T-24h before     | T-24h after             | HT after |
| ----------------------- | ---------------- | ----------------------- | -------- |
| `clv_home`              | 13/13            | **0/13**                | 13/13    |
| `odds_movement_home`    | 13/13            | **0/13**                | 13/13    |
| `velocity_home_1h_to_0` | 13/13            | **0/13**                | 13/13    |
| `opening_home_odds`     | 2.3              | **2.3 kept**            | —        |
| `sharp_consensus_home`  | 2.33625 (pooled) | **2.36 (honest T-24h)** | —        |
| `bookmaker_count_total` | 164 (pooled)     | **21 (genuine)**        | —        |

Real-shield reproduction with the real (stale) sidecar: closing-derived columns surviving at T-24h went **11/14 → 0/14**
for both `target='clv'` and `target='home_win'`.

### 4. 🔴 A TRAINED MODEL IS INVALIDATED — operator-level finding

**`CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417164033`** (`gs://ml-models-store-prd-central-element-323112/models/…`,
trained 2026-04-17, target `clv`, timeframe `fixture` — mislabelled `CEFI_UNKNOWN`, it is a **sports** model):

- `val_accuracy` **0.9936**, `average_precision` **0.9998**, `f1_macro` 0.9924 on a 3-class CLV-direction target.
- Loading `model.joblib`: **`clv_home` is a FEATURE**, with gain **72,585.95 — 494x** the next feature (147.60).
- **The model predicts CLV from CLV.** Its backtest is meaningless. A 99.4% accurate T-24h forecast of closing-line
  direction is not a result; it is the leak.

Sibling artifacts in the same registry: `…V20260417154715` (val_accuracy **1.0**, degenerate — single class in test) and
`…V20260417201036` (0.6411, majority-class-only). **All three CLV models are invalid** and must not be promoted or
cited. No sports model is in `live_*`; nothing was traded on this. **Recommend: delete/quarantine all three + their
`model_registry/manifest.json` entries, and re-train only after the recompute.**

**This was NOT merely historical.** With today's code the shield strips `clv_home`, but `odds_movement_home` (its exact
alias) was declared T-24h and unstripped — so the **next** training run would have leaked identically via the alias.
ml-service@c0603cb closes that path for the existing corpus; features-service@bf6fc2f4 closes it at the source for
future exports.

### 5. What is NOT closed by this leg

- The **1,812-shard recompute** (P0 todo above) — sports is FROZEN. Until it runs, every `ODDS_FEATURES` shard on disk
  and **every `horizon_schema.json` sidecar** still carries the pre-fix registry. ml-service@c0603cb is the interim
  guard: it strips the aliases regardless of what the sidecar claims.
- The **HT-horizon odds source** P0 todo above is now _more_ urgent: post-fix, `clv_*` at HT is computed from a T-0
  bucket that `_find_best_snapshot` still resolves — correct PIT, but the HT container question stands.

---

## T-0 recompute EXECUTED — the leak is gone; the features leg is BLOCKED (2026-07-16)

> **Shipped**: features-service@c57cc753 (HT honest absence) · market-data-processing-service@e2ec8ce (stale-shard
> reconcile). **Sports stayed FROZEN** — all three sports consolidators (`features-sports`, `market-data-sports`,
> `instruments-sports`) and every sports scheduler verified PAUSED before and after; **nothing was resumed**.

### 1. Scope RE-VERIFIED independently (the standing 4-audits lesson) — every number confirmed

Full census, zero read failures, single walk (`gcloud storage ls -r` cached locally, reused for every check):

| claim                                          | doc     | measured    | verdict         |
| ---------------------------------------------- | ------- | ----------- | --------------- |
| canonical T-0 shards                           | 11,373  | **11,373**  | ✅              |
| T-0 rows                                       | 368,366 | **368,366** | ✅              |
| T-0 post-kickoff rows                          | 146,738 | **146,738** | ✅ (39.83%)     |
| T-0 shards carrying ≥1                         | 7,101   | **7,101**   | ✅              |
| worst `bm_minutes_to_kickoff`                  | −374.6  | **−374.6**  | ✅              |
| other 7 timeframes post-kickoff                | 0       | **0**       | ✅ of 4,151,352 |
| `ODDS_FEATURES` shards (FULL scope, not 1,275) | 1,812   | **1,812**   | ✅ 1,812 days   |
| affected days                                  | 1,316   | **1,316**   | ✅              |

**Two corrections to the doc's own numbers** (immaterial to scope, but the record should be right):

- The "97,631 shards" for the other 7 timeframes is a transcription slip — the real count is **101,631**. The ROW census
  (4,151,352) matches exactly, so the original census did cover all of them; only the shard tally was mistyped.
- `DERIVED_FEATURES` exclusion **verified before acting on it**, at BOTH levels: `derived_features_exporter` imports no
  odds calculator and never calls `read_bucketed_odds` (code), and 0/40 sampled shards carry any odds-family column
  (data). Correctly excluded.

### 2. 🔴 BIG FINDING — the prescribed `--force` re-derive is DESTRUCTIVE. Each layer is RICHER than its own upstream.

**The recompute mechanism in the todo above cannot be run as written.** Discovered by piloting one day, measured, then
fully reverted from GCS soft-delete (verified byte-exact).

`reprocess_sports_odds.py --force` re-derives a day from **today's canonical raw**. That raw no longer contains what the
existing corpus was built from:

| day        | canonical raw rows | legacy raw rows | ratio     |
| ---------- | ------------------ | --------------- | --------- |
| 2022-04-16 | **5,626**          | **79,773**      | **14.2×** |
| 2025-04-12 | 168,653            | —               | intact    |
| 2024-11-09 | 147,110            | —               | intact    |

A pre-flight harness (read-only: runs the real adapter, compares to the corpus per horizon) gives the verdict per day:

- **2022-04-16 → UNSAFE**: re-derive yields T-24h only; would destroy **4,741 legitimate pre-match rows**
  (T-10m/T-12h/T-1h/T-2h/T-4h/T-6h all → 0).
- **2025-04-12 / 2024-11-09 → SAFE**: every non-T-0 horizon reproduces **delta 0** (exact), T-0 drops precisely the
  post-kickoff rows (+18/+12 extra valid rows the richer raw supports).

**The old corpus is NOT itself mis-bucketed** — falsified rather than assumed: every non-T-0 shard on 2022-04-16 is
**100% inside its own staleness cap** (T-10m bm 5.6–14.9, T-12h 706.7–744.1, T-6h 343.4–380.4, …). Only T-0 was bad (21%
valid). So the multi-horizon data is real, and a blind re-derive really would have destroyed it.

**Same pathology one layer down**: `odds_features` is richer than the MDPS bucketed layer it derives from.
day=2024-01-01 holds **13 fixtures** in `odds_features` while MDPS bucketed holds **1**. Blast radius measured on a
31-date evenly-spaced sample: **4/31 dates (13%)** would LOSE fixtures on recompute (18 fixtures total) — bounded, not
universal, but non-zero. **This is why the features recompute was NOT run.**

> **Consequence for the cutover lane**: the sports lineage cannot currently rebuild itself at ANY layer. Until the
> legacy→canonical raw recovery (OR-5b(b) option-D G1 read-split-merge) lands, every `--force` re-derive is a data-loss
> event. Filed: `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`.

### 3. What was actually done — a surgical filter, not a re-derive

MDPS@3bf56ff changes **only** the `bm<0` branch (post-kickoff → reject); rows with `bm>=0` are byte-identical
(test-enforced). So removing `bm<0` rows from the existing T-0 shards **is exactly what the fixed code emits from the
same inputs** — with zero dependency on raw completeness. This is the least-bad path: it fulfils the intent (remove the
leak) without the mechanism's destructiveness.

**Result — verified by a FRESH full census, not by re-reading my own output:**

| metric                    | before  | after       |
| ------------------------- | ------- | ----------- |
| canonical T-0 shards      | 11,373  | **8,937**   |
| canonical T-0 rows        | 368,366 | **221,628** |
| **T-0 post-kickoff rows** | 146,738 | **0** ✅    |
| worst `bm`                | −374.6  | **0.0**     |

Both deltas are exact: 11,373 − 2,436 = 8,937; 368,366 − 146,738 = 221,628. 4,665 shards rewritten in place, 2,436
emptied shards deleted (honest absence — the fixed writer emits no group for them).

**Blast radius contained, measured:** total bucketed objects 222,316 → 219,880 (delta **2,436** = exactly the emptied
T-0 shards). Non-T-0 canonical **unchanged at 101,631**. The legacy (no-`pipeline_mode=`) layout **untouched at
109,312** — it is fully shadowed (all 1,813 legacy days have a canonical counterpart, and the features reader probes
canonical first and only falls back when canonical is empty for that day).

### 4. Writer gap found + fixed — MDPS@e2ec8ce

`_write_bucketed_output` was **overwrite-only**: it uploads the (league, horizon) groups present in the NEW frame and
never removes shards the derive no longer produces. So a shard whose rows all become invalid keeps its **stale parquet
on disk**, and readers (which list the date prefix and concatenate) keep consuming it. Measured: **2,436 of the 11,373**
T-0 shards go fully empty under the fix — a naive `--force` recompute would have left **43,119 leaked rows (29.4%)**
live, and the "146,738 → 0" assertion would silently have failed at 43,119. Now reconciled via `_delete_stale_shards`
(canonical prefix only; never the legacy layout; never on a degenerate/empty derive), + 5 regression tests.

### 5. Model quarantine — DONE (nothing deleted)

All 3 CLV models flagged unusable, **artifacts retained**, verified read-back (manifest still parses, 15 other models
untouched). Leak re-confirmed independently before acting: `target_type='clv'` **and** `clv_home` present in
`feature_names` — it predicts CLV from CLV. Metrics re-measured: **0.9936** (V20260417164033), **1.0** (…154715,
degenerate), **0.6411** (…201036).

Flags written (additive keys — `quarantined` / `usable:false` / `promotion_blocked:true` / `quarantine_reason`) to
`model_registry/manifest.json` (entry + every version), each `model_registry/metadata/<id>/…/metadata.json`, and a
`QUARANTINED.json` marker beside each `model.joblib`.

### 6. ML-readiness — BEFORE captured; AFTER not meaningful yet

`verify_ml_readiness.py --start-date 2020-06-07 --end-date 2026-06-20` (full corpus), BEFORE: **2,205 dates checked ·
1,021 passed · 791 failed · 393 missing · avg non-NULL 94.0% · gate NO**. (1,021+791 = 1,812 = the odds_features census
— consistent.) **AFTER is deliberately not reported**: the gate measures `odds_features`, which was NOT recomputed, so
it would be unchanged by construction. Reporting it as an "after" would be a false signal.

## Todos (opened 2026-07-16 by the T-0 recompute leg)

- [x] [DATA] P0. ✅ **Recompute `ODDS_FEATURES` behind a PER-DATE loss guard — DONE 2026-07-17.** Guard shipped
      **features-service@3c15f3ff** (`data/loss_guard.py` pure core + `cli/handlers/_loss_guard_gate.py` wiring, 15 unit
      tests); recompute EXECUTED over the **full re-verified census of 1,861 dates** (not 1,812 — see § below), 4-way
      parallel through the production CLI: **1,524 written · 337 guard-ABORTED (18.1%) · 0 failures (rc=0 on
      1,861/1,861)**. Two-sided verification on the 1,524 written dates, full census (not sampled): `clv_home` **21,922
      → 0** · `odds_movement_home` 21,922 → 0 · `sharp_clv_home` 18,508 → 0 · `clv_direction_home` 21,922 → 0 ·
      `velocity_home_1h_to_0` 19,969 → 0; **`opening_home_odds` SURVIVED 31,539 → 31,545** (not over-gated) ·
      **`steam_detected_home`@T-1h SURVIVED 26,904 → 26,904 unchanged**, gated out at T-24h 26,359 → 0 (its
      `min_horizon` is T-1h) · `bookmaker_count_total`@T-24h pooled-signature dates **1,364 → 0**, median-of-max **145 →
      19** (the predicted ~21 genuine count) · HT rows **1,467 → 0** dates (honest absence). **Zero non-HT fixture
      losses** on written dates; the 134 net fixture-slot drop is entirely HT-only fixtures vanishing with HT. Residual
      leak is a **strict subset of the 337 aborted dates** (`clv_home` dirty-after = 329, `subset_of_blocked=True`, **0
      on written dates**) and all 337 aborted shards are **byte-intact** (row counts unchanged). ML-readiness re-run:
      see § "ODDS_FEATURES recompute EXECUTED" below — **1,021 → 177 passed / 94.0% → 80.0%, a CORRECT drop** (removing
      fabricated signal), gate NO both sides. The `MANIFEST_CONSOLIDATED_STALENESS_SEC` concern did not materialise —
      sports was RESTORED live 2026-07-17 (consolidators `*/1`), so the startup gate passed unmodified.
- [~] [DATA] P0. ✅ **MECHANISM DIAGNOSED + FIXED 2026-07-17 — `market-data-processing-service@9f2560b7`. The recompute
  half is SPLIT OUT into its own todo below (deliberately NOT run in this leg).** The blank-`fixture_id` collapse is
  fixed at the adapter: identity is now COALESCED (blank == absent) into an authoritative `fixture_id` before anything
  keys on it, an unresolvable identity fails LOUD (`MalformedTickFieldError` → `attempted_failed`, never a silent
  collapse or a false `empty_confirmed`), and `odds_loss_guard` now **sources** `resolve_fixture_ids` from the adapter
  instead of carrying a second copy — so guard and derive cannot drift on what a fixture IS. **11 new regression tests**
  (`TestFixtureIdentityResolution`, incl. the pinned `2024-01-15` 1→5-fixture case); QG green (**2040 passed**, 1
  skipped; sentinel == HEAD). Evidence + the two inherited numbers this leg **falsified**: see § "Fixture-identity
  collapse — FIXED" below. Headline: **448** dates carry the signature (**not** the 337 — that was the features-side
  symptom), **423** change on re-derive, **94.8%** of the derive was being destroyed on them (60,517 → 1,173,798 rows),
  **adds-only PROVEN** (0/1,934 dates lose an observation), and the (b) guard now **passes** the exact date it blocked
  pre-fix (`2023-01-08`, 514 → 514, was 514 → 61). Original scope text retained: They are the ONLY dates still carrying
  the closing-line leak. They are **not scattered — 49 contiguous windows with a hard WINTER signature**:
  `2021-01-01..2021-02-20` (49d) · `2022-01-01..2022-03-05` (60d) · `2022-12-23..2023-02-27` (61d) ·
  `2024-01-01..2024-02-02` (31d) · `2024-02-09..2024-02-23` (14d) · `2025-02-02..2025-02-15` (14d), by year 2021:49 ·
  2022:147 · 2023:78 · 2024:45 · 2025:17 · 2026:1. On those dates the corpus holds **10,642 fixtures** and the re-derive
  reaches only **9,842** → the guard protected **800 fixtures** from deletion. Note the era overlaps the 199-day
  `batch_footystats` merge window (`market-tick-data-service@75f226e8`, 2022:112 · 2023:48 · 2024:34) — so that merge
  fixed a _neighbouring_ slice but NOT these; a second, distinct starvation mechanism is live and unidentified. This is
  exactly the "nothing yet proves they cannot starve by another [mechanism]" caveat in
  `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`. Do NOT lower the guard to force these
  through — fix the upstream, then re-run `drive.sh`-equivalent on the 337. > **🟢 MECHANISM IDENTIFIED 2026-07-17 (by
  the fix-(b) leg) — FIXED 2026-07-17 `market-data-processing-service@9f2560b7`.** > **An empty-but-present `fixture_id`
  column silently collapses the MDPS adapter's dedup key.** > `pivot_mtds_to_wide` renames `event_id`→`fixture_id` ONLY
  when `fixture_id` is absent. On the affected dates the > raw carries BOTH — `event_id` populated and `fixture_id`
  present but **blank on 100% of rows** — so no rename > fires, and `_get_dedup_columns` then returns
  `['fixture_id', 'bookmaker_key']`. Dedup therefore runs on > `('', bookmaker_key, horizon_idx)` and **keeps ONE row
  per (bookmaker, horizon) for the whole league-day**, > destroying every other fixture. > **Measured live**
  (`market-data-processing-service/.venv`, real reads + real adapter, zero inherited numbers): > `day=2024-01-15` raw
  holds **5 distinct `event_id`** across 3,759 rows with `fixture_id` non-empty on **0/3,759**; > the adapter derives
  **166 rows / ~21 per horizon** = ~21 bookmakers × **1** collapsed fixture (vs ~5×21×8 ≈ 840 > expected — **~80%
  destroyed**). Every probed shard on such a date has `event_id` nunique == **1**. Contrast > `day=2022-04-16`, where
  raw has `event_id` only → rename fires → **68 fixtures** preserved / 5,635 rows / grid >
  `T-12h=896 · T-6h=898 · T-4h=896 · T-2h=884 · T-10m=870 · T-24h=894` (matches the corpus EXACTLY). > **Corpus
  generation split** (the diagnostic signature — grep it to enumerate the affected dates): > `fixture_id` populated + no
  `event_id` column = HEALTHY; `event_id` populated + blank `fixture_id` = COLLAPSED. > Probed collapsed: `2024-01-15`,
  `2025-02-05` — **both inside the 337 winter windows**. Probed healthy: > `2022-04-16`, `2023-05-10`, `2024-11-09`,
  `2025-04-12` — all outside. > **Why the features guard fired**: the MDPS corpus on these dates is ALREADY collapsed
  (the bug bit at original > derive time), so `odds_features` (13 fixtures) is richer than the MDPS upstream it reads
  (1) — exactly the > "richer than its own upstream" reading, but caused HERE, not by raw truncation. > **Fix
  direction**: make the fixture identity resolution explicit rather than rename-dependent — coalesce >
  `event_id`/`fixture_id` treating blank as absent (fix-(b)'s `_resolve_fixture_ids` in >
  `app/adapters/sports/odds_loss_guard.py` is a working reference), and make `_get_dedup_columns` refuse a dedup > key
  whose every value is blank rather than silently collapsing. ~~**NOT fixed here**~~ — **FIXED 2026-07-17,
  MDPS@9f2560b7** (both prescribed changes landed; the resolver is now SHARED with the guard rather than duplicated). >
  The fix-(b) guard > does NOT protect these dates: old and new both collapse identically, so the derive looks faithful
  — **still true, and still the reason the fix had to come from the derive side.** > _Provenance: fix-(b) leg
  2026-07-17, `market-data-processing-service@6d20fb18`; fix + blast radius 2026-07-17,
  `market-data-processing-service@9f2560b7`._
- [ ] [DATA] P0. **RECOMPUTE the 423 collapse-affected dates through MDPS, then re-run `ODDS_FEATURES` on them.** Split
      out of the todo above (the fix — MDPS@9f2560b7 — is that todo's deliverable; this is the DATA leg it unblocks).
      **It now runs GUARDED**: the (b) loss guard (`market-data-processing-service@6d20fb18`) is unmodified and
      demonstrably passes the post-fix derive (`2023-01-08` 514 → 514; census `2023-01-05..20` **16/16 pass, 0
      blocked**, where pre-fix it blocked **15/16**), so a `--force` over these dates can only add. Do NOT lower the
      guard; a block on any date = STOP-and-diagnose (a THIRD starvation mechanism), not a nuisance. **Scope (measured,
      full census — `~/tmp-collapse/blast_radius.jsonl` methodology, real reader + real adapter):** - **MDPS
      `odds_horizon_bucket`**: **423 dates** whose derive changes (of 448 signature dates; the other 25 are
      single-fixture days where the collapse is a no-op). Range **2020-06-06 … 2026-06-20**; by year 2020:78 · 2021:50 ·
      2022:60 · 2023:52 · 2024:51 · 2025:47 · 2026:110. Expected write: **60,517 → 1,173,798 rows** (+1,113,281
      observations; ~2,800 rows/date avg). **Cost**: measured 27.0s for 16 dates at `--workers 4` dry-run (≈1.7s/date
      derive+guard); with real per-shard uploads (~71 shards/date) budget **~1-2 h** for all 423 at `--workers 4`.
      Command: `reprocess_sports_odds.py --start-date <D> --end-date <D> --force --workers 4` (resumable per date;
      verify each date logs `LOSS_GUARD_PASS`). - **features-service**: re-run `ODDS_FEATURES` (+ `DERIVED_FEATURES`) on
      the **423 dates** AFTER the MDPS leg lands — they read the bucketed layer, so they must not be recomputed against
      the collapsed upstream. This also clears the **337 guard-aborted dates**' residual closing-line leak (the 337 ⊂
      the collapse-affected era), which is the last 18.1% of the leak purge. Feature-side guard =
      `features-service@3c15f3ff` (fixture-SET containment). - **Sequencing**: MDPS first → verify → features. **Sports
      must not be mid-freeze/cutover when this runs**; confirm the bucket cutover's state before starting (this issue's
      own banner + the cutover runbook).
- [ ] [DATA] P1. **The blank-`fixture_id` raw generation is STILL BEING WRITTEN — fix the upstream writer.** The
      collapse signature reaches the **corpus edge** (last collapsed date **2026-06-20**; 2026-04: 28 dates · 2026-05:
      28 · 2026-06: 8 — only **9** healthy dates in all of 2026), so the current ODDS_API capture path emits
      `fixture_id=""` alongside a populated `event_id`. MDPS@9f2560b7 makes the DERIVE immune (identity is coalesced),
      so this is no longer data-destroying — but the raw is still carrying a blank column that means "absent", which is
      the exact trap that cost this corpus ~1.1M observations. Either populate `fixture_id` at write time or drop the
      column rather than writing it blank (a blank-but-present column is a placeholder that looks populated —
      `codex/02-data/honest-absence-downstream-handling.md`). Owner: MTDS (the ODDS_API writer). Measured by the
      2026-07-17 blast-radius census (2,221 dates, 0 gaps).
- [ ] [DATA] P1. **Re-calibrate the `verify_ml_readiness.py` 95% non-NULL threshold against the HONEST matrix.** The
      gate now fails 1,683/1,860 dates at ~69-80% non-NULL — **not a regression**: the threshold was calibrated when the
      closing line was broadcast into every T-24h row, i.e. against a leaking matrix, so 95% was only ever reachable
      _because_ of the leak. Post-purge, a T-24h row legitimately carries NULL for every closing-derived column
      (`clv_*`/`odds_movement_*`/`velocity_*_1h_to_0`/`steam_*`, ~27+ columns), so the gate is now structurally
      unmeetable at 95% and measures the wrong thing. Re-base it per-horizon on the columns each horizon can honestly
      know (`FEATURE_HORIZONS[h]` / the `min_horizon` registry) rather than on a flat cell-count. **Deliberately NOT
      tuned in this leg** — lowering a number to make a gate green is the anti-pattern.
- [ ] [DATA] P1. **Reconcile the market-data-sports manifest for the 2,436 deleted T-0 shards.** They still read as
      `captured` in the availability index; they should be `empty_confirmed` (honest absence). NOT done here: the
      operator scoped this session's manifest work to the FEATURES surface only, and the market-data-sports consolidator
      is owned by the in-flight bucket cutover (its unmerged shard `_index/per_vm/cutover-move-20260716.parquet` must
      not be merged by anyone else).
- [ ] [ML] P2. **Retrain the CLV models after the ODDS_FEATURES recompute.** The 3 quarantined artifacts stay in place
      as the reference for what the leak produced. Do not promote or cite them.

---

## ODDS_FEATURES recompute EXECUTED — the leak is purged on 1,524/1,861 dates (2026-07-17)

> **Shipped**: features-service@3c15f3ff (the per-date loss guard). **No code change to the exporter** — the leak fixes
> (@bf6fc2f4 / @c57cc753) were already live and correct; this leg is the DATA purge they were waiting on.

### 1. Scope RE-VERIFIED — the doc's own number was stale by +49

Single cached walk of `gs://features-sports-prd-central-element-323112/sports_features/by_date/**` (248,813 objects):

| claim                            | doc (2026-07-16)      | measured 2026-07-17                       | verdict                  |
| -------------------------------- | --------------------- | ----------------------------------------- | ------------------------ |
| `ODDS_FEATURES` shards           | 1,812                 | **1,861**                                 | ⚠️ +49 — explained below |
| date range                       | 2020-06-07→2026-06-20 | **2020-06-06→2026-06-20**                 | ⚠️ +1 day earlier        |
| layout                           | day-level             | **day-level (1,861/1,861; 0 per-league)** | ✅                       |
| `DERIVED_FEATURES` odds-derived? | no                    | **no** — re-confirmed                     | ✅ correctly excluded    |

**The +49 is real and benign.** A **10-VM parallel gap-fill campaign** (`fss-backfill-vm-1..10`, launched 02:18Z
2026-07-17 by another lane, `--skip-existing`, ranges spanning 2015-01-01→2026-07-17) filled **49 previously-MISSING
odds_features dates** while this leg was starting. Independently cross-checked: `verify_ml_readiness` missing went **393
→ 345 = 48**, +1 for `2020-06-06` (outside the doc's start) = **49** ✅. Those 49 were written by the FIXED code and are
already clean (probed `day=2020-10-02` / `2020-09-30`: `clv_*` 0 at every horizon, no HT, `opening_*` present, `steam_*`
at T-1h only). **`--skip-existing` means that campaign never touched the 1,812 leaked shards — the `--force` purge below
is exactly the piece it could not do.** No collision: the only two VMs still alive (vm-3 `2017-04-22.. 2018-06-16`, vm-4
`2018-06-17..2019-08-11`) sit entirely **before** odds_features exists (2020-06-06).

`DERIVED_FEATURES` / `FIXTURE_FEATURES` full-corpus counts are **42,965 / 72,347** — the doc's 15,415 / 26,942 were the
_affected-dates subset_, not the corpus; not a contradiction.

### 2. The guard (fix (c)) — features-service@3c15f3ff

Pure decision core `features_service/sports/data/loss_guard.py` (`evaluate_loss_guard`, no I/O) + wiring
`cli/handlers/_loss_guard_gate.py`, called in `_run_feature_group` **after** the emission policy and **before** any
write reaches GCS. **Fixture-SET containment per horizon**, not row-count: the grain is one row per (fixture × horizon),
so the HT honest-absence drop legitimately removes rows on every date — a row-count guard would abort 100% of dates on a
correct fix. Horizons in `EXACT_SNAPSHOT_HORIZONS` (today: `HT`) are exempt, **sourced from the exporter** so the
exemption dissolves by itself when a genuine in-play population lands. Fails **CLOSED**: an unreadable existing shard
blocks the write. Also guards the **empty-derive → `record_empty`** path, which would otherwise stamp `empty_confirmed`
on a date whose shard still holds fixtures (a manifest that contradicts the data).

15 unit tests (`tests/sports/unit/test_loss_guard.py`) pin both sides — including the measured `day=2024-01-01`
52-rows→3 regression, the HT-only-fixture justified drop, a same-count fixture SWAP (which a count-based guard would
wave through), and an int-vs-str id dtype mismatch (which would otherwise fabricate total loss and abort every date). QG
green: **17,632 passed, 209 skipped**.

**Proven in the real production path before the run**: `--date 2024-01-01 --tables odds_features --force` →
`LOSS_GUARD_BLOCKED ... fixtures 13 -> 1 ... Date SKIPPED; existing shard left intact`, and the shard's GCS update time
stayed `2026-07-16T19:10:29Z` (untouched).

### 3. The run — 1,861 dates, 4-way parallel, resumable

`1,524 written · 337 guard-ABORTED (18.1%) · 0 failed`; **rc=0 on 1,861/1,861**. Every date appends one JSON verdict
line, so the run resumes losslessly from any kill.

### 4. Two-sided verification — FULL census, not sampled

Measured over all 1,861 shards before and after (`census_before/after.jsonl`), restricted to the 1,524 **written**
dates:

| column                          | T-24h before                               | T-24h after                               | verdict                             |
| ------------------------------- | ------------------------------------------ | ----------------------------------------- | ----------------------------------- |
| `clv_home`                      | 21,922                                     | **0**                                     | ✅ purged                           |
| `odds_movement_home`            | 21,922                                     | **0**                                     | ✅ purged (identical count = alias) |
| `sharp_clv_home`                | 18,508                                     | **0**                                     | ✅ purged                           |
| `clv_direction_home`            | 21,922                                     | **0**                                     | ✅ purged                           |
| `velocity_home_1h_to_0`         | 19,969                                     | **0**                                     | ✅ purged                           |
| **`opening_home_odds`**         | 31,539                                     | **31,545**                                | ✅ **SURVIVED** — not over-gated    |
| **`steam_detected_home` @T-1h** | 26,904                                     | **26,904**                                | ✅ **SURVIVED** — unchanged         |
| `steam_detected_home` @T-24h    | 26,359                                     | **0**                                     | ✅ gated (`min_horizon` = T-1h)     |
| `bookmaker_count_total` @T-24h  | pooled 1,364 dates / median-of-max **145** | **0 dates** pooled / median-of-max **19** | ✅ genuine count (predicted ~21)    |
| HT rows                         | 1,467 dates                                | **0**                                     | ✅ honest absence                   |

- **Residual leak lives ONLY on the aborted dates**: `clv_home` dirty-after = 329 dates, `subset_of_blocked = True`, **0
  leaked cells on any written date** (all five markers).
- **Zero non-HT fixture losses** across 1,524 written dates. Net fixture-slot delta −134 = HT-only fixtures vanishing
  with the HT horizon (the justified class the guard's own test pins).
- **All 337 aborted shards intact** — row counts identical before/after.

### 5. ML-readiness — the number DROPPED, and that is the correct result

`verify_ml_readiness.py --start-date 2020-06-07 --end-date 2026-06-20`:

| metric        | BEFORE (doc, 2026-07-16) | AFTER (measured 2026-07-17) |
| ------------- | ------------------------ | --------------------------- |
| dates checked | 2,205                    | 2,205                       |
| passed        | **1,021**                | **177**                     |
| failed        | 791                      | 1,683                       |
| missing       | 393                      | 345                         |
| avg non-NULL  | **94.0%**                | **80.0%**                   |
| gate met      | NO                       | NO                          |

**This is the leak leaving, not a regression.** Failures read `non-NULL at target horizons 77.0% < 95%` — i.e. the T-24h
rows now honestly carry NULL where the closing line used to be broadcast in. Internally consistent: before 1,021+791 =
**1,812** = the doc's census; after 177+1,683 = **1,860** = my 1,861 minus `2020-06-06` (outside the range); missing
393→345 = the 48 in-range gap-fill dates. **Nothing was tuned to improve this number** — the 95% threshold was
calibrated against a leaking matrix and is now structurally unmeetable; re-basing it is filed as a P1 todo above.

### 6. Honest limits of this leg

- **337 dates (18.1%) still carry the leak** — the guard refused to purge them because doing so would delete 800
  fixtures. They are 49 contiguous winter-clustered windows: a second, distinct upstream starvation mechanism that the
  `batch_footystats` merge did not address. P0 todo above.
- ~~**Fix (b) — the `reprocess_sports_odds.py` (MDPS) guard — remains OPEN**~~ → **CLOSED 2026-07-17,
  `market-data-processing-service@6d20fb18`** (tracked in
  `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`). This leg shipped fix **(c)** (the features
  guard); the MDPS side is now guarded too — observation-SET containment per horizon at the (fixture × bookmaker) grain,
  T-0 exemption sourced from `POST_KICKOFF_CONTAMINATED_HORIZONS`, fails closed. Proven live: a real `--force` on
  `day=2023-01-08` blocked (514 → 61 observations), shards byte-identical; 15/16 dates blocked across 2023-01-05..20.
  **Anyone running the MDPS tool historically is now protected.** That leg also IDENTIFIED the second starvation
  mechanism behind this doc's 337 aborted dates — see the P0 todo above (empty `fixture_id` collapses the dedup key).
- **`fss-backfill-vm-3` died without its EXIT trap firing** (SPOT preemption): its `EXIT_STATUS` still reads `RUNNING`
  while the instance is gone, so its chunk `2017-04-22..2018-06-16` is silently incomplete. Not this leg's lane —
  flagged for the campaign owner.

---

## Fixture-identity collapse — FIXED (2026-07-17)

> **Shipped**: `market-data-processing-service@9f2560b7` (verified `merge-base --is-ancestor origin/live-defi-rollout`).
> QG `--no-fix` green — **2040 passed / 1 skipped**, sentinel `.qg_last_passed_sha` == HEAD (verified by CONTENT, not
> exit code). **Zero mutations to the corpus**: every measurement below is a read or a `--dry-run`; the recompute is
> deliberately NOT run (scoped as its own P0 todo above).

### 1. REPRODUCED first — the report was not taken on trust

Real reader (`reprocess_sports_odds._read_raw_odds`) + real adapter
(`SportsBucketAssignmentAdapter.process_to_bucketed_df`), never a re-implementation. The signature is exactly as
diagnosed, on 2/2 collapsed and 4/4 healthy dates:

| day            | raw rows | `event_id`        | `fixture_id`         | signature | derive (pre-fix)          |
| -------------- | -------- | ----------------- | -------------------- | --------- | ------------------------- |
| **2024-01-15** | 3,759    | 5 distinct, 100%  | present, **0/3,759** | COLLAPSED | **166 rows / 1 phantom**  |
| **2025-02-05** | 3,246    | 4 distinct, 100%  | present, **0/3,246** | COLLAPSED | **181 rows / 1 phantom**  |
| 2022-04-16     | 83,916   | 68 distinct, 100% | **ABSENT**           | HEALTHY   | 5,635 rows / 68 fixtures  |
| 2023-05-10     | 10,199   | 11 distinct, 100% | **ABSENT**           | HEALTHY   | 1,515 rows / 11 fixtures  |
| 2024-11-09     | 147,110  | 91 distinct, 100% | **ABSENT**           | HEALTHY   | 14,077 rows / 91 fixtures |
| 2025-04-12     | 168,653  | 97 distinct, 100% | **ABSENT**           | HEALTHY   | 14,255 rows / 97 fixtures |

`fixture_id` on the collapsed generation is **literally the empty string** (`object` dtype, `nunique=1`, value `''`) —
not NaN, not whitespace. That is why `"fixture_id" not in df.columns` never fired.

### 2. Two inherited numbers CORRECTED (re-measured, per the standing never-inherit rule)

1. **"~840 expected / ~80% destroyed" on `2024-01-15` was an ESTIMATE** (`5 × 21 × 8`). Measured post-fix: the derive
   yields **746 rows**, not ~840 — not every (fixture × bookmaker × horizon) cell exists (staleness caps + missing
   snapshots). The real destruction on that date is **166/746 = 77.7% destroyed**. Corpus-wide the figure is **worse**
   than the doc's ~80%: **94.8%**.
2. **"337 dates" is the FEATURES-side symptom, not the MDPS blast radius.** Measured directly on MDPS: **448 dates**
   carry the collapsed signature and **423** change on re-derive. The two sets overlap but are not the same population
   (the 337 were winter-clustered; the 448 span **every year 2020→2026** and are heaviest in **2026: 110**).

### 3. THE FIX

`bucket_assignment_adapter.py` — identity is resolved EXPLICITLY, never inferred from a column's presence:

- `FIXTURE_ID_COL_CANDIDATES = ("event_id", "fixture_id")` + `resolve_fixture_ids()` — coalesce, **blank == ABSENT**,
  values normalised to `str`. This is the (b) guard's `_resolve_fixture_ids`, **moved to the adapter** (the authority on
  its own dedup grain) rather than copied — `odds_loss_guard` now imports it, so the two **cannot** disagree about what
  an entity is. Same sourcing pattern as `POST_KICKOFF_CONTAMINATED_HORIZONS`. A regression test pins the identity
  (`odds_loss_guard.resolve_fixture_ids is resolve_fixture_ids`).
- `_materialise_fixture_identity()` runs in `pivot_mtds_to_wide` **and** `_prepare_tick_data` (the already-wide path
  skips the pivot and previously reached dedup with a blank key). Idempotent; drops the redundant `event_id` so both raw
  generations converge on ONE output shape. Column POSITION is preserved (rename-then-overwrite when `fixture_id` is
  absent), so healthy dates keep a byte-identical shape.
- **Fails LOUD, never collapses**: identity unresolvable on every row → `MalformedTickFieldError` (→ `attempted_failed`,
  a diagnosable source-format problem — never a false `empty_confirmed`). Partial → the unkeyable rows are dropped with
  a loud `logger.warning` (they would otherwise merge into one phantom fixture). **Measured: 0/1,934 dates hit either
  path** — the real corpus always resolves.
- `_get_dedup_columns` **refuses** an all-blank `fixture_id` (raises) rather than dropping the column — dropping it
  would silently fall back to `(bookmaker, horizon)`, i.e. the identical collapse by another route.

### 4. BLAST RADIUS — full corpus, both adapters run for real

The **real pre-fix adapter** (loaded from `git show HEAD:…`) and the **real post-fix adapter** were run over **every
date 2020-06-01 … 2026-06-30 — 2,221 dates, zero gaps**, comparing observation SETS per horizon on the shared resolver.
(283 dates have no raw; 4 dates — `2026-06-21..24` — raise the reader's own pre-existing `RawOddsShapeUnrecognizedError`
(meta-snapshot-only blobs), unrelated to this fix.)

| measure                           | value                                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| dates with raw data               | **1,934**                                                                                         |
| COLLAPSED signature               | **448** (23.2%)                                                                                   |
| derive CHANGES                    | **423** (all 423 are collapsed-signature)                                                         |
| collapsed-signature but NO change | 25 — **all single-fixture days** (collapse is a no-op there: exactly what the mechanism predicts) |
| HEALTHY (`event_id` only)         | 1,486 — **0 changed**                                                                             |
| rows on collapsed dates           | **60,517 → 1,173,798** (**94.8% was destroyed**)                                                  |
| observations gained               | **+1,113,281**                                                                                    |

**ADDS-ONLY — PROVEN, not argued:**

| assertion                         | measured      |
| --------------------------------- | ------------- |
| dates losing ≥1 observation       | **0** / 1,934 |
| dates where `new_rows < old_rows` | **0** / 1,934 |
| dates losing ≥1 fixture           | **0** / 1,934 |
| healthy dates changed at all      | **0** / 1,486 |

### 5. The (b) guard PASSES the post-fix re-derive — on the date it blocked

The strongest available proof: the (b) leg recorded `LOSS_GUARD_BLOCKED day=2023-01-08 … observations 514 -> 61` (2,019
lost). Post-fix, through the **real production CLI** (`--force --dry-run`, guard runs identically in dry-run):

```
LOSS_GUARD_PASS 2023-01-08 [no_loss] — Every retained horizon reproduces its observations (514 -> 514); justified drops: none.
  2023-01-08: 48915 rows → 3734 bucketed (8 horizons, 18 bookmakers)
```

And the (b) leg's own 16-date census `2023-01-05..20`, which blocked **15/16** pre-fix, is now **16/16 PASS, 0 blocked**
— observations only ever rise or hold:
`72→83 · 141→160 · 84→179 · 102→117 · 514→514 · 86→168 · 18→18 · 440→440 · 111→119 · 46→48 · 149→282 · 568→621 · 45→48 · 118→148 · 986→991 · 196→217`.
The two dates the (b) leg cited to justify set-vs-count containment (`2023-01-17` 46→47 losing 40; `2023-01-19` 45→45
losing 4) now read `no_loss`.

### 6. 🔴 NOTIFY-OPERATOR — the collapse is LIVE, not historical

The signature reaches the **corpus edge**: **2026-04: 28 dates · 2026-05: 28 · 2026-06: 8**, last collapsed date
**2026-06-20**, against only **9** healthy dates in all of 2026. `2026-05-17` derived **184 rows where the raw supports
16,938** (98.9% destroyed). So the ODDS_API writer is **still emitting a blank `fixture_id`**, and every recent derive —
including anything the rolling `mdps_odds_horizon_scheduler` recon window touched while sports was live — collapsed the
day to ~one fixture per bookmaker. MDPS@9f2560b7 makes the derive immune from now on; the **writer** is a separate P1
todo above. **This also means the recompute is not purely historical clean-up — it is repairing live data.**
