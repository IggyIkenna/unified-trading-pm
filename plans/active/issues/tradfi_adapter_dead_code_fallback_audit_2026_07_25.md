---
doc_type: issue
title:
  TradFi adapter audit — dead-code, runtime-fallback & duplicate-implementation findings across 3 directories (47 files)
summary: >-
  Audit of every adapter/handler module under the 3 codex-named tradfi directories
  (instruments-service/reference_data/adapters/tradfi/, market-tick-data-service/market_interface/adapters/tradfi/,
  execution-service/trade_execution/adapters/ tradfi-scoped files) against
  `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`'s 3-rule ban (dead code / silent runtime fallback /
  undocumented duplicate implementation). 3 parallel sub-agents traced every file's registration + live reachability
  through each repo's own factory/dispatch table, not just import presence. Net: 14 findings across the 3 directories (1
  live silent-fallback feeding the honest-absence gate, 8 dead-code instances, 1 misplaced 8-file cluster, 3 minor
  consistency gaps, 1 duplicate pair found just outside the named scope), plus a documentation-accuracy gap in this
  workspace's own CLAUDE.md. Most of the 47 files (26) are clean.
status: open
nature: issue
asset_group: [tradfi]
stage: [data, execution]
repos: [instruments-service, market-tick-data-service, execution-service, unified-trading-pm]
scope: [engineer]
tags: [tradfi, adapter-audit, dead-code, fallback-ban, duplicate-implementation, close-out, ao-dispatch]
related:
  [
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
  ]
created: 2026-07-31
priority: P1
parent_epic: tradfi_master
source: "[BACKEND] slot 11, tradfi_consolidated_native_ao_extract-004 — 3 parallel sub-agent audit, one per directory"
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# TradFi adapter audit — dead-code, runtime-fallback & duplicate-implementation findings (2026-07-31)

## What I found

Methodology (all 3 sub-agents): trace every file's registration through the repo's own adapter factory/dispatch table,
then confirm actual production reachability by grepping the WHOLE repo (not just the tradfi/ dir) for every class/method
name — per this workspace's own "grep-then-READ, not grep-then-conclude" rule, a 0-hit grep alone was never treated as
proof of dead code without also reading the candidate dynamic-dispatch consumer.

### Directory 1 — `instruments-service/instruments_service/reference_data/adapters/tradfi/` (11 files)

**5 findings, 6 files clean** (`__init__.py`, `databento/__init__.py`, `databento/_pkg_ref.py`,
`databento/symbology.py`, `futures_factory.py`, `fx.py`).

1. **`databento/adapter.py:294-351`, `get_canonical_futures_contracts`** — triple-hit (dead-code + runtime-fallback +
   duplicate). Not part of `BaseReferenceDataAdapter`'s abstract interface; zero non-test callers repo-wide (only
   `tests/unit/test_tradfi_adapters_boost.py`); the live production path for the same job is
   `futures_factory.build_futures_contracts()` (called from `engine/orchestrator/writers.py:471`), which is materially
   more correct (real physical-delivery vs. cash-settled derivation) AND properly logs failures
   (`except Exception as exc: logger.warning(...)` + a `skipped` counter). The dead method instead wraps its entire body
   in `with contextlib.suppress(Exception):` (line 332) — zero logging, not even DEBUG. Neither file states these are
   two parallel implementations or which is authoritative.
2. **`databento/adapter.py:179-181,608-630`, `_create_fx_spot_records`** — dead-code, medium confidence. Only reachable
   via `venue_filter=None`, which no confirmed-live construction site passes (traced all 3: `factory.py:477` always
   passes a concrete venue; `router.py:274`'s entry point `create_reference_data_adapter_for_source` itself has zero
   production callers; `tradfi_live.py:127` always passes a concrete venue). Duplicates `fx.py`'s live
   `FxReferenceDataAdapter.get_instruments()` (same `FX_SPOT_PAIRS` source, independently re-coded) with no
   cross-reference.
3. **`databento/sessions.py`, `_get_xcal()` (:149-161) and `_is_trading_holiday()` (:164-179)** — runtime-fallback,
   **fully silent** (`except Exception as _exc: return None` / `return False`, zero log calls of any kind, not even
   DEBUG). These feed every `InstrumentRecord.is_trading_day`/session field and `non_trading_day_reason()`, which per
   the module's own docstring is consumed by the orchestrator's `ManifestWriter.record_expected_empty(reason=...)`
   honest-absence gate. The sibling function `_compute_utc_hours()` in the SAME file (:279-349) wraps an equivalent
   computation with `logger.warning(...)` — the file is internally inconsistent about failure visibility. **This is the
   highest-operational-risk finding in this doc**: unlike the other findings, this fallback runs live today on every
   trading-day check, and a silent `exchange_calendars` mapping/version regression here would misclassify honest-absence
   reasons with zero trace to debug it by.
4. **`tradfi_live.py`, `_read_most_recent_gcs_snapshot()` (:138-181)** — the class's overall
   GCS-first/Databento-fallback design is a legitimate, documented, logged fallback (fine per the ban's carve-out). The
   narrower issue: the `except Exception as exc: logger.warning(...)` at line 179 wraps the entire GCS access + parquet
   parse, so a genuine infra failure (auth broken, bucket unreachable, corrupt parquet) is indistinguishable from "no
   snapshot captured yet" — both silently fall through to Databento. Unlike sibling adapters in the same directory
   (`databento/adapter.py:442-462`, `massive.py:217-237`), this except does not route through `classify_venue_error()` +
   `log_event("ADAPTER_FETCH_FAILED", ...)`.
5. **`ibkr.py`, `_fetch_details_for_symbol()` (:353-373)** — minor. Already documented + logged at WARNING (clears the
   ban's minimum bar, not a violation) — flagged only because it doesn't route through the same
   `classify_venue_error`/`log_event` pattern its sibling live vendor adapters use, so IBKR per-symbol failures are
   invisible to whatever consumes that structured event stream.

**`massive.py` lead (from workspace CLAUDE.md's "Massive removed as tradfi source 2026-07-19") — resolved NOT dead.**
Fully live: registered in `factory.py` (`_ADAPTERS["massive"]`, source-aware routing), CLI-reachable via a documented
`--source massive` flag, credential-routed, UAC-backed, tested. The 2026-07-19 removal (cited commits UAC `a2beed46` +
MTDS `362a487e`) was scoped precisely to MTDS's market-data/OHLCV sourcing layer — it never touched
instruments-service's reference-data layer, where `massive.py` is a documented, stated Databento-fallback source for the
instrument catalog. **Doc-accuracy gap, not a code violation**: workspace CLAUDE.md's "do NOT reference" line reads as
blanket and would mislead a future agent into deleting or refusing to touch this genuinely live file — see Todo 14.
Databento-vs-Massive dual sourcing itself is the POSITIVE example of rule 3 done right (explicitly prioritized +
reasoned in both files' docstrings and `factory.py:450-456`), not a violation.

### Directory 2 — `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/` (29 files)

**17 files carry findings (9 dead-code + 8 misplaced as one cluster) + 1 additional minor note, 12 files clean**
(`__init__.py`, `base_tradfi_adapter.py`, `tradfi_shared.py`, `fred_adapter.py`, `yahoo_finance_adapter.py`, the
`databento_adapter.py`/`databento_fetch.py`/`databento_fetch_executor.py`/`databento_retry.py`/
`databento_symbology.py`/`databento_enrichment.py` composed-facade cluster, and `databento_equity.py` — the one file
that looks unreached but is properly self-documented as an MVP-excluded scaffold with a dated TODO, meeting the ban's
own carve-out).

6. **Dead-code, 4 zero-reference macro adapters**: `baker_hughes_adapter.py`, `cftc_cot_adapter.py`, `eia_adapter.py`,
   `fear_greed_adapter.py`. None appear in `factory.py`'s `VENUE_REGISTRY` (7 real tradfi entries) or in
   `PLANNED_VENUES` (the dict that explicitly documents not-yet-wired adapters). Zero references repo-wide outside their
   own files, `__init__.py` re-exports, and 2 test files. UAC does carry capability declarations for all 4 (registered
   "somewhere," per rule 1's own definition of the trap) but MTDS never reaches them.
7. **Dead-code, 2 unwired options converters**: `databento_cme_converter.py` (`DatabentoCmeConverter`),
   `databento_opra_converter.py` (`DatabentoOpraConverter`). Absent from `databento_adapter.py`'s own
   docstring-enumerated composition; zero non-test references (`tests/market_interface/unit/test_book_adapters.py`
   only); their output type `CanonicalOptionQuote` appears nowhere in the live fetch path — TradFi options aren't
   converted by anything live today. Unlike `databento_equity.py`, neither has any TODO/scaffold self-documentation.
8. **Dead-code, `ecb_adapter.py` + `ofr_adapter.py`**: registered in `VENUE_REGISTRY` but NOT in UAC's
   `all_databento_venues`/tradfi venue set. `umi_tick_provider.fetch_tick_data_for_venue()`'s full dispatch chain (read
   end-to-end) has no branch for either — a call falls through to the final CeFi-only `get_market_adapter()` fallback,
   raises `ValueError`, gets caught, logs a warning, and silently returns an empty DataFrame. Zero references outside
   tests.
9. **Dead-code (nuanced), `ibkr_adapter.py`**: registered, self-documents WHY it can't run headless ("requires running
   TWS/IB Gateway"), but not WHO calls it — zero references anywhere outside tests/`__init__.py`/`factory.py`. Its
   method shape (`connect`/`fetch_ticker`/live session) is structurally unlike every other tradfi adapter's
   `download_batch` pattern, plausibly built for a not-yet-existing live consumer.
10. **Misplaced-code, the `tardis_adapter.py` + 7-file cluster** (`tardis_batch_download.py`, `tardis_bulk_download.py`,
    `tardis_cefi_shards.py`, `tardis_csv_transport.py`, `tardis_delisted_symbol_filter.py`,
    `tardis_instrument_id_normalization.py`, `tardis_symbol_resolution.py`) — **CONFIRMED misplaced, not dead, not a
    functional duplicate** of the separate `adapters/cefi/tardis_shared.py` home. Evidence: `umi_tick_provider.py`'s own
    module docstring states "Routing: CeFi→Tardis... TradFi→Databento"; `_route_tardis()` is called only from the CEFI
    dispatch branch; `tardis_batch_download.py` writes shards to `category=cefi/` canonical paths; `tardis_adapter.py`
    itself imports its normalization helpers FROM `..cefi.tardis_shared`, not the reverse. All 8 files are genuinely
    live (co-referenced by `tardis_adapter.py`'s own method-body split, dated "codex file-size ratchet, 2026-06-11").
    `tardis_cefi_shards.py`'s cefi-named-file-in-tradfi-folder appearance is explained — a mechanical size-driven split
    that stayed next to its parent module, which is itself the one that's misplaced. `VENUE_REGISTRY`'s own
    `"tardis": ("tradfi", TardisAdapter)` category tag conflicts with the venue's actual live CEFI routing.
11. **Minor, `tardis_bulk_download.py:533`**: a broad `except Exception` (test/smoke-only fallback branch, explicitly
    commented as such) sits 12 lines below a narrower, already-fixed handler citing the 2026-06-10 CF-11 fix for "an
    outage masquerading as an empty bulk shard" — the broad catch-all reintroduces that same risk class for any other
    exception type, though only in the non-production branch (`canonical_bucket` falsy).

### Directory 3 — `execution-service/execution_service/trade_execution/adapters/` (7 tradfi-scoped files)

**1 finding, 6 files clean** (`cboe_adapter.py`, `cme_adapter.py`, `fx_adapter.py`, `ice_adapter.py`,
`nasdaq_adapter.py`, `nyse_adapter.py` — each a thin, tested, factory-registered subclass of `ibkr_tradfi.py`'s shared
`BaseCLOBAdapter`-derived base, no try/except, no duplication; the base+subclass split is explicitly documented as
intentional broker-routing design in UAC's `broker_routes.py`).

12. **Dead-code, `ibkr_tradfi.py:95-135,151-204,622-631`**: `subscribe_market_data`, `subscribe_instruments`,
    `_poll_price`, `get_price`, `pump`, `health_check` — none are part of `BaseCLOBAdapter`'s abstract interface
    (confirmed by reading it in full); unique to this file; zero production callers anywhere in execution-service (only
    their own dedicated test file). By contrast the interface methods that ARE used (`place_order`, `get_order_status`,
    etc.) are demonstrably reached via `order_adapter.py`/`orphan_monitor.py`/the live matching engine. No docstring
    states a feature-flag/activation-path reason these are kept. **Secondary, lower-severity, same file**: `close()`
    (:633-646) catches bare `BaseException` (broader than `Exception`, would also swallow
    `KeyboardInterrupt`/`asyncio.CancelledError`) around cleanup of the also-dead `_subscribed_tickers` — real-world
    risk is near-zero today since it's only reached via the dead subscribe path, but worth narrowing while touching this
    file.

### Out-of-scope side-observations (surfaced incidentally by the sub-agents, NOT part of the 3 named directories — flagged per this workspace's findings-triage convention, not fixed inline)

13. **`execution_service/instruments/factory_tradfi.py` vs `tradfi_creator.py`** — a genuine, live instance of the same
    duplicate-implementation pattern this codex rule targets, found while grepping execution-service for "tradfi," but
    in `execution_service/instruments/` (instrument/reference-data creation), not `trade_execution/adapters/` (this
    audit's assigned directory). Both `create_tradfi_from_config` functions are near-identical (diffed: same structure,
    same param-resolution logic) AND **both are live-imported by different callers**
    (`factory_tradfi.py`→`instruments/factory.py`+`factory_cefi_defi.py`; `tradfi_creator.py`→`config_creator.py`+
    `gcs_creator.py`). `tradfi_creator.py:132` even comments "See sibling factory_tradfi.py for context" — acknowledging
    the sibling without stating which is authoritative. This is a live duplicate carrying real silent-divergence risk
    (an edit to one won't propagate to the other), outside the codex doc's own enumerated path list.
14. **Workspace CLAUDE.md doc-accuracy gap** — see the `massive.py` paragraph above. The "removed as tradfi source
    2026-07-19 — do NOT reference" line conflates MTDS's real market-data-layer removal with instruments-service's
    still-live reference-data layer.

## Why it matters

This is exactly the gap the codex SSOT was written to close: none of `vulture` (blind to referenced-but-unscheduled
code), `check_no_fallback_imports.py` (import-time only, not runtime catch-and-degrade), or the UTL/UAC reuse audit
(service-vs-library, not adapter-vs-adapter) would have caught any of the 14 findings above. Finding 3
(`databento/sessions.py`'s fully-silent trading-day fallback) is the one with live, present-tense operational risk — it
runs on every tradfi trading-day check today and feeds the honest-absence gate this workspace treats as a hard-rule
correctness heartbeat, with zero log trail if it misfires. Findings 1, 2, 6-10, and 12 are dead code sitting in
production-adjacent directories — not actively wrong today, but exactly the shape (registered, plausible-looking,
untested-in-anger) that produces a silent landmine the next time someone extends tradfi coverage and assumes a
registered adapter is a live one. Finding 10 (the Tardis cluster) is a real organizational hazard: `VENUE_REGISTRY`
itself asserts a category (`tradfi`) that contradicts the code's actual live routing (cefi), which is precisely the kind
of registry/reality drift this whole rule exists to prevent.

## Recommended decision

Dispatch the todos below (each independently scoped, files/repos named, no todo collides with another on the same file).
Once they land, `tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md` reconciles
`tradfi_consolidated_closeout_2026_07_18.md`'s own checkbox for this audit todo, citing this doc — per this batch's
established pattern (source plan's own text: "do not write into the closeout plan directly — this batch's finalize plan
reconciles the closeout's own checkbox once this lands").

## Todos

- [ ] [BACKEND] P1. Add `logger.warning(...)` (matching the sibling `_compute_utc_hours()` pattern in the same file) to
      the silent `except` blocks in instruments-service `reference_data/adapters/tradfi/databento/sessions.py`'s
      `_get_xcal()` (:149-161) and `_is_trading_holiday()` (:164-179) — currently zero logging on a live path feeding
      the honest-absence gate. (repo: instruments-service)
- [ ] [BACKEND] P2. Delete `get_canonical_futures_contracts` (dead + silently-swallowed-exceptions + undocumented
      duplicate of the live `futures_factory.build_futures_contracts()`) from instruments-service
      `reference_data/adapters/tradfi/databento/adapter.py:294-351`, plus its now-unused test class in
      `tests/unit/test_tradfi_adapters_boost.py`. (repo: instruments-service)
- [ ] [BACKEND] P3. Resolve `_create_fx_spot_records()` in instruments-service
      `reference_data/adapters/tradfi/databento/adapter.py:179-181,608-630` — confirm `router.py`'s
      `create_reference_data_adapter_for_source` is genuinely unreached in production, then either delete this method
      (duplicates `fx.py`'s live `FxReferenceDataAdapter`) or document why it's intentionally kept. (repo:
      instruments-service)
- [ ] [BACKEND] P3. Narrow + classify the except in instruments-service
      `reference_data/adapters/tradfi/tradfi_live.py`'s `_read_most_recent_gcs_snapshot()` (:138-181) — distinguish "no
      snapshot found" (benign) from a genuine GCS/parse failure, routing the latter through `classify_venue_error()` +
      `log_event("ADAPTER_FETCH_FAILED", ...)` like its sibling adapters (`databento/adapter.py`, `massive.py`). (repo:
      instruments-service)
- [ ] [BACKEND] P3. Optional consistency fix: route instruments-service `reference_data/adapters/tradfi/ibkr.py`'s
      `_fetch_details_for_symbol()` (:353-373) except through
      `classify_venue_error()`/`log_event("ADAPTER_FETCH_FAILED", ...)` like its sibling live vendor adapters in the
      same directory (currently documented + logged at WARNING, not a violation, just inconsistent instrumentation).
      (repo: instruments-service)
- [ ] [BACKEND] P3. Delete or document-with-activation-path 4 zero-reference macro adapters in MTDS
      `market_interface/adapters/tradfi/`: `baker_hughes_adapter.py`, `cftc_cot_adapter.py`, `eia_adapter.py`,
      `fear_greed_adapter.py` (none in `factory.py`'s `VENUE_REGISTRY` or `PLANNED_VENUES`, zero non-test references
      repo-wide). (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Delete or document-as-scaffold (matching `databento_equity.py`'s dated-TODO pattern) 2 unwired
      options converters in MTDS `market_interface/adapters/tradfi/`: `databento_cme_converter.py`,
      `databento_opra_converter.py` (test-only references, no live caller, `CanonicalOptionQuote` unreached in
      production). (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Delete or wire a real dispatch branch in `umi_tick_provider.fetch_tick_data_for_venue()` for MTDS
      `market_interface/adapters/tradfi/ecb_adapter.py` + `ofr_adapter.py` — currently registered in `VENUE_REGISTRY`
      but outside the live tradfi venue set, so any call silently falls through to a CeFi-only fallback that
      `ValueError`s and returns an empty DataFrame. (repo: market-tick-data-service)
- [ ] [BACKEND] P3. Add a stated caller/activation path to MTDS `market_interface/adapters/tradfi/ibkr_adapter.py`
      (documents WHY it needs a running TWS/IB Gateway but not WHO invokes it; zero references outside tests) — or
      delete pending that consumer. (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Relocate the `tardis_adapter.py` + 7-file companion cluster
      (`tardis_batch_download.py`/`tardis_bulk_download.py`/`tardis_cefi_shards.py`/`tardis_csv_transport.py`/
      `tardis_delisted_symbol_filter.py`/`tardis_instrument_id_normalization.py`/`tardis_symbol_resolution.py`) from
      MTDS `market_interface/adapters/tradfi/` to `market_interface/adapters/cefi/` — confirmed live CEFI-purpose code
      (writes `category=cefi` shards; is the actual CEFI Tardis vendor per `umi_tick_provider.py`'s own docstring).
      Update `factory.py`'s `VENUE_REGISTRY` entry `"tardis": ("tradfi", TardisAdapter)` to the correct category in the
      same change. (repo: market-tick-data-service)
- [ ] [BACKEND] P3. Tighten the broad `except Exception` in MTDS
      `market_interface/adapters/tradfi/tardis_bulk_download.py:533` (test/smoke-only fallback branch) to match the
      narrower, already-fixed handler 12 lines above it (the 2026-06-10 CF-11 fix for "an outage masquerading as an
      empty bulk shard"). (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Delete or document-with-activation-path 5 dead methods in execution-service
      `trade_execution/adapters/ibkr_tradfi.py:95-135,151-204,622-631` (`subscribe_market_data`,
      `subscribe_instruments`, `_poll_price`, `get_price`, `pump`, `health_check` — zero production callers, only their
      own dedicated tests). While touching this file, narrow the bare `except BaseException` in `close()` (:639-643) to
      `except Exception`. (repo: execution-service)
- [ ] [BACKEND] P2. Investigate `execution_service/instruments/factory_tradfi.py` vs
      `execution_service/instruments/tradfi_creator.py` (near-identical duplicate `create_tradfi_from_config`
      implementations, BOTH live-imported by different callers today, no stated authoritative one — found just outside
      this audit's named-directory scope but the same codex rule applies) — state which is authoritative and
      consolidate, or document why both must remain live. (repo: execution-service)
- [ ] [DOCS] P3. Fix workspace CLAUDE.md's "Massive formerly-Polygon.io, removed as tradfi source 2026-07-19 — do NOT
      reference" line (both the root copy and the per-tab `cursor-configs/CLAUDE.md` copy) — it conflates the real
      2026-07-19 MTDS market-data-layer removal (UAC `a2beed46` + MTDS `362a487e`) with instruments-service's
      reference-data layer, where `instruments-service/instruments_service/reference_data/adapters/tradfi/massive.py` is
      still live, tested, and CLI-documented (`--source massive`) as a stated Databento-fallback source. Scope the
      wording explicitly to MTDS/OHLCV so a future agent doesn't wrongly delete or refuse to touch the live file. (repo:
      unified-trading-pm)
