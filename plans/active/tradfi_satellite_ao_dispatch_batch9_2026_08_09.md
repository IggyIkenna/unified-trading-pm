---
doc_type: plan
title:
  TradFi satellite AO batch 9 — bounded-item extraction from the RECLASSIFY sweep's 2 whole-doc-ineligible tradfi docs
  (2026-08-09)
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern, produced from a targeted read of the 2 tradfi
  plan/issue docs a same-day RECLASSIFY sweep found did NOT qualify for a whole-doc `assigned_vm` flip. Both docs are
  large, mostly-closed trackers whose few remaining open items are almost entirely operator/credential-gated or already
  claimed by an active sibling batch — this run found exactly 2 genuinely bounded, conflict-clear items, both newly
  unblocked by 2026-08-07 operator rulings that predate both docs' own most recent satellite-batch siblings
  (`tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`, `..._batch7_2026_08_06.md`), whose own Deferred sections still
  carry the pre-ruling "operator-gated" framing. Conflict-checked against tradfi_satellite_ao_dispatch_batch6/7/8 (all
  active) — zero collisions.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-data-processing-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-extraction, batch-9, orphan-extraction]
related:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    features-service/features_service/delta_one/app/core/candle_resampler.py,
  ]
depends_on: []
source: >-
  Targeted satellite-batch extraction (2026-08-09), scoped to the 18-doc list a same-day RECLASSIFY sweep flagged as NOT
  whole-doc-flip-eligible (14 defi + 2 tradfi + 2 prediction). Both tradfi candidates were read end to end; extractable
  items conflict-checked against every active tradfi satellite batch (6, 7, 8) plus the source docs' own Progress Log
  entries confirming the operator rulings that unblock them post-date those batches' drafting.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 9 — 2026-08-09

Only 2 items qualified from the 2 candidate docs — both docs are near-exhausted trackers (most open work is
operator/credential-gated, already extracted into batch6/7/8, or a pure design-question that stays genuinely NA). Yield
is deliberately thin; reported honestly rather than padded.

## Todos

- [ ] [SCRIPT] P3. **Physical GCS cleanup of the old ICE-Databento instrument parquets** — RULED 2026-08-07 (operator,
      via consolidated NA-blocker-digest audit): GO AHEAD, conditional on the twin-verify safety check (0 consumers) the
      doc's own pre-existing gate already requires. Run the twin-verify (confirm 0 consumers of the old ICE-Databento
      instrument parquets, per the tombstone-reconciliation precedent already applied to the ICE whole-venue purge in
      the same source doc), then a FRESH `gcs_bucket_soft_delete_retention_seconds(bucket)` check on the target bucket —
      cite the actual returned value; if ≥604800s (7 days), execute the delete via the sanctioned UTL helpers per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (the operator's GO-AHEAD already covers the delete
      itself; the twin-verify + reversibility check is the sole remaining gate, not a fresh operator ask). Repos:
      deployment-service, instruments-service. Source: `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`
      (ICE-Databento parquet GCS-cleanup todo, "From `tradfi_databento_subscription_universe_lockdown_2026_06_18`"
      section). Done when: the twin-verify confirms 0 consumers, the soft-delete value is cited, and the delete is
      executed (or explicitly re-gated if the check returns below threshold).
- [ ] [BACKEND] P2. **Build the MDPS-owned `ohlcv_1m`→`ohlcv_15m`/`ohlcv_24h` aggregator for CBOE VX-futures** — RULED
      2026-08-07 (operator): YES, build it, MDPS-owned (not a features-service resampler on `vix_features` alone) —
      aggregate `ohlcv_1m` up to `ohlcv_15m`/`ohlcv_24h` once, upstream of every consumer (delta-one groups need
      `ohlcv_24h`; general-purpose, not CBOE-only if other consumers emerge). Reuse
      `features-service/features_service/delta_one/app/core/candle_resampler.py`'s exact-OHLC resampling logic
      (open=first/high=max/low=min/close=last/volume=sum, right-edge labeled, polars `group_by_dynamic`) if it fits —
      the existing `TradfiOhlcv15mAdapter`/`GranularityDetector` in market-data-processing-service are bare
      passthroughs/labelers, NOT resamplers, so this is genuinely new build, not a wiring fix. Wire the output to
      satisfy the `unified_api_contracts.canonical.domain.features.required_inputs`'s `"vix_features"` entry
      (`InputReq(asset_group="tradfi", data_type="ohlcv_15m", ...)`, currently unfed since CBOE's only historical
      `ohlcv_15m` source was formally retired). Scope to CBOE VX-futures only for the first cut (the one venue with a
      live product need) — do not over-generalize to every Databento-covered venue in the same pass. Repo:
      market-data-processing-service (+ features-service if the resampler is extracted to a shared location instead of
      duplicated). Source: `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`
      ("RULED 2026-08-07 — YES, build it, MDPS-owned" todo). Done when: a real `ohlcv_15m` and `ohlcv_24h` row lands in
      the manifest for CBOE VX-futures via the new aggregator (not a passthrough), `quality-gates.sh` green, and
      `vix_features`'s required-input is genuinely fed.

      **BLOCKED 2026-08-09 (slot-28, backend_engineer) — dispatched, found genuine POLICY CONFLICT, not an
          implementation gap.** The aggregation mechanism itself already ships + is proven live for CME/NASDAQ/NYSE
          (`mdps-backfill-tradfi-20260803-104812`: 99,711 candles, 788 captured rows) — this todo's own "genuinely new
          build" framing is stale. The real blocker: CBOE VX-futures raw `ohlcv_1m`/`ohlcv_1s` is captured ONLY at
          `instrument_type=futures_chain` grain (confirmed live on GCS, 2,942 captured rows), which
          `market-data-processing-service@68f95f6`'s `_INSTRUMENT_TYPES_EXCLUDED_FROM_COARSE_TIMEFRAMES` (shipped
          2026-08-06, one day before this todo's ruling) deliberately excludes from `ohlcv_15m`/`ohlcv_24h` — justified at
          the time as "no downstream consumer expects combo-grain 15m/24h candles," a premise this todo's own 2026-08-07
          ruling now contradicts for CBOE/VIX specifically. Filed
          `issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md` with 2 candidate fix paths +
          an `[OPERATOR]` decision todo rather than unilaterally reopen the CME-combo crash that exclusion was built to
          close. This todo stays `- [ ]` pending that decision.

## Not extracted this batch — items that stay behind

- `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s "Launch the ES_OPT backfill" + "Wire the ES_OPT post-launch
  manifest-verify" todos — both already extracted verbatim into the ACTIVE
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` todo #2, which has a live autonomous watcher session tracking the
  singleton Databento lock as of 2026-08-07 — conflict, not re-drafted.
- `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s "purge the 2 residual tradfi catalogue legs" todo
  (NASDAQ/NYSE mis-classified `SPOT_PAIR` rows + the 12 cefi-singles' EQUITY rows) — the doc's own text explicitly
  states this "needs its own explicit operator confirmation before executing (not blanket-covered by the 4-leg
  go-ahead)" — genuinely NOT yet operator-ruled, unlike the ICE-parquet item above. Stays behind.
- `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s top-level "tradfi — same gates" bullet (Gated Phase 2
  rollup) — a header-level umbrella summary, not itself an actionable item.
- `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` has no other open `- [ ]`
  checkboxes — every other finding in the doc (mbp_10, corporate_action_confirmed/earnings_result, YAHOO_FINANCE phantom
  venue, CBOE treasury ohlcv_24h routing) is already resolved/shipped per the doc's own Resolution sections.

## Progress Log

- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside its finalize twin. 2
  conflict-clear todos extracted, both unblocked by 2026-08-07 operator rulings that post-date
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`/`..._batch7_2026_08_06.md`'s own drafting — both of which still
  list these items as "Deferred — operator-gated" in their own text (stale as of that ruling). Conflict-check run
  against batch6/7/8 (all active) — zero collisions on the 2 extracted items.
- 2026-08-09 (slot-28, backend_engineer): dispatched todo 2 (CBOE VX-futures aggregator). Found the aggregation
  mechanism already ships/works (proven live for CME/NASDAQ/NYSE); the real blocker is a policy conflict between
  `market-data-processing-service@68f95f6`'s 2026-08-06 `futures_chain`-exclusion default-ruling and this todo's own
  2026-08-07 ruling — CBOE VX raw data is captured exclusively at the excluded `futures_chain` grain. Filed
  `issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md` (2 candidate fixes + `[OPERATOR]`
  decision todo) rather than absorb an unplanned architecture-judgment call. Todo 2 left `- [ ]`, annotated in place
  with the finding. No code shipped this session (nothing was safe to ship without the decision).
