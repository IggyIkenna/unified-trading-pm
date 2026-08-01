---
doc_type: issue
title:
  "Group A `market-data-tick-` IAM condition prefix omits the per-asset-group segment — uts-prd-sa/uts-test-sa cannot
  write ANY market-data-tick-{ag}-{prd,test} bucket, live-confirmed blocking real MDPS candle writes"
summary: >-
  While executing Track K (MDPS) — the `data-pipeline-check-mdps` skill's SPORTS baseline checkpoint
  (sports_consolidated_native_ao_extract_2026_07_25.md) — the launched `mdps-backfill-sports-pipelinecheck-*` VM
  (running as `uts-prd-sa`, via `launch-mdps-backfill-vm.sh:396`'s `lc_tier_service_account` wiring) failed EVERY
  candle/manifest write with a live `PERMISSION_DENIED` (`storage.objects.create` denied), against BOTH the `-test-`
  output bucket (`market-data-tick-sports-test-central-element-323112`, 16 occurrences in run.log) and the `-prd-`
  bucket (`market-data-tick-sports-prd-central-element-323112`, 932 occurrences) — 4425 total 403s logged before I
  stopped the VM. Root cause (live-verified via `gcloud projects get-iam-policy` + reading
  `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf:79-83,111-136`): `local.group_a_bucket_prefixes` lists a
  single flat prefix `"market-data-tick-"`, which the `group-a-prd-tier-only`/`group-a-test-tier-only` CEL conditions
  expand to `resource.name.startsWith("projects/_/buckets/market-data-tick-prd-")` / `...market-data-tick-test-...`. But
  the REAL bucket naming (confirmed live: `market-data-tick-sports-test-...`, `market-data-tick-sports-prd-...` exist
  and are the ones this VM targeted; confirmed in code: `market-tick-data-service/gcp/main.tf:227-229` —
  `market-data-tick-cefi`, `market-data-tick-defi`, `market-data-tick-tradfi` base names) is asset-group-scoped:
  `market-data-tick-{ag}-{tier}-{project}`. The condition's literal string `market-data-tick-prd-` can NEVER be a prefix
  of `market-data-tick-sports-prd-...` (the asset-group segment sits BETWEEN `market-data-tick-` and `prd-`), so the
  startsWith check always evaluates false for every real market-data-tick bucket, for both tiers, for every asset group.
  This is NOT how Group B was written: `features-*`'s `local.group_b_bucket_prefixes` correctly enumerates one prefix
  PER asset group (`features-cefi-`/`features-tradfi-`/`features-defi-`/`features-pred-`/`features-sports-`) — Group A's
  `market-data-tick-` entry should have received the same per-AG enumeration treatment and did not. `instruments-store-`
  and `features-calendar-` (the other two Group A prefixes) are genuinely flat/non-AG-scoped buckets, so those two ARE
  correctly matched — only the `market-data-tick-` entry is broken.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-data-processing-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [iam, terraform, gcp, data-correctness, bucket-tiers, sequencing-hazard, mdps]
related:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /plans/active/issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md,
    /plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
sequential: false
drift_direction: correct-code
source: >-
  Surfaced 2026-08-01 (slot-7, data_engineering) while executing sports_consolidated_native_ao_extract-031 ("Track K
  (MDPS) — run + cite 3 dated checkpoints for data-pipeline-check-mdps against sports"). Live GCP IAM + terraform
  read-only investigation; no terraform/IAM state was mutated. I DID stop the doomed VM
  (`mdps-backfill-sports-pipelinecheck-20260801-102347-2bf067`, my own just-launched VM, to save further SPOT compute +
  GCS request spend once the root cause was confirmed identity-level and day/shard-independent).
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# Group A `market-data-tick-` IAM condition is missing its per-asset-group segment

## What I found

`deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf:79-83`:

```hcl
group_a_bucket_prefixes = [
  "market-data-tick-",
  "instruments-store-",
  "features-calendar-",
]
```

Used at `:111-118` (`uts_prd_objectadmin_group_a`) and `:123-136` (`uts_test_objectadmin_group_a`) to build:

```
resource.name.startsWith("projects/_/buckets/market-data-tick-prd-")   # uts-prd-sa
resource.name.startsWith("projects/_/buckets/market-data-tick-test-")  # uts-test-sa
```

Live-verified via `gcloud projects get-iam-policy central-element-323112 --format=json`, both conditions are exactly as
above (titles `group-a-prd-tier-only` / `group-a-test-tier-only`). Real market-data-tick buckets are asset-group-scoped
— `market-data-tick-sports-test-central-element-323112` and `market-data-tick-sports-prd-central-element-323112` both
exist live (confirmed via `gcloud storage ls`) and are the exact buckets my MDPS pipeline-check VM targeted (per
`--output-bucket` and the launcher's `PROTOCOL_DATA_SOURCE_BUCKET_SPORTS`/`MDPS_OUTPUT_BUCKET_SPORTS` env). Code
confirmation: `market-tick-data-service/gcp/main.tf:227-229` declares base names `market-data-tick-cefi`,
`market-data-tick-defi`, `market-data-tick-tradfi` (one per asset group) — there is no flat `market-data-tick-{tier}`
bucket for this family to ever match. `"market-data-tick-sports-prd-...".startsWith("market-data-tick-prd-")` is false —
the asset-group segment (`sports-`) sits between the family prefix and the tier, so the condition can never match any
real bucket in this family, for either tier SA, for any asset group.

**Compare to Group B**, which is correctly enumerated per-AG (`bucket_iam_per_tier_sa.tf:96-99`):

```hcl
group_b_bucket_prefixes = [
  "features-cefi-", "features-tradfi-", "features-defi-", "features-pred-", "features-sports-",
]
```

Group A's `market-data-tick-` entry needed the same per-AG treatment and didn't get it — `instruments-store-` and
`features-calendar-` are genuinely flat/non-AG-scoped bucket families, so those two entries ARE correct as written; only
`market-data-tick-` is broken.

## Live reproduction

Running `sports_consolidated_native_ao_extract-031` (Track K MDPS SPORTS baseline checkpoint,
`data-pipeline-check-mdps --day 2025-12-20 --asset-group SPORTS --legs force,skip --require-captured --auto-day`), the
driver launched `mdps-backfill-sports-pipelinecheck-20260801-102347-2bf067` (`launch-mdps-backfill-vm.sh:396` wires
`--service-account="$(lc_tier_service_account prod "$PROJECT")"` → `uts-prd-sa@central-element-323112...`). Its
`run.log`
(`gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-sports-pipelinecheck-20260801-102347-2bf067/run.log`)
shows every candle-parquet write and every manifest `_index/per_vm/...` write failing with
`PERMISSION_DENIED: uts-prd-sa@... does not have storage.objects.create access`, against both
`market-data-tick-sports-test-central-element-323112` (16 occurrences — the `--output-bucket` target) and
`market-data-tick-sports-prd-central-element-323112` (932 occurrences — some manifest/index writes evidently still
target the prod-tier default path even when candle output is routed to `-test-`, a second, narrower finding worth its
own look but secondary to the identity-level block). 4425 total `403`s logged in ~19 minutes of VM runtime before I
stopped it (compute continued — polars aggregation/pivoting kept running per-fixture even though every write failed,
shard-level failure isolation correctly kept it from crashing, but it could never succeed). I additionally live-verified
`uts-test-sa`'s mirrored `group-a-test-tier-only` condition has the identical bug (`market-data-tick-test-` prefix, same
missing-segment shape) — so even re-launching with `--env staging/dev` (→ `uts-test-sa`) would hit the same wall on
market-data-tick buckets specifically.

## Why it matters

- **Any VM launched through `launch-mdps-backfill-vm.sh`'s current default (`DEPLOYMENT_ENV=prod` → `uts-prd-sa`) cannot
  write real candle output**, for any asset group — confirmed live, not theoretical. I checked whether this is ALREADY
  blocking scheduled production backfills: `market-data-tick-cefi-prd-.../processed_candles/` has objects written as
  recently as 2026-07-29T01:19Z (day=2026-07-28) and `market-data-tick-sports-prd-.../processed_candles/` as recently as
  2026-07-30T01:52Z (day=2026-07-29) — so regular scheduled MDPS backfills ARE currently succeeding, meaning they are
  NOT going through `uts-prd-sa` today (most likely still the default compute SA or `unified-trading-sa`, both of which
  hold working, unconditional storage grants per the related sibling issue docs). This bug is therefore **not yet
  manifesting in steady-state production** — but per
  `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`'s Finding 2 ("nothing anywhere in
  the codebase authenticates as uts-prd-sa yet" as of 2026-07-30), this MDPS launcher's `--service-account` wiring
  (`lc_tier_service_account`, its own comment references "P2.2d") looks like a recent addition — the FIRST real caller
  to reach this specific broken condition. That makes it a **live regression risk**: the moment any real
  (non-smoke-check) MDPS backfill runs through this launcher's current prod-tier-SA default, it will hit the identical
  100%-write-failure wall this smoke check just proved, with no advance warning.
- **Blocks the 3 sibling Track K checkpoint todos in the same plan** (`data-pipeline-check-is`, `-mtds`, `-features` —
  running concurrently in other slots as of this writing) IF any of them route through an MDPS candle-write path or a
  market-data-tick write via the tier SA; MDPS specifically cannot produce a genuine force-leg PASS until this is fixed.
- Per `data-pipeline-correctness-is-the-heartbate` + `findings-triage`'s "big finding (data-correctness...) → NOTIFY
  OPERATOR": this is exactly that class — a real, live, currently-active write-path regression on production
  infrastructure, not a theoretical gap.
- **This collides with the already-`operator_pending` SA-strategy decision** in
  `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` (BLK-0c84ceac) — but is DISTINCT
  and much narrower: that thread is "which SA scheme should govern" (per-tier vs per-service vs hybrid); this finding is
  "the ALREADY-DECIDED, ALREADY-LIVE per-tier scheme's own `market-data-tick` condition doesn't match its own declared
  bucket family, for any asset group" — a bug-fix restoring already-agreed scope, not a new policy question. I did NOT
  apply this fix myself: (a) it is a `terraform/gcp/` project-level IAM change, squarely `assigned_role: infra` and
  outside `data_engineering`'s craft (`does_not: infra/VM launches → infra`); (b) touching this SA's grants at all while
  BLK-0c84ceac is open risks stepping on the infra role's in-flight sequencing work on the same file.

## Interaction with the sibling `--env staging` gap (read before fixing either alone)

A sibling finding from the same plan's Track K (features) checkpoint,
`/plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`, independently discovered that
none of the 4 `pipeline_e2e_check.py` drivers pass `--env staging` when launching a `-test-`-bucket smoke VM, so all 4
launch under `uts-prd-sa` (prod-tier) instead of `uts-test-sa` (test-tier) — and shipped a fix for `features-service`,
with a P0 todo to apply the same fix to `market-data-processing-service`. **That fix alone is NOT sufficient for MDPS**:
`features-sports-test-*` is a Group B bucket (correctly per-AG-enumerated even today), so `--env staging` alone gets it
a working `uts-test-sa` grant. `market-data-tick-sports-test-*` is Group A — and `uts-test-sa`'s mirrored
`group-a-test-tier-only` condition has the IDENTICAL missing-asset-group-segment bug as `uts-prd-sa`'s (live-verified
above: `market-data-tick-test-` prefix, not `market-data-tick-sports-test-`). **Both fixes are required together**
before an MDPS Track K checkpoint can get a genuine PASS: the sibling issue's `--env staging` fix (routes to the right
tier SA) AND this issue's terraform fix (makes that tier SA's Group A condition actually match the real bucket name).
Landing only one will still 403 for MDPS specifically.

## Recommended fix

In `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf`, split `group_a_bucket_prefixes` so the AG-scoped
`market-data-tick-` family gets the same per-AG enumeration Group B already uses, while leaving the genuinely-flat
`instruments-store-`/`features-calendar-` prefixes as single entries:

```hcl
locals {
  group_a_flat_bucket_prefixes = [
    "instruments-store-",
    "features-calendar-",
  ]
  group_a_market_data_tick_ag_prefixes = [
    "market-data-tick-cefi-", "market-data-tick-defi-", "market-data-tick-tradfi-",
    "market-data-tick-sports-", "market-data-tick-pred-",
  ]
  group_a_bucket_prefixes = concat(local.group_a_flat_bucket_prefixes, local.group_a_market_data_tick_ag_prefixes)
}
```

(confirm the exact 5-AG set — cefi/defi/tradfi/sports/pred — against `market-tick-data-service/gcp/main.tf`'s and
`market-data-processing-service`'s live bucket declarations before applying; `pred` naming should mirror Group B's
`features-pred-` convention, not assume `-prediction-`). No other file needs to change — the
`for prefix in local.group_a_bucket_prefixes` loops that build the CEL `startsWith` clauses already handle an
arbitrary-length list. Apply via `tofu plan`/`tofu apply` on the `deployment-service` GCP terraform root, live-verify
with a fresh `gcloud projects get-iam-policy` read-back + a real MDPS backfill VM write, per this plan's own P1.2/P2.1
precedent for verifying grants live rather than trusting `tofu apply`'s exit code alone.

## CORRECTION (2026-08-01, slot 15) — `instruments-store-` is NOT flat/correct either; todo 3 answered

This doc's "What I found" section claims `instruments-store-` and `features-calendar-` "are genuinely flat/non-AG-scoped
buckets, so those two ARE correctly matched." **That is wrong for `instruments-store-`** — live-verified while executing
`sports_consolidated_native_ao_extract-029` (Track K IS baseline checkpoint): real buckets ARE asset-group-scoped
(`gsutil ls -p central-element-323112` shows `instruments-store-cefi-prd-...`, `instruments-store-sports-test-...`,
`-defi-`, `-pred-`, `-tradfi-` for both tiers — the exact same `{family}-{ag}-{tier}-{project}` shape as
`market-data-tick-`), and a real VM write against `instruments-store-sports-test-central-element-323112` under
`uts-test-sa` (post-DP-VM-002 fix, so the CORRECT tier SA was already in use) still 403s:

```
uts-test-sa@central-element-323112.iam.gserviceaccount.com does not have storage.objects.create access ...
Permission 'storage.objects.create' denied on resource '.../buckets/instruments-store-sports-test-central-element-323112
/objects/instrument_availability/by_date/day=2025-12-20/league=ALBANIA_SUPERLIGA/venue=API_FOOTBALL/instruments.parquet'
```

(evidence:
`gs://deployment-scripts-central-element-323112/vm-logs/instr-backfill-sports-pchk-0801110449-f-api-football/run.log`,
run at 11:07-11:08Z, `pipeline_e2e_check.py`'s "Fetched 724 fixtures" confirms this is a genuine adapter-level success
blocked purely at the storage-write layer — not a data-fetch problem.) `features-calendar-` I have not independently
re-verified — flagging as unconfirmed rather than assuming it's fine by the same pattern.

**Answers todo 3 below**: YES, the sibling Track K (IS) checkpoint hits this identical identity-level block, on the
`instruments-store-` prefix specifically (not `market-data-tick-`, which IS already fixed per the live IAM state I
re-checked this session — `group-a-test-tier-only`/`group-a-prd-tier-only` now correctly enumerate
`market-data-tick-{cefi,defi,tradfi,sports,pred}-test-`/`-prd-` individually). `instruments-store-` remains the SAME
single flat un-enumerated prefix as before. The recommended fix's `group_a_flat_bucket_prefixes` list (treating
`instruments-store-` as flat) needs revising — it should move to per-AG enumeration exactly like
`group_a_market_data_tick_ag_prefixes`, leaving only `features-calendar-` (genuinely no per-AG variant exists per
`gsutil ls`) as flat.

## Todos

- [x] ✅ [INFRA] P0. **PARTIALLY DONE — `market-data-tick-` half only.** Fixed `group_a_bucket_prefixes` in
      `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf` to enumerate
      `market-data-tick-{cefi,defi,tradfi,     sports,pred}-` per-AG (mirroring `group_b_bucket_prefixes`) —
      live-verified via `gcloud projects get-iam-policy` 2026-08-01 (slot 15): both `group-a-{prd,test}-tier-only`
      conditions now correctly enumerate all 5 asset groups for `market-data-tick-`. **`instruments-store-` was left as
      a flat entry and is STILL BROKEN** — see the correction above. (repo: deployment-service) — Shipped:
      `deployment-service@4a93aac` (slot 2, infra role). Verification beyond the policy read-back cited above: a real
      impersonated `storage.objects.create` write to `market-data-tick-sports-test-...` under `uts-test-sa` succeeded
      (cleaned up after); the `-prd-` side was confirmed read-only via `gcloud asset     analyze-iam-policy` against
      `market-data-tick-sports-prd-...` under `uts-prd-sa` (no real write attempted on prod, per this todo's own
      instruction). `tofu plan` scoped to the two touched IAM-condition resources showed 0 drift post-apply.
- [ ] [INFRA] P0. Extend the same per-AG fix to `instruments-store-`:
      `group_a_instruments_store_ag_prefixes =     ["instruments-store-cefi-", "instruments-store-defi-", "instruments-store-tradfi-", "instruments-store-sports-",     "instruments-store-pred-"]`
      (mirror the market-data-tick pattern exactly; confirm the 5-AG set against
      `gsutil ls -p central-element-323112 | grep instruments-store`, already confirmed present above), added to
      `group_a_bucket_prefixes` alongside the market-data-tick per-AG list, leaving only `features-calendar-` flat.
      Apply via `tofu apply`, live-verify with `gcloud projects get-iam-policy` + a real IS `--test-run` write (rerun
      `sports_consolidated_native_ao_extract-029`'s baseline checkpoint once landed). (repo: deployment-service)
- [ ] [DATA] P1. Once the IAM fix lands, re-run Track K (MDPS)'s 3 SPORTS checkpoints
      (`sports_consolidated_native_ao_extract-031`) for a genuine force/skip PASS/FAIL verdict — my baseline checkpoint
      only proved the infra was broken, not the candle-derivation logic itself. (repo: market-data-processing-service)
- [x] ✅ [DATA] P2. **DONE 2026-08-01 (slot 15)** — see the CORRECTION section above. Track K (IS) hits the identical
      identity-level block, on `instruments-store-` specifically. MTDS/features not independently re-checked this pass
      (features already confirmed fixed per the sibling `--env staging` doc; MTDS unconfirmed).
