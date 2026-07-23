---
title: Refactor G2.2 — Per-client API key issuance
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.2
  - refactor_g2_1_org_scoped_jwt_claims_2026_04_20.plan.md
  - refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md
  - plans/active/user_management_merge_2026_03_23.plan.md (folded)
  - plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md Phase 6 (user-management-ui fold-in — ARCHIVED
    2026-04-20)
# Wave G2-β — sequential after G2-α (needs 2.1 + 2.6). Parallel with G2.7, G2.10.
# PATH AMENDMENT 2026-04-22: admin surfaces live at unified-trading-system-ui/app/(ops)/admin/*.
supersedes: [user_management_merge_2026_03_23.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [user_management_merge_2026_03_23.plan.md](./user_management_merge_2026_03_23.plan.md). user_management_merge folded
> into G2.2 (api-key issuance UI moved to UTSU) See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Refactor G2.2 — Per-client API key issuance

## Context

Stage 3E §2.2 ships per-client API keys. Today every call is a Firebase-session-token; there is no API developer
surface, no UAC declaration of key scopes, and no rate-limit axis per client. Clients cannot integrate their own systems
against ours without session-hijacking a browser login.

Target: per-client API keys issued by Firebase Admin SDK call-sites + Secret Manager, scoped to
`(client_id, api_key_scopes[])` from the G2.1 claim shape. Rotatable via admin console. Rate-limited per-org at
deployment-api. UAC declares the `ApiKeyScope` enum: `read_data`, `read_reporting`, `execute_trades`, `execute_defi`,
`admin_override_coverage`.

## Decisions locked with user (2026-04-20)

| Decision                                                             | Chosen                                                                       | Source                           |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------- |
| API keys stored in GCP Secret Manager (not Firestore)                | SM has hot-reload + audit logging; Firestore is for CRM + user metadata only | CLAUDE.md ApiKeyReloader pattern |
| One key per (client_id, scope-bundle) — multi-key per client allowed | Lets clients separate read-only automations from trading automations         | Stage 3E §2.2                    |
| Keys rotatable from admin console — not client self-serve            | Minimises blast radius during rollout; self-serve can ship later             | Operator deferral                |
| Rate limiting at deployment-api layer (not per-service)              | deployment-api already rate-limits by Firebase user; extends naturally       | Stage 3E §2.2 blast radius       |
| `ApiKeyScope` enum canonicalised in UAC                              | Matches `JwtClaims.api_key_scopes` from G2.1                                 | G2.1 claim schema                |

## Cross-references

- **Upstream:** G2.1 (JWT claims declare scope shape), G2.6 (staging Firebase project)
- **Wave G2-β peers (parallel):** G2.7 (demo provisioning), G2.10 (allocator UI split)
- **Folded plan:** `plans/active/user_management_merge_2026_03_23.plan.md` — API-key sub-phases absorbed
- **Codex:** `/codex/06-coding-standards/config-reloader-pattern.md` — ApiKeyReloader reuse
- **CLAUDE.md:** Secret Manager rules, ApiKeyReloader pattern

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.2
2. `plans/active/user_management_merge_2026_03_23.plan.md`
3. `refactor_g2_1_org_scoped_jwt_claims_2026_04_20.plan.md` — claim shape
4. `/codex/06-coding-standards/config-reloader-pattern.md`
5. `unified-trading-library/` — ApiKeyReloader pattern reference
6. `deployment-api/` (or equivalent) — rate-limiting entry point
7. `unified-trading-system-ui/lib/admin/firebase.ts` + `server/admin/firebase-admin.ts` (post-fold)

## Out of scope

- Client self-serve key rotation UI (future wave)
- Rotating existing Firebase session-token callers (separate migration)
- Touching `firestore.rules` for key metadata (keys live in SM, not Firestore)
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mocks API-key validation by env var `MOCK_API_KEY=<value>`; staging uses real SM-backed keys. Both paths flow
through the same UAC `validate_api_key(key, required_scope) -> ApiKeyValidation` helper — no code-fork.

## Phase breakdown

### Phase A — UAC schema + helpers

- [ ] [AGENT] P0. Declare `ApiKeyScope` enum in
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/api_keys.py`:
      `READ_DATA | READ_REPORTING | EXECUTE_TRADES | EXECUTE_DEFI | ADMIN_OVERRIDE_COVERAGE`.
- [ ] [AGENT] P0. Declare `ApiKey` dataclass: `{key_id, client_id, scopes[], issued_at, expires_at?, rotated_from?}`.
- [ ] [AGENT] P0. Declare `validate_api_key(key_str, required_scope, *, registry=...) -> ApiKeyValidation` pure function
      (takes scope registry injected).
- [ ] [AGENT] P0. Re-export from `unified_api_contracts.auth` facade.

### Phase B — UAC tests + codex

- [ ] [AGENT] P0. `unified-api-contracts/tests/internal/unit/test_api_keys.py` — ≥10 cases: scope match, scope mismatch
      (deny), expired key (deny), invalid key (deny), rotated-from chain validation.
- [ ] [AGENT] P0. Codex doc `/codex/06-coding-standards/api-key-issuance.md` — describes issuance + rotation +
      scope-to-claim mapping.

### Phase C — Secret Manager integration

- [ ] [AGENT] P0. unified-trading-system-ui `(ops)/admin/` handler: issues new API key via Firebase Admin SDK + writes
      to GCP Secret Manager at `api-keys/{client_id}/{key_id}` with access controls.
- [ ] [AGENT] P0. Admin UI `/admin/clients/[id]/api-keys` — list current keys, issue new, rotate, revoke.
- [ ] [AGENT] P0. Display key ONCE at issuance (never again); copy-to-clipboard UI.

### Phase D — deployment-api rate-limit + auth middleware

- [ ] [AGENT] P0. deployment-api middleware accepts `Authorization: Bearer <api-key>` OR Firebase ID token. Routes
      through `validate_api_key()` + attaches `UserContext` with `client_id` + `api_key_scopes`.
- [ ] [AGENT] P0. Per-client rate limiting — counter keyed by `client_id` (not `uid` alone) for API-key calls.
- [ ] [AGENT] P0. ApiKeyReloader hot-reload integration — rotate without restarting services.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd deployment-api && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-2-api-keys.spec.ts` — admin flow, issue + rotate + revoke.
- [ ] [AGENT] P0. Integration smoke — issue key, hit a deployment-api endpoint with `Authorization: Bearer`, verify
      scope enforcement.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/api_keys.py` — NEW
- `unified-api-contracts/unified_api_contracts/auth.py` — MODIFY (extend facade)
- `unified-api-contracts/tests/internal/unit/test_api_keys.py` — NEW
- `/codex/06-coding-standards/api-key-issuance.md` — NEW
- `unified-trading-system-ui/app/(ops)/admin/clients/[id]/api-keys/page.tsx` — NEW
- `unified-trading-system-ui/lib/admin/api-keys/issue.ts` — NEW
- `deployment-api/middleware/api_key_auth.py` — NEW (or equivalent)
- `deployment-api/middleware/rate_limit.py` — MODIFY (per-client axis)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-2-api-keys.spec.ts` — NEW

## Execution DAG

```
A (UAC schema) → B (tests + codex)
                   ↓
                 C (SM + admin UI in (ops)/admin) + D (deployment-api middleware) [parallel]
                   ↓
                 E (QG + Playwright + integration smoke)
```

## Verification

1. `ApiKeyScope` + `ApiKey` + `validate_api_key` exported from UAC auth facade.
2. ≥10 UAC tests green.
3. Admin UI: issue, rotate, revoke all work.
4. deployment-api: `Authorization: Bearer <key>` accepted; scope enforced; rate-limit per client.
5. Playwright spec green.
6. Integration smoke: key-issued endpoint returns 403 without scope, 200 with.
7. QG green on all three repos.

## Handoff

Unblocks:

- **pb3c `dart-demo.md`** — developer-portal walkthrough needs issuable keys.
- **pb2b `dart-briefing.md`** — API-key description grounded in real UI.
- **G3.1 pricing-engine** — admin cost-quote endpoint can gate on `ADMIN_OVERRIDE_COVERAGE` scope.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (unified-trading-system-ui) through MCP Playwright tools as admin
persona. Issue a new API key for a test client, copy the value, switch to `localhost:3000`, hit a DART data endpoint
using the key in `Authorization: Bearer`; verify scope enforcement.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-2-api-keys.spec.ts`:

1. Seed admin persona; issue API key via admin UI.
2. Use issued key to hit a scope-gated endpoint; assert 200.
3. Use issued key on an endpoint requiring a scope NOT on the key; assert 403.
4. Rotate key; assert old key returns 401.
5. Include orphan-reachability assertion for the admin key-management surface.
6. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.2 (Wave G2-β, after G2-α
completes).**

---

You are executing **Refactor G2.2 — Per-client API key issuance** for the Unified Trading System at Odum Research. Wave
G2-β; G2.1 + G2.6 must be shipped first.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
# user-management-ui archived 2026-04-20 (ARCHIVED.md at repo root). Admin work lands in unified-trading-system-ui.
git -C deployment-api checkout live-defi-rollout && git -C deployment-api pull 2>/dev/null || echo "verify deployment-api repo name"
# Verify G2.1 + G2.6 shipped
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/jwt_claims.py 2>/dev/null || echo "G2.1 NOT SHIPPED — BLOCK"
```

All must exist + G2.1 + G2.6 gates green. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_2_per_client_api_key_issuance_2026_04_20.plan.md`

### Read-set (mandatory)

All 7 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 9 files across 4 repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (unified-trading-system-ui) through MCP Playwright tools. Issue API key via admin UI; hit
scope-gated endpoints; verify 200/403/401 round-trip. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-2-api-keys.spec.ts` — seeded via `seed-persona.ts`,
full CRUD + rotation cycle asserted, wired into `scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Four repos touched → four commits. `git pull --rebase` before each push.

```
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.2 — ApiKeyScope + ApiKey + validate_api_key helpers" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(admin/api-keys): G2.2 — issuance + rotation (ops)/admin UI + SM integration" --agent
cd ../deployment-api && bash scripts/quickmerge.sh "feat(auth): G2.2 — API-key auth middleware + per-client rate limiting" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "test(playbooks): G2.2 — API-key issuance Playwright spec" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ `ApiKeyScope` + `ApiKey` + `validate_api_key` exported.
2. ✅ ≥10 UAC tests green.
3. ✅ Admin UI: issue + rotate + revoke flows green.
4. ✅ deployment-api middleware: Authorization: Bearer validated + scope enforced.
5. ✅ Per-client rate limiting enforced.
6. ✅ Playwright spec green.
7. ✅ QG green on 4 repos.
8. ✅ 4 commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT store API keys in Firestore — Secret Manager only.
- Do NOT display key plaintext beyond issuance — one-time display.
- Do NOT build client-self-serve rotation — admin-only in this wave.
- Do NOT use `os.getenv` for SM access — use `UnifiedCloudConfig` per CLAUDE.md.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- API-key scope enum list + UAC test count.
- Admin UI CRUD + rotation flow results.
- deployment-api middleware: 200/401/403 smoke results.
- Per-client rate-limit verification.
- Playwright spec pass status.
- QG results (4 repos).
- 4 commit SHAs pushed to live-defi-rollout.
