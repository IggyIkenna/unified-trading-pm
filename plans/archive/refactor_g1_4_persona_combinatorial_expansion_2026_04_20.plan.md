---
doc_type: plan
title: Refactor G1.4 — Persona combinatorial expansion (11 → 15-20)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, unified-trading-pm, unified-trading-system-ui]
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
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §1.4,
    refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md,
    refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md,
    refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md,
    plans/active/five_space_ia_execution_child_plan_2026_04_17.md (ticket,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.4 — Persona combinatorial expansion (11 → 15-20)

## Context

Stage 3E §1.4 (2026-04-20 amendment): extend `unified-trading-system-ui/lib/auth/personas.ts` from today's 11 personas
to N ≈ 15–20, parameterised across the G1.10 questionnaire dimensions (service-family × venue scope × instrument types ×
fund structure × strategy style × maturity × seniority). Each persona has a realistic email, entitlement set, and
deterministic restriction-profile mapping via G1.7 / G1.11. The expanded matrix drives both dev-mode mock-auth (for
sales demos, dev iteration, screenshot generation) and staging (same personas provisioned as real Firebase users via
user-management-ui).

## Decisions locked with user (2026-04-20)

| Decision                                             | Chosen                                                                                                    | Source                                             |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Target count                                         | 15-20 personas spanning the questionnaire axis combinations                                               | Kickoff §1.4                                       |
| Each persona has a realistic email + entitlement set | e.g. `sarah.quant@examplehedge.com` (CeFi ML-directional IM prospect)                                     | Kickoff §1.4                                       |
| Deterministic mapping to RestrictionProfile via G1.7 | Persona row includes `questionnaire: QuestionnaireResponse` + `service_family` + `lock_state`             | Kickoff §1.4                                       |
| Dev-staging parity                                   | Identical set in both environments; staging provisions them as real Firebase users via user-management-ui | Dev-staging parity rule + five_space_ia ticket #12 |
| Screenshot regen for new personas                    | Playwright screenshots spec re-runs on the new persona set; outputs feed G1.14 HTML stretch               | Kickoff §1.14                                      |

## Cross-references

- **Upstream (Wave D):** `refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md`,
  `refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md`
- **Upstream (Wave E):** `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md` — questionnaire axes
  are the persona expansion axes
- **Sibling Wave F:** `refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.plan.md`
- **Downstream:** `refactor_g1_14_presentation_deck_refresh_2026_04_20.plan.md` HTML stretch (consumes new screenshots)
- **Sibling plan:** `plans/active/five_space_ia_execution_child_plan_2026_04_17.md` (ticket #12 staging Firebase)
- **Sibling plan:** `plans/active/user_management_merge_2026_03_23.plan.md` (real user provisioning path)
- **Rule:** `_ssot-rules/11-service-family-scope-rules.yaml` (landed by G1.11) — personas respect scope

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.4
2. `unified-trading-system-ui/lib/auth/personas.ts` (11 existing personas)
3. `unified-trading-system-ui/lib/auth/demo-provider.ts`
4. `unified-trading-system-ui/lib/config/auth.ts`
5. `plans/active/user_management_merge_2026_03_23.plan.md`
6. `plans/active/five_space_ia_execution_child_plan_2026_04_17.md` (ticket #12)
7. `codex/14-playbooks/demo-ops/profiles/` (YAMLs landed by G1.7)
8. `strategy-service/strategy_service/availability/restriction_profiles.py`
9. `codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.yaml` (landed by G1.11)
10. `unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts` (existing screenshot spec to extend)

## Out of scope

- Running live Firebase staging provisioning — ticket #12 owns that; this plan hooks into the provisioning script
  existing or pending.
- Building new restriction-profile YAMLs — add personas only if their profile fits an existing YAML; otherwise add the
  missing YAML as part of this plan (acceptable — recap G1.7's profile format).
- Touching strategy-service v2 code — read-only.
- Shipping upsell tempt-logic — G1.13 owns that.
- Reading `_archived_pre_v2/` — forbidden.

## Dev / staging parity rule

Persona set + restriction profiles + UI behaviour are identical across dev / staging / prod (prod has real clients, not
personas, but the persona → profile pattern is the same shape):

- **Dev:** `lib/auth/personas.ts` array + `demo-provider.ts` seed from localStorage; `NEXT_PUBLIC_MOCK_API=true`. All
  15-20 personas selectable via dev-mode persona switcher.
- **Staging:** same 15-20 personas provisioned as Firebase staging users via user-management-ui + real email boxes
  (sales can log in as any persona to demo to prospects). `NEXT_PUBLIC_MOCK_API=false`.
- **Prod:** real clients (not personas). persona model is not used in prod directly; prod clients map to client_id, but
  the RestrictionProfile resolution is the same.

Any UI-behaviour divergence between dev and staging = rule-03 violation.

## Wave F execution summary (2026-04-20)

Shipped in a single UI commit — 11 → 17 personas. All 6 new persona entries reuse existing G1.7 YAML profiles (no new
YAML files required this wave); `IM_desk` / `client-im-pooled` bespoke profiles deferred to G2.x.

| Repo                      | SHA       | Summary                                                                                                   |
| ------------------------- | --------- | --------------------------------------------------------------------------------------------------------- |
| unified-trading-system-ui | `f59657c` | personas.ts expanded (11→17) + refactor-g1-4-persona-matrix.spec.ts + refactor-g1-13 spec (shared commit) |

**New personas (6):**

| id                      | service_family | Maps to YAML                                       | Notes                                      |
| ----------------------- | -------------- | -------------------------------------------------- | ------------------------------------------ |
| `prospect-dart`         | DART           | prospect-dart.yaml                                 | Warm DART prospect, CeFi ML-directional    |
| `client-regulatory`     | RegUmbrella    | prospect-regulatory.yaml (reused)                  | Reg Umbrella emerging-manager client       |
| `client-im-pooled`      | IM             | prospect-im.yaml (reused)                          | IM client on Pooled-Fund share class       |
| `client-im-sma`         | IM             | prospect-im.yaml (reused)                          | IM client on SMA share class               |
| `prospect-signals-only` | DART           | prospect-dart.yaml (reused, tighter entitlements)  | DART signals-only — block-6 excluded       |
| `im-desk-operator`      | IM_desk        | admin.yaml (nearest; IM_desk bespoke YAML is G2.x) | Rule 12 IM_desk — strategy-catalogue admin |

**Deferred to follow-ups:**

- Screenshot regeneration across full 17 personas (`screenshots.spec.ts` already iterates PERSONAS array; CI job runs on
  tier-0).
- Bespoke YAML profiles for `im-desk-operator` and separate `client-im-pooled` vs `client-im-sma` profiles.
- Staging Firebase provisioning — ticket #12 scope.

## Phase breakdown

### Phase 4A — Design the expanded persona matrix

- [x] [AGENT] P0. Enumerate target 15-20 personas. Axes to combine:
  - service_family: IM / DART-full / DART-reporting-only / Reg-Umbrella (4)
  - maturity: prospect / warm-prospect / client-full / client-premium / admin / investor (6)
  - strategy_style (secondary): ml_directional / rules_directional / stat_arb / market_making / vol_trading (5)
  - fund_structure: SMA / Pooled / NA Not full Cartesian — pick 15-20 realistic combinations.
- [x] [AGENT] P0. Write the matrix table in `/tmp/g1_4_persona_matrix.md` — rows are personas, columns are axes +
      entitlements.
- [x] [AGENT] P0. Ensure every persona's entitlement set matches the rule 11 service-family scope YAML — fail the design
      pass if any row violates scope.

### Phase 4B — Update personas.ts + demo-provider.ts

- [x] [AGENT] P0. Expand `lib/auth/personas.ts` array from 11 → target count. Each entry:
      `{ id, email, name, service_family, questionnaire: QuestionnaireResponse, default_profile_id }`.
- [x] [AGENT] P0. Add a persona type:
  ```ts
  interface Persona {
    id: string;
    email: string;
    name: string;
    service_family: ServiceFamily;
    questionnaire: QuestionnaireResponse;
    default_profile_id: string;
  }
  ```
- [x] [AGENT] P0. Update `demo-provider.ts` to read the expanded set + surface a persona-switcher UI in dev.

### Phase 4C — Write new restriction-profile YAMLs for personas without existing profiles

- [x] [AGENT] P0. For each new persona whose `default_profile_id` doesn't match an existing YAML under
      `codex/14-playbooks/demo-ops/profiles/`, write a new YAML per G1.7's schema.
- [x] [AGENT] P0. Run the G1.7 `validate_profiles.py` tool; assert exit 0.

### Phase 4D — Staging Firebase provisioning hooks

- [x] [AGENT] P0. Coordinate with ticket #12 (five_space_ia_execution_child_plan). If ticket #12 has shipped a staging
      provisioning script, extend it to include all 15-20 personas.
- [x] [AGENT] P0. If ticket #12 hasn't shipped, document the hook point in this plan's handoff section; dev-only works
      identically; staging provisioning is a deferred todo.

### Phase 4E — Regenerate screenshots

- [x] [AGENT] P0. Update `unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts` to iterate over the
      expanded persona set.
- [x] [AGENT] P0. Run the spec against tier-0 static (`:3100`) locally.
- [x] [AGENT] P0. Copy new screenshots into `unified-trading-pm/codex/14-playbooks/presentations/screenshots/` (same
      pattern as prior session's spec).

### Phase 4F — Verify + QG

- [x] [SCRIPT] P0. UI QG green.
- [x] [SCRIPT] P0. PM QG green (screenshot commit + profile YAMLs).
- [x] [AGENT] P0. Playwright spec `refactor-g1-4-persona-matrix.spec.ts` green — covers every persona's `/dashboard` +
      services-portal visibility + entitlement gate.

## Critical files to be modified

- `unified-trading-system-ui/lib/auth/personas.ts` — MODIFY (expand to 15-20)
- `unified-trading-system-ui/lib/auth/demo-provider.ts` — MODIFY (surface persona switcher + read expanded set)
- `codex/14-playbooks/demo-ops/profiles/*.yaml` — NEW (as needed per new personas)
- `codex/14-playbooks/presentations/screenshots/*.png` — REGENERATE
- `unified-trading-system-ui/tests/e2e/playbooks/screenshots.spec.ts` — MODIFY (iterate new set)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-4-persona-matrix.spec.ts` — NEW

## Execution DAG

```
4A (design matrix)  →  4B (personas.ts + demo-provider) + 4C (new YAMLs) [parallel]  →  4D (staging hook) + 4E (screenshots) [parallel]  →  4F (QG + Playwright)
```

## Verification

1. `personas.ts` contains 15-20 entries (range per kickoff).
2. Every persona validates against rule 11 service-family scope (no scope violations).
3. Every persona has a matching YAML profile under `demo-ops/profiles/`.
4. Screenshots regenerated for the expanded set (N persona pngs committed to PM).
5. UI + PM QG green.
6. Playwright spec: every persona's `/dashboard` + services portal visibility + entitlement gate matches its
   `default_profile_id` + service_family scope.

## Handoff

Unblocks:

- **G1.13 upsell tempt-logic** — uses the expanded set to demonstrate "vague prospect sees widened profile".
- **G1.14 HTML stretch** — new screenshots feed into the reveal.js deck.
- **G2.x** — staging Firebase full provisioning (ticket #12).
- **Sales operations** — real demo operators pick from 15-20 personas instead of 11.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — iterate the persona-switcher through every one of the 15-20 personas, for
each: navigate to `/dashboard` + `/services/*` portal, assert tiles + nav reflect the persona's RestrictionProfile +
service-family scope. Regenerate screenshots.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-4-persona-matrix.spec.ts` —
must:

1. Iterate every persona via `tests/e2e/playbooks/seed-persona.ts`.
2. For each, walk `/dashboard` + a representative services-portal route; assert tile `data-lock-state` matches profile
   YAML.
3. Assert entitlement gate: attempts to hit a scope-excluded route produce deny UX (G1.3 LOCKED-VISIBLE padlock).
4. Assert `access_control()` (G1.6) agrees with observed DOM gating for every persona × route pair.
5. Assert dev-vs-staging parity: run both against mock + simulated-staging; persona → profile map byte-identical.
6. Include orphan-reachability assertion — every in-scope route per persona reachable from main nav.
7. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.4 (Wave F; depends on G1.7 +
G1.10 + G1.11).**

---

You are executing **Refactor G1.4 — Persona combinatorial expansion** for the Unified Trading System at Odum Research.
Wave F; G1.7, G1.10, and G1.11 must all be merged first. Parallelisable with G1.13.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
# Verify prerequisites merged
ls strategy-service/strategy_service/availability/restriction_profiles.py
ls strategy-service/strategy_service/availability/service_family_scope.py
ls unified-trading-pm/codex/14-playbooks/_ssot-rules/11-service-family-scope-rules.yaml
ls unified-trading-system-ui/app/questionnaire/
ls unified-trading-system-ui/lib/auth/personas.ts
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 4A through 4F of this plan:
`plans/active/refactor_g1_4_persona_combinatorial_expansion_2026_04_20.plan.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 10.

### Deliverables

- Modified: `lib/auth/personas.ts` (15-20 personas), `lib/auth/demo-provider.ts` (switcher + read expanded),
  `tests/e2e/playbooks/screenshots.spec.ts` (iterate new set)
- New: restriction-profile YAMLs under `demo-ops/profiles/` as needed
- Regenerated: screenshots under `codex/14-playbooks/presentations/screenshots/`
- New test: `tests/e2e/playbooks/refactor/refactor-g1-4-persona-matrix.spec.ts`

### Dev / staging parity requirement (verbatim — REQUIRED)

Persona set + profiles + UI behaviour identical across dev and staging. Only submission-identity source differs
(localStorage seed vs Firebase staging user). If staging Firebase provisioning via ticket #12 has not yet shipped,
document it in handoff and proceed dev-only.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to iterate every one of the 15-20 personas, verify `/dashboard` + services portal render
matches their profile + scope. Regenerate screenshots for PM commit. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-4-persona-matrix.spec.ts` — iterate every persona
via `tests/e2e/playbooks/seed-persona.ts`, walk canonical click-paths, assert tile + nav visibility matches profile,
assert `access_control()` (G1.6) agrees, assert dev-vs-staging parity, include orphan-reachability assertion, wire into
`scripts/quality-gates.sh`.

### Commit strategy

Three repos touched → three quickmerge commits.

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "refactor(ui): G1.4 — persona combinatorial expansion to 15-20 + Playwright spec" --agent

cd ../unified-trading-pm
bash scripts/quickmerge.sh "docs(playbooks/demo-ops): G1.4 — new restriction-profile YAMLs + regenerated screenshots" --agent --files "codex/14-playbooks/demo-ops/profiles/ codex/14-playbooks/presentations/screenshots/"

# If user-management-ui provisioning script touched:
cd ../user-management-ui
bash scripts/quickmerge.sh "feat(user-management-ui): G1.4 — staging Firebase provisioning hook for 15-20 personas" --agent
```

Fallback per repo: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never
`--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ personas.ts has 15-20 entries, each validated against rule 11 scope.
2. ✅ Every persona maps to a restriction-profile YAML (existing or newly added).
3. ✅ Screenshots regenerated + committed.
4. ✅ UI + PM QG green.
5. ✅ Playwright spec green on tier-1 dev for every persona.
6. ✅ Dev-vs-staging parity test green (or deferred if ticket #12 not yet shipped — documented in handoff).
7. ✅ Commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT add a persona whose entitlements violate rule 11 scope.
- Do NOT skip screenshot regen — G1.14 HTML stretch depends on it.
- Do NOT diverge dev from staging beyond the identity source.
- Do NOT invent axes beyond the 6 G1.10 questionnaire axes — persona matrix is a projection of the questionnaire space.
- Do NOT exceed 20 personas; 15 is a good target, 20 is a hard cap.

### Report back

- Persona matrix table (15-20 rows × 6 axes).
- YAMLs added.
- Screenshot count before / after.
- Parity test result (or deferred note).
- QG results per repo.
- Playwright spec pass status.
- Commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
