---
doc_type: issue
title: >-
  CeFi HL/ASTER/onchain-perp backfill VM over-provisioned — e2-highmem-8 -> e2-highmem-4; 2 more findings tracked
summary: >-
  Follow-on to the TradFi utilization audit (`tradfi_vm_resource_utilization_downsize_2026_08_10.md`), same operator ask
  extended to CeFi given remaining backfill work. Found 4 distinct CeFi backfill launchers with different sizing
  profiles. The primary Tardis launcher (heavy `e2-highmem-16`/light `e2-highmem-8`) has a well-documented OOM history
  (5+ dated bumps, measured 60-66GB real peaks) and is capped at 1 concurrent VM fleet-wide — NOT touched, correctly
  sized and low fleet-wide $ impact regardless. `launch-cefi-hl-aster-historical-backfill.sh` (`e2-highmem-8`,
  hardcoded, no documented sizing rationale) is a real finding: 15 samples across HYPERLIQUID/ASTER/LIGHTER-ZKSYNC,
  including a full 12-day real HYPERLIQUID run, never exceeded 14.6% memory (9.3GB of 64GB) or 21% CPU. Downsized to
  `e2-highmem-4` (32GB, still >3x headroom). This launcher fans out many concurrent VMs on an ongoing campaign (real
  fleet-wide $ leverage, unlike the single-VM Tardis case), and its `MAX_CONCURRENT` fan-out throttle is a VM-count
  knob, not derived from machine size — no concurrency pin needed (unlike the TradFi date-fanout case). Two more
  findings tracked below, not acted on this session: a doc/code sizing mismatch in `launch-tier3-cefi-backfill.sh`, and
  a reliability problem (not a sizing one) in `cefi-fwd-*` forward-poll VMs.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [cefi, cost-optimization, vm-sizing, gcp, resource-utilization, backfill]
related:
  - /plans/active/issues/tradfi_vm_resource_utilization_downsize_2026_08_10.md
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
  - /codex/05-infrastructure/deployment-observability.md
  - /codex/05-infrastructure/vm-launcher-runbook.md
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-10: "and then for cefi can we do the same analysis audit because we still have a
  bunch of cefi data to backfill" — follow-on to the TradFi resource audit in the same session.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
---

# CeFi backfill VM resource audit

## Launchers found and verdict

| Launcher                                                | Machine (before)                                            | CPU / Memory measured                                                             | Verdict                                                                                                                   |
| ------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `launch-cefi-sharded-backfill.sh` (Tardis, heavy/light) | e2-highmem-16 / e2-highmem-8                                | up to 23%/41.6% (≈53GB)                                                           | **Not touched** — documented OOM history, 128GB genuinely needs 16vCPU under e2's 8GB/vCPU ratio cap, single-VM-at-a-time |
| `launch-cefi-hl-aster-historical-backfill.sh`           | e2-highmem-8 (hardcoded)                                    | max 21% CPU / 14.6% mem (9.3GB of 64GB) across 15 samples incl. a 12-day real run | **Downsized → e2-highmem-4** (this doc)                                                                                   |
| `launch-tier3-cefi-backfill.sh`                         | code default e2-highmem-8, header comment says e2-highmem-2 | no live data                                                                      | **Not sized — tracked below**                                                                                             |
| `launch-cefi-extended-starknet-funding-timestamp-vm.sh` | e2-standard-4                                               | 6-12%/8-14% CPU, ~1GB mem                                                         | one-off migration script, bounded/low-priority, not touched                                                               |
| `cefi-fwd-*` forward-poll                               | e2-standard-8                                               | up to 75% mem, 2/3 sampled runs FAILED                                            | **Reliability issue, not sizing — tracked below**                                                                         |

## What changed

`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`: `machine="e2-highmem-8"` → `"e2-highmem-4"`
(see code comment for the full rationale citation).

## Todo

- [ ] [DATA] P3. **Re-measure `launch-cefi-hl-aster-historical-backfill.sh` VMs after this downsize ships** — the sample
      this ruling was based on is thin (3 VMs, only 1 long real run). Confirm a fresh sample of completed runs stays
      comfortably under `e2-highmem-4`'s 32GB (target: revert to `e2-highmem-8` if any run's memory climbs past
      ~50%/16GB). **Done when**: at least 3 fresh completed runs post-downsize are checked and either confirm headroom
      or trigger a revert. Repo: deployment-service.
- [x] ✅ [SCRIPT] P3. **`launch-tier3-cefi-backfill.sh` doc/code machine-type mismatch** — the script's own header
      comment documents an intended default of `e2-highmem-2`, but the code actually ships `e2-highmem-8`. No live VM
      was found in the last-2-day sample to determine which is actually correct via measurement. **Done**:
      `deployment-service@170c73d794` (slot 15, 2026-08-10) — option (b): reconciled header comment to match code
      default (`e2-highmem-8`/64GB). Code default is authoritative (it's what actually runs). Added TODO to re-measure
      when a VM next runs (`e2-highmem-4` may be sufficient per sibling hl-aster audit).
- [ ] [DATA] P2. **`cefi-fwd-*` forward-poll VMs (`e2-standard-8`) — 2 of 3 sampled runs FAILED, memory reached up to
      75% (24GB of 32GB).** This is a reliability finding, not a sizing one — do NOT downsize this launcher; if anything
      the failures + high memory suggest it may need MORE headroom, not less. **Done when**: root-cause the 2 failed
      runs (check their `run.log`s for the actual failure mode — OOM-kill vs. something else) and either fix the
      underlying issue or file a properly-scoped separate issue doc for it. Repo: deployment-service.

## Progress Log

- 2026-08-10: doc created, `launch-cefi-hl-aster-historical-backfill.sh` downsize shipped same session (see commit
  citation on the code comment once pushed). Other 2 findings tracked as todos above, not investigated further this
  session — genuinely need either fresh live data (tier3) or a root-cause dive (cefi-fwd) neither of which was in scope
  for a same-session same-pass fix.
