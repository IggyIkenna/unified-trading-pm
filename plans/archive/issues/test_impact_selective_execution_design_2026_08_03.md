---
doc_type: issue
title: Test-impact / selective test execution — design (P2/P3 extracted from the CI-cost followups plan)
summary: >-
  Extracted the P3 "this is the actual path to 50%" framing note and the P2 "scope a design (design only, no
  implementation)" todo out of github_actions_operator_gated_followups_2026_07_17.md into their own doc, then completed
  the design itself: a conservative, escape-hatch-heavy mapping from changed files to affected pytest files, grounded in
  real codebase facts (dynamic-dispatch adapter registries, per-family conftest.py trees, manifest-driven tests) rather
  than generic import-graph advice. Verdict: static reachability alone is NOT safe in this codebase — real
  dynamic-import and fixture-inheritance patterns exist that would silently under-test. The design compensates with
  explicit, enumerable fallback triggers and a mandatory shadow-mode trial before the selector is ever allowed to skip a
  real CI run. Design only — no implementation shipped here, per the parent todo's own explicit gate.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, testing, pytest, selective-execution, test-impact-analysis, cost, design]
related:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md,
  ]
created: 2026-08-03
priority: P2
parent_epic: deployment_and_user_management_master
source:
  "Interactive session, operator asked whether test-impact/selective execution had ever been implemented (it hadn't —
  still an unchecked P2 'scope a design' todo, operator-approved 2026-07-28), then asked to extract the two related
  todos into their own doc and complete the design work under /autonomous."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
  "Operator, 2026-08-03 (interactive session) — reviewed and approved the safety model directly ('im fine with the
  design unblock Phase 2'); implementation staged as sequential todos in
  test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md Phase 2."
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-03** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by a `cicd` escalation (agt-5c37f6) triaging the `check_archive_candidates` /
> `check_terminal_status_archived` hard gate failures. No content was rewritten.

# Test-impact / selective test execution — design

## Why this matters (extracted verbatim from `github_actions_operator_gated_followups_2026_07_17.md`, P3 framing note)

> **This is the actual path to 50%, not Phase 7** (Phase 7's self-hosted-runner fan-out nets ~3-6% of the fleet total on
> its own). `quality-gates-v2`'s real test/lint job is ~90%+ of a service repo's billed minutes and scales with
> commit/PR volume, which rises with agent parallelism. **Per-run duration** — test-impact/selective execution (skip
> tests the diff can't affect) cuts the ~9min `QG slice (tests)` leg directly but carries real risk of silently
> under-testing; do not attempt without a design that a missed regression is structurally impossible, not just unlikely.
> Do not reach for this before Phase 7's smaller, structurally-safe win is measured and confirmed.

Self-hosting (Phase 7, and the concurrency fix in the companion issue doc) only changes **who pays** — GitHub-billed
minutes go to $0, but the actual wall-clock compute, the ~9min pytest leg's contention footprint on a shared host, and
local `quality-gates.sh` runtime for every engineer are untouched. Selective execution is the only lever that cuts the
**work itself**.

## Original todo (extracted verbatim, P2, operator-approved 2026-07-28)

> Scope a design (design only, no implementation) for test-impact/selective test execution. The design doc must specify,
> before any code is written: (1) the safety guarantee — what makes a missed regression structurally impossible rather
> than merely unlikely; (2) the change→affected-tests mapping mechanism (e.g. import-graph reachability from changed
> files) and its known blind spots (dynamic imports, fixture-level coupling, config/data-driven tests); (3) the fallback
> rule — any ambiguity in the mapping must fall back to running the full suite, never a partial one; (4) how the design
> is itself tested (a false-negative in the selection logic is a silent coverage hole, so the selector needs its own
> regression tests). Blocked on nothing else — Phase 7's fan-out does not need to complete first, but implementation
> should not start until this design is reviewed. Do not implement from this todo directly; a follow-up todo authorizing
> implementation should cite this design once it exists.

---

## The design

### Grounding facts (investigated live in this codebase, not assumed)

1. **No reusable import graph exists today**, but the building block does. `detect_breaking_change.py` only diffs
   changed files' own public surface — it never builds a whole-repo graph. `check_removed_symbols.py` (QG STEP 5.66)
   DOES `ast.walk()` every `.py` file workspace-wide via `iter_python_files()` and matches
   `ImportFrom`/`Import`/`Attribute` nodes — currently against a removed-symbols manifest, but the same walk generalizes
   directly to "record every import edge" → a `file → imported-modules` graph, then invert it to
   `changed-file → files-that-import-it (transitively)`.
2. **Fixture coupling is real and structural, not a theoretical risk.** Larger repos have 9-12 `conftest.py` files, one
   per test family (`strategy-service`: 12, `features-service`: 10, `execution-service`: 9, `unified-trading-library`:
   9). pytest resolves fixtures by **directory ancestry**, not by import statements — a change to a family-level
   `conftest.py` affects every test under it regardless of what any individual test file imports. An import-graph-only
   mapper is blind to this by construction.
3. **`pytest-xdist` is in universal use** (`base-service.sh` hard-requires it; CI runs `-n auto`) and imposes no
   conflict — `pytest <scoped paths>` still partitions cleanly across workers. The existing `{tests, checks}` CI matrix
   (`check_qg_slice_completeness.py`, 3 base selectors × 4 phase flags) is an orthogonal, parallel-leg partition of the
   WHOLE suite — selective execution is a new axis **inside** the `tests` leg, not a competing or colliding mechanism.
4. **Config/data-driven tests exist and have zero import edge to what they really test.**
   `unified-trading-pm/tests/unit/test_validate_strategy_manifest.py` loads its target script via
   `importlib.util.spec_from_file_location` (dynamic, not a static import) and asserts against `strategy-manifest.json`
   content; `test_workspace_manifest_tags.py` reads `workspace-manifest.json` directly. A change to either JSON file has
   **no traceable static edge** to the tests that would catch a regression in it.
5. **Dynamic-dispatch adapter/family registries are real, load-bearing, and untraceable to static AST reachability by
   construction** — this is the finding that rules out a naive "just walk imports" design.
   `features-service/features_service/api/main.py:64` resolves per-family modules via
   `importlib.import_module(f"features_service.{family}.api.main")` in a loop over `_FAMILY_NAMES`.
   `execution-service/execution_service/trade_execution/__init__.py:252-258` resolves adapter classes (`CMEAdapter`,
   `FXAdapter`, `IbkrTradFiAdapter`, …) via a module-level `__getattr__` that does
   `importlib.import_module(module_path)` from a `_TRADFI_ADAPTER_MAP` dict — **no `import` statement anywhere names the
   target module**. A static import-graph walk cannot see this edge at all; a change to `cme_adapter.py` would map to
   **zero** dependent test files under naive reachability, when in reality the whole `trade_execution` test surface
   depends on it.

### (1) The safety guarantee

**The guarantee is not "the mapper is usually right" — it is "the mapper only ever narrows inside a provably-closed
zone, and every case it cannot prove closed is an automatic full-suite run."** Concretely: the selector computes a
**conservative superset**, never a best-guess subset. Static reachability is used strictly as a way to say "this diff
cannot possibly need tests outside set S" for a bounded, enumerable set of safe conditions — never as a way to say "this
diff only needs tests in set S" by default. Every one of the 5 grounding facts above becomes an explicit, checked escape
hatch (below) that forces S = "everything," not a corner case handled by hope.

The second half of the guarantee, per requirement (4), is that this claim is not trusted on paper — see the shadow-mode
validation gate below, which is the actual proof mechanism, not the static analysis alone.

### (2) The mapping mechanism and its blind spots

**Base mechanism**: extend `check_removed_symbols.py`'s existing `ast.walk()`-over-`Import`/`ImportFrom` pattern into a
workspace-wide `file → {imported files}` edge table (built once per run, cached, invalidated on tree-hash change —
reusing the same content-sentinel cache-key pattern `content-gate` already uses for the whole-tree QG skip, so this is
additive infra, not new infra). Invert it to `file → {files that import it, transitively}`. For a given diff's changed
files, the selector's initial candidate test set = the transitive closure of "test files that import (directly or
transitively) any changed source file" — reusing the SAME AST-walk the QG codebase already runs today.

**Blind spots, each with its own mandatory escape hatch (this list IS the design, not an appendix)**:

| Blind spot                                                                                     | Real evidence found                                                                                                                                                         | Escape hatch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Dynamic imports (`importlib.import_module`, `__getattr__`-based lazy resolution, `__import__`) | `features-service`, `execution-service`, `unified_trading_library/cloud_interface/factory.py`, `agent-orchestrator/server/routes/ops.py` — all real, all currently shipping | A changed file that itself CONTAINS a dynamic-import call, OR that is a plausible dynamic-import TARGET (heuristically: any module under a directory whose sibling files are dynamically dispatched, e.g. `trade_execution/*_adapter.py`), maps to "cannot determine" → run the full package's tests, not just direct importers. A one-time, hand-maintained allowlist of known dynamic-dispatch directories (adapter maps, family registries) seeds this — new dynamic-dispatch patterns must be added to the allowlist as a PR-review requirement, enforced by a QG check analogous to `check_removed_symbols.py` (grep for `importlib.import_module`/`__getattr__`/`__import__` outside the allowlist → fail closed, force full-suite for that PR until the allowlist is updated) |
| Fixture-level coupling via `conftest.py` directory ancestry                                    | 9-12 `conftest.py` files per large repo, family-scoped                                                                                                                      | A changed `conftest.py` invalidates its ENTIRE subtree unconditionally (never traced via imports — pytest doesn't resolve fixtures that way). A changed HIGH-level `conftest.py` (e.g. repo-root or `tests/`) invalidates the WHOLE suite, since fixture resolution walks upward from every test file to the root                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Config/data-driven tests                                                                       | `test_validate_strategy_manifest.py`, `test_workspace_manifest_tags.py`                                                                                                     | A maintained allowlist of "artifact files with no static import edge to their tests" (manifests, YAML registries) maps any change to that artifact → the FULL suite of tests known to reference it by string literal (grep-based secondary signal) OR, for the two "core" cross-cutting manifests (`workspace-manifest.json`, `strategy-manifest.json`), unconditionally the full suite — these are cross-cutting by design, narrowing them is not attempted                                                                                                                                                                                                                                                                                                                         |
| Anything the AST walk can't parse, or a changed file outside the known source roots            | N/A — structural fallback, not a discovered case                                                                                                                            | Parse error, unresolvable path, or a changed file the walker has no record of ⇒ full suite. This is the todo's own explicit requirement (3) below, restated as code behavior, not policy                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

### (3) The fallback rule

**Ambiguity always resolves to "run everything," and "ambiguous" is defined expansively, not narrowly.** The selector's
output is binary at the top level: either it emits a provably-safe narrowed test set, or it emits `RUN _FULL_SUITE=true`
and the QG script ignores the narrowed set entirely. Concretely, `RUN_FULL_SUITE` fires if ANY of: the diff touches a
file in the dynamic-dispatch allowlist or a file the allowlist maintainer hasn't yet classified; the diff touches any
`conftest.py` above leaf level; the diff touches a config/data artifact not on the narrow-safe allowlist; the AST walk
fails to parse any changed file; the diff touches `unified-trading-library` or `unified-api-contracts`
(shared-dependency repos other test suites editable-install against — narrowing here is explicitly out of scope for v1,
full stop); or the selector's own process errors for any reason (fail-open to "run everything," never fail-open to "run
nothing"). This makes the common case (a single self-contained service-internal change with no dynamic dispatch, no
conftest touch, no config touch) the one that narrows — everything else pays the existing full-suite cost, unchanged
from today.

### (4) How the design tests itself

Three layers, escalating in cost and confidence, all required before the selector is trusted to actually skip a real CI
run:

1. **Golden-set unit tests for the selector itself** (this is the mandatory regression suite the todo names): a fixture
   repo (or a frozen snapshot of a real repo's file tree) with known import relationships, a known dynamic-dispatch
   file, a known multi-level `conftest.py` tree, and a known config-driven test — asserting the selector produces the
   exact expected narrowed set for the safe cases and `RUN_FULL_SUITE=true` for every one of the 4 escape-hatch
   categories above. A false-negative in ANY of these is a shipped regression in the selector itself — this suite is the
   thing that must never go red silently.
2. **Shadow-mode trial (the actual proof, not the static analysis alone)** — before the selector is EVER allowed to skip
   real test execution, run it in parallel with the existing full suite for a minimum trial window (e.g. 2 weeks
   fleet-wide, long enough to see real diff variety across every repo, not a hand-picked sample): compute the narrowed
   set, but always actually run the FULL suite too, and log whether the full suite's result would have differed from
   what the narrowed set alone would have reported. Promotion criterion: **zero observed divergences** across the full
   trial window, not "mostly zero" — any single divergence (a test outside the narrowed set that would have failed) is a
   design bug, not statistical noise, and resets the trial.
3. **A standing canary, post-promotion** — even after promotion, run the full suite on a low-frequency schedule (e.g.
   nightly per repo, cheap since it's off the hot path) purely to keep catching any escape-hatch gap the shadow-mode
   trial's window didn't happen to exercise. A canary regression pages the same way any other CI failure does and is
   treated as a P0 (a live under-testing gap, not a flaky test).

### Rollout model (explicit, since the todo gates on this)

This design is complete but **implementation is intentionally not started here**, per the parent todo's own instruction
("do not implement from this todo directly"). The natural next step is a follow-up implementation todo, gated on this
design being reviewed, scoped as: (a) build the import-graph walker + allowlists, (b) build the golden-set selector
tests (layer 1), (c) run shadow-mode (layer 2) on ONE repo first (not fleet-wide) to prove the approach before the
2-week fleet trial, (d) only then scope the fleet-wide shadow trial and eventual promotion. Each of those is its own
bounded, checkable unit of work — not one big "implement selective testing" todo.

## Follow-up

- [x] ✅ **Operator review of this design — APPROVED 2026-08-03 (interactive session).** Operator confirmed the safety
      model (conservative-superset, enumerable escape hatches, mandatory shadow-mode trial with a zero-divergence
      promotion bar) — "im fine with the design unblock Phase 2." Implementation is now authorized to begin per the
      staged rollout below; the companion plan's Phase 2 `BLOCKED-OPERATOR-DECISION` tags are cleared in the same edit
      (`test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`).
- [x] ✅ **Implementation-authorization todos — already scoped, not re-authored here.** The companion plan
      (`test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`, Phase 2) already carries the staged rollout as
      independently-checkable todos (walker + allowlists → golden-set selector tests → single-repo shadow trial → fleet
      shadow trial → promotion) — that plan is the live dispatch surface now that review has cleared; nothing further
      needed here.
