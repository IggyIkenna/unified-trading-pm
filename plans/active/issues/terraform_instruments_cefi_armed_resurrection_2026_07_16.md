---
doc_type: issue
title:
  ARMED RESURRECTION — `google_storage_bucket.instruments_cefi` is still declared + in prod state while the physical
  bucket is 404; the next `tofu apply` on prod WILL recreate `instruments-store-cefi-central-element-323112` as an empty
  shell
summary:
  "Measured live 2026-07-16 while executing the sports legacy-bucket cutover T4.4 gate: a real `tofu plan` against
  `terraform/state/prod` (run via the Cloud Build executor, which holds the bucket perms `unified-trading-sa` lacks)
  reports **`google_storage_bucket.instruments_cefi will be created`** — the ONLY bucket-create in the whole plan. The
  physical bucket `instruments-store-cefi-central-element-323112` is **404** (confirmed by the elevated Cloud Build SA,
  not by the 403-prone local SA). Cause: `terraform/gcp/main.tf:137` still DECLARES the resource and the prod state
  still holds the entry, but the bucket was deleted out-of-band — the exact documented resurrection class that recreated
  ~30 cleanup-deleted buckets on 2026-07-12T21:59Z ([[terraform_bucket_estate_drift_resurrection_2026_07_13]]), and
  which `main.tf` itself warns about verbatim in five separate REMOVED-comments. cefi is the one twin that got the
  physical delete WITHOUT the config removal + `state rm`. **Not introduced by the sports cutover** — the sports leg
  removed its own block + `state rm`-ed its entry first, precisely so this could not happen to it, and the same plan
  shows ZERO actions on the sports legacy bucket. Fix = remove the `instruments_cefi` block + `terraform state rm` it,
  mirroring the tradfi/defi removals at `main.tf:172-180`."
status: resolved
nature: issue
asset_group: [cefi]
stage: [data, meta]
repos: [deployment-service, unified-trading-pm]
scope: [admin, engineer]
tags: [terraform, gcs, bucket-canonicalisation, resurrection, drift, infra, destructive-risk]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../bucket_estate_consolidation_to_sub100_2026_07_13.md,
    ../gcs_bucket_estate_cleanup_2026_07_10.md,
  ]
created: 2026-07-16
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: [deployment-service@0981c9c]
source: [sports_legacy_bucket_cutover_2026_07_16.md T4.4 gate execution 2026-07-16]
---

# `instruments_cefi` is an ARMED terraform resurrection

> **✅ RESOLVED 2026-07-17 — `deployment-service@0981c9c`.** The block is removed, the state entry is `state rm`'d, and
> a real elevated `tofu plan` (Cloud Build `b4f4851a-e017-413c-9662-aa1cec946453`) now reports **ZERO**
> `google_storage_bucket.* will be created`; the plan's add-count dropped 20 → 19 (exactly this bucket, nothing else
> moved). A full prod `tofu apply` can no longer resurrect it. **See the Progress Log for the sweep** — every other
> Group-A flat twin is verified de-declared AND state-rm'd, but the sweep found a NEW adjacent landmine (8 IAM grants
> bound to 404 buckets) that is filed as todos below and NOT fixed here.
>
> _(Original framing, retained for provenance: found while running the sports cutover's T4.4 `tofu plan` gate; read-only
> measurement, NOT fixed by the finding leg — fixing it meant touching another plan's resource
> (`bucket_estate_consolidation`), and that leg's rule was findings-triage: outside every plan → issue doc + notify.)_

## The measurement

`tofu plan` against `terraform/state/prod` (OpenTofu 1.12.3, vars `project_id=central-element-323112`,
`region=asia-northeast1`, `environment=prod`, `bucket_prefix=uts`), executed inside Cloud Build
**`ea03c145-25a0-4280-acc3-75a99486ed76` (SUCCESS)** because `unified-trading-sa` lacks `storage.buckets.get` and dies
on 174 pre-existing 403 refresh errors locally:

```
Plan: 1 to import, 20 to add, 51 to change, 1 to destroy.

=== ALL bucket CREATE actions (resurrection candidates) ===
  # google_storage_bucket.instruments_cefi will be created      <-- THE ONLY ONE
```

And the bucket does not exist — via the **elevated** Cloud Build SA (build `0aa821f4-adf2-4ff2-b68d-96d917c4ed1d`), so
this is not the local SA's 403-masquerading-as-404:

```
ERROR: (gcloud.storage.buckets.describe) gs://instruments-store-cefi-central-element-323112 not found: 404.
```

## Why it is armed

| layer         | state                                                                                           |
| ------------- | ----------------------------------------------------------------------------------------------- |
| physical      | **404 — deleted** (2026-07-14, `bucket_estate_consolidation` W2 / item E)                       |
| terraform cfg | **still DECLARED** — `deployment-service/terraform/gcp/main.tf:137` `"instruments_cefi"`        |
| prod state    | **still present** — `google_storage_bucket.instruments_cefi`                                    |
| ⇒ next apply  | **CREATES an empty shell** `instruments-store-cefi-central-element-323112` (metageneration = 1) |

This is the **documented** failure mode. `main.tf` warns about it verbatim in five REMOVED-comments, e.g. `:315-320`:

> _"…was recreated as an empty shell by an out-of-band `tofu apply` (metageneration=1,
> creation_time=2026-07-13T00:52:06Z) because this resource block was still declared here after the physical bucket was
> deleted"_

and `:326-329`:

> _"Removing the resource blocks BEFORE the physical delete (paired with `terraform state rm`) so a future apply cannot
> resurrect them as empty shells — the exact failure that recreated ~30 cleanup-deleted buckets on 2026-07-12T21:59Z"_

**The tradfi / defi / prediction / sports twins all got the config-removal + `state rm` treatment. cefi got the physical
delete without it.** It is the last one holding the loaded chamber.

## Blast radius

Anyone running `tofu apply` on `terraform/gcp` @ `terraform/state/prod` — a routine `bootstrap_gcp.sh --env prod` — will
recreate the bucket. An empty `instruments-store-cefi-…` shell then:

- re-contaminates the estate the `sub-100` consolidation is driving down (it counts against the bucket budget);
- re-creates a **flat, no-env Group-A name** that the 2026-05-11 operator reversal explicitly retired
  (`cloud-providers.yaml:136-140`), which is precisely what `main.tf:6-8`'s corrected header now warns against;
- silently re-arms every "is the flat twin gone?" audit that closed on cefi.

## Fix (one commit, mirrors the existing precedent exactly)

1. Delete the `resource "google_storage_bucket" "instruments_cefi"` block at `terraform/gcp/main.tf:137`, leaving a
   REMOVED comment in the verbatim shape of `:172-180` (tradfi/defi).
2. `tofu state rm google_storage_bucket.instruments_cefi` against
   `bucket=uts-terraform-state-central-element-323112 prefix=terraform/state/prod`.
3. Re-run the plan and require **zero** `google_storage_bucket.* will be created`.

Do **1 before 2 is applied anywhere** — and never run a full `tofu apply` on prod until this is fixed, because that
apply is the very thing that resurrects it.

## Related landmine found in the same plan (NOT fixed, lower severity)

The prod state carries **orphaned entries whose config was removed 2026-07-13 and whose live resources are already
gone** — `google_cloud_scheduler_job.manifest_consolidator_cron["instruments-sports-legacy"]` and
`module.manifest_consolidator_job["instruments-sports-legacy"]` (+ the `market-data-sports-legacy` pair). Both
`gcloud scheduler jobs describe` and `run jobs describe` return NOT_FOUND. These are self-healing (refresh sees 404 →
drops from state) and are **not** delete-blockers, but they are evidence that **no clean `tofu apply` has run against
prod since at least 2026-07-13** — which is itself why this issue could sit armed for days.

## Progress Log

**2026-07-17 — DISARMED + VERIFIED. The chamber is empty.** Executed the 3-step fix exactly as specified above.

| step                           | action                                                                                                                                                                                                                                                               | evidence                                                         |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 1. config removed              | `resource "google_storage_bucket" "instruments_cefi"` deleted from `main.tf`, REMOVED comment in the verbatim precedent shape                                                                                                                                        | `main.tf` (was `:137-170`)                                       |
| 1b. **output removed** (extra) | `output "instruments_cefi_bucket"` referenced the resource ⇒ config would not parse without it. Removed with a REMOVED comment matching the `market_data_cefi_bucket` precedent. **Zero consumers** (grep across ALL repos: the declaration itself was the only hit) | `outputs.tf` (was `:10-13`)                                      |
| 2. state rm                    | `tofu state rm google_storage_bucket.instruments_cefi` @ `prefix=terraform/state/prod` → _"Successfully removed 1 resource instance(s)"_                                                                                                                             | state snapshotted pre-RM (serial **345**, 257 resources)         |
| 3. plan re-verified            | **`=== ALL bucket CREATE actions === ` → EMPTY**                                                                                                                                                                                                                     | Cloud Build **`b4f4851a-e017-413c-9662-aa1cec946453` (SUCCESS)** |
| shipped                        | `deployment-service@0981c9c` — QG green (`--no-fix`, 90s), landed on LDR                                                                                                                                                                                             | `Evidence: cloudbuild=b4f4851a-e017-413c-9662-aa1cec946453`      |

**Plan-count delta — exactly −1 add, nothing else moved** (same executor / same SA / apples-to-apples with the finding
build `ea03c145`):

```
before (ea03c145, 2026-07-16):  Plan: 1 to import, 20 to add, 51 to change, 1 to destroy.
after  (b4f4851a, 2026-07-17):  Plan: 1 to import, 19 to add, 51 to change, 1 to destroy.
                                                   ^^ the bucket-create is gone
```

The only three surviving `instruments_cefi` strings in the plan are **not** the bucket:
`module.instruments_cefi_t1_recon_job.google_cloud_run_v2_job.job` (a live Cloud Run job — a DIFFERENT resource,
correctly retained, its `_imports_reconcile.tf:109-112` import block deliberately kept) ×2, plus
`- instruments_cefi_bucket = "instruments-store-cefi-central-element-323112" -> null` (the output being removed).
`grep -c 'google_storage_bucket.instruments_cefi\b'` over the plan = **0**.

**Note on the plan's 8 `Error:` lines** — all pre-existing 403s on unrelated pubsub topics/subscriptions + one BigQuery
table (the Cloud Build SA lacks those specific perms); they are refresh-time and unrelated to this change. The local SA
is worse (**171** 403s) which is why the elevated Cloud Build executor is mandatory here — as the finding leg
documented.

### Sibling sweep — every Group-A flat legacy twin audited at all three layers

Probe calibrated 403-vs-404 first (the SA lacks `storage.buckets.get`, so **403 = EXISTS**, only **404 = genuinely
gone** — a naive 404-only read would have mislabelled every live bucket):

| resource                 | config         | prod state  | physical   | verdict                                                                                                     |
| ------------------------ | -------------- | ----------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| `instruments_cefi`       | REMOVED (this) | rm'd (this) | 404        | ✅ **was the only armed one — now disarmed**                                                                |
| `instruments_tradfi`     | REMOVED 07-14  | absent      | 404        | ✅ fully de-declared + state-rm'd                                                                           |
| `instruments_defi`       | REMOVED 07-14  | absent      | 404        | ✅ fully de-declared + state-rm'd                                                                           |
| `instruments_sports`     | REMOVED 07-16  | absent      | 404        | ✅ fully de-declared + state-rm'd (ds@4637aed)                                                              |
| `instruments_prediction` | REMOVED 07-13  | absent      | 404        | ✅ fully de-declared + state-rm'd                                                                           |
| `market_data_cefi`       | REMOVED 07-14  | absent      | 404        | ✅ fully de-declared + state-rm'd                                                                           |
| `market_data_tradfi`     | REMOVED 07-14  | absent      | 404        | ✅ fully de-declared + state-rm'd                                                                           |
| `market_data_defi`       | REMOVED 07-14  | absent      | 404        | ✅ fully de-declared + state-rm'd                                                                           |
| `market_data_sports`     | **declared**   | **present** | **EXISTS** | ✅ **correctly retained** — blocked on OR-5b, NOT delete-eligible (550,062 keys on 32 days live only there) |

**⇒ ZERO remaining bucket-create resurrections.** The empty bucket-create list in `b4f4851a` is the machine proof: no
`google_storage_bucket.*` is declared-but-404 anywhere in the prod config.

### 🔴 NEW adjacent landmine found by the sweep — 8 IAM grants bound to 404 buckets (NOT fixed; see below)

The bucket layer is clean, but the sweep found the **same 2026-07-14 flat-twin deletion was not propagated to the IAM
layer**. Eight `google_storage_bucket_iam_member` entries still grant roles on buckets that are physically **404**, and
the plan shows every one of them **`will be created`** (refresh drops them because the bucket is gone) ⇒ **the next full
prod `tofu apply` will ERROR** trying to set IAM on a nonexistent bucket:

| resource                                                               | target bucket                    | physical |
| ---------------------------------------------------------------------- | -------------------------------- | -------- |
| `catalogue_regen_instruments_reader["instruments-store-cefi-…"]`       | `instruments-store-cefi-{pid}`   | 404      |
| `catalogue_regen_instruments_reader["instruments-store-defi-…"]`       | `instruments-store-defi-{pid}`   | 404      |
| `catalogue_regen_instruments_reader["instruments-store-tradfi-…"]`     | `instruments-store-tradfi-{pid}` | 404      |
| `instrument_catalogue_instruments_reader["instruments-store-cefi-…"]`  | `instruments-store-cefi-{pid}`   | 404      |
| `instrument_catalogue_instruments_reader["instruments-store-defi-…"]`  | `instruments-store-defi-{pid}`   | 404      |
| `instrument_catalogue_market_data_reader["market-data-tick-cefi-…"]`   | `market-data-tick-cefi-{pid}`    | 404      |
| `instrument_catalogue_market_data_reader["market-data-tick-defi-…"]`   | `market-data-tick-defi-{pid}`    | 404      |
| `instrument_catalogue_market_data_reader["market-data-tick-tradfi-…"]` | `market-data-tick-tradfi-{pid}`  | 404      |

Declared in `catalogue_regen_scheduler.tf:41-62` + `instrument_catalogue_scheduler.tf:30-63`. **The fix has an exact
in-repo precedent**: `lifecycle_catalogue_scheduler.tf:81-99` already points EVERY asset group at the canonical `-prd-`
name (`instruments-store-cefi-prd-…` etc.) — which is precisely why its IAM members refresh clean and appear nowhere in
the create list. In the two stale files, **sports and prediction were already migrated to `-prd-`** (sports cutover
T1.4; prediction 2026-07-06) — **cefi/defi/tradfi were simply left behind**. The canonical `-prd-` twins all exist
(403).

**NOT fixed here, deliberately** — this is a **different hazard class** (a blocked/erroring apply, not a resurrection;
it cannot recreate a bucket) and it is `bucket_estate_consolidation`'s resource, so fixing it means touching another
plan's surface — the same triage boundary that (correctly) made the finding leg file this doc instead of fixing it. It
also needs a runtime measurement this leg did not take: **whether `catalogue-regen` / `instrument-catalogue` are already
failing at runtime** — if those jobs resolve canonical `-prd-` buckets via `cloud-providers.yaml` they currently hold
**no grant at all** on what they actually read, which would be a live P1, not just a plan-time defect.

- [ ] [INFRA] P1. **Repoint the 8 flat-legacy IAM grants to canonical `-prd-` names** in
      `catalogue_regen_scheduler.tf` + `instrument_catalogue_scheduler.tf` (cefi/defi/tradfi rows only), mirroring
      `lifecycle_catalogue_scheduler.tf:81-99` and the already-migrated sports/prediction rows in the same blocks.
      **Measure first** (grep-then-READ): what bucket do the catalogue-regen / instrument-catalogue jobs actually
      resolve at runtime? If canonical, they are missing their real grant today ⇒ escalate to P0.
- [ ] [DOCS] P2. `instrument_catalogue_scheduler.tf:54-55` claims _"the legacy no-env `market-data-tick-sports-{pid}`
      bucket is DELETED at cutover"_ — **measurably false**: that bucket EXISTS (403) and is DELIBERATELY RETAINED
      (blocked on OR-5b; `main.tf` says so verbatim). The comment conflates it with `instruments-store-sports`, which
      genuinely was deleted. Correct the comment; the `-prd-` repoint itself is fine.

**2026-07-16** — Found by the sports cutover's T4.4 gate (Phase-5/delete leg). Measured, not inherited: real `tofu plan`
via Cloud Build `ea03c145-25a0-4280-acc3-75a99486ed76`; 404 confirmed via elevated SA build
`0aa821f4-adf2-4ff2-b68d-96d917c4ed1d`. Filed rather than fixed — `instruments_cefi` belongs to
`bucket_estate_consolidation_to_sub100_2026_07_13`, and the sports leg's scope was explicitly the instruments-sports
bucket only (its own block WAS removed + `state rm`-ed, and the same plan proves ZERO actions reference it). **Operator
notified in the leg's final report.**
