---
title: "Plan-change manifest — trading-agent-service architecture unlock (May-23 path)"
created: 2026-05-20
source:
  - operator directive 2026-05-20 "architecture unlocked even if not paper tested yet"
  - plans/active/trading_agent_service_architecture_unlock_2026_05_22.md (new actionable plan)
locked_by: live-defi-rollout
locked_since: 2026-05-20
severity: P0 — coordination doc; operator reviews before plan edits land
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/promote_workflow_may23_cli_path_2026_05_10.md
  - plans/active/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md
  - plans/active/uac_source_capability_metadata_promotion_2026_05_20.md
  - plans/active/strategy_repo_consolidation_2026_05_19.md
  - plans/active/strategy_archetype_taxonomy_2026_05_12.md
  - plans/active/features_repo_consolidation_2026_05_08.md
  - plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md
  - plans/active/issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md
priority: P2
status: resolved
---

# Plan-change manifest — trading-agent-service architecture unlock (May-23)

> **Operator directive 2026-05-20**: "architecture unlocked even if not paper tested yet". This manifest enumerates the
> EXACT changes required across the active plan graph to flip trading-agent-service from "Tier 3 post-launch" to
> "architecture-on-May-23-path". DO NOT EDIT any of these plans yet — this doc is operator-review-first.
>
> **Scope reminder**: data flow wired end-to-end, off-by-default. NOT in scope: continuous paper for non-DeFi
> archetypes, full ML/LLM intelligence, production allocator logic, automatic re-weighting. Those land post-cutover.

## Bucket summary

| Bucket                                  | Count | Plans                                                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MUST change — core architecture**     | 4     | `master_to_live_defi_2026_05_23.md` · `promote_workflow_may23_cli_path_2026_05_10.md` · `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` · `issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md`                                                                                                                                                                            |
| **MUST change — cross-cutting epic**    | 1     | `plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md` (Phase 10.7 allocator-split is the architectural home of the directive emission path)                                                                                                                                                                                                                                                             |
| **NEW — actionable plan**               | 1     | `plans/active/trading_agent_service_architecture_unlock_2026_05_22.md` (this manifest's companion)                                                                                                                                                                                                                                                                                                                |
| **SHOULD change — secondary**           | 3     | `strategy_repo_consolidation_2026_05_19.md` · `strategy_archetype_taxonomy_2026_05_12.md` · `features_repo_consolidation_2026_05_08.md`                                                                                                                                                                                                                                                                           |
| **Coordinate / sequence (no conflict)** | 1     | `uac_source_capability_metadata_promotion_2026_05_20.md` (orthogonal UAC dirs — no edit needed, sequencing note in new plan)                                                                                                                                                                                                                                                                                      |
| **Defer to manifest follow-up sweep**   | ~10   | Per-archetype plans (`defi_master`, `cefi_master`, `sports_master`, `predictions_master`, `tradfi_master`, `defi_archetypes_canonicalisation`, `defi_recursive_borrow_archetypes`, `cme_polymarket_arb`, `dex_perp_and_venue_data_expansion`, `tradfi_ohlcv_only_mvp_backfill`) — each gets ONE-LINE "emits PnL per `strategy_pnl_stream.py` contract" added; only carry + APD MUST land May-23; others stay TODO |

**Total estimated coordination effort** (plan edits only, excluding implementation): ~0.8 cal-AI-days for slot-1-main to
apply all manifest entries below + add the new plan to inventory regenerator. Implementation is separately costed in the
new actionable plan at 2.8 cal-AI-days (refactor × 0.4).

---

## Per-plan change list

### 1. `plans/active/master_to_live_defi_2026_05_23.md` — MUST CHANGE (P0)

#### Change M1 — flip Tier-3 classification

- **Location**: line 1369-1371 § "Tier 3 — post-launch enablement (after May 23)"
- **Current text**: `client-reporting-api`, `fund-administration-service`, `trading-agent-service`. Out of cutover
  scope.`
- **Change to**: `client-reporting-api`, `fund-administration-service`. Out of cutover scope. _Note_:
  `trading-agent-service` moved to Tier-1 (architecture-only) per operator directive 2026-05-20 — see new sub-section
  "Tier 1 — architecture-only services" below.`
- **Rationale**: operator directive 2026-05-20 unlocks architecture even without paper-tested logic.

#### Change M2 — add new Tier-1 architecture-only sub-tier

- **Location**: insert immediately after line 1368 § "Tier 2 — backfill catch-up + ML readiness ladder"
- **Add**:

  ```markdown
  ### Tier 1 — architecture-only services (data flow wired by May-23, production logic post-cutover)

  `trading-agent-service`. Subscribes to features + PnL streams; emits no-op `AllocationDirective` by default;
  production allocator logic + LLM/ML integration ships post-cutover. Group A-E required for the dataflow scaffold;
  Group F (live trading prereqs) deferred to post-cutover — service is OFF-BY-DEFAULT in May-23 live run. See
  [`trading_agent_service_architecture_unlock_2026_05_22.md`](trading_agent_service_architecture_unlock_2026_05_22.md)
  for full scope.
  ```

- **Rationale**: codifies the "architecture unlocked" semantics; gives sub-plan a clear parent-row in master.

#### Change M3 — add 4 readiness items to the 23-item master list (extending Group C — Strategy + execution + observability)

- **Location**: Group C section (search for "Group C — Strategy + execution"; in the readiness matrix referenced from
  line 256+ § "Audit — existing SSOTs this plan augments")
- **Add** 4 todos as items 24-27 of the master list (numbering may rebase; place under Group C):
  - `- [ ] [SCHEMA] P0. UAC `strategy_pnl_stream.py`+`strategy_directives.py` Pydantic models land — see Phase 1+4 of trading_agent_service_architecture_unlock plan.`
  - `- [ ] [CODE] P0. strategy-service emits `StrategyPnlStreamEvent`for`carry_staked_basis`+`arbitrage_price_dispersion` per published contract — see Phase 2.`
  - `- [ ] [CODE] P0. strategy-service `StrategyDirectiveReloader`consumes`AllocationDirective` (no-op default; existing capital/equity allocator reads from directive instead of static config) — see Phase 5.`
  - `- [ ] [CODE] P0. trading-agent-service core scaffold subscribes to features + PnL streams + emits no-op directive — see Phase 6.`
- **Rationale**: Group C is the strategy-side row; these are continuous-verification anchors for the architecture
  unlock.

#### Change M4 — extend the SSOT touchpoint map (line 306 "Hot-reload semantics" row)

- **Location**: line 306 § "SSOT touchpoint map" — "Hot-reload semantics" row
- **Current**:
  `/codex/06-coding-standards/config-reloader-pattern.md · /codex/04-architecture/live-strategy-config-hot-reload.md (new — work-stream F)`
- **Change**: append
  `· /codex/04-architecture/trading-agent-service-directive-pipeline.md (new — see architecture-unlock plan Phase 8)`
- **Rationale**: new codex SSOT for the directive-flow architecture (allocator → directive → strategy reloader → capital
  weights).

#### Change M5 — add Item 24 to "Codex SSOT gaps to fill alongside the work" (line 1503-1517 § F)

- **Location**: line 1505 § F · Codex SSOT gaps to fill alongside the work
- **Add**:
  - `- [ ] [DOC] /codex/04-architecture/trading-agent-service-directive-pipeline.md (work-stream G new — see trading_agent_service_architecture_unlock plan)`
- **Rationale**: parent-master-plan tracks new codex SSOT creation.

#### Change M6 — add `last_executed` row to continuous-verification table

- **Location**: search for the per-item "Last verified" column in master's Group-C verification matrix
- **Add**: new row per the 4 items in M3 with `Last verified: PENDING` placeholders

---

### 2. `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` — MUST CHANGE (P0)

#### Change PW1 — add directive-reloader integration note to Phase 1 (carry/APD VM launch)

- **Location**: search for the Phase that first instantiates the strategy VM via `colocated_engine.py` (likely Phase 1
  "VM launcher additions") — add a sub-bullet
- **Add** (under Phase 1's existing launcher items):
  - `- [ ] [CODE] P1. `colocated_engine.py`instantiates`StrategyDirectiveReloader`at boot (no-op default if no directive present); reloader reads from same config-hot-reload bus as existing`config_reloaders.py`. See trading_agent_service_architecture_unlock plan Phase 5. Off-by-default for May-23: no upstream emitter wired except no-op stub.`
- **Rationale**: the CLI promote path is where the strategy VM gets instantiated; the directive reloader needs to be
  wired at the same point or the architecture is broken. SAFE because default is no-op (existing static config path
  preserved).

#### Change PW2 — add Phase X stub under U-track for directive consumer

- **Location**: search for "Phase U" section (UI track Phases U1-U6)
- **Add** banner-level note above Phase U section:
  - `> **Cross-link 2026-05-20**: directive emission path is wired by trading_agent_service_architecture_unlock plan Phase 5+6. UI promote button MAY emit `AllocationDirective` post-cutover (see promote_workflow_post_cutover_ui_pipeline plan). For May-23, UI promote → MinimalCandidateManifest (existing scope); directive emission stays no-op.`
- **Rationale**: closes potential ambiguity — UI promote does NOT touch directive emission for May-23.

---

### 3. `plans/active/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` — MUST CHANGE (P0)

#### Change F1 — add `performance_features` subdomain scaffold to Phase-A or new Phase-H

- **Location**: insert after the existing phases (Phase-A through Phase-G), add new Phase-H
- **Add** new phase block:

  ```markdown
  ## Phase-H: performance-features subdomain passthrough scaffold (P1, ~0.4 days, ARCHITECTURE-ONLY)

  Per operator directive 2026-05-20 "trading-agent-service architecture unlocked": features-service needs the consumer
  surface for performance-derived features to exist even if it only computes passthrough today. Adds the
  `features_service/performance_features/` package; trading-agent-service reads from this surface post-cutover.

  - [ ] [AGENT] P1. Create `features_service/performance_features/__init__.py` + `passthrough_compute.py` that
        subscribes to `StrategyPnlStreamEvent` and emits FeaturesComputedEvent with feature_group=`performance_features`
        containing the raw PnL fields (no derivation today). Output parquet at canonical manifest v5 path.
  - [ ] [AGENT] P1. Add `performance_features` to features-service CLI dispatcher:
        `python -m features_service --operation compute --feature-group performance_features --asset-group <ag>` works
        (no-op passthrough today).
  - [ ] [AGENT] P1. Manifest write: emit `record_empty(reason=EXPECTED_NO_PNL_STREAM)` when no upstream PnL events
        received for the day (off-by-default state).
  - [ ] [TEST] P1. Unit test: subscribe-and-emit passthrough preserves all fields end-to-end; honest-absence path emits
        expected reason.

  **Done gate**: features-service QG green; manifest shows `performance_features` row with `empty_confirmed` reason
  `EXPECTED_NO_PNL_STREAM` for May-23 lead pair; consumer surface exists, no derivation.
  ```

- **Rationale**: trading-agent-service consumes performance features; this is the producer-side scaffold. Passthrough
  today, real derivations post-cutover.

---

### 4. `plans/active/uac_source_capability_metadata_promotion_2026_05_20.md` — NO CONFLICT (coordinate only)

- **Audit conclusion**: slot-3 plan touches `unified_api_contracts/registry/capability.py` +
  `capability_declarations/` + `venue_launch_dates.py`. The new architecture-unlock UAC additions
  (`unified_api_contracts/internal/strategy_pnl_stream.py` + `unified_api_contracts/internal/strategy_directives.py`)
  land in a **different top-level directory** (`internal/` vs `registry/`). No file overlap.
- **No edit needed** to this plan.
- **Sequencing note in new architecture-unlock plan**: Phase 1+4 UAC schema-addition does NOT need to block on slot-3's
  Phase 1.5 schema test (orthogonal modules); both can land in parallel. Add a one-line note in new plan's "Pre-Audit
  Before Execution" section confirming non-conflict.

---

### 5. `plans/active/issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md` — MUST CHANGE (elevate priority)

#### Change Q1 — elevate severity P2 → P0 + flip status

- **Location**: frontmatter line 10
  `severity: P2 — single-repo failure; workspace-qg Phase B succeeded for the other 20`
- **Change to**:
  `severity: P0 — trading-agent-service on May-23 architecture-unlock path per operator directive 2026-05-20; CI green required for layer-7 service`
- **Rationale**: operator directive 2026-05-20 puts trading-agent-service on May-23 critical path; its CI green is now a
  continuous-verification anchor.

#### Change Q2 — flip status section

- **Location**: bottom "Triage — 2026-05-18" section (line 120-124)
- **Add new section below**:

  ```markdown
  ## Triage update — 2026-05-20 (operator directive: architecture unlocked)

  **Status**: OPEN-P0 (was BLOCKED-CREDENTIALS-deferred-post-cutover) **Reason**: trading-agent-service now on May-23
  architecture-unlock path. CI hygiene fix needed for layer-7 continuous verification. **Slot owner**: assigned to
  architecture-unlock plan Phase 7 (CI hygiene). **Operator ask** (CREDENTIAL APPROVAL REQUEST per CLAUDE.md "External
  Data Is Always Available" rule):

  - Rotate `GH_PAT` secret on `IggyIkenna/trading-agent-service` to match the working value on `IggyIkenna/mtds`
  - `gh secret set GH_PAT --repo IggyIkenna/trading-agent-service --body "$VALID_FINE_GRAINED_PAT"`
  - Without it: trading-agent-service workspace-qg stays red; architecture unlock is "shipped but unverified by CI"
    **Workaround until unblock**: per-repo `bash scripts/quality-gates.sh` local invocation by the implementing slot.
  ```

- **Rationale**: closes the gap between "operator directive landed" and "issue still flagged
  BLOCKED-CREDENTIALS-deferred".

---

### 6. `plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md` — MUST CHANGE (P0, epic-level scaffolding)

- **Audit finding**: epic line 196-206 (§1.7 Phase 10.7 — Allocator-as-shared-service split) already scopes
  `IM-side allocator`, `Trading-platform-side allocator`, `Shared allocator core`, `AllocationDirective` emission path
  as P1 post-cutover. Operator directive 2026-05-20 brings the **scaffold-and-data-flow** portion forward.

#### Change E1 — add status banner to Phase 10.7

- **Location**: line 194 § "1.7 Phase 10.7 — Allocator-as-shared-service split"
- **Add immediately under heading**:
  ```markdown
  > **🟢 ARCHITECTURE-UNLOCK 2026-05-20** (operator directive): the **dataflow scaffold** of Phase 10.7 ships May-23 via
  > [`trading_agent_service_architecture_unlock_2026_05_22.md`](../active/trading_agent_service_architecture_unlock_2026_05_22.md).
  > Specifically: `AllocationDirective` UAC model lands; shared-allocator-core stub at
  > `strategy_service/portfolio_allocator/` emits no-op directives; strategy-service `StrategyDirectiveReloader`
  > consumes directives via existing config_reloaders.py pattern. **Production allocator logic + IM-side +
  > Trading-platform-side UIs stay P1 post-cutover.**
  ```
- **Rationale**: keeps the epic's post-cutover scope intact while signalling that the scaffold ships earlier.

#### Change E2 — add status banner to Phase "Allocator service (8 archetype engines)" (line 267-275)

- **Location**: line 267 § "Allocator service (8 archetype engines)"
- **Add immediately under heading**:
  ```markdown
  > **🟢 ARCHITECTURE-UNLOCK 2026-05-20**: the 8th item "Service scaffolding: ServiceBootstrap, Health API +
  > data_freshness, typed config reloader, SM keys" ships May-23 in trading-agent-service via architecture-unlock plan
  > Phase 6. The 7 archetype-engine items + guard rails + shadow mode + NAV reads stay post-cutover.
  ```

---

### 7. `plans/active/strategy_repo_consolidation_2026_05_19.md` — SHOULD CHANGE (secondary)

#### Change SR1 — add directive-reloader call-site to Phase 5 lift sharpening

- **Location**: line 456 § "P1 Phase 5 lifts sharpened — config_reloaders.py is duplicated 4×"
- **Add sub-bullet**:
  - `- [ ] [AGENT] P2. After May-23 architecture unlock, the `StrategyDirectiveReloader`becomes the 5th typed-reloader callsite; lift into UTL as`make_directive_reloader()`alongside`make_config_reloader()` per epic §1.7. POST-CUTOVER.`
- **Rationale**: forward-link so the post-cutover UTL lift consolidates the directive-reloader at the same time as
  config_reloaders.py.

---

### 8. `plans/active/strategy_archetype_taxonomy_2026_05_12.md` — SHOULD CHANGE (secondary)

#### Change SA1 — add PnL-emission contract row to per-archetype matrix

- **Location**: search for the per-archetype taxonomy matrix (it lists 9 families / 53 archetypes)
- **Add column** "Emits StrategyPnlStreamEvent" with values:
  - `carry_staked_basis`: ✅ May-23 (per architecture-unlock plan Phase 2)
  - `arbitrage_price_dispersion`: ✅ May-23 (per architecture-unlock plan Phase 2)
  - All other 51 archetypes: TODO post-cutover (when continuous-paper infrastructure lands per archetype)
- **Rationale**: codifies the per-archetype PnL emission readiness as part of the taxonomy SSOT.

---

### 9. `plans/active/features_repo_consolidation_2026_05_08.md` — SHOULD CHANGE (secondary)

#### Change FC1 — add performance_features subdomain to consolidation scope

- **Location**: search for the per-family scaffold section (`features_service/cefi/`, `features_service/onchain/`,
  `features_service/sports/`, etc.)
- **Add new subdomain entry**:
  - `- [ ] [AGENT] P1. `features_service/performance_features/` subdomain — passthrough scaffold for trading-agent-service performance-derived features. See phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md Phase-H.`
- **Rationale**: features-repo-consolidation is the SSOT for which subdomains exist; new subdomain needs to be
  enumerated.

---

### 10. Per-archetype plans (defer to follow-up sweep)

For each of the following plans, add a single line in the frontmatter `related_plans:` list pointing to the new
architecture-unlock plan; add a one-line body note:
`Emits StrategyPnlStreamEvent per UAC contract (see trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this plan's May-23 scope.`

Plans (deferred to follow-up sweep — NOT blocking the new architecture-unlock plan):

- `plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`
- `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`
- `plans/active/cme_polymarket_arb_2026_05_08.md`
- `plans/active/dex_perp_and_venue_data_expansion_2026_05_12.md`
- `plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`
- `plans/epics/cefi_master.md`
- `plans/epics/defi_master.md`
- `plans/epics/sports_master.md`
- `plans/epics/predictions_master.md`
- `plans/epics/tradfi_master.md`

---

## Top 3 highest-impact plan edits

1. **`master_to_live_defi_2026_05_23.md` Change M1+M2+M3** — flips the cutover-tier classification + adds 4 readiness
   items. This is the single most-load-bearing edit; every other plan inherits its status from this row.
2. **`promote_workflow_may23_cli_path_2026_05_10.md` Change PW1** — wires the directive-reloader at
   `colocated_engine.py` instantiation point. Without this, the architecture has no boot-time entry; with it,
   off-by-default safety holds.
3. **`phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` Change F1** — adds Phase-H performance_features
   subdomain. This is the consumer-surface scaffold trading-agent-service reads from; without it, the agent service has
   no producer to subscribe to.

## Irreducible May-23 risk to flag

- **Risk R1 (P2)**: `trading-agent-service` GH_PAT credential rotation (issue Q2 in this manifest) requires operator
  action. Without it, layer-7 CI stays red — architecture ships but is not CI-verified. Workaround: per-repo local QG
  invocation by implementing slot.
- **Risk R2 (P3)**: The 4 layer-N prerequisite greens (UAC schema additions ~0.5 day · strategy PnL emission ~1 day ·
  features performance-features scaffold ~0.5 day · strategy directive reloader ~0.5 day) total 2.5 cal-AI-days against
  a May-23 deadline that is 3 days out (2026-05-20 → 2026-05-23). Foundation-gate feasibility is tight but achievable
  with 2 parallel slots — slot-1 (UAC) + slot-N (strategy + features in series). New plan declares this in Phase
  ordering.
- **Risk R3 (P3 — soft)**: trading-agent-service repo is currently under-staffed in the work-split (no slot assigned per
  2026-05-19 work-split sweep). Operator may need to allocate a slot or accept slot-1-main spawns sub-agents to execute
  the new plan.

## Approval checklist (operator review)

- [x] Operator acknowledges Tier-1 architecture-only sub-tier classification (Change M2)
- [x] Operator confirms directive emission is off-by-default for May-23 cutover (no auto re-weighting)
- [x] Operator approves GH_PAT rotation for trading-agent-service (Risk R1 unblock)
- [x] Operator approves slot allocation for new architecture-unlock plan execution (Risk R3)

Once all 4 boxes ticked → slot-1-main applies manifest entries in order: M1-M6 → PW1-PW2 → F1 → Q1-Q2 → E1-E2 → SR1 →
SA1 → FC1 → per-archetype sweep. Estimated ~0.8 cal-AI-days of plan-edit work.

## Status update — 2026-05-22

**BLOCKED-OPERATOR**: requires operator to tick the 4 approval checklist items above before slot-1-main applies the 10
plan edits. Do not apply the manifest changes until the operator acknowledges all 4 boxes.

## [ACKED-INTO-PLAN] RESOLVED 2026-05-22 — all 10 plan edits applied by slot-1-main per operator directive "do yourself"; 4 approval checklist items ticked
