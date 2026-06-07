---
title: CI canonical v2 migration — ghost-workflow workaround across PM/UAC/UTL (+5)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
created: 2026-05-29
completion_gates:
  code: C5
  deployment: D3
  business: B3
repo_gates:
  - repo: unified-trading-pm
    code: C0
  - repo: unified-api-contracts
    code: C0
  - repo: unified-trading-library
    code: C0
  - repo: alerting-service
    code: C0
  - repo: ml-service
    code: C0
  - repo: features-service
    code: C0
  - repo: batch-live-reconciliation-service
    code: C0
  - repo: execution-service
    code: C0
  - repo: instruments-service
    code: C0
  - repo: deployment-ui
    code: C0
related_plans:
  - plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md
  - plans/active/tradfi_massive_dual_source_2026_05_28.md
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# CI canonical v2 migration — ghost-workflow workaround

> **✅ COMPLETE (2026-06-02, via `scripts/repo-management/verify_branch_protection_check_names.py`)** — **17/17 repos
> now require `…/quality-gates-v2`; `ALL RULESETS CONSISTENT: True`.** The last holdout `deployment-ui` was finished
> this turn (decoupled v2 callee + operator-directed FF/force promotion of main+staging to LDR + ruleset cutover; see
> Phase 4.5). deployment-ui's stale v1 ghost chain (`workspace-qg.yml` + `ui-quality-gates.yml`) was also deleted from
> all branches 2026-06-02, and the two `backup/*-pre-ff-20260602` refs deleted after the promotion settled. The only
> remaining open item is the Phase 5 PM v1-file deletion (gated on GH Support #4422570).
>
> _History (2026-06-01 → 2026-06-02)_: the 2026-06-01 "8 repos still on v1" reality-check went stale fast — by
> 2026-06-02 16/17 already required `…/quality-gates-v2`. The previously-flagged holdouts (`batch-live-reconciliation`,
> `client-reporting-api`, `deployment-api`, `ibkr-gateway-infra`, `market-data-processing`, `system-integration-tests`,
> `trading-agent-service`) have all rotated to v2 since.
>
> **`deployment-ui` — FINISHED 2026-06-02.** Root cause was that its TS/Vite v2 caller `quality-gates-v2.yml` reused the
> SAME callee `ui-quality-gates.yml` (job `quality-gates`) as the v1 `workspace-qg.yml`, so both emitted the identical
> `…/quality-gates` check (no distinct v2 suffix + v1 ghost collision). Fix: gave the v2 caller its own callee
> `ui-quality-gates-v2.yml` (job `quality-gates-v2`) — deployment-ui@0d2479c — then, on operator directive, FF'd `main`
>
> - force-promoted `staging` up to LDR (they were 23 / 217 commits behind; promotion automation was stalled) and rotated
>   rulesets `13787657` (main) + `13788744` (staging) to require `…/quality-gates-v2`. Verified: `main` push run
>   26800322667 → `Quality Gates (deployment-ui) / quality-gates-v2` **success**; classic-main protection restored. The
>   normal LDR→staging→main flow now resumes. Details + reversibility in Phase 4.5. Cross-ref:
>   `plans/audit/results/infrastructure_master_audit_2026_06_01.md` + `cicd_contract_hardening_2026_06_01.md` Phase 1+6.

## Overview

Rolls every affected workspace repo onto the new canonical CI flow (`codex/08-workflows/ci-cd-flow.md`) AND applies a v2
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
   `workflow_call:` signature OR inline the QG steps directly into the v2 caller (no reusable indirection)
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

| Layer                                      | Status                      | Note                                                                                                                                      |
| ------------------------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Canonical CI codex doc                     | ✅ shipped 2026-05-29       | `codex/08-workflows/ci-cd-flow.md` § three-tier + two-pass + sentinel model                                                               |
| PM `python-quality-gates.yml` real content | ✅ correct on disk          | Bad comment reverted in `7ca446080`                                                                                                       |
| PM main branch protection                  | ✅ rotated 2026-05-29       | Required check now `quality-gates-v2` (was `quality-gates`)                                                                               |
| GH Support ticket                          | 🟡 open                     | #4422570 filed 2026-05-27, awaiting cache clear                                                                                           |
| v2 caller workflow on PM                   | ✅ shipped 2026-05-29       | `quality-gates-v2.yml` on LDR @a9d340df; not yet merged to main                                                                           |
| v2 callee workflow on PM                   | ✅ shipped 2026-05-29       | `python-quality-gates-v2.yml` on LDR @a9d340df; not yet merged to main                                                                    |
| Required-check rotation (all 18 branches)  | ✅ done 2026-05-29          | `quality-gates` → `quality-gates-v2` across all 9 service repos + PM                                                                      |
| Workspace-wide canonical-check state       | ✅ 17/17 on v2 (2026-06-02) | Verifier `ALL RULESETS CONSISTENT: True`; `deployment-ui` finished — decoupled v2 callee + operator FF/force promotion + ruleset rotation |

## Phased execution

### Phase 0 — Pre-flight: confirm canonical doc + branch protection access (0.25 day)

- [x] ✅ [AUDIT] P0. Read `codex/08-workflows/ci-cd-flow.md` end-to-end — 292 lines. Covers three-tier branch model,
      two-pass sentinel model, workspace-qg triggers excluding LDR, staging-first PR target. Plan recipe matches doc.
- [x] ✅ [AUDIT] P0. Admin perms confirmed on PM/UAC/UTL — `gh api` returns `admin=True` for all three.
- [x] ✅ [AUDIT] P0. Confirm `.qg_last_passed_sha` sentinel format expected by quickmerge —
      `bash     scripts/quickmerge.sh --help 2>&1 | head -30` should mention it. If missing in quickmerge
      implementation, file separate fix-quickmerge issue and block this plan on it. — CONFIRMED:
      `scripts/quickmerge.sh:819` (`_SENTINEL=".qg_last_passed_sha"`) reads the sentinel in `--agent` mode;
      `scripts/quality-gates-base/base-service.sh:2411` writes `git rev-parse HEAD` to `.qg_last_passed_sha` on a
      COMPLETE run (all gates on: tests+lint+codex, no --quick/--skip flags). Format: full SHA, trimmed on read
      (`tr -d '[:space:]'`). No separate fix-quickmerge issue needed.

### Phase 1 — PM (1 day)

- [x] ✅ [SCRIPT] P0. **Step 0.5 — Resolve pre-existing PM dep-alignment failure** (Phase 0 side-finding). Run
      `python scripts/manifest/generate-derived-manifest.py` + `check-dependency-alignment.py --json`. If internal-only
      drift: `fix-internal-dependency-alignment.py --apply`. If external drift:
      `fix_external_dependency_alignment.py --apply`. Verify Stage 1.5 of quickmerge passes before proceeding to Step 1.
      Commit the manifest fixes as a SEPARATE quickmerge / admin-merge before the v2 workflow files (clean separation of
      concerns). — RESOLVED by outcome: PM `main` `quality-gates-v2` is GREEN (run on 2026-06-02 03:48, `main push` →
      success), and QG Stage 1.5 = dep-alignment, so a green main QG proves dep-alignment passes. (backfilled
      2026-06-02)

- [x] ✅ [SCRIPT] P0. Run `bash scripts/quality-gates.sh` IN FULL (no skip flags) in PM at current HEAD. Verify exit 0 +
      `.qg_last_passed_sha` file written + SHA matches `git rev-parse HEAD`. — Done by outcome: PM v2 files merged to
      `main` and `quality-gates-v2` reports `success` on main pushes; sentinel-gated quickmerge landed them. (backfilled
      2026-06-02)
- [x] ✅ [SCRIPT] P0. Stage current working-tree changes (none expected post-slot-reset). Create v2 workflow files:
  - `.github/workflows/quality-gates-v2.yml` — caller, triggers push+PR on [main, staging], concurrency group
    `quality-gates-v2-${{ github.ref }}`, job key `quality-gates-v2`, calls v2 callee, `dispatch-cloud-build` job needs
    `quality-gates-v2` — unified-trading-pm@a9d340df
  - `.github/workflows/python-quality-gates-v2.yml` — reusable callee, job key `quality-gates-v2`, includes
    `SLACK_CI_WEBHOOK_URL` secret + failure notification step — unified-trading-pm@a9d340df
  - DO NOT delete v1 files yet — leave them as ghost-targets so the cache doesn't poison v2 via shared registration
- [x] ✅ [SCRIPT] P0.
      `bash scripts/quickmerge.sh "ci(workflows): add v2 caller+callee — escape GHA ghost cache"     --agent --files '.github/workflows/quality-gates-v2.yml .github/workflows/python-quality-gates-v2.yml'`.
      Sentinel verified at quickmerge time → push proceeds → PR to staging → auto-merge. — v2 caller+callee are live on
      PM `main` (live ruleset requires `…/quality-gates-v2`; `main push` runs report `success`). (backfilled 2026-06-02)
- [x] ✅ [SCRIPT] P0. **Branch protection rotation** on PM main+staging via
      `gh api PUT repos/IggyIkenna/unified-trading-pm/branches/{main,staging}/protection`:
  - Removed `quality-gates` from required status checks on both branches
  - Added `quality-gates-v2` as new required status check on both branches
  - All other settings preserved (dismiss_stale=true, required_approving_review_count=1, enforce_admins=false,
    restrictions=null) — 18/18 branches rotated 2026-05-29
- [x] ✅ [VERIFY] P0. PR #83 (TradFi plan) merges. Confirm via `gh pr view 83 --repo IggyIkenna/unified-trading-pm`. —
      MERGED 2026-05-29 18:11:35Z (verified `gh pr view 83` → state MERGED). (backfilled 2026-06-02)
- [x] [VERIFY] P0. Subsequent PR to PM main triggers v2 check, reports success (not startup_failure). If v2 ALSO ghosts,
      fall back to Plan-B (inline QG steps in v2 caller, no reusable). — PR #93 (fix/pm-ci-self-clone) merged
      2026-05-29; run 26654854795 passed ✅ (V=12/12).

### Phase 2 — UAC (0.5 day)

- [x] ✅ [SCRIPT] P0. Same recipe as Phase 1 in UAC:
  - Local `quality-gates.sh` full run → sentinel
  - Add `.github/workflows/quality-gates-v2.yml` to UAC. UAC's caller references PM's v2 callee at LDR ref (just like v1
    references python-quality-gates.yml at LDR)
  - Quickmerge per canonical flow
  - Done by outcome: UAC `main` requires `…/quality-gates-v2` (live ruleset) and `main push` run 2026-06-01 18:18 →
    `success`; staging-v2 PR also green. (backfilled 2026-06-02)
- [x] ✅ [SCRIPT] P0. UAC main+staging branch protection rotation: dropped `quality-gates` → added `quality-gates-v2` on
      both branches. staging had quality-gates-v2 from 18-branch sweep 2026-05-29; main rotation applied 2026-05-29
      (main had no prior required check — was missing from sweep).
- [x] ✅ [VERIFY] P0. PR #50 (TradFi universe expansion) merges. Confirm clean. — MERGED 2026-05-29 18:08:21Z (verified
      `gh pr view 50` → state MERGED). (backfilled 2026-06-02)
- [x] ✅ [VERIFY] P0. Next UAC PR triggers v2 cleanly. — UAC `live-defi-rollout` PR run 2026-06-01 18:13 →
      `quality-gates-v2` success (no startup_failure). (backfilled 2026-06-02)

### Phase 3 — UTL (0.5 day)

- [x] ✅ [SCRIPT] P0. Same recipe as Phase 1+2 in unified-trading-library:
  - Local `quality-gates.sh` full run → sentinel
  - Add v2 caller workflow
  - Quickmerge
  - Done by outcome: UTL requires `…/quality-gates-v2` (live ruleset); v2 green on `staging push` 2026-06-01 15:47 +
    `workflow_dispatch` 2026-06-02 04:45. (backfilled 2026-06-02)
- [x] ✅ [SCRIPT] P0. UTL main+staging branch protection rotation: dropped `quality-gates` → added `quality-gates-v2`
      2026-05-29 (18-branch sweep).
- [x] ✅ [VERIFY] P0. Next UTL PR triggers v2 cleanly. — `quality-gates-v2` registers + runs (green `workflow_dispatch`
      2026-06-02 04:45; green `staging push` 2026-06-01 15:47); no startup_failure on the v2 chain. (backfilled
      2026-06-02)

### Phase 4 — Rollout to remaining 7 ghost-affected repos (1.5 days)

Apply the same v2 recipe to alerting-service, ml-service, features-service, batch-live-reconciliation-service,
execution-service, instruments-service, deployment-ui. Order by risk (lowest first):

- [x] ✅ [SCRIPT] P1. alerting-service — cherry-picked v2 from LDR + ruleset 13787630 rotated to `quality-gates-v2`. PR
      #16 MERGED 2026-05-29 18:40:36Z.
- [x] ✅ [SCRIPT] P1. ml-service — v2 created from scratch (template from alerting-service@main). PR #1 MERGED
      2026-05-29 18:43:59Z. No ruleset (PRs unblocked already).
- [x] ✅ [SCRIPT] P1. features-service — v2 created from scratch, target=`live-defi-rollout` (this repo has no `main`
      branch). PR #1 MERGED 2026-05-29 18:45:09Z.
- [x] ✅ [SCRIPT] P1. batch-live-reconciliation-service — v2 created from scratch + ruleset 13787691 rotated to
      `quality-gates-v2`. PR #6 MERGED 18:41:44Z (with empty file due to shell glob bug); PR #7 MERGED 18:45Z fixed the
      empty file with proper template.
- [x] ✅ [SCRIPT] P1. execution-service — cherry-picked v2 from LDR. PR #202 MERGED 18:42:29Z. Ruleset 13647462 already
      enforces `check-staging-lock` (not `quality-gates`) — hygiene follow-up tracked in
      `plans/active/issues/check_staging_lock_ruleset_hygiene_2026_05_29.md`.
- [x] ✅ [SCRIPT] P1. instruments-service — cherry-picked v2 from LDR. PR #388 MERGED 18:42:37Z. Same hygiene follow-up.
- [x] ✅ [SCRIPT] P1. deployment-ui — **canonical on `…/quality-gates-v2` (2026-06-02)**. Decoupled v2 callee
      `ui-quality-gates-v2.yml` (job `quality-gates-v2`) @0d2479c + operator-directed FF/force promotion of main+staging
      to LDR + rotation of rulesets `13787657`/`13788744`. Verified: `main` push run 26800322667 →
      `Quality Gates (deployment-ui) / quality-gates-v2` success; `ALL RULESETS CONSISTENT: True` = 17/17. Full detail
      in Phase 4.5.
- [x] ✅ [VERIFY] P1. PM workflow_dispatch on `quality-gates-v2.yml` ran for 1m15s (run id 26654010496), NOT 0s
      startup_failure. **Option D verified: v2 chain escapes the GitHub ghost cache.** Subsequent runs on PM main are
      now `success` (e.g. 26654998707). Workspace-qg health restored across all 10 repos.

### Phase 4.5 — deployment-ui canonical-suffix completion (the one open repo) (0.25 day) [UI]

> **✅ COMPLETE 2026-06-02.** Decoupled v2 callee built + verified, then (operator-directed) main+staging
> FF/force-promoted to LDR and both rulesets rotated to `…/quality-gates-v2`. deployment-ui is canonical (17/17). Items
> below are ✅; the only residue is the Phase 5 `workspace-qg.yml`/backup-ref cleanup.

- [x] ✅ [SCRIPT] P1. Create `.github/workflows/ui-quality-gates-v2.yml` = copy of `ui-quality-gates.yml` with its job
      id renamed `quality-gates:` → `quality-gates-v2:` (mirrors the python repos' separate-v2-callee pattern). Repoint
      `quality-gates-v2.yml` `uses:` → `./.github/workflows/ui-quality-gates-v2.yml`. — DONE: deployment-ui@0d2479c on
      `live-defi-rollout` (2026-06-02). v1 `workspace-qg.yml` left in place for now (its `…/quality-gates` check goes
      non-required after the rotation; deletion bundled into the cutover below).
- [x] ✅ [VERIFY] P1. Confirm the v2 caller now emits a GREEN `Quality Gates (deployment-ui) / quality-gates-v2` check.
      — DONE: `workflow_dispatch` run **26799741962** on `live-defi-rollout` → job
      `Quality Gates (deployment-ui) /     quality-gates-v2` → **success** (2026-06-02). That run executes the UI
      quality-gates incl. the playwright smoke → satisfies `pw:L2 ✓`. Evidence:
      `deployment-ui@0d2479c | pw:L2 ✓ (run 26799741962) | regression: tests/smoke/`.
- [x] ✅ [SCRIPT] P1. **DONE 2026-06-02 — operator-directed FF/force promotion + ruleset cutover.** Operator directed
      bringing `main`+`staging` up to LDR so the normal CI/CD flow resumes (explicitly authorizing the force-push to
      main — a human-only hard-stop item). Executed reversibly: (0) pushed backup refs
      `backup/{main,staging}-pre-ff-20260602` + saved full ruleset/classic bodies; (1) relaxed classic-main
      (enforce_admins off + PR-reviews removed) + disabled rulesets `13787657`/`13788744`; (2) **FF `main`**
      `f7715ec→0d2479c` (clean, 0 discarded) + **force `staging`** `bf50cdd→0d2479c` (discarded 2 stale promotion/merge
      artifacts — backed up, no original work lost); (3) rotated ruleset `13787657` (main) + `13788744` (staging, kept
      `check-staging-lock`) required context `…/quality-gates` → `…/quality-gates-v2` + re-enabled both `active`; (4)
      restored classic-main (`enforce_admins: True`, PR-reviews, force-pushes off). **Verified**:
      `verify_branch_protection_check_names.py` → deployment-ui main+staging on `…/quality-gates-v2`,
      `ALL RULESETS CONSISTENT: True` = **17/17**; a `main` push run **26800322667** → job
      `Quality Gates (deployment-ui) / quality-gates-v2` → **success** (normal flow confirmed). Follow-up (Phase 5):
      delete the stale `workspace-qg.yml` ghost (now a non-required failing check) + the backup refs once settled.

### Phase 5 — Cleanup + codex updates (0.25 day)

- [ ] [SCRIPT] P1. **BLOCKED-UPSTREAM (GH Support #4422570 open).** Once all repos run cleanly on v2, delete v1 caller
      workflow files in each repo (single quickmerge per repo). Keep the v1 PM callee `python-quality-gates.yml` for now
      to avoid forced GitHub re-validation; remove in a later cleanup once GH Support ticket clears. Named successor:
      `cleanup_v1_quality_gates_workflows_<TBD>.md` (per § Out of scope). Holds until the ghost cache is confirmed
      cleared — premature v1 deletion risks re-poisoning the v2 registration.
- [x] ✅ [CODEX] P1. `codex/08-workflows/ci-cd-flow.md` updated this turn (2026-05-29 EOD) with new section "Canonical
      required check name (post-Option-D, 2026-05-29)" — names `quality-gates-v2` as the workspace canonical,
      cross-references the per-repo matrix in feature-branch-workflow.md, documents v1-cleanup-pending.
- [x] ✅ [CODEX] P1. Update `workspace_qg_ci_startup_failure_2026_05_26.md` with final Option D close-out — DONE
      (verified 2026-06-07): the issue completed its archival flow and now lives at
      `plans/archive/issues/workspace_qg_ci_startup_failure_2026_05_26.md`. Option D (the `quality-gates-v2` canonical
      required-check) is documented in `codex/08-workflows/ci-cd-flow.md` § "Canonical required check name". The only
      residual (v1 PM callee deletion) is the BLOCKED-UPSTREAM item above (GH #4422570), tracked separately.
- [x] ✅ [CLAUDE-MD] P1. Workspace-wide pointer to v2 canonical — DONE (verified 2026-06-07): `cursor-configs/CLAUDE.md`
      § "CI Verification After Every Push" already carries the line **"Required check name (all repos):
      `quality-gates-v2` (v1 `quality-gates`/`workspace-qg` retired 2026-05-29 — see `codex/08-workflows/ci-cd-flow.md`
      § quality-gates-v2)"**. The codex § "Canonical required check name" remains the authoritative source; the 1-line
      CLAUDE.md cross-reference is present.
- [x] ✅ [SCRIPT] P2. deployment-ui post-cutover tidy — **(a) DONE 2026-06-02**: deleted the stale v1 ghost chain
      `workspace-qg.yml` + its now-orphaned callee `ui-quality-gates.yml` (deployment-ui@45627fe; stale comment ref
      fixed @ebb68d3) and FF-propagated the deletion to `main` + `staging` (relax→FF `0d2479c→ebb68d3`→re-enable;
      rulesets back `active` on `…/quality-gates-v2`, classic-main restored). Verified: `workspace-qg` GONE from
      main/staging/LDR; the `main` push now runs ONLY `quality-gates-v2`; `ALL RULESETS CONSISTENT: True` = 17/17. (This
      chain is independent of PM's python-quality-gates ghost / GH #4422570.) **(b) DONE 2026-06-02**: deleted backup
      refs `backup/main-pre-ff-20260602` (was f7715ec) + `backup/staging-pre-ff-20260602` (was bf50cdd) from
      `origin/deployment-ui` after operator confirmed the promotion settled. Target repo: `deployment-ui`.
- [x] ✅ [PLAN] P1. Pre-archival 5-step audit — DONE 2026-06-07 (codex-alignment step verified): Phases 1-4 + 4.5 done
      (deployment-ui canonical, 17/17 rulesets consistent); the codex SSOT `codex/08-workflows/ci-cd-flow.md` §
      "Canonical required check name" reflects what shipped (Option D / `quality-gates-v2`). The two doc P1s above are
      closed. **The plan stays ACTIVE (not yet archived) by design**: the single remaining item is the BLOCKED-UPSTREAM
      v1 PM-callee deletion (GH #4422570) — per the plan-archival HARD RULE we do not archive with an open in-scope
      item. Archive immediately when #4422570 resolves and the v1 callee is deleted.

## Success criteria

| Phase   | Gate                                                         | Verification                                                                      |
| ------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| Phase 1 | PM `quality-gates-v2` reports success on PR + #83 merges     | `gh pr view 83 --repo IggyIkenna/unified-trading-pm` shows MERGED                 |
| Phase 2 | UAC v2 clean + #50 merges                                    | Same pattern                                                                      |
| Phase 3 | UTL v2 clean                                                 | First post-rotation PR reports success                                            |
| Phase 4 | All 10 repos green on v2                                     | `for repo in ...; gh run list --workflow quality-gates-v2 --limit 1`; all succeed |
| Phase 5 | Codex doc updated + issue doc closed + cleanup commit landed | Inventory regenerator passes; archival audit OK                                   |

## Risks + mitigations

| Risk                                                                                                                                    | Mitigation                                                                                                                                                                                                                                                                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v2 also ghosts (cache keys deeper than file path)                                                                                       | Plan-B: inline QG steps in v2 caller, no reusable indirection. One job, no callees                                                                                                                                                                                                                                                                                                                    |
| Agent lacks branch protection admin perms in some repo                                                                                  | Verified 2026-05-29: `gh auth status` shows `IggyIkenna` with `repo` scope; `admin=True` confirmed on PM/UAC/UTL via `gh api repos/.../permissions`. GH_PAT in `central-element-323112/GH_PAT` is the cron-side fallback. Agent does rotations directly via `gh api PUT repos/.../branches/main/protection`. If any P1 repo refuses, fall back to filed-PR + operator-ack for that specific repo only |
| Rollout-quality-gates-ci-workflows.py (or equivalent template-rollout script) overwrites v2 with v1 templates on next run               | Phase 0 audit confirms rollout script exists; if it does, add v2 exception entry first                                                                                                                                                                                                                                                                                                                |
| Race: another agent merges PR with v1 check still required                                                                              | Phase 1's protection-rotation is ordered as: drop v1 → wait for v2 → add v2. Brief window where NO required check exists; minimize by completing same agent turn                                                                                                                                                                                                                                      |
| `.qg_last_passed_sha` sentinel doesn't exist in quickmerge yet                                                                          | Phase 0 audit gates on this; if missing, file `fix-quickmerge-sentinel` sub-plan and block this plan                                                                                                                                                                                                                                                                                                  |
| Per CLAUDE.md "Pushes to live-defi-rollout / feat/\* → NO remote CI" — v2 still won't fire on LDR pushes (by design per canonical flow) | This is expected per the new canonical; LDR-side validation via sentinel + local QG. No regression                                                                                                                                                                                                                                                                                                    |

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
