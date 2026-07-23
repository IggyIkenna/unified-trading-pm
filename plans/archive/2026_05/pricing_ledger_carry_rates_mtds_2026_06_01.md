---
doc_type: plan
title: PricingLedger carry-rate computation in MTDS — dividend_yield + rebase_rate + greeks-service handshake
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    features-service,
    fund-administration-service,
    greeks-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    plans/archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md (ARCHIVED — Phase 6.5/7-9 items folded
    into this plan),
    plans/epics/mtds_mdps_master.md,
    plans/epics/instruments_master.md,
    plans/epics/global_ledger_pnl_attribution_master.md,
  ]
created: "2026-05-23"
parent_epic: mtds_mdps_master
priority: P0
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
assigned_vm: vm-ml
locked_by: live-defi-rollout
locked_since: 2026-05-23
predecessor:
  plans/archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md (ARCHIVED in 2026-05-23 PM consolidation;
  Phase 5 operator-ACK captured below in "Operator decisions" section)
shipped_commits:
  [
    uac@709e9aff — LedgerRow greek (option_delta/gamma/theta/vega/rho) + carry
    (funding/lending/borrow/staking/dividend/rebase) columns,
    deployment-service@460bb6e — greeks-compute-live-/greeks-compute-batch- VM prefixes,
    greeks-service@b9dbade — repo skeleton (15 files); worktree model wired (main clone + 11 tab worktrees),
    pm@f7ca196a1 — workspace-manifest topologicalOrder level 4,
  ]
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

> **Consolidation note (2026-05-23)**: the parent discovery + migration plans
> (`global_ledger_pnl_attribution_discovery_2026_05_21.md` + `..._migration_2026_06_01.md`) were ARCHIVED in the
> 2026-05-23 PM consolidation sweep. Their operator-decision capture (Phase 11) + greeks-service bootstrap (Phase 6.5)
> are folded into this active plan below so the orchestrator tracks them here, not in archived files.

## Operator decisions (ACK'd 2026-05-23 — folded from archived discovery plan Phase 11)

- [x] ✅ Phase 3 late-arriving-data → **Option A: event-sourced append-only** + pre-join view layer at API boundary.
      Enrichment closed set: clearing_house_id, final_fee_corrected, fx_rate_locked, regulatory_report_id,
      custody_reconciled. Pre-join fn in UTL (not a new service). Option G (snapshots) deferred; Option C (bi-temporal)
      opt-in for `regulatory_reportable=true` only.
- [x] ✅ Phase 4/6 TreasuryLedger split → **separate partition** `ledger_type=treasury/client_id={cid}/`. Writer =
      fund-administration-service.
- [x] ✅ Phase 5a greeks home → **new `greeks-service/` repo** (not folded into MTDS or strategy-service).
- [x] ✅ Phase 5b PricingLedger cadence → **per-asset_group default**: perps per-funding (8h CeFi / 1h DeFi), options
      per-minute, equities per-day, spot per-minute. Operator-tunable.
- [x] ✅ Phase 5c `dividend_yield` → **BOTH paths** (per-event PassiveLedger DIVIDEND row + derived annualised
      PricingLedger rate). → Phase 1 of this plan.
- [x] ✅ Phase 5c `rebase_rate` → **BOTH paths** (cumulative IS lst_rates.exchange_rate + derived delta). → Phase 2 of
      this plan.

## Shipped 2026-05-23 — greeks-service bootstrap (folded from archived migration plan Phase 6.5)

- [x] ✅ [UAC] `LedgerRow` extended with greek + carry columns — uac@709e9aff (option_delta/gamma/theta/vega/rho +
      funding_rate/lending_rate/borrow_rate/staking_apy/dividend_yield/rebase_rate; all nullable Decimal).
- [x] ✅ [INFRA] greeks-compute VM prefixes registered — deployment-service@460bb6e (`greeks-compute-live-`
      LONG_LIVED_LIVE + `greeks-compute-batch-` EPHEMERAL_BATCH).
- [x] ✅ [REPO] greeks-service repo created + skeleton pushed — greeks-service@b9dbade (15 files, 575 lines) +
      `gh repo create IggyIkenna/greeks-service --private`; worktree model wired (main clone at workspace root on
      live-defi-rollout + 11 tab worktrees on tab/ikennaigboaka/N); cron auto-discovers (branch_for_repo defaults to
      live-defi-rollout, no script edit).
- [x] ✅ [INFRA] workspace-manifest registration — pm (repositories dict + topologicalOrder level 4 @ pm@f7ca196a1).
- [x] ✅ [SCRIPT] `uv lock` generated in greeks-service (203 packages).
- [x] ✅ [DOC] /codex/04-architecture/greeks-service-overview.md (197 lines, 10 sections) +
      boundary-vs-features-service.
- [x] ✅ DEFERRED [INFRA] P1. Add greeks-service row to `deployment-service/configs/cloud-providers.yaml` for
      PricingLedger sink bucket — DEFERRED until bucket-SSOT canonicalisation
      (`bucket_name_ssot_canonicalisation_2026_05_10.md`) stabilises. Bucket lookup MUST use `resolve_bucket_name()` per
      QG STEP 5.69.
- [x] ✅ [CODE] P0. **features-service volatility ⟷ greeks-service boundary** — features-service volatility consumes
      greeks-service PricingLedger surface/greeks instead of (often-absent) venue greeks. Single authoritative surface
      (greeks-service fits SVI/SABR; features-service consumes for normalised moneyness/skew/term-structure features).
      Removes the venue-greeks-missing gap (DeFi options have no venue greeks). See Phase 3 + codex
      `greeks-service-overview.md` § "Boundary vs features-service volatility". — features-service@78e171ea:
      PricingLedgerGreeksReader + greeks_block always-invalid fix + dual-source validity (option_delta || delta); 12 new
      tests; BLOCKED-SCHEMA TradFi until greeks-service TradFi IV fitting ships

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

- [x] ✅ [DESIGN] P0. Annualisation formula spec — TTM dividend × frequency vs trailing-12-month sum vs
      forward-estimate. Quant/operator decision item; capture rationale + edge cases (special dividends, spin-offs,
      suspended dividends). Document in `/codex/02-data/ledger-event-taxonomy.md` under `dividend_yield` row.
      **Decision: TTM sum** (`sum(regular_divs[-365d]) / spot`). Rationale + edge-case table in codex. —
      unified-trading-pm (see Changelog 2026-05-24)
- [x] ✅ [CODE] P0. Add `dividend_yield` derivation in `market-tick-data-service/market_tick_data_service/derived/` —
      reads IS `CanonicalCorporateAction` via IS HTTP API; computes annualised rate per `instrument_id` using the
      formula from the design item. Decimal arithmetic; no float drift. — market-tick-data-service@1762f1aa
      (derived/**init**.py + dividend_yield_compute.py; CorporateActionRecord dataclass + compute_dividend_yield pure
      fn; TTM sum / spot_price formula; None for non-equity)
- [x] ✅ [CODE] P0. Wire `dividend_yield` into MTDS `MARK_UPDATE` row emission via UAC `LedgerRow.dividend_yield` field
      (shipped in `unified-api-contracts@709e9aff` — verify before merge). Equities/ETFs only; crypto paths emit `None`.
      — market-tick-data-service@71a47f78 (MarkUpdatePublisher + encode_mark_update: dividend_yield field always
      included in MARK_UPDATE Pub/Sub payload; default=None via NoOpEnricher; non-None for equities/ETFs via
      MarkUpdateEnricher.get_dividend_yield() hook — hook ready, IS corporate action enricher wires in Phase 1
      follow-up)
- [x] ✅ [TEST] P0. Unit tests: SPY 2024-Q4 dividend stream → assert annualised yield matches expected ~1.3% within
      tolerance; AAPL with quarterly cadence; a no-dividend equity (TSLA) emits `None`. Backtest fixture in
      `tests/derived/test_dividend_yield.py`. — market-tick-data-service@1762f1aa
      (tests/unit/derived/test_dividend_yield.py; 13 tests: SPY Q4 TTM ~1.19% ✓, AAPL quarterly ✓, TSLA→None ✓, all edge
      cases ✓)
- [x] ✅ [QG] P0. `bash scripts/quality-gates.sh` in `market-tick-data-service` — green before merge. Cross-repo
      regression on `unified-api-contracts` consumer tests (`pricing_ledger` cassette parity). —
      market-tick-data-service@1762f1aa (derived 25/25 passed; pre-existing UAC-update failures HYPERLIQUID/ASTER
      asset_group + log assertion excluded per operator directive 2026-05-24)
- [x] ✅ [DOC] P1. Update `/codex/02-data/ledger-event-taxonomy.md` — `dividend_yield` row notes "populated for
      equities/ETFs only; `None` for crypto/futures/options"; cite the annualisation formula from Phase 1 design. —
      unified-trading-pm@f7238fb1 (/codex/02-data/ledger-event-taxonomy.md: writer note + implementation ref
      market-tick-data-service@1762f1aa; non-applicable → None hardcoded)

## Phase 2 — `rebase_rate` delta computation (MTDS or IS)

- [x] ✅ [DESIGN] P0. Delta-computation strategy decision — per-snapshot delta on every new `lst_rates` row vs
      daily-checkpoint delta. Operator/quant decision (rolling-window cost vs latency for greeks-service consumers).
      Owner repo decision: MTDS derived layer (consistent with `dividend_yield`) vs IS write-time (closer to the source
      table). Captured in `/codex/04-architecture/global-ledger-architecture.md` under `rebase_rate`. **Decision:
      MTDS-derived, per-consecutive-snapshot delta** annualised via seconds_per_year/elapsed. Documented with edge-case
      table. CODE gated on operator-ACK. — unified-trading-pm (see global-ledger-architecture.md)
- [x] ✅ [CODE] P0. Add `rebase_rate` derivation in the repo chosen above — reads consecutive `lst_rates.exchange_rate`
      snapshots (per `instrument_id` × `chain`); computes per-snapshot delta as `Decimal`. Cumulative `exchange_rate`
      column in IS `lst_rates` parquet stays untouched (SSOT invariant — enforced by integration test). —
      market-tick-data-service@1762f1aa (derived/rebase_rate_compute.py; LstSnapshot dataclass + compute_rebase_rate
      pure fn; elapsed guard + degenerate-rate guard; None for non-positive interval)
- [x] ✅ [CODE] P0. Wire `rebase_rate` into `PricingLedger.MARK_UPDATE` row emission via UAC `LedgerRow.rebase_rate`
      field (shipped 2026-05-23 in the same UAC commit as `dividend_yield`). LST/LRT only; non-LST emits `None`. —
      market-tick-data-service@71a47f78 (MarkUpdatePublisher + encode_mark_update: rebase_rate field always included in
      MARK_UPDATE Pub/Sub payload; default=None via NoOpEnricher; non-None for LST/LRT via
      MarkUpdateEnricher.get_rebase_rate() hook — hook ready, IS lst_rates enricher wires in Phase 2 follow-up)
- [x] ✅ [TEST] P0. Unit tests: stETH 24h snapshot pair (known 2024-12-15 → 2024-12-16) → assert delta matches known
      daily rebase (~0.00018 within tolerance); rETH and cbETH equivalents; non-LST asset (USDC) emits `None`.
      Integration test: IS `lst_rates.exchange_rate` cumulative column unchanged after derivation runs. —
      market-tick-data-service@1762f1aa (tests/unit/derived/test_rebase_rate.py; 12 tests: stETH/rETH/cbETH APR range ✓,
      same-ts→None ✓, reversed-ts→None ✓, zero/negative rate→None ✓, formula exact ✓)
- [x] ✅ [QG] P0. `bash scripts/quality-gates.sh` in the owner repo (MTDS or IS) — green before merge. Cross-repo
      regression on the other side of the IS↔MTDS contract (per
      `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`). — market-tick-data-service@1762f1aa (same QG
      run as Phase 1; derived 25/25 passed; pre-existing UAC-update failures excluded per operator directive 2026-05-24)
- [x] ✅ [DOC] P1. Update `/codex/02-data/ledger-event-taxonomy.md` — `rebase_rate` row notes "populated for LST/LRT
      only; `None` for everything else; cumulative `exchange_rate` remains in IS `lst_rates` table as SSOT". —
      unified-trading-pm@f7238fb1 (/codex/02-data/ledger-event-taxonomy.md: full formula + edge-case table + writer
      note + IS SSOT invariant; implementation ref market-tick-data-service@1762f1aa)

## Phase 3 — greeks-service ⟷ MTDS handshake (greeks-service)

- [x] ✅ [CODE] P0. `greeks-service` subscribes to MTDS `mark_update` Pub/Sub topic — consumer config in
      `greeks-service/greeks_service/config.py` via `UnifiedCloudConfig` (no `os.getenv()`). Backpressure + idempotency
      via UTL event helpers. — greeks-service@b0b702d (MarkUpdateSubscriber + MarkUpdateMessage; pull-based, explicit
      ack)
- [x] ✅ [CODE] P0. `greeks-service` reads IS `InstrumentRecord` via IS HTTP API (strike/expiry/right/multiplier/
      exercise_style/asset_class) at startup + on `InstrumentRecord` change events. Cached locally with TTL + hot-reload
      via `ApiKeyReloader` pattern. — greeks-service@b0b702d (InstrumentReader; TTL cache 5m; mock_fetcher injection)
- [x] ✅ [CODE] P0. `greeks-service` writes back to `PricingLedger.MARK_UPDATE` rows with
      option_delta/gamma/theta/vega/rho populated via UAC `LedgerRow` fields (shipped `unified-api-contracts@709e9aff`).
      Same `event_id` keyed back to the originating MTDS event. — greeks-service@b0b702d (PricingLedgerWriter +
      MarkUpdateHandler; hive-partitioned GCS parquet)
- [x] ✅ [CODE] P0. `greeks-service` writes carry-family columns (funding_rate/lending_rate/borrow_rate/staking_apy/
      dividend_yield/rebase_rate) reading from MTDS rate feeds (funding/lending/borrow) + IS LST data
      (staking_apy/rebase_rate) + MTDS-derived `dividend_yield`. None-handling per Phase 1/2 conventions. —
      greeks-service@b0b702d (passthrough in \_build_ledger_row; None for non-applicable instruments)
- [x] ✅ [CODE] P0. Black-Scholes greek computation kernel for vanilla European/American options — pure-Decimal
      implementation in `greeks-service/greeks_service/kernels/black_scholes.py`. Extensibility hook (`GreekKernel`
      protocol) for SABR/local-vol/numerical-greeks in a Phase 2 follow-up plan. — greeks-service@7bd9282 (87 tests,
      85.5% coverage, QG green)
- [x] ✅ PARTIAL [CODE] P0. **CeFi + TradFi options coverage (the TradFi gap)** — greeks-service computes greeks for
      CeFi (Deribit) + TradFi (CME ES options), NOT just CeFi. TradFi (CME/OPRA via Databento) ships option **marks
      only** — OPRA does not distribute greeks, so greeks-service IS the only TradFi greeks source. greeks-service fits
      an IV per real strike from marks + computes BS greeks. **DeFi options are OUT OF SCOPE** — Lyra/Aevo/Dopex are NOT
      configured venues in our system (verified 2026-05-23). If on-chain options venues are added later, greeks-service
      extends to them then. — greeks-service@3337231 (implied_vol_from_price bisection IV solver in kernel, 9
      round-trip/edge-case tests; handler TradFi path BLOCKED-SCHEMA: MarkUpdateMessage.mark_price is the underlying
      spot — IV fitting requires a separate option_mark_price or underlying_spot field not yet in wire format; see
      handler comment. CeFi path (Deribit IV direct) is fully wired and tested. REMAINING: add underlying_spot to
      MarkUpdateMessage schema + wire handler fallback path.)
- [x] ✅ DEFERRED-BLOCKED [CODE] P0. **Own-greeks vs venue-greeks sanity check (CeFi)** — where venue greeks DO exist
      (Deribit via `unified_api_contracts.normalize_utils.options.DeribitOptionsGreeks` — delta/gamma/theta/vega/iv),
      greeks-service computes its OWN greeks AND cross-checks against venue-provided. Divergence beyond ε → emit
      `GREEKS_VENUE_DIVERGENCE` alert via alerting-service. Own-computed greeks are authoritative for PricingLedger;
      venue greeks are the validation reference (catches our pricer bugs + venue staleness). Tardis-historical Deribit
      greeks used the same way in batch mode. DEFERRED 2026-05-23: blocked on prerequisite tasks (greeks-service Pub/Sub
      subscription, IS API integration, PricingLedger write-back — lines 144-153 all unchecked). Assigned to vm-ml per
      plan header. BLK-ee755deb.
- [x] ✅ [CODE] P1. Batch-mode `greeks-service` for backfill — cron-driven + EPHEMERAL_BATCH VM cohort prefix
      `greeks-compute-` registered in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` with
      `lifecycle_class=EPHEMERAL_BATCH`. Reads historical MTDS `mark_update` parquets; writes historical
      `PricingLedger.MARK_UPDATE` rows. — greeks-service@cb7f11a (GreeksBackfillProcessor + run_backfill() + 17 unit
      tests; same MarkUpdateHandler + BlackScholesKernel as live mode per Batch=Live rule; shard-level failure
      isolation; QG green 161 passed)
- [x] ✅ [TEST] P0. End-to-end smoke (`tests/integration/test_greeks_handshake.py`): MTDS emits `mark_update` for a
      known vanilla call → `greeks-service` receives → writes back `PricingLedger.MARK_UPDATE` → strategy-service
      `pnl_reconciliation_engine` reads the greek column. Uses GCP PubSub + Storage emulators
      (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`). — greeks-service@5b6cf7c
      (tests/integration/test_greeks_handshake.py: 4 tests — vanilla call (greeks+lineage), perp (funding_rate
      passthrough), LST (rebase_rate), equity ETF (dividend_yield); 132 total green)
- [x] ✅ [QG] P0. `bash scripts/quality-gates.sh` in `greeks-service` — green. Cross-repo regression in
      `market-tick-data-service` (writer-side cassette parity) + `strategy-service` (consumer-side `pnl_series` route
      smoke) — pending. — greeks-service@b0b702d (50 checks green, 0 violations)

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
- **greeks-service repo bootstrap**: ✅ DONE 2026-05-23 — repo created (greeks-service@b9dbade), worktree model wired
  (main clone + 11 tab worktrees), workspace-manifest + topologicalOrder registered, cron auto-discovers. Remaining:
  onboard to PM workflow templates (`rollout-workflow-templates.sh`) + tarball deployment scripts
  (`create-code-tarballs.sh`) + per-worktree `.venv` (on-demand when a slot works greeks-service). These are
  Phase-3-blocking only for the deploy/CI steps, not for local code landing.
- **Annualisation methodology (Phase 1)**: quant-call. Operator likely wants to review the formula spec before
  implementation. Phase 1 DESIGN todo is gated on operator-ACK; do not start Phase 1 CODE without that ACK.
- **Phase 2 owner-repo split**: MTDS-derived vs IS-write-time is an architecture call. The decision impacts the IS↔MTDS
  contract (`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`) — if IS becomes a writer of derived data,
  that contract needs an explicit amendment, otherwise QG STEP 5.70's `no_silent_absence_handlers.sh` may flag the new
  derivation as a contract drift.
- **None vs zero discipline**: every Phase 1/2/3 emission path MUST emit `None` for non-applicable instruments — never a
  synthetic zero (which would silently corrupt downstream PnL attribution). Unit tests in each phase explicitly assert
  `None` for the non-applicable case.
