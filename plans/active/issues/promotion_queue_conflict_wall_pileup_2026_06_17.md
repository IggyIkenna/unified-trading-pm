---
title:
  Promotion-queue "conflict wall" pile-up — 18 stuck promote/dep-update PRs (PM hub FIXED; dep-update fan-out +
  stale-mergeability + per-repo test failures remain), and they lack a stale-conflict alert
created: 2026-06-17
author: slot-3·laptop
source:
  - "operator triage-queue screenshot 2026-06-17: 18 PRs 'Conflict wall', 3h–17h stuck, → staging / → main"
  - scripts/cicd/reconcile_manifest_backmerge.py
  - .github/workflows/{ldr-to-staging-promote,ldr-to-main-promote,main-backmerge-to-ldr}.yml
locked_by: live-defi-rollout
priority: P1
status: active
---

# Promotion-queue conflict-wall pile-up (2026-06-17)

## What I found

The orchestrator triage queue showed **18 promote/dep-update PRs parked in "Conflict wall" for 3h–17h**. Investigation
(trial-merges + GitHub `mergeable_state` + `update-branch` probes + v2 conclusions) shows **three distinct classes**,
not one bug:

### Class A — PM main↔LDR hub conflict — **FIXED this session** ✅

`unified-trading-pm#387` (LDR→main standing drain) was `dirty`, and the `main-backmerge-to-ldr` bot had opened conflict
PR `#388`. Root cause: `reconcile_manifest_backmerge.py` (back-merge Guard 2) escalated on a **both-bumped
version-surface** conflict (`versions.unified-trading-library` was 0.11.0 on main vs 0.12.0 on LDR, both ahead of base
0.10.0) — it only auto-resolved `ci_status`-only conflicts. This dammed BOTH the back-merge AND the LDR→main drain, and
held PM's `versions[]` behind main (1.2.128 vs 1.2.146) so the version-align gate blocked every local PM QG.

**Fix shipped:** the reconciler now resolves both-bumped version-surface scalars (`versions.<repo>`,
`repositories.<name>.version`) via **semver-max** (monotonic; never regress; dep-edge floors still escalate; CI-state
still takes main). unified-trading-pm@ee5b7058b (LDR) + PR #391 (main, MERGED). Verified in prod: dispatched
`main-backmerge-to-ldr` → auto-resolved (`versions[utl]`→0.12.0, `versions[pm]`→1.2.146) → **main now fully contained in
LDR**, **#388 MERGED**, **#387 armed + draining** (`dirty`→`blocked`/auto-merge), and the version-align gate now passes
on LDR. SSOT: `cicd_contract_hardening_2026_06_01.md` § Guard 2.

### Class B — dep-update→staging fan-out pile-up (the bulk, ~13 PRs) — **NEEDS per-repo work**

The dependency-update fan-out (`update-dependency-version.yml`) opened per-consumer `dep-update/<dep>-<ver>` PRs
(Dockerfile `BASE_IMAGE_DIGEST` refresh + the dep **floor** bump) on the UTL/UAC/execution/strategy bumps. They stall
because:

- **(a) genuine, current conflicts with the _advancing_ staging.** The dep-update branch was cut from an older staging;
  staging keeps moving (other promotes/bumps), so the branch's `pyproject.toml`/`uv.lock` dep lines now conflict.
  `gh api … /update-branch` returns **422 "merge conflict between base and head"** (e.g. system-integration-tests#234).
  There is **no auto-rebase** of open dep-update PRs onto staging.
- **(b) stacking + supersession.** Multiple dep-update PRs pile up per repo; older ones are superseded:
  - `batch-live-reconciliation-service#82` (UTL-0.11.0) superseded by **#83** (UTL-0.12.0)
  - `market-tick-data-service#223` (UTL-0.11.0) superseded by **#224** (UTL-0.12.0)
- **(c) a few genuine test failures** (NOT just conflicts): `market-tick-data-service#224` v2 fails on
  `tests/unit/test_polymarket_adapter_lifecycle_gating.py::test_canonical_question_group_column_emitted`
  (`assert (df["canonical_question_group"]=="OTHER").all()` → False; 1 failed / 4975 passed). Most others (sit#234,
  ibkr#225, trading-agent#212) have **v2=pass** but are conflict-walled (the (a) branch staleness).

### Class C — staging→main promotes still `dirty` (uac#344, utl#370, deployment-api#101)

Head=`staging`→`main`, auto-merge armed, `dirty` (staging↔main divergence). Same family as the dep-update staleness;
need a rebase/recompute once their staging bases settle.

### Why they "lack alerts"

The promote bots treat `dirty` as a conflict (dispatch the conflict-resolver or leave it); `ci-failure-watcher`
`--auto-recover` only handles the **BLOCKED + v2-absent** signature, not a **DIRTY conflict-wall parked for hours**. So
a multi-hour pile-up is invisible — exactly the operator complaint.

## Why it matters

Every UTL/UAC bump fans out a PR per consumer; with no auto-rebase + no supersede-close + no stale alert, the queue
grows unboundedly and dams staging→main promotion fleet-wide. It is NOT a data-correctness issue (the versions/floors
are real — UTL genuinely built at 0.12.0 in CI), but it freezes the pipeline.

## Recommended decision

**Short fix (drain) — per-repo, fan-out to the epic/CI VMs (NOT a single-agent bulk action — collision risk + each needs
its own QG/v2 verification):**

- [ ] [CICD] P2. Close the **superseded** older dep-update PRs: `batch-live-reconciliation-service#82` (UTL-0.11.0,
      superseded by #83) and `market-tick-data-service#223` (UTL-0.11.0, superseded by #224).
- [ ] [CICD] P1. Rebase each conflicting dep-update branch onto current `staging` (or re-run the fan-out so it
      regenerates from current staging) and let v2-gated auto-merge drain it: `ibkr-gateway-infra#225`,
      `market-data-processing-service#292`(UAC-0.15.0)+`#293`(UTL-0.11.0), `market-tick-data-service#224`,
      `system-integration-tests#232`(UAC)/#234(UTL)/#235(execution)/#236(strategy),
      `trading-agent-service#211`(UAC)/#212(UTL), `batch-live-reconciliation-service#83`.
- [ ] [CICD] P1. **market-tick-data-service** — fix the real unit-test failure
      `test_polymarket_adapter_lifecycle_gating.py::test_canonical_question_group_column_emitted` (diagnose whether UTL
      0.12.0 changed `canonical_question_group` behaviour or the test/fixture is stale), then the dep-update PR can pass
      v2.
- [ ] [CICD] P1. Rebase the staging→main promotes once their bases settle: `unified-api-contracts#344`,
      `unified-trading-library#370`, `deployment-api#101` (these are the staging→main analogue; staging may need its own
      dep-update drains first).

**Long fix (why they stall — systemic):**

- [ ] [CICD] P1. **Auto-rebase open `dep-update/*` PRs onto staging** when staging advances (the missing mechanism —
      there is a SKIPPED `refresh-open-prs` check on these PRs; investigate why it never refreshes and make it
      rebase/regenerate stale dep-update branches). Target repo: `unified-trading-pm` (`scripts/workflow-templates/` +
      the `update-dependency-version.yml` template) — fleet rollout.
- [ ] [CICD] P2. **Auto-close superseded dep-update PRs** when a newer-version dep-update PR for the same (repo, dep)
      opens. Target: the fan-out workflow (`update-dependency-version.yml`).
- [ ] [CICD] P2. **Stale-conflict-wall alert**: extend `ci-failure-watcher` / `promotion_lag_monitor.py` to page when a
      promote/dep-update PR sits `dirty` (or BLOCKED) beyond an SLA (e.g. >2h) — closes the "lack alerts" gap. Target:
      `unified-trading-pm`.
- [ ] [CICD] P3. **Operator decision** — per the range-pin / pull-not-push model, a MINOR internal bump (UTL 0.10→0.12,
      within `<1.0.0`) should NOT force a consumer **floor** bump (the range already absorbs it); only the Dockerfile
      **digest** refresh needs to ride the fan-out. The floor bump is what creates the `pyproject.toml` conflict that
      walls these PRs. Decide whether `update-dependency-version.yml` should stop bumping the floor on a minor internal
      bump (digest-only), which would eliminate most Class-B conflicts at the source.

## Composes with

`cicd_contract_hardening_2026_06_01.md` (Guard 2 + the promote bots) · `ldr_trunk_promotion_decoupling_2026_06_10.md`
(the Tier-C drain) · `provenance_gate_squash_perpetual_block_2026_06_17.md` (same session's gate fix). The
strict-quickmerge / promotion HARD RULES are correct; this is the **fan-out staleness + missing-rebase + missing-alert**
machinery gap.
