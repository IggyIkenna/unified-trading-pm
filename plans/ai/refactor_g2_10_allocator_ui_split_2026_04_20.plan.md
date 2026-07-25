---
title: Refactor G2.10 — Phase 10.7 portfolio-allocator UI split (IM-side vs trading-platform-side)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §2.10
  - refactor_g2_1_org_scoped_jwt_claims_2026_04_20.plan.md
  - refactor_g2_8_fund_business_unit_registry_2026_04_20.plan.md
  - plans/active/platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md (folded)
# Wave G2-β — sequential after G2-α. Parallel with G2.2, G2.7.
# ROUTE-GROUP AMENDMENT 2026-04-22: Next.js app router uses `(platform)` route group for authenticated surfaces.
# All `app/services/...` paths below should read `app/(platform)/services/...`. Public pages stay in `(public)`.
supersedes: [platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md](./platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md).
> platform_strategy_families was folded into G2.10 per depends_on (folded) marker See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Refactor G2.10 — Phase 10.7 portfolio-allocator UI split

## Context

Stage 3E §2.10 ships Phase 10.7 of the strategy-architecture-v2 rollout: split the allocator UI into two distinct
surfaces on the same `portfolio_allocator` core. Today `/services/research/strategy/allocator` is a single surface
serving both IM-desk and trading-platform-subscriber audiences — but these audiences have different workflows (IM-desk
approves proposals manually; trading-platform auto-applies on client infra). Phase 10.6 consumer-surface split already
shipped; 10.7 has been deferred.

Rule 03 also requires that allocator is NOT a research surface — it's a commercial allocation surface. The existing
`/services/research/strategy/allocator` route violates this rule and must be deleted.

Target:

- `/services/investment-management/allocator` (route group `(platform)`) — IM-desk, careful, human-approved
  proposal-then-apply flow.
- `/services/trading-platform/allocator` (route group `(platform)`) — trading-platform-subscriber, auto-apply on client
  infra.
- Research-side allocator page DELETED.
- Same `portfolio_allocator` core; instance-configuration (not code-fork) picks behaviour per-audience.

## Decisions locked with user (2026-04-20)

| Decision                                                                 | Chosen                                                                                                            | Source                              |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Two UI surfaces on the same `portfolio_allocator` core                   | Instance-configuration, not code-fork — Rule 03 same-system-principle                                             | Stage 3E §2.10 + rule 03            |
| Research-side allocator DELETED (not kept as a redirect)                 | Rule 03: allocator is commercial, not research. Hard delete avoids reintroducing the violation                    | Stage 3E §2.10                      |
| IM-side: proposal-then-apply workflow; trading-platform-side: auto-apply | Matches the two audiences' actual operating models                                                                | share_class_architecture + operator |
| Audience resolution via G2.1 `audience` JWT claim                        | Route chosen by claim: `audience=IM_desk` → IM surface; `audience=trading_platform_subscriber` → platform surface | G2.1 + G1.11 rule 12                |
| Fund selection sources from G2.8 FundBusinessUnitRegistry                | Registry-driven dropdowns; no free-form fund names                                                                | G2.8 registry                       |

## Cross-references

- **Upstream:** G2.1 (JWT `audience` claim), G2.8 (fund registry), G1.6 derivation engine (access_control), G1.7
  restriction-profile, Phase 10.5 + 10.6 already shipped
- **Wave G2-β peers (parallel):** G2.2, G2.7
- **Folded plan:** `plans/active/platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md`
- **Codex:** `codex/09-strategy/architecture-v2/` — Phase 10.6 consumer-surface precedent

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.10
2. `plans/active/platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md`
3. `refactor_g2_1_org_scoped_jwt_claims_2026_04_20.plan.md`
4. `refactor_g2_8_fund_business_unit_registry_2026_04_20.plan.md`
5. `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`
6. `/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`
7. `/codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md`
8. `strategy-service/strategy_service/portfolio_allocator/service.py`
9. `unified-trading-system-ui/app/(platform)/services/research/strategy/allocator/page.tsx` (current surface — to
   delete)

## Out of scope

- Changing `portfolio_allocator` core logic — surface-layer only
- Allocator algorithm changes (e.g. new objective functions)
- Cross-fund allocation workflows (future)
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mock-auth seeds `audience` claim via `personas.ts`; staging reads real Firebase claim. Both UI surfaces resolve
identically across environments — no fork.

## Phase breakdown

### Phase A — Surface scaffolding

- [ ] [AGENT] P0. Create `unified-trading-system-ui/app/(platform)/services/investment-management/allocator/page.tsx` —
      new IM-side surface. Proposal-then-apply flow; `<ApprovalQueue>` component.
- [ ] [AGENT] P0. Create `unified-trading-system-ui/app/(platform)/services/trading-platform/allocator/page.tsx` — new
      platform-side surface. Auto-apply flow; `<AllocationApplied>` confirmation component.
- [ ] [AGENT] P0. Lifecycle route mappings updated to register both + remove research-side.

### Phase B — Audience routing

- [ ] [AGENT] P0. `lib/auth/allocator-routing.ts` — `resolveAllocatorRoute(audience)` →
      `/services/investment-management/allocator` (route group `(platform)`) or `/services/trading-platform/allocator`
      (route group `(platform)`).
- [ ] [AGENT] P0. `<AllocatorLink>` component resolves audience from JWT claim + routes correctly.
- [ ] [AGENT] P0. Any legacy link to `/services/research/strategy/allocator` → redirect through `resolveAllocatorRoute`.

### Phase C — IM-side workflow

- [ ] [AGENT] P0. IM-side: allocator proposes changes via strategy-service; UI shows diff; human approver clicks "Apply"
      to commit. `<ApprovalQueue>` lists pending proposals.
- [ ] [AGENT] P0. Fund dropdown populated from G2.8 `FundBusinessUnitRegistry`.
- [ ] [AGENT] P0. Apply action emits UTL event `ALLOCATION_APPLIED_BY_APPROVER`.

### Phase D — Trading-platform-side workflow

- [ ] [AGENT] P0. Platform-side: allocator auto-applies; UI shows confirmation + allocation history.
- [ ] [AGENT] P0. Emits UTL event `ALLOCATION_AUTO_APPLIED` per allocation.

### Phase E — Deletion + redirects

- [ ] [AGENT] P0. DELETE `unified-trading-system-ui/app/(platform)/services/research/strategy/allocator/page.tsx` and
      any nested routes.
- [ ] [AGENT] P0. Add 308 redirect in `next.config.mjs` from `/services/research/strategy/allocator` →
      `/services/investment-management/allocator` (route group `(platform)`) (benign default; audience-router will
      redirect platform users).
- [ ] [AGENT] P0. Remove route from `lib/lifecycle-route-mappings.ts`.

### Phase F — QG + verification

- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd strategy-service && bash scripts/quality-gates.sh` (no code change expected; confirms nothing
      broke).
- [ ] [AGENT] P0. Playwright spec `refactor-g2-10-allocator-split.spec.ts` — 2 audiences, 2 surfaces, deleted-route
      redirect.

## Critical files to be modified

- `unified-trading-system-ui/app/(platform)/services/investment-management/allocator/page.tsx` — NEW
- `unified-trading-system-ui/app/(platform)/services/trading-platform/allocator/page.tsx` — NEW
- `unified-trading-system-ui/app/(platform)/services/research/strategy/allocator/page.tsx` — DELETE
- `unified-trading-system-ui/lib/auth/allocator-routing.ts` — NEW
- `unified-trading-system-ui/components/allocator/ApprovalQueue.tsx` — NEW
- `unified-trading-system-ui/components/allocator/AllocationApplied.tsx` — NEW
- `unified-trading-system-ui/components/allocator/AllocatorLink.tsx` — NEW
- `unified-trading-system-ui/lib/lifecycle-route-mappings.ts` — MODIFY
- `unified-trading-system-ui/next.config.mjs` — MODIFY (redirect)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-10-allocator-split.spec.ts` — NEW

## Execution DAG

```
A (surfaces) → B (audience routing)
                 ↓
               C (IM workflow) + D (platform workflow) [parallel]
                 ↓
               E (delete research-side + redirects)
                 ↓
               F (QG + Playwright)
```

## Verification

1. Two allocator surfaces render per audience.
2. Research-side allocator route returns 308 → IM-side.
3. IM-side: proposal → approve → apply round-trip green.
4. Platform-side: auto-apply round-trip green.
5. UTL events emitted for both paths.
6. Playwright spec green.
7. QG green on UI + strategy-service.

## Handoff

Unblocks:

- **pb3b `investment-management-demo.md`** — IM allocator surface becomes demoable.
- **pb3c `dart-demo.md`** — trading-platform allocator surface becomes demoable.
- **Rule 03** — no-forked-UIs violation closed.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools as `im-desk` persona; walk through
proposal → approve → apply flow. Switch to `trading-platform-subscriber` persona; verify auto-apply rendering. Visit the
deleted research-side URL; assert 308 redirect.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-10-allocator-split.spec.ts`:

1. Seed `im-desk` persona; navigate to `/services/investment-management/allocator` (route group `(platform)`); assert
   proposal queue renders.
2. Approve a proposal; assert `ALLOCATION_APPLIED_BY_APPROVER` event.
3. Seed `trading-platform-subscriber` persona; navigate to `/services/trading-platform/allocator` (route group
   `(platform)`); assert auto-apply confirmation.
4. Navigate to legacy `/services/research/strategy/allocator`; assert 308 redirect.
5. Include orphan-reachability assertion.
6. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.10 (Wave G2-β).**

---

You are executing **Refactor G2.10 — Portfolio-allocator UI split** for the Unified Trading System at Odum Research.
Wave G2-β; G2.1 + G2.8 must be shipped.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
# Verify G2.1 + G2.8 shipped
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/jwt_claims.py 2>/dev/null || echo "G2.1 NOT SHIPPED"
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/fund_business_unit.py 2>/dev/null || echo "G2.8 NOT SHIPPED"
ls unified-trading-system-ui/app/(platform)/services/research/strategy/allocator/page.tsx  # must exist to delete
```

All gates green + research-side page exists (to delete). STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through F of this plan:
`plans/active/refactor_g2_10_allocator_ui_split_2026_04_20.plan.md`

### Read-set (mandatory)

All 9 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 10 files in UI repo.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools as `im-desk` persona + `trading-platform-subscriber` persona +
verify the 308 redirect for the deleted research-side URL. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-10-allocator-split.spec.ts` — 2 personas, 2
surfaces, deletion redirect, approval round-trip, auto-apply round-trip; wired into `scripts/quality-gates.sh`,
including orphan-reachability.

### Commit strategy

Primarily UI repo — one commit.

```
cd unified-trading-system-ui && bash scripts/quickmerge.sh "feat(allocator): G2.10 — IM + trading-platform surface split + research-side removal" --agent
```

Manual-git fallback if quickmerge blocks. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Two new allocator surfaces render.
2. ✅ Research-side allocator deleted + 308 redirect live.
3. ✅ Audience-claim routing works.
4. ✅ IM-side proposal-apply flow green.
5. ✅ Platform-side auto-apply flow green.
6. ✅ UTL events emitted.
7. ✅ Playwright spec green.
8. ✅ UI QG green.
9. ✅ 1 commit SHA pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT modify `portfolio_allocator` core logic — surface-layer split only.
- Do NOT keep the research-side allocator as a live route — rule 03 violation.
- Do NOT hardcode fund names — pull from G2.8 registry.
- Do NOT let platform users see the IM approval queue (distinct surfaces per audience).
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Two new surface routes verified rendering.
- Research-side deletion + redirect verified.
- Audience routing test results.
- UTL event emission verified.
- Playwright spec pass status.
- UI QG results.
- 1 commit SHA pushed to live-defi-rollout.
