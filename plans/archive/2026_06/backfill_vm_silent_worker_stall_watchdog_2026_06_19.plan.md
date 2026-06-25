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
- [x] ✅ [INFRA] P1. **Wire `STALL_PROGRESS_REGEX` per backfill launcher — gas-fees + SFI DONE (verified markers).**
      `setup-data-pipeline-vm.sh` now forwards `STALL_PROGRESS_REGEX` from metadata (mirroring `STALL_TIMEOUT_SEC`) to
      `vm-exec-with-gcs-tee.sh`. Wired with markers VERIFIED against each launcher's live `run.log` (=/space/comma-free
      → metadata-safe; loose-but-progress-correlated → errs toward not-killing, never false-kills): **gas-fees** =
      `sampled|Wrote` (each per-block sample — the 2026-06-19 freeze was MID block-sampling — + per-date parquet write);
      **SFI** = `league` (every per-date "league mapping cache hit for date=…" line). — deployment-service@a8ee104e.
- [x] ✅ [INFRA] P2. **Wire `STALL_PROGRESS_REGEX` for the sports-MDPS launcher (`launch-mdps-sharded-backfill.sh`, the
      `STALL_TIMEOUT_SEC=7200` 2h-threshold case — the worst blunt-threshold offender).** **DONE** —
      deployment-service@3f43c35. Marker = `Processing|Skipping` (=/space/comma-free → metadata-safe; category-agnostic
      shared-orchestration markers — `process_handler.py:517/540/582` emit exactly one of "Processing candles for
      <date>" / "Skipping <date> …" for EVERY date the per-date loop touches, so it resets on every healthy advance and
      only fails to reset on a genuine mid-date hang → errs toward NOT killing). **Verified against a REAL
      mdps-sports-2024 run** (the deferral's exact bar): marker advanced across 5 distinct dates, VM RUNNING ~17min,
      never tripped (cadence ~3min ≪ 7200s); the VM watchdog heartbeat read `mode=progress` (end-to-end: launcher
      metadata → `setup-data-pipeline-vm.sh` forward → `vm-exec` progress branch). Verification VM deleted. Scoped to
      **sports only** (the sole `STALL_TIMEOUT_SEC=7200` case); cefi/defi/tradfi MDPS stay on the default 1800s
      size-based watchdog (no blunt-threshold raise → no progress-marker needed). Repo: `deployment-service`.
      Provenance: 2026-06-21 P1 wiring.
- [x] ✅ [INFRA] P3. **Audit other sports/data adapters for unbounded `aiohttp.ClientSession` timeouts.** **DONE** —
      **instruments-service**: bounded `BaseReferenceDataAdapter._make_session` (the generic base for all
      defi/prediction adapters — the `729fbdb` SFI fix had only covered the SPORTS base) +
      `evm_creation_resolver._make_session` + `block_resolver._make_session` default (instruments-service@06ee145e).
      **mtds**: bounded session-level `ClientTimeout` on 37 bare REST `ClientSession` sites across
      defi/handler/adapter/script fetch paths (market-tick-data-service@7ff6c051). **Scoped out (deliberately):** the
      ~20 `live/connectors/*_ws.py` WebSocket connectors (a bounded `total`/`sock_read` would kill a quiet live stream —
      streaming needs `total=None`, per the tardis precedent), and 4 already-AT-900-line files (`gas_fee_handler` /
      `lending_indices_handler` / `polymarket_adapter` / `umi_tick_provider`) whose actual incident path (POLYGON web3
      HTTPProvider) is already bounded — see the follow-up below. Provenance: 2026-06-19.
- [x] ✅ [INFRA] P3. **Bound the 4 at-900-line mtds REST sites deferred from the P3 sweep**
      (`cli/handlers/gas_fee_handler.py`, `cli/handlers/lending_indices_handler.py`,
      `market_interface/adapters/prediction/polymarket_adapter.py`, `adapters/umi_tick_provider.py`). **DONE** —
      market-tick-data-service@64789a7f. Split each under the 900-line cap via cohesive sibling extractions
      (gas_fee 864 + `_gas_fee_helpers.py` (pure row-builders); lending 851 + `_lending_subgraph.py` (subgraph
      schema/query group); polymarket 716 + `_polymarket_helpers.py` (taxonomy/lifecycle helpers); umi 738 +
      `_umi_yahoo.py` (Yahoo fetchers)), THEN added a per-file
      `_BACKFILL_HTTP_TIMEOUT = aiohttp.ClientTimeout(sock_connect=15, sock_read=60, total=120)` to each
      `_make_session` (matching the 37-site `dex_pools_handler.py` house pattern; module-level constant → no method
      grew past the 50-line cap). QG-green (5217 tests pass, basedpyright/ruff clean). Two split-induced QG issues
      fixed in the same unit: repointed 19 umi `YahooFinanceAdapter` test-patches `umi_tick_provider`→`_umi_yahoo`
      (the moved functions look it up there), and added the 3 new siblings to the repo `_HANDLERS` codex-exclude list
      (consistent with every existing handler sibling — empty-str JSON parsing / deferred imports are sanctioned
      adapter patterns). Repo: `market-tick-data-service`. Provenance: 2026-06-22 mtds P3 sweep.

## Status of the immediate operational fix (DONE 2026-06-19)

- SFI `ClientTimeout` fix shipped: `instruments-service@729fbdb` (LDR; dirty-deps carve-out — UTL/UAC were mid-edit by a
  live session so quickmerge was refused; promotes LDR→staging→main via the standard drain).
- Fixed `instruments-service-code.tar.gz` rebuilt from a clean LDR clone + uploaded to
  `gs://deployment-scripts-central-element-323112/code/`.
- Stalled VMs deleted; re-launched 4 SFI chunks (`--chunks 4 2020-01-01 2026-04-21`, run-id `20260619-195318`) +
  gas-fees (`2021-01-01..2026-06-19`, `mtds-gas-fees-20260619-195416`), all monitored with active short-tick polling of
  the climbing date + uploader-flush metric.
