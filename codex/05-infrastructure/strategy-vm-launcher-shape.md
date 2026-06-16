---
scope: [engineer]
status: stable
last_reviewed: 2026-05-12
related_plan: plans/active/promote_workflow_may23_cli_path_2026_05_10.md
---

# Strategy VM launcher shape — paper + live

> **Entry-point SSOT** for the two strategy VM launchers added in Phase 1 of
> `promote_workflow_may23_cli_path_2026_05_10.md`. Full launcher-governance rules:
> `codex/05-infrastructure/launcher-script-ssot.md`.

## Launchers

| Script                                                      | Purpose                            | Capital at risk        |
| ----------------------------------------------------------- | ---------------------------------- | ---------------------- |
| `deployment-service/scripts/vm/launch-strategy-paper-vm.sh` | Tenderly fork, simulated execution | No                     |
| `deployment-service/scripts/vm/launch-strategy-live-vm.sh`  | Copper MPC custody, mainnet        | **Yes — real capital** |

## Shared shape

Both launchers follow the canonical `deployment-service/scripts/vm/` contract:

- **VM-name pattern**: `strategy-{paper,live}-{archetype-slug}-{YYYYMMDD-HHMMSS}` (≤63 chars).
- **Boot**: `startup-script-url=gs://deployment-scripts-{pid}/vm/setup-data-pipeline-vm.sh`.
- **Code**: `setup-data-pipeline-vm.sh` routes on `VM_TASK={strategy-paper,strategy-live}` → downloads
  `strategy-service-code` + `execution-service-code` + `e2e-testing-code` tarballs.
- **Command dispatch**: `VM_BACKFILL_CMD` metadata key carries the full `bash scripts/defi/run-{paper,live}.sh ...`
  command. `setup-data-pipeline-vm.sh` executes it from `$WORKSPACE/e2e-testing`.
- **Shard isolation**: `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>` required per workspace rule.
- **Singleton lock**: refuses launch if same `(archetype-slug, zone)` VM already RUNNING (`--force` bypass).
- **Self-delete**: shutdown-script deletes the VM on completion.
- **Watchdog registration**: `"strategy-paper-": None` and `"strategy-live-": None` in `vm_zombie_watchdog.py`
  `VM_PREFIX_TO_BUCKET` (heartbeat-only — no per-VM data shards).

## Paper launcher specifics

```bash
bash deployment-service/scripts/vm/launch-strategy-paper-vm.sh \
  --archetype carry_staked_basis \
  --tick-interval 3600 \
  --continuous                  # optional — infinite loop
```

Runs `e2e-testing/scripts/defi/run-paper.sh --strategy <ARCHETYPE> --tick-interval <N> [--continuous]` via
`colocated_engine.py --mode paper --execution-provider tenderly`.

## Live launcher specifics

```bash
bash deployment-service/scripts/vm/launch-strategy-live-vm.sh \
  --archetype carry_staked_basis \
  --dry-run-live-cutover-passed   # mandatory for real launch
```

**Safety gate**: exits 4 unless `--dry-run-live-cutover-passed` OR `--force-live` supplied. This gate ensures Phase 8
dry-run (`promote_workflow_may23_cli_path_2026_05_10.md` Phase 8) completes before any real-capital launch.

Runs `e2e-testing/scripts/defi/run-live.sh --strategy <ARCHETYPE>` via
`colocated_engine.py --mode live --execution-provider copper`.

## Tarball refresh

After code changes to `strategy-service`, `execution-service`, or `e2e-testing`:

```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh \
  --include strategy-service --include execution-service \
  --include e2e-testing \
  --include unified-trading-library --include unified-api-contracts
```

Or `--asset-group DEFI` (which now includes `e2e-testing`).

## Event verification (per "No fire-and-forget VM launches" HARD RULE)

```bash
# Check STARTED event within 90s
gcloud storage cat \
  "gs://central-element-323112-events/events/strategy-service/$(date +%Y-%m-%d)/<VM_NAME>/hour=*/**.jsonl" \
  2>/dev/null | head -5

# Check running (should appear then disappear on completion)
gcloud compute instances list \
  --project=central-element-323112 \
  --filter="name~^strategy-paper- AND status=RUNNING"
```

## Known gaps (Phase 2 + beyond)

- `run-live.sh` has `read -rp "Type CONFIRM LIVE"` interactive prompt — blocks on non-interactive VM. Phase 2 adds
  `--non-interactive` flag to bypass. **DEFERRED to Phase 2.**
- `--archetype` vs `--strategy` flag drift: launchers pass `--strategy` (current run-\*.sh flag); Phase 2 adds
  `--archetype` + `--candidate-version` to run-paper.sh + run-live.sh. **DEFERRED to Phase 2.**
- Deploy-Missing UI button registration (`_SERVICE_LAUNCHER_SCRIPTS`): deferred to
  `launcher_scripts_consolidation_into_deployment_service_2026_05_07.md` Phase 2.
- `VmPrefixSpec` lifecycle class tagging: deferred to `deployment_ui_lifecycle_tabs_2026_05_08.md` Phase A.2.
