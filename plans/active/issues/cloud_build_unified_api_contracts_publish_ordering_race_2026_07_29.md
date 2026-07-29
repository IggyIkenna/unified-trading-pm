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
    /plans/active/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
priority: P2
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

## Update 2026-07-29T14:35Z (slot 6, data_engineering) — instruments-service did NOT self-heal; root-caused + fixed

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

**Fix shipped**: `instruments-service@2941646c` (live-defi-rollout) — Dockerfile now sets `UV_EXTRA_INDEX_URL` (mirrors
pip.conf's URL) + `UV_KEYRING_PROVIDER=subprocess` (uv's keyring auth is opt-in, off by default) right after the
existing `COPY pip.conf` step, so `uv pip install` can reach the private registry exactly like `pip` already does.
Verified: manually re-triggered `instruments-service-prod` against `live-defi-rollout` (commit carrying the fix) — build
succeeded (build id `08c2d347`), confirming the fix resolves the failure in the real Cloud Build environment, not just
my local repro. Full `quality-gates.sh` green (94s) before shipping.

**This todo (below) generalizes beyond instruments-service** — any OTHER `ldr_main` repo whose Dockerfile relies on
`pip.conf` + `uv pip install` (not plain `pip install`) for its private-registry dependency has the SAME latent gap,
just not yet exposed by a floor-bump outpacing its own base image. Worth a quick grep across repos for
`uv pip install.*--no-sources` + `COPY pip.conf` co-occurring without a `UV_EXTRA_INDEX_URL`/`UV_INDEX` env var, as a P2
follow-up — not done in this pass (scope was the instruments-service production blocker for the cefi denominator job).

## Todos

- [ ] [DATA] P2. Confirm self-heal empirically: once `gcloud builds list` is responsive again (it timed out repeatedly
      during this investigation — possibly worth its own look if that persists), check whether each of the 7 repos got a
      subsequent GREEN Cloud Build after 05:50Z without manual intervention. **instruments-service confirmed did NOT
      self-heal — root-caused + fixed separately, see the 2026-07-29T14:35Z update above; this todo now covers the
      REMAINING 6 repos only** (strategy-service, ml-service, market-data-processing-service, trading-agent-service,
      greeks-service, market-tick-data-service — MTDS already confirmed self-healed above, so effectively 5 remain).
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
