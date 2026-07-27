---
doc_type: plan
title: Prediction satellite AO batch 2 — re-triage clearance from batch1's Deferred set
summary: >-
  Second AO-dispatch batch for prediction, produced by re-invoking the `/ag-closeout-audit` skill's "batchN methodology"
  against `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`'s own Deferred section (12 fully-deferred orphaned
  docs + the excluded item 9 of `prediction_phase_ab_residuals_2026_07_24.md`) — NOT a fresh 13-agent triage, a cheap
  re-check of each item's already-logged conflict against the CURRENT content of
  `prediction_consolidated_closeout_2026_07_18.md` and batch1 itself, per the skill's step-1 "before fresh Phase-1
  triage, re-check the prior batch's Deferred section first" rule. Of the 12 deferred docs + item 9 (13 total
  candidates), 8 cleared conflict-free (corrected 2026-07-25 plan-reconcile — was miscounted as "6 cleared" while the
  same sentence's own breakdown summed to 8: 2 were pure duplicates of work batch1 already extracted, so contribute no
  new todo; 6 produced genuinely new, conflict-free AO-eligible todos below, matching this doc's actual 6 dispatchable
  todos); the remainder stay genuinely blocked (duplicate-of-batch1, 0-AO-eligible-content, or operator-gated) and are
  re-recorded in Deferred with an explicit current-state note per item, per the skill's non-batchable taxonomy.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-2, satellite-docs, conflict-checked, re-triage]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25" # same-day correction (consolidated-closeout split pass): phase_ab_residuals open-count refs corrected 10/11 -> 13; the POLYMARKET schema-extension pointer corrected to phase_ab_residuals' A2 todo (was the parent's now-relocated "Queued audits + reviews")
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Re-triage session 2026-07-25, driven by the `/ag-closeout-audit` skill's "batchN methodology" (cursor-configs skill
  doc, added 2026-07-25) re-checking `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`'s own Deferred section
  against the CURRENT content of `prediction_consolidated_closeout_2026_07_18.md` and the original triage journal
  `subagents/workflows/wf_b8829ea8-6cd/journal.jsonl` (13 per-doc agent results, re-read, not re-run).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 2 — re-triage clearance

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 6 todos below are same-priority and touch disjoint files (verified below); none require
> `sequential: true`.
>
> **Why these 6 cleared when batch1 held them back**: batch1 conservatively deferred every candidate whose source-doc
> agent logged ANY conflict, even where (per re-read) the conflict didn't actually touch the specific candidate item, or
> the "other side" turns out to be a citation-only index entry / a demonstrably stale claim / already covered by a
> DIFFERENT batch1 todo. This batch extracts only the items where that re-check resolves the conflict by evidence, not
> by guessing — see each todo's inline resolution note and the Deferred section for what's still genuinely blocked.

## Todos

- [x] ✅ [DIAG] P1. **DONE 2026-07-27 (slot-11).** Verify + flip the stale `manifest_master.md` P2 "Prediction bucket
      naming migration" checkbox (currently `[ ]` unchecked at `plans/epics/manifest_master.md:261`). The target legacy
      prediction buckets (`market-data-tick-prediction-*`, `instruments-store-prediction-*`) were already purge-deleted
      2026-07-13 per `plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md` ("prediction: ✅ DONE
      2026-07-13" — confirmed 404, both live + noncurrent versions purged). Grep `market-tick-data-service` +
      `instruments-service` prediction code paths for any remaining inline legacy bucket-name string literal not routed
      through `resolve_bucket_name()` (STEP 5.69). Repo: unified-trading-pm docs (read-only verification against
      market-tick-data-service, instruments-service). **Resolution note**: originally excluded from batch1 because the
      source doc (`issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`) logged 2 conflicts — but both
      conflicts are about that doc's OTHER 2 prose-only items (the raw_tick_data stall + the dead Kalshi host, already
      covered by batch1 todo 1), not about this checkbox-flip candidate, which has zero conflicts of its own. **Done
      when**: `plans/epics/manifest_master.md`'s "Prediction bucket naming migration" P2 line is either flipped to `[x]`
      with the grep result + decommission-plan citation as evidence, or left open with a dated note naming the exact
      non-compliant file:line(s) found — never silently dropped. Source:
      `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`. **Result: flipped to `[x]`** — every LIVE
      production code path in both repos already routes through `resolve_bucket_name()`; the only raw legacy-literal
      hits are in dated, already-completed one-off migration/reconciliation/purge scripts targeting the now-deleted
      bucket. See `plans/epics/manifest_master.md`'s flipped line for the full grep-result citation.
- [x] ✅ [DIAG] P1. **DONE 2026-07-27 (slot-4).** **Conflict-check (2026-07-25 plan-reconcile)**:
      `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 7 ALSO writes to
      `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log. Do not dispatch/commit concurrently with that todo —
      batch1 was drafted first, run batch1 todo 7 before this todo if both are active. **Collision check before
      starting**: verified via the live backlog (`prediction_satellite_ao_dispatch_batch1-007`) that batch1 todo 7 was
      `status: queued`, `dispatched_to: null` — not concurrently active — so no same-file collision risk at execution
      time; proceeded. **Re-verify the `instrument_type` casing/canonicalisation residual with the CORRECT
      (case-insensitive) comparison rule, and reconcile `prediction_phase_ab_residuals_2026_07_24.md`'s item-9
      checkbox.** Run a fresh READ-ONLY live read of the prediction manifest (`availability_index.parquet` / the live
      `GET /data-status/catalogue-filter-options` endpoint), comparing the `instrument_type` column
      **case-insensitively** — per the RULED codex standard (`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1:
      C2a is RULED UPPERCASE-target, `migration_pending`, operator D1 2026-07-20 — "the reconciliation does NOT REFUSE
      the axis... compares case-INSENSITIVELY and emits NO casing finding during the migration_pending window") — to
      quantify ONLY genuinely malformed (non-casing) `instrument_type` rows, i.e. re-verify the 2026-07-20 census's F2
      106-row (0.014%) residual (`prediction` singular + `None`) is still accurate today. **Do NOT run**
      `canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers --apply` against the 4,001-row lowercase
      `prediction_market` tail — converting THAT casing is the actual D1 migration, and it stays blocked on the still-
      open D1 migration-sequencing gate for this specific `--apply`
      (`plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md` —
      **UPDATE 2026-07-25: that issue's harness-compatibility fix has since SHIPPED + is resolved/archived**
      (`instruments-service@867b68f6`, all 4 todos done) — the harness-compatibility precondition is now MET; any
      remaining hold on running this `--apply` is a separate D1-migration-execution decision, not this gate) — applying
      it now would still need that separate sign-off. Repo: market-tick-data-service (`availability_index.parquet`,
      read-only). **Resolution note**: this is `prediction_phase_ab_residuals_2026_07_24.md`'s item 9, excluded from
      batch1 for conflicting with `prediction_consolidated_closeout_2026_07_18.md`'s "instrument_type casing gap to
      literal 100%" framing. Re-check finds that framing (its "Distinct Values" section, lines 213-215:
      "`prediction_market` (lower) 4,001 (0.54%, **C2a REFUSED** — unruled axis, no migration proposed)") is ITSELF
      stale — the codex SSOT it should have cited documents C2a was RULED (not refused) the SAME day (2026-07-20) it
      measured this census. The conflict clears by evidence (the "other side" is a provably-superseded claim), but the
      original item-9 done-when ("literal 0 non-canonical rows") is narrowed here to the case-insensitive standard the
      ruling actually mandates, to avoid extracting a migration-execution step that's still gated shut elsewhere. **Done
      when**: a fresh case-insensitive live read's malformed-row count + timestamp is recorded in
      `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log, and its item-9 checkbox (lines 276-286) is flipped
      `[x]` if the count is 0 or explained if non-zero — citing the read, never re-citing either historical (2026-07-19
      or 2026-07-20) snapshot as current. Source: `prediction_phase_ab_residuals_2026_07_24.md` (item 9).

      **Result**: fresh live read (2026-07-27T15:28:46Z) of `market-data-tick-pred-prd-central-element-323112`'s
                                  `availability_index.parquet` `instrument_type` column (785,035 rows) found **176 genuinely malformed, non-casing
                                  rows (0.0224%)** — non-zero, so item 9's checkbox stays `[ ]` (explained, not flipped): 76 rows literally
                                  `prediction` (singular, unchanged since the 2026-07-20 baseline — dead residue) + 100 blank/null rows, which are
                                  **NOT static** — 30 (2026-07-20) → 70 (2026-07-24) → 100 (2026-07-27), a consistent ~10 rows/day linear growth,
                                  evidence of an ACTIVE writer defect. Filed a new `[DIAG] P2` todo in `prediction_phase_ab_residuals_2026_07_24.md`
                                  (Phase B) to track finding the responsible writer path, and recorded the full read (count breakdown + casing-
                                  variant context + timestamp) in that doc's Progress Log — `unified-trading-pm@<pending>`.

- [x] ✅ [AGENT] P1. **DONE 2026-07-27 (slot-6).** **Predictions MTDS `canonical_question_group` completion-% slice** —
      compute per-(canonical_question_group, day) completion % against the live manifest's
      `prediction_canonical_question_group` bundle rows
      (`asset_group=prediction, venue, data_type=prediction_canonical_question_group,     canonical_question_group, day`),
      using the already-shipped UAC `CANONICAL_GROUP_METADATA` per-group cadence/expected-count table
      (`unified_api_contracts.canonical.domain.predictions.canonical_groups`): HOURLY = 24 expected/day, DAILY = 1,
      ELECTION = 1. Read-only analysis; no code change. Mirrors the already-completed sports MTDS-slice precedent
      (`sports_master.md`'s "Per-source completion %" entry). Repo: unified-trading-pm (analysis only; reads
      `unified-api-contracts`'s `CANONICAL_GROUP_METADATA` + the live prediction manifest). **Resolution note**: the
      only flagged conflict was against `prediction_consolidated_closeout_2026_07_18.md`'s "ML / arb (downstream,
      gated)" section — re-read confirms (as the original triage agent itself already noted) that section is explicitly
      a pure citation/index entry ("Format: path → its currently-OPEN todos only" per the section's own framing, line
      277), not new work the closeout doc owns; it does not touch this item from any angle. No genuine conflict; the
      original flag was over-cautious. **Done when**: a completion-% table per (canonical_question_group, day) —
      captured/empty_confirmed/expected_unattempted counts and the resulting %, broken out by HOURLY/DAILY/ELECTION
      cadence — is recorded in `predictions_ml_walk_forward_and_arb_2026_06_20.md`'s Progress Log (or a linked dated
      analysis doc), and that item's checkbox is flipped. Source: `predictions_ml_walk_forward_and_arb_2026_06_20.md`.

      **Result**: 68,667 `prediction_canonical_question_group` bundle rows read (single-walk, column-pruned,
                              filter-pushdown) from `market-data-tick-pred-prd-central-element-323112` at 2026-07-27T16:01:28Z → 36,039 distinct
                              (cqg, day) rows; 82/97 registered canonical_question_groups have ≥1 live manifest row. Per-cadence
                              captured/empty_confirmed/attempted_failed/expected_unattempted counts + reachable_coverage % recorded in
                              `predictions_ml_walk_forward_and_arb_2026_06_20.md`'s Progress Log; its own line-89 checkbox flipped
                              (unified-trading-pm@9df4924c0). Finding surfaced (new `[DIAG] P2` todo filed in that same doc, not fixed here):
                              8 registered groups (`BTC_UP_DOWN_HOURLY`/`ETH_UP_DOWN_HOURLY`/`*_5MIN`/`*_INTRADAY`/`ELECTION_PRESIDENT_2028`/
                              `OSCARS_BEST_PICTURE`) have ZERO manifest rows of any capture_status — genuinely absent, not merely low
                              completion.

- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-11).** **Prediction sentinel fan-out for zero-trading-day CQGs** —
      market-tick-data-service's prediction manifest finalize function `_finalize_prediction_bundles`
      (`market_tick_data_service/engine/orchestrator/manifest_finalize.py`) only emits a
      `data_type=prediction_canonical_question_group` manifest row for CQGs present that day in
      `state.prediction_cluster_counts_by_venue`; a `canonical_question_group` with zero markets trading on a given day
      gets NO manifest row at all (not `empty_confirmed`, not anything) — the manifest denominator + deployment-ui
      drilldown silently omit inactive CQGs instead of showing an honest 0%. Fix: after the existing
      per-`(pred_venue,     cqg_str)` loop over `cqg_counts`, fan out
      `pred_writer.record_empty(reason="SOURCE_RETURNED_ZERO", ...)` — mirroring the row_key shape the adjacent
      `record_captured_from_counts`/`record_failed` calls in the same function already use — for every
      `CanonicalQuestionGroup` enum member (`unified_api_contracts.canonical.domain.predictions.canonical_groups`) NOT
      present as a key in that venue's `cqg_counts` for the processing date. Repo: market-tick-data-service.
      **Resolution note**: the flagged conflict is `prediction_phase_c_data_status_ui_2026_07_24.md`'s own P1 todo,
      which bundles ALL 3 of this doc's open items under one claimed closure — but that phase_c todo is machine-gated
      (`depends_on: [prediction_phase_ab_residuals_2026_07_24], gate_on_depends: true`) and
      `prediction_phase_ab_residuals_2026_07_24.md` still has 13 open todos (**corrected 2026-07-25 consolidated-
      closeout split, was 10** — that doc gained 2 relocated todos from the parent's former "Queued audits + reviews"
      section the same day), so the gate has not opened and cannot race this todo. Once this ships, batch2-finalize
      cross-links it in `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` so phase_c's future bundled closure
      finds it already done, not re-attempted. **Done when**: a new/extended unit test in market-tick-data-service
      (extend `tests/unit/engine/test_manifest_finalize_coverage.py`) proves that for a processing date with ≥1 CQG
      absent from `state.prediction_cluster_counts_by_venue` for a venue, `_finalize_prediction_bundles` now emits an
      `empty_confirmed[SOURCE_RETURNED_ZERO]` `prediction_canonical_question_group` manifest row for that (venue, cqg,
      day) instead of omitting it; `quality-gates.sh` is green. Source:
      `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`.

      **Result**: added a fan-out loop in `_finalize_prediction_bundles` (after the existing per-`(pred_venue, cqg_str)`
          loop) that iterates every `CanonicalQuestionGroup` enum member not present in that venue's `cqg_counts` for the
          processing date and calls `pred_writer.record_empty(reason="SOURCE_RETURNED_ZERO", ...)`, mirroring the row_key
          shape of the adjacent `record_captured_from_counts`/`record_failed` calls and reusing the Tier-3 pattern's
          `_reached_empty_fetch_evidence` helper (`sentinels.py`) to prove honest absence (the venue's whole market universe
          was already reached+scanned that date, so a CQG's absence from `cqg_counts` is a proven reached-but-empty result,
          not an unattempted fetch — satisfies the writer's `UnprovenHonestAbsenceError` gate on `SOURCE_RETURNED_ZERO`).
          New test `test_finalize_prediction_bundles_emits_sentinel_for_absent_cqg` in
          `tests/unit/engine/test_manifest_finalize_coverage.py` proves the sentinel fires with the correct reason + a
          `fetch_evidence` that `proves_honest_absence()`, and that every registered CQG except the one captured that day
          gets exactly one sentinel row. `quality-gates.sh` green (7163 passed). Shipped
          `market-tick-data-service@9a8b96c1`. Also flipped the corresponding source-doc item — see
          `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`'s P2 "prediction sentinel fan-out" checkbox.

- [ ] [SCRIPT] P1. **Combined residual-row diagnosis for `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`
      (2 sub-items merged into one todo since both snapshot-then-write against the SAME prediction manifest `_index`,
      avoiding a concurrent-write race):** (a) Diagnose and, only if confirmed safe, purge the 17 blank-`data_type`
      phantom aggregate-marker rows in the live prediction `_index` manifest
      (`market-data-tick-pred-prd-central-element-323112`) — re-verify each row's supersession/genuine-phantom status
      following the `purge_prediction_index_final_residuals_2026_07_11.py` precedent pattern (snapshot-then-write,
      stop-on-surprise re-verify immediately before any delete). (b) Verify the current live count of
      `batch_polymarket_clob` blank-`source` rows — the source issue measured 27,292 such rows on 2026-07-10, but the
      later 2026-07-19 `canonicalize_prediction_manifest_2026_07_18.py --dry-run` measured only 2, suggesting this was
      already resolved by that migration's `--apply`; if the live count is still material (thousands, not ~0-2),
      backfill `source=polymarket_clob` via a targeted rebuild scoped to just this row predicate. Repos:
      instruments-service (new one-off diagnose+purge script), market-tick-data-service (targeted backfill script or
      scoped invocation of the existing canonicalizer). **Downgraded from `[OPERATOR]` 2026-07-27**
      (reversibility-verified, finding T, `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a): part (a)
      purges and part (b) overwrites rows in the prediction `_index` Parquet, an object living in
      `market-data-tick-pred-prd-central-element-323112` — a fresh check confirms that bucket's GCS Soft Delete
      retention is `604800s`, so both mutations are recoverable within the window like an object delete, not the
      irreversible class the codex's Part-2 proof exists for. snapshot-then-write stays required as-is. **Resolution
      note**: the 3 flagged conflicts are about DIFFERENT residual row-sets in this same issue doc (the 189
      blank/UNKNOWN-venue rows and the ~2,414 schema-v4/v5 rows — neither is one of these 2 candidates) or document that
      `prediction_phase_ab_residuals_2026_07_24.md`'s "steps 1-4 landed" / "residuals 5-6 — DONE" checkmarks OVER-CLAIM
      this doc's actual remediation state (the doc's own 2026-07-11 Update explicitly says the 17 blank-`data_type`
      rows + this 27,292-row count were NOT touched by that pass) — which CONFIRMS, rather than blocks, that these 2
      items are still genuinely open, not already-done duplicates. **Done when**: for (a), a fresh live read of the
      17-row predicate is recorded (count + capture_status breakdown), and either each row is confirmed superseded and
      purged via a snapshotted write with the row-count delta logged, or confirmed as the sole surviving evidence and
      explicitly left in place with that finding recorded; for (b), the live `batch_polymarket_clob` blank-source count
      is measured and cited, and either the backfill ran with a before/after delta logged, or the item is recorded as
      already-resolved with the confirming count. Both recorded in
      `plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`'s Progress Log in the same
      commit. Source: `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5, review)** — Reconcile
      `prediction_universe_capture_dead_since_07_01_2026_07_06.md`'s stale `status: open` against its already-shipped
      fix chain** — confirm `market-tick-data-service@a664511f` (Root Cause #4: composite `VENUE:TYPE:BARE_ID` lifecycle
      market_id → bare per-venue id normalization in `_load_market_lifecycle_for_date`), `instruments-service@1fa9177f`
      (Root Cause #5: per-venue `{group,day,venue}` `market_lifecycle` partition — POLYMARKET no longer clobbers
      KALSHI), and `market-tick-data-service@d2040f8f` (Root Cause #6: Kalshi millisecond-vs-second timestamp fix) are
      all present on `live-defi-rollout`/`main` in their respective repos (`git log`/`git branch --contains`, not merely
      a feature branch); confirm the production capture proof cited in
      `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s 2026-07-14T11:00Z entry (423 captured trades
      rows / 6,407 Kalshi trades for day=2026-07-09) still holds; then append a dated Progress Log entry citing all
      three SHAs + the corroborating doc and flip the target doc's frontmatter `status: open` → `status: resolved`.
      Repo: unified-trading-pm. **Resolution note**: `prediction_consolidated_closeout_2026_07_18.md`'s index already
      claims this doc has 0 open todos — substantively correct per this re-check, but never actually verified or
      recorded anywhere; this todo makes that closure real+cited instead of an unverified assumption. The doc's own
      Root-Cause-#2 event-capture-gap question is separately and already covered by batch1 todo 2 (dupes that ground —
      not re-extracted here). **Done when**: the target doc's frontmatter `status` reads `resolved`, a new dated
      Progress Log entry cites all three commit SHAs by hash and names
      `kalshi_live_capture_regression_and_drift_2026_07_13.md` as the corroborating production proof, and ancestry on
      `live-defi-rollout` is confirmed for all three. Source:
      `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`.

      **Evidence**: all 3 SHAs confirmed on `live-defi-rollout` (`git merge-base --is-ancestor`) AND `main`
                                              (content-diff, since these repos squash-merge on promote — distinctive marker lines from each commit found
                                              live in `origin/main`'s copies). Production capture proof re-verified live: `venue=KALSHI, data_type=trades,
                                              date=2026-07-09` in the prediction manifest returns exactly 423 `captured` rows summing to 6,407 — an exact
                                              match to the cited 2026-07-14T11:00Z proof, still holding. `status` flipped to `resolved`, `resolved_by`
                                              populated, dated Progress Log entry added — unified-trading-pm@`<pending>`.

## Deferred — still genuinely blocked after re-check (NOT dispatched)

Per the `/ag-closeout-audit` skill's non-batchable taxonomy, each item below is tagged with WHY it stays deferred — none
of these clear by re-check; a future batch3 should re-check them again only if their named blocker has changed.

- **`prediction_phase_ab_residuals_2026_07_24.md` items 1-3, 5, 7 (5 of batch1's own 7 todos)** — DUPLICATE-OF-BATCH1
  (already dispatched there, not re-extracted). No new state.
- **`issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`** — ADDED 2026-07-25
  plan-reconcile (was silently missing from this Deferred section despite being one of batch1's original 12 deferred
  docs). DUPLICATE-OF-BATCH1: its sole AO-eligible open item (line 115, a `[VERIFY] P2` re-measure of prediction
  attempted/captured trajectory) is substantively identical to batch1 todo 4, which writes its before/after counts into
  this exact same doc's Progress Log. No new todo needed here.
- **`data_completion_prediction_2026_07_15.md`** — 0 AO-eligible (21 human-only items unchanged), 3 conflicts logged
  against the doc generally (FLAG-3/FLAG-2 cross-AG duplication risk, a Phase-B-naming ambiguity between two different
  "Phase B"s). Re-check: none of the 3 conflicts are individually resolvable by evidence today (they're genuine
  cross-doc ownership/naming ambiguities, not stale claims) — OPERATOR-GATED, unchanged from batch1.
- **`issues/prediction_arb_live_execution_bridge_2026_07_20.md`** — 0 AO-eligible; its own text names "the single
  remaining LIVE blocker (needs an OPERATOR-DIRECTED architectural decision)" — GENUINELY HUMAN-ONLY, already
  self-documented as needing an operator call (not a new ambiguity this session is surfacing). Separately,
  `prediction_consolidated_closeout_2026_07_18.md`'s index wrongly claims this doc has "0 open todos" (contradicted by
  the doc's own prose) — a documentation-accuracy finding, not new dispatchable work; noted for the operator, not
  actioned here.
- **`prediction_phase_c_data_status_ui_2026_07_24.md`, `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`,
  `prediction_phase_e_football_arb_live_2026_07_24.md`** — 0 AO-eligible each (all remaining work is either
  machine-gated on `prediction_phase_ab_residuals_2026_07_24.md`'s 13 open items (**corrected 2026-07-25 consolidated-
  closeout split, was 11** — that doc gained 2 relocated todos from the parent the same day; phase_d itself also grew
  from 3 to 6 open items via the same relocation, still all 0-AO-eligible on re-check), or is itself the human-scale
  post-migration smoke/backfill/football-arb work the consolidated plan scopes as a dedicated phase, not a bounded
  solo-worker todo). Unchanged from batch1.
- **`issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`** — both of its 2 AO-eligible
  candidates are DUPLICATE-OF-BATCH1 (batch1 todo 5 already combines the exact same grep-then-READ +
  title/slug-recoverability investigation). No new todo. The doc's OWN Q3/Todos (the operator-ruled POLYMARKET
  `prediction_trades` schema-extension migration) are **corrected 2026-07-25 (consolidated-closeout split, corpus-wide
  referrer fixup)** — no longer tracked in `prediction_consolidated_closeout_2026_07_18.md`'s "Queued audits + reviews"
  (that section was forked out the same day); the ruling + 3-step sequence now live folded into
  `prediction_phase_ab_residuals_2026_07_24.md`'s existing A2 dual-write-trees todo (Phase B section) — not this batch's
  concern either way. The data_type=`prediction_trades` axis-disposition conflict flagged against this doc (open
  question vs. already-applied fold) stays OPERATOR-GATED — the doc's own 2,477-row live measurement (most recently
  written 2026-07-23) genuinely contradicts the "already durable" claim elsewhere and needs the operator to reconcile,
  not a re-triage guess.
- **`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`'s other 2 items** (Phase-5 canonical-groups backfill, the
  `[VERIFY][UI]` deployment-ui drilldown re-walk) — not AO-eligible per the original triage (UI/design-adjacent, needs
  the writer fix this batch's sentinel-fan-out todo ships first); re-check unchanged.
- **`issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`'s secondary conflicts** (the MVP-backfill-gate
  overlap on its 12 dishonest `empty_confirmed` cells, the adapter-file collision-awareness note) — correctly not
  drafted as separate todos per the original triage; the broader MVP backfill gate stays Phase-D's P0, unchanged.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`
(`depends_on: [prediction_satellite_ao_dispatch_batch2_2026_07_25]` + `gate_on_depends: true`), mirroring the batch1
finalize pattern.

## Codex SSOTs

`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1 (C2a instrument_type-casing ruling, load-bearing for todo 2's
resolution — read before touching that todo). No new durable contract is created by this plan — every todo executes an
already-decided spec from its source doc or an already-RULED codex standard.

## Progress Log

### 2026-07-27 (slot-11) — Todo 1 done: prediction bucket naming migration verified complete, checkbox flipped

Picked up todo 1 via `/boot`. Confirmed the legacy prediction buckets are purge-deleted (404) per
`legacy_bucket_dual_write_decommission_2026_07_24.md`. Grepped both `market-tick-data-service` and `instruments-service`
for remaining inline legacy prediction bucket-name literals not routed through `resolve_bucket_name()`: every live
production code path (`reader.py`, `live/websocket_runner.py`, `engine/orchestrator/__init__.py`,
`market_interface/adapters/prediction/*`, `cli/handlers/websocket_streaming_handler.py`,
`instruments_service/engine/orchestrator/catalogue.py`) already calls
`resolve_bucket_name(kind="market-data-tick-prediction"/"instruments-store-prediction", ...)` — the dedicated flat-kind
SSOT pattern. Spot-checked the two most ambiguous hits (`engine/orchestrator/__init__.py:806-815`,
`instruments_service/engine/orchestrator/catalogue.py:37-53`) directly to confirm the `kind=` string is passed INTO
`resolve_bucket_name()`, not used to construct a raw bucket name. The only raw f-string/literal bucket-name
constructions found (`f"market-data-tick-prediction-{PROJECT_ID}"` / `f"instruments-store-prediction-{project_id}"`) are
confined to dated one-off scripts under `scripts/*_2026_0[5-7]_*.py` (e.g. `migrate_prediction_to_pred_prd_v9.py`,
`purge_prediction_index_final_residuals_2026_07_11.py`, `reconcile_legacy_blank_to_typed_reason.py`) whose entire
purpose was migrating away from / auditing / purging the legacy bucket itself — verified one representative
(`migrate_prediction_to_pred_prd_v9.py`'s docstring) is the already-completed E2 migration step from
`prediction_manifest_canonicalisation_2026_06_01.md` (source plan for the decommission that already shipped 2026-07-13).
Flipped `plans/epics/manifest_master.md`'s P2 "Prediction bucket naming migration" checkbox to `[x]` with the full
grep-result citation, and this todo's own checkbox above. No code changed (read-only verification, as scoped). Repo:
unified-trading-pm only.

### 2026-07-27 (slot-4) — Todo 2 done: instrument_type casing residual re-verified case-insensitively, checkbox flipped

Picked up todo 2 via `/boot` (resumed session — task was `already_in_progress`). Per the todo's own collision-avoidance
note, first checked the live backlog for `prediction_satellite_ao_dispatch_batch1-007` (the mirror conflict-check in
batch1 that also writes to `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log): `status: queued`,
`dispatched_to: null` — not concurrently active, so no same-file collision risk; proceeded.

Read `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1 for the C2a ruling context, then wrote a small ad-hoc
read-only script (scratchpad, not committed) reusing `unified_trading_library.read_availability_index` +
`resolve_bucket_name` — the same slim, column-pruned, single-walk pattern deployment-api's `_axis_census.py` uses — to
census the live prediction manifest's `instrument_type` column at `market-data-tick-pred-prd-central-element-323112`.

**Result**: 785,035 total rows; 775,139 exact-uppercase `PREDICTION_MARKET` + 9,720 lowercase `prediction_market`
casing-variant (correctly excluded from the malformed count, `migration_pending` per C2a) + 176 genuinely malformed
non-casing rows (76 `prediction` singular, unchanged since 2026-07-20 — dead residue; 100 blank/null, which is NOT
static — 30→70→100 across 2026-07-20→07-24→07-27, a consistent ~10 rows/day growth, i.e. an active writer defect, not
closed history). Recorded the full read + this composition analysis in `prediction_phase_ab_residuals_2026_07_24.md`'s
Progress Log (item 9's checkbox stays `[ ]`, explained, since the count is non-zero — this todo's done-when only
required recording+explaining, not a zero result). Filed a new `[DIAG] P2` Phase-B todo in that same doc to track
identifying the writer path responsible for the growing blank count. This todo's own checkbox above is flipped `[x]` —
done-when met. No code changed (read-only measurement, as scoped). Repo: unified-trading-pm only (both edited docs).
