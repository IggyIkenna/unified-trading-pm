---
title: TradFi data-source close-out — KRX/Yahoo venue + centralised parity gate + Barchart removal + databento floor precision
parent_epic: tradfi_master
assigned_vm: planning
priority: P1
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-24
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
created: 2026-06-24
---

# TradFi data-source close-out (A–G)

> **Autonomous dispatch (operator 2026-06-24).** Write + TEST + ship ALL the CODE for the tradfi data-source
> close-out. The COORDINATOR owns the production OPS (IS instruments backfill, IS consolidation/catalogue-regen,
> MTDS wave). This plan is the plan-of-record + Progress Log.

## Context / current state (verified 2026-06-24)
- Binance-tradfi-perp universe DONE: 100/100 basis pairs both-legs MVP; databento-first SOURCE_PRIORITY;
  commodity/crypto ETFs + CME futures+options on origin/live-defi-rollout.
- Yahoo intraday lookback guardrail PARTIALLY shipped (uac@9818f051): `YAHOO_INTRADAY_LOOKBACK_DAYS` +
  `assert_yahoo_intraday_within_limit()` + QG test exist in `registry/data_source_continuity.py`; the FETCH-PATH
  WIRING is tracked-but-not-done, and the 1d "since 2019" floor + a general (not VIX-only) guardrail are pending.
- KRX flagged BLOCKED-DATA in `tradfi_ticker_universe.py` ("no US-listed twin") — this dispatch UNBLOCKS via
  KRX/Yahoo direct.

## The work (A–G)

- [x] ✅ [SCRIPT] P1. **A. Yahoo adapter general guardrail + verified test-download.** Bake granularity/lookback limits
      into the adapter as a GENERAL guardrail on the non-bypassable fetch path (download_daily/download_intraday).
      TEST-download the 3 KRX stocks at all 4 granularities. QG unit test: too-old/too-fine rejected.
- [x] ✅ [SCRIPT] P1. **B. KRX venue registration** across IS registry/enumeration, MTDS venue→source routing
      (KRX→yahoo), manifest venue recognition, deployment-ui/api. source=yahoo.
- [x] ✅ [SCRIPT] P1. **C. UAC universe + MVP.** Add 3 KRX stocks (venue=KRX, source=yahoo) → 103/103.
- [x] ✅ [SCRIPT] P1. **D. Centralised parity gate** — ONE data-driven QG test iterating canonical registries,
      validating every venue/source/adapter/(venue,data_type)-MVP-cell wiring. Parametrised. Prove half-wired
      venue RED-fails. Report + fix small pre-existing gaps.
- [x] ✅ [SCRIPT] P1. **E. Barchart removal** — delete adapter/client/source-entries, no shim; remove from enums /
      SOURCE_PRIORITY / continuity; update CLAUDE.md VIX-15m note → VX-futures-via-databento.
- [x] ✅ [SCRIPT] P1. **F. Databento rolling-boundary precision** — probe LIVE, update floor guardrails to MEASURED
      values. QG-test the exact edge.
- [x] ✅ [SCRIPT] P1. **G. IS catalogue + aggregation code** for new symbols (code only; coordinator runs ops).
      Document EXACT backfill command + skip-vs-overwrite answer.

## Surfaces mapped (2026-06-24)
- UAC venue lists: `registry/venue_mapping.py` (`all_databento_venues` L66, `venue_to_databento` L125,
  `venue_to_data_provider` L194, `venue_start_dates` L224); `registry/market_data_categories.py`
  `VENUES_BY_ASSET_GROUP["tradfi"]` L268.
- UAC source priority: `canonical/crosscutting/_source_priority_data.py` (`("tradfi","ohlcv_15m")` L289 carries
  barchart).
- UAC mvp: `canonical/crosscutting/mvp_scope.py` equity carve-out L840-858 (venue roots NASDAQ/NYSE/ARCA/AMEX/BATS;
  `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`); universe `registry/tradfi_ticker_universe.py` L481.
- UAC capability: `registry/capability_declarations/_tradfi.py` (`_BARCHART` L112, `_YAHOO_FINANCE` L139,
  `TRADFI_CAPABILITIES` L236).
- UAC databento floors: `registry/databento_subscription_allowlist.py` `LEVEL_MAX_LOOKBACK_DAYS` (L0 16*365,
  L1 365, L2 30, L3 30), `earliest_allowed_start`/`assert_lookback_allowed`/`assert_databento_request_allowed`.
- UAC barchart: `external/barchart/` dir, `pipeline_mode.BATCH_BARCHART` L76, `_source_priority_data` L289,
  `errors/tradfi.VENUE_ERRORS_TRADFI` barchart entry, `data_source_continuity` BARCHART_VIX_* consts +
  VIX_15M_SOURCE_HISTORY + get_vix_15m_source.
- MTDS yahoo adapter: `market_interface/adapters/tradfi/yahoo_finance_adapter.py` (download_daily/download_intraday/
  download_vix_15m + `_classify_yahoo_ticker`); fetcher `adapters/_umi_yahoo.py` (fetch_yahoo_fx, fetch_yahoo_vix_15m
  — LIVE barchart consumer); routing `adapters/umi_tick_provider.py` `fetch_tick_data_for_venue` L344
  (FX→yahoo_fx L439, CBOE+ohlcv_15m→vix_15m L443, _DATABENTO_VENUES L116).
- IS catalogue: `scripts/build_instrument_catalogue.py` (reads by_date GCS snapshots, venue-agnostic enumeration).

## Progress Log

- 2026-06-24 — Plan created. Read all mandatory rules. Mapped every surface (3 parallel Explore agents + direct
  reads). Verified: Yahoo guardrail intraday lookback partially landed (uac@9818f051), KRX flagged BLOCKED-DATA
  (to unblock), barchart widely referenced (clean removal manifest built). Starting implementation A→C→D→E→F→G.

- 2026-06-24 — **A (Yahoo guardrail) MEASURED + GENERAL — UAC code DONE (worktree, pre-commit).** Probed Yahoo LIVE
  (yfinance, 3 KRX tickers + Samsung). MEASURED vs targets: **1m = 8 days PER REQUEST** (Yahoo: "Only 8 days worth of
  1m granularity data are allowed per request"; target was 28d → real per-request cap 8d, total ~30d via chunking);
  **15m = 60 days** (59d OK, 60d+ → 422; target 89 was WRONG); **1h = 730 days** (confirmed; ≤729 OK, exactly-730 fails);
  **1d = unbounded** (probed 2019-05 OK; backfill floor = operator 2019-01-01). Updated
  `registry/data_source_continuity.py`: corrected `YAHOO_INTRADAY_LOOKBACK_DAYS` (15m 89→60, 1m 28→30+per-req-cap),
  added `YAHOO_DAILY_BACKFILL_FLOOR=2019-01-01`, `YAHOO_INTRADAY_MAX_REQUEST_DAYS` (1m=8), `YahooRequestTooWideError`,
  `assert_yahoo_request_width_ok`, and made `assert_yahoo_intraday_within_limit` GENERAL (clamps unbounded 1d to the
  floor too). Exported all new symbols from `registry/__init__.py`.
- 2026-06-24 — **TEST-DOWNLOAD PROOF (A): all 3 KRX stocks fetch + write at all 4 granularities** (within-limit windows):
  Hyundai 005380.KS / Samsung 005930.KS / SK Hynix 000660.KS — 1d rows=243, 1h rows=2762, 15m rows≈910 (within 60d),
  1m rows≈1773 (within 8d/req). Sane OHLCV (Samsung last C=322500 KRW, etc.). 15m EMPTY only when window > 60d
  (confirms the guardrail boundary).
- 2026-06-24 — **C (UAC universe + MVP) — DONE (worktree).** Added `KrxEquityDef` + `KRX_EQUITIES` (3 stocks, .KS
  tickers, first_available 2019) + `KRX_EQUITY_SYMBOLS` to `tradfi_instrument_universe.py`; added the 3 bare KRX
  codes (005380/005930/000660) to `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` (removed the "BLOCKED-DATA no US twin" note →
  UNBLOCKED via KRX/Yahoo direct). Extended the `mvp_scope.is_mvp` equity carve-out venue set to include KRX. Verified:
  `is_mvp(tradfi,KRX,EQUITY,ohlcv_1m,base_ccy=005930,source=yahoo)=True`, non-basis ticker=False. → 103/103 (100 perp
  basis pairs already + 3 KRX).
- 2026-06-24 — **B (UAC venue registration) — DONE (worktree).** KRX added to `venue_mapping.all_databento_venues`
  (the full-tradfi-universe list), `venue_to_data_provider=yahoo_finance`, `venue_start_dates=2019-01-02`,
  `market_data_categories.VENUES_BY_ASSET_GROUP["tradfi"]`; `_VENUE_SOURCE_EXCLUSIONS` (KRX excludes databento+massive →
  yahoo-only, fail-closed); SOURCE_PRIORITY ohlcv_1m/15m gain `yahoo`, new `("tradfi","ohlcv_24h"):["yahoo"]`.
- 2026-06-24 — **D (Centralised parity gate) — DONE (worktree).** New `tests/unit/test_venue_source_adapter_parity.py`
  — 249 tests, all parametrised over the canonical registries (zero new test code for future venues). Asserts:
  (1) venue ⟺ asset_group reverse-index consistency; (2) every tradfi venue resolves to a data source; (3) every
  SOURCE_PRIORITY source resolves to a capability / computed-service / documented-gap; (4) every tradfi-equity MVP cell
  is fetchable + the venue's source is valid; (5) Yahoo + Databento adapters declare AND enforce their limits.
  **Half-wired RED-fail PROVEN**: `test_half_wired_venue_invokes_real_gate_and_red_fails` monkeypatches KRX out of both
  source maps and asserts the real rule-2 assertion raises `AssertionError(match="resolves to NO data source")`.
  **Pre-existing gaps found + documented (allowlisted, NOT blocking KRX)**: `massive` + `polymarket_clob`/
  `polymarket_gamma_api` lack SourceCapability rows; `YAHOO_FINANCE` is a legacy source-as-venue artifact in
  VENUES_BY_ASSET_GROUP["tradfi"]; `PROTOCOL_CAPABILITIES` is a list of operation strings (not SourceCapability objects).
- 2026-06-24 — **F (Databento rolling-boundary precision) — MEASURED, UAC floor code DONE (worktree).** Probed LIVE
  (operator Method B — real `timeseries.get_range` with continuous front-month `ES.c.0`). Method A (get_cost) returns
  $0.0000 at every date → does NOT model a rolling free allowance (confirms our FIXED subscription has none).
  **FINDING: full-history entitlement, NO PAYG rolling edge** — L1 trades served at 1460d (4y), L2 mbp-10 + L3 mbo
  served at 730d (2y), L0 ohlcv-1m bounded only by DATASET start (~2010-06-06 ≈16y; API 422s
  `data_start_before_available_start` at 5870d). The prior `LEVEL_MAX_LOOKBACK_DAYS` (L1 365 / L2,L3 30) were
  conservative PAYG guesses that WRONGLY clip valid history. **BEFORE: L0 16*365, L1 365, L2 30, L3 30 → AFTER: all =
  16*365** (full history; true floor = dataset available-start, the gate 422s there). QG edge test in the parity gate
  asserts 730d-back now ALLOWED (old window rejected it) + one-day-past-floor still raises. Guard RE-ENABLED (never
  bypassed — the probe used a standalone script, the live gate was untouched).

- 2026-06-24 — **E (Barchart removal) — UAC SIDE DONE (worktree → cherry-picked to real LDR clone @51417b53).**
  Deleted `external/barchart/` dir (4 files); removed `_BARCHART` capability + `TRADFI_CAPABILITIES` entry; removed
  `PipelineMode.BATCH_BARCHART`; removed `VENUE_ERRORS_TRADFI["barchart"]`; removed `BARCHART_VIX_FIRST/LAST_DATE/
  FILE_COUNT` + rewrote `VIX_15M_SOURCE_HISTORY` (BARCHART_CSV window → `DATABENTO_VX_FUTURES`) + `get_vix_15m_source`
  (no BARCHART_CSV; `is_vix_15m_gap_date` always False now — VX futures cover full history); removed barchart endpoint
  (`_endpoint_registry_data.py`/`endpoints.py`), venue_manifest, possible_manifest, data_availability provider,
  venue_freshness SLA, SOURCE_MODE_CAPABILITY, emission-latency, canonical_mappings VIX→databento routing,
  normalize_utils `normalize_barchart_ohlcv`, `_VENUES` list. Updated all consuming UAC tests (counts 31→30, 9→8;
  removed batch_barchart test cases). NEW `DATABENTO_VX_FUTURES_FIRST_DATE` export. **VALIDATION: full UAC pytest
  10587 passed / 565 skipped (2 ignored = worktree-path/sandbox artifacts unrelated to change); basedpyright clean.**
- 2026-06-24 — **UAC SHIPPED: commit `51417b53` on `live-defi-rollout` (real clone).** Cherry-picked from the isolated
  worktree onto current origin/LDR tip (`aa943afa`), preserving a CONCURRENT agent's `features_mvp_universe.py` WIP
  (stashed-by-name → cherry-pick → pop; clean separation verified — my `__init__.py` barchart removal committed, their
  feature-universe imports stay uncommitted/theirs). 40 files, +805/-433. Running quality-gates.sh for the green
  sentinel before the staging-PR promotion.

## Remaining: E cross-repo CONSUMERS (UTL pipeline_mode_resolver, MTDS _umi_yahoo, MDPS orchestration_writer — they
import the removed barchart consts/enum), MTDS wiring (A fetch-path guardrail + B KRX→yahoo routing + KRX equities
fetcher + `_classify_yahoo_ticker` .KS support), IS catalogue + backfill command doc (G). These break the build of
their repos until updated — doing next.

## Progress Log (continued)

- 2026-06-24 — **🟢 BARCHART REMOVAL ATOMICALLY SHIPPED — FLEET UNBLOCKED (coordinator-urgent done).**
  - UAC: barchart-removal + KRX + parity gate + databento floors landed on origin/live-defi-rollout via quickmerge
    (`1300079e`, QG-green sentinel `844c5ee6`, "ALL QUALITY GATES PASSED (229s)"). `BATCH_BARCHART` confirmed GONE from
    origin's `pipeline_mode.py`.
  - Blocker resolved en route: codex-compliance "3 violations" 3rd was MY docstring phrase "backward-compatible callers"
    (STEP 5.8 no-backward-compat grep) — reworded → ≤2 (the 2 pre-existing being file-size on the regrown
    source_priority/mvp_scope/honest_coverage + the pre-existing backward-compat in tradfi_symbology/events). Did NOT
    silence the pre-existing file-size (reverted my exclude-list edit).
  - **FOOTGUN caught + fixed**: quickmerge's stash/restore popped a CONCURRENT agent's `__init__.py` feature-universe
    imports back into the tree before `--files` staging → my push bundled their `__init__.py` change (16 insertions) but
    NOT their untracked `features_mvp_universe.py` module → origin had a BROKEN import. FIXED by pushing the module
    (`b10e8d6e`) to complete their already-half-landed work (verified importable + complete locally). Origin import now
    whole; their WIP preserved (not stomped — completed).
  - UTL: barchart-removal (pipeline_mode_resolver + data_source_mapping VIX→databento + 3 stale massive-first test
    assertions → databento-first) shipped via quickmerge (`8fd40a90`, QG-green "ALL QUALITY GATES PASSED (146s)").
    45/45 resolver tests pass.
  - **Coordinator: fleet is UNBLOCKED — origin/live-defi-rollout (UAC `1300079e`+`b10e8d6e`, UTL `8fd40a90`) is
    consistent; no dangling BATCH_BARCHART; UAC imports whole.**
- 2026-06-24 — **MTDS wiring (A fetch-path + B KRX routing + E consumer) IN PROGRESS (pre-commit).** YahooFinanceAdapter:
  guardrail wired into `download_daily` (1d floor clamp) + `download_intraday` (lookback + per-request width) — the
  non-bypassable fetch path; `_classify_yahoo_ticker` recognises `.KS` KRX codes → EQUITY. `_umi_yahoo.py`: removed the
  barchart-const consumer (preload-range branch gone; VIX 15m gap always-False now) + added `fetch_yahoo_equities`
  (KRX, source=yahoo, ohlcv_24h, shard-isolated). `umi_tick_provider.py`: KRX→`_fetch_yahoo_equities` routing branch +
  import. Rewrote `test_vix_15m_source_layering.py` for the post-barchart reality (no gap; Yahoo-window calls Yahoo;
  pre-window empty). Running MTDS QG next.

- 2026-06-24 — **MTDS SHIPPED (cb3d0088): KRX/Yahoo equities fetch + routing + general guardrail + barchart-consumer
  removal.** ALL QUALITY GATES PASSED (94s), 5 files (only mine; foreign catalog_reader WIP untouched). PROVEN:
  fetch_yahoo_equities downloads all 3 KRX stocks (005380/005930/000660) → venue=KRX/equity/ohlcv_24h, sane OHLCV.
  Guardrail wired on the non-bypassable adapter path — download_daily 1d pre-2019 RAISES, download_intraday 15m>60d
  RAISES, 1m>8d-width RAISES (all verified live). MDPS barchart consumer (orchestration_writer) fixed + tests rewritten
  (14 pass). IS: KRX added to `_TRADFI_VENUES` + `_create_krx_equity_records` in the databento reference adapter
  (KRX:EQUITY:<code>, raw_symbol=.KS, Asia/Seoul tz). All A-G CODE done; MDPS+IS pending final QG + ship.

## Item G — IS backfill command + skip/overwrite answer (FOR COORDINATOR)

**The skip-vs-overwrite question (READ the code, answered):** the IS instruments backfill is **IDEMPOTENT
SKIP-IF-EXISTS** — `instruments_service/engine/orchestrator/venue_core.py::_should_skip_shard`: a shard already at
`captured`/`empty_confirmed`/`EXPECTED_*` is SKIPPED unless `--force`; `attempted_failed` rows are NEVER skipped
(auto-retried). **A full-enumeration re-run yields OLD+NEW with NO DATA LOSS** — the enumeration source returns the
COMPLETE per-venue universe each run; skip-existing PRESERVES captured old shards (skip ≠ overwrite-with-empty), and new
symbols (or KRX as a fresh venue) backfill clean. So:
- **KRX (FRESH venue, never backfilled)** → no existing rows → backfills clean WITHOUT `--force`.
- **Existing venues (NASDAQ/NYSE) with new symbols** → run WITHOUT `--force` to backfill only the new/failed shards
  (old captured shards skipped, preserved); OR `--force` to re-attempt everything (old+new, still no loss).

**Exact commands for the coordinator (do NOT run — coordinator owns the ops):**
1. **Rebuild the IS+UAC tarballs from clean origin/LDR** (they must carry the KRX UAC + IS adapter changes):
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --include instruments-service --include unified-api-contracts`
   (from a clean `WORKSPACE_ROOT` at origin/live-defi-rollout).
2. **IS instruments backfill for KRX** (fresh venue): launch the IS instruments backfill VM with `VM_ASSET_GROUP=tradfi`
   + venue=KRX (the launcher passes `--venues KRX`); since KRX is fresh, no `--force`. Verify per-day shards land at the
   `KRX:EQUITY:<code>` grain (`captured`/`empty_confirmed`). End-date ≤ yesterday.
3. **IS consolidation / catalogue-regen**: re-run the `lifecycle-catalogue-regen-tradfi` Cloud Run job
   (`gcloud run jobs execute lifecycle-catalogue-regen-tradfi --region asia-northeast1`) so the catalogue rolls up the
   new KRX instrument lifecycle into `prod/catalog.parquet` (the catalogue is venue-agnostic — it walks the by_date
   snapshots, so KRX flows in once the IS backfill writes KRX by_date rows). Expected: catalog mtime=today, KRX rows
   present.
4. **MTDS backfill / wave** for KRX OHLCV: launch a tradfi MTDS backfill for venue=KRX, `VM_SOURCE=yahoo`,
   `VM_TASK=mtds-backfill` (the KRX route in `umi_tick_provider.fetch_tick_data_for_venue` calls `fetch_yahoo_equities`).
   data_types: ohlcv_24h (daily) + ohlcv_1m/15m within the Yahoo lookback ladder. The `_VENUE_SOURCE_EXCLUSIONS`
   fail-closes a stray `--source databento/massive` for KRX. Expected: KRX ohlcv_24h captured for trading days, 3
   instruments.

- 2026-06-24 — **MDPS + IS in flight.** MDPS: barchart consumer fixed + found+fixed 10 PRE-EXISTING databento-first
  test failures (test_canonical_writer_archetype_grain / _record_helpers / test_orchestration_scanner_multi_source —
  they asserted the 2026-06-11 massive-first order but UAC flipped to databento-first; stale tests, code correct;
  99 MDPS tests now pass). MDPS QG re-running. IS: KRX venue + adapter committed in an ISOLATED worktree (a850a82,
  off origin/LDR) to avoid the main IS clone's foreign WIP (catalogue.py/sports_dependency + a deleted reconcile
  script). IS targeted tests (52) pass. IS catalogue (build_instrument_catalogue) is venue-agnostic (walks by_date
  snapshots) → KRX flows in once the IS backfill writes KRX by_date rows; no catalogue code change needed. The OHLCV
  aggregation (1m→15m/1h/24h) is symbol-agnostic → no KRX config change needed.

## ✅ FINAL HANDOFF REPORT (2026-06-24) — A–G ALL SHIPPED + GREEN

**Shipped commits on origin/live-defi-rollout:**
- UAC: `1300079e` (close-out) + `b10e8d6e` (un-break import) — QG-green sentinel `844c5ee6`, 10587 tests pass.
- UTL: `8fd40a90` — QG-green "ALL QUALITY GATES PASSED (146s)".
- MTDS: `cb3d0088` — QG-green (94s).
- MDPS: `ca5ca33` — QG-green (63s).
- IS: `1ba5da4` — KRX QG-clean (basedpyright/ruff + 54 databento-tardis + 52 venue/adapter tests pass; shipped via the
  dirty-deps carve-out because the IS clone had a concurrent agent's defi-pool WIP).

**Per-item DONE:**
- **A (Yahoo guardrail — GENERAL + MEASURED)**: `registry/data_source_continuity.py` — MEASURED limits (1m=8d/request +
  ~30d total, 15m=60d [not 89], 1h=730d, 1d=unbounded→clamped to 2019-01-01 backfill floor). New
  `YAHOO_DAILY_BACKFILL_FLOOR`, `YAHOO_INTRADAY_MAX_REQUEST_DAYS`, `YahooRequestTooWideError`,
  `assert_yahoo_request_width_ok`; `assert_yahoo_intraday_within_limit` is now GENERAL (bounds 1d too). **WIRED on the
  non-bypassable MTDS fetch path** (`YahooFinanceAdapter.download_daily`/`download_intraday`) — verified live: 1d pre-2019
  RAISES, 15m>60d RAISES, 1m>8d-width RAISES. QG unit test pins each. **TESTED Yahoo limits confirmed vs targets**:
  1m=8d/req (target 28→real 8 per-request), 15m=60d (target 89→real 60), 1h=730d (confirmed), 1d unbounded (confirmed).
- **A test-download (3 KRX × 4 granularities)**: Hyundai 005380.KS / Samsung 005930.KS / SK Hynix 000660.KS — 1d
  rows=243, 1h rows=2762, 15m rows≈910 (within 60d), 1m rows≈1773 (within 8d/req); sane OHLCV. `fetch_yahoo_equities`
  proven end-to-end (3 rows venue=KRX/equity/ohlcv_24h written).
- **B (KRX venue)**: UAC `venue_mapping` (all_databento_venues + venue_to_data_provider=yahoo_finance + start_dates) +
  `market_data_categories.VENUES_BY_ASSET_GROUP["tradfi"]` + `_VENUE_SOURCE_EXCLUSIONS` (KRX excludes databento+massive)
  + `expected_coverage._TRADFI`; MTDS `umi_tick_provider` KRX→`fetch_yahoo_equities` routing + `_classify_yahoo_ticker`
  `.KS` support; IS `_TRADFI_VENUES` + `_create_krx_equity_records`. Canonical code = **KRX** (matches `.KS` Yahoo
  convention). source=yahoo. Deployment-ui/api enumerate venues dynamically from UAC — no hardcoded list to touch.
- **C (UAC universe + MVP → 103/103)**: 3 KRX bare codes in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` (removed the BLOCKED-DATA
  "no US twin" note); `mvp_scope.is_mvp` equity carve-out venue set gains KRX. `is_mvp(tradfi,KRX,EQUITY,ohlcv_1m,
  005930,yahoo)=True`, non-basis ticker=False.
- **D (Centralised parity gate)**: `tests/unit/test_venue_source_adapter_parity.py` — 249 tests, ALL parametrised over
  the canonical registries (zero new test code for future venues). Validates: venue⟺asset_group reverse-index; every
  tradfi venue→a data source; every SOURCE_PRIORITY source→a capability/computed/documented-gap; every tradfi-equity MVP
  cell fetchable + source-valid; Yahoo+Databento adapters declare+enforce limits. **HALF-WIRED RED-FAIL PROVEN**:
  `test_half_wired_venue_invokes_real_gate_and_red_fails` monkeypatches KRX out of both source maps → the real rule-2
  assertion raises `AssertionError(match="resolves to NO data source")`. **PRE-EXISTING GAPS found + documented
  (allowlisted, NOT blocking KRX)**: `massive`/`polymarket_clob`/`polymarket_gamma_api` lack SourceCapability rows;
  `YAHOO_FINANCE` is a legacy source-as-venue artifact; `PROTOCOL_CAPABILITIES` is a string-list (skipped). Wired into
  UAC contract tests (pytest).
- **E (Barchart FULLY removed, no shim)**: deleted `external/barchart/` dir + `_BARCHART` capability +
  `PipelineMode.BATCH_BARCHART` + `VENUE_ERRORS_TRADFI[barchart]` + `BARCHART_VIX_*` consts + barchart endpoint/
  venue_manifest/possible_manifest/data_availability/venue_freshness/SOURCE_MODE_CAPABILITY/emission-latency +
  `normalize_barchart_ohlcv`; rewrote `VIX_15M_SOURCE_HISTORY`/`get_vix_15m_source` (BARCHART_CSV→DATABENTO_VX_FUTURES;
  `is_vix_15m_gap_date` always False); canonical_mappings VIX→databento. Cross-repo consumers fixed: UTL
  (pipeline_mode_resolver + data_source_mapping), MTDS (`_umi_yahoo`), MDPS (orchestration_writer). `rg -i barchart` →
  only retirement-note comments remain. **The parity gate (D) confirms no source=barchart survives.** CLAUDE.md VIX-15m
  note updated → VX-futures-via-databento.
- **F (Databento boundary precision)**: **MEASURED LIVE** (operator Method B — real `timeseries.get_range` with
  continuous `ES.c.0`; Method A get_cost returns $0 at every date, confirming no rolling free allowance). **FINDING: our
  FIXED subscription grants FULL HISTORY, NO PAYG rolling edge** — L1 trades served at 1460d (4y), L2 mbp-10 + L3 mbo at
  730d (2y), L0 bounded only by dataset-start (~2010 ≈16y). **BEFORE→AFTER floor values**: `LEVEL_MAX_LOOKBACK_DAYS` L0
  16*365 / L1 365 / L2 30 / L3 30 → **ALL = 16*365** (full history; true floor = dataset available-start, the API 422s
  there). QG edge test asserts 730d-back now ALLOWED (old L1=365 window wrongly rejected it) + one-day-past-floor raises.
  Guard RE-ENABLED (probe used a standalone script; the live gate was never bypassed). CLAUDE.md databento-floor note
  updated.
- **G (IS catalogue + aggregation code)**: KRX in `_TRADFI_VENUES` + `_create_krx_equity_records` (databento reference
  adapter). The daily-catalogue `build_instrument_catalogue.py` is **venue-agnostic** (walks by_date snapshots) → KRX
  flows in once the IS backfill writes KRX by_date rows; NO catalogue code change needed. The OHLCV aggregation
  (1m→15m/1h/24h) is **symbol-agnostic** → NO KRX config change. **skip-vs-overwrite ANSWER (read the code):** IS
  backfill is **IDEMPOTENT SKIP-IF-EXISTS** (`_should_skip_shard`) — captured/empty_confirmed/EXPECTED_* shards skipped
  unless `--force`; attempted_failed never skipped. A full-enumeration re-run yields **OLD+NEW with NO DATA LOSS**
  (enumeration returns the complete per-venue universe; skip-existing preserves captured shards). KRX = fresh venue →
  backfills clean WITHOUT --force.

**FOR THE COORDINATOR — the exact OPS commands (do NOT run; I prepared, you run):** see the "Item G — IS backfill
command + skip/overwrite answer" section above for the 4-step sequence (tarball rebuild → IS KRX instruments backfill →
IS catalogue-regen Cloud Run job → MTDS KRX OHLCV wave with VM_SOURCE=yahoo).

**One filed finding (NOT blocking, concurrent-agent-owned):**
`plans/active/issues/is_build_catalogue_defi_pool_dual_form_test_failures_2026_06_24.md` — 4 PRE-EXISTING defi-pool
dual-form tests fail on origin/LDR (a concurrent agent's mid-flight `reconcile_defi_pool_manifest_dual_form` refactor);
unrelated to KRX; blocks the IS green sentinel until that agent lands their fix (KRX shipped via the dirty-deps carve-out
because of it).
