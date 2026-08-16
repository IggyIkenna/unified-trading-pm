---
doc_type: issue
title:
  "28 shared QG checker scripts lack a `.claude` exclusion — any locked per-agent worktree under a repo's
  `.claude/worktrees/<id>/` gets scanned as if it were the repo's own source, producing false violations for code nobody
  in the actual checkout wrote"
summary: >-
  Found live 2026-08-06 debugging an unrelated deployment-service QG failure: `test_event_logging.py`'s
  `find_python_files()` crashed on a dangling symlink inside a LOCKED nested worktree
  (`.claude/worktrees/agent-aa4b436033ef73e2f/`), and the same worktree's stale code independently tripped false
  positives in `check_manifest_import_alignment.py` (missing-manifest-declaration for imports that don't exist in the
  real checked-out tree) and `base-service.sh`'s STEP 5.79 dockerfile-pin scan. All three were fixed by adding `.claude`
  to the checker's own dir-exclusion set — never by touching the worktree itself (it is a live, `locked` per-agent
  artifact from another session; `git worktree list` confirms). A follow-up grep for the same
  `EXCLUDE_DIR*`/`SKIP_DIRS`-style pattern across `scripts/quality_gates/`, `scripts/validation/`, `scripts/qg/`,
  `scripts/checkers/`, `scripts/workspace/` found **28 more Python checker scripts with the identical gap** — every one
  excludes `.venv`/`.git`/`build`/`node_modules`/etc. but not `.claude`. None of the 28 has been individually confirmed
  to currently misfire (that requires a live locked worktree with divergent content to actually be present when the
  checker runs, which is intermittent/session-dependent) — this issue tracks the STRUCTURAL gap, not 28 confirmed false
  positives.
status: resolved
nature: issue
asset_group:
  [infrastructure] # corrected 2026-08-07 (ag-closeout-audit infra-tranche run) -- was [cross-cutting]. Real content is
  # generic repo/script-governance QG-checker hygiene (28 checkers missing a `.claude` worktree-exclusion pattern),
  # not data-pipeline correctness -- per the cross-cutting tranche's own 2026-08-07 audit finding 7, which deferred
  # the retag to infra as the owning tranche.
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, false-positive, worktree, tooling-gap, claude-worktrees]
related: [/codex/05-infrastructure/per-tab-worktrees.md]
created: "2026-08-06"
author: unknown
last_updated: "2026-08-07"
parent_epic: infrastructure_master
priority: P3
source: >-
  Surfaced while shipping the pipeline_e2e_check driver-VM pattern (2026-08-06) — chasing 3 confirmed false-positive QG
  failures on deployment-service back to a common root cause (a locked nested worktree lacking a `.claude` scan
  exclusion), then grepping for the same pattern workspace-wide.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-trading-pm@5955e07cdc
depends_on: []
context_scope:
  [
    scripts/quality-gates-base/base-service.sh,
    scripts/validation/check_manifest_import_alignment.py,
    scripts/quality_gates/check_no_legacy_bucket_string_concat.py,
    deployment-service/tests/unit/test_event_logging.py,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
---

> **ARCHIVED — resolved 2026-08-16.** All 30 checkers (list drifted 28→30 since 2026-08-06) fixed;
> unified-trading-pm@5955e07cdc. See Fix + Progress Log below.

# 28 shared QG checkers missing a `.claude` worktree exclusion

## What was found

Three checkers were confirmed, live, to mis-scan a `locked` nested per-agent git worktree
(`deployment-service/.claude/worktrees/agent-aa4b436033ef73e2f/`) as if its content were part of the actual checked-out
repo — because none of them excluded `.claude` from their source walk, only the usual `.venv`/`.git`/`build`/etc.:

1. `deployment-service/tests/unit/test_event_logging.py` — `find_python_files()` crashed with `FileNotFoundError` on a
   dangling symlink (`.cursor/scripts/check-import-patterns.py`) inside the worktree. **Fixed** (added `.claude` to its
   `exclude` set).
2. `scripts/validation/check_manifest_import_alignment.py` — flagged deployment-service for importing
   `unified_internal_contracts`/`unified_cloud_interface`/`unified_events_interface`/`unified_config_interface` without
   declaring them in its manifest — the imports existed only in the worktree's stale snapshot, not the real tree.
   **Fixed**.
3. `scripts/quality-gates-base/base-service.sh` STEP 5.79 (dockerfile-base-pin) — its `find` command walked the
   worktree's own stale `Dockerfile`. **Fixed**.

All three fixes were scoped to the CHECKER (add `.claude` to its exclusion list), never to the worktree itself — the
worktree is `locked` (confirmed via `git worktree list`), meaning it's a live, in-use artifact from another session, not
stray/cleanup-eligible state.

## Why this is a class, not 3 isolated bugs

A follow-up grep for the same dir-exclusion pattern (`EXCLUDE_DIR*` / `SKIP_DIRS` / `skip_dirs` constants in Python;
`find -not -path ".../.venv*"`-style filters in bash) across every checker directory found **28 more Python scripts**
with an exclusion set that lists `.venv`/`.venv-workspace`/`venv`/`build`/`dist`/`node_modules`/`__pycache__`/`.git` but
never `.claude`:

```
scripts/checkers/check-data-availability.py
scripts/qg/no_blank_record_empty_reason.py
scripts/quality_gates/check_adapter_contract_regression.py
scripts/quality_gates/check_banned_placeholder_methods.py
scripts/quality_gates/check_bar_edge_open_ingestion.py
scripts/quality_gates/check_bare_read_availability_index.py
scripts/quality_gates/check_canonical_futures_construction.py
scripts/quality_gates/check_canonical_model_regressions.py
scripts/quality_gates/check_emission_policy_paired_callsites.py
scripts/quality_gates/check_inline_bucket_uri.py
scripts/quality_gates/check_manifest_writer_missing_write_before_return.py
scripts/quality_gates/check_mdps_bar_available_at_stamping.py
scripts/quality_gates/check_no_category_kwarg_at_manifest_write.py
scripts/quality_gates/check_no_explicit_project_id_bucket.py
scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py
scripts/quality_gates/check_record_empty_reason_closed_set.py
scripts/quality_gates/check_removed_symbols.py
scripts/quality_gates/check_source_returned_zero_needs_fetch_evidence.py
scripts/quality_gates/check_subprocess_gcs_object_cli.py
scripts/quality_gates/check_tradfi_source_explicit_at_record_captured.py
scripts/quality_gates/check_uac_hard_required_fields.py
scripts/quality_gates/check_unrouted_source_returned_zero.py
scripts/validation/check-import-patterns.py
scripts/validation/check_env_canon.py
scripts/validation/check_schema_provenance.py
scripts/validation/validate-buildspec.py
scripts/validation/validate-cloudbuild.py
scripts/workspace/check-import-deps.py
```

(Regenerate via:
`grep -rlE 'EXCLUDE_DIR|exclude_dir|EXCLUDE_DIRS|SKIP_DIRS|skip_dirs' scripts/ --include="*.py" | xargs grep -L '"\.claude"'`
from the `unified-trading-pm` repo root — re-run before fixing, this list drifts as checkers are added/renamed.) A
separate bash-`find` sweep for the same class found no additional hits beyond the already-fixed `base-service.sh` STEP
5.79.

**Every `assigned_vm` slot's `.claude/worktrees/<id>/` can independently trigger this** — the failure mode is
intermittent (only fires when a locked worktree with content divergent from the real tree happens to exist at
QG-run-time), which is why it reads as 3 unrelated one-off flakes until grepped for the shared root cause.

## Why this wasn't fixed wholesale in the session that found it

Auditing and safely touching 28 files' exclusion logic (verifying each one's exact list-literal syntax, confirming no
checker relies on `.claude`-prefixed paths being scanned on purpose, running each affected repo's full QG afterward) is
real, bounded but non-trivial work — deliberately scoped out of the session that found it (which was mid-flight on an
unrelated VM-launch-pattern deliverable) per the "every deferral is a tracked todo, not prose" rule.

## Fix

- [x] ✅ [SCRIPT] P3. For each of the 28 files above: add `".claude"` to its dir-exclusion set/frozenset/tuple, following
      the exact pattern already applied in `check_manifest_import_alignment.py` and
      `check_no_legacy_bucket_string_concat.py` (both in this same repo, `unified-trading-pm`) — a one-line addition + a
      short comment explaining why (nested per-agent worktree can carry a stale/divergent snapshot of the SAME repo's
      source). Batch by directory (`scripts/quality_gates/`, `scripts/validation/`, `scripts/qg/`, `scripts/checkers/`,
      `scripts/workspace/`) for reviewable commit sizes. Re-run the grep above FIRST to confirm the list hasn't drifted,
      then verify each touched file still imports/runs clean
      (`python3 -c "import ast; ast.parse(open('<file>').read())"` at minimum; prefer actually invoking the checker). —
      unified-trading-pm@5955e07cdc. Re-ran the regen grep first per instruction: list had drifted from 28 to **30**
      (`check_pytest_unit_dir_coverage.py` and `check_xfail_skip_tracked.py` added since 2026-08-06) — fixed all 30, not
      just the original 28. Each file `ast.parse()`-verified clean; re-ran the regen grep post-fix — 0 remaining hits.

## Progress Log

- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-07 (infra tranche)**: RECLASSIFY, `assigned_vm: NA -> planning` (`execution_scope` ->
  `orchestrator-agent`). The one open todo is bounded, mechanical, deterministic-outcome work: add the literal string
  `".claude"` to an existing dir-exclusion set/frozenset/tuple in each of 28 named files, following an exact
  already-proven reference pattern from 2 sibling files in this same repo, with the file list independently regenerable
  via the grep command given in the doc body and a stated verification bar (each touched file still
  parses/imports/runs). No design ambiguity, no live-infra blast radius (the change only widens what a checker IGNORES,
  it cannot change checker PASS/FAIL semantics for real repo content). `assigned_role: data_engineering` is a valid
  registry role (`unified-trading-pm/agents/data_engineering.md`) — left as authored, not changed. Conflict-check
  (`ao-dispatch-batch-naming-and-conflict-check.md` § 3): grepped the full `plans/active/` corpus for the fix's own
  signature (`claude.*worktree.*exclusion`, `EXCLUDE_DIR.*claude`) — the only other hits are (a) this doc's own citation
  in `infra_consolidated_closeout_2026_07_25.md`'s Sources list (a pure linkage/tracking entry on an `assigned_vm: NA`
  hub doc with no todo of its own claiming this fix — not a competing claim), (b) a same-day
  `ag_closeout_audit_cross_cutting_parked_2026_08_07.md` finding recommending the exact retag-out-of-cross-cutting this
  doc already received earlier today (no fix-work claim, a tagging note only), and (c) two unrelated mentions of a
  DIFFERENT already-fixed checker's `.claude` exclusion used as an incidental precedent citation. No active
  `assigned_vm: planning` plan, satellite/finalize batch, or the infra tranche's own closeout doc claims this fix. Clear
  to flip. No finalize-plan twin required — `doc_type: issue` docs live under `plans/active/issues/` and
  `check_finalize_plan_coverage.py` globs only `plans/active/*.md` (verified by reading the script), so this doc type is
  structurally exempt regardless of todo count.
- **slot-13 2026-08-16**: fixed + shipped, unified-trading-pm@5955e07cdc (30 files — list had drifted from 28 to 30
  since 2026-08-06). Same session also hit + resolved an unrelated pre-existing quickmerge Stage-5 re-gate blocker
  (`plans/archive/2026_08/issues/doc_body_link_regression_placeholder_archetype_2026_08_16.md`) — landed in the same
  commit range, unrelated to this doc's own fix.
