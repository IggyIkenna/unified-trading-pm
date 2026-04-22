---
name: fund-administration-service — real POD integration (crypto-only)
overview:
  Replace the fund-administration-service's mock AML/KYC gate + NAV-strike resolution with real HTTP / file-drop
  integration against POD, the regulated fund administrator for **crypto-denominated** Pooled funds. (TradFi Pooled
  funds use a separate administrator — see `tradfi_fund_administrator_selection_2026_04_22.plan.md`.)
type: mixed
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22

completion_gates:
  code: C5
  deployment: D3
  business: B3

repo_gates:
  - repo: fund-administration-service
    code: C0
    deployment: D3
  - repo: unified-api-contracts
    code: C0
    deployment: none
  - repo: unified-trading-pm
    code: C0
    deployment: none

depends_on:
  - fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md
  - fund_administration_persistence_swap_in_2026_04_22.plan.md
---

# Context

fund-administration-service Phase 2 shipped with stubbed provider interfaces:

- `AmlKycGate` — auto-approves every subscription in staging.
- `NavProvider` — returns a single hard-coded NAV snapshot.
- `SettlementExecutor` — logs withdrawal request but doesn't actually settle.

Each is a Protocol. Real POD integration means replacing the stub impls with real ones that talk to POD's API (or SFTP
file-drop if that's POD's integration mode).

**SCOPE: CRYPTO-ONLY.** POD administers crypto-denominated pooled funds — that's the first and currently only
integration. TradFi Pooled funds use a separate administrator; different plan.

# Unknowns to resolve before coding

- [ ] Does POD expose a REST API, an SFTP file-drop, or both? Confirm with compliance / POD account manager.
- [ ] What AML/KYC does POD do vs what does Odum do? Responsibility matrix for investor onboarding, refresh,
      suspicious-activity reporting.
- [ ] NAV strike cadence — daily? Weekly? Intra-day? For crypto this is usually daily; confirm.
- [ ] Subscription / redemption settlement SLA — confirm grace-period default (currently 5 days in fund-admin scaffold).
- [ ] Custodian handoff — POD coordinates with Copper on asset movement. Odum's role in that handoff is?

# Scope

## Contracts + discovery

- [ ] Obtain POD integration spec (API docs or SFTP schema). File into `codex/14-playbooks/external-integrations/pod.md`
      (internal-only).
- [ ] Add `PodClient` Protocol to fund-administration-service (not UAC — POD is internal-specific).
- [ ] Secret Manager: API key / SFTP credentials provisioned via deployment-service.

## Implementation

- [ ] `RealAmlKycGate` — calls POD for investor-level AML check.
- [ ] `RealNavProvider` — pulls NAV from POD at the published strike cadence; caches with TTL.
- [ ] `RealSettlementExecutor` — initiates the withdrawal (POD executes on custodian; fund-admin waits for confirmation
      webhook / polls SFTP).
- [ ] Webhook receiver for POD → fund-administration-service callbacks (if REST) OR SFTP poller (if file-drop).
- [ ] Circuit breaker: if POD is unreachable, subscriptions queue as PENDING rather than fail. Alerts ops.

## Tests

- [ ] Unit: each Real\* impl with `responses` library faking POD.
- [ ] Integration (staging): stub POD sandbox if POD provides one; otherwise gate behind manual-test flag.

## Commercial + compliance

- [ ] Legal agreement with POD confirmed + e-signed before production traffic.
- [ ] Compliance sign-off on AML responsibility matrix.

## Out of scope

- TradFi Pooled administrator integration — separate plan.
- IM SMA flow — doesn't touch POD (clients hold their own venue accounts).

# Commercial gate

Production rollout (D5) gated on first signed IM Pooled mandate + POD contract effective.
