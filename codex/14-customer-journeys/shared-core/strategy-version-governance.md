---
doc_type: codex-ssot
title: Strategy Version Governance — Operator Playbook
summary:
  Day-to-day operator playbook for DART forked strategy versions — who approves (internal-trader/admin), SLA targets,
  the hard backtest_1yr approval floor (412 on lower maturity, no exception path), reject/backtest-failure escalation,
  rollout + hot-revert + feature-flag rollback, and the quarterly auditor checklist.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, runbook, audit, escalation, uac, verification]
related:
  [
    ../../09-strategy/architecture-v2/dart-exclusive-research-fork.md,
    ../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/14-customer-journeys/shared-core/odum-paper-client-zero.md,
    ../../09-strategy/architecture-v2/performance-overlay.md,
  ]
created: 2026-04-22
authoritative_for: [DART strategy-version approval/rollout operator playbook (backtest_1yr floor, SLAs)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
    /codex/14-customer-journeys/shared-core/odum-paper-client-zero.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Version Governance — Operator Playbook

Status: **canonical** — source of truth for the day-to-day governance of DART forked strategy versions. All runbooks +
UI copy must mirror this document.

Parent plan: `plans/archive/dart_exclusive_subscription_research_fork_2026_04_21.plan.md`. Architecture SSOT:
[`/codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md`](../../09-strategy/architecture-v2/dart-exclusive-research-fork.md).

Cross-refs:

- UAC types: `unified_api_contracts.strategy` — `StrategyVersion`, `VersionStatus`, `ApprovalRecord`, `ConfigDiff`,
  `minimum_approval_maturity()`.
- UTA endpoints: `unified_trading_api/routes/strategy_subscriptions.py`.
- UTL events: `STRATEGY_VERSION_APPROVAL_REQUESTED`, `STRATEGY_VERSION_APPROVED`, `STRATEGY_VERSION_REJECTED`,
  `STRATEGY_VERSION_ROLLED_OUT`.
- Plan A maturity ladder:
  [`/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md`](../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md).
- Odum-paper runs: [`odum-paper-client-zero.md`](odum-paper-client-zero.md).

---

## 1. Who approves

| Role                      | Can request approval | Can approve / reject | Can roll out |
| ------------------------- | :------------------: | :------------------: | :----------: |
| DART-exclusive subscriber |  ✓ (their own fork)  |                      |              |
| `internal-trader`         |                      |          ✓           |      ✓       |
| `admin`                   |          ✓           |          ✓           |      ✓       |
| Other personas            |                      |                      |              |

Any admin action writes an `ApprovalRecord` + emits the corresponding UTL event. The audit ledger is the Firestore
collection `strategy_versions` + Pub/Sub replay topic — no out-of-band channel counts as "approval."

**On-call expectation:** admin approval queue is watched during business hours (UK 09:00–18:00); out-of-hours approvals
are allowed but not expected.

## 2. SLA targets

| Step                                              | Target turnaround | Escalation threshold |
| ------------------------------------------------- | ----------------- | -------------------- |
| `DRAFT` → `PENDING_APPROVAL` (client self-serve)  | Instant           | —                    |
| `PENDING_APPROVAL` → approve/reject (1-yr BT)     | 48h               | 72h                  |
| `PENDING_APPROVAL` → approve/reject (multi-yr BT) | 5 business days   | 7 business days      |
| `APPROVED` → `ROLLED_OUT`                         | 24h               | 48h                  |

Backtest runs (kicked off by strategy-service on `STRATEGY_VERSION_APPROVAL_REQUESTED`) are the primary source of
turnaround variance. A 1-year backtest on the odum-paper representative account typically completes in 30-90min
depending on archetype data density; multi-year runs are batched overnight.

## 3. Approval gate — backtest_1yr floor

The admin approval endpoint (`POST /api/v1/strategy-versions/{vid}/approve`) returns **412 Precondition Failed** when
the caller supplies `backtest_maturity` below `BACKTEST_1YR`. Enforced at the UTA route layer AND at the UAC dataclass
invariant (`StrategyVersion.__post_init__` rejects a non-None approval whose `backtest_maturity` is below the floor).

The floor is **not a soft preference** — the user directive (2026-04-21) is categorical: _"new versions only roll out
after thorough backtesting."_ Lowering the floor below `BACKTEST_1YR` requires a codex amendment + plan D version bump.

**Exception path:** none. The approval gate is hard. If a strategy must go live before a 1-year backtest is viable (e.g.
pre-seeded archetype with < 1yr of historical data), the admin must:

1. Run an extended paper trade on the `odum-paper` account for ≥ 90 days AT the version's config, promoting through
   `PAPER_1D → PAPER_14D → PAPER_STABLE`.
2. Synthesise a 1-year equivalent via the strategy-service backtest engine's **synthetic-history** mode (documented in
   Phase A p3-extended-backfill-mode).
3. Approval still records `BACKTEST_1YR` maturity; `review_notes` must cite the synthesis provenance.

## 4. Reject path

Admin rejection (`POST /strategy-versions/{vid}/reject`) transitions `PENDING_APPROVAL → REJECTED` (terminal).
`rejection_reason` is **required** — the UTA endpoint returns 422 on empty reason.

Common rejection reasons (non-exhaustive):

- Alpha signal below threshold (Sharpe < 1.0 on 1yr backtest).
- Config change introduces venue beyond the instance's venue-set variant.
- Backtest reveals regime-break sensitivity the author didn't control for.
- Insufficient review notes — the `ApprovalRecord.review_notes` field is populated on both approve and reject; clients
  can read `.review_notes` to understand the decision rationale.

Rejected versions stay in the version DAG (they are not deleted), so the lineage trail remains auditable. The author can
fork from the original parent again to produce a new draft.

## 5. Backtest failure escalation

The strategy-service version-governance worker (`approval_worker.py` — Phase 3) retries failed backtest runs 3× with
exponential backoff. On 3rd failure it:

1. Emits `STRATEGY_ADAPTER_FAILURE` with `details.version_id + details.cause`.
2. Leaves the version in `PENDING_APPROVAL` (does NOT transition to REJECTED).
3. Surfaces the failure on the admin approvals queue with a red "backtest-failed" badge + last-error message.

Admins triage manually. Typical resolutions:

- Underlying data availability gap → wait for MTDS backfill, then re-trigger via
  `strategy-service/scripts/retry_backtest.py --version <vid>`.
- Venue downtime → same (MTDS will retry the adapter fetch; `ADAPTER_FETCH_FAILED` events surface the cause).
- Strategy-engine bug → version stays pending indefinitely until the engine fix ships + the run retries.

## 6. Rollout + rollback

### 6.1 Rollout

`POST /api/v1/strategy-versions/{vid}/rollout` transitions `APPROVED → ROLLED_OUT`, sets `rolled_out_at = now()`, and
automatically **retires** any previously rolled-out version on the same `parent_instance_id`. Active subscriptions'
`version_id` pointer updates on the next reload window (strategy-service's `LifecycleReloader` has a 5-min max stale
window).

Rollouts are **monotonic forward** — you can't rollout a version older than the currently active one without first
retiring the active one via explicit admin action.

### 6.2 Hot revert

When a rolled-out version misbehaves in production, the admin uses the CLI script
`strategy-service/scripts/hot_revert_version.py --version <prev_vid>` to:

1. Re-approve the prior version (bypasses PENDING_APPROVAL — admin-only path).
2. Transition it back to `ROLLED_OUT`.
3. Retire the misbehaving version.

Hot reverts emit `STRATEGY_VERSION_ROLLED_OUT` with a `revert=True` flag in details. The misbehaving version stays in
the version DAG as `RETIRED` with a notes annotation describing the revert reason.

(Phase 6 follow-up: the hot-revert CLI script itself ships as part of Phase 3 strategy-service version-governance
delivery.)

### 6.3 Feature-flag rollback

Both rollout and hot-revert are gated by `dart_exclusive_enabled` in UTA app state. If the feature needs to be disabled
org-wide:

1. Set env `UTA_DART_EXCLUSIVE_ENABLED=false` (read by startup config).
2. All 7 endpoints return 404.
3. In-flight versions + subscriptions remain in their Firestore state; they resume when the flag flips back on.

## 7. Auditor checklist

When preparing a version-governance audit (quarterly or on-demand):

- [ ] Pull the last N `STRATEGY_VERSION_APPROVED` events from Pub/Sub replay.
- [ ] Cross-check each with the Firestore `strategy_versions` collection — every event MUST have a matching record with
      a non-null `approval`.
- [ ] Verify `approval.backtest_maturity >= BACKTEST_1YR` for all approved.
- [ ] Verify `approved_by` corresponds to an admin-role account at the time of approval (admin-permissions ledger).
- [ ] Sample 5 versions and reconstruct the lineage via `parent_version_id` chain — the DAG should be consistent +
      cycle-free.
- [ ] Verify every `STRATEGY_VERSION_ROLLED_OUT` has a corresponding `supersedes_version_id` transition to `RETIRED` on
      the prior active.

Failures at any step are tier-1 incidents; page the on-call + open a post-mortem per
`/codex/12-incidents/post-mortem-template.md`.

## 8. Links

- Parent plan:
  [dart_exclusive_subscription_research_fork_2026_04_21.plan.md](../../../plans/archive/dart_exclusive_subscription_research_fork_2026_04_21.plan.md)
- Architecture: [dart-exclusive-research-fork.md](../../09-strategy/architecture-v2/dart-exclusive-research-fork.md)
- Maturity ladder: [strategy-lifecycle-maturity.md](../../09-strategy/architecture-v2/strategy-lifecycle-maturity.md)
- Odum-paper runs: [odum-paper-client-zero.md](odum-paper-client-zero.md)
- Performance overlay (for admin review UI):
  [performance-overlay.md](../../09-strategy/architecture-v2/performance-overlay.md)
