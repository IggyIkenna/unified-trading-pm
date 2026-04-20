---
title: Refactor G1.11 — Service-family scope rules
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.11
  - codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md
  - codex/14-playbooks/shared-core/same-system-principle.md
  - codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md
  - refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md
# Wave D — parallel with refactor_g1_7. Downstream (Wave F): refactor_g1_4.
# Also informs refactor_g1_14 (deck slide).
---

# Refactor G1.11 — Service-family scope rules

## Context

Stage 3E §1.11 (2026-04-20 amendment): codify hard service-family scope constraints as machine-readable rules, enforced
inside G1.6's `access_control` formula. The constraints flow from commercial + architectural reality:

- `observe ∈ {DART}` only — IM + Reg Umbrella clients don't own observability; Odum (for IM) or the client (for Reg)
  manages deployment/logging outside Odum's infra.
- `reporting ∈ {IM, DART-reporting-only, Reg Umbrella}` — the three service-family paths that surface client reporting.
- `research, promote ∈ {full-DART only}` — IM runs predetermined strategies; Reg Umbrella is compliance overlay;
  research surfaces live only for full-DART subscribers.
- `strategy-catalogue-admin ∈ {admin, IM-desk}` only — locking strategies in/out of demo visibility is an Odum-internal
  operation.

Today these constraints are scattered across UI route-gating, demo-ops docs, and implicit audience assumptions. G1.11
lifts them into an explicit rule file + enforcement in `access_control`.

## Decisions locked with user (2026-04-20)

| Decision                                        | Chosen                                                                                                                                                         | Source                                                           |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Codify as new rule 11 (OR extend rule 04)       | Recommend **new rule 11** — scope rules are a distinct axis from the DART commercial axes (rule 04). Rule file: `_ssot-rules/11-service-family-scope-rules.md` | Kickoff §1.11 — "codify as rule 11 (or extend rule 04)"          |
| Enforcement lives in `access_control()` formula | G1.6's `access_control(user, route, item, phase)` calls `check_service_family_scope(user, route)` as a pre-check before the generic gate                       | Kickoff §1.11 + G1.6 handoff                                     |
| Declarative rule table                          | YAML at `_ssot-rules/11-service-family-scope-rules.yaml` — machine-readable. Rule 11 .md doc explains + cross-refs                                             | Kickoff §1.11                                                    |
| Service families covered                        | `IM`, `Reg Umbrella`, `DART` (+ `DART-reporting-only` sub-family for shared reporting tool)                                                                    | Kickoff §1.11 + shared-core/client-reporting-demo-walkthrough.md |
| SMA-vs-Pooled applies to IM + Reg, not DART     | DART clients bring their own capital infra; SMA vs Pooled is an IM / Reg structural decision                                                                   | `plans/active/share_class_architecture_2026_04_01.plan.md`       |

## Cross-references

- **Upstream (Wave C):** `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md` —
  hard dep
- **Sibling Wave D:** `refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md` — parallel; both layer on top of
  G1.6
- **Downstream:** `refactor_g1_4` (persona matrix respects scope rules), `refactor_g1_14` (deck slide)
- **Rules:** `_ssot-rules/04-dart-commercial-axes.md`, `_ssot-rules/03-same-system-principle.md`
- **Shared-core:** `shared-core/same-system-principle.md`, `shared-core/client-reporting-demo-walkthrough.md`,
  `shared-core/org-fund-client-entity-model.md`, `shared-core/shared-reporting-core.md`
- **Cross-cutting:** `cross-cutting/sma-vs-pooled.md`
- **Strategy v2 TIER_ZERO:** `codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
- **Strategy v2 archetype declarations (read-only):** `strategy-service/strategy_service/engine/strategies/v2/` —
  informs which archetypes surface to which service families
- **v2 cross-cutting:** `codex/09-strategy/architecture-v2/cross-cutting/`
- **Sibling plan:** `plans/active/share_class_architecture_2026_04_01.plan.md`

## Mandatory read-set

1. `codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.11
2. `codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md` (full)
3. `codex/14-playbooks/_ssot-rules/03-same-system-principle.md`
4. `codex/14-playbooks/shared-core/same-system-principle.md`
5. `codex/14-playbooks/shared-core/client-reporting-demo-walkthrough.md`
6. `codex/14-playbooks/shared-core/org-fund-client-entity-model.md`
7. `codex/14-playbooks/shared-core/shared-reporting-core.md`
8. `codex/14-playbooks/cross-cutting/sma-vs-pooled.md`
9. `codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md` (full)
10. `codex/09-strategy/architecture-v2/cross-cutting/` (all files)
11. `strategy-service/strategy_service/engine/strategies/v2/` (read-only — archetype-by-archetype check of which
    families the archetype surfaces to)
12. `strategy-service/strategy_service/availability/derivation.py` (landed by G1.6)
13. `plans/active/share_class_architecture_2026_04_01.plan.md`

## Out of scope

- Shipping restriction profiles — G1.7 owns persona-level overlay.
- Shipping the DART rebrand marketing copy — future G2 / roadmap item.
- Shipping SMA vs Pooled account-level flow — `share_class_architecture` plan owns that.
- Re-architecting IM / Reg services — scope rules are guardrails, not re-org.
- Touching strategy-service v2 code — read-only.
- Reading `_archived_pre_v2/` — strictly forbidden.

## Dev / staging parity rule

Scope rules behave identically in dev and staging:

- **Dev (`localhost:3010`):** mock auth seeds a persona tagged with a service family; `access_control` enforces the same
  rule table as staging.
- **Staging (`odum-research.co.uk`):** Firebase staging users carry service-family claims; `access_control` enforces the
  same rule table.
- **Prod:** Firebase prod users; same rule table; same enforcement.

Identical rule YAML + identical `check_service_family_scope` function. Any divergence is a rule-03 violation.

## Phase breakdown

### Phase 11A — Audit + draft rule YAML

- [ ] [AGENT] P0. Enumerate every `/services/<family>/*` route in the UI. Classify each by required service-family
      membership.
- [ ] [AGENT] P0. Write `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.yaml`:

  ```yaml
  rule_id: 11
  service_families:
    IM:
      surfaces: [reporting, client-portal]
      excludes: [observe, research, promote, strategy-catalogue-admin]
    RegUmbrella:
      surfaces: [reporting, compliance-overlay]
      excludes: [observe, research, promote, strategy-catalogue-admin]
    DART:
      surfaces: [reporting, observe, research, promote]
      excludes: [strategy-catalogue-admin]
    DART-reporting-only:
      surfaces: [reporting]
      excludes: [observe, research, promote, strategy-catalogue-admin]
    admin:
      surfaces: [everything, strategy-catalogue-admin]
      excludes: []
    IM-desk:
      surfaces: [strategy-catalogue-admin] # IM-desk OPERATORS can lock/unlock demo slots
      excludes: []
  ```

- [ ] [AGENT] P0. Write `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.md` — prose rule doc explaining
      each row with rationale + cross-refs to shared-core + TIER_ZERO docs.

### Phase 11B — Implement `check_service_family_scope`

- [ ] [AGENT] P0. Add `strategy-service/strategy_service/availability/service_family_scope.py`:

  ```python
  def check_service_family_scope(user: UserContext, route: str) -> ScopeDecision: ...
  # returns ALLOW | DENY(reason: str)
  ```

- [ ] [AGENT] P0. Loader reads the YAML at module import; fails loud on malformed.
- [ ] [AGENT] P0. Wire into G1.6's `access_control()` — pre-check before the generic gate. If scope denies,
      short-circuit return DENY without further evaluation.

### Phase 11C — Update rule 04 + SSOT index cross-refs

- [ ] [AGENT] P0. Update `_ssot-rules/04-dart-commercial-axes.md` to cross-ref rule 11 under a "Service-family scope —
      see rule 11" section. Do NOT duplicate the rule table.
- [ ] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` to register rule 11.

### Phase 11D — Unit tests + rule 11 YAML validator

- [ ] [AGENT] P0. `strategy-service/tests/availability/test_service_family_scope.py` — ≥ 30 cases covering every
      (service-family × route-category) combination from the YAML.
- [ ] [AGENT] P0. Validator tool at `codex/14-playbooks/_ssot-rules/_tools/validate_scope_yaml.py` — asserts YAML
      schema + unknown family/route rejection.

### Phase 11E — Verify + QG

- [ ] [SCRIPT] P0. strategy-service QG green.
- [ ] [SCRIPT] P0. PM QG green.
- [ ] [AGENT] P0. Playwright spec `refactor-g1-11-service-family-scope.spec.ts` green on tier-1 dev.

## Critical files to be modified

- `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.md` — NEW
- `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.yaml` — NEW
- `codex/14-playbooks/_ssot-rules/_tools/validate_scope_yaml.py` — NEW
- `codex/00-SSOT-INDEX.md` — MODIFY
- `codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md` — MODIFY (cross-ref)
- `strategy-service/strategy_service/availability/service_family_scope.py` — NEW
- `strategy-service/strategy_service/availability/derivation.py` — MODIFY (wire pre-check in `access_control`)
- `strategy-service/tests/availability/test_service_family_scope.py` — NEW (≥ 30 cases)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts` — NEW

## Execution DAG

```
11A (YAML + doc)  →  11B (impl + wire access_control) + 11D (validator + tests)  [parallel after 11A]  →  11C (cross-refs)  →  11E (QG + Playwright)
```

## Verification

1. Rule 11 YAML parses + `validate_scope_yaml.py` exit 0.
2. `check_service_family_scope(im_user, "/services/research/...")` returns DENY with cited rule.
3. `access_control()` short-circuits on scope denial — verified by unit test + integration.
4. SSOT-INDEX + rule 04 cross-ref landed.
5. strategy-service + PM QG green.
6. Playwright spec: IM persona hitting research route sees deny UX; DART persona hitting research route passes.

## Handoff

Unblocks:

- **G1.4 persona matrix** — personas carry service-family tags; scope rules enforce their visibility.
- **G1.10 questionnaire** — questionnaire's service-family picker maps directly to the YAML families.
- **G1.14 deck slide** — rule 11 is a slide topic.
- **G2.x** — future client onboarding flows respect scope rules by default.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — seed personas representing each service family (IM, Reg Umbrella, DART,
DART-reporting-only, admin, IM-desk), attempt to navigate scoped routes, verify deny UX (e.g. padlock + "contact sales"
tooltip) appears for out-of-scope navigation. Iterate until every (family × route) cell matches YAML.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts` — must:

1. Seed personas via `tests/e2e/playbooks/seed-persona.ts` representing each service family (6 total).
2. For each persona, attempt to navigate to `/services/research/*`, `/services/observe/*`, `/services/reporting/*`,
   `/services/strategy-catalogue/admin`. Verify allow/deny matches rule 11 YAML.
3. Assert the deny UX matches G1.3 LOCKED-VISIBLE pattern — padlock icon + tooltip.
4. Assert `access_control()` (from G1.6) produces the same decisions — cross-check via exposed debug endpoint or
   computed client-side.
5. Assert dev-vs-staging parity: same persona → same allow/deny decisions in both environments.
6. Include orphan-reachability assertion — every in-scope route is reachable from main nav for that family.
7. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.11 (Wave D, parallel with G1.7;
both depend on G1.6).**

---

You are executing **Refactor G1.11 — Service-family scope rules** for the Unified Trading System at Odum Research. Wave
D; G1.6 must be merged first; parallelisable with G1.7.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
ls unified-trading-pm/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md
ls unified-trading-pm/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md
# Verify G1.6 merged
ls strategy-service/strategy_service/availability/derivation.py
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 11A through 11E of this plan:
`plans/active/refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 13. Cite `strategy-service/strategy_service/engine/strategies/v2/` for
archetype-per-family verification (NEVER `_archived_pre_v2/`).

### Deliverables

- New: `_ssot-rules/11-service-family-scope-rules.{md,yaml}`, `_tools/validate_scope_yaml.py`
- New: `strategy-service/strategy_service/availability/service_family_scope.py` + test (≥ 30 cases)
- Modified: `strategy-service/strategy_service/availability/derivation.py` (wire pre-check), `codex/00-SSOT-INDEX.md`,
  `_ssot-rules/04-dart-commercial-axes.md` (cross-ref)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts`

### Dev / staging parity requirement (verbatim — REQUIRED)

Scope rules behave identically in dev and staging. Identical YAML + identical `check_service_family_scope` enforcement.
Only the user-identity source differs (localStorage seed vs Firebase). Any divergence = rule-03 violation.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to verify every (service-family × route) cell renders allow or deny matching the rule 11
YAML. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts` — seed 6 personas
via `tests/e2e/playbooks/seed-persona.ts`, walk family-specific routes, assert allow/deny matches YAML, assert deny UX
is G1.3 LOCKED-VISIBLE padlock, assert `access_control` agrees, assert dev-vs-staging parity, include
orphan-reachability assertion, wire into `scripts/quality-gates.sh`.

### Commit strategy

Three repos touched → three quickmerge commits.

```
cd unified-trading-pm
bash scripts/quickmerge.sh "docs(ssot-rules): G1.11 — rule 11 service-family scope (yaml + md + cross-ref rule 04)" --agent

cd ../strategy-service
bash scripts/quickmerge.sh "feat(strategy-service/availability): G1.11 — service-family scope enforcement in access_control" --agent

cd ../unified-trading-system-ui
bash scripts/quickmerge.sh "test(playbooks): G1.11 — service-family scope Playwright spec" --agent --files "tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts"
```

Fallback per repo: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never
`--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ Rule 11 YAML parses + validator exit 0.
2. ✅ ≥ 30 scope test cases green.
3. ✅ `access_control()` short-circuits on scope denial — integration test green.
4. ✅ Rule 04 cross-refs rule 11; SSOT-INDEX registers rule 11.
5. ✅ strategy-service + PM + UI QG green.
6. ✅ Playwright spec green on tier-1 dev.
7. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT duplicate the rule 11 table inside rule 04 — cross-ref only.
- Do NOT modify strategy-service v2 archetype code — read-only.
- Do NOT introduce a new service family without explicit user approval —
  `{IM, RegUmbrella, DART, DART-reporting-only, admin, IM-desk}` is closed.
- Do NOT bypass G1.6's `access_control` — layer on top, not around.
- Do NOT diverge dev from staging.

### Report back

- Rule 11 YAML (paste full file in report).
- Service-family × route matrix — 6 × N table.
- Test count per service family.
- QG results (3 repos).
- Playwright spec pass status.
- 3 commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
