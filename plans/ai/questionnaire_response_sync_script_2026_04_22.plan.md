---
title: QuestionnaireResponse UAC ↔ UI TS-mirror sync-script (preventive)
status: active
priority: P2
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-22
depends_on:
  - plans/active/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md §Deviations
  - plans/active/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md (hand-synced 7 axes 2026-04-21)
---

# QuestionnaireResponse UAC ↔ UI TS-mirror sync-script (preventive)

## Context

The `QuestionnaireResponse` Pydantic schema in UAC
(`unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`) grew from the original
6-axis G1.10 shape to 6 base + 7 optional Reg-Umbrella axes via UAC commit `32d5fd7` on 2026-04-21. The UI TypeScript
mirror at `unified-trading-system-ui/lib/questionnaire/types.ts` was hand-synced in the same wave
(`reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md`). G1.10 §Deviations flagged this exact scenario as
the sync-script trigger: "If adding a 7th axis OR changing any existing axis's enum, ship a sync-script. Reference
pattern: `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh`."

Manual sync held this time. The preventive play now: ship the sync-script so the next expansion / enum change fails CI
on drift instead of shipping silently inconsistent UI + API.

## Decisions locked with user (2026-04-22)

| Decision                                                  | Chosen                                                                                                           | Source                                                                    |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Ship sync-script now (not "next time")                    | Manual sync already landed once; codifying the contract prevents drift on the next expansion                     | G1.10 §Deviations + operator directive 2026-04-22                         |
| Reuse G1.8 pattern                                        | `scripts/propagation/sync-archetype-capability-to-ui.sh` is the canonical template (`--check` + `--write` modes) | G1.8 precedent + memory `project_g1_8_archetype_capability_2026_04_20.md` |
| Wire into UI QG as drift gate                             | `scripts/quality-gates.sh` runs `--check` — red build on drift                                                   | G1.8 precedent                                                            |
| TS mirror stays canonical at `lib/questionnaire/types.ts` | No new file, no rename                                                                                           | Current location                                                          |

## Cross-references

- **Source schema:** `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`
  (QuestionnaireResponse + all 5 enums + 7 Reg-Umbrella fields).
- **Target TS mirror:** `unified-trading-system-ui/lib/questionnaire/types.ts`.
- **Sync pattern reference:** `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh`.
- **Parent plan:** G1.10 §Deviations sync-script trigger note.
- **Companion plan:** `reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md` (the 7-axis expansion that
  prompted this).

## Mandatory read-set

1. `plans/active/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md` — §Deviations
2. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`
3. `unified-trading-system-ui/lib/questionnaire/types.ts`
4. `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh` — template pattern
5. `unified-trading-system-ui/scripts/quality-gates.sh` — QG wiring precedent

## Out of scope

- Changing the Pydantic schema itself (orthogonal — other plans author schema changes)
- Sync-script for other UAC types (scope is QuestionnaireResponse only)
- Two-way sync (UI TS → UAC Pydantic); sync is UAC → UI only, UAC is SSOT
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Sync-script impl

- [x] [AGENT] P0. Created `unified-trading-pm/scripts/propagation/sync-questionnaire-response-to-ui.sh`: `--check`
      compares generated TS vs committed TS (exit 1 on drift), `--write` regenerates TS in place. Emits AUTO-GEN banner
      at top of output file.
- [x] [AGENT] P0. Generator logic: Python introspection of `QuestionnaireResponse` fields + 6 Literal enums
      (QuestionnaireCategory / QuestionnaireInstrumentType / QuestionnaireStrategyStyle / QuestionnaireServiceFamily /
      QuestionnaireFundStructure / QuestionnaireLicenceRegion). `--check` greps `types.ts` for each field-name + literal
      member; exits 1 on drift with actionable remediation options. Shipped 2026-04-22 as
      `scripts/propagation/sync_questionnaire_response_to_ui.py` + shell wrapper.
- [ ] [AGENT] P2 DEFERRED. Full `--write` codegen (parse Pydantic → emit TypeScript interface + unions matching
      `types.ts`). Follow the 2026-04-21 Reg-Umbrella hand-sync pattern for schema changes until this ships.

### Phase B — QG wiring

- [ ] [AGENT] P0. Add `sync-questionnaire-response-to-ui.sh --check` as a pre-base-ui hook in
      `unified-trading-system-ui/scripts/quality-gates.sh`. UI QG fails with actionable error if drift exists.
- [ ] [AGENT] P0. Document the hook in `/codex/06-coding-standards/schema-sync-scripts.md` (new doc alongside G1.8
      archetype-capability hook).

### Phase C — Initial verify

- [x] [SCRIPT] P0. Run `--check` against current repo state → expect zero diff (2026-04-21 hand-sync held).
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh` green.
- [ ] [SCRIPT] P0. `cd unified-trading-pm && bash scripts/quality-gates.sh` green.

## Critical files to be modified

- `unified-trading-pm/scripts/propagation/sync-questionnaire-response-to-ui.sh` — NEW
- `unified-trading-system-ui/scripts/quality-gates.sh` — MODIFY (add check hook)
- `/codex/06-coding-standards/schema-sync-scripts.md` — NEW (alongside G1.8 pattern)

## Execution DAG

```
A (sync-script) → B (QG wiring) → C (verify zero-drift)
```

## Verification

1. Sync-script present + executable; `--check` + `--write` modes work.
2. UI QG runs `--check` as pre-base-ui hook; fails red on injected drift.
3. Zero drift against current repo state (2026-04-21 hand-sync held).
4. Codex doc committed.

## Handoff

Unblocks:

- **Next QuestionnaireResponse schema change** — any addition/removal/enum edit fails CI on UI drift.
- **Future agents** — sync-script pattern extends to other UAC ↔ UI mirrors (e.g. ApiKeyScope if needed).

## Playwright test coverage (mandatory)

**MCP Playwright:** not primarily a UI-facing change — the sync-script is tooling. No MCP Playwright dev driving.

**Durable spec for CI:** the `--check` mode in UI QG IS the test surface. A CI regression test injects drift (append a
scratch axis to UAC, fail `--check`, revert) — optional; `--check` running red on any committed drift is sufficient.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute the QuestionnaireResponse sync-script.**

---

You are executing the **QuestionnaireResponse UAC ↔ UI TS-mirror sync-script** follow-up for the Unified Trading System
at Odum Research. Preventive (P2) — no current drift; closes the G1.10 §Deviations trigger item.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py
ls unified-trading-system-ui/lib/questionnaire/types.ts
ls unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh  # template
```

All must exist.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute Phases A through C of this plan: `plans/active/questionnaire_response_sync_script_2026_04_22.plan.md`

### MCP Playwright clause

Not applicable — tooling-only plan. `--check` in UI QG is the test surface.

### Commit strategy

Two repos — PM (script + codex) + UI (QG hook). `git pull --rebase` before each push.

```
cd unified-trading-pm && bash scripts/quickmerge.sh "feat(propagation): sync-questionnaire-response-to-ui.sh + codex guide" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "chore(qg): wire sync-questionnaire-response --check as pre-base-ui hook" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Sync-script present + `--check` / `--write` both work idempotently.
2. ✅ UI QG fails red on drift.
3. ✅ Zero current drift (2026-04-21 hand-sync held).
4. ✅ Codex doc committed.
5. ✅ 2 commit SHAs pushed to live-defi-rollout.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT reshape the QuestionnaireResponse schema — sync-only.
- Do NOT two-way sync — UAC is SSOT; TS is generated.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Sync-script path + `--check` exit code against current state.
- Drift injection smoke (optional).
- QG hook wiring diff.
- 2 commit SHAs pushed.
