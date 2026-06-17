---
type: analysis
title: QG config dual-SSOT matrix — TIER-A vs TIER-B knob classification + bandit -c verdict
epic: infrastructure_master
auditor: slot-1 (claude)
date: "2026-06-10"
status: complete
source:
  - plans/archive/2026_06/quality_gates_speed_and_config_ssot_2026_06_09.md — Phase 0 audit items (dual-SSOT matrix,
    bandit-`-c` question, TIER-A/TIER-B classification)
  - static analysis of scripts/quality-gates-base/base-service.sh + base-library.sh (PM @ working tree 2026-06-10)
  - per-repo sweep of <repo>/scripts/quality-gates.sh stubs vs <repo>/pyproject.toml across the .tabs/1 workspace
---

# QG config dual-SSOT matrix (Phase 0 — drives Phase 1 mechanism)

> **Headline**: **13 TIER-A knobs** (a native `[tool.*]` toml home exists; today the bash flag SHADOWS it or the toml is
> DEAD) and **27 TIER-B knobs** (bash-orchestration only; no native toml home → the planned `[tool.quality-gates]`
> table). **Bandit verdict: `[tool.bandit]` is DEAD config fleet-wide** — the bases run bandit WITHOUT `-c`, and bandit
> does NOT auto-discover pyproject (verified concretely below). **5 repos carry a live coverage stub-vs-toml numeric
> drift** (alerting 76/78 · mdps 70/77 · mtds 28/71 · SIT 2/0 · uta 77/70).

## Method

Static enumeration of every tool invocation + caller-settable variable in `base-service.sh` and `base-library.sh` (ruff
/ pytest / coverage / basedpyright / bandit / pip-audit / vulture / actionlint + stub vars), cross-checked against what
each tool can natively express in `pyproject.toml`. Per-repo values swept with grep across all 22+ workspace repos
(`MIN_COVERAGE=` in the stub vs `[tool.coverage.report] fail_under` in toml; `[tool.bandit]` presence). Bandit behaviour
verified empirically (not from docs).

## Bandit `-c` verdict (plan P1 question — answered definitively)

Test: temp project with `[tool.bandit] skips = ["B602"]` in pyproject.toml + a `shell=True` call (B602, HIGH). bandit
**1.9.4** (the fleet version), Python 3.13:

| Invocation                                              | Result                                              |
| ------------------------------------------------------- | --------------------------------------------------- |
| `bandit -r src/ -ll` (today's base invocation, no `-c`) | **B602 REPORTED, exit 1** — toml NOT read           |
| `bandit -c pyproject.toml -r src/ -ll`                  | **B602 skipped, exit 0** — `[tool.bandit]` honoured |

- **Verdict: shadowed-by-absence.** The per-repo `[tool.bandit]` sections (present in ~20 repos, e.g. MTDS
  `skips = ["B608","B104","B108","B310"]`) are **DEAD** under the current base invocation.
- No `toml` extra needed: bandit 1.9.4 on Python 3.13 parses pyproject via stdlib `tomllib` when passed
  `-c pyproject.toml`.
- Irony note: base-service's bandit **cache key already hashes pyproject.toml content** — so editing the dead
  `[tool.bandit]` busts the cache for a run that then ignores it.
- Migration: add `-c pyproject.toml` to both bases — **safe unconditionally** (verified: a pyproject WITHOUT a
  `[tool.bandit]` section still scans normally, B602 reported, exit 1 — no config error). The `-ll` severity threshold
  has no toml key → stays CLI (or `[tool.quality-gates]`).

## Per-repo coverage drift sweep (stub `MIN_COVERAGE` vs toml `fail_under`)

`--cov-fail-under=$MIN_COVERAGE` always SHADOWS `[tool.coverage.report] fail_under`, so "stub" is the effective value.

| Repo                                                                                                                                                                                           | stub | toml | Verdict                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ---- | ---------------------------------------------------------------------------------- |
| alerting-service                                                                                                                                                                               | 76   | 78   | **drift** (toml stricter, shadowed)                                                |
| market-data-processing-service                                                                                                                                                                 | 70   | 77   | **drift** (toml stricter, shadowed)                                                |
| market-tick-data-service                                                                                                                                                                       | 28   | 71   | **drift** (the template case, plan §28-vs-71)                                      |
| system-integration-tests                                                                                                                                                                       | 2    | 0    | **drift** (stub stricter)                                                          |
| unified-trading-api                                                                                                                                                                            | 77   | 70   | **drift** (stub stricter — a flip-to-toml without reconciliation SILENTLY LOOSENS) |
| batch-live-reconciliation-service                                                                                                                                                              | 80   | 80   | agree                                                                              |
| ibkr-gateway-infra                                                                                                                                                                             | 51   | 51   | agree                                                                              |
| instruments-service                                                                                                                                                                            | 77   | 77   | agree                                                                              |
| strategy-service                                                                                                                                                                               | 74   | 74   | agree                                                                              |
| unified-api-contracts                                                                                                                                                                          | 83   | 83   | agree                                                                              |
| unified-trading-library                                                                                                                                                                        | 80   | 80   | agree                                                                              |
| alerting/client-reporting-api · deployment-api · deployment-service · execution-service · features-service · fund-administration-service · greeks-service · ml-service · trading-agent-service | 70   | 70   | agree (floor)                                                                      |
| e2e-testing · unified-trading-pm                                                                                                                                                               | 0    | 0    | agree (non-coverage repos)                                                         |
| agent-orchestrator                                                                                                                                                                             | n/a  | 70   | n/a — custom gate, does NOT source base-service.sh                                 |
| deployment-ui · unified-trading-system-ui                                                                                                                                                      | n/a  | n/a  | n/a — UI repos (base-ui.sh, no Python coverage)                                    |

**5 numeric drifts confirmed** (the plan's "7 of 22" likely counted the two n/a rows). Phase-1 rule: reconcile each
drifting repo to ONE honest value BEFORE dropping the flag — flipping to toml as-is reds alerting/mdps/mtds and silently
loosens uta/SIT.

## TIER-A — tool-native toml home exists (toml is the home; base must stop shadowing)

| Knob                        | Current source (flag/env)                                   | Toml-native home                                     | Verdict                        | Migration note                                                                                                                                                      |
| --------------------------- | ----------------------------------------------------------- | ---------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage floor              | `--cov-fail-under=$MIN_COVERAGE` (stub var)                 | `[tool.coverage.report] fail_under`                  | **shadowed** (5 drift)         | Drop flag after per-repo reconciliation; `MIN_COVERAGE` derives from toml (Phase 1)                                                                                 |
| Coverage source             | `--cov=$SOURCE_DIR`                                         | `[tool.coverage.run] source`                         | shadowed (agree)               | Drop flag; toml `source` already set fleet-wide                                                                                                                     |
| Coverage report output      | `--cov-report=xml:coverage.xml`                             | `[tool.coverage.xml] output` / report config         | shadowed (agree)               | Drop flag or keep (CI parsers expect coverage.xml — verify before drop)                                                                                             |
| Coverage branch/omit        | (not passed — toml already authoritative)                   | `[tool.coverage.run] branch/omit`                    | agree                          | Already single-home; the "exclude market_interface" intent dupes live here                                                                                          |
| pytest test paths           | positional `${PYTEST_UNIT_DIR} [tests/integration/]`        | `[tool.pytest.ini_options] testpaths`                | **shadowed**                   | Positional args override toml `testpaths` (MTDS toml says `tests`, base runs `tests/unit/`); unify via testpaths + markers OR keep orchestration + delete dead toml |
| pytest per-test timeout     | `--timeout=${PYTEST_TIMEOUT:-60}`                           | `[tool.pytest.ini_options] timeout` (pytest-timeout) | shadowed-by-absence            | Move 60 to toml; PYTEST_TIMEOUT env stays as emergency override                                                                                                     |
| pytest output opts          | `-q -r a --tb=short --no-header`                            | `[tool.pytest.ini_options] addopts`                  | **shadowed/merged**            | CLI appended after addopts (`-q` beats repos' `addopts="-v"`); pick one home                                                                                        |
| pytest-socket allowlist     | `--allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket` | `addopts`                                            | shadowed-by-absence            | Policy-uniform — fine to keep CLI, but then delete any toml dupes                                                                                                   |
| bandit skips/tests/excludes | NOT passed — `[tool.bandit]` exists in ~20 repos            | `[tool.bandit]` via `-c pyproject.toml`              | **DEAD** (shadowed-by-absence) | Add `-c pyproject.toml` to both bases (see verdict above); audit each repo's skips first — they re-activate                                                         |
| bandit target               | `-r "$SOURCE_DIR/"`                                         | `[tool.bandit] targets`                              | shadowed (agree)               | Keep CLI (target = orchestration) or move; low value either way                                                                                                     |
| basedpyright target         | positional `"$SOURCE_DIR/"`                                 | `[tool.basedpyright] include`                        | shadowed (agree)               | Toml include/exclude already authoritative for config; CLI path narrows scope only                                                                                  |
| ruff rule config            | (none passed — rules read from toml)                        | `[tool.ruff]`                                        | agree                          | Already single-home (the model TIER-A end-state)                                                                                                                    |
| vulture min-confidence      | `--min-confidence 80` (base-library [5.6])                  | `[tool.vulture] min_confidence`                      | shadowed-by-absence            | vulture auto-reads `[tool.vulture]`; CLI flag would override a repo's toml value                                                                                    |

## TIER-B — bash-orchestration only (no native toml home → `[tool.quality-gates]` candidates)

| Knob                                                                                                                                                                                      | Current source            | Proposed `[tool.quality-gates]` key / note                                                                                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MIN_COVERAGE`                                                                                                                                                                            | stub var                  | DELETE — becomes a derived read of TIER-A `fail_under` (Phase 1)                                                                                                     |
| `PYTEST_WORKERS` / xdist `-n` (CI auto vs local 1)                                                                                                                                        | env + stub                | `pytest_workers` (host-dependent — keep env override)                                                                                                                |
| `PYTEST_UNIT_DIR` (per-family layouts)                                                                                                                                                    | stub var (pre-source)     | `pytest_unit_dir`                                                                                                                                                    |
| `RUN_INTEGRATION`                                                                                                                                                                         | stub var (service)        | `run_integration`                                                                                                                                                    |
| `MAX_DURATION` / `IGNORE_TIMEOUT`                                                                                                                                                         | stub var / env+flag       | `max_duration`; IGNORE_TIMEOUT stays env (session escape hatch)                                                                                                      |
| `PYRIGHT_TIMEOUT` (120) + per-step `run_timeout`s (ruff 30, bandit 30, pip-audit 180, vulture 60)                                                                                         | env / hardcoded           | `step_timeouts` sub-table (or leave hardcoded — measure first)                                                                                                       |
| `CODEX_MAX_VIOLATIONS`                                                                                                                                                                    | stub var                  | `codex_max_violations` (ratchet → 0)                                                                                                                                 |
| Codex exclude arrays: `OS_ENVIRON_` / `INSIDE_` / `RAW_JSON_` / `EMPTY_FALLBACK_` / `BROAD_EXCEPT_` / `DEEP_IMPORT_EXTRA_EXCLUDES`, `GCP_PROJECT_ID_EXCLUDE_GLOBS`, `SIZE_EXTRA_EXCLUDES` | stub arrays (8 knobs)     | `exclude_globs` sub-table — THE "exclude intent in ~7 places" collapse target                                                                                        |
| Size limits: `MAX_FILE_LINES` (900, hardcoded) / `MAX_FUNCTION_LINES` / `MAX_CLASS_LINES` / `MAX_METHOD_LINES`                                                                            | hardcoded + env (4 knobs) | workspace-constant — arguably NOT per-repo config; leave in base                                                                                                     |
| `PIP_AUDIT_EXTRA_ARGS` + 4 sanctioned `--ignore-vuln` CVEs                                                                                                                                | env + hardcoded in base   | pip-audit has NO pyproject support at all → inherently TIER-B; `pip_audit_ignores`                                                                                   |
| `BANDIT_EXTRA_ARGS` (base-service only; base-library lacks it)                                                                                                                            | env                       | dies when TIER-A `-c` lands (skips move to `[tool.bandit]`)                                                                                                          |
| `QG_THREAD_CAP` / `QG_MEM_CAP` / `QG_GOVERNOR_DISABLE` / `QG_SENTINEL_DISABLE` / `QG_PIP_AUDIT_MAX_AGE_HOURS` / `QG_SLICE` / `QG_PROFILE`                                                 | env (7 knobs)             | host/session-scoped, NOT repo config — stay env (document, don't migrate)                                                                                            |
| Feature toggles: `ENFORCE_NO_TYPE_IGNORE` / `SKIP_IMPORT_PATTERNS` / `UAC_CANONICAL_EXEMPT` / `REPO_ARCH_TIER`                                                                            | stub vars (4 knobs)       | `[tool.quality-gates]` booleans/strings                                                                                                                              |
| Identity/wiring: `SERVICE_NAME`·`PACKAGE_NAME` / `SOURCE_DIR` / `LOCAL_DEPS` / `EXPECTED_BASE_VERSION`                                                                                    | stub vars (4 knobs)       | `SOURCE_DIR` duplicates `[project.name]`+coverage source+bandit target+basedpyright include — derive from toml in Phase 1; LOCAL_DEPS duplicates `[tool.uv.sources]` |
| vulture fail/warn thresholds (100/20)                                                                                                                                                     | hardcoded (base-library)  | workspace-constant — leave in base                                                                                                                                   |

Count basis: TIER-A = 13 table rows above; TIER-B = 27 individual knobs (expanding the grouped rows: 8 exclude arrays, 4
size limits, 7 QG\_\* env, 4 toggles, 4 identity + the 10 singles, minus the env-stay rows still counted as knobs).

## Base-service vs base-library deltas found during enumeration (feed Phase 1/3)

- base-library pip-audit + bandit had **NO content-hash caching** (base-service caches both, 24 h max-age for
  pip-audit). _Update same-day 2026-06-10: the pip-audit deps-hash cache + bandit content-hash cache were ported to
  base-library by the parallel Phase-3 caching change (same working tree, pending commit) — delta closed._
- base-library lacked `IGNORE_TIMEOUT` honour on the duration meta-gate (fixed with the profiler instrumentation,
  2026-06-10) and lacks `BANDIT_EXTRA_ARGS` / `PYTEST_TIMEOUT` overrides.
- base-library pip-audit runs bare `pip_audit` (no `--skip-editable`, no JSON parse) vs base-service's richer path.

## Per-repo `[tool.bandit] skips` audit (2026-06-17) — `-c pyproject.toml` flip is SAFE

> Closes the Phase-0 P1 precondition: "audit each repo's skips BEFORE the bases add `-c pyproject.toml`, else
> re-activating dead skips may silently suppress a real finding." Verdict: **safe to flip** — no scanned-tree finding is
> suppressed by any existing skip.

**Method**: `tomllib`-parse every repo's `pyproject.toml` `[tool.bandit]`; for each repo with non-empty `skips`, run the
repo's own `.venv/bin/bandit` `-t <codes>` over its `SOURCE_DIR` (the exact tree the base scans —
`bandit -r "$SOURCE_DIR/" -ll`).

**Findings**:

- **20 of 22 repos** have `[tool.bandit] = {skips: []}` — empty → adding `-c pyproject.toml` is a **no-op** for them.
- **2 repos carry real skips**, both **MOOT in the scanned tree** (0 findings for the skipped codes within
  `SOURCE_DIR`): | Repo | skips | findings in `SOURCE_DIR` | findings in `scripts/` (NOT scanned) | | --- | --- | --- |
  --- | | market-tick-data-service | B608,B104,B108,B310 | **0** (all 4 moot) | 4×B310 + 1×B108 (one-off scripts) | |
  strategy-service | B608 | **0** (moot) | — |

**Why moot today**: (a) the base runs bandit WITHOUT `-c`, so the toml skips are not honored at all; (b) the base scans
only `SOURCE_DIR`, and neither repo has any of its skipped codes there (the mtds hits are all under `scripts/`, outside
the scan root).

**Verdict / decision**: **adding `-c pyproject.toml` is SAFE** — it changes nothing in any repo's scanned tree (the two
skip-sets suppress zero real findings). The flip is de-risked; no repo reds, nothing real is hidden. The 2 skip-sets may
be **pruned for cleanliness** (they suppress nothing) but pruning is optional, not a blocker. (Verified earlier in this
doc that bandit tolerates `-c pyproject.toml` even with no `[tool.bandit]` section.)

**Side-finding (captured as a todo, not part of this flip)**: mtds `scripts/massive_flat_files_smoke.py:56` uses a
hardcoded `/tmp` (B108) — outside bandit's scan path but violates the workspace no-hardcoded-`/tmp` HARD RULE
(`tempfile.gettempdir()`); plus 4 `urllib.urlopen` (B310) in mtds `scripts/`. Tracked in the speed/config plan.

## Phase-1 implications (decision input, not decisions)

1. TIER-A rule confirmed viable: every TIER-A knob has a working toml home **today** — but 5 repos need coverage
   reconciliation FIRST, and `[tool.bandit]` re-activation needs a per-repo skips audit (dead config may hide
   stale/wrong skips).
2. `[tool.quality-gates]` schema should cover: `min_coverage` (transitional), `run_integration`, `pytest_workers`,
   `pytest_unit_dir`, `max_duration`, `codex_max_violations`, `exclude_globs.*`, `pip_audit_ignores`. Host/session env
   (`QG_*`) and workspace constants (size limits) stay OUT of toml.
3. `SOURCE_DIR` is the deepest duplication (stub + coverage source + bandit target + basedpyright include + ruff target)
   — deriving it from toml collapses 5 declarations to 1.
