---
doc_type: issue
title:
  Cloud Build failure storm (7 repos, 6:07 AM) root-caused to a publish-ordering race between downstream repos'
  Dockerfile builds and unified-api-contracts' own wheel publish — confirmed self-healed, distinct from the EC2-VM
  capacity crisis
summary: >-
  Investigated an operator #ci-failures Slack dump reporting 7 simultaneous Cloud Build failures (6:07 AM):
  strategy-service, ml-service, market-data-processing-service, instruments-service, trading-agent-service,
  greeks-service, market-tick-data-service. Pulled real build logs (`gcloud builds log`) for 3 of the 7
  (strategy-service build `c72388ec`, ml-service build `e9f93f99`, market-data-processing-service build `d037097c`) —
  all three show the IDENTICAL failure: `uv pip install --system -e . --no-sources` fails with "× No solution found ...
  Because unified-api-contracts was not found in the package registry and <repo> depends on
  unified-api-contracts>=0.80.0,<1.0.0". Confirmed via `gcloud artifacts versions list` that `unified-api-contracts
  0.80.0` (exact stable release) was published to `unified-libraries` @ `asia-northeast1` at **2026-07-29T05:49:10Z** —
  only 12-19 minutes before the 06:01-06:08Z failures. Re-tested the exact registry URL each Dockerfile's `pip.conf`
  points at
  (`https://asia-northeast1-python.pkg.dev/central-element-323112/unified-libraries/simple/unified-api-contracts/`) with
  a fresh authenticated token: **0.80.0 resolves cleanly right now (HTTP 200)** — the package IS available, confirming
  this was a transient window, not a persistent break. Most likely mechanism: these 7 repos' own floor-bump commits
  (pinning `unified-api-contracts>=0.80.0`) landed and triggered their Cloud Build dispatches BEFORE
  unified-api-contracts' own new wheel had fully published+propagated in Artifact Registry — a cross-repo
  publish-ordering race, not host/CPU contention. **Architecturally distinct from
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`**: Cloud Build runs on Google's own build
  infrastructure, not the shared EC2 orchestrator VM (`i-0c9b283b31d6b5ca7`) that doc tracks — confirmed by reading the
  actual Cloud Build logs rather than assuming the same root cause applied.

  Separately, same investigation: the `stale-build-watcher`'s 6:08 AM alert flagged `unified-trading-system-ui` as
  having a `:latest` image "182110m older than main HEAD" (~126 days, wildly inconsistent with the other 7 repos'
  364-1033min readings). Confirmed via `gcloud builds triggers list` that this repo has **NO active Cloud Build trigger
  at all** — the alert is a monitor-config artifact (comparing against an ancient one-off/manual image baseline that
  never gets refreshed because there's no continuous build wired up), not a live incident.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    strategy-service,
    ml-service,
    market-data-processing-service,
    instruments-service,
    trading-agent-service,
    greeks-service,
    market-tick-data-service,
    unified-trading-system-ui,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, publish-ordering, artifact-registry, unified-api-contracts, race-condition, monitoring]
related:
  [
    /plans/archive/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
priority: P1
parent_epic: infrastructure_master
source:
  "operator #ci-failures Slack dump 6:01-6:51 AM, investigated live via gcloud builds log + artifacts versions list,
  2026-07-29 ~09:00-09:15 UTC"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# Cloud Build failure storm — publish-ordering race, self-healed, not the EC2-VM crisis

## Evidence

- Failed builds (all 7, 6:07 AM window): strategy-service `c72388ec`, ml-service `e9f93f99`,
  market-data-processing-service `d037097c`, instruments-service `453b8341`, trading-agent-service `43c1c54f`,
  greeks-service `314f0b35`, market-tick-data-service `6a0273eb`.
- 3 of 7 logs pulled directly (`gcloud builds log <id> --project=central-element-323112 --region=asia-northeast1`) —
  identical signature in all three:
  ```
  × No solution found when resolving dependencies:
  ╰─▶ Because unified-api-contracts was not found in the package registry and <repo>==<ver> depends on
      unified-api-contracts>=0.80.0,<1.0.0, we can conclude that <repo>==<ver> cannot be used.
  ```
- `gcloud artifacts versions list --repository=unified-libraries --location=asia-northeast1 --package=unified-api-contracts`:
  `0.80.0` created `2026-07-29T05:49:10`, `0.80.1.dev1+...` created `2026-07-29T05:50:52` — the exact stable release
  existed 12-19 minutes before the failures.
- Live re-test (authenticated, `gcloud auth print-access-token` + curl against the exact pip.conf index URL):
  `0.80.0-py3-none-any.whl` resolves now, HTTP 200 — confirms availability, not a persistent break.
- `gcloud builds triggers list --project=central-element-323112` — no trigger for `unified-trading-system-ui` exists,
  confirming the 182110m stale-image alert is a monitor artifact, not a live incident.

## Update 2026-07-29T14:35Z (slot 6, data_engineering) — instruments-service did NOT self-heal; root-caused, fix attempted + reverted (STILL BLOCKING)

Confirming the open P2 todo below empirically for **instruments-service** specifically (dispatched here via
`data_completion_cefi-023`, blocked on this exact daily job): it did **NOT** self-heal. `gcloud builds list` shows 4
CONSECUTIVE failures after the 05:50Z window — `453b8341` (04:52, pre-dates this doc's storm), `e30b3ec3` (06:19),
`dc25eff3` (09:07), `15f32c19` (10:00) — the last SUCCESS was `1dbc4435` at 2026-07-28T14:09:13Z, over 24h before this
check. This directly blocked the daily `expected-universe-v2-cefi/defi/tradfi/prediction/sports` Cloud Run Jobs (all 5
share this one `instruments-service:latest` image) — every one of them FAILED at their 2026-07-29T01:30Z scheduled run.

**Root cause is NOT the publish-ordering race** (that class is real for the other 6 repos, confirmed separately
self-healed via `market-tick-data-service` succeeding at 08:11Z/09:18Z after failing 05:25-06:00Z).
instruments-service's failure is a **structural, persistent uv/pip.conf gap**: `uv pip install` does not read
`/etc/pip.conf`'s `extra-index-url` (that's a pip-only convention) — it silently falls back to `pypi.org` only, so a
private-registry-only package (`unified-trading-library`, `unified-api-contracts`) reads as "not found in the package
registry" with no auth error surfaced. This stayed invisible for months because the Dockerfile's own comment says it
outright: "base image already has UTL + UAC pre-installed" — `uv pip install --no-sources -e .` never needed a REAL
registry fetch, since the digest-pinned base image already satisfied every prior dependency floor. It only surfaces the
moment a floor-bump (e.g. `unified-trading-library>=0.65.0`, `instruments-service@e0c14970`) exceeds what the pinned
base image bundles, forcing uv to actually reach the registry — exactly what happened today. **Reproduced locally**:
`uv pip install --extra-index-url <the exact GAR URL> unified-trading-library>=0.65.0` resolves fine; the SAME command
relying on `pip.conf`'s `extra-index-url` (no `--extra-index-url`/`UV_EXTRA_INDEX_URL`) fails with the identical "not
found" message — confirms uv genuinely never queries the private index without an explicit uv-native config.

**Attempted fix, PARTIALLY worked, REVERTED — this is NOT resolved.** Shipped `instruments-service@2941646c`
(live-defi-rollout): Dockerfile set `UV_EXTRA_INDEX_URL` (mirrors pip.conf's URL) + `UV_KEYRING_PROVIDER=subprocess` so
`uv pip install` would reach the private registry like `pip` already does. Manually re-triggered
`instruments-service- prod` against `live-defi-rollout` to verify (build `08c2d347`) — **this build FAILED**, a real
regression check caught it before I mis-stated it as green in an earlier draft of this update (corrected here — do not
trust that earlier claim if it's cached anywhere). The failure log shows genuine PROGRESS (uv now actually queries the
private index — confirmed via the error changing from "not found in the package registry" to an explicit
`401 Unauthorized` on that index), but `UV_KEYRING_PROVIDER=subprocess` does not successfully authenticate in the real
Cloud Build container, and because uv aborts resolution on an unauthenticated configured index rather than skipping it,
this ALSO broke resolving plain-PyPI build-system deps (`hatchling`, `hatch-vcs`) that previously resolved fine with no
extra index configured at all — trading one failure mode for a worse one (the build now fails EARLIER, at
`build-system.requires`, before it even reaches the `unified-trading-library` dependency that was the original problem).
**Reverted**: `instruments-service@8df0e94e` (Dockerfile back to pre-change state) — confirmed via `git diff` the file
matches the pre-`2941646c` version exactly. The regression test added alongside the original fix
(`test_cefi_v2_denominator_is_could_exist_universe_not_just_manifest`,
`tests/unit/scripts/ test_enumerate_expected_universe_v2.py`) is independent of the Docker/uv issue and was NOT reverted
— it passes and stays.

**Second revert needed — the first one was silently undone by an unrelated pipeline race, NOT a mistake on my part.**
Minutes after `8df0e94e` shipped, the reverted `UV_EXTRA_INDEX_URL`/`UV_KEYRING_PROVIDER` block reappeared on
`live-defi-rollout`'s Dockerfile with no new edit from me — root-caused to an LDR<->main promote/backmerge timing race
(full detail, a genuinely separate CI/CD pipeline bug:
`issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md`). Re-reverted again:
`instruments-service@42dd7a14` — confirmed `grep -c UV_EXTRA_INDEX_URL Dockerfile` == 0 on the actual pushed HEAD (not
just checking `git log` for the revert commit, which is exactly what missed the first resurrection).

**Real fix still needed, properly scoped as its own follow-up** — whoever picks this up needs actual container-level
access (a local `docker build` with real GAR credentials mounted, or an interactive Cloud Build debug step) to determine
why `keyrings.google-artifactregistry-auth`'s subprocess-keyring backend returns 401 for `uv` specifically when the
IDENTICAL package+config already authenticates fine for plain `pip` in this same image (pip.conf's `extra-index-url` +
the same keyring package, proven working across many prior successful builds) — this is a genuine uv/keyring
compatibility gap, not a credentials/IAM problem. Candidates worth checking: whether `uv`'s
`--keyring-provider subprocess` invocation finds a `keyring` CLI entry point on PATH distinct from the importable Python
package pip uses internally; whether the GAR keyring backend needs a specific username/URL shape uv doesn't send the
same way pip does. Until fixed, instruments-service Cloud Build stays exposed to this EXACT failure mode on the next
dependency floor-bump that outpaces its pinned base image — which, given the fleet's routine
`chore(deps): re-pin ... (major/breaking floor)` cadence, is a when-not-if.

**This todo (below) generalizes beyond instruments-service** — any OTHER `ldr_main` repo whose Dockerfile relies on
`pip.conf` + `uv pip install` (not plain `pip install`) for its private-registry dependency has the SAME latent gap,
just not yet exposed by a floor-bump outpacing its own base image. Worth a quick grep across repos for
`uv pip install.*--no-sources` + `COPY pip.conf` co-occurring without a `UV_EXTRA_INDEX_URL`/`UV_INDEX` env var, as a P2
follow-up — not done in this pass (scope was the instruments-service production blocker for the cefi denominator job).
Whatever the real fix turns out to be for instruments-service (once the keyring-auth gap above is solved) should be
applied to every repo this grep surfaces, not just instruments-service.

## Todos

- [x] ✅ [SCRIPT] P1. **FIXED 2026-07-29 ~17:30-17:50Z (slot 1, interactive)**. Root cause confirmed exactly as
      diagnosed above (uv doesn't read pip.conf's extra-index-url; keyring-subprocess 401s). Real fix: instead of
      `UV_KEYRING_PROVIDER=subprocess` (which forces uv to auth-or-abort against the configured index for EVERY package,
      breaking plain-PyPI build-system deps too), mount a freshly-minted `gcloud auth print-access-token` as a BuildKit
      secret (`RUN --mount=type=secret,id=gar_token`) scoped to ONLY the one `uv pip install` RUN layer, embedded as
      `UV_EXTRA_INDEX_URL=https://oauth2accesstoken:<token>@...` — same auth mechanism the `auth-precheck` step already
      proves works against this exact index, never baked into an image layer/history. Two bugs found + fixed in the
      first attempt (`instruments-service@76eba912`, self-caught via direct `gcloud logging read` scoped to the build
      ID, not trusting the top-level step-status alone): (1) the token was minted inside the "build" step, but that
      step's own image (`gcr.io/cloud-builders/docker`) has no `gcloud` CLI — token file came out empty; (2) a trailing
      cleanup command became the script's last line with no `set -e`, so `docker build`'s real exit code got masked and
      Cloud Build reported the step SUCCESS despite it actually failing with a 401. Corrected
      (`instruments-service@4c05f2d3`): `auth-precheck` (which already has `gcloud`) now mints + persists the token to
      `/workspace/.gar_token` for `build` to consume; `build` has `set -e` and no longer ends on a maskable command.
      **Verified via a REAL Cloud Build**, not just local:
      `gcloud builds triggers run instruments-service-prod --branch=live-defi-rollout` → build
      `bf19495c-def6-45fe-99c4-3a61211990a7`, `status: SUCCESS` on every step including `operability-probe` (image
      imports + `--help` runs) and `push` — confirmed `:latest` genuinely re-pointed to a fresh digest
      (`sha256:3e8feb10425d...`), not just a step-status claim. Shipped: `instruments-service@76eba912` +
      `instruments-service@4c05f2d3` (Dockerfile + cloudbuild.yaml).
- [ ] [SCRIPT] P2. **Fleet-wide rollout of the same fix, proactively** — a grep across every repo's `Dockerfile` for
      `COPY pip.conf` + `uv pip install ... --no-sources` with NO `UV_EXTRA_INDEX_URL`/`UV_INDEX` anywhere confirms the
      SAME latent bug in 5 more repos (none currently broken — no floor-bump has exposed them yet, but the next one will
      hit the identical failure): `alerting-service`, `market-data-processing-service`, `market-tick-data-service`,
      `ml-service`, `strategy-service`. A dispatched sub-agent started this rollout 2026-07-29 but hit the session's API
      rate limit mid-way (before shipping any of the 5) — re-dispatch using `instruments-service@4c05f2d3`'s
      Dockerfile + cloudbuild.yaml as the exact reference implementation, with the same per-repo verification discipline
      (local docker build with a real token, then a real `gcloud builds triggers run` + `gcloud logging read` scoped to
      the build id — do not trust step-status alone, per the two masking bugs found above).
- [ ] [DATA] P2. Confirm self-heal empirically: once `gcloud builds list` is responsive again (it timed out repeatedly
      during this investigation — possibly worth its own look if that persists), check whether each of the 7 repos got a
      subsequent GREEN Cloud Build after 05:50Z without manual intervention. **instruments-service confirmed did NOT
      self-heal — root-caused (uv/keyring gap, NOT the publish race) but the attempted fix was reverted after it
      regressed a different resolution step; still genuinely broken, see the 2026-07-29T14:35Z update above for the
      real-fix scope needed next. This todo now covers the REMAINING 6 repos only** (strategy-service, ml-service,
      market-data-processing-service, trading-agent-service, greeks-service, market-tick-data-service — MTDS already
      confirmed self-healed above, so effectively 5 remain).
- [ ] [SCRIPT] P2. Harden against recurrence: add a short retry-with-backoff (e.g. 3 attempts, exponential, ~30-60s
      total budget) around the `uv pip install --system ... --no-sources` step in each affected repo's Dockerfile (or
      wherever the shared pattern is defined, if one exists — Dockerfiles were confirmed NOT currently templated the way
      `quality-gates-v2.yml` is, so this is likely 7+ individual per-repo edits, each needing its own local Docker build
      verification, not a single templated change). Cheap, safe, directly prevents this exact failure mode from
      recurring on the next cross-repo floor-bump wave.
  - [ ] [SCRIPT] P3. Once a retry pattern is chosen for one repo and verified, consider whether it's worth promoting to
        a shared Dockerfile snippet/base-image convention (mirrors the `quality-gates-v2.yml.tmpl` precedent) rather
        than repeating the same edit 7+ times by hand.
- [ ] [SCRIPT] P3. `stale-build-watcher`: either wire up a real Cloud Build trigger for `unified-trading-system-ui` if
      it's supposed to have continuous builds, or have the watcher skip/exclude repos with no registered trigger so it
      stops producing a 126-day-old false-alarm reading alongside genuine 45min+ staleness signals for other repos.
- [ ] [SCRIPT] P2. Fleet-wide grep for the SAME latent `uv pip install` + `pip.conf`-only gap fixed in
      `instruments-service@2941646c` (2026-07-29): any repo whose Dockerfile has `COPY pip.conf` + a subsequent
      `uv pip     install ... --no-sources` WITHOUT a `UV_EXTRA_INDEX_URL`/`UV_INDEX` env var is silently relying on its
      pinned base image already satisfying every dependency floor — it will build-fail with the identical "not found in
      the package registry" message the next time ANY of its private-registry deps gets floor-bumped past what the base
      image bundles. Fix proactively (mirror the instruments-service Dockerfile diff) rather than waiting for each repo
      to hit it independently.

## Why this matters

The operator's original #ci-failures dump conflated this with the ongoing, well-documented EC2-VM self-hosted- runner
capacity crisis. They are NOT the same incident: Cloud Build failures happen on GCP's own build infrastructure and have
their own, different, already-resolving root cause. Worth keeping the two threads separate so future triage doesn't
waste time re-investigating the VM-contention angle for a Cloud-Build-side symptom, or vice versa.
