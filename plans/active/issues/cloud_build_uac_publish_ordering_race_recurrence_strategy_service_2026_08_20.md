---
doc_type: issue
title:
  strategy-service Cloud Build FAILURE = recurrence of the unified-api-contracts publish-ordering race — this instance
  self-healed, but the recurring CLASS has an identified root-cause fix (update-repo-version.yml resolvability gate
  checks git, not Artifact Registry) that has not been implemented yet
summary: >-
  `cloud-build-failure-watcher` paged CRITICAL for strategy-service build `77fbf981` (main @ `bb3ff1b`,
  2026-08-20T11:02:18Z): docker step 6 `uv pip install` failed "× No solution found ... strategy-service==0.79.2
  depends on unified-api-contracts>=0.149.0,<1.0.0", while the newest wheel on `unified-libraries`@asia-northeast1 at
  that moment was only `0.148.1.dev1` (published 10:43:57Z). ROOT-CAUSED as a recurrence of the publish-ordering race
  documented in
  /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md: the
  `chore(deps): re-pin unified-api-contracts to 0.149.0 (major/breaking floor)` commit (`51471024`) was promoted to main
  and fired the Cloud Build ~12 min BEFORE UAC `0.149.0`'s wheel was published (11:14:57Z). NOT a code defect —
  strategy-service's GAR auth path (BuildKit-secret `gar_token` + `UV_EXTRA_INDEX_URL` + retry wrapper, shipped in the
  fleet-wide 2026-07-29/30 rollout) is present and correct, and the failing build log proves uv reached AR (it found the
  index, just not the version). VERIFIED RESOLVED by re-running the same commit: build `10283751` SUCCESS (7m47s) with
  log line `+ unified-api-contracts==0.149.0` and a fresh `strategy-service:latest` digest pushed. **UPDATE (same day,
  interactive slot-1 deep-dive)**: the operator explicitly asked for the real fix rather than another self-heal
  writeup. Found the exact gate this needs: `update-repo-version.yml`'s existing "Resolvability gate" step (built for a
  DIFFERENT resolution path — git tag / branch pyproject.toml — not Artifact Registry) is the single fan-out point for
  every consumer's floor-bump; extending its check to also require the wheel be live on AR closes the race at its
  source, before the downstream Cloud Build trigger ever fires, at zero Cloud Build cost (the wait happens in cheap
  GitHub Actions compute, not a billed Cloud Build worker). See "Root-cause fix" section below. NOT YET IMPLEMENTED.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm, market-data-processing-service, trading-agent-service, instruments-service]
scope: [engineer, admin]
tags: [ci, cloud-build, publish-ordering, artifact-registry, unified-api-contracts, race-condition, live-incident]
related:
  - /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md
  - /plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md
  - /plans/active/issues/agent_orchestrator_qg_cancel_notifier_same_sha_rerun_gap_2026_08_20.md
  - /plans/active/issues/publish_package_semver_tag_race_breaks_consumer_builds_2026_08_20.md
created: 2026-08-20
author: cloud-build-failure-watcher escalation (cicd, slot-11)
parent_epic: ci_master
priority: P2
source: cloud-build-failure-watcher CRITICAL for strategy-service build 77fbf981 (2026-08-20T11:02:18Z)
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-21
context_scope:
  [
    strategy-service/Dockerfile,
    strategy-service/pyproject.toml,
    strategy-service/cloudbuild.yaml,
    /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
  ]
---

# strategy-service Cloud Build — UAC publish-ordering race (recurrence, self-healed)

## Evidence (measured, not inferred)

- **Failing build** `77fbf981-185c-4a18-884b-814bac36b9b0` (main @ `bb3ff1b3`, 2026-08-20T11:02:18Z) — FAILURE,
  docker step 6 (the `RUN --mount=type=secret,id=gar_token UV_EXTRA_INDEX_URL=... uv pip install --system --no-sources -e .`
  retry-wrapper layer). Log:
  ```
  × No solution found when resolving dependencies:
  ╰─▶ Because only unified-api-contracts<=0.148.1.dev1+gfd4391914
      is available and strategy-service==0.79.2 depends on
      unified-api-contracts>=0.149.0,<1.0.0, we can conclude that ...
  uv pip install failed after 3 attempts
  ```
- **Wheel-availability timeline** (`gcloud artifacts versions list`): `0.148.1.dev1` @10:43:57Z →
  `0.149.0` @**11:14:57Z** (~12 min AFTER the failed build) → `0.149.1.dev1` @11:17:19Z. The floor-bump commit
  `51471024` in strategy-service pinned `unified-api-contracts>=0.149.0,<1.0.0` (pyproject.toml) and was promoted to
  main (`bb3ff1b3 chore(promote): LDR → main`) before the wheel existed.
- **Re-run build** `10283751-dc24-4cd7-aab0-9d76fbfcc77b` on the SAME commit `bb3ff1b3`: **SUCCESS** 11:30:26 →
  11:38:13Z (7m47s). Log line: `+ unified-api-contracts==0.149.0` (downloaded from AR, replacing the base-image-pinned
  dev version). Fresh `strategy-service:latest` pushed (digest `sha256:c3a451b2e31d...`); scan-check + notify-deployment
  steps finished.
- **Not a uv/pip.conf structural gap** (unlike the MTDS 2026-08-10 case): the failing log says "`unified-api-contracts`
  was found on https://asia-northeast1-python.pkg.dev/.../simple/ but not at the requested version" — uv reached AR, so
  publishing the wheel genuinely unblocks it. The BuildKit-secret auth pattern (fleet rollout in the 2026-07-29 doc) is
  present and correct.
- **Same-window sibling failures** (likely the same class, each its own wall/dispatch — NOT investigated here):
  `features-service-build` 11:14:32Z (20s BEFORE the wheel published), `instruments-service-prod` 11:03:50Z,
  `fund-administration-service-build` 11:03:20Z.

## Root cause

Recurrence of the **publish-ordering race**: a consuming repo's `chore(deps): re-pin unified-api-contracts to X.Y.0
(major/breaking floor)` lands on `live-defi-rollout`, gets promoted to `main`, and fires its Cloud Build **before**
`unified-api-contracts`'s own wheel for that version is published+propagated to Artifact Registry. The build then fails
with a now-fixed version requirement. Once the wheel lands, a re-build succeeds. Exactly the class documented (and
closed) in `cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md` — that incident's *structural* fix
(uv actually reaching AR) was shipped fleet-wide, but the *ordering* coordination itself was never enforced, so the
race recurs on the fleet's routine floor-bump cadence.

## Why this matters

- The GH Actions `quality-gates-v2` gate can be green while the Cloud Build image pipeline is red — separate pipelines
  (per the watcher's dispatch context). A stale red build looks like a persistent break when it is a transient window.
- 2nd occurrence of this class in ~3 weeks, 4 repos this window → without an ordering guard, every future
  `re-pin unified-api-contracts` floor-bump that races its wheel publish re-pages the watcher.

## Root-cause fix — where the ordering gate actually belongs (session 2026-08-20, interactive slot-1 deep-dive)

**Why the 2026-07-29 fix didn't prevent this recurrence**: that incident shipped a build-time retry wrapper
(`uv pip install` × 3 attempts, 15s/30s/45s backoff ≈ 90s total) into every affected Dockerfile — see
`/codex/06-coding-standards/dockerfile-standards.md` § "uv pip install Retry Wrapper". It's present and working
correctly in today's logs (you can see the 3 retry attempts before the final failure). It just isn't a big enough
window: today's real gap between the floor-bump landing on `main` (~11:01-11:03Z) and the wheel actually being
resolvable on AR (11:14:57Z) was **~12-20 minutes**, roughly 8-13x the wrapper's absorption budget. A build-time retry
can never be sized correctly because it's guessing a delay instead of checking the real condition — and widening it
further just burns more BILLED Cloud Build compute per race (this is why option "just widen the retry window" was
rejected in favor of the below — see the operator discussion this session).

**A purpose-built check for this already exists, unwired**: `scripts/cicd/assert_deps_published_to_ar.py`. Its own
docstring: *"STATUS (2026-06-16): NOT currently wired into any workflow — RESERVED for the production IMAGE-BUILD
dep-publish gate... Wire this in at the image/cloud-build step when that cutover happens."* That cutover (Cloud Build
resolving internal deps from live AR) has since happened — this incident IS the condition the docstring anticipated.
The script queries AR directly (`gcloud artifacts versions list --package=<dep> ...`) rather than the racy
`published_packages` manifest field, and is FAIL-OPEN on any ambiguity (only blocks on a confirmed "AR doesn't have
it yet" signal) — exactly the right contract for a gate.

**The correct wiring point is NOT a Cloud Build step** (that would mean paying for a live, billed `E2_HIGHCPU_8`
worker to sit and poll for up to ~10-20 min every time this races — real, recurring GCP spend for pure idle-wait).
It's `unified-trading-pm/.github/workflows/update-repo-version.yml`, the ONE fan-out point that decides when to
dispatch the `dependency-update` event that eventually produces the `chore(deps): re-pin ...` commit → promotion →
push to `main` → (for these repos) the native Cloud Build trigger. This workflow **already has** a step built for
almost exactly this purpose:

- Job `update-manifest`, step id `resolve-gate`, name *"Resolvability gate — dep promoted before consumer fan-out
  (DEFECT-2)"* (~line 502-568). Bounded poll: 10 attempts × 30s (~5 min), and on timeout it does NOT fail outright —
  it re-dispatches itself with `fanout_retry+1` (max 3 retries, so up to ~20 min total across retries) before finally
  paging CRITICAL via the `notify-fanout-unresolvable` job. This is exactly the shape we want.
- Its `check_resolvable()` function (~line 534-555) checks TWO things: (a) does git tag `v$VERSION` exist on the
  producer repo, (b) does the producer's `$BRANCH` `pyproject.toml` already carry `version = "$VERSION"`. **Neither
  checks Artifact Registry.** Per this same file's own comment (~line 484-490), this gate was built to protect a
  DIFFERENT consumer of "is this version available" — `python-quality-gates-v2`'s dev-time `clone_repo()`, which
  resolves internal deps from git (tag / branch / PR-base-tier), not from AR. The Cloud Build image pipeline is a
  SECOND, separate consumer of the same underlying fact, added later, and this gate was never extended to also protect
  it.

**Proposed fix**: add a third condition (c) to `check_resolvable()` — query AR the same way
`assert_deps_published_to_ar.py` already does, and require it alongside the existing (a)/(b) checks before the fan-out
dispatch (and therefore the floor-bump commit, promotion, and Cloud Build trigger) is allowed to fire. This:
- Runs in ordinary GitHub Actions compute (this workflow's existing job), not billed Cloud Build minutes — closes the
  operator's cost objection to a build-time wait.
- Is a single-file change (one fan-out point covers the whole fleet) — no per-repo `cloudbuild.yaml`/Dockerfile edits,
  no drift-ratchet risk (`check_cloudbuild_template_drift.py` is untouched).
- Reuses proven retry/backoff/loop-breaker machinery already in this file rather than inventing new polling logic.
- Needs its own sizing check: today's real gap (~12-20 min) is close to the CURRENT total retry budget (~20 min across
  3 fanout_retry attempts) — verify that's still enough headroom once the AR check is added, or widen it.

Not yet implemented — see Todos.

## Finalized implementation design (session 2026-08-20, continued — operator review requested before shipping)

Three follow-up questions from the operator refined the design below. Each is answered with what was actually checked,
not assumed.

**Q1: does the wait need to cover the producer's wheel-build time too, or just AR propagation lag?** Checked
`semver-agent.yml` (the workflow that actually dispatches `version-bump`, triggering this whole fan-out chain) — it has
ZERO references to "wheel" or "publish-package" anywhere in it. It mints the version and dispatches `version-bump`
completely independently of, and unsequenced with, `publish-package.yml`'s wheel build+upload. **They are parallel,
racing reactions to the same push/tag event, not a pipeline.** So the wait this gate needs to absorb is the FULL
producer-side latency — wheel build+upload time (comparable builds in this fleet run several minutes) PLUS the AR
indexing/propagation lag already measured today (12-31 min) — not propagation lag alone. This raises the priority of
the "verify retry budget" todo below; the current ~20 min budget (5 min × 3 `fanout_retry` retries) may not be enough
once build time is added on top, and should be re-sized deliberately rather than assumed sufficient.

A structurally cleaner alternative exists — **sequence `semver-agent`'s dispatch behind `publish-package.yml`'s own
AR-confirmation** (have the publish workflow, which is already running and already paying for its own runtime, be the
thing that fires the fan-out once AR is confirmed, instead of two independent workflows racing) — which would need
zero incremental wait at all. That is a real rewire of the trigger graph across two workflows, bigger than the
poll-based fix below. Noting it here as the eventual "does this properly" option; not in scope for the initial fix.

**Q2 + Q3: will the wait bill GitHub Actions minutes, and can we avoid that by using the self-hosted glue pool
instead?** Confirmed: GitHub-hosted runner billing (`ubuntu-latest`, which is what this job currently uses) is
wall-clock, not CPU-based — a step that just polls/sleeps is billed the same as one doing real compute for the full
duration the runner is held. So yes, widening this gate's wait window costs real (if modest, compared to the Cloud
Build alternative) GH Actions spend, scaling with how often the race happens.

**CORRECTED 2026-08-20 (`/plan-reconcile` finding F-G09-1)**: the original text above claimed PM is a **private**
repo (`gh api repos/IggyIkenna/unified-trading-pm --jq .private` → `true`) as part of the billing analysis. Re-checked
live this session: PM is **public** (`{"private":false,"visibility":"public"}`). This matters beyond billing —
`plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md` documents that every self-hosted-routed
workflow in this repo, including this exact job, was deliberately reverted to `runs-on: ubuntu-latest` on 2026-08-07
specifically because self-hosted-runner-on-a-public-repo is a fork-PR security exposure. **The self-hosted-glue-runner
half of the "Decided approach" below (todo item 4a) must NOT ship as designed while PM stays public** — it would
reintroduce the exact exposure that revert fixed.

Operator direction: the self-hosted glue-runner pool is already running 24/7 as effectively sunk capacity, and exists
specifically to absorb this class of cheap/bounded workflow rather than paying GH-hosted per-minute rates — same
reasoning already applied fleet-wide to move lightweight per-repo dispatcher stubs there (e.g. `publish-package.yml`'s
per-repo trigger). Checked whether that's a clean move for this job specifically: `cloud-build-router.yml` (the other
GCP-orchestration workflow in this same repo) runs on `ubuntu-latest` with an explicit `google-github-actions/auth@v3`
step (WIF-first, SA-key fallback) — self-hosted runners in this fleet do NOT carry ambient GCP credentials, so moving
runner type doesn't remove the need for an auth step either way. `update-repo-version.yml` already HAS this exact
auth pattern in-file (`digest-auth-wif` / `digest-auth-key` steps, used later in the same job for the
`unified-trading-library` base-image-digest case) — reuse it rather than inventing a new one.

**Decided approach** (pending operator review of this doc, not yet shipped):

1. Change the `update-manifest` job's `runs-on: ubuntu-latest` → `runs-on: [self-hosted, glue]`. This moves the WHOLE
   job (checkout, manifest edit, git push-with-retry, DAG check, digest resolution, resolve-gate poll, dispatch
   fan-out) onto the cheap pool, not just the poll step — simplest change, no job-splitting, stays a single workflow
   file (operator preference: no new workflow file).
2. Add a GCP auth step near the top of the job (before `resolve-gate` needs it), mirroring the existing
   `digest-auth-wif`/`digest-auth-key` steps already in this file rather than a new pattern.
3. Extend `check_resolvable()` (as already scoped below) with the AR check, now sized against Q1's finding (build time
   + propagation lag, not propagation lag alone).

Residual consideration, not a blocker: this job holds the `concurrency: group: version-bump, cancel-in-progress: false`
slot for its entire duration, so moving it to the glue pool adds ONE bounded, serialized (never-concurrent) occupant —
predictable footprint, not a fan-out of parallel runners. A quick sanity check on current glue-pool headroom before
shipping is worth doing, but nothing found this session suggests a real contention risk.

## Todos

- [x] ✅ [CICD] P1. **Diagnose + verify resolved.** Root-caused to the publish-ordering race; re-ran the
      `strategy-service-build` trigger on the same failing commit (`bb3ff1b3`) → build `10283751` SUCCESS; log confirms
      `+ unified-api-contracts==0.149.0`; fresh `:latest` pushed. Wall closed, no strategy-service code change made.
- [x] ✅ [CICD] P2. **Root-cause the recurring CLASS (not just this instance) and find the correct fix location.**
      Done this session — see "Root-cause fix" section above. Confirmed: `assert_deps_published_to_ar.py` exists,
      unwired, built for exactly this; `update-repo-version.yml`'s `resolve-gate` step is the correct single fan-out
      point but checks git resolvability, not AR. Supersedes the prior `[OPERATOR] P3` "judgment call" framing — the
      mechanism is now identified, this is implementation work, not an open design question.
- [x] ✅ [CICD] P2. **Finalize the implementation design** (runner choice, auth reuse, wait-budget scope) — done this
      session, see "Finalized implementation design" above. Pending operator review of this doc before shipping.
- [ ] [CICD] P2. **Implement** (operator review pending — do not ship until reviewed):
      (a) **BLOCKED-OPERATOR — do NOT ship while PM stays public** (see "CORRECTED 2026-08-20" note above):
      `update-repo-version.yml`'s `update-manifest` job: `runs-on: ubuntu-latest` → `runs-on: [self-hosted, glue]`.
      Either re-verify PM has been deliberately re-privatized before doing this, or drop this sub-item and keep the
      job on `ubuntu-latest`;
      (b) add a GCP auth step (WIF-first, SA-key fallback) mirroring the existing `digest-auth-wif`/`digest-auth-key`
      steps already in this file, placed before `resolve-gate` — independent of (a), ships either way;
      (c) extend `check_resolvable()` (~line 534-555) with a third check against Artifact Registry (`gcloud artifacts
      versions list --repository=unified-libraries --location=asia-northeast1 --package=$REPO
      --format="value(name)"`, compare against `$VERSION`), required alongside the existing git-tag/branch-pyproject
      checks. Test against this incident's real timeline: a floor-bump for `unified-api-contracts=0.149.0` dispatched
      before 11:14:57Z should have been held; after, allowed through immediately. Independent of (a), ships either way.
- [ ] [CICD] P2. **Re-size the retry budget** for the combined build-time + propagation-lag wait (current: ~5 min ×
      up to 3 `fanout_retry` retries ≈ 20 min total; today's real gap was ~12-20 min of propagation lag ALONE, before
      adding producer build time on top — re-derive a real number, don't assume 20 min still covers it). Widen
      `MAX_FANOUT_RETRY` or the per-attempt poll count as needed.
- [ ] [CICD] P3. **Quick glue-pool headroom sanity check** before shipping (a); confirm adding one bounded, serialized
      occupant doesn't meaningfully change current utilization.
- [ ] [CICD] P3. **Longer-term option, not in scope for the initial fix**: sequence `semver-agent`'s `version-bump`
      dispatch behind `publish-package.yml`'s own AR-confirmation instead of racing them, eliminating the need for
      this gate's wait entirely. Bigger change (trigger-graph rewire across two workflows); track separately once the
      poll-based fix above is shipped and stable.
- [ ] [CICD] P3. **Optional defense-in-depth**: also wire `assert_deps_published_to_ar.py` into `cloudbuild.yaml` as a
      cheap, single-shot (no poll loop) preflight check, in case some future path bypasses the
      `update-repo-version.yml` fan-out (e.g. a manually-edited `pyproject.toml` floor bump). Lower priority than the
      primary fix above — the fan-out path is the one that actually produced every failure seen in this incident.

## Related alerts from the same Slack #ci-failures batch (2026-08-20, ~16:23-16:49 IST)

This incident was one of six alerts the operator asked to be triaged together. Disposition of the other five:

- **9 more Cloud Build failures in the same window** (fund-administration-service, client-reporting-api, ml-service,
  trading-agent-service, market-data-processing-service, greeks-service, instruments-service, +2 more) — same class,
  confirmed via direct log pull on 3 of them (instruments-service, fund-administration-service, ml-service): byte-for-
  byte identical "`unified-api-contracts<=0.148.1.dev1+gfd4391914` ... needs `>=0.149.0`" error. All triggered by the
  SAME `ldr-to-main-promote-fleet` batch-promote tick (11:01:50-11:03:16Z, confirmed via each repo's `chore(promote):
  LDR → main` commit timestamp). instruments-service self-cleared on its own next natural build (11:37:49Z, after the
  wheel went live) — no manual re-run needed there.
- **`publish-package` "FAILED" for unified-api-contracts v0.149.0`** (Slack, ~11:19Z) — does not match current run
  history: `v0.149.0`'s `publish-package` GH Actions run (`32360286459`) shows `conclusion: success`, and the last 50
  runs of that workflow are all `success`. Likely the SAME underlying incident viewed from the publish side (the
  workflow's `twine upload` step reporting success while AR's indexing/propagation genuinely lagged ~12-31 min behind
  — consistent with the wheel-availability timeline above) rather than a distinct failure. NOT fully reconciled —
  whoever picks this up should treat "publish-package succeeded but wasn't immediately resolvable" as the same root
  cause, not a separate one.
- **agent-orchestrator "QG slice CANCELLED/TIMED-OUT" ×2** — unrelated class, own finding + doc: see
  `/plans/active/issues/agent_orchestrator_qg_cancel_notifier_same_sha_rerun_gap_2026_08_20.md`.
- **unified-trading-pm LDR went RED at `664cd60f`** (Plan hygiene hard gate slice) — self-healed within ~1 hour via the
  repo's normal high-velocity `docs(plans):` commit flow (green again by `ac502e5e`, 11:09Z). Which specific commit
  fixed the underlying violation, and whether it's a recurring/flaky check vs. a genuine one-off, was NOT identified
  this session — flagging as an open question, not closing it out.

## Progress Log

- **2026-08-20 (cicd slot-11, escalation `agt-8ab43f`)** — Verified resolved LIVE: failing build `77fbf981` root-caused
  to the UAC publish-ordering race; UAC `0.149.0` wheel confirmed live+resolvable on AR (HTTP 200); re-ran
  `strategy-service-build` on the same main HEAD → `10283751` SUCCESS (11:30:26→11:38:13Z), log shows
  `+ unified-api-contracts==0.149.0` installed from AR and `strategy-service:latest` re-pushed. No code change shipped —
  the pipeline was never structurally broken. Sibling failures noted for their own walls. Escalation closed.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
- **2026-08-20 (interactive, slot-1)** — Operator asked for the actual root-cause fix, not another self-heal
  confirmation, and specifically pushed back on a build-time-retry-inside-Cloud-Build design on cost grounds. Traced
  the fan-out chain (`unified-api-contracts` publish-package.yml → `update-repo-version.yml` → per-consumer
  `dependency-update` dispatch → floor-bump commit → promote → native Cloud Build trigger) and found the correct,
  cheap wiring point: `update-repo-version.yml`'s existing `resolve-gate` step, currently blind to AR. Documented the
  concrete fix above; not implemented this session (operator asked for the issue doc first so the implementation has
  full context). Also confirmed instruments-service self-cleared without intervention, and reconciled the
  `publish-package` "FAILED" alert against real run history (does not match — same incident, different vantage point).

**na-eligibility-audit 2026-08-21** (ci tranche wave 2, first audit pass — doc filed 2026-08-20): KEEP-NA, valid.
The doc's own primary "Implement" todo (line ~233) is explicitly gated: "operator review pending — do not ship
until reviewed" — cannot be dispatched ahead of that sign-off regardless of how bounded the implementation reads.
The remaining 4 todos are sizing/sequencing/defense-in-depth follow-ups explicitly scoped as secondary to that same
gated primary fix. No operator review recorded yet as of this pass (doc is 1 day old). No `assigned_vm` change.

- **2026-08-21 (cicd slot-24, escalation `agt-5560fb`)** — 3rd+ recurrence of the same class, this time
  `market-data-processing-service`. `cloud-build-failure-watcher` paged for build `71ad811a` (main @ `96fd90a5`,
  2026-08-21T12:32:01Z) — docker step 6 `uv pip install`: "× No solution found ... market-data-processing-service==0.32.7
  depends on unified-api-contracts>=0.159.0,<1.0.0" while AR's newest wheel at that moment was
  `0.158.1.dev1+gae56a4f9f` (0.159.0 published 4.5 min later at 12:36:34Z). Same-repo evidence of the class
  recurring on its own routine cadence, not just at a fleet-wide batch-promote tick: TWO EARLIER same-day MDPS
  failures against the PRIOR floor too — `71d477bd` (10:36:44Z) and `736cf29b` (10:15:33Z) both hit
  `unified-api-contracts<=0.157.1.dev1+g615972874` vs. a required `>=0.158.0` floor (0.158.0 never even shows in the
  `gcloud artifacts versions list` history — that floor-bump's own re-pin looks to have been superseded by the next
  one, `0.159.0`, before it ever resolved). Verified resolved LIVE the same way as the strategy-service instance:
  re-ran `market-data-processing-service-build` on the same `main` HEAD (`gcloud builds triggers run
  market-data-processing-service-build --branch=main`) → build `967d5bb2` **SUCCESS** (13:37→13:44:31Z, ~7min), log
  confirms `+ unified-api-contracts==0.159.2` (a later clean release, published in the interim) resolved and
  `market-data-processing-service:latest` (+ `96fd90a` + `0.32.7` tags) re-pushed. No MDPS code change made — per this
  doc's own root-cause section, the fix belongs in `update-repo-version.yml`'s `resolve-gate`, not in any consumer
  repo. Not implementing here — the doc's P2 "Implement" todo is still operator-review-gated; this entry is
  additional evidence for whoever picks that up, not a new investigation. Escalation closed.
- **2026-08-21 (cicd slot-31, escalation `agt-568ea1`)** — Another sibling of the SAME 2026-08-21 `0.159.0` floor wave
  as the MDPS entry above, this time `trading-agent-service`. `cloud-build-failure-watcher` paged for build
  `ccd69f30-9d09-40f8-a384-9261d3e408d7` (main @ `35be999b`, 2026-08-21T12:32:01Z, region asia-northeast1) — docker
  step 6 `uv pip install`: "× No solution found ... trading-agent-service==0.13.23 depends on
  unified-api-contracts>=0.159.0,<1.0.0" while AR's newest wheel at that moment was `0.158.1.dev1+gae56a4f9f`
  (`0.159.0` published ~3.7 min later at 12:36:34Z). Same repo also hit the PRIOR floor race earlier the same day:
  build `eb5be051-8c32-4d47-820a-5b59540b345a` (main @ `9de11645`, 2026-08-21T10:22:34Z) failed on
  `unified-api-contracts>=0.158.0` vs. only `<=0.157.1.dev1+g615972874` available — that one self-healed on its own
  next natural trigger (`55cf8fd5`, 11:07:01Z, SUCCESS) with no manual re-run needed. For the 12:32 failure: did NOT
  need a manual re-run either — by the time this escalation was triaged (~15:25Z), two later natural builds had
  already gone SUCCESS on their own (`ff19a6d9` 14:30:06Z, `294fee39` 14:38:27Z, both against `>=0.159.0` — current AR
  head is `0.161.1`). Verified LIVE: current `live-defi-rollout` `pyproject.toml` already carries the correct
  `unified-api-contracts>=0.159.0,<1.0.0` constraint (no drift), `origin/repo-blockers` has no open entry for
  `trading-agent-service`, and the most recent build is green — no code change needed, no re-run needed, nothing to
  ship. Root cause identical to every other entry in this doc: the fix belongs in `update-repo-version.yml`'s
  `resolve-gate`, not in any consumer repo; this entry is additional evidence for the still operator-review-gated P2
  "Implement" todo, not a new investigation. Escalation closed.
- **2026-08-21 (cicd slot-8, escalation `agt-069c25`, wall_type `cloud_build_router_failure`)** — Another sibling of
  the SAME 2026-08-21 `0.158.0`-floor wave as the `trading-agent-service` PRIOR-floor entry above, this time
  `instruments-service`. Escalated Cloud Build `95687259-49f9-48ab-ae2c-25779f33d853` (main @ `42f81d962b`,
  createTime 2026-08-21T10:53:53Z, FAILURE 11:06:25Z) — docker step 5 `uv pip install` (7 retry attempts, ~594s):
  "× No solution found ... instruments-service==0.104.0 depends on unified-api-contracts>=0.158.0,<1.0.0" while AR's
  newest wheel at that moment was `0.157.1.dev1+g615972874` (published 10:07:19Z) — `0.158.0` never resolved cleanly;
  AR went straight from `0.158.1.dev1+gae56a4f9f` (11:46:00Z) to `0.159.0` (12:36:34Z), the same never-a-clean-release
  pattern the MDPS entry above documented. Verified LIVE, no manual re-run needed: 10 consecutive natural
  `instruments-service-prod` builds since 12:51:16Z today are all SUCCESS (spot-checked through 16:50:40Z), current
  `live-defi-rollout`/`main` `pyproject.toml` already carries `unified-api-contracts>=0.159.0,<1.0.0` (no drift, matches
  the sibling repos' already-advanced floor), and current AR head is `0.161.2` — comfortably inside range. No open
  repo-blocker for instruments-service (`GET /api/repo-blockers` → only one open entry, an unrelated unified-trading-pm
  BATS finding `RB-fbd8d08f`). Root cause identical to every other entry in this doc: the fix belongs in
  `update-repo-version.yml`'s `resolve-gate`, not in any consumer repo; this entry is additional evidence for the
  still operator-review-gated P2 "Implement" todo, not a new investigation. Escalation closed.
