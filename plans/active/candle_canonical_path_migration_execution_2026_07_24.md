---
doc_type: plan
title:
  Candle canonical-path migration — 8-phase epic (writer/reader lockstep shipped; census → executor → per-AG SPOT
  migration → verify)
summary: |
  Extracted from data_pipeline_check_mdps_features_2026_07_20.md (plan-hygiene line-cap remediation, triage row #8):
  the operator-ruled "Option A" candle canonical-path migration — add `instrument_type=` to
  `processed_candles/` paths, keep SOURCE `data_type` on-path, align the manifest to SOURCE, and migrate the
  ~10-20M-object existing candle corpus (cefi/defi/tradfi/prediction) BACKWARD to the new shape. The parent plan's
  own text called this "an EPIC, not a cheap migration" (8 phases, P0-P8). Writer + reader lockstep (P1-P4) already
  SHIPPED across UTL/MDPS/features-service/unified-trading-api; this plan owns what remains — rebuild+verify on
  `-test-` (the gate), the Tier-2 census, the migration executor build, drain+snapshot, the per-AG SPOT apply, and
  final verify/reconcile (P5-P8).
status: active
nature: process
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos:
  [
    unified-trading-library,
    market-data-processing-service,
    features-service,
    deployment-service,
    unified-trading-pm,
    ml-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [data-pipeline, candle-canonical, migration, mdps, processed_candles, backfill, epic, canonical-paths, gcs]
related:
  [
    data_pipeline_check_mdps_features_2026_07_20,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4.0
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >
  Extracted 2026-07-24 from data_pipeline_check_mdps_features_2026_07_20.md per the plan-hygiene line-cap remediation
  triage (plan_line_cap_remediation_2026_07_23.md, row #8 / bucket (c)): the parent plan's own "8-phase EPIC, not a
  cheap migration" scoping (2026-07-21) is split into its own plan (depends_on-gated split, not a clean-partition) so
  the parent's backfill-execution todo can be gated on this plan's completion without the parent carrying the whole
  migration's history inline.
---

# Candle canonical-path migration — 8-phase epic

> **Split provenance.** This plan was extracted 2026-07-24 from
> `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md` (that plan's "2026-07-21 — OPTION-A MIGRATION
> SCOPED" + "RESUMPTION STATE" sections, moved verbatim below as this plan's Progress Log). The parent's own text called
> this "an EPIC, not a cheap migration" — 8 phases (P0-P8) to add `instrument_type=` to `processed_candles/` paths, keep
> SOURCE `data_type` on-path, align the manifest, and migrate the existing ~10-20M-object candle corpus backward to the
> new canonical shape. **Read `issues/candle_feature_canonical_path_divergence_2026_07_20.md` too** (the corrected
> ruling + coordinated-upgrade principle + LOCKED shape) before touching anything here — per the parent's own resumption
> note, the migration design is DECIDED, do not re-litigate it.

## Context

The writer + reader lockstep half of this epic (P1 MDPS writer single-derivation fix, P2 features-service volatility
writer fix, P3 reader dual-read lockstep across features-service/unified-trading-api, P4 deployment-api coverage check)
is **already SHIPPED** (see Progress Log below for the per-repo SHA table). What remains is the prod-data-touching half:
rebuild+verify on `-test-` (the gate before any executor), the Tier-2 spot-VM census, the migration executor build
(clone the proven `market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py` pattern), drain+snapshot
coordination with the concurrently-running `canonical-migration-cefi-wp*` raw_tick VMs (disjoint prefix, no object
collision, but manifest-shard contention), the per-AG SPOT migration apply (defi→prediction→cefi→tradfi, tradfi last),
and final verify/reconcile.

## Finish-line criteria

1. `-test-` bucket VERIFIED (via `/data-pipeline-check-mdps` force+skip+canonical legs) that the writer emits the
   canonical shape end-to-end and readers dual-read correctly — the gate before any prod-data executor.
2. Tier-2 spot-VM single-walk census run — precise per-AG object count, dup-shape inflation, and empty-stem defect rate
   (replacing the in-session ±2-3x estimate).
3. Migration executor built (idempotent, sharded, enumeration-file-driven, `--apply`-gated, PROGRESS.json checkpointed)
   implementing the full path transform + DEDUP + PURGE + QUARANTINE + manifest re-record, with crc32c (not size-only)
   pre-delete verification.
4. Drain+snapshot done, coordinated with the concurrent raw_tick canonical-migration fleet.
5. Per-AG SPOT migration applied in order defi→prediction→cefi→tradfi, target ≤2-3h runtime.
6. Verify/reconcile complete: 4-surface reconciliation + the UAC canonical-path-violations oracle extended to the
   `processed_candles/` namespace + a both-axes reader load-test (a derivative/trades 15m slice AND a tradfi 1m slice,
   so a tradfi-only test can't false-pass axis-1 of the two break-axes).

## Codex SSOTs (read + keep this plan aligned)

- `/codex/02-data/availability-manifest-and-data-status.md`, `…/honest-coverage-model.md` (4-state `capture_status`,
  shard atom, coverage formula)
- `/codex/02-data/per-asset-group-bucket-layouts.md` (candle path layout SSOT — amended 2026-07-21 to add
  `instrument_type=`; the codex, not the UTL registry template, is authoritative — see Lesson 1 below)
- `/codex/02-data/mdps-candle-canonical-reconciliation.md`
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, `…/gcs-object-operations.md` (crc32c verify before any
  prod delete; server-side copy via `gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object`, never subprocess
  `gcloud`/`gsutil`)
- `/codex/02-data/reconciliation-census-and-compute-tiers.md` (Tier-2 spot-VM single-walk sanction)
- `/codex/05-infrastructure/spot-vms-for-backfill.md`, `…/vm-launcher-runbook.md` (MDPS/features are Tardis-EXEMPT;
  `launch-canonical-migration-vm.sh` extension)

## Todos

- [x] 1. ✅ [DATA] P0. Rebuild code tarballs (`refresh_code_tarballs.sh`) for the 4 already-shipped repos
      (unified-trading-library, market-data-processing-service, features-service, unified-trading-api) so the
      canonical-shape writer/reader changes are live on VM images. (RESUME ORDER step 4a.) — deployment-service@<script
      run, no code change>. `unified-trading-library` was already up to date at LDR tip (0d3b959c2de2, includes the
      writer/reader lockstep changes). `unified-trading-api` is NOT part of the VM-tarball fleet (`REPOS` list in
      `refresh_code_tarballs.sh`) — it deploys via a different path, not VM tarballs, so N/A here. Rebuilt+uploaded:
      `market-data-processing-service-code` (sha=a35ccb71a991, confirms `mdps@752eaff` as ancestor — the shipped writer
      fix is live) and `features-service-code` (sha=568c56303d83, confirms `features@99d5554e` as ancestor — the shipped
      reader fix is live), plus 3 other stale VM tarballs (market-tick-data-service, deployment-service,
      batch-live-reconciliation-service) that the SHA-skip scan also found changed. Found + fixed a real bug along the
      way: this slot's `deployment-service` checkout had no `.venv`, so `gcs_upload_via_adc.py`'s
      `${DS_ROOT}/.venv/bin/python` fallback silently hit bare `python3` (no `deployment_service` package installed) →
      every upload failed with `ModuleNotFoundError`. Fixed via
      `uv venv .venv && UV_PROJECT_ENVIRONMENT=.venv uv sync     --frozen` in this slot's deployment-service clone (an
      environment/local-venv fix, not a code change — no commit needed). Manifest SHAs verified post-upload via
      `gcloud storage cat`.
- [x] ✅ 2. [DATA] P0. VERIFY on `-test-` via `/data-pipeline-check-mdps` (force+skip+canonical legs) that the writer
      now emits the canonical shape (`instrument_type=` present, SOURCE `data_type`, path==manifest). **THIS IS THE GATE
      before any prod-data executor** — do not start todo 5+ before this passes. (RESUME ORDER step 4b.) **RE-VERIFIED
      2026-07-27 (slot-4, this closure):** this exact gate already ran and PASSED 2026-07-21 per
      `issues/candle_feature_canonical_path_divergence_2026_07_20.md`'s Progress Log (`mdps@752eaff` writer +
      `mdps@2d720b4` manifest-source fix, real GCS object ground-truthed to the LOCKED shape). Confirmed today the
      shipped SHAs are still ancestors of LDR tip (no regression/revert since) AND re-checked the SAME `-test-` shard
      used for that original gate —
      `gs://market-data-tick-cefi-test-.../processed_candles/by_date/day=2026-06-27/     pipeline_mode=batch_tardis/timeframe=15m/data_type=trades/instrument_type=PERPETUAL/venue=DERIBIT/...parquet`
      — still carries the exact LOCKED canonical shape live. See the "BIG FINDING" Progress Log entry below: the sibling
      issue doc's Progress Log shows the ENTIRE P5-P8 migration (todos 3-15 below) also already executed + independently
      verified clean 2026-07-21→23, one day BEFORE this plan was split out 2026-07-24 carrying a stale pre-completion
      todo snapshot.
- [x] ✅ 3. [DATA] P0. **VERIFIED 2026-07-27 (slot-10)**: confirms slot-4's "BIG FINDING" below — this todo is also a
      duplicate of already-shipped, already-verified work. Direct code read (not just trusting the sibling doc) of all
      four named readers confirms every one dual-reads via the UTL `candle_read_prefixes` SSOT: features-service
      `delta_one/app/core/data_loader.py:460`, `volatility/core/data_loader.py:284/299` +
      `volatility/io/loader.py:91/105` (all import + call `candle_read_prefixes`); unified-trading-api
      `services/batch_candles.py:131` (same); MDPS `build_continuous_engine.py` — writer uses
      `build_canonical_candle_path` (canonical shape incl. `pipeline_mode=`/`instrument_type=continuous_future`, line
      ~100) and its reader dual-reads via `candle_read_prefixes` too (line ~138, comment: "dual-read for the
      migration"). This matches the sibling doc's Phase-0 ruling ("continuous_future slice → IN SCOPE... writer + reader
      move in lockstep... already canonical") and its Progress Log ("2026-07-21 — coordinated writer+reader lockstep
      landed" — `features@99d5554e`/`features@d58b7760` delta_one+volatility dual-read, `uta@8377c98` chart reader
      dual-read), independently re-confirmed by P8 cross-AG verify/reconcile (2026-07-23, all 4 AGs clean). No code
      change needed — closing as verified-via-code-read, not re-implementing.
- [ ] 4. [SCRIPT] P0. Run the sanctioned Tier-2 spot-VM single-walk census (bounded in-session sampling already
      estimated ~10-20M candle objects, tradfi-dominated, ±2-3x) to get a precise per-AG object count + dup-shape
      (`pipeline_mode=` vs naked `timeframe=`) + empty-stem inventory before sizing the migration fleet.
- [ ] 5. [SCRIPT] P0. Build the migration executor (P5): clone
      `market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py` — idempotent, sharded,
      enumeration-file-driven, `--apply`-gated, PROGRESS.json checkpointed.
- [ ] 6. [SCRIPT] P0. Implement the path transform in the executor: backward-add `instrument_type=` via
      `build_canonical_candle_path`, keep SOURCE `data_type` (no re-aggregation), tf-normalise where needed,
      `pipeline_mode=` insert where missing.
- [ ] 7. [SCRIPT] P0. Implement DEDUP in the executor for the split-brain candle layout (same object present under both
      `pipeline_mode=` AND a naked `timeframe=` prefix on cefi/tradfi/prediction, ~2x inflation).
- [ ] 8. [SCRIPT] P0. Implement PURGE of empty-stem objects (`venue={V}/.parquet` with no leaf id, ~0.6-0.8% defect
      rate) → rewrite to `ticks.parquet` per `candle_leaf_filename`, or delete if unrecoverable.
- [ ] 9. [SCRIPT] P0. Implement QUARANTINE (never guess) for unresolvable legacy TradFi `E1AF0_*_migrated_*` leaf ids
      via `_renormalize_legacy_instrument_ids` — objects that don't resolve move to quarantine, never silently dropped
      or renamed wrong.
- [ ] 10. [SCRIPT] P0. Wire manifest re-record to the SOURCE-keyed row (via `record_captured`, path-independent) into
      the executor pass so skip-if-fresh is correct post-migration (freshness now keys SOURCE; pre-migration candles
      legitimately re-process during the transition per the shipped writer's caveat).
- [ ] 11. [SCRIPT] P0. Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum before any prod
      object delete.
- [ ] 12. [DATA] P0. Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch (target
      ≤2-3h runtime: server-side copies, ~40 VMs × ~120 concurrent).
- [ ] 13. [DATA] P1. P6 drain+snapshot: coordinate with the running `canonical-migration-cefi-wp*` raw_tick VMs
      (disjoint `raw_tick_data/` vs `processed_candles/` prefix — no object collision — but manifest-shard contention +
      drain needed) before the candle migration writes; snapshot pre-migration state.
- [ ] 14. [DATA] P0. P7 per-AG SPOT migration apply, in order defi→prediction→cefi→tradfi (tradfi last — largest corpus,
      ~99% carrying the `E1AF0_*_migrated_*` artifact leaf ids needing canonicalisation).
- [ ] 15. [DATA] P0. P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle
      (currently scoped ONLY to `raw_tick_data/by_date/`) to the `processed_candles/` namespace + a both-axes reader
      load-test (a derivative/trades 15m slice AND a tradfi 1m slice — a tradfi-only test can false-pass axis-1 of the
      two break-axes per the blast-radius analysis below).
- [ ] 16. [DATA] P1. Root-cause + close the candle object↔manifest disconnect (6 degenerate MDPS manifest rows vs 20k+
      objects/day pre-migration) so skip-if-fresh can be trusted at scale post-migration — cross-check against
      `issues/candle_feature_canonical_path_divergence_2026_07_20.md` todo 7 (same finding, tracked there too; close
      both together, don't duplicate the fix).

## Progress Log

### 2026-07-27 (slot-4) — 🔴 BIG FINDING: this plan's todos 3-15 likely duplicate ALREADY-COMPLETED work

While closing todo 2 (dispatched task `candle_canonical_path_migration_execution-002`), found that
`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`'s own Progress Log documents the **entire
P5-P8 migration** (todos 5-15 below: executor build, drain+snapshot, per-AG SPOT `--apply` for all 4 asset groups,
verify/reconcile) as **already executed and independently verified clean on 2026-07-21 through 2026-07-23** — that is
BEFORE this plan (`candle_canonical_path_migration_execution_2026_07_24.md`) was split out on 2026-07-24. The split
appears to have carried forward a **stale pre-completion snapshot** of the todo list rather than the post-completion
state.

**Evidence gathered this session** (2026-07-27, read-only, no VM launches, no prod writes):

- `mdps@752eaff` (writer single-derivation), `mdps@2d720b4` (manifest source-key fix), `mdps@6ce1a25` (P5 migration
  executor) all verified as real commits, ancestors of current LDR tip — nothing reverted since.
- Live `gcloud storage ls -r` on the SAME `-test-` shard the original 2026-07-21 gate used
  (`market-data-tick-cefi-test-.../processed_candles/by_date/day=2026-06-27/pipeline_mode=batch_tardis/timeframe=15m/ data_type=trades/instrument_type=PERPETUAL/venue=DERIBIT/`)
  confirms the LOCKED canonical shape is still live today.
- Live spot-check of PROD `processed_candles/by_date/` on a recent day for **all 4 asset groups** (cefi
  `day=2026-07-21`, defi `day=2026-07-26`, tradfi `day=2026-07-22`, prediction `day=2026-01-14`) confirms EVERY one
  carries the canonical `pipeline_mode=/timeframe=/data_type=/instrument_type=/venue=` shape in PROD right now —
  corroborating the sibling doc's "P7 per-AG SPOT migration apply, ALL 4 asset groups COMPLETE" claim (defi 1,131,814
  objects, prediction 1,165,459, cefi 940,606, tradfi 7,646,831 — per that doc's 2026-07-22/23 entries).

**Recommendation (NOT unilaterally actioned — outside this session's assigned scope of todo 2 only):** before AO
dispatches todos 4-15 to another slot (each of which would launch a real VM fleet — todo 12/14 alone spec "~40 VMs ×
~120 concurrent"), main/operator should reconcile this plan against
`issues/candle_feature_canonical_path_divergence_2026_07_20.md`'s Progress Log and flip/close the ones that duplicate
already-completed work. Leaving them open risks a slot agent actually re-launching a ~40-VM SPOT migration fleet against
an already-migrated corpus — safe (idempotent) but a real, avoidable cost + multi-hour waste. Genuinely open residual
items from the sibling doc (TRADFI's ~7.1M quarantined objects = its todo 3; CEFI's 149-object residual = its todo 19)
are NOT duplicated by this plan's todo list and should stay tracked wherever they already are.

---

> Everything below this line was moved **verbatim** from `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md`
> (its "2026-07-21 — OPTION-A MIGRATION SCOPED" and "RESUMPTION STATE 2026-07-21" sections) on 2026-07-24, as part of
> the plan line-cap remediation split. No content was summarized or rewritten — only the Todos section above and this
> header are new.

### 2026-07-21 — OPTION-A MIGRATION SCOPED (workflow wvyttno6s, 5 agents) — it is an 8-phase EPIC, not a cheap migration

**Scale CORRECTION (material):** the original issue said "cefi 6 rows → cheap" — that was the MANIFEST count. The
workflow's bounded sampling found the OBJECT corpus is **~10-20M candle objects** (order 10^7), tradfi-dominated: tradfi
~10^7 (~99% carry `E1AF0_*_migrated_*` artifact leaf ids needing canonicalisation), cefi ~10^6, defi ~10^5-10^6,
**prediction ~10^5 (an EXTRA in-scope AG)**; ~2x DUP-SHAPE inflation (same object under `pipeline_mode=` AND naked
`timeframe=` on cefi/tradfi/pred → dedup required); empty-stem defect ~0.6-0.8%. Precise count needs the sanctioned
**Tier-2 spot-VM single-walk** (in-session est. ±2-3x).

**Blast radius (5+ repos, silent-miss is the hazard — empty frames, NO errors):** WILL-BREAK — features-service
delta_one `data_loader.py:552-635` (hardcodes "dropped instrument_type 2026-04") + volatility
`data_loader.py`/`io/loader.py`, unified-trading-api `batch_candles.py` (charts/UI go blind), UTL
`domain_client/market_data.py:142-169` (legacy client), MDPS `build_continuous_engine.py:52` (continuous-future input).
UNCERTAIN — deployment-api coverage scan. SAFE — ml/strategy/batch-recon (don't read candles by path). Two break-axes:
(1) `instrument_type=` insert breaks EVERY flat reader; (2) source→aggregated data_type breaks derivative/trades/dex
slices (tradfi base ohlcv passes through → axis-1 only → **false-pass risk if a reviewer tests only a tradfi-1m
slice**).

**Path transform (well-defined):** source→aggregated via `mdps_data_type_key`, tf-normalise (24h→1d), `instrument_type`
via `_infer_instrument_type`, `pipeline_mode=` insert; defect folds — TradFi ids via
`_renormalize_legacy_instrument_ids` (UNRESOLVABLE → QUARANTINE, never guessed), empty-stem → `ticks.parquet`.
**Tooling: REUSE** `gcs_copy/delete/describe`, CLONE the proven executor
`market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py` (idempotent, sharded, enumeration-file-driven,
--apply-gated), `record_captured` (path-independent) for manifest population, extend `launch-canonical-migration-vm.sh`.
Upgrade verify SIZE→crc32c before any prod delete.

**8 phases:** P0 (2 human-gated decisions + census) → P1 writer single-derivation fix (MDPS) → P2 volatility writer
defect (features, independent — DOING NOW) → P3 reader lockstep (5+ repos) → P4 deployment-api coverage → P5 migration
tooling (clone) → P6 drain+snapshot → P7 per-AG SPOT migration (defi→pred→cefi→tradfi, tradfi last) → P8
verify/reconcile.

**GATING (Phase 0, operator):** (a) `pipeline_mode=` placement — the registry template `registry.py:28` has
`instrument_type=` but NO `pipeline_mode=` (injected post-hoc by `config.py:144-145`); add to the
template+partition_keys OR keep the post-hoc insert. (b) continuous_future slice IN or OUT of scope (already carries
`instrument_type=continuous_future`). Both gate the writer + all readers + the migration path-builder. Bringing these to
the operator now; starting P2 (safe, independent) in parallel.

---

## ⚠️ RESUMPTION STATE 2026-07-21 (pre-compact) — coordinated candle-canonical migration MID-FLIGHT

**A fresh session: READ THIS + `candle_feature_canonical_path_divergence_2026_07_20.md` (the corrected ruling +
coordinated-upgrade principle + LOCKED shape). Do NOT restart the migration design — it is decided.**

### LOCKED canonical candle shape (operator-ruled 2026-07-21, corrected against the codex — see the LESSON below)

`processed_candles/by_date/day={date}/pipeline_mode={pm}/timeframe={tf}/data_type={SOURCE}/instrument_type={it}/venue={v}/{canonical_id}.parquet`

- ADD `instrument_type=` (operator wants it → amend codex `per-asset-group-bucket-layouts.md:166`). KEEP **SOURCE**
  `data_type` on the path (derivative_ticker/trades/…, NOT aggregated deriv_ohlcv). Align the MANIFEST to record the
  SOURCE key (path==manifest). Upgrade codex+docs+manifest+code+data TOGETHER and migrate the WHOLE corpus BACKWARD.

### UNCOMMITTED working-tree state — a coordinated BREAKING change HELD for ATOMIC landing (do NOT commit piecemeal — UTL alone KeyErrors MDPS)

| Repo                           | Files                                                                                                                                                                                                                                                                                                                                                                                              | Status                                                                                                                            | What                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| unified-trading-library        | registry.py, config_interface/paths/**init**.py, config_interface/**init**.py, **init**.py, domain_client/clients/market_data.py, tests/config_interface/unit/test_paths_registry_smoke.py                                                                                                                                                                                                         | ✅ SHIPPED (staging-first landing 2026-07-21)                                                                                     | registry template + `pipeline_mode=`; new `build_canonical_candle_path` + `candle_read_prefixes` (dual-read); MarketCandleDomainClient passes pipeline_mode                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| unified-trading-api            | services/batch_candles.py, tests/unit/test_batch_candles.py                                                                                                                                                                                                                                                                                                                                        | ✅ SHIPPED uta@8377c98                                                                                                            | charts reader dual-read via candle_read_prefixes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| features-service               | volatility/core/feature_writer.py, tests/volatility/unit/test_feature_writer.py                                                                                                                                                                                                                                                                                                                    | ✅ SHIPPED features@99d5554e                                                                                                      | P2 volatility prefix fix (volatility/by_date/)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| features-service               | delta_one/app/core/{data_loader,dependency_checker}.py, volatility/core/data_loader.py, volatility/io/loader.py + tests                                                                                                                                                                                                                                                                            | ✅ **SHIPPED features@99d5554e** (dirty-deps carve-out)                                                                           | delta_one+volatility readers dual-read via `candle_read_prefixes` (canonical instrument_type= first, legacy flat fallback, SOURCE data_type); dependency_checker drops delimiter=/ to walk subtree; continuous_future intact. QG-red ONLY on untracked peer WIP `cross_instrument/app/calculators/adv.py` (NOT mine) — land my files via carve-out. NOTE: instrument_type token divergence (GCS_PATHS plural vs UTL/reader singular-lowercase) — reader probes both; reconcile the vocabulary during -test- verify.                                                                                                                                                                                                                                                                                                                            |
| market-data-processing-service | app/core/{candle_write_mixin,canonical_writer,canonical_writer_shaping,canonical_writer_streaming,canonical_writer_manifest,data_sink,live_workers_streaming,output_path_helpers,build_continuous_engine}.py, cli/handlers/build_continuous_handler.py, io/writer.py, config.py, docs/GCS_PATHS.md + tests + codex `per-asset-group-bucket-layouts.md` & `mdps-candle-canonical-reconciliation.md` | ✅ **SHIPPED mdps@752eaff** (dirty-deps carve-out; also closed the continuous-engine reader gap + a broken bucket-resolution bug) | writer single-derivation via new `build_canonical_candle_object_path`/`derive_candle_object_path` (adds instrument_type + SOURCE data_type + pipeline_mode; caller gcs_path now advisory); manifest `data_type` axis = SOURCE (via `manifest_row_key` override; aggregated kwarg kept for schema-contract/cluster gate) in eager+streaming; empty-stem → `ticks.parquet` (`candle_leaf_filename`); config.get_processed_path pipeline_mode KeyError fixed; codex :166 amended to SOURCE+instrument_type+pipeline_mode. **CAVEAT for the backward executor**: going-forward manifest is SOURCE-keyed but existing rows stay aggregated until the backward migration re-keys them; freshness now keys SOURCE → pre-migration candles RE-PROCESS during the transition (safe, not wrong) — the backward manifest re-record to SOURCE resolves it. |
| deployment-api                 | —                                                                                                                                                                                                                                                                                                                                                                                                  | ✅ NO CHANGE NEEDED (verified)                                                                                                    | coverage is a coarse prefix-existence probe stopping at data_type=, transparent to the instrument_type= insert                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

**PEER WIP (NOT mine, do NOT stage):** features-service calendar_orchestrator.py + onchain/*; unified-trading-pm codex
data-lineage/manifest-consolidator + aster/sports/tarball issue docs + untracked plan files. Stage ONLY the files listed
above, BY NAME.

### RESUME ORDER (the going-forward code half — NO prod object is touched by any of this)

> **Steps 1-3 DONE 2026-07-21** — see `issues/candle_feature_canonical_path_divergence_2026_07_20.md` Progress Log for
> full detail + evidence. Summary: the ONE gap (continuous-engine reader) closed + a bonus broken-bucket-resolution bug
> fixed; all 4 repos QG-green; landed dep-ordered (UTL staging-first, MDPS/features/uta via the dirty-deps carve-out —
> UAC had live peer WIP throughout). Shas: `mdps@752eaff`, `features@99d5554e`, `uta@8377c98`. **Resume at step 4**
> (rebuild tarballs + verify on `-test-`) — this is the gate before the P5 executor.

1. ~~Read agent outputs...~~ DONE — both agents' output landed; the continuous-engine gap closed in the same pass.
2. QG each repo green (`bash scripts/quality-gates.sh --no-fix`).
3. Land dep-ordered: UTL first (dirty-deps carve-out likely — UAC peer WIP), then MDPS, then features + uta. features
   quickmerge is blocked by whole-program peer WIP — use the carve-out with QG-green verified.
4. Rebuild tarballs (`refresh_code_tarballs.sh`), then VERIFY on `-test-` via `/data-pipeline-check-mdps` (force+skip+
   canonical) — confirm the writer emits the canonical shape (instrument_type= present, source data_type,
   path==manifest) AND readers dual-read. THIS IS THE GATE before any prod-data executor.
5. THEN build the executor (P5, clone `market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py`): backward
   add instrument_type= via `build_canonical_candle_path`, DEDUP split-brain (pipeline_mode= vs naked timeframe=), PURGE
   empty-stem `/.parquet`, QUARANTINE unresolvable TradFi `E1AF0_*_migrated_*` ids, re-record manifest to SOURCE;
   copy→crc32c-verify→delete, idempotent, sharded, --apply-gated, PROGRESS.json.
6. P0 census (bounded/Tier-2), P6 drain+snapshot (coordinate with the 23-24 running `canonical-migration-cefi-wp*`
   raw_tick VMs — DISJOINT prefix so no object collision, but manifest-shard contention + drain), P7 per-AG SPOT apply
   `defi→prediction→cefi→tradfi` (target ≤2-3h runtime: server-side copies, ~40 VMs × ~120 concurrent), P8
   verify/reconcile (4-surface + oracle + BOTH-axes reader load: a derivative/trades 15m slice AND a tradfi 1m slice).

### 🔑 LESSONS (would be re-learned the hard way)

1. **CHECK THE CODEX LAYOUT SSOT, not just the UTL registry template.** My original Option-A framing treated
   `registry.py`'s `processed_candles` template (which HAS instrument_type=) as the SSOT. The AUTHORITATIVE codex
   `per-asset-group-bucket-layouts.md:166` says cefi/tradfi/defi candles have NO instrument_type= — the objects matched
   the codex, the registry template was the drift. Option A as first framed CONTRADICTED the codex. The operator
   re-decided WITH the correction (deliberately amend the codex to add instrument_type=). A whole ~10-20M-object
   migration was almost run in the wrong-premise direction. Always ground a "canonical" claim in the codex layout doc.
2. **The candle-path migration is NOT duplicative** — the 23-24 running `canonical-migration-cefi-wp*` VMs migrate
   `raw_tick_data/` (instrument_id COLUMN patching via `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`
   PREFIX=raw_tick_data/by_date), NOT `processed_candles/`. No plan/VM/todo touches candle PATHS. Confirmed by workflow
   wq44d6bto + A3 ground-truth (instrument_type= count = 0 across all 4 AGs). Coordinate but do not collide.
3. **The aggregated key `deriv_ohlcv` exists NOWHERE** in codex/plans (only defi `swaps_ohlcv`). That's why the operator
   ruled KEEP SOURCE data_type on the path (align manifest to source) rather than migrate to an aggregated key.
4. **The derivative_ticker P0 root cause was the MDPS pre-upload validator gating OHLC-nullability on CATEGORY** (not a
   UAC key mismatch — my first hypothesis, corrected by workflow w6kkdobay). Fixed mdps@d4052e20b; proven 0→140 objects.
5. **Skill "failed" verdict on a successful write was a stale-consolidated-read** (driver read the merged index not the
   leg VM's per-VM shard) — fixed utl@69ff7fee + mdps@8890508.

### Scratchpad = deliberate DROP (all regenerable): verify_*.py, _.log, tradfi__.txt samples, uac_code.tar.gz,

DESIGN_mdps_features_skills.md (skills shipped; key facts already journaled above). Nothing here is needed to resume.
