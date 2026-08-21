---
doc_type: issue
title:
  data_status_cell_grid_rearchitecture_2026_07_18.md todo 3 (bounded date-window read) shipped as
  deployment-api@777f1fa531 -- source plan was live-edited concurrently and could not be flip-cited directly
summary: >-
  This session implemented + shipped the ready-to-apply 6-file `date_window` threading spec left in
  data_status_cell_grid_rearchitecture_2026_07_18.md's 2026-08-20 Progress Log entry (todo 3, the Bound direction).
  deployment-api quality-gates ran green (5411-5412 passed both runs; the only failures were a shifting subset of
  the unrelated TestProductionGuardBootRejection auth-boot-subprocess class -- host contention, not this diff).
  Shipped as deployment-api@777f1fa531, verified landed on origin/live-defi-rollout. When attempting to flip the
  source plan's todo 3 checkbox, the doc was found under active, uncommitted, very-recent edit by another session
  (mtime within ~100s of the check -- an apparent na-eligibility-audit RECLASSIFY pass touching ~80 plans/active
  files workspace-wide, which also removed the BLOCKED-SANDBOX markers from this same plan's todos 3/5 and flipped
  assigned_vm NA -> planning). Per the inherited-dirty-WIP liveness rule this doc could not be safely edited
  directly. Filing this separately so the shipped evidence is durable and, critically, so an AO worker picking up
  the now-`assigned_vm: planning` doc does not redispatch/redo todo 3's already-shipped work.
status: open
nature: issue
asset_group: [ui]
stage: [execution]
repos: [deployment-api, unified-trading-pm]
scope: [engineer]
tags: [cell-grid, oom, data-status, deployment-api, evidence-citation, dirty-wip-collision]
related:
  [/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md]
created: "2026-08-21"
author: T1 tranche session
source: >-
  First-hand: this session wrote, tested (deployment-api quality-gates.sh, two runs), and shipped the todo-3 code
  change itself (deployment-api@777f1fa531), then found the source plan doc under live concurrent edit when
  attempting to flip the checkbox -- not a relayed/sub-agent finding.
priority: P1
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md]
locked_by:
resolved_by:
supersedes:
superseded_by:
---

# Cell-grid todo 3 shipped (`deployment-api@777f1fa531`) -- flip the source plan once its concurrent edit settles

## What shipped

`data_status_cell_grid_rearchitecture_2026_07_18.md`'s 2026-08-20 Progress Log entry recorded a fully-designed,
ready-to-apply 6-file spec for todo 3 (the Bound direction, threading an optional `date_window: (start, end)` param
through the on-demand manifest live-build fallback path so it takes the same pyarrow row-group predicate-pushdown
`/coverage-grid` already proved). This session applied that spec verbatim:

1. `deployment_api/services/data_status_service.py::_read_index_cached` -- added `date_window` param, cache key
   became `(bucket, date_window)`, threaded to `read_availability_index(bucket, date_window=date_window)` (the
   module-level import aliases `manifest_source.read_manifest_index`, which is what actually implements the
   pushdown -- confirmed by reading both functions, not assumed from the spec's shorthand).
2. `deployment_api/services/data_status/defi.py::_read_defi_merged_index` + `_collect_defi_index_frames` -- added
   the same optional param, threaded to both `_read_index_cached` call sites (main + sub-dimension bucket).
3. `deployment_api/services/data_status/manifest_category_builder.py::_resolve_category_bucket_and_index` -- same,
   threaded to `_read_defi_merged_index`; `_build_manifest_category`'s call site passes
   `date_window=(start_date, end_date)`.
4. `deployment_api/services/data_status/manifest_category_builder_dual_scope.py::_build_manifest_category_dual_scope`
   -- same call-site change.
5. `deployment_api/services/data_status/sports.py::_read_upstream_venue_dates` -- passes
   `date_window=(start_date, end_date)` (already had both in scope, no signature change needed -- static method).
6. `deployment_api/services/data_status/missing_shards.py::_scan_category_manifest` -- same treatment.

`coverage.py` / `coverage_dual_scope.py` (`GET /coverage-summary`) deliberately left unchanged, per the spec's own
scoping note (no date-range param on that endpoint by design).

Added regression tests pinning the new threading (not in the original spec, added this session):
`tests/unit/test_data_status_service.py::TestReadIndexCached::test_date_window_threaded_to_underlying_read` +
`::test_windowed_and_unwindowed_reads_cache_separately`; `tests/unit/test_manifest_status_dual_scope.py::
TestBuildManifestCategoryDualScope::test_date_window_passed_to_resolve_single_scope` + `::..._dual_scope`.

**Evidence**: `deployment-api@777f1fa531` -- verified an ancestor of `origin/live-defi-rollout`
(`git rev-list --count HEAD..origin/live-defi-rollout` = 0 post-push) and content-verified via
`git show origin/live-defi-rollout:deployment_api/services/data_status_service.py | grep -c "date_window: tuple"`.

**QG evidence**: two full `quality-gates.sh` runs on deployment-api, 605s and 460s. Run 1: 3 failed / 5411 passed.
Run 2: 2 failed / 5412 passed (one new test collected -- the regression tests above). All failures were inside
`tests/unit/test_auth.py::TestProductionGuardBootRejection` (`subprocess.TimeoutExpired` on a fresh-process
`import deployment_api.auth`, 30s) -- a **different** subset of that class failed each run (run 1:
`test_disable_auth_true_deployment_env_prod_rejected_at_boot` / `..._production_rejected_at_boot` /
`test_disable_auth_unset_in_prod_boots_fine`; run 2: `..._prod_rejected_at_boot` again + a THIRD, different test
`test_disable_auth_true_non_prod_boots_fine`), which is the shifting-failure-set signature of host contention
(this slot had 5+ other live sessions running concurrently all session), not a stable regression -- and this diff
touches no file `test_auth.py` or its subject (`deployment_api/auth.py`, boot-time guard logic) comes anywhere
near. None of the 6 changed files or 4 new tests appear in either run's failure list.

**Todo 7 (codex audit)** was also completed this session, since it is correctly sequenced after todo 3 ships and
does not touch the contested plan doc:
[`deployment-observability.md`](/codex/05-infrastructure/deployment-observability.md) § "deployment-api cache &
memory architecture" gained a new paragraph ("Bounded date-window read on the live-build fallback") documenting
the change, explicitly restating the plan's own "does NOT retire the OOM guard" caveat (row-group pushdown is
near-zero-reduction for genuinely full-history requests, since cefi/MTDS row groups span 2-2.5 calendar years each)
so the codex doc doesn't imply more than what actually shipped.

## Why this is a separate doc instead of a direct checkbox flip

When attempting to flip todo 3 `[ ]` -> `[x]` in the source plan directly, `git status` showed it already modified
and uncommitted, with an mtime ~100s old (well inside the workspace's live-WIP liveness window) -- part of an
apparent na-eligibility-audit RECLASSIFY pass touching roughly 80 files across `plans/active/` in this shared
checkout simultaneously. Its own uncommitted diff (read via `git diff`, not touched) shows it independently:
flipped `assigned_vm: NA` -> `planning` / `execution_scope: local-only` -> `orchestrator-agent`, removed the
`BLOCKED-SANDBOX` markers from todos 3 and 5 (correctly -- those were an interactive-session `isolation: "worktree"`
artifact, not a real block for an AO worker with a full checkout), strengthened todo 8's done-when, and authored a
companion `data_status_cell_grid_rearchitecture_finalize_2026_08_21.md` gated on this plan's completion. Editing a
file mid-write by another live session risks losing that work or corrupting its multi-file commit; per this
workspace's inherited-dirty-WIP rule, a live claim (mtime this recent) is PROTECT, not inherit.

**The urgent risk this creates**: the reclassification flips `assigned_vm` to `planning` (AO-dispatchable) while
todo 3's checkbox is still `[ ]` in that session's own diff -- an AO worker could pick this plan up and redo the
exact 6-file change already shipped here, wasting a dispatch cycle re-deriving work this doc already did. This
issue doc's evidence block above is written so whichever session flips the checkbox next (the na-eligibility-audit
session itself, once it commits; an AO worker; or a future finalize-doc pass) can cite `deployment-api@777f1fa531`
directly instead of re-verifying or re-implementing.

## Todos

- [ ] [DOC] P1. **Once `data_status_cell_grid_rearchitecture_2026_07_18.md` is no longer under live edit
      (`git status --porcelain` clean on that path), flip its todo 3 checkbox to `[x]` citing
      `deployment-api@777f1fa531` and this issue doc**, then flip this doc's own todos and archive it (small,
      single-fact doc -- fold into the standard archival pass, no separate ritual needed beyond the checkbox flip
      + a `resolved_by` pointer to the flip commit).
- [ ] [REVIEW] P3. **If an AO worker is dispatched against this plan's todo 3 before the flip above lands, verify
      it detects the already-shipped SHA (e.g. via a pre-dispatch content check) rather than re-implementing** --
      no evidence either way yet; only actionable if/when it's observed to happen.

## Progress Log

- **2026-08-21** — Authored immediately after shipping `deployment-api@777f1fa531` and discovering the source plan
  under live concurrent edit. T1 tranche session, first-hand (not sub-agent-relayed).
