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
related: [/plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md]
created: 2026-07-17
parent_epic: manifest_master
source:
  "data_engineering worker (slot-9, planning VM), 2026-07-17, AO task sports_manifest_canonicalisation-005 ([AUDIT] P2
  Reconcile the THREE parallel coverage-floor registries). Direct reads of unified-api-contracts
  canonical/coverage_starts.py, registry/venue_mapping.py, canonical/domain/sports/league_data.py; git log on
  coverage_starts.py and venue_mapping.py around commit c280e1ff to confirm which files that amendment actually touched;
  cross-verified via an independent Explore sub-agent covering the same three files + git history."
locked_by:
resolved_by:
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: NA
depends_on: []
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
lives in `plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`.)

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

- [ ] [CODE] P1. Add a falsifier test (mirroring `scripts/check_coverage_exclusions.py`'s pattern) that fails CI when a
      venue/source key present in BOTH `unified_api_contracts/canonical/coverage_starts.py` and
      `unified_api_contracts/registry/venue_mapping.py` (`venue_start_dates`/`source_data_start_dates`) disagrees on its
      date — normalize the two key schemes first (e.g. `BINANCE` vs `BINANCE-SPOT`/`-FUTURES`/`-DELIVERY`) so the
      comparison is apples-to-apples. This is the permanent backstop against re-divergence. (repo:
      unified-api-contracts)
- [ ] [DATA] P1. Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT,
      DERIBIT, OKX, BINANCE, BYBIT, HYPERLIQUID — table above) per venue: probe the actual manifest min(date) per
      `coverage_starts.py`'s own docstring instruction (`read_availability_index({bucket}).date.min()`) and update
      whichever registry is wrong to match measured reality. (repo: unified-api-contracts)
- [ ] [DATA] P2. Resolve the CME mismatch — `coverage_starts.py`'s 2010-01-01 carries `# TODO verify` while
      `venue_mapping.py`'s 2020-01-01 does not; probe the manifest to confirm 2020-01-01 is correct, update
      `TRADFI_SOURCE_COVERAGE_START["CME"]`, and drop the TODO marker. (repo: unified-api-contracts)
- [ ] [DATA] P2. Resolve the POLYMARKET mismatch (2022-11-21 CLOB-launch vs 2025-03-14 first-actual-instrument,
      ~2.3-year gap) — decide whether the catalogue denominator should measure from CLOB launch or from first actual
      captured instrument, and reconcile `PREDICTION_SOURCE_COVERAGE_START["POLYMARKET"]` against `venue_mapping.py`'s
      `POLYMARKET` entry accordingly. (repo: unified-api-contracts)
- [ ] [DATA] P3. Resolve the small 1-21 day DeFi protocol drifts (CURVE, UNISWAP_V2, UNISWAP_V4, BALANCER, LIDO) and
      decide the AAVE_V3 chain-axis question — either add a per-chain axis to `DEFI_SOURCE_COVERAGE_START` (matching
      `venue_mapping.py`'s `PROTOCOL-CHAIN` grain) or explicitly document that the flat value is intended as the
      min-across-chains and verify each current value actually is the min. (repo: unified-api-contracts)
- [ ] [DATA] P3. Publish an explicit key-mapping table between `coverage_starts.py`'s bare venue/protocol keys and
      `venue_mapping.py`'s instrument-type/chain-suffixed keys (e.g. `BINANCE` →
      `{BINANCE-SPOT, BINANCE-FUTURES,     BINANCE-DELIVERY}`, `CURVE` →
      `{CURVE-ETHEREUM, CURVE-AVALANCHE, CURVE-OPTIMISM}`) — a prerequisite for the P1 falsifier todo above to compare
      the two registries key-by-key instead of by coincidental name match. (repo: unified-api-contracts)
