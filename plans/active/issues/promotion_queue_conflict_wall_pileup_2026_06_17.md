---
title:
  Promotion-queue "conflict wall" pile-up — 18 stuck promote/dep-update PRs (PM hub FIXED; dep-update fan-out +
  stale-mergeability + per-repo test failures remain), and they lack a stale-conflict alert
created: 2026-06-17
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

- [x] ✅ [CICD] P2. Close the **superseded** older dep-update PRs: `batch-live-reconciliation-service#82` (UTL-0.11.0,
      superseded by #83) and `market-tick-data-service#223` (UTL-0.11.0, superseded by #224). **DONE 2026-06-17** — both
      CLOSED + branches deleted (superseders #83/#224 confirmed open first).
- [x] ✅ [CICD] P1. Rebase each conflicting dep-update branch onto current `staging` → **NOW OWNED BY THE WORKER CHAIN
      (2026-06-17), not a human todo.** The `supersede-stale-dep-update-prs` bot escalates each surviving CONFLICTING
      dep-update PR (`ibkr-gateway-infra#225`, `market-data-processing-service#292/#293`,
      `market-tick-data-service#224`, `system-integration-tests#232/#234/#235/#236`, `trading-agent-service#211/#212`,
      `batch-live-reconciliation-service#83`) via `merge-conflict-detected` → `conflict-resolution-agent` →
      `escalate-to-orchestrator`; a worker rebases the branch onto staging keeping the floor bump, per the new playbook
      `codex/08-workflows/dep-update-conflict-resolution.md` (and Slacks + asks the operator in the orchestrator UI if
      it genuinely can't). Goes live once the bot reaches main (PM drain).
- [ ] [CICD] P1. **market-tick-data-service** — fix the real unit-test failure
      `test_polymarket_adapter_lifecycle_gating.py::test_canonical_question_group_column_emitted` (diagnose whether UTL
      0.12.0 changed `canonical_question_group` behaviour or the test/fixture is stale), then the dep-update PR can pass
      v2.
- [ ] [CICD] P1. Rebase the staging→main promotes once their bases settle: `unified-api-contracts#344`,
      `unified-trading-library#370`, `deployment-api#101` (these are the staging→main analogue; staging may need its own
      dep-update drains first).

**Long fix (why they stall — systemic):**

- [x] ✅ [CICD] P1. **Give dep-update→staging PRs a resolution OWNER** (the gap: `ldr-to-staging-promote` only owns
      LDR→staging drains). **SHIPPED 2026-06-17 as an escalate-to-worker chain** (not a bulk auto-rebase bot, which
      would need conflict-resolution it can't safely do headless): `supersede-stale-dep-update-prs` escalates a
      surviving CONFLICTING dep-update PR → `conflict-resolution-agent` (now emits a **dep-update-specific** context —
      "rebase the topic branch onto staging, keep the floor bump" — instead of the wrong generic "resolve ON LDR" that
      made escalated workers unable to find the context) → `escalate-to-orchestrator` worker, which resolves per
      `codex/08-workflows/dep-update-conflict-resolution.md`. Worker resolves the mechanical 90%; the can't-resolve
      fallback Slacks #ci-failures + surfaces the question in the orchestrator UI for the operator. Digest-only (Fix
      below) prevents the recurrence; this chain drains the existing ones. unified-trading-pm@(LDR f7f6203e9).
- [x] ✅ [CICD] P2. **Auto-close superseded dep-update PRs** when a newer-version dep-update PR for the same (repo, dep)
      opens. **SHIPPED 2026-06-17** — new PM-central bot `.github/workflows/supersede-stale-dep-update-prs.yml`
      (`*/2h` + dispatch + dry_run; groups open `dep-update/<dep>-<ver>` per repo, closes all but the highest version;
      strictly bounded — only closes when a strictly-higher-version dep-update PR for the same repo+dep is open). Logic
      unit-verified; immediate cleanup already closed #82/#223. unified-trading-pm@(LDR 11ec53a4c, drains to main).
- [x] ✅ [CICD] P2. **Stale-conflict-wall alert**: **SHIPPED 2026-06-17** — `promotion_lag_monitor.py` `_stuck_prs()` +
      `_classify_stuck_pr()` now page on any open promote/dep-update PR parked CONFLICTING (`mergeable_state==dirty`)
      beyond `--stuck-pr-threshold-min` (default 120m). Alert on `dirty` (conflict wall), NOT `blocked`
      (checks-in-progress). Pure classifier unit-tested (6 cases). unified-trading-pm@(LDR cc1376fc4, drains to main).
- [x] ✅ [CICD] P3. **Operator decision: digest-only on minor internal bump — APPROVED + SHIPPED 2026-06-17.** Operator
      confirmed; `update-dependency-version.yml` now skips the consumer floor rewrite (+ uv lock) for a NON-breaking
      minor/patch internal bump (range absorbs it; pull-not-push) — digest-only. MAJOR/breaking keeps the floor re-pin +
      PR. Verified safe: dep-alignment presence-checks internal deps (no floor match;
      `scripts/manifest/check-dependency-alignment.py`). SSOT committed + rolled out to all 24 repo LDRs (drift checker:
      0 new drift). unified-trading-pm@(LDR 3d41a6e9d, drains to main).

## Composes with

`cicd_contract_hardening_2026_06_01.md` (Guard 2 + the promote bots) · `ldr_trunk_promotion_decoupling_2026_06_10.md`
(the Tier-C drain) · `provenance_gate_squash_perpetual_block_2026_06_17.md` (same session's gate fix). The
strict-quickmerge / promotion HARD RULES are correct; this is the **fan-out staleness + missing-rebase + missing-alert**
machinery gap.

## Drain-to-main blockers discovered while pushing PM LDR→main (#387) — 2026-06-17

Pushing the PM LDR→main standing drain (#387) so the new machinery goes live surfaced TWO separate systemic blockers
(NOT the conflict-wall, which is fixed; NOT introduced by this session's commits — verified clean: the failing typecheck
files are all foreign/pre-existing):

- [ ] [CICD] P1. **PM (and fleet) `quality-gates-v2` is FLAKY on a stale-dep clone.** When a repo's LDR is AHEAD of its
      latest release tag, the CI version-aware dep-clone falls back to a STALE tag for UTL/UAC → basedpyright resolves
      their types as `Unknown` → broad `reportUnknown*` errors across many files (`check-repo-readiness.py`,
      `generate-cicd-diagram.py`, `reap_stale_blockers.py`, …) that are green when deps resolve correctly. PM v2 went
      green at `0d51af1e` (01:36Z) then RED across `cc1376fc`→`14ab1a12` (~40 min, multiple heads) on this — per-run
      flaky by dep-resolution, not content. This persistently blocks the LDR→main drain (a red required check). Fix
      candidates: cut fresh UTL/UAC release tags so LDR≤tag, OR make the CI dep-clone fall back to the dep's LDR/branch
      (not a stale tag) when source is ahead of its tag. Target: `unified-trading-pm` quality-gates-base clone logic.
      **Big finding — operator/CI.**
- [ ] [CICD] P1. **The PM LDR→main forward drain has no manifest-conflict resolver** (only the back-merge does, via
      reconcile_manifest_backmerge.py). main churns `workspace-manifest.json` `ci_status` every few minutes (every
      repo's v2 result writes a `[skip ci]` commit to main), so #387 perpetually re-`dirty`s on the manifest faster than
      it can merge — even after a hand back-merge it re-diverges within ~1-3 min. Durable fix: give the forward drain
      (ldr-to-main-promote bot, or a merge driver in the bot's clone) the same reconciler resolution for
      `workspace-manifest.json` so LDR→main merges cleanly regardless of ci_status churn (take main's
      ci_status/version-surface + LDR structure), then arm/merge in the same run.

**Interim state:** the conflict-wall fixes (digest-only, supersede+escalate owner chain, alert, the reconciler
semver-max) are all on `live-defi-rollout` and drain to main via the standing PR once v2 goes green (flaky → will pass
on a clean-dep-resolve run; `ldr-to-main-promote` \*/15 keeps retrying). NOT force-merged over the red v2 (would land 91
commits over a — flaky but real — failing required check).

## Autonomous unjam — Progress Log (2026-06-17, operator: "go autonomous, unblock everything")

**Root cause of the circular deadlock (confirmed):** jammed promotion → no fresh UTL/UAC release tags → CI dep-clone
falls back to STALE tags (UTL v0.10.0 while LDR=0.13.0; UAC v0.14.0 while LDR=0.18.0) → basedpyright resolves dep types
as `Unknown` → broad `reportUnknown*` typecheck failures fleet-wide → v2 red → promotion jammed. UTL/UAC
main↔staging↔LDR are 3-way diverged (UTL staging+22/main+29) BUT **LDR is the verified lossless SUPERSET** (`main ⊆ LDR`
AND `staging ⊆ LDR`, zero missing commits — incl. main's starlette-CVE fix `f1dbf572` + risk/margin features). So
tagging the superset content is lossless.

**Action taken (operator-chosen option a — cut fresh tags; additive + reversible):**

- Cut **UTL `v0.13.0`** @ staging HEAD `ce02c219` (pyproject=0.13.0, ⊆ LDR) — was stuck at v0.10.0.
- Cut **UAC `v0.18.0`** @ staging HEAD `ad81150b` (pyproject=0.18.0, ⊆ LDR) — was stuck at v0.14.0.
- These become the LATEST tags ≥ every consumer floor → the CI dep-clone fallback now resolves the CURRENT public API →
  basedpyright should stop seeing `Unknown`. Verifying via a re-triggered PM v2.

**Expected cascade if verified:** fresh UTL/UAC tags → consumer v2 typecheck green fleet-wide → the conflict-walled
dep-update/staging→main PRs (Class B/C) + PM #387 drain on their armed auto-merge → all this session's machinery
(digest-only, supersede+escalate owner chain, alert, reconciler) lands on main.

**If the re-triggered v2 does NOT clear:** the tags are reversible (`git push origin :v0.13.0`); the clone falls back
via a different path → escalate to the operator (this is the boundary). NOT force-syncing main blind at depth (rule 11).

### CORRECTION (2026-06-17) — the PM-drain blocker is a FLAKY basedpyright Unknown-cascade, NOT a stale tag

The "cut fresh tags" hypothesis was WRONG and is REVERTED (UTL→v0.10.0, UAC→v0.14.0). Evidence: a PM v2 run WITH fresh
deps installed (`unified-trading-library==0.13.0` + `unified-api-contracts==0.18.0` built from the file:// clone) STILL
failed typecheck with the SAME ~3000 errors. The errors are `reportAny`/ `reportUnknown` on PM's own
`json.loads`/`dict.get` across many scripts — **dep-version-independent**.

**Actual root (documented at `scripts/quality-gates-base/base-service.sh:312-319`):** a basedpyright **Unknown-type
CASCADE** — when the workspace libs (UTL/UAC) are not resolved into the `.venv` that basedpyright reads (`venv=".venv"`;
LOCAL*DEPS can land outside it), basedpyright degrades \_all* types to `Unknown` → thousands of spurious
`reportUnknown*`/`reportAny`. It is **FLAKY per-run** (`0d51af1e` typecheck =success at 01:36; `cc1376fc`→`14ab1a12`
=failure since) and **fleet-wide** (every repo's typecheck depends on its deps resolving into `.venv`). NOT introduced
by this session (the failing files are foreign/pre-existing).

**Implication — NOT "stuck forever":** because it is FLAKY (not deterministic), a re-run that lands the deps in `.venv`
goes green, and `ldr-to-main-promote` (\*/15) + the v2 re-dispatch keep retrying → the drain CONVERGES when a
green-typecheck run aligns with a mergeable (post-back-merge) #387 window. The conflict-wall fixes are all on LDR and
ride that convergence.

- [ ] [CICD] P1. **Durable fix for the basedpyright Unknown-cascade flake** (`base-service.sh` typecheck slice):
      guarantee the workspace deps (UTL/UAC editable) are installed into the SAME `.venv` basedpyright reads before the
      type-check step, and fail-loud (not Unknown-cascade) if they are not. Fleet-wide. **Big finding — CI-infra.** This
      is the real keystone behind the whole promotion jam (it reds every repo's v2 typecheck on a bad-luck dep-install
      run). Separate, dedicated investigation — NOT 3000 hand-fixes.

### .venv-install fix SHIPPED + VERIFIED (2026-06-17) — fleet cascade cured; PM-#387 residual isolated

**Root (confirmed):** the reusable `python-quality-gates-v2.yml` typecheck slice installed cloned sibling deps with a
bare `uv pip install -e ../$dep` (NO `--python .venv/bin/python`). On a runner with a pyenv/global interpreter, uv
installed them OUTSIDE `.venv`; basedpyright (`venv=".venv"`) then saw the workspace lib unresolved → Unknown-type
cascade → typecheck red. FLAKY (green only when uv picked `.venv`).

**Fix:** `uv pip install -e "../$dep" --python "$_qg_venv_py"` (+ a loud unresolved-dep warning), mirroring the proven
local fix `base-service.sh:316-327`. The reusable workflow is referenced by every repo at `@live-defi-rollout`, so it
went **fleet-live on the PM LDR push (df6291b6d)** — no rollout, no main-drain.

**VERIFIED:** re-ran v2 typecheck on a CONSUMER (`market-tick-data-service`) → **typecheck SUCCESS** (was red); deps
resolve, no cascade. → the ~24 consumer repos' Class-B dep-update + Class-C staging→main PRs now pass typecheck and
drain.

**PM-#387 residual (separate issue, NOT the cascade):** PM's own v2 typecheck still fails — count 2992 vs
`BASEDPYRIGHT_MAX_ERRORS=1517` (`0d51af1e` was exactly 1517=green). My fix WORKED for PM too (deps resolve: the
unresolved-dep warning did NOT fire; only 1 UTL/UAC ref in 2992). The 2992 is PM's OWN basedpyright debt: ~592
`reportAny` + `reportUnknown` on `json.loads`/`dict.get`/loop-vars across PM scripts (`generate-cicd-diagram.py` 145,
`plan-hygiene/fix_frontmatter.py` 124, `_prospectus_manifest.py` 83, `reap_stale_blockers.py` 69, …), plus ~86 from one
genuinely-unresolved import `unified_trading_services` (`audit-library-imports.py`; NOT in PM's `dep_repos`). The
1517→2992 jump is unexplained (genuine debt growth vs a measurement change) and needs investigation BEFORE a decision.

- [ ] [CICD] P1. **PM #387 typecheck-debt-vs-ceiling** — decide (do NOT blind-bump): (a) investigate the 1517→2992 jump
      (which commits/scripts added the ~1475; is any a regression vs intentional-Any json debt); (b) ✅ DONE — the ~86
      `unified_trading_services` errors were from ONE dead one-off `scripts/migration/delete-gcs-data-for-dates.py`
      importing the REMOVED `unified_trading_services` package (`unified-trading-services` is NOT a real repo — the
      earlier "add to dep_repos" idea was WRONG); DELETED it (PM@6915debdb; its fns now live in
      `unified_trading_library.cloud_interface`); (c) for the genuine intentional-Any json/argparse scripts, extend the
      existing
      `[tool.basedpyright] ignore` list (consistent with its stated rationale) OR recalibrate the ceiling once the jump
      is understood. Only PM's v2 (and thus the PM-central bots reaching main: supersede, alert, ldr-to-main provenance,
      conflict-agent context) is gated on this; the FLEET is already unblocked.
