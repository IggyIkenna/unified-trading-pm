---
title: Global Ledger + PnL Attribution — discovery, target-state spec, delta-to-current-system
parent_epic: global_ledger_pnl_attribution_master
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

- [ ] [DESIGN] P0. Survey downstream join patterns (DART, client-reporting-api, alerting-service) to determine whether
      (A) is tolerable or (B) is required.
- [ ] [DESIGN] P0. Decision recorded with rationale + cross-reference to codex audit-trail requirements.

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

- [ ] [DESIGN] P1. PricingLedger row spec: mid/bid/ask/IV + greeks (delta/gamma/theta/vega/rho) + carry-family rates
      (funding_rate, lending_apr, borrow_apr, dividend_yield, staking_apr, rebase_rate).
- [ ] [DESIGN] P1. Greeks computation home: MTDS vs strategy-service vs new module. Operator decision likely required
      for greeks-vs-IV ownership.
- [ ] [DESIGN] P1. Carry-family rate sourcing: which instruments-service handler emits what; gaps to fill.
- [ ] [DESIGN] P1. Snapshot vs streaming cadence: PricingLedger row per tick? Per minute? Operator-tunable per
      asset_group?

### Phase 6 — Treasury cohort vs separate table (P1)

- [ ] [DESIGN] P1. Consumer-overlap survey: does fund-administration-service / client-reporting-api / regulatory
      reporting need treasury rows separately from trading rows?
- [ ] [DESIGN] P1. Cardinality vs SLA trade-off recorded.
- [ ] [DESIGN] P1. Decision (own table vs filter-view) with rationale.

### Phase 7 — Backtest synthesiser parity (P1)

- [ ] [DESIGN] P1. PassiveLedger synthesiser runs in TWO modes: live (listens + reconciles vs synthesised expectation)
      and backtest/paper (synthesises from schedule alone). Document the contract that keeps backtest
      `Σ passive PnL = live Σ passive PnL` for the same instrument set + time window.
- [ ] [DESIGN] P1. InstructionLedger replay-from-history for backtest (already a workspace pattern via batch=live —
      `codex/04-architecture/batch-live-architecture.md`).

### Phase 8 — VM assignment for net-new runtime artifacts (P1)

- [ ] [INFRA] P1. **ledger-reconcile-** VM prefix decision: net-new (declare in `VM_PREFIX_TO_BUCKET` with
      `LifecycleClass.SCHEDULED_RECURRING`, launcher in `deployment-service/scripts/vm/launch-ledger-reconcile-vm.sh`)
      vs absorb into existing `batch-live-recon-cron-` cohort.
- [ ] [INFRA] P1. **passive-listener-** VM prefix decision: dedicated `LONG_LIVED_LIVE` daemon vs absorb into MTDS /
      execution-service worker.
- [ ] [INFRA] P1. Confirm derived-ledger compute home = `strategy-paper-*` + `strategy-live-*` +
      `client-reporting-cutover-*` (existing cohorts; no new prefixes).
- [ ] [INFRA] P1. Lifecycle compliance: every new prefix carries `VmPrefixSpec(bucket=..., lifecycle_class=...)` per the
      workspace HARD RULE.

### Phase 9 — Migration sub-plan stub (P1)

- [ ] [DOC] P1. Create `plans/active/global_ledger_pnl_attribution_migration_2026_06_XX.md`
      (`parent_epic: global_ledger_pnl_attribution_master`) with: (a) UAC schemas landing (Phase 2 deliverable
      upstream). (b) Writer-side refactors in execution-service. (c) Reader-side refactors in strategy-service `v2/`
      modules + client-reporting-api. (d) PassiveLedger synthesiser implementation (live + backtest modes). (e) Backfill
      of historical events into the canonical ledgers (single-walk discipline per
      `gcs_migration_bundle_pipeline_mode_2026_05_08.md`). (f) Cutover: derived views switch from service-internal state
      to canonical ledger reads.
- [ ] [DOC] P1. Stub declares `estimate_class: refactor` (likely; 0.4× multiplier) since most work is wiring existing
      engines into a new SSOT, not greenfield design.

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
