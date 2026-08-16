---
doc_type: issue
title: "plan_reconciler defi-tranche run findings — 2026-08-16 (dispatch agt-1a88e0, slot 6)"
summary: >-
  Daily deep reconciliation pass over the defi topic tranche (130 active docs). Deep-reconciled a data-correctness
  bucket-delete-safety thread across 4 docs, fixed a self-contradicting checkbox connected to an unresolved POOL-row
  recurrence incident, archived one HARD-RULE-violating unarchived-done doc, converted 2 zero-checkbox docs to tracked
  todos, and applied several same-day missed-flips found by a 7-hunter fan-out. Run in progress — this doc is the
  live journal, appended to as checkpoints land.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, defi, reconciliation, checkpoint]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: "2026-08-16"
author: plan_reconciler
source: "agt-1a88e0"
locked_by:
priority: P2
assigned_vm: NA
execution_scope: local-only
parent_epic: defi_master
resolved_by:
depends_on: []
---

# plan_reconciler defi-tranche findings — 2026-08-16

Dispatch `agt-1a88e0`, slot 6, tranche `defi`. **Note on boot config**: `PM_REPO_PATH` in this dispatch's boot message
pointed at the root PM clone (`/home/ubuntu/unified-trading-system-repos/unified-trading-pm`), not the slot clone —
contradicts the explicit root-read-only guardrail in `agents/RULES.md`/`agents/plan_reconciler.md`. All work in this run
used the slot clone (`.tabs/6/unified-trading-pm`) instead; flagging this as a dispatch-generator bug worth a fix (likely
in `agent-orchestrator/server`'s boot-message construction) so future dispatches don't get a literal root path.

## Coverage

- STEP1: FF-pulled every repo in the slot (one repo, `unified-api-contracts`, not FF-clean — pre-existing dirty
  `registry/__init__.py`, flagged, not touched — out of this tranche's scope).
- Tranche inventory: 130 active docs (`generate_tranche_doc_inventory.py --tranche defi`).
- Fanned out 7 parallel read-only hunters (batches A-G) covering all 126 docs not already deep-reconciled inline —
  every doc read in full by exactly one hunter. Hunters returned 50+ candidates across contradictions, missed-flips,
  zero-checkbox docs, AO-dispatch-readiness issues, and dangling refs.

## Flips verified (applied this run)

1. `data_completion_defi_2026_07_15.md` — C0 parent todo flipped `[ ]`→`[x]`: all 7 of its own stated sub-todos
   (C0-PROVISION, C0a-C0f) were independently confirmed `[x]` by direct read.
2. `defi_migration_audit_log_2026_07_24.md` — 2 todos annotated/rescoped (not flipped, corrected in place): the
   "VERIFY-then-MIGRATE unique orphan gaps" todo (downgraded P1→P2, marked BLOCKED not done — source buckets deleted)
   and the "DELETE duplicate/legacy DeFi orphan buckets" todo (rescoped — `market-data-tick-defi{,-prd}` removed, it's
   the PERMANENT canonical bucket, not legacy; `solana-defi`/`evm-defi` already deleted 2026-07-10, nothing left to
   delete there either). See Contradictions #1 below for the full evidence chain.
3. `defi_migration_audit_log_2026_07_24.md` — aggregator-routes 9th-migrator-spec todo: added a CAVEAT (do not
   `--apply`, destination bucket unprovisioned) + a new `[OPERATOR] P1` follow-up todo.
4. `defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md` — converted its prose "Recommended decision"
   into tracked checkboxes reflecting current resolution state (zero-checkbox-doc sweep); downgraded priority P2→P3
   (3 of 4 items now resolved).
5. `defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md` — flipped its `[OPERATOR] P1` "re-scope the
   delete list" todo to `[x]`, citing the fix applied in item 2 above.
6. `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` — REOPENED (`[x]`→`[ ]`) the POOL-instrument_type-fold P3
   todo: the doc's own later-appended text already says the "0 remaining" DONE claim is STALE/CONTRADICTED (7.9M rows
   recurred), but the checkbox itself was never aligned to that reality. See Contradictions #2.
7. `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` — added a `> **SUPERSEDED 2026-08-14**` banner to the
   PACIFICA-decommission decision: the operator reversed this 2026-08-14 ("jupiter and pacifica please"), confirmed
   live in `/codex/04-architecture/solana-defi-coverage.md`; the doc carried no banner reflecting the reversal (an
   unbannered supersession). Also fixed its `context_scope` path to the archived location (item 8).
8. `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` — **ARCHIVED** via `git mv` to
   `plans/archive/2026_08/issues/` (all 9 todos + 2 follow-ups `[x]`, unlocked, `archive_exempt: true` note said "will
   archive in immediate follow-up" dated 2026-08-10 — 6 days overdue, a HARD RULE violation per CLAUDE.md "A plan with
   every todo done + unlocked MUST be archived immediately"). Fixed its one genuine path-form referrer (item 7 above);
   4 other referrers are historical bare-name prose mentions, left as-is (not misleading, don't need a live path).

## Zero-checkbox docs found → converted to tracked todos

1. `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` (P1, `assigned_vm: planning`) — converted its
   "Recommended decision" (4 items) into real checkboxes. 2 of the 4 were ALREADY resolved in the doc's own "What I
   found" section (struck through) but never reflected in "Recommended decision" — flipped those `[x]` too; 2 remain
   genuinely open (GCS-object sampling + the final retirement decision). This is the doc tracking the recurrence
   connected to Flip #6 above.
2. `dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md` (P1, `assigned_vm: NA`) — converted its
   "Recommended decision" (Option A/B) into 2 tracked todos.

## Contradictions (confirmed)

1. **[P0, data-correctness] A DELETE todo's target list included the live production canonical bucket.**
   `defi_migration_audit_log_2026_07_24.md`'s "DELETE duplicate/legacy DeFi orphan buckets" todo listed
   `market-data-tick-defi{,-prd}` as a legacy-delete candidate. Two independent live-verified investigations
   (`defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md` and, more thoroughly,
   `defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`, slot 22, live-GCS-verified) already
   confirmed this bucket is PERMANENT canonical — every DeFi handler converges on it since the 2026-07-10..07-16 bucket
   estate cleanup. Fresh-confirmed again this turn via `deployment-service/configs/cloud-providers.yaml`. FIXED (Flip
   #2). Was NOT yet executed (operator sign-off gate existed), but a future worker reading the todo literally could
   have destroyed the live DeFi tick-data store. Also: `solana-defi{,-prd}`/`evm-defi{,-prd}` are themselves already
   DELETED (2026-07-10) — nothing left there to delete either; the Aave/marinade "unique gap" data may have been lost
   in that deletion with no audit trail confirming it was checked first — this specific sub-question is ALREADY
   tracked as its own `[OPERATOR] P2` todo in `defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`
   (Cloud-Logging admin-activity check needed) — not re-filed here, just cross-linked.

2. **[P0, data-correctness, UNRESOLVED] `instrument_type=POOL` (uppercase) manifest rows regrew from 0 to 7.9M after a
   verified-clean fold, mechanism still unknown — and a related `dex_swaps` migration-completion claim conflicts with
   a fresh live count by an order of magnitude.** `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P3 todo
   claimed "0 POOL rows remain" (2026-08-05, verified via full corpus scan). `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`
   (2026-08-11) found 7,930,863 such rows. Two obvious mechanisms (live-writer regression, manifest-rebuild
   re-emitting stale casing) were directly ruled out by code read — root cause remains open. Checkbox realigned (Flip
   #6), zero-checkbox doc converted to todos (item 1 above) so the remaining DIAG/SCRIPT work is now dispatchable.
   **Related, NOT independently verified this run** (routing only, per Calibration's "no new measurement" rule):
   hunter batch B separately found `dex_swaps` migration-completion claims conflicting by ~3.26M rows across 4 docs
   (`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`, `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`,
   `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`,
   `defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md`) — none cross-reference each other. Given both threads
   involve the SAME manifest-consolidator/rebuild machinery and the SAME bucket, they may share a root cause. Routed
   to STEP 6 (below) rather than resolved — would require fresh live GCS/manifest reads beyond doc reconciliation.

3. **[P2, doc-hygiene] `market-data-tick-defi-prd`'s aggregator-routes 9th migrator spec shipped code targeting an
   unprovisioned bucket.** The 2026-08-08 decision to keep `aggregator-routes` a dedicated bucket cited `gas-fees`/
   `liquidations` as precedent — but both had ALREADY been retired to the shared bucket by the time that decision was
   made (07-10/07-12 vs 08-08). Fixed (Flip #3).

4. **[P1, unbannered supersession] PACIFICA-SOLANA decommission decision superseded by a later operator reversal, no
   banner.** Fixed (Flip #7); confirmed live in `/codex/04-architecture/solana-defi-coverage.md`.

## Doc-drift / routed to STEP 6 (not auto-fixed — needs either fresh live investigation or operator awareness)

- **Contradiction #2's `dex_swaps` cross-doc row-count conflict** — genuinely needs a fresh live manifest read to
  adjudicate, which is out of scope for doc reconciliation alone. Recommend: (a) the 4 docs get cross-linked to each
  other so the next worker on any one of them sees the others, (b) a dedicated data-engineering investigation
  (not this reconciler) re-measures the live `dex_swaps` captured-row count and reconciles against all 4 claims.
- **`defi_manifest_index_catastrophic_shrink_2026_08_16.md`'s "159M→138K catastrophic shrink" claim** (hunter batch C)
  looks like it may conflate two distinct bucket KINDS (`instruments-store-defi-prd` vs `market-data-tick-defi-prd`)
  — the doc's own `[OPERATOR] P0` "halt the consolidator" order is premised on this comparison. Not independently
  re-verified this run (would require a fresh live bucket-identity check). Flagging for operator/next-pass attention
  given the severity (a live P0 halt-order may be based on a bucket mix-up) — **NOT resolved, NOT auto-fixed**.
  **UPDATE 2026-08-16 (slot-32, data_engineering root-cause task `defi_manifest_index_catastrophic_shrink-a4d9f031deba`)
  — CONFIRMED, this hunch was correct.** Pulled 40h of Cloud Run execution logs for
  `uts-prod-manifest-consolidator-instruments-defi` — `instruments-store-defi-prd-central-element-323112`'s canonical
  index has been stably ~138,468-138,612 rows the whole window, never larger. Live `gcs_describe_object` confirms
  `market-data-tick-defi-prd-central-element-323112` (the bucket the 159M/6.8GiB figure actually describes) is fully
  intact: 7,147,986,304 bytes, actively growing, last written 2026-08-16T18:03Z. No data loss occurred; the
  consolidator's merge logic behaved correctly throughout. Full evidence + retraction in
  `defi_manifest_index_catastrophic_shrink_2026_08_16.md`'s banner + "Root cause investigation" section (now
  `status: resolved`, all 4 recommended-decision todos resolved as moot/covered).
- **`defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e)** — a ready-to-fire 133M-row prod write
  against the bucket the 159M figure actually belongs to, relying on the same consolidator machinery
  `defi_manifest_index_catastrophic_shrink_2026_08_16.md` suspects may be defective. Worth operator awareness before
  it fires; not independently adjudicated this run.
  **UPDATE 2026-08-16 (slot-32)** — the consolidator machinery is now CONFIRMED not defective (see the update above);
  the "may be defective" premise is cleared, so this todo no longer needs to wait on that question. Not otherwise
  re-adjudicated by this update — the todo's own content/timing is unrelated to this specific concern.
- **`defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md`** (hunter batch B) claims an "undocumented"
  scheduler pause, but the pause + its resume-gate ARE already tracked in `defi_consolidated_closeout_2026_07_18.md`
  Track 8 (a wrong-vocabulary grep miss, not a real gap) — and the new doc's own proposed safety re-check
  (`mtds-<op>-backfill` VM-name pattern) would not catch the actual gating VM
  (`canonical-migration-defi-rebuild-*`). Not fixed this run (would need to rewrite the new doc's safety-check
  methodology) — flagged for next pass or operator attention before anyone resumes those schedulers based on the new
  doc's check alone.

## Refuted (dropped by verify)

- Hunter batch A's finding #8 ("a prior plan_reconciler pass today introduced a wrong `/issues/`-segment path") —
  checked live against the current file (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md:424`): the path is
  already correct, no `/issues/` segment present. Either the hunter misread it or it was already fixed by the time of
  this check. Not applied.

## Coverage / hunter tally

- 7 hunters, 126 docs (+4 already deep-reconciled inline = 130/130 tranche docs read in full).
- Candidates returned: ~15 contradictions/self-contradictions, ~10 missed-flip candidates, 2 zero-checkbox docs
  (both converted), ~10 AO-dispatch-readiness issues, ~12 dangling-ref/hedge-pointer findings, ~20 other notable
  findings (stale frontmatter, stale progress-table counts, a `sequential: true` violation, a checkbox with zero
  completion evidence, non-standard checkbox markers, etc).
- This checkpoint covers the highest-confidence/highest-severity subset. Remaining lower-priority items (see hunter
  reports) continue in the next checkpoint(s) of this same run.

## Checkpoint 2 — additional fixes applied

- `data_pipeline_check_mdps_features_2026_07_20.md` — 2 stale gates annotated (both cited blocking docs are now
  `status: resolved`/archived; gates cleared 19 and 10 days ago respectively, never re-checked). Not re-attempted
  myself (out of plans/**-only scope), flagged for the next dispatch.
- `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — 2 todos flipped `[ ]`→`[x]`: same-day (2026-08-16)
  operator rulings in this doc's own Progress Log were never propagated to their todos (DEX-relevance TVL fallback
  WON'T-DO; prediction cross-AG pointer resolved-as-stale).
- `defi_satellite_ao_dispatch_batch6_2026_07_30_finalize.md` / `..._batch9_2026_08_06_finalize.md` — stale
  gate-status banners corrected (both parent batches are now fully `[x]`, both finalize plans are gate-clear and
  dispatch-ready; the banners still said "1 of 26 open" / "batch9 stays draft").
- `solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md` — todo 4 flipped `[x]`, per its own text
  ("should be closed alongside todo 3", which was already `[x]`).
- `instruments_docs_audit_outstanding_items_2026_07_08.md` — fixed 6 of 8 `related:` paths (archived since filing;
  the doc's own `context_scope` already had 2 of these correct, proving the drift was real) + added leading slashes
  per the cross-reference convention.
- `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — resolved a hedge-pointer ("out of scope for this
  pass", uncited) by citing where the deferred item is actually tracked
  (`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:472-483`).
- **Meta-finding**: my own `/blocked` post (BLK-9b43a627, the bucket-identity halt-order question) reproduced the
  SAME-DAY `ao`-tranche-filed infra bug (`plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md`) — the
  operator's answer ("A") never reached `GET /api/slots/6/messages`, only recoverable via `GET /api/activity` as
  `event_type: blocked_message_orphaned_by_reassign`. Added this as new evidence to that existing tracked doc rather
  than re-filing — the event-type name is a genuinely new diagnostic clue (points at task/slot reassignment as the
  likely mechanism) that the first report didn't have.

## Plans not reached (yet)

Remaining lower-priority items from the hunter reports not yet applied (elysium progress-table 4 stale counts, a
`sequential: true` process-order note on `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`, the
`defi_turbo_api_hides_real_captured_data_2026_07_07.md` moot-premise todo, a handful of P3 frontmatter/cosmetic
items) — left for a future pass; none carry live-risk or data-correctness stakes.

## Split finding (routed, not fixed)

`plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` is **1005L, over the 1000L hard
cap** — discovered when a small, unrelated hedge-pointer citation fix (batch G's finding) got blocked by
`check_line_caps` on ANY staged change to this file. This is pre-existing (confirmed: reverting my edit still leaves
it at 1005L at HEAD) — not caused by this run, and apparently never surfaced before because the pre-commit line-cap
check only fires on staged files, and nobody had staged a change to this specific doc since it crossed the cap.
Reverted my citation-fix edit rather than trim someone else's content to force it under cap (splitting a plan is an
operator-gated planning decision per CLAUDE.md, not a mechanical trim). The hedge-pointer fix itself
(deployment-api PREDICTION_DATA_TYPE_META retirement — actually tracked in
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:472-483`) is still valid and can be reapplied
once this doc is split.

## Progress Log

- **na-eligibility-audit 2026-08-16** [body-hash:6ed0e2abbbdcefbe]: KEEP-NA, valid — 0 open '- [ ]' todos confirmed
  via grep (matches Phase-0), but this doc is not a task-tracking plan/issue doc in the usual sense — it is
  plan_reconciler's own live run-journal for the 2026-08-16 defi-tranche dispatch (agt-1a88e0), at the time of this
  verdict still self-described as "Run in progress" and `locked_by: plan_reconciler-agt-1a88e0` with `status: open`.
- **2026-08-16 (plan_reconciler /plan-reconcile Phase -1, separate dispatch reconciling this doc against fresh
  state)**: `agt-1a88e0`'s own last commit landed 2026-08-16T18:34:45Z (the manifest-catastrophic-shrink retraction);
  no live AO dispatch to slot 6 remains (fleet-wide backlog check: 0 tasks dispatched to slot 6, `dispatched: 2`
  fleet-wide total at check time, ~3h after the last commit) — confirmed dead per the same evidence class (git-log
  gap + AO dispatch-status cross-reference) `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` uses, whose Option A
  (2026-08-15 operator ruling: "once AO confirms a dispatch id is reaped-stale, the lock auto-clears without a human
  step") is the precedent applied here — `locked_by:` cleared above. This doc is NOT fully resolved (genuine open
  work remains, listed below) so it stays in `plans/active/issues/`, unlocked rather than archived.
  - Verified `defi_manifest_index_catastrophic_shrink_2026_08_16.md`'s STEP-6 "not yet resolved" item IS now resolved
    and archived (`plans/archive/2026_08/issues/defi_manifest_index_catastrophic_shrink_2026_08_16.md`) — the doc's
    own text above already reflects this correctly; no further action.
  - Cross-linked the 4 `dex_swaps` row-count-conflict docs the STEP-6 section recommended linking: added the missing
    cross-references to `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (had 0 of 3) and
    `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` (had 1 of 3, now 3 of 3) — the row-count
    conflict itself is still NOT resolved (needs a fresh live manifest read, out of scope for doc reconciliation).
  - `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` re-checked: still 1005L, still over the 1000L
    hard cap. STILL-OPEN — genuine split work (operator-gated per CLAUDE.md: "splitting a plan is a planning
    decision"), not attempted here given the risk of corrupting content mid-split without a dedicated pass.
  - `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) re-checked: still `[ ]` open, as
    expected — the STEP-6 update already correctly noted only the "consolidator may be defective" premise was
    cleared, not the todo itself.
  - `defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md` re-checked: still `status: open`, still
    genuinely unactioned (real scheduler-pause investigation work, not a doc-hygiene gap) — left as-is.
  - `defi_turbo_api_hides_real_captured_data_2026_07_07.md` re-checked: still `status: open`, no `resolved_by` —
    still a live P0 data-correctness finding, correctly tracked, nothing new needed from doc reconciliation.
  - "Plans not reached" section's remaining low-priority items (elysium progress-table stale counts,
    `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`'s `sequential: true` note, and the elysium doc's
    exact stale-count location) were spot-checked where cheap: `batch3_finalize`'s `sequential: true` is already
    self-explained in its own body text ("todo 2 ..."), likely already a non-issue; the specific elysium
    progress-table doc could not be pinpointed among 5 candidate docs matching "elysium" in a quick grep — left
    unresolved, low priority (original run: "none carry live-risk or data-correctness stakes").
