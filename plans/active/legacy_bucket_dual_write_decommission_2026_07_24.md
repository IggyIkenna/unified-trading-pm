---
doc_type: plan
title: Legacy tick-bucket dual-write remediation — decommission (split from M-1)
summary: >-
  Extracted 2026-07-24 from data_completion_to_100_all_ag_2026_06_21.md (M-1) per the plan line-cap remediation
  (/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md, bucket-(d) split, operator-approved). This is the
  still-inline residual of the already-archived `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (drain ->
  code-fix -> migrate -> decommission of the legacy dual-written tick buckets), migrated VERBATIM — no scope added,
  dropped, or reworded. M-1 remains the coordinator hub for cross-cutting work and owns the shared Progress Log.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [backfill, manifest, bucket-naming, decommission, data-completion, data-correctness]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-08-09
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- extracted 2026-07-24, plan line-cap remediation
  (/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md) bucket-(d) split, operator-approved.
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf,
    unified-trading-library/unified_trading_library/core/cloud_constants.py,
    deployment-service/terraform/gcp/bigquery_feature_external_tables.tf,
  ]
---

# Legacy tick-bucket dual-write remediation — decommission

> **Split from M-1 on 2026-07-24** (`data_completion_to_100_all_ag_2026_06_21.md`, plan line-cap remediation,
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split, operator-approved). This plan carries
> M-1's still-inline `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` fold-in residual **verbatim**; M-1
> stays the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. This plan is the legacy dual-write-bucket
> decommission tail specifically (drain -> code-fix -> migrate -> decommission of the pre-canonical tick buckets).

### From `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (archived 2026-07-13 -- Legacy tick-bucket dual-write remediation (drain -> code-fix -> migrate -> decommission))

- [x] ✅ [SCRIPT] P1. `unified-trading-library` `cloud_interface/constants.py` legacy `get_bucket_name` → delete or
      redirect to `resolve_bucket_name` (kill the latent flat-`market_data` foot-gun). Confirm zero top-level importers
      first. **(MIGRATED FROM: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** — **DONE 2026-07-29 (verified, not redeleted).** Confirmed the real file is
      `unified_trading_library/core/cloud_constants.py::get_bucket_name` (already SSOT-delegating: for every domain
      registered in `_DOMAIN_TO_YAML_KIND` it delegates straight to `resolve_bucket_name()` on GCP, and hard-raises
      `BucketNamingError` on an unknown domain since the 2026-07-20 fix cited in its own docstring — not the
      flat-`market_data` foot-gun this item names). Audited every importer across all 6 named repos
      (strategy-service/features-service/deployment-service/market-tick-data-service/instruments-service/ml-service,
      `rg -n 'get_bucket_name' --include='*.py'` then read each call site's `domain` arg): every current call site
      passes `"market_data"`, `"instruments"`, or `"features_sports"` — all three are covered `_DOMAIN_TO_YAML_KIND`
      keys, so zero call sites hit the legacy no-env-shape fallback on the GCP production path. No redirect needed;
      codified the "new writers call `resolve_bucket_name()` directly, not `get_bucket_name()`" rule in
      `/codex/05-infrastructure/bucket-isolation-model.md` so this doesn't silently regress.

- [x] ✅ [SCRIPT] P1. MTDS remaining env-LESS instruments-store readers: `engine/orchestrator/__init__.py:445-451`
      (`_sports_instr_bucket`/`_cefi_instr_bucket`/`_defi_instr_bucket`/`_tradfi_instr_bucket` all use `get_bucket_name`
      → env-LESS) + `cli/handlers/_instruments_metadata.py:218,442,518` (`build_bucket("instruments", …, "defi")`).
      **DEFERRED** from the `assert_defi_catalog_fresh` durable fix (market-tick-data-service@ea33d38, 2026-06-21) which
      fixed only the preflight reader. All 4 should use
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=ag)`. Blast-radius:
      `_instruments_metadata.py` reads/writes manifest for IS catalog; orchestrator uses the bucket for its per-shard IS
      availability check — both read the env-LESS bucket today; canonical `-prd-` indexes exist and are fresh for all 4
      AGs. **(MIGRATED FROM: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** — **DONE 2026-07-29 (live-code re-verification).** `_instruments_metadata.py`: all 4
      cited sites (now lines 295/505/585/666, code moved since the original line numbers) call
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="defi")`, each with an in-code comment
      explaining the historical `build_bucket()` bug being avoided. `orchestrator/__init__.py`: the named
      `_sports_instr_bucket`/`_cefi_instr_bucket`/`_defi_instr_bucket`/`_tradfi_instr_bucket` helpers no longer exist
      (grep 0 hits); the module now imports + re-exports `resolve_bucket_name` directly (`__all__` includes it) and uses
      it for the market-data bucket path. Swept the rest of the repo for residuals
      (`rg -n 'build_bucket\(' --include='*.py'` and `get_bucket_name("instruments"` ) — every remaining hit is a code
      COMMENT documenting the old bug for context (e.g. `catalog_registration.py:134`), not a live call; the repo also
      already carries a dedicated QG regression script (`scripts/quality_gates/check_reader_writer_bucket_parity.py`)
      guarding this exact reader/writer-bucket-parity class going forward. No residual env-LESS site found; nothing to
      redirect.

- **[INFRA] P0. RESOLVED-MOOT 2026-08-09** (extracted 2026-08-09 to
  `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` as "Migration data-copy fan-out — re-attempt the 20-VM
  fan-out"; closed out there, not re-dispatched). The `[BLOCKED-INFRA]` tag above was already stale before this
  extraction — not just because the round5-cross-cutting-audit 2026-08-08 note below resolved the tarball-pin gate, but
  because **the launcher + its target script no longer exist and there is no source data left to copy**:
  `launch-legacy-bucket-migration-sharded.sh` (`deployment-service/scripts/vm/`) was deleted 2026-08-03
  (`deployment-service@d407b8b9`) as confirmed-dead code — its target script
  `migrate_legacy_tick_buckets_to_canonical.py` was independently deleted 2026-07-25
  (`market-tick-data-service@4d235caf`/`@f8276e22`) once its own `Delete-when` OR-clause was satisfied by E8's deletion
  of `market-data-tick-sports-central-element-323112` (per `bucket_iam_write_protection_per_tier_2026_06_09.md`
  P2.2f/g/i's investigation, done 2026-08-03 — six days before this doc's 2026-08-09 batch-extraction re-surfaced the
  item as still actionable). Re-verified live 2026-08-09: all 5 legacy flat tick buckets this script's `PAIRS` list
  covered (`market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112`) return
  `BucketNotFoundException: 404` — none exist; their 5 canonical `-prd-`/`pred-prd-` counterparts all exist and are
  live. The drain→migrate→decommission sequence for the legacy tick buckets is fully complete via a path independent of
  this launcher — there is nothing to re-attempt. **round5-cross-cutting-audit 2026-08-08**: option (a) (pin-aware
  retention) also shipped as a general mechanism (`/codex/05-infrastructure/vm-tarball-deployment.md` § "Pin-aware
  retention", `tarball_pins.collect_in_use_pins()`, `unified-trading-library@52ee4056` +
  `deployment-service@4c6cef9`/`@dfd7608`) — moot for this item specifically, but real for any other launcher still
  relying on pin protection.

- [ ] [SCRIPT] P0. **Manifest completion belongs to the canonicalisation plans, NOT this plan.** Canonical `_index` is
      made authoritative by `defi_manifest_canonicalisation_2026_06_01.md` (defi) + the manifest v8/v9 schema
      migration + `pipeline_mode_implementation` + `data_source_provenance` — they regenerate canonical-format rows from
      the (already dual-written) canonical DATA. This plan COORDINATES (single-walk ordering, banner in defi_manifest)
      but does not seed. Confirm canonical `_index` is `C-GREEN` per those plans before decommission.

  > ⏸️ **GATED on G4 applies completing** — all 5 AG `--apply` single-walks still `[ ]` pending in
  > `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (operator-fired; not yet run 2026-06-12).
  > Re-dispatch with G4-apply prereq per operator guidance (BLK-fb70523c, 2026-06-12 slot-2). **(MIGRATED FROM:
  > `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [SCRIPT] P0. **GATED** — after the prerequisite plans above complete for each asset_group, relaunch
      `mdps-backfill-defi` (defi), `mdps-prediction-2025` (prediction), `sports-scheduler` (sports) from a tarball that
      carries the MDPS canonical-bucket fix (`market-data-processing-service@61900a3`); T+10min verify each writes ONLY
      to the canonical `-prd-`/`-pred-prd-` bucket (`_index` mtime advances on canonical, NOT the flat legacy name).
      NOTE: same pinned-tarball-prune blocker applies — resolve tarball persistence first.

  > **Naming-collision note (2026-07-12):** the `sports-scheduler` named here is the **MDPS `mdps-backfill`-family
  > writer VM** (drained in Phase 3 above) — it is NOT the deployment-service Cloud Run Job `uts-prod-sports-scheduler`
  > (the `SportsTriggerScheduler` cron, fixed + tofu-applied 2026-07-12; see
  > `plans/active/issues/sports_trigger_scheduler_cloud_dispatch_broken_2026_07_08.md`). Same name, different
  > repo/target — don't conflate the two when tracking relaunch/deploy status. **(MIGRATED FROM:
  > `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [SCRIPT] P0. Legacy buckets receive **0** new `_index` writes for ≥1h post-relaunch (writers fully canonical).
      **(MIGRATED FROM: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [SCRIPT] P0. Canonical row count ≥ pre-migration (legacy ∪ canonical), zero `pipeline_mode IS NULL`, zero
      shard-key dupes. Per-asset_group A3 manifest-divergence check clean. **(MIGRATED FROM:
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [INFRA] P0. **VERIFIED ALREADY DONE via `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09.md` todo 7 -- no
      code change needed.** `manifest_consolidator_scheduler.tf` at live-defi-rollout HEAD already carries no `-legacy`
      keys; the live Cloud Run Jobs/crons themselves were removed via direct `gcloud` on 2026-07-12/13/16, all PREDATING
      this doc's own 2026-07-24 creation -- the item's premise was already stale when written. Live-reverified
      2026-08-09: `gcloud scheduler jobs list` returns zero `-legacy`-named or orphaned manifest-consolidator jobs.

- [ ] [SCRIPT] P0. **L6 decommission — gated PER asset_group on its L3 plan reporting C-GREEN** (legacy-only CELLS = 0 +
      canonical v9). L3 owners: defi=`defi_manifest_canonicalisation` §C ·
      prediction=`prediction_manifest_canonicalisation_2026_06_01` · cefi=`cefi_manifest_canonicalisation_2026_06_01` ·
      tradfi=`tradfi_manifest_canonicalisation_2026_06_01` (v9+partition single-walk; C-source rider absorbed
      `tradfi_massive_dual_source` Task -031 — was: "`tradfi_massive_dual_source` re-walk (v9+partition, master
      CONFLICT-2)" — corrected 2026-07-12, doc-reconciliation finding 177, §A2 B-queue ruling:
      `tradfi_massive_dual_source_2026_05_28.md`'s own owner table (L504) says its Task -031 manifest re-consolidation
      "MIGRATED" to `tradfi_manifest_canonicalisation_2026_06_01.md`, matching this same doc's L3 section above) ·
      sports=verify-only. For each AG, after its L3 is C-GREEN + a short soak: empty + delete the legacy flat +
      tier-first + long-form tick bucket (and the instruments-store legacy buckets per the adjacent drift), GCP + AWS.
      Canonical `-prd-`/`-pred-prd-` becomes the sole SSOT. Record in `_index/snapshots/decommission_2026_06_0X.md`.
      **Do NOT delete an AG's legacy bucket while its L3 plan is open** — prediction/cefi hold legacy-only history.
      **cefi: ✅ BUCKET ALREADY DELETED 2026-07-14** (10 days before this doc's own L3 gate was attempted;
      operator-confirmed deliberate; see
      `/plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`). CF-11 normalization-aware
      comparison run 2026-08-07 shows 59,488 unique (date,venue,itype,dtype) cells from the legacy 2026-05-16 snapshot
      absent from -prd; breakdown is pre-canonical-era data (2019+ DERIBIT/BYBIT/etc.) + pre-CF-11 empty-itype/dtype
      ghost rows — not a post-migration regression gap. Full counts recorded in that issue doc. **prediction: ✅ DONE
      2026-07-13** — `prediction_manifest_canonicalisation_2026_06_01.md`'s E7/E8/E8b data-safety gates were all GREEN
      (0 legacy-only cells both buckets, snapshots taken, operator-authorized 2026-07-10); both
      `market-data-tick-prediction-…` + `instruments-store-prediction-…` version-purged + bucket-deleted, confirmed 404.
      defi/tradfi/sports unaffected, this item stays open for them. cefi: ✅ already deleted (see note above).
      **(MIGRATED FROM: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [SCRIPT] P0. **Version-aware + orphan-aware delete (slot/Harsh bucket-state verification 2026-06-02).** Two gaps
      the per-bucket delete must handle, surfaced by reading live bucket state: (1) the canonical `-prd` buckets were
      pre-seeded by a PARTIAL env-split copy in legacy FORM (live-object: defi ~43% / cefi ~65% / tradfi ~93% of legacy;
      cefi also ~17 days stale) — after each L3 form-walk writes canonical `pipeline_mode=` paths, the pre-existing
      legacy-FORM objects inside `-prd` are ORPHANS and must be swept (owned in each AG's L3 verify step), else the
      consolidator rebuild double-counts; (2) the legacy buckets carry large NONCURRENT/soft-deleted version history
      (cefi 3.81M, tradfi 3.52M, defi 1.15M noncurrent via Cloud Monitoring `storage/v2/total_count`) — the decommission
      must purge object VERSIONS (not just live objects), and the "canonical ≥ legacy" verify gate must compare
      Monitoring `type=live-object` counts, never a naive recursive `ls` (which counts versions + soft-deleted).
      **prediction: ✅ DONE 2026-07-13** — `gcloud storage rm --recursive --continue-on-error` purged all versions
      (live + noncurrent) of both prediction buckets natively in one op each (no orphan-sweep needed — prediction's
      `-prd`/`-pred-prd` buckets were not part of the partial env-split pre-seed this item describes). **cefi: ✅ BUCKET
      DELETED 2026-07-14** — all live + noncurrent versions (formerly 3.81M) purged with the bucket. tradfi (3.52M) /
      defi (1.15M) noncurrent versions remain untouched, out of scope for this pass. **(MIGRATED FROM:
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [SCRIPT] P1. Add this finding to the `batch_live_symmetry_master` audit instructions as a recurring check
      (legacy bucket-name dual-write detection) — extends the pipeline_mode checks already landed 2026-06-01.
      **(MIGRATED FROM: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** — **DONE 2026-07-29**: added item (l) to
      `plans/audit/instructions/batch_live_symmetry_master_audit_instructions.md`, following the existing (g)-(k)
      pipeline_mode-check format — greps for uncovered-domain `get_bucket_name()` calls and hand-rolled bucket-name
      string concatenation, cross-referencing this plan as the precedent incident.

- [x] ✅ [SCRIPT] P1. Reopen-note on archived `bucket_name_ssot_canonicalisation_2026_05_10.md`: add a
      residual-runtime-drift banner pointing here (the resolver was canonical but live writers bypassed it). Update
      `codex/05-infrastructure/` bucket-naming SSOT doc with the "writer must use resolver, not string-concat" rule.
      **(MIGRATED FROM: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** — **DONE 2026-07-29**: added a `🔁 REOPEN-NOTE` banner to
      `plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` pointing here. Updated
      `/codex/05-infrastructure/bucket-isolation-model.md`'s opening "Stale pointer removed" note to also disambiguate
      the live `unified_trading_library.core.cloud_constants.get_bucket_name()` (same name, different module, still in
      use) from the retired `unified-cloud-interface` one, and codified the "new writers call `resolve_bucket_name()`
      directly, never `get_bucket_name()` or hand-rolled string-concat" rule there.

- [ ] [INFRA] P2. **DEFERRED** Fix the 6 BQ `feature_external` external tables in
      `deployment-service/terraform/gcp/bigquery_feature_external_tables.tf` — point `source_uri_prefix` at each
      bucket's actual hive-partitioned SUBTREE (not the bucket root, which sweeps
      `_index/`/`backfill-logs/`/`raw_tick_data/` and fails BQ CUSTOM partition validation) and reconcile the declared
      5-key schema with the real per-bucket layout; the tradfi/features buckets are near-empty so guard for "matched no
      files". Net-new tables, 0 live impact while blocked. Provenance: TF reconcile 2026-06-19. Owning plan:
      `bigquery_feature_ml_compute_engine_option_2026_06_08.md`. **(MIGRATED FROM:
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [INFRA] P3. **DEFERRED** Decide migrate-first/retire for the UNMANAGED legacy prod resources surfaced by the
      reconcile (not destroyed). ~~unified `strategy-store-central-element-323112` + `strategy-store-test-…` (superseded
      by per-AG)~~ — **RESOLVED, no longer applicable**: the flat `strategy-store-central-element-323112` bucket was
      DELETED 2026-07-18 per `bucket_fold_execution_strategy_2026_07_17.md`'s Fold-D cutover (re-tiered to
      `strategy-store-prd`, source flat bucket deleted, operator pre-authorized), independently re-verified live
      2026-07-25 (`gcloud storage buckets describe` → 404 not found). Remaining open portion: legacy non-prefixed
      schedulers (`client-reporting-hourly`, `instruments-daily-backfill`, `sports-ref-v3-{1,2,3}-start`,
      `t1-daily-pipeline-trigger`, `qg-snapshot-daily`, `market-tick-*-daily-*`, `*-service-daily-trigger`) +
      `uts-prod-ml-inference-t1-schedule` (TF canonical is `ml-service-t1-recon`). These are NOT TF-modeled → not
      destroy-drift; importing entrenches old naming, so migrate consumers → canonical then delete.
      `uts-dev-*`/`uts-staging-*` schedulers are OTHER-ENV (managed under terraform/state/{dev,staging}) — correctly
      absent from prod state, out of scope. Provenance: TF reconcile 2026-06-19.

**NEVER destroyed a live resource.** Lock file (`.terraform.lock.hcl`) intentionally left on the committed
HashiCorp-registry version — the local `tofu` runs swap it to the opentofu mirror, but that swap is a tool artifact
(CI/`terraform` operators use the HashiCorp registry) and was reverted before commit. **(MIGRATED FROM:
`bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

## Deferred work — migrated to:

- Instruments-store env-LESS readers item (line ~62, MTDS orchestrator + `_instruments_metadata.py`): N/A — no
  migration, still owned + open in this plan.
- P2 (BQ `feature_external` external tables terraform fix): migrated to
  `bigquery_feature_ml_compute_engine_option_2026_06_08.md` (named owning plan).
- P3 (migrate-first/retire decision for unmanaged legacy prod resources): N/A — no migration, still owned + open in this
  plan.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the L6 decommission and version-aware delete todos are
  prod-bucket deletes = human-only hard stop; a [BLOCKED-INFRA] P0 carries a 3-option operator decision on tarball
  persistence.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries) -- added the tarball-deployment codex SSOT
  (current BLOCKED-INFRA gate), the legacy-cron terraform target, and the bucket-resolver source module.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-07-30; all 10 open todos are gated behind the
  BLOCKED-INFRA tarball-persistence 3-option operator decision, prod-bucket deletes (human-only hard stop), or per-AG L3
  plans' own C-GREEN gates this plan only coordinates, not executes.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged):
  today's round5-cross-cutting-audit entry cleared the tarball-persistence operator-gate on the `[BLOCKED-INFRA]` P0
  fan-out item, but the doc's other 9 open todos remain gated behind prod-bucket deletes (human-only hard stop) or
  per-AG L3-plan C-GREEN gates this plan only coordinates -- whole doc stays NA.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **cross_cutting_satellite_ao_dispatch_batch3 finalize reconciliation, 2026-08-09 (slot 15)**: reconciled the remaining
  `EXTRACTED 2026-08-09 -> batch3` pointer (the 8 legacy manifest-consolidator cron Terraform blocks item, todo 7) --
  verified already done, no code change needed, flipped to `[x]`. The other batch3-related item in this doc (Migration
  data-copy fan-out, RESOLVED-MOOT) was already correctly reconciled by a prior session -- no further edit needed there.
  Doc keeps 8 open `- [ ]` items (L6 decommission gates, version-aware delete, manifest-completion coordination,
  relaunch/verify chain) -- `status` stays `active`, all real prod-bucket-delete/per-AG-gate work.
- **na-eligibility-audit 2026-08-17** [body-hash:c5427bf439e4e9ef]: KEEP-NA, valid -- Reaffirmed KEEP-NA by 3 prior na-eligibility-audit passes (2026-07-30, 2026-08-07, 2026-08-08 round7 RECLASSIFY sweep). Independently re-verified: every remaining open todo is gated -- 4 items sequenced behind per-AG L3 canonicalisation plans reaching C-GREEN (this plan explicitly coordinates, does not seed); 2 items are prod-bucket deletes, a human-only hard stop per the delete-safety protocol; 1 item is explicitly redirected to a different owning plan (bigquery_feature_ml_compute_engine_option_2026_06_08.md, per the doc's own 'Deferred work -- migrated to:' section); 1 item is an explicit open migrate-vs-retire decision.
- **context-scout 2026-08-17**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
