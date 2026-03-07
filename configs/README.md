# unified-trading-pm/configs — PM-Level Configs

This directory contains workspace-wide configuration files that are the single source of truth (SSOT) for runtime
behavior.

## Files

| File                    | Purpose                                                                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `runtime-topology.yaml` | Runtime interaction topology — defines messaging transports, storage backends, and deployment profiles per mode. Consumed by deployment-service, libraries, and quality gates. |

## Usage

Set `RUNTIME_TOPOLOGY_PATH` env var to override the default location. When unset, services resolve it as:
`{WORKSPACE_ROOT}/unified-trading-pm/configs/runtime-topology.yaml`

The `WORKSPACE_ROOT` env var should point to the root of this multi-repo workspace.

## Ownership

All files here are owned by `unified-trading-pm`. Individual repos read from here; they do not own these configs.
