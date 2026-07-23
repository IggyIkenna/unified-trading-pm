---
doc_type: codex-ssot
title: Reconciliation Age Tracking, 12 Dimensions, and Escalation Ladder
summary:
  SSOT for live reconciliation staleness — the 12 ReconciliationDimensions, ReconciliationAgeFields (all ages written at
  row-write-time, never query-time), the 3-band escalation ladder (warn 5min / investigate 15min / critical 30min) plus
  7 immediate-SEV0 overrides, and HUMAN-ONLY unfreeze. Live recon is distributed across strategy-service/position +
  execution-service + alerting-service (NOT BLRS, which is T+1 batch-only); RECON_FREEZE_ARMED is still unwired.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, batch-live-reconciliation-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [reconciliation, escalation, monitoring, execution, data-correctness, kill-switch]
related:
  [
    /codex/04-architecture/reconciliation-resolution.md,
    /codex/04-architecture/incident-gateway-state-machine.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-05-25
authoritative_for: [reconciliation-age, recon-dimensions, recon-escalation, recon-freeze]
referenced_by:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/incident-gateway-state-machine.md,
    plans/active/reconciliation_age_tracking_and_escalation_2026_05_23.md,
  ]
owner:
last_reviewed: 2026-05-27
code_refs:
---

> **OWNERSHIP CORRECTED 2026-05-27 (BLRS audit D1, decision A —
> `plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md`)**: earlier revisions of this doc
> attributed live continuous reconciliation (the recovery-verification callback + a daily `check_oldest_age.py`) to
> `batch-live-reconciliation-service`. **That is wrong.** BLRS is a **T+1 batch auditor only** — it does NOT perform
> live reconciliation, owns no recovery callback, and ships no age script. Live reconciliation is implemented by the
> three repos in § "Component ownership" below.

# Reconciliation Age Tracking, 12 Dimensions, and Escalation Ladder

> SSOT for how the system tracks reconciliation staleness, escalates by elapsed time, and freezes new trading when
> reconciliation risk is live. Codified 2026-05-23 per
> `plans/active/reconciliation_age_tracking_and_escalation_2026_05_23.md`.

## Principle

Every reconciliation breach is **age-tracked**, **dimensioned**, and **escalated by elapsed time**. Ages are persisted
at row-write-time (never computed at query time — same rule as `available_at` in the manifest). Auto-unfreeze does NOT
exist — unfreeze is HUMAN-ONLY even when recon age recovers below threshold.

---

## Component ownership (who implements what)

Live reconciliation is **distributed**, not owned by a single service. `batch-live-reconciliation-service` is NOT in
this list — it is a separate T+1 batch auditor (see `reconciliation-resolution.md`).

| Concern                                                                       | Owner repo / module                                                                                                                                                                          | Status                                                                                         |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Live venue↔internal position/balance recon + age fields + deviation lifecycle | `strategy-service/strategy_service/position/` (merged PBMS): `core/reconciliation_engine.py`, `core/fee_reconciliation_engine.py`, `core/position_drift_monitor.py`, `v2/recon_freshness.py` | Built; only `POSITIONS` + `FEES` of the 12 dimensions are populated today (other 10 spec-only) |
| Live venue accrual / funding recon                                            | `execution-service`: `services/yield_recon_engine.py`, `services/funding_recon_engine.py`, `services/account_history_client.py`                                                              | Built                                                                                          |
| Escalation ladder + 7 immediate-SEV0 overrides                                | `alerting-service`: `rules/reconciliation_rules.py` (`evaluate_recon_age`, `evaluate_immediate_sev0`)                                                                                        | Built                                                                                          |
| `RECON_FREEZE_ARMED` publisher                                                | `alerting-service` (per § "Reconciliation Freeze")                                                                                                                                           | ⚠️ **NOT WIRED** — no code publishes the event; freeze chain is dormant (BLRS audit G12)       |
| Recon-freeze order-block subscriber                                           | `execution-service`: `preflight/recon_freeze.py` (`ReconFreezeChecker`)                                                                                                                      | Built (but never armed — see above)                                                            |
| Recovery-verification aggregator                                              | `alerting-service`: `gateway/recovery_verifier.py`                                                                                                                                           | Built; generic 5-boolean DR gate (see § "Recovery-verification callback")                      |
| T+1 batch audit (batch↔live↔paper)                                            | `batch-live-reconciliation-service`                                                                                                                                                          | Separate concern; NOT live recon                                                               |

---

## 12 Reconciliation Dimensions

`ReconciliationDimension` StrEnum (12 members, closed set) in `unified_api_contracts/internal/reconciliation.py`
(shipped unified-api-contracts@ae5771e2):

| Dimension                   | What it tracks                                             |
| --------------------------- | ---------------------------------------------------------- |
| `ORDERS`                    | Open orders: internal vs venue REST                        |
| `FILLS`                     | Fill events: internal vs venue trade history               |
| `POSITIONS`                 | Net positions: internal vs venue position query            |
| `BALANCES`                  | Account balances: internal vs venue balance query          |
| `FUNDING_PAYMENTS`          | Funding: internal accrual vs venue payment history         |
| `FEES`                      | Fees charged: internal vs venue fee statements             |
| `TRANSFERS`                 | Deposits/withdrawals: internal vs venue transfer history   |
| `BORROW_LENDING_BALANCES`   | Borrow/lend amounts: internal vs DeFi protocol state       |
| `COLLATERAL_BALANCES`       | Collateral posted: internal vs venue/protocol              |
| `MARGIN_MODE_AND_LEVERAGE`  | Margin mode + leverage setting: internal config vs venue   |
| `STRATEGY_LEVEL_ALLOCATION` | Strategy-level position allocation vs executed fills       |
| `ACCOUNT_LEVEL_AGGREGATE`   | Cross-strategy aggregate: total internal exposure vs venue |

---

## Age Fields (ReconciliationAgeFields mixin)

Applied to all reconciliation row models (shipped unified-api-contracts@ae5771e2):

| Field                                      | Type              | Meaning                                          |
| ------------------------------------------ | ----------------- | ------------------------------------------------ |
| `first_seen_at`                            | datetime (tz=UTC) | When this deviation was first observed           |
| `last_seen_at`                             | datetime (tz=UTC) | When it was last observed / refreshed            |
| `event_time`                               | datetime (tz=UTC) | Source event timestamp                           |
| `venue_trade_time`                         | datetime (tz=UTC) | Venue-side trade/fill timestamp                  |
| `internal_trade_time`                      | datetime (tz=UTC) | Internal system timestamp for the same event     |
| `last_successful_reconciliation_at`        | datetime (tz=UTC) | When this dimension last fully reconciled        |
| `unreconciled_age_seconds`                 | float             | now - first_seen_at at row-write-time            |
| `oldest_unreconciled_trade_age_seconds`    | float             | Age of the oldest unreconciled trade event       |
| `oldest_unreconciled_order_age_seconds`    | float             | Age of the oldest unreconciled order event       |
| `oldest_unreconciled_position_age_seconds` | float             | Age of the oldest unreconciled position snapshot |

**All ages are computed at row-write-time** using UTL `utc_now()` — never naive datetime, never query-time computation.

---

## Escalation Ladder (3 bands)

Thresholds in UAC `ALERT_THRESHOLDS` registry (shipped alerting-service@9c47947):

| Band        | Threshold                                      | Action                                             |
| ----------- | ---------------------------------------------- | -------------------------------------------------- |
| Warn        | `recon_age_warn_seconds = 300` (5 min)         | Internal log + Slack warning + agent investigation |
| Investigate | `recon_age_investigate_seconds = 900` (15 min) | SEV1 (human investigation required)                |
| Critical    | `recon_age_critical_seconds = 1800` (30 min)   | SEV0 + recon freeze armed                          |

Per-venue / per-strategy / per-instrument-type / per-account overrides supported via UAC `per_archetype_overrides`
matching the existing `AlertThreshold` pattern.

---

## 7 Immediate-SEV0 Overrides

These bypass the age-band ladder entirely. ANY True predicate fires SEV0 immediately.

`evaluate_immediate_sev0(row)` in `alerting-service/alerting_service/rules/reconciliation_rules.py` (shipped
alerting-service@9c47947). 7 unit tests in `tests/unit/rules/test_immediate_sev0_overrides.py`.

Uses `ImmediateSev0Override` StrEnum (UAC `unified_api_contracts/canonical/crosscutting/incident/state.py`):

| Override                                        | Condition                                                                   |
| ----------------------------------------------- | --------------------------------------------------------------------------- |
| `UNKNOWN_NET_EXPOSURE`                          | Venue total ≠ internal total + no explanation row in transfers/funding      |
| `OPEN_ORDERS_UNCONFIRMABLE`                     | Venue REST returns 5xx + we have N open orders in internal                  |
| `KILL_SWITCH_CANNOT_CONFIRM_CANCEL`             | kill_switch.activate() ran but cancel-all-orders returned partial           |
| `VENUE_INTERNAL_BALANCE_MISMATCH`               | abs(venue - internal) > USD threshold (configurable per asset, default $1k) |
| `POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY` | Venue returns position we have no internal record of                        |
| `MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED`         | Balance moved > USD threshold + no transfer/fill/funding row                |
| `MARGIN_COLLATERAL_SAFETY_UNCERTAIN`            | Venue API can't confirm margin state OR ADL/insurance-fund signal           |

---

## Reconciliation Freeze

When `recon_age_critical_seconds` breaches OR any immediate-SEV0 fires, alerting-service is to publish
`RECON_FREEZE_ARMED` to PubSub topic `reconciliation-freeze`.

> ⚠️ **NOT WIRED (BLRS audit G12, 2026-05-27)**: no code in alerting-service (or anywhere) actually publishes
> `RECON_FREEZE_ARMED`. Critical recon-age + the 7 immediate-SEV0 overrides currently route to PagerDuty/Telegram
> **alerts only** — they never arm the freeze, so the order-block below never engages. The independent
> `position_drift_monitor` (strategy-service/position) does fire `KILL_SWITCH_ACTIVATED` on CRITICAL drift, so there is
> a live reflex, but the recon-freeze chain is dormant. Tracked as its own issue.

`execution-service/execution_service/preflight/recon_freeze.py` (`ReconFreezeChecker`) subscribes and updates its
in-memory freeze set within 5s (once a publisher exists). New order submissions for (strategy, venue, symbol) tuples in
the freeze set are rejected with `ReconFreezeError` (shipped execution-service@d649af364).

**Unfreeze is HUMAN-ONLY**: operator clicks "Unfreeze" in DART after acknowledging the incident and verifying the recon
delta resolved. Emits `RECON_FREEZE_LIFTED` event. No auto-unfreeze — even if `oldest_unreconciled_age` drops below
threshold, trading does NOT automatically resume.

---

## Recovery-verification callback

The recovery verifier is `alerting-service/alerting_service/gateway/recovery_verifier.py` — a per-service callback
aggregator that produces a 5-boolean `RecoveryVerificationResult` (`health_checks_passed`, `positions_reconciled`,
`orders_reconciled`, `market_data_fresh`, `strategy_state_restored`); all 5 must be True for `RECOVERY_CONFIRMED` (see
`/codex/04-architecture/incident-gateway-state-machine.md`). The recon-relevant booleans are `positions_reconciled` +
`orders_reconciled`.

> **CORRECTION (BLRS audit D1, 2026-05-27)**: there is **no** `reconciliation_age`-specific gate in the result today,
> and **no** service (BLRS or otherwise) registers a "12-dimension `oldest_unreconciled_age` < threshold" callback. The
> verifier neither references nor depends on `batch-live-reconciliation-service`. If a per-dimension recon-age recovery
> gate is wanted, it should be registered by the **live-recon owner** (`strategy-service/position`, which holds the age
> fields), not BLRS.

---

## Continuous verification

- Live age/freshness signal is produced by **strategy-service/position**: `unreconciled_age_seconds` is written at
  row-creation time on reconciliation rows (`core/reconciliation_engine.py`, `core/fee_reconciliation_engine.py`) and
  surfaced via the `v2/recon_freshness.py` feed (consumed by risk-service pre-flight).
- A standalone daily "max(age) < 30min" check script is **NOT YET BUILT** (the previously-referenced
  `batch-live-reconciliation-service/scripts/check_oldest_age.py` never existed; BLRS audit G7). If added, it belongs
  with the live-recon owner (`strategy-service/position`), not BLRS.
- Per-incident: assert recon-freeze armed within 5s of SEV0 fire — blocked until the `RECON_FREEZE_ARMED` publisher is
  wired (see § "Reconciliation Freeze" ⚠️ / BLRS audit G12).

---

## Related

- `04-architecture/incident-gateway-state-machine.md` — ImmediateSev0Override enum + RecoveryVerificationResult
- `04-architecture/autonomous-recovery-matrix.md` — RECONCILIATION FAILURE decision tree
- `plans/archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md` — implementation plan
