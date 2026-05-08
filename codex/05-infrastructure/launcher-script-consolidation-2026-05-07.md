---
scope: [engineer, admin]
---

# Launcher-script consolidation (2026-05-07)

## Why this exists

The workspace SSOT is "every VM launcher lives under `deployment-service/scripts/vm/`"
([`launcher-script-ssot.md`](launcher-script-ssot.md)). Pre-2026-05-07 we had ~30 ad-hoc launchers scattered across
`e2e-testing/scripts/`, `features-*-service/scripts/`, plus the intra-repo
`deployment-service/scripts/deploy-dashboard-gce-vm.sh`. Each ad-hoc launcher (a) bypassed the deployment-UI's
Deploy-Missing button registry (`_SERVICE_LAUNCHER_SCRIPTS`), (b) drifted from the workspace conventions
(`MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=<unique-tag>`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`, `VM_PREFIX_TO_BUCKET`), and
(c) created collision risk in parallel-agent reasoning. This doc tracks the migration to the SSOT shape.

## Migration table

| Old path                                                                  | New path under `deployment-service/scripts/vm/`         | Status                       |
| ------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------- |
| `e2e-testing/scripts/launch-cefi-backfill.sh`                             | `launch-cefi-{venue}-{flavor}-vm.sh`                    | (per-venue migration)        |
| `e2e-testing/scripts/launch-tradfi-backfill.sh`                           | `launch-tradfi-{root}-{flavor}-vm.sh`                   | (per-root migration)         |
| `e2e-testing/scripts/launch-sports-backfill.sh`                           | `launch-sports-{source}-vm.sh`                          | shipped                      |
| `e2e-testing/scripts/launch-prediction-backfill.sh`                       | `launch-prediction-{venue}-vm.sh`                       | shipped                      |
| `e2e-testing/scripts/launch-defi-backfill.sh`                             | `launch-defi-{chain}-{flavor}-vm.sh`                    | (per-chain migration)        |
| `features-onchain-service/scripts/launch-*.sh`                            | `launch-features-onchain-vm.sh` (or asset-scoped)       | folds into features-service consolidation |
| `features-volatility-service/scripts/launch-*.sh`                         | `launch-features-volatility-vm.sh`                      | folds into features-service consolidation |
| `features-cross-instrument-service/scripts/launch-*.sh`                   | `launch-features-cross-instrument-vm.sh`                | folds into features-service consolidation |
| `features-sports-service/scripts/launch-*.sh`                             | `launch-features-sports-vm.sh`                          | folds into features-service consolidation |
| `features-prediction-service/scripts/launch-*.sh`                         | `launch-features-prediction-vm.sh`                      | folds into features-service consolidation |
| `deployment-service/scripts/deploy-dashboard-gce-vm.sh` (intra-repo)      | `deployment-service/scripts/vm/launch-dashboard-vm.sh`  | intra-repo move              |

Once a row is migrated:

1. The new launcher under `deployment-service/scripts/vm/` is canonical.
2. Its VM-name prefix is registered in `VM_PREFIX_TO_BUCKET`
   ([`vm-zombie-watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py)).
3. The script is registered in `_SERVICE_LAUNCHER_SCRIPTS` in
   `deployment-api/deployment_api/services/deploy_missing.py` so the UI's Deploy-Missing button surfaces it.
4. The old path is removed from its home repo.
5. Tarballs are refreshed via `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` so the new launcher's
   payload reaches the VM at boot.

## Why per-asset-group launchers (post features-service consolidation)

The features-service consolidation
([`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md)) collapses
5–6 features-* repos into a single repo with sub-packages. The per-asset-group launchers (e.g.
`launch-features-cefi-vm.sh` for the colocated cefi cluster) replace the 5–6 per-repo launchers with one launcher per
deployment-cluster shape (asset-scoped vs cross-cutting).

## What goes wrong without this consolidation

- **Deploy-Missing UI button** can't render for unregistered services — operators run the ad-hoc script manually,
  bypassing the dashboard.
- **Watchdog blindness** — VMs with prefixes not in `VM_PREFIX_TO_BUCKET` zombie forever burning money on a network
  partition. (Reference 2026-05-05 incident: 5 prefixes silently zombied.)
- **Workspace conventions drift** — ad-hoc launchers forget `MANIFEST_PER_VM_SHARDS=true`, leading to manifest race
  bugs when concurrent VMs run.

## Cross-references

- Launcher SSOT: [`launcher-script-ssot.md`](launcher-script-ssot.md)
- VM tarball deployment: [`vm-tarball-deployment.md`](vm-tarball-deployment.md)
- Features-service architecture: [`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md)
- Watchdog dict: `deployment-service/scripts/vm/vm_zombie_watchdog.py` (`VM_PREFIX_TO_BUCKET`)
- Deploy-Missing registry: `deployment-api/deployment_api/services/deploy_missing.py`
  (`_SERVICE_LAUNCHER_SCRIPTS`)
