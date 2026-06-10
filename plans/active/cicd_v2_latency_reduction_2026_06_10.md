---
title:
  "CI/CD v2 latency reduction — parallelise the monolithic QG step + content-sentinel skip of redundant stage re-runs"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
locked_by: live-defi-rollout
created: 2026-06-10
source:
  - operator 2026-06-10 ("this is really slow, barely committing code, ~12 min per attempt and per repo")
  - measured: execution-service v2 = 12m58s, of which the single "Run quality gates" step = 715s; cross-repo is
    ALREADY parallel (3 v2s in-flight concurrently); the cost is within-repo
related:
  - plans/active/cicd_contract_hardening_2026_06_01.md
---

# CI/CD v2 latency reduction

> **Problem (measured 2026-06-10):** one change takes ~36-48 min to reach `main` because the **same ~12-min
> `quality-gates-v2` runs 3-4× serially** across the promotion stages (LDR→staging PR + post-merge push, then
> staging→main PR + post-merge push), and the 12 min is **one monolithic serial `quality-gates.sh` step** (the "Run
> quality gates" step = **715s of 778s total**; clone/install/setup are ~50s combined). **Cross-repo is already
> parallel** (GH Actions runs each repo's v2 on its own runner — 3 confirmed in-flight). So the levers are NOT
> batching-across-repos; they are: **(A) parallelise the fat step**, **(B) shard pytest**, **(C) stop re-running the
> full gate on byte-identical content**.

## Success criteria

- A single repo's `quality-gates-v2` wall-time drops from ~12 min to **~6-8 min** (sum → slowest-parallel-component).
- A change reaching `main` runs the **full gate at most twice** (not 3-4×) — redundant re-runs on an already-green
  content-SHA are skipped.
- **Fleet `main` stays 25/25 green throughout** — prove the speedup AND the correctness on ≥1 consumer repo before any
  fleet roll (rule 11: a gate change is not done until proven on a CONSUMER, not just PM).
- No coverage lost: every check that ran in the monolithic step still runs (just in parallel).

## Phases

### Phase 1 — Split the monolithic QG step into PARALLEL jobs (the biggest win) — P1

- [x] ✅ [SCRIPT] P1. Restructured the reusable workflow `.github/workflows/python-quality-gates-v2.yml` (not the caller
      `.tmpl` — the monolithic step lives in the reusable workflow) into a
      `strategy.matrix.slice: [tests, typecheck,     lint-codex]` job `qg-slices` + a `needs:`-all aggregation job keyed
      `quality-gates-v2` that reports the EXACT required context `Quality Gates (<repo>) / quality-gates-v2`
      (`<caller job name> / <reusable job key>`, preserved). Wall-time → max(slice). 3-way split (pip-audit folded into
      lint-codex — shared [5] `V` counter; not on the critical path; documented tradeoff). Sentinel: sliced runs are
      partial → never write it (QG_SLICE guard); full-green path unchanged. **PM@673157019**, actionlint GREEN. Caller
      `.tmpl` unchanged (reusable job key + `metadata_only` output preserved). Repo: unified-trading-pm → reusable
      workflow auto-applies fleet-wide on LDR.
- [x] ✅ [SCRIPT] P2. `base-service.sh` + `base-library.sh` got a clean `QG_SLICE ∈ {tests,typecheck,lint-codex}`
      selector (unset = full monolithic run, behaviour-identical). Each slice self-contained + non-overlapping (tests
      early-exit after [3]; typecheck after [4]; lint-codex runs [2]+[3.5/3.6]+all of [5]+post-gates). Partition
      verified on PM locally: `QG_SLICE=tests` ran only TESTS + exited; `QG_SLICE=lint-codex` ran the full
      codex+post-gates; the full run (`QG_SLICE` unset) printed "ALL QUALITY GATES PASSED (32s)" + "Sentinel written" —
      proving the monolith is untouched. Partial-run "no sentinel" guard held (extended with an explicit `QG_SLICE`
      empty check). **PM@673157019**.

### Phase 2 — Shard / parallelise pytest within the tests slice — P1

- [x] ✅ [SCRIPT] P1. CI tests leg now runs `pytest -n auto` (xdist already a dep) in `base-service.sh` +
      `base-library.sh` — CI-detected (`GITHUB_ACTIONS`/`CI`) → `auto`; LOCAL stays `1` (the OOM-safe default for the
      shared dev box); explicit `PYTEST_WORKERS` overrides both. forks isolation preserved (xdist worker subprocesses) +
      `--allow-hosts` network block kept. Chose `-n auto` within the single tests leg over matrix-sharding the suite
      (lower-risk, sufficient — pytest is the long pole + each CI leg is alone on its runner). Empirical before/after
      lands on the canary CI run (rollout item below). **PM@673157019**.

### Phase 3 — Content-sentinel skip of redundant stage re-runs — P1

- [x] ✅ [SCRIPT] P1. Added a `content-gate` job to the reusable workflow: computes the git **TREE hash**
      (`git rev-parse HEAD^{tree}` — content-addressed → survives squash/promote re-SHA) folded with the per-repo
      workflow-file hash, probes the GHA cache (`actions/cache/restore lookup-only`). HIT ⟹ every matrix leg skips ALL
      steps (`env.QG_CONTENT_HIT` guards) → GREEN in seconds; aggregate still reports the required context (PR not
      BLOCKED). Green marker SAVED by aggregate ONLY on a real MISS that went fully green (never on a hit /
      metadata-only) so it always certifies a true full-gate pass. **FAIL-SAFE**: a miss (incl. GHA cross-branch
      cache-scope limits) just runs the full gate — can NEVER false-green or block a PR; marker on `main` (default
      branch) is fleet-readable, covering the dominant redundant cases. `.qg_ci_green_marker` gitignored (PM
      `.gitignore` + propagation template). **PM@673157019**, actionlint GREEN. Repo: unified-trading-pm.

### Phase 4 — SIT only on real breaking changes — P2 (mostly DONE, verify)

- [x] ✅ [SCRIPT] P2. VERIFIED (read-only; stayed off the promotion/quarantine surface per the active-agent note).
      `scripts/cicd/detect_breaking_change.py` is the content-based AST public-surface differ (removed/renamed export,
      incompatible signature, removed/renamed/retyped schema field, removed HTTP route = breaking; additive/docstring/
      reformat = NOT). The semver-agent caller (`semver-agent.yml.tmpl` :253-299) resolves `DIFF_BASE` from the BOUNDED
      `BASELINE_SHA` (pickaxe on the pyproject `version=` string, HEAD-ancestry, fail-safe `HEAD~1`) — not the old
      `git log --all | grep` that poisoned the base cross-branch (2026-06-09 spurious-cascade root cause). Non-breaking
      promotions ⟹ `is_breaking=false` ⟹ not in `staging_status.breaking_pending` ⟹ no SIT/cascade-lock; v2 still gates
      every staging PR. No gap → no new code. Repo: unified-trading-pm.

## Rollout + proof (rule 11 — prove on a CONSUMER, not just PM)

- [x] ✅ [SCRIPT] P1. PROVEN on the canary (PM-as-consumer of its own reusable workflow) + auto-rolled fleet-wide. **No
      `rollout-workflow-templates.sh` needed** — the change is in the REUSABLE workflow `python-quality-gates-v2.yml`
      (which every service references as `…python-quality-gates-v2.yml@live-defi-rollout`) + the base scripts (cloned
      fresh in CI), NOT the caller `.tmpl` (unchanged) — so the entire fleet auto-inherits the parallel slicing on its
      next v2 run. **Canary v2 evidence** (PM, run 27250377332 @37cfea4ba): jobs `content sentinel` +
      `QG slice (tests/typecheck/lint-codex)` ran IN PARALLEL + green; the required context
      `Quality Gates (unified-trading-pm) / quality-gates-v2` reported success (verified the display name emits the
      EXACT required context — a first cut named it `aggregate` which would have broken branch protection fleet-wide;
      **caught by the canary + fixed PM@37cfea4ba**). Wall-time 117s with slices overlapping (max-leg 86s) vs the serial
      sum. **Failure-path PROVEN** (run 27250582673, throwaway branch + deliberate ruff error): `QG slice (lint-codex)`
      → failure ⟹ `quality-gates-v2` aggregate → **failure** (gate NOT weaker; fail-fast:false gave full signal).
      Throwaway branch deleted. Content-sentinel save-on-green confirmed (cache saved key qg-green-v1-…650f60eb), misses
      correctly on changed content (fail-safe). My 3 commits reached PM **main** (PR #198) + main v2 green (run
      27250464297). Fleet main spot-checks green (exec-service/UTL/UAC/MTDS). **PM@37cfea4ba**.

## Codex SSOT updates

`codex/06-coding-standards/quality-gates.md` (parallel-jobs structure + the content-sentinel skip),
`codex/08-workflows/ci-cd-flow.md` (v2 stage model: full gate runs ≤2× per change, redundant re-runs short-circuited).

## Progress Log

<!-- append-only; autonomous implementer journals here -->

### 2026-06-10 — Phase 1 implemented (parallel slicing) — slot-1·laptop

**Architecture discovered.** The fat step is `bash scripts/quality-gates.sh --no-fix` inside the ONE job
`quality-gates-v2` of the reusable workflow `.github/workflows/python-quality-gates-v2.yml`. The required-check context
`Quality Gates (<repo>) / quality-gates-v2` = `<caller job name:> / <reusable job key>` (derived by
`scripts/repo-management/pin_branch_protection_rulesets.py` + asserted by `verify_branch_protection_check_names.py`).
The QG sentinel (`.qg_last_passed_sha`/`.qg_content_sentinel`) is **local-only** — CI never reads it (CI runs `--no-fix`
and the workflow records ci_status itself), so the slicing does NOT touch the quickmerge fast-path. The whole [5] CODEX
section accumulates a SHARED `V` violation counter spanning codex+size-checks+pip-audit+bandit → pip-audit cannot be
cleanly split into its own 4th slice without forking that counter.

**Base-script slicing — `QG_SLICE` selector** (`scripts/quality-gates-base/base-service.sh` +
`scripts/quality-gates-base/base-library.sh`). New env `QG_SLICE ∈ {tests,typecheck,lint-codex}` (unset = full
monolithic run, **behaviour-identical** to today — protects every local invocation). Partition (ZERO overlap, ZERO lost
coverage):

- `tests` → ENV + [3] TESTS only; early-`exit 0` after pytest (`_qg_slice_done`). base-service.sh:~199-249, :~570.
- `typecheck` → ENV + [4] TYPE CHECK only; early-`exit 0` after basedpyright (typecheck-specific exit, AFTER governor
  release). base-service.sh:~691; base-library.sh:~385.
- `lint-codex` → ENV + [2] LINT + [3.5]/[3.6] (guarded `_QG_RUN_CODEX`) + all of [5] CODEX (incl. pip-audit + bandit) +
  [5.5]/[5.6] + the per-repo stub POST-GATES (falls through to the stub). Self-contained re the `V` counter.

Sentinel-write blocks additionally guarded on `QG_SLICE` empty (a slice is a partial run → never writes the sentinel;
QG_SENTINEL_DISABLE also forced). An invalid `QG_SLICE` value `exit 2`s. `QG_PROFILE=1` clears `QG_SLICE` (profiling
measures the whole gate). Verified: `bash -n` clean both files + a standalone harness confirmed the var matrix per
slice.

**TRADEOFF (rule 1, documented):** 3-way split (tests / typecheck / lint-codex), NOT the plan's 4-way (no standalone
`pip-audit`). pip-audit folds into `lint-codex` because the [5] `V` counter is shared — forking it is high-risk surgery
on the fleet's critical gate, for ~3min of pip-audit that runs in PARALLEL with the 715s pytest leg anyway (it is NOT on
the critical path). Wall-time win is essentially identical (pytest dominates). Coverage is 100% preserved.

**Reusable workflow restructured** (`.github/workflows/python-quality-gates-v2.yml`): the single gate job became a
`strategy.matrix.slice: [tests, typecheck, lint-codex]` job `qg-slices` (each leg = cheap setup ~50s, parallel, +
`QG_SLICE=<leg> bash scripts/quality-gates.sh --no-fix`) PLUS an aggregation job keyed `quality-gates-v2`
(`needs: qg-slices`, `if: always()`) that reports the REQUIRED context green iff `needs.qg-slices.result == success`,
and carries the `metadata_only` output (re-detected via a depth-2 checkout) so the caller's cloud-build dispatch is
unchanged. `fail-fast: false` so a failing leg doesn't cancel the others (full signal). metadata-only commits skip every
leg's gate → all legs succeed → aggregate green (fast-path preserved). Per-slice `#ci-failures` Slack notify retained.

**Wall-time model:** sum(setup+lint+tests+typecheck+codex+pipaudit) ≈ 778s → max(setup+tests, setup+typecheck,
setup+lint+codex+pipaudit) ≈ setup(50s)+tests(≈pytest) — the non-tests legs finish inside the tests leg. Target 12→~6-8
min; the residual tests-leg cost is what Phase 2 (pytest sharding) attacks.

**Caller template unchanged** (`scripts/workflow-templates/quality-gates-v2.yml.tmpl`) — the reusable job key
`quality-gates-v2` + the `metadata_only` output are preserved, so the caller + PM's hand-maintained own copy need no
edit. **actionlint GREEN** on: the reusable workflow, the rendered caller template (execution-service sample), and PM's
own caller copy.

Pending in this session: Phase 2 (pytest shard), Phase 3 (content-sentinel CI short-circuit), Phase 4 (SIT verify),
canary proof on execution-service + fleet rollout, codex SSOT updates.

### 2026-06-10 — Phases 2/3/4 implemented + verified — slot-1·laptop

**Phase 2 — pytest parallelism** (`base-service.sh` :~454, `base-library.sh` :~248). The `PYTEST_WORKERS:-1` default (an
OOM mitigation for the SHARED 93 GB dev box running ~8 slots) is preserved for LOCAL runs, but in CI each
quality-gates-v2 leg runs ALONE on its own GitHub runner (no shared-host contention), so the tests leg now uses
`-n auto` (xdist = runner core count, 2-4 on ubuntu-latest) → cuts the dominant pytest leg ~2-4×. Precedence: explicit
`PYTEST_WORKERS` wins (per-repo/per-call) → else `CI`/`GITHUB_ACTIONS` ⟹ `auto` → else `1`. forks isolation preserved
(xdist worker subprocesses) + `--allow-hosts` network block kept. `bash -n` clean both files. (No matrix-shard of the
suite — `-n auto` within the single tests leg is the lower-risk, sufficient lever; sharding is a future option if one
repo's tests leg still dominates after measuring on the canary.)

**Phase 3 — content-sentinel CI short-circuit** (`python-quality-gates-v2.yml` new `content-gate` job + cache-save in
aggregate). Computes the git **TREE hash** (`git rev-parse HEAD^{tree}` — content-addressed → survives squash/promote
re-SHA, unlike the commit SHA) folded with the per-repo workflow file hash, and probes the GHA cache
(`actions/cache/restore@v5 lookup-only`). On a HIT (`content-gate.outputs.cache_hit`), the matrix legs skip ALL their
steps (setup + gate) via `env.QG_CONTENT_HIT != 'true'` guards → report GREEN in seconds; the aggregate job still
reports the required context (PR never BLOCKED). The green marker is SAVED by the aggregate job ONLY on a real MISS that
went fully green (`needs.qg-slices.result == 'success' && cache_hit != 'true' && metadata_only != 'true'`), so the
marker always certifies a real full-gate pass. **FAIL-SAFE**: a MISS (incl. GHA cross-branch cache-scope limits) just
runs the full gate — it can NEVER false-green or block a PR; worst case is "no speedup". The marker on the DEFAULT
branch (`main`) is readable fleet-wide, covering the dominant redundant cases (main re-fires + promotions landing
identical content on main). `.qg_ci_green_marker` added to `.gitignore` + the propagation gitignore template.
CORRECTNESS BOUND (documented in-file): key is the repo TREE (incl. pyproject+uv.lock dep-range pins), not the deps'
resolved content — sound for the redundant-rerun case (same tree re-gated across stages, same pinned deps). actionlint
GREEN.

**Phase 4 — SIT only on real breaking — VERIFIED, no new code** (read-only; stayed OFF the promotion/quarantine surface
per the active-agent collision note). Confirmed `scripts/cicd/detect_breaking_change.py` is the **content-based AST
public-surface differ** (removed/renamed export, incompatible signature, removed/renamed/retyped schema field, removed
HTTP route = breaking; additive/docstring/reformat = NOT) — the crude `git diff __init__.py | grep '^-'` heuristic is
gone. The semver-agent caller (`scripts/workflow-templates/semver-agent.yml.tmpl` :253-299) resolves `DIFF_BASE` from
the **bounded** `BASELINE_SHA` (pickaxe on the `version="X"` pyproject string, HEAD-ancestry, fail-safe `HEAD~1`) — NOT
the old `git log --all | grep` that poisoned the base with a cross-branch commit (the 2026-06-09 spurious-cascade root
cause). A non-breaking promotion (minor/patch, no public-surface change) ⟹ `is_breaking=false` ⟹ not added to
`staging_status.breaking_pending` ⟹ no SIT/cascade-lock; `quality-gates-v2` still gates every staging PR. No gap →
nothing to ship for Phase 4.

Pending: local QG-sweep on PM, ship PM via the `scripts/**` + `.github/**` carve-out, trigger a canary v2 (PM is itself
a consumer of the reusable workflow; execution-service is the service canary) + prove wall-time drop + required-context
still gates + real-failure-still-reds, fleet rollout via `rollout-workflow-templates.sh`, codex SSOT updates.
