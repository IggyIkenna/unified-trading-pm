---
doc_type: issue
title: Plan-reconciler run findings — sports tranche — 2026-08-09
summary:
  Run-findings journal for the plan_reconciler agent's sharded reconciliation pass over the sports topic tranche
  (asset_group sports), dispatch agt-8da8df, slot 14, 2026-08-09.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, sports, findings]
related: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-08-09"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
author: plan_reconciler
source: agt-8da8df
resolved_by:
locked_by: plan_reconciler (agt-8da8df) since 2026-08-09T16:15:00Z
---

# Plan-reconciler run findings — sports tranche — 2026-08-09

Dispatch `agt-8da8df`, slot 14. Sharded run scoped to `asset_group: sports` docs under `plans/active/` (+ `issues/`),
per `cursor-configs/skills/plan-reconcile/SKILL.md` § "Topic-scoped (sharded) runs" and `agents/plan_reconciler.md`.

**Corpus**: 92 sports-tagged active docs. **Grace-window (12h, read-only-context)**: 60 docs — an unusually high
fraction, reflecting heavy same-day fleet activity across sports batch9-12 AO dispatches + taxonomy P1-P4 today.
**Eligible for write this run**: 32 non-grace docs.

## Flips verified

(none yet)

## Contradictions

(none yet)

## Doc-drift

(none yet)

## Hygiene fixes

1. `sports_index_recency_masked_captured_atoms_2026_07_13.md` — softened an unsourced "operator ruling" citation
   (`check_plan_operator_ruling_evidence` gate) to a factual restatement (branch never fired, contingency not exercised)
   since no traceable source doc could be found; substance unchanged.
2. Re-normalized `locked_by: ""` (literal quoted-empty-string) → truly-blank `locked_by:` on
   `sports_index_recency_masked_captured_atoms_2026_07_13.md` — confirms the resurrection (see Archive candidates)
   reverted the FULL effect of `ad137ae4e`+`f44dfadd4`, not just the archive `git mv`: this exact normalization was
   `ad137ae4e`'s entire content, and its absence is what made `check-locked-plan-deletion.sh` block this run's archival
   commit (naive `grep -oP` parser reads `""` as a non-empty locked-by value). Also found + fixed the SAME pre-existing
   pattern in `sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md` (already-archived,
   touched here only for its referrer-path fix) — 2 instances this run, on top of the 6 the 2026-08-08 run already
   normalized fleet-wide.
3. 8 dangling `/plans/active/...` referrer paths repointed to their current `/plans/archive/...` locations across
   `sports_consolidated_closeout_aggregated_sources_2026_07_24.md` (6) and
   `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (2) — all 8 targets had simply moved, confirmed via direct lookup
   before repointing.
4. Softened 4 more pre-existing unsourced "operator ruling"/"OPERATOR RULING" citations (all independently
   sha/evidence-backed) in `sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md` (3) and
   `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (1) — same fix class as item 1, forced into scope by touching
   those files for their referrer-path fix (the `--only` staged-file gate is unconditional, not baseline-exempt).

## Filed

1. `plan_archive_resurrected_by_concurrent_merge_2026_08_09.md` — process-integrity finding (below).

## Archive candidates (operator review)

1. **`sports_index_recency_masked_captured_atoms_2026_07_13.md`** — ARCHIVED this run (unlocked, all 7 todos
   HARD-verified done: fresh live grep-then-READ confirmed the guard code present at instruments-service HEAD,
   converging with the doc's own independent 2026-08-05 fleet-wide re-verification). `status: open` → `resolved`;
   `git mv` → `plans/archive/2026_08/`; 4 stale leading-slash referrers repointed
   (`sports_satellite_ao_dispatch_batch2_2026_07_24.md`,
   `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`,
   `sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md`,
   `sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`). **Notable: this is a RE-archival.**
   `unified-trading-pm@f44dfadd4` (2026-08-08 01:02:55Z, slot-11, `agt-2add8d`) already archived this exact doc once,
   with an identical evidence basis — but by the time of this run the doc was back at its original active path with
   pre-archive content (`status: open`), and NO trace of `f44dfadd4` or its preceding `ad137ae4e` (locked_by
   normalization) appears in `git log -- <active path>`. A sibling doc archived by the SAME commit
   (`dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`, not sports-tranche) shows the identical pattern
   — also back at its active path, not touched here (outside scope). Root cause not fully diagnosed (would need
   bisecting the merge/rebase history around 2026-08-08–09 across the fleet's concurrent quickmerge activity) — filed as
   `plans/active/issues/plan_archive_resurrected_by_concurrent_merge_2026_08_09.md` for the workspace
   git/quickmerge-process owner; NOTIFYING OPERATOR per the cross-repo/SSOT-integrity big-finding triage rule, since a
   durable archival action being silently undone by concurrent merge activity is a correctness concern for the archival
   ritual fleet-wide, not sports-specific.

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(none yet)

## Plans not reached

(none yet)
