---
title:
  "Backfill VMs silently stall — dead worker masked by independent heartbeat sidecar; missing per-shard wall-clock
  watchdog + bounded HTTP/RPC timeouts"
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

Two batch-backfill VMs **silently stalled** on 2026-06-19 — the application worker thread hung on a network call while
the **separate heartbeat sidecar process kept the VM "RUNNING"**, so the stall was invisible until an operator noticed
the in-log date had stopped advancing.

1. **`sfi-backfill-chunk-2of4-20260619-161036`** — processed **exactly ONE date** (2021-08-14 → `{}`), then froze 3h25m
   on the 2nd date's `/matches/day/basic/` fetch. **No error, no OOM, no progress.** Root cause:
   `BaseSportsReferenceAdapter._make_session()` built `aiohttp.ClientSession(connector=...)` with **NO `timeout=`** →
   aiohttp default `ClientTimeout(total=300)` with **unbounded `sock_connect`/`sock_read`** → a half-open / stalled
   provider socket blocks the single worker forever. **NOT a credential problem** — the rotated SFI key v2 worked
   (`Fetched 50 leagues`). **NOT a scope bug** — `filtered 50 → 4 mapped prediction leagues` is the intended
   prediction-tier filter; the `{}` for 2021-08-14 is legitimate (no completed matches in the 4 mapped leagues that day
   = honest empty). **FIXED**: `instruments-service@729fbdb` adds bounded
   `sock_connect=15s / sock_read=60s / total=120s` → a stalled socket now raises `aiohttp.ServerTimeoutError` (a
   `ClientError` subclass) which `_get_with_retry` already retries + escalates to `record_failed` → the per-date loop
   continues.

2. **`mtds-gas-fees-20260619-151404`** — was genuinely **progressing** (wrote ETHEREUM/BSC parquets, advanced 2021-01-22
   → 2021-01-26) but **crawled** (~5 days in 2.5h) then froze ~1h48m mid-POLYGON block-sampling (last line
   `...sampled 200 pts for POLYGON`). The Web3 HTTPProvider already carries a 30s request timeout + `_rpc_call` retries
   (bounded ~12 min), so the freeze is most likely a degraded POLYGON RPC stacking 30s-timeout+retry across ~410
   per-sample `get_block` calls. The throughput is the bigger issue: ~5 days/2.5h × 1900 days × 12-14 chains on a SINGLE
   VM is multi-week.

## Why it matters

The data pipeline is the heartbeat (HARD RULE). A dead-but-"RUNNING" backfill VM burns hours of wall-clock with zero
progress and zero alert. The heartbeat sidecar proves _the box is up_, not _the work is moving_ — a per-shard
**progress** watchdog is missing fleet-wide for these tarball-launched batch VMs.

## Recommended decision (todos)

- [x] ✅ [INFRA] P1. **Per-shard wall-clock progress watchdog for tarball-batch VMs.** **DONE** — found the existing
      log-SIZE stall-watchdog in `scripts/vm/vm-exec-with-gcs-tee.sh` (SIGKILLs on `LOCAL_LOG` not-grown in
      `STALL_TIMEOUT_SEC`); its blind spot is that raw growth (heartbeats / empty-date "no events" noise) resets the
      timer, so a worker HUNG on a network call while the log emits noise isn't caught — and the blunt fix (raising
      `STALL_TIMEOUT_SEC` for empty-date asset_groups like sports) then lets a GENUINE hang idle for hours (SFI 3h25m /
      gas-fees 1h48m). Added an opt-in **progress-marker** mode (`STALL_PROGRESS_REGEX`): the timer resets ONLY on a NEW
      line matching the marker (a date advanced / a shard parquet written), scanned over just the bytes appended since
      the last reset (bounded — never re-greps a multi-GB log); raw noise no longer masks a hang, so the threshold stays
      TIGHT even for empty-date stretches (an empty date still advances → still resets). Emits a structured
      `WORKER_STALLED` log + breadcrumb reason (`reason=WORKER_STALLED mode=…`) the daemon turns into
      `DEPLOYMENT_FAILED`. Default (unset regex) = identical size-based behavior, fully backward compatible. —
      deployment-service@773b96e.
- [x] ✅ [INFRA] P2. **Gas-fees backfill chunk-parallelism.** **DONE** — added opt-in `--chunks N` to
      `launch-mtds-gas-fees-backfill-vm.sh`: a Python date-splitter divides the range into N DISJOINT contiguous
      windows + fires N sibling VMs (shared `run-id` label + `chunk=` label, per-VM manifest shards, sibling-aware
      singleton lock). Mirrors `launch-sfi-backfill-vm.sh`'s STRUCTURE but NOT its `--chunks` BAN (SFI's RapidAPI key
      has a hard 4-req/s per-account cap that N× definitely breaks; gas-fees' 2026-06-19 stall was LATENCY-bound — a
      degraded POLYGON RPC, no 429/CU errors — so a modest N=2–4 is a real speedup). Documented the **Alchemy shared-CU
      caveat** (the 8 Tier-1+2 chains share one key's CU budget → sub-linear on those; the 6 Tier-4 public-RPC chains
      parallelise freely; reduce N or provision a 2nd Alchemy key if 429/CU errors appear) so it's not blindly
      over-scaled. Dry-run verified (N=4 over 2021→2026 splits cleanly; single-stream default unchanged). —
      deployment-service@773b96e.
- [ ] [INFRA] P1. **Wire `STALL_PROGRESS_REGEX` per backfill launcher (P1 follow-up — needs real-log verification).**
      The P1 mechanism is live but OPT-IN; each launcher (`launch-sfi-backfill-vm.sh`,
      `launch-mtds-gas-fees-backfill-vm.sh`, sports MDPS launchers — especially those that RAISE `STALL_TIMEOUT_SEC` for
      empty-date gaps) should set a `STALL_PROGRESS_REGEX` in VM metadata matching that backfill's actual
      per-date/per-shard completion line (e.g. gas-fees `No gas fee data for .* on [0-9]{4}-|wrote [0-9]+ .*records`;
      verify against a live VM's `run.log` first — a wrong regex FALSE-KILLS a working VM, so this MUST be verified
      against real output, not guessed). Until wired, those VMs keep the (still-protective) size-based watchdog. Repo:
      `deployment-service`. Provenance: 2026-06-21 P1 mechanism ship.
- [ ] [INFRA] P3. **Audit other sports/data adapters for unbounded `aiohttp.ClientSession` timeouts** — the SFI fix was
      in the shared `BaseSportsReferenceAdapter._make_session` (covers all sports-reference adapters), but verify no
      other adapter creates a bare `ClientSession()` without a bounded `ClientTimeout`. Repo: `instruments-service` +
      `market-tick-data-service`. Provenance: 2026-06-19. **instruments-service half DONE** — bounded
      `BaseReferenceDataAdapter._make_session` (the generic base for all defi/prediction adapters) +
      `evm_creation_resolver._make_session` + `block_resolver._make_session` default (instruments-service@06ee145e).
      **mtds half IN PROGRESS** (sub-agent sweep of the ~27 bare `ClientSession(connector=…)` handler sites — flip when
      it lands).

## Status of the immediate operational fix (DONE 2026-06-19)

- SFI `ClientTimeout` fix shipped: `instruments-service@729fbdb` (LDR; dirty-deps carve-out — UTL/UAC were mid-edit by a
  live session so quickmerge was refused; promotes LDR→staging→main via the standard drain).
- Fixed `instruments-service-code.tar.gz` rebuilt from a clean LDR clone + uploaded to
  `gs://deployment-scripts-central-element-323112/code/`.
- Stalled VMs deleted; re-launched 4 SFI chunks (`--chunks 4 2020-01-01 2026-04-21`, run-id `20260619-195318`) +
  gas-fees (`2021-01-01..2026-06-19`, `mtds-gas-fees-20260619-195416`), all monitored with active short-tick polling of
  the climbing date + uploader-flush metric.
