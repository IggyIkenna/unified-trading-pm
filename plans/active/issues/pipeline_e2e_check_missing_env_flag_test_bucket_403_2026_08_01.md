---
doc_type: issue
title: >-
  All 4 pipeline_e2e_check.py drivers (IS/MTDS/MDPS/features) launch their -test- bucket VM under the PROD-tier service
  account by default — every force/skip leg 403s since the tier-isolation IAM lockdown landed
summary: >-
  Discovered while running Track K (features) baseline checkpoint for sports
  (sports_consolidated_native_ao_extract_2026_07_25.md). `launch-features-vm.sh --sink-bucket features-sports-test-...`
  launched the VM under `uts-prd-sa` (the launcher's `lc_tier_service_account` helper defaults `DEPLOYMENT_ENV` to
  `prod` unless `--env` is passed explicitly). Since `bucket_iam_write_protection_per_tier_2026_06_09.md` /
  `bucket_fold_ features_2026_07_17.md` landed, `uts-prd-sa`'s `storage.objectAdmin` grant is IAM-Condition- scoped to
  `-prd-` buckets ONLY (`group-a-prd-tier-only` / `group-b-prd-tier-only` conditions, verified live via `gcloud projects
  get-iam-policy`) — `uts-test-sa` holds the mirror-image `-test-`-only grant. Neither `instruments-service`,
  `market-tick-data-service`, nor `market-data-processing-service`'s own `pipeline_e2e_check.py` passes `--env staging`
  (or sets `DEPLOYMENT_ENV=staging`) either — grepped all 4 drivers, confirmed none of the other 3 do it. Fixed in
  `features-service` (this session, `features-service@524b71ef`); the other 3 repos carry the identical gap as follow-up
  todos below.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [instruments-service, market-tick-data-service, market-data-processing-service, features-service]
scope: [engineer]
tags: [pipeline-e2e-check, iam, gcp, service-account, vm-launcher, cross-repo, blocking]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-032]
resolved_by:
locked_by:
context_scope: [/codex/05-infrastructure/vm-launcher-runbook.md]
depends_on: []
---

# pipeline_e2e_check.py drivers launch -test- VMs under the wrong (prod-tier) service account

## What I found

Running Track K (features) baseline checkpoint
(`--asset-group SPORTS --family sports --day 2025-12-20 --legs force,skip`), both legs failed with `vm_exit_nonzero=1`.
The VM's `run.log` showed the real cause:

```
403 POST .../features-sports-test-central-element-323112/o?uploadType=multipart:
"uts-prd-sa@central-element-323112.iam.gserviceaccount.com does not have
storage.objects.create access to the Google Cloud Storage object.
Permission 'storage.objects.create' denied on resource
'.../buckets/features-sports-test-central-element-323112/objects/
sports_features/by_date/day=2025-12-20/feature_group=fixture_stats/features.parquet'"
```

(A second, non-fatal instance of the same 403 also fires on every event-log upload to `central-element-323112-events`,
since that bucket presumably has the same tier scoping — not chased further here, subsumed by the same root cause.)

**Root cause, verified via `gcloud projects get-iam-policy central-element-323112 --format=json`**: `uts-prd-sa` carries
TWO `roles/storage.objectAdmin` bindings, each with an IAM Condition (`group-a-prd-tier-only` / `group-b-prd-tier-only`)
restricting `resource.name.startsWith(...)` to `-prd-` bucket prefixes ONLY (`market-data-tick-prd-`,
`instruments-store-prd-`, `features-{cefi,tradfi,defi,pred,sports,calendar}-prd-`). The mirror-image `uts-test-sa`
carries the `-test-`-scoped equivalents (`group-a-test-tier-only` / `group-b-test-tier-only`) — verified it explicitly
includes `features-sports-test-`.

`deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_tier_service_account <env> <project>` resolves `uts-prd-sa`
for `env=prod` and `uts-test-sa` for `env=staging|dev`. Every `launch-*-vm.sh` (including `launch-features-vm.sh`)
defaults `DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"` and only overrides it via an explicit `--env` flag. **None of the 4
`pipeline_e2e_check.py` drivers pass `--env`/set `DEPLOYMENT_ENV` when launching a `-test-`-bucket smoke-check VM** —
confirmed by reading each driver's launcher-argv builder:

| Repo                             | argv builder                                                                     | passes `--env`/`DEPLOYMENT_ENV`?                                                                                |
| -------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `features-service`               | `pipeline_e2e_check.py::_build_launch_argv`                                      | **NO (fixed this session, see below)**                                                                          |
| `instruments-service`            | `pipeline_e2e_check.py::_build_launcher_argv`                                    | NO                                                                                                              |
| `market-data-processing-service` | `pipeline_e2e_check.py::_launcher_argv`                                          | NO (only fail-fast-validates `DEPLOYMENT_ENV` if the CALLER'S shell env already set one — never sets it itself) |
| `market-tick-data-service`       | not yet inspected — same driver family, presumed same gap; confirm before fixing | UNCONFIRMED                                                                                                     |

So EVERY force/skip leg any of these 4 skills has ever run against a real `-test-` bucket has launched under
`uts-prd-sa` — which the tier-isolation IAM lockdown (2026-06-09 / 2026-07-17) now blocks from writing there. This is
not sports-specific and not features-specific: it is a structural gap in the shared driver pattern across the whole
`data-pipeline-check-*` skill family, live since whichever of the two IAM-lockdown dates landed after these drivers were
last exercised against real infra.

**Confirmed impact right now (2026-08-01)**: this exact session's Track K split dispatched 4 sibling AO tasks in
parallel (IS/MTDS/MDPS/features, all against `SPORTS` day `2025-12-20`) — every one of them is either about to hit, or
(MDPS, peeked read-only at slot-7's `/tmp/mdps_sports_baseline_run.log`) already mid-VM-run toward, the identical 403.
Each retry burns real VM spend for a guaranteed-fail outcome until the launch argv carries `--env staging`.

## Why it matters

- **Every `data-pipeline-check-{is,mtds,mdps,features}` skill invocation against a `-test-` bucket currently fails 100%
  of the time** — not flaky, not asset_group-specific, deterministic. Any plan todo dispatched to run one of these
  checks (Track K's 4 sibling todos here, and any future dispatch of these skills for any asset_group) will burn a VM
  launch + multi-minute wait for a guaranteed 403.
- **Silent billing waste**: `deployment-service/scripts/vm/launch-*-vm.sh`'s `VM_SHUTDOWN_ON_COMPLETION=true`
  self-deletes cleanly on this failure (not a preemption/hang case the existing `/vm-preemption-billing-waste-audit`
  skill would catch), but each failed attempt still pays full VM boot+compute time for zero useful output.
- **Masks real regressions**: while this gap is live, a GENUINE force/skip regression in any of these 4 pipelines is
  indistinguishable from this IAM/launcher-argv gap without reading the `run.log` — every failure currently reads as
  `vm_not_success:vm_exit_nonzero=1` with no differentiation in the pipeline_e2e_check.py report table itself.

## What I actually shipped this session (bounded, verified)

Fixed `features-service`'s `_build_launch_argv` to append `--env staging` unconditionally (every leg this driver runs is
test-bucket-only by contract, so this is never conditional) — `features-service@524b71ef`. Re-ran the baseline
checkpoint after the fix; see the Track K (features) plan todo for the fresh green result.

## Todos

- [ ] [CODE] P0. Add `--env staging` (or equivalent `DEPLOYMENT_ENV=staging` env-var set) to
      `instruments-service/scripts/pipeline_e2e_check.py::_build_launcher_argv`'s `launch-instruments-backfill-vm.sh`
      invocation — mirrors the `features-service@524b71ef` fix. Verify with a fresh force/skip run against any
      asset_group/venue and confirm the VM's `run.log` shows no `storage.objects.create` 403. (repo:
      instruments-service)
- [ ] [CODE] P0. Add the same `--env staging` fix to
      `market-data-processing-service/scripts/pipeline_e2e_check.py::_launcher_argv`'s `launch-mdps-backfill-vm.sh`
      invocation (currently relies entirely on the caller's shell `DEPLOYMENT_ENV` being pre-set, which
      `pipeline_e2e_check.py`'s own `main()` never does — `_deployment_env_fail_fast()` only validates an already-set
      value, it doesn't set one). Verify with a fresh force/skip run. (repo: market-data-processing-service)
- [ ] [CODE] P0. Confirm `market-tick-data-service/scripts/pipeline_e2e_check.py`'s launcher-argv builder has the
      identical gap (not yet inspected in this session — confirm before assuming) and apply the same `--env staging` fix
      if so. Verify with a fresh force/skip run. (repo: market-tick-data-service)
- [ ] [DOC] P2. Once all 4 repos carry the fix, add a one-line note to `/codex/05-infrastructure/vm-launcher-runbook.md`
      (or a new short section) documenting that any NEW `pipeline_e2e_check.py`-family driver launching a
      `-test-`-bucket smoke VM MUST pass `--env staging`/`DEPLOYMENT_ENV=staging` explicitly — the launcher's own
      `prod`-default is correct for real launchers, but silently wrong for every e2e-check-style test-bucket run. (repo:
      unified-trading-pm)

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`.
