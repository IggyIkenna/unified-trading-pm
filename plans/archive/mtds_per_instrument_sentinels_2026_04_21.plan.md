---
doc_type: plan
title: mtds-per-instrument-sentinels
summary: Phase 8 — tighten MTDS honest-coverage denominator to per-instrument for per-instrument-shard data_types (trades
  / book_snapshot_5 / derivative_ticker / options_chain / futures_chain).
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-ui,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-21
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: deployment-api, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [availability_manifest_v4_and_data_status_2026_04_13, honest_coverage_metrics_2026_04_19]
todos:
  - { id: wave-8b-scaffold-uac-accessor, content: "- [x] [AGENT] P0. WAVE 8B — UAC
        `get_expected_instruments_for_venue(venue, data_type, *, as_of_date, instruments_provider=None, cap=None)`
        accessor in `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`. Returns
        `list[str]` of canonical instrument_ids that are per-instrument shard members on (venue, data_type, as_of_date).
        Per-instrument data_types = {trades, book_snapshot_5, derivative_ticker, options_chain, futures_chain,
        dex_swaps, dex_pools, lending_indices, oracle_prices, lst_rates, rewards, risk_params, prediction_trades,
        prediction_book_snapshot, prediction_market_metadata}. Venue-level data_types = {liquidations, ohlcv_1m,
        ohlcv_15m, ohlcv_24h, tbbo, gas_fees, perp_funding, odds}. Returns empty list (not None) for venue-level
        data_types so callers can branch on `if expected_instruments: fan_out_tier_3 else: tier_2`. Export from
        `unified_api_contracts` root. Seed 10+ unit tests covering (a) per-instrument dt returns capped list, (b)
        venue-level dt returns `[]`, (c) unknown (venue, dt) returns `[]`, (d) cap honoured when provider overshoots,
        (e) `_SPOT_MVP_SEED_INSTRUMENTS` / `_PERP_MVP_SEED_INSTRUMENTS` used when `instruments_provider is None` (MVP
        cap path). Register in `tests/unit/test_mtds_venue_coverage.py` alongside the
        `get_expected_data_types_for_venue` suite.

        ", status: done, note: Scaffolded in WAVE 8B — see UAC commit hash in plan notes section below. }
  - { id: wave-8c-mtds-orchestrator-per-instrument-sentinel, content: "- [x] [AGENT] P0. MTDS orchestrator — in
        `market-tick-data-service/market_tick_data_service/engine/orchestrator.py` (lines ~1352-1472), replace the
        per-(venue, data_type) Tier-2 sentinel with a per-(venue, data_type, instrument_id) Tier-3 fan-out for
        per-instrument shard data_types. For venue-level data_types, keep the current per-(venue, data_type) Tier-2
        emission. Logic: call `get_expected_instruments_for_venue(venue, dt, as_of_date=date,
        instruments_provider=_orchestrator_instrument_provider, cap=_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP)`; iterate;
        skip instruments already present in CAPTURED shards (track `captured_instruments_by_venue_dt: dict[tuple[str,
        str], set[str]]`); emit `record_empty` / `record_failed` per instrument. The `_orchestrator_instrument_provider`
        function reads the already-loaded-in-memory instruments set from the current pipeline step (the same source
        `_fetch_one_venue` uses for its `instrument_ids` arg); never reads GCS inline inside the sentinel pass. Add
        module-level `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50` constant (MVP threshold — see note below). Log each
        per-venue-dt fan-out emitting >0 rows at INFO level with instrument count, mirroring the SPORTS Tier-2 fan-out
        log line. Add 3 new unit tests under `tests/unit/test_orchestrator_per_data_type_sentinel.py` covering (a)
        per-instrument fan-out for CEFI `trades`, (b) venue-level preserved for `liquidations`, (c) captured-instrument
        skip suppression.

        ", status: todo, blocked_by: wave-8b-scaffold-uac-accessor }
  - { id: wave-8d-deployment-api-aggregator, content: "- [x] [AGENT] P0. deployment-api aggregator — extend
        `_mtds_honest_coverage_for_venue` (`deployment-api/deployment_api/services/data_status_service.py` lines
        ~526-619) to iterate per-instrument for per-instrument shard data_types. Reuse UAC
        `get_expected_instruments_for_venue`. New counted unit = `(venue, data_type, instrument_id, date)` for
        per-instrument dt; `(venue, data_type, date)` preserved for venue-level dt. Expected denominator =
        `len(expected_instruments) * len(expected_dates)` per per-instrument dt. Found = distinct `(instrument_id,
        date)` tuples inside `venue_df_ok` gated on capture_status. Add fallback path for manifest rows that pre-date
        per-instrument fan-out (no `instrument_id` column or empty values) — count as venue-level aggregate so coverage
        % doesn't regress on legacy backfills. Add 5 new unit tests under `tests/unit/test_data_status_service.py`.

        ", status: todo, blocked_by: wave-8c-mtds-orchestrator-per-instrument-sentinel }
  - { id: wave-8e-mvp-cap-size-rollout-strategy, content: "- [x] [AGENT] P0. MVP cap + rollout config —
        `--per-instrument-sentinel-cap INT` CLI flag wired through MTDS `cli/main.py` → `tick_data_handler.py` →
        `process_ticks(per_instrument_sentinel_cap=...)` → `get_expected_instruments_for_venue(..., cap=sentinel_cap)`.
        Module-level `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50` preserved as MVP fallback when flag absent. Rollout
        tiers (MVP=50 / Expanded=200 / Full=10000) documented in new `/codex/02-data/per-instrument-sentinel-rollout.md`
        — promotion criteria (manifest row-count drift <5%/day for 30d; honest-coverage ±2pp; INSTRUMENT_PROVIDER_FAILED
        <5/day; record_empty p99 <2s; GCS object budget <10M), observability gates, rollback path including emergency
        `--per-instrument-sentinel-cap=0` Tier-3-disabled escape hatch. Registered in `codex/00-SSOT-INDEX.md`. 2 new
        unit tests in `tests/unit/test_orchestrator_per_data_type_sentinel.py` — CLI argparse + end-to-end cap honoured
        (cap=2 bounds Tier-3 fan-out to 2 instruments per dt).

        ", status: done, blocked_by: wave-8d-deployment-api-aggregator }
  - { id: wave-8f-codex-matrix-update, content: '- [x] [AGENT] P0. Codex + tests + workspace QG — update
        `unified-trading-pm/codex/02-data/mtds-data-source-coverage-matrix.md` § 2 & § 4 coverage-axis tables so
        per-instrument-shard rows say "emits Tier-3 sentinel (venue × data_type × instrument × date)" instead of the
        current Tier-2 text. Update § 7 aggregator pseudocode to show the per-instrument dt branch. Update § 8 to move
        the "Instrument-level expected" bullet from ⏳ to ✅ with closing-date + commit-hash. Run `bash
        scripts/quality-gates.sh` on all 4 repos (UAC, MTDS, deployment-api, unified-trading-pm) and confirm clean.
        Final phase — promote plan checkboxes to done, request human `[unlock-plan]` on PM to archive.

        ', status: todo, blocked_by: wave-8e-mvp-cap-size-rollout-strategy }
isProject: true
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

Phase 6d / Phase 7 closed per-venue × per-data_type Tier-2 sentinels plus the SPORTS per-(bookmaker, league,
fixture-date) Tier-2 fan-out. Per `/codex/02-data/mtds-data-source-coverage-matrix.md` §§ 2, 4 and 8, the remaining gap
is that `trades` / `book_snapshot_5` / `derivative_ticker` / `options_chain` / `futures_chain` (plus the DeFi
per-market/per-pool equivalents and PREDICTION per-conditionId) are per-instrument shards. The honest-coverage
denominator currently under-counts: 1 shard/venue/day when the adapter writes ~200 shards/day (BINANCE-FUTURES perps).

### Pre-audit manifest

| Repo                     | File                                                         | Line(s)                                                                               | Action                                                                                                                                                                                     |
| ------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| unified-api-contracts    | `unified_api_contracts/registry/market_data_categories.py`   | after line 799 (end of file)                                                          | Add `_PER_INSTRUMENT_SHARD_DATA_TYPES` frozenset, `_SPOT_MVP_SEED_INSTRUMENTS` + `_PERP_MVP_SEED_INSTRUMENTS` tables, `get_expected_instruments_for_venue()` function                      |
| unified-api-contracts    | `unified_api_contracts/__init__.py`                          | after line 586 (export list) + after line 1217 (**all**)                              | Add `get_expected_instruments_for_venue` import + `__all__` entry                                                                                                                          |
| unified-api-contracts    | `tests/unit/test_mtds_venue_coverage.py`                     | append                                                                                | 10+ unit tests for the accessor                                                                                                                                                            |
| market-tick-data-service | `market_tick_data_service/engine/orchestrator.py`            | ~1352-1472 (Tier-2 fan-out block)                                                     | Replace per-(venue, dt) sentinel with per-(venue, dt, instrument_id) Tier-3 for per-instrument dt; keep Tier-2 for venue-level dt                                                          |
| market-tick-data-service | `market_tick_data_service/cli/handlers/tick_data_handler.py` | existing `max_instruments` wiring (~line 158)                                         | Add `--per-instrument-sentinel-cap` + thread through orchestrator call                                                                                                                     |
| market-tick-data-service | `tests/unit/test_orchestrator_per_data_type_sentinel.py`     | append                                                                                | 3 new per-instrument fan-out tests                                                                                                                                                         |
| deployment-api           | `deployment_api/services/data_status_service.py`             | `_mtds_honest_coverage_for_venue` lines 526-619 + `_mtds_expected_dates_for_venue_dt` | Per-instrument expected = `len(expected_instruments) × len(expected_dates)` for per-instrument dt; venue-level preserved for venue-level dt; legacy-row fallback for pre-Phase-8 manifests |
| deployment-api           | `tests/unit/test_data_status_service.py`                     | append                                                                                | 5 new unit tests                                                                                                                                                                           |
| unified-trading-pm       | `/codex/02-data/mtds-data-source-coverage-matrix.md`         | § 2 / § 4 / § 7 / § 8                                                                 | Tier-3 language, new aggregator pseudocode, move instrument-level bullet to ✅                                                                                                             |

### Execution DAG

```
WAVE 8B (DONE) — UAC accessor + tests (leaf, no upstream deps)
        │
        ▼
WAVE 8C — MTDS orchestrator per-instrument sentinel (consumes UAC helper)
        │
        ▼
WAVE 8D — deployment-api aggregator (consumes same UAC helper; denominator swap)
        │
        ▼
WAVE 8E — MVP cap + CLI flag rollout + smoke-test size guardrail
        │
        ▼
WAVE 8F — codex matrix update + workspace QG + plan closeout
```

Each wave is **sequential**. Waves within a wave are PARALLEL (e.g. UAC tests + export + body all land in the same
commit).

### Success criteria per wave

- **8B**: UAC `quality-gates.sh` green; accessor exported from root; 10+ unit tests passing; basedpyright + ruff clean.
- **8C**: MTDS `quality-gates.sh` green; 3 new orchestrator tests passing; existing orchestrator tests unaffected; no
  regression in SPORTS Tier-2 fan-out (Phase 7).
- **8D**: deployment-api `quality-gates.sh` green; 5 new tests passing; aggregator smoke on a fixture manifest shows
  honest denominator lift (expected_shards ~10× higher on BINANCE-FUTURES `trades`).
- **8E**: CLI flag present; smoke passes; codex § 8 documents cap tiers.
- **8F**: All 4 repos `quality-gates.sh` green; codex cross-reference alignment; plan archivable pending
  `[unlock-plan]`.

### Technical constraints

1. **Instrument list provider is injectable.** UAC accessor accepts
   `instruments_provider: Callable[[str, str], list[str]] | None = None` so callers (MTDS orchestrator, deployment-api
   aggregator) can inject their live instrument list. When `None`, UAC falls back to the MVP seed tables, keeping UAC
   free of runtime GCS reads.
2. **Size-capping is MANDATORY.** Never expand the denominator without `cap`. The
   `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50` keeps the 4-year backfill manifest under ~4M rows across 11 CEFI venues ×
   5 per-instrument dts × ~1460 days × 50 caps = ~4M cap. Expanded tier (cap=200) is an opt-in operator-controlled
   rollout.
3. **Legacy row compatibility.** deployment-api aggregator must gracefully degrade for pre-Phase-8 manifests that have
   no `instrument_id` column — treat as venue-level and do not inflate the denominator retroactively on already-written
   dates.
4. **No technical debt.** The per-venue Tier-2 emission for per-instrument dt is **removed**, not kept for backwards
   compat. Aggregator consumers will stop seeing per-venue sentinel rows for `trades` after Phase 8C ships.
5. **Shard-level failure isolation (D10).** If `instruments_provider` raises on a (venue, dt) pair (e.g.,
   instruments-service parquet read failure), the orchestrator logs + emits a Tier-2 venue-level `attempted_failed`
   sentinel with error_code=`INSTRUMENT_PROVIDER_FAILED` and skips Tier-3 for that (venue, dt). Never propagates.

### Follow-ups / Out-of-scope

- Multi-chain DeFi per-pool fan-out (chain axis): already handled by existing per-chain manifest columns; only the
  `instrument_id` axis needs to be threaded through.
- **DeFi POOL / LENDING markets list seed** — MVP seed tables in UAC cover CEFI SPOT_PAIR + PERPETUAL + FUTURE + OPTION
  (BTC, ETH, + top-N). DeFi seed (top-20 UniswapV3 pools by TVL + top-10 Aave reserves) is ~5 engineer-hours — filed as
  a WAVE 8G follow-up after 8F ships.
- Aggregator UI changes (deployment-ui coverage dashboard) to render per-instrument % breakdown — out of scope for Phase
  8; the API will still return aggregate coverage % at the (venue, data_type) level for the dashboard.

### Open questions for human decision (surface during 8E)

1. **MVP cap threshold**: Is `cap=50` the right MVP threshold for Phase 8, or should it be `cap=20` to stay conservative
   on the first pass through a 4-year backfill? Cost impact = linear in cap × number of per-instrument dts × number of
   backfill days. Defaulting to 50 in plan; operator can dial via CLI flag until telemetry lands.
2. **Expanded-tier gate**: Do we wait for 30 days of MVP-tier observation before flipping the expanded tier (cap=200)
   for all CEFI venues? Recommended yes — 30-day bake matches existing honest-coverage Phase B rollout cadence.
3. **Full-tier gate**: Is uncapped per-instrument fan-out acceptable for any venue, or should we always enforce a cap
   (possibly infinity-equivalent) to prevent adapter-bug-induced unbounded fan-out? Recommended always-enforce — set
   Full-tier cap=10_000 as a hard ceiling.

### References

- `unified-trading-pm/codex/02-data/mtds-data-source-coverage-matrix.md` § 8 (Phase 8 stretch goal).
- `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md` — v5 schema with `instrument_id` /
  `instrument_type` columns already present.
- `market-tick-data-service bd24295` — Phase 6d Tier-2 sentinel orchestration (reference pattern).
- `plans/active/availability_manifest_v4_and_data_status_2026_04_13.md` — parent v4→v5 plan.
- `plans/active/honest_coverage_metrics_2026_04_19.md` — Phase B record_empty / record_failed contract.

### Wave log

- **2026-04-21 — WAVE 8B scaffold**: UAC accessor landed with MVP seed tables; commit hash recorded in this section upon
  commit.
