---
doc_type: codex-ssot
title: Client Lifecycle State Machine
summary:
  Client onboarding state machine (DRAFT→KYC_SUBMITTED→KYC_APPROVED→DEPOSITED→SUBSCRIBED→LIVE, SUSPENDED terminal) with
  per-transition evidence + idempotency; UTL ClientOnboardingStateMachine persisted to GCS; May-23 MVP is manual
  single-client with no production KYC provider.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [client-lifecycle, onboarding, kyc, state-machine, mvp, gcs]
related: [/codex/04-architecture/client-lifecycle-event-bus.md, /codex/04-architecture/client-funds-isolation.md]
created: 2026-05-13
authoritative_for: [client onboarding state machine and lifecycle states]
referenced_by:
  [/codex/04-architecture/capital-efficiency-patterns.md, /codex/04-architecture/client-lifecycle-event-bus.md]
owner:
last_reviewed: 2026-10-05
code_refs:
---

# Client Lifecycle State Machine

## Purpose

The client lifecycle state machine governs onboarding, funding, and activation of a client before they can participate
in live trading. It ensures a client's KYC, deposit, and subscription state are formally verified before capital is
allocated to archetypes.

**Cutover MVP scope (May-23):** a single demo client is walked through all states manually as a dry-run gate
(`wallet_treasury_client_flow_2026_05_10.md` Phase 7.A). The state machine is implemented in UTL
`ClientOnboardingStateMachine` and persists to GCS; no production KYC provider is wired for May-23.

**Deferred:** multi-client concurrent onboarding, production KYC provider integration (Onfido / Jumio), automated
state-progression webhooks. These items are post-cutover and tracked in
[`/plans/archive/wallet_treasury_post_cutover_custody_signing_2026_06_01.md`](/plans/archive/wallet_treasury_post_cutover_custody_signing_2026_06_01.md).

> **[DELTA 2026-05-22]** **Current state:** MVP ships with manual single-client DRAFT→LIVE walkthrough; no production
> KYC provider wired; SUSPENDED is terminal (no automated re-activation). **Planned delta:** Post-cutover items tracked
> in [`/plans/archive/wallet_treasury_post_cutover_custody_signing_2026_06_01.md`](/plans/archive/wallet_treasury_post_cutover_custody_signing_2026_06_01.md): production Onfido/Jumio KYC wiring, multi-client
> concurrent onboarding, automated state-progression webhooks, SUSPENDED recovery path. **Target architecture:**
> `ClientOnboardingStateMachine` accepts KYC provider webhooks, auto-advances on approval, and supports
> operator-initiated SUSPENDED → re-onboarding flow.

---

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> DRAFT : client record created
    DRAFT --> KYC_SUBMITTED : operator submits KYC stub
    KYC_SUBMITTED --> KYC_APPROVED : approval recorded (approved_at + approval_notes)
    KYC_APPROVED --> DEPOSITED : deposit txid confirmed
    DEPOSITED --> SUBSCRIBED : ≥1 ClientShareClassSubscription added
    SUBSCRIBED --> LIVE : operator advances (no evidence)
    LIVE --> SUSPENDED : suspension_reason provided
    KYC_SUBMITTED --> SUSPENDED : suspension_reason provided
    KYC_APPROVED --> SUSPENDED : suspension_reason provided
    DEPOSITED --> SUSPENDED : suspension_reason provided
    SUBSCRIBED --> SUSPENDED : suspension_reason provided
    SUSPENDED --> [*] : terminal (no automatic recovery; requires operator action)
```

> **SUSPENDED is a terminal state** in the MVP. Recovery requires an operator to create a new client record.
> Re-activation path is deferred post-cutover.

---

## Per-Transition Evidence Requirements

| Transition                     | Required evidence fields                                       | Notes                                                     |
| ------------------------------ | -------------------------------------------------------------- | --------------------------------------------------------- |
| `[*] → DRAFT`                  | `client_id`, `client_name`, `created_at`                       | Record initialised by operator or seed script             |
| `DRAFT → KYC_SUBMITTED`        | none beyond state change                                       | KYC stub payload (`ClientKYCStub`) attached separately    |
| `KYC_SUBMITTED → KYC_APPROVED` | `approved_at: datetime`, `approval_notes: str`                 | Both fields mandatory; blank `approval_notes` rejected    |
| `KYC_APPROVED → DEPOSITED`     | `deposit_txid: str`                                            | On-chain txid or custodian reference; verified externally |
| `DEPOSITED → SUBSCRIBED`       | at least one `ClientShareClassSubscription` present for client | Machine validates presence before advancing               |
| `SUBSCRIBED → LIVE`            | none beyond state change                                       | Final operator gate confirming readiness                  |
| `Any → SUSPENDED`              | `suspension_reason: str`                                       | Non-blank; included in audit log entry                    |

The `ClientOnboardingStateMachine.advance(...)` method validates the evidence dict against these requirements before
writing. Missing required fields raise **`InvalidStateTransitionError`** (fail-loud; no silent defaults).

> **Corrected 2026-07-31.** The implementation defines exactly **one** exception type,
> `InvalidStateTransitionError(ValueError)` in
> `unified-trading-library/unified_trading_library/client_lifecycle/onboarding.py`. Earlier revisions of this doc named
> three separate errors (`MissingTransitionEvidenceError`, `IllegalStateRegressionError`, `IllegalStateSkipError`) and
> two sub-validators (`assert_kyc_evidence`, `assert_deposit_evidence`) — **none of these exist in any repo**. All three
> failure modes (missing evidence, regression, state-skip) raise the same `InvalidStateTransitionError`.

---

## Idempotency Contract

Advancing a client to its **current state** is a **no-op**: the method returns the existing state record unchanged and
does **not** append a duplicate audit log entry. This allows retry-safe callers.

Advancing to a state **already in the past** (regression) raises `InvalidStateTransitionError`. There is no rollback
path — state only moves forward (or to SUSPENDED).

---

## Storage Layout

State is persisted to GCS at:

```
gs://{pid}-client-state/{client_id}/onboarding.json
```

`{pid}` resolves via `resolve_bucket_name(cloud="gcp", kind="client_state", env=DEPLOYMENT_ENV)` — never an inline
f-string (QG STEP 5.69 ratchet). The `onboarding.json` schema:

```json
{
  "client_id": "...",
  "state": "LIVE",
  "history": [
    {
      "from_state": "SUBSCRIBED",
      "to_state": "LIVE",
      "transitioned_at": "2026-05-13T10:00:00Z",
      "evidence": {}
    }
  ]
}
```

`history` is append-only; earlier entries are never modified. The write uses GCS CAS (precondition on object generation)
to guard concurrent writers — see manifest concurrency principle in CLAUDE.md.

---

## Cross-References

### UAC types

All five live in `unified_api_contracts/internal/domain/client_lifecycle.py` (field lists verified 2026-07-31 — there
is **no** `unified_api_contracts.canonical.domain.client` module; that path in earlier revisions was wrong):

- `ClientOnboardingState` — 7-value enum (`DRAFT` / `KYC_SUBMITTED` / `KYC_APPROVED` / `DEPOSITED` / `SUBSCRIBED` /
  `LIVE` / `SUSPENDED`) — matches the diagram above exactly
- `ClientKYCStub` — KYC payload attached at `KYC_SUBMITTED`; fields: `client_name`, `client_email`, `jurisdiction`,
  `accredited_investor_claimed`, `submitted_at`, `approved_at`, `approval_notes`. (There is **no** `full_name` field —
  it is `client_name` — and **no** `kyc_provider` field; the MVP has no provider axis at all.)
- `ClientApiKeyMaterial` — API key credentials issued post-`LIVE`; fields: `api_key_id`, `label`, `created_at`,
  `expires_at`, `scopes`. Secret material itself lives in Secret Manager, not this record.
- `ClientRiskPreferences` — per-client risk limits; fields: `max_leverage`, `max_single_leg_usd`, `max_daily_loss_pct`,
  `max_drawdown_pct`, `liquidation_threshold_pct`, `preferred_currencies`
- `ClientShareClassSubscription` — required pre-`SUBSCRIBED`; fields: `client_id`, `share_class_id`, **`archetype_id`**,
  `allocation_pct`, `max_drawdown_for_suspension_pct`, `subscribed_at`, `suspended_at`, `suspension_reason`. (There is
  **no** `status` enum field — suspension is expressed by `suspended_at` + `suspension_reason` being set.)

### UTL

- `ClientOnboardingStateMachine` — shipped at UTL@b87daf02 + UTL@a93f78be (both SHAs verified present in UTL history);
  lives in `unified_trading_library/client_lifecycle/onboarding.py`; implements `advance` + idempotency + evidence
  validation + GCS read/write. It does **not** expose `assert_kyc_evidence` / `assert_deposit_evidence` sub-validators —
  validation is inline in `advance`.

### Plans (all archived — records, not live tracking)

- [`/plans/archive/wallet_treasury_client_flow_2026_05_10.md`](/plans/archive/wallet_treasury_client_flow_2026_05_10.md)
  Phase 1 (UAC types + GCS layout), Phase 2.A (`ClientOnboardingStateMachine` UTL implementation), Phase 7.A (demo
  client seed walkthrough DRAFT → LIVE — see `client-reporting-api/scripts/seed_demo_client.py`)

---

## Anti-Patterns

- **Never skip states.** `DRAFT → DEPOSITED` in a single call is rejected by `InvalidStateTransitionError`. All
  intermediate states must be explicitly advanced through.
- **Never inline KYC PII in the audit log.** `history[].evidence` must contain references, not raw PII fields (passport
  numbers, SSN). Full KYC payload stored separately in a KYC-scoped bucket with tighter IAM. (Earlier revisions named a
  `kyc_document_ref` field as the reference carrier; no such field exists — the rule is the convention, not a schema.)
- **Never persist state in service memory.** The GCS file is the authoritative store. Services re-read on each
  `advance()` call; no in-process cache of `ClientOnboardingState`.
- **Never advance from SUSPENDED.** SUSPENDED is terminal in the MVP — attempts raise `InvalidStateTransitionError`.
