---
title: Workspace repos lacking branch protection — UI + 3 others
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
type: infra
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
created: 2026-05-29
owner: ikenna
asset_group: cross-cutting
completion_gates:
  code: C5
repo_gates:
  - repo: unified-trading-system-ui
    code: C0
  - repo: user-management-ui
    code: C0
  - repo: features-service
    code: C0
  - repo: batch-live-reconciliation-service
    code: C0
  - repo: unified-trading-api
    code: C0
related_plans:
  - plans/active/ci_canonical_v2_migration_2026_05_29.md
  - plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md
---

# Workspace repos lacking branch protection — UI + 3 others

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

- [ ] [AUDIT] P1. Run a clean per-repo audit via `gh api repos/IggyIkenna/<repo>/branches/<default>/protection` for each
      of the 5 repos. Cross-check with `gh api repos/IggyIkenna/<repo>/rulesets` to record both branch-protection AND
      ruleset state per repo. Update the table above with the actual state column for each.
- [ ] [AUDIT] P1. For each repo, identify the canonical required check name the workspace expects (likely
      `quality-gates-v2` for backend, `pw-smoke` or similar for UIs). Cross-reference with
      `codex/06-coding-standards/ui-testing-layers.md` for UI-specific gates.

### Phase 2 — Apply branch protection per repo (0.5 day)

- [ ] [SCRIPT] P1. unified-trading-system-ui: enable branch protection on `main`. Required checks: `quality-gates-v2` +
      `pw-smoke` (per playwright UI gate HARD RULE). Strict mode = true.
- [ ] [SCRIPT] P1. user-management-ui: same recipe as unified-trading-system-ui.
- [ ] [SCRIPT] P1. features-service: enable branch protection on `live-defi-rollout` (its default branch). Required
      check: `quality-gates-v2`. Strict mode = true. Note: this is the only repo where the canonical branch is LDR, not
      main.
- [ ] [SCRIPT] P1. batch-live-reconciliation-service: enable branch protection on `main` (ruleset already enforces
      `quality-gates-v2`; this is belt-and-suspenders alignment). Required check: `quality-gates-v2`.
- [ ] [SCRIPT] P1. unified-trading-api: enable branch protection on `main`. Required check: `quality-gates-v2`.

### Phase 3 — Verify + codex update (0.2 day)

- [ ] [VERIFY] P1. Re-run the audit script for all 5 repos. Confirm `required_status_checks.contexts` populated.
      Document final required-check name per repo.
- [ ] [VERIFY] P1. Open a tiny test PR in one of the 5 (most reversible: a `docs(README):` PR) and confirm auto-merge
      waits for the required check.
- [ ] [CODEX] P1. Update `codex/06-coding-standards/feature-branch-workflow.md` (or equivalent) with a per-repo
      required-check matrix so future agents know what's expected per repo.
- [ ] [PLAN] P1. Pre-archival 5-step audit per CLAUDE.md HARD RULE.

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

- `codex/06-coding-standards/feature-branch-workflow.md` (Phase 3 — per-repo required-check matrix)
- `codex/06-coding-standards/ui-testing-layers.md` (referenced for UI repo gate)

## Out of scope (deferred — named successors required)

- Auditing OTHER workspace repos beyond the 5 named here — separate workspace-wide branch-protection-hygiene sweep can
  ratchet this later.
- Adding rulesets to the 5 (some already have rulesets; the gap is specifically branch-protection-side).

## Provenance

Discovered during ci_canonical_v2_migration_2026_05_29 verification workflow (id wap99raio, Phase 1 Step 3
verification). Parallel agent flagged unified-trading-system-ui directly; the other 4 surfaced as incidental finds
during the same survey.
