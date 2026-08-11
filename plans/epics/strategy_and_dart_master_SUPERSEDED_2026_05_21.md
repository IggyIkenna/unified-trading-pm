---
doc_type: epic
title: Strategy + DART Master (umbrella)
summary: >-
  SUPERSEDED 2026-05-21 archaeology-only umbrella: the pre-split epic that folded strategy_architecture_v2,
  dart_ux_cockpit_refactor, and consolidated_strategy_and_ui into one SSOT. Split into strategy_master.md (L2,
  archetype/allocator/risk/pnl) and dart_and_promote_master.md (L3, DART operator UX + promote workflow) — do not add
  new work here; new plans declare the split parent_epic.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, e2e-testing, execution-service, features-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, refactor, consolidation, promote, ui, ssot-audit]
[/plans/epics/strategy_master.md, /plans/epics/dart_and_promote_master.md, /plans/epics/README.md]
created: 2026-05-07
name:
tier:
priority:
assigned_vm: vm-trading-core
parent:
co_operators:
codex_ssots:
related_plans:
deadline: 2026-05-23 (live DeFi) — only manual-trade gate verification + Group F prereq parts; rest post-May-23
owner_repos:
  [
    unified-api-contracts,
    unified-trading-library,
    strategy-service,
    execution-service,
    position-balance-monitor-service,
    ml-inference-service,
    features-delta-one-service,
    features-onchain-service,
    features-cross-instrument-service,
    market-tick-data-service,
    unified-trading-system-ui,
    unified-trading-api,
  ]
folds_in:
  [
    plans/archive/strategy_architecture_v2_finalization_2026_04_19.md,
    plans/archive/dart_ux_cockpit_refactor_2026_04_29.md,
    plans/archive/consolidated_strategy_and_ui_2026_04_15.md,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Strategy + DART Master — SUPERSEDED 2026-05-21

> **⚠️ SUPERSEDED-BY 2026-05-21**: This umbrella was split into two everlasting epics per the epic consolidation:
>
> - **Strategy archetype + allocator + risk/position/pnl scope** → [`strategy_master.md`](strategy_master.md) (L2)
> - **DART operator UX + promote workflow + state machine scope** →
>   [`dart_and_promote_master.md`](dart_and_promote_master.md) (L3)
>
> This file is kept as **archaeology only** — DO NOT add new work here. New active plans assigned to the split scopes
> declare `parent_epic: strategy_master` OR `parent_epic: dart_and_promote_master` in their frontmatter. Full epic-flow
> SSOT: [`README.md`](README.md).

> **Consolidation 2026-05-07** (historical): this umbrella folded 3 previously-standalone plans
> (strategy_architecture_v2_finalization / dart_ux_cockpit_refactor / consolidated_strategy_and_ui) into one SSOT
> covering archetype lifecycle (engine v2 finalization), DART operator UX cockpit, and cross-domain alpha + UI
> walkthrough. Source plans archived with ARCHIVED banner; all open todos preserved in Phase 1-3 below.

> **📋 RELATED PLAN — Promote workflow (May-23 dual-track + post-cutover, spawned 2026-05-10)**: the audit-driven
> promote workflow plans
> ([`promote_workflow_may23_cli_path_2026_05_10`](../active/promote_workflow_may23_cli_path_2026_05_10.md) dual-track
>
> - [`promote_workflow_post_cutover_ui_pipeline_2026_05_10`](../active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
>   extension) ship the cutover-blocker UI track that this umbrella's DART scope depends on. **BE AWARE** when touching
>   `unified-trading-system-ui/components/promote/*` (Promote workflow context + flow modal — owned by May-23 plan Phase
>   U4 wiring), `unified-trading-system-ui/components/shell/dart-scope-bar.tsx` (3-way visualization owner is May-23
>   Phase U5 = `pvl-p23a`), or any `ManualTradeGateDialog` work (May-23 Phase U6 = `pvl-p23c`). Post-cutover plan Phase
>   1 also consolidates 4 competing UAC lifecycle SSOTs (`StrategyMaturityPhase` chosen canonical) — coordinate Phase 1
>   strategy-service `availability/store.py` migration with this umbrella's archetype lifecycle Phase 1 work. Question
>   doc:
>   [`plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md`](../questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md).

## Scope

This umbrella is the SSOT for three previously-parallel work-streams that all converge on the operator surface and the
strategy lifecycle:

1. **Archetype engine v2 finalization** (was `strategy_architecture_v2_finalization`) — the factory cutover from legacy
   strategies to the v2 archetype + 4-layer-risk model, the shadow deployment registry + ledger, the 18-archetype shadow
   observation period, and the capability-gap close-out (multi-venue SOR, hold-policy mixin, transfer-rebalance
   integration, benchmark-fills, dated-future roll mechanism, IM/Trading allocator split). Most of this is post-May-23;
   the parts that block live DeFi are minimal.

2. **DART operator UX cockpit** (was `dart_ux_cockpit_refactor`) — the 9-phase programme that collapses DART from a
   route tree into a guided cross-asset trading cockpit. **Substantively shipped**: all 9 phases + Configuration
   lifecycle UI surfaces + persona walkthrough Playwright matrix + Phase 1A/1B foundational primitives. **7 open polish
   items remain**: widget vocabulary SSOT, cross-cutting widget conventions, Layer-2 minimum proof signals, v2
   archetype-expansion roadmap (HUMAN), doc alignment (HUMAN), IR copy alignment (HUMAN), public website copy alignment
   (HUMAN).

3. **Cross-domain alpha + UI walkthrough** (was `consolidated_strategy_and_ui`) — the residual from 5 source plans
   (cross_domain_alpha_execution_intelligence, strategy_lifecycle_visibility_ui, client_config_and_defi_risk,
   ui_walkthrough_and_e2e_alignment, ui_sync_hardening). Strategy lifecycle Phase 1 + microstructure features have
   shipped; cross-domain alpha core (UAC schemas
   - UTL SLA engine + DataQualityScorer + cross-domain calc + DeFi alpha features + execution cost prediction + unified
     CeFi+DeFi SOR) is genuinely-open net-new work.

The 3 source plans had heavy scope overlap on (a) DART scope/ack panels + per-strategy detail page (Strategy Catalogue
Phase 10 in v2-finalization fed the dart-cockpit Phase 5 widgets fed the consolidated-strategy-and-ui
slv-p3-research-shell), (b) archetype availability + lock state metadata + RBAC (Phase 10.5 in v2-finalization fed the
dart-cockpit Phase 1A StrategyAvailabilityResolver fed slv-p3-ml-dashboard), and (c) UI walkthrough audit + batch=live
verification (Phase 10.6 service-split in v2-finalization fed the dart-cockpit persona-walkthrough matrix fed
ui-1a-walkthrough-audit + ui-2a-batch-live in consolidated). One umbrella resolves the cross-references.

## Codex SSOTs

- [`codex/09-strategy/architecture-v2/`](../../codex/09-strategy/architecture-v2/) — strategy v2 SSOT (README +
  MIGRATION + 18 archetypes + 7 axes + 11 cross-cutting + 2 architecture docs)
- [`codex/14-customer-journeys/dart/`](../../codex/14-customer-journeys/dart/) — DART terminal vs research playbook
  (paired SSOT for the cockpit refactor)
- [`/codex/04-architecture/shadow-deployment-pattern.md`](/codex/04-architecture/shadow-deployment-pattern.md) — shadow
  window contract for archetype builds

## Phase 1 — Archetype engine v2 finalization (was: strategy_architecture_v2_finalization)

> Source plan: `plans/archive/strategy_architecture_v2_finalization_2026_04_19.md`. Phase 1 (factory cutover Tier 2 —
> 1a/1b/1c/1d/1e/1f), Phase 2 (shadow persistence — registry + ledger + events + codex doc + tests), Phase 7
> (NEEDS_REVIEW resolutions), Phase 8 (test flakes), and Phase 9 (coverage matrix SSOT) are SHIPPED — see source archive
> for [x] evidence. Phase 10 master matrix + combinatoric discovery + block-list browser + per-strategy detail +
> reusable chip primitives + service landing page + 45 vitest are SHIPPED. Phase 10.5 UAC registry + events + watchdog +
> allocator enforcement + admin toggle UI + badges + 56 unit tests are SHIPPED.
>
> **Phase 3 source items (4 OPS items: start shadow clock / weekly EXTEND-REJECT review / wait for PROMOTE / human
> triggers `promote_to_prod()`)** are DROPPED per audit verdict — V1-RETIRE bypassed shadow window per operator
> directive 2026-05-06.
>
> **Phase 5 (Live Unity UAT)** is operator-only post-May-23 ($550 connection fee + Java Feed Connector binary).

### 1.1 Phase 2 follow-up — Promotion ledger UI

- [ ] [CODE] P2. UI surface — `/archetype-promotions` page in `unified-trading-system-ui` (or `deployment-ui`). Lists
      all 18 archetypes with current PROD build, active SHADOW candidates, decision timeline for each. Reads the ledger
      via a strategy-service API endpoint. Deferred — P2; can land after Phase 3 shadow clock is live.

### 1.2 Phase 4 — Factory full cutover + legacy code deletion (gated on Phase 3 PROMOTE; see DROPPED note above)

> Audit verdict 2026-05-06: V1-RETIRE bypassed shadow window. Phase 4 still represents real deletion work; the ordering
> changes (no longer gated on shadow PROMOTE) but the items below are still pending physical deletion of the legacy code
> fence.

- [ ] [CODE] P1. Change `STRATEGY_DISPATCH_MODE` default from `legacy` to `v2_prod`. Ship + observe for 1-2 days.
- [ ] [CODE] P1. Delete feature-flag gate; v2 is the only path.
- [ ] [CODE] P1. `git rm -rf strategy-service/strategy_service/engine/strategies/_archived_pre_v2/`
- [ ] [CODE] P1. Rewrite `strategy_service/engine/strategies/__init__.py` — remove legacy re-exports; keep only `v2/`
      namespace.
- [ ] [CODE] P1. **Test migration — 3 buckets (per memory's Commit D):** Bucket A — DELETE legacy tests for promoted
      archetypes with equivalent v2 coverage; Bucket B — `pytest.mark.xfail` on NEEDS_REVIEW residuals; Bucket C —
      RETARGET integration tests to v2 `V2EngineOrchestrator.register_instance()` + `on_tick()`. ~49 legacy test files
      audit, all buckets land in the same commit as the archive deletion.
- [ ] [CODE] P1. Clear the `# noqa: E501` annotations added during archive (only needed because the archive path is
      long; deletion makes them unnecessary).
- [ ] [CODE] P1. Update `legacy_strategy_mapping.py` `legacy_module` strings — keep field for audit provenance; set
      values to `"RETIRED:strategy_service.engine.strategies._archived_pre_v2.<module>"`.
- [ ] [CODE] P1. Delete `codex/09-strategy/_archived_pre_v2/` + the archive README + the inbound-link repointings.
- [ ] [TEST] P1. Full QG green on strategy-service + e2e-testing + execution-service after deletion.

### 1.3 Phase 5 — Live Unity UAT (post-May-23, operator-gated)

- [ ] [OPS] P1. Unity onboarding — pay $550 connection fee per `UNITY_COMMERCIAL_TERMS`
      (`production_deposit_usd=10_800`; refund at 5_300_000 lifetime turnover).
- [ ] [OPS] P1. Obtain Unity Java Feed Connector binary + sandbox credentials.
- [ ] [CODE] P1. Swap `make_mock_launch_fn()` for `make_real_launch_fn(binary_path=...)` in execution-service Unity
      adapter. JSON-line protocol identical.
- [ ] [TEST] P1. End-to-end smoke against Unity UAT — place 0.01 GBP bet, verify fill + commission + per-book
      attribution.
- [ ] [OPS] P1. 48-hour observation period with the real binary before enabling live capital.

### 1.4 Phase 6 — Capability gap close-out (non-blocking, deferred)

- [ ] [CODE] P2. **Venue-selection SOR multi-venue logic** — v2 emits eligible venue set; execution-service currently
      picks first. Implement fee-adjusted SOR in `execution-service/execution_service/v2/` with VenueCapabilityV2
      fee_bps + latency + liquidity inputs.
- [ ] [CODE] P2. **Parameterized hold-policy engine mixin** — pull MAX_DURATION / EXPIRATION_GATE / PNL_TARGET /
      LIQUIDATION_GATE into a shared mixin so configs can flip between them without changing engine code.
- [ ] [CODE] P2. **Transfer-rebalance service integration to V2EngineOrchestrator** — wire transfer-rebalance to fan
      TRANSFER instructions to DeFi engines for cross-venue rebalancing.
- [ ] [CODE] P2. **Benchmark-fills on v2 instructions** — add `benchmark_price_ref` to `StrategyInstructionEnvelope` +
      wire strategy-side emission for alpha attribution clarity.
- [ ] [CODE] P2. **Portfolio-allocator repo split** — relocate to its own repo when team size warrants. Designed to be
      relocatable; no refactor needed.

### 1.5 Phase 9 — Coverage matrix follow-up

> **May-23 gating note** (deep audit 2026-05-07): the parity test below feeds Phase 2.2 manual-trade gate Playwright
> assertions — without the markdown↔TS drift detector, Phase 2.2 acceptance assertions silently pass on stale matrix
> mismatches. Phase 1.5 SHOULD ship before Phase 2.2 verification runs to keep coverage truth-set honest.

- [ ] [TEST] P1. Add `unified-trading-system-ui/tests/unit/lib/architecture-v2/coverage.test.ts` — markdown ↔ TS parity
      test: parse `category-instrument-coverage.md` at test time and assert every matrix row matches a cell in
      `ARCHETYPE_COVERAGE`. Detects drift early.

### 1.6 Phase 10.6 — Service-split refactor: mine /research/strategy/families + /catalog, redistribute, delete

> Closes the double-heading shown in the user's 2026-04-19 screenshot. **Critical-path subset for May-23**: the audit
> step + RBAC-scoped refactor of `/services/research/strategies` + `/services/trading/strategies` are needed for Group F
> live-trading guardrails. IM-DESK + IM-CLIENT wiring is post-May-23.

- [ ] [AUDIT] P1. **Pre-execution audit.** Grep both legacy pages (`/services/research/strategy/families` +
      `/services/research/strategy/catalog`) for every feature worth preserving. Also grep client-reporting tool source
      to find where the catalogue tab lives. Produce a migration manifest per feature.
- [ ] [CODE] P1. **Refactor `/services/research/strategies`** to consume the catalogue registry. Scoped by
      `slots_visible_to(audience="trading_platform_subscriber", client_id=user.client_id)`. Backtest-config playground
      lives here. "Talk to IM" CTA on locked-but-visible slots.
- [ ] [CODE] P1. **Refactor `/services/trading/strategies`** to show user's promoted-to-live subset. Per-slot view: live
      fills, PnL, live-vs-backtest delta (from `ShadowComparisonMetrics`).
- [ ] [CODE] P1. **Wire `/services/investment-management/catalog`** as IM-DESK view. Full universe minus
      pre-`CODE_AUDITED` placeholders, with lock-state + maturity badges. `im_desk` role.
- [ ] [CODE] P1. **Wire IM-CLIENT catalogue inside client-reporting tool** (location TBD by audit step). Audience filter
      `slots_visible_to(audience="im_client", client_id=client.id)`. Two sections: "Allocated to you" (real details) +
      "Available to invest in" (aspirational).
- [ ] [CODE] P1. **Delete** `/services/research/strategy/families/` and `/services/research/strategy/catalog/`. Update
      sidebar nav. Lands last.
- [ ] [TEST] P1. Vitest per refactored page. Playwright e2e two happy paths: (a) trading-platform subscriber → research
      → backtest → promote → trading; (b) IM-client opens reporting tool → sees allocated + aspirational.

### 1.7 Phase 10.7 — Allocator-as-shared-service split

> **🟢 ARCHITECTURE-UNLOCK 2026-05-20** (operator directive): the **dataflow scaffold** of Phase 10.7 ships May-23 via
> [`trading_agent_service_architecture_unlock_2026_05_22.md`](../active/trading_agent_service_architecture_unlock_2026_05_22.md).
> Specifically: `ArchetypeAllocationDirective` UAC model lands; shared-allocator-core stub at
> `strategy_service/portfolio_allocator/` emits no-op directives; strategy-service `StrategyDirectiveReloader` consumes
> directives via existing config_reloaders.py pattern. **Production allocator logic + IM-side + Trading-platform-side
> UIs stay P1 post-cutover.**

- [ ] [CODE] P1. **IM-side allocator** inside the IM service. Careful-mode UI: human-approved weight changes, multi-sign
      workflows, full audit trail via UTL events.
- [ ] [CODE] P1. **Trading-platform-side allocator** inside the Trading service. Auto-mode: client target weight vector
      → system applies directives automatically via the existing portfolio-allocator instance on the client's own
      infrastructure.
- [ ] [CODE] P1. **Shared allocator core** lives in `strategy_service/portfolio_allocator/`. Both UIs are thin shells
      over the same `AllocationDirective` emission path.
- [ ] [CODE] P1. **Delete `/services/research/strategy/allocator`** — research is the iteration surface, not the
      capital-commitment surface.
- [ ] [TEST] P1. Vitest + integration: IM approval workflow rejects un-approved allocation changes; trading auto-apply
      triggers a real allocator tick.

### 1.8 Phase 11 — Dated-future roll mechanism (representative-future-service + combo creation)

> Implements block-list entry BL-10 from `category-instrument-coverage.md`. Unblocks every `-dated-` slot. Codex spec at
> `/codex/09-strategy/architecture-v2/cross-cutting/futures-roll-and-combos.md`.
>
> **May-23 gating clarification** (deep audit 2026-05-07): the May-23 lead archetype `carry_staked_basis` (and
> hedging-leg `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`; renamed from legacy `leveraged_funding_arb` per
> Stream B canonicalisation 2026-05-07)) are perp-based — NO `-dated-` slot is on the May-23 critical path. Phase 1.8
> roll mechanism is **advisory pre-May-23, hard prerequisite post-May-23** (when the first `-dated-` archetype goes
> live). Stays P1, but does NOT gate the May-23 cutover.

- [ ] [CODE] P1. **UAC registry + event contract.** Implement gap #11 from `uac-registry-gaps.md`:
      `UnderlyingDeclaration`, `RollTriggerPolicy`, `REPRESENTATIVE_FUTURE_REGISTRY` tuple.
      `RepresentativeFutureChangedEvent` in UAC. Constants in UTL `event_types.py`.
- [ ] [CODE] P1. **`representative-future-service` scaffold.** New thin service. Subscribes to liquidity feature group,
      applies `RollTriggerPolicy`, emits `REPRESENTATIVE_FUTURE_CHANGED`. Publishes snapshot at
      `gs://{project}-reference-artifacts/representative_future/{underlying_id}.json`. REST endpoint
      `GET /representative/{underlying_id}?as_of={iso_ts}` for deterministic replay.
- [ ] [CODE] P1. **Strategy-service subscriber.** On `-dated-` slot instances, subscribe to
      `REPRESENTATIVE_FUTURE_CHANGED`, lookup net position via PBMS, emit `FUTURES_ROLL` ATOMIC instruction (new
      `CALENDAR_ROLL` mode).
- [ ] [CODE] P1. **Execution-service combo resolution.** Extend ATOMIC handler with `CALENDAR_ROLL` mode: (1) listed
      combo ticker → single-order; (2) synthetic combo via multi-leg if venue supports; (3) LEADER_HEDGE fallback with
      hard slippage guard. All paths enforce `synthetic_fair_value_ref` guardrail bounded by `max_roll_slippage_bps`.
- [ ] [CODE] P1. **Circuit breakers + events.** Emit `FUTURES_ROLL_COMPLETED` / `FUTURES_ROLL_FAILED`. Hard-stop on
      slippage breach; soft-freeze on feed-staleness; ops escalation on consecutive failures. Integrate with R&E
      kill-switch rules engine.
- [ ] [CODE] P1. **PBMS position-attribution rewrite.** On `FUTURES_ROLL_COMPLETED`, PBMS rewrites attribution from
      `prior_contract` → `new_contract` so PnL stays continuous.
- [ ] [TEST] P1. Backtest-parity test: replay window crossing actual roll boundary (e.g., 2026-03-13 CME ES H6→M6);
      assert v2 roll path produces position + PnL continuity.
- [ ] [TEST] P1. Cross-service integration test in e2e-testing: `REPRESENTATIVE_FUTURE_CHANGED` → `FUTURES_ROLL` →
      execution → PBMS attribution rewrite, on a mock combo-listing venue.
- [ ] [CODE] P2. **Slot-label migration script.** Rewrite target-universe / legacy-mapping rows using
      `-fixed-{contract}-` to `-dated-` once roll mechanism is green. Operator-gated.

### 1.9 Phase 3-11 fold-in residuals (from archived strategy_v2_phase3_11_handoff)

> Carried forward from the strategy_v2 plan's "Phase 3-11 implementation scope" section. ~22 P1 todos. The minimum
> subset needed for Group F live-trading is `11 action handlers, one per InstructionActionV2`, the policy registry, the
> `AccountInstruction` orchestrator, and Layer 3 venue-account pre-flight. Rest is post-May-23.

#### Strategy migration + execution v2

- [ ] [CODE] P1. Migrate 53 existing strategies to `(archetype, instance, config)` triples (Phase 11).
- [ ] [CODE] P1. 11 action handlers, one per `InstructionActionV2`.
- [ ] [CODE] P1. Policy registry reading artifact-versioned `ExecutionPolicy` docs.
- [ ] [CODE] P1. Algo library registration with mandatory `benchmark_fill()` method.
- [ ] [CODE] P1. Venue-account pre-flight (Layer 3 of 4-layer risk model) consuming PBMS + `VenueCapabilityV2`.
- [ ] [CODE] P1. ATOMIC handler sub-modes: same-venue native, LEADER_HEDGE cross-venue, SEQUENCED_WITH_PACING.
- [ ] [CODE] P1. `BenchmarkFillMode` per action type (arrival_mid, twap_window, pool_mid_at_block, ...).
- [ ] [CODE] P1. META_BROKER router for Unity with child-book attribution + Unity TCP adapter.
- [ ] [CODE] P1. MEV router (Flashbots + MEV Blocker + Manifold; Bloxroute excluded).
- [ ] [CODE] P1. Cost-model artifact loader (`cost_model/*` registry).
- [x] [CODE] P1. `AccountInstruction` orchestrator (non-benchmarked, operator-driven). **SHIPPED 2026-05-07** — verified
      via deep audit at `execution-service/execution_service/v2/account_orchestrator.py`
      `AccountInstructionOrchestrator` class with `dispatch()` method (validates + routes). Remaining 1.9 minimum-subset
      items (11 action handlers, policy registry, Layer 3 pre-flight) still pending; orchestrator itself done.

#### Allocator service (8 archetype engines)

> **🟢 ARCHITECTURE-UNLOCK 2026-05-20**: the service scaffolding item "ServiceBootstrap, Health API + data_freshness,
> typed config reloader, SM keys" ships May-23 in trading-agent-service via architecture-unlock plan Phase 6. The 7
> archetype-engine items + guard rails + shadow mode + NAV reads stay post-cutover.

- [ ] [CODE] P1. 8 allocator archetypes: FIXED, PNL_WEIGHTED, SHARPE_WEIGHTED, RISK_PARITY, KELLY, MIN_CVAR, [+2].
- [ ] [CODE] P1. Per-client instance registry; cadence scheduler (DAILY / HOURLY / WEEKLY / ON_EVENT).
- [ ] [CODE] P1. Guard rails: max_weight, min_weight, max_turnover, correlation_cap, family_diversification.
- [ ] [CODE] P1. Shadow mode (primary + shadow instance per client); emits `AllocationDirective` events.
- [ ] [CODE] P1. Reads NAVs + returns from PBMS; kill switches from risk-service.
- [ ] [CODE] P1. Cross-share-class NAV conversion + audit log retention per directive.
- [ ] [CODE] P1. Service scaffolding: ServiceBootstrap, Health API + `data_freshness`, typed config reloader, SM keys.

#### Strategy instance / venue-account dual projection

- [ ] [CODE] P1. Dual projection: strategy-instance view + venue-account view.
- [ ] [CODE] P1. Sum-equality invariant check; emit `VENUE_ACCOUNT_STRATEGY_SUM_DRIFT` on violation.
- [ ] [CODE] P1. Fill attribution: match `fill_id → instruction_id → strategy_instance_id`.

## Phase 2 — DART operator UX cockpit (was: dart_ux_cockpit_refactor)

> Source plan: `plans/archive/dart_ux_cockpit_refactor_2026_04_29.md`. **Substantively shipped per audit**: 9-phase
> programme (Workspace scope → Scope bar → Terminal IA → Research IA → Scope-reactive widgets → Eight starter cockpits →
> Locked previews + system-map → Mock-mode liveness → Route-redirects + unified shell), Configuration lifecycle UI
> surfaces (Promote / Explain / Admin), Persona-walkthrough Playwright matrix (6 personas), Phase 1A/1B foundational
> primitives (StrategyAvailabilityResolver + Configuration Lifecycle types). 7 polish items remain.

### 2.1 Polish items (open)

> **Priority-vs-criticality clarification** (deep audit 2026-05-07): the 7 polish items below carry P0/P1/HUMAN priority
> labels, but ONLY Phase 2.2 (6-persona Playwright matrix) is on the May-23 critical path. The 5 P0-tagged items here
> are post-May-23 quality work — re-tagged P2 below to align priority with criticality. Original P0 reflects
> "cockpit-architecture importance," not "live-trading deadline." If May-23 hard floor work needs an agent, it pulls
> from Phase 2.2 + Phase 1.9 fold-in subset, not from this list.

- [ ] [AGENT] P2. **Phase 5 widget vocabulary SSOT** (§4.9, was P0). Every `DartWidgetMeta.id` maps 1:1 to a canonical
      surface name from `unified-trading-system-ui/docs/reference/common-tools.md` (30 manual surfaces) or
      `automation-common-tools.md` (18 automated surfaces). Phase 5 ships with a `canonicalSurfaceName` field; v2
      archetype expansion reuses widgets without rename churn. **DEFERRED post-May-23**.
- [ ] [AGENT] P2. **Cross-cutting widget conventions** (§4.11, was P0). Ten conventions propagated as `DartWidgetMeta`
      extensions (`freshnessSla`, `nativeUnit`, `drilldownScope`, hotkey contract, audit-on-mutate, replay-time-binding,
      etc.). Lands alongside Phase 5. **DEFERRED post-May-23**.
- [ ] [AGENT] P2. **Layer 2 minimum proof signals** (was P0) — six irreducible badges (data-freshness pill, last-update
      timestamp, maturity badge, visibility-state badge, demo-data badge, report/reconciliation placeholder link). Built
      alongside Phases 7-8. Add **two more** post-§4.8: **release-bundle audit pill** (current strategy version + active
      runtime overrides count) and **reproducibility pill** (training data hash known / unknown). **DEFERRED
      post-May-23**.
- [ ] [HUMAN] P2. **v2 archetype-expansion roadmap** (§4.10, was P1). v1 = 8 presets covering 6 archetype clusters; v2
      names 7 missing archetype presets (Market-Making · Equity LS · Rates · Macro · FX · Energy · Event-Driven) +
      Firm-Risk Aggregate Console for David. Not blocking v1. **DEFERRED post-May-23**.
- [ ] [HUMAN] P2. **Doc alignment** (§25.A.7, was P0) — propagate vocabulary into PM codex (`14-customer-journeys/dart`,
      `14-customer-journeys/audiences-and-journeys`, `09-strategy/architecture-v2/*`, `08-workflows/*`, `02-data/*`,
      `GLOSSARY.md`, `00-SSOT-INDEX.md`) + UI-repo docs (`context/AGENT_UI_STRUCTURE.md`, `context/CONTEXT_GUIDE.md`,
      `context/CONFIG_REFERENCE.md`, `docs/TIER_ZERO.md`). **DEFERRED post-May-23**.
- [ ] [HUMAN] P2. **IR presentation copy alignment** (§25.A.2, was P1) — board / platform / investment / plan decks +
      competitive-landscape SSOT + briefings YAML + `service-labels.ts`. **DEFERRED post-May-23**.
- [ ] [HUMAN] P2. **Public website copy alignment** (§25.A.3, was P1) — homepage metadata + `_home-client.tsx`
      Hero/MarketsUniverse/EngagementRoutes/WhyOdum + DART platform page + our-story. **DEFERRED post-May-23**.

### 2.2 Manual-trade gate verification (May-23 critical-path; from Phase 3 of umbrella scope)

- [ ] [AGENT] P0. **6-persona Playwright matrix on manual-trade flow.** Master plan Group G acceptance criterion. Re-run
      the existing 6-persona walkthrough harness (admin / im_desk / im_client / dart_full / dart_signals_in /
      regulatory) against the manual-trade gate path (Catalogue → Research → Promote → Live confirm dialog → fill →
      Explain attribution). Captures distinct persona screenshots; asserts §4.3 Live confirm dialog fires on Paper →
      Live for entitled personas only; asserts AccountConnectivityConfig pre-flight gates fire for missing CeFi accounts
      / DeFi wallets. Hard prereq for Group G acceptance.

## Phase 3 — Cross-domain alpha + UI walkthrough (was: consolidated_strategy_and_ui)

> Source plan: `plans/archive/consolidated_strategy_and_ui_2026_04_15.md`. Strategy lifecycle Phase 1 + microstructure
> features + UI health page have shipped; cross-domain alpha core is the genuinely-open net-new work. Group E + F + G
> largely subsumed by Phase 2 above (DART cockpit) — only the parts that name distinct deliverables remain.

### 3.1 Group A — Cross-domain alpha: UAC + UTL schemas & engines (genuinely-open net-new)

- [ ] [AGENT] P0. **cda-p1-uac-schemas**: Add cross-domain feature, SLA, and DQS schemas to UAC internal. (UAC grep
      `FeatureFreshnessSLA|DataQualityScorer|CrossDomainFeature` → 0 hits.)
- [ ] [AGENT] P0. **cda-p1-utl-sla-engine**: Build FeatureFreshnessSLAEngine in UTL
      `feature_service_base/sla_engine.py`. (UTL grep `FeatureFreshnessSLAEngine|sla_engine` → 0 hits.)
- [ ] [AGENT] P0. **cda-p1-utl-crossdomain-calc**: Build cross-domain feature calculators in UTL
      `feature_calculator/crossdomain.py`. (UTL `feature_calculator/` has time_series, transformations, onchain,
      liquidation_bands, validations, base, registry — no `crossdomain.py`.)
- [ ] [AGENT] P0. **cda-p1-utl-dqs**: Build DataQualityScorer in UTL `feature_service_base/data_quality.py`. (UTL grep
      `DataQualityScorer` → 0 hits in production.)
- [ ] [AGENT] P1. **cda-p1-qg**: Run quality-gates.sh on UAC, UTL — all pass. Final QG gate; depends on the four
      preceding net-new builds.

### 3.2 Group B — Cross-domain alpha: Feature service integration

- [ ] [AGENT] P0. **cda-p2-crossdomain-features**: Wire cross-domain features into features-cross-instrument-service.
      (Note: the SLA-driven cross-domain wiring is distinct from the paired_price_dispersion family already shipped at
      UAC@0e7ba95 + features-cross-instrument `190bea1`/`2804f47`/`071604f`/`d1da107`.)
- [ ] [AGENT] P0. **cda-p2-defi-alpha**: Add DeFi-specific alpha features to features-onchain-service. (features-onchain
      has aave\_\*, block_priority_gas_distribution, concentrated_liquidity_il_realised, cryptoquant_exchange_flow
      shipped; the named "alpha features" catalogue is unspecified. Likely overlap with `defi_master` umbrella — verify
      scope before re-scoping.)
- [ ] [AGENT] P0. **cda-p2-sla-integration**: Integrate SLA engine into all feature services. BLOCKED-ON
      cda-p1-utl-sla-engine.
- [ ] [AGENT] P0. **cda-p2-dqs-mtds**: Integrate DataQualityScorer into market-tick-data-service. BLOCKED-ON
      cda-p1-utl-dqs. Verify scope vs writegate-honest-coverage's `record_captured` 4-pillar gate (NaN ratio + cluster
      coverage) before committing.
- [ ] [AGENT] P1. **cda-p2-qg**: Run quality-gates.sh on all Phase 2 repos — pass.

### 3.3 Group C — Cross-domain alpha: Execution intelligence (Group F live-trading prereq)

- [ ] [AGENT] P0. **cda-p3-cost-model**: Build execution cost prediction model in execution-service. (execution-service
      ships deterministic estimator at `execution_service/services/execution_cost_estimator.py` + `v2/cost_models.py`.
      The "learned vs deterministic" design gap is the open scope.)
- [ ] [AGENT] P0. **cda-p3-unified-sor**: Build unified CeFi+DeFi SOR in execution-service. (execution-service ships
      `algo_library/sor_cross_chain.py` for DeFi cross-chain; the unified facade across both venue types is the open
      piece. **Live trading prereq.**)
- [ ] [AGENT] P1. **cda-p3-qg**: Run quality-gates.sh on execution-service — pass.
- [ ] [AGENT] P1. **cda-p4-final-qg**: Final QG on all cross-domain repos.

### 3.4 Group D — Strategy lifecycle visibility (residuals after Plan A shipped)

- [ ] [AGENT] P0. **slv-p2-composable**: Implement composable strategy building blocks in strategy-service.
      (strategy-service grep `ComposableStrategy|composable_strategy` → 0 hits. Likely lower priority post-Plan A 5-dim
      catalogue; archetype variants already provide composition surface.)
- [ ] [AGENT] P0. **slv-p2-auto-retune**: Add auto-retuning trigger in ml-inference-service.
      (`ml_inference_service/engine/drift_monitor.py` ships `auto_retune_enabled: bool` + monitor pipeline; needs the
      actual retune-trigger publish wiring to ml-training-service.)
- [ ] [AGENT] P0. **slv-p2-lineage**: Add prediction lineage tracking. (ml-inference `69d6313` + ml-training `f7369f2`
      thread service-run job_id + model_family into manifest writes; the strategy-side consumer (strategy reads back
      which model produced which signal) is the remaining gap.)
- [ ] [AGENT] P1. **slv-p2-qg**: Run quality-gates.sh on strategy-service, ml-inference-service — pass.

### 3.5 Group E — Strategy & ML UI dashboards (most folded into Phase 2 cockpit; only distinct items remain)

- [ ] [AGENT] P0. **slv-p3-ml-dashboard**: Build ML model performance dashboard in unified-trading-system-ui. Surface
      `app/(platform)/services/research/ml/training/page.tsx` + `monitoring/page.tsx` shipped with
      `components/grid-config-editor.tsx` + `training-run-detail.tsx`; "model performance dashboard" depth (drift
      charts, P&L attribution to model_family) unclear. Likely partially folded into Phase 2.
- [ ] [AGENT] P0. **slv-p3-research-shell**: Build strategy research shell in unified-trading-system-ui.
      `app/(platform)/services/research/` shipped with sub-routes (strategies, signals, features, ml, execution,
      allocate, quant, overview, strategy). Substantively shipped modulo UX polish; flip to DONE after a Playwright walk
      verifies acceptance. **Deep audit 2026-05-07**: Playwright walk NOT done — `tests/e2e/` has 24 spec.ts files but
      none target `/services/research/` shell routes specifically (no `research-shell*` or `slv-p3*` named specs).
      Recommend authoring `tests/e2e/research-shell.spec.ts` covering each sub-route's render + first-paint as a
      pre-flip task; sub-component tests exist in `components/research/` directory but operator-flow walk is the gate.
- [ ] [AGENT] P0. **slv-p3-risk-attribution**: Build risk attribution dashboard in unified-trading-system-ui. (workspace
      grep `RiskAttribution` returns only schema definitions in `context/` + plan files. No risk-attribution route
      shipped. **Live trading prereq for Group F.**)
- [ ] [AGENT] P1. **slv-p3-qg**: Run quality-gates.sh / UI build on unified-trading-system-ui — pass.
- [ ] [AGENT] P1. **slv-p4-final-qg**: Final QG on all strategy lifecycle repos.

### 3.6 Group F — Client config E2E & UI alignment

- [ ] [AGENT] P1. **cc-4a-e2e**: Add client config + risk scenarios to e2e-testing. (e2e-testing/ under
      unified-trading-pm has 23 service stubs but no client-config cross-cutting scenario. Overlaps with
      `consolidated_operational_validation` Group B.)
- [ ] [AGENT] P1. **cc-5a-docs**: Update codex docs for client config and DeFi risk. (codex 04-architecture has
      `flash-loan-receiver.md`, `interface-credential-convention.md`; "client config" scope unverified.)
- [ ] [HUMAN+AGENT] P0. **ui-1a-walkthrough-audit**: Audit UI for every strategy walkthrough — can client manually
      execute each step? BLOCKED-ON Phase 2 above (DART surface owns the walkthrough flow); also partial-overlap with
      strategy-catalogue UI shipped at unified-trading-system-ui `app/(platform)/services/strategy-catalogue/`.
- [ ] [HUMAN+AGENT] P0. **ui-2a-batch-live**: Verify batch=live alignment across all services for all strategies.
      BLOCKED-ON `master_to_live_defi_2026_05_23` Group F batch-vs-live reconciliation deliverable. The CLAUDE.md "Batch
      = Live" architectural rule is the principle; the verification is the deliverable.
- [ ] [AGENT] P0. **ui-2b-e2e-all-strategies**: Create E2E test suite covering all strategies in all modes. BLOCKED-ON
      `consolidated_operational_validation` Group B cluster e2e completion + Plan A 228 strategy instances catalogue.
- [ ] [AGENT] P1. **ui-3a-demo-scripts**: Create demo walkthrough scripts for client presentations. Narrowly demo-only;
      not on May-23 critical path.
- [ ] [AGENT] P1. **ui-4a-docs**: Update codex + handover docs. Doc-only acceptance gate.

### 3.7 Group G — UI sync hardening (residuals after health-page shipped)

- [ ] [AGENT] P1. **ui-p9b-qg-validation**: Run quality gates: vitest + vite build + playwright. (
      `unified-trading-system-ui` is Next.js — commands: `npm test` (vitest) + `npm build` + `npx playwright test`.)

## Critical-path priority for May-23

> **Phase numbering note.** Phase 1 sub-numbering (1.1 → 1.9) is inherited from the source plan's archaeological phase
> numbering (Phase 2 / 4 / 5 / 6 / 9 / 10.6 / 10.7 / 11 / 3-11-fold-in) and does NOT reflect dependency order. The
> May-23 critical-path block below pulls the live-trading hard floor items out of that numbering. The only true
> sequencing constraint inside Phase 1 is that **Phase 1.9 (Phase 3-11 fold-in residuals) gates Phase 1.6
> service-split** — the 11 action handlers + policy registry + `AccountInstruction` orchestrator must exist before the
> RBAC-scoped research/trading-strategies refactor can route through them. Everything else inside Phase 1 is
> post-May-23.

- **Phase 2.2 manual-trade gate verify**: 6-persona Playwright matrix on manual-trade flow (master Group G acceptance
  criterion).
- **Phase 1.9 Phase 3-11 fold-in residuals (subset)**: 11 action handlers + policy registry + `AccountInstruction`
  orchestrator + Layer 3 venue-account pre-flight — minimum subset of the ~22 P1 items needed for Group F live-trading.
  The HEAVIEST live-trading critical-path block in Phase 1; the rest of Phase 1.9 (allocator service, dual projection)
  is post-May-23.

  **Topology GAP closure todos (from topology_qgroup_gap_closure_2026_05_09 Phase 1+8):**
  - [x] [AGENT] P0. **GAP-1 + GAP-4**: `/codex/04-architecture/strategy-ensemble-topology.md` pinning ONE VM per
        asset_group + DeFi/CeFi split + multi-tenancy rules + colocation-bootstrap protocol. Shipped PM@369d8424
        2026-05-14.
  - [x] [AGENT] P0. **GAP-2 + GAP-3**: Process-vs-in-proc shape codified in
        `/codex/04-architecture/strategy-ensemble-topology.md` § "Per-VM process layout" — 4 separate OS processes,
        local Redis IPC, `POSITION_BALANCE_URL`/`RISK_EXPOSURE_URL`/`EXECUTION_URL` env-var service discovery. Shipped
        PM@369d8424 2026-05-14. Colocation bootstrap script (`colocate-strategy-vm.sh`) DEFERRED Phase 1.9.
  - [x] [AGENT] P0. **GAP-5**: `ExecutionRejectionCode` + `ExecutionRejectionEvent` shipped UAC@25d9a70.
        Strategy-service rejection consumer shipped strategy-service@c87f9c1 (`rejection_handler.py` + 11 unit tests).
        Shipped 2026-05-14.
  - [x] [AGENT] P0. **GAP-12**: `/codex/04-architecture/matching-engine-assumptions.md` pinning per-matcher slippage
        model + commission schedule + latency model + venue-liquidity proxy + `BenchmarkFillMode` per
        `InstructionActionV2`. `MatchingEngineConfig` UAC class TODO: ship in UAC internal/architecture_v2 Phase 1.9
        bundle. Shipped PM@369d8424 2026-05-14.
  - [x] [AGENT] P0. **GAP-14 + GAP-15**: 5 matcher classes (L0/L1/L2/AMM/BenchmarkMatcher) importable + mode dispatch
        tests in `execution-service/tests/unit/matching_engine/test_mode_dispatch.py`. Codex doc shipped PM@736f2ada.
        Shipped execution-service@4bf6ec2c2 + PM@736f2ada 2026-05-15.
  - [x] [AGENT] P0. **GAP-16**: `BENCHMARK_FILL_MODE_BY_ACTION` dict with all 14 `InstructionActionV2` →
        `BenchmarkFillMode` mappings shipped UAC@42da7d0. Tests in execution-service@4bf6ec2c2. Shipped 2026-05-15.

- **Phase 3.3 cda-p3-unified-sor**: Live trading prereq for Group F.
- **Phase 3.5 slv-p3-risk-attribution**: Live trading prereq for Group F.
- **Phase 1.6 Phase 10.6 service-split refactor (subset)**: pre-execution audit + RBAC-scoped refactor of
  `/services/research/strategies` + `/services/trading/strategies` for Group F live-trading guardrails. Distinct from
  Phase 1.9 above — that ships the action-handler engine; this routes the operator UI through it. IM-DESK + IM-CLIENT
  wiring is post-May-23.
- Everything else: post-May-23. **Phase 1.3 (Live Unity UAT) is explicitly post-May-23.**

## Sub-plans (referenced from this epic)

- **`plans/active/compute_optimization_mock_data_2026_05_13.md`** (~4.8 cal-AI-days, P1, deadline 2026-05-23) —
  Mock-data optimization sprint covering: per-stage parallelization (MDPS / features-service / strategy /
  execution-alpha / ml-training), big-machine SKU matrix extension (`c3-highcpu-88` / `-176` / `m3-megamem-128` /
  `m3-ultramem-160`), `strategy-service/scripts/run_2yr_config_grid_backtest.py` extension to cover all 6 Tier A
  archetype families, codex SSOTs for performance-targets + cutover-window dependency-order. Mock-data approach lets
  this run in parallel with real-backfill workstream (no I/O dependency). MVP universe scope per
  `/codex/09-strategy/mvp-universe-per-asset-group.md`.
- **`plans/active/strategy_archetype_taxonomy_2026_05_12.md`** — archetype taxonomy refinement (separately
  cross-referenced earlier; parent_epic already set).
- **`plans/active/strategy_repo_consolidation_2026_05_19.md`** (~12 cal-AI-days, P0, deadline 2026-05-23, `infra` class)
  — Subtree-merge `risk-and-exposure-service` + `position-balance-monitor-service` + `pnl-attribution-service` into the
  existing `strategy-service` repo as sub-packages (`strategy_service/risk/`, `/position/`, `/pnl/`); archive 3 source
  repos via `gh repo archive`. ONE Docker image, ONE flat `pyproject.toml`, ONE Health-API exposing aggregated
  freshness, ONE CLI with `--operation` discriminating risk-monitor / position-recon / pnl-attribution / strategy-batch
  / strategy-live / backtest. Mirrors `features_repo_consolidation_2026_05_08.md` 10-phase pattern. Pre-cutover race;
  flips to `BLOCKED-CUTOVER` if Phase 6 parity slips. Soft freeze on structural changes in the 4 affected repos for
  duration. Sibling: `plans/active/ml_repo_consolidation_2026_05_19.md` (independent execution).

**MVP scope SSOT for backtest config-grid + ML training sizing**:
[`/codex/09-strategy/mvp-universe-per-asset-group.md`](/codex/09-strategy/mvp-universe-per-asset-group.md) defines Tier
A (backtest-complete by May-23) vs Tier B (code-ready architecture only). Tier A = ml-continuous (CeFi + ES) +
ml-settled (Sports) + arbitrage-funding-rate + arbitrage-sports-book + arbitrage-event-markets + defi-carry-family.

## Coordination with sibling plans

- **`features_and_ml_master`**: Phase 4D (strategy-service calibrated-signal consumption
  - cost-aware filtering) overlaps with this umbrella's Phase 3.4 `slv-p2-*` ML lineage items and Phase 3.5
    `slv-p3-ml-dashboard`. Calibrated-signal consumption is owned by ml_and_features_master Phase 4D (model lifecycle);
    strategy-service-side consumer wiring is the boundary.
- **`writegate_honest_coverage_endtoend_2026_05_06`**: Phase 4.A typed-error rendering + Phase 5 baseline ratchet feed
  the data-status surface that DART (Phase 2) consumes. No direct dependency, but Phase 2.2 manual-trade gate Playwright
  matrix should re-run after writegate Phase 4.A lands so the typed `error_reason` badges render correctly.
- **`master_to_live_defi_2026_05_23`**: Phase 1.9 fold-in residuals (subset) feeds master Group F items 17-22; Phase 2.2
  manual-trade gate is master Group G item 23. Coordinate completion-flip cadence with master refresh agent.
- **`defi_master`**: `carry_staked_basis` lead archetype lives in defi_master Fork 1; Phase 1.9 action-handler engine is
  the upstream that defi_master strategy-config consumes. Coordinate timing — action-handler engine should ship before
  carry_staked_basis live-mode validation.

## Already-shipped from sources (per 2026-05-07 audit)

- `consolidated_strategy_and_ui:cda-p2-microstructure` —
  `features-delta-one-service/features_delta_one_service/app/calculators/microstructure.py` +
  `tests/unit/test_feature_groups/test_microstructure.py` shipped.
- `consolidated_strategy_and_ui:slv-p1-uac-lifecycle-schemas` — UAC `bf407a2` (Plan A 5-dim StrategyInstance + lifecycle
  phasing) + `1a08159` (Plan A catalogue with venue-set variants + lifecycle phasing).
- `consolidated_strategy_and_ui:slv-p1-lifecycle-enforcement` — strategy-service `f50d25c` + `07ac1f7`
  (InstanceLifecycleService + SeedLifecycleHandler + maturity-phase gate in `SignalEmitter.emit_signal`).
- `consolidated_strategy_and_ui:slv-p1-qg` — Plan A archived per memory; QG green at lifecycle-ship time.
- `consolidated_strategy_and_ui:ui-p9a-health-all-services` — `/health` page shipped at `http://localhost:3000/health`
  with auto-detect tier + connector checks.
- `dart_ux_cockpit_refactor` — substantively shipped: 9-phase programme + Configuration lifecycle UI + 6-persona
  Playwright matrix + Phase 1A/1B primitives. Audit verdict: 7 polish items remain (carried forward to Phase 2.1 above).
- `strategy_architecture_v2_finalization:Phase 1` — factory cutover Tier 2 (1a/1b/1c/1d/1e/1f) all shipped per evidence
  trail in archived plan.
- `strategy_architecture_v2_finalization:Phase 2` — shadow persistence registry + ledger + 4 UTL events + codex doc + 19
  unit tests shipped (strategy-service `d51f54c` + UTL `1178301b`).
- `strategy_architecture_v2_finalization:Phase 7` — all 7 NEEDS_REVIEW + Phase 7-closed SPORTS_KELLY resolved
  (strategy-service `3326f9d` + UAC `1d2288e` + strategy-service `a656f91`).
- `strategy_architecture_v2_finalization:Phase 8` — both pre-existing test flakes fixed (execution-service `043d10dc`).
- `strategy_architecture_v2_finalization:Phase 9` — coverage matrix SSOT + archetype-doc propagation + UAC gap memo all
  shipped (codex docs + UI `lib/architecture-v2/coverage.ts`).
- `strategy_architecture_v2_finalization:Phase 10` — master matrix + combinatoric discovery + block-list + per-strategy
  detail + reusable chip primitives + service landing page (UI `a8012c4`
  - `490ff54`); 45 vitest tests pass.
- `strategy_architecture_v2_finalization:Phase 10.5` — UAC registry (`c5b870c`) + events (UTL `c1ccf55c`) + watchdog
  (strategy-service `7e0b6a4`) + allocator enforcement + admin toggle UI (`490ff54`) + badges + 56 unit tests.
- `strategy_architecture_v2_finalization:Phase 3` — DROPPED per audit verdict (V1-RETIRE bypassed shadow window per
  operator directive 2026-05-06). Originally: start shadow clock for all 18 archetypes / weekly EXTEND-REJECT review /
  wait for PROMOTE / human triggers `promote_to_prod()`.

## Closed items (from sources, retained for audit trail)

### From `consolidated_strategy_and_ui_2026_04_15` § Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 32 of 32 unchecked todos
- **Mis-marked DONE → flipped**: 1 — `cda-p2-microstructure` flipped to `[x]`. Verified: features-delta-one-service
  ships `app/calculators/microstructure.py` with `tests/unit/test_feature_groups/test_microstructure.py`.
- **In-flight (running VMs)**: none directly — backfill VMs feed the features that strategy will consume.
- **Blocked by**: `consolidated_ml_advanced_pipeline_2026_04_15` Phase 4 (now folded into `features_and_ml_master`);
  `feature_dag_uac_ssot_and_features_coverage_2026_05_06` (also now folded into `features_and_ml_master`);
  `dart_ux_cockpit_refactor_2026_04_29` (sibling — now Phase 2 of THIS umbrella).
- **Blocks**: `master_to_live_defi_2026_05_23` Group F (Trading prereqs) — cost-aware filtering + calibrated signals;
  Group G (Operator UX) — Strategy & ML dashboards.
- **Last meaningful commit**: strategy-service `e4a0cdd` (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION Phase 9 Phase
  3); `f50d25c` + `07ac1f7` (Plan A lifecycle + maturity-phase gate); UAC `bf407a2` + `1a08159` (5-dim catalogue);
  features-delta-one microstructure; features-cross-instrument paired-dispersion
  (`190bea1`/`2804f47`/`071604f`/`d1da107`).
- **Recommendation**: KEEP active, RESCOPE. Done — folded into THIS umbrella.

### From `dart_ux_cockpit_refactor_2026_04_29` (no audit section; closed-state inferred from plan-of-record)

Plan-of-record at top of source plan: 18 of 25 plan-of-record line items are `[x]` (9-phase programme + Configuration
lifecycle UI + persona-walkthrough matrix + Phase 1A/1B primitives). 7 unchecked items carried into Phase 2.1 above.

### From `strategy_architecture_v2_finalization_2026_04_19` (no audit section; closed-state inferred from per-Phase evidence)

Of original 117 todos in source plan: 50 are `[x]` covering Phase 1 (factory cutover Tier 2), Phase 2 (shadow
persistence except UI surface), Phase 7 (all NEEDS_REVIEW resolved), Phase 8 (test flakes), Phase 9 (coverage matrix),
Phase 10 (master matrix + combinatoric + per-strategy detail), and Phase 10.5 (lock state + maturity registry). 67
remain open across Phase 2 follow-up UI, Phase 3 (DROPPED), Phase 4 (legacy deletion gated reordered), Phase 5 (Unity
UAT post-May-23), Phase 6 (capability gaps), Phase 9 follow-up (markdown↔TS parity test), Phase 10.6 (service-split
refactor), Phase 10.7 (allocator split), Phase 11 (futures roll), and the Phase 3-11 fold-in residuals.

## Referenced sub-plans (active, added 2026-05-14)

Active sub-plans owned by or closely coordinated with this epic:

| Plan                                                                                                                                 | Role                                                                                                | Status |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------ |
| [`active/simulation_scenarios_topology_price_shocks_2026_05_09`](../active/simulation_scenarios_topology_price_shocks_2026_05_09.md) | Simulation scenarios — topology + price shock stress tests for strategy backtests                   | Active |
| [`active/simulation_scenarios_post_cutover_2026_06_01`](../active/simulation_scenarios_post_cutover_2026_06_01.md)                   | Simulation scenarios (post-cutover) — extended scenario library for June-1+ strategy expansion      | Active |
| [`active/topology_qgroup_gap_closure_2026_05_09`](../active/topology_qgroup_gap_closure_2026_05_09.md)                               | Topology + qgroup gap closure — strategy topology + question-group wiring gap remediation           | Active |
| [`active/client_reporting_pnl_attribution_mvp_2026_05_10`](../active/client_reporting_pnl_attribution_mvp_2026_05_10.md)             | Client reporting + P&L attribution MVP — per-client P&L attribution surface for May-23 live trading | Active |

## Source plan archive references

- [`plans/archive/strategy_architecture_v2_finalization_2026_04_19.md`](../archive/strategy_architecture_v2_finalization_2026_04_19.plan.md)
- [`plans/archive/dart_ux_cockpit_refactor_2026_04_29.md`](../archive/dart_ux_cockpit_refactor_2026_04_29.plan.md)
- [`plans/archive/consolidated_strategy_and_ui_2026_04_15.md`](../archive/consolidated_strategy_and_ui_2026_04_15.plan.md)
