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
---

# plan_reconciler tradfi-tranche run — 2026-08-16

Dispatch `agt-a74a6a`, slot 31, tranche `tradfi`. Corpus: 86 docs / 2,755,415 bytes under `plans/active/` +
`plans/active/issues/` tagged `asset_group: tradfi` (via `generate_tranche_doc_inventory.py --tranche tradfi`).

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

`run_hygiene_sweep.sh --ci --no-regen`: 1 hard failure (`assigned_vm:NA corpus size ratchet` — corpus-wide,
`/na-eligibility-audit`'s remit, not a tradfi-tranche contradiction; noted, not chased by this run), 1 soft
warning (`Delete/VM-launch todo tagging` candidate signal — folded into each batch hunter's AO-readiness check
instead of a dedicated pass).
