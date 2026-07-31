---
doc_type: issue
title:
  "P2.2 ('wire every runtime to its tier SA') is not mechanically executable today — 3 live-verified blockers: tier SAs
  are storage-only, VM launchers run as an over-privileged 3rd identity (not unified-trading-sa), and a competing
  per-service SA scheme already exists unreconciled"
summary: >-
  Dispatched task bucket_iam_p2_god_sa_removal_before_runtime_rewire-001 (assigned_role: infra) asked me to execute
  bucket_iam_write_protection_per_tier_2026_06_09.md P2.2 literally: wire every deployment-service Cloud Run service +
  VM launcher to its tier SA (uts-prd-sa/uts-test-sa/uts-migration-sa) instead of unified-trading-sa. Investigation
  (live GCP queries + static analysis, no terraform state mutated) surfaced three separate, independently-blocking
  findings that make a mechanical rewrite unsafe: (1) uts-prd-sa/uts-test-sa/uts-migration-sa hold ONLY storage roles
  live-verified via `gcloud projects get-iam-policy` — zero secretmanager/pubsub/bigquery/run.invoker roles — so wiring
  any real runtime to them today immediately breaks that runtime's Secret Manager / Pub/Sub / BigQuery access; (2) the
  plan's own premise that VM launchers run as `unified-trading-sa` is wrong — main.tf's own comment + a live IAM query
  confirm 155/156 `launch-*.sh` scripts actually run as the GCP default compute SA
  (`1060025368044-compute@developer.gserviceaccount.com`), which live-verified holds 28 UNCONDITIONAL project-wide roles
  including `roles/storage.admin` (broader than objectAdmin — includes bucket IAM policy writes),
  `roles/bigquery.admin`, `roles/iam.serviceAccountTokenCreator` (SA impersonation/token minting), and
  `roles/firebaseauth.admin` — a materially bigger, live-confirmed security exposure than the god-SA grant this whole
  plan was created to close, and one this plan's docs never mention; (3) a separate, ALREADY-LIVE per-service SA scheme
  (`deployment-service/configs/gcp_service_accounts.yaml`, from the archived-complete
  `api_keys_wallets_accounts_readiness_2026_05_10.md`) coexists unreconciled with this plan's per-tier design —
  `features-prod@...` is a real, non-disabled GCP SA already referenced by
  `scripts/cloud-run/deploy_features_service_cloud_run.sh`, and the live SA list also shows a THIRD family
  (`uts-{dev,staging,prod}-batch-sa`, `t1-batch-sa`, `market-tick-cefi-cr`, `features-sports-sa`, `features-onchain-sa`,
  `batch-processing-sa`, `ibkr-gateway-sa`, `aethergate-vm-sa`) not documented in either scheme. I did NOT apply any
  terraform/IAM change (grants, removals, or SA rewiring) — this is a pure investigation + plan split, mirroring this
  plan's own P1.2→P1.2a/P1.2b and P2.1→P2.1a/P2.1b precedent for "a checkbox that bundles a safe slice with a
  currently-unsafe slice."
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [iam, terraform, gcp, security, sequencing-hazard, ssot-contradiction, bucket-tiers]
related:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/active/issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md,
    /plans/active/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
sequential: true
drift_direction: correct-plan
source: >-
  Surfaced 2026-07-30 (slot-12, infra) while executing bucket_iam_p2_god_sa_removal_before_runtime_rewire-001, which
  itself dispatched bucket_iam_write_protection_per_tier_2026_06_09.md's P2.2 todo.
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# P2.2's literal "wire every runtime to its tier SA" is blocked on 3 separate, live-verified findings

## What I found

### Finding 1 — tier SAs are storage-only; wiring anything today breaks Secret Manager / Pub/Sub / BigQuery

Live-verified
(`gcloud projects get-iam-policy central-element-323112 --flatten="bindings[].members" --filter="bindings.members:uts-prd-sa@..."`):

```
roles/storage.objectAdmin   (x2, IAM-Condition-scoped to Group A / Group B -prd- prefixes)
roles/storage.objectViewer  (project-wide)
```

That's it — matches `bucket_iam_per_tier_sa.tf` exactly (P1.1/P1.2's scope was deliberately storage-only). Compare to
what `unified-trading-sa` (the current Cloud Run runtime identity per `deploy-shared.sh`) actually holds
(`main.tf:598-663`): `storage.objectAdmin`, `bigquery.dataEditor`, `secretmanager.secretAccessor`, `run.invoker`,
`pubsub.editor`, `compute.instanceAdmin.v1`, `iam.serviceAccountUser`, `artifactregistry.reader`. **If deployment-api's
Cloud Run service were switched to `uts-prd-sa` today, it would immediately lose Secret Manager access (API keys),
Pub/Sub access (event log), and BigQuery access** — a functional regression, not just a theoretical security gap. The
plan's own P0 design section never scoped tier SAs beyond storage roles, so this is a genuine gap in the original
design, not an execution mistake.

### Finding 2 — VM launchers don't run as `unified-trading-sa` (the plan's own premise is wrong); they run as an even MORE over-privileged identity

`main.tf`'s own comment (near the `default_compute_sa_datastore_user` grant) already documents this: "155/156 launchers
under `deployment-service/scripts/vm/launch-*.sh` pass NO `--service-account=`, so gcloud falls back to
`{project_number}-compute@developer.gserviceaccount.com`" — the **GCP default compute service account**, not
`unified-trading-sa`. Live-confirmed via census: of 165 `launch-*.sh` scripts, only 5 pass `--service-account=`
explicitly; of the rest, 4 route through the shared `lc_gcloud_create()` helper (`scripts/vm/lib/launcher_common.sh`,
which also never sets `--service-account`) and 138 call `gcloud compute instances create` directly with no SA flag — all
falling back to the default compute SA.

Live-verified IAM policy for `1060025368044-compute@developer.gserviceaccount.com` — **28 UNCONDITIONAL, project-wide
roles**, including:

```
roles/storage.admin                    <- broader than objectAdmin (includes bucket IAM policy writes)
roles/storage.objectAdmin
roles/storage.objectCreator
roles/storage.objectViewer
roles/bigquery.admin
roles/bigquery.dataEditor / .jobUser / .user
roles/iam.serviceAccountTokenCreator   <- can mint tokens for / impersonate OTHER service accounts
roles/firebaseauth.admin
roles/secretmanager.secretAccessor
roles/pubsub.publisher / .subscriber
roles/compute.instanceAdmin.v1
roles/cloudscheduler.admin
roles/run.developer / .invoker
roles/logging.logWriter / .viewer
... (14 more, all unconditional / project-wide)
```

**This is a materially bigger, already-live security exposure than the god-SA (`unified-trading-sa`) grant this whole
plan exists to close** — `roles/storage.admin` alone lets any of 155 VM launchers rewrite bucket IAM policy or delete
buckets project-wide, and `iam.serviceAccountTokenCreator` lets it impersonate other service accounts. Neither this plan
nor any doc I found mentions the default compute SA's role set. **This is arguably the higher-priority finding of the
two** — but fixing it (scoping 155 launchers off the default compute SA) is its own large, separately-scoped effort
requiring per-launcher analysis of what each startup script actually calls (GCS write tier, Secret Manager keys,
Pub/Sub, BigQuery), not a blind mechanical swap.

### Finding 3 — a second, already-partially-live per-service SA scheme exists, unreconciled with this plan

`deployment-service/configs/gcp_service_accounts.yaml` (SSOT from the archived `status: complete`
`api_keys_wallets_accounts_readiness_2026_05_10.md`, 2026-05-12) defines per-service-per-env SAs (`instruments-prod`,
`mtds-prod`, `mdps-prod`, `features-prod`, etc.), each with its own role/bucket/secret scoping — a completely different
strategy from this plan's per-TIER SAs. Live-confirmed this isn't purely aspirational: `features-prod@...` exists as a
real, non-disabled GCP SA and IS referenced by `scripts/cloud-run/deploy_features_service_cloud_run.sh` (though that
script is marked "OPERATOR-SIDE ONLY — do NOT run this script from an agent", so I did not invoke it). The live SA list
also surfaced a THIRD, apparently ad-hoc family not documented in either scheme: `uts-dev-batch-sa` /
`uts-staging-batch-sa` / `uts-prod-batch-sa`, `t1-batch-sa` (used by `launch-planning-vm.sh`), `market-tick-cefi-cr`,
`features-sports-sa`, `features-onchain-sa`, `batch-processing-sa`, `ibkr-gateway-sa`, `aethergate-vm-sa`. Neither this
plan's `related:` list nor `bucket-isolation-model.md` §8 acknowledges the per-service scheme or the ad-hoc family, so
there is no documented answer to "does per-tier supersede per-service, do they coexist by domain, or should per-tier be
abandoned in favor of finishing the per-service rollout?" This is an unreconciled SSOT contradiction between two (really
at least three) IAM strategies solving the same bucket-write-protection problem.

## Why it matters

Per `data-pipeline-correctness-is-the-heartbeat` (a data-write-path outage is the single most protected invariant in
this workspace) and `findings-triage`'s "SSOT contradiction → NOTIFY OPERATOR": mechanically wiring ANY live runtime to
a tier SA today would silently break Secret Manager / Pub/Sub / BigQuery access for that runtime the moment it deployed
— exactly the fleet-wide-403 failure mode P2.1's sequencing-hazard issue doc already flagged, just from the opposite
direction (missing grants on the NEW identity, rather than a removed grant on the OLD one). Finding 2 additionally means
P2.2's own success criteria ("verify live/batch prod workloads retain -prd- write... now via the tier SA") can't even be
stated correctly for VM launchers yet, since the plan never identified their real current identity. Finding 3 means
committing to per-tier SAs without an operator ruling risks building out a second, competing IAM scheme nobody asked to
keep.

## Recommended decision

1. **Operator decision needed** on which SA strategy is authoritative going forward: per-tier (`uts-{prd,test}-sa`, this
   plan), per-service (`configs/gcp_service_accounts.yaml`, already partially live), or a hybrid (e.g. per-tier for
   Group A raw-data buckets already covered by this plan, per-service for domain services that already migrated).
2. Once resolved, grant the winning SA(s) the non-storage roles real runtimes need (mirror `unified-trading-sa`'s
   current grant set, scoped appropriately) BEFORE wiring any Cloud Run service or VM launcher to it.
3. Wire Cloud Run services one at a time, live-verifying each (start with `deploy-shared.sh` / deployment-api — the most
   centralized, single-script target).
4. VM launcher rewiring is its own large, separately-scoped effort (165 scripts, only ~142 flow through 2 shared entry
   points) — needs a per-launcher tier classification pass, not a blind bulk edit. **Fix independently of the tier-SA
   question**: the default compute SA's 28-role unconditional grant set (Finding 2) is worth its own security-hardening
   plan regardless of which SA scheme wins, since it's a bigger live exposure than the original god-SA problem.

I split P2.2 in the plan into P2.2a (blocked, [OPERATOR] SA-strategy decision) / P2.2b (blocked on P2.2a, grant
non-storage roles) / P2.2c (blocked on P2.2b, wire Cloud Run) / P2.2d (its own large VM-launcher effort, blocked on
P2.2a) — mirroring this plan's own P1.2→P1.2a/P1.2b and P2.1→P2.1a/P2.1b precedent.

## Hybrid (C) boundary proposal — operator decision surface (2026-07-31)

Per main's interim guidance on BLK-0c84ceac (still `operator_pending` — this is NOT a ratification, it's the prep work
main asked for before any grant executes): a concrete hybrid boundary, built from live-verified facts, so "hybrid"
doesn't become a fourth unreconciled scheme. **No terraform/IAM state was touched to produce this — read-only
research.**

### Bucket → scheme mapping

| Bucket family                                                                                                                                                                                                                           | Scheme                                    | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Group A raw-data (`market-data-tick-*`, `instruments-store-*`, `features-calendar-*`, `-prd-`/`-test-`)                                                                                                                                 | **per-tier** (`uts-prd-sa`/`uts-test-sa`) | Already the live scope of `bucket_iam_per_tier_sa.tf:107-165`; no single "service" owns cross-service raw data lakes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Group B `features-{ag}-{prd,test}` (cefi/defi/tradfi/sports/pred)                                                                                                                                                                       | **per-tier** (already covered, same file) | Matches `group_b_bucket_prefixes`; already live.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Group B's other 4 folds (`ml-store`, `execution-store`, `strategy-store`, `portfolio-state`) — **not yet joined to any IAM scheme**                                                                                                     | **per-service** (recommended)             | Domain SAs already exist scoped to these (`strategy-prod`, `execution-prod`, `risk-prod`, `pbms-prod`, `client-reporting-prod`, `trade-event-prod` in `gcp_service_accounts.yaml`) — extending per-tier here would duplicate work the per-service scheme already started.                                                                                                                                                                                                                                                                                                                               |
| Domain services (instruments/mtds/mdps/features/strategy/execution/pbms/risk/alerting/signal-broadcast/deployment/client-reporting/trade-event/ui/batch-live-recon/disaster-recovery/oracle-aggregation/feature-onchain/feature-sports) | **per-service** (already live)            | 19 SAs already defined in `gcp_service_accounts.yaml`. **Caveat (blocking before this scheme can be trusted)**: those entries' `bucket_access:` names (e.g. `unified-trading-features-prod`) do **not** match the canonical `resolve_bucket_name()` grammar (`features-cefi-prd-central-element-323112`, per `codex/05-infrastructure/bucket-isolation-model.md` §2/§11) — the YAML's own drift-verifier (`sync_gcp_service_accounts.py`) shows `last_executed: NEVER`. Its grants may be stale/aspirational relative to live buckets; needs a live-verify pass before being ratified as authoritative. |

### Ad-hoc-family reconciliation

| SA                                                               | Classification (live-verified where possible)                                                                                                                       | Recommended disposition                                                                                                                                                                                                |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uts-{dev,staging,prod}-batch-sa`                                | Cloud Scheduler → Cloud Run Jobs invoker identity, `roles/run.invoker` ONLY (`t1_batch_scheduler.tf:55-59`)                                                         | **Out of scope** — not a bucket-write-protection SA at all (orthogonal scheduler-auth concern). Exclude from this ruling; leave as-is.                                                                                 |
| `t1-batch-sa`                                                    | Runs the orchestrator/planning VM (`launch-planning-vm.sh:46`)                                                                                                      | **Out of scope** — a control-plane VM identity, not a data-bucket writer. Audit its own grant set separately if over-privilege is suspected.                                                                           |
| `features-sports-sa`                                             | Tied to features-service-sports Cloud Run/Workflow/Scheduler (`terraform.tfvars:31-32`), scoped to `features-sports-prd`                                            | **Likely duplicate** of per-service's `feature-sports-prod` (same domain, near-identical name). Needs a live `gcloud` dedup + consolidation onto one canonical SA before ratifying per-service as that bucket's owner. |
| `ibkr-gateway-sa`                                                | `ibkr-gateway-infra/ibkr-gateway/terraform.tfvars:4`, no in-repo role/bucket grant located                                                                          | **Onboard to per-service** — new entry alongside `execution-prod`; needs its own terraform IAM definition (doesn't exist yet).                                                                                         |
| `market-tick-cefi-cr`                                            | No confirmed live reference; circumstantial tie to the retired `trigger-market-tick-cefi-job` Cloud Run trigger (403'd 4+ months, replaced by a cron-VM 2026-05-20) | **Likely orphaned** — live-verify via `gcloud iam service-accounts describe` (last-authenticated timestamp), delete if confirmed unused. Small standalone cleanup, not part of this ruling.                            |
| `features-onchain-sa`, `aethergate-vm-sa`, `batch-processing-sa` | Zero-to-weak in-repo references (may be console/gcloud-created, or defined outside this checkout)                                                                   | **Cannot classify without a live GCP audit** (`gcloud iam service-accounts list` + `get-iam-policy` + last-authenticated per SA) — do not assume orphaned without checking actual usage.                               |

### Default-compute-SA remediation (folded into the same ruling, per main's guidance)

Already tracked as this doc's own P3.1/P3.2 todos. Recommend the operator's ruling also states the VM-launcher
direction: **(a)** migrate prd/test-tier launchers onto the per-tier SAs (extend `uts-prd-sa`/`uts-test-sa`/
`uts-migration-sa` grants to cover launcher needs — mirrors the Cloud-Run-side hybrid, recommended), **(b)** a new
per-launcher-tier SA family, or **(c)** scope down the existing default compute SA's 28 roles in place (least migration
effort, keeps one shared identity across 155 launchers — weaker isolation).

### Explicit operator ask

1. Ratify hybrid (C) as authoritative (vs. full per-tier / full per-service).
2. Approve the bucket → scheme table above, or amend it.
3. Rule on the ad-hoc family per the table: in-scope-now (`features-sports-sa` dedup, `ibkr-gateway-sa` onboarding) vs.
   explicitly out-of-scope (`*-batch-sa` family) vs. needs-live-audit-first (the 4 unclassifiable names).
4. Pick a VM-launcher remediation direction (a/b/c above) to scope P3.1/P3.2.

Once 1-4 are answered, P1 (todo 2 below) becomes mechanically executable against a concrete target instead of a guess.

## Dispatch-gating note (2026-07-31)

`sequential: true` added after the backlog dispatched P1 (todo 2, "grant the winning SA the non-storage roles") to a
worker while P0 (todo 1, the `[OPERATOR]` ruling) was still open and unchecked — `/api/backlog/<id>/blockers` confirmed
the derived task read `"ready (no blockers)"`, i.e. nothing in the backlog was gating it on P0's completion. Executing
P1 today would mean guessing the operator-only SA-strategy call. This also protects P2/P3.2 (todos 3/5), which depend on
the same ruling, from the identical premature-dispatch risk. Accepted cost: P3.1 (todo 4, the independent
default-compute-SA hardening effort) also waits behind P0-P2 under strict sequential ordering, even though it doesn't
depend on the SA-strategy outcome — a full plan split would avoid that, but wasn't done here to keep this fix in-scope
for the dispatched task.

## Todos

- [ ] [OPERATOR] P0. Rule on the competing bucket-write-protection SA strategies: per-tier (`uts-{prd,test}-sa`,
      `bucket_iam_write_protection_per_tier_2026_06_09.md`) vs per-service
      (`deployment-service/configs/gcp_service_accounts.yaml`, `features-prod`/`instruments-prod`/etc., already
      partially live) vs the undocumented ad-hoc family (`uts-{dev,staging,prod}-batch-sa`, `t1-batch-sa`, etc.).
      Unblocks P2.2a below. (repo: unified-trading-pm)
- [ ] [TERRAFORM] P1. Once P0 resolves, grant the winning per-tier/per-service SA(s) the non-storage roles real runtimes
      need (`secretmanager.secretAccessor`, `pubsub.editor` or `.publisher`/`.subscriber`, `bigquery.dataEditor`,
      `run.invoker`, `iam.serviceAccountUser` + `compute.instanceAdmin.v1` for self-impersonating VM launches) — mirror
      `unified-trading-sa`'s current grant set (`main.tf:598-663`), scoped per tier/service. (repo: deployment-service)
- [ ] [CODE] P2. Wire `scripts/cloud-run/deploy-shared.sh` (deployment-api's Cloud Run identity) to the winning SA from
      P0, gated on P1's role grants being live-verified first; live-verify via a real deploy that Secret Manager /
      Pub/Sub / BigQuery access still works. (repo: deployment-service)
- [ ] [INFRA] P3.1. Security hardening, independent of the P0/P1/P2 SA-strategy question: the GCP default compute SA
      (`{project_number}-compute@developer.gserviceaccount.com`, the identity 155/165 VM launchers actually run as)
      holds 28 unconditional project-wide roles incl. `roles/storage.admin` and `roles/iam.serviceAccountTokenCreator` —
      audit which of those roles the launcher startup scripts genuinely use and scope down; this is a bigger live
      exposure than the original god-SA (`unified-trading-sa`) grant. (repo: deployment-service)
- [ ] [CODE] P3.2. VM-launcher rewiring itself (165 `scripts/vm/launch-*.sh`, only 4 through the shared
      `lc_gcloud_create()` helper) — its own large, separately-scoped effort requiring a per-launcher tier
      classification pass (which write `-prd-` vs `-test-`, which are migration scripts). Do not attempt as a single
      mechanical bulk edit. Gated on P0. (repo: deployment-service)
