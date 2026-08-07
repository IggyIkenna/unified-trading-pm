---
doc_type: issue
title: Plan-reconciler findings — sports tranche (2026-08-07)
summary:
  Daily plan_reconciler run over the sports tranche (agt-cf1afa). 81 docs total (28 grace/read-only, 53 scannable). 1
  archive, 5 zero-checkbox conversions (3 docs), 6 contradictions found (all P2/P3), 2 codex drift items, 1 stale-locked
  doc routed.
status: open
nature: issue
asset_group: sports
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, sports, reconciliation, daily-run]
related: []
created: 2026-08-07
author: plan_reconciler
source: agt-cf1afa
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
locked_by:
resolved_by:
---

**Dispatch ID:** `agt-cf1afa` **Tranche:** sports **Run date:** 2026-08-07 **Review branch:**
`plan_reconciler/agt-cf1afa` **Result:** 5 commits, 1 archive, 5 todos converted, 6 contradictions + 2 codex drift
routed

---

## Flips verified

- ❌ **REFUTED**: `sports_group_c_execution_backtest_harness_2026_07_21.md:77` —
  `- [ ] [BACKEND] P3. Wire a data source: reuse Group-B fixture shipped in strategy-service@9a7de7f8`. Commit
  `9a7de7f8` IS reachable on LDR (fixture `tests/fixtures/sports_odds/premier_league_arb_sample.py` exists), but the
  todo's OWN work (wiring into execution-service: `run_sports_backtest`, `extract_sports_instrument`) has zero evidence
  in execution-service. Commit is the source dataset (prerequisite), not completion. Checkbox correctly open.

## Contradictions

All P2/P3, within sports consolidated closeout and child docs:

- **C1 (P2)**: `sports_consolidated_closeout_2026_07_19.md` internally contradicts on legacy bare `entity=fixtures/`
  write status — "FROZEN (last real write 2026-05-23)" vs Track S "write path still active today." 2026-08-04 resolution
  covers reads only; write-side unresolved, Track S todo open.
- **C2 (P2)**: Same doc's Canonical-target narrative still says "NOT YET EXECUTED" while Track C todos show all 3 steps
  executed + verified 2026-07-27/28 (registry, writers, 345,852-object data migration). Stale SSOT-section state.
- **C3 (P2)**: 6-venue unregistered lowercase `odds`/`trades` duplicate cleanup fold-in never materialized — closeout
  says "folded into Track V delete todo at line ~698," but Track V covers raw-keyed `league_id` objects (different
  population); line ~698 is now a Track H DIAG todo; fork plan only recorded it as an addendum on a now-flipped todo. No
  issue doc owns the delete.
- **C4 (P2, acknowledged)**: Catalog league-grain plan's fixture-grain redesign collides with closeout's canonical
  split-entity design. Both docs carry reciprocal cross-link banners — known but unresolved.
- **C5 (P3)**: Catalog plan claims sports captured manifest atom is "venue-blank at league grain" vs codex
  `availability-manifest-and-data-status.md:53` stating sports shard atom includes `venue/source`. Possibly different
  surfaces.
- **C6 (P3)**: Closeout's open venue-cleanup todo still lists LADBROKES_UK/SPORT888/FOOTYSTATS re-stamps as open, but
  native AO extract flipped its re-stamp todo `[x]` with census-verified completion. Parent rollup partially stale —
  double-execution risk.
- **C7 (P3)**: Same 6-venue duplicate population attributed to different root causes (closeout: "unrelated earlier fork"
  vs fork plan: "K1/K2 UPPER-casing migration residue").

## Doc-drift (codex)

- **D1 (P3)**: `sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md` cites
  `/codex/11-project-management/plan-completion-and-archival-discipline.md` — file lives at
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. (GRACE doc — noted, not fixed.)
- **D2 (P3)**: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` cites
  `/codex/02-data/sports-canonical-league-cup-registry.md` — "New:" proposal never created, 6 weeks stale, no tracking
  todo. (LOCKED doc — noted, not fixed.)

## Hygiene fixes

- **Zero-checkbox conversions** (3 docs, 5 todos added):
  - `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` — added 2 `[DATA]` P1/P2 todos for the
    CEFI/SPORTS shard-enumeration fix + verification.
  - `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` — converted the 3 prose "Suggested
    follow-up" items to `[INFRA]` P1/P1/P2 checkbox todos (diagnose kill, check reaper policy, install pkill-guard
    host-wide).
  - `sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md` — added `[OPERATOR]` P1 (A/B
    ruling) + `[DATA]` P2 (execute ruling) todos for the 5-day-unanswered escalation.

## Filed

- **Stale-locked doc**: `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` — status=superseded,
  `locked_by=live-defi-rollout` with `locked_since 2026-05-21` predating the doc's 2026-07-30 creation (demonstrably
  stale lock). Duplicate of archived `instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`.
  Ready-to-archive but needs `[unlock-plan]` from operator.
- **6 contradictions** above are filed in this doc for operator review — all are within the sports consolidated closeout
  ecosystem and need the closeout owner to resolve.
- **2 codex drift** items above — D1 is in a grace doc (batch10 finalize), D2 is in a locked doc (universe expansion).

## Archive candidates (operator review)

- ✅ **ARCHIVED**: `sports_index_recency_masked_captured_atoms_2026_07_13.md` → `plans/archive/2026_08/` — 7/7 todos
  done with evidence, `locked_by: ""` (seed artifact) cleared, `status: resolved`. All cross-tranche references are to
  archive docs only.
- 🔒 **LOCKED**: `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` — superseded duplicate, ready
  to archive but `locked_by: live-defi-rollout` with stale pre-creation lock date. Operator `[unlock-plan]` needed.

## Refuted (dropped by verify)

- `sports_group_c_execution_backtest_harness_2026_07_21.md:77` — commit `9a7de7f8` is a prerequisite (fixture shipped in
  strategy-service), not completion evidence for the wiring task in execution-service. Half-flip committed then
  reverted. Checkbox correctly open.

## Coverage (hunters / batches / docs)

- **Tranche:** sports
- **Total docs:** 81 (28 plans + 53 issues)
- **Grace set (read-only):** 28
- **Scannable:** 53
- **Hunters launched:** 3 (archive-candidates, zero-checkbox, contradictions+missed-flips)
- **Hunters completed:** 3
- **Verified confirmed:** 8 (1 archive + 5 todo conversions + 1 stale-lock route + 1 revert)
- **Verified refuted:** 1 (missed flip)
- **Plus normative refs:** PLAN_FORMAT.md, task_template.md, INDEX.md, ACTIVE_INDEX.md
- **Plus codex:** corpus-wide (read-only for drift detection)

## Plans not reached

(none — all 53 scannable non-grace sports docs were scanned)

---

## Progress Log

- **2026-08-07 00:01**: Run started. STEP 0-2 complete. Created review branch `plan_reconciler/agt-cf1afa`.
- **2026-08-07 00:15**: STEP 3 — 3 hunters launched (archive-candidates, zero-checkbox, contradictions+missed-flips).
  Mechanical scans ran (hedge pointers clean, moved-doc referrers found, codex SSOT sections absent).
- **2026-08-07 00:25**: All hunters complete. Archive-candidate hunter: 1 of 6 truly archive-ready. Zero-checkbox
  hunter: 3 docs need todo conversion. Contradiction hunter: missed flip REFUTED, 6 contradictions + 2 codex drift
  found.
- **2026-08-07 00:35**: STEP 5 — Archived `sports_index_recency_masked_captured_atoms` (cleared stale `locked_by: ""`
  seed artifact). Reverted premature half-flip. Converted 3 zero-checkbox docs to tracked todos (5 items). Branch pushed
  (5 commits).
- **2026-08-07 00:40**: Final report written. PR created.
