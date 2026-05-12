---
scope: infrastructure
status: stable
last_reviewed: 2026-05-10
---

# VM launcher script SSOT — `deployment-service/scripts/vm/`

The deployment-UI is the workspace's single SSOT for **how do we launch a VM**. Every script that runs
`gcloud compute instances create` (or the AWS `aws ec2 run-instances` equivalent) MUST live under
[`deployment-service/scripts/vm/`](../../../deployment-service/scripts/vm/). No exceptions.

## Why this rule exists

1. **One registry the UI can render.** The Deploy-Missing button + the operational dashboards both read from
   `_SERVICE_LAUNCHER_SCRIPTS` in
   [`deployment_api/services/deploy_missing.py`](../../../deployment-api/deployment_api/services/deploy_missing.py).
   Scattered launchers can't be rendered by the UI; operators end up cargo-culting copies of bash that drift in shape
   over time.
2. **Workspace conventions land in one place.** Every launcher must set `MANIFEST_PER_VM_SHARDS=true`, a unique
   `VM_NAME=<unique-tag>`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`, and register the prefix in `VM_PREFIX_TO_BUCKET`
   (CLAUDE.md "VM Naming Convention"). Forgetting any of these breaks per-VM shard isolation, the zombie watchdog, or
   the manifest concurrency protocol.
3. **Parallel-agent reasoning.** When two operators / agents launch at the same time, every launcher in
   `deployment-service/scripts/vm/` follows the same patterns; an agent reading any one knows the contract.

## Scope: what counts as a "VM launcher"

| Pattern                                                                                                                      | Move to `deployment-service/scripts/vm/`?                                 |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `gcloud compute instances create ...`                                                                                        | **Yes** — the canonical case.                                             |
| `gcloud beta compute instances create ...`                                                                                   | **Yes**.                                                                  |
| `aws ec2 run-instances ...`                                                                                                  | **Yes** — same SSOT, parallel `launch-*-ec2.sh` shape.                    |
| Cloud Build job that launches a VM as a side effect                                                                          | **Yes** — wrap the `gcloud` call in a launcher.                           |
| Local script (e.g. `instruments-service/scripts/local_fill_pairs.sh`) that runs in-process                                   | **No** — pure local-process orchestration; no VM.                         |
| Service-repo orchestration script (e.g. `run_vm_backfill_e2e.sh`) that **invokes** a launcher but doesn't itself create a VM | **No** — let it stay; just ensure it `bash`-execs the canonical launcher. |
| `setup.sh` / `run_local.sh` / `smoke_matrix.py`                                                                              | **No** — local dev / test scaffolding.                                    |

## How the script reaches the VM (4 modes; UI exposes a toggle)

When a launcher runs, the **VM at boot** needs the launcher's transitive dependencies (UAC / UTL / service source). Four
modes resolve this; the UI's Deploy-Missing flow exposes the first two as a radio toggle.

### 1. Tarball (default / production)

`gs://deployment-scripts-${PID}/code/<tarball>.tar.gz` → `setup-data-pipeline-vm.sh` extracts at boot → launcher
invoked. Refresh via:

```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh --all
```

(or the per-asset_group variant). Stale tarball = stale code on the VM. Operators must remember to refresh when they
push fixes; the [`deploy_missing_auto_launch_2026_05_07`](../../plans/ai/deploy_missing_auto_launch_2026_05_07.md)
successor plan adds an automatic refresh step.

### 2. Tarball-from-local (developer path; Deploy-Missing UI mode toggle)

The UI's `DeployMissingButton` exposes a radio toggle:

- **preview** (default) — launcher invocation against the GCS tarball that's currently in the bucket. Safe in any
  environment; operator copies + runs from their authenticated terminal.
- **tarball-from-local** — pairs the launcher with `create-code-tarballs.sh --all` via `&&` so the VM boots the
  OPERATOR'S LOCAL working tree (uncommitted edits included). **ONLY works from the operator's workstation**, never from
  the deployment-api Cloud Run pod / CI runners / shared shells. The endpoint emits a `LOCAL-ONLY + UNCOMMITTED CHANGES`
  warning, surfaced in the UI as a prominent amber panel above the command.

Implementation:
[`deployment-api/deployment_api/services/deploy_missing.py`](../../../deployment-api/deployment_api/services/deploy_missing.py)

- [`deployment-ui/src/components/DeployMissingButton.tsx`](../../../deployment-ui/src/components/DeployMissingButton.tsx).

### 3. Sibling-clone (local-stack dev)

The operator's workstation has every service repo cloned as siblings under `${WORKSPACE_ROOT}` per the
workspace-manifest pattern. Local launches assume `deployment-service` exists at
`${WORKSPACE_ROOT}/deployment-service/scripts/vm/...`. CI / Cloud Run pods do NOT have sibling clones; they read from
the tarball.

### 4. Image (future, not yet shipped)

Bake the launcher set into a Docker image cached in Artifact Registry / ECR. The deployment-api would pull + run a
per-shard launch container rather than `gcloud compute instances create`-ing a fresh VM each time. Tracked in
[`deploy_missing_auto_launch_2026_05_07.md`](../../plans/ai/deploy_missing_auto_launch_2026_05_07.md); out of scope
today.

## Adding a new launcher

1. **File** — `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh` (or `launch-{operation}-vm.sh` for
   cross-asset ops).
2. **VM-name prefix** — register in
   [`VM_PREFIX_TO_BUCKET`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py) (CLAUDE.md "VM Naming
   Convention" rule). After the dict edit, **relaunch the watchdog VM** so it picks up the new prefix.
3. **Deploy-Missing registry** — add to
   [`_SERVICE_LAUNCHER_SCRIPTS`](../../../deployment-api/deployment_api/services/deploy_missing.py) if the launcher
   should be reachable from the Deploy-Missing UI button.
4. **Tarball inclusion** — if the launcher depends on code outside CORE (`UAC` / `UTL` / `MTDS` / `deployment-service`),
   add an `--include <repo>` line in `create-code-tarballs.sh` or use `--asset-group X` to include the right scope.

### Codified governance gaps (PRE_CUTOVER backlog, codified 2026-05-12)

Today every step above is **reviewer-discipline-only** — no automated check enforces a launcher registration. Two known
foot-guns:

- **Step 2 gap** — a new prefix added to `VM_PREFIX_TO_BUCKET` without a watchdog VM relaunch leaves the prefix
  un-watched. Reference incident 2026-05-05 (5 prefixes silently un-watched → zombie burn). **Proposed QG check**:
  correlate `git log -p deployment-service/scripts/vm/vm_zombie_watchdog.py | grep VM_PREFIX_TO_BUCKET` against the
  watchdog VM relaunch event in `gs://...vm-logs/vm-zombie-watchdog-*/EXIT_STATUS`. **Status**: unbacked — owner is
  governance + slot 11 (launcher-consolidation owner); design tradeoff between agent-run check vs operator-discipline
  reminder.
- **Step 3 gap** — a new launcher under `launch-*.sh` without a `_SERVICE_LAUNCHER_SCRIPTS` registration silently
  degrades the Deploy-Missing UI button to "no launcher registered" (per "What goes wrong" enumeration further down this
  doc). **Proposed QG check**: static dual-list parity check — every file matching `launch-*.sh` must appear in the dict
  (or in an explicit allowlist of "intentionally non-Deploy-Missing-reachable" launchers like internal-tooling /
  one-off-audit launchers). **Status**: unbacked — owner is governance + slot 11.

Both QG-check ADDs are **operator-design-gated** as of 2026-05-12 — the closed-set policy (auto-fail vs warning,
allowlist taxonomy, false-positive cost) needs an operator call before the check is wired into `scripts/quality_gates/`.
Tracked as PRE_CUTOVER backlog in `plans/active/issues/codex_audit_ops_2026_05_12.md` findings O-7 + O-8.

## features-service consolidation (2026-05-08)

The pre-2026-05-08 layout had 8 per-family launchers (`launch-features-onchain-vm.sh`,
`launch-features-volatility-vm.sh`, `launch-features-cross-instrument-vm.sh`, `launch-features-sports-vm.sh`,
`launch-features-calendar-vm.sh`, `launch-features-commodity-vm.sh`, `launch-features-delta-one-vm.sh`,
`launch-features-multi-timeframe-vm.sh`).

Per [`features_repo_consolidation_2026_05_08`](../../plans/active/features_repo_consolidation_2026_05_08.md) Phase 8A,
those 8 launchers collapse to a single `deployment-service/scripts/vm/launch-features-vm.sh` parameterised by
`--feature-family` + `--asset-group`. The consolidated launcher:

1. Reads `--feature-family` from its argv + validates against the UAC `FeatureFamily` StrEnum (8 members).
2. Reads `--asset-group` per the workspace VM-Naming convention.
3. Composes the VM name as `features-{asset_group_lower}-{feature_family}-{ts}` — e.g.
   `features-defi-onchain-20260508-152400`. The `features-` prefix is registered ONCE in `VM_PREFIX_TO_BUCKET`,
   replacing the 8 per-family prefixes that would otherwise be needed.
4. Boots with `python -m features_service --feature-family <X> ...` per the dispatcher contract in
   [`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

**Tarball impact**: `create-code-tarballs.sh --asset-group X` includes the single `features-service/` repo (rather than
the 8 prior `features-*-service` repos). The consolidated tarball is smaller (deduplicated boilerplate + shared common/
directory) and faster to refresh.

**Architecture SSOT**:
[`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

## Migration status (2026-05-10): 10 shipped Tab 11 + 20 deferred

The pre-2026-05-08 baseline of 29 ad-hoc VM launchers + 1 dashboard launcher outside `deployment-service/scripts/vm/`
has been substantially migrated. Per
[`plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../../plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md)
DONE-2026-05-08 block: **10 launchers shipped Tab 11** (with 17 new VM_PREFIX_TO_BUCKET entries + watchdog VM relaunch);
the remaining **20 launchers are deferred** per documented per-launcher reasons (duplicates of canonical launchers,
collision-risk with in-flight tabs, partial supersession by canonical equivalents).

Source repo bucket counts (baseline 30):

| Source                             | Count  | Pattern                                                |
| ---------------------------------- | ------ | ------------------------------------------------------ |
| `e2e-testing/scripts/common/`      | 4      | `launch_*_vm.sh`                                       |
| `e2e-testing/scripts/defi/`        | 10     | `launch_*_vm.sh`                                       |
| `e2e-testing/scripts/prediction/`  | 4      | `launch_*_vm.sh` + `setup-backfill-vm.sh`              |
| `e2e-testing/scripts/sports/`      | 10     | `launch_*_vm.sh` + sweep wrappers                      |
| `features-sports-service/scripts/` | 1      | `launch_parallel_backfill.sh`                          |
| `deployment-service/scripts/`      | 1      | `deploy-dashboard-gce-vm.sh` (move into `scripts/vm/`) |
| **Total**                          | **30** |                                                        |

### Shipped 2026-05-08 (Tab 11 — 10 launchers)

| #   | Old path                                                         | New canonical path under `deployment-service/scripts/vm/` | Status + commit                                                |
| --- | ---------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------- |
| 1   | `e2e-testing/scripts/common/launch_mtds_category_backfill_vm.sh` | `launch-mtds-backfill-vm.sh`                              | shipped — deployment-service@76f4ecc + e2e-testing@8daba1a     |
| 2   | `e2e-testing/scripts/common/launch_instruments_backfill_vms.sh`  | `launch-instruments-backfill-vm.sh`                       | shipped — deployment-service@fbb3673 + e2e-testing@2da6867     |
| 3   | `features-sports-service/scripts/launch_parallel_backfill.sh`    | `launch-features-sports-parallel-backfill-vm.sh`          | shipped — deployment-service@0215086 + features-sports@06f6b30 |
| 4   | `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh`          | `launch-mtds-sports-odds-backfill-vm.sh`                  | shipped — deployment-service@2e1d967 + e2e-testing@deff088     |
| 5   | `e2e-testing/scripts/sports/launch_instruments_reference_v3.sh`  | `launch-sports-instruments-reference-vm.sh`               | shipped — deployment-service@fc9211e + e2e-testing@db7ace3     |
| 6   | `e2e-testing/scripts/defi/launch_dex_pools_vm.sh`                | `launch-mtds-dex-pools-backfill-vm.sh`                    | shipped — deployment-service@5778811 + e2e-testing@43d8e49     |
| 7   | `e2e-testing/scripts/defi/launch_eigenlayer_rewards_vm.sh`       | `launch-mtds-eigenlayer-rewards-backfill-vm.sh`           | shipped — deployment-service@5778811 + e2e-testing@43d8e49     |
| 8   | `e2e-testing/scripts/defi/launch_solana_drift_vm.sh`             | `launch-mtds-solana-drift-backfill-vm.sh`                 | shipped — deployment-service@5778811 + e2e-testing@43d8e49     |
| 9   | `e2e-testing/scripts/common/launch_cefi_migration_vm.sh`         | `launch-cefi-migration-vm.sh`                             | shipped — deployment-service@ce99d43 + e2e-testing@4f1f92b     |
| 10  | `e2e-testing/scripts/common/launch_defi_backfill_vm.sh`          | `launch-defi-backfill-vm.sh`                              | shipped — deployment-service@ce99d43 + e2e-testing@4f1f92b     |

**Migration shape** (each row): copy source → canonical destination, rename to canonical form, deprecation banner on old
path, register new prefix in `VM_PREFIX_TO_BUCKET`, smoke-test `--dry-run` (or `bash -n` syntax check), single-relaunch
of watchdog VM at end of cycle. **Watchdog VM** relaunched as `vm-zombie-watchdog-20260508-121344` after all 17 new
prefix entries landed.

### Deferred (20 launchers — documented reasons)

| Old path                                                          | Deferred reason                                                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `e2e-testing/scripts/defi/launch_gas_fees_vm.sh`                  | DEFERRED — duplicate of canonical `launch-mtds-gas-fees-backfill-vm.sh`; reconcile in delete-vs-merge follow-up.                                       |
| `e2e-testing/scripts/defi/launch_gas_fees_fleet.sh`               | DEFERRED — duplicate (fleet wrapper) of canonical `launch-mtds-gas-fees-backfill-vm.sh`.                                                               |
| `e2e-testing/scripts/defi/launch_lst_rates_vm.sh`                 | DEFERRED — duplicate of canonical `launch-mtds-lst-rates-backfill-vm.sh`.                                                                              |
| `e2e-testing/scripts/defi/launch_lending_indices_vm.sh`           | DEFERRED — duplicate of canonical `launch-mtds-lending-indices-backfill-vm.sh`; **Tab 9 (`lending-indices-relaunch-tab`) in flight** — collision risk. |
| `e2e-testing/scripts/defi/launch_perp_funding_vm.sh`              | DEFERRED — duplicate; canonical `mtds-perp-funding-` prefix already in watchdog.                                                                       |
| `e2e-testing/scripts/defi/launch_solana_gas_vm.sh`                | DEFERRED — defer post-May-23 cutover.                                                                                                                  |
| `e2e-testing/scripts/defi/launch_liquidations_vm.sh`              | DEFERRED — defer post-May-23 cutover.                                                                                                                  |
| `e2e-testing/scripts/prediction/launch_prediction_backfill_vm.sh` | DEFERRED — **Tab 10 (`predictions-phase1-ingestion-tab`) in flight** on prediction surface; collision risk.                                            |
| `e2e-testing/scripts/prediction/launch_prediction_features_vm.sh` | DEFERRED — collision with Tab 10 in flight on prediction surface.                                                                                      |
| `e2e-testing/scripts/prediction/launch_prediction_pipeline_vm.sh` | DEFERRED — collision with Tab 10 in flight on prediction surface.                                                                                      |
| `e2e-testing/scripts/prediction/setup-backfill-vm.sh`             | DEFERRED — collision with Tab 10 in flight on prediction surface.                                                                                      |
| `e2e-testing/scripts/sports/full_api_football_sweep.sh`           | DEFERRED — orchestrator that wraps other launchers; defer.                                                                                             |
| `e2e-testing/scripts/sports/full_sports_entity_sweep.sh`          | DEFERRED — orchestrator that wraps other launchers; defer.                                                                                             |
| `e2e-testing/scripts/sports/launch_fss_features_v3.sh`            | DEFERRED — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.                                          |
| `e2e-testing/scripts/sports/launch_fss_features_vm.sh`            | DEFERRED — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.                                          |
| `e2e-testing/scripts/sports/launch_fss_phase3_backfill.sh`        | DEFERRED — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.                                          |
| `e2e-testing/scripts/sports/launch_instruments_reference_vm.sh`   | DEFERRED — superseded by v3 form (#5 above).                                                                                                           |
| `e2e-testing/scripts/sports/launch_mdps_phase3_bucketing.sh`      | DEFERRED — partially superseded by canonical `launch-mdps-sports-bucket-vm.sh`; reconcile in follow-up.                                                |
| `e2e-testing/scripts/sports/launch_mdps_reprocess_vm.sh`          | DEFERRED — partially superseded by canonical `launch-mdps-sports-bucket-vm.sh`; reconcile in follow-up.                                                |
| `e2e-testing/scripts/sports/launch_oddspapi_vm_backfill.sh`       | DEFERRED — odds API specific; defer post-May-23 cutover.                                                                                               |

**Intra-repo move not in the e2e-testing list** (separate item): `deployment-service/scripts/deploy-dashboard-gce-vm.sh`
→ `deployment-service/scripts/vm/launch-dashboard-vm.sh`. DEFERRED — already inside deployment-service repo so callsite
drift risk is contained; intra-repo move ships in a follow-up cycle.

**Per-asset-group rename intentions for follow-up cycles** (canonical-shape patterns; not single migrations):

| Old path                                                             | New path under `deployment-service/scripts/vm/`        | Status                                    |
| -------------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------- |
| `e2e-testing/scripts/launch-cefi-backfill.sh`                        | `launch-cefi-{venue}-{flavor}-vm.sh`                   | per-venue migration pattern               |
| `e2e-testing/scripts/launch-tradfi-backfill.sh`                      | `launch-tradfi-{root}-{flavor}-vm.sh`                  | per-root migration pattern                |
| `e2e-testing/scripts/launch-sports-backfill.sh`                      | `launch-sports-{source}-vm.sh`                         | shipped (canonical sports launchers)      |
| `e2e-testing/scripts/launch-prediction-backfill.sh`                  | `launch-prediction-{venue}-vm.sh`                      | shipped (canonical prediction launchers)  |
| `e2e-testing/scripts/launch-defi-backfill.sh`                        | `launch-defi-{chain}-{flavor}-vm.sh`                   | per-chain migration pattern               |
| `features-onchain-service/scripts/launch-*.sh`                       | `launch-features-onchain-vm.sh` (or asset-scoped)      | folds into features-service consolidation |
| `features-volatility-service/scripts/launch-*.sh`                    | `launch-features-volatility-vm.sh`                     | folds into features-service consolidation |
| `features-cross-instrument-service/scripts/launch-*.sh`              | `launch-features-cross-instrument-vm.sh`               | folds into features-service consolidation |
| `features-sports-service/scripts/launch-*.sh`                        | `launch-features-sports-vm.sh`                         | folds into features-service consolidation |
| `features-prediction-service/scripts/launch-*.sh`                    | `launch-features-prediction-vm.sh`                     | folds into features-service consolidation |
| `deployment-service/scripts/deploy-dashboard-gce-vm.sh` (intra-repo) | `deployment-service/scripts/vm/launch-dashboard-vm.sh` | intra-repo move (deferred)                |

> **Folded in from `launcher-script-consolidation-2026-05-07.md`** (deleted by `codex_refactor_2026_05_08.md` Phase
> C.3).

Once a row is migrated:

1. The new launcher under `deployment-service/scripts/vm/` is canonical.
2. Its VM-name prefix is registered in `VM_PREFIX_TO_BUCKET`
   ([`vm-zombie-watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py)).
3. The script is registered in `_SERVICE_LAUNCHER_SCRIPTS` in `deployment-api/deployment_api/services/deploy_missing.py`
   so the UI's Deploy-Missing button surfaces it.
4. The old path is removed from its home repo.
5. Tarballs are refreshed via `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` so the new launcher's
   payload reaches the VM at boot.

### Why per-asset-group launchers (post features-service consolidation)

The features-service consolidation
([`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md)) collapses
5–6 features-\* repos into a single repo with sub-packages. The per-asset-group launchers (e.g.
`launch-features-cefi-vm.sh` for the colocated cefi cluster) replace the 5–6 per-repo launchers with one launcher per
deployment-cluster shape (asset-scoped vs cross-cutting).

### What goes wrong without this consolidation

- **Deploy-Missing UI button** can't render for unregistered services — operators run the ad-hoc script manually,
  bypassing the dashboard.
- **Watchdog blindness** — VMs with prefixes not in `VM_PREFIX_TO_BUCKET` zombie forever burning money on a network
  partition. (Reference 2026-05-05 incident: 5 prefixes silently zombied.)
- **Workspace conventions drift** — ad-hoc launchers forget `MANIFEST_PER_VM_SHARDS=true`, leading to manifest race bugs
  when concurrent VMs run.

Plan:
[`plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../../plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md).

Until the plan ships:

- Deploy-Missing UI button degrades to "no launcher registered" for services whose launcher hasn't migrated yet.
  Operators run the ad-hoc script manually from their terminal.
- Source-repo callsites (Makefiles / READMEs / GHA workflows) keep their current paths; the migration plan updates them
  in lockstep with each move.

## References

- CLAUDE.md "VM launcher script SSOT" rule (cursor-configs/CLAUDE.md, codified 2026-05-07).
- CLAUDE.md "VM tarball deployment" — `create-code-tarballs.sh --all` + boot path.
- CLAUDE.md "VM Naming Convention" — `VM_PREFIX_TO_BUCKET` registry.
- [`codex/05-infrastructure/vm-tarball-deployment.md`](vm-tarball-deployment.md) — tarball mechanics.
- [`plans/ai/deploy_missing_auto_launch_2026_05_07.md`](../../plans/ai/deploy_missing_auto_launch_2026_05_07.md) —
  preview → auto-launch successor.
- [`plans/active/aws_migration_defi_first_2026_05_07.md`](../../plans/active/aws_migration_defi_first_2026_05_07.md) —
  bigger AWS S3 / ECR / EC2-launcher work.
