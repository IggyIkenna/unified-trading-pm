---
doc_type: codex-ssot
title: Greeks-Service Overview
summary:
  Dedicated derivation service computing option greeks (delta/gamma/theta/vega/rho) + carry-family rates and writing
  MARK_UPDATE rows to the PricingLedger SSOT — live (Pub/Sub) and batch modes share one Black-Scholes/carry kernel.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, features-service, greeks-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: [greeks, strategy, mtds, instruments, reconciliation]
related:
  [
    /codex/04-architecture/global-ledger-architecture.md,
    /codex/02-data/ledger-event-taxonomy.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-05-23
authoritative_for: [greeks-service greek + carry-rate PricingLedger derivation]
referenced_by: [/codex/04-architecture/global-ledger-architecture.md]
owner:
last_reviewed: 2026-05-23
code_refs:
type: architecture
---

# Greeks-Service Overview

> **[DELTA 2026-05-23]** **New dedicated service codified** — operator decision in
> `plans/archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md` (ARCHIVED; greeks compute is its own
> service, not absorbed into MTDS or strategy-service). Phase 1 skeleton landed at `greeks-service/` (15 files / 575
> lines); Phase 2+ (`BlackScholesGreeksCalculator`, carry-rate readers, batch/live mode handlers, PricingLedger
> writers) SHIPPED under `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` Phase 3 (status:
> complete) — the `..._migration_2026_06_01.md` plan originally cited here never actually carried this work; it was
> archived as a stub and the work folded into the pricing-ledger plan instead (see that plan's "Consolidation note").
> **[DELTA 2026-08-21]** Verified `greeks_service/config_reloaders.py` (DomainConfigReloader-based instrument hot
> -reload) remains an unwired Phase 1 stub with zero callers — the instrument-metadata need it was meant to serve was
> fulfilled instead by `InstrumentReader` (HTTP + TTL cache) in the Phase 3 work above. No active plan owns wiring it;
> left as-is rather than inventing new design intent.

## What it is

greeks-service is the dedicated workspace computation service that derives **option greeks** (`option_delta`, `gamma`,
`theta`, `vega`, `rho`) and **carry-family rates** (`funding_rate`, `lending_rate`, `borrow_rate`, `staking_apy`,
`dividend_yield`, `rebase_rate`) for every instrument the workspace marks-to-market, and writes the results to the
global `PricingLedger` SSOT (`unified_api_contracts.canonical.crosscutting.ledger`) as `event_type=MARK_UPDATE` rows. It
is a pure derivation step: fan-in from MTDS mark prices + IV + instruments-service instrument metadata, fan-out to
PricingLedger consumed by strategy / execution / risk / pnl-attribution.

---

## Why a dedicated service (vs MTDS or strategy-service absorption)

| Reason                                                      | Why a separate service wins                                                                                                                                                                                                                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Keep mark-price write path lock-step                        | MTDS owns the canonical mark/mid/IV write path. Injecting greeks compute into MTDS handlers couples capture-cadence to compute-cadence and risks blocking the mark write on a slow Black-Scholes call.                                            |
| Separate concern from strategy logic                        | strategy-service consumes greeks (`PnLAttributor`, `RiskGuard`, `ExposureAggregator`); making it also a writer creates a circular dependency and forces every backtest replay to re-derive greeks.                                                |
| Backend swap (Black-Scholes → SABR / local-vol / numerical) | A standalone service lets us swap the computation kernel per asset_group without touching MTDS or strategy. Path-dependent options will need numerical greeks; vanilla options run analytic Black-Scholes — both behind the same writer contract. |
| Cadence asymmetry                                           | MTDS captures at tick frequency. Greeks for equities recompute daily; perp funding every 8h (CeFi) / 1h (DeFi); options per-minute. A dedicated service can pace each asset_group independently without distorting MTDS handlers.                 |
| Operational isolation                                       | A bad greek-formula rollout cannot block mark capture (data heartbeat). Crash/OOM isolation is per-service VM cohort.                                                                                                                             |

---

## Inputs

### MTDS `mark_update` Pub/Sub topic

| Field consumed       | Type     | Source          | Used for                          |
| -------------------- | -------- | --------------- | --------------------------------- |
| `instrument_id`      | str      | MTDS canonical  | Join key to InstrumentRecord      |
| `mark_price`         | Decimal  | MTDS mark/mid   | Underlying spot in Black-Scholes  |
| `implied_volatility` | Decimal  | MTDS IV surface | Vol input to greeks               |
| `timestamp`          | datetime | MTDS event time | `event_time` on PricingLedger row |
| `venue_id`           | str      | MTDS            | Carry-rate venue scoping          |
| `asset_group`        | StrEnum  | MTDS            | Cadence + backend selection       |

### instruments-service `InstrumentRecord` (read via IS contract)

| Field consumed      | Type     | Used for                                                     |
| ------------------- | -------- | ------------------------------------------------------------ |
| `strike`            | Decimal  | Option strike in Black-Scholes                               |
| `expiry`            | datetime | Time-to-expiry for theta / time-decay                        |
| `right`             | StrEnum  | `CALL` / `PUT` branch                                        |
| `multiplier`        | Decimal  | Contract size for greek scaling                              |
| `exercise_style`    | StrEnum  | `EUROPEAN` / `AMERICAN` / `BERMUDAN` — backend dispatch      |
| `settlement_style`  | StrEnum  | `CASH` / `PHYSICAL` — affects rho                            |
| `dividend_schedule` | list     | Discrete dividend stream for equity options                  |
| `asset_class`       | StrEnum  | OPTION vs PERP vs SPOT vs EQUITY → which greeks/carry fields |

Per the IS→MTDS contract (`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`), greeks-service consumes
`InstrumentRecord` via the same canonical reader path — never re-derives strike/expiry from venue strings.

---

## Outputs

PricingLedger rows with `event_type=MARK_UPDATE` and **greek + carry columns populated**. Column names match
`unified_api_contracts.canonical.crosscutting.ledger.LedgerRow`:

| Column           | Type          | Populated for                        | Definition                                                                                                                |
| ---------------- | ------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `option_delta`   | Decimal\|None | options                              | ∂Price/∂Underlying (greek delta; named `option_delta` to avoid collision with the row-level asset-quantity `delta` field) |
| `gamma`          | Decimal\|None | options                              | ∂²Price/∂Underlying²                                                                                                      |
| `theta`          | Decimal\|None | options                              | ∂Price/∂t per day                                                                                                         |
| `vega`           | Decimal\|None | options                              | ∂Price/∂Vol (per 1.0 vol point)                                                                                           |
| `rho`            | Decimal\|None | options                              | ∂Price/∂r (rate sensitivity)                                                                                              |
| `funding_rate`   | Decimal\|None | perps (CeFi + DeFi)                  | Per-period funding rate (sign convention: positive = longs pay shorts)                                                    |
| `lending_rate`   | Decimal\|None | money-market supply legs             | Annualised supply APR (Aave/Compound/Morpho)                                                                              |
| `borrow_rate`    | Decimal\|None | money-market borrow legs             | Annualised borrow APR                                                                                                     |
| `staking_apy`    | Decimal\|None | staked assets (LSTs, native staking) | Annualised staking yield                                                                                                  |
| `dividend_yield` | Decimal\|None | equity / equity-option               | Annualised dividend yield (continuous-equivalent for Black-Scholes)                                                       |
| `rebase_rate`    | Decimal\|None | rebasing LSTs (stETH-style)          | Per-snapshot LST `exchange_rate` delta (cumulative since last snapshot)                                                   |

Every row carries `client_id` (set to the SSOT-pricing sentinel, since PricingLedger is client-agnostic) per the
`client_id` discipline below.

---

## Two runtime modes

| Mode      | Trigger                                         | Throughput target               | VM lifecycle      |
| --------- | ----------------------------------------------- | ------------------------------- | ----------------- |
| **live**  | Pub/Sub streaming from MTDS `mark_update` topic | Per-tick (matches MTDS cadence) | `LONG_LIVED_LIVE` |
| **batch** | Cron-based backfill over a manifest horizon     | Walk-once parquet pipeline      | `EPHEMERAL_BATCH` |

**Both modes share the same computation kernels.** Per the workspace-wide `Batch = Live` HARD RULE, greeks-service has
exactly one code path for `BlackScholesGreeksCalculator` + `CarryRateReader`; the only difference is the input adapter
(Pub/Sub envelope decoder vs manifest-driven parquet reader) and the sink adapter (PricingLedger row appender →
streaming-write vs bundled batch-write). No standalone backtest greek calculator. No asset-group-specific kernels.

---

## Cadence table per asset_group

Operator-tunable via `GreeksServiceConfig`. Defaults:

| asset_group / instrument family              | Cadence                  | Backend                                | Notes                                                   |
| -------------------------------------------- | ------------------------ | -------------------------------------- | ------------------------------------------------------- |
| Perps — CeFi                                 | Per funding period (8h)  | `funding_rate` read from MTDS          | Aligned with venue funding settlement clocks            |
| Perps — DeFi                                 | Per funding period (1h)  | `funding_rate` read from on-chain      | Hyperliquid / Aster / Drift                             |
| Options                                      | Per minute               | Black-Scholes (vanilla European)       | SABR/local-vol post-Phase 2 for skew-sensitive surfaces |
| Equities                                     | Per day (close-to-close) | `dividend_yield` read from IS schedule | Aligns with TradFi market session                       |
| Spot                                         | Per minute               | n/a (carry rates only)                 | Lending/borrow/staking_apy/rebase_rate as applicable    |
| LSTs (stETH / rETH / cbETH / JitoSOL / mSOL) | Per minute               | `staking_apy` + `rebase_rate`          | Rebase-rate from on-chain `exchange_rate` snapshots     |

---

## Computation backends (Phase 2 placeholder)

| Backend                        | Asset surface                               | Status                       |
| ------------------------------ | ------------------------------------------- | ---------------------------- |
| `BlackScholesGreeksCalculator` | Vanilla European options on liquid surfaces | Phase 2 — first ship         |
| `SABRGreeksCalculator`         | Skew-sensitive equity / FX option surfaces  | Phase 3 — extensibility hook |
| `LocalVolGreeksCalculator`     | Path-dependent / Bermudan exercise          | Phase 3 — extensibility hook |
| `NumericalGreeksCalculator`    | Path-dependent (Asian / barrier / lookback) | Phase 4 — finite-difference  |

The writer contract (PricingLedger row shape) is identical across backends; selection happens at the dispatcher keyed on
`(asset_class, exercise_style, settlement_style)`.

### Verified NON-finding — Black-Scholes kernel is correctly local (UTL/UAC reuse audit, 2026-07-13)

`greeks_service/kernels/black_scholes.py` implements the `GreekKernel` protocol as a pure-function BSM library — **there
is no UTL/UAC equivalent to reuse**: UAC ships only `DeltaStrike`-family option-identity/schema types (option metadata,
not pricing math), and UTL carries no options-pricing kernel. The `Decimal`-only vanilla-European BSM implementation
here is the correct, sole home for this compute; do not re-flag it in a future reuse audit. SSOT:
`plans/archive/2026_07/utl_uac_reuse_consolidation_remediation_2026_06_10.md` § Verified NON-findings.

---

## Plug-in points

| Plug-in point         | Direction | Mechanism                                                                         | Owner module                                      |
| --------------------- | --------- | --------------------------------------------------------------------------------- | ------------------------------------------------- |
| MTDS Pub/Sub          | read      | `mark_update` topic subscriber (Pub/Sub in GCP)                                   | `greeks_service/inputs/mark_update_sub.py`        |
| IS `InstrumentRecord` | read      | Canonical reader via instruments-service contract                                 | `greeks_service/inputs/instrument_reader.py`      |
| Batch backfill (cron) | read      | Manifest-driven parquet walk over horizon                                         | `greeks_service/batch/backfill.py`                |
| PricingLedger         | write     | `LedgerRow(event_type=MARK_UPDATE, ...)` append; bucket via `resolve_bucket_name` | `greeks_service/outputs/pricing_ledger_writer.py` |

All bucket lookups via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — no inline
`gs://` f-strings (QG STEP 5.69 enforces).

---

## VM topology

VM prefix declared in `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`:

| VM prefix         | LifecycleClass    | Cohort                                                    |
| ----------------- | ----------------- | --------------------------------------------------------- |
| `greeks-compute-` | `LONG_LIVED_LIVE` | Live streaming greek + carry compute (Pub/Sub subscriber) |
| `greeks-compute-` | `EPHEMERAL_BATCH` | Backfill cohort (one VM per asset_group × horizon-window) |

Per the `VmPrefixSpec` Phase A.2 contract, every entry MUST declare a `lifecycle_class`. Both the long-lived streaming
VM and the ephemeral batch cohort share the `greeks-compute-` prefix but are differentiated by `lifecycle_class`; the
prefix maps to the same PricingLedger sink bucket in both lifecycles. T+10min post-launch verification per
`/codex/05-infrastructure/vm-tarball-deployment.md` § "Post-launch verification" applies (no fire-and-forget launches).

---

## Boundary vs features-service volatility

features-service `volatility` computes ATM IV, skew, term-structure, and second-order greeks from processed option chain
candles. Its `greeks_block` validity check depends on a `delta` column in those candles — currently sourced from
venue-provided marks (often absent for DeFi options, unreliable for illiquid TradFi strikes).

**Authoritative boundary (Phase 3+):** greeks-service is the single source of truth for all greek columns, including
`option_delta`. features-service MUST consume `option_delta` from the PricingLedger SSOT rather than re-deriving from
venue marks or running its own BSM. This avoids:

- Greek divergence between greeks-service and features-service (different IV sources, different models)
- Silent None greeks for DeFi options (Lyra/Aevo/Dopex not yet configured, but design must be forward-compatible)
- Latency coupling: features-service waiting on venue greeks rather than reading PricingLedger

**Consumer pattern (features-service):** read PricingLedger rows for the relevant `asset_group` + `date`, join on
`asset_canonical_id` (= `instrument_id`), take `option_delta` from the latest `event_type=MARK_UPDATE` row before the
features window close. Fall back to `None` if no row exists (emit `empty_confirmed` for that shard's `greeks_block`).

**Status (2026-05-24):** kernel + handler + batch backfill wired in greeks-service. features-service PricingLedger
reader and greeks_block join are pending (plan Phase 3 CODE P0 — BLOCKED-SCHEMA: requires `underlying_spot` field in
`MarkUpdateMessage` for TradFi IV fitting before features-service consumption fully closes the gap).

---

## Cross-references

- `/codex/04-architecture/global-ledger-architecture.md` — PricingLedger SSOT this service writes into; greeks-service
  is a fifth PricingLedger writer alongside MTDS and instruments-service.
- `/codex/02-data/ledger-event-taxonomy.md` — `MARK_UPDATE` event type and the PricingLedger routing rule
  (`event_type=MARK_UPDATE` → PricingLedger).
- `/codex/04-architecture/client-funds-isolation.md` — HARD RULE: greeks-service does NOT move funds, but every emitted
  `LedgerRow` inherits the `client_id` discipline (PricingLedger rows carry the client-agnostic sentinel, never blank;
  readers join on `client_id` downstream).
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS as the SSOT for instrument metadata;
  greeks-service consumes `InstrumentRecord` via the same canonical reader path.
- `/codex/02-data/availability-manifest-and-data-status.md` — greeks-service emits the standard 4-state `capture_status`
  per shard (`captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted`); no silent placeholder rows.
- `plans/archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md` — ARCHIVED; operator decision
  (2026-05-23) to spin greeks-service as a standalone service.
- `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` — ARCHIVED, status complete; Phase 3 shipped
  the calculator/handler/batch-backfill/PricingLedger writer wiring (the `..._migration_2026_06_01.md` plan cited
  here previously never carried this work — see the DELTA callout above).
