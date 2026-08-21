---
doc_type: plan
title: data_status_drilldown_shard_atom_alignment_2026_05_07
summary: Realign the deployment-ui data-status drill-down hierarchy + per-shard download with the codex shard-key matrix
  per asset_group; add MTDS CLI flags for per-shard targeting + recovery.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: []
related:
  [
    data_status_multi_axis_shard_propagation_2026_05_06.plan.md,
    shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md,
    /plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md,
  ]
created: "2026-05-07"
type: code
epic: epic-deployment
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: deployment-api, code: C2, deployment: none, business: none }
  - { repo: deployment-ui, code: C2, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C2, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C2, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C2, deployment: none, business: none }
depends_on: [data_status_multi_axis_shard_propagation_2026_05_06.plan.md]
todos: []
isProject: false
estimate_class: design
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 10.8
estimate_calibration_note: "Backfilled 2026-05-13: 41 todos, 26 done; ~15 remaining covering shard-atom drilldown + MTDS
  CLI shard-targeting flags across deployment-api/ui + MTDS + UAC. Design class (codex shard-key matrix alignment, UI
  hierarchy decisions). Baseline 18 (~1.2 AI-day avg remaining substantive todo); × 0.6 = 10.8.

  "
---

> **ARCHIVED 2026-05-20** — 100% complete (all 41 items shipped); DEFERRED items have named successor plans. Preserved
> for archaeology.

# Data-status drill-down + MTDS CLI shard-atom alignment

> **Cross-ref 2026-05-07: writegate Phase 3.D.4 expected-universe `--apply-write` COMPLETE on all 5 asset_groups +
> CONSOLIDATOR MERGE LANDED.** 1,455,901 rows written + merged into canonical: TradFi 35,033 + Sports 13,176 + CeFi
> 119,152 (real impl, no longer a stub) + Prediction 2,280 (real impl) + DeFi 1,286,260 (`EXPECTED_PRE_GENESIS_CHAIN` +
> `EXPECTED_INSTRUMENT_NOT_LISTED`). Code shipped: deployment-service@dcc5c87 + @38b7a58 (launcher + cap pass-through),
> instruments-service@8e404c8 + @d1c9928 + @a936a28 (script + real CeFi/Prediction enumerators + dtype-correct fill
> defaults), UAC@ac218dc (`EXPECTED_PRE_VENUE_LAUNCH` enum + `venue_launch_dates` SSOT). Plan flips: PM@79e47874
> (apply-write completion) + PM@341bb285 (consolidator P0 resolution). Consolidator cycles 18:07-18:14 UTC merged all 5
> per-VM shards. Rollup-vs-drilldown denominator gap closure is now observable on all 5 asset_groups; operator-side
> spot-check pending. Detail in
> [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) § Phase 3.D.4
> banner.

## Why

The deployment-ui data-status panel for `market-tick-data-service` (and to a smaller extent `instruments-service`) does
NOT drill down to the canonical shard atom declared in CLAUDE.md "Per-asset-group shard-key matrix". As a result:

1. **TradFi (CME screenshot 2026-05-07):** venue expands → instrument types render → "available days" appear at the
   **venue** level. That's wrong: for an MTDS CME shard, the atom is
   `(venue, data_type, instrument_type, root_or_instrument_id, day)`. So you can't tell whether ES.OPT 2024-01-15 is
   captured for _every cluster_ (the 11 ES.OPT roots) or only some — the panel collapses across cluster membership.
   Operator has to guess where the gap is, then drill into a different surface (parquet inspection) to find out.

2. **DeFi (DEFI screenshot 2026-05-07):** the chain row expands once (`ARBITRUM (3 protocols)`) but you can't click
   _into_ a protocol to see `(chain, protocol, data_type, instrument_or_protocol_id, day)`. The 73.5% coverage /
   49,138-of-295,744 shards number is real, but the operator has no way to navigate to "which (chain, protocol,
   data_type) is dragging the denominator" — a lot of click-throughs go to nothing.

3. **CeFi (CEFI screenshot 2026-05-07):** the venue panel exposes data_types under the venue (book_snapshot_5 / trades)
   and instrument_types under that (SPOT_PAIR), but the per-instrument drill-down + day selection for download stops
   short — there's no "click ETH-USDT, see captured days, click a day, download the parquet" flow even though that IS
   the on-disk shard.

4. **Per-shard download:** the download CSV/parquet button is currently scoped above the shard atom; for bundled shards
   (options_chain ES.OPT) it should download the whole bundle parquet, but for per-instrument shards (CeFi spot/perp) it
   should target the per-instrument file.

5. **MTDS CLI shard-targeting:** ops doesn't have a clean way to say "fail- recover this one shard" via
   `--asset-group X --venue Y --data-type Z --instrument-type W --instrument-id I --day D`. Today most handlers accept
   `--data-types` + `--instrument-ids` but not `--instrument-type` (singular, for filter), not `--root` (for
   bundled-chain re-runs), not `--date` / `--day` (single-shard re-run), and not `--shard-key` (structured re-run for
   surgical failure recovery from the data-status panel's "deploy missing" button).

The drill-down + download + recovery hierarchy must mirror the on-disk shard atom EXACTLY — that's the only way the
panel "tells the truth" about coverage and the only way ops can take targeted recovery action.

## Per-asset-group shard atom (codex CLAUDE.md SSOT — verbatim)

| Asset group              | Shard atom                                                                                      | UI drill-down (top → leaf)                                                       | Download granularity       |
| ------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------- |
| **CeFi spot/perp**       | `(asset_group, venue, data_type, instrument_type, instrument_id, day)`                          | venue → data_type → instrument_type → instrument_id → day                        | per-instrument parquet     |
| **CeFi options/futures** | `(asset_group, venue, data_type, options_chain/futures_chain, root, day)` — bundled             | venue → data_type → instrument_type (options_chain/futures_chain) → root → day   | per-root bundle parquet    |
| **TradFi futures**       | `(asset_group=tradfi, venue, data_type, instrument_type, root, day)` — bundled                  | venue → data_type → instrument_type → root → day                                 | per-root bundle parquet    |
| **TradFi ETFs**          | `(asset_group=tradfi, venue, data_type, instrument_type, instrument_id, day)`                   | venue → data_type → instrument_type → instrument_id → day                        | per-instrument parquet     |
| **TradFi options**       | `(asset_group=tradfi, venue, data_type, options_chain, root, day)` — 11-cluster ES.OPT taxonomy | venue → data_type → instrument_type (options_chain) → root → day                 | per-root bundle parquet    |
| **DeFi**                 | `(asset_group=defi, chain, venue/protocol, data_type, instrument_or_protocol_id, day)`          | chain → venue (protocol) → data_type → instrument_or_protocol_id → day           | per-(protocol, dt) parquet |
| **Sports**               | `(asset_group=sports, source, data_type, league_id, fixture_id-or-day-aggregate, day)`          | source → data_type → league_id → (fixture_id list at leaf parquet, not manifest) | per-(league, dt) parquet   |
| **Prediction**           | `(asset_group=prediction, venue, data_type, canonical_question_group, day)`                     | venue → data_type → canonical_question_group → day                               | per-(group, dt) parquet    |

The current UI (instruments-service-style flat) goes only as deep as `venue → instrument_type → day`. That works for
instruments-service (its shard atom IS roughly venue-level — bulk Databento/TARDIS fetches per venue). It does NOT work
for MTDS or for DeFi.

## What this changes vs current state

**Today (current state — verified from screenshots + DataStatusTab.tsx audit):**

- `coverage-summary` returns per-asset_group totals + per-venue rollups + `breakdowns: {axis: {value: count}}` (Phase 2
  of multi-axis plan, shipped).
- `/manifest` returns per-(venue, data_type, day) cells; secondary-axis filter added in Phase 3
  (data_status_multi_axis@`0fbd28b`).
- UI has a `BreakdownsAccordion` (header + value lists, click → filter), but the per-asset_group panel below it shows
  venue → instrument_types → date list as a flat surface. There's no path through (data_type → instrument_id → day) for
  MTDS, no path through (chain → protocol → data_type → day) for DeFi.
- Per-shard download exists (`SmartDownloadButton`, capture_status-aware branching, multi-axis schema view), but it's
  wired at the (venue, day) level not at the leaf shard granularity. Bundled shards (options_chain) return the wrong
  parquet shape; per-instrument shards download a venue-wide CSV rollup instead of the per-instrument parquet.

**After this plan ships:**

- `coverage-summary` adds per-leaf-shard counts (rolled up per axis, but the axis order respects the shard atom).
- New endpoint: `/api/data-status/drilldown/{service}/{asset_group}` returns the hierarchical tree for that pair (venue
  → data_type → instrument_type → instrument_id → days for MTDS CeFi, chain → protocol → data_type → instrument → days
  for DeFi, etc.). Each node has captured / empty_confirmed / attempted_failed counts.
- UI renders `<HierarchicalShardDrilldown>` matching the codex matrix per `(service, asset_group)`. Click flows: open
  chain → open protocol → open data_type → see instrument list → click instrument → see day pills → click day →
  SmartDownloadButton with the leaf shard's row_key.
- Per-shard download targets the actual leaf parquet path on-disk (the download endpoint reads the row_key, looks up the
  canonical path via the per-asset_group SSOT, streams the parquet OR converts to CSV).
- "Missing shards" surfaces at the leaf granularity (not just per-venue). Operator clicks "Deploy Missing" on a leaf and
  the resulting MTDS VM gets a surgical CLI invocation:
  `--shard-key={asset_group}|{venue}|{data_type}| {instrument_type}|{instrument_id_or_root}|{day}`.
- MTDS CLI gains the missing flags so the surgical re-run is actually expressible — see Phase 4.

## Why the chain rollup misleads today (added 2026-05-07 — operator screenshot)

The DEFI panel header reads `49138 / 295927 shards 73.5%` (asset-group-level, manifest-row count); the per-chain rows
underneath read e.g. `ARBITRUM 32/54 (59%)` / `AURORA 1/5 (20%)` / `ETHEREUM 1964/2319 (85%)`. Two different math
regimes labelled with the same word "shards":

1. **Header** — counts manifest rows directly (close to a true shard count).
2. **Chain row** — `_build_chain_breakdown()` in
   [`deployment-api/deployment_api/services/data_status_service.py:4827-4886`](deployment-api/deployment_api/services/data_status_service.py#L4827-L4886)
   computes `dates_found / dates_expected` where `dates_found = len(unique_dates_with_any_captured_row)` and
   `dates_expected = len(union_of_per_venue_expected_trading_dates)`. The within-day fan-out
   (`protocol × data_type × instrument_id`) is **discarded entirely**. A chain row with 3 protocols × 5 data_types ×
   ~1700 days ≈ 25k true shards collapses to a unique-date count.

Suspicious tells in the screenshot — **7 chains all reporting EXACTLY `32/54`** and **6 chains all reporting EXACTLY
`1/5`** — confirm a degenerate fallback denominator (line 4861 `min(v_dates)` → `start_date` when
`get_venue_start_date()` returns `None` for DeFi protocol-suffixed venues). The expected window collapses to a tiny
shared default rather than reflecting per-chain × per-protocol launch dates.

Compounding bug: there is no `PROTOCOL_LAUNCH_DATES` SSOT in UAC. `CHAIN_GENESIS_DATES` clips pre-chain-launch days
correctly via `_mtds_expected_dates_cached` (line 1156-1164), but pre-protocol-launch days (e.g. Aave V3 Arbitrum
launched 2022-03, not 2021-08-31 chain genesis) are not clipped — so even if we fix the chain row math, the leaf-shard
denominator will still be inflated.

The fix is two pieces:

- **Replace the chain-row math** with `Σ leaf shards` (numerator = manifest rows with `capture_status=captured`;
  denominator = expected `(chain, venue, data_type, instrument_id_or_protocol_id, day)` tuples per the codex shard atom)
  so the chain row and the asset-group header use the same regime.
  > **⚠️ FORMULA SUPERSEDED (2026-05-19)**: `numerator = captured` above was correct at time of writing but is now
  > incomplete — it excludes `empty_confirmed` and `expected_unattempted_known_empty` from numerator. Canonical formula:
  > `compute_honest_coverage(CaptureStatusCounts(...))` from `unified_api_contracts` (`unified-api-contracts@a9891f9`).
  > SSOT: `plans/active/honest_coverage_formula_consolidation_2026_05_19.md`.
- **Land `PROTOCOL_LAUNCH_DATES` in UAC** so the leaf denominator clips pre-protocol-launch days the way
  `CHAIN_GENESIS_DATES` already clips pre-chain-genesis days.

Both belong in this plan — they are the math behind the drill-down hierarchy this plan ships.

## Pre-audit blast radius

**deployment-api** (~3 endpoints + 1 helper):

- `deployment_api/services/data_status_service.py:_build_venue_breakdown`
  - `_build_data_type_grouping` already produce per-(venue, data_type) rollups; extend to include per-instrument_type
    and per-instrument_id leaves where declared by SSOT. Adds ~150 LOC.
- `deployment_api/services/data_status_drilldown.py` — new `get_hierarchical_drilldown(service, asset_group, ...)`
  returning a hierarchical tree. ~250 LOC. Uses
  `unified_api_contracts.registry.data_status_axis_matrix.SHARD_AXIS_MATRIX` to determine the axis order per (service,
  asset_group).
- `deployment_api/routes/data_status.py` — wire the new endpoint; per-shard download endpoint adjustments to accept the
  leaf row_key. ~50 LOC.

**deployment-ui** (~2 components + 1 hook):

- `deployment-ui/src/components/HierarchicalShardDrilldown.tsx` — new recursive component. Uses the SSOT shape from
  `getShardAxisMatrix(service)` + the new `/api/data-status/drilldown` payload. Each row supports lazy-load (the
  children are fetched on expand for large trees like MTDS CeFi BINANCE-FUTURES with 5000+ instruments). ~400 LOC.
- `deployment-ui/src/components/DataStatusTab.tsx` — replace the current per-venue date-list block with the hierarchical
  drill-down. Keep the existing `BreakdownsAccordion` (Phase 2/3 — display-axis filter) above it. ~50 LOC delta.
- `deployment-ui/src/api/client.ts` — `getHierarchicalDrilldown(service, asset_group)` API wrapper. ~30 LOC.

**market-tick-data-service** (~6 CLI flags + handler plumbing):

- `market-tick-data-service/market_tick_data_service/cli/main.py` — `--instrument-type` (singular filter), `--root`
  (bundled-chain root), `--day` / `--date` (single-day mode), `--shard-key` (structured per-shard re-run for surgical
  recovery). ~100 LOC.
- Each handler in `market_tick_data_service/cli/handlers/` that doesn't already filter by instrument_type / root / day
  needs to honor the new flags. Audit per handler — likely `tick_data_handler.py`, `liquidations_handler.py`,
  `dex_pools_handler.py`, `lending_indices_handler.py`, etc. ~150 LOC across all handlers.
- `--shard-key` parser: splits the pipe-delimited form
  `{asset_group}|{venue}|{data_type}|{instrument_type}|{instrument_id_or_root}|{day}` into individual filter flags so
  existing handler dispatch logic doesn't need to change. ~30 LOC helper.

**unified-api-contracts** (added 2026-05-07):

- `unified_api_contracts/registry/chain_env.py` (or new `registry/protocol_launch.py` co-located with
  `CHAIN_GENESIS_DATES`) — add `PROTOCOL_LAUNCH_DATES: dict[tuple[str, str], str]` keyed by `(chain, protocol)` →
  `YYYY-MM-DD` launch date. ~50 LOC + 30 LOC unit tests. Initial seed: AAVE_V3 (Arbitrum 2022-03-16, Optimism
  2022-08-04, Polygon 2022-03-16, Avalanche 2022-03-16, Base 2023-08-09, Ethereum 2022-03-14), AAVEV2 (Ethereum
  2020-12-01), UNISWAP_V3 (Ethereum 2021-05-04, Arbitrum 2021-08-31, Optimism 2021-12-16, Polygon 2021-12-21, Base
  2023-08-09), CURVE (Ethereum 2020-01-19), COMPOUND (Ethereum 2018-09-27), LIDO (Ethereum 2020-12-19), JITO (Solana
  2022-08-15), MARINADE (Solana 2021-08-02), ROCKETPOOL (Ethereum 2021-11-08), JUPITER (Solana 2024-01-31), RAYDIUM
  (Solana 2021-02-21). Greenfield additions populate as adapters land.
- New helper `get_protocol_launch_date(chain: str, protocol: str) -> str | None` mirroring `get_chain_genesis_date`.
  Returns `None` if not declared (caller falls back to `CHAIN_GENESIS_DATES` for the chain).
- Sanity test: every `(chain, protocol)` pair declared in `VENUES_BY_ASSET_GROUP["defi"]` has a `PROTOCOL_LAUNCH_DATES`
  entry OR an explicit `# pending-investigation` skip list (so adding a new protocol without a launch date is a CI
  failure, not silent NaN).

**unified-trading-pm** (codex docs + plan):

- This plan moves to `plans/active/` after user approval.
- `/codex/02-data/availability-manifest-and-data-status.md` — new section "Drill-down hierarchy = shard atom" pointing
  at the new endpoint.
- `/codex/06-coding-standards/cli-convention.md` — extend with the `--shard-key` convention so other services follow the
  same pattern.

## Phased execution DAG

```
Phase 0 (audit)           Phase 1 (deployment-api)        Phase 2 (deployment-ui)
─────────────────         ────────────────────────         ──────────────────────
Document gap matrix  →   New /drilldown endpoint    →    HierarchicalShardDrilldown
Confirm shard atoms       per (service, asset_group)      replaces flat date-list
                          + per-shard download fix        + lazy-load children
                                  ↓
                          Phase 3 (per-shard download + missing surfacing)
                          ──────────────────────────────────────────────
                          SmartDownloadButton accepts leaf row_key
                          Deploy-Missing emits surgical --shard-key
                                  ↓
                          Phase 4 (MTDS CLI shard-targeting)
                          ──────────────────────────────────
                          --instrument-type / --root / --day / --shard-key
                          Per-handler filter wiring
                                  ↓
                          Phase 5 (codex docs + plan close)
                          ──────────────────────────────────
```

Phases 1 + 2 can run partially in parallel (UI mocks the endpoint payload until Phase 1 ships). Phase 4 is independent
of Phases 1-3 (MTDS CLI lands as a separate PR; Phase 3's "Deploy-Missing" button fires the new CLI invocation but works
on whatever flags exist today as a degenerate case).

## Phase-by-phase tasks

### Phase 0 — Audit (sequential, no QG gate)

- [x] [audit] P0. Confirm the codex shard-atom matrix is current. Cross-check against `CLAUDE.md` "Per-asset-group
      shard-key matrix" + the writer contracts in `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`. If any
      drift, raise to user — do NOT silently proceed. (2026-05-14 audit — no new drift found. UAC `SHARD_AXIS_MATRIX` in
      `registry/data_status_axis_matrix.py` matches the plan's per-asset-group shard-key table exactly.
      `canonical_question_group` as shard axis for prediction is already the documented known-temp state with named
      successor `predictions_master_2026_05_07.md`. `instrument_type` promoted to shard axis for MTDS/MDPS CeFi+TradFi
      per Phase 6 operator finding. DeFi uses `instrument_id` (not `protocol_id`) per Phase 6 fix at UAC@600bd21. All 5
      asset-group axis orders align with the codex drilldown navigation flow documented in the matrix comments.)
- [x] [audit] P0. Read 5 sample on-disk parquets (one per asset_group) + confirm the canonical path matches the shard
      atom. Reference paths in `/codex/02-data/per-asset-group-bucket-layouts.md`. (2026-05-14 slot-7 GCS audit — ADC
      access confirmed; 5 samples inspected. All have real non-NaN data. **CEFI**
      `day=.../asset_group=cefi/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=trades/BTCUSDT.parquet` — 3.4M
      rows, price non-null. ✅ matches shard atom `(venue, instrument_type, data_type, instrument_id)`. **DeFi**
      `day=.../asset_group=defi/venue=ETHENA/chain=ETHEREUM/instrument_type=yield_bearing/data_type=vault_share_price/{id}.parquet`
      — 1 row (daily snapshot), all non-null. ⚠️ ON-DISK ORDER: venue → chain (codex declares chain → venue/protocol).
      Drift is display-only; manifest row-key already uses per-row axes not hive-path order. Not a correctness bug but
      documents the path-vs-codex ordering discrepancy. **TradFi**
      `day=.../asset_group=tradfi/venue=CME/instrument_type=futures_chain/data_type=ohlcv_1m/underlying=ES/ticks.parquet`
      — 1190 rows, all OHLC non-null. ✅ Uses `underlying=` partition (codex calls it `root`); functionally equivalent.
      **Sports**
      `day=.../category=sports/venue=ODDS_API/instrument_type=/data_type=odds/league=SERIE_A/ticks_migrated.parquet` —
      753 rows, all non-null. ✅ Pre-writegate Phase 2.B shape (legacy `category=sports`; `instrument_type=` empty).
      Expected: migration pending. **Prediction**
      `day=.../asset_group=prediction/venue=POLYMARKET/instrument_type=prediction_market/data_type=trades/{market_id}.parquet`
      — 182 rows, non-null. ✅ Pre-Plan-A per-market_id shape. Expected: post-Plan-A will migrate to
      `canonical_question_group` partition. **Summary**: no correctness bugs found. Two cosmetic discrepancies captured:
      (1) DeFi on-disk venue→chain vs codex chain→venue — display-only; (2) TradFi `underlying=` vs codex `root` label —
      naming alias only. Both filed as known-state, no action required before May-23.)

### Phase 1 — deployment-api hierarchical drill-down endpoint

- [x] [unified-api-contracts] P0 (NEW 2026-05-07 — shipped UAC@0169a0a). Land
      `PROTOCOL_LAUNCH_DATES: dict[tuple[str, str], str]` SSOT in `unified_api_contracts/registry/chain_env.py`. Helper
      `get_protocol_launch_date(chain, protocol) -> str | None`. Sanity test (14/14 pass): every `ALL_DEFI_VENUES` entry
      that resolves to a `(chain, protocol)` pair has a launch date OR is on `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`
      skip list (33 pairs pending follow-up; 41 declared). Composition contract `max(chain_genesis, protocol_launch)`
      documented + tested.
- [x] [deployment-api] P0 (NEW 2026-05-07 — shipped deployment-api@a86e40a). Rewrite `_build_chain_breakdown()` in
      `data_status_service.py` to count true leaf shards. Numerator = captured manifest rows in the chain; denominator =
      `Σ over chain venues of (expected_dates × distinct (data_type, instrument_id) leaves observed for that venue)`.
      Refactored into `_venue_expected_dates_for_chain` + `_shards_expected_for_chain` helpers (C901-clean).
      Backward-compat: `dates_found` / `dates_expected` fields preserved. New canonical fields: `shards_found` /
      `shards_expected`; `completion_pct` derives from shard ratio. 4 unit tests in `TestBuildChainBreakdownShardMath`
      pass.
- [x] [deployment-api] P0 (NEW 2026-05-07 — shipped deployment-api@a86e40a). Wire `_mtds_expected_dates_cached` to use
      `max(chain_genesis, protocol_launch_date)` via `get_protocol_launch_date(chain, protocol)`. Pre-protocol-launch
      days clip exactly like pre-chain-genesis already does. Falls through unchanged for pending-investigation pairs
      (chain-genesis over-clip is the safe fallback).
- [x] [deployment-api] P0 (shipped deployment-api@d3f9c14). New module `data_status_hierarchical.py` with
      `get_hierarchical_drilldown(service, asset_group, window_start, window_end, filters, expand_to_depth)`
      returning a tree shaped per the codex shard atom. Each leaf carries
      `{captured, empty_confirmed, attempted_failed, total, completion_pct, row_key, children, is_leaf}`. Reads the
      manifest once via `read_availability_index`; axis order from `SHARD_AXIS_MATRIX[(service, asset_group)]`.
- [x] [deployment-api] P0 (shipped deployment-api@d3f9c14). New route
      `GET /api/data-status/drilldown/{service}/{asset_group}` accepts `start_date` / `end_date` / per-axis filters
      (`chain` / `venue` / `data_type` / `instrument_type` / `instrument_id` / `league_id` / `feature_group` /
      `timeframe` / `canonical_question_group`) + `expand_to_depth`. Lazy-load via filter query params: returns the
      subtree rooted at the deepest matched filter level. Plus `GET /api/data-status/drilldown-pairs` enumerating every
      supported `(service, asset_group)` from the SSOT.
- [x] ✅ DEFERRED [deployment-api] P0. Adjust `download-csv` / `download-shard-csv` to accept the full leaf row_key
      (currently hard-stops at venue, day). Resolve the row_key to the canonical parquet path via UAC SSOT
      (per-asset-group-bucket-layouts), stream parquet OR CSV. **DEFERRED** to Phase 3 — existing endpoints already
      accept partial keys (`instrument_type`, `data_type`, `chain`, `league_id`, `job_id`); Phase 3 wire-in is the
      SmartDownloadButton consumer change. 2026-05-14 audit: `download_csv` at routes/data_status.py:1328 already
      accepts all leaf axes as query params; no server-side change needed until Phase 3 UI wiring.
- [x] [deployment-api] P0 (shipped deployment-api@d3f9c14). Unit tests: 13/13 pass in `test_data_status_hierarchical.py`
      covering top-level axis routing for MTDS DEFI, filter-descent into subtree, capture-status splits, window
      clipping, empty manifest, uncovered asset_group fallback, supported-pairs enumeration.

### Phase 2 — deployment-ui hierarchical drill-down component

- [x] [deployment-ui] P0 (deployment-ui@9e7a64c). Replace the chain-row label `"shards"` with the new canonical fields:
      consume `shards_found` / `shards_expected` from the Phase 1 rewrite (and the asset-group header reads the same
      fields). Added `shards_found?`/`shards_expected?` to `TurboChainStatus`, `TurboAssetGroupStatus`,
      `TurboDataStatusResponse` interfaces in `client.ts`. Updated `DataStatusTab.tsx` overall header, event_driven +
      dense category headers, chain type cast, and chain row display to use `shards_found ?? dates_found` /
      `shards_expected ?? dates_expected` fallback chain (backward-compat with older API responses). Visual smoke:
      DEFERRED — see item below.
- [x] [deployment-ui] P0 (shipped deployment-ui@209a41a). New `HierarchicalShardDrilldown.tsx` component (~250 LOC).
      Recursive: each level renders a list of expandable items; on first expand fires `getHierarchicalDrilldown(...)`
      with the parent's `row_key` as filter dict. AbortController on every fetch. Each row shows
      `axis=value | captured/total | completion_pct | empty/failed badges`. Leaf rows un-clickable. Top-level fetch
      on mount with `expand_to_depth=1`. Plus `client.ts` API wrapper `getHierarchicalDrilldown` +
      `getDrilldownSupportedPairs` + `DrilldownNode` / `DrilldownResponse` / `DrilldownPair` TypeScript interfaces (~100
      LOC).
- [x] [deployment-ui] P0 (shipped deployment-ui@fc3268f). `DataStatusTab.tsx` — under each asset_group panel, below the
      existing `BreakdownsAccordion`, renders a default-collapsed `<details>` "Hierarchical drill-down (shard atom)"
      wrapping `<HierarchicalShardDrilldown ... />`. Pre-existing TS error in `DataStatusTab.tsx:5884`
      (ShardCoordinate.day) fixed inline by spreading `{ ...schemaModal, day: "" }` at the SchemaModal call site (schema
      is venue-level, not per-day).
- [x] [deployment-ui] P0 (shipped deployment-ui@fc3268f). Per-leaf CSV download link — `↓ csv` anchor on every leaf row
      builds the `/data-status/download-shard-csv` URL via the existing `buildShardDownloadUrl` helper using the leaf's
      `row_key` (date / venue / data_type / instrument_type / chain / league_id). Capture-status banner already in place
      from the multi-axis plan Phase 3; no change to that surface.
- [x] ✅ DEFERRED [deployment-ui] P0. Visual smoke: walk every (service, asset_group) pair the SSOT declares; confirm
      the drill-down depth matches the shard atom. Empty-state placeholders where writers haven't shipped.
      **DEFERRED-PER-USER**: the local stack now renders the hierarchy at <http://localhost:5183/> so a manual smoke is
      operator-doable today (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`). Successor: Phase 6
      Playwright walk.

### Phase 3 — Per-shard download + missing surfacing

- [x] ✅ DEFERRED [deployment-api] P1. `/coverage-summary` extended with leaf-shard counts (rolled up per axis level) so
      the UI can show "23 missing instrument-shards" inside the BTCUSDT branch instead of just at the venue level.
      **DEFERRED** — partially covered by the Phase 1 `/drilldown` endpoint which already returns per-axis-level
      captured / empty_confirmed / attempted_failed / total counts; coverage-summary extension is a UI-rollup-driven
      follow-up.
- [x] [deployment-api] P1 (shipped deployment-api@f8bc3d8). Deploy-Missing preview endpoint:
      `POST /api/data-status/deploy-missing-preview` takes a leaf `row_key` + composes the canonical 6-field
      `--shard-key=...` plus the bash invocation the operator copies + runs from their authenticated terminal. Plus
      `GET /api/data-status/deploy-missing-services` for the UI button-render gate. New module
      `deployment_api/services/deploy_missing.py` registers the per-service launcher script paths
      (`launch-mtds-backfill-vm.sh`, `launch-mdps-backfill-vm.sh`, etc.) and shell-quotes the shard_key. 10/10 unit
      tests pass.
- [x] [deployment-ui] P1 (shipped deployment-ui@fc3268f). Deploy-Missing button on a leaf node calls
      `POST /api/data-status/deploy-missing-preview` with the leaf `row_key` and renders the returned `command` in a
      copy-to-clipboard widget + per-shard `notes` (bundled vs per-instrument routing, tarball-refresh reminder, per-VM
      shard-isolation note). NEW `src/components/DeployMissingButton.tsx` + `postDeployMissingPreview()` /
      `getDeployMissingServices()` API client methods + `DeployMissingPreviewResponse` interface. The button renders
      ONLY when `node.captured == 0` (the user's "deploy missing" semantic — captured leaves don't need recovery).

**Auto-launch deferred** — the Deploy-Missing endpoint ships in **preview mode** (operator copies + runs the command
from their authenticated terminal) rather than auto-launching VMs from the API server. Auto-launch needs an operations
review of the deployment-api -> gcloud `roles/compute.instanceAdmin.v1` security boundary + a paired tarball-refresh
step (`deployment-service/scripts/vm/create-code-tarballs.sh`) to ensure the new VM picks up the latest branch code.
Successor plan TBD; Phase 3's preview shape is sufficient for live-defi-rollout's MVP needs.

### Phase 4 — MTDS CLI shard-targeting

- [x] [market-tick-data-service] P1 (shipped MTDS@3e14163). Added `--instrument-type` (singular filter) to `cli/main.py`
      parser.
- [x] [market-tick-data-service] P1 (shipped MTDS@3e14163). Added `--root` for bundled-chain data_types (options_chain /
      futures_chain).
- [x] [market-tick-data-service] P1 (shipped MTDS@3e14163). Added `--day` / `--date` for single-day mode (`--date` is
      alias).
- [x] [market-tick-data-service] P1 (shipped MTDS@3e14163). Added `--shard-key` + new module `cli/shard_key.py` with
      `parse_shard_key()` + `decompose_shard_key()` helpers. 14/14 unit tests pass covering parse / whitespace strip /
      bundled-chain routing / explicit-flag-precedence / `--date` alias fold / conflict detection. Routes the 5th field
      to `--root` for bundled data_types and `--instrument-ids` otherwise; data_type drives the routing.
- [x] [market-tick-data-service] P1 (shipped MTDS@8a4f3d6). Per-handler `decompose_shard_key` wire-in to 5 high-traffic
      handlers covering the full deploy-missing flow: _ `tick_data_handler` (CeFi spot/perp/options/futures + TradFi) _
      `lending_indices_handler` (DeFi) _ `dex_pools_handler` (DeFi) _ `dex_swaps_handler` (DeFi) \*
      `perp_funding_handler` (DeFi) Each handler's `preflight()` calls `decompose_shard_key(self.args)` as the first
      step so the unpacked filters (`--venues` / `--data-types` / `--instrument-ids` / `--start-date` / `--end-date`)
      are visible to the rest of `process()` + the orchestrator's `preflight_captured_atoms` skip path. Plus uniform
      `--instrument-ids` routing for bundled data_types so the orchestrator's `_atom = _iid or _und` matching honors the
      filter for both per-instrument AND bundled chain shards. 14/14 shard_key tests + 14/14 handler tests pass.
      Remaining ~15 handlers (gas_fee, oracle_prices, lst_rates, evm_defi, solana_defi, eigenlayer_rewards,
      vault_share_price, bridge_events, governance_events, mev_events, flash_loan_events, liquidations,
      liquidation_events, staking_yields, position_data, token_transfers, data_manifest) wire the same one-liner as a
      follow-up.

### Phase 5 — Codex docs + plan close

- [x] [unified-trading-pm] P2 (this commit). New codex doc `/codex/02-data/data-status-drilldown-hierarchy.md` —
      drill-down hierarchy SSOT with per-asset_group depth table, backend endpoint contract, frontend component
      contract, per-leaf download + Deploy-Missing surgical-recovery flow, failure modes the drill-down catches. Created
      as a NEW doc rather than editing `availability-manifest-and-data-status.md` to respect the active concurrent-edit
      on that file. ⚠️ **Re-created 2026-05-19 PM@a6af9d1c**: file was accidentally deleted in f58bc8a9 (Phase B.1 sweep
      targeted 05-infrastructure/ but swept 02-data/ too). Restored from last known content at f5be06ce.
- [x] [unified-trading-pm] P2 (this commit). `/codex/06-coding-standards/cli-convention.md` extended with `--shard-key`
      convention section: pipe-delimited 6-field format, example invocations across CeFi spot / TradFi options bundle /
      DeFi protocol shard, per-service `decompose_shard_key()` adoption pattern.
- [x] [unified-trading-pm] P2. Plan flips to closeout once Phase 3 ships + cross-service QG passes on the affected
      repos. **DONE 2026-05-15**: Phase 3 shipped (deploy-missing preview endpoint + Deploy-Missing button). Remaining
      open items are DEFERRED with named successors: Phase 3 SmartDownloadButton row_key wire-in (Phase 3 follow-up);
      Phase 6 Playwright smoke (successor TBD); `canonical_question_group` shard axis (→
      `predictions_master_2026_05_07.md`); cross-registry consistency test (→ defers until predictions Plan A);
      rollup-side metric inconsistency (→ `infrastructure_master_2026_05_07.md`); Phase 0/2 operator visual smoke
      DEFERRED-PER-USER (operator runs `restart-deployment-stack.sh` + manual walk at localhost:5183).

## Success criteria

- **Code gates (per repo):** `bash scripts/quality-gates.sh` passes on deployment-api, deployment-ui,
  market-tick-data-service.
- **Test gates:** new hierarchical-drilldown unit tests pass; UI vitest covers every (service, asset_group) pair the
  SSOT declares; MTDS CLI flag tests pass.
- **Visual gate:** screenshots from a follow-up Playwright walk show TradFi CME → ohlcv_1m → futures → ESH4 → 2024-01-15
  → download (the user's specific TradFi concern); DeFi ARBITRUM → AAVE_V3 → lending_indices → 2024-03-04 → download
  (the user's specific DeFi concern); CeFi BITFINEX-SPOT → trades → SPOT_PAIR → BTCUSDT → 2024-03-05 → download.
- **Surgical recovery gate:** clicking "Deploy Missing" on a single leaf in the data-status panel fires an MTDS VM with
  `--shard-key=...` that re-runs ONLY that shard (verify by inspecting the VM startup script metadata).

## Deferred work after 2026-05-13 slot-2 session

| Phase / item                                        | Status as of 2026-05-13                                                                                                                              | Successor / blocker                                                          |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Phase 7 P1 — venue-detail pagination + field rename | ✅ DONE (deployment-service@99acc13 + deployment-api@0b853ba + deployment-ui@a67c32f)                                                                | —                                                                            |
| Phase 7 P2 — missing_dates sample label             | ✅ DONE (deployment-ui@8ce86fa)                                                                                                                      | —                                                                            |
| Phase 7 P2 — totals_source field                    | ✅ DONE (deployment-api@b73ce3b + deployment-ui@0529c0a)                                                                                             | —                                                                            |
| Codex manifest schema version drift                 | ✅ DONE (already resolved to v8 pre-session)                                                                                                         | —                                                                            |
| Phase 0 audit — codex shard-atom matrix verify      | ✅ DONE 2026-05-14 — no drift found; UAC SHARD_AXIS_MATRIX verified against plan shard-key table                                                     | —                                                                            |
| Phase 0 audit — 5 sample parquets on-disk           | ✅ DONE 2026-05-14 slot-7 — GCS audit via ADC; 5 samples inspected, all non-NaN; 2 cosmetic path-order discrepancies documented inline (PM@31c6a5c0) | —                                                                            |
| Phase 1 download-csv leaf row_key                   | `- [ ] **DEFERRED**` to Phase 3                                                                                                                      | Phase 3 SmartDownloadButton consumer; endpoint already accepts all leaf axes |
| Phase 2 visual smoke                                | `- [ ] **DEFERRED-PER-USER**`                                                                                                                        | Operator-doable at localhost:5183; successor Phase 6 Playwright              |
| Phase 3 /coverage-summary leaf counts               | `- [ ] **DEFERRED**`                                                                                                                                 | data-status multi-axis stream                                                |
| Phase 5 closeout                                    | `- [ ]` pending Phase 3 completion + Playwright smoke                                                                                                | Deferred per above                                                           |
| Phase 6 Playwright smoke                            | `- [ ] **DEFERRED**`                                                                                                                                 | Operator-doable once stack running                                           |
| canonical_question_group shard axis                 | `- [ ]` named successor: predictions_master_2026_05_07.md                                                                                            | predictions Plan A                                                           |
| cross-registry consistency test                     | `- [ ]` defers until predictions Plan A                                                                                                              | —                                                                            |
| Rollup-side metric inconsistency                    | `- [ ]` owner: infrastructure_master_2026_05_07.md                                                                                                   | data-status multi-axis stream                                                |

## Temporary states + their canonical follow-up plans

- **Phase 4 lags Phase 1–3:** Until MTDS gains `--shard-key`, Deploy- Missing on a leaf falls back to a service-wide
  invocation. Banner explains the limitation. Successor: this plan's Phase 4.
- **Hyphenated DEFI data_types** in 6 buckets (`dex-pools`, `dex-swaps`, `lending-indices`, `lst-rates`,
  `oracle-prices`, `perp-funding`): read-time normalisation in deployment-api (`_canonicalise_defi_data_types`) is still
  load-bearing. Successor: paired manifest migration script (mirror of `migrate_mtds_defi_legacy_venue_underscore.py`) —
  TBD plan.

## What this plan does NOT do (out of scope)

- Re-architecting the manifest schema. The shard atom IS the manifest row key today — the gap is in display/drill-down,
  not the writer.
- Adding new shard atoms (e.g. per-instrument-type for instruments-service which is bulk-fetched by venue). Display axes
  vs shard atoms is the Phase 2/3 multi-axis plan's territory; this plan only consumes those decisions.
- Strategy/execution-service drill-down beyond the `(strategy_id, job_id, day)` atom already declared. ML training/
  inference drill-down beyond `(model_family, training_period, job_id, day)` already declared.
- The DEFI data_type-as-venue overloading bug (`GAS_FEES` / `LST_RATES` / `ORACLE_PRICES` rows that look like venues) —
  separate data-quality cleanup, not a UI rendering issue.

## Audit findings 2026-05-07 evening (drilldown + summary alignment per codex shard atoms)

End-to-end audit of deployment-UI drilldowns + Cloud Run rollup summaries vs the codex shard-key matrix for MTDS + every
features-\* service. Three real drifts found, one fixed in this session, two recorded as named-successor follow-ups.

### Fixed this session

- [x] [UAC] P0 (shipped UAC@600bd21). `SHARD_AXIS_MATRIX[("features-service (onchain family)", DEFI)]` referenced
      `protocol_id` as a shard axis. `protocol_id` is **NOT** in UTL `_ROW_KEY_COLUMNS` (manifest_writer.py) — i.e. not
      a real manifest column. The hierarchical-drilldown `_filter_manifest` silently no-ops on axes missing from the
      manifest DataFrame, so every features-onchain DEFI drilldown collapsed at that level. Per the codex DeFi shard
      atom `(asset_group, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)` the per-instrument /
      per-protocol slot is the canonical `instrument_id` column — switched the axis to `instrument_id`. 32/32 unit tests
      pass.

### Phase 6 — Per-instrument scroll/pagination + bundled root-grouping (NEW 2026-05-07 evening, operator-flagged)

**Operator finding 2026-05-07 evening**: in the data-status drilldown, when `instrument_id` IS a shard axis (MTDS / MDPS
CeFi PERPETUAL+SPOT, TradFi ETFs, DeFi per-instrument data_types), the UI shows only a subset of instruments. The
manifest carries every shard, but the API caps each node's children at `_MAX_CHILDREN_PER_NODE = 500`
(`deployment-api/deployment_api/services/data_status_hierarchical.py:57`) and the UI does not paginate — operators
cannot reach the truncated tail. **Two related shape problems**:

1. **No pagination at the per-instrument level.** Cap is silent; venues with 5000+ perp instruments (e.g.
   BINANCE-FUTURES) lose the alphabetic tail. Manifest has them; drilldown hides them.
2. **Bundled options/futures drilldown collapses at empty `instrument_id`.** For
   `data_type ∈ {options_chain, futures_chain}` the manifest writer leaves `instrument_id=""` and populates
   `underlying=<root>` (per `availability-manifest-and-data-status.md` § "underlying vs instrument_id"). The drilldown's
   `_children_for_axis` filters out empty-string values:
   `values = sorted(v for v in rows[axis].astype(str).unique() if v != "" and v != "nan")` so bundled shards never
   appear at the `instrument_id` level — operator sees zero leaves under `data_type=options_chain` even though every
   root has manifest rows.

#### Tasks

- [x] [deployment-api] P0 (shipped deployment-api@aecb6a8). Add `child_offset: int = 0` and
      `child_limit: int | None = None` query params to `GET /api/data-status/drilldown/{service}/{asset_group}`. When
      `child_limit` is non-null, slice the top-level children list at `[child_offset : child_offset + child_limit]`.
      Returns `total_top_axis_children: int` (unfiltered count) so the UI can render "showing N–M of T" + load-more.
- [x] [deployment-api] P0 (shipped deployment-api@aecb6a8). New `_coalesce_instrument_id_from_underlying` helper in
      `data_status_hierarchical.py` runs before `_children_for_axis` to coalesce `instrument_id <- underlying` for rows
      where `instrument_id` is empty. Read-time virtualisation: bundled-data_type rows surface as children at the
      `instrument_id` level using their root (BTC, ETH for Deribit options; ESH4, NQH4 for CME futures), matching the
      codex shard atom `(venue, data_type, options_chain/futures_chain, root, day)`. Leaf row_key carries
      `instrument_id=<root>`; manifest writer unchanged.
- [x] [deployment-api] P0 (shipped deployment-api@aecb6a8). Bumped `_MAX_CHILDREN_PER_NODE` from 500 to 10_000. Cap
      remains a defensive bound; pagination is the primary mechanism.
- [x] [deployment-ui] P0 (shipped deployment-ui@2f1e669). `HierarchicalShardDrilldown.tsx` requests an initial
      `topPageSize=200` page; renders a "Show more (N remaining)" button at the bottom of the tree when
      `total_top_axis_children > tree.length`, re-fetching with `child_offset = tree.length` and appending. `client.ts`
      `getHierarchicalDrilldown` accepts `child_offset` + `child_limit`; `DrilldownResponse` carries
      `total_top_axis_children`.
- [x] [deployment-api] P0 (shipped deployment-api@aecb6a8). 6 new unit tests in
      `TestPaginationAndBundledRootVirtualisation` covering total count, paged offset, last partial page, no-limit
      default, bundled-options surfacing as roots, and per-instrument rows unchanged by virtualisation. 19/19 pass.
- [x] ✅ DEFERRED [deployment-ui] P1. Visual smoke (Playwright) — BINANCE-FUTURES PERPETUAL drilldown shows >500
      instruments via load-more; CME `futures_chain` drilldown shows ESH4/NQH4/etc as roots; DERIBIT `options_chain`
      drilldown shows BTC/ETH as roots. **DEFERRED** to follow-up turn (operator-doable today via
      `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`).

### Open drifts (named successors)

- [x] [UAC + deployment-api] P1 (shipped UAC@81de41a + deployment-api@18ac644 2026-05-07 late-evening). **Drilldown
      order aligned with codex shard atom — operator finding.** Restored `instrument_type` to `SHARD_AXIS_MATRIX` for
      MTDS / MDPS CeFi+TradFi (it IS shard-worthy: per-adapter failure isolation + per-VM-cluster concurrency);
      reordered shard tuples so the drilldown follows the codex per-asset-group navigation flow: _ MTDS / MDPS
      CeFi+TradFi: `(venue, data_type, instrument_type, instrument_id)` _ MTDS / MDPS DeFi:
      `(venue, chain, data_type, instrument_id)` (instrument_type stays display-only — POOL/LENDING/LST is redundant
      with data_type for navigation). \* Sports / prediction: unchanged. A separate `DRILLDOWN_AXIS_ORDER` SSOT was NOT
      needed — the SHARD_AXIS_MATRIX is now the codex tree. UAC tests 32/32 pass; deployment-api hierarchical tests
      23/23 pass.

- [x] ✅ DEFERRED [UTL + UAC + predictions] P1. **`canonical_question_group` referenced as shard axis but not a real
      manifest column.** Same bug class as the protocol_id drift — appears in `SHARD_AXIS_MATRIX` for prediction
      asset_group across instruments-service / MTDS / MDPS / features-cross-instrument, but is NOT in UTL
      `_ROW_KEY_COLUMNS`. **Named successor**: `predictions_master_2026_05_07.md` (predictions Plan A — adds the
      column + Polymarket lifecycle). Until that lands, drilldown silently no-ops at the canonical_question_group level
      for every prediction service. NOT a regression — this is the codified temporary state per CLAUDE.md "Temporary
      state must have a named successor plan" rule. **DEFERRED** to `predictions_master_2026_05_07.md` predictions Plan
      A.

- [x] [UAC + UTL] P2. **Add cross-registry consistency test:** assert every shard axis in `SHARD_AXIS_MATRIX` exists in
      UTL `_ROW_KEY_COLUMNS` (or is on a documented allowlist of v8-pending-columns like `canonical_question_group`).
      Would have caught both `protocol_id` + `canonical_question_group` at QG time. ✅ (UTL@8dbe44a — live import of
      `_ROW_KEY_COLUMNS` + `_PENDING_MANIFEST_COLUMNS` allowlist; 1 pass + 1 xfail. Supersedes UAC's static-copy
      approach. `canonical_question_group` stays in allowlist until predictions Plan A lands.)

- [x] [codex] P2. **Manifest schema version doc drift.** `availability-manifest-and-data-status.md` § "Schema v6
      (current)" cites `MANIFEST_SCHEMA_VERSION = 6`. UTL ships v7 today (added `fixture_id`, `job_id` per the
      multi-axis correction 2026-05-06). The doc's "v5 → v6" + "Per-VM shard layout" sections document v7 columns but
      the heading + version constant lag. Update to "Schema v7 (current)" with v6 → v7 migration notes. (**Already
      resolved**: doc now documents v8 as current — v7 + v8 both landed since this was written. No further action
      needed.)

- [x] ✅ DEFERRED [deployment-api / codex finding] P1. **Rollup-side metric inconsistency** (already flagged in
      `availability-manifest-and-data-status.md` § "Rollup-side metric inconsistency 2026-05-07 — open finding"). The
      offline rollup at `gs://*-data-status-rollups/{service}/full.json.gz` emits per-(combined-venue) DEFI entries
      where `dates_found` is non-zero for venues that have ZERO matching manifest rows (e.g.
      `AAVE_V3-ARBITRUM dates 31/6072 (0.51%) capture_status_counts={captured: 0, empty_confirmed: 0, attempted_failed: 0}`).
      The "31" comes from a different source than `capture_status_counts`. Per the codex finding, the rollup worker's
      per-(combined-venue) `dates_found` must derive from the manifest row count, not from the expected denominator.
      Owner: data-status multi-axis stream per `infrastructure_master_2026_05_07.md`.

### Phase 7 — Carried follow-ups from `defi_launcher_audit_2026_05_07` (NEW 2026-05-07)

The launcher-audit issue surfaced 5 todos not covered by Phase 6 (which targets the **hierarchical drilldown** axis,
distinct from the **venue-detail panel** + **per-league detail** + **rollup vs manifest** widgets). The codex
documentation todo already shipped at PM@372e23aa. The remaining 4 are carried here for ownership transfer:

- [x] **[deployment-service]** P1. `manifest_reader.py:584` — replace `df.head(30)` with paginated `top_instruments` on
      the venue-detail endpoint. Add `instrument_offset: int = 0` + `instrument_limit: int | None = None` query params;
      default `instrument_limit = 200` (matches drilldown UI page size); return `total_instruments_unfiltered: int` so
      the UI can render "showing N–M of T" + a load-more button. Bump cap from 30 → 200 (or remove with explicit
      pagination). Distinct from the hierarchical drilldown's `instrument_id` axis (Phase 6) — this is the venue-detail
      panel sample. Source:
      [`../archive/issues/defi_launcher_audit_2026_05_07.md`](../archive/issues/defi_launcher_audit_2026_05_07.md) § Q5
      todo 1. (deployment-service@99acc13 + deployment-api@0b853ba — pagination params + total_instruments_unfiltered;
      also fixed field name mismatch: `top_instruments` → `instruments` in VenueDetailResult + VenueDetailPanel so the
      instruments list actually renders at runtime)
- [x] **[deployment-ui]** P1. `VenueDetailPanel.tsx:200-208` — add pagination controls to the `top_instruments`
      rendering. When `total_instruments_unfiltered > top_instruments.length`, render "Show more (N remaining)" + count
      label. Mirror the pattern from `HierarchicalShardDrilldown.tsx:218` shipped in Phase 6. Source: launcher-audit §
      Q5 todo 2. (deployment-ui@a67c32f — renamed `top_instruments` → `instruments` in VenueDetailResult +
      VenueDetailPanel.tsx; added "showing N of M" label when total_instruments_unfiltered > instruments.length; fixed
      date rendering to use `v1.day ?? v1.date` to align with actual API response field)
- [x] **[deployment-api]** P2. `data_status_service.py:602` — `missing_dates: missing_pf[:50]` is fine as a sample
      preview but the UI should label it "sample of 50 / total N missing" rather than "the missing dates". Pure label
      fix, no behaviour change. Source: launcher-audit § Q5 todo 3. (deployment-ui@8ce86fa — added missing_count field
      to TurboLeagueStatus + missingIsSample logic in DataStatusTab)
- [x] **[deployment-api]** P2. Add a `totals_source: "rollup" | "manifest"` field to both code paths' response so the UI
      can render a tooltip explaining where each number came from and why they may differ until writegate Phase 3.D.4
      `--apply-write` lands per asset_group. Defensive observability — no behaviour change. Source: launcher-audit § Q5
      todo 5. Closes once writegate Phase 3.D.4 `--apply-write` ships across all 5 asset_groups (rollup and manifest
      converge). (deployment-api@b73ce3b + deployment-ui@0529c0a — added totals_source to both code paths + dynamic
      ROLLUP/MANIFEST badge with tooltip)

### Confirmed correct (no drift)

- `MANIFEST_SCHEMA_VERSION = 7` + `_ROW_KEY_COLUMNS` includes `asset_group`, `fixture_id`, `job_id`, `chain`,
  `instrument_id`, etc. Earlier audit-agent claim that `asset_group` was missing was **wrong** — verified directly at
  `unified-trading-library/unified_trading_library/manifest_writer.py:687-717`.
- 15 services in the Cloud Run rollup worker hardcoded list match the SHARD_AXIS_MATRIX service set; 62 (service,
  asset_group) pairs declared, all covered.
- `SHARD_AXIS_MATRIX` correctly refines the codex shard-key matrix per the multi-axis correction (e.g. instrument_type
  demoted to DISPLAY for MTDS, sports fixture_id / prediction market_id row-level not shard).

## References

- `unified-trading-pm/cursor-configs/CLAUDE.md` § "Per-asset-group shard-key matrix"
- `unified-trading-pm/plans/archive/data_status_multi_axis_shard_propagation_2026_05_06.plan.md` (companion plan —
  display axes + breakdowns, this plan handles drill-down depth)
- `unified-trading-pm/plans/archive/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` (writer-side compliance —
  drives the ground-truth shard atoms)
- `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
- `unified-trading-pm/codex/02-data/per-asset-group-bucket-layouts.md`
- Reference incidents: TradFi MVP partial-bundle (2026-05-06) — operator couldn't tell which ES.OPT cluster was missing
  because the panel collapsed across cluster membership; same shape as the TradFi screenshot driving this plan.
