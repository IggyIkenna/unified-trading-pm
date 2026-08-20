---
doc_type: plan
title: CeFi consolidated close-out — track + close every remaining cefi workstream once and for all
summary:
  Single coordination plan that references (does NOT duplicate) every still-open cefi plan/issue so they can be closed
  off together. Authored 2026-07-18 from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification;
  restructured 2026-07-25 into a lean coordination index over 4 new forked children (migration-cutover critical path,
  coverage-backfill checkpoints, candle-namespace residual, misc-audits) plus the pre-existing execution-log,
  aggregated-sources, satellite-batch, and native-extraction docs. VERDICT — for the INSTRUMENT-ID CANONICALIZATION axis
  (GCS filename / parquet column / manifest key / reader), the migration is Phase-C dry-run-clean, awaiting only the
  operator-approved cutover (now the sequential critical path in
  /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md). CeFi is NOT "done" overall — a
  REOPENED coverage question (the archived "honest-done 50.79%" rested on a code-bug-induced throughput collapse
  mistaken for a 1.8-year physical ceiling, now fillable in ~1-2 days) and an operator-ruled "done first" side-quest
  (cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md's Phases 1/1b/1c/2/5) both remain open.
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [cefi, close-out, consolidation, canonicalisation, manifest, coverage, backfill, denominator, adapter-retrofit]
related:
  [
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
  ]
created: 2026-07-18
last_updated: "2026-07-25" # 2026-07-25: 4-child split (migration-cutover, coverage-backfill, candle-namespace, misc-hygiene) + Track 0 cryptovenue-phases embed (cefi.1) + 11 AO-readiness fixes; was 2026-07-24
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 8.0
estimate_calibrated_ai_days: 6.4
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    cefi_4surface_migration_execution_log_2026_07_24,
    cefi_migration_cutover_and_track8_completion_2026_07_25,
    cefi_track2_coverage_backfill_checkpoints_2026_07_25,
    cefi_track7_candle_namespace_residual_2026_07_25,
    cefi_misc_audits_and_hygiene_2026_07_25,
  ]
source:
  3-agent cefi plan/issue audit + direct verification (slot-3, 2026-07-18) at operator request ("consolidate all
  remaining cefi issues/plans into one plan referencing the others so we can close them off once and for all");
  restructured 2026-07-25 into a 4-child split (read-only design pass + operator-resolved ambiguities cefi.1-4).
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py,
  ]
---

# CeFi consolidated close-out

> **Purpose.** One place to see + close ALL remaining cefi work. This plan **references** the source docs; it does not
> duplicate their content. Close a track by closing its source doc(s), then tick it here. Authored from a 3-agent audit
> (2026-07-18) of every active cefi/IS/MTDS plan+issue; restructured 2026-07-25 into a lean coordination index — see
> "Reachability map" below for where each piece of real work now lives.

## Headline verdict — "is the migration final?"

- **Instrument-ID canonicalization (4 surfaces: GCS filename / parquet `instrument_id` column / manifest key / reader):
  YES, this is the FINAL migration for that axis.** The 4-script program is Phase-C dry-run-clean; the operator-gated
  drain+apply is now the sequential critical path in
  `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`. Everything id-format-related is
  subsumed, absorbed, or already done — see that child plan for the full predecessor-subsumption record.
- **CeFi OVERALL: NOT done.** Several separate open tracks remain — none blocks the id-migration; several are real
  data-correctness work; Track 2 (coverage) is a decision that reframes "cefi done."

## Reachability map — how a reader gets to every piece of real work from here

1. **Migration-completion critical path** →
   `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (`sequential: true`, 5 todos:
   DERIBIT quote fix → on-disk `:PERP:` rename → cutover `--apply` → post-cutover flip → terminal enumeration
   checkpoint) → its gated finalize.
2. **Coverage-backfill path** → `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` (gated on path 1 finishing) →
   its gated finalize.
3. **Candle-namespace path** → `cefi_track7_candle_namespace_residual_2026_07_25.md` (gated on
   `cefi_consolidated_native_ao_extract_2026_07_25.md`'s verify+backfill todo finishing) → its gated finalize.
4. **Misc-audit path** → `cefi_misc_audits_and_hygiene_2026_07_25.md` (ungated, 3 independent todos) → its gated
   finalize.
5. **Native-todo AO extraction** (a PARALLEL, independently-drafted triage of this parent's OWN 32 native todos,
   distinct from paths 1-4 above — 12 AO-eligible candidates) → `cefi_consolidated_native_ao_extract_2026_07_25.md` →
   its gated finalize.
6. **Satellite-doc AO batch** (every OTHER cefi plan/issue's AO-eligible work, 33 todos) →
   `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` → its gated finalize.
7. **Full execution history** (day-by-day Progress Log, DELTA checkpoints) →
   `cefi_4surface_migration_execution_log_2026_07_24.md` (LOCAL, historical record — see Progress Log below).
8. **Discoverability index** (every other cefi-relevant plan/issue's open-todo digest) →
   `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`.

## Track 0 — CeFi equity perps/tokenized stocks: finish Phases 1/1b/1c/2/5 (operator ruling 2026-07-25, "done first") · P0/P1

> **Source**: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — the operator ruled (2026-07-25) that this
> doc's Phase 1 (incl. 1b, 1c), Phase 2, and Phase 5 should finish and be embedded HERE as high-priority work, sequenced
> ahead of/alongside the migration-critical-path work (path 1 in the Reachability map above), NOT buried in
> misc-hygiene. Phase 1 itself is 100% done (its 1 todo already checked in the source doc). The 11 todos below are
> everything still unchecked in Phases 1b/1c/2/5 as of 2026-07-25 — read the source doc for full context (per-venue
> live-listing counts, probed Yahoo/Databento limits) before touching any of these.

- [x] ✅ [SCRIPT] P0. **DONE 2026-08-09** (dispatched via `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1).
      Propagation ops B1/B3/B4 — IS→catalogue→enumerator→MTDS wave chain for the new Binance tradfi-perp cash-twin
      equities. Source: Phase 1b. Verified live against prod GCS state (the 2026-06-24-launched
      `instr-backfill-tradfi-20260623` backfill + nightly schedulers already propagated the chain over the past ~6 weeks
      — no new run needed): catalogue has 103 mvp-tagged equity/ETF base_assets incl. every sampled new ticker; manifest
      shows `expected_unattempted` for every sampled ticker; `NASDAQ:EQUITY:HOOD-USD` 2026-07-20 `ohlcv_15m` sample = 49
      rows, 0 NaN OHLCV. Full evidence: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Progress Log,
      2026-08-09 entry.
- [x] ✅ [DATA] P2. ~~**BLOCKED-DATA — source a Korea-equity vendor** for HYUNDAI/SAMSUNG/SK-Hynix cash-twin coverage
      (no US-listed twin on Databento DBEQ.BASIC; neither current vendor covers KRX). Repo: instruments-service (vendor
      ask → operator). Source: Phase 1b.~~ **CLOSED — na-eligibility-audit 2026-08-09.** Embedded mirror of the
      identical item closed 2026-08-08 citing a 2026-08-07 operator ruling documented in
      `/plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` (line 662): "daily from yahoo finance
      is enough" — `unified-api-contracts@844c5ee6b` + `instruments-service@1ba5da4b`. This embedded copy was never
      flipped to match; fixed now.
- [x] ✅ [SCRIPT] P1. **CLOSED — already-satisfied (2026-08-15).** Capture Binance/OKX/Bybit
      `indexPrice`/`markPrice`/`fundingRate` for the equity-perps as a first-class data_type (rides the existing
      premiumIndex/funding endpoints). The existing `derivative_ticker` data_type (already first-class, already in
      `EXPECTED_COVERAGE` for all 3 venues) already fully populates these fields via already-wired live WS connectors,
      generically across each venue's whole instrument universe (no symbol-type filter excludes the equity-perps) —
      building a standalone data_type would duplicate storage for an identical-source signal, the same anti-pattern
      `perp_funding_handler.py`'s ASTER/LIGHTER-ZKSYNC precedent documents avoiding. Full evidence + file:line
      citations:
      `/plans/archive/issues/cefi_equity_perp_mark_index_funding_derivative_ticker_already_covers_2026_08_15.md`
      (unified-trading-pm@229e86f53b). Repo: market-tick-data-service. Source: Phase 1b.
- [x] ✅ [SCRIPT] P2. **Wire a recurring daily funding/basis scan** across all crypto-venue equity-perps (annualized
      funding + perp-vs-index basis + market-hours-vs-off-hours flag) → opportunity-sizing report. Repo: e2e-testing.
      Source: Phase 1b. — **SHIPPED e2e-testing@d1fe3dc6aa** (`scripts/cefi/equity_perp_funding_basis_scan.py` + a daily
      cron wrapper, 15 new unit tests, QG green); found + reconciled 2026-08-15 by a /plan-reconcile hunter pass — the
      identical item was already shipped and tracked under `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s own
      Track-0 mirror entry citing the same commit, but this doc's own checkbox was never flipped to match.
- [x] ✅ [DESIGN] P2. **strategy-service — decide the single-stock basis execution-venue/hedge approach** (IBKR /
      tokenized / cross-crypto-venue dispersion; off-hours = no-cash-hedge). Repo: strategy-service. Source: Phase 1b.
      **RESOLVED + APPROVED (operator, 2026-08-08)**: hedge=IBKR cash-stock borrow for all singles (decided same-day
      2026-06-20 in the source doc's Phase 1d NET-basis backtest; operator's "Approve, build it" ruling confirms it).
      Mirrors the source doc's own Phase 1b checkbox flip
      (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`, 2026-08-08 Progress Log entry). Open work is now
      the IBKR adapter BUILD itself (that doc's Phase 1e P0 todo, `[BACKEND]`, not embedded in this Track 0's 11-todo
      list — out of this track's Phase 1/1b/1c/2/5 scope).
- [x] ✅ [UAC] P0. **DONE 2026-08-09 — `unified-api-contracts@e973c62d`** (dispatched via
      `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2). Map the index perps SPXUSDT/NAS100/SPYUSDT/XAUUSDT to
      CME index-future + Databento index canonical, carrying scale/multiplier. Source: Phase 1c. New
      `canonical/crosscutting/index_commodity_perp_hedge_link.py` (`INDEX_COMMODITY_PERP_HEDGE_LINK` +
      `hedge_link_for()`), 12 new unit tests, `quality-gates.sh` green. **2 of the 4 requested symbols were stale,
      corrected with live evidence**: `SPXUSDT` is now the `SPX6900` meme coin (no longer S&P 500-tracking); no
      `NAS100`/`NAS100USDT` symbol exists on Binance. Shipped: `SPY→ES`, `QQQ→NQ` (substitute for the nonexistent
      NAS100), `XAU→GC`; `SPX`/`NAS100` recorded in `EXCLUDED_INDEX_COMMODITY_PERP_BASES` with evidenced reasons rather
      than silently dropped.
- [ ] [DESIGN] P1. **strategy-service — design the INDEX-perp cash-and-carry archetype** (short Binance SPX/NAS perp +
      long CME ES/NQ real hedge, scale-adjusted) — the FIRST fully-executable equity-perp basis archetype (deep real
      hedge, both legs already in universe+data, CME Globex ~23h/day). Repo: strategy-service. Source: Phase 1c.
- [ ] [SCRIPT] P1. **Launch the CeFi Tardis backfill for the equity-perp window** (sub-item 4 of Phase 2, explicitly out
      of scope until now — the un-filter + type-stamping code landed 2026-07-18, this is the actual backfill). Verify
      manifest `capture_status` for an EQUITY_PERP-tagged shard. Repos: instruments-service, deployment-service. Source:
      Phase 2.
- [x] ✅ [SCRIPT] P1. **NARROWED + DONE 2026-08-09** (dispatched via `cefi_satellite_ao_dispatch_batch11_2026_08_09.md`
      todo 3). Backfill the 3 KRX stocks via guardrailed Yahoo. Source: Phase 5. The 1h/15m/1m legs conflict with a
      RESOLVED, still-live 2026-07-12 operator decision this todo's source predates (Yahoo doesn't reliably serve
      intraday granularity over long historical windows — `unified-api-contracts@a2751f36` narrowed the KRX registry
      entry to `["ohlcv_24h"]` only). The achievable 1d/`ohlcv_24h` leg verified ~98% complete since 2019-01-02 across
      all 3 symbols (2943/~2997 canonical-instrument-id shards captured), spot-checked against a real GCS parquet
      object. 2 adjacent manifest-integrity defects found + filed as follow-up todos. Full evidence:
      `/plans/archive/issues/krx_batch11_todo3_intraday_conflicts_with_2026_07_12_ruling_2026_08_09.md` (archived
      2026-08-10).
- [x] ✅ [UAC] P1. **DONE 2026-08-09 — `unified-api-contracts@92a418e5`** (dispatched via
      `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 4). Measure the exact Databento L-floor boundary per level
      live + update the 3 named constants/functions. Source: Phase 5. Binary-searched `metadata.get_cost` live on
      GLBX.MDP3/ES.c.0: L1 (trades) 367d free/368d metered (was conservative 365d), L2/L3 (mbp-10/mbo) 33d free/34d
      metered (was conservative 30d) — L1 boundary cross-checked identical on DBEQ.BASIC/AAPL. L0 has no rolling metered
      boundary at all (probed 5850-5908d back, all $0.0000, then a hard 422 at 5909d+ — `_FULL_HISTORY_DAYS` updated
      from the arbitrary `16*365` to the measured 5908d). `LEVEL_MAX_LOOKBACK_DAYS` + docstrings + boundary-assertion
      tests updated to match. `quality-gates.sh` green (336s).
- [x] ✅ [REFACTOR] P2. **DONE 2026-08-09 — `unified-api-contracts@fc1b4897`, `market-tick-data-service@aea655a9`**
      (dispatched via `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 5). Deprecate + remove all Barchart code,
      no shim. Source: Phase 5. Deleted `BARCHART_OHLCV_15M_SCHEMA` + registry entries + the `barchart:` registry blocks
      in both `provider_api_versions.yaml` copies + the stale comment in `registry/endpoints.py`
      (unified-api-contracts); deleted the dead `TestBarchartOhlcv` test, renamed `test_barchart_and_yahoo_adapters.py`
      → `test_yahoo_adapter.py`, dropped the dead `smoke_matrix.py` entry (market-tick-data-service). Deliberately kept
      the live `TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` frozenset (protects 9,119 real legacy manifest rows) and the
      historical-manifest-compat parsing code — both are live data-compat, not retired fetch-adapter code. Both repos
      `quality-gates.sh` green, shipped via `quickmerge --agent`, post-push ancestry verified on `live-defi-rollout`.

**Close-out criterion**: all 11 todos above closed or explicitly re-deferred by the operator; the source doc's own
Phases 1/1b/1c/2/5 sections show 0 remaining open todos.

## Track 1 — Instrument-ID canonicalization (THE final id migration) · FORKED

> **Forked 2026-07-25** to `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`
> (sequential 5-todo critical path — path 1 in the Reachability map above). This section stays as a compact pointer +
> the historical subsumption record.

- **Vehicle**: `plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (+ blueprint
  `/plans/archive/2026_07/issues/cefi_canonical_blueprint_2026_07_17.md`). Phase A (code on `main`) ✅ · Phase B (deploy) ✅ · Phase C (4 scripts
  dry-run-clean) ✅ · **Phase D/E (drain + `--apply`) — DONE, see checkbox below.**
- [ ] [PM] P0. **Execute the minutes-gap hybrid cutover (Phase D/E: drain + `--apply` for Scripts 1-4)** — Scripts 2
      (filename rename), 3 (manifest dedup v2), 4 (eu-twin drop) DONE 2026-07-27. Script 1 (parquet CONTENT backfill —
      true corpus scope measured at ~4.5M files, executed as an iteratively-resharded 42+-VM fan-out) was reported here
      as finished with every shard `EXIT_STATUS=0` on 2026-07-27, but the SAME-DAY
      `cefi_consolidated_native_ao_extract_2026_07_25.md:332-335` records Script 1 as "still in progress" at ~2 orders
      of magnitude larger than originally planned, corroborated by
      `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` showing 17/44 shards still incomplete on 2026-07-31.
      **RE-OPENED 2026-08-02 (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 1d, option
      A): the fleet docs are the measured ground truth — this closeout doc is a roll-up and follows the fleet, not the
      reverse. Un-checked pending Script 1's fleet docs themselves reporting all shards complete.** The operator's
      `ADAF0:USTF0.parquet` equivalent (`BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`) confirmed canonical on GCS filename /
      parquet `instrument_id` column / manifest key — that spot-check remains valid, it does not establish corpus-wide
      completion. Full evidence (drain/consolidate/snapshot, per-script dry-run+apply logs, the full VM campaign):
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 3, archived).
- **Close-out criterion**: the operator's `ADAF0:USTF0.parquet` is canonical on all four surfaces, verified live (MET,
  above); each script's `--dry-run` re-run asserts 0 further changes (idempotency — MET, above).
- **Subsumes / closes on cutover**: `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`
  (relabel + purge `--apply`), `instrument_id_format_canonicalization_2026_07_08.md` (id-format traces),
  `instruments_remaining_work_audit_2026_07_10.md` (BYBIT-SPOT anomaly).
- **Residual adapter-retrofit carve-out → Track 5** (the 4 scripts are one-time DATA migrations; they do NOT retrofit
  the adapters, so re-drift prevention is separate).

## Track 1b — 🟢 RESOLVED 2026-07-25: CeFi raw-tick capture outage (was HALTED 2026-07-21..24, OOM crash-loop)

- [x] ✅ [INFRA] P0. **The batch-download Cloud Run Job was crash-looping on SIGKILL/OOM within 10-40s of every
      execution since ≥2026-07-23** — 3 days of zero manifest writes. Fixed by bumping memory 8Gi→16Gi + a verification
      run (full 10m2s success, measured `peak_rss=8646.5MB`). Capture flowing again as of 2026-07-25T01:44Z. Root-cause
      attribution + a permanent bound remain open follow-ups (not blockers) — full detail:
      `/plans/archive/issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`.

## Track 2 — CeFi backfill COVERAGE reopened · FORKED to its own gated plan · P0

> **Forked 2026-07-25** to `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` (gated on Track 1's cutover
> finishing — path 2 in the Reachability map above). This section stays as the decision record + pointer.

- **Source**: `issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md` (root-cause `status: resolved`) +
  `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (archived "honest-done, 50.79% accepted").
- **The finding (verified 2026-07-18)**: the archival's basis — "the 2.89M-cell gap is not closable at the N=1 Tardis
  ceiling ≈ 1.8 years" — is FALSE. It was a **~350x code-bug throughput collapse** (`run_in_executor(None,…)`
  default-pool + a date-serial barrier), not a physical ceiling; the gap is **~1-2 days of work at June rates**. **THE
  THROUGHPUT BUG IS NOW FIXED + MEASURED LIVE** (~14 MB/s on the VM). The doc also flags that "operator accepted 50.79%"
  may have been INFERRED from the erroneous ceiling verdict, not actually given.
  **STALE (ag-closeout-audit, cefi tranche, 2026-08-19): the date-serial barrier this paragraph calls "fixed" was
  never actually shipped — live-measured 2026-08-16 on the running BINANCE-FUTURES resume VM at only ~4 MB/s
  (download-leg 4.01 MB/s / upload-leg 3.22 MB/s), not ~14 MB/s. Root cause + corrected estimate:
  `issues/cefi_tardis_date_serial_barrier_still_open_2026_08_16.md`; fix design:
  `cefi_tardis_date_concurrency_2026_08_16.md`.**
- [x] ✅ [REVIEW] P0. **RULING (autonomous, within documented intent — /autonomous, 2026-07-18)**: **RE-OPEN the CeFi
      Completion Program + REVERSE the 50.79% acceptance.** Basis (all operator-stated): the archival's premise is a
      verified-false ~350x code-bug, now fixed + measured live; the "accept 50.79%" was inferred, not actually given.
      Coverage % is the climbing metric. The operator can reverse this ruling; surfaced in the session report.
- **Close-out criterion**: operator ruling recorded (done, above — source:
  `plans/archive/2026_07/cefi_completion_program_2026_07_15.md`, the archived "honest-done, 50.79% accepted" doc this
  ruling reverses); coverage re-measured post-resume-backfill (tracked in the forked child plan).

### Checkpoint cadence

Per `task_template.md` §3 finding K, this plan needs 3 distinct DATED run checkpoints per skill. ✅ **DONE 2026-07-28**
— the 2 PRE-BACKFILL baselines (candidates 3/4 of `cefi_consolidated_native_ao_extract_2026_07_25.md`) shipped:
**candidate 3** (`/data-pipeline-check-is` cefi): report promoted to
`plans/audit/results/data_pipeline_e2e_check_is_2026_03_15.md` (+ `.json`), run date 2026-03-15 (26/21/1/4 totals).
**candidate 4** (`/data-pipeline-check-mtds` cefi): reused existing same-day report
`plans/audit/results/data_pipeline_e2e_check_mtds_2026_03_15.md` (`unified-trading-pm@95074df6e`). The MID/POST
checkpoints (timing-coupled to the backfill) are in the forked
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`.

**Reconciled 2026-07-30** (finalize-001, slot 10) — 3 of 5 sub-checkpoints have genuine, verified evidence; the
POST-BACKFILL pair does NOT (the backfill VM was preempted mid-run, see below) and stays unflipped:

- [x] ✅ [DATA] P1. **Resume the coverage backfill** — DONE 2026-07-27 (slot-6). Launched
      `cefi-queue-heavy-binancefutu-x17-20260727-210013` (SPOT, N=1 Tardis cap satisfied), confirmed RUNNING with
      progress climbing over 2+ checks. Full evidence: `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` todo 1.
- [x] ✅ [DATA] P1. **MID-BACKFILL `/data-pipeline-check-is` checkpoint** — DONE 2026-07-28 (slot-6). Report:
      `instruments-service/pipeline_e2e_check_reports/data_pipeline_e2e_check_is_2026_03_15.md` (run date 2026-03-15;
      live-leg `total=26 passed=21 failed=1 ambiguous=0 skipped=4`, 1 genuine gap filed as
      `issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`). Full evidence: gating plan todo 2.
- [x] ✅ [DATA] P1. **MID-BACKFILL `/data-pipeline-check-mtds` checkpoint** — DONE 2026-07-28 (slot-6). Report:
      `plans/audit/results/data_pipeline_e2e_check_mtds_2026_03_15.md` (run date 2026-03-15; root-caused failures to a
      launcher guard scoping bug, filed as
      `issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`, not a data-correctness
      regression). Full evidence: gating plan todo 3.
- [ ] [DATA] P1. **POST-BACKFILL `/data-pipeline-check-is` final gate** — **NOT DONE.** The backfill VM was **preempted
      2026-07-28T10:51 UTC** at only ~2.3% of the target span (`compute.instances.preempted`, confirmed via
      `gcloud compute operations list`); no relaunch has occurred since. Running this gate against a 2.3%-complete, dead
      backfill would misrepresent it as finished — declined per the data-pipeline-correctness HARD RULE. See
      `issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` for the relaunch todo.
- [ ] [DATA] P1. **POST-BACKFILL `/data-pipeline-check-mtds` final gate + new coverage %** — **NOT DONE**, same blocker
      as above. **No new coverage % supersedes the archived 50.79%** — that measurement is gated on this checkpoint
      genuinely running post-completion. (The 2026-07-27 pre-launch baseline, 44.96%, is NOT the post-backfill number
      and should not be cited as one.)

## Track 3 — Manifest completeness axis (SEPARATE from id-format) · P1

- **Source**: `data_completion_cefi_2026_07_15.md` — a DIFFERENT canonicalization axis: manifest `pipeline_mode`
  partition + legacy-bucket orphan-sweep + cefi `_index` v8→v9 schema. ~15 open items (E4 orphan sweep, E7/E8
  verify+delete, candle-coverage gaps, denominator seed, v8→v9 CF-audit). NOT subsumed by Track 1.
- **Close-out criterion**: its own todos closed; do NOT fold into Track 1 (parallel track).

## Track 4 — Denominator / catalogue-completeness correctness · P1

- **Sources**: `instruments_service_plan_reconciliation_2026_06_29.md` (C1/C2 ASTER denominator over-seed + connector,
  C5 Deribit-options false-"complete"); `instruments_completion_tracker_2026_07_06.md` (D2);
  `instruments_foundation_completeness_2026_06_24.md` (G4/G5 not fully closed);
  `issues/cefi_layer1_denominator_gaps_2026_07_03.md` (being archived via `cefi_misc_audits_and_hygiene_2026_07_25.md`).
  Denominator-honesty, separate from id format.
- **Also here (P0 data-correctness bugs found in the audit, filed in their own docs):**
  - `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` — **⚠️ its "structurally-absent channel" premise is
    DEBUNKED**: the futures_chain 122,585 `attempted_failed` are NOT source-absence — the failure + aggregation are ON
    OUR SIDE (per-symbol capture gap → bundle never built). Not a writer-gate fix; it FILLS on the Track-2 coverage
    backfill. Do not propagate the debunked premise; do not treat this as an open Track-4 fix.
  - `/plans/archive/2026_08/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md` — **ARCHIVED
    2026-08-16** — gated Tardis requests on the vendor catalog; stopped recording impossible combos as
    `attempted_failed` (denominator-corruption, P0). All 6 todos shipped + verified.
- **Close-out criterion**: the impossible-combo bug fixed; denominator gaps resolved or accepted.

## Track 5 — Adapter canonical-ID-builder retrofit (RE-DRIFT prevention, post-migration) · P2

- **Sources**: `issues/instruments_docs_audit_outstanding_items_2026_07_08.md` (B1 — only ~4/63 adapters route through
  the shared canonical-id builder); `canonical_id_builder_retrofit_checklist_2026_07_08.md` (FI*/FF* Kraken-Futures
  13-instrument collision, unresolved).
- **Why separate**: Track 1's scripts are one-time DATA migrations; they do NOT change the ~59/63 adapters that stamp
  ids ad hoc, so new writes can re-drift unless retrofitted. This is the durability half of "canonical everywhere."
- **Close-out criterion**: adapters route through the shared builder (or a QG gate enforces canonical-id shape on
  write). ✅ **DONE 2026-08-04** — all 3 `*_native.py` files confirmed dead (zero production references), deleted
  (`execution-service@93402a06`); QG baseline updated (`unified-trading-pm@f9523e16f`). Adjacent finding
  (bitfinex/bitget native unreachable) filed as
  `/plans/archive/2026_08/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md`. Full evidence:
  `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 1 Progress Log.

## Track 6 — Independent cefi data-correctness / hygiene items · P2

Real but non-blocking, each in its own doc; listed for completeness so nothing is orphaned:

- `issues/aster_mtds_failure_count_regression_2026_07_07.md` — ASTER `attempted_failed` 3,491→17,675, untouched 11 days
  (NOTIFY-OPERATOR class, unresolved).
- `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` — 273 rows `venue=DERIBIT/type=COMBO` mislabel (should
  be `DERIBIT-COMBO`); post-migration check.
- `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — MTDS `_L5_VENUES` hardcoded, missing 11 cefi
  venues → read from `VENUE_DATA_TYPE_CAPABILITIES`.
- `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` — `DATA_TYPE_CAPABILITY_REGISTRY` missing entries; consolidator
  incremental no-op root cause never fixed (worked around); Tardis HTTP-400 from IS-catalog missing `available_to`.
- `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md` — reader-surface test
  (`test_canonical_parquet_reader_integration.py`) sat in the ungated `tests/integration/**` (`RUN_INTEGRATION=false`).
  **Resolved and archived 2026-07-31**: that doc's own todo 4 folded this file (credential-free, 74/74 passing) directly
  into `PYTEST_UNIT_DIR` — the D3 reader-bridge half of Track 1 now HAS CI enforcement.
- `issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md` — blank-itype `attempted_failed` re-tag,
  gated on `cefi-recapture-sweep-complete` (still false).
- `plans/archive/2026_08/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md` — **RESOLVED 2026-08-08,
  re-verified 2026-08-09, ARCHIVED 2026-08-12**: the Tardis `lighter` entitlement gap is gone (re-probed live,
  non-1st-of-month dates return real data); the LIGHTER-ZKSYNC `derivative_ticker` re-launch VERIFY landed (16,491
  captured rows, 2026-04-17..2026-08-02, source=tardis) and Layer-1 confirms LIGHTER-ZKSYNC is no longer among cefi's
  missing tuples (only BITGET-FUTURES/OKX-FUTURES remain) — all todos `[x]`, archived alongside its finalize plan.
- `/plans/archive/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` — ✅ DONE (`deployment-service@9b13679`,
  launcher entries removed).
- `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` — spot-check GCS/manifest/UI
  consistency (dispatched as a bounded slice via `cefi_misc_audits_and_hygiene_2026_07_25.md`) + decide the
  reconciliation cadence (stays human).
- `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md` —
  `deribit_volatility_index_handler.py` and `book_microstructure_handler.py` stamp `available_at` from BATCH-run
  wall-clock instead of a deterministic per-row/`as_of` timestamp. Audit-only finding, code fix not yet started.
- `issues/cefi_margin_model_hyphenated_instrument_id_misclassification_2026_07_27.md` — `_CefiMarginModelBase.compute()`
  only strips a colon-delimited prefix, so hyphenated instrument ids from AccountQueryClient/UPI adapters
  (`BTC-USD-PERP`) never match `CEFI_MARGIN_TIERS`; the tier-miss fallback then self-referentially substitutes
  `mmr_warning_pct` as the assumed MMR rate, misclassifying healthy positions as WARNING/CRITICAL. Affects every live
  CeFi margin computation (both `margin_health.py` and the new `emit_live_cefi_margin_events` push path). P1, open.
- `/plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md` F5 (rehomed here 2026-07-27, was falsely
  cited "0 open todos" there) — bybit dated-futures fetches (`BTC-26DEC25`, `MNTUSDT-29MAY26`) time out en masse against
  `datasets.tardis.dev` (~2,600 failures/VM across `cefi-bybit-2025-light`/`cefi-bybit-2026-light`) while perps succeed;
  the date is marked OK regardless. Open question: are these failures recorded as honest-absence (`record_captured`
  failed/unattempted) or silently dropped — verify before deciding whether it's a vendor-gap skip-list fix or a
  recording-correctness bug. P2, open.
- `/plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md` §C9 (rehomed here 2026-07-28 per
  operator ruling 2026-07-27, interactive session §5#27; source doc archived 2026-07-28, `[unlock-plan]` granted — see
  that doc's C9 section) — EXTENDED candle/ohlcv fetch path (`_fetch_extended_candles_for_symbol`,
  `adapters/_umi_extended.py:151`) silently swallows HTTP-error/exception/ empty-200 failures (no
  `failed_per_instrument` param wired, unlike sibling `/funding`/`/trades`/`/orderbook`) — a real honest-absence
  violation, low MVP urgency (ohlcv non-MVP today), ~10-line fix (thread the failure router + `record()` on error +
  `record_empty()` on empty-200). P3, open.

✅ **DONE 2026-08-05** — 12 non-Tardis cefi VM classes evaluated, 12 PASS, 0 FAIL. The one class closest to the bar
(mdps-backfill single-VM for cefi) already has a cross-machine-sharded launcher. Read-only fleet audit, no code change.
Full evidence: `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 2 Progress Log.

## Operator dispositions (2026-07-18) — pre-migration execution

> The operator reviewed the audit and directed a pre-migration close-out. Each maps to a source doc; archive the source
> when its item lands.

- [x] ✅ [BACKEND] P0. **DERIBIT missing-quote fix + `prod/catalog.parquet` rebuild** — DONE
      `instruments-service@d72edcf7` (adapter/builder fix — DERIBIT `instrument_id` always `BASE-QUOTE`) +
      `instruments-service@b2e084fa` (Phase-−1 gate extended with the quote-mandatory assertion), both 2026-07-18;
      live-verified 2026-07-27 against the 429,129-row `prod/catalog.parquet`: `GREEN=True`, 0 `:PERP:`, 0
      id!=canonical, **0 missing-quote**. Full evidence:
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 1, archived).
- [x] ✅ [BACKEND] P0. **Remove the UAC-seed catalogue fallback — catalogues FAIL LOUD** — DONE
      `market-tick-data-service@3253cae3`. New `InstrumentCatalogUnavailableError(RuntimeError)`; cefi/defi/tradfi
      `list_instruments` + sentinel paths now RAISE on absent/empty/schema-drift; off-season empty sports stays honest.
- [x] ✅ [BACKEND] P0. **Gate Tardis cefi on the vendor response + stop false `attempted_failed`** — DONE
      `market-tick-data-service@a7569298`. Tardis HTTP-400 `code=300`/`code=140` now classified structural-absence. **⚠️
      CORRECTION (operator 2026-07-18): the futures_chain 122,585 are NOT source-absence** — see Track 4 above; they
      FILL on the Track-2 coverage backfill, not a reclass.
- ✅ **DONE 2026-07-26** — UAC per-venue seed fallback blast-radius audit (candidate 9 of
  `cefi_consolidated_native_ao_extract_2026_07_25.md`): 3 real production callers found, all blocking removal today (2
  by explicit design). Filed `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`
  (`unified-trading-pm@2a6a7db62`). The parent `[OPERATOR]` todo (line below) is already closed with ruling "KEEP,
  deferred." Full evidence: `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 9 Progress Log.
- [x] ✅ [PM] P1. **Decide whether to remove the UAC per-venue seed fallback — RULING: KEEP, do not remove** (deferred,
      not declined). Forked to `cefi_misc_audits_and_hygiene_2026_07_25.md`, ruled 2026-07-26 (retagged
      `[OPERATOR]`→`[PM]` 2026-07-28): all 3 real production callers currently depend on the fallback firing (2 by
      explicit design), removing it now would reproduce the silent-coverage-loss regression the 2026-07-18
      `mtds@3253cae3` ruling eliminated for CEFI. Full audit + revisit trigger:
      `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` (unified-trading-pm@2a6a7db62).
- [x] ✅ [DOCS] P1. **Upgrade the `data-pipeline-check-mtds` skill** — DONE `unified-trading-pm@ca3aebfc7` (DERIBIT
      futures_chain negative check, DERIBIT/BINANCE-FUTURES content spot-checks).
- [x] ✅ [INFRA] P1. **`/plans/archive/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`** — DONE
      (`deployment-service@9b13679` removed the DRIFT/PACIFICA launcher entries; `instruments-service@ee19f6f3` hardens
      against re-mint).
- [x] ✅ [BACKEND] P2. **`_L5_VENUES` RESOLVED-BY-DELETION** (2026-07-18) — the hardcoded tuple no longer exists
      (`market-tick-data-service@a4fb3d13` retired `order_flow_imbalance` entirely). The 2 onchain sub-audits stay open
      in the issue doc (DeFi, not cefi — outside this close-out).
- **Track 0 above**: `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phases 1/1b/1c/2/5 (operator ruling
  2026-07-25 — see Track 0, embedded natively in this doc, sequenced ahead of/alongside the migration).
- [x] ✅ [VERIFY] P2. **Reconciliation-gap spot-check — DONE.** Spot-checked the next 3 unverified findings (DERIBIT
      live-vs-batch FUTURE misclassification, HUOBI/BITSTAMP venue-universe gaps, OKX `margin_type` inversion) across
      GCS/manifest/deployment-api/UI layers, dispatched as part of `cefi_misc_audits_and_hygiene_2026_07_25.md`. Full
      PASS/FAIL verdicts + evidence:
      `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` Progress Log
      (unified-trading-pm@ab28a0f39). That doc's `[DECISION]` P2 reconciliation-cadence todo remains separately
      open/human.
- [x] ✅ [PM] P1. **Consolidate + archive `issues/cefi_layer1_denominator_gaps_2026_07_03.md` — DONE.** Confirmed 0 open
      checkbox-syntax todos of its own, `status` flipped to `resolved`, moved to `plans/archive/issues/`
      (unified-trading-pm@ff8312609), dispatched (re-scoped to the 2 named docs) as part of
      `cefi_misc_audits_and_hygiene_2026_07_25.md`. Sibling
      `issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md` already archived — no action needed there.
- [x] ✅ [REVIEW] P0. **Track-2 coverage decision — RULED** (same decision as the Track-2 ruling above; not a second
      decision). Re-open the completion program + reverse the inferred 50.79% acceptance. Autonomous ruling within
      documented intent (/autonomous 2026-07-18); operator can reverse.

## Track 8 — Non-canonical ENUMERATION audit → align EVERY form to one SSOT (operator ask, 2026-07-18) · P0

> **Numbered 8, not 6 or 7 (pre-existing, unchanged by this pass)** — this section was renumbered off a duplicate "Track
> 6" heading collision with the hygiene-items section above; Track 7 (candle-namespace, below) already existed at the
> time, so this became Track 8 rather than re-colliding. Reading order (Track 8 before Track 7) does not match numeric
> order — a pre-existing quirk, not introduced by the 2026-07-25 split.

- **Source / ask**: the deployment-ui/api "data status" view used to enumerate every instrument_type / data_type / chain
  / venue in the GCS data/manifest for an asset_group — a duplication + non-canonical-naming detector. Removed from the
  UI/API; operator (2026-07-18): re-add it, and use the enumeration so the migration is COMPLETE (align EVERY
  non-canonical form to one SSOT), not just the classes Scripts 1-4 target.
- **Audit tool**: `market-tick-data-service@81b72f1d`
  (`scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`). Measured live 2026-07-18 on the
  **11,185,557-row** cefi manifest: **instrument_id 1,864,357 non-canonical (16.67%)**; **instrument_type COLUMN drift**
  (BLANK 3,186,640, lowercase `perpetual` 289,700, etc.); minor venue/data_type drift. Full breakdown moved to
  `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s live-manifest-worklist table.
- **Coverage gap (why the `--apply` must WAIT)**: Scripts 1-4 resolve ~380k bare-wire; ~1.48M non-canonical rows
  (blank-itype-driven bare-wire, `:PERP:`, missing-quote, COMBO) need DEDICATED paths — Track 8 gates the cutover
  `--apply` (now `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`).

- [x] ✅ [REVIEW] P0. **Operator canonical rulings — RECEIVED 2026-07-18.** The rebuilt catalogue is the SSOT: (1)
      blank/missing instrument_type → catalogue-resolve + venue-suffix-infer; (2) orphans not in catalogue → DROP unless
      cleanly mappable; (3) KALSHI-PERP/POLYMARKET-PERP → DROP (100% `empty_confirmed`, no real data); (4) DERIBIT:COMBO
      is CANONICAL (gets migrated, not excluded).
- [x] ✅ [SCRIPT] P0. **instrument_type column normalization** — DONE `instruments-service@555ddf1c` (dry-run measured:
      3,824,258 itype rows changed; canonical-fraction 84.98%→99.41%). **`--apply` DRAIN-GATED under the Track-1
      cutover.** Casing freeze lifted 2026-07-20 (ruling D1, UPPERCASE ratified) — ruling recorded in
      `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § D1.
- [x] ✅ [SCRIPT] P0. **`:PERP:` → `:PERPETUAL:` rewrite** — manifest side SHIPPED (`instruments-service@555ddf1c`,
      374,227/374,272 rows). **On-disk GCS rename — DONE 2026-07-27** (sub-agent): live audit confirmed 0 `:PERP:`-form
      rows both before and after (manifest side already corpus-wide-complete); a fresh 9-shard `--dry-run`
      re-verification (full corpus, 2019-03-30..today) confirmed 0 further planned changes on every shard except the
      already-analyzed DERIBIT spot/perpetual-mislabel collision class (~5,001 objects, left honest-raw per that
      finding's own "leave as-is, zero data loss" ruling — not a fresh open call). Full evidence:
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 2, archived). ✅ **DONE
      2026-07-27** — writer-side fix (candidate 8 of `cefi_consolidated_native_ao_extract_2026_07_25.md`) found ALREADY
      FIXED: `market-tick-data-service@c20ea464` + `@1e8870b1` (2026-07-08). All HL/ASTER/LIGHTER/EXTENDED capture write
      paths emit `PERPETUAL` (never `:PERP:`), confirmed via repo-wide grep + fresh unit test run (114 tests, 100%
      pass). No new commit was possible or needed. Full evidence: `cefi_consolidated_native_ao_extract_2026_07_25.md`
      todo 8 Progress Log.
- [x] ✅ [SCRIPT] P1. **bare-wire / missing-quote / DATED-contract recovery** — DONE `instruments-service@555ddf1c`
      (operator Option A + resolver-gap fix). +115,225 captured dated rows / ~40.7B ticks recovered via the dated-wire
      itype-fix; +3,531 rows / 186M ticks via the `-SPOT`/`-SWAP` override. Result: adjusted canonical-fraction 99.41%.
      Residual 53,965 captured rows / 7.46B ticks, all genuinely-unresolvable (captured-with-data dropped = 0).
- [x] ✅ [BACKEND] P0. **POST-CUTOVER: flip the smoke-check + downloader to canonical ids** — CODE SHIPPED
      `market-tick-data-service@a4f90769` (2026-07-27, slot-13): `venue_fetch._process_venue` resolves canonical
      `--instrument-ids` to raw wire symbols via `CeFiWireCanonicalMap.raw_symbol_for`; `pipeline_e2e_check.py`'s
      canonical-stem skip-guard removed. **Residual live-refetch proof CLOSED 2026-07-28**: a real end-to-end VM smoke
      run (`pipeline_e2e_check.py --day 2024-06-15 --venue BITFINEX-FUTURES --tardis-only --legs force --auto-day`) —
      the `CEFI:BITFINEX-FUTURES:trades` shard passed `exit=0`, a real parquet written
      (`BITFINEX-FUTURES:PERPETUAL:AAVE-USDT@LIN`), manifest status `captured`; the other 8 shards' `no_parquet_under`
      failures are an unrelated data-availability gap (the venue genuinely has no data for those data_types on that
      day), not a canonical-id-resolution failure. Full evidence:
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 4, archived);
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md` (RESOLVED section).
- **Re-add the "data status" enumeration to deployment-ui/api** — code COMPLETE + `quality-gates.sh`-green
  (deployment-ui shipped `deployment-ui@3fb6779`; deployment-api blocked only on 3 dirty sibling-repo deps as of
  2026-07-18, now **7 days stale — re-check before trusting**). Investigation found no single removal commit; shipped as
  a NEW read-only endpoint (`GET /api/data-status/axis-value-census`) rather than touching the legitimate math fix that
  eroded the raw-value signal. ✅ **DONE 2026-07-27** — found ALREADY LANDED (`deployment-api@09656f42`, 2026-07-18,
  well before this triage), touches all 4 cited files, `Quickmerge: agent` trailer, ancestor of current
  `live-defi-rollout`, `gh run list` green, all 3 previously-dirty deps now clean. No new commit was possible or needed.
  Full evidence: `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 5 Progress Log.
- [x] ✅ [DATA] P1. **Enumeration-audit terminal checkpoint** — DONE 2026-07-27. Re-ran
      `scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py` (read-only) against the live cefi manifest
      post-cutover (8,880,557 rows): **`instrument_id` 8,790,637/8,880,557 canonical (99.49%)**, the 45,170-row residual
      all bare-wire/missing-quote/bad-itype (accepted-exception class), down from the pre-migration ~1.48M.
      `instrument_type`: 2,982 non-canonical, dominated by already-ruled lowercase-casing variants (D1/D2 2026-07-20). 2
      findings without an existing ruling filed as a new followup (not silently accepted):
      `issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`. Full evidence:
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (todo 5, archived).
      **Superseded 2026-08-17**: the `instrument_type` 2,982 figure above is stale — re-verified live and found to
      have grown 13x to 39,286 (an active writer regression, since fixed); the `instrument_id` figures above are
      unaffected. See `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`.
- [ ] [DATA] P2. **na-eligibility-audit 2026-08-16**: extracted to `cefi_casing_residual_ao_dispatch_2026_08_16.md`
      (+ finalize) — **both now archived 2026-08-17** (`plans/archive/2026_08/`); re-count done (residual is
      39,286, not 2,982 — active writer regression, since fixed via `market-tick-data-service@c07cc70e93`), but the
      literal-0 done-when below is NOT yet met — the `--apply` VM dispatch is in flight, not complete. Stays open
      here (source doc), tracking through to `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`
      (live follow-up) until that reaches 0. Original text: **Folded in 2026-08-02 from
      `/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md` (operator directive,
      2026-07-24).** cefi's `instrument_type` casing target is literal **100% UPPERCASE**, not the "substantially
      complete"/99.41%-snapshot framing above — the 2,982-row non-canonical residual the checkpoint todo just above
      found (dominated by already-ruled D1/D2 lowercase-casing variants) must reach literal 0 before the deployment-ui
      data-status Distinct Values panel is considered clean for this axis. Not yet closed as of this fold — a fresh live
      re-count against the current manifest is the done-when, same convention as tradfi's already-closed equivalent todo
      (`tradfi_manifest_content_recovery_completion_2026_07_24.md`, casing sub-scope). (repo: instruments-service,
      unified-trading-library)

## CEFI CANONICAL SPEC (operator-authoritative, 2026-07-18 — the migration target)

> ⚠️ **Possible overlap with the "Pass-through" section, flagged not resolved** — see
> `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s own flag on that moved section.

**Shard atom** (identical across writer/manifest/status/gate/UI):
`pipeline_mode({mode}_{source}) · date · asset_group · venue · [chain] · instrument_type · data_type · (instrument_id OR underlying) · [quote · margin] · source`.
Flat-per-contract shards key on `instrument_id` (filename == column == manifest key). **BUNDLE shards
(`options_chain`/`futures_chain`) key on `underlying`; per-row `instrument_id` MAY BE NULL by design.**

**Representative canonical ids (cefi)**: `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` · `BINANCE-SPOT:SPOT_PAIR:BTC-USDT`
(no margin on spot) · `BYBIT:FUTURE:BTC-USD@INV-20231201` (per-contract, not a bundle) ·
`DERIBIT:OPTION:BTC-USD@INV-20260401-3250-C` (options_chain bundle, **quote ALWAYS**) ·
`DERIBIT:FUTURE:AVAX-USDC@LIN-20260401` (futures_chain bundle; USDC=linear) · `OKX-SWAP:PERPETUAL:BTC-USD@INV` (folds to
OKX in Layer-1) · `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN` (USDC-margined) · `ASTER:PERPETUAL:BTC-USDT@LIN` (USDT
corrected). Margin: quote∈{USDT,USDC,…}→`@LIN`, quote==USD→`@INV`; SPOT no marker.

**Drop venues (cefi purge, remove entirely, snapshot-first)**: BITSTAMP/HUOBI/GEMINI/PHEMEX (defunct); Solana-perp cull
DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN. **KEPT registered (NOT purged)**: **BINANCE-DELIVERY** (live
COIN-M product — descope from MVP backfill, keep the UAC scaffold + its real captured data; operator ruling 2026-07-18,
overriding the earlier "purge" framing — do NOT delete its data), KALSHI-PERP + POLYMARKET-PERP (roadmap — do NOT drop
despite being empty), LIGHTER-ZKSYNC (blocked-scaffold), EXTENDED-STARKNET (MVP). SSOT:
`/codex/02-data/cross-asset-canonical-target-ssot.md` §10. (Bundle keys on `underlying`, NOT a synthesized `VENUE:BASE`
id.)

## MVP universe (SSOT: `/codex/02-data/mvp-scope-canonical.md`)

> Consolidates the per-venue MVP status scattered across the Operator dispositions section and the CEFI CANONICAL SPEC
> above into one place, cross-checked against the codex SSOT's CeFi MVP table (config v16). States which cells are
> **PROVEN WIRED** (real captured data flowing, evidenced elsewhere in this plan) vs. just **DECLARED IN-SCOPE**
> (registered/planned but not yet flowing data).

**Codex MVP venue list (config v16)**: BINANCE-SPOT/-FUTURES · BYBIT(/-SPOT) · OKX-SPOT/-SWAP/-FUTURES · DERIBIT ·
HYPERLIQUID · ASTER · KRAKEN-SPOT/-FUTURES · COINBASE-SPOT/-FUTURES · BITFINEX-SPOT/-FUTURES · BITGET-SPOT/-FUTURES ·
UPBIT · LIGHTER-ZKSYNC · EXTENDED-STARKNET.

| Venue(s)                                                                                                                                                                               | Codex MVP status                                                                                                                                | Wired status (this plan's evidence)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-SPOT/-FUTURES, BYBIT(/-SPOT), OKX-SPOT/-SWAP/-FUTURES, DERIBIT, HYPERLIQUID, ASTER, KRAKEN-SPOT/-FUTURES, COINBASE-SPOT/-FUTURES, BITFINEX-SPOT/-FUTURES, BITGET-SPOT/-FUTURES | MVP                                                                                                                                             | **PROVEN WIRED** — real captured rows throughout the 11.19M-row cefi manifest; KRAKEN-SPOT independently re-verified fully clean 2026-07-23                                                                                                                                                                                                                                                                                                                                                                          |
| EXTENDED-STARKNET                                                                                                                                                                      | MVP                                                                                                                                             | **PROVEN WIRED** — "live MVP" per the CEFI CANONICAL SPEC + Operator dispositions sections                                                                                                                                                                                                                                                                                                                                                                                                                           |
| LIGHTER-ZKSYNC                                                                                                                                                                         | MVP                                                                                                                                             | ✅ **DONE 2026-07-28** — canonical-rename backfill complete (candidate 10 of `cefi_consolidated_native_ao_extract_2026_07_25.md`). Reused existing general-purpose migration script: dry-run `already_canonical=12,908, would_rename=0, would_merge=0` — fully resolved. Code: `market-tick-data-service@feeb8a6e` (dtype fix in `do_merge()`). Live capture remains BLOCKED-CREDENTIALS (separate, not this item's scope). Full evidence: `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 10 Progress Log. |
| UPBIT                                                                                                                                                                                  | MVP                                                                                                                                             | ✅ **DONE 2026-08-04** — VERDICT: FAIL against MVP definition (FAIL on 2.5+ month data gap). Live manifest: 488 active instruments, Tardis-only coverage 2021-03-03..2026-05-22, then ZERO objects May 25→present (72+ days). Filed `issues/upbit_cefi_data_gap_may_2026_2026_08_04.md` with P1 follow-up. Full evidence: `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 6 Progress Log.                                                                                                                   |
| BINANCE-DELIVERY                                                                                                                                                                       | **NOT MVP** (COIN-M inverse/delivery, decision #3)                                                                                              | Registered/kept in UAC (not purged) with real historical captured data, but explicitly descoped from MVP backfill going forward — do not re-add to MVP scope                                                                                                                                                                                                                                                                                                                                                         |
| KALSHI-PERP, POLYMARKET-PERP                                                                                                                                                           | **NOT in the codex CeFi MVP table today** — this plan's "roadmap, will be added" framing is a future-scope declaration, not a current MVP grant | **NOT WIRED** — verified 2026-07-18: 100% `empty_confirmed`, `row_count=0`, `instrument_count=0`; kept registered purely for the roadmap                                                                                                                                                                                                                                                                                                                                                                             |
| BITSTAMP-SPOT, HUOBI-SPOT/-FUTURES, GEMINI-SPOT, PHEMEX-SPOT (defunct); Solana-perp cull (DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN)                                    | **NOT MVP**                                                                                                                                     | Being PURGED entirely (snapshot-first) per the Operator dispositions venue-purge ruling — never re-add                                                                                                                                                                                                                                                                                                                                                                                                               |

## Track 7 — Candle namespace bundle-collision residual (`processed_candles/`) · FORKED · P2

> ✅ **DONE 2026-08-04.** The verify + targeted MDPS `--force` backfill (candidate 7 of
> `cefi_consolidated_native_ao_extract_2026_07_25.md`) completed: Part (a) raw-tick presence verified — ALL 8 days PASS;
> Part (b) 149 residual objects ALL GONE (verified via `gsutil stat`). Bundle integrity audit: 7/112 cells OK, 9
> partial, 96 missing — MDPS `--force` backfill blocked on compute (framework load unsafe for shared VM, needs dedicated
> VM). Code: `market-tick-data-service@feeb8a6e` (dtype-normalization fix for `do_merge()`). Follow-up:
> `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md`. The terminal `[OPERATOR]`-gated delete of the 149
> stale objects is ACCOMPLISHED (all gone); remaining work is bundle regeneration only. Full evidence:
> `cefi_consolidated_native_ao_extract_2026_07_25.md` todo 7 Progress Log.

- **Source**: `issues/candle_feature_canonical_path_divergence_2026_07_20.md` todo 19 (folded 2026-07-23). CEFI's live
  `processed_candles/` corpus is 99.98%+ clean (405,259/405,408 objects `CANONICAL_NOOP`); the residual is exactly 149
  objects (93 BYBIT `futures_chain` + 56 DERIBIT `options_chain`), listed in
  `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv` — real, distinct per-contract-leg candle files
  that lost a bundle-target-collision race, NOT redundant duplicates (deleting first = permanent data loss).
- **Close-out criterion**: the 8 affected `(day, venue)` cells re-derived via MDPS backfill, the regenerated bundle
  verified complete, the 149 stale objects then safely deleted, and todo 19 updated to reference this track's
  resolution.

## Codex SSOTs (read before touching a track)

`/codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`
(Tardis cap + the throughput-fix ruling), `/codex/06-coding-standards/read-time-filter-pushdown.md`.

## Aggregated source docs

> Full discoverability index of every other cefi-relevant plan/issue (with open-todo digest) lives in
> [`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`](/plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md)
> — including, as of 2026-07-25, the "Pass-through from the 2026-07-18 consolidated canonicalisation audit" section
> (operator decisions + live manifest worklist table) moved there verbatim from this doc.

## Progress Log

- **slot-3 2026-08-17 (review)**: `cefi_casing_residual_ao_dispatch_2026_08_16.md` (+ finalize) archived to
  `plans/archive/2026_08/` — re-verified independently, writer-regression fixed
  (`market-tick-data-service@c07cc70e93`), VM apply dispatched (not yet complete). Annotated the stale 2,982
  `instrument_type` citation above (P1 checkpoint) as superseded; updated the P2 todo below to track through to
  `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md` (kept open — literal-0 done-when not
  yet met).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 10)**: confirmed against
  `/codex/02-data/cross-asset-canonical-target-ssot.md` D1 — manifest `instrument_type` COLUMN case is
  UPPERCASE for cefi (operator-ruled 2026-07-20, "uppercase is fine"), matching this same line 523/2,982-row
  directive exactly. This is the SAME item already extracted in round 3 (below), not a separate open question —
  the audit report's flagging of it as distinct was a duplicate, closed by citation. No new action.
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: the instrument_type casing residual
  (line 523, 2,982 non-canonical rows) — **re-count fresh, then apply** — extracted to
  `cefi_casing_residual_ao_dispatch_2026_08_16.md` (`assigned_vm: planning`).

> **Full day-by-day Progress Log + DELTA checkpoints** live in
> [`cefi_4surface_migration_execution_log_2026_07_24.md`](/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md)
> — read that file for the complete narrative (PRE-COMPACT checkpoints, DELTA session updates, deferred-work tables)
> from plan-authoring (2026-07-18) through the 2026-07-24 ~13:35Z Step 8 verdict. **Fully mirrored as of 2026-07-25**
> (the 4-child split moved every remaining DELTA section there verbatim — nothing stays duplicated here). Keep appending
> new session entries to that child file, not here, going forward.
>
> **Current status** (as of the child's last entry, 2026-07-24 ~13:35Z Step 8 verdict): CeFi 4-surface migration still
> IN FLIGHT. KRAKEN-SPOT rename is DONE (Surface A genuinely clean for that venue); LATE colliding-venue renames +
> Surface C v2 manifest-dedup `--apply` + LIGHTER-ZKSYNC backfill remain the critical-path items (tracked in the child's
> Deferred-work table) — do NOT assume done without re-measuring. The `/autonomous` loop is OFF; resuming requires a
> fresh explicit invocation.

- **2026-07-27** — Discoverability fix (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 4): 2
  cefi-tagged docs reclassified `assigned_vm: NA → planning` this session were not mentioned anywhere in this hub, the
  exact "orphan invisible to sweep" bug class fixed twice before (entry #18/#25 in
  `autonomous_session_operator_decisions_2026_07_25.md`). Added here for future tranche-sweep discoverability:
  `issues/cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md` (DNS-starvation Tardis-client fix, mechanical
  apply-of-proven-pattern) and `mdps_candle_manifest_population_disconnect_2026_07_25.md` (candle-manifest root-cause +
  fix, multi-AG tagged cefi-first). Neither is tracked in any Track above; both are now `assigned_vm: planning` and live
  in the AO backlog.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - carries a BLOCKED-DATA Korea-equity
  vendor ask (operator) plus 3 `[DESIGN]` archetype/hedge-venue calls that are not worker-determinable.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — was codex-only; swapped 3 of the 5 codex docs for
  the migration-cutover critical-path child, the execution-log child, and a source path (the noncanonical
  manifest-enumeration audit script cited in the closeout's own body).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict;
  still mixes genuinely bounded script work with real DESIGN/judgment calls (strategy-service archetype design,
  hedge-venue choice), a BLOCKED-DATA Korea-equity vendor ask, and VM-preemption-gated backfill re-launches.
- **stale-checkbox reconciliation 2026-08-05** (slot-15, review): all 5 stale-checkbox findings identified by
  `cefi_consolidated_native_ao_extract_2026_07_25.md`'s triage re-verified against live state — (1) KRAKEN-SPOT
  `_PATH_RE`: Surface A still clean, 155,872 objects auto-renamed, execution-log checkbox stays `[x]`; (2) 658 wire
  keys: 213/216 shipped + 3 permanent terminal state confirmed, execution-log checkbox stays `[x]`; (3) ≈5,413
  catalogue-gap: enumeration half flipped to `[x]` (`instruments-service@f6f16785` shipped, 211 gap rows measured),
  OKX-SPOT/COINBASE-SPOT fix half stays open (needs operator decision on `_CEFI_VENUE_QUOTE_EXTENSIONS`), BITGET-FUTURES
  fix half already closed via todo 1 (candidate 11) of the extraction plan; (4) COMBO-in-perp design: design doc exists,
  execution-log checkbox stays `[x]`; (5) DERIBIT combo mispartition part (a): `mtds@2ddc6d4a` confirmed ancestor of
  `origin/live-defi-rollout`, flipped to `[x]`, part (b) stays operator-owned. Plus `_DRYRUN_COLS` P0: `"chain"`
  confirmed in `_DRYRUN_COLS` at `instruments-service/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py:220`,
  `1284606a` on LDR — fix predates the triage. All evidence in `cefi_4surface_migration_execution_log_2026_07_24.md`.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — hub/coordination doc that references
  (does not duplicate) every open cefi plan/issue; of 15 open items, most sit under explicit redirect banners (the fleet
  docs are ground truth, not this roll-up) or are embedded judgment/design calls from a source plan per an operator
  sequencing ruling. Not a dispatchable unit.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries) — all 6 (2 codex SSOTs, the
  aggregated-sources + migration-cutover-critical-path + execution-log children, and the noncanonical-enumeration audit
  script) re-verified still resolving on disk.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — hub doc, 15 open items: 9 genuine build/investigation work, 3
  operator-gated (Korea-equity vendor ask, 2 strategy-desk design calls), 3 dependency-blocked (Track 1 cutover + 2
  Track 2 post-backfill gates in sibling fleet docs).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-checked against today's 9
  cheat-sheet rulings; none convert this hub's mixed content into a bounded whole (Track 0's Korea-equity vendor ask was
  independently resolved 2026-08-07 in the sibling `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` doc —
  see that doc's own fix in this same sweep — but this doc's DART/hedge-venue design item was already resolved today
  in-doc, and Track 0 still carries genuine `[SCRIPT]`/`[UAC]`/`[DESIGN]` build items alongside real operator- and
  dependency-gated ones). Whole-doc flip stays blocked per the HARD RULE (mixed judgment + bounded items). Track 0's
  remaining bounded items (B1/B3/B4 propagation ops, index-perp UAC mapping, KRX Yahoo backfill, Databento L-floor
  measurement, Barchart removal) are candidates for a future satellite-batch extraction (mirroring the established
  `cefi_satellite_ao_dispatch_batchN` pattern) — not executed in this pass, out of this sweep's whole-doc-flip
  mechanism.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, stale-items — closed the Korea-equity-vendor
  mirror item (line 139 area; source doc cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md already closed the
  identical item 2026-08-08 citing a 2026-08-07 operator ruling). Remaining items: Track 1 correctly follows-the-fleet
  per a 2026-08-02 operator ruling (not independently reclassify-able), 2 dependency-blocked backfill-verification
  gates, rest genuine coordination/judgment work.
- **cefi_satellite_ao_dispatch_batch11_finalize 2026-08-09 (slot-17, review) — Track 0 reconciliation**: batch11's todos
  1-5 (the 5 items this doc EXTRACTED to it 2026-08-09) all landed DONE; replaced each `EXTRACTED — see that doc`
  pointer above with the real shipping commit + evidence (verified every cited SHA reachable on
  `origin/live-defi-rollout` before citing it). **Track 0 remaining-open count: 4 of 11** — todo 3 (capture
  indexPrice/markPrice/fundingRate for equity-perps, `[SCRIPT]` P1), todo 4 (wire recurring funding/basis scan,
  `[SCRIPT]` P2), todo 7 (design INDEX-perp cash-and-carry archetype, `[DESIGN]` P1), todo 8 (launch CeFi Tardis
  backfill for the equity-perp window, `[SCRIPT]` P1) — none of these were in batch11's scope (batch11 only extracted
  the 5 items independently verified as bounded/AO-eligible at drafting time; these 4 remain open, uncategorized new
  work).
- **context-scout 2026-08-15**: re-verified context_scope (6 entries), unchanged — the 2 codex SSOTs and the 3 child
  plans (aggregated-sources, migration-cutover critical path, execution-log) + the noncanonical-enumeration audit script
  all still resolve and remain the right minimal reading-list for this hub/coordination doc.
- **na-eligibility-audit 2026-08-16** [body-hash:49a4c9eb8252c6f6]: KEEP-NA, stale-citation fix applied (checkbox(es) corrected to cite where the work actually landed -- see inline citations above). Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17 (re-verify, cefi tranche)** [body-hash:4aede5e2257241d5]: KEEP-NA, valid — full re-read, 6 open items unchanged in substance from the 2026-08-16 marker. Track 0 (2 items): the INDEX-perp archetype design call is GENUINE_WORK; the equity-perp Tardis backfill launch is DEPENDENCY_BLOCKED (Tardis N=1 slot occupied by the live BINANCE-FUTURES 2026 backfill, ~316 days remaining per cefi_tardis_date_concurrency_2026_08_16.md). Track 1 (1 item, the hybrid-cutover execute todo): KEEP-NA on an explicit redirect-banner citation — "the fleet docs are the measured ground truth ... follows the fleet, not the reverse" (2026-08-02 operator ruling) — not re-litigated. Track 2 (2 items, POST-BACKFILL IS/MTDS gates): DEPENDENCY_BLOCKED, redirects to cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md for the relaunch. Track 8 casing residual (1 item): DEPENDENCY_BLOCKED, tracks through to issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md until literal 0. No item individually clears the whole-doc or per-todo RECLASSIFY bar. Doc stays assigned_vm: NA.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (6 entries) — hub/coordination doc, open-item set unchanged in substance since 2026-08-17; the 2 codex SSOTs + 3 child plans (aggregated-sources, migration-cutover critical path, execution-log) + noncanonical-enumeration audit script remain the right minimal set.
