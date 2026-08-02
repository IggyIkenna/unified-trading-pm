---
doc_type: issue
title:
  "TradFi adapter audit — dead code, silent fallbacks, and one live SSOT contradiction across
  instruments-service/MTDS/execution-service"
summary: >-
  Full-file audit of every adapter/handler module under the 3 codex-named tradfi directories
  (instruments-service/reference_data/adapters/tradfi/, MTDS market_interface/adapters/tradfi/, execution-service
  trade_execution/adapters/ tradfi venues) per adapter-dead-code-and-fallback-ban.md, run via 3 parallel full-repo
  sub-agent audits (2026-07-31). Two big findings: (1) instruments-service's `massive.py` (Massive/Polygon.io
  reference-data adapter) is live, tested, and fully wired end-to-end, directly contradicting the codex SSOT +
  CLAUDE.md's standing claim it was "removed... deleted" 2026-07-19 — the cited removal commits never touched this repo.
  (2) ALL 6 execution-service tradfi venue order-adapters (CME/CBOE/NASDAQ/NYSE/ICE/FX) plus their shared IBKR base are
  registered + tested but structurally unreachable from either production entry point — live tradfi order execution is
  currently impossible end-to-end. Also found: a real bug (silent fabricated `status="cancelled"` on a not-found order)
  inside that same dead execution path; 1 dead-code candidate + 3 unlogged fallback nits in instruments-service; 6
  dead-code findings (4 unregistered macro adapters, 2 unused converter classes) + 1 residual fallback nit in MTDS; a
  cleared duplicate-implementation suspicion (MTDS `_umi_yahoo.py`/ `_umi_fred.py` are a routing layer, not competing
  fetch implementations); no duplicate-implementation violations found anywhere in the 3 directories. 21/29 MTDS files,
  8/11 instruments-service files, and the execution-service duplicate-check are clean.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    tradfi,
    adapter-audit,
    dead-code,
    fallback,
    duplicate-implementation,
    ssot-contradiction,
    execution,
    massive,
    ibkr,
    databento,
  ]
related:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-31
priority: P1
parent_epic: tradfi_master
source: "tradfi_consolidated_native_ao_extract_2026_07_25.md todo 4 — 3 parallel full-repo sub-agent audits, 2026-07-31"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
context_scope:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
---

# TradFi adapter audit — dead code, silent fallbacks, duplicate-implementation check

## Why 2 of these findings are "big findings" (per workspace triage rule)

Per `SUB_AGENT_MANDATORY_RULES.md`/CLAUDE.md: an SSOT-contradiction or cross-repo finding is escalated to the operator
in-chat AND filed here, not buried in an audit report. Both below meet that bar; neither was fixed inline (this is a
read-only audit — the task's own done_definition is a filed finding, not an inline fix).

1. **`massive.py` is live, not deleted.** Two governing docs (codex `tradfi-databento-sourcing-ssot.md`, workspace
   `CLAUDE.md`) assert in the present tense that Massive/Polygon.io was removed as a tradfi source 2026-07-19. It wasn't
   — not in instruments-service. See Finding I-2 below.
2. **Live tradfi order execution is currently impossible.** All 6 execution-service tradfi venue adapters are registered
   and tested but unreachable from both production entry points. See Finding E-1 below. This is direct, new evidence for
   this SAME plan family's still-open todo 1 ("Determine... whether backfill=paper=live wiring is actually proven" —
   `tradfi_consolidated_native_ao_extract_2026_07_25.md`).

## Methodology

3 parallel sub-agents (one per repo), each reading every target file in full (not excerpts), tracing each file's
registration in its repo's adapter factory/dispatch table, tracing actual production callers (CLI wiring, orchestrator,
engine/handler code — not just "is it imported"), reading every `except` block in context, and checking for
duplicate-venue implementations. Full per-file reports available in this session's transcript; this doc consolidates the
findings that require action plus a terse roll-up of the clean verdicts.

---

## A. instruments-service — `instruments_service/reference_data/adapters/tradfi/` (11 files)

**Clean (8 of 11)**: `__init__.py`, `databento/__init__.py`, `databento/_pkg_ref.py`, `databento/symbology.py`,
`futures_factory.py`, `fx.py` — registered in `factory.py`, reached via confirmed live call paths
(`cli → instruments_handler → process_instruments → urdi_reference_provider → factory → adapter → writers`), tested. No
duplicate-implementation violations: Databento/Massive and Databento/TradFiLive both explicitly document which is
primary vs. fallback (see `tradfi_live.py` below) — not silent duplication.

### Finding I-1 — 3 unlogged silent-fallback catch blocks (P3, mechanical)

- `databento/adapter.py::_parse_tick_and_lot` (lines 715-729): both except blocks substitute a hardcoded
  `Decimal("0.01")`/`Decimal("1")` default with **zero logging**.
- `databento/sessions.py::_get_xcal` (lines 149-161): `except Exception: return None`, unlogged.
- `databento/sessions.py::_is_trading_holiday` (lines 164-179): `except Exception: return False`, unlogged.

Inconsistent with the same files' other catch blocks (e.g. `sessions.py::_apply_early_close` logs via `logger.debug`,
`::_compute_utc_hours` logs via `logger.warning`) — an oversight, not house style.
`tradfi_live.py::_read_most_recent_gcs_snapshot` (lines 138-181) has a similar broad catch but DOES log
(`logger.warning`) — satisfies the rule's letter, just worth narrowing later so a persistent permissions bug can't
masquerade as "no data yet" forever. Not filing that one as a separate todo (already logged, lower priority).

### Finding I-2 — `massive.py` is live, tested, fully wired — contradicts codex + CLAUDE.md (P1, BIG FINDING)

The task's own lead asked to determine definitively whether `massive.py` is dead code left over from the 2026-07-19
Massive/Polygon.io removal. It is not — it is a maintained, tested, currently-functional feature:

- `factory.py:167` (`_ADAPTERS["massive"]`), `:219` (`ADAPTER_DATA_SOURCES["massive"]`), `:370`
  (`_DATE_AWARE_TRADFI_ADAPTER_KEYS = frozenset({"databento", "massive"})`), `:450-456`
  (`_resolve_source_aware_adapter_key` — a dedicated function whose sole job is re-pointing Databento-default venues to
  Massive when `source="massive"`), `:470` (explicit `if adapter_key == "massive":` branch).
- `cli/main.py:345-353` documents the `--source massive` flag verbatim as routing CME/NASDAQ/NYSE/CBOE/ICE/FX to
  Massive.
- `cli/instruments_handler.py:94-98,150-154,207-210` fully wires it (adds `MASSIVE_API_KEY` to `ApiKeyReloader`, threads
  `source` through `process_instruments`).
- `engine/urdi_reference_provider.py:273-288` resolves the credential and calls the adapter for real.
- `engine/orchestrator/writers.py:287-295` confirms the write path does **not** gate on vendor source — a
  `--source massive` run completes successfully and writes real fetched data to GCS with no error.
- `tests/unit/test_massive_adapter.py` has currently-passing tests explicitly asserting this is intentional current
  behavior (`test_massive_registered`, `test_source_massive_routes_tradfi_to_massive`, lines 173/177).
- Codex `tradfi-databento-sourcing-ssot.md:44-53` cites `unified-api-contracts@a2beed46` +
  `market-tick-data-service@362a487e` as the removal commits. Verified via `git log` in unified-api-contracts:
  `a2beed46`'s actual scope is removing `"massive"` from the **read-time `SOURCE_PRIORITY` routing dict** — it did NOT
  delete the UAC schemas/normalizers (`normalize_massive_equity/futures/fx`, `MassiveTickersResponse`, etc.) that
  `massive.py` depends on, all still exported today. Neither cited commit touches instruments-service.

**Decision needed** (todo 1 below): either finish the removal in instruments-service to match the stated policy, or
correct the codex SSOT + CLAUDE.md text to scope the 2026-07-19 removal accurately (UAC routing + MTDS only).

### Finding I-3 — `ibkr.py` dead-code candidate, flagged with explicit uncertainty (P2)

`IBKRReferenceDataAdapter` is registered twice (`factory.py:168`, `router.py:236,329`) and has substantial test
coverage, but: (a) UAC's `VENUE_TO_ADAPTER_KEY` (the canonical-venue routing SSOT) has **zero** entries mapping any
venue to adapter key `"ibkr"` — confirmed via direct parse, plus an explicit UAC comment
(`_endpoint_registry_data.py:674`) stating `"ibkr"` is a broker, not a venue, and routes to CME/ICE/CBOE instead; (b) a
full-workspace grep (all ~25 sibling repos, including `ibkr-gateway-infra`) found no external caller of
`IBKRReferenceDataAdapter` or of the two direct-key call forms that could reach it outside this repo's own tests.
Caveat: `"ibkr"` as a venue _string_ is genuinely live elsewhere (execution-service order routing, MTDS's own
`ibkr_adapter.py`) — none of those call into _this_ reference-data class specifically. Static analysis can't rule out an
undiscovered external caller with full certainty; within everything checked, no confirmed production invocation.

---

## B. market-tick-data-service — `market_interface/adapters/tradfi/` (29 files)

**Clean (21 of 29)**: `base_tradfi_adapter.py`, `databento_adapter.py` (facade), `databento_enrichment.py` (the real
live CME-options enrichment path), `databento_equity.py` (an intentionally-documented no-op scaffold — the textbook
correct version of "document why it's kept"), `databento_fetch_executor.py`, `databento_retry.py`,
`databento_symbology.py`, `ecb_adapter.py`, `fred_adapter.py`, `ibkr_adapter.py`, `ofr_adapter.py`, `tardis_adapter.py`
(facade), `tardis_batch_download.py`, `tardis_cefi_shards.py`, `tardis_delisted_symbol_filter.py`,
`tardis_instrument_id_normalization.py`, `tardis_symbol_resolution.py`, `tradfi_shared.py` (explicitly documents "no
silent fallbacks" as its own invariant), `yahoo_finance_adapter.py`. All registered/reached via the confirmed live call
chain `umi_tick_provider.py → _umi_*.py routing → these adapters`, tested.

### Finding M-1 — Yahoo/FRED duplicate-implementation suspicion: CLEARED, not a violation

The task flagged `market_tick_data_service/adapters/_umi_yahoo.py` + `_umi_fred.py` (a sibling top-level directory,
outside the audited `tradfi/` path) as a possible undisclosed duplicate of `yahoo_finance_adapter.py`/`fred_adapter.py`
given the naming resemblance. Traced in full: `_umi_fred.py`/`_umi_yahoo.py` import and call the Part-A classes directly
(`_umi_fred.py:38-41,124,79,139`; `_umi_yahoo.py:37,61,171,257`) — there is exactly one fetch implementation each for
FRED and Yahoo; the `_umi_*` files are a routing/disambiguation layer (Yahoo alone serves 4 distinct canonical venues —
FX/KRX/ICE/a CBOE-treasury slice — and the router decides which venue a request is for and whether Yahoo or Databento
should serve it), extracted out of `umi_tick_provider.py` to stay under the workspace's file-size ratchet (stated in
`_umi_yahoo.py:1`'s own docstring). Not a violation — no todo needed.

### Finding M-2 — 4 unregistered macro adapters, fully implemented + tested but dead (P2)

`baker_hughes_adapter.py`, `cftc_cot_adapter.py`, `eia_adapter.py`, `fear_greed_adapter.py` — each a complete, working,
fail-loud implementation, exported from `tradfi/__init__.py`, but **never** registered in `factory.py`'s
`VENUE_REGISTRY`/`PLANNED_VENUES` (the module's own stated "single source of truth for supported venues",
`factory.py:140`), and no CLI operation or orchestrator call path reaches any of them. Tested only via
`tests/unit/test_macro_adapters.py` / `tests/integration/test_macro_adapters_integration.py` (unit tests alone don't
make a path "live" per the governing rule). `factory.py:149`'s comment `# TradFi (9 venues)` followed by only 7 actual
entries is likely stale drift from the same gap (these 4 would plausibly have brought the count past 9 before being left
unregistered).

### Finding M-3 — 2 unused converter classes producing an orphaned type (P2)

`databento_cme_converter.py::DatabentoCmeConverter` and `databento_opra_converter.py::DatabentoOpraConverter` — both
complete, well-engineered, fail-loud (raise rather than silently default expiry/strike/option-type). Instantiated
**only** in `tests/market_interface/unit/test_book_adapters.py`; zero production imports from any live databento module;
the `CanonicalOptionQuote` type they produce has no other producer/consumer anywhere in the repo. The live CME-options
enrichment path (`databento_enrichment.py::_classify_row`) does its own classification without them.
`docs/tradfi-venue-coverage-matrix.md:26` credits `DatabentoCmeConverter` for "canonicalised greeks/strike," citing a
smoke test that doesn't actually reference this class — that doc row is stale/aspirational.

### Finding M-4 — 2 partial-dead-code cases: generic interface methods superseded by venue-specific batch methods (P3, informational)

`databento_fetch.py`'s `download_batch`/`download_market_data`/`fetch_trades` (+ their only-callers
`_run_batch_download`, `_split_dbn_by_symbol`, `_emit_payg_spend`) and `tardis_csv_transport.py`'s
`download_market_data`/`fetch_trades` are all bound onto their adapter classes but have zero production callers — the
confirmed live paths are exclusively `download_batch_df` (Databento) and `download_batch` (Tardis), both reached via
`umi_tick_provider.py`. Root cause: a generic `fetch_trades()`/`download_market_data()` `BaseTradfiAdapter` interface
contract exists per-adapter, but every real caller uses the venue-specific batch method instead; the generic interface's
only other would-be caller, `market_interface/api.py`, is itself unreached in production. This pattern plausibly extends
beyond tradfi (the generic interface is shared infrastructure) — **not filing a delete-it todo** here since that
requires checking non-tradfi asset groups too (out of this audit's scope); flagging for whoever owns
`market_interface/api.py` broadly. Secondary, currently-moot note: the dead `databento_fetch.py::download_batch`'s own
except block (lines 876-878) would itself be a fail-loud violation if ever reactivated (`return {symbol: [] for ...}` on
`OSError`/`ValueError`/`RuntimeError` instead of raising) — worth fixing if this path is ever revived, not before.

### Finding M-5 — residual unlogged-scope silent fallback (P3, mechanical)

`tardis_bulk_download.py::_download_bulk`'s non-canonical-bucket fallback branch (lines 533-541, "tests/smoke paths
only" per its own comment) has a residual `except Exception: logger.warning(...); return (0, None)` sitting directly
below an already-fixed narrower except for the real transport/HTTP error tuple (lines 520-532, the CF-11 2026-06-10 fix
that made outages raise instead of masquerading as empty). The residual catch-all is narrower in practical impact
(confined to the non-production branch) but still technically swallows any other exception type.

### Directory-naming observation (not a bug — informational, P3)

The 8-file `tardis_*` cluster lives under `tradfi/` and is categorized `"tardis": ("tradfi", TardisAdapter)` in
`factory.py:151`, yet fetches exclusively crypto CEX venues and its own write path lands under `category=cefi` GCS
paths. This is `tradfi/` grouping by data-vendor/transport rather than asset-category — internally consistent and
extensively self-documented, but could surprise a reader expecting `tradfi/` to contain only traditional-finance venues.
Worth a one-line clarifying comment (todo 11).

---

## C. execution-service — tradfi venue files under `trade_execution/adapters/` (7 files + shared base)

**No duplicate-implementation violations.** Unlike the cefi `*_ccxt.py`/`*_native.py` pattern that originally motivated
this codex rule, tradfi uses one shared base (`IbkrTradFiAdapter`) with 6 thin per-venue subclasses differing only in
`venue_name` — a clean design, not a duplicate. No second IBKR/tradfi connectivity file exists anywhere in the repo.

### Finding E-1 — all 6 venue adapters + shared base are dead code (registered + tested, structurally unreachable) (P1, BIG FINDING)

`cme_adapter.py`, `cboe_adapter.py`, `nasdaq_adapter.py`, `nyse_adapter.py`, `ice_adapter.py`, `fx_adapter.py`, and
their shared base `ibkr_tradfi.py` are all registered (`factory.py`'s `TRADFI_VENUES` set, `:210-303` dispatch,
`:506-532` supported-venues list) and individually unit-tested, but two independent, currently-live production entry
gates both structurally exclude every venue string the factory dispatches on:

- **Strategy pre-load path** (`live_execution_handler.py::_validate_instructions`, lines 258-273): rejects any
  instruction whose venue isn't in `SUPPORTED_VENUES = NAUTILUS_SUPPORTED_VENUES | DEFI_VENUES | SPORTS_VENUES`.
  `NAUTILUS_SUPPORTED_VENUES` contains only crypto-CEX names; CME/CBOE/NASDAQ/NYSE/ICE/FX are explicitly enumerated in
  the sibling `NAUTILUS_UNSUPPORTED_VENUES` (`nautilus_compatibility.py:30-42`).
- **Manual/operator HTTP path** (`manual_instruction_api.py::_validate_instruction_request`, line 243): derives
  `_get_supported_venues()` from UAC's `CAPABILITY_DECLARATIONS`. The only tradfi-domain source declared in the UAC
  registry (`_tradfi.py:11-57`) is `"ibkr"` — and `"ibkr"` isn't a `TRADFI_VENUES` key either, so even that would fail
  at the factory's own `ValueError`. This same function backs the `/manual/venues` dropdown the operator UI polls — an
  operator cannot select "CME" as a manual-trade venue today.

No third production caller found (repo-wide grep). TradFi backtesting is unaffected — it runs through a wholly separate
simulated-fill path (GCS Databento data + `SimulatedMatcher`) that never touches this adapters directory.

**This is direct new evidence for this same plan family's still-open todo 1** ("Determine, per MVP cell, whether
backfill=paper=live wiring is actually proven" — `tradfi_consolidated_native_ao_extract_2026_07_25.md`): for the
execution leg specifically, the answer is "not wired, and cannot be reached even if you tried."

**Decision needed** (todo 3 below): bridge the two vocabulary gates to make tradfi execution reachable, or explicitly
document this as intentional not-yet-activated scaffolding (matching the `databento_equity.py` precedent found in
Finding-B above).

### Finding E-2 — `cancel_order()` silently fabricates a successful cancel (P1, real bug — independent of E-1's dead-code status)

`ibkr_tradfi.py::cancel_order()`, real-mode branch (lines 412-434): loops `ib.openTrades()` looking for a matching
`order_id`; if nothing matches (order already filled, wrong id, race condition), the loop falls through with **no**
`break`, **no** `ib.cancelOrder()` call, **no** exception, **no** log — and the method still unconditionally returns
`CanonicalOrder(..., status="cancelled", ...)`. This directly contradicts the adjacent `get_order_status()` in the _same
file_ (lines 439-482), which correctly raises `ValueError(f"Order {order_id} not found")` for the identical not-found
case. No comment anywhere states cancel is meant to be treated as idempotent/best-effort — per the governing rule,
silence here is itself the violation. Currently unreachable per Finding E-1, but this needs fixing regardless (and
especially before E-1 is ever resolved in the "bridge the gates" direction) — this is a scoped, non-judgmental bug fix,
not a design decision.

### Finding E-3 — bare `except BaseException` at debug level in cleanup path (P3, minor)

`ibkr_tradfi.py::close()` (lines 638-643) catches `BaseException` (broader than needed — would also swallow
`asyncio.CancelledError`) at `logger.debug` (invisible in production) with no re-raise, during ticker-unsubscribe
cleanup. Defensible as best-effort shutdown cleanup rather than a trading-correctness fallback (not substituting
stale/degraded trading data) — worth tightening but far lower severity than E-2.

---

## Todos

- [ ] [OPERATOR] P1. **DECISION — instruments-service `massive.py`** (Finding I-2): live, tested, fully wired
      (`factory.py:167,219,370,450-456,470`; `cli/main.py:345-353`; `cli/instruments_handler.py:94-98,150-154,207-210`)
      but codex `tradfi-databento-sourcing-ssot.md:44-53` + workspace CLAUDE.md both assert it was "removed... deleted"
      2026-07-19; the cited removal commits (`unified-api-contracts@a2beed46`, `market-tick-data-service@362a487e`)
      never touched instruments-service. Decide: (a) finish the removal in instruments-service, or (b) correct the codex
      SSOT + CLAUDE.md text to scope the 2026-07-19 removal accurately. Repos: instruments-service, unified-trading-pm.

- [x] ✅ [BACKEND] P1. **Fix silent fabricated cancel-success** (Finding E-2):
      `execution-service/execution_service/trade_execution/adapters/ibkr_tradfi.py::cancel_order()` (lines 412-434) —
      when the target order isn't found in `ib.openTrades()`, it must not unconditionally return `status="cancelled"`.
      Made it fail loud with `raise ValueError(f"Order {order_id} not found")`, matching `get_order_status()`'s existing
      not-found behavior; the success return now only happens inside the matched-order branch (the loop no longer falls
      through past a silent miss). Updated `test_cancel_order_real_not_found` (previously asserted the buggy
      fabricated-success behavior) to assert the raise instead. Repo: execution-service — execution-service@2514bd6b.

- [ ] [OPERATOR] P1. **DECISION — execution-service tradfi order-routing is entirely unreachable** (Finding E-1): all 6
      venue adapters (`cme_adapter.py`, `cboe_adapter.py`, `nasdaq_adapter.py`, `nyse_adapter.py`, `ice_adapter.py`,
      `fx_adapter.py`) + shared `ibkr_tradfi.py` base are registered+tested but excluded by both the
      `NAUTILUS_UNSUPPORTED_VENUES` strategy gate and the UAC-capability-declarations manual-HTTP gate. Cross-refs this
      plan family's open todo 1 (backfill=paper=live wiring proof). Decide: bridge the two vocabulary gates, or document
      as intentional not-yet-activated scaffolding. Repos: execution-service, unified-api-contracts.

- [x] ✅ [BACKEND] P2. **instruments-service `ibkr.py` dead-code candidate** (Finding I-3): registered twice
      (`factory.py:168`, `router.py:236,329`), tested, but zero entries for adapter key `"ibkr"` in UAC's
      `VENUE_TO_ADAPTER_KEY` and no confirmed external caller workspace-wide. Either delete it, or add an explicit
      docstring/comment stating its intended external activation path. Repo: instruments-service. — **2026-07-31 (slot
      6, backend_engineer)**: confirmed unreachable via full call-graph tracing of BOTH registration points (not just a
      class-name grep) — `create_reference_data_adapter()`'s only real caller resolves adapter keys through UAC
      `VENUE_TO_ADAPTER_KEY` (zero "ibkr" entries), and `create_reference_data_adapter_for_source()` has no caller
      anywhere in the workspace outside its own tests. Chose DOCUMENT over DELETE, per this same audit's own
      `databento_equity.py` precedent ("document why it's kept") — substantial, well-tested adapter, and
      `ibkr-gateway-infra` exists workspace-wide suggesting real planned IBKR integration, just not yet wired to
      reference-data. Added a STATUS note to `ibkr.py`'s module docstring (full explanation + activation path) + short
      pointer comments at both registration sites. `instruments-service@1bf5467c`, `quality-gates.sh` PASSED (122s),
      verified on origin.

- [ ] [OPERATOR] P2. **DECISION — 4 unregistered MTDS macro adapters** (Finding M-2): `baker_hughes_adapter.py`,
      `cftc_cot_adapter.py`, `eia_adapter.py`, `fear_greed_adapter.py` are complete + tested but never registered in
      `factory.py`'s `VENUE_REGISTRY`/`PLANNED_VENUES`, no CLI/orchestrator path. Decide: register + wire a CLI
      operation, delete, or (minimum) document scaffold status matching `databento_equity.py`'s precedent. Correct
      `factory.py:149`'s stale `# TradFi (9 venues)` comment (only 7 registered) once decided. Repo:
      market-tick-data-service.

- [ ] [OPERATOR] P2. **DECISION — 2 unused MTDS converter classes** (Finding M-3): `databento_cme_converter.py`'s
      `DatabentoCmeConverter` and `databento_opra_converter.py`'s `DatabentoOpraConverter` produce an orphaned
      `CanonicalOptionQuote` type used only in tests. Decide: wire into the live `databento_enrichment.py` path, delete,
      or document as intentionally unused. Correct the stale credit at `docs/tradfi-venue-coverage-matrix.md:26`
      regardless of direction. Repo: market-tick-data-service.

- [ ] [BACKEND] P3. **3 unlogged silent-fallback catch blocks in instruments-service** (Finding I-1):
      `reference_data/adapters/tradfi/databento/adapter.py::_parse_tick_and_lot` (lines 715-729),
      `reference_data/adapters/tradfi/databento/sessions.py::_get_xcal` (lines 149-161) and `::_is_trading_holiday`
      (lines 164-179) — add logging (`logger.debug`/`warning`) consistent with the other catch blocks in the same files.
      Repo: instruments-service.

- [ ] [BACKEND] P3. **Narrow residual broad except in MTDS `tardis_bulk_download.py::_download_bulk`** (Finding M-5,
      lines 533-541) to the same explicit transport/HTTP error tuple used one block above (lines 520-532, the CF-11 fix)
      instead of a bare `except Exception`. Repo: market-tick-data-service.

- [ ] [BACKEND] P3. **Narrow `ibkr_tradfi.py::close()`'s bare `except BaseException`** (Finding E-3, lines 638-643) to a
      specific exception type and bump the log level from `debug` to `warning`. Repo: execution-service.

- [ ] [BACKEND] P3. **Update MTDS `market_interface/adapters/tradfi/__init__.py`'s module docstring** (lines 1-16) to
      mention all 10 exported adapter/converter classes (currently narrates only 6 of 10) once todos for M-2/M-3 above
      are resolved — the stale docstring is corroborating evidence for those findings. Repo: market-tick-data-service.

- [ ] [BACKEND] P3. **Add a one-line clarifying comment in MTDS `market_interface/factory.py`** near line 151's
      `"tardis": ("tradfi", TardisAdapter)` registration, noting `tradfi/` groups by data-vendor/transport (Tardis is a
      market-data vendor) rather than by asset-category (Tardis's write path lands under `category=cefi`) — see the
      directory-naming observation in Finding-B. Repo: market-tick-data-service.

## Reconciliation

Once this doc lands, `tradfi_consolidated_native_ao_extract_2026_07_25.md`'s own todo 4 checkbox is flipped by its
companion finalize plan (`tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md`), not by this doc directly — per
that plan's own stated reconciliation pattern.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
