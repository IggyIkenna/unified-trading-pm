---
doc_type: issue
title:
  Databento fetch path shares asyncio's default executor with aiohttp's DNS resolver — same bug class that wedged the
  Tardis backfill (lower severity, not yet observed in prod)
summary:
  databento_fetch.py:672 runs `loop.run_in_executor(None, _next_dbn_chunk, chunk_iter)` — the DEFAULT
  ThreadPoolExecutor, which is also where aiohttp's ThreadedResolver runs getaddrinfo. This is the same mechanism that
  wedged the CeFi Tardis backfill at cpu=0% with 203 ConnectionTimeoutError (root-caused + fixed 2026-07-17,
  market-tick-data-service@2e7c2b5d). Severity here is LOWER and the failure has NOT been observed on the TradFi path --
  Databento parks a worker per CHUNK (short, released between chunks) whereas Tardis parked one for the ENTIRE transfer
  -- so the pool cycles rather than filling. It is still a latent starvation risk whenever concurrent fetches x
  per-chunk duration saturates min(32, cpu+4). Filed as a follow-up, NOT a claimed live defect.
status: open
resolved_by:
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, databento, asyncio, executor, dns, latent-risk, follow-up]
related: [/plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md]
created: 2026-07-17
source:
  - Found while root-causing the CeFi Tardis throughput collapse 2026-07-17 (adjacent-code finding; triaged to its own
    issue doc rather than widened into that fix's commit).
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
drift_direction: advance-code
parent_epic: infrastructure_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
---

# Databento fetch path shares the default executor with aiohttp's DNS resolver

## The mechanism (proven on the Tardis path, latent here)

`market_tick_data_service/market_interface/adapters/tradfi/databento_fetch.py:672`:

```python
raw_chunk = await asyncio.wait_for(
    loop.run_in_executor(None, _next_dbn_chunk, chunk_iter),   # None == DEFAULT pool
    timeout=timeout_s,
)
```

asyncio's **default** ThreadPoolExecutor is capped at `min(32, cpu_count + 4)` (= **20** on a 16-vCPU box), and
aiohttp's `ThreadedResolver` runs `getaddrinfo` **on that same pool**. When blocking work fills it, DNS cannot resolve,
every new connection dies at the `connect` timeout, and the run wedges. In aiohttp, `connect` covers **DNS + pool
acquisition**, not just the TCP handshake — so the symptom masquerades as a network/vendor fault.

Reproduced locally (`market-tick-data-service/tests/unit/test_tardis_parse_executor_dedicated.py`): saturate the default
pool with `N = pool_size` blocking tasks → `getaddrinfo` **starves >8.0s**; dedicated pool → **0.01s**.

## Why this is LOWER severity than the Tardis case (be precise)

|                       | Tardis (fixed)                                                                       | Databento (this issue)                                                |
| --------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| what holds the worker | the **whole transfer** — the parse blocks pulling chunks off the network for minutes | **one chunk** — `_next_dbn_chunk` pulls the next chunk, then releases |
| pool behaviour        | fills and **stays** full → hard wedge                                                | **cycles** → transient pressure                                       |
| observed in prod?     | YES — 203 `ConnectionTimeoutError`, 45 min frozen at cpu=0.0%, 0.49 MB/s             | **NO — not observed**                                                 |

The Tardis defaults were exactly pathological (16 downloads + 4 book-snapshots = 20 = the pool). Databento has no
equivalent standing saturation, which is very likely why this has never bitten. **This is a latent risk, not a live
defect** — do not cite it as a known TradFi outage cause.

## Todos

- [x] ✅ [CODE] P1. **DONE (already landed as `mtds@ac857`, confirmed 2026-07-26, slot-12)**: the Databento chunk pull
      uses a dedicated `_get_dbn_fetch_executor()` (`databento_fetch_executor.py`), not the default pool — verified live
      in `databento_fetch.py` at all 3 named call sites (`:192`, `:394`, `:683`).
- [x] ✅ [AUDIT] P2. **DONE (confirmed 2026-07-26, slot-12)**: swept all named call sites — `databento_batch_jobs.py`
      (now `:661`) already uses `_get_dbn_fetch_executor()`; `databento_fetch.py:186/:388/:672` (now `:192/:394/:683`
      after intervening edits) all use it too. Only `databento_base_client.py:499` (warmup) still uses the default pool,
      exactly as pre-classified above — one-shot, not holds-for-transfer, no change needed.
- [x] ✅ [CODE] P2. **DONE — `market-tick-data-service@889ff829`.** `aiodns` viable (transitively available via ccxt,
      promoted to direct dep). Databento itself has no aiohttp session to switch (synchronous SDK). Fixed the real
      targets: `tardis_stream_client.py` (was hardcoding `ThreadedResolver()`) and `tardis_base_client.py` (was relying
      on aiohttp's implicit resolver-picks-AsyncResolver-if-aiodns-importable behavior) — both now explicit
      `AsyncResolver()`. 2 new regression tests + a live DNS smoke test against `api.tardis.dev` (200 OK). Full
      evidence: `plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s corresponding todo. **Same-pattern
      follow-up (not done here, out of this tradfi-scoped todo)**: `aster_base_client.py` and
      `hyperliquid_base_client.py` (CEFI-only live-venue clients) hardcode the identical `ThreadedResolver()` pattern —
      a future CEFI-scoped todo could apply the same fix there.

## Progress Log (append-only)

- 2026-07-17: filed. Found while root-causing the CeFi Tardis collapse (`eb336036`, 2026-06-11, put the blocking parse
  on the default pool). Deliberately NOT folded into `market-tick-data-service@2e7c2b5d` — that commit fixes the Tardis
  path where the failure is measured; widening it to a path where the failure is only theoretical would have shipped an
  unverified change under the cover of a verified one. Severity stated honestly: same class, lower risk, unobserved.
- 2026-07-26 (slot-12): closed out all 3 remaining todos. Todos 1+2 were already done (dedicated executor landed as
  `mtds@ac857` at some point after this doc was filed, never checked off; audit sweep confirmed all named call sites
  compliant). Todo 3 (aiodns/AsyncResolver) genuinely required new code — shipped `market-tick-data-service@889ff829`.
  Status left `open` pending someone picking up the flagged CEFI (aster/hyperliquid) follow-up, otherwise this doc's own
  scope is now fully closed.
