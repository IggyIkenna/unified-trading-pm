---
doc_type: issue
title:
  Tardis academic API key allows only ONE concurrent IP — 74.9% of ALL cefi attempted_failed rows (1.29M/1.72M) are HTTP
  403 lockouts, not genuine data unavailability
summary:
  "Live-reproduced 2026-07-12: `datasets.tardis.dev` bulk-CSV requests return HTTP 403 with Tardis error code 274 ('This
  Data API key is already active from another IP address. Use one API key from one IP address at a time.',
  retryAfterSeconds present) whenever more than one Tardis-calling process (VM) uses the shared academic key
  concurrently. A live manifest query shows this is not a one-off: 1,290,959 of 1,724,206 (74.9%) `attempted_failed`
  rows in the cefi prd manifest carry `error_reason` containing '403' — including DERIBIT 98.1%, BITFINEX 99.0%, BINANCE
  97.6%, COINBASE 96.3%, BITGET-FUTURES 95.3%, OKEX-SWAP 91.6%. This plan (`mvp_backfill_cefi_tick_v10`) has repeatedly
  launched 20-80+ SPOT VMs concurrently across its multi-week history — each VM calls Tardis directly from its own IP,
  so only one VM in any concurrent batch can succeed at a time; every other VM in the SAME wave gets 403'd for its
  entire overlapping runtime. This is very likely the dominant cause of this plan's persistent attempted_failed
  accumulation, not per-venue data unavailability, credential expiry (the 2026-07-03 BLOCKED-CREDENTIALS diagnosis was a
  PATH/gcloud-wrapper false-abort, already corrected same-day), or the (separately resolved) billing gate
  (`cefi_tardis_historical_blocked_credentials_2026_06_21.md`, lifted 2026-07-12)."
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    tardis,
    rate-limit,
    concurrency,
    honest-coverage,
    denominator-audit,
    layer-2,
    data-correctness,
    cefi,
    mvp-backfill-v10,
    big-finding,
  ]
related:
  [
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    cefi_tardis_historical_blocked_credentials_2026_06_21.md,
    cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md,
    ../../../codex/02-data/tradfi-databento-sourcing-ssot.md,
    ../../../codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P0
source:
  mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T13:00-13:35Z session (data_engineering slot-2)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: infra
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
depends_on: []
---

## What I found

Testing `datasets.tardis.dev` bulk-CSV access directly (to verify whether a prior session's DERIBIT-COMBO 403 was a real
credential/entitlement gap, per `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`'s "Genuinely still open"
section), a plain `curl` from THIS session's environment (which has working `gcloud`/network access, unlike the prior
sandboxed session) reproduced the SAME 403 — but the response body reveals the real cause:

```json
{
  "code": 274,
  "message": "This Data API key is already active from another IP address. Use one API key from one IP address at a time.",
  "retryAfterSeconds": 893
}
```

This is a **Tardis-side concurrent-session lock**, not a missing entitlement, not an expired key, not a billing gate.
The academic-tier key this workspace uses only permits ONE active IP at a time for the bulk-CSV dataset endpoint. At the
moment of the test, 2 SPOT VMs were confirmed RUNNING in this plan's fleet
(`cefi-bitget-futures-2024-heavy-20260712-090713`, `cefi-bybit-spot-2025-heavy-20260712-121327`) — either one holding
the lock explains the 403 on a 3rd concurrent caller (this session's curl).

**Scope check (live manifest query, cefi prd, 2026-07-12T13:32Z):**

| venue            |           403 |      total af | pct       |
| ---------------- | ------------: | ------------: | --------- |
| DERIBIT          |       565,315 |       576,288 | 98.1%     |
| BITFINEX         |       102,860 |       103,860 | 99.0%     |
| BINANCE          |        76,955 |        78,855 | 97.6%     |
| COINBASE         |        32,874 |        34,133 | 96.3%     |
| BITGET-FUTURES   |       157,922 |       165,764 | 95.3%     |
| OKEX-SWAP        |        93,537 |       102,126 | 91.6%     |
| OKEX-FUTURES     |        43,463 |        50,160 | 86.6%     |
| CRYPTOFACILITIES |        12,736 |        20,601 | 61.8%     |
| BYBIT            |       119,486 |       168,874 | 70.8%     |
| BYBIT-SPOT       |         2,798 |         3,776 | 74.1%     |
| BINANCE-FUTURES  |        76,158 |       191,007 | 39.9%     |
| **ALL VENUES**   | **1,290,959** | **1,724,206** | **74.9%** |

(KRAKEN-FUTURES, BITFINEX-FUTURES, BINANCE-SPOT, BITGET-SPOT, OKX-SWAP/FUTURES/SPOT, COINBASE-SPOT, KRAKEN-SPOT,
HYPERLIQUID show 0% 403 — either genuinely different failure modes or these venues' af rows predate/postdate the
concurrent-wave windows.)

For BITGET-FUTURES specifically (the venue investigated in depth this session for a separate blank-`instrument_type`
bug, see `cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`), the full error_reason breakdown of its
165,764 attempted_failed rows: `Tardis HTTP 403`=157,922 (95.3%), `Tardis HTTP 400`=5,824, `Tardis HTTP 500`=1,399,
`Tardis HTTP 503`=553, plus small CSV-parse/timeout/connection-reset tails — i.e. even the NON-403 tail is mostly other
transient HTTP errors, not genuine "this venue has no data" honest-absences.

## Why it matters

This plan's whole operating pattern — launch 20 to 80+ SPOT VMs concurrently per wave, each calling Tardis directly from
its own ephemeral IP — is **structurally self-defeating against a single-concurrent-IP key**. Every wave in this plan's
multi-week history (2026-06-28 through 2026-07-12, at least 6 distinct multi-VM waves recorded in the plan's Progress
Log) would have had at most 1 VM succeed at Tardis calls at any given moment, with every other concurrently- running
VM's Tardis requests 403'ing for the full duration of the overlap. This means:

- The plan's repeated "relaunch, wait, re-verify, still NOT MET" cycle across many sessions was very likely fighting
  this lockout the whole time, not resolving genuine per-venue data gaps.
- `attempted_failed` counts in every prior G4 verification run in this plan's Progress Log are NOT a reliable signal of
  genuine per-cell data unavailability — they are dominated by a self-inflicted concurrency conflict.
- The recent DERIBIT-COMBO/OKX code fixes (`unified-api-contracts@f0dc61a2`/`84ce5929`,
  `market-tick-data-service@ 1bc4e000`/`7dbd19f4`/`b03e39de`) are very likely CORRECT and unverifiable-until-now only
  because every live-fire attempt (this session's included) collided with this lock, not because the fixes are wrong.
- This is NOT specific to cefi or this plan — ANY Tardis-based CeFi backfill anywhere in this system (this key is shared
  workspace-wide) hits the same ceiling the moment 2+ Tardis-calling processes run concurrently.

## Recommended decision (operator judgment call — not a plain code fix)

Three non-exclusive resolution paths, in rough order of effort:

**(a) Serialize Tardis-calling VMs.** Add a distributed lock (e.g. a GCS object lease, or a Cloud Run/Firestore-backed
mutex) that `launch-cefi-sharded-backfill.sh`-launched VMs acquire before calling `datasets.tardis.dev` and release
after. Cheapest to build, but destroys the wall-clock parallelism this plan has relied on throughout (backfills that
took hours with 20-80 concurrent VMs would take 20-80x longer serialized).

**(b) Tardis plan upgrade.** Contact Tardis to ask whether the current academic-tier key can be upgraded to allow
multiple concurrent IPs (common on paid/commercial tiers) — a billing/procurement decision, not engineering.

**(c) Centralized fetch proxy.** Route every VM's Tardis bulk-CSV calls through ONE long-lived proxy service (fixed
egress IP, e.g. a Cloud Run service or a dedicated always-on VM) that serializes/queues Tardis requests internally while
still letting the SPOT VMs parallelize everything else (GCS writes, manifest updates, symbol resolution). Real
engineering effort (a new small service + client-side redirect in `tardis_batch_download.py`), but preserves the
existing parallel-VM operational pattern.

**My recommendation**: (c) is the only option that doesn't sacrifice this plan's (and every future CeFi backfill's)
wall-clock throughput, but it's real net-new infrastructure, not a same-session fix — flagging as
`assigned_role: infra`, `model_tier: opus-required` (architecture decision) rather than attempting unilaterally. (a)
could be a quick stopgap (a shared GCS-lease mutex is maybe a 1-2 hour build) if the operator wants to unblock G4 sooner
at the cost of wave wall-clock time.

## Engineering grounding (infra, slot-2, 2026-07-12)

Grounding the operator decision in the actual code surface (all paths workspace-relative to `.tabs/<slot>/`):

- **Launch fan-out is real and default-15.** `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` defaults
  `MAX_CONCURRENT=15` (line 66) and the plan's Progress Log shows operators driving it to 20-80+ via `VENUES`/`ONLY`.
  Every VM provisions its own external IP (`--provisioning-model=SPOT` at line 432, no `--no-address`) and calls
  `datasets.tardis.dev` directly — so against a single-concurrent-IP key, at most ONE VM per wave can hold the Tardis
  lock at any instant; the other 14-79 get code-274 403 for the full overlap. The issue's 74.9% figure is the direct
  consequence.
- **403 is NOT retried and code-274 is NOT distinguished** — the root aggravator.
  `market-tick-data-service/.../clients/tardis_base_client.py` sets `retry_status_codes = (429, 500, 502, 503, 504)`
  (line 138) — 403 is absent — and the 403 handler (line 431) only logs "Check API key access / subscription plan",
  never parsing the `code: 274` / `retryAfterSeconds` body. So a concurrent-lock 403 is recorded as a terminal
  `attempted_failed` row **indistinguishable from genuine data-unavailability**. This is exactly why todo #3 must treat
  every prior af count as noise.
- **Complementary near-zero-cost mitigation (direction-independent, recommended under ALL of a/b/c):** teach
  `tardis_base_client.py` to recognise a 403 whose body carries `code == 274`, honour `retryAfterSeconds` as a backoff,
  and tag the manifest `error_reason` distinctly (e.g. `Tardis 403 code=274 concurrent-IP-lock`) so lock-403s are
  visibly separated from honest-absence in the manifest. This does NOT by itself serialise anything (15 VMs all retrying
  still contend on one lock), so it is a hygiene/observability fix, not a substitute for a/b/c — but it makes every
  option's data cleaner and directly de-noises todo #3's re-measurement.
- **Cross-check on option (b):** the key is loaded from Secret Manager (`config.py` lines 34-77: `tardis-api-key` /
  `tardis-api-key-full`) — a plan upgrade that lifts the single-IP ceiling would require zero code change (just a new
  secret value), which is why (b), if procurement grants it, is the cleanest and could moot (a)/(c).

**Effort estimates (infra craft):** (a) GCS-lease TTL mutex ≈ 1-2 h build (must be TTL-leased, not object-exists, so a
SPOT preemption can't leak the lock); (b) 0 engineering (procurement email + secret swap); (c) centralized fetch proxy ≈
2-3 net-new-service-days (Cloud Run or dedicated always-on VM with a fixed egress IP, plus a client redirect in the
Tardis download path) — preserves the parallel-VM wall-clock the plan relies on. The 403-code-274 hygiene fix above is ≈
30-60 min and is additive to whichever path is chosen.

## Todos

- [ ] [INFRA] P0. Operator decision: which of (a) serialize / (b) Tardis plan upgrade / (c) centralized proxy — or
      accept slower serialized waves as a stopgap while (c) is built. (repo: deployment-service,
      market-tick-data-service)
- [ ] [INFRA] P1. Once decided: implement the chosen fix. If (a) stopgap: a GCS-object-lease mutex acquired in the VM
      startup script or `tardis_batch_download.py` before any `datasets.tardis.dev` call, released on completion/
      preemption (must handle SPOT preemption not leaking the lock — a TTL-based lease, not a plain object-exists
      check). (repo: deployment-service, market-tick-data-service)
- [ ] [DATA] P1. Once the lock contention is resolved (any path above), RE-RUN this plan's G4 verification from a clean
      slate — every prior session's `attempted_failed` count in this plan's Progress Log should be treated as
      upper-bound noise until re-measured post-fix, not a genuine per-venue gap census. (repo: instruments-service,
      e2e-testing)
