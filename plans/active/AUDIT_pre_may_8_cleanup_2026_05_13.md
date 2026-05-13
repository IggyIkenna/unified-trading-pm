---
title: Pre-May-8 Plans Cleanup & Completion Audit
type: coordination-doc
status: active
created: 2026-05-13
deadline: 2026-05-15
estimate_class: design
estimate_calibrated_ai_days: 1.5
---

## Executive Summary

Audited all 26 plans dated ≤2026-05-08 after fresh rebase from origin/live-defi-rollout. **Key finding: All 26 plans have remaining work (1+ TODOs).** No plans are complete enough to archive.

**Categorization approach**: Instead of "ready to archive" vs "active," plans are grouped by blocker type and deadline criticality. Action for each: identify blockers, mark deferred items, assign ownership.

**Metadata**: 60 commits landed during audit on origin (rebase conflict resolved by taking remote versions on cross_asset_group_catalogue_audit + dex_perp_and_venue_data_expansion, which have concurrent agent work).

---

## CRITICAL PATH (Deadline: 2026-05-15 to 2026-05-23) — Unblock & Ship Now

These 8 plans are on the May-23 critical path. All have either no blockers or blockers that are operator-resolvable in real time.

1. **alerting_service_live_rules_2026_05_07.md** (22 TODOs) — 38/60 done. Phases 1,2,5,6 ✅; Phases 3,4,7,8,9 open. Credentials available (Secret Manager + deployment-services VM). **Blocker:** None (PagerDuty Phase 4 deferred post-cutover). **Next:** Ship Phases 3,7,8,9 (est. 2-3d).

2. **api_football_minimal_flattening_removal_2026_05_07.md** (5 TODOs) — 11/18 done. Phases 1/2 ✅; Phase 3.B/3.C executable (credentials available). **Blocker:** None. **Next:** Execute Phase 3 smoke + forward-poll (1d), then ship Phases 4-5.

3. **cross_cutting_may_23_deliverables_2026_05_08.md** (13 TODOs) — 15/31 done. Catalogue + strategy ID ✅; Open: catalogue UI wiring, client setup, DART lane. **Blocker:** None. **Next:** Confirm Harsh ownership of catalogue UI, track in daily splits.

4. **defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md** (23 TODOs) — 17/40 done. Streams A+B ✅; Streams C/D/E open. **Blocker:** None. **Next:** Assign Streams C/D/E to slots (codex backports + config schema, est. 2–3d).

5. **defi_master_2026_05_07.md** (80 TODOs) — 23/103 done (22%). Multi-slot umbrella (14.1 cal AI-days baseline). **Blocker:** None (executors assigned per daily splits). **Next:** Delegate per-phase ownership per master plan priority ordering.

6. **deploy_missing_auto_launch_2026_05_07.md** (8 TODOs) — 6/14 done. Phases 0-1 ✅; Phases 2–4 straightforward (UI + docs). **Blocker:** Resolved (Q1 on calendar pre-skip logic). **Next:** Ship Phases 2–4 (est. 1-2d) OR defer if lower priority per daily splits.

7. **gcs_migration_bundle_pipeline_mode_2026_05_08.md** (OPERATOR-GATED) — 6/12 done. Design + Phases 1/2/5.1/7 ✅. **Blocker:** Phase 3 VM fleet scope (which DeFi shards, compute tier) — operator decision needed. **Next:** Answer Phase 3 scope (30m), execute Phase 3, ship Phases 4–9 (est. 3–4d total).

8. **manifest_cross_asset_rescan_design_2026_05_08.md** (3 TODOs) — 2/5 done. Axis extensions ✅; 5-VM dry-run in-flight. **Blocker:** Pending operator answers (Q1 triage cadence, Q2 per-asset cost, Q3 sequencing vs gcs_migration). **Next:** Answer Q1/Q2/Q3 (1h), monitor dry-run, execute reconciler launch (est. 1d).

---

## NEAR-CRITICAL (Deadline: 2026-05-15 to 2026-05-20) — Resolve Blockers, Then Ship

These 5 plans block other critical work. Blockers are mostly design questions or schema gates that require operator input.

9. **available_at_lookahead_bias_completion_2026_05_08.md** (33 TODOs) — 18/55 done. Phase 0 SSOT ✅; CeFi/TradFi/Sports/Predictions partial; Phase 2–10 mostly open. **Blocker:** Design question on `enforce_available_at=True` for non-tick MTDS paths. **Next:** Resolve design Q (est. 30m), fan out TAB work for Phases 2–4 stamping.

10. **aws_migration_defi_first_2026_05_07.md** (64 TODOs) — 8/72 done (11%). Phases 0/2/5 ✅; ~70 GCS-URI sites remain. **Blocker:** Phase 1.5B–D design (Pub/Sub parity, tarball parity, scripts). **Next:** Rebase already complete (incoming 4 commits landed); audit GCS→S3 sites, ship Phase 1.5.

11. **expected_universe_v2_design_2026_05_08.md** (15 TODOs) — 0/15 done. Design complete + paste-ready. **Blocker:** Gated on `manifest_schema_final_gate_2026_05_09` (v8 schema). Also needs Q1/Q2 operator answers (cefi venue-sharding, denominator cache). **Next:** Answer Q1/Q2 (30m sync), wait for schema gate, then 1-day implementation.

12. **live_pipeline_mtds_mdps_features_2026_05_08.md** (UPSTREAM-GATED) — 13/18 done (P0, deadline 2026-05-23). **Blocker:** Depends on `features_repo_consolidation` (deadline 2026-05-13, status TBD) + `gcs_migration_bundle_pipeline_mode` Phase 3. **Next:** Verify upstream unblocks, then ship Phases 3-5.

13. **writegate_honest_coverage_endtoend_2026_05_06.md** (142 TODOs) — 104/246 done (42%, LARGEST plan). Phases 1A/1C/2E.1/2E.2(partial)/3D.1–4/Wave4(a)(b)/4.A/4.B/5(partial) ✅; Phases 2B/2C/2E.3/3B/3C/3D.5/Wave3/Wave4(c) open. **Blockers:** Phase 2B decision made (not built); Phase 3E.3 audit (3–4d); Phase 3D.5 catalog-driven enum (8–12d); Wave4(c) per-service rollout (15–20d). **Next:** Triage scope into May-23 critical vs. post-cutover; ship critical, defer post-cutover.

---

## BLOCKED ON UPSTREAM (Deadline: 2026-05-15 to 2026-05-20) — Unblock Pre-Req, Then Proceed

These 3 plans cannot proceed until upstream plans resolve.

14. **data_status_comprehensive_test_coverage_2026_05_07.md** (UPSTREAM-BLOCKED) — 0/30 done. **Blocker:** Depends on `data_status_drilldown_shard_atom_alignment` Phase 6 (in-flight; Phase 7 pending). **Next:** Block until Phase 6 upstream ✅, then assign to test-focused slot (est. 3–4d).

15. **data_status_drilldown_shard_atom_alignment_2026_05_07.md** (16 TODOs) — 25/41 done. Phases 1–5 ✅; Phase 7 (pagination) open. Named successor drifts (canonical_question_group not in ROW_KEY, cross-registry consistency test). **Blocker:** None (direct work). **Next:** Ship Phase 7 pagination (4h), migrate named-successor drifts to successor plans.

16. **mdps_streaming_and_backpressure_2026_05_07.md** (7 TODOs) — 3/14 done. **Blocker:** Phase 1.2B architectural decision (dual-SSOT lifecycle collision, 3 options in issue doc). Phases 2+ deferred pending 1.2B. **Next:** Operator triage issue (30m), resolve design, ship Phase 1.2B + Phases 2–4 (est. 3–4d).

---

## FALSE POSITIVE BLOCKERS FOUND (HIGH PRIORITY FIX)

One plan has a critical false positive that needs immediate correction.

17. **deployment_ui_lifecycle_tabs_2026_05_08.md** (BLOCKER FOUND) — 4/37 done. **FALSE POSITIVE:** A.2 checkbox marked done but `vm_zombie_watchdog.py` dict registration never shipped (5 missing lines + VM dict entry). **Blocker:** Implementation incomplete, not code-complete. **Next:** Re-open A.2 checkbox, ship 5 lines + dict registration (new VmPrefixSpec entries for live-* and exp-* VM name prefixes per deployment-ui-architecture.md), then ship Phases B–G (est. 2–3d for full completion).

---

## SCHEMA & DECISION GATES (Deadline: 2026-05-13 to 2026-05-15)

These 2 plans have concrete operator decisions that are P0 blockers for the schema freeze.

18. **wave3x_residual_ssots_2026_05_08.md** (6 TODOs) — 16/22 done. Track D case-D (zero-activity bars) deferred post-cutover. **DECISION ALREADY MADE:** `EXPECTED_KNOWN_SOURCE_GAP` → UAC enum already shipped (Option A, UAC@174f401, 2026-05-11). **Next:** Update Track D status row to "done — UAC shipped"; resolve Track E features-sports wiring (Harsh Slot 4).

19. **mtds_databento_path_streaming_2026_05_07.md** (EXECUTION-GATED) — 1/4 done. Phase 1 ✅; Phases 2/3 P2 optional. **Blocker:** Phase 4 D3 deployment gate (VM backfill validation, confirms data stability before production deploy). **Next:** Run Phase 4 Databento backfill VM validation (est. 1d), unblock master plan deployment gate.

---

## POST-CUTOVER or EXPLICIT OUT-OF-SCOPE (Deadline: after 2026-05-23)

These 2 plans are explicitly deferred post-May-23 cutover or are P2 Q3+ items.

20. **cme_polymarket_arb_2026_05_08.md** (2 TODOs) — 2/7 done. **Status:** Explicitly NOT on May-23 critical path. Phases 2–5 blocked on `predictions_master` Phase 5 + `tradfi_master` Q1/Q2. **Next:** Defer to Q2 2026 per master plan; update with cross-reference to post-cutover roadmap.

21. **fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md** (Q3+ institutional onboarding) — 17/35 done. **Status:** Explicitly P2, post-2026-05-23. **Next:** Archive with cross-reference to post-cutover roadmap.

---

## DEFERRED ITEMS (Move to Active Successor Plans)

These 3 plans have significant deferred work that needs named successor plans.

22. **launcher_scripts_consolidation_into_deployment_service_2026_05_07.md** (11/15 done, 11% deferred) — Phases 0/1/4 ✅; Phases 2/3 deferred (registry extension + AWS audit pending upstream completion). **Action:** Mark Phases 2/3 as deferred, create `plans/active/issues/launcher_scripts_registry_extension_aws_audit_<YYYY_MM_DD>.md` with successor plan reference.

---

## Notes

- **Fund Admin (2026-04-20)**: Originally included in 26 pre-May-8 plans; explicitly moved to archive in this session with cross-reference to post-cutover roadmap (Q3 institutional onboarding).
- **Features Repo Consolidation**: Deadline was 2026-05-13 (today). Status TBD from last agent's work; verify final 2 TODOs are actually done and push to completion to unblock live-pipeline.
- **Credentials available**: Secret Manager + deployment-services VM service accounts enable all Phase 3 smoke tests and credential-gated operations to run immediately (not deferred).
- **Rebase complete**: Rebased to origin/live-defi-rollout post-fetch; 60 commits landed on remote during audit.
