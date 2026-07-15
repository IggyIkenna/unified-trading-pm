---
doc_type: issue
title:
  "features-onchain bare bucket (gs://features-onchain-central-element-323112) does NOT fit the assigned cefi/defi
  asset-group migration pattern — its only content (16 objects) is a live personal cross-sectional on-chain-netflow
  research + trading-sleeve harness (e2e-testing/scripts/onchain/), not legacy production feature-store shards;
  migrating/deleting would pollute the canonical siblings and can break a live consumer"
summary:
  'Dispatched sub-task under plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md (Wave-3 fold / features-*
  flat-bucket migrate phase), bucket pair features-onchain: bare gs://features-onchain-central-element-323112 ->
  canonical features-onchain-{cefi,defi}-central-element-323112. Diff phase (prior agent) + this session''s live
  re-verification (gcloud storage ls -r on the bare bucket, gcloud storage buckets describe, grep of the referencing
  repo) agree: all 16 objects (70,768,303 bytes, matches the pre-known figure exactly) live under ONE prefix,
  `netflow_xsec_research/` — 7 parquet research datasets, a live `_dune_sleeve_ledger.csv`/`_dune_sleeve_state.json`
  trading-sleeve ledger/state, 4 PNGs, and a 301KB STRATEGY_STATE.md. There is NO `by_date=`/`asset_group=`/
  `pipeline_mode=` hive partitioning anywhere, i.e. no asset_group signal to classify by — structurally incompatible
  with the canonical features-onchain-{cefi,defi} siblings (which only contain `_index/`[+`by_date/` for defi]
  production manifest+feature partitions, zero prefix overlap confirmed). Content is confirmed to be the operator''s
  personal research playground (moved here 2026-06-20 per e2e-testing/scripts/onchain/README.md) plus a LIVE
  cross-sectional on-chain-netflow trading sleeve — e2e-testing/scripts/onchain/{README.md, gcs_sync.py,
  _dune_sleeve_deploy.py} hardcode this exact bare bucket+prefix as the documented "Data SSOT" (gcs_sync.py:22 `BUCKET =
  "gs://features-onchain-central-element-323112/netflow_xsec_research"`; README.md:6 same path as "Data SSOT"), and this
  session re-confirmed those 3 references are still present verbatim in the live checkout (2026-07-15). No
  migrate/delete was executed this session (diagnostic-only, per this repo''s findings-triage HARD RULE: a big finding —
  data-correctness / cross-repo / SSOT contradiction — routes to operator notification + an issue doc, not a unilateral
  mechanical migration).'
status: resolved
nature: issue
asset_group: [defi, cefi]
stage: [data, meta]
repos: [deployment-service, e2e-testing, execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [gcs, buckets, features-onchain, legacy-bucket-migration, data-correctness, live-consumer, operator-decision]
related:
  [../bucket_estate_consolidation_to_sub100_2026_07_13.md, ../../archive/2026_05/bucket_env_split_rollout_2026_06.md]
created: "2026-07-15"
parent_epic: infrastructure_master
priority: P1
source:
  "Dispatched sub-agent task, 2026-07-15: 'Migrate phase' for the features-onchain bucket pair under the
  bucket-estate-consolidation plan's flat-bucket migration sweep (features-*, instruments-store-*, market-data-tick-*
  legacy flat buckets -> canonical form -> delete). Diff phase (prior agent, same dispatch chain) already flagged this
  bucket as NOT fitting the assigned pattern; this doc formalizes that finding for operator ruling before any
  apply-phase action is taken."
assigned_vm: NA
resolved_by: "2026-07-15 execute-phase sub-agent (Option A)"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# features-onchain bare bucket is not an asset-group-classifiable migration target

## Finding

`gs://features-onchain-central-element-323112` (the bare/flat bucket named in the bucket-estate consolidation plan's
features-onchain migration pair) contains exactly 16 objects, ALL under one prefix `netflow_xsec_research/`:

```
netflow_xsec_research/STRATEGY_STATE.md                              (301 KB)
netflow_xsec_research/data/btc_netflow_by_cex.parquet
netflow_xsec_research/data/btc_netflow_netted_multiyear.parquet
netflow_xsec_research/data/evm_hourly_netflow.parquet
netflow_xsec_research/data/evm_hourly_prices.parquet
netflow_xsec_research/data/evm_universe_bycex.parquet
netflow_xsec_research/data/evm_v2_netflow.parquet
netflow_xsec_research/data/evm_v2_prices.parquet
netflow_xsec_research/live/_dune_sleeve_ledger.csv
netflow_xsec_research/live/_dune_sleeve_state.json
netflow_xsec_research/netflow_granular_cadence.png
netflow_xsec_research/plots/netflow_evm_sleeve.png
netflow_xsec_research/plots/netflow_granular_cadence.png
netflow_xsec_research/plots/netflow_portfolio.png
netflow_xsec_research/plots/netflow_sleeve_pnl.png
```

Total 70,768,303 bytes — matches the pre-known ~70.7MB figure exactly (re-verified live via
`gcloud storage ls -r "gs://features-onchain-central-element-323112/**"` on 2026-07-15).

This does not fit the assigned migration pattern ("classify each object by its real asset_group and route to the
matching cefi/defi flat bucket") because:

1. **No asset_group signal exists.** There is no `by_date=`/`asset_group=`/`pipeline_mode=` hive partitioning anywhere
   in this bucket — the canonical siblings `features-onchain-{cefi,defi}-central-element-323112` only contain `_index/`
   (+`by_date/` for defi) production manifest+feature partitions, with zero prefix overlap against
   `netflow_xsec_research/`.
2. **The content is not production feature-store data at all.** It is the operator's personal cross-sectional
   on-chain-netflow research playground ("moved here from the .tabs/1 research playground, operator 2026-06-20" per
   `e2e-testing/scripts/onchain/README.md`), plus a LIVE cross-sectional netflow trading sleeve
   (`_dune_sleeve_ledger.csv` / `_dune_sleeve_state.json` / `_dune_sleeve_deploy.py` = "the live position emitter (the
   deployable)").
3. **There is a live, still-referenced consumer.**
   `e2e-testing/scripts/onchain/{README.md, gcs_sync.py, _dune_sleeve_deploy.py}` hardcode this exact bare bucket +
   prefix as the documented "Data SSOT":
   - `gcs_sync.py:22` — `BUCKET = "gs://features-onchain-central-element-323112/netflow_xsec_research"`
   - `README.md:6` — `` `gs://features-onchain-central-element-323112/netflow_xsec_research/` `` labeled "Data SSOT"
     Re-confirmed live in the checkout on 2026-07-15 (both references still present verbatim).

Blind-copying these 16 objects into `features-onchain-cefi`/`features-onchain-defi` would pollute the canonical
production feature-store buckets with unrelated personal research/trading-sleeve files (wrong shape, no asset_group to
route by). Deleting the bare bucket without first repointing the e2e-testing scripts would break a live, still-updated
(files touched as recently as 2026-07-05 per the diff-phase agent) personal quant trading sleeve.

## Secondary (non-blocking) findings, same bucket

- `execution-service/execution_service/utils/dependency_checker.py:242-246` hardcodes
  `bucket_template="features-onchain-{project_id}"` + `path_template="by_date/day={date}/"`, `required=False`. Since
  `by_date/` no longer exists in this bucket (production onchain feature data was already migrated to the cefi/defi
  split), this check is a permanent silent no-op — same bug-class as the features-service DEFI dependency-checker
  landmine already fixed elsewhere in the parent plan. Non-blocking (not `required`), but worth a follow-up repoint.
- `execution-service/execution_service/service_config.py`'s `features_onchain_source_bucket` field (env aliases
  `FEATURES_ONCHAIN_GCS_BUCKET`/`FEATURES_ONCHAIN_BUCKET`) has zero consumers workspace-wide (grep-clean) — genuinely
  dead. `e2e-testing/configs/defi/local-{live,batch,paper}.env` setting
  `FEATURES_ONCHAIN_BUCKET=features-onchain-central-element-323112` feeds only this dead field.
- No terraform `google_storage_bucket` resource manages the bare bucket anywhere in `deployment-service/terraform/**`
  (`canonical_buckets.tf`'s `for_each` only emits `features-onchain-{cefi,defi}-{pid}` per `cloud-providers.yaml`, which
  has no bare/shared key for this kind) — so no terraform/state surgery is needed for this bucket regardless of which
  path below is chosen.

## What was NOT done this session

No object copy, no bucket delete, no manifest write, and no code change were made. This is diagnostic only — the task's
own dispatch instructions state "If you find yourself about to touch any of these, STOP" for a list of
deliberately-excluded buckets, and while `features-onchain` bare is not on that literal list, the same STOP-and-verify
posture applies once the diff/migrate phase itself contradicts the assigned pattern: this is a "big finding"
(data-correctness / cross-repo / SSOT contradiction) under the workspace findings-triage HARD RULE, which routes to
operator notification + an issue doc, not a unilateral mechanical migration.

## Operator decision needed

A: **Relocate + repoint [WORKER REC].** Move `netflow_xsec_research/` into a dedicated, differently-named research/ops
bucket (e.g. a new `{pid}-onchain-research` or similar, registered in the infra bucket list alongside the other
ops-tooling singletons this same plan already registered), repoint
`e2e-testing/scripts/onchain/{README.md, gcs_sync.py}` (and `_dune_sleeve_deploy.py` if it also reads the path) at the
new location, verify the live sleeve still reads/writes correctly, THEN delete the empty bare
`features-onchain-central-element-323112` bucket and drop the now-fully-dead
`execution-service/execution_service/utils/dependency_checker.py:242-246` check +
`service_config.py.features_onchain_source_bucket` field + the `e2e-testing` env-file lines that feed it.

B: **Exclude from this migration, leave as-is.** Treat `features-onchain` bare as out of scope for the features-*
cefi/defi-split migration entirely (its content was never part of the asset-group split to begin with) — leave the
bucket and the live e2e-testing consumer untouched, possibly re-key it under a different `cloud-providers.yaml` kind
name later (own follow-up item) so it stops appearing as an "unregistered flat legacy bucket" in future estate audits.

C: **Delete the dead code paths only, defer the bucket itself.** Ship the two non-blocking dead-code fixes
(dependency_checker.py silent no-op, service_config.py dead field + env-file lines) now since they carry no data risk,
and leave the bare-bucket relocate-or-exclude decision (A vs B) for later.

Other: operator can specify a different path (e.g. a different destination bucket name/kind).

## Resolution (2026-07-15, execute phase — Option A)

Operator ruled **Option A**. A prior session provisioned the destination (`onchain-research-central-element-323112`,
registered as kind `onchain-research` in `deployment-service/configs/bucket_config.yaml`'s `infrastructure_buckets.gcp`
list — `deployment-service@45c9924b`) and confirmed no live automated GCS writer races the bucket. This session executed
the remainder:

1. **Copy** — all 16 objects (70,768,303 bytes) copied `netflow_xsec_research/` -> the new bucket via UTL
   `gcs_copy_object` (server-side rewrite; no `gsutil`/`gcloud` subprocess). Every object individually verified
   size+crc32c match post-copy.
2. **Verify** — both live sleeve files (`_dune_sleeve_ledger.csv`, `_dune_sleeve_state.json`) byte-diffed src-vs-dst
   (not just crc32c) twice — immediately post-copy and again as the final pre-delete gate — bit-for-bit identical both
   times. Total corpus byte-count (`gcloud storage du -s`) matched on both sides throughout.
3. **Repoint** — `e2e-testing/scripts/onchain/gcs_sync.py` (docstring + `BUCKET` constant) and `README.md` (Data SSOT
   line) repointed to `gs://onchain-research-central-element-323112/netflow_xsec_research`. `_dune_sleeve_deploy.py`
   re-confirmed to need no change (zero `gs://`/bucket-name references). Proved the repointed script works end-to-end:
   ran `gcs_sync.py pull` then `gcs_sync.py push` live against the new bucket (idempotent, corpus unchanged). Shipped
   `e2e-testing@a4f8bdc6` via `quickmerge --agent --files`.
4. **Terraform/config check** — confirmed (again, independently) zero terraform resource ever managed the bare bucket
   and zero remaining bare-name references in `bucket_config.yaml`/`cloud-providers.yaml`/VM-launcher scripts — no
   `terraform state rm` needed.
5. **Delete** — `gcloud storage rm --recursive --continue-on-error` then `gcloud storage buckets delete --quiet` on
   `gs://features-onchain-central-element-323112`. Post-delete `gcloud storage buckets describe` returns `404`; the new
   bucket independently re-verified intact (70,768,303 bytes / 16 objects) after the source delete.

**Deliberately NOT done this session** (Option A's secondary dead-code cleanup — a distinct, lower-risk follow-up, not
required to safely relocate+delete the bucket): the 3 `e2e-testing/configs/defi/local-{live,batch,paper}.env`
`FEATURES_ONCHAIN_BUCKET=` lines, `execution-service/execution_service/service_config.py`'s
`features_onchain_source_bucket` field, and `dependency_checker.py`'s `features-onchain` bucket-template entry remain —
these feed a confirmed-dead code path (zero real consumers) and are safe to delete independently of this bucket's
lifecycle. **Open follow-up**: file/track a small cleanup touch for these 3 dead references (incl. regenerating the
mirrored `unified-api-contracts/openapi/config-registry.json` copies if the `service_config.py` field is removed).

Full narrative + evidence: see the Progress Log entry dated 2026-07-15 ("operator ruling executed (Execute phase)") in
`../bucket_estate_consolidation_to_sub100_2026_07_13.md`.
