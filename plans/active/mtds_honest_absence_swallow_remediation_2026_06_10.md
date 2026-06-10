---
title: MTDS honest-absence swallow remediation — re-verified P0/P1 fix batch (audit 2026-06-09/10)
created: 2026-06-10
parent_epic: epics/mtds_mdps_master.md
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

- [ ] [DATA] P0. Manifest reality check for the affected cells: read `_index/availability_index.parquet` per
      `market-data-tick-defi-*` (+ cefi for tardis): distribution of `capture_status × empty_confirmed_reason` for
      venues AAVE/COMPOUND/MORPHO (lending_indices), MARINADE/JITO (solana_defi lst_rates), PYTH×SOLANA (oracle_prices),
      GMX (perp_funding), SOLEND (lending backfill), and a tardis cefi venue sample — how many
      `SOURCE_RETURNED_ZERO`/`empty_confirmed` rows exist that may be mislabeled outages. Record counts here as the
      fix's before-state.
- [ ] [DATA] P0. v9 `schema_version` distribution while in the buckets (unblocks audit item (g)/v9 BLOCKED-DATA): actual
      % at v9 per `market-data-tick-<ag>` `_index`.
- [ ] [DATA] P0. Raw tradfi ohlcv column-name census (`ts_event` vs `timestamp`) — decisive for the bar-edge METASTABLE
      P0 (`bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 1); sample N files per day-range across the databento
      corpus.

## Phase 1 — P0 swallow fixes (one QG-sweep batch; per-unit commits via quickmerge)

- [ ] [CODE] P0. `lending_indices_handler.py:768` — narrow the blanket except: re-raise transport
      (`ClientError/OSError/TimeoutError`) alongside `SubgraphSchemaError`; re-raise non-schema GraphQL body errors
      (`:1182-1194`); move the GCS upload (`:741`) out of the swallowed try. — market-tick-data-service
- [ ] [CODE] P0. `solana_defi_handler.py:932,973,1051,1120` — remove/re-raise the four collector swallows so failures
      escape to `:457 record_failed`. — market-tick-data-service
- [ ] [CODE] P0. `oracle_prices_handler.py:828-832,948-960` — Pyth helpers raise on transport + non-200 (keep historical
      404 → `[]`), engaging the dead `:757 record_failed` branch. — market-tick-data-service
- [ ] [CODE] P0. `liquidations_handler.py` — re-raise transport in `_fetch_morpho_*` (`:781-787`) AND remove
      `aiohttp.ClientError/OSError/SchemaValidationError` from the `:510-517` catch (all protocols). —
      market-tick-data-service
- [ ] [CODE] P0. `perp_funding_handler.py:963-969,1017-1023` — `_query_gmx_*` re-raise transport (reserve `None` for
      schema-unavailable); `record_failed` when both variants None instead of `:887 rows or []`. —
      market-tick-data-service
- [ ] [CODE] P0. `tardis_adapter.py` — 404-vs-error split: streaming `:833-835` + bulk `:2313-2327` + legacy `:906-908`
      RAISE on non-404/non-401 `TardisHTTPError` so §6A runner-exception → `record_failed` (`:1784-1789`) fires;
      optionally wire 429/5xx retry (config `retry_status_codes` currently dead on the path). — market-tick-data-service
- [ ] [CODE] P0. `engine/orchestrator.py:3141` — pass `asset_group=ag` to the chain-bundle `record_captured_from_counts`
      (mirror prediction `:3302`; do NOT pass `latency_source`). — market-tick-data-service

## Phase 2 — P1 follow-ons

- [ ] [CODE] P1. Solend chart backfill error accounting: `_solana_defi_fetch.py:248-253` + duplicate
      `solana_defi_handler.py:~1353-1364` + `fetch_phoenix:453` — errors>0 ∧ rows==0 → raise; partial → surface via
      warning/cluster validation. — market-tick-data-service
- [ ] [CODE] P1. `umi_tick_provider.py:429-430` FX per-ticker Yahoo swallow → route to `failed_shards`/AFF; add AFF
      emission to `yahoo_finance_adapter` error paths. — market-tick-data-service
- [ ] [CODE] P1. Kalshi CF-11 plumbing before the venue is ever enabled (mirror Polymarket `failed_tickers_out` +
      `failed_per_dt` + AFF). — market-tick-data-service
- [ ] [UTL] P1. Source on NON-captured rows: add `source=` kwarg to `record_empty:2197`/`record_failed:2413` + stamp in
      `_record_status:3447-3574`; then the MTDS `DefiManifestRecorder` pass-through one-liner. — unified-trading-library

## Success criteria

- Every Phase-1 site: transport error → `attempted_failed` row (unit test per site pinning the routing); zero
  fetch-error paths returning honest-empty shapes.
- MTDS `quality-gates.sh` exit 0 on the batch; shipped via `quickmerge --agent --files`.
- Phase-0 before-state counts recorded here; after the backfill re-runs, the mislabeled cells get relabeled (tracked as
  a follow-up data fix, not silently).

## Progress journal

- 2026-06-10: plan created from the re-verified audit (slot-4). Phase 0 starting.
