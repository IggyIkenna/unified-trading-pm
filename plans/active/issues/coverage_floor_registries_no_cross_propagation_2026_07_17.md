---
doc_type: issue
title:
  "Three coverage-floor registries don't propagate to each other: 9 CeFi venues + CME + Polymarket disagree by
  months-to-years; only sports (import-linked) stays in sync"
summary:
  "AUDIT (data_engineering, slot-9, 2026-07-17, AO task sports_manifest_canonicalisation-005). Reconciled the THREE
  parallel coverage-floor registries the plan flagged: UAC canonical/coverage_starts.py (catalogue denominator +
  coverage_start() oracle), UAC registry/venue_mapping.py (venue_start_dates/source_data_start_dates → MTDS
  orchestrator's is_venue_available_on_date pre-skip), and UAC canonical/domain/sports/league_data.py
  (SOURCE_COVERAGE_START/DATA_TYPE_COVERAGE_START → ManifestWriter's is_pre_launch_date pre-launch drop-guard). FINDING:
  registries 1 and 3 are structurally ONE SSOT for sports — coverage_starts.py imports league_data.SOURCE_COVERAGE_START
  directly and re-exports a dict() copy, so the 2026-07-15 c280e1ff floor amendment to league_data.py propagated to the
  catalogue automatically with zero additional diff. Registry 2 (venue_mapping.py) has NO import, test, or any
  code-level link to the other two — it is a genuinely independent third literal. Every CeFi venue with entries in BOTH
  registry 1 and registry 2 disagrees, mostly by YEARS not days: DERIBIT (2016-06-13 vs 2019-03-30), BYBIT (2018-11-21
  vs 2020-01-01), COINBASE-SPOT (2014-12-08 vs 2020-01-01), BITFINEX (2013-04-30 vs 2019-12-01/2020-01-01), KRAKEN
  (2013-09-10 vs 2020-01-01), OKX (2017-05-31 vs 2020-01-01), BINANCE (2017-08-17 vs 2019-11-17/2020-01-01), HYPERLIQUID
  (2023-06-29 vs 2023-04-15). TradFi CME disagrees by a decade (2010-01-01 TODO-verify vs 2020-01-01 verified).
  Prediction POLYMARKET disagrees by ~2.3 years (2022-11-21 CLOB-launch vs 2025-03-14 first-actual-instrument). DeFi
  protocol floors mostly show small 1-21 day drifts (CURVE/UNISWAP_V2/UNISWAP_V4/BALANCER/LIDO) except AAVE_V3, which
  has no exact match across either registry's chain-suffixed keys because registry 1 carries no chain axis at all.
  Sports itself shows NO live mismatch today (1≡3 by import; registry 2's lone overlapping key
  ODDS_API/odds_api=2020-06-06 happens to agree) but that agreement is unenforced coincidence — nothing would catch a
  future divergence. BITGET/KALSHI-PERP/POLYMARKET-PERP match exactly (added together by the same recent operator
  ruling). No code fixed inline — this is the audit's deliverable; concrete reconciliation + a falsifier test are filed
  below as todos."
status: open
priority: P1
nature: issue
asset_group: [cefi, defi, tradfi, prediction, sports]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    coverage-floor,
    coverage-starts,
    venue-mapping,
    sports-league-data,
    honest-coverage,
    ssot-drift,
    data-correctness,
    cross-repo,
  ]
related:
  [
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
created: 2026-07-17
author: unknown
parent_epic: manifest_master
source:
  "data_engineering worker (slot-9, planning VM), 2026-07-17, AO task sports_manifest_canonicalisation-005 ([AUDIT] P2
  Reconcile the THREE parallel coverage-floor registries). Direct reads of unified-api-contracts
  canonical/coverage_starts.py, registry/venue_mapping.py, canonical/domain/sports/league_data.py; git log on
  coverage_starts.py and venue_mapping.py around commit c280e1ff to confirm which files that amendment actually touched;
  cross-verified via an independent Explore sub-agent covering the same three files + git history."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-api-contracts/unified_api_contracts/canonical/coverage_starts.py,
    unified-api-contracts/unified_api_contracts/registry/venue_mapping.py,
    unified-api-contracts/scripts/check_coverage_floor_registry_drift.py,
    /plans/archive/2026_08/issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md,
  ]
---

## What I found

Three registries all express a "coverage floor" (earliest date a venue/source has data), consumed by three different
downstream mechanisms, with two different levels of code-level linkage:

1. **`unified_api_contracts/canonical/coverage_starts.py`** —
   `{CEFI,DEFI,TRADFI,PREDICTION,SPORTS}_SOURCE_COVERAGE_START`
   - `coverage_start()`. Feeds the catalogue's _expected date denominator_ — the number the honest-coverage % is
     computed against.
2. **`unified_api_contracts/registry/venue_mapping.py`** — `venue_start_dates` / `source_data_start_dates` +
   `is_venue_available_on_date()`. Consumed by MTDS's `_build_active_venues_for_date` (via
   `market_tick_data_service/engine/orchestrator/__init__.py::is_venue_available`) to pre-skip venues below their floor
   — this is what actually gates whether a fetch is even attempted.
3. **`unified_api_contracts/canonical/domain/sports/league_data.py`** — `SOURCE_COVERAGE_START` /
   `DATA_TYPE_COVERAGE_START` + `is_pre_launch_date()`. Consumed by UTL's `manifest_writer/_writer_ingest.py` and
   `_writer_record.py` to silently drop below-floor writes at capture time.

**Registries 1 and 3 are not actually independent — they're one SSOT for sports.** `coverage_starts.py` lines 29-31
imports `league_data.SOURCE_COVERAGE_START` directly and re-exports `dict(_SPORTS_SOURCE_COVERAGE_START)` at line 226;
the module docstring says so explicitly ("Sports already has its SSOT in `league_data`… re-exported through this module
for parity"). Confirmed via git log: commit `c280e1ff` ("fix(sports): amend UAC sports coverage floors to measured
reality") touched **only** `league_data.py` — `coverage_starts.py` has no commit that day. Registry 1's sports view
inherited the fix for free via the live import.

**Registry 2 has zero code-level link to either.** No import of `coverage_starts` or `league_data` anywhere in
`venue_mapping.py`; no shared test. `git log --since=2026-07-10 -- registry/venue_mapping.py` shows only unrelated
CeFi/DeFi-venue churn around `c280e1ff`'s timestamp — nothing touching `ODDS_API` or any sports key.

**Every CeFi venue present in both registry 1 and registry 2 disagrees**, mostly by years:

| Venue         | Registry 1 (`coverage_starts.py`) | Registry 2 (`venue_mapping.py`)                                      | Gap       |
| ------------- | --------------------------------- | -------------------------------------------------------------------- | --------- |
| BITFINEX      | 2013-04-30                        | BITFINEX-SPOT 2020-01-01 / BITFINEX-FUTURES 2019-12-01               | ~6.5 yr   |
| KRAKEN        | 2013-09-10                        | KRAKEN-SPOT/-FUTURES 2020-01-01                                      | ~6.3 yr   |
| COINBASE-SPOT | 2014-12-08                        | 2020-01-01                                                           | ~5 yr     |
| DERIBIT       | 2016-06-13                        | 2019-03-30                                                           | ~2.75 yr  |
| OKX           | 2017-05-31                        | OKX-SPOT/-FUTURES/-SWAP 2020-01-01                                   | ~2.6 yr   |
| BINANCE       | 2017-08-17                        | BINANCE-SPOT 2020-01-01 / -FUTURES 2019-11-17 / -DELIVERY 2020-01-01 | ~2-2.5 yr |
| BYBIT         | 2018-11-21                        | BYBIT 2020-01-01 / BYBIT-SPOT 2021-12-04                             | ~1.1 yr   |
| HYPERLIQUID   | 2023-06-29                        | 2023-04-15 (registry 2 EARLIER)                                      | 75 days   |

(BITGET, KALSHI-PERP, POLYMARKET-PERP match exactly — added together by the same recent operator ruling, per the shared
comment referencing `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md` in both files — that plan
was split + archived 2026-07-24 per the plan line-cap remediation; the KALSHI-PERP/POLYMARKET-PERP venue-add content now
lives in `plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`.)

TradFi: **CME** = 2010-01-01 (`# TODO verify`) in registry 1 vs 2020-01-01 (no TODO, i.e. verified) in registry 2 — a
decade apart. Prediction: **POLYMARKET** = 2022-11-21 (CLOB launch) in registry 1 vs 2025-03-14 (first actual
GCS-captured instrument) in registry 2 — ~2.3 years apart. DeFi: small 1-21 day drifts on CURVE/UNISWAP_V2/UNISWAP_V4
/BALANCER/LIDO; AAVE_V3 has no exact match at all — registry 1 carries no per-chain axis (flat 2022-03-16) while
registry 2's earliest chain leg is 2022-03-12 and its Ethereum leg is 2023-01-27, ~10 months later.

Note also a **key-naming-scheme mismatch** layered on top of the date mismatches: registry 1 uses bare venue/protocol
names (`BINANCE`, `CURVE`); registry 2 uses instrument-type/chain-suffixed keys (`BINANCE-SPOT`/`-FUTURES`/ `-DELIVERY`,
`CURVE-ETHEREUM`). There is no 1:1 key to compare for most of these venues without an explicit mapping.

## Why it matters

This is exactly the failure class the plan flagged and that `c280e1ff` was fixing — a floor amended in one place not
reaching the surfaces that actually gate fetching and writing. Two concrete failure directions, both live today:

- **Registry 1 earlier than registry 2** (the common case above): the catalogue denominator counts the gap window (e.g.
  BINANCE 2017-08-17 → 2019-11-17, ~2.25 years) as "expected", so it renders as missing/uncaptured coverage — but the
  MTDS orchestrator's pre-skip (registry 2) never even attempts to fetch inside that window, and the ManifestWriter's
  `is_pre_launch_date` guard (registry 3, sports-only) would silently drop any row that did get captured there. Years of
  permanently-red "missing" coverage that was never actually fetchable or intended to be.
- **Registry 2 earlier than registry 1** (HYPERLIQUID, by 75 days): the orchestrator will attempt to fetch and the
  writer will accept rows in a window the catalogue denominator doesn't count as expected at all — those captured rows
  exist but don't move the coverage % the operator watches, an invisible-progress gap in the other direction.

Because registry 2 has no code-level or test-level tie to 1/3, the sports fix pattern (import-linked SSOT) cannot be
retrofitted onto it without a deliberate change — and there is currently no falsifier catching new divergence, so this
will silently reappear even after a one-time reconciliation.

## Recommended decision

The workspace just shipped exactly this pattern for bounded exclusions (`COVERAGE_EXCLUSIONS`, typed `ExclusionReason`,
mandatory `evidence_uri`/`evidence_probe`, and `scripts/check_coverage_exclusions.py` as a falsifier — UAC@c280e1ff per
the plan's amended-CODE todo above). The natural fix for these floors is the same shape: either (a) make
`venue_mapping.py::venue_start_dates` derive from `coverage_starts.py` (import, like sports does today) rather than
maintaining a parallel literal, or (b) keep both but add a falsifier test that fails CI the moment a shared key's date
disagrees. Recommend (a) where the key schemes can be reconciled (most CeFi venues, since venue_mapping.py's
per-instrument-type split could resolve to the catalogue's venue-level floor as a MAX/fallback), and (b) as the
permanent backstop regardless, since the venue_mapping.py grain (per BINANCE-SPOT/-FUTURES/-DELIVERY) is genuinely finer
than the catalogue's flat per-venue value and may deliberately need to differ per instrument-type — an operator call on
which value is measured-reality is needed per venue, not a mechanical merge.

## Todos

- [x] ✅ [CODE] P1. Add a falsifier test (mirroring `scripts/check_coverage_exclusions.py`'s pattern) that fails CI when
      a venue/source key present in BOTH `unified_api_contracts/canonical/coverage_starts.py` and
      `unified_api_contracts/registry/venue_mapping.py` (`venue_start_dates`/`source_data_start_dates`) disagrees on its
      date — normalize the two key schemes first (e.g. `BINANCE` vs `BINANCE-SPOT`/`-FUTURES`/`-DELIVERY`) so the
      comparison is apples-to-apples. This is the permanent backstop against re-divergence. (repo:
      unified-api-contracts) — **DONE unified-api-contracts@09169cfe** `scripts/check_coverage_floor_registry_drift.py`
      (+ `tests/unit/test_coverage_floor_registry_drift.py`, wired into `quality-gates.sh` via pytest, mirroring
      `check_coverage_exclusions.py`'s script+test split). Normalizes via a narrow per-asset_group suffix allowlist
      (cefi: SPOT/FUTURES/DELIVERY/SWAP/CDE; defi: chain names; tradfi/prediction: exact-match only) — NOT a blind
      `startswith()`, which false-matched prediction's `POLYMARKET`/`KALSHI` against the unrelated cefi
      `POLYMARKET-PERP`/`KALSHI-PERP` crypto-perp venues (a different product, per coverage_starts.py's own comment).
      Sports excluded (already import-linked SSOT with its own falsifier). Ships with a `KNOWN_DIVERGENCES`
      shrinking-ratchet baseline covering the 16 currently-real mismatches this audit found (8 CeFi P1 + POLYMARKET P2 +
      7 DeFi P3, each citing this doc) so QG doesn't go red fleet-wide before those [DATA] todos land — a baseline entry
      whose pair no longer disagrees is itself a failure (`STALE BASELINE`), forcing removal the moment each [DATA] todo
      below resolves, so the baseline only shrinks. Verified live against the real registries: 0 new findings, 0 stale
      baseline entries (16/16 still genuinely tracked).
- [x] ✅ [DATA] P1. Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT,
      DERIBIT, OKX, BINANCE, BYBIT, HYPERLIQUID — table above) per venue: probe the actual manifest min(date) per
      `coverage_starts.py`'s own docstring instruction (`read_availability_index({bucket}).date.min()`) and update
      whichever registry is wrong to match measured reality. (repo: unified-api-contracts) — **DONE 2026-07-27 (slot-6)
      — unified-api-contracts@3d24f147c.** Probed live
      `read_availability_index("market-data-tick-cefi-prd-central-element-323112")`, grouped by venue on
      `capture_status="captured"`, cross-checked every result for a hidden "never-attempted gap before the registered
      floor" trap (the exact failure mode that would make a naive min() wrong — caught it live on HYPERLIQUID, see
      below). **Fixed 8/8 in `coverage_starts.py` `CEFI_SOURCE_COVERAGE_START`**: BITFINEX/KRAKEN/COINBASE-SPOT/OKX/
      BINANCE → `2020-01-01`; DERIBIT → `2019-05-08`; BYBIT → `2021-01-01`; HYPERLIQUID → `2023-04-15` (matched
      `venue_mapping.py`'s vendor-verified value, NOT the naive measured-captured-min of `2024-01-01` — see the new
      HYPERLIQUID backfill-gap todo below for why). **Fixed 3/5 in `venue_mapping.py` `venue_start_dates`**:
      `BINANCE-FUTURES` 2019-11-17→2020-01-01, `DERIBIT` 2019-03-30→2019-05-08, `BYBIT` 2020-01-01→2021-01-01.
      **Deliberately did NOT touch** `BITFINEX-FUTURES` (stays 2019-12-01) or `BYBIT-SPOT` (stays 2021-12-04) — both
      have their OWN documented, evidence-backed rationale in `venue_mapping.py`'s existing comments (Tardis-available
      vs symbol-reliability gap; separate spot-vs-perp product launch), a real residual gap not an unverified seed.
      Updated `scripts/check_coverage_floor_registry_drift.py`'s `KNOWN_DIVERGENCES`: removed 6 now-fully-resolved
      entries (KRAKEN/COINBASE-SPOT/DERIBIT/OKX/BINANCE/HYPERLIQUID), narrowed BITFINEX + BYBIT's notes to the real
      residual per-suffix gap. Verified via the falsifier itself: 0 new findings, 0 stale baseline (10 tracked
      divergences, down from 16). Fixed 2 tests that hardcoded the old baseline count/dates. All 39 targeted tests + the
      full UAC suite (12094 tests) pass; full `quality-gates.sh` green. Three new findings surfaced while probing are
      tracked as their own todos immediately below (not fixed here — separate, genuine backfill/data-completeness gaps,
      not coverage-floor-registry errors).
- [x] ✅ [DATA] P1. HYPERLIQUID gap ROOT-CAUSED + backfill CONFIRMED already in progress (2026-07-27, slot-11).
      Investigated per the todo — **neither "adapter gap" nor "never scheduled"**: (1) NOT vendor unavailability —
      Hyperliquid's own S3 archive genuinely has `book_snapshot_5` from 2023-04-15 (vendor-verified; matches
      `coverage_starts.py`'s floor, cross-checked against the 2026-05-05 incident investigation cited there). (2) NOT
      never-scheduled — `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` has targeted
      `VENUE_START_DATE["HYPERLIQUID"]="2023-01-01"` since its very first commit (`deployment-service@8a027c0`,
      2026-06-21) — the range was never config-excluded. (3) ROOT CAUSE = operational: the `cefi-hyperliquid-2023-*`
      shard has been repeatedly SPOT-preempted (3 separate mass-preemptions logged 2026-07-27 alone, per the parent
      tracking doc below) plus a since-fixed catalogue-universe-cap bug (`deployment-service@07936fa`, 2026-06-23)
      suppressed early fetches; some partial `attempted_failed` rows existed at one point (per
      `plans/archive/2026_06/cefi_hl_aster_batch_data_gaps_history_2026_06_22.md:170`) but were superseded/reset without
      a completed re-fetch ever landing. **Live-probed the exact window** (direct `_index/availability_index.parquet`
      read on `market-data-tick-cefi-prd-central-element-323112`, bypassing
      `read_availability_index(bucket, columns=[...])`, which returned an empty DataFrame in this session for an
      unrelated reason — worth its own follow-up, not chased here to stay in scope): confirms genuine
      zero-rows-of-any-`capture_status` for **2023-03-05 through 2023-12-31** — the true fully-blank gap starts ~6 weeks
      EARLIER than this todo's stated 2023-04-15 (dates 2023-01-01..2023-03-04 carry real `empty_confirmed` rows —
      genuinely probed and confirmed empty, evidence of a prior interrupted run's progress before the floor even
      begins). **NOT `BLOCKED`** — a live, healthy, idempotent non-force backfill VM is ALREADY actively closing this
      exact gap RIGHT NOW: `cefi-hyperliquid-2023-20260727-071055` (`ON_DEMAND=true`, non-preemptible, run-id
      `20260727-071055`), launched under the parent tracking doc's remediation effort — NOT launched by this task (a
      duplicate launch would have violated that effort's own "verify zero fleet VMs running first" guardrail). Verified
      RUNNING + genuinely advancing via a fresh `run.log` tail (not just VM status): chronological day-by-day walk from
      a `PROGRESS.json` checkpoint, real `ManifestWriter: per-VM shard updated` writes each day, currently at day
      **2023-02-27** (as of 2026-07-27T08:37:45Z) advancing at ~88s/day — climbing toward and through the
      2023-04-15→2023-12-31 window (ETA to window start ~1h, full window ~7-8h at the observed rate; this is the parent
      doc's own characterized "multi-hour-to-multi-day background operation", not completable within one task session).
      No new code or VM launch needed from this task. Cross-referenced with
      `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` (the live parent doc already tracking +
      operating this exact fleet, `locked_by: live-defi-rollout`) — added a pointer there too. Follow-up: re-verify
      manifest coverage for 2023-04-15..2023-12-31 once `DEPLOYMENT_COMPLETED exit_code=0` lands for
      `cefi-hyperliquid-2023-*`. (repo: market-tick-data-service / deployment-service — investigation + cross-ref only,
      no code shipped this task)
- [x] ✅ [DATA] P2. **DONE 2026-08-02 (slot-9, duplicate of the same finding in
      `/plans/archive/2026_08/issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md`, synced here to avoid a stale
      duplicate)** — DERIBIT's `trades` sparse-2019 gap root-caused: Tardis confirms `availableSince: 2019-03-30` for
      DERIBIT (denser + earlier than our 2019-05-08 floor); root cause was `_venue_years()` in
      `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` never including `"2019"` for DERIBIT, so no
      full-year sharded launch ever targeted it. Fix shipped (added `"2019"` + generalized `START_DATE` override) — full
      writeup + follow-up launch command in the sibling doc above. Evidence: `deployment-service@4fff44f`. (repo:
      market-tick-data-service backfill)
- [x] ✅ [DATA] P3. `venue_mapping.py`'s `BINANCE-DELIVERY` entry (`2020-01-01`) has ZERO real captured rows in the
      manifest (only 7 `attempted_failed` rows dated 2026-07-26) — the registered floor is unverifiable against measured
      reality because no real data exists yet. Investigate whether Binance COIN-M delivery contracts are actually being
      fetched at all, or whether this is a dead/never-implemented shard. (repo: market-tick-data-service) —
      **unified-api-contracts@9241dc85**. INVESTIGATION COMPLETE: BINANCE-DELIVERY is conclusively a
      dead/never-implemented shard. Added to MVP v9 (2026-06-24), removed by operator decision #3 in v10 (2026-06-27) —
      has NEVER been fetched by any production pipeline. Every downstream system (MTDS cefi_catalog_reader.py:172,
      _mvp_scope_rules.py:452-456, launch-mtds-live-cefi-consolidated.sh:30, liquid_representative.py:28) explicitly
      excludes it per the MVP spec. No backfill launcher targets it; the live connector (binance_futures_ws.py)
      references it only in comments. The 7 attempted_failed rows from 2026-07-26 were a one-off probe during the brief
      v9 window. The Tardis binance-delivery endpoint is real and correctly registered, but the venue_start_dates entry
      at 2020-01-01 is Tardis metadata only (unverifiable). Annotated the comment in venue_mapping.py to document this;
      kept the entry because is_venue_available_on_date() defaults to True for unknown venues (worse). **CORRECTION
      (2026-08-09, plan_reconciler agt-5f7f31):** a later, same-topic investigation in
      `/plans/archive/2026_08/issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md` (2026-08-05, slot-5) found
      this "dead/never-implemented" conclusion was WRONG on the live-fetch question — the forward/cron pipeline STILL
      attempts BINANCE-DELIVERY daily (704 manifest rows: 669 attempted_failed + 35 empty_confirmed, 2026-05-01 to
      2026-08-04, 6 data_types, all instrument_count=0.0), because the venue stays in `VENUES_BY_ASSET_GROUP["cefi"]` so
      it's iterated even though MVP catalog-tagging makes every attempt fail — wasting Tardis API quota daily. The
      MVP-removal and backfill-launcher-exclusion findings above are still correct; only "has NEVER been fetched" is
      false. The open remediation (`[INFRA] P3` in the doc cited above, and echoed in
      `/plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md`) is the live tracking location — no new todo
      needed here. **RESOLVED 2026-08-10**: the `[INFRA] P3` deregistration landed — BINANCE-DELIVERY removed from
      `VENUES_BY_ASSET_GROUP["cefi"]` + `tardis_to_venue`/`all_tardis_exchanges` (the forward-poll's actual iteration
      source) + `VENUE_DATA_TYPE_CAPABILITIES` (unified-api-contracts@56db28e6, verified ancestor of
      `origin/live-defi-rollout`); sibling doc archived resolved. This checkbox stays `[x]` — kept in sync per batch10
      todo 4.
- [x] ✅ [DATA] P2. Resolve the CME mismatch — `coverage_starts.py`'s 2010-01-01 carries `# TODO verify` while
      `venue_mapping.py`'s 2020-01-01 does not; probe the manifest to confirm 2020-01-01 is correct, update
      `TRADFI_SOURCE_COVERAGE_START["CME"]`, and drop the TODO marker. (repo: unified-api-contracts) —
      **unified-api-contracts (pending sha, quickmerge in progress 2026-07-25)**: probed live
      `market-data-tick-tradfi-prd-central-element-323112` manifest (`availability_index.parquet`, 5.8M rows) — earliest
      CME `capture_status=captured` row is 2020-01-01; every pre-2020 CME date is
      `empty_confirmed`/`EXPECTED_INSTRUMENT_NOT_LISTED` or `expected_unattempted`, not real data. Confirms
      `venue_mapping.py`'s 2020-01-01 ("earliest manifest data", no TODO) was correct and `coverage_starts.py`'s
      2010-01-01 was the unscrutinized value (git-blame: single commit `e81f598b`, never touched since, no rationale
      comment — unlike the DERIBIT-COMBO near-miss in the sibling shard-dimension doc). Updated
      `TRADFI_SOURCE_COVERAGE_START["CME"]` to `date(2020, 1, 1)`, dropped the TODO marker.
- [x] ✅ [DATA] P2. Resolve the POLYMARKET mismatch (2022-11-21 CLOB-launch vs 2025-03-14 first-actual-instrument,
      ~2.3-year gap) — **DONE 2026-08-04 (slot-15) — unified-api-contracts@d1eac060.** Corrected
      `PREDICTION_SOURCE_COVERAGE_START["POLYMARKET"]` from `date(2022, 11, 21)` (CLOB launch — ~2.3 years of
      permanently-red "missing" coverage before any actual instrument) to `date(2025, 3, 14)` (first actual captured
      instrument, manifest-verified per `venue_mapping.py`'s per-market GCS-parquet dates: `POLYMARKET:BTC=2025-03-13`,
      `POLYMARKET:ETH/SOL/XRP=2025-03-14`, etc.). Same pattern as the CME fix (2026-07-25, same issue doc) — catalogue
      denominator measures from first actual captured instrument, not venue/platform launch. Removed POLYMARKET from
      `check_coverage_floor_registry_drift.py`'s `KNOWN_DIVERGENCES` (now 9 baselined, down from 10). Falsifier confirms
      clean (0 new findings, 0 stale baseline). (repo: unified-api-contracts)
- [x] ✅ [DATA] P3. Resolve the small 1-21 day DeFi protocol drifts (CURVE, UNISWAP_V2, UNISWAP_V4, BALANCER, LIDO) and
      decide the AAVE_V3 chain-axis question — either add a per-chain axis to `DEFI_SOURCE_COVERAGE_START` (matching
      `venue_mapping.py`'s `PROTOCOL-CHAIN` grain) or explicitly document that the flat value is intended as the
      min-across-chains and verify each current value actually is the min. (repo: unified-api-contracts) — **DONE
      2026-08-05 (slot-15) — unified-api-contracts@1e190b0b.** Updated `DEFI_SOURCE_COVERAGE_START` to match
      `venue_mapping.py`'s manifest-verified ETHEREUM-chain dates: CURVE 2020-01-19→2020-01-20, UNISWAP_V2
      2020-05-04→2020-05-06, UNISWAP_V4 2025-01-31→2025-01-30 (dropped TODO), BALANCER 2021-05-13→2021-04-22, LIDO
      2020-12-19→2020-12-18. AAVE_V3 2022-03-16→2022-03-12 (min across POLYGON/AVALANCHE/ARBITRUM/OPTIMISM), documented
      as min-across-chains. UNISWAP_V2/V4/LIDO fully resolved (single ETHEREUM chain, no remaining mismatch).
      CURVE/UNISWAP_V3/BALANCER/AAVE_V3 re-baselined for non-min-chain differences (expected per-chain launch dates, not
      registry errors). Falsifier KNOWN_DIVERGENCES: 7→4 DeFi entries (3 fully resolved, 4 narrowed to non-min-chain
      differences). All 11 falsifier tests pass; full `quality-gates.sh` green.
- [x] ✅ [DATA] P3. Publish an explicit key-mapping table between `coverage_starts.py`'s bare venue/protocol keys and
      `venue_mapping.py`'s instrument-type/chain-suffixed keys (e.g. `BINANCE` →
      `{BINANCE-SPOT, BINANCE-FUTURES, BINANCE-DELIVERY}`, `CURVE` →
      `{CURVE-ETHEREUM, CURVE-AVALANCHE, CURVE-OPTIMISM}`) — a prerequisite for the P1 falsifier todo above to compare
      the two registries key-by-key instead of by coincidental name match. (repo: unified-api-contracts) —
      **unified-api-contracts@a9a27144**: Added `BARE_KEY_TO_VENUE_MAPPING_KEYS` dict in `coverage_starts.py` (12 CeFi +
      9 DeFi entries); updated `check_coverage_floor_registry_drift.py` to resolve from explicit mapping (replacing
      suffix-allowlist approach with lookup + exact-match fallback); added `_validate_mapping_completeness()` two-way
      gate check (stale references + undeclared mappings); 5 new tests (16/16 pass); full `quality-gates.sh` green.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (6 entries).
- **slot-6 2026-08-05** (coverage_floor_registries_no_cross_propagation-008): BINANCE-DELIVERY investigation complete —
  conclusively dead/never-implemented. Annotated `venue_mapping.py` comment (unified-api-contracts@9241dc85).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — all 6 Todos are done; re-pointed at the sole open
  Follow-up's real target (`manifest_writer/_read_index.py`, where `read_availability_index` lives) and kept the 2 core
  registries + the falsifier + the sibling fold-in-target doc; dropped the now-fully-resolved sports `league_data.py`
  and the closed `cefi_hl_aster_batch_data_gaps_2026_06_22.md` HYPERLIQUID item.

## Follow-ups

- [ ] [DATA] P3. Investigate why read_availability_index(bucket, columns=[...]) returned an empty DataFrame on
      2026-07-27 (flagged 'worth its own follow-up, not chased here').
- [ ] [DATA] P3. **Re-verify manifest coverage for Hyperliquid 2023-04-15..2023-12-31** once
      `DEPLOYMENT_COMPLETED exit_code=0` lands for the `cefi-hyperliquid-2023-*` backfill VM (run-id `20260727-071055`
      was actively advancing through this window as of 2026-07-27T08:37:45Z, ~88s/day — check current run status, it has
      had 13 days to complete since). Cross-ref: `cefi_hl_aster_batch_data_gaps_2026_06_22.md` (the live parent doc
      tracking this fleet). Repo: market-tick-data-service.

> **CORRECTED 2026-08-09 (plan_reconciler)**: the 2026-08-06 audit note below was itself already stale — its first named
> item (read_availability_index empty-DF) IS tracked above; only the second (re-verify manifest coverage) was genuinely
> prose-only. Converted to a tracked todo per the CLAUDE.md HARD RULE ("every follow-up is a `- [ ]` todo, never
> prose").
>
> **2026-08-06 archive-candidate audit**: Hyperliquid todo's own text flags 'worth its own follow-up, not chased here to
> stay in scope' (read_availability_index empty-DF) and a second prose-only 'Follow-up: re-verify manifest coverage for
> 2023-04-15..2023-12-31 once DEPLOYMENT_COMPLETED exit_code=0 lands' — neither became a `- [ ]` todo.
