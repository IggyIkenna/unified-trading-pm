---
name: data_status_drilldown_shard_atom_alignment_2026_05_07
overview:
  Realign the deployment-ui data-status drill-down hierarchy + per-shard download with the codex shard-key matrix per
  asset_group; add MTDS CLI flags for per-shard targeting + recovery.
type: code
epic: epic-deployment
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: deployment-api
    code: C2
    deployment: none
    business: none
  - repo: deployment-ui
    code: C2
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C2
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C2
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C2
    deployment: none
    business: none
depends_on:
  - data_status_multi_axis_shard_propagation_2026_05_06.plan.md
todos: []
isProject: false
related:
  - data_status_multi_axis_shard_propagation_2026_05_06.plan.md
  - shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
  - writegate_honest_coverage_endtoend_2026_05_06.plan.md
---

# Data-status drill-down + MTDS CLI shard-atom alignment

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
  `YYYY-MM-DD` launch date. ~50 LOC + 30 LOC unit tests. Initial seed: AAVEV3 (Arbitrum 2022-03-16, Optimism 2022-08-04,
  Polygon 2022-03-16, Avalanche 2022-03-16, Base 2023-08-09, Ethereum 2022-03-14), AAVEV2 (Ethereum 2020-12-01),
  UNISWAPV3 (Ethereum 2021-05-04, Arbitrum 2021-08-31, Optimism 2021-12-16, Polygon 2021-12-21, Base 2023-08-09), CURVE
  (Ethereum 2020-01-19), COMPOUND (Ethereum 2018-09-27), LIDO (Ethereum 2020-12-19), JITO (Solana 2022-08-15), MARINADE
  (Solana 2021-08-02), ROCKETPOOL (Ethereum 2021-11-08), JUPITER (Solana 2024-01-31), RAYDIUM (Solana 2021-02-21).
  Greenfield additions populate as adapters land.
- New helper `get_protocol_launch_date(chain: str, protocol: str) -> str | None` mirroring `get_chain_genesis_date`.
  Returns `None` if not declared (caller falls back to `CHAIN_GENESIS_DATES` for the chain).
- Sanity test: every `(chain, protocol)` pair declared in `VENUES_BY_ASSET_GROUP["defi"]` has a `PROTOCOL_LAUNCH_DATES`
  entry OR an explicit `# pending-investigation` skip list (so adding a new protocol without a launch date is a CI
  failure, not silent NaN).

**unified-trading-pm** (codex docs + plan):

- This plan moves to `plans/active/` after user approval.
- `codex/02-data/availability-manifest-and-data-status.md` — new section "Drill-down hierarchy = shard atom" pointing at
  the new endpoint.
- `codex/06-coding-standards/cli-convention.md` — extend with the `--shard-key` convention so other services follow the
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

- [ ] [audit] P0. Confirm the codex shard-atom matrix is current. Cross-check against `CLAUDE.md` "Per-asset-group
      shard-key matrix" + the writer contracts in `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`. If any
      drift, raise to user — do NOT silently proceed.
- [ ] [audit] P0. Read 5 sample on-disk parquets (one per asset_group) + confirm the canonical path matches the shard
      atom. Reference paths in `codex/02-data/per-category-bucket-layouts.md`.

### Phase 1 — deployment-api hierarchical drill-down endpoint

- [x] [unified-api-contracts] P0 (NEW 2026-05-07 — shipped UAC@0169a0a). Land
      `PROTOCOL_LAUNCH_DATES: dict[tuple[str, str], str]` SSOT in `unified_api_contracts/registry/chain_env.py`. Helper
      `get_protocol_launch_date(chain, protocol) -> str | None`. Sanity test (14/14 pass): every `ALL_DEFI_VENUES` entry
      that resolves to a `(chain, protocol)` pair has a launch date OR is on `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`
      skip list (33 pairs pending follow-up; 41 declared). Composition contract `max(chain_genesis, protocol_launch)`
      documented + tested.
- [ ] [deployment-api] P0 (NEW 2026-05-07 — supersedes the date-only chain math). Rewrite `_build_chain_breakdown()` in
      `data_status_service.py:4827-4886` to count true leaf shards. Numerator =
      `len(filtered[(filtered.chain == chain) & (filtered.capture_status == "captured")])`; denominator = expected
      `(chain, venue, data_type, instrument_id_or_protocol_id, day)` tuple count from the per-asset_group expected
      universe. Use `get_protocol_launch_date(chain, protocol)` to clip the per-protocol denominator. Existing
      `dates_found` / `dates_expected` keys stay in the payload for backward-compat but ALSO emit `shards_found` /
      `shards_expected` as the canonical fields. UI consumers switch to the new fields in Phase 2. Add unit tests
      asserting `shards_expected` ≫ `dates_expected` for ARBITRUM-AAVEV3 (5 data_types × ~1100 days ≈ 5500 vs ~1100
      dates).
- [ ] [deployment-api] P0 (NEW 2026-05-07). Wire `_mtds_expected_dates_cached` (`data_status_service.py:1164`) to use
      `max(chain_genesis, protocol_launch_date)` — pre-protocol-launch days clip exactly like pre-chain-genesis already
      does. Unit test: AAVEV3-ARBITRUM 2021-08-31 → 2022-03-15 returns empty expected (chain genesis but protocol not
      launched yet); 2022-03-16 onward returns expected dates.
- [ ] [deployment-api] P0. New service method
      `data_status_drilldown.get_hierarchical_drilldown(service, asset_group,     window_start, window_end)` returning a
      tree shaped per the codex shard atom. Each leaf has
      `{captured, empty_confirmed, attempted_failed,     row_key, download_url}`. Reads the manifest once via
      `read_availability_index`; groups by axis order from
      `data_status_axis_matrix.SHARD_AXIS_MATRIX[service][asset_group]`.
- [ ] [deployment-api] P0. New route `GET /api/data-status/drilldown/{service}/{asset_group}` accepts `start_date` /
      `end_date` / optional `chain` / `venue` / `data_type` / `instrument_type` / `instrument_id` filters for lazy-load.
      Returns partial tree shaped by the requested filter depth.
- [ ] [deployment-api] P0. Adjust `download-csv` / `download-shard-csv` to accept the full leaf row_key (currently
      hard-stops at venue, day). Resolve the row_key to the canonical parquet path via UAC SSOT
      (per-category-bucket-layouts), stream parquet OR CSV.
- [ ] [deployment-api] P0. Unit tests: hierarchical tree shape per asset_group; lazy-load filter at each depth;
      per-shard download correctness for bundled (options_chain) vs per-instrument shards.

### Phase 2 — deployment-ui hierarchical drill-down component

- [ ] [deployment-ui] P0 (NEW 2026-05-07). Replace the chain-row label `"shards"` with the new canonical fields: consume
      `shards_found` / `shards_expected` from the Phase 1 rewrite (and the asset-group header reads the same fields).
      The "X dates missing" sub-pill stays date-scoped and uses `dates_found` / `dates_expected` so both signals are
      visible. Search the UI for hardcoded "shards" / "dates" mislabels — `DataStatusTab.tsx`,
      `BreakdownsAccordion.tsx`, `CategoryHeader.tsx` — and align label-to-field exactly. Visual smoke: ARBITRUM should
      now read e.g. `5500 / 8400 shards (65%)` not `32/54 shards (59%)`, AND `1084 dates missing` becomes whatever the
      new chain-clipped denominator yields (e.g. ~200 instead of 1084).
- [ ] [deployment-ui] P0. New `HierarchicalShardDrilldown.tsx` component. Recursive: each level renders a list of
      expandable items; on expand fires `getHierarchicalDrilldown(...)` with the next-level filter set. Empty levels (no
      captured + no expected) collapse to "no data" badge.
- [ ] [deployment-ui] P0. `DataStatusTab.tsx` — under each asset_group panel, below the existing `BreakdownsAccordion`,
      render the new component. Default-collapsed; lazy-load on first expand.
- [ ] [deployment-ui] P0. Per-leaf SmartDownloadButton — passes the full row_key to the download endpoint.
      Capture-status banner already in place from Phase 3 (multi-axis plan); no change to that surface.
- [ ] [deployment-ui] P0. Visual smoke: walk every (service, asset_group) pair the SSOT declares; confirm the drill-down
      depth matches the shard atom. Empty-state placeholders where writers haven't shipped.

### Phase 3 — Per-shard download + missing surfacing

- [ ] [deployment-api] P1. `/coverage-summary` extended with leaf-shard counts (rolled up per axis level) so the UI can
      show "23 missing instrument-shards" inside the BTCUSDT branch instead of just at the venue level.
- [ ] [deployment-ui] P1. Deploy-Missing button on a leaf node fires a surgical CLI invocation with `--shard-key=...`
      (Phase 4 supplies the flag). Pre-Phase-4 fallback: degrades to the existing service-wide invocation with a banner
      explaining "fine-grained recovery requires MTDS shard-key flag".

### Phase 4 — MTDS CLI shard-targeting

- [ ] [market-tick-data-service] P1. Add `--instrument-type` (singular, filter) to `cli/main.py` argument parser. Today
      there's `--instrument-ids` (plural) but no `--instrument-type` for filter.
- [ ] [market-tick-data-service] P1. Add `--root` for bundled-chain data_types (options_chain, futures_chain) — re-runs
      only the named root.
- [ ] [market-tick-data-service] P1. Add `--day` / `--date` for single-day mode — fetch only this date for this shard.
- [ ] [market-tick-data-service] P1. Add `--shard-key` parser. Pipe- delimited form
      `asset_group|venue|data_type|instrument_type|     instrument_id_or_root|day`. Splits into individual flags before
      handler dispatch — handlers don't need to know about `--shard-key`, just consume the unpacked flags.
- [ ] [market-tick-data-service] P1. Per-handler audit: each handler under `cli/handlers/` honors the new flags. Verify
      `tick_data_handler` / `liquidations_handler` / `dex_pools_handler` / `lending_indices_handler` /
      `dex_swaps_handler` / `gas_fees_handler` / `lst_rates_handler` / `oracle_prices_handler` / `perp_funding_handler`
      / `evm_defi_handler` / `solana_defi_handler` / `eigenlayer_rewards_handler`.

### Phase 5 — Codex docs + plan close

- [ ] [unified-trading-pm] P2. `codex/02-data/availability-manifest-and-data-status.md` new section "Drill-down
      hierarchy = shard atom" with the matrix from this plan.
- [ ] [unified-trading-pm] P2. `codex/06-coding-standards/cli-convention.md` add the `--shard-key` convention.
- [ ] [unified-trading-pm] P2. Plan flips to closeout once Phases 1–4 ship + cross-service QG passes on the affected
      repos.

## Success criteria

- **Code gates (per repo):** `bash scripts/quality-gates.sh` passes on deployment-api, deployment-ui,
  market-tick-data-service.
- **Test gates:** new hierarchical-drilldown unit tests pass; UI vitest covers every (service, asset_group) pair the
  SSOT declares; MTDS CLI flag tests pass.
- **Visual gate:** screenshots from a follow-up Playwright walk show TradFi CME → ohlcv_1m → futures → ESH4 → 2024-01-15
  → download (the user's specific TradFi concern); DeFi ARBITRUM → AAVEV3 → lending_indices → 2024-03-04 → download (the
  user's specific DeFi concern); CeFi BITFINEX-SPOT → trades → SPOT_PAIR → BTCUSDT → 2024-03-05 → download.
- **Surgical recovery gate:** clicking "Deploy Missing" on a single leaf in the data-status panel fires an MTDS VM with
  `--shard-key=...` that re-runs ONLY that shard (verify by inspecting the VM startup script metadata).

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

## References

- `unified-trading-pm/cursor-configs/CLAUDE.md` § "Per-asset-group shard-key matrix"
- `unified-trading-pm/plans/active/data_status_multi_axis_shard_propagation_2026_05_06.plan.md` (companion plan —
  display axes + breakdowns, this plan handles drill-down depth)
- `unified-trading-pm/plans/active/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` (writer-side compliance —
  drives the ground-truth shard atoms)
- `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
- `unified-trading-pm/codex/02-data/per-category-bucket-layouts.md`
- Reference incidents: TradFi MVP partial-bundle (2026-05-06) — operator couldn't tell which ES.OPT cluster was missing
  because the panel collapsed across cluster membership; same shape as the TradFi screenshot driving this plan.
