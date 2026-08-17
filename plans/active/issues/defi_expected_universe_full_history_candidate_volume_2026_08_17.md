---
doc_type: issue
title: DeFi --full-history expected-universe enumeration exceeds 100M candidates — cap/machine sizing genuinely unknown
summary: >-
  Three real production VM runs of enumerate_expected_universe.py --full-history --apply-write
  for asset_group=defi each hit the --max-writes-per-run halt-safety cap in turn (1M → 15M →
  100M), with no sign of leveling off — the true candidate count is unmeasured but exceeds
  100,000,001. Root cause is NOT a bug in per-instrument date-bounding (available_from is 100%
  populated with real dates) — it is that the defi catalog has grown to 78,802 instruments, 10x
  the "7,895" figure baked into launch-expected-universe-v2-vm.sh's own MACHINE_TYPE-sizing
  comment (now corrected in the same commit as this issue). The --full-history codepath's own
  code comment already flags it as "not implicated in the 2026-08-01 DeFi OOM — the daily cron
  never passes --full-history", i.e. genuinely untested at this scale.
status: blocked
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [defi, expected-universe, honest-coverage, halt-safety, oom-risk, escalation]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
  ]
created: "2026-08-17"
author: worker (slot-3, data_engineering craft)
assigned_vm: planning
parent_epic: defi_master
resolved_by:
source: >-
  Live execution of defi_satellite_ao_dispatch_batch16_2026_08_17.md todo "[IS] P1 Execute the
  LST catalogue + expected-universe v2 regen" — the operator-ruled (2026-08-12, reconfirmed
  2026-08-15) literal regen-script run.
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: "2026-08-17"
locked_by:
locked_since:
---

# DeFi `--full-history` expected-universe enumeration exceeds 100M candidates

## What I found

Executing `instruments-service/scripts/enumerate_expected_universe.py --asset-group defi
--enumerator-version v2 --full-history --apply-write` against real prod infra (per the
2026-08-12 operator ruling requiring a literal regen-script run, not just invariant-test
confirmation) via `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh` (extended
this session with a `FULL_HISTORY=true` env passthrough — `deployment-service@28272cafd3`):

| Attempt | VM | Machine | `--max-writes-per-run` | Result | Time to halt (post manifest-load) |
|---|---|---|---|---|---|
| 1 | `expected-universe-v2-defi-20260817-054923` | e2-standard-16 (64GB) | 1,000,000 (default) | `EXIT_STATUS=5`, 1,000,001 candidates | ~1 min |
| 2 | `expected-universe-v2-defi-20260817-060458` | e2-standard-16 (64GB) | 15,000,000 | `EXIT_STATUS=5`, 15,000,001 candidates | ~4.75 min |
| 3 | `expected-universe-v2-defi-20260817-062508` | e2-highmem-16 (128GB) | 100,000,000 | `EXIT_STATUS=5`, 100,000,001 candidates | ~25 min |

Each attempt reloads the manifest present-set from scratch (~7-11 min; `present=150,610,557`,
`captured=29,873,931` as of this run) before candidate generation even starts, and the
`--full-history` codepath (`enumerate_expected_universe.py` main(), the `if not full_history:`
branch's else-arm) drains the FULL per-day candidate generator into one in-memory Python list
before range-encoding — it is NOT chunked/streamed the way the bounded-window daily-cron path is
(that streaming fix, `V2_STREAM_CHUNK_SIZE`, was built specifically to fix the 2026-08-01 DeFi
OOM, but the code's own comment states the full-history branch was never exercised by that
incident and is untested at scale: "Not implicated in the 2026-08-01 DeFi OOM — the daily cron
never passes --full-history").

**Root-cause check performed** (to rule out a per-instrument date-bounding bug before assuming
this volume is "just how big defi is"): downloaded and inspected the live
`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` directly.
`available_from` is populated on **100% of 78,802 rows** (zero nulls) with a real date
distribution (2022-2026) — so per-instrument lifecycle-window narrowing IS working correctly, not
silently defaulting every pool to "since 2018". The volume is real, not a bounding bug.

**The actual stale assumption**: `launch-expected-universe-v2-vm.sh`'s own `MACHINE_TYPE`-sizing
comment said "defi is the largest at 7,895 instruments" (dated to whenever it was last measured).
The live catalog is now **78,802 rows** — a 10x undercount had been silently baked into every
sizing decision anyone made off that comment, including my own initial `MACHINE_TYPE=e2-standard-16`
choice for attempt 1/2. **Fixed in the same commit as this issue** (comment corrected, no other
launcher change).

## Why it matters

- The 2026-08-12/2026-08-15 operator ruling requires this literal regen run to close
  `defi_satellite_ao_dispatch_batch16_2026_08_17.md`'s `[IS] P1` todo (catalogue half already
  shipped `instruments-service@fd0d12a9`/regenerated 2026-08-15; only the
  `_index/expected_universe_ranges.parquet` companion — last real write 2026-07-03 — remains
  stale). That todo cannot honestly close until a run actually completes.
- Continuing to blindly multiply `--max-writes-per-run` (1M→15M→100M, each ~10-6x the last, each
  still insufficient) is now firmly in "guessing, not engineering" territory: each attempt costs
  real VM-minutes (13/17/29 min so far, escalating machine cost e2-standard-16→e2-highmem-16), and
  the NEXT guess (e.g. 300M-1B) risks a genuine OOM mid-`range_encode()` (which builds a groupby
  dict over the SAME already-materialized list, roughly doubling peak memory at the compaction
  step) rather than a clean halt-safety exit — a real OOM wastes the full run with zero
  diagnostic value, unlike the halt-safety path which at least reports the exact candidate count.
- This is the SAME code shape (unbounded full-history drain) that already caused the tracked
  `defi_v2_expected_universe_enumerator_oom_2026_08_01.md` 19-day OOM incident on the
  BOUNDED-window path before it was fixed with streaming — the `--full-history` branch was
  explicitly NOT covered by that fix and is not chunked at all.

## Recommended decision

Given the true candidate count is unmeasured but demonstrably >100,000,001 and climbing without
sign of a plateau, I recommend **one of**:

1. **(Preferred, cheapest)** Add streaming/chunked accumulation to the `--full-history` branch's
   candidate drain + `range_encode()` (mirror the `V2_STREAM_CHUNK_SIZE` fix already applied to
   the bounded-window path) — this is a real code change to `enumerate_expected_universe.py`,
   scoped to `instruments-service`, and removes the need to guess a cap at all. Not attempted in
   this session (out of a single P1 todo's scope; needs its own reviewed change).
2. **(Fallback, more $ but no code change)** One more attempt on a much larger machine
   (`e2-highmem-32`, 256GB) with `--max-writes-per-run` raised generously (e.g. 500,000,000) —
   accepts real OOM risk; if it OOMs, the ONLY signal recovered is "still not enough", another
   dead end with no candidate count learned (unlike halt-safety, which reports the count it hit).
3. **(Operator-decision)** Revisit whether the 2026-08-12 ruling's "must be a literal
   regen-script run" requirement can be satisfied by a narrower, still-correct scope for JUST the
   2 target denominator cells this todo actually needs
   (`(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` + `(AAVE, spot_asset, oracle_prices)`) —
   NOTE: `--data-types oracle_prices` narrowing was considered and REJECTED in this session
   because `_write_range_artifact`'s write is last-writer-wins over the WHOLE
   `_index/expected_universe_ranges.parquet` blob (not additive) — a narrower run would silently
   DROP every other data_type's previously-written range rows, a regression, not a safe shortcut.
   A genuinely safe narrower approach would need the write path to merge with the existing
   artifact instead of overwriting it (also a code change).

I have not picked one of these unilaterally — it's a genuine judgment call (accept more $ risk vs.
scope a code fix vs. revisit the ruling's literal-run requirement) that the operator/main agent
should weigh in on.

## Todos

- [x] ✅ [OPERATOR] P1. Decide which of the 3 options above to pursue — **answered via `BLK-2efccf37`
      (2026-08-17): option 1 (code fix), do NOT raise the cap further.** Operator's exact
      reasoning: 1M→15M→100M with no levelling-off against a root-caused real volume means the
      next guess very likely OOMs with zero diagnostic value; this is a code-fix task, not a
      cap-tuning task. Sequence directed: (1) file/confirm the P1 code todo — done, see below;
      (2) once shipped, retest `--full-history` with the CURRENT 100M cap (not higher); (3) if it
      still trips post-fix, that IS a genuinely new signal worth a fresh `/blocked`. The
      2026-08-12/15 ruling authorized the regen itself, not a specific implementation, so this did
      not need to go back to the operator a second time.
- [x] ✅ [IS] P1. Add streaming accumulation to `enumerate_expected_universe.py`'s `--full-history`
      branch — `instruments-service@6384984c`. Removed `main()`'s redundant
      `v2_absent: list[ExpectedRow] = []` materialisation; a new `counted_expected_rows()`
      generator (raises `_MaxWritesExceededError` mid-stream) streams candidates directly into
      `range_encode()`, enforcing the halt-safety cap without ever holding more than one row's
      worth of `ExpectedRow` at a time. 4 new unit tests (byte-identical-output-vs-old-shape +
      no-over-consumption-before-raise), all 245 tests in
      `tests/unit/scripts/test_enumerate_expected_universe_v2.py` green. Split from the original
      bundled todo (2026-08-17, worker slot-15) since the code half is genuinely done while the
      live-retest half below is not — see the next todo.
- [x] ✅ [IS] P1. Live-retest done: VM `expected-universe-v2-defi-20260817-071454` hit
      `EXIT_STATUS=5` at the EXACT SAME candidate count (100,000,001) as the pre-fix attempt —
      confirms the fix is deterministic/correct (no behavior change at the halt boundary) — and
      reached that count in ~12min vs ~25min pre-fix (~2x faster, strong signal memory pressure
      dropped substantially). Per operator sequencing step 3, this genuinely-still-tripping result
      was escalated fresh (`BLK-fbf334bd`) rather than silently raising the cap. Operator answered:
      run a scan-only measurement pass first (now safe post-fix, no write-side memory pressure
      difference) to learn the TRUE candidate count, then size one precisely-calibrated
      `--apply-write` run instead of continuing to guess. Scan-only pass launched: VM
      `expected-universe-v2-defi-20260817-074211` (`--scan-only 10000000000`) — see the fresh todo
      below for the actual regen completion, which is what the original `[IS] P1` todo's "Done
      when" always meant (this checkbox closes the LIVE-RETEST-PROVES-THE-FIX-WORKS sub-goal, not
      the full regen).
- [ ] [IS] P1. Complete the actual defi `--full-history --apply-write` regen: read the true
      candidate count from the scan-only pass (VM `expected-universe-v2-defi-20260817-074211`),
      set `--max-writes-per-run` to that count + 10-20% margin (operator direction via
      `BLK-fbf334bd`), launch the real `--apply-write` run, verify
      `_index/expected_universe_ranges.parquet`'s GCS timestamp moves past 2026-08-17 and the 2
      target cells (`CHAINLINK-ETHEREUM`/`AAVE` `oracle_prices`) confirm `expected_unattempted`.
      Repo: instruments-service. Closes `defi_satellite_ao_dispatch_batch16_2026_08_17.md`'s
      `[IS] P1` regen todo.
- [ ] [SCRIPT] P3. Audit every OTHER asset_group's `--full-history` viability under the same
      unbounded-drain code shape (cefi/tradfi/prediction/sports) before anyone else hits this same
      wall blind — sports in particular is flagged elsewhere
      (`asia_northeast1_c_spot_preemption_storm_2026_08_04.md`) as having a 448K+-instrument
      catalog, likely an even worse candidate-volume case. Repo: instruments-service. Done when:
      each asset_group's live catalog row count is measured and compared against its
      `--full-history` feasibility, findings folded into this issue or a fresh one per
      asset_group.

## Progress Log

- **2026-08-17 (worker, slot-3, data_engineering craft)**: filed after 3 real production VM
  attempts (evidence table above) all hit the halt-safety cap; root-cause-checked and ruled out a
  per-instrument date-bounding bug (available_from 100% populated); found + fixed the stale
  "7,895 instruments" launcher comment (actual: 78,802) in the same commit. Not resolving further
  autonomously — this is a genuine judgment call per the "Recommended decision" section, escalated
  via `/blocked` on the same turn.
- **2026-08-17 (same session, continued)**: operator answered `BLK-2efccf37` — option 1 (code
  fix), do not raise the cap further. Implemented the streaming fix (removed `main()`'s redundant
  full-list materialisation ahead of `range_encode()`; new `counted_expected_rows()` generator
  enforces the halt-safety cap mid-stream instead), added 4 unit tests, all 245 tests in the
  enumerator's test file green. Shipping + live retest against the existing 100M cap next.
- **2026-08-17 (worker, slot-15, backend_engineer craft)**: dispatched this same `[IS] P1` todo
  independently and implemented an equivalent streaming fix from scratch before discovering, at
  `quickmerge`-time, that slot-3 had already shipped the identical fix
  (`instruments-service@6384984c`, same root cause, same `counted_expected_rows()` approach, same
  4 test cases) moments earlier. Confirmed via `git pull --rebase --autostash` conflict + diff
  inspection that origin's landed version is functionally equivalent to mine; discarded my
  duplicate local changes (`git checkout HEAD -- <files>`, never shipped) rather than overwrite the
  already-landed commit. Corrected the stale "NOT YET shipped" claim on the todo above (code IS
  shipped) — checkbox stays unchecked because the todo's own "Done when" also requires the
  `--full-history --apply-write` live retest against the real 78,802-row defi catalog, which has
  NOT happened yet (a VM-launch task, out of backend_engineer craft scope for this session).
  Split the bundled todo in two: the code half is genuinely `[x]` done
  (`instruments-service@6384984c`); a fresh `[ ]` todo carries the still-open live-retest half so
  the checkbox honestly reflects only the part that's actually complete.
- **2026-08-17 (worker, slot-3, continued)**: completed the live-retest slot-15 flagged as open.
  VM `expected-universe-v2-defi-20260817-071454` hit `EXIT_STATUS=5` at the identical
  100,000,001-candidate count as pre-fix, ~2x faster (~12min vs ~25min) — fix confirmed
  deterministic/correct, memory pressure clearly reduced. Escalated fresh (`BLK-fbf334bd`) per the
  operator's own anticipated step 3 rather than guessing a new cap; operator directed a scan-only
  measurement pass first. Launched VM `expected-universe-v2-defi-20260817-074211`
  (`--scan-only 10000000000`) to measure the true candidate count safely; will size the real
  `--apply-write` run off its result next.
- **2026-08-17 (worker, slot-21, infra craft)**: dispatched the same live-retest todo
  independently and watched the SAME VM (`expected-universe-v2-defi-20260817-071454`, already
  RUNNING from an earlier turn of this session) to its terminal state via a background poller —
  corroborates slot-3's finding above byte-for-byte (`ENUMERATOR_FAILED`, 100,000,001 candidates
  vs the 100M cap, `EXIT_STATUS=5`). Discovered at quickmerge-time that slot-3 had already
  escalated (`BLK-fbf334bd`), gotten the operator's scan-only-first answer, and launched the
  scan-only measurement VM — no independent `/blocked` filed to avoid duplicating an
  already-answered escalation. Deferring to slot-3's Todos-section resolution above (the scan-only
  pass + calibrated-run plan) as the current path forward; no further action taken this session.
- **2026-08-17 (worker, slot-17, backend_engineer craft, IN PROGRESS — checkpoint before context
  compaction)**: dispatched the remaining `[IS] P1` regen todo. The original scan-only VM
  (`expected-universe-v2-defi-20260817-074211`) was SPOT-preempted mid-run at 08:04:36 with zero
  candidate-count signal recovered (confirmed via `gcloud logging read` audit-log
  `compute.instances.preempted`, not a code failure — its own log went silent after the manifest-load
  phase with the VM still nominally RUNNING per `describe`, which is what first looked like a stall).
  Relaunched (another slot got there first — `expected-universe-v2-defi-20260817-080605`, deferred to
  it rather than duplicate) on `ON_DEMAND=true MACHINE_TYPE=e2-highmem-16` to avoid a second silent
  preemption loss on a run with zero write-side checkpointing. **Scan-only result: TRUE CANDIDATE
  COUNT = 294,144,873** (`range_rows=267499`, `eu_days=288659526`, `written=0`,
  `run_id=enum-universe-defi-20260817-081015`, completed cleanly 09:22:04 UTC — ~2.94x the 100M cap
  that kept tripping halt-safety across 4 prior attempts). Deleted that VM after confirming clean
  completion via its `ENUMERATOR_COMPLETED` event (staleness confirmed by the log itself, not by
  heartbeat-age alone) to free the launcher's singleton lock. **Calibrated the real `--apply-write`
  run at `--max-writes-per-run 350000000`** (true count + ~19% margin, in the spirit of the operator's
  10-20% direction) and launched it — then discovered ANOTHER slot had independently launched the
  IDENTICAL command (`expected-universe-v2-defi-20260817-092709`, same asset_group/mode/cap) moments
  earlier; deleted my own redundant duplicate (`...092925`, still `STAGING`, zero writes had started)
  rather than risk two concurrent writers racing on the single non-additive
  `_index/expected_universe_ranges.parquet` target (the exact hazard the plan's own "Recommended
  decision" §3 already flagged for a *narrower*-scope write — the same last-writer-wins mechanism
  applies here to a full-scope duplicate). **`expected-universe-v2-defi-20260817-092709` is the live
  run of record** — SPOT-provisioned (not mine to change without re-duplicating), actively
  enumerating as of this checkpoint, being watched by an active session Monitor for both log-progress
  and a VM-status-flip (to catch a repeat preemption early rather than discovering it via silence).
  **Not yet done**: this checkbox stays `[ ]` until (a) the VM reaches `ENUMERATOR_COMPLETED` with
  `written>0`, (b) `_index/expected_universe_ranges.parquet`'s GCS timestamp is confirmed past
  2026-08-17, and (c) the 2 target cells (`CHAINLINK-ETHEREUM`/`AAVE` `oracle_prices`) confirm
  `expected_unattempted`, per the todo's own "Done when". **If this VM also gets preempted before
  finishing**: relaunch with `ON_DEMAND=true MACHINE_TYPE=e2-highmem-16 FULL_HISTORY=true` (same
  flags as the scan-relaunch above) — the 294,144,873 measurement + 350M cap are already known-good,
  no need to re-scan. **Lesson for future full-history VM babysitting**: a completed-but-`RUNNING`
  VM (process done, instance not self-terminating — this launcher has no auto-shutdown) silently
  keeps billing until manually deleted; check the run.log's own terminal event before concluding a
  VM is "stuck", don't infer state from `describe`'s STATUS field alone.
- **2026-08-17 (worker, slot-19, data_engineering craft)**: dispatched the remaining `[IS] P1`
  live todo (final regen). Live-reverified before acting: `_index/expected_universe_ranges.parquet`
  still `last_modified=2026-07-03` (no other slot had landed a write since), no
  `expected-universe-v2-defi-*` VM currently RUNNING. Found the scan-only pass (VM
  `expected-universe-v2-defi-20260817-074211`, relaunched as `-080605` since the first attempt's
  log tail was mid-run when checked) had already completed cleanly: **true candidate count
  294,144,873** → 267,499 range rows (288,659,526 EU-days, 1100x compaction), `exit_code=0`,
  self-deleted. Sized the calibrated `--apply-write` run at 294,144,873 × ~1.19 ≈ **350,000,000**
  (`--max-writes-per-run`), matching the operator's 10-20%-margin direction from `BLK-fbf334bd`.
  Launched `MACHINE_TYPE=e2-highmem-16 FULL_HISTORY=true bash
  deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh defi --apply-write 350000000`
  (same machine class the scan-only pass proved sufficient for the full 294M-candidate volume) →
  VM `expected-universe-v2-defi-20260817-092709`, confirmed RUNNING (SPOT) at launch. Watching to
  terminal state via a bounded background poller (3hr cap) rather than fire-and-forget; will record
  the before/after `expected_universe_ranges.parquet` timestamp + the 2 target cells'
  `expected_unattempted` confirmation here once it completes.
