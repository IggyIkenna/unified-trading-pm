---
title: Refactor G2.11 — Account-intelligence-record CRM base
status: active
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.11
  - plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md Phase 6 (user-management-ui fold-in — ARCHIVED
    2026-04-20)
# Wave G2-α — parallel with G2-α peers 2.1, 2.6, 2.8, 2.9. G2/G3 border — defer if bandwidth tight.
# PATH AMENDMENT 2026-04-22: CRM admin surfaces live at unified-trading-system-ui/app/(ops)/admin/prospects/* + lib/admin/account-intelligence/.
---

# Refactor G2.11 — Account-intelligence-record CRM base

## Context

Stage 3E §2.11 ships a minimal CRM base: one record per prospect tracking questionnaire response, demo history, not-show
deviations, and next playbook. Today this information lives in sales-person heads + ad-hoc Google Docs. Rule 09
`09-internal-commercial-oneliners.md` and rule 06 §Enforcement #5 both reference "account-intelligence record" as if it
exists; this wave stands up the minimum enforceable surface.

Target: Firestore collection `/account_intelligence/{prospect_id}` + admin UI surface at `/admin/prospects/[id]` in
unified-trading-system-ui `(ops)/admin/*` (post user-management-ui fold 2026-04-20). Questionnaire response (G1.10)
auto-populates the record at submission; demo-provisioning (G2.7) appends to demo_history; sales team edits
not_show_deviations + next_playbook manually.

Priority P1 (not P0) because the CRM is nice-to-have; G1.10 questionnaire already captures the foundation via the
`/questionnaires` Firestore collection. This plan formalises the CRM layer on top.

## Decisions locked with user (2026-04-20)

| Decision                                                                           | Chosen                                                          | Source                             |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------------------------- |
| Firestore backend (not a separate DB)                                              | "Firebase IS the API" per Wave E closure memory                 | Operator 2026-04-20                |
| Minimal schema — 8 fields, no workflow engine                                      | Can expand once real usage tells us what sales needs            | Stage 3E §2.11 "Minimal CRM table" |
| Admin UI lives in unified-trading-system-ui `(ops)/admin/*` (post-fold 2026-04-20) | Prospect data is internal; no public surface                    | Rule 06 + fold memo 2026-04-20     |
| P1 priority — G2/G3 border                                                         | Explicit in Stage 3E §2.11 — can slide to G3 if bandwidth tight | Stage 3E §2.11                     |

## Cross-references

- **Wave G2-α peers:** G2.1, G2.6, G2.8, G2.9
- **Wave G2-β inputs:** G2.7 demo-provisioning (appends to `demo_history`)
- **G1 inputs:** G1.10 questionnaire (seeds record on submission)
- **Codex:** `/codex/14-playbooks/demo-ops/account-intelligence-record.md`,
  `/codex/14-playbooks/_ssot-rules/09-internal-commercial-oneliners.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.11
2. `/codex/14-playbooks/demo-ops/account-intelligence-record.md`
3. `/codex/14-playbooks/_ssot-rules/09-internal-commercial-oneliners.md`
4. `/codex/14-playbooks/_ssot-rules/06-show-dont-show-discipline.md` — §Enforcement #5
5. `unified-trading-system-ui/app/(ops)/admin/questionnaires/page.tsx` — G1.10 admin playback pattern
6. `unified-trading-system-ui/lib/admin/firebase.ts`

## Out of scope

- Full workflow engine (next-action scheduling, email reminders, calendar integration)
- Integration with external CRMs (Salesforce, HubSpot)
- Surfacing prospect data to unified-trading-system-ui (internal-only)
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Schema + Firestore rules

- [ ] [AGENT] P0. Declare TypeScript interface `unified-trading-system-ui/lib/admin/account-intelligence/types.ts`:
      `{prospect_id, org_id, commercial_path, resolved_cell, demo_history[], not_show_deviations[], upcoming_actions[], next_playbook}`.
- [ ] [AGENT] P0. Firestore security rules update at `deployment-service/firestore/staging/firestore.rules`: admin-only
      read/write on `/account_intelligence/**`.

### Phase B — Firestore writer + reader

- [ ] [AGENT] P0. `unified-trading-system-ui/lib/admin/account-intelligence/firestore.ts` — `getRecord(prospect_id)`,
      `createRecord(record)`, `appendDemoHistory(prospect_id, entry)`, `updateNotShowDeviations(prospect_id, list)`,
      `updateNextPlaybook(prospect_id, playbook_id)`.
- [ ] [AGENT] P0. Hook `useAccountIntelligence(prospect_id)` for React components.
- [ ] [AGENT] P0. G1.10 questionnaire-submit handler seeds the CRM record on first submission.

### Phase C — Admin UI

- [ ] [AGENT] P0. `unified-trading-system-ui/app/(ops)/admin/prospects/page.tsx` — list view, filterable by
      commercial_path.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/(ops)/admin/prospects/[id]/page.tsx` — detail view + edit UI for
      not_show_deviations + next_playbook.
- [ ] [AGENT] P0. Admin navigation link added to unified-trading-system-ui `(ops)/admin/*` shell.

### Phase D — QG + verification

- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh` (covers (ops)/admin/prospects)
- [ ] [SCRIPT] P0. `cd deployment-service && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-11-crm.spec.ts` — admin persona, CRUD record, assert Firestore.
- [ ] [AGENT] P0. Manual smoke: submit questionnaire as prospect → verify CRM record auto-created.

## Critical files to be modified

- `unified-trading-system-ui/lib/admin/account-intelligence/types.ts` — NEW
- `unified-trading-system-ui/lib/admin/account-intelligence/firestore.ts` — NEW
- `unified-trading-system-ui/lib/admin/account-intelligence/hooks.ts` — NEW (useAccountIntelligence)
- `unified-trading-system-ui/app/(ops)/admin/prospects/page.tsx` — NEW
- `unified-trading-system-ui/app/(ops)/admin/prospects/[id]/page.tsx` — NEW
- `unified-trading-system-ui/app/(public)/questionnaire/submit-handler.ts` (or equivalent) — MODIFY
- `deployment-service/firestore/staging/firestore.rules` — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-11-crm.spec.ts` — NEW (tests submit flow;
  assertion happens against Firestore state)

## Execution DAG

```
A (schema + rules) → B (writer + reader + questionnaire hook)
                        ↓
                      C (admin UI)
                        ↓
                      D (QG + Playwright)
```

## Verification

1. CRM schema declared + Firestore rules restrict read/write to admin.
2. Questionnaire submission auto-creates CRM record.
3. Admin list + detail views render + edit flow works.
4. Playwright spec green.
5. QG green on unified-trading-system-ui + deployment-service.

## Handoff

Unblocks:

- **G2.7** — demo-provisioning appends to `demo_history`.
- **Future operator workflow** — sales team can track follow-ups without leaving the admin surface.
- **Rule 06 §Enforcement #5** — the "account-intelligence record" reference becomes grounded.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (unified-trading-system-ui `(ops)/admin/prospects`) through MCP
Playwright tools as admin persona. Submit a questionnaire in a separate tab at `localhost:3000` as a prospect; verify
the admin UI surfaces the new CRM record.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-11-crm.spec.ts`:

1. Seed prospect persona; submit questionnaire.
2. Switch to admin persona; navigate to `/admin/prospects/[id]`.
3. Assert CRM record rendered with fields populated from questionnaire.
4. Edit `next_playbook`; assert Firestore round-trip.
5. Include orphan-reachability assertion.
6. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.11 (Wave G2-α, P1).**

---

You are executing **Refactor G2.11 — Account-intelligence-record CRM base** for the Unified Trading System at Odum
Research. Wave G2-α, priority P1. Deferrable if bandwidth tight.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
# user-management-ui archived 2026-04-20; admin surfaces under unified-trading-system-ui/(ops)/admin.
git -C deployment-service checkout live-defi-rollout && git -C deployment-service pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls unified-trading-system-ui/lib/admin/firebase.ts
ls unified-trading-system-ui/app/\(ops\)/admin/questionnaires/page.tsx  # G1.10 pattern post-fold
ls /codex/14-playbooks/demo-ops/account-intelligence-record.md
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through D of this plan:
`plans/active/refactor_g2_11_account_intelligence_record_crm_2026_04_20.plan.md`

### Read-set (mandatory)

All 6 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 8 files across 3 repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (unified-trading-system-ui) through MCP Playwright tools. Submit questionnaire as prospect at
:3000; verify admin CRM record renders at :3001. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-11-crm.spec.ts` — seeded personas, CRUD flow
asserted, wired into `scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Three repos touched → three commits. `git pull --rebase` before each push.

```
cd deployment-service && bash scripts/quickmerge.sh "feat(firestore): G2.11 — account_intelligence collection rules" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(admin/crm): G2.11 — account-intelligence-record base + (ops)/admin/prospects UI + CRM submission spec" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ CRM schema declared; Firestore rules admin-only.
2. ✅ Questionnaire submit auto-creates CRM record.
3. ✅ Admin list + detail render + edit works.
4. ✅ Playwright spec green.
5. ✅ QG green on deployment-service + unified-trading-system-ui (user-management-ui archived).
6. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT expose CRM data in unified-trading-system-ui (internal-only).
- Do NOT build a workflow engine (email reminders, calendar sync) — out-of-scope.
- Do NOT integrate with Salesforce/HubSpot — out-of-scope.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- CRM schema field list.
- Firestore rule diff.
- Playwright spec pass status.
- QG results (3 repos).
- 3 commit SHAs pushed to live-defi-rollout.
