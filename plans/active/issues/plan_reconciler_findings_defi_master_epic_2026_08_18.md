---
doc_type: issue
title: "plan_reconciler defi_master EPIC-scoped run findings — 2026-08-18 (interactive, epic-scoped mode)"
summary: >-
  First-ever epic-scoped `/plan-reconcile defi_master` pass (50 parent_epic:defi_master docs — a different axis
  from the same-day defi-TRANCHE run in plan_reconciler_findings_defi_2026_08_18.md, which covers asset_group:[defi]
  ~131 docs and has substantial but not total overlap). Phase -1 reconciled the 3 prior dated defi-tranche findings
  docs (2026-08-16/17/18) against fresh state, closing a "routed finding never delivered back" gap in the
  2026-08-17 doc (2 items the 2026-08-18 tranche run's own Phase -1 had already verified resolved but never flipped
  in the 2026-08-17 doc's own checkboxes). Fanned 5 read-only hunters (10/10/10/10/7 docs) across the full corpus,
  every doc read in full. Applied 24 auto-fixed items (all provable via git/grep/code-read this same turn) directly
  under trust mode, archived 3 fully-done issue docs via the 6-step ritual (10 referrer-path fixes), and parks 4
  items genuinely needing live-infra verification or a further operator/design call. 1 Phase-0 mechanical flag
  (fully-done-archival-candidate) was refuted on adversarial verification. DO NOT SHIP constraint in effect for this
  run — every fix landed in the working tree only, no commit/push; a separate lead session ships.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, defi_master, epic-scoped, reconciliation]
related:
  [
    /plans/epics/defi_master.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_18.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_17.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_16.md,
  ]
created: "2026-08-18"
author: plan_reconciler
source: "interactive session, /plan-reconcile defi_master (epic-scoped)"
locked_by:
priority: P2
assigned_vm: NA
execution_scope: local-only
parent_epic: defi_master
resolved_by:
depends_on: []
drift_direction: advance-code
context_scope:
  [
    /plans/epics/defi_master.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_18.md,
    /codex/11-project-management/epic-html-report-format.md,
  ]
---

# plan_reconciler defi_master EPIC-scoped findings — 2026-08-18

Interactive session, epic-scoped mode (`/plan-reconcile defi_master`), not AO-dispatched. **DO NOT SHIP constraint**:
shared checkout under heavy contention today (a concurrent session's `ci`-tranche + other WIP was visibly present in
`git status` throughout this run — untouched, not staged, not committed). All fixes below are working-tree-only.

## Coverage

- Phase -1: found + reconciled the 3 existing `plan_reconciler_findings_defi_2026_08_{16,17,18}.md` docs (all
  `parent_epic: defi_master`, in-scope). None had zero genuinely-open items (none archived); the 2026-08-17 doc had
  2 checkboxes that should have already been flipped by the 2026-08-18 tranche run's own Phase -1 findings but
  never were — closed that specific "routed finding never delivered back" gap this run (see Fixes below).
- Phase 0: deterministic inventory of all 50 `parent_epic: defi_master` docs (throwaway scratchpad script) — 109
  open / 177 done checkboxes, 6 zero-checkbox docs, 1 fully-done-candidate flag (refuted, see below), 22
  near-complete (≤1 open) docs (steady-state shape for this AO-heavy satellite-batch epic, not actioned per
  SKILL.md's "ongoing near-complete handling routes through the regular cadence, not a one-off sweep"), 0 over the
  1000L hard cap (5 over the 500L soft cap, noted only), 0 conflict markers, 0 locked docs.
- Phase 1-2: 5 parallel read-only hunters (batches of 10/10/10/10/7), every one of the 50 docs read in full by
  exactly one hunter, cross-checked against the same-day tranche run's own findings so already-known items weren't
  re-flagged. ~24 raw candidates returned across contradictions, done-but-unchecked, hygiene/frontmatter drift,
  dangling refs, and one epic-hub architecture-staleness finding.
- Phase 3: every candidate independently re-verified this turn (fresh `grep`/`git log`/`wc -l` re-checks) before
  applying — none trusted from hunter prose alone.

## Fixes applied (all AUTO-FIXABLE — provable this turn, applied directly under trust mode)

1. **[P2]** `plans/epics/defi_master.md` `related_plans:` was missing 3 still-open child plans while listing only
   their finalize/satellite companions (`defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md`,
   `defi_live_poller_phased_build_2026_08_15.md`, `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`)
   — the exact "orphan invisible to sweep" class this corpus has hit twice before. Added.
2. **[P3]** `defi_epics/defi_master.md` §"MTDS DeFi slice" + §"Discoveries during Priority #5" present the
   dedicated-per-data_type DeFi bucket architecture as current fact; it was retired 2026-07-10..07-16 (see
   `defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`, corroborated by
   `defi_consolidated_closeout_2026_07_18.md`'s own headline verdict). Added STALE banners to both sections.
3. **[P3]** `defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md`'s `depends_on` pointed at
   `defi_by_date_capture_cron_stale_2026_08_16`, archived 2026-08-16 as a false positive (this doc's own body
   already says so). Cleared `depends_on: []`.
4. **[P2]** `defi_satellite_ao_dispatch_batch14_2026_08_16_finalize.md:65` cited "todos 1 and 3" for a source doc
   whose Todos section has only 2 items (batch14 itself already had this citation corrected 2026-08-18; the
   finalize companion's identical citation was missed). Fixed to "1 and 2".
5. **[P3]** `defi_satellite_ao_dispatch_batch11_2026_08_09_finalize.md` said "12 todos" in 3 places; batch11 itself
   now has 13 (a mid-execution split 2026-08-09, corrected in batch11's own text 2026-08-18, never propagated to
   the finalize companion). Fixed all 3.
6. **[P3]** `defi_satellite_ao_dispatch_batch16_2026_08_17.md` had a duplicate `effort: high` YAML key. Removed the
   duplicate.
7. **[P2]** `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` todo 3's prose said 2 of 3 sub-items
   "remain unverified/likely open"; sub-item (2)'s retag is independently confirmed live (frontmatter shows the
   2026-08-02 retag + cleared lock). Updated the prose — only sub-item (1) is genuinely still open.
8. **[P3]** `pacifica_solana_perp_reintegration_2026_08_14.md`'s final Progress Log line was genuinely truncated
   mid-sentence on disk (verified via raw `tail`), and its "26/27" count was off-by-one against a fresh
   `grep -cE` recount (27 done + 1 open = 28). Closed the sentence honestly (no fabrication) + corrected the count.
9. **[P2]** `defi_track01_per_instrument_and_canon_id_2026_07_24.md:295` cited a VM's terminal-SUCCESS as
   "confirmed in the R3-run entry above" — grep-verified the VM name never appears there (a mis-citation). Fixed
   the citation to point at the 3 docs that actually corroborate it; the R3 checkbox's own broader open question
   (does that VM's success cover R3's FULL remaining scope) is NOT resolved by this fix — see Parked #3 below.
10. **[P2]** `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` had `assigned_vm: planning` +
    `execution_scope: local-only` — code-verified (`count_open_tasks.py:130`) this combination silently excludes
    the doc from the AO-dispatch-eligible count despite the intended 2026-08-08 NA→planning flip. Fixed to
    `orchestrator-agent`, matching the corpus-wide pattern (369/372 planning docs use it).
11. **[P3]** `mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md:215` cited
    `market-data-processing-service@5bc11b8` — git-verified NOT an ancestor of that repo's live branch (a
    pre-history-rewrite dangling hash); the doc's OWN line 179 already cites the correct `@5bc11b8`. Fixed.
12. **[P2]** Same doc's `[REVIEW] P2` "per-slot RSS ceiling, out of scope to design" todo — a matching mechanism
    (`ORCHESTRATOR_WORKER_MEMORY_MAX` / `_worker_mem_scope_prefix()`, built 2026-06-12) already exists but is
    unarmed fleet-wide (0 references found repo-wide). Reframed the todo from "design fork" to "is it armed +
    does it cover this subprocess class" — narrower, not closed (see Parked — no, this one has enough evidence to
    reframe directly; the remaining question is itself the todo now, not a separate parked item).
13-26. **14 stale `last_updated` frontmatter fields** bumped to their real `git log -1` date (verified per-file
    before applying): `defi_consolidated_closeout_2026_07_18`, `defi_satellite_ao_dispatch_batch2_2026_07_26` (+
    `_finalize`), `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize`, `defi_strategy_pnl_axis_index_2026_07_24`,
    `defi_track01_per_instrument_and_canon_id_2026_07_24`, `defi_track5_coverage_mvp_backfill_2026_07_24`,
    `pacifica_solana_perp_reintegration_2026_08_14`, `solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12`,
    `issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04`,
    `issues/defi_morpho_lending_indices_never_wired_2026_07_12`,
    `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30`,
    `issues/na_eligibility_audit_defi_blocks_2026_08_16` (+ `_17`).
27-28. **2 checkboxes flipped in `plan_reconciler_findings_defi_2026_08_17.md`'s own "Doc-drift / routed" section**
    — both were already independently confirmed resolved by the same-day tranche run's own Phase -1
    (`plan_reconciler_findings_defi_2026_08_18.md`) but never flipped in the 2026-08-17 doc itself: the
    `data_pipeline_check_mdps_features_2026_07_20.md` `[REVIEW] P2` todo, and the
    `strategy_service_centralization_fixes_2026_08_16.md` `sequential`/`[OPERATOR]` question. Also split the
    "AO-dispatch-readiness tagging gaps" item into its 2 halves (batch14 = fixed 2026-08-18; indexer todo = still
    genuinely open, now confirmed a LIVE gap not a pre-flip one).

## Archived (fully-done, verified, unlocked — 6-step ritual executed)

1. `defi_dex_pool_density_drop_pool_level_followup_2026_08_14.md` → `plans/archive/2026_08/issues/` — 0 genuine
   open work (sole todo CANCELLED/extracted, extraction target confirmed live); `archive_exempt: true` was a
   "not yet archived" bridge marker, not a genuine standing-reference exemption.
2. `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` → `plans/archive/2026_08/issues/` — all 3
   todos `[x]` with hard evidence (market-tick-data-service@f5753479 + slot-23's live 2026-08-15 verification).
3. `features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md` →
   `plans/archive/2026_08/issues/` — all 4 items `[x]`; `archive_exempt: true` bridge note was 6+ days stale.

Referrer sweep: 10 path-form references across 5 active docs fixed to point at the new archived paths
(`defi_satellite_ao_dispatch_batch14_2026_08_16{,_finalize}.md`,
`defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08.md`,
`features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07.md`). Bare-name prose mentions in
already-archived docs left untouched (not misleading, don't need a live path — same precedent the 2026-08-16 run
used).

## Refuted (Phase-0 mechanical flag, not a real finding)

1. `defi_strategy_pnl_axis_index_2026_07_24.md` was Phase-0-flagged FULLY-DONE-CANDIDATE (open=0, done=1, active,
   unlocked). Adversarial verification: it carries `archive_exempt: true` + an explicit 2026-08-06
   `archive_candidates_content_verification` ruling that it's a standing-reference entry-point hub, not
   archivable. Phase-0's mechanical checker doesn't check `archive_exempt` — a known, documented limitation, not a
   new bug. Not archived.

## Parked — needs live-infra verification or further judgment (NOT resolved this pass)

1. **[P3]** `defi_satellite_ao_dispatch_batch11_2026_08_09.md` is 995L with its own self-recorded warning
   ("next tick MUST condense 35th-38th-era journal entries") only partially acted on. **[WORKER REC]**: condense
   the ~lines 640-975 near-duplicate pre-compact re-check entries before the next append risks the 1000L hard cap.
2. **[P3]** Same doc's "Deferred work after 2026-08-10" table (mdps-defi fleet drain / manifest-consolidator
   pause gate) is 7 days stale with no live re-check since. **[WORKER REC]**: a data_engineering pass should
   re-verify current GCP/VM state before trusting the doc's "Recommended next item".
3. **[P2]** `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3-run checkbox (line ~181, still `[~]`
   partial) — VM `canonical-migration-defi-rebuild-20260810-204358`'s terminal SUCCESS is now correctly cited
   (fix #9 above), but whether that success covers R3's FULL remaining scope (vs. one resumed sub-window) is
   unresolved without a fresh live check. **[WORKER REC]**: a data_engineering follow-up should confirm scope
   coverage, then flip the checkbox if it's genuinely complete.
4. **[P2]** `solana_dex_pool_swaps_indexer_2026_08_08.md` todo 5 — a VM-launch/data todo carrying no `[OPERATOR]`
   tag or safe-idempotent justification. Confirmed a LIVE gap (doc is `status: active` + `assigned_vm: planning`,
   already AO-dispatched) by both the 2026-08-18 tranche run and this pass's own re-check. **[WORKER REC]**: add
   the tag or a stated safe-idempotent justification before this todo next dispatches.

## Phase 5.9 ledger

- `routed = 4` (the 4 Parked items above, each genuinely needs_operator/live-investigation, none auto-fixable).
- `parked_in_issue_doc = 4` (all 4 written into this doc's "Parked" section, with `[WORKER REC]` each).
- **`routed == parked`: 4 == 4.** ✅
- `agent_skips = 0` (no sub-agent apply-pass was used — every fix was applied directly by the orchestrating
  session after its own Phase 3 verification, so there is no separate skip-reporting sub-agent step to reconcile).
- Conservation (Phase 5.9(d)): no fold/move operations this run (no near-complete plan was folded), so no
  FOLDED-OUT/FOLDED-IN balance to check.

## Coverage tally

- Docs read in full: 50/50 (`parent_epic: defi_master`), by hunter batch: 10/10/10/10/7 + 3 (the 3 prior
  findings docs, read directly by the orchestrating session in Phase -1, not delegated).
- Candidates returned: ~24 raw. Disposition: 24 auto-fixed + applied, 3 archived, 1 refuted, 4 parked.
- Zero-checkbox docs swept: 6 (`defi_dex_pool_density_drop_pool_level_followup_2026_08_14` → archived;
  `na_eligibility_audit_defi_blocks_2026_08_{16,17,18}` + `plan_reconciler_findings_defi_2026_08_{16,18}` → all
  confirmed genuine index/run-journal docs holding zero actionable prose work, verdict re-confirmed not just
  assumed).

## Progress Log

- **2026-08-18 (interactive, epic-scoped `/plan-reconcile defi_master`)**: full pass as documented above. DO NOT
  SHIP — every fix is working-tree-only; a concurrent session's unrelated `ci`-tranche + other WIP was visibly
  present in `git status` throughout (untouched). Lead session ships this doc's own file list by name.
- **2026-08-18 (lead-session ship)**: `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s mis-cited-VM
  correction (genuine content fix — a `canonical-migration-defi-rebuild-20260810-204358` VM name that turned out
  to be absent from the cited corroborating entry, re-sourced from 3 other docs) could NOT ship this pass: the
  file was already exactly 1000L on origin (zero headroom), and the correction's net +5 lines pushes it to 1005L,
  over the hard cap — none of `check_line_caps.sh`'s 4 existing narrow carve-outs cover a genuine multi-line
  content correction. Same class of gap as `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` (epic
  taxonomy restructure, same day). Deferred; the fix stays applied locally, uncommitted, pending either a real
  split of this doc or a 5th operator-ruled carve-out.

- [ ] [DOCS] P2. Ship `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s mis-cited-VM correction (see
      above) — needs the doc split under its own 1000L cap first, or a `check_line_caps.sh` carve-out for a
      bounded multi-line content correction.

- **na-eligibility-audit 2026-08-19** (tranche=defi, dispatch agt-88e4bb): KEEP-NA, valid — read end to end, 1 open
  item confirmed (matches Phase-0). The remaining todo needs either splitting `defi_track01_per_instrument_and_canon_id_2026_07_24.md`
  under its own line cap, or an operator-ruled `check_line_caps.sh` carve-out — both squarely operator-gated per
  this same corpus's own established precedent (`plan_reconciler_findings_defi_2026_08_16.md`'s identical
  1000L-cap class of finding: "splitting a plan is an operator-gated planning decision per CLAUDE.md, not a
  mechanical trim"). Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
