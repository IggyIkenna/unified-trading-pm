# Active Plans Index

> **🟢 AUTO-GENERATED as of 2026-07-27** (operator decision,
> `plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5#26, resolving
> `issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md` Finding 2): this file was hand-maintained with no
> regenerator and had drifted to **226 stale entries** against the live plan set (dangling links into `archive/`, plans
> added without an INDEX bump, dozens of dated correction banners papering over the drift instead of fixing it).
> Replaced with `scripts/plans/regenerate_active_plan_index.py`, which reads every `plans/active/*.md` plan's own
> `asset_group:`/`summary:` frontmatter and regenerates the block below between the AUTO-INDEX markers — the same
> self-healing pattern `active_plan_inventory_dashboard_2026_07_24.md` already uses for checkbox-progress tracking, now
> wired into `scripts/plan-hygiene/run_hygiene_sweep.sh` alongside it. **Never hand-edit between the markers** — re-run
> the script instead; edits there are overwritten on the next regen. The prior hand-maintained content (307 lines,
> spanning 2026-03 through 2026-07-25) is preserved in this file's git history if historical context is ever needed — it
> is not reproduced here.

---

<!-- AUTO-INDEX-START -->

_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. 253 plans across 10 domains. A plan tagged with
multiple `asset_group:` values appears under each. Grep this block for a domain keyword before scanning `plans/active/`
by hand._

### cefi (42)

- [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) — Autonomous session (/autonomous,
  operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset groups that haven't had it yet —
  cefi, defi, tradfi, prediction — each of which already carries its own…
- [`aster_and_cefi_rolling_adv_feature_2026_07_21`](./aster_and_cefi_rolling_adv_feature_2026_07_21.md) — Strategy code
  needs a rolling-N-day average-daily-volume (ADV) signal per CeFi instrument, both to cap position size as a % of ADV
  and to gate an instrument as "not yet tradeable" until it has a minimum history of real volume. Surfaced…
- [`candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27`](./candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for candle_canonical_path_migration_execution_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`canonical_id_builder_retrofit_checklist_2026_07_08`](./canonical_id_builder_retrofit_checklist_2026_07_08.md) — The
  operator-decided one-builder architecture (instrument_id_format_canonicalization_2026_07_08.md — "one builder for
  everything... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by…
- [`canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27`](./canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for canonical_id_builder_retrofit_checklist_2026_07_08.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`cefi_4surface_migration_execution_log_2026_07_24`](./cefi_4surface_migration_execution_log_2026_07_24.md) — Verbatim
  extraction of the Progress Log from cefi_consolidated_closeout_2026_07_18.md (line-cap remediation, 2026-07-24) — the
  day-by-day narrative + PRE-COMPACT checkpoints + DELTA updates + deferred-work tables tracking the CeFi…
- [`cefi_consolidated_closeout_2026_07_18`](./cefi_consolidated_closeout_2026_07_18.md) — Single coordination plan that
  references (does NOT duplicate) every still-open cefi plan/issue so they can be closed off together. Authored
  2026-07-18 from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification; restructured…
- [`cefi_consolidated_closeout_aggregated_sources_2026_07_24`](./cefi_consolidated_closeout_aggregated_sources_2026_07_24.md)
  — The "Aggregated source docs" discoverability index extracted verbatim from
  cefi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap trim (2nd pass -- the umbrella:true exemption was
  removed same-day, flat 1000L hard cap now applies…
- [`cefi_consolidated_native_ao_extract_2026_07_25`](./cefi_consolidated_native_ao_extract_2026_07_25.md) — Fresh
  AO-eligibility triage of cefi_consolidated_closeout_2026_07_18.md's OWN 32 native `- [ ]` todos (not the satellite-doc
  digest, already covered by cefi_satellite_ao_dispatch_batch1_2026_07_25.md). Classified every open native todo…
- [`cefi_consolidated_native_ao_extract_2026_07_25_finalize`](./cefi_consolidated_native_ao_extract_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for cefi_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 12 of that plan's todos are done. Mirrors the batch1_finalize pattern, plus one extra:
  because the…
- [`cefi_deribit_binance_futures_bundle_verification_2026_06_20`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)
  — Verify DERIBIT options/futures and BINANCE-FUTURES perp bundle backfill coverage and triage phantom-manifest
  residuals.
- [`cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for cefi_deribit_binance_futures_bundle_verification_2026_06_20.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28`](./cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md)
  — Consolidates THREE overlapping, previously-separately-dispatched todos in data_completion_cefi_2026_07_15.md (the
  "E4 remaining work = ORPHAN SWEEP + gap-fill" todo / data_completion_cefi-015, its "Orphan sweep + bucket-state
  evidence"…
- [`cefi_migration_cutover_and_track8_completion_finalize_2026_07_25`](./cefi_migration_cutover_and_track8_completion_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md —
  machine-held via depends_on + gate_on_depends: true until all 5 of that plan's sequential todos are done. Reconciles
  the parent…
- [`cefi_misc_audits_and_hygiene_2026_07_25`](./cefi_misc_audits_and_hygiene_2026_07_25.md) — 3 independent, ungated
  todos on different files/repos forked from cefi_consolidated_closeout_2026_07_18.md's "Operator dispositions" section
  (2026-07-25 split): the `[OPERATOR]`-gated UAC per-venue seed fallback removal decision, a bounded…
- [`cefi_misc_audits_and_hygiene_finalize_2026_07_25`](./cefi_misc_audits_and_hygiene_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for cefi_misc_audits_and_hygiene_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 3 of that plan's todos are done. Reconciles the parent
  (cefi_consolidated_closeout_2026_07_18.md) checkboxes for…
- [`cefi_ml_directional_continuous_live_2026_06_20`](./cefi_ml_directional_continuous_live_2026_06_20.md) — "Ship the
  live CeFi ML_DIRECTIONAL_CONTINUOUS archetype across OKX, Binance, and Bybit: live tick to live ML inference to live
  strategy to live execution."
- [`cefi_satellite_ao_dispatch_batch1_2026_07_25`](./cefi_satellite_ao_dispatch_batch1_2026_07_25.md) — First
  AO-dispatch batch for cefi. Extracted from a 29-doc AO-eligibility triage over every cefi satellite doc not covered by
  cefi_consolidated_closeout_2026_07_18.md / cefi_consolidated_closeout_aggregated_sources_2026_07_24.md. The triage…
- [`cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25`](./cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for cefi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 33 of that plan's todos are done. Mirrors the tradfi batch1_finalize / prediction
  batch1_finalize pattern…
- [`cefi_satellite_ao_dispatch_batch3_2026_07_26`](./cefi_satellite_ao_dispatch_batch3_2026_07_26.md) — Third
  AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-07-26 (autonomous mode) immediately
  after the cefi `/plan-reconcile` pass. Phase 0-2 re-derived the covering-plan set (19 plans + the epic) and…
- [`cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26`](./cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md)
  **[draft]** — Gated closeout for cefi_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's todos are done. Mirrors the batch1/batch2 finalize pattern: reconcile
  each source doc's…
- [`cefi_track2_coverage_backfill_checkpoints_2026_07_25`](./cefi_track2_coverage_backfill_checkpoints_2026_07_25.md) —
  Resumes the CeFi Tardis COVERAGE backfill (reversing the archived "honest-done 50.79%" verdict — the throughput
  ceiling was a ~350x code bug, now fixed and measured live) and brackets it with the MID/POST…
- [`cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25`](./cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for cefi_track2_coverage_backfill_checkpoints_2026_07_25.md — machine-held via
  depends_on + gate_on_depends: true until all 5 of that plan's sequential todos are done. Reconciles the parent…
- [`cefi_track7_candle_namespace_residual_2026_07_25`](./cefi_track7_candle_namespace_residual_2026_07_25.md) — Track
  7's terminal, `[OPERATOR]`-tagged step only — deleting the 149 stale legacy per-leg `processed_candles/` objects
  (BYBIT futures_chain + DERIBIT options_chain bundle-collision residual). Forked from…
- [`cefi_track7_candle_namespace_residual_finalize_2026_07_25`](./cefi_track7_candle_namespace_residual_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for cefi_track7_candle_namespace_residual_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until that plan's single delete todo is done. Reconciles the parent
  (cefi_consolidated_closeout_2026_07_18.md)…
- [`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20`](./cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md)
  — Add canonical universe coverage for crypto-venue single-stock perpetuals and tokenized stocks (Binance/OKX/Bybit),
  enabling equity basis/dispersion arb cross-venue.
- [`data_completion_cefi_2026_07_15`](./data_completion_cefi_2026_07_15.md) — CeFi slice of the data-completion-to-100%
  program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on 2026-07-15 per operator ruling (plan-reconcile
  §8) when M-1 breached the absolute 5000-line ceiling. Carries the cefi scope…
- [`data_completion_cefi_2026_07_15_finalize_2026_07_27`](./data_completion_cefi_2026_07_15_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for data_completion_cefi_2026_07_15.md -- machine-held via depends_on + gate_on_depends:
  true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once its AO-dispatched
  todos ship…
- [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md) — Extend the
  shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle derivation) and
  features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers + two Claude…
- [`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27`](./data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for data_pipeline_check_mdps_features_2026_07_20.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`defi_pipeline_e2e_and_coverage_validation_2026_06_20`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20.md) —
  End-to-end validation of the DeFi pipeline (features-onchain → strategy → execution) before the live cutover gate: run
  the full batch, verify each of the 11 registered DEFI handlers produces real (non-NaN) GCS coverage, confirm the
  Stage-4…
- [`defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for defi_pipeline_e2e_and_coverage_validation_2026_06_20.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`instruments_cefi_g1_g5_gate_execution_2026_07_24`](./instruments_cefi_g1_g5_gate_execution_2026_07_24.md) — Split
  out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split, operator-
  approved). Owns cefi's gated G1→G5 rebuild — instrument-definition correctness (G1.1-G1.4 catalogue false-delisting /…
- [`instruments_satellite_ao_dispatch_batch1_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_2026_07_27.md) —
  First /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified
  honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md as mixed across 14 open items: 8 are genuinely
  operator/judgment-gated (stay NA),…
- [`instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md)
  — Gated closeout for instruments_satellite_ao_dispatch_batch1_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 5 batch todos is done, reconciles the
  corresponding checkbox…
- [`is_daily_enum_capture_heal_2026_07_07`](./is_daily_enum_capture_heal_2026_07_07.md) — is-daily-enum-prediction (dead
  07-01→) and is-daily-enum-sports (dead 06-28→, longer, previously undetected) both still exit(1) in the cloud even
  though the deployed image now carries the UTL write-side dtype coercion — a SECOND, different…
- [`is_daily_enum_capture_heal_2026_07_07_finalize_2026_07_27`](./is_daily_enum_capture_heal_2026_07_07_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for is_daily_enum_capture_heal_2026_07_07.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todos ship…
- [`mdps_candle_manifest_population_disconnect_2026_07_25`](./mdps_candle_manifest_population_disconnect_2026_07_25.md)
  — MDPS-owned root-cause + fix for the candle object↔manifest disconnect — root-cause first (three undistinguished
  hypotheses), because a fresh 2026-07-25 re-measurement shows the manifest is STILL only 6 degenerate CEFI rows, 4 days
  AFTER…
- [`mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27`](./mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mdps_candle_manifest_population_disconnect_2026_07_25.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`prediction_capture_incident_remediation_2026_07_06`](./prediction_capture_incident_remediation_2026_07_06.md) —
  "Actionable remediation for the 2026-07-01→07-06 prediction-universe-capture outage (diagnosis + root-cause evidence:
  issue doc prediction_universe_capture_dead_since_07_01_2026_07_06). Two workstreams: (A) harden the capture path —
  UTL…
- [`prediction_cross_venue_arb_and_coverage_2026_07_24`](./prediction_cross_venue_arb_and_coverage_2026_07_24.md) — The
  cross-venue Kalshi↔Polymarket arb detector (matcher, dispersion features, strategy engine, GCS arb-store, live
  dispatch), cqg canonicalization, the honest-coverage P0 correctness chain (43a-43d), and historical backfill/manifest
  work…
- [`prediction_live_clob_depth_capture_2026_07_24`](./prediction_live_clob_depth_capture_2026_07_24.md) — The live/batch
  data-capture pipeline for PREDICTION Kalshi + Polymarket YES/NO markets — WS connectors, transport/ sink correctness,
  message-shape fixes, live producer VM operations, source/pipeline-mode registration; split out of…

### defi (43)

- [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) — Autonomous session (/autonomous,
  operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset groups that haven't had it yet —
  cefi, defi, tradfi, prediction — each of which already carries its own…
- [`candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27`](./candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for candle_canonical_path_migration_execution_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`canonical_id_builder_retrofit_checklist_2026_07_08`](./canonical_id_builder_retrofit_checklist_2026_07_08.md) — The
  operator-decided one-builder architecture (instrument_id_format_canonicalization_2026_07_08.md — "one builder for
  everything... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by…
- [`canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27`](./canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for canonical_id_builder_retrofit_checklist_2026_07_08.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`cefi_deribit_binance_futures_bundle_verification_2026_06_20`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20.md)
  — Verify DERIBIT options/futures and BINANCE-FUTURES perp bundle backfill coverage and triage phantom-manifest
  residuals.
- [`cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27`](./cefi_deribit_binance_futures_bundle_verification_2026_06_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for cefi_deribit_binance_futures_bundle_verification_2026_06_20.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`cefi_ml_directional_continuous_live_2026_06_20`](./cefi_ml_directional_continuous_live_2026_06_20.md) — "Ship the
  live CeFi ML_DIRECTIONAL_CONTINUOUS archetype across OKX, Binance, and Bybit: live tick to live ML inference to live
  strategy to live execution."
- [`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20`](./cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md)
  — Add canonical universe coverage for crypto-venue single-stock perpetuals and tokenized stocks (Binance/OKX/Bybit),
  enabling equity basis/dispersion arb cross-venue.
- [`data_completion_defi_2026_07_15`](./data_completion_defi_2026_07_15.md) — DeFi slice of the data-completion-to-100%
  program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on 2026-07-15 per operator ruling (plan-reconcile
  §8) when M-1 breached the absolute 5000-line ceiling. Carries the defi scope…
- [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md) — Extend the
  shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle derivation) and
  features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers + two Claude…
- [`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27`](./data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for data_pipeline_check_mdps_features_2026_07_20.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`defi_consolidated_closeout_2026_07_18`](./defi_consolidated_closeout_2026_07_18.md) — Single coordination plan that
  AGGREGATES (references, does NOT duplicate) every open defi + defi-touching IS/MTDS plan/issue into ONE ordered pass,
  mirroring cefi_consolidated_closeout_2026_07_18.md /…
- [`defi_consolidated_native_ao_extract_2026_07_25`](./defi_consolidated_native_ao_extract_2026_07_25.md) — Fresh
  AO-eligibility triage of defi_consolidated_closeout_2026_07_18.md's OWN native `- [ ]` todos (not its satellite source
  docs — those already got the defi_satellite_ao_dispatch_batch1_2026_07_25.md treatment). Of 19 open native todo…
- [`defi_consolidated_native_ao_extract_2026_07_25_finalize`](./defi_consolidated_native_ao_extract_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for defi_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 4 of that plan's todos are done. Reconciles each shipped todo's evidence back into…
- [`defi_dedicated_bucket_shared_migration_2026_07_13`](./defi_dedicated_bucket_shared_migration_2026_07_13.md) — The 3
  remaining kind-dedicated DeFi buckets (dex-pools-prd, lst-rates-prd, perp-funding-prd) were kept out of the earlier
  gcs_bucket_estate_cleanup consolidation specifically because they have real, live readers…
- [`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25`](./defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md) —
  Operator decision 2026-07-25 -- delete the bad unattributed TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state data, fix
  the subgraph-query bug that caused it (see issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md),
  then…
- [`defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25`](./defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md)
  — Gated closeout for defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's todos are done, so this never dispatches early. Reconciles the
  originating bug report…
- [`defi_expected_unattempted_seeder_design_2026_07_26`](./defi_expected_unattempted_seeder_design_2026_07_26.md) —
  Design track for the real DeFi expected_unattempted seeder ruled for on BLK-7c950d06 (Option A) — DeFi currently has
  NO expected_unattempted signal at all (MTDS orchestrator excludes every defi venue from the sentinel fan-out;…
- [`defi_expected_unattempted_seeder_design_2026_07_26_finalize_2026_07_28`](./defi_expected_unattempted_seeder_design_2026_07_26_finalize_2026_07_28.md)
  **[draft]** — Gated closeout for defi_expected_unattempted_seeder_design_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`defi_pipeline_e2e_and_coverage_validation_2026_06_20`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20.md) —
  End-to-end validation of the DeFi pipeline (features-onchain → strategy → execution) before the live cutover gate: run
  the full batch, verify each of the 11 registered DEFI handlers produces real (non-NaN) GCS coverage, confirm the
  Stage-4…
- [`defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27`](./defi_pipeline_e2e_and_coverage_validation_2026_06_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for defi_pipeline_e2e_and_coverage_validation_2026_06_20.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`defi_satellite_ao_dispatch_batch1_2026_07_25`](./defi_satellite_ao_dispatch_batch1_2026_07_25.md) — First
  AO-dispatch batch for defi (the last of 5 asset groups getting the /ag-closeout-audit skill's Phase 3 treatment this
  session, after sports/tradfi/prediction/cefi). Extracted from a 40-doc AO-eligibility triage over every defi…
- [`defi_satellite_ao_dispatch_batch1_finalize_2026_07_25`](./defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for defi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 54 of that plan's todos are done (53 original + todo 54, appended 2026-07-25 once
  operator-decision entry #3…
- [`defi_satellite_ao_dispatch_batch2_2026_07_26`](./defi_satellite_ao_dispatch_batch2_2026_07_26.md) — Second
  AO-dispatch batch for defi, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 56 defi AG-primary docs not already covered by the consolidated closeout,…
- [`defi_satellite_ao_dispatch_batch2_2026_07_26_finalize`](./defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md)
  — Gated closeout for defi_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 23 of that plan's todos are done. Mirrors batch1-finalize's pattern (reconcile each distinct source
  doc's…
- [`defi_satellite_ao_dispatch_batch3_2026_07_26`](./defi_satellite_ao_dispatch_batch3_2026_07_26.md) — Third
  AO-dispatch batch for defi, produced by the `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 59 defi AG-primary docs, run AFTER batch2 landed (2026-07-26). With batch1,…
- [`defi_satellite_ao_dispatch_batch3_2026_07_26_finalize`](./defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md)
  **[draft]** — Gated closeout for defi_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 12 of that plan's todos are done. Mirrors batch1/batch2-finalize's pattern (reconcile
  each distinct source…
- [`defi_satellite_ao_dispatch_batch4_2026_07_26_finalize`](./defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md)
  **[draft]** — Gated closeout for defi_satellite_ao_dispatch_batch4_2026_07_26.md — machine-held via depends_on plus
  gate_on_depends: true until both of that plan's todos are done. Small by construction, mirroring the batch2-finalize
  and batch3-finalize…
- [`defi_satellite_ao_dispatch_batch5_2026_07_27`](./defi_satellite_ao_dispatch_batch5_2026_07_27.md) **[draft]** —
  Fifth AO-dispatch batch for defi, produced by the scheduled `ag_closeout_auditor` role running the
  `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3 (conflict-check + draft) triage over all 65 defi
  AG-primary docs, run one…
- [`defi_satellite_ao_dispatch_batch5_2026_07_27_finalize`](./defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md)
  **[draft]** — Gated closeout for defi_satellite_ao_dispatch_batch5_2026_07_27.md — machine-held via depends_on +
  gate_on_depends: true until all 7 of that plan's todos are done. Mirrors batch1-4-finalize's pattern (reconcile each
  distinct source doc's…
- [`defi_strategy_pnl_axis_index_2026_07_24`](./defi_strategy_pnl_axis_index_2026_07_24.md) — Entry-point index for the
  DeFi strategy/PnL/backtest-engine axis (`strategy-service`), extracted from defi_consolidated_closeout_2026_07_18.md's
  "Strategy/PnL/backtest-side DeFi tracking" section (folded in there 2026-07-23, "no orphans")…
- [`defi_track01_per_instrument_and_canon_id_2026_07_24`](./defi_track01_per_instrument_and_canon_id_2026_07_24.md) —
  Extracted 2026-07-24 from defi_consolidated_closeout_2026_07_18.md's "Per-instrument re-architecture" + "Track 1 —
  CANON" sections (line-cap remediation follow-through) so the parent could come back under the 1000-line hard cap.
  Carries…
- [`defi_track5_coverage_mvp_backfill_2026_07_24`](./defi_track5_coverage_mvp_backfill_2026_07_24.md) — Forked verbatim
  from defi_consolidated_closeout_2026_07_18.md's "Track 5 — COVERAGE" section (2026-07-24, per task_template.md's
  "partial parallelism is NOT expressible inside one plan — SPLIT" rule and an operator ruling during the 5-AG…
- [`instruments_satellite_ao_dispatch_batch1_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_2026_07_27.md) —
  First /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified
  honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md as mixed across 14 open items: 8 are genuinely
  operator/judgment-gated (stay NA),…
- [`instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md)
  — Gated closeout for instruments_satellite_ao_dispatch_batch1_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 5 batch todos is done, reconciles the
  corresponding checkbox…
- [`lst_rate_honest_coverage_2026_07_21`](./lst_rate_honest_coverage_2026_07_21.md) — Operator-directed (2026-07-21)
  build to bring the four LST exchange-rate surfaces to HONEST COVERAGE end-to-end so the DeFi interest PnL can sit on
  real data. #1 CEX spot = a Tardis backfill (denominator already complete — adding pairs is…
- [`market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24`](./market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md)
  — MTDS `liquidations_handler.py`'s lending `instrument_type` writer bug is already fixed going forward
  (`mtds@fec20de2` — manifest stamp + disk write both derive from the same `resolve_lending_instrument_type()` call),
  but existing…
- [`mdps_candle_manifest_population_disconnect_2026_07_25`](./mdps_candle_manifest_population_disconnect_2026_07_25.md)
  — MDPS-owned root-cause + fix for the candle object↔manifest disconnect — root-cause first (three undistinguished
  hypotheses), because a fresh 2026-07-25 re-measurement shows the manifest is STILL only 6 degenerate CEFI rows, 4 days
  AFTER…
- [`mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27`](./mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mdps_candle_manifest_population_disconnect_2026_07_25.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`mtds_available_at_cross_asset_backfill_2026_07_13`](./mtds_available_at_cross_asset_backfill_2026_07_13.md) —
  Backfill the historical available_at="" backlog on CAPTURED market-data-tick manifest rows, now that
  unified-trading-library@9c9cdc50 fixed record_captured()/record_captured_from_counts() to actually persist the value.
  Phases…
- [`mtds_available_at_cross_asset_backfill_2026_07_13_finalize_2026_07_27`](./mtds_available_at_cross_asset_backfill_2026_07_13_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mtds_available_at_cross_asset_backfill_2026_07_13.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`mvp_backfill_defi_onchain_v10_2026_06_27`](./mvp_backfill_defi_onchain_v10_2026_06_27.md) — Backfill all DeFi
  on-chain data_types (dex_pool_swaps/state, lending_indices, lst_rates, perp_funding, oracle_prices) for the v10 DeFi
  MVP scope on SPOT VMs, respecting per-protocol genesis.
- [`mvp_backfill_defi_onchain_v10_2026_06_27_finalize_2026_07_27`](./mvp_backfill_defi_onchain_v10_2026_06_27_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mvp_backfill_defi_onchain_v10_2026_06_27.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todo…

### tradfi (31)

- [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) — Autonomous session (/autonomous,
  operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset groups that haven't had it yet —
  cefi, defi, tradfi, prediction — each of which already carries its own…
- [`candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27`](./candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for candle_canonical_path_migration_execution_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08`](./canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md)
  — TradFi multi-leg spreads (calendar spreads, butterflies, etc.) on CBOE/VX currently land in the catalog as flat,
  undecomposed strings using the wrong instrument_type (`SPOT_PAIR`, reused from equity spot) and a whitespace-padded
  dash as an…
- [`data_completion_tradfi_2026_07_15`](./data_completion_tradfi_2026_07_15.md) — TradFi slice of the
  data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on 2026-07-15 per
  operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the tradfi…
- [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md) — Extend the
  shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle derivation) and
  features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers + two Claude…
- [`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27`](./data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for data_pipeline_check_mdps_features_2026_07_20.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`instruments_satellite_ao_dispatch_batch1_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_2026_07_27.md) —
  First /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified
  honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md as mixed across 14 open items: 8 are genuinely
  operator/judgment-gated (stay NA),…
- [`instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md)
  — Gated closeout for instruments_satellite_ao_dispatch_batch1_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 5 batch todos is done, reconciles the
  corresponding checkbox…
- [`instruments_tradfi_g1_g5_gate_execution_2026_07_24`](./instruments_tradfi_g1_g5_gate_execution_2026_07_24.md) —
  Split out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split,
  operator- approved). Owns tradfi's gated G1→G5 rebuild — billable-venue guard, calendar/session fail-closed, CME/ES
  ohlcv + Yahoo…
- [`mdps_candle_manifest_population_disconnect_2026_07_25`](./mdps_candle_manifest_population_disconnect_2026_07_25.md)
  — MDPS-owned root-cause + fix for the candle object↔manifest disconnect — root-cause first (three undistinguished
  hypotheses), because a fresh 2026-07-25 re-measurement shows the manifest is STILL only 6 degenerate CEFI rows, 4 days
  AFTER…
- [`mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27`](./mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mdps_candle_manifest_population_disconnect_2026_07_25.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`mtds_available_at_cross_asset_backfill_2026_07_13`](./mtds_available_at_cross_asset_backfill_2026_07_13.md) —
  Backfill the historical available_at="" backlog on CAPTURED market-data-tick manifest rows, now that
  unified-trading-library@9c9cdc50 fixed record_captured()/record_captured_from_counts() to actually persist the value.
  Phases…
- [`mtds_available_at_cross_asset_backfill_2026_07_13_finalize_2026_07_27`](./mtds_available_at_cross_asset_backfill_2026_07_13_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mtds_available_at_cross_asset_backfill_2026_07_13.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`tradfi_backfill_throughput_followups_2026_07_24`](./tradfi_backfill_throughput_followups_2026_07_24.md) — Forked
  from tradfi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap remediation split. Carries Phase A3
  (download/backfill throughput — DNS-starvation executor, T+1 forward-fill job, OOM/SIGKILL hardening, phantom-row
  retirement)…
- [`tradfi_consolidated_closeout_2026_07_18`](./tradfi_consolidated_closeout_2026_07_18.md) — Coordination index
  (umbrella) that AGGREGATES (references, does not duplicate) every open tradfi + tradfi-touching IS/MTDS plan/issue
  into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md. **2026-07-24 line-cap…
- [`tradfi_consolidated_native_ao_extract_2026_07_25`](./tradfi_consolidated_native_ao_extract_2026_07_25.md) — Fresh
  AO-eligibility triage of `tradfi_consolidated_closeout_2026_07_18.md`'s own 13 open native `- [ ]` todos (deliberately
  excluded from this session's earlier `tradfi_satellite_ao_dispatch_batch1/2_2026_07_25.md` extractions, which…
- [`tradfi_consolidated_native_ao_extract_2026_07_25_finalize`](./tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for `tradfi_consolidated_native_ao_extract_2026_07_25.md` — machine-held via
  `depends_on` + `gate_on_depends: true` until all 10 of that plan's todos are done. Unlike the batch1/batch2 satellite
  extractions (whose "source…
- [`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24`](./tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md) —
  Small follow-up forked out of tradfi_v9_stage1_finish_2026_07_06.md (now archived, all its other tasks closed) during
  the 2026-07-24 plan-hygiene line-cap remediation. Carries the single remaining legacy-twin bucket delete todo — after
  the…
- [`tradfi_manifest_content_recovery_completion_2026_07_24`](./tradfi_manifest_content_recovery_completion_2026_07_24.md)
  — Forked from tradfi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap remediation split. Carries Phase A1's
  writer re-drift-prevention residual + Phase B (migrate the catalogue/manifest/GCS-filename/tick-content surfaces to…
- [`tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27`](./tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for tradfi_manifest_content_recovery_completion_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`tradfi_multisource_backfill_2026_06_22`](./tradfi_multisource_backfill_2026_06_22.md) — Extend the TradFi OHLCV
  backfill to cover FX via Yahoo Finance, CBOE cash-index (no provider path), and ICE (source-ask).
- [`tradfi_phase_d_terminal_gate_2026_07_24`](./tradfi_phase_d_terminal_gate_2026_07_24.md) — Forked from
  tradfi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap remediation split. Carries Phase D — the parent's
  terminal completion gate — post-migration re-smoke-test of every tradfi (venue, data_type) shard via the…
- [`tradfi_registry_coverage_and_ao_readiness_2026_07_25`](./tradfi_registry_coverage_and_ao_readiness_2026_07_25.md)
  **[draft]** — Forked from `tradfi_consolidated_closeout_2026_07_18.md`'s 2026-07-25 second-tier line-cap trim (mirrors
  the 2026-07-24 3-way split pattern — see that plan's Split notice). Carries Phase A2 (adapter/registry correctness —
  CME capability…
- [`tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize`](./tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md)
  **[draft]** — Housekeeping companion for `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` — gated via
  `depends_on` + `gate_on_depends: true` on that plan's own todos (Phase A2 + the still-open Phase C residue) being
  done, mirroring the…
- [`tradfi_satellite_ao_dispatch_batch1_2026_07_25`](./tradfi_satellite_ao_dispatch_batch1_2026_07_25.md) — First
  AO-dispatch batch for tradfi (tradfi has never had one before, unlike sports). Extracted from the 2026-07-25
  orphan-audit's 21 genuinely-orphaned tradfi satellite docs (of 23 audited; the 91% orphan rate reflects that…
- [`tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25`](./tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for tradfi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's todos are done. Mirrors the sports batch2_finalize/ batch3_finalize
  pattern (reconcile…
- [`tradfi_satellite_ao_dispatch_batch2_2026_07_25`](./tradfi_satellite_ao_dispatch_batch2_2026_07_25.md) — Second
  AO-dispatch batch for tradfi, produced by the `/ag-closeout-audit` skill's batchN re-check methodology (never a fresh
  Workflow triage) against `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s own Deferred section — 33…
- [`tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25`](./tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for tradfi_satellite_ao_dispatch_batch2_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 11 of that plan's todos are done. Mirrors the batch1_finalize pattern (reconcile each
  of the 11 distinct…
- [`tradfi_satellite_ao_dispatch_batch4_2026_07_26`](./tradfi_satellite_ao_dispatch_batch4_2026_07_26.md) — Fourth
  AO-dispatch batch for tradfi, produced by a second `/ag-closeout-audit tradfi` pass on 2026-07-26 (autonomous mode),
  run AFTER batch3 was activated and 5 of its 9 todos had already executed. Re-audited all 27 tradfi-primary…
- [`tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize`](./tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md)
  **[draft]** — Gated closeout for tradfi_satellite_ao_dispatch_batch4_2026_07_26.md — machine-held via depends_on plus
  gate_on_depends: true until all 8 of that plan's todos are done. Mirrors the batch1/batch2/batch3-finalize pattern:
  reconcile each…
- [`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20`](./tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md)
  — Run ES feature calculations and ML training smoke test, and complete the full S&P 500 backtest for price-arb and
  prediction strategies.

### sports (40)

- [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) — Autonomous session (/autonomous,
  operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset groups that haven't had it yet —
  cefi, defi, tradfi, prediction — each of which already carries its own…
- [`candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27`](./candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for candle_canonical_path_migration_execution_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`canonical_id_builder_retrofit_checklist_2026_07_08`](./canonical_id_builder_retrofit_checklist_2026_07_08.md) — The
  operator-decided one-builder architecture (instrument_id_format_canonicalization_2026_07_08.md — "one builder for
  everything... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by…
- [`canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27`](./canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for canonical_id_builder_retrofit_checklist_2026_07_08.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`data_completion_sports_2026_07_24`](./data_completion_sports_2026_07_24.md) — Sports slice of the
  data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on 2026-07-24 per the
  plan line-cap remediation (plans/active/issues/plan_line_cap_remediation_2026_07_23.md,…
- [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md) — Extend the
  shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle derivation) and
  features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers + two Claude…
- [`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27`](./data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for data_pipeline_check_mdps_features_2026_07_20.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`predictions_ml_walk_forward_and_arb_2026_06_20`](./predictions_ml_walk_forward_and_arb_2026_06_20.md) — Run Model 2A
  walk-forward validation (AUC gate) and ship the FSS arb_calculator — the predictions-ML half of the
  sports_predictions_e2e milestone.
- [`sports_arb_decay_window_and_alpha_gate_design_2026_07_21`](./sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)
  — Brand-new feature work with zero prior spec (confirmed: grepped decay_window/arb_decay/alpha_gate/paper_trade_alpha
  across strategy-service + execution-service + codex, only unchecked todos in archived plans exist). This plan defines
  WHAT…
- [`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24`](./sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md)
  — Curate the sports canonical trading universe (94 leagues) and expand the API-Football reference universe to ~300
  leagues to eliminate out-of-universe over-capture in instruments-service.
- [`sports_catalog_league_grain_only_scope_2026_07_08`](./sports_catalog_league_grain_only_scope_2026_07_08.md) —
  `prod/catalog.parquet` for sports has 116 rows, all `venue=""` and `instrument_type="league"` — confirmed via a real
  GCS read (2026-07-08). This is NOT a silently-broken write path (unlike the earlier weather stale-GCS-path bug):…
- [`sports_closeout_exchange_fixed_odds_fork_2026_07_25`](./sports_closeout_exchange_fixed_odds_fork_2026_07_25.md) —
  Self-contained extraction of sports_consolidated_closeout_2026_07_19.md's Track C "EXCHANGE_ODDS vs FIXED_ODDS fork"
  block (line-cap split, 2026-07-25) — the full UAC-contract-fork + GCS-migration sequence splitting the sports `odds`…
- [`sports_closeout_exchange_fixed_odds_fork_2026_07_25_finalize`](./sports_closeout_exchange_fixed_odds_fork_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for sports_closeout_exchange_fixed_odds_fork_2026_07_25.md — machine-held via
  depends_on + gate_on_depends: true until all 11 of that plan's todos are done. Reconciles evidence back into…
- [`sports_closeout_track_s2_foldin_2026_07_25`](./sports_closeout_track_s2_foldin_2026_07_25.md) — Extraction of
  sports_consolidated_closeout_2026_07_19.md's remaining Track S2 "FOLD-IN ABSORPTION" items (line-cap split,
  2026-07-25) — real data/infra engineering work extracted 2026-07-23 from 3 now-archived plans…
- [`sports_closeout_track_s2_foldin_2026_07_25_finalize`](./sports_closeout_track_s2_foldin_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for sports_closeout_track_s2_foldin_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all of that plan's dispatchable todos are done. Reconciles evidence back into…
- [`sports_closeout_track_x_hygiene_2026_07_25`](./sports_closeout_track_x_hygiene_2026_07_25.md) — Extraction of
  sports_consolidated_closeout_2026_07_19.md's remaining Track X plan/doc-hygiene items (line-cap split, 2026-07-25) —
  the parent's own orphan-satellite-plan reconciliation todos and a peripheral-bucket data-correctness item…
- [`sports_closeout_track_x_hygiene_2026_07_25_finalize`](./sports_closeout_track_x_hygiene_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for sports_closeout_track_x_hygiene_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 4 of that plan's todos are done. Reconciles evidence back into
  sports_consolidated_closeout_2026_07_19.md's…
- [`sports_consolidated_audit_2026_07_19`](./sports_consolidated_audit_2026_07_19.md) — A measured, read-only audit of
  the full sports data path (instruments-service reference, market-tick-data-service odds,
  market-data-processing-service bucketing, features-service) plus SSOT/codex alignment and plan reconciliation.
  Produced…
- [`sports_consolidated_closeout_2026_07_19`](./sports_consolidated_closeout_2026_07_19.md) — The single actionable plan
  that takes the sports asset_group all the way to ML-ready: canonical SSOT + naming, right buckets, codex migration,
  no-regression guards, honest-coverage backfill across instruments-service /…
- [`sports_consolidated_native_ao_extract_2026_07_25`](./sports_consolidated_native_ao_extract_2026_07_25.md) — A fresh
  AO-eligibility triage of sports_consolidated_closeout_2026_07_19.md's OWN native `- [ ]` todos (never before extracted
  — every prior sports satellite batch drew from OTHER orphaned docs, deliberately not this doc's own checkboxes).…
- [`sports_consolidated_native_ao_extract_2026_07_25_finalize`](./sports_consolidated_native_ao_extract_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for sports_consolidated_native_ao_extract_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 26 of that plan's todos are done. Reconciles each completed todo's evidence back into…
- [`sports_group_c_execution_backtest_harness_2026_07_21`](./sports_group_c_execution_backtest_harness_2026_07_21.md) —
  Scopes a `run_sports_backtest` CLI in execution-service, mirroring the 3 existing domain runners
  (run_cefi_backtest/run_tradfi_backtest/run_defi_backtest), so sports/predictions gets a real Group-C execution-alpha
  harness. Decided…
- [`sports_legacy_fixtures_path_migration_2026_07_24`](./sports_legacy_fixtures_path_migration_2026_07_24.md) — Forked
  from sports_consolidated_closeout_2026_07_19.md's "Live contradiction with this closeout's FROZEN-legacy-path
  declaration" todo (operator ruling 2026-07-24: scope a real migration, do not grandfather). instruments-service's…
- [`sports_live_availability_and_source_latency_2026_07_24`](./sports_live_availability_and_source_latency_2026_07_24.md)
  — Sports-specific live/forward data-availability matrix (per data_type x source: availability phase, live
  timestamp/cadence, live feed status, gap + cheap-source recommendation) and the companion source-latency validation
  (empirical p95-lag…
- [`sports_odds_feature_naming_canonicalization_2026_07_21`](./sports_odds_feature_naming_canonicalization_2026_07_21.md)
  — Operator-ruled 2026-07-21 (BLK-a1ce4719) resolution of sports_odds_feature_naming_four_way_mismatch_2026_07_21.md —
  direction is UAC-as-SSOT (Option A), executed as a scoped migration, not a blind rename. Picks deliberate field names
  for…
- [`sports_predictions_live_mode_activation_readiness_2026_07_21`](./sports_predictions_live_mode_activation_readiness_2026_07_21.md)
  — Scopes the full MTDS/MDPS/FSS/strategy-service live-mode activation chain for asset_group=sports and
  asset_group=prediction so a plan is READY, not to activate live trading now — both asset groups are deliberately
  backtest-only today per…
- [`sports_satellite_ao_dispatch_batch2_2026_07_24`](./sports_satellite_ao_dispatch_batch2_2026_07_24.md) — 22 sports-AG
  satellite plans/issues were confirmed `assigned_vm: NA` / `execution_scope: local-only` — referenced by
  `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s discoverability index for human visibility only,
  never…
- [`sports_satellite_ao_dispatch_batch2_finalize_2026_07_24`](./sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md)
  — Gated closeout for sports_satellite_ao_dispatch_batch2_2026_07_24.md — machine-held via depends_on +
  gate_on_depends: true until all 37 of that plan's todos are done (corrected 2026-07-25 plan-reconcile, was 36), so
  this never dispatches…
- [`sports_satellite_ao_dispatch_batch3_2026_07_25`](./sports_satellite_ao_dispatch_batch3_2026_07_25.md) — Third
  AO-dispatch batch for sports, extracted from the 2026-07-25 orphan-audit's 26 genuinely-orphaned satellite docs (of 72
  sports-primary docs total; see `ag_closeout_audit_rollout_2026_07_25.md` for the full audit). A 26-agent…
- [`sports_satellite_ao_dispatch_batch3_finalize_2026_07_25`](./sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for sports_satellite_ao_dispatch_batch3_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 12 of that plan's todos are done. Mirrors
  sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md's…
- [`sports_satellite_ao_dispatch_batch4_2026_07_25`](./sports_satellite_ao_dispatch_batch4_2026_07_25.md) — Fourth
  AO-dispatch batch for sports, produced by the `/ag-closeout-audit` skill's "batchN methodology" (iterative drain):
  re-checks batch3's own `## Deferred — conflict-gated` section (6 docs, 7 AO-eligible candidates, 2026-07-25) against…
- [`sports_satellite_ao_dispatch_batch4_finalize_2026_07_25`](./sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for sports_satellite_ao_dispatch_batch4_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 3 of that plan's todos are done. Mirrors
  sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md's…
- [`sports_satellite_ao_dispatch_batch5_2026_07_26`](./sports_satellite_ao_dispatch_batch5_2026_07_26.md) — Fifth
  AO-dispatch batch for sports, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 60 sports AG-primary docs not already covered by the consolidated closeout,…
- [`sports_satellite_ao_dispatch_batch5_2026_07_26_finalize`](./sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md)
  — Gated closeout for sports_satellite_ao_dispatch_batch5_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 25 of that plan's todos are done. Mirrors batch3/batch4-finalize's pattern (reconcile
  each distinct source…
- [`sports_satellite_ao_dispatch_batch6_2026_07_26`](./sports_satellite_ao_dispatch_batch6_2026_07_26.md) — Sixth
  AO-dispatch batch for sports, produced by an `/ag-closeout-audit sports` run later on 2026-07-26 (autonomous mode,
  operator away). batch5's Phase-1 snapshot was taken earlier the SAME day; its own execution then (a) split…
- [`sports_satellite_ao_dispatch_batch6_2026_07_26_finalize`](./sports_satellite_ao_dispatch_batch6_2026_07_26_finalize.md)
  **[draft]** — Gated closeout for sports_satellite_ao_dispatch_batch6_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 9 of that plan's todos are done. Mirrors the batch3/batch4/batch5-finalize pattern
  (reconcile each…
- [`sports_satellite_ao_dispatch_batch7_2026_07_27`](./sports_satellite_ao_dispatch_batch7_2026_07_27.md) — Seventh
  AO-dispatch batch for sports, produced by an `/ag-closeout-audit sports` run 2026-07-27 (autonomous mode, operator
  away) targeted specifically at `sports_consolidated_closeout_2026_07_19.md`'s own ~35 remaining open todos (not a…
- [`sports_satellite_ao_dispatch_batch7_2026_07_27_finalize`](./sports_satellite_ao_dispatch_batch7_2026_07_27_finalize.md)
  — Gated closeout for sports_satellite_ao_dispatch_batch7_2026_07_27.md — machine-held via depends_on +
  gate_on_depends: true until all 4 of that plan's todos are done. Mirrors the batch3-6-finalize pattern: reconcile each
  distinct source…
- [`sports_track_h_denominator_gated_2026_07_28`](./sports_track_h_denominator_gated_2026_07_28.md) — Extracted,
  verbatim, from `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H denominator todo — 4 consecutive
  same-day dispatches (slots 11, 7, 10, 15 on 2026-07-28) confirmed the same 2 real blockers (`odds_horizon_bucket`…
- [`sports_track_h_denominator_prereqs_2026_07_28`](./sports_track_h_denominator_prereqs_2026_07_28.md) — The 2 real
  remaining blockers (of an original 3) on `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H
  "registry-aware honest-coverage denominator" todo — confirmed still unshipped across 4 consecutive same-day
  dispatches…

### prediction (39)

- [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) — Autonomous session (/autonomous,
  operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset groups that haven't had it yet —
  cefi, defi, tradfi, prediction — each of which already carries its own…
- [`candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27`](./candle_canonical_path_migration_execution_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for candle_canonical_path_migration_execution_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`canonical_id_builder_retrofit_checklist_2026_07_08`](./canonical_id_builder_retrofit_checklist_2026_07_08.md) — The
  operator-decided one-builder architecture (instrument_id_format_canonicalization_2026_07_08.md — "one builder for
  everything... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by…
- [`canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27`](./canonical_id_builder_retrofit_checklist_2026_07_08_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for canonical_id_builder_retrofit_checklist_2026_07_08.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`data_completion_prediction_2026_07_15`](./data_completion_prediction_2026_07_15.md) — Prediction slice of the
  data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on 2026-07-15 per
  operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the…
- [`data_pipeline_check_mdps_features_2026_07_20`](./data_pipeline_check_mdps_features_2026_07_20.md) — Extend the
  shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle derivation) and
  features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers + two Claude…
- [`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27`](./data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for data_pipeline_check_mdps_features_2026_07_20.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`instruments_satellite_ao_dispatch_batch1_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_2026_07_27.md) —
  First /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified
  honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md as mixed across 14 open items: 8 are genuinely
  operator/judgment-gated (stay NA),…
- [`instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27`](./instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md)
  — Gated closeout for instruments_satellite_ao_dispatch_batch1_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 5 batch todos is done, reconciles the
  corresponding checkbox…
- [`is_daily_enum_capture_heal_2026_07_07`](./is_daily_enum_capture_heal_2026_07_07.md) — is-daily-enum-prediction (dead
  07-01→) and is-daily-enum-sports (dead 06-28→, longer, previously undetected) both still exit(1) in the cloud even
  though the deployed image now carries the UTL write-side dtype coercion — a SECOND, different…
- [`is_daily_enum_capture_heal_2026_07_07_finalize_2026_07_27`](./is_daily_enum_capture_heal_2026_07_07_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for is_daily_enum_capture_heal_2026_07_07.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todos ship…
- [`mdps_candle_manifest_population_disconnect_2026_07_25`](./mdps_candle_manifest_population_disconnect_2026_07_25.md)
  — MDPS-owned root-cause + fix for the candle object↔manifest disconnect — root-cause first (three undistinguished
  hypotheses), because a fresh 2026-07-25 re-measurement shows the manifest is STILL only 6 degenerate CEFI rows, 4 days
  AFTER…
- [`mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27`](./mdps_candle_manifest_population_disconnect_2026_07_25_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mdps_candle_manifest_population_disconnect_2026_07_25.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`mtds_available_at_cross_asset_backfill_2026_07_13`](./mtds_available_at_cross_asset_backfill_2026_07_13.md) —
  Backfill the historical available_at="" backlog on CAPTURED market-data-tick manifest rows, now that
  unified-trading-library@9c9cdc50 fixed record_captured()/record_captured_from_counts() to actually persist the value.
  Phases…
- [`mtds_available_at_cross_asset_backfill_2026_07_13_finalize_2026_07_27`](./mtds_available_at_cross_asset_backfill_2026_07_13_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for mtds_available_at_cross_asset_backfill_2026_07_13.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`prediction_capture_incident_remediation_2026_07_06`](./prediction_capture_incident_remediation_2026_07_06.md) —
  "Actionable remediation for the 2026-07-01→07-06 prediction-universe-capture outage (diagnosis + root-cause evidence:
  issue doc prediction_universe_capture_dead_since_07_01_2026_07_06). Two workstreams: (A) harden the capture path —
  UTL…
- [`prediction_consolidated_closeout_2026_07_18`](./prediction_consolidated_closeout_2026_07_18.md) — Single
  coordination plan that AGGREGATES (references, does not duplicate) every open prediction + prediction-touching IS/MTDS
  plan and issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md and…
- [`prediction_consolidated_native_ao_extract_2026_07_25`](./prediction_consolidated_native_ao_extract_2026_07_25.md) —
  First AO-eligibility triage of prediction_consolidated_closeout_2026_07_18.md's OWN native `- [ ]` todos (distinct
  from the prediction_satellite_ao_dispatch_batch1/2 docs, which extracted from OTHER orphaned prediction plans/issues
  and…
- [`prediction_consolidated_native_ao_extract_2026_07_25_finalize`](./prediction_consolidated_native_ao_extract_2026_07_25_finalize.md)
  **[draft]** — Gated closeout for prediction_consolidated_native_ao_extract_2026_07_25.md — machine-held via
  depends_on + gate_on_depends: true until all 5 of that plan's todos are done. This extract's own source WAS…
- [`prediction_cross_venue_arb_and_coverage_2026_07_24`](./prediction_cross_venue_arb_and_coverage_2026_07_24.md) — The
  cross-venue Kalshi↔Polymarket arb detector (matcher, dispersion features, strategy engine, GCS arb-store, live
  dispatch), cqg canonicalization, the honest-coverage P0 correctness chain (43a-43d), and historical backfill/manifest
  work…
- [`prediction_live_clob_depth_capture_2026_07_24`](./prediction_live_clob_depth_capture_2026_07_24.md) — The live/batch
  data-capture pipeline for PREDICTION Kalshi + Polymarket YES/NO markets — WS connectors, transport/ sink correctness,
  message-shape fixes, live producer VM operations, source/pipeline-mode registration; split out of…
- [`prediction_phase_ab_residuals_2026_07_24`](./prediction_phase_ab_residuals_2026_07_24.md) — Phases A
  (get-the-code-ready — capture path, canonical-identity writers, venue-perps residuals, fixture-attribute writers) and
  B (manifest/catalogue migrations) of the prediction consolidated close-out, split out verbatim (line-cap…
- [`prediction_phase_c_data_status_ui_2026_07_24`](./prediction_phase_c_data_status_ui_2026_07_24.md) — Phase C of the
  prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — RE-ADD the data-status
  "dimensions enumeration" view to deployment-ui/api, confirm honest-coverage rolls up prediction correctly +…
- [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24`](./prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)
  — Phase D of the prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — the
  `-test-` bucket isolation, MVP-scope reconciliation, and smoke-adaptation code fixes are shipped; residual open work
  is running…
- [`prediction_phase_e_football_arb_live_2026_07_24`](./prediction_phase_e_football_arb_live_2026_07_24.md) — Phase E of
  the prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — the af_fixture_id
  identity chain (Polymarket + Kalshi soccer, ~0%→~100% team-name matching) and the 3-venue Kalshi/Polymarket/Betfair…
- [`prediction_satellite_ao_dispatch_batch1_2026_07_25`](./prediction_satellite_ao_dispatch_batch1_2026_07_25.md) —
  First AO-dispatch batch for prediction (prediction has never had one before, unlike sports). Extracted from the
  2026-07-25 orphan-audit's 13 genuinely-orphaned prediction satellite docs (of 20 audited; 6 more were correctly
  deferred to the…
- [`prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25`](./prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for prediction_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 7 of that plan's todos are done. Mirrors the sports/tradfi finalize-plan pattern
  (reconcile each of…
- [`prediction_satellite_ao_dispatch_batch2_2026_07_25`](./prediction_satellite_ao_dispatch_batch2_2026_07_25.md) —
  Second AO-dispatch batch for prediction, produced by re-invoking the `/ag-closeout-audit` skill's "batchN methodology"
  against `prediction_satellite_ao_dispatch_batch1_2026_07_25.md`'s own Deferred section (12 fully-deferred orphaned
  docs…
- [`prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25`](./prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md)
  **[draft]** — Gated closeout for prediction_satellite_ao_dispatch_batch2_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 6 of that plan's todos are done. Mirrors the batch1 finalize-plan pattern (reconcile
  each of the 5…
- [`prediction_satellite_ao_dispatch_batch4_2026_07_26`](./prediction_satellite_ao_dispatch_batch4_2026_07_26.md) —
  Fourth AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run 2026-07-26
  (ag_closeout_auditor, slot 7). Phase 1 re-classified all 26 prediction AG-primary candidate docs via a Workflow
  fan-out (26…
- [`prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize`](./prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md)
  **[draft]** — Finalize/gate plan for `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`. Runs ONLY after batch4's
  dispatched todos land (`gate_on_depends: true`): flips the corresponding checkboxes back in the 2 sibling source docs…
- [`prediction_satellite_ao_dispatch_batch6_2026_07_29`](./prediction_satellite_ao_dispatch_batch6_2026_07_29.md)
  **[draft]** — Sixth AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run
  2026-07-29 (ag_closeout_auditor, slot 14). Phase 1 classified 22 prediction-primary/dual-legit AG candidate docs (of
  61…
- [`prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize`](./prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md)
  **[draft]** — Gated closeout for prediction_satellite_ao_dispatch_batch6_2026_07_29.md — machine-held via depends_on +
  gate_on_depends: true until all 13 of that plan's todos are done. Mirrors the batch4-finalize pattern (reconcile each
  of the 9…
- [`predictions_ml_walk_forward_and_arb_2026_06_20`](./predictions_ml_walk_forward_and_arb_2026_06_20.md) — Run Model 2A
  walk-forward validation (AUC gate) and ship the FSS arb_calculator — the predictions-ML half of the
  sports_predictions_e2e milestone.
- [`predictions_other_bucket_and_ui_drilldown_2026_06_20`](./predictions_other_bucket_and_ui_drilldown_2026_06_20.md) —
  Build the synthetic OTHER canonical-question-group catch-all bucket end-to-end and add the 3-level drilldown panel to
  deployment-ui for predictions data.
- [`sports_arb_decay_window_and_alpha_gate_design_2026_07_21`](./sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)
  — Brand-new feature work with zero prior spec (confirmed: grepped decay_window/arb_decay/alpha_gate/paper_trade_alpha
  across strategy-service + execution-service + codex, only unchecked todos in archived plans exist). This plan defines
  WHAT…
- [`sports_group_c_execution_backtest_harness_2026_07_21`](./sports_group_c_execution_backtest_harness_2026_07_21.md) —
  Scopes a `run_sports_backtest` CLI in execution-service, mirroring the 3 existing domain runners
  (run_cefi_backtest/run_tradfi_backtest/run_defi_backtest), so sports/predictions gets a real Group-C execution-alpha
  harness. Decided…
- [`sports_odds_feature_naming_canonicalization_2026_07_21`](./sports_odds_feature_naming_canonicalization_2026_07_21.md)
  — Operator-ruled 2026-07-21 (BLK-a1ce4719) resolution of sports_odds_feature_naming_four_way_mismatch_2026_07_21.md —
  direction is UAC-as-SSOT (Option A), executed as a scoped migration, not a blind rename. Picks deliberate field names
  for…
- [`sports_predictions_live_mode_activation_readiness_2026_07_21`](./sports_predictions_live_mode_activation_readiness_2026_07_21.md)
  — Scopes the full MTDS/MDPS/FSS/strategy-service live-mode activation chain for asset_group=sports and
  asset_group=prediction so a plan is READY, not to activate live trading now — both asset groups are deliberately
  backtest-only today per…

### cross-cutting (64)

- [`ag_closeout_audit_rollout_2026_07_25`](./ag_closeout_audit_rollout_2026_07_25.md) — Autonomous session (/autonomous,
  operator away, 2026-07-25) driving the /ag-closeout-audit skill across the 4 asset groups that haven't had it yet —
  cefi, defi, tradfi, prediction — each of which already carries its own…
- [`asset_class_to_asset_group_rename_2026_07_21`](./asset_class_to_asset_group_rename_2026_07_21.md) — Rename the
  DOMAIN-level unified_api_contracts.AssetClass (crypto/equity/fx/commodity/fixed_income) to AssetGroup across UAC + 7
  downstream consumer repos + the UI, in one coordinated atomic landing per repo (no backward-compat shims…
- [`bigquery_feature_ml_compute_engine_option_2026_06_08`](./bigquery_feature_ml_compute_engine_option_2026_06_08.md) —
  Adds BigQuery as an OPTIONAL third feature/ML compute-engine tier (in-process polars → DuckDB → BigQuery) over the
  hive-partitioned GCS corpus: Hive-partitioned external tables (uts_feature_external, one per asset_group×data_type,…
- [`bucket_estate_consolidation_closeout_2026_07_24`](./bucket_estate_consolidation_closeout_2026_07_24.md) — "Forks the
  6 still-open todos from bucket_estate_consolidation_to_sub100_2026_07_13.md (15/21 done, archived 2026-07-24 per the
  plan line-cap remediation triage) into a small standalone closeout plan: recon-bucket end-to-end chain…
- [`bucket_estate_fold_design_2026_07_13`](./bucket_estate_fold_design_2026_07_13.md) **[draft]** — "DESIGN doc for
  Wave-3 of bucket_estate_consolidation_to_sub100_2026_07_13. Specifies the five structural folds that take the
  post-Wave-2 estate (~139) to ~100 total (~80 non-GCP-system): features 25 per-AG/kind buckets → 5 per-AG (kind…
- [`bucket_fold_execution_strategy_2026_07_17`](./bucket_fold_execution_strategy_2026_07_17.md) — "Executes Folds C + D
  of the Wave-3 fold design in ONE plan (same services, same cutover window). Fold C collapses the per-AG
  execution-store buckets (cefi/defi/tradfi/sports + the execution-store-prediction kind) into a single…
- [`bucket_fold_features_2026_07_17`](./bucket_fold_features_2026_07_17.md) — "Executes Fold A of the Wave-3 fold design
  — collapses the ~25 per-AG/kind feature buckets (delta-one/volatility/onchain/xinstrument/mtf ×
  cefi/defi/tradfi/sports/pred) into FIVE per-asset-group env-tiered buckets…
- [`bucket_fold_ml_2026_07_17`](./bucket_fold_ml_2026_07_17.md) — "Executes Fold B of the Wave-3 fold design — collapses
  the five ml kind-buckets (models/predictions/configs/training-artifacts/artifacts) into ONE env-tiered
  ml-store-{env}-{pid}, kind becoming a top-level path prefix. Ground-truth object…
- [`bucket_fold_portfolio_state_2026_07_17`](./bucket_fold_portfolio_state_2026_07_17.md) — "Executes Fold E of the
  Wave-3 fold design — the LAST fold, live-trading-adjacent. Collapses six position/pnl/risk stores (positions-store,
  pnl-attribution-store, risk-metrics-store, pnl-attribution-output, archetype-state,…
- [`bucket_iam_write_protection_per_tier_2026_06_09`](./bucket_iam_write_protection_per_tier_2026_06_09.md) — Implements
  bucket-isolation-model §8 credential-level write-protection: replaces the project-wide god-SA (unified-trading-sa
  holds roles/storage.objectAdmin over all buckets) with per-tier/per-domain service accounts (batch/live SAs write…
- [`bucket_iam_write_protection_per_tier_2026_06_09_finalize_2026_07_27`](./bucket_iam_write_protection_per_tier_2026_06_09_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for bucket_iam_write_protection_per_tier_2026_06_09.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched…
- [`carry_staked_basis_funding_scan_experiment_2026_06_16`](./carry_staked_basis_funding_scan_experiment_2026_06_16.md)
  — Exploratory analysis harness + journal for the CeFi funding leg of carry_staked_basis: scans ~30 perp coins across
  venues, ranks each day by net carry (annualised short-perp funding + staking APY where the short venue accepts the LST
  as…
- [`carry_strategy_ensemble_productionization_2026_07_24`](./carry_strategy_ensemble_productionization_2026_07_24.md) —
  Forked 2026-07-24 (line-cap remediation) from carry_staked_basis_funding_scan_experiment_2026_06_16.md: the 4-strategy
  ensemble orchestrator engine (funding-dispersion / funding-rate arb / pure-basis / staked-basis) built on top of the…
- [`citadel_paper_batch_live_reconciliation_2026_06_19`](./citadel_paper_batch_live_reconciliation_2026_06_19.md) —
  Implement the determinism spine ensuring paper(W)==batch-rerun(W) trade-for-trade, with full reconciliation across
  paper/batch/live trading modes.
- [`colocated_feature_pipeline_in_memory_handoff_2026_06_21`](./colocated_feature_pipeline_in_memory_handoff_2026_06_21.md)
  — Land deferred colocated feature pipeline I/O efficiency items (in-memory DAG handoff, parquet consolidation, column
  pruning) and restore features-service basedpyright strictness.
- [`consolidator_throughput_backlog_monitor_2026_07_09`](./consolidator_throughput_backlog_monitor_2026_07_09.md) — Make
  the Consolidators cockpit tab answer "is the consolidator keeping up?" — surface the per-asset_group backlog (per-VM
  shards written since the last consolidated-index run, i.e. not yet absorbed) and a live throughput view of shards…
- [`cross_cutting_consolidated_closeout_2026_07_25`](./cross_cutting_consolidated_closeout_2026_07_25.md) — New 6th
  "asset-group-style" umbrella (alongside cefi/defi/tradfi/prediction/sports) for data-pipeline (+ a small
  strategy/execution-determinism angle, Track 24) work that genuinely spans multiple asset groups rather than belonging
  to one.…
- [`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26`](./cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md)
  — First AO-dispatch batch for the cross-cutting tranche (genuinely cross-asset-group data-pipeline work — never
  audited before this session), produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) + Phase-3…
- [`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize`](./cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md)
  **[draft]** — Gated closeout for cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md AND its sibling
  cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md — machine-held via depends_on + gate_on_depends: true until
  all 31 todos across both…
- [`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26`](./cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md)
  — Second half of the cross-cutting tranche's first AO-dispatch batch — see
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` for the full Phase-1/Phase-3 audit summary, the Deferred
  conflict-gated/operator-gated/time-gated sections…
- [`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26`](./cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md)
  — Second AO-dispatch batch for the cross-cutting tranche, produced by re-invoking `/ag-closeout-audit cross-cutting`
  after batch1/batch1b. Its dominant finding is a MEMBERSHIP gap, not a fresh-orphan gap: batch1's Phase-1 scope was 59
  docs,…
- [`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize`](./cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize.md)
  **[draft]** — Gated closeout for cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via
  depends_on + gate_on_depends: true until all 14 todos are done. Reconciles each named source doc's checkboxes
  independently, then re-checks…
- [`cross_cutting_strategy_execution_determinism_2026_07_26`](./cross_cutting_strategy_execution_determinism_2026_07_26.md)
  — Extracted 2026-07-26 from `cross_cutting_consolidated_closeout_2026_07_25.md` Track 24 (resolved
  `autonomous_session_operator_decisions_2026_07_25.md` entry #19) — a genuinely different angle from that doc's other
  23 Tracks…
- [`cross_venue_funding_reversion_research_2026_07_24`](./cross_venue_funding_reversion_research_2026_07_24.md) — Forked
  2026-07-24 (line-cap remediation) from carry_staked_basis_funding_scan_experiment_2026_06_16.md: a genuinely distinct
  strategy that only got journaled inside the carry-scan harness plan — cross-sectional / cross-venue funding-rank…
- [`data_completion_to_100_all_ag_2026_06_21`](./data_completion_to_100_all_ag_2026_06_21.md) — Drives MTDS
  market-data + IS reference-data to 100% honest-coverage across every asset group (cefi/defi/ tradfi/sports/pred),
  batch AND live, on manifest v9. Snapshot 2026-06-21: LIVE=0 rows on every AG (live pipeline never populated), low…
- [`data_feed_sla_registry_and_active_self_healing_2026_06_19`](./data_feed_sla_registry_and_active_self_healing_2026_06_19.md)
  — Build a single declarative data-feed SLA registry (consolidating scattered freshness thresholds) and add active feed
  self-healing via re-fetch on stale detection.
- [`data_pipeline_ag_residual_backfill_decisions_2026_07_24`](./data_pipeline_ag_residual_backfill_decisions_2026_07_24.md)
  — The residual per-asset-group data-backfill/scope decisions forked out of
  data_pipeline_hardening_self_monitoring_2026_06_22.md's "TradFi pending work" section + the DeFi/TradFi correctness
  items surfaced during per-AG hardening dispatch,…
- [`data_pipeline_alert_substrate_residual_2026_07_24`](./data_pipeline_alert_substrate_residual_2026_07_24.md) — The
  residual alert-substrate + hygiene-digest + writer-invariant hardening items forked out of
  data_pipeline_hardening_self_monitoring_2026_06_22.md's Phase 2/3/4/6-B sections during the 2026-07-24 line-cap
  remediation split. Everything…
- [`data_pipeline_e2e_milestones_gate_2026_07_24`](./data_pipeline_e2e_milestones_gate_2026_07_24.md) —
  Operator-specified checklist (2026-07-24) of 14 milestones that must hold, symmetrically, across all 5 asset groups
  (tradfi/defi/cefi/prediction/sports) — across every data source, venue, chain, league, fixture, data_type,
  instrument_type,…
- [`data_pipeline_hardening_self_monitoring_2026_06_22`](./data_pipeline_hardening_self_monitoring_2026_06_22.md) —
  Harden all data-pipeline adapters against silent misclassification with FetchEvidence gates, per-adapter guards, daily
  summaries, and self-monitoring alerts across all 5 asset groups.
- [`data_pipeline_reconciliation_skill_2026_07_20`](./data_pipeline_reconciliation_skill_2026_07_20.md) — Build the
  SSOT-backed `/data-pipeline-reconciliation` skill that, per asset_group, reconciles the FOUR canonical surfaces — GCS
  object path, parquet content columns, manifest shard-atom key, and the catalogue/data-status render — across…
- [`data_pipeline_self_healing_completion_residual_2026_07_24`](./data_pipeline_self_healing_completion_residual_2026_07_24.md)
  — The residual self-healing (Phase 6-C) items forked out of data_pipeline_hardening_self_monitoring_2026_06_22.md
  during the 2026-07-24 line-cap remediation split: finishing the e2e escalation-issue ship, scheduling the auto-flip…
- [`data_source_provenance_enforcement_2026_07_24`](./data_source_provenance_enforcement_2026_07_24.md) — Extracted
  2026-07-24 from data_completion_to_100_all_ag_2026_06_21.md (M-1) per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, bucket-(d) split, operator-approved). This is the
  still-inline…
- [`data_status_catalogue_true_source_phase2_2026_07_24`](./data_status_catalogue_true_source_phase2_2026_07_24.md) —
  Phase-2 follow-up forked from data_status_page_ux_and_canonicalisation_2026_07_16.md's P6 (catalogue explorer). Phase
  1 ("captured instruments, availability-derived") is shipped. This plan builds the true-catalogue / expected-universe
  side…
- [`data_status_cell_grid_rearchitecture_2026_07_18`](./data_status_cell_grid_rearchitecture_2026_07_18.md) — Operator
  ruled 2026-07-18 to schedule the real fix for a data-status tab that is fast at FULL history. Today the tab's manifest
  cell-grid is built by reading the entire per-service manifest into memory (measured ~18GB IS / 81GB MTDS / 56GB…
- [`data_status_page_ux_and_canonicalisation_2026_07_16`](./data_status_page_ux_and_canonicalisation_2026_07_16.md) —
  Eight operator issues on the instruments-service data-status page (deployment-ui + deployment-api), each
  code/live-verified via a multi-agent audit. P1 (Honest Coverage rendering only DeFi) is ROOT-CAUSED and FIXED — the
  daily writer OOM'd…
- [`data_status_tab_and_downloads_remediation_2026_06_16`](./data_status_tab_and_downloads_remediation_2026_06_16.md) —
  Fix data-status tab UI bugs and instruments CSV download regressions in deployment-api/deployment-ui, gated on v9
  manifest migration completion.
- [`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17`](./defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)
  — Implement collateral-aware position sizing with USDC down-size branch, opportunity checker scoring for stables-only
  venues, and full wizard parameterization for all supported archetypes.
- [`features_service_e2e_pipeline_test_2026_05_26`](./features_service_e2e_pipeline_test_2026_05_26.md) — Stands up a
  repeatable real-data end-to-end test of the full features-service pipeline per family (discover v8 manifest → read GCS
  inputs → calculate → write parquet + manifest row → read-back & assert). Fixes the WRITE blocker…
- [`infra_capture_and_devops_leftovers_2026_07_06`](./infra_capture_and_devops_leftovers_2026_07_06.md) — The infra-role
  slice of the instruments-completion capture work — the VM launches, connector registrations, and live runners that are
  not data_engineering tasks, plus the credential/operator-gated capture items that stay visible but cannot…
- [`infra_capture_and_devops_leftovers_finalize_2026_07_25`](./infra_capture_and_devops_leftovers_finalize_2026_07_25.md)
  — Gated closeout for infra_capture_and_devops_leftovers_2026_07_06.md ("AO Plan 6" of the instruments-completion set),
  added per the finalize-plan-coverage gate (task_template.md §4, operator ruling 2026-07-24 — every
  `assigned_vm: planning`…
- [`infra_ops_residual_migration_verification_2026_07_24`](./infra_ops_residual_migration_verification_2026_07_24.md) —
  9 residual todos forked verbatim out of the archived migration-verification/orphan-safety harness plan (2026-07-24
  plan line-cap remediation split) — the catch-all infra/ops/audit tail that didn't fit the other 3 named residual
  buckets…
- [`instrument_record_schema_completeness_extra_forbid_2026_07_18`](./instrument_record_schema_completeness_extra_forbid_2026_07_18.md)
  — Operator ruled 2026-07-18 to close the InstrumentRecord silent-drop class properly (not a minimal remove).
  InstrumentRecord uses pydantic's default extra='ignore', so any kwarg an adapter passes that the model does not
  declare is silently…
- [`instruments_completion_tracker_2026_07_06`](./instruments_completion_tracker_2026_07_06.md) — Operator-owned working
  tracker to drive the instruments denominator/numerator completion to done. Points at the source plans/issues (does NOT
  restate them). Holds the live Decision Gates, the dependency-ordered Stage 0–6 checklist, the…
- [`instruments_foundation_completeness_2026_06_24`](./instruments_foundation_completeness_2026_06_24.md) — Gated
  (G0->G5, operator sign-off each gate) rebuild of the instruments foundation cefi-first then defi/tradfi/sports --
  honest 4-state capture, expected_unattempted seeded by the IS writer, catalogue available_to from venue-truth (not…
- [`instruments_foundation_phase0_cross_cutting_2026_07_24`](./instruments_foundation_phase0_cross_cutting_2026_07_24.md)
  — Split out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split,
  operator- approved). Owns the cross-cutting Phase-0 prerequisites — observability wiring, Honest-Coverage v2,
  cumulative-drawdown…
- [`instruments_mtds_consistency_remediation_residuals_2026_07_24`](./instruments_mtds_consistency_remediation_residuals_2026_07_24.md)
  — Split 2 of 3 from instruments_mtds_subset_consistency_remediation_2026_06_17.md (2026-07-24 line-cap remediation,
  clean-partition). This is the parent's own CORE original scope -- the F1-F7/N1-N9 findings from the 2026-06-17…
- [`instruments_service_e2e_live_mock_observability_2026_07_27`](./instruments_service_e2e_live_mock_observability_2026_07_27.md)
  — Re-scoped from the never-completed Phases 5-7 of the archived 2026-03 instruments-service E2E audit
  (plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md) — live-mode 15-min clock alignment,
  mock-mode failure scenarios,…
- [`instruments_store_cf_canonicalization_single_walk_2026_07_24`](./instruments_store_cf_canonicalization_single_walk_2026_07_24.md)
  — Split 1 of 3 from instruments_mtds_subset_consistency_remediation_2026_06_17.md (2026-07-24 line-cap remediation,
  clean-partition). Carries the instruments-store canonical-form (CF-1..CF-12) single-walk code-remediation lineage --
  the…
- [`is_catalogue_g1_root_audit_log_2026_07_24`](./is_catalogue_g1_root_audit_log_2026_07_24.md) — Verbatim
  IS-catalogue-G1-root audit trail (G1-ENUM shape-aware producer ship, Era-B options/futures-chain canonicalisation, the
  G1-ENUM over-fan false-candidate finding, the G1-V8 v9-migrator "two G1 long poles" analysis) extracted from…
- [`june_2026_vintage_audit_findings_2026_07_27`](./june_2026_vintage_audit_findings_2026_07_27.md) — Durable capture of
  the 2026-07-27 /plan-vintage-audit run over all 81 June-2026-created plans/issues (12-group Workflow classification).
  2 cross-plan false-citation bugs, 11 archivable-now docs, 15 migrate-to-July-plan-then-archive docs,…
- [`legacy_bucket_dual_write_decommission_2026_07_24`](./legacy_bucket_dual_write_decommission_2026_07_24.md) —
  Extracted 2026-07-24 from data_completion_to_100_all_ag_2026_06_21.md (M-1) per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, bucket-(d) split, operator-approved). This is the
  still-inline…
- [`master_data_canonicalisation_migration_catalogue_2026_06_07`](./master_data_canonicalisation_migration_catalogue_2026_06_07.md)
  — Master coordinator for data + manifest + schema migration + IS catalogue + pipeline_mode standardisation — a pure
  dependency-gated sequencer tracking the global DAG for the whole data-layer cutover.
- [`mtds_file_size_refactor_2026_06_08`](./mtds_file_size_refactor_2026_06_08.md) — MTDS/MDPS tech-debt plan — split 15
  pre-existing >900-line source files, apply pandas-to-polars adapter seam, and clear QG residuals after per-AG data
  migrations complete. Resumed 2026-07-27 (operator directive, interactive operator-gate…
- [`mtds_retry_safe_default_audit_2026_07_14`](./mtds_retry_safe_default_audit_2026_07_14.md) — Follow-up to
  issues/mtds_perp_funding_backfill_hang_2026_07_14.md. The ~70-site audit this plan was originally sized for completed
  concurrently while it was being authored — market-tick-data-service@f82f29c1 (slot-8) classified all 70…
- [`mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24`](./mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md)
  — Split 3 of 3 from instruments_mtds_subset_consistency_remediation_2026_06_17.md (2026-07-24 line-cap remediation,
  clean-partition). Carries the venue-onboarding + operational-hardening workstreams that accumulated inline in the
  parent…
- [`mvp_scope_catalogue_tagging_2026_06_08`](./mvp_scope_catalogue_tagging_2026_06_08.md) — Build a rules-derived MVP
  subset of the instrument catalogue (instruments + features + strategies + models) and wire a toggle into data-status
  so missing-data counts only MVP in-scope cells.
- [`pipeline_mode_partition_migration_2026_06_01`](./pipeline_mode_partition_migration_2026_06_01.md) — Promote
  pipeline_mode from a column to an on-disk hive partition key in GCS paths by bundling the change as a rider into each
  asset group's next scheduled whole-corpus manifest canonicalisation walk.
- [`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`](./pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md)
  — Standardise pipeline_mode to source-aware live/batch/replay schema across all repos, gating all v9 manifest --apply
  runs on Phase 0 completion.
- [`pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28`](./pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md)
  — Forked from the [REVIEW] P1 todo in
  /plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md's "NEW FINDING" section —
  unified-trading-pm's OWN `.github/workflows/` had never been run through…
- [`self_hosted_runner_pm_core_workflows_2026_07_28`](./self_hosted_runner_pm_core_workflows_2026_07_28.md) — Follow-up
  to the Wave-2 self-hosted-runner migration's "NEW FINDING" — unified-trading-pm's OWN `.github/workflows/` had never
  been run through `scripts/self-hosted-runners/classify-glue-workflows.sh` as a directed audit. Re-running it…
- [`sports_prediction_mvp_writetime_precompute_2026_07_24`](./sports_prediction_mvp_writetime_precompute_2026_07_24.md)
  — Forked out of mtds_data_status_page_parity_2026_07_21.md's sole remaining open todo (plan line-cap remediation,
  2026-07-24): implement the already-traced, already-designed write-time `mvp: bool` stamp for sports/prediction rows on
  UTL's…
- [`v2_engine_venue_buildout_2026_06_15`](./v2_engine_venue_buildout_2026_06_15.md) — Build out real strategy engines
  for 22 engineless archetypes and wire up 9 unwired venues in the v2 strategy framework.
- [`ws_i_service_to_service_auth_migration_2026_07_28`](./ws_i_service_to_service_auth_migration_2026_07_28.md) —
  "Re-homes WS-I (the service-to-service-auth migration onto the UTL create_s2s_auth_dependency factory) out of the
  archived cicd_consolidated_remaining_2026_06_24.md, per operator decision 2026-07-27 — WS-I specifically is still
  wanted; the…

### ao (4)

- [`ao_fleet_observability_kpis_2026_07_20`](./ao_fleet_observability_kpis_2026_07_20.md) — Roughly four of five
  dispatches produce no completion and nothing surfaces it, 43% of CI escalations go unresolved after ~3.8 dispatches
  each, plan_health burns 55 haiku runs a day of which 13 return nothing, snapshot recency is…
- [`ao_satellite_ao_dispatch_batch1_2026_07_26`](./ao_satellite_ao_dispatch_batch1_2026_07_26.md) — FIRST AO-dispatch
  batch for the `ao` topic tranche, produced by the `/ag-closeout-audit` skill's full Phase-0/1/2/3 procedure over all
  35 AO-tranche-primary docs (2026-07-26, autonomous mode). The tranche had NO batch plan at all and its…
- [`ao_satellite_ao_dispatch_batch1_finalize_2026_07_26`](./ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md)
  **[draft]** — Gated closeout for ao_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on +
  gate_on_depends until every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE
  source issue doc (the…
- [`orchestrator_vm_e2e_hardening_2026_07_24`](./orchestrator_vm_e2e_hardening_2026_07_24.md) — Agent-orchestrator
  bootstrap/watchdog/memory-guardrail hardening and VM-from-scratch e2e validation — split out of
  monitoring_control_plane_master_2026_06_10.md as a file-disjoint scope-creep section (agent-orchestrator internals,
  not the…

### ci (9)

- [`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24`](./capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md)
  — Small follow-up plan forking the 2 residual items left open when `capability_wizard_and_manifest_2026_06_11.md`
  archived (65/67 todos done, plan-line-cap remediation 2026-07-24): (1) the CI-runner-blocked full
  `generate-unified-openapi.sh`…
- [`ci_satellite_ao_dispatch_batch1_2026_07_26`](./ci_satellite_ao_dispatch_batch1_2026_07_26.md) — First AO-dispatch
  batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-26) after
  `/plan-reconcile ci` had just cleaned the same corpus. Phase 0 found the tranche has NO dispatch vehicle at all —…
- [`ci_satellite_ao_dispatch_batch1_finalize_2026_07_26`](./ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md)
  **[draft]** — Gated closeout for ci_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 29 of that plan's todos are done. Carries the ONE piece of work the batch deliberately
  could not contain: the…
- [`ci_satellite_ao_dispatch_batch2_2026_07_29`](./ci_satellite_ao_dispatch_batch2_2026_07_29.md) **[draft]** — Second
  AO-dispatch batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-29)
  re-running against `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (still `status: active`, 14/30 todos done at audit…
- [`ci_satellite_ao_dispatch_batch2_finalize_2026_07_29`](./ci_satellite_ao_dispatch_batch2_finalize_2026_07_29.md)
  **[draft]** — Gated closeout for ci_satellite_ao_dispatch_batch2_2026_07_29.md — machine-held via depends_on +
  gate_on_depends: true until all 14 of that plan's todos are done. Reconciles each distinct source doc's
  checkboxes/prose independently,…
- [`cicd_mvp_ldr_to_main_pipeline_2026_06_30`](./cicd_mvp_ldr_to_main_pipeline_2026_06_30.md) — "OPERATOR DECISION
  (Harsh + Ikenna, reaffirmed 2026-06-30): we do NOT need the complex CI/CD pipeline. The MVP is: commits reach LDR via
  local-green quality-gates + quickmerge (already enforced) → SIT validates → merge LDR→main. Staging is…
- [`github_actions_operator_gated_followups_2026_07_17`](./github_actions_operator_gated_followups_2026_07_17.md) — Open
  follow-up work forked from /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md per the 2026-07-23
  plan line-cap remediation triage. Carries every todo from the parent that was still open (9 total): the quickmerge…
- [`monitoring_control_plane_master_2026_06_10`](./monitoring_control_plane_master_2026_06_10.md) — Master coordinator
  for the monitoring control plane — CI dashboard in deployment-ui and fleet git-health in the orchestrator, providing a
  single-pane view of repo pipeline state and slot health.
- [`ui_build_warm_cache_2026_06_17`](./ui_build_warm_cache_2026_06_17.md) — Keep the UI quality-gate build cache warm so
  incremental rebuilds only recompile changed code, not the full app.

### infrastructure (15)

- [`artifact_pipeline_observability_2026_07_17`](./artifact_pipeline_observability_2026_07_17.md) — A new /ops/artifacts
  page that shows the deployment estate's FINAL stage end-to-end — every Docker image and VM tarball built, where it
  landed, what git SHA it carries, why a build failed, and (the view that does not exist today) what each…
- [`codex_violations_ratchet_to_five_2026_06_10`](./codex_violations_ratchet_to_five_2026_06_10.md) — Ratchet all repo
  codex-violation budgets to ≤5 fleet-wide and split egregious oversized source files (registry.py 18k, orchestrator.py
  8k).
- [`codex_vs_repo_docs_ssot_audit_2026_06_01`](./codex_vs_repo_docs_ssot_audit_2026_06_01.md) — Audit and consolidate
  all active repo docs/ folders against codex/ SSOT, removing duplication and migrating unique content into codex.
- [`codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27`](./codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for codex_vs_repo_docs_ssot_audit_2026_06_01.md -- machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own checkboxes/prose once
  its AO-dispatched todos…
- [`docker_artifact_registry_cleanup_policy_2026_07_24`](./docker_artifact_registry_cleanup_policy_2026_07_24.md) —
  Executable, human-driven fix for the unbounded Docker-image retention issue (4.01 TB, ~$400/mo, no cleanup policy on
  any of 75 GCP AR repos + 20 AWS ECR repos). Audit-first — enumerate which image digests are ACTUALLY deployed in prod…
- [`docker_artifact_registry_cleanup_policy_2026_07_24_finalize_2026_07_27`](./docker_artifact_registry_cleanup_policy_2026_07_24_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for docker_artifact_registry_cleanup_policy_2026_07_24.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`docker_artifact_registry_cleanup_side_tracks_2026_07_27`](./docker_artifact_registry_cleanup_side_tracks_2026_07_27.md)
  — Satellite plan split out of docker_artifact_registry_cleanup_policy_2026_07_24.md on 2026-07-27 so this work can run
  IN PARALLEL with that plan's Phase B-D `unified-trading-system` spine instead of being serialized behind it by the…
- [`e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27`](./e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md)
  — Three services have no genuine end-to-end test coverage, surfaced by the 2026-07-27 pre-June-1 stale-plans audit
  while archiving the old plans/active/end-to-end-testing/ per-service checklist. alerting-service and
  deployment-service each…
- [`infra_satellite_ao_dispatch_batch1_2026_07_26`](./infra_satellite_ao_dispatch_batch1_2026_07_26.md) — The infra
  tranche's covering set is a ZERO-TODO digest. `infra_consolidated_closeout_2026_07_25.md` lists 32 Source docs for
  discoverability and carries no `- [ ]` of its own (verified: `grep -cE '^\s*-\s*\[[ xX]\]'` on it returns 0), and…
- [`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26`](./infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md)
  **[draft]** — Gated closeout for `infra_satellite_ao_dispatch_batch1_2026_07_26.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 25 of that plan's todos are done, so this can never dispatch early. Batch 1 was
  extracted from 17…
- [`infra_satellite_ao_dispatch_batch2_2026_07_27`](./infra_satellite_ao_dispatch_batch2_2026_07_27.md) — First
  /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified 21 assigned_vm:NA docs; 4 verdicted
  RECLASSIFY carried mixed content (some items genuinely bounded, others still operator/judgment-gated) — per the…
- [`infra_satellite_ao_dispatch_batch2_finalize_2026_07_27`](./infra_satellite_ao_dispatch_batch2_finalize_2026_07_27.md)
  — Gated closeout for infra_satellite_ao_dispatch_batch2_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 9 batch todos is done, reconciles the
  corresponding checkbox back…
- [`na_docs_validity_and_ao_eligibility_audit_2026_07_26`](./na_docs_validity_and_ao_eligibility_audit_2026_07_26.md) —
  Scoped 2026-07-26 per operator directive, for a FUTURE session (not this one). The 2026-07-25/26 `/ag-closeout-audit`
  9-tranche run + this session's mass-flip only ever acted on ORPHANED docs (no active plan covering them) — it never…
- [`repo_scripts_governance_audit_2026_06_18`](./repo_scripts_governance_audit_2026_06_18.md) — Govern the scripts/
  directories across repos — add ruff-lint pass, audit for deprecation/deletion, and define the strict-quickmerge carve
  scope for D16.
- [`stash_pile_workspace_cleanup_2026_06_03`](./stash_pile_workspace_cleanup_2026_06_03.md) — Runbook for auditing and
  clearing git stash piles across all workspace repos on any host, with archive-first conservative tooling.

### meta (10)

- [`ao_open_issues_consolidated_close_out_2026_07_17`](./ao_open_issues_consolidated_close_out_2026_07_17.md) —
  2026-07-17 operator-session sweep of the 10 open AO issue docs — every doc's claims re-verified against the current
  LDR code AND the production orchestrator on the planning VM (read-only SSM — live state.db, activity_log, process
  table,…
- [`data_pipeline_alerts_batch_remediation_2026_07_15`](./data_pipeline_alerts_batch_remediation_2026_07_15.md) —
  "Operator pasted a dense batch of data-pipeline-alerts Slack alerts (2026-07-14 23:50 to 2026-07-15 00:19 UTC) —
  DP_RUN_MOSTLY_EMPTY across sports/cefi/defi/tradfi and DP_VM_EXIT_NONZERO for features-sports VMs — and asked (a) why…
- [`deepseek_claude_blended_provider_routing_2026_07_28`](./deepseek_claude_blended_provider_routing_2026_07_28.md) —
  Register DeepSeek V4 Pro as a second, first-class model provider in agent-orchestrator's account pool, and add a
  routing layer so AutoSpawn decides per-task whether a fresh spawn uses DeepSeek or a Claude Max account — a real
  policy…
- [`deployment_registry_firestore_migration_2026_07_14`](./deployment_registry_firestore_migration_2026_07_14.md) —
  Design overview + phase index for migrating the deployment registry (heartbeat + lifecycle state, one JSON blob per VM
  under deployments/active/ in GCS) to Firestore. The GCS-object-per-VM read pattern does not scale — the inventory
  census…
- [`deployment_registry_firestore_p0_unblock_2026_07_14`](./deployment_registry_firestore_p0_unblock_2026_07_14.md) —
  Restore the prod Deployments tab NOW, before the multi-week Firestore migration. The inventory census times out and
  renders empty because ~3k stale registry entries must be downloaded within a 45s bound. Fix it two ways — schedule
  the…
- [`deployment_registry_firestore_p0_unblock_2026_07_14_finalize_2026_07_27`](./deployment_registry_firestore_p0_unblock_2026_07_14_finalize_2026_07_27.md)
  **[draft]** — Gated closeout for deployment_registry_firestore_p0_unblock_2026_07_14.md -- machine-held via
  depends_on + gate_on_depends: true until all of that plan's todos are done. Reconciles the source doc's own
  checkboxes/prose once its…
- [`deployment_registry_firestore_p3_cutover_2026_07_14`](./deployment_registry_firestore_p3_cutover_2026_07_14.md) —
  Once every reader is on Firestore (Phase 2), stop writing GCS — drop the dual-write so Firestore is the sole SSOT —
  then delete the GCS registry blobs after a snapshot, keeping only a codex note of the GCS-to-Firestore lineage. The
  two…
- [`deployment_registry_firestore_p5_verify_2026_07_14`](./deployment_registry_firestore_p5_verify_2026_07_14.md)
  **[draft]** — Prove the migration actually solved the scale ceiling — a synthetic 5,000-doc registry with the
  inventory query + UI render staying under budget, a recorded heartbeat-cadence cost recommendation — then close the
  loop in the docs by…
- [`deployment_ui_observability_ux_tracker_2026_07_17`](./deployment_ui_observability_ux_tracker_2026_07_17.md)
  **[draft]** — Operator-driven tracker for the next round of deployment-ui work, captured 2026-07-17 so nothing is lost
  — to be SPLIT into per-workstream AO plans before dispatch. WS-1 Cost/day column accuracy (root cause CONFIRMED by
  code trace — the…
- [`qg_host_adaptive_resource_governor_2026_07_14`](./qg_host_adaptive_resource_governor_2026_07_14.md) — Replace
  quality-gates.sh's fixed-K host-concurrency token bucket with a host-adaptive admission controller that reads each
  host's real MemTotal/MemAvailable + physical cores at runtime and admits a QG heavy phase only when BOTH a RAM…

<!-- AUTO-INDEX-END -->

---

## How to Use This Index

1. **To find a plan by domain:** grep this file for a `### <asset_group>` heading (the ten
   `plans/PLAN_FORMAT.md`-declared groups: cefi, defi, tradfi, sports, prediction, cross-cutting, ao, ci,
   infrastructure, meta) or search for a keyword — every entry carries the plan's own `summary:` frontmatter.
2. **To run a plan:** click the link and follow the plan's execution steps.
3. **To create a new plan:** author it per `plans/active/task_template.md` with correct `asset_group:` + `summary:`
   frontmatter — it appears here automatically on the next regen, no manual INDEX edit needed.
4. **Regen cadence:** wired into `scripts/plan-hygiene/run_hygiene_sweep.sh` (dry-run, no auto-commit there); run
   `python3 scripts/plans/regenerate_active_plan_index.py --commit` directly for a self-committing regen.
