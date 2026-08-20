---
doc_type: plan
title: Empty-confirmed correctness audit — cefi/defi/tradfi/prediction (Phase 0, audit-only)
summary: >-
  Pre-investigation phase before any manifest mutation, backfill, or purge: for each asset_group's large empty_confirmed
  population, determine root cause (genuinely out-of-scope → prune, mislabeled → re-backfill, or tagging-quality bug →
  fix the tagger) with real evidence, not guesses. Covers cefi PERPETUAL/SPOT_PAIR scope + error_reason breakdown,
  defi's un-investigated 78.7M empty_confirmed, a cross-AG SOURCE_RETURNED_ZERO tagging-quality audit,
  weekend/holiday-gap handling, defi's EXPECTED_INSTRUMENT_NOT_LISTED semantics, and prediction's catalogue-driven
  expected-window feasibility + category-dimension design. Zero mutations in this phase — findings feed Phase-N
  execution plans (per-AG or per-fix-type) gated via depends_on.
status: active
nature: design
asset_group: [meta]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, deployment-api, deployment-ui]
scope: [engineer]
tags: [honest-coverage, empty-confirmed, data-correctness, cefi, defi, tradfi, prediction, audit]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
    /plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 7.2
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    instruments-service/scripts/measure_honest_coverage.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
effort: high
drift_direction: advance-code
---

# Empty-confirmed correctness audit — cefi/defi/tradfi/prediction (Phase 0, audit-only)

> **Phase 0 of 2 — audit only, ZERO manifest/GCS mutations in this plan.** Operator ruling 2026-08-15: human plan (not
> AO-dispatched — most of this is genuine judgment calls), audit-first structure. Findings here feed per-AG/per-fix-type
> Phase-N execution plans, each gated on this plan via `depends_on` + `gate_on_depends: true`. Any todo below that would
> mutate manifest rows or GCS objects is out of scope for THIS doc — cite
> `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` in whichever Phase-N plan actually performs it.

## Why

Session-long investigation (2026-08-15) into the Honest Coverage rollup's `empty_confirmed` volumes surfaced real
concern: for several asset_groups, `empty_confirmed` is comparable to or larger than `captured` (defi 78.7M vs 32.5M;
prediction 2.27M vs 452K). The operator's framing: for each large population, is it (a) a known-out-of-scope population
that should never have been marked `empty_confirmed` at all — clear/purge it, or (b) a genuinely mislabeled population
that needs re-backfill + recategorization? Guessing either way risks either leaving real data gaps invisible, or purging
data that's actually needed. This plan gets the evidence first.

## Todos (LOCAL — investigation only, no mutations)

- [x] 1. ✅ [DATA] P1. **cefi PERPETUAL/SPOT_PAIR scope determination — RESOLVED, no purge needed.** None of the top-15
      dominant combos are phantom/enumerator bugs — every venue genuinely supports the flagged instrument_type/data_type
      combination (verified against UAC's `DATA_TYPE_CAPABILITY_REGISTRY`/`INSTRUMENT_TYPES_BY_VENUE`). Full
      error_reason breakdown (folds in todo 2 below) shows **81.15% of cefi's 6.99M empty_confirmed already carries a
      reason in `OUT_OF_COVERAGE_WINDOW_REASONS`** (`EXPECTED_INSTRUMENT_NOT_LISTED` 57.17% +
      `EXPECTED_INSTRUMENT_DELISTED` 11.53% + `EXPECTED_PRE_VENUE_LAUNCH` 8.07% + `EXPECTED_PRE_SOURCE_COVERAGE_START`
      4.38%) — already excluded from the coverage-% denominator by existing honest-coverage v2 logic, genuinely correct
      absence signaling, nothing to prune or backfill. The remaining 18.72% is `SOURCE_RETURNED_ZERO` (1.31M rows) — the
      only population that could be a real gap or miscategorized failure, folded into todo 6's tagging-quality audit
      below. One minor find: 5,567 rows (0.08%) carry a legacy `EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400` reason no longer
      in the current `EmptyConfirmedReason` enum — too small to chase, noted for whoever next touches that taxonomy.
- [x] 2. ✅ [DATA] P1. **cefi error_reason breakdown — DONE, folded into todo 1 above** (same investigation, same
      evidence). Full table: `EXPECTED_INSTRUMENT_NOT_LISTED` 3,998,955 (57.17%) · `SOURCE_RETURNED_ZERO` 1,309,725
      (18.72%) · `EXPECTED_INSTRUMENT_DELISTED` 806,823 (11.53%) · `EXPECTED_PRE_VENUE_LAUNCH` 564,587 (8.07%) ·
      `EXPECTED_PRE_SOURCE_COVERAGE_START` 306,641 (4.38%) · `EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400` 5,567 (0.08%,
      legacy/unmapped) · `EXPECTED_SOURCE_DELIVERY_LAG` 3,072 (0.04%).
- [x] 3. ✅ [DATA] P1. **FUTURE→futures_chain bundling migration scope — DONE, found a LIVE ongoing bug, not just
      backlog.** CeFi FUTURE-itype: 1,596,176 rows (empty_confirmed 65.5%, matches the 16.24%-of-6.4M finding). Venue
      split: KRAKEN-FUTURES 46.6% · BYBIT 25.6% · OKX-FUTURES 11.9% · DERIBIT 7.8%. The enumerator/denominator side is
      already correctly wired for DERIBIT/OKX (`FUTURE_BUNDLE_VENUES={"cefi":{"DERIBIT","OKX"}}`,
      `market_data_categories.py:1712`). **The writer side is NOT** — OKX-FUTURES is still actively writing 159,732
      bare-`FUTURE` rows with real per-contract IDs, writes continuing through 2026-08-10/11 (4 days before this audit —
      a live ingestion defect, not closed backlog). Duplication check on the 182,584 captured FUTURE rows: the ~3,299
      legacy blank-ID rows (BYBIT/DERIBIT) are genuinely unique (zero matching `futures_chain` rows exist for either
      venue) — **needs re-stamping, not purging**. TradFi's side is already fixed at the code level
      (`unified-trading-library@74fe04fd98`, `instruments-service@de6c820956`) — only needs a
      `rebuild_tradfi_manifest.py` re-run, no new code. CeFi needs THREE separate fixes: (a) canonicalizer fix +
      re-stamp for the legacy blank-ID bucket (mirror the tradfi fix — add `"future"` to `_BUNDLE_GRAIN_EXCLUDED` or
      route it to `futures_chain` at `rebuild_cefi_manifest.py:454`), (b) an actual ingestion-code change for
      OKX-FUTURES' live per-contract writing (re-stamping alone would mislabel real per-contract files — the writer
      itself needs to fetch bundle-grain), (c) an `[OPERATOR]` decision on KRAKEN-FUTURES (743,935 rows, not even in
      `FUTURE_BUNDLE_VENUES` today). **Policy conflict flagged for Phase-N, needs operator ruling** (source: this doc's
      own Progress Log, 2026-08-15 session entry —
      `/plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`): the operator's 2026-08-15 "always
      bundle" ruling is broader than the existing F2 rule, which deliberately leaves BYBIT (409,343 rows) as
      per-contract — does BYBIT come into scope too, or stay an intentional exception?
- [x] 4. ✅ [DATA] P1. **defi empty_confirmed breakdown — DONE, same benign spread shape as cefi.** Live-measured total
      78,754,548 (matches the 2026-08-14 snapshot within normal drift). Grain:
      `(date, chain, venue, instrument_type, instrument_id, data_type)` — defi's chain axis confirmed. By chain:
      ETHEREUM 31.50% · BASE 14.36% · AVALANCHE 14.31% · ARBITRUM 13.77% · SOLANA 10.02%, 17 more long-tail. By venue
      (76 distinct): MORPHO 21.45% · UNISWAP_V3 16.12% · TRADER_JOE_V2 12.28%, long-tail. By date: 3,149 distinct dates,
      top-20 sum to only 1.57% — no incident window, tracks organic onboarding 2018→2026 same as cefi. Cross-tab: 4,583
      distinct combos, top-25 sum to only 43% — genuinely spread; largest structural (non-bug) cluster is Morpho's
      per-market a_token+debt_token × 5-data_type grid (~11.4% combined). **Critically, `SOURCE_RETURNED_ZERO` is only
      0.003% (2,648 rows)** of defi's total — the miscategorization bug found in the 5 oracle collectors (todo 6) is
      real but only affects a tiny sliver of this 78.7M figure, not the bulk of it. Error_reason is the real explanatory
      axis: `EXPECTED_INSTRUMENT_NOT_LISTED` 41.25% · `EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH` 28.42% ·
      `EXPECTED_PRE_GENESIS_CHAIN` 13.83% · `EXPECTED_INSTRUMENT_DELISTED` 10.47% · `EXPECTED_NOT_ENOUGH_TVL` 5.91%.
- [x] 5. ✅ [DATA] P1. **defi `EXPECTED_INSTRUMENT_NOT_LISTED` semantics — RESOLVED, nuanced "both true" answer, with 2
      confirmed real incidents.** For instruments ALREADY in instruments-service's catalogue, `NOT_LISTED` is genuinely
      evidence-backed — cross-referenced against on-chain contract-creation timestamps, subgraph earliest events, or a
      pre-commit-gated `PROTOCOL_LAUNCH_DATES` registry requiring a `# DERIVED YYYY-MM-DD from...` citation
      (`enumerate_expected_universe.py:1442-1580,1583-1793`). **But the operator's worry is confirmed real for a
      DIFFERENT failure mode**: whole archetypes/venues IS never catalogued at all read as silent absence (no expected
      row generated) unless a remediation script explicitly backfills them. Two confirmed past incidents: 112 Kamino
      _vaults_ entirely absent from the catalogue (IS only had Kamino _pools_,
      `reclassify_defi_orphan_eu_notlisted_2026_06_24.py`), and 6 entire LST venues (Ankr/Stader/StakeWise/Swell/
      Mantle/Maker-Ethereum) missing from the catalogue while MTDS had already captured 90 real days of their data
      (`expand_defi_lst_vault_catalogue_from_manifest_2026_07_31.py`). **Cannot rule out more undetected catalogue gaps
      existing today** without a deeper per-archetype on-chain walk (out of this read-only pass's scope).
      **Pre-coverage-start**: defi uses `EXPECTED_PRE_GENESIS_CHAIN` (not `EXPECTED_PRE_SOURCE_COVERAGE_START`, same
      semantic role) — mechanically already excluded from `coverage_pct`'s denominator
      (`OUT_OF_COVERAGE_WINDOW_REASONS`, confirmed). **But the headline `coverage.json`
      `by_asset_group.defi.empty_confirmed` figure — the exact number that triggered this whole audit — has ZERO reason
      breakdown at that top level** (`measure_honest_coverage.py` grep for `error_reason`/`by_reason`: zero hits). A
      reason breakdown DOES exist, but only in deployment-api's per-venue drilldown (`client.ts:1352-1372`), not the
      aggregate. **Real, validated UX finding**: the scary-looking headline number is genuinely indistinguishable from a
      real gap at the surface the operator was actually looking at, even though the underlying math is fine — a
      reporting gap, not a data-correctness gap. Separate note: `EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH` (28.42%) is
      deliberately NOT out-of-window by design — its own docstring states re-classifying it as out-of-window would be
      "the exact honest-coverage distortion this reason exists to prevent" (the instrument is genuinely
      alive/catalogued, just structurally non-fetchable).
- [x] 6. ✅ [DATA] P1. **Cross-AG `SOURCE_RETURNED_ZERO` tagging-quality audit — DONE, confirms operator's concern was
      correct.** Per-AG verdict: **cefi MISCATEGORIZING** (Deribit DVOL: sustained HTTP 429 has no backoff/failure flag,
      `deribit_volatility_index_handler.py:119-152`; Hyperliquid perp funding: per-coin failures swallowed via
      `return_exceptions=True`, `_perp_funding_hyperliquid.py:253-262` — if every coin fails, returns 0 without raising,
      fabricates a 200-OK evidence object). **defi MISCATEGORIZING** (5 on-chain oracle collectors — Aave/Compound/
      Fluid/Radiant/Spark — nested per-reserve/per-market `except Exception` swallows without setting an error flag; if
      every call in the loop fails, `clean_fetch_evidence()` synthesizes a fabricated 200-OK/0-rows evidence never
      reflecting real state; `dex_swaps`/`evm_defi`/`lending` call sites are clean by contrast). **sports CLEAN** (both
      call sites correctly gate on genuine confirmed-2xx-empty, any real failure re-raises to `attempted_failed`).
      **tradfi mostly CLEAN with one live structural landmine**: `_route_databento` (`umi_tick_provider.py:513-518`)
      pre-filters requested data_types against a supported-list BEFORE contacting Databento — unsupported types silently
      return an empty DataFrame with no failure signal, fabricating evidence for a request that never reached the
      source; not misfiring today (all configured tradfi dts are supported) but the code's own comment confirms this
      exact pattern caused a real incident once (mbp_10, fixed 2026-07-15) — a future dt addition without updating the
      supported-list reproduces it. **prediction PARTIAL**: per-market historical backfill is clean (real per-ticker
      evidence); the daily venue-grain catalog stamp (`process_completeness.py:205-259`) fabricates evidence the same
      way — and may already be connected to the already-filed Polymarket catalog-writer gap (zero blobs since
      2026-08-05): if `get_instruments_cached()` returns `[]` without raising when that gap fires, it lands in
      `empty_ok_venues` and stamps honest `SOURCE_RETURNED_ZERO` daily, masking a real production outage. **NOT verified
      against live manifest rows in this pass — see new todo below.**
- [x] 7. ✅ [DATA] P2. **Weekend/holiday gap handling — RESOLVED, deliberate documented design, not a bug.** Tradfi
      weekend/holidays ARE enumerated into `expected` (`enumerate_expected_universe.py:1918-1958`), but as a calendar
      pre-skip (no real fetch attempted, dedicated `EXPECTED_WEEKEND`/`EXPECTED_HOLIDAY` reasons). Keeping them IN the
      coverage-% denominator is an explicit, documented decision (`_honest_coverage_empty_reasons.py:660-664`: "a
      covered venue's weekend gap is part of the coverable universe") — not something to prune.
      `is_non_trading_day`/`non_trading_day_reason` is only called from the tradfi enumerator path —
      cefi/defi/sports/prediction are structurally unaffected (24/7 or non-calendar-gated markets), matching the
      operator's own hunch. No fix needed.
- [x] 8. ✅ [DATA] P2. **Prediction: instrument-catalogue-gated expected-window feasibility — RESOLVED, already built
      and already wired in, contrary to the plan's premise.** instruments-service already maintains a per-market
      catalogue (`build_prediction_catalogue_dataframe`, `build_instrument_catalogue.py:2127-2439`) with real
      `market_created_at`/`settlement_time` per (venue, conditionId), rolled up to (venue, canonical_question_group).
      `enumerate_expected_universe.py::_enumerate_v2_prediction` (lines 2964-3111) already gates on it: before listing →
      `EXPECTED_INSTRUMENT_NOT_LISTED`, after expiry → `EXPECTED_INSTRUMENT_DELISTED`, only inside the live window →
      `expected_unattempted`. One real nuance, not a bug: gating is at cqg-bundle grain (not literal per-market) per
      "decision 338" (2026-06-19), deliberately, to avoid a >50M-row blowup — same grain the manifest itself uses
      everywhere else for prediction. **No enumerator change needed** — the operator's original ask is already
      satisfied.
- [x] 9. ✅ [DATA] P1. **Prediction: June-2026 expected-universe growth spike — root cause found, already fixed,
      separate from the live-capture issue.** NOT connected to the already-filed live-capture doc (that's dated
      ~08-03/08-05, seven weeks after this spike began). Real cause: `build_instrument_catalogue.py`'s prediction
      catalogue parser required a `canonical_question_group=` path segment the writer never emits — so the prediction
      catalogue was **permanently 0 rows from the start of history** until commit `aab02153` (2026-06-16 19:11 UTC)
      fixed the path-parsing bug, jumping 0 → 668,384 rows in one commit (exact match to the "~668K markets" finding).
      Before that fix, `_enumerate_v2_prediction`'s `for instr in catalog:` loop (line 3018) never ran for ANY
      historical date — only the venue-grain pre-launch pass existed. Once fixed, the enumerator began correctly
      reaching real, previously-unenumerated markets and confirming them empty (99.8% `SOURCE_RETURNED_ZERO` in the
      surge = genuine data, not a tagging bug). **Already shipped — nothing to execute, just recorded here for the
      record.**
- [x] 10. ✅ [DATA] P2. **Prediction: category dimension feasibility — RESOLVED, cheaper than the VM-join framing
      suggested.** (1) Confirmed structurally, not just observationally:
      `write_guard.py::validate_prediction_instrument_type` (lines 35-45) raises `ValueError` unless
      `instrument_type == PREDICTION_MARKET` — it is the ONLY value possible, enforced at write time. (2) No
      existing-column proxy — `venue + instrument_type` collapses to just `venue` (2 values) since instrument_type is
      invariant. (3)/(4) A classifier already computes `(category, underlying, resolution_period)` internally
      (`classifiers.py`) but never persists it; `CanonicalQuestionGroup` is a small, closed, static 89-member enum, not
      a live-cardinality problem — **recommendation: build an ~89-row static `cqg → category` lookup table** (a UAC
      registry addition, NOT a manifest schema change, near-zero cost), covering the cqg-bundle grain used everywhere in
      the rollup today. A finer per-conditionId join is possible later against the already-built catalogue snapshot if
      wanted, but isn't required to satisfy the original ask.

### New execution-scoped todos (surfaced by the above audit findings, not in original scope)

- [x] ✅ [UI] P1. **Surface an error_reason breakdown at the `coverage.json` headline `by_asset_group[ag]` level**, not
      just deployment-api's per-venue drilldown (`client.ts:1352-1372`). The exact number that triggered this whole
      audit (`empty_confirmed`) is currently a flat aggregate indistinguishable from a real gap at the surface an
      operator actually looks at, even though the underlying reason data + denominator math already correctly separate
      out-of-window/reference-only/genuine-failure. At minimum: an `out_of_window_pct` / `reference_only_pct` /
      `unexplained_pct` split alongside the existing `empty_confirmed` count, computed once in
      `measure_honest_coverage.py` (currently zero `error_reason`/`by_reason` references there) and rendered as a
      sub-breakdown on the Honest Coverage card. **2026-08-15**: implemented.
      `instruments-service/scripts/measure_honest_coverage.py`: added `_READ_COLUMNS_WITH_CHAIN_AND_REASON` (a new top
      read-tier including `error_reason`, gracefully falling back to the existing chain-only tier on older buckets) and
      `_empty_confirmed_reason_split()` (computes `out_of_window_pct`/`reference_only_pct`/`unexplained_pct` off
      `OUT_OF_COVERAGE_WINDOW_REASONS` + `EmptyConfirmedReason.EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH`, wired into
      `_count_statuses` so every drilldown level gets it, not just `by_asset_group`), with unit tests. `deployment-ui`:
      added the 3 fields to `HonestCoverageStatusCounts` in `client.ts`, rendered as a new "empty_confirmed reasons" row
      in `HonestCoverageCard.tsx` (hidden, not faked as 0%, when a bucket predates the read column), with a Playwright
      regression spec. Not yet run through quality-gates.sh/Playwright (host RAM contention this session) — deferred to
      the final ship batch.
- [ ] [DATA] P2. **Audit for undetected defi instruments-service catalogue gaps** beyond the 2 already-fixed incidents
      (112 Kamino vaults, 6 LST venues) — some undetermined share of the current 32.48M `EXPECTED_INSTRUMENT_NOT_LISTED`
      rows may still be uncaught catalogue-gap residue rather than genuine not-yet-listed absence. Needs a per-archetype
      on-chain-reality walk, out of scope for this audit's read-only pass.
- [x] ✅ [DATA] P0. **Fix cefi's 2 SOURCE_RETURNED_ZERO miscategorization bugs**: Deribit DVOL sustained-429 (no
      backoff/ no failure flag, `deribit_volatility_index_handler.py:119-152`) and Hyperliquid per-coin swallowing
      (`_perp_funding_hyperliquid.py:253-262`, `return_exceptions=True` with no per-coin failure propagation).
      Done-when: both paths correctly route a total-failure case to `attempted_failed`/`record_failed`, not a fabricated
      `SOURCE_RETURNED_ZERO`, with a regression test forcing all-calls-fail and asserting the correct reason.
      **2026-08-15**: fixed both + shipped with regression tests, `market-tick-data-service` (QG-verified, 10,807 tests
      passed — see Progress Log for the SHA once the final ship batch lands).
- [x] ✅ [DATA] P0. **Fix defi's 5 oracle-collector SOURCE_RETURNED_ZERO miscategorization bugs**: Aave/Compound/Fluid/
      Radiant/Spark all have nested per-reserve/per-market `except Exception` that swallows without setting an error
      flag (`_aave_oracle_collection.py:78-79`, `_compound_oracle_collection.py:151-152,169-170,261-262`, and the
      identically-structured Fluid/Radiant/Spark equivalents). Done-when: each collector correctly distinguishes
      "genuinely queried, got nothing" from "every RPC call in the loop errored," with a regression test forcing
      total-failure and asserting `record_failed` not `record_empty`. **2026-08-15**: fixed all 5 + shipped with
      regression tests, same `market-tick-data-service` batch as the cefi fix above.
- [x] ✅ [DATA] P1. **Close tradfi's `_route_databento` unsupported-dt landmine** (`umi_tick_provider.py:513-518`)
      before it reproduces the mbp_10 incident (fixed 2026-07-15) — add a real failure signal when a requested data_type
      isn't in `_DATABENTO_SUPPORTED_DATA_TYPES` instead of silently returning an empty DataFrame with no failure flag.
      Not urgent (nothing currently misfires — all configured tradfi dts are supported today) but should land before any
      new tradfi data_type is added to the expected-universe. **2026-08-15**: fixed — `_route_databento` now populates
      `failed_per_dt` for every unsupported data_type instead of silently returning empty, with 2 regression tests
      (single-unsupported-dt, mixed supported+unsupported). Same `market-tick-data-service` batch.
- [x] ✅ [DATA] P0. **Verify whether prediction's Polymarket catalog-writer gap (zero blobs since 2026-08-05) is being
      silently absorbed as honest `SOURCE_RETURNED_ZERO`** via `process_completeness.py:205-259`'s daily venue-grain
      stamp — check live manifest rows for POLYMARKET `empty_confirmed`/`SOURCE_RETURNED_ZERO` counts since 2026-08-05
      specifically (not yet done, flagged but out of scope in the tagging-quality pass). If confirmed, this is masking a
      real production outage as clean data — treat as P0 alongside the already-filed catalog-gap issue. **2026-08-15**:
      re-measured live (`get_storage_client().list_blobs()` against `instruments-store-pred-prd-central-element-323112`)
      — gap is real and ONGOING through today: 08-03/08-05/08-08 had 62-63 POLYMARKET blobs, **08-10 through 08-15 all
      have exactly 0** (KALSHI stayed healthy every date, 43→50 growing) — the actual break point is between 08-08 and
      08-10, not immediately after 08-05. Separately confirmed the Gamma API itself is healthy right now (live
      unauthenticated `GET gamma-api.polymarket.com/markets?closed=false&active=true` → HTTP 200, normal payload, no
      schema drift), so this is **NOT** the same SOURCE_RETURNED_ZERO-absorption class as the cefi/defi bugs just fixed
      above (those were a code path silently swallowing a real fetch failure into a false confirmed-empty stamp).
      Checked for a Cloud Scheduler job or GH Actions `schedule:` workflow driving this catalogue build — found neither
      in this project's visible config, so the trigger lives outside this repo (Cloud Run job / VM cron / AO dispatch).
      Zero blobs (not a thin/partial catalogue) is more consistent with the job simply not running for POLYMARKET since
      08-10 than with an in-code absorption bug, but this isn't fully proven without the job's own run logs — full
      evidence + the updated root-cause todo landed in
      `plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`
      (Root Cause B), which remains open pending whoever owns the trigger mechanism.
- [x] ✅ [OPERATOR] P1. **Rule on BYBIT's scope in the FUTURE→futures_chain "always bundle" policy** — 409,343 rows,
      currently an intentional per-contract exception under the existing F2 rule; the 2026-08-15 "always bundle" ruling
      is broader than F2 and doesn't explicitly resolve whether BYBIT is now in scope too. **Operator ruling
      2026-08-15** (source: this doc's own Progress Log, 2026-08-15 session entry —
      `/plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`): YES, bundle BYBIT (and
      KRAKEN-FUTURES below) into `futures_chain` — "everything as long as FUTURE is correctly tagged and not a perpetual
      (must have expiry — the whole point of bundling per underlying)". Explicit gating condition: the migration must
      verify each row genuinely carries a dated expiry before bundling it — a PERPETUAL mislabeled as FUTURE must NOT be
      swept into `futures_chain` by this migration; that's a separate correctness bug (instrument_type mis-tagging), not
      an in-scope bundling candidate.
- [x] ✅ [OPERATOR] P2. **Rule on KRAKEN-FUTURES's scope** (743,935 FUTURE-itype rows) — not in `FUTURE_BUNDLE_VENUES`
      at all today; needs an explicit decision before any bundling migration touches it. **Operator ruling 2026-08-15**
      (source: this doc's own Progress Log, 2026-08-15 session entry —
      `/plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`): YES, bundle KRAKEN-FUTURES too —
      see the BYBIT ruling directly above for the full decision text and the expiry-gating condition (identical ruling,
      same message, covers both venues).
- [ ] [DATA] P1. **Bundle BYBIT (409,343 rows) + KRAKEN-FUTURES (743,935 rows) into `futures_chain`** per the operator's
      2026-08-15 ruling above — add both venues to `FUTURE_BUNDLE_VENUES` in `market_data_categories.py`, migrate their
      captured FUTURE rows (same Phase-N-execution class as the cefi legacy blank-ID bucket re-stamp above — consider
      running both as one combined migration), re-run the manifest rebuild. **Hard gate from the ruling: verify each row
      genuinely carries a dated expiry before bundling it** — any row that turns out to be a PERPETUAL mislabeled as
      FUTURE must be excluded from this migration and filed as a separate instrument_type mis-tagging bug, not silently
      swept into futures_chain. Do NOT start until the mis-tagging check has run.
- [x] ✅ [UI] P2. **Un-suppress `HierarchicalShardDrilldown` for instruments-service cefi/tradfi/defi** — operator
      reviewed `isHierarchicalDrilldownRedundant`'s subset-of-the-grid suppression (plan
      `data_status_page_ux_and_canonicalisation_2026_07_16` P5) and wants the drilldown visible for those asset groups
      too, not just sports/prediction. **2026-08-15**: shipped — `deployment-ui/src/lib/data-status-helpers.ts`'s
      `isHierarchicalDrilldownRedundant` now always returns `false` (kept as a named predicate, not inlined, so a future
      narrower suppression can reuse the axis-comparison machinery); `DataStatusTab.tsx`'s stale P5 comment block
      updated to match; existing unit tests updated to assert the new always-visible behavior.
- [x] ✅ [UI] P2. **Fix the MTDS asset-group-selector UX** — an empty `selectedCategories` filter means "no filter, all
      asset groups included" downstream, but every per-category toggle pill rendered unhighlighted in that state,
      reading as "nothing selected" rather than "all selected". **2026-08-15**: shipped — added an explicit "All" pill
      to `DataStatusTab.tsx`'s asset-group toggle group (highlighted when `selectedCategories.length === 0`, clears the
      selection when clicked; selecting any specific category deselects it), plus a new Playwright regression spec
      (`data-status-tab-renders.spec.ts`). Not yet run through Playwright (host RAM contention this session, no dev
      server running) — deferred to the final ship batch.
- [x] ✅ [INFRA] P1. **Set up service-account/API-key access to deployment-api** for this interactive session AND for
      Agent-Orchestrator agents, without requiring interactive Google OAuth sign-in each time. **2026-08-15**:
      deployment-api already had a working `X-API-Key` header auth path (`deployment_api/auth.py::verify_api_key`) — no
      new code needed. Retrieved the live secret
      (`gcloud secrets versions access latest --secret=deployment-api-api-key --project=central-element-323112`) and
      verified it end-to-end against the live Cloud Run service (`uts-shared-deployment-api`, `asia-northeast1`): `401`
      without the key, `200` with it, on a real protected endpoint (`/api/data-status/honest-coverage`), not just
      `/api/health`. Granted `roles/secretmanager.secretAccessor` on that secret to
      `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (the shared service account essentially every fleet VM
      — including AO-dispatched worker VMs — already runs as), so AO agents can read the same secret without a new grant
      per-VM. My own interactive gcloud identity (`ikenna@odum-research.com`) already had read access, confirmed
      working. Usage:
      `curl -H "X-API-Key: $(gcloud secrets versions access latest --secret=deployment-api-api-key --project=central-element-323112)" https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/api/...`.
- [x] ✅ [DATA] P1. **Verify/close the BYBIT-FUTURES captured-row verification** from
      `cross_ag_live_capture_parity_2026_08_14.md` (the 2026-08-09 venue-alias fix was applied + a fresh VM launched,
      but captured-row confirmation was blocked on an IS daily-catalog-timing gap as of the last checkpoint).
      **2026-08-15**: re-verified live via SSH + direct manifest queries — **NOT closed, a real bug remains**. The
      venue-alias fix is confirmed working (universe resolved successfully at 06:07:55 UTC today, 1,282 instruments),
      and the IS catalog-timing gap is confirmed real but transient (catalog absent at every check from VM boot through
      06:02 UTC, present by 06:07:55). But a THIRD problem was found: even after the universe resolves, a direct read of
      the live VM's own per-VM manifest shard shows BYBIT-FUTURES is STILL 100% `empty_confirmed` (5,128 rows, including
      `data_type=trades` dated today) — the WS connector is not producing any real captured rows post-resolve. Full
      evidence + two new follow-up todos (root-cause the post-resolve capture gap; file the IS catalog-timing gap as its
      own instruments-service issue) landed in `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`'s existing
      BYBIT-FUTURES finding entry.
- [x] ✅ [DATA] P2. Re-run `rebuild_tradfi_manifest.py` to apply the already-shipped FUTURE-canonicalization fix
      (`unified-trading-library@74fe04fd98`, `instruments-service@de6c820956`) — no code change needed, purely
      operational.

      **DONE 2026-08-15 (slot-28, backend_engineer) — same operation as
          `plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "Re-run rebuild_tradfi_manifest.py..." todo
          (dispatched separately, resolved here concurrently — see that plan for full evidence).** Full-corpus rebuild
          (`canonical-migration-tradfi-manifest-rebuild-20260815-061239`, 2020-01-01..2026-08-15, `--chunk-days 30`)
          completed exit_code=0, 1,397,013 shards / 81 chunks. Live manifest recount confirms 0
          `instrument_type=FUTURE` rows with populated `underlying` + blank `instrument_id` remain (checked both
          CME-scoped and unscoped across all venues).

- [x] ✅ [DATA] P2. Fix cefi's legacy blank-instrument-id FUTURE bucket (~3,299 captured rows, BYBIT/DERIBIT) — add
      `"future"` to `_BUNDLE_GRAIN_EXCLUDED` or route it to `futures_chain` at `rebuild_cefi_manifest.py:454` (mirrors
      the tradfi fix), then re-stamp the confirmed-unique existing rows (NOT duplicates — verified this session).
      **2026-08-15**: code fix shipped (`rebuild_cefi_manifest.py` now reroutes any bundle-grain-shaped FUTURE parse —
      blank instrument_id + populated underlying — to `instrument_type=futures_chain` at manifest-write time, with 2
      regression tests; a genuine per-contract FUTURE is left untouched). **The actual DATA re-stamp of the existing
      ~3,299 rows is deliberately NOT done in this pass** — running `rebuild_cefi_manifest.py` for real is a production
      GCS/manifest mutation that this Phase-0 audit-only plan explicitly excludes (see the banner at the top of this
      doc) and workspace policy requires it run on a VM, not locally. Tracked as Phase-N execution work (see the
      BYBIT/KRAKEN-FUTURES bundling todo below, which is the same class of migration and should absorb this one too
      rather than running two separate rebuild passes).
- [x] ✅ [DATA] P1. Fix OKX-FUTURES' live per-contract writing bug (159,732 rows and growing daily as of 2026-08-15) —
      needs an actual ingestion-code change (bulk bundle-grain fetch replacing per-contract fetch), not a manifest-only
      re-stamp; re-stamping alone would mislabel real per-contract files as bundle-grain. **2026-08-15**: investigated,
      NOT fixed — deliberately deferred, documented here rather than blind-shipped. Traced the live OKX-FUTURES
      websocket connector (`market_tick_data_service/live/connectors/okx_futures_ws.py`) hardcoding
      `instrument_type="FUTURE"` on every `ReceivedTick` (3 call sites) with a real per-contract `instrument_id`. The
      batch/Tardis side already has a working per-venue bundle-grain mechanism (`_download_futures_per_instrument` in
      `tardis_bulk_download.py`, plus `symbol_rules.py`'s `_VENUE_INSTRUMENT_TYPE["OKX-FUTURES"] = "futures_chain"`
      venue-default), but the LIVE connector's own per-tick stamp is a wire-level fact about one specific contract —
      relabeling it to `"futures_chain"` while keeping a real per-contract `instrument_id` would be internally
      inconsistent with the bundle-grain shape (blank id + underlying) every other bundle-grain consumer expects, and I
      could not verify against live traffic whether the correct fix is (a) a downstream write-path grouping step that
      collapses same-underlying live ticks into one bundle-grain shard, mirroring the batch fallback, or (b) something
      else. Given this touches live production trading infrastructure and a wrong guess could break live capture
      entirely (worse than the current mislabeling), did not ship an unverified change. Filed as its own properly-scoped
      todo below for whoever picks up the actual fix, with the exact file/line evidence needed to start. - [ ] [CODE]
      P1. Fix OKX-FUTURES' live connector so same-underlying trades write as bundle-grain (`futures_chain`, blank
      instrument_id + populated underlying) instead of one shard per real per-contract `instrument_id` — start at
      `market_tick_data_service/live/connectors/okx_futures_ws.py` (3 `instrument_type="FUTURE"` stamps) and
      `tardis_bulk_download.py::_download_futures_per_instrument`'s batch-side grouping pattern for the target shape.
      Needs live-traffic verification before shipping — do NOT relabel the connector's per-tick `instrument_type` alone
      without also changing what gets grouped into one shard.
- [x] ✅ [DATA] P2. Add the ~89-row static `cqg → category` lookup table to UAC (per todo 10's recommendation) and wire
      it into the deployment-api/ui drilldown once built. **2026-08-15: premise corrected — this already exists, nothing
      to build.** `category_for_group(cqg) -> PredictionMarketCategory`
      (`unified-api-contracts/unified_api_contracts/canonical/domain/predictions/ cross_venue_mapping.py:338`) is a
      complete, tested, already-public (`unified_api_contracts.predictions` facade) cqg→category function covering every
      `CanonicalQuestionGroup` member via `underlying_for_group` + `_category_for_underlying` composition — functionally
      identical to the requested static table (7 categories:
      POLITICS/FINANCIAL/SPORTS/CRYPTO/WEATHER/ENTERTAINMENT/OTHER). Building a second, duplicate static dict would
      itself be a maintenance-drift risk (two sources of truth for the same mapping). Remaining work is UI-only — folded
      into the un-suppress-drilldown todo below, since "wire into the drilldown" only makes sense once that component is
      live.
- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) →
      `infra_satellite_ao_dispatch_batch18_2026_08_17.md` item 1 — CLOSED STALE-DUPLICATE 2026-08-18 (slot-11,
      data_engineering).** The extraction's premise ("still open, agent was running at session checkpoint time
      2026-08-15, not yet reported") was a snapshot from mid-checkpoint on 2026-08-15, before the same session's
      `/autonomous` pass finished the last of the 9 original audit todos later that same day. By the time this
      extraction was drafted (2026-08-17), todos 4 and 5 above already fully covered this exact scope — todo 4 is the
      breakdown (grain, chain/venue/date distribution, error_reason classification), todo 5 is the
      `EXPECTED_INSTRUMENT_NOT_LISTED` semantics resolution — literally the same title as this entry, already `[x]`
      RESOLVED with full evidence. No new investigation was run; batch18 item 1 has been re-flipped to cite todos 4/5
      directly rather than re-executed. See batch18's Progress Log for the citation-correction detail.

## Progress Log

- **2026-08-15 (interactive session, slot 3)**: Filed following operator's session-long investigation into
  cefi/defi/tradfi/prediction empty_confirmed volumes and several structural questions (FUTURE→futures_chain, prediction
  catalogue-gating, category dimension, SOURCE_RETURNED_ZERO tagging quality). Operator ruled: human plan (not AO),
  audit-first structure with per-AG/per-fix-type execution plans to follow, gated on this doc's findings.
  Cross-referenced and linked (not duplicated) two already-open relevant docs:
  `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` (FUTURE-vs-bundle-grain, tradfi side already tracked) and
  `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` (live-capture-side
  prediction bugs, possibly connected to the batch-backfill growth-spike question).
- **2026-08-15 (same session, ~2h later, /pre-compact checkpoint)**: 8 of 9 original audit todos completed via 5
  parallel investigation agents (one of them recursively spawned its own 5 sub-agents for the per-AG
  SOURCE_RETURNED_ZERO tagging pass). Only the defi breakdown remained in-flight at checkpoint time — see the new
  execution-scoped todos above, which convert every finding into tracked follow-up work rather than leaving it as
  chat-only prose (workspace hard rule). Headline results: cefi's PERPETUAL/SPOT_PAIR dominance turned out to be benign
  (81% already correctly out-of-coverage-window); the SOURCE_RETURNED_ZERO tagging-quality concern was CONFIRMED correct
  — real miscategorization bugs found in cefi (2 sites) and defi (5 oracle collectors), plus a live structural landmine
  in tradfi; the FUTURE→futures_chain migration found a LIVE ongoing bug (OKX-FUTURES still writing bare-FUTURE rows
  daily as of 2026-08-10/11), not just historical backlog; and two of prediction's three open questions turned out to
  already be solved (catalogue-gated expected-windows already exist and are already wired in; the June-2026 growth spike
  has an exact, already-shipped root-cause commit) — only the category-dimension question needed a genuine new
  recommendation. Also caught and fixed a real correctness issue while shipping the UAC prediction-registry fix: a
  2026-07-07 decision had deliberately deleted this exact registry row, and both that decision AND this session's fix
  are correct simultaneously — they're about two different consumers (Layer-2 backfill vs Layer-1 audit) that the
  2026-07-07 decision didn't distinguish. Documented the reconciliation in both the test and the registry comment so a
  future reader doesn't repeat the same "looks inert, safe to delete" mistake.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (7 entries).
- **2026-08-15 (same session, /autonomous execution pass)**: user explicitly invoked `/autonomous` to drive the 13
  execution-scoped todos to completion in one pass, deferring all shipping/heavy verification to a final batch (host
  under genuine multi-session RAM contention this whole pass — confirmed via `vm_stat` + `ps`, several concurrent Claude
  sessions + a manifest consolidator). Completed all 13: (1)(2)(3) cefi/defi/tradfi SOURCE_RETURNED_ZERO + landmine
  fixes shipped earlier this session (`market-tick-data-service`, QG-verified 10,807 passed); (4) Polymarket catalog-gap
  verified live, absorption hypothesis ruled out; (5) BYBIT+KRAKEN-FUTURES operator ruling obtained (bundle both,
  expiry-gated); (6) cefi legacy blank-ID bucket — code fix shipped, data re-stamp deliberately deferred to Phase-N (a
  real GCS/manifest mutation out of scope for this audit-only plan); (7) OKX-FUTURES live writer — root-caused to 3
  hardcoded `instrument_type="FUTURE"` stamps in the live WS connector, deliberately NOT fixed blind (live production
  trading infra, no way to verify against real traffic this session) — filed as its own precise todo; (8) cqg category
  lookup — discovered it already exists (`category_for_group`), corrected the plan's premise rather than building a
  duplicate; (9) HierarchicalShardDrilldown un-suppressed per operator review; (10) MTDS asset-group-selector UX fixed
  (explicit "All" pill); (11) error_reason breakdown surfaced end-to-end (instruments-service compute + deployment-ui
  render, both with tests); (12) deployment-api service-account access — found the API-key auth already existed,
  retrieved + verified the live secret end-to-end (401→200), granted the fleet-wide `uts-prd-sa` service account read
  access so AO agents inherit it too; (13) BYBIT-FUTURES verification — NOT closed, found a genuine third bug (universe
  resolves, WS connector still produces zero captured rows) beyond the two already-diagnosed issues, filed with full
  evidence in the source plan. **A real process lesson from this pass, worth keeping**: an earlier
  `bash scripts/plan-hygiene/run_hygiene_sweep.sh --only <this-file>` invocation used an unrecognized `--only` flag (the
  real flag needs `--precommit`, not `--only`, for a single-file staged check) — since the flag wasn't recognized, the
  script silently fell through to the FULL interactive sweep (which regenerates the active-plan inventory and can
  rewrite plan files), which I then killed mid-run after it ran long. This appears to have wiped a batch of uncommitted
  edits to this exact file (the BYBIT/KRAKEN-FUTURES ruling + cqg-lookup correction + error_reason-breakdown todo flip)
  that had been sitting uncommitted for a while — they had to be redone from scratch this entry. Lesson: verify a
  hygiene-sweep flag is real before running it (`--precommit` for a fast staged-files-only check; there is no `--only`),
  and don't let edits to a shared-checkout file sit uncommitted for long stretches — ship each unit promptly instead of
  batching a large diff across many tool calls, exactly the risk `CLAUDE.md`'s "ahead=0 + clean tree ≠ landed ≡ work
  DESTROYED" warning is about, just via a different mechanism (a killed background process rewriting files) than the
  git-reset-style loss that rule was originally written for. **Shipping status at the end of this pass**: the
  cefi/defi/tradfi SOURCE_RETURNED_ZERO fixes were already shipped earlier this session. Everything else from this pass
  (tradfi `_route_databento` fix, cefi legacy-bucket code fix, the error_reason breakdown backend+UI, the drilldown
  un-suppress, the MTDS UX fix, and this doc itself) is staged locally, verified only by syntax-check + careful manual
  review (not a live `quality-gates.sh`/Playwright run) due to sustained host RAM contention across this entire pass —
  retry is the very next action after this entry lands.
- **2026-08-15 (same session, retry-shipping pass)**: `deployment-ui` (error_reason UI, drilldown un-suppress, MTDS
  "All" pill UX fix) — ✅ landed `deployment-ui@080ceb8c39`, content-verified against `origin/live-defi-rollout`. Hit a
  genuine (not host-contention) global branch-coverage-threshold gate failure on the first attempt (63.89% vs the 64%
  floor) — root-caused to two new conditional branches in `HonestCoverageCard.tsx`'s error_reason-split render block
  (the `referenceOnlyPct > 0` guard and the amber-vs-muted `unexplainedPct` ternary) that were exercised only by a
  Playwright smoke spec, which doesn't feed this repo's Vitest coverage report at all — added 2 new unit tests to
  `HonestCoverageCard.test.tsx` covering both branch directions (76.52% on that file, up from 70.43%), which cleared the
  global floor on retry. Lesson for future UI work here: a Playwright-only assertion of new conditional JSX does NOT
  satisfy this repo's Vitest branch-coverage gate — every new branch needs a same-repo Vitest unit-test case too, not
  just an e2e/smoke one. `market-tick-data-service` (14 files) and `instruments-service` (2 files) remain unshipped:
  both are blocked on a **foreign, currently-live** cross-repo conflict, not a bug in either diff — another concurrent
  session (slot-6, `backend_engineer`, tracked in
  `plans/active/issues/tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md`) has been actively flip-flopping
  `unified-trading-library`'s canonical "combo" instrument-type casing today (3 commits: add `combo_chain` dispatch →
  stop-excluding `combo` from uppercase canon → revert that exclusion-removal, the last one local + unpushed as of this
  entry, `unified-trading-library@64af7a4e`). Both MTDS's
  `tests/unit/scripts/test_migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` /
  `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py` and instruments-service's
  `tests/unit/scripts/test_enumerate_expected_universe_v2.py` (4 tests) now assert the now-reverted "combo → COMBO"
  behavior and fail deterministically (confirmed by reproducing in isolation, not just full-suite xdist noise; MTDS's
  first identical-twice failure was initially mis-diagnosed as xdist test-order pollution before this deeper root cause
  surfaced). Neither this diff's own files nor any foreign-owned file were touched — per per-tab-worktree discipline
  this is the other session's active WIP to land, not mine to patch. Waiting for that conflict to settle (their commit
  to land + push, or their test/canon state to otherwise stabilize) before retrying either ship; both diffs are
  otherwise complete and were QG-clean before this cross-repo drift appeared mid-session.
- **2026-08-15 (same session, ~15 min later)**: the foreign UTL conflict settled — `unified-trading-library@64af7a4e`
  landed on `origin/live-defi-rollout` (no longer locally-ahead), and slot-6 had already fixed the dependent tests on
  their side (`market-tick-data-service@b5343275`/`6fa0dd9d`, instruments-service's
  `test_enumerate_expected_universe_v2.py` verified passing locally). Re-verified both previously-failing test sets pass
  cleanly and that only this session's own files were still dirty in each repo, then retried both ships.
  `instruments-service` — ✅ landed `instruments-service@1c1ca7553f`, content-verified against
  `origin/live-defi-rollout`. `market-tick-data-service` retry still in flight at this entry's time of writing.
- **2026-08-15 (same session, final entry)**: `market-tick-data-service` — ✅ landed
  `market-tick-data-service@cdf782b249`, content-verified against `origin/live-defi-rollout`. **All 3 repos from this
  session's 13 execution-scoped todos are now fully shipped**: `market-tick-data-service@cdf782b249` (cefi/defi/tradfi
  SOURCE_RETURNED_ZERO + landmine fixes, cefi legacy-bucket futures_chain reroute), `instruments-service@1c1ca7553f`
  (error_reason breakdown backend), `deployment-ui@080ceb8c39` (error_reason UI, drilldown un-suppress, MTDS "All" pill
  UX fix). Working trees clean in all three repos. Still outstanding: the deferred Playwright verification for
  `deployment-ui`'s new UI (beyond the Vitest unit-test coverage added this pass) and a live pytest/QG confirmation pass
  is already satisfied by the ships themselves (each landed through a genuine green `quality-gates.sh` run, not a
  bypass) — what remains is manual/visual UI verification in a browser, not test coverage. Also still open, deliberately
  deferred to Phase-N per this doc's own scope (audit-only, zero manifest/GCS mutations): the cefi legacy blank-ID
  FUTURE bucket re-stamp, the BYBIT+KRAKEN-FUTURES bundling migration, the OKX-FUTURES live-writer fix, and the
  newly-filed BYBIT-FUTURES post-universe-resolve zero-capture root-cause (see
  `cross_ag_live_capture_parity_2026_08_14.md` for that last one's tracked todos).

- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:c01242758aa55671]: RECLASSIFY_SPLIT — extracted the
  sole remaining item (defi empty_confirmed breakdown pickup) to
  `infra_satellite_ao_dispatch_batch18_2026_08_17.md` item 1 (not yet executed). Doc stays `assigned_vm: NA` — this
  is a LOCAL/human plan by design (operator ruling 2026-08-15) and the extraction is a per-todo split, not a
  whole-doc flip; the BYBIT/KRAKEN-FUTURES bundling migration and the catalogue-gap audit remain genuinely NA
  (judgment/design-gated).
- **na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:65f9b307b0915187]: KEEP-NA, valid — unchanged.
  The extracted batch18 item 1 was independently found to be a stale duplicate of this doc's own already-resolved
  todos 4/5 and closed 2026-08-18 by regular work (slot-11, data_engineering), not by this audit — see this doc's
  own todo entry above. The 2 remaining open items (undetected defi catalogue-gap on-chain walk; BYBIT/KRAKEN-FUTURES
  futures_chain migration, hard-gated on a per-row expiry verification) stay genuine investigation/production-data-
  migration work, not worker-determinable alone.
- **context-scout 2026-08-20**: refreshed context_scope (7 entries)
