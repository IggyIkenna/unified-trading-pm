---
title: "PricingLedger carry-rate computation in MTDS — dividend_yield + rebase_rate + greeks-service handshake"
parent_epic: mtds_mdps_master
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
assigned_vm: vm-ml
locked_by: live-defi-rollout
locked_since: 2026-05-23
predecessor: plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md (Phase 5 operator-ACK 2026-05-23)
related_plans:
  - plans/active/global_ledger_pnl_attribution_migration_2026_06_01.md
  - plans/epics/mtds_mdps_master.md
  - plans/epics/instruments_master.md
---

# PricingLedger carry-rate computation in MTDS — dividend_yield + rebase_rate + greeks-service handshake

## Scope

Three MTDS/IS deliverables unblock `greeks-service` from consuming `mark_update` events and emitting `MARK_UPDATE` rows
on `PricingLedger` with both option greeks and carry-family rates populated. The discovery plan
(`global_ledger_pnl_attribution_discovery_2026_05_21.md` Phase 5) operator-ACKed 2026-05-23 that (a) `dividend_yield` is
derived in MTDS from IS `CanonicalCorporateAction` history (annualised, formula TBD), (b) `rebase_rate` is the
per-snapshot delta of `lst_rates.exchange_rate` (cumulative exchange_rate stays the IS SSOT, untouched), and (c)
`greeks-service` is the writer for both greek columns and carry-family columns on `PricingLedger.MARK_UPDATE` rows. This
plan sequences the three workstreams; no UAC schema changes are in scope (the `LedgerRow` columns shipped 2026-05-23 in
the discovery plan's Phase 2 — see commit verification under Risk callouts).

## Readiness gates (per PLAN_FORMAT.md)

- **Code**: C0 — design-into-MTDS-and-greeks-service; implementation lands across MTDS + IS + greeks-service repos per
  phase.
- **Deployment**: N/A — design-driven implementation; deployment topology for `greeks-service` belongs to its own epic.
- **Business**: B1 — acceptance criteria defined below.

**B1 acceptance criteria**:

1. `dividend_yield` derived annualised rate emitted on `PricingLedger.MARK_UPDATE` rows where applicable (equities/ETFs
   with dividend history in IS `CanonicalCorporateAction`). Non-applicable instruments (crypto/futures/options) emit
   `None` — never a synthetic zero.
2. `rebase_rate` delta emitted on `PricingLedger.MARK_UPDATE` rows for LST/LRT assets, computed from consecutive
   `lst_rates.exchange_rate` snapshots (Decimal subtraction; cumulative `exchange_rate` in IS `lst_rates` table stays
   untouched as the SSOT). Non-LST instruments emit `None`.
3. `greeks-service` receives `mark_update` Pub/Sub events from MTDS, reads `InstrumentRecord` from IS HTTP API
   (strike/expiry/right/multiplier/exercise_style/asset_class), and writes back to `PricingLedger.MARK_UPDATE` rows with
   both greek columns (option_delta/gamma/theta/vega/rho) AND carry columns
   (funding_rate/lending_rate/borrow_rate/staking_apy/dividend_yield/rebase_rate) populated. End-to-end smoke
   demonstrates a derived ledger consumer (strategy-service `pnl_reconciliation_engine`) reads a populated greek column
   from `PricingLedger`.

## Phase 1 — `dividend_yield` derived rate computation (MTDS)

- [ ] [DESIGN] P0. Annualisation formula spec — TTM dividend × frequency vs trailing-12-month sum vs forward-estimate.
      Quant/operator decision item; capture rationale + edge cases (special dividends, spin-offs, suspended dividends).
      Document in `codex/02-data/ledger-event-taxonomy.md` under `dividend_yield` row.
- [ ] [CODE] P0. Add `dividend_yield` derivation in `market-tick-data-service/market_tick_data_service/derived/` — reads
      IS `CanonicalCorporateAction` via IS HTTP API; computes annualised rate per `instrument_id` using the formula from
      the design item. Decimal arithmetic; no float drift.
- [ ] [CODE] P0. Wire `dividend_yield` into MTDS `MARK_UPDATE` row emission via UAC `LedgerRow.dividend_yield` field
      (shipped in `unified-api-contracts@<sha-pending-2026-05-23>` — verify before merge). Equities/ETFs only; crypto
      paths emit `None`.
- [ ] [TEST] P0. Unit tests: SPY 2024-Q4 dividend stream → assert annualised yield matches expected ~1.3% within
      tolerance; AAPL with quarterly cadence; a no-dividend equity (TSLA) emits `None`. Backtest fixture in
      `tests/derived/test_dividend_yield.py`.
- [ ] [QG] P0. `bash scripts/quality-gates.sh` in `market-tick-data-service` — green before merge. Cross-repo regression
      on `unified-api-contracts` consumer tests (`pricing_ledger` cassette parity).
- [ ] [DOC] P1. Update `codex/02-data/ledger-event-taxonomy.md` — `dividend_yield` row notes "populated for
      equities/ETFs only; `None` for crypto/futures/options"; cite the annualisation formula from Phase 1 design.

## Phase 2 — `rebase_rate` delta computation (MTDS or IS)

- [ ] [DESIGN] P0. Delta-computation strategy decision — per-snapshot delta on every new `lst_rates` row vs
      daily-checkpoint delta. Operator/quant decision (rolling-window cost vs latency for greeks-service consumers).
      Owner repo decision: MTDS derived layer (consistent with `dividend_yield`) vs IS write-time (closer to the source
      table). Captured in `codex/04-architecture/global-ledger-architecture.md` under `rebase_rate`.
- [ ] [CODE] P0. Add `rebase_rate` derivation in the repo chosen above — reads consecutive `lst_rates.exchange_rate`
      snapshots (per `instrument_id` × `chain`); computes per-snapshot delta as `Decimal`. Cumulative `exchange_rate`
      column in IS `lst_rates` parquet stays untouched (SSOT invariant — enforced by integration test).
- [ ] [CODE] P0. Wire `rebase_rate` into `PricingLedger.MARK_UPDATE` row emission via UAC `LedgerRow.rebase_rate` field
      (shipped 2026-05-23 in the same UAC commit as `dividend_yield`). LST/LRT only; non-LST emits `None`.
- [ ] [TEST] P0. Unit tests: stETH 24h snapshot pair (known 2024-12-15 → 2024-12-16) → assert delta matches known daily
      rebase (~0.00018 within tolerance); rETH and cbETH equivalents; non-LST asset (USDC) emits `None`. Integration
      test: IS `lst_rates.exchange_rate` cumulative column unchanged after derivation runs.
- [ ] [QG] P0. `bash scripts/quality-gates.sh` in the owner repo (MTDS or IS) — green before merge. Cross-repo
      regression on the other side of the IS↔MTDS contract (per
      `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`).
- [ ] [DOC] P1. Update `codex/02-data/ledger-event-taxonomy.md` — `rebase_rate` row notes "populated for LST/LRT only;
      `None` for everything else; cumulative `exchange_rate` remains in IS `lst_rates` table as SSOT".

## Phase 3 — greeks-service ⟷ MTDS handshake (greeks-service)

- [ ] [CODE] P0. `greeks-service` subscribes to MTDS `mark_update` Pub/Sub topic — consumer config in
      `greeks-service/greeks_service/config.py` via `UnifiedCloudConfig` (no `os.getenv()`). Backpressure + idempotency
      via UTL event helpers.
- [ ] [CODE] P0. `greeks-service` reads IS `InstrumentRecord` via IS HTTP API (strike/expiry/right/multiplier/
      exercise_style/asset_class) at startup + on `InstrumentRecord` change events. Cached locally with TTL + hot-reload
      via `ApiKeyReloader` pattern.
- [ ] [CODE] P0. `greeks-service` writes back to `PricingLedger.MARK_UPDATE` rows with option_delta/gamma/theta/vega/rho
      populated via UAC `LedgerRow` fields (shipped `unified-api-contracts@<sha-pending-2026-05-23>`). Same `event_id`
      keyed back to the originating MTDS event.
- [ ] [CODE] P0. `greeks-service` writes carry-family columns (funding_rate/lending_rate/borrow_rate/staking_apy/
      dividend_yield/rebase_rate) reading from MTDS rate feeds (funding/lending/borrow) + IS LST data
      (staking_apy/rebase_rate) + MTDS-derived `dividend_yield`. None-handling per Phase 1/2 conventions.
- [ ] [CODE] P0. Black-Scholes greek computation kernel for vanilla European/American options — pure-Decimal
      implementation in `greeks-service/greeks_service/kernels/black_scholes.py`. Extensibility hook (`GreekKernel`
      protocol) for SABR/local-vol/numerical-greeks in a Phase 2 follow-up plan.
- [ ] [CODE] P1. Batch-mode `greeks-service` for backfill — cron-driven + EPHEMERAL_BATCH VM cohort prefix
      `greeks-compute-` registered in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` with
      `lifecycle_class=EPHEMERAL_BATCH`. Reads historical MTDS `mark_update` parquets; writes historical
      `PricingLedger.MARK_UPDATE` rows.
- [ ] [TEST] P0. End-to-end smoke (`tests/integration/test_greeks_handshake.py`): MTDS emits `mark_update` for a known
      vanilla call → `greeks-service` receives → writes back `PricingLedger.MARK_UPDATE` → strategy-service
      `pnl_reconciliation_engine` reads the greek column. Uses GCP PubSub + Storage emulators
      (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`).
- [ ] [QG] P0. `bash scripts/quality-gates.sh` in `greeks-service` + cross-repo regression in `market-tick-data-service`
      (writer-side cassette parity) + `strategy-service` (consumer-side `pnl_series` route smoke) — all green before
      merge.

## Full-execution criterion (per `Plans Run To Actual Completion` HARD RULE)

- All three B1 acceptance criteria pass end-to-end on real infra (`asia-northeast1-c` GCS + Pub/Sub; no emulator).
  - **What ran**: MTDS `dividend_yield` + `rebase_rate` derivation batch on representative instrument universe;
    `greeks-service` live consumer on `mark_update` for ≥1h; sampled `PricingLedger` parquet inspection.
  - **Verification**: representative `PricingLedger.MARK_UPDATE` rows inspected per asset_group — equities have
    populated `dividend_yield`, LSTs have populated `rebase_rate`, options have populated greek columns; non-applicable
    instruments have `None` (not synthetic zeros). `gsutil cat` sample + Python `pyarrow` row dump shows
    operationally-correct state.

## Risk callouts

- **Foundation-completion-gate**: PricingLedger carry + greek columns depend on the UAC `LedgerRow` extension shipped
  2026-05-23 in the discovery plan's Phase 2. **Pending commit verification** — slot-1 main confirms UAC@sha before
  Phase 1 code lands. Layer-N+1 work in `greeks-service` cannot begin until that UAC commit is on `live-defi-rollout`.
- **greeks-service repo bootstrap**: the `greeks-service` repo must be initialised
  (`gh repo create IggyIkenna/greeks-service`) + onboarded to PM workflow templates + tarball deployment scripts before
  Phase 3 code can land. Operator-actionable; capture as a slot-1 ping under this plan if not done by Phase 1
  completion.
- **Annualisation methodology (Phase 1)**: quant-call. Operator likely wants to review the formula spec before
  implementation. Phase 1 DESIGN todo is gated on operator-ACK; do not start Phase 1 CODE without that ACK.
- **Phase 2 owner-repo split**: MTDS-derived vs IS-write-time is an architecture call. The decision impacts the IS↔MTDS
  contract (`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`) — if IS becomes a writer of derived data,
  that contract needs an explicit amendment, otherwise QG STEP 5.70's `no_silent_absence_handlers.sh` may flag the new
  derivation as a contract drift.
- **None vs zero discipline**: every Phase 1/2/3 emission path MUST emit `None` for non-applicable instruments — never a
  synthetic zero (which would silently corrupt downstream PnL attribution). Unit tests in each phase explicitly assert
  `None` for the non-applicable case.
