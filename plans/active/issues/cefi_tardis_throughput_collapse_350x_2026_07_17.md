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
status: open
resolved_by:
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

- [ ] [INFRA] P0. **Check the Tardis account/licence/key state FIRST (5 min, highest value).** The
      `403 code=274 concurrent-IP-lock` FIRST appears 2026-07-12 — the same window as the throughput collapse. June
      evidently ran many parallel VMs with no lockout. If the key was downgraded/expired into a lower tier (or Tardis
      began enforcing a limit), that ONE fact explains BOTH the new 403s AND the ~350x collapse, and the "N=1 cap" we
      hard-coded on 2026-07-16 would be a symptom we institutionalised rather than a law.
- [ ] [INFRA] P0. **Bisect the MTDS Tardis client for a regression (late-June → 2026-07-12).** If the account is
      unchanged, diff `market-tick-data-service` Tardis-path commits in that window (timeout / retry / backoff /
      connection-pool / streaming config) against the June-vs-July throughput cliff.
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

## 🎯 ROOT CAUSE FOUND — aiohttp connection-pool STARVATION. Tardis is fine (125 MB/s). — 2026-07-17T10:15Z

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
