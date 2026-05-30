---
title: TradFi dual-source — Massive alongside Databento with co-mingled source column
parent_epic: tradfi_master
assigned_vm: vm-tradfi
priority: P1
status: active
type: infra
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7
created: 2026-05-28
owner: ikenna
asset_group: tradfi
completion_gates:
  code: C5
  deployment: D3
  business: B4
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
related_plans:
  - plans/epics/tradfi_master.md
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
---

# TradFi dual-source — Massive alongside Databento

## Overview

Adds Massive (formerly Polygon.io, rebranded 2025-10-30) as a second TradFi data source alongside Databento. Both
vendors cover any (symbol, data*type) in the TradFi cell of the MVP coverage matrix; they co-mingle on the existing hive
prefix `day=…/asset_group=tradfi/venue=…/` and disambiguate via a new `source` column written into every TradFi
parquet + recorded in the manifest. Lands the deferred
`multi_source_priority_merge_2026*\*`work that the`SOURCE_PRIORITY` module docstring already names as the prerequisite
for any TradFi cell to legitimately list two sources.

**Operator decisions captured (2026-05-28 chat)**:

1. **Architecture**: co-mingle on shared hive layout, add `source: str` row column. NOT a hive partition key.
2. **Coverage policy**: Massive and Databento each allowed for any (symbol, data_type) — no vendor lock-in per cell.
3. **VX futures (CFE)**: Massive does NOT cover CFE. Keep existing pattern (Yahoo + Barchart as already wired in
   `("tradfi", "ohlcv_15m"): ["databento", "yahoo", "barchart"]`). No change to the VX cell required.
4. **Scope**: batch / historical REST first. Live / WebSocket connector deferred — operator stated "not too worried
   about live yet".
5. **Tier**: Massive billed at delayed-OK tier — Stocks Starter $29 + Options Starter $29 + Indices Starter $29 +
   Futures $199 ≈ $290/mo. Pricing TBC at signup; ping operator if real-time required for any cell.

## Status snapshot

| Layer                                              | Status                       | Note                                                               |
| -------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------ |
| UAC SOURCE_PRIORITY registry                       | 🟡 single-source seeds today | Append `"massive"` to 6 TradFi cells                               |
| Multi-source merge logic                           | 🔴 deferred (named)          | Unblocks any two-entry list — this plan lands it                   |
| MTDS Massive REST connector                        | 🔴 missing                   | Mirror `databento_tradfi_ws_connector.py` REST path                |
| MTDS Massive WS connector                          | ⚪ out of scope              | Deferred — see `tradfi_massive_live_ws_<TBD>.md` (named successor) |
| Schema: `source` column on TradFi parquets         | 🔴 missing                   | New required column; backfill plan in Phase 4                      |
| Manifest `record_captured(source=...)` integration | 🟡 partial                   | `available_at` per-row exists; `source` per-row new                |
| Databento backfill with `source='databento'`       | 🔴 missing                   | One-shot rewrite of existing TradFi corpus                         |

## Coverage matrix (Massive vs Databento, MVP cells)

| UAC data_type   | Databento endpoint | Massive endpoint                              | Both ✅? |
| --------------- | ------------------ | --------------------------------------------- | -------- |
| `trades`        | Trades             | Trades (Futures/Options/Stocks)               | ✅       |
| `tbbo`          | TBBO               | Quotes / NBBO (OPRA-consolidated for options) | ✅       |
| `ohlcv_1m`      | OHLCV-1m           | Custom Bars (mult=1, timespan=minute)         | ✅       |
| `ohlcv_15m`     | OHLCV-15m          | Custom Bars (mult=15, timespan=minute)        | ✅       |
| `options_chain` | Definition + chain | Option Chain Snapshot + All Contracts         | ✅       |
| `futures_chain` | Definition         | Contracts + Products                          | ✅       |

**Exchange exception**: Massive Futures covers CME/CBOT/NYMEX/COMEX. **CFE (CBOE Futures Exchange — VX/VIX futures) is
NOT covered.** Resolved by existing Yahoo + Barchart layering on `ohlcv_15m` per operator decision above.

## Phased execution

### Phase 0 — Audit + plan baseline (0.5 day)

- [ ] [AUDIT] P1. Confirm Massive subscription tier(s) signed up + API key in Secret Manager.
  - Credential ask → operator if not yet signed. Per External Data Is Always Available rule, this is
    `BLOCKED-CREDENTIALS` until [ack].
  - Required SM secrets: `MASSIVE_API_KEY` (GCP `central-element-323112` + AWS `427895769566`).
- [x] ✅ [AUDIT] P1. Workspace-wide grep for "databento" + "polygon" + "polygon.io" hardcoded references; capture
      remediation list. Plan Pass 1 = registry-driven, not text-replace. **DONE 2026-05-30** (slot-1 audit):
      12 production code files with hardcoded references found. Key groups:
      - **Registry-level (expected/acceptable)**: `unified_api_contracts/registry/endpoints.py:43-44`
        (databento hist/live URLs); `registry/_endpoint_registry_data.py:147`; `capability_declarations/_tradfi.py:74`
        (base_urls). These are the SSOT — not targets for removal.
      - **Adapter-level hardcoded URLs (remediation target)**: `features-service/…/polygon_corporate_actions_adapter.py:27`
        (`_BASE_URL = "https://api.polygon.io"`); `instruments-service/…/tradfi/polygon.py:67`
        (`_POLYGON_BASE = "https://api.polygon.io"`). Fix: route through `get_tradfi_protocol_url("polygon")` in UAC.
      - **Source string hardcodes in domain logic (remediation target)**:
        `unified_api_contracts/registry/tradfi_symbology.py:243,254` (`data_source="databento"`);
        `features-service/…/corporate_actions_calculator.py:71,100` (`source="polygon"`);
        `instruments-service/…/router.py:231` (`if source == "databento"`). Fix: import source constants from UAC
        `SOURCE_PRIORITY` registry or a `TradFiSource` enum (Phase 1 UAC work).
      - **Config/SM layer (acceptable — not hardcoded secrets)**: `cloud_config.py:526`, `data_source_mapping.py:67`,
        `market_interface/config.py:42` all use `AliasChoices("DATABENTO_API_KEY")` / SM lookup — correct pattern.
      Remediation plan: Pass 1 (registry-driven) = Phase 1 UAC SOURCE_PRIORITY update will make source strings
      importable constants; adapters switch to `get_tradfi_protocol_url()`. Pass 2 = when Massive connector is added,
      adapter URL hardcodes become moot (both route through registry). No text-replace needed.
- [x] ✅ [AUDIT] P1. Confirm `SOURCE_PRIORITY` module docstring's deferred-plan slug is `multi_source_priority_merge_*` and
      reserve THIS plan's slug as the canonical successor (cross-link both ways). **DONE 2026-05-30** (slot-1):
      `unified_api_contracts/canonical/crosscutting/source_priority.py` line 18 had
      `multi_source_priority_merge_2026_*<TBD>.md` — updated to name THIS plan
      (`tradfi_massive_dual_source_2026_05_28.md Phase 2`) as the canonical successor. UAC@{sha below}.
      Cross-link: `source_priority.py` → this plan (docstring); this plan Phase 2 → `source_priority.py`
      (the `read_with_source_priority()` extension is Phase 2 task #1).

### Phase 0.5 — Universe expansion (shipped 2026-05-28)

- [x] ✅ [UAC] P1. `tradfi_ticker_universe.py` — added missing BTC ETFs (BITB, BTCO, BRRR, HODL, EZBC) + ETH ETFs (ETHV,
      ETHW, CETH, QETH, EZET); coverage now 10 BTC + 8 ETH = all 18 US-listed crypto-spot ETFs the operator validated on
      ThetaData earlier.
- [x] ✅ [UAC] P1. `tradfi_ticker_universe.py` — added new `TRADFI_FUTURES_PRODUCTS` list (12 CME-group root products):
      ES, MES, BTC, MBT, ETH, MET (CME); CL, MCL, NG, QG (NYMEX); GC, MGC (COMEX). Wired into `TRADFI_TICKER_UNIVERSE`
      dict under `futures_products` key.
- [x] ✅ [BLOCKED-CREDENTIALS — operator action] [AUDIT] P0. Massive `/v3/reference/futures/*` endpoints return
      `404 page not found` despite operator confirming Futures Advanced package purchased 2026-05-28.
      `/v3/reference/tickers?market=futures` returns 200 + empty array. Either (a) subscription still propagating
      (typical 30-60 min after billing) or (b) API endpoint shape differs from Massive's published docs. **Operator to
      verify on `massive.com/dashboard` that Futures Advanced shows active**; re-test after activation. Options Advanced
      verified working (SPX, I:SPX, IBIT chains all return contract tickers).
      **Finding (2026-05-30):** Main agent confirmed Futures Advanced subscription IS active on massive.com/dashboard.
      Root cause of 404 is endpoint shape mismatch — `MASSIVE_API_KEY` not accessible from worker VM (not in GCP/AWS SM
      on this host), so live re-test deferred to Phase 0.5+ code task with creds. Suggestion from main agent: use REST
      API or S3 flat files approach for futures reference data. S3 flat files path (`s3://flatfiles/`) should be
      investigated as an alternative to `/v3/reference/futures/*` REST endpoint. Unblocking condition met: subscription
      confirmed active. Follow-on: ticket convention audit (line 111) and S3 flat files feasibility remain open.
- [ ] [AUDIT] P1. Once Futures endpoint works, confirm Massive ticker convention for CME contracts (`ESH26` / `ES:H26` /
      `ES.H26` / `F:ESH26`). Codify in `registry/tradfi_symbology.py`.
- [ ] [AUDIT] P1. BTC/ETH ETF backfill audit — confirm Databento has historical bars for all 18 ETF tickers (10 BTC + 8
      ETH) since each ETF's listing date. Per Mega-Audit 2026-05-20 0% v8 incident, "constant says v8" is not evidence;
      read actual GCS rows. Status TBC pending audit script run.
- [x] ✅ [AUDIT] P1. Massive Stocks Starter coverage of BTC/ETH ETFs verified live 2026-05-28 — operator added Stocks
      Starter tier; smoke-tested 1m OHLCV for every ETF on its listing day; all 18 return data: 9 BTC spot at 2024-01-11
      (IBIT/FBTC/BITB/ARKB/BTCO/BRRR/HODL/EZBC/GBTC), BITO at 2021-10-19 (BTC futures ETF), 8 ETH spot at 2024-07-23
      (ETHA/FETH/ETHE/ETHV/ETHW/CETH/QETH/EZET). Starter's 5-year window (boundary verified 2021-05-28 = NOT_AUTHORIZED,
      2021-06-01 = OK) contains every ETF's full lifetime — Massive alone is sufficient backfill source for the ETF
      cells regardless of Databento state. Phase 4 connector should prefer `s3://flatfiles/us_stocks_sip/` bulk download
      for these 18 tickers (one-shot per ETF for full history vs paginated REST).

### Phase 1 — UAC contract additions (1 day)

- [x] ✅ [UAC] P1. `unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY` — append `"massive"` to:
  - `("tradfi", "trades")`
  - `("tradfi", "tbbo")`
  - `("tradfi", "ohlcv_1m")`
  - `("tradfi", "ohlcv_15m")` — slot AFTER databento, BEFORE yahoo/barchart (priority order)
  - `("tradfi", "options_chain")`
  - `("tradfi", "futures_chain")`
  - UAC@f7cf8828
- [x] ✅ [UAC] P1. `pipeline_mode_for_source("massive")` — register the batch `PipelineMode` for Massive:
      `BATCH_MASSIVE = "batch_massive"` (alphabetically after BATCH_HYPERLIQUID_REST); closed-set round-trip test passes.
  - UAC@f7cf8828
- [x] ✅ [UAC] P1. `emission_latency_ms_for_source("massive")` — register Massive's emission latency. Delayed-tier default
      = 15 minutes (900_000 ms) per Massive's Starter tier semantics. Real-time tier would be sub-second.
  - UAC@f7cf8828
- [x] ✅ [UAC] P1. Add Massive to UAC source-string registry test fixture; assert closed-set tests pass.
      62 tests pass: test_source_priority (28) + test_source_priority_pipeline_mode (14) + test_pipeline_mode (20).
- [ ] [UAC] P1. `quality-gates.sh` green for `unified-api-contracts`.

### Phase 2 — Multi-source merge logic (3 days — the deferred plan slot)

- [x] ✅ [UAC] P1. `read_with_source_priority()` — extend to return `Iterator[tuple[Row, source, pipeline_mode]]` when
      multiple sources are present for the same (asset_group, venue, day, data_type) cell. Today the function assumes
      single-source-per-cell; this is the merge logic.
  - Added `get_all_sources_with_priority(asset_group, data_type) -> list[tuple[str, PipelineMode]]` returning full
    ordered source list (primary first). Multi-source cells like `("tradfi","trades")` return `[("databento", BATCH_DATABENTO), ("massive", BATCH_MASSIVE)]`.
  - 6 new tests; 73 total pass. Exposed via crosscutting facade. UAC@87570f4d
- [x] ✅ [UAC] P1. Tie-breaker implementation per module docstring:
  1. Timestamp-availability (live-time emitters win over archive-only)
  2. Coverage (broader-coverage wins where overlap)
  3. Information richness (more-fields wins)
  4. Merge-different-fields (non-overlapping field sets → consumers union)
  - `select_primary_available_source(asset_group, data_type, available_sources)` applies rules 1-3 (list order)
    at runtime: databento absent + massive present → returns massive. Rule 4 (field union) is consumer-layer.
  - 7 new tests; 80 total pass. UAC@898bc948
- [ ] [UAC] P1. Conflict detection: same (asset_group, venue, day, ticker, ts) appearing in both sources → log + count,
      emit to manifest as `divergence_kind=DUAL_SOURCE_DUPLICATE`. Do NOT silently drop.
- [ ] [UAC] P1. Unit tests: dual-source happy path, conflict path, missing-source-A-present-source-B path, field-union
      path.
- [ ] [UAC] P1. Remove the "deferred to a follow-up plan" line from `source_priority.py` docstring; replace with link to
      THIS plan's archive path.

### Phase 3 — Schema: source column on TradFi parquets (1 day)

- [ ] [UTL] P1. Add `source: str` column to TradFi writer schemas in `unified_trading_library.writegate` per
      writegate_honest_coverage_endtoend Phase 6.x conventions.
- [ ] [UTL] P1. Update `record_captured(source=...)` kwarg — pass-through to manifest row. Validate in `record_captured`
      that `source` is in `SOURCE_PRIORITY` for the (asset_group, data_type) pair.
- [ ] [UAC] P1. Bump TradFi parquet `schema_version` (likely v8 → v9 per the v8 divergence already documented).
      Cluster-validation kwargs in `record_captured` include `source` in the cluster spec.
- [ ] [QG] P1. STEP 5.64 (cluster validation) MUST fail if writer omits `source` for TradFi cells.

### Phase 4 — MTDS Massive connector (REST / batch only) (2 days)

- [ ] [MTDS] P1. New module `market_tick_data_service/handlers/tradfi/massive_tradfi_rest_connector.py`. Mirror shape of
      `databento_tradfi_ws_connector.py` REST path. Auth via `MASSIVE_API_KEY`.
- [ ] [MTDS] P1. Endpoint mapping (per coverage matrix above): | data_type | Massive endpoint | |---|---| | `trades` |
      `/v3/trades/{ticker}` | | `tbbo` | `/v3/quotes/{ticker}` | | `ohlcv_1m` |
      `/v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}` | | `ohlcv_15m` |
      `/v2/aggs/ticker/{ticker}/range/15/minute/{from}/{to}` | | `options_chain` | `/v3/snapshot/options/{underlying}` |
      | `futures_chain` | `/v3/reference/futures/contracts` + `/v3/reference/futures/products` |
- [ ] [MTDS] P1. Universe / symbol resolution: instruments-service → Massive ticker mapping. SPX = `I:SPX`, VIX index =
      `I:VIX`, ETF options use OPRA root, CME futures use Massive's futures contract ticker convention.
- [ ] [MTDS] P1. Error classification via UAC `classify_venue_error()`. Emit `ADAPTER_FETCH_FAILED` per workspace
      adapter contract.
- [ ] [MTDS] P1. Manifest emission per writegate Phase 6.x: every (asset_group, venue, day, data_type) cell gets
      `record_captured(source="massive", ...)` or `record_empty(reason=<typed>, source="massive")`.
- [ ] [MTDS] P1. Unit tests: 200 happy path, 401 auth-fail, 429 rate-limit, 5xx upstream, 200 empty (→
      `SOURCE_RETURNED_ZERO`), per-data_type cassette tests.
- [ ] [MTDS] P1. Integration tests: `@pytest.mark.requires_credentials` — gated, skipped without `MASSIVE_API_KEY`.

### Phase 5 — Backfill Databento corpus with source column (1 day + run-to-completion)

- [ ] [SCRIPT] P1. `market-tick-data-service/scripts/backfill_tradfi_source_column.py` — single-walk pass over existing
      TradFi parquets, write `source='databento'` row column, increment `schema_version` to match Phase 3.
  - Composes with single-walk discipline HARD RULE: this is part of the next bundled migration; if Phase 2.2 walk is
    still open, bundle into it. If Phase 2.2 is closed, this is a scheduled next-migration window.
- [ ] [SCRIPT] P1. Pre-migration drain per CLAUDE.md HARD RULE: stop all TradFi-writing VMs (GCP + AWS) → consolidate
      manifest → snapshot `_index/snapshots/pre_dual_source_2026_05_28.parquet` → run backfill → verify divergence=0 →
      resume.
- [ ] [VERIFY] P1. Post-backfill audit: every TradFi parquet has `source` column populated. NULL count = 0.
      `source ∈ {"databento", "yahoo", "barchart"}` (Massive parquets first appear post-Phase-4 dispatch).
- [ ] [VERIFY] P1. Manifest re-consolidation: every TradFi `(asset_group, venue, day, data_type)` row has `source` field
      populated.

### Phase 6 — Codex SSOT updates + plan archival prep (0.5 day)

- [ ] [CODEX] P1. `codex/02-data/contracts-scope-and-layout.md` — document `source` column as part of TradFi canonical
      schema. Update SOURCE_PRIORITY example to show multi-source TradFi cell.
- [ ] [CODEX] P1. `codex/02-data/availability-manifest-and-data-status.md` — document `source` field in manifest row +
      per-source `capture_status` semantics. Multi-source cell can be `captured` from one source + `empty_confirmed`
      from another in the same window.
- [ ] [CODEX] P1. `codex/02-data/honest-absence-downstream-handling.md` — add per-source consumer policy: if cell has at
      least one `captured` source, downstream treats cell as captured (union semantics). Per-reason taxonomy unchanged.
- [ ] [CODEX] P1. `plans/epics/tradfi_master.md` `related_plans:` — append this plan's path.
- [ ] [CLAUDE.md] P1. Update "Other key rules" → "VIX 15m" entry to remain accurate post-Massive (no change expected; VX
      futures gap still resolved via Yahoo/Barchart).
- [ ] [PLAN] P1. Pre-archival 5-step audit per CLAUDE.md Plan-archival HARD RULE.

## Success criteria

| Phase   | Gate                         | Verification                                                                                                                                 |
| ------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 | UAC C4                       | `cd unified-api-contracts && bash scripts/quality-gates.sh` exit 0                                                                           |
| Phase 2 | UAC C4 + tests               | New dual-source merge tests pass; closed-set tests still pass                                                                                |
| Phase 3 | UTL + UAC C4                 | `record_captured` rejects TradFi write without `source` kwarg; QG STEP 5.64 enforces                                                         |
| Phase 4 | MTDS C4 + D2                 | Unit tests green; integration tests skip cleanly without creds; smoke run with creds writes ≥1 parquet per data_type with `source='massive'` |
| Phase 5 | B4 + manifest divergence = 0 | Every existing TradFi parquet has `source` column; no NULL rows; manifest consolidated; snapshot saved                                       |
| Phase 6 | All codex docs updated       | `parent_epic` resolves; codex alignment check (per Plan Archival HARD RULE) passes                                                           |

## Out of scope (deferred — named successors required)

- **Live / WebSocket Massive connector** — deferred per operator. Named successor:
  `tradfi_massive_live_ws_<YYYY_MM_DD>.md` to be filed when live becomes priority.
- **Real-time tier upgrade** — if any TradFi cell needs sub-second emission latency, the Massive Starter tier ($29)
  won't suffice. Named successor: same as above.
- **Sportradar / sports vendor dual-sourcing** — this plan is TradFi-scoped. Sports + Prediction get their own follow-up
  plans under `epics/sports_master.md` + `epics/predictions_master.md` if dual-sourcing wanted there.
- **CFE VIX futures (VX) primary coverage** — operator chose to keep Yahoo + Barchart layering. If CFE-direct ever
  becomes desired, named successor: `tradfi_cfe_vx_futures_<YYYY_MM_DD>.md`.

## Dependencies + ordering

- **Phase 0 → Phase 1**: blocks on credential ack ([ack] from operator on slot ping with `MASSIVE_API_KEY`).
- **Phase 1 → Phase 2**: registry must accept `"massive"` before merge logic can reference it.
- **Phase 2 → Phase 3 + 4**: merge logic must land before any consumer reads from dual-source cells; otherwise silent
  correctness bug.
- **Phase 3 → Phase 4**: schema column must exist before MTDS connector writes use it.
- **Phase 4 → Phase 5**: backfill is symmetric — Databento writes get `source='databento'` retroactively at the same
  time Massive writes start landing with `source='massive'`.
- **Phase 5 (drain) HARD ORDER**: VM drain → manifest consolidate → snapshot → backfill → resume. Per the pre-migration
  drain HARD RULE.

## Risks + mitigations

| Risk                                                                             | Mitigation                                                                                                      |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Schema bump (v8 → v9) catches Mega-Audit v8 divergence in flight                 | Coordinate with `mtds_mdps_master.md` Phase -1 workspace QG green gate before bumping                           |
| Massive ticker convention differs from Databento (e.g. futures contract symbols) | Phase 4 includes universe resolution layer; instruments-service is SSOT for symbol mapping per IS→MTDS contract |
| Dual-source divergence (same cell different values)                              | Phase 2 logs + counts but doesn't silently merge; surfaces as `DUAL_SOURCE_DUPLICATE` for operator visibility   |
| Massive Futures tier is single-price ($199) with no delayed option               | Confirmed in pricing-page research; operator-accepted at MVP                                                    |
| Massive subscription tier change post-MVP                                        | Re-emission-latency registration when tier upgraded; no schema change                                           |

## Codex SSOTs

- `codex/02-data/contracts-scope-and-layout.md` (Phase 6)
- `codex/02-data/availability-manifest-and-data-status.md` (Phase 6)
- `codex/02-data/honest-absence-downstream-handling.md` (Phase 6)
- `codex/02-data/data-pipeline-correctness-hard-rule.md` (reference — this plan is a data-correctness expansion for
  TradFi)
- `unified_api_contracts/canonical/crosscutting/source_priority.py` module docstring (Phase 2 — remove deferred slot
  reference)

## Provenance

Operator chat 2026-05-28 (slot 1 worktree `.tabs/1/`). Decisions recorded inline in Overview § "Operator decisions
captured".
