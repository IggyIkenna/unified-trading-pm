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
    /plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
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
      scheduled run green; wire Cloud Run failure alerting (55 silent failures).
- [ ] [DATA] P0. Track to completion the deletions OWNED BY OTHER PLANS (checkpoint; UPDATED 2026-07-25 — was:
      "dex-pools-prd purge-lifecycle armed (24h async; disarm window if concerns)", stale vs. the sibling plan's more
      final status, corrected per `defi_dedicated_bucket_shared_migration_2026_07_13.md`:221-224: DeFi trio — parity
      re-verified by agent incl. closing a 6,941-object gap, all 3 of lst-rates-prd/perp-funding-prd/dex-pools-prd
      CONFIRMED DELETED (`gcloud storage buckets list`, zero matches in any form, 2026-07-14) — dex-pools-prd was
      deleted directly by the operator on 2026-07-14T11:03:47Z, BEFORE that todo's own snapshot-before-delete step ran
      (not via the planned 24h purge-lifecycle path; no independent pre-delete object-diff of the ~209k-object legacy
      tree exists — risk assessed low, not zero, per the sibling plan's own writeup), kinds removed from all 5 yaml
      copies (34), TF state clean; L6 twins — cefi/defi/tradfi tick+instruments purge-lifecycle armed (sports pair HELD
      for sports-plan E1/E8; bucket deletes = follow-up one-liner once purged); lending pair still HELD — Morpho VM
      completed but write-target verification inconclusive): `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` (−3,
      [[defi_dedicated_bucket_shared_migration_2026_07_13]] todos 6-9 incl. the TF-resource removal added 2026-07-13);
      `lending-indices`+`-prd` (−2, same plan / estate cleanup §5i, gated on VM `mtds-lending-indices-20260712-112557`
      completion); legacy flat tick+instruments twins (−8, M-1 `data_completion_to_100_all_ag_2026_06_21` L6,
      operator-gated version-aware deletes — millions of noncurrent versions).
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
      sunset per the todo below). Left `- [ ]` deliberately — see notes.

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
- [ ] [DOCS] P3. **Close (or re-confirm still-open) the three bucket-SSOT audit issue docs** referenced by the
      codex-audit todo above — assessed during that audit and deliberately left open rather than closed by the fold;
      re-verify their current status before closing.

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
  - **Bash/tooling note**: this session hit a transient shared-host `/tmp` tmpfs exhaustion (2GB tmpfs, other concurrent
    agents' sessions) that blocked all Bash calls for a stretch — recovered on its own; no workaround was needed beyond
    waiting + continuing read-only (Read-tool) investigation in the meantime. Flagging in case it recurs for another
    slot.
