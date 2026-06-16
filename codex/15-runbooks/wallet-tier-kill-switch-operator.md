---
scope: [engineer, admin]
title: Wallet-Tier Kill-Switch — Operator Runbook
type: runbook
status: active
created: 2026-05-14
source_finding: R-16 (codex_audit_risk_2026_05_12.md)
locked_by: live-defi-rollout
execution:
  owner: on-call operator (Ikenna / Harsh by rotation)
  cadence: on-demand (incident response) + quarterly DR drill
  verifier: slot-1 orchestrator reviews audit log within 24h of any arm event
  last_executed: never (first arm expected post-cutover 2026-05)
---

# Wallet-Tier Kill-Switch — Operator Runbook

> **Source**: R-16 finding from `codex_audit_risk_2026_05_12.md`. Shipped as part of
> `alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` Group A.

## When to use this runbook

Arm a wallet-tier kill switch when you need to halt live trading at a granularity **below** `KILL_ALL_LIVE`:

- A specific hot wallet shows unexpected on-chain activity or balance drift
- A single archetype is misbehaving but other archetypes are healthy
- A specific venue adapter is producing bad fills but the DeFi/CeFi split is still valid

Do NOT use wallet-tier kill switches as a first response to a global outage — reach for `KILL_ALL_LIVE`
(`OPERATOR_MANUAL`) first, then narrow the scope once you have signal.

---

## Decision tree — which kill switch to arm

```
Is the problem isolated to ONE wallet address?
  YES → KILL_PER_WALLET (most surgical)
  NO  ↓

Is the problem isolated to ONE strategy archetype?
  YES → KILL_PER_ARCHETYPE (e.g. carry_staked_basis only)
  NO  ↓

Is the problem isolated to ONE venue?
  YES → KILL_PER_VENUE (e.g. all Hyperliquid positions)
  NO  ↓

Arm KILL_ALL_LIVE (see kill-switch-event-bus.md for full procedure)
```

### Scope definitions

| Kill switch          | Scope halted                           | Remaining active                        |
| -------------------- | -------------------------------------- | --------------------------------------- |
| `KILL_PER_WALLET`    | All instructions touching `wallet_id`  | All other wallets + archetypes + venues |
| `KILL_PER_ARCHETYPE` | All instructions for `archetype_id`    | All other archetypes (same venues)      |
| `KILL_PER_VENUE`     | All instructions routing to `venue_id` | All other venues (same archetypes)      |
| `KILL_ALL_LIVE`      | Everything                             | Nothing                                 |

---

## How to arm (DART operator UI)

1. Open DART → **Execution** tab → **Kill Switch** panel.
2. Select the kill-switch tier from the dropdown.
3. For `KILL_PER_WALLET`: enter the `wallet_id` (e.g. `csb-eth-hot-lido-v1`). For `KILL_PER_ARCHETYPE`: enter the
   `archetype_id` (e.g. `carry_staked_basis`). For `KILL_PER_VENUE`: enter the `venue_id` (e.g. `hyperliquid`).
4. Enter a short reason (min 10 chars) in the **Reason** field. This is written to the audit log.
5. Click **Arm**. A confirmation modal shows the scope and estimated position impact. Click **Confirm arm**.
6. Watch the **Kill-switch status** tile update to `ARMED` within 5s.
7. Verify open positions for the halted scope are flat or in cancel-pending state in the **Positions** tile.

### CLI alternative (if DART UI is unavailable)

```bash
# Arm KILL_PER_WALLET for a specific wallet
deployment-service/scripts/kill-switch/arm.sh \
  --scope KILL_PER_WALLET \
  --id csb-eth-hot-lido-v1 \
  --reason "Unexpected balance drift on hot wallet — operator manual arm" \
  --operator "$OPERATOR_ID"

# Arm KILL_PER_ARCHETYPE
deployment-service/scripts/kill-switch/arm.sh \
  --scope KILL_PER_ARCHETYPE \
  --id carry_staked_basis \
  --reason "Carry basis inverted — pausing archetype pending config fix" \
  --operator "$OPERATOR_ID"
```

---

## Rollback procedure

1. Confirm the root cause is resolved (balance reconciled / venue adapter patched / archetype config updated).
2. In DART → Kill Switch panel, click **Disarm** for the active scope.
3. Confirm the disarm by entering your operator ID in the modal.
4. Watch positions resume on the next strategy heartbeat (≤30s).
5. Monitor PnL attribution tile for 5 minutes post-disarm to verify no stale fills re-entering.
6. Append resolution note to the audit log entry (DART → Audit → filter by kill-switch events → **Add note**).

---

## Audit-log signature

Every arm and disarm writes a structured audit entry. Verify it landed:

```json
{
  "event_type": "KILL_SWITCH_ARMED",
  "kill_switch_id": "KILL_PER_WALLET",
  "scope_value": "csb-eth-hot-lido-v1",
  "provenance": "OPERATOR_MANUAL",
  "requested_by": "<operator_id>",
  "reason": "<operator-supplied reason>",
  "armed_at_utc": "<ISO-8601 timestamp>",
  "audit_serial": "<monotonic int — verify against previous serial>"
}
```

**Verify** via: DART → Audit → filter `event_type=KILL_SWITCH_ARMED` OR query BQ table
`unified_trading.kill_switch_audit` with `WHERE armed_at_utc > '<event time>'`.

Missing audit entry after arm → escalate immediately; the arm may not have propagated to all execution shards.

---

## Open positions at arm time

When a wallet-tier kill switch arms, in-flight instructions are handled as follows:

- Instructions in `PENDING` state → cancelled immediately.
- Instructions in `SUBMITTED` state → cancel-request sent to venue adapter; may take up to 10s for venue ACK.
- Instructions in `FILLED` state → already executed; no action taken (manage manually).

Check the **Pending Orders** tile in DART immediately after arming to confirm cancel-pending orders are draining.

---

## Related docs

- `codex/04-architecture/kill-switch-event-bus.md` — event schema + provenance gating
- `codex/04-architecture/custody-providers.md` — wallet provisioning
- `codex/15-runbooks/smoke-testing-playbook.md` — post-disarm smoke test procedure
