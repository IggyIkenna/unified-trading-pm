---
doc_type: issue
title:
  "manifest_hygiene_daily.py escalation-issue filename collides across asset_groups (destroys prior findings) + its
  phantom/4pillar subprocess calls fail without GCP_PROJECT_ID in the invoking shell"
summary:
  "Discovered 2026-07-14 while running the G2 verification todo in mvp_backfill_defi_onchain_v10_2026_06_27.md. (1)
  `e2e-testing/scripts/audit/_dp_common.py::file_escalation_issue` writes to `plans/active/issues/{slug}_{date}.md` with
  a FIXED slug (`manifest_hygiene_red`) and no asset_group in the path. The docstring assumes one invocation per UTC day
  covering ALL asset_groups, but the CLI accepts `--asset-group` and is routinely invoked per-asset_group (a defi-only
  run and a cefi-only run, same day) — the second invocation silently overwrites the first's file, discarding its
  frontmatter (`status: resolved`, `resolved_by`) and its completed root-cause-analysis todo, replacing them with an
  unresolved todo for the new asset_group. Caught in this session before it reached git (working tree only, restored via
  `git restore`); nothing was actually lost, but this is the second occurrence of this failure CLASS after
  `audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md` (resolved) — that fix added commit/push logic
  but did not asset_group-scope the filename. (2) A `--mode full` run for `defi` logged `Cannot resolve manifest bucket
  for defi: Required environment variable 'GCP_PROJECT_ID' is not set` for its divergence + 4-pillar sub-checks (harness
  errors, correctly NOT counted as shard fails) AND its phantom-reconcile subprocess call
  (`reconcile_phantom_manifest_rows_all.py --dry-run`) also failed for the same reason — but that failure was NOT
  classified as a harness error like the 4-pillar one; it was recorded as a `phantom_captured_no_parquet: count=1`
  finding with an uninformative detail string (`phantom CLI rc=1`), i.e. an environment-config failure silently posing
  as a real data finding."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, instruments-service]
scope: [engineer, admin]
tags: [data-pipeline, observability, audit, manifest-hygiene, git-hygiene, tooling-defect]
related:
  [
    plans/active/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md,
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
  ]
created: 2026-07-14
parent_epic: observability_master
priority: P2
source:
  [
    "data_engineering slot-16, 2026-07-14, running mvp_backfill_defi_onchain_v10 G2 verify todo",
    "e2e-testing/scripts/audit/manifest_hygiene_daily.py",
    "e2e-testing/scripts/audit/_dp_common.py::file_escalation_issue",
  ]
assigned_vm: planning
resolved_by: e2e-testing@407a6f9
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
---

# manifest_hygiene_daily.py: cross-asset_group filename collision + env-dependent subprocess failures mis-classified as findings

## What I found

Running `python scripts/audit/manifest_hygiene_daily.py --asset-group defi --mode full` (per this plan's G2 todo)
produced two tooling defects, not real defi data findings:

1. **Filename collision destroys prior asset_group's resolved issue.** `file_escalation_issue()`
   (`e2e-testing/scripts/audit/_dp_common.py:375`) writes to `out_dir / f"{slug}_{date}.md"` — `slug` is the literal
   constant `"manifest_hygiene_red"` (see call site `manifest_hygiene_daily.py:631`), with no asset_group in the path. A
   prior slot's `cefi`-only run today had already produced and RESOLVED
   `plans/active/issues/manifest_hygiene_red_2026_07_14.md` (`status: resolved`, `resolved_by: e2e-testing@0fa7148`, its
   `[CODE] P1` todo checked with a detailed root-cause writeup). My `defi`-only run overwrote that same path, resetting
   `status` back to a bare todo referencing `defi` instead of `cefi` — the resolved analysis would have been silently
   destroyed had the auto-commit succeeded (it didn't, for reason unrelated to this — see repo state note below). I
   caught it via `git diff HEAD` before it committed and ran `git restore` to recover the cefi version.
2. **Environment-dependent subprocess calls fail silently as data findings.** The same run's phantom-reconcile
   subprocess (`reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`, invoked internally) failed with
   `BucketNamingError: Required environment variable 'GCP_PROJECT_ID' is not set` (same root cause as the parallel
   4-pillar harness failure logged in the same run, which correctly appeared as
   `WARNING 4-pillar harness error ... rc=2, not a shard fail`). But the phantom subprocess's failure was NOT given the
   same harness-error treatment — it surfaced as a `phantom_captured_no_parquet: count=1` CSV row with detail
   `"phantom CLI rc=1"`, i.e. a plain environment misconfiguration recorded as if it were a genuine phantom-row finding.

## Why it matters

(1) is a data-loss risk for other agents/operators triaging manifest-hygiene findings — a per-asset_group escalation
silently clobbering another asset_group's resolved history undermines the entire audit→issue→plan escalation pipeline
this script exists to drive, and will recur every time two different asset_groups get a `--asset-group` run on the same
UTC day (a normal, expected usage pattern, not an edge case). (2) risks operators/workers spending time triaging a
phantom "finding" that is actually just a missing shell env var, and could mask a REAL `phantom_captured_no_parquet`
finding for defi (the true count is unknown until the phantom-reconcile script is run with the required environment
correctly set — see the parent plan's Progress Log for the direct-invocation result with `GCP_PROJECT_ID` supplied).

## Recommended decision

Fix both in `e2e-testing`: (a) make `file_escalation_issue`'s output path asset_group-aware (e.g.
`{slug}_{asset_group_or_all}_{date}.md`, derived from the actual `ag_results` keys passed to a single invocation) so two
different `--asset-group` runs on the same day never collide; (b) classify subprocess-level `BucketNamingError`/
missing-env failures the same way the 4-pillar harness already does (a harness-error log line, `SKIPPED` in the findings
table) instead of emitting a misleading `count=1` finding row.

## Todos

- [x] ✅ [CODE] P2. Asset_group-scope `file_escalation_issue`'s output filename in
      `e2e-testing/scripts/audit/_dp_common.py` (repo: e2e-testing) so a `defi`-only and a `cefi`-only run on the same
      UTC day never collide. Add a regression test asserting two same-day, different-asset_group calls produce two
      distinct files. — e2e-testing@d83f12c. Added `asset_groups` param folded into the filename
      (`{slug}_{ag_scope}_     {date}.md`, `all` when covering the full universe); wired both
      `manifest_hygiene_daily.py` and `reprobe_new_empty_confirmed.py` (same collision class) to pass their `ag_results`
      keys; 2 regression tests added (`test_file_escalation_issue_asset_group_scope_avoids_collision`,
      `test_file_escalation_issue_full_universe_scope_collapses_to_all`).
- [x] ✅ [CODE] P2. In `e2e-testing/scripts/audit/manifest_hygiene_daily.py`, classify a `BucketNamingError`/missing-env
      failure from the phantom-reconcile subprocess call the same way the 4-pillar harness error is already handled
      (log + `SKIPPED`, never a `count=1` finding row) (repo: e2e-testing). — e2e-testing@407a6f9. Added a
      `BucketNamingError`/`Required environment variable` text match in `_check_phantom` (mirrors `_check_4pillar`'s
      rc=2 harness-error branch): sets `fc.skipped = "phantom_harness_error"` + logs a warning instead of falling
      through to the generic rc!=0 branch that recorded a misleading `phantom_captured_no_parquet: count=1` finding.
      Regression test `test_check_phantom_missing_env_is_harness_error_not_fail` added.
