---
title: Manifest scaling — range index for instrument×timeframe coverage
id: manifest_scaling_range_index_2026_05
status: parked — pre-activation audit in progress (2026-05-06)
created: 2026-04-30
owner: harsh
audience: backend engineers, data platform engineers
parent_reference:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/data-catalogue-schema.md
  - codex/14-playbooks/cross-cutting/catalogue-data.md
sibling_plans:
  - plans/active/instrument_catalogue_availability_matrix_2026_04_29.plan.md
  - plans/active/instrument_schema_cohesion_and_market_hours_2026_03_31.plan.md
  - plans/active/data_catalogue_cleanup_2026_04_24.plan.md
  - plans/active/combo_bundle_aggregation_2026_04_30.plan.md
  - plans/active/defi_e2e_pipeline_2026_04_30.plan.md
  - price_chart_gcs_delivery_2026_04_29.plan.md
hard_prerequisite_plan: plans/active/shard_granularity_ssot_propagation_2026_05_06.plan.md
prior_audit: plans/ai/audit_instruments_gcs_2026_04_25.md
---

## Status banner (2026-05-06)

This plan is **parked**, not abandoned. Two pieces of pre-work are running before any v7 schema code is written:

1. **Pre-activation measurement** — confirm whether any of the four activation triggers
   (manifest > 50 MB, cold-read p99 > 3 s, chart p99 > 2 s, ~100 concurrent users) is firing today. Without a fired
   trigger, range-index code is premature optimization.
2. **Open-question resolution** — Q1 (DEFI Layer 1 path), Q2 (sports range-fit), Q5b (TRADFI `instrument_type` bug),
   Q5c (`available_from_datetime` semantics). These block the JSON sample from being faithful and the schema from
   being committable.

**Hard prerequisite** for moving from parked → active: the shard-granularity propagation plan
(`plans/active/shard_granularity_ssot_propagation_2026_05_06.plan.md`) must reach Phase 2 done. Reason: collapsing
v6 rows into v7 ranges only works if v6 is honest. Today's v6 has confirmed lies (MDPS 1440 NaN-bar phantoms passed
as `captured`; MTDS DeFi drops `instrument_id`; instruments-service Polymarket overloads `data_type`). Collapsing
those into `(covered_from, covered_to, gap_dates)` would bake the lies into the v7 schema and make them
unauditable inside multi-year ranges.

**Pre-activation audit roadmap** (this plan, this branch — `live-defi-rollout`, no separate feature branch):

- [ ] [AUDIT] A1. Capture current manifest read p99 baseline via `scripts/bench_candle_reads.py`
      (add "manifest read p99" scenario if missing). Owner: harsh. Output: number, written into Section
      "Activation triggers — current measurements" below.
- [ ] [AUDIT] A2. Measure today's `_index/availability_index.parquet` size per bucket
      (instruments-store-{ag}, market-data-tick-{ag}, mdps output). Output: table in Section "Activation triggers".
- [ ] [AUDIT] A3. Resolve Q1 — DEFI Layer 1 on-disk path (read 1-2 sample
      `gs://instruments-store-defi-{pid}/...` parquets, decide canonical surface). Update Q1 with the answer.
- [ ] [AUDIT] A4. Resolve Q2 — SPORTS Layer 1 fixtures schema (read sample
      `sports_reference/by_date/day=*/entity=fixtures/fixtures.parquet`). Decide whether range model applies or
      sports gets its own catalogue plan.
- [ ] [AUDIT] A5. Resolve Q5b — TRADFI cash-equity `instrument_type='SPOT_PAIR'` and `holiday_calendar='NASDAQ'`
      vs codex-spec `EQUITY` and `XNYS`. Determine intentional vs bug. If bug, this plan blocks on
      `instrument_schema_cohesion_and_market_hours_2026_03_31` fixing it.
- [ ] [AUDIT] A6. Resolve Q5c — confirm `available_from_datetime` = listing date and `available_to_datetime` =
      expiry/null on a real options + spot/perp sample.
- [ ] [AUDIT] A7. Cross-reference shard-granularity Phase 1 fix list. Identify which fixes affect range-index
      `gap_dates` correctness (e.g. MIG-MDPS2 1440-NaN-bar fix changes which days are "honest empty" vs "real
      gap"). Document the dependency edges so the plan unparks at the right moment.
- [ ] [AUDIT] A8. Append each finding to "## Audit findings (pre-activation)" below as the audit progresses.
      Commit each finding to `live-defi-rollout` immediately (per workspace feedback rule).

Phase 0 (this audit) is **read-only** — no code, no schema changes, no manifest writes. Sole deliverable: data + Q&A
that lets harsh decide whether to (a) move plan to `active` and start Unit B, (b) keep parked but with a sharper
re-measurement trigger, or (c) supersede with a different design (e.g. two-tier sharded index from the rejected
alternatives appendix) if measurements suggest it.

## Activation triggers — current measurements

_Filled in by audit items A1, A2 below. Empty until measured._

| Trigger                                    | Threshold       | Today's value                                                  | Status                |
| ------------------------------------------ | --------------- | -------------------------------------------------------------- | --------------------- |
| Largest **canonical** `availability_index.parquet` | > 50 MB         | **30.2 MiB** (`market-data-tick-cefi`, 2026-05-06)             | NOT FIRED (60% of)    |
| Largest **per-VM shard** in any `_index/per_vm/` | > 50 MB         | **3.65 MB** (`market-data-tick-defi/per_vm/local-10889-bd08`)  | NOT FIRED             |
| Total `_index/` footprint per bucket       | (advisory)      | up to **163 MiB** (sports-instruments, mostly weather backfill VMs) | advisory; consolidator should compact |
| `read_availability_index` p99 cold cache   | > 3 s           | TBD (A1)                                                       | TBD                   |
| Chart-route p99 (manifest-read portion)    | > 2 s           | TBD (A1)                                                       | TBD                   |
| Concurrent chart users                     | ~100            | TBD (operations data)                                          | TBD                   |

## Audit findings (pre-activation)

_Findings appended per audit item as they complete. Each entry: date, item ID, what was checked, what was found,
what it means for this plan._

### 2026-05-06 — A2: index parquet sizes per bucket (read-only GCS scan)

**What was checked:** all 10 canonical buckets (5 asset_groups × `instruments-store` + `market-data-tick`) at
`gs://{kind}-{ag}-central-element-323112/_index/`. For each, captured size of the canonical
`availability_index.parquet` and the largest per-VM shard, plus the total `_index/` footprint.

**Canonical `availability_index.parquet` sizes (2026-05-06):**

| Bucket                                    | Canonical index size |
| ----------------------------------------- | -------------------- |
| `market-data-tick-cefi`                   | **30.2 MiB**         |
| `instruments-store-sports`                | **18.8 MiB**         |
| `market-data-tick-defi`                   | **3.6 MiB**          |
| `market-data-tick-tradfi`                 | **2.2 MiB**          |
| `market-data-tick-sports`                 | **2.1 MiB**          |
| `instruments-store-defi`                  | **1.1 MiB**          |
| `instruments-store-cefi`                  | **0.6 MiB**          |
| `instruments-store-tradfi`                | **0.5 MiB**          |
| `market-data-tick-prediction`             | **0.2 MiB**          |
| `instruments-store-prediction`            | **0.09 MiB**         |

(`instruments-store-tradfi` has no `BucketKind.MARKET_DATA` entry per UAC SSOT — TRADFI uses Databento managed
storage; not relevant here.)

**Verdict against Trigger 1 (> 50 MB):** **NOT FIRED.** Largest canonical index is 30.2 MiB on `market-data-tick-cefi`,
~60% of threshold. Sports-instruments at 18.8 MiB is the second-largest and is plausibly inflated by
weather-backfill per-VM shards (4 weather VMs alone wrote 0.5–0.7 MB each into `_index/per_vm/`); after the
consolidator merges + dedup, the canonical would shrink.

**However**: the `market-data-tick-cefi` bucket is at 30 MiB **today**, with backfill ongoing. Two of the active
backfills will inflate it materially:
1. Deribit options backfill (2020–2025) — `_index/per_vm/opt-deribit-{year}.parquet` shards already total
   ~199 KB summing 2020–2025; once consolidated into the canonical and as more option chains land, this is the
   biggest single growth driver.
2. CeFi spot/perp full backfill (mdps-cefi-2024/2025/2026 per-VM shards visible) — per-instrument-per-day
   v6 row shape × ~7 timeframes × ~4 data_types × ~3000 cefi instruments × multi-year = the dominant row source.

**Implication for this plan:**
- **Don't unpark yet.** Trigger 1 is at 60%, not over.
- **Re-measure in 2 weeks** (post-shard-granularity Phase 1 cleanup, post-Deribit-options-2024-2025 backfill
  wave). If `market-data-tick-cefi` canonical exceeds 50 MB by then, Trigger 1 has fired and this plan moves to
  active.
- **Cluster the per-VM shards.** A separate concern: per-VM shards count is high (1307 shards on
  `market-data-tick-cefi/_index/per_vm/`). Consolidator already runs but the per-VM tail is long. This is a
  Trigger-2/3 (read-latency) leading indicator regardless of canonical size — every reader that does
  `read_availability_index` after a recent write must walk per-VM shards until consolidation catches up.

**Doesn't change the Q1–Q5 schema design questions** — Trigger 1's not-fired status delays activation but doesn't
invalidate the schema work; that work proceeds independently and remains gated on the shard-granularity
prerequisite.



## Relationship to existing plans

**Most important:** this plan is an **extension** of the existing catalogue plan, not a replacement or rival. They
compose:

```
┌─ Layer (this plan changes) ─────────────────┐
│  manifest_writer.py / range_index.parquet   │
│  Per-range rows. O(1) per-instrument lookup.│
│  Hot path readable. Holiday-aware.          │
└─────────────┬───────────────────────────────┘
              │  read by
              ▼
┌─ Layer (existing catalogue plan owns) ──────┐
│  instrument-catalogue.json + .md            │
│  Tuple-keyed (asset_group × data_type ×     │
│  venue × instrument_type) coverage matrix.  │
│  Nightly cron. Operator-facing report.      │
└─────────────────────────────────────────────┘
```

Without this plan: the catalogue's coverage % calculation walks N manifest rows per tuple. At full backfill that's
O(millions) per nightly regen. With this plan: catalogue computes coverage % from a single range row's
`(covered_from, covered_to, gap_dates)` — constant work per tuple, regardless of date range.

The catalogue plan **does not need to know** this plan landed — it just queries `read_availability_index()` as before;
UTL surfaces range rows transparently after v7 ships. (Reader compat, see Unit D.)

**`instrument_catalogue_availability_matrix_2026_04_29`** (active, locked*by `live-defi-rollout`) ships a \_catalogue
artifact* — `instrument-catalogue.json` + `shard-dynamics.json` + `.md` matrix generated nightly by joining static UAC
SSOT (bucket → schema → coverage-start) with manifest aggregation (capture_status counts). That plan **reads** the
manifest as-is. It does NOT change the manifest's shape.

**This plan** restructures the manifest's _underlying shape_ — per-row → range-row — so hot-path consumers (chart route,
future backtests, real-time scanners) can do O(1) per-symbol lookups instead of O(N) pandas filters over the whole
index. It is one layer beneath the catalogue plan.

The two are complementary, not duplicates:

| Concern            | Catalogue plan                                     | This plan                                      |
| ------------------ | -------------------------------------------------- | ---------------------------------------------- |
| Audience           | Humans + AI agents reasoning about the system      | API hot path (chart, backtest engine, scanner) |
| Output             | `instrument-catalogue.{json,md}` artifact, nightly | Manifest schema v7 (range rows)                |
| Consumes manifest? | Reads, aggregates                                  | Writes, restructures                           |
| Delivery cadence   | Nightly                                            | Per-write (continuous)                         |
| Latency budget     | Minutes (operator review)                          | Sub-millisecond (chart fetch)                  |

After this plan lands the catalogue plan still works — it just derives coverage % from `(from, to, gaps)` ranges instead
of counting rows.

**`instrument_schema_cohesion_and_market_hours_2026_03_31`** (active, P0) is the calendar/market-hours prerequisite this
plan depends on. It already adds `pre_market_open_utc`, `post_market_close_utc`, `holiday_calendar`, `timezone`,
`auction_open_utc/close_utc` to `InstrumentRecord` (Phase 1E `[x]` done; Phase 2C `[ ]` populating in databento adapter
still open as P0). When that plan finishes populating those fields, this plan's "holidays vs gaps" distinction has a
clean source. Until then, this plan's blocker is simply waiting for that work to finish — no NEW calendar service plan
needed.

**`data_catalogue_cleanup_2026_04_24`** (active) is unrelated — removes dead venues (OddsJam, PredictIt, Betdaq,
Smarkets), wires combo adapters. Different scope.

---

# Manifest scaling — range index for instrument × timeframe coverage

## Problem

Today's manifest format (`_index/availability_index.parquet`) is one row per
`(date, venue, data_type, timeframe, instrument_id, ...)` — one row per shard. Works fine for our current 4 TRADFI
symbols × ~70 trading days = ~280 MDPS rows in TRADFI bucket.

At full scale this collapses:

- **Stocks** ~10K listed instruments × 252 trading days/year × 6 timeframes × 1-2 data_types ≈ **~30M rows/year**.
- **Crypto perpetuals** ~3K symbols × 365 days × 7 timeframes × 4 data_types ≈ **~30M rows/year**.
- **Options chains** sparse coverage but per-strike: 10K underlyings × 5 expiries × ~50 strikes × 252 days = **~500M
  rows** if exploded per strike, much less if grouped by underlying.
- **DeFi pools** thousands × every block-relevant timeframe.

Add 5+ years of history and the parquet hits **multi-GB**. Even at 500 MB it's painful: every chart load =
`read_availability_index` cache miss = 500 MB GET + 100 MB pandas DataFrame in RAM × N API workers. UTL's 60 s
in-process cache means up to N × 500 MB cold GETs per minute fleet-wide.

The chart route's pruning predicate is:

```python
mdps[
    (mdps["data_type"] == data_type)
    & (mdps["timeframe"] == timeframe_partition)
    & (mdps["venue"] == venue)
    & (mdps["instrument_id"] == symbol)
    & (mdps["available"] == True)
]
```

Linear pandas filter over the whole DataFrame. At 30M+ rows this is hundreds of milliseconds per chart click on the API
process.

## Proposal — range index

Replace one-row-per-shard with **one row per continuous coverage range** per
`(service, venue, instrument_id, timeframe, data_type)` tuple:

```
service, venue, instrument_id, timeframe, data_type,
  available_from   date,
  available_to     date,
  gap_dates        list[date]   -- genuine pipeline gaps only, NOT holidays
  shard_count      int
  written_at       timestamp
```

For continuously-traded AAPL 1m: instead of ~250 rows/year you get **1 row** per (NASDAQ, AAPL, 1m, ohlcv_1m) tuple with
`from=2020-01-02`, `to=today`, `gap_dates=[]`. Multi-year coverage = single row.

For an option that listed Jan 5 and expired Mar 17: 1 row, `from=2026-01-05`, `to=2026-03-17`, gaps based on actual
ingestion log not "weekends weren't backfilled."

### Index size estimate post-collapse

| Surface                            | Today's row count          | Range-index row count          |
| ---------------------------------- | -------------------------- | ------------------------------ |
| Stocks (10K × 5y × 6tf × 2dt)      | ~150M rows                 | **~120K rows** (one per tuple) |
| Crypto perps (3K × 5y × 7tf × 4dt) | ~150M rows                 | **~84K rows**                  |
| Options chains (chain-bundled)     | ~few-M rows                | **~few-K rows**                |
| DeFi pools                         | ~few-M rows                | **~few-K rows**                |
| **Total**                          | **~300M+ rows / multi-GB** | **~250K rows / few MB**        |

100×–1000× shrink. Single-row hash lookup on a few-MB index = sub-ms filter, even cold-loaded.

### Holidays vs gaps — critical distinction (from operator review)

**Holidays are NOT gaps.** A US equity having no NYSE 09:30-16:00 bar on Christmas is the venue closing, not a pipeline
failure. Marking holidays as gaps in this index would inflate gap_dates and trigger spurious "missing data" alerts.

**Source of truth for "is this a trading day for this venue?"** — comes from `instruments-service`'s `InstrumentRecord`
(which already has `is_trading_day`, `regular_open_utc`, `regular_close_utc`, `early_close_utc`) plus the in-progress
`instrument_schema_cohesion_and_market_hours_2026_03_31` plan which is adding `pre_market_open_utc`,
`post_market_close_utc`, `holiday_calendar` (e.g. `XNYS`), `timezone` (e.g. `America/New_York`), `auction_open_utc`,
`auction_close_utc`. Phase 1E of that plan is done; Phase 2C (databento adapter populates those fields per instrument)
is the open P0.

(Initial sketch of this plan said `features-calendar-service` would own the per-venue session model — wrong. The model
lives on `InstrumentRecord` per-instrument, not on a separate calendar service. The calendar service has FX-session
encoding for ML features, a different concern.)

The right separation:

1. **`instruments-service.InstrumentRecord`** owns: per-instrument trading calendar (which days are trading days),
   session timings (open/close UTC per date, with timezone + holiday_calendar lookup to derive DST-adjusted hours).
2. **manifest range index** owns: which days within those trading calendars actually got ingested.
3. **gap_dates** in this index = days that are trading days per (1) but missing per (2). Real pipeline failures only.

This plan blocks on `instrument_schema_cohesion_and_market_hours` Phase 2C reaching done. No new calendar plan needed —
the work is already scoped and active.

## Why this and not the alternatives

Six options were considered (full discussion at the end of this doc). Selected option 2 — **range index** — over:

- **BQ external table** — adds BQ dependency to the chart hot path for an index-lookup problem we can solve in parquet.
  Defer until we have multi-cluster fleet-wide read patterns.
- **Two-tier sharded index** (one file per symbol) — solves the same problem as range index but with fan-out fragility
  (millions of tiny files in `_index/by_symbol/`). Use only if range index isn't enough.
- **Bloom filters / Object tables / Postgres-Redis** — overkill for an index that should fit in memory once we collapse
  it.

Range index is the smallest delta to existing code (writer change + nightly compaction job), uses the existing parquet
path, plugs into the same `read_availability_index` reader API, and gives 100×+ shrink for the dominant case.

## Out of scope

- **Holiday calendar gap**. If features-calendar-service can't answer the two questions above, **a separate plan must
  land first** to add `(is_trading_day, session_window)` per venue with DST handling. This plan blocks on that.
- **Raw data manifest**. Same problem applies to MTDS's raw_tick_data index but raw data is out of scope for the chart
  UX. Raw-tick coverage is its own audit; resolve there separately.
- **DeFi pools have a different ranging shape** (block height, not date). Range index works but the range key changes
  from `(from_date, to_date)` to `(from_block, to_block)` for DeFi rows. Land for TRADFI/CEFI first, extend to DEFI in a
  follow-up.

## Hybrid catalogue thought

The operator review surfaced an important framing: this is **the combination of instruments and market data**.

- `instruments-service` already publishes the canonical instrument catalogue
  (`instruments-store-{category}-{project}/reference_data/instruments/...`) with `available_from_datetime` /
  `available_to_datetime` per instrument. That's the reference-data dimension.
- This plan's range index is the **per-data-type coverage** dimension.

Joining the two answers: **"for instrument X, what data exists between its listing date and its expiry?"** — which is
the question every chart, backtest, and feature service actually wants to ask.

The shape:

```
INSTRUMENT (from instruments-service)        COVERAGE (this plan)
  venue: NASDAQ                                 venue: NASDAQ
  instrument_id: AAPL                           instrument_id: AAPL
  available_from: 1980-12-12                    timeframe: 1m
  available_to: null (still listed)             data_type: ohlcv_1m
                                                covered_from: 2020-01-02
                                                covered_to: today
                                                gap_dates: []
```

When we extend this index, the join shape is natural — same key shape on both sides. Worth keeping in mind so the schema
doesn't drift.

## Data catalogue schema collision

`codex/02-data/data-catalogue-schema.md` defines the per-service `data-catalogue.{service}.yaml` files (one row per
dataset). That's a **dataset-level** catalogue (e.g. "instruments_cefi_binance dataset exists, last updated 2026-04-29,
retention 90d") — a different granularity from this plan's per-(instrument, timeframe) coverage. The two are
complementary; they don't replace each other:

- Data catalogue YAML = "does dataset X exist as a deployable artifact"
- Range index = "for dataset X, which (instrument, date) tuples have data"

This plan's range index sits **inside** the dataset (replacing the current `_index/availability_index.parquet`); the
data catalogue schema is unchanged.

## Measurement trigger — when to escalate from "parked" to "active"

Move this plan to `active` when ANY of the following fires:

1. `_index/availability_index.parquet` for any single bucket exceeds **50 MB** uncompressed.
2. `read_availability_index` p99 (cold cache miss) exceeds **3 s** on the API process.
3. Single chart-route request p99 (route entry → response) exceeds **2 s** in real backend, after the GCS reads
   themselves are sub-100ms (i.e. when the manifest read becomes the bottleneck, not GCS).
4. Number of concurrent users on the chart approaches **100**, even if (1)-(3) haven't fired yet — at that scale
   per-worker memory pressure becomes the issue.

Whichever triggers first.

Track via the existing benchmark (`scripts/bench_candle_reads.py`) — add a "manifest read p99" scenario when this plan
is reactivated.

## Plan units (for when activated)

### Unit A — confirm InstrumentRecord market-hours fields populated

Block: confirm `plans/active/instrument_schema_cohesion_and_market_hours_2026_03_31.plan.md` Phase 2C is done —
databento adapter populates `pre_market_open_utc`, `post_market_close_utc`, `holiday_calendar`, `timezone`,
`auction_open_utc/close_utc` per TradFi instrument. Spot-check a sample: NASDAQ:AAPL InstrumentRecord must have non-null
`holiday_calendar='XNYS'`, `timezone='America/New_York'`. If not, that plan is the blocker; this plan waits.

### Unit B — schema + writer

`AvailabilityRecord` v7 with the new range-row shape. Writer in `unified-trading-library/manifest_writer.py` emits range
rows on top of (or replacing) per-day rows. Backwards compat: reader backfills v6 rows by collapsing them into ranges on
read for the transition window.

### Unit C — daily compaction cron

`manifest-consolidator` already exists per-bucket (1-minute cron). Add a sibling `manifest-compactor` cron that runs
nightly: read the consolidated manifest, group by tuple, derive ranges, filter holidays via calendar-service, write the
v7 manifest.

### Unit D — reader migration

`read_availability_index` returns range rows. `BatchCandleReader._prune_dates_via_manifest` re-implemented as a range
lookup (single row per `(venue, symbol, tf, dt)`) instead of a date-set filter. Same return shape (set of present dates)
— but built from `(from, to, gaps)` instead of row filter.

### Unit E — backfill + cutover

Run a one-time conversion: read v6 manifest, write v7. Keep both for ~1 week, route reader to v7. Once stable, drop v6
emission.

## Open questions for reviewers

These were surfaced while drafting the illustrative JSON sample (`manifest_scaling_range_index_2026_05.SAMPLE.json`).
They need domain-owner answers before the JSON sample can be made faithful, and ultimately before this plan can move
from `parked` to `active`. Tagged by likely owner:

### Q1 — DEFI Layer 1 source [owner: instruments-service]

Today `gs://instruments-store-defi-{project}/` has no `instrument_availability/by_date/...` parquet — only
`_index/availability_index.parquet` with manifest rows keyed `(date, venue, chain, instrument_count)`. Per-instrument
`InstrumentRecord` rows for DEFI are not shipped to GCS at the same shape as CEFI/TRADFI.

**Question**: is DEFI's per-instrument record meant to land at
`instrument_availability/by_date/day=*/chain=*/venue=*/instruments.parquet` in the same shape as CEFI/TRADFI? Or is the
`_catalogue/instruments-service/...` path (visible in the bucket listing) intended to be the canonical surface?

If DEFI Layer 1 lands at a different path than CEFI/TRADFI, this plan's range-index location for DEFI must follow that
decision. Until confirmed, the JSON sample's DEFI Layer 1 rows are extrapolated from UAC schema (correct field names)
but not anchored to a real on-disk parquet today.

### Q2 — SPORTS Layer 1 schema [owner: sports / instruments-service]

`codex/02-data/per-category-bucket-layouts.md` documents that sports uses
`sports_reference/by_date/day=*/entity=*/{entity}.parquet` (entities: `fixtures`, `footystats_odds`, `sfi_leagues`,
`progressive_stats`, `teams`, `standings`, `lineups`, `injuries`, `weather`) — fundamentally different shape from
CEFI/TRADFI/PREDICTION's `instrument_availability/...` path.

**Questions**:

- Is `sports_reference/by_date/day=*/entity=fixtures/fixtures.parquet` the right canonical source for "the instrument"
  (= a fixture) at the Layer 1 layer for sports?
- What's the actual schema of that fixtures parquet? (`league_id`, `home_team`, `away_team`, `kickoff_ts` are likely;
  rest is guessed).
- Does the range-index pattern even apply to sports, given fixtures are point-in-time events not date-ranges? A fixture
  has a single `kickoff_ts` — there's no `covered_from / covered_to` in the same sense as "this stock has 1m bars from X
  to Y."

If the answer is "sports doesn't fit the range-index shape," it gets its own catalogue plan (sports-specific). The
CEFI/TRADFI/DEFI range index lands without sports.

### Q3 — Layers 2 + 3 SSOT [owner: MTDS / MDPS]

Layers 2 (raw) and 3 (processed) range indexes are entirely **proposed** by this plan — they don't exist on disk
anywhere today. Today's manifest is the per-day `_index/availability_index.parquet` with one row per shard, written by
MTDS / MDPS via `ManifestWriter`.

**Questions**:

- The compactor that derives a Layer 2/3 range index would aggregate existing per-shard manifest rows. Does that
  compactor live in MTDS / MDPS (each owns its own), or in a shared infra repo (`unified-trading-deployment-v2` or
  sibling) that runs against any bucket?
- For sports raw data (`(fixture, bookmaker, market_type)` per pre-kickoff window), is the Layer 2 row shape
  `(covered_from, covered_to, gap_intervals)` over timestamps (not dates) acceptable, or does sports want a different
  range model entirely?
- For DEFI raw data keyed by block height (not date), do we range over `(from_block, to_block)`? If yes, the schema
  differs per asset group (DEFI uses block ranges, others use date ranges).
- Should Layer 2 inherit the asset-group's Layer 1 filter columns (denormalised) or stay narrow with just
  `(venue, instrument_id, data_type)` and force a join? **Proposal in this plan**: denormalise (per the CEFI sample).
  Confirm or push back.
- Should Layer 3 likewise denormalise Layer 1 columns, plus carry `data_type` + `timeframe`? **Proposal**: yes. Confirm.

### Q4 — `bytes_total` worth keeping? [owner: data engineering]

Sample JSON includes `bytes_total` per range row. It's free at write time (compactor already lists shards to count them,
`blob.size` comes back in the same metadata response). Storage cost is a single int64 column. Worth keeping for capacity
planning and "is this shard suspiciously sized" checks?

**Default if no answer**: keep it. Easy to drop later if unused.

### Q5b — TRADFI cash-equity instrument_type [owner: instruments-service]

Sampling real data 2026-04-30:
`gs://instruments-store-tradfi-{project}/instrument_availability/by_date/day=2026-04-10/venue=NASDAQ/instruments.parquet`
has AAPL with `instrument_type='SPOT_PAIR'`, not `'EQUITY'`. Same row has `asset_class='equity'` and
`holiday_calendar='NASDAQ'` (not `'XNYS'`).

**Question**: are the values `instrument_type='SPOT_PAIR'` and `holiday_calendar='NASDAQ'` for cash equities
intentional, or a backfill bug? Codex `availability-manifest-and-data-status.md` documents `EQUITY` as the expected
`instrument_type` for the TRADFI bucket, and `instrument_schema_cohesion_and_market_hours_2026_03_31` specifies
`holiday_calendar='XNYS'` (`exchange_calendars` keys).

If intentional, the range-index plan adopts `SPOT_PAIR` / `'NASDAQ'` and the codex doc needs reconciliation. If bug,
this is a blocker that the schema-cohesion plan should fix before this plan ships.

### Q5c — `available_from_datetime` semantics for options [owner: instruments-service]

DERIBIT BTC option `BTC-26JUN26-120000-C` (2026-06-26 expiry) has `available_from_datetime=2025-06-26` — the option's
**listing date**, ~12 months before expiry. `expiry` is the separate column.

**Confirm**: `available_from_datetime` = listing date, `available_to_datetime` = (expiry for dated derivatives, null for
spot/perp). This is what the catalogue-builder docs say already, but the range-index reuses these fields directly so the
semantic match matters.

### Q5 — Sports + prediction schema differences [owner: sports / prediction]

The sample JSON has sports rows shaped completely differently from CEFI (timestamp ranges instead of date ranges,
per-bookmaker keying, horizon-bucketed processed rows). Prediction has different shape again (event_id + outcome).

**Question**: should each asset group's Layer 1/2/3 range-index schema be defined per-group with no schema-cohesion
attempt across groups? **Proposal**: yes — per-group buckets imply per-group schemas, matches existing convention
(`per-category-bucket-layouts.md` documents that sports diverges).

If schemas must align across groups (for some downstream tool that queries cross-asset-group), say so — that constraint
changes the shape of every Layer's columns.

---

## Pointers

- `codex/02-data/availability-manifest-and-data-status.md` — current schema (v6, expanded by `quote_margin_combo`
  2026-04-23).
- `codex/02-data/chunk-safe-manifest-migrations.md` — pattern for large parallel manifest rewrites without races.
- `codex/02-data/per-instrument-sentinel-rollout.md` — related prior work on per-instrument tracking.
- `instruments-service/docs/instrument-catalogue.md` — reference-data catalogue this index would natural-join with.
- `features-calendar-service/docs/SCHEMA_VALIDATION.md` — current session encoding (FX-only, gap to fill).
- `unified-trading-pm/reports/price_chart_gcs_benchmark_*.md` — current manifest read latency baseline; rerun when this
  plan activates to measure the win.

---

## Appendix — rejected alternatives

For the record, the six options considered:

1. **BQ external table over the manifest** — query the parquet via BigQuery with auto-cached results. Defers manifest
   schema changes but adds BQ to the chart hot path. Use when we have other reasons to query indexes from BQ (admin
   tooling, cross-bucket reporting), not for the chart route alone.
2. **Range index** — _this plan_. Smallest schema change; biggest shrink for the dominant case; preserves existing
   parquet/UTL reader API.
3. **Two-tier sharded index** (`_index/symbols.parquet` directory + `_index/by_symbol/{venue}__{symbol}.parquet`
   detail). Naturally distributed; per-chart-click I/O is one small file. Cost: millions of tiny files in
   `_index/by_symbol/` for option chains; LIST pricing on GCS. Use only if range index hits its limits at 100K+ symbols
   in active use.
4. **BQ Object Tables** (query GCS object listing as a BQ table). No manifest writer code, always current. Cost: GCS
   metadata access limits, no partition pruning on path-pattern queries. Useful as a debugging surface, not as the chart
   route's primary index.
5. **Bloom filters** per `(venue, timeframe, data_type)`. Tiny memory, microsecond lookups. Cost: false positives mean
   wasted GCS calls on misses; ranged "give me all dates between X and Y" queries need a different structure. Worth
   pairing with range index for the negative-cache case if needed.
6. **Postgres / Redis hot cache**. SQL queries with proper indexes or sorted-sets keyed by tuple. Sub-millisecond
   lookups. Cost: another moving piece, sync job, divergence risk. Operational, not architectural — defer until
   measured.
