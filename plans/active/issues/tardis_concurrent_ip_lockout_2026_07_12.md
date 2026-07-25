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
    /plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    /plans/archive/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md,
    /plans/active/issues/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P0
source:
  mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T13:00-13:35Z session (data_engineering slot-2)
assigned_vm: NA
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

- [x] [INFRA] P0. ✅ Operator decision (BLK-58aea31d): operator ruled **"proceed now"** → build option **(a)** the
      GCS-lease serialize stopgap (2026-07-12, slot-7 infra). (b) Tardis plan upgrade + (c) centralized proxy remain the
      doc's longer-term recommendation — (a) coexists as the interim stopgap. (repo: deployment-service,
      market-tick-data-service)
- [x] [INFRA] P1. ✅ Implemented option **(a)**: a **DEFAULT-OFF** workspace-wide GCS TTL-lease mutex so only ONE
      Tardis-calling VM holds the single-concurrent-IP key at a time. — market-tick-data-service@a9f1b52b +
      deployment-service@c33f681 (2026-07-12, slot-7 infra). `TardisConcurrencyLease`
      (`clients/tardis_concurrency_lease.py`) acquires a process-wide lease over one GCS control object before the first
      KEYED `datasets.tardis.dev` call (free/day-1 no-auth fetches don't use the key → stay parallel), wired into
      `tardis_csv_transport` (streaming + legacy) via a thread-executor acquire (event loop not blocked). Config flags
      in `service_config.py`; launcher/startup-script pass `TARDIS_CONCURRENCY_LEASE` + `..._BUCKET` opt-in only.
      **Safety:** DEFAULT-OFF (no-op unless enabled + a control bucket is set — zero fleet-behaviour change until an
      operator opts in; enabling serialises waves ~20-80x); **fail-open** (acquire blocks ≤ max_wait then proceeds
      WITHOUT the lock → a stuck/leaked lease can never deadlock the fleet); **SPOT-safe** (TTL + background renewer; a
      preempted holder's lease expires and the next VM steals it). 11 unit tests (`test_tardis_concurrency_lease.py`,
      mocked storage). **Known limitation (tracked, see follow-up todo):** UTL has no generation-CAS write, so
      acquisition is write-then-read-back verify (not atomic CAS) — removes STEADY-STATE contention (the 74.9% problem)
      but leaves a rare acquisition-handoff race that yields a single tagged code=274 403 (re-run), not corruption.
      (repo: deployment-service, market-tick-data-service)
- [x] [INFRA] P2. ✅ **Part (1) — race-free atomic CAS: DONE.** — unified-trading-library@b010c7ad +
      market-tick-data-service@7b8144ff (2026-07-12, slot-9 infra, opus). Added generation-precondition
      (compare-and-set) primitives to the UTL `cloud_interface` `StorageClient` — the sanctioned home
      (`google.cloud`/`boto3` are QG-banned in service repos): `download_bytes_with_generation` (one GET returns
      content + generation consistently, no metadata+download race), `conditional_upload_bytes`
      /`conditional_delete_blob` (both keyed on `if_generation_match`), plus `BlobMetadata.generation` and the URI
      wrappers `gcs_read_object_with_generation` / `gcs_conditional_put` / `gcs_conditional_delete`. GCS implements them
      natively via `if_generation_match`; `LocalStorageProvider` emulates generations via `mtime_ns` (10 new UTL unit
      tests); AWS/S3 inherits the `NotImplementedError` base (no generation-match). Switched `TardisConcurrencyLease`
      acquire/steal/renew/release from write-then-read-back-verify to atomic CAS: every write conditions on the exact
      object generation the free/expiry decision was based on, so only ONE of N racing VMs wins any handoff — the
      residual acquisition-handoff race (two VMs briefly both holding the key) is CLOSED; renew CAS drops the lease if
      the generation was stolen; release CAS no-ops instead of clobbering a new holder. Lease stays DEFAULT-OFF +
      fail-open + SPOT-safe. Lease tests rewritten with a generation-aware fake covering lost-CAS-handoff /
      stolen-generation-renew / stale-generation-release. **Evidence:** UTL `quality-gates.sh` green (124s, 10 new CAS
      tests pass); market-tick-data-service `quality-gates.sh` green (`✅ ALL QUALITY GATES PASSED`); both landed on
      live-defi-rollout via `quickmerge --agent`. (repo: unified-trading-library, market-tick-data-service)
- [x] [INFRA] P2. ✅ **Part (2) — enablement smoke-test: PASSED against REAL GCS (slot-4 infra, opus, 2026-07-12).** The
      prior "BLOCKED: gcloud unavailable" premise was **FALSE** — a non-snap gcloud at `~/google-cloud-sdk/bin/gcloud`
      works (SDK 569.0.0, auth `ikenna@odum-research.com`, project `central-element-323112`), and the lease is
      Python/UTL (needs only ADC + the UTL storage client, both live in the slot) so it never needed gcloud at all.
      Runtime-verified the SHIPPED lease code + full wiring against real GCS (control bucket
      `config-store-test-central-element-323112`, unique `_tardis_concurrency_lease_smoketest/` objects, all cleaned
      up): (1) **lifecycle** — acquire CREATES the control object, renew CAS BUMPS the generation, release CAS DELETES
      it; (2) **serialization** — while holder A holds, holder B's `try_acquire_once()` returns False, then acquires
      after A releases; (3) **TTL steal + no leaked lock on preemption** — a short-TTL lease expires, B STEALS it via
      CAS, and A's stale renew CAS returns None (renewer stops) + A's stale release CAS no-ops (B never clobbered); (4)
      **create-only CAS** — a create-CAS(`if_generation_match=0`) against a held lease fails (lost-CAS handoff closed);
      (5) **env→config→transport chain** — `TARDIS_CONCURRENCY_LEASE=1`+`_BUCKET` → `service_config` AliasChoices →
      `get_config()` → transport `_ensure_tardis_concurrency_lease()` (the exact fn at tardis_csv_transport.py:384/:607)
      acquires a real GCS lease, idempotent on re-call; (6) **DEFAULT-OFF** — flag unset → no-op, no control object
      touched; (7) **launcher plumbing** — `DRY_RUN=1 TARDIS_CONCURRENCY_LEASE=1     TARDIS_CONCURRENCY_LEASE_BUCKET=…`
      stamps `TARDIS_CONCURRENCY_LEASE=1,TARDIS_CONCURRENCY_LEASE_BUCKET=…` into the VM metadata
      (`launch-cefi-sharded-backfill.sh:433-434`), which `setup-data-pipeline-vm.sh:205-208` exports. Because the lease
      is a GCS-control-object mutex, the CAS contention is byte-identical whether the two contending processes are two
      VMs or two lease holders in one process (GCS generation preconditions are server-side, host-agnostic), so this
      real-GCS run IS the on-VM behavior. **A physical backfill-VM launch was deliberately NOT run** (see verification
      log): 4 non-lease cefi VMs were concurrently RUNNING and holding the real Tardis IP lock, so a lease-enabled test
      VM's downstream keyed fetch would 403 and add more `code=274` lock-403 rows to the very manifest this issue exists
      to de-noise — counterproductive for a byte-identical, already-verified code path; the lease stays DEFAULT-OFF so
      no fleet change results. **Operational gate for the operator:** the first real lease-enabled wave must have the
      lease enabled on ALL VMs in the wave (a lone lease-enabled VM among non-lease VMs is still 403'd) — that wave is
      itself the natural in-situ 2+VM serialization confirmation. No code changed (parts 1 already shipped); this is a
      verification-only flip. (repo: deployment-service, market-tick-data-service)
- [x] [DATA] P1. ✅ **Direction-independent 403-code-274 error_reason hygiene fix (done under ANY of a/b/c — did NOT
      require the operator decision).** — market-tick-data-service@31934527 (2026-07-12, slot-7 infra).
      `TardisHTTPError` now (i) parses a 403 response body for `code == 274` + `retryAfterSeconds` (attributes
      `concurrent_ip_lock` / `tardis_code` / `retry_after_seconds`); (ii) appends a STABLE `code=274 concurrent-IP-lock`
      marker to the message so `_classify_tardis_error` emits `Tardis HTTP 403 code=274 concurrent-IP-lock` into the
      manifest `error_reason` (`classify_venue_error` is exact-match → the tag passes through unclassified; KEEPS the
      `403` substring so the `error_reason CONTAINS '403'` audit query still matches). `async_iter_bytes` (streaming) +
      `_fetch_tardis_bytes` (legacy) now pass the 403 body through. (iii) `retryAfterSeconds` is CAPTURED as an
      attribute but intentionally NOT slept-on — a 403 stays a terminal fetch-failure; blindly honouring the ~15-min
      backoff with N concurrent VMs would re-contend on the same lock and risk stall-watchdog kills (serialization is
      the a/b/c fix, not this). Unit tests:
      `test_tardis_stream_client.py::TestAsyncIterBytes::test_403_code_274_tagged_as_concurrent_ip_lock` +
      `TestTardisHTTPErrorConcurrentIPLock` (4 cases). This separates lock-403s from genuine honest-absence and DIRECTLY
      de-noises the G4 re-measurement below. (repo: market-tick-data-service)
- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION (gated on todo #1 + todo #2 above — do NOT run pre-fix).** Once the lock
      contention is resolved (any path above), RE-RUN this plan's G4 verification from a clean slate — every prior
      session's `attempted_failed` count in this plan's Progress Log should be treated as upper-bound noise until
      re-measured post-fix, not a genuine per-venue gap census. **Verified 2026-07-12 (data_engineering slot-3): gate
      UNMET — todos #1/#2 both open, no lock/mutex/proxy/403-274 fix in git; a pre-fix re-run would only reproduce the
      known 403-noise. Escalated as BLK-12b5a8b0 (recommend: park this todo, priority 999 + false prereq, until the fix
      lands so it stops being prematurely dispatched).** (repo: instruments-service, e2e-testing)

## Verification log

### 2026-07-12 — G4 re-run gate check (data_engineering slot-3)

Dispatched the `[DATA] P1` "RE-RUN G4 verification from a clean slate" todo. Before running anything, checked whether
the gate ("Once the lock contention is resolved (any path above)") was actually met:

- **Todo #1 (operator decision a/b/c): OPEN** — still `- [ ]`; no operator ruling on this lockout exists (the
  `plan_reconciliation_operator_decisions_2026_07_11.md` Tardis entries are all about the SEPARATE, already-resolved
  billing gate `cefi_tardis_historical_blocked_credentials_2026_06_21.md`, not the concurrent-IP lock).
- **Todo #2 (implement chosen fix): OPEN** — no lock/mutex/GCS-lease/proxy/403-code-274 commit in
  `market-tick-data-service` or `deployment-service` git log since 2026-07-10.
- **Code confirms the aggravator is still live**: `tardis_base_client.py`
  `retry_status_codes = (429, 500, 502, 503, 504)` (403 absent, line ~138) and the 403 handler (~line 431) still only
  logs a generic warning — it does not parse `code == 274` / `retryAfterSeconds`, so concurrent-lock 403s continue to
  land in the manifest as `attempted_failed` rows indistinguishable from genuine unavailability.

**Verdict: gate UNMET.** A pre-fix G4 re-run would only reproduce the same 403-lockout-dominated `attempted_failed`
counts (74.9% of cefi af per the live query above) that todo #3 itself says to treat as upper-bound noise — so it would
be actively misleading and a wasted ~35M-row manifest re-scan. Escalated the premature-dispatch + unmet-gate as a
blocked question (BLK-12b5a8b0) with recommendation (A) the operator makes the todo-#1 decision. Promoted the
direction-independent 403-code-274 error_reason hygiene fix (previously only prose in "Engineering grounding") to an
explicit tracked `[DATA]` todo above, since it de-noises exactly the measurement this task needs and is correct under
any a/b/c choice. Did NOT flip the G4 todo (it is not done) and did NOT run a pre-fix measurement.

### 2026-07-12 — todo #2 (implement chosen fix) dispatched to slot-7 infra

Dispatched `tardis_concurrent_ip_lockout-002` ("Once decided: implement the chosen fix. If (a) stopgap: a
GCS-object-lease mutex…"). Confirmed the gate is UNMET and the fix cannot be built unilaterally:

- **No a/b/c decision exists.** Backlog `-001` (operator decision) is `dispatched` with `assigned_slot: null`, no
  `notes`/`resolution`; no operator messages to slot-7; no ruling anywhere in this doc or the plans corpus. Todo #2
  literally says "implement the **chosen** fix" — nothing is chosen.
- **The issue itself forbids a unilateral pick** — "operator judgment call — not a plain code fix … flagging as
  `assigned_role: infra`, `model_tier: opus-required` (architecture decision) rather than attempting unilaterally."
- **Engineering finding (raises the cost of option (a) above the plan's 1-2h estimate):** UTL's cloud-interface exposes
  only `gcs_copy_object` / `gcs_delete_object` / `gcs_describe_object` — there is NO generation-precondition (CAS)
  conditional-write primitive. A correct SPOT-preemption-safe TTL-lease mutex requires atomic compare-and-set, so option
  (a) needs a NEW UTL primitive first (direct `google.cloud`/`boto3` is QG-banned in service repos) — a cross-repo
  build, not a same-session stopgap. Option (b) (Tardis plan upgrade) needs zero code and would moot (a)/(c) entirely.

**Actions:** escalated the a/b/c decision as **BLK-58aea31d** (recommendation: pursue the free (b) upgrade in parallel
AND build (c) as the throughput-preserving endgame; only build the serializing (a) stopgap if G4 must unblock this
week). Left todo #2 unchecked/blocked. While blocked, shipped the direction-independent 403-code-274 error_reason
hygiene fix (the `[DATA] P1` todo above) — market-tick-data-service@31934527, QG-green, landed on live-defi-rollout —
which is safe and correct under any a/b/c choice and de-noises the G4 re-measurement. Did NOT build any
mutex/serialization.

### 2026-07-12 — operator ruled "proceed now" → built option (a) (slot-7 infra)

Operator answered BLK-58aea31d with **"proceed now"** → implemented option (a), the GCS-lease serialize stopgap, as a
**DEFAULT-OFF** capability:

- **market-tick-data-service@a9f1b52b** — `TardisConcurrencyLease` (`clients/tardis_concurrency_lease.py`): a
  workspace-wide TTL lease over one GCS control object, acquired process-wide before the first KEYED
  `datasets.tardis.dev` call (free/day-1 no-auth fetches stay parallel), wired into `tardis_csv_transport` (streaming +
  legacy) via a thread-executor acquire. Config flags in `service_config.py`. **DEFAULT-OFF + fail-open + SPOT-safe**
  (TTL
  - background renewer). 11 unit tests (mocked storage) + the full MTDS QG green.
- **deployment-service@c33f681** — `launch-cefi-sharded-backfill.sh` (opt-in stamp) + `setup-data-pipeline-vm.sh` (env
  export) pass `TARDIS_CONCURRENCY_LEASE` + `..._BUCKET`; unstamped by default so waves stay parallel until an operator
  opts in. deployment-service QG green.

**Chose the write-then-read-back-verify lease (not atomic CAS)** because UTL exposes no generation-precondition write
and adding one to the multi-backend abstraction + the cross-repo dep-ordering was out of proportion for a stopgap; the
residual acquisition-handoff race only yields a single **tagged** code=274 403 (re-run), not corruption, and the shipped
403-tagging makes even those visible. **gcloud is unavailable in the agent slot** (snap-confine broken), so a
bash/gcloud lease could not be runtime-verified here and the on-VM enablement smoke-test is deferred to a real VM launch
— tracked as the new `[INFRA] P2` follow-up (race-free CAS + on-VM smoke-test) above. The lease is DEFAULT-OFF, so
nothing changes until that smoke-test passes and an operator enables it.

### 2026-07-12 — todo #1 duplicate escalation reconciled (slot-2 infra, opus)

Slot-2 was independently dispatched the todo-#1 operator-decision backlog task (`tardis_concurrent_ip_lockout-001`).
Before escalating I grounded the a/b/c decision in the actual code surface — added the "Engineering grounding" section
above (`MAX_CONCURRENT=15` fan-out, 403 absent from the Tardis retry set, code-274 not distinguished from
honest-absence, Secret-Manager key → option (b) = zero code, per-option effort estimates + the 403-code-274 hygiene fix)
— committed `unified-trading-pm@77fb77f44`, then escalated the same decision as **BLK-f1417674** (recommendation: pursue
free (b) in parallel + authorize (a) stopgap + (c) durable follow-up + the hygiene fix under any path). This was a
**duplicate** of the sibling **BLK-58aea31d**; the operator's "proceed now → option (a)" ruling on that sibling resolves
BLK-f1417674 identically. Todo #1 was already flipped `[x]` and option (a) shipped by slot-7 (mtds@a9f1b52b +
deployment-service@c33f681), and the 403-code-274 hygiene fix I'd recommended landed as mtds@31934527 — so slot-2 built
no duplicate code. `tardis-concurrent-ip-lock-fix-landed` condition flipped true by main; remaining open items are the
`[INFRA] P2` race-free-CAS + on-VM smoke-test and the `[DATA] P1` post-fix G4 re-run (both gated appropriately).

### 2026-07-12 — `[INFRA] P2` part (1) race-free CAS SHIPPED (slot-9 infra, opus)

Dispatched `tardis_concurrent_ip_lockout-003` ("Harden option (a) to be race-free + enable it: (1) add a UTL
generation-CAS conditional-write"). Built the generation-CAS primitive the earlier session found missing (the reason the
stopgap shipped as write-then-read-back rather than atomic CAS), then switched the lease to it:

- **unified-trading-library@b010c7ad** — added `download_bytes_with_generation`, `conditional_upload_bytes`,
  `conditional_delete_blob` (`if_generation_match`) to the `cloud_interface` `StorageClient` ABC +
  `BlobMetadata.generation`
  - URI wrappers (`gcs_read_object_with_generation` / `gcs_conditional_put` / `gcs_conditional_delete`). GCS: native
    `if_generation_match`; Local: `mtime_ns`-emulated generations (10 new unit tests); AWS: inherits the base
    `NotImplementedError` (S3 has no generation-match — the Tardis control bucket is GCS). This is the sanctioned UTL
    home since `google.cloud`/`boto3` are QG-banned in service repos. UTL `quality-gates.sh` green (124s).
- **market-tick-data-service@7b8144ff** — `TardisConcurrencyLease` acquire/steal/renew/release now go through atomic
  CAS: read `(payload, generation)`, and if the lease is free write conditioned on that exact generation (0 =
  create-if-absent). Only one of N racing VMs can win a handoff; a lost CAS returns cleanly (caller yields + re-polls);
  a stale renew/release no-ops instead of clobbering the new holder — the residual acquisition-handoff race is CLOSED.
  DEFAULT-OFF + fail-open + SPOT-safe unchanged. Lease tests rewritten with a generation-aware fake (lost-CAS-handoff /
  stolen-generation-renew / stale-generation-release). MTDS `quality-gates.sh` green (`✅ ALL QUALITY GATES PASSED`).

Both landed on live-defi-rollout via `quickmerge --agent`. **Part (2) — the on-VM enablement smoke-test — remains OPEN
and BLOCKED**: it needs a real cefi backfill VM launch with the lease env vars set (gcloud is unavailable in the agent
slot, per the earlier session's note), so it is split out as its own `[INFRA] P2` todo above. The lease is still
DEFAULT-OFF, so nothing changes in the fleet until that smoke-test passes and an operator opts in.

### 2026-07-12 — `[INFRA] P2` part (2) enablement smoke-test PASSED vs real GCS (slot-4 infra, opus)

Dispatched `tardis_concurrent_ip_lockout-004` (the part-(2) on-VM enablement smoke-test). **First corrected the stale
blocker premise:** prior sessions recorded "gcloud is unavailable in the agent slot (snap-confine broken)" and therefore
deferred this to a real VM launch. That premise was false on two counts — (i) only `/snap/bin/gcloud` is broken; a
**non-snap `~/google-cloud-sdk/bin/gcloud` (SDK 569.0.0)** works and is authenticated (`ikenna@odum-research.com`,
project `central-element-323112`); and (ii) more fundamentally, the lease is **Python/UTL, not bash/gcloud** — it needs
only ADC + the UTL `StorageClient` CAS primitives, both of which are fully live in the slot (`google.auth.default()` →
`central-element-323112`, `download_bytes_with_generation`/`conditional_upload_bytes`/`conditional_delete_blob` all
present and working against real GCS). So the smoke-test never required a VM or gcloud.

**What was runtime-verified (all against REAL GCS, shipped code, no mocks):**

- **Harness A — `TardisConcurrencyLease` direct** (drives the shipped class against control bucket
  `config-store-test-central-element-323112`, unique `_tardis_concurrency_lease_smoketest/lease_<uuid>.json` per run):
  Scenario 1 single-holder lifecycle (acquire → object created @gen G1; renew CAS → gen bumps G1→G2; release → object
  deleted); Scenario 2 create-only CAS (`if_generation_match=0` against a held lease → None, lost-CAS handoff closed);
  Scenario 3 2-holder serialization (B `try_acquire_once()` False while A holds, True after A releases); Scenario 4 TTL
  steal + no leaked lock on preemption (short-TTL lease expires → B steals via CAS; A's stale renew CAS → None so the
  renewer stops; A's stale release CAS no-ops → B's lease never clobbered). **All 26 checks PASS.**
- **Harness B — env→config→transport wiring** (the exact `_ensure_tardis_concurrency_lease()` the CSV transport calls at
  `tardis_csv_transport.py:384`/`:607`, driven purely by the `TARDIS_CONCURRENCY_LEASE*` env vars a VM gets from its
  metadata): env → `service_config` AliasChoices → `get_config()` → transport acquire → **real GCS control object
  created** (process holds the single-IP lease), idempotent on re-call, released + deleted on reset. **DEFAULT-OFF**
  path: `TARDIS_CONCURRENCY_LEASE=0` → `enabled False` → acquire is a no-op, no control object touched. **All checks
  PASS.**
- **Launcher plumbing (`DRY_RUN`)**:
  `DRY_RUN=1 TARDIS_CONCURRENCY_LEASE=1 TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-test-central-element-323112 VENUES=BINANCE-FUTURES YEARS=2024 launch-cefi-sharded-backfill.sh`
  → the printed VM metadata carries
  `…,TARDIS_CONCURRENCY_LEASE=1,TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-test-central-element-323112` (launcher
  lines 433-434), which `setup-data-pipeline-vm.sh:205-208` reads from the metadata server and exports.
- **Cleanup**: every smoke-test control object was released by the lease's own CAS-delete; a post-run
  `gcloud storage ls _tardis_concurrency_lease_smoketest/**` returns "matched no objects" — clean (itself confirming the
  release path against real GCS).

**Why no physical backfill-VM was launched (deliberate, documented):** the lease is a **GCS-control-object mutex** — its
CAS contention is server-side and host-agnostic, so two lease holders in one slot process contend on the GCS object
identically to two VMs; the real-GCS run above IS the on-VM behavior for every claim the todo names (acquire/renew/
release lifecycle, serialization, TTL-steal, CAS no-op). A physical VM would add only in-situ run-log framing of a
byte-identical code path, and doing it **right now would be actively counterproductive**: 4 non-lease cefi VMs
(`cefi-binance-futures-2020/2021-heavy/light-…`) were concurrently RUNNING and holding the real Tardis single-IP lock,
so a lone lease-enabled test VM would still 403 on its keyed fetch and write more `code=274` lock-403 `attempted_failed`
rows into the exact manifest this whole issue exists to de-noise. The lease is DEFAULT-OFF, so nothing changes in the
fleet from this verification.

**Operational gate handed to the operator (the real "should waves run with the lease enabled" decision):** enabling the
lease is only effective if **every VM in a wave** has `TARDIS_CONCURRENCY_LEASE=1` + a shared `_BUCKET` — a single
lease-enabled VM among non-lease VMs is still 403'd because the non-lease VMs ignore the GCS mutex and hold the real IP.
That first fully-enabled wave is itself the natural in-situ 2+VM serialization confirmation (and note: enabling
serialises waves ~20-80× slower — option (a) is the stopgap, option (c) centralized proxy remains the throughput-
preserving endgame). Recommend the operator run that first enabled wave on a small venue/year slice and confirm the
staggered "Tardis lease ACQUIRED by <vm>" ordering in the per-VM logs before enabling it fleet-wide.

### 2026-07-13 — fresh corroboration from an unrelated CeFi futures/derivatives triage pass (still no lease enabled)

Redoing a lost triage pass on `data_pipeline_e2e_check_2026_07_10.md` todo 25's CeFi futures/derivatives cluster
(DERIBIT, DERIBIT-COMBO, OKX, OKX-SPOT, KRAKEN-FUTURES, BYBIT, BINANCE-DELIVERY). Two independent, real confirmations
this exact gate is still live and still the dominant confound for this venue cluster specifically:

1. **`CEFI:DERIBIT:liquidations`'s original 2026-07-09 sweep failure** (`manifest_status_invalid:attempted_failed`) —
   pulled the real run.log (`mtds-backfill-cefi-pipelinecheck-20260712-041757`, a clean single-shard run, no VM-name
   collision): `Tardis streaming request: exchange=deribit, symbol=BTC-PERPETUAL, data_type=liquidations` →
   `Tardis HTTP 403` → `SHARD_INCOMPLETE ... missing: ['DERIBIT']`. Byte-for-byte the same signature this doc's own
   summary already cites DERIBIT hitting 98.1% of the time. Not a new finding, just a fresh, independently-pulled
   confirmation — no code action needed, corroborating only.
2. **A live, real-time reproduction while THIS session's own diagnostic VMs were running** (2026-07-12T23:30-23:50Z):
   launched fresh, clean (post-VM-name-collision-fix, post-candidate-venue-fix) solo re-verification VMs for
   `DERIBIT-COMBO`/`KRAKEN-FUTURES`/`OKX-SPOT` (`trades`/`book_snapshot_5`/`derivative_ticker`, one venue per VM, no
   self-inflicted concurrency beyond the 5-7 launched sequentially by this session's own driver). **Every single
   per-symbol Tardis request across all 3 venues hit `code=274 concurrent-IP-lock`** (856/856 for OKX-SPOT `trades`,
   646/646 for KRAKEN-FUTURES `trades`, 542/542 for DERIBIT-COMBO `trades` — 0 successes across ~2,044 real requests) —
   confirmed via `gcloud compute instances list` that the SAME 4 production `cefi-binance-futures-2020/2021-heavy/light`
   VMs (started 2026-07-12T08:46-08:49Z) were still RUNNING throughout, holding the real single-concurrent-IP lock for
   their entire ~15+ hour lifetime so far. **This means a whole class of "genuine failure" venue-level findings from
   this session's own fresh re-verification attempts (DERIBIT-COMBO/KRAKEN-FUTURES/OKX-SPOT's regular data_types) are
   themselves inconclusive, not clean reads** — cross-referenced in detail onto
   `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`'s DERIBIT-COMBO section. Reinforces the existing
   recommendation: a trustworthy per-venue verdict for this whole cluster needs either the fleet-wide lease enablement
   or a genuine solo window (the 4 production VMs finishing/being paused) — re-running into contention just produces
   more of the same 403-dominated noise, not new signal.

### 2026-07-13T01:16-01:40Z — fresh corroboration (slot-7 data_engineering, DERIBIT-COMBO `[VERIFY]` re-attempt)

Still no operator enablement decision on the lease; 3 of the 4 production `cefi-binance-futures-2020/2021-heavy/light`
VMs were confirmed still RUNNING (~24h elapsed). A solo `opt-deribit-combo-2024` diagnostic VM sampled 4 consecutive
dates: 2/4 hit `code=274 concurrent-IP-lock` directly, 1 hit an unrelated transient `Tardis HTTP 500`, and 1
(2024-01-03) got a full real stream through (59.7M rows) despite the contention — consistent with this doc's own
"retriable, not a hard block" framing rather than a 100% lockout. No change to the underlying blocker or its resolution
path. Full trail: `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`'s "VERIFY re-attempt" section.

### 2026-07-13 — write-level corroboration from BYBIT futures_chain shape-scope audit (slot-8 data_engineering)

While auditing BYBIT `futures_chain` write shapes for `bybit_futures_chain_write_shape_migration_2026_07_13.md` Phase 1
(unrelated task — BYBIT-specific write-shape inconsistency, not this issue), found a **write-level** (not just
`attempted_failed`-row-level) confirmation that adds a sharper data point to this issue: a real day-by-day GCS walk of
the ENTIRE `pipeline_mode=batch_tardis` partition (all CeFi venues, not just BYBIT) shows object counts collapsing from
~4,500/day (2026-05-20/22) → ~500 (2026-05-23) → a flat 203/day (2026-05-25 through 2026-06-03, and those 203 are all
mislabeled `EXTENDED-STARKNET` objects, not real Tardis CEX capture) → **zero objects written under `batch_tardis` for
any venue, any day, from 2026-06-04 onward** (checked through 2026-06-10). Sibling `pipeline_mode=batch_aster` /
`batch_hyperliquid` / `batch_extended` all have normal, current-dated objects (2026-06-15 / 2026-07-01 / 2026-07-10) —
so this is `batch_tardis`-specific, consistent with this issue's premise (the shared academic key gates only
Tardis-sourced calls) rather than a manifest-wide or bucket-wide outage. This means the 74.9% `attempted_failed` figure
above likely understates the real-world impact during the worst-affected window — from 2026-06-04 onward it looks like
essentially 100% of `batch_tardis` write attempts are failing (zero successful writes at all), not just a majority. Not
actioned further here (outside this issue's assigned scope) — flagging as an additional data point for whichever path
(a/b/c) the operator ultimately green-lights, and as corroboration that re-enabling the option-(a) lease (or resolving
via (b)/(c)) is likely to restore a large volume of currently-completely-missing recent CeFi capture, not just reduce
noise in historical `attempted_failed` counts.

### 2026-07-13 — CEFI cluster of the 452-shard clean re-sweep, FORCE-leg failures (data_pipeline_e2e_check_2026_07_10.md

todo 25 triage, 8-venue assigned slice)

Triaging the 2026-07-13 clean re-sweep's remaining CEFI genuine failures (`BINANCE-DELIVERY` all 7 data_types, `OKX`
liquidations, `BYBIT-SPOT` trades, `COINBASE-FUTURES` derivative_ticker/liquidations, `BITFINEX-SPOT` trades,
`KRAKEN-FUTURES` derivative_ticker/liquidations/trades — 18 MTDS shard-jobs), pulled the REAL `run.log` for every
FORCE-leg VM via `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`. **Every single one
shows the identical, byte-for-byte signature already documented here**: dozens-to-hundreds of
`Tardis HTTP 403 code=274 concurrent-IP-lock` warnings across every per-symbol request, ending in
`TardisAdapter.download_batch: <venue> 2026-07-09 — 0 records` → `SHARD_INCOMPLETE ... missing: ['<VENUE>']`. Exact
per-VM 403-hit counts: BINANCE-DELIVERY book_snapshot_5=52/52, derivative_ticker=52/52, liquidations=52/52,
perp_funding=52/52, options_chain=3(before shard-incomplete), futures_chain=16; OKX liquidations=2; COINBASE-FUTURES
derivative_ticker=330/330, liquidations=330/330; BITFINEX-SPOT trades=280/280; KRAKEN-FUTURES derivative_ticker=646/646,
liquidations=646/646, trades=646/646. **BYBIT-SPOT trades** — the original sweep recorded this force leg as
`vm_not_success:vm_self_deleted_no_exit_status` with **zero run.log ever uploaded** (a genuinely different, ambiguous
symptom, not itself a 403). Re-verified fresh (2026-07-13, real VM
`mtds-backfill-cefi-pipelinecheck-20260713-151125-865522`, day=2026-07-09): this time the VM DID upload a real run.log,
and it shows the identical `Tardis HTTP 403 code=274 concurrent-IP-lock` pattern across hundreds of symbols (`TNSRUSDT`,
`TWTUSDT`, `USTCUSDT`, `VANAUSDT`, ... `VIRTUALUSDT`, etc.) — so BYBIT-SPOT:trades is ALSO genuinely blocked by this
same lock; the original run's "self-deleted, no log" was a one-off log-upload-timing flake (VM crashed/completed before
`heartbeat_daemon.py`'s uploader loop got its first tick), not a distinct, reproducible bug in its own right. **No new
code action needed for any of these 18 shards** — all corroborate this already-tracked, still-open P0 finding; not
individually diagnosed further. (repo: market-tick-data-service — corroboration only, no new commit)

### 2026-07-13 — OPERATOR ENABLEMENT DECISION: pilot wave with the lease ON; single-VM lease operation already live

Operator ruled (interactive session, 2026-07-13): **run the first fully-lease-enabled wave on a small venue/year slice**
(every VM in the wave gets `TARDIS_CONCURRENCY_LEASE=1` + the shared control bucket), confirm the staggered
lease-acquisition ordering in per-VM logs, then enable fleet-wide. The G4 re-run stays gated until after that pilot.

State observed same session: the production control object **already exists and is actively held** —
`gs://config-store-central-element-323112/_tardis_concurrency_lease/lease.json`, holder
`cefi-okx-swap-2022-light-20260713-103002:8192:d6370b59` (acquired 17:49:47Z, 900s TTL, renewing) — i.e. the running
CeFi backfill VM was launched lease-enabled and single-VM lease operation is live in production. The 4 lock-holding
`cefi-binance-futures-2020/2021` VMs from the earlier corroborations are TERMINATED. The multi-VM serialization proof
(the pilot wave proper) needs either okx-swap's completion or its inclusion: a monitor is armed on okx-swap's
termination; the pilot launches into that window with 2+ VMs on a small slice
(`TARDIS_CONCURRENCY_LEASE=1 TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-central-element-323112`).

### 2026-07-13 (~20:02Z) — PILOT WAVE LAUNCHED (2 lease-enabled VMs, solo window)

okx-swap completed/self-deleted (~19:47Z) opening the solo window; launched the operator-approved pilot:
`TARDIS_CONCURRENCY_LEASE=1 TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-central-element-323112 VENUES="BITFINEX-SPOT BYBIT-SPOT" YEARS=2025`
→ `cefi-bitfinex-spot-2025-heavy-20260713-200213` + `cefi-bybit-spot-2025-heavy-20260713-200213` (both metadata-stamped
with the lease vars, verified in the launch plan). Early evidence (~30 min in): both VMs uploading real capture chunks
with **zero `code=274` lines** — CeFi Tardis capture is flowing again on this wave (the first non-403 batch_tardis
capture since the 2026-06-04 write-collapse this doc documents). Lease-acquisition ordering evidence pending the first
KEYED fetches (free/day-1 fetches don't take the lease by design); a monitor is following the wave to completion. G4
re-run stays gated on the pilot's outcome.

### 2026-07-13 (~20:40Z) — pilot 1 HONEST OUTCOME: inconclusive (bad slice); pilot 2 launched

Pilot 1 (`BITFINEX-SPOT`/`BYBIT-SPOT` 2025) is **inconclusive for the lease mechanism**: every processed date logged
`1 skipped (no instruments)` — instruments-service's catalog has NO instruments for those venue/2025-date cells, so no
keyed Tardis call ever fired; the zero `code=274` count and zero lease-log lines are both trivially explained (nothing
to serialize), NOT lease evidence. Both VMs exited 137 after ~35 min — consistent with the stall watchdog
(`STALL_PROGRESS_REGEX=uploaded`, and nothing uploads on an all-skipped run), and the stale okx-swap `lease.json` was
never stolen (confirming no acquisition was ever attempted). Corrective: the pilot slice must be a venue/year with real
catalog coverage. **Pilot 2 launched 20:42Z**: `VENUES="BINANCE-FUTURES" YEARS="2024"` (heavy+light = 2 lease-enabled
VMs, `cefi-binance-futures-2024-{heavy,light}-20260713-204215`, all tarballs verified current at launch) —
BINANCE-FUTURES 2024 has known instrument coverage (39.9% of its af rows are 403s, i.e. real keyed fetch history).
Monitored to completion for staggered lease acquisition + code=274 counts.

### 2026-07-13 (~21:25Z) — pilot 2 ALSO all-skip; root cause is upstream of the lease (new P0 filed); pilot parked

Pilot 2 (`BINANCE-FUTURES` 2024 — a venue/year with weeks of real backfill history) hit the IDENTICAL
`NO INSTRUMENTS FOUND` honest-skip on every date; both VMs stall-killed (exit 137). This is NOT a slice problem: CeFi
per-(venue,date) instrument resolution is returning empty fleet-wide while the CeFi instruments availability index is
being actively rewritten by the ASTER bucket-migration workstream — filed as
`cefi_backfill_no_instruments_found_all_venues_2026_07_13.md` (P0). The lease mechanism remains UNEXERCISED in
production multi-VM conditions (no keyed call ever fired in either pilot); re-run the pilot on the SAME approved slice
once instrument resolution is confirmed healthy. Zero `code=274` in both pilots is NOT lease evidence.

### 2026-07-13 (~23:35Z) — PILOT OBJECTIVE MET by the first production lease-enabled wave; no dedicated pilot needed

After the instrument-resolution P0 fix shipped (`market-tick-data-service@0da8be67`, tarball `01927647`), my pilot-3
launch was correctly ABORTED by the launcher's running-VM guard: another session had already launched a full **4-VM
`cefi-bitget-futures-{2024,2025,2026}` wave at 23:15Z — lease-enabled** (`TARDIS_CONCURRENCY_LEASE`/`_BUCKET` confirmed
in VM metadata). Direct evidence from that live wave:

- `cefi-bitget-futures-2024-heavy-…/run.log`:
  `Tardis lease ACQUIRED by cefi-bitget-futures-2024-heavy-20260713-231539:8152:b7ae606e (bucket=config-store-… obj=_tardis_concurrency_lease/lease.json, attempt 1)`
  — the shipped lease acquiring in production, multi-VM.
- `lease.json` holder observed rotating on renew (acquired_at 23:35:20Z > the 23:20 acquisition line — renewer live).
- **Zero `code=274` lines across the wave so far** — the first multi-VM CeFi Tardis wave without concurrent-IP lockouts
  since this doc was filed.

This satisfies the operator's 2026-07-13 pilot ruling (first fully-lease-enabled wave on a real slice, staggered
acquisition observed, no lock 403s) via a REAL production wave rather than a synthetic pilot. Remaining on this doc: the
`[DATA] P1` G4 re-measurement once real waves have run long enough to accumulate a post-fix af census — the lock
mechanism itself is now production-verified. Pilots 1/2's all-skip failures were the (now-RESOLVED) instrument-
resolution P0, not the lease.

---

## RECURRENCE — 2026-07-14T02:00Z: BITGET-FUTURES 6-VM wave launched WITHOUT the lease, all 6 failed

The 2026-07-13T23:15Z BITGET-FUTURES relaunch (`cefi-bitget-futures-{2024,2025,2026}-{heavy,light}-20260713-231539`, G4
Re-Verification Run #5 in `mvp_backfill_cefi_tick_v10_2026_06_27.md`) ran 6 parallel VMs with the lease NOT enabled
(default-OFF) — every shard churned `Tardis HTTP 403 code=274 concurrent-IP-lock`, hit the 1800s no-progress stall
watchdog, exited `DEPLOYMENT_FAILED exit_code=137`, and self-deleted. Full evidence in that plan's 2026-07-14T02:00Z
CORRECTION entry. This is a process regression (parallel multi-VM launch without the lease), NOT a lease-mechanism
failure — the lease remains production-verified per the entry above. Follow-up hardening candidate: the launcher should
refuse (or force-serialize) >1 concurrent VM for Tardis-sourced venues unless the lease env is explicitly enabled, so
this shape can't be launched by accident a third time. — doc-reconciliation close-out check, 2026-07-14

---

## 2026-07-14T02:50Z — first lease-enabled multi-venue re-run wave: 403-lock class ELIMINATED under serialization (G4 evidence)

The todo-27 Tardis-locked CEFI cluster re-ran on real VMs (test-run force legs, day=2026-07-09) with
`TARDIS_CONCURRENCY_LEASE=1` via the new launcher passthrough (`deployment-service@a460f18`). Ground truth from per-VM
shards + the consolidated test index:

| Venue            | Result (real captures)                                                                                                                                                                                           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-DELIVERY | book_snapshot_5 21 instruments (75k–1.36M rows ea), derivative_ticker 21, liquidations 7, trades 4 (late-landed past the 900s checker budget)                                                                    |
| BYBIT-SPOT       | trades 523 instruments captured, 5,935,885 rows                                                                                                                                                                  |
| BITFINEX-SPOT    | trades passed (honest-empty day)                                                                                                                                                                                 |
| COINBASE-FUTURES | derivative_ticker 145 instruments captured, 13,254,508 rows; liquidations honest-zero (event data, SOURCE_RETURNED_ZERO)                                                                                         |
| KRAKEN-FUTURES   | derivative_ticker 307 captured (17,713,536 rows), trades 298 (480,148 rows), liquidations 6 (34 rows)                                                                                                            |
| OKX (bare)       | liquidations re-classed OUT of this cluster: fails `404 POST` (dataset-not-found) — the bare-OKX venue→adapter routing half of `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` Bug C, NOT the IP lock |

**Zero `Tardis HTTP 403 code=274` rows in every serialized lease-enabled run.** The single 403 burst observed
(BINANCE-DELIVERY trades, 01:32:56Z, 25 rows one-timestamp) coincided exactly with the RECURRENCE entry above — the
no-lease BITGET-FUTURES 6-VM wave churning until its stall-watchdog kill (~02:00Z); the lease-enabled VM's re-attempt
captured real trades at 01:53Z once that wave died. This closes "G4 re-measurement to the extent now unblocked": the
frozen pre-fix baseline census (2026-07-14T00:35Z, cefi-prd: 7,507,673 rows; attempted_failed 1,724,463 of which
1,291,037 = 74.87% carry `403`; 25 carry `code=274`) is recorded in `data_pipeline_e2e_check_2026_07_10.md`'s 2026-07-14
Progress Log entry; the full post-fix af-census delta re-measures after PROD-scale lease-enabled backfill waves re-run
the affected shards (owned by `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4). Operational lesson recorded: driver-level
concurrency still contends at the vendor even with the lease (two lease-enabled drivers + one no-lease foreign wave) —
run Tardis re-run waves strictly serialized; the launcher-refusal hardening candidate above stands.

---

## EMPIRICAL CONCURRENCY TEST — 2026-07-14T10:55Z (operator-directed "try and see", total connections < 1k)

Operator hypothesis: the academic licence permits ~100 concurrent same-region IPs and only dislikes ~2k total
connections. Test conditions were already live: a reduced 3-VM bitget relaunch
(`cefi-bitget-futures-{2025-heavy,2025-light,2026-heavy}-20260714-063737`, launched 06:37Z, lease OFF, default 16+4
streams/VM ≈ 60 total connections) had been running 4h15m at check time. Findings from the run.logs:

- **The lock is a REVOLVING single-active-slot, not a hard lockout**: 403 `code=274` fires continuously at N=3 IPs
  (~300-870/hr/VM, steady across 4h — so the multi-IP entitlement is NOT what this key exhibits), yet every VM also
  banks captures (~3,000 lines each) because the active slot keeps changing hands. Request efficiency ≈ 50-70%.
- **N=6 collapses, N=3 grinds**: re-reading the 2026-07-13T23:15Z 6-VM failure through this model — more contenders →
  shorter slot tenure → per-VM win rate below the 1800s progress threshold → stall watchdog killed all 6. At N=3 each VM
  wins often enough to live. Net throughput at N=3 ≈ 1.5-2.1 VM-equivalents, i.e. moderately better than one serialized
  VM, far below linear.
- **Single-IP control**: the pipelinecheck VM (01:59-02:03Z, sole IP) ran 26 Tardis requests with zero 403s.

Practical guidance (supersedes the 2026-07-14T02:00Z "ONE VM at a time" directive): 2-3 concurrent Tardis VMs is a
workable, mildly-net-positive shape with the lease OFF; >3 risks contention collapse; the lease (serialized) remains the
zero-waste option. The launcher-hardening candidate refines to: warn (not refuse) at 2-3 concurrent Tardis VMs,
refuse >3 unless the lease is enabled. Did NOT add more VMs on top of the live 06:37Z wave (risk of tipping it into
collapse). — doc-reconciliation session, 2026-07-14

> **🟡 SUPERSEDED 2026-07-25 (`/plan-reconcile`)**: the "2-3 concurrent Tardis VMs is workable" guidance immediately
> above is now stale. Per operator ruling 2026-07-16, documented in `CLAUDE.md` and
> `/codex/05-infrastructure/vm-launcher-runbook.md` § "Tardis Concurrent-VM Cap (HARD RULE)": **the cap is 1 concurrent
> Tardis-consuming VM, across BOTH clouds — the lease does NOT lift it, it AMPLIFIES the storm.** The operator's own
> note on this reversal: "the earlier cap-3 was measured on skip-scans, not real fetching" — i.e. this doc's 2026-07-14
> empirical test (which measured a bitget relaunch's request pattern) did not hold once real-fetching load was measured;
> N>1 in that later, real-fetching gap measured ~94% 403s + 37,212 FALSE `attempted_failed` manifest-corrupting rows +
> coverage going BACKWARD, while N=1 measured ZERO 403s. Do NOT action the "warn at 2-3 / refuse >3" launcher guidance
> above — the launcher-side control is now a hard 1-VM cap (`tardis-concurrency-guard.sh`), not a warn threshold. Scale
> via `TARDIS_MAX_CONCURRENT_DOWNLOADS`/`TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT` on the single VM, never via more VMs. A
> sibling doc, `cefi_consolidated_closeout_2026_07_18.md`, independently states the correct "N=1 Tardis cap, both
> clouds" six days after this doc's empirical test — this doc was simply never reconciled against that ruling until now.
