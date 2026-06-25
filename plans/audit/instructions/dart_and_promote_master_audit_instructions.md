---
doc_type: audit-instruction
title: dart_and_promote_master_audit_instructions
summary:
status:
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-22"
tier: L3
parent_epic:
cadence:
verifier:
lifespan:
type: audit-instructions
epic: dart_and_promote_master
assigned_vm: vm-operator-ops
last_updated: 2026-05-22
---

# DART + Promote Master — Audit Instructions

## Epic Scope

DART (Deal Allocation and Review Tool), ManualTradeGateDialog (first 3 trading days), promote workflow
(`POST /api/promote/{strategy_id}/{manifest_id}`), `MinimalCandidateManifest` in Firestore, promote state machine.
May-23 valid promote path: `paper_1d` → `live_early` only. `live_full` is post-cutover.

Codex SSOTs: `codex/04-architecture/promote-workflow-architecture.md`,
`codex/09-strategy/operational/cli-promote-paths.md`

## Triggers

- Weekly (minimum cadence)
- Before any promote workflow change
- After May-23 cutover (scope expands to `live_full`)
- When Firebase enforcement layer changes

## Checklist

- [ ] (a) **Promote endpoint scope**: `POST /api/promote/{strategy_id}/{manifest_id}` only accepts
      `paper_1d → live_early` promote target before May-23 cutover. `live_full` rejected with 422. Read: promote
      endpoint implementation — verify target validation

- [ ] (b) **MinimalCandidateManifest not enriched**: `MinimalCandidateManifest` does NOT carry pinned shas, model refs,
      or features manifest version before cutover (those are post-cutover scope). Grep:
      `rg "MinimalCandidateManifest" --include="*.py"` — verify no extra fields beyond minimal set

- [ ] (c) **ManualTradeGateDialog fires for 3 days**: DART dialog is triggered for first 3 trading days of a live
      strategy; auto-dismissed after day 3. Read: DART dialog logic — verify countdown mechanism

- [ ] (d) **Firebase execution-full at UI layer only**: backend Firebase integration is post-cutover. UI layer enforces
      `execution-full` before May-23. Read: promote workflow codex — verify this is documented; grep for Firebase
      imports in backend code

- [ ] (e) **State machine covers all transitions**: all valid transitions defined and invalid ones rejected. Find:
      `rg "StateMachine\|transition\|promote_state" --include="*.py" -l` — read transitions list Verify: invalid
      transitions raise appropriate error

- [ ] (f) **Promote workflow codex alignment**: `codex/04-architecture/promote-workflow-architecture.md` matches current
      code. No code patterns present that contradict the codex doc. Read: both codex doc and implementation — spot-check
      3 key code paths

### E2E Flow Verification

- (e2e-promote) **Promote flow audit**: run a paper-to-live promote end-to-end (paper_1d → live_early) using a test
  strategy. Confirm ManualTradeGateDialog fires. If promote can't run against prod, verify the code path with a dry-run
  or staging environment.
- (mock-upstream) **Staging-only audit**: deployment and promote workflows MUST be auditable on staging without
  affecting prod. Document the staging invocation.

## Success Criteria

- All 6 checklist items GREEN
- Promote smoke test: paper strategy → promote → paper_1d → live_early succeeds end-to-end
- deployment-api + deployment-ui QG exits 0

## Output Format

Result file at `plans/audit/results/dart_and_promote_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
