# Manifest Consolidator — SSOT

> **Anchor**: CLAUDE.md § "Manifest + Honest Absence". This doc is the canonical reference for the consolidator runtime,
> coverage, and operational invariants.
>
> Codified 2026-05-20 round 3 after mega-audit Phase A4 v2 finding (HYBRID runtime — legacy GCE VM + Cloud Run jobs both
> running). Operator directive: "it should just be cloud run and once per asset group I guess across all services unless
> we need them split per service for some sort of bandwidth issues though I doubt it; and in any case should cover all
> services not just MTDS and IS. Kill deprecated and the associated scripts and update SSOT docs."

## Runtime — GCP: Cloud Run + Cloud Scheduler (CANONICAL)

## Runtime — AWS: Batch Fargate + EventBridge Scheduler (shipped 2026-05-26)

### GCP

**Terraform**:
[deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf](../../../deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf)

**Architecture**:

- ONE Cloud Run Job per (service_kind, asset_group) pair → currently 10 jobs:
  - 5 `uts-prod-manifest-consolidator-instruments-{cefi,defi,tradfi,sports,prediction}`
  - 5 `uts-prod-manifest-consolidator-market-data-{cefi,defi,tradfi,sports,prediction}`
- ONE Cloud Scheduler cron per job → 10 crons, all `*/1 * * * * (UTC)`, all ENABLED.
- Image: `market-tick-data-service:latest` (UTL installed as dep).
- Entrypoint: `python -m unified_trading_library.manifest_consolidator --bucket {X} --once`.
- Service accounts: scheduler invoker = `t1_batch_sa`; container runtime = `unified_trading_sa` (storage.objectAdmin on
  the per-bucket prefix).
- Idempotent: skips when `_index/availability_index.parquet` already up-to-date.
- Tolerates one missed cycle — `read_availability_index` reader falls back to per-VM-shard merge when canonical blob is
  older than `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default 120s).

### AWS

**Terraform**:
[deployment-service/terraform/aws/manifest_consolidator_scheduler.tf](../../../deployment-service/terraform/aws/manifest_consolidator_scheduler.tf)

**Architecture**:

- ONE AWS Batch Fargate job definition per bucket → currently 10 Group A jobs (Phase C, 2026-05-26); 16 Group B (Phase
  D) authored in TF at `deployment-service@effdcb2`, pending `tofu apply`.
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

**Phase D status (2026-05-26)**: TF authored (deployment-service@effdcb2), `terraform plan` verified (89 add / 23 change
/ 17 destroy). Pending `tofu apply` by operator (P1.10 in `plans/active/aws_manifest_consolidator_scope_2026_05_21.md`).

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
  schema change; for large buckets pair with a high `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` on a big-RAM host).
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
`coverage % = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`. instruments-service
dominating the row count just means the backfill is early (most expected cells not yet captured) — it is manifest
metadata, not data, so it does not violate "MTDS owns market data". SSOT:
`codex/02-data/availability-manifest-and-data-status.md` § "expected-universe enumerator".

## Deprecated paths (do NOT use)

| Removed 2026-05-20                                                 | Was                                  | Why                                                                                                                                |
| ------------------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| GCE VM `manifest-consolidator-20260511-190513`                     | Long-lived poller (since 2026-05-11) | Redundant — Cloud Run does the same work via Cloud Scheduler                                                                       |
| `deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh` | Launcher for the legacy VM           | Deleted; no replacement needed (Cloud Run is auto-provisioned via Terraform)                                                       |
| `_register "manifest-consolidator"` in `launch-ec2-vm.sh`          | AWS EC2 launcher entry               | Stubbed with DEPRECATED comment; replaced by AWS Batch + EventBridge (shipped 2026-05-26 via `manifest_consolidator_scheduler.tf`) |

If a tab agent finds a NEW reference to either deprecated path, **flag as review-blocking + delete** — there is no
scenario in which the legacy VM should be relaunched.

## Coverage gap (operator directive 2026-05-20 — extend to ALL services)

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

**Status 2026-05-26**: AWS Phase D TF authored (deployment-service@effdcb2) covering all 16 buckets in the table above.
GCP extension TF not yet authored — still pending.

**Action required** (GCP-side, owner: vm-cross-cutting):

1. Verify each missing service actually emits manifest rows (some may write raw parquets without
   `_index/per_vm/<vm>.parquet` shards — in which case no consolidator needed).
2. For services that DO emit: extend `manifest_consolidator_buckets` locals in the GCP Terraform with the missing
   entries (same pattern as the AWS Phase D block).
3. Add per-bucket timeout overrides if shard count is high.
4. `tofu apply` (or `terraform apply`) + verify the new Cloud Run jobs + crons land.
5. Re-run A3 v3 — every service has a consolidated manifest OR an explicit `BLOCKED-OPERATOR-DECISION` ack.

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

## Operational invariants (HARD RULES)

1. **Cloud Run is canonical**. No agent re-launches the legacy VM. No agent reintroduces
   `launch-manifest-consolidator-vm.sh`.
2. **One consolidator per env tier**. Currently only `prd` jobs exist; `dev` + `staging` consolidators must be
   deliberately provisioned + paired with corresponding bucket sets per `cloud-providers.yaml` env-tier policy.
3. **Idempotent + tolerates missed cycles**. The reader fallback (UTL `read_availability_index`) handles up to 120s of
   consolidator staleness; anything longer surfaces as a freshness alert in deployment-ui.
4. **Singleton per (service_kind, asset_group) job**. Cloud Run guarantees at-most-one execution per cron trigger.
   Manual `gcloud run jobs execute` invocations during operator interventions are safe (CAS on canonical blob prevents
   double-write).
5. **Per_vm shards are the source of truth for in-flight writes**. The consolidator MUST merge them into canonical
   without downgrading `schema_version` (preserve source version). A4 v2 verifies this. The DuckDB merge (§ "Merge
   engine") preserves source version via `union_by_name`; a NULL version in the output traces to a source shard that
   OMITS the column (enumerator-writer gap), not a consolidator downgrade.

## Composes with

- CLAUDE.md § "Manifest + Honest Absence" — every row in canonical OR per_vm shard is either `captured` /
  `empty_confirmed` (with typed reason) / `attempted_failed` / `expected_unattempted`.
- CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" — consolidator coverage gap (R-NEW-1) is a P0
  data-pipeline-correctness issue.
- `codex/02-data/data-pipeline-correctness-hard-rule.md` — slot-freeze protocol if consolidator goes silent for >120s.
- `codex/05-infrastructure/per-tab-worktrees.md` — per-VM shard discipline for tab worktrees writing to manifests.

## Verification recipe

```bash
# 1. List active consolidator Cloud Run jobs (expect 10 currently, target 5 post-consolidation).
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
