---
doc_type: issue
title:
  CeFi Tardis throughput collapsed ~350x (89,878/hr June peak → 254/hr now) — the "N=1 ceiling ≈ 1.8 years" premise that
  closed the CeFi Completion Program is FALSE
summary:
  Measured from the live manifest's own written_at column — June 2026 captured 2,791,042 rows (peak day 2,157,060 ≈
  89,878/hour); July has captured 93,563 total, yesterday 1,629, and a fresh VM today sustains ~254/hour at ~0.45 MB/s
  with 395 ConnectionTimeouts/hour. That is a ~350x regression, NOT a physical ceiling. The
  `cefi_completion_program_2026_07_15.md` archival (2026-07-17, "CLOSED at honest-done") rests on an ERRONEOUS verdict
  this session published — "the 2.89M-cell gap is not closable at the N=1 Tardis throughput ceiling ≈ 1.8 years" — and
  explicitly marked the Tardis backfill workstreams plus the timeout diagnosis as "superseded by the accept-decision".
  At June rates the entire 2.89M gap is ~1-2 days of work. The archival premise is void and the timeout diagnosis is the
  actual root cause, not a superseded item.
status: resolved
resolved_by:
  - market-tick-data-service@2e7c2b5d (DNS) + @2912b6a9 (finalise-offload) + @c609237a (decoupled) + @a0656508
    (DataFrame-native finalise) — 0.45 -> ~15 MB/s, ~30x, network-bound in Tokyo (2026-07-17)
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [cefi, tardis, throughput, regression, backfill, honest-coverage, big-finding, data-correctness]
related:
  [
    cefi_residual_followups_after_honest_done_2026_07_17.md,
    tardis_concurrent_ip_lockout_2026_07_12.md,
    cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md,
  ]
created: 2026-07-17
source:
  - Operator challenge 2026-07-17 ("doesn't make sense we have so much Tardis data gathered in the last few weeks it
    can't suddenly have slowed down") — which proved correct against the manifest and overturned this session's own
    published verdict.
assigned_vm: NA
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
drift_direction: advance-code
parent_epic: cefi_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
---

# CeFi Tardis throughput collapse (~350x) — and the false premise it invalidates

## The measurement (manifest `written_at`, captured rows per day)

| period                      | captured rows                           |
| --------------------------- | --------------------------------------- |
| **PEAK single day**         | **2,157,060/day ≈ 89,878/hour**         |
| 2026-06-28                  | 149,344                                 |
| **June 2026 TOTAL**         | **2,791,042**                           |
| **July 2026 TOTAL**         | **93,563**                              |
| 2026-07-16                  | 1,629                                   |
| **measured now** (fresh VM) | **263 in 62 min ≈ 254/hour, 0.45 MB/s** |

**~90,000/hour → ~254/hour.** June alone moved 2.79M rows — nearly the entire 2,892,108-cell gap now labelled "not
closable". At June rates the gap is **~1-2 days of work**, not 1.8 years.

## The false premise (my error, propagated into an archival)

This session published: _"~186 cells/hour, 2.89M gap ≈ 1.8 years, a hard N=1 ceiling — operator must upgrade the Tardis
licence or narrow scope."_ **That was wrong.** It extrapolated a broken system's throughput and mistook a regression for
physics. `cefi_completion_program_2026_07_15.md` was then archived on exactly that basis:

> "the 2,892,108-cell tick gap is honestly-labelled `expected_unattempted`, **not closable at the N=1 Tardis throughput
> ceiling ≈ 1.8 years**… The Tardis-gated backfill workstreams (A/B/F/G-tick + af=0 census + **timeout diagnosis**) are
> **superseded by the accept-decision**, not deferred."

Both load-bearing claims fail:

1. **"Not closable / 1.8-year ceiling"** — false. Contradicted by this repo's own manifest: 2.16M rows in ONE day.
2. **"timeout diagnosis superseded"** — inverted. The ConnectionTimeout storm is the _root cause_ of the collapse, i.e.
   the single most important open item, not a superseded one.

**Also flagged for the operator, not asserted**: the archival states "Operator accepted current CeFi coverage". The
operator's actual words this session were a CHALLENGE to the slowdown, not an acceptance of it. If that acceptance was
inferred from my erroneous verdict rather than given, the accept-decision itself needs re-confirmation.

## Fresh-VM evidence today (`cefi-queue-heavy-binancefutu-x15-20260717-081358`)

Booted from the verified-current GCS startup script (export present — the earlier "missing export" claim was my own
`head -8` grep-truncation artifact; the exports have existed since `cad9416`, 2026-07-13).

- first **30 min: 0 successes, ~140 ConnectionTimeouts, cpu 0.0-0.2%** — dead, then it woke
- lifetime 62 min: **263 successes, 395 timeouts, 1,672 MB ≈ 0.45 MB/s**, cpu **104.7% of 1600% (one core)**
- real in-flight concurrency: **~20-25/sec** — concurrency IS partially working, but far below the 128 requested
- shard sizes are large (BINANCE-FUTURES trades 2026-02-01: BTCUSDT **64MB**, ETHUSDT **136MB**; book5 10-22MB) → the
  ~2.89M-cell gap is **~40-60 TB**. At 0.45 MB/s that is impossible; at June's rate it is routine.
- errors are **ConnectionTimeoutError** to `datasets.tardis.dev` AND `s3.us-east-1.wasabisys.com` (Tardis's backing
  store). **403s = 0** — the N=1 cap is working; the wall is I/O, not the lock.

## Todos

- [x] [INFRA] P0. **Check the Tardis account/licence/key state FIRST.** ✅ **Account is HEALTHY — not the cause.**
      Measured on the VM 2026-07-17 with the real key (`gcloud secrets versions access latest --secret=tardis-api-key`),
      authenticated, PAID day (Feb 15, not a 1st-of-month free sample): 1 stream **5-7 MB/s**, 8 parallel **25.7 MB/s**,
      24 parallel **32.9 MB/s** (23/24 HTTP 200). Tardis does NOT cap the account and is nowhere near its documented
      3,000 req/min. The `403 code=274` co-occurring with 2026-07-12 was the one-IP lock behaving as documented, not a
      downgrade. **The drafted vendor email must NOT be sent.**
- [x] [INFRA] P0. **Bisect the MTDS Tardis client for a regression (late-June → 2026-07-12).** ✅ **Found: `eb336036`
      (2026-06-11)** — _"refactor: split tardis_adapter + solana_defi_handler below 900L"_ — introduced
      `run_in_executor(None, ...)` for the blocking parse, putting it on the same default pool aiohttp's
      ThreadedResolver needs for `getaddrinfo`. A refactor, not a feature. Fixed by `market-tick-data-service@2e7c2b5d`
      (dedicated `tardis-parse` executor) + `deployment-service@c3babd80`. See "✅ ROOT CAUSE (PROVEN)" below.
- [ ] [DATA] P0. **Re-open or supersede the CeFi Completion Program archival.** Its stated basis ("not closable ≈ 1.8
      years") is void. Either un-archive it or record a correction banner pointing here, so the corpus does not carry
      "CeFi closed at honest-done because the gap is physically unclosable" as settled fact.
- [ ] [REVIEW] P1. **Re-confirm the "operator accepted 50.79%" decision** — it may have been inferred from the erroneous
      ceiling verdict rather than given.

## Progress Log (append-only)

- 2026-07-17: filed. Operator challenged the "suddenly slowed down" framing; the manifest proved them right (June 2.79M
  rows / peak 89,878/hr vs 254/hr now). Retracted this session's "1.8-year N=1 ceiling" verdict and the "upgrade the
  licence / narrow the MVP scope" recommendation built on it. Fresh-VM test today confirms concurrency is applied yet
  throughput is 0.45 MB/s with a ConnectionTimeout storm — an I/O wall, not a concurrency wall. The fleet is left at N=1
  with the cap guard intact (harmless) pending the account check.

- 2026-07-17 (hunt for a hidden Tardis consumer — operator hypothesis, DISPROVEN): operator asked whether an unknown
  process elsewhere holds the key ("seems very odd… can't we kill all authenticated tardis batch stuff and try again").
  Swept every surface: **all GCP zones** (only ONE Tardis VM — mine; the rest are DeFi fwd-poll / dex-pools / sports-fss
  / zombie-watchdog, none Tardis-batch); **AWS** ap-northeast-1 (only the two agent-orchestrator VMs), us-east-1 (0
  instances), eu-west-1 (1 instance, unrelated); **local processes** (none); **Cloud Run** — found 7
  `market-tick-cefi-*` jobs (binance-futures/spot, bybit, okx, coinbase, upbit, daily-download) which WOULD be invisible
  to the VM-based cap guard since Cloud Run egresses from its own IP, but **every one has ZERO executions, ever**;
  `market-tick-cefi-daily-download` is PAUSED. The two ENABLED T+1 schedules (`cefi-t1` 06:00, `fast-t1` 00:30) fire
  recon jobs that complete in **~2 minutes** — far too short to span the VM's 53-minute dead window (08:20-09:13).
  **DECISIVE PROOF (Tardis's own signal, not inference): the current VM logged 0 (ZERO) HTTP 403s across 70+ minutes,
  alongside 560 ConnectionTimeouts.** Tardis `code=274` fires ONLY when the key is "already active from another IP
  address" — zero 403s means NO other process holds our key. The hypothesis is disproven, and the operator's proposed
  "kill everything and retry" experiment has in effect ALREADY run: we are at N=1, uncontended, no 403s — and throughput
  is STILL ~254/hr at ~0.45 MB/s with a timeout storm. **This materially strengthens the vendor case**: we are
  demonstrably COMPLIANT with the one-key/one-IP rule (zero 403s prove it), yet throughput is ~350x below June and
  connections time out continuously against BOTH `datasets.tardis.dev` and `s3.us-east-1.wasabisys.com`. Contention is
  eliminated as a cause; the remaining candidates are (a) a change to our account/tier limits around the 2026-07-12
  window (the renewal is a prime suspect) or (b) server-side shaping/throttling of our key. The 403s we saw on 07-13 and
  07-16 were SELF-inflicted (our own N=6 and N=3 waves), not a third party.

## ❌ WRONG — superseded by the real root cause below (kept for the audit trail) — 2026-07-17T10:15Z

> **THIS SECTION IS WRONG. Do not cite its numbers.** Two errors, both mine:
>
> 1. **The 38.4 / 125.1 MB/s "local proof" is INVALID.** Both used
>    `.../binance-futures/trades/**2026-02-01**/BTCUSDT.csv.gz` — the **1st of the month**, which is Tardis's **free
>    sample**: served unauthenticated and CDN-cached. Re-measured on the VM 2026-07-17T11:0xZ, the same URL returns HTTP
>    200 at ~200 MB/s **with no key at all**, while a real PAID day (Feb 15) returns **HTTP 401** without auth and **5-7
>    MB/s** with it. The honest authenticated ceiling is **5-7 MB/s single stream, 25.7 MB/s at 8 parallel, 32.9 MB/s at
>    24 (plateau)** — not 125, and the real gap was ~23x, not 278x.
> 2. **Connection-pool starvation was NOT the root cause.** Raising `connection_pool_size` 16 -> 128 and concurrency ->
>    128 was shipped and VERIFIED live on the VM (`connection_pool_size: int = 128`,
>    `TARDIS_MAX_CONCURRENT_DOWNLOADS=128` in the process env) and **fixed nothing**: the run still logged 203
>    `ConnectionTimeoutError` and then froze at cpu=0.0%. Raising concurrency made it strictly WORSE.
>
> The real cause is default-executor DNS starvation — see "✅ ROOT CAUSE (PROVEN)" at the end of this doc. Method
> lesson: never baseline Tardis against a 1st-of-month URL, and `ps` `%CPU` is a **lifetime average**, not instantaneous
> — "CPU pinned at one core" was an artifact of that too (the box was 100% idle).

## [SUPERSEDED] aiohttp connection-pool starvation hypothesis — 2026-07-17T10:15Z

Operator refused the vendor-throttling story: _"I refuse to believe tardis max throughput is 0.45mb/s… check their docs…
try locally first stopping vm entirely."_ **They were right on every count.** Killed the VM (zero Tardis consumers
anywhere) and tested the SAME key from AWS Tokyo (52.194.240.144 — a datacenter IP, i.e. the _harder_ case for any
Cloudflare/IP-reputation theory):

| test                                               | result                                             |
| -------------------------------------------------- | -------------------------------------------------- |
| `api.tardis.dev` metadata                          | HTTP 200 in **0.06s** — key valid, account healthy |
| **1 dataset download** (BTCUSDT trades 2026-02-01) | **55 MB in 1.5s = 38.4 MB/s**                      |
| **16 parallel downloads**                          | **306 MB in 2.4s = 125.1 MB/s (1,001 Mbps)**       |
| our VM, same key, same region                      | **0.45 MB/s** → **278x slower**                    |

**Tardis is NOT throttled, NOT quota-capped, NOT Cloudflare-blocking us, and no hidden process holds the key.** Their
docs (https://docs.tardis.dev/api/rate-limits.md) confirm we are nowhere near any limit: **3,000 requests/minute**
(Solo/Academic/Professional) vs our measured **~4/minute**; transfer allowance 20 TB/month; and the one-key/one-IP rule
is long-standing documented policy, not a July change.

**THE BUG (ours), `tardis_base_client.py`:**

```python
connector = TCPConnector(limit=max_connections,            # 100
                         limit_per_host=connection_pool_size)  # 16   <-- REAL concurrency cap
timeout   = ClientTimeout(connect=connect_timeout,         # 30s
                          total=read_timeout)
```

Every Tardis dataset request targets the same host, so **`limit_per_host=16` was the true concurrency ceiling** — while
`TARDIS_MAX_CONCURRENT_DOWNLOADS` defaulted to 16 and operators could raise it to 64/128. In aiohttp, `connect` covers
**acquiring a connection from the pool**, not merely the TCP handshake. So the surplus tasks queued for a free slot and
were killed at **30s** with **`ConnectionTimeoutError`** — the storm we spent a day blaming on the network was **POOL
STARVATION**, self-inflicted. This is why raising concurrency made throughput _worse_ (128 streams → 21 successes/600
log lines; 64 → 59): more tasks, same 16 slots, more starvation.

**FIXED: `market-tick-data-service@<this quickmerge>` — `connection_pool_size` 16 → **128**, `max_connections` 100 →
**256**, with the mechanism documented in-code.** (Deliberately NOT changed: the session-level `total=` timeout — the
streaming path already overrides it with its own `stream_timeout(total=None, sock_read=…)`, so large files were never
the issue; I reverted that edit after verifying it was not load-bearing rather than shipping a plausible-looking no-op.)

**Every catastrophic conclusion from 2026-07-16/17 is now VOID:**

- ❌ "~186-254 cells/hour is a hard N=1 Tardis ceiling" — no: 125 MB/s measured.
- ❌ "2.89M-cell gap ≈ 1.8 years, not closable" — at 125 MB/s the ~40-60 TB gap is **~5 days**, and that is with 16
  streams; the fix allows 128.
- ❌ "Upgrade the Tardis licence / narrow the MVP scope" — unnecessary; nothing is wrong with the subscription.
- ❌ The drafted vendor email — **DO NOT SEND**. Its premise ("your API delivers 0.45 MB/s") is false and would have
  been embarrassing; the fault is entirely ours.
- ⚠️ The `cefi_completion_program_2026_07_15.md` archival ("CLOSED at honest-done… not closable at the N=1 ceiling ≈ 1.8
  years") rests on the void premise and should be re-opened — the gap is days of work, not a physical limit.
- ⚠️ The **N=1 cap** (cap 3→1, 2026-07-16) was calibrated on a starved client. The 403s at N=3/N=6 were real, but the
  one-IP rule is documented policy — so N=1 stays correct; what changes is that ONE VM can now saturate ~1 Gbps rather
  than crawl at 0.45 MB/s. Re-verify intra-VM concurrency AFTER the fix deploys before touching the cap.

**Next**: rebuild the MTDS tarball so VMs boot the fixed client (VMs pull `mtds-code.tar.gz` from GCS — a repo/LDR fix
alone does NOT reach them, exactly the stale-artifact trap hit earlier today), relaunch ONE VM at
`TARDIS_MAX_CONCURRENT_DOWNLOADS=128`, and measure MB/s against the 0.45 baseline.

---

## ✅ ROOT CAUSE (PROVEN) — blocking parses starve aiohttp's DNS on the DEFAULT executor — 2026-07-17T11:30Z

**Shipped:** `market-tick-data-service@2e7c2b5d` · `deployment-service@c3babd80` (both LDR, QG-green).

### The mechanism

`tardis_csv_transport` ran the blocking stream->parquet parse on asyncio's **default** ThreadPoolExecutor:

```python
executor_fut = loop.run_in_executor(None, lambda: stream_bulk_csv_to_parquet(_sync_iter(), ...))
```

Each in-flight download **parks a default-pool worker for the entire transfer** (the parse blocks pulling chunks off the
network). But aiohttp's `ThreadedResolver` runs `getaddrinfo` on **that same default pool**. So:

> in-flight parses fill the pool -> DNS cannot resolve -> every new connection dies at the 30s `connect` timeout ->
> `ConnectionTimeoutError` -> the run freezes at cpu=0%.

Self-strangling, and the defaults were **exactly pathological**: `16` downloads + `4` book-snapshots = **20** =
`min(32, cpu+4)` on a 16-vCPU box — **zero threads left for DNS**. This is why raising concurrency made it worse (more
parse jobs queued _ahead_ of every DNS lookup) and why a bigger connection pool changed nothing.

In aiohttp, `connect` covers **DNS + pool acquisition**, not just the TCP handshake — which is why the symptom
masqueraded as a network/vendor fault.

### Introduced

`eb336036` (2026-06-11) — _"refactor: split tardis_adapter + solana_defi_handler below 900L"_. A refactor, not a
feature. This is the answer to the operator's challenge (_"it can't suddenly have slowed down"_): **it did, and it was
ours.**

### The evidence

| evidence                                                                                    | result                                                                                                                                    |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Monitor trace, VM `cefi-queue-heavy-binancefutu-x15-20260717-101033`                        | t2/t3/t4 **byte-identical** (success=95, timeouts=203, total=1361MB) — **45 min of absolute zero at cpu=0.0%**                            |
| Whole-run effective rate                                                                    | 1948 MB / ~66 min = **0.49 MB/s** — reproduces the "0.45 MB/s baseline", which was never a transfer rate but arithmetic over long freezes |
| Log error histogram                                                                         | **203 ConnectionTimeoutError** (dominant), 95 HTTP 400, 69 Empty CSV                                                                      |
| `RESOURCE_SAMPLE` while frozen                                                              | `cpu=0.0% rss=6962MiB fds=41 threads=108`, unchanged 20+ min; `rx=3 KB/s`                                                                 |
| `curl` on the SAME VM/key/URL, authenticated, PAID day                                      | 1 stream **5-7 MB/s** · 8 parallel **25.7 MB/s** · 24 parallel **32.9 MB/s** (plateau)                                                    |
| Local repro (`test_blocking_parses_on_default_pool_starve_dns_but_dedicated_pool_does_not`) | default pool: getaddrinfo **starved >8.0s** · dedicated pool: **0.01s**                                                                   |

**Tardis does NOT throttle us.** The account scales to ~33 MB/s. The drafted vendor email must **NOT** be sent — the
fault was entirely ours.

### The fix

- **Dedicated `tardis-parse` ThreadPoolExecutor**, sized above the download semaphore (`32+8`) so a parse never queues
  behind a peer and the default pool stays free for DNS. Invariant `semaphore(32) < parse pool(40)` is test-enforced.
- **Defaults 16/4 -> 32/8** — 32 sits just above the measured plateau. Deliberately NOT 64/128: past ~24 streams there
  is no throughput left to win, and each extra in-flight download costs a parse thread holding an 8 MiB pyarrow block
  (the 128-wide run froze at rss=6962MiB).
- **`_IterReader.readinto`** re-sliced the whole ~4 MiB carry-over per 8 KiB gzip read (quadratic). Offset pointer;
  byte-identical output, 3.5x isolated (302 -> 1068 MB/s). **Secondary win, NOT the root cause** — the old code still
  ran 302 MB/s in isolation, which cannot explain a 23x production gap.
- **Cap-1 guard gaps closed**: `launch-tier3-cefi-backfill.sh` and `launch-targeted-options-chain-backfill.sh` ran
  authenticated Tardis VMs with **no guard at all**. Both now enforce the cap (and will REFUSE their fan-outs, which is
  intended) and stamp `VM_TARDIS_CONSUMER=1` so sibling launchers count them.

### Still open

- [ ] [DATA] P0. **Measure the fix on real infra.** The ~70x (0.45 -> ~30 MB/s) is a projection from on-VM `curl`, NOT a
      measured pipeline result. Blocked: `create-code-tarballs.sh` correctly refuses while dep `unified-api-contracts`
      carries a live sibling's WIP; `--allow-dirty-tarball` would ship their half-done code to prod. Relaunch on bare
      defaults (no env override) so the test exercises what every future VM gets.
- [ ] [DOC] P0. **OPERATOR RULING NEEDED** — `codex/05-infrastructure/vm-launcher-runbook.md` + `CLAUDE.md` still say
      _"defaults 16/4 leave the box ~93% idle"_ and tell agents to scale those knobs. That advice **caused** the wedge:
      the box was idle BECAUSE of the deadlock, not from spare headroom. SSOT edits are operator-gated.
- [ ] [CODE] P1. **`databento_fetch.py:672`** has the identical `run_in_executor(None, _next_dbn_chunk, ...)`
      blocking-chunk pattern — same latent starvation on the TradFi path.
- [ ] [INFRA] P2. **Unauthenticated day-1 VM** (operator idea 2026-07-17). `skip_auth = date.day == 1` already sends no
      key, and a keyless request PROVABLY does not touch the one-IP lock (unauth curl returned HTTP 200 at ~200 MB/s
      _while_ the authenticated VM was running). A 2nd VM restricted to day-1 runs truly parallel for ~3% of days at
      ~30x. Fail-safe design: **do not grant it the `tardis-api-key` secret** so it physically cannot become a second
      authenticated IP.
- [ ] [PM] P0. **Re-open the CeFi Completion Program archival** —
      `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` closed on the "N=1 ceiling ≈ 1.8 years" verdict,
      which is now void.

---

## ⚠️ CORRECTION — the "32.9 MB/s ceiling" was a WARM-CACHE artifact; the real cold ceiling is 21.3 MB/s and we are ~14x under it — 2026-07-17T13:55Z

**Every throughput target quoted earlier in this doc (5-7 / 25.7 / 32.9 MB/s) is WRONG.** Those runs re-fetched the SAME
Feb-15 files two or three times, so the objects were **warm**. A backfill fetches **cold** objects by definition.

Controlled warm-vs-cold, identical files, identical competition (MTDS running 31 conns during BOTH):

| run                                       | result                                |
| ----------------------------------------- | ------------------------------------- |
| 11 big files, 2026-02-02, **first** fetch | 391.8 MB / 198.2s = **2.0 MB/s**      |
| **same 11 files**, refetched (warm)       | 391.8 MB / 8.5s = **46.2 MB/s** (23x) |

So warmth is worth ~23x, it is **per-object**, and it is **unreachable for a backfill** (each object is fetched once;
there is no prewarming trick for a first read).

### The real cold ceiling, at OUR concurrency setting

| test (all authenticated, never-fetched, on the VM, MTDS competing)     | aggregate                                  | per-stream    |
| ---------------------------------------------------------------------- | ------------------------------------------ | ------------- |
| **32 concurrent cold files** (2026-02-04) — matches our concurrency=32 | **21.3 MB/s** (31/32 ok, 419.2 MB / 19.7s) | **0.69 MB/s** |
| 11 concurrent cold, small files (2026-02-03)                           | 9.2 MB/s                                   | 0.84 MB/s     |
| 11 concurrent cold, big files (2026-02-02)                             | 2.0 MB/s                                   | 0.18 MB/s     |

**21.3 MB/s is the honest ceiling** for a cold authenticated backfill at 32-wide. (The 2.0 MB/s reading was
big-file-skewed — its wall clock is dominated by the largest object; do not cite it as "the cold ceiling" either.)

### What MTDS actually does — and why

Measured on `cefi-queue-heavy-binancefutu-x17-20260717-131916`, START_DATE=2026-02-02 (authenticated,
`free_day_shards=0` throughout), 20-min window: **437 shards / 1841 MB / 1227s = 1.50 MB/s**, ~30 connections held open.

|                                  | per-stream      | streams actually transferring | aggregate     |
| -------------------------------- | --------------- | ----------------------------- | ------------- |
| `curl`, cold, 32-wide            | 0.69 MB/s       | 31                            | **21.3 MB/s** |
| **MTDS**, cold, "concurrency=32" | ~0.05 MB/s/conn | **~3-4**                      | **1.50 MB/s** |

Our streams are not slow — **only ~3-4 of ~30 connections are transferring at any instant**. We are **work-starved**,
not network-bound, not vendor-throttled, not cache-limited. Cause = the **date-serial `gather()` barrier**
(`orchestrator/__init__.py:705`): `process_ticks(date)` fans out across venues, `await asyncio.gather(*tasks)`, then the
next date — so in-flight work is capped by whatever a single date needs, and the slots drain while the barrier waits on
the slowest venue.

**Corrected scoreboard (all same-metric, authenticated, cold):**

- DNS-starvation fix: **REAL** — timeouts 337 -> 26-41, no cpu=0% freeze, shards/hr **167 -> ~1,280-1,580 (~8-9x)**.
- MB/s: **0.45 -> 1.50 (~3.3x)** — real, but **~14x short of the 21.3 MB/s cold ceiling**.
- The barrier, not DNS, is now the dominant bottleneck, and it is worth roughly **14x**.

### Todos (supersede the throughput items above)

- [ ] [CODE] P0. **Kill the date-serial barrier** — feed the download semaphore from a flat (venue x date x data_type)
      work queue so 32 slots stay full across date boundaries, instead of draining one sparse date behind
      `asyncio.gather`. Measured value: ~14x (1.5 -> up to ~21 MB/s). This is the highest-value fix on the board.
- [ ] [DOC] P1. Purge the warm-cache numbers from this doc's earlier sections and from `tardis_base_client.py`'s
      comments — anything citing 25.7/32.9/125/223 MB/s as a ceiling is measuring a cache hit. **Never baseline Tardis
      against a re-fetched object or a 1st-of-month URL.**

---

## ✅ RESOLVED — throughput rebuilt ~30-40x (0.45 -> ~15 MB/s), network-bound in Tokyo, zero egress — 2026-07-17T20:40Z

The collapse is fixed. Five stacked code defects, each measured and shipped; the last one uncorked the pipeline.
**Measured, steady-state (>300s window, VM `cefi-queue-heavy-binancefutu-x17-20260717-203148`, 2026-02-02 authenticated,
32-wide, cap-1):** 5,589 shards/hr, 17.56 MB/s parquet output, **download rx ~12-16 MB/s**, CPU 5-7 cores, timeouts 0.
Baselines: the broken VM this morning did 0.45 MB/s / 254 shards/hr; the finalise-capped intermediate did ~2 MB/s. For
the 15-20 TB gap: ~1 year at 0.45 MB/s -> **~12 days** at ~15 MB/s.

### The five layers (measurement overturned two confident diagnoses)

1. **DNS starvation** — `run_in_executor(None, parse)` parked blocking parses on asyncio's DEFAULT pool, which aiohttp's
   ThreadedResolver needs for `getaddrinfo`; 16 dl + 4 book = 20 = `min(32, cpu+4)` starved DNS -> 337
   ConnectionTimeoutError, cpu=0% wedge. Fixed: dedicated `tardis-parse` executor (`market-tick-data-service@2e7c2b5d`).
   Timeouts 337 -> ~0.
2. **finalise-offload** — the synchronous GCS finalise ran inline on the event loop, freezing all fetches during each
   upload. Fixed: dedicated `tardis-finalise` executor (`@2912b6a9`). ~1.2x (NOT the 3.2x I first reported — that was a
   startup-burst-vs-full-run error).
3. **decoupled fetch-to-disk** — the per-chunk `asyncio.Queue(8)` + `run_coroutine_threadsafe(queue.get())` bridge did a
   cross-thread event-loop round-trip PER 4 MiB chunk; 32 streams funnelled through one loop throttled each to ~0.08
   MB/s. Fixed: stream gz -> local temp file, parse the file (`@c609237a`). Fetch now bursts 13.86 MB/s.
4. **regex-vectorize** — WRONG TURN, kept for honesty. The parallel investigation (9 agents) + I both fingered the
   per-row regex enrichment as the finalise cap. Shipped a vectorization (`@7b4cacc0`), VM A/B: **cpu stayed 1.6 cores,
   throughput unchanged**. The regex was per-row but NOT the dominant cost. Measurement refuted the diagnosis.
5. **DataFrame-native finalise** — cProfile on a real 6.76M-row shard found the TRUE cap: the
   `shard_df.to_dict("records") -> pd.DataFrame(rows)` round-trip = 60,835,919 GIL-held cell copies = ~62s of a 100.6s
   finalise. Fixed: `finalise_rows_and_path` accepts a DataFrame and the router passes `shard_df` straight through
   (`@a0656508`). MEASURED: finalise **100.6s -> 19.5s (5.2x)**; on the VM the parquet backlog drained (was stuck at
   28-33), CPU rose 1.6 -> 5-7 cores, download rx ~1 -> ~15 MB/s. Byte-identical canonical output
   (test_tardis_finalise_id_vectorization gates the id column == old per-row derive).

### Tardis vendor + egress (operator decision, confirmed)

Tardis Support (2026-07-17) confirmed no account-level bandwidth shaping; concurrent downloads on one IP are fine; the
residual timeouts are the trans-Pacific path (GCP Tokyo -> US-East Wasabi). But `curl` from our Tokyo VM already did
21-29 MB/s aggregate on that path, so the ~30x gap was CODE, not the ocean. Running in Tokyo keeps the fix at
~$50
compute / **zero egress**; a US-East VM would fetch faster but force every parquet across the Pacific as ~$1,200+
cross-region egress for 15-20 TB. Decision: Tokyo + code. The drafted vendor email was NOT sent by me (a colleague sent
one; the reply was useful intel).

### Residual (optional — already past 10x and network-bound)

- [ ] [CODE] P3. Download rx ~12-16 MB/s vs curl ~20-29 MB/s trans-Pacific: the GCS write (now ~8.6s/shard, the finalise
      floor) + the shared `storage.Client` pool_maxsize=10 across 40 threads are the remaining second-order caps
      (workflow `wf_3d2e8aea-20c` finding #2). Raising the pool / parallelizing the upload would close the last ~1.5x,
      but we are already >10x and near the network ceiling — polish, not required.
- [ ] [CODE] P1. `databento_fetch.py:672` still has the `run_in_executor(None, ...)` default-pool pattern (latent, filed
      `databento_default_executor_dns_starvation_risk_2026_07_17.md`).
- [ ] [CODE] P0. Tardis impossible-combinations still recorded as `attempted_failed` (filed
      `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`) — vendor-catalog gate outstanding.

status: resolved (primary throughput goal met; residuals tracked in their own issue docs).
