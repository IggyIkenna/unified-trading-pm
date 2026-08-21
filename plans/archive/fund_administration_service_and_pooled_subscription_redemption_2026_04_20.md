---
doc_type: plan
title: fund-administration-service-and-pooled-subscription-redemption
summary: Build the subscription/redemption rail for IM Pooled clients — UAC fund_administration domain types, new fund-administration-service
  with subscription/redemption state machine + capital-routing orchestrator, platform UI pages under /services/im/funds/
  — by extending existing primitives (TreasuryMonitor, TransferAdapter, CustodyProvider, FundNAVSnapshot, FeeStructure)
  rather than re-inventing them. Treasury/buffer wallet split is already generic in position-balance-monitor-service; this
  plan layers fund-admin semantics (share classes, NAV-strike unit issuance, grace-period redemption settlement) on top.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    client-reporting-api,
    execution-service,
    fund-administration-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
type: mixed
epic: epic-path-to-100m
locked_by: live-defi-rollout
locked_since: 2026-04-20
completion_gates: { code: C5, deployment: D3, business: B3 }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: fund-administration-service, code: C0, deployment: D3, business: B3 }
  - { repo: unified-trading-system-ui, code: C0, deployment: D2, business: none }
  - { repo: client-reporting-api, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: []
estimate_class: design
estimate_baseline_ai_days: TBD
estimate_calibrated_ai_days: TBD
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (design, multiplier 0.6×).

  Owner agent: fill baseline + multiply × 0.6 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Context

> **🟢 SCOPE CLARIFICATION — RATIFIED 2026-05-10 cross-plan audit L4.** Two areas where May-10 plans pulled scope
> forward from this plan:
>
> - **Performance-fee HWM accounting** (originally fund_administration's settlement scope) → pulled into
>   [`wallet_treasury_client_flow_2026_05_10.md`](wallet_treasury_client_flow_2026_05_10.md) Phase 5.G for May-23
>   cutover (operator direction 2026-05-10). `PerformanceFeeCrystallizedEvent` is shipped by wallet_treasury; this plan
>   inherits the event for pooled-fund-level NAV+HWM ledger consolidation post-cutover (no re-implementation needed).
> - **Per-client treasury rollup endpoint** → owned by
>   [`api_keys_wallets_accounts_readiness_2026_05_10.md`](api_keys_wallets_accounts_readiness_2026_05_10.md) Phase 3.D
>   (canonical multi-source rollup) + wallet_treasury Phase 6.A (per-client attribution layer).
>
> **This plan REMAINS canonical for**: fund-level (vs client-level) NAV calc, pooled subscription/redemption flow,
> qualified-custodian (Copper/CEFFU) booking, AIFMD/regulatory disclosures, audit/tax reporting, multi-fund accounting.
> Those domains have NOT been pulled forward and stay post-cutover (Group H+).

> **Cross-plan position 2026-05-08**: this plan is **POST-2026-05-23 P2**. Fund administration + pooled subscription /
> redemption is institutional infrastructure that does **NOT** block the May-23 live-DeFi cutover. The cutover model is
> single-wallet operator-funded; pooled subscription is a Q3 2026 follow-on. Owner: Ikenna (operator + governance); not
> assigned in current daily splits ([`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) +
> [`work_split_2026_05_08_harsh.md`](work_split_2026_05_08_harsh.md) defer this plan in their "Defer post-cutover"
> sections).
>
> **Master plan position**: NOT on [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) critical
> path. May-23 readiness ladder is Group A-G; fund administration is Group H+ (post-cutover scope). **Re-prioritise
> post-cutover** when the operator picks up institutional client onboarding work — at that point this plan moves to
> active-priority status + gets daily-split assignment per CLAUDE.md "Daily Work-Split Process".
>
> **Successor plan when this plan picks up**: this plan IS its own completion (no further successor needed). Per
> CLAUDE.md "Citadel-Grade Planning Standards §3 — No Technical Debt", every phase's exit criteria is the final
> production shape; no fold-into-umbrella is required because this plan's domain (fund administration) is orthogonal to
> the May-23 live-trading umbrellas.

## Why this plan

**User correction 2026-04-20:** the briefing copy + codex drift previously suggested a universal "treasury wallet + Odum
sub-account" model across all paths. The corrected model is:

| Path                 | Custody                                     | Capital rail                                             |
| -------------------- | ------------------------------------------- | -------------------------------------------------------- |
| IM — Pooled (Fund)   | Qualified 3rd-party custodian (Copper etc.) | **Portal subscription / redemption via POD** ← this plan |
| IM — SMA             | Client-owned venue accounts                 | Client funds venue directly                              |
| DART — Signals-In    | Client-owned venue accounts                 | Client funds venue directly                              |
| DART — Full Pipeline | Client-owned venue accounts                 | Client funds venue directly                              |
| Regulatory Umbrella  | Client-owned venue accounts                 | Client funds venue directly                              |
| Odum Signals-Out     | Counterparty stack                          | N/A                                                      |

The subscription / redemption mechanic applies to **IM Pooled only**. SMA + DART + Reg Umbrella clients hold their own
venue accounts and do not touch this rail.

SSOTs now reflecting the correction:

- `/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md` — custody model per path; Odum never
  custodies; POD is the fund administrator; Copper (and equivalents) named as qualified custodians.
- `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` — Pooled subscription/redemption rail;
  portal surface; contract surface sketch (this plan is its implementation).

## Existing primitives to reuse (not rebuild)

Pre-audit 2026-04-20 (`unified-trading-system-ui` Explore agent):

- [execution-service/execution_service/custody/base.py](../../../execution-service/execution_service/custody/base.py) —
  `CustodyProvider` protocol (Mock / LocalKey / Copper MPC). Signing + balance queries + atomic transfers. **Reuse
  as-is.**
- [execution-service/execution_service/engine/transfers/adapter.py](../../../execution-service/execution_service/engine/transfers/adapter.py)
  — `TransferAdapter` protocol with CCXT (CeFi), Custody (DeFi), Composite implementations. `execute_internal_transfer`,
  `execute_withdrawal`, `execute_onchain_transfer`, `get_balance`. **Reuse — this IS the capital-routing rail already.**
- [position-balance-monitor-service/position_balance_monitor_service/core/treasury_monitor.py](../../../position-balance-monitor-service/position_balance_monitor_service/core/treasury_monitor.py)
  — `TreasuryMonitor` with `WalletConfig`, `TreasuryConfig` (reserve_pct, min_threshold_pct, max_threshold_pct),
  `TreasurySnapshot` (treasury_balance_usd, total_trading_balance_usd, per_strategy_balance). Emits TREASURY_LOW /
  TREASURY_HIGH. **The treasury-vs-trading-wallet-with-buffer concept already exists generically** — this plan extends
  it with optional target_allocations + share-class keying.
- [unified-api-contracts/unified_api_contracts/internal/domain/client_reporting/nav_snapshot.py](../../../unified-api-contracts/unified_api_contracts/internal/domain/client_reporting/nav_snapshot.py)
  — `FundNAVSnapshot` (nav_usd, asset_balances, venue_balances, strategy_exposures_usd). **Reuse as-is for NAV strike
  points.**
- [unified-api-contracts/unified_api_contracts/internal/reporting/fee_structure.py](../../../unified-api-contracts/unified_api_contracts/internal/reporting/fee_structure.py)
  — `FeeStructure` with trader/odum/introducer tiers + HWM. **Reuse as-is for redemption fee calculation.**
- [unified-api-contracts/unified_api_contracts/internal/domain/account.py](../../../unified-api-contracts/unified_api_contracts/internal/domain/account.py)
  — `TradingAccount`, `AccountType`. **Extend additively with `WalletRole` enum field (default None for back-compat).**
- [unified-api-contracts/unified_api_contracts/canonical/crosscutting/share_class.py](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/share_class.py)
  — `ShareClass` canonical type. **Reuse as-is.**
- `unified-trading-system-ui/app/(platform)/services/reports/fund-operations/page.tsx` — investor register +
  capital-account ledger + distribution waterfall already exist. **Extend with subscription/redemption capture +
  allocator-facing views.** (Path kept as inline code because the `(platform)` Next.js route-group segment confuses the
  markdown-link validator; Cursor still auto-links the path.)

## What this plan adds

1. **UAC** — new `unified_api_contracts.internal.domain.fund_administration` sub-package:
   - `AllocatorSubscription` — subscription_id, fund_id, allocator_id (= client_id), requested_amount_usd, share_class,
     requested_timestamp, status, nav_strike_snapshot_id, units_issued, approval_timestamp.
   - `AllocatorRedemption` — redemption_id, fund_id, allocator_id, units_to_redeem, share_class, requested_timestamp,
     status, grace_period_days, redemption_nav_snapshot_id, cash_amount_due_usd, settlement_timestamp.
   - `FundAllocation` — fund_id, strategy_id, target_amount_usd, share_class, allocation_timestamp, execution_status.
   - `SubscriptionStatus` + `RedemptionStatus` + `AllocationExecutionStatus` enums.
2. **UAC** — add `WalletRole` enum to `TradingAccount` (`TREASURY` / `TRADING` / `RESERVE`), additive + defaults to
   None.
3. **UTL** — register 6 lifecycle events in `STANDARD_LIFECYCLE_EVENTS`: `SUBSCRIPTION_REQUESTED`,
   `SUBSCRIPTION_APPROVED`, `SUBSCRIPTION_REJECTED`, `SUBSCRIPTION_SETTLED`, `REDEMPTION_REQUESTED`,
   `REDEMPTION_APPROVED`, `REDEMPTION_REJECTED`, `REDEMPTION_PROCESSED`, `REDEMPTION_SETTLED`,
   `FUND_ALLOCATION_REBALANCED`.
4. **position-balance-monitor-service** — extend `TreasuryConfig` with optional `target_allocations: dict[str, Decimal]`
   (strategy_id → target_usd) and optional `share_class: str` + `fund_id: str` keying.
5. **fund-administration-service** — NEW repo. Subscription/redemption state machine + REST API + capital-routing
   orchestrator + background tasks (subscription approval automation, grace-period expiry handler). Depends on
   TransferAdapter (execution-service) for capital movement, TreasuryMonitor (PBMS) for balance queries, FeeStructure
   (UAC) for redemption fees.
6. **unified-trading-system-ui** — NEW routes under `app/(platform)/services/im/funds/`: subscription-request form,
   redemption-request form, allocation-health dashboard, history ledger. Wire to fund-administration-service API. Extend
   existing `/services/reports/fund-operations/` views rather than duplicate.
7. **client-reporting-api** — extend reporting routes to include allocator-facing views (subs/reds history, cash account
   movements) filtered by `client_id` and `share_class`.
8. **Codex** — update `treasury-and-subaccount-model.md` with the concrete contract/event names and service endpoints as
   they land.

## Execution DAG

```
Phase 0 (UAC + UTL)
     │
     ├─→ Phase 1a (PBMS extension)  ──┐
     │                                 │
     ├─→ Phase 1b (ES TransferAdapter ─┤  (both independent of each other)
     │       signature)                │
     │                                 ▼
     └────────────────────→ Phase 2 (fund-administration-service core)
                                       │
                              ┌────────┴────────┐
                              ▼                 ▼
                       Phase 3 (UI)      Phase 4 (Integration tests)
                              │                 │
                              └────────┬────────┘
                                       ▼
                              Phase 5 (Codex + memory + sign-off)
```

---

# Todos

## Phase 0 — UAC + UTL foundations (PARALLEL with itself, SEQUENTIAL with everything else)

- id: uac-fund-administration-subpackage content: |
  - [x] [AGENT] P0. UAC: create sub-package `unified_api_contracts/internal/domain/fund_administration/` with types
        `AllocatorSubscription`, `AllocatorRedemption`, `FundAllocation`, and enums `SubscriptionStatus`,
        `RedemptionStatus`, `AllocationExecutionStatus`. Re-export from `unified_api_contracts.internal` facade per
        Citadel import rules. Dataclasses with frozen=True; AwareDatetime; Decimal for money. No pydantic BaseModel
        unless the type is externally serialised. Mirror the schema sketch in
        `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` §"Contract surface". status: pending

- id: uac-wallet-role-enum content: |
  - [x] [AGENT] P0. UAC: add `WalletRole` enum (`TREASURY` / `TRADING` / `RESERVE`) to `internal/domain/account.py`. Add
        `wallet_role: WalletRole | None = None` field to `TradingAccount`. Additive + default None preserves
        back-compat; no downstream migration required. status: pending

- id: utl-lifecycle-events content: |
  - [x] [AGENT] P0. UTL: register 10 events in `STANDARD_LIFECYCLE_EVENTS` — `SUBSCRIPTION_REQUESTED`,
        `SUBSCRIPTION_APPROVED`, `SUBSCRIPTION_REJECTED`, `SUBSCRIPTION_SETTLED`, `REDEMPTION_REQUESTED`,
        `REDEMPTION_APPROVED`, `REDEMPTION_REJECTED`, `REDEMPTION_PROCESSED`, `REDEMPTION_SETTLED`,
        `FUND_ALLOCATION_REBALANCED`. Add event payload schemas that reference UAC fund_administration types. status:
        pending

- id: uac-tests content: |
  - [x] [AGENT] P0. UAC tests: roundtrip serialisation + frozen-dataclass invariants for each new type; ensure
        `unified_api_contracts.internal` facade re-exports work.
        `cd unified-api-contracts && bash scripts/quality-gates.sh` must pass. status: pending

## Phase 1a — PBMS TreasuryMonitor extension (PARALLEL with Phase 1b)

- id: pbms-treasury-config-extend content: |
  - [x] [AGENT] P0. PBMS: extend `TreasuryConfig` in `position_balance_monitor_service/core/treasury_monitor.py` with
        optional `target_allocations: dict[str, Decimal] | None = None` (strategy_id → target USD), optional
        `share_class: str | None = None`, optional `fund_id: str | None = None`. All additive + backwards compatible.
        status: pending

- id: pbms-treasury-snapshot-delta content: |
  - [x] [AGENT] P0. PBMS: add `allocation_deltas: dict[str, Decimal]` to `TreasurySnapshot` — per-strategy delta from
        target (positive = needs top-up from treasury, negative = excess in trading wallet that should sweep back).
        Delta computed when `target_allocations` is set; None when not set. status: pending

- id: pbms-per-share-class-keying content: |
  - [ ] [AGENT] P0. PBMS: allow `TreasuryMonitor` to be instantiated per-(fund_id, share_class) so a fund with BTC /
        USDC / ETH share classes gets one monitor each. Emit `TREASURY_LOW`/`HIGH` events with fund_id + share_class
        context. status: pending

- id: pbms-tests content: |
  - [ ] [AGENT] P0. PBMS tests: target-allocations math; per-share-class instantiation; event emission carries fund_id +
        share_class. `cd position-balance-monitor-service && bash scripts/quality-gates.sh` must pass + coverage ratchet
        held. status: pending

## Phase 1b — Execution-service TransferAdapter fund-context (PARALLEL with Phase 1a)

- id: es-transfer-fund-context content: |
  - [x] [AGENT] P0. ES: extend `TransferAdapter.execute_internal_transfer` signature with optional
        `fund_context: FundTransferContext | None = None` where
        `FundTransferContext = {fund_id: str, share_class: str, allocation_id: str | None}`. All adapter impls accept +
        pass-through into event payloads. Additive; no behavioural change when fund_context is None. status: pending

- id: es-transfer-tests content: |
  - [ ] [AGENT] P0. ES tests: fund_context pass-through in Mock, CCXT (CeFi), Custody (DeFi), Composite adapters.
        `cd execution-service && bash scripts/quality-gates.sh` must pass. status: pending

## Phase 2 — fund-administration-service (SEQUENTIAL after Phase 0 + Phase 1a + Phase 1b)

- id: fas-repo-scaffold content: |
  - [x] [AGENT] P0. Create NEW repo `fund-administration-service/` with standard service scaffolding per
        `unified-trading-library` template — pyproject.toml (flat deps), Dockerfile (ARG PROJECT_ID +
        asia-northeast1-docker.pkg.dev base), scripts/quality-gates.sh, ServiceBootstrap wiring (per STEP 5.61 QG rule),
        api/main.py with make_health_router (STEP 5.62), typed config reloaders (STEP 5.34), tests/ + mocks. Add to
        workspace-manifest.json. status: pending

- id: fas-subscription-state-machine content: |
  - [x] [AGENT] P0. FAS: implement subscription state machine — `PENDING → APPROVED / REJECTED → SETTLED`. Approval step
        runs AML/KYC gate (stub for now, real POD integration in follow-up); on approval, resolve NAV strike from
        nearest FundNAVSnapshot and compute units_issued = amount / nav_per_unit. On SETTLED, emit SUBSCRIPTION_SETTLED
        and update share-class unit register. status: pending

- id: fas-redemption-state-machine content: |
  - [x] [AGENT] P0. FAS: implement redemption state machine — `PENDING → APPROVED / REJECTED → PROCESSED → SETTLED`.
        Approval runs liquidity + mandate-limit gates. On APPROVED, schedule grace-period expiry (default 5 days,
        configurable per fund). On grace-period expiry, resolve settlement NAV from FundNAVSnapshot, compute
        cash_amount_due (units \* settlement_nav - redemption_fees via FeeStructure), call
        TransferAdapter.execute_withdrawal from treasury wallet to client's declared destination, emit
        REDEMPTION_PROCESSED then REDEMPTION_SETTLED with tx hash / wire ref. status: pending

- id: fas-capital-routing-orchestrator content: |
  - [x] [AGENT] P0. FAS: `CapitalRouter` that reads `TreasurySnapshot.allocation_deltas` from PBMS, decides which
        per-strategy trading wallets to top-up or sweep, calls `TransferAdapter.execute_internal_transfer` for each with
        `FundTransferContext`, tracks rebalance in `FundAllocation` records, emits FUND_ALLOCATION_REBALANCED.
        Idempotent on `allocation_id`. status: pending

- id: fas-rest-api content: |
  - [x] [AGENT] P0. FAS: REST API — `POST /subscriptions`, `GET /subscriptions/{id}`,
        `POST /subscriptions/{id}/approve`, `POST /redemptions`, `GET /redemptions/{id}`,
        `GET /funds/{fund_id}/allocations`, `POST /funds/{fund_id}/allocations/rebalance`,
        `GET /funds/{fund_id}/nav/history`. OpenAPI spec + contract tests against UAC types. Auth via platform API-key;
        route all writes through audit-log event emission. status: pending

- id: fas-background-tasks content: |
  - [x] [AGENT] P1. FAS: background tasks — subscription auto-approval on clean AML (stub for now); grace-period expiry
        handler (polls pending redemptions with settlement due); NAV-strike scheduler (triggers FundNAVSnapshot capture
        at publish cadence). Use scheduler pattern from other services. status: pending

- id: fas-tests content: |
  - [ ] [AGENT] P0. FAS tests: unit tests for state machines; integration test for full subscription → NAV strike → unit
        issuance → allocation → redemption → settlement loop with Mock TransferAdapter + in-memory PBMS.
        `cd fund-administration-service && bash scripts/quality-gates.sh` must pass with coverage ≥ 70%. status: pending

## Phase 3 — Platform UI (PARALLEL with Phase 4 after Phase 2)

- id: ui-routes-scaffold content: |
  - [x] [AGENT] P0. UI: scaffold `app/(platform)/services/im/funds/` with routes `/subscriptions` (list + request form),
        `/redemptions` (list + request form), `/allocations` (current targets + rebalance button + treasury health),
        `/history` (per-allocator ledger). Match existing `/services/reports/fund-operations/` visual style. status:
        pending

- id: ui-api-client content: |
  - [x] [AGENT] P0. UI: lib/api/fund-administration.ts typed client for FAS REST API. Reuse existing auth-header
        injection pattern from other platform-API clients. status: pending

- id: ui-subscription-flow content: |
  - [ ] [AGENT] P0. UI: subscription request form — amount, currency, share-class picker, confirm modal, success toast
        with subscription_id + pending-approval notice. Wire to `POST /subscriptions`. Entitlement: show only if
        allocator has fund access. status: pending

- id: ui-redemption-flow content: |
  - [ ] [AGENT] P0. UI: redemption request form — units or notional, destination bank/wallet, grace-period notice
        ("settlement at next NAV strike, typically 5 business days"), confirm modal. Wire to `POST /redemptions`.
        status: pending

- id: ui-treasury-health-dashboard content: |
  - [ ] [AGENT] P1. UI: allocations page shows treasury/trading split per share class with visual gauge (reserve_pct vs
        current), per-strategy allocation vs target, and — for ops users only — a "Rebalance" action that calls
        `POST /funds/{fund_id}/allocations/rebalance`. status: pending

- id: ui-mock-mode content: |
  - [x] [AGENT] P0. UI: mock mode (VITE_MOCK_API=true) returns deterministic subscription/redemption fixtures so local
        dev + CI smoke works without backend. Fixtures cover PENDING / APPROVED / SETTLED subscription, plus pending +
        settled redemption with cash account ledger. status: pending

- id: ui-tests content: |
  - [ ] [AGENT] P0. UI tests: vitest unit tests for the subscription + redemption forms (validation, submit, error
        handling); one Playwright e2e that walks the happy path in mock mode from subscription request through approval
        to allocation display. `CI=true npm test -- --run` must pass. status: pending

## Phase 4 — Client-reporting-api allocator views (PARALLEL with Phase 3)

- id: cra-allocator-statements content: |
  - [x] [AGENT] P0. client-reporting-api: add routes `GET /allocators/{client_id}/subscriptions`,
        `GET /allocators/{client_id}/redemptions`, `GET /allocators/{client_id}/cash-account` (movements + balance).
        Filter strictly by client_id entitlement. Data sourced from fund-administration-service + existing
        FundNAVSnapshot pipeline. status: pending

- id: cra-tests content: |
  - [ ] [AGENT] P0. client-reporting-api tests: entitlement filter holds (client A can't read client B's data); payload
        schema matches UAC types; `cd client-reporting-api && bash scripts/quality-gates.sh` must pass. status: pending

## Phase 5 — Codex + briefings + memory cross-link (SEQUENTIAL after Phases 2-4)

- id: codex-treasury-doc-concretise content: |
  - [ ] [AGENT] P0. PM: update `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` — replace the
        "to-be-built" sketches with concrete UAC type paths, event names, and service endpoints as they landed. Add link
        to this plan in §Related docs. status: pending

- id: codex-service-index content: |
  - [ ] [AGENT] P0. PM: register `fund-administration-service` in `/codex/05-infrastructure/service-index.md` (if
        present) + add to `service-boundaries-and-responsibilities.md` decision table. status: pending

- id: briefings-concretise content: |
  - [ ] [AGENT] P1. UI: update the IM Pooled briefing section on `/briefings/investment-management` to reference the
        concrete portal surface (`/services/im/funds/`) once the UI is live. No schema claim beyond what the user sees.
        status: pending

- id: memory-followup content: |
  - [ ] [AGENT] P0. Memory: update `memory/project_custody_model_per_path_2026_04_20.md` with a "Platform now live" note
        once Phase 3 is in staging + add link to this plan. status: pending

## Phase 6 — Deployment + sign-off (SEQUENTIAL after Phase 5)

- id: fas-deploy-staging content: |
  - [ ] [AGENT] P0. Deploy fund-administration-service to staging — Cloud Run service per standard template; wire to
        staging PBMS + execution-service; smoke-test subscription + redemption loop in staging. D2 gate. status: pending

- id: fas-integration-staging content: |
  - [ ] [AGENT] P0. Integration tests in staging — real PBMS + execution-service calls; real Copper testnet custody for
        DeFi transfer path; end-to-end subscription → NAV strike → unit issuance → allocation → redemption → settlement
        with live webhook + event emission. D3 gate. status: pending

- id: ui-deploy-staging content: |
  - [ ] [AGENT] P0. Deploy UI changes to staging (`live-defi-rollout` or next feature branch). Smoke-test the new
        `/services/im/funds/` routes against staging FAS. D2 gate for UI. status: pending

- id: business-signoff content: |
  - [ ] [HUMAN] P0. Business sign-off — user confirms: (1) subscription flow reads correctly for an IM Pooled allocator;
        (2) redemption grace-period framing matches commercial model; (3) treasury-health dashboard is useful for ops;
        (4) codex + briefings remain internally consistent. B3 gate. status: pending

- id: quickmerge-all-affected content: |
  - [ ] [AGENT] P0. Quickmerge (`--agent`) across all 7 affected repos once each reaches its completion_gates target.
        Never `git push`; never `--dep-branch`. Push before quickmerge if local commits are ahead of origin. C5 gate per
        repo. status: pending

---

# Pre-audit manifest

Every file / symbol touched — so executing agents don't need to re-scan:

## Read-only reuse (NO edits — depend on as-is)

| File                                                                                           | Purpose                                                         |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `execution-service/execution_service/custody/base.py`                                          | CustodyProvider protocol — signing + balance + atomic transfers |
| `execution-service/execution_service/engine/transfers/adapter.py`                              | TransferAdapter protocol — CCXT / Custody / Composite impls     |
| `unified-api-contracts/unified_api_contracts/internal/domain/client_reporting/nav_snapshot.py` | FundNAVSnapshot for NAV strikes                                 |
| `unified-api-contracts/unified_api_contracts/internal/reporting/fee_structure.py`              | FeeStructure for redemption fee math                            |
| `unified-api-contracts/unified_api_contracts/canonical/crosscutting/share_class.py`            | ShareClass canonical type                                       |

## Additive edits (all back-compat, no breaking changes)

| File                                                                                          | Change                                                                                                                                |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/unified_api_contracts/internal/domain/fund_administration/__init__.py` | NEW — sub-package with 3 dataclasses + 3 enums                                                                                        |
| `unified-api-contracts/unified_api_contracts/internal/domain/account.py`                      | ADD `WalletRole` enum + `wallet_role: WalletRole \| None = None` field on `TradingAccount`                                            |
| `unified-api-contracts/unified_api_contracts/internal/__init__.py`                            | ADD re-exports for fund_administration types                                                                                          |
| `unified-trading-library/unified_trading_library/events/standard_lifecycle_events.py`         | ADD 10 event names + payload schemas                                                                                                  |
| `position-balance-monitor-service/position_balance_monitor_service/core/treasury_monitor.py`  | ADD `target_allocations`, `share_class`, `fund_id` optional fields to `TreasuryConfig`; ADD `allocation_deltas` to `TreasurySnapshot` |
| `execution-service/execution_service/engine/transfers/adapter.py`                             | ADD optional `fund_context: FundTransferContext \| None = None` to `execute_internal_transfer`                                        |

## New repo

| Path                                                                                         | Contents                                      |
| -------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `fund-administration-service/`                                                               | Full service scaffold per template            |
| `fund-administration-service/fund_administration_service/subscription/state_machine.py`      | Subscription PENDING→APPROVED→SETTLED         |
| `fund-administration-service/fund_administration_service/redemption/state_machine.py`        | Redemption PENDING→APPROVED→PROCESSED→SETTLED |
| `fund-administration-service/fund_administration_service/capital_router.py`                  | Treasury ↔ trading-wallet orchestrator        |
| `fund-administration-service/fund_administration_service/api/main.py`                        | FastAPI routes                                |
| `fund-administration-service/fund_administration_service/background/grace_period_handler.py` | Settles redemptions on grace-period expiry    |
| `fund-administration-service/fund_administration_service/background/nav_strike_scheduler.py` | Triggers NAV snapshot capture                 |
| `fund-administration-service/tests/`                                                         | Unit + integration tests                      |

## New UI routes (unified-trading-system-ui)

| Path                                                      | Contents                              |
| --------------------------------------------------------- | ------------------------------------- |
| `app/(platform)/services/im/funds/subscriptions/page.tsx` | List + request form                   |
| `app/(platform)/services/im/funds/redemptions/page.tsx`   | List + request form                   |
| `app/(platform)/services/im/funds/allocations/page.tsx`   | Treasury-health dashboard + rebalance |
| `app/(platform)/services/im/funds/history/page.tsx`       | Per-allocator cash-account ledger     |
| `lib/api/fund-administration.ts`                          | Typed FAS API client                  |
| `lib/mocks/fund-administration.ts`                        | Mock fixtures for VITE_MOCK_API=true  |

## Client-reporting-api new routes

| Route                                       | Purpose                              |
| ------------------------------------------- | ------------------------------------ |
| `GET /allocators/{client_id}/subscriptions` | Allocator's own subscription history |
| `GET /allocators/{client_id}/redemptions`   | Allocator's own redemption history   |
| `GET /allocators/{client_id}/cash-account`  | Cash-account movements + balance     |

---

# Success criteria

| Phase   | Gate    | How verified                                                                                                                                                      |
| ------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 | C4      | `cd unified-api-contracts && bash scripts/quality-gates.sh` + `cd unified-trading-library && bash scripts/quality-gates.sh` both pass                             |
| Phase 1 | C4      | `cd position-balance-monitor-service && bash scripts/quality-gates.sh` + `cd execution-service && bash scripts/quality-gates.sh` both pass; coverage ratchet held |
| Phase 2 | C4      | `cd fund-administration-service && bash scripts/quality-gates.sh` passes; coverage ≥ 70%; integration test walks full sub→red loop with mocks                     |
| Phase 3 | C4      | `cd unified-trading-system-ui && CI=true npm test -- --run` passes; Playwright e2e walks mock happy path; routes render with mock fixtures                        |
| Phase 4 | C4      | `cd client-reporting-api && bash scripts/quality-gates.sh` passes; entitlement filter test holds                                                                  |
| Phase 5 | —       | codex + briefings consistent; memory updated                                                                                                                      |
| Phase 6 | D3 + B3 | staging integration test end-to-end green; user sign-off on UX; all 7 repos at C5                                                                                 |

## B3 KPIs (domain-specific)

- Subscription approval latency (request → SUBSCRIPTION_APPROVED): P95 < 24h in staging (real POD integration later
  lowers this).
- Redemption settlement latency (grace-period expiry → REDEMPTION_SETTLED): P99 within the declared grace-period + 1
  business day.
- Capital-routing rebalance: target-allocation delta reconciled to < 0.5% of AUM within 1 rebalance cycle (monitor emits
  TREASURY_LOW when drift exceeds threshold).
- NAV strike determinism: two replays of the same FundNAVSnapshot produce identical units_issued within 8-decimal
  precision.

---

# Related plans

- `autonomous_recovery_and_transfer_architecture_2026_04_16.md` — transfer architecture; this plan reuses its
  TransferAdapter extensions.
- `position_reconciliation_and_cost_preview` — position-tracking foundation this plan relies on.
- `signal_leasing_broadcast_architecture_2026_04_20.md` — parallel commercial-path work on Odum Signals-Out.

# Follow-ups (out of scope)

- **Real POD integration**: the subscription-approval AML/KYC gate starts as a stub; real POD API integration is a
  separate plan once POD's fund-admin endpoints are confirmed.
- **Custodian onboarding matrix**: which qualified custodians map to which asset class (Copper for crypto, equivalents
  for TradFi + on-chain). Confirm with compliance + name them internally; public copy already says "qualified
  third-party custodian such as Copper".
- **DART Signals-In upstream sub-client partitioning**: covered by the multi-mandate / sub-client section in the DART
  briefing; the venue-level sub-account primitive work is a separate plan (no treasury-wallet dependency).
- **IM SMA subscription UI**: SMA clients fund their own venue accounts directly — no platform subscription rail needed.
  The `/services/im/funds/` routes are Pooled-only; SMA clients see `/services/im/accounts/` (already exists or in scope
  of a different plan).
