---
scope: infrastructure
status: stable
last_reviewed: 2026-05-07
---

# VM launcher script SSOT — `deployment-service/scripts/vm/`

The deployment-UI is the workspace's single SSOT for **how do we launch a VM**. Every script that runs
`gcloud compute instances create` (or the AWS `aws ec2 run-instances` equivalent) MUST live under
[`deployment-service/scripts/vm/`](../../../deployment-service/scripts/vm/). No exceptions.

## Why this rule exists

1. **One registry the UI can render.** The Deploy-Missing button + the operational dashboards both read from
   `_SERVICE_LAUNCHER_SCRIPTS` in
   [`deployment_api/services/deploy_missing.py`](../../../deployment-api/deployment_api/services/deploy_missing.py).
   Scattered launchers can't be rendered by the UI; operators end up cargo-culting copies of bash that drift
   in shape over time.
2. **Workspace conventions land in one place.** Every launcher must set
   `MANIFEST_PER_VM_SHARDS=true`, a unique `VM_NAME=<unique-tag>`,
   `RUN_TS="$(date +%Y%m%d-%H%M%S)"`, and register the prefix in `VM_PREFIX_TO_BUCKET` (CLAUDE.md
   "VM Naming Convention"). Forgetting any of these breaks per-VM shard isolation, the zombie watchdog,
   or the manifest concurrency protocol.
3. **Parallel-agent reasoning.** When two operators / agents launch at the same time, every
   launcher in `deployment-service/scripts/vm/` follows the same patterns; an agent reading any one
   knows the contract.

## Scope: what counts as a "VM launcher"

| Pattern | Move to `deployment-service/scripts/vm/`? |
|---|---|
| `gcloud compute instances create ...` | **Yes** — the canonical case. |
| `gcloud beta compute instances create ...` | **Yes**. |
| `aws ec2 run-instances ...` | **Yes** — same SSOT, parallel `launch-*-ec2.sh` shape. |
| Cloud Build job that launches a VM as a side effect | **Yes** — wrap the `gcloud` call in a launcher. |
| Local script (e.g. `instruments-service/scripts/local_fill_pairs.sh`) that runs in-process | **No** — pure local-process orchestration; no VM. |
| Service-repo orchestration script (e.g. `run_vm_backfill_e2e.sh`) that **invokes** a launcher but doesn't itself create a VM | **No** — let it stay; just ensure it `bash`-execs the canonical launcher. |
| `setup.sh` / `run_local.sh` / `smoke_matrix.py` | **No** — local dev / test scaffolding. |

## How the script reaches the VM (4 modes; UI exposes a toggle)

When a launcher runs, the **VM at boot** needs the launcher's transitive dependencies (UAC / UTL / service
source). Four modes resolve this; the UI's Deploy-Missing flow exposes the first two as a radio toggle.

### 1. Tarball (default / production)

`gs://deployment-scripts-${PID}/code/<tarball>.tar.gz` → `setup-data-pipeline-vm.sh` extracts at boot →
launcher invoked. Refresh via:

```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh --all
```

(or the per-asset_group variant). Stale tarball = stale code on the VM. Operators must remember to refresh
when they push fixes; the
[`deploy_missing_auto_launch_2026_05_07`](../../plans/ai/deploy_missing_auto_launch_2026_05_07.plan.md)
successor plan adds an automatic refresh step.

### 2. Tarball-from-local (developer path; Deploy-Missing UI mode toggle)

The UI's `DeployMissingButton` exposes a radio toggle:

* **preview** (default) — launcher invocation against the GCS tarball that's currently in the bucket.
  Safe in any environment; operator copies + runs from their authenticated terminal.
* **tarball-from-local** — pairs the launcher with `create-code-tarballs.sh --all` via `&&` so the VM
  boots the OPERATOR'S LOCAL working tree (uncommitted edits included). **ONLY works from the operator's
  workstation**, never from the deployment-api Cloud Run pod / CI runners / shared shells. The
  endpoint emits a `LOCAL-ONLY + UNCOMMITTED CHANGES` warning, surfaced in the UI as a prominent amber
  panel above the command.

Implementation:
[`deployment-api/deployment_api/services/deploy_missing.py`](../../../deployment-api/deployment_api/services/deploy_missing.py)
+
[`deployment-ui/src/components/DeployMissingButton.tsx`](../../../deployment-ui/src/components/DeployMissingButton.tsx).

### 3. Sibling-clone (local-stack dev)

The operator's workstation has every service repo cloned as siblings under `${WORKSPACE_ROOT}` per the
workspace-manifest pattern. Local launches assume `deployment-service` exists at
`${WORKSPACE_ROOT}/deployment-service/scripts/vm/...`. CI / Cloud Run pods do NOT have sibling clones;
they read from the tarball.

### 4. Image (future, not yet shipped)

Bake the launcher set into a Docker image cached in Artifact Registry / ECR. The deployment-api would
pull + run a per-shard launch container rather than `gcloud compute instances create`-ing a fresh VM
each time. Tracked in
[`deploy_missing_auto_launch_2026_05_07.plan.md`](../../plans/ai/deploy_missing_auto_launch_2026_05_07.plan.md);
out of scope today.

## Adding a new launcher

1. **File** — `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh`
   (or `launch-{operation}-vm.sh` for cross-asset ops).
2. **VM-name prefix** — register in
   [`VM_PREFIX_TO_BUCKET`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py) (CLAUDE.md
   "VM Naming Convention" rule). After the dict edit, **relaunch the watchdog VM** so it picks up the
   new prefix.
3. **Deploy-Missing registry** — add to
   [`_SERVICE_LAUNCHER_SCRIPTS`](../../../deployment-api/deployment_api/services/deploy_missing.py)
   if the launcher should be reachable from the Deploy-Missing UI button.
4. **Tarball inclusion** — if the launcher depends on code outside CORE
   (`UAC` / `UTL` / `MTDS` / `deployment-service`), add an `--include <repo>` line in
   `create-code-tarballs.sh` or use `--asset-group X` to include the right scope.

## Migration in flight (2026-05-07)

29 ad-hoc VM launchers + 1 dashboard launcher live outside `deployment-service/scripts/vm/`:

| Source | Count | Pattern |
|---|---|---|
| `e2e-testing/scripts/common/` | 4 | `launch_*_vm.sh` |
| `e2e-testing/scripts/defi/` | 10 | `launch_*_vm.sh` |
| `e2e-testing/scripts/prediction/` | 4 | `launch_*_vm.sh` + `setup-backfill-vm.sh` |
| `e2e-testing/scripts/sports/` | 10 | `launch_*_vm.sh` + sweep wrappers |
| `features-sports-service/scripts/` | 1 | `launch_parallel_backfill.sh` |
| `deployment-service/scripts/` | 1 | `deploy-dashboard-gce-vm.sh` (move into `scripts/vm/`) |
| **Total** | **30** | |

Plan:
[`plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md`](../../plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md).

Until the plan ships:

* Deploy-Missing UI button degrades to "no launcher registered" for services whose launcher hasn't
  migrated yet. Operators run the ad-hoc script manually from their terminal.
* Source-repo callsites (Makefiles / READMEs / GHA workflows) keep their current paths; the
  migration plan updates them in lockstep with each move.

## References

* CLAUDE.md "VM launcher script SSOT" rule (cursor-configs/CLAUDE.md, codified 2026-05-07).
* CLAUDE.md "VM tarball deployment" — `create-code-tarballs.sh --all` + boot path.
* CLAUDE.md "VM Naming Convention" — `VM_PREFIX_TO_BUCKET` registry.
* [`codex/05-infrastructure/vm-tarball-deployment.md`](vm-tarball-deployment.md) — tarball mechanics.
* [`plans/ai/deploy_missing_auto_launch_2026_05_07.plan.md`](../../plans/ai/deploy_missing_auto_launch_2026_05_07.plan.md)
  — preview → auto-launch successor.
* [`plans/active/aws_migration_defi_first_2026_05_07.plan.md`](../../plans/active/aws_migration_defi_first_2026_05_07.plan.md)
  — bigger AWS S3 / ECR / EC2-launcher work.
