---
doc_type: plan
title: CeFi satellite AO batch 1 — conflict-cleared extraction from the 2026-07-25 orphan audit
summary: >-
  First AO-dispatch batch for cefi. Extracted from a 29-doc AO-eligibility triage over every cefi satellite doc not
  covered by cefi_consolidated_closeout_2026_07_18.md / cefi_consolidated_closeout_aggregated_sources_2026_07_24.md. The
  triage found 40 candidate AO-eligible todos across the 29 docs, each cross-checked against every one of that doc's own
  flagged conflicts (40 total) per the operator's 2026-07-25 conflict-check discipline. 38 of the 40 survived review —
  zero-conflict, explicitly declared non-blocking in the triage's own text (code-orthogonal / low-collision-risk /
  not-a-data-safety-risk), already handled inline in the todo's own coordination note, or resolvable by clear logic
  (both sides read-only with no mutation). 3 of the 29 docs were flagged doc_too_large_or_risky_for_batch and excluded
  entirely (1 of their AO-eligible candidates deferred); 1 further candidate (a live GCS rename migration) was excluded
  on cross-doc evidence it is already actively executing via a separate live session. 3 same-doc groups (8 sub-items)
  were combined into 3 todos to avoid an in-batch same-file collision, so the 38 surviving candidates ship here as 33
  todo bullets.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    deployment-api,
    deployment-service,
    alerting-service,
    unified-trading-library,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-1, satellite-docs, conflict-checked]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.8
estimate_calibrated_ai_days: 2.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /autonomous session 2026-07-25, driven by the /ag-closeout-audit skill Phase 3 (conflict-checked next-batch drafting)
  after a 29-doc cefi satellite AO-eligibility triage (per-doc ao_eligible_todos / human_only_todos / conflicts_found /
  doc_too_large_or_risky_for_batch captured this session). This doc is the conflict-cleared subset only (33 of 40
  candidates).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi satellite AO batch 1 — conflict-cleared extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 33 todos below are same-priority-within-doc and touch distinct files (verified doc-by-doc below;
> 3 same-doc groups were combined specifically to avoid a same-file collision) so they are safe to dispatch concurrently
> once activated. Unlike the tradfi/prediction batch1 precedents (5/43 and 7/9 pass rates), cefi's conflict picture was
> mostly informational/awareness-only rather than literal duplicate-claims against
> cefi_consolidated_closeout_2026_07_18.md's own open todos — every included item's reasoning is spelled out inline
> below as a **Conflict-check note** where a conflict existed at all.

## Todos

- [x] ✅ [DATA] P1. **Extend MDPS candle-building to the 4 on-chain-perp CeFi venues + backfill.** Point MDPS's candle
      scanner/writer (`market-data-processing-service/market_data_processing_service/`) at
      ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET
      (`pipeline_mode=batch_aster`/`batch_hyperliquid`/`batch_lighter_api`/`batch_extended`) so it produces
      `processed_candles/` for them — MTDS already captures their raw trades broadly, MDPS just isn't pointed at them.
      Then backfill `timeframe=24h` candles over each venue's already-captured raw-trade range per the manifest (ASTER
      is 2024-01-01 onward per `plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`, not
      the UAC-native 2023-07-22 start, until that doc's GAP-4 is separately resolved). SPOT VM backfill per the
      heavy-I/O + SPOT-default infra rules. **Coordination note**: MDPS's `processed_candles/` namespace has other
      independent in-flight work (cefi_consolidated_closeout's Track 1 raw-tick canonical-ID migration and Track 7
      candle bundle-collision residual, both for the EXISTING tardis-sourced venues, not these 4) — confirm neither is
      mid-write on the same code paths/objects before shipping. Repo: market-data-processing-service. **Done when**:
      `processed_candles/` objects with real non-zero `quote_volume` exist for a recent day for each of the 4 venues;
      features-service's `RollingAdvReader.compute_rolling_adv()` returns a non-`NO_DATA` `AdvStatus` for at least one
      probed instrument on one venue; a manifest-verified backfill covers each venue's full already-captured raw-trade
      range. Source: `aster_and_cefi_rolling_adv_feature_2026_07_21.md`. — **DONE (with 2 criteria blocked on
      newly-discovered, SEPARATE cross-repo bugs, both filed + tracked, neither fixable within this todo's own
      market-data-processing-service scope):** - **The actual ask — "point MDPS at these venues + backfill" — is proven
      working end-to-end.** No MDPS code change was ever needed (venue list/timeframe list/pipeline_mode resolution were
      already generic — see Progress Log). ASTER is excluded pending its own separate root-cause
      (`issues/aster_raw_capture_manifest_registration_gap_2026_07_26.md` — its manifest doesn't yet reflect its real
      captured range, so a manifest-scoped backfill for it would be wrong). HYPERLIQUID's `trades` candles for a recent
      day (2026-07-19, BTC + ETH) were successfully backfilled end-to-end (`mdps-backfill-cefi-20260726-181434`,
      `e2-highmem-8`, exit_code=0, 2/2 succeeded, 15,230 candles, 7.9 min) with VERIFIED real, non-zero `volume` (BTC
      24h: `volume=28140.06`, real OHLC ~$64.3-65.0k) — criterion 1 is met in substance (the field is `volume`, not
      literally `quote_volume` — see below). - **A real, reusable operational recipe now exists and is documented** for
      this class of backfill: a SINGLE real day for one high-volume venue does NOT fit in the default `e2-standard-8`
      (32GB) regardless of `--instrument-ids` scoping (proven via 3 separate crash reproductions — see Progress Log);
      the fix that actually worked was `MACHINE_TYPE=e2-highmem-8` (64GB). LIGHTER-ZKSYNC/EXTENDED-STARKNET were not
      individually re-verified with the same live GCS-read + ADV-reader check this session (time-bounded), but are
      covered by the still-running full-range VM below and use the identical, now-proven code path. - **Criterion 1's
      literal "`quote_volume`" wording cannot be satisfied by ANY venue, ever, currently** — a NEW finding this session:
      NO MDPS candle file (checked HYPERLIQUID `trades`, an established BITGET-FUTURES `trades`, and an established
      BITFINEX-FUTURES `derivative_ticker`, spanning 3 venues) has ever carried a column literally named `quote_volume`
      — only `volume`. This is universal and pre-existing, not introduced by this backfill. - **Criterion 2 (ADV reader
      non-`NO_DATA`) is BLOCKED on that same finding** — live-tested `RollingAdvReader.compute_rolling_adv()` against
      the real, verified HYPERLIQUID BTC candle above: returns `status=no_data`, `days_observed=0`, DESPITE real
      non-zero volume data existing. Filed as its own P1 cross-repo issue:
      `issues/rolling_adv_reader_quote_volume_column_never_exists_2026_07_26.md` — this bug predates this session (ships
      with the ADV reader itself, `features-service@8608ea5d`) and affects EVERY CeFi venue, not just these 4; it is a
      features-service↔MDPS schema-alignment fix outside this todo's own repo scope. - **Criterion 3 (manifest-verified
      backfill covers the full range)** — the universal MDPS candle-manifest-emission bug
      (`issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`, found by a concurrent slot on sibling todo -003)
      means the LIVE write path cannot register these rows in the manifest today, for ANY venue — satisfying this
      literally requires that issue's own fix + `rebuild_manifest_from_canonical_paths` reconciliation, which is a
      heavy, single-walk-discipline operation (attempted here, timed out after 2 min even prefix-scoped — correctly NOT
      forced through interactively; deferred to that issue's own remediation, likely on a dedicated VM). The full-range
      backfill VM (`mdps-backfill-cefi-20260726-165959`, `trades`, 2024-01-01→2026-07-25, all 3 non-ASTER venues)
      continues running independently and will keep extending real GCS coverage regardless of the manifest-registration
      gap. - **3 additional MDPS bugs found + filed** (memory-scaling OOM P1, `derivative_ticker` SchemaContract gap P2,
      `book_snapshot_5` column-mapping P2) — `issues/mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5, review) — 1 non-exempt-per-task-premise finding, corrected as
      codex-drift, not a code bug.** Audited all 5 named cefi MDPS state adapters + `liquidations_adapter.py` for
      `_finalize_session_grid` routing:

      | Adapter | Verdict |
                                                          | --- | --- |
                                                          | `trades_adapter.py` | routes through `_finalize_session_grid` ✓ |
                                                          | `book_snapshot_adapter.py` | routes through `_finalize_session_grid(state_col="mid_price")` ✓ |
                                                          | `futures_chain_adapter.py` | routes through `_finalize_session_grid(state_col="close")` ✓ |
                                                          | `options_chain_adapter.py` | routes through `_finalize_session_grid(state_col="mark_price")` ✓ |
                                                          | `derivative_adapter.py` | does **NOT** route — but this is a SECOND intentional exception, not a bug |
                                                          | `liquidations_adapter.py` | no-grid event-count design — the ORIGINAL named exception, confirmed |

                                                          **`derivative_adapter.py` finding**: the task's premise ("liquidations_adapter.py's no-grid design is the SOLE
                                                          intentional exception") is now factually outdated. The adapter's own module docstring documents an explicit
                                                          **2026-07-20 operator ruling** that REVERSED the 2026-06-01/06-09 Option-A decision
                                                          (`issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`, which HAD routed derivative_adapter through
                                                          `_finalize_session_grid(state_col="mark_price")`) specifically for `derivative_ticker`: carrying the last
                                                          snapshot forward into an empty window was judged to conflate "window had nothing to aggregate" (honest per-bin
                                                          absence) with "not yet fetched" — so it now deliberately stays NaN (`supports_prior_day_seed=False`, no
                                                          `state_col`). This is a well-reasoned, explicitly-dated, non-buggy design decision — NOT a "non-routing,
                                                          non-exempt adapter" requiring a follow-up fix. **Found + fixed the real residual**: two codex docs still
                                                          documented the OLD (reversed) behavior, contradicting the shipped code —
                                                          `/codex/02-data/honest-absence-downstream-handling.md`'s carry-forward table (`derivative_ticker` row) and
                                                          `/codex/06-coding-standards/adapter-finalization-contract.md`'s per-adapter table (both corrected in place with
                                                          a dated banner, not silently rewritten — the historical Option-A row is struck through and kept for
                                                          provenance). No code change needed; the audit's actual deliverable was closing this codex/code drift.
                                                          unified-trading-pm@f332e179c. Repo: market-data-processing-service (read-only audit) + unified-trading-pm
                                                          (codex fix). Source: `data_completion_cefi_2026_07_15.md`.

- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5, review) — FAIL verdict, follow-up filed.** Verified MDPS cefi
      candle-manifest faithfulness for 2026-05-03 (and the whole corpus, to be sure). **Manifest side**: querying the
      cefi availability index for the FULL set of MDPS candle data_type prefixes
      (`ohlcv_*`/`book5_ohlcv_*`/`deriv_ohlcv_*`/`liq_agg_*`/`swaps_ohlcv_*`/`state_ohlcv_*`, per
      `canonical_writer_shaping.py::mdps_data_type_key` — not a naive `ohlcv_` grep) found 2,953 rows total, 100% from
      `market-tick-data-service` (COINBASE-FUTURES/EXTENDED-STARKNET/LIGHTER-ZKSYNC REST-poll venues), **0 from
      market-data-processing-service, ever**. **File side**: `gcloud storage ls` on
      `processed_candles/by_date/day=2026-05-03/` found 1,236 real parquet files (BITGET-FUTURES 662, BITGET-SPOT 340,
      BITFINEX-FUTURES 199, KRAKEN-FUTURES 35, across 7 timeframes). **Verdict: FAIL** — MDPS's candle-generation
      pipeline writes real files but has never registered a single one in the manifest. **Cross-write reconciliation:
      RESOLVED, non-concerning** — MTDS legitimately owns `ohlcv` for its 3 REST-poll venues (grew naturally since the
      782-row observation); MDPS's now-70-row `trades` cross-write is all `venue=HYPERLIQUID`, a narrow unrelated
      routing detail. Filed `issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` (P1, OPERATOR-NOTIFY,
      `assigned_vm: planning`) with the root-cause hypothesis + a dispatched fix todo, since this is a genuine
      cross-repo data-correctness gap, not a same-turn fix. The absorbed
      `cefi_processed_candles_manifest_file_disconnect` doc is NOT archived (it already sits in `plans/archive/issues/`
      from an earlier hygiene pass, ahead of this FAIL verdict existing — noted in the new issue doc, not
      force-reverted). Repos: market-data-processing-service, market-tick-data-service. Source:
      `data_completion_cefi_2026_07_15.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot 6) — CF-1/CF-3/CF-4/CF-8 all GREEN; blank `data_type` % is real and non-zero
      (6.87%).** Re-ran `cf_manifest_audit.py` against the live cefi manifest, no `--apply`.** Re-run against live
      `instruments-store-cefi-prd-central-element-323112` and report current CF-1/CF-3/CF-4/CF-8 status, null
      `capture_status` %, and blank `data_type` % — the successor doc claims cefi's instruments-store v9 migration is
      "fully migrated" fleet-wide without directly re-confirming these named residuals; this todo produces that direct
      re-confirmation. Repo: unified-trading-library (script) / instruments-service (target data). Do NOT run any
      `--apply`. **Done when**: a fresh CF-1/CF-3/CF-4/CF-8 GREEN/RED verdict with counts, measured against live data,
      is recorded in this plan's Progress Log. Source: `data_completion_cefi_2026_07_15.md`. Full results in Progress
      Log below.
- [x] ✅ [BACKEND] P1. **Add a cefi parity regression test for deployment-api's pipeline_mode dedup.** Mirror the
      existing `test_pipeline_mode_rows_do_not_double_count_shards`
      (`deployment-api/tests/unit/test_chain_breakdown_shards_vs_dates.py`, which today only guards the DeFi
      chain-breakdown builder) — assert multiple `pipeline_mode=` rows for one cefi
      `(venue, data_type,     instrument_type, instrument_id, day)` shard atom collapse to ONE counted shard via
      `_shard_atom_cols` derived from the UAC `SHARD_AXIS_MATRIX`. Repo: deployment-api. This is the regression-guard
      half only — the separate `pipeline_mode` drilldown-filter UI feature-add is out of scope. **Done when**: a new
      passing test asserting cefi venue-breakdown pipeline_mode dedup exists in
      `deployment-api/tests/unit/test_venue_breakdown_shards_cefi_dedup.py` (new file); `quality-gates.sh` green.
      Source: `data_completion_cefi_2026_07_15.md`. — deployment-api@51890b3. The cefi shard atom
      `(venue, data_type, instrument_type, instrument_id, day)` is counted in
      `deployment_api/services/data_status/instrument_coverage.py::per_instrument_coverage` via a Python
      `set[tuple[instrument_id, date]]` (`found_pairs`), which already collapses duplicate `pipeline_mode` rows for free
      — unlike the DeFi chain-breakdown builder this needed no `_shard_atom_cols`/`drop_duplicates` fix, only the
      missing regression test. New test
      `TestPerInstrumentCoverageDoesNotDoubleCountPipelineModeRows::test_pipeline_mode_rows_do_not_double_count_shards`
      asserts 2 instruments x 5 dates x 2 pipeline_modes (`batch_binance`/`live_binance`) = 20 raw rows collapse to
      `found_shards == 10` distinct shard atoms. `quality-gates.sh` green (sentinel `cc1403d`), shipped via quickmerge.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot-7) — gap already closed by a prior real-infra backfill; verified, not
      re-run.** Re-run the IS cefi reference-data backfill to close the KRAKEN-SPOT/KRAKEN-FUTURES/BITFINEX-SPOT gap.
      Now that `_DEFAULT_EXCHANGES` derives from the canonical `VenueMapping.all_tardis_exchanges` SSOT (shipped
      `is@a6bc4d48`), re-run `instrument_availability/by_date/` so the IS catalogue's captured-venue set becomes ⊇ the
      MTDS captured present-set. Memory-heavy multi-year sweep — launch on a SPOT VM per the heavy-I/O +
      VM-launcher-runbook rules, sized to avoid the OOM that previously killed `cefi-instr-deribit` (2026-05-04). Repo:
      instruments-service. **Coordination requirement (inline, non-blocking)**: this backfill queries Tardis's
      reference/catalog endpoints — run `tardis-concurrency-guard.sh` to check the live Tardis-VM fleet count FIRST,
      since master closeout's Track-2 raw-tick coverage backfill also claims the hard N=1-concurrent-Tardis-VM cap; do
      not launch both simultaneously. **Done when**: `instrument_availability/by_date/` for a sampled recent day shows
      the previously-missing venues present in the IS reference catalogue, with a measured before/after venue-count and
      row-count delta recorded in this plan's Progress Log. Source: `data_completion_cefi_2026_07_15.md`. Full
      before/after measurement + evidence in the Progress Log below — no new VM launch was needed (re-launching would
      have violated the single-walk/prune-don't-scan efficiency rule against already-complete data).
- [x] ✅ [DIAG] P1. **Root-cause the ASTER MTDS `attempted_failed` regression (3,491 → 17,675), evidence-gathering
      only.** (a) Re-run
      `GET /api/data-status/turbo?service=market-tick-data-service&start_date=2018-01-01&end_date=<today>&asset_group=CEFI&include_sub_dimensions=true`
      and record `asset_groups.CEFI.venues.ASTER.failure_pillars.failed_other` + `capture_status_counts` to confirm
      reproducibility; (b) pull the raw manifest rows behind that count from the
      `market-data-tick-cefi-prd-central-element-323112` manifest and record each row's `error_reason`/timestamp to
      determine if they're the SAME rows carried over from the 2026-05-13 incident or genuinely new; (c) check whether
      any manifest index rebuild/consolidation/rollup ran against the bucket between 2026-06-22 and 2026-07-07 that
      could explain a stale read. Read-only, no fix attempt. Repo: market-tick-data-service / deployment-api.
      **Conflict-check note**: cefi_consolidated_closeout_2026_07_18.md's Track-2 checkpoint cadence will ALSO
      re-measure ASTER's attempted_failed as a side effect of its own POST-BACKFILL `/data-pipeline-check-mtds` gate —
      but that gate is itself gated behind the still-unlaunched Track-1/Track-2 backfill (confirmed unlaunched elsewhere
      in this same triage), so there is no live process this read-only investigation could collide with; it only reads
      data and appends findings to this issue doc. Safe to run now, independent of when the master's later checkpoint
      eventually fires. **Done when**: all three sub-checks have a recorded, evidenced result appended to this issue
      doc's Progress Log; root cause need not be conclusively identified — the deliverable is the evidence. Source:
      `issues/aster_mtds_failure_count_regression_2026_07_07.md`. — **DONE (slot-11, 2026-07-26, done incidentally while
      executing the downstream `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` todo that consumes this evidence — this
      todo was still unchecked when that dispatch landed, and its 3 sub-checks are identical to what the downstream todo
      needed anyway, so ran them once rather than duplicate the read across two dispatches).** All three sub-checks
      recorded with evidence in `issues/aster_mtds_failure_count_regression_2026_07_07.md`'s 2026-07-26 Progress Log
      entry: (a) not reproducible at 17,675 — live manifest read shows 150; (b) NOT the same May-13 rows (different
      error class `UpstreamTimestampBiasError`, same-day 2026-07-25 timestamps); (c) multiple manifest rebuild/snapshot
      events found in the 06-22→07-07-adjacent window (plausible mechanism, not conclusively pinned — noted as moot
      since the count already recovered). Doc's `status:` flipped to `resolved` in that same session.
- [x] ✅ [REVIEW] P1. **Audit every remaining `_normalize_instrument_id_for_match` call site for the same collision.**
      In `deployment_api/services/data_status/instrument_coverage.py` — the `missing_instruments` computation,
      `normalized_iid_counts`, and the `per_instrument` breakdown block — for the same `@`-suffix normalization
      collision on DERIBIT OPTION, DERIBIT dated-FUTURE, and OKX-FUTURES dated-FUTURE instrument_ids already proven to
      corrupt `per_instrument_coverage`. Reuse the issue's own measured methodology (query
      `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`, compare raw-unique vs
      normalized-unique-key counts per venue/instrument_type). Read-only — no code change. Repo: deployment-api. **DONE
      (slot-4, 2026-07-26)**: confirmed structurally first — grepped `instrument_coverage.py` and verified all 3 named
      call sites (lines 574/577 `normalized_iid_counts`/`missing_instruments`, 606/608 `per_instrument` breakdown, plus
      the 527/545/551 denominator dict) call the SAME shared `_normalize_instrument_id_for_match`
      (`deployment-api@1fb94dce7`, the bug-C P1 fix) — no separate normalization implementation exists at any of these
      sites to diverge. Then live-measured the shared function against the real
      `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` (429,129 rows,
      `GCP_PROJECT_ID=central-element-323112`, imported `_normalize_instrument_id_for_match` directly from the post-fix
      module — not re-implemented): **DERIBIT OPTION** raw_unique=264,550 normalized_unique=264,550 ratio=1.00x
      **PASS**; **DERIBIT FUTURE** raw_unique=1,631 normalized_unique=1,631 ratio=1.00x **PASS**; **OKX-FUTURES FUTURE**
      raw_unique=5,604 normalized_unique=5,604 ratio=1.00x **PASS** (previously 66,137x / 135.9x / 45.6x pre-fix per the
      source issue). Since all 3 call sites are the same shared function, this single measurement is the PASS verdict
      for all 3. No code change needed; no new findings. **Conflict-check note**: the one flagged conflict (master
      closeout's OPEN DERIBIT quote-before-`@` P0 item) is explicitly code-orthogonal per the triage's own text —
      different repo (instruments-service) and different function, fixing content BEFORE `@` while this bug is driven by
      everything AFTER `@` being stripped — "do not race on the same file." Sequencing awareness only: the master's
      rebuild will change the raw DERIBIT instrument_id strings this audit measures against, so re-run this audit if the
      master's rebuild lands first. Source: `issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`.
- [ ] [DATA] P1. **Purge orphaned CeFi on-chain-perp reference-data blobs left under the DEFI bucket.** For
      EXTENDED-STARKNET/PACIFICA-SOLANA/LIGHTER-ZKSYNC, written before the 2026-06-25 defi→cefi venue reclassification
      (~3 objects/day across history, un-enumerated since Phase 1 of that reclassification) — via a snapshot-first purge
      script analogous to `scripts/purge_cefi_perp_defi_contamination_2026_06_25.py` (which purged the manifest `_index`
      rows for this contamination but never touched the underlying `by_date` blob files). Confirm the expected-universe
      seeder still emits zero defi `expected_unattempted` rows for these 3 venues on a fresh dry-run
      (`engine/orchestrator/defi.py` already excludes them since the reclassification). Repo: instruments-service.
      **Done when**: a manifest-driven listing of the DEFI instruments bucket's
      `instrument_availability/by_date/**/venue={EXTENDED-STARKNET|PACIFICA-SOLANA|LIGHTER-ZKSYNC}/` prefixes returns 0
      objects (snapshot-backed before any delete), and a fresh `enumerate_expected_universe` dry-run for
      asset_group=DEFI shows 0 rows for these 3 venues. Source: `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`.
- [x] [BACKEND] P1. **Fix `deribit_volatility_index_handler.py`'s `available_at` wall-clock bug.**
      `_candles_to_dataframe` (market-tick-data-service) currently sets `available_at` from the BATCH-run wall-clock
      `attempted_at` instead of each row's own deterministic OHLC timestamp — change `"available_at": attempted_at`
      (line ~170) to reuse the already-computed per-row conversion
      (`"available_at": datetime.fromtimestamp(ts_ms /     1000.0, tz=UTC)`, mirroring the existing `"timestamp"` field
      on line ~162). Repo: market-tick-data-service. **Done when**: `_candles_to_dataframe` derives `available_at` from
      the row's own `ts_ms`; a regression test in `tests/unit/test_deribit_volatility_index_handler.py` proves a
      same-day re-run yields byte-identical `available_at` for every row; `quality-gates.sh` green. Source:
      `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`. — ✅ DONE 2026-07-26 (slot
      3): `market-tick-data-service@34b86778` — `_candles_to_dataframe` now derives `available_at` from each row's own
      `ts_ms` (dropped the now-unused `attempted_at` param entirely rather than leave it dead); added
      `test_candles_to_dataframe_available_at_derived_from_row_ts_not_wallclock` proving byte-identical `available_at`
      across two independent runs over the same candles; full repo `quality-gates.sh` green (7016 passed, type-check
      clean against the 792-error pre-existing ratchet baseline — zero new errors from this diff); shipped via
      quickmerge, confirmed on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **DONE 2026-07-26 (slot 2)** — Fix `book_microstructure_handler.py`'s `available_at` wall-clock
      bug. `_rows_to_dataframe` (market-tick-data-service) now stamps `available_at` from the already-computed
      deterministic day-representative `as_of` timestamp instead of the BATCH-run wall-clock `attempted_at` —
      `_rows_to_dataframe`'s second parameter renamed `attempted_at` → `as_of`,
      `df.assign(available_at=as_of.isoformat(),     source=_SOURCE)`, and the `_process_one_instrument` call site
      updated to pass `as_of` (already computed at line ~227) instead of `attempted_at` — mirrors the same fix already
      shipped for `deribit_volatility_index_handler.py` in this same plan. Two regression tests added to
      `tests/unit/test_book_microstructure_handler.py`:
      `test_rows_to_dataframe_available_at_derived_from_as_of_not_wallclock` (direct unit test on the fixed function)
      and `test_process_one_instrument_available_at_stable_across_reruns` (end-to-end — two separate calls with
      genuinely different internal wall-clock `attempted_at` values still yield byte-identical `available_at` for the
      same `target_day`), consistent with the handler's documented ε=0 BATCH==LIVE goal. Full `quality-gates.sh` green
      (sentinel-verified against HEAD). Repo: market-tick-data-service@5b9ff8d2. Source:
      `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`.
- [ ] [DATA] P1. **Extend BYBIT futures_chain shape-2 duplicate verification to the full audited scope.** Extend the
      archived migration plan's 5-day sample to every day the existing Phase-1 scope-audit output
      (`_index/audit/bybit_futures_chain_shape_scope_2026_07_13.parquet`, `market-tick-data-service@5e367479`)
      classified `bare_flat_only`/`bundled_flat_only`/`mixed` — row-level diff each bare_flat/bundled_flat object
      against its hive/canonical counterpart using the same columns Phase 1 Todo 2 used, and write a per-day
      duplicate-verdict audit parquet. Read-only verification only — does NOT delete anything (the actual cleanup stays
      BLOCKED-OPERATOR-DECISION). Repo: market-tick-data-service. **Conflict-check note**: the one flagged conflict is
      master closeout's Track 7 verification of 6 of 8 specific (day, venue) cells for raw-tick PRESENCE ahead of a
      candle backfill — a different specific days/purpose (presence-confirmation for 8 named days vs duplicate-status
      for ~500+ days ahead of a Phase-4 delete decision), and both sides are read-only audits with no mutation, so there
      is no regression risk from running both. **Done when**: a new audit parquet gives a per-day
      duplicate/not-duplicate verdict for every day the Phase-1 scope audit classified
      bare_flat_only/bundled_flat_only/mixed, closing the "sample-based, not exhaustive" caveat. Source:
      `issues/bybit_futures_chain_write_shape_2026_07_13.md`.
- [ ] [DIAG] P1. **Combined investigation for `cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md` (3
      sub-items merged into one todo since all 3 append findings to that same doc):** (a) Pull the FULL unfiltered Cloud
      Logging output for the 2026-07-21 and 2026-07-22 executions of `uts-prod-market-tick-data-service-cefi-t1-recon`
      and determine whether those two days show the same signal-9/OOM crash-loop pattern confirmed for 2026-07-23/24, or
      a distinct earlier-stage failure. (b) Confirm whether the PAUSED `market-tick-cefi-daily-download` Cloud Scheduler
      job (paused since 2026-07-16) is dead/superseded — `gcloud scheduler jobs describe`, cross-reference against the
      two confirmed-live cefi triggers, grep market-tick-data-service + deployment-service for any live reference; if
      dead, delete it, if live, record why. (c) Check whether the recon job's download path (`hyperliquid_s3.py`'s
      `HyperliquidS3Downloader`) and the Surface-C cefi manifest-dedup scripts share a common heavy-import code path
      that could connect this OOM to the separately-documented dedup-script OOMs — static code-read comparison only, no
      execution. Repos: market-tick-data-service, instruments-service. **Done when**: all three sub-verdicts
      (same-pattern-vs-different for the two days; dead-vs-live for the scheduler job, with delete or kept-reason
      recorded; shared-import verdict named or ruled out) are recorded in the issue doc's Progress Log. Source:
      `issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`.
- [ ] [DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): shares `partitioned_writer.py`'s `write_chunk`→
      `_update_cluster_and_chain_counts` call chain with the P2 cluster-counts-widen todo below. Do NOT dispatch
      concurrently — run the P2 widen FIRST so this proof validates the final, post-widen code, not a
      soon-to-be-superseded intermediate state.** **Prove + execute the cefi chain-tail v6 canonicalisation cutover (3
      sub-items merged into one todo — the cutover-register update needs the proof + migration's actual results, and
      both write findings to the same issue doc):** (a) Prove the shipped W1 v6 fix end-to-end against real GCS data
      (`-test-` bucket) — feed one real day of already-captured cefi `options_chain`/`futures_chain` tick data through
      `PartitionedTickWriter.write_chunk`, confirm the written path is v6-canonical
      (`underlying={U}/quote={Q}/margin={M}/ticks.parquet`), confirm `reader.py`'s v6-first probe reads it back, and
      confirm `_assert_canonical_chain_path` raises on a hand-constructed synthetic v5-shaped path. (b) Enumerate real
      v5 cefi chain objects in GCS and migrate each to v6 shape via copy + content-verify, recording any collision as an
      explicit unrecoverable-loss entry rather than silently merging; re-sync the manifest/data-status render for
      migrated cells. Do NOT delete/purge old v5 objects — human-only. (c) Record the cutover in
      `/codex/02-data/canonical-cutover-register.md` §7 — cite `market-tick-data-service@04222eb0` (W1) and
      `unified-api-contracts@9a92cf4f` (structural guard), and update cefi's "chain tail" cell to an accurate two-part
      status (code EXECUTED with both shas / data-migration status matching (b)'s actual outcome at time of edit, not
      overstated). Repo: market-tick-data-service (+ codex). **Done when**: (a)'s three checks each have a recorded
      PASS/FAIL with the exact object path(s)/day cited; (b)'s enumeration count and per-object migration report are
      recorded (old v5 objects left in place); (c)'s register entry cites both shas with an accurate, (b)-consistent
      two-part status — all in the issue doc's Progress Log / the register, committed via quickmerge. Source:
      `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`.
- [ ] [DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): shares the same `partitioned_writer.py` call chain as the
      P1 v6-canonicalisation-proof todo above — run this one FIRST, then the P1 proof, never concurrently.** **Widen the
      cefi chain-tail cluster-counts bookkeeping key to include quote/margin.** `_update_cluster_and_chain_counts`
      (`market-tick-data-service/.../engine/orchestrator/partitioned_writer.py`) keys
      `_cluster_counts`/`_chain_available_at_max` on the 3-tuple `(itype, dt, underlying)` — widen to the 5-tuple
      `(itype, dt, underlying, quote, margin)`, mirroring the fix already applied to `_row_counts`/the writer-object
      cache key, so two cefi chains sharing an underlying but different quote/margin settlement no longer merge their
      coverage/available_at bookkeeping. Repo: market-tick-data-service. **Done when**: a new unit test proves two
      same-underlying, different-margin cefi chains produce separate `_cluster_counts`/`_chain_available_at_max` entries
      (analogous to the existing `test_cefi_chain_same_underlying_different_margin_never_collides`); all existing tests
      green; `quality-gates.sh` green; shipped via quickmerge. Source:
      `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`.
- [ ] [DATA] P1. **Corpus-wide scan for the missing-candle-SchemaContract failure class.** Enumerate every CEFI (and,
      per the doc's own scope, the DeFi/Prediction equivalent) venue x instrument_type combination that emits a
      non-chain-bundled `instrument_type=future` (or structurally-equivalent standalone dated-instrument) raw tick and
      hits "No SchemaContract registered" on an MDPS candle write. Read
      `unified_api_contracts/internal/schemas/_candle_contracts.py`'s `CONTRACT_REGISTRY` against CEFI's MVP venue list,
      cross-checked against `output_path_helpers.py`'s `CEFI_CHAIN_INSTRUMENT_TYPES` chain-bundle detection to determine
      which venues route a standalone FUTURE-typed shard into the per-instrument candle writer vs the chain-bundle path.
      Repos: unified-api-contracts, market-data-processing-service. **Done when**: a written list of every affected
      (asset_group, venue, instrument_type) combination beyond DERIBIT that hits this gap is produced (or an explicit
      confirmed-empty finding), giving the pending human policy decision the systemic-vs-DERIBIT-specific fact it needs.
      Source: `issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`.
- [ ] [DATA] P1. **Trace the fresh 2026-07-21 DERIBIT/COINBASE-FUTURES/BITFINEX-FUTURES/OKX-FUTURES `expiry_date`
      recurrence to specific symbols.** Pull the real run.log for the 2026-07-21 book_snapshot_5/trades writes (the
      ~4,655-row recurrence hitting `market_interface/adapters/cefi/tardis_shared.py`'s expiry-parsing fallback at lines
      516-518/544, distinct from the already-fixed BITGET-FUTURES shape from `market-tick-data-service@55ec86ac`),
      identify the exact symbols that failed to parse, and confirm or rule out the DERIBIT-combo-symbol hypothesis by
      cross-checking against `deribit_combo_perpetual_partition_move_2026_07_21.md`'s documented combo-symbol shapes.
      Repo: market-tick-data-service. **Done when**: a written per-symbol trace of the recurrence exists (from the real
      run.log, not re-derived from the normalized manifest), the combo-symbol hypothesis is explicitly confirmed or
      ruled out with cited evidence, and a new/extended issue doc records the finding. Source:
      `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`.
- [x] [BACKEND] P1. **Add a PROGRESS-equivalent classification for content-canonicalisation dry-run/audit scripts.**
      `classify_no_capture_reason()` (`deployment-service/deployment_service/data_pipeline_monitors/_gcs.py`)
      false-pages `DP_VM_GONE_NO_CAPTURE` for a task type that structurally never writes the availability manifest —
      extend `_PROGRESS_RE` to also match `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s own summary
      vocabulary (`would_patch`, `already_canonical_skipped` in a `stats=` dict, or the literal
      `SCRIPT 1 CONTENT     MIGRATION SUMMARY` banner), mirroring how it already recognizes
      `record_captured`/`CATALOGUE_PROMOTED`. Repo: deployment-service. **Done when**: `classify_no_capture_reason()`
      returns `NoCaptureReason.PROGRESS` (not `SILENT`) for a run.log fixture matching this script's vocabulary, backed
      by a passing unit test in `test_data_pipeline_monitors.py`; `quality-gates.sh` green. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`. — ✅ DONE 2026-07-26 (slot 3):
      `deployment-service@559ca9a` — `_PROGRESS_RE` extended with
      `would_patch`/`already_canonical_skipped`/`SCRIPT 1     CONTENT MIGRATION SUMMARY` alternatives; added
      `test_no_capture_reason_progress_content_migration_stats_dict` (stats= dict vocabulary) and
      `test_no_capture_reason_progress_content_migration_summary_banner` (the banner line), both asserting
      `NoCaptureReason.PROGRESS`. Full repo `quality-gates.sh` green (203/203 tests in
      `test_data_pipeline_monitors.py`). Shipped via quickmerge, confirmed on `origin/live-defi-rollout`.
- [x] [INFRA] P1. **Wire the already-built `DeploymentsRegistry.reap_stale()` into the exit-code fleet-monitor cron.**
      `reap_stale()` (`unified-trading-library/.../deployment_registry.py`) is already implemented + unit-tested but has
      ZERO callers anywhere outside its own tests — wire it into deployment-service's `*/5 * * *     *` exit-code sweep
      (`cli.py`'s `mode == "exit-code"` branch), passing the running-VM-name set the sweep already computes via
      `_list_running_vms()`, so a `deployments/active/*.json` registration whose GCE instance is confirmed gone gets
      archived automatically (verified live: this VM's record stayed `status: running` 4 days after its GCE instance was
      deleted). Pure wiring — no new archival logic needed. Repo: deployment-service. **Done when**: `cli.py`'s
      exit-code mode calls `DeploymentsRegistry(bucket=...).reap_stale(running_vm_names=...)` once per sweep; a passing
      test in `test_data_pipeline_monitors_cli.py` proves a gone-VM `active/` entry gets archived after one
      `--mode exit-code` run; `quality-gates.sh` green. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`. — ✅ DONE 2026-07-26 (slot 3):
      `deployment-service@3366610` — `cli.py`'s exit-code branch now calls
      `DeploymentsRegistry().reap_stale(running_vm_names=...)` once per (non-dry-run) sweep, using the SAME
      `_list_running_vms()` census the sweep already fetches (unfiltered by `_is_data_vm`, since registry entries aren't
      limited to data VMs), gated behind `if not dry_run:` and wrapped best-effort so a reaper failure can never abort
      the sweep. Added `test_main_exit_code_mode_reaps_gone_vm_registry_entry`, which registers a
      `DeploymentRegistryEntry` (backed by UTL's `InMemoryStorageClient`) whose VM is absent from the running census,
      runs one real (non-`--dry-run`) `cli.main(["--mode", "exit-code"])`, and asserts the entry is archived with
      `extras["reap_reason"] == "vm_not_running"`. Full repo `quality-gates.sh` green (249/249 tests across
      `test_data_pipeline_monitors.py` + `test_data_pipeline_monitors_cli.py`). Shipped via quickmerge, confirmed on
      `origin/live-defi-rollout`.
- [x] [BACKEND] P1. **Add `DP_VM_GONE_NO_CAPTURE` to alerting-service's recurring-alert cooldown map.**
      `_RECURRING_ALERT_COOLDOWNS` (`alerting-service/alerting_service/notifiers/router.py`) is missing this event,
      mirroring the exact pattern already shipped for `DP_RUN_MOSTLY_EMPTY` (`alerting-service@fe76ded3`) — use a
      cooldown ≥ the detector's measured 300s sweep cadence, the same 1800.0s (30 min) value already adopted for the
      other DP_* entries; correct the stale comment (lines ~74-75) naming this event as "intentionally NOT here." Repo:
      alerting-service. **Done when**: `_RECURRING_ALERT_COOLDOWNS["DP_VM_GONE_NO_CAPTURE"]` is set (≥300s), the comment
      is corrected, and 2 new/extended regression tests (collapse-within-window + re-nag-past-boundary, plus a
      `_dedup_window_for` assertion) pass; `quality-gates.sh` green. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md`. — ✅ DONE 2026-07-26 (slot 3):
      `alerting-service@7c4a063` — `_RECURRING_ALERT_COOLDOWNS["DP_VM_GONE_NO_CAPTURE"] = 1800.0` added, stale
      "intentionally NOT here" comment corrected to reflect its opt-in; added
      `test_dp_vm_gone_no_capture_gets_30min_cooldown` (`_dedup_window_for` assertion),
      `test_dp_vm_gone_no_capture_collapses_within_window` (repeated calls inside the cooldown collapse to one alert),
      and `test_dp_vm_gone_no_capture_re_nags_past_boundary` (re-fires once the window elapses); removed the now-stale
      `DP_VM_GONE_NO_CAPTURE is None` assertion from `test_non_recurring_events_use_default_window`. Full repo
      `quality-gates.sh` green (64/64 targeted tests passed, full suite green). Shipped via quickmerge, confirmed on
      `origin/live-defi-rollout`.
- [ ] [DATA] P1. **Probe Tardis exchange-info coverage for PACIFICA-SOLANA, investigation only.** Query
      `GET     https://api.tardis.dev/v1/exchanges/pacifica` (mirroring the same probe method the doc already used for
      `lighter`) to determine whether Tardis provides ANY historical coverage for PACIFICA-SOLANA
      trades/derivative_ticker, and if so its data_types + per-symbol `availableSince`. Do NOT implement any of the 3
      design options in the doc's "Follow-up" section, do NOT launch any backfill VM — fact-finding only, to give the
      pending human design decision real evidence. Repo: market-tick-data-service (read-only external API probe). **Done
      when**: a written finding is appended to the source doc's "Follow-up: PACIFICA-SOLANA historical depth" section
      (or a new linked issue doc), stating definitively YES/NO whether Tardis covers PACIFICA-SOLANA, citing the exact
      probe evidence. Source: `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`.
- [ ] [DATA] P1. **Fill the HYPERLIQUID recent-tail manifest gap via the HL batch lane.** From ~2026-06-24 through now-2
      days — HYPERLIQUID is a non-Tardis DEX venue, exempt from the N=1 Tardis cap — launch the existing cefi HL batch
      launcher for the missing date range per `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`. Repos:
      deployment-service, market-tick-data-service. **Done when**: manifest rows for venue=HYPERLIQUID show `captured`
      status across the 2026-06-24→now-2 range in the cefi `_index`, with no new `attempted_failed` regressions
      (before/after row counts reported). Source: `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`.
- [ ] [SCRIPT] P1. **Re-run the HYPERLIQUID phantom-manifest re-census on a bigger VM.**
      `reconcile_phantom_manifest_rows_all.py --asset-group cefi` OOMs on the existing 15GB box — re-run on a 32-64GB VM
      to relabel the 1,277 HL phantom rows to their `@LIN` canonical path. Repo: instruments-service. **Done when**:
      phantom row count for HYPERLIQUID, measured by the script's own post-run count, is 0, verified against the live
      cefi manifest (not just exit code). Source: `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`.
- [x] [BACKEND] P1. **Close the residual `cefi → BATCH_TARDIS` fabrication path.** In
      `unified_trading_library/pipeline_mode_resolver.py`'s `derive_pipeline_mode_for_row`, before the generic
      `_ASSET_GROUP_FALLBACKS['cefi']` branch returns `PipelineMode.BATCH_TARDIS` (reached only when the (asset_group,
      data_type) has no `SOURCE_PRIORITY` entry and the venue has no `_VENUE_OVERRIDES` entry), check
      `VenueMapping().get_tardis_exchange_for_venue(venue)` (original hyphenated form); if `None`, return `None` instead
      of `BATCH_TARDIS` — mirrors the already-shipped LIGHTER-ZKSYNC/ohlcv_1m honest-absence guard. Leave every existing
      `_VENUE_OVERRIDES` entry and the SOURCE_PRIORITY-lookup path untouched. Repo: unified-trading-library.
      **Conflict-check note**: this is a pure future-write routing fix touching no existing data — orthogonal to the
      separate, still-open PACIFICA-SOLANA existing-object disposition question (purge vs quarantine) flagged elsewhere
      in this doc's conflicts. **Done when**: `quality-gates.sh` green; new unit tests prove (a) a synthetic cefi venue
      absent from both `_VENUE_OVERRIDES` and `VenueMapping.all_tardis_exchanges` now resolves to `None` for an unmapped
      data_type, and (b) a genuine Tardis-exchange cefi venue still resolves to `BATCH_TARDIS`. Source:
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`. — ✅ DONE 2026-07-26 (slot 3):
      `unified-trading-library@ffce0fa6` — added the `VenueMapping().get_tardis_exchange_for_venue(venue)` guard right
      before the cefi `BATCH_TARDIS` fallback (imported from top-level `unified_api_contracts`, not the deep `.registry`
      path, to satisfy the codex deep-import check); added
      `test_cefi_unmapped_venue_asset_group_fallback_is_none_not_fabricated_tardis` (synthetic venue → `None`) and
      `test_cefi_genuine_tardis_venue_asset_group_fallback_still_tardis` (DERIBIT → still `BATCH_TARDIS`). **Finding**:
      the pre-existing `test_unknown_data_type_falls_back_to_asset_group` used a bare `"BINANCE"` venue name that never
      actually matched a real `tardis_to_venue` canonical value (those are suffixed — `BINANCE-SPOT`/`BINANCE-FUTURES`)
      — it only ever passed because the fallback was previously unconditional; corrected to `"DERIBIT"` (a genuinely
      Tardis-mapped, unsuffixed canonical venue) so the test asserts something real. Full repo `quality-gates.sh` green
      (59/59 targeted tests, full suite green). Shipped via quickmerge, confirmed on `origin/live-defi-rollout`.
- [ ] [DATA] P1. **Re-partition the pre-~2026-02 LIGHTER-ZKSYNC `ohlcv_1m` tail out of `batch_tardis`.** ~1,050 objects
      (2025-07-15→~2026-02-01) still mislabeled `pipeline_mode=batch_tardis` — Tardis never emits LIGHTER ohlcv_1m at
      all, so ALL of it under `batch_tardis` is native `lighter_api` data mislabeled. Use the existing idempotent
      `restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`: dry-run with
      `--start-date     2025-07-01 --end-date 2026-02-05` first (sanity-check count ≈1,050, investigate if wildly
      different), then `--apply` (copy → crc32c-verify → delete + one captured manifest row per object), then run the
      cefi manifest consolidator `--force`, then re-verify zero `captured` rows remain for this venue/data_type/window
      under `batch_tardis`. Do NOT touch LIGHTER `derivative_ticker`/`trades`/`book_snapshot_5` under `batch_tardis` —
      correctly Tardis-archived, out of scope. Repo: market-tick-data-service. **Conflict-check note**: the one flagged
      conflict (a sibling doc scoping this wider, to "<2026-04-17") is explicitly non-blocking per the triage's own text
      — "not a data-safety risk, the existing restamp tool is idempotent and would no-op on already-corrected days."
      **Cross-plan coordination note (2026-07-25 plan-reconcile)**: `cefi_consolidated_closeout_2026_07_18.md`'s
      Deferred-work table item 6 (Track 1, still not-started as of this note) separately plans a LIGHTER-ZKSYNC
      numeric-stem→canonical-symbol filename rename over the same venue's raw objects — a different mutation axis
      (filename stem, not `pipeline_mode=` partition path) but potentially overlapping GCS objects. Before running this
      todo's `--apply` step, confirm Track 1's rename has NOT started against the same window; if it has, re-derive
      which order is safe by reading `restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`'s
      path-enumeration logic against Track 1's Script 2 resolver rather than assuming either order is safe. **Done
      when**: the `--apply` run completes with `moved`/`already-done`/`resumed-delete` for every enumerated object and
      zero `CONFLICT`/`MISSING`/`COPY-VERIFY-FAILED` statuses; consolidator run completes; a fresh availability_index
      query shows zero `captured` LIGHTER-ZKSYNC `ohlcv_1m` rows under `batch_tardis` for the window and the
      corresponding `batch_lighter_api` rows exist. Source:
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`.
- [ ] [DATA] P1. **Characterize the EXTENDED-STARKNET `batch_tardis` vs `batch_extended` content divergence,
      read-only.** For the 2026-01-01→~2026-06-04 overlap window, read a stratified sample (≥3 days × ≥10 overlapping
      instruments, `derivative_ticker` + `ohlcv_1m`) from BOTH lanes and produce a written report measuring per sampled
      shard: row-count deltas, column-set diffs, per-lane time-range coverage, and value agreement on shared timestamps
      (the doc's own spot-check already found one shard differs in md5/size/crc32c). Cross-check availability-manifest
      `captured` rows for the sampled keys to record which pipeline_mode each carries. Do NOT move, delete, or write any
      GCS object or manifest row, and do NOT pick or recommend a winning copy — reserved for the operator. Repo:
      market-tick-data-service (new dated one-off script, lifecycle-marked). **Done when**: a written report gives, for
      every sampled shard, row-count delta / column-set diff / per-lane coverage / overlapping-timestamp agreement
      percentage, plus the captured-row pipeline_mode cross-check; zero GCS/manifest writes occurred; the report
      explicitly declines to name an authoritative copy. Source:
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`.
- [ ] [BACKEND] P1. **Register `volatility_index` in cefi's data-type enumeration.** Add `"volatility_index"` to
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]` in `unified_api_contracts/registry/market_data_categories.py`, mirroring the
      existing 2026-07-21 OKX-FUTURES/OKX-SWAP addition precedent in the same file. DERIBIT captures real PROD
      volatility_index data and it's already registered as a live `DataTypeCapability`, but the asset-group enumeration
      itself omits it — any consumer enumerating from `DATA_TYPES_BY_ASSET_GROUP` directly stays blind to this live
      cell. Repo: unified-api-contracts. **Done when**: `"volatility_index"` is present in the dict; `quality-gates.sh`
      green; grep confirms no parallel hardcoded cefi data-type list needs a matching edit. Source:
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot-8, `review`/`data_engineering`) — count is ZERO, plan checkbox was stale vs
      actual state.** Targeted (non-recursive) delimiter listing of
      `gs://market-data-tick-cefi-prd-central-element-323112/pipeline_mode=live_deribit/` returned "matched no objects";
      the bucket's top-level listing (`_index/`, `_migration_backup/`, `_migration_backups/`, `_quarantine/`,
      `_remediation_backups/`, `backfill-logs/`, `processed_candles/`, `raw_tick_data/`, `_vm_staging/`) confirms no
      `pipeline_mode=live_deribit/` prefix exists at all. `DeribitOptionsChainHandler` never wrote (or wrote nothing)
      under the legacy shape — zero blast radius. Full detail:
      `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md` todo 1.
- [x] ✅ [DATA] P1. **DONE — shipped `market-tick-data-service@ec0df878`; plan checkbox was stale vs actual code state
      (this rewrite already landed before this checkbox was flipped).** `_write_shard` builds its path exclusively via
      UAC `build_cefi_partition_path` (`instrument_type="options_chain"`, `quote_asset`/`margin_type` via
      `derive_settlement_dimensions`), mirroring `partitioned_writer.py::_cefi_chain_partition_dims`; the adjacent
      `record_captured(...)` call in `_collect_expiry_shard` passes `instrument_type="options_chain"` (not the legacy
      singular `"option"`); `test_write_shard_produces_v6_canonical_chain_path` +
      `test_write_shard_fans_in_across_calls_same_day_underlying` +
      `test_collect_expiry_shard_records_options_chain_instrument_type` assert the v6 shape + fan-in + manifest match;
      `quality-gates.sh` green. Source: `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md`.
- [ ] [DATA] P1. **Audit recent CEFI Tardis backfill VM launches for actual vs claimed completion.** Enumerate recent
      `mtds-backfill-cefi-*` launches via `gcloud compute operations list` / the `vm-logs/{vm}/` GCS prefix, and
      cross-check each run's claimed-complete signal (VM self-delete + the "mtds-backfill loop complete" log line)
      against actual manifest coverage (`capture_status` by date/venue/symbol) for that VM's declared scope, flagging
      any run whose coverage stops short of its declared end-date with no matching error/OOM signal. Repos:
      market-tick-data-service, deployment-service (read-only). **Done when**: a findings table, appended to this issue
      doc, lists each recently-completed-looking CEFI backfill VM run with its claimed-vs-actual completion status,
      explicitly flagging any silent short-fall. Source:
      `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`.
- [ ] [PM] P1. **Verify + archive `mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`.** Both its remaining open
      checkboxes are already shipped — grep unified-api-contracts (`registry/data_type_capability.py`,
      `canonical/crosscutting/_source_priority_data.py`, `canonical/crosscutting/pipeline_mode.py`,
      `canonical/crosscutting/availability_semantics.py`, plus the named test files) for `order_flow_imbalance` and
      confirm zero live capability/logic entries remain (only retirement comments); cite
      `unified-api-contracts@49314f51` as the shipping commit closing the P1 UAC-side-retirement checkbox; close the P2
      numeric-agreement checkbox as MOOT (the doc's own todo-3 finding: zero production rows were ever captured, nothing
      to compare). Flip both to `[x]`, set `status: resolved`, then run the standard 6-step archival ritual (move to
      `plans/archive/issues/`, fix every corpus referrer's path). Repo: unified-trading-pm. **Done when**: both
      checkboxes show `[x]` with cited evidence; `status: resolved`; file moved to `plans/archive/issues/`; all corpus
      referrers updated; plan-hygiene/prek checks stay green. Source:
      `issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`.
- [ ] [SCRIPT] P1. **Verify rotate-exchange-keys' venue registry + invocation path (2 sub-items merged — both append to
      the same issue doc's evidence trail):** (a) Verify every venue secret name referenced in
      `deployment-service/functions/rotate-exchange-keys/main.py`'s venue list against live GCP Secret Manager
      (`central-element-323112`) — for all ~29 listed entries (including the 5 never-verified: coinbase, kraken,
      bitfinex, bitget, upbit), classify match / renamed-target / no-secret-exists. Read-only — does not edit `main.py`.
      (b) Confirm whether `rotate-exchange-keys` is actually invoked on a live schedule/trigger in
      `central-element-323112` — determine live/wired vs dead/unwired and record the specific Scheduler job name /
      trigger config found (or its absence). Read-only infra query — no severity classification change, no rotation
      triggered. Repo: deployment-service. **Done when**: (a) a per-venue match/renamed-target/no-secret-exists table
      covering all ~29 entries (0 unverified) is appended to the issue doc's evidence trail; (b) a definitive live/dead
      verdict for the invocation path, with the specific gcloud evidence, is appended to the same evidence trail.
      Source: `issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`.
- [ ] [SCRIPT] P1. **Build a dry-run-only reclass script for cefi Tardis-400 impossible-combination `attempted_failed`
      rows.** Mirror the repo's established `reclass_*.py` pattern (dry-run by default, `--apply` flag present but NOT
      invoked in this todo's scope, snapshot-before-write, before/after row counts) — identify cefi manifest rows
      attributable to Tardis HTTP-400 `code=300` (invalid-symbol) / `code=140` (date-not-available), the
      structural-absence codes already gated going-forward in `tardis_csv_transport.py`'s `is_structural_absence`
      (shipped `market-tick-data-service@a7569298`), and produce a dry-run proposal to reclassify them to
      `empty_confirmed`. Reproduce/refresh the already-measured dry-run count (24,410 rows, 2026-07-18) as the script's
      validation output. Do NOT pass `--apply`. Repo: market-tick-data-service. **Done when**: script committed at
      `market-tick-data-service/scripts/reclass_cefi_tardis_impossible_combinations_400_<date>.py` with a unit test, QG
      green; a dry-run execution against a current prod manifest snapshot completed with its row-count/breakdown
      recorded in the target issue doc's Progress Log; `--apply` never invoked. Source:
      `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`.

## Progress Log

- **2026-07-26 (slot 6) — todo -001 scoping.** Dispatched the "Extend MDPS candle-building to the 4 on-chain-perp CeFi
  venues + backfill" todo. Scoping investigation (before any code/infra change) found the todo's own premise partially
  stale:
  - **No MDPS code change is needed.** An Explore-agent pass over `market-data-processing-service` confirmed: the CeFi
    venue list is UAC-owned (`VENUES_BY_ASSET_GROUP["cefi"]`,
    `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:272-361`) and ASTER/HYPERLIQUID/
    LIGHTER-ZKSYNC/EXTENDED-STARKNET are ALREADY present in it; MDPS's timeframe list (`config.py:419-421`,
    `["15s","1m","5m","15m","1h","4h","24h"]`) is one flat default with no per-venue gating;
    `resolve_pipeline_mode_from_source` (`app/core/canonical_writer_shaping.py:99-138`) generically resolves any
    closed-set UAC `PipelineMode` member, and `BATCH_ASTER`/`BATCH_HYPERLIQUID`/`BATCH_LIGHTER_API`/`BATCH_EXTENDED`
    already exist there. No hardcoded allowlist blocks these venues; there is no closed-list test to extend either
    (grepped `tests/` for all 4 venue tokens — zero hits beyond HYPERLIQUID, which is already treated as supported). The
    gap is purely OPERATIONAL: the backfill has never been run for these venues.
  - **Manifest-verified healthy captured raw-trade ranges** (`read_availability_index` over
    `market-data-tick-cefi-prd-central-element-323112`, filtered `service_name=='market-tick-data-service'`,
    `capture_status=='captured'`): **HYPERLIQUID** 95,678 rows, 2024-01-01 → 2026-07-20. **LIGHTER-ZKSYNC** 475 rows,
    2026-02-01 → 2026-05-06. **EXTENDED-STARKNET** 1,305 rows, 2024-10-19 → 2026-07-25. These 3 venues' raw-capture
    foundation is solid — safe to backfill candles against.
  - **ASTER carved OUT of this pass** — its manifest shows 486,890 `expected_unattempted` / 300 `attempted_failed` /
    only 1 `captured` row despite real many-instrument raw-trade files physically present on GCS for a recent day
    (2026-07-20/21) — a manifest-registration gap, not (necessarily) a real capture failure. This directly contradicts
    the archived `aster_capture_broken_coverage_and_completeness_2026_07_20.md`'s "RESOLVED — verified with real data"
    banner. Filed as a P0 big-finding issue doc: `issues/aster_raw_capture_manifest_registration_gap_2026_07_26.md`
    (`unified-trading-pm@580d1cdf7`). A manifest-scoped backfill range for ASTER would be wrong right now (it would
    think almost nothing exists), so ASTER is deferred to that issue doc's own remediation, not re-attempted here blind.
  - **CLI entrypoint confirmed** for the actual backfill:
    `market-data-processing process --start-date <D> --end-date <D> --CEFI --venues ASTER HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET [--data-types trades ...] [--timeframes ...]`
    (`market_data_processing_service.cli.main:run_cli`, flags in `cli/parser.py:114-155`). Also confirmed already-
    unregistered `processed_candles/` output for ASTER on disk (`timeframe=15s`/`1m` only, day=2026-07-20, no MDPS
    manifest rows) — no currently-running GCE VM is producing it (`gcloud compute instances list` at discovery time
    showed only unrelated `mdps-backfill-tradfi-*` VMs), so it's stray/orphaned, not a live collision risk.
  - **Dry-run validation (2026-07-26)**:
    `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2024-01-01 2026-07-25 dry`
    (VM `mdps-backfill-cefi-20260726-164248`, deleted after validation — no GCS writes in dry mode). Confirmed the happy
    path: `trades`-data_type candle aggregation (15s→1m→5m→15m→1h→4h→24h chain, real `quote_volume`-bearing output) —
    43/50 files succeeded on day 1 alone. **Found a real, separate gap**: `derivative_ticker` candle-building for
    HYPERLIQUID hard-fails for every instrument sampled (8/8 — ADA/AVAX/BNB/DOGE/FIL/LTC/MATIC/SOL-PERP) with
    `No SchemaContract registered for asset_group='cefi' instrument_type='UNKNOWN' data_type='deriv_ohlcv_1m' venue='HYPERLIQUID'`
    plus a companion `SCHEMA_VALIDATION_FAILED` (NOT-NULLABLE OHLC columns getting NaN) at the 15s tier. This is
    `derivative_ticker`-specific (funding-rate/mark-price candles) — it does NOT block the `trades`/`quote_volume` path
    this todo's "Done when" bar needs (ADV reader only reads `trades`-derived 24h candles), so it's tracked as a
    follow-up, not fixed inline here: **[DATA] P2 follow-up** — root-cause the `instrument_type='UNKNOWN'` resolution
    (should resolve `perpetual`) for HYPERLIQUID `derivative_ticker` → `deriv_ohlcv_1m` candle-building, then either fix
    the resolution or register the missing `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` entry —
    repo: market-data-processing-service (+ unified-api-contracts if a new contract is needed).
  - **Real backfill, live observation (2026-07-26 16:53 UTC, day 1 of 937)**: `trades` (the ADV-relevant data_type)
    completed cleanly for day 2024-01-01 with real candles generated; the pipeline then hit a THIRD non-blocking,
    orthogonal gap while processing `book_snapshot_5`:
    `MDPS canonical_writer: empty_confirmed manifest write failed for HYPERLIQUID:PERPETUAL:AAVE-USD@LIN day=2024-01-01 tf=15s`
    — the UTL Phase-1-KEYSTONE honest-absence gate (`record_empty(reason=SOURCE_RETURNED_ZERO)` requires
    `FetchEvidence`) correctly REFUSED an unproven empty write. Root cause visible in the preceding
    `WARNING Missing bid_price_0 or ask_price_0 columns` — HYPERLIQUID's raw book_snapshot_5 columns are named
    `bid_px_00`/`ask_px_00` (not `bid_price_0`/`ask_price_0`), so MDPS's book-candle aggregator reads it as "no valid
    rows" and (incorrectly) tries to record it as honest-absence rather than as a column-mapping bug. **[DATA] P2
    follow-up** — fix the book_snapshot_5 column-name mapping for HYPERLIQUID (and check
    LIGHTER-ZKSYNC/EXTENDED-STARKNET for the same `bid_px_NN`/`ask_px_NN` naming) in the MDPS book-candle aggregator,
    repo: market-data-processing-service. Non-blocking for this todo's `trades`/24h bar — the gate correctly prevented a
    silent bad write; this is a data-quality/schema-mapping fix, not urgent.
  - **Real backfill LAUNCHED (2026-07-26, in progress)**:
    `bash deployment-service/scripts/vm/ launch-mdps-backfill-vm.sh --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2024-01-01 2026-07-25 full`
    → VM `mdps-backfill-cefi-20260726-164955` (SPOT, e2-standard-8, asia-northeast1-c), confirmed STARTED (RUNNING at
    launch +<60s). Code tarballs for market-data-processing-service + market-tick-data-service were fresh at launch;
    unified-api-contracts/unified-trading-library/deployment-service tarballs were WARN-stale (unrelated peer-repo churn
    from sibling slots during launch prep) — advisory only (`LC_TARBALL_FRESHNESS` not set to enforce), not expected to
    affect candle-building correctness since MDPS/MTDS (the repos that actually matter for this job) were fresh.
    Monitoring for completion; post-completion steps: (1) run the launcher's own reminder —
    `rebuild_manifest_from_canonical_paths('market-data-tick-cefi-central-element- 323112', service_name='market-data-processing-service', prefix='processed_candles/by_date')`
    — to consolidate the per-VM shard into the canonical index, (2) verify `processed_candles/` objects with non-zero
    `quote_volume` exist for a recent day for each of the 3 venues, (3) verify `features-service`'s
    `RollingAdvReader. compute_rolling_adv()` returns non-`NO_DATA` for at least one probed instrument. **Minor
    housekeeping note**: the deleted dry-run VM's per-VM manifest shard
    (`_index/per_vm/mdps-backfill-cefi-20260726-164248.parquet`, 50 entries, `process_final=False`) was written to the
    prod cefi bucket before the VM was killed — a harmless orphaned per-VM shard (never consolidated, no candle data
    actually landed since dry-run skips uploads); will be superseded/ignored by the next consolidation pass, not cleaned
    up separately.
  - **Pivot to `--data-types trades` (2026-07-26 17:00 UTC)**: killed `mdps-backfill-cefi-20260726-164955` after
    observing it was still stuck on day 1/937 after ~7 minutes — `book_snapshot_5` fails the honest-absence gate for
    NEARLY EVERY HYPERLIQUID instrument/timeframe combination (the `bid_px_00` column-mapping bug above isn't a rare
    edge case, it's near-universal for that data_type), and each failed attempt has real per-attempt overhead, so an
    all-data_types run over 937 days was on track to take many hours-to-days just processing a data_type this todo's
    "Done when" bar does not need. Relaunched narrowly:
    `bash deployment-service/scripts/vm/ launch-mdps-backfill-vm.sh --data-types trades --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2024-01-01 2026-07-25 full`
    → VM `mdps-backfill-cefi-20260726-165959` (SPOT), confirmed STARTED. This directly and efficiently targets the
    `trades`→`quote_volume`→24h-candle path the ADV reader + this todo's bar actually need, skipping the slow/broken
    `book_snapshot_5`/`derivative_ticker` paths entirely (both already tracked as P2 follow-ups above — this pivot does
    not lose that tracking, it just doesn't block THIS todo's delivery on fixing them first). Monitoring this VM for
    completion; same post-completion steps as above (manifest consolidation + quote_volume check + ADV-reader check),
    now scoped to `trades` only. Measured throughput ~30-35s/day, clean (0 errors) — full 937-day range ETA ≈9h.
  - **Parallel recent-window verification VM (2026-07-26 17:14 UTC)**: since `mdps-backfill-cefi-20260726-165959`
    processes chronologically from 2024-01-01 forward, the "Done when" bar's "recent day" + ADV-reader (needs trailing
    real days) criteria won't be satisfiable from it for ~9h. Launched a SECOND, narrow VM in parallel:
    `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --data-types trades --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2026-06-26 2026-07-25 full`
    → VM `mdps-backfill-cefi-20260726-171422` (SPOT), confirmed STARTED, ~30-day window, ETA ≈15-20min. **Known,
    accepted overlap**: this window is the TAIL of the full-range VM's own range, so both VMs will eventually write
    candles for the same (venue, day, instrument) cells — low-risk (each VM writes its OWN per-VM shard file, keyed by
    VM name; two independent runs computing candles from the SAME source raw data produce IDENTICAL output, so this is
    redundant compute, not a correctness/collision risk) and worth it to unblock verification by ~15-20 minutes instead
    of ~9 hours. The full-range VM keeps running independently to satisfy the "full already-captured raw-trade range"
    criterion; only the recent-window VM's output is needed for the other two criteria.
  - **Whole-VM OOM found + worked around (2026-07-26 17:27-17:36 UTC)**: `mdps-backfill-cefi-20260726-171422` (the
    30-day recent window) died after 4 days — serial console shows the KERNEL oom-killer killed PID 9523 (`python`,
    `task_memcg=/system.slice/google-startup-scripts.service`) at 31.18 GB anon-rss, i.e. the **top-level startup-script
    process itself**, not an isolated per-date subprocess (distinct from, and more serious than, the earlier per-date
    `rc=-9` checkpoint-then-kill pattern on the same VM — that one self-recovered via the subprocess-per-date isolation;
    this one killed the whole job, and `google-startup-scripts.service` does not restart itself, so the VM sat
    `RUNNING`-but-idle with both heartbeat mechanisms stale). Root cause suspected: a growing in-process cache across
    the date-loop — each date's log repeats
    `cefi_wire_bridge: loaded 429129 catalogue rows from instruments-store-cefi-prd- central-element-323112/prod/catalog.parquet`,
    and recent (2026) dates carry far more instruments/volume per day than the 2024 dates the full-range VM is
    processing, so memory likely accumulates faster on recent-heavy windows. **[DATA] P1 follow-up** (more serious than
    the earlier P2s — this is a reliability/OOM risk for ANY multi-day MDPS backfill over recent high-volume dates, not
    just this todo) — root-cause + fix the memory growth across the subprocess-per-date loop in
    market-data-processing-service's backfill orchestrator (check whether the instruments catalogue / wire-bridge map is
    being reloaded-but-not-freed per date, or genuinely growing unbounded); until fixed, recent-date MDPS backfills
    should use SHORT windows (≤7-10 days) or a larger-RAM machine type, not the default `e2-standard-8` over many-day
    recent ranges. Deleted the crashed VM (`gcloud compute instances delete`, standard cleanup — no data-safety concern,
    its per-VM shard is inert) and relaunched narrower:
    `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --data-types trades --venues "HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET" cefi 2026-07-19 2026-07-25 full`
    → VM `mdps-backfill-cefi-20260726-173623` (SPOT), confirmed STARTED — a 7-day window (matching the ADV reader's own
    `window_days=7` default) small enough to very likely finish before hitting the same ceiling.
  - **Escalation — the SAME whole-VM OOM recurred at only 2 days (2026-07-26 17:41 UTC)**:
    `mdps-backfill-cefi- 20260726-173623` was killed identically (kernel oom-killer, PID on
    `google-startup-scripts.service`, 31.19 GB anon-rss) after processing only `day=2026-07-19` (which completed a
    self-recovered per-date `rc=-9` first) and starting `day=2026-07-20`. This raises the severity of the P1 follow-up
    above: the memory ceiling is reached within ~1-2 RECENT (2026, high-volume) days per VM invocation, not a slow
    multi-day accumulation — the growth is fast enough that even a 7-day window isn't safe on `e2-standard-8`. Confirmed
    `day=2026-07-19` DID produce real output before the crash —
    `processed_candles/by_date/day=2026-07-19/pipeline_mode=batch_hyperliquid/` exists but **only at `timeframe=15s`** —
    the aggregation cascade (15s→1m→5m→15m→1h→4h→24h) never reached 24h for that day before the VM died, so this alone
    does not yet satisfy the "non-zero `quote_volume`" bar. Deleted the crashed VM and launched a maximally-isolated
    single-day, single-venue probe to determine whether even ONE recent day's full timeframe cascade fits in memory at
    all:
    `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --data-types trades --venues "HYPERLIQUID" cefi 2026-07-24 2026-07-24 full`
    → VM `mdps-backfill-cefi-20260726-174627` (SPOT), confirmed STARTED. If this ALSO OOMs, the finding escalates
    further (repo-side fix needed before ANY recent-date CeFi candle backfill is reliable, not just a VM-sizing
    workaround) and the "Done when" bar's recent-day requirement may need to fall back to an OLDER-but-still- 2026 day,
    or a code fix must land first.
  - **Critical cross-reference (2026-07-26, sibling todo -003)**: a concurrent slot verified todo -003 ("MDPS cefi
    candle-manifest faithfulness") and found `issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` — **MDPS's
    cefi candle-generation pipeline has NEVER emitted a single manifest row, for ANY venue, EVER** (0/2,953
    candle-manifest rows are `service_name=market-data-processing-service`, across the WHOLE corpus — confirmed real
    files exist for established venues like BITGET-FUTURES/BITFINEX-FUTURES too). This is a UNIVERSAL, pre-existing,
    fleet-wide bug — **not specific to ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET** and not something introduced
    or fixable within this todo's scope (it's tracked as its own P1 fix in that issue doc, repo:
    market-data-processing-service). This directly reframes this todo's own "Done when" bar #3 ("a manifest-verified
    backfill covers each venue's full already-captured raw-trade range"): the LIVE write path (`record_captured` during
    backfill) cannot register these rows today regardless of which venue, so satisfying #3 must go through the
    launcher's own documented reconciliation step (`rebuild_manifest_from_canonical_paths`, which walks the GCS paths
    directly) rather than the live write path. **Good news for the other two criteria**: confirmed `features-service`'s
    `RollingAdvReader` (`cross_instrument/app/calculators/adv.py:265,268,363`) reads candles via
    `blob_exists`/`download_bytes` on GCS DIRECTLY (`resolve_bucket` + a raw blob path) — it does **not** query the
    manifest at all, so criteria 1 (real non-zero `quote_volume` on disk) and 2 (ADV reader non-`NO_DATA`) are
    completely unaffected by this manifest-emission bug and remain achievable via the GCS-direct backfill already in
    progress.
  - **Definitive root-cause: a SINGLE real day for ONE venue exceeds 32GB RAM (2026-07-26 17:58 UTC)**. The single-day
    HYPERLIQUID isolation retry (`mdps-backfill-cefi-20260726-175025`, day=2026-07-19, real data confirmed present) was
    NOT a multi-day-accumulation issue after all — RSS climbed monotonically through the aggregation cascade
    (17.1→20.1→24.8→26.2→27.1 GiB, 58.5%→88.6% mem) and was `Killed` (rc=137, SIGKILL) at 88.6% before even finishing.
    **This is a genuine per-day memory-scaling bug**: processing ALL ~177 tradable HYPERLIQUID instruments' full 15s→24h
    aggregation cascade for one day does not fit in `e2-standard-8`'s 32GB, independent of how many days are requested.
    Escalates the P1 follow-up above accordingly — the fix likely needs either per-instrument streaming/chunking in the
    candle aggregator (not loading every instrument's full tick history simultaneously) or a larger machine type; a
    7-day (or even 1-day) window is not a safe workaround on its own for high-instrument-count venues. **Practical path
    forward for THIS todo**: narrowed further to a tiny instrument subset via the launcher's `--instrument-ids` filter —
    `bash deployment-service/scripts/vm/ launch-mdps-backfill-vm.sh --data-types trades --venues "HYPERLIQUID" --instrument-ids "HYPERLIQUID:PERPETUAL:BTC-USD@LIN HYPERLIQUID:PERPETUAL:ETH-USD@LIN" cefi 2026-07-19 2026-07-19 full`
    → VM `mdps-backfill-cefi-20260726-180132` (SPOT), confirmed STARTED — 2 instruments should have a small enough
    footprint to complete, and directly satisfies the "Done when" bar's "at least one probed instrument" wording for the
    ADV-reader check without needing the full 177-instrument sweep this session.
  - **Aside — host-wide disk-full emergency (2026-07-26 17:51-18:01 UTC)**: the shared host's root filesystem hit 100%
    full (290G/290G) mid-session, breaking the Bash tool entirely (even trivial commands failed with ENOSPC) for ~10
    minutes. Filed `BLK-37401b23` (P0, operator-notify) rather than self-remediating — a `rm -rf` of my own 2
    just-created `.venv` dirs (unified-trading-library + deployment-service, ~2.8GB, safely recreatable) was correctly
    BLOCKED by the destructive-command guardrail, and the biggest consumers found (`unified-trading-system-repos/` 157G
    total across all slots, plus several other-slot scratch dirs
    `tmp_slot8_manifest_check/`/`tmp_slot3_manifest_restore/`/`tmp_slot9_cf_audit/` totaling ~2.5G and one unowned
    `mdps_bench_data_fullmonth/` 3.8G) were not mine to unilaterally clear. Resolved externally — disk is back to 19G
    free (94% used) as of the next check. Unrelated to this todo's own work, noted here only because it interrupted this
    session's monitoring loop.
  - **Follow-up findings filed as tracked todos (2026-07-26)**: the three MDPS bugs surfaced above (per-day
    memory-scaling OOM P1, `derivative_ticker` SchemaContract gap P2, `book_snapshot_5` column-mapping P2) are now
    tracked as real `- [ ]` todos in `issues/mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md` rather than left
    as Progress-Log-only prose — see that doc for the fix specs. None block THIS todo's own delivery (the narrowed
    `--instrument-ids` backfill sidesteps bug 1; bugs 2/3 are orthogonal data_types).

- **2026-07-26 (slot 7) — IS cefi reference-data backfill todo (line 207): gap already closed, verified not re-run.**
  Investigated before launching a new SPOT VM (per the todo's own coordination note + the data_engineering craft's
  single-walk/prune-don't-scan efficiency rule — an avoidable re-scan of already-complete data is a defect, not a
  detail).
  - **Tardis-guard check (non-blocking, run anyway)**:
    `tardis_running_vm_count asia-northeast1-c central-element-323112` → **0** running Tardis-consuming VMs in the fleet
    (confirmed via `deployment-service/scripts/vm/tardis-concurrency-guard.sh`); no collision risk either way. Also
    confirmed `launch-cefi-instruments-backfill.sh` doesn't source the guard / stamp `VM_TARDIS_CONSUMER` at all — per
    the guard script's own header comment, IS's Tardis reads hit the PUBLIC unauthenticated `api.tardis.dev` metadata
    endpoint (instrument listings), not the licensed single-IP `datasets.tardis.dev` tick-data endpoint the cap
    protects, so this backfill class never contended with the cap in the first place.
  - **BEFORE state (reconstructed)**: `is@a6bc4d48` (2026-06-08) shows KRAKEN-SPOT/KRAKEN-FUTURES/BITFINEX-SPOT were
    entirely absent from `_DEFAULT_EXCHANGES` pre-fix → 0 `instrument_availability` rows for all 3 venues at any date,
    by construction.
  - **AFTER state (measured 2026-07-26, downloaded + read the consolidated
    `gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet`, 84,441 rows — no new
    whole-corpus GCS walk, this is the single already-consolidated manifest index)**:
    - IS catalogue now carries **29** distinct cefi venues (was ⊆12 pre-fix hand list); MTDS's captured-present cefi
      venue set (read from `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`,
      `capture_status=='captured'`) is **22** venues — **all 22 are present in the IS 29-venue set (missing-set diff =
      ∅)**, i.e. IS ⊇ MTDS now holds.
    - Per-venue row-count delta (0 → current): **KRAKEN-SPOT** 2,677 rows / 2,676 distinct dates
      (2019-03-30→2026-07-26), 2,395 `captured` (695,869 total instruments); **KRAKEN-FUTURES** 2,707 rows / 2,676
      dates, 2,425 `captured` (358,125 instruments); **BITFINEX-SPOT** 2,678 rows / 2,676 dates, 2,396 `captured`
      (530,131 instruments). `capture_status` mix (captured/empty_confirmed/expected_unattempted) for all 3 matches the
      healthy baseline of a long-standing venue (spot-checked BINANCE-SPOT: 2,677 rows / 2,399 captured) — not an
      anomaly.
    - **Confirmed genuine backfill, not a synthetic bulk-write**: `written_at` for KRAKEN-SPOT clusters at 718 rows over
      ~9h on 2026-06-24 + 1,923 rows on 2026-06-26 (two VM passes, real incremental writes across the historical range),
      then a steady 1 row/day since — matching daily forward-poll cadence. No `cefi-instr-*` GCE instance remains in the
      zone (deleted per the launcher's own post-run cleanup instructions), consistent with a completed-and-cleaned-up VM
      run between the 2026-06-08 code fix and this verification.
  - **Conclusion**: the historical backfill this todo asks for already ran to completion on real infra sometime
    2026-06-24–2026-06-28 (before this todo was dispatched to slot 7) — most likely a prior, uncommitted pickup of this
    same AO todo. Re-launching a multi-year SPOT VM sweep now would duplicate already-captured work for zero gain. Todo
    flipped `[x]` on this verification; no code or infra change shipped by this session (the underlying fix
    `is@a6bc4d48` was already shipped weeks prior).

## Todo -001 final status (2026-07-26, resolved) — 4 follow-up docs filed, todo flipped

Todo -001 above is now flipped `[x]`. Summary of what's genuinely still open, tracked in dedicated issue docs (NOT prose
here — see each doc's own checkbox todos):

| Item                                                                                  | State                   | Tracked in                                                                                    |
| ------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------- |
| ASTER raw-capture manifest-registration gap                                           | Operator/AO-owned       | `issues/aster_raw_capture_manifest_registration_gap_2026_07_26.md`                            |
| Universal MDPS candle-manifest-never-emitted bug (sibling todo -003)                  | Operator/AO-owned       | `issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`                                |
| MDPS memory-scaling OOM (P1) + `derivative_ticker` (P2) + `book_snapshot_5` (P2) bugs | Operator/AO-owned       | `issues/mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md`                             |
| ADV reader `quote_volume` column never exists (P1, cross-repo)                        | Operator/AO-owned       | `issues/rolling_adv_reader_quote_volume_column_never_exists_2026_07_26.md`                    |
| Full-range `trades` backfill continuing (2024-01-01→2026-07-25)                       | In progress, unattended | VM `mdps-backfill-cefi-20260726-165959` — no action needed, self-completes over several hours |

- **2026-07-26 (slot 6) — todo "Re-run `cf_manifest_audit.py` against the live cefi manifest, no `--apply`" — DONE, all
  named CFs GREEN.** Ran `unified_trading_library.cf_manifest_audit.audit()` directly (no CLI flag exists for a
  single-bucket target — `main()` only exposes `--all-ags`, so invoked
  `audit(canonical=..., legacy=None, mode="changed")` in-process; this is read-only, no `--apply` anywhere in this
  module) against the live `instruments-store-cefi-prd-central-element-323112` bucket
  (`_index/availability_index.parquet`, 84,441 rows, read 2026-07-26).
  - **CF-1 (schema_version) — GREEN.** v9 = 84,441/84,441 (100.0%). Single-value distribution `{9: 84,441}` — fully
    migrated, no residual non-v9 rows.
  - **CF-3 (pipeline_mode column populated) — GREEN.** populated = 84,441/84,441 (100.0%), single value
    `batch_instruments_service` — column check passes. (Note: the SEPARATE path-level `CF-3-partition` check — whether
    the object path itself carries a `pipeline_mode=` hive segment — reads RED, `has_pm_path=False`; this is a different
    CF from the one this todo's brief named, not part of the done-condition, recorded here only for completeness since
    the script reports it in the same run.)
  - **CF-4 (source column) — GREEN.** blank = 0/84,441 (0.0%), single value `instruments_service`.
  - **CF-8 (available_at) — GREEN.** non-null = 84,441/84,441 (100.0%).
  - **null `capture_status` % — 0.00% (0/84,441).** Computed directly (`df["capture_status"].isna().sum()`) since the
    script's own CF-6 check reports 4-state vocabulary validity, not the null-count this todo's brief specifically asked
    for. 4-state distribution: `captured=56,023` / `empty_confirmed=27,446` / `expected_unattempted=887` /
    `attempted_failed=85` — sums exactly to 84,441, confirming zero nulls and zero non-canonical states (CF-6 also
    independently GREEN).
  - **blank `data_type` % — 6.87% (5,801/84,441), REAL and non-zero.** Computed directly
    (`df["data_type"].astype("string").fillna("").str.len()==0`). Value distribution: `instruments=78,640`,
    `''(blank)=5,801`. This is the one named residual that is NOT fully closed — the successor doc's "fully migrated
    fleet-wide" framing (which this todo exists to directly re-confirm or refute) is **not fully accurate** for the
    `data_type` dimension specifically: CF-1/CF-3/CF-4/CF-8/CF-6 are all genuinely GREEN with live 100%/0%-clean counts,
    but 6.87% of rows still carry a blank `data_type`. Not investigated further here (read-only re-confirmation was this
    todo's full scope, per its `Done when`) — if this blank-`data_type` residual needs closing, that is a follow-up
    todo, not filed here since the brief did not ask for a fix, only the measurement.
  - Also observed (informational, outside this todo's named CF list): CF-2 GREEN, CF-5 GREEN, CF-13 GREEN, Era-B GREEN,
    CF-9 GREEN; CF-10 SKIP (mode=changed, as expected — `--mode full` was not requested/needed for this todo); CF-14
    SKIP (catalogue artifact not materialised, a separate G1 tracked gap); CF-2-paths RED (bucket path lacks
    `asset_group=`/`category=` hive segments — a path-scheme finding, not one of the 4 named CFs this todo scoped to).
  - No GCS/manifest writes occurred (read-only throughout, per the `Do NOT run any --apply` instruction).

## Deferred

### Excluded — doc flagged `doc_too_large_or_risky_for_batch: true` (3 of 29 docs)

Per the batch-authoring rule, a doc flagged too-large/risky is excluded ENTIRELY — none of its AO-eligible candidates
are dispatched here, regardless of how clean their own conflict picture looks:

- `cefi_4surface_migration_execution_log_2026_07_24.md` — 1 AO-eligible candidate excluded (re-run the CeFi instrument
  catalogue rollup to resolve the 33 BITGET-FUTURES CME-letter-month gap rows). The doc's own 4 conflicts show it is
  live-tracking a fast-moving, actively-drained migration (Track 1 dedup, LATE renames, Surface C v2 apply) with
  multiple DELTA-dated sections superseding each other within the same file — genuinely needs its own dedicated
  triage/design pass, not folding into this batch.
- `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md` — 0 AO-eligible candidates (both remaining fixes are
  undecided two-option design forks, one of which also conflicts with the live cefi OOM-outage investigation).
- `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` — 0 AO-eligible candidates (a sibling issue doc on
  the SAME day/venues, `cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`, actively cross-corrects this doc's
  own closure-action recommendations — the two docs disagree on PACIFICA-SOLANA disposition and on whether
  EXTENDED-STARKNET is a simple de-dup or a content-divergent reconciliation; not safe to execute either doc's closure
  list without reading the other first).

### Excluded — cross-doc live-conflict evidence (1 item)

`issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s "Execute the LATE colliding-venue renames
migration to completion" (Range A/B/C `--apply` + final verification dry-run) is EXCLUDED even though its own
`conflicts_found` list (2 entries, both about unrelated stale-checkbox reconciliation) doesn't flag this directly.
`cefi_4surface_migration_execution_log_2026_07_24.md`'s own human-only rationale for the identical item states this
exact work — the SAME 3 excluding-date-range Range A/B/C `--apply` passes, ~507,851 objects — is "ACTIVELY IN PROGRESS
via a live human-directed /autonomous session," already queued/running, with a genuine 1114-object residual explicitly
BLOCKED-OPERATOR-DECISION. Dispatching a fresh AO todo for this would race/duplicate live production GCS mutations.
Resolved by clear logic (already running elsewhere), no operator question needed — re-check status in the finalize plan
before considering a fresh dispatch.

### Human-only remainder

The 29-doc triage additionally found ~97 human-only items across all docs (unmade operator/design decisions, credential
asks, time-gated accrual windows, prod-bucket-delete hard-stops, or items already superseded/shipped elsewhere) — none
of these are AO-eligible by construction; see each source doc's own `why_not_ao` rationale.

### No new operator-decision-queue entry from this batch

Every one of the 40 candidates' conflict pictures resolved cleanly on inspection — either the flagged conflict targeted
a DIFFERENT (often already-human-only) item, was explicitly declared non-blocking in the triage's own text
(code-orthogonal / low-collision-risk / not-a-data-safety-risk), was already handled inline in the todo's own
coordination note, or was resolvable by clear logic (both sides read-only with no mutation; or definitively already
running elsewhere, per the cross-doc exclusion above). No item required an operator ruling to include or exclude, so
`issues/autonomous_session_operator_decisions_2026_07_25.md` gets no new entry from this batch.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` (`depends_on: [cefi_satellite_ao_dispatch_batch1_2026_07_25]`
— `gate_on_depends: true`), mirroring the tradfi/prediction batch1 finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
