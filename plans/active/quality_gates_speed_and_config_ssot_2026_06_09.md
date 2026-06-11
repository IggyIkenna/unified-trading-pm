---
title: Quality-gates speed (change-scoped, single-core) + config SSOT centralisation (toml as single home)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
created: 2026-06-09
locked_by: live-defi-rollout
related_plans:
  - plans/active/qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md
  - plans/active/ci_local_qg_parity_2026_06_08.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/archive/2026_06/quality_gates_resource_contention_speedup_2026_06_02.md
source:
  - operator design discussion 2026-06-09 (Harsh) — single-core wall-time + change-scoped gate + config-SSOT drift
  - discovery: MTDS MIN_COVERAGE=28 (stub) vs fail_under=71 (pyproject) — toml silently shadowed by --cov-fail-under
---

# Quality-gates: faster (change-scoped, single-core) + one config home (toml)

> Two axes, one effort. **Axis A — speed**: lower per-repo WALL-TIME on a SINGLE core by doing only the work a change
> actually requires, NOT by adding parallelism (parallelism gives false wall-time, doesn't help the 20-repo case, and
> OOMs the host — see archived `quality_gates_resource_contention_speedup_2026_06_02.md`). **Axis B — config SSOT**:
> collapse every QG setting that today lives in BOTH `scripts/quality-gates.sh` (stub) AND `pyproject.toml` into a
> single home (toml), the same way `pyrightconfig.json` + standalone ruff config were already folded into toml. The two
> axes met because the speed audit surfaced the dual-SSOT drift (MTDS coverage 28-vs-71).
>
> **Hard invariant across everything below: no speedup may drop measured coverage or let a real violation through.**
> Every fast path is a LOCAL ITERATION convenience; the merge boundary (quickmerge Pass-1 / CI `quality-gates-v2`)
> always runs the FULL gate with FULL coverage. Speed is bought by scoping the _iteration loop_, never by weakening the
> _gate_.

## Problem statement

1. A 2-line change in a repo with 1000s of files triggers a full QG run — all tests, full basedpyright over
   `SOURCE_DIR/`, ~60 codex grep/AST checks over the whole tree, pip-audit (OSV network, 180s timeout), bandit,
   actionlint. Baseline wall times are ~4.5–7 min/repo (`scripts/dev/qg_resource_baseline.json`: alerting 319s,
   deployment-api 401s, …). That is the iterate→quality-gates→quickmerge loop tax.
2. Parallelism is the wrong lever: it hides true single-core cost, and at 20-repo fan-out it OOMs (incident history) —
   the host governor already exists to _prevent_ over-parallelism, not encourage it.
3. The green content-sentinel (`.qg_content_sentinel`) already handles "tree UNCHANGED → skip heavy phases." The gap is
   "tree changed SLIGHTLY → run only the impacted subset," with coverage preserved.
4. Config drift: the same logical setting lives in the stub AND in toml and silently diverges. Confirmed: MTDS
   `MIN_COVERAGE=28` (stub) vs `[tool.coverage.report] fail_under=71` (toml), where base-service.sh's
   `--cov-fail-under=$MIN_COVERAGE` SHADOWS the toml value. 7 of 22 repos' stub-vs-toml coverage numbers already differ;
   other tool configs (pytest testpaths, bandit skips, tool-version pins, exclude lists) are duplicated too.

## Non-goals

- Adding test parallelism / raising `PYTEST_WORKERS` / raising the host-governor K as the primary speed lever.
- Weakening any gate, lowering any coverage floor to "go faster," or skipping a check at the MERGE boundary.
- Re-doing the shipped resource work (governor / mem-cap / sentinel) — extend it, don't duplicate it.

---

## Phase 0 — MEASURE FIRST (data before any change)

> Per operator: "we are discussing and auditing first … conclusion when we have the data backing us." Phase 0 produces
> the datasets that decide every later phase. NO behaviour change in this phase. **We need, per PHASE, per REPO:
> wall-time AND peak/mean RAM (RSS).** The existing `profile_qg_steps.py` only measures per-phase WALL time (parsed from
> `log_section` headers), runs repos SERIALLY, does NO RAM tracking, and no core-pinning — so it must be
> extended/replaced.

### Measurement methodology (the harness must enforce all of these — else the numbers lie)

- **Per-phase RAM**: a sampler thread polls the QG process-TREE RSS (sum across the subtree, e.g. `/proc/<pid>/statm` or
  `smaps_rollup`) at ~5 Hz, timestamped; bucket each sample into the active phase by the `log_section` boundary
  timestamps → per-phase `peak_rss_mb` + `mean_rss_mb`. (cgroup `memory.peak` via systemd-run only covers the wrapped
  pytest/typecheck phases — the sampler is the general solution.)
- **Single-core semantics**: pin each repo's run to ONE core (`taskset -c <core>`), force `QG_THREAD_CAP=1`,
  `PYTEST_WORKERS=1`. Goal is true single-core wall-time, not parallel speedup.
- **Parallel measurement, not parallel execution**: run N repos AT ONCE, each pinned to its own core, with
  `QG_GOVERNOR_DISABLE=true` (else the flock token-bucket serializes them). Machine is 24-core / ~46 GB free → safe at
  ~8–10 concurrent service repos; gate concurrency on a RAM budget (sum of expected peaks < ~36 GB headroom; UTL peaks
  5.27 GB — schedule the heavy ones (UTL/UAC) without piling them together).
- **Make every phase actually run**: `QG_SENTINEL_DISABLE=true` (else an unchanged tree skips tests+typecheck → bogus ~0
  s), `QG_MEM_CAP=0` (else a >10 GB phase is SIGKILLed and you measure the cap, not the peak), and `--no-fix` (don't
  reformat/dirty trees during measurement).
- **Interference caveat**: parallel-pinned wall-time ≈ isolated single-core only if RAM doesn't swap and
  mem-bandwidth/disk contention is low. Confirm the heaviest repos (UTL, UAC) with a second ISOLATED single-run pass and
  compare.
- **Repeatability**: ≥2 runs per repo, report median; record host, core map, timestamp, git SHA per repo.

### Output (machine-readable, for analysis)

- Per-repo JSON: `{repo, total_wall_s, exit_code, sha, phases:[{name, wall_s, pct, peak_rss_mb, mean_rss_mb, status}]}`.
- One combined CSV (`repo,phase,wall_s,peak_rss_mb,mean_rss_mb,status`) for pivoting across all repos.
- Raw per-repo JSON/txt/markers/logs land in the **gitignored `.qg_profile/` scratch dir** (large intermediates — NEVER
  committed; the runner hard-refuses a git-tracked `--outdir`). Only the authored summary
  `plans/audit/results/qg_step_profile_2026_06_09.md` is committed.
  - [x] ✅ [INFRA] P0. **Measurement must NOT dirty the trees — TWO leak/dirt mechanisms found + fixed (2026-06-11).**
        (1) **Auto-fix dirtied 20+ repos**: `QG_PROFILE=1` was forcing `FIX_MODE=true`, so every profiled repo got a
        tree-wide `prettier --write "**/*"` + `ruff --fix` — the exact churn `FIX_MODE` defaults false to avoid. Fixed
        in BOTH `base-service.sh` + `base-library.sh` (QG_PROFILE keeps `FIX_MODE=false`, matching this plan's "--no-fix
        during measurement" methodology); the small auto-fix span cost is not worth dirtying the fleet. (2) **Markers
        leaked into repos**: a RELATIVE `--outdir` resolved against the gate's `cwd=<repo>`, writing
        `<repo>.markers.jsonl` into 22 repo trees. Fixed: outdir resolved ABSOLUTE + a guard refuses any git-tracked
        outdir. Cleanup: removed all leaked markers/smoke dirs + reverted 72 auto-fixed (formatting-only,
        token-identical-to-HEAD) files across the fleet; real-content WIP left untouched. — base-service.sh +
        profile_qg_resources.py (unified-trading-pm@022c3113e)

### Phase 0 todos

- [x] [SCRIPT] P0. Build/extend the profiler harness to capture **per-phase peak+mean RSS** (sampler thread) alongside
      the existing per-phase wall-time, emit the per-repo JSON + combined CSV schema above. (`profile_qg_steps.py` today
      does wall-only/serial/no-RAM — extend it or add a `profile_qg_resources.py` companion.) ✅ —
      `profile_qg_resources.py` (existed) extended 2026-06-10: combined CSV
      (`repo,phase,wall_s,peak_rss_mb,mean_rss_mb,status`; span rows prefixed `span:`), `--repos a,b,c` SERIAL
      multi-repo mode, `--output` alias for `--outdir`, macOS portability (ps-pgid RSS fallback + unpinned-when-no-
      taskset, flagged in report) so smokes run on operator laptops. — unified-trading-pm (unified-trading-pm@779dc3683)
- [x] ✅ [SCRIPT] P0. **Parallel-pinned measurement runner — DONE** (`profile_qg_resources.py --parallel`,
      unified-trading-pm@022c3113e). Each repo runs on its OWN core (`taskset -c`, pool `--cores`, default nproc-4)
      under a weighted **RAM-token budget** (`--ram-budget-gb`, default 0.8×MemAvailable; per-repo `--per-repo-gb` 4G /
      heavy UTL+UAC `--heavy-gb` 6.5G) so two heavies never overlap + the host never swaps — two limiters compose
      (free-core queue × RAM-token Condition). `--all` discovers every sibling repo with a `quality-gates.sh`. Each
      concurrent run still measures TRUE single-core wall (own pinned core + `QG_THREAD_CAP=1`/`PYTEST_WORKERS=1`). Uses
      the evolved **`QG_PROFILE=1`** full-no-skip override (supersedes the plan's original
      `QG_SENTINEL_DISABLE=true … --no-fix` combo — `QG_PROFILE=1` disables the sentinel, forces a complete run, relaxes
      only the `<MAX_DURATION>` meta-gate, in BOTH bases) + `QG_GOVERNOR_DISABLE=true QG_MEM_CAP=0`. Per-repo raw stdout
      → `<repo>.log` (no interleave), per-repo JSON/txt + combined CSV + a cross-repo summary with a
      **`complete`/`⚠PARTIAL`** flag. Validated by a 3-repo parallel smoke (cores 2–4, budget tracked 28.8→20.8G,
      distinct per-repo wall+peak). — unified-trading-pm@022c3113e
  - [ ] [INFRA] P1. **Measurement-prerequisite finding (smoke 2026-06-11): some repo `.venv`s are incomplete → the gate
        EARLY-BAILS at TESTS and the profile is PARTIAL, not full.** greeks-service exited at `[3/6] TESTS` in 10 s on
        `❌ pytest-timeout required: uv pip install pytest-timeout` (vs ibkr/alerting which ran all of `[0/6]→[5/6]` and
        only failed at the final CODEX step — a _complete_, usable measurement). The runner now flags these
        (`complete:     false` / `⚠PARTIAL` in the summary) so they're excluded from timing, but the underlying gap is
        real per-repo venv hygiene: a stale slot `.venv` missing a dev dep (`pytest-timeout`). Before/after the full
        sweep, repair the flagged repos' venvs (`setup.sh` is idempotent) and re-profile ONLY those, so the wall+RAM
        table has full-run numbers for every repo. Provenance: parallel-runner smoke.
- [x] [TEST] P0. **Smoke-test on ONE repo first** (e.g. MTDS or a small service) — verify the RAM sampler attributes
      peaks to the right phase and every phase actually ran (sentinel disabled), BEFORE fanning out to all 22.
      (smoke-then-scale.) ✅ — 2× smoked: instruments-service (2026-06-09, Linux-style /proc path — see findings
      below) + ibkr-gateway-infra full profiled gate 2026-06-10 on macOS (exit 0, 25.73 s total, 111 RSS samples, all 9
      spans present incl. autofix/tests/typecheck — sentinel-disabled full run confirmed; peaks attributed: codex 259 MB
      / tests 140 MB / pip-audit 92 MB; combined.csv 73 rows). macOS numbers are UNPINNED/indicative; the 22-repo
      canonical sweep still runs pinned on Linux. — unified-trading-pm (unified-trading-pm@779dc3683)
- [x] ✅ [AUDIT] P0. Full sweep DONE (2026-06-11, 25 repos / 19 complete, 24-core host). Per-phase wall+RAM table landed
      in `plans/audit/results/qg_step_profile_2026_06_09.md`. **Findings: tests=59.5% wall (+ 5.5 GB peak RAM, both #1);
      codex=21.7% (the real #2, NOT basedpyright); typecheck=10.5% (warm cache, tiny RAM); pip-audit 3.5% (cached).**
      Hypothesis refined: pytest dominates wall+RAM as expected, but **codex > basedpyright** for #2 — and codex
      OVERTAKES tests on large repos (execution-service codex 409>387; deployment-api 245>168) because the grep/AST
      checks scan the whole tree.
- [x] ✅ [AUDIT] P0. **Phase scopability classification DONE** (table in `qg_step_profile_2026_06_09.md`). SCOPABLE →
      tests (impact-sel), codex (per-file grep/AST), typecheck (changed+rev-deps), size-checks, bandit = **91.7% of
      wall, all change-scopable**; FIXED-COST-CACHEABLE → pip-audit (deps-hash); NON-OPTIONAL-FULL → removed-symbols
      (cross-repo, cron) + lint (already negligible). Conclusion: scoping tests+codex+typecheck to the changed-file set
      is the fast tier; merge boundary always runs full.
- [ ] [AUDIT] P0. **Phase scopability classification** (drives Phase 2): tag each phase NON-OPTIONAL-FULL (must run over
      the whole tree even for a 2-file change — e.g. ruff*, basedpyright*) vs SCOPABLE-TO-CHANGED-FILES (codex 5.x
      grep/AST, coverage-bearing tests via impact selection) vs FIXED-COST-CACHEABLE (pip-audit/bandit/actionlint). (\*
      the data may show even basedpyright can be changed-file-scoped on the fast tier with full at merge — let the
      numbers decide.)
- [x] [AUDIT] P0. Dual-SSOT matrix across all 22 repos: for every QG-relevant concept (coverage threshold, coverage
      source/omit/branch, pytest testpaths/addopts/markers, bandit skips, ruff/basedpyright/python version pins, exclude
      lists) record (a) toml location, (b) stub/base location, (c) does base pass a CLI flag that overrides toml?, (d)
      verdict ∈ {agree, drift, shadowed, bash-only}. Seed from the MTDS findings already gathered. Land as
      `plans/audit/results/qg_config_ssot_matrix_2026_06_09.md`. ✅ — landed 2026-06-10 (unified-trading-pm@779dc3683):
      all concepts classified (a)–(d); per-repo NUMERIC sweep complete for coverage (5 confirmed drifts: alerting 76/78
      · mdps 70/77 · mtds 28/71 · SIT 2/0 · uta 77/70 — uta/SIT are the silent-loosen direction) + `[tool.bandit]`
      presence (~20 repos, ALL dead — see next item). Residual depth (per-repo testpaths/omit/version-pin value columns)
      only needed if Phase 1 hits a repo-specific surprise — concept-level verdicts already decide the mechanism.
- [x] [AUDIT] P1. Verify the bandit-`-c` question definitively: does base-service.sh `bandit -r … -ll` (no
      `-c pyproject.toml`) actually read `[tool.bandit]`? If not, the per-repo `[tool.bandit] skips` are DEAD config (a
      shadowed-by-absence case). ✅ — VERDICT: **DEAD (shadowed-by-absence)**, verified empirically on bandit 1.9.4 /
      py3.13: without `-c` a toml-skipped B602 is still reported (exit 1); with `-c pyproject.toml` the skip is honoured
      (exit 0); `-c pyproject.toml` is safe even when the file has NO `[tool.bandit]` section (normal scan, no error) →
      the bases can add it unconditionally. Full transcript in the matrix doc. (unified-trading-pm@779dc3683)
- [ ] [AUDIT] P1. Per-repo `[tool.bandit] skips` audit BEFORE the bases add `-c pyproject.toml` — the ~20 repos' skips
      have been DEAD config (never enforced); re-activating them un-audited may silently suppress real findings (e.g.
      MTDS skips B608/B104/B108/B310). Review each list, prune, THEN flip the invocation. (discovered by the bandit
      verdict above, 2026-06-10)
- [x] [AUDIT] P1. Classify every knob into TIER-A (tool-native — toml is the home) vs TIER-B (bash-orchestration —
      governor/mem-cap/MAX_DURATION/PYTEST_WORKERS/codex-exclude-globs/pip-audit-ignores/size-limits — toml has no
      native home). This classification decides Phase 1's mechanism. ✅ — **13 TIER-A / 27 TIER-B**, full tables with
      per-knob migration notes in `plans/audit/results/qg_config_ssot_matrix_2026_06_09.md`; headline: `SOURCE_DIR` is
      the deepest duplication (5 declarations), QG\_\* env knobs stay host/session-scoped (NOT toml).
      (unified-trading-pm@779dc3683)

---

## Phase 0 findings + immediate fixes (2026-06-09, from instruments-service smoke)

Profiler capability SHIPPED (opt-in, gitignored): `qg_prof` hook in `qg-common.sh` + 9 instrumented spans in
`base-service.sh` (autofix/lint/tests/typecheck/codex/size-checks/pip-audit/bandit/removed-symbols), forced full-no-skip
run under `QG_PROFILE=1`, harness `scripts/quality_gates/profile_qg_resources.py` (per-phase wall + peak/mean RSS,
single-core pinned), output under gitignored `.qg_profile/`.

- [x] [SCRIPT] P0. `qg_prof` profiler hook + base-service instrumentation + `QG_PROFILE=1` full-run override +
      `profile_qg_resources.py` (markers→spans + RSS) + `.qg_profile/` gitignored. — unified-trading-pm (local)
- [x] [SCRIPT] P0. **FIX: STEP 5.65 removed-symbols mis-scope** — it used `basename/dirname "$REPO_ROOT"`, but
      `REPO_ROOT` IS the workspace root, so it AST-scanned the ENTIRE workspace (~146k `.py` incl. all `.tabs/` slot
      clones) single-threaded on EVERY repo's gate → **~286 s = 64% of wall-time, fleet-wide**. Fixed to
      `basename "$PROJECT_ROOT"` + `REPO_ROOT` (matches the already-correct STEP 5.67). + added `.tabs` to the checker's
      `EXCLUDE_DIR_NAMES`. Expected: 286 s → sub-second per gate. — base-service.sh + check_removed_symbols.py
- [ ] [INFRA] P0. **Part 3 — add the workspace-wide removed-symbols sweep** (cron/CI, `.tabs` excluded, run ONCE) to
      preserve the cross-repo guarantee that the per-repo scope narrows away. NO such sweep exists today (the mis-scope
      was accidentally serving as it). SSOT: check_removed_symbols.py docstring "run separately via CI cron".
- [x] [INFRA] P0. ✅ **pip-audit = 38 s (8%) OSV network** (now visible after decomposing the codex blob). Cache OSV
      results and/or move pip-audit to a deps-change/cron trigger instead of every gate run. Advisory gate → safe to
      move off the hot path. — unified-trading-pm base-service.sh + base-library.sh (unified-trading-pm@779dc3683): ONE
      mechanism covers both halves — deps-change trigger (key = pyproject.toml + uv.lock + ignore-set + pip-audit
      version → `.qg_cache/pip_audit_deps_hash`) + 24h freshness bound (`QG_PIP_AUDIT_MAX_AGE_HOURS`, the
      cron-equivalent for newly-published advisories). Clean-run-only caching (vulns/timeouts never cached);
      internal-advisories check stays uncached (PM-yaml input, not deps); SBOM upload moved inside the miss branch (a
      hit must not re-upload another repo's stale /tmp output); `QG_NO_CACHE=1` bypass; `.qg_cache/` gitignored (PM +
      canonical template) + excluded from the green-sentinel untracked hash. Verified in isolation: cold=MISS /
      unchanged+fresh=HIT / deps-change=MISS / 25h-stale=MISS / bypass=MISS.
- [x] [SCRIPT] P0. **Instrument base-library.sh** with the same `qg_prof` spans + `QG_PROFILE` full-run override
      (UTL/UAC are libraries — the heaviest repos, 5.27 GB peak — and currently have NO span instrumentation). Needed
      before the full 22-repo sweep covers libraries. ✅ — 2026-06-10 (unified-trading-pm@779dc3683): 8 span pairs
      (autofix/lint/tests/typecheck/codex/size-checks/pip-audit/bandit — base-library has no removed-symbols step) + the
      `QG_PROFILE=1` full-no-skip override block + `IGNORE_TIMEOUT` honour on the duration meta-gate (was missing in
      base-library — a profile run would have false-failed `<MAX_DURATION`). `bash -n` clean; zero behaviour change when
      `QG_PROFILE` unset (qg_prof is a no-op function; override inside the `== "1"` guard). End-to-end exercise rides
      the library legs of the 22-repo sweep (running a full UTL/UAC gate locally just for smoke exceeds host budget);
      the span mechanism itself is unit-verified + identical to the service base's, which passed the ibkr smoke.
- [ ] [AUDIT] P1. Typecheck numbers are **warm-cache** (~11 s); report BOTH cold (clear `BASEDPYRIGHT_CACHE_DIR`) and
      warm in the sweep so basedpyright isn't under-counted.

## Phase 1 — CONFIG SSOT: one home (toml), no shadowing

> Conclusion to validate with Phase 0 data: **toml is the single home for both tiers** — TIER-A via the tools' own
> tables, TIER-B via a new `[tool.quality-gates]` table that base-service.sh parses — so the per-repo stub collapses
> toward a one-line `source base-service.sh`.

- [ ] [DESIGN] P0. Decide the TIER-A rule: base-service.sh must STOP passing CLI flags that shadow toml
      (`--cov-fail-under`, explicit pytest test dir vs `testpaths`, bandit without `-c`). For each, either drop the
      override (let the tool read toml) or pass the tool its own config explicitly. Reconcile each of the 7 drifting
      repos to ONE honest value FIRST (a flip with no reconciliation reds MTDS/MDPS/alerting and silently loosens
      uta/SIT — see Phase 0 matrix).
- [ ] [DESIGN] P0. Design `[tool.quality-gates]` table schema for TIER-B knobs (e.g. `min_coverage`, `run_integration`,
      `pytest_workers`, `max_duration`, `codex_max_violations`, `pytest_unit_dir`, exclude-package lists,
      pip-audit-ignores). base-service.sh reads it (single toml parse) instead of stub bash vars. Keep a back-compat
      read of the stub var during migration, warn on divergence, then remove.
- [ ] [INFRA] P1. Implement base-service.sh + base-library.sh to read the `[tool.quality-gates]` table; make
      `MIN_COVERAGE` derive from `fail_under` (or the table) so the coverage number lives in exactly ONE place. Update
      coverage-floor-guard.sh to read the authoritative source and keep enforcing the system floor (70) + the
      signed-exception path.
- [ ] [REFACTOR] P1. Per-repo: move TIER-A duplicates out of the stub (rely on toml), collapse the duplicated exclude
      intent (e.g. "exclude market_interface" expressed in ~7 places) to the minimum each tool genuinely needs.
      Reconcile honest coverage values (MTDS: settle 28-vs-71 per the Axis-A outcome — likely 28 now, ratchet to 71 as
      ISS-031 tests land). **[CONFLICT-GUARD 2026-06-10 — operator-ratified]**: when syncing canonical [tool.ruff]
      sections into per-repo pyprojects, the DTZ + TID251 select entries must be EXCLUDED (they stay ratchet-only via
      STEP 5.95) OR per-repo per-file-ignores baselines must ship FIRST — otherwise every repo's plain ruff lint step
      hard-fails on the ~180 DTZ + ~211 TID251 pre-existing sites (instant fleet redness; the exact failure mode the
      ratchet design exists to avoid).
- [ ] [DOCS] P1. Update `codex/06-coding-standards/quality-gates.md` § config-SSOT: toml is the single home, the
      `[tool.quality-gates]` contract, the "base must never shadow toml on the CLI" rule.

---

## Phase 2 — CHANGE-SCOPED FAST TIER (the single-core wall-time win)

> Two-tier model. **Fast/iterative tier** = scoped to changed files + impacted tests; for the local dev loop; does NOT
> write the sentinel and is NOT sufficient to merge. **Full/merge tier** = today's complete gate with full coverage;
> writes the sentinel; runs at quickmerge Pass-1 / CI. The fast tier turns a 2-file edit from minutes into seconds
> without touching the gate's strength.

- [ ] [DESIGN] P0. Specify the two-tier contract + the trigger: a new `--fast` (or `--scoped`) mode that diffs
      HEAD/worktree, computes the changed file set, and runs only impacted work. Reuse the existing green-sentinel
      (unchanged→skip) as the degenerate case; this adds the "small change → impacted subset" case between "unchanged"
      and "full." **[CONFLICT-GUARD 2026-06-10 — operator-ratified]**: the fast tier must NEVER write
      .qg_last_passed_sha (that sentinel = "COMPLETE green run" and is what quickmerge ships on — a fast write silently
      dissolves the commit-quality boundary). Design REQUIRES: (a) its own .qg_fast_sentinel; (b) an explicit quickmerge
      policy decision for what a fast-sentinel permits (likely: nothing on the promote path; fast = inner-loop only);
      (c) the base scripts ALREADY hard-exclude QG_FAST from the full-sentinel write (defense-in-depth shipped
      2026-06-10) — the tier must set QG_FAST=1.
- [ ] [DESIGN] P0. Coverage-preservation design (THE hard part). Options to evaluate with Phase 0 data: (a)
      `pytest-testmon` to select only tests impacted by changed code; (b) maintain a coverage cache/DB so the fast tier
      reports combined (cached + delta) coverage; (c) fast tier runs impacted tests WITHOUT the coverage gate, and the
      coverage floor is enforced ONLY at the merge tier. **Invariant: the merge tier always recomputes full coverage**,
      so the floor can never silently drop regardless of which option we pick.
- [ ] [INFRA] P1. Test impact selection: wire pytest-testmon (or coverage-map equivalent) so the fast tier runs only
      tests that touch the changed files + their importers. Single-core; the win is fewer tests, not more cores.
- [ ] [INFRA] P1. basedpyright fast path: type-check changed files + their reverse-dependents only (full `SOURCE_DIR/`
      stays on the merge tier). Warm `BASEDPYRIGHT_CACHE_DIR` (already set) so incremental runs are cheap.
- [x] ✅ [INFRA] P1. **Codex STEP 5.x fast path — DONE (2026-06-11, operator's #2: "codex on changed files only").**
      `--fast` (env `QG_FAST=1`) restricts the ~60 codex grep checks to the source `.py` files CHANGED vs the
      merge-base, passed to `rg` as **INCLUDE-globs** via a `codex_rg` wrapper (`rg ${CODEX_SCOPE_GLOBS[@]+…} "$@"`).
      Include-globs PRESERVE each check's own exclude-globs (a changed `tests/` file is still dropped by its
      `--glob '!tests/**'`), so the only effect is "scan changed, not the whole tree" — a 2-file edit's codex pass goes
      O(tree)→O(changed). Mechanically: `CODEX_SCOPE_GLOBS` (empty in full mode) + 64 `rg`→`codex_rg` in
      base-service.sh's codex block (45 in base-library.sh) + a `--fast` flag, in BOTH bases. **VERIFIED**: (a)
      **full/merge tier BYTE-IDENTICAL** — old-vs-new codex STEP results identical on ibkr with `QG_FAST` unset (empty
      array → `codex_rg`≡`rg`, proven at shell level too); (b) **fast tier scopes + catches** — `QG_FAST=1` on ibkr
      scoped codex to its 1 changed file and caught that file's 2 real violations; (c) rg-glob mechanism proven
      (720-file scan → 1 file). The fast tier NEVER writes `.qg_last_passed_sha` (base scripts already enforce), so any
      fast miss is re-checked at the merge boundary. — unified-trading-pm@<sha>
- [ ] [TEST] P0. Differential correctness harness: for a corpus of known-bad commits (each violating one specific
      check/coverage), assert the fast tier catches anything WITHIN the changed files AND the full/merge tier catches
      everything. This is the proof that scoping never lets a regression through.

---

## Phase 3 — PER-STEP COST REDUCTION (helps single-core full gate too)

- [x] [INFRA] P1. ✅ pip-audit: it is advisory + has an 180s OSV network timeout. Move to cached OSV results and/or a
      periodic cron (e.g. on dependency change only) instead of every gate run. Big fixed-cost removal from the hot
      loop. — unified-trading-pm@779dc3683; same unit as the Phase-0 pip-audit item above (deps-hash trigger + 24h
      freshness bound, both bases in parity).
- [x] [INFRA] P2. ✅ bandit + actionlint: cache results keyed by content hash. — unified-trading-pm base-service.sh +
      base-library.sh + qg-common.sh helpers (unified-trading-pm@779dc3683). bandit key = content (`git ls-files -s`
      index blobs + `git diff` worktree delta + untracked contents) over SOURCE_DIR + pyproject.toml + bandit version +
      BANDIT_EXTRA_ARGS → `.qg_cache/bandit_content_hash`; actionlint key = workflow file names+contents (plain cat —
      `_WF_LINT_DIR` can resolve outside the repo pathspec in CI) + actionlint version + SHELLCHECK_OPTS →
      `.qg_cache/actionlint_content_hash`. Clean-run-only store; `QG_NO_CACHE=1` bypass; CI-safe (no `.qg_cache` in a
      fresh checkout → first run full). Measured (PM, isolation): bandit MISS 2.53s → HIT 0.13s; actionlint (55 wf) MISS
      3.99s → HIT 0.10s; content-bust verified for new/changed/removed files (mtime-independent, deterministic).
- [x] ✅ [INFRA] P0. **Codex-check hot spots — O(n²) re-scan + `.venv` walk-waste FIXED (2026-06-11, operator-flagged
      "the AST-walk issue").** Decomposing the codex span (the real #2 cost @ ~15% wall, and the #1 on big repos —
      execution-service codex 409s > tests 387s) found two offenders SEPARATE from the already-fixed STEP-5.65
      removed-symbols walk: (1) **`check_schema_provenance.py` was O(files × schemas)** — for every local schema it
      found it re-walked + re-read the WHOLE repo to test "is it imported from UAC/UIC" → **157s on execution-service
      alone**. Fixed: collect all UAC/UIC-imported names in ONE pass → O(1) membership. (2) **`.py` checks `rglob`'d the
      repo WITHOUT excluding `.venv`** — a plain `repo.rglob("*.py")` still ENUMERATES ~14k `.venv` files before
      discarding them per-path. Fixed in `check_schema_provenance` + `check_env_canon` +
      `check_manifest_import_alignment`: an `os.walk` that EXCLUDES
      `{.venv,.venv-workspace,venv,build,dist,node_modules,__pycache__,.git}` at the directory level (never descends
      in). **VERIFIED behavior-preserving** — old-vs-new violation output byte-identical across 5 repos
      (execution-service 178 / mtds 63 / deployment-api 92 / instruments 0 / uta 0). **Result: schema-provenance 157s →
      0.4s (~390×)** on execution-service; env_canon 10s + manifest 1.5s also drop. Runs in every service-repo codex
      block → fleet-wide. — unified-trading-pm@<sha>
  - [x] ✅ [INFRA] P2. **Sweep DONE (2026-06-11) — audited all 14 FS-walking checks in
        `scripts/{validation,quality_gates,cicd}/`; only 2 genuinely descended a `.venv`-bearing root.** Methodical grep
        (`rglob|glob|os.walk`) → 8 candidates → on inspecting each walk ROOT: `check-circular-imports` (argv
        `source_dir` = package dir, no .venv), `validate-strategy-manifest` (deep `engine/strategies`),
        `check-integration-dep-coverage` (`tests/{unit,integration}`), `check_cost_leakage` (bounded
        `app/(public)/**`,`marketing-static/**`,`codex/**` globs), `check-cursor-plan-format` (`plans/*.plan.md`),
        `check-workflow-bash-guards` (`.github/workflows/*.yml`), `check_plan_discipline`/ `detect_template_drift` (no
        broad walk) — **none enumerate `.venv`**; `audit-library-imports` + `check-import-patterns` **already** exclude
        it. The two real offenders **`rglob` over `WORKSPACE_ROOT`** (descending every repo's `.venv` +
        `.venv-workspace` + UI `node_modules`): `validate-cloudbuild.py` `find_cloudbuild_files` +
        `validate-buildspec.py` `find_buildspec_files` → converted to `os.walk` + `EXCLUDE_DIR_NAMES`. **VERIFIED
        byte-identical** found-file sets (cloudbuild 544 / buildspec 351, diff empty) with **cloudbuild 40.8s→8.0s
        (~5×)** + **buildspec 13.7s→4.9s (~2.8×)** — ~42 s off the PM gate. — unified-trading-pm@<sha>
- [ ] [INFRA] P2. bandit fast-tier scoping: scope bandit to changed files on the `--fast` tier (residual from the cache
      item above — depends on the Phase-2 fast-tier mechanism landing; the content-hash cache already covers the
      unchanged-tree case).
- [ ] [INFRA] P2. Coverage instrumentation is already off the `--quick` hot path; confirm the fast tier inherits that
      and measure the per-line-instrumentation cost the profile (Phase 0) attributes to `--cov`.
- [ ] [INFRA] P2. Re-profile after Phases 1–3 and re-baseline `qg_resource_baseline.json`; the 2× resource-drift guard
      keys off it.
- [x] ✅ [PERF] P1. **size-checks batching — DONE (2026-06-11): the hidden #2 non-test cost on big repos.** The
      size-checks phase spawned ONE `wc` + ONE `python -c` (AST parse) **PER source file** — O(files) process launches.
      On a large repo that's the dominant non-test/non-codex cost (NOT the gate startup I first suspected — see
      correction below). Fixed in BOTH bases: one `find` feeds a **single batched `python` pass per check** (file-size +
      function/class/method-size), find exclusions + thresholds + the AST visitor copied **verbatim**. **VERIFIED
      byte-identical** violation sets with order-independent diff on 5 repos + **huge speedups**: execution-service
      84.1s→1.3s (65×, 23 viol), features-service 94.2s→1.5s (63×, 18 viol), instruments-service 23.6s→0.5s (47×, 85
      viol), UAC/UTL via base-library (warn/fail test split preserved). Helps EVERY context (local/CI/SIT) since
      size-checks always runs full. — base-service.sh + base-library.sh @<sha>
- [x] ✅ [INFRA] P1. **"NON-codex overhead" finding CORRECTED (2026-06-11).** My first decomposition attributed ~122 s
      of an execution-service run to "gate STARTUP (`uv pip install -e`) + pip-audit network". Re-measuring against the
      Phase-0 profile + the size-checks decomposition above shows the real picture: (a) **size-checks was ~84 s** of
      that (per-file spawn — now ~1.3 s, fixed above); (b) **pip-audit's network hit was a COLD-CACHE artifact** — it
      has a 24 h deps-hash cache (`.qg_cache/pip_audit_deps_hash`), so steady-state local runs skip the OSV query; my
      fresh session just missed it; (c) there is **no separate large "startup" phase** — the editable-dep install is
      amortised by the venv being warm. **Remaining genuine non-test levers** (not artifacts): **typecheck
      cold-vs-warm** (the profile's 10.5% is WARM `BASEDPYRIGHT_CACHE_DIR`; a cold CI/SIT run is materially higher →
      cache persistence across CI runs is the lever, line ~the basedpyright item) and **pip-audit/basedpyright/bandit
      cache persistence in CI** (each CI container is cold → the local content-hash caches don't carry over; an
      `actions/cache` mount would close it — a CI-workflow change, separate surface). Provenance: 2026-06-11 size-checks
      decomposition.
- [x] ✅ [INFRA] P1. **pip-audit infra-error misclassification — FIXED in both bases (2026-06-11).** PM PR #258's
      `lint-codex` slice failed with `❌ pip-audit vulnerabilities found` whose real cause (one line up) was
      `could not parse pip-audit output: [Errno 2] No such file or directory: '/tmp/pip-audit-output.json'` — pip-audit
      exited non-zero on an OSV/network ERROR **without writing its `-o` json**, and the code bucketed the exit code as
      `0`=clean / `124`=timeout-advisory / **else=vulnerabilities-FOUND** → so a network blip fell into the vuln-FAIL
      branch and reddened a green PR (PM tolerance-0 → blocked auto-merge; the run passed on re-run, confirming it was
      an infra blip not a vuln). **Fix (option a): classify by WHAT pip-audit PRODUCED, not just the exit code** — only
      FAIL when the json EXISTS and parses to ≥1 dependency with `vulns`; a non-zero exit with no vuln report is now an
      **advisory `log_warn`** (same intent as the existing rc-124 timeout branch), not a gate fail. **Does NOT weaken
      security**: a genuine finding always writes the json and still fails (verified: vuln-json→FAIL,
      clean/missing/empty -json→advisory). Applied to `base-service.sh` (json `-o` path) + `base-library.sh` (main json
      path + the bare-PATH fallback via a `known vulnerabilit` signature). Option (b) — persist the deps-hash cache
      across cold CI containers via `actions/cache` — remains the complementary follow-up under the CI-cache item above.
      — base-service.sh + base-library.sh @<sha>

---

## Phase 4 — VALIDATION & BACKSTOP (no coverage drop, no missed violation)

- [ ] [TEST] P0. Coverage-floor invariant test: prove the MERGE tier still enforces each repo's real floor after the
      Phase-1 SSOT change (no repo silently dropped to pytest-cov default 0; no repo silently loosened).
- [ ] [TEST] P1. Run the Phase-2 differential harness in CI as a recurring guard so a future change to the fast tier
      can't regress its catch-rate.
- [ ] [INFRA] P1. Periodic FULL sweep (cron) across all repos as the backstop: even if the fast tier ever under-scopes,
      the sweep guarantees a full gate (incl. full coverage + full codex) runs within an SLA, so scoping can never let a
      regression persist undetected.

---

## Phase 5 — ROLLOUT & CODEX

- [ ] [INFRA] P1. Land base-service.sh / base-library.sh changes in PM (SSOT — no per-repo rollout needed; repos source
      it).
- [ ] [REFACTOR] P1. Per-repo stub slimming + toml reconciliation, repo-by-repo, each behind its own QG-green +
      quickmerge (do NOT mass-sweep — collision risk per Findings-Triage; ratchet, don't bulk-edit).
- [ ] [DOCS] P1. Codex SSOT updates: `codex/06-coding-standards/quality-gates.md` (two-tier model,
      `[tool.quality-gates]` table, "merge tier is authoritative" invariant, per-step cost notes). Add
      SUPERSEDED/extends banner cross-ref to the archived resource-contention plan.

---

## Open questions (resolve with Phase 0 data, not before)

- Coverage preservation mechanism: testmon vs coverage-cache vs floor-only-at-merge — pick after measuring testmon
  overhead and how often the merge tier runs anyway.
- Is pip-audit's network cost big enough to justify the cron move, or is caching sufficient?
- For the 7 drifting repos: which honest value per repo (keep-green-now vs raise-to-target-and-fix-tests)? MTDS is the
  template case (28 now → 71 as ISS-031 lands).
- `[tool.quality-gates]` table vs keeping a few genuinely-bash-only knobs in the stub — where exactly is the line?

## Codex SSOT updates (required)

- `codex/06-coding-standards/quality-gates.md` — config-SSOT rule, two-tier gate, `[tool.quality-gates]` contract,
  per-step cost guidance.

## Success criteria

- Single-core wall-time for a small (≤2 file) change drops to seconds via the fast tier, on a single core, no
  parallelism.
- Every QG setting has exactly ONE home (toml); the dual-SSOT matrix shows zero `drift`/`shadowed` rows.
- Differential harness proves: fast tier catches in-scope violations; merge tier catches everything; no coverage floor
  silently changed.

## UI build warm-cache (filed 2026-06-10, slot-3 — cold-clone build tripped the 90s gate; warm = 365 ms)

Operator direction: if fundamental deps don't change, the build cache should be warm ALWAYS — only our code rebuilds.

- [ ] [CODE] P2. `tsc` incremental for UI repos: `"incremental": true` + gitignored `.tsbuildinfo` (deployment-ui +
      unified-trading-system-ui tsconfigs) — only changed files re-check; cold cost limited to a fresh clone's first
      build. Repo: deployment-ui, unified-trading-system-ui.
- [ ] [CODE] P2. Pre-warm in `setup.sh`: run one `npm run build` at clone-setup time so the QG gate never pays the
      cold-cache cost (the cold build moves to where there is no timeout). Repo: unified-trading-pm
      (`scripts/quality-gates-base` setup template) + the two UI repos.
- [ ] [INFRA] P3. Evaluate pnpm global content-addressable store for UI repos: hardlinked node_modules → identical
      inodes across ALL slot clones → OS page cache warm fleet-wide while deps are unchanged (npm copies per-clone: N×
      disk + N× cold reads). Decision item — changes lockfile format + CI install steps.
- [ ] [SCRIPT] P3. base-ui.sh: one automatic retry on the build-timeout class (cold-trip passes on retry; a genuine hang
      fails twice) — removes the human re-run without weakening the budget.
- [ ] [SCRIPT] P2. `restart-deployment-stack.sh` must export `GCP_PROJECT_ID`/`PROJECT_ID` (env-inline launcher sets
      provider but no project → Secret-Manager paths malformed → live 500 on any secret-reading route; found shipping
      the Repos-CI dashboard 2026-06-10; interim: operator exports inline).
