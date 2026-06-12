---
name: cefi_master
title: "CeFi Master — asset_group umbrella"
type: epic
tier: L0
status: active
priority: P0
assigned_vm: vm-cefi
parent: master_to_live_defi_2026_05_23
created: 2026-05-07
last_updated: 2026-06-20
locked_by: live-defi-rollout
locked_since: 2026-05-07
related_plans:
  - ../active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md
  - ../active/cefi_ml_directional_continuous_live_2026_06_20.md
  - ../active/cefi_manifest_canonicalisation_2026_06_01.md
  - ../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md
  - ../archive/2026_05/venue_heartbeat_calibration_2026_05_post23.md
  - ../active/trading_agent_service_architecture_unlock_2026_05_22.md
---

> **🔧 RESTRUCTURED 2026-06-20 (asset-group-umbrella thinning)**: this epic had accumulated ~28 open `- [ ]` todos
> INLINE in its body (a frozen May-07/08 snapshot from when child plans were "folded in"). The backlog regen
> (`regen_backlog_from_plan.py`) only scans `plans/active/*.md`, never `plans/epics/`, so those inline todos were never
> dispatched — the epic read as "0 plans". The inline blocks have been **reconciled, not deleted**: net-new unowned work
> extracted to child active plans (see § "Assigned active plans"); already-owned work pointed at its owning June plan;
> cutover success-criteria routed to the master. No work was dropped and nothing was flipped ✅ without evidence. See §
> "Workstream routing" below for the full map.

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **🔴 P0 ABSORBED 2026-05-20 — mega-audit A3 findings for cefi asset_group**: 16,171 `MISSING_EXPECTED` + 17,207
> `ATTEMPTED_FAILED` cells. MISSING: OKX (trades/book_snapshot_5/derivative_ticker/liquidations all 2,332 cells) +
> COINBASE (trades/book_snapshot_5, 2,332 each) + UPBIT (trades/book_snapshot_5, 450 each). FAILED: DERIBIT
> futures_chain (2,286) + options_chain (2,283) + liquidations (1,819) + BINANCE-FUTURES futures_chain (2,309) +
> book_snapshot_5 (669) + BYBIT futures_chain (2,083) + book_snapshot_5 (589) + ASTER ALL 4 types (563 each from
> launch) + HYPERLIQUID liquidations (916). Reassigned slot 9 portion per `work_split_2026_05_19_ikenna.md` § "Slot 9 —
> REASSIGNED"
>
> - CLAUDE.md HARD RULE.
>
> **Scope MUST cover every venue × data_type — no asset_group skipped, no deadline-driven cutbacks**.

# CeFi Master — asset_group umbrella

> **🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping** (coordinated by
> `available_at_lookahead_bias_completion_2026_05_08` Phase 1). Re-verify per-adapter `available_at` stamping wiring
> before adding new adapters to this plan.

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest v5 schema + 4-state capture taxonomy + cluster validation for bundled CeFi data_types (`options_chain` /
  `futures_chain`)
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  CeFi `empty_confirmed` rule (only venue-level reasons legit: `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` /
  `EXPECTED_PRE_VENUE_LAUNCH` / `EXPECTED_PARTIAL_HALF_DAY`); zero-source-response on alive instrument-day must flip to
  `attempted_failed`
- [`codex/02-data/per-asset-group-bucket-layouts.md`](../../codex/02-data/per-asset-group-bucket-layouts.md) — CeFi
  shard matrix: spot/perp = per-instrument-per-day (35GB roots); options/futures = bundled by `options_chain` /
  `futures_chain` root; per-VM shard isolation policy
- [`codex/02-data/mtds-data-source-coverage-matrix.md`](../../codex/02-data/mtds-data-source-coverage-matrix.md) — MTDS
  per-(venue, data_type) source coverage with `SOURCE_COVERAGE_START` per venue (Tardis vs Databento vs venue-native
  REST)
- [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
  batch=live unified pipeline: same shard atom, same fields, same `available_at` semantics across modes; CeFi
  forward-poll + backfill share one code path
- [`codex/04-architecture/asset-class-ownership.md`](../../codex/04-architecture/asset-class-ownership.md) — CeFi venue
  list (Bybit / Deribit / Binance / OKX / Bitfinex / Bitget / Kraken / Coinbase / Hyperliquid) + `VENUE_TO_ASSET_GROUP`
  SSOT
- [`codex/04-architecture/interface-credential-convention.md`](../../codex/04-architecture/interface-credential-convention.md)
  — CeFi credentials: `get_order_adapter(venue, api_key, api_secret, ...)` keys-as-params shape; ApiKeyReloader
  hot-reload pattern
- [`codex/05-infrastructure/launcher-script-ssot.md`](../../codex/05-infrastructure/launcher-script-ssot.md) — CeFi
  backfill / forward-poll launchers MUST live under `deployment-service/scripts/vm/`; `VM_PREFIX_TO_BUCKET` registry
  keeps zombie watchdog visibility

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## AI-day estimate

- **Total**: ~5 ai-days net (XL — 24 VMs running for backfill, ~34% of 29 todos in-flight per 2026-05-07 audit).
- **Workstream split**:
  - 24-VM backfill drain monitoring + per-VM 4-pillar validation: ~1.5 ai-days (passive monitoring with active
    spot-checks, ETA 2026-05-09)
  - Bitfinex / Bitget / Kraken Tardis venue universe expansion (UAC + adapter wiring): ~1 ai-day (mostly shipped per
    UAC@7cb9068 / 405cbf5; integration verification + per-instrument coverage check pending)
  - DERIBIT options + futures bundle backfill to genesis (2025/2026 light-VM relaunched 2026-05-06): ~1 ai-day
  - BINANCE-FUTURES perps backfill manifest cleanup: ~0.5 ai-day
  - Phantom-audit + manifest-rebuild port to CeFi (`reconcile_phantom_manifest_rows_all.py --asset-group cefi`): ~1
    ai-day (run on same-region GCE VM per workspace rule)
- **Parallelism factor**: ~2x (Bitfinex/Bitget/Kraken can proceed independent of DERIBIT bundle work; phantom-audit is
  read-only and runs anywhere). **~2-3 calendar days** wall-clock.
- **Critical path to 2026-05-23 cutover**: 4 perp venues (Bybit / Deribit / Binance / OKX) tick-data ≥99% complete +
  forward-poll wired before May 23; the extended-backfill venues (Bitfinex/Bitget/Kraken) are P1 enabling new archetypes
  but NOT live-trading-blocking.

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 22 of 22 unchecked todos
- **Mis-marked DONE → flipped**: 4 (UAC venue_mapping bitfinex/bitget/kraken; MTDS `_TARDIS_CEFI_VENUES` populated per
  `b12ecb5` kraken slash→hyphen normalization; `launch-cefi-sharded-backfill.sh` live, used to launch the 24 RUNNING
  VMs; coverage-start clipping per-venue via UAC SOURCE_COVERAGE_START SSOT)
- **In-flight (running VMs)**: 24 VMs (8 venues × multi-year shards), all on `live-defi-rollout` tarball,
  asia-northeast1-c. Bitfinex spot (5) + futures (4), Bitget futures (3), Coinbase spot (4), Hyperliquid (2), Kraken
  futures (1) + Kraken spot (7). ETA 2026-05-07 to 2026-05-09.
- **Blocked by**: `manifest_migration_SUPERSEDED_2026_05_21:Stage 4` (rescan-all-manifests gates MTDS-to-100%
  verification); `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder deletion gates honest-coverage % numbers)
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
  (`carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`); the latter renamed from legacy
  `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07).
- **CeFi extended tick-data backfill**: Bitfinex, Bitget, Kraken (Tardis-served).
- **CeFi options + futures bundles**: DERIBIT options/futures, BINANCE-FUTURES perps.
- **MTDS coverage to 100% for the CeFi slice** (per-instrument-per-day for spot/perp; bundled-by-root for
  options/futures).

**MVP backtest scope** (per
[`codex/09-strategy/mvp-universe-per-asset-group.md`](../../codex/09-strategy/mvp-universe-per-asset-group.md)): ~30 MVP
coins × 6 perp venues for arbitrage-funding-rate archetype. Dust-conversion spot coins (e.g. EIGEN) captured for prices,
NOT in backtest config-grid. Data capture remains broad (all instruments per venue catalog). Tier A archetypes touching
CeFi: ml-continuous + arbitrage-funding-rate + defi-carry-family (perp hedge legs).

**Not covered here** (out of asset_group scope):

- TradFi (CME / CBOE / NYSE / NASDAQ) → see `tradfi_master.md`.
- DeFi DEX perps (Hyperliquid / Aster / Lighter / Extended / Pacifica) → see `defi_master.md`. Note: Lighter / Extended
  / Pacifica were originally scoped under `cefi_venue_universe_expansion` as "DEX perps" but they're DeFi by
  asset_group.
- Sports / Predictions → see `sports_master.md` / `predictions_master.md`.
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

37 cefi VMs running in `asia-northeast1-c` covering bitfinex/bitget/kraken × futures+spot × 2020-2026 (`e2-highmem-2`).
Sample event verification (3 VMs at T+30min): STARTED + PROCESSING_STARTED + PROCESSING_COMPLETED flowing properly, ~4
min/date pace.

**Findings from per-VM manifest spot-check (Harsh, 2026-05-07 15:35 IST)** — concerns to feed back into writegate

- shard-granularity follow-ups, NOT VM-blockers (the data IS being written, just the manifest shape is asymmetric):

1. **Asymmetric manifest shard shape — captured rows are bundle-level, empty_confirmed rows are per-instrument.**
   Verified across 2 VMs (`cefi-bitfinex-spot-2020-heavy-...` 200 rows, `cefi-kraken-spot-2020-heavy-...` 250 rows):
   100% of `captured` rows have empty `instrument_id` + `instrument_count=8.3M` (BTC bundle), while 100% of
   `empty_confirmed` rows have populated `instrument_id=BTCUSD/ETHUSD/...` + `instrument_count=0`. This **violates the
   per-asset-group shard-key matrix** in CLAUDE.md "Shard-granularity SSOT" section
   (`cefi spot/perp = (asset_group, venue, data_type, instrument_type, instrument_id, day) — per-instrument`). The
   bundle-level captured row passes the rollup check but the data-status drilldown can't show per-instrument coverage.
   **Owner: Ikenna writegate Phase 2.A residual** (per work-split D2). Reference incident shape: this is the same class
   as TradFi MVP partial-bundle (ES.OPT 18 single-parent fills) and MDPS 1440-NaN-OHLC — captured rows at the wrong
   granularity.

2. **`PROCESSING_COMPLETED` event lacks `rows_captured` field.** Event details show only `date` — no row count, no shard
   count, no duration. Workspace rule (CLAUDE.md "no fire-and-forget VM launches") says: _"Adapters MUST emit
   per-instrument progress events with row counts so silent-success-with-zero-output is detectable from the event stream
   alone."_ Currently silent-zero on a (venue, data_type, day) is invisible from events alone — operators must read the
   per-VM manifest shard to verify. **Owner: MTDS adapter writegate wiring** (writegate Phase 2.E per-source progress
   events).

3. **`PROCESS_CPU_SATURATED` events frequent on `e2-highmem-2` (2 vCPU).** Sample VM had 16 saturation events in ~30 min
   (process_cpu_percent peaks at 115.9%). Workload sized too tight for instance type — book_snapshot_5 parsing for
   SPOT_PAIR universe at heavy-tier saturates 2 vCPU. **Recommendation**: future cefi heavy-tier relaunches should use
   `e2-highmem-4` (4 vCPU) or `e2-standard-8`. Not VM-blocking now (events still flow), but wall-clock could be 30-50%
   faster on a wider instance.

Sample-spotted concerns aside, the 37-VM sweep is producing data. Continue monitoring per CLAUDE.md verification
protocol (90s STARTED + 10-15min progress + STOPPED at exit). Per-VM manifest shards merge into canonical via the
manifest-consolidator daemon (already running per `manifest-consolidator-...` watchdog dict entry).

### Day 2 monitoring sweep — 2026-05-08 (24 VMs on e2-highmem-8 post-relaunch)

The original 37-VM `e2-highmem-2` wave was relaunched 2026-05-07 18:48–19:01 UTC as **24 VMs on `e2-highmem-8`**, ~3
hours after the `UTL@68b3804a` blank-reason classifier fix landed. This subsection tracks the Day 2 monitoring loop
(10-min cadence, owned by `cefi-babysit-tab`).

**Fleet snapshot (2026-05-08 04:15 UTC, T+~9h)**: 24/24 RUNNING in `asia-northeast1-c`, all `e2-highmem-8`.
Distribution: bitfinex spot (6: 2020–2025) + futures (4: 2021/22/24/25); bitget spot (1: 2025) + futures (1: 2025);
kraken spot (7: 2020–2026) + futures (5: 2021–2025).

**Liveness sweep (24/24 OK)**: every VM has last_event_age ≤ 1 min. Zero stalls, zero near-watchdog (the
`vm_zombie_watchdog.py` defaults are `--heartbeat-stale=15min` auto-kill, `--shard-stale=120min` fallback).

**Data-quality spot-check (4 VMs across 3 venues + 2 timeframes)**:

| VM                    | rows  | captured | empty | failed | blank-reason | per-instrument shape          |
| --------------------- | ----- | -------- | ----- | ------ | ------------ | ----------------------------- |
| bitfinex-spot-2020    | 2762  | 100%     | 0%    | 0%     | 0            | ✓ (11 instruments × 2 dtypes) |
| bitfinex-futures-2025 | 2537  | 100%     | 0%    | 0%     | 0            | ✓ (8 instruments × 2 dtypes)  |
| bitget-spot-2025      | 11154 | 100%     | 0%    | 0%     | 0            | ✓ (24 instruments × 2 dtypes) |
| kraken-spot-2020      | 6170  | 100%     | 0%    | 0%     | 0            | ✓ (13 instruments × 2 dtypes) |

Tight post-RED-ALERT threshold (<5% empty) trivially passes — actual is 0% empty. Zero blank-reason `empty_confirmed`
writes (RED ALERT not triggered). All `instrument_id` columns populated; per-instrument `instrument_count` ranges 4 →
6.7M (real per-instrument tick counts, NOT bundle-rollup 8.3M).

**Important resolution — asymmetric shard shape no longer reproducing.** The bundle-vs-per-instrument shape documented
in
[`../archive/issues/cefi_tardis_writegate_findings_2026_05_07.md`](../archive/issues/cefi_tardis_writegate_findings_2026_05_07.md)
Finding 1 is no longer present on the Day 2 fleet. Current shards are SSOT-conformant per-instrument shape (see
CLAUDE.md § "Shard-granularity SSOT" cefi spot/perp matrix). Either Ikenna's writegate Phase 2.A residual landed
overnight, or the relaunched-on-`-8` VMs use a tarball that includes the fix. Issue-doc owner should sweep + resolve
when convenient.

**Drain progress samples (T+~9h, % through year)**:

| VM                    | dates done                    | est. progress |
| --------------------- | ----------------------------- | ------------- |
| bitfinex-spot-2020    | 210 (2020-01-01 → 2020-07-29) | ~57%          |
| bitfinex-futures-2025 | 160 (2025-03-15 → 2025-08-21) | ~44%          |
| bitget-spot-2025      | 234 (2025-01-07 → 2025-09-12) | ~64%          |
| kraken-spot-2020      | 261 (2020-01-01 → 2020-09-17) | ~71%          |

ETA 05-08 / 05-09 plausible for leading VMs; trailing ones (e.g. bitfinex-futures-2025) may slip into 05-09 evening.

**Caveats / unresolved (NOT filing as findings)**:

1. `PROCESS_CPU_SATURATED` events still firing on `e2-highmem-8` (~11 events / 10 min on sampled VM). Operational
   metrics show this is misleading: `process_cpu_percent=105%` on 8 vCPU is nowhere near saturated, pace 3.67 min/date
   is _faster_ than expected ~4 min, queue depth 16 in-flight oldest 40 s old is healthy. Threshold likely fires on
   `cpu_percent > 100%` which is single-thread semantics and noise on multi-thread workloads. **Observability artifact,
   not a data-quality risk.**
2. `PROCESSING_COMPLETED` still lacks `rows_captured` (writegate-findings Finding 2). Silent-zero is invisible from
   events alone — mitigated by reading per-VM shards directly. Owner remains Ikenna writegate Phase 2.E.

**Iteration log** (one-line per 10-min sweep, oldest first):

- 2026-05-08 04:15 UTC — sweep #1: 24/24 alive, 100% captured on 4 sampled VMs, RED ALERT not triggered. No actions.
- 2026-05-08 04:37 UTC — sweep #2: 23/24 alive (cefi-bitfinex-futures-2021 drained normally), worst event_age 0m, sample
  VM cefi-kraken-futures-2021 100% captured (1252 rows, latest 2021-08-05). No actions.
- 2026-05-08 04:46 UTC — sweep #3: 23/23 alive (no further drain), worst event_age 0m, sample VM cefi-bitfinex-spot-2023
  100% captured (4766 rows, latest 2023-06-04 ≈42% through year). No actions.
- 2026-05-08 04:54 UTC — sweep #4: 23/23 alive, worst event_age 0m, sample VM cefi-kraken-spot-2021 100% captured (3192
  rows, latest 2021-04-22 ≈31% through year). No actions.
- 2026-05-08 05:04 UTC — sweep #5: 23/23 alive, worst event_age 0m, sample VM cefi-bitget-futures-2025 100% captured
  (6617 rows, latest 2025-05-24 ≈40% through year). No actions.
- 2026-05-08 05:15 UTC — sweep #6: 23/23 alive, worst event_age 0m, sample VM cefi-kraken-spot-2023 100% captured (6924
  rows, latest 2023-06-22 ≈47% through year). No actions.
- 2026-05-08 05:24 UTC — sweep #7: 23/23 alive, worst event_age 0m, sample VM cefi-kraken-spot-2026 100% captured (4215
  rows, latest 2026-04-16 ≈83% through partial-year window). No actions.
- 2026-05-08 05:35 UTC — sweep #8: 22/23 alive (cefi-kraken-futures-2025 drained normally — 2nd completion), worst
  event_age 0m, sample VM cefi-bitget-futures-2025 100% captured (6950 rows, latest 2025-05-31 ≈42% through year). No
  actions.
- 2026-05-08 05:45 UTC — sweep #9: 21/22 alive at sweep, then 20/24 by 05:46 UTC recheck (cefi-kraken-futures-2023 +
  cefi-kraken-spot-2021 both drained in close succession — 3rd + 4th completions); worst event_age 0m, sample VM
  cefi-kraken-futures-2021 100% captured (1438 rows, latest 2021-09-05 ≈68% through year). 20/24 = 83%, above 80% commit
  trigger. No actions.
- 2026-05-08 05:55 UTC — sweep #10: 20/24 alive (83%, no further drain), worst event_age 0m, sample VM
  cefi-bitfinex-futures-2025 100% captured (2997 rows, latest 2025-09-19 ≈72% through year). No actions.
- 2026-05-08 06:05 UTC — sweep #11: 20/24 alive (83%, no further drain), worst event_age 0m, sample VM
  cefi-kraken-spot-2023 100% captured (7440 rows, latest 2023-07-04 ≈51% through year). No actions.
- 2026-05-08 06:15 UTC — sweep #12: 20/24 alive (83%, no drain), worst event_age 0m, sample VM cefi-kraken-futures-2024
  100% captured (2052 rows, latest 2024-12-19 ≈97% through year — close to its drain). No actions.
- 2026-05-08 06:25 UTC — sweep #13: 20/24 alive (83%, no drain), worst event_age 0m, sample VM cefi-bitfinex-spot-2024
  100% captured (4796 rows, latest 2024-06-07 ≈43% through year). No actions.
- 2026-05-08 06:35 UTC — sweep #14: 20/24 alive (83%, no drain), worst event_age 0m, sample VM cefi-kraken-spot-2026
  100% captured (4841 rows, latest 2026-05-01 ≈97% through partial-year window — closest to drain). No actions.
- 2026-05-08 06:45 UTC — sweep #15: 19/24 alive (cefi-kraken-futures-2024 drained — 5th completion, was at ≈97% per
  sweep #12), worst event_age 0m, sample VM cefi-bitfinex-spot-2025 100% captured (4896 rows, latest 2025-06-11 ≈44%
  through year). **Fleet at 79.16% — crossed below 80% commit trigger.** Iteration-log catch-up commit follows.
- 2026-05-08 06:55–09:55 UTC — sweeps #16–#34 (condensed; cefi-babysit-tab original): fleet drained 19→18→17 over the
  window (cefi-kraken-spot-2026 #17, cefi-bitget-spot-2025 #24); 100min plateau at 17/24 (71%) starting #24. Every
  sweep: 100% liveness, worst event_age 0m, 100% captured on sampled shards, zero blank-reason writes (RED ALERT not
  triggered). No actions across the window.
- 2026-05-08 10:05 UTC — sweep #35: 17/24 alive (71%, 110min plateau), worst event_age 0m, sample VM
  cefi-kraken-futures-2021 100% captured (2003 rows, latest 2021-12-09 ≈94% through year — near drain). No actions.
- 2026-05-08 10:15 UTC — sweep #36: 16/24 alive (67%, cefi-kraken-spot-2020 drained — 8th completion, was at ≈97% per
  sweep #29), worst event_age 0m, sample VM cefi-kraken-spot-2023 100% captured (10831 rows, latest 2023-09-20 ≈72%
  through year). No actions (still in 60-80% milestone band).
- 2026-05-08 11:19 UTC — sweep #37 (Tab 4 vm-ops-tab takes over from cefi-babysit-tab): 16/24 alive (67%, 64min plateau
  since #36 — no new drains in the gap), worst event_age ~1m (latest events 11:18:25-42 UTC across 5 sample VMs in
  hour=11 partition), sample VM cefi-bitfinex-spot-2025 100% captured (6652 rows, latest 2025-08-08 ≈60% through year —
  up from 4896 rows / 2025-06-11 at sweep #15, healthy progress), zero empty_confirmed / attempted_failed rows (RED
  ALERT not applicable — no blank-reason class to even check). No actions (still in 60-80% milestone band).
- 2026-05-08 11:31 UTC — sweep #38: 14/24 alive (58%, 2 new drains in 12min: cefi-bitfinex-futures-2022 9th completion,
  cefi-kraken-futures-2021 10th completion). **Crossed below 60% milestone band — fleet entering 40-60% band.** Worst
  event_age 0-1m (latest events 11:30:51-11:31:14 UTC across 3 sample VMs). No actions (drain accelerating again
  post-#36 plateau, healthy).
- 2026-05-08 11:41 UTC — sweep #39 (re-applied after Tab 5 pull --rebase silently dropped sweeps #16-#38 in working
  tree; recovered from prior conversation memory): 14/24 alive (58%, 10min plateau since #38, no new drains in gap).
  Worst event_age <1m. **Recovery commit follows immediately to avoid another loss.** No fleet actions.
- 2026-05-08 11:54 UTC — sweep #40: 13/24 alive (54%, 1 new drain in 13min: cefi-bitfinex-futures-2025 11th completion).
  Still in 40-60% band. No actions.

## Critical path

| Workstream                                                | Status                            | Source plan / commit                                                 | Success gate                                                                                                                                                                                             |
| --------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4 CeFi perp venues live (Bybit / Deribit / Binance / OKX) | INSTRUMENTS LIVE; tick-data ~60%  | `cefi_tradfi_tick_data_backfill`                                     | Per-venue per-data*type per-day shard ≥99% captured for 2024-01-01 → today; `perp_funding` populated continuously; forward-poll launcher emits `STARTED`+`PROCESSING*\*` events for each venue           |
| DERIBIT options + futures bundles backfilled to genesis   | 2024 done; 2025/2026 in flight    | `cefi_tradfi_tick_data_backfill` (2025/2026 VMs running 2026-05-06+) | All `options_chain` / `futures_chain` bundles record_captured with `expected_root_clusters` validation passing per-day (cluster coverage gate per CLAUDE.md "Cluster validation MANDATORY")              |
| BINANCE-FUTURES perps backfill                            | partial; manifest cleanup pending | `cefi_tradfi_tick_data_backfill`                                     | Manifest reconciliation drops phantom rows; per-instrument-per-day coverage ≥99% on all live perps                                                                                                       |
| Bitfinex / Bitget / Kraken Tardis venues                  | NOT STARTED                       | `cefi_venue_universe_expansion`                                      | All 3 venues × spot+futures × 2020-2026 backfilled; per-VM 4-pillar validation green (row count > 0, NaN ratio in tolerance, schema match, cluster coverage where applicable); zero silent-zero captures |
| CeFi MTDS shards to 100%                                  | partial                           | `market_tick_data_to_100pct` (CeFi slice)                            | data-status drilldown shows ≥99% coverage % per (venue, data_type); residual gaps stamped with typed `EMPTY_CONFIRMED_REASONS`                                                                           |
| Phantom-audit + manifest-rebuild for CeFi                 | partial — TradFi port pending     | `cefi_tradfi_tick_data_backfill` (CeFi half)                         | `reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` reports <0.5% phantom rate (per 2026-05-04 99.7% reduction precedent); residual classified by drift axis                           |

## Workstream routing (restructured 2026-06-20)

The CeFi work is dispatched through child active plans (regen scans `plans/active/`, not this epic). Every former inline
todo block below maps to one of these homes — nothing dropped, nothing flipped ✅ without evidence:

| Former inline block                                                                                                                                                                    | Disposition                                                                                                                     | Home (the live, dispatchable plan)                                                                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DERIBIT options/futures + BINANCE-FUTURES bundle backfill verify + spot-checks + phantom-audit residual triage                                                                         | **EXTRACTED (net-new)**                                                                                                         | [`cefi_deribit_binance_futures_bundle_verification_2026_06_20`](../active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)                                                                                                                                          |
| A1 / "End-state at May 23" ML success criteria (continuous ML signal live on OKX+Binance+Bybit)                                                                                        | **EXTRACTED (net-new)**                                                                                                         | [`cefi_ml_directional_continuous_live_2026_06_20`](../active/cefi_ml_directional_continuous_live_2026_06_20.md)                                                                                                                                                                    |
| Tardis-venue drain verify, per-venue completion %, data-status rollup, stale-manifest cleanup, post-drain `completion_pct` / `capture_status` distribution, MTDS/IS slice verification | **OWNED ELSEWHERE — do not duplicate**                                                                                          | [`cefi_manifest_canonicalisation_2026_06_01`](../active/cefi_manifest_canonicalisation_2026_06_01.md) (slot-3 CeFi master orchestrator: deployment-api CeFi multi-source UNION coverage + per-source breakdown + pipeline_mode dedup/drilldown + expected_unattempted enumeration) |
| Per-adapter `available_at` stamping + CeFi feature_groups → UAC `FEATURE_REQUIRED_INPUTS` (the Q1 structural blocker)                                                                  | **✅ COMPLETE (shipped)** — owner plan archived `open=0/done=30`                                                                | [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md) Phase 1/4 (the Q1 structural mismatch was resolved as part of it; issue-doc `cefi_available_at_spawn_task_structural_mismatch_2026_05_08` closed)   |
| QG forever-todo, zombie-VM reap                                                                                                                                                        | **DROPPED** — process/operational notes, not shippable units (covered by `vm_zombie_watchdog.py` cron + the per-commit QG rule) | —                                                                                                                                                                                                                                                                                  |

The blocks below are the **frozen May-07/08 source snapshot**, retained for archaeology only. They are SUPERSEDED by the
routing table above — do NOT pick work from them directly.

## Consolidated todos — SUPERSEDED 2026-06-20 (history only; see § "Workstream routing")

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
      flag per CLAUDE.md, used 2026-05-04 to reduce 130k→354 false-positives on cefi (per MEMORY)] [SLOT-6 RAN
      2026-05-11 — `launch-defi-phantom-recon-vm.sh cefi --dry-run` → `defi-phantom-recon-cefi-20260511-193451`
      (e2-standard-4, asia-northeast1-c; 129220 prefixes @~370/sec; completed 14:16 UTC, exit 0, VM self-deleted):
      **1290706 real captures / 2223 "phantom captures" = 0.17% phantom rate — UNDER the <0.5% criterion** (line 292 of
      this plan). Residual 2223 spread across drift-axis-suspicious clusters: blank `venue` 1453, DERIBIT 136 (mostly
      `options_chain` 435 + `futures_chain` 401 — bundled data_types), `venue=UNKNOWN` 111, Bitfinex `*F0` perpetual
      codes (BTCF0/ETHF0/DOTF0/… ~20-34 each ≈ 400). These are NOT obviously real-missing-data — they're the classic
      manifest-vs-disk shape drifts (blank/UNKNOWN venue rows the audit can't probe a path for; chain-bundle `option`↔
      `options_chain` equivalence; venue-normalization `BTCF0`→canonical). **Did NOT `--apply`** — flipping all 2223 to
      `attempted_failed` would corrupt the manifest for the false-positive majority (2026-05-04 130,897-false-positive
      class). **Pending (cefi owner)**: per-cluster real-vs-false-positive triage — sample each cluster, check parquet
      existence, then either add the missing drift axis to `reconcile_phantom_manifest_rows_all.py`'s cefi templates
      (for false-positives) or `--apply` only the genuinely-real subset. Criterion-met for now (0.17% < 0.5%); full
      classification is the residual work. Cross-ref: `code_freeze_migrate_backfill_sequencing_2026_05_10.md`
      DONE-2026-05-11 deferral table (phantom-audit row) + `harsh_orchestrator/pings/slot_6.md` 2026-05-11 14:00/14:18
      UTC.]
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
      Move-out into `defi_master.md`. [AUDIT 2026-05-07: DONE — Lighter + Pacifica live OHLCV historical via
      MTDS@10aa715/51fecd5/d898985/fc53a97 + UAC@e890022 (per MEMORY entry project_dex_perp_onboarding_2026_05_07);
      Extended pending per dex_perp_onboarding_handover_2026_05_07.HANDOVER.md Item C; this todo is the move-out
      announcement which IS DONE]

## `available_at` adapter stamping (coordinated) — SUPERSEDED 2026-06-20 (owned by the coordinator plan; history only)

> **OWNED ELSEWHERE**: this block is tracked in
> [`available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
> Phase 1/4 (CeFi adapter stamping + feature-registry). Do NOT dispatch from here. Retained below for context only.

> **Coordinator:**
> [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
> Phase 1. Audit 2026-05-08 found CeFi adapters lack explicit per-adapter `available_at` stamping wiring per UAC
> `AVAILABILITY_AT_SEMANTICS`. Without it, `assert_available_at_present` in `ManifestWriter.record_captured()` is dead
> code for cefi shards.

- [ ] [SCRIPT] P0. **Per-adapter `available_at` stamping for CeFi**. For every CeFi adapter (Bybit, Binance, OKX,
      Deribit, Bitfinex, Bitget, Coinbase, Hyperliquid, Kraken, Aster) across `ohlcv_*` / `trades` / `funding_rate` /
      `perp_*` / `options_chain` / `futures_chain`: stamp
      `available_at = tick_timestamp + source_priority_scrape_latency` per UAC `SOURCE_PRIORITY` (tick-level), or
      `available_at = bar_close_boundary` (bar-level — depends on coordinator Phase 0 MDPS bar boundary contract).
      Insert call before `record_captured`. Mirror precedent in `features-sports/_enforce_pit_sports`.
- [ ] [SCRIPT] P1. **CeFi feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. ~5 cefi feature_groups (volatility,
      liquidity, microstructure, perp_basis, options_iv) need registry entries. Source-of-truth:
      `features-cefi-service/calculators/` metadata. Coordinator Phase 4.

## Open questions — SUPERSEDED 2026-06-20 (extracted / tracked-elsewhere; history only)

> **ROUTED**: the A1 "End-state at May 23" ML success criteria + the locked design decisions (archetype / cadence /
> capital) are extracted to
> [`cefi_ml_directional_continuous_live_2026_06_20`](../active/cefi_ml_directional_continuous_live_2026_06_20.md). The
> Q1 `available_at` structural blocker is tracked in the coordinator plan + issue-doc
> `cefi_available_at_spawn_task_structural_mismatch_2026_05_08`. Retained below for context only — do NOT dispatch from
> here.

### Q1 — [cefi-available-at-stamping-tab (Tab F2), 2026-05-08] — Spawn task structurally blocked: 3 facts contradict the spec

**Status**: 🟡 BLOCKED — waiting for master agent + operator triage

The Tab F2 spawn prompt in [`work_split_2026_05_08_ikenna.md`](../active/work_split_2026_05_08_ikenna.md) (fresh
fan-out: instruments-service + MTDS) specs CeFi per-venue `available_at` stamping at
`market-tick-data-service/market_tick_data_service/adapters/{venue}.py` across 10 venues (bybit / binance / okx /
deribit / kraken / bitfinex / bitget / coinbase / gate / kucoin) using helper
`stamp_available_at_cefi_tick(df["timestamp"], venue, data_type)` from `unified_trading_library.availability_stamping`,
with formula `available_at = tick_ts + emission_latency_ms` per UAC SOURCE_PRIORITY.

**Probe results 2026-05-08 (this agent, before any code edit)**:

1. **Per-venue adapter files do NOT exist.** `market_tick_data_service/adapters/` contains only `hyperliquid_s3.py` +
   `umi_tick_provider.py`. The 10 cefi venues listed in the spawn prompt have NO standalone `{venue}.py` files. CeFi
   venues route through `market_interface/adapters/cefi/` which has:
   `__init__.py / ccxt_adapter.py / databento_mbo_adapter.py / l2_book_state.py / tardis_incremental_book_adapter.py / tardis_shared.py / upbit_adapter.py`
   — 5 source-shaped adapters, NOT 10 venue-shaped adapters.

2. **`stamp_available_at_cefi_tick` does NOT exist in UTL.**
   `unified-trading-library/unified_trading_library/availability_stamping.py` (sole module, single file — NOT a package)
   exports 5 sports-shaped helpers only: `stamp_available_at_lineups` / `stamp_available_at_event_time` /
   `stamp_available_at_post_match` / `stamp_available_at_offset` / `stamp_available_at_explicit`. **No CeFi/DeFi/TradFi
   tick-shape helper exists.** This is the master-gate `[A.10]` UTL helper the spawn prompt's PRE-REQ GATE references —
   it has not been shipped.

3. **`SOURCE_PRIORITY` does NOT carry `emission_latency_ms` / `scrape_latency`.**
   `unified_api_contracts/canonical/crosscutting/source_priority.py:84` types `SOURCE_PRIORITY` as
   `Final[dict[tuple[str, str], list[str]]]` — value is a list of source-name strings (top-source-only per Phase 1B
   convention), no per-source latency field. The formula `available_at = tick_ts + source_priority_scrape_latency` per
   plan-of-record
   [`available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
   Phase 1 cannot be evaluated against the current UAC shape.

4. **`record_captured` callsites in MTDS are in `cli/handlers/`, NOT per-venue files.** The 27+ `record_captured(`
   callsites in `market-tick-data-service/market_tick_data_service/cli/handlers/` are mostly DeFi handlers
   (`lst_rates_handler`, `perp_funding_handler`, `dex_swaps_handler`, etc.) plus `position_data_handler`. The CeFi
   bar-shaped writes flow through `engine/orchestrator.py` (per writegate plan Phase 2.B Option α refactor — itself
   listed as PENDING under Tab 2 LIVE-PIPELINE 2026-05-08 evening DONE block). There is NO 1:1 mapping
   `(venue, data_type) -> single record_captured callsite` to wrap with a stamping call.

**Why this is BIG (Findings Triage Discipline Case 5)**: contradicts a workspace SSOT (the work-split's premise about
file layout); requires action across ≥2 repos (UAC `SOURCE_PRIORITY` shape extension + UTL helper creation + MTDS
multi-callsite wiring); changes the work-split (Tab F2 cannot ship 10 per-venue commits as scoped). Issue doc:
[`plans/archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md`](../archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md).

**What this Tab F2 agent did NOT do (per "don't edit unfamiliar files when blocked" + "Plans Run To Actual Completion"
HARD RULEs)**: did not ship `stamp_available_at_cefi_tick` (master-gate work owned by Tab 2 LIVE-PIPELINE / writegate
Phase 2.D); did not extend UAC `SOURCE_PRIORITY` shape (cross-cutting design = Ikenna-side); did not modify CeFi cli
handlers / engine orchestrator (collision boundary with Tab 2 LIVE-PIPELINE per work-split § "collision-risk callouts").

**Recommended next agent action** (when master gate clears): the actual scope per
`available_at_lookahead_bias_completion_2026_05_08` Phase 1 P0 todo `**CeFi adapter stamping**` is to wire stamping at
the writer boundary in MTDS `engine/orchestrator.py`

- `cli/handlers/*_handler.py` (the actual record_captured callsites), NOT at non-existent per-venue files. The right
  shape is one stamping call per writer-boundary record, not 10 per-venue commits.

#### A1 — [main, awaiting]

**Status**: pending

> **Folded epic** (operator direction 2026-05-08): May-23 deadline content originally in
> `plans/epics/cefi_ml_may_23_2026.epic.md` is consolidated here. Archived epic:
> [`plans/archive/cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md).

**Why:** Second live archetype for May 23 — continuous ML prediction signal tradable across OKX + Binance + Bybit on
real capital. Distinct from DeFi rollout (rules-based, carry-family). Ships the live ML loop end-to-end.

### End-state at May 23 (success criteria)

- [ ] **Continuous ML prediction signal live** on real capital across OKX + Binance + Bybit, ≥7 continuous days.
- [ ] **End-to-end ML pipeline live**: live tick data → live features → live model inference → live strategy decision →
      live execution → live position + risk + P&L attribution.
- [ ] **Backtest fidelity** for the same signal proven via 2-year batch backtest config grid (master plan Group F item
      18).
- [ ] **Live model lifecycle**: hot-reload of model artefacts without service restart; model-version traceability per
      trade; model-drift alerting.
- [ ] **Live alerting active**: signal-staleness + execution-quality + P&L deviation + position breaches.
- [ ] **Kill switches + circuit breakers**: position-limit, P&L drawdown, signal-staleness, model-drift detection.
- [ ] **DART manual override**: operator can pause / override / replicate any ML-driven trade.

### IN/OUT scope

- **IN**: one ML archetype × OKX + Binance + Bybit live; full live ML pipeline; live model registry + hot-reload +
  version traceability; live alerting + kill switches; DART manual-trade replication; backtest fidelity proof (2-year
  config grid).
- **OUT (post-May-23)**: additional CeFi venues; multiple concurrent ML archetypes; cross-asset-group ML signals; full
  AWS-side parity for live ML.

### Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_SUPERSEDED_2026_05_21` for strategy catalogue, strategy IDs, client wiring,
  infrastructure baseline.
- **Shares with:** `live_defi_rollout` (CeFi venue connectivity overlap on Bybit / Binance / OKX; same execution-service
  adapters + alerting rules).
- **Provides to:** `sp_prediction` + `sports_ml` + `prediction_markets` (shared ML lifecycle infrastructure: model
  registry, training pipeline, drift detection, batch backtest harness).

### Open questions

- [x] ✓ **Which ML archetype family — RESOLVED 2026-05-08 (master Q&A 7).** **`ML_DIRECTIONAL_CONTINUOUS`** — continuous
      directional prediction signal. Deployed in production on real capital ≥7 days. Venues: OKX + Binance + Bybit
      (deepest liquidity, lowest unit cost; Deribit deferred to post-cutover). Wires through
      `mlr-p4-strategy-calibrated-signals` + `mlr-p4-cost-aware-strategy` + live model registry / hot-reload / per-trade
      `model_version` tagging — all P0 May-23-blockers. See `plans/archive/operator_decisions_2026_05_08.plan.md`.
- [x] ✓ **Model retraining cadence — RESOLVED 2026-05-08.** **Daily** — overnight retrain via ml-training (UTC
      midnight + 30min buffer for tick-data settlement); ml-inference hot-reload picks up new model_version on next
      day-open. Feature staleness budget = 24h hard ceiling, 6h soft target. Alerting thresholds: `ML_SIGNAL_STALENESS`
      warns at 4h, criticals at 12h, kill-switch at 24h.
- [x] ✓ **Capital scale — RESOLVED 2026-05-08.** **Starting allocation $10k notional per venue ($30k total)**. Position
      cap per `ArchetypeConfig.position_cap_usd = 10000` per venue. Drawdown kill-switch `kill_switch_drawdown_pct = 5`.
      Position breach kill-switch `kill_switch_position_breach_pct = 20`. `kill_switch_scope=ARCHETYPE` so a CeFi-ML
      trip does NOT halt DeFi archetypes. Ramp 2× per week absent kill-switch trips, capped at $250k notional total by
      post-cutover review.

## Anti-patterns + workspace-rule cross-references

- **Live = batch**: same code path; only fill source differs (cefi_master shares the unified pipeline; no live-only
  data_types). See CLAUDE.md "Live = batch" rule.
- **Honest absence**: tail-end days of a venue's launch use `record_empty(empty_confirmed)`. No NaN-placeholder rows.
  See `codex/02-data/honest-absence-downstream-handling.md`.
- **Manifest concurrency**: backfill VMs use per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=<unique>`).
- **VM naming**: prefixes per CLAUDE.md "VM Naming Convention" (`cefi-{venue}-{flavor}-{ts}`); add new prefix to
  `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` before launch.

## Assigned active plans

_Active plans declaring `parent_epic: cefi_master`. Workers pick up in priority order (P0 first). Auto-populated by
`scripts/plans/populate_epic_bodies_2026_05_21.py` — the list below was seeded by the 2026-06-20 restructure and the
script keeps it in sync from frontmatter._

**Delegated (CeFi work tracked under service-epic plans, listed for visibility — NOT direct `parent_epic` children):**
[`cefi_manifest_canonicalisation_2026_06_01`](../active/cefi_manifest_canonicalisation_2026_06_01.md) (manifest /
coverage / source) ·
[`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)
(`available_at` stamping — ✅ complete/archived).

## P0 — must complete before next foundation gate

### [`cefi_deribit_binance_futures_bundle_verification_2026_06_20`](../active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra). Verify the DERIBIT options/futures + BINANCE-FUTURES
perp bundle backfill completed (manifest captured %, cluster validation, greeks/IV/funding spot-checks); re-run only
genuine gaps; per-cluster triage of the 2,223 phantom residual.

### [`cefi_ml_directional_continuous_live_2026_06_20`](../active/cefi_ml_directional_continuous_live_2026_06_20.md)

**status**: active · **estimate**: 12 cal AI-days (class: brand-new). Second live CeFi archetype —
`ML_DIRECTIONAL_CONTINUOUS` continuous prediction signal on real capital across OKX + Binance + Bybit ≥7 days, full live
loop + model lifecycle + alerting + kill-switches + DART override + backtest fidelity.

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`venue_heartbeat_calibration_2026_05_post23`](../archive/2026_05/venue_heartbeat_calibration_2026_05_post23.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 5 items DEFERRED-OPERATOR-DECISION; blocked on ≥7 days MTDS live telemetry. ·
**estimate**: 1.8 cal AI-days (class: research)

**Deferred (MIGRATED FROM archived plan)** — P0/P1 post-cutover backlog:

- **Collect inter-message gap telemetry (P0)**: Gate: MTDS live ≥7 days with `LiveConnectivityWatchdog` emitting events.
- **Compute P99 per (venue, data_type) + update UAC `venue_thresholds.py` (P0)**: Gate: telemetry above.
- **Staging smoke test — ≤5 spurious events/venue/day (P1)**: Gate: UAC update above.
- **Codex update — `live-pipeline-architecture.md` heartbeat calibration subsection (P1)**: Gate: UAC update.

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md).
- Write-gate cluster:
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](../active/writegate_honest_coverage_endtoend_2026_05_06.md).
- Shard granularity:
  [`shard_granularity_ssot_propagation_2026_05_06.md`](../archive/shard_granularity_ssot_propagation_2026_05_06.plan.md).
- Sibling asset_group umbrellas: `defi_master`, `tradfi_master`, `sports_master`, `predictions_master`.
- Honest-coverage % surface: `GET /api/data-status/honest-coverage` + `HonestCoverageCard` (deployment-ui). SSOT:
  [`codex/03-deployment/data-status-ui-surface.md`](../../codex/03-deployment/data-status-ui-surface.md). Phase 7F per
  `cross_asset_group_catalogue_audit_2026_05_10.md`.
- Canonical asset_group registry: `unified_api_contracts.canonical.crosscutting.asset_group_registry` (Phase 5C/5D).

## Folded plans (archived 2026-05-07)

- `cefi_venue_universe_expansion_2026_05_01.md` — Tardis venues + DEX perps; CeFi todos lifted above; DEX perp todos
  move to `defi_master`.
- `cefi_tradfi_tick_data_backfill_2026_04_10.md` — CeFi half lifted above; TradFi half lifted into `tradfi_master`.
- `market_tick_data_to_100pct_2026_05_05.md` (CeFi slice) — full plan archived after splitting per asset_group; CeFi
  slice is in this umbrella; other slices in their respective asset_group umbrellas.

## DONE-2026-05-08 — Tab F2 cefi-available-at-stamping (BLOCKED, no code shipped)

Tab F2 (`cefi-available-at-stamping-tab`) of
[`work_split_2026_05_08_ikenna.md`](../active/work_split_2026_05_08_ikenna.md) § "Spawn prompts — fresh fan-out:
instruments-service + MTDS". Spawn task structurally blocked on probe; flagged per CLAUDE.md "Findings Triage
Discipline" Case 5 BIG. **No code shipped — only doc landings.**

Commits shipped:

- PM@c3b5e070 — `docs(plans): cefi available_at Tab F2 blocked — file structural mismatch flagged`. 3 files, 260
  insertions: new § "Open questions" Q1 on this plan + new
  [`plans/archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md`](../archive/issues/cefi_available_at_spawn_task_structural_mismatch_2026_05_08.md)
  - cross-side ping in [`plans/active/_agent_pings.md`](../active/_agent_pings.md).
- PM@&lt;next sha&gt; — this DONE block append.

What this session did NOT do (per "don't edit unfamiliar files when blocked" + "Plans Run To Actual Completion" HARD
RULEs):

- did NOT ship `stamp_available_at_cefi_tick` UTL helper (master-gate A.10; needs UAC SOURCE_PRIORITY shape extension
  first; Tab 2 LIVE-PIPELINE / writegate Phase 2.D collision boundary).
- did NOT extend UAC `SOURCE_PRIORITY` shape with per-source `emission_latency_ms` field (cross-cutting design call =
  Ikenna-side).
- did NOT modify any MTDS source code (cli/handlers/_\*.py / engine/orchestrator.py / market_interface/adapters/cefi/_).
- did NOT create per-venue adapter files (the spawn prompt's premise is wrong; reshape to per-callsite is the
  recommended next-agent action per issue-doc § "Recommended decision").

Items still open (deferrals already captured as plan todos before this DONE block — per CLAUDE.md EOD-audit clause):

- **UAC SOURCE_PRIORITY emission_latency field** — captured in
  [`available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
  Phase 1 P0 todo line 260-264 ("CeFi adapter stamping" cites the formula but the field doesn't exist yet) + new
  issue-doc § "Recommended decision (1)".
- **UTL `stamp_available_at_cefi_tick` helper** — captured in
  [`available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
  Phase 1 P0 (TRACKED writegate Phase 2.D adapter stamping helpers shipped — but only sports-shaped helpers exist; this
  is the unticked half) + new issue-doc § "Recommended decision (2)".
- **Per-callsite wiring at writer boundary** — captured in
  [`available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
  Phase 1 P0 "CeFi adapter stamping" todo + new issue-doc § "Recommended decision (3)" + cefi_master § "Open questions"
  Q1.

Next agent picks up at: master-gate clear (UAC SOURCE_PRIORITY field + UTL `stamp_available_at_cefi_tick` shipped) →
re-read issue-doc § "Recommended decision" → mechanically wire ~5-7 callsites at writer boundary in MTDS
`cli/handlers/*` + `engine/orchestrator.py:1940` + the writegate Phase 2.B refactor's bar-write path.
