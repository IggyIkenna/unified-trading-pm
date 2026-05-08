---
title: Firestore security rules for G1.10 questionnaires collection (follow-up)
status: active
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - plans/active/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md (§Deviations)
  - refactor_g2_6_staging_firebase_provisioning_2026_04_20.md
  - plans/active/ui_unification_v2_sanitisation_2026_04_20.md Phase 6 (user-management-ui fold-in)
---

# Firestore security rules for G1.10 questionnaires collection

## Context

G1.10 shipped the prospect-facing questionnaire at `/questionnaire` with Firestore write to `/questionnaires/{id}` as
the canonical submit path (localStorage is the fallback for anonymous / unauthenticated flows). G1.10's §Deviations
flagged Firestore security rules as a deployment-service follow-up. Today the write path either succeeds against
default-permissive rules (dev) or has no rules deployed yet (staging pending G2.6). That's acceptable for dev but not
for staging / prod.

This plan fills in the 3 required rules. Rides on G2.6 staging Firebase provisioning.

## Decisions locked with user (2026-04-20)

| Decision                                                  | Chosen                                                                              | Source                 |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------- |
| 3 rules required: anonymous write, admin read, rate-limit | Minimum enforceable surface                                                         | G1.10 plan §Deviations |
| Rate-limit: 5 writes per IP per hour                      | Prevents abuse but allows legitimate prospect submissions (typical 1-2 per session) | Operator 2026-04-20    |
| Rules live in deployment-service (not a UI repo)          | Deployment-service owns Firestore rule deployment per G2.6                          | G2.6 plan              |
| P1 priority (not blocking G2)                             | Dev works without them; staging needs them for safe exposure                        | G1.10 plan note        |

## Cross-references

- **Parent:** `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md` §Deviations
- **Prereq:** `refactor_g2_6_staging_firebase_provisioning_2026_04_20.md` (rule deploy infra)
- **Codex:** `codex/14-playbooks/authentication/` auth playbook docs

## Mandatory read-set

1. `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md` — §Deviations
2. `refactor_g2_6_staging_firebase_provisioning_2026_04_20.md` — Firestore rules phase
3. `unified-trading-system-ui/lib/admin/firebase.ts` — Firestore client pattern

## Out of scope

- Other Firestore collections (handled in their own rule sets)
- Firebase Auth rules (separate)
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Rule file

- [ ] [AGENT] P0. Extend `deployment-service/firestore/staging/firestore.rules` (shipped by G2.6):

  ```javascript
  match /questionnaires/{id} {
    // Rule 1: anonymous clients CAN write their own questionnaire.
    allow create: if request.resource.data.keys().hasAll(
      ['categories','instrument_types','venue_scope','strategy_style','service_family','fund_structure']
    )
      && request.resource.data.size() <= 8;

    // Rule 2: admin-role required for reads + updates.
    allow read, update, delete: if request.auth != null
      && request.auth.token.audience == 'admin';

    // Rule 3: rate limit — 5 writes per IP per hour via Cloud Function counter.
    // (Firestore rules alone can't rate-limit by IP; see Phase B.)
  }
  ```

### Phase B — Rate-limit Cloud Function

- [ ] [AGENT] P0. `deployment-service/functions/questionnaire_rate_limit.ts` — Firestore `onCreate` trigger; increments
      `/ip_counters/{ip_hash}/questionnaire/{hour}`; if > 5, deletes the just-written document and logs.

### Phase C — Unit tests

- [ ] [AGENT] P0. `deployment-service/tests/firestore_rules/test_questionnaires.py` (or equivalent via Firebase emulator
      runtime) — ≥8 cases: allowed anonymous create with all axes, rejected missing axis, rejected extra fields, admin
      read allow, non-admin read deny, rate-limit trigger (6th write rejected), admin delete allow, anonymous delete
      deny.

### Phase D — Deploy + smoke

- [ ] [AGENT] P0. Deploy to staging via G2.6's deploy script.
- [ ] [AGENT] P0. Playwright spec in UI: submit 6 questionnaires in rapid succession; assert 6th is rate-limited.
- [ ] [SCRIPT] P0. `cd deployment-service && bash scripts/quality-gates.sh`

## Critical files to be modified

- `deployment-service/firestore/staging/firestore.rules` — MODIFY (extend)
- `deployment-service/functions/questionnaire_rate_limit.ts` — NEW
- `deployment-service/tests/firestore_rules/test_questionnaires.py` — NEW
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/firestore-rules-questionnaires.spec.ts` — NEW

## Execution DAG

```
A (rules) → B (rate-limit fn)
              ↓
            C (emulator tests) + D (deploy + smoke) [parallel after B]
```

## Verification

1. Rules deployed to staging.
2. ≥8 emulator tests green.
3. Rate-limit Cloud Function triggers on 6th write within hour.
4. Playwright smoke: 6th submission rejected in staging.
5. deployment-service QG green.

## Handoff

Unblocks:

- **G1.10 §Deviations closeout** — Firestore security rules line item.
- **Staging / prod safe exposure** of the `/questionnaire` route.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools; submit 6 questionnaires in rapid
succession against the Firebase emulator; assert 6th rejected.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/firestore-rules-questionnaires.spec.ts`:

1. Submit 5 valid questionnaires from same session.
2. Submit 6th; assert rate-limit rejection.
3. Admin persona reads `/questionnaires` list; assert success.
4. Non-admin persona attempts read; assert 403.
5. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute the Firestore rules follow-up.**

---

You are executing the **Firestore security rules for G1.10 questionnaires** follow-up for the Unified Trading System at
Odum Research. P1; G2.6 staging Firebase provisioning must be shipped.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C deployment-service checkout live-defi-rollout && git -C deployment-service pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls deployment-service/firestore/staging/firestore.rules 2>/dev/null || echo "G2.6 NOT SHIPPED"
```

All must exist. STOP if missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute Phases A through D of this plan: `plans/active/firestore_security_rules_for_questionnaires_2026_04_21.md`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools against the Firebase emulator. Submit 6 questionnaires; assert
rate-limit rejection. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/firestore-rules-questionnaires.spec.ts`, wired into
`scripts/quality-gates.sh`.

### Commit strategy

Two repos → two commits.

```
cd deployment-service && bash scripts/quickmerge.sh "feat(firestore): questionnaires collection security rules + rate-limit fn" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "test(e2e): firestore-rules questionnaires smoke" --agent
```

### Success criteria

1. ✅ 3 rules deployed.
2. ✅ Rate-limit Cloud Function live.
3. ✅ ≥8 emulator tests green.
4. ✅ Playwright smoke green.
5. ✅ deployment-service QG green.
6. ✅ 2 commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT relax rate-limit beyond 5/hour without operator sign-off.
- Do NOT make `/questionnaires` readable to non-admin audiences — prospect data is internal.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Rule diff.
- Rate-limit function deployment URL.
- Emulator test count + pass rate.
- Playwright smoke result.
- 2 commit SHAs pushed to live-defi-rollout.
