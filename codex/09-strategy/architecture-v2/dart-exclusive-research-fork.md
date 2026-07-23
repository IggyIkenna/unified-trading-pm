---
doc_type: codex-ssot
title: DART Exclusive Subscription + Research Fork + Version Lineage
summary:
  Design SSOT for DART exclusive subscriptions + client research fork — the exclusive-lock invariant (one active
  dart_exclusive per instance_id), the 5-state fork version lifecycle (draft→pending_approval→approved→rolled_out), the
  joint Odum-client approval gate enforced at backtest_1yr, and the approval SLA.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, dart, escalation, uac, reconciliation, verification]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/performance-overlay.md,
    /codex/09-strategy/architecture-v2/dart-tab-structure.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
  ]
created: 2026-04-21
authoritative_for: [DART exclusive subscription + client research-fork version governance]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/dart-tab-structure.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
    /codex/14-customer-journeys/shared-core/strategy-version-governance.md,
  ]
owner:
last_reviewed:
code_refs:
---

# DART Exclusive Subscription + Research Fork + Version Lineage

> **Status:** design (2026-04-21) **Owner:** Strategy Architecture v2 **Plan:**
> [`plans/archive/dart_exclusive_subscription_research_fork_2026_04_21.plan.md`](../../../plans/archive/dart_exclusive_subscription_research_fork_2026_04_21.plan.md)
> **Depends on:** [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) ·
> [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) · [`performance-overlay.md`](./performance-overlay.md)
> · [`dart-tab-structure.md`](./dart-tab-structure.md) · [`dashboard-services-grid.md`](./dashboard-services-grid.md)
> **SSOT (implementation):** `unified_api_contracts.internal.domain.strategy_service.subscription` +
> `unified_api_contracts.internal.domain.strategy_service.versions`; UTA `routers/strategy_instances.py` +
> `routers/strategy_versions.py`; strategy-service `version_governance/` module.

This document is the design spec. The plan above owns the rollout checklist. Implementation SSOT is the code. When any
three drift, the code wins; next re-read updates the other two.

---

## §1 Rationale

DART is Odum's primary hosted-alpha offering: a full Data-Analytics-Research-Trading surface where the client runs
Odum-owned strategies on their capital. Historically a DART client was a _consumer_ of the strategy catalogue — they
subscribed, we ran the strategy, they saw their P&L. The 2026-04-21 product decision elevates them to **joint
governance** of the strategy configuration:

1. **Exclusive ownership.** When a DART client subscribes to a strategy instance, that instance is locked to them for
   DART purposes. No other DART client can subscribe to the same instance concurrently. The exclusivity is the
   commercial value — the client knows the alpha is theirs, not diluted across every DART subscriber on the platform. IM
   allocations are untouched because IM is pooled-by-design (every IM client shares the same underlying strategy runs);
   signals-in subscribers also coexist because they consume signal feeds rather than owning strategy config.

2. **Client-authored research.** A subscribed DART client can open the strategy in Research, modify its configuration
   (entry thresholds, risk limits, confirmer chains, ML-model variants, execution algos), and produce a **draft
   version**. This lives in the instance's version lineage — it is not a clone to a new `instance_id`. The client is
   making a new version of the strategy _they already own exclusively_.

3. **Joint rollout decision.** Odum retains the rollout gate. A draft does not reach live trading until it passes the
   canonical backtest pipeline (at minimum `backtest_1yr` per the maturity model) AND an Odum admin explicitly approves.
   The user's phrasing: "a combination of them and us deciding when we want to roll out new versions, but that would
   only happen after thorough backtesting."

This model satisfies three constraints simultaneously:

- **Commercial differentiation.** Exclusive DART subscribers receive genuinely bespoke alpha.
- **Platform safety.** Odum never ships unvetted client-authored configs to live trading.
- **Batch = Live parity** (CLAUDE.md). Forked versions traverse the same strategy → exec → matching-engine pipeline as
  parent versions; the governance gate is about config correctness, not about a separate pipeline.

---

## §2 Subscription model

The `StrategyInstanceSubscription` record in UAC (`internal/domain/strategy_service/subscription.py`) has three
discriminated subscription types.

| `subscription_type` | `exclusive_lock` | Concurrent with same instance_id                                                    | Gating entitlement                  |
| ------------------- | ---------------- | ----------------------------------------------------------------------------------- | ----------------------------------- |
| `dart_exclusive`    | `true` (always)  | Never another `dart_exclusive`. Coexists with `im_allocation` and `signals_in`.     | `strategy-full` or `ml-full`        |
| `im_allocation`     | `false`          | Any number of concurrent `im_allocation`s (pooled). Coexists with `dart_exclusive`. | `im-client` profile                 |
| `signals_in`        | `false`          | Any number of concurrent `signals_in` subscriptions (read-only on signal feed).     | `execution-full` (Signals-In shape) |

**Exclusive-lock invariant.** At most one active (`released_at IS NULL`) subscription per `instance_id` may have
`subscription_type = dart_exclusive` AND `exclusive_lock = true`. The invariant is enforced at three layers:

1. **UAC class validators** (`class_invariants()`) reject malformed records at deserialisation time.
2. **Firestore composite index** on `(instance_id, exclusive_lock, released_at)` + a **query-before-write** pattern in
   the UTA subscribe endpoint — UTA returns 409 on contention rather than letting Firestore silently race.
3. **UI optimistic update with rollback** — the Subscribe button applies optimistically on click, rolls back on 409, and
   renders an `<ExclusiveLockBadge>` showing who currently holds it.

**Release flow.** Unsubscribing writes `released_at = now()` (never deletes); the Firestore record is preserved for
audit and fork-lineage history. A new `dart_exclusive` may then be created.

**IM coexistence.** An instance with `product_routing = {DART, IM}` can simultaneously carry one active DART exclusive
AND any number of IM pooled/SMA allocations. Routing `{DART}` means no IM footprint — exclusive holder owns the whole
commercial surface. Routing `{IM}` means the instance is never surfaced as Subscribe-able on DART.

**DART Full vs DART Signals-In.** DART Full (`execution-full` + `strategy-full` + `ml-full`) holders can subscribe AND
fork. DART Signals-In (`execution-full` only) can subscribe as `signals_in` but cannot fork — they consume the
Odum-owned signal feed, they do not own the strategy config.

---

## §3 Fork lifecycle

A draft strategy version is a `StrategyVersion` record in UAC (`internal/domain/strategy_service/versions.py`) with a
five-state machine:

```
   draft ──(request-approval)──▶ pending_approval ──(approve)──▶ approved ──(rollout)──▶ rolled_out
     │                                    │                                                    │
     │                                    └──────(reject)──────▶ rejected                      │
     │                                                                                         │
     └──(author edits)───▶ draft                                                                ▼
                                                                                            retired
                                                                                     (on next rollout superseding)
```

**Genesis versions.** Every UAC-seeded `StrategyInstance` has a genesis `StrategyVersion` with
`parent_version_id = None`, `config_diff = None`, `status = rolled_out`. The genesis is authored by `odum-admin` and
represents the default Odum-tuned configuration. Forks descend from whatever version is currently `rolled_out`.

**Fork creation.** `POST /api/v1/strategy-instances/{id}/fork` validates that the caller holds an active
`dart_exclusive` subscription on this instance. It constructs a new `StrategyVersion` with:

- `version_id` = new uuid4
- `parent_version_id` = current rolled_out version's id
- `config_diff` = caller's submitted field-level diff, validated against the parent instance's archetype schema
- `maturity_phase` = `smoke` (drafts reset the maturity staircase — the config has changed, prior backtest credit does
  not transfer)
- `status` = `draft`
- `authored_by` = subscription's client_id

The `subscription.fork_lineage` list appends the new `version_id`, preserving the full chain of drafts the client has
authored.

**Approval request.** `POST /strategy-versions/{vid}/request-approval` publishes a message to the Pub/Sub topic
`strategy-version-approval-queue`. strategy-service's `pending_approvals_runner` subscribes, invokes the canonical
backtest pipeline (see [`strategy-registry-v2.md`](./strategy-registry-v2.md)) with the draft's config applied, persists
the backtest series to `gs://<bucket>/strategy-versions/{vid}/backtest.parquet`, and updates the version's
`maturity_phase` + `backtest_series_ref`. The runner uses shard-level failure isolation per CLAUDE.md: any backtest
exception is classified via `classify_venue_error()`, emits `ADAPTER_FETCH_FAILED`, and the version stays
`pending_approval` rather than crashing the runner loop.

**Approval gate.** `POST /strategy-versions/{vid}/approve` is admin-only and enforces `maturity_phase >= backtest_1yr`
(strict precondition — returns 412 below threshold, not 403). Approval writes an `ApprovalRecord` with
`backtest_maturity`, `backtest_series_ref`, and admin's `review_notes`. Status transitions to `approved`. No rollout
yet.

**Rollout.** `POST /strategy-versions/{vid}/rollout` is admin-only. It transitions `approved → rolled_out`, retires the
prior `rolled_out` version for this `parent_instance_id`, and emits `STRATEGY_VERSION_ROLLED_OUT`. The in-service
`VersionGovernanceReloader` polls Firestore every 5 minutes and hot-reloads any newly-rolled-out version into
strategy-service's in-memory registry. Within one reload cycle, live strategy-service workers are running the new
config.

---

## §4 Version governance

**Who approves.** Admin role (`execution-full` + admin claim). In practice a small on-call rotation of Odum strategy-ops
engineers holds the approve action, backed by the strategy-architect lead for large config deltas.

**What the approver reviews.** The admin queue at `/admin/strategy-version-approvals` shows each pending version with
(a) author + requested-at, (b) `config_diff.changed_fields` rendered as an inline table, (c) a maturity badge, (d) the
`<PerformanceOverlay>` (Plan C) preloaded from `backtest_series_ref`. The admin compares the draft backtest against the
parent's backtest and, optionally, against `odum-paper`'s paper series. The overlay makes alpha-decay and slippage
divergence visible in the same surface where the approve action lives.

**Rejection.** Rejections require a `rejection_reason` of ≥ 40 characters. Rejected versions are terminal — the client
must start a new fork. The rejection message surfaces back to the DART client on their `/services/trading/versions`
page.

**Cross-instance rule.** A client's exclusive on `instance_id = A` does NOT grant them authoring rights on
`instance_id = B` even if A and B share an archetype. Each exclusive is scoped to one instance.

**Retirement cascade.** When an instance itself is retired (maturity phase → `retired`), all active subscriptions on
that instance are released (`reason = "instance_retired"`). Any `pending_approval` or `draft` versions on the retired
instance transition to `rejected` with auto-reason `"parent instance retired"`.

---

## §5 Approval SLA

| Scenario                                   | Target turnaround | Escalation                                                                               |
| ------------------------------------------ | ----------------- | ---------------------------------------------------------------------------------------- |
| Single-parameter diff, <1yr backtest ready | 48h               | Slack `#strategy-governance` at 24h; strategy-architect lead at 48h.                     |
| Multi-year backtest required               | 5 business days   | Runner retries 3× on adapter failure; manual review after 3rd retry.                     |
| Client urgency override                    | 24h               | Client requests via support ticket; approver commits to 24h sync turnaround or declines. |

The SLA is operational guidance, not a hard contract — the `approve` action never auto-fires based on elapsed time.
Humans remain in the loop per CLAUDE.md §Executing actions with care.

**Audit trail.** Every state transition writes a UTL lifecycle event (7 events in total — see plan §Phase 1). The event
stream is queryable in the admin approvals UI for forensic review and ships to the standard BigQuery lifecycle-event
sink for compliance reporting.

---

## §6 Rollout gates

**Feature flag.** All six endpoints + UI surfaces are gated behind `dart_exclusive_enabled` (UnifiedCloudConfig, per
environment). Disabled → endpoints return 404, UI chips hidden, admin approvals queue hidden. Staging/CI default `true`;
prod default `false` until B3 gate passes.

**D3 (staging SIT).** The staging smoke loop is the seven-step sequence documented in the plan's `p6-d3-staging-sit`
todo: odum-paper subscribes → forks → requests approval → strategy-service runs backtest → admin approves → admin rolls
out → VersionGovernanceReloader hot-reloads within 5min. Green on `central-element-323112` (staging doubles as R&D per
2026-04-20 session memory) unlocks GA readiness.

**B3 (first-client loop).** Captures the first non-odum DART Full client completing the full loop end-to-end, with
screenshots + event-log excerpts appended to
[`/codex/14-customer-journeys/shared-core/strategy-version-governance.md`](../../14-customer-journeys/shared-core/strategy-version-governance.md)
as an appendix. B3 is the commercial sign-off that the feature is usable as sold, not merely functional.

**Rollback posture.** Prior rolled_out versions remain in Firestore after supersession (status `retired`). Admin can
issue a hot-revert via `strategy-service/scripts/hot_revert_version.py --version <prior-version-id>`, which re-promotes
the retired version to `rolled_out` and retires the current. UI rollback is deferred to a follow-up plan — the CLI path
is sufficient for the incident response use case at the capacity this feature launches at.

---

## §7 Out of scope (documented here so follow-ups are unambiguous)

- **Side-by-side A/B comparison UI.** Admin queue shows one version's backtest; future work renders draft vs parent
  side-by-side with the Plan C `<PerformanceOverlay>` in split-mode. Deferred plan.
- **Multi-tenant dart_exclusive.** The exclusive is literally one-at-a-time; multiple concurrent exclusives would be a
  different commercial product and a different data model.
- **Pricing / commercial terms.** The exclusive premium, minimum-subscription-period, and upsell ladder are owned by the
  commercial-model codex (`codex/14-customer-journeys/commercial-model/`), not this technical design.
- **Signals-In fork capability.** Signals-in subscribers never fork. The signal feed is the product; the strategy config
  upstream is not theirs to edit.
- **UI rollback flow.** Admin CLI hot-revert covers the immediate operational need; UI work is a follow-up.
