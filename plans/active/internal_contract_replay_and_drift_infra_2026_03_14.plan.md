---
name: internal-contract-replay-and-drift-infra-2026-03-14
overview: >
  Citadel-grade internal/external contract assurance rollout. Establishes strict ownership boundaries across existing
  plans, separates UAC (external) from UIC (internal), adds deterministic replay gates, live SIT compatibility checks,
  and scheduled drift recording with approval-only promotion.
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C1
    deployment: D1
    business: none
    readiness_note: "Reusable workflows + rollout orchestration are scaffolded, not fully propagated."
  - repo: system-integration-tests
    code: C0
    deployment: D1
    business: none
    readiness_note: "Internal replay/live split not yet formalized."
  - repo: unified-api-contracts
    code: C1
    deployment: none
    business: none
    readiness_note: "External VCR registry exists; internal entries must be decoupled."
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
    readiness_note: "Internal endpoint contract registry module not yet created."
  - repo: alerting-service
    code: C2
    deployment: D1
    business: none
    readiness_note: "Can consume drift/replay signals once standardized events are emitted."
  - repo: logs-dashboard-ui
    code: C2
    deployment: D1
    business: none
    readiness_note: "Can display lane health after API additions."

depends_on:
  - cicd_code_rollout_master_2026_03_13
  - cicd_e2e_testing_master_2026_03_13
  - integration_tests_codex_compliance_8357b7b7
  - sit_build_source_ci_rollout_1dd6b9d4
  - uac_canonical_normalization_master_7b288edc
  - defi_keys_data_integration_2026_03_13
  - ui_api_alerting_observability_2026_03_14

supersedes: []

todos:
  # ── R0: GOVERNANCE ALIGNMENT ─────────────────────────────────────────────────

  - id: r0-governance-alignment
    content: >
      - [ ] [AGENT] Insert ownership-boundary clauses into the 7 dependent plans exactly as defined in plan_updates.
      Each plan must explicitly declare "owns" and "does_not_own" to prevent overlap.
    status: todo

  - id: r1-add-blocked-by-links
    content: >
      - [ ] [AGENT] Add blocked_by references to overlapping todos in all 7 plans: e2e/sit tasks blocked_by
      cicd_code_rollout; observability lane dashboards blocked_by integration_tests_codex; nightly drift scheduling
      blocked_by sit_build_source_ci_rollout.
    status: todo
    blocked_by: cicd_code_rollout_master_2026_03_13

  # ── R2–R3: UAC/UIC BOUNDARY ──────────────────────────────────────────────────

  - id: r2-uic-internal-registry
    content: >
      - [ ] [AGENT] Create internal endpoint contract registry in UIC (new module under
      unified_internal_contracts/testing/). Define endpoint metadata for replay/record and bind each endpoint to UIC
      schema class names.
    status: todo

  - id: r3-uac-boundary-cleanup
    content: >
      - [ ] [AGENT] Remove internal endpoint ownership from UAC VCR registry and document external-only boundary. Keep
      UAC focused on external provider contracts and normalization outputs.
    status: todo
    blocked_by: r2-uic-internal-registry

  # ── R4–R6: REPLAY, SIT, DRIFT WORKFLOWS ───────────────────────────────────────

  - id: r4-replay-workflow-pr-gate
    content: >
      - [ ] [AGENT] Implement PM reusable replay workflow for deterministic PR checks: external replay validates against
      UAC schemas; internal replay validates against UIC schemas; fail hard on schema mismatch/version mismatch.
    status: todo
    blocked_by: r3-uac-boundary-cleanup

  - id: r5-live-sit-compat-gate
    content: >
      - [ ] [AGENT] Implement SIT live compatibility checks for internal producer/consumer behavior. Keep separate from
      replay and smoke; this is runtime truth.
    status: todo
    blocked_by: integration_tests_codex_compliance_8357b7b7

  - id: r6-nightly-drift-recording
    content: >
      - [ ] [AGENT] Add scheduled/manual drift recording workflow: records from staging only; creates PR with
      cassette/schema diff summary; labels schema-impact and requires manual approval; never auto-merges
      schema-affecting updates.
    status: todo
    blocked_by: sit_build_source_ci_rollout_1dd6b9d4

  # ── R7–R8: SECRETS & OBSERVABILITY ───────────────────────────────────────────

  - id: r7-secrets-hardening-for-recorders
    content: >
      - [ ] [AGENT] Apply least-privilege secrets model for recorder jobs and audit all secret accesses. Ensure PR
      workflows do not expose production recorder credentials.
    status: todo
    blocked_by: defi_keys_data_integration_2026_03_13

  - id: r8-observability-lane-metrics
    content: >
      - [ ] [AGENT] Emit standardized events/metrics for each lane (smoke, replay, live, drift). Wire alerts and
      dashboard visibility for regressions and stale drift jobs.
    status: todo
    blocked_by: ui_api_alerting_observability_2026_03_14

  # ── R9–R10: ROLLOUT & READINESS ──────────────────────────────────────────────

  - id: r9-rollout-and-adoption
    content: >
      - [ ] [AGENT] Roll out reusable workflows and test matrix to all in-scope repos via PM propagation scripts. Verify
      no per-repo CI logic drift from PM SSOT.
    status: todo
    blocked_by: r4-replay-workflow-pr-gate

  - id: r10-readiness-verification
    content: >
      - [ ] [AGENT] Drive readiness to C5/D3: C5 quickmerge complete for all touched repos; D3 staging SIT with
      replay+live lanes green, nightly drift run validated.
    status: todo
    blocked_by: r5-live-sit-compat-gate

isProject: false
---

# Internal Contract Replay and Drift Infrastructure

Citadel-grade internal/external contract assurance rollout. Establishes strict ownership boundaries across existing
plans, separates UAC (external) from UIC (internal), adds deterministic replay gates, live SIT compatibility checks, and
scheduled drift recording with approval-only promotion.

---

## Design Principles

- **Schema authority:** UAC = external, UIC = internal.
- **Replay gate** is deterministic and fast; **SIT gate** is live and behavioral.
- **Drift recording** is scheduled/manual only; never auto-promote schema-impacting diffs.
- **Single owner per concern:** infra, tests, schemas, secrets, observability.

---

## Plan Updates (Owner Boundaries)

| Plan                              | Owns                                                           | Does Not Own                         |
| --------------------------------- | -------------------------------------------------------------- | ------------------------------------ |
| **cicd_code_rollout_master**      | Reusable workflow infra for replay/record; rollout propagation | Endpoint semantics; schema ownership |
| **cicd_e2e_testing_master**       | Live smoke and E2E/SIT behavioral validation                   | Cassette recording mechanics         |
| **integration_tests_codex**       | Contract test matrix and compliance checks                     | —                                    |
| **sit_build_source_ci_rollout**   | SIT scheduling/build source orchestration                      | —                                    |
| **uac_canonical_normalization**   | External canonical normalization; provider schema governance   | Internal endpoint contract registry  |
| **defi_keys_data_integration**    | Secret scope and key lifecycle for recorder jobs               | —                                    |
| **ui_api_alerting_observability** | Operational visibility and alerting for contract lanes         | —                                    |

---

## Required Edits by Plan

### cicd_code_rollout_master_2026_03_13

- Add reusable workflow: `contract-replay.yml` (PR gate)
- Add reusable workflow: `contract-drift-record.yml` (nightly/manual)
- Policy: record jobs cannot run on untrusted PR contexts
- Policy: drift PRs require manual approval when schema-affecting

### cicd_e2e_testing_master_2026_03_13

- Split smoke vs replay vs SIT into separate jobs and pass/fail criteria
- Consume replay artifacts/results; do not duplicate replay implementation

### integration_tests_codex_compliance_8357b7b7

- Add matrix: external replay→UAC schema, internal replay→UIC schema, live SIT compatibility
- Guard: internal endpoint definitions forbidden in UAC external config
- Guard: internal contract schema imports must resolve from UIC

### sit_build_source_ci_rollout_1dd6b9d4

- Trigger nightly drift recording after staging readiness checks
- Publish run metadata + diff summary artifact

### uac_canonical_normalization_master_7b288edc

- Declare internal VCR endpoint ownership out-of-scope
- Migrate/remove internal endpoint cassette definitions from UAC-owned registry

### defi_keys_data_integration_2026_03_13

- Least-privilege credentials for scheduled recording workflows
- Rotation/audit requirements for recorder identities

### ui_api_alerting_observability_2026_03_14

- Add dashboard panels for smoke/replay/live/drift lanes
- Add alert severity policy for schema drift regressions

---

## Dependency Chain

```
r0 (governance) → r1 (blocked_by links)
r2 (UIC registry) → r3 (UAC cleanup) → r4 (replay workflow) → r9 (rollout)
r5 (live SIT) → r10 (readiness)
r6 (drift recording) — blocked by sit_build_source
r7 (secrets) — blocked by defi_keys
r8 (observability) — blocked by ui_api_alerting
```
