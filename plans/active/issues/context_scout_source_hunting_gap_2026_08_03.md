---
doc_type: issue
title:
  "`/context-scout` Phase 1's own spec-mandated source-hunting (root-cause sections + error messages are its stated
  'highest-yield spots') did not fire on a doc whose P2 todo names exactly that kind of content -- confirmed on a live
  repro, not measured on a corpus sample"
summary:
  "Investigating why session context blows past 200k despite `context_scope` being populated, I traced a concrete repro:
  `/plans/active/issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md`'s P2 todo
  (added 2026-07-31, commit ce22ca1d0) is a root-cause investigation naming specific concepts in prose --
  `weekend`/`holiday`, `venue_trading_calendar`/`EXPECTED_WEEKEND` marker, `DEPENDENCY CHECK FAILED` -- across two named
  repos (market-tick-data-service, market-data-processing-service). `cursor-configs/skills/context-scout/ SKILL.md`
  Phase 1 step 4 states root-cause sections and error messages are the highest-yield spots for source-path hunting, and
  that a codex-only `context_scope` on a doc with real code substance 'should be treated as an unfinished Phase-1 pass,
  not an acceptable minimal result.' The actual context-scout pass on this doc ran 2026-08-01 (commit cd4b6bc9e,
  'context-scout backfill batch 7') -- AFTER the P2 todo already existed -- and wrote exactly 3 entries, all codex/plan
  docs, zero source paths. Cold-grepping the same two repos for the todo's own named symbols
  (`weekend|holiday|trading_calendar|EXPECTED_WEEKEND` in MTDS, `dependency_checker` in MDPS) surfaces 25 candidate
  files (579,376 chars / ~145k tokens if read blind); even a disciplined top-4-by-name triage is ~92k chars / ~23k
  tokens -- a cost the P2 todo's own picker-up now pays cold, which `context_scope` exists specifically to avoid. This
  is not a novel failure mode -- SKILL.md's own Phase-1 write-up cites a 2026-07-30 corpus spot-check finding only 51%
  of already-scouted docs carried a real source path -- but this is a fresh, reproducible instance from AFTER that
  measurement/spec tightening, on a doc whose content is a textbook match for the stated hunting criteria. Separately
  (unconfirmed, flagged for the audit todo below, not asserted): this doc's git-last-commit date moved to 2026-08-02 via
  a same-day mechanical hygiene commit (17b53df1e, 'fix(plan-hygiene): resolve plan_health gate... fix reference-path
  drift') that likely did not touch doc substance -- worth checking whether `generate_context_scope_inventory.py`'s
  STALE/UP_TO_DATE heuristic (marker date vs. `last_updated`-or-git-commit-date) can be fooled into UP_TO_DATE by a
  content-irrelevant mechanical commit bumping the fallback date, independent of the Phase-1 miss confirmed above."
status: open
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [context-scope, context-scout, plan-hygiene, tooling, agent-context-cost, mvi, source-path-hunting]
related:
  [
    /plans/active/issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md,
    /plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-08-03
parent_epic: agent_operating_framework_master
source:
  "Surfaced in an interactive session on 2026-08-03 explaining to the operator why session context exceeds 200k despite
  a doc's context_scope being populated; traced to a concrete Phase-1 source-hunting miss rather than a structural
  limitation of the context_scope field (which does carry source paths correctly elsewhere in the corpus -- confirmed
  via corpus grep, dozens of other docs have `.py` entries)."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
assigned_role: docs_reconciler
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
context_scope:
  [
    /plans/active/issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md,
    cursor-configs/skills/context-scout/SKILL.md,
    scripts/plan-hygiene/generate_context_scope_inventory.py,
  ]
priority: P2
---

## What I found

`generate_context_scope_inventory.py` is a pure eligibility classifier -- it parses frontmatter, compares a
`context-scout YYYY-MM-DD` Progress Log marker date against the doc's last-touched date, and buckets NEVER_SCOUTED /
STALE / UP_TO_DATE. It does zero content grepping and never reads todo text; it cannot be the thing that decides _what_
goes into `context_scope`. That decision is entirely inside the Phase 1 sub-agent process SKILL.md describes: read the
doc's body, extract cited codex/plan paths (free), then "actively hunt" named filenames/scripts/classes/modules in prose
-- explicitly calling out root-cause sections and error messages as the highest-yield spots -- and grep the named repo
if nothing is named explicitly.

The `tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md` P2 todo is exactly that shape: it
names a marker concept (`venue_trading_calendar`/`EXPECTED_WEEKEND`), an error string (`DEPENDENCY CHECK FAILED`), a
specific check module (`market_data_processing_service.app.core.dependency_checker`), and two repos by name. Per
SKILL.md's own bar, this should have been a "near-automatic include" once verified to exist. It wasn't included -- the
doc's `context_scope` has 3 entries, all codex/plan docs (`infrastructure_master.md`, `honest-coverage-model.md`, one
archived issue), zero source paths -- despite the 2026-08-01 scout pass running after the P2 todo already existed in the
doc body.

I confirmed the candidates ARE cheaply discoverable: `rg -il 'weekend|holiday|trading_calendar|EXPECTED_WEEKEND'`
against market-tick-data-service surfaces 15 files; `rg -il 'dependency_checker'` against market-data-processing-service
surfaces 10. Among them, `market_data_processing_service/app/core/ dependency_checker.py` and
`market_tick_data_service/scripts/reclass_per_instrument_weekend_holiday_eu.py` are exactly the kind of "obvious entry
point" SKILL.md Phase 1 step 4 asks a hunter to grep for when nothing is named literally -- and here something WAS named
literally (`dependency_checker`), which should have made this even more automatic than the fallback case.

This confirms `context_scope` is not structurally code-blind (dozens of other corpus docs carry `.py` entries fine) --
this is a Phase-1 execution miss on a doc that should have been a clean hit, consistent with SKILL.md's own
self-reported 51% source-path-coverage baseline (2026-07-30) not having meaningfully improved by the very next scouting
pass on this doc (2026-08-01).

## Why it matters

`context_scope` exists to cut a worker's cold-start cost. When Phase 1 misses on a doc whose todo requires reading two
services' source to root-cause, the worker who picks up that todo pays the full cold-grep cost anyway -- measured here
at ~145k tokens if the 25 grep-surfaced candidates are read blind, ~23k tokens even with disciplined triage to the 4
most name-plausible files -- stacked on top of ~72k tokens already spent on this doc's doc-level `context_scope` +
CLAUDE.md + directly-relevant-but-unlisted codex docs. That's most of a 200k context budget spent before the actual fix
is attempted, for exactly the class of todo (open investigation, root-cause unknown) where `context_scope` is supposed
to matter most.

## Todos

- [ ] [SCRIPT] P2. Manually run `/context-scout` Phase 1 against
      `/plans/active/issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md` and confirm
      it now surfaces `market_data_processing_service/app/core/dependency_checker.py` and/or
      `market_tick_data_service/scripts/reclass_per_instrument_weekend_holiday_eu.py` (or the actual correct
      weekend-marker-write module, once identified) as source-path entries. This is a live demonstration the fix works
      on the exact repro case, not a theoretical claim.
- [ ] [SCRIPT] P2. Spot-check a fresh sample (20-30 docs scouted since 2026-08-01, after the SKILL.md spec revision that
      added the "near-automatic include" / "unfinished Phase-1 pass" language) for real source-path presence, the same
      way the 2026-07-30 342-doc baseline was measured. Report whether the rate improved from 51% or is still flat --
      this determines whether the SKILL.md spec tightening actually changed sub-agent behavior or the miss found here is
      representative of an ongoing gap.
- [ ] [SCRIPT] P3. Add a cheap deterministic post-hoc lint to Phase 3's report (not a blocker, a surfaced warning): for
      each doc scouted with zero source-path entries, check whether the doc body contains any token matching a known
      filename/module pattern (e.g. `\w+_service\b`, `\.py\b`, a `repos:` frontmatter repo name followed by a path-like
      token) that doesn't appear anywhere in the written `context_scope`. Flag those in the Phase 3 report for human
      spot-check, since Phase 1's hunting is pure agent judgment with no other check that it actually ran as specified.
- [ ] [SCRIPT] P3. Verify whether `generate_context_scope_inventory.py`'s STALE/UP_TO_DATE fallback (git last-commit
      date, when frontmatter `last_updated` is absent) can produce a false UP_TO_DATE when a content-irrelevant
      mechanical commit (e.g. a corpus-wide hygiene/reference-path-fix sweep) bumps a doc's git last-commit date past
      its last real context-scout marker. If confirmed, the fix is comparing against the latest commit that touched doc
      BODY content (via `git log -p` diff classification, or excluding known hygiene-sweep commit patterns) rather than
      any commit touching the file at all.

## Progress Log

- **na-eligibility-audit 2026-08-03** (ao tranche): RECLASSIFY, conflict-check CLEAR — flipped
  `assigned_vm: NA -> planning`, `execution_scope: local-only -> orchestrator-agent`. All 4 open items are bounded,
  mechanically-checkable audit/tooling tasks against plan-hygiene scripts (`generate_context_scope_inventory.py`) or a
  scripted live-demo verification run against one named repro doc — no undecided design/judgment call, no
  live-dispatch-critical orchestrator code touched, no BLOCKED-OPERATOR banner or `depends_on` gate anywhere in the doc.
  Conflict-check (3 surfaces): (a) no open todo in any active `assigned_vm: planning` doc in
  `parent_epic: agent_operating_framework_master` claims this same ground (checked all 9 —
  `context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` is the closest topical neighbor but covers
  line-cap/locked-doc mechanics, not Phase-1 source-hunting accuracy; two topically-adjacent NA docs,
  `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`'s backfill-coverage todo and
  `context_scope_consumption_enforcement_2026_07_30.md`'s consumption-enforcement todo, are both different claims — "is
  it scouted at all" / "is it read once scouted" vs. this doc's "did scouting find the right paths"); (b) no sibling
  batch/finalize doc drafted earlier in this run; (c) the ao consolidated-closeout doc
  (`ao_open_issues_consolidated_close_out_2026_07_17.md`) does not touch this topic. Frontmatter already carried
  `assigned_role: docs_reconciler` + `model_tier: sonnet-doable`, no correction needed. Companion finalize plan:
  `context_scout_source_hunting_gap_2026_08_03_finalize_2026_08_03.md`.
