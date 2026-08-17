---
doc_type: issue
title: "plan_reconciler defi-tranche run findings — 2026-08-17 (dispatch agt-5dedc7, slot 28)"
summary: >-
  Daily deep reconciliation pass over the defi topic tranche (140 active docs). Run in progress — this doc is the
  live journal, appended to as checkpoints land.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, defi, reconciliation, checkpoint]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md, /plans/active/issues/plan_reconciler_findings_defi_2026_08_16.md]
created: "2026-08-17"
author: plan_reconciler
source: "agt-5dedc7"
locked_by: plan_reconciler-agt-5dedc7
priority: P2
assigned_vm: NA
execution_scope: local-only
parent_epic: defi_master
resolved_by:
depends_on: []
drift_direction: advance-code
---

# plan_reconciler defi-tranche findings — 2026-08-17

Dispatch `agt-5dedc7`, slot 28, tranche `defi`.

## Phase -1 — prior findings doc reconciliation

`plan_reconciler_findings_defi_2026_08_16.md` re-checked against fresh state: all its STILL-OPEN items remain
accurately open (no drift, nothing newly resolved) — see that doc's own 2026-08-17 Progress Log entry for the
per-item detail. Not archived (genuine open work remains).

## Coverage

- STEP1: FF-pulled every repo in the slot — all clean, no WARN.
- Tranche inventory: 140 active docs (`generate_tranche_doc_inventory.py --tranche defi`), up from 130 on 08-16 (10
  new docs — mostly new satellite-dispatch batch14/15 pairs + same-day incident docs).
- Phase 0 mechanical sweep: corpus-wide `run_hygiene_sweep.sh --ci` is RED (4 hard fails + 4 orphans), but every
  one of the 4 hard-fail items was traced to its exact violating file and confirmed NOT defi-tranche-owned
  (`check_reference_paths`→tradfi doc, `check_ag_closeout_linkage`→cross-cutting doc, `check_create_only_archive_commits`→CI/infra doc,
  `check_na_corpus_ratchet`→mostly expected growth: legitimate new incident docs + the reconciler's own daily
  findings docs + 2 already-converted zero-checkbox docs from yesterday's run). None fixed here — out of tranche
  scope, left for the owning tranche/skill.
- Fanned out 7 parallel read-only hunters (batches A-G, ~20 docs each) covering all 139 docs not already
  deep-reconciled inline (doc #125 in the inventory, yesterday's own findings doc, handled directly in Phase -1
  above) — every doc read in full by exactly one hunter. Hunters returned ~55 candidates across contradictions,
  missed-flips, zero-checkbox docs, AO-dispatch-readiness issues, structural/line-cap flags, and dangling refs.
- Verified inline (I am sonnet/max — small-to-moderate candidate counts verified directly per this doc's own
  frontmatter `model: sonnet` + CLAUDE.md's 2026-08-08 ruling that opus is manual-only): re-ran the cited greps,
  re-counted checkboxes, and re-read surrounding context for every candidate before applying a fix.

## Checkpoint 2 — operator answered BLK-bddcd537 ("A"), applied

Filed as a blocked-question (STEP 6a) after `check_line_caps` correctly blocked the §I table fix — see
Contradictions #4 below for the original finding. Operator answered **A** (via `GET /api/activity`, since the
answer never reached `/api/slots/28/messages` — the same known orphaning bug as
`plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md`; adding this as a fresh data point there).
Applied: extracted 3 more historical Progress Log entries (measurement lesson, fourth pass, third pass — all
2026-08-12, pure session narration already folded into sections H/H.5/H.7 above, no open todo referenced) from
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` to the existing companion archive doc
(`/plans/archive/2026_08/elysium_october_delivery_and_code_disclosure_readiness_progress_log_history_2026_08_15.md`),
same pattern as that doc's own 2026-08-15 extraction. Doc now 960L (was 1001L), comfortable headroom restored.
Reapplied the previously-reverted §I table fix on top (elysium_carveout 16/2→18/4, uac_kamino 0/0→1/0).

## Flips verified (applied this run)

1. `elysium_carveout_stubbed_strategy_service_2026_08_12.md` — PortfolioRiskService todo `[ ]`→`[x]`: the doc's own
   established convention (flip on ruling-landed, matching its structurally-identical sibling item two entries
   later) wasn't applied to this one even though the identical "RULED 2026-08-16 (operator)" ruling text is
   present. Verified the ruling text directly before flipping.

## Contradictions (confirmed) — all fixed this run

1. **[P0]** `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` — a `> **SUPERSEDED 2026-08-14**` banner
   (PACIFICA-SOLANA decommission reversal) was added to only 1 of 4 sibling todos in the same decision cluster;
   the other 3 ("PACIFICA stays fully removed", "do NOT re-add it") carried no pointer — a reader landing on those
   3 without hitting the first gets actively wrong guidance. Fixed: added a pointer note redirecting to the banner
   + flagging both FIX todos' N/A premises for re-examination now that PACIFICA has a live pipeline again
   (did not resolve the underlying re-examination myself — that's real investigative work, not doc hygiene).
2. **[P1]** `defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md` — banner claimed batch9 has "17" todos (3
   locations: summary, 2 status lines) while the doc's OWN Todo-1 entry, dated the same day, corrected the count
   to 18 (`grep -c '^- \[x\]' defi_satellite_ao_dispatch_batch9_2026_08_06.md` = 18, independently re-verified).
   Fixed all 3 stale "17"s to "18" (left the historical 2026-08-06 Progress Log entry's "17" untouched — historical
   record, not a live claim).
3. **[P2]** `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` — title said "mechanism UNRESOLVED" while the
   doc's own summary (same doc) said "ROOT CAUSE NOW CONFIRMED 2026-08-16". Fixed the title to match.
4. **[P2, fix identified but BLOCKED, see Doc-drift below]** `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`
   §I work-surface table — 2 stale sibling-doc rows: `elysium_carveout_stubbed_strategy_service_2026_08_12` listed
   "16/2" vs actual (re-counted) 18/4; `uac_kamino_venue_reachability_cascade_regression_2026_08_15` listed "0/0"
   vs actual 1/0 (it has 1 real open todo). Correct fix identified and drafted, then REVERTED — `check_line_caps`
   pre-commit hook correctly blocked it: this doc is independently at 1001L, over the 1000L hard cap (pre-existing,
   not caused by this edit — the edit was a net-zero line-count content swap). Not committed; see Doc-drift.
5. **[P1]** `na_eligibility_audit_defi_blocks_2026_08_16.md` carry-forward list — claimed
   `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` still had 3 open items; 2 of the 3 (the `ShardedState`
   migration + the watchdog pip-install-swallow fix) are actually `deployment-service@6f2f8e02bf`, independently
   confirmed via `git show 6f2f8e02bf:scripts/recovery/relaunch_stalled_vm.py | grep -c ShardedState` = 4. Fixed
   the carry-forward list to show only the 1 genuinely-remaining item (re-derive the "four preemptions" narrative).
6. **[P1]** `defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md` — claimed a corpus-wide grep for the
   4 paused scheduler names found "no hit". Independently re-ran the identical grep: it DOES hit
   `defi_consolidated_closeout_2026_07_18.md` Track 8, which tracks the exact same 4-scheduler pause (dated
   2026-07-22) and names the real resume-gating condition (Track-1/2 landing + the in-flight
   `canonical-migration-defi-rebuild-*` VM finishing) — materially different from this doc's own narrower
   VM-race-only check. **Corrected the false claim and added the Track 8 pointer; did NOT resume any scheduler
   myself** — that remains a live operational decision for whoever next reads the corrected doc.
7. **[P2]** `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` open question #3 (LIGHTER-ZKSYNC fix "exists
   only as uncommitted working-tree changes") — the sibling doc shows it shipped+re-verified 2026-07-30,
   `market-tick-data-service@0c4000a02` (independently confirmed via grep before citing). Fixed.
8. **[P1]** `lst_rate_honest_coverage_2026_07_21.md` Deferred-work table, 2 self-contradicting cells:
   (a) Phase-5-#1 row's prose explicitly said the memory-hang issue doc is NOT this item's real blocker, but the
   "Blocked on" column still cited it — fixed the column to state the actual blocker (operator decision only).
   (b) Phase-6-E3 row said "Not started", but the doc's own 2026-08-08 Progress Log entry says this exact item was
   already closed (`strategy-service@23bd8b76`) — the table row was never updated to match. Fixed.

## Hygiene fixes

1. `defi_strategy_pnl_axis_index_2026_07_24.md` — `repos:` frontmatter was missing `strategy-service` despite the
   doc's own title/summary naming it as the entry point for exactly that repo's DeFi track. Added.
2. `uac_kamino_venue_reachability_cascade_regression_2026_08_15.md` — file was truncated mid-sentence (a corrupted
   write, most likely from a prior na-eligibility-audit edit) at its very last line. Completed the sentence using
   the actual todo text it was quoting.
3. `solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md` — removed a stray leftover line (`edit.`) sitting
   between two todos — an accidental editing artifact, not content.
4. `defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md` — **REVERTED, see Doc-drift below.** Attempted to
   add `gate_on_depends: true` alongside its existing `depends_on:`; the `plan-hygiene` pre-commit hook correctly
   flagged this as creating an inconsistent state ("finalize plan redundantly stuck at status: draft — gate_on_depends
   already holds them, flip to status: active"). On reflection this doc's real gate is OPERATOR AUTHORIZATION
   (its own summary: "status draft until the operator authorizes firing it... do not fire it from this dispatch"),
   not dependency-completion — `depends_on` here is informational context, not a machine-gate candidate. Reverted;
   no fix applied. This doc is fine as originally written.

## Zero-checkbox docs found → converted to tracked todos

1. `subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md` (P1, `assigned_vm: NA`) — converted its
   "Recommended decision" prose (a conditional wait-then-triage-or-close plan) into one tracked `[DIAG] P2` todo
   with an explicit done-when, preserving the original conditional logic.

## Doc-drift / routed (NOT auto-fixed — genuine judgment calls, blocked by another gate, or needs live infra/investigation beyond doc reconciliation)

- ~~`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` over cap~~ **RESOLVED — see Checkpoint 2
  above** (operator ruling A applied: extraction + table fix both landed).
- **`data_pipeline_check_mdps_features_2026_07_20.md`** (hunter batch A) — a same-day-earlier plan_reconciler entry
  in this SAME doc already found the todo's cited gating doc (`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`)
  resolved/archived 19 days ago, but the still-open `[REVIEW] P2` todo (line ~255, "split the P0 item into its own
  plan gated on" that same doc) was never updated to reflect this. Whether a companion plan is still needed at all
  (and if so, ungated) is a scope/design call for the todo's owner, not a mechanical flip — routing rather than
  guessing.
- **`defi_by_date_capture_cron_stale_2026_08_16.md`** (hunter batch A) — a `[DIAG]` todo's first line names its
  target ambiguously ("likely `instruments-daily-backfill` or `instruments-service-daily-trigger`"). Resolving
  which one is correct needs a live `gcloud scheduler jobs list` check I did not run (out of scope for doc
  reconciliation alone) — routing for whoever picks up this AO-dispatched todo to resolve at dispatch time, or a
  follow-up to disambiguate before dispatch.
- **`operator_action_items_consolidated_2026_08_08.md`** (hunter batch G) — a `.tabs/2` stash-cleanup item claims
  (as of 2026-08-08) a live unresolved 3-way git merge conflict in another slot's working tree; 9 days of
  subsequent Progress Log entries never re-verified whether it was resolved. I did not check `.tabs/2` myself
  (reading/touching another slot's live working tree is out of this run's scope per multi-agent-safety rules) —
  routing for a fresh check.
- **`strategy_service_centralization_fixes_2026_08_16.md`** (hunter batch G) — `sequential: true` + todo 1 tagged
  `[OPERATOR]` serializes the whole 18-todo plan behind one human decision, including todos that read as
  semantically independent (GCS config-loader unification, venue-literal audit, a docstring fix, a 69-candidate
  inventory/classify task). Whether to de-scope `sequential: true` or restructure the dependency is a plan-authoring
  preference call (SKILL.md Modes § Calibration: "how to split a plan" stays operator-gated even under trust mode)
  — routing rather than restructuring unilaterally.
- **`defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`** (hunter batch D) — `sequential: true`'s stated
  justification ("todo 4/archival must run last") is now provably stale: todo 4 already ran and archived batch3
  on 2026-08-06, while todo 1 (source-doc reconciliation) is still open ~3 weeks later — the declared process
  order was violated in practice with no apparent ill effect. Low-risk (nothing is currently blocked by it), noting
  for whoever next touches this doc's ordering metadata rather than fixing preemptively.
- **`data_completion_defi_2026_07_15.md`** (hunter batch A) — a 3-way tracking overlap (this doc's C2/C3/C4/C9/C11
  vs `defi_consolidated_closeout_2026_07_18.md` vs `defi_track01_per_instrument_and_canon_id_2026_07_24.md`) is
  self-flagged by the doc's own na-eligibility-audit entry as "deferred to a dedicated hands-on pass" — not
  attempted here, corroborating only.
- **`uac_data_type_validity_combinator_fragmentation_2026_07_07.md`** (1005L) — pre-existing over-cap doc from
  yesterday's run, re-confirmed still 1005L today (Phase -1 above), still operator-gated for a split, unchanged.

## Refuted (dropped by verify)

_(none this run so far)_

## Coverage (hunters / batches / docs)

- 7 hunters (batches A-G), 139 docs + 1 already deep-reconciled inline (Phase -1) = 140/140 tranche docs read in
  full.
- Candidates returned: ~10 contradictions (8 confirmed+fixed above, rest routed below), ~4 missed-flip candidates
  (1 confirmed+fixed above), 2 zero-checkbox docs (1 converted above, 1 self-documented intentional exception —
  `na_eligibility_audit_defi_blocks_2026_08_16.md`, a pure index doc), ~10 AO-dispatch-readiness issues, ~10
  dangling-ref/hedge-pointer findings, ~15 structural/line-cap/format findings.

## Plans not reached (lower-priority hunter candidates, not independently acted on this run)

- **`defi_operator_ruling_ao_dispatch_2026_08_15.md`'s PHOENIX-SOLANA registry claim** (hunter batch C) — partially
  verified: PHOENIX-SOLANA DOES appear in `unified-api-contracts`'s `defi_venues.py` venue list + adapter mapping +
  `defi_venue_capabilities.py` (capability since 2023-02-01), so `uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md`'s
  "IS present in ALL_DEFI_VENUES" claim checks out. But `defi_venues.py:800` also carries a
  "METEORA-SOLANA / LIFINITY-SOLANA / PHOENIX-SOLANA excluded 2026-07-22" comment, whose exact target list I did not
  fully resolve — `cross_ag_live_capture_parity_2026_08_14.md`'s "not in VENUES_BY_ASSET_GROUP" claim may ALSO be
  correct if that's a different, narrower structure than `ALL_DEFI_VENUES`, which would mean this isn't actually a
  contradiction (both claims true of different registry structures). Needs one more grep to fully resolve before
  the still-open dead-code-deletion todo in `defi_operator_ruling_ao_dispatch_2026_08_15.md:54` is actioned either
  way — not resolved here.
- **Cross-link asymmetry among the 4 `dex_swaps` row-count-conflict docs** (hunter batch B) — 2 of the 4 docs
  (`defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md`, `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`)
  still carry no reciprocal cross-link note, and the 2 that do have one disagree on membership (one lists only 2 of
  the other 3 docs). Mechanical fix (add/complete 4 cross-reference notes) not applied this run — lower priority
  than the contradictions actually fixed above.
- **`~2025-07-27→2025-08-06` date in the dex_swaps docs** (hunter batch B, flagged as a possible year-typo) —
  checked: both `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` and the newly-authored
  `defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md` consistently say "2025", not "2026" — **REFUTED as a
  propagation-typo finding** (the two docs agree with each other, so there's no cross-doc contradiction here,
  whatever the actual correct year is — that's a separate empirical question needing a live manifest check, out of
  scope for doc reconciliation).
- **`defi_expected_unattempted_backlog_1m_2026_07_03.md`'s `locked_by:` field** (hunter batch B) — confirmed via
  `git log -p`: the lock (`locked_by: live-defi-rollout`, `locked_since: 2026-07-03`) WAS deliberately cleared in a
  commit carrying `last_updated: "2026-08-08"`. Current state: no lock. This means the finalize plan's archival
  todos (which 7 prior dispatch cycles declined to act on citing this exact lock) may now be actionable — but
  actually running the archival needs a fresh full read confirming every todo is genuinely done first (the 6-step
  ritual), which I did not do this pass (time-boxed). Flagging as a high-confidence, concretely actionable item for
  a focused follow-up, not attempted here.
- Assorted P3 format/cosmetic items (missing `[ ]`/`[x]` checkbox brackets on several `CANCELLED — extracted...`
  bullets across multiple docs) — all corroborate an ALREADY-tracked corpus-wide issue
  (`todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md` per hunter batch A), not
  re-filed separately.
- Minor AO-dispatch-readiness tagging gaps on 2 still-`status: draft` docs (`defi_satellite_ao_dispatch_batch14_2026_08_16.md`
  VM-launch todos untagged `[OPERATOR]`; `solana_dex_pool_swaps_indexer_2026_08_08.md` todo 5, low-confidence per
  the hunter itself) — pre-dispatch check window, not urgent while still draft/scoped, noted for whoever reviews
  before flipping to active.
