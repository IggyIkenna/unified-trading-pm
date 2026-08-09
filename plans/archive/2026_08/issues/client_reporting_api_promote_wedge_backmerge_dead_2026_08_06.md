---
doc_type: issue
title: >-
  client-reporting-api promotion wedge: main-backmerge-to-ldr dead on main (validation-fails — notify-slack.yml missing)
  → main/LDR diverge → promote PR #646 CONFLICTING (Dockerfile base-image digest); LDR's CI fixes (notify-slack.yml,
  GH-hosted runner revert) waiting to promote
summary: >-
  During ldr_qg_failure escalation agt-57645a (client-reporting-api#642, failing run 30990644645), confirmed the QG
  failure was a SELF-HOSTED RUNNER infra flake, not a code defect — the "Run quality gates (leg tests)" step PASSED and
  the run died on the "Post Cache uv package cache" step ("self-hosted runner lost communication with the server"). The
  fix (revert to GitHub-hosted runners) is ALREADY on LDR (6e0622b, tracked ✅ in
  self_hosted_runner_public_repo_revert_2026_08_05.md todo 7); PR #642 MERGED (7ee59f8); LDR QG green locally (68s) and
  on CI (31059752380). Root-caused a follow-on PROMOTION WEDGE: main's main-backmerge-to-ldr.yml fails validation
  (zero-job 0s failures) because its notify-failure job references ./github/workflows/notify-slack.yml which is MISSING
  on main (introduced 3155c8e → promoted by d8fe06c) → the backmerge never runs → main(7ee59f8)/LDR(6e0622b) diverge →
  current promote PR #646 (promote/client-reporting-api/6e0622b853a7) is CONFLICTING on Dockerfile (ARG
  BASE_IMAGE_DIGEST: main stale sha256:9c1a… vs LDR current sha256:a27d…) and has NO quality-gates-v2 check + sit-gate
  fail-closed. LDR already carries the exact fixes that would repair main once promoted.
status: open # flipping to resolved + archiving in a SEPARATE follow-up commit, per the flip/mv split HARD RULE
nature: issue
asset_group: [ci, infrastructure]
stage: [meta]
repos: [client-reporting-api]
scope: [engineer, admin]
tags: [ci-cd, promote, backmerge, github-actions, notify-slack, self-hosted-runners, dockerfile]
related:
  - /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md
  - /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md
  - /plans/archive/2026_07/pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md
  - /codex/08-workflows/ci-cd-flow.md
created: "2026-08-06"
author: ikennaigboaka [slot-4·planning]
source: [escalation agt-57645a — ldr_qg_failure, client-reporting-api#642, run 30990644645]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
parent_epic: infrastructure_master
drift_direction: advance-code
resolved_by: plan_reconciler agt-a398c9 2026-08-09
archive_exempt: true # THIS COMMIT ONLY — flip precedes archival per the flip/mv split HARD RULE, see next commit
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    client-reporting-api/.github/workflows/main-backmerge-to-ldr.yml,
    client-reporting-api/.github/workflows/notify-slack.yml,
    client-reporting-api/Dockerfile,
    client-reporting-api/.github/workflows/quality-gates-v2.yml,
    /codex/08-workflows/ci-cd-flow.md,
  ]
---

# client-reporting-api promotion wedge (backmerge dead → #646 conflicting)

## What I found

Dispatched as `ldr_qg_failure` for client-reporting-api promotion PR #642 (failing run
[30990644645](https://github.com/IggyIkenna/client-reporting-api/actions/runs/30990644645)). The wall's gate failure was
**not a code defect**:

- The **"Run quality gates (leg tests)" step PASSED** (✓) on run 30990644645; the job died on **"Post Cache uv package
  cache"** — the self-hosted runner lost comms while tar'ing the uv cache (`/usr/bin/tar: … file changed as we read it`
  for 20 min, then `##[error]The operation was canceled.`; annotation: _"The self-hosted runner lost communication with
  the server."_).
- The fix is **already on LDR**: `6e0622b` "fix(ci): revert to GitHub-hosted runners (public repo, GH Actions
  unmetered)" — tracked ✅ as `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 7.
- **PR #642 MERGED** 2026-08-05T08:49:54Z (merge commit `7ee59f8` = current `origin/main` HEAD). **LDR QG is green**
  locally (`quality-gates.sh --no-fix` at `6e0622b` → ALL QUALITY GATES PASSED, 68s) and on CI (run 31059752380,
  2026-08-06T00:27Z, all slices success).

The wall itself is resolved. But the LDR→main **promotion is wedged**, blocking the above fixes from reaching main:

1. **main-backmerge-to-ldr.yml on main is INVALID → the backmerge is dead** (zero-job, 0s, `conclusion: failure` runs:
   30945927557 20:01Z 08-04, 30963556930 00:31Z 08-05, 30990648518 08:49Z 08-05). Cause: the `notify-failure` job does
   `uses: ./.github/workflows/notify-slack.yml`, and **`notify-slack.yml` does NOT exist on main** (it exists only on
   LDR, added by `e901dd3` 2026-08-05, un-promoted). A missing reusable-workflow reference fails the whole workflow at
   validation → GitHub records a run with no jobs. Introduced by `3155c8e` (08-04 19:40Z) → carried to main by the
   `d8fe06c` promote (08-04 20:01Z) — exactly the first 0s failure.
2. **Because the backmerge never runs, main and LDR diverge** (merge-base `bc0e517`), so the current promote PR **#646**
   (`promote/client-reporting-api/6e0622b853a7`) is `mergeable: CONFLICTING` on **Dockerfile**: `ARG BASE_IMAGE_DIGEST`
   — main `sha256:9c1a…` (stale) vs LDR `sha256:a27d…` (current, from 154ab79/1cfd5c1).
3. **#646 has no quality-gates-v2 check** (merge-ref unavailable on a conflicting PR → workflow can't check out) and
   **sit-gate/fleet-green FAIL** (fail-closed — no informative full-workspace SIT in last 10). label-check passes.

**Main-only content is exactly the 3 promote squash commits** (`7ee59f8`, `9e7873f`, `d8fe06c`) — all LDR-content
duplicates — so LDR is authoritative for the Dockerfile resolution; nothing on main would be lost by taking LDR's side.

## Why it matters

The promotion PR is the ONLY path for LDR's CI fixes (`e901dd3` notify-slack.yml, `6e0622b` GH-hosted runner revert,
`154ab79` Dockerfile digest) to reach main. While #646 stays CONFLICTING, main keeps its broken backmerge (validation
failure) + stale Dockerfile digest, and every client-reporting-api LDR→main gate stays red — the exact class of
`ldr_qg_failure` wall this slot was dispatched for.

## Recommended resolution

Dispatch a **merge_conflict wall** for #646 (or fold into the fleet recovery):

1. Resolve #646's Dockerfile conflict taking **LDR's** digest (`sha256:a27d…`) — LDR is authoritative (main-only commits
   are all promote squashes of LDR content).
2. With the PR mergeable, quality-gates-v2 re-triggers (PM is public again — the 2026-08-06 visibility incident is
   reverted); it runs the LDR tree which is green, so it should pass.
3. sit-gate/fleet-green needs a green full-workspace SIT run (fleet-wide — tracked by the active CI recovery).
4. Once #646 merges, main gains `notify-slack.yml` → `main-backmerge-to-ldr.yml` validates again → the backmerge resumes
   and the divergence closes permanently.

Note: `shared_ci_workflow_repo_extraction_2026_08_06.md` (wave 3, `client-reporting-api`) is the durable follow-up that
moves notify-slack.yml to the shared `unified-trading-ci` repo; this issue is the immediate unblock until then.

## Resolution (2026-08-09, plan_reconciler agt-a398c9 — infra tranche)

**This doc had ZERO `- [ ]`/`- [x]` checkboxes anywhere — the "Recommended resolution" above was plain numbered prose,
invisible to `regen_backlog_from_plan.py`'s checkbox-driven AO dispatch despite `assigned_vm: planning` + `priority: P1`
(independently caught by 2 hunters this run, cross-referenced against
`zero_checkbox_sweep_all_tranches_2026_07_31.md:141`'s prior "NEW — unclassified" flag). Converting to real todos below
— but live re-verification (not the stale 2026-08-06 snapshot above) shows the underlying wedge is now **RESOLVED**, not
still-open:

- [x] ✅ [VERIFY] P1. **Confirm PR #646's fate and current main↔LDR relationship.** `gh pr view 646` shows
      `state: CLOSED` (not merged) — superseded, not landed. `gh pr list --search "chore(promote)"` shows **zero** open
      promote PRs for client-reporting-api today. `gh api .../compare/main...live-defi-rollout` shows
      `ahead_by: 287, behind_by: 0` — main is a pure ancestor of LDR (287 commits behind), no longer carrying unique
      diverging commits the way the original 3-commit conflict described. The specific #646 conflict this doc was
      written around no longer exists as an open, actionable PR.
- [x] ✅ [VERIFY] P1. **Confirm whether `main-backmerge-to-ldr.yml` is still dead on main.** It is NOT —
      `gh run     list --workflow main-backmerge-to-ldr.yml --branch main` shows 5 consecutive `conclusion: success`
      runs as recently as 2026-08-09T00:18:47Z. The zero-job 0s validation-failure pattern this doc describes is gone.
- [x] ✅ [VERIFY] P1. **Root-cause check: does main's copy of `main-backmerge-to-ldr.yml` still reference the missing
      `notify-slack.yml`?** No — `gh api .../contents/.github/workflows/main-backmerge-to-ldr.yml?ref=main` + grep for
      "notify" returns zero hits; the broken `uses: ./.github/workflows/notify-slack.yml` reference this doc root-caused
      is gone from main's copy of the workflow. `notify-slack.yml` itself still does not exist as a standalone file on
      main (still 404) — but nothing on main references it anymore, so that's no longer a defect.
- [x] ✅ [VERIFY] P1. **Identify what fixed it.** `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 13 (`[x]`
      DONE) — "Wave 3: client-reporting-api..." — shipped `client-reporting-api@6b09fcd`, exactly the durable follow-up
      this doc's own "Note" above named as the eventual fix. The wedge was closed by that sibling plan, not by anything
      dispatched from this doc.

**Net: no remaining live work.** All 4 todos above are closure-verification, not net-new work — filed as real todos (not
left as prose) per this run's zero-checkbox-sweep obligation, then immediately closed with today's evidence. Doc has 0
open items, is unlocked (`locked_by:` blank) — archived this same run (6-step ritual). **Note for whoever next touches
this doc**: it carries `asset_group: [ci, infrastructure]`, and `ag_closeout_audit_ci_parked_2026_08_08.md`
independently flagged it as likely ci-owned content pending a retag decision it deliberately deferred
("non-owning-tranche-race caution") — that retag question is still open and unrelated to this archival; the doc's
location (now `plans/archive/`) doesn't block a future retag of its `asset_group` frontmatter.

## Evidence

- Failing wall run: `gh run view 30990644645` — `QG slice (tests)` step "Run quality gates (leg tests)" ✓, failure on
  "Post Cache uv package cache" (runner lost comms), run canceled 2026-08-05T10:03:46Z.
- Backmerge validation-failure runs (zero jobs, 0s): 30945927557 / 30963556930 / 30990648518.
- `notify-slack.yml` present on LDR (e901dd3), absent on main (`git ls-tree origin/main .github/workflows/`).
- Merge-tree reproduce: `git merge-tree --write-tree origin/main origin/promote/client-reporting-api/6e0622b853a7` →
  `CONFLICT (content): Merge conflict in Dockerfile`.
- LDR QG green: local `quality-gates.sh --no-fix` PASSED (68s) at `6e0622b`; CI run 31059752380 (all slices success).
- PR states: #642 `MERGED` (7ee59f8), #646 `mergeable=CONFLICTING`, checks sit-gate FAIL / label-check pass / QG-v2
  absent.

- **context-scout 2026-08-06**: populated context_scope.
