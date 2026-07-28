---
doc_type: issue
title:
  "launch-mtds-backfill-vm.sh silently ignores --data-types scoping for HYPERLIQUID/ASTER; dedicated launcher missing
  from runbook"
summary:
  launch-mtds-backfill-vm.sh --venues HYPERLIQUID --data-types trades routes through --operation download, which for
  cefi on-chain-perp venues (HL/ASTER) does NOT honor the data-type filter — it fetches trades + book_snapshot_5 +
  derivative_ticker regardless. The correct, dedicated launcher (launch-cefi-hl-aster-historical-backfill.sh, using
  --operation collect-onchain-perp-batch --onchain-perp-data-types) does honor it and is purpose-sharded for this
  workload, but is absent from vm-launcher-runbook.md entirely — nothing routes an agent to it.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [vm-launcher, hyperliquid, aster, data-types, runbook-gap, efficiency]
related: [defi_satellite_ao_dispatch_batch1_2026_07_25]
created: 2026-07-28
assigned_vm: planning
parent_epic: infrastructure_master
priority: P2
source: defi_satellite_ao_dispatch_batch1_2026_07_25
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# launch-mtds-backfill-vm.sh silently ignores --data-types for HL/ASTER (2026-07-28)

## What I found

Working `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s HYPERLIQUID `trades` re-run todo, I launched
`launch-mtds-backfill-vm.sh --asset-group CEFI --venues HYPERLIQUID --data-types trades --force` (the launcher the
runbook's § 2 "MTDS Backfill VMs" points to for exactly this job class). VM metadata correctly carried
`VM_DATA_TYPES=trades`, but the run.log showed it fetching `book_snapshot_5` (154K L2 snapshots/coin) and
`derivative_ticker` (asset_ctxs/coin) for every instrument anyway — day 1 alone (2025-05-25) took ~6 minutes instead of
the ~25s a trades-only single-pass parse takes. Projected across the real 429-day range this would have run many hours
to over a day on one VM, when the actual job is a single day's node_fills parse × ~19-165 instruments.

Root cause (`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`, `VM_TASK=mtds-backfill` branch, ~line 1575): for
`VM_ASSET_GROUP != defi`, this branch builds `BASE_CLI="--operation download ..." --data-types ...`. HL/ASTER are
CeFi-classified venues but are on-chain-perp sources under the hood — the generic `--operation download` CLI path does
NOT thread `--data-types` down into `OnchainPerpBatchHandler`'s per-data-type filtering; it always processes the
handler's full declared data_type set for the venue.

The CORRECT, ALREADY-BUILT fix for this exact job exists: `launch-cefi-hl-aster-historical-backfill.sh` sets
`VM_TASK=cefi-hl-aster-backfill` → `--operation collect-onchain-perp-batch --onchain-perp-data-types <VM_DATA_TYPES>`,
which DOES honor per-data-type filtering (verified: my corrected relaunch scoped types=trades only, confirmed via a
clean dry-run showing `types=trades` per shard). This launcher is also purpose-built for exactly this venue class —
day-range sharding (`SHARD_DAYS`), per-venue start-date clamping, and its own header comment even documents this exact
scenario:
`VENUES=HYPERLIQUID DATA_TYPES=trades FORCE=true SYMBOLS=ALL YEARS="2025 2026" SHARD_DAYS=21 OVERRIDE_START_DATE=2025-05-25`
— literally my task's parameters, already written as the canonical example.

**But `vm-launcher-runbook.md` never mentions `launch-cefi-hl-aster-historical-backfill.sh` at all** (confirmed: zero
grep hits). An agent following the runbook's own "MTDS Backfill VMs" section for a HYPERLIQUID/ASTER-scoped,
data-type-filtered job has no way to discover the correct launcher exists — it silently reaches for the generic one,
which silently over-fetches. I caught this only because I directly inspected `run.log` and found unexpected
`book_snapshot_5`/`derivative_ticker` fetch lines; a less-scrutinized run would have just run for many extra hours at
real SPOT-VM cost with no error, no warning.

**Mitigation taken this session**: deleted the misscoped VM (`mtds-backfill-cefi-hyperliquid-trades-1`, ~7 min in, had
already captured real trades for 2025-05-25 — that data is redundantly-but-harmlessly recaptured by the correct
relaunch) and relaunched via `launch-cefi-hl-aster-historical-backfill.sh` with
`DATA_TYPES=trades SHARD_DAYS=21 OVERRIDE_START_DATE=2025-05-25 YEARS="2025 2026"` — 21 correctly-scoped shard VMs now
running.

## Why it matters

Silent over-fetch is a real-money SPOT-VM cost + wall-clock tax with zero error signal — the exact "no fire-and-forget,
efficiency is a co-equal craft north-star" failure mode this workspace explicitly guards against elsewhere (Tardis cap
incidents, tarball staleness). Any future HL/ASTER-scoped `--data-types`-filtered launch via the generic launcher will
silently hit the same trap.

## Recommended decision

- [ ] [DOC] P2. Add `launch-cefi-hl-aster-historical-backfill.sh` to `vm-launcher-runbook.md` § 2 "MTDS Backfill VMs" as
      its own entry (When/Required/Duration/Failures, mirroring the existing entries), and add a cross-reference note
      under `launch-mtds-backfill-vm.sh`'s entry: "for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET with
      `--data-types` scoping, use `launch-cefi-hl-aster-historical-backfill.sh` instead — the generic launcher's
      `--operation download` path does not honor per-data-type filtering for these venues (see this doc)." Repo:
      unified-trading-pm. Done when: both doc changes are present and the doc's own line-cap check passes.
- [ ] [BACKEND] P2. Harden `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s `VM_TASK=mtds-backfill` branch:
      when `VM_ASSET_GROUP` resolves to a CeFi on-chain-perp venue (HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/ EXTENDED-STARKNET
      — reuse whatever registry `OnchainPerpBatchHandler` already uses to recognize these) AND `VM_DATA_TYPES` is set,
      either (a) route to `--operation collect-onchain-perp-batch --onchain-perp-data-types` automatically instead of
      the generic `--operation download --data-types` path, or (b) fail loud at VM startup with a clear message pointing
      at the dedicated launcher, rather than silently accepting and ignoring the scoping flag. (a) is preferable (fixes
      the trap transparently) but needs verifying no other caller relies on the current `download` routing behavior for
      these venues. Repo: deployment-service. Done when: a `--data-types trades`-scoped
      `launch-mtds-backfill-vm.sh --venues HYPERLIQUID` launch either correctly fetches trades-only or refuses with an
      actionable error, verified via a `--test-run` smoke launch.
