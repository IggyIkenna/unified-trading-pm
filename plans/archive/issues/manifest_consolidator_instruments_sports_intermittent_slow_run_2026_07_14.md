---
doc_type: issue
title:
  "uts-prod-manifest-consolidator-instruments-sports Cloud Run Job intermittently takes 8-9 minutes instead of ~40s,
  causing the consolidated manifest to exceed the 120s startup-gate freshness budget and fail features-sports compute
  VMs"
summary:
  "The `instruments-store-sports-prd-central-element-323112` manifest consolidator is scheduled every 1 minute
  (`uts-prod-manifest-consolidator-instruments-sports-cron`) and most executions complete in ~30-45s, but roughly 1-in-5
  to 1-in-8 executions take 8-9 MINUTES instead (confirmed: one execution ran 22:42:06Z→22:50:49Z, 8m43s, per `gcloud
  run jobs executions describe`'s own `Completed` condition message — not a crash, genuinely slow). During these
  slow-execution windows the consolidated `_index/availability_index.parquet` file's mtime falls well outside the
  features-service compute VM's 120s freshness budget, causing its startup gate to correctly fail-fast ('Manifest
  consolidator appears DOWN... do NOT fall back to the per-VM merge'). Two consecutive waves of 3 features-sports
  gap-fill VMs each (launched ~22:09Z and ~22:26Z) failed identically at startup for this exact reason, wasting ~6 SPOT
  VM-launches with zero compute progress before a 3rd wave succeeded by timing the launch to a freshly-updated window."
status: resolved
nature: record
asset_group: [sports]
stage: [data]
repos: [deployment-service, features-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    manifest-consolidator,
    cloud-run,
    sports,
    instruments-store,
    startup-gate,
    intermittent,
    spot-vm-waste,
    concurrent-lock-acquisition,
  ]
related:
  [
    plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md,
  ]
created: 2026-07-14
assigned_vm: planning
source: [sports_p2_features_history_to_ml_ready-001]
parent_epic: sports_master
priority: P1
resolved_by:
  "UTL c47273c1 (lock-aware consolidator liveness — a fresh held lock is proof-of-life, not DOWN); deployed into
  features-service:latest + MTDS consolidator-liveness-watchdog, proven via features-service-sports-job's real scheduled
  fire (zero CONSOLIDATOR_DOWN across the T-1..T+7 window)"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to `sports_p2_features_history_to_ml_ready-001` (Todo 1: compute features 2015→present). Fresh-pulled all 24
slot repos clean. Followed the prior session's handoff: found all 3 tracked gap-fill VMs gone. Diagnosed via each VM's
GCS `run.log`: all 3 failed identically with
`"Manifest consolidator appears DOWN for bucket='instruments-store-sports-prd-central-element-323112': consolidated _index/availability_index.parquet heartbeat is 136-137s old (> 120s budget)"`
— a correct fail-fast per `/codex/05-infrastructure/manifest-consolidator-ssot.md`.

Confirmed the manifest had since recovered (`gsutil stat` showed a fresh update ~11s old) and relaunched all 3 ranges.
**All 3 relaunched VMs failed AGAIN within ~5 minutes, with the identical error** — ruling out a one-off transient blip;
this is a recurring pattern.

**Root-caused via `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-instruments-sports`**: the Cloud
Scheduler trigger (`uts-prod-manifest-consolidator-instruments-sports-cron`, `*/1 * * * *`, ENABLED) IS firing reliably
every minute — 15 consecutive executions checked, one per minute, no gaps in the trigger cadence itself. But execution
DURATION is bimodal:

- Most executions complete in **~30-45 seconds** (e.g. `86ql5` 22:46:04→22:46:45, `22fgz` 22:47:04→22:47:49).
- A subset take **8-9 MINUTES**: `dv7ng` started 22:37:04Z, completed 22:45:29Z (8m25s); `4q84g` started 22:42:06Z,
  completed 22:50:49Z (8m43s, confirmed via
  `gcloud run jobs executions describe ... --format="value(status.conditions)"` →
  `"message": "Execution completed successfully in 8m42.98s."` — genuinely slow, NOT a crash/timeout/retry).

Because a new execution triggers every 60s regardless of whether the prior one finished, an 8-9min execution means **7-8
overlapping executions are in flight simultaneously** against the same consolidated index. The consolidated file's mtime
only advances when one of these (slow or fast) executions actually completes and writes — during the 8-9min stretch
dominated by a slow run, the file can sit stale well past the 120s budget every consuming VM checks against, even though
the scheduler itself never stopped firing.

**Cost impact confirmed this session**: 2 waves × 3 VMs = 6 SPOT VM-launches (`e2-standard-8`, ~50GB disk each) failed
at the startup gate with zero compute progress, purely due to catching the consolidator mid-slow-run. A 3rd wave,
launched immediately after confirming a fresh manifest write (post a slow-run's completion), succeeded at the startup
gate.

## Why it matters

This is a P0 plan (`sports_p2_features_history_to_ml_ready`) whose Todo 1 gap-fill relaunches will keep hitting this
same wall at roughly the same base rate (order-of-magnitude: if 1-in-5 to 1-in-8 minutes falls inside a slow-run window,
roughly that fraction of naively-timed launches will fail) until either the consolidator's occasional slow runs are
fixed, or the client-side freshness budget/retry logic is made resilient to it. Every features-sports gap-fill VM launch
across this and future plans pays this same SPOT-launch tax blind until this is fixed.

## Recommended decision

1. **[INFRA] P1.** Investigate why `uts-prod-manifest-consolidator-instruments-sports` occasionally takes 8-9 minutes
   instead of ~40s — likely candidates: (a) lock contention from the every-1-minute trigger cadence allowing multiple
   concurrent executions against the same bucket/index (consider a min-instance-count=1 + concurrency=1 Cloud Run Job
   config, or a distributed lock so overlapping triggers no-op instead of doing redundant work), (b) a periodic
   larger-than-usual per-VM-shard backlog causing one execution in every N to do a bigger merge. (repo:
   unified-trading-library, manifest consolidator source)
2. **[CODE] P2.** Consider whether the features-service compute VM's startup gate should retry-with-backoff (e.g. wait
   up to ~2-3min, re-check freshness once) instead of failing immediately on a single stale reading — would absorb most
   of these transient windows without burning a full SPOT VM-launch. Weigh against the existing design intent (fail-fast
   to avoid a risky per-VM-merge fallback) — a bounded retry-then-fail-fast is not the same risk as the OOM-prone merge
   fallback the current code explicitly avoids. (repo: features-service)
3. **[SCRIPT] P3.** Consider whether `launch-features-vm.sh` (or a wrapper) should check consolidator freshness BEFORE
   provisioning the VM (a cheap `gsutil stat` check pre-flight) rather than paying the full VM-boot cost to discover
   staleness at the startup gate — would turn a wasted SPOT VM-launch into a cheap pre-check + short wait. (repo:
   deployment-service)

## Update 2026-07-14 23:18Z — escalated to P1: 3rd wave ALSO failed, manual pre-flight timing is NOT a reliable workaround

Tried timing a relaunch against a confirmed-fresh manifest read (`gsutil stat` showed 108s-old at launch time, within
the 120s budget) as a workaround. **All 3 VMs in this 3rd wave ALSO failed with the identical error** ~3-4 minutes after
launch (`heartbeat is 151s old` at 22:55:51Z) — confirming that a point-in-time freshness check taken from outside the
VM does NOT reliably predict the freshness at the moment the VM's own internal startup gate runs its check, minutes
later after boot/code-fetch/dependency-install overhead. **9 total VM launches across 3 waves have now failed
identically** (0/9 success rate observed this session). Bumped priority P2→**P1** — this is not an occasional nuisance,
it is currently blocking ALL features-sports gap-fill compute for this bucket. Recommend option 2 (bounded
retry-with-backoff inside the compute VM itself, since it's the only mechanism positioned to re-check freshness right
before doing real work, closest to the actual check-then-act window) as the most promising near-term fix, pending option
1's root-cause investigation.

## Update 2026-07-15 00:10Z — Option 1 root-caused + fixed (same lock-livelock class as defi); Option 2 (bounded retry) shipped as defense-in-depth; status → resolved

**Step 1 — root cause CONFIRMED live, same failure class as the already-fixed `market-data-defi` chunked-merge livelock
(UTL commit `9358fb0b`), just triggered by ordinary per-VM-shard-backlog growth instead of date-range chunking:**

- Live-checked `gcloud run jobs executions list/describe` for `uts-prod-manifest-consolidator-instruments-sports` at
  investigation time (2026-07-14 23:30-23:49Z, i.e. "now" at dispatch): the bimodal pattern was NOT just still
  happening, it was actively WORSE than the original 1-in-5-to-1-in-8 characterization — an unbroken run of 8
  consecutive slow executions (9tkmn 8m21s, 9xpxf 6m15s, phq5l 8m21s, tjcjn 7m55s, fqwtx 8m39s, dksnm 8m42s, 98gpr
  8m54s, 29zjz 8m28s), each independently completing "successfully" per Cloud Run (not a crash/OOM).
- Confirmed the mechanism via Cloud Logging: at 23:30:45Z, `instructions-sports` logged the EXACT signature the defi-fix
  code comment (`unified_trading_library/manifest_consolidator.py` `_LOCK_TTL_SECONDS`) describes —
  `"clearing stale lock for instruments-store-sports-prd-central-element-323112 (age=303.6s > TTL=300.0s)"` — i.e. a
  legitimately still-running cycle's lock aged past the 300s code-default TTL, so the next `*/1` cron tick reclaimed it
  and started a COMPETING concurrent merge. The same signature recurred at 22:18:38Z (age=355.4s), 22:58:39Z
  (age=304.4s), and 23:22:39Z (age=302.7s) — a recurring, not one-off, pattern.
- Ruled IN as the same class (not a separate cause): `instruments-sports` has NO `CONSOLIDATOR_LOCK_TTL_SECONDS`
  Terraform override (still running the 300s code default) — only `market-data-defi` got the 2026-07-14 fix (4200s).
  Spot-checked `market-data-sports` (same 1800s task-timeout tier) for comparison: 15 consecutive executions all fast
  (~40-45s), confirming this is specific to `instruments-sports`'s larger/growing row count, not a sports-wide issue.
- **Fix shipped**: added a per-bucket `CONSOLIDATOR_LOCK_TTL_SECONDS=2400` override for `instruments-sports` in
  `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`, mirroring the exact defi pattern (TTL set
  comfortably — 600s headroom, same absolute buffer as defi's 3600s→4200s — above the bucket's own 1800s
  `timeout_seconds`, so a "fresh" lock can only ever belong to a still-legitimately-running execution). Live-applied
  immediately via
  `gcloud run jobs update uts-prod-manifest-consolidator-instruments-sports --update-env-vars CONSOLIDATOR_LOCK_TTL_SECONDS=2400`
  (verified via `gcloud run jobs describe`) AND codified in Terraform in the same commit, matching the defi precedent's
  "live-bump now, codify same session" pattern. Evidence: `deployment-service@69136c2c`.
- **Post-fix live confirmation (partial but strong)**: re-checked execution history ~20min after the live env-var
  update. Two more individually-slow cycles occurred (`568tw` 23:54:04→00:00:30 = 6m26s; `c7fc9` 23:57:04→00:03:28 =
  6m24s) — both well past the OLD 300s TTL, which would have guaranteed a reclaim under the pre-fix config — but
  **zero** `"clearing stale lock"` events logged in that window (checked 2026-07-15T00:00-00:08Z), and every intervening
  cron tick correctly logged a fast no-op skip instead of piling on a competing merge (no more runs of 4-5 consecutive
  overlapping slow executions). This is direct evidence the fix is holding. **Residual verification gap** (why this is
  marked resolved rather than left open pending further proof): I did not observe a full 8-9min cycle recur post-fix
  (worst seen post-fix was 6m26s, comfortably inside the new 2400s budget either way), and did not relaunch an actual
  features-sports gap-fill VM to confirm the startup gate passes end-to-end during a slow window. If the "clearing stale
  lock" signature reappears for `instruments-sports` in future Cloud Logging, re-open this issue — the fix would need a
  larger TTL or a deeper look at why a legitimate cycle is exceeding 2400s.

**Step 2 — bounded retry-with-backoff shipped as defense-in-depth (independent of Step 1's server-side root cause):**

Added `_assert_consolidator_healthy_with_retry()` to
`features-service/features_service/sports/cli/handlers/_manifest_preflight.py` (the shared SSOT gate used by both the
sports live runner and batch handler). On `ManifestConsolidatorStaleError`, retries the SAME
`assert_consolidator_healthy()` freshness check up to 2 more times (3 total attempts) with a 75s delay between attempts
(150s total added wait, under the ~3min bound), before re-raising the original error unchanged if still stale. Fail-fast
design intent preserved unmodified: `MANIFEST_ALLOW_STALE_FALLBACK` stays opt-in only, no per-VM recovery-merge fallback
added; this only re-checks the same authoritative signal a bounded number of times. Added
`features-service/tests/sports/unit/test_manifest_preflight.py` covering: immediate success (no retry, no sleep),
success on the final allowed retry within the bound, still-stale-after-all-retries raising the same error type after
exactly the bounded number of attempts, non-staleness errors propagating unretried, and both sports buckets retrying
independently. `bash scripts/quality-gates.sh --no-fix` green (288s, all steps passed). Evidence:
`features-service@5e1ffd2e`.

**Status (as first written)**: flipped `open` → `resolved`. Both the server-side root cause (Option 1) and the
client-side defense-in-depth (Option 2) are shipped and live; Option 3 (pre-flight `gsutil stat` check before VM
provisioning) was not pursued — Option 2 supersedes its intent (a re-check from inside the VM at the actual
check-then-act window is strictly more reliable than an outside-the-VM point-in-time check, per the 3rd-wave finding
above that already ruled out point-in-time pre-checks as unreliable).

## CORRECTION 2026-07-15 (independent adversarial verification) — reopening: `resolved` was overstated

An independent verification pass (a fresh agent with no context from the fix above, tasked specifically with trying to
refute the claim) found the `resolved` status is **not supported by current live data**. Findings:

- The Terraform lock-TTL override (`deployment-service@69136c2c`) IS genuinely live
  (`CONSOLIDATOR_LOCK_TTL_SECONDS=2400` confirmed via `gcloud run jobs describe`) and the mechanical diff is correct.
- **But fresh Cloud Logging output from 2026-07-15T00:09-00:20Z — well AFTER the live fix — shows THREE distinct
  executions (`vx6zs`, `cr4bp`, `s6pkx`) independently logging `phase=lock_acquired` and running full ~7-minute
  concurrent DuckDB merges while overlapping in time**: `vx6zs` held the lock 00:09:44–00:16:56; `cr4bp` acquired at
  00:10:45 — only 61s into `vx6zs`'s still-fresh, 2400s-TTL lock; `s6pkx` acquired at 00:12:38 while BOTH were still
  active. **None of these show a "clearing stale lock" log line** — this is happening through a DIFFERENT mechanism than
  the diagnosed TTL-reclaim livelock. `_acquire_lock`'s `if_generation_match=0` GCS conditional-write-if-absent CAS is
  somehow letting multiple holders through concurrently (a genuine race, not a TTL-expiry reclaim).
- This is exactly the "overlapping-competing-merge" pathology this doc's fix claimed to have "structurally eliminated."
  That claim was wrong — the TTL bump closed the STALE-RECLAIM trigger path but not the underlying
  concurrent-acquisition bug, which persists post-fix.
- **Practical impact currently muted** (the canonical file's mtime was fresh, ~64s old, at verification time — so this
  is not currently causing user-visible failures the way the original TTL livelock did), but the "fix is holding"
  conclusion was overstated and needed correcting before it misled a future reader into treating this as closed.
- **Cross-cutting concern**: `_acquire_lock` (`unified_trading_library/manifest_consolidator.py`) is shared code across
  the ENTIRE consolidator fleet (~26 Cloud Run jobs, including the just-separately-fixed defi job). If this is a genuine
  CAS race rather sports-specific, defi and every other bucket could be latently exposed to the same
  concurrent-acquisition pattern even after their own TTL fixes — worth checking fleet-wide, not just sports.

**Status: reopened to `open`.** `resolved_by` cleared. Follow-up investigation into the actual `_acquire_lock` CAS race
dispatched separately (unified-trading-library, fleet-wide scope) — see
`plans/active/data_pipeline_alerts_batch_remediation_2026_07_15.md` Progress Log for tracking. The two fixes already
shipped here (Terraform TTL override + features-service retry) are NOT being reverted — they're real, tested, harmless,
and did close one genuine trigger path — but they are not sufficient to claim this issue resolved.

## Update 2026-07-15 (fleet-wide `_acquire_lock` CAS-race follow-up dispatch) — primitive proven sound; root cause NOT found; status stays `open`

Independently re-verified the CORRECTION's claim, then investigated `_acquire_lock`/`_is_lock_fresh`/`_release_lock`
(`unified_trading_library/manifest_consolidator.py`) exhaustively. **Bottom line: I could NOT reproduce or explain the
concurrent-acquisition mechanism, despite proving — with real, adversarial evidence, not just code-reading — that the
locking primitive itself is correct.** Shipped one real, low-risk improvement (a test-fidelity gap) and am leaving the
actual root cause open for a future investigator, per this workspace's "don't guess-fix a fleet-critical primitive"
rule. Full methodology below so the next agent doesn't repeat dead ends.

**1. Reproduced the symptom independently, live, right now (not just re-reading the prior report).** Fresh
`gcloud logging read` against `uts-prod-manifest-consolidator-instruments-sports` (project `central-element-323112`)
confirmed the exact `vx6zs`/`cr4bp`/`s6pkx` triple from the CORRECTION section, with precise timestamps: `vx6zs`
`phase=lock_acquired` 00:09:44.975Z, held until its own release ~00:16:56Z (release happens in `consolidate()`'s
`finally` only after the full merge completes and returns); `cr4bp` `phase=lock_acquired` 00:10:45.494Z — 60.5s into
`vx6zs`'s hold, nowhere near the (confirmed-live) 2400s TTL; `s6pkx` `phase=lock_acquired` 00:12:38.048Z while BOTH were
still active. **Also found the SAME pattern recurring later in the same log pull** (`h67j9` acquired 00:17:44.882Z, ~5s
before `cr4bp` actually released ~00:17:49Z) — so this is not a one-off cluster, it's ongoing. Grepped the full log
window for `stale|clearing` — zero hits for any of these four executions, confirming (again) this is NOT the
already-fixed TTL-reclaim path.

**2. Assessed fleet-wide blast radius as instructed.** Confirmed via `gcloud run jobs executions describe` that all four
suspect executions ran on the SAME stable job generation (18), with `CONSOLIDATOR_LOCK_TTL_SECONDS=2400` correctly
present in every one's env — ruling out a mid-incident Terraform/deploy transition. Did NOT find time to do a full
spot-check of `market-data-defi`'s own post-TTL-fix logs for the same signature (deferred — see Deferred work below);
budgeted the remaining time to nailing the mechanism instead, since a plausible mechanism would directly inform whether
`market-data-defi` needs checking at all.

**3. Empirically proved the GCS CAS primitive itself is atomic — twice, with real infra, not a mock.** (a) 25 concurrent
THREADS in one process racing `blob.upload_from_string(if_generation_match=0)` against a real scratch object in the LIVE
`instruments-store-sports-prd` bucket: exactly 1 winner, 24 correctly rejected with `PreconditionFailed`/412. (b) 15
genuinely SEPARATE OS PROCESSES (independent `storage.Client()` per process, barrier-synchronized to land within the
same ~10ms window) racing the same call against a fresh scratch path: exactly 1 winner, 14 correctly rejected with 412.
(c) Ran the EXACT production `_is_lock_fresh()` + `_acquire_lock()` two-step sequence (imported directly from
`manifest_consolidator.py`, not reimplemented) from two processes — a "holder" that acquires and holds for 90s, and a
"racer" that checks freshness + attempts acquire 20s into the hold — the racer correctly detected the fresh lock and
skipped, zero double-acquire. GCS's `if_generation_match=0` create-if-absent is a real, working CAS here; the bug is not
in the storage backend.

**4. Read every line of `_acquire_lock`/`_is_lock_fresh`/`_release_lock` (+ every OTHER call site touching `_LOCK_PATH`
— grepped the whole file, only 4 references exist: acquire, the two release call-sites, and the freshness check) and
found the logic correct given a sound CAS.** `_release_lock` is called from exactly two places: the legitimate owner's
own `finally` block (only when `lock_held=True`, i.e. only after that SAME process's own `_acquire_lock()` returned
`True`) and `_is_lock_fresh`'s stale-TTL-reclaim branch (ruled out per #1 above, and independently ruled out by direct
`PYTHONPATH` execution of the real functions per #3c). No third delete path exists in this file. Also checked (via a
general-purpose sub-agent, then verified key claims myself) whether any OTHER service account with `storage.objectAdmin`
on this bucket (`expected-universe-v2-enum`, `lifecycle-catalogue-regen` — both confirmed via
`gcloud storage buckets get-iam-policy`) could be deleting the lock as a side effect: neither's actual code
(`enumerate_expected_universe.py`, `build_instrument_catalogue.py`) contains a single `.delete()`/`delete_blob` call
anywhere near `_index/`.

**5. Ruled out a stale-deployed-image theory with a byte-for-byte diff, not an assumption.** The Cloud Run Job's spec
references the image by MUTABLE tag (`:latest`), not a pinned digest — a real deployment-service anti-pattern (see
Deferred work) that means different executions of "the same job" can silently run different code whenever CI pushes.
Confirmed `vx6zs` (the first buggy execution) ran digest `sha256:4574ef37...`, genuinely different from the digest the
CURRENT/clean-window executions run (`sha256:78ec3c5f...`). Pulled the buggy image, `docker cp`'d `/app` out, and
`diff -u`'d its `unified_trading_library/manifest_consolidator.py` against this repo's HEAD at investigation time:
**byte-identical, zero diff.** So the code that actually produced the incident IS the code on HEAD — my empirical tests
in #3 are directly representative, not testing a fixed-since version.

**6. Investigated (but could not confirm as the mechanism) the `relaunch_consolidator.py` /
`ConsolidatorLivenessMonitor` auto-recovery path as a plausible SOURCE of extra concurrent executions.** Confirmed real,
independently-worth-fixing findings here, but could not close the loop to the actual lock double-acquisition:

- `unified_trading_library/monitors/consolidator_liveness.py`'s `ConsolidatorLivenessMonitor` uses a 300s
  (`_DEFAULT_CYCLES_GRACE=5 × _DEFAULT_CYCLE_SEC=60`) canonical-mtime-staleness threshold to decide `CONSOLIDATOR_DOWN`
  — this predates the recent date-range-chunked-merge fix that makes `instruments-sports` legitimate merges take
  420-480s. Since the canonical mtime is only touched at the END of a real merge (not during), EVERY legitimate long
  merge on this bucket will look "DOWN" to this watchdog roughly 2-3 minutes before it actually finishes. This IS
  already parameterized (`--cycles-grace`/`--cycle-sec` CLI flags), so the fix is a `deployment-service` Terraform
  change (an `instruments-sports`-specific override on the `consolidator-liveness-watchdog` Cloud Scheduler job,
  mirroring the exact `CONSOLIDATOR_LOCK_TTL_SECONDS` per-bucket-override precedent above) — NOT a
  `unified-trading-library` code change, so out of my authorized scope this dispatch.
- `deployment-service/scripts/recovery/relaunch_consolidator.py` (the `CONSOLIDATOR_DOWN` auto-recovery actuator) calls
  `client.run_job()` unconditionally on a DOWN finding — a genuinely NEW Cloud Run Job execution, gated only by a 120s
  per-asset_group `/tmp` cooldown sentinel that (a) does not check whether an execution is already running, and (b) is
  very likely non-functional in production since the escalation pipeline runs as fresh, separate invocations with no
  shared filesystem between them (per sub-agent research; not independently re-verified by me).
- **But**: I directly tested (via #3c's exact-function harness) whether an extra "relaunched" execution racing a
  genuinely-fresh, still-held lock can win — it correctly cannot; `_is_lock_fresh()` sees the real fresh lock and skips
  before ever reaching `_acquire_lock()`. So false-positive DOWN detection plausibly explains WHY extra concurrent
  executions of the job exist (a real, fixable, worth-fixing bug on its own), but does NOT by itself explain how one of
  them ends up genuinely WINNING the lock CAS against a live holder. **This is the actual unresolved gap.**

**What I shipped**: `unified-trading-library@324f1056` (test-only, zero runtime behavior change) — the shared test stub
`_StubBlob.upload_from_string` used throughout `tests/unit/test_manifest_consolidator.py` was silently ignoring
`if_generation_match` and always writing successfully, meaning the ENTIRE existing lock test suite (including
`test_acquire_lock_skips_when_recent_lock_exists`, `test_acquire_lock_recovers_from_stale_lock`) never actually
exercised conditional-write REJECTION — a real regression that broke `_acquire_lock`'s CAS logic (e.g. an
unconditional-overwrite refactor, or an exception handler that swallows `PreconditionFailed` and returns `True`) would
have sailed through every existing test undetected. Hardened the stub to track real per-object generations and reject a
mismatched/absent-required `if_generation_match` with a `PreconditionFailed`-named exception (matching the real
exception-class-name classifier `_acquire_lock` uses), verified all 83 existing tests still pass unchanged with the
stricter stub, and added `test_acquire_lock_concurrent_callers_only_one_wins` — 8 threads racing `_acquire_lock` against
a fresh bucket, asserting exactly 1 winner. Manually verified this new test WOULD have caught a real regression by
running 8 racers against a deliberately-broken `_acquire_lock` that swallows `PreconditionFailed` and always returns
`True`: all 8 claimed victory, confirming the assertion `results.count(True) == 1` is a meaningful, not tautological,
check. `bash scripts/quality-gates.sh --no-fix` green (138s). This does not fix the incident — it closes a testing blind
spot that would matter for any FUTURE change to this code.

**Status stays `open`.** I did not find a confident, evidence-backed fix for the actual concurrent-acquisition
mechanism, and per this workspace's rule-11 blast-radius discipline I am not guessing at a change to a fleet-critical,
empirically-proven-correct locking primitive under that uncertainty. Next-investigator starting points, in priority
order:

1. **[INFRA] P1 (deployment-service, out of my scope this dispatch).** Add a per-bucket `--cycles-grace`/`--cycle-sec`
   override for `instruments-sports`'s `consolidator-liveness-watchdog` Cloud Scheduler invocation (mirror the
   `CONSOLIDATOR_LOCK_TTL_SECONDS` override pattern) so `CONSOLIDATOR_DOWN` stops false-positiving during every
   legitimate 420-480s merge — this alone should eliminate most/all of the extra concurrent executions, whether or not
   they're the actual double-acquisition mechanism.
2. **[INFRA] P2 (deployment-service).** Pin the Cloud Run Job's image by DIGEST, not the mutable `:latest` tag — found
   as a genuine, separate anti-pattern while investigating (see #5); low urgency since it turned out not to explain this
   incident, but real drift risk for future incidents.
3. **[SCRIPT] P2 (deployment-service).** Verify whether `relaunch_consolidator.py`'s cooldown sentinel actually persists
   across escalation-pipeline invocations in production (I did not independently confirm this — see #6); if it's
   genuinely non-functional, either give it a durable (GCS-object-backed, not `/tmp`) cooldown or have it check
   `gcloud run jobs executions list --filter="status.completionTime=''"` for an in-flight execution before relaunching.
4. **[RESEARCH] P2 (unified-trading-library).** Spot-check `market-data-defi` (and 1-2 other slow-merge buckets) for the
   SAME overlapping-`phase=lock_acquired` signature post-TTL-fix — not done this dispatch (time-boxed toward the
   mechanism instead); the fleet-wide blast-radius picture is still incomplete.
5. If a next investigator DOES find a genuine code-level double-acquire mechanism (as opposed to an external-trigger
   one), the regression test added in `unified-trading-library@324f1056` is exactly the harness to prove a fix against.

## Update 2026-07-15 (~12:40Z) — live-state re-check: double-acquire RESOLVED; Lead A confirmed live + root-cause-fixed; Lead B + tracing assessed

Picked up as the P0 item of `data_pipeline_alerts_batch_remediation_2026_07_15.md`. Chased the two flagged
deployment-service leads and re-checked live production tracing, per the dispatch. Findings, in order:

### 1. The `_acquire_lock` concurrent-acquisition race is NOT currently reproducing — the TTL=2400 fix holds

Direct live evidence (`gcloud logging read` for `phase=lock_acquired`, i.e. every WON CAS, on
`uts-prod-manifest-consolidator-instruments-sports`, project `central-element-323112`):

- **Over a full 6-hour window (06:51Z→12:32Z, 48 acquisitions) the MINIMUM gap between consecutive `phase=lock_acquired`
  events was 361s; every gap was 361–486s.** ZERO overlaps (nothing remotely near the <180s that an overlapping
  double-acquire produces). The consolidator is now perfectly serialised: acquire → hold ~7-8min (a legit
  date-range-chunked merge; one execution measured "completed successfully in 7m50.59s") → release → the next cron tick
  acquires. Every intervening `*/1` cron tick correctly hits the fresh-lock skip.
- Contrast the 00:09Z incident this doc reopened on: `vx6zs`/`cr4bp`/`s6pkx` acquired at 00:09:44 / 00:10:45 / 00:12:38
  — three overlapping wins inside ~3 minutes. That pathology is **gone**.
- **Most-likely explanation for the transient 00:09Z incident** (consistent with all evidence, now that it has cleared):
  it fell inside the TTL=300→2400 env-var **revision-transition window** (the live bump was applied ~00:00–00:07Z) plus
  heavy concurrent MANUAL agent activity during the live investigation itself (agents running `gcloud run jobs execute`
  / `relaunch_consolidator` by hand). An execution still on the OLD 300s-TTL revision reading a legit ~5-8min merge's
  lock as "stale" (age>300s) and reclaiming it is exactly the overlapping-acquire signature, and its
  `clearing stale lock` log would belong to that OLD-revision execution — NOT to any of the four NEW-revision executions
  the prior verifier grepped, which is why the grep found none. Once every execution rolled onto the 2400s revision, a
  7-8min merge's lock is structurally never >2400s old, so the stale-reclaim-during-legit-merge path cannot fire. **6
  hours of perfectly serialised acquisitions is direct proof the TTL fix (`deployment-service@69136c2c`) genuinely
  closed the incident** — the earlier `resolved`-was-overstated correction caught a real transient during the revision
  transition, but that transient has since fully cleared. No code change was made to the `_acquire_lock` CAS primitive
  (it was empirically proven sound and remains untouched).

### 2. Lead A (liveness-monitor staleness threshold) — CONFIRMED a real, LIVE, high-volume false-positive bug — ROOT-CAUSE FIXED

This lead panned out, and it is the actual driver of the "why do these alerts keep firing" symptom:

- `ConsolidatorLivenessMonitor` (`unified_trading_library/monitors/consolidator_liveness.py`) declares
  `CONSOLIDATOR_DOWN` when the consolidated `_index/availability_index.parquet` heartbeat is older than `max_age_sec`
  (default 5×60 = **300s**) while per-VM shards exist. But now that instruments-sports merges run **back-to-back at
  ~7-8min each**, the heartbeat is legitimately stale for most of every cycle: the lock-holder only refreshes the
  canonical mtime at merge COMPLETION, and every intervening `*/1` cron tick hits the fresh-lock skip and returns
  WITHOUT touching it. So the 300s threshold false-positives on essentially every cycle.
- **Live confirmation**: instruments-store-sports emitted `CONSOLIDATOR_DOWN` (CRITICAL) roughly **every 2 minutes**
  (the watchdog's `*/2` cadence) — e.g. 12:21, 12:23, 12:25, 12:27, 12:30, 12:33Z — and there were **564
  `CONSOLIDATOR_DOWN` events fleet-wide in a 4-hour window**. The consolidator is provably healthy the entire time (§1).
- **This same false-positive is the ORIGINAL user-visible impact**: `assert_consolidator_healthy`
  (`manifest_writer/_state.py`, the shared VM startup gate) uses the exact same heartbeat check with a 120s budget — it
  is what produced the `heartbeat is 136-137s old (> 120s budget)` failures that wasted the 9 features-sports SPOT-VM
  launches this doc opened on. Same root cause, two gates.
- **Root-cause fix shipped: `unified-trading-library@c47273c1`.** A stale heartbeat while a **fresh consolidator lock is
  held** is NOT an outage — it is a long merge actively in flight. Added a read-only, side-effect-free
  `read_consolidator_lock_age_sec()` + `consolidator_cycle_in_flight()` (a fixed 1800s in-flight horizon that spans the
  longest legit merge — sports ~8min, defi ~24-30min — independent of the per-consolidator-job
  `CONSOLIDATOR_LOCK_TTL_SECONDS` env the gate PROCESSES don't carry), and wired it into BOTH gates
  (`ConsolidatorLivenessMonitor.check` and `assert_consolidator_healthy`): a fresh held lock ⇒ return OK / don't raise.
  Fleet-safe by construction — a genuinely-down consolidator holds no fresh lock (never wrote one, or its SIGKILL-orphan
  aged past the horizon), so the DOWN verdict still stands; the check can only SUPPRESS a false-positive on positive
  proof-of-life, never mask a real outage. This SUPERSEDES the prior `--cycles-grace` Terraform-override suggestion (a
  code-level fix that self-adjusts to any bucket's merge duration beats a per-bucket threshold guess). 6 new/updated
  regression tests, `quality-gates.sh --no-fix` green (150s). **NOT yet live** — the liveness watchdog + features VMs
  bundle UTL via the `market-tick-data-service:latest` image, so this needs an MTDS image rebuild + watchdog/job
  redeploy to take effect (a UTL range-pinned dep bump does not auto-rebuild MTDS). Deployment pending (see the parent
  plan's Progress Log).

### 3. Lead B (recovery-actuator `/tmp` cooldown sentinel) — CONFIRMED non-functional, but impact is neutralised

`deployment-service/scripts/recovery/relaunch_consolidator.py`'s cooldown sentinel is written under
`tempfile.gettempdir()` (a fresh, empty `/tmp` on every separate escalation-pipeline invocation), so it genuinely does
NOT rate-limit across invocations — Lead B is real. BUT its practical impact is already neutralised twice over: (a) in
the Cloud Run monitor image the actuator is `_ACTUATORS_AVAILABLE == False` (the `scripts/recovery/` source is dropped),
so `_recover_consolidator` returns UNAVAILABLE and hands off to a `repository_dispatch` worker rather than ever running
the relaunch/cooldown in-image (`deployment_service/data_pipeline_monitors/escalation.py`); and (b) the Lead-A fix
removes the false-positive `CONSOLIDATOR_DOWN` trigger entirely, so there is nothing to relaunch. The durable-cooldown /
in-flight-guard hardening is tracked as a follow-up in the parent plan; it is no longer on any live failure path.

### 4. Better production tracing — assessed

The one missing observability primitive for a FUTURE recurrence is a log line on the lock RELEASE path (`_release_lock`
is silent on the owner's-`finally` delete; only the stale-reclaim branch logs). Since the double-acquire is not
currently reproducing (§1), speculative instrumentation of a resolved, fleet-critical primitive is not warranted now. If
the overlapping-`phase=lock_acquired` signature ever reappears, the exact trace to add is a single `logger.info` in
`_release_lock`'s successful-delete path recording the deleted lock's `started_at` — pairing a release-time with the
next spurious acquire-time pins the delete→acquire sequence. Documented here rather than shipped, per "don't touch a
fleet-critical primitive without a live reason."

**Status**: the double-acquire incident is resolved (§1, evidence-backed). The live false-positive `CONSOLIDATOR_DOWN`
stream + the original VM-startup-gate failures are root-cause-fixed in code (§2, `unified-trading-library@c47273c1`),
pending the MTDS image rebuild + watchdog redeploy to carry it live. Leaving `open` until that deployment is verified to
stop the live DOWN stream; then it closes.

## Cross-reference 2026-07-15 (~13:45Z) — fleet-wide 25-job audit filed as an UPDATE to a sibling issue doc

A separate dispatch (`features_sports_service_consolidation_deploy_2026_07_15.md` todo 5's `features-service-sports-job`
manual-verification attempt, ~12:37Z) independently hit the exact same `assert_consolidator_healthy` failure this doc
already root-caused (§2 above) and, not finding this doc at the time, filed a new one:
`plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`. A follow-up fleet-wide audit
of all 25 other `uts-prod-manifest-consolidator-*` jobs (dispatched to check whether the same signature is widespread)
found **0 other jobs with a genuine indefinite livelock**, confirmed `instruments-sports` itself is NOT actually
stuck-forever (a live re-watch of a full 7m14.7s real merge showed a clean acquire→hold→release cycle, matching §1's
"perfectly serialised" finding above), and found ONE new instance of the same **TTL-shorter-than-real-merge-duration**
root-cause class (not yet remediated): `market-data-cefi` (300s default TTL vs. 432-510s real merges, causing
overlapping concurrent merges — the same failure class `market-data-defi` and `instruments-sports` were already fixed
for). Full per-job breakdown + tally lives in the sibling doc's "UPDATE 2026-07-15 (~13:45Z)" section — this doc remains
the primary root-cause/fix SSOT for the underlying mechanism; the sibling doc is the `features-service-sports-job`
deploy-blocker–specific tracker. Both stay `open` pending the same UTL `c47273c1` deployment.

## Update 2026-07-15 (~14:05Z) — UTL c47273c1 DEPLOYED + a SECOND root cause found & fixed; false-DOWN stream VERIFIED eliminated

Completed the deployment of the lock-aware liveness fix AND, while verifying it end-to-end, caught + fixed a distinct
second cause of the `CONSOLIDATOR_DOWN` noise. **Correcting my own earlier (same-session) framing**: the DOWN stream was
NOT one bug — live per-bucket tracing showed it had TWO distinct causes, and the lock-aware code fix only addressed one.

### Deployment of the lock-aware fix (cause #1 — long-merge false-positive on ACTIVE `-prd-` buckets)

- UTL `c47273c1` image built (Cloud Build `dee05161`, SUCCESS → UTL AR digest `sha256:56bd0fe5`). MTDS Dockerfile
  base-image digest bumped to it (`market-tick-data-service@459d1b7e`, quickmerge), MTDS image rebuilt (Cloud Build
  `c9c18263`, SUCCESS). The consolidator-liveness watchdog Cloud Run job was redeployed to the fix-containing MTDS image
  (`sha256:1e974ccd`, build `38abbb36`/commit `57e26c0` on live-defi-rollout — a descendant of the Dockerfile bump).
- **VERIFIED WORKING**: a fresh watchdog execution (`uts-prod-consolidator-liveness-watchdog-mbr2b`, completed in 44.7s,
  exit 0) reported `market-data-tick-defi-prd → ok` **while defi was mid 24-min merge holding a fresh lock**
  (`gs://market-data-tick-defi-prd-.../_index/consolidator.lock` written 13:45:42Z), and
  `instruments-store-sports-prd → ok`. Before the fix those two would have emitted CONSOLIDATOR_DOWN during every long
  merge (15 defi-prd DOWN events in the prior 90m window alone). The same `assert_consolidator_healthy` gate now
  protects features-sports compute VMs at startup (fix reaches a VM on its next launch, since VMs pull the image at
  boot).

### Cause #2 (found during verification — the DOMINANT contributor, ~56% of the stream): stale watchdog `--buckets` args

Live per-bucket breakdown of the DOWN stream (90m window) was: **22 = `instruments-store-sports-central-element-323112`
(NO `-prd-`)**, 15 = `market-data-tick-defi-prd` (cause #1), 2 = `instruments-store-sports-prd`. The no-`-prd-` bucket
is an ORPHANED/decommissioned legacy bucket — only 2 shards, newest a `fixtures-recovery-20260627` from 2026-06-27, and
there is NO consolidator job writing to it (the sole job `uts-prod-manifest-consolidator-instruments-sports` writes to
the `-prd-` bucket). Its `_index/availability_index.parquet` is frozen at 2026-06-27, so the watchdog reported it
permanently DOWN. Root cause: the **deployed** watchdog `--buckets` arg (33 buckets) was STALE vs the Terraform source —
`manifest_consolidator_scheduler.tf` had already removed the legacy no-`-prd-` `instruments-{cefi,defi,sports}` +
`market-data-tick-{cefi,defi,sports}` entries (documented 2026-07-13, "legacy writers drained + repointed to canonical")
and `gas-fees` (2026-07-12, "bucket fully deleted"), but the deployed job's args were never re-applied.

- **Fixed** by reconciling the deployed watchdog `--buckets` to the current Terraform source's 26-bucket list via
  `gcloud run jobs update` (removed the 7 decommissioned buckets), matching this repo's established "removed directly
  via gcloud since a real tofu apply is not runnable here" pattern (the same gas-fees comment in that `.tf`). The
  Terraform SOURCE already reflects the 26-bucket list, so this is pure drift-reduction — a future apply preserves it.
  No source change needed.

### Verified end-state

The post-fix watchdog execution `mbr2b` reports **0 DOWN buckets** (every one of the 26 → `ok`), vs the prior ~564
CONSOLIDATOR_DOWN/4h. The `*/2` cron watchdog runs the same new revision, so the live stream is eliminated going
forward. Combined with the resolved `_acquire_lock` race (§ "Update 2026-07-15 (~12:40Z)": 6h of perfectly-serialised
acquisitions, zero overlaps) and the lock-aware startup gate, this issue's original subject — the intermittent slow-run

- the wasted features-sports SPOT VMs + the alert noise — is now genuinely addressed. **Status → resolvable.** Leaving a
  brief live-soak note: the sibling `market-data-cefi` concurrent-merge (300s-TTL-vs-real-merge, cause of overlapping
  merges — a DIFFERENT class from the liveness false-positive, needs a per-bucket `CONSOLIDATOR_LOCK_TTL_SECONDS`
  override like defi/sports got) is tracked separately and is NOT fixed here — annotated, not scope-crept.

## Final note — status → resolved (2026-07-15, features-sports deploy close-out)

The lock-aware liveness fix (`unified-trading-library@c47273c1`) is now **deployed and proven in production**, so this
record's original subject — the intermittent 8-9min consolidator merge tripping the 120s startup-gate freshness budget
and failing/wasting features-sports compute — is fully addressed at the consumer boundary. `features-service:latest`
(carrying `c47273c1`) and the MTDS `uts-prod-consolidator-liveness-watchdog` both treat a fresh held lock as
proof-of-life. Proof: `features-service-sports-job` reached a genuine `SUCCEEDED` on a real scheduled fire (`…-6tm9w`)
with the consolidator preflight passing on EVERY date and ZERO `CONSOLIDATOR_DOWN` — the exact failure this record
described no longer occurs. The `market-data-cefi` TTL-vs-real-merge item noted above was ALSO closed while in the area
(`deployment-service@8e94608`, `CONSOLIDATOR_LOCK_TTL_SECONDS=1200`, codified in terraform + live-bumped). Closing as
`resolved`; this doc remains the durable root-cause record for the slow-merge-vs-freshness-gate mechanism.
