---
doc_type: plan
title: Fund Administration — Redemption/NAV Cadence Engine Made Real
summary:
  Makes fund-administration-service's redemption engine actually run — GracePeriodHandler and NAVStrikeScheduler are
  both fully implemented but never wired to a real interval loop or a real DI backend, and settlement NAV is currently
  fund-level total_equity used as a per-unit-NAV stand-in. Adds hour-granularity grace periods, a real units-outstanding
  NAV-per-share, a redemption-processing fee charged against the redeemed amount only, and the acked-but-unimplemented
  treasury ledger writer.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [fund-administration-service, unified-api-contracts]
scope: [engineer]
tags: [fund-administration, redemption, nav, ledger, strategy-agnostic]
related:
  [
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
    /plans/epics/strategy_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
depends_on:
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator conversation relay (Greg/Patrick SMA-redemption chat) + interactive session slot 5, 2026-08-20
context_scope:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/04-architecture/client-funds-isolation.md,
    fund-administration-service/fund_administration_service/redemption/state_machine.py,
    fund-administration-service/fund_administration_service/background/grace_period_handler.py,
    fund-administration-service/fund_administration_service/background/nav_strike_scheduler.py,
    fund-administration-service/fund_administration_service/api/main.py,
    unified_api_contracts/internal/domain/fund_administration/_types.py,
    unified_api_contracts/internal/reporting/fee_structure.py,
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
  ]
---

# Fund Administration — Redemption/NAV Cadence Engine Made Real

**Why this doc exists**: a client wants faster, more automated redemptions (semi-instant, delay measured in hours
rather than business days) settled at a real per-unit NAV, with any redemption-processing fee charged only against the
redeemed amount — never socialized across the rest of the fund's NAV. Reading the current code found the mechanism is
already ~half-built as a scaffold: `AllocatorRedemption`'s state machine (PENDING→APPROVED→PROCESSED→SETTLED) and
`GracePeriodHandler`/`NAVStrikeScheduler` are fully implemented, but neither is ever invoked outside unit tests, the
grace period is day-granularity only, and settlement NAV is fund-level `total_equity` used directly in place of a real
per-unit NAV (flagged in the code's own comment as a scaffold gap). This plan makes that machinery real, strategy-
agnostic by construction — it lives entirely in fund-administration-service's accounting/administration layer and never
references a trading strategy or archetype.

**Resolved design** (confirmed with the operator 2026-08-20, do not re-litigate): each redemption in a cadence batch
still pays its OWN fee out of its OWN proceeds — a percentage of the redeemed amount, computed exactly the way the
existing `trader_fee_pct`/`odum_fee_pct` deduction already works — not a cost socialized across remaining NAV. What's
new is that all redemptions whose grace period expires in the same cadence tick settle against ONE shared per-unit NAV
snapshot, rather than each needing its own. Exact cadence value (operator floated 8h vs daily) and exact
redemption-fee percentage are left as tunable config defaults, not blocking design questions — see todos below.

**Companion plan**: [`redemption_wallet_transfer_execution_2026_08_20.md`](redemption_wallet_transfer_execution_2026_08_20.md)
owns the wallet-transfer-execution + per-client-isolation leg under `client_isolation_and_governance_master`; that plan
`depends_on` this one for ordering (not gated — its tests inject a real adapter directly, independent of this plan's DI
wiring).

**Why `sequential: true`**: nearly every todo below touches `grace_period_handler.py` and/or `api/main.py` — the hot
files this whole engine is scaffolded around. Same-file concurrent edits are banned by multi-agent safety, so this
plan is a serial chain by file-topology, not a reflexive default.

## Todos

- [ ] [BACKEND] P0. Add `grace_period_seconds: int | None` to UAC `AllocatorRedemption`
  (`unified_api_contracts/internal/domain/fund_administration/_types.py:125`), default `None`, alongside the existing
  `grace_period_days: int` (kept, unchanged, for backward compatibility with existing callers/tests). Update
  `create_redemption()` (`fund_administration_service/redemption/state_machine.py`) to accept an optional
  `grace_period_seconds` param. Done-when: a new pydantic round-trip test on `AllocatorRedemption` proves the field
  persists through `model_copy`.

- [ ] [BACKEND] P0. Update grace-period expiry math in `GracePeriodHandler.run_once()`
  (`fund_administration_service/background/grace_period_handler.py:81`) to prefer `grace_period_seconds` when set,
  falling back to `grace_period_days * 86400` otherwise — this is what turns "5 business days" into "a few hours"
  when a redemption is created with the new field. Done-when: a unit test creates a redemption with
  `grace_period_seconds=14400` (4h) and asserts `run_once()` processes it after 4h simulated elapsed time, not 5 days.

- [ ] [BACKEND] P0. Add `redemption_cadence_seconds: int` to `FundAdministrationServiceConfig`
  (`fund_administration_service/config.py`), default `28800` (8h, the operator's own suggested starting cadence —
  tunable via env, not a blocking decision). Implement the real wall-clock loop `GracePeriodHandler` currently lacks:
  add a `run_forever(interval_seconds: int) -> None` async method that calls `run_once()` on an `asyncio.sleep`-driven
  interval, and start it from `create_app()`'s FastAPI startup/lifespan hook (`fund_administration_service/api/main.py`).
  Done-when: an async test with a monkeypatched sleep asserts `run_once()` fires at the configured interval, not zero
  times ever (today's state).

- [ ] [BACKEND] P0. Implement the real wall-clock loop `NAVStrikeScheduler`'s own docstring describes but never ships
  (`fund_administration_service/background/nav_strike_scheduler.py:1-8`) — an `asyncio.sleep`-driven loop calling
  `tick()` every `nav_publish_cadence_seconds` (config field already exists, default 86400s), started from the same
  FastAPI startup hook as the prior todo. Done-when: equivalent interval test to the prior todo, for `tick()`.

- [ ] [BACKEND] P0. Wire `_default_container()`'s stub dependencies to real implementations
  (`fund_administration_service/api/main.py`, ~line 130): `nav_provider=_EmptyNavProvider()` and `transfer_adapter=None`
  both currently no-op in production. Locate the actual `FundNAVSnapshot` producer (per
  `unified_api_contracts/internal/domain/client_reporting/nav_snapshot.py`'s own docstring, "Odum's
  position-balance-monitor-service") and wire a real `NavProvider` reading from it; wire `transfer_adapter` to
  execution-service's `CompositeTransferAdapter` (the structural-mirror `TransferAdapter` Protocol in
  `fund_administration_service/allocation/transfer_protocol.py` already documents this as the intended production
  implementation). Done-when: `ctx.transfer_adapter is None` at `api/main.py:439` is unreachable via the real
  `_default_container()` path (mock/test containers still allowed to pass `None` explicitly).

- [ ] [BACKEND] P1. Implement the real units-outstanding divisor for per-unit NAV, replacing the placeholder in
  `GracePeriodHandler._drive_unchecked` (`grace_period_handler.py:112-114`) that reads `snapshot.nav_usd` directly as
  per-unit NAV. Add a `units_outstanding: dict[tuple[str, str], Decimal]` running ledger to `PersistenceStore`
  (`fund_administration_service/persistence/in_memory_store.py`), keyed by `(fund_id, share_class)`, incremented when a
  subscription reaches `PROCESSED` and decremented when a redemption reaches `PROCESSED`; compute
  `settlement_nav = snapshot.nav_usd / units_outstanding[(fund_id, share_class)]`. Done-when: a test proves NAV-per-unit
  changes correctly across a subscribe-then-redeem sequence and is never equal to raw `nav_usd` once units outstanding
  != 1.

- [ ] [BACKEND] P1. Add `redemption_fee_pct: Decimal` to UAC `FeeStructure`
  (`unified_api_contracts/internal/reporting/fee_structure.py`), default `Decimal("0")`. Deduct it in
  `process_redemption()` (`fund_administration_service/redemption/state_machine.py:99-102`) alongside the existing
  `trader_fee_pct`/`odum_fee_pct` — same computation shape (`gross_usd * total_fee_pct`), added into the existing
  `total_fee_pct` sum, still deducted only from that redemption's own `cash_amount_due_usd`. This is the "fast
  withdrawal fee" from the operator conversation — confirmed 2026-08-20 to be a ratio of the redeemed amount, never
  fund-wide. Done-when: existing `tests/unit/test_redemption_state_machine.py` stays green, plus a new case asserting
  a nonzero `redemption_fee_pct` reduces `cash_amount_due_usd` proportionally with zero effect on other redemptions'
  fee math.

- [ ] [BACKEND] P1. Strike ONE `FundNAVSnapshot` per `(fund_id, share_class)` per cadence tick and reuse it across every
  redemption settled in that tick, instead of `run_once()`'s current per-redemption `nav_provider.latest_snapshot()`
  call (`grace_period_handler.py:106`) — this is what makes "all outstanding withdrawals processed on one cadence,
  same NAV strike" real rather than incidental. Done-when: a test with 2 pending redemptions for the same fund/share
  class in one `run_once()` call asserts both settle against the identical `snapshot_id`.

- [ ] [BACKEND] P2. Implement the acked-but-unimplemented `ledger_type=treasury/client_id={cid}/` writer
  (confirmed zero code hits fleet-wide as of `strategy_master.md`'s 2026-08-18 fold-in note) — record each redemption's
  cash movement as a canonical UAC `LedgerRow` at the point `_persist_processed`/`_persist_settled`
  (`grace_period_handler.py:138-180`) already emit their fund-admin events, so accounting has a real source for
  redemption cash flows. Done-when: processing one redemption in a test produces a `ledger_type=treasury` row
  queryable by `client_id`.

- [ ] [REVIEW] P2. Confirm no regression: run `fund-administration-service`'s full test suite
  (`bash scripts/quality-gates.sh`) after all prior todos land and cite the green run. Done-when: QG passes with the
  new interval loops, schema fields, fee field, and ledger writer all exercised by tests (not just present).

## Progress Log

- **2026-08-20**: Plan authored following `/plan-brainstorm` — operator confirmed (a) redemption-processing fee is
  ratio-of-redeemed-amount, not fund-wide-socialized, and (b) the epic split (this plan under `strategy_master`,
  wallet-transfer-execution under `client_isolation_and_governance_master`). Original proposal named
  `global_ledger_pnl_attribution_master` as parent — corrected in-session: that epic is `status: superseded`, folded
  into `strategy_master` 2026-08-18, which already carries the same acked treasury-ledger-gap finding this plan
  resolves.
