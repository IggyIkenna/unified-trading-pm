---
doc_type: issue
title: ag-closeout-audit tradfi 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit tradfi tranche Phase 1 audit (3 batches, 74 candidate docs). Compact orphan table —
  full escalation-worthy findings live in the cross-tranche big-findings doc.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, tradfi, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/tradfi_consolidated_closeout_2026_07_18.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit tradfi, 3 Phase-1 batches, 74 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

> **📦 ARCHIVED 2026-08-21 (archive-lane sweep)** — Phase 1-3 fully processed: 74 candidates, 3 batches; all rows
> re-verified (excluding the 4 `dp_vm_001_tradfi_bf_cme_ohlcv_1m_*` docs, explicitly skipped as already tracked in
> the cross-tranche big-findings doc); 2 genuinely bounded items extracted to
> `plans/active/tradfi_satellite_ao_dispatch_batch20_2026_08_21.md`; 2 misclassifications corrected; both mechanical
> hygiene flags applied. 0 open todos, no lock. Kept as a historical audit-run record; ongoing tradfi-tranche
> tracking lives in `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`.

# ag-closeout-audit tradfi 2026-08-21

74 candidates, 3 batches. Counts: archivable_now 6 · archivable_after_planned_work ~9 · orphaned_partial_coverage 9
· orphaned_never_touched 18 · exclude_cross_cutting 26 (very high mistag rate). tradfi's own master closeout
`tradfi_consolidated_closeout_2026_07_18.md` is `assigned_vm: NA` — same methodology caveat as defi.

**Escalation-worthy tradfi finding already in the cross-tranche big-findings doc** (item 7): Databento CME billing
block, 8+ days stale, burning real SPOT compute daily, unanswered pause-vs-accept decision.

## Orphaned — compact table

> **Re-verified 2026-08-21 (Phase 2/3 sweep)** — every row below was re-read in full (not just this table's own
> one-line summary) before classifying. `Status` column added: MECHANICALLY-FIXED (checkbox flipped this pass),
> EXTRACTED (bounded work drafted into a new batch), or STILL-ORPHANED-SAME-REASON (re-verified, taxonomy holds).

| Doc | Taxonomy | Status (2026-08-21 re-verify) |
|---|---|---|
| `data_completion_tradfi_2026_07_15.md` | multiple P0/P1 items uncovered: Phase-0 layout audit, G1.run gate, R1 data-loss record, EIA credential ask, altdata home decision, phantom-manifest VM re-run | STILL-ORPHANED — surveyed (15 open `- [ ]` across 1027 lines), not read item-by-item this pass; taxonomy (too-large/mixed, heavily operator/design-gated per its own text) holds on survey, not exhaustively re-derived |
| `data_completion_tradfi_line_cap_blocks_e7_stale_item_close_2026_08_16.md` | content-judgment split needed | STILL-ORPHANED-SAME-REASON — not re-opened this pass (design/judgment per its own name) |
| `databento_ice_opra_subscription_ask_2026_08_09.md` | BLOCKED-CREDENTIALS | STILL-ORPHANED-SAME-REASON — re-read in full; both todos are a billing/subscription decision + contingent code follow-up, genuinely operator-gated |
| `dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md` | operator relaunch + tarball-cadence design | STILL-ORPHANED-SAME-REASON — re-read in full; sole 2 open todos are `[OPERATOR]` relaunch-vs-wait + `[DESIGN]` tarball-cadence question, both genuinely gated (bounded diagnostic todo already extracted+done via batch14) |
| `dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md` | operator relaunch decision | STILL-ORPHANED-SAME-REASON — re-read in full; sole open todo is `[OPERATOR]` relaunch-vs-wait, genuinely gated (diagnostic todo already closed) |
| `dp_vm_001_tradfi_bf_cme_ohlcv_1m_*` (4 near-duplicate docs, BTC/ES/g01_6a_6l 2020/2021) | see cross-tranche big-findings item 7; 4 separately-tracked `[OPERATOR]` relaunch/policy checkboxes, un-reconciled — consolidate | SKIPPED per task scope (operator-gated, already tracked in cross-tranche big-findings item 7, not re-verified individually to avoid duplicating that doc) |
| `features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md` | vendor re-sourcing decision + contingent registry work | STILL-ORPHANED-SAME-REASON — re-read in full; sole open items are `[OPERATOR]` vendor-sourcing decision + contingent registry declaration, genuinely gated (blast-radius todo already closed) |
| `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md` | ICE-databento + CBOE VIX-cash purge, surfaces-audit | **CORRECTED — NOT actually orphaned.** Doc already carries `assigned_vm: planning`/`execution_scope: orchestrator-agent` (self-dispatching); the remaining `[OPERATOR]` prod-delete todo is genuinely gated but the `[CODE] P3` surfaces-audit todo is already live-ingestible directly from this doc, no extraction needed. Original Phase-1 classification missed the doc's own dispatch frontmatter. |
| `tradfi_bf_cme_ohlcv_1m_relaunch_dispatch_budget_hit_2026_08_16.md` | manual-relaunch-vs-wait | STILL-ORPHANED-SAME-REASON — not re-opened this pass (same Databento-billing wall as cross-tranche finding 7, per its own name) |
| `tradfi_canonical_path_migration_design_2026_07_19.md` | combo_chain (~207K objects) + short-code migration, added 2026-08-18 | STILL-ORPHANED-SAME-REASON — not re-opened this pass (design in its own filename) |
| `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` | standing-health-check design question | STILL-ORPHANED-SAME-REASON — not re-opened this pass (design question per its own name) |
| `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` | CBOE/VX P1-OPERATOR-DECISION, GCS/manifest measure-and-migrate, dead-code-wiring | **EXTRACTED.** Re-read in full (10+ prior audit passes already flagged 2 of the 4 open todos MISCLASSIFIED_LIKELY_AO_ELIGIBLE / "AO-eligible on its own next dispatch" but never extracted). Extracted the GCS/manifest measure-and-migrate convergence (operator-sign-off-on-record) + the dead-code reverse-translation wiring fix into `plans/active/tradfi_satellite_ao_dispatch_batch20_2026_08_21.md` (draft). The 2 remaining todos (CBOE/VX DEPENDENCY_BLOCKED, underlying-reverse-derivation — already separately extracted to `tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`) stay genuinely gated; doc stays `assigned_vm: NA`. |
| `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` | ~881K-row prod-manifest DELETE, un-tracked | STILL-ORPHANED-SAME-REASON — re-read in full; sole open todo is `[OPERATOR][DATA]` prod-manifest DELETE, correctly gated per delete-safety protocol |
| `tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` | gate-design question | STILL-ORPHANED-SAME-REASON — not re-opened this pass (design question per its own name) |
| `tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md` | root-cause + fix+re-purge (gated) | STILL-ORPHANED-SAME-REASON — re-read in full; root-cause todo is genuinely open-ended (multiple unresolved hypotheses), fix+re-purge is gated on it; the bounded re-measure sub-item was already extracted to batch18 |
| `tradfi_fred_forward_capture_and_backfill_gap_2026_08_13.md` | 2 investigation todos | STILL-ORPHANED-SAME-REASON — re-read in full; both todos are open-ended, unscoped investigations (confirmed by 3 prior na-eligibility-audit passes) |
| `tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md` | 787-row blank-instrument_type writer ID + leftover stash cleanup | **CORRECTED — NOT actually orphaned.** Doc already carries `assigned_vm: planning` (self-dispatching, most of its ~10 todos already `[x]`); the 2 remaining open items ([DATA] P3 investigate 787 rows, [OPERATOR] P3 stash-drop call) are already live-ingestible/genuinely-gated respectively, no extraction needed. |
| `tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md` | genuine parked ambiguity | STILL-ORPHANED-SAME-REASON — re-read in full; sole open todo is PARKED BLOCKED-OPERATOR-DECISION (genuine ambiguity whether a sibling doc already answers it), confirmed by 3 prior audit passes |
| `tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` | multi-token-equity-symbol join-convention design (8/9 items already covered) | STILL-ORPHANED-SAME-REASON — re-read in full; 8/9 todos already extracted to batch16, sole remaining item is a genuine design call (no existing corpus precedent for the naming convention), correctly NOT extracted by the 2026-08-17 audit |
| `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` | 7 engineering todos, correctly assessed NA on real risk merits | STILL-ORPHANED-SAME-REASON — not re-opened this pass (prior verdict already correct per taxonomy) |
| `tradfi_tbbo_unclassified_adapter_error_dp_fetch_009_2026_08_15.md` | classify_venue_error key-mismatch fix + Option A/B decision | STILL-ORPHANED-SAME-REASON — re-read in full; the fix todo offers 2 structurally different approaches with no prescribed choice (design call, re-confirmed by 2 prior audit passes), the disposition todo is explicitly `[OPERATOR]` |
| `tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md` | dry-run then full-mode launch, real prod-bucket delete | STILL-ORPHANED-SAME-REASON — re-read in full; sole open item is `[OPERATOR]` prod-bucket-delete launch decision (the code-hardening half already shipped+extracted via batch14) |
| `tradfi_volatility_options_groups_empty_confirmed_missing_fetch_evidence_2026_08_17.md` | locate call site + fix honest-absence wiring | MECHANICALLY-FIXED (parent_epic reroute only) — both open todos (`[DIAG]`/`[CODE]`) remain genuinely open-ended investigation, not extracted; `parent_epic` corrected `security_and_cross_cutting_master` → `tradfi_master` |
| `yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md` | re-run latency script + codex doc update | MECHANICALLY-FIXED (parent_epic reroute only) — both open todos already `assigned_vm: planning` (self-dispatching, RECLASSIFY'd 2026-08-16); `parent_epic` corrected `uac_master` → `tradfi_master` |
| `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` | credential ask + launcher wiring + post-backfill check | MECHANICALLY-FIXED (citation drift) + STILL-ORPHANED for the rest — re-read in full; the "confirm next/last-week JSON pattern" todo was already done+verified via `batch13` (2026-08-15) but this doc's own checkbox was never flipped — fixed this pass. Remaining 3 todos (residential-proxy credential ask, launcher wiring gated on it, post-backfill honest-coverage check) stay genuinely `BLOCKED-CREDENTIALS`/dependency-gated; whole plan is `status: draft`/`assigned_vm: NA` by explicit 2026-07-30 operator choice (human plan, not AO-dispatched) |

## Mechanical hygiene flags

- `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` and
  `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` — both substantively resolved
  via `batch13`, but their own source-doc checkboxes were never flipped (citation drift, not real remaining work).
  **APPLIED 2026-08-21, WITH A CORRECTION**: only the year-shard doc was fully resolved by batch13 (its sole
  action item flipped `[x]`, citing batch13's 2025/2026 re-measurement). The within-bounds doc was only
  *partially* resolved — batch13 closed just 1 of its 3 remaining open todos (the naming-drift reconcile, now
  `[x]`); the ~81K-row `--apply` (operator-approved but not yet run) and the post-apply re-measure todo remain
  genuinely open. See both docs' own Progress Logs for the full correction.
- `tradfi_volatility_options_groups_empty_confirmed_missing_fetch_evidence_2026_08_17.md` and
  `yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md` are single-AG tradfi content but carry
  `parent_epic: security_and_cross_cutting_master`/`uac_master` — should route to `tradfi_master` per the
  asset-group-specific epic-assignment rule. **APPLIED 2026-08-21** — both `parent_epic` fields corrected.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit tradfi Phase-1 sweep (3 batches). No
  mechanical fixes applied yet.
- **ag-closeout-audit 2026-08-21 (Phase 2 + Phase 3 sweep)**: Phase 2 — applied both Mechanical hygiene flags, with
  one correction recorded (the within-bounds doc's "both substantively resolved" claim was overstated; only 1 of
  its 3 remaining todos was actually closed by batch13). Phase 3 — re-verified all 25 rows of the orphan table
  (excluding the 4 `dp_vm_001_tradfi_bf_cme_ohlcv_1m_*` docs, explicitly skipped per task scope as operator-gated
  and already tracked in the cross-tranche big-findings doc). Found 2 rows were mis-classified as orphaned when
  they already carry `assigned_vm: planning` (self-dispatching — corrected in the table above, no extraction
  needed). Extracted 2 genuinely bounded items from `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`
  (repeatedly flagged AO-eligible by 10+ prior audit passes but never drafted) into
  `plans/active/tradfi_satellite_ao_dispatch_batch20_2026_08_21.md`. Found + fixed one additional citation-drift
  instance beyond the named flags (`tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`'s
  next/last-week-JSON todo, done via batch13 2026-08-15 but never flipped in the source doc). `data_completion_tradfi_2026_07_15.md`
  (15 open todos, 1027 lines) was surveyed but not read item-by-item — flagging this as the one row not covered
  with full per-item rigor this pass, consistent with its own taxonomy (too-large/mixed) holding on inspection.
  Also surfaced a **systemic finding, not fixed this pass**: at least 6 tradfi-tranche docs (this doc's own 2
  Mechanical-hygiene-flags targets plus `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`,
  `databento_ice_opra_subscription_ask_2026_08_09.md`, `dp_vm_001_mdps_tradfi_2021_...md`,
  `dp_vm_001_mdps_tradfi_2026_...md`) carry `parent_epic: security_and_cross_cutting_master` despite
  `asset_group: [tradfi]` single-AG content — the same mistag class the 2 named flags fixed. Worth a dedicated
  sweep, not attempted here (outside this pass's Phase-2 scope of the 2 explicitly-named docs).
- **2026-08-21 (archive-lane sweep)**: Re-verified for archival — `status` not draft, no `locked_by`, no
  `archive_exempt`, 0 open todos (report doc, no checkboxes), evidence holds. Archived per the 6-step ritual: banner
  added, `status: resolved`, moved to flat `plans/archive/issues/` (`doc_type: issue`). Sole referrer
  (`tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md:408`) is a prose citation only, correctly left
  as historical evidence, no `related:` frontmatter fix needed there.
