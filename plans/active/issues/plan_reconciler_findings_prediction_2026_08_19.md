---
title: Plan-reconciler findings — prediction tranche — 2026-08-19
created: 2026-08-19
author: plan_reconciler
source: agt-4a2f8b
locked_by: plan_reconciler (agt-4a2f8b) since 2026-08-19T15:20:03Z
doc_type: issue
status: active
nature: incident
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, prediction, findings, 2026-08-19]
related: [/plans/active/issues/plan_reconciler_findings_prediction_2026_08_16.md, /plans/active/issues/plan_reconciler_findings_prediction_2026_08_18.md]
---

# Plan-reconciler findings — prediction tranche — 2026-08-19

Daily deep reconciliation run, dispatch `agt-4a2f8b`, slot 7, tranche `prediction`. Sonnet-5, effort max, extended
thinking. Corpus: 49 docs (`generate_tranche_doc_inventory.py --tranche prediction`), PM repo FF'd to `8f22134b48` at
run start. 6 hunter sub-agents fanned out (2 Phase -1 reconcilers + 4 fresh-sweep batches covering all 49 docs), then
every candidate adversarially re-verified inline (direct Read + `git`/`find` checks) before any write.

## Phase -1 — prior findings docs reconciled

Both prior findings docs (`..._2026_08_16.md`, `..._2026_08_18.md`) were fully re-verified against fresh corpus state.
**Neither is archive-ready** and **both are inside this run's 12h grace window** (1h old — last touched by
`/ag-closeout-audit prediction`, slot-21, 14:06 UTC — confirmed NOT a concurrent `plan_reconciler` collision), so no
edits could be applied to either doc this run despite 2 confirmed auto-fixable items:

- **08-16 doc**: 8 items RESOLVED (reconfirmed via 6/6 SHA-ancestor checks — all genuinely landed), 1 AUTO-FIXABLE
  (flip the `mdps_fleet_duplicate_relaunch_explosion` `[OPERATOR]`-tag checkbox to `[x]` MOOT — the P1 item it
  questioned no longer exists), 1 NEEDS-RULING (batch11/phase_d duplicate P0 todos — see Filed below), 3 STILL-OPEN
  ORDINARY-WORK (no action needed).
- **08-18 doc**: 4 items RESOLVED (reconfirmed), 1 AUTO-FIXABLE (flip a DIFFERENT `mdps_fleet_duplicate_relaunch_explosion`
  checkbox — confirms the `[OPERATOR]` P0 tag on line 352 is correct, not a mistag, citing
  `agent-orchestrator/server/regen_backlog_from_plan.py:2209-2216`'s dispatch-blocking semantics for a bare
  `[OPERATOR]` tag), 4 STILL-OPEN ORDINARY-WORK.

**Both auto-fixable flips are deferred to the next non-grace-blocked run** — they are pure tracking-checkbox flips in
the OLD findings docs (the underlying facts they'd cite are already true; no other file needs editing for either).

## Flips verified

- `prediction_satellite_ao_dispatch_batch12_2026_08_17.md` todo 4 — `[SCRIPT]` (was briefly `[OPERATOR][SCRIPT]`
  mid-run, see Contradictions C1 below) — dispatchable as originally written per the operator's ruling.

## Contradictions

**C1 (P0, CONFIRMED, RESOLVED same run via operator ruling).** `prediction_satellite_ao_dispatch_batch12_2026_08_17.md`
todo 4 (AO-dispatchable, was untagged) would have executed a live PROD manifest CAS write
(`canonicalize_prediction_manifest_2026_07_18.py --bundle-mode normalize --apply --confirm-prod-write`) on the
CQG-bundle `instrument_type` field, but `prediction_phase_ab_residuals_2026_07_24.md`'s own still-open finding (i)
explicitly framed the disposition of that SAME 2,280-row population as an unresolved 3-way operator decision. The
todo's "RESOLVED BY PRECEDENT" framing only actually justified the per-CID half (9,260 rows), not the CQG-bundle half.
**Action taken**: applied a protective `[OPERATOR]` gate + cross-reference note to both docs immediately (before
verification of the rest of the corpus continued), alerted the operator via `POST /blocked` (`BLK-2062d75e`) with 3
framed options + a reasoned recommendation (A: normalize). **Operator answered A** (2026-08-19T15:44:13Z) — both docs
updated to reflect the ruling, `[OPERATOR]` tag removed, todo is dispatchable as originally written. Full
before/after in the two docs' own Progress Log / inline annotations.

**C2 (P1, CONFIRMED, FIXED).** `prediction_consolidated_closeout_2026_07_18.md`'s own Ground-truth verdict table
had two contradictions:
1. The "MTDS prediction `-test-` bucket isolation" row still read `**MISSING (writes to PROD)**` while the doc's own
   Conclusion paragraph, 9 lines later, states it was FIXED 2026-07-18 with 3 cited SHAs. Fixed: row now reads
   `**FIXED 2026-07-18** (see Conclusion below)`, matching the annotation style every other corrected row already
   uses.
2. The CQG-cluster-atom row cites a 2026-07-18 finding ("phantom wipe... downgraded to verify-not-fix") with no
   cross-reference to a completely different, still-open, still-unowned finding on the SAME atom:
   `manifest_hygiene_red_all_2026_08_17.md` shows `(POLYMARKET, prediction_canonical_question_group)`
   `DIVERGENT_EMPTY` on 419/970 days (43%, including today), real writer unidentified after 4 diagnosis rounds. Fixed:
   added a `RE-OPENED... DIFFERENT mechanism` note to the table row + added `manifest_hygiene_red_all_2026_08_17.md`
   to the Aggregated-source-docs "Manifest / CQG / phantom" index (that target doc itself is grace-blocked, 0h old —
   only the hub doc pointing AT it was edited, no edit needed to the grace-blocked doc itself).

**C3 (P1, CONFIRMED, self-healing — no fix applied).** Batch11 and batch12 (both same-tranche AO-dispatch-batch docs,
6 days apart) use two different source-checkbox-extraction conventions: batch11 leaves the source doc's item open
until real work lands; batch12 marks the source item `[x]` at extraction time. `prediction_phase_ab_residuals`'s own
"blank/null instrument_type ACTIVELY GROWING" item is `[x]` (already closed per batch12's convention) while the
actual fix (batch12 todo 2) is still `[ ]` — reads as "done" when it isn't. Per the fresh-sweep hunter's own analysis,
`prediction_satellite_ao_dispatch_batch12_2026_08_17_finalize.md`'s own still-open todo 1 is DESIGNED to reconcile
this exact gap once it runs — genuinely self-healing, not left broken. No action needed; noted for awareness only.

## Doc-drift

None requiring operator routing this run (C1/C2/C3 above were all either resolved via the operator's direct ruling or
mechanically auto-fixable with HARD evidence).

## Codex corrections applied (mechanical, evidence-cited)

None this run — no codex/SSOT-doc edit met the narrow STEP-5.f2 carve-out bar (no codex text was found factually
stale with a single unambiguous correction).

## Hygiene fixes

- **SHA citation corrected**: `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` cited
  `instruments-service@176d4610` for the OKX/BYBIT margin-type fix — confirmed NOT an ancestor of
  `origin/live-defi-rollout` (lives only on an orphaned `wip-preserve` branch); the same content landed verbatim
  under the rebased `a4542b2d` (confirmed ancestor + content-verified present at HEAD). Citation corrected.
- **Non-standard checkbox marker**: same doc, a `- [~]` line (not a valid `plans/PLAN_FORMAT.md` marker) corrected to
  `[x]` — the work it describes is genuinely complete; the untouched P2/P3 items it might have been hedging about
  remain separately prose-tracked, not part of this checkbox's own scope.
- **Reference-path convention (leading-slash, repo-root-relative; HARD RULE)** — 6 bare/wrong-directory citations of
  `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` fixed across `prediction_phase_ab_residuals`,
  `prediction_phase_c_data_status_ui`, `prediction_phase_d_formal_smoke_and_backfill`,
  `prediction_phase_e_football_arb_live` (1 each, all in `source:` frontmatter prose) — each verified against a fresh
  `find` before fixing. `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s entire `related:` frontmatter block
  (9 entries, ALL missing the leading slash, 3 also pointing at the wrong directory) rewritten wholesale after
  verifying every target's real location. `prediction_capture_incident_remediation_2026_07_06.md`'s top blockquote
  link to the capture-outage issue doc corrected from a `../`-relative-equivalent bare path to the leading-slash
  absolute form (target confirmed archived, not active).
- **Internal-consistency fix**: `prediction_satellite_ao_dispatch_batch13_2026_08_19_finalize.md`'s own `summary:`
  referenced "this batch's items 3/4" — batch13 has exactly 2 todos; the phrase didn't correspond to anything in this
  doc. Corrected to remove the dangling reference rather than guess a replacement number.

## Filed

- **`- [ ]` todos added (6, new)** to `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` — untracked P1/P2 bugs
  that existed only as prose in its § "Full bug list" (DERIBIT-COMBO no live WS connector, OKX-SWAP live venue-key
  mis-registration, BYBIT base/underlying pollution, Bitfinex quote-asset filter drop, Databento CME event-contract
  mistyping, ICE/CBOE Yahoo-fallthrough) — per CLAUDE.md's HARD RULE ("every follow-up is a `- [ ]` todo, never
  prose").
- **batch11/phase_d duplicate-todo double-execution risk (NEEDS-RULING, carried forward from Phase -1)**:
  `prediction_satellite_ao_dispatch_batch11_2026_08_13.md`'s 2 todos duplicate P0 todos already tracked in
  `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` — if both an interactive session and an AO dispatch
  picked up the same physical action concurrently, there is no single correct owner to remove without a planning
  decision (confirmed by 2 independent doc reads: the 08-16 findings doc's own citation + this doc's Phase -1
  hunter). Not resolved this run — deduplicating either copy without a fresh, careful re-read of BOTH docs' current
  exact wording risks losing real tracked work (Phase 5.9(d) conservation risk). Recommend: the next `plan-reconcile`
  or `/na-eligibility-audit` pass on this tranche resolve which copy is canonical.
- **v9-schema-WARN already-shipped finding (P0, GRACE-BLOCKED, deferred)**: a fresh-sweep hunter found
  `prediction_satellite_ao_dispatch_batch14_2026_08_19.md` (status: draft) todo 3 asks a worker to build a
  cross-repo v9-schema-drift WARN mechanism that is ALREADY shipped + tested in all 3 named repos (features-service,
  strategy-service, market-data-processing-service), hard-evidenced via 3 confirmed-ancestor commit SHAs. The source
  citation (`data_completion_prediction_2026_07_15.md` GAP-4) is also still unflipped. **Both docs are inside this
  run's 12h grace window (1h and 7h old respectively) — could not be edited this run.** Batch14 is still `draft`
  (not yet dispatched), so no worker time has been wasted yet, but flagging prominently since it WOULD be wasted the
  moment batch14 flips to `active` unless this is fixed first. Next run: drop batch14 todo 3 (or convert it to a
  `[REVIEW]` verify-and-flip todo) and flip `data_completion_prediction_2026_07_15.md:410`'s GAP-4 checkbox, citing
  `features-service@5a5246e6`, `strategy-service@3561f137`, and the pre-existing MDPS pattern.
- **Karak-decommission stale citation (P3, low priority, deferred)**: `mtds_is_full_adapter_smoketest_findings`'s §3a
  still frames the Karak fabricated-vault-address bug as "remains open P1" — a 2026-08-16 operator ruling
  (`karak_decommission_2026_08_16.md`, confirmed to exist) has since decided to decommission Karak entirely, which
  supersedes that framing. Not fixed this run (lower priority, deferred in favor of the higher-value fixes above);
  next pass should update §3a to cite the decommission doc.
- **Symbiotic fabricated-address doc-owner (P3, unconfirmed, deferred)**: the same §3a's Symbiotic fabricated-address
  twin (2/4 addresses) has no confirmed tracking doc — only an unrelated-scope `symbiotic_venue_onboarding_2026_08_16.md`
  was found, not independently confirmed to cover this specific bug. Needs a dedicated check, not done this run.

## Archive candidates (operator review)

None this run. One candidate was raised by a fresh-sweep hunter
(`mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`'s `archive_exempt: true` flagged as
"unjustified") but was **REFUTED** on direct verification — see Refuted below.

## Trust-mode auto-applied [WORKER REC]

None — the one genuine judgment call this run surfaced (C1, the CQG-bundle normalize-vs-null decision) was routed
through an actual interactive operator ruling (`BLK-2062d75e`) rather than a trust-mode auto-apply, since it involved
an imminent live PROD write risk that warranted the operator's own explicit sign-off rather than a worker
recommendation applied unreviewed.

## Refuted (dropped by verify)

Three hunter-reported findings did not survive my own direct-Read verification pass — each is recorded here rather
than silently dropped, per the no-miss-ledger discipline:

1. **`features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md:322-323` stray-space
   citation** — a fresh-sweep hunter reported a filename with a mid-word space
   (`..._and_vm_ tarball_staleness_...`) at this location. My own complete, fresh read of this exact file found no
   such text anywhere. A corpus-wide grep for the exact stray-space string found it in a DIFFERENT file instead —
   `plans/active/data_pipeline_check_mdps_features_2026_07_20.md:323` — not the one the hunter named. **Not fixed
   this run** (wrong-file misattribution caught, but the real occurrence is outside my planned edit set — filing
   here rather than expanding scope further); a future pass should fix it at its real location.
2. **`mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`'s `archive_exempt: true` "lacks
   justification"** — a fresh-sweep hunter flagged this as inconsistent with an identical sibling doc that WAS
   archived normally. My own complete read of this doc's Progress Log found a 2026-08-17 `na-eligibility-audit`
   entry that directly and explicitly validates the flag ("`archive_exempt: true` is... the correct standing marker
   per the archival-discipline codex SSOT. No action needed") — the hunter's finding did not account for this
   entry. Not archived; not edited.
3. **S3/S4 bare-path citations in `prediction_live_clob_depth_capture_2026_07_24.md`** (a fresh-sweep hunter cited
   lines 443/455 for two mis-pathed references) — a complete fresh read of the full 934-line file (both halves) found
   neither citation anywhere in the current content. Not fixed.

## Coverage (hunters / batches / docs)

- 6 hunter sub-agents dispatched (2 Phase -1 reconcilers + 4 fresh-sweep batches), all completed successfully.
- 49/49 prediction-tranche docs read in full across the 4 fresh-sweep batches (12+12+12+11 partition) + the 2 Phase-1
  docs read by the reconciler hunters — 100% coverage of the tranche's own doc inventory.
- Every hunter-reported candidate that fed an actual edit was independently re-verified via a fresh direct Read (and,
  where applicable, `find`/`git merge-base --is-ancestor`) by the orchestrator before any write — 3 candidates were
  refuted this way (see Refuted above); the rest were confirmed.
- Verified/confirmed: 20 (all fixes actually applied, see Flips verified + Hygiene fixes + Filed's 6 new todos).
  Refuted: 3. Needs-ruling, filed not applied: 1 (batch11/phase_d dedup). Grace-blocked, deferred: 3 items across 2
  old findings docs + 1 (F1, v9-schema) across 2 further docs.

## Plans not reached

Not "not reached" in the coverage sense (all 49 docs WERE read) — these are confirmed-findings that could not be
**acted on** this run because their target doc(s) fall inside the 12-hour grace window (16 of 49 tranche docs are
grace-blocked this run):

- `plan_reconciler_findings_prediction_2026_08_16.md`, `..._2026_08_18.md` — both fully re-verified (see Phase -1
  above), 2 mdps_fleet-related checkbox flips deferred.
- `data_completion_prediction_2026_07_15.md`, `prediction_satellite_ao_dispatch_batch14_2026_08_19.md` (+its
  `_finalize`) — the v9-schema-already-shipped finding (F1, Filed above) deferred.
- `manifest_hygiene_red_all_2026_08_17.md` — read for context (fed the C2 cross-reference fix in the hub doc), not
  itself edited; its own 3 open [DATA]/[SCRIPT] P1/P2 todos remain genuinely open, untouched.
- `b21_distinct_values_noncanonical_live_2026_08_18.md`, `dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`,
  `instruments_remaining_work_audit_2026_07_10.md` (incl. its own confirmed-stale hedge-pointer finding about
  `instruments_completion_tracker_2026_07_06.md`'s D6 row — this is now CONFIRMED WRONG per a fresh-sweep hunter, but
  the fix target is this grace-blocked doc itself), `mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`,
  `prediction_satellite_ao_dispatch_batch13_2026_08_19.md`, `..._batch14_2026_08_19_finalize.md`,
  `..._batch15_2026_08_19.md` (+`_finalize`), `..._batch6_2026_07_29.md`, `sports_prediction_mvp_writetime_precompute_2026_07_24.md`,
  `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` — all read for context (no findings requiring an edit
  to THESE specific docs surfaced from the hunters covering them, beyond what's already filed above), all
  grace-protected regardless.

**Pre-existing corpus-wide hygiene condition, out of this tranche-run's remit**: the `assigned_vm:NA` corpus-size
ratchet hard-failed the whole-corpus sweep at STEP 1 (pre-existing, not caused by this run — I did not add any doc to
the NA population). Owned by `/na-eligibility-audit`, not this skill; not actioned here.
