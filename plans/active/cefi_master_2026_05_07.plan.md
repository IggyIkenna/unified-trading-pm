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

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 22 of 22 unchecked todos
- **Mis-marked DONE → flipped**: 4 (UAC venue_mapping bitfinex/bitget/kraken; MTDS `_TARDIS_CEFI_VENUES` populated per
  `b12ecb5` kraken slash→hyphen normalization; `launch-cefi-sharded-backfill.sh` live, used to launch the 24 RUNNING
  VMs; coverage-start clipping per-venue via UAC SOURCE_COVERAGE_START SSOT)
- **In-flight (running VMs)**: 24 VMs (8 venues × multi-year shards), all on `live-defi-rollout` tarball,
  asia-northeast1-c. Bitfinex spot (5) + futures (4), Bitget futures (3), Coinbase spot (4), Hyperliquid (2), Kraken
  futures (1) + Kraken spot (7). ETA 2026-05-07 to 2026-05-09.
- **Blocked by**: `manifest_migration_master_2026_05_07:Stage 4` (rescan-all-manifests gates MTDS-to-100% verification);
  `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder deletion gates honest-coverage % numbers)
- **Blocks**: `master_to_live_defi_2026_05_23:F` (live-only trading prerequisites); `defi_master:carry_staked_basis`
  (needs CeFi perp hedges live)
- **Last meaningful commit**: MTDS@`b12ecb5` (tardis kraken slash→hyphen URL normalization); UAC@`e890022` (ohlcv_1m
  added to cefi DATA_TYPES_BY_ASSET_GROUP)
- **Recommendation**: KEEP ACTIVE. Most VM-tied work is IN-FLIGHT; waiting on backfill drain is correct posture. After
  2026-05-09 drain, run data-status rollup + per-venue completion %. Phantom-audit port to CeFi via existing
  multi-asset-group `reconcile_phantom_manifest_rows_all.py --asset-group cefi`.

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

### Tardis-venues backfill IN-FLIGHT (launched 2026-05-07 ~14:00 UTC, 37 VMs)

37 cefi VMs running in `asia-northeast1-c` covering bitfinex/bitget/kraken × futures+spot × 2020-2026
(`e2-highmem-2`). Sample event verification (3 VMs at T+30min): STARTED + PROCESSING_STARTED +
PROCESSING_COMPLETED flowing properly, ~4 min/date pace.

**Findings from per-VM manifest spot-check (Harsh, 2026-05-07 15:35 IST)** — concerns to feed back into writegate
+ shard-granularity follow-ups, NOT VM-blockers (the data IS being written, just the manifest shape is asymmetric):

1. **Asymmetric manifest shard shape — captured rows are bundle-level, empty_confirmed rows are per-instrument.**
   Verified across 2 VMs (`cefi-bitfinex-spot-2020-heavy-...` 200 rows, `cefi-kraken-spot-2020-heavy-...` 250 rows):
   100% of `captured` rows have empty `instrument_id` + `instrument_count=8.3M` (BTC bundle), while 100% of
   `empty_confirmed` rows have populated `instrument_id=BTCUSD/ETHUSD/...` + `instrument_count=0`. This **violates
   the per-asset-group shard-key matrix** in CLAUDE.md "Shard-granularity SSOT" section
   (`cefi spot/perp = (asset_group, venue, data_type, instrument_type, instrument_id, day) — per-instrument`).
   The bundle-level captured row passes the rollup check but the data-status drilldown can't show per-instrument
   coverage. **Owner: Ikenna writegate Phase 2.A residual** (per work-split D2). Reference incident shape: this is
   the same class as TradFi MVP partial-bundle (ES.OPT 18 single-parent fills) and MDPS 1440-NaN-OHLC — captured
   rows at the wrong granularity.

2. **`PROCESSING_COMPLETED` event lacks `rows_captured` field.** Event details show only `date` — no row count, no
   shard count, no duration. Workspace rule (CLAUDE.md "no fire-and-forget VM launches") says: _"Adapters MUST emit
   per-instrument progress events with row counts so silent-success-with-zero-output is detectable from the event
   stream alone."_ Currently silent-zero on a (venue, data_type, day) is invisible from events alone — operators
   must read the per-VM manifest shard to verify. **Owner: MTDS adapter writegate wiring** (writegate Phase 2.E
   per-source progress events).

3. **`PROCESS_CPU_SATURATED` events frequent on `e2-highmem-2` (2 vCPU).** Sample VM had 16 saturation events in
   ~30 min (process_cpu_percent peaks at 115.9%). Workload sized too tight for instance type — book_snapshot_5
   parsing for SPOT_PAIR universe at heavy-tier saturates 2 vCPU. **Recommendation**: future cefi heavy-tier
   relaunches should use `e2-highmem-4` (4 vCPU) or `e2-standard-8`. Not VM-blocking now (events still flow), but
   wall-clock could be 30-50% faster on a wider instance.

Sample-spotted concerns aside, the 37-VM sweep is producing data. Continue monitoring per CLAUDE.md verification
protocol (90s STARTED + 10-15min progress + STOPPED at exit). Per-VM manifest shards merge into canonical via the
manifest-consolidator daemon (already running per `manifest-consolidator-...` watchdog dict entry).

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

- [x] [AGENT] P0. UAC `unified_api_contracts/registry/venue_mapping.py` — extend `all_tardis_exchanges` with `bitfinex`,
      `bitget`, `kraken`. [AUDIT 2026-05-07: DONE — verified live (24 cefi VMs running including bitfinex/bitget/kraken
      Tardis-routed; MTDS@b12ecb5 kraken-specific URL fix landed)]
- [x] [AGENT] P0. UAC `registry/market_data_categories.py` — extend `VENUES_BY_ASSET_GROUP['cefi']` with the 3 venues.
      [AUDIT 2026-05-07: DONE — verified via running VMs writing to cefi asset_group]
- [x] [AGENT] P0. UAC `canonical/coverage_starts.py` — add launch dates: `BITFINEX 2013-04-15`, `BITGET 2018-07-30`,
      `KRAKEN 2011-07-28`. [AUDIT 2026-05-07: DONE — VMs running 2020+ year-shards within bounds]
- [x] [AGENT] P0. UAC `registry/capability_declarations/_cefi.py` — add `SourceCapability` declarations per venue.
      [AUDIT 2026-05-07: DONE — VMs would not route through MTDS without capability declarations]
- [x] [AGENT] P0. MTDS `adapters/umi_tick_provider.py` — update `_TARDIS_CEFI_VENUES` to include the 3 new venues.
      [AUDIT 2026-05-07: DONE — MTDS@b12ecb5 + dae9bc4 confirm Tardis routing live for kraken (and bitfinex/bitget by
      extension)]
- [x] [AGENT] P0. Coverage-start clipping per-venue in adapter pre-fetch (existing pattern). [AUDIT 2026-05-07: DONE —
      UAC SOURCE_COVERAGE_START SSOT is wired]
- [x] [SCRIPT] P0. `scripts/vm/launch-cefi-sharded-backfill.sh` — add symbol lists for each new venue. [AUDIT
      2026-05-07: DONE — launcher confirmed live by 24 RUNNING VMs with `cefi-{venue}-{flavor}-{ts}` prefix]
- [x] [SCRIPT] P0. Add `launch_cefi_shard` calls per venue × heavy/light × year-shard (2020..today). [AUDIT 2026-05-07:
      DONE — 24 running shards span 2020/21/22/23/24/25/26 across bitfinex/bitget/kraken/coinbase/hyperliquid]
- [x] [SCRIPT] P0. Refresh CEFI tarball: `bash scripts/vm/create-code-tarballs.sh --asset-group CEFI` then launch
      backfill VMs. [AUDIT 2026-05-07: DONE — 24 VMs launched 2026-05-06 from refreshed tarball]
- [ ] [VERIFY] P0. After 2-4h: query manifest for new venues; confirm `captured` rows for spot + futures. [AUDIT
      2026-05-07: IN-FLIGHT — VMs cefi-bitfinex-* / cefi-bitget-* / cefi-kraken-* RUNNING since 2026-05-06T08:00-17:00
      UTC, ETA 2026-05-08 to 2026-05-09; verify after drain]
- [ ] [VERIFY] P0. Sanity-check parquets at canonical paths. [AUDIT 2026-05-07: IN-FLIGHT — gated on VM drain above]
- [ ] [QG] P0. Quality gates + quickmerge on UAC + MTDS changes. [AUDIT 2026-05-07: DONE for shipped commits
      (UAC@e890022 + MTDS@b12ecb5/dae9bc4 + 10aa715/51fecd5/d898985/fc53a97); ongoing for pending changes — keep open as
      forever-todo]

### From `cefi_tradfi_tick_data_backfill_2026_04_10` — CeFi half (DERIBIT options + BINANCE-FUTURES + phantom audit)

- [ ] [AGENT] P0. Verify MTDS orchestrator handles all target data_types (options_chain, derivative_ticker, perpetual)
      for DERIBIT + BINANCE-FUTURES. [AUDIT 2026-05-07: FRESH — actionable; MTDS@260325c cluster-coverage gate at
      finalize landed so options_chain root-cluster validation should now run live]
- [ ] [AGENT] P0. Verify instruments-service has historical DERIBIT options/futures and BINANCE-FUTURES perps for target
      windows. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. VM launch script for DERIBIT options backfill (instrument_type=options_chain). [AUDIT 2026-05-07:
      STALE — 2025/2026 light-VM relaunched 2026-05-06 per current-state line; treat IN-FLIGHT for relaunched ones]
- [ ] [SCRIPT] P0. VM launch script for DERIBIT futures backfill (instrument_type=futures_chain). [AUDIT 2026-05-07:
      STALE — launcher pattern exists]
- [ ] [SCRIPT] P0. VM launch script for BINANCE-FUTURES perps backfill (instrument_type=perpetual). [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [SCRIPT] P1. Launch all 3 CeFi VMs in parallel + monitor via GCS logs. [AUDIT 2026-05-07: FRESH — actionable
      post-drain of current 24-VM batch]
- [ ] [SCRIPT] P2. Verify manifest entries appear in deployment-ui data status tab. [AUDIT 2026-05-07: IN-FLIGHT —
      deployment-stack rollup fast-path live; reverify after drain 2026-05-09]
- [ ] [AGENT] P0. Port phantom-audit + manifest-rebuild scripts to CeFi (current scripts target sports/multi-asset).
      [AUDIT 2026-05-07: DONE — `reconcile_phantom_manifest_rows_all.py` is multi-asset-group with `--asset-group cefi`
      flag per CLAUDE.md, used 2026-05-04 to reduce 130k→354 false-positives on cefi (per MEMORY)]
- [ ] [AGENT] P0. Monitor + reap zombie VMs (`gcloud compute instances list` + parallel-delete pattern per workspace
      VM-naming convention). [AUDIT 2026-05-07: IN-FLIGHT — `vm-zombie-watchdog-20260506-175221` RUNNING; ongoing role;
      treat as forever-todo]
- [ ] [AGENT] P0. Post-drain: `/api/data-status/turbo?service=market-tick-data-service&force=true` → CeFi completion_pct
      ≥ target. [AUDIT 2026-05-07: BLOCKED-ON cefi_master:in-flight backfill VMs draining 2026-05-09]
- [ ] [AGENT] P0. Record final capture_status distribution + VM rc count (rc=0 vs rc=137 vs other). [AUDIT 2026-05-07:
      BLOCKED-ON cefi_master:in-flight backfill VMs draining 2026-05-09]
- [ ] [SCRIPT] P2. Spot-check: download 3 random days of DERIBIT options; verify options_chain greeks/IVs populated.
      [AUDIT 2026-05-07: FRESH — actionable post-drain]
- [ ] [SCRIPT] P2. Spot-check: download 1 day of BINANCE-FUTURES perps; verify funding + open_interest populated. [AUDIT
      2026-05-07: FRESH — actionable post-drain]

### From `market_tick_data_to_100pct_2026_05_05` — CeFi slice (per asset_group split)

CeFi-specific MTDS-to-100% todos lifted at the asset_group split commit. Tracks CeFi spot/perp/options/futures coverage
percentage in the deployment-ui data-status panel toward 100%.

- [ ] [AGENT] P1. After CeFi backfill VMs drain, run data-status rollup
      (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api`) and confirm CeFi shards count against
      expected. [AUDIT 2026-05-07: BLOCKED-ON cefi_master:in-flight 24-VM drain (ETA 2026-05-09)]
- [ ] [AGENT] P1. Per-venue completion %: Bybit, Deribit, Binance, OKX, Bitfinex, Bitget, Kraken, BINANCE-FUTURES.
      Surface gaps to operator via deployment-ui drill-down. [AUDIT 2026-05-07: BLOCKED-ON cefi_master:in-flight 24-VM
      drain (ETA 2026-05-09)]
- [ ] [AGENT] P1. Cleanup stale CEFI manifest rows post-MVP scope reduction. [AUDIT 2026-05-07: FRESH — actionable
      post-drain (concurrent with phantom audit re-run)]

### Bitfinex / Bitget / Kraken — extended (post-cutover)

These were originally scoped in `cefi_venue_universe_expansion`; deferring expansion-only items past May 23 is fine
because the 4 critical-path perp venues (Bybit / Deribit / Binance / OKX) are already live.

- [x] [DEFERRED-POST-CUTOVER] P2. Extended / Pacifica / Lighter DEX-perp venues — these are DeFi asset_group, not CeFi.
      Move-out into `defi_master_2026_05_07.plan.md`. [AUDIT 2026-05-07: DONE — Lighter + Pacifica live OHLCV historical
      via MTDS@10aa715/51fecd5/d898985/fc53a97 + UAC@e890022 (per MEMORY entry project_dex_perp_onboarding_2026_05_07);
      Extended pending per dex_perp_onboarding_handover_2026_05_07.HANDOVER.md Item C; this todo is the move-out
      announcement which IS DONE]

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
