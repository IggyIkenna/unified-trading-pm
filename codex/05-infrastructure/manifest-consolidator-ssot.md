---
doc_type: codex-ssot
title: Manifest Consolidator — SSOT
summary:
  "Canonical reference for the manifest consolidator: GCP Cloud Run Job + Cloud Scheduler (AWS Batch Fargate +
  EventBridge), one per (service_kind, asset_group), `python -m unified_trading_library.manifest_consolidator --bucket X
  --once`. Memory-bounded DuckDB merge (not pandas) with canonical-order projection + blank-capture_status drop;
  content-write-marker incremental cutoff (idle-bucket trap fix); loud-fails on stale canonical; dated-instrument
  seeding must clip to the listing window (CeFi OOM lesson)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [manifest, consolidation, infrastructure, data-correctness, single-walk, instruments]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-05-20
authoritative_for: [manifest consolidator runtime]
referenced_by:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/05-infrastructure/gcs-lifecycle-policies.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    /codex/15-runbooks/phase-2-6-bucket-name-cutover-runbook.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    plans/archive/2026_07/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    plans/epics/mtds_mdps_master.md,
  ]
owner:
last_reviewed: 2026-07-21
code_refs:
---

# Manifest Consolidator — SSOT

> **Anchor**: CLAUDE.md § "Manifest + Honest Absence". This doc is the canonical reference for the consolidator runtime,
> coverage, and operational invariants.
>
> Codified 2026-05-20 round 3 after mega-audit Phase A4 v2 finding (HYBRID runtime — legacy GCE VM + Cloud Run jobs both
> running). Operator directive: "it should just be cloud run and once per asset group I guess across all services unless
> we need them split per service for some sort of bandwidth issues though I doubt it; and in any case should cover all
> services not just MTDS and IS. Kill deprecated and the associated scripts and update SSOT docs."

## Runtime — GCP: Cloud Run + Cloud Scheduler (CANONICAL)

## Runtime — AWS: Batch Fargate + EventBridge Rules (shipped 2026-05-26)

### GCP

**Terraform**:
[deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf](../../../deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf)

**Architecture**:

- ONE Cloud Run Job per (service_kind, asset_group) pair → currently 20 Phase A jobs (10 env-tiered + 10 legacy flat);
  Phase D (14 Group B buckets) authored in TF at `deployment-service@e8e72e7`, pending `tofu apply`:
  - 5 `uts-prod-manifest-consolidator-instruments-{cefi,defi,tradfi,sports,prediction}` (env-tiered)
  - 5 `uts-prod-manifest-consolidator-market-data-{cefi,defi,tradfi,sports,prediction}` (env-tiered)
  - 10 `*-legacy` (flat no-env variants for MDPS/IS scripts still using non-env-tiered names) **[PENDING
    DECOMMISSION]**: these 10 legacy flat crons are active but targeted for pause + Terraform removal once per-AG L3
    single-walk reaches C-GREEN for every asset_group. Do NOT delete ahead of that gate — they are the fallback read
    path for any service still referencing flat bucket names.
- ONE Cloud Scheduler cron per job → 20 crons, all `*/1 * * * * (UTC)`, all ENABLED (10 env-tiered + 10 legacy flat).
- Image: `market-tick-data-service:latest` (UTL installed as dep).
- Entrypoint: `python -m unified_trading_library.manifest_consolidator --bucket {X} --once`.
- Service accounts: scheduler invoker = `t1_batch_sa`; container runtime = `unified_trading_sa` (storage.objectAdmin on
  the per-bucket prefix).
- Idempotent: skips when `_index/availability_index.parquet` already up-to-date.
- Stale canonical (blob older than `MANIFEST_CONSOLIDATED_STALENESS_SEC`, default 120s) while per-VM shards exist now
  **loud-fails by DEFAULT** (`read_availability_index` raises `ManifestConsolidatorStaleError` + emits
  `CONSOLIDATOR_STALE`); the per-VM-shard recovery merge is an opt-IN escape-hatch via
  `MANIFEST_ALLOW_STALE_FALLBACK=true`. See § "Liveness + health contract" below (2026-06-01 — supersedes the prior
  silent-fallback-by-default behaviour).

### AWS

**Terraform**:
[deployment-service/terraform/aws/manifest_consolidator_scheduler.tf](../../../deployment-service/terraform/aws/manifest_consolidator_scheduler.tf)

**Architecture**:

- ONE AWS Batch Fargate job definition per bucket → 10 Group A jobs (Phase C, 2026-05-26) + 16 Group B jobs (Phase D,
  **applied 2026-06-01**) = **26 ACTIVE job definitions**.
- ONE EventBridge **Rule** per bucket (NOT EventBridge Scheduler — ap-northeast-1 does not support Batch as a direct
  Scheduler target; switched at abdb1fb). Rules use `aws_cloudwatch_event_rule` + `aws_cloudwatch_event_target`.
  Schedule expression: `rate(1 minute)`, all ENABLED.
- Shared: 1 Batch compute environment (`uts-prod-manifest-consolidator`, Fargate) + 1 job queue.
- Image: `{account_id}.dkr.ecr.{region}.amazonaws.com/market-tick-data-service:latest` (ECR; same UTL dep)
- Entrypoint: `python -m unified_trading_library.manifest_consolidator --bucket {X} --once`
- `CLOUD_PROVIDER=aws` routes `get_storage_client()` to S3 — no Python changes required
- IAM: `unified_trading` role extended with `manifest_consolidator` S3 policy
  (GetObject/PutObject/DeleteObject/ListBucket on all 26 buckets post-Phase-D)
- Bucket naming:
  - Group A (instruments, market-data) — `unified-trading-{domain}-{category}-{account_id}` (no env suffix)
  - Group B (features, strategy, execution, ml) — flat, env-split ROLLED BACK per cloud-providers.yaml:
    `unified-trading-{kind}-{category}-{account_id}` (no env suffix). Re-enable when
    `bucket_env_split_rollout_2026_06.md` Phase 1 provisions + migrates data.
- Task timeout: 1800s (bumped from 60s default at effdcb2 — matches GCP-side bump at 03b9d22).

**Phase D status — LIVE 2026-06-01**: `terraform apply` targeted to the consolidator modules
(`module.manifest_consolidator_job_extended` + `module.manifest_consolidator_schedule_extended` +
`aws_iam_policy.manifest_consolidator`) → `64 added, 1 changed, 0 destroyed`. Targeted deliberately: the full-module
plan showed `89 add / 23 change / 17 destroy`, but the 17 destroys / 23 changes were unrelated drift in other AWS
resources; targeting kept blast radius to the 16 Group B consolidator buckets only (correct during the legacy-bucket
migration freeze). Verified: 26 EventBridge rules, all ENABLED; 26 ACTIVE Batch job definitions. Prereq:
`api_host_auto_reboot.tf` duplicate `required_providers` block fixed (deployment-service@6a4194f) — it had broken
`terraform init` for the whole AWS dir. **Note**: run terraform with the native arm64 binary
(`/opt/homebrew/bin/terraform`) on Apple Silicon — the x86 `/usr/local/bin/terraform` under Rosetta hangs on provider
plugin start.

**AWS verification**:

```bash
# Confirm rules ENABLED (10 Phase A; 26 after Phase D apply)
aws events list-rules --name-prefix uts-prod-consolidator --region ap-northeast-1 \
  --query 'Rules[].{Name:Name,State:State}' --output table

# Spot-check canonical blob freshness (mtime < 90s after first run)
aws s3 ls s3://unified-trading-market-data-defi-427895769566/_index/availability_index.parquet
```

## Merge engine — memory-bounded DuckDB (shipped 2026-05-26, `unified-trading-library@7a72049`)

The merge is **DuckDB, not pandas**. The pandas concat/sort/dedup OOM'd the 16 GiB Cloud Run job once the cefi flat
manifest reached 132M input rows (→ 75.5M deduped; pandas peaks 50-70 GB → SIGKILL). DuckDB streams parquet from local
temp files and bounds working memory via `memory_limit`.
[`manifest_consolidator.py`](../../../unified-trading-library/unified_trading_library/manifest_consolidator.py)
`_duckdb_consolidate_and_write`.

- **Incremental cycle (steady state)** — anti-join. `read_parquet('canonical')` is streamed and ANTI/SEMI-joined against
  the changed shards' dedup keys, so only contested keys are re-windowed: O(changed-shards) memory, fits 16 GiB at any
  canonical size.
- **Full / `--force` rebuild** — window dedup over canonical + all shards, then a deterministic
  `ORDER BY date, venue, data_type`. `--force` ignores the incremental mtime cutoff (one-off seed after backfill /
  schema change; for large buckets pair with a high `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` on a big-RAM host). _(Pattern
  adopted (2026-07-03): the instrument lifecycle-catalogue rollup now uses the same canonical+delta shape — prev
  `catalog.parquet` + trailing-window upsert daily, weekly `--mode full` self-heal — see
  [instruments-foundation-and-catalogue-completeness.md §4](/codex/02-data/instruments-foundation-and-catalogue-completeness.md).)_
- **`memory_limit`** = env `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` (default **8GB**), set BELOW the container so an oversized
  rebuild raises a catchable `OutOfMemoryException` instead of a kernel SIGKILL crash-loop. Anti/semi joins spill to
  `temp_directory`; the **window does NOT spill (DuckDB 1.5.x)** — so a bulk shard rewrite landing as one huge "changed"
  shard must be seeded via `--force` on a big-RAM host, not handled by the per-minute cron. Peak ≈ `memory_limit` + ~2.5
  GB Python/IO (+~1.7 GB tmpfs on Cloud Run gen2).
- **Dedup key** — base (`date, venue, data_type, service_name`) + optional dims present in the union schema,
  last-write-wins by `attempted_at` → `written_at` DESC NULLS LAST (mirrors the old pandas stable-sort + `keep="last"`).
  NULL-safe key match (coalesce-to-sentinel) for enumerator shards that omit key columns like `timeframe`/`underlying`.
- **Validated** against the real 75.5M-row cefi canonical in a hard 16 GiB cgroup: incremental ~10.5 GB peak at the 8GB
  default, 0 duplicate keys, exact key-set parity vs a full re-merge incl. the NULL-key path. **No Cloud Run memory bump
  needed.**

### UNION-ALL correctness — project to canonical column ORDER + drop blank-`capture_status` rows (2026-06-27)

Two HARD invariants on the DuckDB UNION ALL (`_duckdb_consolidate_and_write`, `unified-trading-library@6b0520a6` +
`@dd17ce23`). Violating either silently CORRUPTS the canonical.

1. **Project shard columns into canonical ORDER before the UNION ALL — never `SELECT *`.** Per-VM shards (e.g.
   instruments-service enumeration shards) carry the **same column NAMES** as the canonical but in a **different
   positional ORDER**. A plain `SELECT *` UNION ALL aligns POSITIONALLY, so every shard value lands in the wrong
   canonical slot — a column-order mismatch shifts every field right (e.g. `asset_group` leaks into the `date` column,
   `capture_status` into `job_id`). The merge MUST build each scan as an explicit projection in `union_cols` (canonical)
   order, padding absent columns with `NULL AS <col>` (the `shard_proj` / `shard_scan` / `canon_read` SQL). Applies to
   BOTH the incremental anti-join and the `--force` full-rebuild path (both read through `shard_scan`).
2. **Drop rows with blank/sub-canonical `capture_status` AT the UNION ALL so they never re-accrete.** A row whose
   `capture_status` is NOT one of the four valid states (`captured` / `empty_confirmed` / `attempted_failed` /
   `expected_unattempted`) is a stale pre-v9 placeholder (old per-VM shard or old canonical baseline) that a `SELECT *`
   merge silently carried forward, re-accreting every cycle. The `_stale_drop_predicate(union_cols)` WHERE-clause keeps
   only valid-4-state rows, applied to BOTH the shard scan AND the canonical baseline read — once a stale row is dropped
   it never returns (no honest producer re-emits a blank-status row), so consolidation is **self-healing**. The
   discriminator is **blank `capture_status` ALONE — deliberately NOT `schema_version < current`**: a blank status is
   the true stale signature, but legitimate older-schema rows (e.g. a v6 market-data row) DO carry a valid status, so
   dropping on schema would wipe them. Degrades to `TRUE` (no-op) when the manifest predates the `capture_status`
   column.

**Recovery when a deployed consolidator is on a bad image** (the fix is in UTL but the Cloud Run job runs an old
digest): pause its cron → snapshot the canonical → FORCE-REBUILD the canonical locally with fixed UTL
(`consolidate(bucket, force=True)` on a big-RAM host) → bump+rebuild the service image (or re-deploy the job to
re-resolve `:latest`) → re-enable the cron. (See § "Image deploy-hygiene" in `/codex/08-workflows/ci-cd-flow.md` — a UTL
fix does NOT reach a service image until its `BASE_IMAGE_DIGEST` is bumped + rebuilt.)

### Incremental cutoff = LAST-CONTENT-WRITE marker, NOT freshness mtime (idle-bucket trap fix, 2026-06-19)

The incremental cutoff reads a **dedicated content-write marker, separate from the freshness mtime** — the fix for the
idle-bucket starvation trap. Two GCS object-metadata markers on the canonical `_index/availability_index.parquet`:

| Marker                          | Set by                                                                         | Read by                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `consolidator_run_at`           | a real merge (`_write_consolidated`) **AND** the idle `_touch_canonical_mtime` | the READER freshness check (`_get_canonical_mtime`, 120 s threshold)               |
| `consolidator_content_write_at` | **ONLY** a real merge (`_write_consolidated`)                                  | the incremental **cutoff** + the post-merge **prune** (`_get_content_write_mtime`) |

**Why two markers.** The `*/1` cron `_touch`es `consolidator_run_at` forward on every idle cycle (so the reader's
freshness window stays valid on a bucket with no active writers). The OLD code used that same touch-advanced mtime as
the incremental cutoff. On an **idle bucket** (no concurrent capture writes), an out-of-band per-VM shard — e.g. the
expected-universe v2 enumerator's `expected_unattempted` seed (`enum-universe-v2-<ag>`), a rebuild, a finished backfill
— could be written, then `_touch`-advanced PAST by the very next idle cycle's freshness bump and **pruned as "settled"
before it ever merged** → its rows silently never reached the canonical. (Observed live 2026-06-19: `defi`/`sports`
merged within 1 cycle because captures were flowing; `cefi`/`tradfi` were idle, never merged across ~10 cycles, and
needed a manual `consolidate(bucket, force=True)`.)

The fix tracks `consolidator_content_write_at` independently: it advances ONLY when a genuine merge writes new rows, so
an idle `_touch` can no longer move the cutoff past an unmerged shard. The changed-shard predicate AND the prune cutoff
both read it. Code:
[`manifest_consolidator.py`](../../../unified-trading-library/unified_trading_library/manifest_consolidator.py)
`_get_content_write_mtime` + `_CONSOLIDATOR_CONTENT_WRITE_AT_KEY`; regression
`tests/unit/test_manifest_consolidator.py::test_idle_bucket_shard_written_after_last_merge_is_NOT_skipped` +
`::test_content_write_marker_stamped_on_real_merge_not_on_idle_touch`. Issue (RESOLVED):
`plans/active/issues/consolidator_idle_bucket_incremental_trap_2026_06_19.md`.

#### NO fallback chain — a missing marker means MERGE, never prune (2026-07-17, HARD RULE)

**There is NO fallback for the prune cutoff. It reads `consolidator_content_write_at` and NOTHING else**
(`unified-trading-library@1e995f75`). The old chain — `consolidator_content_write_at` → `consolidator_run_at` →
`blob.updated`, documented here and in the code as "a one-shot, fail-toward-correctness chain (it can only make the
cutoff OLDER … never under-includes → silent drop)" — **was WRONG and destroyed real data.** Both fallbacks resolve to
~NOW on a canonical no merge has touched:

- **`blob.updated`** — ANY out-of-band rewrite of `_index/availability_index.parquet` (a purge, a repair one-off, a
  manual `cp`/restore; the workspace has ~15 such scripts) does two things AT ONCE: it **strips** the custom metadata (a
  plain rewrite does not carry it forward) and **bumps `blob.updated` to now**. The fallback then read that unrelated
  writer's mtime as if it were a merge's shard-listing time → the cutoff jumped **FORWARD** past genuinely-pending
  shards → they were classified "unchanged → already consolidated" → the no-op branch → `_prune_consolidated_shards`
  **DELETED them unmerged**, logging `success=True rows_in=0 pruned_shards=N` and exiting 0. **Fired live 2026-07-17**
  on instruments-store-sports: 7,185 manifest rows (describing ~344k real objects) destroyed by a "successful" run; GCS
  retained **no** noncurrent versions of per_vm shards. Recovered only because the executing agent happened to have
  downloaded the shards minutes earlier.
- **`consolidator_run_at`** — the FRESHNESS marker, which the idle `_touch_canonical_mtime` re-stamps to `now()` every
  cycle. Once a strip removes both markers, the very next idle touch re-creates `run_at` at now and **re-arms the
  identical reap** through the second fallback. Closing only the `blob.updated` hole would have left this one live.

**The contract**: a missing/malformed marker means _"I cannot PROVE these shards were merged"_ — **not** _"everything
older is settled"_. `_get_content_write_mtime` returns `None` (= UNPROVABLE) and `consolidate()` fails **CLOSED**: treat
every shard as changed (**merge** it — idempotent, dedup collapses anything already present) and **prune NOTHING** (both
prune call sites are gated on `content_write_mtime is not None`). The merge re-stamps a genuine marker, so normal
incremental+prune resumes next cycle — **self-healing, one merge of cost, never a silent drop.** _Pruning is an
optimisation; merging is the contract — never trade a durability invariant for a cleanup._ The recovery merge EXCLUDES
the legacy seed (same reason the full-rebuild branch does when a canonical exists: the deletion-resurrection gap — the
out-of-band purge that strips the marker is exactly the shape whose deletions the frozen seed would undo).

**This is why out-of-band index writers do NOT each need to remember to carry the marker** (one fix beats N one-offs
remembering — a marker strip is now COST, one full merge, never LOSS). Preserving the metadata is still the polite thing
to do; relying on it is not a safety mechanism. Regressions:
`::test_out_of_band_index_rewrite_stripping_marker_does_not_reap_pending_shard` (end-to-end; models GCS's
metadata-replace + mtime-bump semantics) + `::test_get_content_write_mtime_never_falls_back_to_run_at_or_blob_updated`
(pins BOTH fallbacks). Issue:
`plans/active/issues/consolidator_content_write_marker_strip_silent_shard_reap_2026_07_17.md`.

> **Diagnostic caveat — `rows_in=0 … pruned_shards=N>0` is NOT a reliable tell of loss.** The issue doc proposed it as
> the detector; **measured 2026-07-17 it false-positives on normal steady state** (instruments-cefi:
> `13:33:39 rows_in=93995 pruned=0` → `13:34:43 rows_in=0 pruned=1` — the shard merged, settled, and was pruned
> correctly one cycle later; that merge-then-prune-next-cycle sequence IS the design). Proving a past firing requires
> knowing the pruned shard's rows never merged — and the shards are gone with no versioning, so **past firings are
> generally unprovable after the fact.** The checkable signal is the ARMING condition, not the firing: an index whose
> `custom_fields.consolidator_content_write_at` is **absent**
> (`gcloud storage objects describe gs://<bucket>/_index/availability_index.parquet --format="value(custom_fields.consolidator_content_write_at)"`
> — note `custom_fields`, NOT `metadata`, in current gcloud) while per-VM shards can land.

> **Diagnostic caveat #2 — a STATIC `rows_out` with a nonzero, fluctuating `dedup_dropped` is NOT evidence of a silent
> drop. It is the EXPECTED signature of an idempotent re-capture (2026-07-30).** `dedup_dropped` is not an independent
> measurement — `consolidate()` computes it as **`rows_in - rows_out`** (`manifest_consolidator.py`, the
> `ConsolidationReport` construction). So "`rows_out` unchanged" and "`dedup_dropped` == this cycle's shard row count"
> are the SAME fact stated twice, never two corroborating signals. A writer re-capturing cells that already exist in the
> canonical collides on the dedup key and UPDATES those rows in place; row COUNT is conserved by construction, and
> `dedup_dropped` rises with the shard purely because the shard is growing. Watching the row count therefore cannot
> distinguish "absorbing correctly" from "dropping silently".
>
> **The correct absorption test is content, not count**: capture the per-VM shard BEFORE a prune can delete it, then
> assert the canonical carries the shard rows' own `attempted_at` (or `(capture_status, row_count)`) on the SAME dedup
> key — resolving that key with the module's own `_resolve_dedup_cols()` + `_dedup_key_sql()`, never a hand-rolled key.
> Measured live 2026-07-30 on `instruments-store-sports-prd`: four consecutive merges held `rows_out=11,789,693` while
> `dedup_dropped` climbed 976→1,003→1,029→1,048 in lockstep with the shard, and 1,029/1,049 shard rows were verifiably
> already in the canonical with the shard's exact `attempted_at` — zero loss. This false signal consumed four worker
> sessions before being disproven; the actual defect was upstream, in the BACKFILL's `check_shard_freshness` smart-skip
> (which is `source`/`data_type`-blind and matches an `expected_venues` token against the `data_type` column too, so an
> unrelated pipeline's sentinel row marks a date "fresh" forever). Full account + the 2×2 proof:
> `/plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` § "Root cause (2026-07-30)".
>
> **Corollary — "the writer's log says it processed the date" is not evidence either.** Both VMs blamed in that incident
> logged **2,139 `SKIP date=… all N venues fresh` lines and exactly ONE `Processed date=`**; the investigation had read
> the skip lines as processing. Grep for `Processed date=` explicitly and COUNT it before concluding a writer produced
> anything for a range.

> **A shard's mtime is `blob.updated`, NOT `creation_time` — and a lifecycle transition moves it (2026-07-17).** Both
> `_list_per_vm_shards_with_mtime` and `_prune_consolidated_shards` read **`blob.updated`**. `gcloud storage ls -l`
> prints **`creation_time`**, so the two disagree whenever anything touches an object without rewriting it — most
> notably a **GCS lifecycle storage-class transition** (STANDARD→COLDLINE), which advances `blob.updated` with **no
> write, no content change and no metadata strip**. Measured: `instruments-store-cefi-prd`'s
> `_index/per_vm/_legacy_seed.parquet` has `creation_time=2026-05-12T17:06:19Z` but `update_time=2026-07-14T03:17:52Z`
> (`storage_class: COLDLINE`, `metageneration: 2`) — a 2-month gap. **Reading the wrong one when reasoning about a
> cutoff is a data-loss-grade error**: it made the marker-strip issue doc's interim mitigation name a stamp value that
> would have re-merged the frozen legacy seed and resurrected purged rows (caught by a pre-flight guard). Take a shard's
> effective mtime from `gcloud storage objects describe … --format="value(update_time)"`, never from `ls -l`.

> **`gcloud builds` is REGIONAL here — always pass `--region asia-northeast1` (2026-07-17).** A region-less
> `gcloud builds list` / `builds triggers list` queries the GLOBAL scope and returns an empty/stale answer that reads
> exactly like "no trigger exists / nothing built" — this produced a false "the UTL base-image republish is not
> automatic" finding. The base image IS republished automatically by the `unified-trading-library-live-defi-rollout`
> trigger, which fires on **LDR pushes (not main)**: a UTL fix reaches the base image on the quickmerge, so the MTDS
> `BASE_IMAGE_DIGEST` bump + rebuild is the only manual link in the chain (MTDS's `cloudbuild.yaml` does NOT pass
> `--build-arg BASE_IMAGE_DIGEST`, so the `Dockerfile` ARG default governs the base). Cloud Run jobs resolve `:latest` →
> digest at **execution-creation** time, so no job repin is needed after a rebuild (verified 2026-07-17: 24/24
> consolidator jobs moved to the new digest on their next `*/1` execution with zero intervention).

**schema_version preservation (ties to invariant #5)**: `union_by_name` keeps each source row's `schema_version` — the
merge never downgrades. A NULL `schema_version` in the consolidated output means the SOURCE shard omitted the column
(observed: the cefi instruments-service enumeration shards `slot4-cefi-c*-20260523`, a reduced 14-col schema also
missing `written_at`) — an enumerator-writer gap to fix upstream, NOT a consolidator downgrade. Specifically
`instruments-service/scripts/enumerate_expected_universe.py::_write_absent_rows` writes its rows via a raw
`pd.DataFrame.to_parquet` and only reindexes to the full manifest schema when an existing `manifest_df` is passed.

**Two-writer model (why instruments-service appears in a market-data manifest)**: a market-data bucket's manifest is
co-authored — **MTDS** writes the coverage NUMERATOR (`captured` rows for cells it fetched), **instruments-service**'s
expected-universe enumerator writes the DENOMINATOR (`expected_unattempted` / `empty_confirmed(EXPECTED_*)` for the full
venue × instrument × data_type × date cross-product, since only it knows the instrument lifecycle).
~~`coverage % = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`~~ — **⛔ SUPERSEDED
formula, corrected 2026-07-20, doc-reconciliation P1-09**: this is the v1 shape. The live, CK3-certified (2026-06-29)
formula is `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)` with `empty_confirmed`
**EXCLUDED** from the reachable denominator (retained in the all-shards completeness view). SSOT:
`/codex/02-data/honest-coverage-model.md` § Coverage formula; shipping implementation
`instruments-service/scripts/measure_honest_coverage.py`:600-603. instruments-service dominating the row count just
means the backfill is early (most expected cells not yet captured) — it is manifest metadata, not data, so it does not
violate "MTDS owns market data". SSOT: `/codex/02-data/availability-manifest-and-data-status.md` § "expected-universe
enumerator".

## Deprecated paths (do NOT use)

| Removed 2026-05-20                                                 | Was                                  | Why                                                                                                                                |
| ------------------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| GCE VM `manifest-consolidator-20260511-190513`                     | Long-lived poller (since 2026-05-11) | Redundant — Cloud Run does the same work via Cloud Scheduler                                                                       |
| `deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh` | Launcher for the legacy VM           | Deleted; no replacement needed (Cloud Run is auto-provisioned via Terraform)                                                       |
| `_register "manifest-consolidator"` in `launch-ec2-vm.sh`          | AWS EC2 launcher entry               | Stubbed with DEPRECATED comment; replaced by AWS Batch + EventBridge (shipped 2026-05-26 via `manifest_consolidator_scheduler.tf`) |

If a tab agent finds a NEW reference to either deprecated path, **flag as review-blocking + delete** — there is no
scenario in which the legacy VM should be relaunched.

## Coverage gap (operator directive 2026-05-20 — extend to ALL services)

> **SUPERSEDED by the Wave-3 bucket folds (2026-07-17/19)** — the per-kind / per-AG bucket axis in the table below no
> longer exists. The folds collapsed the Group B consolidator target set to the **folded** buckets, so the consolidator
> job counts dropped accordingly. Post-fold GCP consolidator targets:
>
> | Folded target     | Consolidator jobs                                                                                                        | Fold effect                                                                                                                                                                                                                                                      |
> | ----------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | `features-{ag}`   | per-AG (cefi/defi/tradfi/sports/pred) — the 5 per-kind→1 per-AG                                                          | feature consolidators **N → 5** (per-AG)                                                                                                                                                                                                                         |
> | `execution-store` | **1 single-root** (`_index/` at bucket root; asset_group → prefix)                                                       | execution consolidators **3 → 1** (operator ruling: single-root, execution not live / test data)                                                                                                                                                                 |
> | `ml-store`        | 1 (cross-asset flat)                                                                                                     | ml consolidators **2 → 1** (corrected 2026-08-10 — only `ml-training-artifacts` ever had a consolidator; the other 4 ml kinds never had one, so this is a retarget-of-1-logical-job, not 5→1; see `bucket_fold_ml_2026_07_17.md`'s own confirmed retarget sites) |
> | `strategy-store`  | 1 (cross-asset flat)                                                                                                     | unchanged (already flat)                                                                                                                                                                                                                                         |
> | `portfolio-state` | **none** — the flat position/pnl/risk trio never had a consolidator (plan-noted); no portfolio-state consolidator exists | n/a                                                                                                                                                                                                                                                              |
>
> The retarget was applied via direct `gcloud run jobs update <job> --args=…@--bucket@<folded-bucket>` (tofu-apply
> unsafe mid-fold) and verified by executing each job + checking the folded bucket's root `_index/latest.json`. The
> Cloud Scheduler `*/1` crons only trigger the jobs — the bucket lives in the JOB args, so no cron edit was needed. Job
> **renames** (e.g. `uts-prod-manifest-consolidator-execution-cefi` → `-execution`) are deferred/cosmetic (renaming a
> Cloud Run job = delete+recreate; the args already point at the folded bucket). SSOT for the fold:
> `plans/active/bucket_fold_{features,ml,execution_strategy,portfolio_state}_2026_07_17.md` +
> `bucket_fold_closeout_2026_07_17.md`. **The 2026-05-20/26 table below is retained as history** — read it for the
> pre-fold coverage-gap rationale, not the current target set.

Cloud Run currently covers 10 buckets (5 IS + 5 MTDS). Per A3 v2 finding R-NEW-1, **16 service buckets have NO
consolidated manifest**:

| Service kind          | Buckets without consolidator                     |
| --------------------- | ------------------------------------------------ |
| features-delta-one    | cefi, defi, tradfi, sports                       |
| features-volatility   | cefi, defi                                       |
| features-onchain      | defi                                             |
| features-sports       | (1)                                              |
| features-calendar     | (1)                                              |
| strategy-store        | defi, tradfi (cefi has manifest but only 7 rows) |
| execution-store       | cefi, defi, tradfi                               |
| ml-artifacts          | (1)                                              |
| ml-training-artifacts | (1)                                              |

**Status 2026-05-26**:

- **AWS Phase D**: TF authored (deployment-service@effdcb2), `terraform plan` verified. Pending `tofu apply` by operator
  (P1.10 in `plans/active/aws_manifest_consolidator_scope_2026_05_21.md`).
- **GCP Phase D**: TF authored (deployment-service@e8e72e7) — 14 buckets (strategy consolidated to 1 flat per D6 Phase
  4; AWS has 16 because strategy-cefi/tradfi/defi per-AG buckets still exist on AWS side). Pending `tofu apply` by
  operator.

**Action required** (both clouds, owner: vm-cross-cutting):

1. `tofu apply` GCP + verify 14 new Cloud Run jobs + crons land (`gcloud run jobs list --filter name~consolidator`).
2. `tofu apply` AWS + verify 26 rules ENABLED (`aws events list-rules --name-prefix uts-prod-consolidator`).
3. Re-run A3 v3 — every service has a consolidated manifest OR an explicit `BLOCKED-OPERATOR-DECISION` ack.

**Cadence question** (operator decides): should we keep `*/1 * * * *` per service kind × asset_group (currently 10 jobs
minute-by-minute = 600 invocations/hour), OR consolidate to per-asset-group only (5 jobs that each consolidate every
service kind for that asset_group)? Operator favored "once per asset_group across all services unless we need them split
for bandwidth." Recommend the consolidation since:

- Each Cloud Run invocation is ~30-90s; 5 jobs covering ~5 buckets each per minute is well under any quota.
- Reduces number of cron triggers from 10 → 5.
- Removes the artificial split between instruments + market-data.

**Implementation**: rewrite `manifest_consolidator_buckets` locals so each key is an asset_group
(cefi/defi/tradfi/sports/prediction) and the Cloud Run Job takes a list of buckets to consolidate sequentially within
one container invocation. Owner: slot 5 to design + apply.

## Coverage exemptions — `-test-` buckets are exempt by design (2026-07-10)

**`-test-` buckets are NOT wired to the consolidator scheduler on either cloud, deliberately.** GCP:
`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`'s `manifest_consolidator_buckets` /
`manifest_consolidator_buckets_extended` locals are hardcoded `for_each` map literals (built from
`local.deployment_env_short` ∈ `{dev,stg,prod}` or flat legacy literals) — zero `-test-` entries exist anywhere in the
file. AWS mirrors this gap via EventBridge Rules. The `-test-` buckets themselves ARE provisioned (27
`google_storage_bucket` resources in `main.tf`, e.g. `instruments-store-cefi-test-${var.project_id}`) — nothing else is
missing except a scheduler binding.

**Decided (not extending): document-exempt, per the real end-to-end `/data-pipeline-check-{is,mtds}` smoke-check tool**
(`data_pipeline_e2e_check_2026_07_10.md` todo 15) hitting `ManifestConsolidatorStaleError` against `-test-` buckets
during real-VM runs. Extending the scheduler would be mechanical (IAM is already project-wide — `unified_trading_sa` has
`roles/storage.objectAdmin` at the project level, so no new IAM; the Cloud Run Job + Scheduler resources are already
generic `for_each` blocks) — but it's the wrong direction given this doc's own Coverage-gap section above is actively
trying to REDUCE cron count (10 → 5) for cost/complexity reasons. Adding ~10 more permanent `*/1 * * * *` Cloud Run +
Scheduler pairs for buckets that only see occasional smoke-check traffic (never continuous production writes) moves the
wrong way.

**The actual mitigation**: `MANIFEST_ALLOW_STALE_FALLBACK=true` — an opt-in env var / VM-metadata key (wired through
`deployment-service/scripts/vm/setup-data-pipeline-vm.sh` + both `launch-{instruments,mtds}-backfill-vm.sh` launchers,
plus the `/data-pipeline-check-{is,mtds}` scripts' own local reads) that bypasses `ManifestConsolidatorStaleError` for
these buckets — a safe, bounded workaround since test buckets are always small. If a `-test-` bucket's real-world
traffic ever grows past "occasional smoke-check," re-open this as a real scheduler-extension todo rather than widening
the fallback's scope.

## Operational invariants (HARD RULES)

1. **Cloud Run is canonical**. No agent re-launches the legacy VM. No agent reintroduces
   `launch-manifest-consolidator-vm.sh`.
2. **One consolidator per env tier**. Currently only `prd` jobs exist; `dev` + `staging` consolidators must be
   deliberately provisioned + paired with corresponding bucket sets per `cloud-providers.yaml` env-tier policy.
3. **Idempotent + tolerates missed cycles, then LOUD-FAILS**. The consolidator heartbeats every cycle (incl. no-op — it
   touches the canonical mtime + emits `MANIFEST_CONSOLIDATED`). A reader tolerates up to
   `MANIFEST_CONSOLIDATED_STALENESS_SEC` of staleness; **beyond that, with other VMs' shards present,
   `read_availability_index` RAISES `ManifestConsolidatorStaleError` by default** (NOT a silent per-VM merge — see §
   "Liveness + health contract"). The silent fallback is gone; a stale consolidator is an incident, not a degraded read.
4. **Singleton per (service_kind, asset_group) job**. Cloud Run guarantees at-most-one execution per cron trigger.
   Manual `gcloud run jobs execute` invocations during operator interventions are safe (CAS on canonical blob prevents
   double-write).
5. **Per_vm shards are the source of truth for in-flight writes**. The consolidator MUST merge them into canonical
   without downgrading `schema_version` (preserve source version). A4 v2 verifies this. The DuckDB merge (§ "Merge
   engine") preserves source version via `union_by_name`; a NULL version in the output traces to a source shard that
   OMITS the column (enumerator-writer gap), not a consolidator downgrade.

## Liveness + health contract (shipped `unified-trading-library@3732ffaa`, 2026-06-01)

The consolidator is infrastructure that **must always run**. The contract makes its absence loud instead of silently
degrading reads (operator direction 2026-06-01; plan `manifest_consolidator_liveness_health_2026_06_01`).

- **Heartbeat (already existed)** — the consolidator touches the canonical `_index/availability_index.parquet` mtime and
  emits `MANIFEST_CONSOLIDATED` **every cycle, including no-op cycles** (`manifest_consolidator.py` no-op paths emit
  `{no_op}` / `{no_op_unchanged}`). So "fresh mtime" == "consolidator ran this cycle".
- **Read-path loud-fail by DEFAULT** — `read_availability_index`: a stale/missing consolidated index WHILE other VMs'
  per-VM shards exist raises `ManifestConsolidatorStaleError` + emits `CONSOLIDATOR_STALE`. The ~1700-shard per-VM
  recovery merge (12+ GB heap → OOM on cefi) is now an explicit opt-IN escape-hatch via
  `MANIFEST_ALLOW_STALE_FALLBACK=true` (inverse of the legacy opt-in `MANIFEST_FAIL_ON_STALE_FALLBACK`, which still
  forces fail-fast). A genuinely-empty bucket, and a writer-VM reading back its OWN just-written self-shard on a fresh
  bucket, are NOT outages (the `exclude_self` guard) and read normally.
- **Traced to a concrete incident, not just theoretical** — the opt-in `MANIFEST_ALLOW_STALE_FALLBACK` gap (the
  per-VM-only fallback read never sees a legacy-CAS canonical write) was confirmed as the root cause of the 2026-07-19
  sports incident; closed in practice by this loud-fail default (opt-in only) plus a 2026-08-02 fleet-wide sweep that
  gave the specific closer script `per_vm_shards=True` (`instruments-service@d0e4e5a3`) — see
  `/plans/archive/issues/sports_legacy_cas_shard_fallback_gate_investigation_2026_08_03.md`.
- **Preflight gate** — `assert_consolidator_healthy(bucket)` (exported from `unified_trading_library`): a shared SSOT
  that raises if the heartbeat is stale past `MANIFEST_CONSOLIDATED_STALENESS_SEC` while other-VM shards exist. VM
  bootstrap / batch preflight / the shell preflight in `setup-data-pipeline-vm.sh` (`deployment-service@7add531`) should
  wrap this instead of spinning their own `gsutil` stat.
- **Liveness watchdog** — `unified_trading_library.monitors.consolidator_liveness.ConsolidatorLivenessMonitor` +
  `check_buckets()` + CLI (`python -m unified_trading_library.monitors.consolidator_liveness --buckets a,b`). Per bucket
  it reads the heartbeat age and emits `CONSOLIDATOR_DOWN` (ERROR) when it misses > N cycles (default 5 × 60s),
  `CONSOLIDATOR_RECOVERED` on return. **Deployed** as its own Cloud Run Job `uts-prod-consolidator-liveness-watchdog`
  - Cloud Scheduler `uts-prod-consolidator-liveness-watchdog-cron` (`*/2 * * * *`, ENABLED) over all manifest buckets
    (`deployment-service@eb75df0`, `terraform/gcp/consolidator_liveness_scheduler.tf`). Live since 2026-06-01 —
    executions complete `1/1` every 2 min.
- **Failed-cycle alerting** — `MANIFEST_CONSOLIDATION_FAILED` is now emitted with `severity=ERROR` so the alert sink
  routes it (it was previously consumed by nothing → silent crash-loops).

Per-asset-group consolidation freshness is audited in each asset-group audit instruction (`(consolidation-health)`
item) + the engine invariant in `manifest_master_audit_instructions.md` (h2/h3/h4).

## Cockpit data-correctness signals + `_index/latest.json` run summary (WS-3, 2026-07-11)

The deployment cockpit's Consolidators tab (`deployment-api /api/health/consolidator` → `deployment-ui` Cockpit) reads
this estate through a **data-correctness lens** ("did each run PRODUCE its data?"), complementing the Deployments tab's
liveness lens. One card per (kind, asset_group), sourced from `consolidator_catalog.generated.json` (a projection of the
terraform locals via `gen_consolidator_catalog.py`, so a new consolidator auto-appears on catalog regen).

- **`_index/latest.json` — the AUTHORITATIVE self-reported run summary (SSOT for "did it produce").** Every cycle
  `manifest_consolidator.main()` overwrites `_index/latest.json` with
  `{last_run_at, verdict(produced|empty|failed), shards_scanned, shards_changed, rows_in, rows_out, rows_added, dedup_dropped, duration_ms, incremental, no_op}`
  (from the `ConsolidationReport`). Written on EVERY run — success, failure, or no-op — so `last_run_at` is a liveness
  heartbeat. Best-effort (`_write_latest_run_summary`, mirrors `_write_stall_state`): a write failure logs, never
  crashes the cycle. **A consolidator that has never run the reporting code publishes no `latest.json`** → the cockpit
  shows it as **"not reporting" (dead / not yet fired up)**, never a fabricated all-clear. All ~25 Cloud Run jobs run
  this one shared module, so a dead consolidator starts reporting the moment it is fired — zero per-job change. Shipped
  `unified-trading-library@111592eb`.
- **Verdict vocabulary** (`deployment-api` `_verdict` / `_authoritative_verdict`): `produced` · `producing` (fresh +
  absorbing a backlog) · `fired_but_empty` (a recent SUCCEEDED run — `latest.json`=empty, or the Cloud Run execution
  join — against a stale index: ran green, wrote nothing) · `stale_output` (index older than budget while shards wait) ·
  `empty` (genuinely empty bucket) · `unknown`. When `latest.json` is present its verdict is authoritative; absent, the
  endpoint derives it from index freshness + the Cloud Run execution join (`latest_execution_by_job`).
- **Per-(kind, AG) cadence staleness budget — CORRECTED 2026-07-30
  (manifest_consolidator_cadence_cost_audit_2026_07_20.md).** The "every other consolidator = 86400s" claim below was
  WRONG — it never matched the actual enforcement code. The REAL code-level override,
  `unified_trading_library.manifest_writer._staleness_budget.AG_STALENESS_BUDGET_SEC` (read by
  `read_availability_index()`/`assert_consolidator_healthy()` via `_state.py`'s `_resolve_consolidated_staleness_sec()`
  — this is the gate every REAL caller hits, not just the cockpit display), is
  `{"cefi": 86400, "sports": 1800, "defi": 3600}` (sports added 2026-07-24, defi added 2026-07-29). Every OTHER
  asset_group/bucket — tradfi, prediction, and every asset-group-less flat bucket (`strategy-store`, `execution-store`,
  `ml-store`, `features-calendar`) — falls through to the Pydantic field default of **120s**, unless the SPECIFIC
  reading process happens to export `MANIFEST_CONSOLIDATED_STALENESS_SEC` itself (set ad hoc by ~25 one-off backfill-VM
  launchers, `deployment-service/scripts/vm/launch-*-backfill-vm.sh`, all `=86400` — NOT a durable per-bucket guarantee
  for every reader, e.g. a dashboard or health check that never sets it). `deployment-api`'s cockpit-only
  `_AG_STALENESS_BUDGET_SEC` (`deployment_api/routes/health_consolidator.py`) mirrors the SAME 3-entry dict (duplicated,
  not imported — deployment-api depends on UTL, not vice versa).

  The Cloud Scheduler cron is **NO LONGER a uniform `*/1`** either (RULED 2026-07-29 "proceed", shipped 2026-07-30): 12
  of the 18 consolidator jobs (`manifest_consolidator_cadence_cost_audit_2026_07_20.md` found cost tracks INVOCATION
  COUNT, not data volume — ~$180/day on a uniform per-minute cadence) now run **hourly** (`0 * * * *`) instead of
  `*/1 * * * *`: `instruments-{cefi,tradfi,defi,prediction}`, `market-data-cefi`,
  `features-{cefi,defi,tradfi,calendar}`, `strategy`, `execution`, `ml-training-artifacts`
  (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`'s `manifest_consolidator_schedule` local). The
  4 live market-data buckets (defi/tradfi/sports/prediction) and `instruments-sports`/`features-sports` (an
  actively-written bucket at audit time) stay on `*/1`. The liveness watchdog (below) was split into a matching
  fast/slow tier pair so the hourly-cadence buckets don't false-trip `CONSOLIDATOR_DOWN` ~5min into every gap.

- **Backlog + oldest-pending** — `per_vm_shard_backlog` returns `(pending, total, oldest_pending_at)` from ONE prefix
  list: pending shards, fan-in width, and the oldest un-absorbed shard's age ("how long has the merge been behind").
- **Absolute index snapshot** — row count (cheap parquet-footer ranged read, never downloads the whole index) + file
  size.

Shipped `deployment-api@{022bfebc,1a505c16,14650f9}`, `deployment-ui@{c97a769e,368ea8e6,15832cd}`. The estate redeploy
that makes `latest.json` appear in prod is DEFERRED to the end-of-cockpit-plans deploy window; until then the endpoint +
UI degrade honestly to "not reporting". Plan: `plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md`.

## Writers: per-VM shard mode is the ONLY sanctioned standing write path (2026-07-15, HARD RULE)

A consolidator-managed bucket has exactly ONE writer of the canonical `_index/availability_index.parquet`: the
consolidator. Every standing producer (VM, Cloud Run job, cron) MUST run the ManifestWriter in per-VM shard mode
(`MANIFEST_PER_VM_SHARDS=true` + a stable `VM_NAME`) so its rows land in `_index/per_vm/{VM_NAME}.parquet` and are
absorbed by the consolidator. A legacy-mode direct canonical read-merge-write RACES the per-minute consolidator
(lost-update) **and** dedups the canonical at a COARSER key than the consolidator's schema-union key
(`_merge_dataframes` value-presence-gated optional dims vs `_resolve_dedup_cols`) — it can silently collapse rows a
finer-grained co-writer legitimately holds. Reference incident: 2026-07-15, the
`uts-prod-instruments-service-sports-fixtures` Cloud Run job (legacy-mode env) clobbered **328,292 rows (5.7%)** of the
sports IS canonical, reopening the L6/E8 data-loss gate
(`plans/active/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`).

- **Cloud Run jobs are writers too** — the four `uts-prod-sports-fixtures-*` dispatch paths + the 3
  `uts-prod-sports-enrichment-*` jobs were converted in place 2026-07-15 (`VM_NAME=sports-fixtures-job` /
  `sports-enrichment-<key>`; TF SSOT `deployment-service/terraform/gcp/sports_enrichment_provider_scheduler.tf` carries
  the env for the TF-managed set). The fixtures job itself is NOT terraform-managed — if it is ever recreated,
  `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` are REQUIRED env vars. Adding any NEW scheduled job that constructs a
  `ManifestWriter` without these env vars is review-blocking.
- **Defense-in-depth (UTL `unified-trading-library@45a43438`)**: the writer's direct canonical path now REFUSES any
  write whose merged output is >2% smaller than the base it just read (`_INDEX_SHRINK_GUARD_PCT`,
  `ManifestIndexShrinkRefusedError`, CRITICAL log + `MANIFEST_ROW_COUNT_REGRESSION` `action=write_refused`). Deliberate
  one-off maintenance rewrites opt out via `ManifestWriter(allow_index_shrink=True)` — never a standing service. The
  consolidator's own `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD` (0.1%, observability-only) is the sibling check on the
  merge side.
- **Defense-in-depth against ad-hoc-CLI OOM (UTL `unified-trading-library@74fdeeca`, 2026-07-31)**: a `ManifestWriter`
  that DOES land on the legacy CAS path (per_vm_shards not set — an interactive/ad-hoc CLI invocation, not a standing
  service) can still trigger the SAME class of unbounded-memory failure the Cloud Run job's own DuckDB path guards
  against (see "Why the OOM is unavoidable at 1 GB" below), because the legacy path's `pd.read_parquet` +
  `pd.concat`/`.drop_duplicates()` merge has NO memory cap at all. Confirmed incident: a routine single-day/single-venue
  `market-tick-data-service` capture (`AAVE-PLASMA`, 18 rows) ballooned to 44.4GB RSS on a 61GB shared host before being
  killed — root-caused to `_write_with_generation_match()`'s legacy-mode fallthrough, NOT `consolidate()` (which has
  exactly one production call site, its own Cloud Run entrypoint). Fix: `_refuse_if_legacy_read_oversized()`
  cheap-checks the canonical blob's compressed size via a metadata-only `blob.reload()` (no download) BEFORE any
  read/merge is attempted; oversized (default >200 MiB, `MANIFEST_LEGACY_READ_MAX_BYTES`) raises
  `ManifestLegacyWriteRefusedError` instead of proceeding — a REFUSE, not a truncated read (the canonical blob is fully
  overwritten on every legacy write, so a partial read would silently drop untouched rows). Escape hatches:
  `MANIFEST_LEGACY_READ_MAX_BYTES=0` (env opt-out) or `ManifestWriter(allow_oversized_legacy_write=True)` (per-writer
  force flag) for a deliberate one-off correction script — both reintroduce the original unbounded-memory risk, so
  prefer converting the writer to per-VM shard mode instead (this section's own HARD RULE) wherever the caller can. Full
  incident + fix detail: `plans/archive/issues/manifest_consolidator_inline_unbounded_memory_cli_2026_07_31.md`.
- **The per-VM shard flush is ALREADY debounced — do not re-derive an "O(n²) flush" hypothesis.**
  `unified-trading-library@6b6d53bd` (2026-06-21, "serialize per-VM shard write + coalesce per-call final into the
  debounce") added a count+time write-debounce specifically for the per-VM shard path: `_state.py`'s
  `manifest_per_vm_flush_entries` (default 50) and `manifest_per_vm_flush_interval_sec` (default 5.0s) gate how often a
  shard is actually re-uploaded, independent of the legacy CAS path's own throttle. A reader who sees frequent
  per-record `flush()` calls and suspects an unbounded per-call GCS rewrite should check these two config knobs first —
  the debounce already bounds it to at most one shard upload per 50 entries or 5.0s, whichever comes first.

## Surgical ROW REMOVAL from the canonical — a paused-consolidator CAS drop, never a force-rebuild (2026-07-20)

**A force-rebuild does NOT drop rows — a DELETION correction survives it trivially (the deletion-resurrection gap).**
`consolidate(force=True)` re-scans 100% of the canonical's CURRENT state; a row you removed from the canonical is simply
the ONLY row for its key on the next rebuild, so it survives (`manifest_consolidator.py:850-862`,
`legacy_seed_captured_outranks_resurrection_risk_2026_07_15`). Additive per-VM-shard rebuilds
(`rebuild_tradfi_manifest.py`) also can't drop — the consolidator MERGES them with the stale canonical. **The only way
to remove rows is a SURGICAL in-place rewrite of `_index/availability_index.parquet`.** The recipe (validated live on
the tradfi tick `_index`, 2026-07-20 — dropped 686,005 `batch_massive` + 3,615 disk-verified phantom rows, 5,209,585 →
4,519,965):

1. **PAUSE** the bucket's consolidator Cloud Scheduler cron
   (`gcloud scheduler jobs pause <job>-cron --location asia-northeast1`); record the resume command; verify no in-flight
   execution (no `_index/consolidator.lock`, last write settled).
2. **SNAPSHOT** the exact generation to `_index/snapshots/pre_<slug>_<ts>.parquet`
   (`gcloud storage cp <index>#<gen> <snapshot>`) — soft-delete gives a 7-day restore window on top.
3. **Re-derive the drop set against LIVE DISK, never a stale heuristic list.** A "captured with no object" list goes
   stale the moment a backfill fills a cell — a 2026-07-20 phantom list was **22% contaminated** (CME is a
   databento-native GLBX venue that genuinely holds historical tbbo/trades), so a blind drop would have deleted ~12,790
   real captured rows. Verify EACH candidate shard on disk; drop only genuinely-zero-object shards (safe
   under-approximation).
4. **Edit at the Arrow level to preserve the EXACT schema** — especially `schema_version` **int64** (do not regress
   `mtds@ac051bfe`). `pq.read_table` → boolean `.filter` → `pq.write_table`; assert `schema.equals(source)` +
   residual-drop-target == 0.
5. **CAS write** with `if_generation_match=<snapshotted gen>` (mirror `_write_consolidated`); ABORT on drift, never
   blind-overwrite. **Preserve `consolidator_content_write_at`** (keeps the next cycle a no-op) and refresh
   `consolidator_run_at`. **Gotcha, confirmed 2026-07-21**: the sanctioned CAS helpers
   (`unified_trading_library.cloud_interface.gcs_conditional_put` / the underlying
   `StorageClient.conditional_upload_bytes`) take **no `metadata` kwarg at all** — there is currently no way to carry
   the marker forward through the sanctioned write path itself. A plain CAS write via these helpers strips it every
   time, and the NEXT consolidator cycle then fails closed on the missing marker (§ above, "canonical EXISTS but carries
   no marker") — merges every per-VM shard again with pruning disabled. **Verified recovery**: immediately after your
   CAS write (same operation, don't wait for the cron), call `manifest_consolidator.consolidate(bucket, force=True)`
   yourself — this is the officially-supported write path and re-stamps the marker correctly in the same pass. Skipping
   this step measured as a real, if narrow, resurrection window: a paused-then-resumed cron's first post-edit cycle can
   transiently restore rows you just removed before a later cycle re-derives cleanly — durability-check across ≥4
   consolidator cycles after the write, not just one.

   **Correction (2026-07-26, superseding the "separate, non-blocking failure" framing this section used to carry)**:
   calling `consolidate(force=True)` directly (bypassing `manifest_consolidator.py`'s own CLI `main()`) is NOT
   automatically safe just because the CAS write already landed. **Two real failure modes measured live, both of which
   silently no-op the ENTIRE re-stamp while still returning what looks like a normal-ish report**:
   - **Missing `setup_events()` bootstrap.** `consolidate()` emits lifecycle events via `log_event()`, which raises
     `RuntimeError: Event logging not initialized` unless `setup_events()` already ran. `main()` does this bootstrap; a
     direct `consolidate()` call from a one-off script does NOT get it for free. The `RuntimeError` is caught INTERNALLY
     and returned as `success=False, shards_scanned=0, error_reason='RuntimeError: ...'` — the merge never starts at
     all, not a benign post-write log skip. A caller that only checks truthiness of the return value (or logs the report
     without checking `.success`) will believe the re-stamp worked when it did nothing.
   - **`no_op_lock=True` masquerading as success.** If another cycle (the resumed cron itself, or a concurrent caller)
     holds `_index/consolidator.lock` (`_LOCK_TTL_SECONDS=300` default), `consolidate()` skips the cycle and returns
     `success=True, shards_scanned=0, no_op_lock=True, error_reason='locked'` — `success=True` here means "no error",
     NOT "the marker was re-stamped". A caller checking only `report.success` will falsely conclude the no-op was a real
     re-stamp.
   - **Sanctioned fix, live-validated 2026-07-26** (`plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md` +
     `plans/archive/2026_07/cefi_bybit_spot_manifest_remediation_2026_07_25.md` Progress Logs): don't mirror `main()`'s
     `PubSubEventSink` bootstrap for a one-off caller — a canonical-migration VM's service account has no standing need
     for `pubsub.topics.publish` on the `lifecycle-events` topic, so that mirror hits
     `PermissionDenied: 403 ... pubsub.topics.publish` the first time anything actually calls it from that VM class. Use
     `setup_events("manifest-consolidator", mode="local")` instead (no sink, no IAM dependency, `log_event()` just logs
     locally — losing Pub/Sub-routed alerting for a one-off remediation run is a fine trade). Check
     **`report.success AND not report.no_op_lock`** before declaring the re-stamp done, and retry the no-op-lock case
     (it is a transient condition — the lock's 300s TTL means it either releases normally or a later attempt reclaims it
     as stale) rather than treating it as terminal.
     `market-tick-data-service/scripts/one_offs/ restamp_manifest_consolidator_2026_07_26.py` (Lifecycle: permanent)
     implements both fixes plus a bounded lock-contention retry loop — reuse it via
     `launch-canonical-migration-vm.sh manifest-restamp` (`RESTAMP_BUCKET= <bucket>`) rather than re-deriving this
     pattern per one-off script.

6. **RESUME** the cron; watch ≥2 cycles — a durable drop shows `verdict=empty, shards_changed=0, rows_added=0` and the
   row count holds. **Durability holds because `_legacy_seed` is EXCLUDED from every merge path once a canonical
   exists** (`manifest_consolidator.py:783` marker-strip branch, `:873-875` force branch; the incremental path never
   reaches its old mtime). Any OTHER standing per-VM shard would re-add its rows on merge, so this recipe is safe only
   when the drop target lives solely in the canonical + `_legacy_seed`. Even a marker strip is now recoverable — a
   missing `consolidator_content_write_at` fails CLOSED (merge, prune nothing), never a silent drop. SSOT for the
   finding: `plans/archive/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`.

### Pause-first applies to ANY canonical read-modify-write, not only row removal (2026-07-15 near-miss)

The 6-step recipe above was written for row _removal_, but the PAUSE-first requirement (step 1) is not specific to
deletion — it applies to **any** direct read-modify-write against `_index/availability_index.parquet`, including
in-place `capture_status` **reclassification** (floor-clip scripts, rule-based reclass scripts) that change row _values_
without changing row _count_. A reclass run races the consolidator cron exactly the same way a removal does: both are a
read-current-state → mutate → write-back against the same canonical object the cron also reads and rewrites on its own
tick.

**Near-miss precedent (2026-07-15, tradfi floor-clip)**: the 2026-07-15 run of
`instruments-service/scripts/correct_tradfi_universe_floor_clip_and_vix_index.py --apply` (reclassifying 18,980 rows —
8,959 `mbp_10` Databento-floor + 10,021 derived `ohlcv_15m` — from `expected_unattempted` to `empty_confirmed`) did a
direct canonical-index read-modify-write **without pausing** the tradfi consolidator cron
(`uts-prod-manifest-consolidator-market-data-tradfi-cron`). A post-hoc Cloud Logging phase-by-phase trace confirmed no
lost-update actually occurred — the one consolidator cycle that ran concurrently wrote its (no-net-change) canonical
version at 00:48:49Z, _before_ the script's read completed at ~00:49:02Z, and the next cycle didn't start until
00:49:35Z, _after_ the script's write completed at 00:49:28Z. **This was race-free by observed timing luck, not by an
enforced pause** — the same interleaving on a busier tick (or a longer-running reclass script) would have raced. Full
account: `plans/active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` (2026-07-15 Progress Log entry,
"Caveat (transparency, not swept under the rug)").

**Rule**: treat rule-based/additive reclassification scripts the same as a row-removal script for step 1 — PAUSE the
bucket's consolidator cron first, run the reclass, then RESUME (steps 1 and 6 of the recipe above), regardless of how
additive or purely rule-derived the reclass logic is. "The script only changes `capture_status` values, it doesn't touch
row count" is not a reason to skip the pause — the race is on the read-modify-write, not on whether rows are added or
removed.

## Composes with

- CLAUDE.md § "Manifest + Honest Absence" — every row in canonical OR per_vm shard is either `captured` /
  `empty_confirmed` (with typed reason) / `attempted_failed` / `expected_unattempted`.
- CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" — consolidator coverage gap (R-NEW-1) is a P0
  data-pipeline-correctness issue.
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — slot-freeze protocol if consolidator goes silent for >120s.
- `/codex/05-infrastructure/per-tab-worktrees.md` — per-VM shard discipline for tab worktrees writing to manifests.
- **Feed-SLA registry (2026-06-20)** — consolidator staleness is one feed in
  `/codex/03-observability/data-feed-sla-registry.md`. **Corrected 2026-07-12 (finding 205)** — was: a single blanket
  `MANIFEST_CONSOLIDATED_STALENESS_SEC` (120s) → CRITICAL rule applied uniformly to every asset_group. **Superseded** by
  a shipped per-AG override: `deployment-api@90ace9f` (`deployment_api/routes/health_consolidator.py`) added
  `_AG_STALENESS_BUDGET_SEC: dict[str, int] = {"cefi": 86400}` + `_budget_for(asset_group, default)`, wired into both
  `get_consolidator_health()` and `consolidator_posture()`. Root cause: cefi market-tick is a DAILY batch whose
  consolidator effectively runs only ~every 5 min (index age climbing 174→228s between runs), so the uniform 120s budget
  false-flagged it `degraded` ~60% of the time. Fix: cefi now gets an **86400s** budget (matching its launchers' own
  `MANIFEST_CONSOLIDATED_STALENESS_SEC` override); every OTHER asset_group keeps the **120s** default. Only the per-AG
  BUDGET changed — the escalation path is unchanged: beyond its budget a breach still loud-fails
  (`ManifestConsolidatorStaleError` / `CONSOLIDATOR_DOWN`), recovery is tracked via the autonomous-recovery matrix, and
  alert routing still uses the same `CRITICAL` → PagerDuty + Telegram channel path. The registry-keyed `refetch_action`
  pattern does NOT apply to the consolidator (it is infrastructure, not a data source, and has its own watchdog).
  **STALE as of 2026-07-30 — see the corrected § above** ("Per-(kind, AG) cadence staleness budget"): sports (1800s,
  2026-07-24) and defi (3600s, 2026-07-29) have SINCE gained their own code-level overrides too, so "every OTHER
  asset_group keeps the 120s default" no longer holds for those two — only tradfi/prediction/the flat Group-B buckets
  still fall through to 120s (absent a reader-side env override). Kept this entry's original 2026-07-12 finding intact
  above (historically accurate at the time) rather than rewritten, per this doc's own dated-finding convention.

## Verification recipe

```bash
# 1. List active consolidator Cloud Run jobs (expect 20 currently: 10 env-tiered + 10 legacy flat;
#    target 10 env-tiered only after legacy flat crons are decommissioned post-L3 C-GREEN).
gcloud run jobs list --region asia-northeast1 --filter="name~consolidator" --format="value(name)"

# 2. Confirm all crons enabled.
gcloud scheduler jobs list --location asia-northeast1 --filter="name~consolidator" --format="value(name,state,schedule)"

# 3. Confirm NO legacy VM running.
gcloud compute instances list --filter="name~manifest-consolidator" --format="value(name,status)"
# Expected: zero rows.

# 4. Recent execution health.
for job in $(gcloud run jobs list --region asia-northeast1 --filter="name~consolidator" --format="value(name)"); do
  echo "── ${job}"
  gcloud run jobs executions list --job="${job}" --region asia-northeast1 --limit 3 --format="value(name,startTime,completionStatus)"
done
```

If any check fails: ping `plans/active/_agent_pings.md` cross-side + freeze layer-N+1 slots per the data-correctness
HARD RULE until restored.

---

## Dated-instrument seeding bloat — diagnosis + fix (CeFi lesson 2026-06-24)

> **Source**: `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` § "Manifest consolidator FROZE" + fixed
> at `market-tick-data-service@7b18433b`.

### What happened

The per-VM shard writer (`cefi_catalog_reader._iter_not_yet_listed`) emitted `EXPECTED_INSTRUMENT_NOT_LISTED` manifest
rows for every dated instrument (OPTION / FUTURE) across the instrument's **entire theoretical listing window** —
including pre-listing dates before the instrument actually existed. These are valid rows for SPOT/PERP (a live
instrument that wasn't observed yet is genuinely `expected_unattempted`), but OPTION and FUTURE instruments only exist
in a narrow dated window: over-seeding them across the full range creates phantom rows for dates where the instrument
could never have existed.

CeFi numbers (June 2026):

| Metric                                         | Value   |
| ---------------------------------------------- | ------- |
| Total shard rows (per-VM)                      | 49.7M   |
| `EXPECTED_INSTRUMENT_NOT_LISTED` phantom cells | 44.2M   |
| Rows with **blank `instrument_type`**          | 43.9M   |
| Deribit alone (options + inverse perps)        | 36.3M   |
| Canonical index size at OOM point              | 1.02 GB |
| Canonical index size after clean rebuild       | 137 MB  |

### Why the OOM is unavoidable at 1 GB

The consolidator runs on Cloud Run (GCP) with a **hard ceiling of 32 Gi RAM / 8 vCPU** — there is no larger instance
class available. A 1 GB canonical parquet loaded via DuckDB with sorting + deduplication + merge requires far more than
32 Gi working memory. Critically:

- **`--force` full-rebuild path OOM'd** (exit 137 / signal 9) — cannot hold the full canonical in memory for a cold
  rebuild.
- **Incremental path also OOM'd** — even loading the canonical for a delta merge exceeded the ceiling.

The consolidator cannot be scaled vertically. The ONLY fix is to keep the canonical small.

### Diagnosis signals

1. **Index frozen**: the consolidated `_index/` GCS object's mtime is not advancing across consolidator execution ticks
   — the job is running but the canonical is not being written (OOM before the write).
2. **Exit 137 / signal 9** in Cloud Run execution logs
   (`gcloud run jobs executions describe <name> --region asia-northeast1 --format=json | jq '.status.conditions'`).
3. **Disproportionate shard row count vs captured rows**: `attempted_failed` + `captured` rows are small, but total
   shard rows are orders of magnitude larger — the difference is phantom seeding.

### Fix sequence (verified 2026-06-24)

1. **Clip the seeding** — `cefi_catalog_reader._iter_not_yet_listed` must skip
   `_DATED_INSTRUMENT_TYPES = {InstrumentType.FUTURE, InstrumentType.OPTION}`. Dated instruments exist only within a
   narrow window and are handled by the `NOT_YET_LISTED` handler only for the specific date range they appear in the
   live catalogue (not across their full theoretical range). Fix shipped as `market-tick-data-service@7b18433b`.

2. **Purge bloated per-VM shards** — delete all existing per-VM manifest shard files for the asset_group:

   ```bash
   gsutil -m rm "gs://manifest-store-{env}/{asset_group}/shards/**"
   ```

3. **Purge the bloated canonical** — delete the existing `_index/` canonical parquet:

   ```bash
   gsutil rm "gs://manifest-store-{env}/{asset_group}/_index/manifest_consolidated.parquet"
   ```

4. **Cold `--force` rebuild** — deploy the clipped code + re-run the consolidator with `--force`. Because the shards are
   now empty (step 2), the rebuild is fast and the resulting canonical is lean (~137 MB for CeFi).

5. **Revert to incremental** — once the canonical is lean, downsize the Cloud Run job back to 16 Gi / 4 cpu and run
   normally. The 32 Gi / 8 cpu sizing is not needed (and not sustainable) for a lean canonical.

### Prevention

- **Any new shard writer that seeds `expected_unattempted` or `EXPECTED_INSTRUMENT_NOT_LISTED` for a dated instrument
  type MUST restrict seeding to the instrument's actual listing window** — never across a theoretical range.
- Watch the canonical size in the verification recipe (step 4): if it exceeds ~300 MB, investigate phantom row counts in
  per-VM shards before the OOM recurs.
- `DATED_INSTRUMENT_TYPES` seeding exemption is enforced by code review — see the `_DATED_INSTRUMENT_TYPES` constant in
  `cefi_catalog_reader.py` and its guard at the top of `_iter_not_yet_listed`.
