---
doc_type: issue
title:
  "ci-status-consolidator's [skip ci] commit suppresses the push-triggered main-backmerge-to-ldr, silently starving PM's
  live-defi-rollout manifest cache and stalling the LDR→main fleet-promote gate fleet-wide"
summary: >-
  While resolving a main_ci_red escalation for deployment-service (quality-gates-v2 red on main, fix already green on
  live-defi-rollout via eb131cd raising PYTEST_TIMEOUT/PYRIGHT_TIMEOUT to 300s), the stuck promote PR (#675,
  CONFLICTING) turned out to be a symptom of a deeper, fleet-wide bug: ldr-to-main-promote-fleet.yml is heartbeat
  force-dispatched every ~15 min via `gh workflow run ... --ref live-defi-rollout`
  (scripts/orchestrator/ldr-to-main-promote-heartbeat.sh), so it checks out and reads PM's live-defi-rollout copy of
  workspace-manifest.json — NOT main's copy. ci-status-consolidator.yml (the hourly Firestore→manifest projector)
  commits and pushes its ci_status updates only to main, with a commit message containing `[skip ci]`. GitHub's built-in
  [skip ci] handling suppresses ALL push-triggered workflows for that commit, including main-backmerge-to-ldr.yml's `on:
  push: branches: [main]` trigger — so the consolidator's fix NEVER automatically reaches live-defi-rollout. The
  fleet-promote gate then keeps reading a stale cached ci_status=FAILING off LDR's manifest indefinitely (confirmed:
  deployment-service sat GATE BLOCKED for 3 consecutive ticks — 11:46Z/11:48Z/12:00Z — reading cached='FAILING' even
  ~15-30 min after the consolidator had already flipped main's copy to FEATURE_GREEN at 11:47:56Z). Manually dispatching
  main-backmerge-to-ldr.yml (workflow_dispatch, no push-trigger needed) at 12:03Z immediately fixed it — the next fleet
  tick (12:15Z) read cached='FEATURE_GREEN', closed the stale PR #675 as superseded, and merged a fresh PR #676. This is
  a general defect, not deployment-service-specific: ANY repo whose ci_status flips green via the consolidator (rather
  than via a fresh LDR push, which DOES trigger main-backmerge normally through the OTHER direction... no, backmerge is
  main→LDR only, so this gap is universal) will silently stall its fleet-promote gate until someone happens to manually
  dispatch main-backmerge-to-ldr.
summary_continued: >-
  Two independent fixable angles: (1) drop `[skip ci]` from ci-status-consolidator.yml's commit message (or replace with
  a targeted skip that still allows main-backmerge-to-ldr to fire — e.g. path-filter the backmerge trigger instead of
  relying on repo-wide [skip ci] suppression), or (2) give main-backmerge-to-ldr.yml its own heartbeat dispatch
  (mirroring ldr-to-main-promote-heartbeat.sh) so it doesn't depend solely on the push trigger. Either closes the gap;
  (1) is simpler and directly addresses the root cause (consolidator commits opting out of the one workflow they need to
  reach LDR).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, promotion, ldr-main, manifest-cache, ci-status, backmerge, skip-ci]
related: [/codex/08-workflows/ci-cd-flow.md, /codex/15-runbooks/devops-ci-walls.md]
created: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: cicd
drift_direction: stable
source: agt-368655
resolved_by:
locked_by:
depends_on: []
---

# ci-status-consolidator's `[skip ci]` starves the LDR backmerge — fleet-promote gate can stall indefinitely

## What happened (this escalation)

- Wall: `main_ci_red` escalation (agt-368655) — deployment-service `quality-gates-v2` red on `main`.
- Diagnosis: the real code fix (`eb131cd`, raises `PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT` to 300s under fleet-wide
  self-hosted-runner contention) was already green on `live-defi-rollout` — no code re-fix needed.
- The auto-generated promote PR (#675, base `032a8c0`, opened 07:02Z) had gone `CONFLICTING`/`DIRTY` vs `main` because a
  later promote PR (#674) had already squash-merged past its base.
- The fleet's own "superseded ref cleanup" logic (`scripts/cicd/ldr_to_main_fleet_promote.sh`) is DESIGNED to close a
  stale PR like #675 automatically once the repo's Tier-A `ci_status` gate passes — but it kept reading
  `cached='FAILING'` for 3+ ticks after LDR's own CI had already gone green (11:39:35Z).

## Root cause

1. `ldr-to-main-promote-fleet.yml` is dispatched via `scripts/orchestrator/ldr-to-main-promote-heartbeat.sh` with
   `--ref live-defi-rollout` most ticks (GHA silently drops most `schedule:` ticks — the heartbeat is the documented
   top-up). `actions/checkout` with no explicit `ref:` defaults to `github.ref`, i.e. it checks out **PM's
   `live-defi-rollout` branch**, and reads `workspace-manifest.json` from THAT checkout.
2. `ci-status-consolidator.yml` (hourly Firestore→manifest projector) commits and pushes its `ci_status` update only to
   `main` (`git push origin HEAD` after checking out `main`), with commit message
   `"ci: consolidate ci_status from Firestore [skip ci]"`.
3. GitHub's native `[skip ci]` handling suppresses **every** push-triggered workflow for that commit — including
   `main-backmerge-to-ldr.yml`'s `on: push: branches: [main]` trigger (main-backmerge-to-ldr.yml has NO `schedule:` —
   that was deliberately removed 2026-06-27 in favor of the push trigger + PM's `branch-health.yml` 30-min dispatch, per
   its own top-of-file comment).
4. Net effect: the consolidator's fix to `main`'s manifest has **no automatic path** to `live-defi-rollout`. It sits
   there until either (a) someone manually dispatches `main-backmerge-to-ldr.yml`, or (b) PM's `branch-health.yml`
   happens to tick within its declared 30-min interval (untested here whether that path reliably fires — GHA's
   documented ~10-20% schedule-drop rate applies to it too).

## Fix applied this session (manual, not automated)

```bash
gh workflow run ci-status-consolidator.yml --repo IggyIkenna/unified-trading-pm --ref main   # forced early refresh
gh workflow run main-backmerge-to-ldr.yml --repo IggyIkenna/unified-trading-pm --ref main     # forced the LDR sync
```

Confirmed: LDR's `workspace-manifest.json` copy flipped to `deployment-service.ci_status=FEATURE_GREEN` immediately
after the backmerge run completed; the next fleet-promote tick (12:15:03Z) read `cached='FEATURE_GREEN'`, closed stale
PR #675 as superseded, and merged fresh PR #676 to `main`.

## Recommended durable fix (not yet applied — needs a todo owner)

Pick ONE:

- [ ] [SCRIPT] P2. **(a) Drop `[skip ci]`** from `ci-status-consolidator.yml`'s commit message, replacing it with a
      targeted mechanism that still avoids re-triggering `quality-gates-v2` (which is presumably the actual thing
      `[skip ci]` was meant to suppress) without blocking `main-backmerge-to-ldr`. E.g. rename the commit message marker
      to something `quality-gates-v2.yml`'s own paths-filter/content-sentinel already ignores (a manifest-only diff),
      rather than relying on GitHub's blanket `[skip ci]`.
- [ ] [SCRIPT] P2. **(b) Give `main-backmerge-to-ldr.yml` its own heartbeat dispatch** (mirror
      `scripts/orchestrator/ldr-to-main-promote-heartbeat.sh`'s pattern) so it doesn't depend solely on the (now
      partially-suppressed) push trigger.

Either fix removes the need for a human/agent to notice+manually-dispatch the backmerge every time this class of stall
recurs. Until fixed, **any `cicd` agent hitting a
`GATE BLOCK ... ci_status=FAILING (cached='FAILING', live='<something green>')` on a fleet-promote tick should suspect
this exact gap** and dispatch `main-backmerge-to-ldr.yml` before assuming the promote PR itself needs conflict
resolution.

## Evidence

- deployment-service escalation agt-368655, repo `deployment-service`, 2026-08-03.
- `eb131cd` (deployment-service@live-defi-rollout) — the actual code fix, unrelated to this bug.
- `unified-trading-pm@20e7d24f2` — consolidator commit that flipped `main`'s manifest (11:47:52Z, `[skip ci]`).
- Fleet-promote runs 30810912821 (11:47Z) / 30811745929 (12:00Z) both logged
  `GATE BLOCK deployment-service: ci_status=FAILING (cached='FAILING', live='FEATURE_GREEN')` despite `main` already
  showing `FEATURE_GREEN` at the time.
- `unified-trading-pm` manual dispatch `main-backmerge-to-ldr.yml` run 30812044629 (12:03Z, success) — immediately
  after, LDR's manifest copy read `FEATURE_GREEN`.
- Fleet-promote run 30812812761 (12:15Z) —
  `TIER A PASS deployment-service: ci_status cached='FEATURE_GREEN' live='FEATURE_GREEN'`, closed PR #675, merged PR
  #676.
