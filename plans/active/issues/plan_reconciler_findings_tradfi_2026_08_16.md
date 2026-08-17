---
doc_type: issue
title: "plan_reconciler tradfi-tranche deep reconciliation run — 2026-08-16"
summary: >-
  Run-findings doc for a sharded, autonomous /plan-reconcile pass over the tradfi tranche (86 docs, 2.75MB),
  dispatch agt-a74a6a, slot 31. Fans out 9 size-balanced (~305KB) read-only hunter batches covering every tradfi
  doc in full, adversarially verifies every candidate, auto-fixes the verified-easy, routes the hard ones.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, tradfi, sharded]
related: [/plans/active/tradfi_consolidated_closeout_2026_07_18.md]
created: 2026-08-16
author: plan_reconciler
source: agt-a74a6a
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler-agt-a74a6a
depends_on: []
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md,
  ]
---

# plan_reconciler tradfi-tranche run — 2026-08-16

Dispatch `agt-a74a6a`, slot 31, tranche `tradfi`. Corpus: 86 docs / 2,755,415 bytes under `plans/active/` +
`plans/active/issues/` tagged `asset_group: tradfi` (via `generate_tranche_doc_inventory.py --tranche tradfi`).

## Todos (follow-ups from this run, not executed here — see "Filed" section below for full context)

> **Phase -1 reconciliation pass (2026-08-16, same-day follow-up)** — all 9 items below re-checked against fresh state.
> 5 executed this pass (4 archivals + 1 mechanical text correction); 2 partially executed (item 5: correction done,
> archival deferred — referrer sweep too large to safely rush; item 8: 3/7 done, 4/7 grace-blocked); 1 blocked by a
> NEW pre-existing finding (item 6: the target doc is over its own 1000L hard line-cap, so ANY commit touching it —
> incl. this tag-only fix — is hook-rejected until it's split); 1 genuinely grace-blocked (item 7); 1 codex-gated,
> correctly not auto-applied per the skill's codex-edit carve-out (item 9), flagged to the operator instead. See the
> per-item notes below and the new "## Phase -1 reconciliation" section at the end of this doc for full evidence.

- [x] ✅ [DOC] P2. **Archive `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`** — verified 9/9 todos `[x]`,
      unlocked; `archive_exempt: true` bridge explicitly deferred to a separate follow-on pass. **RESOLVED before this
      pass reached it** — confirmed already archived (by na-eligibility-audit, per its own banner) at
      `plans/archive/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`; spot-checked its ~23 corpus
      referrers, every structured leading-slash reference already repoints to the archived path (only prose/bare-name
      fact-citations remain, correct per the fact-vs-path convention). No action needed.
- [x] ✅ [DOC] P2. **Archive `tradfi_recovery_quarantine_registration_gap_2026_07_27.md`** — verified 4/4 todos `[x]`,
      unlocked, `locked_by` cleared 2026-08-12; same deferred-bridge pattern. **DONE 2026-08-16 (plan_reconciler
      Phase -1)**: 6-step ritual run, archived to `plans/archive/2026_08/issues/`; only referrers found were prose/bare
      mentions (no structured refs to repoint).
- [x] ✅ [DOC] P2. **Archive `tradfi_backfill_oom_remediation_2026_06_24.md`** — verified all todos `[x]` as of
      2026-08-16, confirmed outside the 12h grace window via direct `git log` check at time of this run. **DONE
      2026-08-16 (plan_reconciler Phase -1)**: 6-step ritual run, archived to `plans/archive/2026_08/issues/`; 2
      structured referrers repointed (`tradfi_vm_resource_utilization_downsize_2026_08_10.md` ×2,
      `tradfi_backfill_throughput_followups_2026_07_24.md` ×1).
- [x] ✅ [DOC] P2. **Archive `backfill_smoke_write_path_canonical_audit_finalize_2026_08_08.md`** — verified 2/2 todos
      `[x]` since 2026-08-10 (6 days overdue at time of this run), `archive_exempt` never dropped per its own
      codex-cited convention. **DONE 2026-08-16 (plan_reconciler Phase -1)**: 6-step ritual run, archived to
      `plans/archive/2026_08/`; `INDEX.md` + `infrastructure_master.md` referrers left for their own regen tooling
      (machine-generated, established precedent from this doc's own earlier "Hygiene fixes" section); a
      Progress-Log-only historical mention in `defi_satellite_ao_dispatch_batch11_2026_08_09.md` left untouched
      (fact-vs-path convention).
- [x] ✅ [DATA] P2. **EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) →
      `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 6 (archival half only).** Correct the stale
      Massive-purge section in `tradfi_canonical_path_migration_design_2026_07_19.md`, then archive it. Doc body
      (steps 5-6 / hard-stops list) still frames the 1.47M-object Massive purge as future-gated;
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3 confirms it EXECUTED 2026-07-20/21 (1,701,422
      objects → 0, 0 collateral) and names this doc as the source design doc. All todos already `[x]`,
      `archive_exempt: true` bridge pending this correction + a follow-on pass. **HALF-DONE 2026-08-16
      (plan_reconciler Phase -1): the text correction is DONE** (Sequencing step 6 + Hard-stops list corrected in
      place, evidence cited inline). Archival half (43 corpus referrers, confirmed via a fresh grep 2026-08-17, up
      from the "35+" estimate at filing) is bounded/mechanical (standard 6-step ritual + referrer sweep) —
      extracted to the AO batch above rather than executed in this audit pass.
- [ ] [SERVICE] P3. **Fix the missing `[OPERATOR]` tag on 2 open todos in
      `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`** (lines ~975, ~983 as of this run — SPOT vs
      on-demand VM cost/reliability question, raised twice in Progress Log across 6 consecutive gated-skip dispatches,
      never formally escalated). Tag-only fix; the underlying design question itself stays genuinely open pending an
      operator ruling. **BLOCKED 2026-08-16 (plan_reconciler Phase -1) — NEW finding, not the originally-scoped
      issue.** Drafted the tag-fix edit (both todos → `[DATA→OPERATOR]`), but the pre-commit hook rejected it:
      `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` is 1010L, already OVER its own 1000L hard
      line-cap BEFORE this edit (my edit would only have pushed it further over) — `check_line_caps.sh` blocks any
      commit touching an over-cap doc regardless of whether the edit adds or removes lines. Reverted the edit
      (uncommitted, cleanly — nothing landed). Per the skill's own "line-cap-blocked-done is a distinct sub-case" rule
      (Phase 2), this is now a **split finding**, operator-gated (splitting a 1000+-line doc is a planning decision,
      not a mechanical fix) — not something this pass can force through. Genuinely still open.
- [x] ✅ [DOCS] P3. **EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) →
      `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 7.** Fix the residual reference-path ratchet
      regression from this run's archivals (baseline 34, currently 38 — 2 of the original 6 were fixed same-run) —
      `tradfi_consolidated_closeout_2026_07_18.md` (×2) and `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` (×2)
      still reference the now-archived `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`(+`_finalize`). **STILL
      OPEN 2026-08-16 (plan_reconciler Phase -1)**: re-checked — both docs were still inside the 12h grace window as
      of that pass. Grace-blocked, mechanical, not a judgment call — extracted rather than fixed directly here
      (by 2026-08-17 dispatch time this is a new day; the extracted todo re-verifies grace has cleared before
      editing).
- [x] ✅ [DOCS] P3. **EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) →
      `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 8 (4/7 remaining slice).** Bump stale
      `last_updated` frontmatter on the tradfi-tranche docs found during this run. **3/7 DONE 2026-08-16
      (plan_reconciler Phase -1)**: `instruments_remaining_work_audit_2026_07_10.md`,
      `tradfi_manifest_content_recovery_completion_2026_07_24.md`,
      `strategy_ml_orphan_coverage_design_gaps_2026_08_03.md` bumped already. **4/7 remaining** —
      `ag_closeout_audit_rollout_2026_07_25.md`, `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`,
      `estate_orphan_assessment_2026_07_21.md`, `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` — were
      inside the 12h grace window at 2026-08-16 filing time; mechanical, grace-blocked, extracted rather than
      fixed directly here (the extracted todo re-verifies grace has cleared, now a new day, before editing).
- [x] ✅ [DOCS] P3. **File 4 codex-alignment corrections** identified this run (new content needed, not a pure
      substitution, so not auto-applied per the mechanical carve-out): `/codex/02-data/tradfi-databento-sourcing-ssot.md`
      (2 gaps — stale CBOE-floor-fix status + silent on `EXCHANGE_CODE_TO_NAME`), `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`
      (missing a 3rd billing-waste failure-mode class), `/codex/05-infrastructure/manifest-consolidator-ssot.md` (no
      warning that rebuild scripts resurrect retired-venue manifest rows), `/codex/05-infrastructure/data-pipeline-alerts.md`
      (no detector for intended-pause-then-silently-resumed, confirmed recurred twice). Flagged to the operator, who
      approved landing all 4 as content additions on 2026-08-17. **DONE 2026-08-17** — all 4 investigated fresh
      (re-verified against live code/plan corpus, not assumed from this doc's framing) and shipped:
      `unified-trading-pm@a07e438230` (CBOE floor-fix status corrected + `EXCHANGE_CODE_TO_NAME`/`tradfi_symbology.py`
      section added), `unified-trading-pm@cb424aad2e` (3rd billing-waste failure-mode class —
      `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`'s under-scoped relaunch actuator, ~20-30x fan-out),
      `unified-trading-pm@206dc9cb15` (manifest-consolidator retired-venue resurrection warning —
      `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md`'s ICE finding),
      `unified-trading-pm@6745e86402` (data-pipeline-alerts "intended-pause-then-silently-resumed" gap — the
      2026-07-31 prediction + tradfi consolidator-cron recurrences). All 4 ancestor-verified on
      `origin/live-defi-rollout`.

## na-eligibility-audit 2026-08-17 (tradfi tranche, dispatch agt-d99b5c)

**RECLASSIFY, per-todo split.** Items 1 (archival half), 3 (reference-path regression), and 4 (last_updated bumps,
4/7 remaining) are bounded/mechanical, blocked only by a self-resolving 12h grace window (now cleared, a new day) —
extracted to `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todos 6/7/8 respectively (see checkboxes above).
Item 2 (line-cap-blocked tag fix on `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`) stays KEEP-NA —
explicitly operator-gated (splitting a 1000+-line doc is a planning decision), self-cited in-doc. Item 5 (4 codex
SSOT corrections) stays KEEP-NA — gated by this skill's own codex-edit carve-out (new content, not a pure
substitution, stays gated regardless of trust mode); already flagged to the operator per the originating pass. Doc
stays `assigned_vm: NA` (this is an issue-doc classification action on individual findings within it, not a
whole-doc reclassify — the doc's own remaining open items, 2 and 5, are genuinely NA).

## Phase -1 — prior findings reconciliation

No `plan_reconciler_findings_tradfi_*.md` doc existed prior to this run. Checked the two most recent `all`-scope
runs for still-open tradfi items:

- `plan_reconciler_findings_all_2026_08_15.md`: no unchecked (`- [ ]`) items mention tradfi — all tradfi-related
  findings in that run were resolved `[x]`.
- `plan_reconciler_findings_all_2026_08_12.md`: 2 still-open tradfi items, both already re-checked same-day
  (2026-08-16, presumably by a concurrent session) with an inline `**CHECKED 2026-08-16**` note in each case
  concluding genuine remaining work (not a doc-hygiene gap):
  - `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` — "Full MTDS+IS adapter smoke findings" sub-item
    still open; a full 3-item re-verify is more than a one-line fix.
  - `tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27.md:12` — original finding gave
    no specifics to re-verify against; left open/unclear.

  Disposition: STILL-OPEN ORDINARY-WORK for both — inherited, not re-litigated. No action taken by this run.

## Coverage (hunters / batches / docs)

9 hunter batches, ~305KB each, 86/86 docs covered in full (see `tradfi_batches.txt` partition). Each batch also
covers: contradiction sweep, done-but-unchecked evidence hunt, AO-dispatch-readiness (task_template.md §3),
codex-alignment, hedge-pointer verification, and prose/structural-integrity for any doc it reads.

## Archive-ready plans executed (gated finalize plans with a stale, cleared gate)

Two `*_finalize` plans had their `depends_on` gate cleared (source batch fully `[x]`) but sat with ZERO reconciliation
progress for days — executed both finalize plans' own todos (reconcile source docs, re-check Deferred/Flagged, archive)
and archived both the batch + its finalize twin:

1. **`tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` + `_finalize`** — gate cleared 2026-08-09 (4/4 todos done),
   7 days idle. All 5 source docs turned out to need no further edit (2 already archived, 1 already fully `[x]`, 1
   grace-protected with its diagnostic finding already recorded, 1 already archived). Archived →
   `plans/archive/2026_08/`. Evidence: `unified-trading-pm@6cb3115f53`.
2. **`tradfi_satellite_ao_dispatch_batch11_2026_08_10.md` + `_finalize`** — gate cleared ~2026-08-15 (14/14 todos
   done), idle since creation. Reconciled 11 of 14 source docs with direct evidence (full breakdown in the finalize
   doc's own Progress Log); 2 sit in the 12h grace window (correctly left untouched); 1 needs a targeted follow-up
   read not completed this pass. **Surfaced one real finding in the process**: batch11's own todo 3 (EXCHANGE_CODE_TO_NAME
   convergence, claimed DONE) has a dead-code gap recorded in its source doc 5 days later — the convergence isn't
   actually wired into the live checker path (`tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`, already
   tracked there as a P2 item, not newly filed). Archived → `plans/archive/2026_08/`. Evidence:
   `unified-trading-pm@909becfad0` (+ `90ad0a8e4b` fixing an incomplete-rename duplicate this run's own retry churn
   introduced, caught by direct verification before reporting done).

## Flips verified (done-but-unchecked, HARD evidence)

| Doc | Item | Evidence |
| --- | --- | --- |
| `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` | todo 1 (`_resolve_spot_perp` fix) | `features-service@f441638932` → superseded `features-service@a46681c84a` |
| `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md` | distinct-values/axis-value census todo | `unified-trading-pm@d302e45cc6` |
| `tradfi_manifest_content_recovery_completion_2026_07_24.md` | CME monolith investigation todo | doc's own next section documents bootstrap fixed, count investigated, VM cleaned, tool already done (`mtds@02284f8e`) |
| `tradfi_manifest_content_recovery_completion_2026_07_24.md` | legacy-content rewrite-pass todo | doc's own Phase B section shows gate-closed, 0 violations (961/961 canonical) |

**Not flipped (grace-protected, HARD evidence exists)** — flag for the next pass once grace clears:
`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (3 items: residual purge extraction note, ES_OPT launch +
manifest-verify — all superseded/verified via `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`);
`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (`canonical_twin_path()` fix shipped `is@bbcc6395` via
batch11, doc's own checkbox still open).

## Contradictions — fixed this pass

| Severity | Doc | Fix |
| --- | --- | --- |
| P0 | `data_completion_tradfi_2026_07_15.md` | Stale "NO terraform scheduler for ANY asset group" todo (2026-06-07) contradicted by `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` (scheduler created 2026-06-11, live-verified driving the exact producer). Risked dispatching a DUPLICATE scheduler bypassing the other doc's protective exclusion filter. Added a correction pointing to the current-truth doc. |
| P1 | `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` | §5.1 said "cefi+tradfi only", contradicted by §7's own DONE item widening to cefi+defi. Corrected. Also: a `- [ ] [SERVICE] P2` todo was embedded mid-line inside a DONE item, invisible to line-anchored parsers (incl. AO backlog gen) — moved to its own line. The doc's 2026-08-11 "all §7 todos are now `[x]`" claim (which set `archive_exempt:true`) was false because of this — corrected with a dated note. |
| P1 | `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` | Title/summary claimed "20,254 rows, static since 2026-08-07" — body shows the population grew substantially and kept growing. Corrected title+summary; deleted the stale exact figure rather than restating a new one (avoids re-staling). |
| P1 | `tradfi_databento_account_billing_suspended_2026_08_09.md` | Header claimed "FULL account-level outage" — the doc's own fresher (2026-08-15) body finding shows CME/GLBX.MDP3-specific, other venues unaffected in the same run. Corrected framing, preserved original text for history. |
| P1 | `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` | Frontmatter summary said "not investigated to root cause here... time-bounded" — body shows both root causes found + fixed 3 weeks ago (`instruments-service@f651ff8b` + a splitter-bug fix). Corrected. Also fixed a line-1-completeness gap (todo cut off mid-parenthetical). |
| P1 | `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` | Body banner said "status: draft — not ingested" contradicting frontmatter `status: active` + a shipped todo. Corrected. |
| P2 | `dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md` | Todo text cited "99.5% of FX" overlap; the doc's own Progress Log measurement is 99.3% (10/1379). Corrected. |
| P2 | `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` | A todo pointed to an archived doc "for execution" when the fuller write-up is actually in this doc's own Progress Log. Corrected. |

## Structural / hygiene fixes

- `tradfi_manifest_content_recovery_completion_2026_07_24.md` — heading mangled across 2 physical `###` lines with an
  orphaned floating `)`; merged onto one line.
- `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md` — one checkbox was missing the
  `[TAG] Pn.` format every other todo in the corpus follows; added (`[DIAG] P3`).
- `dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md` — zero-checkbox doc (real remaining
  work, invisible to backlog generation); converted the "Recommended decision" prose into 2 canonical `- [ ]` todos.
- Referrer sweep for both archivals: fixed structured `/plans/…` path references in 6 active docs
  (`tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md`, `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`,
  `tradfi_databento_account_billing_suspended_2026_08_09.md`, `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` +
  `_finalize`) — plus self-references inside the archived docs themselves. Did NOT hand-fix `plans/epics/tradfi_master.md`'s
  child-plan list (machine-generated by `populate_epic_bodies_2026_05_21.py` — belongs to a regen, not a hand-edit) or
  2 prose-only mentions inside prior dated `plan_reconciler_findings_all_*.md` docs (historical record, not
  structured links, lower priority).

## Codex-alignment drift found — filed, NOT auto-applied (needs new content, not a pure substitution)

- `/codex/02-data/tradfi-databento-sourcing-ssot.md` — stale on the CBOE discovery-floor granularity fix's shipped
  status (still frames as "open, unaddressed"; fix shipped 2026-08-12) and silent on
  `EXCHANGE_CODE_TO_NAME`/`tradfi_symbology` despite being cited in 3 docs' `context_scope` for exactly that topic.
- `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` — enumerates 2 billing-waste failure modes;
  a 2026-08-15 incident (`mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`) found and fixed a 3rd class
  (under-scoped/under-deduped relaunch actuator, 20-30x fan-out) the codex doesn't yet name.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` (or the ICE retirement section) — doesn't warn that
  `rebuild_tradfi_manifest.py`-style rescans resurrect retired-venue manifest rows (live-caught 2026-08-15,
  `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md`).
- `/codex/05-infrastructure/data-pipeline-alerts.md` — no registered detector for "job was intentionally paused, then
  silently resumed" (the opposite of the existing DP-WATCHER-004); confirmed recurred TWICE
  (`tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md`).

## Filed / left for a future pass (not executed this pass — reasons noted)

- **4 more archive-ready docs identified, not executed** (time-bounded this pass): `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`
  and `tradfi_recovery_quarantine_registration_gap_2026_07_27.md` (both fully `[x]`, both explicitly say archival is
  deferred to "a separate follow-on pass" in their own `archive_exempt` bridge text — this pass is a candidate for
  that but ran out of allotted scope); `tradfi_backfill_oom_remediation_2026_06_24.md` (fully `[x]` as of today,
  same bridge pattern, confirmed OUTSIDE the 12h grace window via direct git-log check); `backfill_smoke_write_path_canonical_audit_finalize_2026_08_08.md`
  (fully `[x]` since 2026-08-10, `archive_exempt` never dropped per its own codex-cited convention).
  `tradfi_canonical_path_migration_design_2026_07_19.md` additionally needs its stale Massive-purge section corrected
  first (codex confirms the purge executed 2026-07-20/21; the doc's own body still frames it as future-gated) before
  archiving.
- **`tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` todo 3** — stays correctly
  `[OPERATOR]`-gated (genuine risk/tradeoff call on loosening a QG hard-cap gate). Note: a related-shaped carve-out
  shipped for a sibling doc's scenario (`PM@d765b4cfb1`) — may or may not cover this exact case; not assumed, left
  for an operator/follow-up check.
- **`uac_data_type_validity_combinator_fragmentation_2026_07_07.md`** — an unresolved SPOT-vs-on-demand VM
  cost/reliability design question has been raised twice in Progress Log entries without a formal `[OPERATOR]`
  escalation; 6 consecutive dispatches gated-skip rather than surfacing it. Already tracked in-doc; not re-escalated
  as new (would duplicate), flagging so a future pass adds the formal tag.
- **`tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md`** todos 2/3 — batch11 claims these shipped;
  not independently re-verified at the specific-checkbox granularity this pass.
- The 3 `last_updated` frontmatter-staleness findings from batches 3+8 (7 docs total, 3 days to 3 weeks stale) — P2/P3
  cosmetic, mechanical tooling gap (audit passes don't bump the field) rather than 7 one-off hand-edits; worth a
  tooling fix, not chased individually this pass.

## Refuted (dropped by verify)

None — every hunter candidate this pass that reached the apply stage was corroborated by direct re-reading before
acting (inline verification, per this skill's "small candidate counts" allowance). One near-miss caught and
self-corrected: `dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md` mischaracterized a
sibling doc's `exit_code=137` (stall) as sharing its own `exit_code=1` signature — correctly identified as P1 by the
hunter, but the doc is grace-window-protected (created today) so left unfixed and noted here instead of applied.

## Plans not reached

None among the 86-doc tradfi tranche corpus (full coverage via the 9 hunter batches). Several docs OUTSIDE the
tranche that batch11/7's source-doc citations point at were not independently re-read (see "Filed" above) — bounded
scope, not a coverage gap in the tranche itself.

## Phase 5.9 ledger

- `routed_to_operator` = 0 — every genuinely-ambiguous item found was ALREADY tracked as an open `[OPERATOR]`-tagged
  todo before this pass (re-escalating would duplicate, not inform); nothing new crossed the "ask" bar this pass.
- `parked_in_issue_doc` = 0 (consistent with the above — nothing new to park).
- `agent_skips_enumerated`: N/A — no sub-agent applied a fix this pass; all applies were done directly by the
  orchestrator (this session) after inline verification, per the hunter/verifier split (hunters detect, orchestrator
  applies).
- **Coverage**: 9 hunter batches, 86/86 docs read in full. **Confirmed fixes applied**: 4 flips + 8 contradiction
  fixes + 3 structural/hygiene fixes + 2 full finalize-plan executions (2 batches + 2 finalize plans archived, 4
  archives total) = 17 individual file edits + 4 archivals, across 4 commits, all verified landed on origin.

## Phase-0 hygiene sweep (corpus-wide, informational)

**Entry (Phase 0, `--no-regen`)**: 1 hard failure (`assigned_vm:NA corpus size ratchet` — corpus-wide,
`/na-eligibility-audit`'s remit, not a tradfi-tranche contradiction), 1 soft warning (folded into hunter checks).

**Exit gate (`--ci` with regen, run after all fixes)**: 3 hard failures — the pre-existing NA-ratchet (unchanged,
out of scope), plus 2 NEW ones this run's own archival work caused, both understood and one fully fixed:
- `AG-closeout linkage` (baseline 0 → found 1 orphan) — **FIXED**: `tradfi_recovery_quarantine_registration_gap_2026_07_27.md`
  was missing a `related:` link to its closeout family; added. Re-verify not yet re-run (see below).
- `Reference path convention — existence` (baseline 34 → 40, i.e. +6) — **2 of 6 fixed** (a missed `_finalize`-variant
  path in `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` + its own finalize twin, both pointing at the
  now-archived batch11). **4 remain, unfixable this pass by the HARD RULE**: `tradfi_consolidated_closeout_2026_07_18.md`
  (×2, referencing archived batch7) and `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` (×2, same) are BOTH inside
  the 12h grace window (active same-day edits by other sessions) — archiving batch7 was correct and necessary
  (7-day-stale cleared gate), but the referrer-repoint side of that archival cannot land until grace clears on those
  2 docs. This is a genuine, temporary, self-explaining ratchet regression, not an oversight — flagging honestly
  rather than claiming a clean exit gate. Recommend the next `all` or `tradfi` pass (or whichever session next
  legitimately touches those 2 docs) repoints these 4 refs to close the gap.

## Phase -1 reconciliation (2026-08-16, same-day follow-up pass)

Re-checked all 9 Todos above against fresh state (`git pull --ff-only` first). Verdicts, per the skill's Phase -1
routing (RESOLVED / STILL-OPEN AUTO-FIXABLE / STILL-OPEN NEEDS-CODEX-RULING / STILL-OPEN ORDINARY-WORK):

1. Archive `tradfi_mvp_of_mvp_...` — **RESOLVED**, already archived (na-eligibility-audit), referrers already correct.
2. Archive `tradfi_recovery_quarantine_registration_gap_2026_07_27.md` — **AUTO-FIXED**: archived.
3. Archive `tradfi_backfill_oom_remediation_2026_06_24.md` — **AUTO-FIXED**: archived, 3 structured referrers repointed.
4. Archive `backfill_smoke_write_path_canonical_audit_finalize_2026_08_08.md` — **AUTO-FIXED**: archived.
5. Correct + archive `tradfi_canonical_path_migration_design_2026_07_19.md` — **PARTIALLY AUTO-FIXED**: text correction
   applied (evidence: `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3, `RUN_TS=20260720-193849`,
   1,701,422→0); archival itself is **STILL-OPEN ORDINARY-WORK** — 35+ referrers, 2 in the grace window at check time,
   a rushed sweep risks dangling refs.
6. `[OPERATOR]` tag fix on `uac_data_type_validity_...` — **BLOCKED, NEW finding — STILL-OPEN ORDINARY-WORK (split
   required)**: the tag-fix edit was drafted and then reverted uncommitted after the pre-commit hook rejected it — the
   target doc is 1010L, already over its own 1000L hard line-cap BEFORE this edit, and `check_line_caps.sh` blocks
   ANY commit touching an over-cap doc. Per the skill's own "line-cap-blocked-done" rule this is now a split finding,
   operator-gated (splitting a 1000+-line doc is a planning decision) — not mechanically fixable this pass.
7. Reference-path ratchet regression (4 refs) — **STILL-OPEN ORDINARY-WORK, grace-blocked** — re-checked fresh, both
   source docs still inside grace at this pass's check time too (one apparently mid-edit by a concurrent session).
8. `last_updated` bump on 7 docs — **3/7 AUTO-FIXED** (outside grace); **4/7 STILL-OPEN, grace-blocked** (all touched
   within the last ~40min-3h20min at check time, several likely by a concurrent na-eligibility-audit-style pass).
9. 4 codex-alignment corrections — **STILL-OPEN NEEDS-CODEX-RULING** — per the skill's codex-edit carve-out (new
   content, not a pure substitution, stays gated regardless of trust mode), NOT applied this pass. Flagged to the
   operator per the calling task's instructions (see final chat report) rather than edited.

**Doc disposition**: 3 genuinely open items remain (6 split-blocked/NEW finding, 7 grace-blocked, 9 codex-gated) plus
2 half-done items with real remaining work (5 archival-deferred, 8 partial-grace-blocked) — this findings doc is NOT
fully resolved and stays
`status: open` in `plans/active/issues/`, not archived.

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-071b5c) [body-hash:5d2f3751c4f96721]: KEEP-NA,
  valid — re-verified this same-day doc's own earlier na-eligibility-audit verdict (dispatch agt-d99b5c) is still
  current; the doc's one remaining open item (`[SERVICE] P3` OPERATOR-tag fix on
  `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`) is the rubric's own named line-cap-blocked-done
  sub-case — genuinely un-actionable until that target doc is split under its own 1000L hard cap, correctly reported
  rather than reclassified or force-flipped. This marker only backfills the machine-readable dated-hash tag the
  earlier same-day pass's narrative verdict omitted, so future incremental runs can skip this doc without a full
  re-read.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
