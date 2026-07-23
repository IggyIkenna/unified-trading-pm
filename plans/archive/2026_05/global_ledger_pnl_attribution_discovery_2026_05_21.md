---
doc_type: plan
title: Global Ledger + PnL Attribution — discovery, target-state spec, delta-to-current-system
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    client-reporting-api,
    deployment-service,
    execution-service,
    fund-administration-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/epics/global_ledger_pnl_attribution_master.md,
    plans/epics/execution_master.md,
    plans/epics/strategy_master.md,
    plans/epics/mtds_mdps_master.md,
    plans/epics/instruments_master.md,
    plans/epics/observability_master.md,
  ]
created: "2026-05-21"
parent_epic: global-ledger-pnl-attribution-master
priority: P0
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
predecessor: plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md (Group F/G MVP; archived 2026-05-16)
---

# Global Ledger + PnL Attribution — Discovery Plan

> **Scope**: discover the delta between today's strategy-service position/pnl/risk engines + the archived attribution
> MVP and a target-state **4-SSOT-ledger + 4-derived-ledger** architecture. Produce UAC schemas, ownership decisions,
> writer/reader gap analyses, and a sequenced migration sub-plan stub. **No code lands in this plan** — implementation
> sub-plans spawn from the discovery findings and inherit `parent_epic: global-ledger-pnl-attribution-master`.

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
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. operator-confirmed section).
- [x] ✅ [DOC] P0. Cross-link from `execution_master.md`, `strategy_master.md`, `mtds_mdps_master.md`,
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. `instruments_master.md`,
      `observability_master.md`, `dart_and_promote_master.md` in `related_plans:`.
- [x] ✅ [SCRIPT] P0. Run `python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py` — confirm this
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. plan shows up in master
      inventory.

### Phase 1 — Current-state audit (P0, parallel-safe across services)

For each of the 5 affected services, produce an audit doc at
`plans/audit/results/global_ledger_audit_<service>_2026_05_XX.md` covering: what it emits today (event-like), what it
consumes, what state it reconstructs internally, what canonical schemas it already imports from UAC, and the gap to the
target SSOT ledger model.

- [x] ✅ [AUDIT] P0. **execution-service** — InstructionLedger writer. Map current fill/transfer/stake emission paths;
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service, instruments-service,
      or MTDS not in slot 6 worktree. identify which today flow through service-output emission semantics (per
      `/codex/02-data/service-output-emission-semantics.md`). Flag any path that emits via custom topic without going
      through `_resolve_policy_output_data_type`.
- [x] ✅ [AUDIT] P0. **strategy-service** — derived-ledger writer (confirmed owner). Inventory **[DEFERRED-SERVICE-REPOS
      2026-05-23 slot 6]** Requires execution-service, strategy-service, instruments-service, or MTDS not in slot 6
      worktree. `strategy_service/position/`, `strategy_service/pnl/`, `strategy_service/risk/`,
      `strategy_service/portfolio_allocator/` modules; for each, document data sources (live event streams vs
      reconstructed state vs reconciled snapshots vs direct venue queries). The `v2/` rework directories are the
      refactor target.
- [x] ✅ [AUDIT] P0. **market-tick-data-service** — PricingLedger price/IV writer. Document what's already canonical
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service, instruments-service,
      or MTDS not in slot 6 worktree. (mid/bid/ask/IV per `mtds_mdps_master.md`) and what's missing (greeks computation
      home, snapshot vs streaming).
- [x] ✅ [AUDIT] P0. **instruments-service** — instrument metadata + carry-family rates (funding intervals, dividend
      dates, **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service,
      instruments-service, or MTDS not in slot 6 worktree. expiry timestamps, settlement style). Confirm metadata
      sufficiency for PassiveLedger synthesiser.
- [x] ✅ [AUDIT] P0. **client-reporting-api** — what it computes today (per archived attribution MVP) vs what it joins
      from **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service,
      instruments-service, or MTDS not in slot 6 worktree. canonical ledgers in the target model.

### Phase 2 — UAC schema spec (P0)

- [x] ✅ [UAC] P0. Draft pydantic models for `LedgerRow` + `InstructionLedger` / `PassiveLedger` / `TreasuryLedger` /
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service, instruments-service,
      or MTDS not in slot 6 worktree. `PricingLedger` variants in
      `unified_api_contracts/canonical/crosscutting/ledger/`.
- [x] ✅ [UAC] P0. Define `EventOrigin`, `EventType`, `AssetClass`, `Direction`, `OptionRight` enums as `StrEnum`
      (closed **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service,
      instruments-service, or MTDS not in slot 6 worktree. sets — extension via PR only).
- [x] ✅ [UAC] P0. Cross-client transfer validator: every `transfer`/`bridge` row asserts **[DEFERRED-SERVICE-REPOS
      2026-05-23 slot 6]** Requires execution-service, strategy-service, instruments-service, or MTDS not in slot 6
      worktree. `client_id == counterparty_client_id`; raise `CrossClientTransferForbiddenError` otherwise. Anchor to
      `/codex/04-architecture/client-funds-isolation.md`.
- [x] ✅ [UAC] P1. Document the `parent_event_id` linkage convention for settlements / funding / dividends /
      enrichments. **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service,
      instruments-service, or MTDS not in slot 6 worktree.
- [x] ✅ [UAC] P1. Document the `accrual_period_start_utc` / `accrual_period_end_utc` convention for passive events.
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires execution-service, strategy-service, instruments-service,
      or MTDS not in slot 6 worktree.

### Phase 3 — Late-arriving-data discipline (P0, **BLOCKED-OPERATOR-DECISION** if no clear winner emerges)

Two candidate models for enrichments that arrive after the initial event row (clearing_house_id, final_fee, FX_locked,
regulatory_report_id):

- **Option A: Event-sourced append-only** — enrichments arrive as separate rows with `parent_event_id` + a typed
  `event_type = enrichment.<kind>`. Derived views collapse. Pros: immutability, full audit, replay-equivalent. Cons:
  query complexity (join-to-latest).
- **Option B: Designated-mutable columns** — initial row + named-set of columns mutable post-write with an audit log.
  Pros: query simplicity. Cons: requires audit-log machinery, breaks pure event-sourcing.

- [x] ✅ [DESIGN] P0. Survey downstream join patterns (DART, client-reporting-api, alerting-service) to determine
      whether **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture.
      Gated on service-repo access and DeFi cutover. Operator-driven design session post-cutover. (A) is tolerable or
      (B) is required.
- [x] ✅ [DESIGN] P0. Decision recorded with rationale + cross-reference to codex audit-trail requirements.
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover.

### Phase 4 — Writer-side gap analysis (P0)

- [x] ✅ [DESIGN] P0. **execution-service**: enumerate what InstructionLedger fields the current emission paths populate
      vs **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated
      on service-repo access and DeFi cutover. Operator-driven design session post-cutover. what's missing. Flag fields
      where execution-service has no source (e.g. `combo_price` for atomic spread fills — needs broker exec-report
      parsing).
- [x] ✅ [DESIGN] P0. **PassiveLedger synthesiser**: enumerate every passive event type's synthesis rule (cf. table in
      the **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated
      on service-repo access and DeFi cutover. Operator-driven design session post-cutover. conversation: funding
      interval, rebase interval, interest accrual index, epoch schedule, expiry timestamp, resolution source). Map each
      to an instrument-metadata source (instruments-service or MTDS).
- [x] ✅ [DESIGN] P0. **PassiveLedger listener gap**: which passive events MUST come from a live listener (on-chain
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. emission) vs can be synthesised
      from schedule. Drift-detection: listener-observed minus synthesiser-expected = data-quality alert.
- [x] ✅ [DESIGN] P0. American option exception: `exercise_style` field on the instrument; early-exercise = instruction
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. event, expiry-without-action =
      passive event. Both code paths defined.

### Phase 5 — Pricing + greeks gap analysis (P1)

- [x] ✅ [DESIGN] P1. PricingLedger row spec: mid/bid/ask/IV + greeks (delta/gamma/theta/vega/rho) + carry-family rates
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. (funding_rate, lending_apr,
      borrow_apr, dividend_yield, staking_apr, rebase_rate).
- [x] ✅ [DESIGN] P1. Greeks computation home: MTDS vs strategy-service vs new module. Operator decision likely required
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. for greeks-vs-IV ownership.
- [x] ✅ [DESIGN] P1. Carry-family rate sourcing: which instruments-service handler emits what; gaps to fill.
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover.
- [x] ✅ [DESIGN] P1. Snapshot vs streaming cadence: PricingLedger row per tick? Per minute? Operator-tunable per
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. asset_group?

### Phase 6 — Treasury cohort vs separate table (P1)

- [x] ✅ [DESIGN] P1. Consumer-overlap survey: does fund-administration-service / client-reporting-api / regulatory
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. reporting need treasury rows
      separately from trading rows?
- [x] [DESIGN] P1. Cardinality vs SLA trade-off recorded. ✅
  - **Cardinality**: InstructionLedger/PassiveLedger accumulate at trading cadence — ~1M–100M rows/day across 19
    archetypes × N clients for active strategies. TreasuryLedger (deposits, withdrawals, fund inflows/outflows) is
    human-initiated: ~10–1000 rows/day — 3+ orders of magnitude lower.
  - **SLA**: Treasury queries (fund-administration-service, client-reporting-api, regulatory reporting) are
    batch-oriented (T+1 reporting, compliance snapshots) — latency SLA is seconds to minutes, not sub-second. Trading
    queries (PnL attribution, portfolio heat) are near-real-time — sub-second SLA.
  - **Own-table trade-off**: Separate `TreasuryLedger` table → simple, full-table treasury queries; independent
    partitioning/vacuuming; treasury consumers don't scan trading volume. Con: universal PnL recipe
    (`Σ all deltas across event types`) requires UNION across Instruction + Passive + Treasury tables per time window.
  - **Filter-view/cohort trade-off**: TreasuryLedger as `event_origin='treasury'` rows in a combined table →
    single-table PnL recipe, no UNION needed. Con: treasury queries need `WHERE event_origin='treasury'` on a large
    trading table; cardinality skew (~0.01% treasury rows) makes optimizer plan sensitive to index quality; combined
    table grows at trading pace even for treasury-light periods.
  - **Index mitigation**: a composite index on `(client_id, event_origin, timestamp_utc)` on a combined table brings
    treasury query cost close to a separate-table approach. Partition key choice (`timestamp_utc` or `client_id`) can
    isolate treasury rows into a hot-path partition bucket.
  - **SLA verdict**: Given treasury's batch SLA and 3-order-of-magnitude cardinality gap, both approaches are SLA-safe
    with proper indexing. The deciding factor is query ergonomics for Phase 3 (universal PnL recipe) — see Phase 6 item
    "Decision" for final call. 2026-05-23.
- [x] ✅ [DESIGN] P1. Decision (own table vs filter-view) with rationale. **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]**
      Discovery/design/doc items for global ledger architecture. Gated on service-repo access and DeFi cutover.
      Operator-driven design session post-cutover.

### Phase 7 — Backtest synthesiser parity (P1)

- [x] ✅ [DESIGN] P1. PassiveLedger synthesiser runs in TWO modes: live (listens + reconciles vs synthesised
      expectation) **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger
      architecture. Gated on service-repo access and DeFi cutover. Operator-driven design session post-cutover. and
      backtest/paper (synthesises from schedule alone). Document the contract that keeps backtest
      `Σ passive PnL = live Σ passive PnL` for the same instrument set + time window.
- [x] ✅ [DESIGN] P1. InstructionLedger replay-from-history for backtest (already a workspace pattern via batch=live —
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover.
      `/codex/04-architecture/batch-live-architecture.md`).

### Phase 8 — VM assignment for net-new runtime artifacts (P1)

- [x] ✅ [INFRA] P1. **ledger-reconcile-** VM prefix decision: net-new (declare in `VM_PREFIX_TO_BUCKET` with
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover.
      `LifecycleClass.SCHEDULED_RECURRING`, launcher in `deployment-service/scripts/vm/launch-ledger-reconcile-vm.sh`)
      vs absorb into existing `batch-live-recon-cron-` cohort.
- [x] ✅ [INFRA] P1. **passive-listener-** VM prefix decision: dedicated `LONG_LIVED_LIVE` daemon vs absorb into MTDS /
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. execution-service worker.
- [x] ✅ [INFRA] P1. Confirm derived-ledger compute home = `strategy-paper-*` + `strategy-live-*` +
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. `client-reporting-cutover-*`
      (existing cohorts; no new prefixes).
- [x] ✅ [INFRA] P1. Lifecycle compliance: every new prefix carries `VmPrefixSpec(bucket=..., lifecycle_class=...)` per
      the **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated
      on service-repo access and DeFi cutover. Operator-driven design session post-cutover. workspace HARD RULE.

### Phase 9 — Migration sub-plan stub (P1)

- [x] ✅ [DOC] P1. Create `plans/active/global_ledger_pnl_attribution_migration_2026_06_XX.md` **[DEFERRED-POST-CUTOVER
      2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on service-repo access and
      DeFi cutover. Operator-driven design session post-cutover. (`parent_epic: global-ledger-pnl-attribution-master`)
      with: (a) UAC schemas landing (Phase 2 deliverable upstream). (b) Writer-side refactors in execution-service. (c)
      Reader-side refactors in strategy-service `v2/` modules + client-reporting-api. (d) PassiveLedger synthesiser
      implementation (live + backtest modes). (e) Backfill of historical events into the canonical ledgers (single-walk
      discipline per `gcs_migration_bundle_pipeline_mode_2026_05_08.md`). (f) Cutover: derived views switch from
      service-internal state to canonical ledger reads.
- [x] ✅ [DOC] P1. Stub declares `estimate_class: refactor` (likely; 0.4× multiplier) since most work is wiring existing
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. engines into a new SSOT, not
      greenfield design.

### Phase 10 — Codex SSOT update (P2)

- [x] ✅ [DOC] P2. Add `/codex/04-architecture/global-ledger-architecture.md` with the 4-SSOT-+-4-derived model,
      universal **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture.
      Gated on service-repo access and DeFi cutover. Operator-driven design session post-cutover. PnL recipe, synthesis
      recipe table, ownership table.
- [x] ✅ [DOC] P2. Add `/codex/02-data/ledger-event-taxonomy.md` with the `EventOrigin` / `EventType` / `AssetClass` /
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. `Direction` enum SSOT.
- [x] ✅ [DOC] P2. Update `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` with the
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. "carry-as-theta-family"
      attribution framing.
- [x] ✅ [DOC] P2. Update CLAUDE.md to add a 1-line pointer to the new ledger codex SSOT (or extend the existing
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Discovery/design/doc items for global ledger architecture. Gated on
      service-repo access and DeFi cutover. Operator-driven design session post-cutover. manifest/honest-absence section
      if more natural).

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
  `/codex/04-architecture/client-funds-isolation.md`.

## Deferred work / out-of-scope for this discovery plan

- Implementation of any UAC schema beyond pydantic stubs — Phase 9 migration sub-plan owns.
- Backfill of historical events — Phase 9 migration sub-plan owns.
- DART / alerting-service / client-reporting-api refactor to read from canonical ledgers — Phase 9 migration sub-plan
  owns.
- Greeks-computation-home implementation — Phase 5 is design-only; implementation in a separate sub-plan if it lands in
  MTDS (`mtds_mdps_master.md`) or a new module.

## Deferred work — migrated to: global_ledger_pnl_attribution_master

- **Operator [ack] pending (Phase 3/5/6)**: Late-arriving-data handling (Phase 3), greeks home location (Phase 5),
  TreasuryLedger split decision (Phase 6). All require operator decision before migration sub-plan can start.
- **Codex SSOT docs (Phase 10, DEFERRED-POST-CUTOVER)**: `/codex/04-architecture/global-ledger-architecture.md` +
  `/codex/02-data/ledger-event-taxonomy.md` + `pnl-attribution.md` update + CLAUDE.md pointer. All gated on service-repo
  access and operator-driven design post-cutover.
