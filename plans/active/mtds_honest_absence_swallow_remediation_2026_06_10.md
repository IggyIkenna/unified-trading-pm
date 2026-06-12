---
title: MTDS honest-absence swallow remediation — re-verified P0/P1 fix batch (audit 2026-06-09/10)
created: 2026-06-10
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
locked_by: live-defi-rollout
locked_since: 2026-06-10
source:
  - plans/audit/results/mtds_mdps_master_audit_2026_06_09.md § Re-verification 2026-06-10 (adversarial caller-chain)
  - operator 2026-06-10 ("start working on them; check raw GCS data before changes where needed")
---

# MTDS honest-absence swallow remediation — P0 fix batch

> The re-verified GENUINE set only (5 false-positives retracted, 9 latent/dead-code routed to the disposition todo in
> the audit result § P2 — do NOT implement those here). Fix shape everywhere: **transport errors RAISE** (or typed
> sentinel / `failed_per_dt`) so the existing `record_failed` routing fires; `None`/empty reserved for
> honestly-probed-zero. Mirrors: `dex_swaps_handler:715` (handlers) / Polymarket CF-11 (adapters, mtds@2004c0e4).
> **Pre-change data check (operator 2026-06-10)**: read actual prod `_index` rows for affected venue cells BEFORE
> changing routing, so the fix's blast radius (how many cells currently lie) is measured, not assumed.

## Phase 0 — GCS data-state reads (BEFORE code changes; ADC available on slot-4 host)

- [x] ✅ [DATA] P0. Manifest reality check for the affected cells: read `_index/availability_index.parquet` per
      `market-data-tick-defi-*` (+ cefi for tardis): distribution of `capture_status × empty_confirmed_reason` for
      venues AAVE/COMPOUND/MORPHO (lending_indices), MARINADE/JITO (solana_defi lst_rates), PYTH×SOLANA (oracle_prices),
      GMX (perp_funding), SOLEND (lending backfill), and a tardis cefi venue sample — how many
      `SOURCE_RETURNED_ZERO`/`empty_confirmed` rows exist that may be mislabeled outages. Record counts here as the
      fix's before-state.
- [x] ✅ [DATA] P0. v9 `schema_version` distribution while in the buckets (unblocks audit item (g)/v9 BLOCKED-DATA):
      actual % at v9 per `market-data-tick-<ag>` `_index`.
- [x] ✅ [DATA] P0. Raw tradfi ohlcv column-name census (`ts_event` vs `timestamp`) — decisive for the bar-edge
      METASTABLE P0 (`bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 1); sample N files per day-range across
      the databento corpus.

## Phase 1 — P0 swallow fixes (one QG-sweep batch; per-unit commits via quickmerge)

- [x] ✅ [CODE] P0. (mtds@7455ffb + tests test_cf11_swallow_remediation.py) `lending_indices_handler.py:768` — narrow
      the blanket except: re-raise transport (`ClientError/OSError/TimeoutError`) alongside `SubgraphSchemaError`;
      re-raise non-schema GraphQL body errors (`:1182-1194`); move the GCS upload (`:741`) out of the swallowed try. —
      market-tick-data-service
- [x] ✅ [CODE] P0. (mtds@7455ffb) `solana_defi_handler.py:932,973,1051,1120` — remove/re-raise the four collector
      swallows so failures escape to `:457 record_failed`. — market-tick-data-service
- [x] ✅ [CODE] P0. (mtds@7455ffb) `oracle_prices_handler.py:828-832,948-960` — Pyth helpers raise on transport +
      non-200 (keep historical 404 → `[]`), engaging the dead `:757 record_failed` branch. — market-tick-data-service
- [x] ✅ [CODE] P0. (mtds@7455ffb) `liquidations_handler.py` — re-raise transport in `_fetch_morpho_*` (`:781-787`) AND
      remove `aiohttp.ClientError/OSError/SchemaValidationError` from the `:510-517` catch (all protocols). —
      market-tick-data-service
- [x] ✅ [CODE] P0. (mtds@7455ffb) `perp_funding_handler.py:963-969,1017-1023` — `_query_gmx_*` re-raise transport
      (reserve `None` for schema-unavailable); `record_failed` when both variants None instead of `:887 rows or []`. —
      market-tick-data-service
- [x] ✅ [CODE] P0. (mtds@7455ffb) `tardis_adapter.py` — 404-vs-error split: streaming `:833-835` + bulk `:2313-2327` +
      legacy `:906-908` RAISE on non-404/non-401 `TardisHTTPError` so §6A runner-exception → `record_failed`
      (`:1784-1789`) fires; optionally wire 429/5xx retry (config `retry_status_codes` currently dead on the path). —
      market-tick-data-service
- [x] ✅ [CODE] P0. (mtds@7455ffb, asset_group hoisted — CME-OPTIONS branch had it unbound)
      `engine/orchestrator.py:3141` — pass `asset_group=ag` to the chain-bundle `record_captured_from_counts` (mirror
      prediction `:3302`; do NOT pass `latency_source`). — market-tick-data-service

## Phase 2 — P1 follow-ons

- [x] ✅ [CODE] P1. (mtds@7455ffb) Solend chart backfill error accounting: `_solana_defi_fetch.py:248-253` + duplicate
      `solana_defi_handler.py:~1353-1364` + `fetch_phoenix:453` — errors>0 ∧ rows==0 → raise; partial → surface via
      warning/cluster validation. — market-tick-data-service
- [x] ✅ [CODE] P1. (mtds@7455ffb — PerLeafFailureRouter) `umi_tick_provider.py:429-430` FX per-ticker Yahoo swallow →
      route to `failed_shards`/AFF; add AFF emission to `yahoo_finance_adapter` error paths. — market-tick-data-service
- [x] ✅ [CODE] P1. (mtds@7455ffb + test_kalshi_cf11_fetch_failure.py ×5; umi dispatch TypeError latent bug also fixed)
      Kalshi CF-11 plumbing before the venue is ever enabled (mirror Polymarket `failed_tickers_out` + `failed_per_dt` +
      AFF). — market-tick-data-service
- [x] ✅ [UTL] P1. (utl@6f347d90 — optional source=+asset_group= on record_empty/record_failed/\_record_status,
      validated vs SOURCE_PRIORITY, blank allowed; tests test_manifest_writer_source_noncaptured.py. REMAINING fragment
      → new todo below: the mtds DefiManifestRecorder pass-through) Source on NON-captured rows: add `source=` kwarg to
      `record_empty:2197`/`record_failed:2413` + stamp in `_record_status:3447-3574`; then the MTDS
      `DefiManifestRecorder` pass-through one-liner. — unified-trading-library
- [ ] [CODE] P1. **DefiManifestRecorder pass-through (the UTL-item residual)**: `_defi_manifest.py` record_empty (:359)
      / record_failed (:485) now CAN forward `source=` + `asset_group="defi"` to the shipped UTL kwargs — add the
      params + forward (auto-stamps single-source DeFi cells on non-captured rows). — market-tick-data-service
- [ ] [CODE] P1. **GraphQL body-error swallows (same CF-11 class, surfaced 2026-06-11 while fixing transport)**:
      `liquidations_handler.py` subgraph `errors→return None` (~:589) and Morpho `errors→empty df` (~:778) — the
      transport split is fixed; the body-error path still degrades to honest-empty. — market-tick-data-service
- [ ] [CODE] P2. `polymarket_adapter._load_instruments_from_gcs` two inner `except Exception: pass` fallbacks
      (parquet→json→{}) — an IS-store read failure degrades to "no instruments" instead of failing loud. —
      market-tick-data-service

## Success criteria

- Every Phase-1 site: transport error → `attempted_failed` row (unit test per site pinning the routing); zero
  fetch-error paths returning honest-empty shapes.
- MTDS `quality-gates.sh` exit 0 on the batch; shipped via `quickmerge --agent --files`.
- Phase-0 before-state counts recorded here; after the backfill re-runs, the mislabeled cells get relabeled (tracked as
  a follow-up data fix, not silently).

## Progress journal

- 2026-06-10: plan created from the re-verified audit (slot-4). Phase 0 starting.
- 2026-06-10 Phase-0 RESULTS (read from actual prod GCS, slot-4 host ADC):
  - **v9 = 0.0% in ALL THREE consolidated `_index`es** — defi 1.9M rows (v6=308k/v8=307k/v7=8.5k), cefi 35.8M rows
    (99.9% v8), tradfi 579k rows (v8=488k/v6=39k/v4=17k). The `source` + `empty_confirmed_reason` columns DO NOT EXIST
    yet in these indexes (v8 shape). Audit item (g)/(v9) is **RED on data**; the canonicalisation walk has not reached
    these buckets (or the consolidated index lags it). Item (j)/(n) data-side verification is MOOT until v9 lands on
    data — the writer-side fixes remain correct.
  - **Swallow before-state (defi)**: JITO `lst_rates` **497 empty_confirmed vs 30 attempted_failed** (the swallow's
    signature); MARINADE 486 captured / 40 empty; SOLEND `lending_indices` **331 empty_confirmed vs 195 captured**
    (suspicious ratio); PYTH venue rows absent from top-cells (verify venue label when fixing oracle_prices);
    AAVE_V3/MORPHO write `rate_indices`/`utilization`/`risk_params` data_types (no `lending_indices` cells — handler
    name ≠ data_type; flag for the relabel pass). No reason split available pre-v9.
  - **ts_event census: 24/24 sampled raw tradfi ohlcv parquets are `timestamp`-named (zero `ts_event`)** — e.g.
    `raw_tick_data/by_date/day-2025-11-02/data_type-ohlcv_1m/equities/NYSE/...` (note: OLD pre-canonical path shape with
    dashes). The MDPS name-keyed shift will NOT fire on any of these → the bar-edge METASTABLE P0 is one rebuild from
    corpus-wide left-shift; census decisively supports the MTDS-converts + MDPS-content-aware fix
    (`bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 1 P0).
  - Follow-up filed: after Phase-1 ships, the mislabeled `empty_confirmed` cells (JITO/SOLEND et al.) need a
    relabel/re-fetch pass; and the v9=0% finding needs routing to the canonicalisation programme owner.
- 2026-06-11 (slot-4, autonomous run): **ALL Phase-1 P0 items + Phase-2 P1 riders (umi FX router, Solend/Phoenix
  accounting, Kalshi CF-11 plumbing) IMPLEMENTED + QG-GREEN** (`quality-gates.sh --no-fix` exit 0, full suite 3324+
  tests incl. 18 new: `test_cf11_swallow_remediation.py` ×13 + `test_kalshi_cf11_fetch_failure.py` ×5; 3 stale
  old-behaviour pins updated). Implementation notes: lending_indices got a typed `SubgraphQueryError` (body errors now
  raise too at `_execute_subgraph_query`; GCS upload moved out of the try); perp_funding both-variants-None now OMITS
  the chain entry → `count is None` → `record_failed`; tardis legacy `download_csv` raises `TardisHTTPError(status)` on
  non-200/404; orchestrator chain-bundle `asset_group=ag` hoisted above the branch (CME-OPTIONS branch had it unbound).
  Also in-batch: 2 fallback-import shims removed (`rebuild_tradfi_manifest.py:309` was silently SKIPPING the CF-11
  re-emit on UTL import error; `subgraph_health_probe.py:442`) → STEP 5.94 back at baseline 3. **Checkboxes flip on the
  quickmerge sha** — ship is one command, held only on the in-slot UTL WIP (the Phase-2 UTL item, being implemented
  concurrently) clearing the dep-audit. Paths staged-list preserved at `/tmp/mtds_quickmerge2.log`.
