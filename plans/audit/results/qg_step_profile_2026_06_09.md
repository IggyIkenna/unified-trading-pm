---
type: benchmark
title: QG per-phase wall+RAM profile — fleet sweep results + scopability classification
epic: infrastructure_master
auditor: slot (interactive)
date: "2026-06-11"
status: complete
parent_plan: plans/active/quality_gates_speed_and_config_ssot_2026_06_09.md
source:
  - profile_qg_resources.py --all --parallel (host-adaptive pinned sweep, 2026-06-11)
  - raw per-repo JSON/txt/markers in the gitignored .qg_profile/ (not committed — large intermediates)
---

# QG per-phase profile — fleet sweep (2026-06-11)

Phase-0 deliverable for `quality_gates_speed_and_config_ssot_2026_06_09.md`. Answers: **where does the single-core QG
wall-time actually go**, and **which phases can be scoped to changed files** (the fast-tier design).

## Method

- `profile_qg_resources.py --all --parallel` on a 24-core / ~48 GB host: each repo pinned to its own core (`taskset`),
  single-core caps (`QG_THREAD_CAP=1`, `PYTEST_WORKERS=1`), `QG_PROFILE=1` (sentinel disabled → every phase runs;
  `FIX_MODE=false` → no auto-fix, no tree dirt). RAM = process-tree RSS sampled ~5 Hz, bucketed into spans by the
  `qg_prof` markers the bases emit.
- **25 repos swept; 19 produced a COMPLETE run** (reached tests + typecheck). 6 `⚠PARTIAL` excluded from phase timing:
  the 2 UI repos (different gate), `agent-orchestrator`, and 3 with incomplete `.venv`s that early-bail at TESTS on a
  missing `pytest-timeout` (tracked as a P1 venv-repair item in the parent plan).
- **Total serial-equivalent wall = ~6,145 s** (~102 min if run one-repo-at-a-time).

## Fleet-wide: where the wall-time goes (instrumented spans, summed across repos)

| Phase                    | % of total wall | total_s | avg/repo | max peak RAM | notes                                              |
| ------------------------ | --------------- | ------- | -------- | ------------ | -------------------------------------------------- |
| **tests** (pytest)       | **59.5%**       | 3264    | 172 s    | **5.5 GB**   | dominates wall AND RAM (5.5 GB = UTL)              |
| **codex** (grep/AST)     | **21.7%**       | 1192    | 66 s     | 259 MB       | ~60 compliance checks; cost scales with tree size  |
| typecheck (basedpyright) | 10.5%           | 577     | 30 s     | 8 MB         | WARM cache — cold is higher (see caveat)           |
| pip-audit                | 3.5%            | 190     | 10 s     | 96 MB        | OSV network; already deps-hash-cached on real runs |
| size-checks              | 3.2%            | 178     | 9 s      | 23 MB        | per-file file-size limits                          |
| bandit                   | 0.5%            | 28      | 1.5 s    | 59 MB        | content-hash cached                                |
| removed-symbols          | 0.4%            | 21      | 3 s      | 35 MB        | cross-repo whole-tree (cron-able)                  |
| lint (ruff)              | 0.0%            | 0.7     | —        | 4 MB         | already negligible                                 |

**Hypothesis check (plan §Phase-0):**

- ✅ "pytest dominates wall-time" — yes, 59.5%, and RAM too (5.5 GB peak).
- 🔶 "pytest + basedpyright are the top two" — REFUTED on #2: **codex (21.7%) is the real #2, ~2× typecheck (10.5%)**.
- ✅ "pip-audit OSV network is a fixed tax" — yes but small (3.5%) and already cached off the hot path.
- 🔶 "basedpyright dominates RAM" — NO; typecheck RAM is tiny (warm cache). pytest owns RAM.

> **Caveat — typecheck is WARM-cache** (`BASEDPYRIGHT_CACHE_DIR` persisted). A cold run is materially higher; the parent
> plan's P1 cold-vs-warm item still applies. Even cold, tests remain #1.

## Per-repo: the bottleneck is not uniform (full runs, slowest first)

| repo                    | total_s | tests   | codex   | typecheck |
| ----------------------- | ------- | ------- | ------- | --------- |
| execution-service       | 958     | 387     | **409** | 68        |
| features-service        | 805     | **573** | 50      | 73        |
| unified-trading-library | 668     | **323** | 0       | 63        |
| unified-api-contracts   | 509     | **315** | 54      | 51        |
| deployment-api          | 487     | 168     | **245** | 43        |
| ml-service              | 337     | **199** | 98      | 35        |
| unified-trading-api     | 288     | **236** | 17      | 14        |
| instruments-service     | 286     | **166** | 22      | 27        |
| market-data-processing  | 213     | **145** | 42      | 20        |

**Two bottleneck classes:**

1. **tests — universal #1** for almost every repo.
2. **codex — spikes on LARGE repos and overtakes tests** (`execution-service` 409 > 387; `deployment-api` 245 > 168).
   The ~60 grep/AST checks scan the whole tree, so cost scales with file count, not change size.

Both are exactly what a 2-line change does NOT need to re-run in full.

## Scopability classification → the fast-tier design (Phase 2)

For each phase: can the FAST/iterative tier scope it to the changed file set (merge tier always runs full)?

| Phase           | %wall | Class                     | Fast-tier action                                                        |
| --------------- | ----- | ------------------------- | ----------------------------------------------------------------------- |
| tests           | 59.5% | **SCOPABLE** (impact-sel) | run only tests that import the changed files (pytest-testmon / cov-map) |
| codex           | 21.7% | **SCOPABLE** (per-file)   | run the per-file grep/AST checks over changed files only                |
| typecheck       | 10.5% | **SCOPABLE** (+rev-deps)  | basedpyright on changed files + their importers; warm cache             |
| size-checks     | 3.2%  | **SCOPABLE** (per-file)   | changed files only                                                      |
| pip-audit       | 3.5%  | FIXED-COST-CACHEABLE      | skip when deps unchanged (already deps-hash gated)                      |
| bandit          | 0.5%  | SCOPABLE / cached         | changed files / content-hash cache                                      |
| removed-symbols | 0.4%  | **NON-OPTIONAL-FULL**     | cross-repo whole-tree → stays on cron/merge tier                        |
| lint (ruff)     | 0.0%  | already fast              | full (negligible)                                                       |

**Conclusion:** scoping **tests + codex + typecheck** (91.7% of wall-time, all SCOPABLE) to the changed-file set turns a
small change from minutes into seconds — and specifically kills the two real bottlenecks (tests everywhere, codex on big
repos). The merge boundary (quickmerge Pass-1 / CI `quality-gates-v2`) always runs the FULL gate with FULL coverage, so
scoping never weakens the gate — it only shortens the iterate loop.

**Hard part to design next (Phase 2):** coverage preservation under scoped tests — `pytest-testmon` vs a coverage-cache
vs floor-only-at-merge (evaluate with this data). The differential-correctness harness (known-bad commits) is the proof
that scoping never lets a regression through.
