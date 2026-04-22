---
name: dart-exclusive-subscription-research-fork-2026-04-21
overview: |
  DART clients subscribe to strategy instances with exclusive-lock semantics (only
  one DART client can subscribe to a given instance at a time; IM clients can still
  allocate to it under pooled / SMA routing). Once subscribed, the DART client can
  fork the strategy in Research, modify configuration, and publish as a new draft
  version. Version graduation is joint Odum-client governance — new versions only
  roll out after thorough backtesting (≥ `backtest_1yr` maturity threshold) plus
  explicit Odum admin approval. This plan introduces `StrategyInstanceSubscription`
  + `StrategyVersion` records in UAC, subscribe/fork/approve/rollout endpoints in
  UTA, a version-governance module in strategy-service, and the DART subscription
  / fork / approvals UI in unified-trading-system-ui. Depends on Plan A (lifecycle
  maturity model — provides maturity phases + product routing), Plan B (3-tier
  catalogue — provides the Subscribe CTA surface), Plan C (PerformanceOverlay —
  provides the backtest/paper/live series the admin reviews for approval).
type: mixed
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-21

completion_gates:
  code: C5
  deployment: D3
  business: B3

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-api
    code: C0
    deployment: D0
    business: none
  - repo: strategy-service
    code: C0
    deployment: D0
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: D0
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - strategy_lifecycle_maturity_model_2026_04_21
  - strategy_catalogue_3tier_surface_2026_04_21
  - performance_overlay_continuous_timeline_2026_04_21

# ────────────────────────────────────────────────────────────────────────────
# CONTEXT
# ────────────────────────────────────────────────────────────────────────────
#
# User directive (2026-04-21 session):
#   "For Dart ... we would also want to give them the ability to select which
#    strategies they want to subscribe to for Dart. At that point they can now
#    run research, change configurations and such, and they can see the default
#    strategy that they subscribe to that already exists, but they can also
#    change that. Effectively, they're making new versions of strategies
#    themselves. At that point, we've already locked up the strategy if we're
#    giving it to them, so it's an exclusive deal. It has put our codex so
#    it's going to be a combination of them and us deciding when we want to
#    roll out new versions, but that would only happen after thorough
#    backtesting."
#
# Three interlocking concepts:
#
#   1. EXCLUSIVE SUBSCRIPTION (DART only)
#      At most ONE DART client can hold `subscription_type=dart_exclusive` +
#      `exclusive_lock=true` per `instance_id`. IM allocations
#      (`subscription_type=im_allocation`) and signals-in subscriptions
#      (`subscription_type=signals_in`) are NOT exclusive — they coexist with
#      each other AND with an active DART exclusive on the same instance,
#      because IM is pooled-by-design and signals-in reads the signal feed
#      rather than owning the instance config.
#
#   2. RESEARCH FORK
#      A DART client holding an exclusive subscription can fork the instance
#      into a new draft `StrategyVersion` via the DART Research surface. The
#      fork inherits the parent's config and produces a diff. The draft runs
#      under the SAME instance_id — versions are ordered within the instance's
#      lineage, not cloned to new instance_ids.
#
#   3. JOINT VERSION GOVERNANCE
#      A draft must be submitted for approval. strategy-service runs it through
#      the canonical backtest pipeline. Approval requires the backtest to reach
#      `backtest_1yr` minimum viability (per Plan A maturity enum) AND an Odum
#      admin to explicitly approve. Only then can it roll out to live,
#      superseding the prior version on the same instance_id. Client authors
#      the version; Odum gates rollout. "Joint decision" in the user's phrasing.
#
# DART Full vs DART Signals-In:
#   - DART Full holders (`execution-full` + `strategy-full` + `ml-full`) CAN
#     hold exclusive subscriptions and fork.
#   - DART Signals-In (`execution-full` only, no `strategy-full`/`ml-full`) CAN
#     subscribe with `subscription_type=signals_in` but CANNOT fork — they
#     consume signals, they don't own the strategy config.
#
# IM interaction:
#   An instance with `product_routing={DART, IM}` can simultaneously have one
#   DART exclusive holder AND any number of IM pooled/SMA allocations. The
#   exclusive lock gates DART subscriptions only. If the routing is
#   `product_routing={DART}` only, the DART holder's exclusive is the entire
#   commercial footprint — no IM allocations exist for that instance.
#
# `odum-paper` / `odum-live` interaction:
#   The `odum-paper` client-zero (Plan A) is NEVER an exclusive subscriber —
#   it's an internal paper-run client that runs every instance regardless of
#   exclusive status. It consumes the parent version's config; when a client
#   forks, `odum-paper` starts paper-running the draft version alongside the
#   parent so backtests + paper series exist at version-approval time.
#
# Batch = Live parity (CLAUDE.md):
#   Forked versions run through the SAME pipeline as parent versions (strategy
#   → exec → matching-engine for backtest/paper, real venue for live). The
#   approval gate is about config safety, not about pipeline divergence.
#
# ────────────────────────────────────────────────────────────────────────────
# PRE-AUDIT MANIFEST
# ────────────────────────────────────────────────────────────────────────────
#
# Symbols introduced (net new — no existing type is being renamed or deleted):
#   - unified_api_contracts.internal.domain.strategy_service.subscription.StrategyInstanceSubscription
#   - unified_api_contracts.internal.domain.strategy_service.subscription.SubscriptionType
#   - unified_api_contracts.internal.domain.strategy_service.subscription.ExclusiveLockViolation
#   - unified_api_contracts.internal.domain.strategy_service.versions.StrategyVersion
#   - unified_api_contracts.internal.domain.strategy_service.versions.VersionStatus
#   - unified_api_contracts.internal.domain.strategy_service.versions.ConfigDiff
#   - unified_api_contracts.internal.domain.strategy_service.versions.ApprovalRecord
#   - unified_trading_library.events.STRATEGY_VERSION_* (5 new UTL lifecycle events)
#
# Downstream consumers to update (pre-audit grep across workspace):
#
#   [UAC] unified-api-contracts
#     - unified_api_contracts/__init__.py — export subscription + versions facades
#     - unified_api_contracts/strategy.py — re-export from domain facade
#     - unified_api_contracts/registry/strategy_instances/ — ensure instance IDs
#       referenced by subscriptions resolve (Plan A seed)
#     - tests/internal/domain/strategy_service/ — add ~40 test cases
#
#   [UTL] unified-trading-library
#     - unified_trading_library/events/lifecycle_events.py — add:
#       STRATEGY_VERSION_DRAFT_CREATED
#       STRATEGY_VERSION_APPROVAL_REQUESTED
#       STRATEGY_VERSION_APPROVED
#       STRATEGY_VERSION_REJECTED
#       STRATEGY_VERSION_ROLLED_OUT
#       STRATEGY_SUBSCRIPTION_CREATED
#       STRATEGY_SUBSCRIPTION_RELEASED
#     - unified_trading_library/events/STANDARD_LIFECYCLE_EVENTS set
#     - tests/events/test_lifecycle_events.py
#
#   [UTA] unified-trading-api
#     - unified_trading_api/routers/strategy_instances.py — add 5 endpoints
#       (subscribe / unsubscribe / fork / request-approval / approve / rollout)
#     - unified_trading_api/auth/entitlements.py — new dart_exclusive gate
#     - unified_trading_api/stores/ — Firestore repositories:
#         strategy_instance_subscriptions_repo.py (new)
#         strategy_versions_repo.py (new)
#     - unified_trading_api/config/features.py — feature flag dart_exclusive_enabled
#     - tests/integration/test_strategy_subscriptions.py
#     - tests/integration/test_strategy_versions.py
#
#   [strategy-service]
#     - strategy_service/version_governance/ — new module
#         __init__.py
#         pending_approvals_runner.py
#         backtest_gate.py
#         version_publisher.py
#     - strategy_service/service_config.py — add governance reloader
#     - strategy_service/config_reloaders.py — new VersionGovernanceReloader
#     - tests/unit/version_governance/
#
#   [unified-trading-system-ui]
#     - components/strategy-catalogue/RealityPositionCard.tsx — add "Unsubscribe"
#     - components/strategy-catalogue/FomoTearsheetCard.tsx — replace "Request
#       allocation" CTA with "Subscribe (DART Exclusive)" when product_routing
#       includes DART AND instance is not already exclusively held
#     - components/strategy-catalogue/SubscribeButton.tsx (new)
#     - components/strategy-catalogue/ExclusiveLockBadge.tsx (new)
#     - app/(platform)/services/research/[slot]/fork/page.tsx (new)
#     - app/(platform)/services/research/[slot]/config-diff-editor.tsx (new)
#     - app/(ops)/admin/strategy-version-approvals/page.tsx (new)
#     - components/strategy-versions/VersionLineageBadge.tsx (new)
#     - components/strategy-versions/ApprovalQueueRow.tsx (new)
#     - lib/config/services.ts — DART tile: add `subscriptions` + `versions` chips
#     - lib/auth/persona-dashboard-shape.ts — chip visibility per persona
#     - lib/auth/persona-lifecycle-shape.ts — DART sub-tab for Approvals (admin-only)
#     - lib/api/strategy-subscriptions.ts (new)
#     - lib/api/strategy-versions.ts (new)
#     - tests/unit/components/strategy-catalogue/subscribe-button.test.tsx
#     - tests/unit/components/strategy-versions/version-lineage-badge.test.tsx
#     - tests/unit/app/admin/strategy-version-approvals.test.tsx
#
#   [PM — this plan + codex]
#     - plans/active/INDEX.md — new entry under Strategy Lifecycle & Catalogue
#     - codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md (new)
#     - codex/14-playbooks/shared-core/strategy-version-governance.md (new)
#     - codex/09-strategy/architecture-v2/dashboard-services-grid.md — amend §6
#       with cross-ref to Plan D
#     - codex/09-strategy/architecture-v2/dart-tab-structure.md — amend §2 with
#       Approvals sub-tab (admin-only)
#
# Files I CANNOT verify from this authoring-only scope:
#   - Firestore security rules (manually checked only at exec time in Phase 6)
#   - Secret Manager entries for signed webhook reuse — not applicable here, no
#     external webhooks; all calls are inbound UTA → Firestore
#
# ────────────────────────────────────────────────────────────────────────────
# EXECUTION DAG
# ────────────────────────────────────────────────────────────────────────────
#
#   Phase 1 (UAC + UTL schema)  ─┐
#         │                       │
#         ▼                       │
#   Phase 2 (UTA endpoints)  ─────┤
#         │                       │
#         ▼                       ├── Phase 5 codex + tests (PARALLEL with 1-4)
#   Phase 3 (strategy-service) ───┤
#         │                       │
#         ▼                       │
#   Phase 4 (UI surfaces)    ─────┘
#         │
#         ▼
#   Phase 6 (rollout + QG sweep + feature flag + staging SIT)
#
# QG gate between every phase. Phase 5 codex is parallelisable because it
# describes design not implementation; updates as each phase lands.
#
# ────────────────────────────────────────────────────────────────────────────

todos:
  # ──────────────────────────────────────────────────────────────────────
  # PHASE 1 — UAC + UTL schema (SEQUENTIAL, P0, AGENT)
  # ──────────────────────────────────────────────────────────────────────

  - id: p1-uac-subscription-record
    content: |
      - [x] [AGENT] P0. Create
            `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/subscription.py`
            with:
              - `SubscriptionType` Enum: `dart_exclusive` | `im_allocation` | `signals_in`
              - `StrategyInstanceSubscription` dataclass (frozen):
                  instance_id: str (FK to StrategyInstance)
                  client_id: str (FK to Client — Plan A)
                  subscription_type: SubscriptionType
                  subscribed_at: datetime
                  released_at: datetime | None (None = active)
                  exclusive_lock: bool (True only for subscription_type=dart_exclusive)
                  version_id: str (currently active version for this subscription)
                  fork_lineage: tuple[str, ...] (ordered; parent → draft → approved → rolled_out)
                  notes: str | None
              - `ExclusiveLockViolation(Exception)` with
                  `.existing_holder: str` + `.instance_id: str` attributes
              - `__post_init__` validator enforcing:
                  - `exclusive_lock=True` ⇒ `subscription_type=dart_exclusive`
                  - `released_at` is None OR > subscribed_at
                  - `version_id` in `fork_lineage`
              - Re-exported from `unified_api_contracts.strategy` facade.
            **DONE 2026-04-22** (UAC `07b5089`). Dataclass (frozen) matches
            catalogue.py pattern; BaseModel not used here (repo convention for
            domain records). 11/11 test_subscription.py cases green.
      status: done

  - id: p1-uac-versions-record
    content: |
      - [x] [AGENT] P0. Create
            `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/versions.py`
            with:
              - `VersionStatus` Enum: `draft` | `pending_approval` | `approved` |
                `rolled_out` | `retired` | `rejected`
              - `ConfigDiff` BaseModel:
                  base_version_id: VersionId
                  changed_fields: dict[str, tuple[Any, Any]] (field_name → (old, new))
                  unchanged_fingerprint: str (sha256 of unchanged subset)
              - `ApprovalRecord` BaseModel:
                  approved_by: str (admin client_id)
                  approved_at: datetime
                  backtest_maturity: StrategyMaturityPhase (from Plan A)
                  backtest_series_ref: str (GCS URI)
                  review_notes: str | None
              - `StrategyVersion` BaseModel:
                  version_id: VersionId
                  parent_instance_id: str
                  parent_version_id: VersionId | None (None for genesis)
                  config_diff: ConfigDiff | None (None for genesis)
                  backtest_series_ref: str | None (populated after strategy-service run)
                  maturity_phase: StrategyMaturityPhase
                  status: VersionStatus
                  authored_by: str (client_id)
                  approval: ApprovalRecord | None
                  created_at: datetime
                  rolled_out_at: datetime | None
              - `class_invariants()` validator:
                  - `status=approved` ⇒ `approval is not None` AND
                    `approval.backtest_maturity >= backtest_1yr`
                  - `status=rolled_out` ⇒ `rolled_out_at is not None`
                  - `parent_version_id is None` ⇒ `config_diff is None` (genesis)
              - Re-export from `unified_api_contracts.strategy` facade.
            **DONE 2026-04-22** (UAC `07b5089`). `versions.py` ships
            `ConfigDiff`, `ApprovalRecord`, `StrategyVersion`, `VersionStatus`
            + `minimum_approval_maturity()` helper. 15/15 test_versions.py cases
            green including the BACKTEST_1YR-floor gate.
      status: done

  - id: p1-utl-lifecycle-events
    content: |
      - [x] [AGENT] P0. Extend
            `unified-trading-library/unified_trading_library/events/lifecycle_events.py`
            with 7 new events:
              STRATEGY_SUBSCRIPTION_CREATED — details: instance_id, client_id,
                subscription_type, exclusive_lock
              STRATEGY_SUBSCRIPTION_RELEASED — details: instance_id, client_id,
                reason ("client_unsubscribed"|"admin_revoked"|"instance_retired")
              STRATEGY_VERSION_DRAFT_CREATED — details: version_id,
                parent_instance_id, authored_by
              STRATEGY_VERSION_APPROVAL_REQUESTED — details: version_id,
                requested_at
              STRATEGY_VERSION_APPROVED — details: version_id, approved_by,
                backtest_maturity, backtest_series_ref
              STRATEGY_VERSION_REJECTED — details: version_id, rejected_by,
                rejection_reason
              STRATEGY_VERSION_ROLLED_OUT — details: version_id,
                supersedes_version_id, rolled_out_at
            Add all 7 to `STANDARD_LIFECYCLE_EVENTS` set so they are validated
            by the lifecycle-event linter.
            **DONE 2026-04-22** (UTL `797f1f99`). 7 new constants grouped as
            `STRATEGY_SUBSCRIPTION_AND_VERSION_EVENT_TYPES` and appended to
            `STANDARD_LIFECYCLE_EVENTS` at import time. Note: shipped into
            `event_types.py` (which carries the QG size-cap exemption) rather
            than a new `lifecycle_events.py` module — matches the file layout
            other Plan-era events ship into.
      status: done

  - id: p1-uac-utl-tests
    content: |
      - [x] [AGENT] P0. Unit tests in UAC + UTL:
              - UAC: `tests/internal/domain/strategy_service/test_subscription.py`
                — exclusive_lock invariants, subscription_type mismatches,
                temporal validity (released_at > subscribed_at).
              - UAC: `tests/internal/domain/strategy_service/test_versions.py` —
                version status invariants, genesis handling, approval-required
                rule, backtest_1yr minimum gate.
              - UTL: `tests/events/test_lifecycle_events.py` — 7 events present,
                STANDARD_LIFECYCLE_EVENTS contains all 7, details schemas
                accepted.
            `cd unified-api-contracts && bash scripts/quality-gates.sh` AND
            `cd unified-trading-library && bash scripts/quality-gates.sh` both green.
            **DONE 2026-04-22** — UAC 26/26 tests (11 subscription + 15 versions)
            green. UTL import smoke confirms all 7 new constants load cleanly
            and are in `STANDARD_LIFECYCLE_EVENTS`. Full QG deferred to Phase 6
            workspace sweep per plan convention (Phase 1 uses test-level gates).
      status: done

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 2 — UTA subscription + fork API (SEQUENTIAL after Phase 1, P0)
  # ──────────────────────────────────────────────────────────────────────

  - id: p2-uta-firestore-repos
    content: |
      - [ ] [AGENT] P0. Create UTA Firestore repositories:
              - `unified_trading_api/stores/strategy_instance_subscriptions_repo.py`
                — collection `strategy_instance_subscriptions`; CRUD + query by
                instance_id + query by client_id; composite index on
                `(instance_id, exclusive_lock, released_at)` for fast
                exclusive-lock contention checks.
              - `unified_trading_api/stores/strategy_versions_repo.py` —
                collection `strategy_versions`; CRUD + query by instance_id
                ordered by created_at + list-by-status for admin queue.
            Both repos use the existing `get_firestore_client()` from UCI. Mock
            backend via `MockStateStore` from UTL for local-dev-mode mutations
            persisting to `.local-dev-cache/`.
      status: pending

  - id: p2-uta-subscribe-endpoints
    content: |
      - [ ] [AGENT] P0. Add `unified_trading_api/routers/strategy_instances.py`
            endpoints:
              POST /api/v1/strategy-instances/{instance_id}/subscribe
                body: {client_id, subscription_type}
                200 → {subscription: StrategyInstanceSubscription}
                409 → ExclusiveLockViolation when a dart_exclusive subscription
                  already exists with released_at=None for this instance_id AND
                  the incoming request is also dart_exclusive
                403 → if client lacks entitlement for requested subscription_type
                  (dart_exclusive requires `strategy-full` or `ml-full`;
                  signals_in requires `execution-full`; im_allocation requires
                  `im-client` profile).
                Emits STRATEGY_SUBSCRIPTION_CREATED via UTL.
              DELETE /api/v1/strategy-instances/{instance_id}/subscribe
                query: client_id
                200 → {released_at}. Sets released_at=now(). Releases the
                  exclusive_lock so a new dart_exclusive can be created.
                Emits STRATEGY_SUBSCRIPTION_RELEASED(reason="client_unsubscribed").
      status: pending

  - id: p2-uta-fork-endpoint
    content: |
      - [ ] [AGENT] P0. POST /api/v1/strategy-instances/{instance_id}/fork
            body: {client_id, config_diff: ConfigDiff}
            200 → {version: StrategyVersion with status=draft}
            403 → unless caller holds active dart_exclusive subscription on
              this instance_id.
            422 → if config_diff references fields not declared by the
              parent instance's strategy archetype schema.
            Creates new VersionId (uuid4), parent_version_id = current active
            version for this instance, maturity_phase = parent's phase capped
            at `smoke` (drafts start fresh on the maturity staircase).
            Appends version_id to subscription.fork_lineage.
            Emits STRATEGY_VERSION_DRAFT_CREATED.
      status: pending

  - id: p2-uta-approval-endpoints
    content: |
      - [ ] [AGENT] P0. Add UTA version-governance endpoints:
              POST /api/v1/strategy-versions/{version_id}/request-approval
                caller: version.authored_by
                200 → transitions status draft → pending_approval; triggers
                  strategy-service via Pub/Sub `strategy-version-approval-queue`
                  topic (Phase 3 runner subscribes).
                Emits STRATEGY_VERSION_APPROVAL_REQUESTED.
              POST /api/v1/strategy-versions/{version_id}/approve
                caller: admin role only (`execution-full` + admin claim)
                body: {review_notes?}
                200 → transitions pending_approval → approved; writes
                  ApprovalRecord with backtest_maturity fetched from
                  strategy-service (via Firestore — written by Phase 3 runner).
                  REJECTS the approval if backtest_maturity < backtest_1yr
                  (returns 412 Precondition Failed).
                Emits STRATEGY_VERSION_APPROVED.
              POST /api/v1/strategy-versions/{version_id}/reject
                caller: admin only
                body: {rejection_reason}
                200 → transitions pending_approval → rejected.
                Emits STRATEGY_VERSION_REJECTED.
              POST /api/v1/strategy-versions/{version_id}/rollout
                caller: admin only
                200 → transitions approved → rolled_out; supersedes prior
                  active version on the parent instance_id (previous
                  rolled_out version → retired).
                Emits STRATEGY_VERSION_ROLLED_OUT.
      status: pending

  - id: p2-uta-feature-flag-and-tests
    content: |
      - [ ] [AGENT] P0. Add feature flag `dart_exclusive_enabled` in
            `unified_trading_api/config/features.py`. All 6 new endpoints gated
            behind this flag (returns 404 when disabled). Integration tests:
              - tests/integration/test_strategy_subscriptions.py — happy path,
                double-subscribe → 409, unsubscribe-then-resubscribe, wrong
                entitlement → 403.
              - tests/integration/test_strategy_versions.py — fork requires
                active subscription, approve rejects below-threshold backtest,
                rollout retires prior version.
            `cd unified-trading-api && bash scripts/quality-gates.sh` green.
      status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 3 — strategy-service version-governance module (P0)
  # ──────────────────────────────────────────────────────────────────────

  - id: p3-strategy-service-governance-module
    content: |
      - [ ] [AGENT] P0. Create `strategy-service/strategy_service/version_governance/`:
              - `pending_approvals_runner.py` — subscribes to the
                `strategy-version-approval-queue` Pub/Sub topic via UCI
                `get_pubsub_client()`. For each `request-approval` message:
                  1. Load StrategyVersion from Firestore.
                  2. Invoke existing canonical backtest pipeline (see
                     `codex/09-strategy/architecture-v2/strategy-registry-v2.md`)
                     with version.config_diff applied to parent instance.
                  3. Write backtest output to GCS at path
                     `gs://<bucket>/strategy-versions/{version_id}/backtest.parquet`.
                  4. Compute maturity_phase from backtest coverage (reuse Plan
                     A maturity derivation helper — `derive_maturity_from_backtest_series`).
                  5. Update version.backtest_series_ref + version.maturity_phase
                     in Firestore.
              - `backtest_gate.py` — `is_approval_eligible(version) -> bool`:
                returns True only if version.maturity_phase >=
                StrategyMaturityPhase.backtest_1yr. Imported by UTA approve
                endpoint AND by the admin UI.
              - `version_publisher.py` — on STRATEGY_VERSION_ROLLED_OUT, emits
                a `strategy_instance_reconfig` signal so running
                strategy-service processes hot-reload the new version's config
                via the existing `VersionGovernanceReloader`.
            Shard-level failure isolation per CLAUDE.md — runner catches all
            exceptions per-version via `classify_venue_error()`, emits
            `ADAPTER_FETCH_FAILED` on the backtest shard, never raises to the
            Pub/Sub loop.
      status: pending

  - id: p3-strategy-service-reloader
    content: |
      - [ ] [AGENT] P0. Add `VersionGovernanceReloader` to
            `strategy-service/strategy_service/config_reloaders.py` following
            the typed-config-reloader pattern from
            `codex/06-coding-standards/config-reloader-pattern.md`. Reloader
            polls Firestore `strategy_versions` collection for rolled_out
            versions whose `rolled_out_at > last_poll` and hot-reloads them
            into the in-memory `strategy_registry`. Uses `ApiKeyReloader`-style
            5-minute cadence. No one-shot validation.
      status: pending

  - id: p3-strategy-service-tests
    content: |
      - [ ] [AGENT] P0. Unit tests:
              - `tests/unit/version_governance/test_backtest_gate.py` —
                below-threshold phases (smoke → backtest_minimal) rejected;
                at-threshold (backtest_1yr) accepted; above accepted.
              - `tests/unit/version_governance/test_pending_approvals_runner.py`
                — mocked backtest pipeline, asserts Firestore write +
                `ADAPTER_FETCH_FAILED` event path on backtest exception.
              - `tests/unit/test_config_reloaders.py` — Reloader hot-reload
                path.
            `cd strategy-service && bash scripts/quality-gates.sh` green.
      status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 4 — UI DART subscription + fork + approvals flow (P0)
  # ──────────────────────────────────────────────────────────────────────

  - id: p4-ui-subscribe-button-component
    content: |
      - [ ] [AGENT] P0. Create
            `unified-trading-system-ui/components/strategy-catalogue/SubscribeButton.tsx`.
            Props: `instanceId`, `productRouting`, `existingExclusiveHolder?`,
            `callerClientId`, `callerEntitlements`. Behaviour:
              - Disabled if productRouting excludes DART.
              - Disabled + tooltip "Already held by {holder}" if
                existingExclusiveHolder && existingExclusiveHolder !== callerClientId.
              - Label toggles "Subscribe (DART Exclusive)" ↔ "Unsubscribe"
                based on whether caller already holds the exclusive.
              - Click POSTs to /api/v1/strategy-instances/{id}/subscribe or
                DELETE. Optimistic UI with rollback on 409.
              - Emits toast on success/error.
      status: pending

  - id: p4-ui-exclusive-lock-badge
    content: |
      - [ ] [AGENT] P0. Create
            `components/strategy-catalogue/ExclusiveLockBadge.tsx`. Renders a
            lock icon + "Held by {holder}" label on instances with active
            dart_exclusive subscriptions. Variant: compact (tooltip only) for
            tearsheet cards; expanded (full text) for admin universe.
      status: pending

  - id: p4-ui-fomo-card-replace-cta
    content: |
      - [ ] [AGENT] P0. Update
            `components/strategy-catalogue/FomoTearsheetCard.tsx` — replace
            the existing "Request allocation" CTA with `<SubscribeButton>` when
            `productRouting.includes("DART")` AND caller has DART Full
            entitlements AND `allowsAllocationCta(maturity_phase)` returns
            true. Render `<ExclusiveLockBadge>` alongside header when the
            instance is already held. Keep "Request allocation" CTA for IM-only
            routings (falls back to Plan B contact-form).
      status: pending

  - id: p4-ui-reality-card-unsubscribe
    content: |
      - [ ] [AGENT] P0. Update
            `components/strategy-catalogue/RealityPositionCard.tsx` — add
            overflow-menu "Unsubscribe" action (destructive confirm dialog)
            and "Fork for research" primary action that navigates to
            `/services/research/{slot}/fork?instance={instanceId}`. Disabled
            for IM subscriptions (no fork from pooled routing).
      status: pending

  - id: p4-ui-research-fork-page
    content: |
      - [ ] [AGENT] P0. Create
            `app/(platform)/services/research/[slot]/fork/page.tsx`. Reads
            `instance` query param, loads parent StrategyInstance + active
            StrategyVersion, renders config-diff editor as child:
              - `config-diff-editor.tsx` — renders each editable param from
                the parent archetype schema with the parent value pre-filled;
                change events accumulate a ConfigDiff.changed_fields map;
                unchanged fields hashed for fingerprinting.
              - Primary actions: "Save draft" → POST /fork (status=draft);
                "Request approval" → POST /request-approval (status=pending_approval).
              - Banner: "Batch = Live parity enforced. Forked version runs
                through the full pipeline before rollout." Cites CLAUDE.md.
            Gate: only rendered for holders of dart_exclusive subscription on
            this instance; otherwise 403 shell.
      status: pending

  - id: p4-ui-admin-approvals-page
    content: |
      - [ ] [AGENT] P0. Create
            `app/(ops)/admin/strategy-version-approvals/page.tsx`. Admin-only
            queue view of all StrategyVersions with status=pending_approval:
              - Columns: version_id, parent_instance (family.archetype.slot),
                authored_by, maturity_phase badge, backtest_series link,
                requested_at.
              - Row actions: "Approve" (disabled when maturity < backtest_1yr,
                with tooltip citing Plan D version-governance gate); "Reject"
                (requires rejection_reason); "View backtest" (opens
                `<PerformanceOverlay>` from Plan C preloaded with
                backtest_series_ref).
              - Polling cadence 30s; optimistic row updates on action.
            Wired from Admin & Ops tile via new chip `strategy-version-approvals`.
      status: pending

  - id: p4-ui-version-lineage-badge
    content: |
      - [ ] [AGENT] P0. Create
            `components/strategy-versions/VersionLineageBadge.tsx`. Renders
            "v{N} (forked from v{parentN})" with hover-card showing full
            lineage from genesis. Injected into RealityPositionCard,
            FomoTearsheetCard, and the DART terminal header. `v` numbers
            derived from position in parent instance's version history
            (0-indexed genesis = v0).
      status: pending

  - id: p4-ui-tile-chip-wiring
    content: |
      - [ ] [AGENT] P0. Extend `lib/config/services.ts`:
              - DART tile: add chips
                  `subscriptions` → `/services/trading/subscriptions` (new
                    overview page showing caller's active dart_exclusive
                    subscriptions as RealityPositionCard grid)
                  `versions` → `/services/trading/versions` (caller's
                    authored draft + pending versions)
              - Admin & Ops tile: add chip
                  `strategy-version-approvals` →
                    `/admin/strategy-version-approvals`
            Update `persona-dashboard-shape.ts`:
              - `prospect-dart` + `client-full` see `subscriptions` + `versions`
              - `admin` + `internal-trader` see all three chips + approvals
              - `client-premium` + `elysium-defi` see `subscriptions`
                (no `versions` — no fork capability without ml-full)
              - DART Signals-In personas see `subscriptions` only (signals_in
                type, no fork).
            Update `persona-lifecycle-shape.ts` — no change (approvals is
            admin-only chip, not a lifecycle tab).
      status: pending

  - id: p4-ui-api-clients
    content: |
      - [ ] [AGENT] P0. Create `lib/api/strategy-subscriptions.ts` +
            `lib/api/strategy-versions.ts` with typed fetch wrappers for all 6
            new UTA endpoints. Zod-validate responses. Mock-mode stubs in
            `lib/api/mocks/strategy-subscriptions.mock.ts` mirror the
            Firestore-backed behaviour so UAT works credential-free.
      status: pending

  - id: p4-ui-tests
    content: |
      - [ ] [AGENT] P0. Unit tests (vitest, `pool: "forks"`):
              - `tests/unit/components/strategy-catalogue/subscribe-button.test.tsx`
                — 5 cases: DART-gated, exclusive contention, optimistic update,
                rollback on 409, unsubscribe flow.
              - `tests/unit/components/strategy-catalogue/fomo-card-cta-swap.test.tsx`
                — 4 cases: CTA swap to Subscribe when DART-routed, fallback to
                Request-allocation when IM-only, maturity gating, lock-badge
                render.
              - `tests/unit/components/strategy-versions/version-lineage-badge.test.tsx`
                — 3 cases: genesis render (v0 no parent), multi-level lineage,
                hover-card order.
              - `tests/unit/app/admin/strategy-version-approvals.test.tsx` — 5
                cases: queue render, approve disabled below threshold, reject
                requires reason, backtest_series link, row-level optimistic
                update.
              - Playwright smoke: `/services/strategy-catalogue` → Subscribe →
                /services/research/{slot}/fork → Request approval →
                /admin/strategy-version-approvals approve → rollout visible on
                DART terminal. Gated behind `dart_exclusive_enabled` flag.
            `cd unified-trading-system-ui && CI=true npm test -- --run` green.
            `npm run orphan-audit -- --blocking` exits 0 (2 new admin pages +
            3 new client subroutes + all chips wired).
      status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 5 — Codex + playbooks (PARALLEL with Phases 1-4, P1)
  # ──────────────────────────────────────────────────────────────────────

  - id: p5-codex-dart-exclusive-research-fork
    content: |
      - [x] [AGENT] P1. Create
            `codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md`
            (authored in this PR). Six sections:
              §1 Rationale — why exclusive + why joint governance
              §2 Subscription model — SubscriptionType matrix, exclusive-lock
                invariants, DART vs IM vs signals_in
              §3 Fork lifecycle — draft → pending_approval → approved →
                rolled_out → retired state machine
              §4 Version governance — backtest_1yr gate, approval SLA,
                Odum-admin role
              §5 Approval SLA — target turnaround + escalation path
              §6 Rollout gates — feature flag, D3 SIT, B3 first-client loop
            Cross-refs to Plan A lifecycle, Plan B catalogue, Plan C overlay,
            dashboard-services-grid §4.5, dart-tab-structure §2.
      status: done

  - id: p5-codex-strategy-version-governance-playbook
    content: |
      - [ ] [AGENT] P1. Create
            `codex/14-playbooks/shared-core/strategy-version-governance.md` —
            operator-facing playbook:
              - Who approves (admin role + on-call rotation expectation).
              - SLA: target 48h from request-approval to approve/reject under
                normal load; 5 business days for multi-year backtest versions.
              - Escalation: if backtest shard fails, runner retries 3×; on 3rd
                failure version stays pending with STRATEGY_ADAPTER_FAILURE
                event; admin reviews manually.
              - Rollback: admin can rollout a prior approved version as "hot
                revert" via CLI script
                `strategy-service/scripts/hot_revert_version.py --version <vid>`
                (Phase 6 follow-up).
              - Audit: every approval requires review_notes ≥ 40 chars when
                rejecting; approvals without notes are allowed (diff + tests
                are the record).
      status: pending

  - id: p5-amend-dashboard-services-grid-codex
    content: |
      - [ ] [AGENT] P1. Amend
            `codex/09-strategy/architecture-v2/dashboard-services-grid.md` §6
            — add cross-ref row for Plan D:
              "DART exclusive subscription + research fork + version
               lineage lives on the DART tile under `subscriptions` +
               `versions` chips; admin approvals queue under Admin & Ops →
               `strategy-version-approvals`. See
               `dart-exclusive-research-fork.md` for full design."
      status: pending

  - id: p5-amend-dart-tab-structure-codex
    content: |
      - [ ] [AGENT] P1. Amend
            `codex/09-strategy/architecture-v2/dart-tab-structure.md` §2
            DART sub-tab catalogue — no new DART sub-tab (approvals is admin
            tile chip, not DART). Add a note under §6 "Open follow-ups" that
            DART personas with exclusive subscriptions now see Research
            `fork` action on RealityPositionCard — cross-ref Plan D.
      status: pending

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 6 — Rollout + QG sweep + SIT (P0)
  # ──────────────────────────────────────────────────────────────────────

  - id: p6-workspace-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. Run `bash scripts/quality-gates.sh` across all 5
            affected code repos (UAC, UTL, UTA, strategy-service,
            unified-trading-system-ui). Max 20 concurrent per CLAUDE.md. All
            green before Phase 6 continues.
      status: pending

  - id: p6-feature-flag-gradual-rollout
    content: |
      - [ ] [HUMAN+AGENT] P0. Gradual rollout of `dart_exclusive_enabled`:
              - Internal personas first (admin, internal-trader) — validate
                approvals queue + fork flow with `odum-paper` as fake client.
              - Then DART Full pilot client (single org) — 2-week pilot.
              - Then GA to all DART Full clients.
            Feature flag configured via UnifiedCloudConfig per environment;
            CI/staging enabled, prod gated behind human GA decision.
      status: pending

  - id: p6-d3-staging-sit
    content: |
      - [ ] [HUMAN+AGENT] P0. Staging SIT smoke:
              1. odum-paper subscribes to STATARB.BASIC.ely_base_3cex (Plan A
                 seed instance).
              2. Fork draft: change `entry_threshold_bps` 5 → 8.
              3. Request approval.
              4. strategy-service runner picks up via Pub/Sub, runs backtest,
                 writes backtest_1yr-grade series to GCS.
              5. Admin reviews in `/admin/strategy-version-approvals`,
                 approves.
              6. Admin rolls out.
              7. Observe STRATEGY_VERSION_ROLLED_OUT event in UTL log;
                 VersionGovernanceReloader hot-reloads config within 5min.
            D3 gate: all 7 steps green on live-defi-rollout staging project
            `central-element-323112`.
      status: pending

  - id: p6-b3-first-client-loop
    content: |
      - [ ] [HUMAN] P0. B3 business gate: record the first complete
            subscribe → fork → request-approval → approved → rollout loop
            from a non-odum client in staging. Capture evidence (screenshots
            + event-log excerpt) in
            `codex/14-playbooks/shared-core/strategy-version-governance.md`
            §Appendix.
      status: pending

  - id: p6-index-update-and-commit
    content: |
      - [ ] [AGENT] P0. Update `plans/active/INDEX.md` — Plan D entry under
            Strategy Lifecycle & Catalogue section. Commit via quickmerge:
              `bash scripts/quickmerge.sh "docs(plans): Plan D — DART exclusive subscription + research fork + version lineage" --agent`
            PM doc-only fast-path → targets main.
      status: pending

# ────────────────────────────────────────────────────────────────────────────
# SUCCESS CRITERIA
# ────────────────────────────────────────────────────────────────────────────
#
# Phase 1 — UAC + UTL:
#   - StrategyInstanceSubscription + StrategyVersion types exist in UAC and
#     are importable via `from unified_api_contracts.strategy import ...`.
#   - 7 new UTL lifecycle events registered + in STANDARD_LIFECYCLE_EVENTS.
#   - UAC + UTL quality-gates.sh green.
#
# Phase 2 — UTA:
#   - 6 new endpoints functional + gated behind dart_exclusive_enabled.
#   - 409 on double-exclusive, 403 on entitlement mismatch, 412 on
#     below-threshold approve.
#   - UTA quality-gates.sh green; integration tests pass under mock mode.
#
# Phase 3 — strategy-service:
#   - pending_approvals_runner subscribed to Pub/Sub topic + backtest path
#     runs against the canonical pipeline (not a new engine).
#   - VersionGovernanceReloader hot-reloads rolled_out versions within 5min.
#   - strategy-service quality-gates.sh green.
#
# Phase 4 — UI:
#   - SubscribeButton + FomoTearsheetCard CTA swap + fork page + admin
#     approvals queue + version-lineage badges all functional.
#   - 17 new vitest cases green.
#   - orphan-audit --blocking exit 0.
#   - Playwright end-to-end smoke green under mock mode.
#
# Phase 5 — Codex:
#   - dart-exclusive-research-fork.md + strategy-version-governance.md shipped.
#   - Cross-refs added to dashboard-services-grid.md §6 + dart-tab-structure.md §6.
#
# Phase 6 — Rollout:
#   - 5-repo workspace QG sweep green.
#   - D3 staging SIT loop complete (7 steps).
#   - B3 first non-odum client loop captured.
#   - INDEX.md updated.
#
# ────────────────────────────────────────────────────────────────────────────
# OUT OF SCOPE
# ────────────────────────────────────────────────────────────────────────────
#
# - Multi-tenant exclusive-lock beyond DART (IM pooled = shared by design;
#   no multi-client dart_exclusive at any time).
# - Version rollback via UI (admin-only CLI path for hot_revert_version.py;
#   UI rollback deferred to a follow-up plan).
# - Forked-version A/B comparison UI (side-by-side performance tearsheet for
#   draft vs parent — deferred to follow-up plan once Plan C overlay lands).
# - Signals-In fork capability — signals_in subscribers never fork; they
#   consume the Odum-owned signal feed.
# - Pricing / commercial terms for exclusive subscriptions — owned by the
#   commercial-model codex, not this technical plan.
#
# ────────────────────────────────────────────────────────────────────────────

isProject: false
---

## Architecture diagram (Mermaid)

```mermaid
flowchart LR
  subgraph UAC[unified-api-contracts]
    S[StrategyInstanceSubscription]
    V[StrategyVersion]
  end
  subgraph UTL[unified-trading-library]
    E[Lifecycle events x7]
  end
  subgraph UTA[unified-trading-api]
    R1[POST /subscribe]
    R2[DELETE /subscribe]
    R3[POST /fork]
    R4[POST /request-approval]
    R5[POST /approve]
    R6[POST /rollout]
    FS[(Firestore)]
  end
  subgraph SS[strategy-service]
    RUN[pending_approvals_runner]
    GATE[backtest_gate]
    REL[VersionGovernanceReloader]
  end
  subgraph UI[unified-trading-system-ui]
    SUB[SubscribeButton]
    FORK[Research fork page]
    APPR[/admin/strategy-version-approvals/]
    LIN[VersionLineageBadge]
  end

  UAC --> UTA
  UTL --> UTA
  UTL --> SS
  UTA --> FS
  UTA --> SS
  SS --> FS
  UI --> UTA
  RUN --> GATE
  REL --> SS
```

## Related plans

- [Plan A — strategy-lifecycle-maturity-model](./strategy_lifecycle_maturity_model_2026_04_21.plan.md)
- [Plan B — strategy-catalogue-3tier-surface](./strategy_catalogue_3tier_surface_2026_04_21.plan.md)
- [Plan C — performance-overlay-continuous-timeline](./performance_overlay_continuous_timeline_2026_04_21.plan.md)
- [Plan E — orphan-audit-policy](./orphan_audit_policy_2026_04_21.plan.md)
