---
doc_type: issue
title:
  GCS path resolution is not centralized — recurring "hand-rolled prefix drifts from canonical shape" bug class,
  workspace-wide audit in progress
summary: >-
  Root-caused via the MDPS `subprocess-per-date` timeout investigation (2026-07-28): a hand-rolled GCS existence-check
  prefix silently omitted the `pipeline_mode=` hive segment, making skip-existing/resume logic ALWAYS report "nothing
  found" for every pipeline_mode-partitioned category. Fixed forward, but a 4-agent audit (CEFI-scoped so far) found
  this is a genuinely recurring pattern — 3 more confirmed instances, plus a confirmed-stale UTL path-registry template
  consumed live by multiple services. No single canonical function resolves read/write paths workspace-wide; every
  service hand-rolls its own. Operator has directed extending the audit to DEFI/TRADFI/SPORTS/PREDICTION (batch + paper
  + live) and designing genuine centralization, under /autonomous.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [meta]
repos:
  [
    unified-trading-library,
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [gcs, path-resolution, pipeline-mode, silent-failure, canonical-paths, centralization]
related:
  [
    /plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md,
    /plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md,
  ]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  found while root-causing mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md Update 13's subprocess-per-date timeout;
  4-agent CEFI-scoped audit dispatched 2026-07-28 per operator directive, then scope-expanded to
  defi/tradfi/sports/prediction + batch/paper/live under /autonomous.
resolved_by:
depends_on: []
---

# GCS path resolution centralization audit

## Origin

Found while root-causing the MDPS `subprocess-per-date` 30-min-timeout bug
(`/plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 13, 2026-07-28):
`market_data_processing_service/app/core/orchestration_scanner.py::_check_existing_outputs` built its GCS
existence-check prefix as `processed_candles/by_date/day={date}/timeframe={tf}/data_type={dt}/`, omitting the
`pipeline_mode=` hive segment the 2026-07-20 LOCKED canonical shape requires. Because GCS prefix listing is a literal
string match, this was never a crash — it silently returned "nothing exists here" on every call, so skip-existing never
worked for any pipeline_mode-partitioned category and every retry redid all prior work from scratch. Fixed:
`market-data-processing-service@df02dd0`.

**This is a recurring pattern, not a one-off**: the SAME bug class was already found+fixed ONCE before (2026-07-26,
`_list_blobs_scoped_by_venue`, the raw-tick LISTING side) — meaning this was at least the third independent occurrence
before today's audit even started.

Operator's directive (2026-07-28, verbatim intent): "worth doing a full audit of everything across the codebase to
ensure we don't mix GCS prefixes... centralise all checks to use UTL or UAC — something probably exists already that
maps inputs to paths read and write." Then, after the first (CEFI-scoped) pass landed: "we did this cefi analysis, need
to do defi tradfi sports and prediction too — ideally they use centralised functions to resolve paths, it's not just
about pipeline_mode, it's making sure every read and write path (batch, paper, live) uses the right path per what
canonically the data is supposed to be read and written from/to." Invoked under `/autonomous`.

## The canonical SSOT (as it exists today — itself found to have gaps)

`unified-trading-library/unified_trading_library/config_interface/paths/registry.py` — `PATH_REGISTRY` dict of
`DataSetSpec` entries, each with a `path_template`; consumed via `build_path(name, **partition_values)`,
`build_canonical_candle_path(...)`, `build_canonical_candle_object_path(...)`, `derive_candle_object_path(...)` (the
last two also live in MDPS's `canonical_writer_shaping.py`, delegating to the registry). **No single helper spans every
dataset for existence-checking** — this is the architecture gap the operator is pointing at. Each new dataset gets a
bespoke prefix-builder, which is structurally why this bug class keeps recurring (UTL audit agent's finding).

## Audit round 1 (CEFI-scoped) — COMPLETE, 4 parallel agents, all returned 2026-07-28

### Confirmed bugs (not yet fixed, beyond today's `_check_existing_outputs` fix)

1. **`unified-trading-library/unified_trading_library/config_interface/paths/registry.py:18-24`** — `"raw_tick_data"`
   `path_template` is **stale/wrong**:
   `raw_tick_data/by_date/day={date}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/` has NO
   `pipeline_mode=`/`asset_group=` segment and wrong key order. Real objects (live-verified via `gcloud storage ls` on
   `gs://market-data-tick-cefi-prd-central-element-323112/`, **independently confirmed by 3 of 4 agents**):
   `raw_tick_data/by_date/day={date}/pipeline_mode={pm}/asset_group={ag}/venue={V}/instrument_type={IT}/data_type={DT}/{id}.parquet`.
   **Consumed live**: `unified_trading_library/domain_client/clients/market_data.py:56-65`
   `MarketTickDomainClient.get_tick_data()` calls `build_path("raw_tick_data", ...)` directly — would build a wrong
   prefix. Live-vs-dead-code severity for this exact call site NOT fully resolved (caller census incomplete, one agent's
   budget ran out). **This is the highest-leverage single fix** — one registry correction instead of N per-caller fixes,
   and it's the root cause "just call `build_path()`" doesn't yet work for `raw_tick_data` callers. Two more registry
   rows in the same bucket family (`l2_book_checkpoints`, `liquidation_clusters`, `registry.py:295-308`) show the same
   missing-`pipeline_mode=` pattern — **not GCS-verified, flagged likely-same-bug, unconfirmed**.

2. **`features-service/features_service/delta_one/app/core/dependency_checker.py:648`** — `_discover_instruments()`
   hand-rolls `processed_candles/by_date/day={date}/timeframe={timeframe}/` (no `pipeline_mode=`). Called from
   `validate_lookback_candles()` (line 486) whenever `instruments=None`. Because `LookbackValidationReport.valid`
   defaults `True` and only flips `False` via `add_insufficient()`, an empty discovery list produces a **VACUOUS PASS**
   (0/0 "validated") — the validator silently reports success while validating nothing. This is a **known-open gap**:
   `/plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 4 already asked
   for exactly this audit and this call site wasn't caught then. Reachability of `instruments=None` in the common bulk
   CLI path traced but not fully proven end-to-end.

3. **`market-tick-data-service/market_tick_data_service/cli/handlers/deribit_options_chain_handler.py::_write_shard`
   (~line 515-556)** — calls UAC `build_cefi_partition_path(...)` and uses the result **directly** for the GCS
   read/write, with NO post-hoc `pipeline_mode=` insertion — every sibling CeFi writer
   (`engine/orchestrator/symbol_rules.py:535`, `live/websocket_runner.py:124`,
   `cli/handlers/book_microstructure_handler.py:193`) does this insertion; this one doesn't. Writes the manifest row
   with `pipeline_mode=PipelineMode.LIVE_DERIBIT` but the OBJECT PATH doesn't carry it — a genuine path≠manifest
   divergence. Impact currently unclear: 6 sampled dates (2026-05-15/06-15/07-15/07-26/07-27/07-28) found ZERO Deribit
   options_chain objects at either shape — this data_type may be dormant right now, but the writer is structurally
   broken for whenever it next fires.

4. **`market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py:135,160,320-322`**
   — same missing-`pipeline_mode=` pattern, but with an explicit code comment claiming "the CeFi GCS partition path...
   carries no pipeline_mode segment (unlike DeFi's), so this write path doesn't need it." **This comment may itself be
   stale** — contradicts the 2026-06-01 operator ruling (cited in `symbol_rules.py:487,514-521`) that pipeline_mode is
   canonical-in-path AND primary for cefi/tradfi/prediction. Needs an explicit ruling: deliberate exception, or the same
   bug wearing a self-justifying comment?

### Confirmed dead/duplicate code (not live bugs, but landmines — fix or delete, don't just leave)

- `market_data_processing_service/app/core/orchestration_scheduling.py:262-306`
  `OrchestrationSchedulingMixin._check_existing_outputs` — unreferenced duplicate of the function fixed today, STILL
  carries the broken pre-fix prefix. Zero production callers (only test-only subclasses).
- `market_data_processing_service/config.py:210-240` `get_raw_tick_path()` — zero production callers, same stale order
  as the registry (no `pipeline_mode=`/`asset_group=`).
- `market_data_processing_service/app/core/data_source.py:64` `GCSDataSource` class — zero production instantiations
  (only `LiveDataSource` is instantiated).
- `market_data_processing_service/app/core/output_path_helpers.py:75-101` `build_processed_candle_path()` — zero
  production callers; its own docstring says prefer `build_canonical_candle_object_path`.
- `features-service/features_service/cross_instrument/app/calculators/adv.py:194-214` `_candidate_paths()` — wrong
  timeframe token (`24h` vs real `1d`) + missing `instrument_type=`. Zero live callers found (`RollingAdvReader`/
  `compute_rolling_adv` unused) — a landmine for the first real caller, not an active bug.
- `execution-service/execution_service/utils/loader.py` + `utils/io/loader.py` — byte-for-byte identical dead files,
  `MarketDataLoader.build_path()` missing 3 segments (`pipeline_mode=`, `instrument_type=`, `venue=` — the worst-broken
  prefix found in the whole audit). Zero instantiation call sites, not even exported from `utils/__init__.py`.
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py::build_partition_path`
  (line 434) — a SECOND, independently-maintained copy of UAC's `build_cefi_partition_path`, explicitly documented as
  mirroring it "byte-for-byte." Not dead (used by the Tardis bulk-download lane) but a drift-risk duplicate.

### Confirmed-safe / positive baseline (don't re-flag these later)

- MDPS write path (`candle_write_mixin.py`, `output_path_helpers.py::build_canonical_candle_object_path`,
  `canonical_writer_shaping.py::derive_candle_object_path`) — all correctly delegate to the UTL registry SSOT.
- MDPS's now-fixed `orchestration_scanner.py::_check_existing_outputs` / `_list_blobs_scoped_by_venue` — correctly
  enumerate every candidate `pipeline_mode` via `_candidate_pipeline_mode_values()`.
- Several **day-only-prefix + substring-match-on-full-blob-name** patterns across MDPS/MTDS/strategy-service — robust to
  `pipeline_mode=` position BY CONSTRUCTION (a shallow prefix is a true string-prefix of every real object shape
  regardless of what comes after `day=`). This is a genuinely good, cheap, defensive pattern worth naming as a positive
  convention.
- `features-service/delta_one/app/core/data_loader.py:430-476` `_resolve_blob_paths` — a well-documented 3-tier
  canonical-first probe built on `candle_read_prefixes()`/`build_canonical_candle_path()`.
- `strategy-service/strategy_service/engine/core/canonical_adv_ranked_universe_provider.py:313-360` — shallow `day={D}/`
  prefix + full listing + substring match, sidesteps the whole bug class by construction.
- `instruments-service`'s sports domain — correctly uses UAC's `candidate_parquet_paths()`
  (`unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py`), pipeline_mode-aware and
  legacy-fallback-aware. Some standing orchestrator files (`sports_fixtures.py:217-218`,
  `sports_reference_core.py:64-65`, `weather.py:268-269`, `footystats.py:799-800`) hand-roll the SAME correct dual
  canonical/legacy shape instead of calling the shared helper — not a bug today, but the same duplication pattern that
  caused the original MDPS bug; low-priority follow-up to consolidate onto the one helper.
- `market_tick_data_service/reader.py`, `instrument_availability_paths.py`, `rebuild_*_manifest.py`,
  `reconcile_market_tick_manifest.py`, `check_tradfi_manifest_disk_consistency.py::build_shard_prefixes` — all either
  day-level-list-then-parse or deliberately dual-shape-aware. Correct.

### Not fully verified in round 1

- `MarketTickDomainClient.get_tick_data()`'s real reachability (live vs. effectively-dead) — full caller census
  incomplete.
- `l2_book_checkpoints`/`liquidation_clusters` registry rows — flagged, not GCS-verified.
- MDPS's live-mode async persistence worker (`cli/handlers/live_mode_handler.py:349-354`, `_persistence_worker`) — its
  logging-only path AND the real write's `data_sink.write(..., partition={...})` dict both omit
  `pipeline_mode=`/`instrument_type=`; unclear whether UTL's `ProtocolDataSink`/`get_data_sink()` contract actually
  requires those keys to land canonically. **Needs a UTL-side check of `get_data_sink().write()`'s partition-key
  contract against this call site** — this is THE live/paper real-time path, the operator's "live" axis, and is
  currently unresolved.
- Deribit options_chain / Kalshi-Polymarket-perp findings (MTDS, above) are code-confirmed but not GCS-verified for
  real-world blast radius (sparse/possibly-dormant data_types; a full corpus walk was deliberately avoided per the
  workspace's single-walk/heavy-I/O rule).
- Full line-by-line audit of MTDS's 100+ one-off migration scripts was NOT performed (spot-checks showed
  dual-shape-awareness is the norm post-2026-07-20; deprioritized vs. LIVE standing code).

## What's NOT done yet (the operator's expanded scope)

Round 1 was CEFI-scoped only (every GCS spot-check, every "confirmed for CEFI too" line, targeted the CEFI bucket).
**DEFI, TRADFI, SPORTS, PREDICTION have not been audited for this bug class at all** — each asset group has its own
bucket family, its own pipeline_mode vocabulary, and potentially its own hand-rolled path-construction sites that round
1 never looked at. The operator explicitly wants:

1. The same audit methodology (find hand-rolled prefixes, classify read/write, check against live GCS, resolve
   registry-staleness questions) extended to DEFI/TRADFI/SPORTS/PREDICTION.
2. Explicitly **batch AND paper AND live** code paths checked, not just batch (today's audit was almost entirely
   batch/standing-service code; live-mode and paper-trading read/write paths are a distinct, unaudited surface — see the
   MDPS live-mode landmine above as the one data point so far).
3. A genuine **centralization** design, not just point-fixes — i.e., does a true "resolve me the read/write path for
   dataset X, given these partition keys" universal function need to be built (or does one already exist that services
   should be migrated onto), so this bug class becomes structurally impossible instead of periodically re-discovered.

## Todos

- [x] [SCRIPT] P0. **Fix the UTL `raw_tick_data` path-registry template** — DONE 2026-07-28,
      `unified-trading-library@2943224b`. `path_template`/`partition_keys` now match the real, live, 3-agent-confirmed
      shape:
      `raw_tick_data/by_date/day={date}/pipeline_mode={pipeline_mode}/asset_group={category}/venue={venue}/instrument_type={instrument_type}/data_type={data_type}/`.
      `build_path("raw_tick_data", ...)` now REQUIRES `pipeline_mode=` (KeyError without it), mirroring
      `processed_candles`/`instruments`. Regression test added:
      `tests/config_interface/unit/test_paths_registry_smoke.py::test_raw_tick_data_template_now_requires_pipeline_mode`
      (mirrors `test_processed_candles_template_now_requires_pipeline_mode`). Checked `l2_book_checkpoints`
      (registry.py:303-309) and `liquidation_clusters` (registry.py:310-316) for the same gap: BOTH have it too (no
      `pipeline_mode=`/`asset_group=` placeholder in either template) — but unlike `raw_tick_data`, neither has a
      3-agent-verified live shape or a confirmed real writer (grepped MTDS/features-service: only
      `domain_client/clients/liquidity.py` consumes them, same dead-abstraction layer as `MarketTickDomainClient`; no
      writer found). NOT fixed in this pass — guessing the shape without live-GCS verification risks a confidently-wrong
      fix, worse than the current silent-empty-prefix failure. Tracked as a new P1 todo below. (repo:
      unified-trading-library)

- [x] [SCRIPT] P0. **Complete the `MarketTickDomainClient.get_tick_data()` caller census** and fix or confirm-dead —
      DONE 2026-07-28, `unified-trading-library@2943224b`. Caller census: grepped `get_tick_data\b` workspace-wide
      (excluding tests/.venv) — 3 hits, all inside `unified-trading-library` itself
      (`domain_client/clients/market_data.py`, `domain/standardized_service.py`, `domain/market_data_client.py`, the
      latter two independent hand-rolled implementations, not calling this method) — zero real external callers anywhere
      in the 10+-repo workspace, so the signature change is breaking-change-safe. Fixed
      `MarketTickDomainClient.get_tick_data()` to require `pipeline_mode: str` and pass `category=asset_group` into
      `build_path()`, mirroring `MarketCandleDomainClient.get_candles()`'s established convention exactly. No test
      coverage existed for this specific class (confirmed via grep — `tests/unit/test_domain_clients.py`'s
      `get_tick_data` tests target the DIFFERENT `MarketTickDataDomainClient` class in `domain/market_data_client.py`),
      so nothing broke. `tests/unit/test_domain_client_catalog.py:13`'s `raw_tick_data` mock checked — it fully
      monkey-patches `get_spec()` with its own synthetic spec, isolated from the real registry, so it's unaffected by
      the template change; no update needed. (repo: unified-trading-library)

- [ ] [SCRIPT] P1. **Verify + fix (or confirm-dead) the `l2_book_checkpoints`/`liquidation_clusters` registry
      templates** (`unified_trading_library/config_interface/paths/registry.py:303-316`) — found 2026-07-28 while
      landing the `raw_tick_data` fix above: both templates have the SAME missing-`pipeline_mode=`/`asset_group=` gap,
      but neither has a live-GCS-verified real shape (unlike `raw_tick_data`'s 3-agent confirmation) or a confirmed
      writer — grepped MTDS + features-service, found only readers/consumers in the same dead
      `domain_client/clients/liquidity.py` layer as `MarketTickDomainClient`. First determine whether either dataset has
      a real producer anywhere in the workspace (if not, these are dead-code cleanup, fold into the P2 dead-code todo
      below instead); if a real writer exists, verify its actual GCS shape before touching the template — do NOT
      guess-copy the `raw_tick_data` fix pattern without confirmation. (repo: unified-trading-library)

- [ ] [SCRIPT] P2. **Decide + act on the two duplicate `raw_tick_data` path builders found during the `get_tick_data()`
      caller census** — `unified_trading_library/domain/standardized_service.py:125-127`
      (`f"raw_tick_data/by_date/day={date_str}/data_type={data_type}/{instrument}.parquet"`) and
      `unified_trading_library/domain/market_data_client.py:236`
      (`f"raw_tick_data/by_date/day={date_str}/data_type={data_type}"`) — two MORE independent, mutually-disagreeing,
      hand-rolled `raw_tick_data` path implementations, neither delegating to the registry SSOT. Both live in the same
      domain-client/domain layer already shown dead for `MarketTickDomainClient.get_tick_data()` (zero real callers
      workspace-wide) — `tests/unit/test_domain_clients.py`'s `TestMarketTickDataDomainClient` exercises
      `market_data_client.py`'s class directly, so confirm whether ANY real service imports
      `MarketTickDataDomainClient`/`StandardizedService` before deciding delete-as-dead vs. fix-to-delegate. (repo:
      unified-trading-library)

- [ ] [SCRIPT] P1. **Fix `features-service/delta_one/app/core/dependency_checker.py:648`'s vacuous-pass bug** —
      `_discover_instruments()` needs the same `pipeline_mode=`-aware prefix enumeration MDPS's
      `_candidate_pipeline_mode_values()` pattern uses (or better: a shared UTL helper if one gets built per the
      centralization todo below). This closes
      `/plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 4. Add a
      regression test proving a real discovery list is non-empty for a pipeline_mode-partitioned date (fail pre-fix,
      pass post-fix, matching today's established pattern). (repo: features-service)

- [ ] [DESIGN] P1. **Rule on the two MTDS findings** — (a) `deribit_options_chain_handler.py::_write_shard` missing
      `pipeline_mode=` insertion (path≠manifest divergence, data_type currently appears dormant) and (b)
      `_perp_funding_kalshi_polymarket.py`'s "CeFi paths carry no pipeline_mode" comment (contradicts the 2026-06-01
      operator ruling cited in `symbol_rules.py` — deliberate exception or stale bug?). Needs a real judgment call, not
      a guessable fix — is (b) a genuine carve-out for these two non-standard prediction-market-shaped cefi writers, or
      should they conform like every sibling writer? (repo: market-tick-data-service)

- [ ] [DESIGN] P1. **Resolve the MDPS live-mode async-persistence partition-key question** — does UTL's
      `get_data_sink().write(..., partition={...})` actually require `pipeline_mode=`/`instrument_type=` to land
      canonically, or does the sink derive them some other way? This is the ONE live/paper-path data point found so far
      and it's unresolved — the operator explicitly called out live/paper as in-scope, so this needs an answer, not just
      a flag. (repo: unified-trading-library, market-data-processing-service)

- [ ] [SCRIPT] P2. **Delete or fix the 6 confirmed dead/duplicate path-construction sites** listed above
      (`OrchestrationSchedulingMixin._check_existing_outputs`, `get_raw_tick_path()`, `GCSDataSource`,
      `build_processed_candle_path()`, `adv.py::_candidate_paths`, `execution-service`'s duplicate
      `MarketDataLoader.build_path()` files) — CLAUDE.md's "delete deprecated code, no shims" rule; each is either truly
      dead (delete) or a landmine waiting for its first real caller (fix to match canonical shape first, or delete if
      genuinely superseded). Low individual risk, real hygiene value, cheap to batch together. (repo:
      market-data-processing-service, features-service, execution-service)

- [ ] [SCRIPT] P1. **Extend the audit to DEFI** — same 4-agent-style methodology (hand-rolled prefix hunt, live GCS
      spot-check, registry-staleness check), scoped to the DeFi bucket family and DeFi-specific writers/readers across
      MDPS/MTDS/features-service/strategy-service/execution-service/instruments-service. DeFi has its own
      `pipeline_mode` vocabulary (see `/codex/02-data/defi-canonical-naming-ssot.md`) — do not assume CEFI's findings
      transfer directly. (repo: all of the above)

- [ ] [SCRIPT] P1. **Extend the audit to TRADFI** — same methodology, scoped to the TradFi bucket family
      (`/codex/02-data/tradfi-databento-sourcing-ssot.md` for the sourcing/pipeline_mode conventions). (repo: all of the
      above)

- [ ] [SCRIPT] P1. **Extend the audit to SPORTS** — same methodology. Sports is where today's ORIGINAL P2/P3 work
      happened (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`) — cross-reference against that doc's findings so
      this doesn't re-discover the same ground. (repo: all of the above)

- [ ] [SCRIPT] P1. **Extend the audit to PREDICTION** — same methodology, scoped to KALSHI/POLYMARKET's `pipeline_mode`
      conventions (today's P2 fix, `market-data-processing-service@df02dd0`, is the one already-confirmed PREDICTION
      data point — build from there, don't re-derive it). (repo: all of the above)

- [ ] [DESIGN] P1. **Design + build genuine centralization** — the real fix the operator is asking for, beyond
      individual bug patches: a single canonical "resolve the read/write path for dataset X given these partition keys,
      INCLUDING the correct pipeline_mode" function (or confirm `build_path()` + a completed/corrected registry already
      IS this, once the P0 registry fix lands, and the remaining work is migrating callers onto it rather than building
      something new). Cover explicitly: batch, paper, and live code paths for every asset group, both read and write.
      This is the todo that actually closes the recurring-bug-class problem — everything else in this doc is finding and
      patching individual instances of a pattern this todo is meant to make structurally impossible going forward.
      (repo: unified-trading-library, and every consumer once the mechanism is chosen)

- [x] [SCRIPT] P1. **Round 1 (CEFI-scoped) 4-agent audit** — DONE 2026-07-28, findings documented above.
