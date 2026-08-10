---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — sports tranche, 2026-08-10"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-8005f6 (slot 19, 2026-08-10), tranche=sports. Corpus: 101
  asset_group:sports-tagged docs in plans/active + plans/active/issues (37 active plans + 60 issue docs, plus 4
  filename-sports_*-but-multiline-array docs already counted, ~3.7MB). 57 (56%) are in the 12h grace window and
  read-only this run, leaving 44 non-grace docs (~1.9MB) as the actionable set, plus the normative refs (PLAN_FORMAT.md
  / task_template.md / INDEX.md / ACTIVE_INDEX.md) and codex which stay in scope for every shard per
  cursor-configs/skills/plan-reconcile/SKILL.md.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, sports]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-08-10"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-10"
supersedes:
superseded_by:
resolved_by:
source: "slot 19, plan_reconciler agt-8005f6, 2026-08-10"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-10 (agt-8005f6, sports tranche)

## Scope + method

- `TRANCHE=sports` supplied → sharded per-tranche run (one of a wave of sibling tranche workers this cadence).
- Corpus: `asset_group: sports`-tagged docs across `plans/active/*.md` (37) + `plans/active/issues/*.md` (60) = 101 docs
  (multi-line `asset_group:` arrays included via a `\n`-aware grep — 4 docs would have been missed by a single-line
  pattern), ~3.7MB. One filename-`sports_*` doc (`sports_prediction_mvp_writetime_precompute_2026_07_24.md`) is
  genuinely tagged `[cross-cutting]`, not sports — excluded correctly.
- Grace set (newest commit <12h old at run start): 57 of 101 docs (56%). Read-only context this run — the sports AG is
  under heavy concurrent activity right now.
- Non-grace actionable set: 44 docs.
- Normative refs (`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`, `ACTIVE_INDEX.md`) + codex stay in scope per the
  skill's sharded-run rules.
- Archival caution: before archiving anything, grep the other 9 tranches' consolidated-closeout docs for
  cross-references (`/plan-reconcile` SKILL.md § "Archival caution in a topic-scoped run").
- **Cross-tranche handoffs picked up from sibling runs' findings docs** (2026-08-06 through 2026-08-09): the cefi
  (`plan_reconciler_findings_cefi_2026_08_09.md`) and tradfi (`plan_reconciler_findings_tradfi_2026_08_09.md`) runs both
  flagged `sports_odds_feature_naming_canonicalization_2026_07_21.md` and
  `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` as archive candidates outside their shard. Both are
  GRACE-protected this run (last touched ~3-4h before this run started) — noted, not actioned.
  `sports_index_recency_masked_captured_atoms_2026_07_13.md` (flagged done-but-unarchived by the 2026-08-08 `all` run)
  and the `sports_closeout_track_s2_foldin_2026_07_25.md` VM-completion review todo are likewise GRACE-protected now.

## Flips verified

(none yet)

## Archived (verified-done, unlocked, non-grace)

(none yet)

## Contradictions

(none yet)

## Doc-drift

(none yet)

## Hygiene fixes

(none yet)

## Codex corrections applied (mechanical, evidence-cited)

(none yet)

## Filed

1. **`regenerate_active_plan_index.py` frontmatter parser silently drops docs with a commented multi-line `asset_group:`
   array** — root-caused and reproduced live (not inferred): `parse_frontmatter()`'s block-scalar continuation-line
   consumption (`scripts/plans/regenerate_active_plan_index.py:80-88`) only skips a continuation line that is LITERALLY
   `[` or `]`; a line like `  [sports] # corrected 2026-07-25 (... ), a genuine mistag: ...` (a legitimate, encouraged
   corpus style — the `/ag-closeout-audit` retag convention itself uses inline `#` comments to explain a correction)
   gets appended verbatim, comment text included, into the raw `asset_group` value. Then `parse_asset_groups()`'s naive
   `raw.strip("[]"); raw.split(",")` shatters that comment prose on its OWN internal commas into 5 garbage tokens
   (verified:
   `['sports] # corrected 2026-07-25 (... fix) -- was [cross-cutting]', 'a genuine mistag: # 100% sports-specific (FixturesBrowser.tsx', 'fixtures_browser.py', 'sports fixture catalogue)', 'no cross-AG mechanism']`),
   none of which equal `sports` — so the doc silently lands in neither its correct domain section NOR "uncategorized"
   (the raw value wasn't empty), it just vanishes. Confirmed live via
   `python3 -c "... parse_frontmatter(...); parse_asset_groups(...)"` against
   `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`. This is WHY re-running the regenerator this run did
   NOT add either of the 2 sports docs flagged by the cefi/tradfi sibling runs' `INDEX.md` drift check (see Scope above)
   — it's not a staleness problem, it's a parser bug, so a plain regen (which I ran, verified via a post-regen `grep`
   returning 0 hits for both docs, then reverted since it doesn't fix the sports gap and touches all 10 domains) cannot
   fix it. **Not sports-isolated**: the same `raw.strip("[]"); raw.split(",")` pattern (grepped) also appears in
   `check_priority_tier_policy.py` and `count_operator_blocking_todos.py` — unverified whether those two share the exact
   same continuation-comment bug, but worth auditing together. **A correct pattern already exists in this same corpus**
   to fix from: `check_na_corpus_ratchet.py` and `scripts/docs/docspec.py` both use a real `import yaml` parser instead
   of the hand-rolled one, which is presumably why the NA-corpus-ratchet check did NOT mis-parse this doc's
   `asset_group`. Outside `plans/**` (my role's hard limit), so filed rather than fixed. Suggested fix: either switch
   `regenerate_active_plan_index.py` (and the other 2 scripts, if confirmed affected) to `docspec.py`'s
   `parse_frontmatter`, or apply the same `re.sub(r"\s+#.*$", "", val).strip()` trailing-comment strip already used for
   single-line scalars (line ~89) to each continuation line before appending it in the block-scalar branch.
   - [x] ✅ [SCRIPT] P2. Fix `regenerate_active_plan_index.py`'s frontmatter parser (and audit
         `check_priority_tier_policy.py` + `count_operator_blocking_todos.py` for the same bug) —
         unified-trading-pm@0edf5bf2ee. Fix: strip trailing `# comment` from each block-scalar continuation line
         (mirroring the existing single-line scalar treatment at line 98), skip standalone `#` comment lines entirely.
         12 unit tests (`tests/unit/test_regenerate_active_plan_index.py`) cover commented-continuation, multi-group,
         standalone-comment, and regression cases. Dry-run verified: the 2 plan-type affected docs
         (`sports_fixtures_browser_single_catalogue_source_2026_07_24.md`,
         `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`) now appear in regenerated INDEX.md under sports
         (previously vanished). The 2 issue-type docs
         (`sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`,
         `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`) aren't indexed by design (`doc_type: issue`
         excluded from INDEX.md). **Audit**: `check_priority_tier_policy.py` and `count_operator_blocking_todos.py` do
         NOT share the exact continuation-comment bug (their `_parse_frontmatter()` doesn't consume block scalars), but
         both carry the same fragile `strip('[]').split(',')` pattern — a single-line
         `asset_group: [sports] # was: cross-cutting` would produce a garbage group token. Lower severity
         (miscategorized vs vanished). Left unfixed per task scope (audit only).

## Archive candidates (operator review)

(none yet)

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(in progress)

## Plans not reached

(none yet)

## Progress Log

- 2026-08-10: Run started. Inherited + shipped dead WIP found in slot 19 on boot (unrelated prior `prediction`-tranche
  archival, `046ff3cb0` — see that commit). STEP 1 (repo sync across all 25 sibling repos; `alerting-service` showed a
  transient not-FF-clean WARN that resolved on immediate re-check, no action needed) + STEP 2/2b (grace set + findings
  doc) complete.
- 2026-08-10: `run_hygiene_sweep.sh --ci` completed corpus-wide: 2 hard failures, 1 soft warning. Both hard failures
  verified OUTSIDE the sports tranche and out of a single shard's scope to fix: (1) **prosewrap continuation-padding
  ratchet** — 4710 violating lines vs baseline 4472 (+238), spread across `plans/`, `codex/`, and multiple SERVICE repos
  (e.g. `market_tick_data_service/scripts/*`, `ml_service/*`, `strategy_service/*`) — a pre-existing, slowly-growing
  corpus-wide metric tracked by `plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`,
  not sports-specific and far too large (238 new lines across many repos) for a single tranche shard to remediate; (2)
  **assigned_vm:NA corpus size ratchet** — FAILED inside the full `--ci` sweep (379/1093 vs baseline tolerance) but
  PASSED when the same checker (`check_na_corpus_ratchet.py`) was re-run standalone moments later (379 docs / 1093
  todos, within the 372+10 / 1109+30 tolerance) — almost certainly a transient read against a moving target under high
  fleet-wide concurrent-commit load, not a real regression; not sports-specific either way. Discarded the `--ci` regen
  side-effect on `plans/active/INDEX.md` + `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (the
  named grace-window target from the STEP-1 instructions, `master_to_live_defi_2026_05_23.md`, has since been archived
  itself, so the regen now lands on these two files instead — same discard-the-side-effect intent). INDEX.md drift: 33
  docs corpus-wide missing from INDEX.md, 2 of them sports
  (`sports_fixtures_browser_single_catalogue_source_2026_07_24.md`,
  `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`) — queued as a STEP-5 mechanical hygiene fix (regenerate
  INDEX.md; it's a normative ref, in scope for every shard).
- 2026-08-10: Sports corpus inventory built (101 docs, size/mtime/status/parent_epic), partitioned into 8 size-balanced
  epic-cluster hunter batches (~400-500KB / 12-13 docs each). Proceeding to STEP 3 hunter fan-out.
- 2026-08-10: STEP 3 launched — 8 parallel read-only epic-cluster hunters (sonnet, one per batch) fanned out over all
  101 docs. While awaiting results, investigated the 2 sports INDEX.md-drift entries directly (mechanical, no hunter
  needed): root-caused + reproduced a genuine parser bug in `regenerate_active_plan_index.py` (see `## Filed` #1) — ran
  the regenerator, confirmed via live repro it does NOT add either flagged sports doc (comment-swallowing bug in the
  hand-rolled frontmatter parser, not staleness), then reverted the partial 10-domain-wide regen from the working tree
  rather than commit an out-of-sports-scope diff that doesn't even fix the thing it was run for. Filed as a
  `[SCRIPT] P2` todo (outside `plans/**`, outside this role's write scope) with full repro + suggested fix.
- 2026-08-10 (slot-18): shipped the fix for `[SCRIPT] P2` — stripped trailing `# comment` from block-scalar continuation
  lines in `parse_frontmatter()`, skip standalone `#` comment lines. 12 unit tests pass. Dry-run verified the 2
  plan-type affected docs now appear in regenerated INDEX.md under sports. Audited the other 2 scripts: neither shares
  the exact continuation-comment bug (their `_parse_frontmatter` doesn't consume block scalars), but both carry the same
  fragile `strip('[]').split(',')` in their `_asset_groups`/raw-value parsing — left unfixed per task scope. Shipped
  unified-trading-pm@0edf5bf2ee.
