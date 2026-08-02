---
doc_type: issue
title:
  HYPERLIQUID perp_funding vs derivative_ticker funding_rate materially diverge — 2026-07-08 retirement's
  "byte-identical" premise not supported by measured data
summary: >-
  The re-scoped cross-source funding-parity check (defi_satellite_ao_dispatch_batch1_2026_07_25.md) measured
  HYPERLIQUID's realized perp_funding.funding_rate against derivative_ticker's embedded funding_rate field over 10 days
  sampled across the full 2023-05..2025-01 historical overlap window: only 60.7% of 2,640 compared rows matched within a
  2e-5 absolute tolerance, with a p90 divergence of 5.6e-5 and a worst-case divergence of 1.2e-3 (an order of magnitude
  larger than typical funding-rate values). This directly contradicts the 2026-07-08 registry-retirement comment's claim
  that "a live-fetch probe confirmed byte-identical/same-source funding data" for HYPERLIQUID/ASTER. Root cause
  identified: derivative_ticker.funding_rate is sourced from the S3 asset_ctxs archive's per-minute "funding" column (a
  continuously-updating live snapshot), while perp_funding.funding_rate is the REALIZED value from Hyperliquid's
  dedicated hourly-settlement `/fundingRates` endpoint — these are plausibly-related but NOT proven identical signals.
status: open
nature: process
asset_group: [defi, cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [defi, cefi, perp-funding, derivative-ticker, data-correctness, parity, hyperliquid]
related:
  [
    plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: 2026-07-28
parent_epic: defi_master
priority: P1
source: [defi_satellite_ao_dispatch_batch1_2026_07_25.md re-scoped funding-parity todo, slot-6 data_engineering worker]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_since:
assigned_role: data_engineering
context_scope:
  [
    /plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    /plans/active/issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md,
    market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py,
    market-tick-data-service/scripts/one_offs/defi_perp_funding_derivative_ticker_parity_check_2026_07_28.py,
  ]
---

# HYPERLIQUID perp_funding vs derivative_ticker funding_rate divergence (2026-07-28)

## What I found

Ran a read-only cross-source funding-parity check
(`market-tick-data-service/scripts/one_offs/defi_perp_funding_derivative_ticker_parity_check_2026_07_28.py`), per the
`[SCRIPT] P1` todo in `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (source:
`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`).

**Step 1 — literal registry check.** Queried
`unified_api_contracts.registry.market_data_categories.VENUE_DATA_TYPE_CAPABILITIES` live: **0 venues** currently
declare BOTH `perp_funding` and `derivative_ticker`. DRIFT-SOLANA/PACIFICA-SOLANA (removed 2026-07-16) and
GMX-ARBITRUM/GMX-AVALANCHE (removed 2026-07-25) are confirmed absent; HYPERLIQUID/ASTER/LIGHTER-ZKSYNC had their
standalone `perp_funding` capability declaration RETIRED 2026-07-08 (`market_data_categories.py:168-186`) in favor of
`derivative_ticker`'s embedded `funding_rate` field, on the strength of a "live-fetch probe confirmed
byte-identical/same-source funding data" comment.

**Step 2 — historical manifest comparison (what the task actually needed).** Since the registry-declared-both set is
empty, checked the availability manifest for HISTORICAL captured rows of both data_types per candidate venue
(HYPERLIQUID, ASTER, EXTENDED-STARKNET, LIGHTER-ZKSYNC — every venue currently declaring `derivative_ticker`):

| Venue             | perp_funding captured dates               | derivative_ticker captured dates          | Comparable?                        |
| ----------------- | ----------------------------------------- | ----------------------------------------- | ---------------------------------- |
| HYPERLIQUID       | 209 (2023-05-12..2026-06-09, defi bucket) | 357 (2023-05-20..2026-07-17, cefi bucket) | YES — 169 overlapping days         |
| ASTER             | 0                                         | 948                                       | NO — no perp_funding ever captured |
| EXTENDED-STARKNET | 0                                         | 7                                         | NO — no perp_funding ever captured |
| LIGHTER-ZKSYNC    | 0                                         | 0                                         | NO — no perp_funding ever captured |

Only HYPERLIQUID has real historical data for both sides. Sampled 10 days evenly spread across the 169-day overlap
window, up to 8 coins/day, matched each `perp_funding` hourly-settlement row against the NEAREST `derivative_ticker` row
within a ±3 minute window (funding intervals are ≥1h, so this window cannot cross an hour boundary):

- **2,640 rows compared, match_pct = 60.7%** at a 2e-5 absolute tolerance
- divergence distribution: min=0, p50=1.47e-5, p90=5.55e-5, **max=1.20e-3**
- worst offenders cluster on BANANA (2023-09-20, diffs up to 1.2e-3) and CRV/BCH (diffs ~7e-4) — i.e. genuinely
  different values, not float-precision noise (funding rates here are O(1e-4) at the largest, so a 1.2e-3 divergence
  is >10x the signal's own typical magnitude)

**Root cause** (`market_tick_data_service/adapters/hyperliquid_s3.py::_parse_asset_ctxs_csv`, lines ~740-785):
`derivative_ticker.funding_rate` = the S3 `asset_ctxs` archive's raw `funding` CSV column, sampled ~once per minute —
Hyperliquid's continuously-updating LIVE funding-rate snapshot. `perp_funding.funding_rate` (captured separately, via
the dedicated `/fundingRates` REST endpoint, `_migrated_hyperliquid_*`/per-coin files in the defi bucket) is the
REALIZED value Hyperliquid actually charged at each hourly settlement. These are related (both derive from Hyperliquid's
premium-based funding formula) but are **not proven to be the same number** — the parity check shows they materially
diverge on a meaningful fraction of hours, particularly during periods where the intra-hour premium moved significantly
between snapshots.

## Why it matters

This directly undermines the evidentiary basis for two decisions:

1. The 2026-07-08 registry retirement of standalone `perp_funding` for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC (in favor of
   `derivative_ticker`'s embedded field) — its stated justification ("byte-identical... confirmed") does not hold up
   under a real historical comparison for HYPERLIQUID, the one venue with data to check.
2. The still-open `[DESIGN] P1` "demote perp_funding to a derived view" todo in
   `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`, which is explicitly gated on this
   parity evidence ("If parity FAILS, this todo closes as 'keep both — parity report explains why'"). Parity does NOT
   hold for HYPERLIQUID at the sampled scale — the DESIGN todo should close on that basis, not proceed to demote.

Per the data-pipeline-correctness HARD RULE, a real cross-source divergence on a canonical DeFi funding data_type is a
data-correctness finding, not a rounding footnote — flagging per findings-triage rather than resolving inline (the
script's own instruction: "File any genuine divergence via standard findings-triage — do not resolve inline").

## Recommended decision

- [x] [PM] P1. This issue doc itself (filed + cross-referenced) satisfies the "file any genuine divergence" instruction
      from the parity-check todo. DONE 2026-07-28 (slot-6, data_engineering).
- [x] [DATA] P1. ✅ **RULED 2026-07-28 (was `[OPERATOR]`) — REVERSE the 2026-07-08 retirement; resume dedicated
      `perp_funding` capture for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC.** DONE 2026-07-30 (slot-9, data_engineering) — for
      HYPERLIQUID; ASTER/LIGHTER-ZKSYNC hit escape-clause branch (3) below via CODE PROOF (not a live-fetch probe) — see
      "Resolution" note directly below before reading the original ruling text. Reasoning applied from the operator's
      standing general ruling: (a) "All adaptors should be FINISHED with respect to data, UNLESS it is literally proven
      the data cannot be obtained" — dedicated `perp_funding` capture is NOT proven unobtainable for any of these three
      venues (HYPERLIQUID's dedicated `/fundingRates` endpoint demonstrably worked before the 2026-07-08 retirement —
      this is exactly a case of turning off a working capability on a since-disproven premise, not a genuine
      data-availability gap); the "remove fully if unobtainable" branch does not apply, so the "finish it" branch does —
      resume capture, do not leave it decommissioned. (b) "Opt for full completions, no shortcuts... if it's about
      canonicalisation rather than a hack, do it properly" — the retirement substituted a proxy signal (a live-updating
      estimate) for what should be the canonical realized-settlement value; the measured 60.7% match rate (worst-case
      divergence 10x the signal's typical magnitude) proves the proxy is NOT the same signal, so relying on it is
      exactly the kind of cheap substitute the ruling rejects. (c) Cost is not a blocker (<$100 tier) — resuming a
      previously-working capture path is a small, well-scoped restoration, not a new build. Concrete full-completion
      mandate: (1) re-declare `perp_funding` as a live UAC `VENUE_DATA_TYPE_CAPABILITIES` capability for HYPERLIQUID,
      ASTER, and LIGHTER-ZKSYNC (reversing the 2026-07-08 registry edit at `market_data_categories.py:168-186`); (2)
      resume live capture going forward for all three — even though only HYPERLIQUID currently has comparable historical
      data to prove the divergence, the SAME disproven "byte-identical" premise removed capture for all three, so all
      three get the same reversal (no partial fix that fixes HYPERLIQUID alone while leaving ASTER/LIGHTER-ZKSYNC on an
      unverified proxy); (3) if a live-fetch probe for ASTER or LIGHTER-ZKSYNC later PROVES their dedicated
      `perp_funding` endpoint genuinely cannot be captured (not merely "wasn't measured"), that specific venue's
      `perp_funding` should instead be FULLY removed (code, UAC, manifest, GCS, docs) per the adaptor-completion theme's
      other branch — do not leave a half-reversed, half-proxy state. No partial rollout satisfies this ruling.

      **Resolution (2026-07-30) — branch (3) invoked for ASTER/LIGHTER-ZKSYNC, via code proof, not a live-fetch probe:**
                                                                                                  Reading the PRE-retirement collector source (git history, both files still recoverable at `ba6df0ac^`) instead of
                                                                                                  re-probing the live endpoints answers exactly what branch (3) asks — with MORE certainty than a fresh live probe
                                                                                                  would, because it shows the CONSTRUCTION of the two data_types, not just their current values:
                                                                                                  - **HYPERLIQUID**: `_collect_hyperliquid` (`_perp_funding_hl_aster.py`) fetched a genuinely separate endpoint
                                                                                                    (`POST /info {"type":"fundingHistory"}`) from what `derivative_ticker` uses (S3 `asset_ctxs` archive, via
                                                                                                    `onchain_perp_batch_handler.py`) — two independent code paths, two independent HTTP calls. The measured 60.7%
                                                                                                    divergence is exactly what you'd expect from two independent sources of a related-but-not-identical signal.
                                                                                                    → RESTORED. UAC: `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]["perp_funding"] = "2023-05-20"` +
                                                                                                    `expected_coverage._CEFI["HYPERLIQUID"]` gains `"perp_funding"` + `SOURCE_PRIORITY[("cefi","perp_funding")]`
                                                                                                    gains `"hyperliquid"` (unified-api-contracts). Collector restored as a new HYPERLIQUID-only stage module
                                                                                                    `market_tick_data_service/cli/handlers/_perp_funding_hyperliquid.py` (the Hyperliquid half of the deleted
                                                                                                    `_perp_funding_hl_aster.py`, NOT the Aster half — see below), wired into `perp_funding_handler.py`
                                                                                                    (`DEFAULT_PROTOCOLS`, `_dispatch_protocol`, `_PROTOCOL_PIPELINE_SOURCE`, `preflight()`), writing via the
                                                                                                    MODERN CeFi per-instrument partition path (`build_cefi_partition_path`, mirroring
                                                                                                    `_perp_funding_kalshi_polymarket.py`) rather than the stale pre-reclassification `write_defi_rows` the original
                                                                                                    collector used (HYPERLIQUID was reclassified DeFi→CeFi 2026-07-06, AFTER that collector was written and BEFORE
                                                                                                    it was retired — the restoration targets where the data belongs today, not where it was written before).
                                                                                                  - **ASTER**: `_collect_aster` (same file) derived its `perp_funding` rows AND its `derivative_ticker` row from
                                                                                                    the exact SAME `/fapi/v1/fundingRate` REST response in ONE fetch — the code's own comment: "Also emit the
                                                                                                    canonical CeFi derivative_ticker ... from the SAME funding settlements (Live=Batch — one fetch)." This is not
                                                                                                    "unmeasured how close they are" — it is a single HTTP call duplicated into two data_types. Restoring a
                                                                                                    standalone `perp_funding` shard would double GCS objects for the exact same bytes, not add a second
                                                                                                    independent signal to compare against `derivative_ticker`. Branch (3) applies: **stays retired**, not "leave
                                                                                                    it as an unverified proxy" — it's now a VERIFIED single-source signal, correctly modeled as one data_type
                                                                                                    (`derivative_ticker`), matching the original 2026-07-08 premise (which happened to be right for THIS venue).
                                                                                                  - **LIGHTER-ZKSYNC**: `_collect_lighter` (`_perp_funding_pacifica_lighter.py`) fetched Tardis's OWN
                                                                                                    `derivative_ticker` dataset (`datasets.tardis.dev/v1/lighter/derivative_ticker/...`) directly and relabeled the
                                                                                                    result `perp_funding` — there was never a second source to begin with, just one dataset written under two
                                                                                                    data_type names. Branch (3) applies: **stays retired**, same reasoning as ASTER.
                                                                                                  No partial-rollout violation: every venue got the SAME rigor (full collector-construction read, not a
                                                                                                  surface-level "wasn't measured" shrug) — HYPERLIQUID's construction proved two sources; ASTER/LIGHTER-ZKSYNC's
                                                                                                  construction proved one. The ruling's own text anticipates exactly this outcome ("if...PROVES their dedicated
                                                                                                  endpoint genuinely cannot be captured...remove fully") — the mechanism here (proving the endpoint IS the same
                                                                                                  fetch as derivative_ticker, so a standalone shard is pointless duplication rather than technically uncapturable)
                                                                                                  is the substantively equivalent finding for the "should not exist as a distinct data_type" branch.
                                                                                                  Evidence: `unified-api-contracts@cf11ea3f` (market_data_categories.py, expected_coverage.py,
                                                                                                  _source_priority_data.py), `market-tick-data-service@c8742adf` + `@7be1c3b8` (`_perp_funding_hyperliquid.py`
                                                                                                  new, `cli/handlers/perp_funding_handler.py`, `cli/main.py`, `tests/unit/test_perp_funding_hyperliquid.py` new) —
                                                                                                  QG green both repos (7560 passed market-tick-data-service; unified-api-contracts full suite green), shipped via
                                                                                                  quickmerge.

- [x] ✅ [DESIGN] P1. **Verified already closed — no action needed.** Checked
      `plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`: its
      `[DESIGN] P1` "demote perp_funding to a derived view" todo is already marked
      `[x] ✅ CLOSED 2026-07-28 — "keep     both"`, citing exactly this doc's parity findings (HYPERLIQUID 60.7% match,
      parity FAILS) as the closing evidence — the cross-reference this todo asked for was made when that doc's todo
      itself closed, and that doc's own header banner already reads "🟢 RESOLVED 2026-07-28 — all todos shipped; the
      DESIGN gate closed as KEEP BOTH". Nothing further to do here.
- [ ] [DIAG] P2. Determine whether `derivative_ticker.predicted_funding_rate` (the asset_ctxs `premium` column,
      currently unused in this comparison) tracks `perp_funding.funding_rate` more closely than `funding_rate` does — if
      Hyperliquid's realized hourly rate is actually closer to a smoothed/clamped function of the premium than to the
      raw per-minute funding snapshot, this would change which derivative_ticker column is the right proxy. Repo:
      market-tick-data-service (read-only re-run of the same parity script with `--dt-column predicted_funding_rate` or
      an ad-hoc variant).

## Progress log

- **2026-07-30 (slot-13, data_engineering, AO dispatch)**: Actioned the `[DESIGN] P1` close-out todo. The referenced
  todo in `plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` was
  already closed `[x]` 2026-07-28 ("keep both") citing this doc's own parity findings — the cross-reference this todo
  asked for had already happened at that doc's own close-out. No code/doc change needed there; flipped this todo done.
  Remaining open work on this doc: the `[DIAG] P2` predicted_funding_rate re-check.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - operator RULED 2026-07-28 (reverse the retirement); all
  3 todos are bounded registry/close-out/read-only-reprobe work

- **2026-07-28 (gated-decision retag sweep)** — Applied the operator's general-theme ruling: reverse the 2026-07-08
  `perp_funding` retirement for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC and resume dedicated capture, since the
  "byte-identical" premise it was retired on is now disproven and the data is not proven unobtainable
  (adaptors-finished-unless-proven- unobtainable theme). Retagged the operator todo to `[DATA]` with the ruling +
  reasoning + a full-completion mandate (all three venues, no partial fix) written in; unblocked the dependent
  `[DESIGN]` close-out todo, which was only waiting on this decision. Docs-only, no code/UAC change made.
- 2026-07-28 (slot-6, data_engineering): Filed from the `defi_satellite_ao_dispatch_batch1_2026_07_25.md` funding-parity
  todo's own findings-triage instruction. Script:
  `market-tick-data-service/scripts/one_offs/defi_perp_funding_derivative_ticker_parity_check_2026_07_28.py` (read-only,
  lifecycle-marked). Full report appended to the source issue doc's Progress log
  (`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`).

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY candidate PARKED on conflict-check:
  `aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md` (active, planning) still asserts the
  "funding rate is byte-identical to derivative_ticker's funding_rate" premise that THIS doc's measurement disproves
  (60.7% match, worst case 10x the signal). Contradictory claims on the same ground - operator ruling needed, not a
  silent flip. Filed as BLOCKED-OPERATOR-DECISION in this run's Deferred list; `assigned_vm` unchanged.
- **✅ RESOLVED 2026-07-31** (corpus-wide ownership-conflict sweep): **no new ruling was needed — the operator had
  already ruled on 2026-07-28** to REVERSE the retirement, per this doc's own `[DATA] P1` (already `[x]`, retagged from
  `[OPERATOR]`). The 2026-07-30 audit entry above treated a settled decision as still-open, which is what kept it
  parked. The aster doc's stale premise has now been corrected in place: a dated PREMISE CORRECTION banner sits above
  its Finding 1, records this doc's measurement (60.7% / p90 5.6e-5 / worst case 1.2e-3), states the retirement is being
  reversed, and separates what in Finding 1 is still mechanically true (the retired path is not yet restored, so
  `--perp-protocols aster` would still write false `attempted_failed` rows today) from what is not (that
  `derivative_ticker` is an equivalent substitute). No checkbox was flipped in either doc — the reversal itself is still
  work in flight, and the aster doc's own open todo is an unrelated, genuinely operator-gated genesis-date question.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
