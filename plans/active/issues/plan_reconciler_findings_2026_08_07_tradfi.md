---
doc_type: issue
title: "Plan-reconciler findings — tradfi tranche 2026-08-07"
created: 2026-08-07
author: plan_reconciler
source: agt-ec6642
locked_by: none
asset_group: tradfi
status: open
nature: issue
tags: [plan_reconciler, tradfi, reconciliation, auto-generated]
parent_epic: plan_hygiene_master
summary:
  "Automated plan_reconciler run for the tradfi topic tranche — fan-out DETECT + adversarial VERIFY. 61 docs in scope
  (27 grace, 34 non-grace). Both hunters completed: 0 P0 missed-flips, 0 P0 contradictions, 4 P1 + 9 P2 + 5 P3
  contradiction findings."
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
related: []
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-07
resolved_by: ""
---

## Flips verified

Missed-flip hunter completed (34/34 non-grace docs read, full corpus). **No P0/P1 missed flips.** Every P0/P1 open
checkbox is genuinely open: operator-gated (`[OPERATOR-REVIEW]` retire-phase `--apply`), KEEP-NA'd, machine-gated
(`gate_on_depends: true`), or re-verified with restated real-remaining-gap text.

### P2 candidates — work demonstrably shipped, checkboxes never flipped

1. **`tradfi_manifest_content_recovery_completion_2026_07_24.md` line 505 — P2.** Todo (code-quoted): "The true
   legacy-content population (FUTURE/OPTION per-contract chain-bundle content) still needs its own rewrite pass…"
   **Evidence**: follow-up shipped as `scripts/rewrite_tradfi_chain_bundle_content_id_2026_07_25.py` (mtds@a23dd8bd);
   `--apply` at scale launched 2026-07-27 (8 SPOT VMs). **Plan's own `[VERIFY] P0 GATE` todo (lines 238-241) is `[x]`**:
   "checked=961 canonical=961 violations=0". **Note**: code-quoted span — not a real mechanical checkbox.

2. **Same doc, line 681 — P2.** "Finish the CME monolith investigation…" **Evidence**: every sub-step documented
   complete in the following section; migration-tool todo (line 731) flipped `[x]`: "TOOL DONE 2026-07-26
   (mtds@02284f8e)". Also code-quoted.

3. **Same doc, line 843 — P3 (cosmetic).** QG-sentinel diagnostic. Doc's own next section states root cause found and
   fixed. Shipped: uac@68c4c371d. Also code-quoted.

### P3 candidates (cosmetic)

4. **`backfill_smoke_write_path_canonical_audit_2026_07_20.md` lines 284-286 — P3.** `[DOCS] P2` — correct three in-repo
   comments. All three sites corrected with explicit "CORRECTION (2026-07-30…)" annotations.

5. **`tradfi_master.md` line 478 — P3.** "TradFi 5,212 legacy-blank apply-flips run…" — work confirmed complete in
   archived home. **Caveat**: SUPERSEDED 2026-06-20 section — archaeology-only.

### Checked and dropped

6 candidates verified and dropped: `candle_feature_canonical_path_divergence_2026_07_20.md` todo 9 (deliberately kept
open), `estate_orphan_assessment_2026_07_21.md` todo 7 (already `[x]`), `adapter_findings_…` DECISION P2 (KEEP-NA'd),
`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` rollup (remaining gates genuinely open),
`tradfi_phase_d_terminal_gate_2026_07_24.md` P3 test-add (gate still `status: open`), all finalize plans (genuinely
ungated prerequisites).

**Action taken**: none — all 5 candidates are code-quoted documentation spans or SUPERSEDED sections, not real
mechanical checkboxes. Real tracking gates already `[x]` elsewhere.

## Contradictions

Contradiction hunter completed (full corpus: epic, hub closeout, 34 non-grace plans, 20 issues). **0 P0, 4 P1, 9 P2, 5
P3.** Dominant pattern: the hub closeout's aggregated source-doc digests (lines 573-939) systematically lag their cited
docs' checkbox states — every digest checked except the two corrected at 900/909 and the registry digest (re-derived
2026-07-31) shows drift. The hub's own 2026-07-31 sweep note (lines 348-357) admits digests go stale.

### P1 — Material drift (could mis-route live work)

**F1. ES CME futures MVP-cell row: hub says "manifest-verify still owed" — owning plan executed it 2026-07-30 with a
zero-capture result.**

- Hub: `tradfi_consolidated_closeout_2026_07_18.md:259` — "Manifest-verify still owed"
- Plan: `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md:126-142` — "DONE 2026-07-30… result is NOT 'backfill
  proven,' it's a concerning zero-capture finding, filed as `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`"
- **Impact**: a reader of the hub would re-run an already-executed check or misread the gate state of a zero-capture
  finding. The g1_g5 doc's 2026-07-30 comment explicitly states the hub row was knowingly left stale.

**F2. sp500 digest: hub lists BLOCKED-OPERATOR-DECISION as open — plan closed it 2026-07-31 (count also 9 vs 7).**

- Hub: `tradfi_consolidated_closeout_2026_07_18.md:701-707` — "(9 open — capped)" + BLOCKED-OPERATOR-DECISION items
- Plan: `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:101-102` — `[x]` "DONE — CLOSED 2026-07-31
  (na-eligibility-audit, dispatch agt-6d6eaf)" — 7 open total
- **Impact**: a BLOCKED-OPERATOR-DECISION tag shown open after resolution is the exact stale-tag class CLAUDE.md's retag
  rule targets.

**F3. g1_g5 digest count "(14 open — capped)" vs actual 6 open.**

- Hub: `tradfi_consolidated_closeout_2026_07_18.md:729-746` — 14 items listed incl. the ES ohlcv manifest-verify item as
  open (which F1 shows is DONE-with-finding)
- Plan: `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — 6 open checkboxes
- **Impact**: count drift >2×; dispatch-scope + item-level misread.

**F4. Epic's "Assigned active plans" index: claims 6 active children; 23 exist; lists archived doc as active; invalid
`assigned_vm: vm-tradfi`.**

- Epic: `tradfi_master.md:801` — "6 active plans declare `parent_epic: tradfi_master`" + `assigned_vm: vm-tradfi` (line
  33, violates CLAUDE.md `{planning, NA}` only) + `last_updated: 2026-06-20` (body has 2026-08-03 events)
- Reality: `rg -l "^parent_epic: tradfi_master" plans/active/` → **23 docs**; section lists
  `tradfi_multisource_ao_dispatch_2026_07_25` (archived 2026-08-03) as active; omits 17 live children incl. all
  batch6/7/8 satellites, finalize docs, g1_g5, phase_d_terminal_gate
- **Impact**: workers/readers using the epic as the tranche map miss 17 plans and see a dead one first. `assigned_vm`
  schema violation. Epic is `locked_by: live-defi-rollout` — cannot auto-fix.
- **Authoritative**: CLAUDE.md/PLAN_FORMAT for schema; `rg` corpus for count. The epic's auto-populate script was last
  run 2026-06-20.

### P2 — Material drift (state wrong; dispatch effect indirect)

**F5. Chain-bundle sampler: hub says "0 open todos (closed)" — doc has open P1-OPERATOR-DECISION.**

- Hub: `tradfi_consolidated_closeout_2026_07_18.md:896-897` — "(0 open todos (closed/archived/record-only…))"
- Issue: `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md:168` — open `[DATA] P1-OPERATOR-DECISION` (CBOE/VX
  root mismatch), `status: open`
- **Impact**: hub's cited dependency (phase_d gate) depends on this finding's resolution — gate reads wrong state.

**F6. "0 open todos (closed/archived/record-only)" misclaims on three ACTIVE docs with 1 open each.**

- Hub lines 830, 854, 886 claim 0 open for `instruments_docs_audit`, `phantom_audit`, `instruments_remaining_work`
- Reality: each has 1 open (P1 REVIEW, P2, and **P0** respectively — all `status: open`, none archived)
- **Impact**: the remaining_work P0 becomes invisible to anyone trusting the hub.

**F7. OOM digest: hub lists 2 open items — doc has 0 open (both DONE).**

- Hub: `tradfi_consolidated_closeout_2026_07_18.md:651-655` — env override + memray listed as open
- Issue: `tradfi_backfill_oom_remediation_2026_06_24.md` — both `[x]` (DONE 2026-07-14/27), 0 open

**F8. adapter_findings digest: 3 items listed open — 2 are `[x]`, 1 open.**

- Hub lines 804-808 vs `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md:206,219`

**F9. mdps_deadcode digest: 8 items listed open — 4 are `[x]`; 4 open.**

- Hub lines 838-848 vs `mdps_features_deadcode_consolidation_2026_07_20.md:87-107`

**F10. Candle canonical-path migration: hub says "(16 open — nearly all P0)" — doc is ARCHIVED with 0 open.**

- Hub lines 750-752 vs `plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md:15-16` — "status:
  complete … verified zero open todos (all 17), archived 2026-07-28"
- **Impact**: false "P0 open" claims; no live mis-route since doc is archived, but misleading.

**F11. mtds_available_at digest: BLOCKED-OPERATOR-DECISION items listed under "(archived 2026-08-05, all 16 todos done)"
— archived doc has an open checkbox beneath the "all done" banner.**

- Hub lines 575-579 vs `plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md:58,525` — orphan_reap
  P1 checkbox never migrated before archival (archival-ritual violation).

**F12. data_completion digest "(stale fork; 20 open — capped)" vs 15 open (17 incl. nested).**

- Hub line 594 vs `data_completion_tradfi_2026_07_15.md` — "stale fork" label fair; count 5 off.

**F13. mdps base-plan digest "(28 open — capped)" vs 3 open.**

- Hub lines 770-775 vs `data_pipeline_check_mdps_features_2026_07_20.md` — mass-closed by 2026-07-27 session; finalize
  twin exists to reconcile it.

### P3 — Stale refs / cosmetic

**F14. Combo-leg issue vs migration-design "0 open"**: two docs dispute whether the design doc ever genuinely closed.
Both closed/archived.

**F15. Smoketest "0 tradfi-scoped open" claim**: hub line 444 vs `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`
— 3 open. Partially reconcilable via "tradfi-scoped" qualifier, but absolute phrasing false.

**F16. Legacy-id digest already stale again**: hub line 909 ("CORRECTED 2026-07-30…") listing 4 items — all 4 `[x]` in
`tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`, which gained a new open P2 (line 342, 2026-07-31 null-id
repair) after the correction.

**F17. 2026-07-27 finalize twins**: frontmatter `status: active` vs body banner "STATUS: `draft` — NOT dispatched" with
no documented rationale (unlike batch6/7 finalizes which cite the 2026-07-30 ruling). Both carry `depends_on` +
`gate_on_depends: true` — machine gate holds; risk limited to status readers and missing rationale.

**F18. Epic routing table stale pointer**: `tradfi_master.md:91` — "canonical migration COMPLETE; superseded_by
data_completion_to_100_all_ag_2026_06_21, the live owner" — the "live owner" pointer is stale (canonical migration moved
through two more docs, the current one still has an open P1). "COMPLETE" premature.

## Doc-drift

Covered by contradiction findings above. The hub closeout (`tradfi_consolidated_closeout_2026_07_18.md`) is the single
largest source of drift — its aggregated digests systematically lag cited docs across all but 2 of ~20 digest sections.
The hub's own 2026-07-31 sweep note (lines 348-357) establishes digests are known-stale-prone; the 2026-08-04 refresh
updated the MVP table but not the digests.

## Hygiene fixes

1. **Zero-checkbox doc → canonical todos** (`mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`):
   Converted 3 prose follow-up items into canonical `- [ ] [INFRA] P1.` todos. Commit: `bacb5ed66`.

## Filed

## Archive candidates (operator review)

4 fully-done docs identified (0 open todos, all `[x]`):

| Doc                                                      | Open | Done | Locked?                   | Cross-refs | Verdict                                                                                    |
| -------------------------------------------------------- | ---- | ---- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------ |
| `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` | 0    | 5    | No                        | 4          | **Deferred** — 4 cross-refs in other tranches; sharded run can't verify all referrers safe |
| `autonomous_session_operator_decisions_2026_07_25.md`    | 0    | 2    | No                        | 42         | **Deferred** — 42 cross-references; too risky in a sharded run                             |
| `tradfi_backfill_oom_remediation_2026_06_24.md`          | 0    | 12   | YES (`live-defi-rollout`) | 8          | **BLOCKED** — locked plan, never auto-archive                                              |
| `tradfi_canonical_path_migration_design_2026_07_19.md`   | 0    | 1    | YES (`live-defi-rollout`) | 9          | **BLOCKED** — locked plan, never auto-archive                                              |

## Refuted (dropped by verify)

## Coverage (hunters / batches / docs)

- Tranche: tradfi
- Docs in scope: 61 (20 active plans + 37 issues + 1 epic + 3 normative refs)
- Grace (read-only): 27
- Non-grace (editable): 34
- Normative refs: PLAN_FORMAT.md, task_template.md, INDEX.md, ACTIVE_INDEX.md
- Hunters dispatched: 2 — **both complete**
  - **Missed-flip hunter** ✅ — 34/34 docs, 0 P0/P1, 5 P2/P3 (all code-quoted artifacts)
  - **Contradiction hunter** ✅ — full corpus, 0 P0, 4 P1, 9 P2, 5 P3
- Direct scan: 4 archive candidates checked, 1 zero-checkbox converted

## Deferred work after 2026-08-07

| Item                                                                                         | State / why deferred                                                                                                                                          | Blocked on                    |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **P1 F1**: Hub ES MVP-cell row stale (manifest-verify DONE 2026-07-30, zero-capture)         | Hub closeout needs MVP-table row update to reflect g1_g5's 2026-07-30 execution + `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md` filing.                    | Hub edit (large doc, careful) |
| **P1 F2**: Hub sp500 digest BLOCKED-OPERATOR-DECISION stale (closed 2026-07-31)              | Hub closeout digest needs count + status update.                                                                                                              | Hub edit                      |
| **P1 F3**: Hub g1_g5 digest count 14→6                                                       | Hub closeout digest needs recount from plan source.                                                                                                           | Hub edit                      |
| **P1 F4**: Epic child index (6→23), invalid `assigned_vm`, stale `last_updated`              | Epic is `locked_by: live-defi-rollout`. Needs operator `[unlock-plan]` + rerun `populate_epic_bodies` or manual fix.                                          | Operator `[unlock-plan]`      |
| **P2 F5-F13**: Hub digest drift (9 findings)                                                 | Every hub digest section lags its cited doc. Systemic — needs a re-derive pass, not point fixes. Saturday `all`-tranche run or dedicated hub-refresh session. | Hub refresh session           |
| **P3 F14-F18**: Stale refs / cosmetic (5 findings)                                           | Low priority; fold into next hub refresh.                                                                                                                     | Hub refresh session           |
| Archive: `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` (0 open, 5 done, unlocked) | Deferred — 4 cross-refs in other tranches. Needs `all`-tranche run or manual verification.                                                                    | Cross-tranche verification    |
| Archive: `autonomous_session_operator_decisions_2026_07_25.md` (0 open, 2 done, unlocked)    | Deferred — 42 cross-references. Too risky in a sharded run.                                                                                                   | Cross-tranche verification    |
| Archive: `tradfi_backfill_oom_remediation_2026_06_24.md` (0 open, 12 done)                   | BLOCKED — `locked_by: live-defi-rollout`. Operator must unlock before archival.                                                                               | Operator `[unlock-plan]`      |
| Archive: `tradfi_canonical_path_migration_design_2026_07_19.md` (0 open, 1 done)             | BLOCKED — `locked_by: live-defi-rollout`. Operator must unlock before archival.                                                                               | Operator `[unlock-plan]`      |

**Recommended next items** (priority order):

1. **Operator**: review P1 F4 (epic `assigned_vm` + child index) — unlock epic, fix schema + rerun populate
2. **Saturday `all`-tranche run**: handle 2 deferred cross-tranche archives + re-derive hub digests (F1-F3, F5-F13 would
   all collapse if the hub's digests are re-derived from live checkbox state)
3. **Next tradfi reconciler run**: verify F1-F3, F5-F13 resolved after hub refresh

## Lessons

- **Sharded run limitation**: With 27/61 docs in the grace window, the non-grace corpus was 34 docs — direct scan more
  efficient than full 10-agent fan-out.
- **Archive candidates in sharded runs**: Cross-tranche archival caution correctly blocked 2 archives. Saturday `all`
  run is the right place.
- **`locked_by: live-defi-rollout`** blocked 2 archives + 1 epic fix. Most common lock value in tradfi.
- **Missed-flip P2s are code-quoted documentation artifacts**: All 5 hunter-confirmed "missed flips" are inside backtick
  code spans or SUPERSEDED sections — not real mechanical checkboxes. False-positive signal for future hunter prompts.
- **Hub closeout is the single largest drift surface**: The contradiction hunter found that
  `tradfi_consolidated_closeout_2026_07_18.md`'s aggregated digests systematically lag cited docs across ~18 of ~20
  digest sections. The hub's own 2026-07-31 sweep note admits this. A re-derive pass (grep every cited doc's live
  checkbox state) would collapse 12 of 18 findings at once. The hub is a coordination convenience, not an SSOT — but
  readers treat it as one, and that gap creates real mis-routing risk (F1, F2, F6).
- **Epic auto-populate has not run since 2026-06-20**: `tradfi_master.md`'s child-plan index is ~2 months stale (6→23
  children). The script exists (`populate_epic_bodies_2026_05_21.py`) but isn't on a cron. Worth wiring into the weekly
  reconciler cadence or the plan-hygiene sweep.
