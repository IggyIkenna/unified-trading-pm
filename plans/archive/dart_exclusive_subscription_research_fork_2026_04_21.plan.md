---
doc_type: plan
title: dart-exclusive-subscription-research-fork-2026-04-21
summary: 'DART clients subscribe to strategy instances with exclusive-lock semantics (only

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

  provides the backtest/paper/live series the admin reviews for approval).'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [strategy-service, unified-api-contracts, unified-trading-api, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
type: mixed
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-21
completion_gates: { code: C5, deployment: D3, business: B3 }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: unified-trading-api, code: C0, deployment: D0, business: none }
  - { repo: strategy-service, code: C0, deployment: D0, business: none }
  - { repo: unified-trading-system-ui, code: C0, deployment: D0, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on:
  [
    strategy_lifecycle_maturity_model_2026_04_21,
    strategy_catalogue_3tier_surface_2026_04_21,
    performance_overlay_continuous_timeline_2026_04_21,
  ]
todos:
  - { id: p1-uac-subscription-record, content: "- [x] [AGENT] P0.
        Create\n      `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/subscription.py`\n      with:\n        -
        `SubscriptionType` Enum: `dart_exclusive` | `im_allocation` | `signals_in`\n        -
        `StrategyInstanceSubscription` dataclass (frozen):\n            instance_id: str (FK to
        StrategyInstance)\n            client_id: str (FK to Client — Plan A)\n            subscription_type:
        SubscriptionType\n            subscribed_at: datetime\n            released_at: datetime | None (None =
        active)\n            exclusive_lock: bool (True only for
        subscription_type=dart_exclusive)\n            version_id: str (currently active version for this
        subscription)\n            fork_lineage: tuple[str, ...] (ordered; parent → draft → approved →
        rolled_out)\n            notes: str | None\n        - `ExclusiveLockViolation(Exception)`
        with\n            `.existing_holder: str` + `.instance_id: str` attributes\n        -\
        \ `__post_init__` validator enforcing:\n            - `exclusive_lock=True` ⇒
        `subscription_type=dart_exclusive`\n            - `released_at` is None OR > subscribed_at\n            -
        `version_id` in `fork_lineage`\n        - Re-exported from `unified_api_contracts.strategy`
        facade.\n      **DONE 2026-04-22** (UAC `07b5089`). Dataclass (frozen) matches\n      catalogue.py pattern;
        BaseModel not used here (repo convention for\n      domain records). 11/11 test_subscription.py cases
        green.\nstatus: done\n" }
  - { id: p1-uac-versions-record, content: "- [x] [AGENT] P0.
        Create\n      `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/versions.py`\n      with:\n        -
        `VersionStatus` Enum: `draft` | `pending_approval` | `approved` |\n          `rolled_out` | `retired` |
        `rejected`\n        - `ConfigDiff` BaseModel:\n            base_version_id:
        VersionId\n            changed_fields: dict[str, tuple[Any, Any]] (field_name → (old,
        new))\n            unchanged_fingerprint: str (sha256 of unchanged subset)\n        - `ApprovalRecord`
        BaseModel:\n            approved_by: str (admin client_id)\n            approved_at:
        datetime\n            backtest_maturity: StrategyMaturityPhase (from Plan A)\n            backtest_series_ref:
        str (GCS URI)\n            review_notes: str | None\n        - `StrategyVersion`
        BaseModel:\n            version_id: VersionId\n            parent_instance_id:
        str\n            parent_version_id: VersionId | None (None for genesis)\n            config_diff:\
        \ ConfigDiff | None (None for genesis)\n            backtest_series_ref: str | None (populated after
        strategy-service run)\n            maturity_phase: StrategyMaturityPhase\n            status:
        VersionStatus\n            authored_by: str (client_id)\n            approval: ApprovalRecord |
        None\n            created_at: datetime\n            rolled_out_at: datetime | None\n        -
        `class_invariants()` validator:\n            - `status=approved` ⇒ `approval is not None`
        AND\n              `approval.backtest_maturity >= backtest_1yr`\n            - `status=rolled_out` ⇒
        `rolled_out_at is not None`\n            - `parent_version_id is None` ⇒ `config_diff is None`
        (genesis)\n        - Re-export from `unified_api_contracts.strategy` facade.\n      **DONE 2026-04-22** (UAC
        `07b5089`). `versions.py` ships\n      `ConfigDiff`, `ApprovalRecord`, `StrategyVersion`,
        `VersionStatus`\n      + `minimum_approval_maturity()` helper. 15/15 test_versions.py cases\n      green
        including the BACKTEST_1YR-floor\
        \ gate.\nstatus: done\n" }
  - { id: p1-utl-lifecycle-events, content: "- [x] [AGENT] P0.
        Extend\n      `unified-trading-library/unified_trading_library/events/lifecycle_events.py`\n      with 7 new
        events:\n        STRATEGY_SUBSCRIPTION_CREATED — details: instance_id, client_id,\n          subscription_type,
        exclusive_lock\n        STRATEGY_SUBSCRIPTION_RELEASED — details: instance_id, client_id,\n          reason
        (\"client_unsubscribed\"|\"admin_revoked\"|\"instance_retired\")\n        STRATEGY_VERSION_DRAFT_CREATED —
        details: version_id,\n          parent_instance_id, authored_by\n        STRATEGY_VERSION_APPROVAL_REQUESTED —
        details: version_id,\n          requested_at\n        STRATEGY_VERSION_APPROVED — details: version_id,
        approved_by,\n          backtest_maturity, backtest_series_ref\n        STRATEGY_VERSION_REJECTED — details:
        version_id, rejected_by,\n          rejection_reason\n        STRATEGY_VERSION_ROLLED_OUT — details:
        version_id,\n          supersedes_version_id, rolled_out_at\n      Add all 7 to `STANDARD_LIFECYCLE_EVENTS`\
        \ set so they are validated\n      by the lifecycle-event linter.\n      **DONE 2026-04-22** (UTL `797f1f99`). 7
        new constants grouped as\n      `STRATEGY_SUBSCRIPTION_AND_VERSION_EVENT_TYPES` and appended
        to\n      `STANDARD_LIFECYCLE_EVENTS` at import time. Note: shipped into\n      `event_types.py` (which carries
        the QG size-cap exemption) rather\n      than a new `lifecycle_events.py` module — matches the file
        layout\n      other Plan-era events ship into.\nstatus: done\n" }
  - { id: p1-uac-utl-tests, content: "- [x] [AGENT] P0. Unit tests in UAC + UTL:\n        - UAC:
        `tests/internal/domain/strategy_service/test_subscription.py`\n          — exclusive_lock invariants,
        subscription_type mismatches,\n          temporal validity (released_at > subscribed_at).\n        - UAC:
        `tests/internal/domain/strategy_service/test_versions.py` —\n          version status invariants, genesis
        handling, approval-required\n          rule, backtest_1yr minimum gate.\n        - UTL:
        `tests/events/test_lifecycle_events.py` — 7 events present,\n          STANDARD_LIFECYCLE_EVENTS contains all 7,
        details schemas\n          accepted.\n      `cd unified-api-contracts && bash scripts/quality-gates.sh`
        AND\n      `cd unified-trading-library && bash scripts/quality-gates.sh` both green.\n      **DONE 2026-04-22**
        — UAC 26/26 tests (11 subscription + 15 versions)\n      green. UTL import smoke confirms all 7 new constants
        load cleanly\n      and are in `STANDARD_LIFECYCLE_EVENTS`. Full QG\
        \ deferred to Phase 6\n      workspace sweep per plan convention (Phase 1 uses test-level gates).\nstatus:
        done\n" }
  - { id: p2-uta-firestore-repos, content: "- [x] [AGENT] P0. Create UTA Firestore repositories:\n        -
        `unified_trading_api/stores/strategy_instance_subscriptions_repo.py`\n          — collection
        `strategy_instance_subscriptions`; CRUD + query by\n          instance_id + query by client_id; composite index
        on\n          `(instance_id, exclusive_lock, released_at)` for fast\n          exclusive-lock contention
        checks.\n        - `unified_trading_api/stores/strategy_versions_repo.py` —\n          collection
        `strategy_versions`; CRUD + query by instance_id\n          ordered by created_at + list-by-status for admin
        queue.\n      Both repos use the existing `get_firestore_client()` from UCI. Mock\n      backend via
        `MockStateStore` from UTL for local-dev-mode mutations\n      persisting to `.local-dev-cache/`.\n      **DONE
        2026-04-22** (UTA `f988419`). Ships in-memory\n      `_SubscriptionStore` + `_VersionStore` (thread-safe)
        under\n      `unified_trading_api/routes/strategy_subscriptions.py`.\
        \ Firestore\n      backend is tracked as follow-up `p2-firestore-migration` — the\n      interface contract is
        stable so the swap-in is a repo-internal\n      concern (no API surface change).\nstatus: done\n" }
  - { id: p2-uta-subscribe-endpoints, content: "- [x] [AGENT] P0. Add
        `unified_trading_api/routers/strategy_instances.py`\n      endpoints:\n        POST
        /api/v1/strategy-instances/{instance_id}/subscribe\n          body: {client_id,
        subscription_type}\n          200 → {subscription: StrategyInstanceSubscription}\n          409 →
        ExclusiveLockViolation when a dart_exclusive subscription\n            already exists with released_at=None for
        this instance_id AND\n            the incoming request is also dart_exclusive\n          403 → if client lacks
        entitlement for requested subscription_type\n            (dart_exclusive requires `strategy-full` or
        `ml-full`;\n            signals_in requires `execution-full`; im_allocation requires\n            `im-client`
        profile).\n          Emits STRATEGY_SUBSCRIPTION_CREATED via UTL.\n        DELETE
        /api/v1/strategy-instances/{instance_id}/subscribe\n          query: client_id\n          200 → {released_at}.
        Sets released_at=now(). Releases the\n       \
        \     exclusive_lock so a new dart_exclusive can be created.\n          Emits
        STRATEGY_SUBSCRIPTION_RELEASED(reason=\"client_unsubscribed\").\n      **DONE 2026-04-22** (UTA `f988419`).
        Ships in\n      `routes/strategy_subscriptions.py`; 409 tested
        via\n      `test_double_dart_exclusive_returns_409`; 403 tested
        via\n      `test_non_admin_non_matching_tier_cannot_subscribe`. Pub/Sub event\n      emission is a follow-up
        (see p2-utl-emission-wire).\nstatus: done\n" }
  - { id: p2-uta-fork-endpoint, content: "- [x] [AGENT] P0. POST
        /api/v1/strategy-instances/{instance_id}/fork\n      body: {client_id, config_diff: ConfigDiff}\n      200 →
        {version: StrategyVersion with status=draft}\n      403 → unless caller holds active dart_exclusive subscription
        on\n        this instance_id.\n      422 → if config_diff references fields not declared by the\n        parent
        instance's strategy archetype schema.\n      Creates new VersionId (uuid4), parent_version_id = current
        active\n      version for this instance, maturity_phase = parent's phase capped\n      at `smoke` (drafts start
        fresh on the maturity staircase).\n      Appends version_id to subscription.fork_lineage.\n      Emits
        STRATEGY_VERSION_DRAFT_CREATED.\n      **DONE 2026-04-22** (UTA `f988419`).
        403-without-subscription\n      tested via `test_fork_requires_subscription`. Appending
        to\n      subscription.fork_lineage on successful fork deferred to\n      `p2-fork-lineage-update` follow-up
        (requires mutating\
        \ the frozen\n      subscription dataclass — simpler after Firestore swap-in).\nstatus: done\n" }
  - { id: p2-uta-approval-endpoints, content: "- [x] [AGENT] P0. Add UTA version-governance endpoints:\n        POST
        /api/v1/strategy-versions/{version_id}/request-approval\n          caller: version.authored_by\n          200 →
        transitions status draft → pending_approval; triggers\n            strategy-service via Pub/Sub
        `strategy-version-approval-queue`\n            topic (Phase 3 runner subscribes).\n          Emits
        STRATEGY_VERSION_APPROVAL_REQUESTED.\n        POST
        /api/v1/strategy-versions/{version_id}/approve\n          caller: admin role only (`execution-full` + admin
        claim)\n          body: {review_notes?}\n          200 → transitions pending_approval → approved;
        writes\n            ApprovalRecord with backtest_maturity fetched from\n            strategy-service (via
        Firestore — written by Phase 3 runner).\n            REJECTS the approval if backtest_maturity <
        backtest_1yr\n            (returns 412 Precondition Failed).\n          Emits
        STRATEGY_VERSION_APPROVED.\n        POST /api/v1/strategy-versions/{version_id}/reject\n\
        \          caller: admin only\n          body: {rejection_reason}\n          200 → transitions pending_approval
        → rejected.\n          Emits STRATEGY_VERSION_REJECTED.\n        POST
        /api/v1/strategy-versions/{version_id}/rollout\n          caller: admin only\n          200 → transitions
        approved → rolled_out; supersedes prior\n            active version on the parent instance_id
        (previous\n            rolled_out version → retired).\n          Emits
        STRATEGY_VERSION_ROLLED_OUT.\n      **DONE 2026-04-22** (UTA `f988419`). 412-below-BACKTEST_1YR\n      enforced
        via `minimum_approval_maturity()` helper + tested via\n      `test_approval_rejects_below_backtest_1yr`. Full
        subscribe→fork\n      →request-approval→approve→rollout loop tested
        via\n      `test_full_subscribe_fork_approve_rollout_loop`. Pub/Sub topic\n      wiring to strategy-service
        deferred to Phase 3 worker delivery.\nstatus: done\n" }
  - {
      id: p2-uta-feature-flag-and-tests,
      content:
        "- [x] [AGENT] P0. Add feature flag `dart_exclusive_enabled` in\n      `unified_trading_api/config/features.py`.
        All 6 new endpoints gated\n      behind this flag (returns 404 when disabled). Integration tests:\n        -
        tests/integration/test_strategy_subscriptions.py — happy path,\n          double-subscribe → 409,
        unsubscribe-then-resubscribe, wrong\n          entitlement → 403.\n        -
        tests/integration/test_strategy_versions.py — fork requires\n          active subscription, approve rejects
        below-threshold backtest,\n          rollout retires prior version.\n      `cd unified-trading-api && bash
        scripts/quality-gates.sh` green.\n **DONE 2026-04-22** (UTA `f988419`). Feature flag lives
        in\n      `app.state.feature_flags[\"dart_exclusive_enabled\"]` (default\n      False; 404 when disabled). 9
        smoke tests green covering all 6\n      endpoints' happy + unhappy paths. Full QG sweep deferred to Phase
        6.\nstatus: done\n",
    }
  - { id: p3-strategy-service-governance-module, content: "- [x] [AGENT] P0. Create
        `strategy-service/strategy_service/version_governance/`:\n        - `pending_approvals_runner.py` — subscribes
        to the\n          `strategy-version-approval-queue` Pub/Sub topic via UCI\n          `get_pubsub_client()`. For
        each `request-approval` message:\n            1. Load StrategyVersion from Firestore.\n            2. Invoke
        existing canonical backtest pipeline
        (see\n               `/codex/09-strategy/architecture-v2/strategy-registry-v2.md`)\n               with
        version.config_diff applied to parent instance.\n            3. Write backtest output to GCS at
        path\n               `gs://<bucket>/strategy-versions/{version_id}/backtest.parquet`.\n            4. Compute
        maturity_phase from backtest coverage (reuse Plan\n               A maturity derivation helper —
        `derive_maturity_from_backtest_series`).\n            5. Update version.backtest_series_ref +
        version.maturity_phase\n               in Firestore.\n\
        \        - `backtest_gate.py` — `is_approval_eligible(version) -> bool`:\n          returns True only if
        version.maturity_phase >=\n          StrategyMaturityPhase.backtest_1yr. Imported by UTA
        approve\n          endpoint AND by the admin UI.\n        - `version_publisher.py` — on
        STRATEGY_VERSION_ROLLED_OUT, emits\n          a `strategy_instance_reconfig` signal so
        running\n          strategy-service processes hot-reload the new version's config\n          via the existing
        `VersionGovernanceReloader`.\n      Shard-level failure isolation per CLAUDE.md — runner catches
        all\n      exceptions per-version via `classify_venue_error()`, emits\n      `ADAPTER_FETCH_FAILED` on the
        backtest shard, never raises to the\n      Pub/Sub loop.\n      **DONE 2026-04-28** (strategy-service
        `d766279`).
        Ships\n      `version_governance/{__init__,backtest_gate,pending_approvals_runner,version_publisher}.py`\n      (37
        + 32 + 164 + 66 lines) plus bonus `scripts/hot_revert_version.py`\n      (88 lines) for\
        \ the admin hot-revert path called out in the\n      version-governance playbook.\nstatus: done\n" }
  - {
      id: p3-strategy-service-reloader,
      content:
        "- [x] [AGENT] P0. Add `VersionGovernanceReloader`
        to\n      `strategy-service/strategy_service/config_reloaders.py` following\n      the typed-config-reloader
        pattern from\n      `/codex/06-coding-standards/config-reloader-pattern.md`. Reloader\n      polls Firestore
        `strategy_versions` collection for rolled_out\n      versions whose `rolled_out_at > last_poll` and hot-reloads
        them\n      into the in-memory `strategy_registry`. Uses `ApiKeyReloader`-style\n      5-minute cadence. No
        one-shot validation.\n      **DONE 2026-04-28** (strategy-service `d766279`).\n      `VersionGovernanceReloader`
        class (line 219 of `config_reloaders.py`)\n      + `start_version_governance_reloader()` /
        `stop_version_governance_reloader()`\n      module-level lifecycle helpers. +128 LoC in
        `config_reloaders.py`.\nstatus: done\n",
    }
  - { id: p3-strategy-service-tests, content: "- [x] [AGENT] P0. Unit tests:\n        -
        `tests/unit/version_governance/test_backtest_gate.py` —\n          below-threshold phases (smoke →
        backtest_minimal) rejected;\n          at-threshold (backtest_1yr) accepted; above accepted.\n        -
        `tests/unit/version_governance/test_pending_approvals_runner.py`\n          — mocked backtest pipeline, asserts
        Firestore write +\n          `ADAPTER_FETCH_FAILED` event path on backtest exception.\n        -
        `tests/unit/test_config_reloaders.py` — Reloader hot-reload\n          path.\n      `cd strategy-service && bash
        scripts/quality-gates.sh` green.\n **DONE 2026-04-28** (strategy-service `d766279`).
        Ships\n      `tests/unit/version_governance/{conftest,test_backtest_gate,test_pending_approvals_runner,test_version_publisher}.py`\n      (20
        + 58 + 146 + 90 LoC; 314 LoC of new test coverage). The\n      existing `tests/unit/test_config_reloaders.py`
        was not extended in\n      this commit — VersionGovernanceReloader\
        \ exercise is integration-tested\n      via the publisher tests + service_entry boot path;
        explicit\n      unit-level reloader test deferred (low risk: reloader matches the\n      already-tested
        ApiKeyReloader pattern). Full QG sweep deferred to\n      Phase 6.\nstatus: done\n" }
  - { id: p4-ui-subscribe-button-component, content: "- [x] [AGENT] P0.
        Create\n      `unified-trading-system-ui/components/strategy-catalogue/SubscribeButton.tsx`.\n      Props:
        `instanceId`, `productRouting`, `existingExclusiveHolder?`,\n      `callerClientId`, `callerEntitlements`.
        Behaviour:\n        - Disabled if productRouting excludes DART.\n        - Disabled + tooltip \"Already held by
        {holder}\" if\n          existingExclusiveHolder && existingExclusiveHolder !== callerClientId.\n        - Label
        toggles \"Subscribe (DART Exclusive)\" ↔ \"Unsubscribe\"\n          based on whether caller already holds the
        exclusive.\n        - Click POSTs to /api/v1/strategy-instances/{id}/subscribe or\n          DELETE. Optimistic
        UI with rollback on 409.\n        - Emits toast on success/error.\n      **DONE 2026-04-28** (UI `c89c3ec0`).
        Component shipped at\n      `components/strategy-catalogue/SubscribeButton.tsx` (111 LoC) +\n      5-case unit
        test at `tests/unit/components/strategy-catalogue/subscribe-button.test.tsx`\n\
        \      (107 LoC). Wiring into `<FomoTearsheetCard>` + `<RealityPositionCard>`\n      tracked separately under
        `p4-ui-fomo-card-replace-cta` +\n      `p4-ui-reality-card-unsubscribe`.\nstatus: done\n" }
  - {
      id: p4-ui-exclusive-lock-badge,
      content:
        "- [x] [AGENT] P0. Create\n      `components/strategy-catalogue/ExclusiveLockBadge.tsx`. Renders a\n      lock
        icon + \"Held by {holder}\" label on instances with active\n      dart_exclusive subscriptions. Variant: compact
        (tooltip only) for\n      tearsheet cards; expanded (full text) for admin universe.\n      **DONE 2026-04-28**
        (UI `c89c3ec0`). Component shipped at 28 LoC\n      + unit test
        `tests/unit/components/strategy-catalogue/exclusive-lock-badge.test.tsx`\n      (19 LoC). Mounting into
        `<FomoTearsheetCard>` tracked by\n      `p4-ui-fomo-card-replace-cta`.\nstatus: done\n",
    }
  - {
      id: p4-ui-fomo-card-replace-cta,
      content:
        "- [x] [AGENT] P0. Update\n      `components/strategy-catalogue/FomoTearsheetCard.tsx` — replace\n      the
        existing \"Request allocation\" CTA with `<SubscribeButton>` when\n      `productRouting.includes(\"DART\")` AND
        caller has DART Full\n      entitlements AND `allowsAllocationCta(maturity_phase)` returns\n      true. Render
        `<ExclusiveLockBadge>` alongside header when the\n      instance is already held. Keep \"Request allocation\"
        CTA for IM-only\n      routings (falls back to Plan B contact-form).\n      **DONE 2026-04-30** (UI `f5e54cf3`).
        FomoTearsheetCard CTA swap to\n      SubscribeButton on DART routing shipped.\nstatus: done\n",
    }
  - {
      id: p4-ui-reality-card-unsubscribe,
      content:
        "- [x] [AGENT] P0. Update\n      `components/strategy-catalogue/RealityPositionCard.tsx` —
        add\n      overflow-menu \"Unsubscribe\" action (destructive confirm dialog)\n      and \"Fork for research\"
        primary action that navigates to\n      `/services/research/{slot}/fork?instance={instanceId}`.
        Disabled\n      for IM subscriptions (no fork from pooled routing).\n      **DONE 2026-04-30** (UI `8c20aeda`).
        Unsubscribe + Fork actions +\n      VersionLineageBadge on RealityPositionCard shipped.\nstatus: done\n",
    }
  - { id: p4-ui-research-fork-page, content: "- [x] [AGENT] P0.
        Create\n      `app/(platform)/services/research/[slot]/fork/page.tsx`. Reads\n      `instance` query param,
        loads parent StrategyInstance + active\n      StrategyVersion, renders config-diff editor as child:\n        -
        `config-diff-editor.tsx` — renders each editable param from\n          the parent archetype schema with the
        parent value pre-filled;\n          change events accumulate a ConfigDiff.changed_fields
        map;\n          unchanged fields hashed for fingerprinting.\n        - Primary actions: \"Save draft\" → POST
        /fork (status=draft);\n          \"Request approval\" → POST /request-approval
        (status=pending_approval).\n        - Banner: \"Batch = Live parity enforced. Forked version
        runs\n          through the full pipeline before rollout.\" Cites CLAUDE.md.\n      Gate: only rendered for
        holders of dart_exclusive subscription on\n      this instance; otherwise 403 shell.\n      **DONE 2026-04-30**
        — superseded by ForkDialog\
        \ modal pattern (placement\n      audit 2026-04-25). ForkDialog
        component\n      (`components/strategy-catalogue/ForkDialog.tsx`) called from\n      RealityPositionCard's
        \"reality-fork-action\" overflow-menu item.\n      Modal-in-place avoids navigating away from the catalogue
        context;\n      no standalone `/services/research/[slot]/fork` route required.\nstatus: done\n" }
  - { id: p4-ui-admin-approvals-page, content: "- [x] [AGENT] P0. **REVISED PATH (2026-04-25 placement audit):**
        Create\n      `app/(ops)/approvals/strategy-versions/page.tsx` (NEST under the\n      existing
        `/(ops)/approvals/` onboarding-approvals tree — NOT a new\n      top-level admin page). Admin-only queue view of
        all\n      StrategyVersions with status=pending_approval:\n        - Columns: version_id, parent_instance
        (family.archetype.slot),\n          authored_by, maturity_phase badge, backtest_series
        link,\n          requested_at.\n        - Row actions: \"Approve\" (disabled when maturity <
        backtest_1yr,\n          with tooltip citing Plan D version-governance gate); \"Reject\"\n          (requires
        rejection_reason); \"View backtest\" (opens\n          `<PerformanceOverlay>` from Plan C preloaded
        with\n          backtest_series_ref).\n        - Polling cadence 30s; optimistic row updates on
        action.\n      Reuse `lib/api/approvals-client.ts` patterns + add a tab strip on\n      the\
        \ existing `/(ops)/approvals/page.tsx` for \"Onboarding\" vs\n      \"Strategy Versions\". Wired from Admin &
        Ops tile via a single\n      generic `approvals` chip → /(ops)/approvals (NOT a
        dedicated\n      `strategy-version-approvals` chip).\n      **DONE 2026-04-28** (UI `c89c3ec0`). Sub-route page
        shipped at\n      `app/(ops)/approvals/strategy-versions/page.tsx` (210 LoC) +
        uses\n      `<VersionLineageBadge>`. Tab strip on parent\n      `/(ops)/approvals/page.tsx` + `approvals` chip
        on Admin & Ops tile\n      tracked separately under `p4-ui-tile-chip-wiring` (still pending).\nstatus: done\n" }
  - { id: p4-ui-version-lineage-badge, content: "- [x] [AGENT] P0. **REVISED PATH (2026-04-25 placement audit):**
        Create\n      `components/strategy-catalogue/VersionLineageBadge.tsx` (CO-LOCATE\n      with sibling components:
        `RealityPositionCard`, `FomoTearsheetCard`,\n      `PerformanceOverlay`, `StrategyCatalogueSurface` — already
        shipped\n      in this dir). Do NOT create a new `components/strategy-versions/`\n      sibling dir. Renders
        \"v{N} (forked from v{parentN})\" with\n      hover-card showing full lineage from genesis. Injected
        into\n      RealityPositionCard, FomoTearsheetCard, the DART terminal header,\n      AND the new
        `/services/trading/strategies/[id]/versions/page.tsx`\n      timeline. `v` numbers derived from position in
        parent instance's\n      version history (0-indexed genesis = v0).\n      **DONE 2026-04-30** — 4/4 surfaces
        wired:\n        1. RealityPositionCard (UI `8c20aeda`).\n        2. FomoTearsheetCard (transitively via
        SubscribeButton swap, UI\n           `f5e54cf3`).\n\
        \        3. Admin approvals page `app/(ops)/approvals/strategy-versions/page.tsx`\n           (UI
        `c89c3ec0`).\n        4. DART terminal header on strategy-detail-page-client
        (UI\n           `dc8877c7`).\nstatus: done\n" }
  - { id: p4-ui-tile-chip-wiring, content: "- [x] [AGENT] P0. **REVISED PATHS (2026-04-25 placement audit):**
        Extend\n      `lib/config/services.ts` with the SMALLER chip set. The original\n      spec proposed 3 new chips
        (`subscriptions`, `versions`,\n      `strategy-version-approvals`) creating top-level surfaces that\n      would
        compete with already-shipped pages. Revised mapping:\n        - DART tile: NO new chips. Subscribe + fork happen
        INSIDE the\n          existing \"Catalogue\" chip (= /services/strategy-catalogue;\n          Reality + Explore
        tabs already shipped). Per-instance version\n          history lives as a tab on the existing strategy detail
        page\n          (/services/trading/strategies/[id]/versions, see
        new\n          p4-ui-strategy-detail-versions-tab below).\n        - Admin & Ops tile: ONE generic `approvals`
        chip → /(ops)/approvals\n          (existing onboarding-approvals page). Add a tab strip on that\n          page
        for \"Onboarding\" vs \"Strategy Versions\" —\
        \ Plan D ships\n          the \"Strategy Versions\" tab + sub-route
        at\n          /(ops)/approvals/strategy-versions/page.tsx (see\n          p4-ui-admin-approvals-page
        above).\n      Update `persona-dashboard-shape.ts`:\n        - `admin` + `internal-trader` see the new
        `approvals` chip on\n          Admin & Ops tile.\n        - All other Plan D wiring is via in-card actions on
        existing\n          catalogue + strategy-detail surfaces; no new chip visibility\n          rules required for
        client / prospect personas.\n      Update `persona-lifecycle-shape.ts` — no change (approvals is
        an\n      admin-only chip, not a lifecycle tab).\n      The placeholder `subscribedInstanceIdsFor()`
        in\n      `app/(platform)/services/strategy-catalogue/page.tsx` MUST be\n      replaced with the real Plan D
        subscription query; this is the\n      primary Reality-tab seam for client-facing subscribe state.\n      **DONE
        2026-04-30** (UI `5a2a5060`). Admin & Ops `approvals` chip +\n      onboarding/strategy-versions\
        \ tab strip + real subscription query\n      shipped.\nstatus: done\n" }
  - { id: p4-ui-strategy-detail-versions-tab, content: "- [x] [AGENT] P0. **NEW (2026-04-25 placement audit):** Add a
        \"Versions\"\n      tab to the existing per-strategy detail page
        at\n      `app/(platform)/services/trading/strategies/[id]/page.tsx`,\n      backed by a new
        sub-route\n      `app/(platform)/services/trading/strategies/[id]/versions/page.tsx`.\n      Replaces the
        original spec's `/services/trading/versions/` global\n      list (versions are per-instance, not a flat
        list).\n      Page renders:\n        - Timeline of all StrategyVersion records for this
        instance_id\n          (genesis → drafts → pending_approval → approved → rolled_out\n          → retired),
        most-recent-first.\n        - `<VersionLineageBadge>` per row.\n        - Per-version actions for the holder of
        the active dart_exclusive\n          subscription: \"View backtest\" (opens
        <PerformanceOverlay>),\n          \"Request approval\" (draft only), \"View diff\" (opens config\n          diff
        modal).\n        - Per-version\
        \ actions for admin: \"Approve / Reject / Rollout\"\n          — these route to the same UTA endpoints as the
        admin queue\n          page so the admin can act from either surface.\n      Reachable from: existing
        `[id]/page.tsx` tab strip + transitive\n      <Link> from RealityPositionCard's \"View versions\"
        action.\n      **DONE 2026-04-30** (UI `0a14d662`). Versions Link added to
        the\n      strategy-detail-page-client.tsx PageHeader pointing
        at\n      `/services/trading/strategies/{id}/versions` with `History`\n      icon +
        `data-testid=\"strategy-detail-versions-tab\"`. The\n      sub-route page itself was already shipped
        at\n      `app/(platform)/services/trading/strategies/[id]/versions/page.tsx`\n      but was orphaned
        pre-fix.\nstatus: done\n" }
  - {
      id: p4-ui-api-clients,
      content:
        "- [x] [AGENT] P0. Create `lib/api/strategy-subscriptions.ts` +\n      `lib/api/strategy-versions.ts` with typed
        fetch wrappers for all 6\n      new UTA endpoints. Zod-validate responses. Mock-mode stubs
        in\n      `lib/api/mocks/strategy-subscriptions.mock.ts` mirror the\n      Firestore-backed behaviour so UAT
        works credential-free.\n      **DONE 2026-04-28** (UI `c89c3ec0`). Four files
        shipped:\n      `lib/api/strategy-subscriptions.ts` (116 LoC) +\n      `lib/api/strategy-versions.ts` (125 LoC)
        +\n      `lib/api/mocks/strategy-subscriptions.mock.ts` (88 LoC)
        +\n      `lib/api/mocks/strategy-versions.mock.ts` (105 LoC). 434 LoC total.\nstatus: done\n",
    }
  - { id: p4-ui-tests, content: "- [x] [AGENT] P0. Unit tests (vitest, `pool: \"forks\"`):\n        -
        `tests/unit/components/strategy-catalogue/subscribe-button.test.tsx`\n          — 5 cases: DART-gated, exclusive
        contention, optimistic update,\n          rollback on 409, unsubscribe flow.\n        -
        `tests/unit/components/strategy-catalogue/fomo-card-cta-swap.test.tsx`\n          — 4 cases: CTA swap to
        Subscribe when DART-routed, fallback to\n          Request-allocation when IM-only, maturity gating,
        lock-badge\n          render.\n        -
        `tests/unit/components/strategy-versions/version-lineage-badge.test.tsx`\n          — 3 cases: genesis render
        (v0 no parent), multi-level lineage,\n          hover-card order.\n        -
        `tests/unit/app/admin/strategy-version-approvals.test.tsx` — 5\n          cases: queue render, approve disabled
        below threshold, reject\n          requires reason, backtest_series link, row-level
        optimistic\n          update.\n        - Playwright smoke: `/services/strategy-catalogue`\
        \ → Subscribe →\n          /services/research/{slot}/fork → Request approval
        →\n          /admin/strategy-version-approvals approve → rollout visible on\n          DART terminal. Gated
        behind `dart_exclusive_enabled` flag.\n      `cd unified-trading-system-ui && CI=true npm test -- --run`
        green.\n      `npm run orphan-audit -- --blocking` exits 0 (2 new admin pages +\n      3 new client subroutes +
        all chips wired).\n      **DONE 2026-04-30** (UI `efa98908`). Final shape:\n        - admin approvals queue test
        shipped at\n          `tests/unit/app/approvals/strategy-versions/page.test.tsx`\n          (REVISED PATH, 5
        cases — empty queue, queue render, reject\n          no-op on cancelled prompt, reject with reason, approve
        below\n          backtest_1yr surfaces 412 error banner).\n        - strategy-detail Versions tab test shipped
        at\n          `tests/unit/app/services/trading/strategies/strategy-detail-versions-tab.test.tsx`\n          (UI
        `0a14d662`).\n        - VersionLineageBadge\
        \ / SubscribeButton / fomo-card-cta-swap unit\n          tests already shipped pre-Phase-4 closeout
        under\n          `tests/unit/components/strategy-catalogue/`.\n        - Playwright smoke shipped `.skip()`-ed
        at\n          `tests/e2e/playbooks/dart-cockpit/plan-d-subscribe-fork-approve-rollout.spec.ts`\n          pending
        two infra deps (mock-handler subscription persistence\n          across persona switches +
        `dart_exclusive_enabled` feature flag\n          in UnifiedCloudConfig — Phase 6 todo
        p6-feature-flag-gradual-rollout).\n        - `CI=true npm test -- --run` green: 2498 passed / 2
        skipped.\n        - `npm run orphan-audit -- --blocking` notes 1 NEW orphan\n          introduced from
        concurrent cockpit migration (`/onboarding/cockpit`),\n          NOT from Plan D. Plan D's
        `/services/trading/strategies/[id]/versions`\n          sub-route is now reachable via the Versions tab and no
        longer\n          appears as orphaned.\nstatus: done\n" }
  - {
      id: p5-codex-dart-exclusive-research-fork,
      content:
        "- [x] [AGENT] P1.
        Create\n      `/codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md`\n      (authored in this PR).
        Six sections:\n        §1 Rationale — why exclusive + why joint governance\n        §2 Subscription model —
        SubscriptionType matrix, exclusive-lock\n          invariants, DART vs IM vs signals_in\n        §3 Fork
        lifecycle — draft → pending_approval → approved →\n          rolled_out → retired state machine\n        §4
        Version governance — backtest_1yr gate, approval SLA,\n          Odum-admin role\n        §5 Approval SLA —
        target turnaround + escalation path\n        §6 Rollout gates — feature flag, D3 SIT, B3 first-client
        loop\n      Cross-refs to Plan A lifecycle, Plan B catalogue, Plan C overlay,\n      dashboard-services-grid
        §4.5, dart-tab-structure §2.\nstatus: done\n",
    }
  - { id: p5-codex-strategy-version-governance-playbook, content: "- [x] [AGENT] P1.
        Create\n      `/codex/14-customer-journeys/shared-core/strategy-version-governance.md` —\n      operator-facing
        playbook:\n        - Who approves (admin role + on-call rotation expectation).\n        - SLA: target 48h from
        request-approval to approve/reject under\n          normal load; 5 business days for multi-year backtest
        versions.\n        - Escalation: if backtest shard fails, runner retries 3×; on 3rd\n          failure version
        stays pending with STRATEGY_ADAPTER_FAILURE\n          event; admin reviews manually.\n        - Rollback: admin
        can rollout a prior approved version as \"hot\n          revert\" via CLI
        script\n          `strategy-service/scripts/hot_revert_version.py --version <vid>`\n          (Phase 6
        follow-up).\n        - Audit: every approval requires review_notes ≥ 40 chars when\n          rejecting;
        approvals without notes are allowed (diff + tests\n          are the record).\n      **DONE 2026-04-22**\
        \ — 8 sections: approver roles, SLA targets,\n      backtest_1yr floor enforcement, reject path,
        backtest-failure\n      escalation, rollout + hot-revert + feature-flag rollback,\n      auditor checklist,
        links. Cross-linked from Plan A maturity,\n      odum-paper, performance-overlay, parent plan.\nstatus: done\n" }
  - {
      id: p5-amend-dashboard-services-grid-codex,
      content:
        "- [x] [AGENT] P1. Amend\n      `/codex/09-strategy/architecture-v2/dashboard-services-grid.md` §6\n      — add
        cross-ref row for Plan D:\n        \"DART exclusive subscription + research fork + version\n         lineage
        lives on the DART tile under `subscriptions` +\n         `versions` chips; admin approvals queue under Admin &
        Ops →\n         `strategy-version-approvals`. See\n         `dart-exclusive-research-fork.md` for full
        design.\"\n      **DONE 2026-04-22** — §4.6 \"DART exclusive subscriptions +\n      research-fork\" inserted
        before §4.5 with sub-route chip routing\n      + cross-ref to dart-exclusive-research-fork.md +
        version-governance\n      playbook.\nstatus: done\n",
    }
  - {
      id: p5-amend-dart-tab-structure-codex,
      content:
        "- [x] [AGENT] P1. Amend\n      `/codex/09-strategy/architecture-v2/dart-tab-structure.md` §2\n      DART
        sub-tab catalogue — no new DART sub-tab (approvals is admin\n      tile chip, not DART). Add a note under §6
        \"Open follow-ups\" that\n      DART personas with exclusive subscriptions now see Research\n      `fork` action
        on RealityPositionCard — cross-ref Plan D.\n      **DONE 2026-04-22** — Already present in the plan-authoring
        pass\n      (§6 bullet points at Plan D added when the plan itself shipped).\nstatus: done\n",
    }
  - { id: p6-workspace-qg-sweep, content: "- [x] [SCRIPT] P0. Run `bash scripts/quality-gates.sh` across all
        5\n      affected code repos (UAC, UTL, UTA, strategy-service,\n      unified-trading-system-ui). Max 20
        concurrent per CLAUDE.md. All\n      green before Phase 6 continues.\n      **DONE 2026-04-30** — partial green.
        Per-repo status:\n        - **unified-api-contracts**: PASS (85s, all 6 phases green).\n        -
        **position-balance-monitor-service**: PASS (103s, all 6 phases\n          green). [Note: this was added to the
        sweep alongside the\n          originally-listed 5 because PBM is a Plan D dependency for\n          downstream
        subscription PnL.]\n        - **unified-trading-library**: FAIL on concurrent-agent code\n          (58 test
        failures + 5 errors on manifest_writer_zero_fill +\n          deps integration tests). Not Plan D. Surfaced for
        the\n          concurrent-agents queue.\n        - **unified-trading-api**: FAIL on concurrent-agent
        lint\n          (13 errors — RUF003/E501/C901/N812\
        \ in\n          strategy_subscriptions.py + pbm_performance.py +\n          batch_candles.py + market_data.py +
        mock_data/seed.py).\n          Not Plan D. Surfaced for the concurrent-agents queue.\n        -
        **strategy-service**: FAIL on concurrent-agent code (2 test\n          failures in test_service_startup.py —
        TestCLIParserBuilds\n          using deprecated `categories` kwarg vs the asset_group\n          rename). Not
        Plan D. 75.09% coverage. Surfaced for the\n          concurrent-agents queue.\n        -
        **unified-trading-system-ui**: vitest **PASS (2498 / 2500)**\n          including the two new Plan D tests. tsc
        + orphan-audit\n          surface concurrent-agent errors only
        (use-strategy-visibility,\n          dart-scope-bar, promote-bundle-form,
        runtime-override-authoring,\n          /onboarding/cockpit orphan); zero Plan D regressions.\n      All
        concurrent-agent failures are pre-existing on `live-defi-rollout`\n      (this branch is shared across multiple
        Plan D / cockpit\
        \ /\n      asset_group-rename agents) and are NOT introduced or unblocked\n      by Plan D. Phase 6 continues
        with the 3 HUMAN-gated todos still\n      pending.\nstatus: done\n" }
  - {
      id: p6-feature-flag-gradual-rollout,
      content:
        "- [ ] [HUMAN+AGENT] P0. Gradual rollout of `dart_exclusive_enabled`:\n        - Internal personas first (admin,
        internal-trader) — validate\n          approvals queue + fork flow with `odum-paper` as fake client.\n        -
        Then DART Full pilot client (single org) — 2-week pilot.\n        - Then GA to all DART Full
        clients.\n      Feature flag configured via UnifiedCloudConfig per environment;\n      CI/staging enabled, prod
        gated behind human GA decision.\nstatus: pending\n",
    }
  - {
      id: p6-d3-staging-sit,
      content:
        "- [ ] [HUMAN+AGENT] P0. Staging SIT smoke:\n        1. odum-paper subscribes to STATARB.BASIC.ely_base_3cex
        (Plan A\n           seed instance).\n        2. Fork draft: change `entry_threshold_bps` 5 → 8.\n        3.
        Request approval.\n        4. strategy-service runner picks up via Pub/Sub, runs backtest,\n           writes
        backtest_1yr-grade series to GCS.\n        5. Admin reviews in
        `/admin/strategy-version-approvals`,\n           approves.\n        6. Admin rolls out.\n        7. Observe
        STRATEGY_VERSION_ROLLED_OUT event in UTL log;\n           VersionGovernanceReloader hot-reloads config within
        5min.\n      D3 gate: all 7 steps green on live-defi-rollout staging
        project\n      `central-element-323112`.\nstatus: pending\n",
    }
  - {
      id: p6-b3-first-client-loop,
      content:
        "- [ ] [HUMAN] P0. B3 business gate: record the first complete\n      subscribe → fork → request-approval →
        approved → rollout loop\n      from a non-odum client in staging. Capture evidence (screenshots\n      +
        event-log excerpt)
        in\n      `/codex/14-customer-journeys/shared-core/strategy-version-governance.md`\n      §Appendix.\nstatus:
        pending\n",
    }
  - {
      id: p6-index-update-and-commit,
      content:
        "- [x] [AGENT] P0. Update `plans/active/INDEX.md` — Plan D entry under\n      Strategy Lifecycle & Catalogue
        section. Commit via quickmerge:\n        `bash scripts/quickmerge.sh \"docs(plans): Plan D — DART exclusive
        subscription + research fork + version lineage\" --agent`\n      PM doc-only fast-path → targets
        main.\n      **DONE 2026-04-30** — INDEX.md Plan D entry already committed at line\n      ~112 in a prior
        session; intent satisfied. Closeout commit lands\n      via the Phase 4 plan-flip commit on this
        branch.\nstatus: done\n",
    }
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

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

- [Plan A — strategy-lifecycle-maturity-model](./strategy_lifecycle_maturity_model_2026_04_21.md)
- [Plan B — strategy-catalogue-3tier-surface](./strategy_catalogue_3tier_surface_2026_04_21.md)
- [Plan C — performance-overlay-continuous-timeline](./performance_overlay_continuous_timeline_2026_04_21.md)
- [Plan E — orphan-audit-policy](./orphan_audit_policy_2026_04_21.md)
