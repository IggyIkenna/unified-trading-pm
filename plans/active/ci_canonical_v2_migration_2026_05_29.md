---
title: CI canonical v2 migration — ghost-workflow workaround across PM/UAC/UTL (+5)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
type: infra
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
created: 2026-05-29
owner: ikenna
asset_group: cross-cutting
completion_gates:
  code: C5
  deployment: D3
  business: B3
repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none
  - repo: ml-service
    code: C0
    deployment: none
    business: none
  - repo: features-service
    code: C0
    deployment: none
    business: none
  - repo: batch-live-reconciliation-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
related_plans:
  - plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md
  - plans/active/tradfi_massive_dual_source_2026_05_28.md
---

# CI canonical v2 migration — ghost-workflow workaround

## Overview

Rolls every affected workspace repo onto the new canonical CI flow (codex/08-workflows/ci-cd-flow.md) AND applies a v2
rename of the workspace-qg caller workflow with a new job key to escape GitHub's server-side BuildFailed ghost cache.

**Operator directive 2026-05-29**: "All pushed. Here's the canonical updated flow: LDR → Cloud Build (canonical,
post-fixes)". Operator wants PM → UAC → UTL first (in order), each migrated by:

1. Running `bash scripts/quality-gates.sh` LOCALLY in FULL (no skip flags) — writes `.qg_last_passed_sha` sentinel
2. Verifying sentinel SHA matches `git rev-parse HEAD`
3. **Temporarily bypassing remote `quality-gates` required check** in main branch protection (defense-in-depth only;
   local sentinel IS the canonical pass per the new flow)
4. `quickmerge.sh "msg" --agent` per repo on the canonical-aligned content
5. **Renaming** the workspace-qg caller workflow (new file path + new `name:` + new job key like
   `quality-gates-2026-06`) to escape the GitHub-cached BuildFailed ghost
6. Verifying the new check registers cleanly (no startup_failure on first trigger)
7. **Re-requiring** the new job key as the required status check
8. Removing the old `quality-gates` from required checks (it's now orphaned)

## Why v2 rename will work (theory + plan-B)

The existing issue doc tested Option B (rename `workspace-qg.yml` → `workspace-qg-v2.yml`) and Option C (brand-new file
`workspace-qg-v3.yml`); both reproduced startup_failure because **GitHub's cache also keys on the callee path**
(`IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates.yml@live-defi-rollout`). Renaming the caller
alone doesn't escape it.

**v2 design (NEW — Option D)** must change BOTH ends of the chain simultaneously:

1. **Caller**: new file path (e.g. `quality-gates-v2.yml`) + new `name:` field + new job key
2. **Callee**: new file path for python-quality-gates (e.g. `python-quality-gates-v2.yml`) + new `name:` + new
   `workflow_call:` signature OR inline the QG steps directly into the v2 caller (no reusable indirection at all)
3. Update `infra-quality-gates.yml` (intermediate reusable) to reference v2 callee — or skip infra-qg entirely
4. The v2 chain has **zero references** to the original `python-quality-gates.yml` path → GitHub has no prior cache key
   to hit

**If v2 ALSO ghosts** (cache also keys on something deeper like job-id or signature):

- Plan-B: inline the QG steps directly into `quality-gates-v2.yml` (no reusable indirection). One job, no callees.
  GitHub can't ghost what doesn't reference anything.
- Plan-C: wait for GH Support ticket #4422570 to clear (timeline unknown)

## Scope

| Priority                       | Repos                                                                                                                                              | Why                                                                                                |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **P0 — this plan, this cycle** | PM, UAC, UTL (3 repos)                                                                                                                             | Operator-prioritized; PM hosts the broken callee, UAC + UTL unblock TradFi PR #50 dependency chain |
| **P1 — same plan, next phase** | alerting-service, ml-service, features-service, batch-live-reconciliation-service, execution-service, instruments-service, deployment-ui (7 repos) | All ghost-affected per issue doc; same v2 pattern applies; lower urgency                           |

## Status snapshot

| Layer                                      | Status                | Note                                                                                  |
| ------------------------------------------ | --------------------- | ------------------------------------------------------------------------------------- |
| Canonical CI codex doc                     | ✅ shipped 2026-05-29 | `codex/08-workflows/ci-cd-flow.md` § three-tier + two-pass + sentinel model           |
| PM `python-quality-gates.yml` real content | ✅ correct on disk    | Bad comment reverted in `7ca446080`                                                   |
| PM main branch protection                  | 🔴 blocks merges      | Required `quality-gates` check fires ghost workflow 283699244                         |
| GH Support ticket                          | 🟡 open               | #4422570 filed 2026-05-27, awaiting cache clear                                       |
| v2 caller workflow on PM                   | 🔴 missing            | This plan ships it                                                                    |
| v2 callee workflow on PM                   | 🔴 missing            | This plan ships it                                                                    |
| Required-check rotation                    | 🔴 missing            | This plan flips it from `quality-gates` → `quality-gates-2026-06` (or chosen v2 name) |

## Phased execution

### Phase 0 — Pre-flight: confirm canonical doc + branch protection access (0.25 day)

- [ ] [AUDIT] P0. Read `codex/08-workflows/ci-cd-flow.md` end-to-end + confirm every step of the canonical flow is
      reflected in this plan. If anything drifted between codex and operator-stated flow, update plan first per the
      doc-plan-code principle.
- [ ] [AUDIT] P0. Verify operator has admin perms on GitHub branch protection settings for PM, UAC, UTL (and the 7 P1
      repos). Without admin perms, the rotation step requires operator action.
- [ ] [AUDIT] P0. Confirm `.qg_last_passed_sha` sentinel format expected by quickmerge —
      `bash     scripts/quickmerge.sh --help 2>&1 | head -30` should mention it. If missing in quickmerge
      implementation, file separate fix-quickmerge issue and block this plan on it.

### Phase 1 — PM (1 day)

- [ ] [SCRIPT] P0. Run `bash scripts/quality-gates.sh` IN FULL (no skip flags) in PM at current HEAD. Verify exit 0 +
      `.qg_last_passed_sha` file written + SHA matches `git rev-parse HEAD`.
- [ ] [SCRIPT] P0. Stage current working-tree changes (none expected post-slot-reset). Create v2 workflow files:
  - `.github/workflows/quality-gates-v2.yml` — new `name:`, new `on:` triggers (same as v1: push+PR to main), new job
    key `quality-gates-2026-06`, calls new v2 callee
  - `.github/workflows/python-quality-gates-v2.yml` — new `name:`, new `workflow_call:` signature, fresh
    `jobs.quality-gates:` block (same body as v1)
  - DO NOT delete v1 files yet — leave them as ghost-targets so the cache doesn't poison v2 via shared registration
- [ ] [SCRIPT] P0.
      `bash scripts/quickmerge.sh "ci(workflows): add v2 caller+callee — escape GHA ghost cache"     --agent --files '.github/workflows/quality-gates-v2.yml .github/workflows/python-quality-gates-v2.yml'`.
      Sentinel verified at quickmerge time → push proceeds → PR to staging → auto-merge.
- [ ] [SCRIPT] P0. **Branch protection rotation** on PM main:
  - Remove `quality-gates` from required status checks (frees PR #83 immediately for auto-merge)
  - Wait for first PR-against-main to trigger v2 caller → verify it does NOT startup_failure
  - Add `quality-gates-2026-06` (v2 job key) as new required status check
- [ ] [VERIFY] P0. PR #83 (TradFi plan) merges. Confirm via `gh pr view 83 --repo IggyIkenna/unified-trading-pm`.
- [ ] [VERIFY] P0. Subsequent PR to PM main triggers v2 check, reports success (not startup_failure). If v2 ALSO ghosts,
      fall back to Plan-B (inline QG steps in v2 caller, no reusable).

### Phase 2 — UAC (0.5 day)

- [ ] [SCRIPT] P0. Same recipe as Phase 1 in UAC:
  - Local `quality-gates.sh` full run → sentinel
  - Add `.github/workflows/quality-gates-v2.yml` to UAC. UAC's caller references PM's v2 callee at LDR ref (just like v1
    references python-quality-gates.yml at LDR)
  - Quickmerge per canonical flow
- [ ] [SCRIPT] P0. UAC main branch protection rotation: drop v1 required check → add v2.
- [ ] [VERIFY] P0. PR #50 (TradFi universe expansion) merges. Confirm clean.
- [ ] [VERIFY] P0. Next UAC PR triggers v2 cleanly.

### Phase 3 — UTL (0.5 day)

- [ ] [SCRIPT] P0. Same recipe as Phase 1+2 in unified-trading-library:
  - Local `quality-gates.sh` full run → sentinel
  - Add v2 caller workflow
  - Quickmerge
- [ ] [SCRIPT] P0. UTL main branch protection rotation.
- [ ] [VERIFY] P0. Next UTL PR triggers v2 cleanly.

### Phase 4 — Rollout to remaining 7 ghost-affected repos (1.5 days)

Apply the same v2 recipe to alerting-service, ml-service, features-service, batch-live-reconciliation-service,
execution-service, instruments-service, deployment-ui. Order by risk (lowest first):

- [ ] [SCRIPT] P1. alerting-service — already has `workspace-qg.yml` and `workspace-qg-v2.yml` from May-27 Option B
      attempt. Add v3 caller pointing at v2 callee; rotate branch protection.
- [ ] [SCRIPT] P1. ml-service — straight v2 application
- [ ] [SCRIPT] P1. features-service
- [ ] [SCRIPT] P1. batch-live-reconciliation-service
- [ ] [SCRIPT] P1. execution-service
- [ ] [SCRIPT] P1. instruments-service
- [ ] [SCRIPT] P1. deployment-ui — note: uses `ui-quality-gates.yml` not python-quality-gates; v2 here means
      ui-quality-gates-v2.yml + GCP_SA_KEY secret path verified
- [ ] [VERIFY] P1. workspace-qg green across all 10 repos via
      `gh run list --repo <each> --workflow quality-gates-v2 --limit 1` per repo

### Phase 5 — Cleanup + codex updates (0.25 day)

- [ ] [SCRIPT] P1. Once all 10 repos run cleanly on v2, delete v1 caller workflow files in each repo (single quickmerge
      per repo). Keep the v1 PM callee `python-quality-gates.yml` for now to avoid forced GitHub re-validation; remove
      in a later cleanup once GH Support ticket clears.
- [ ] [CODEX] P1. Update `codex/08-workflows/ci-cd-flow.md` to reference the v2 job key as the canonical required-check
      name. Add SUPERSEDED banner to any sub-doc that names the v1 `quality-gates` context.
- [ ] [CODEX] P1. Update `plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md` with Option D results +
      close-out: which repos shipped v2 successfully, whether v2 ghosted (Plan-B trigger), GH ticket status.
- [ ] [CLAUDE.md] P1. If the v2 workflow filename/job key needs to be communicated workspace-wide, add a 1-line pointer
      under "CI Verification After Every Push" section.
- [ ] [SCRIPT] P1. **Enable `enforce_admins` on staging + main across all 10 repos** — blocks admin bypass of branch
      protection (currently `enforce_admins: false`, meaning `IggyIkenna` can merge PRs even when `quality-gates` check
      has not passed). Only enable AFTER all 10 repos are green and passing QG on main. Command per repo:
      `bash     for repo in unified-trading-pm unified-api-contracts unified-trading-library execution-service \                 instruments-service strategy-service market-tick-data-service alerting-service \                 deployment-service unified-trading-system-ui; do       gh api repos/IggyIkenna/$repo/branches/staging/protection/enforce_admins -X POST       gh api repos/IggyIkenna/$repo/branches/main/protection/enforce_admins -X POST       echo "$repo: enforce_admins enabled on staging + main"     done     `
      **Precondition**: all 10 repos show green on `gh run list --workflow quality-gates-v2 --limit 1`. **Reverting**
      (emergency): `gh api repos/IggyIkenna/<repo>/branches/main/protection/enforce_admins -X DELETE`.
- [ ] [PLAN] P1. Pre-archival 5-step audit per CLAUDE.md HARD RULE.

## Success criteria

| Phase   | Gate                                                         | Verification                                                                      |
| ------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| Phase 1 | PM `quality-gates-v2` reports success on PR + #83 merges     | `gh pr view 83 --repo IggyIkenna/unified-trading-pm` shows MERGED                 |
| Phase 2 | UAC v2 clean + #50 merges                                    | Same pattern                                                                      |
| Phase 3 | UTL v2 clean                                                 | First post-rotation PR reports success                                            |
| Phase 4 | All 10 repos green on v2                                     | `for repo in ...; gh run list --workflow quality-gates-v2 --limit 1`; all succeed |
| Phase 5 | Codex doc updated + issue doc closed + cleanup commit landed | Inventory regenerator passes; archival audit OK                                   |

## Risks + mitigations

| Risk                                                                                                                                    | Mitigation                                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v2 also ghosts (cache keys deeper than file path)                                                                                       | Plan-B: inline QG steps in v2 caller, no reusable indirection. One job, no callees                                                                                                                                                                                                                                                                                        |
| Agent lacks branch protection admin perms in some repo                                                                                  | Verified 2026-05-29: `gh auth status` shows `IggyIkenna` with `repo` scope; `admin=True` confirmed on PM/UAC/UTL via `gh api repos/.../permissions`. GH_PAT in `central-element-323112/GH_PAT` is the cron-side fallback. Agent does rotations directly via `gh api PUT repos/.../branches/main/protection`. If any P1 repo refuses, fall back to filed-PR + operator-ack |
| Rollout-quality-gates-ci-workflows.py (or equivalent template-rollout script) overwrites v2 with v1 templates on next run               | Phase 0 audit confirms rollout script exists; if it does, add v2 exception entry first                                                                                                                                                                                                                                                                                    |
| Race: another agent merges PR with v1 check still required                                                                              | Phase 1's protection-rotation is ordered as: drop v1 → wait for v2 → add v2. Brief window where NO required check exists; minimize by completing same agent turn                                                                                                                                                                                                          |
| `.qg_last_passed_sha` sentinel doesn't exist in quickmerge yet                                                                          | Phase 0 audit gates on this; if missing, file `fix-quickmerge-sentinel` sub-plan and block this plan                                                                                                                                                                                                                                                                      |
| Per CLAUDE.md "Pushes to live-defi-rollout / feat/\* → NO remote CI" — v2 still won't fire on LDR pushes (by design per canonical flow) | This is expected per the new canonical; LDR-side validation via sentinel + local QG. No regression                                                                                                                                                                                                                                                                        |

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` (Phase 5 update — v2 job key as canonical required check)
- `codex/05-infrastructure/quickmerge-architecture.md` (verify sentinel-write step doc; no edit expected)
- `codex/06-coding-standards/feature-branch-workflow.md` (verify aligned with new canonical; no edit expected)
- `plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md` (Phase 5 close-out)
- `CLAUDE.md` § "CI Verification After Every Push" (Phase 5 — 1-line v2 pointer if needed)

## Out of scope (deferred — named successors required)

- **Cloud Build / Artifact Registry side** of canonical (step 7 of operator's flow) — covered by separate
  cloud-build-on-main-canonical plan (file as needed in Phase 0 if not already present)
- **semver-agent + staging-to-main.yml** rollout — already canonical per the codex doc; no change
- **Removing v1 `python-quality-gates.yml` from PM** — held until GH Support clears the cache; named successor:
  `cleanup_v1_quality_gates_workflows_<TBD>.md`

## Provenance

Operator chat 2026-05-29 (slot 1 worktree `.tabs/1/`). Canonical flow operator-stated verbatim in chat. Built on top of
issue doc `workspace_qg_ci_startup_failure_2026_05_26.md` (slot-1 May-26/27 investigation + GH Support ticket #4422570).
