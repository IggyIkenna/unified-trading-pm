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
- [x] ✅ [CICD] P1. **market-tick-data-service** — the unit-test failure
      `test_polymarket_adapter_lifecycle_gating.py::test_canonical_question_group_column_emitted` is **RESOLVED on LDR**
      (verified 2026-06-17 afternoon): the test now asserts the decision-338 `MISC_NOVELTY` residual (commit `ed23954e`
      "align polymarket cqg test to MISC_NOVELTY residual") and **PASSES** on current LDR (`1 passed in 0.32s`). The
      dep-update #224 failure was its STALE base carrying the old `OTHER`-asserting test against new UTL behaviour; #224
      is CLOSED and no dep-update PRs remain (digest-only fix). No code/test change needed — the bug never existed on
      LDR. mtds@ed23954e (already on LDR).
- [x] ✅ [CICD] P1. Staging→main promotes **drained** (verified 2026-06-17 afternoon): `unified-api-contracts#344` and
      `unified-trading-library#370` were CLOSED as superseded by the LDR→main reconcile path (UAC #353 MERGED, UTL #376
      armed — the Class-D option-(b) pattern: LDR is the SSOT + carries both back-merges, so LDR→main reconciles cleanly
      where staging→main conflicts). `deployment-api#101` is OPEN + MERGEABLE + UNSTABLE (carrying the monitor
      content-identity fix; v2 running, auto-merge armed → self-draining). The systemic "staging→main perpetually
      CONFLICTS" root is tracked durably at § Class-D P1 below (line ~299).

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

- [x] ✅ [CICD] P1. **PM (and fleet) `quality-gates-v2` FLAKY on a stale-dep clone — RESOLVED** (this was a duplicate
      symptom of the basedpyright Unknown-cascade below; the real root was NOT a stale tag but the editable dep install
      landing outside `.venv`). The fix `uv pip install -e "../$dep" --python "$_qg_venv_py"` is **live** in the reusable
      `python-quality-gates-v2.yml` (line ~479, referenced `@live-defi-rollout` fleet-wide → no rollout). Verified on a
      consumer (market-tick-data-service typecheck SUCCESS) + PM itself (v2 GREEN run 2c82c780 → #387 MERGED). The
      "cut fresh tags" hypothesis was tried + REVERTED (UTL→v0.10.0, UAC→v0.14.0) — see CORRECTION below. unified-trading-pm@df6291b6d.
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

- [x] ✅ [CICD] P1. **Durable fix for the basedpyright Unknown-cascade flake — SHIPPED + VERIFIED** (the keystone). The
      reusable `python-quality-gates-v2.yml` typecheck slice installed cloned sibling deps with a bare `uv pip install -e
      ../$dep` (no `--python`) → on a runner with a pyenv/global interpreter uv installed them OUTSIDE `.venv` →
      basedpyright (`venv=".venv"`) saw the workspace lib unresolved → Unknown-type cascade → typecheck red (FLAKY: green
      only when uv happened to pick `.venv`). Fix: `uv pip install -e "../$dep" --python "$_qg_venv_py"` + loud
      unresolved-dep warning (line ~479), mirroring the proven local `base-service.sh:316-327`. Fleet-live on the PM LDR
      push (referenced `@live-defi-rollout` by every repo — no rollout). VERIFIED on a consumer (market-tick-data-service
      typecheck SUCCESS, was red) and PM (v2 green → #387 merged). unified-trading-pm@df6291b6d. **See § ".venv-install
      fix SHIPPED + VERIFIED" for full detail.**

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

- [x] ✅ [CICD] P1. **PM #387 typecheck-debt-vs-ceiling** — decide (do NOT blind-bump): (a) investigate the 1517→2992 jump
      (which commits/scripts added the ~1475; is any a regression vs intentional-Any json debt); (b) ✅ DONE — the ~86
      `unified_trading_services` errors were from ONE dead one-off `scripts/migration/delete-gcs-data-for-dates.py`
      importing the REMOVED `unified_trading_services` package (`unified-trading-services` is NOT a real repo — the
      earlier "add to dep_repos" idea was WRONG); DELETED it (PM@6915debdb; its fns now live in
      `unified_trading_library.cloud_interface`); (c) for the genuine intentional-Any json/argparse scripts, extend the
      existing
      `[tool.basedpyright] ignore` list (consistent with its stated rationale) OR recalibrate the ceiling once the jump
      is understood. Only PM's v2 (and thus the PM-central bots reaching main: supersede, alert, ldr-to-main provenance,
      conflict-agent context) is gated on this; the FLEET is already unblocked. **✅ RESOLVED 2026-06-17** — the
      1517→2992 "debt" was NOT real debt: it was the `.venv` UTL/UAC Unknown-CASCADE in PM's CI typecheck slice. Proven
      locally: `basedpyright scripts/` with UTL/UAC resolved in `.venv` = **1489 errors < 1523 ceiling** (PASSES); CI's
      2992 = 1489 genuine + ~1503 cascade from unresolved deps. The `df6291b6d` `--python .venv/bin/python` fix made the
      editable install deterministic → PM v2 typecheck went GREEN (run 2c82c780, 03:25Z) → **#387 MERGED** (head
      aaa133c72). PM-central machinery is now live on main. No ceiling change needed.

---

## Class D — fleet-wide "drain stalled / N commits behind" is SQUASH-ACCOUNTING NOISE, not real backlog (2026-06-17)

**The operator's "we're staging, doing nothing faster than we can clear it" is 90% illusory.** The deployment-UI Repos
CI page showed 15 repos "drain stalled" with "199 commits behind / 37 files ahead / 6d lag" etc. and a 29-deep "Conflict
wall" triage queue. Direct measurement (`git diff --name-only origin/staging origin/live-defi-rollout`) proves:

- **deployment-api, ibkr-gateway-infra (UI: "208 behind"), trading-agent-service ("219"), system-integration-tests
  ("189"), client-reporting-api, market-tick-data-service, … = 0 FILES content-delta.** staging AND main are already
  CONTENT-IDENTICAL to LDR. The huge "commits behind" is pure squash-merge history divergence (`ahead_by>0`, `files:[]`)
  — the exact "noise to collapse, not work to merge" case from CLAUDE.md § "LDR is the SSOT". The Tier-C drain bot
  already knows this: it auto-closes such promote PRs with _"staging tree == LDR tree (content-identical; the ahead_by
  gap is squash-accounting noise)"_.
- The **deployment-UI / Repos-CI monitor measures COMMIT-count divergence (and a files-touched-across-commits count),
  NOT net tree-delta** → it perpetually shows a fake backlog that can never "clear" (squash-merges keep `ahead_by`
  climbing forever). This is the source of the "doing nothing faster than we clear it" perception.

### What was GENUINELY stuck (now fixed this session)

1. **~29 stale `dep-update/*` PRs** (the real "conflict wall") — redundant under the range-pin/pull model (internal dep
   floors `>=0.x,<1.0.0` absorb every minor bump; the floors were already on LDR). **CLOSED all of them** (0 open
   dep-update PRs fleet-wide now, verified). Composes with the digest-only-on-minor fix (24/24 LDRs) that stops new ones.
2. **UAC + UTL real staging→main content** (UAC 37 files/+4823; UTL 31 files) blocked by **CONFLICTING staging→main
   PRs** (UAC #344, UTL #370). Root cause = the staging→main merge-base is stale because **staging never receives a
   `main` back-merge — only LDR does** (`main-backmerge-to-ldr` + `staging-backmerge-to-ldr` both converge on LDR; there
   is no `main→staging`). LDR carries main's back-merge → the clean reconcile path is **LDR→main** (like PM Option-B).
   Resolved: **UAC #353 (LDR→main) MERGED** ✅, **UTL #376 (LDR→main) armed** (v2-gated); stale #344/#370 closed as
   superseded. No SIT bypass — auto-merge (non-admin) respects all required checks; v2 passed on the additive content.
3. **e2e-testing** — the only repo with a genuine staging→LDR divergence (staging had 2 dep-pin commits LDR lacked).
   Back-merged staging→LDR, resolved `pyproject.toml` (kept higher `strategy-service>=0.14.0` floor + LDR driftpy NOTE).
4. **deployment-api + batch-live-reconciliation-service** "fails quarantined" = STALE (content-identical 0/0 → nothing
   to promote; the quarantine flag never cleared).

### Structural root-cause fixes (so this stops recurring)

- [x] ✅ [CICD] P1. **Repos-CI triage queue measures CONTENT-delta, not commit-count — SHIPPED 2026-06-17**
      (deployment-api@e35dd00c, LDR; Tier-C drains to staging). Root: `classify_stuck_pr` keyed only on
      `mergeable_state`/`v2_present`, so a content-identical promote PR (staging==main==LDR by tree, but `ahead_by>0` and
      CONFLICTING/BLOCKED off a stale squash merge-base) was flagged `v2_never_reported`/`conflicting` → phantom "Conflict
      wall" in the triage queue (the operator "doing nothing faster than we clear it"). Fix: `branch_head` now returns the
      head commit `tree_sha` (the reliable content fingerprint — the compare API's three-dot `files` is inflated by the
      stale merge-base, e.g. 37 "files" for an identical tree); `classify_stuck_pr` short-circuits to `None` when
      `base.tree_sha == head.tree_sha`. `drain_stalled` was already content-based (LDR-relative deltas, `behind_by=0` →
      reliable `files_changed`). **Verified live** (slot-3 stack, real GitHub): deployment-api #101 → `content_identical=True`,
      `stuck_class=None`, dropped from the queue; remaining stuck PRs all `content_identical=False` (genuinely
      content-bearing). 21 unit tests (2 new guard cases incl. the CONFLICTING-but-identical #101 case); basedpyright clean;
      QG green. `repo_ci.py` / `_repo_ci_{stuck,github,types,mocks}.py` + `test_repo_ci_stuck.py`. SSOT § Class D.
  - [ ] [CICD] P2 (residual). **deployment-ui `RepoCi.tsx` per-row "N commits behind" TEXT** still renders `ahead_by`
        prominently for the LDR↔staging↔main columns. The backend `deltas` carry the honest `files_changed`; the UI should
        lead with the net file-delta (render "in sync (squash skew)" when `files_changed==0` despite `ahead_by>0`), like the
        LDR→main delta column already does. Frontend-only display polish — the operationally-painful phantom-stuck queue is
        already fixed above. Target: `deployment-ui` (Repos CI page). [UI] — needs `pw:L2` evidence.
- [ ] [CICD] P1. **staging→main promote PRs perpetually CONFLICT (stale merge-base).** `staging` gets no `main`
      back-merge (only LDR does via `main-backmerge-to-ldr`), so any `main`-only commit (semver version promotes,
      ci_status) makes every `staging→main` PR CONFLICTING. Fix (pick one, target PM promote workflows): (a) add a
      `main-backmerge-to-staging` tick mirroring `main-backmerge-to-ldr`, OR (b) make `staging-to-main`/`ldr-to-main`
      promote bots use the **LDR→main reconcile path when staging→main conflicts** (LDR is the SSOT + carries both
      back-merges — this is the PM Option-B pattern generalised to service/lib repos). Provenance: UAC #344 / UTL #370.
- [ ] [CICD] P2. **Stale "fails quarantined" flag never clears when content becomes identical.** deployment-api + blrs
      showed "N fails quarantined / escalated" while staging==main==LDR (0 content-delta). The quarantine/breaking-pending
      writer should clear the flag when the promote range's content-delta is 0. Target: the quarantine/`breaking_pending`
      writer (PM `ci_status` / staging_status). Provenance: this session.

## Manual drain of the residual triage queue + a NEW gate finding — 2026-06-17 (afternoon)

The structural fixes at § "Structural root-cause fixes" are NOT yet shipped, so the queue kept refilling. Drained the
residual **manually** (operator-directed) and surfaced a new systemic gate:

- **Closed 4 squash-NOISE staging→main PRs** (content-identical by TREE → nothing to promote): `alerting-service#97`,
  `agent-orchestrator#322`, `execution-service#314`, `instruments-service#471`. (deployment-api#101 stayed open — it later
  re-evaluated as REAL once the monitor fix landed on its LDR; draining via v2.)
- **Merged the 5 GENUINELY-stuck promote PRs** via **close+reopen → fresh `pull_request` v2 + re-arm auto-merge**:
  `ml-service#123`, `instruments-service#472`, `unified-trading-api#414`, `features-service#573`; and an **LDR→main
  reconcile** for the conflict-walled `strategy-service#211` → **#213** (main ⊆ LDR → clean; #211 closed superseded —
  exactly the option (b) at line 299 / the UAC#353·UTL#376 Class-C pattern, done by hand).
- **Shipped the monitor content-identity guard** — see § Class D P1 above, flipped (deployment-api@e35dd00c).

- [ ] [CICD] P1. **NEW — promote PRs strand on a `quality-gates-v2` run that completes `conclusion=action_required`
      (NOT `success`), so the required check is non-green → PR BLOCKED with auto-merge armed but unable to fire.** Hit
      ≥4 PRs at once today (`features-service#573`, `ml-service#123`, `unified-trading-api#414`, `unified-trading-pm#392`).
      Two facts pinned: (1) a `workflow_dispatch` v2 does NOT satisfy a PR's required context — only a `pull_request`-event
      run counts (so `gh workflow run quality-gates-v2.yml --ref <branch>` is the WRONG recovery for a stuck PR; it greens
      the SHA but not the PR check). (2) `action_required` here is NOT a fork-approval (`/approve` API → "not from a fork
      pull request") and has **0 pending_deployments** — root still unknown (a conditional cloud-build/deploy job?).
      Proven recovery = **close+reopen** (fires a fresh `pull_request` v2, which went `success` for all 5 today). But
      `ci-failure-watcher --auto-recover` only handles the v2-**ABSENT** signature, NOT v2=`action_required` — so these
      strand until a human nudges. **Fix:** (a) diagnose what makes a v2 run conclude `action_required` vs `success`
      (intermittent — same head went `success` at 04:04 then `action_required` at 04:41); (b) extend
      `ci_failure_watcher.py` auto-recover to include the `conclusion==action_required` signature (close+reopen recovers it
      deterministically). Target: `scripts/repo-management/ci_failure_watcher.py`. Provenance: 2026-06-17 afternoon drain.
