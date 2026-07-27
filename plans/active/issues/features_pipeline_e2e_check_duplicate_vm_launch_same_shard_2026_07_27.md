---
doc_type: issue
title:
  "features-service pipeline_e2e_check.py launched a SECOND force-leg VM for the same TRADFI:volatility shard while the
  first was still alive and working — concurrent writes to the same sink"
summary:
  "Running --family volatility (no --asset-group filter, covers CEFI+TRADFI), the driver launched
  features-e2e-tradfi-20260727-104900-b1a99f for the TRADFI:volatility force-leg, then at 11:29:01 (~40min later, while
  the FIRST VM was still confirmed RUNNING and actively producing fresh log output) launched a SECOND VM
  (features-e2e-tradfi-20260727-112901-b1a99f) for the same shard/window/sink bucket. Both VMs were independently
  confirmed RUNNING simultaneously, each running its own features_service compute process against the identical TRADFI
  2026-01-29..2026-01-30 volatility window, both writing to features-tradfi-test-central-element-323112."
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, duplicate-vm-launch, vm-spend, launcher-timeout, concurrency]
related: [data_pipeline_check_mdps_features_2026_07_20]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source:
  "todo 9b full-matrix run (/data-pipeline-check-features), slot-3, 2026-07-27 — caught while monitoring an apparent
  CEFI freeze and cross-checking the volatility task's own driver log"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# Duplicate concurrent VM launch for the same shard (2026-07-27)

## What happened

Driver log (task b04i8g53p) shows:

```
10:49:00 launching --vm-name features-e2e-tradfi-20260727-104900-b1a99f ...
10:49:21 launcher exited 0 for vm=features-e2e-tradfi-20260727-104900-b1a99f — polling for EXIT_STATUS
11:29:01 launching --vm-name features-e2e-tradfi-20260727-112901-b1a99f ...   <- SAME shard, same window, same sink
11:29:22 launcher exited 0 for vm=features-e2e-tradfi-20260727-112901-b1a99f — polling for EXIT_STATUS
```

Both VM names independently confirmed `RUNNING` at 11:40 UTC via `gcloud compute instances describe`, both with active,
advancing run.log content (the first VM was still iterating instruments — SOYMEAL/SOYOIL at 11:39-11:40 — well after the
second VM's own bootstrap logs at 11:31). The second VM's log shows a completely independent `deployment_id`
(`1a8b357a-...` vs the first's presumed different id) and its own fresh `ServiceRuntime: op=__bootstrap__` /
`Dependencies verified for 2026-01-29/TRADFI` / `Processing 4 volatility feature groups` sequence — a genuine second
compute run, not a log-tail artifact.

## Root cause — CONFIRMED

The same driver invocation eventually finished (~80min total) and its own report answers this directly:

```
| TRADFI:volatility | force | failed | not_applicable | - | 0 | - | vm_not_success:timeout_no_exit_status |
| TRADFI:volatility | skip  | failed | not_applicable | - | 0 | - | vm_not_success (exit=None)             |
```

**Confirmed: option 1 above.** The driver's own poll/wait logic timed out waiting for VM #1
(`features-e2e-tradfi-20260727-104900-b1a99f`)'s `EXIT_STATUS` and recorded the shard as `failed` —
`timeout_no_exit_status` / `exit=None`, never a real nonzero exit — while the VM was independently confirmed still
`RUNNING` and actively producing fresh log output well past that point (SOYMEAL/SOYOIL entries at 11:39-11:40, long
after the timeout). The driver then launched VM #2 for the same shard, presumably as its own retry-on-failure path,
without checking whether VM #1 was still genuinely alive. This is exactly the same class of bug already fixed for the
MDPS check in `unified-trading-library@137e219c` (`_LAUNCHER_SCRIPT_TIMEOUT_SEC` treating a slow-but-alive VM as a hard
failure with zero retry-with-liveness-check) — features-service's `pipeline_e2e_check.py` needs the same fix (or to
reuse the shared UTL fix if it isn't already).

Both orphaned VMs (#1 and #2) were left running independently past the driver's own completion; this issue doc's
existing todo below to spot-check their eventual output for corruption stands.

## Why it's probably not data-corrupting (but not verified)

Both VMs compute the identical deterministic transform (same window, same feature groups, same input) — if the compute
path is genuinely deterministic, concurrent writes to the same GCS object path should converge to byte-identical content
regardless of write order, making this a **wasted-spend** issue rather than a correctness issue. This is an assumption,
not verified — the todo 9b report for this shard should be treated with a LOWER confidence flag (re-verify the written
parquet/manifest look sane, not just "some VM exited 0") until this is confirmed.

## Todos

- [ ] [SCRIPT] P2. Find and fix the root cause of the duplicate launch in
      `features-service/scripts/pipeline_e2e_check.py` (or wherever its VM-wait logic lives) — likely the same class of
      premature-timeout-treated-as-failure bug already fixed for MDPS in `unified-trading-library@137e219c`. Add a
      concurrency guard (check for an already-running VM for the same shard before launching another) if the shared UTL
      launcher doesn't already provide one for this driver.
- [ ] [DATA] P3. Once both VMs for this incident complete, spot-check the written TRADFI:volatility parquet/manifest for
      the 2026-01-29..2026-01-30 window to confirm no partial-write corruption from the concurrent writes (the
      determinism assumption above is unverified).

## Progress Log

- 2026-07-27 (slot-7): **Independently corroborated — same shard, same failure signature, different run.** The
  day=2026-07-05 full-matrix run hit the byte-identical pattern for the SAME `TRADFI:volatility` shard (force-leg VM
  timed out at exactly 2400s with no EXIT_STATUS while genuinely still computing, driver launched a second VM for the
  same shard without checking the first's liveness) AND separately for `CEFI:delta_one` (confirming this is not
  TRADFI:volatility-specific — any large-enough real instrument universe triggers it). Also directly confirmed via
  `gcloud` that the abandoned VMs remain RUNNING with no code ever checking their eventual result after the driver moves
  on — an orphaned-compute angle this doc's own findings didn't explicitly call out. Full writeup + the CEFI:delta_one
  occurrence + a negative control (TRADFI:delta_one, a smaller/faster-covered window, completed both legs cleanly in
  ~3.5min, proving this is universe-size-dependent):
  `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`. Recommend tracking the actual fix
  in ONE of these two docs going forward (this one has the deeper root-cause trace to `utl@137e219c`'s sibling fix; the
  other has the broader multi-shard evidence) rather than splitting effort — not merged outright here to avoid
  clobbering either author's in-progress doc.
