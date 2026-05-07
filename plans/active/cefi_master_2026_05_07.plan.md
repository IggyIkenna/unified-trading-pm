---
name: cefi-master
slug: cefi_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P0
phase: pending_approval
domain: cefi
asset_group: cefi
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - cefi_venue_universe_expansion_2026_05_01
  - cefi_tradfi_tick_data_backfill_2026_04_10 # CeFi half (TradFi half goes to tradfi_master)
  - market_tick_data_to_100pct_2026_05_05 # CeFi slice (per asset_group split)
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
  - shard_granularity_ssot_propagation_2026_05_06
  - data_status_multi_axis_shard_propagation_2026_05_06
---

# CeFi Master — asset_group umbrella

## Scope

Single source of truth for **CeFi asset_group** work toward live DeFi 2026-05-23. Covers:

- **4 CeFi perp venues live by May 23**: Bybit, Deribit, Binance, OKX. Hedge legs for the 2 DeFi archetypes
  (`carry_staked_basis` + `leveraged_funding_arb`).
- **CeFi extended tick-data backfill**: Bitfinex, Bitget, Kraken (Tardis-served).
- **CeFi options + futures bundles**: DERIBIT options/futures, BINANCE-FUTURES perps.
- **MTDS coverage to 100% for the CeFi slice** (per-instrument-per-day for spot/perp; bundled-by-root for
  options/futures).

**Not covered here** (out of asset_group scope):

- TradFi (CME / CBOE / NYSE / NASDAQ) → see `tradfi_master_2026_05_07.plan.md`.
- DeFi DEX perps (Hyperliquid / Aster / Lighter / Extended / Pacifica) → see `defi_master_2026_05_07.plan.md`. Note:
  Lighter / Extended / Pacifica were originally scoped under `cefi_venue_universe_expansion` as "DEX perps" but they're
  DeFi by asset_group.
- Sports / Predictions → see `sports_master_2026_05_07.plan.md` / `predictions_master_2026_05_07.plan.md`.
- Cross-cutting concerns (writegate, shard-granularity, data-status, instruments+MTDS infra) → see master plan + the
  named cross-cutting plans.

## Current state (2026-05-07)

- **4 perp venues**: 4/4 instrument-coverage live; tick-data backfill in progress per `cefi_tradfi_tick_data_backfill`
  (15/24 done across CeFi+TradFi).
- **Extended backfill venues** (Bitfinex / Bitget / Kraken): NOT yet wired into UAC + Tardis adapter
  (cefi_venue_universe_expansion 0/20).
- **DERIBIT options/futures bundles**: pre-2024 backfill running; 2025/2026 light-VM relaunched 2026-05-06.
- **MTDS CeFi shards**: deployment-UI shows partial coverage; full audit pending.

## Critical path

| Workstream                                                | Status                            | Source plan / commit                                                 |
| --------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------- |
| 4 CeFi perp venues live (Bybit / Deribit / Binance / OKX) | INSTRUMENTS LIVE; tick-data ~60%  | `cefi_tradfi_tick_data_backfill`                                     |
| DERIBIT options + futures bundles backfilled to genesis   | 2024 done; 2025/2026 in flight    | `cefi_tradfi_tick_data_backfill` (2025/2026 VMs running 2026-05-06+) |
| BINANCE-FUTURES perps backfill                            | partial; manifest cleanup pending | `cefi_tradfi_tick_data_backfill`                                     |
| Bitfinex / Bitget / Kraken Tardis venues                  | NOT STARTED                       | `cefi_venue_universe_expansion`                                      |
| CeFi MTDS shards to 100%                                  | partial                           | `market_tick_data_to_100pct` (CeFi slice)                            |
| Phantom-audit + manifest-rebuild for CeFi                 | partial — TradFi port pending     | `cefi_tradfi_tick_data_backfill` (CeFi half)                         |

## Consolidated todos (lifted from folded children)

### From `cefi_venue_universe_expansion_2026_05_01` — Bitfinex / Bitget / Kraken Tardis venues

- [ ] [AGENT] P0. UAC `unified_api_contracts/registry/venue_mapping.py` — extend `all_tardis_exchanges` with `bitfinex`,
      `bitget`, `kraken`.
- [ ] [AGENT] P0. UAC `registry/market_data_categories.py` — extend `VENUES_BY_ASSET_GROUP['cefi']` with the 3 venues.
- [ ] [AGENT] P0. UAC `canonical/coverage_starts.py` — add launch dates: `BITFINEX 2013-04-15`, `BITGET 2018-07-30`,
      `KRAKEN 2011-07-28`.
- [ ] [AGENT] P0. UAC `registry/capability_declarations/_cefi.py` — add `SourceCapability` declarations per venue.
- [ ] [AGENT] P0. MTDS `adapters/umi_tick_provider.py` — update `_TARDIS_CEFI_VENUES` to include the 3 new venues.
- [ ] [AGENT] P0. Coverage-start clipping per-venue in adapter pre-fetch (existing pattern).
- [ ] [SCRIPT] P0. `scripts/vm/launch-cefi-sharded-backfill.sh` — add symbol lists for each new venue.
- [ ] [SCRIPT] P0. Add `launch_cefi_shard` calls per venue × heavy/light × year-shard (2020..today).
- [ ] [SCRIPT] P0. Refresh CEFI tarball: `bash scripts/vm/create-code-tarballs.sh --asset-group CEFI` then launch
      backfill VMs.
- [ ] [VERIFY] P0. After 2-4h: query manifest for new venues; confirm `captured` rows for spot + futures.
- [ ] [VERIFY] P0. Sanity-check parquets at canonical paths.
- [ ] [QG] P0. Quality gates + quickmerge on UAC + MTDS changes.

### From `cefi_tradfi_tick_data_backfill_2026_04_10` — CeFi half (DERIBIT options + BINANCE-FUTURES + phantom audit)

- [ ] [AGENT] P0. Verify MTDS orchestrator handles all target data_types (options_chain, derivative_ticker, perpetual)
      for DERIBIT + BINANCE-FUTURES.
- [ ] [AGENT] P0. Verify instruments-service has historical DERIBIT options/futures and BINANCE-FUTURES perps for target
      windows.
- [ ] [SCRIPT] P0. VM launch script for DERIBIT options backfill (instrument_type=options_chain).
- [ ] [SCRIPT] P0. VM launch script for DERIBIT futures backfill (instrument_type=futures_chain).
- [ ] [SCRIPT] P0. VM launch script for BINANCE-FUTURES perps backfill (instrument_type=perpetual).
- [ ] [SCRIPT] P1. Launch all 3 CeFi VMs in parallel + monitor via GCS logs.
- [ ] [SCRIPT] P2. Verify manifest entries appear in deployment-ui data status tab.
- [ ] [AGENT] P0. Port phantom-audit + manifest-rebuild scripts to CeFi (current scripts target sports/multi-asset).
- [ ] [AGENT] P0. Monitor + reap zombie VMs (`gcloud compute instances list` + parallel-delete pattern per workspace
      VM-naming convention).
- [ ] [AGENT] P0. Post-drain: `/api/data-status/turbo?service=market-tick-data-service&force=true` → CeFi completion_pct
      ≥ target.
- [ ] [AGENT] P0. Record final capture_status distribution + VM rc count (rc=0 vs rc=137 vs other).
- [ ] [SCRIPT] P2. Spot-check: download 3 random days of DERIBIT options; verify options_chain greeks/IVs populated.
- [ ] [SCRIPT] P2. Spot-check: download 1 day of BINANCE-FUTURES perps; verify funding + open_interest populated.

### From `market_tick_data_to_100pct_2026_05_05` — CeFi slice (per asset_group split)

CeFi-specific MTDS-to-100% todos lifted at the asset_group split commit. Tracks CeFi spot/perp/options/futures coverage
percentage in the deployment-ui data-status panel toward 100%.

- [ ] [AGENT] P1. After CeFi backfill VMs drain, run data-status rollup
      (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api`) and confirm CeFi shards count against
      expected.
- [ ] [AGENT] P1. Per-venue completion %: Bybit, Deribit, Binance, OKX, Bitfinex, Bitget, Kraken, BINANCE-FUTURES.
      Surface gaps to operator via deployment-ui drill-down.
- [ ] [AGENT] P1. Cleanup stale CEFI manifest rows post-MVP scope reduction.

### Bitfinex / Bitget / Kraken — extended (post-cutover)

These were originally scoped in `cefi_venue_universe_expansion`; deferring expansion-only items past May 23 is fine
because the 4 critical-path perp venues (Bybit / Deribit / Binance / OKX) are already live.

- [ ] [DEFERRED-POST-CUTOVER] P2. Extended / Pacifica / Lighter DEX-perp venues — these are DeFi asset_group, not CeFi.
      Move-out into `defi_master_2026_05_07.plan.md`.

## Anti-patterns + workspace-rule cross-references

- **Live = batch**: same code path; only fill source differs (cefi_master shares the unified pipeline; no live-only
  data_types). See CLAUDE.md "Live = batch" rule.
- **Honest absence**: tail-end days of a venue's launch use `record_empty(empty_confirmed)`. No NaN-placeholder rows.
  See `codex/02-data/honest-absence-downstream-handling.md`.
- **Manifest concurrency**: backfill VMs use per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=<unique>`).
- **VM naming**: prefixes per CLAUDE.md "VM Naming Convention" (`cefi-{venue}-{flavor}-{ts}`); add new prefix to
  `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` before launch.

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Write-gate cluster:
  [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](./writegate_honest_coverage_endtoend_2026_05_06.plan.md).
- Shard granularity:
  [`shard_granularity_ssot_propagation_2026_05_06.plan.md`](./shard_granularity_ssot_propagation_2026_05_06.plan.md).
- Sibling asset_group umbrellas: `defi_master_2026_05_07`, `tradfi_master_2026_05_07`, `sports_master_2026_05_07`,
  `predictions_master_2026_05_07`.

## Folded plans (archived 2026-05-07)

- `cefi_venue_universe_expansion_2026_05_01.plan.md` — Tardis venues + DEX perps; CeFi todos lifted above; DEX perp
  todos move to `defi_master`.
- `cefi_tradfi_tick_data_backfill_2026_04_10.plan.md` — CeFi half lifted above; TradFi half lifted into `tradfi_master`.
- `market_tick_data_to_100pct_2026_05_05.plan.md` (CeFi slice) — full plan archived after splitting per asset_group;
  CeFi slice is in this umbrella; other slices in their respective asset_group umbrellas.
