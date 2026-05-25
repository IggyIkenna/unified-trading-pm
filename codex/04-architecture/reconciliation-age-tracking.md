---
scope: [engineer, admin]
last_reviewed: 2026-05-23
authoritative_for: [reconciliation-age, recon-dimensions, recon-escalation, recon-freeze]
referenced_by:
  - codex/04-architecture/autonomous-recovery-matrix.md
  - codex/04-architecture/incident-gateway-state-machine.md
  - plans/active/reconciliation_age_tracking_and_escalation_2026_05_23.md
---

# Reconciliation Age Tracking, 12 Dimensions, and Escalation Ladder

> SSOT for how the system tracks reconciliation staleness, escalates by elapsed time, and freezes new trading when
> reconciliation risk is live. Codified 2026-05-23 per
> `plans/active/reconciliation_age_tracking_and_escalation_2026_05_23.md`.

## Principle

Every reconciliation breach is **age-tracked**, **dimensioned**, and **escalated by elapsed time**. Ages are persisted
at row-write-time (never computed at query time — same rule as `available_at` in the manifest). Auto-unfreeze does NOT
exist — unfreeze is HUMAN-ONLY even when recon age recovers below threshold.

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

When `recon_age_critical_seconds` breaches OR any immediate-SEV0 fires, alerting-service publishes `RECON_FREEZE_ARMED`
event to PubSub topic `reconciliation-freeze`.

`execution-service/execution_service/preflight/recon_freeze.py` (`ReconFreezeChecker`) subscribes and updates its
in-memory freeze set within 5s. New order submissions for (strategy, venue, symbol) tuples in the freeze set are
rejected with `ReconFreezeError` (shipped execution-service@d649af364).

**Unfreeze is HUMAN-ONLY**: operator clicks "Unfreeze" in DART after acknowledging the incident and verifying the recon
delta resolved. Emits `RECON_FREEZE_LIFTED` event. No auto-unfreeze — even if `oldest_unreconciled_age` drops below
threshold, trading does NOT automatically resume.

---

## Recovery-verification callback

`batch-live-reconciliation-service` registers a callback with the Incident Gateway (`recovery_verifier.py`):
`oldest_unreconciled_age_seconds < configured threshold` across all 12 dimensions. This is the `reconciliation_age` gate
within `RecoveryVerificationResult` — one of the 5 booleans needed for `RECOVERY_CONFIRMED` (see
`codex/04-architecture/incident-gateway-state-machine.md`).

---

## Continuous verification

- Daily: `python3 batch-live-reconciliation-service/scripts/check_oldest_age.py` → max(age) < 30min in healthy state.
- Per-incident: assert recon-freeze armed within 5s of SEV0 fire (synthetic test runs nightly).

---

## Related

- `04-architecture/incident-gateway-state-machine.md` — ImmediateSev0Override enum + RecoveryVerificationResult
- `04-architecture/autonomous-recovery-matrix.md` — RECONCILIATION FAILURE decision tree
- `plans/archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md` — implementation plan
