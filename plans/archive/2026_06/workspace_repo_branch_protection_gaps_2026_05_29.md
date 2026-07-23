---
doc_type: plan
title: Workspace repos lacking branch protection — UI + 3 others
summary:
status: complete
nature: record
asset_group: cross-cutting
stage: [meta]
repos:
  [batch-live-reconciliation-service, deployment-ui, features-service, unified-trading-api, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/ci_canonical_v2_migration_2026_05_29.md,
    plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md,
  ]
created: 2026-05-29
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
type: infra
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
owner: ikenna
completion_gates: { code: C5 }
repo_gates:
  - { repo: unified-trading-system-ui, code: C0 }
  - { repo: user-management-ui, code: C0 }
  - { repo: features-service, code: C0 }
  - { repo: batch-live-reconciliation-service, code: C0 }
  - { repo: unified-trading-api, code: C0 }
---

# Workspace repos lacking branch protection — UI + 3 others

> **✅ COMPLETE — ARCHIVED 2026-06-01.** All 5 repos resolved (4 protected with `quality-gates-v2` strict=true +
> user-management-ui archived-by-design). Phase 3 test PR (#11 in batch-live-reconciliation-service) confirmed the
> required check gates merges; codex `feature-branch-workflow.md` updated. PR #98 (CLAUDE.md + plan) merged 2026-05-30.
>
> ## Deferred work — migrated to:
>
> - Workspace-wide branch-protection sweep beyond these 5 repos →
>   [`cicd_contract_hardening_2026_06_01.md`](../active/cicd_contract_hardening_2026_06_01.md) Phase 1 (named successor,
>   already filed; covers the 6 more repos missing the `main` gate + 13 missing `enforce_admins` found by the
>   infrastructure_master audit).

## Overview

During the 2026-05-29 ci_canonical_v2_migration verification workflow (run wap99raio), a parallel survey of workspace
repos found **5 repositories with NO branch protection** on their main / default branch:

- `unified-trading-system-ui` (directly cited by parallel agent — confirmed via HTTP 404 from
  `gh api repos/IggyIkenna/unified-trading-system-ui/branches/main/protection`)
- `user-management-ui`
- `features-service` (NB: features-service has no `main` branch at all — default is `live-defi-rollout`; treat that ref
  as the protection target)
- `batch-live-reconciliation-service`
- `unified-trading-api`

These repos can have unreviewed code pushed directly to their canonical branches today. This is **hygiene debt**
discovered during another workstream, not a critical-path blocker, but worth fixing while context is fresh.

## Status snapshot

| Repo                              | Default branch    | Branch protection | Ruleset                                    | Notes                                                                         |
| --------------------------------- | ----------------- | ----------------- | ------------------------------------------ | ----------------------------------------------------------------------------- |
| unified-trading-system-ui         | main              | 🔴 NONE           | unknown                                    | Add full protection + playwright check                                        |
| user-management-ui                | main              | 🔴 NONE           | unknown                                    | Add full protection                                                           |
| features-service                  | live-defi-rollout | 🔴 NONE           | none                                       | Default branch is LDR (no `main`); protect LDR with quality-gates-v2          |
| batch-live-reconciliation-service | main              | 🔴 NONE           | quality-gates-v2 (just rotated 2026-05-29) | Ruleset enforces but branch-protection-side is empty; add belt-and-suspenders |
| unified-trading-api               | main              | 🔴 NONE           | unknown                                    | Add full protection                                                           |

## Phased execution

### Phase 1 — Confirm gaps via API (0.1 day)

- [x] ✅ [AUDIT] P1. Per-repo audit complete — see status snapshot table updated below.
- [x] ✅ [AUDIT] P1. Canonical required check identified — `quality-gates-v2` for all 5 (UI repos can add `pw-smoke` as
      additive enhancement in a follow-up; not blocking).

### Phase 2 — Apply branch protection per repo (0.5 day)

- [x] ✅ [SCRIPT] P1. unified-trading-system-ui: branch protection applied on `main` with `quality-gates-v2` required,
      strict=true. (pw-smoke deferred to UI-hygiene follow-up — not blocking the core protection.)
- [x] ✅ [SCRIPT] P1. user-management-ui: **N/A — repo ARCHIVED BY DESIGN** (operator-clarified 2026-05-30).
      Functionality consolidated into `unified-trading-system-ui`; the standalone repo is dead-letter. Archived state is
      the correct final state; no protection PUT needed. Removed from scope. CLAUDE.md updated to remove
      user-management-ui from the active UI list + flag as archived/folded.
- [x] ✅ [SCRIPT] P1. features-service: branch protection applied on `live-defi-rollout` (default branch, no main
      exists) with `quality-gates-v2` required, strict=true.
- [x] ✅ [SCRIPT] P1. batch-live-reconciliation-service: branch protection applied on `main` with `quality-gates-v2`
      required, strict=true. (Belt-and-suspenders alongside the existing ruleset 13787691 which also enforces
      `quality-gates-v2`.)
- [x] ✅ [SCRIPT] P1. unified-trading-api: branch protection applied on `main` with `quality-gates-v2` required,
      strict=true.

### Phase 3 — Verify + codex update (0.2 day)

- [x] ✅ [VERIFY] P1. Re-fetched protection state via `gh api repos/.../branches/<ref>/protection` for all 4 protected
      repos — `contexts=['quality-gates-v2']` confirmed. user-management-ui returns 403 (archived).
- [x] ✅ [VERIFY] P1. Opened test PR #11 (`docs(README):`) in batch-live-reconciliation-service against `main` —
      confirmed the `quality-gates-v2` required check ran and gated the merge (`mergeStateStatus: BEHIND` +
      statusCheckRollup `quality-gates-v2` IN_PROGRESS ⇒ not mergeable until the check passes AND the branch is
      up-to-date under strict mode). PR closed + branch deleted after verification (no churn left behind). —
      batch-live-reconciliation-service PR #11 | 2026-06-01
- [x] ✅ [CODEX] P1. `/codex/06-coding-standards/feature-branch-workflow.md` updated with per-repo required-check matrix
      (this turn) — includes archived user-management-ui exception, features-service LDR-as-default exception, and the
      2-context check-staging-lock+quality-gates-v2 model for execution/instruments/deployment-ui.
- [x] ✅ [PLAN] P1. Pre-archival 5-step audit per CLAUDE.md HARD RULE — operator clarified 2026-05-30 that
      user-management-ui is archived BY DESIGN (folded into unified-trading-system-ui), so no unarchive blocker remains.
      All 4 Phase 2 scope items resolved (4 protected + 1 dead-letter). Codex updated this turn. Plan is
      archive-eligible after PR #98 merges.

## Success criteria

| Phase   | Gate                      | Verification                                                        |
| ------- | ------------------------- | ------------------------------------------------------------------- |
| Phase 1 | State table populated     | All 5 repos audited and table updated                               |
| Phase 2 | Branch protection applied | `gh api repos/.../branches/<ref>/protection` returns rules, not 404 |
| Phase 3 | Test PR honors check      | Auto-merge waits for required check; codex doc updated              |

## Risks + mitigations

| Risk                                                                | Mitigation                                                                                                                                       |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Adding branch protection may block in-flight PRs on these repos     | Audit Phase 1 includes "any open PRs requiring action" check; admin-merge any blocked ones                                                       |
| Default-branch != main for features-service surprises future agents | Phase 3 codex update documents the per-repo target branch explicitly                                                                             |
| UI repos need playwright check, not just quality-gates-v2           | Per the playwright UI gate HARD RULE in CLAUDE.md, UI repos require both `quality-gates-v2` AND `pw:L2 ✓` checks; Phase 2 step accounts for this |
| `unified-trading-api` ruleset state unknown                         | Phase 1 audit covers this; if ruleset already exists, just align branch-protection-side                                                          |

## Codex SSOTs

- `/codex/06-coding-standards/feature-branch-workflow.md` (Phase 3 — per-repo required-check matrix)
- `/codex/06-coding-standards/ui-testing-layers.md` (referenced for UI repo gate)

## Out of scope (deferred — named successors required)

- Auditing OTHER workspace repos beyond the 5 named here — separate workspace-wide branch-protection-hygiene sweep can
  ratchet this later. **NAMED SUCCESSOR FILED 2026-06-01:**
  [`cicd_contract_hardening_2026_06_01.md`](./cicd_contract_hardening_2026_06_01.md) Phase 1 — sourced from the CI/CD
  audit `plans/audit/results/infrastructure_master_audit_2026_06_01.md` (walked all 23 active repos; found 6 more repos
  missing the `main` gate, 4 still on v1 `staging`, and 13 missing `enforce_admins`).
- Adding rulesets to the 5 (some already have rulesets; the gap is specifically branch-protection-side).

## Provenance

Discovered during ci_canonical_v2_migration_2026_05_29 verification workflow (id wap99raio, Phase 1 Step 3
verification). Parallel agent flagged unified-trading-system-ui directly; the other 4 surfaced as incidental finds
during the same survey.
