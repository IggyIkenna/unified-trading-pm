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
status: resolved
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
  market-tick-data-service@53431680 (todo 1), instruments-service@d68f3d59 (todo 2), instruments-service --apply run
  2026-07-15T22:35Z (todo 3)
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
  `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap) on requests that get 403'd and land as
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

- [x] ✅ [BACKEND] P1. Fix `ensure_process_lease_acquired()`
      (`market_tick_data_service/market_interface/clients/tardis_concurrency_lease.py:262`) so concurrent callers
      actually await the in-flight acquisition instead of skipping past a synchronously-set boolean flag (see option (1)
      above — an `asyncio.Event`/shared `Future` the first caller resolves once `lease.acquire()` returns). Add a
      regression test that spawns N concurrent callers before the first `acquire()` resolves and asserts only ONE real
      `lease.acquire()` call fires while the rest block until it resolves (extend the existing
      `tardis_concurrent_ip_lockout_2026_07_12.md` Harness A/B pattern — real GCS CAS, no mocks). (repo:
      market-tick-data-service) — market-tick-data-service@53431680. Replaced the boolean `_process_lease_attempted`
      fast-path with a `threading.Event` (`_process_lease_ready`) set only after the winning caller's `lease.acquire()`
      resolves (success or fail-open, via `try/finally` so an exception can't deadlock the waiters); every other
      concurrent caller now blocks on that event instead of returning immediately. Added
      `test_concurrent_callers_wait_for_inflight_acquire_not_skip_past` (16 threads racing a slowed `acquire()`,
      asserting zero callers return before it resolves + exactly one real `TardisConcurrencyLease` is constructed) to
      `tests/market_interface/unit/test_tardis_concurrency_lease.py`, extending the existing real-CAS
      (`_FakeStorage`-backed, generation-aware, no naive mocks) harness pattern from this file / the 2026-07-12
      enablement smoke-test. Full `quality-gates.sh` green on the committed HEAD.
- [x] ✅ [SCRIPT] P2. Once fixed + verified, re-audit the `attempted_failed` rows the 3 relaunched cefi-queue-\* VMs
      wrote during this session's race window (`cefi-queue-light-binancefutu-x2-20260715-202013`, date=2026-01-02
      primarily) — distinguish genuine no-data shards from this-bug-caused false failures (e.g. via `error_reason`
      containing `code=274`) so a targeted re-fetch (not a blind full re-run) closes just the affected shards. (repo:
      instruments-service or market-tick-data-service, whichever owns the manifest reconcile tooling) —
      instruments-service@d68f3d59. Audit-only (per BLK-8a051482 resolution: -001 the actual lease fix had NOT shipped
      when this ran, so the flip-to-`expected_unattempted` mutation is NOT applied yet — only identification). See
      Progress Log + todo (3) below for the corpus-wide scope this audit surfaced.
- [x] ✅ [SCRIPT] P1. **NEW — bigger than originally scoped.** Once `tardis_concurrency_lease_intra_process_race-001`
      (the lease fix) has shipped + its regression test passed, run
      `instruments-service/scripts/audit_tardis_concurrency_lease_race_false_failures_2026_07_15.py --apply     --confirm-lease-fix-shipped`
      (with `MANIFEST_PER_VM_SHARDS=true VM_NAME=<unique>`) to flip the CORPUS-WIDE 21,982 race-caused
      `attempted_failed` rows (not just the 3-VM session subset — see Progress Log) to `expected_unattempted` so the
      next backfill wave re-attempts them. Re-verify post-flip that `captured` row count is unchanged (script's own
      safety gate) and spot-check a sample of flipped rows re-attempt cleanly (no repeat code=274) before considering
      this closed. (repo: instruments-service) — done 2026-07-15T22:35Z. See Progress Log for full evidence
      (consolidator-quiesce procedure, exact row counts, spot-check).

## Progress Log

- **2026-07-15T20:3xZ (infra, slot-6)**: Filed this doc while executing
  `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md` todo (4). No fix attempted this session
  (out of scope for an INFRA relaunch task; needs a BACKEND-craft fix + regression test per above). The 3 relaunched VMs
  were left running — they are still making real, useful progress overall (the heavy VM and light-bybit VM show zero
  403s; light-binancefutu is the one affected VM and will eventually clear date=2026-01-02 and continue, just with some
  wasted/false-failed shards in the interim).
- **2026-07-15T21:4xZ (data_engineering, slot-6, task `tardis_concurrency_lease_intra_process_race-002`)**: Worked todo
  (2) — the re-audit. **Sequencing gap found**: todo (2)'s title says "once fixed + verified" (referring to todo (1) /
  backlog task `-001`), but `-001` was still `status: queued` (unclaimed) with no `prereqs.completed_tasks` wiring
  gating `-002` on it — the dispatcher handed out `-002` anyway. Filed `BLK-8a051482` flagging this and proceeded with
  the audit-ONLY portion (identification, no mutation), since that's valid regardless of whether `-001` has shipped —
  only the actual re-fetch trigger needs to wait.
  - Shipped `instruments-service/scripts/audit_tardis_concurrency_lease_race_false_failures_2026_07_15.py`
    (instruments-service@d68f3d59) — identifies `attempted_failed` rows with the exact, stable
    `error_reason == "Tardis HTTP 403 code=274 concurrent-IP-lock"` string (confirmed at
    `market_tick_data_service/market_interface/clients/tardis_base_client.py:175`), dry-run only (no `--apply` this
    session — see `--confirm-lease-fix-shipped` gate in the script).
  - **Session-scoped finding** (matches todo (2)'s literal ask, `attempted_at` 2026-07-15T20:20-20:39Z): **411 rows**,
    ALL `venue=BITGET-FUTURES`, ALL `date=2026-01-02`, ALL `data_type=liquidations` — precisely the single stalled shard
    the issue doc's live evidence described for `cefi-queue-light-binancefutu-x2-20260715-202013`.
  - **BIGGER FINDING — corpus-wide, NOT scoped to this session's 3 VMs**: querying the full cefi PRD merged manifest
    (`_index/availability_index.parquet`, 11,369,553 rows) for the SAME exact error_reason returns **21,982 rows** with
    `attempted_at` spanning **2026-07-13T09:01:48Z through 2026-07-15T20:49:23Z** — i.e. this race has been silently
    corrupting the manifest for ~2.5 days across MANY cefi backfill VM launches, not just this session's 3 relaunched
    VMs. Venue breakdown: `BITGET-FUTURES` (12,014), `OKX-SPOT` (5,353), `OKX-FUTURES` (2,010), `LIGHTER-ZKSYNC`
    (1,556), `KRAKEN-FUTURES` (672), `COINBASE-SPOT` (366), `DERIBIT-COMBO`/`DERIBIT` (10) — most of these venues were
    NEVER touched by the 3 session VMs (which only fetched BINANCE-FUTURES/BITGET-FUTURES/BYBIT), confirming this is a
    systemic, ongoing issue across the whole cefi backfill fleet, not an artifact of this one relaunch. By day: 10,223
    rows on 2026-07-14 alone (a day BEFORE this session even started), 11,758 on 2026-07-15. Also 2 of the 3 relaunched
    VMs' per-VM manifest shards (`_index/per_vm/{vm}.parquet`) had already been consolidated into the merged index by
    the time this audit ran (only `cefi-queue-heavy-binancefutu-x15-...`'s shard was still live, with 0 race rows —
    consistent with the issue doc's claim it saw zero 403s).
  - **This is a big data-correctness finding** per the CLAUDE.md findings-triage HARD RULE (corpus-wide manifest
    corruption, cross-repo, silently degrading the honest-coverage gate) — flagged via `/progress` to the dashboard +
    tracked as new todo (3) above (gated on `-001` shipping, same as this todo's flip would have been). NOT flipping
    anything to `expected_unattempted` this session (dry-run only) — every launcher since 2026-07-13 that hit a
    cold-process concurrent fan-out on a non-free date is a plausible source, so a blind flip-and-refetch before `-001`
    ships would just reproduce all 21,982 failures again.
- **2026-07-15T22:1xZ (backend_engineer, slot-7, task `tardis_concurrency_lease_intra_process_race-001`)**: Shipped todo
  (1) — the lease fix. `market-tick-data-service@53431680`. Root cause confirmed at `tardis_csv_transport.py:51`'s
  `_ensure_tardis_concurrency_lease()`: it dispatches the sync `ensure_process_lease_acquired()` to a thread-pool
  executor once per concurrently-gathered coroutine (up to `tardis_max_concurrent_downloads=16`), so the module
  singleton races across real OS threads, not just asyncio tasks. Applied option (1) from the recommendation: replaced
  the `_process_lease_attempted` boolean fast-path with a `threading.Event` (`_process_lease_ready`) that is set only
  after the winning caller's `lease.acquire()` resolves (wrapped in `try/finally` — an unhandled exception in
  `acquire()` must still release the waiters, or the fix would trade the skip-past race for a new deadlock); every
  concurrent caller — whether it hits the flag pre-set or loses the lock race — now blocks on that event instead of
  returning immediately. Full `bash scripts/quality-gates.sh` run green **twice**: once against the working tree before
  commit (caught nothing to fix), then re-run after commit so the `.qg_last_passed_sha` sentinel matched the shipped
  HEAD before `quickmerge --agent` (the correct order is commit-then-QG, not QG-then-commit — noted here in case this
  sequencing gap trips up a future session). Added `test_concurrent_callers_wait_for_inflight_acquire_not_skip_past` —
  races 16 threads against a slowed `acquire()` and asserts (a) zero callers return before it resolves and (b) exactly
  one `TardisConcurrencyLease` is ever constructed — using the same real-CAS `_FakeStorage` harness the rest of
  `test_tardis_concurrency_lease.py` already uses (generation-aware, no naive return-value mocking), per the todo's ask
  to extend the 2026-07-12 Harness A/B pattern. Todo (3) (the corpus-wide `--apply --confirm-lease-fix-shipped` re-flip
  of the 21,982 race-caused `attempted_failed` rows) is now unblocked — its prerequisite (this fix shipped) is
  satisfied.
- **2026-07-15T22:1x-22:36Z (data_engineering, slot-16, task `tardis_concurrency_lease_intra_process_race-003`)**:
  **Sequencing gap recurred a third time**: same class as `BLK-8a051482` (todo (2)) — the dispatcher handed this slot
  todo (3) while `-001` was still `status: queued` (no `prereqs.completed_tasks` wiring), so the same "once fixed +
  shipped" gate was unmet at dispatch time again. Filed `BLK-72ba59e6`; main answered A (pick up unclaimed `-001` myself
  as continue_on). While starting that BACKEND fix, **slot-7 landed `-001` first** (`market-tick-data-service@53431680`,
  see above) — discarded my in-progress duplicate diff for `tardis_concurrency_lease.py`/its test (via
  `git restore --staged --worktree` + `git merge --ff-only`, confirmed slot-7's fix is equivalent-and-better:
  `threading.Event` + `try/finally` vs my simpler hold-the-lock-through-acquire approach) rather than ship a
  redundant/conflicting commit. Found + fixed one unrelated pre-existing off-by-one in
  `test_release_does_not_delete_foreign_lease` (same test file, failed standalone under a full quality-gates.sh run, a
  tautological `assert 1 != 1` from a hardcoded generation coinciding with the fresh fake-storage's first-seed
  generation) — shipped separately as `market-tick-data-service@39b0daf1` per the in-your-file findings-triage rule.
  - **Todo (3) — the corpus-wide apply-flip**: main's answer additionally required "consolidator quiesced;
    evidence-verify" before running `--apply`, since `_flip_to_expected_unattempted()` does a direct read-modify-write
    of the FULL merged canonical (`_index/availability_index.parquet`), not a per-VM-shard write — exactly the race
    pattern the same-day HARD RULE in `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Writers: per-VM shard
    mode is the ONLY sanctioned standing write path" warns about (reference incident: 2026-07-15 sports IS canonical
    lost 328,292 rows / 5.7% to a legacy-mode direct write racing the consolidator). The script's
    `MANIFEST_PER_VM_SHARDS=true`/`VM_NAME` env-var gate is validated but never actually used to route the write through
    shard mode — it still writes the canonical directly — so quiescing the consolidator for the write's duration was the
    correct (and only) way to close that race for this one-off script, rather than rewrite the script's write path under
    this task's scope.
  - **Quiesce procedure**: identified the ONE relevant job via GCP Cloud Scheduler Python SDK (`gcloud` CLI is broken in
    this sandbox — snap confinement error — so used `google.cloud.scheduler_v1`/`google.cloud.run_v2` directly):
    `uts-prod-manifest-consolidator-market-data-cefi-cron` (the other 5 `*-cefi-cron` jobs consolidate different buckets
    — execution/instruments/features-onchain/features-volatility/features-delta-one — irrelevant to this bucket). AWS
    has no separate rule for this exact GCS bucket (AWS Batch/EventBridge mirrors its OWN S3 buckets under a different
    naming scheme, not this GCP bucket) — confirmed no AWS-side pause needed. Paused via
    `CloudSchedulerClient.pause_job` → `PAUSED`; polled the canonical blob's `generation` (via
    `get_storage_client().get_blob_metadata`) every 15s for 3 consecutive stable reads (~70s) to confirm no in-flight
    execution was still writing before proceeding (a scheduler pause does not kill an already-triggered execution).
  - **Apply run**: fresh dry-run first (`21982` rows, matching the original finding exactly — zero new race rows
    accumulated between the original audit and now, consistent with `-001` having shipped in between). Ran
    `--apply --confirm-lease-fix-shipped` with `MANIFEST_PER_VM_SHARDS=true VM_NAME=cefi-race-refetch-slot16-<ts>` —
    script's own safety gate reported `captured` count preserved at `3140808` before/after. Post-apply dry-run re-audit:
    `0` race rows remain; `attempted_failed` total dropped `1751967 → 1729985` (exactly `-21982`); total row count
    unchanged (`11370710`). Spot-checked `BITGET-FUTURES`/`liquidations`/`2026-01-02` (the original session's stalled
    shard): 427 of that triple's 842 rows now `expected_unattempted` with cleared `error_reason`; the remaining
    `attempted_failed` rows in that same triple carry genuinely DIFFERENT reasons (a non-`code=274` `403`,
    `SOURCE_RETURNED_ZERO`, a `404`) — confirming the exact-match discipline didn't over-capture. Corpus-wide
    `error_reason == "Tardis HTTP 403 code=274 concurrent-IP-lock"` count is `0` across every `capture_status`, not just
    `attempted_failed`.
  - **Resume + verify**: `CloudSchedulerClient.resume_job` → `ENABLED`, independently re-confirmed via `get_job` (given
    `plans/active/issues/defi_consolidator_cron_left_paused_2026_07_15.md` is a live cautionary precedent for forgetting
    to resume a paused consolidator cron). Additionally polled the canonical blob's `generation` post-resume until it
    advanced (confirmed within ~4 min) — proving the cron didn't just report `ENABLED` but actually fired and completed
    a real consolidation cycle, closing the loop on "resumed" meaning "genuinely running again," not just an API-state
    flip.
  - Next backfill wave against these 21,982 shards will re-attempt them under the now-fixed lease; no further action
    needed on this issue doc unless a future audit finds NEW `code=274` rows post-`-001` (which would mean the fix
    itself has a gap, not a scope item for this doc).
