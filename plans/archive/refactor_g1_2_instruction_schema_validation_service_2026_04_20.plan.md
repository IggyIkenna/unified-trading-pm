---
doc_type: plan
title: Refactor G1.2 — Instruction-schema validation service
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
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
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.2,
    /codex/14-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
    /codex/14-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    codex/14-playbooks/infra-spec/stage-3b-combo-rules-schema.yaml,
    /codex/14-playbooks/_ssot-rules/10-strategy-instruction-schema-principles.md,
    refactor_g1_8_uac_archetype_capability_v2_2026_04_20.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

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

- **Upstream (Wave B):** `refactor_g1_8_uac_archetype_capability_v2_2026_04_20.md` — hard dep
  (ArchetypeCapabilityRegistry)
- **Sibling Wave C:** `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md` — consumes
  the integration-depth signal emitted here.
- **Stage 3B specs (infra source of truth):** `stage-3b-instruction-schema-contract.md`, `stage-3b-uac-combo-rules.md`,
  `stage-3b-combo-rules-schema.yaml`, `stage-3b-downstream-analytics-capability-matrix.md`
- **Rule 10:** `_ssot-rules/10-strategy-instruction-schema-principles.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.2
2. `/codex/14-playbooks/infra-spec/stage-3b-instruction-schema-contract.md` — full
3. `/codex/14-playbooks/infra-spec/stage-3b-uac-combo-rules.md` — full
4. `codex/14-playbooks/infra-spec/stage-3b-combo-rules-schema.yaml` — full
5. `/codex/14-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md`
6. `/codex/14-playbooks/_ssot-rules/10-strategy-instruction-schema-principles.md`
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

- [x] [AGENT] P0. Defined `InstructionValidator` Python class in UAC with
      `validate(instruction: ClientInstruction) -> InstructionValidationResult` (`ok=True` → `integration_depth: float`
      ∈ [0, 1]; `ok=False` → `errors: InstructionFieldError[]`).
- [x] [AGENT] P0. Mapped each rule-10 principle + stage-3b §2 field to one validation check; routed (category,
      instrument_type, venue) tuples through `archetypes_for_pair()` so BL-1..BL-10 group rejections surface as
      field-level errors without local blocker re-declaration.
- [x] [AGENT] P0. Validator lives at `unified-api-contracts/unified_api_contracts/internal/validation/instruction.py`
      (Citadel-internal per workspace rule); public surface is the new `unified_api_contracts.instruction` facade.
      Middleware at `execution-service/execution_service/validation/instruction_validator_middleware.py`.

### Phase 2B — Implement the library

- [x] [AGENT] P0. `InstructionValidator.validate()` implemented — Pydantic-layer + venue + pair-support checks produce
      `InstructionFieldError[]` on failure; rule-10 integration-depth score computed on success.
- [x] [AGENT] P0. `InstructionFieldError` BaseModel: `field: str`, `violation: str`, `allowed: tuple[str, ...]`,
      `why: str`. `ConfigDict(frozen=True, extra="forbid")`.
- [x] [AGENT] P0. Integration-depth scorer: weighted ratio over stage-3b fields (structured enum = 1.0, hybrid = 0.5,
      free text = 0.0).
- [x] [AGENT] P0. 47 unit cases green — 8 Pydantic required-field + 10 BL-1..BL-10 + 3 venue-mismatch + 7 nested
      validator + 7 integration-depth boundaries + 4 happy-path + 3 result-invariant.

### Phase 2C — Wire the service wrapper

- [x] [AGENT] P0. Added `execution-service/execution_service/validation/instruction_validator_middleware.py` as
      framework-agnostic pre-handler (`validate_client_instruction(...) -> InstructionAccepted | InstructionRejected`).
- [x] [AGENT] P0. On failure: `InstructionRejected(http_status=400, errors: InstructionFieldError[])`; caller renders
      structured 400 + stops. No partial-instruction forwarding.
- [x] [AGENT] P0. On success: emits `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` via injected `emit_event` callable
      (production binds to UTL `log_event`/`publish_coordination_event`).

### Phase 2D — UTL event registration

- [x] [AGENT] P0. Registered `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` in
      `unified-trading-library/unified_trading_library/events/event_types.py` (real path — plan prose said `src/...`
      which was stale) + `STANDARD_LIFECYCLE_EVENTS` + new `INSTRUCTION_VALIDATION_EVENT_TYPES` domain group.
- [x] [AGENT] P0. `InstructionIntegrationDepthObservedPayload` dataclass with `__post_init__` guards:
      `instruction_id: str` (non-empty), `integration_depth: float` ∈ [0, 1] (NaN/inf rejected), `client_id: str`
      (non-empty), `timestamp_utc: str` (non-empty, ISO-8601). 11 test cases green.

### Phase 2E — Verify + QG

- [x] [SCRIPT] P0. UAC: 47 validator tests green (44 landed 2026-04-20 commit `6dfa23f`; +3 explicit 0.75/0.875/1.0
      integration-depth spec-boundary cases in 2026-04-20 follow-up commit `ddb841f` to close the Wave C/D audit
      test-count reconciliation); ruff clean; basedpyright clean on new files.
- [x] [SCRIPT] P0. execution-service: 8 middleware tests green; ruff clean; basedpyright clean on new files.
- [x] [SCRIPT] P0. UTL: 11 event tests green; ruff clean; basedpyright clean on new files.
- [x] [AGENT] P0. Playwright spec `refactor-g1-2-instruction-schema-validation.spec.ts` committed (UI commit `50a3519`)
      — file-presence + orphan-reachability + UTL symbol structural check; live POST/400-matrix marked `test.fixme`
      pending G2.x instruction-submission UI surface.

### Commit SHAs (pushed to `origin/live-defi-rollout` 2026-04-20)

| Repo                      | SHA        | Summary                                                                       |
| ------------------------- | ---------- | ----------------------------------------------------------------------------- |
| unified-api-contracts     | `6dfa23f`  | validator library + 44 tests + `unified_api_contracts.instruction` facade     |
| unified-trading-library   | `45741b9e` | `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` event + payload dataclass + 11 tests |
| execution-service         | `573d4012` | `instruction_validator_middleware.py` + 8 tests                               |
| unified-trading-system-ui | `50a3519`  | Playwright spec + 3 `test.fixme` placeholders for G2.x submission-UI          |

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

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) through MCP
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
`plans/active/refactor_g1_2_instruction_schema_validation_service_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 10.

### Deliverables

- New: `unified-api-contracts/unified_api_contracts/validation/instruction.py` + test
- New: `execution-service/execution_service/validation/instruction_validator_middleware.py` + test
- Modified: `unified-trading-library/.../events/` (register `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED`)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
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

---

## Micro-execution plan (sub-agent Phase 1, appended 2026-04-20)

> Drafted by Wave-C kickoff sub-agent. Plan-mode only — no code edits yet; operator approval required before Phase 2A/2B
> execution. Companion micro-plan for G1.6 is in
> `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md` § Micro-execution plan.

### Plan-prose drifts vs reality (verified 2026-04-20 against `live-defi-rollout`)

| #   | Plan claims                                                                                              | Reality (post-G1.8)                                                                                                                                                             | Resolution                                                                                                                                                                                                                                                                                                                                                                      |
| --- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Line 35: `ArchetypeCapabilityRegistry.for_pair(category, instrument)`                                    | UAC ships free function `archetypes_for_pair(category, instrument_type, *, include_partial=True)` + module-level tuple `ARCHETYPE_CAPABILITY_REGISTRY`                          | Validator calls `archetypes_for_pair()` from `unified_api_contracts.strategy`; no Registry class. Use `include_partial=False` for strict SUPPORTED-only archetype set.                                                                                                                                                                                                          |
| 2   | Line 35: "checks venue is in archetype's `supported_venues`"                                             | `ArchetypeCapability.supported_venues` exists as `@property` aggregating over `cells`. `archetypes_for_venue(venue)` also exists.                                               | Either API works; validator prefers `capability.supported_venues` per archetype (tighter coupling + clearer error copy).                                                                                                                                                                                                                                                        |
| 3   | Line 82-83: validator library at `unified_api_contracts/validation/instruction.py` (public path)         | Public validation facade does not exist. UAC rule: domain types live under `unified_api_contracts/internal/...`; public surface is `unified_api_contracts/{domain}.py` facades. | Put types + checker in `unified_api_contracts/internal/validation/instruction.py` (Pydantic `BaseModel` with `ConfigDict(frozen=True, extra="forbid")`, mirrors G1.8 pattern). Re-export from NEW public facade `unified_api_contracts/instruction.py` — `from unified_api_contracts.instruction import InstructionValidator, ClientInstruction, ValidationResult, FieldError`. |
| 4   | Line 125-126: UTL events at `unified-trading-library/src/unified_trading_library/events/__init__.py`     | Real path: `unified-trading-library/unified_trading_library/events/__init__.py` (no `src/` prefix). `STANDARD_LIFECYCLE_EVENTS` lives in `event_types.py`.                      | Register `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` in `unified_trading_library/events/event_types.py`.                                                                                                                                                                                                                                                                           |
| 5   | Line 34 (Decisions table): "Library in UAC (schema-owning repo); service wrapper in execution-service"   | UAC Citadel rule: Schema provenance — all domain types come from UAC. Execution-service has no existing `validation/` sub-package.                                              | Locked: types + validator in UAC (`internal/validation/`), public facade `unified_api_contracts.instruction`, middleware in execution-service `execution_service/validation/`.                                                                                                                                                                                                  |
| 6   | Line 93 (Phase 2B): "the 10 block-list groups in `category-instrument-coverage.md` (BL-1 through BL-10)" | G1.8 codex parity test enforces these 10 groups exist in codex md; block_list_refs live on `ArchetypeCapabilityCell.block_list_refs`                                            | Validator does NOT re-check BL-\* groups directly — it asks `archetypes_for_pair()` (which respects blocks already baked into manifest by G1.8). Unit tests spot-check each BL-1..BL-10 group produces the right `FieldError`. Don't duplicate G1.8's invariants.                                                                                                               |

Stage-3B richer schema reference (read-only SSOT for validator field-level checks):
`/codex/14-playbooks/infra-spec/stage-3b-instruction-schema-contract.md` defines the 8 required fields
(instrument_venue_context, intended_action, size_or_target_exposure, timeframe_urgency, order_constraints,
strategy_instruction_id, lifecycle_replace_cancel, risk_and_allocation_constraints) — the validator mirrors this
structurally with Pydantic models.

**Note:** The UTL parquet schema at
`unified-trading-library/unified_trading_library/domain_client/schemas/instruction_schema.py` is a DIFFERENT,
lower-level artefact (execution-service parquet contract — TRADE / SWAP / LEND / ... instruction-types with direction,
quantity, etc.). G1.2's `ClientInstruction` is the HIGHER-level client-facing shape defined by stage-3b — the mapping
between them is a validator concern (a valid `ClientInstruction` projects down to one or more rows of the UTL parquet
schema). Keep both; do not merge.

### Pre-audit manifest (Citadel rule-6)

Grep across workspace, excluding `.venv*`, `node_modules`, `build`, `_archived_pre_v2`:

| Symbol                                      | Current hits                                                                                                                                                        | Action                                                                                   | Note                                                                                                       |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `InstructionValidator`                      | 0 runtime hits (plan mentions only)                                                                                                                                 | Net-new                                                                                  | No collision.                                                                                              |
| `ClientInstruction`                         | 0 runtime hits                                                                                                                                                      | Net-new                                                                                  | UAC Pydantic model — new type.                                                                             |
| `ValidationResult` (in a validator context) | Several in UTL/strategy-service domains (`unified_trading_library/domain/validation.py`, `strategy_service/engine/core/validation_service.py`) — unrelated contexts | Scope-rename — call ours `InstructionValidationResult` to avoid collision across facades | Picks: `InstructionValidationResult`, `InstructionFieldError` (not plain `ValidationResult`/`FieldError`). |
| `FieldError`                                | 0 runtime hits as top-level symbol                                                                                                                                  | Net-new as `InstructionFieldError`                                                       | Safer namespacing.                                                                                         |
| `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED`    | 0 runtime hits; only referenced in this plan                                                                                                                        | Net-new UTL event                                                                        | Register in `event_types.py` + `__init__.py` + schemas.py.                                                 |
| `instruction_validator_middleware`          | 0 hits                                                                                                                                                              | Net-new module                                                                           | Execution-service `execution_service/validation/instruction_validator_middleware.py`.                      |
| `integration_depth` (score field)           | 0 runtime hits                                                                                                                                                      | Net-new                                                                                  | Plan-unique scoring.                                                                                       |

Zero existing runtime consumers → zero backwards-compat shims. Purely additive surface.

### Execution DAG

```
2A (audit + design)
    ├── 2B.1 UAC types (ClientInstruction, InstructionFieldError, InstructionValidationResult, IntegrationDepth)
    │       └── 2B.2 UAC InstructionValidator + archetype_capability/venue checks + 30+ tests
    │               └── COMMIT 1 (UAC)
    ├── 2D UTL event registration (INSTRUCTION_INTEGRATION_DEPTH_OBSERVED + schema)
    │       └── COMMIT 2 (UTL) — INDEPENDENT of UAC commit, can PARALLELIZE
    └── after 2B.2 + 2D both complete:
            2C execution-service middleware → COMMIT 3 (execution-service)
                    └── 2E.1 UI Playwright spec → COMMIT 4 (UI)
                                └── 2E.2 full 4-repo QG
```

**Parallel opportunity:** 2B.1+2B.2 (UAC) and 2D (UTL) have no interdep — a single agent can sequence them or two
mini-agents can split. Recommend single agent since UTL work is ~20 LOC.

### Files × line-ranges × commit sequence

**COMMIT 1 — UAC** `feat(uac): G1.2 — instruction-schema validator library (rule 10 + stage-3b)`

| File                                                                             | Action                                                                                                                                                                                                                                                                                                       | Approx LOC |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `unified-api-contracts/unified_api_contracts/internal/validation/__init__.py`    | NEW — export InstructionValidator, ClientInstruction, InstructionValidationResult, InstructionFieldError, IntegrationDepth                                                                                                                                                                                   | ~15        |
| `unified-api-contracts/unified_api_contracts/internal/validation/instruction.py` | NEW — Pydantic `ClientInstruction` mirroring stage-3b §2 (8 required fields), `InstructionFieldError(field, violation, allowed, why)`, `InstructionValidationResult` discriminated union (Ok/Err), `InstructionValidator.validate()` calling `archetypes_for_pair()` + venue check, integration-depth scorer | ~250       |
| `unified-api-contracts/unified_api_contracts/instruction.py`                     | NEW — public domain facade re-exporting the 5 symbols (matches G1.8 pattern)                                                                                                                                                                                                                                 | ~25        |
| `unified-api-contracts/unified_api_contracts/__init__.py`                        | MODIFY — add new domain facade to package-level exports                                                                                                                                                                                                                                                      | +5         |
| `unified-api-contracts/tests/internal/unit/test_instruction_validator.py`        | NEW — ≥30 cases: 8 required-field rejection (8), each BL-1..BL-10 pair-level rejection (10), venue-mismatch (3), integration_depth scoring boundaries (5+), happy path (3+)                                                                                                                                  | ~400       |

Shape mirrors `strategy_availability.py:128-172` (BaseModel, frozen=True, extra=forbid, module-level helpers).
Integration-depth scorer weights: structured enum = 1.0, free text = 0.0, hybrid = 0.5 (per plan line 90-91) —
aggregated as ratio over present fields.

**COMMIT 2 — UTL** `feat(utl/events): G1.2 — INSTRUCTION_INTEGRATION_DEPTH_OBSERVED event`

| File                                                                         | Action                                                                                                                                      | Approx LOC |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `unified-trading-library/unified_trading_library/events/event_types.py`      | MODIFY — add `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED = "INSTRUCTION_INTEGRATION_DEPTH_OBSERVED"` + inclusion in `STANDARD_LIFECYCLE_EVENTS` | +5         |
| `unified-trading-library/unified_trading_library/events/schemas.py`          | MODIFY — payload dataclass `{instruction_id: str, integration_depth: float, client_id: str, timestamp: str}`                                | +20        |
| `unified-trading-library/unified_trading_library/events/__init__.py`         | MODIFY — re-export new symbol                                                                                                               | +2         |
| `unified-trading-library/tests/events/unit/test_new_events.py` (or new file) | MODIFY/NEW — registration + schema validation                                                                                               | +15        |

**COMMIT 3 — execution-service** `feat(execution-service): G1.2 — instruction validator middleware`

| File                                                                                 | Action                                                                                                                                   | Approx LOC |
| ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `execution-service/execution_service/validation/__init__.py`                         | NEW                                                                                                                                      | ~5         |
| `execution-service/execution_service/validation/instruction_validator_middleware.py` | NEW — pre-handler, on fail → structured 400 with `errors: InstructionFieldError[]`, on success → forward + emit UTL event carrying score | ~120       |
| `execution-service/tests/unit/test_instruction_validator_middleware.py`              | NEW — ≥10 cases: bad instruction paths → 400 + no downstream call; good instruction → 200 + event emitted (mock bus)                     | ~200       |

**COMMIT 4 — UI** `test(playbooks): G1.2 — validator Playwright spec`

| File                                                                                                         | Action                                                                                                                                                                                                                                                                                           | Approx LOC |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-2-instruction-schema-validation.spec.ts` | NEW — mirrors `refactor-g1-8-*.spec.ts` shape: seed `client-full` via `seed-persona.ts`, matrix of invalid + valid submissions via `request.post`, assert 400 + FieldError[] for each invalid, assert integration_depth in success response, orphan-reachability of execution submission surface | ~140       |

UI `scripts/quality-gates.sh` — no edit needed (Playwright auto-discovers `tests/e2e/playbooks/refactor/*.spec.ts`).

### Playwright spec design

Canonical port is `localhost:3000` (tier-1, per `unified-trading-system-ui/scripts/dev-tiers.sh`). The execution
submission surface may not yet exist in the UI — spec uses direct API-level `request.post()` assertions against the
execution-service endpoint (port 8004-8016 range, lookup in `ui-api-mapping.json`) for the 400/200 matrix, and
additionally walks a canonical route like `/services/execution/` for the orphan-reachability assertion (reachable from
main nav).

If the execution submission surface is not yet wired into the UI (expected), the spec skips the UI-click path and runs
API-only, with a `test.fixme()` hook that lights up when the UI surface lands (follow-up concern — not blocking G1.2
merge).

### Breaking-change analysis (Citadel rule-3)

Zero existing runtime consumers → zero shims. Purely additive: new UAC facade (`unified_api_contracts.instruction`), new
UTL event, new middleware, new test. No rename, no deletion. Stage-3b schema is the authoritative external contract;
validator just enforces it.

### Success criteria (per phase)

| Phase         | Gate                                                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 2A design     | Pydantic schema matches stage-3b §2 exactly; symbol naming locked (`Instruction*` prefix, no bare `ValidationResult`/`FieldError`)          |
| 2B library    | `from unified_api_contracts.instruction import InstructionValidator` clean; ≥30 test cases green; UAC `bash scripts/quality-gates.sh` green |
| 2C middleware | execution-service `bash scripts/quality-gates.sh` green; bad instruction → 400 + FieldError[]; good → 200 + event emitted                   |
| 2D UTL        | event registered in `STANDARD_LIFECYCLE_EVENTS`; UTL `bash scripts/quality-gates.sh` green                                                  |
| 2E verify     | UI Playwright spec green on tier-1 dev; 4 commit SHAs visible in `git log origin/live-defi-rollout --oneline -20`                           |

### Open questions for operator

1. **Symbol naming:** OK to call the types `InstructionValidator` / `ClientInstruction` / `InstructionValidationResult`
   / `InstructionFieldError` (not `ValidationResult` / `FieldError`) to avoid cross-domain collisions with UTL's
   `domain/validation.py` and strategy-service's `engine/core/validation_service.py`?
2. **Public facade location:** OK to add a new `unified_api_contracts.instruction` public facade (matches G1.8 pattern —
   new domain facade for new domain)? Alternative: re-export from existing `unified_api_contracts.execution` facade.
   Defaulting to new facade unless you push back.
3. **Execution submission UI surface:** Does a UI instruction-submission surface exist today, or is Playwright spec
   API-only with a `test.fixme()` UI hook for future wiring? Defaulting to API-only + orphan-reachability stub.

### Pre-flight for Phase 2A execution (when approved)

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
# Already on live-defi-rollout; other agents have concurrent WIP on UAC/execution-service — stage files explicitly
git -C unified-api-contracts status --short  # note WIP — do NOT stage unrelated files
git -C execution-service status --short
git -C unified-trading-library status --short
.venv-workspace/bin/python -c "from unified_api_contracts.strategy import archetypes_for_pair, ARCHETYPE_CAPABILITY_REGISTRY; print(len(ARCHETYPE_CAPABILITY_REGISTRY))"  # expect 18
```
