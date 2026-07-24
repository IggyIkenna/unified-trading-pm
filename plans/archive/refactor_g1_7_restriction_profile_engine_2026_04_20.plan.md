---
doc_type: plan
title: Refactor G1.7 — Restriction-profile engine
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
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
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.7,
    /codex/14-playbooks/demo-ops/demo-restriction-profiles.md,
    /codex/14-playbooks/demo-ops/pre-demo-curation-rules.md,
    /codex/14-playbooks/demo-ops/dart-demo-modes.md,
    /codex/14-playbooks/demo-ops/demo-decision-matrix.md,
    refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.7 — Restriction-profile engine

> ## Implementation note (post-ship — Option X pattern)
>
> Plan body says the engine lives in `strategy-service/strategy_service/availability/restriction_profiles.py`. **Actual
> ship hosts pure logic in UAC; strategy-service only carries the HTTP wrapper** (Option X).
>
> Authoritative paths (verified 2026-04-22):
>
> - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py` — engine + registry
> - `strategy-service/strategy_service/api/restriction_profile_router.py` — HTTP wrapper
>   (`/internal/restriction-profile`)
>
> The plan body's `strategy-service/strategy_service/availability/restriction_profiles.py` reference is kept for
> historical context; trust this note over body prose.

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

| Decision | Chosen | Source | |
------------------------------------------------------------------------------------------------------- |
-----------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------------------------ | ----------------------------------------------- |
------------------- | | Engine lives in `strategy-service/strategy_service/availability/restriction_profiles.py` |
Colocated with derivation engine (G1.6) — single source of truth for all availability logic | Kickoff §1.7 | | Demo
profile registry is declarative YAML at `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/` | One file per
profile (`prospect-im.yaml`, `prospect-dart.yaml`, `prospect-regulatory.yaml`, `admin.yaml`, `client-full.yaml`, etc.) |
Kickoff §1.7 + `demo-ops/demo-restriction-profiles.md` | | Persona overlays are computed, not stored |
`RestrictionProfile = base_profile + persona_overlay + questionnaire_override + env_override` | Kickoff §1.7 | |
Environment-agnostic | Identical logic dev/staging/prod; input source differs only | Dev-staging parity rule | | Profile
shape uses closed enum |
`RestrictionProfile = { [tile_id]: "unlocked"                                                                                       | "padlocked"                                            | "hidden" }`
— maps directly to G1.3's lockState | Kickoff §1.3 + §1.7 |

## Cross-references

- **Upstream (Wave C):** `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md` — hard
  dep (derivation engine + access_control)
- **Sibling Wave D:** `refactor_g1_11_service_family_scope_rules_2026_04_20.md` — parallel; both depend on G1.6
- **Downstream Wave E:** `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md` — questionnaire output maps
  to overlays
- **Downstream Wave F:** `refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md` (15-20 personas × this engine),
  `refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.md` (tempt logic extends this)
- **G1.3 consumer:** restriction profile's per-tile state feeds `use-tile-lock-state.ts`
- **Rules cited:** `_ssot-rules/06-show-dont-show-discipline.md`, `_ssot-rules/04-dart-commercial-axes.md`
- **Cross-cutting:** `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.7
2. `/codex/14-playbooks/demo-ops/demo-restriction-profiles.md` — full
3. `/codex/14-playbooks/demo-ops/pre-demo-curation-rules.md`
4. `/codex/14-playbooks/demo-ops/dart-demo-modes.md`
5. `/codex/14-playbooks/demo-ops/demo-decision-matrix.md`
6. `/codex/14-playbooks/demo-ops/pre-demo-discovery-framework.md`
7. `/codex/14-playbooks/demo-ops/account-intelligence-record.md`
8. `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md`
9. `/codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md`
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

- **Dev (`localhost:3000`):** mock auth via `demo-provider.ts` + localStorage; persona identity comes from the seed.
  Restriction-profile engine receives the seeded persona ID and returns the same profile as it would in staging.
- **Staging (`odum-research.co.uk`):** Firebase staging project; same personas provisioned as real Firebase users.
  Engine receives Firebase user ID, maps to persona, returns the same profile.
- **Prod (`odum-research.com`):** Firebase prod project; real paying clients. Engine receives Firebase user ID, maps to
  client context, returns the prod-scoped profile.

Only difference: persona identity source. Profile computation + YAML definitions + overlay logic are identical. Any
divergence is a rule-03 violation.

## Wave D execution summary (2026-04-20)

All Phase 7A-7E shipped in 5 commits. Option X carry-through (UAC host, not strategy-service). Plus the strategy-service
HTTP endpoint that was flagged as "defer" in the micro-plan — operator signed off on shipping it too.

| Repo                      | SHA        | Summary                                                                        |
| ------------------------- | ---------- | ------------------------------------------------------------------------------ |
| unified-trading-pm        | `6ab71bf7` | 6 YAML profiles + `validate_profiles.py`                                       |
| unified-api-contracts     | `38324af`  | `restriction_profiles.py` engine + `RestrictionProfile.tiles` field + 29 tests |
| unified-trading-pm        | `49c0117f` | `sync-restriction-profiles-to-ui.sh` (YAML → TS mirror)                        |
| strategy-service          | `5b08b4f`  | `api/restriction_profile_router.py` (/internal/restriction-profile) + 5 tests  |
| unified-trading-system-ui | `da1cd43`  | TS mirror + `useTileLockState` real resolver + QG hook + Playwright spec       |

**Deviations from micro-plan:**

- Vocabulary translation at the sync-script boundary: YAML+UAC use `padlocked`; UI uses `padlocked-visible` (G1.3 enum).
  The sync script maps at the boundary so neither side has to shift vocabulary. Cleaner than bulk-renaming either side.
- Upstream fix: `unified_api_contracts.internal.__init__` imported a non-existent `ScopedKillSwitchSpec` which broke
  every UAC test import. Surgical removal (two dangling references) landed with the G1.7 UAC commit.

## Phase breakdown

### Phase 7A — Design profile YAML schema + registry

- [x] [AGENT] P0. Define profile YAML schema — each file under
      `codex/14-playbooks/demo-ops/profiles/<persona-slug>.yaml` has: `persona_id`, `base_audience`,
      `tiles: { [tile_id]: "unlocked"|"padlocked"|"hidden" }`, `overrides: { [flavour_id]: { ... }}`.
- [x] [AGENT] P0. Draft at least 6 profile files: `admin.yaml` (unlocks everything), `client-full.yaml`,
      `prospect-im.yaml`, `prospect-dart.yaml`, `prospect-regulatory.yaml`, `anon.yaml`.
- [x] [AGENT] P0. Schema validation tool at `codex/14-playbooks/demo-ops/_tools/validate_profiles.py` — fails loud on
      malformed YAML, unknown tile_id, unknown state value.

### Phase 7B — Implement restriction-profile engine

- [x] [AGENT] P0. Create `strategy-service/strategy_service/availability/restriction_profiles.py`:

  ```python
  class RestrictionProfile(TypedDict):
      persona_id: str
      tiles: Mapping[str, Literal["unlocked", "padlocked", "hidden"]]
      source: Literal["demo", "prod", "admin"]

  def resolve_profile(persona: Persona, flavour: DemoFlavour | None, env: Env, questionnaire: QuestionnaireResponse | None = None) -> RestrictionProfile: ...
  ```

- [x] [AGENT] P0. Loader reads YAML at boot; applies overlays in defined order:
      `base → persona_overlay → questionnaire_override → env_override`.
- [x] [AGENT] P0. Integration with G1.6: `demo_universe()` + `prod_restrictions()` now call `resolve_profile` when
      caller provides a profile ID.
- [x] [AGENT] P0. Thread-safe; reads YAML once at module load.

### Phase 7C — Wire UI consumer + replace stub

- [x] [AGENT] P0. Update `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` (the stub landed by G1.3) to
      query a profile-resolution endpoint (server-side) OR hydrate the profile from a server-rendered JSON blob.
      Recommended: hydrate at page load via Next.js RSC + `getPropsForPersona()` helper.
- [x] [AGENT] P0. Expose profile resolution as internal API: `execution-service` (or a strategy-service internal API)
      serves `/internal/restriction-profile/<persona_id>` returning the resolved RestrictionProfile. UI consumes this
      via server-side fetch.
- [x] [AGENT] P0. For dev (`VITE_MOCK_API=true`), lib/auth/demo-provider.ts reads the same YAML files (bundled at build)
      and resolves locally without a network call.

### Phase 7D — Unit tests + parity tests

- [x] [AGENT] P0. `strategy-service/tests/availability/test_restriction_profiles.py` — ≥ 20 cases (base profile per
      persona, overlay application, env override, invalid inputs).
- [x] [AGENT] P0. Dev/staging parity test: given the same persona + flavour + questionnaire, assert `resolve_profile`
      returns byte-identical RestrictionProfile across dev/staging fixtures.

### Phase 7E — Verify + QG

- [x] [SCRIPT] P0. strategy-service QG green.
- [x] [SCRIPT] P0. PM QG green (YAML validation).
- [x] [SCRIPT] P0. UI QG green.
- [x] [AGENT] P0. Playwright spec `refactor-g1-7-restriction-profile.spec.ts` green on tier-1 dev.

## Shipped-state reconciliation (2026-04-20)

Checkboxes above flipped retroactively after code shipped in 3 commits without the plan updating. Deviations from plan
prose worth naming for downstream agents:

- **Option X carry-through:** restriction-profile engine lives at
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py` — NOT
  `strategy-service/strategy_service/availability/restriction_profiles.py` as the plan header states. This mirrors
  G1.6's Option X decision. Public facade re-exports via `unified_api_contracts.strategy` (`resolve_profile`,
  `RESTRICTION_PROFILE_REGISTRY`, `known_persona_ids`, `Env`, `QuestionnaireResponse`, `ProfileYaml`).
- **Tests landed in UAC**, not strategy-service:
  `unified-api-contracts/tests/internal/unit/test_restriction_profiles.py` — 22 cases (plan target ≥ 20 met).
- **6 YAML profile files shipped** under `codex/14-playbooks/demo-ops/profiles/` as planned: admin.yaml,
  client-full.yaml, prospect-im.yaml, prospect-dart.yaml, prospect-regulatory.yaml, anon.yaml.
- **G1.3 stub replaced:** `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` now resolves real lockState
  via the restriction-profile engine (commit `da1cd43`).
- **PM sync script + CI hook** shipped as the delivery pattern for the UI TS mirror:
  `unified-trading-pm/scripts/propagation/sync-restriction-profiles-to-ui.{sh,py}` regenerates
  `unified-trading-system-ui/lib/architecture-v2/restriction-profiles.ts`; hooked into UI `scripts/quality-gates.sh` as
  a drift-check.
- **Commit SHAs:** UAC `38324af` (engine); PM `49c0117f` (YAMLs) + `6ab71bf7` (sync tooling); UI `da1cd43` (TS mirror +
  Playwright spec + QG hook).

## Spillover carried from G1.6 (allocator-gate deferral)

G1.6 Phase 6D checkbox "Wire access_control into ClientAllocatorInstance gate" was deferred to G1.7 per the committed
plan. G1.7 as shipped did NOT pick it up; G1.11 as shipped (2026-04-20 commit `073e6c1`) also did NOT pick it up —
G1.11's scope was the UAC-layer service-family pre-check, which lands at a different layer than the allocator's gate.
`portfolio_allocator/service.py:125` in strategy-service still calls the legacy `validate_allocation_authorised()` gate.
**Deferred to Wave E** per the 2026-04-20 Wave C/D audit — the Wave E (G1.10 questionnaire) agent should pick up the
swap since they will already be modifying `portfolio_allocator/` surfaces for questionnaire-driven client setup. See
`refactor_g1_11_service_family_scope_rules_2026_04_20.md` § Follow-ups / spillover.

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

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
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
`plans/active/refactor_g1_7_restriction_profile_engine_2026_04_20.md`

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

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
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

---

## Micro-execution plan (sub-agent Phase 1, appended 2026-04-20)

> Drafted by Wave-D kickoff sub-agent. Plan-mode only — no code edits yet; operator approval required before Phase 7A.
> Companion micro-plan for G1.11 in `refactor_g1_11_service_family_scope_rules_2026_04_20.md` § Micro-execution plan.

### Plan-vs-reality drifts (verified 2026-04-20 against `live-defi-rollout` post-Wave-C)

| # | Plan claims | Reality post-Wave-C | Resolution | | --- |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
-------------------------------------------------------------------------------------------------------------------------------

|
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| | 1 | Line 39 Decisions table: engine lives in
`strategy-service/strategy_service/availability/restriction_profiles.py`. Lines 108, 138, 152 reinforce. | Wave-C Option
X put `derivation.py` in **UAC** (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py`).
G1.7's `resolve_profile()` must be callable by `demo_universe()` + `prod_restrictions()` inside derivation.py; those
calls would become a **circular dep** if resolve_profile lives in strategy-service (UAC → strategy-service is the wrong
direction). | **Recommend Option X carry-through.** Ship `restriction_profiles.py` in UAC at
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`. Tests in
`unified-api-contracts/tests/internal/unit/test_restriction_profiles.py`. YAML loader uses `importlib.resources`-style
path resolution (PM codex is sibling repo; dev/CI resolve via `UNIFIED_TRADING_WORKSPACE_ROOT` env var same as G1.8
`_find_codex_markdown()` helper). Operator sign-off requested. | | 2 | Line 121: "Integration with G1.6:
`demo_universe()` + `prod_restrictions()` now call `resolve_profile` when caller provides a profile ID" | These
functions live in UAC derivation.py now, not strategy-service. **Modifying derivation.py here risks merge conflict with
G1.11's `access_control()` modification** (both Wave D items touch the same file). | **Sequence conflicts, not
parallelise.** G1.7 touches derivation.py `demo_universe()` + `prod_restrictions()` bodies; G1.11 touches
`access_control()` + new pre-check call. Land G1.7 commit first, then G1.11 rebases. Document as sequential inside Wave
D despite the plans being tagged parallel. | | 3 | Line 131: "Expose profile resolution as internal API:
`execution-service` (or a strategy-service internal API) serves `/internal/restriction-profile/<persona_id>`" | G1.7 is
a pure-function layer — no HTTP surface justification yet for Wave D. Stage-3c §5 says "restriction-profile-service" is
a Stage-3E G3 concern. | **Defer HTTP endpoint.** Ship only the pure function + YAML loader + UI integration. If UI
needs server-rendered profile for SSR, add a minimal strategy-service `api/restriction_profile_router.py` in a FOLLOW-UP
commit (stage-3c §5 G3 scope). For Wave D, UI-dev hydrates from bundled YAML (bundled at build via a TS mirror similar
to how G1.8 coverage.ts mirrors UAC manifest). | | 4 | Line 134: "dev (`VITE_MOCK_API=true`), lib/auth/demo-provider.ts
reads the same YAML files (bundled at build)" | YAML-in-TS-bundle adds build-time complexity. Simpler: generate a
`lib/architecture-v2/restriction-profiles.ts` TS mirror from YAML via a PM
`scripts/propagation/sync-restriction-profiles-to-ui.sh` (mirrors G1.8's `sync-archetype-capability-to-ui.sh` pattern,
canonical post-G1.8). | **Use G1.8 sync-script pattern.** PM script reads YAML at `demo-ops/profiles/*.yaml`, renders TS
mirror with AUTO-GEN banner, wired into UI `scripts/quality-gates.sh` pre-hook for drift detection. UI reads the TS
mirror directly — no runtime YAML parsing. | | 5 | Line 40 Decisions table: "Demo profile registry is declarative YAML
at `codex/14-playbooks/demo-ops/profiles/`" | Directory does NOT exist today. | Net-new, fine. Validator tool at
`codex/14-playbooks/demo-ops/_tools/validate_profiles.py` (also net-new directory). | | 6 | Line 116 signature:
`resolve_profile(persona: Persona, flavour: DemoFlavour                                                                                         | None, env: Env, questionnaire: QuestionnaireResponse                                                                                                                                                                                                                                                                                                                                            | None = None)`
| `Persona` + `DemoFlavour` already exist in UAC derivation.py (G1.6 shipped these). `Env` + `QuestionnaireResponse` are
net-new. | Reuse existing `Persona` + `DemoFlavour`. Define `Env = Literal["dev", "staging", "prod"]` + placeholder
`QuestionnaireResponse` BaseModel (concrete fields are G1.10 scope — ship with `extra="allow"` for forward-compat OR
empty dict default for Wave D). |

### Pre-audit manifest (Citadel rule-6)

Grep across workspace excluding `.venv*`, `node_modules`, `build`, `_archived_pre_v2`:

| Symbol                          | Current hits                                                                                                   | Action                                                                                                                                   |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `resolve_profile`               | 0 runtime                                                                                                      | Net-new.                                                                                                                                 |
| `RestrictionProfile`            | 1 in UAC derivation.py (G1.6 shipped a stub type) + 1 in `prod_restrictions.py` plan prose only                | Extend the existing stub in derivation.py with full tile-map shape (`tiles: Mapping[str, Literal[...]]`). No rename — same type evolves. |
| `check_service_family_scope`    | 0                                                                                                              | Net-new (G1.11 owns).                                                                                                                    |
| `QuestionnaireResponse`         | 0                                                                                                              | Net-new. Minimal stub for Wave D; G1.10 fleshes out.                                                                                     |
| `useTileLockState`              | 1 — `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` (stub returns "unlocked" for every tile) | Replace stub body with real lookup into the TS mirror `lib/architecture-v2/restriction-profiles.ts`.                                     |
| `demo-provider.ts` persona seed | existing `lib/auth/` infra                                                                                     | Profile loaded via the TS mirror; no changes to persona seed mechanism.                                                                  |

### Execution DAG

```
7A YAML schema + 6 profile files + PM validator tool
    └── 7B restriction_profiles.py in UAC + resolve_profile() + unit tests (≥ 20)
        └── 7C Extend demo_universe() + prod_restrictions() in derivation.py to delegate to resolve_profile()
            └── COMMIT 1 (UAC — must land BEFORE G1.11's access_control edit — sequencing note)
        └── 7D PM sync-script (YAML → TS mirror with AUTO-GEN banner) + COMMIT 2 (PM)
            └── 7E UI: use-tile-lock-state.ts replace stub; wire QG hook → COMMIT 3 (UI)
                └── 7F Playwright spec → COMMIT 4 (UI add or same commit)
```

### Files × line-ranges × commit sequence

**COMMIT 1 — UAC** `feat(uac): G1.7 — restriction-profile engine + 6 YAML profiles`

| File                                                                                           | Action                                                                                                                                                                                       | Approx LOC |
| ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/admin.yaml`                           | NEW                                                                                                                                                                                          | ~30        |
| `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/client-full.yaml`                     | NEW                                                                                                                                                                                          | ~40        |
| `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/prospect-im.yaml`                     | NEW                                                                                                                                                                                          | ~35        |
| `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/prospect-dart.yaml`                   | NEW                                                                                                                                                                                          | ~35        |
| `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/prospect-regulatory.yaml`             | NEW                                                                                                                                                                                          | ~30        |
| `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/anon.yaml`                            | NEW                                                                                                                                                                                          | ~25        |
| `unified-trading-pm/codex/14-playbooks/demo-ops/_tools/validate_profiles.py`                   | NEW — schema validator (fails loud on unknown tile_id / state)                                                                                                                               | ~100       |
| `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py` | NEW — `Env`, `QuestionnaireResponse` stub, `resolve_profile()`, YAML loader via `UNIFIED_TRADING_WORKSPACE_ROOT`                                                                             | ~280       |
| `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py`           | MODIFY — `demo_universe()` + `prod_restrictions()` delegate to `resolve_profile()` when caller provides a profile-id; extend `RestrictionProfile` type with `tiles: dict[str, Literal[...]]` | +40 / -5   |
| `unified-api-contracts/unified_api_contracts/internal/architecture_v2/__init__.py`             | MODIFY — export new symbols                                                                                                                                                                  | +6         |
| `unified-api-contracts/unified_api_contracts/strategy.py`                                      | MODIFY — re-export `resolve_profile`, `RestrictionProfile` (tile-map shape), `Env`, `QuestionnaireResponse`                                                                                  | +8         |
| `unified-api-contracts/tests/internal/unit/test_restriction_profiles.py`                       | NEW — ≥ 20 cases: base profile per persona × 6, overlay application × 5, env override × 3, invalid inputs × 4, YAML loader tests × 2+                                                        | ~350       |

Split rationale: keep all G1.7 UAC + PM work in a single commit so UAC CI tests see the YAML the loader expects. PM's
sync-script commits separately.

**COMMIT 2 — PM** `feat(pm): G1.7 — UAC→UI restriction-profiles sync script`

| File                                                                        | Action                                                                    | Approx LOC |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ---------- |
| `unified-trading-pm/scripts/propagation/sync-restriction-profiles-to-ui.sh` | NEW — shell wrapper (mirrors G1.8 `sync-archetype-capability-to-ui.sh`)   | ~40        |
| `unified-trading-pm/scripts/propagation/sync_restriction_profiles_to_ui.py` | NEW — Python body reading YAML + rendering TS mirror with AUTO-GEN banner | ~150       |

**COMMIT 3 — UI** `feat(ui/visibility): G1.7 — real tile-lock-state resolution + sync hook`

| File                                                                                               | Action                                                                                                        | Approx LOC |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---------- |
| `unified-trading-system-ui/lib/architecture-v2/restriction-profiles.ts`                            | REGENERATED (AUTO-GEN banner) — TS mirror of 6 YAML profiles + `resolveTileLockState(persona, tileId)` helper | ~200       |
| `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts`                                  | MODIFY — replace stub body with `resolveTileLockState()` call; read persona from existing persona context     | +15 / -5   |
| `unified-trading-system-ui/scripts/quality-gates.sh`                                               | MODIFY — add sync-check pre-hook (mirrors G1.8 pattern)                                                       | +4         |
| `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-7-restriction-profile.spec.ts` | NEW — seed 6 personas, assert `data-lock-state` matches YAML, orphan-reachability, dev/staging parity note    | ~180       |

### Playwright spec design

Canonical port `localhost:3000`. Spec mirrors G1.8 + G1.6 shape. Seed 6 personas (`admin` / `client-full` /
`prospect-im` / `prospect-dart` / `prospect-regulatory` / `anon`), navigate catalogue, assert per-tile `data-lock-state`
attribute matches YAML-declared state. Dev/staging parity check via PM sync-script `--check` (same technique as G1.8
coverage.ts).

### Breaking-change analysis (Citadel rule-3)

- G1.3's `use-tile-lock-state.ts` stub — EXPECTED stub replacement, not a regression. Stub already documents the G1.7
  plan.
- UAC `derivation.py` — `demo_universe()` + `prod_restrictions()` gain optional `profile_id` arg (kwargs-only, default
  None to preserve existing test behaviour). New fallback path only fires when caller opts in.
- New `RestrictionProfile` `tiles` field — extends the existing BaseModel. Existing consumers don't break because
  `tiles: Mapping[str, ...] = {}` default.

### Success criteria

| Phase                     | Gate                                                                                                                       |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 7A YAML                   | 6 profile files pass `validate_profiles.py`; every tile_id exists in UI ServiceDefinition registry                         |
| 7B engine                 | `from unified_api_contracts.strategy import resolve_profile, RestrictionProfile, Env` clean; ≥ 20 tests green              |
| 7C derivation integration | UAC QG green; existing derivation tests still pass; new integration tests for profile-id path                              |
| 7D PM sync                | `bash sync-restriction-profiles-to-ui.sh --check` fails pre-regen, passes after `--write` (same as G1.8)                   |
| 7E UI                     | UI QG pre-hook catches drift; `useTileLockState` returns YAML-declared value; Playwright spec green; commit SHAs on origin |

### Open questions for operator

1. **Option X carry-through** (drift #1): ship `restriction_profiles.py` in UAC, not strategy-service? Default yes.
   Operator confirm?
2. **Sequencing with G1.11** (drift #2): both Wave D items modify UAC `derivation.py`. Land G1.7 first, G1.11 rebases?
   Or keep parallel and accept merge conflicts? Default sequential (G1.7 first), G1.11 rebases.
3. **HTTP endpoint defer** (drift #3): skip `/internal/restriction-profile/<id>` endpoint for Wave D; UI consumes via TS
   mirror only. Adds it in a follow-up if SSR needs it. Default yes.
4. **QuestionnaireResponse stub**: ship as empty BaseModel placeholder; concrete fields land in G1.10. Default yes.

### Pre-flight for Phase 7A execution (when approved)

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-api-contracts status --short
git -C unified-trading-pm status --short
git -C unified-trading-system-ui status --short
# Wave C verified:
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py
.venv-workspace/bin/python -c "from unified_api_contracts.strategy import resolve_profile" 2>&1 | head  # expect ImportError (not yet shipped)
```
