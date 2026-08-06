---
doc_type: issue
title:
  "strategy-service LDR→main promotion: quality-gates-v2 'red' on promote PR #490 was a CI infra flake (Post-Cache
  teardown canceled; both QG legs passed), AND the promotion is deadlocked by a broken main-backmerge-to-ldr on main
  (references notify-slack.yml that only exists on LDR)"
summary: >-
  Escalation agt-5709e0 (wall_type ldr_qg_failure, strategy-service, promote PR #490). (1) Root cause of the failing run
  30949045415 is NOT a code break: both QG slices (checks 92126303871, tests 92126303949) show the "Run quality gates
  (leg …)" steps as ✓ exit-0; the only failing step in each is "Post Cache uv package cache" — the actions/cache
  teardown that packed the uv cache for ~1h20m (04:16→05:37Z) then was canceled ("The operation was canceled"). LDR's
  quality-gates-v2 has been GREEN since (31059776456 @08-06 00:27, 31035314764, 31021886219). (2) The CURRENT promotion
  PR #495 (head = LDR 4733a7e7) was `dirty` on pyproject.toml: main carried a stale squash-promoted
  `unified-api-contracts>=0.92.0` while LDR raised the floor to `>=0.95.0` (4cd72b7b). The PM drain bot
  (unified-trading-pm/.github/workflows/ldr-to-main-promote.yml) leaves non-manifest conflicts to main-backmerge-to-ldr,
  which is DEAD: main's copy of main-backmerge-to-ldr.yml references `./.github/workflows/notify-slack.yml` (added on
  LDR at ca00c76e 08-05 18:53, never promoted to main) → the reusable-workflow ref fails validation → backmerge fails at
  0s on every main push (30982629505 @08-05 06:48, 30949047138 @08-04 20:42) → main→LDR reconcile never runs → promote
  conflict never clears → LDR→main stuck. FIX SHIPPED: resolved the promote conflict on the promote branch in favor of
  LDR (`>=0.95.0`) and pushed merge commit 6ef522d3 to `promote/strategy-service/4733a7e7e8fe` (resulting tree == LDR
  tree, verified `git diff` empty); PR #495 now `mergeable: true`. The push fired pull_request:synchronize → v2 run
  31074521897 queued on 6ef522d3 (tree identical to LDR which already passed v2 → expected green). Remaining:
  sit-gate/fleet-green (ruleset require-quality-gates 13787628 requires BOTH quality-gates-v2 AND sit-gate/fleet-green)
  is a fleet signal recovering (full-workspace-sit run 31074341114 pending).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ci-failures, quality-gates, promotion, backmerge, ldr-main, escalation, infra-flake, deadlock]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/devops-ci-walls.md,
    plans/active/issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md,
  ]
created: 2026-08-06
author: slot-15 (cicd escalation agt-5709e0)
last_updated: 2026-08-06
parent_epic: infrastructure_master
resolved_by:
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: cicd
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    cicd escalation agt-5709e0,
    wall_type ldr_qg_failure,
    failing run https://github.com/IggyIkenna/strategy-service/actions/runs/30949045415,
  ]
context_scope:
  [
    strategy-service/pyproject.toml,
    strategy-service/.github/workflows/main-backmerge-to-ldr.yml,
    strategy-service/.github/workflows/notify-slack.yml,
    unified-trading-pm/.github/workflows/ldr-to-main-promote.yml,
    unified-trading-pm/.github/workflows/ldr-to-main-promote-fleet.yml,
  ]
---

# strategy-service LDR→main: QG "red" was infra flake; promotion deadlocked by broken backmerge on main

## What I found

### 1. The gate failure (the wall) — CI infra flake, NOT a code break

Failing run 30949045415 (promote PR #490, head `678c9269e2ae`). Both QG slices:

- QG slice (checks) job 92126303871 — `✓ Run quality gates (leg checks)` (exit 0); `X Post Cache uv package cache`.
- QG slice (tests) job 92126303949 — `✓ Run quality gates (leg tests)` (exit 0); `X Post Cache uv package cache`.

The only failing step in each slice is the actions/cache POST-teardown: the uv-cache `tar --use-compress-program zstdmt`
ran from 04:16:33Z and was canceled at 05:37:31Z ("##[error]The operation was canceled.") — i.e. the runner teardown
hung ~1h20m then got killed. The gates themselves passed on their merits. LDR's `quality-gates-v2` has been green since
(latest 31059776456 @ 2026-08-06 00:27 on the current LDR head; also 31035314764, 31021886219). No code fix exists or is
needed on live-defi-rollout for this failure. (The `⚠️ 7 basedpyright error(s)` line in the checks log is a non-enforced
warning — `BASEDPYRIGHT_MAX_ERRORS` is not set in this repo's gate, so it does not fail the leg.)

### 2. The current promotion PR #495 — was `dirty`, now resolved

PR #490 (head 678c9269e2ae) merged 08-04 20:41:57Z (squash `9be1e2c6`). The current promotion is **PR #495** (head =
current LDR `4733a7e7`, base main `19565cd3`). It was `mergeable_state: dirty` on exactly one file: `pyproject.toml` —
main `unified-api-contracts>=0.92.0,<1.0.0` vs LDR `>=0.95.0,<1.0.0` (LDR raised the floor at
`4cd72b7b chore(deps): re-pin unified-api-contracts to 0.95.0 (major/breaking floor)`). main is a projection of LDR, so
LDR's floor is the SSOT; the correct promoted result carries `>=0.95.0`.

### 3. The deadlock (why the promotion was stuck for ~23h)

The PM drain bot (`unified-trading-pm/.github/workflows/ldr-to-main-promote.yml`, every */15) handles a `dirty` promote
PR by an inline Guard-2 reconcile for `workspace-manifest.json`-only conflicts; for **non-manifest** conflicts it prints
"leaving to main-backmerge-to-ldr". But strategy-service's `main-backmerge-to-ldr.yml` **on main** references the
reusable workflow `./.github/workflows/notify-slack.yml`, which exists only on LDR (added at `ca00c76e`, 08-05 18:53,
never promoted). A missing reusable-workflow reference fails validation at 0s ("This run likely failed because of a
workflow file issue") → backmerge dead → main→LDR reconcile never runs → the pyproject conflict never clears → every
promote PR stays dirty. Confirmed: backmerge run 30982629505 (08-05 06:48, 0s) and 30949047138 (08-04 20:42, 0s) both
failed; last working backmerge was 30915458024 (08-04 13:46). Circular: the promote can't merge (conflict) → main never
gets notify-slack.yml → backmerge stays broken → conflict never clears.

## What I did (already shipped)

1. **Resolved the promote conflict** on the promote branch: merged `origin/main` into
   `promote/strategy-service/4733a7e7e8fe`, resolved `pyproject.toml` keeping LDR's `>=0.95.0`, committed
   `chore(promote): resolve pyproject dep floor conflict (keep LDR >=0.95.0)` = **`6ef522d3`**, pushed to the promote
   ref. Verified `git diff 6ef522d3 4733a7e7` is EMPTY (merged tree == LDR tree). PR #495 → `mergeable: true`. (Note:
   first commit attempt was rejected by the pre-commit Conventional-Commits hook — a `Merge …` subject is not a valid
   conventional-commit type; prefix with `chore(promote):`.)
2. The push fired `pull_request: synchronize` → **v2 run 31074521897** is queued on `6ef522d3`. Same tree as LDR which
   passed v2 (31059776456) → expected green.
3. Verified the gate set: branch-protection ruleset `require-quality-gates` (id 13787628, active on ~DEFAULT_BRANCH)
   requires BOTH `Quality Gates (strategy-service) / quality-gates-v2` AND `sit-gate/fleet-green`. Classic protection
   additionally requires quality-gates-v2. `Plan Alignment Agent` failing on the PR is advisory (not in either set).

## Current state + resume here

- LDR quality-gates-v2: **GREEN**. Nothing to fix on live-defi-rollout.
- PR #495: `mergeable: true`, `mergeable_state: blocked` (v2 queued + sit-gate).
- v2 run 31074521897 on `6ef522d3`: was `queued` at last check (glue self-hosted pool slow today — see the host OOM
  incidents of 08-05; LDR v2 runs took 10-12 min when healthy, 1h30m+/2h15m when infra-flaky).
- `sit-gate/fleet-green`: fleet signal, fail-closed on no recent non-cancelled full-workspace-sit run; a
  `full-workspace-sit` run (31074341114) was pending 08-06 05:30Z — outside strategy-service scope; flips when SIT
  completes.

**Remaining (this escalation's tail):** verify 31074521897 completes GREEN; confirm PR #495 gates (v2 + sit-gate) go
green so the drain bot auto-merges; then POST `/api/slots/15/done` for agt-5709e0. If v2 infra-flakes again, re-trigger
(`gh workflow run quality-gates-v2.yml --repo IggyIkenna/strategy-service --ref promote/strategy-service/4733a7e7e8fe`).

## Follow-ups (tracked work, not prose)

- [ ] [CICD] P0. Verify quality-gates-v2 on promote PR #495 (run 31074521897, head `6ef522d3`) completes GREEN; if
      green + sit-gate passes, confirm the drain bot auto-merges the promote. Provenance: agt-5709e0, PR #495.
- [ ] [CICD] P1. Backmerge deadlock on strategy-service `main`: `main-backmerge-to-ldr.yml` references
      `notify-slack.yml` missing on main → 0s failures (30982629505, 30949047138). Self-heals once the promote merges
      (main then carries notify-slack.yml). If the promote stays stuck >1h on sit-gate, either roll `notify-slack.yml`
      to main via a promote, or harden the backmerge template to fail-open when the referenced reusable workflow is
      absent on the base branch. SSOT: /codex/08-workflows/ci-cd-flow.md, rollout via
      `scripts/workflow-templates/rollout-workflow-templates.sh`.

## Lessons / traps (re-learned at cost)

- **The promote gate is NOT just quality-gates-v2.** The `require-quality-gates` ruleset requires `sit-gate/fleet-green`
  too. A "blocked" promote PR can be green on v2 and still not merge while the fleet SIT signal is stale.
- **actions/cache POST-teardown failure ≠ gate failure.** A job can show `X Post Cache uv package cache` (cache pack
  canceled after >1h) while the actual quality-gates step shows `✓`. Judge gate health from the gate step, not the job
  verdict.
- **A reusable-workflow reference to a file missing on the base branch fails the run at 0s** with the generic "workflow
  file issue" message, and it makes the workflow dead for EVERY trigger on that branch until the referenced file lands.
- **Conventional-Commits pre-commit hook rejects `Merge …` subjects.** A merge-commit subject must carry a valid type
  (`chore(promote): …`).
- **The `git branch -D` guardrail hook blocks force-deletes.** Use `git branch -d` (or leave a harmless local branch).
