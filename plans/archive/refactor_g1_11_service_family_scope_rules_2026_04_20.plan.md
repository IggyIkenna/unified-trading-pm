---
doc_type: plan
title: Refactor G1.11 — Service-family scope rules
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  [
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.11,
    /codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-playbooks/shared-core/same-system-principle.md,
    /codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md,
    refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.11 — Service-family scope rules

> ## Implementation note (post-ship — Option X pattern)
>
> Plan body says scope rules live in `strategy-service/strategy_service/availability/service_family_scope.py`. **Actual
> ship hosts pure logic in UAC; the access_control() pre-check is wired in UAC alongside the rules** (Option X).
>
> Authoritative paths (verified 2026-04-22):
>
> - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/service_family_scope.py` — scope rules
>   - access_control pre-check, all in UAC
>
> Plan body's `strategy-service/strategy_service/availability/service_family_scope.py` reference is kept for historical
> context; trust this note over body prose.

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
| SMA-vs-Pooled applies to IM + Reg, not DART     | DART clients bring their own capital infra; SMA vs Pooled is an IM / Reg structural decision                                                                   | `plans/active/share_class_architecture_2026_04_01.md`            |

## Cross-references

- **Upstream (Wave C):** `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md` — hard
  dep
- **Sibling Wave D:** `refactor_g1_7_restriction_profile_engine_2026_04_20.md` — parallel; both layer on top of G1.6
- **Downstream:** `refactor_g1_4` (persona matrix respects scope rules), `refactor_g1_14` (deck slide)
- **Rules:** `_ssot-rules/04-dart-commercial-axes.md`, `_ssot-rules/03-same-system-principle.md`
- **Shared-core:** `shared-core/same-system-principle.md`, `shared-core/client-reporting-demo-walkthrough.md`,
  `shared-core/org-fund-client-entity-model.md`, `shared-core/shared-reporting-core.md`
- **Cross-cutting:** `cross-cutting/sma-vs-pooled.md`
- **Strategy v2 TIER_ZERO:** `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
- **Strategy v2 archetype declarations (read-only):** `strategy-service/strategy_service/engine/strategies/v2/` —
  informs which archetypes surface to which service families
- **v2 cross-cutting:** `codex/09-strategy/architecture-v2/cross-cutting/`
- **Sibling plan:** `plans/active/share_class_architecture_2026_04_01.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.11
2. `/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md` (full)
3. `/codex/14-playbooks/_ssot-rules/03-same-system-principle.md`
4. `/codex/14-playbooks/shared-core/same-system-principle.md`
5. `/codex/14-playbooks/shared-core/client-reporting-demo-walkthrough.md`
6. `/codex/14-playbooks/shared-core/org-fund-client-entity-model.md`
7. `/codex/14-playbooks/shared-core/shared-reporting-core.md`
8. `/codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md`
9. `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md` (full)
10. `codex/09-strategy/architecture-v2/cross-cutting/` (all files)
11. `strategy-service/strategy_service/engine/strategies/v2/` (read-only — archetype-by-archetype check of which
    families the archetype surfaces to)
12. `strategy-service/strategy_service/availability/derivation.py` (landed by G1.6)
13. `plans/active/share_class_architecture_2026_04_01.md`

## Out of scope

- Shipping restriction profiles — G1.7 owns persona-level overlay.
- Shipping the DART rebrand marketing copy — future G2 / roadmap item.
- Shipping SMA vs Pooled account-level flow — `share_class_architecture` plan owns that.
- Re-architecting IM / Reg services — scope rules are guardrails, not re-org.
- Touching strategy-service v2 code — read-only.
- Reading `_archived_pre_v2/` — strictly forbidden.

## Dev / staging parity rule

Scope rules behave identically in dev and staging:

- **Dev (`localhost:3000`):** mock auth seeds a persona tagged with a service family; `access_control` enforces the same
  rule table as staging.
- **Staging (`odum-research.co.uk`):** Firebase staging users carry service-family claims; `access_control` enforces the
  same rule table.
- **Prod:** Firebase prod users; same rule table; same enforcement.

Identical rule YAML + identical `check_service_family_scope` function. Any divergence is a rule-03 violation.

## Phase breakdown

### Wave D execution summary (2026-04-20)

All Phase 11A-11E shipped in 3 commits. Option X carry-through (UAC host). Rule number shifted from 11 → 12 because slot
11 was already taken by `11-codex-scope-registry.md` (G1.9, shipped 2026-04-20).

| Repo                      | SHA        | Summary                                                                              |
| ------------------------- | ---------- | ------------------------------------------------------------------------------------ |
| unified-trading-pm        | `a1741e0a` | rule 12 YAML + MD + `_tools/validate_scope_yaml.py` + rule 04 cross-ref + SSOT-INDEX |
| unified-api-contracts     | `073e6c1`  | `service_family_scope.py` + `access_control()` pre-check + 20+ tests                 |
| unified-trading-system-ui | `78736f1`  | Playwright spec (file presence + route-gating + persona skips for G1.10)             |

**Checkbox-mapping note:** each `- [ ] ... 11-service-family-scope-rules.*` item below executed against the
**12-prefixed** files — rule number rename is the only delta from the pre-execution plan prose.

### Phase 11A — Audit + draft rule YAML

- [x] [AGENT] P0. Enumerate every `/services/<family>/*` route in the UI. Classify each by required service-family
      membership.
- [x] [AGENT] P0. Write `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.yaml`:

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

- [x] [AGENT] P0. Write `/codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.md` — prose rule doc explaining
      each row with rationale + cross-refs to shared-core + TIER_ZERO docs.

### Phase 11B — Implement `check_service_family_scope`

- [x] [AGENT] P0. Add `strategy-service/strategy_service/availability/service_family_scope.py`:

  ```python
  def check_service_family_scope(user: UserContext, route: str) -> ScopeDecision: ...
  # returns ALLOW | DENY(reason: str)
  ```

- [x] [AGENT] P0. Loader reads the YAML at module import; fails loud on malformed.
- [x] [AGENT] P0. Wire into G1.6's `access_control()` — pre-check before the generic gate. If scope denies,
      short-circuit return DENY without further evaluation.

### Phase 11C — Update rule 04 + SSOT index cross-refs

- [x] [AGENT] P0. Update `_ssot-rules/04-dart-commercial-axes.md` to cross-ref rule 11 under a "Service-family scope —
      see rule 11" section. Do NOT duplicate the rule table.
- [x] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` to register rule 11.

### Phase 11D — Unit tests + rule 11 YAML validator

- [x] [AGENT] P0. `strategy-service/tests/availability/test_service_family_scope.py` — ≥ 30 cases covering every
      (service-family × route-category) combination from the YAML.
- [x] [AGENT] P0. Validator tool at `codex/14-playbooks/_ssot-rules/_tools/validate_scope_yaml.py` — asserts YAML
      schema + unknown family/route rejection.

### Phase 11E — Verify + QG

- [x] [SCRIPT] P0. strategy-service QG green.
- [x] [SCRIPT] P0. PM QG green.
- [x] [AGENT] P0. Playwright spec `refactor-g1-11-service-family-scope.spec.ts` green on tier-1 dev.

## Critical files to be modified

- `/codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.md` — NEW
- `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.yaml` — NEW
- `codex/14-playbooks/_ssot-rules/_tools/validate_scope_yaml.py` — NEW
- `codex/00-SSOT-INDEX.md` — MODIFY
- `/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md` — MODIFY (cross-ref)
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
- **G1.14 deck slide** — rule 12 is a slide topic.
- **G2.x** — future client onboarding flows respect scope rules by default.

## Follow-ups / spillover (carried past Wave D)

- **Allocator-gate orphan (from G1.6 Phase 6D).** `portfolio_allocator/service.py:125` in strategy-service still calls
  the legacy `validate_allocation_authorised()`. G1.7 reconciliation flagged this as carried-forward; G1.11 did NOT pick
  it up either (scope was confined to UAC service-family pre-check, which lands BEFORE the allocator is ever invoked —
  different layer). **Deferred to Wave E** as an independent cleanup commit: the swap needs a new `access_control`-
  backed gate in strategy-service + test updates + strategy-service QG. Tracked in G1.6 plan as `[DEFERRED → G1.7]` on
  line 140; the "→ G1.7" tag is now stale (G1.7 did not pick it up); Wave E (G1.10 questionnaire) agent should pick up
  the swap since they'll already be modifying `portfolio_allocator/` surfaces for questionnaire-driven client setup.
- **Audit review 2026-04-20:** verified all 13 Phase-11A-through-11E checkboxes flipped; rule 11 prose inside this plan
  refers to rule-12 files on disk (Checkbox-mapping note at line 114 of this plan covers the rename). No further paper
  fix required.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
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
`plans/active/refactor_g1_11_service_family_scope_rules_2026_04_20.md`

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

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
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

---

## Micro-execution plan (sub-agent Phase 1, appended 2026-04-20)

> Drafted by Wave-D kickoff sub-agent. Plan-mode only — no code edits yet; operator approval required before Phase 11A.
> Companion micro-plan for G1.7 in `refactor_g1_7_restriction_profile_engine_2026_04_20.md` § Micro-execution plan.

### Plan-vs-reality drifts (verified 2026-04-20 against `live-defi-rollout` post-Wave-C)

| #   | Plan claims                                                                                                                                                                                                                                                    | Reality                                                                                                                                                                                                                                          | Resolution                                                                                                                                                                                                                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Entire plan assumes **"rule 11"** is the new slot for service-family scope (file paths `_ssot-rules/11-service-family-scope-rules.{md,yaml}`, rule_id `11` inside YAML, etc.)                                                                                  | **Rule 11 slot is already taken** by `11-codex-scope-registry.md` (shipped with G1.9 on 2026-04-20). `ls _ssot-rules/` shows rules 01–11 all populated.                                                                                          | **Renumber to rule 12.** All file paths, the YAML `rule_id` key, rule-04 cross-ref text, and SSOT-INDEX registration move to `12-*`. Plan's Phase 11A-11E labels preserved (they're plan-phase identifiers, not rule numbers). Operator sign-off requested.                             |
| 2   | Line 140 signature: `def check_service_family_scope(user: UserContext, route: str) -> ScopeDecision: ...` and Line 175: "MODIFY `derivation.py` (wire pre-check in `access_control`)" points at `strategy-service/strategy_service/availability/derivation.py` | Post-Wave-C, `derivation.py` lives in **UAC** (Option X). Plan's host assumption is stale. `UserContext` + `access_control` are UAC symbols now.                                                                                                 | **Option X carry-through.** Ship `service_family_scope.py` in UAC at `unified-api-contracts/unified_api_contracts/internal/architecture_v2/service_family_scope.py`. Wire pre-check inside UAC `derivation.py` `access_control()`. Tests colocated in UAC. Operator sign-off requested. |
| 3   | Lines 124, 173: both G1.7 **and** G1.11 modify `derivation.py` (G1.7 touches `demo_universe()` + `prod_restrictions()`; G1.11 touches `access_control()`)                                                                                                      | Same file, different functions → concurrent agent commits would merge-conflict on import block + `__init__.py` exports.                                                                                                                          | **Sequence, not parallelise.** Land G1.7's UAC commit first; G1.11 rebases on top and adds `access_control()` pre-check + new import. Plans are tagged parallel in frontmatter — relax that for Wave-D execution.                                                                       |
| 4   | Line 125 YAML example `strategy-catalogue-admin` included in `admin.surfaces` list                                                                                                                                                                             | Plan defines a closed enum of service families `{IM, RegUmbrella, DART, DART-reporting-only, admin, IM-desk}`. The enum semantics are clear but `strategy-catalogue-admin` is a **route category**, not a service-family surface. Confuses axes. | Clarify in the YAML `surfaces` entries — use `surfaces: [...]` for surface-category names and a separate `route_allowlist: [pattern, ...]` (glob) for route-level allow. Align with the UI route layout.                                                                                |
| 5   | Line 137 puts `service_family_scope.py` in strategy-service; Line 139 signature uses `UserContext` (a UAC type after G1.6). A strategy-service module importing a UAC type and being called BY a UAC function creates a dep loop.                              | Same root cause as drift #2 (plan is pre-Wave-C).                                                                                                                                                                                                | Resolved by drift #2 resolution (Option X host).                                                                                                                                                                                                                                        |
| 6   | Plan's persona list (line 196 onwards): `admin`, `client-full`, `prospect-im`, `prospect-dart`, `prospect-regulatory`, `anon`                                                                                                                                  | Existing `lib/auth/personas.ts` doesn't have `prospect-dart` or `prospect-regulatory` — they ship with G1.10 questionnaire flow. G1.6 memory/MEMORY.md noted this.                                                                               | Playwright spec for G1.11 skips `prospect-dart` + `prospect-regulatory` with `TODO(G1.10)` marker; assert scope logic against the 4 existing personas via fixture-seeded UserContext instead of browser-real personas. Decouples this plan from G1.10 gate.                             |

### Pre-audit manifest (Citadel rule-6)

| Symbol                                       | Current hits                     | Action                                                                                                                                                                                                                                              |
| -------------------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `check_service_family_scope`                 | 0                                | Net-new.                                                                                                                                                                                                                                            |
| `ScopeDecision`                              | 0                                | Net-new — `Literal["allow"] \| ScopeDeny` discriminated pair, mirrors `AccessDecision`.                                                                                                                                                             |
| `ServiceFamily`                              | Several unrelated hits in UI     | New UAC enum `ServiceFamily = Literal["IM", "RegUmbrella", "DART", "DART_reporting_only", "admin", "IM_desk"]` (snake_case for `DART_reporting_only` + `IM_desk` to avoid hyphen issues in Python). Distinct from UI references — different domain. |
| `access_control`                             | UAC derivation.py (G1.6 shipped) | MODIFY: add `check_service_family_scope(user, route)` pre-check at the top of the function body. If scope denies → short-circuit return `AccessDecision(status="deny", reason=scope_decision.reason, upgrade_hint=scope_decision.upgrade_hint)`.    |
| `UserContext`                                | UAC derivation.py                | EXTEND: `UserContext` may already have `audience: ClientAudience`; `ClientAudience` enum maps 1:1 with `ServiceFamily` for the scope-check purpose. Add a `service_family` property or derive from audience. Flag design decision.                  |
| `11-service-family-scope-rules.md` / `.yaml` | 0                                | Cannot use rule-11 slot (taken). Use **rule 12**: `12-service-family-scope-rules.md` + `.yaml`.                                                                                                                                                     |

### Execution DAG

```
11A audit + draft rule 12 YAML + draft rule 12 md + validator tool in _tools/
    └── COMMIT 1 (PM — rule 12 doc + yaml + validator)
        └── 11B service_family_scope.py in UAC
            └── 11C wire access_control pre-check in derivation.py (SEQUENCED AFTER G1.7's derivation.py edits land)
                └── COMMIT 2 (UAC — depends on G1.7 UAC commit being on origin first)
                    └── 11D PM cross-refs + SSOT-INDEX update → folded into COMMIT 1 OR NEW COMMIT 3 (PM)
                        └── 11E UI Playwright spec + COMMIT 4 (UI)
```

### Files × line-ranges × commit sequence

**COMMIT 1 — PM** `docs(ssot-rules): G1.11 — rule 12 service-family scope (yaml + md + validator + cross-refs)`

| File                                                                                   | Action                                                                                     | Approx LOC |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------- |
| `unified-trading-pm/codex/14-playbooks/_ssot-rules/12-service-family-scope-rules.md`   | NEW — prose rule doc explaining each service-family row with rationale + cross-refs        | ~200       |
| `unified-trading-pm/codex/14-playbooks/_ssot-rules/12-service-family-scope-rules.yaml` | NEW — machine-readable rule table with 6 families × surfaces/excludes/route_allowlist      | ~80        |
| `unified-trading-pm/codex/14-playbooks/_ssot-rules/_tools/validate_scope_yaml.py`      | NEW — schema validator (new `_tools/` dir under \_ssot-rules)                              | ~120       |
| `unified-trading-pm/codex/00-SSOT-INDEX.md`                                            | MODIFY — register rule 12                                                                  | +3         |
| `unified-trading-pm/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md`         | MODIFY — add "Service-family scope — see rule 12" cross-ref section (no table duplication) | +8         |

**COMMIT 2 — UAC** `feat(uac): G1.11 — service-family scope enforcement wired into access_control()`

| File                                                                                           | Action                                                                                                                            | Approx LOC |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `unified-api-contracts/unified_api_contracts/internal/architecture_v2/service_family_scope.py` | NEW — `ServiceFamily` enum, `ScopeDecision` type, `check_service_family_scope()`, YAML loader                                     | ~220       |
| `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py`           | MODIFY — add scope pre-check at top of `access_control()` body                                                                    | +18        |
| `unified-api-contracts/unified_api_contracts/internal/architecture_v2/__init__.py`             | MODIFY — export new symbols                                                                                                       | +4         |
| `unified-api-contracts/unified_api_contracts/strategy.py`                                      | MODIFY — re-export `check_service_family_scope`, `ScopeDecision`, `ServiceFamily`                                                 | +6         |
| `unified-api-contracts/tests/internal/unit/test_service_family_scope.py`                       | NEW — ≥ 30 cases: every (service-family × route-category) combination + malformed-YAML rejection + default-deny for unknown route | ~400       |
| `unified-api-contracts/tests/internal/unit/test_derivation.py`                                 | MODIFY — add integration test: out-of-scope user → `access_control` returns deny via scope path                                   | +20        |

**COMMIT 3 — UI** `test(playbooks): G1.11 — service-family scope Playwright spec`

| File                                                                                                 | Action                                                                                                                                                                                                                                                                                                 | Approx LOC |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts` | NEW — seed 4 available personas (`admin`, `client-full`, `prospect-im`, `anon`) + fixture UserContext objects for the 6 ServiceFamily values; assert allow/deny per route matches rule 12 YAML; orphan-reachability for in-scope routes. Prospect-dart + prospect-regulatory skipped with TODO(G1.10). | ~220       |

No UI `scripts/quality-gates.sh` edit needed — Playwright auto-discovers.

### YAML schema proposal (operator-review)

```yaml
rule_id: 12
rule_name: service-family-scope-rules
service_families:
  IM:
    surfaces: [reporting, client_portal]
    excludes: [observe, research, promote, strategy_catalogue_admin]
    route_allowlist:
      - /services/investment-management/**
      - /services/reports/**
  RegUmbrella:
    surfaces: [reporting, compliance_overlay]
    excludes: [observe, research, promote, strategy_catalogue_admin]
    route_allowlist:
      - /services/regulatory-umbrella/**
      - /services/reports/**
  DART:
    surfaces: [reporting, observe, research, promote]
    excludes: [strategy_catalogue_admin]
    route_allowlist:
      - /services/**
      - "!/admin/**"
  DART_reporting_only:
    surfaces: [reporting]
    excludes: [observe, research, promote, strategy_catalogue_admin]
    route_allowlist:
      - /services/reports/**
  admin:
    surfaces: [everything, strategy_catalogue_admin]
    excludes: []
    route_allowlist: ["/**"]
  IM_desk:
    surfaces: [strategy_catalogue_admin, reporting]
    excludes: []
    route_allowlist:
      - /services/strategy-catalogue/admin/**
      - /services/reports/**
```

Glob matcher chosen for readability; Python `fnmatch` with `**` handling (or `pathspec`). Negation via `!` prefix.

### Breaking-change analysis (Citadel rule-3)

- `access_control()` gains a pre-check. Existing Wave-C tests that pass admin/im_desk personas still return `allow`
  because scope allows those; tests for other audiences may newly deny if the fixture persona's audience isn't in the
  enum. **Pre-audit existing derivation tests:** rerun after pre-check wiring, adjust any fixture that assumed
  scope-blind access.
- New enum `ServiceFamily`: additive. Rule 12 prose and YAML close the set at 6 members.
- `UserContext.audience` today accepts `Literal["trading_platform_subscriber", "im_desk", "im_client", "admin"]` per
  G1.6 shipped code. Need mapping `audience → service_family`. Add helper
  `service_family_from_audience(audience) -> ServiceFamily | None`.

### Success criteria

| Phase               | Gate                                                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11A rule doc + YAML | `validate_scope_yaml.py` exit 0; SSOT-INDEX shows rule 12; rule 04 cross-ref rendered                                                                               |
| 11B + 11C           | `from unified_api_contracts.strategy import check_service_family_scope, ServiceFamily` clean; integration test in UAC shows `access_control` denying via scope path |
| 11D tests           | ≥ 30 unit cases green (every family × route combo)                                                                                                                  |
| 11E Playwright      | spec green on tier-1 dev; scope-deny route shows G1.3 LOCKED-VISIBLE padlock                                                                                        |
| final               | 3 commit SHAs on `origin/live-defi-rollout`; `contracts.py` 908-LOC WIP still sidesteppable via explicit staging                                                    |

### Open questions for operator

1. **Rule number** (drift #1): ship as **rule 12** (not 11 — slot taken). Operator confirm?
2. **Option X carry-through** (drift #2,5): `service_family_scope.py` in UAC, not strategy-service. Operator confirm?
3. **Sequencing G1.7 → G1.11** (drift #3): G1.7 lands first, G1.11 rebases onto UAC `derivation.py`. Or inverted.
   Operator confirm order?
4. **YAML schema — `surfaces` vs `route_allowlist` split** (drift #4): both fields per family, surfaces is the
   audience-semantic vocabulary, route_allowlist is the glob that `check_service_family_scope` actually matches on.
   Operator confirm?
5. **Persona skips** (drift #6): Playwright spec skips `prospect-dart` + `prospect-regulatory` until G1.10 ships those
   personas; fixture-seeded UserContext drives 6×N matrix instead. Operator confirm?

### Pre-flight for Phase 11A execution (when approved)

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
ls unified-trading-pm/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md  # expect exists — confirms rule-11 slot taken
.venv-workspace/bin/python -c "from unified_api_contracts.strategy import check_service_family_scope" 2>&1 | head  # expect ImportError (not yet shipped)
# After G1.7 UAC commit lands:
git -C unified-api-contracts log --oneline origin/live-defi-rollout | grep "G1.7" | head
```
