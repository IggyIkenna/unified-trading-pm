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
status: resolved
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
  "features-service@bd0db4d7 (mock the fixtures split-fallback so no unit test makes a real gs:// read); green build
  fd73ca17-8d5a-435c-8ec6-9af11eb377fc → features-service:latest rebuilt carrying UTL c47273c1"
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

## Progress Log

- 2026-07-15 (~16:20-16:44Z, FixBuildHang phase — real evidence, not inference; root cause STILL NOT confirmed):
  Root-caused what the "suspected root cause" section above got wrong, applied one concrete, well-evidenced fix, and
  re-triggered a build to test it. **Result: the hang reproduces even with the fix applied** — the real root cause
  remains open.
  1. **Falsified the xdist-worker-memory-pressure theory with source-level evidence** (not a guess): read
     `features-service/scripts/quality-gates.sh:21` (`PYTEST_WORKERS=${PYTEST_WORKERS:-0}`, set BEFORE sourcing
     `base-service.sh`) against `unified-trading-pm/scripts/quality-gates-base/base-service.sh:687-693`'s local/CI
     branching
     (`if [ -n "${PYTEST_WORKERS:-}" ]; then _PYTEST_N="${PYTEST_WORKERS}"; elif [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${CI:-}" ]; then _PYTEST_N="auto"; else _PYTEST_N="1"; fi`).
     Because features-service's own script already sets `PYTEST_WORKERS=0` (a non-empty string), the FIRST branch always
     wins — `-n 0` (single-process, no xdist forking) is used identically in local AND Cloud Build runs. The CI-only
     `_PYTEST_N="auto"` path this issue's "suspected root cause" blamed is **never reached for this repo**, regardless
     of `GITHUB_ACTIONS`/`CI` env vars. This directly falsifies "8 parallel xdist workers spike memory" as the mechanism
     — do NOT apply the `E2_HIGHCPU_32` or `-n 4` fixes this doc's "Recommended next steps" suggested; they would not
     change anything (parallelism is already off in both environments).
  2. **Confirmed Cloud Build resource telemetry is genuinely unavailable, not merely unpulled**:
     `gcloud builds describe 0b5cec2d... --format='yaml(options,status,timeout)'` → `pool: {}` (default managed pool,
     not a Private Pool). Default-pool Cloud Build workers are not exposed as a queryable Compute Engine instance in the
     project, so there is no `docker stats`/Cloud Monitoring CPU/memory series obtainable for these builds after the
     fact — a structural gap, confirmed rather than assumed.
  3. **Corrected a framing point**: `base-service.sh` (lines ~710-732) redirects ALL pytest stdout/stderr to a temp file
     (`_pytest_log`) and only prints it (on failure) or a one-line `Tests PASSED` (on success) — this is true LOCALLY
     too. So "zero log growth during the TESTS phase" is the EXPECTED signature of a HEALTHY run as well (the local 93s
     pass also produces zero pytest-level output until it finishes); the real anomaly is purely DURATION vs the 93s
     local baseline, not the silence itself. Also confirmed pytest-timeout's default `signal` method (`--timeout=60`, no
     `--timeout-method` override anywhere) only wraps each test item's setup+call+teardown once execution begins — a
     hang during collection or a session-scoped fixture's first invocation is invisible to it.
  4. **Found and fixed a real local<->CI parity bug** (a plausible, evidence-backed candidate, not a guess): both
     `tests/cross_instrument/conftest.py` and `tests/multi_timeframe/conftest.py` define a session-scoped
     `gcp_auth_info` fixture that calls the REAL `google.auth.default()` or (in the source before this touch's fix)
     silently swallowed real-credential-discovery failures in the same way and only fell back to the mock branch after
     ambient credential discovery failed. In `tests/multi_timeframe/conftest.py` this fixture is pulled in by an
     `autouse=True` guard (`_skip_integration_without_creds`) that fires for EVERY test collected under
     `tests/multi_timeframe/` — including the `unit/` subtree that `PYTEST_UNIT_DIR` actually collects (confirmed via
     `rg`, not assumed). A Cloud Build worker IS a genuine GCE VM (its metadata server at `169.254.169.254` is real and
     reachable), so `google.auth.default()` can resolve REAL ambient Compute-Engine credentials there while it fails
     through to the mock branch on any non-GCE host — a concrete violation of the `Local↔CI env parity` invariant
     `base-service.sh` itself states in a comment (`CLOUD_MOCK_MODE=true` is exported unconditionally for every
     `quality-gates.sh` run, local or CI). Shipped a fix gating both fixtures on `CLOUD_MOCK_MODE=true` (short-circuits
     to the mock branch before ever calling `default()`) — `features-service@78fd05d1`
     (`bash scripts/quality-gates.sh --no-fix` full run passed locally in 6:02, sentinel `.qg_last_passed_sha` matches
     HEAD; landed via
     `quickmerge.sh --agent --files 'tests/cross_instrument/conftest.py tests/multi_timeframe/conftest.py'`).
  5. **Re-triggered the build against the fix**
     (`gcloud builds triggers run features-service-build --branch=live-defi-rollout`) → build
     `cc976c01-794a-4437-a745-4e1c8ccf722f` (commit `78fd05d17a135b29c7bd6db243675130b18129bd`). **The hang reproduced
     at the identical checkpoint**: same `[3/6] TESTS` → `✓ Coverage floor: MIN_COVERAGE=70 >= system floor 70` line,
     then flat at 1005 log lines from ~16:34:40Z onward with zero growth. Watched live (not left unattended) for ~10
     minutes of confirmed flatness (vs. the local 93s `--quick` baseline) before cancelling deliberately at 16:44:04Z
     (`gcloud builds cancel cc976c01-794a-4437-a745-4e1c8ccf722f`) rather than waiting out a third full 1800s — the
     evidence was already conclusive and further waiting added no new diagnostic signal (Cloud Build gives no visibility
     into WHERE inside the redirected pytest run it is stuck, per finding 3 above).
  6. **Conclusion: the `gcp_auth_info` local<->CI parity fix is a genuine, worthwhile correctness improvement (now
     shipped) but is NOT the cause of this hang** — the real root cause is still unconfirmed. Did NOT apply the
     machine-type bump or xdist-worker-cap "recommended next steps" from this doc's original write-up, since finding 1
     above falsifies the mechanism they were meant to address, and applying either now would be a guess unsupported by
     evidence, not a targeted fix. Not yet tried (flagged for the next touch, in priority order): (a) get a build to
     stream pytest output LIVE instead of silently redirecting it (a `tee` in the `quality-gates` docker-run instead of
     the `>>"$_pytest_log"` capture used by `base-service.sh` — would require a change to the shared base script,
     cross-repo blast radius, needs its own review) so the NEXT hang shows exactly which test/module is stuck instead of
     another blind stall; (b) a controlled bisection by temporarily deselecting test subtrees
     (`--ignore=tests/<family>/unit`) one family at a time via a throwaway manual Cloud Build trigger, to localize which
     of the 8 consolidated feature families' unit tests is actually the hang site, before proposing any
     resource/parallelism change. features-service:latest in Artifact Registry is UNCHANGED (still the stale 2026-07-14
     `sha256:c204c49d...` image) — the UTL `c47273c1` fix has still not reached a pushed image. `status` stays `open`;
     not resolved this touch.
- 2026-07-15 (~17:53Z, ShipAndTrigger phase — implemented "not yet tried" item (a) from the prior touch + added a
  phase-agnostic diagnostic the prior touch did not have, then re-triggered the build). The prior touch established: (1)
  the xdist-worker-memory theory is FALSIFIED (`PYTEST_WORKERS=0` forces `-n 0` in BOTH local and CI); (3) pytest's
  redirected-output silence is the EXPECTED healthy signature too, so the only anomaly is DURATION; and pytest-timeout's
  default `signal` method + the redirect-to-tempfile-with-`trap rm EXIT` design together mean the 1800s timeout kill
  deletes the tempfile → zero diagnostic. This touch ships the two-pronged fix for that blind spot:
  1. **Live-streamed pytest output** (`unified-trading-pm@0148b6f34`) — rewrote both pytest invocations in
     `scripts/quality-gates-base/base-service.sh` from `>>"$_pytest_log" 2>&1` (silent redirect, `cat` only on non-zero
     exit) to `2>&1 | tee -a "$_pytest_log"` with `_pytest_rc=${PIPESTATUS[0]}` and explicit exit-on-nonzero. Keeps the
     original xrealloc-avoidance guarantee (never stuffs stderr into a bash VAR) and the tempfile for the downstream
     `_TESTS_RAN`/`_SKIPPED` greps, while surfacing output AS IT HAPPENS. **Caveat (verified, not assumed):
     base-service.sh is BAKED INTO THE UTL BASE IMAGE** at
     `/app/unified-trading-pm/scripts/quality-gates-base/ base-service.sh`, so this change does NOT reach the failing
     build — it needs a UTL rebuild + a features-service Dockerfile `BASE_IMAGE_DIGEST` re-pin to land in CI. Shipped
     anyway as operator-requested fleet-hardening (helps local runs, GitHub-Actions quality-gates-v2, and every future
     UTL-based build).
  2. **Phase-agnostic faulthandler watchdog** (`features-service@b4cae4eb`, tests/conftest.py) — the LOAD-BEARING new
     diagnostic that DOES reach this build (the features-service repo's own `tests/conftest.py` is COPY'd into the
     image). At module level (import time), gated on `CLOUD_BUILD == "true"`:
     `faulthandler.dump_traceback_later(420, exit=True, file=sys.stderr)`. Unlike pytest-timeout's per-item `thread`
     watchdog (which only arms once an item's setup/call/teardown begins, so it is BLIND to a collection/import-phase
     stall — the leading suspect given the `gcp_auth_info`/`google.auth.default()` import-time credential-resolution
     path the prior touch found), this is a wall-clock watchdog that fires in ALL phases: at 420s it dumps every
     thread's stack to stderr (captured by base-service.sh's log) and `_exit(1)`s → non-zero pytest exit → the failure
     path surfaces the stack → the build fails FAST at ~7min WITH the hung stack instead of a silent 1800s TIMEOUT. 420s
     is huge headroom over the ~90-160s a healthy `--quick` CI run takes (full local `--no-fix` here was 273s).
     faulthandler is stdlib — no new dep. Also paired with `timeout_method = "thread"` in
     `features-service/pyproject.toml` (same commit) so a TEST/FIXTURE-phase hang additionally fires the `--timeout=60`
     thread dump + fail-fast (the default `signal` method can't interrupt a C-level/syscall hang). Chose to gate the
     watchdog on `CLOUD_BUILD` only, NOT `CLOUD_BUILD or CI`: the Cloud Build target sets `-e CLOUD_BUILD=true` (goal
     met), whereas GitHub-Actions quality-gates-v2 runs the FULL suite (not `--quick`) which could legitimately exceed
     420s and false-fail — decide-and-document.
  3. **Ship + re-trigger**: features-service full `quality-gates.sh --no-fix` green in 273s (sentinel
     `.qg_last_passed_sha=78fd05d1...` == pre-commit HEAD); the `tee` change was observed working live locally (pytest
     output streamed instead of being buffered). Landed features-service@`b4cae4eb`
     (`quickmerge.sh --agent --files 'pyproject.toml tests/conftest.py'`) + unified-trading-pm@`0148b6f34`
     (base-service.sh, PM `scripts/**` carve-out). Re-triggered
     `gcloud builds triggers run features-service-build --branch=live-defi-rollout --region=asia-northeast1` → build
     **`136fce13-69dd-4eac-bc5b-e9fe0251c524`** (QUEUED against commit `b4cae4eb`, createTime 2026-07-15T17:53:04Z). NOT
     watched here — a follow-on phase watches: if the hang reproduces, the faulthandler dump at ~7min now localizes
     WHERE (which module/fixture/syscall) it is stuck, converting the blind stall into an actionable stack. `status`
     stays `open`; features-service:latest in Artifact Registry is still the stale `sha256:c204c49d...` until a build
     reaches SUCCESS + pushes.

## Root cause CONFIRMED + fixed (2026-07-15, ~19:1x UTC)

- **The diagnostics worked.** Build `136fce13` FAILED FAST (~91% of the sports unit suite) with a captured
  pytest-timeout **thread-method stack dump** (the `timeout_method = thread` change fired where the default `signal`
  method could not). Exact hang:
  - `tests/sports/unit/test_gcs_paths_and_reader_deps.py:138`
    `test_missing_fixtures_within_coverage_raises_dependency_error`
  - → `features_service/sports/data/gcs_reader.py:307` `read_reference_entity` → `:266` `_read_split_fixtures_fallback`
  - → UTL `unified_trading_library/fixtures/joined_reader.py:248` `read_fixtures_joined` → `:178`
    `_load_fixtures_for_day`
  - → `pd.read_parquet(gs://…)` → pyarrow `ParquetDataset.__init__` → `filesystem.get_file_info(path)` **← hangs**.
- **Why CI-only:** pyarrow's GCS filesystem does NATIVE C++ network I/O that pytest-socket's `--allow-hosts` cannot
  block. On a Cloud Build GCE worker the metadata server (169.254.169.254) is reachable → ambient ADC resolves → pyarrow
  attempts a real GCS stat and hangs on retry. Locally (no ambient creds) it fails fast → the code swallows it → the
  test passed, masking the gap. A unit-test **hermeticity** bug (unit test making a real cloud call), same class as the
  earlier gcp_auth_info fix (features-service@78fd05d1).
- **Fix:** `features-service@bd0db4d7` — mock `_read_split_fixtures_fallback` → `None` in the two fixtures tests in
  `test_gcs_paths_and_reader_deps.py` (verifies "all read strategies exhausted → DependencyError" without touching real
  GCS). Sweep confirmed the only unit-level offender: `test_pre_match_standings.py` +
  `test_fixture_features_pipeline.py` fully monkeypatch `read_reference_entity` (never reach the real read);
  `test_sports_integration.py` is integration (not run in the CI `--quick` unit build). Full local
  `quality-gates.sh --no-fix` green (278s). Rebuild triggered: build `fd73ca17-8d5a-435c-8ec6-9af11eb377fc` against
  `bd0db4d7`.
- **Kept as permanent hardening:** the `timeout_method = thread` (pyproject) + faulthandler watchdog (tests/conftest.py,
  CLOUD_BUILD-gated 420s exit=True) + base-service.sh `tee`-streaming (`unified-trading-pm@0148b6f34`) all stay — they
  turn any FUTURE CI hang into a fast fail with a stack dump instead of a silent 1800s timeout.

## Resolution (2026-07-15)

**RESOLVED.** Root cause was a unit-test hermeticity bug, NOT the originally-suspected xdist/memory pressure (which was
falsified: `features-service/scripts/quality-gates.sh` forces `PYTEST_WORKERS=0`, so pytest is already single-process in
CI). The instrumentation shipped to make a silent hang fail-fast (thread-method pytest timeout + a CLOUD_BUILD-gated
import-time faulthandler watchdog + `tee`-streamed pytest output) did its job: instrumented build `136fce13` failed fast
with a thread stack dump pinpointing `tests/sports/unit/test_gcs_paths_and_reader_deps.py:138` →
`_read_split_fixtures_fallback` → UTL `read_fixtures_joined` → `pd.read_parquet(gs://…)` → pyarrow `get_file_info`
hanging on native C++ GCS I/O that `pytest-socket` cannot block (hangs on a GCE Cloud Build worker with ambient ADC;
passes locally). **Fix:** `features-service@bd0db4d7` mocks the fixtures split-fallback so no unit test issues a real
`gs://` read (sweep-confirmed the sole unit-level offender); full local `quality-gates.sh` green (278s).

**Verified end-to-end.** Rebuild `fd73ca17-8d5a-435c-8ec6-9af11eb377fc` against `bd0db4d7` completed `SUCCESS` and
pushed a fresh `features-service:latest` — confirmed in-container to carry both the UAC internal-namespace fix and UTL
`c47273c1` (lock-aware consolidator liveness). That image unblocked `features-service-sports-job`, which then reached a
genuine `SUCCEEDED` on both a manual and a real scheduled fire (see
`features_sports_service_consolidation_deploy_2026_07_15.md`). The hardening changes are retained fleet-wide as
permanent regression protection.
