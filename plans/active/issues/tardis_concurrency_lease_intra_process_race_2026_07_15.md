---
doc_type: issue
title:
  "TardisConcurrencyLease's process-wide singleton bypasses the lease-wait for concurrent intra-process symbol fetches —
  only the FIRST of up to 16 concurrent coroutines actually blocks on acquire(); the other 15 fire Tardis requests
  immediately, reproducing the code=274 concurrent-IP-lock 403 the lease exists to prevent"
summary:
  "infra (slot-6, 2026-07-15T20:2x-20:3xZ), while executing
  cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md todo (4) (relaunch the 3 cefi-queue-*
  Tardis VMs against the fixed mtds-code.tar.gz@5d44a197 tarball). Live-observed on the relaunched
  cefi-queue-light-binancefutu-x2-20260715-202013 VM: 1928+ (climbing) 'Tardis HTTP 403 code=274 concurrent-IP-lock'
  errors starting immediately after it moved past the free (day=1) date to date=2026-01-02, stalling on that single date
  for 9+ minutes. TARDIS_CONCURRENCY_LEASE=1 + TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-central-element-323112 were
  confirmed present in VM metadata, the actual process env (/proc/<pid>/environ via SSH), AND resolve correctly to
  tardis_concurrency_lease_enabled=True when replicated locally — so this is NOT a config/wiring gap (the 2026-07-12
  enablement smoke-test in tardis_concurrent_ip_lockout_2026_07_12.md correctly verified that path). Concurrently, the
  other 2 VMs launched in the SAME wave (cefi-queue-heavy-binancefutu-x15-20260715-202000,
  cefi-queue-light-bybit-x4-20260715-202022) show ZERO HTTP 403s over the same window, ruling out cross-VM/cross-fleet
  contention as the (sole) cause — no other Tardis-consuming VM was running (checked full instance list). Root cause
  read directly from source: TardisConcurrencyLease.ensure_process_lease_acquired() (tardis_concurrency_lease.py:262)
  sets the module-global _process_lease_attempted=True SYNCHRONOUSLY, immediately, BEFORE calling the (up-to-1800s)
  blocking lease.acquire() — and _ensure_tardis_concurrency_lease() (tardis_csv_transport.py:51) is called once PER
  SYMBOL FETCH from up to tardis_max_concurrent_downloads=16 (config default) concurrently-gathered asyncio coroutines
  per process. Only the FIRST coroutine to reach the check actually waits; every other coroutine racing in that same
  window sees the flag already True and returns immediately as a no-op, proceeding straight to its Tardis HTTP call
  WITHOUT the lease confirmed held. Live log evidence: 6 distinct-symbol 'Tardis streaming request' lines within a 2ms
  window (20:26:01,704-,706), each followed by a 403 code=274 — proof of true intra-process concurrency overlapping the
  lease-wait, not sequential retries. The 2026-07-12 enablement smoke-test (harness B) verified 'idempotent on re-call'
  via a SEQUENTIAL second call after the first completed — it did not exercise concurrent racing callers, so this gap
  was not caught."
status: open
priority: P1
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, tardis, concurrency, race-condition, lease, infra, backfill-efficiency]
related:
  [
    ./tardis_concurrent_ip_lockout_2026_07_12.md,
    ./cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md,
  ]
created: 2026-07-15
parent_epic: cefi_master
assigned_vm: planning
source:
  "Live-observed 2026-07-15T20:2x-20:3xZ while executing INFRA todo (4) of
  cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md (relaunching the 3-VM Tardis fleet
  against the fixed manifest-canonicalization tarball). Root cause traced directly against shipped source
  (tardis_concurrency_lease.py + tardis_csv_transport.py) on the live-defi-rollout HEAD checked out at the time
  (market-tick-data-service@90ecde17). No code changed this session — filed per the findings-triage HARD RULE (this is
  orthogonal to the manifest-canonicalization defect the parent plan is tracking, so it gets its own issue doc rather
  than being folded into that plan)."
locked_by:
locked_since:
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# TardisConcurrencyLease intra-process concurrent-fetch race — lease-wait silently skipped for 15/16 concurrent callers

## What I found

`TardisConcurrencyLease`'s process-wide singleton (`ensure_process_lease_acquired()`,
`market_tick_data_service/market_interface/clients/tardis_concurrency_lease.py:262`) is designed so only the FIRST call
per process actually acquires the lease; every subsequent call is meant to be a fast no-op because the process already
holds (or is holding) the lease. The implementation:

```python
if _process_lease_attempted:
    return
with _process_lease_lock:
    if _process_lease_attempted:
        return
    _process_lease_attempted = True      # <-- set BEFORE acquire() runs
    lease = TardisConcurrencyLease(...)
    lease.acquire()                       # <-- blocking, up to max_wait_seconds=1800
    _process_lease = lease
```

`_process_lease_attempted` flips to `True` the instant the first caller enters the lock — not after `acquire()`
resolves. `_ensure_tardis_concurrency_lease()` (`tardis_csv_transport.py:51`) is invoked once per symbol/date/data_type
fetch, and MTDS fans these out concurrently via `asyncio.gather` bounded by `tardis_max_concurrent_downloads` (config
default **16**, `service_config.py:220`). So on a cold process, up to 16 coroutines can call
`_ensure_tardis_concurrency_lease()` within the same tens-of-milliseconds window. Coroutine A wins the lock, flips the
flag, and starts (possibly slow) `lease.acquire()` in a thread executor. Coroutines B-P (the other ~15) then hit
`_process_lease_attempted == True`, return immediately, and proceed straight to their own Tardis HTTP call — **without
ever waiting for A's acquire() to actually resolve, and without holding the lease themselves.**

## Live evidence (this session, relaunching the cefi-queue-\* fleet per the parent plan's todo (4))

- `cefi-queue-light-binancefutu-x2-20260715-202013` (VENUES=BINANCE-FUTURES BITGET-FUTURES): 1928 `HTTP 403` lines (1167
  explicitly tagged `code=274`) in its run.log, all starting the moment it moved off the free (day=1) date onto
  `date=2026-01-02` (the first date requiring auth). It stalled on that single date for 9+ minutes vs. the sibling light
  VM's ~1-2 min/date pace.
- `cefi-queue-heavy-binancefutu-x15-20260715-202000` and `cefi-queue-light-bybit-x4-20260715-202022` — launched in the
  SAME wave, same TARDIS_CONCURRENCY_LEASE=1 config — show **zero** HTTP 403s over the identical window. Full
  `gcloud compute instances list` confirmed no other Tardis-consuming VM was running concurrently (the 4
  `cefi-hyperliquid/lighter-zksync/pacifica-solana/extended-starknet-2026` VMs use the non-Tardis
  `OnchainPerpBatchHandler` REST lane per the parent issue doc's own scope correction — they don't contend for the
  Tardis key). This rules out cross-VM/cross-fleet contention as the (sole) explanation for light-binancefutu's errors.
- Config/wiring verified NOT at fault: `TARDIS_CONCURRENCY_LEASE=1` and
  `TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-central-element-323112` confirmed present in (a) the VM's
  `gcloud compute instances describe` metadata, (b) the actual running process's `/proc/<pid>/environ` via SSH, and (c)
  `MarketTickDataServiceConfig.tardis_concurrency_lease_enabled` resolves `True` when the same env vars are replicated
  locally. This matches (does not contradict) the 2026-07-12 enablement smoke-test in
  `tardis_concurrent_ip_lockout_2026_07_12.md`, which verified the env→config→transport wiring is correct — that test
  called `_ensure_tardis_concurrency_lease()` a SECOND time only after the FIRST call had already completed ("idempotent
  on re-call"), which is a sequential re-call, not a concurrent-race scenario. It did not exercise 16-way concurrent
  callers racing the flag-flip, so it did not (and could not) catch this gap.
- Direct proof of true concurrency, not fast-sequential retries: `grep "Tardis streaming request"` shows 6 DIFFERENT
  symbols (`OXTUSDT`, `PORTALUSDT`, `SAGAUSDT`, `SNTUSDT`, `SOLVUSDT`, ...) requested within a ~2ms window
  (`20:26:01,704`-`20:26:01,706`), each immediately followed by its own `403 code=274` — consistent with ~16 coroutines
  firing near-simultaneously, only one of which could plausibly have been the lease-holder.

## Why it matters

- **Actively wastes the hard-capped 3-VM Tardis fleet's quota** (operator 2026-07-14 HARD cap,
  `codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap) on requests that get 403'd and land as
  `attempted_failed` in the manifest — real API calls burned for zero data, on a resource explicitly capped because it's
  scarce/contention-prone.
- **Silently degrades the honest-coverage gate the parent plan
  (`cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md` todo (3)) is trying to close**: a
  shard that legitimately has data but got 403'd during this race records as `attempted_failed`, indistinguishable
  (without log-diving) from a genuine no-data day — risks masking real coverage as a false gap on re-measurement, or
  requiring redundant re-fetch waves to paper over losses this bug caused.
- **Not a config mistake an operator can work around** — every launcher already sets `TARDIS_CONCURRENCY_LEASE=1` + the
  control bucket correctly per the 2026-07-12 fix; the bug is in the lease's own concurrency model, so it reproduces on
  every SINGLE_VM_QUEUE launch (the now-standard launch mode) that has ANY concurrent fan-out on a cold process's first
  non-free date, independent of whether other VMs are running.

## Recommended decision

The lease needs concurrent callers to actually WAIT for the in-flight acquisition, not skip past it. Two viable shapes,
not mutually exclusive:

1. **Have late callers await the SAME acquire, not skip it.** Replace the boolean `_process_lease_attempted` guard with
   an `asyncio.Event` (or a shared `Future`) that every caller `await`s: the first caller creates it and clears it once
   `lease.acquire()` (run in the executor) resolves; every other concurrent caller awaits the same event instead of
   returning immediately. Straightforward, keeps the "acquire once per process" design intent, and closes the race
   without touching the CAS/GCS mechanics that the 2026-07-12 smoke-test already proved correct.
2. **Gate the CONCURRENT fan-out itself on non-free dates** — hold the `tardis_max_concurrent_downloads` semaphore
   acquisition behind the lease check (rather than lease-check-then-semaphore, as today), so at most 1 request per
   process is ever in flight until the lease resolves, then ramp back up to 16 once held. More invasive, but also fixes
   any other future concurrency-gated-resource that needs the same "serialize until ready, then parallelize" shape.

Recommend (1) as the minimal, surgical fix — it directly targets the singleton race without changing the
already-verified CAS/GCS lease mechanics or the (unrelated, working) download concurrency model.

- [ ] [BACKEND] P1. Fix `ensure_process_lease_acquired()`
      (`market_tick_data_service/market_interface/clients/tardis_concurrency_lease.py:262`) so concurrent callers
      actually await the in-flight acquisition instead of skipping past a synchronously-set boolean flag (see option (1)
      above — an `asyncio.Event`/shared `Future` the first caller resolves once `lease.acquire()` returns). Add a
      regression test that spawns N concurrent callers before the first `acquire()` resolves and asserts only ONE real
      `lease.acquire()` call fires while the rest block until it resolves (extend the existing
      `tardis_concurrent_ip_lockout_2026_07_12.md` Harness A/B pattern — real GCS CAS, no mocks). (repo:
      market-tick-data-service)
- [ ] [SCRIPT] P2. Once fixed + verified, re-audit the `attempted_failed` rows the 3 relaunched cefi-queue-\* VMs wrote
      during this session's race window (`cefi-queue-light-binancefutu-x2-20260715-202013`, date=2026-01-02 primarily) —
      distinguish genuine no-data shards from this-bug-caused false failures (e.g. via `error_reason` containing
      `code=274`) so a targeted re-fetch (not a blind full re-run) closes just the affected shards. (repo:
      instruments-service or market-tick-data-service, whichever owns the manifest reconcile tooling)

## Progress Log

- **2026-07-15T20:3xZ (infra, slot-6)**: Filed this doc while executing
  `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md` todo (4). No fix attempted this session
  (out of scope for an INFRA relaunch task; needs a BACKEND-craft fix + regression test per above). The 3 relaunched VMs
  were left running — they are still making real, useful progress overall (the heavy VM and light-bybit VM show zero
  403s; light-binancefutu is the one affected VM and will eventually clear date=2026-01-02 and continue, just with some
  wasted/false-failed shards in the interim).
