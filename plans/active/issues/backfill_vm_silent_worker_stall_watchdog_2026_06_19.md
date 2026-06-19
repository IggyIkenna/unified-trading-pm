---
title: "Backfill VMs silently stall — dead worker masked by independent heartbeat sidecar; missing per-shard wall-clock watchdog + bounded HTTP/RPC timeouts"
created: 2026-06-19
parent_epic: infrastructure_master
source:
  - "vm-logs/sfi-backfill-chunk-2of4-20260619-161036/run.log (froze 3h25m after 1 date)"
  - "vm-logs/mtds-gas-fees-20260619-151404/run.log (froze ~1h48m mid-POLYGON sampling)"
  - "instruments-service@729fbdb (SFI ClientTimeout fix)"
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

Two batch-backfill VMs **silently stalled** on 2026-06-19 — the application worker thread hung on a
network call while the **separate heartbeat sidecar process kept the VM "RUNNING"**, so the stall was
invisible until an operator noticed the in-log date had stopped advancing.

1. **`sfi-backfill-chunk-2of4-20260619-161036`** — processed **exactly ONE date** (2021-08-14 → `{}`),
   then froze 3h25m on the 2nd date's `/matches/day/basic/` fetch. **No error, no OOM, no progress.**
   Root cause: `BaseSportsReferenceAdapter._make_session()` built `aiohttp.ClientSession(connector=...)`
   with **NO `timeout=`** → aiohttp default `ClientTimeout(total=300)` with **unbounded
   `sock_connect`/`sock_read`** → a half-open / stalled provider socket blocks the single worker forever.
   **NOT a credential problem** — the rotated SFI key v2 worked (`Fetched 50 leagues`). **NOT a scope bug** —
   `filtered 50 → 4 mapped prediction leagues` is the intended prediction-tier filter; the `{}` for
   2021-08-14 is legitimate (no completed matches in the 4 mapped leagues that day = honest empty).
   **FIXED**: `instruments-service@729fbdb` adds bounded `sock_connect=15s / sock_read=60s / total=120s`
   → a stalled socket now raises `aiohttp.ServerTimeoutError` (a `ClientError` subclass) which
   `_get_with_retry` already retries + escalates to `record_failed` → the per-date loop continues.

2. **`mtds-gas-fees-20260619-151404`** — was genuinely **progressing** (wrote ETHEREUM/BSC parquets,
   advanced 2021-01-22 → 2021-01-26) but **crawled** (~5 days in 2.5h) then froze ~1h48m mid-POLYGON
   block-sampling (last line `...sampled 200 pts for POLYGON`). The Web3 HTTPProvider already carries a
   30s request timeout + `_rpc_call` retries (bounded ~12 min), so the freeze is most likely a degraded
   POLYGON RPC stacking 30s-timeout+retry across ~410 per-sample `get_block` calls. The throughput is the
   bigger issue: ~5 days/2.5h × 1900 days × 12-14 chains on a SINGLE VM is multi-week.

## Why it matters

The data pipeline is the heartbeat (HARD RULE). A dead-but-"RUNNING" backfill VM burns hours of wall-clock
with zero progress and zero alert. The heartbeat sidecar proves *the box is up*, not *the work is moving* —
a per-shard **progress** watchdog is missing fleet-wide for these tarball-launched batch VMs.

## Recommended decision (todos)

- [ ] [INFRA] P1. **Per-shard wall-clock progress watchdog for tarball-batch VMs** (deployment-service VM
  startup / heartbeat_daemon.py). Track last-shard-completion timestamp; if a single shard exceeds N×
  (median shard duration) or no shard completes in M minutes → emit `WORKER_STALLED` + (configurable)
  self-terminate so AutoSpawn/relaunch can recover. Closes the "heartbeat-up but worker-dead" blind spot
  for sfi/gas-fees/sports/all batch backfills. Repo: `deployment-service`. Provenance: 2026-06-19 SFI +
  gas-fees silent stalls.
- [ ] [INFRA] P2. **Gas-fees backfill chunk-parallelism** for the full 2021→2026 range — single-VM
  throughput (~5 days/2.5h) is multi-week. Add a `--chunks N` fan-out to
  `launch-mtds-gas-fees-backfill-vm.sh` mirroring `launch-sfi-backfill-vm.sh` (disjoint date windows,
  per-VM shards, singleton-lock treats one run-id as one job). Repo: `deployment-service`. Provenance:
  2026-06-19 gas-fees crawl rate.
- [ ] [INFRA] P3. **Audit other sports/data adapters for unbounded `aiohttp.ClientSession` timeouts** —
  the SFI fix was in the shared `BaseSportsReferenceAdapter._make_session` (covers all sports-reference
  adapters), but verify no other adapter creates a bare `ClientSession()` without a bounded
  `ClientTimeout`. Repo: `instruments-service` + `market-tick-data-service`. Provenance: 2026-06-19.

## Status of the immediate operational fix (DONE 2026-06-19)

- SFI `ClientTimeout` fix shipped: `instruments-service@729fbdb` (LDR; dirty-deps carve-out — UTL/UAC were
  mid-edit by a live session so quickmerge was refused; promotes LDR→staging→main via the standard drain).
- Fixed `instruments-service-code.tar.gz` rebuilt from a clean LDR clone + uploaded to
  `gs://deployment-scripts-central-element-323112/code/`.
- Stalled VMs deleted; re-launched 4 SFI chunks (`--chunks 4 2020-01-01 2026-04-21`,
  run-id `20260619-195318`) + gas-fees (`2021-01-01..2026-06-19`, `mtds-gas-fees-20260619-195416`),
  all monitored with active short-tick polling of the climbing date + uploader-flush metric.
