---
doc_type: plan
title:
  Migration verification & orphan-safety — the 'migrate once, never need a v10' harness (canonical possible-manifest
  registry + bidirectional orphan sweep + schema-attribute completeness + catalogue-seeded denominator + candle-edge +
  verified-delete + projected-manifest preview), folded into re-runnable CF-15…CF-21
summary:
  Build the "migrate once, never need a v10" harness — a canonical possible-manifest registry + bidirectional orphan
  sweep + schema-attribute completeness verification that acts as the G3.5 pre-apply gate for the v9 data migration.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [migration, orphan-safety, manifest, verification, harness, audit, data-quality]
related:
  [
    /plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md,
    /plans/active/prediction_cqg_residual_2026_07_24.md,
    /plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md,
    /plans/active/defi_venue_lst_rates_residual_2026_07_24.md,
    /plans/active/infra_ops_residual_migration_verification_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: 2026-06-10
parent_epic: manifest_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 11
estimate_calibrated_ai_days: 6.6
last_updated: 2026-07-24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - operator 2026-06-10 ("worried about GCS orphans after migration; prove everything migrated; projected v9 manifest we
    can hook data-status/deployment-UI to in dev to see the goalposts; delete only what's in the manifest; know the data
    size; migrate once — no v10 because we missed an attribute or a whole shard-dynamic")
  - operator 2026-06-10 ("registry of all possible shard dynamics per AG = consolidation of the possible manifest; run
    manifest where we only have instruments → seed denominator as expected_unattempted; candle left/right edge from
    external sources; everything new must be augmented into the re-runnable audit instructions; non-data GCS paths (vm
    logs) understood not deleted")
  - {
      audit:
        plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md (the full design + decisions),
    }
codex_ssots:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/bar-boundary-candle-edge-convention.md,
    plans/audit/instructions/canonical_form_cross_service_audit_checklist.md,
  ]
drift_direction: advance-code
---

# Migration verification & orphan-safety — the "migrate once" harness

> **Archived 2026-07-25** — all todos verified done, no living-tracker/recurring purpose. status: active -> complete.

> **🟡 TRIMMED + UNLOCKED (2026-07-24, plan line-cap remediation split,
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 18 / bucket (d)).** This plan's durable protocol
> (CF-15…CF-21) already migrated to codex (see the V7 todos below) — it is now a **narrative citation, not the mechanism
> SSOT**. Its full historical Progress Log (all 2026-06-10→2026-06-22 entries) is archived VERBATIM as an Appendix to
> `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md`. Every genuinely-open `- [ ]` todo
> that was in this plan (15 total, across the main body + Progress Log) has been forked verbatim into 4 small residual
> plans, tracked there going forward — nothing was dropped:
>
> - `plans/active/prediction_cqg_residual_2026_07_24.md` (2 todos)
> - `plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md` (2 todos)
> - `plans/active/defi_venue_lst_rates_residual_2026_07_24.md` (2 todos)
> - `plans/active/infra_ops_residual_migration_verification_2026_07_24.md` (9 todos)
>
> `locked_by: live-defi-rollout` is cleared (operator-approved unlock, 2026-07-24) — the harness build this plan tracked
> is done and its mechanism lives in codex now. What remains below (all closed) is kept as the historical record of what
> this plan built.

> **🟢 V6 CLOSED (2026-07-06).** TradFi G4 `--apply` DONE for 2020-2025 + 2026 (7 VMs total, e2-standard-16 · SPOT ·
> workers 24 · per-year; launcher OOM-fix `deployment-service@77cfcda`; MTDS pin `9ecd1e29e16429f8`). 2026 year landed
> 15:14 UTC via `canonical-migration-tradfi-20260706-145606` (planned=332825 moved=122703, exit_code=0, fatal=0). **All
> 5 AGs now canonical (5/5).** Post-apply cleanup (E5 manifest rebuild + orphan sweep re-run + enumerate-seed +
> straggler re-run) tracked in `tradfi_v9_stage1_finish_2026_07_06.md`. Tracker:
> `instruments_completion_tracker_2026_07_06.md`. **SCOPE CLARIFIED 2026-07-14 (doc-reconciliation verify-rerun-2,
> finding 155)**: "canonical (5/5)" here means the **G4 physical `--apply`** (path/schema migration) is done for all 5
> AGs — it does NOT mean every AG's manifest-content is CF-1…CF-21 clean. The fresher (2026-07-11) sibling doc
> `plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md` explicitly flags **cefi as "NOT
> ADJUDICATED"** on real CF-content RED items (CF-1 string-schema, CF-4 source 54% blank/3.9M rows, CF-5 189,665
> untyped, Era-B 521,513 chain-rows) as of its own 2026-07-14 re-adjudication pass (sports/tradfi/defi were confirmed
> stale-and-fixed there; cefi was not, for lack of a fresh CF-audit re-run). Read "5/5 canonical" as G4-apply-complete,
> not as "all content-correctness gaps closed" — cefi's data-content gaps remain genuinely open pending its own fresh
> CF-audit.

> **Role**: this is the **G3.5 pre-apply verification gate** of
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — it sits between **G3** (UNION view) and **G4**
> (`--apply`). The master coordinator's **①–⑫ pre-apply audit** already proves read/write paths (⑤), batch=live (⑪),
> 4-state honesty (③④), rollback (⑫). This plan adds the **provable-completeness + preview + safe-cleanup + durability**
> layer the operator's "no v10" concern exposes: points **⑬–⑲ + G4.5**, folded into re-runnable **CF-15…CF-21**.
>
> **Decisions baked in (operator 2026-06-10)**: ⑬–⑲ **ALL HARD-BLOCK** G4 `--apply`; execution config = a
> capability/compatibility pre-flight (audit-and-enhance, post-G4); config change ≠ code bump (config_version,
> per-config).
>
> **Gating & ownership** (foundation-completion-gate: the cross-cutting layer is GREEN before the per-AG layer):
>
> | Layer                                                                | Owner                                        | AGs                  |
> | -------------------------------------------------------------------- | -------------------------------------------- | -------------------- |
> | **Cross-cutting scaffolds** (V0 registry + all tooling + durability) | **slot-3 / vm-cross-cutting**                | —                    |
> | **Per-AG runs: CeFi + Prediction** (the two STUB enumerators)        | **slot-3 / vm-cefi + vm-prediction**         | cefi, prediction     |
> | **Per-AG runs: DeFi + TradFi + Sports** (FULL enumerators)           | **slot-2 / vm-defi + vm-tradfi + vm-sports** | defi, tradfi, sports |
>
> slot-2's per-AG runs are **BLOCKED-UNTIL** slot-3's V0 + tool scaffolds are GREEN (they consume them). This matches
> the account topology (`orchestrator_vm_registry.yaml`: iggy2london→cefi/prediction/cross-cutting;
> ikenna→defi/sports/tradfi).

## Phased execution DAG (gated)

```
V0  Canonical possible-manifest registry (CF-15)         ─┐ slot-3 · BLOCKS all per-AG
V1  Catalogue-seeded enumerator (CF-16)                   ─┤ slot-3 cefi/pred (complete STUBs) ∥ slot-2 defi/tradfi/sports (verify FULL)
V2  Orphan sweep + bucket prefix taxonomy + sizing (CF-17)─┤ slot-3 builds tool → both run per-AG (single GCS walk w/ V3+sizing)
V3  Schema-attribute completeness (CF-18)                 ─┤ slot-3 builds framework → both run per-AG (rides V2 walk)
V4  Candle edge-timestamp audit (CF-19)                   ─┤ per-AG owner of each external OHLCV source
V5  Projected-manifest preview + data-status render (CF-20)┘ slot-3 builds harness → both render per-AG in dev
        ↓ (⑬–⑲ GREEN per AG)
V6  Per-AG pre-apply verdict → [G4 --apply, operator] → G4.5 verified-delete cleanup (CF-21)
V7  Durability — encode CF-15…CF-21 into the checklist + per-service instruction files (slot-3, cross-cutting)
B   MVP Phase 2-3 + config_version + execution-config compatibility pre-flight (lower priority; references existing plans)
```

## V0 — Canonical possible-manifest registry (CF-15) — slot-3, BLOCKS all per-AG

- [x] ✅ [UAC] P0. Build `unified_api_contracts/registry/possible_manifest.py` (`PossibleManifestSpec` /
      `enumerate_possible_shard_keys` / `is_valid_shard_key` / `canonical_path_templates`); composes the 3 layers, never
      re-declares; `canonical_path_templates` GENERATES the `pipeline_mode=batch_<source>/` prefixes from the source
      registry (Axis-10 de-scatter at the root). 41 tests. — uac@483e8c2a (QG-green, staging PR #119).
- [x] ✅ [UAC] P0. Axis-completeness assertion (each AG's spec declares every physical shard axis; DeFi `chain` guarded;
      RED on a missing axis) — the CF-15/CF-18 join. — uac@483e8c2a.
- [x] ✅ [REFACTOR] P0. Redirect + DELETE the scattered re-derivations: (b) `reconcile_phantom_manifest_rows_all.py`
      `prefix_tpls` now DERIVES from `canonical_path_templates` (hand-list DELETED; **byte-identical superset** verified
      for all 4 AGs) — is@da74c72c; (a) `enumerate_expected_universe.py` already reads the UAC validity layer (G1-ENUM,
      2026-06-07) — STUB docstring corrected to FULL is@da74c72c; (c) deployment-api VERIFIED already-canonical (counts
      the materialised 4-state per F4 + reads canonical UAC `get_chain_genesis_date`/`get_protocol_launch_date` — no
      bespoke cross-product to redirect). Grep-verified.

## V1 — Catalogue-seeded denominator at zero data (CF-16) — per-AG

- [x] ✅ [SCRIPT] P0. **CeFi**: VERIFIED FULL (not re-implemented) — the G1-ENUM shape-aware v2 producer
      (`_enumerate_v2_cefi`, is@6ea46565, 2026-06-07) already completed the CeFi path via the now-shipped
      `build_instrument_catalogue.py` + the UAC validity matrix; the stale STUB docstring is corrected is@da74c72c.
      Cross-checked master-plan G1-ENUM — no double-implementation.
- [x] ✅ [SCRIPT] P0. **Prediction**: VERIFIED FULL — `_enumerate_v2_prediction` (G1-ENUM) drives per-market lifecycle +
      per-row data_type grain-binding from the prediction catalogue; STUB docstring corrected is@da74c72c.
- [x] ✅ [VERIFY] P0. **DeFi / TradFi / Sports**: FULL enumerators VERIFIED reading V0's composed validity layer (no
      regression); 0-data cell → `expected_unattempted` denominator. — is@live-defi-rollout (code-read verify
      2026-06-16). All 5 `_enumerate_v2_*` are FULL + dispatch-mapped (`_V2_ENUMERATORS`, zero remaining stubs — the
      `STUB` mentions are docstrings noting the stub is CLOSED). defi/tradfi/sports each resolve data-type validity via
      `valid_data_types_for_instrument_type(asset_group, instrument_type)` (the UAC validity matrix V0's
      `possible_manifest` COMPOSES, never re-declares) + `CHAIN_GENESIS_DATES` (chain genesis) + per-instrument
      `available_from/available_to` lifecycle bounds — the exact 3 layers V0 composes (single SSOT, no divergent
      re-derivation = the no-regression guarantee). Alive cells with `row_key not in present_set` →
      `capture_status="expected_unattempted"` (the 0-data denominator). Per-AG unit tests assert it
      (`tests/unit/scripts/test_enumerate_expected_universe_v2.py`: defi pre-genesis/genesis-beats-available_from/
      delisted; tradfi pre-listing/delisted; sports pre-fixture/post-fixture/league_id-propagated) + the v1→v2 superset
      property test (`tests/integration/test_enumerate_v2_superset_property.py`). slot-2. instruments-service.

## V2 — Orphan sweep + bucket prefix taxonomy + sizing (CF-17) — slot-3 tool, both run

- [x] ✅ [SCRIPT] P0. Built the **orphan sweep** `migration_orphan_sweep.py` (GCS→manifest, the phantom-reconciler
      inverse): single walk → forced 6-class taxonomy (A/B/C/C2/D/E) with **grain-aware wildcard covering** (manifest
      coarser than objects → blank manifest field = wildcard; the fix for the prediction `A=0` false-orphan class). 18
      tests. — is@da74c72c. **RAN on real prod GCS** (cefi 5.3M obj + prediction).
- [x] ✅ [SCRIPT] P0. **Bucket prefix taxonomy**: every top-level prefix labelled (incl. the separate
      `processed_candles` corpus + vm-staging/logs, understood + never raw-tick-deleted); **`unknown_prefixes==0`
      verified on the full cefi + prediction walks** ("every byte accounted for"). — is@da74c72c.
- [x] ✅ [SCRIPT] P0. **Sizing rollup** published: cefi total **22.8 TiB** across 101 cells (biggest: DERIBIT trades
      ~3.6 TiB, OKX/BINANCE/KRAKEN book_snapshot_5 ~1 TiB each — pre-download candidates); prediction 22.7 GiB. Rides
      the single walk. — is@da74c72c.
- [x] ✅ [RUN] P0. Per-AG acceptance: `orphan_class_E==0` ∧ `unknown_prefixes==0` — **🟢 GREEN ON ALL FOUR HIVE AGs
      (2026-06-11 ~14:32Z)**: defi E=0 (13:14Z) · cefi E=0 (13:14Z, was 74,392) · prediction E=0 (13:28Z, was 61,014) ·
      tradfi E=0 (14:32Z, was 47,102); unknown*prefixes=0 everywhere. Mechanics: backfill applies (prediction 17+7,445
      converted/2,477 cells; tradfi 14,707+987 converted/~350 cells; cefi 74,392 record-only/7,965 cells; defi 100%
      matcher-false-positive — 0 needed) + one-shot `manifest_consolidator.consolidate(force=True)` per bucket (per-VM
      backfill shards → consolidated index; NO data loss — every index ≥ its pre_migration_2026_06_08 snapshot) + sweep
      fixes (pre-hive blank-venue derivation via shared backfill parser is@f73abe4; lazy footer read via UCI
      `download_bytes` — 7 weekend 0-row shells honestly split to class D). Final reports:
      `\_index/audit/orphan_sweep*<ag>.parquet` (refreshed per AG). **Sports = R8 — 🟢 GREEN 2026-06-11 ~16:12Z** (BOTH
      sports buckets E=0 + unknown_prefixes=0 via the candidate_parquet_paths-driven sweep — see the R8-part-2 Progress
      Log entry; all 5 AGs now orphan-clean). NOTE for R7/R3 verdict packs: re-run all four sweeps once more on final
      HEAD for the sign-off snapshot (defi/cefi/pred verdicts predate the last two sweep fixes — non-material to their
      corpora, but Citadel re-verifies on final code).
- [x] ✅ [SCRIPT] P0. (is@d4190ba — scripts/manifest_diff.py + tests, grain-aware wildcard covering via
      possible_manifest, human + --out JSON) **Manifest-diff tool (projected-vs-current) — operator 2026-06-10.** Build
      `instruments-service/scripts/manifest_diff.py`: load TWO `_index` parquets (the `beta_manifest_writer` PROJECTED
      v9 vs the CURRENT/live consolidated `_index`), diff by shard-key → report added / removed / changed cells +
      `capture_status` transitions + per-(AG,data_type,venue) row deltas. This is the manifest-vs-manifest diff
      (distinct from the orphan sweep's GCS-vs-manifest and the beta writer's projection) — it's what lets us SEE the
      goalposts as a delta before `--apply`. Reuses `possible_manifest.canonical_path_templates` for key alignment.
      slot-3 (cross-cutting tool); both AGs run it as part of the V5 projected-preview verdict.

## V3 — Schema-attribute completeness (CF-18) — slot-3 framework, both run

- [x] ✅ [SCRIPT] P0. Framework `migration_schema_completeness.py`: footer-column union per (AG, data_type, venue) vs
      the v9 UAC canonical contract (`schema_spec.find_schema`); RED on any silently-dropped column; partition/meta
      columns excluded; rides the orphan-sweep object list (single-walk). 8 tests. — is@da74c72c.
- [x] ✅ [RUN] P0. (2026-06-11 R2 COMPLETE — CITADEL, zero acked drops: uac@715e2ed carries ALL source columns incl. the
      11 polymarket cols via source_aliases rename maps + new defi/tradfi/prediction SchemaSpecs; alias-aware matching
      via UAC carried_column_names shipped in the checker; VERDICTS: defi 0 RED/32 cells, tradfi 0 RED/19, prediction 0
      RED/2; cefi re-verifies on R1's sweep re-run) Per-AG: any source column not carried into v9 = RED → carry it
      (extend canonical schema BEFORE apply) or operator-ack the drop in this plan. **Zero silent truncation.**
      cefi/pred=slot-3; defi/tradfi/sports=slot-2.

## V4 — Candle edge-timestamp audit (CF-19) — per-AG owner of the external OHLCV source

- [x] ✅ [VERIFY] P0. Candle-edge standing check VERIFIED LIVE — the right-edge (`t_close`) convention is codified +
      QG-enforced + per-source documented. — codex@live-defi-rollout (verify 2026-06-16).
      `/codex/02-data/bar-boundary-candle-edge-convention.md` is the SSOT (closed bar stamped on its RIGHT/close edge;
      half-open `[t_open, t_close)`). **One normalization point**: the MDPS processed-candle store (data-state verified
      right-edge correct 2026-06-08) + MTDS ingestion conversion (`databento_adapter._convert_ohlcv_open_edge_to_close`,
      stamps the row-level `bar_edge="close"` marker). **Per external source × timeframe edge label documented + handled
      source-aware** (MDPS `ohlcv_passthrough._is_start_of_period_input` decision order: `bar_edge` marker → row
      `source` provenance → `ts_event` name → census default): Databento `ts_event`=open,
      Massive=open-by-representation, Uniswap `periodStartUnix`=open → SHIFT; yahoo/barchart=close, Hyperliquid/Pacifica
      candle `T`, Binance kline `[6]`=explicit close → never shift. **Standing check is QG-wired** (not a one-off): STEP
      5.92 `check_bar_edge_open_ingestion.py` runs in BOTH `base-service.sh` (line ~3153) and `base-library.sh` (line
      ~1154) — baseline-ratchet, a NEW open-edge site fails the commit; STEP 5.74
      `check_mdps_bar_boundary_compliance.py` bans inline truncation bypasses; runtime
      `unified_trading_library.availability_stamping.assert_close_edge` raises on a mismatched edge; the **independent
      reference + batch==live** is the cross-source equivalence fixture (tick-aggregated vs pre-aggregated → SAME
      `t_close`) shipped in `market-tick-data-service/tests/unit/test_databento_bar_edge.py`,
      `market-data-processing-service/tests/unit/test_tradfi_adapters.py`,
      `features-service/tests/delta_one/unit/test_cross_source_bar_edge_equivalence.py`. Known-latent open-edge sites
      (Massive `_normalise_ohlcv`, MDPS `liquidity_adapter._convert_timestamps`) are baselined + owned by named plans +
      do NOT write consumed candles to prod. Owner = the AG's source owner (standing check now enforces it fleet-wide).
- [x] ✅ [SCRIPT] P3. **`STEP 5.92` label collision in `base-service.sh` FIXED** — pm@3be7eb595. The legacy-`category=`-
      kwarg ban (4 log lines, ~line 2214) was renumbered `STEP 5.92`→`STEP 5.98` (a globally-free number, verified
      absent across base-service.sh + base-library.sh); the bar-edge open-ingestion detector keeps the canonical
      `STEP 5.92` (matches the codex `bar-boundary-candle-edge-convention.md` + base-library.sh). Cosmetic (log prefix
      only, no gate logic; `bash -n` clean). `base-service.sh` is PM-sourced + fleet-live (sourced at runtime, NOT a
      per-repo rollout template) → the fix is live fleet-wide on merge; no `rollout-workflow-templates.sh` needed (the
      original capture-not-fix note assumed the template-rollout model — base-`*`.sh is the live-source model instead).

## V5 — Projected-manifest preview + data-status render (CF-20, ⑭) — slot-3 harness, both render

- [x] ✅ [SCRIPT] P1. `beta_manifest_writer.py` — `write_projected_index(df, --beta-manifest-out gs://<dev>/…)` writes
      the projected v9 `_index` (`schema_version` stays 9 = "v9 projected"); **dev-target HARD-guard** (refuses any
      prod/staging `_index`); no objects moved. Migrator dry-runs call it. 4 tests. — is@da74c72c. _(The per-AG dev
      render + operator goalpost eyeball remains — next item.)_
- [x] ✅ [VERIFY] P1. Per-AG dev render — **DONE via the superseding `DATA_STATUS_BETA_MANIFEST_BLOB` mechanism**
      (deployment-api `services/manifest_source.py`, landed 2026-06-11: the env var redirects EVERY data-status surface
      to `_index/audit/projected_index_{asset_group}.parquet` in the SAME prd bucket — read-only, no dev-bucket copy,
      loud-fail on a missing projection; supersedes the dev-bucket-drop recipe — 3 of 5 dev buckets never existed).
      BETA-vs-LIVE rendered + captured for instruments + market-tick-data data-status views (all 5 AGs inline);
      evidence + per-AG verdict packs at `plans/audit/results/r3_beta_renders_2026_06_11/` (pm@a30de5abd). **Operator
      goalpost EYEBALL remains open — V6.** | regression: deployment-api tests/unit/services/test_manifest_source.py

## V6 — Pre-apply verdict → G4 → verified-delete (CF-21)

- [x] ✅ [VERIFY] P0. Per-AG pre-apply verdict ⑬–⑲ GREEN for **4/5 AGs (DeFi/CeFi/Sports/Prediction)** — their G4
      `--apply` RAN to completion 2026-06-29 (evidence: `master_data_canonicalisation_migration_catalogue` "G4 apply run
      2026-06-29 — 4/5 AGs COMPLETE", slots 2/3/4/5 G4 `[x]`). The ⑬–⑲ verdict (orphan-E=0 + schema-completeness +
      candle-edge + projected preview) gated and passed for these four. cefi/pred=slot-3; defi/sports=slot-2.
- [x] ✅ [VERIFY] P0. **TradFi** pre-apply verdict ⑬–⑲ → G4 — **CLOSED 2026-07-06** (slot-7). TradFi G4 `--apply` DONE
      for 2020-2025 + 2026 via `tradfi_v9_stage1_finish_2026_07_06.md` task 1 (7 VMs total, e2-standard-16 · SPOT ·
      workers 24 · per-year fan-out; launcher OOM-fix `deployment-service@77cfcda`; MTDS pin `9ecd1e29e16429f8`; 2026
      year landed 15:14 UTC via `canonical-migration-tradfi-20260706-145606` — TOTAL planned=332825 moved=122703,
      exit_code=0, fatal=0; run.log at
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-20260706-145606/run.log`).
      Pre-apply ⑬–⑲ verdict was GREEN: V2 orphan-E=0 for tradfi 14:32Z 2026-06-11 · V3 schema 0-RED/19 cells 2026-06-11
      · V4 candle-edge convention QG-enforced · V5 projected preview rendered per-AG · IS catalogue tradfi
      `catalogue-rollup-tradfi-20260706T154714Z` (1,096,069 rows / 685,111 MVP promoted to
      `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` 2026-07-06T15:48:30 UTC). **All 5
      AGs now canonical (5/5).** Post-apply cleanup (E5 manifest rebuild + orphan sweep re-run + enumerate-seed +
      straggler re-run) tracked in `tradfi_v9_stage1_finish_2026_07_06.md`. slot-7.
- [x] ✅ [SCRIPT] P0. **G4.5 verified-delete** `cleanup_legacy_twins.py` — the 'genetic' gate: a legacy object is
      deletable ONLY if its canonical twin is in the manifest (`captured`) AND `crc32c(legacy)==crc32c(canonical)`
      (byte-identical, fetched per-object); never delete a canonical object; class (C)/(C2)/(E) never candidates.
      `--dry-run` default; `--apply` requires `--i-understand` + operator-gated like G4. 8 tests. — is@da74c72c. _(The
      `--apply` RUN stays operator-gated — post-apply re-runs the orphan sweep, E still 0.)_ slot-3 tool, both run.

## V7 — Durability: re-runnable audit instructions (operator 2026-06-10) — slot-3, cross-cutting

- [x] ✅ [DOC] P0. CF-15…CF-21 added to `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` in
      steady-state v9 form — pm@<pending-flip>. (Done in this planning session; flip on ship.)
- [x] ✅ [DOC] P0. Add the CF-15…CF-21 concrete checks to each owning per-service instruction file (`manifest_master`
      CF-15/17/21 · `instruments_master` CF-16 · `mtds_mdps_master` CF-18/19 · `deployment_and_user_management_master`
      CF-20) so re-running the per-service audit covers them — steady-state v9 form, concrete runnable commands. No CF
      item left without an owning audit. — pm@<flip>.

## A2 — Full audit of all non-operator-gated data-pipeline code work (operator 2026-06-16)

- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "FULL AUDIT — after the prediction
  cqg work, verify what is actually shipped vs left across ALL the non-operator-gated code work..." — full verbatim text
  relocated to the child plan as part of the 2026-07-24 plan line-cap remediation split.

## B — MVP, config-versioning, execution-config compatibility (lower priority; reference existing plans)

- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "MVP Phase 2-3 — already in
  `mvp_scope_catalogue_tagging_2026_06_08.md`..." — full verbatim text relocated to the child plan as part of the
  2026-07-24 plan line-cap remediation split.
- [x] ✅ [DESIGN] P1. `config_version` (per-config monotonic int + content-hash on `MVP_SCOPE` / sports-leagues /
      prediction-markets; surfaced in data-status so a coverage delta attributes to scope-change vs data-change; NO GCS
      partition key) — DESIGN folded into `mvp_scope_catalogue_tagging_2026_06_08.md` § "Config versioning
      (config_version)" with per-config decision + 3 implementation todos. — pm@<flip>. slot-3.
- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "Execution-config compatibility
  pre-flight (audit-and-enhance, NOT a new catalogue)..." — full verbatim text relocated to the child plan as part of
  the 2026-07-24 plan line-cap remediation split.

- [x] ✅ [UTL] P1. **E5 — catalogue-reader repoint to the canonical `{env}/catalog.parquet` lifecycle roll-up** —
      **unified-trading-library@94775d05** (2026-06-16 /autonomous). `instruments_catalog_reader.py` now reads
      `gs://instruments-store-{ag}-{env}-{pid}/{env}/catalog.parquet` (the `build_instrument_catalogue.py`
      `InstrumentCatalogEntry` lifecycle roll-up, env via `get_config("DEPLOYMENT_ENV","prod")`) instead of the
      decommissioned `reference_data/instruments/{ag}/all.parquet` (verified ABSENT in prod GCS for cefi+defi; the new
      object EXISTS — cefi 220,222 rows / defi 6,853 rows, both carrying `available_from`/`available_to`). Alias-aware
      column resolution (`instrument_id`↔`instrument_key`, `available_from`↔`available_from_datetime`) keeps every
      legacy-schema fixture green while serving the new shape; 48 reader unit tests pass, UTL QG green 115s.
      **`CatalogueBuilder` NOT deleted** — it remains the live per-AG current-catalogue builder wired into the IS
      orchestrator (`engine/orchestrator/catalogue.py:229`); a DIFFERENT artifact from the lifecycle roll-up (documented
      in the reader docstring). The E5 "gated on sports+pred roll-ups" note is moot for this reader (its only consumers
      are the cefi/defi `legacy_reason_classifier`; both have prod `catalog.parquet`).
- [x] ✅ [IS] P2. **Follow-up to E5 — CeFi catalogue carries `raw_symbol`/`base_asset` so the lifecycle cross-ref
      matches** — **instruments-service@30e4bb4** (2026-06-16 /autonomous). Added `raw_symbol` + `base_asset` to
      `build_instrument_catalogue.py` `CATALOG_COLUMNS` + `_extract_meta` + the generic roll-up row (populated from the
      by_date instruments-store source, which carries both); blank for prediction/sports (no exchange-native symbol).
      **NO reader change needed** — the UTL reader's existing `venue+raw_symbol` / `venue+base_asset` strategies now
      match. **Uniqueness VERIFIED on real prod data before committing to the key**: `(venue, raw_symbol)` is UNIQUE — 0
      collisions in a live snapshot (3,657 instruments) AND 0 across 14 days spanning 2019→2026 (13,905 groups), with
      `instrument_type` never disambiguating; `(venue, base_asset)` is NOT unique (119/285 groups → many instruments) so
      it stays the lossy last-resort fallback (existing best-effort contract). 40 catalogue tests pass (+2 new: carries
      the symbols; blank-not-NaN when source absent); IS QG green. Shipped via a dep-clean waiter (UAC was held dirty by
      a live peer's `perp_funding` WIP — never stomped; landed the instant deps went clean). The DETAILED measurement /
      original framing ⤵ (retained for provenance): • **Measured on real prod GCS (2026-06-16):** the CeFi
      `availability_index` DOES carry `instrument_id` (95.8% non-blank / 2.6M rows) but in **bare per-venue form**
      (`BTC-PERPETUAL`, `ADA-PERP`, `SOL-PERP`, `ARB-USDT`), whereas the new `catalog.parquet` keys on canonical
      `VENUE:TYPE:SYMBOL` (`BINANCE-FUTURES:PERPETUAL:ADA-USDT`; bare ccxt `0G/USDT:USDT` for OKX-SWAP 2,869 +
      COINBASE-SPOT 757) → **manifest∩catalog instrument_id = 0 for every CeFi venue** (OKX-SWAP 103 vs 2,912 → 0;
      BINANCE-FUTURES 51 vs 37 → 0). So the reader's per-instrument CeFi cross-ref (EXPECTED_INSTRUMENT_NOT_LISTED/
      DELISTED) stays dark (safe `SOURCE_RETURNED_ZERO` fallback, never a wrong label). **tradfi + defi are CLEAN** —
      both manifest and catalog use canonical `VENUE:TYPE:SYMBOL` so they match end-to-end (tradfi e.g.
      `CBOE:OPTION:O:SPX...`). The OLD `all.parquet` carried `raw_symbol`/`base_asset` and the reader's strategy-2/3
      matched the bare symbol against those; the new roll-up dropped them. **Correct fix (clean, no guessing):** add
      `raw_symbol` + `base_asset` to `build_instrument_catalogue.py` `CATALOG_COLUMNS` (populated from the by_date
      instruments-store source), so the reader's EXISTING `venue+raw_symbol` / `venue+base_asset` strategies match. A
      reader-side normaliser is the WRONG fix (the catalogue's own ids are internally inconsistent — 98.4% canonical vs
      3,626 bare — so there is no single target to normalise to). Repo: instruments-service
      (build_instrument_catalogue + the by_date raw_symbol availability). Provenance: E5 repoint GCS inspection,
      2026-06-16 — this run.

## Success criteria

1. V0 registry is the single could-exist SSOT; 0 bespoke cross-products remain (grep-verified).
2. Per AG: `phantom_count==0` ∧ `orphan_class_E==0`; bucket prefix taxonomy has 0 `unknown`; sizing published.
3. Per AG: schema-attribute completeness GREEN (every source column carried or operator-acked); candle-edge GREEN.
4. Projected v9 `_index` renders in dev data-status/UI; operator goalpost sign-off per AG.
5. G4 `--apply` (operator) → orphan-E still 0 post-apply → G4.5 deletes only crc32c-identical in-manifest twins.
6. CF-15…CF-21 encoded in the checklist + owning per-service instruction files (re-runnable forever).

## Progress Log

> **Archived 2026-07-24** (plan line-cap remediation split) — the full historical Progress Log that used to live here
> (2026-06-10 → 2026-06-22, ~1024 lines) is preserved **verbatim** as an Appendix to
> `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md`. Every genuinely-open `- [ ]` todo
> found within it was forked verbatim into one of 4 residual plans (see the banner at the top of this file); the 9
> already-closed `- [x]` items embedded in it are preserved unmodified in the archived Appendix. Nothing in this section
> was summarized or rewritten — it was relocated in full.
>
> New progress on this now-trimmed plan (if any — it has no open todos of its own) starts below.
