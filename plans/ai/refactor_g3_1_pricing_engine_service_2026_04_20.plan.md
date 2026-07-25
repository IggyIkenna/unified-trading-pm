---
title: Refactor G3.1 — Pricing-engine service
status: active
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §3.1
  - refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md
  - refactor_g3_2_pricing_numbers_from_finance_2026_04_20.plan.md
  - refactor_g2_2_per_client_api_key_issuance_2026_04_20.plan.md
# Wave G3-β — sequential after G2 + G3.2. Gates on G1.6 + G2.2 + G3.2.
---

# Refactor G3.1 — Pricing-engine service

## Context

Stage 3E §3.1 ships a pricing-engine service that exposes G1.6's `cost(combo, tier, integration_depth) -> PriceQuote`
formula as a REST endpoint. Today the formula exists as a pure function in UAC but nothing serves it to callers —
proposals are built by hand and the billing service does not reconcile against a programmatic cost source.

Target: `pricing-engine-service` (new) OR `strategy-service/availability/pricing/` (extension per stage-3c §5). Reads
populated numbers from `commercial-model/pricing-building-blocks.md` (once G3.2 populates). Exposes
`GET /api/pricing/quote?combo=&tier=&depth=`. Capability-gated via G2.2 API-key scope `ADMIN_OVERRIDE_COVERAGE` for
`tier=internal` reads. Billing reconciles monthly against this.

## Decisions locked with user (2026-04-20)

| Decision                                                                     | Chosen                                                                | Source                      |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------- |
| Ship as `strategy-service/availability/pricing/` extension                   | Lower lift than new service; stage-3c §5 already suggests this layout | Stage 3E §3.1 + stage-3c §5 |
| Numbers sourced from pricing-building-blocks.md (populated by G3.2)          | Single SSOT for commercial numbers                                    | G3.2 hand-off               |
| `tier=internal` response capability-gated on `ADMIN_OVERRIDE_COVERAGE` scope | Internal cost never leaks to clients                                  | Rule 08 + G2.2 scope enum   |
| Endpoint: `GET /api/pricing/quote?combo=&tier=&depth=`                       | Simple REST; clients can integrate                                    | Stage 3E §3.1               |
| Billing reconciliation monthly                                               | Quarterly is too slow; monthly matches invoicing cadence              | Operator 2026-04-20         |

## Cross-references

- **Upstream:** G1.6 derivation engine (`cost()`), G3.2 populated numbers, G2.2 API-key scope enum
- **Wave G3-β dependencies:** G2-α + G2-β + G3.2 all shipped
- **Codex:** `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md`,
  `/codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md` §5
- **Billing service:** will reconcile against this endpoint (separate plan, out of scope here)

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §3.1
2. `/codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md` §5 (pricing sub-package layout)
3. `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`
4. `refactor_g3_2_pricing_numbers_from_finance_2026_04_20.plan.md`
5. `refactor_g2_2_per_client_api_key_issuance_2026_04_20.plan.md`
6. `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md`
7. `/codex/14-playbooks/_ssot-rules/08-internal-cost-leakage.md`
8. `strategy-service/strategy_service/availability/` — Phase 10.5 infrastructure
9. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py` — `cost()` formula

## Out of scope

- Billing service reconciliation implementation (separate plan)
- Admin UI `/admin/pricing/quote-builder` (future — requires real number availability)
- Contract generation (separate initiative)
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mock mode serves shape-only quotes (TODO_numeric markers from G1.6 `cost()` output); staging reads populated
numbers. Both paths flow through the same HTTP contract. Playwright asserts identical response shapes.

## Phase breakdown

### Phase A — Pricing sub-package

- [ ] [AGENT] P0. Create `strategy-service/strategy_service/availability/pricing/__init__.py` + `registry.py` +
      `loader.py`.
- [ ] [AGENT] P0. `loader.py` — reads `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md` + parses
      the 13-row × 3-col table into `PricingRegistry`.
- [ ] [AGENT] P0. Inject `PricingRegistry` into `cost()` calls (UAC `cost()` accepts `pricing_registry` kwarg; this
      wires it up server-side).

### Phase B — REST endpoint

- [ ] [AGENT] P0. `strategy-service/strategy_service/api/pricing_router.py` — FastAPI router with
      `GET /api/pricing/quote?combo=&tier=&depth=`. Decodes combo string → `Combo` object; calls `cost()`; returns JSON.
- [ ] [AGENT] P0. Capability-gate: `tier=internal` requires JWT claim or API-key scope including
      `ADMIN_OVERRIDE_COVERAGE`. Returns 403 otherwise.
- [ ] [AGENT] P0. `tier=tier_a`, `tier=tier_b` accessible to any authenticated caller.

### Phase C — Tests + integration

- [ ] [AGENT] P0. `strategy-service/tests/api/test_pricing_router.py` — ≥10 cases: valid quote per tier, unauthorised
      internal-tier request, unknown combo, malformed params, depth bounds.
- [ ] [AGENT] P0. Integration test: round-trip combo encode/decode via endpoint.

### Phase D — Codex + admin stub

- [ ] [AGENT] P0. Codex doc `/codex/06-coding-standards/pricing-engine-endpoint.md` — describes HTTP contract + scope
      requirement.
- [ ] [AGENT] P0. Admin UI stub at `/admin/pricing/quote-builder/page.tsx` — shape-only form + endpoint call (full
      polish post G3.2 number population).

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd strategy-service && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g3-1-pricing-engine.spec.ts` — admin quote-builder stub renders + endpoint
      call round-trip.
- [ ] [AGENT] P0. Scope-enforcement smoke: call with internal-tier without scope → 403; with scope → 200.

## Critical files to be modified

- `strategy-service/strategy_service/availability/pricing/__init__.py` — NEW
- `strategy-service/strategy_service/availability/pricing/registry.py` — NEW
- `strategy-service/strategy_service/availability/pricing/loader.py` — NEW
- `strategy-service/strategy_service/api/pricing_router.py` — NEW
- `strategy-service/tests/api/test_pricing_router.py` — NEW
- `strategy-service/strategy_service/api/main.py` — MODIFY (register router)
- `/codex/06-coding-standards/pricing-engine-endpoint.md` — NEW
- `unified-trading-system-ui/app/admin/pricing/quote-builder/page.tsx` — NEW (stub)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-1-pricing-engine.spec.ts` — NEW

## Execution DAG

```
A (pricing sub-package + loader) → B (REST endpoint)
                                    ↓
                                  C (tests + integration)
                                    ↓
                                  D (codex + admin stub)
                                    ↓
                                  E (QG + Playwright + scope smoke)
```

## Verification

1. Pricing sub-package loads numbers from codex doc.
2. REST endpoint serves quotes per tier.
3. Scope enforcement: internal-tier requires `ADMIN_OVERRIDE_COVERAGE`.
4. ≥10 unit tests green.
5. Playwright spec green.
6. Scope-enforcement smoke: 403/200 round-trip.
7. QG green on strategy-service + UI.

## Handoff

Unblocks:

- **Billing service reconciliation** — monthly billing pulls from this endpoint.
- **pb2a/b/c proposal generation** — automated quoting at scale.
- **Commercial-ops automation** — contract generators read canonical numbers.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI) + hit strategy-service REST endpoint via MCP tools. Verify
admin quote-builder stub renders, calls endpoint, returns shape-only or populated quote per environment.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-1-pricing-engine.spec.ts`:

1. Seed admin persona.
2. Navigate quote-builder; submit combo + tier=tier_a; assert quote renders.
3. Submit tier=internal without scope; assert 403 / error message.
4. Seed admin with `ADMIN_OVERRIDE_COVERAGE` scope; submit tier=internal; assert quote renders.
5. Include orphan-reachability.
6. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G3.1 (Wave G3-β).**

---

You are executing **Refactor G3.1 — Pricing-engine service** for the Unified Trading System at Odum Research. Wave G3-β;
G1.6 + G2.2 + G3.2 all must be shipped.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
# Verify upstream gates
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py  # G1.6
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/api_keys.py 2>/dev/null || echo "G2.2 NOT SHIPPED"
grep -q "# populated" /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md 2>/dev/null || echo "G3.2 NOT SHIPPED (ship with TODO sentinels for now)"
```

All must exist. STOP if G1.6 missing. G2.2 + G3.2 are hard gates.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g3_1_pricing_engine_service_2026_04_20.plan.md`

### Read-set (mandatory)

All 9 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 9 file changes across 3 repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools as admin persona. Navigate quote-builder stub; verify endpoint call
round-trip + scope-enforcement behaviour (403 without scope, 200 with). Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-1-pricing-engine.spec.ts` — full flow + scope
enforcement + orphan-reachability, wired into `scripts/quality-gates.sh`.

### Commit strategy

Three repos touched → three commits. `git pull --rebase` before each push.

```
cd strategy-service && bash scripts/quickmerge.sh "feat(pricing): G3.1 — pricing-engine sub-package + REST endpoint + scope gating" --agent
cd ../unified-trading-pm && bash scripts/quickmerge.sh "docs(codex): G3.1 — pricing-engine-endpoint contract doc" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(admin): G3.1 — quote-builder stub + Playwright spec" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Pricing sub-package loads numbers from codex.
2. ✅ REST endpoint serves 3 tiers.
3. ✅ Scope enforcement: internal-tier gates on `ADMIN_OVERRIDE_COVERAGE`.
4. ✅ ≥10 unit tests green.
5. ✅ Playwright spec green.
6. ✅ Scope smoke 403/200 green.
7. ✅ QG green on 2 repos (strategy-service + UI).
8. ✅ 3 commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT surface tier=internal response without scope gate — rule 08.
- Do NOT duplicate cost() formula — always call the UAC function.
- Do NOT hard-code numbers — read from pricing-building-blocks.md loader.
- Do NOT build full billing reconciliation — separate plan.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Endpoint contract (path + params + response shape).
- Unit test count + pass rate.
- Scope-enforcement smoke results.
- Playwright spec pass status.
- QG results (strategy-service + UI).
- 3 commit SHAs pushed to live-defi-rollout.
