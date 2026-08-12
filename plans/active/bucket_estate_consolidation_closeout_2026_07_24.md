---
doc_type: plan
title: Bucket estate consolidation — closeout residuals (6 forked mop-up todos)
summary:
  "Forks the 6 still-open todos from bucket_estate_consolidation_to_sub100_2026_07_13.md (15/21 done, archived
  2026-07-24 per the plan line-cap remediation triage) into a small standalone closeout plan: recon-bucket end-to-end
  chain characterization, the cross-plan deletion checkpoint (DeFi/lending/legacy-twin buckets owned by other plans),
  the ml legacy flat-bucket trio delete, the 11-alias `_KIND_ALIASES` hard-removal, residual asset-group-parity cosmetic
  drift, and closing/re-confirming the 3 bucket-SSOT audit issue docs. Content moved verbatim, not rewritten — see the
  archived parent's Progress Log for the full Wave 0-3 execution history."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    deployment-service,
    unified-api-contracts,
    unified-trading-pm,
    unified-trading-library,
    deployment-api,
    unified-trading-system-ui,
    batch-live-reconciliation-service,
    e2e-testing,
    execution-service,
  ]
scope: [engineer, admin]
tags: [gcs, buckets, consolidation, closeout, terraform, migration, lifecycle, infrastructure, plan-hygiene]
related:
  [
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    /plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md,
    /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on: [defi_dedicated_bucket_shared_migration_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Forked 2026-07-24 from bucket_estate_consolidation_to_sub100_2026_07_13.md per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 1) — parent hit 2129 lines against the 1000L
  hard-fail cap with only 6/21 todos still open; this plan carries those 6 forward verbatim while the parent archives
  with its Progress Log intact as history."
last_updated: 2026-07-25
context_scope:
  [
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md,
    deployment-api/deployment_api/deployment_api_config.py,
    batch-live-reconciliation-service/batch_live_reconciliation_service/config.py,
  ]
---

# Bucket estate consolidation — closeout residuals

> **Forked 2026-07-24** from `bucket_estate_consolidation_to_sub100_2026_07_13.md` (archived same day to
> `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md`, 15/21 todos done — see its Progress Log
> for the full Wave 0-3 execution history, including the audit provenance, the operator rulings baked in, and every
> shipped commit). This plan carries forward, **verbatim, unedited**, the 6 todos that were still open at archival time
> — no scope was added or dropped in the fork.

Codex SSOTs: `/codex/05-infrastructure/bucket-isolation-model.md`, `/codex/05-infrastructure/gcs-lifecycle-policies.md`,
`/codex/05-infrastructure/gcs-object-operations.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/05-infrastructure/manifest-consolidator-ssot.md`.

## Wave 2 residuals — in-flight completions + audit-found breakages

- [ ] [DATA] P0. **recon bucket** ([[recon_bucket_missing_nightly_recon_failing_2026_07_13]]) — UPDATED 2026-07-14 (this
      session, see item D in the Round-2 table + Progress Log for full detail): prod image pickup is now DONE + verified
      (BLRS's Dockerfile needed a SECOND digest bump — the first landed a UTL base image whose bundled UAC snapshot
      predated the actual recon-kind commit by ~3.5h; `blrs@be056b1` fixes it, live-verified via a real triggered
      execution that Stage 0 now resolves the bucket correctly and gates on the RIGHT, already-documented reason). The
      upstream t1-recon ML/strategy producer chain investigation is COMPLETE and the finding is precisely scoped:
      execution-service's config-snapshot job and ml-service's t1-recon job were BOTH NEVER PROVISIONED (Cloud Scheduler
      fires daily into a 404); strategy-service's job existed but its container-exec config was broken (FIXED this
      session, `ds` terraform + a direct `gcloud run jobs update` — now runs but hits a missing required `--date` arg
      one layer deeper); no producer in this chain (ml or strategy) implements the `--run-tag`/`_SUCCESS`-marker writer
      convention at all (ml-service parses a dead `--run-tag` flag that nothing consumes; strategy-service has no such
      flag). Standing up the real end-to-end chain is multi-repo feature work
      (execution-service/ml-service/strategy-service/features-service) — OUT OF SCOPE for this plan, left as a
      precisely-characterized open item. Cloud Run failure alerting (55 silent failures) remains untouched — not reached
      this session, still open. Original todo: operator decides kind vs prefix; provision; repoint
      `batch_live_reconciliation_service/config.py` to the resolver; fix launcher doc; end-to-end T1 chain run; next
      scheduled run green; wire Cloud Run failure alerting (55 silent failures). **round5-cross-cutting-audit 2026-08-08
      correction**: "operator decides kind vs prefix" is STALE — `kind="recon"` was decided+shipped 2026-07-13/14
      (config.py:97 `resolve_bucket_name(..., kind="recon")`, live-verified). No operator input needed; remaining scope
      is non-operator-gated multi-repo ENGINEERING work. **round5-cross-cutting-audit 2026-08-08 correction**: the
      "operator decides kind vs prefix" framing is STALE — `kind="recon"` was decided and shipped 2026-07-13/14 (see
      above: `cloud-providers.yaml` `recon` kind added, buckets provisioned,
      `batch_live_reconciliation_service/config.py:97` repoints to
      `resolve_bucket_name(cloud=cloud_name,     kind="recon")`, live-verified). No operator input needed; remaining
      scope is non-operator-gated multi-repo ENGINEERING work (producer-chain stand-up + Cloud Run failure alerting),
      correctly still open but not a blocker-digest question.
- [x] ✅ [DATA] P0. Track to completion the deletions OWNED BY OTHER PLANS (checkpoint). **DONE 2026-07-31 —
      unified-trading-pm@\<see plan-flip commit\>.** Freshly re-verified all 3 sub-items (transcription-only for the
      DeFi trio per the 2026-07-31 corpus-wide ownership-conflict sweep's scope-fence; live citation re-derivation for
      the other two) — **all 13 buckets across the 3 sub-items are now confirmed deleted, zero residual.** - **DeFi
      trio** (`dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd`) — TRANSCRIBED from
      [[defi_dedicated_bucket_shared_migration_2026_07_13]] (now archived, 16/17 todos `[x]`, the doc's own 2026-07-31
      banner reads "✅ OWNERSHIP RESOLVED... this plan is the authoritative record... all `[x]` with evidence"): all 3
      CONFIRMED DELETED (`gcloud storage buckets list`, zero matches in any form, 2026-07-14) — `dex-pools-prd` deleted
      directly by the operator 2026-07-14T11:03:47Z, before that todo's own snapshot-before-delete step ran (no
      independent pre-delete object-diff of the ~209k-object legacy tree exists — risk assessed low, not zero, per the
      sibling plan's own writeup); kinds removed from all 5 `cloud-providers.yaml` copies (34 kinds); Terraform state
      clean (`tofu state list` zero matching `google_storage_bucket` entries). No independent re-audit run here, per the
      scope-fence. - **`lending-indices` + `lending-indices-prd`** — **CONFIRMED DELETED, not "still HELD" as this
      checkpoint previously (2026-07-25) read.** Per `gcs_bucket_estate_cleanup_2026_07_10.md` §5l (2026-07-21
      reconciliation, citing `bucket_estate_consolidation_to_sub100_2026_07_13.md` Item C, line ~533): purge-lifecycle
      armed 2026-07-14T14:00Z (flat unversioned; `-prd` `versioning_enabled=true`/`soft_delete_policy=604800s`),
      **"STATUS: COMPLETE 2026-07-15"** — `gcloud storage buckets delete --quiet` on BOTH
      `lending-indices-central-element-323112` and `lending-indices-prd-central-element-323112` succeeded (no "not
      empty" error), both confirmed 404 via `buckets describe`. The Morpho VM (`mtds-lending-indices-20260712-112557`)
      referenced in the prior checkpoint text wrote to the unrelated canonical shared bucket, not either of these two —
      its completion/SIGKILL status was never actually a gate on this deletion; the prior "write-target verification
      inconclusive" phrasing was itself the stale artifact, superseded by the same-doc's own later Item C closure
      note. - **Legacy flat tick+instruments twins (−8)** — **ALL 8 CONFIRMED DELETED**, not "purge-lifecycle armed
      (cefi/defi/tradfi) + sports pair HELD" as this checkpoint previously read. 6 of 8
      (`market-data-tick-{cefi,defi,tradfi}`, `instruments-store-{cefi,defi,tradfi}`) per
      `bucket_estate_consolidation_to_sub100_2026_07_13.md` (archived) — the 6-sibling purge-lifecycle drain completed
      with zero force-purge needed (armed 2026-07-13, all 404 via `buckets describe` by 2026-07-14T10:57Z), plus
      `instruments-store-cefi` (that doc's own "Item A", the 7th/8th of this set, closed separately after a shape-aware
      re-diff found only 4 true legacy-only keys, all superseded-by-venue-rename — not a real gap — Purge RE-ARMED
      2026-07-14T13:31:43Z UTC, **"STATUS: COMPLETE 2026-07-15"**, `buckets describe` → 404, "Item A CLOSED"). The
      remaining 2 (sports pair, `market-data-tick-sports`/`instruments-store-sports` flat) were the genuinely still-HELD
      residual as of this checkpoint's 2026-07-25 text (gated on `sports_manifest_canonicalisation_2026_06_01` E1/E8's
      CF-8 gate) — **since resolved by a dedicated cutover plan not previously cross-referenced here**:
      `sports_legacy_bucket_cutover_2026_07_16.md` (status: complete, archived 2026-07-27) ran its own Phase 0-6
      freeze/move/purge/delete/restore runbook independently of the CF-8 `available_at` gate (a data-quality gate on the
      CANONICAL `-prd-` bucket, orthogonal to whether the LEGACY flat twin is safe to delete) —
      `instruments-store-sports-central-element-323112` **DELETED 2026-07-16T19:52Z** (T5.4; 968,927 objects + 34,596
      versions purged, 0 errors, `describe` → 404, no-resurrection proved via a clean `tofu plan`);
      `market-data-tick-sports-central-element-323112` **DELETED 2026-07-17T~16:50Z** (T5.4 MDT half; OR-5b resolved,
      32-day/549,392-key recovery landed into canonical first, `legacy_only==0` verified on every gap day, zero loss;
      342,629 objects/versions purged, 0 errors, `describe` → 404). Phase 6 RESTORE completed 2026-07-17 (every
      writer/consolidator/scheduler un-paused, first run GREEN on canonical). Original text (for provenance):
      "dex-pools-prd purge-lifecycle armed (24h async; disarm window if concerns)" was stale vs. the sibling plans' more
      final status — corrected 2026-07-25, then re-corrected again here 2026-07-31 for the lending-indices and
      legacy-twin sub-items, which the 2026-07-25 pass had not yet re-derived from current sibling-plan state.
- [ ] [DATA] P1. **ml legacy variants**: `ml-models-store` flat (data already migrated §5e, resolver fixed §5h — verify
      no new writes since, then delete) + `ml-models-store-{dev,prod,staging}`,
      `ml-configs-store`/`ml-predictions-store` flat twins (empty). Verify
      `deployment-api/deployment_api_config.py:642`'s flat `ml-configs-store-{pid}` default is repointed first.
      **UPDATED 2026-07-25 (this session) — re-verified safe, but NOT executed: delete crosses a human-only hard stop.**
      Repoint precondition CONFIRMED: `deployment_api_config.py`'s `ml_configs_store_bucket` field (now at line ~603,
      shifted from :642) defaults `""` → folds through `resolve_bucket_name` to `ml-store-{env}-{pid}` already — no code
      change needed. Bucket-existence probe this session (`gcloud storage buckets describe`, 403=exists vs 404=absent —
      see `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` Part 1): `ml-models-store-{dev,prod,staging}`
      (GCP) = **404, already gone** (matches `bucket_estate_fold_design_2026_07_13.md`'s note that Wave 1/2 already
      deleted these); `ml-configs-store` / `ml-predictions-store` flat, no-suffix (GCP + AWS via
      `aws s3api head-bucket`) = **404, already gone**. Only **one bucket remains**: GCP `ml-models-store` (flat legacy,
      403=exists) — content-parity already proven by a prior session (`bucket_fold_ml_2026_07_17.md` TICK 2: server-side
      byte-count parity, dst `/models/` byte- identical to `ml-models-store-prd`, "100% redundant... its delete loses
      NOTHING") and zero live readers already proven (`bucket_fold_ml_2026_07_17.md` TICK 1: "verified NO live source
      reader resolves the flat name anymore"). Fresh grep-then-READ this session (not grep-then-conclude) across
      ml-service/deployment-service/ deployment-api/UTL for every literal
      `resolve_bucket_name(kind="ml-models-store"...)` (and sibling `get_write_bucket_name`/`_KIND_ALIASES` call sites)
      found **zero live executable callers** — every hit is a `#`/docstring comment describing the (already-executed)
      fold, not an actual resolver call (READ, not just grepped: `ml-service/ml_service/inference/config.py` resolves
      via `get_write_bucket_name("ml_models")`, not the retired kind literal). **Disposition: `yes-twin-confirmed`** per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`'s five-part proof (Parts 1/2/5 cited from the prior
      session's real GCS verification since this SA lacks `storage.buckets.get`/`objects.list` on this specific bucket
      to independently re-run them — see below; Parts 3/4 freshly re-verified this session). **NOT executed — this is a
      HARD STOP, not a judgment call:** that same codex doc's § 3 human-only hard stops (#1) reads "Any prod-bucket
      delete... There is no confidence level at which an agent deletes from prod... Human executes; agent suggests" —
      `ml-models-store` held live production model artifacts pre-fold and is production-tier storage, so it is in scope
      regardless of the confirmed-safe disposition. Separately (belt-and-suspenders, not the primary reason): this
      session's `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` ADC also lacks
      `storage.buckets.get`/`storage.objects.list` on this specific bucket (403 on both probes) and lacks
      `resourcemanager.projects.getIamPolicy`, so it could not execute the delete even absent the hard stop.
      **Ready-to-run for the operator**: `gcloud storage rm -r gs://ml-models-store` (GCP project
      `central-element-323112`), then remove any now-dead TF/yaml reference to the flat name (none found this session —
      the flat name was never in `cloud-providers.yaml`, only the resolver-side `_KIND_ALIASES`, which is itself already
      sunset per the todo below). Left `- [ ]` deliberately — see notes. **NOTE 2026-08-12 (docs-drift correction,
      interactive session): the delete this todo asks for has ALREADY HAPPENED, via the sibling plan, not this one.**
      `bucket_fold_ml_2026_07_17.md`'s "Delete sources" P0 todo is checked `[x]` DONE 2026-08-08 (operator
      authorization, NA-corpus blocker digest round 5, id=44) and its own text states, GCP side: "already gone — nothing
      to delete... none of the 5 legacy source names (`ml-models-store`, `ml-models-store-prd`, `ml-predictions-store`,
      `ml-configs-store`, `ml-training-artifacts`, `ml-artifacts`) exist in this project any more" — cross-checked via
      both `gcloud storage buckets list` and `gcloud asset     search-all-resources` (project-level inventory). That is
      the SAME flat `ml-models-store` GCP bucket this todo targets. So the categorical human-only hard stop this todo
      was waiting on is moot — the bucket is confirmed gone, executed under the sibling plan's own record, not this one.
      Not flipping this checkbox `[x]` here myself (no independent re-verification run from this session, and this doc's
      own convention treats the checkbox flip as a formal closeout step) — left `- [ ]` for a human/future pass to
      reconcile formally against `bucket_fold_ml_2026_07_17.md` as the actual execution record.

## Wave 3 residuals — structural-fold closeout

- [x] ✅ [DATA] P3. **`_KIND_ALIASES` hard-removal — 11 coupled aliases still need a per-consumer repoint before their
      alias can be removed** (folded in from `bucket_fold_closeout_2026_07_17.md`, its sole open todo). — **RE-VERIFIED
      2026-07-25 (this session): ALREADY DONE, no code change needed — `unified-trading-library@055948e33` (2026-07-19,
      an ancestor of `origin/live-defi-rollout`, confirmed via `git merge-base --is-ancestor`) shipped this exact work 5
      days before this closeout plan was even forked.** `git blame` on `bucket_naming.py`'s `_KIND_ALIASES` dict
      confirms the commit message: "refactor(cloud): sunset the 11 coupled bucket-kind aliases
      (features-_/ml-_/execution-store-prediction) — every resolver caller repointed to the folded
      features/ml-store/execution-store kinds; v8 migration + cloud_constants \_DOMAIN_TO_YAML_KIND folded; no double
      SSOT." Fresh grep-then-READ this session (not grep-then-conclude) re-confirmed: (1) `_KIND_ALIASES` in
      `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py` carries **zero** entries for
      any of the 11 (only `features-cross-instrument`/`features-multi-timeframe`/`tick-data` remain — the 3
      permanent-vocab KEEP kinds); (2) all 3 real `cloud-providers.yaml` copies (deployment-service authoring, UAC
      packaged, PM mirror) are grep-clean of all 11 as yaml keys too; (3) every named consumer the todo called out was
      individually READ (not just grepped) and found already repointed:
      `features-service/scripts/e2e/     run_pipeline_e2e.py` `_delta_one_test_bucket()` calls
      `_test_bucket("features", ...)` not the retired alias;
      `unified-trading-library/.../migrations/upgrade_manifest_to_v8.py` enumerates the folded `"features"`/
      `"execution-store"` kinds directly (its `_PER_AG_KINDS`/`_FLAT_KINDS_PREDICTION` tuples, not the retired
      per-kind/execution-store-prediction names); `deployment-api/deployment_api_config.py`'s `ml_configs_store_bucket`
      field already folds through the resolver; `ml-service/ml_service/inference/config.py` resolves via
      `get_write_bucket_name("ml_models"/"ml_predictions")`, not a literal retired-kind `resolve_bucket_name` call.
      Every remaining hit across ml-service/deployment-service/deployment-api/UTL for the 11 kind-literal strings is a
      `#`/docstring comment describing the (already-executed) fold — zero live executable callers. **Gate satisfied**:
      11/11 grep-clean, all aliases removed, no terraform change needed (nothing left referencing the retired yaml keys
      to plan a destroy against). Evidence: `unified-trading-library@055948e33` (already shipped, ancestor of
      `origin/live-defi-rollout`) — no new commit required for the code; this session's contribution is the
      re-verification recorded here. Phase 1 + Phase 2 Part A are DONE: 6 alias-only/grep-clean kinds already
      hard-removed (`pnl-attribution-store`, `risk-metrics-store`, `pnl-attribution-output`, `positions-store`,
      `archetype-state`, `position-store-sports` — UTL@c8f5bf39/384e0b28), every LIVE
      `resolve_bucket_name(kind=<retired>)` consumer across ml-service, features-service, execution-service, UTL,
      deployment-service, and deployment-api now calls the folded kind directly (behaviorally no-op), and the
      yaml-key/terraform coupling that gated Part B is CLEARED (13 retired yaml keys stripped from all 5 copies,
      `tofu plan` 0 bucket-create/0 bucket-destroy). **⛔ SUPERSEDED (see the 2026-07-25 update above) — the rest of
      this paragraph is the ORIGINAL (2026-07-17-vintage, carried verbatim through the fork) description and is now
      factually stale; kept for history, not current status.** ~~**Remaining = 11 aliases** whose readers deliberately
      still resolve the retired vocab and are NOT yet repointed:~~
      `features-{delta-one,volatility,onchain,xinstrument,mtf}` (features-service `run_pipeline_e2e.py`
      `_test_bucket`/`_delta_one_test_bucket` + `smoke_matrix.py` SMOKE_INPUT_KIND + data-status-drilldown service→kind
      maps + the still-present `upgrade_manifest_to_v8.py` loop resolver for xinstrument/mtf),
      `ml-{models,predictions,configs,training-artifacts,artifacts}-store` (deployment-api `deployment_api_config.py`
      resolvers + ml-service), and `execution-store-prediction` (same `upgrade_manifest_to_v8.py` loop — delete the dead
      migration OR repoint). Each needs its caller repointed to the folded kind
      (`features`/`ml-store`/`execution-store`) + an explicit object-key prefix BEFORE its `_KIND_ALIASES` entry (UTL
      `bucket_naming.py`) is removed. **KEEP permanently**: `tick-data`, `features-cross-instrument`,
      `features-multi-timeframe` (live consumer vocabulary, not retired). **Gate**: each of the 11 grep-clean of
      `resolve_bucket_name(kind=<retired>)`, its alias removed, and `terraform plan` stays green after removal. "No
      double SSOT." **Not this todo's scope, deferred separately (found during the fold, not omitted)**: a
      `deployment-service` git stash reverting a digest-pin fix on
      `terraform/services/features-service-sports/gcp/terraform.tfvars` (owner: features-service-sports, "NOT decided
      autonomously" — a real pin-vs-`:latest` tradeoff); 4 UAC git stashes (replay/source-capability WIP, a different
      feature's WIP, not bucket-fold scope). Neither is tracked anywhere else yet — flagging so they don't get lost, not
      claiming them here.
- [x] ✅ [CONFIG] P2. **Residual asset-group-parity drift the 2026-07-17 sweep found but left** (all cosmetic/waste,
      none blocking; the GCP live path is fully reconciled): (a)
      `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf:35` + `terraform/aws/main.tf:74` still
      declare `features-onchain-cefi` against the LEGACY `unified-trading-features-onchain-cefi-*` AWS names — same
      producer-less finding as the GCP side, but it points at legacy buckets that still exist, so it wastes a
      consolidator rather than 404-ing; fold into the dev/stg-tier retirement (item above) rather than a standalone
      apply. (b) PM catalogue placeholders naming deleted buckets:
      `configs/data-catalogue.features-volatility-service.yaml:102` (`features-volatility-defi-test-project`),
      `configs/data-catalogue.features-onchain-service.yaml:35`, `configs/checklist.prerequisites.yaml:173,400`,
      `configs/services/features-volatility-service/batch.env:12`
      (`PROTOCOL_DATA_SINK_BUCKET_DEFI=uts-prod-features-volatility-defi` — a `uts-prod-*` shape matching no live
      bucket, so likely dead already: confirm before editing). (c) legacy one-off migration scripts still listing the 7
      deleted names (`deployment-service/scripts/archive-flat-buckets.sh`,
      `scripts/aws/migrate-bucket-names-unified-to-canonical.sh`) — these are historical records of an executed
      migration; decide delete-vs-annotate per the one-off lifecycle rule rather than editing in place. **DONE
      2026-07-25 (this session), (b)+(c) fully + (a) partially (the non-destructive half — see note):** **(a)**
      `manifest_consolidator_scheduler.tf:35` — removed the `features-onchain-cefi` entry, mirroring the already-shipped
      GCP-side fix (same file's GCP twin, removed 2026-07-17) with a matching rationale comment (on-chain metrics are
      DeFi-only in every consumer; CEFI could never have a producer). This is a consolidator-schedule-only map (AWS
      Batch job + EventBridge cron `for_each`), not a bucket resource. **Deliberately LEFT UNTOUCHED:
      `terraform/aws/main.tf:74`'s `group_b_buckets` list** — confirmed (read the file) this feeds a REAL
      `resource "aws_s3_bucket" "unified_trading" { for_each = toset(local.all_buckets) }` (+
      versioning/encryption/public-access-block siblings); removing that entry would plan a live S3 bucket DESTROY on
      the next real `terraform apply` — exactly the standalone-apply risk this todo's own text warns against ("fold into
      the dev/stg-tier retirement... rather than a standalone apply"), and a bucket delete is a human-only hard stop
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3) regardless. Flagging this explicitly rather than
      silently dropping it: the umbrella dev/stg-tier retirement this was meant to fold into is already DONE (per the
      note below this list), so this specific line was simply never folded in and remains open — a genuine residual for
      whoever next does a supervised AWS bucket-list retirement, not a standalone edit. **(b)** Fixed all 4 named files
      to repoint the retired `features-{volatility,onchain}-{ag}` per-kind bucket-name shape to the current Fold-A
      folded `features-{ag}` shape: `data-catalogue.features-volatility-service.yaml` (all 3 CEFI/TRADFI/DEFI `bucket:`
      fields, not just the cited DEFI one — same drift, same file), `data-catalogue.features-onchain-service.yaml` (CEFI
      row corrected + annotated producer-less-by-design, DEFI row repointed), `checklist.prerequisites.yaml` (both the
      GCS `gcs_buckets_features_onchain` and S3 `s3_buckets_features_onchain` sections — the CEFI entry dropped,
      verification greps updated). `batch.env:12` — **confirmed dead, per the todo's own "confirm before editing"**: the
      whole `PROTOCOL_DATA_SINK_BUCKET_*`/`PROTOCOL_DATA_SOURCE_BUCKET_*` block uses a `uts-prod-{kind}-{ag}` naming
      scheme found nowhere in the current estate (no `${GCP_PROJECT_ID}` templating either, unlike the
      `PROTOCOL_EVENT_BUS_PROJECT` var 2 lines below it — pre-dates the bucket-name SSOT); `deployment-service`'s
      bootstrap consumer (`scripts/bootstrap/bootstrap_gcp.sh:165` reads `$REPO_ROOT/configs/services/`) has no
      `configs/services/` directory at all, so this PM-repo copy is not confirmed live-injected anywhere. Annotated as
      stale rather than guessing a "corrected" value nothing verifiably reads (a wrong-but-confidently-relabeled value
      would be worse than a clearly-flagged stale one). **(c)** Both scripts already carried the
      Epic/Lifecycle/Delete-when 3-line marker (`/codex/06-coding-standards/script-homes.md`) — added a STATUS note to
      each confirming the migration they perform has executed and the bucket names inside are a historical snapshot, not
      a live inventory (do not "fix" the names in place); left the actual delete-vs-keep decision against the
      Delete-when condition (orphan-sweep=0) for a dedicated sweep, since I didn't run one this session. Evidence:
      `deployment-service@b47a66f` ((a)+(c)), `unified-trading-pm@b7bef5c7f` ((b)).
- [x] ✅ [DOCS] P3. **Close (or re-confirm still-open) the three bucket-SSOT audit issue docs** referenced by the
      codex-audit todo above. **DONE 2026-07-31 — unified-trading-pm@\<see plan-flip commit\>.** The 3 docs were never
      named by filename anywhere in the corpus (grep-confirmed) — identified via
      `bucket_estate_fold_design_2026_07_13.md`'s own citation trail: its `related:` frontmatter cites
      `terraform_bucket_estate_drift_resurrection_2026_07_13.md` and `strategy_store_split_brain_2026_07_13.md`
      directly, and its body's "hardcoded-name sweeps in the three audit issue docs" line (§1) matches
      `legacy_bucket_template_literals_2026_07_16.md`'s own subtitle ("the QG blind-spot class T1.2 closed") almost
      verbatim — all 3 dated inside the 2026-07-13→07-16 fold window. Re-verified each: 1.
      **`terraform_bucket_estate_drift_resurrection_2026_07_13.md`** — already `status: resolved`
      (`resolved_by: "2026-07-19 bucket_fold_closeout tail-item sweep — all GCP directions (a/b/c/d) + tail items        done"`).
      No change needed. 2. **`strategy_store_split_brain_2026_07_13.md`** — already `status: resolved`. No change
      needed. 3. **`legacy_bucket_template_literals_2026_07_16.md`** — **re-confirmed still-open, with a reason, not
      closed.** Its sole todo (pay down 15 baselined legacy no-env bucket-name TEMPLATE literals across
      features-onchain/calendar/store/sports + instruments-store-tradfi) is genuinely unfinished — none of the 5
      asset-group buckets has reached its own legacy-bucket decommission yet (matches the 2026-07-30
      na-eligibility-audit's independent KEEP-NA verdict). Fresh live check this session
      (`gcloud storage buckets        describe`, all 5 flat legacy names): **all 5 already 404**
      (`features-onchain`/`features-calendar`/
      `features-store`/`features-sports`/`instruments-store-tradfi`-central-element-323112) — so the baselined literals
      are dead code paths (would hard-fail loud on invocation, not silently misdirect to a live bucket); this lowers the
      risk class but does not close the todo, since the code itself still carries the wrong hardcoded template strings
      pending the `resolve_bucket_name(...)` repoint the doc's own Disposition section specifies. Left `status: open`.
      All 3 accounted for (2 pre-existing resolutions confirmed still valid, 1 re-confirmed open with fresh evidence) —
      this todo's own DONE criterion ("re-verify... before closing", not "force all 3 closed") is satisfied.

> **Note on the "(item above)" / "the fold" cross-references above**: these two todos were extracted verbatim from the
> archived parent, where "item above" referred to the dev/stg-tier retirement (Wave 1, DONE) and "the fold" referred to
> the Wave 3 structural-fold execution (DONE) — both fully described in the archived parent's Wave 1/Wave 3 sections and
> Progress Log. Read `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md` for that context
> before starting either todo; it was deliberately not re-paraphrased here per the lossless-fork rule.

## Progress Log

- **2026-07-24** — Plan created. Forked verbatim from `bucket_estate_consolidation_to_sub100_2026_07_13.md`'s 6
  remaining open todos (of 21; 15 were already done) as part of the plan line-cap remediation
  (`/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md`, row 1 / bucket (c)). Parent archived same day to
  `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md` with `status: complete` and
  `superseded_by: [bucket_estate_consolidation_closeout_2026_07_24.md]`; its Progress Log (Waves 0-3 execution history,
  audit provenance, operator rulings) stays intact there as the historical record. No new work executed yet under this
  plan — todo bodies are exactly as they read in the parent at fork time.

- **2026-07-25 — sub-agent session, 3 of the 6 todos closed out (scoped: ml legacy delete + `_KIND_ALIASES` +
  asset-group-parity drift; the recon-bucket E2E chain, the cross-plan deletion checkpoint, and the 3 audit-issue docs
  were explicitly OUT OF SCOPE for this session and were not touched).**
  - **`_KIND_ALIASES` hard-removal — flipped `[x]`.** Re-verification (not new work) found the entire 11-alias
    repoint+removal already shipped `unified-trading-library@055948e33` (2026-07-19, confirmed ancestor of
    `origin/live-defi-rollout`), 5 days before this plan's own 2026-07-24 fork — a plan/code drift the fork's
    lossless-carry-forward didn't catch because the parent's Wave-3 text was itself already stale by 07-19 and nobody
    re-checked before forking. Grep-then-READ (not grep-then-conclude) across every named consumer confirmed zero live
    callers of the retired kind literals. See the todo's inline evidence for the full grep/READ trail.
  - **Asset-group-parity drift cleanup — flipped `[x]`.** (b)+(c) fully done; (a) done only for the non-destructive
    consolidator-schedule half — the bucket-resource half (`terraform/aws/main.tf`'s `group_b_buckets`) was deliberately
    left alone (real S3 `for_each`, a destroy-on-apply risk + a human-only hard-stop territory, and the todo's own text
    already warned against a standalone apply here). Shipped `deployment-service@b47a66f` +
    `unified-trading-pm@b7bef5c7f`.
  - **ml legacy variants — LEFT `[ ]` UNCHECKED, deliberately.** Re-verified genuinely safe to delete (five-part proof
    per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, disposition `yes-twin-confirmed`) — but did NOT
    execute the delete. Two independent reasons, either one sufficient on its own: (1) that same codex doc's § 3
    hard-stop #1 — "Any prod-bucket delete... there is no confidence level at which an agent deletes from prod... Human
    executes; agent suggests" — applies unconditionally to `ml-models-store` regardless of how well-proven the
    disposition is; (2) this session's own GCP/AWS credentials (`unified-trading-sa@central-element-323112...`)
    independently lack `storage.buckets.get`/`storage.objects.list` on this specific bucket (confirmed via direct
    `gcloud storage buckets describe`/`ls` 403s) and lack `resourcemanager.projects.getIamPolicy`, so the delete could
    not have been executed from this session even absent the hard stop. Also confirmed (bucket-existence probes,
    403=exists vs 404=absent): `ml-models-store-{dev,prod,staging}` and the flat `ml-configs-store`/
    `ml-predictions-store` twins are ALL already-gone (404) — only the single flat `ml-models-store` bucket remains,
    fully proven safe, ready for an operator to run `gcloud storage rm -r gs://ml-models-store`. Full disposition +
    evidence recorded inline on the todo.
    > **Correction 2026-08-09 (operator, interactive session)**: reason (1)'s "applies unconditionally... regardless of
    > how well-proven" overstates the codex rule. `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a
    > (extended 2026-07-28 to whole-bucket destroys) DOES let an agent execute a hard-stop-#1 delete autonomously once a
    > FRESH `gcs_bucket_soft_delete_retention_seconds()` check on `ml-models-store` clears ≥604800s — that check was
    > never run here, so "categorically human-only" is the wrong framing; "human-only unless/until §3a's fresh retention
    > check is run and clears it" is correct. This doesn't change the practical outcome this session (reason (2)'s IAM
    > gap independently blocks execution regardless), but the next agent to pick this up should run the §3a check before
    > assuming human-only, not after.
  - **Bash/tooling note**: this session hit a transient shared-host `/tmp` tmpfs exhaustion (2GB tmpfs, other concurrent
    agents' sessions) that blocked all Bash calls for a stretch — recovered on its own; no workaround was needed beyond
    waiting + continuing read-only (Read-tool) investigation in the meantime. Flagging in case it recurs for another
    slot.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — 3 of 4 open todos are human-only hard stops or cross-plan
  checkpoints (prod-bucket delete of `ml-models-store` per delete-safety §3, deletions owned by other plans, the
  recon-bucket multi-repo chain explicitly out of scope).

- **2026-07-31 (data_engineering, `cross_cutting_satellite_ao_dispatch_batch1-001`) — 2 of the 4 remaining todos closed
  out (the cross-plan deletion checkpoint + the 3 bucket-SSOT audit issue docs; the recon-bucket E2E chain and the
  `ml-models-store` prod-bucket delete remain untouched, both correctly out of this dispatch's scope).**
  - **Cross-plan deletion checkpoint — flipped `[x]`.** Per the corpus-wide ownership-conflict sweep's scope-fence, the
    DeFi trio sub-item was TRANSCRIBED (not re-audited) from `defi_dedicated_bucket_shared_migration_2026_07_13.md` (now
    the confirmed authoritative record, archived, 16/17 done). The other 2 sub-items (`lending-indices` pair + the
    8-bucket legacy flat tick/instruments twin set) genuinely needed fresh citation re-derivation, since the 2026-07-25
    checkpoint text was stale on both: `lending-indices`+`-prd` were actually CONFIRMED DELETED 2026-07-15 (per
    `gcs_bucket_estate_cleanup_2026_07_10.md` §5l, citing the sibling plan's Item C), and the sports pair (the only 2 of
    the 8 legacy twins still HELD as of 2026-07-25) were resolved by a dedicated cutover plan
    (`sports_legacy_bucket_cutover_2026_07_16.md`, archived complete 2026-07-27) that ran independently of the CF-8 gate
    the 2026-07-25 text assumed was still blocking — both buckets deleted 2026-07-16/17. **All 13 buckets across the
    checkpoint's 3 sub-items are now confirmed deleted, zero residual.**
  - **3 bucket-SSOT audit issue docs — flipped `[x]`.** None was named by filename anywhere in the corpus; identified
    via `bucket_estate_fold_design_2026_07_13.md`'s own `related:` frontmatter + body citation trail:
    `terraform_bucket_estate_drift_resurrection_2026_07_13.md` (already resolved 2026-07-19),
    `strategy_store_split_brain_2026_07_13.md` (already resolved), and `legacy_bucket_template_literals_2026_07_16.md`
    (re-confirmed genuinely still open — its pay-down todo is unfinished, though a fresh live bucket-existence check
    this session confirmed all 5 referenced legacy bucket names are already 404, lowering the risk class from
    silent-misdirect to loud-fail-if-invoked).
  - Full evidence trail inline on both todos above.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, trimmed from 8) — re-derived off the 2 genuinely
  still-open todos (recon-bucket E2E chain P0, `ml-models-store` prod delete P1, both otherwise blocked) rather than the
  whole original 6-todo spread; added 2 real source paths (`deployment_api_config.py`'s `ml_configs_store_bucket`
  resolver, BLRS's `config.py` recon resolver).
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — only 2 open todos remain, both genuinely NA: recon-bucket P0 is
  explicit multi-repo feature work pending an operator kind-vs-prefix decision before any dispatch can even be scoped;
  ml-models-store delete P1 is a fully-proven-safe disposition that is a human-only hard stop per
  `gcs-and-manifest-delete-safety-protocol.md`.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged): recon-bucket P0 needs an
  operator kind-vs-prefix decision before it can even be scoped; ml-models-store delete P1 is a proven-safe disposition
  that is still a human-only hard stop per delete-safety-protocol.md §3.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-06 (unchanged, only 2 open todos):
  recon-bucket P0 remains OPERATOR_QUESTION-blocked (kind-vs-prefix decision); ml-models-store delete P1 remains
  OPERATOR_QUESTION (fully-proven-safe disposition, but a human-only hard stop per
  `gcs-and-manifest-delete-safety-protocol.md` §3 — agent execution is categorically excluded, not just judgment-gated).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged): 2
  open todos remain -- the recon-bucket item's operator-gate is now cleared (per its own 2026-08-08
  round5-cross-cutting-audit correction) but its remaining scope (multi-repo producer-chain stand-up) is explicitly
  out-of-scope-for-this-plan; the `ml-models-store` prod-bucket delete stays a human-only hard stop per
  `gcs-and-manifest-delete-safety-protocol.md` §3 regardless of how well-proven the disposition is -- whole doc stays
  NA.
- **2026-08-12 (docs-drift correction, interactive session)**: the "ml legacy variants" P1 todo's `ml-models-store` GCP
  delete already happened — via `bucket_fold_ml_2026_07_17.md`'s "Delete sources" P0 todo, `[x]` DONE 2026-08-08
  (operator authorization, NA-corpus blocker digest round 5, id=44). That doc's own text confirms the flat
  `ml-models-store` bucket is gone (project-level `gcloud asset search-all-resources` inventory, zero `ml-*` hits beyond
  the folded `ml-store-{prd,test}` targets) — the same bucket this plan's todo names. Added a dated note inline on the
  todo pointing to the sibling plan as the actual execution record; did not flip this todo's checkbox (no independent
  re-verification run this session) — left for a human/future pass to formally reconcile.
