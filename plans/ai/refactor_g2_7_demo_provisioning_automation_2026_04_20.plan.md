---
title: Refactor G2.7 — Demo-provisioning automation
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §2.7
  - refactor_g2_1_org_scoped_jwt_claims_2026_04_20.plan.md
  - refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md
  - refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md
  - plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md (folded)
  - plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md Phase 6 (user-management-ui fold-in — ARCHIVED
    2026-04-20)
# Wave G2-β — sequential after G2-α. Parallel with G2.2, G2.10.
# PATH AMENDMENT 2026-04-22: admin surfaces live at unified-trading-system-ui/app/(ops)/admin/demos/*.
supersedes: [defi_demo_e2e_workflow_2026_03_30.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [defi_demo_e2e_workflow_2026_03_30.plan.md](./defi_demo_e2e_workflow_2026_03_30.plan.md). defi_demo_e2e was folded
> into G2.7 per amendment 2026-04-22 See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Refactor G2.7 — Demo-provisioning automation

## Context

Stage 3E §2.7 ships per-prospect demo credential automation. Today demo credentials are seeded by hand for each
prospect, there is no persona-factory, no automatic expiry, and no per-prospect isolation — two prospects sharing a
persona see each other's session state. This doesn't scale past ~5 concurrent demos.

Target: admin console issues a per-prospect demo credential (1-day TTL) via Firebase Admin SDK. `demo_profile_id` chosen
from a dropdown (DART / IM / Reg Umbrella × flavour). Credentials auto-rotate. Each prospect gets a unique `org_id`
(e.g. `demo-prospect-<uuid>`) so visibility slicing is enforceable per-prospect. Appends to the CRM's `demo_history`
(G2.11).

## Decisions locked with user (2026-04-20)

| Decision                                                              | Chosen                                                                                                   | Source                          |
| --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------- |
| One Firebase user per demo prospect (unique uid)                      | Isolated sessions; rotatable without affecting peers                                                     | Stage 3E §2.7                   |
| 1-day TTL default; admin-extendable                                   | Aligns with sales call cadence; expiry auto-revokes                                                      | Stage 3E §2.7 TTL note          |
| Demo credential carries full G2.1 claim set + `demo_profile_id` claim | Restriction-profile engine (G1.7) consumes `demo_profile_id` + questionnaire → resolves visibility slice | G1.7 + G1.10 + G2.1 composition |
| Per-prospect org_id (`demo-prospect-<uuid>`) — never shared           | Avoids cross-prospect session bleed                                                                      | Stage 3E §2.7                   |
| Credential delivery: email magic-link (not password)                  | Prospect doesn't set up a password; ops-friendly                                                         | Operator 2026-04-20             |

## Cross-references

- **Upstream:** G2.1 (JWT claims), G2.6 (staging Firebase), G1.7 (restriction-profile engine), G1.10 (questionnaire)
- **Wave G2-β peers (parallel):** G2.2, G2.10
- **Downstream:** G2.11 CRM `demo_history` append
- **Folded plan:** `plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md`
- **Codex:** `codex/14-playbooks/demo-ops/` — all demo-ops docs

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.7
2. `plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md`
3. `refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md`
4. `refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.plan.md`
5. `/codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md`
6. `/codex/14-customer-journeys/demo-ops/dart-demo-modes.md`
7. `unified-trading-system-ui/lib/admin/firebase.ts` + `server/admin/firebase-admin.ts` (post-fold)
8. `codex/14-playbooks/demo-ops/upsell-overlay-hierarchy.yaml` (G1.13)

## Out of scope

- Actual demo content (walkthroughs live in pb3a/pb3b/pb3c playbooks)
- Magic-link email template copy (marketing owns)
- Integration with external calendaring (future)
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mock-mode generates demo credentials via `personas.ts` persona-clone; staging generates real Firebase users. Both
resolve via the same UAC `create_demo_credential()` helper — no code-fork.

## Phase breakdown

### Phase A — UAC schema + helper

- [ ] [AGENT] P0. Declare `DemoCredential` dataclass in
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/demo_provisioning.py`:
      `{prospect_id, uid, org_id, demo_profile_id, expires_at, created_at, questionnaire_response_ref}`.
- [ ] [AGENT] P0. Declare `create_demo_credential_request(...) -> DemoCredentialRequest` pure constructor.
- [ ] [AGENT] P0. Declare `resolve_demo_entitlements(credential) -> EntitlementSlice` — composes G1.7 + G1.13
      transforms.

### Phase B — Firebase Admin SDK emission

- [ ] [AGENT] P0. `unified-trading-system-ui/lib/admin/demo-provisioning/issue.ts` — Firebase Admin SDK: creates unique
      user, attaches custom claims (G2.1 shape + `demo_profile_id`), generates magic-link.
- [ ] [AGENT] P0. 1-day TTL enforcement — scheduled Cloud Function deletes expired users.

### Phase C — Admin UI

- [ ] [AGENT] P0. `unified-trading-system-ui/app/(ops)/admin/demos/new/page.tsx` — form: prospect_id dropdown (from CRM
      G2.11), `demo_profile_id` dropdown, flavour dropdown, TTL override.
- [ ] [AGENT] P0. Submit → calls `issue.ts`, shows magic-link + expiry + access QR code.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/(ops)/admin/demos/page.tsx` — list active demos, revoke, extend TTL.

### Phase D — CRM + restriction-profile integration

- [ ] [AGENT] P0. On credential issuance, append to CRM `demo_history` (G2.11 Firestore collection).
- [ ] [AGENT] P0. G1.7 restriction-profile engine reads `demo_profile_id` from JWT claim; applies profile +
      questionnaire overlay + tempt-logic (G1.13) to produce visibility slice.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh` (covers (ops)/admin/demos)
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-7-demo-provisioning.spec.ts` — admin flow: issue credential → sign in as
      prospect → assert visibility slice matches profile+overlay.
- [ ] [AGENT] P0. Smoke: 3 concurrent demo prospects, verify zero cross-session bleed.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/demo_provisioning.py` — NEW
- `unified-api-contracts/tests/internal/unit/test_demo_provisioning.py` — NEW
- `unified-trading-system-ui/lib/admin/demo-provisioning/issue.ts` — NEW
- `unified-trading-system-ui/lib/admin/demo-provisioning/revoke.ts` — NEW
- `unified-trading-system-ui/app/(ops)/admin/demos/page.tsx` — NEW
- `unified-trading-system-ui/app/(ops)/admin/demos/new/page.tsx` — NEW
- `deployment-service/functions/expire_demo_credentials.ts` — NEW (Cloud Function)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-7-demo-provisioning.spec.ts` — NEW

## Execution DAG

```
A (UAC schema) → B (Firebase emission)
                   ↓
                 C (admin UI) + D (CRM + restriction-profile wiring) [parallel]
                   ↓
                 E (QG + Playwright + concurrent smoke)
```

## Verification

1. Demo credential issuance creates unique Firebase user + magic-link.
2. 1-day TTL enforced via Cloud Function.
3. Per-prospect isolation (3 concurrent prospects → 0 bleed).
4. CRM `demo_history` appended on each issuance.
5. G1.7 resolves demo_profile_id + questionnaire to visibility slice.
6. Playwright spec green.
7. QG green on all three repos.

## Handoff

Unblocks:

- **pb3a / pb3b / pb3c** — warm-prospect demos scale past ops-by-hand.
- **G2.11 CRM** — `demo_history` becomes real live data.
- **G3.5 consistency agents** — demo-state monitoring becomes feasible with real data.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (unified-trading-system-ui `(ops)/admin/demos`) through MCP
Playwright tools as admin persona. Issue a demo credential for a test prospect; copy magic-link; open in incognito and
sign in; verify persona-scoped visibility in `localhost:3000`.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-7-demo-provisioning.spec.ts`:

1. Seed admin persona; issue demo credential with `demo_profile_id=im_demo_basic`.
2. Sign in as the new credential (Firebase emulator handles magic-link in CI).
3. Assert visibility slice matches G1.7 resolution of (im_demo_basic + no questionnaire) + G1.13 tempt-logic widening.
4. Issue 3 demo credentials concurrently (different prospects); assert each sees own slice.
5. Revoke credential; assert subsequent sign-in fails.
6. Include orphan-reachability.
7. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.7 (Wave G2-β).**

---

You are executing **Refactor G2.7 — Demo-provisioning automation** for the Unified Trading System at Odum Research. Wave
G2-β; G2.1 + G2.6 + G1.7 + G1.10 must be shipped.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
# user-management-ui archived 2026-04-20.
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
git -C deployment-service checkout live-defi-rollout && git -C deployment-service pull
# Verify G2.1 (JWT claims), G2.6 (staging Firebase), G1.7 (restriction-profile), G1.10 (questionnaire) shipped
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/jwt_claims.py 2>/dev/null || echo "G2.1 NOT SHIPPED"
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py 2>/dev/null || echo "G1.7 NOT SHIPPED"
```

All gates green. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_7_demo_provisioning_automation_2026_04_20.plan.md`

### Read-set (mandatory)

All 8 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 8 files across 4 repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (unified-trading-system-ui) through MCP Playwright tools. Issue demo credential + sign in +
verify visibility slice + concurrent smoke. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-7-demo-provisioning.spec.ts` — full flow + 3
concurrent prospects + revoke, wired into `scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Four repos touched → four commits. `git pull --rebase` before each push.

```
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.7 — DemoCredential schema + resolver" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(admin/demo-provisioning): G2.7 — (ops)/admin/demos issuance UI + magic-link" --agent
cd ../deployment-service && bash scripts/quickmerge.sh "feat(functions): G2.7 — expire_demo_credentials TTL enforcer" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "test(playbooks): G2.7 — demo-provisioning flow + concurrent smoke" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ `DemoCredential` + resolver in UAC.
2. ✅ ≥10 UAC tests green.
3. ✅ Admin issuance + revoke + TTL enforcement all green.
4. ✅ 3-concurrent-prospect smoke: 0 cross-session bleed.
5. ✅ CRM `demo_history` appended.
6. ✅ Playwright spec green.
7. ✅ QG green on 4 repos.
8. ✅ 4 commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT share `org_id` across prospects — unique per credential.
- Do NOT skip TTL expiry — 1-day default is a hard requirement.
- Do NOT bypass G1.7 restriction-profile resolution — credentials flow through the engine.
- Do NOT write magic-link plaintext to Firestore — Firebase Admin SDK handles it.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- DemoCredential schema.
- Issuance + revoke + TTL flow results.
- Concurrent-prospect smoke results.
- CRM append verification.
- Playwright spec pass status.
- QG results (4 repos).
- 4 commit SHAs pushed to live-defi-rollout.
