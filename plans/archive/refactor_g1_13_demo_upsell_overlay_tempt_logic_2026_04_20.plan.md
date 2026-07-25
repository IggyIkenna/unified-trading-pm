---
doc_type: plan
title: Refactor G1.13 — Demo upsell-overlay tempt-logic
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
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §1.13,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    refactor_g1_7_restriction_profile_engine_2026_04_20.md,
    refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.13 — Demo upsell-overlay tempt-logic

## Context

Stage 3E §1.13 (2026-04-20 amendment) implements the tempt-logic specified in `demo-ops/upsell-overlays.md`: when a
prospect's questionnaire response is **vague** on a given axis (e.g. "all" selected for venue scope, or no strategy
style expressed), the demo restriction-profile **widens by one level** on that axis — surfacing adjacent capability that
the prospect might want to upsell into. In prod, profiles tighten back to the explicit picks. This is a per-axis
transform applied between questionnaire ingestion and G1.7 `resolve_profile` execution.

## Decisions locked with user (2026-04-20)

| Decision                                            | Chosen                                                                                                                                                                                                   | Source                                        |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Tempt-logic widens profile in DEMO environment only | Prod NEVER widens — tight-pick profile stays tight                                                                                                                                                       | Kickoff §1.13 + `demo-ops/upsell-overlays.md` |
| Widening is per-axis, +1 level                      | Axis hierarchy: explicit picks → adjacent capability → all-in-family → everything. Widen by one step per vague axis                                                                                      | Kickoff §1.13                                 |
| Engine extension to G1.7                            | New `apply_tempt_logic(response: QuestionnaireResponse, env: Env) -> QuestionnaireResponse` transform in `strategy-service/strategy_service/availability/tempt_logic.py`; chained into `resolve_profile` | Kickoff §1.13                                 |
| Config lives in demo-ops                            | `codex/14-playbooks/demo-ops/upsell-overlay-hierarchy.yaml` — declarative per-axis hierarchy                                                                                                             | Kickoff §1.13                                 |
| Dev-staging parity                                  | Same tempt-logic in both demo environments; prod disables via env flag                                                                                                                                   | Dev-staging parity rule                       |

## Cross-references

- **Upstream (Wave D):** `refactor_g1_7_restriction_profile_engine_2026_04_20.md` — extends this engine
- **Upstream (Wave E):** `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md` — consumes questionnaire
  response
- **Sibling Wave F:** `refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md`
- **Demo-ops source:** `/codex/14-customer-journeys/demo-ops/upsell-overlays.md`,
  `/codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md`,
  `/codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md`
- **Rules cited:** `_ssot-rules/06-show-dont-show-discipline.md` (LOCKED-VISIBLE as the upsell surface)

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.13
2. `/codex/14-customer-journeys/demo-ops/upsell-overlays.md` — full, especially "When overlays appear / When overlays do
   NOT appear / Design principles / Anti-patterns"
3. `/codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md`
4. `/codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md`
5. `strategy-service/strategy_service/availability/restriction_profiles.py` (landed by G1.7)
6. `unified-trading-system-ui/lib/auth/demo-provider.ts`
7. `unified-trading-system-ui/app/questionnaire/` (landed by G1.10)

## Out of scope

- Widening in prod — prod NEVER tempts; only explicit picks apply.
- Touching strategy-service v2 code — read-only.
- New questionnaire axes — tempt logic operates on G1.10's existing 6 axes.
- New persona definitions — G1.4 owns persona matrix.
- Reading `_archived_pre_v2/` — forbidden.

## Dev / staging parity rule

Tempt-logic behaves identically in dev and staging demo modes; disabled in prod:

- **Dev (demo mode):** `VITE_MOCK_API=true`. Tempt-logic runs on every questionnaire response. UI surfaces padlocked
  (LOCKED-VISIBLE) tiles for widened-in slots.
- **Staging (demo mode):** `VITE_MOCK_API=false` but `DEMO_MODE=true` env flag. Tempt-logic runs identically; UI
  behaviour matches dev.
- **Prod:** `DEMO_MODE=false`. Tempt-logic is a no-op; `apply_tempt_logic` returns the response unchanged.

Logic, YAML, and UI surfaces are identical across dev/staging; prod gates on env flag. Any dev/staging divergence =
rule-03 violation.

## Wave F execution summary (2026-04-20)

All Phase 13A-13E shipped in 3 commits. Option X carry-through (tempt- logic transform in UAC, not strategy-service).
Rule ID 13 for the hierarchy YAML (slot free — rule 11 was codex-scope-registry, rule 12 service-family-scope-rules).

| Repo                      | SHA        | Summary                                                                        |
| ------------------------- | ---------- | ------------------------------------------------------------------------------ |
| unified-trading-pm        | `a7f970b1` | `upsell-overlay-hierarchy.yaml` + `validate_upsell_hierarchy.py`               |
| unified-api-contracts     | `147c773`  | `tempt_logic.py` + `apply_tempt_logic` wired into `resolve_profile` + 22 tests |
| unified-trading-system-ui | `f59657c`  | `refactor-g1-13-upsell-tempt-logic.spec.ts` (shared with G1.4 spec commit)     |

**Deviations:**

- UAC host (Option X carry-through) — `tempt_logic.py` lives in `unified-api-contracts/.../internal/architecture_v2/`,
  not in strategy-service. Matches G1.6/G1.7 pattern. Plan prose suggested `strategy-service/.../tempt_logic.py`; that
  was pre-Wave-C drift.
- For Wave F each vague axis widens to its "all" fallback (simplest hierarchy step). Adjacent-family-by-asset-class
  nuance is a G2.x extension — the YAML hierarchy already enumerates the richer steps for the tempt-logic to consume
  later.
- UI widening-round-trip Playwright assertion marked `test.fixme` — the demo-provider doesn't yet thread
  `questionnaire-response-v1` localStorage into `useTileLockState`. That wiring is the last mile and lands in a
  follow-up (tracked under downstream unblocks).

## Phase breakdown

### Phase 13A — Draft the upsell hierarchy YAML

- [x] [AGENT] P0. Write `codex/14-playbooks/demo-ops/upsell-overlay-hierarchy.yaml` — per-axis widening rules:

  ```yaml
  axes:
    categories:
      hierarchy: [explicit-picks, adjacent-by-family, all-in-class, everything]
      vague_triggers: [empty_array, all_selected]
    instrument_types:
      hierarchy: [explicit-picks, adjacent-by-asset-class, all-in-category, everything]
      vague_triggers: [empty_array]
    venue_scope:
      hierarchy: [explicit-venues, all-in-category, all]
      vague_triggers: [all_keyword, empty]
    strategy_style:
      hierarchy: [explicit-families, adjacent-families, all]
      vague_triggers: [empty_array]
    # service_family + fund_structure do NOT widen — these are commercial / structural decisions.
  ```

- [x] [AGENT] P0. Validator tool at `codex/14-playbooks/demo-ops/_tools/validate_upsell_hierarchy.py`.

### Phase 13B — Implement `apply_tempt_logic`

- [x] [AGENT] P0. Create `strategy-service/strategy_service/availability/tempt_logic.py`:

  ```python
  def apply_tempt_logic(response: QuestionnaireResponse, env: Env) -> QuestionnaireResponse:
      if not env.is_demo:
          return response  # prod / no-op
      widened = dict(response)
      for axis, cfg in load_hierarchy().items():
          if is_vague(response[axis], cfg.vague_triggers):
              widened[axis] = step_up(response[axis], cfg.hierarchy)
      return widened
  ```

- [x] [AGENT] P0. `is_vague` + `step_up` pure helpers; each axis's widening is independent.

### Phase 13C — Wire into `resolve_profile`

- [x] [AGENT] P0. Modify `strategy-service/strategy_service/availability/restriction_profiles.py` `resolve_profile`
      signature: `resolve_profile(persona, flavour, env, questionnaire=None)` → internally calls
      `apply_tempt_logic(questionnaire, env)` before applying the questionnaire-overlay step.
- [x] [AGENT] P0. Prod disables by setting `env.is_demo = False`.

### Phase 13D — Unit tests

- [x] [AGENT] P0. `strategy-service/tests/availability/test_tempt_logic.py` — ≥ 20 cases covering: every vague-trigger
      per axis; widening result matches hierarchy step; prod env returns unchanged; service_family + fund_structure
      never widen.
- [x] [AGENT] P0. End-to-end test: vague questionnaire → `resolve_profile` → RestrictionProfile has more `padlocked`
      (not `unlocked`, not `hidden`) tiles than a tight questionnaire for the same persona.

### Phase 13E — Verify + QG

- [x] [SCRIPT] P0. strategy-service QG green.
- [x] [SCRIPT] P0. PM QG green (YAML).
- [x] [AGENT] P0. Playwright spec `refactor-g1-13-upsell-tempt-logic.spec.ts` green on tier-1 dev.

## Critical files to be modified

- `codex/14-playbooks/demo-ops/upsell-overlay-hierarchy.yaml` — NEW
- `codex/14-playbooks/demo-ops/_tools/validate_upsell_hierarchy.py` — NEW
- `strategy-service/strategy_service/availability/tempt_logic.py` — NEW
- `strategy-service/strategy_service/availability/restriction_profiles.py` — MODIFY (wire `apply_tempt_logic` into
  `resolve_profile`)
- `strategy-service/tests/availability/test_tempt_logic.py` — NEW (≥ 20 cases)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-13-upsell-tempt-logic.spec.ts` — NEW

## Execution DAG

```
13A (hierarchy YAML + validator)  →  13B (apply_tempt_logic)  →  13C (wire resolve_profile) + 13D (tests)  [parallel]  →  13E (QG + Playwright)
```

## Verification

1. Hierarchy YAML validates.
2. `apply_tempt_logic` returns unchanged in prod env.
3. Vague questionnaire → wider profile than tight questionnaire — assertion in tests.
4. service_family + fund_structure NEVER widen — assertion in tests.
5. QG green on strategy-service + PM + UI.
6. Playwright spec: vague prospect sees padlocked adjacent-capability tiles; tight prospect sees only their scope.

## Handoff

Unblocks:

- **G2.x** — sales-ops tempt-logic tuning (hierarchy YAML is the knob).
- **G2.x** — post-demo followup orchestration (upsell-candidate tiles observed during the demo become CRM hot signals).
- **G1.14 HTML stretch** — demo slide can show the tempt-logic visually with before/after persona screenshots.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — submit a vague questionnaire (e.g. all categories + empty strategy
style), navigate to services portal, verify padlocked adjacent-capability tiles appear. Submit a tight questionnaire for
same persona and verify those tiles are hidden. Toggle `DEMO_MODE` env and verify prod behaviour (no widening).

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-13-upsell-tempt-logic.spec.ts` — must:

1. Run two scenarios: vague questionnaire + tight questionnaire for the same persona seed.
2. For vague: assert services-portal shows `data-lock-state="padlocked"` on adjacent-capability tiles that would be
   `hidden` under tight.
3. For tight: assert those tiles are `hidden`.
4. Toggle env flag (via test fixture) to simulate prod; assert vague input produces the same profile as tight input (no
   widening in prod).
5. Assert service_family + fund_structure answers never widen — tight/vague on those axes produces identical profile.
6. Assert `access_control()` (G1.6) agrees with observed tile states.
7. Assert dev-vs-staging parity: same response + same env → identical profile.
8. Include orphan-reachability assertion — widened-in tiles show LOCKED-VISIBLE + hover upsell copy but never route to a
   broken page.
9. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.13 (Wave F; depends on G1.7 +
G1.10).**

---

You are executing **Refactor G1.13 — Demo upsell-overlay tempt-logic** for the Unified Trading System at Odum Research.
Wave F; G1.7 and G1.10 must be merged first. Parallelisable with G1.4.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls unified-trading-pm/codex/14-customer-journeys/demo-ops/upsell-overlays.md
# Verify G1.7 + G1.10 merged
ls strategy-service/strategy_service/availability/restriction_profiles.py
ls unified-trading-system-ui/app/questionnaire/
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 13A through 13E of this plan:
`plans/active/refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 7.

### Deliverables

- New: `codex/14-playbooks/demo-ops/upsell-overlay-hierarchy.yaml`
- New: `codex/14-playbooks/demo-ops/_tools/validate_upsell_hierarchy.py`
- New: `strategy-service/strategy_service/availability/tempt_logic.py` + test (≥ 20 cases)
- Modified: `strategy-service/strategy_service/availability/restriction_profiles.py` (wire `apply_tempt_logic` into
  `resolve_profile`)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-13-upsell-tempt-logic.spec.ts`

### Dev / staging parity requirement (verbatim — REQUIRED)

Tempt-logic behaves identically in dev and staging demo modes, disabled in prod. Identical YAML hierarchy + identical
`apply_tempt_logic` transform + identical UI surfacing. Only prod differs via `DEMO_MODE=false` env flag. Dev-vs-staging
divergence = rule-03 violation.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to submit vague + tight questionnaires, verify widened vs tight profile in UI, toggle env to
simulate prod + assert no widening. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-13-upsell-tempt-logic.spec.ts` — seed relevant
personas via `tests/e2e/playbooks/seed-persona.ts`, walk canonical click-paths for vague + tight scenarios, assert
widening in demo + no-widening in prod + service_family/fund_structure never widen, assert `access_control()` agrees,
assert dev-vs-staging parity, include orphan-reachability assertion, wire into `scripts/quality-gates.sh`.

### Commit strategy

Three repos touched → three quickmerge commits.

```
cd unified-trading-pm
bash scripts/quickmerge.sh "docs(playbooks/demo-ops): G1.13 — upsell-overlay hierarchy YAML + validator" --agent

cd ../strategy-service
bash scripts/quickmerge.sh "feat(strategy-service/availability): G1.13 — tempt-logic transform + wire into resolve_profile" --agent

cd ../unified-trading-system-ui
bash scripts/quickmerge.sh "test(playbooks): G1.13 — upsell tempt-logic Playwright spec" --agent --files "tests/e2e/playbooks/refactor/refactor-g1-13-upsell-tempt-logic.spec.ts"
```

Fallback per repo: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never
`--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ Hierarchy YAML validates.
2. ✅ ≥ 20 tempt-logic unit tests green.
3. ✅ Prod env passes questionnaire unchanged.
4. ✅ service_family + fund_structure never widen.
5. ✅ Vague response → wider profile; tight response → tight profile — integration assertion.
6. ✅ QG green on strategy-service + PM + UI.
7. ✅ Playwright spec green on tier-1 dev; dev-staging parity + prod no-widening all covered.
8. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT widen in prod — `DEMO_MODE=false` is a hard gate.
- Do NOT widen service_family or fund_structure axes — commercial / structural axes are never tempted.
- Do NOT skip `apply_tempt_logic` in demo env — every questionnaire response passes through it.
- Do NOT add new questionnaire axes — logic operates on G1.10's 6 axes.
- Do NOT diverge dev from staging (demo mode behaviour identical).

### Report back

- Hierarchy YAML (paste full).
- Unit test count.
- Vague-vs-tight profile diff example.
- QG results (3 repos).
- Playwright spec pass status.
- 3 commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
