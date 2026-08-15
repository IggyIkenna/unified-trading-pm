---
doc_type: plan
title: cefi satellite AO dispatch batch 19 — 2026-08-13
summary: >-
  Extraction batch from the cefi tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 37 live
  conflict-cleared, bounded/deterministic items (40 total todos, 3 marked out-of-scope, see below) pulled directly from
  10 source docs (RECLASSIFY_SPLIT bounded items from the NA audit, orphaned_never_touched/orphaned_partial_coverage
  bounded items from the AG-closeout audit). Rescoped 2026-08-13 (operator scoping instruction): 3 MDPS-backfill items
  with no manifest-canonical/migration angle marked [x] OUT-OF-SCOPE (checkbox format per
  todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md -- the source items remain open in their
  own source docs, untouched by this batch). Each todo cites its exact source doc; the source docs themselves are NOT
  touched by this batch (checkbox reconciliation back into each source doc happens in the paired finalize plan).
  Conflict-checked against every existing active batch/finalize plan for this tranche via basename-citation
  cross-reference before drafting — no item here duplicates ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/archive/issues/dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md,
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /plans/archive/2026_08/mdps_cefi_chain_bundle_delay_features_timestamp_float_compare_2026_08_12.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5.6
estimate_calibrated_ai_days: 4.4
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# cefi satellite AO dispatch batch 19 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [WRITER] P2. implement Gap 1's resolution — row-level column-value gate for bundle-shaped
      (chain-bundle/options_chain) writers, dropping non-canonical rows to record_failed(NON_CANONICAL_INSTRUMENT_ID,
      granularity=row) + adding quarantined_legs to the manifest row (market-tick-data-service) Source:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` — **SHIPPED
      market-tick-data-service@c1626c5dbd** (a7a1ae39 gate + c1626c5d file-size-cap consolidation, no behavior change).
      `finalise_rows_and_path` classifies each chain-bundle row's own `instrument_id` immediately before write via
      `classify_id_form()`; NON_CANONICAL rows drop (canonical + registered-quarantined legs both survive) and are
      tracked on the new `FinalisedShard.quarantined_legs`, propagated through `ShardChunk.metadata`, and routed to a
      per-leg `record_failed(error="NON_CANONICAL_INSTRUMENT_ID")` manifest row in
      `finalise_and_write_cefi_shards_streaming` (reconciliation queries these by `error=`/`underlying=`/`day=` rather
      than a first-class `quarantined_legs` field on the aggregate row — see the new todo below). 4 new unit tests
      (`tests/market_interface/adapters/cefi/test_chain_bundle_row_level_id_gate.py`). **Prerequisite fix shipped
      alongside**: the row-level gate exposed a real, pre-existing UAC ID_FORM-oracle gap —
      `is_canonical_instrument_id`'s regex only recognized the `@LIN`/`@INV` margin-marker convention, not the
      co-existing legacy lowercase `-inverse`/`-linear` word-form suffix `_build_option`/`_build_future` still emit when
      `quote_asset`+`margin_type` are supplied without a `margin_marker` — so the new gate was misclassifying real
      DERIBIT/BYBIT inverse+linear options_chain/futures_chain rows as NON_CANONICAL and dropping legitimate production
      data. Fixed at the oracle (widened `_CANONICAL_INSTRUMENT_ID_RE`), not worked around in the writer — **SHIPPED
      unified-api-contracts@8b81dd78bb**.
- [ ] [WRITER] P3. Extend Gap 1's row-level gate with first-class manifest visibility: add a `quarantined_legs` field to
      UTL's `ManifestRow` schema (unified-trading-library) and thread it from `FinalisedShard.quarantined_legs` through
      `ShardChunk.metadata` → the day-level `_DateRunState` accumulator (`venue_fetch.py`) → `_write_bundle_shard_row`'s
      aggregate `record_captured_from_counts` call (`manifest_finalize.py`), so the underlying-keyed captured row itself
      carries the dropped-leg list, per §5b's original "the manifest keeps its existing underlying-keyed row, plus a new
      quarantined_legs: [...] field" spec. Deferred out of the Gap 1 todo above because `ManifestRow` lives in a
      different repo (unified-trading-library) not named in that todo's scope, and today's per-leg
      `record_failed(error="NON_CANONICAL_INSTRUMENT_ID")` rows already give reconciliation a queryable (if
      row-granularity rather than field-granularity) signal. Repos: unified-trading-library, market-tick-data-service.
      Source: `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` §5b.
- [x] ✅ [WRITER] P2. implement Gap 2's resolution — make the live/on-chain lane's manifest key a deterministic function
      of the already-computed column value instead of an independent resolve_cefi_instrument_id() call
      (market-tick-data-service: venue_fetch.py, partitioned_writer.py) — **SHIPPED
      market-tick-data-service@d518aca80d**. `PartitionedTickWriter` now persists the column resolution
      `_normalize_cefi_instrument_id_column` already computes into a new `resolved_cefi_instrument_ids` map (keyed on
      the SAME `(instrument_type, sanitized_symbol)` atom `underlying_counts` uses).
      `venue_fetch._canonicalize_manifest_instrument_id` gained a `resolved_column_id` kwarg and derives the manifest
      key by parsing that already-computed value instead of independently re-resolving; `resolve_cefi_instrument_id()`
      is now only a fallback for the no-column-value-yet case. 10 new/updated unit tests
      (`tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py::TestGap2ManifestKeyFromColumnValue`,
      `tests/unit/test_partitioned_writer_cefi_column.py`). Source:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`
- [ ] [UAC] P3. implement Gap 3's resolution — add the temporal 'unclassified' manifest-row state and wire the Stage 3
      read gate to pass-with-warning on it until a backfill-complete flag promotes it to enforced-fail
      (unified-api-contracts + market-tick-data-service) Source:
      `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`
- [ ] [SCRIPT] P3. Root-cause + fix mtds_chunk_loop.sh's PROGRESS.json GCS upload call - confirmed silently stopped
      firing after chunk 17 on mtds-backfill-odds-smallchunk2-20260807 while run.log's own PROGRESS: chunk=N lines kept
      advancing normally through at least chunk 21. Done when: the upload call's failure mode is identified (e.g. a
      swallowed exception, a once-per-VM-lifetime guard misfiring, a stale path) and fixed, with a regression check that
      PROGRESS.json keeps advancing across >=20 consecutive chunks on a fresh run. Repo: deployment-service. Source:
      `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`
- [x] [CODE] P2. Re-launch mdps-cefi-2021-* sharded MDPS CeFi backfill (launch-mdps-sharded-backfill.sh cefi
      --year 2021) **OUT-OF-SCOPE FOR THIS BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service
      backfill/recompute work is excluded from this batch unless manifest-canonical or migration-related. The underlying
      item remains open in its own source doc, untouched by this batch/commit. Source:
      `plans/archive/issues/dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md`
- [x] ✅ [CODE] P2. ~~Capture Binance/OKX/Bybit indexPrice+markPrice+fundingRate as a first-class MTDS data_type (Phase
      1b follow-up, market-tick-data-service)~~ **CLOSED — already-satisfied (2026-08-15, operator-approved via BLOCKED
      Q BLK-483148f6).** The existing `derivative_ticker` data_type (already first-class, already in `EXPECTED_COVERAGE`
      for all 3 venues) already fully populates `mark_price`/`index_price`/`funding_rate` for Binance/OKX/Bybit via
      already-wired live WS connectors, generically across each venue's whole instrument universe (no symbol-type filter
      excludes the equity-perps) — building a standalone data_type would duplicate storage for an identical-source
      signal, the same anti-pattern `perp_funding_handler.py`'s ASTER/LIGHTER-ZKSYNC precedent documents avoiding. No
      code shipped (none needed). Full evidence + file:line citations:
      `plans/archive/issues/cefi_equity_perp_mark_index_funding_derivative_ticker_already_covers_2026_08_15.md`
      (unified-trading-pm@229e86f53b). That issue doc's own `[CODE] P3` follow-up (manifest-level verification that
      capture is actually dispatched+landing non-null for the equity-perp symbol subset specifically) is now ALSO DONE
      (2026-08-15, slot-9) — confirmed via a direct manifest query (144/180/123 distinct equity-perp bases captured on
      BINANCE-FUTURES/OKX-SWAP/BYBIT respectively; no enumeration gap; the archived doc's own Progress Log carries the
      full evidence + two venue-naming corrections vs. this todo's literal OKX-FUTURES/BYBIT-FUTURES wording). Issue doc
      archived (both todos done). Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [x] ✅ [CODE] P2. Recurring daily funding/basis scan across crypto-venue equity-perps (e2e-testing, scheduled job)
      Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — **SHIPPED
      e2e-testing@d1fe3dc6aa**. `scripts/cefi/equity_perp_funding_basis_scan.py`: scans the
      `CEFI_EQUITY_PERP_BASE_UNIVERSE` across Binance/OKX/Bybit, computing annualized funding (UAC
      `perp_funding_cadence`), perp-vs-index basis (bps), and a market-hours-vs-off-hours flag, ranked into an
      opportunity-sizing report. Reads the already-populated `derivative_ticker` data
      (mark_price/index_price/funding_rate — see
      `cefi_equity_perp_mark_index_funding_derivative_ticker_already_covers_2026_08_15.md`) via
      `CanonicalParquetReader`, no new capture needed. Wired as a scheduled job via
      `scripts/cefi/equity_perp_funding_basis_scan_daily.sh` (mirrors `scripts/defi/daily_positioning_dump.sh`'s cron
      pattern, 00:15 UTC). 15 new unit tests (`tests/unit/test_equity_perp_funding_basis_scan.py`), `quality-gates.sh`
      green.
- [x] ✅ [CODE] P2. **Daily leg backfilled; 1h/15m/1m intraday leg is superseded by an operator ruling recorded in
      `/plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` (2026-07-12, KRX narrowed to
      ohlcv_24h-only, predates this todo's own 2026-06-24 authoring).** (2026-08-15, slot-29·backend_engineer)
      `market_tick_data_service/adapters/_umi_yahoo.py::route_yahoo_tradfi` hard-blocks any non-ohlcv_24h KRX request by
      design — per that same archived doc, operator chose "narrow the registry" over "build intraday", shipped
      `unified-api-contracts@a2751f36`; manifest confirms zero `captured` rows for KRX 1h/15m/1m fleet-wide. Re-launched
      the existing daily launcher (`deployment-service/scripts/vm/launch-tradfi-bf-krx-equities-ohlcv-24h.sh`) for all 8
      year-shards (2019-2026) to close the real `attempted_failed`/`expected_unattempted` gap in the already-partially-
      captured daily data — all 8 VMs confirmed STARTED. Full diagnosis + a new residual-finding todo recorded in the
      source doc. Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [x] ✅ [CODE] P2. Databento L-floor boundary PRECISION probe + update LEVEL_MAX_LOOKBACK_DAYS (Phase 5,
      unified-api-contracts) **CLOSED — already-satisfied (2026-08-15).** This exact probe already shipped
      **unified-api-contracts@92a418e5** (2026-08-09, `sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 4, prior
      to this batch's drafting): `metadata.get_cost` binary search on GLBX.MDP3/ES.c.0 (cross-checked DBEQ.BASIC/AAPL
      for L1) measured the exact free/metered boundary per level — L1 (trades/tbbo/mbp-1/bbo) 367d free/368d metered, L2
      (mbp-10) 33d free/34d metered, L3 (mbo) 33d free/34d metered, L0 (ohlcv/definition/statistics/status) no rolling
      metered boundary at all (bound only by GLBX.MDP3's real 2010-06-06 inception, 5908d). `LEVEL_MAX_LOOKBACK_DAYS` /
      `earliest_allowed_start` / `assert_lookback_allowed` in `databento_subscription_allowlist.py` already carry these
      exact measured values (verified live in repo, not stale). QG test coverage already matches the "one day past the
      boundary rejected, one day inside allowed" spec:
      `tests/unit/test_databento_subscription_allowlist.py::TestLookbackFloorBoundaries` asserts
      `test_l1_within_367d_passes`/`test_l1_at_368d_raises`, `test_l2_within_33d_passes`/`test_l2_at_34d_raises`,
      `test_l3_within_33d_passes`/`test_l3_at_34d_raises`, plus L0 within/at-boundary/beyond-window cases. The manifest
      enumerator's floor-clip already consumes the same values transitively —
      `instruments-service/scripts/enumerate_expected_universe.py:1878` and
      `correct_tradfi_universe_floor_clip_and_vix_index.py:103` both `import earliest_allowed_start` from this module
      rather than hardcoding a lookback constant, so they automatically picked up the 2026-08-09 measured values with no
      separate change needed. No code shipped by this batch (none needed) — this todo's source line
      (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 5) simply never had its own checkbox flipped
      after batch11's fix landed. Source: `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [x] ✅ [CODE] P2. Deprecate + remove all Barchart code (Phase 5, cross-repo delete-deprecated-code) Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — **bulk removal already shipped
      2026-08-09** (`unified-api-contracts@fc1b4897`, `market-tick-data-service@aea655a9`, see
      `cefi_consolidated_closeout_2026_07_18.md` Track 0's own entry for that todo — same underlying Phase-5 item, cited
      via a sibling source doc). Verified live on `origin/live-defi-rollout` before closing this one as a duplicate:
      `rg -i barchart` across every repo in the slot found zero live adapter/client/schema/registry-entry code —
      everything remaining was either historical-retirement comments (correct to keep, e.g. "barchart RETIRED
      2026-06-24") or 2 genuinely stale residuals fixed by THIS todo: (1) `ProviderBinding.provider`'s type comment in
      `unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py` still listed `barchart` as a valid
      provider value post-removal — **SHIPPED unified-api-contracts@49ae9bc433**; (2)
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/__init__.py`'s module
      docstring pointed at `scripts/upload_vix_barchart_local.py`, a one-time backfill script deleted along with the
      rest of the Barchart adapter (confirmed gone via `git log --all -- '*upload_vix_barchart*'`, last existed at
      `05348709`) — **SHIPPED market-tick-data-service@ea870f05cd**. Both are misleading-comment/dead-pointer fixes per
      CLAUDE.md's "doc/comment that MISLED you is a finding" rule, not new Barchart-removal scope.
- [x] ✅ [CODE] P2. Map the index perps (SPXUSDT/NAS100/SPYUSDT/XAUUSDT) to the CME index-future canonical with
      contract_multiplier (Phase 1c, unified-api-contracts) **CLOSED — already-satisfied (2026-08-15,
      slot-29·backend_engineer).** This exact mapping already shipped **unified-api-contracts@e973c62d** (2026-08-09,
      via `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2, prior to this batch's drafting) —
      `index_commodity_perp_hedge_link.py` maps SPY→ES ($50/pt), QQQ→NQ ($20/pt), XAU→GC (100oz), with
      `EXCLUDED_INDEX_COMMODITY_PERP_BASES` documenting SPX (confirmed a meme coin, not S&P500) and NAS100 (no such
      Binance symbol) as evidenced negative results rather than silent omissions. No code shipped by this batch (none
      needed) — this batch's audit pulled the same Phase 1c line from a sibling source doc without catching the batch11
      overlap. **Source doc's own checkbox NOT flipped in this commit** — see the new follow-up todo below (the source
      doc is already over its line-cap hard gate, pre-existing, blocking any commit that touches it). Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
- [ ] [SCRIPT] P3. Trim `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` back under its
      1000-line hard cap (currently 1003L, pre-existing — `check_line_caps.sh`/plan-hygiene pre-commit hard-blocks ANY
      commit touching this file until it's under cap) so its own stale Phase-1c index-perp-mapping checkbox (line ~815,
      already satisfied by `unified-api-contracts@e973c62d` — see this batch's todo above + its Progress Log entry) can
      finally be flipped. Judgment call on what to archive/condense (likely candidate: fold older superseded
      Progress-Log sections into an archived companion doc per the plan-completion-and-archival-discipline SSOT), so out
      of scope for this batch's mechanical todo. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. Trim `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` back under its 1000-line
      hard cap (currently 1001L, pre-existing — `check_line_caps.sh`/plan-hygiene pre-commit hard-blocks ANY commit
      touching this file until it's under cap) so its own stale `meta_watchers.check_high_attempted_failed`
      windowed-ratio checkbox (line ~303, already satisfied by `deployment-service@96271280`/`@0c38c00d` — see this
      batch's todo above + its Progress Log entry) can finally be flipped. Judgment call on what to archive/condense
      (likely candidate: fold the many near-duplicate `(cefi, book_snapshot_5)` STATIC-BACKLOG repeat-dispatch Progress
      Log entries into a condensed summary, per the plan-completion-and-archival-discipline SSOT), so out of scope for
      this batch's mechanical todo. Repo: unified-trading-pm.
- [x] ✅ [CODE] P2. Codex SSOT updates for crypto-venue equity-perp sourcing + equity-basis arb archetype Source:
      `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — **SHIPPED unified-trading-pm (this
      commit).** `/codex/02-data/tradfi-databento-sourcing-ssot.md`: new subsection documenting DBEQ.BASIC's missing
      dividends/corporate-actions schema + the yfinance dividend-yield workaround used by the equity-basis NET-basis
      backtest. `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`: new "Crypto-venue equity-perp basis
      variant" section (sourcing via `tracks_equity`, the operator-approved IBKR hedge decision, backtest evidence
      pointer, what's still open in Phase 4/1e — explicitly distinguished from the separate still-open INDEX-perp
      cash-and-carry idea). `/codex/09-strategy/architecture-v2/category-instrument-coverage.md`: new CARRY_BASIS_PERP
      coverage-matrix row for the CeFi×TradFi cross-category pairing. The archetype DESIGN itself (dispersion +
      overnight-gap legs, Phase 4) and the IBKR adapter (Phase 1e) remain open in the source plan — this todo covers
      documentation of what's already decided/shipped, not new design.
- [x] ✅ [CODE] P2. Alert-accuracy quartet fix (deployment-service: interpolate/drop fixed '(0 → 0)' template, extend
      captured-reader probe fallback, conditional Tardis-guard text, exempt cron/launcher host VMs from GONE_NO_CAPTURE)
      **CLOSED — already-shipped elsewhere (2026-08-15, slot-7·backend_engineer).** `deployment-service@0c38c00d`
      (2026-08-11, subject line literally "alert-accuracy quartet") shipped all four pieces before this batch was even
      drafted — verified live on `origin/live-defi-rollout`: the `"(0 → 0)"` figure was always interpolated (never a
      literal fixed string) in `_classify.py::finding_for`; `_captured_reader.py::make_captured_reader._read` probes
      every `market-data`/`instruments-store`/`features` bucket via `_probe_all` on a bucket-resolves-but-blob-absent
      miss, not just an unresolvable bucket; the DP_VM_PREEMPTED relaunch-note text is gated on `TARDIS_GUARD_LAUNCHERS`
      membership (non-member launchers like `launch-mdps-sharded-backfill.sh` get "(no Tardis dependency)" instead of
      the Tardis-guard phrase); `classify_terminated_vm`'s `is_launcher_host` branch exempts a registered launcher/cron
      host from `GONE_NO_CAPTURE`. No code shipped by this batch (none needed) — the source doc's own checkbox was
      flipped in the same commit as this one citing the same sha; see its Progress Log entry for full file:line detail.
      Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Determine which layer wrote the cefi attempted_failed rows (MTDS fetch vs MDPS derivation) and
      whether the 2026-08-02 ruling inflates them Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` — **CLOSED 2026-08-15 (slot-16),
      hypothesis TESTED AND REJECTED, no code fix needed.** Read-only analysis, no code shipped (none needed): the
      reason matching this hypothesis (`NO_RAW_TICK_DATA_FOR_SHARD`, 6,630/1,064,950 = 0.6% of cefi attempted_failed) is
      100% MDPS-side and matches an already-settled TradFi precedent
      (`issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`, 5+ re-checks) — MDPS makes no live vendor
      call so has no FetchEvidence for `empty_confirmed`; `record_failed` is the deliberate, correct interim, not
      inflation. The dominant bucket (`VENUE_FETCH_FAILED`, 218,038 rows, 20.5%) is 100% MTDS-side genuine vendor
      errors, unrelated to the zero-rows question. Full evidence in the source doc's own todo (same commit).
- **[CODE] P2. CANCELLED — SUPERSEDED 2026-08-15 (slot-28·backend_engineer, per operator ruling on `BLK-f5cd6b22`) —
  redirected to a phased LOCAL plan: `plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md`.** Chain
  relabel migration part 2 of 2 (options_chain/futures_chain path-position fix, entity-rename-governed,
  writer+manifest+status+gate+UI same change) Source:
  `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` — **SCOPING INVESTIGATION DONE (2026-08-15,
  slot-28·backend_engineer).** This is a genuine multi-repo entity-rename PLUS a live production GCS data move with
  unknown blast radius, not a mechanical fix. Full consumer inventory (entity-rename-governed rule step 1): **(1)
  market-tick-data-service** — writer builds the wrong shape at `partitioned_writer.py:179-225` (`_get_writer` passes
  `instrument_type=` the raw `"options_chain"`/`"futures_chain"` string; `data_type` column defaults to literal
  `"trades"` at `partitioned_writer.py:338-340`; `_resolve_partition_data_type`/ `_MERGED_DATA_TYPE_MAP` in
  `symbol_rules.py:160-162,218-220` never remaps to `data_type=`), same drift mirrored in the manifest at
  `manifest_finalize.py::_write_bundle_shard_row` (`base_row_key`, lines 255-265, 360-379). **(2)
  unified-api-contracts** — `canonical/partition_paths.py::build_cefi_partition_path`/ `build_tradfi_partition_path`
  (lines 219-302/320-) construct the same wrong shape; critically, the canonical-path ORACLE itself —
  `canonical/_partition_path_canonicality.py:61,70` (`CEFI_CHAIN_INSTRUMENT_TYPES` / `TRADFI_CHAIN_INSTRUMENT_TYPES`) —
  currently VALIDATES `options_chain`/`futures_chain` as legitimate `instrument_type` values, so fixing only the writer
  would immediately trip `canonical_path_violations()` the other way; the oracle must migrate in the SAME change. **(3)
  market-data-processing-service** — chain adapters (`app/adapters/cefi/options_chain_adapter.py`,
  `futures_chain_adapter.py`, routing already fixed part-1 `@93d783df`), `schemas/output_schemas.py:307,314,321`
  hardcoded `applies_to={"options_chain","futures_chain"}`, `app/core/output_path_helpers.py:31`
  `is_chain_bundle_data_type`. **(4) deployment-api** — the whole data-status stack:
  `services/data_status_hierarchical.py`, `services/data_status_drilldown/*`,
  `routes/data_status/{_distinct_values,_axis_census,_downloads,_query_meta,_live_coverage}.py`,
  `services/shard_detail/_shard_core.py`, `utils/path_combinatorics.py`, `services/deploy_missing.py`. **(5)
  deployment-ui** — `DataStatusTab.tsx`, `DataStatusDrilldown.tsx`, `ShardDetailModal.tsx`, `src/lib/mock-api.ts`.
  **Blast radius: unknown** — no existing GCS-object/manifest-row count doc found anywhere in the corpus; the source
  doc's only quantification is qualitative ("affecting every vintage", "6+ years of good data", a 2019 vs 2025-06-16
  spot-check). **Unresolved tactical tension flagged, not settled**: the source doc says "move, don't
  copy-then-delete-separately" (operator, 2026-08-10) but the cited precedent
  (`market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py:1-72`) does
  COPY-ONLY-then-separately-gated-delete specifically because GCS has no atomic move (a bare move risks data loss on a
  partial failure) — the source doc itself says to check that rationale before overriding it, i.e. this was left open,
  not decided. Filed `BLK-f5cd6b22`; **operator ruled (2026-08-15): scope this down to a written consumer-inventory +
  phased plan only, default `assigned_vm: NA`, do not resolve the move-vs-copy tension outside the new plan's own
  drafting** — see `plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md` for the resulting 5-phase
  plan (UAC oracle dual-acceptance → writer+adapters+catalogue migrate together → operator-gated backfill → oracle
  narrows + close-out). No code changed by this investigation; this todo's own tracked work now lives in that plan.
- [ ] [CODE] P2. Resolve margin_type for the ~1,578 cefi liquidation instrument_ids lacking @LIN/@INV suffix via
      instruments-service reference data Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Widen canonical_writer_shaping int32->int64 coercion to every contract-declared int64 column (or assert
      dtype match at the write seam) Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Audit UNCLASSIFIED_ADAPTER_ERROR rows (51% of trades cell, 14% of derivative_ticker) **CLOSED —
      root-caused, no live-adapter bug found (2026-08-15, slot-17·backend_engineer).** Full-repo grep of
      market-tick-data-service for every literal `UNCLASSIFIED_ADAPTER_ERROR` emitter (excluding tests) found exactly
      TWO producers, both already-shipped one-off manifest-canonicalisation scripts, NOT a live adapter routing path:
      `scripts/_rebuild_cefi_cf11.py::_process_attempted_failed_cefi_row` (CF-11 manifest rebuild) and
      `scripts/canonicalize_mtds_index.py::canonicalize_cefi` (wholesale live-index canonicalisation,
      `lifecycle:     oneoff`) — both deliberately normalise a legacy blank/`LegacyBlankErrorReasonError` `error_reason`
      (predating the manifest's structured error taxonomy) into the visible `UNCLASSIFIED_ADAPTER_ERROR` catch-all, per
      their own docstrings: "a recorded failure, kept visible + backfill-worthy — never hide a possible gap." No CeFi
      trades/ derivative_ticker live fetch/write path (`engine/orchestrator/sentinels.py`'s tier-2/tier-3 sentinel
      emitters, the actual `record_failed` callsite for these two data_types) ever produces this literal string — its
      unclassified-error fallback writes a DIFFERENT free-text value (`f"UNCLASSIFIED:{code_token}"`, carrying the raw
      exception class name) when `classify_venue_error()` returns `None`, confirmed via
      `unified_trading_library/manifest_writer/_writer_record.py::record_failed` (writes `error_reason=<error>`
      verbatim, no enum coercion) — so a live routing gap there would show up as a distinct `UNCLASSIFIED:<Code>`
      string, not this one. UAC's own `honest_coverage.py` docstring reviewer-flags `UNCLASSIFIED_ADAPTER_ERROR` in
      "production" as a calling-adapter bug — these rows are legacy-migration output, not production adapter emissions,
      so the flag doesn't apply here. Since these are `attempted_failed` (retried by default per `record_failed`'s own
      docstring), the 51%/14% figure is not a silent gap — it's the designed interim state for historically-blank-reason
      rows pending re-fetch/reclassification. No code shipped (none needed) — this todo's "audit" outcome is a
      negative/clean result, not a fix. Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Fix meta_watchers.check_high_attempted_failed's mismatched trailing-14-day-numerator vs
      all-time-denominator ratio **CLOSED — already-shipped elsewhere (2026-08-15, slot-20·backend_engineer).** This
      exact fix already shipped **deployment-service@96271280** (2026-08-08, "trailing-window threshold for
      check_high_attempted_failed (DP-FETCH-009)") and was refined further by **deployment-service@0c38c00d**
      (2026-08-11, "windowed attempted_failed ratio"). Verified live in
      `_attempted_failed_index.py::read_attempted_failed_cells`:
      `windowed_captured_mask = captured_mask &     within_window_mask` — `captured` now shares the SAME
      `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` window as `attempted_failed`, so the ratio is no longer a 14-day
      numerator over an all-time denominator. `max_attempted_at`/`stale_days` diagnostics correctly remain
      LIFETIME-scoped (a different, intentional use — "when did this last fail at all"). No code shipped by this batch
      (none needed) — this todo's own source line was never flipped after the fix landed. **Source doc's own checkbox
      NOT flipped in this commit** — see the new follow-up todo below (the source doc is 1001L, over its 1000-line hard
      cap, pre-existing, blocking any commit that touches it). Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix sports reference-table exporter fabricating http_status=200 FetchEvidence for a GCS-missing
      upstream Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Recompute the 2026-08-10 sports reference tables once instruments-service backfills that day
      **CLOSED — stale-checkbox correction (2026-08-15), already-shipped elsewhere per the AO-dispatch conflict-check
      protocol §3(4).** The source doc's own identical todo was verified done by slot-29 on 2026-08-14 (manifest lookup:
      `day=2026-08-10` `fixture_features`/`derived_features` `capture_status=captured`, real non-placeholder GCS output
      — 172 blobs, 17-490KB each, across 40+ leagues; instruments-service `sports_reference` upstream for 2026-08-10
      also confirmed real, 648 objects) and the source doc itself is `[x] ✅` there. Full evidence:
      `/plans/archive/2026_08/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md`
      Progress Log (slot-29, 2026-08-14) — that issue doc is `status: resolved` and already archived. No recompute run
      by this todo; nothing left to do. Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] [CODE] P2. Shard the slow date in the MDPS per-date backfill so one date cannot fail a complete run **OUT-OF-SCOPE
      FOR THIS BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is
      excluded from this batch unless manifest-canonical or migration-related. The underlying item remains open in its
      own source doc, untouched by this batch/commit. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] [CODE] P2. Rightsize the MDPS backfill VM class per the 2026-08-10 rightsizing HARD RULE **OUT-OF-SCOPE FOR THIS
      BATCH (2026-08-13, operator scoping instruction)** — MDPS/features-service backfill/recompute work is excluded
      from this batch unless manifest-canonical or migration-related. The underlying item remains open in its own source
      doc, untouched by this batch/commit. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix empty instrument_id in the chain-bundle path (live_workers_streaming.py writing no manifest row)
      Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Promote _ShardedState out of relaunch_backfill_vm.py into a shared helper Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix flaky shellcheck under host load in launch-expected-universe-v2-vm.sh Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Generalise the test-hermeticity guard for the pytest fake-GCS backend persistence bug Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Fix the pre-existing hardcoded-prod-project-ID QG violation in test_vm_launcher_scripts.py Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [ ] [CODE] P2. Track 0: Capture Binance/OKX/Bybit indexPrice/markPrice/fundingRate for equity-perps as a first-class
      data_type Source: `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [x] ✅ [CODE] P2. Track 0: Wire a recurring daily funding/basis scan across all crypto-venue equity-perps Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md` — **SAME underlying work as this batch's earlier
      "Recurring daily funding/basis scan" todo above (both cite the same cryptovenue Phase 1b item via different source
      docs)** — SHIPPED e2e-testing@d1fe3dc6aa, see that entry for full evidence.
- [ ] [CODE] P2. Track 0: Launch the CeFi Tardis backfill for the equity-perp window Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [ ] [CODE] P2. instrument_type casing residual: fresh live re-count against current manifest to confirm literal 100%
      UPPERCASE Source: `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [ ] [CODE] P2. Live-query OKX/Bybit SPOT instrument endpoints for the tokenized-equity symbol set + listing dates
      Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Add confirmed tokenized-equity symbols to the UAC CeFi instrument universe with
      instrument_type=SPOT_PAIR + tracks_equity link Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Add confirmed symbols to the CeFi MVP scope rule (mirror CEFI_EQUITY_PERP_BASE_UNIVERSE pattern)
      Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Register an InstrumentRecord per confirmed symbol dated to its real historical listing date Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [ ] [CODE] P2. Launch the CeFi Tardis/venue-native backfill for the tokenized-equity SPOT window Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [x] ✅ [CODE] P2. Grep prior mdps-cefi-_/mdps-tradfi-_/mdps-defi-* run.log archives (or manifest attempted_failed
      reason strings) for the exact Timestamp-vs-float TypeError signature to size the historical blast radius, and
      re-trigger record_failed→retry for any shard whose failure resolves to this exact root cause —
      market-data-processing-service@4cd46c17ba. Manifest: 0 rows matched across cefi/tradfi/defi. run.log grep: 19/294
      matched, all pre-fix `mdps-cefi-2019-*` relaunch attempts of the already-relaunched-with-fix shard — blast radius
      contained, no further retry needed. Source doc archived + resolved:
      `plans/archive/2026_08/mdps_cefi_chain_bundle_delay_features_timestamp_float_compare_2026_08_12.md`
- [ ] [CODE] P2. Mechanical citation-reconciliation for todo 2 (S1-b): flip the checkbox to [x] citing
      deployment-service@e7d17f2 + the CEFI 117-shard/DeFi 3,535-shard production verification already documented
      in-doc, and update the doc's stale 'Big findings — Recommended (A): delete' section to reflect that option (B)
      finish-the-dispatcher-branch is what actually shipped Source:
      `plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`
- [ ] [CODE] P2. Archive this doc via the 6-step archival ritual
      (/codex/12-agent-workflow/plan-completion-and-archival-discipline.md), repointing the 7 listed active corpus
      referrers (tradfi_satellite_ao_dispatch_batch7_2026_08_06.md, ag_closeout_audit_defi_parked_2026_08_08.md,
      mdps_features_deadcode_consolidation_2026_07_20.md, plans/active/INDEX.md, plus 3 already-repointed archive-path
      references) in the same commit Source:
      `plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

## Progress Log

- **2026-08-15 (slot-17·backend_engineer)**: dispatched the "Audit UNCLASSIFIED_ADAPTER_ERROR rows" todo. Grepped every
  literal `UNCLASSIFIED_ADAPTER_ERROR` producer in market-tick-data-service (excluding tests) and found only two, both
  already-shipped one-off manifest-canonicalisation scripts (`_rebuild_cefi_cf11.py`, `canonicalize_mtds_index.py`) that
  normalise legacy blank/`LegacyBlankErrorReasonError` `error_reason` values into this visible catch-all — never a live
  adapter/sentinel routing path (traced the actual trades/derivative_ticker `record_failed` callsite in
  `engine/orchestrator/sentinels.py` + `unified_trading_library/manifest_writer/_writer_record.py::record_failed`; a
  live unclassified-error fallback writes a distinct `UNCLASSIFIED:<exception-class>` string, not this literal enum
  value). Conclusion: the 51%/14% figure is legacy-migration output, not a live routing bug — no code fix needed. See
  the todo's own entry above for full file:line citations.

- **2026-08-15 (slot-29·backend_engineer)**: dispatched the "Map the index perps... to the CME index-future canonical"
  todo — found it already shipped `unified-api-contracts@e973c62d` (2026-08-09) via
  `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2, sourced from the SAME underlying Phase 1c item via a
  different citing doc (`cefi_consolidated_closeout_2026_07_18.md` Track 0 vs this batch's
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`). This batch's 2026-08-13 conflict-check (§3 of
  `ao-dispatch-batch-naming-and-conflict-check.md`) did not catch the overlap because it checked the tranche's
  consolidated-closeout doc's own Track content, not the underlying Phase-1c-source doc's later 2026-08-09 Progress Log
  entries recording the same work done under a sibling batch. This doc's own checkbox flipped per protocol §3.4
  "already-shipped elsewhere, checkbox just never flipped" — stale-checkbox correction, not new work, no conflict. The
  source doc's mirror checkbox could NOT be flipped in the same commit: that file is already 1003L, over its 1000-line
  hard cap (pre-existing, unrelated to this fix) — `check_line_caps.sh`/plan-hygiene pre-commit hard-blocks any commit
  touching it. Filed a P3 follow-up todo above to trim it under cap first; the source checkbox stays stale until then.

- **2026-08-15 (slot-7·backend_engineer)**: dispatched the "Deprecate + remove all Barchart code" todo. Verified live:
  the bulk removal already shipped 2026-08-09 (`unified-api-contracts@fc1b4897`, `market-tick-data-service@aea655a9`,
  same underlying Phase-5 item as `cefi_consolidated_closeout_2026_07_18.md` Track 0's own entry) — `rg -i barchart`
  workspace-wide found zero live adapter/client/schema/registry code, only historical-retirement comments (correctly
  kept) plus 2 stale residuals: a `ProviderBinding.provider` type-comment still listing `barchart` as valid
  (`unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py`), and a tradfi-adapters module docstring
  pointing at the deleted one-time backfill script `scripts/upload_vix_barchart_local.py`
  (`market-tick-data-service/.../adapters/tradfi/__init__.py`). Both fixed as misleading-pointer corrections (CLAUDE.md
  "doc/comment that MISLED you is a finding"), not new Barchart-removal scope. **SHIPPED
  unified-api-contracts@49ae9bc433, market-tick-data-service@ea870f05cd** — both verified ancestors of
  `origin/live-defi-rollout`.

- **context-scout 2026-08-15**: refreshed context_scope (4 entries), still accurate.

- **2026-08-15 (slot-10·backend_engineer)**: shipped the "Codex SSOT updates for crypto-venue equity-perp sourcing +
  equity-basis arb archetype" todo — 3 codex docs updated (`tradfi-databento-sourcing-ssot.md` dividends-gap subsection,
  `carry-basis-perp.md` new equity-perp basis variant section, `category-instrument-coverage.md` new coverage row),
  checkbox flipped in the same commit. See the todo's own evidence line for full detail.

- **2026-08-15 (slot-7·backend_engineer)**: dispatched the "Alert-accuracy quartet fix" todo — found it already shipped
  `deployment-service@0c38c00d` (2026-08-11, same commit as its source doc's todo 1, subject line literally
  "alert-accuracy quartet") before this batch was drafted. Verified all four pieces live on `origin/live-defi-rollout`
  (interpolated `(before → after)` captured-count text, the bucket-resolves-but-blob-absent probe fallback, the
  Tardis-guard-conditional relaunch text, the launcher-host `GONE_NO_CAPTURE` exemption) rather than trusting the commit
  subject alone. No code shipped by this batch (none needed) — checkbox flipped citing the sha; the source doc's own
  checkbox was flipped in the same commit, see its Progress Log entry for full file:line detail.

- **2026-08-15 (slot-28·backend_engineer)**: dispatched the "Chain relabel migration part 2 of 2" todo. Investigated (2
  Explore sub-agent passes) before touching any code and found it is NOT a 1-hour mechanical fix — a genuine 5-repo
  entity-rename (market-tick-data-service writer+manifest, unified-api-contracts canonical builders + the canonical-path
  oracle itself, market-data-processing-service adapters/schemas, deployment-api's full data-status stack,
  deployment-ui) plus a live production GCS data move over "6+ years" of vintage data with no measured blast radius
  anywhere in the corpus. The source doc's own instruction ("move, don't copy-then-delete-separately") is in unresolved
  tension with the cited precedent script's copy-first/delete-later safety pattern — the source doc itself flags this as
  something to double-check, not a settled call. Filed `BLK-f5cd6b22` (recommendation: code-side 5-repo migration this
  dispatch, live GCS copy/delete split into a separate `[OPERATOR]`-tagged delete-safety-gated follow-up) rather than
  guessing on a judgment call this size. Full consumer inventory + file:line citations added to the todo item above. No
  code changed — investigation + escalation only.

- **2026-08-15 (slot-28·backend_engineer, resolution)**: operator ruled on `BLK-f5cd6b22` — scope down to a written
  consumer-inventory + phased plan, default `assigned_vm: NA` (human/LOCAL) given the cross-repo blast radius and
  canonical-oracle change, do not resolve the move-vs-copy tactical question outside the new plan's own drafting.
  Drafted `plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md` (5 phases: resolve move-vs-copy →
  UAC oracle dual-acceptance → writer+adapters+catalogue migrate together → operator-gated measured backfill → oracle
  narrows + close-out), carrying the full consumer inventory forward. This todo's checkbox marked CANCELLED — SUPERSEDED
  (redirected, not dead work) per the todo-format disposition-marker convention. No code shipped — scoping + plan
  authoring only, per the operator's explicit instruction not to implement in this session.

- **2026-08-15 (slot-16·backend_engineer)**: dispatched the "Determine which layer wrote the cefi attempted_failed rows"
  read-only analysis todo. Live-queried `market-data-tick-cefi-prd-.../_index/availability_index.parquet`
  (cols-pushdown) and traced the reason matching the operator's hypothesis (`NO_RAW_TICK_DATA_FOR_SHARD`) to a code
  mechanism already exhaustively settled for TradFi — hypothesis rejected, no code fix needed. Checkbox flipped citing
  the finding; the source doc's own checkbox was flipped in the same commit with the full evidence.

- **2026-08-15 (slot-20·backend_engineer)**: dispatched the "Fix meta_watchers.check_high_attempted_failed's mismatched
  trailing-14-day-numerator vs all-time-denominator ratio" todo. Read `_attempted_failed_index.py` directly and found
  the fix already shipped — `deployment-service@96271280` (2026-08-08) introduced the trailing-window threshold, then
  `deployment-service@0c38c00d` (2026-08-11) windowed `captured` to the SAME `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14`
  cutoff as `attempted_failed` (`windowed_captured_mask = captured_mask & within_window_mask`), closing exactly the gap
  this todo describes; the module's own docstring documents the fix inline. Confirmed via `git log` that both commits
  are ancestors of `origin/live-defi-rollout`. No code shipped by this batch (none needed) — checkbox flipped citing
  both shas. The source doc's own checkbox could NOT be flipped in the same commit:
  `data_pipeline_alert_storm_root_ cause_batch_2026_08_10.md` is 1001L, over its 1000-line hard cap (pre-existing,
  unrelated to this fix) — `check_line_caps.sh`/plan-hygiene pre-commit hard-blocks any commit touching it. Filed a P3
  follow-up todo above to trim it under cap first; the source checkbox stays stale until then.
