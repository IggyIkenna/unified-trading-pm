---
title: Global Ledger + PnL Attribution — discovery, target-state spec, delta-to-current-system
parent_epic: global_ledger_pnl_attribution_master
assigned_vm: vm-trading-core
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-05-21
predecessor: plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md (Group F/G MVP; archived 2026-05-16)
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/global_ledger_pnl_attribution_master.md
  - plans/epics/execution_master.md
  - plans/epics/strategy_master.md
  - plans/epics/mtds_mdps_master.md
  - plans/epics/instruments_master.md
  - plans/epics/observability_master.md
---

# Global Ledger + PnL Attribution — Discovery Plan

> **Scope**: discover the delta between today's strategy-service position/pnl/risk engines + the archived attribution
> MVP and a target-state **4-SSOT-ledger + 4-derived-ledger** architecture. Produce UAC schemas, ownership decisions,
> writer/reader gap analyses, and a sequenced migration sub-plan stub. **No code lands in this plan** — implementation
> sub-plans spawn from the discovery findings and inherit `parent_epic: global_ledger_pnl_attribution_master`.

## Readiness gates (per PLAN_FORMAT.md)

- **Code**: C0 — design plan, no implementation in this plan.
- **Deployment**: N/A — design plan.
- **Business**: B1 — acceptance criteria defined below.

**B1 acceptance criteria**:

- (1) UAC schema spec for `InstructionLedger`, `PassiveLedger`, `TreasuryLedger`, `PricingLedger` rows lands in
  `unified_api_contracts.canonical.crosscutting.ledger/` as pydantic models with documented enums.
- (2) Current-state audit report enumerates every position/pnl/risk/pricing/treasury emit + consume site across the 5
  affected services (execution-service, strategy-service, MTDS, instruments-service, client-reporting-api).
- (3) Late-arriving-data discipline decided (event-sourced append-only vs designated-mutable columns), with rationale
  anchored in audit/replay requirements.
- (4) TreasuryLedger split decision (own table vs cohort of InstructionLedger) recorded with consumer-overlap evidence.
- (5) Derived-ledger writer-owner confirmed as `strategy-service` (per operator 2026-05-21).
- (6) Migration sub-plan stub published at `plans/active/global_ledger_pnl_attribution_migration_2026_06_XX.md` with
  sequenced phases + risk callouts.
- (7) VM-prefix additions enumerated in `VM_PREFIX_TO_BUCKET` PR (or absorbed-into-existing decisions recorded).

## Background

The operator's design intent (captured 2026-05-21):

> "Every event affecting our instruments ultimately. Separately for PnL we will need every event affecting our
> positions. Funding rate, settlement, staking and lending and deposit rewards all happen WITHOUT trade or swap or
> transfer like events — they are not instruction-driven, they are passive. Expiry would arguably go here actually since
> it's automated, apart from American options where we can trigger it. Long as we know expiry time we can derive it.
> Money coming in and out also an active event. Pricing events technically events too but they need their own ledger as
> that's all instrument-/client-/strategy-agnostic and that's just the lowest-granularity updates on price and greeks
> for everything since PnL needs current prices/theos of course and attribution needs greeks where borrow and lending
> rates and dividends and perp funding rates are all greeks in this regard. Allows PnL to join fill events with pricing
> events. All global with optionals and the right part of the system handling. Joins simple for who needs them. Columns
> updated as they can be pre or post trade by different things."

Current state of the workspace's PnL/position/risk stack (`strategy-service`, audited 2026-05-21):

- `strategy_service/position/` — sports_position_tracker, defi_lp_aggregator, greeks_aggregator, mark_price_subscriber,
  transfer_reconciler, **pnl_reconciliation_engine**, cross_venue_aggregator, isolation_policy, `v2/` rework underway,
  position/api/routes/pnl_series.py.
- `strategy_service/pnl/` — engine/breakdown.py, archetype_aggregator, sports_pnl, reward_attribution,
  execution_alpha/calculator, analytics/performance, api/main.py.
- `strategy_service/risk/` — risk_calculator, risk_monitor, **exposure_aggregator**, var_attribution,
  leverage_breach_detector, correlation_matrix, alert_manager, defi_reconciliation.
- `strategy_service/portfolio_allocator/` — service, guard_rails, emitter, share_class_fx, archetypes, cadence.

The archived `client_reporting_pnl_attribution_mvp_2026_05_10.md` (Group F/G of the May-23 cutover) shipped per-client
NAV/PnL/metrics. This plan generalises that MVP into the SSOT ledger model and uncovers what additional canonicalisation
is required so DART, alerting-service, and client-reporting-api join one of four canonical surfaces (Instruction /
Passive / Treasury / Pricing) rather than service-internal state.

## Target architecture (under discovery)

Four SSOT ledgers + four derived ledgers + one view. **The discovery plan does not lock the schema** — Phase 2 produces
the spec, Phase 3+ reviews it against current-state evidence, and the migration sub-plan implements the agreed model.

**Provisional schema** (`unified_api_contracts.canonical.crosscutting.ledger/`):

```
LedgerRow:                              # universal SSOT row shape (~32 columns)
  # Identity & discriminators
  event_id: str                         # tx_hash on-chain | exec_id off-chain | settlement_id for venue settles
  row_id: str                           # event_id.{n} — unique per row in multi-asset events
  event_origin: EventOrigin             # instruction | passive
  event_type: EventType                 # trade | transfer | stake | ... | funding | settlement | ...
  trade_id: str | None                  # logical strategy/structure group
  leg_id: str | None                    # within trade_id
  parent_event_id: str | None           # settlement/funding/dividend → originating trade
  timestamp_utc: datetime
  # Where
  asset_group: AssetGroup               # cefi | defi | tradfi | sports | prediction
  venue: str
  chain: str | None
  chain_tx_hash: str | None
  chain_block_number: int | None
  gas_paid_native: Decimal | None
  gas_currency: str | None
  # Account / counterparty (HARD RULE: client_id matches on both sides of transfers)
  account_id: str
  client_id: str
  counterparty_account: str | None
  counterparty_client_id: str | None    # MUST == client_id (CrossClientTransferForbiddenError)
  # Asset moved (one row = one asset delta)
  asset_symbol: str                     # human: USDC, aUSDC, stETH, NGZ26P3.50
  asset_canonical_id: str               # chain addr | OCC | CUSIP | ISIN | event slug
  asset_class: AssetClass               # spot_token | atoken | debt_token | lst | lrt | option | future | perp | ...
  delta: Decimal                        # signed: + received, - sent
  price: Decimal | None                 # quote_currency per unit
  quote_currency: str | None
  fees_in_quote: Decimal | None
  # Instrument detail (nullable per asset_class)
  underlying: str | None
  expiry_date: date | None
  option_right: OptionRight | None      # P | C
  strike: Decimal | None
  contract_multiplier: int | None
  selection: str | None                 # sports/prediction outcome label
  direction: Direction | None           # buy | sell | back | lay | yes | no | long | short | supply | ...
  # Combos
  combo_id: str | None
  combo_price: Decimal | None
  # Passive-only
  accrual_period_start_utc: datetime | None
  accrual_period_end_utc: datetime | None
```

`InstructionLedger`, `PassiveLedger`, `TreasuryLedger` are variants of this shape filtered by `event_origin` /
`event_type` cohort. `PricingLedger` has its own narrower schema (instrument, timestamp, mid, bid, ask, IV, delta,
gamma, theta, vega, rho, carry-family rates: funding_rate, lending_apr, borrow_apr, dividend_yield, staking_apr,
rebase_rate) — discovery Phase 5 finalises.

**Universal PnL recipe** (derived ledger compute):

```
holdings(t, asset) = Σ delta where row.asset = asset and row.timestamp ≤ t  →  PositionLedger
cash_out(row) = -row.delta × row.price                                       →  realised cash flow per row
realised_pnl = Σ cash_out − Σ fees_in_quote − Σ gas_cost(FX-converted)       →  PnLLedger realised
unrealised_pnl = Σ holdings(t) × mark(t)                                     →  PnLLedger unrealised
attribution = decompose Δ(unrealised) into delta/gamma/theta/vega/carry/...  →  PnLAttributionLedger
```

## Phases

### Phase 0 — Cross-link + inventory (P0)

- [x] ✅ [DOC] P0. Cross-link this plan from `master_to_live_defi_2026_05_23.md` § "Post-cutover backlog" (or
      operator-confirmed section). Added to "Post-cutover consolidated successor plans" section. —
      unified-trading-pm@slot-7 2026-05-23.
- [x] ✅ [DOC] P0. Cross-link from `execution_master.md`, `strategy_master.md`, `mtds_mdps_master.md`,
      `instruments_master.md`, `observability_master.md`, `dart_and_promote_master.md` in `related_plans:`. Added to
      `mtds_mdps_master`, `instruments_master`, `dart_and_promote_master` (other 3 already had it). —
      unified-trading-pm@slot-7 2026-05-23.
- [x] ✅ [SCRIPT] P0. Run `python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py` — confirm this
      plan shows up in master inventory. Ran: 34 plans, 0 orphans, 60% done overall. Plan appears in inventory table. —
      unified-trading-pm@slot-7 2026-05-23.

### Phase 1 — Current-state audit (P0, parallel-safe across services)

For each of the 5 affected services, produce an audit doc at
`plans/audit/results/global_ledger_audit_<service>_2026_05_XX.md` covering: what it emits today (event-like), what it
consumes, what state it reconstructs internally, what canonical schemas it already imports from UAC, and the gap to the
target SSOT ledger model.

- [x] ✅ [AUDIT] P0. **execution-service** — InstructionLedger writer. Map current fill/transfer/stake emission paths;
      identify which today flow through service-output emission semantics (per
      `codex/02-data/service-output-emission-semantics.md`). Flag any path that emits via custom topic without going
      through `_resolve_policy_output_data_type`. —
      `plans/audit/results/global_ledger_audit_execution_service_2026_05_23.md` (4 P0 gaps: no
      `_resolve_policy_output_data_type`, manifest failures silently swallowed, client_id absent from log_event
      payloads, `build_attribution_rows()` dead-end). unified-trading-pm@2026-05-23.
- [x] ✅ [AUDIT] P0. **strategy-service** — derived-ledger writer (confirmed owner). Inventory
      `strategy_service/position/`, `strategy_service/pnl/`, `strategy_service/risk/`,
      `strategy_service/portfolio_allocator/` modules; for each, document data sources (live event streams vs
      reconstructed state vs reconciled snapshots vs direct venue queries). The `v2/` rework directories are the
      refactor target. — `plans/audit/results/global_ledger_audit_strategy_service_2026_05_23.md` (unrealized_pnl always
      0 — MarkPrice not bridged; fees not deducted; PnL reconciliation not wired; PnL time-series API always 404).
      unified-trading-pm@2026-05-23.
- [x] ✅ [AUDIT] P0. **market-tick-data-service** — PricingLedger price/IV writer. Document what's already canonical
      (mid/bid/ask/IV per `mtds_mdps_master.md`) and what's missing (greeks computation home, snapshot vs streaming). —
      `plans/audit/results/global_ledger_audit_mtds_2026_05_23.md` (dividend_rate MISSING; rho MISSING from entire
      stack; mid not stored — must derive (bid+ask)/2; 8+ DeFi handlers annotated
      `# QG-allow: emission-policy-not-applicable`). unified-trading-pm@2026-05-23.
- [x] ✅ [AUDIT] P0. **instruments-service** — instrument metadata + carry-family rates (funding intervals, dividend
      dates, expiry timestamps, settlement style). Confirm metadata sufficiency for PassiveLedger synthesiser. —
      `plans/audit/results/global_ledger_audit_instruments_service_2026_05_23.md` (IS NECESSARY but NOT SUFFICIENT; 7
      gaps: exercise_style/settlement_style/dividend_schedule absent, funding_interval not stored, rocket_pool.py
      missing source_archive_url_template, Sanctum not wired, native_staking_rates deferred).
      unified-trading-pm@2026-05-23.
- [x] ✅ [AUDIT] P0. **client-reporting-api** — what it computes today (per archived attribution MVP) vs what it joins
      from canonical ledgers in the target model. —
      `plans/audit/results/global_ledger_audit_client_reporting_api_2026_05_23.md` (10 HIGH severity gaps: no canonical
      ledger joins, realised_pnl hardcoded "0.00"). unified-trading-pm@2026-05-23.

### Phase 2 — UAC schema spec (P0)

- [x] ✅ [UAC] P0. Draft pydantic models for `LedgerRow` + `InstructionLedger` / `PassiveLedger` / `TreasuryLedger` /
      `PricingLedger` variants in `unified_api_contracts/canonical/crosscutting/ledger/`. — 32-field frozen Pydantic
      model; 4 type aliases; re-exported from canonical.crosscutting. unified-api-contracts@13155355.
- [x] ✅ [UAC] P0. Define `EventOrigin`, `EventType`, `AssetClass`, `Direction`, `OptionRight` enums as `StrEnum`
      (closed sets — extension via PR only). — `ledger/_enums.py`: 5 StrEnums, all closed (14 EventType values, 14
      AssetClass values, 12 Direction values). unified-api-contracts@13155355.
- [x] ✅ [UAC] P0. Cross-client transfer validator: every `transfer`/`bridge` row asserts
      `client_id == counterparty_client_id`; raise `CrossClientTransferForbiddenError` otherwise. Anchor to
      `codex/04-architecture/client-funds-isolation.md`. — `assert_no_cross_client_transfer()` + `@model_validator` on
      LedgerRow enforces HARD RULE at construction time. unified-api-contracts@13155355.
- [x] ✅ [UAC] P1. Document the `parent_event_id` linkage convention for settlements / funding / dividends /
      enrichments. — Codified in `LedgerRow` class docstring: 5 linkage patterns (settlement→trade, funding→perp fill,
      dividend→buy fill, staking/lending→stake/borrow, enrichment→original). unified-api-contracts@008e59ce.
- [x] ✅ [UAC] P1. Document the `accrual_period_start_utc` / `accrual_period_end_utc` convention for passive events. —
      Codified in `LedgerRow` class docstring: per-event-type intervals (FUNDING_ACCRUAL 8h CeFi/block DeFi; DIVIDEND
      ex-div→payment; STAKING_REWARD LST oracle/epoch; LENDING_INTEREST liquidity-index blocks). Field descriptions
      updated. unified-api-contracts@008e59ce.

### Phase 3 — Late-arriving-data discipline (P0, **BLOCKED-OPERATOR-DECISION** if no clear winner emerges)

Two candidate models for enrichments that arrive after the initial event row (clearing_house_id, final_fee, FX_locked,
regulatory_report_id):

- **Option A: Event-sourced append-only** — enrichments arrive as separate rows with `parent_event_id` + a typed
  `event_type = enrichment.<kind>`. Derived views collapse. Pros: immutability, full audit, replay-equivalent. Cons:
  query complexity (join-to-latest).
- **Option B: Designated-mutable columns** — initial row + named-set of columns mutable post-write with an audit log.
  Pros: query simplicity. Cons: requires audit-log machinery, breaks pure event-sourcing.

- [x] ✅ [DESIGN] P0. Survey downstream join patterns (DART, client-reporting-api, alerting-service) — 2026-05-23:

      **client-reporting-api**:
      - `/api/pnl/` monthly history scan → bulk GCS read, fully append-only compatible (Option A OK)
      - `/api/v1/performance/summary` + `/positions` → calls `collector.get_client_snapshot(client_id)` — requires
        current mutable state (or backend pre-join before serving)
      - Trade history / bills ledger → sum-over-event-log; append-only fully compatible (Option A OK)

      **alerting-service**: Fully event-driven — consumes `DEVIATION_CONFIRMED`/`BALANCE_DISCREPANCY_DETECTED`/
      `UNEXPLAINED_PNL_RESIDUAL` payloads. Never reads a row directly. Completely agnostic to Option A vs B.

      **DART**: UI client only. `fetchInstructionStatus` polls for current fill state (`unrealized_pnl`, `filled_qty`).
      `RunRecord` per-run `realized_pnl`/`unrealized_pnl` is a point-in-time snapshot. Mock position ledger is
      append-and-mutate — models mutable position per `(instrument, venue, strategy)`. DART would need backend to
      pre-join before serving if Option A is chosen.

      | Consumer | Needs latest state? | Option A tolerable? |
      |---|---|---|
      | CRA /api/pnl/ history scan | No | ✅ fully compatible |
      | CRA /positions + /performance | Yes — current snapshot | Only if backend pre-joins |
      | CRA trade history | No | ✅ fully compatible |
      | alerting-service | No — event-driven | ✅ fully agnostic |
      | DART instruction status | Yes — current fill state | Only if backend pre-joins |

- [x] ✅ [DESIGN] P0. Decision recorded with rationale — **RECOMMENDATION: Option A (append-only) with a pre-join view
      layer at the API boundary**. Rationale: (a) alerting-service is fully agnostic; (b) history/PnL paths are
      append-only compatible; (c) the two hard blockers (`GET /positions`, DART status) do NOT require mutable rows at
      the storage layer — they only require a pre-joined "latest state" view that the API constructs on read. This is a
      thin `JOIN LATERAL ... ORDER BY timestamp_utc DESC LIMIT 1` (or equivalent GCS last-row aggregation) in the API
      layer, NOT a schema mutation. Option B (designated-mutable columns) adds audit-log machinery and breaks
      event-sourcing purity for marginal query simplicity gains. **BLOCKED-OPERATOR-DECISION**: final confirmation from
      operator required before Phase 7 migration implements the late-arriving-data model. Survey evidence supports
      Option A.

### Phase 4 — Writer-side gap analysis (P0)

- [x] ✅ [DESIGN] P0. **execution-service**: enumerate what InstructionLedger fields the current emission paths populate
      vs what's missing. Flag fields where execution-service has no source (e.g. `combo_price` for atomic spread fills —
      needs broker exec-report parsing). — **Gap analysis from audit (2026-05-23)**:

      **Currently populated** (from `CanonicalFill` → `attribution_builder.py`):
      - `event_id` (exec_id), `timestamp_utc`, `asset_symbol`, `asset_canonical_id`, `delta`, `price`,
        `quote_currency`, `venue`, `account_id`, `direction`, `underlying`, `expiry_date`, `option_right`, `strike`

      **Missing / not yet populated**:
      - `client_id` — not in `log_event` payloads (HIGH — blocks per-client join)
      - `row_id` — multi-asset events not split into per-row suffixes
      - `event_origin` / `event_type` — not explicitly set (defaults needed)
      - `asset_group` — not in current fill schema
      - `asset_class` — mapped loosely; ATOKEN/DEBT_TOKEN/LST/LRT/VAULT_SHARE not discriminated
      - `fees_in_quote` — fee extraction from exec report partial; gas not converted
      - `gas_paid_native` / `gas_currency` / `chain` / `chain_tx_hash` / `chain_block_number` —
        on-chain fills not populating any chain metadata
      - `combo_id` / `combo_price` — atomic spread fills require broker exec-report parsing (no source yet)
      - `trade_id` / `leg_id` — strategy grouping not threaded through to execution
      - `contract_multiplier` — not extracted from instrument metadata
      - `selection` — sports/prediction fills not wiring outcome label

      **Emission path gap**: `build_attribution_rows()` returns empty list. Emission does not go through
      `_resolve_policy_output_data_type` / `_publish_emission_check`. Fix target: execution-service v2 writer refactor
      (Phase 7 migration sub-plan). unified-trading-pm@2026-05-23.

- [x] ✅ [DESIGN] P0. **PassiveLedger synthesiser**: enumerate every passive event type's synthesis rule (cf. table in
      the conversation: funding interval, rebase interval, interest accrual index, epoch schedule, expiry timestamp,
      resolution source). Map each to an instrument-metadata source (instruments-service or MTDS). — **Synthesis
      rules**:

      | EventType          | Synthesis rule                                              | Rate source              | Position source                | Cadence              |
      | ------------------ | ----------------------------------------------------------- | ------------------------ | ------------------------------ | -------------------- |
      | FUNDING_ACCRUAL    | delta = position.qty × funding_rate × sign(direction)      | MTDS `funding_rate`      | InstructionLedger TRADE rows   | 8h CeFi; block DeFi  |
      | STAKING_REWARD     | delta = atoken_balance × (index_now/index_prev - 1)        | MTDS `lst_rates`         | InstructionLedger STAKE rows   | Oracle report / epoch|
      | LENDING_INTEREST   | delta = balance × (liquidity_index_now/prev - 1)           | MTDS `lending_indices`   | InstructionLedger BORROW rows  | Block-level          |
      | DIVIDEND           | delta = share_qty × dividend_per_share                     | IS `CanonicalCorporateAction` | InstructionLedger TRADE rows | Ex-dividend date     |
      | SETTLEMENT         | delta = settlement_price × contract_multiplier × qty × sign | IS `expiry_date` + MTDS mark | InstructionLedger TRADE rows | Expiry date          |
      | EXPIRY (OTM)       | delta = 0 (position zeroed)                                | IS `expiry_date`         | InstructionLedger TRADE rows   | Expiry date          |

      **Critical gap from IS audit**: `funding_interval` not stored in IS; must be inferred from venue convention.
      `exercise_style` absent — cannot distinguish American vs European for early exercise logic.
      unified-trading-pm@2026-05-23.

- [x] ✅ [DESIGN] P0. **PassiveLedger listener gap**: which passive events MUST come from a live listener (on-chain
      emission) vs can be synthesised from schedule. Drift-detection: listener-observed minus synthesiser-expected =
      data-quality alert. — **Listener vs synthesiser classification**:

      **MUST listen (live on-chain emission, cannot reliably synthesise)**:
      - `STAKING_REWARD` (stETH rebase): oracle report timing is irregular; missed rebase = permanent error
      - `STAKING_REWARD` (validator): Ethereum `Withdrawal` events must be caught at block; no predictable schedule
      - `LIQUIDATION`: forced by protocol at any block; no schedule
      - `DIVIDEND` (surprise/special): special dividends not in any schedule

      **CAN synthesise (predictable schedule + rate data)**:
      - `FUNDING_ACCRUAL` (CeFi): fixed 8h cadence; synthesiser queries MTDS at 00:00/08:00/16:00 UTC
      - `FUNDING_ACCRUAL` (DeFi): block-level; synthesiser queries MTDS `funding_rate` at block
      - `LENDING_INTEREST`: every block via `lending_indices`; synthesiser queries MTDS
      - `SETTLEMENT` / `EXPIRY`: known from IS `expiry_date`; synthesiser reads IS at expiry time
      - `DIVIDEND` (scheduled): cash/stock dividend on record date from IS `CanonicalCorporateAction`

      **Drift detection**: synthesiser-expected row vs listener-observed row within ε tolerance per period.
      Divergence > threshold → `PASSIVE_LEDGER_DIVERGENCE` alert. unified-trading-pm@2026-05-23.

- [x] ✅ [DESIGN] P0. American option exception: `exercise_style` field on the instrument; early-exercise = instruction
      event, expiry-without-action = passive event. Both code paths defined. — **Design**:

      **Gap**: `exercise_style` (AMERICAN / EUROPEAN) absent from `InstrumentRecord` (IS audit Gap 1 — 2026-05-23).
      Must be added to IS before this code path can be discriminated.

      **Code paths once IS gap is fixed**:
      - `exercise_style=AMERICAN`: when holder exercises early → execution-service emits
        `EventType.TRADE` (EXERCISE direction) on InstructionLedger. Counterparty (writer) gets
        `EventType.TRADE` (ASSIGN direction) simultaneously.
      - `exercise_style=EUROPEAN` or AMERICAN at expiry without exercise: synthesiser emits
        `EventType.SETTLEMENT` (cash settled) or `EventType.EXPIRY` (OTM = zero value) on PassiveLedger.
      - **Blocker**: IS Gap 1 (`exercise_style` field) must land before Phase 7 migration sub-plan can
        implement this split. Plan item: IS instruments_master Phase B.2 (deferred from current IS audit).
      unified-trading-pm@2026-05-23.

### Phase 5 — Pricing + greeks gap analysis (P1)

- [x] ✅ [DESIGN] P1. PricingLedger row spec: mid/bid/ask/IV + greeks (delta/gamma/theta/vega/rho) + carry-family rates
      — **carry-family sourcing audit 2026-05-23**:

      | carry_rate_type | MTDS data_type | key fields | gaps |
      |---|---|---|---|
      | `funding_rate` | `perp_funding` | `funding_rate`, `premium`, `mark_price`, `index_price` | GMX Messari fallback is OI-proxy (synthetic) |
      | `lending_apr` | `lending_indices` | `liquidity_rate` (Aave), `supply_rate` (Compound/Messari) | field name varies by schema cascade |
      | `borrow_apr` | `lending_indices` | `variable_borrow_rate` (Aave), `borrow_rate` (Compound/Messari) | same variance |
      | `staking_apr` (APY) | `staking_yields` | `apy` | EigenLayer `apy=0.0` stub |
      | `staking_exchange_rate` | `lst_rates` | `exchange_rate` | `apy` always 0.0; ezETH absent (2-contract multicall gap) |
      | `native_staking_apy` | `native_staking_rates` | `base_apy`, `mev_apy`, `total_apy` | per-validator rows BLOCKED-CREDENTIALS (Helius) |
      | `rebase_rate` | — | — | **ABSENT** — no owner; exchange_rate encodes cumulative rebase |
      | `dividend_yield` | — | — | **ABSENT** as rate; IS/IBKR emits per-event `CanonicalCorporateAction` only |

      **Proposed PricingLedger carry fields** (mapping to LedgerRow from MTDS sources):
      - `funding_rate: Decimal | None` — from MTDS `perp_funding.funding_rate`
      - `lending_rate: Decimal | None` — from MTDS `lending_indices.liquidity_rate` (supply side)
      - `borrow_rate: Decimal | None` — from MTDS `lending_indices.variable_borrow_rate` (borrow side)
      - `staking_apy: Decimal | None` — from MTDS `staking_yields.apy` or `lst_rates.exchange_rate`-derived
      - `dividend_yield: Decimal | None` — **ABSENT** pending operator decision on whether to compute from IS corporate actions
      - `rebase_rate: Decimal | None` — **ABSENT** pending operator decision

- [x] ✅ [DESIGN] P1. Greeks computation home: **BLOCKED-OPERATOR-DECISION** — IS is the reference-data owner
      (InstrumentRecord, option strike/expiry); MTDS is the market-data owner (mark price, IV, book snapshots). Neither
      currently computes greeks. Candidates: (a) MTDS writer adds greek computation layer post mark-price fetch; (b)
      strategy-service computes from MTDS mark + IS instrument ref; (c) new greeks-service. Survey 2026-05-23: no greek
      computation exists in any service. Operator must decide ownership before Phase 7 PricingLedger writer is built.

- [x] ✅ [DESIGN] P1. Carry-family rate sourcing — see PricingLedger row spec item above for full table. **Gap
      actions**: (1) `rebase_rate` needs operator decision on whether to compute from IS LST `exchange_rate` deltas; (2)
      `dividend_yield` needs operator decision; (3) EigenLayer APY needs real data source; (4) ezETH multicall gap
      tracked in instruments_master.

- [x] ✅ [DESIGN] P1. Snapshot vs streaming cadence — **BLOCKED-OPERATOR-DECISION**: per-tick is highest fidelity but
      high GCS write volume (esp. for options chains). Per-minute is a reasonable default. Operator-tunable per
      asset_group is the recommended pattern (e.g. perps = per-funding-period, options = per-minute, equities =
      per-day). No implementation decision possible without operator input on acceptable PricingLedger cardinality.

### Phase 6 — Treasury cohort vs separate table (P1)

- [x] ✅ [DESIGN] P1. Consumer-overlap survey — **2026-05-23 audit findings**:

      **fund-administration-service**: Explicitly models `treasury_wallet_id` as first-class config; has
      `capital_router.py` for "treasury → strategy wallets" routing; `subscription/state_machine.py` terminates at
      "funds landed in treasury"; redemptions via `execute_withdrawal`. No BigQuery reads — purely event-driven.
      **Verdict**: strongly needs treasury concept separated; it IS the treasury writer.

      **client-reporting-api**: `transfer_store.py` is declared SSOT for all transfers (deposits/withdrawals) and is
      read separately from `trades.json`. `pnl_chart_generator.py` computes `trading_pnl = equity - initial_equity -
      cumulative_transfers` — `net_deposits` is explicitly subtracted to isolate trading PnL from capital flows.
      `reporting/nav.py` has dedicated `_capital_flows_for_clients()`. `fund_operations.py` builds ledger-style rows
      with "Net Deposits" and "Trading PnL" as distinct line items. Tax/compliance routes read trades only.
      **Verdict**: treasury rows MUST stay separate — current architecture has structural separation.

      **Regulatory**: MiFID II compliance route is trade-only. FIFO tax route is trade-only. No regulatory
      path consumes treasury rows mixed with trade rows.

- [x] ✅ [DESIGN] P1. Cardinality vs SLA trade-off: TreasuryLedger is low-cardinality (deposits/withdrawals are rare
      events, order of magnitude lower frequency than trades). SLA is moderate — daily reconciliation is fine. A
      separate table/partition adds zero operational complexity and removes accidental JOINs between capital-flow rows
      and trade rows. No cardinality concern with separation.

- [x] ✅ [DESIGN] P1. **Decision: TreasuryLedger as a separate partition** — `ledger_type=treasury/client_id={cid}/` —
      **BLOCKED-OPERATOR-DECISION for final confirmation**. Evidence strongly supports separation: (a) both fund-admin
      and CRA treat capital flows as structurally distinct from trading rows today; (b) regulatory paths (tax, MiFID II)
      explicitly exclude treasury rows; (c) low cardinality makes a separate partition operationally cheap; (d)
      fund-administration-service is the natural TreasuryLedger writer (it already owns the treasury event lifecycle). A
      filter-view on a unified table would work but is architecturally foreign to both current consumers.

### Phase 7 — Backtest synthesiser parity (P1)

- [x] ✅ [DESIGN] P1. PassiveLedger synthesiser TWO-mode contract — 2026-05-23:

      **Live mode** (strategy-live-* VM):
      - Subscribes to on-chain event listener + MTDS rate feed.
      - On every funding period / block / epoch, SYNTHESISES the expected row from position × rate.
      - Waits up to `PASSIVE_LEDGER_DRIFT_WINDOW` for the observed event to appear.
      - If observed == synthesised within ε → emits to PassiveLedger; logs RECONCILED.
      - If no observed event → emits synthesised row; logs PASSIVE_LEDGER_DIVERGENCE alert.
      - If observed ≠ synthesised by > ε → emits both; logs PASSIVE_LEDGER_DIVERGENCE with delta.

      **Backtest/paper mode** (strategy-paper-* VM):
      - Reads InstructionLedger history (batch = live SSOT, no separate code path — `batch-live-architecture.md`).
      - Synthesises ALL passive rows from schedule alone (MTDS historical rates + IS instrument metadata).
      - No drift detection (no observed events in backtest).
      - Output row `event_id = synthetic_{period_key}_{instrument_id}` to prevent collisions with live rows.

      **Parity contract**: for any instrument I and time window [T0, T1],
      `Σ_backtest(passive_pnl[I, T0..T1]) == Σ_live(passive_pnl[I, T0..T1])` within tolerance δ.
      δ is per-event-type: FUNDING_ACCRUAL δ ≤ 1bp; LENDING_INTEREST δ ≤ 5bp (APY rounding); STAKING_REWARD
      δ ≤ 1bp (exchange_rate precision); DIVIDEND δ = 0 (exact per CanonicalCorporateAction).

- [x] ✅ [DESIGN] P1. InstructionLedger replay-for-backtest: no new design needed. Existing batch=live pattern
      (`codex/04-architecture/batch-live-architecture.md`) covers this — backtest reads InstructionLedger GCS history
      via the same `read_parquet` path that live mode reads from the write buffer. The synthesiser queries historical
      MTDS rates (same GCS bucket, same schema, time-parameterised).

### Phase 8 — VM assignment for net-new runtime artifacts (P1)

- [x] ✅ [INFRA] P1. **ledger-reconcile-** VM prefix decision — **ABSORB into `batch-live-recon-cron-`** cohort.
      Rationale: ledger reconciliation is structurally identical to existing batch-live reconciliation (periodic run,
      GCS reads, manifest writes). Adding a new prefix would split the watchdog entry without adding isolation value.
      `batch-live-recon-cron-*` is already `SCHEDULED_RECURRING` in `VM_PREFIX_TO_BUCKET`. Migration sub-plan Phase 7
      tests will run under this prefix.

- [x] ✅ [INFRA] P1. **passive-listener-** VM prefix decision — **ABSORB into `strategy-live-*`** cohort. Rationale: the
      PassiveLedger synthesiser's live mode (listens + reconciles) is a strategy-service subprocess that runs inside the
      `StrategySupervisor` on the same strategy-live VM. It shares the position state and MTDS rate feed that the
      supervisor already has access to. A dedicated daemon VM would duplicate the MTDS connection and position snapshot.
      Per-client subprocess isolation already provided by multiprocessing boundary in
      `per-client-isolation-architecture.md`. Exception: if volume of passive events demands dedicated GCS write
      throughput, a `passive-synth-` prefix may be warranted in a future review.

- [x] ✅ [INFRA] P1. Derived-ledger compute home confirmed: `strategy-paper-*` (backtest synthesis + paper
      PassiveLedger) + `strategy-live-*` (live PassiveLedger + InstructionLedger ingestion) +
      `client-reporting-cutover-*` (PnL join + realised_pnl computation). No new prefixes required for Phase 7-9 scope.

- [x] ✅ [INFRA] P1. Lifecycle compliance: all 3 confirmed cohorts already have `VmPrefixSpec` entries in
      `vm_zombie_watchdog.py`. The `batch-live-recon-cron-` prefix carries `SCHEDULED_RECURRING`; `strategy-paper-*`
      carries `EPHEMERAL_BATCH`; `strategy-live-*` carries `LONG_LIVED_LIVE`; `client-reporting-cutover-*` carries
      `EPHEMERAL_BATCH`. No new lifecycle entries needed for Phase 7-9.

### Phase 9 — Migration sub-plan stub (P1)

- [x] ✅ [DOC] P1. Create `plans/active/global_ledger_pnl_attribution_migration_2026_06_01.md` — pm@a636100a3; stub with
      Phases 7-9, 8 B1 acceptance criteria, pre-migration gates. Original spec:
      (`parent_epic: global_ledger_pnl_attribution_master`) with: (a) UAC schemas landing (Phase 2 deliverable
      upstream). (b) Writer-side refactors in execution-service. (c) Reader-side refactors in strategy-service `v2/`
      modules + client-reporting-api. (d) PassiveLedger synthesiser implementation (live + backtest modes). (e) Backfill
      of historical events into the canonical ledgers (single-walk discipline per
      `gcs_migration_bundle_pipeline_mode_2026_05_08.md`). (f) Cutover: derived views switch from service-internal state
      to canonical ledger reads.
- [x] ✅ [DOC] P1. Stub declares `estimate_class: refactor` (0.4× multiplier) — confirmed in migration plan frontmatter
      pm@a636100a3.

### Phase 10 — Codex SSOT update (P2)

- [x] ✅ [DOC] P2. Add `codex/04-architecture/global-ledger-architecture.md` with the 4-SSOT-+-4-derived model,
      universal PnL recipe, synthesis recipe table, ownership table. — Updated existing file: Phase 2 UAC DONE banner +
      UAC contract code block + 5-service gap table. unified-trading-pm@a7aed81d3.
- [x] ✅ [DOC] P2. Add `codex/02-data/ledger-event-taxonomy.md` with the `EventOrigin` / `EventType` / `AssetClass` /
      `Direction` enum SSOT. — Expanded from stub: full EventOrigin (2), EventType (15), AssetClass (14), Direction
      (12), OptionRight (2) tables with string values + routing summary + cross-client invariant.
      unified-trading-pm@a7aed81d3.
- [x] ✅ [DOC] P2. Update `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` with the
      "carry-as-theta-family" attribution framing. — Added Global Ledger Integration section: carry-as-theta table
      (FUNDING*ACCRUAL/STAKING_REWARD/LENDING_INTEREST/DIVIDEND → CARRY*\* factors), ledger→factor mapping code block,
      implementation status from audit. unified-trading-pm@8317120eb.
- [x] ✅ [DOC] P2. Update CLAUDE.md to add a 1-line pointer to the new ledger codex SSOT (or extend the existing
      manifest/honest-absence section if more natural). — Added 1-line global ledger SSOT pointer in UAC Citadel
      Architecture section. unified-trading-pm@8317120eb.

### Phase 11 — Post-audit reconciliation (P0; landed 2026-05-23)

> Discovered 2026-05-23 by post-flip backing-evidence audit (36/38 BACKED + 2/38 PARTIAL). Three drift items closed
> same-day; one operator gate surfaced. Captured here so the work is visible to the orchestrator + the
> `Post-Plan-Phase Codex Audit` HARD RULE.

- [x] ✅ [UAC] P0. **Phase 2 enum expansion** — `EventType` 15 → 37 (19 INSTRUCTION + 18 PASSIVE) and `AssetClass` 14 →
      17 (added STABLE / ETF / NFT). Backwards-compatible (no removals/renames). `MARK_UPDATE` + `EXPIRY` retained per
      codex SSOT routing (MARK_UPDATE = PricingLedger discriminator; EXPIRY = OTM position-zeroing distinct from
      SETTLEMENT = ITM cash flow). Ruff + basedpyright green on edited dir. — uac edit landed 2026-05-23 (Agent B work,
      pending commit).
- [x] ✅ [DOC] P0. **Codex taxonomy sync** — `codex/02-data/ledger-event-taxonomy.md` updated to reflect 37 EventTypes +
      17 AssetClasses; Routing Summary expanded with new TreasuryLedger event types (DEPOSIT, WITHDRAWAL_TO_BANK,
      CUSTODY_MOVE); Changelog footer added with 2026-05-23 expansion entry. Closes the codex-drift gap flagged by Agent
      B during Phase 11 enum expansion. — codex edit landed 2026-05-23 (Agent C work, pending commit).
- [x] ✅ [EPIC] P0. **Epic format compliance** — added missing `owner: ikenna` + `asset_group: cross-cutting`
      frontmatter fields; trimmed epic body to canonical pattern (Owns / Status / Codex SSOTs table / Cross-epic
      handshakes / Assigned active plans priority blocks / VM assignment notes / Continuous-verification table); removed
      architecture-summary content that duplicated the codex SSOT docs (epic is read-mostly per `plans/epics/README.md`
      § "How to use these epics"). — epic edit landed 2026-05-23 (pending commit).
- [x] ✅ [README] P0. **Epic registry update** — `plans/epics/README.md` table 19 → 20 epics; added row 13 for
      `global_ledger_pnl_attribution_master` (L2 / `vm-trading-core`); updated `vm-trading-core` row in VM topology
      table to include this epic; updated 2 header counts. — README edit landed 2026-05-23 (pending commit).
- [ ] [SCRIPT] P0. **Run `python3 scripts/orchestrator/regen_vm_registry.py --check`** — confirm the new epic + its
      assigned_vm pass the orchestrator VM registry validation. Expected exit 0.
- [ ] [SCRIPT] P0. **Run `python3 scripts/plans/regenerate_active_plan_inventory.py`** — confirm 0 orphans + the new
      epic + its 2 assigned plans are reflected in the master inventory.
- [ ] [QG] P0. `bash scripts/quality-gates.sh` in `unified-api-contracts/` — confirm enum expansion + LedgerRow are
      QG-green workspace-wide (Agent B reported targeted ruff + basedpyright green; full QG hung on test-cassette
      collection in agent environment).
- [ ] [OPERATOR] P0. **Operator [ack] on Phase 3 decision** — late-arriving-data discipline (recommended Option A:
      event-sourced append-only with pre-join view layer). **BLOCKED-OPERATOR-DECISION** — migration plan Phase 7 gated
      until [ack] received.
- [ ] [OPERATOR] P0. **Operator [ack] on Phase 5 decision** — PricingLedger greeks-computation-home (MTDS vs
      strategy-service vs new module) + snapshot-vs-streaming cadence. **BLOCKED-OPERATOR-DECISION** — migration plan
      Phase 8 + 9 gated until [ack] received.
- [ ] [OPERATOR] P0. **Operator [ack] on Phase 6 decision** — TreasuryLedger split (own table vs cohort of
      InstructionLedger; current draft = own table per consumer-overlap evidence). **BLOCKED-OPERATOR-DECISION** —
      migration plan Phase 7 partition routing gated until [ack] received.

## Full-execution criterion

This plan is **operationally complete** (per `Plans Run To Actual Completion` HARD RULE) when:

1. All 5 audit docs landed in `plans/audit/results/`.
2. UAC schemas merged on `unified-api-contracts` `live-defi-rollout`.
3. Decisions recorded for late-arriving-data, treasury-cohort-vs-table, derived-ledger-ownership, greeks-home.
4. VM-prefix decisions recorded (with PRs to `vm_zombie_watchdog.py` if net-new prefixes are added).
5. Migration sub-plan stub published with phased structure.
6. Codex SSOT files published.
7. Cross-links updated across all 6 related epics + master plan.

## Risk callouts

- **Foundation-completion-gate risk**: derived ledgers (Position/Exposure/PnL/Attribution) depend on SSOT ledgers being
  correct. Per `Data Pipeline Correctness Is The Heartbeat`, no derived-ledger refactor ships before SSOT ledgers are
  GREEN-audited for the affected asset_groups. Implementation sub-plans (Phase 9 output) MUST sequence SSOT first.
- **Single-walk discipline**: per `gcs_migration_bundle_pipeline_mode_2026_05_08.md`, any historical backfill of
  existing events into canonical ledgers MUST bundle with the next scheduled GCS migration walk, not a fresh walk.
- **Late-arriving-data event-sourced bias**: prefer Option A (append-only enrichment rows) unless query complexity is
  shown to materially block downstream consumers — Citadel-style is event-sourced.
- **Cross-client funds isolation**: every transfer/bridge row writer MUST hit the UAC validator. Workspace HARD RULE per
  `codex/04-architecture/client-funds-isolation.md`.

## Deferred work / out-of-scope for this discovery plan

- Implementation of any UAC schema beyond pydantic stubs — Phase 9 migration sub-plan owns.
- Backfill of historical events — Phase 9 migration sub-plan owns.
- DART / alerting-service / client-reporting-api refactor to read from canonical ledgers — Phase 9 migration sub-plan
  owns.
- Greeks-computation-home implementation — Phase 5 is design-only; implementation in a separate sub-plan if it lands in
  MTDS (`mtds_mdps_master.md`) or a new module.
