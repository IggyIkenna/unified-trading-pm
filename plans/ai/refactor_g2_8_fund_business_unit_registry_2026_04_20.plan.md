---
title: Refactor G2.8 — Fund + business_unit + reserving_business_unit_id registry
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.8
  - plans/active/share_class_architecture_2026_04_01.plan.md (folded)
# Wave G2-α — parallel with G2-α peers 2.1, 2.6, 2.9, 2.11. Gates G2.10 (allocator split).
supersedes: [share_class_architecture_2026_04_01.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [share_class_architecture_2026_04_01.plan.md](./share_class_architecture_2026_04_01.plan.md). share_class_architecture
> was folded into G2.8 (Phases A+B shipped per UAC 48bf6ee) See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence anchors.

# Refactor G2.8 — Fund + business_unit + reserving_business_unit_id registry

## Context

Stage 3E §2.8 ships a typed registry of funds, business units, and reserving business-unit IDs. Today
`StrategyAvailabilityRegistry` takes `business_unit ∈ {saas, im_desk, admin}` but no registry declares which BU owns
which `reserving_business_unit_id`. IM operates multiple funds (Reg Umbrella + IM Pooled + per-client SMAs); allocator
call-sites use free-form strings. Stage-3a §3.2 flagged this as adjacent-missing #2.

Target: `FundBusinessUnitRegistry` declared in UAC. Every IM Pooled fund + Reg Umbrella fund + SMA has a typed record
mapping `fund_id → business_unit → reserving_business_unit_id` plus custody model (from 2026-04-20 custody memory).
Allocator + reporting services read from this registry instead of strings. Share-class architecture plan folds here.

## Decisions locked with user (2026-04-20)

| Decision                                                           | Chosen                                                                                                              | Source                                              |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Registry lives in UAC (not strategy-service)                       | Follows Option X pattern from G1.6/G1.7/G1.11; enables cross-service consumption                                    | Wave E closure memory — Option X                    |
| One record per (fund_id, business_unit) pair                       | IM Pooled has one BU; Reg Umbrella has one BU; each SMA has one BU                                                  | Operator 2026-04-20 + share_class_architecture plan |
| Custody model field required                                       | IM SMA + DART = client-owned venue + scoped keys; IM Pooled = Copper custodian + Odum portal subs/redemptions       | Custody-model memory 2026-04-20                     |
| `reserving_business_unit_id` is validated against capacity budgets | Capacity reserved per slot must resolve to a known reserving BU                                                     | Existing StrategyAvailability invariant             |
| POD affiliate stays INTERNAL-ONLY in codex                         | Registry does not surface POD in public copy; naming convention keeps the affiliate invisible to prospect-facing UI | Custody-model memory 2026-04-20                     |

## Cross-references

- **Wave G2-α peers (parallel):** G2.1, G2.6, G2.9, G2.11
- **Downstream Wave G2-β:** G2.10 allocator UI split (consumes this registry)
- **Folded plan:** `plans/active/share_class_architecture_2026_04_01.plan.md` — full scope absorbed
- **G1 cross-refs:** G1.6 derivation engine (allocator call-sites), G1.11 service-family scope (audience mapping)
- **Codex docs:** `/codex/14-playbooks/shared-core/fund-administration-and-custody.md`,
  `/codex/14-playbooks/shared-core/treasury-and-subaccount-model.md`,
  `/codex/14-playbooks/cross-cutting/sma-vs-pooled.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.8
2. `plans/active/share_class_architecture_2026_04_01.plan.md` — full
3. `/codex/14-playbooks/shared-core/fund-administration-and-custody.md` — custody model SSOT
4. `/codex/14-playbooks/shared-core/treasury-and-subaccount-model.md`
5. `/codex/14-playbooks/cross-cutting/sma-vs-pooled.md`
6. `/codex/14-playbooks/shared-core/org-fund-client-entity-model.md`
7. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py` — existing
   `StrategyAvailabilityEntry` with `business_unit` field
8. `strategy-service/strategy_service/portfolio_allocator/service.py` — consumer call-site

## Out of scope

- Allocator UI split (G2.10)
- Custody integrations (out-of-scope even for G3; Copper + treasury integrations are a separate initiative)
- Touching existing `StrategyAvailabilityEntry` schema beyond adding a `reserving_business_unit_id` reference
- Surfacing POD affiliate in public UI — INTERNAL-ONLY per custody memory
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Registry schema — SHIPPED 2026-04-22 (UAC `48bf6ee`)

- [x] [AGENT] P0. Declare `FundBusinessUnitEntry` Pydantic model at
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/fund_business_unit.py`:
      `{fund_id, fund_name, business_unit, reserving_business_unit_id, custody_model, service_family, notes?}`.
- [x] [AGENT] P0. `custody_model` enum: `CLIENT_OWNED_VENUE | COPPER_CUSTODIAN | NOT_APPLICABLE`.
- [x] [AGENT] P0. `FUND_BUSINESS_UNIT_REGISTRY: tuple[FundBusinessUnitEntry, ...]` module-level tuple with seed records:
      IM Pooled (Copper), Reg Umbrella (client-owned), per-client SMA fixtures, admin, IM-desk.
- [x] [AGENT] P0. Helper functions: `fund_for(fund_id) -> FundBusinessUnitEntry`,
      `funds_for_business_unit(business_unit) -> tuple[FundBusinessUnitEntry, ...]`,
      `reserving_business_unit_for(fund_id) -> str`.

### Phase B — UAC tests + codex parity

- [x] [AGENT] P0. `unified-api-contracts/tests/internal/unit/test_fund_business_unit.py` — ≥10 cases: every seeded
      record retrievable; invariant: each `fund_id` unique; invariant: `reserving_business_unit_id` resolves to a known
      business_unit.
- [x] [AGENT] P0. Codex parity test — structural check that
      `/codex/14-playbooks/shared-core/fund-administration-and-custody.md`'s fund list matches the registry records.

### Phase C — Allocator call-site refactor — DEFERRED to G2.10

- [ ] [AGENT] P0. Update `strategy-service/strategy_service/portfolio_allocator/service.py` to lookup
      `reserving_business_unit_id` via `reserving_business_unit_for(fund_id)` instead of string concatenation.
- [ ] [AGENT] P0. Update allocator tests to assert registry-driven lookups.

> **Amendment 2026-04-22:** `ClientAllocatorInstance` does not currently carry `fund_id`; it only carries
> `business_unit ∈ {saas, im_desk, admin}` (the 3-value literal). The plan's "replace string concatenation" phrasing
> anticipated a signature that doesn't exist. Adding `fund_id` to `ClientAllocatorInstance` is a bigger surface change
> that naturally folds into the G2.10 allocator UI split (which introduces fund-dropdown selection). **Phase C is
> therefore deferred into G2.10's execution scope**; the UAC registry from Phase A is already usable by any fund-aware
> caller via `reserving_business_unit_for(fund_id)`.

### Phase D — UI consumers

- [ ] [AGENT] P0. TypeScript mirror at `unified-trading-system-ui/lib/architecture-v2/fund-business-unit.ts`
      (auto-generated or hand-synced — document which pattern and add sync-script if hand-synced).
- [ ] [AGENT] P0. Any allocator-UI consumers (limited today; more in G2.10) read the registry via a helper hook.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd strategy-service && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-8-fund-registry.spec.ts` — admin view renders fund list matching
      registry.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/fund_business_unit.py` — NEW
- `unified-api-contracts/tests/internal/unit/test_fund_business_unit.py` — NEW
- `strategy-service/strategy_service/portfolio_allocator/service.py` — MODIFY
- `strategy-service/tests/unit/portfolio_allocator/test_service.py` — MODIFY (or new cases)
- `unified-trading-system-ui/lib/architecture-v2/fund-business-unit.ts` — NEW
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-8-fund-registry.spec.ts` — NEW

## Execution DAG

```
A (schema) → B (tests + codex parity)
               ↓
             C (allocator refactor) + D (UI consumers) [parallel]
               ↓
             E (QG + Playwright)
```

## Verification

1. `FundBusinessUnitRegistry` exports ≥6 seeded records covering IM Pooled, Reg Umbrella, 2+ SMA fixtures, admin,
   IM-desk.
2. UAC tests: ≥10 cases green.
3. Codex parity test: fund list matches SSOT doc.
4. strategy-service allocator: test count maintained or raised; registry-driven lookups assert.
5. TS mirror sync: drift check returns zero diff.
6. Playwright spec green.

## Handoff

Unblocks:

- **G2.10** — allocator UI split can render per-fund views.
- **G2.1 indirectly** — JWT `fund_id` + `business_unit_id` claims reference registry records.
- **Reporting surfaces** — any per-fund reporting now has a typed source for fund metadata.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools as admin persona. Navigate to admin
fund-registry view; assert each seeded `FundBusinessUnitEntry` renders with correct `business_unit`, `custody_model`,
`reserving_business_unit_id`.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-8-fund-registry.spec.ts`:

1. Seed admin persona via `seed-persona.ts`.
2. Navigate to registry view.
3. Assert all registry records render.
4. Assert no POD affiliate name surfaces in public DOM (INTERNAL-ONLY invariant).
5. Include orphan-reachability assertion.
6. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.8 (Wave G2-α, parallel with
G2.1/2.6/2.9/2.11).**

---

You are executing **Refactor G2.8 — Fund + business_unit + reserving_business_unit_id registry** for the Unified Trading
System at Odum Research. Wave G2-α.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py
ls /codex/14-playbooks/shared-core/fund-administration-and-custody.md 2>/dev/null || echo "verify codex path"
ls strategy-service/strategy_service/portfolio_allocator/service.py
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_8_fund_business_unit_registry_2026_04_20.plan.md`

### Read-set (mandatory)

All 8 paths from the plan's Mandatory read-set. Pay special attention to
`shared-core/fund-administration-and-custody.md` — the public-vs-internal custody-model distinction (IM SMA + DART
client-owned vs IM Pooled Copper-custodied) is load-bearing, and POD affiliate must stay INTERNAL-ONLY in all code
comments + public UI strings.

### Deliverables

Per plan's Critical files list — 6 files across 3 repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (tier-1 dev) through MCP Playwright tools as admin persona. Navigate the admin fund-registry
view; assert each seeded `FundBusinessUnitEntry` renders with correct attributes. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-8-fund-registry.spec.ts` — seeded via
`seed-persona.ts`, asserting registry records render, asserting POD affiliate does NOT surface publicly, wired into
`scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Three repos touched → three commits. `git pull --rebase` before each push.

```
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.8 — FundBusinessUnitRegistry + helpers" --agent
cd ../strategy-service && bash scripts/quickmerge.sh "refactor(allocator): G2.8 — registry-driven reserving BU lookup" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(arch-v2): G2.8 — TS mirror of fund-business-unit registry + Playwright spec" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ ≥6 seeded `FundBusinessUnitEntry` records in UAC registry.
2. ✅ ≥10 UAC tests green; codex parity test green.
3. ✅ strategy-service allocator tests still green + registry-driven lookup asserted.
4. ✅ TS mirror drift check: zero.
5. ✅ Playwright spec green; POD affiliate invariant green.
6. ✅ QG green on all three repos.
7. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT surface POD affiliate in public UI or user-facing strings — INTERNAL-ONLY per custody memory.
- Do NOT rewrite `StrategyAvailabilityEntry` schema — this plan only references its `business_unit` field.
- Do NOT ship custody integrations (Copper, treasury) — registry metadata only.
- Do NOT delete `share_class_architecture_2026_04_01.plan.md` — mark as superseded in its frontmatter, retain history.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Registry record count + list.
- UAC test count + pass rate.
- Allocator tests diff.
- TS mirror sync pattern (auto-gen or hand-synced).
- Playwright spec pass status.
- QG results (3 repos).
- 3 commit SHAs pushed to live-defi-rollout.
