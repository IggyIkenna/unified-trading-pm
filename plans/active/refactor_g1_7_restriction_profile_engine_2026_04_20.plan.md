---
title: Refactor G1.7 — Restriction-profile engine
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.7
  - codex/14-playbooks/demo-ops/demo-restriction-profiles.md
  - codex/14-playbooks/demo-ops/pre-demo-curation-rules.md
  - codex/14-playbooks/demo-ops/dart-demo-modes.md
  - codex/14-playbooks/demo-ops/demo-decision-matrix.md
  - refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md
# Wave D — parallel with refactor_g1_11. Downstream (Wave E): refactor_g1_10; (Wave F): refactor_g1_{4,13}.
---

# Refactor G1.7 — Restriction-profile engine

## Context

Stage 3E §1.7 builds the demo-profile registry + persona-overlay engine specified in
`demo-ops/demo-restriction-profiles.md`. A restriction profile declares, per audience, which catalogue slots / nav items
/ tiles are unlocked, padlocked, or hidden. The engine consumes persona + flavour + environment context, returns a
structured RestrictionProfile, and feeds three surfaces:

1. **G1.3 LOCKED-VISIBLE tile** — maps profile entries to the three-state enum.
2. **G1.6 derivation engine** — `demo_universe()` + `prod_restrictions()` call into this engine when the caller provides
   a pre-constructed profile ID.
3. **G1.13 upsell tempt-logic** — extension layer that widens the profile for vague questionnaire answers.

Environment-agnostic: identical engine behaviour in dev / staging / prod. Only the persona identity source differs
(localStorage seed in dev vs Firebase in staging/prod).

## Decisions locked with user (2026-04-20)

| Decision                                                                                                | Chosen                                                                                                                              | Source                                                 |
| ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------- | ------------------- |
| Engine lives in `strategy-service/strategy_service/availability/restriction_profiles.py`                | Colocated with derivation engine (G1.6) — single source of truth for all availability logic                                         | Kickoff §1.7                                           |
| Demo profile registry is declarative YAML at `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/` | One file per profile (`prospect-im.yaml`, `prospect-dart.yaml`, `prospect-regulatory.yaml`, `admin.yaml`, `client-full.yaml`, etc.) | Kickoff §1.7 + `demo-ops/demo-restriction-profiles.md` |
| Persona overlays are computed, not stored                                                               | `RestrictionProfile = base_profile + persona_overlay + questionnaire_override + env_override`                                       | Kickoff §1.7                                           |
| Environment-agnostic                                                                                    | Identical logic dev/staging/prod; input source differs only                                                                         | Dev-staging parity rule                                |
| Profile shape uses closed enum                                                                          | `RestrictionProfile = { [tile_id]: "unlocked"                                                                                       | "padlocked"                                            | "hidden" }` — maps directly to G1.3's lockState | Kickoff §1.3 + §1.7 |

## Cross-references

- **Upstream (Wave C):** `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md` —
  hard dep (derivation engine + access_control)
- **Sibling Wave D:** `refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md` — parallel; both depend on G1.6
- **Downstream Wave E:** `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md` — questionnaire output
  maps to overlays
- **Downstream Wave F:** `refactor_g1_4_persona_combinatorial_expansion_2026_04_20.plan.md` (15-20 personas × this
  engine), `refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.plan.md` (tempt logic extends this)
- **G1.3 consumer:** restriction profile's per-tile state feeds `use-tile-lock-state.ts`
- **Rules cited:** `_ssot-rules/06-show-dont-show-discipline.md`, `_ssot-rules/04-dart-commercial-axes.md`
- **Cross-cutting:** `codex/14-playbooks/cross-cutting/visibility-slicing.md`

## Mandatory read-set

1. `codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.7
2. `codex/14-playbooks/demo-ops/demo-restriction-profiles.md` — full
3. `codex/14-playbooks/demo-ops/pre-demo-curation-rules.md`
4. `codex/14-playbooks/demo-ops/dart-demo-modes.md`
5. `codex/14-playbooks/demo-ops/demo-decision-matrix.md`
6. `codex/14-playbooks/demo-ops/pre-demo-discovery-framework.md`
7. `codex/14-playbooks/demo-ops/account-intelligence-record.md`
8. `codex/14-playbooks/cross-cutting/visibility-slicing.md`
9. `codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md`
10. `strategy-service/strategy_service/availability/derivation.py` (landed by G1.6)
11. `strategy-service/strategy_service/availability/store.py` (existing Phase-10.5)

## Out of scope

- The questionnaire UI that feeds profile overlays — that's G1.10.
- The upsell tempt-logic overlay — that's G1.13 (extends this engine).
- The persona matrix expansion to 15-20 personas — that's G1.4 (this engine serves whatever personas exist).
- The service-family hard constraints (observe ∈ DART, etc.) — that's G1.11 (layered as a separate gate).
- UI-side rendering of padlocks — that's G1.3 (shipped Wave A).

## Dev / staging parity rule

Demo flows MUST behave identically in dev and staging:

- **Dev (`localhost:3010`):** mock auth via `demo-provider.ts` + localStorage; persona identity comes from the seed.
  Restriction-profile engine receives the seeded persona ID and returns the same profile as it would in staging.
- **Staging (`odum-research.co.uk`):** Firebase staging project; same personas provisioned as real Firebase users.
  Engine receives Firebase user ID, maps to persona, returns the same profile.
- **Prod (`odum-research.com`):** Firebase prod project; real paying clients. Engine receives Firebase user ID, maps to
  client context, returns the prod-scoped profile.

Only difference: persona identity source. Profile computation + YAML definitions + overlay logic are identical. Any
divergence is a rule-03 violation.

## Phase breakdown

### Phase 7A — Design profile YAML schema + registry

- [ ] [AGENT] P0. Define profile YAML schema — each file under
      `codex/14-playbooks/demo-ops/profiles/<persona-slug>.yaml` has: `persona_id`, `base_audience`,
      `tiles: { [tile_id]: "unlocked"|"padlocked"|"hidden" }`, `overrides: { [flavour_id]: { ... }}`.
- [ ] [AGENT] P0. Draft at least 6 profile files: `admin.yaml` (unlocks everything), `client-full.yaml`,
      `prospect-im.yaml`, `prospect-dart.yaml`, `prospect-regulatory.yaml`, `anon.yaml`.
- [ ] [AGENT] P0. Schema validation tool at `codex/14-playbooks/demo-ops/_tools/validate_profiles.py` — fails loud on
      malformed YAML, unknown tile_id, unknown state value.

### Phase 7B — Implement restriction-profile engine

- [ ] [AGENT] P0. Create `strategy-service/strategy_service/availability/restriction_profiles.py`:

  ```python
  class RestrictionProfile(TypedDict):
      persona_id: str
      tiles: Mapping[str, Literal["unlocked", "padlocked", "hidden"]]
      source: Literal["demo", "prod", "admin"]

  def resolve_profile(persona: Persona, flavour: DemoFlavour | None, env: Env, questionnaire: QuestionnaireResponse | None = None) -> RestrictionProfile: ...
  ```

- [ ] [AGENT] P0. Loader reads YAML at boot; applies overlays in defined order:
      `base → persona_overlay → questionnaire_override → env_override`.
- [ ] [AGENT] P0. Integration with G1.6: `demo_universe()` + `prod_restrictions()` now call `resolve_profile` when
      caller provides a profile ID.
- [ ] [AGENT] P0. Thread-safe; reads YAML once at module load.

### Phase 7C — Wire UI consumer + replace stub

- [ ] [AGENT] P0. Update `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` (the stub landed by G1.3) to
      query a profile-resolution endpoint (server-side) OR hydrate the profile from a server-rendered JSON blob.
      Recommended: hydrate at page load via Next.js RSC + `getPropsForPersona()` helper.
- [ ] [AGENT] P0. Expose profile resolution as internal API: `execution-service` (or a strategy-service internal API)
      serves `/internal/restriction-profile/<persona_id>` returning the resolved RestrictionProfile. UI consumes this
      via server-side fetch.
- [ ] [AGENT] P0. For dev (`VITE_MOCK_API=true`), lib/auth/demo-provider.ts reads the same YAML files (bundled at build)
      and resolves locally without a network call.

### Phase 7D — Unit tests + parity tests

- [ ] [AGENT] P0. `strategy-service/tests/availability/test_restriction_profiles.py` — ≥ 20 cases (base profile per
      persona, overlay application, env override, invalid inputs).
- [ ] [AGENT] P0. Dev/staging parity test: given the same persona + flavour + questionnaire, assert `resolve_profile`
      returns byte-identical RestrictionProfile across dev/staging fixtures.

### Phase 7E — Verify + QG

- [ ] [SCRIPT] P0. strategy-service QG green.
- [ ] [SCRIPT] P0. PM QG green (YAML validation).
- [ ] [SCRIPT] P0. UI QG green.
- [ ] [AGENT] P0. Playwright spec `refactor-g1-7-restriction-profile.spec.ts` green on tier-1 dev.

## Critical files to be modified

- `strategy-service/strategy_service/availability/restriction_profiles.py` — NEW
- `strategy-service/tests/availability/test_restriction_profiles.py` — NEW (≥ 20 cases)
- `codex/14-playbooks/demo-ops/profiles/{admin,client-full,prospect-im,prospect-dart,prospect-regulatory,anon}.yaml` —
  NEW (6 files)
- `codex/14-playbooks/demo-ops/_tools/validate_profiles.py` — NEW
- `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` — MODIFY (replace G1.3 stub with real resolution)
- `unified-trading-system-ui/lib/auth/demo-provider.ts` — MODIFY (hydrate profile from bundled YAML in dev)
- `execution-service/execution_service/api/internal_restriction_profile.py` (or strategy-service internal API) — NEW
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-7-restriction-profile.spec.ts` — NEW

## Execution DAG

```
7A (YAML schema + registry)  →  7B (engine)  →  7C (UI wire) + 7D (tests)  [parallel after 7B]  →  7E (QG + Playwright)
```

## Verification

1. 6 YAML profile files validated by `_tools/validate_profiles.py`.
2. `resolve_profile(persona, flavour, env)` returns expected RestrictionProfile for every (persona, flavour) fixture.
3. Dev/staging parity: identical profile for identical input across environments.
4. G1.3 `use-tile-lock-state.ts` stub replaced; tiles in UI now show real lockState from engine.
5. strategy-service + PM + UI QG green.
6. Playwright spec green.

## Handoff

Unblocks:

- **G1.10 questionnaire flow** — questionnaire response becomes the `questionnaire` arg to `resolve_profile`.
- **G1.13 upsell tempt-logic** — extends `resolve_profile` with a "widen on vague answer" step.
- **G1.4 persona matrix** — expansion to 15-20 personas just adds YAML files; engine doesn't change.
- **G2.x** — restriction-profile preview UI (sales operators can visually confirm what a persona will see before a
  demo).

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — seed 6 personas in turn, navigate services portal, assert tiles render
per each persona's resolved RestrictionProfile. Toggle demo flavours where applicable and re-verify.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-7-restriction-profile.spec.ts` — must:

1. Seed 6 personas in turn via `tests/e2e/playbooks/seed-persona.ts`: `admin`, `client-full`, `prospect-im`,
   `prospect-dart`, `prospect-regulatory`, `anon`.
2. For each persona, walk the services portal and assert each tile's `data-lock-state` attribute matches the
   YAML-declared state.
3. For `prospect-im`, toggle flavour = "sales-pitch" vs "technical-deep-dive" and assert overlays apply correctly.
4. Assert `access_control()` gating (from G1.6) agrees with the RestrictionProfile — a padlocked tile also fails
   access_control for navigation.
5. Assert dev-vs-staging parity: run the same spec against the staging environment (CI pipeline) and assert
   byte-identical RestrictionProfile per persona.
6. Include orphan-reachability assertion — every unlocked tile routes to a real page.
7. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.7 (Wave D, parallel with G1.11;
both depend on G1.6).**

---

You are executing **Refactor G1.7 — Restriction-profile engine** for the Unified Trading System at Odum Research. Wave
D; G1.6 must be merged first; parallelisable with G1.11.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls unified-trading-pm/codex/14-playbooks/demo-ops/demo-restriction-profiles.md
ls unified-trading-pm/codex/14-playbooks/demo-ops/pre-demo-curation-rules.md
# Verify G1.6 merged
ls strategy-service/strategy_service/availability/derivation.py
# Verify G1.3 stub landed
ls unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 7A through 7E of this plan:
`plans/active/refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 11.

### Deliverables

- New: `strategy-service/strategy_service/availability/restriction_profiles.py` + test (≥ 20 cases)
- New: 6 YAML profile files under `codex/14-playbooks/demo-ops/profiles/`
- New: `codex/14-playbooks/demo-ops/_tools/validate_profiles.py`
- New: restriction-profile internal API endpoint
- Modified: `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` (replaces G1.3 stub)
- Modified: `unified-trading-system-ui/lib/auth/demo-provider.ts` (hydrates profile from bundled YAML in dev)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-7-restriction-profile.spec.ts`

### Dev / staging parity requirement (verbatim — REQUIRED)

Demo flows MUST behave identically in dev and staging:

- Dev: localStorage persona seed → `demo-provider.ts` → resolve_profile → RestrictionProfile.
- Staging: Firebase staging auth → persona map → resolve_profile → RestrictionProfile.
- Prod: Firebase prod auth → client context → resolve_profile → RestrictionProfile (prod-scoped).

Engine logic + YAML definitions + overlay ordering are identical. Only the identity source differs. Any divergence =
rule-03 violation.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to verify every persona's rendered tile states match the YAML-declared RestrictionProfile,
including flavour toggles. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-7-restriction-profile.spec.ts` — seed 6 personas via
`tests/e2e/playbooks/seed-persona.ts`, walk canonical click-paths, assert `data-lock-state` matches profile YAML, assert
`access_control()` agrees with profile, assert dev-vs-staging parity, include orphan-reachability assertion, wire into
`scripts/quality-gates.sh`.

### Commit strategy

Four repos touched → four quickmerge commits.

```
cd unified-trading-pm
bash scripts/quickmerge.sh "docs(playbooks/demo-ops): G1.7 — 6 restriction-profile YAMLs + validator tool" --agent

cd ../strategy-service
bash scripts/quickmerge.sh "feat(strategy-service/availability): G1.7 — restriction-profile engine" --agent

cd ../execution-service   # or strategy-service if hosting internal API there
bash scripts/quickmerge.sh "feat(execution-service): G1.7 — internal restriction-profile endpoint" --agent

cd ../unified-trading-system-ui
bash scripts/quickmerge.sh "refactor(ui): G1.7 — wire restriction-profile resolution + spec" --agent
```

Fallback per repo: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never
`--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ 6 YAML profiles validate (`validate_profiles.py` exit 0).
2. ✅ `resolve_profile` test suite ≥ 20 cases green.
3. ✅ G1.3's stub is replaced — `use-tile-lock-state.ts` no longer returns `"unlocked"` unconditionally.
4. ✅ Dev-vs-staging parity test green.
5. ✅ QG green on all 4 repos.
6. ✅ Playwright spec green on tier-1 dev.
7. ✅ 4 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT ship the questionnaire UI here — G1.10 owns it.
- Do NOT ship the upsell tempt-logic here — G1.13 extends this engine.
- Do NOT diverge dev from staging — identical profile logic is a hard rule.
- Do NOT introduce a fourth lockState value — closed enum (unlocked|padlocked|hidden).
- Do NOT bypass `access_control()` from G1.6 — profile and access_control must agree.

### Report back

- YAML profile count + persona IDs.
- Engine test count.
- Parity test result.
- QG results (4 repos).
- Playwright spec pass status.
- 4 commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
