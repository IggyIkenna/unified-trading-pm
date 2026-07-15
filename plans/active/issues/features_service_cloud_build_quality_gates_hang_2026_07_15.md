---
doc_type: issue
title:
  "features-service Cloud Build hangs reproducibly (2/2) inside the quality-gates test step and hits the 1800s build
  timeout — the Dockerfile UTL-base-image digest bump (unblocking features-service-sports-job) is committed but the new
  image has NOT been built/pushed"
summary:
  "Dispatched to rebuild features-service against unified-trading-library@c47273c1 (lock-aware consolidator liveness
  fix) to unblock features-service-sports-job's manifest-consolidator preflight false-DOWN
  (plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md). The code fix itself is
  correct and shipped (features-service@7c2e4ef1 bumps Dockerfile ARG BASE_IMAGE_DIGEST to the UTL image confirmed via
  real `docker run` to contain the fix; local `quality-gates.sh --no-fix` passed green in 93s). But the
  features-service-build Cloud Build trigger only fires on push to `main` (not `live-defi-rollout`, where quickmerge
  lands), so it was manually triggered twice (`gcloud builds triggers run features-service-build
  --branch=live-defi-rollout`) against the correct commit. BOTH runs hung with ZERO log progress for the remainder of
  the build after printing quality-gates.sh's '[3/6] TESTS / Coverage floor' checkpoint line, and both were killed by
  the 1800s build timeout (first: TIMEOUT status after the full 30 min; second: manually cancelled after 7 straight
  45s-interval stall-count readings with 0 log-line growth, i.e. ~5+ min flat, once the first run's identical stall
  point was reproduced). The SAME test suite completes locally (`quality-gates.sh --no-fix`) in 93 seconds on the exact
  same commit — this is a Cloud-Build-environment-specific hang, not a code/test regression. Because the build never
  reaches its push step, Artifact Registry's `features-service:latest` is STILL the old 2026-07-14 image
  (`sha256:c204c49d...`) that predates the UTL fix — features-service-sports-job (which resolves the mutable `:latest`
  tag at execution time) will keep hitting the manifest-consolidator false-DOWN error until this is resolved and a build
  actually reaches SUCCESS."
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [features-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    cloud-build,
    ci,
    hang,
    timeout,
    features-service,
    quality-gates,
    resource-starvation,
    features-sports,
    deployment-blocker,
  ]
related:
  [
    plans/active/features_sports_service_consolidation_deploy_2026_07_15.md,
    plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md,
    plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md,
  ]
created: "2026-07-15"
parent_epic: sports_master
priority: P1
source:
  "Dispatched sub-agent task, 2026-07-15 (UnblockDeploy phase of
  features_sports_service_consolidation_deploy_2026_07_15.md): rebuild features-service against
  unified-trading-library@c47273c1 and verify the fix is present in the built image. Discovered as a direct consequence
  of triggering that build."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# features-service Cloud Build hangs in the quality-gates step — deployment blocker for the UTL c47273c1 fix

## Finding

Two consecutive manual triggers of `features-service-build` against commit `7c2e4ef1d19b155fb70e05b55363d06a3e55d270`
(the Dockerfile `BASE_IMAGE_DIGEST` bump) both hung and did not reach `SUCCESS`:

1. **Build `0b5cec2d-2f6a-4416-b870-44e3db644e1f`** — started 2026-07-15T14:51:47Z. Docker image build (step 6)
   completed normally (~image tagged `features-service:7c2e4ef`/`:0.66.0`/`:latest` locally inside the worker). Step 7
   "quality-gates" started, printed through its `[3/6] TESTS` section header and the `✓ Coverage floor: MIN_COVERAGE=70
   > = system floor
   > 70`line — then **zero further log output** for the remainder of the build. Killed by the build's own`1800s`timeout at`2026-07-15T15:22:56Z`(status`TIMEOUT`),
   > i.e. the quality-gates step alone consumed 20+ minutes past that checkpoint with no progress.
2. **Build `c4262919-003a-468c-9b9d-169b64a2adc8`** — re-triggered immediately after, same commit. Log line count grew
   normally through the docker build step (0 → 1008 lines by 15:29:49Z, matching build #1's exact same total), then
   **plateaued at exactly 1008 lines for 7 consecutive 45s-interval checks** (15:29:49Z → 15:36:44Z, ~7 minutes flat) —
   the identical stall point as build #1. Manually cancelled at that point rather than waiting a further ~23 minutes to
   confirm a second full timeout, since the reproduction was already conclusive.

**Local control**: `bash scripts/quality-gates.sh --no-fix` run on the exact same commit, same machine, same repo
checkout, completed in **93 seconds**, fully green (`.qg_last_passed_sha` sentinel written matching HEAD). The identical
`[3/6] TESTS` / `Coverage floor` checkpoint line appears in both the local run and the two hung Cloud Build runs — the
hang is specific to the Cloud Build execution environment, not a code or test regression introduced by this commit (the
commit's only change is a 1-line Dockerfile `ARG` bump; no test/source files touched).

## Suspected root cause (not confirmed — flagged for investigation, not guessed as fact)

`cloudbuild.yaml`'s `options.machineType: E2_HIGHCPU_8` — an `e2-highcpu-8` worker has 8 vCPUs but only ~8GB RAM (the
`highcpu` family ships ~1GB RAM/vCPU, well below the `standard`/`highmem` families). `features-service` is the
**consolidated 8-family features repo** (calendar/commodity/cross-instrument/delta-one/multi-timeframe/onchain/sports/
volatility) with heavy numeric dependencies (numba, hmmlearn, ta-lib, pandas/numpy) — its pytest run already prints a
`QG_MEM_CAP=10G set but systemd-run unavailable on this host → running pytest + basedpyright without hard memory cap`
warning in both hung runs (also present, harmlessly, in the local 93s run). If `pytest-xdist`'s auto worker count spins
up close to 8 parallel workers each loading these libraries, the aggregate working set could exceed 8GB and cause the
container to swap-thrash rather than cleanly OOM-kill — which would look exactly like an indefinite hang (no crash, no
log output, no progress) rather than a fast, loud failure. **This is a plausible mechanism, not verified** — no
`docker stats`/memory-pressure telemetry was pulled from the live Cloud Build worker (not accessible after the fact),
and no isolated repro (e.g. running the exact quality-gates test step inside a locally-resource-constrained 8GB-RAM
container) was attempted this touch.

## Why not fixed here

Diagnosing and right-sizing a Cloud Build machine type (or reducing pytest-xdist parallelism, or splitting the test
step) is a real infra change with fleet-wide-template implications (this `cloudbuild.yaml` follows the canonical
template shared by every service) — outside the scope of the dispatch that found it (rebuild + verify one image), and
risky to guess-fix under time pressure without reproducing the resource-pressure theory directly.

## Impact

- **`features-service-sports-job` is NOT yet running the UTL `c47273c1` fix** — `features-service:latest` in Artifact
  Registry is still the pre-fix 2026-07-14 image (`sha256:c204c49d...`). The manual re-verification execution planned in
  `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md` todo 5 and
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` will still hit the
  `Manifest consolidator appears DOWN` false-positive until a build actually reaches `SUCCESS` and pushes.
- No other consumer of `features-service:latest` is known to be blocked by the STALE image itself (the image is
  otherwise fine, just missing this one fix) — the urgency is specifically the sports-job unblock.
- If this machine-type/memory theory is correct, it could also affect ANY future features-service Cloud Build (unrelated
  to this fix), not just this one — worth a fleet-wide check of the shared `E2_HIGHCPU_8` template if the theory is
  confirmed.

## Recommended next steps (operator/engineer follow-up, not actioned here)

1. Retry the build a third time (transient Cloud Build worker contention/flakiness cannot be fully ruled out from 2 data
   points, though 2/2 identical stall points at the identical log-line count is strong evidence against pure chance).
2. If it reproduces again: bump `features-service/cloudbuild.yaml`'s `options.machineType` to `E2_HIGHCPU_32` (or an
   `E2_STANDARD_*`/`E2_HIGHMEM_*` tier with more RAM per vCPU) as a diagnostic — if the hang disappears, this confirms
   the memory-pressure theory and the fix is a permanent machine-type bump (with a cost tradeoff to weigh).
3. Alternatively/additionally: cap `PYTEST_WORKERS`/`-n` explicitly (rather than xdist auto-detecting 8 workers on an
   8-vCPU/8GB box) so parallel worker memory footprint stays bounded regardless of machine type.
4. Once a build reaches `SUCCESS`: verify with
   `docker run --rm --entrypoint python <new-digest> -c "import inspect; from unified_trading_library.manifest_writer import _state; print('cycle_in_flight' in inspect.getsource(_state.assert_consolidator_healthy))"`
   → `True`, THEN re-attempt the `features-service-sports-job` manual verification execution per the linked issue doc's
   next step.

## Evidence

- `gcloud builds describe 0b5cec2d-2f6a-4416-b870-44e3db644e1f --format='value(status,timeout,startTime,finishTime)'` →
  `TIMEOUT 1800s 2026-07-15T14:52:35Z 2026-07-15T15:22:56Z`.
- `gcloud builds log 0b5cec2d-2f6a-4416-b870-44e3db644e1f` → last line before silence:
  `Step #7 - "quality-gates": ✓ Coverage floor: MIN_COVERAGE=70 >= system floor 70`, then nothing until the transcript
  ends at `TIMEOUT`.
- `gcloud builds log c4262919-003a-468c-9b9d-169b64a2adc8 | wc -l` sampled every 45s: 2 → 49 → 221 → 348 → 968 → 1008 →
  1008 → 1008 → 1008 → 1008 → 1008 → 1008 → 1008 (7 consecutive flat reads, 15:29:49Z–15:36:44Z) — cancelled at that
  point (`gcloud builds cancel c4262919-003a-468c-9b9d-169b64a2adc8`).
- Local control: `cd features-service && bash scripts/quality-gates.sh --no-fix` on the identical commit
  (`7c2e4ef1d19b155fb70e05b55363d06a3e55d270`) → `✅ ALL QUALITY GATES PASSED (93s)`, sentinel
  `.qg_last_passed_sha=4675d4a1f97c4f2e8f257849e15631c00ee55567` (pre-commit HEAD, matches).
- `features-service/cloudbuild.yaml` line 406: `machineType: "E2_HIGHCPU_8"`.
- `gcloud artifacts docker images list ...features-service --include-tags` (checked before this dispatch's triggers):
  most recent successfully-pushed image is still 2026-07-14, `sha256:c204c49d...`, tags `0.66.0,7a60a31,latest`.
