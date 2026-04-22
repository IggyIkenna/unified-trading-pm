---
name: fund-administration-service — SQL / Firestore persistence swap-in
overview:
  fund-administration-service currently uses an in-memory `PersistenceStore` for local dev + initial staging. Ship a
  durable persistence backend (SQL or Firestore) so subscription / redemption / allocation state survives restarts and
  scales horizontally. Keep the Protocol seam so in-memory stays available for tests.
type: code
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22

completion_gates:
  code: C5
  deployment: D3
  business: B1

repo_gates:
  - repo: fund-administration-service
    code: C0
    deployment: D3
  - repo: unified-api-contracts
    code: C0
    deployment: none
  - repo: deployment-service
    code: C0
    deployment: D3

depends_on:
  - fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md
---

# Context

`fund_administration_service/persistence/in_memory_store.py` implements the `PersistenceStore` Protocol with in-process
dicts. Good for local dev + unit tests, inappropriate for staging / production.

# Backend choice

Decide between Firestore vs SQL (likely Postgres) first:

- **Firestore** — matches the codebase convention for event-sourced / document-shaped state (unified-trading-library has
  a Firestore client). Better fit for allocator-facing read paths; weaker for aggregate rebalance queries.
- **SQL (Cloud SQL / AlloyDB Postgres)** — stronger for the allocation-rebalance aggregation query; requires schema
  migrations. Matches the pattern used by `position-balance-monitor-service` or similar.

Decision: pick one based on ops preference + existing infra skew. Default recommendation: **Firestore** to stay
consistent with the rest of the SaaS tier.

# Scope

## Schema + contracts

- [ ] If Firestore: document collections schema (subscriptions, redemptions, allocations, cash-account-ledger).
- [ ] If SQL: Alembic migration for the 4 tables + indexes.
- [ ] Contract doesn't change — UAC types already define the shape.

## Implementation

- [ ] Add `FirestorePersistenceStore` (or `SqlPersistenceStore`) impl satisfying the existing `PersistenceStore`
      Protocol.
- [ ] Wire via `ServiceBootstrap` config — `PERSISTENCE_BACKEND` env var picks impl (default `memory`, staging/prod
      `firestore`).
- [ ] Migration story from in-memory: irrelevant since in-memory doesn't persist across restarts.

## Tests

- [ ] Unit tests against the new impl using the Firestore emulator / in-memory Postgres.
- [ ] Integration test in staging: subscription → approve → settle → restart service → read subscription history.

## Deployment

- [ ] Cloud SQL instance OR Firestore database provisioned in staging GCP project via deployment-service terraform.
- [ ] IAM: fund-administration-service service account gets read/write on the persistence resource.
- [ ] Cloud Run service definition updated with DB connection config / Firestore emulator fallback for local.

## Out of scope

- Audit log: lifecycle events still emit via UTL `log_event` — the persistence store is state snapshot, not event log.
  Follow-up plan needed if we want to back-fill an event store.
- Read replicas / perf tuning — do later if throughput warrants.
