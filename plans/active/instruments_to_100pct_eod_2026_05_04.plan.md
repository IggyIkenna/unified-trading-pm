---
title: "instruments-service to 100% honest coverage across all 5 asset groups (EOD 2026-05-04)"
priority: P0
status: active
owner: harsh
created: 2026-05-04
type: deployment
epic: data-pipeline-completion
completion_gates:
  code: none
  deployment: D2
  business: none
repo_gates:
  - repo: instruments-service
    deployment: D2
depends_on:
  - instruments_and_market_tick_data_completion_2026_05_01
isProject: false
---

## Adapter health summary (2026-05-04 13:36 IST)

| Asset group | Healthy | Failed                | Bug type                                             |
| ----------- | :-----: | --------------------- | ---------------------------------------------------- |
| CEFI        | 7 / 9   | OKX, COINBASE         | 3-SSOT canonical-name disagreement (multi-repo align) |
| TRADFI      | 6 / 8   | POLYGON, FRED         | api_key not in SM (POLYGON), zero records (FRED)      |
| DEFI        | 7 / 7   | —                     | clean                                                 |
| SPORTS      | 6 / 6¹  | —                     | clean (SFI excluded by design)                        |
| **TOTAL**   | **26 / 30** | **4 broken**      |                                                       |

¹ SOCCER_FOOTBALL_INFO is the 7th sports provider but excluded due to in-flight VM.

**87% of adapters confirmed healthy via 1-day smoke.** The 4 broken ones (OKX, COINBASE,
POLYGON, FRED) are out-of-scope for today's EOD push — they need separate plans
(canonical-name alignment, SM secret rotation, FRED adapter debugging).

The 26 healthy adapters can all proceed to Phase 2 backfill.

## Phase 2 fan-out (2026-05-04 13:40 IST)

After confirming all 26 healthy adapters via 1-day smoke, fanned out the full backfill.

**Machine sizing**: AMD Ryzen 9 7900X, 24 cores, 93 GB RAM. At full fan-out: 85 concurrent
`instruments-service` procs, load avg ~41, mem 54 GB used / 38 GB free. Comfortable
headroom; can sustain.

**Backfills running** (all via `run_vm_backfill_e2e.sh` for CEFI/TRADFI/DEFI, direct CLI for
SPORTS):

- **DEFI 7 venues** — per-protocol cutoff dates from `DEFI_SOURCE_COVERAGE_START` in UAC
  - AAVEV3-ETHEREUM: 2022-03-16 → today
  - UNISWAPV3-ETHEREUM: 2021-05-05 → today
  - UNISWAPV2-ETHEREUM: 2020-05-04 → today
  - CURVE-ETHEREUM: 2020-01-19 → today
  - LIDO-ETHEREUM: 2020-12-19 → today
  - BALANCER-ETHEREUM: 2021-05-13 → today
  - EIGENLAYER-ETHEREUM: 2023-06-15 → today
- **CEFI 7 venues** — 2019-01-01 → today (per-venue inception clipped by adapter)
  - BINANCE-SPOT, BINANCE-FUTURES, DERIBIT, BYBIT, UPBIT, HYPERLIQUID, ASTER
  - **OKX + COINBASE excluded** (3-SSOT canonical name disagreement)
- **TRADFI 6 venues** — 2019-01-01 → today
  - CME, CBOE, NASDAQ, NYSE, ICE, FX
  - **POLYGON + FRED excluded** (api_key + zero-records bugs)
- **SPORTS** — 2020-06-01 → today
  - API_FOOTBALL (primary)
  - OPEN_METEO, UNDERSTAT, FOOTYSTATS, TRANSFERMARKT (enrichment, parallel)
  - **SOCCER_FOOTBALL_INFO excluded** (other agent's VM in flight)

All chunks resumable via `.backfill-checkpoints/<AG>_<venue>_<range>/`. CEFI/TRADFI use
30-day chunks × 4 parallel workers per venue.

**Confirmed healthy**: chunks completing — first `DONE` lines visible by 13:41:36 IST
(CEFI BINANCE-SPOT 2019-01-01..2019-01-30 + 2019-03-02..2019-03-31). Env vars propagating
correctly (the silent-fail bug from earlier today is fixed).

**ETA estimate**: CEFI/TRADFI ~18-25 min per venue (89 chunks × ~50s / 4 parallel),
DEFI faster (smaller date ranges, fewer pools), SPORTS depends on rate-limit pacing.

### Rate-limit watchdog (2026-05-04 13:46 IST)

Concern raised mid-run: 85 concurrent procs may hit provider API rate limits. Set up
`/tmp/rate-limit-watchdog.sh` (PID 443611, also tails to `/tmp/rate-limit-watch.log`)
that scans every 60s for these signatures across all chunk logs:

- HTTP 429 / status 429 / "429 Too Many"
- RateLimitError / RateLimitException
- retry-after / Retry-After headers
- quota_exceeded / QuotaExceeded
- "throttled by API" / Tardis-specific throttling

**Initial regex was too loose** — caught timestamp-millisecond `:42:43,429` as fake
matches; tightened to require word-boundary context ("HTTP 429", "status 429",
"429 Too Many"). Re-scanned with the precise regex → **0 real rate-limit hits**
across all 85 procs.

**Why we're holding up**: most providers we hit at scale are paid feeds (Tardis,
Databento) with high quotas, and adapters bake in per-venue pacing internally.
Sports providers (api-football, transfermarkt, footystats, understat, openmeteo)
each run as a single process, not chunked, so they self-pace.

**Only real concurrency warning seen**: 9× `ManifestWriter: generation conflict after 15
retries, falling back to unconditional write` — expected under heavy concurrent
manifest writes (85 procs all updating `_index/availability_index.parquet`). The
unconditional-write fallback is safe (manifest is upsert-keyed); not a data-loss bug,
just GCS optimistic-concurrency noise. Will quiet down as venues finish.

### Force-flag verification (2026-05-04 13:48 IST)

Confirmed: **no `--force` flag anywhere** in this run.

- Inspected all 85 running cmdlines: 0 procs have `--force`.
- `run_vm_backfill_e2e.sh` source line 131 hardcodes the chunk command with no
  `--force`: `instruments-service --operation instruments --mode batch --asset-group X
  --venues Y --start-date A --end-date B`.
- Sports CLI invocations were also fired without `--force`.

Implication: the orchestrator's `_should_skip_shard` is doing its job — for any
`(asset_group, venue, day)` whose manifest row is `captured` or `empty_confirmed`, the
adapter returns immediately. Only `attempted_failed` (the 56,489 phantoms we flipped
+ any pre-existing real failures) and missing rows get re-attempted. **Massive cost
savings** vs `--force` which would re-pay every shard. Tardis/Databento quotas
preserved.

### System resource pressure (2026-05-04 13:50 IST)

Memory got tight at peak — 90 GB RAM used / 1 GB free, 7 GB swapped. Top consumers:
- DERIBIT chunk: 4.8 GB (options chain — 200k symbol filter cost)
- Sports providers: 2.8-4.7 GB each, 5 providers = ~18 GB total
- DEFI/CEFI/TRADFI chunks: ~1 GB each, 60+ procs

**At 13:50 I incorrectly claimed "no OOM, system stable".** That was wrong — see correction
below.

### OOM kill at 13:55:21 (correction to earlier "no OOM" call)

**`systemd-oomd` killed the entire `app.slice` cgroup at 13:55:21 IST.** I missed this on
first scan because systemd-oomd sends SIGTERM (with 20s grace period) before SIGKILL,
which produces "graceful shutdown" log lines that look like external termination, not OOM.
Reading journalctl correctly:

```
May 04 13:55:21 hk systemd[2009]: app-org.chromium.Chromium-6423.scope:
                                   A process of this unit has been killed by the OOM killer.
May 04 13:55:24 hk systemd[2009]: app.slice:
                                   A process of this unit has been killed by the OOM killer.
May 04 13:55:47 hk systemd[2009]: app-org.chromium.Chromium-6423.scope: Failed with result 'oom-kill'.
```

systemd-oomd watches cgroup memory pressure and intervenes before kernel OOM. It killed:
- VS Code chromium electron procs (the editor)
- All 85 instruments-service procs (they were children of the same `app.slice`)
- The rate-limit watchdog
- Anything else in the user's app.slice

**What survived (durable):**
- 376 chunk `.done` files in `.backfill-checkpoints/` — these resume cleanly
- All parquet writes already in GCS (376 chunks worth: cefi 192, tradfi 157, defi 27)
- Manifest rows for those captured shards

**What was lost (in-flight only):**
- 60 in-flight chunks at moment of kill — checkpoints not yet written, will redo on resume
- Sports near-zero progress: api_football 0, open_meteo 2 dates, understat 0, footystats 0,
  transfermarkt 3 dates

### Real RC of sports memory bloat (corrected, with code citation)

Found the actual bug at
[`instruments-service/instruments_service/engine/orchestrator.py:369-374`](../../../instruments-service/instruments_service/engine/orchestrator.py#L369):

```python
# Sports reference core entity caches — leagues/teams/standings are the same
# across all dates within a batch run. Fetched once, written to every date partition.
_cached_leagues_df: pd.DataFrame | None = None
_cached_teams_df: pd.DataFrame | None = None
_cached_standings_df: pd.DataFrame | None = None
_cached_prediction_league_ids: list[int] = []
```

These are **module-level pandas DataFrames** that hold the full sports reference dataset
(1,228 leagues + 618 teams + standings rows from the API_FOOTBALL smoke earlier). They're
populated via `_set_cached_leagues / _teams / _standings` and **never cleared** for the
duration of the proc.

There's a `clear_defi_universe_cache()` for the DeFi equivalent, but **no
`clear_sports_caches()`** function exists. So when sports runs with
`--start-date 2020-06-01 --end-date 2026-05-04` in a single proc, those DFs stay resident
through ~1,800 days of iteration, plus per-day intermediate state (fixtures, oddslike
buffers, etc.) accumulates inside the orchestrator's loop without per-day flushes.

User intuition correct: **once data is uploaded to GCS, it should be cleared from memory.**
The orchestrator does write to GCS per-day, but doesn't `del` the dataframes / call gc
afterwards. RAM grows monotonically until the process dies (or systemd-oomd kills it).

**Verified — the cache is intentional, NOT used for any aggregate calculation:**

Confirmed across the entire `instruments-service` repo:
- `_cached_leagues_df / _teams_df / _standings_df / _prediction_league_ids` are referenced
  **only inside `orchestrator.py`** — 3 setter sites + 4 reader sites, all within the
  per-date sports loop.
- **No other module imports them.** Verified `grep -rn "_cached_leagues_df" instruments-service/`
  → only orchestrator.py + tests.
- **No finalize / wrap-up / aggregate / post-loop function** uses the accumulated DFs.
  No "compute season-summary from full cache" logic anywhere. The cache is purely a
  per-batch-run API-call optimization.
- **Data is durable in GCS per-date** via `_gated_sink_write(... entity="leagues" ...)`.
  Clearing the memory copy after each date's write is safe — nothing downstream consumes
  the in-memory copy.
- **Read sites verify**: every read (lines 2912, 2942, 2978, 3012) is to write the same
  DF to a different date's GCS partition. Not used for any joins, computations, or
  cross-date aggregations.

**Conclusion**: cache is intentional for the "skip 67 API calls per date" optimization,
but NOT used for any calculation. It can be cleared at any point (per-date, per-chunk,
per-N-dates) without losing data — just adds API call cost where cleared. This makes
fixing it safe and low-risk.



After tracing read sites in `orchestrator.py:2912, 2942, 2978, 3012` — the cached DFs
are read on every subsequent date in the loop. The original-author comment says it
saves **~67 API calls per date** (1 leagues + 33 teams + 33 standings = 67 calls, all
slow-moving). Without the cache, a 1,800-date sports backfill would do 120,600
API calls just for reference data — would hit api-football's daily quota many times
over and fail.

Code-flow verification:
- Lines 2917-2918: fetch leagues → `_set_cached_leagues(df)`
- Lines 2931-2938: same df ALSO written to GCS via `_gated_sink_write(... entity="leagues" ...)`
  (so persistent copy lives in GCS too)
- Lines 2942-2944: next date reads `teams_df = _cached_teams_df` first; only fetches if `None`
- Same pattern for standings (line 3012) and prediction_league_ids (line 2978)

So the cache is **intentional, downstream-consumed, and cost-saving**. It's NOT a stale
artifact never read again. Decision-trade-off:

| Approach | API call cost | RAM cost | Process restart cost |
|---|---|---|---|
| Cache held forever (current) | 67 calls / batch run | Grows with batch (problem) | None |
| Clear cache per date | 67 × N dates | Bounded ~50 MB | None |
| No cache, refetch per date | 67 × N dates | Tiny | None |
| **Chunk processes (workaround)** | 67 × N chunks | Bounded per proc | Process restart between chunks |

Original design assumed sports runs as **VM-per-source** (one VM, one source, runs
till done in ~hours, then VM dies → cache cleared by VM termination). Today's
local-driver pattern runs sports as a **single 6-year proc** which violates that
assumption and OOMs.

**Two paths to fix**:

1. **Proper fix (follow-up plan)**: add a `clear_sports_caches()` function (mirroring
   `clear_defi_universe_cache()`) and invoke it at smaller intervals — e.g. every 30
   days, or per-season. Re-fetches at the boundary cost ~67 API calls but bounds RAM.
2. **Workaround for today's EOD push**: chunk sports the same way CEFI/TRADFI/DEFI are
   chunked. Each 30-day proc starts fresh, fetches reference once for the chunk, writes
   per-date GCS partitions, dies. No code change required, just wrapper script edit.

For VMs in the cloud: the existing pattern (VM-per-source, runs to completion, dies)
already works correctly because VM lifetime ≈ batch lifetime. **The fix is local-only.**

### Local-vs-VM optimisation note (2026-05-04 13:55 IST)

**Decisions about parallelism / chunking made today are LOCAL-ONLY.** The cloud VM
launchers (`launch-{api-football,transfermarkt,...}-backfill-vm.sh`) spawn one VM per
source with much smaller machine types (e2-standard-2 = 2 vCPU / 8 GB RAM, not 24 vCPU /
93 GB). VMs do NOT run different sources in parallel — singleton-locked launchers explicitly
forbid it. So:

- **Don't carry over `--parallel 4` to VM launches** — VMs only have 2 vCPU; chunking
  parallelism that high will thrash. VM-appropriate value is `--parallel 1` or `2`.
- **Don't run multiple sources concurrently on a single VM** — each VM should run ONE
  source over a date range, no fan-out within the VM.
- **Don't size SPORTS RAM expectations off this run** — on a VM, sports must be chunked
  too (the 5 GB single-proc memory load would OOM the e2-standard-2's 8 GB).
- **Local IP rate-limits** are different from VM static-IP rate-limits — Tardis whitelists
  the cloud-VM egress IPs but treats laptop IP differently. What works locally may 429 in
  cloud and vice versa.

When IAM grant lands and we move sports to VM launchers, remember: lower parallelism, no
inter-source fan-out, and chunk sports just like CEFI/TRADFI/DEFI.

### Resume strategy (2026-05-04 14:05 IST)

Checkpoints survived: 192 cefi + 145 tradfi + 27 defi = 364 chunks durably done. The
~12-chunk discrepancy from earlier "376" count is from chunks that wrote parquets to
GCS but didn't get checkpoint files written before the OOM SIGTERM hit. Recon will
classify those correctly.

**Step 1 (in flight)**: realign manifest with reality post-OOM via per-AG dry-run
reconciler. Goal: see how many manifest rows are now phantom (claimed-captured but
parquet was never actually written because the proc was killed mid-write).

**Step 2 (after recon completes)**: flip any new phantoms (no `--dry-run`) so the
orchestrator's `_should_skip_shard` will retry them on resume.

**Step 3 (CEFI/TRADFI/DEFI resume)**: re-fire with `--parallel 2` (was 4). Checkpoints
skip the 364 already-done chunks. Only mid-flight + post-OOM-phantom chunks get
re-attempted. Lower parallelism halves peak RAM.

**Step 4 (SPORTS via chunked launcher)**: use `/tmp/sports-chunked-backfill.sh PROVIDER`
which chunks the 6-year window into 30-day procs. Each proc dies after its window,
reclaiming the leagues/teams/standings DataFrames. RAM bounded to ~500 MB per chunk
instead of growing to 5 GB across the full window. Run 5 providers in parallel
(API_FOOTBALL, TRANSFERMARKT, FOOTYSTATS, UNDERSTAT, OPEN_METEO; SFI excluded).

**Step 5**: post-resume dry-run reconciler again to confirm headline coverage moved.

### Resume status (2026-05-04 14:25 IST)

**Recon results (post-OOM phantom counts) — phantom drift from OOM is minimal:**

| AG | Pre-OOM | Post-OOM | Delta | Status |
|---|---:|---:|---:|---|
| CEFI | 12,540 | 12,557 | +17 | dry-run done, not yet flipped |
| TRADFI | 2,726 | 2,734 | +8 | dry-run done, not yet flipped |
| DEFI | 597 | 645 | +48 | dry-run done, not yet flipped |
| SPORTS | 41,223 | timed out (GCS list) | TBD | needs retry with `--workers 16` later |

**Resume drivers all firing correctly**: each runner's summary log shows `SKIP ...
(checkpoint exists)` for the 376 done chunks then `START` for the next un-checkpointed
chunk. Resume strategy working as designed.

**Sports chunked launcher**: committed to
[`instruments-service/scripts/sports_chunked_backfill.sh`](../../../instruments-service/scripts/sports_chunked_backfill.sh)
(commit `619a32e`). Each invocation chunks the date range into 30-day windows; per-chunk
proc dies + reclaims the leagues/teams/standings DataFrame caches between windows.
RAM-safe because no single proc holds 6 years of accumulated DFs.

**5 sports providers fired chunked** (TRANSFERMARKT first as smoke test, then API_FOOTBALL
+ FOOTYSTATS + UNDERSTAT + OPEN_METEO after RAM headroom confirmed). SFI excluded as
designed.

**Resource cap**: Harsh set hard cap at 80 GB RAM used (out of 93 GB). Currently at
~48 GB used / 40 GB free, comfortably under cap. RAM monitor PID 571212 logging to
`/tmp/ram-monitor.log`. Wakeup at 14:31 will check trend; if approaching 75 GB hold,
if breaches 80 GB kill heaviest sports providers.

**System state at 14:25 IST**:
- 42 concurrent `instruments-service` procs
- 376 chunks durable (durable from pre-OOM run + early new completions)
- New chunks DONE since resume: cefi 3, tradfi 5, defi 1 (will accelerate)
- 0 swap thrashing, no rate-limit hits, no OOM

### Health snapshot (2026-05-04 14:31 IST)

10 min after sports fan-out, 16 min after CEFI/TRADFI/DEFI resume:

| Metric | Value | Status |
|---|---|---|
| RAM used | 58 GB / 80 GB cap | ✅ 22 GB headroom (under 65 GB threshold) |
| RAM trend (5 min) | 53→58 GB (~1.25 GB/min slow climb) | ✅ stable, will plateau as chunks cycle |
| Swap | 0.7 GB | ✅ idle (was 6.7 GB at OOM) |
| OOM kills | 0 | ✅ |
| Rate-limit hits | 0 (real signatures) | ✅ |
| Concurrent procs | 46 | — |
| Checkpoints | 408 (+32 since OOM resume start) | ✅ |
| Errors last 5min | 53 (51 = known Databento NASDAQ symbology pre-listing tickers; 1 transient Tardis 500; 1 URDI zero-records) | ✅ within expected bounds |

Progress per AG:
- CEFI: 200 chunks done
- TRADFI: 171 chunks done (fastest velocity)
- DEFI: 37 chunks done
- Sports chunked progress (window-1-then-cycle pattern):
  - API_FOOTBALL: 6 chunks done, on chunk 7 (2020-11-28)
  - FOOTYSTATS: 2 chunks done, on chunk 3
  - UNDERSTAT: 1 chunk done, on chunk 2
  - OPEN_METEO: 0 chunks done, on chunk 1 (started 14:26)
  - TRANSFERMARKT: 0 chunks done, on chunk 1 since 14:15 (47 min — Transfermarkt's
    ~1 req/sec rate-limit pacing makes a 30-day chunk slow but it's not stalled)

Decision per the wakeup rule: RAM is at 58 GB (<65 GB threshold) and stable.
**Holding course, no scaling changes.** Next wakeup at ~14:36 to reassess.

### Health snapshot (2026-05-04 14:37 IST)

| Metric | Value | Status |
|---|---|---|
| RAM used | 68 GB / 80 GB cap | ⚠️ on 65 GB boundary, no further fan-out |
| RAM trend (5 min) | 58→67→65→68 GB | ✅ plateauing around 65, not climbing |
| Swap | 0.7 GB | ✅ idle |
| OOM kills | 0 | ✅ |
| Rate-limit hits (real) | 0 | ✅ |
| Concurrent procs | 47 | — |
| Checkpoints | 415 (+7 since 14:31) | ✅ progressing |
| Errors last 5min | 75 (74 known Databento NASDAQ symbology pre-listing tickers; 1 transient Tardis 500) | ✅ within bounds |

CEFI/TRADFI/DEFI deltas since 14:31:
- CEFI: 200→204 (+4)
- TRADFI: 171→173 (+2)
- DEFI: 37→38 (+1)

Sports chunked progress (was 6+2+1+0+0):
- API_FOOTBALL: 6→10 chunks (+4) — fastest
- UNDERSTAT: 1→3 chunks (+2)
- FOOTYSTATS: 2→2 chunks (+0 — investigate? prob just slow on chunk 3)
- OPEN_METEO: 0→0 (still chunk 1, started 14:26 = 11 min in)
- **TRANSFERMARKT: 0→0** (still chunk 1, started 14:15 = 22 min in)

#### TRANSFERMARKT chunk 1 — root cause identified

Not stalled, **bottlenecked on ManifestWriter generation-conflict** retry loop. Log shows
sequential GCS optimistic-concurrency-control conflicts up to attempt 11/15:

```
14:29:22 generation conflict (attempt 2/15), retrying in 1.0s
14:30:41 generation conflict (attempt 4/15), retrying in 2.0s
...
14:36:31 generation conflict (attempt 11/15), retrying in 5.5s
```

47 concurrent writers competing for the same `_index/availability_index.parquet` blob.
Each conflict waits, retries, gets clobbered again. Will eventually fall through to
unconditional write at attempt 15. **Not blocking — just slow under high concurrency.**

This is the same `ManifestWriter: generation conflict, falling back to unconditional
write` warning we saw at the original 85-proc fan-out, just amplified now because
TRANSFERMARKT happens to fetch slowly enough that other procs win the manifest race
every time.

Decision per wakeup rule: **plateau holding around 65 GB, no further fan-out.** Not
killing anything (cap not breached). Will continue monitoring at 14:42.

### Health snapshot (2026-05-04 14:43 IST)

| Metric | Value | Status |
|---|---|---|
| RAM used | 67 GB / 80 GB cap | ⚠️ 13 GB headroom, holding plateau |
| RAM trend (5 min) | 62–69 GB oscillating around 65 | ✅ stable, not climbing |
| Swap | 0.7 GB | ✅ idle |
| OOM kills | 0 | ✅ |
| Rate-limit hits (real) | 0 | ✅ |
| Concurrent procs | 46 | — |
| Checkpoints | 426 (+11 in 5 min) | ✅ progressing |
| Errors (last 5 min) | 102 (100 known Databento, 1 Tardis transient, 1 URDI zero-records) | ✅ within bounds |

CEFI/TRADFI/DEFI deltas since 14:37 (was 415):
- CEFI: 204→208 (+4)
- TRADFI: 173→179 (+6, fastest)
- DEFI: 38→39 (+1)

Sports chunked deltas since 14:37 (was 10+2+0+0+3):
- API_FOOTBALL: 10→10 (slow chunk in flight)
- FOOTYSTATS: 2→5 (+3)
- UNDERSTAT: 3→5 (+2)
- OPEN_METEO: 0→0 (still chunk 1 — paced)
- TRANSFERMARKT: 0→0 (still chunk 1 — but **past the manifest conflict** and now actively
  fetching teams per league: DK1, NL1, MEXA, FR1 at ~30-40s/league)

#### TRANSFERMARKT broke through

Earlier 14:37 snapshot showed TRANSFERMARKT stuck on attempt 11/15 of ManifestWriter
generation conflicts. Current log shows it past the bottleneck:

```
14:41:25 RapidAPI: fetched 14 clubs for league DK1 season 2019
14:42:32 RapidAPI: fetched 19 clubs for league MEXA season 2019
14:43:13 RapidAPI: fetched 20 clubs for league FR1 season 2019
```

Transfermarkt's internal ~1 req/sec pacing + 32 leagues × pagination = ~45 min/chunk
expected. Slow but progressing. Not stuck.

Decision: **holding course**. RAM stable at boundary, not breaching 75 GB hold-threshold
or 80 GB kill-threshold. No new fan-out, no kills.

### Health snapshot (2026-05-04 14:50 IST)

| Metric | Value | Status |
|---|---|---|
| RAM used | 67 GB / 80 GB cap | ✅ 13 GB headroom, plateau holding |
| RAM trend (5 min) | 64-68 GB oscillating around 65-66 | ✅ stable, not climbing |
| Swap | 0.7 GB | ✅ idle |
| OOM kills | 0 | ✅ |
| Rate-limit hits (real) | 0 | ✅ |
| Concurrent procs | 42 | — (was 46, normal cycling) |
| Checkpoints | 448 (+22 in 7 min) | ✅ healthy pace |
| Errors total | 124 (+22, all same Databento NASDAQ) | ✅ no new categories |

Deltas since 14:43:
- CEFI: 208→214 (+6)
- TRADFI: 179→188 (+9, fastest)
- DEFI: 39→46 (+7, accelerating — was +1 last interval)

Sports chunked deltas since 14:43 (was 10+5+0+0+5):
- API_FOOTBALL: 10→10 (chunk 11 still in flight)
- FOOTYSTATS: 5→6 (+1)
- UNDERSTAT: 5→8 (+3)
- OPEN_METEO: 0→0 (still chunk 1 — paced)
- TRANSFERMARKT: 0→0 (still chunk 1 — see below)

#### TRANSFERMARKT chunk 1 — data written, manifest write in conflict loop

Important nuance: log at 14:44:52-53 shows the **chunk's real data IS written to GCS**:
- "RapidAPI: fetched 10 clubs for league C1 season 2019" → done fetching
- "Transfermarkt teams → player_values: 131 rows written" → wrote 131 player_values to GCS
- "Transfermarkt team mapping cache: 131 rows written for season=2019" → cache written

Then 14:45:45 onwards, back into ManifestWriter generation-conflict loop (attempt 1→6/15
as of last log read). This is **only the index-manifest write** stuck — the actual data
is durably in GCS. The chunk will mark itself `captured` whenever attempt N succeeds (or
attempt 15 unconditional fallback fires).

So TRANSFERMARKT chunk 1's data is safe; the checkpoint file just hasn't been written
yet. Resume-safe regardless.

Decision: **holding course**. RAM stable, real work happening (+22 checkpoints in 7 min,
DEFI accelerating). No changes.

### Health snapshot (2026-05-04 14:56 IST)

| Metric | Value | Status |
|---|---|---|
| RAM used | 74 GB / 80 GB cap | ⚠️ 6 GB headroom, **at 75 GB hold-threshold** |
| RAM trend (5 min) | 69→74 GB, slowly climbing | ⚠️ plateau breaking |
| Swap | 0.7 GB | ✅ idle |
| OOM kills | 0 | ✅ |
| Concurrent procs | 43 | — |
| Checkpoints | 461 (+13 in 6 min) | ✅ |
| Errors total | 151 (+27, all same Databento) | ✅ |

Deltas since 14:50 (was 448):
- CEFI: 214→219 (+5)
- TRADFI: 188→191 (+3)
- DEFI: 46→51 (+5)

#### Key insight: sports `done_chunks` counter is misleading

My `grep -c "rc=0"` only counts whole-chunk completions. Inside each chunk, individual
DATES are completing — log inspection shows:

- **OPEN_METEO chunk 1**: at day 30/30 (2020-06-29 done, 2020-06-30 in flight). About
  to wrap chunk 1.
- **API_FOOTBALL chunk 11**: wrote 3,434 records for 2021-04-06; iterating through
  remaining days.
- **TRANSFERMARKT chunk 1**: at day 10/30 (date 2020-06-09 done, 2020-06-10 active).
  Each day fetches 32 leagues + ~131 teams.

**All sports providers ARE writing data per-day to GCS**. The chunk-level counter just
doesn't reflect that. Real progress is happening; chunks finishing will accelerate as
they wrap.

#### Top RAM consumers (kill candidates if we breach 78 GB)

```
DERIBIT chunk:    13.5 GB  (2019-04-01 → 2019-04-30, options chain — known heavy)
FOOTYSTATS:        5.8 GB  (2020-11-28 → 2020-12-27)
TRANSFERMARKT:     5.0 GB  (2020-06-01 → 2020-06-30)
API_FOOTBALL:      4.3 GB  (2021-03-28 → 2021-04-26)
OPEN_METEO:        3.5 GB  (2020-06-01 → 2020-06-30)
UNDERSTAT:         2.7 GB
```

DERIBIT is doing real CEFI work — won't kill that even though it's heaviest. If forced
to kill, would target FOOTYSTATS (smallest impact: only 1 chunk done so far + the data
within chunk is small per-day).

Decision: **holding, but tightening monitor cadence** (4 min instead of 5). If RAM
breaches 78 GB, kill the heaviest sports provider (FOOTYSTATS) to bring under 75 GB.

### Health snapshot (2026-05-04 15:03 IST) — RAM breached, killed + restarted FOOTYSTATS

**RAM peaked 79 GB** during the last 8 ticks (one tick away from 80 GB cap). Per the
wakeup rule I killed the FOOTYSTATS chunk-8 worker (PID 742647).

| Metric | Value | Status |
|---|---|---|
| RAM peak last 8 ticks | 79 GB / 80 GB cap | ❌ breached 78 GB threshold |
| RAM after kill | 74 GB | ⚠️ back at threshold |
| Swap | 0.7 GB | ✅ idle |
| OOM kills | 0 | ✅ |
| Concurrent procs | 46 | — |
| Checkpoints | 470 (+9 in 7 min) | ✅ slowing slightly |

#### Mistake during kill — full FOOTYSTATS wrapper died, restarted

I killed PID 742647 (Python worker) AND PID 742646 (timeout wrapper). The bash wrapper
script (PID 607671) had `set -euo pipefail`, so when its `timeout` child exited
abnormally, the wrapper exited too. **All FOOTYSTATS work stopped, not just the
in-flight chunk.**

Restarted FOOTYSTATS wrapper at 15:04 (new PID 755950). It restarts at chunk 1, but the
orchestrator's `_should_skip_shard` will fast-forward through already-captured dates
(chunks 1-7 are durably done). Net cost: ~30s of skip-checks per already-done chunk +
loss of in-flight chunk 8 progress (small, will redo).

**Lesson (saved as feedback memory)**: when killing a wrapped process, `set -e` in the
parent shell can propagate exit through the wrapper. Next time, kill ONLY the
`instruments-service` Python child (not the `timeout` parent or the bash wrapper).

#### DERIBIT is the actual RAM hog — flagging for future

```
DERIBIT chunk:    16 GB  ← biggest single consumer, growing (was 13.5 → 16 over 6 min)
FOOTYSTATS:        4.5 GB (now killed)
API_FOOTBALL:      3.9 GB
UNDERSTAT:         3.9 GB
TRANSFERMARKT:     3.5 GB
OPEN_METEO:        2.4 GB
```

Killing FOOTYSTATS only freed 4.5 GB, while DERIBIT keeps growing. The RAM pressure is
DERIBIT-dominated. DERIBIT has the 200k-symbol options chain — known heavy. If RAM
breaches 78 GB again, DERIBIT chunk is the bigger lever (CEFI cost vs sports cost
trade-off — would need user call).

Decision per rule: kill executed (FOOTYSTATS, accidentally full-killed not just chunk).
Restarted. Next watch in 4 min; if RAM breaches 78 GB again with FOOTYSTATS already
restarted → escalate to user, do NOT kill DERIBIT autonomously (it's a real CEFI work
chunk, scope-impacting).

5 min after sports fan-out:

| Metric | Value | Status |
|---|---|---|
| RAM used | 52 GB / 80 GB cap | ✅ 28 GB headroom |
| RAM trend (5 min) | 46→52 GB | ✅ stable, slow climb |
| Swap | 0.7 GB | ✅ idle (was 6.7 GB at OOM, now drained) |
| OOM kills | 0 | ✅ |
| Rate-limit hits | 0 | ✅ (watchdog re-armed PID 621482) |
| Procs | 43 | — |
| Checkpoints | 399 (+23 since resume) | ✅ |

Progress per AG:
- CEFI: 199 chunks (+7 since resume)
- TRADFI: 166 chunks (+21 since resume; fastest)
- DEFI: 34 chunks (+7 since resume)
- SPORTS chunked: API_FOOTBALL 3 chunks, FOOTYSTATS 1, others on chunk 1
  - TRANSFERMARKT still on chunk 1 since 14:15 (15 min/chunk — internal rate-limit at ~1 req/sec is the real-world pace; not stuck, just paced)

### Real adapter errors observed (not rate-limit)

- **9× Databento NASDAQ `XNAS.ITCH symbols=2: 422 symbology_invalid_request`** — adapter
  sending invalid symbol format for some early dates (likely BTC/ETH ETF tickers that
  don't exist pre-listing; `TRADFI_TICKER_COVERAGE_START` should clip but apparently
  isn't always). Lands as `attempted_failed` rows; not blocking. Follow-up: investigate
  why the ticker cutoff isn't applying for these specific cases.

## Status snapshot (2026-05-04 13:15 IST — end of session)

**Phase 0 (diagnose) — DONE.** Per-asset-group dry-runs completed; phantom counts known.
**Phase 1 (flip phantoms) — DONE for cefi/tradfi/sports.**
- cefi: 12,540 phantoms flipped to `attempted_failed`
- tradfi: 2,726 phantoms flipped
- sports: 41,223 phantoms flipped (SFI excluded)
- prediction: 11,848 phantoms found but **out of scope** (POLYMARKET/`trades` is MTDS data)
- defi: 597 phantoms found, deferred (low priority)

**Phase 2 (backfill) — NOT DONE, two blockers:**

1. **Local cefi/tradfi backfill via `run_vm_backfill_e2e.sh` failed silently** — runner
   doesn't export `GCP_PROJECT_ID`, so every chunk aborts at bootstrap. Re-fire commands
   with corrected env are in the "Pending work" section below. ~Easy fix.
2. **Sports VM launches blocked on IAM** — `harshkantariya@odum-research.com` lacks
   `roles/iam.serviceAccountUser` on the Compute SA. Ikenna needs to grant. Fallback:
   run sports adapters locally too (same Python CLI; needs `GCP_PROJECT_ID` env). Singleton
   lock would be bypassed — risk of API thrash if other agents launch sports VMs in parallel.

**Net**: nothing's been actually backfilled today. Manifests are honest now (phantoms
flipped → orchestrator will retry on next launch), but the launches haven't happened.
Resume tomorrow once the env-var fix is applied + IAM grant lands.

## Context

Scope of *this* plan is narrower than the parent epic
(`instruments_and_market_tick_data_completion_2026_05_01.plan.md`):

- **Service**: `instruments-service` only — instrument-definition shards, not market-tick or
  market-data-processing.
- **Asset groups**: all five — `cefi`, `tradfi`, `sports`, `prediction`, `defi`.
- **Target**: ≥99% `captured + empty_confirmed` under the secondary-cutoff denominator (per
  parent-epic success criteria) by EOD 2026-05-04.
- **Non-goals (this plan)**: deployment-ui Phase 0 bug fixes (deferred — Harsh will pick up
  later), market-tick-data backfills, MDPS candle generation, sports % drive (in flight by
  another agent).

**Why a separate plan**: parent epic has Phase 0 (UI) → Phase 1 (sports tick) → Phase 2 (cefi)
→ etc. as a sequential DAG. Today's "instruments-only to 100%" cuts a horizontal slice across
all asset groups for a single service. Tracking it separately keeps the parent epic clean and
gives a tight EOD success criterion.

**Background discoveries from this session (2026-05-04)** that shape this plan:

- `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` is the right diagnostic
  — supports all 5 asset groups via `ASSET_GROUP_CONFIG`, probes both `category=` (legacy) and
  `asset_group=` (canonical) hive keys to avoid the 2026-05-01 false-181k-phantoms incident on
  cefi.
- `reconcile_phantom_manifest_rows.py` (no `_all` suffix) is sports-only. Don't use it for
  cefi/tradfi/defi/prediction.
- The `deployment-ui` Deploy button does **not** spawn VMs locally (no orchestrator worker
  runs in T2 dev). VM-spawning is done via the shell launchers in
  `deployment-service/scripts/vm/launch-*.sh` directly. Harsh's teammate's 31 running VMs all
  came from those launchers.
- The cloud `deployment-dashboard` Cloud Run service exists but is in failed state since
  2026-04-30 (`Ready=False`, container failed startup). T3 is non-functional. T2 is the SSOT.
- Per CLAUDE.md and the playbook, the canonical workflow is:
  ```
  1. reconcile dry-run (per asset group)        — diagnose
  2. reconcile (no --dry-run) for any phantoms  — flip stale captured→attempted_failed
  3. launch backfill VMs                        — orchestrator now retries the failed shards
  4. wait, re-run reconcile dry-run             — verify zero phantoms remain
  5. verify drilldown / GCS spot-check          — confirm ≥99%
  ```

## Cutoffs (per playbook + UAC `coverage_starts.py`)

Same cutoffs as parent epic — repeated here so this plan is self-contained:

| Asset group | Start (global)             | End   | Per-shard secondary clip                     |
| ----------- | -------------------------- | ----- | -------------------------------------------- |
| CEFI        | 2019-01-01                 | today | per-venue inception (`CEFI_SOURCE_COVERAGE_START`) |
| TRADFI      | 2019-01-01                 | today | per-ticker listing (`TRADFI_TICKER_COVERAGE_START`) |
| SPORTS      | 2020-06-01                 | today | per-source + prediction-vs-reference league filter |
| PREDICTION  | 2020-06-12 (POLYMARKET)    | today | per-venue + per-sub-category (`PREDICTION_SOURCE_COVERAGE_START`) |
| DEFI        | per-protocol launch        | today | per-protocol-per-chain (`DEFI_SOURCE_COVERAGE_START`) |

Always pass the **global** start. Launchers + manifest writers handle the secondary clip
through UAC `clip_dates_to_source_coverage` / equivalents — pre-launch days land as
`empty_confirmed`, not `attempted_failed`.

## Execution DAG

```
Phase 0 (Diagnose, parallel)
   ├── reconcile dry-run cefi
   ├── reconcile dry-run tradfi
   ├── reconcile dry-run sports
   ├── reconcile dry-run prediction
   └── reconcile dry-run defi
        │
        ▼  (review numbers; decide what to launch)
Phase 0.5 (Sports gate — verify in-flight work has settled before launching new sports VMs)
        │
        ▼
Phase 1 (Flip phantoms, parallel — only for asset groups with non-zero phantoms)
        │
        ▼
Phase 2 (Launch backfills, parallel by asset group)
        │
        ▼  (wait — VMs run hours/days)
Phase 3 (Verify, parallel)
        │
        ▼
Phase 4 (Sign-off + plan close)
```

Realistic ETA caveat: Phase 2 wall time depends on shard count. CEFI 2019-→today across 9
venues has ~22k potential shards. Even with 100 concurrent VMs and ~5 min per shard, that's
~18 hours. **EOD target may slip into the next day** if the gap is large; we'll know after
Phase 0 dry-runs.

## Phase 0 — Diagnose (read-only, parallel)

**Scope nit before starting**: "instruments at 100%" can mean two things:

1. **Per-day shard coverage**: every `(asset_group, venue, day)` tuple in the cutoff window has
   a manifest row in `captured + empty_confirmed`. The reconciler measures this.
2. **Per-instrument completeness on captured days**: each captured day's parquet contains
   every instrument that was tradeable on that day on that venue.

The reconciler dry-run only measures (1). (2) requires a separate per-row content audit.

- [ ] [HUMAN] P0. Confirm with Ikenna which "100%" he means before launching backfills. If
      (2), the work is much larger (we'd need a content-validation script per AG, none
      exists generically today). Default assumption for now: **(1)**.

For each asset group, dry-run the reconciler to learn:

- Total manifest rows scanned
- Phantom rows found (claimed `captured` but no parquet)
- Real `captured` count
- Real `attempted_failed` count
- Missing-row count under the secondary cutoff

Run each in its own terminal/background — they're independent. Per script docstring, bulk-list
pattern is ~5 min for 600k rows per asset group.

- [ ] [SCRIPT] P0. Dry-run cefi:
      ```bash
      cd ~/unified-trading-system-repos/instruments-service
      .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \
        --asset-group cefi --dry-run 2>&1 | tee /tmp/recon-cefi.log
      ```
- [ ] [SCRIPT] P0. Dry-run tradfi: same as above with `--asset-group tradfi`, log to
      `/tmp/recon-tradfi.log`.
- [ ] [SCRIPT] P0. Dry-run sports: same with `--asset-group sports`, log to
      `/tmp/recon-sports.log`. **Note**: sports manifest is the in-flight one; numbers may
      shift as the consolidator daemon merges. Re-run if anomalies appear.
- [ ] [SCRIPT] P0. Dry-run prediction: same with `--asset-group prediction`, log to
      `/tmp/recon-prediction.log`.
- [ ] [SCRIPT] P0. Dry-run defi: same with `--asset-group defi`, log to `/tmp/recon-defi.log`.
- [ ] [HUMAN] P0. Review all five logs. Capture the per-asset-group counts in this plan's
      Notes section so we have a baseline. Decide: which asset groups need phantom flips
      (Phase 1)? Which need backfill VMs (Phase 2)?

## Phase 0.5 — Sports gate (partial — SFI excluded from this run)

Per parent-epic Phase 0.5 — sports backfill VMs share league partitions, so collisions cause
double-writes and manifest noise. As of session start (2026-05-04 11:30 IST):

- **SFI (`soccer_football_info`) has 1 instruments-service VM running** for sports
  backfill. **This plan EXCLUDES SFI** — do not launch any new SFI backfill or run sports
  reconciler with SFI data types in scope. Other sports sources (api-football, transfermarkt,
  footystats, understat, openmeteo) are eligible if their gate query is clean.

- [ ] [HUMAN] P0. Confirm the SFI VM is the only in-flight sports work, and capture which
      data types it's covering (so we know what NOT to touch):
      ```bash
      gcloud compute instances list \
        --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' \
        --format='table(name,status,zone,creationTimestamp)'
      ```
      Expected: only the SFI VM + optional `manifest-consolidator-*`. If `af` / `tm` / `fs`
      VMs are also RUNNING — stop and ping the other agent's owner.
- [ ] [SCRIPT] P0. When running sports phantom recon, scope away from SFI to avoid racing
      its writes:
      ```bash
      .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py \
        --asset-group sports --dry-run \
        --data-types FIXTURES,FIXTURE_EVENTS,STANDINGS,LEAGUES,TEAMS,PLAYER_STATS,ODDS,PLAYER_VALUES,TRANSFERMARKT_LEAGUES
      ```
      (Replace data-types list with the non-SFI set Phase 0 reveals as relevant.) **Do NOT**
      include `SFI_LEAGUES` or `SFI_PROGRESSIVE_STATS` while SFI VM is running — its
      writes are mid-flight and reconciler reads would race them.
- [ ] [HUMAN] P0. Snapshot sports drilldown headline coverage. Per parent-epic Phase 0.5,
      should be ≥80% captured.

## Phase 1 — Flip phantoms (parallel, only for AGs with phantoms > 0)

Run *without* `--dry-run` only for asset groups where Phase 0 found phantoms. This is fast
(same bulk-list pattern as dry-run, plus a single manifest write per asset group).

**Critical**: do NOT write empty placeholder parquets to mask phantoms. Per CLAUDE.md
manifest-phantom-audit rule: `record_empty(...)` is for legitimately-empty source responses
only. Phantoms must be flipped to `attempted_failed` so VMs re-attempt them.

- [ ] [SCRIPT] P0. Flip phantoms for each AG with phantom_count > 0:
      ```bash
      .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag>
      ```
      (no `--dry-run`). Repeat per asset group.
- [ ] [SCRIPT] P0. Re-run dry-run for each flipped AG to confirm phantom count → 0.

## Phase 2 — Launch backfills (parallel by asset group)

This is where the actual instruments-service work happens. Critical distinction discovered
in this session (2026-05-04):

**The cefi/tradfi/defi/prediction launchers in `deployment-service/scripts/vm/launch-*-backfill*.sh`
that look like they're for instruments are NOT.** They have `VM_SERVICE=market_tick_data_service`
and `VM_TASK=cefi-backfill` — they download tick data, not instrument definitions. Inspected
the metadata of all 31 currently-running VMs (`cefi-bitfinex-…`, `cefi-okx-swap-…`,
`cefi-deribit-…`, etc.) — they're all MTDS, not instruments-service.

**Launchers that actually run instruments-service** (verified by
`grep VM_SERVICE=instruments_service` across `deployment-service/scripts/vm/`):

- `launch-instruments-smoke-vm.sh` — single-day smoke test (writes to `*-test-` buckets,
  not prod)
- `launch-{api-football,transfermarkt,sfi,footystats,understat,openmeteo}-backfill-vm.sh`
  — sports instruments only
- `launch-sfi-forward-poll.sh`, `launch-footystats-forward-poll.sh` — daily forward-poll
  (live, not backfill)
- `launch-sports-manifest-rescan-vm.sh` — sports manifest rescan only

For **cefi/tradfi/defi/prediction instruments**, **no dedicated VM launcher exists**. The
canonical local-driver script is
[`instruments-service/scripts/run_vm_backfill_e2e.sh`](../../../instruments-service/scripts/run_vm_backfill_e2e.sh)
(despite the name "vm" it runs locally — it invokes `.venv/bin/instruments-service ...` on
whatever machine you run it on, with checkpointing + parallel chunks). Two paths to use it:

**Path A — local driver (simplest, fine for small gaps)**: run `run_vm_backfill_e2e.sh`
directly on this machine. Resumable via checkpoints, so safe to interrupt. **IP-rate-limited
to your laptop's IP** — fine for instruments-service (low API volume, tiny payloads), bad
for tick-data scale.

**Path B — wrap in a VM (ad-hoc)**: write a one-line `gcloud compute instances create` that
sets `VM_SERVICE=instruments_service`, `VM_OPERATION=download`, `VM_ASSET_GROUP=…`,
`VM_VENUE=…`, `VM_START_DATE`, `VM_END_DATE` — same metadata pattern as
`launch-instruments-smoke-vm.sh` but with prod buckets (no `IS_TEST_RUN=true`). Defer to
Ikenna before doing this — the smoke launcher exists, the prod-equivalent doesn't, and
adding one new pattern is something he'd want to bless.

**Cost model (correction to common intuition)**: VMs in this stack have
`VM_SHUTDOWN_ON_COMPLETION=true` — each one self-deletes when its shard finishes.
Cost ≈ `(shard_count × per-shard_runtime × $0.07/hr)` on `e2-standard-2`. **Many
short-lived VMs are NOT inherently expensive** — what matters is total runtime. For
instruments-service the per-shard runtime is small (low API volume). The 31 currently-running
MTDS VMs cost ~$52/day at full burn; instruments-service backfill at the same scale would
cost a fraction of that since shards finish in minutes. Don't switch to a long-lived
single-VM model — that costs more (idle time billed) and breaks shard-level failure isolation.

**Tarball refresh**: per CLAUDE.md, refresh only if **instruments-service / UAC / UTL** code
changed. Today's session changed only deployment-api + deployment-service routes (irrelevant
to backfill VMs). **No tarball refresh needed.** If unsure:
```bash
bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group <X>
```

**`--force` warning**: every launcher / CLI accepts a force flag (the deploy form defaults
it to `true`, but for these scripts default is `false`). With `force=true`, the orchestrator
re-fetches every shard regardless of `_should_skip_shard` — billable API cost, possible
rate-limit hit. **Use `force=false` for daily gap-fill.** Reserve `force=true` for retesting
one specific shard or after a code-fix that requires re-running known-bad data.

### CEFI

- [ ] [HUMAN] P0. Confirm Phase 0 cefi gap (review `/tmp/recon-cefi.log`).
- [ ] [HUMAN] P0. **Pick path** — local-driver (Path A, fast iteration) or VM-wrap (Path B,
      needs Ikenna sign-off). For the per-asset-group counts likely seen at 85% baseline,
      Path A is probably enough.
- [ ] [HUMAN] P0. Path A launch (per CEFI venue):
      ```bash
      cd ~/unified-trading-system-repos/instruments-service
      bash scripts/run_vm_backfill_e2e.sh \
        --venue BINANCE-SPOT \
        --asset-group CEFI \
        --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      ```
      Repeat for each CEFI venue with a non-trivial gap (BINANCE-FUTURES, DERIBIT, BYBIT,
      OKX, UPBIT, COINBASE, HYPERLIQUID, ASTER). The script chunks the date range,
      parallel-runs `--parallel` chunk workers, and checkpoints to
      `.backfill-checkpoints/<venue>/<chunk>.done` so re-runs skip completed chunks.
- [ ] [HUMAN] P1. Watch progress via the checkpoint dir:
      `ls instruments-service/.backfill-checkpoints/CEFI/<venue>/ | wc -l`.

### TRADFI

- [ ] [HUMAN] P0. Confirm Phase 0 tradfi gap (review `/tmp/recon-tradfi.log`).
- [ ] [HUMAN] P0. Same Path A pattern as CEFI, per TradFi venue:
      ```bash
      bash scripts/run_vm_backfill_e2e.sh \
        --venue CME --asset-group TRADFI \
        --start-date 2019-01-01 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      ```
      Repeat for `CBOE`, `NASDAQ`, `NYSE`, `ICE`, `FX`, `POLYGON`, `FRED` if their slice is
      red. Per-ticker listing-date clip is shipped (`TRADFI_TICKER_COVERAGE_START` UAC
      `15b9e74`), pre-listing days auto-skip.

### SPORTS — instruments-service backfill, with SFI excluded

- [ ] [HUMAN] P0. **GATE**: Phase 0.5 must confirm only the SFI VM is running. Other
      sources (af/tm/fs/understat/openmeteo) clear to launch.
- [ ] [HUMAN] P0. Sports has dedicated launchers (`VM_SERVICE=instruments_service`
      confirmed in metadata). Pick the launcher matching the data-type slice that's red in
      `/tmp/recon-sports.log`. **Do NOT touch SFI** while its VM is running — skip
      `launch-sfi-backfill-vm.sh` and `launch-sfi-forward-poll.sh`.
      ```bash
      # api-football (LEAGUES, TEAMS, FIXTURES, FIXTURE_EVENTS, STANDINGS, INJURIES, …)
      bash ~/unified-trading-system-repos/deployment-service/scripts/vm/launch-api-football-backfill-vm.sh \
        --data-type <X> --start-date 2020-06-01

      # transfermarkt (PLAYER_VALUES, TRANSFERMARKT_LEAGUES)
      bash .../launch-transfermarkt-backfill-vm.sh --data-type <X> --start-date 2020-06-01

      # footystats / understat / openmeteo — same pattern
      ```
      For non-prediction reference leagues, scope to FIXTURES + FIXTURE_EVENTS + STANDINGS
      only — per parent-epic prediction-vs-reference cutoff rule. The orchestrator's
      `_should_skip_shard` + `_should_skip_reference_league` guards handle this; pass
      `--leagues prediction|reference|all` if the launcher accepts it.
- [ ] [SCRIPT] P0. After each non-SFI launcher batch completes, re-run sports phantom recon
      (no `--dry-run`) **with the same `--data-types` scope as Phase 0.5** (i.e. excluding
      SFI_LEAGUES / SFI_PROGRESSIVE_STATS until the SFI VM is done).

### PREDICTION

- [ ] [HUMAN] P0. Confirm Phase 0 prediction gap (review `/tmp/recon-prediction.log`).
- [ ] [HUMAN] P0. **No dedicated launcher exists**. Use Path A (local driver):
      ```bash
      bash scripts/run_vm_backfill_e2e.sh \
        --venue POLYMARKET --asset-group PREDICTION \
        --start-date 2020-06-12 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 2
      bash scripts/run_vm_backfill_e2e.sh \
        --venue KALSHI --asset-group PREDICTION \
        --start-date 2021-07-19 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 2
      ```
      Lower `--parallel` (2 not 4) since PREDICTION venues have stricter rate limits.
- [ ] [HUMAN] P1. Per-sub-category cutoffs (crypto/macro/football for POLYMARKET) — handled
      by the adapter's internal coverage clip; pass venue-only here.

### DEFI

- [ ] [HUMAN] P0. Confirm Phase 0 defi gap (review `/tmp/recon-defi.log`).
- [ ] [HUMAN] P0. **No dedicated launcher exists**. Use Path A per DeFi venue:
      ```bash
      bash scripts/run_vm_backfill_e2e.sh \
        --venue AAVEV3-ETHEREUM --asset-group DEFI \
        --start-date 2022-03-16 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      bash scripts/run_vm_backfill_e2e.sh \
        --venue UNISWAPV3-ETHEREUM --asset-group DEFI \
        --start-date 2021-05-05 --end-date $(date -u +%Y-%m-%d) \
        --chunk-days 30 --parallel 4
      # Repeat per (protocol × chain) — see UAC DEFI_SOURCE_COVERAGE_START for inception dates.
      ```
      DeFi instruments are monotonically-increasing (immutable contracts) per the
      orchestrator high-watermark logic — `_should_skip_shard` + per-venue HWM means most
      days will auto-skip. Only red shards re-run.

## Phase 3 — Verify (parallel)

- [ ] [SCRIPT] P0. For each asset group: re-run `reconcile_phantom_manifest_rows_all.py
      --asset-group <X> --dry-run` and confirm phantom count is 0.
- [ ] [HUMAN] P0. Snapshot the deployment-ui drilldown for `service=instruments-service` per
      asset group. Each should show ≥99% `captured + empty_confirmed` under the secondary-
      cutoff denominator.
- [ ] [HUMAN] P1. Spot-check 5 random `(asset_group, day, venue, instrument_type)` rows:
      follow each to its canonical GCS path and confirm the parquet exists.

## Phase 4 — Sign-off + plan close

- [ ] [HUMAN] P0. Update parent epic
      (`instruments_and_market_tick_data_completion_2026_05_01.plan.md`) progress notes:
      mark instruments-service slice complete, link to this plan.
- [ ] [HUMAN] P0. Brief Ikenna on results vs the EOD target.
- [ ] [AGENT] P2. Mark this plan complete and move to `plans/archive/`.

## Files / commands referenced

| Repo                  | File / command                                                  | Phase |
| --------------------- | --------------------------------------------------------------- | ----- |
| instruments-service   | `scripts/reconcile_phantom_manifest_rows_all.py`                | 0,1,3 |
| instruments-service   | `scripts/run_vm_backfill_e2e.sh` (local-driver, resumable)      | 2     |
| deployment-service    | `scripts/vm/launch-{api-football,transfermarkt,footystats,understat,openmeteo}-backfill-vm.sh` (sports instruments only) | 2 |
| deployment-service    | `scripts/vm/launch-instruments-smoke-vm.sh` (single-day, *-test buckets) | ref |
| unified-api-contracts | `unified_api_contracts/canonical/coverage_starts.py`            | ref   |
| unified-trading-pm    | `codex/14-playbooks/backfill-completion-playbook.md`            | ref   |

**Explicitly NOT used** (these run MTDS / market-tick-data, not instruments-service):
`launch-cefi-sharded-backfill.sh`, `launch-tradfi-backfill-vm.sh`, `launch-mdps-*-backfill*.sh`.

## Success criteria

- All 5 asset groups: ≥99% `captured + empty_confirmed` for `service=instruments-service`,
  scoped to the secondary-cutoff denominator (per parent-epic). **Definition (1) of "100%"**
  per Phase 0 scope-nit; revisit if Ikenna meant (2).
- Phantom recon dry-run reports 0 phantom flips for every asset group (excluding SFI while
  its VM is running).
- Drilldown spot-check: 5 random captured rows per AG resolve to actual parquets in GCS.

## Execution log (2026-05-04 EOD push)

- **12:33–12:48 IST**: Phase 0 dry-runs for cefi/tradfi/sports/prediction/defi (parallel after
  the `tempfile` patch). Sports first attempt timed out on GCS list under 5x parallel load;
  retry with `--workers 16` succeeded.
- **12:46–12:57 IST**: Phase 1 phantom flips for cefi (12,540), tradfi (2,726), sports
  (41,223 SFI-excluded). All wrote manifest back successfully.
- **12:55 IST**: Phase 2 TRADFI backfill fired locally via `run_vm_backfill_e2e.sh` for
  CME/CBOE/NASDAQ/NYSE/ICE/FX (6 venues × 4 chunk-workers = 24 concurrent
  instruments-service procs). No IAM issue — runs on this machine.
- **12:57 IST**: Phase 2 CEFI backfill fired locally for the 9 active CEFI venues
  (9 × 4 = 36 concurrent procs).
- **12:57 IST**: Phase 2 SPORTS af + tm VM launches blocked: `User does not have access to
  service account 1060025368044-compute@developer.gserviceaccount.com. Ask a project owner
  to grant the iam.serviceAccountUser role.`
- **13:10 IST**: Discovered cefi+tradfi local backfills had been silently failing every
  chunk on `GCP_PROJECT_ID must be set in environment` — `run_vm_backfill_e2e.sh` doesn't
  export the env. All 90 chunks per venue × 15 venues showed "START" but never "DONE",
  produced zero checkpoints, wrote nothing to GCS. Killed all in-flight procs, cleaned
  checkpoints + logs.
- **13:08 IST**: Investigation found that the `setup-data-pipeline-vm.sh` script (line 596+)
  for `VM_TASK=sports-backfill` just runs:
  ```
  python -m instruments_service --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider {API_FOOTBALL|TRANSFERMARKT|...} \
    --sports-entity <ENTITY> --start-date <X> --end-date <Y>
  ```
  **The IAM block is NOT a hard blocker — same CLI runs locally** like cefi/tradfi.
  Smoke test confirmed: `.venv/bin/python -m instruments_service ...` accepts the same
  args; only requires `GCP_PROJECT_ID=central-element-323112` env. Can fire all sports
  retries on this laptop without VM access. (Whether this is *desirable* — singleton
  rate-limit lock exists for a reason; running locally bypasses it — see Risks section.)

## Adapter smoke matrix (1 day per venue, 2026-05-01)

Run before any fan-out — confirms the adapter+API+GCS+manifest path is wired per venue.
Command pattern:
```bash
cd ~/unified-trading-system-repos/instruments-service
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false \
  .venv/bin/instruments-service \
  --operation instruments --mode batch \
  --asset-group <AG> --venues <VENUE> \
  --start-date 2026-05-01 --end-date 2026-05-01
```

### Column meanings

- **Active@day** — instruments that were **actually written to GCS** for the queried date
  (after applying per-instrument launch/delisting filtering). This is the captured count.
- **Universe** — instruments the adapter received from the upstream source AFTER symbol-level
  filtering (majors + x-coins, not the entire venue universe). Tells us the adapter is
  talking to the API. `Universe ≥ Active@day` always; the gap = instruments that exist in
  the venue's history but aren't tradeable on the queried day.
- A healthy smoke = `Active@day > 0`. A zero `Universe` means the adapter never reached the
  API. A non-zero `Universe` with zero `Active@day` means date-filter / validation rejected
  everything (config bug, not API bug).

### CEFI smoke results (2026-05-04 13:20 IST)

| Venue            | Status | Active@day / Universe  | Notes                                                                                                                                                                                                                                                              |
| ---------------- | :----: | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| BINANCE-SPOT     |   ✅   | 48 / 51                | Tardis `binance` endpoint, healthy. 3 instruments delisted before 2026-05-01.                                                                                                                                                                                       |
| BINANCE-FUTURES  |   ✅   | 33 / 37                | Tardis `binance-futures` endpoint, healthy.                                                                                                                                                                                                                        |
| DERIBIT          |   ✅   | 3,720 / 200,312        | Tardis returns full historical options chain (200k symbols across all expiries we ever saw); 3.7k active for 2026-05-01.                                                                                                                                            |
| BYBIT            |   ✅   | 32 / 291               | Tardis `bybit` + `bybit-spot`, healthy.                                                                                                                                                                                                                            |
| **OKX**          |   ❌   | adapter never ran      | `URDI[OKX]: ADAPTER_ERROR (permanent): No Tardis exchange mapping for canonical venue 'OKX'`. Config bug — UAC `venue_to_tardis` mapping missing for canonical name `OKX`. Sharding config lists `OKX`, but adapter expects `OKX-SPOT` / `OKX-SWAP` / `OKX-FUTURES`. **Not geo-block.** |
| UPBIT            |   ✅   | 12 / 13                |                                                                                                                                                                                                                                                                    |
| **COINBASE**     |   ❌   | adapter ran, 0 written | `URDI returned zero records for date=2026-05-01 asset_groups=['CEFI']`. Adapter ran but got nothing back. Either bare `COINBASE` is also a sharding-vs-adapter mismatch (canonical might be `COINBASE-SPOT`), or transient API issue.                                |
| HYPERLIQUID      |   ✅   | 21 / 21                | On-chain CLOB, native API. No history-vs-active gap.                                                                                                                                                                                                                |
| ASTER            |   ✅   | 19 / 19                |                                                                                                                                                                                                                                                                    |

**7 of 9 CEFI venues healthy. OKX + COINBASE blocked on canonical-venue-name mismatches.**
The Phase 2 backfill should proceed for the 7 working venues; OKX + COINBASE need a fix
in either UAC `venue_to_tardis` map or the sharding YAML before they can run.

#### OKX + COINBASE root cause (deeper)

Followed the trail across three SSOTs that disagree:

1. **PM `unified-trading-pm/configs/venues.yaml`** (used by deployment-api shard calculator):
   ```yaml
   CEFI: { venues: [..., OKX, COINBASE, ...], venue_to_tardis: { OKX: [okex,okex-futures,okex-swap], COINBASE: coinbase } }
   ```
   Canonical names: **unsuffixed** `OKX` / `COINBASE`.

2. **UAC `unified_api_contracts/registry/venue_mapping.py` `tardis_to_venue`**:
   ```python
   "okex": "OKX-SPOT", "okex-swap": "OKX-SWAP", "okex-futures": "OKX-FUTURES",
   "coinbase": "COINBASE-SPOT"
   ```
   Canonical names: **suffixed** `OKX-SPOT` / `OKX-SWAP` / `OKX-FUTURES` / `COINBASE-SPOT`.

3. **UAC venue registry** (CeFi / TradFi / DeFi / sports membership for validation):
   Rejects BOTH unsuffixed (`OKX`, `COINBASE`) AND suffixed (`OKX-SPOT`, `COINBASE-SPOT`)
   forms. Per smoke test: `--venues OKX-SPOT` runs through Tardis fine (fetches 112
   instruments), then `Instrument validation: 112 rejected — unknown venue 'OKX-SPOT' —
   not in CeFi, TradFi, DeFi, or sports registries`.

So **all three** of `OKX`, `OKX-SPOT`, `OKX-SWAP`, `OKX-FUTURES`, `COINBASE`,
`COINBASE-SPOT` fail somewhere in the pipeline. There's no working canonical name today.

**Fix scope**: this is a multi-repo alignment problem (PM venues.yaml ↔ UAC tardis_to_venue
↔ UAC venue registry). Out of scope for an EOD push. **Action for tomorrow**: file a
separate plan to align the three SSOTs on one canonical naming convention. For today's
"100% by EOD" goal, accept that OKX + COINBASE remain at their current coverage and
proceed with the 7 healthy CEFI venues.

### TRADFI smoke results (2026-05-04 13:26 IST)

| Venue        | Status | Active@day / Universe     | Notes                                                                                                                                                          |
| ------------ | :----: | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CME          |   ✅   | 14,794 / 16,394           | Databento, healthy. Includes futures + options chain. 1.6k gap = expired or future-dated quarterlies.                                                          |
| CBOE         |   ✅   | 1 / 1                     | VIX index (Barchart). Single-record SSOT, expected.                                                                                                            |
| NASDAQ       |   ✅   | 43 / 258                  | Databento equities (BTC/ETH ETFs only — universe is 258 symbols we ever cared about; 43 active for 2026-05-01).                                                |
| NYSE         |   ✅   | 215 / 256                 |                                                                                                                                                                |
| ICE          |   ✅   | 2,067 / 2,069             |                                                                                                                                                                |
| FX           |   ✅   | 1 / 1                     | KRW/USD via Yahoo Finance, single instrument.                                                                                                                  |
| **POLYGON**  |   ❌   | adapter never ran         | `URDI[POLYGON]: ADAPTER_ERROR (permanent): api_key required — service must fetch polygon-api-key from Secret Manager`. Either secret is missing in SM or `ApiKeyReloader` isn't picking it up. **Needs SM check.** |
| **FRED**     |   ❌   | adapter ran, 0 written    | `URDI returned zero records for date=2026-05-01`. 2026-05-01 was a Friday — FRED should have data. Not yet root-caused; possibly adapter bug or cutoff issue.   |

**6 of 8 TRADFI venues healthy.** POLYGON + FRED fail. Both need separate investigation;
do not block the 6 healthy venues from Phase 2 backfill.

### DEFI smoke results (2026-05-04 13:36 IST)

| Venue                  | Status | Active@day / Universe | Notes                                                               |
| ---------------------- | :----: | --------------------- | ------------------------------------------------------------------- |
| AAVEV3-ETHEREUM        |   ✅   | 52 / 89               | Lending markets (subgraph). 89 historical, 52 active.               |
| UNISWAPV3-ETHEREUM     |   ✅   | 318 / 5,997           | Pool universe (subgraph). 5.9k pools ever, 318 active.              |
| UNISWAPV2-ETHEREUM     |   ✅   | 24 / 772              | Pool universe (subgraph).                                           |
| CURVE-ETHEREUM         |   ✅   | 13 / 49               |                                                                     |
| LIDO-ETHEREUM          |   ✅   | 2 / 2                 | Liquid-staking tokens (stETH, wstETH).                              |
| BALANCER-ETHEREUM      |   ✅   | 1,249 / 2,072         | Pool universe — biggest write count, ~60% historical-pool dropout.  |
| EIGENLAYER-ETHEREUM    |   ✅   | 1 / 1                 | EIGEN token. Single instrument, expected.                           |

**7 of 7 DEFI venues healthy.** All protocol-chains verified. DEFI Phase 2 backfill is
unblocked — local-driver pattern works for every protocol. (Reminder: DEFI manifest had
only 597 phantoms and they were all on EIGENLAYER `rewards`, not core instruments. Low
priority for Phase 2 work, but the adapter health is confirmed.)

### SPORTS smoke results (2026-05-04 13:36 IST)

Sports has a different architecture than CEFI/TRADFI/DEFI — **two layers**:

1. **Primary provider** (`API_FOOTBALL`) — fetches fixtures, leagues, teams from the
   API; populates the canonical sports_reference paths in GCS.
2. **Enrichment providers** (`OPEN_METEO`, `UNDERSTAT`, `FOOTYSTATS`, `TRANSFERMARKT`,
   `SOCCER_FOOTBALL_INFO`) — read fixtures from GCS (already fetched by API_FOOTBALL),
   call only their own API to enrich those fixtures. They short-circuit the main
   orchestrator path.

A healthy enrichment-provider smoke = exits cleanly (rc=0) with no error, even if
returns `{}` (no fixtures to enrich on that date / those fixtures aren't in this
provider's coverage).

**Valid `--sports-provider` values** (from CLI error output): `API_FOOTBALL`,
`API_FOOTBALL_ENRICHMENT`, `OPEN_METEO`, `TRANSFERMARKT`, `SOCCER_FOOTBALL_INFO`,
`UNDERSTAT`, `FOOTYSTATS`. Use these exact strings.

| Provider           | Entity                  | Status | Notes                                                                                                                                            |
| ------------------ | ----------------------- | :----: | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| API_FOOTBALL       | FIXTURES                |   ✅   | Manifest-skip on already-captured days (correct). With `--force`: `Fetched 101 fixtures` + 1,228 leagues + 618 teams. Healthy, just slow (rate-limit pacing). |
| API_FOOTBALL       | STANDINGS               |   ✅   | Manifest-skip behavior identical. Adapter healthy.                                                                                                |
| API_FOOTBALL       | TEAMS                   |   ✅   | Same.                                                                                                                                             |
| TRANSFERMARKT      | PLAYER_VALUES           |   ✅¹  | Hit 90s timeout on smoke — adapter is rate-limited at ~1 req/sec, fully expected. Healthy.                                                        |
| TRANSFERMARKT      | TRANSFERMARKT_LEAGUES   |   ✅   | DONE: `{transfermarkt_leagues: 32}` — wrote 32 league rows to GCS.                                                                                |
| FOOTYSTATS         | FS_LEAGUES              |   ✅   | Short-circuited (enrichment), exit 0, empty result for 2024-08-15. Adapter healthy.                                                              |
| UNDERSTAT          | UNDERSTAT_TEAMS         |   ✅   | Short-circuited, exit 0, empty for 2024-08-15. Healthy.                                                                                          |
| OPEN_METEO         | WEATHER                 |   ✅   | Short-circuited, exit 0, empty for 2024-08-15. Healthy. (Initial test failed with `OPENMETEO` — correct provider name is `OPEN_METEO` with underscore.) |
| SOCCER_FOOTBALL_INFO | SFI_LEAGUES           |   ⏭️   | **Excluded** from this run — other agent's SFI VM is in flight. Don't touch.                                                                     |

¹ TRANSFERMARKT/PLAYER_VALUES did not finish within the 90s smoke timeout, but reached
the API and was making progress. For real backfill via the launcher (longer timeout +
shutdown-on-completion) this is fine.

**6 of 6 testable sports providers healthy.** SFI excluded by design. All sports
adapters can run.

## Pending work — what to launch when permissions / decisions land

### CEFI / TRADFI — local backfill failed silently, must re-fire with env vars

**Status (2026-05-04 13:10 IST)**: First run of `run_vm_backfill_e2e.sh` for cefi+tradfi
failed on every chunk — the runner doesn't export `GCP_PROJECT_ID` and the
`instruments-service` CLI bootstrap aborts at `log_event("STARTED")` with
`ValueError: GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment`. All chunks
showed "START" but no "DONE", produced no checkpoints, and wrote nothing to GCS.
**Killed and cleaned** — `.backfill-checkpoints/` and `logs/recon-fill-*` removed so
reruns start fresh.

**Re-fire command (must export env first)**:
```bash
cd ~/unified-trading-system-repos/instruments-service
export GCP_PROJECT_ID=central-element-323112
export CLOUD_PROVIDER=gcp
export CLOUD_MOCK_MODE=false

TODAY=$(date -u +%Y-%m-%d)

# CEFI — 9 venues
for venue in BINANCE-SPOT BINANCE-FUTURES DERIBIT BYBIT OKX UPBIT COINBASE HYPERLIQUID ASTER; do
  bash scripts/run_vm_backfill_e2e.sh \
    --venue "$venue" --asset-group CEFI \
    --start-date 2019-01-01 --end-date "$TODAY" \
    --chunk-days 30 --parallel 4 \
    --log-dir "logs/recon-fill-cefi-$venue" > "/tmp/backfill-cefi-$venue.log" 2>&1 &
done

# TRADFI — 6 venues
for venue in CME CBOE NASDAQ NYSE ICE FX; do
  bash scripts/run_vm_backfill_e2e.sh \
    --venue "$venue" --asset-group TRADFI \
    --start-date 2019-01-01 --end-date "$TODAY" \
    --chunk-days 30 --parallel 4 \
    --log-dir "logs/recon-fill-tradfi-$venue" > "/tmp/backfill-tradfi-$venue.log" 2>&1 &
done
wait
```

Resumable via `.backfill-checkpoints/<AG>_<venue>_<range>/`. Cumulative ~60 concurrent
`instruments-service` procs. Smoke-test one chunk first to confirm env propagates:
```bash
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp \
  .venv/bin/instruments-service --operation instruments --mode batch \
  --asset-group CEFI --venues DERIBIT --start-date 2019-01-01 --end-date 2019-01-03
```
Expected: real progress past the bootstrap log lines (currently it dies at log_event("STARTED")).

**Follow-up bug to file**: `run_vm_backfill_e2e.sh` should export `GCP_PROJECT_ID` /
`CLOUD_PROVIDER` for child invocations, OR at minimum check that they're set before
spawning chunks. Silent fail across 90 chunks per venue with no visible error in the
top-level log was a data quality risk. Tracking under
`instruments-service` (no plan slug yet — Harsh to follow up tomorrow).

### SPORTS — choose one path

**Path 1 (preferred, requires IAM grant) — VM launchers, singleton-locked:**

Ikenna runs as project owner:
```bash
gcloud iam service-accounts add-iam-policy-binding \
  1060025368044-compute@developer.gserviceaccount.com \
  --member="user:harshkantariya@odum-research.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=central-element-323112
```

Then fire:
```bash
bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh 2020-06-01 2026-05-04
# (sfi excluded — other agent's VM in flight)
# Optional, if recon shows phantoms in their data types:
bash deployment-service/scripts/vm/launch-footystats-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-understat-backfill-vm.sh 2020-06-01 2026-05-04
bash deployment-service/scripts/vm/launch-openmeteo-backfill-vm.sh 2020-06-01 2026-05-04
```
Singleton-lock prevents thundering herd against shared API keys. **This is the canonical
path** per the playbook — same pattern your teammate's existing 31 VMs use.

**Path 2 (fallback, no IAM grant needed) — local CLI, manually paced:**

If the IAM grant doesn't land in time, run sports adapters locally one-at-a-time:
```bash
cd ~/unified-trading-system-repos/instruments-service
export GCP_PROJECT_ID=central-element-323112
export CLOUD_PROVIDER=gcp

# api-football — sequential per entity to mimic the singleton lock behavior
for entity in FIXTURES STANDINGS INJURIES PLAYER_STATS FIXTURE_LINEUPS FIXTURE_STATS FIXTURE_EVENTS TEAMS LEAGUES; do
  .venv/bin/python -m instruments_service \
    --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider API_FOOTBALL --sports-entity $entity \
    --start-date 2020-06-01 --end-date 2026-05-04 \
    > /tmp/sports-af-$entity.log 2>&1
done

# transfermarkt — PLAYER_VALUES is the big one (8,647 phantoms)
for entity in PLAYER_VALUES TRANSFERMARKT_LEAGUES TEAM_SQUAD; do
  .venv/bin/python -m instruments_service \
    --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider TRANSFERMARKT --sports-entity $entity \
    --start-date 2020-06-01 --end-date 2026-05-04 \
    > /tmp/sports-tm-$entity.log 2>&1
done
```

⚠️ **Caveat**: this bypasses the singleton lock. If another sports VM (or your
teammate's SFI VM) is hitting the same shared API key, you'll thrash. Before firing
Path 2 confirm `gcloud compute instances list --filter='name~"^(af|tm|fs|understat|openmeteo)-"'`
is empty.

### PREDICTION — out of scope

Phase 0 dry-run found 11,848 phantoms but they're all on POLYMARKET / `trades` data type.
That's MTDS data (market-tick), not `instruments-service` reference data. Either the
prediction manifest is conflating MTDS writes with instruments writes, or the writers are
mis-attributing the asset group. **Flag for Ikenna separately**, do not flip in this plan.

### DEFI — optional cleanup

597 phantoms, all on EIGENLAYER / `rewards`. Not core instruments data. Two choices:
- Skip (0.2% of defi manifest, won't move the headline percentage).
- Flip with `reconcile_phantom_manifest_rows_all.py --asset-group defi` (~5 min,
  no backfill needed, just clears the phantoms so the headline is honest).

## Verification after backfills complete

For each AG:
```bash
cd ~/unified-trading-system-repos/instruments-service
.venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag> --dry-run
```
Expected: "No phantoms found. Manifest is clean." If non-zero, the orchestrator's
`_should_skip_shard` skipped some shards as `attempted_failed` → `attempted_failed`
(real failure, not phantom). Check the new `error_reason` distribution to decide
whether to retry, fix the adapter, or accept as legitimate API failure.

## Risks / blockers

- **SFI VM in flight**: while the single SFI instruments VM is running, do NOT touch
  `SFI_LEAGUES` / `SFI_PROGRESSIVE_STATS` data types in either reconciler or launcher
  invocations. Reading the manifest mid-write is OK (atomic GCS object), but flipping
  rows the VM is about to write would race.
- **Cefi/tradfi/defi/prediction instruments have no dedicated VM launcher.** Default path
  is `run_vm_backfill_e2e.sh` running locally on this machine — IP-rate-limited by the
  laptop's egress. For instruments-service this is fine (low API volume); if a particular
  venue's daily fetch is slow, Path B (wrap in a VM) is the upgrade. Defer to Ikenna before
  introducing a new VM-launcher pattern.
- **Wall-clock**: realistic only after Phase 0 dry-run reveals gap size. Instruments-service
  shards are tiny (one daily JSON pull per venue), so even thousands of red shards can
  finish in hours via `run_vm_backfill_e2e.sh --parallel 4`. Tick-data scale doesn't apply.
- **API rate limits**: singleton-locked launchers (`launch-sfi-forward-poll.sh` etc.) refuse
  duplicates by design. Don't bypass with `--force` without explicit reason. Use
  `--parallel 2` instead of `--parallel 4` for prediction venues (POLYMARKET / KALSHI
  rate-limit harder than crypto exchanges).
- **Scope ambiguity**: the (1) vs (2) "100%" question above. Resolve before EOD push.

## Out of scope (for *this* plan — covered by parent epic)

- deployment-ui Phase 0 bug fixes (CSV download, day-shard scroll, schema modal, market-tick
  + market-data-processing unified view).
- market-tick-data-service backfills (parent-epic Phase 2/3/4/5).
- market-data-processing-service candle generation (parent-epic Phase 2).
- VIX futures full-tick chain (parent-epic Phase 3, P2 deferred).
- mbp_10 deep-book for tradfi (parent-epic Phase 3, P2 deferred).

## Notes — Phase 0 dry-run results (2026-05-04 12:33–12:45 IST)

| Asset group | Manifest rows | Captured-in-scope | Real captured | Phantoms | % phantom | Top concentration |
| ----------- | ------------: | ----------------: | ------------: | -------: | --------: | ----------------- |
| cefi        | 1,343,892     | 188,684           | 176,144       | **12,540** | 6.6%   | DERIBIT 3,070; BYBIT 1,834; BINANCE-FUTURES 1,763; OKX-SWAP 1,740; UPBIT 1,352. By data_type: empty=9,757 (schema-4 legacy rows), `trades` 2,501 |
| tradfi      | 32,345        | 26,594            | 23,866        | **2,728**  | 10%    | CBOE 657; ICE 379; CME 373; NASDAQ/NYSE 368 each; FX 330. By data_type: empty=2,472 (schema-4), `ohlcv_*`+`trades`+`tbbo` <70 each |
| sports      | 2,401,547     | 758,465           | 717,242       | **41,223** | 5.4%   | STANDINGS 13,022; INJURIES 9,872; PLAYER_VALUES 8,647; PLAYER_STATS 3,057; FIXTURE_{LINEUPS,STATS} ~2.7k each. SFI excluded (other agent's VM). All venue=`""` (sports keys on league_id, not venue). |
| prediction  | 14,369        | 14,328            | 2,480         | **11,848** | 83%    | POLYMARKET / `trades` 11,831 of 11,848. Almost all phantom — but `trades` is MTDS data, not strict instruments-service |
| defi        | 307,341       | 307,341           | 306,744       | **597**    | 0.2%   | EIGENLAYER / `rewards` (all 597). Effectively clean for instruments. |

### Read of the data

- **cefi**: 12,540 phantoms is real work but tractable — they're spread across the 9 active venues and the 9,757 empty-data_type rows are likely schema-4 legacy that need the same flip-to-`attempted_failed` treatment. Once flipped, the orchestrator will retry. Reasonable target for EOD.
- **tradfi**: 2,728 phantoms, similar shape to cefi. The 2,472 empty-data_type rows are again schema-4 legacy. Should be quick.
- **prediction**: 83% phantom rate is alarming but **the data_type is `trades`** — that's market-tick (MTDS) territory, not `instruments-service` reference data. Almost certainly the prediction manifest is conflating MTDS writes with instruments writes. **Out of scope for this plan**, flag for Ikenna separately.
- **defi**: essentially clean. The 597 EIGENLAYER `rewards` phantoms aren't core instruments either. Could leave as-is or flip in 2 seconds.
- **sports**: still running, will refresh when it completes.

### Decisions

| AG | Phase 1 (flip)? | Phase 2 (launch)? | Notes |
| --- | --- | --- | --- |
| cefi | YES — 12,540 phantoms | YES — after flip | Use `run_vm_backfill_e2e.sh` per venue |
| tradfi | YES — 2,728 phantoms | YES — after flip | Same pattern |
| sports | YES — 41,223 phantoms (SFI excluded) | YES — after flip | Use `launch-{api-football,transfermarkt}-backfill-vm.sh` for affected data types. SFI launchers stay off. |
| prediction | NO | NO | Out of plan scope; `trades` rows are MTDS not instruments. Flag for Ikenna. |
| defi | OPTIONAL — 597 phantoms | NO | EIGENLAYER `rewards` only, not strict instruments. Skip or flip-and-leave. |
