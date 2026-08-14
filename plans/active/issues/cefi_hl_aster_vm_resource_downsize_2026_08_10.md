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
context_scope:
  - deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh
  - deployment-service/scripts/vm/launch-cefi-forward-poll.sh
  - /codex/05-infrastructure/deployment-observability.md
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
- [x] ✅ [DATA] P2. **`cefi-fwd-*` forward-poll VMs (`e2-standard-8`) — 2 of 3 sampled runs FAILED, memory reached up to
      75% (24GB of 32GB).** Root cause confirmed: `cefi-fwd-20260806-065837` exit_code=137 (SIGKILL/OOM), RSS climbed
      7→29.3GB (96.4% of 32GB) in ~10min processing a 74-day range with `--force`. Second failure
      (`cefi-fwd-20260808-115442`): truncated log, no completion marker — likely same OOM pattern. Third
      (`cefi-fwd-20260808-122833`): 0-byte log, VM deleted — startup/immediate kill. **Fix**: upsized `e2-standard-8` →
      `e2-highmem-8` (8 vCPU, 64GB, same vCPU count, 2× memory) in `launch-cefi-forward-poll.sh` —
      `deployment-service@1717d294`. The `ParallelPerSymbolRunner` memory-pressure pause (UTL, 75% threshold, 30s
      window) gates only NEW symbol tasks — in-flight large-symbol downloads continue consuming memory past the OOM
      point of no return. 64GB gives ≥2× worst-case headroom. Also tracked a follow-up below to make the memory-pressure
      mechanism more effective (UTL code change is a separate scope from this launcher change).
- [ ] [DATA] P3. **Improve `ParallelPerSymbolRunner` memory-pressure mechanism** — the current 75% threshold + 30s pause
      only gates NEW symbol tasks. In-flight tasks past the `_await_resume()` checkpoint continue consuming memory, and
      by the time the second warning fires at ~96% RAM the kernel OOM killer has already decided. Options: (a) lower the
      warning threshold from 75% to 60%, (b) require memory to actually DROP below threshold before resuming (not just a
      time-based pause), (c) add a global semaphore that blocks ALL task acquisition (including semaphore waiters) when
      memory is above threshold. Repo: unified-trading-library (`parallel_per_symbol_runner.py` +
      `resource_profiler.py`). This follow-up is tracked here because it was discovered during the cefi-fwd root-cause
      analysis but the UTL code change is a separate scope from the launcher machine-type fix.

## Progress Log

- 2026-08-10: doc created, `launch-cefi-hl-aster-historical-backfill.sh` downsize shipped same session (see commit
  citation on the code comment once pushed). Other 2 findings tracked as todos above, not investigated further this
  session — genuinely need either fresh live data (tier3) or a root-cause dive (cefi-fwd) neither of which was in scope
  for a same-session same-pass fix.
- 2026-08-10 (slot 23): cefi-fwd root-cause complete. Confirmed OOM-kill (exit_code=137) on `cefi-fwd-20260806-065837` —
  RSS climbed 7→29.3GB (96.4% of 32GB) in ~10min processing a 74-day range with `--force`. The `ParallelPerSymbolRunner`
  memory-pressure pause (75%/30s) gates only NEW tasks; in-flight downloads continue past OOM threshold. Fixed by
  upsizing `e2-standard-8` → `e2-highmem-8` (64GB) in `launch-cefi-forward-poll.sh` (`deployment-service@1717d294`).
  Also identified a secondary gap in the UTL memory-pressure mechanism — tracked as a new P3 follow-up above.
- **data_engineering (slot 16) 2026-08-11T12:10Z**: Re-measurement attempted for the hl-aster todo. Downsize shipped
  `deployment-service@9db194e6` (2026-08-10 13:42Z). Queried
  `central-element-323112.deployment_operational_data.run_ledger` (BigQuery) for every
  `cefi-hyperliquid-*`/`cefi-aster-*`/`cefi-lighter-zksync-*`/`cefi-extended-starknet-*` row — **zero completions since
  2026-08-09 21:24Z** (the last pre-downsize batch, an `extended-starknet` sweep). Cross-checked live GCE state
  (`gcloud compute instances list --filter="name~'^cefi-(hyperliquid|aster|lighter-zksync|extended-starknet)-'"`) —
  **zero running instances**, confirming this isn't an in-flight-but-uncompleted gap. Confirmed
  `launch-cefi-hl-aster-historical-backfill.sh` has no cron/scheduler wiring anywhere in the repo (`grep` for its name
  outside itself only hits the unrelated Tardis launcher + its concurrency guard) — this launcher is invoked on-demand
  (by an operator or another agent's campaign work), not on a fixed cadence, so there is no ETA mechanism to key off.
  **Todo remains gated**: the launcher genuinely has not been re-invoked since the downsize shipped — nothing to
  re-measure yet, not a data-access or methodology gap. Releasing back to queue with `reason_code: GATED` per worker.md
  § 4c; next check should occur whenever this campaign is next dispatched (no fixed interval known).
- **data_engineering (slot 14) 2026-08-11T~19:00Z**: Re-checked. `run_ledger` query (partition-filtered
  `completed_at >= 2026-08-01`) for `cefi-hyperliquid-*`/`cefi-aster-*`/`cefi-lighter-zksync-*`/
  `cefi-extended-starknet-*` still shows the last completion at `2026-08-09 21:24:53` (same pre-downsize
  `extended-starknet` batch slot 16 found) — zero new rows since. Live GCE filter for the same name prefixes returns
  zero running instances. State is unchanged from slot 16's check ~7h ago: the launcher has not been re-invoked since
  the downsize shipped (`deployment-service@9db194e6`, 2026-08-10 13:42Z), so there is still nothing to re-measure.
  Releasing back to queue with `reason_code: GATED` again — this todo needs the launcher's next real dispatch, not
  another poll.
- **infra (slot 22) 2026-08-11T18:36Z**: Re-checked, third identical result. `run_ledger` (partition-filtered
  `completed_at >= 2026-08-01`) top row for `cefi-hyperliquid-*`/`cefi-aster-*`/`cefi-lighter-zksync-*`/
  `cefi-extended-starknet-*` is still `cefi-extended-starknet-20260302-20260809-203922` completed `2026-08-09 21:24:53`
  — byte-identical to both prior checks, zero new rows. `gcloud compute instances list` for the same 4 prefixes returns
  zero running instances. Launcher confirmed still not re-invoked since the downsize shipped
  (`deployment-service@9db194e6`, 2026-08-10 13:42Z) — now ~29h with no dispatch. Releasing `GATED` with
  `estimated_unblock_minutes: 180` (the fleet cap) this time, since two prior GATED releases at default cooldown still
  produced two more no-op re-checks within ~24h on a launcher with no fixed cadence — a longer cooldown should cut
  redundant polling until the campaign actually re-dispatches this launcher.
- **context-scout 2026-08-14**: populated context_scope (3 entries).
