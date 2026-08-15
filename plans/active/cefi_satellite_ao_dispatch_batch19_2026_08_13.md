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
    /plans/archive/2026_08/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
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
- [x] ✅ [WRITER] P3. Extend Gap 1's row-level gate with first-class manifest visibility: add a `quarantined_legs` field
      to UTL's `ManifestRow` schema (unified-trading-library) and thread it from `FinalisedShard.quarantined_legs`
      through `ShardChunk.metadata` → the day-level `_DateRunState` accumulator (`venue_fetch.py`) →
      `_write_bundle_shard_row`'s aggregate `record_captured_from_counts` call (`manifest_finalize.py`), so the
      underlying-keyed captured row itself carries the dropped-leg list, per §5b's original "the manifest keeps its
      existing underlying-keyed row, plus a new quarantined_legs: [...] field" spec. Deferred out of the Gap 1 todo
      above because `ManifestRow` lives in a different repo (unified-trading-library) not named in that todo's scope,
      and today's per-leg `record_failed(error="NON_CANONICAL_INSTRUMENT_ID")` rows already give reconciliation a
      queryable (if row-granularity rather than field-granularity) signal. Repos: unified-trading-library,
      market-tick-data-service. Source: `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` §5b.
      **SHIPPED** `unified-trading-library@04ffad098c` (`ManifestRow`/`AvailabilityRecord.quarantined_legs` +
      `record_captured_from_counts` threading) + `market-tick-data-service@839480686b`
      (`PartitionedTickWriter.record_quarantined_legs` → `_DateRunState.chain_bundle_quarantined_legs` →
      `_write_bundle_shard_row`'s `record_captured_from_counts` call).
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
- [x] ✅ [UAC] P3. implement Gap 3's resolution — add the temporal 'unclassified' manifest-row state and wire the Stage 3
      read gate to pass-with-warning on it until a backfill-complete flag promotes it to enforced-fail
      (unified-api-contracts + market-tick-data-service) — **SHIPPED unified-api-contracts@8203b600c0 +
      market-tick-data-service@ecedb15f4e** (2026-08-15, slot-17·backend_engineer). UAC:
      `IdFormVerdict` widened to a 4th `"unclassified"` state; new
      `classify_manifest_row_id_form(instrument_id_form, candidate)` in `canonical/quarantine.py` is
      field-presence-aware (absent/empty field → `unclassified`, regardless of what the candidate's own shape would
      classify as; a present recognized value is trusted verbatim; a malformed value falls back to a fresh
      `classify_id_form`). MTDS: new `enforce_read_gate_id_form()` in `engine/orchestrator/symbol_rules.py` (mirrors
      the existing Stage 0/P write-side `enforce_structural_and_observe_id_form` helper) — canonical/quarantined PASS
      silently, unclassified PASS-WITH-WARNING (log only, never raises) while the new
      `_STAGE2_ID_FORM_BACKFILL_COMPLETE` module flag is False (its only value today — Stage 2's schema v10
      `instrument_id_form` field has not shipped, so every manifest row is honestly unclassified), non_canonical
      always raises. Wired into `CanonicalParquetReader.read_from_manifest` via a new
      `_enforce_cefi_id_form_read_gate` helper (kept the method under the 50-line cap), called only for the one
      confirmed-captured cefi shard after `_resolve_pipeline_mode_from_manifest` — zero production behaviour change
      today (pass-with-warning only) since Stage 2 is still open (this batch's own `[DATA] P3` schema-v10 todo).
      Uses a call-time-deferred import to avoid a real circular import
      (`reader.py` → `symbol_rules.py` → `engine.orchestrator` package → `market_interface` → `reader.py`), caught by
      re-running quality gates before shipping. 6 new unit tests (UAC `tests/unit/test_quarantine.py`, MTDS
      `tests/unit/test_symbol_rules_read_gate.py`), both gates green. Source:
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
      batch's todo above + its Progress Log entry) AND its stale "Resolve margin_type for the ~1,578 cefi liquidation
      instrument_ids" checkbox (line ~289, already satisfied by `unified-trading-library@8142cab5ad` +
      `market-data-processing-service@6422150034` — see this batch's own todo above) can finally be flipped. Judgment
      call on what to archive/condense (likely candidate: fold the many near-duplicate `(cefi, book_snapshot_5)`
      STATIC-BACKLOG repeat-dispatch Progress Log entries into a condensed summary, per the
      plan-completion-and-archival-discipline SSOT), so out of scope for this batch's mechanical todo. Repo:
      unified-trading-pm.
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
- [x] ✅ [CODE] P2. Resolve margin_type for the ~1,578 cefi liquidation instrument_ids lacking @LIN/@INV suffix via
      instruments-service reference data — **SHIPPED unified-trading-library@8142cab5ad +
      market-data-processing-service@6422150034** (2026-08-15, slot-11·backend_engineer). New
      `read_instruments_catalog_margin_type()` reader in UTL's `instruments_catalog_reader.py`, mirroring the existing
      `read_instruments_catalog_contract_size()` shape/cache exactly (shared `_get_cached_catalog_row` scan;
      `margin_type` was already in `CATALOG_COLUMNS` — no writer change needed). Wired as a fallback in
      `liquidations_adapter.py::_resolve_margin_type_via_catalog_fallback`, tried only when `infer_cefi_quote_margin`'s
      string heuristics exhaust unresolved — before falling to the honest `MalformedTickFieldError`. 8 new unit tests
      across both repos (`TestReadInstrumentsCatalogMarginType`, `TestUnsuffixedMarginTypeFromCatalog`), both gates
      green. **Source doc's own checkbox NOT flipped in this commit** — that file is already 1001L, over its 1000-line
      hard cap (pre-existing, unrelated to this fix); `check_line_caps.sh`/plan-hygiene pre-commit hard-blocks any
      commit touching it (same situation as this batch's earlier "Map the index perps" todo). Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Widen canonical_writer_shaping int32->int64 coercion to every contract-declared int64 column (or
      assert dtype match at the write seam) — **SHIPPED market-data-processing-service@5b2701fa9f (2026-08-15,
      slot-9·backend_engineer).** `_inject_schema_contract_columns` now accepts an optional
      `schema_contract: SchemaContract | None` param; when supplied, it coerces EVERY contract-declared `int64` column
      present on the frame from int32→int64 (not just the hardcoded `trade_count`) — this closes the exact class of
      defect `liquidation_count` hit invisibly. Both call sites now pass the already-resolved contract:
      `canonical_writer.py`'s `lookup_mdps_contract()` call was reordered to run BEFORE the injection call (previously
      ran after, so the contract wasn't available yet); `canonical_writer_streaming.py`'s `CandleStreamingWriteContext`
      gained a `schema_contract: SchemaContract | None = None` field, populated at `open_candle_streaming_writer()` time
      and threaded into `write_streaming_chunk()`'s injection call. Callers with no contract (none remain, but the param
      is optional for API stability) fall back to the legacy `trade_count`-only coercion. New regression test
      `test_inject_schema_contract_columns_widens_every_int64_column` (asserts `trade_count` + `liquidation_count` both
      coerce, an unrelated non-contract int32 column is left untouched). `quality-gates.sh` green. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Audit UNCLASSIFIED_ADAPTER_ERROR rows (51% of trades cell, 14% of derivative_ticker) **CLOSED —
      root-caused, no live-adapter bug found (2026-08-15, slot-17·backend_engineer).** Full-repo grep of
      market-tick-data-service for every literal `UNCLASSIFIED_ADAPTER_ERROR` emitter (excluding tests) found exactly
      TWO producers, both already-shipped one-off manifest-canonicalisation scripts, NOT a live adapter routing path:
      `scripts/_rebuild_cefi_cf11.py::_process_attempted_failed_cefi_row` (CF-11 manifest rebuild) and
      `scripts/canonicalize_mtds_index.py::canonicalize_cefi` (wholesale live-index canonicalisation,
      `lifecycle: oneoff`) — both deliberately normalise a legacy blank/`LegacyBlankErrorReasonError` `error_reason`
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
      `windowed_captured_mask = captured_mask & within_window_mask` — `captured` now shares the SAME
      `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` window as `attempted_failed`, so the ratio is no longer a 14-day
      numerator over an all-time denominator. `max_attempted_at`/`stale_days` diagnostics correctly remain
      LIFETIME-scoped (a different, intentional use — "when did this last fail at all"). No code shipped by this batch
      (none needed) — this todo's own source line was never flipped after the fix landed. **Source doc's own checkbox
      NOT flipped in this commit** — see the new follow-up todo below (the source doc is 1001L, over its 1000-line hard
      cap, pre-existing, blocking any commit that touches it). Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Fix sports reference-table exporter fabricating http_status=200 FetchEvidence for a GCS-missing
      upstream — **SHIPPED features-service@656f2e10** (2026-08-15, slot-7·backend_engineer). Root cause:
      `_run_reference_tables`'s `df.empty` branch unconditionally fabricated a `http_status=200`/`rows_in_response=0`
      `FetchEvidence` for ANY empty export, including a REQUIRED entity (only `fixtures` today) whose GCS blob
      instruments-service hasn't written yet — `read_all_reference_data()` swallows that `DependencyError` per-entity
      for shard isolation, so the exporter's cached read couldn't distinguish a genuine 2xx-empty upstream from one
      never actually reached. New `_dependency_missing_gate.py` (extracted to keep `batch_handler.py` under the 900-line
      QG cap) re-probes REQUIRED entities directly before recording empty; a `DependencyError` now routes to
      `record_failed`, mirroring `_run_feature_group`'s existing handling of this same gap class. 1 new regression test
      (`test_run_reference_tables_records_failed_on_dependency_error`). Also regenerated the
      `adapter_contract_baseline.yaml` entry for the two touched files (the `record_failed` call moved, not vanished) —
      `unified-trading-pm@0c49f53583`. Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
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
- [x] ✅ [CODE] P2. Fix empty instrument_id in the chain-bundle path (live_workers_streaming.py writing no manifest row)
      Source: `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` —
      **market-data-processing-service@ef9e38b9a4.** `_record_streaming_empty_timeframe`'s early-return gated the
      manifest write on BOTH `bucket_name` AND `instrument_id`; the eager chain path (`live_workers_chain.py`'s
      `_process_all_timeframes`) never gated on `instrument_id`, only on the resolved manifest bucket, and
      `_resolve_empty_failed_shard_tuple("")` degrades gracefully (`venue` falls back to `input_venue` or `"UNKNOWN"`).
      Dropped the `instrument_id` half of the guard to match that convention, so the shard is no longer silently absent
      from the manifest (WARNING-only). Updated the stale regression test asserting the old no-write behavior + added a
      fully-degenerate (`instrument_id=""`, `input_venue=None`) case. QG green (2435 passed, 2 skipped,
      sentinel=970122bafe921968d21c31dd6c5ead618a231e9b).
- [x] ✅ [CODE] P2. Promote _ShardedState out of relaunch_backfill_vm.py into a shared helper **CLOSED —
      already-satisfied (2026-08-15, slot-17·backend_engineer).** This exact extraction already shipped
      `deployment-service@0c38c00d` (2026-08-10) as part of the "Durable, race-free relaunch state" fix — verified live
      on `origin/live-defi-rollout` (HEAD `d49dd57e`): `scripts/recovery/_durable_state.py`'s own module docstring
      states it was "Extracted from `relaunch_backfill_vm.py` (2026-08-10) when that module crossed the 960-line cap ...
      the next actuator needing state across Cloud Run Job executions should import it from here rather than re-deriving
      the race-free pattern." The class is now public `ShardedState` (no longer the private `_ShardedState` this todo's
      title references), `relaunch_backfill_vm.py` imports it via
      `from ._durable_state import ShardedState, _state_bucket`. No other actuator has needed cross-execution state yet
      (`rg ShardedState deployment-service/scripts/recovery/*.py` shows only the definition + the one re-importer), so
      there is nothing further to promote. No code shipped by this todo (none needed) — this todo's own line was never
      flipped after the 0c38c00d fix landed and its Progress Log's own text already documents the extraction. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Fix flaky shellcheck under host load in launch-expected-universe-v2-vm.sh Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` — **SHIPPED deployment-service@8df1bf3e20
      (2026-08-15, slot-9·backend_engineer).** Independently arrived at the same root cause + fix slot-3 already
      diagnosed below (`TestShellcheckClean.test_shellcheck_no_errors`, `tests/unit/test_vm_zombie_watchdog.py`, ~180
      parametrized per-script `shellcheck` subprocess calls flaking under concurrent gate load — SIGPIPE, the same
      anti-pattern `test_script_syntax_validation` fixed 2026-08-14): batched into ONE
      `shellcheck --severity=error <all scripts>` subprocess call (shellcheck accepts multiple file args natively, no
      wrapper loop needed). Unlike slot-3's commit (`2512a92b`, GATED — stayed local to their clone, never reached
      origin after repeated host-contention QG kills), this run's Pass-1 `quality-gates.sh` completed clean (527s,
      sentinel matched HEAD) on the first attempt and shipped via quickmerge with no rebase —
      `post-push ancestry verified` against `origin/live-defi-rollout`.
- [x] ✅ [CODE] P2. Generalise the test-hermeticity guard for the pytest fake-GCS backend persistence bug **CLOSED —
      already-shipped in the SAME commit as the original ad-hoc fix (2026-08-15, slot-26·backend_engineer).** Read
      `deployment-service/tests/conftest.py` directly: `_isolate_local_storage_provider_default_root` (an `autouse=True`
      fixture in the ROOT `tests/conftest.py`, confirmed the ONLY `conftest.py` in the whole `tests/` tree via
      `find tests -iname conftest.py`) monkeypatches
      `unified_trading_library.cloud_interface.providers.local._default_local_storage_root` to
      `tmp_path / "local-storage"` for EVERY test in the suite, not just the two `sweep()` alert tests the source doc's
      own Lesson 5 names. `git log -S"_isolate_local_storage_provider_default_root" -- tests/conftest.py` → single hit,
      `0c38c00d` — the exact same commit the source doc cites for the "ad hoc" fix, and the fixture's own docstring
      already states the generalisation intent verbatim ("Porting the same fixture ... closes the class for EVERY
      deployment-service feature that writes durable state, not just those actuators"), mirroring UTL's own `@8f0d6e8f`
      fixture rather than inventing a repo-local one. Confirmed no narrower/duplicate local-storage-root patch exists
      elsewhere (`grep -rn '_isolate_local_storage_provider_default_root\|_default_local_storage_root' tests/` outside
      `conftest.py` → only a citing comment in `test_dp_recovery_actuators.py`, no second implementation). The todo's
      own framing (still "ad hoc," needing a follow-up generalisation) was accurate at the moment the source doc's
      Progress Log was written mid-session but was already resolved by session-end — simply never checked off. No code
      shipped by this batch (none needed). Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. **STALE PREMISE — already fixed, no violation exists.** (2026-08-15, slot-22·backend_engineer) The
      named QG check (`base-service.sh`: `codex_rg "central-element-[0-9]+" tests/` → "Hardcoded prod project ID in
      tests") runs clean in deployment-service today: a live re-run of the exact check regex against `tests/` finds zero
      matches. `git log -- tests/unit/test_vm_launcher_scripts.py` shows
      `c55faf2c "test(dp): drop hardcoded prod project id from vm-launcher test fixture"` already landed this fix after
      the source doc (2026-08-10) was filed. No code change made; nothing to restore. Source:
      `plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
- [x] ✅ [CODE] P2. Track 0: Capture Binance/OKX/Bybit indexPrice/markPrice/fundingRate for equity-perps as a
      first-class data_type **CLOSED — duplicate of this same batch's earlier "Capture Binance/OKX/Bybit
      indexPrice+markPrice+ fundingRate" entry above (2026-08-15), which cites the identical underlying Phase 1b item
      via a different source doc (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` vs this entry's own
      `cefi_consolidated_closeout_2026_07_18.md` Track 0 — that doc's own header states its Track 0 is an operator-ruled
      embed of the cryptovenue doc's Phase 1b items, sequenced ahead of/alongside the migration).** No code shipped
      (none needed) — the existing `derivative_ticker` data_type already fully populates
      mark_price/index_price/funding_rate for Binance/OKX/Bybit equity-perps via already-wired live WS connectors,
      generically across each venue's whole instrument universe. Full evidence:
      `/plans/archive/issues/cefi_equity_perp_mark_index_funding_derivative_ticker_already_covers_2026_08_15.md`
      (unified-trading-pm@229e86f53b). Source's own checkbox also flipped in this commit — see
      `cefi_consolidated_closeout_2026_07_18.md` Track 0. Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [x] ✅ [CODE] P2. Track 0: Wire a recurring daily funding/basis scan across all crypto-venue equity-perps Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md` — **SAME underlying work as this batch's earlier
      "Recurring daily funding/basis scan" todo above (both cite the same cryptovenue Phase 1b item via different source
      docs)** — SHIPPED e2e-testing@d1fe3dc6aa, see that entry for full evidence.
- [x] ✅ [CODE] P2. Track 0: Launch the CeFi Tardis backfill for the equity-perp window **LAUNCHED 2026-08-15
      (slot-14·backend_engineer)** — see Progress Log for VM name + evidence. Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [x] ✅ [CODE] P2. **DONE 2026-08-15 (slot-19·backend_engineer) — residual FOUND, not literal 100% UPPERCASE.** Fresh
      live re-count of the cefi manifest's `instrument_type` column
      (`gs://market-data-tick-cefi-prd-central-element-323112`, now 29,481,508 rows, up from the 2026-07-18 baseline's
      11.19M) found **39,286 rows still lowercase** (`perpetual` 38,083 / `future` 1,191 / `spot_pair` 12) against the
      canonical UPPERCASE targets — the `instruments-service@555ddf1c` fold was **dry-run measured only**; its `--apply`
      remains drain-gated under the Track-1 cutover (still `RE-OPENED` per Track 1 above). Not an active writer
      regression: the residual SHRANK from the 2026-07-18 baseline (289,700 lowercase `perpetual`) to 38,083 despite the
      manifest nearly tripling in size — live writes already emit UPPERCASE; the residual is pre-fix historical rows
      awaiting the backfill `--apply`. Two other non-canonical buckets the same re-count surfaced are OUT OF SCOPE here
      (not casing issues, already tracked): `futures_chain`/`options_chain` (205,835 rows, distinct non-canonical VALUES
      from the chain-bundle writer — tracked in
      `/plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md`) and `index` (3,910 rows) +
      blank/`None` (310,662 rows) — both already the aggregated-sources doc's separate "resolve from id / remap" row,
      not a casing fold. **Corrected the stale "already-canonical — no action" claim** in
      `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s live-manifest-worklist table + D1 blockquote to
      match this measurement (unified-trading-pm, this commit) — no code shipped (this is a pure re-measurement todo;
      the actual backfill stays gated under Track 1's cutover, already tracked there, not duplicated here). Source:
      `plans/active/cefi_consolidated_closeout_2026_07_18.md`
- [x] ✅ [CODE] P2. **CLOSED — already-shipped elsewhere (2026-08-15, slot-12·backend_engineer).** Live-query OKX/Bybit
      SPOT instrument endpoints for the tokenized-equity symbol set + listing dates — this exact research already
      COMPLETE as the source doc's own Todo 1 (2026-08-13, slot-18·data_engineering worker): OKX SPOT endpoint
      (`GET .../api/v5/public/instruments?instType=SPOT`) confirmed 56 `X`-prefixed tokenized-equity tokens
      (`instCategory=3`, distinct from ordinary crypto SPOT pairs) with a real per-symbol `listTime` for every one;
      Bybit SPOT endpoint (`GET .../v5/market/instruments-info?category=spot`) confirmed 11 `xstocks`
      (`symbolType="xstocks"`) — that endpoint has no `launchTime` field, so per-symbol dates for those were later
      sourced from Tardis's own `availableSince` field (source doc Todo 5, also already complete). Full 56+11 symbol
      table + venue-plumbing findings (existing Tardis CeFi pipeline already covers both venues, no new adapter needed)
      already recorded in the source doc's own Progress Log — no new code/research needed by this batch; this batch's
      2026-08-13 conflict-check drafted the item before the source doc's own audit-day research landed later the same
      day. Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md` (Todo 1, already `[x] ✅`).
- [x] ✅ [CODE] P2. **CLOSED — already-shipped elsewhere (2026-08-15, slot-8·backend_engineer), stale-checkbox
      correction per the AO-dispatch conflict-check protocol §3.4.** Add confirmed tokenized-equity symbols to the UAC
      CeFi instrument universe with instrument_type=SPOT_PAIR + tracks_equity link. The source doc's own identical Todo
      2 was verified DONE by slot-6 on 2026-08-13 — **`unified-api-contracts@7e9a5b5d1`** ("feat(uac): register
      OKX/Bybit tokenized-equity SPOT_PAIR symbols + tracks_equity links", confirmed ancestor of
      `origin/live-defi-rollout`): added `MCD` to `CEFI_EQUITY_PERP_BASE_UNIVERSE` and 41 new `tracks_equity` links in
      `CRYPTO_EQUITY_PERP_TO_REAL_EQUITY`. Source doc's own checkbox is already `[x]` there. No code shipped by this
      batch (none needed). Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [x] ✅ [CODE] P2. **CLOSED — already-shipped elsewhere (2026-08-15, slot-8·backend_engineer), stale-checkbox
      correction per the AO-dispatch conflict-check protocol §3.4.** Add confirmed symbols to the CeFi MVP scope rule
      (mirror CEFI_EQUITY_PERP_BASE_UNIVERSE pattern). The source doc's own identical Todo 3 was verified DONE by
      slot-29 on 2026-08-13 — **`unified-api-contracts@bfad33b58`** (confirmed ancestor of `origin/live-defi-rollout`):
      new `CEFI_TOKENIZED_EQUITY_BASE_UNIVERSE` (67 raw venue bases) unioned into `CeFiMvpRule.base_ccys`, with a
      perp-gate-exempt carve-out for the no-perp-leg SPOT_PAIR cells. No code shipped by this batch (none needed).
      Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [x] ✅ [CODE] P2. **CLOSED — already-shipped elsewhere (2026-08-15, slot-8·backend_engineer), stale-checkbox
      correction per the AO-dispatch conflict-check protocol §3.4.** Register an InstrumentRecord per confirmed symbol
      dated to its real historical listing date. The source doc's own identical Todo 5 was verified DONE by slot-7 on
      2026-08-13 — no code change was needed (the Tardis adapter's existing full-universe enumeration already emits a
      `SPOT_PAIR` record per symbol dated to its real `availableSince`); a regression guard shipped —
      **`instruments-service@4eca07bac4`** (confirmed ancestor of `origin/live-defi-rollout`). No code shipped by this
      batch (none needed). Source: `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [x] ✅ [CODE] P2. Launch the CeFi Tardis/venue-native backfill for the tokenized-equity SPOT window — **LAUNCHED
      2026-08-15T15:14 UTC (slot-3·backend_engineer).** Tardis 1-VM concurrency guard cleared (0 running Tardis
      consumers, per the sourced `tardis_concurrency_guard 1 asia-northeast1-c central-element-323112` function, not a
      manual `gcloud` count) → OK, 0 running + 1 planned = 1 <= cap 1. Dry-run confirmed the same single-combined-VM
      plan every prior gated check recorded; launched for real via
      `VENUES="OKX-SPOT BYBIT-SPOT" YEARS="2025 2026" SINGLE_VM_QUEUE=1 bash scripts/vm/launch-cefi-sharded-backfill.sh`
      (deployment-service repo). VM `cefi-queue-heavy-okxspot-x2-20260815-151408` (e2-highmem-16, asia-northeast1-c)
      confirmed STAGING via `gcloud compute instances list` immediately after launch — covers OKX-SPOT + BYBIT-SPOT,
      `VM_START_DATE=2025-01-01 VM_END_DATE=2026-08-14`, data_types trades;book_snapshot_5, shuts down on completion.
      Source doc's own Todo 6 flipped in the same commit (see its Progress Log). Source:
      `plans/active/cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`
- [x] ✅ [CODE] P2. Grep prior mdps-cefi-_/mdps-tradfi-_/mdps-defi-* run.log archives (or manifest attempted_failed
      reason strings) for the exact Timestamp-vs-float TypeError signature to size the historical blast radius, and
      re-trigger record_failed→retry for any shard whose failure resolves to this exact root cause —
      market-data-processing-service@4cd46c17ba. Manifest: 0 rows matched across cefi/tradfi/defi. run.log grep: 19/294
      matched, all pre-fix `mdps-cefi-2019-*` relaunch attempts of the already-relaunched-with-fix shard — blast radius
      contained, no further retry needed. Source doc archived + resolved:
      `plans/archive/2026_08/mdps_cefi_chain_bundle_delay_features_timestamp_float_compare_2026_08_12.md`
- [x] ✅ [CODE] P2. Mechanical citation-reconciliation for todo 2 (S1-b): flip the checkbox to [x] citing
      deployment-service@e7d17f2 + the CEFI 117-shard/DeFi 3,535-shard production verification already documented
      in-doc, and update the doc's stale 'Big findings — Recommended (A): delete' section to reflect that option (B)
      finish-the-dispatcher-branch is what actually shipped Source:
      `plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md` — **DONE 2026-08-15 (slot-11)**: verified
      `deployment-service@e7d17f2` reachable on `origin/live-defi-rollout` via `git merge-base --is-ancestor`, flipped
      the source doc's todo 2 to `[x]` with a CLOSED note, and updated its "Big findings" section to record option (B)
      as what actually shipped for S1-b. No new code shipped (doc-only, per the todo's own scope).
- [x] ✅ [CODE] P2. Archive this doc via the 6-step archival ritual
      (/codex/12-agent-workflow/plan-completion-and-archival-discipline.md), repointing the 7 listed active corpus
      referrers (tradfi_satellite_ao_dispatch_batch7_2026_08_06.md, ag_closeout_audit_defi_parked_2026_08_08.md,
      mdps_features_deadcode_consolidation_2026_07_20.md, plans/active/INDEX.md, plus 3 already-repointed archive-path
      references) in the same commit Source:
      `plans/archive/2026_08/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`
      — **DONE 2026-08-15 (slot-8·backend_engineer), unified-trading-pm (this commit).** Fresh corpus-wide grep found
      the doc's own referrer list stale since 2026-08-09: `ag_closeout_audit_defi_parked_2026_08_08.md` has itself since
      been archived (frozen historical record, no repoint needed) and `plans/active/INDEX.md` carries no direct
      reference (auto-generated, self-corrects). Repointed the 3 real remaining active referrers
      (`tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` — also had stale CONTENT, corrected in place;
      `mdps_features_deadcode_consolidation_2026_07_20.md`; this doc's own frontmatter + Source citation above) +
      `git mv`'d the doc to `plans/archive/2026_08/issues/`. New finding filed separately, out of scope here:
      `plans/active/issues/launch_ml_training_vm_codex_claims_deleted_but_live_2026_08_15.md`. See the archived doc's
      own Progress Log for full detail.

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

## Progress Log

- **2026-08-15 (slot-8·backend_engineer)**: dispatched the "Add confirmed tokenized-equity symbols to the UAC CeFi
  instrument universe with instrument_type=SPOT_PAIR + tracks_equity link" todo — found the source doc
  (`cefi_okx_bybit_tokenized_equity_mvp_addition_2026_08_12.md`) had ALL FIVE of its own code/research todos already
  done (Todos 1-5, completed 2026-08-13 by slots 6/7/18/29) while this batch's mirrored copies of those same 4 items
  (research, universe registration, MVP-scope rule, InstrumentRecord registration — Todo 6/launch and Todo 7/docs were
  correctly excluded, neither mirrored here nor claimed done) sat unflipped. Verified all 3 cited commits
  (`unified-api-contracts@7e9a5b5d1`, `unified-api-contracts@bfad33b58`, `instruments-service@4eca07bac4`) are real
  ancestors of `origin/live-defi-rollout` via `git merge-base --is-ancestor` before flipping. Per the AO-dispatch
  conflict-check protocol §3.4 ("already-shipped elsewhere, checkbox just never flipped"), flipped all 4 as
  stale-checkbox corrections, not new work — no code shipped by this todo (none needed).

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

- **2026-08-15 (slot-17·backend_engineer)**: dispatched the "Promote _ShardedState out of relaunch_backfill_vm.py into a
  shared helper" todo. Found it already done: `deployment-service@0c38c00d` (2026-08-10) — the SAME commit that fixed
  the durable-state race — already extracted the class into `scripts/recovery/_durable_state.py` as a public
  `ShardedState`, with the module docstring explicitly documenting it as the shared helper the next actuator should
  import rather than re-derive. No other actuator has needed it yet, so there was nothing left to promote. No code
  shipped (none needed) — checkbox flipped citing the existing sha + file:line evidence.

- **2026-08-15 (slot-9·backend_engineer)**: shipped the "Widen canonical_writer_shaping int32->int64 coercion" todo —
  `market-data-processing-service@5b2701fa9f`. See the todo's own evidence line for full file/function detail. The
  source doc's checkbox stays stale for the same 1000-line hard-cap reason recorded in the entry immediately above
  (unrelated to this fix, pre-existing, needs the trim-under-cap follow-up todo first).

- **2026-08-15 (slot-26·backend_engineer)**: dispatched the "Generalise the test-hermeticity guard for the pytest
  fake-GCS backend persistence bug" todo. Read `deployment-service/tests/conftest.py` directly and found the
  generalisation already shipped — `_isolate_local_storage_provider_default_root` is an `autouse=True` fixture in the
  repo's ONLY `conftest.py` (confirmed via `find tests -iname conftest.py`), so it already covers every test in the
  suite, not just the two `sweep()` alert tests the todo's own wording implies are still the only ones covered.
  `git log -S` on the fixture name found a single introducing commit, `0c38c00d` — the SAME commit the source doc cites
  for the original ad-hoc fix, and the fixture's own docstring already documents the generalisation intent. No
  narrower/duplicate local-storage-root patch exists anywhere else in `tests/`. No code shipped (none needed) — checkbox
  flipped citing the existing sha. Same 1000-line hard-cap block as the two entries above prevents touching the source
  doc's own checkbox in this commit; it stays stale until the trim-under-cap follow-up lands.

- **2026-08-15 (slot-26·backend_engineer)**: dispatched the "Track 0: Capture Binance/OKX/Bybit
  indexPrice/markPrice/fundingRate for equity-perps as a first-class data_type" todo (sourced from
  `cefi_consolidated_closeout_2026_07_18.md` Track 0). Found it is a duplicate of this same batch's earlier "Capture
  Binance/OKX/Bybit indexPrice+markPrice+fundingRate" entry (already closed 2026-08-15, citing archived issue doc
  `cefi_equity_perp_mark_index_funding_derivative_ticker_already_covers_2026_08_15.md`) — both cite the identical
  underlying cryptovenue Phase 1b item, just via two different source docs (that closeout doc's own Track 0 header
  states it is an operator-ruled embed of the cryptovenue doc's Phase 1b items). Per the AO-dispatch conflict-check
  protocol (§ 3.4, "already-shipped elsewhere, checkbox just never flipped") this is a stale-checkbox correction, not
  new work and not a conflict. No code shipped (none needed). **Source doc's own checkbox ALSO flipped in this commit**
  — `cefi_consolidated_closeout_2026_07_18.md` is 693L, well under its 1000-line hard cap, so no line-cap block applies
  here (unlike several sibling entries above).

- **2026-08-15 (slot-11·backend_engineer)**: shipped the "Resolve margin_type for the ~1,578 cefi liquidation
  instrument_ids lacking @LIN/@INV suffix" todo — `unified-trading-library@8142cab5ad` (new
  `read_instruments_catalog_margin_type()` reader in `instruments_catalog_reader.py`, mirroring
  `read_instruments_catalog_contract_size()`'s shape/shared-cache exactly; `margin_type` was already in
  `CATALOG_COLUMNS` since it long predated the `contract_size` gap, so no writer-side change was needed) +
  `market-data-processing-service@6422150034` (new module-level `_resolve_margin_type_via_catalog_fallback` helper in
  `liquidations_adapter.py`, called between `infer_cefi_quote_margin`'s heuristic resolution and the
  `MalformedTickFieldError` raise — tries the catalogue only when the heuristics genuinely exhaust unresolved; extracted
  to a helper rather than inlined to keep `process_to_candles` under the ruff C901 complexity cap). 5 new UTL unit tests
  (`TestReadInstrumentsCatalogMarginType`) + 4 new MDPS unit tests (`TestUnsuffixedMarginTypeFromCatalog`, covering
  catalogue-resolves-inverse, catalogue-resolves-linear, catalogue-miss-still-fails-honestly, and
  suffixed-ids-never-call-the-fallback). Both gates green. Same 1000-line hard-cap block as the sibling entries above
  prevents flipping the source doc's own checkbox in this commit — added to the existing trim-under-cap follow-up todo
  above rather than a new one.

- **2026-08-15 (slot-27·backend_engineer)**: dispatched the "Track 0: Launch the CeFi Tardis backfill for the
  equity-perp window" todo — **GATED, not shipped.** Resolved the two open questions from the source todo's Phase-2 spec
  (`venue_launch_dates.py`/`coverage_starts.py` do NOT carry a per-symbol equity-perp listing date — that guidance is
  stale for this specific universe): live `GET fapi.binance.com/fapi/v1/exchangeInfo` cross-referenced against UAC's
  `CEFI_EQUITY_PERP_BASE_UNIVERSE` (145 bases parsed from the frozenset, 139 live-matched
  `contractType= TRADIFI_PERPETUAL` today) gives earliest `onboardDate` 2025-12-11 (XAUUSDT, a commodity base in the
  same universe — earliest genuine single-stock is TSLAUSDT 2026-01-28). Validated launch scope via `DRY_RUN=1`:
  `VENUES="BINANCE-FUTURES" YEARS="2026" LAUNCH_GROUPS="heavy" ONLY="BINANCE-FUTURES:2026:heavy" bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`
  — catalogue-mvp-driven (no `--instrument-ids` needed; MTDS resolves the perp-gated universe from IS's `by_date`
  snapshot per-day, so the launcher doesn't need a per-symbol list), `VM_START_DATE=2026-01-01` `VM_END_DATE=2026-08-14`
  `data_types=trades;book_snapshot_5`. Deliberately scoped to YEARS=2026 only + `LAUNCH_GROUPS=heavy` (not light,
  not 2025) — the Tardis single-concurrent-VM hard cap (operator 2026-07-16) means only ONE (group,data_types) bucket
  can run at a time; `LAUNCH_GROUPS` exists specifically for this "fill one free slot now, the next slice later" pattern
  (see the launcher's own comment at line 121-125). The ~3-week Dec-2025 XAU/XAG tail (pre-2026-01-01, commodities not
  single-stock equities) is knowingly NOT covered by this window — negligible relative to the 8-month 2026 window and
  cheap to add later via a `YEARS=2025 START_DATE= 2025-12-11` slice once a slot frees. **Blocked on the actual
  `gcloud compute instances create` call**: `tardis_concurrency_guard` refused — "2 running + 1 planned = 3 > 1" (cap is
  HARD, not negotiable by a worker; `FORCE=1` is explicitly an operator-only override per the launcher's own error text,
  given the exact 2026-07-14 N=3 incident it exists to prevent — 37,212 false `attempted_failed` rows + coverage
  regression). Live-identified the 2 occupants (`gcloud compute instances list` --filter matching the launcher's own
  Tardis-consumer pattern): `mtds-backfill-cefi-extended-starknet-fullhist-1` (unrelated full-history EXTENDED-STARKNET
  backfill, `PROGRESS.json` shows `last_completed_date=2024-11-29` as of 11:48Z today — genuinely deep in a multi-year
  walk, not near completion) and `mtds-backfill-cefi-pipelinecheck-20260815-114758-fdd5b9` (another slot's
  `/data-pipeline-check-mtds`-shaped smoke VM, booted ~114758, no logs yet). Neither is mine to kill and neither looks
  close to freeing the slot on any bounded timeline I can commit to within one worker session — waiting synchronously
  risks sitting idle for hours (against the async-wait-discipline HARD RULE), so this todo is left **unflipped** and the
  task is being returned to the backlog with `reason_code=GATED` rather than force-launched or silently abandoned.
  **Whoever picks this up next (possibly this same slot on a future dispatch) can run the exact validated command above
  directly** — the equity-perp-window date-math and DRY_RUN validation above do not need to be redone, only re-check the
  Tardis fleet is actually clear first
  (`gcloud compute instances list --filter='name~"^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill- cefi-" AND status=RUNNING' --zones=asia-northeast1-c --project=central-element-323112`).
  Follow-up (light group + the small Dec-2025 tail) should be a separate slice launched once this heavy slice is
  running, per the same `LAUNCH_GROUPS` pattern — not folded into this same VM.

- **2026-08-15 (slot-3·backend_engineer)**: dispatched the "Fix flaky shellcheck under host load in
  launch-expected-universe-v2-vm.sh" todo — **GATED, code correct + committed but not yet landed.** Root-caused: the
  cited flake is `TestShellcheckClean.test_shellcheck_no_errors` in
  `deployment-service/tests/unit/test_vm_zombie_watchdog.py` (parametrized one-Python-subprocess-per-launcher-script
  over ~180 `launch-*.sh` files) — the exact same anti-pattern already fixed for `test_script_syntax_validation` in
  `test_vm_launcher_scripts.py` on 2026-08-14 (see that test's own docstring: SIGPIPE/SIGTRAP/timeout under concurrent
  gate load). Applied the identical fix: batched into ONE bash subprocess looping `shellcheck --severity=error` over
  every script, collecting failures instead of spawning ~180 Python subprocesses. **Committed**
  `deployment-service@2512a92b` (rebased once mid-ship onto a peer push; content-identical diff, verified via `git diff`
  against the pre-rebase SHA that already passed QG clean). **Blocked purely on re-verification, not on the fix
  itself**: the FIRST Pass-1 `quality-gates.sh` run completed cleanly (`ALL QUALITY GATES PASSED`, 736s, sentinel
  matched HEAD) before a peer's push forced a rebase and invalidated that sentinel. Every attempt since to re-stamp the
  sentinel against the rebased HEAD (5 consecutive: 1 quickmerge-internal re-gate + 4 direct `quality-gates.sh` re-runs,
  one after a bounded 20-min wait-for-capacity loop) was killed mid-run by genuine, severe shared-host contention —
  `uptime` 1-min load 25-36 throughout, 15+ concurrent `quality-gates.sh` processes fleet-wide observed via `ps aux`
  (vs. the documented `≤2 full QGs at once` rule), one kill caught live as the qg-governor's own runtime abort-watchdog
  firing (loud `SIGTERM`, "host RAM pressure >= 75%") at 91% through the TESTS stage — this is the exact,
  already-catalogued pattern in `/plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`
  (status: resolved — the fix made kills loud/safe, it did not eliminate the underlying contention), whose own precedent
  is explicit: stop blind-retrying after repeated kills, preserve the commit, GATED-skip rather than keep burning shared
  host capacity. Following that precedent here. **Nothing left to redo**: the diff above is final and content-verified;
  whoever next picks this up (possibly this same slot) only needs a clean `quality-gates.sh` run against
  `deployment-service@2512a92b` (or its current rebase) to re-stamp the sentinel and ship via
  `quickmerge --agent --files 'tests/unit/test_vm_zombie_watchdog.py'`. Commit stays local to slot-3's
  `deployment-service` clone (not stashed, not lost) per the incident doc's own established pattern. Returning task to
  backlog with `reason_code=GATED`.

- **2026-08-15 (slot-11·backend_engineer)**: dispatched the "Mechanical citation-reconciliation for todo 2 (S1-b)" todo.
  Re-verified `deployment-service@e7d17f2` as a reachable ancestor of `origin/live-defi-rollout` via
  `git merge-base --is-ancestor` before citing. Flipped `mdps_features_deadcode_consolidation_2026_07_20.md`'s todo 2 to
  `[x]` with a CLOSED note citing the commit + the already-documented CEFI 117-shard/DeFi 3,535-shard production
  verification, and updated that doc's "Big findings — Recommended (A): delete" section with a dated UPDATE block
  recording that option (B) — finish-the-dispatcher-branch — is what actually shipped for S1-b (S1-a/S1-c unchanged,
  still match the original recommendation). No new code shipped (doc-only citation reconciliation, per the todo's own
  scope). Doc stays `assigned_vm: NA` overall — todo 8 (S3-b sports dual entrypoint) remains the sole open item and is
  still a genuine, un-superseded design adjudication.

- **2026-08-15 (slot-19·backend_engineer)**: dispatched the "instrument_type casing residual" todo. Ran a lean, bounded
  (`run-bounded-analysis.sh`, RSS-poll cap) one-off read of ONLY the manifest's `instrument_type` column (the full
  `audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` script exceeded a 4G cap on this shared host loading all
  5 audit columns across 29.48M rows) against the live `market-data-tick-cefi-prd` bucket. Result: NOT literal 100%
  UPPERCASE — 39,286 residual lowercase rows (`perpetual`/`future`/`spot_pair`), down from the 2026-07-18 baseline's
  289,700 despite the manifest nearly tripling in size (11.19M→29.48M rows), consistent with "writer already fixed,
  backfill `--apply` still drain-gated under Track 1." Corrected the aggregated-sources doc's stale "already-canonical —
  no action" claim to match. No code shipped — this todo's own scope is the re-measurement only; the actual backfill is
  already tracked under Track 1's cutover critical path, not duplicated here. See the todo's own entry above for the
  full breakdown (incl. the two out-of-scope buckets: chain-bundle `instrument_type` values already tracked by
  `cefi_chain_relabel_migration_options_futures_2026_08_15.md`, and `index`/blank rows already the aggregated-sources
  doc's separate "resolve from id / remap" row).

- **2026-08-15 (slot-7·backend_engineer)**: dispatched + shipped the "sports reference-table exporter fabricating
  http_status=200" todo — `features-service@656f2e10`, see the todo's own entry above for the fix. Notable infra
  friction worth recording for the next worker hitting it: this session's `quality-gates.sh`/`quickmerge.sh` runs
  repeatedly got silently killed (zero output, no exit code) under severe shared-host contention (load 25-39, sub-1Gi
  free RAM for a sustained ~25min window) — matches
  `plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`'s documented pattern. Plain Bash
  `run_in_background: true` invocations were the ones dying instantly with zero output every time (5 consecutive kills,
  including a quickmerge attempt that never even started its own internal rebase); wrapping the SAME commands in the
  `Monitor` tool instead succeeded reliably on the first or second try once host RAM recovered — worth trying that swap
  before escalating if `run_in_background` keeps dying silently on this host. Also hit + fixed a self-caused regression:
  extracting `_dependency_missing_gate.py` (to keep `batch_handler.py` under the 900-line file-size cap) moved a
  `record_failed` call out of `batch_handler.py`, tripping the non-shrinking `adapter_contract_baseline.yaml` ratchet
  (STEP 5.83) — fixed via a targeted 2-line hand-edit of the baseline (not a full `--regenerate-baseline`, which would
  have bundled in a large amount of unrelated fleet-wide drift from other slots' merged work) —
  `unified-trading-pm@0c49f53583`. Also filed + self-resolved repo-blocker `RB-0d4b223c` (push_race) after 3+
  consecutive quickmerge kills under sustained branch churn (code was green throughout — QG sentinel matched HEAD on
  every attempt).

- **2026-08-15 (slot-14·backend_engineer)**: **SHIPPED** the "Track 0: Launch the CeFi Tardis backfill for the
  equity-perp window" todo that slot-27 left GATED earlier today (same Progress Log, above) — no new design work needed,
  only re-checking the Tardis fleet per slot-27's own hand-off note. Live
  `gcloud compute instances list --project=central-element-323112` re-check confirmed both prior occupants slot-27
  identified (`mtds-backfill-cefi-extended-starknet-fullhist-1`, another slot's `pipelinecheck` smoke VM) are no longer
  running, and grep for the launcher's own Tardis-consumer name pattern
  (`^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-`) against the live fleet returned zero matches —
  fleet genuinely clear. Re-ran the exact `DRY_RUN=1` command slot-27 validated
  (`VENUES="BINANCE-FUTURES" YEARS="2026" LAUNCH_GROUPS="heavy" ONLY="BINANCE-FUTURES:2026:heavy" bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`)
  to reconfirm the same shard (`VM_START_DATE=2026-01-01 VM_END_DATE=2026-08-14 VM_DATA_TYPES=trades;book_snapshot_5`,
  catalogue-mvp-driven universe), then launched for real (same command, no `DRY_RUN`): `tardis_concurrency_guard` passed
  (fleet clear) and the launcher reported "All 1 VMs launched". Verified live:
  `cefi-binance-futures-2026-heavy-20260815-143847` present in `gcloud compute instances list` (zone
  `asia-northeast1-c`, status `STAGING` at verification time). No code changed — this is an infra-launch todo; the
  launcher script + its concurrency guard are the existing mechanism, used as designed. The knowingly-uncovered ~3-week
  Dec-2025 XAU/XAG tail and the `light` group slice remain the documented follow-up (slot-27's note above) — not part of
  this todo's scope.
