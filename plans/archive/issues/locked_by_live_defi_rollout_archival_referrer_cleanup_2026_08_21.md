---
doc_type: issue
title: Residual prose referrers to the archived locked_by-placeholder doc need repointing
summary: >-
  Archiving `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (ARCHIVE_RESOLVED, chunk-3 archival
  pass, 2026-08-21 -- moved to `plans/archive/issues/`) fixed the 4 active-corpus `related:`/`context_scope:`
  frontmatter citations that would have tripped `check_active_refs_archived_plans.py`/`check_reference_paths.py` on
  next touch, but 7 more active-corpus docs still cite the OLD `/plans/active/issues/...` path in PROSE (mostly inside
  an `archive_exempt: true # BRIDGE ...` comment explaining why that OTHER doc is bridged, plus 2 plan_reconciler
  run-journal citations). None of these tripped this session's own commit (the precommit hook only checks staged
  files), but the path is now genuinely dangling and will surface as a new `check_reference_paths` violation the next
  time any of these 7 files is staged for an unrelated edit.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [archival, referrer-sweep, hygiene, locked_by]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
author: agent
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.05
assigned_role: worker
drift_direction: none
resolved_by:
locked_by:
locked_since:
source: "chunk-3 archival-lane pass, 2026-08-21 (this session), while archiving the corpus-wide locked_by-placeholder investigation doc"
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
---

> **🟢 ARCHIVED 2026-08-22** — the only todo `[x]` done (6/7 dangling citations were already repointed by a prior
> session, `unified-trading-pm@68566babc5`; this session repointed the 1 remaining hit in
> `plan_reconciler_findings_ui_2026_08_10.md:201` and re-verified 0 hits corpus-wide under `plans/active` +
> `plans/epics`), unlocked, not `archive_exempt`; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule.

# Residual prose referrers to the archived locked_by-placeholder doc

## What I found

Grep of `plans/active/` + `plans/epics/` for the literal string (written here without its leading slash so this doc's
own body doesn't itself trip `check_reference_paths` on the dangling form it's describing)
`plans` + `/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10` (post-archival, 2026-08-21)
still returns hits in:

1. `plans/active/sports_consolidated_native_ao_extract_2026_07_25.md:51` — `archive_exempt:` bridge comment.
2. `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md:50` — `archive_exempt:` bridge comment.
3. `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md:366` — prose citation in a closed run-journal.
4. `plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md:31,375` —
   `archive_exempt:` bridge comment + a prose mention.
5. `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md:201` — prose citation in a closed run-journal.
6. `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md:26,866` — `archive_exempt:` bridge
   comment (this doc is itself currently NOT archive-eligible per its own 2026-08-19 stale-note) + a prose mention.
7. `plans/archive/issues/pm_scripts_typecheck_debt_2026_06_11.md` (archived 2026-08-21, chunk-6 archival pass) —
   `archive_exempt:` bridge comment + a prose mention, both dropped as part of that archival.

None of these 7 are in my chunk-3 archival batch, and none were staged in the commit that archived the source doc, so
`check_reference_paths.py --only` (staged-files-scoped) did not fire on them this round — but the path they cite no
longer resolves. `plans/epics/security_and_cross_cutting_master.md`'s own `locked_by:` comment (`# was:
live-defi-rollout ... `, filename-only mention of the archived doc, no leading slash) is a bare filename, not a
leading-slash path, and likely does not resolve-check the same way — lower priority, verify when this todo is picked
up.

## Recommended decision

Repoint each of the 7 (bare path substitution: the dangling active-corpus form of the path shown above → its
equivalent under `plans/archive/issues/`) the next time any of them is touched, or in one small dedicated sweep. This
is a same-line path-token substitution (no content change), so it qualifies for the line-cap's bounded-link-repoint
carve-out (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "line-cap does NOT block a bounded
same-line link-repoint") on any of these that are over-cap.

## Todo

- [x] ✅ [SCRIPT] P3. Repoint all 7 dangling citations of the old active-corpus path listed above (`plans` +
      `/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`) to point instead at
      `/plans/archive/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (same-line path-token
      substitution only), then re-verify via a corpus grep for the old active-form path returning 0 hits under
      `plans/active` + `plans/epics`. Also verify the `plans/epics/security_and_cross_cutting_master.md` bare-filename
      comment mention and repoint if it resolves as a checked path. — 6/7 already repointed by a prior session
      (`unified-trading-pm@68566babc5`); this session fixed the 1 remaining hit
      (`plan_reconciler_findings_ui_2026_08_10.md:201`) and re-verified 0 hits corpus-wide.

## Progress Log

- **2026-08-21**: filed during chunk-3 archival-lane processing, discovered as a byproduct of archiving
  `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`. Out of this session's chunk scope (none of
  these 7 files were assigned to this batch), so filed as a tracked follow-up rather than fixed inline.
- **2026-08-22**: re-verified via a fresh corpus grep — 6 of the original 7 dangling citations were already
  repointed by an earlier session (`unified-trading-pm@68566babc5`, "fix(plans): repoint dangling active-corpus
  refs at now-archived docs..."): items 1/2/3/6 (`sports_consolidated_native_ao_extract`,
  `sports_satellite_ao_dispatch_batch5`, `plan_reconciler_findings_all`, `tradfi_canonical_path_migration_design`)
  now correctly cite `/plans/archive/issues/...`; item 4 (`features_universe_filter_settlement_suffix_and_vm_tarball_staleness`)
  was itself archived and its citation moved+fixed with it; item 7 (`pm_scripts_typecheck_debt`) was itself archived
  2026-08-21 (chunk-6), so it's out of the `plans/active`+`plans/epics` re-verification scope regardless of its
  internal content. Fixed the 1 remaining genuine hit: `plan_reconciler_findings_ui_2026_08_10.md:201` (same-line
  `active`→`archive` token substitution only, no other content change). Verified the
  `plans/epics/security_and_cross_cutting_master.md` bare-filename `locked_by:` comment mention: it names the doc
  with no path prefix at all (not `/plans/...` or `/codex/...` leading-slash form), so it does not resolve as a
  `check_reference_paths.py`-checked path — no repoint needed. Re-ran the corpus grep scoped to
  `plans/active/**.md` + `plans/epics/**.md`: 0 remaining hits of the old active-form path (the only 2 residual
  matches are inside this doc's own `## What I found`/`## Todo` prose describing the search pattern itself,
  deliberately written without a leading slash so it doesn't trip the checker — not live references). Todo done,
  0 open todos, no lock — archiving per the 6-step ritual (single-repo same-commit flip+archival, sanctioned for
  `doc_type: issue` docs per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).
