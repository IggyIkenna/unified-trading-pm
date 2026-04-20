---
title: Refactor G1.2 — Instruction-schema validation service
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.2
  - codex/14-playbooks/infra-spec/stage-3b-instruction-schema-contract.md
  - codex/14-playbooks/infra-spec/stage-3b-uac-combo-rules.md
  - codex/14-playbooks/infra-spec/stage-3b-combo-rules-schema.yaml
  - codex/14-playbooks/_ssot-rules/10-strategy-instruction-schema-principles.md
  - refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md
# Wave C — parallel with refactor_g1_6.
---

# Refactor G1.2 — Instruction-schema validation service

## Context

Stage 3E §1.2: build the validation service that enforces `stage-3b-instruction-schema-contract.md`. Client instructions
submitted to the execution path today can be malformed, reference non-existent venues, or combine (archetype, category,
instrument, venue) tuples that are not declared supported in the UAC ArchetypeCapabilityV2 registry (built in G1.8).
Without a validator, bad instructions surface as mysterious fills-or-fails deep inside execution-service. The validator
rejects non-compliant shapes at the edge with actionable error messages, and feeds the pricing engine with an
integration-depth signal per rule 10 — clients who integrate more deeply (structured instructions vs loose text) get
preferential pricing and validation behaviour.

## Decisions locked with user (2026-04-20)

| Decision                                                                  | Chosen                                                                                                                                                                                                                                     | Source                      |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- |
| Validator is a Python library + a thin service wrapper, not an edge proxy | Library in UAC (schema-owning repo); service wrapper in execution-service OR a new sidecar. This plan lays out both options; recommendation: live in execution-service as a pre-handler, sidecar deferred to G2 if load profile demands it | Kickoff §1.2                |
| Consumes UAC `ArchetypeCapabilityV2` (G1.8)                               | Validator calls `ArchetypeCapabilityRegistry.for_pair(category, instrument)` + checks archetype is in the returned set + checks venue is in archetype's `supported_venues`                                                                 | Kickoff §1.2 + G1.8 handoff |
| Error messages are actionable                                             | Each rejection names the violating field + allowed values + a single sentence explaining "why"                                                                                                                                             | rule 10                     |
| Integration-depth signal                                                  | Validator emits a per-instruction score `0–1` (0 = text, 1 = fully structured) to pricing engine via a sidecar event; pricing formula (G1.6) includes this term                                                                            | Kickoff §1.2 + rule 10      |

## Cross-references

- **Upstream (Wave B):** `refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md` — hard dep
  (ArchetypeCapabilityRegistry)
- **Sibling Wave C:** `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md` —
  consumes the integration-depth signal emitted here.
- **Stage 3B specs (infra source of truth):** `stage-3b-instruction-schema-contract.md`, `stage-3b-uac-combo-rules.md`,
  `stage-3b-combo-rules-schema.yaml`, `stage-3b-downstream-analytics-capability-matrix.md`
- **Rule 10:** `_ssot-rules/10-strategy-instruction-schema-principles.md`

## Mandatory read-set

1. `codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.2
2. `codex/14-playbooks/infra-spec/stage-3b-instruction-schema-contract.md` — full
3. `codex/14-playbooks/infra-spec/stage-3b-uac-combo-rules.md` — full
4. `codex/14-playbooks/infra-spec/stage-3b-combo-rules-schema.yaml` — full
5. `codex/14-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md`
6. `codex/14-playbooks/_ssot-rules/10-strategy-instruction-schema-principles.md`
7. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py` (landed by G1.8)
8. `strategy-service/strategy_service/engine/strategies/v2/` (read-only, for sanity-checking validator against source of
   truth)
9. `execution-service/execution_service/` — existing request-handling layout for deciding the validator injection point
10. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py`

## Out of scope

- Running the pricing formula itself (that's G1.6).
- Defining what "integration depth" means beyond the 0–1 score — rule 10 + stage-3b own the definition; validator just
  measures.
- Changing execution-service's post-validation execution path.
- Venue-specific schema quirks — stage-3b is venue-agnostic at the contract level; per-venue validators are a G2
  concern.
- Building a sidecar (recommend execution-service pre-handler; sidecar is a future G2 if needed).

## Phase breakdown

### Phase 2A — Design the validator contract

- [ ] [AGENT] P0. Define `InstructionValidator` Python class with
      `validate(instruction: ClientInstruction) -> ValidationResult` where
      `ValidationResult = Ok(integration_depth: float) | Err(FieldError[])`.
- [ ] [AGENT] P0. Map each rule-10 principle + each stage-3b schema field to one validation check.
- [ ] [AGENT] P0. Specify where validator lives: library at
      `unified-api-contracts/unified_api_contracts/validation/instruction.py`; wrapper at
      `execution-service/execution_service/validation/`.

### Phase 2B — Implement the library

- [ ] [AGENT] P0. Implement `InstructionValidator.validate()` — calls `ArchetypeCapabilityRegistry.for_pair()`, walks
      the stage-3b schema, produces `FieldError[]`.
- [ ] [AGENT] P0. Each `FieldError` has: `field: str`, `violation: str`, `allowed: Sequence[str]`, `why: str`.
- [ ] [AGENT] P0. Implement integration-depth scorer: ratio of structured fields present / total fields + weight by
      field type (structured enum = 1.0, free text = 0.0, hybrid = 0.5).
- [ ] [AGENT] P0. Unit tests: 30+ cases covering valid shapes, every field-level rejection, the 10 block-list groups in
      `codex/09-strategy/architecture-v2/category-instrument-coverage.md` (BL-1 through BL-10).

### Phase 2C — Wire the service wrapper

- [ ] [AGENT] P0. Add `execution-service/execution_service/validation/instruction_validator_middleware.py` that
      intercepts incoming instructions and runs the validator before the execution path.
- [ ] [AGENT] P0. On validation failure: return a structured 400 response with every `FieldError`; no
      partial-instruction execution.
- [ ] [AGENT] P0. On validation success: forward the instruction + emit `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` UTL
      event (see UTL events in `unified-trading-library/src/unified_trading_library/events/`) carrying score +
      instruction id.

### Phase 2D — UTL event registration

- [ ] [AGENT] P0. Register `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` event in
      `unified-trading-library/src/unified_trading_library/events/` `STANDARD_LIFECYCLE_EVENTS`.
- [ ] [AGENT] P0. Payload schema:
      `{ instruction_id: str, integration_depth: float, client_id: str, timestamp: iso8601 }`.

### Phase 2E — Verify + QG

- [ ] [SCRIPT] P0. UAC QG green.
- [ ] [SCRIPT] P0. execution-service QG green.
- [ ] [SCRIPT] P0. UTL QG green.
- [ ] [AGENT] P0. Playwright spec `refactor-g1-2-instruction-schema-validation.spec.ts` green on tier-1 dev.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/validation/instruction.py` — NEW
- `unified-api-contracts/tests/unit/test_instruction_validator.py` — NEW (30+ cases)
- `execution-service/execution_service/validation/instruction_validator_middleware.py` — NEW
- `execution-service/tests/unit/test_instruction_validator_middleware.py` — NEW
- `unified-trading-library/src/unified_trading_library/events/__init__.py` (or wherever STANDARD_LIFECYCLE_EVENTS is
  declared) — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts` — NEW

## Execution DAG

```
2A (design)  →  2B (library) + 2D (UTL event register)  [parallel after 2A]  →  2C (middleware)  →  2E (QG + Playwright)
```

## Verification

1. UAC tests: 30+ validator cases green.
2. execution-service middleware tests green.
3. Rejected instruction returns 400 with structured `FieldError[]` — verified by integration test.
4. Accepted instruction emits `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` — verified by mocked event bus.
5. QG green on UAC + execution-service + UTL.

## Handoff

Unblocks:

- **G1.6 derivation engine** — pricing formula can now consume `integration_depth` to tier pricing.
- **G2.x** — analytics pipeline that correlates integration_depth to execution quality.
- **G2.x** — client-facing validation error UI (render the FieldError[] as actionable fix-this-now messages).

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) through MCP
Playwright tools — submit a series of instructions via the execution submission surface (wherever the UI client surface
lives; `/services/execution/` or similar): valid instruction, missing-field, unsupported (archetype, category) pair,
unsupported venue, purely-text. Verify 400 with structured FieldError[] surfaces to the UI; verify success case emits
event (inspect via network tab).

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts` — must:

1. Seed a `client-full` persona via `tests/e2e/playbooks/seed-persona.ts`.
2. Submit the matrix of valid + invalid test instructions via the UI submission surface (or direct API-call assertion
   via `request.post`).
3. For each invalid submission, assert `status === 400` + response body includes `errors: FieldError[]` with actionable
   copy.
4. For the valid submission, assert integration_depth in response body (or in the UTL event emitted, if surfaced).
5. Assert visibility-slicing vs G1.6 `access_control(user, route, item, phase)` formula — client-full should have
   access; validator runs per-submission regardless of role.
6. Include orphan-reachability assertion — the execution submission surface is reachable from main nav.
7. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.2 (Wave C, parallel with G1.6;
both depend on G1.8).**

---

You are executing **Refactor G1.2 — Instruction-schema validation service** for the Unified Trading System at Odum
Research. Wave C; G1.8 must be merged first; parallelisable with G1.6.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C execution-service checkout live-defi-rollout && git -C execution-service pull
git -C unified-trading-library checkout live-defi-rollout && git -C unified-trading-library pull
ls unified-trading-pm/codex/14-playbooks/infra-spec/stage-3b-instruction-schema-contract.md
ls unified-trading-pm/codex/14-playbooks/infra-spec/stage-3b-uac-combo-rules.md
# Verify G1.8 has merged
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 2A through 2E of this plan:
`plans/active/refactor_g1_2_instruction_schema_validation_service_2026_04_20.plan.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 10.

### Deliverables

- New: `unified-api-contracts/unified_api_contracts/validation/instruction.py` + test
- New: `execution-service/execution_service/validation/instruction_validator_middleware.py` + test
- Modified: `unified-trading-library/.../events/` (register `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED`)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to submit the matrix of valid + invalid instructions via the UI submission surface; verify
structured 400 + FieldError[] surfaces and success case emits the integration-depth event. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts` — seed
`client-full` persona via `tests/e2e/playbooks/seed-persona.ts`, walk canonical click-path, assert 400 + FieldError[]
for each invalid case + integration_depth surfaced on success, assert visibility-slicing vs G1.6 `access_control`
formula (stub until G1.6 lands), include orphan-reachability assertion, wire into `scripts/quality-gates.sh`.

### Commit strategy

Four repos touched → one commit per repo with an agent quickmerge each.

```
cd unified-api-contracts
bash scripts/quickmerge.sh "feat(uac): G1.2 — instruction-schema validator library" --agent

cd ../unified-trading-library
bash scripts/quickmerge.sh "feat(utl/events): G1.2 — INSTRUCTION_INTEGRATION_DEPTH_OBSERVED event" --agent

cd ../execution-service
bash scripts/quickmerge.sh "feat(execution-service): G1.2 — instruction validator middleware" --agent

cd ../unified-trading-system-ui
bash scripts/quickmerge.sh "test(playbooks): G1.2 — validator Playwright spec" --agent --files "tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts"
```

Fallback per repo if quickmerge blocks: `git add <files> && git commit -m "..." && git push origin live-defi-rollout`.
Never `--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ UAC tests: ≥ 30 validator cases green, including every BL-1…BL-10 block-list group.
2. ✅ execution-service middleware tests green; bad instruction → 400 + FieldError[]; good instruction → 200 + event.
3. ✅ UTL event registered in STANDARD_LIFECYCLE_EVENTS.
4. ✅ QG green on all four touched repos (UAC + UTL + execution-service + UI).
5. ✅ Playwright spec green on tier-1 dev.
6. ✅ 4 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT build a sidecar — live in execution-service as a pre-handler; sidecar is a deferred G2 option.
- Do NOT inline the archetype × venue × (category, instrument) truth table — call `ArchetypeCapabilityRegistry` from
  G1.8.
- Do NOT bypass the validator in the execution path — every instruction flows through validation.
- Do NOT emit partial-instruction execution — reject whole instruction on any FieldError.

### Report back

- Validator test count + coverage.
- Middleware test count.
- UTL event registration confirmation.
- Playwright spec path + pass status.
- 4 commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
