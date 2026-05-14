---
title: strategy-paper VM crashes on ModuleNotFoundError nautilus_trader
created: 2026-05-14
author: slot-9
source:
  - promote_workflow_may23_cli_path_2026_05_10.md Phase 1 RE-RUN
  - e2e-testing/scripts/defi/colocated_engine.py:950
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

During the strategy-paper smoke VM re-run (2026-05-14 slot-9), VM
`strategy-paper-carry-staked-basis-20260514-121752` emitted STARTED then FAILED within 5 seconds:

```
FAILED: "No module named 'nautilus_trader'"
```

Trace: `colocated_engine.py:950` (inside `run_engine()`) has a lazy import:
```python
from execution_service.providers.tenderly import TenderlyExecutionProvider
```
`execution-service` itself depends on `nautilus_trader`. The VM startup script
`setup-data-pipeline-vm.sh` only installs `uac + utl + e2e-testing` via
`uv pip install --no-sources`. `execution-service` is NOT in the install list, so
`nautilus_trader` is never present on the VM.

This is a pre-existing gap unrelated to the wire-ins that were being verified (afd0c16 + ab6bfd2).
The GcsEventSink / STARTED / FAILED / VM self-delete wire-ins all worked correctly.

## Why it matters

- Severity: **P1** — the paper/live strategy VM cannot run even a single tick. Every colocated-engine
  VM launch will crash immediately on the tenderly import.
- The promote_workflow Phase 1 done-def requires the engine to run at least 10 minutes of progress
  events. That cannot pass until this is resolved.
- Two options for resolution (operator triage required):

  **Option A — Add execution-service to VM pip install**
  In `setup-data-pipeline-vm.sh`, add `execution-service` to the `uv pip install --no-sources` list.
  Risk: execution-service pulls `nautilus_trader` which is large (~300 MB) and may increase VM
  cold-start time significantly.

  **Option B — Move the tenderly import to connection-time (lazy per call, not per module)**
  `colocated_engine.py:950`: hoist the `from execution_service...` import inside the function body
  so it only runs when `provider=tenderly` is actually used. This avoids adding execution-service
  to every VM regardless of provider.

  **Option C — Use a mock/stub provider for paper mode**
  Paper trading doesn't execute real orders; `TenderlyExecutionProvider` is used for simulation.
  Could wire a lighter stub that doesn't require nautilus_trader for paper runs.

## Recommended decision

Operator triage: pick A, B, or C. This issue blocks promote_workflow Phase 1 full-execution criterion
(10min progress events) but does NOT block the May-23 cutover gate if Phase 2 (live strategy VM) is
the actual gate. The paper VM is a smoke harness, not the live gate.

Suggested owner: harsh-slot-9 or any defi slot in next wave (30-60 min fix for Option B).
