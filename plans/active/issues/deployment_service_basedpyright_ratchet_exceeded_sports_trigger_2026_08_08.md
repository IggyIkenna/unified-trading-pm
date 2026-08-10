---
doc_type: issue
title: deployment-service basedpyright ratchet exceeded (1295 > 1293) — blocks all future quickmerges
summary: >
  A quickmerge re-gate for an unrelated fix (BLAZESTAKE DP-FETCH-009 detector) failed on deployment-service's
  basedpyright type-check ratchet, currently 1295 errors against a BASEDPYRIGHT_MAX_ERRORS=1293 ceiling. All 23
  offending errors are in sports_trigger_ evaluation.py/periodic.py/scheduler.py/state.py — files untouched by the fix
  that surfaced this. Independently reproduced standalone (not a transient collision): the errors are on committed HEAD,
  not from a dirty working tree. This blocks EVERY future code quickmerge to this repo until the ratchet clears, not
  just the one that found it.
status: open
nature: issue
asset_group:
  [ci] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is a
  # basedpyright quality-gate ratchet breach blocking every future quickmerge to one repo -- squarely
  # ci-tranche CI/CD-pipeline-mechanics territory, not cross-AG data-pipeline content.
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [quality-gates, basedpyright, ratchet, ci-blocking]
related: [cross_cutting_consolidated_closeout_2026_07_25]
created: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: backend_engineer
drift_direction: advance-code
source: >-
  Surfaced while shipping an unrelated operator-approved fix (DP-FETCH-009 detector, interactive session, 2026-08-08) —
  quickmerge's re-gate step failed on a pre-existing basedpyright ratchet violation in files the fix never touched.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    deployment-service/deployment_service/sports_trigger_evaluation.py,
    deployment-service/deployment_service/sports_trigger_periodic.py,
    /codex/06-coding-standards/quality-gates.md,
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
  ]
---

## Finding

`quickmerge.sh`'s re-gate step failed shipping an unrelated fix
(`deployment_service/data_pipeline_monitors/{attempted_failed_staleness,meta_watchers}.py` +
`tests/unit/test_data_pipeline_monitors.py` — the DP-FETCH-009 `superseded_by_*` exclusion, operator-ruled 2026-08-08)
with:

```
1295 errors, 0 warnings, 0 notes
❌ Type check FAILED — 1295 error(s) > BASEDPYRIGHT_MAX_ERRORS=1293 (ratchet down to fix errors)
```

Every listed error is in 4 files, none touched by the fix that surfaced this:

- `deployment_service/sports_trigger_evaluation.py`
- `deployment_service/sports_trigger_periodic.py`
- `deployment_service/sports_trigger_scheduler.py`
- `deployment_service/sports_trigger_state.py`

Confirmed NOT a transient shared-clone collision: `git status --porcelain` on all 4 files returns empty (clean — these
errors are baked into committed HEAD, not someone's uncommitted WIP), and re-running `.venv/bin/basedpyright` standalone
against 2 of the 4 files independently reproduces a subset of the same errors (mostly
`reportUnknownVariableType`/`reportUnknownArgumentType`/`reportUnknownMemberType` — untyped dict access chains, e.g.
`trigger_raw = ...get(...)` with no narrowing).

## Impact

This is a HARD ratchet gate (`quality-gates.md`'s "NEVER raise a count" convention) — it will fail identically for ANY
future commit to this repo, regardless of what files that commit touches, until the error count drops back to or
below 1293. Currently blocking:

- The DP-FETCH-009 fix above (code + tests complete, QG-verified standalone earlier, blocked only at re-gate).

## Recommendation

Someone with context on the `sports_trigger_*.py` feature (recently added, per the naming/scope — not part of this
session's DeFi work) needs to either add proper type narrowing at the ~23 flagged sites, or determine if a subset are
false positives worth a targeted `# type: ignore`-equivalent per this repo's own typing conventions (check
`codex/06-coding-standards/` for the sanctioned pattern — raw `# type: ignore` is banned workspace-wide).

## Todos

- [ ] [BACKEND] P1. Fix or properly annotate the ~23 basedpyright errors in `sports_trigger_evaluation.py`,
      `sports_trigger_periodic.py`, `sports_trigger_scheduler.py`, `sports_trigger_state.py` so
      `BASEDPYRIGHT_MAX_ERRORS` drops back to ≤1293. Unblocks all future deployment-service ships, including the
      DP-FETCH-009 fix parked in a working tree pending this (see Progress Log for exact file diffs still sitting
      uncommitted, safe to re-apply).

## Progress Log

- **2026-08-08**: found while shipping an unrelated fix. The DP-FETCH-009 fix itself (code + tests, ~96 lines across 3
  files) is complete and QG-verified in isolation — sitting as an uncommitted local working-tree diff in this repo's
  clone, not lost, just blocked. Once this ratchet clears, re-run `bash scripts/quality-gates.sh` +
  `quickmerge.sh "fix(alerts): DP-FETCH-009 excludes superseded_by_* retirement markers from the attempted_failed alert count" --agent --files 'deployment_service/data_pipeline_monitors/attempted_failed_staleness.py deployment_service/data_pipeline_monitors/meta_watchers.py tests/unit/test_data_pipeline_monitors.py'`.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: considered for RECLASSIFY -- the sole todo (fix ~23
  basedpyright errors in `sports_trigger_{evaluation,periodic,scheduler,state}.py` so the ratchet drops to <=1293) is
  bounded/deterministic on its face. **Conflict-check HELD, not flipped**: an active `assigned_vm: planning` doc in a
  DIFFERENT parent_epic (`plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`, parent_epic
  `sports_master`) shipped a same-repo, same-file-family basedpyright fix in
  `deployment_service/sports_trigger_periodic.py` one week ago (moved the ratchet 1293->1294 via a `reportPrivateUsage`
  fix) and remains AO-dispatchable -- a fresh worker on this doc's todo risks racing that plan's own future edits to the
  identical file family under the same shared repo-wide basedpyright counter. Per the
  ao-dispatch-batch-naming-and-conflict-check.md protocol step 3 ("CONFLICT -- do NOT draft a competing todo... queue it
  for an explicit operator ruling"), staying `assigned_vm: NA` and flagging here rather than guessing which side should
  own the file family.
- **context-scout 2026-08-09**: populated context_scope (4 entries).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:34bffa9113b13578]: KEEP-NA,
valid — The sole open todo is bounded/deterministic ON ITS FACE (fix ~23 named basedpyright errors in 4 named files to
drop a repo-wide error-count ratchet from 1295 to <=1293) -- ordinarily an easy RECLASSIFY shape. However the doc's own
2026-08-08 na-eligibility-audit pass ran the mandatory conflict-check and explicitly HELD it at KEEP-NA: an ACTIVE
assigned_vm: planning doc in a DIFFERENT parent_epic,
plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md (parent_epic sports_master), shipped a
same-repo same-file-family basedpyright fix in sports_trigger_periodic.py one week prior (moved the ratchet 1293->1294
via a reportPrivateUsage fix) and remains AO-dispatchable, creating a real race risk on the SAME shared repo-wide
basedpyright counter/file family.
