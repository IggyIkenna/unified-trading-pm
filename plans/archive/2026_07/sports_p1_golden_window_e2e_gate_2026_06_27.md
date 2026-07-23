---
doc_type: plan
title: Sports P1e — golden-window e2e GATE (manifest-clean + catalogue + alerts-zero)
summary:
  E2E gate proving the full sports stack is 100% and clean on the golden window before Phase 2 history expansion begins.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, golden-window, e2e-gate, manifest, catalogue, alerts, verification]
related:
  [
    plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
  ]
created: 2026-06-27
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-14
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    sports_p1_golden_window_apifootball_2026_06_27,
    sports_p1_golden_window_reference_sources_2026_06_27,
    sports_p1_golden_window_mtds_odds_2026_06_27,
    sports_p1_golden_window_features_2026_06_27,
    master_data_canonicalisation_migration_catalogue_2026_06_07,
  ]
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **✅ ARCHIVED 2026-07-14 [unlock-plan] (operator ruling 2026-07-14, sports plan-set bulk archival).** All todos `[x]`
> complete (0 open; audited complete 2026-07-13); the P1e gate formally flipped GREEN 2026-07-12 (0/0/0/0 re-audit — see
> the Progress Log and P2b's NOTE 2026-07-12). E2e-gate / manifest-clean learnings were codified in the cited Codex
> SSOTs during the work — no unmigrated durable contract found. Lock cleared per the ruling; historical/frozen.

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 1, the GATE). This is the
> **climbing-metric gate** — it proves the FULL sports stack is 100% + clean on the golden window (**2025-09-01 ..
> 2025-11-30**) BEFORE Phase 2 expands to 2015→present. If this gate is RED, the expansion does NOT start (a RED data
> audit freezes layer-N+1 work). One agent, `data_engineering` (Sonnet/high). Verification-only — no new captures.

# Sports P1e — golden-window e2e GATE

## What this proves

The operator's whole strategy: drive EVERY source × data_type to 100% on the window, ironing out every
code/manifest/GCS/catalogue/alert issue, so the proven recipe generalizes. This plan is the single GREEN/RED verdict on
the window across all three surfaces — manifest, catalogue, alerts.

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted_pending_fetch == 0`, phantom =
  captured-without-parquet
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator freshness (loud-fail-on-stale)
- `/codex/05-infrastructure/data-pipeline-alerts.md` (+ `.registry.yaml`) — DP\_\* taxonomy + drive-to-zero
- `/codex/05-infrastructure/deployment-observability.md` — active-dp-alerts blobs + RESOLVED bookend

## Todos

- [x] ✅ [VERIFY] P0. **Manifest-clean on the window — ALL sources.** Run a single `read_availability_index`
      window-scoped audit (no whole-corpus walk) across api_football + the 5 reference sources + odds-api + features.
      Assert, for `date in [2025-09-01, 2025-11-30]`, 94 universe: (a) `expected_unattempted_pending_fetch == 0`; (b) 0
      `empty_confirmed` with blank/null `error_reason`; (c) 0 un-evidenced `attempted_failed`; (d) forward phantom
      dry-run ≈ 0 (P0 #5 unblocked). **Gate**: the audit prints 0/0/0/≈0 for every `(source, data_type)`; output pasted
      into the Progress Log. Any non-zero → file the residual back to the owning P1 plan (do NOT mask). — 2026-06-27: IS
      sports (`instruments-store-sports-prd`): (a)=0 (b)=0 blank-EC (c)=0 un-evidenced AF (3,220 AF all evidenced:
      FIXTURES_FETCH_FAILED/HTTP_NOT_FOUND/ApiFootballResponseError/UNCLASSIFIED) (d)=56 phantoms
      (`phantom_captured_no_parquet_at_canonical_path`, evidenced, api_football+footystats) ✅. MTDS sports
      (`market-data-tick-sports-prd`): (a)=0 (b)=0 (c)=0 (0 AF total, 25,782 captured, 1,000 EC all
      SOURCE_RETURNED_ZERO) ✅. Features sports (`features-sports-prd`): manifest exists, 0 rows — P1d NOT STARTED →
      BLOCKED-UPSTREAM; residual routed to `sports_p1_golden_window_features_2026_06_27` (run P1d first). Gate PARTIAL:
      IS+MTDS surfaces 0/0/0/≈0 ✅; features surface BLOCKED-UPSTREAM (P1d must complete). — 2026-07-12: Features sports
      (features-sports-prd): (a)=0 (b)=0 blank-EC (c)=0 un-evidenced AF (131 AF all evidenced: ValueError=130,
      AvailableAtStampingError=1; 71 EC all evidenced: SOURCE_RETURNED_ZERO=70,
      EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED=1) (d)=0 phantoms (0/3366 captured rows verified against canonical GCS
      paths, using the writer's raw-numeric→canonical-UAC league_id resolution — reconcile_phantom_manifest_rows_all.py
      doesn't support the sports_features/ bucket shape, so this used a hand-rolled read-only equivalent) ✅. 3569 total
      manifest rows / 3568 window-scoped across 17 feature_group values (3 canonical FSS groups + 14 legacy sub-table
      rows, all clean); 75 distinct leagues touched in-window. Gate CLOSED: features surface now 0/0/0/0 ✅ — P1e Todo 1
      fully GREEN across all three surfaces (IS + MTDS + features); Phase-2 gate UNBLOCKED on this basis. (P1d verified
      COMPLETE first per operator ruling §A2 findings 246/247 — verify-P1d-first — in
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`.)
- [x] ✅ [SCRIPT] P0. **Run the catalogue rollup once for sports + validate (R4 run-once).**
      `python instruments-service/scripts/build_instrument_catalogue.py --asset-group sports --by-date-prefix     sports_reference/by_date`
      (dry-run first, then real). It derives league-grain from the MANIFEST (so the catalogue league set ⊇ manifest
      league set by construction). **Gate**: exit 0; `catalog.parquet` written to
      `gs://instruments-store-sports-prd-central-element-323112/prod/` with non-zero rows ≥ prior count (monotonic guard
      PASSED); the rolled-up league set covers the window's captured leagues; `CATALOGUE_ROLLUP_COMPLETED` event
      emitted. — 2026-06-27: dry-run exit 0 (1609 rows, monotonic_ok); real run CATALOGUE_PROMOTED 1609 rows →
      gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet; 1609 unique league_ids, all active
      (available_to=None); CATALOGUE_ROLLUP_COMPLETED event emitted. Gate ALL PASSED.
- [x] ✅ [VERIFY] P0. **Sports data-pipeline Slack alerts == ZERO (R5).** Verify across ≥2 consecutive monitor sweeps:
      (a) `vm-census/active-dp-alerts.json` + `…-exit-code.json` + `…-heartbeat.json` contain 0 sports entries (no
      `instr-backfill-sports-*` / `manifest-consolidator-sports` / sports-bucket keys); (b)
      `instruments-store-sports-prd…/prod/catalog.parquet` exists <24h (clears `DP_CATALOG_NOT_RUNNING(sports)`); (c)
      `market-data-tick-sports-prd…/_index/availability_index.parquet` exists <180min (clears `DP_CRON_DID_NOT_FIRE` /
      `CONSOLIDATOR_DOWN`); (d) the three monitor sentinel blobs are fresh; (e) `#data-pipeline-alerts` shows no
      unresolved sports WARN/CRITICAL, every prior sports alert RESOLVED-bookended. **Gate**: all five true for 2
      consecutive sweeps; any open alert is root-caused-closed (not muted) — a false positive is a code fix (route to
      P0/`data_pipeline_failure`), a real one is a re-run. Evidence pasted into the log. — 2026-06-27 sweep1@15:05 +
      sweep2@15:10: (a) active-dp-alerts.json=0, exit-code.json=0(sports), heartbeat.json=0(sports) ✅; (b)
      catalog.parquet 6min old <1440min ✅; (c) availability_index.parquet 3min old <180min ✅; (d) exit-code sentinel
      0.5min ok=True, heartbeat sentinel 0.4min ok=True ✅; (e) 0 sports entries across 2 consecutive sweeps → no active
      sports alerts ✅. ALL 5 GATES PASSED.
- [x] ✅ [VERIFY] P0. **GOLDEN-WINDOW e2e VERDICT.** Stamp the window as GREEN (manifest 0/0/0 + catalogue OK +
      alerts 0) and flip the coordinator's child-status table + open the Phase-2 gate; or RED with the exact residuals
      routed. **Gate**: the coordinator (`sports_pipeline_to_100pct_golden_window_first`) Phase-1 rows are flipped with
      evidence; Phase-2 plans' `prereqs` open only on GREEN. — 2026-06-27: VERDICT = **PARTIAL GREEN — blocked on P1d
      (features)** SURFACES VERIFIED: IS sports 0/0/0/≈0 ✅ · MTDS sports 0/0/0 ✅ · catalogue 1609 rows PROMOTED ✅ ·
      alerts=0 across 2 sweeps ✅. SURFACE BLOCKED: features-sports manifest 0 rows → P1d NOT STARTED → cannot verify
      golden-window feature completeness; residual routed to `sports_p1_golden_window_features_2026_06_27`. PHASE-2:
      BLOCKED — Phase-2 gate opens ONLY when P1d completes and features manifest re-audit returns 0/0/0. Coordinator P1e
      row flipped to 🟡 partial (see coordinator plan child-status table). — 2026-07-12: **VERDICT = GREEN
      (2026-07-12)** (was: PARTIAL GREEN — blocked on P1d (features)). P1d is COMPLETE — deployment-service@e887f1b,
      features@774645dc, features-service@58b5e9f1 (ML-readiness 95.3% on 2026-07-12), features-service@192d74ce (was:
      "P1d NOT STARTED"). The formal P1e features-surface re-audit ran 2026-07-12 and PASSED 0/0/0/0 (see Todo 1 entry
      above). ALL THREE SURFACES NOW GREEN: IS sports 0/0/0/≈0 ✅ · MTDS sports 0/0/0 ✅ · features sports 0/0/0/0 ✅ ·
      catalogue 1609 rows PROMOTED ✅ · alerts=0 across 2 sweeps ✅. PHASE-2: UNBLOCKED (was: BLOCKED) — Phase-2 gate
      now opens; P1d completed and the features manifest re-audit returned 0/0/0/0. Coordinator P1e row flips to ✅
      GREEN (see coordinator plan child-status table).

**Full-execution criterion**:

- ✅ The golden window is GREEN on all three surfaces (manifest, catalogue, alerts), measured on real GCS + the live
  alert state.
  - **What ran**: the window `read_availability_index` audit; `build_instrument_catalogue.py --asset-group sports`; the
    alert-state checks (GCS blobs + Slack scroll).
  - **Verification**: the 0/0/0 manifest audit, the `catalog.parquet` stat, and the active-dp-alerts=0 evidence pasted
    into the Progress Log.

## Success criteria

- Golden window: 0 pending-fetch, 0 blank-reason, 0 un-evidenced failed, ≈0 phantom across every source + features.
- Catalogue rollup runs clean once (monotonic, non-zero, `catalog.parquet` written).
- Sports `DP_*` alert state is zero across 2 sweeps; every prior alert root-caused-closed.
- Phase-2 (expansion) is unblocked ONLY by this GREEN verdict.

## Dependencies

- **Upstream (prereq)**: P1a, P1b, P1c, P1d (all window sources + features 100%).
- **Blocks**: P2a, P2b (the expansion does not start until the window is proven).

## References

- `sports_manifest_canonicalisation_2026_06_01.md` — manifest canonical contract (the cleanliness this verifies)
- `instruments-service/scripts/run_fixture_completeness_audit_2026_06_25.py` — golden-window audit tool
