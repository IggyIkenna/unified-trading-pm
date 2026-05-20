# Manifest Consolidator — SSOT

> **Anchor**: CLAUDE.md § "Manifest + Honest Absence". This doc is the canonical
> reference for the consolidator runtime, coverage, and operational invariants.
>
> Codified 2026-05-20 round 3 after mega-audit Phase A4 v2 finding (HYBRID
> runtime — legacy GCE VM + Cloud Run jobs both running). Operator directive:
> "it should just be cloud run and once per asset group I guess across all
> services unless we need them split per service for some sort of bandwidth
> issues though I doubt it; and in any case should cover all services not just
> MTDS and IS. Kill deprecated and the associated scripts and update SSOT docs."

## Runtime — Cloud Run + Cloud Scheduler (CANONICAL)

**Terraform**: [deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf](../../../deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf)

**Architecture**:

- ONE Cloud Run Job per (service_kind, asset_group) pair → currently 10 jobs:
  - 5 `uts-prod-manifest-consolidator-instruments-{cefi,defi,tradfi,sports,prediction}`
  - 5 `uts-prod-manifest-consolidator-market-data-{cefi,defi,tradfi,sports,prediction}`
- ONE Cloud Scheduler cron per job → 10 crons, all `*/1 * * * * (UTC)`, all ENABLED.
- Image: `market-tick-data-service:latest` (UTL installed as dep).
- Entrypoint: `python -m unified_trading_library.manifest_consolidator --bucket {X} --once`.
- Service accounts: scheduler invoker = `t1_batch_sa`; container runtime =
  `unified_trading_sa` (storage.objectAdmin on the per-bucket prefix).
- Idempotent: skips when `_index/availability_index.parquet` already up-to-date.
- Tolerates one missed cycle — `read_availability_index` reader falls back
  to per-VM-shard merge when canonical blob is older than
  `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default 120s).

## Deprecated paths (do NOT use)

| Removed 2026-05-20 | Was | Why |
|---|---|---|
| GCE VM `manifest-consolidator-20260511-190513` | Long-lived poller (since 2026-05-11) | Redundant — Cloud Run does the same work via Cloud Scheduler |
| `deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh` | Launcher for the legacy VM | Deleted; no replacement needed (Cloud Run is auto-provisioned via Terraform) |
| `_register "manifest-consolidator"` in `launch-ec2-vm.sh` | AWS EC2 launcher entry | Stubbed with DEPRECATED comment; AWS-side consolidation (if needed) requires a new Lambda+EventBridge plan (not currently in scope) |

If a tab agent finds a NEW reference to either deprecated path, **flag as
review-blocking + delete** — there is no scenario in which the legacy VM
should be relaunched.

## Coverage gap (operator directive 2026-05-20 — extend to ALL services)

Cloud Run currently covers 10 buckets (5 IS + 5 MTDS). Per A3 v2 finding
R-NEW-1, **16 service buckets have NO consolidated manifest**:

| Service kind | Buckets without consolidator |
|---|---|
| features-delta-one | cefi, defi, tradfi, sports |
| features-volatility | cefi, defi |
| features-onchain | defi |
| features-sports | (1) |
| features-calendar | (1) |
| strategy-store | defi, tradfi (cefi has manifest but only 7 rows) |
| execution-store | cefi, defi, tradfi |
| ml-artifacts | (1) |
| ml-training-artifacts | (1) |

**Action required** (owner: slot 5, paired with R6 + R-NEW-1):

1. Verify each missing service actually emits manifest rows (some may write
   raw parquets without `_index/per_vm/<vm>.parquet` shards — in which case
   no consolidator needed).
2. For services that DO emit: extend `manifest_consolidator_buckets` locals
   in the Terraform with the missing entries.
3. Add per-bucket timeout overrides if shard count is high (see existing
   `manifest_consolidator_timeouts` for sports + cefi market-data sizing).
4. `tofu apply` (or `terraform apply`) + verify the new Cloud Run jobs +
   crons land.
5. Re-run A3 v3 — every service has a consolidated manifest OR an explicit
   `BLOCKED-OPERATOR-DECISION` ack that it doesn't emit (and therefore
   doesn't need one).

**Cadence question** (operator decides): should we keep `*/1 * * * *` per
service kind × asset_group (currently 10 jobs minute-by-minute = 600
invocations/hour), OR consolidate to per-asset-group only (5 jobs that
each consolidate every service kind for that asset_group)? Operator favored
"once per asset_group across all services unless we need them split for
bandwidth." Recommend the consolidation since:

- Each Cloud Run invocation is ~30-90s; 5 jobs covering ~5 buckets each
  per minute is well under any quota.
- Reduces number of cron triggers from 10 → 5.
- Removes the artificial split between instruments + market-data.

**Implementation**: rewrite `manifest_consolidator_buckets` locals so each
key is an asset_group (cefi/defi/tradfi/sports/prediction) and the Cloud
Run Job takes a list of buckets to consolidate sequentially within one
container invocation. Owner: slot 5 to design + apply.

## Operational invariants (HARD RULES)

1. **Cloud Run is canonical**. No agent re-launches the legacy VM. No agent
   reintroduces `launch-manifest-consolidator-vm.sh`.
2. **One consolidator per env tier**. Currently only `prd` jobs exist;
   `dev` + `staging` consolidators must be deliberately provisioned + paired
   with corresponding bucket sets per `cloud-providers.yaml` env-tier policy.
3. **Idempotent + tolerates missed cycles**. The reader fallback (UTL
   `read_availability_index`) handles up to 120s of consolidator staleness;
   anything longer surfaces as a freshness alert in deployment-ui.
4. **Singleton per (service_kind, asset_group) job**. Cloud Run guarantees
   at-most-one execution per cron trigger. Manual `gcloud run jobs execute`
   invocations during operator interventions are safe (CAS on canonical blob
   prevents double-write).
5. **Per_vm shards are the source of truth for in-flight writes**. The
   consolidator MUST merge them into canonical without downgrading
   `schema_version` (preserve source version). A4 v2 verifies this.

## Composes with

- CLAUDE.md § "Manifest + Honest Absence" — every row in canonical OR
  per_vm shard is either `captured` / `empty_confirmed` (with typed reason)
  / `attempted_failed` / `expected_unattempted`.
- CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" — consolidator
  coverage gap (R-NEW-1) is a P0 data-pipeline-correctness issue.
- `codex/02-data/data-pipeline-correctness-hard-rule.md` — slot-freeze
  protocol if consolidator goes silent for >120s.
- `codex/05-infrastructure/per-tab-worktrees.md` — per-VM shard discipline
  for tab worktrees writing to manifests.

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

If any check fails: ping `plans/active/_agent_pings.md` cross-side + freeze
layer-N+1 slots per the data-correctness HARD RULE until restored.
