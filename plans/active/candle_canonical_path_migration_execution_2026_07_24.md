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
- [x] ✅ 4. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-4)**: another duplicate of already-shipped work, confirming
      slot-4's "BIG FINDING" below yet again (3 of the first 3 dispatched todos on this plan so far — 2, 3, 4 — have all
      been already-completed duplicates). The P0 census ran to completion **2026-07-22** per
      `plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md`'s Progress Log — 4
      parallel SPOT VMs (`{cefi,defi,tradfi,prediction}-candle-census`), real GCS enumeration (not inferred),
      `exit_code=0` on every VM, `ORPHAN=0` on every asset group (the executor's own hard safety invariant — every
      enumerated object got exactly one disposition or the run aborts loudly):

      | Asset group    |  Total objects |   MIGRATE | SPLIT_BRAIN_DUPLICATE | QUARANTINE_CORRUPT | EMPTY_STEM (w/wo underlying) | NEEDS_CONTENT_ITYPE | NEEDS_CONTENT_TRADFI_ID | CANONICAL_NOOP | ORPHAN |
                                                      | -------------- | -------------: | --------: | ---------------------: | ------------------: | ---------------------------: | -------------------: | ----------------------: | --------------: | -----: |
                                                      | defi           |      1,124,849 | 1,123,407 |         (folded into MIGRATE) |               1,442 |                        0 / 0 |                    0 |                       0 |               0 |      0 |
                                                      | prediction     |      1,165,459 |         1 |              1,165,458 |                   0 |                        0 / 0 |                    0 |                       0 |               0 |      0 |
                                                      | cefi           |        940,606 |        10 |                804,670 |             130,906 |                2,576 / 2,198 |                  238 |                       0 |               8 |      0 |
                                                      | tradfi         |      7,646,831 |         0 |                724,214 |                   0 |              428,792 / 6,780 |                    0 |               6,487,045 |               0 |      0 |
                                                      | **TOTAL**      | **10,877,745** |         — |                      — |                   — |                            — |                    — |                       — |               — |      0 |

                                                      Evidence: each VM's `run.log` at
                                                      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-{cat}-candle-census-<ts>/run.log` +
                                                      staged mapping TSVs at
                                                      `gs://deployment-scripts-central-element-323112/canonical-migration-candle-census/<ts>/canonical-migration-{cat}-candle-census-<ts>/mappings/`.
                                                      This satisfies the todo's own ask exactly: precise per-AG object count (replacing the ±2-3x in-session estimate),
                                                      dup-shape breakdown (`pipeline_mode=` vs naked `timeframe=` split-brain counts per AG), and empty-stem inventory
                                                      (with/without `underlying=`) — all measured, not estimated. No re-run needed; re-launching 4 more Tier-2 census
                                                      VMs against an unchanged corpus would be pure duplicate cost. Follow-up findings from that census (cefi's
                                                      anomalous 13.9% QUARANTINE_CORRUPT rate, the unregistered `pipeline_mode=batch_hyperliquid_rest` value) were
                                                      filed as that doc's own todos 17/18 — not re-filed here.

- [x] ✅ 5. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-10)**: another duplicate of already-shipped work (5 of the first 5
      dispatched todos on this plan — 2,3,4,5 — now all confirmed already-completed; only todo 1, the tarball rebuild,
      was genuinely new work). `market-data-processing-service@6ce1a25` ("feat(migration): P5 candle-canonical backward
      migration executor (dry-run default, --apply gated)") shipped `scripts/migrate_candle_canonical_2026_07.py` (1033
      lines) + `tests/.../test_migrate_candle_canonical_2026_07.py` (469 lines), confirmed still an ancestor of current
      LDR tip (`git merge-base --is-ancestor 6ce1a25 HEAD`). Direct read of the shipped file confirms every property
      this todo asks for: dry-run default / `--apply`-gated destructive path; idempotent copy→verify→delete (skip-copy
      if target already verified-present, safe for concurrent/retried runs); sharded (`--shard-of`/ `--shard-index`,
      applied only to the classify pass + `--apply`'s execution loop, never to index construction — documented as
      load-bearing, not an oversight); enumeration-file-driven (`--enumeration <file>`, a physical pre-listed object
      file, never a live re-walk); its own content-hashed checkpoint mechanism for VM resume
      (`enumeration_signature`-fingerprinted, explicitly distinct from — but functionally equivalent to — the
      workspace's generic day-frontier `PROGRESS.json`). Matches the sibling doc's Progress Log ("P5 migration executor
      shipped `mdps@6ce1a25`, 951 lines + 23 tests — a 3-lens adversarial review caught a CRITICAL pre-prod bug...
      before any real object was touched"). No code change needed.
- [x] ✅ 6. **VERIFIED 2026-07-27 (slot-4)**: another duplicate of already-shipped work (6 of the first 6 dispatched
      todos on this plan — 2,3,4,5,6 — now all confirmed already-completed; only todo 1 was genuinely new). Direct read
      of `market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` (shipped `mdps@6ce1a25`, confirmed
      ancestor of LDR tip) confirms the exact transform this todo asks for is already implemented: its docstring states
      the LOCKED canonical shape
      (`.../pipeline_mode={pm}/timeframe={tf}/data_type={SOURCE}/     instrument_type={it}/venue={v}/...`) and that the
      migration "ADDS a missing `instrument_type=` segment, ADDS/normalises a missing `pipeline_mode=` segment (default
      `BATCH_DATABENTO` when absent, matching the writer's own `resolve_pipeline_mode_from_source` convention)... NEVER
      rewrites `data_type`" (i.e. SOURCE `data_type` kept, no re-aggregation) — reusing `_infer_instrument_type`,
      `_renormalize_legacy_instrument_ids`, `_normalise_timeframe` (tf-normalise), `resolve_pipeline_mode_from_source`
      VERBATIM from the writer's own `canonical_writer_shaping` module (not re-implemented by hand, per the migration
      design's explicit instruction). This is the exact same executor already independently verified in todo 5. No code
      change needed.
- [x] ✅ 7. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-9)**: another duplicate of already-shipped work (7 of the first 7
      dispatched todos on this plan — 2,3,4,5,6,7 — now all confirmed already-completed; only todo 1, the tarball
      rebuild, was genuinely new work). Direct read of
      `market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` (current LDR tip, HEAD `0b513c0`; the
      executor's own commits `mdps@6ce1a25`/`efa559a`/`6b9ee49` all confirmed ancestors via
      `git merge-base --is-ancestor`) confirms DEDUP for the split-brain layout is already fully implemented, not
      partially: `classify_object()` (`migrate_candle_canonical_2026_07.py:661-667`) detects the split via a corpus-wide
      provisional-target index — `target_index.count(res.target_rel) > 1` → disposition `D_SPLIT_BRAIN_DUPLICATE` — and
      BOTH twins (the `pipeline_mode=`-carrying object and its naked-`timeframe=` sibling) run through the SAME
      idempotent `A_COPY` action (line 985: "A_COPY — MIGRATE / SPLIT_BRAIN_DUPLICATE: copy -> verify(size/crc32c) ->
      delete src. Idempotent."): whichever twin's copy lands first creates the canonical target; the second twin's copy
      sees the target already verified-present (skip-copy), then verifies + deletes its own source — so no artificial
      "primary election" is needed, both converge to ONE canonical object. The module docstring's defect #3 documents
      this exact design (verbatim: "detected GENERICALLY over every axis via a provisional-target index, not
      hand-restricted to the pipeline_mode axis alone"). Critically, the target-index + a dedicated
      `PipelineModeSiblingIndex` (pm_index) are BOTH built over the FULL, UNSHARDED enumeration in passes -1/3 and 0/3
      (never per-shard) specifically so a `--shard-of N` run can't miss a cross-shard sibling and silently fail to
      converge — a subtlety the file's own comments call out as the exact failure mode this design avoids. No code
      change needed; this todo's ask (DEDUP for the pipeline_mode= vs naked timeframe= split-brain shape) is the
      executor's core, already-battle-tested feature. Cross-referenced against
      `issues/candle_canonical_path_migration_execution_stale_todos_2026_07_27.md`, which already flags this whole
      plan's todos 3-15 as likely-duplicate; this closes todo 7 specifically with direct code-level confirmation (not
      just trusting the sibling doc's narrative).
- [x] ✅ 8. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-7)**: another duplicate of already-shipped work. Direct read of
      `market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` (current LDR tip) confirms empty-stem
      handling is fully implemented as TWO distinct dispositions: `D_EMPTY_STEM_WITH_UNDERLYING` (line 640) repairs to
      `CHAIN_BUNDLE_FILENAME = "ticks.parquet"` (line 222) under the SAME `underlying=` partition; genuinely
      unattributable stems with no `underlying=` to repair against (`D_EMPTY_STEM_WITHOUT_UNDERLYING`, line 612) route
      to QUARANTINE (line 615: `"<QUARANTINE: zero-length instrument stem, no underlying= to attribute to>"`) —
      quarantine rather than this todo's literal "or delete" wording, consistent with the executor's own
      never-delete-only-quarantine safety invariant (safer, not a gap). Test coverage:
      `test_empty_stem_without_underlying_is_unattributable_quarantine`
      (`tests/unit/scripts/test_migrate_candle_canonical_2026_07.py:332`). No code change needed.
- [x] ✅ 9. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-7)**: another duplicate of already-shipped work. Direct read of
      `market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` (current LDR tip) confirms the module
      docstring's defect #2 (lines 46-48) states verbatim: "TradFi non-canonical leaf ids
      (`E1AF0_C3200_migrated_20260418T131054Z.parquet`) — resolved via content read +
      `_renormalize_legacy_instrument_ids` in `--apply`... unresolvable → QUARANTINE (never fake-canonicalize, never
      guess)" — this todo's exact ask, word for word. `_content_resolve_tradfi_leaf_id` (line 839) calls
      `_renormalize_legacy_instrument_ids` (imported verbatim from the writer's own `canonical_writer_shaping` module,
      never re-implemented) and returns `("", "")` on unresolvable; the apply-path (lines 886-931) routes that through
      `_copy_verify_delete(uri, quarantine_uri, success_label="CONTENT_REPAIR_UNRESOLVED_QUARANTINED")` — objects that
      don't resolve genuinely move to `_quarantine/`, never silently dropped or renamed wrong. Test coverage:
      `test_non_canonical_tradfi_leaf_id_needs_content_repair` +
      `test_tradfi_leaf_id_repair_stays_tradfi_disposition_not_cefi`
      (`tests/unit/scripts/test_migrate_candle_canonical_2026_07.py:340,357`). Cross-referenced against
      `issues/candle_canonical_path_migration_execution_stale_todos_2026_07_27.md` (already flags todos 3-15 as
      likely-duplicate) — this closes todo 9 specifically with direct code-level confirmation, same pattern as todos
      2-8. No code change needed.
- [x] ✅ 10. [SCRIPT] P0. **SHIPPED 2026-07-27 (slot-7)**: unlike todos 2-9/11 (all already-completed duplicates —
      confirmed via direct code read that the executor's manifest surface was ZERO before this change: the sibling issue
      doc's own cross-AG confirmation states verbatim "the migration script itself contains ZERO manifest-writing code,
      only its own internal tracking TSV" — this todo was genuinely open). `market-data-processing-service@800f3b5` adds
      `_record_captured_for_target()`, wired into `_copy_verify_delete` (via a new `record_manifest_asset_group` kwarg,
      called from `_apply_one`'s A_COPY branch + `_apply_content_repair`'s final migrate) and into `_apply_one`'s
      A_VERIFY_ONLY branch (already-canonical-in-place objects) — every successful migrate/content-repair-migrate/
      verify-in-place/idempotent-already-migrated outcome now calls `ManifestWriter.record_captured` at the SOURCE-keyed
      shard coordinate (`data_type=parsed.data_type`, the SOURCE axis per the LOCKED canonical shape) with `source=`
      derived from `source_string_for(pipeline_mode)` (UAC, no guessing). Uses a `validate=False` bookkeeping df
      (`pd.DataFrame()`, `row_count=0`) — same pattern as the precedent `manifest_swap_2026_07_22.py`'s
      `_row_count_only_df`: re-reading ~11M objects' content here purely to satisfy the 4-pillar content gate would be
      prohibitively expensive at this corpus's scale, and `check_shard_freshness` (the sole skip-if-fresh consumer,
      `unified_trading_library/manifest_writer/_queries.py`) keys off shard presence + `capture_status`/`written_at`,
      never `row_count`, so the placeholder is sufficient for the todo's stated goal. QUARANTINE outcomes are
      deliberately excluded (not a valid candle shard coordinate). Per-object isolation preserved — a manifest re-record
      failure logs + continues, never aborts the migration or changes the returned outcome string (so existing
      checkpoint-safety classification is unaffected). Reuses `ManifestWriter`/`PipelineMode`/ `source_string_for`
      verbatim (never re-implemented) and MDPS's own `_flush_manifest_with_backoff` (429-retry, already proven at
      candle-write scale). `bash scripts/quality-gates.sh` green; shipped via quickmerge.
- [x] ✅ 11. [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-12)**: another duplicate of already-shipped work (8th of 9
      dispatched todos on this plan confirmed stale — see
      `issues/candle_canonical_path_migration_execution_stale_todos_2026_07_27.md`). Direct read of
      `market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py:794-831` (`_copy_verify_delete`) shows
      the crc32c upgrade already implemented from the executor's ORIGINAL commit `mdps@6ce1a25` (2026-07-21, "P5
      candle-canonical backward migration executor") — not a later patch. The function checks `smeta.size != dmeta.size`
      (`SIZE_MISMATCH_KEPT_SRC`, no delete) THEN requires crc32c on BOTH sides (`CRC32C_MISSING_KEPT_SRC` if either is
      absent, no delete) THEN compares `smeta.crc32c != dmeta.crc32c` (`CRC32C_MISMATCH_KEPT_SRC`, no delete) —
      `gcs_delete_object(src_uri)` is the LAST line, reachable only after size AND crc32c both match. The docstring says
      so explicitly: "verify SIZE->crc32c before any prod delete" is already the built contract, not the gap. All 4
      crc32c-path outcomes (`SIZE_MISMATCH_KEPT_SRC`/`CRC32C_MISSING_KEPT_SRC`/`CRC32C_MISMATCH_KEPT_SRC` +
      checkpoint-safety) are already covered by `tests/unit/scripts/test_migrate_candle_canonical_2026_07.py:995-1009`
      (`test_outcome_is_checkpoint_safe_rejects_every_failure_and_anomaly_outcome`). No code change needed.
- [x] ✅ 12. [DATA] P0. **VERIFIED 2026-07-27 (slot-3, corroborated independently by slot-10)**: another duplicate of
      already-shipped work (9th of 9 dispatched todos on this plan now confirmed stale — see
      `issues/candle_canonical_path_migration_execution_stale_todos_2026_07_27.md`, which explicitly names this todo).
      Direct code read of `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (current LDR tip `d805e2d`)
      confirms the `<ag>-candle-apply` category is fully wired for all 4 asset groups
      (`cefi-candle-apply|defi-candle-apply|tradfi-candle-apply|prediction-candle-apply` in the usage string; dry/full
      modes, `SHARD_OF`/`SHARD_INDEX` fan-out, per-AG bucket wiring via the existing `canonical-migration-<ag>-`
      `VM_PREFIX_TO_BUCKET` prefix, the shard-name-length fix, `_candle_apply_cmd()`) — shipped
      `deployment-service@3af1a67` ("feat(vm): add candle-apply category (P7 real --apply migration+purge); fix DRY_RUN
      and shard-name-length bugs") **2026-07-22, two days before this todo was even written (2026-07-24)**, confirmed
      still an ancestor of current LDR tip (`git merge-base --is-ancestor 3af1a67 HEAD`). Independently re-verified LIVE
      (not just trusting the sibling doc's narrative): `gcloud storage ls` against PROD `processed_candles/by_date/` for
      all 4 asset groups on their most recent day (cefi `day=2026-07-21`, defi `day=2026-07-26`, tradfi
      `day=2026-07-22`, prediction `day=2026-01-14`) confirms every one already carries the full LOCKED canonical shape
      (`pipeline_mode=.../timeframe=.../data_type=.../instrument_type=...`) right now — corroborating
      `candle_feature_canonical_path_divergence_2026_07_20.md`'s Progress Log ("P7 full per-AG `--apply` sequence, all 4
      asset groups" complete 2026-07-22/23). No code change needed; extending an already-extended launcher would be pure
      duplicate cost, and launching a fresh fleet against this already-migrated corpus is exactly the wasteful/risky
      action the stale-todos issue doc warns against — NOT done.
- [x] 13. [DATA] P1. **VERIFIED 2026-07-27 (slot-10)**: 10th duplicate on this plan — the sibling doc
      `candle_feature_canonical_path_divergence_2026_07_20.md`'s Progress Log ("2026-07-22/23 P6 drain → P7 per-AG SPOT
      `--apply`...") + its "P6 drain + P7 apply started: DEFI's 200-object `--apply` canary succeeded and was
      hard-verified on real GCS" entry confirm the drain+snapshot already happened as part of the already-executed
      P6→P7→P8 sequence. No action needed here.
- [x] 14. [DATA] P0. **VERIFIED 2026-07-27 (slot-10) — the exact re-launch risk
      `issues/candle_canonical_path_migration_execution_stale_todos_2026_07_27.md` named for THIS todo.** Same evidence
      chain as todos 12/13: the sibling doc's Progress Log ("2026-07-22/23 — P7 full per-AG `--apply` sequence, all 4
      asset groups") gives per-AG object counts — DEFI 1,131,814 (1 straggler retry, 0 outstanding), PREDICTION
      1,165,459 (clean first pass), CEFI 940,606 (survived 2 SPOT-preemption bursts, 149-object 0.0158% permanent
      residual tracked as that doc's own todo 19), TRADFI 7,646,831 (survived 3 SPOT-preemption storms, 0 outstanding) —
      and slot-3's independent 2026-07-27 live `gcloud storage ls` re-check (todo 12's closure, same commit) confirms
      `processed_candles/by_date/` for all 4 asset groups carries the canonical shape TODAY, not just at apply-time.
      Launching a fresh ~40-VM per-AG SPOT fleet against this already-migrated corpus would be the exact wasteful/risky
      duplicate the issue doc warns against. No VM launch performed. TradFi's residual `E1AF0_*` artifact ids are the
      SEPARATE, still-genuinely-open `NEEDS_CONTENT_TRADFI_ID`/quarantine population tracked in the sibling doc's own
      todo 3 — not re-opened here.
- [x] 15. [DATA] P0. **VERIFIED 2026-07-27 (slot-10)**: same evidence chain — sibling doc's "2026-07-23 — P8 cross-AG
      verify/reconcile: all 4 AGs independently confirmed CLEAN" (4 parallel agents, fresh GCS enumeration + `--dry-run`
      classifier, `ORPHAN=0` and `sum(dispositions)==total` on every AG). No code change needed here; any residual
      oracle-scope-extension work (`canonical_path_violations()` → `processed_candles/`) is tracked in that sibling doc
      directly, not duplicated as a fresh todo on this plan.
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
