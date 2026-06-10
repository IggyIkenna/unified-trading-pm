---
title: LDR-trunk promotion decoupling — quickmerge lands on LDR, tier-drain promotes, hotfix is the only break-glass
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
created: 2026-06-10
locked_by: live-defi-rollout
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
source:
  - plans/active/cicd_contract_hardening_2026_06_01.md
---

# LDR-trunk promotion decoupling

> **Parent / umbrella:** this plan is a focused tranche OF
> [`cicd_contract_hardening_2026_06_01.md`](cicd_contract_hardening_2026_06_01.md). It finishes the "staging-first path
> unused / staging behind LDR" thread (that plan's item H / todo @2559) by making the Tier-C drain the **sole**
> LDR→staging path and removing the per-commit staging coupling from `quickmerge`. Read the conflict reconciliation (§4)
> before touching any shared surface.

## Why (the trigger)

Two live symptoms on 2026-06-10 share one root cause — **per-commit promotion couples shipping to staging state**:

1. **BLR `main` went RED** with `dependency unified-trading-library: resolved 0.4.0 < floor 0.5.0`. The
   `feat(docker): pin base image via ARG BASE_IMAGE_DIGEST` commit was **direct-pushed to `main`** (the FROM-digest
   Phase-6 rollout used the direct-to-main carve-out). A full QG on a `main` push resolves internal deps **against
   main-tier** (`BRANCH = github.ref_name`), where UTL is still 0.4.0 / only `v0.4.0` is tagged — even though UTL 0.5.0
   is live on staging+LDR. The **same change through LDR→staging** (`base_ref=staging`) resolves against staging-tier →
   finds 0.5.0 → passes. The red is an artifact of bypassing the orderly LDR→staging→main flow.
2. **Staging-lock serialization.** `quickmerge` STAGE 1.5 blocks **every** agent commit while staging is locked for a
   breaking-change SIT — even though `live-defi-rollout` is supposed to be the gateless integration trunk. "Commit a
   million things but each blocks the next" is this gate.

## The model (what changes)

`live-defi-rollout` becomes the **gateless trunk** in practice, not just in docs:

- **`quickmerge --agent --files` lands on LDR and stops there.** No per-unit LDR→staging PR for service repos. The
  commit-quality boundary (local `quality-gates.sh` sentinel) still binds — LDR isn't unguarded, it's
  _server-gate-deferred_.
- **Promotion is the existing tier-ordered batched drain.** `ldr-to-staging-promote.yml` (Tier C) is already
  tier-ordered (`topologicalOrder.levels[]`) and dep-order-gated (`tier_c_promotion_gate.py`). Its cadence moves **6h →
  30min** so "CI on LDR content" (the LDR→staging PR's `quality-gates-v2`, resolving deps against staging-tier) lands
  within ≤30 min. That PR **is** the authoritative server gate.
- **Hotfix is the only break-glass.** `--hotfix` still opens a staging PR and **still hits the staging lock** (correct:
  a queue-jumping change must reconcile with whatever is converging on staging). An exceptional `--hotfix-to-main` opens
  a main PR whose **only gate is `quality-gates-v2` on main** (no SIT, no staging hop). Both require an explicit
  operator signal + a commit-message marker; agents cannot self-authorize.

## Decisions recorded (so they aren't re-litigated)

- **D1 — drop `push:[staging]` QG; staging-green INHERITS from feature-green (operator decision 2026-06-10).** The QG
  that runs on the LDR→staging PR (`pull_request:[staging]`, head=LDR, base=staging) executes on the **exact tree** that
  lands on staging — re-running v2 on the `push:[staging]` event is redundant (same content, same staging-tier
  resolution). So **remove `staging` from the `push:` triggers** in `quality-gates-v2.yml.tmpl` (keep
  `pull_request:[main,staging]` + `push:[main]`). The `STAGING_GREEN` ci_status is **derived from the feature-green
  result** (the LDR→staging PR's pass = `FEATURE_GREEN`) at merge time, not from a staging-branch QG run.
  - **HARD ORDERING (do not reorder):** `STAGING_GREEN` today is written by `ci-status-update.yml` _on a QG pass on the
    staging branch_ — i.e. the `push:[staging]` run. The Tier-C dep-order gate (`tier_c_promotion_gate.py`) **reads**
    `STAGING_GREEN`. So removing `push:[staging]` **before** wiring the inheritance STARVES the dep-order gate → the
    drain jams fleet-wide. Sequence: (1) wire `FEATURE_GREEN→STAGING_GREEN` inheritance in `ci-status-update.yml`, (2)
    teach the @4950 zero-check-run detector that a staging head legitimately has no _push_ check (its gate is the merged
    PR's check), (3) THEN drop `staging` from `push:` in the template + `rollout-workflow-templates.sh`. See todos
    below.
  - We still do **NOT** add a `push: live-defi-rollout` trigger — a raw LDR-push QG has _no_ `base_ref=staging`
    fallback, so it would re-introduce the BLR failure (a dep on staging-but-not-LDR). The staging→main required check
    is unaffected (the `pull_request:[main]` trigger re-runs v2 on the staging head).
- **D2 — local dep-alignment stays main-aligned.** `version-alignment-gate.sh:99-108` deliberately compares local
  `versions{}` vs `origin/main` (not `staging_versions`) to avoid false-blocking the whole promotion window. The
  operator's "build off latest staging" intent is satisfied by **CI tiered resolution** (staging-tier on staging PRs),
  not by changing the local gate. No change to the local gate; instead see todo P1.5 (compose with hardening @4228,
  dep-clone ref-determinism).

## §4 — Conflict reconciliation with `cicd_contract_hardening_2026_06_01.md` remaining todos

Checked all ~50 open todos. **No hard conflicts.** Interactions:

| Hardening todo                                                    | Relationship                       | Action here                                                                                                                                                                                                               |
| ----------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| @2559 staging behind LDR / staging-first unused (P2)              | **This plan completes it**         | Making the drain the sole path + 30min is the resolution.                                                                                                                                                                 |
| @4228 QG dep-clone ref-determinism (P2)                           | **Complement / prerequisite-soft** | The model leans on deps resolving at the _same_ (staging) ref. Cross-link; not blocking — fail today is a mixed-ref edge, our model reduces its blast radius.                                                             |
| @4941 sanitize Tier-C squash body `[skip ci]` (P1)                | **NOT triggered by current drain** | The live drain uses `--auto --rebase` (lines 166/220), not squash → no squash-body poisoning. **Verify before declaring done**; the bug lives on the `ldr-to-main`/`staging-to-main` _squash_ paths, out of this tranche. |
| @4950 flag staging head w/ ZERO check runs (P2)                   | **Must adapt (was a blocker)**     | Dropping `push:[staging]` (D1) makes a checkless staging head LEGITIMATE — the detector must flag only heads with no check AND no merged-PR check (else false-positive on every drain merge). Sequenced todo below.       |
| @4933 per-cone parallel staging locks (P3)                        | **Composes (future)**              | 30min drain + per-cone locks compose; lock duration → longest cone. No change needed now.                                                                                                                                 |
| @4882 4 repos lack `quickmerge.sh` (P2)                           | **Coverage gap**                   | ml-service et al. won't get the new behavior until they have the symlinked script. Out of scope; cross-link.                                                                                                              |
| @4843-4849 sit-gate/cloud-build-router concurrency review (P2/P3) | **Adjacent**                       | Unaffected; promotion ordering unchanged.                                                                                                                                                                                 |

## Todos

- [x] ✅ [SCRIPT] P0. **Drain cadence 6h → 30min.** `ldr-to-staging-promote.yml:26` cron `"17 */6 * * *"` →
      `"13,43 * * * *"` (off top/bottom-of-hour). PM-only workflow; must land on PM `main` to fire (scheduled workflows
      fire only from the default branch). — unified-trading-pm@ef76571 (PR #219 → main)
- [x] ✅ [SCRIPT] P0. **quickmerge: land-on-LDR, skip per-unit staging PR for service repos.** After the LDR push, for a
      commit that is NOT PM, NOT `[skip ci]`, NOT `--hotfix` → do **not** `gh pr create --base staging`; print "landed
      on LDR — Tier-C drain (≤30min) promotes to staging". PM→main and `[skip ci]`→main paths unchanged. File:
      `scripts/quickmerge.sh` (early-exit after PR_BASE block). FAIL-SAFE (worst case: promotion waits ≤30min). —
      unified-trading-pm@ef76571
- [x] ✅ [SCRIPT] P0. **quickmerge: decouple LDR commits from staging state.** STAGE 1.5 (staging-lock) and STAGE 1.7
      (dep-tier): guard changed `TO_STAGING=true` → `HOTFIX=true` so only a hotfix-to-staging respects the lock /
      dep-tier gate; normal LDR landings skip them (the drain re-gates dep-order). FAIL-SAFE. —
      unified-trading-pm@ef76571
- [x] ✅ [SCRIPT] P1. **quickmerge: STAGE 1.6 dep-version gate → WARN for non-hotfix, BLOCK for hotfix.** Building
      against a dep that is version-behind-staging is legitimate on the LDR trunk; the drain + SIT catch real
      incompatibilities. Keep the hard BLOCK on the `--hotfix` path (a hotfix must reconcile with staging). —
      unified-trading-pm@ef76571
- [ ] [SCRIPT] P1. **quickmerge: harden `--hotfix` + add `--hotfix-to-main`.** `--hotfix` requires a `[hotfix]` marker
      in the commit message (else refuse) and keeps the staging-lock respect. New `--hotfix-to-main`: requires
      `[hotfix-main]` marker **and** explicit operator env `QUICKMERGE_HOTFIX_TO_MAIN_OK=1` (agents cannot
      self-authorize); opens a **main** PR with auto-merge whose only gate is `quality-gates-v2` on main (no SIT, no
      staging). **Does NOT script a protection bypass / direct push** — the operator does that manually via the
      documented relax→push→re-enable if ever truly needed.
- [ ] [DOCS] P1. **codex SSOT update.** `codex/08-workflows/ci-cd-flow.md` § "Two-Pass Workflow Model" + §
      strict-quickmerge: record that the service-repo staging PR is now drain-only, the staging-lock/dep-tier gates are
      hotfix-scoped, and the hotfix/hotfix-to-main break-glass contract. Update
      [CLAUDE.md](../../cursor-configs/CLAUDE.md) one-liners (strict-quickmerge carve-out set) to match.
- [ ] [SCRIPT] P1.5. **Compose with @4228 (dep-clone ref-determinism).** Confirm the LDR→staging PR resolves _all_
      internal deps at the staging ref consistently (no mixed staging-new/main-old set). Cross-linked,
      verify-on-first-green.
- [ ] [SCRIPT] P1. **Drop `push:[staging]` QG — STEP 1 of 3 (inheritance FIRST).** Wire `FEATURE_GREEN → STAGING_GREEN`
      inheritance in `ci-status-update.yml`: when a repo's LDR→staging PR merges green (its `quality-gates-v2` passed =
      the staging gate, same tree), set ci_status `STAGING_GREEN` at merge — do NOT depend on a `push:[staging]` QG run.
      **MUST land before STEP 3** or the Tier-C dep-order gate (`tier_c_promotion_gate.py`, reads `STAGING_GREEN`)
      starves → drain jams fleet-wide. repo: unified-trading-pm.
- [ ] [CODE] P2. **Drop `push:[staging]` QG — STEP 2 of 3 (detector).** Teach the @4950 zero-check-run detector
      (Repos-CI dashboard) that a staging head with no _push_ check is legitimate when its merged PR carries the v2
      check; flag only no-check AND no-merged-PR-check. Composes with `monitoring_control_plane_master_2026_06_10.md`.
- [ ] [CI] P1. **Drop `push:[staging]` QG — STEP 3 of 3 (template + rollout).** Remove `staging` from the `push:`
      branches in `scripts/workflow-templates/quality-gates-v2.yml.tmpl` (keep `pull_request:[main,staging]` +
      `push:[main]`), then `rollout-workflow-templates.sh --template quality-gates-v2` to all 24 repos + commit each
      per-repo copy (rollout is not done until `detect_template_drift.py --workflows` is clean and no repo's
      `.github/workflows/` is dirty). **Gated on STEP 1 being live.** Verify v2-on-staging count drops to zero while
      `STAGING_GREEN` still populates + the drain keeps promoting.
- [ ] [TEST] P2. **First-use watch.** After PM ships: confirm (a) a normal `quickmerge --agent` lands on LDR with no
      staging PR + a clean message, (b) the 30min drain opens the LDR→staging PR and it auto-merges on v2-green, (c)
      `--hotfix` still hits the lock when staging is locked. Record evidence here.
- [x] ✅ [CI] P0. **Tier-C drain auto-merge was SILENTLY DEAD — `--auto --rebase` cannot ARM on a merge-laden LDR**
      (GraphQL `This branch can't be rebased`; LDR carries merge commits from the backmerge-bot + resolved backmerges) →
      every promote PR opens but never auto-merges → the LDR→staging pile-up (the "treadmill"). The arm failure was
      swallowed (`2>/dev/null` / `|| true`). **FIX (PM@84fe257ae):** `--auto --rebase || --auto --squash` fallback
      (squash always arms) at BOTH merge sites (line 166 primary + line 220 close-reopen), with an explicit **sanitized
      subject/body** so no inherited `[skip ci]` poisons the staging push — pre-emptively closing @4941 for the drain's
      NEW squash path (the separate `ldr-to-main`/`staging-to-main` squash paths still need @4941). Validated:
      `--auto --squash` arms + merges (execution-service #254 merged via the probe). **VERIFY end-to-end** once it
      reaches PM `main` (Option-B) + the next :13/:43 tick auto-merges a promote via the squash fallback. Finding + fix:
      harsh slot, 2026-06-10.

## Success criteria

- `quickmerge --agent --files` on a service repo: commit on `origin/live-defi-rollout`, **no** staging PR opened,
  exit 0.
- Staging-locked → a normal `quickmerge` still succeeds (lands on LDR); a `--hotfix` is blocked by the lock.
- `ldr-to-staging-promote` runs at :13/:43, drains in tier order, LDR→staging PR `quality-gates-v2` green (deps resolved
  against staging-tier).
- BLR-class failure (`resolved < floor` on a `main` push) cannot recur for changes that flow through LDR.
- `detect_template_drift.py` clean; no per-repo `.github/workflows` dirty; codex + CLAUDE.md aligned.
