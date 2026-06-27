---
title: "Sports P1e — golden-window e2e GATE (manifest-clean + catalogue + alerts-zero)"
parent_epic: sports_master
priority: P0
status: active
assigned_vm: vm-sports
assigned_role: data_engineering
drift_direction: advance-code
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p1_golden_window_apifootball_2026_06_27
  - sports_p1_golden_window_reference_sources_2026_06_27
  - sports_p1_golden_window_mtds_odds_2026_06_27
  - sports_p1_golden_window_features_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_manifest_canonicalisation_2026_06_01.md
---

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

- `codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted_pending_fetch == 0`, phantom =
  captured-without-parquet
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator freshness (loud-fail-on-stale)
- `codex/05-infrastructure/data-pipeline-alerts.md` (+ `.registry.yaml`) — DP\_\* taxonomy + drive-to-zero
- `codex/05-infrastructure/deployment-observability.md` — active-dp-alerts blobs + RESOLVED bookend

## Todos

- [ ] [VERIFY] P0. **Manifest-clean on the window — ALL sources.** Run a single `read_availability_index` window-scoped
      audit (no whole-corpus walk) across api_football + the 5 reference sources + odds-api + features. Assert, for
      `date in [2025-09-01, 2025-11-30]`, 94 universe: (a) `expected_unattempted_pending_fetch == 0`; (b) 0
      `empty_confirmed` with blank/null `error_reason`; (c) 0 un-evidenced `attempted_failed`; (d) forward phantom
      dry-run ≈ 0 (P0 #5 unblocked). **Gate**: the audit prints 0/0/0/≈0 for every `(source, data_type)`; output pasted
      into the Progress Log. Any non-zero → file the residual back to the owning P1 plan (do NOT mask).
- [ ] [SCRIPT] P0. **Run the catalogue rollup once for sports + validate (R4 run-once).**
      `python instruments-service/scripts/build_instrument_catalogue.py --asset-group sports --by-date-prefix     sports_reference/by_date`
      (dry-run first, then real). It derives league-grain from the MANIFEST (so the catalogue league set ⊇ manifest
      league set by construction). **Gate**: exit 0; `catalog.parquet` written to
      `gs://instruments-store-sports-prd-central-element-323112/prod/` with non-zero rows ≥ prior count (monotonic guard
      PASSED); the rolled-up league set covers the window's captured leagues; `CATALOGUE_ROLLUP_COMPLETED` event
      emitted.
- [ ] [VERIFY] P0. **Sports data-pipeline Slack alerts == ZERO (R5).** Verify across ≥2 consecutive monitor sweeps: (a)
      `vm-census/active-dp-alerts.json` + `…-exit-code.json` + `…-heartbeat.json` contain 0 sports entries (no
      `instr-backfill-sports-*` / `manifest-consolidator-sports` / sports-bucket keys); (b)
      `instruments-store-sports-prd…/prod/catalog.parquet` exists <24h (clears `DP_CATALOG_NOT_RUNNING(sports)`); (c)
      `market-data-tick-sports-prd…/_index/availability_index.parquet` exists <180min (clears `DP_CRON_DID_NOT_FIRE` /
      `CONSOLIDATOR_DOWN`); (d) the three monitor sentinel blobs are fresh; (e) `#data-pipeline-alerts` shows no
      unresolved sports WARN/CRITICAL, every prior sports alert RESOLVED-bookended. **Gate**: all five true for 2
      consecutive sweeps; any open alert is root-caused-closed (not muted) — a false positive is a code fix (route to
      P0/`data_pipeline_failure`), a real one is a re-run. Evidence pasted into the log.
- [ ] [VERIFY] P0. **GOLDEN-WINDOW e2e VERDICT.** Stamp the window as GREEN (manifest 0/0/0 + catalogue OK + alerts 0)
      and flip the coordinator's child-status table + open the Phase-2 gate; or RED with the exact residuals routed.
      **Gate**: the coordinator (`sports_pipeline_to_100pct_golden_window_first`) Phase-1 rows are flipped with
      evidence; Phase-2 plans' `prereqs` open only on GREEN.

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
