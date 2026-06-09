---
title:
  "unified-trading-library: strict-ify the ~108 pre-existing pyright/type suppressions + drive CODEX_MAX_VIOLATIONS 6→0"
parent_epic: plans/epics/infrastructure_master.md
assigned_vm: vm-cross-cutting
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
created: 2026-06-09
author: ikennaigboaka [slot-6·laptop]
status: active
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-06-09
source:
  - plans/active/issues/utl_strictify_preexisting_pyright_suppressions_2026_06_08.md
  - plans/active/utl_full_quality_gates_green_2026_06_01.md (parent QG-green campaign)
Codex SSOTs:
  - codex/06-coding-standards/quality-gates.md (Type Checking Standards; zero-baseline policy)
  - codex/06-coding-standards/README.md (imports, no Any, no type: ignore)
---

> **Wrapper plan** closing `plans/active/issues/utl_strictify_preexisting_pyright_suppressions_2026_06_08.md`.
> Post-May-23 housekeeping — NOT on the critical path; schedule freely behind live-DeFi work.

## Context + the discrepancy this plan corrects

The parent issue describes ~108 pre-existing type-suppressions in `unified-trading-library` HEAD (a prior automated
pass's templated shortcut) and asks to (a) strict-ify them and (b) "ratchet `CODEX_MAX_VIOLATIONS` 6→0".

**Diagnosis (verified 2026-06-09 by tracing every `V=$(( V + 1 ))` site in
`unified-trading-pm/scripts/quality-gates-base/base-library.sh`):** these are **two orthogonal axes** —

1. **The ~108 suppressions** (`# pyright: ignore`, `# type: ignore`, file-level `# pyright: reportX=false`) hide errors
   from the **basedpyright TYPECHECK step** (zero-baseline, hard-exit). The QG script **never scans for or counts them**
   — removing them does **not** decrement the `V` counter. They are real work only against basedpyright.
2. **`CODEX_MAX_VIOLATIONS=6`** gates the `V` counter, which counts **codex coding-standard violations** (V1–V6 below),
   documented as accepted exceptions in `QUALITY_GATE_BYPASS_AUDIT.md`. None of them are suppressions.

Operator decision 2026-06-09: do **both** — clear the suppressions **and** drive `CODEX_MAX_VIOLATIONS` to 0.

The 6 counted violations (from `scripts/quality-gates.sh:75-82`, to be re-verified against a live `--no-fix` run in
Phase 0):

- **V1** — `os.environ.get(...)` in `manifest_consolidator.py:151,152,174` (consolidator CLI/Cloud-Run tunables).
- **V2** — imports-inside-functions (legacy lazy-import pattern, AST-detected, several modules).
- **V3** — empty-string fallback (`config_interface/persistence.py`).
- **V4** — deep unified-lib import in `config_interface/persistence.py` (`ConfigVersionEntry`).
- **V5** — bandit B608 (DuckDB/BigQuery SQL string) — **genuine false positive**; resolve via sanctioned `# nosec B608`
  on every flagged callsite (the canonical bandit mechanism — already present on most; find + annotate the residual) or
  restructure. NOT a type-suppression; NOT a bug.
- **V6** — STEP 5.23 deep UAC import.

## Method (per the parent QG-green campaign + the issue's recommended decision)

Replace bare suppressions with **exact-rule** `# pyright: ignore[reportX]` **only** where a dependency is genuinely
stub-limited; otherwise **fix the type**: add a `cast()`, a local `Protocol`, or proper annotations. Apply the
**`cloud_interface/providers/_gcp_sdk_protocols.py` Protocol pattern** (structural `Protocol` + no-op `cast()`) at the
boto3 / google / fsspec / firestore SDK boundaries. File-level blanket `# pyright: reportX=false` directives are the
worst offenders — replace each with either proper typing or the narrowest exact-rule per-line ignores. Delete the bare
suppression once the type is real. **No new broad/blanket suppressions.**

## Foundation-Completion-Gate + parallelization

Each cluster = **one Commit+Push+Flip unit**, parallel-safe (disjoint file sets). Sub-agents EDIT + verify each touched
file with `basedpyright <file>` clean (check-only, safe in parallel); the **QG-sweep** runs `quality-gates.sh --no-fix`
once per wave over the whole repo (host cap ≤2 concurrent QG), then per-cluster `quickmerge --agent --files '<paths>'`
commits serialize through one actor (shared `.git/index`). Phase 3 (the ratchet) is gated on **all** of Phases 1+2
landing green.

---

## Phase 0 — Baseline capture (DO FIRST)

- [ ] [SCRIPT] P0. Run `cd unified-trading-library && bash scripts/quality-gates.sh --no-fix` once; capture the exact
      TYPECHECK error set each suppression currently hides AND the live `V` breakdown. Confirm V1–V6 still match the
      script comment (drift-check). Snapshot the suppression inventory (43 bare `# pyright: ignore` + 43 bare
      `# type: ignore` + 22 file-level `# pyright: reportX=false`). This is the regression baseline for every cluster.

## Phase 1 — Suppression clusters (each = one Commit+Push+Flip; PARALLEL across clusters)

- [ ] [LIBRARY] P1. **domain_client/** — clear 10 bare `# type: ignore` + 8 file-level `# pyright: reportX=false`
      (`clients/{execution,instruments,market_data}.py`, `__init__.py`, `schemas/{instruction_schema,__init__}.py`,
      `readers/base.py`, `artifact_store.py`). Apply the Protocol/`cast()` pattern at the parquet/SDK boundaries.
      Evidence: `unified-trading-library@<sha> | basedpyright touched files clean | QG-sweep green`.
- [ ] [LIBRARY] P1. **feature_service_base/** — clear 12 bare `# pyright: ignore` + 4 bare `# type: ignore`
      (`metrics.py`, `validity.py`, `anti_leakage.py`, …).
- [ ] [LIBRARY] P1. **core/** — clear 5 bare `# pyright: ignore` + 2 bare `# type: ignore` (`error_handling.py`,
      `health_router.py`, `cloud_data_provider.py`).
- [ ] [LIBRARY] P1. **synthetic/** — clear 5 bare `# pyright: ignore` + 3 file-level `# pyright: reportAny=false`
      (`profile.py`, `generator.py`, `cli.py`).
- [ ] [LIBRARY] P1. **cloud_interface/** — clear 1 bare `# pyright: ignore` + the file-level directive on
      `providers/protocol_impls.py` (extend the existing `_gcp_sdk_protocols.py` / `_aws_sdk_protocols.py` pattern).
- [ ] [LIBRARY] P1. **risk/** — clear 1 bare `# pyright: ignore` + 6 bare `# type: ignore` (`rule_evaluator.py`,
      `family_aggregator.py`).
- [ ] [LIBRARY] P1. **streaming/** — clear 2 bare `# pyright: ignore` (`parallel_per_symbol_runner.py`).
- [ ] [LIBRARY] P1. **service_framework/** — clear 3 bare `# pyright: ignore` + 4 bare `# type: ignore`.
- [ ] [LIBRARY] P1. **manifest cluster** — `manifest_migrations/` (4 type:ignore), `lifecycle/` (4), `migrations/` (2),
      `manifest_freshness.py` (2 pyright:ignore), `manifest_completeness.py` (3). Group: shared manifest-row internals.
- [ ] [LIBRARY] P1. **post_trade / margin / recovery / scenario** — `post_trade/` (4 pyright:ignore),
      `margin_and_liquidation/` (3 type:ignore), `recovery/` (1), `scenario/` (1).
- [ ] [LIBRARY] P1. **domain / features_interface / root-files** — `domain/{timestamp,date}_validation.py` (file-level +
      1 type:ignore), `features_interface/adapters/{footystats,understat}.py` (the **largest** blanket directives, 30+
      rules each — external-API adapters; type the response shapes or apply narrowest exact-rule ignores), `io/` (1),
      `batch_live_reconciler.py` (2), `service_runtime.py` (file-level + 1), `options_cluster_lookup.py` (1),
      `startup_validation.py` (file-level), `instruments_write_gate.py` (file-level).

## Phase 2 — Codex V1–V6 (drive `V` to 0; PARALLEL with Phase 1, disjoint files)

- [ ] [LIBRARY] P1. **V1** — replace the 3 `os.environ.get(...)` consolidator tunables in `manifest_consolidator.py`
      with the typed-config / `UnifiedCloudConfig` pattern (or confirm the `# noqa: qg-os-environ` allowance is honored
      by the checker — if the checker counts them despite the noqa, refactor to config).
- [ ] [LIBRARY] P1. **V2** — hoist the AST-detected imports-inside-functions to module top (respect the
      lazy-import-heavy-ML-deps exception — only hoist non-ML, non-cycle imports; document any that MUST stay lazy and
      confirm the checker excludes them).
- [ ] [LIBRARY] P1. **V3+V4** — `config_interface/persistence.py`: remove the empty-string fallback (fail-fast) and
      replace the deep unified-lib import (`ConfigVersionEntry`) with a top-level/facade import.
- [ ] [LIBRARY] P1. **V5** — annotate every bandit-B608-flagged SQL string with the sanctioned `# nosec B608` (find the
      residual flagged callsite not yet annotated; most already carry it). Genuine false positive — no bug.
- [ ] [LIBRARY] P1. **V6** — fix the STEP 5.23 deep UAC import (use `from unified_api_contracts.{domain} import X`).

## Phase 3 — Ratchet + close (GATED on Phases 1+2 all green)

- [ ] [SCRIPT] P0. After every cluster + V1–V6 land, set `CODEX_MAX_VIOLATIONS=6 → 0` in
      `unified-trading-library/scripts/quality-gates.sh:~82` and prune the V1–V6 comment block. Update the matching
      `QUALITY_GATE_BYPASS_AUDIT.md` sections (remove the now-resolved exceptions; keep V5's nosec rationale).
- [ ] [SCRIPT] P0. Full `bash scripts/quality-gates.sh` green at `CODEX_MAX_VIOLATIONS=0` with zero bare/blanket
      suppressions remaining (re-grep: 0 hits for `# pyright: ignore` w/o `[rule]`, 0 bare `# type: ignore`, 0
      file-level `# pyright: reportX=false`). Verify via CI `quality-gates-v2` on the staging PR.
- [ ] [DOCS] P0. Archive `plans/active/issues/utl_strictify_preexisting_pyright_suppressions_2026_06_08.md`
      (issue-doc-lifecycle: acked → shipped → archive). Banner-link this plan.

## Success criteria

- Zero bare `# pyright: ignore` (no rule code), zero bare `# type: ignore`, zero file-level `# pyright: reportX=false`
  in `unified_trading_library/`. Exact-rule `# pyright: ignore[reportX]` retained ONLY for genuinely stub-limited deps,
  each with a one-line rationale.
- `CODEX_MAX_VIOLATIONS=0`; full `quality-gates.sh` exit 0; `quality-gates-v2` green on the promotion PR.
- Issue doc archived.

## Continuous verification

The QG `STEP 5.21` + `STEP 5.22` (zero-baseline) + `CODEX_MAX_VIOLATIONS=0` ceiling permanently prevent regression — any
re-introduced bare suppression that hides an error fails TYPECHECK; any new codex violation trips the now-zero ceiling.
