---
name: utl_full_quality_gates_green_2026_06_01
title:
  "unified-trading-library full quality-gates.sh → GREEN (B1 type-hardening campaign + imports/size/coverage backlog)"
parent_epic: plans/epics/infrastructure_master.md
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
created: 2026-06-01
last_updated: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
codex_ssots:
  - codex/06-coding-standards/quality-gates.md
source_issue: plans/archive/2026_06/utl_full_qg_red_backlog_2026_06_01.md
related_plans:
  - plans/active/manifest_reader_fail_fast_on_stale_fallback_2026_05_28.md
  - plans/archive/2026_06/manifest_consolidator_liveness_health_2026_06_01.md
---

# unified-trading-library full `quality-gates.sh` → GREEN

## Why this exists

`bash scripts/quality-gates.sh` in **unified-trading-library** (Tier-0; every service depends on it) exits **1** on a
pre-existing backlog — it violates the workspace HARD RULE **"Quality Gates Are A Merge Prerequisite."** UTL has been
shipping to `live-defi-rollout` red because the dirty-dep direct-push path has no remote CI and `quickmerge` (which runs
the codex gate) was not used.

This plan **acks + owns** the backlog catalogued in the now-archived issue doc
[`utl_full_qg_red_backlog_2026_06_01.md`](../archive/2026_06/utl_full_qg_red_backlog_2026_06_01.md). The feature work of
the two plans that surfaced it (`manifest_reader_fail_fast_on_stale_fallback` C4 + the archived
`manifest_consolidator_liveness_health` C4) is **shipped + verified**; only the repo-wide green gate is unmet, and no
single plan owned it. This plan is that owner.

> **Blocks**: `manifest_reader_fail_fast_on_stale_fallback_2026_05_28` C4 (full `quality-gates.sh` exit 0) closes when
> this plan reaches Phase 6.

## The backlog (verified @ `unified-trading-library@73209d50`)

| #   | Check                                                                                                                                                          | Scope                                                                                                                                                                                               | Why it's not a quick fix                                                                                                                                                                               |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| B1  | **STEP 5.21** — `reportUnknownMemberType/VariableType/ParameterType/ArgumentType/LambdaType = "none"` in `pyproject.toml` (workspace strict default = `error`) | repo config                                                                                                                                                                                         | Flipping to `error` surfaces **962 basedpyright errors**, almost all from untyped third-party deps (pandas/duckdb/google-cloud/pyarrow). Dominant blocker.                                             |
| B2  | **imports-inside-functions** ×25 (AST-detected)                                                                                                                | `instruments_catalog_reader.py`, `manifest_writer.py`, `point_in_time.py`, `legacy_reason_classifier.py`, `synthetic/cli.py`, `treasury/withdrawal_reconciler.py`, `services/client_worker_base.py` | Mostly deliberate deferred imports (heavy deps / circular-import avoidance) — need per-line `# noqa: imports-inside-functions` (PLC0415).                                                              |
| B3  | **Deep unified-lib imports**                                                                                                                                   | `legacy_reason_classifier.py` ×7 (`unified_api_contracts.registry.*`) + `margin_model`, `settler`, `options_cluster_lookup`, `approval_bus`, `understat`, `footystats`                              | Facade does not re-export the registry submodules (`half_day_sessions`/`venue_session_hours`/`chain_env`/`venue_launch_dates`/`generators`). Fix = add UAC facade exports OR `# noqa: qg-deep-import`. |
| B4  | **Function/class/method size**                                                                                                                                 | `event_sink.py:110 GcsEventSink.write_event()` = 59L (limit 50)                                                                                                                                     | Clean helper-extract.                                                                                                                                                                                  |
| B5  | **Test coverage 79.49% < 80%**                                                                                                                                 | repo-wide                                                                                                                                                                                           | Borderline (~0.5% gap); the gate early-exits before codex. Confirm determinism, then add targeted tests for lowest-covered modules.                                                                    |

## Design decision (SSOT for this plan)

**Restore workspace strict-basedpyright compliance — do NOT institutionalise the `"none"` downgrade.** The workspace
standard is `reportUnknownMemberType/VariableType/...= error` (`§ Workspace Configs`); UTL's `"none"` is an
out-of-compliance local override. The campaign's order of operations minimises hand-annotation:

1. **Install available type stubs FIRST** (`pandas-stubs`, `types-protobuf`, `types-pyarrow` if available,
   `google-cloud-*` typed packages) — this auto-resolves a large fraction of the 962 before any hand-annotation.
2. **Measure the residual** error count after stubs land. The annotate-vs-narrow-exemption call (Phase 1 P0) is then
   made on the _real residual_, not the gross 962.
3. **Annotate the residual** by module (Phase 2). A **narrow, documented per-rule exemption** is acceptable ONLY for
   genuinely-unstubbable deps, and ONLY as `BLOCKED-OPERATOR-DECISION` with explicit rationale in `pyproject.toml` — NOT
   a blanket `"none"`.

## Phases

### Phase 1 — B1 triage: stubs + informed annotate-vs-exempt decision (P0, foundation)

- [ ] [INFRA] P0. Add available type-stub packages to UTL `pyproject.toml` flat deps (`pandas-stubs`, `types-protobuf`,
      typed `google-cloud-*`, `types-pyarrow`/`duckdb` stubs where they exist). `uv pip install`, re-lock.
- [ ] [INFRA] P0. Flip `reportUnknownMemberType/VariableType/ParameterType/ArgumentType/LambdaType` from `"none"` →
      `error` in `pyproject.toml`; run `run_timeout 120 basedpyright unified_trading_library/` and record the
      **residual** error count + per-module histogram (post-stubs). Compare to the 962 baseline.
- [ ] [DESIGN] P0. On the residual: decide per-rule **annotate** (default — restore strict) vs a **narrow documented
      exemption** for unstubbable deps only. If exemption: codify `BLOCKED-OPERATOR-DECISION` with explicit rationale +
      the exact deps it covers, never a blanket downgrade. Surface the residual count + recommendation to the operator.

### Phase 2 — B1 annotation campaign (P0)

- [ ] [TYPE] P0. Annotate the residual basedpyright sites module-by-module (one commit per module cluster, QG-green
      ratchet on the touched module). Prefer explicit return/param annotations + `cast()` at dep boundaries over
      `# type: ignore` (banned by workspace standard).
- [ ] [TEST] P0. After each module cluster, `run_timeout 120 basedpyright unified_trading_library/<module>/` exits
      clean.

### Phase 3 — B2/B3 imports (P1)

- [ ] [UAC] P1. Add the missing registry facade re-exports in `unified-api-contracts`
      (`half_day_sessions`/`venue_session_hours`/`chain_env`/`venue_launch_dates`/`generators`) so the B3 deep imports
      become facade-clean (`from unified_api_contracts import …`). Audit each of the ~7 sites.
- [ ] [UTL] P1. For the deliberate deferred imports (B2 ×25) that are genuinely heavy-dep / circular-import avoidance,
      apply per-line `# noqa: imports-inside-functions` (PLC0415) with a one-word reason. Files are UTL-owned — confirm
      ownership before touching.

### Phase 4 — B4 size + B5 coverage (P1)

- [ ] [UTL] P1. Helper-extract `GcsEventSink.write_event()` (`event_sink.py:110`, 59L → ≤50L) into a clean private
      helper; behaviour-preserving, unit test unchanged.
- [ ] [TEST] P1. Confirm coverage determinism (re-run); if genuinely <80%, add targeted tests for the lowest-covered
      modules until ≥80%. The gate early-exits on coverage before codex, so this unblocks the codex step.

### Phase 5 — process fix: UTL gets remote CI so debt cannot re-accumulate (P1)

- [ ] [CI] P1. Wire UTL into a remote `quality-gates-v2` required check on `live-defi-rollout` (or enforce
      `quickmerge --agent` for all UTL promotion) so the dirty-dep direct-push path can no longer ship red. Document the
      enforced path in `codex/06-coding-standards/quality-gates.md`.

### Phase 6 — close-out (P0 verification)

- [ ] [TEST] P0. Full `bash scripts/quality-gates.sh` in `unified-trading-library` exits **0** (no skip flags; writes
      `.qg_last_passed_sha`). Capture the green evidence line.
- [ ] [DOC] P1. Flip `manifest_reader_fail_fast_on_stale_fallback_2026_05_28` C4 → ✅ (cite this plan + the QG-green
      SHA).
- [ ] [CODEX] P1. Post-phase codex audit: update `codex/06-coding-standards/quality-gates.md` if the stub strategy / any
      documented per-rule exemption becomes a new workspace pattern.

## Success criteria

- C1: post-stubs basedpyright residual measured + the annotate-vs-exempt decision recorded (Phase 1).
- C2: `basedpyright unified_trading_library/` clean with the strict rules at `error` (or a narrow documented
  `BLOCKED-OPERATOR-DECISION` exemption for named unstubbable deps only).
- C3: B2/B3/B4/B5 cleared.
- C4: full `bash scripts/quality-gates.sh` exits 0; `.qg_last_passed_sha` written.
- C5: UTL on a remote-CI / quickmerge-enforced path; `manifest_reader_fail_fast` C4 flipped ✅.

## Out of scope (deferred — named successors required)

- Type-hardening **other** Tier-0/Tier-1 repos to strict compliance — if a sibling repo also carries a `"none"`
  downgrade, file `<repo>_quality_gates_green_<date>.md` per repo; do NOT bundle here.

## Codex SSOTs

- `codex/06-coding-standards/quality-gates.md` — STEP 5.21 strict-basedpyright policy + any documented exemption.

## Provenance

Filed 2026-06-01 (slot 1, operator-directed "yes") to give the UTL-QG-red backlog an owner. Acks + supersedes issue doc
`utl_full_qg_red_backlog_2026_06_01.md` (archived to `plans/archive/2026_06/` on ack per issue-doc-lifecycle).
