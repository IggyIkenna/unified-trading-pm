---
scope: [engineer, admin]
title: VM Event Emission Compliance Audit
type: infrastructure
status: living
last_reviewed: 2026-05-17
owner: deployment-platform
---

# VM Event Emission Compliance Audit

**Author**: slot-2 agent  
**Date**: 2026-05-15  
**Scope**: All VM launchers in `deployment-service/scripts/vm/` + `setup-data-pipeline-vm.sh`

---

## Summary

| Category                                                  | Count | Status                                               |
| --------------------------------------------------------- | ----- | ---------------------------------------------------- |
| VM launchers with heartbeat/tee wrapper coverage          | ~83   | ✅ STARTED/COMPLETED/FAILED via `_launch_with_tee()` |
| VM launchers (backtest path — pre-fix)                    | 1     | ❌ bare nohup, no events (FIXED 2026-05-15)          |
| Heartbeat-only prefixes (zombie-watchdog, no event trail) | 56    | ℹ️ expected                                          |

---

## Architecture

All non-backtest VM tasks route through a single startup script:  
`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`

The event emission chain:

```
[VM startup-script]
  └─ setup-data-pipeline-vm.sh
       ├─ starts vm_heartbeat_sidecar.sh (GCS blob, zombie-watchdog detection)
       ├─ downloads vm-exec-with-gcs-tee.sh + deployment_heartbeat.py + heartbeat_daemon.py
       └─ _launch_with_tee("cmd") → nohup vm-exec-with-gcs-tee.sh → heartbeat_daemon.py
            ├─ DEPLOYMENT_STARTED  (emitted at daemon start, via HeartbeatDaemon)
            ├─ DEPLOYMENT_PROGRESS (emitted every 60s heartbeat)
            └─ DEPLOYMENT_COMPLETED / DEPLOYMENT_FAILED  (emitted on cmd exit)
```

Python binding: `deployment_service/vm/heartbeat_cli.py` wraps UTL `HeartbeatDaemon`  
with `setup_events()` + `run_lifecycle()` (STEP 5.63 compliant).

---

## Audit Gap Found (2026-05-15)

**File**: `setup-data-pipeline-vm.sh`, lines 469-495 (original)  
**Trigger**: `VM_PIPELINE_MODE=backtest` (set by `launch-strategy-test-vm.sh`)

**Root cause**: The `backtest` branch used bare `nohup bash` and then `exit 0` **before** the heartbeat sidecar and tee
wrapper were downloaded (those were at lines 497-570, after the `exit 0`). As a result:

- GCS-blob heartbeat sidecar never started → zombie-watchdog could not detect hung backtests
- `vm-exec-with-gcs-tee.sh` wrapper never downloaded → no `DEPLOYMENT_STARTED` / `DEPLOYMENT_COMPLETED` /
  `DEPLOYMENT_FAILED` events emitted
- Backtest VMs were effectively invisible to the deployment-events audit trail

**Affected launcher**: `launch-strategy-test-vm.sh` only (only launcher that sets `VM_PIPELINE_MODE=backtest`).

---

## Fix Applied (2026-05-15)

PR-equivalent: deployment-service `live-defi-rollout`, commit following item-5 work.

**Change**: Moved the observability setup block (VM_NAME_SELF + heartbeat sidecar + tee wrapper download +
`_launch_with_tee()` definition) to **before** the backtest branch check. Changed the backtest branch to call
`_launch_with_tee()` instead of raw `nohup bash`.

```bash
# BEFORE (broken)
if [[ "$VM_PIPELINE_MODE" == "backtest" ]]; then
  nohup bash "$BACKFILL_SCRIPT" $BACKFILL_ARGS > ... &
  exit 0   # ← exits before heartbeat setup at line 499+
fi
# ... heartbeat sidecar + tee + _launch_with_tee() defined here (never reached for backtest)

# AFTER (fixed)
# ── 5a. VM identity + observability setup (all task modes, including backtest) ──
VM_NAME_SELF=$(curl ...)
# ... heartbeat sidecar start ...
# ... tee wrapper download ...
_launch_with_tee() { ... }

if [[ "$VM_PIPELINE_MODE" == "backtest" ]]; then
  _launch_with_tee "bash $BACKFILL_SCRIPT $BACKFILL_ARGS" "$LOGS/backtest-pipeline.log"
  exit 0  # skip generic VM_TASK routing — backtest handled above via _launch_with_tee
fi
```

**Result**: Backtest VMs now get:

- GCS-blob heartbeat sidecar (zombie-watchdog detection)
- `DEPLOYMENT_STARTED` at daemon start
- `DEPLOYMENT_COMPLETED` or `DEPLOYMENT_FAILED` on exit
- GCS log streaming every 30s

---

## Coverage of All VM_TASK Routing Branches

Every `elif [[ "$VM_TASK" == "..." ]]; then` branch at lines 572+ calls `_launch_with_tee()`. The catch-all at line 807
(`elif [ -n "$VM_TASK" ]; then`) also calls `_launch_with_tee()`. The `else` at line 832 (`No VM_TASK metadata`) is a
no-op (manual launch scenario).

All paths are covered.

---

## Test Coverage

Unit tests: `tests/unit/test_vm_event_emission.py`

- Verifies `heartbeat_cli.main()` invokes `setup_events()` (event sink init)
- Verifies `HeartbeatDaemon` is constructed with `DEPLOYMENT_STARTED` / `DEPLOYMENT_COMPLETED` / `DEPLOYMENT_FAILED`
  constants
- Verifies `run_lifecycle()` context manager is entered (STEP 5.63 compliance)
- Verifies `_vm_payload()` includes all required fields

---

## References

- `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (fixed)
- `deployment-service/deployment_service/vm/heartbeat_cli.py` (event emission Python binding)
- `codex/05-infrastructure/launcher-script-ssot.md` (trigger chain SSOT)
- `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md`
