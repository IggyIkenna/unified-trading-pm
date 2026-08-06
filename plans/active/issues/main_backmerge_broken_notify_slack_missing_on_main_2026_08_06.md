---
doc_type: issue
title: >-
  notify-slack.yml missing on main makes main-backmerge-to-ldr fail to LOAD, so main diverges and every LDR→main promote
  PR goes CONFLICTING (v2 never reported) — fleet-wide
summary: >-
  Found while resolving ldr_qg_failure escalation agt-e8cf53 (slot 16, 2026-08-06) for batch-live-reconciliation-service
  (quality-gates-v2 red on promote PR #302; that failure was an infra cancellation of the QG checks-slice job on the
  overloaded self-hosted glue runner — already fixed by LDR commit 437d630 reverting to GitHub-hosted runners; LDR QG
  green). The CURRENT promote PR #307 (head = LDR 437d630) was stuck mergeable=CONFLICTING with quality-gates-v2 never
  reported. Root cause of the conflict: `main-backmerge-to-ldr.yml` on main (promoted via PR #302 = dcdf261909cf)
  references `./.github/workflows/notify-slack.yml` (line 437), but notify-slack.yml exists ONLY on live-defi-rollout
  (added by LDR commit 288708e "fix(ci): add missing notify-slack.yml reusable workflow", never promoted to main). A
  reusable-workflow `uses:` pointing at a file absent on main makes the workflow fail to LOAD on main — the last
  main-backmerge-to-ldr run (30960939336, 2026-08-04 23:43:22Z, immediately after PR #302 merged) failed with "log not
  found", and NO subsequent runs fire on update-dependency-version pushes to main. main therefore diverges from LDR
  (main's promote-merge 4b7f8ac1 + version bumps are never back-merged), so every subsequent promote PR
  (batch-live-reconciliation-service #303–#307) is mergeable=CONFLICTING; GitHub suppresses pull_request workflows on a
  conflicting PR → quality-gates-v2 never reported → promote deadlocked. FLEET-WIDE: the 2026-08-06 05:30
  ldr-to-main-promote-fleet tick reported SIX repos CONFLICTED (alerting-service, execution-service, strategy-service,
  client-reporting-api, batch-live-reconciliation-service, deployment-service) — all promoted the dcdf261909cf-era
  backmerge workflow that references notify-slack.yml; conflict-resolution agents were dispatched for all six.
summary_continued: >-
  Self-heal path: the conflict-resolution agent back-merges main into LDR (additive); once a promote lands,
  notify-slack.yml reaches main and the backmerge workflow loads again, reconciling main→LDR going forward. Durable
  options beyond that: (1) promote notify-slack.yml to main as part of the next successful LDR→main promote (the
  self-heal), or (2) make main-backmerge-to-ldr.yml self-contained (inline the notify job instead of `uses:
  ./.github/workflows/notify-slack.yml`). Verified current as of 2026-08-06 05:45Z: notify-slack.yml still absent on
  origin/main; backmerge still not running. Re-check after the conflict-resolution agents land before considering this
  resolved.
status: active
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  - unified-trading-pm
  - batch-live-reconciliation-service
  - alerting-service
  - execution-service
  - strategy-service
  - client-reporting-api
  - deployment-service
scope: [engineer]
tags: [ci-cd, promotion, ldr-main, backmerge, notify-slack, workflow-load, merge-conflict, quality-gates-v2]
related: [/codex/08-workflows/ci-cd-flow.md, /codex/15-runbooks/devops-ci-walls.md]
created: 2026-08-06
---

# main-backmerge-to-ldr broken on main (notify-slack.yml missing) → LDR→main promotes CONFLICTING fleet-wide

## Symptom (the wall that surfaced it)

`ldr_qg_failure` agt-e8cf53: quality-gates-v2 failed on batch-live-reconciliation-service promote PR #302 (run
30960936027). Root cause of THAT failure was infra, not code — the QG slice (checks) job was cancelled ("The operation
was canceled") after the checks themselves passed in 33s, on the overloaded self-hosted glue runner (the
2026-07-27/08-04 fleet QG capacity crisis). Already fixed on LDR by `437d630` "fix(ci): revert to GitHub-hosted
runners". LDR full QG green (run 31059749850 on 437d630).

The live promote PR #307 (head = LDR 437d630) was instead stuck on `mergeable: CONFLICTING` with `quality-gates-v2`
**never reported** — a different blocker. Re-triggering v2 on the promote head (workflow_dispatch → run 31074608149)
went green (QG slice checks + aggregate quality-gates-v2 both SUCCESS), but the PR still cannot merge while CONFLICTING.

## Root cause chain

1. `main-backmerge-to-ldr.yml` on **main** (the version promoted via PR #302 = dcdf261909cf) references
   `uses: ./.github/workflows/notify-slack.yml` at line 437.
2. `notify-slack.yml` exists **only on live-defi-rollout** (added by `288708e` "fix(ci): add missing notify-slack.yml
   reusable workflow"; never promoted to main because the promote that would carry it is itself blocked).
3. A reusable-workflow `uses:` pointing at a file absent on the branch makes the workflow fail to **LOAD** on main: the
   last backmerge run (30960939336, 2026-08-04 23:43:22Z, right after PR #302 merged) failed with "log not found", and
   no backmerge runs fire since — despite `update-dependency-version` pushing to main repeatedly.
4. main therefore diverges from LDR (main's promote-merge `4b7f8ac1` + version bumps never back-merged into LDR).
   Verified: `git merge-base --is-ancestor origin/main HEAD` = NO.
5. Every LDR→main promote PR at a diverged main goes `mergeable=CONFLICTING`; GitHub does not run `pull_request`
   workflows on a conflicting PR → required `quality-gates-v2` never reports → promote deadlocked.

## Evidence

- Backmerge failed run: `30960939336` (conclusion failure, "log not found", 2026-08-04 23:43:22Z).
- Last successful backmerge: `30935541189` (2026-08-04 17:47:30Z, pre-PR-302).
- notify-slack.yml on main: absent (`git cat-file -e origin/main:.github/workflows/notify-slack.yml` → missing).
- Backmerge workflow ref: `git show origin/main:.github/workflows/main-backmerge-to-ldr.yml | grep notify-slack` →
  line 437.
- Three-way merge conflict (base 413816d): `main-backmerge-to-ldr.yml` runs-on + `Dockerfile` digest, "changed in both".
- Fleet tick 2026-08-06 05:30: Slack summary "1 promoted, 14 blocked, **6 conflicted**" — repos: alerting-service,
  execution-service, strategy-service, client-reporting-api, batch-live-reconciliation-service, deployment-service;
  "Conflict resolver dispatched for: alerting-service execution-service strategy-service client-reporting-api
  batch-live-reconciliation-service deployment-service".

## Resolution path

- The dispatched conflict-resolution agents back-merge main into LDR (additive, LDR wins the 2-file conflict — LDR's
  versions are the current/deliberate ones). Next promote then lands cleanly, carrying notify-slack.yml to main, after
  which main-backmerge-to-ldr loads and self-heals.
- v2 on the current promote head is already green (run 31074608149) — the remaining merge blockers are the CONFLICT
  (being resolved) + `sit-gate/fleet-green` fail-closed (full-workspace-sit runs cancelled fleet-wide — see
  `/plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`; the fleet promoter auto-retriggers SIT
  when red).
- Durable fix option (beyond self-heal): make `main-backmerge-to-ldr.yml` self-contained (inline the notify job) so a
  reusable-file gap on main can never break backmerge loading again.
