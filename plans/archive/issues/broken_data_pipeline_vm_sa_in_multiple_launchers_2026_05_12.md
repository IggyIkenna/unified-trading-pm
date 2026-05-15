---
title:
  Multiple VM launchers hardcode a non-existent `data-pipeline-vm` SA (gcloud `serviceAccount of type was not found`)
resolved: 2026-05-12
resolution_commit: deployment-service@357438a
created: 2026-05-12
author: harsh-mock-data-benchmarking-tab (slot 7)
source:
  - https://github.com/IggyIkenna/deployment-service/blob/live-defi-rollout/scripts/vm/launch-mdps-backfill-vm.sh
  - https://github.com/IggyIkenna/deployment-service/blob/live-defi-rollout/scripts/vm/launch-cefi-sharded-backfill.sh
  - https://github.com/IggyIkenna/deployment-service/blob/live-defi-rollout/scripts/vm/launch-mdps-sharded-backfill.sh
  - https://github.com/IggyIkenna/deployment-service/blob/live-defi-rollout/scripts/vm/launch-sfi-forward-poll.sh
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P1
suggested_owner: deployment-service maintainer (Ikenna-side, slot 1 main triage)
---

> **✅ RESOLVED 2026-05-12** via Option A (env-var-override) — deployment-service@`357438a`. 1 launcher updated
> (`launch-alerting-quietness-baseline.sh`). The other launchers mentioned in this issue body
> (`launch-mdps-backfill-vm.sh`, `launch-cefi-sharded-backfill.sh`, `launch-mdps-sharded-backfill.sh`,
> `launch-sfi-forward-poll.sh`) had already been refactored to omit `--service-account` entirely — verified at fix time.
> Reference template: deployment-service@`91ee79e` (launch-synthetic-benchmark-vm.sh). Verified 0 `data-pipeline-vm@`
> references remain in `deployment-service/scripts/vm/`.

## What I found

`gcloud iam service-accounts list --project=central-element-323112` does **not** include
`data-pipeline-vm@central-element-323112.iam.gserviceaccount.com`. Every VM launcher in
`deployment-service/scripts/vm/*.sh` that hardcodes that SA in
`--service-account=data-pipeline-vm@${PROJECT}.iam.gserviceaccount.com` will fail with:

```
ERROR: (gcloud.compute.instances.create) Could not fetch resource:
 - The resource 'data-pipeline-vm@central-element-323112.iam.gserviceaccount.com' of type 'serviceAccount' was not found.
```

Verified 2026-05-12 16:16 UTC while launching the synthetic-benchmark smoke VM
(`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md` Phase 5.B). My `launch-synthetic-benchmark-vm.sh` is fixed
(deployment-service@`91ee79e`) — defaults to `${PROJECT_NUMBER}-compute@developer.gserviceaccount.com` (the project's
Compute Engine default SA), overridable via `SERVICE_ACCOUNT=…` env var. Same shape of fix would unblock the other
launchers but each is owned by its consuming plan; I'm flagging not fixing (per Findings Triage Discipline).

### Affected launchers (grep for `data-pipeline-vm@`)

```bash
$ grep -l "data-pipeline-vm@" deployment-service/scripts/vm/*.sh
deployment-service/scripts/vm/launch-mdps-backfill-vm.sh
deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh
deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh
# (also several inline-startup launchers within deployment-service/scripts/vm/inline_startups/)
```

### What's actually running on the project's VMs (verified)

`gcloud compute instances list --project=central-element-323112 --format='value(serviceAccounts.email)'` returns
`1060025368044-compute@developer.gserviceaccount.com` for every currently-running VM (manifest-consolidator,
mtds-gas-fees, vm-zombie-watchdog). The hardcoded `data-pipeline-vm@…` is a ghost — likely the SA was created in a
sibling project (or deleted at some point) and not re-provisioned here.

## Why it matters

- Every operator who runs one of these launchers without checking SA-existence first hits the same dead-end I did (cost:
  ~10 min of VM-fail / debug cycle per attempt).
- For the May-23 cutover, the MDPS / cefi-sharded backfill launchers are on the critical path (Group F item 18,
  real-backfill calibration for the synthetic benchmark, etc.). Silent breakage delays the cutover.
- The hardcoded SA is also a SSOT-leak — if/when `data-pipeline-vm@…` IS provisioned, these launchers won't pick up the
  upgraded SA without a global edit.

## Recommended decision

Option A (preferred, ~30 min total): roll out the same
`SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"` env-var-overridable
default to every launcher in `deployment-service/scripts/vm/*.sh` that hardcodes `data-pipeline-vm@…`. Reference impl:
`launch-synthetic-benchmark-vm.sh` deployment-service@`91ee79e`.

Option B (~10 min): provision the `data-pipeline-vm` SA in `central-element-323112` with the same cloud-platform scope
the default-compute SA has; leaves the launchers as-is. **Operator decision required** because IAM SA-creation has
shared blast radius across the project.

Option A is the safer choice — no IAM mutation, every launcher gets a sensible default that already works for every
other VM in this project, and the env-var override leaves the door open for project-specific SAs in the future.

## Composes with

- CLAUDE.md "Findings Triage Discipline" — case 4 (outside every active plan; not service-owned per the rule's strict
  reading because the launchers cross multiple plans).
- CLAUDE.md "VM launcher script SSOT" — every `gcloud compute instances create` lives under
  `deployment-service/scripts/vm/`; fixes there propagate to every consumer.
- CLAUDE.md "No fire-and-forget VM launches" — broken SA means STARTED never emits, but the launcher exit code 1 is the
  failure mode operators see first.

## Suggested resolution timeline

P1 — resolve within 7 days (≤2026-05-19). Cutover deadline is 2026-05-23; the affected launchers (mdps-backfill,
cefi-sharded-backfill, mdps-sharded-backfill, sfi-forward-poll) are on the critical path.
