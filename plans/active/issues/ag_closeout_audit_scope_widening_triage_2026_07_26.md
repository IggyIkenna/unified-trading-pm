---
doc_type: issue
title: /ag-closeout-audit scope gap — asset_group infrastructure/meta docs invisible to all 9 tranches
summary: >-
  The 9-tranche partition (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra) only ever sweeps `asset_group:
  cross-cutting` (plus the 5 AGs) when building tranche membership, but `plans/PLAN_FORMAT.md:88` also declares
  `infrastructure` and `meta` as valid `asset_group` enum values — sweeping those 2 additional values returns ~48
  unlisted active docs, so the partition's stated "total coverage of the plans/issues corpus" claim was false by ~48
  docs. Resolved as `autonomous_session_operator_decisions_2026_07_25.md` entry #32 (option A): the SKILL.md fix (widen
  `all` mode + every tranche's membership rule to also sweep `infrastructure`/`meta`) already landed; this doc tracks
  the remaining corpus-wide triage of the ~48-doc delta the widened rule now surfaces. 4 of the ~48 (all
  ci-tranche-relevant) were already found and given a live home by the ci-tranche's own 2026-07-26 audit pass — see
  `ci_consolidated_closeout_2026_07_25.md`'s Progress Log for that subset; the remainder is unmeasured.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, scope-gap, plan-hygiene, asset-group, triage]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
priority: P2
locked_by:
resolved_by:
source: >-
  ci tranche audit (2026-07-26), Phase-3 conflict-check — "four tranche members listed in NO consolidated closeout at
  all, found by sweeping beyond asset_group: cross-cutting." Generalized to all 9 tranches, resolved as
  autonomous_session_operator_decisions_2026_07_25.md entry #32.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# /ag-closeout-audit scope widening — triage the ~48-doc delta

## What's already done

- [x] [DOC] P2. Widen `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s membership rule so `all` mode (and every
      single-tranche run) also sweeps `asset_group: infrastructure` and `asset_group: meta`, not just `cross-cutting` +
      the 5 AGs. ✅ DONE 2026-07-26.
- [x] [REVIEW] P2. 4 of the ~48 docs (ci-tranche-relevant, found by the ci tranche's own 2026-07-26 audit sweeping
      beyond `cross-cutting`) already triaged and given a live home:
      `issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` +
      `issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` (both `[meta]`) cited as
      `Source:`/Deferred-table entries in `ci_satellite_ao_dispatch_batch1_2026_07_26.md`;
      `issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` +
      `issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md` (both `[infrastructure]`) already
      `assigned_vm: planning` and actively dispatched. See `ci_consolidated_closeout_2026_07_25.md`'s Progress Log for
      the full note.

## Todos

- [ ] [REVIEW] P2. **Run the corpus-wide sweep for the remaining delta**:
      `rg -l '^asset_group:.*\[.*infrastructure' plans/active` and the equivalent for `meta`, minus the 4
      already-triaged docs above, minus anything already covered by an existing tranche's Sources list under its
      epic-based membership rule. **Done when**: every remaining doc in the delta is classified into exactly one of the
      9 tranches (or explicitly ruled genuinely out-of-scope, with why), with the classification recorded either here or
      in the receiving tranche's own consolidated-closeout doc.
- [ ] [DOC] P3. Once the delta is fully classified, add a corpus-wide regression check (or extend
      `check_ag_closeout_linkage.py`, which does not currently catch this class) so a future doc tagged
      `infrastructure`/`meta` cannot silently re-accumulate outside every tranche's membership sweep.
