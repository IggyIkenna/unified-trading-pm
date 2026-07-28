---
doc_type: plan
title: WS-I — Service-to-Service Auth Migration (re-homed from the archived cicd_consolidated_remaining)
summary:
  "Re-homes WS-I (the service-to-service-auth migration onto the UTL create_s2s_auth_dependency factory) out of the
  archived cicd_consolidated_remaining_2026_06_24.md, per operator decision 2026-07-27 — WS-I specifically is still
  wanted; the archived plan's other ~51 open todos stay deferred/archived, unchanged. Live-state verification
  (2026-07-28) found execution-service's migration ALREADY SHIPPED (execution-service@7454c81a — source + test rewrite
  both landed); the only genuinely open item is deployment-api, held at an explicit 2026-06-24 operator ruling (LEAVE
  AS-IS — a real auth-contract difference, not a pure shim) that this plan re-affirms rather than re-litigates."
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, deployment-api, unified-trading-pm, unified-trading-library, strategy-service]
scope: [engineer, admin]
tags: [security, s2s-auth, ws-i, migration, execution-service, deployment-api, re-homed]
related:
  [
    /codex/07-security/service-to-service-auth.md,
    /plans/archive/2026_06/cicd_consolidated_remaining_2026_06_24.md,
    /plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,
  ]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  "Re-homed from the archived plans/archive/2026_06/cicd_consolidated_remaining_2026_06_24.md ▸ WS-I (contract_hardening
  #3), per operator decision 2026-07-27 (relayed via plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md's
  'Archival caveat' note: WS-I is still wanted; the other ~51 non-WS-I todos in that archived plan — D13
  version-out-of-source, misc P2/P3 hygiene — stay deferred/archived, NOT re-homed here)."
assigned_role: backend_engineer
drift_direction: advance-code
---

# WS-I — Service-to-Service Auth Migration

> **Plan-destination note (no interactive operator confirmation available at authoring time):** per `CLAUDE.md` § "Plans
> — format + authoring discipline" ("Plan destination — ASK BEFORE CREATING"), a new plan should ask the operator
> "agent-orchestrator plan or human plan?" before creation. This plan was authored non-interactively (background
> dispatch), so per the stated default it uses `assigned_vm: NA` / `execution_scope: local-only` (LOCAL track). This is
> also the substantively correct choice on the merits: the one genuinely open item below (deployment-api) is an explicit
> human judgment call already ruled on once by the operator, not a bounded AO-dispatchable outcome — see
> `task_template.md` § "Bounded outcome only — no judgment calls in a todo".

## Background

`cicd_consolidated_remaining_2026_06_24.md` (archived 2026-06-30, superseded by
`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`) was a multi-workstream CI/CD SSOT with ~51 open todos beyond the promote
pipeline itself — D13 version-out-of-source, misc P2/P3 hygiene, and **WS-I** (its own mixed workstream:
deps-hygiene/CVE items + the service-to-service-auth migration). The 2026-06-30 archival folded ALL of it into
"deferred, per the operator's 'everything else out of scope for now' directive" — including WS-I's auth-migration
sub-thread, even though two codex docs (`/codex/07-security/service-to-service-auth.md`,
`/codex/08-workflows/ci-cd-flow.md`) kept citing the archived plan as their live tracker.

**Operator decision (2026-07-27):** WS-I's service-to-service-auth migration specifically is still wanted. This plan
re-homes JUST that sub-thread. It does **not** re-open D13, the deps-hygiene/CVE items, or any of the other ~50 hygiene
todos — those remain correctly deferred, living on in the archived plan as their record.

## What WS-I actually was (from the archived plan, `### WS-I — deps hygiene / CVE`)

The archived WS-I section covered two unrelated sub-threads under one heading:

1. **Deps hygiene / CVE** (pip-floor bumps, the aiohttp/aioresponses `--ignore-vuln` tracked-for-removal item) — **NOT
   in scope here**, stays in the archived plan's record (it isn't "service-to-service-auth").
2. **Service-to-service-auth migration** (`(promotion_pipeline ▸ contract_hardening #3)`) — collapse the 3 remaining
   hand-rolled local `verify_service_token` copies (strategy-service, execution-service, deployment-api) onto the shared
   UTL factory `create_s2s_auth_dependency(service_name)` in `unified_trading_library/cloud_interface/s2s_auth.py`.
   **This is the scope of this plan.**

## Live-state verification (2026-07-28) — what's actually still open

Before writing new todos, this plan re-verified the 3-repo migration against the CURRENT checkouts (not just the
archived plan's prose, which had gone stale):

| Service             | Archived-plan (2026-06-24/25) status                                                                                                                                                            | VERIFIED live status, 2026-07-28                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `strategy-service`  | ✅ done, `strategy-service@b41db5684`                                                                                                                                                           | ✅ confirmed — `risk`/`pnl`/`position` all bind `create_s2s_auth_dependency("strategy-service")`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `execution-service` | Archived checkbox already cited `execution-service@7454c81a` as shipped, but the prose body + the codex doc's enrolled-services table still described it as "⏳ pending / needs a test rewrite" | ✅ **ALREADY SHIPPED, confirmed by direct read**: `execution_service/auth_s2s.py` is the canonical 5-line factory binding (`verify_service_token = create_s2s_auth_dependency("execution-service")`); `git log -- execution_service/auth_s2s.py` shows `7454c81ae refactor(auth): migrate execution-service S2S auth onto create_s2s_auth_dependency factory`, tree clean (no drift). The test rewrite ALSO shipped: `tests/unit/test_auth_s2s_and_timeline_builder.py`'s `TestAuthS2S...` class patches `unified_trading_library.cloud_interface.s2s_auth._is_mock_mode` / `_get_service_auth_token` (the factory's internals) and includes a `test_mock_mode_bypasses_auth` case — i.e. the "needs a test rewrite" caveat from the archived plan is ALSO already resolved, not just the source swap. |
| `deployment-api`    | "LEAVE AS-IS (operator-confirmed 2026-06-24): genuine auth-contract difference, not a pure S2S shim)"                                                                                           | ✅ confirmed still the live state — `deployment_api/auth.py` is still the hand-rolled `APIKeyHeader`/`DISABLE_AUTH` implementation, unchanged since the ruling (no drift). The ruling still applies; not re-litigated.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

**Conclusion: 2 of the 3 migrations are fully done (strategy-service, execution-service); the 3rd (deployment-api) is
intentionally NOT migrated per a standing operator ruling.** There is no dispatchable "finish the migration" code work
left — the only remaining action was the documentation staleness this plan's Task 3 fixed directly (see below), plus
keeping the deployment-api decision visibly on record in case it's ever revisited.

## Todos

- [x] 1. ✅ [DOCS] P2. Fix the stale `/codex/07-security/service-to-service-auth.md` "Enrolled Services" table —
      execution-service's row said "⏳ local `auth_s2s.py` — migrate to factory"; corrected to "✅ on factory" with the
      `execution-service@7454c81a` evidence (source + test-rewrite). Also repointed 3 references (top-of-doc "being
      collapsed onto it", the "Migration tracker" line, the bottom Cross-references entry) off the archived
      `cicd_consolidated_remaining_2026_06_24.md` onto this plan's path. Done-when:
      `grep -n     "cicd_consolidated_remaining" /codex/07-security/service-to-service-auth.md` returns zero hits. —
      evidence: `unified-trading-pm` (this session's commit, see plan Progress Log below for the SHA once shipped).
- [ ] 2. [OPERATOR] P3. BLOCKED-OPERATOR-DECISION — deployment-api's local `auth.py` → UTL factory migration. HELD at
      the 2026-06-24 operator ruling (LEAVE AS-IS: `deployment_api/auth.py`'s contract is genuinely different from the
      factory's — 401 vs the factory's 403 on missing/mismatched token, `DISABLE_AUTH` env vs `CLOUD_MOCK_MODE`,
      `Security(APIKeyHeader)` DI returning `str` vs the factory's `None`-returning `Request`-based dependency, a
      generic `"AUTH_FAILURE"` event vs the factory's typed `S2S_AUTH_FAILURE`). This is a genuine
      business/behavior-contract judgment call (task_template.md § finding U (i) — a standing ruling already on record,
      not a live gate to re-ask), so it stays non-dispatchable unless/until the operator explicitly reopens it. **If
      ever reopened**, the done-when is: the operator names the target shape (adopt the factory's contract as-is,
      accepting the 401→403 / event-name / DISABLE_AUTH semantic changes for every deployment-api caller; OR build a
      deployment-api-specific factory variant that preserves its current contract; OR confirm LEAVE AS-IS again) — then
      the swap ships + `deployment-api/tests/unit/test_auth.py` (the existing coverage for
      `verify_api_key`/`api_key_header`/`DISABLE_AUTH`) stays green, extended with the mock-mode-bypass case
      `execution-service/tests/unit/test_auth_s2s_and_timeline_builder.py`'s `TestAuthS2S` class demonstrates as the
      template.
- [x] 3. ✅ [DOCS] P3. Verify strategy-service + execution-service both carry ZERO drift from their archived-plan-cited
      shipped SHAs (no uncommitted local changes reverting the migration). Done-when: `git status --short` clean on both
      `strategy_service/{risk,pnl,position}/auth_s2s.py` and `execution_service/auth_s2s.py` in their respective
      checkouts. — Verified 2026-07-28: both clean, see the Live-state verification table above.

## Codex SSOTs

- `/codex/07-security/service-to-service-auth.md` — the S2S auth SSOT (Enrolled Services table + migration tracker
  updated by this plan's todo 1).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — why todo 2
  stays `[OPERATOR]`-gated rather than becoming AO-dispatchable.

## Progress Log

- 2026-07-28: Plan created — re-homed WS-I's service-to-service-auth migration out of the archived
  `cicd_consolidated_remaining_2026_06_24.md` per operator decision 2026-07-27 (relayed via
  `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`'s "Archival caveat" note). Live-state verification found
  execution-service's migration was ALREADY fully shipped (`execution-service@7454c81a`, source + test rewrite) — the
  archived plan's checkbox had recorded this but the codex doc + the archived plan's own prose still described it as
  pending; fixed the codex doc's staleness in the same pass (todo 1). deployment-api remains intentionally un-migrated
  per the standing 2026-06-24 operator ruling (todo 2, non-dispatchable). No new code-migration work is actually
  required to close this plan beyond the doc fix already shipped — todo 2 is a standing decision record, not active
  work.
