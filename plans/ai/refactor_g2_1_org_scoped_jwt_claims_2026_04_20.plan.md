---
title: Refactor G2.1 — Org-scoped JWT claims
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.1
  - refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md
  - plans/active/user_management_merge_2026_03_23.plan.md (folded)
  - plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md Phase 6 (user-management-ui fold-in — ARCHIVED
    2026-04-20)
# Wave G2-α — parallel with G2-α peers 2.6, 2.8, 2.9, 2.11. Downstream Wave G2-β: 2.2, 2.7, 2.10.
# PATH AMENDMENT 2026-04-22: user-management-ui archived; admin surfaces now live at
#   unified-trading-system-ui/app/(ops)/admin/* + lib/admin/* + server/admin/*.
supersedes: [user_management_merge_2026_03_23.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [user_management_merge_2026_03_23.plan.md](./user_management_merge_2026_03_23.plan.md). user_management_merge folded
> into G2.1 (and consumers via UTSU (ops)/admin/\*) See `_reconciliation_evidence_map_2026_04_25.md` for evidence
> anchors.

# Refactor G2.1 — Org-scoped JWT claims

## Context

Stage 3E §2.1 ships org/business-unit scoped JWT claims. Today Firebase ID tokens carry `uid`, `email`,
`email_verified`, and generic Firebase custom claims. No `org_id`, `business_unit_id`, `service_family`, `audience`,
`fund_id`, `client_id`, or `api_key_scopes` fields. Persona metadata lives client-side only in
[`lib/auth/personas.ts`](../../../unified-trading-system-ui/lib/auth/personas.ts), which means `access_control()` (G1.6)
cannot trust the token; every call-site performs a client-side persona lookup that is not verifiable server-side.

Target: Firebase custom claims emit the full audience context at provisioning time; every backend service derives its
`UserContext` from decoded claims verbatim; persona lookup is retired for authenticated flows (mock-auth-only dev keeps
the lookup for localhost).

## Decisions locked with user (2026-04-20)

| Decision                                                                                                    | Chosen                                                                                                                                                                            | Source                                             |
| ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Firebase IS the API — no separate `user-management-api` repo                                                | Claims emitted via Firebase Admin SDK call-sites colocated with admin provisioning handlers in unified-trading-system-ui `(ops)/admin/*` (user-management-ui archived 2026-04-20) | Operator 2026-04-20 + fold 2026-04-22              |
| Claim set: `{org_id, business_unit_id, service_family, audience, fund_id, client_id, api_key_scopes}`       | Minimum enforceable surface to make `access_control()` self-contained                                                                                                             | Stage 3E §2.1 + Stage 3C §1.5 UserContext shape    |
| `service_family` claim uses 6-value internal enum (`IM RegUmbrella DART DART_reporting_only admin IM_desk`) | Prospect-facing 4-value enum (`IM DART RegUmbrella combo`) stays UI-only — claims encode what the backend actually resolves to                                                    | G1.11 rule 12 + Wave E closure note                |
| Staging Firebase must land FIRST                                                                            | Claim emission path needs a real Firebase project that isn't prod                                                                                                                 | Hard prereq — G2.6 `staging Firebase provisioning` |
| Mock-auth (localhost) keeps client-side persona lookup                                                      | CI + dev-tier-0 remain credential-free; dev only consults claims when `NEXT_PUBLIC_USE_FIREBASE_AUTH=true`                                                                        | CLAUDE.md 5-axis mode table                        |

## Cross-references

- **Upstream Wave G2-α prereq:** `refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md`
- **Downstream Wave G2-β:** `refactor_g2_2_per_client_api_key_issuance_2026_04_20.plan.md`,
  `refactor_g2_7_demo_provisioning_automation_2026_04_20.plan.md`,
  `refactor_g2_10_allocator_ui_split_2026_04_20.plan.md`
- **Folded plan:** `plans/active/user_management_merge_2026_03_23.plan.md` — JWT-shaping sub-phases absorbed here
- **G1 cross-refs:** G1.6 (`access_control` UserContext consumer), G1.11 rule 12 (service_family enum source), G1.10
  (questionnaire → persona → claim mapping)
- **Folded UAC types:** G1.8 `ArchetypeCapability`, G1.11 `ServiceFamily` enum

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.1
2. `/codex/14-playbooks/_ssot-rules/12-service-family-scope-rules.md` + `.yaml` (G1.11)
3. `plans/active/user_management_merge_2026_03_23.plan.md` — full, for JWT-shaping context being folded
4. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py` — `UserContext` dataclass
5. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/service_family_scope.py` (G1.11)
6. `unified-trading-system-ui/lib/auth/personas.ts` — 11 personas reference
7. `unified-trading-system-ui/lib/auth/demo-provider.ts`
8. `unified-trading-system-ui/lib/config/auth.ts`
9. `unified-trading-system-ui/lib/admin/firebase.ts` — admin SDK surface
10. `unified-trading-system-ui/app/(ops)/admin/users/` + `server/admin/providers.js` — provisioning handlers (post-fold)

## Out of scope

- Issuing API keys (that's G2.2; this plan only declares the `api_key_scopes` claim shape)
- Demo-provisioning automation (G2.7)
- Allocator UI split (G2.10)
- Changing any persona entitlement array in `personas.ts` — claims mirror personas, do not redefine them
- Touching `firestore.rules` security rules (deployment-service concern; separate follow-up)
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev (`localhost:3000` tier-1, mock-auth) MUST resolve the same `UserContext` shape as staging (`odum-research.co.uk`,
real Firebase). The only difference is the source: mock reads `personas.ts`; staging reads decoded claims. Every
Playwright spec uses the same `UserContext` assertion shape across both environments.

## Phase breakdown

### Phase A — UAC claim schema + decoder

- [ ] [AGENT] P0. Declare `JwtClaims` Pydantic model at
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/jwt_claims.py`:
      `{uid, email, email_verified, org_id, business_unit_id, service_family, audience, fund_id?, client_id?, api_key_scopes[]}`.
      `service_family` uses the `ServiceFamily` enum from G1.11 (6-value). `audience` uses the 4-value enum from G1.10.
- [ ] [AGENT] P0. Declare `decode_claims(token_payload: dict) -> JwtClaims` pure function with explicit field
      validation; raises `JwtClaimsValidationError` on missing required fields
      (uid/org_id/business_unit_id/service_family/audience).
- [ ] [AGENT] P0. Declare `user_context_from_claims(claims: JwtClaims) -> UserContext` adapter that lifts claims to the
      `UserContext` shape consumed by `access_control()` (G1.6) — no inference, no defaults for required audience
      fields.
- [ ] [AGENT] P0. Re-export from `unified_api_contracts.auth` public facade.

### Phase B — UAC tests + codex

- [ ] [AGENT] P0. `unified-api-contracts/tests/internal/unit/test_jwt_claims.py` — ≥12 cases: valid claim sets for each
      audience × service_family combination, missing-field rejection, malformed-enum rejection, optional-field handling.
- [ ] [AGENT] P0. Codex doc `/codex/06-coding-standards/jwt-claims-contract.md` — describes the claim shape + consumer
      pattern + mock-vs-real axis split.

### Phase C — admin claim emission (in unified-trading-system-ui `(ops)/admin/*` post-fold)

- [ ] [AGENT] P0. Extend unified-trading-system-ui `(ops)/admin/` provisioning handlers to call Firebase Admin SDK
      `setCustomUserClaims(uid, claims)` at account creation + persona-change. Claims derived from the new user's
      questionnaire response (G1.10) and rule-12 service-family scope (G1.11).
- [ ] [AGENT] P0. Admin UI surface `/admin/users/[uid]/claims` — read-only view of current custom claims + history (last
      10 mutations). No mutation UI in this wave.
- [ ] [AGENT] P0. Backfill script `scripts/backfill_jwt_claims.ts` — iterates existing Firebase users, derives claims
      from their current persona, writes via Admin SDK. Idempotent.

### Phase D — unified-trading-system-ui claim reader

- [ ] [AGENT] P0. New module `unified-trading-system-ui/lib/auth/claims.ts` — reads decoded ID token, validates shape,
      returns `UserContext`. When `NEXT_PUBLIC_USE_FIREBASE_AUTH=false` (mock mode), falls back to `personas.ts`.
- [ ] [AGENT] P0. Update `lib/auth/use-auth.ts` + `app/api/auth/session/route.ts` (or equivalents) to consume the new
      helper. Every `access_control()` caller flows through `claims.ts` → `UserContext`.
- [ ] [AGENT] P0. Playwright spec `tests/e2e/playbooks/refactor/refactor-g2-1-jwt-claims.spec.ts` seeds both mock and
      real-firebase personas, asserts that `UserContext` resolved in both modes is structurally identical.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec green on tier-1 dev AND staging Firebase.
- [ ] [AGENT] P0. Backfill script dry-run report: count of users updated, 0 errors.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/jwt_claims.py` — NEW
- `unified-api-contracts/unified_api_contracts/auth.py` — NEW facade (or extend existing)
- `unified-api-contracts/tests/internal/unit/test_jwt_claims.py` — NEW
- `/codex/06-coding-standards/jwt-claims-contract.md` — NEW
- `unified-trading-system-ui/server/admin/firebase-admin.ts` — MODIFY (add setCustomUserClaims helpers)
- `unified-trading-system-ui/app/(ops)/admin/users/[uid]/claims/page.tsx` — NEW
- `unified-trading-system-ui/scripts/admin/backfill_jwt_claims.ts` — NEW
- `unified-trading-system-ui/lib/auth/claims.ts` — NEW
- `unified-trading-system-ui/lib/auth/use-auth.ts` — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-1-jwt-claims.spec.ts` — NEW

## Execution DAG

```
A (UAC schema) → B (UAC tests + codex)
                   ↓
                 C (admin emission) + D (claim reader) [parallel]
                   ↓
                 E (QG + Playwright)
```

## Verification

1. UAC tests: ≥12 green cases.
2. unified-trading-system-ui `(ops)/admin/*`: `setCustomUserClaims` wired + admin claims-view page renders.
3. unified-trading-system-ui: `UserContext` identical in mock and real-firebase modes for same persona.
4. Backfill script dry-run: count equals expected Firebase user count; 0 validation errors.
5. Playwright spec green in CI.
6. All three repos: QG green.

## Handoff

Unblocks:

- **G2.2** — `api_key_scopes` claim becomes the authoritative scope source for per-client API keys.
- **G2.7** — demo-provisioning automation writes full claim set at per-prospect demo creation.
- **G2.10** — allocator UI routes on `audience` claim to distinguish IM-desk vs trading-platform-subscriber.
- **All backend services** — once G2.1 ships, any new service can consume `UserContext` from UAC without re-deriving.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools. Seed personas in both `NEXT_PUBLIC_USE_FIREBASE_AUTH=false` (mock) and
`=true` (real staging) modes; assert the resolved `UserContext` shape is structurally identical.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-1-jwt-claims.spec.ts` —

1. Seed personas via `tests/e2e/playbooks/seed-persona.ts`: `admin`, `client-full`, `prospect-im`, `prospect-dart`,
   `prospect-regulatory`, `internal-trader`.
2. For each persona, assert `UserContext.org_id / business_unit_id / service_family / audience` matches the expected
   claim shape per `personas.ts` declarations.
3. Assert `access_control(user, "/services/strategy-catalogue", "STAT_ARB_PAIRS_FIXED", phase="research")` returns the
   same decision in mock and staging modes.
4. Include orphan-reachability assertion — every claim-gated route has reachable detail.
5. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.1 (Wave G2-α, parallel with
G2.6/2.8/2.9/2.11; G2.6 must ship first for staging Firebase).**

---

You are executing **Refactor G2.1 — Org-scoped JWT claims** for the Unified Trading System at Odum Research. Wave G2-α;
depends on G2.6 (staging Firebase) completing first.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
# NOTE: user-management-ui archived 2026-04-20; admin work lands in unified-trading-system-ui under (ops)/admin/
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/service_family_scope.py
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py
ls unified-trading-system-ui/lib/admin/firebase.ts
# Verify G2.6 staging Firebase landed
grep -q "FIREBASE_PROJECT_ID.*staging" unified-trading-system-ui/.env.example 2>/dev/null || echo "G2.6 NOT SHIPPED — BLOCK"
```

All must exist + G2.6 gate satisfied. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_1_org_scoped_jwt_claims_2026_04_20.plan.md`

### Read-set (mandatory)

All 10 paths from the plan's Mandatory read-set. Read `user_management_merge_2026_03_23.plan.md` for context on JWT
shaping being folded here — do NOT re-execute its phases, just absorb its JWT-claim decisions.

### Deliverables

Per plan's Critical files list — 10 files across 3 repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev. Seed personas in both `NEXT_PUBLIC_USE_FIREBASE_AUTH=false` (mock) and `=true` (real
staging) modes; assert `UserContext` identical in both. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-1-jwt-claims.spec.ts`, seeded via `seed-persona.ts`,
asserting claim-shape parity, wiring into `scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Three repos touched → three commits. `git pull --rebase` before each push.

```
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.1 — JwtClaims schema + decoder + UserContext adapter" --agent
# Admin emission + claim reader ship in one UI commit now that user-management-ui is folded.
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(admin+auth): G2.1 — Firebase custom-claim emission in (ops)/admin + claim reader + UserContext parity + backfill" --agent
```

Manual-git fallback if quickmerge blocks on unrelated WIP: per-repo
`git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never `--dep-branch`, never
`git reset --hard` / `git push --force`.

### Success criteria

1. ✅ `JwtClaims` + `decode_claims` + `user_context_from_claims` exported from UAC auth facade.
2. ✅ ≥12 UAC tests green.
3. ✅ unified-trading-system-ui `(ops)/admin/*`: claim emission wired; admin view renders; backfill dry-run succeeds.
4. ✅ unified-trading-system-ui: `UserContext` parity between mock and real modes.
5. ✅ Playwright spec green on tier-1 dev + staging Firebase.
6. ✅ QG green on all three repos.
7. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT skip G2.6 prereq verification — JWT emission needs a real Firebase project that isn't prod.
- Do NOT redefine persona entitlement arrays — claims MIRROR personas; `personas.ts` remains SSOT.
- Do NOT issue API keys here — that's G2.2. Just declare the `api_key_scopes` claim SHAPE.
- Do NOT touch `firestore.rules` — deployment-service owns that follow-up.
- Do NOT `--no-verify` the pre-commit hook — fix the underlying failure.
- Do NOT use the 4-value prospect-facing enum as the `service_family` CLAIM value — claims carry the internal 6-value.
  The 4-value enum stays in UI form selectors.

### Report back

- Claim shape (field list) with rule-12 citation for `service_family`.
- UAC test count + pass rate.
- Backfill dry-run metrics.
- Playwright spec pass status (mock + staging).
- QG results (3 repos).
- 3 commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
