---
title: Manifest scaling — range index for instrument×timeframe coverage
id: manifest_scaling_range_index_2026_05
status: parked — pre-activation audit in progress (2026-05-06)
created: 2026-04-30
owner: harsh
audience: backend engineers, data platform engineers
parent_reference:
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/data-catalogue-schema.md
  - /codex/14-customer-journeys/playbook-concepts/catalogue-data.md
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

1. **Pre-activation measurement** — confirm whether any of the four activation triggers (manifest > 50 MB, cold-read
   p99 > 3 s, chart p99 > 2 s, ~100 concurrent users) is firing today. Without a fired trigger, range-index code is
   premature optimization.
2. **Open-question resolution** — Q1 (DEFI Layer 1 path), Q2 (sports range-fit), Q5b (TRADFI `instrument_type` bug), Q5c
   (`available_from_datetime` semantics). These block the JSON sample from being faithful and the schema from being
   committable.

**Hard prerequisite** for moving from parked → active: the shard-granularity propagation plan
(`plans/active/shard_granularity_ssot_propagation_2026_05_06.plan.md`) must reach Phase 2 done. Reason: collapsing v6
rows into v7 ranges only works if v6 is honest. Today's v6 has confirmed lies (MDPS 1440 NaN-bar phantoms passed as
`captured`; MTDS DeFi drops `instrument_id`; instruments-service Polymarket overloads `data_type`). Collapsing those
into `(covered_from, covered_to, gap_dates)` would bake the lies into the v7 schema and make them unauditable inside
multi-year ranges.

**Pre-activation audit roadmap** (this plan, this branch — `live-defi-rollout`, no separate feature branch):

- [ ] [AUDIT] A1. Capture current manifest read p99 baseline via `scripts/bench_candle_reads.py` (add "manifest read
      p99" scenario if missing). Owner: harsh. Output: number, written into Section "Activation triggers — current
      measurements" below.
- [ ] [AUDIT] A2. Measure today's `_index/availability_index.parquet` size per bucket (instruments-store-{ag},
      market-data-tick-{ag}, mdps output). Output: table in Section "Activation triggers".
- [ ] [AUDIT] A3. Resolve Q1 — DEFI Layer 1 on-disk path (read 1-2 sample `gs://instruments-store-defi-{pid}/...`
      parquets, decide canonical surface). Update Q1 with the answer.
- [ ] [AUDIT] A4. Resolve Q2 — SPORTS Layer 1 fixtures schema (read sample
      `sports_reference/by_date/day=*/entity=fixtures/fixtures.parquet`). Decide whether range model applies or sports
      gets its own catalogue plan.
- [ ] [AUDIT] A5. Resolve Q5b — TRADFI cash-equity `instrument_type='SPOT_PAIR'` and `holiday_calendar='NASDAQ'` vs
      codex-spec `EQUITY` and `XNYS`. Determine intentional vs bug. If bug, this plan blocks on
      `instrument_schema_cohesion_and_market_hours_2026_03_31` fixing it.
- [ ] [AUDIT] A6. Resolve Q5c — confirm `available_from_datetime` = listing date and `available_to_datetime` =
      expiry/null on a real options + spot/perp sample.
- [ ] [AUDIT] A7. Cross-reference shard-granularity Phase 1 fix list. Identify which fixes affect range-index
      `gap_dates` correctness (e.g. MIG-MDPS2 1440-NaN-bar fix changes which days are "honest empty" vs "real gap").
      Document the dependency edges so the plan unparks at the right moment.
- [ ] [AUDIT] A8. Append each finding to "## Audit findings (pre-activation)" below as the audit progresses. Commit each
      finding to `live-defi-rollout` immediately (per workspace feedback rule).

Phase 0 (this audit) is **read-only** — no code, no schema changes, no manifest writes. Sole deliverable: data + Q&A
that lets harsh decide whether to (a) move plan to `active` and start Unit B, (b) keep parked but with a sharper
re-measurement trigger, or (c) supersede with a different design (e.g. two-tier sharded index from the rejected
alternatives appendix) if measurements suggest it.

## Activation triggers — current measurements

_Filled in by audit items A1, A2 below. Empty until measured._

| Trigger                                            | Threshold  | Today's value                                                       | Status                                |
| -------------------------------------------------- | ---------- | ------------------------------------------------------------------- | ------------------------------------- |
| Largest **canonical** `availability_index.parquet` | > 50 MB    | **30.2 MiB** (`market-data-tick-cefi`, 2026-05-06)                  | NOT FIRED (60% of)                    |
| Largest **per-VM shard** in any `_index/per_vm/`   | > 50 MB    | **3.65 MB** (`market-data-tick-defi/per_vm/local-10889-bd08`)       | NOT FIRED                             |
| Total `_index/` footprint per bucket               | (advisory) | up to **163 MiB** (sports-instruments, mostly weather backfill VMs) | advisory; consolidator should compact |
| `read_availability_index` p99 cold cache           | > 3 s      | TBD (A1)                                                            | TBD                                   |
| Chart-route p99 (manifest-read portion)            | > 2 s      | TBD (A1)                                                            | TBD                                   |
| Concurrent chart users                             | ~100       | TBD (operations data)                                               | TBD                                   |

## Audit findings (pre-activation)

_Findings appended per audit item as they complete. Each entry: date, item ID, what was checked, what was found, what it
means for this plan._

### 2026-05-06 — A2: index parquet sizes per bucket (read-only GCS scan)

**What was checked:** all 10 canonical buckets (5 asset_groups × `instruments-store` + `market-data-tick`) at
`gs://{kind}-{ag}-central-element-323112/_index/`. For each, captured size of the canonical `availability_index.parquet`
and the largest per-VM shard, plus the total `_index/` footprint.

**Canonical `availability_index.parquet` sizes (2026-05-06):**

| Bucket                         | Canonical index size |
| ------------------------------ | -------------------- |
| `market-data-tick-cefi`        | **30.2 MiB**         |
| `instruments-store-sports`     | **18.8 MiB**         |
| `market-data-tick-defi`        | **3.6 MiB**          |
| `market-data-tick-tradfi`      | **2.2 MiB**          |
| `market-data-tick-sports`      | **2.1 MiB**          |
| `instruments-store-defi`       | **1.1 MiB**          |
| `instruments-store-cefi`       | **0.6 MiB**          |
| `instruments-store-tradfi`     | **0.5 MiB**          |
| `market-data-tick-prediction`  | **0.2 MiB**          |
| `instruments-store-prediction` | **0.09 MiB**         |

(`instruments-store-tradfi` has no `BucketKind.MARKET_DATA` entry per UAC SSOT — TRADFI uses Databento managed storage;
not relevant here.)

**Verdict against Trigger 1 (> 50 MB):** **NOT FIRED.** Largest canonical index is 30.2 MiB on `market-data-tick-cefi`,
~60% of threshold. Sports-instruments at 18.8 MiB is the second-largest and is plausibly inflated by weather-backfill
per-VM shards (4 weather VMs alone wrote 0.5–0.7 MB each into `_index/per_vm/`); after the consolidator merges + dedup,
the canonical would shrink.

**However**: the `market-data-tick-cefi` bucket is at 30 MiB **today**, with backfill ongoing. Two of the active
backfills will inflate it materially:

1. Deribit options backfill (2020–2025) — `_index/per_vm/opt-deribit-{year}.parquet` shards already total ~199 KB
   summing 2020–2025; once consolidated into the canonical and as more option chains land, this is the biggest single
   growth driver.
2. CeFi spot/perp full backfill (mdps-cefi-2024/2025/2026 per-VM shards visible) — per-instrument-per-day v6 row shape ×
   ~7 timeframes × ~4 data_types × ~3000 cefi instruments × multi-year = the dominant row source.

**Implication for this plan:**

- **Don't unpark yet.** Trigger 1 is at 60%, not over.
- **Re-measure in 2 weeks** (post-shard-granularity Phase 1 cleanup, post-Deribit-options-2024-2025 backfill wave). If
  `market-data-tick-cefi` canonical exceeds 50 MB by then, Trigger 1 has fired and this plan moves to active.
- **Cluster the per-VM shards.** A separate concern: per-VM shards count is high (1307 shards on
  `market-data-tick-cefi/_index/per_vm/`). Consolidator already runs but the per-VM tail is long. This is a Trigger-2/3
  (read-latency) leading indicator regardless of canonical size — every reader that does `read_availability_index` after
  a recent write must walk per-VM shards until consolidation catches up.

**Doesn't change the Q1–Q5 schema design questions** — Trigger 1's not-fired status delays activation but doesn't
invalidate the schema work; that work proceeds independently and remains gated on the shard-granularity prerequisite.

### 2026-05-06 — A3 / Q1: DEFI Layer 1 canonical path resolved

**What was checked:** top-level prefixes of `gs://instruments-store-defi-{pid}/` and the contents of both
`_catalogue/instruments-service/` and `instrument_availability/by_date/`.

**Findings:**

- `instrument_availability/by_date/day=YYYY-MM-DD/venue={PROTOCOL-CHAIN}/instruments.parquet` **exists and is the
  canonical surface** for DEFI Layer 1.
- `_catalogue/instruments-service/day=YYYY-MM-DD/manifest.json` is a **pointer**, not a duplicate. Sample manifest
  (`day=2020-03-01`):
  ```json
  {
    "dataset_id": "instruments",
    "category": "",
    "processing_date": "2020-03-01",
    "row_count": 11,
    "gcs_bucket": "instruments-store-defi-...",
    "gcs_prefix": "instrument_availability/by_date/day=2020-03-01/venue=CURVE-ETHEREUM/instruments.parquet",
    "service_name": "instruments-service",
    "written_at": "..."
  }
  ```
  i.e. catalogue points at `instrument_availability/...`. Q1's premise ("`_catalogue/...` is intended canonical
  surface") is wrong — `_catalogue` is a per-day, per-dataset shipping receipt, the data lives at
  `instrument_availability/by_date/.../instruments.parquet` exactly like CEFI/TRADFI/PREDICTION.

**Sample parquet** (`day=2020-01-20/venue=CURVE-ETHEREUM/instruments.parquet`, 13 rows): same `InstrumentRecord` schema
as CEFI/TRADFI (`instrument_key`, `venue`, `instrument_type`, `available_from_datetime`, `available_to_datetime`,
`asset_class`, ...) **plus** DEFI-specific columns (`pool_address`, `pool_fee_tier`, `base_asset_contract_address`,
`quote_asset_contract_address`, `base_asset_decimals`, `base_asset_symbol_onchain`, `atoken_address`,
`debt_token_address`, `rate_method_selector`). `instrument_type='POOL'` for AMMs.

**Drift to flag separately (not an A3 blocker):** the partition uses `venue={PROTOCOL-CHAIN}` joined (e.g.
`venue=CURVE-ETHEREUM`, `venue=RAYDIUM-SOLANA`), not separate `venue=` and `chain=` partitions. Per the
shard-granularity SSOT (CLAUDE.md per-asset-group shard-key matrix), the DeFi shard atom is
`(asset_group=defi, **chain**, venue/protocol, data_type, instrument_id_or_protocol_id, day)` — `chain` is first-class,
not embedded in `venue`. The path layout collapses chain into the venue token. This is **already known to the
shard-granularity audit** — see MTDS finding `engine/orchestrator.py:1880-1908` (DeFi protocol-prefix list to lift to
UAC) and instruments-service `_extract_prediction_shard` parallels.

**Implication for this plan:**

- **Q1 is RESOLVED.** Use `instrument_availability/by_date/day=*/venue=*/instruments.parquet` as the DEFI Layer 1
  surface for the range index, exactly like CEFI/TRADFI/PREDICTION.
- **JSON sample can be made faithful** for the DEFI Layer 1 rows (drop the "extrapolated from UAC schema" caveat).
- **The `chain`-in-`venue` partition drift becomes the range-index plan's problem too**: when v7 emits a row per
  `(service, venue, instrument_id, ...)` for DeFi, must we use `venue='CURVE-ETHEREUM'` (matches today's partition) or
  split into `venue='CURVE'` + `chain='ETHEREUM'`? **Recommendation**: split — adopt the shard-granularity SSOT shape;
  the path partition stays joined for backwards compat (legacy reader handles it per CLAUDE.md "asset_group= canonical,
  category= legacy" pattern), but the manifest row keys carry `chain` as a first-class column. Encode this in Unit B
  schema definition when the plan unparks.
- **No new prerequisite added.** This is a clean schema decision the plan can carry alone.

### 2026-05-06 — A4 / Q2: SPORTS Layer 1 fixtures schema + range-fit verdict

**What was checked:** `sports_reference/by_date/day=2024-08-15/entity=fixtures/fixtures.parquet`. 43 rows. Schema:

```
af_fixture_id int64, referee_name string, date string, timestamp string, periods_first string, periods_second string,
venue_id double, venue_name string, venue_city string, status_long/short/elapsed_time, af_league_id int64,
season int64, round string, af_home_id/away_id/winner_id, af_home_name/away_name, home_score/away_score,
home_score_halftime/fulltime/extratime/penalty (and away_*), day string, data_available_at timestamp[UTC]
```

**Findings:**

- **Fixture is the "instrument" for sports Layer 1** — confirmed. Each row is a fixture identified by `af_fixture_id`
  with a single `timestamp` (kickoff). Schema is rich (referee, venue, scores, halftime/fulltime splits) —
  completed-match data on this date.
- **`data_available_at` IS stamped at write-time per fixture** — sample shows `2024-08-08 01:00:00+UTC` for a fixture on
  `2024-08-15 01:00:00+UTC`, i.e. ~7 days before kickoff. (Aligns with the `kickoff - 72h` / `kickoff - 60min` rules per
  the shard-granularity audit's sports temporal-availability stamping section.) This is good news — sports already has
  the column the shard-granularity plan demands; the gap is in features-sports midnight-UTC fallback
  (`_ensure_timestamp` at `batch_handler.py:146-151`), not at instruments Layer 1.
- **Schema cohesion concern:** prefixed columns (`af_*` for api-football, `tm_*` elsewhere likely) inside a
  generic-named entity (`fixtures`). Reasonable per-source provenance; flag for harmonisation only if a cross-source
  join is needed.
- **Range model FIT VERDICT: does NOT apply naturally.** Each fixture is point-in-time (`(af_fixture_id, kickoff_ts)`).
  There is no `(covered_from, covered_to, gap_dates)` semantic for fixtures themselves — a fixture exists on its kickoff
  day, not as a range. The "coverage" question for sports is different: "for league L on day D, how many fixtures were
  ingested vs how many actually played?" — a _count-based_ coverage matrix, not a _range-based_ one. (A range model
  COULD apply to per-league season windows: "Premier League season 2024-25 coverage_from=2024-08-16 to=2025-05-25
  gap_dates=[mid-week breaks]" — but that's a higher-level rollup, not the L1 atom.)

**Implication for this plan:**

- **Q2 is RESOLVED with a recommendation: scope sports OUT of v7 range index for the first cut.** Land
  CEFI/TRADFI/DEFI/PREDICTION (where range model is the natural shape because instruments persist over multi-year
  windows with daily/intraday data). Sports needs its own per-fixture coverage catalogue — a sibling artifact, not the
  same shape.
- **The catalogue plan (`instrument_catalogue_availability_matrix_2026_04_29`) already handles sports correctly** — it's
  count-based (fixtures captured / fixtures expected per (league, day)), which IS the right shape for sports. The
  range-index plan deferring sports doesn't leave a gap; the catalogue plan covers it.
- **Update Unit B schema to explicitly state "asset_group ∈ {cefi, defi, tradfi, prediction}"** when this plan unparks.
  Sports gets a follow-up plan if/when the catalogue's count-based aggregation hits scaling pain.
- **`data_available_at` column already exists** on Layer 1 fixtures — when Layers 2/3 sports range-coverage is designed
  (deferred), inputs will have honest PIT stamping. The shard-granularity Phase 1 fix (features-sports
  `_ensure_timestamp` midnight UTC bug) is in the consumer, not the source.

### 2026-05-06 — A5 / Q5b: TRADFI cash-equity `instrument_type='SPOT_PAIR'` confirmed BUG (still firing)

**What was checked:** sampled `instruments-store-tradfi-{pid}/instrument_availability/by_date/day=2026-05-04/` for both
NASDAQ (43 rows) and NYSE (215 rows = 174 SPOT_PAIR + 41 ETF). 6 days after the original Q5b sample (2026-04-30) — same
backfill version, no fix shipped between then and 2026-05-04.

**Findings (per-row, NASDAQ:AAPL example):** | Column | Codex spec / expected | On disk (2026-05-04) | Verdict | |
----------------------- | --------------------- | -------------------------- | -------------- | | `instrument_type` |
`EQUITY` | `SPOT_PAIR` | ❌ BUG | | `asset_class` | `equity` | `crypto` | ❌ BUG (worse) | | `holiday_calendar` | `XNYS`
(exchange_calendars key) | `NASDAQ` / `NYSE` | ❌ BUG | | `timezone` | `America/New_York` | `America/New_York` | ✓ | |
`regular_open_utc` | `13:30:00 UTC` | `13:30:00 UTC` | ✓ | | `regular_close_utc` | `20:00:00 UTC` | `20:00:00 UTC` | ✓ |
| `pre_market_open_utc` | non-null | `08:00:00 UTC` | ✓ (2C done?) | | `post_market_close_utc` | non-null | next-day
`00:00:00 UTC` | ✓ | | `instrument_key` | format consistent | `NASDAQ:SPOT_PAIR:AAPL` | derived from buggy
`instrument_type` | | ETFs (NYSE row sample) | `instrument_type=ETF` | correct | ✓ ETFs OK |

The `asset_class='crypto'` finding is **new and worse than the original Q5b note** — the original noted
`asset_class='equity'` was correct; that's now ALSO wrong. Likely the same root-cause backfill bug propagated.

**Implication for this plan:**

- **Q5b is RESOLVED as a BLOCKER, not a clarification.** The TRADFI cash-equity backfill is producing data with three
  mis-stamped columns. If the range-index plan adopts the on-disk vocabulary (`instrument_type='SPOT_PAIR'`,
  `asset_class='crypto'`, `holiday_calendar='NASDAQ'`), the v7 manifest will index broken classification — every TRADFI
  cash-equity range row would be keyed `SPOT_PAIR` instead of `EQUITY`, making cross-asset-group queries (e.g. "show me
  all EQUITY ranges") return zero on TRADFI.
- **This plan now has TWO hard prerequisites:**
  1. `plans/active/shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 2 done (existing).
  2. `plans/active/instrument_schema_cohesion_and_market_hours_2026_03_31.plan.md` Phase 2C **plus** a corrective
     re-stamp of the in-bucket TRADFI rows (instrument_type, asset_class, holiday_calendar). The original
     instruments_schema_cohesion plan owns the writer fix; the corrective re-stamp likely needs a sibling migration
     script (precedent: `instruments-service/scripts/migrate_local_sfi_to_canonical.py`).
- **Recommendation:** flag this finding to the schema-cohesion plan owner immediately. The bug is producing bad data on
  every backfill run and silently growing the corrupted footprint. (Not the range-index plan's job to fix, but the
  range-index plan can't ship until this is fixed.)
- **Pre-market / regular-hours fields are correct** — Phase 1E of `instrument_schema_cohesion_and_market_hours` has
  clearly shipped to TRADFI; the gap is Phase 2C (databento adapter populating the _correct_ per-instrument values, not
  just any values). The `'NASDAQ'` placeholder in `holiday_calendar` looks like a default-fill rather than a
  `pandas_market_calendars` lookup result.

### 2026-05-06 — A6 / Q5c: options `available_from_datetime` semantics PARTIALLY confirmed + new gap found

**What was checked:** sampled
`instruments-store-cefi-{pid}/instrument_availability/by_date/day=2026-05-04/venue=DERIBIT/instruments.parquet`. 3563
rows: 2918 OPTION + 547 COMBO + 74 FUTURE + 16 PERPETUAL + 8 SPOT_PAIR.

**Findings:**

1. **`available_from_datetime` = listing date — CONFIRMED for options + futures.**
   - BTC-26JUN26 option chain (10 strikes inspected): all share `available_from_datetime=2025-06-26 00:00:00+UTC` (12
     months before the 2026-06-26 expiry). Identical timestamp across strikes → it's the **chain listing date** (Deribit
     lists the chain together), not per-strike activation time.
   - BTC-26JUN26 future: `available_from_datetime=2025-06-27` (1 day after option-chain listing — adjacent but
     distinct).
   - BTC-PERPETUAL: `available_from_datetime=2019-03-30` — perpetual listing date matches Deribit's BTC perp launch.
     Plausible.
2. **`available_to_datetime` = NaT (always null) — REGARDLESS of expiry.** 0/3563 rows have a non-null
   `available_to_datetime`, including instruments with concrete `expiry` columns (futures + options). The schema
   declares the column but the writer never populates it. Today's options chain happens to contain only live instruments
   (`expiry >= today`, min expiry = 2026-05-04 = today), so this isn't visible from a single-day snapshot. **For the
   range index, this means today's L1 has no `available_to` to use as the natural `covered_to` for dated derivatives —
   must be derived from `expiry`.**
3. **The day-snapshot partition holds the as-of-day live universe, not the historical universe.** 0/2918 options on
   day=2026-05-04 are expired. To find an instrument's full lifetime via L1, must walk the day-partitions between its
   `available_from_datetime` and either its `expiry` or its disappearance from a later partition. This is exactly what
   the range index is supposed to compute — so the "where do I find the full lifetime?" question is answered by the
   index existing.

**Implication for this plan:**

- **Q5c is RESOLVED with refinement:**
  - `available_from_datetime` = chain/instrument **listing date** ✓ (matches plan's prior assumption)
  - `available_to_datetime` is **declared but unpopulated** — the v7 range index for dated derivatives must derive
    `covered_to` from `expiry`, not from `available_to_datetime`.
- **Recommendation for Unit B schema:**
  ```
  covered_from = max(available_from_datetime, first day instrument actually has data in this bucket)
  covered_to   = (expiry if instrument_type ∈ {OPTION, FUTURE, COMBO}) else (last day instrument has data; null if still active)
  ```
- **No new prerequisite required.** This works around the unpopulated `available_to_datetime` column rather than
  blocking on a fix. Optional follow-up: file a separate ticket to populate `available_to_datetime=expiry` at write-time
  so the column matches its name; cosmetic but reduces confusion for future consumers.
- **Schema-cohesion plan note**: TRADFI futures (CME `MES`, etc.) need the same scrutiny — likely also have
  `available_to_datetime=NaT`. Cross-check when running the same audit on
  `instruments-store-tradfi/.../venue=CME/instruments.parquet`. Tracked but not blocking.

### 2026-05-06 — A7: shard-granularity Phase 1 dependency cross-reference

**What was checked:** read-only review of `plans/active/shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 0
audit findings against this plan's Unit A–E execution plan. Goal: identify which shard-granularity fixes MUST land
before range-index Unit B–E can compute honest `(covered_from, covered_to, gap_dates)`.

**Mapping (shard-granularity finding → range-index dependency):**

| Shard-granularity item | Service / file | Range-index impact | Severity for unparking | |

| --------------------------------------------------------------------------------------------------------------- |
| --------------------------------------------------------------------------------------------------------------- |

---

|
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| -------------------- | | **MIG-MDPS1** + **MIG-MDPS2** — MRO shadow + 1440-NaN-bar phantom fix | MDPS
`orchestration_writer.py:328`, 17 `_create_empty_output` sites in `adapters/{cefi,tradfi,defi,sports}/` | **CRITICAL** —
every NaN-bar day collapsed into `(covered_from, covered_to)` becomes part of the range, falsely claiming coverage.
Until MDPS stops writing 1440-NaN parquets with `capture_status=captured`, v7 cannot trust v6 `captured` status to
derive ranges. | **HARD BLOCKER** | | **MIG-MDPS3** — `_write_manifest_records` v3-shape → v6 with
`chain, instrument_type, instrument_id, timeframe` | MDPS `orchestration_service.py:283-388` | **CRITICAL** — v7 ranges
are keyed `(service, venue, instrument_id, timeframe, data_type)`. If MDPS today writes v3 coarse
`(date, venue, data_type, row_count)` rows, there is NO per-instrument signal to range over. v7 cannot be derived from
v3 rows. | **HARD BLOCKER** | | **MTDS DeFi instrument_id drop** — `_defi_manifest.py:120,300` | MTDS DeFi handlers |
HIGH — DeFi v7 needs `instrument_id_or_protocol_id` per row. If today's manifest has empty `instrument_id`, can't range
per-pool. | HARD BLOCKER | | **MTDS GMX `chain=""`** — `perp_funding_handler.py:225` | MTDS DeFi perp funding | MED —
GMX rows need `chain="ARBITRUM"`/`"AVALANCHE"`. v7 keys `chain` first-class; bad chain = mis-bucketed range. | blocker
(small surface) | | \*\*instruments-service Polymarket
`data_type=BTC                                                               | ETH`overload**
—`orchestrator.py:1988-1995` | instruments-service | HIGH (prediction only) — v7 ranges for prediction need
`canonical_question_group`. UAC SSOT greenfield (BUILD-PRED1..4). Block prediction range-index land until UAC ships
canonical_question_group. | blocker (prediction) | | **instruments-service SFI / FOOTYSTATS coarser-pre-flight bug** |
instruments-service `orchestrator.py:5013-5018`, `4747-4750` | LOW for range-index (sports out-of-scope per A4) — but
may pollute the catalogue plan's count-based sports coverage which range-index docs reference. | not a blocker | |
**`available_at` not stamped at write-time anywhere** (5/5 services) | MTDS, MDPS, features-onchain, features-sports,
features-delta-one | MED for range-index L1 (instruments already have `available_from_datetime`). HIGH for L2/3 (raw +
processed) — range-index L2/3 was deferred in plan's Q3, so this isn't immediately blocking. | not a blocker for L1 | |
**No NaN-ratio / row-count / schema / cluster write-gate** (5/5 services) | UTL `FeatureWriteGate` extension +
per-service apply | HIGH — same root cause as MDPS phantom: write-gate failure means `captured` rows lie. Range-index
trusts `captured` to decide a day is "in" the range. | HARD BLOCKER | | **Honest-coverage trio (`record_empty` /
`record_failed`) absent in main paths** | MDPS, features-onchain, features-delta-one | HIGH — range-index treats
`empty_confirmed` as "honest empty within trading calendar" → not a `gap_date`. If the writer never emits
`record_empty`, the range-index can't distinguish "we tried and source had nothing" from "we never tried." | HARD
BLOCKER | | **Pre-flight coarser than writer** (5+ services) | instruments / MTDS / MDPS / features-onchain /
features-sports | MED — affects re-run + concurrent backfill safety, not range correctness directly. Range-index can
land with this still partially open as long as writer is honest. | not a blocker | | **LookaheadBiasError input-side
gap** | features-\* (3/3 audited) | NONE for range-index L1 — affects feature-output correctness, not instrument
coverage. Don't block on this. | not a blocker | | **except: continue` per-instrument silent-drops**
(umi_tick_provider.py 3 sites) | MTDS | HIGH — silently-failed-but-ranged-as-captured instruments produce false ranges.
Same severity class as the empty-placeholder bug. | HARD BLOCKER |

**Hard-blocker summary** (must land before this plan unparks):

1. MIG-MDPS1 + MIG-MDPS2 (MRO shadow + 1440-NaN fix) — without this, ranges encode lies on every option/perp.
2. MIG-MDPS3 (v3 → v6 manifest shape) — without per-instrument rows, no per-instrument ranges to compute.
3. MTDS DeFi `instrument_id` + GMX `chain` fixes (`_defi_manifest.py`, `perp_funding_handler.py:225`).
4. UTL write-gate trio (NaN / row-count / schema / cluster) lifted from `schema_validation.py` + applied workspace-wide.
   Specifically: range-index trusts `capture_status=captured` to mean "real rows landed"; without write-gates, that's
   not enforceable.
5. Honest-coverage trio (`record_empty` / `record_failed`) added to MDPS + features-onchain + features-delta-one main
   paths — without `record_empty`, range-index can't subtract holidays / honest gaps from the "missing days" set.
6. MTDS `umi_tick_provider.py:581/737/921` per-instrument silent-drop fix — same root cause as MDPS phantoms.

**Plan-level status update:** the original "Hard prerequisite: shard-granularity Phase 2 done" was correct but
under-specified. **Concretely, the items above are the critical subset of Phase 1 + a slice of Phase 2.** Range- index
plan can unpark when those 6 hard-blockers green plus Q5b TRADFI `instrument_type` re-stamp lands. Other Phase 1 items
(LookaheadBiasError, pre-flight coarseness, sports-specific fixes, dual-vocab probe lift) are complementary but not
unparking-blockers.

**Action items for this audit's harness (no code changes, just tracking):**

- [x] A7-1: Cross-reference table embedded above. ✓
- [ ] A7-2: When shard-granularity Phase 1 ships any of the 6 hard-blockers, append a "blocker N green" line to this
      finding and update the activation-trigger table at the top of this plan.
- [ ] A7-3: Sync with shard-granularity plan owner (claude/teammate) to flag the 6 hard-blockers as items the
      range-index plan depends on, so they don't get reordered/parked behind lower-impact items.

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

`/codex/02-data/data-catalogue-schema.md` defines the per-service `data-catalogue.{service}.yaml` files (one row per
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

`/codex/02-data/per-category-bucket-layouts.md` documents that sports uses
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

- `/codex/02-data/availability-manifest-and-data-status.md` — current schema (v6, expanded by `quote_margin_combo`
  2026-04-23).
- `/codex/02-data/chunk-safe-manifest-migrations.md` — pattern for large parallel manifest rewrites without races.
- `/codex/02-data/per-instrument-sentinel-rollout.md` — related prior work on per-instrument tracking.
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
