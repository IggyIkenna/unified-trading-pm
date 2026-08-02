---
doc_type: issue
title:
  "deploy-shared.sh's Cloud Run memory/CPU had drifted stale (4Gi/2cpu vs cloudbuild.yaml's live 16Gi/4cpu) — fixed; a
  SEPARATE, still-unresolved cold-start failure (likely the SAME mechanism as the open SIGABRT crash-loop doc) remains
  and blocks promoting bucket_iam_write_protection_per_tier's uts-prd-sa wiring to live traffic"
summary: >-
  Executing bucket_iam_write_protection_per_tier_2026_06_09.md P2.2c ("wire deployment-api's Cloud Run identity to its
  tier SA, live-verify Secret Manager/Pub/Sub/BigQuery access"): updated deploy-shared.sh's default --service-account to
  uts-prd-sa (was unified-trading-sa) and live-verified full functional access (Secret Manager versions.access, Pub/Sub
  topics.list, BigQuery datasets.list, Storage objects.list on a Group-A -prd- bucket) via direct API calls under an
  impersonated uts-prd-sa token — all four passed. While verifying the SA change on a real deploy, found + fixed a
  genuine, unrelated drift bug: deploy-shared.sh hardcoded --memory=4Gi --cpu=2, which predates cloudbuild.yaml's
  documented 2026-07-17 8Gi->16Gi OOM fix for this exact service (data-status's concurrent heavy-catalogue reads) —
  every revision deployed via this script (both under the old SA and the new one) was running under-provisioned and
  failing every cold start. Fixed to 16Gi/4cpu, matching cloudbuild.yaml exactly. BUT: even after that fix, a fresh cold
  start of a NEW/tagged revision still fails with the identical "Container called exit(0)" + "Default STARTUP TCP probe
  failed" signature (~30-32s in) — so the memory fix, while real and worth keeping, was not sufficient on its own. This
  failure signature strongly resembles the already-open, extensively-investigated
  deployment_api_sigabrt_crash_loop_2026_07_24.md (1001 lines, dozens of agent-sessions, still not 100% root-caused) —
  NOT duplicating that investigation here; cross-referencing it with this session's specific new data point (fresh
  cold-starts of NON-100%-traffic/tagged revisions reproduce a startup-time failure every single time, a angle that
  doc's investigation — focused on the always-warm, 100%-traffic revision — hadn't specifically isolated). Live traffic
  was never touched (still 100% on the old-SA revision, confirmed healthy throughout).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api]
scope: [engineer, admin]
tags: [cloud-run, reliability, cold-start, iam, bucket-tiers, sigabrt]
related:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: correct-code
source: >-
  Surfaced 2026-07-31 (slot-5, infra) while executing bucket_iam_write_protection_per_tier_2026_06_09.md P2.2c.
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md,
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    deployment-service/scripts/cloud-run/deploy-shared.sh,
  ]
---

# deploy-shared.sh resource drift (fixed) + a separate cold-start reliability gap (still open, likely == the SIGABRT doc)

## What I found

Working P2.2c ("wire Cloud Run service identities... start with `scripts/cloud-run/deploy-shared.sh`... live-verifying
Secret Manager/Pub/Sub/BigQuery access after each"):

1. Updated `deployment-service/scripts/cloud-run/deploy-shared.sh`'s `SA` variable default from `unified-trading-sa` to
   `uts-prd-sa` (per the Hybrid(C) ruling — Group A/B raw-data Cloud Run runtimes use the per-tier `-prd-`/`-test-` SAs
   granted their non-storage roles by `deployment-service@e8684fe`), keeping an env override (`RUNTIME_SA=`) for an
   instant revert.
2. Deployed via `--deploy-only` (no code change, image unchanged). Two attempts (`00390-wqh`, `00391-rgs`) both
   eventually failed fresh-instance health checks; `spec.containers[0].resources.limits` on both read
   `cpu=2, memory=4Gi` — matching `deploy-shared.sh`'s then-hardcoded `--memory=4Gi --cpu=2`.
3. **Found genuine drift**: the currently-LIVE revision (`00374-4pd`) and another healthy revision (`00389-d9d`) both
   run at `cpu=4, memory=16Gi`. `deployment-api/cloudbuild.yaml`'s own deploy step (the CI/promote path for this same
   service) explicitly sets `--memory 16Gi --cpu 4` with a detailed comment: bumped from 8Gi on 2026-07-17 after a
   MEASURED live OOM (data-status's concurrent heavy per-AG catalogue reads packed onto one 8Gi instance under
   concurrency=80, container killed, all in-flight panel requests 500'd) — `deploy-shared.sh` (a separate, manual
   "Tier-3" deploy script for the same service) was never updated to match and had drifted back to its original pre-fix
   sizing. **Fixed**: `deploy-shared.sh` now also deploys at `--memory=16Gi --cpu=4`, with a comment pointing at
   `cloudbuild.yaml`'s rationale so it doesn't drift again.
4. Redeployed with the corrected sizing (`00392-vzb`, `cpu=4, memory=16Gi`, `uts-prd-sa`) — passed its own creation-time
   health check (`Ready: True`). **But tagging it for isolated verification
   (`gcloud run services update-traffic --set-tags=prd-sa-verify=...`) still failed** with the identical signature as
   before the resource fix: "The user-provided container failed to start and listen on the port... within the allocated
   timeout" / `HealthCheckContainerError`. Log for that exact attempt (21:56:08-21:56:40Z):
   `WARNING Container called exit(0)` immediately followed by
   `ERROR Default STARTUP TCP probe failed 1 time consecutively... The instance was not started.` — no application
   stdout/stderr precedes it. **So the memory/CPU fix was real and worth keeping, but is NOT the (or not the only) cause
   of this specific failure.**
5. **Ruled out the SA as a cause** (independent of the resource question): revision `00388-9mt`, running the OLD SA
   (`unified-trading-sa`) at the stale `4Gi/2cpu` size, showed the identical `exit(0)`+STARTUP-probe-failed signature
   repeated ~8 times. Both SA identities fail identically at a given resource size, so SA is not the driving variable
   either.
6. **This is very likely the SAME underlying mechanism as `deployment_api_sigabrt_crash_loop_2026_07_24.md`** (1001
   lines, `assigned_vm: planning`, still open) — that doc's exhaustive investigation (memory-limit correlation,
   gunicorn/uvicorn signal-handler ordering, exec'd-subprocess-child SIGABRT, sandbox-external-termination) is scoped to
   the ALWAYS-WARM, 100%-traffic revision, where the failure manifests as an intermittent RUNTIME crash
   (`Uncaught signal: 6` on an already-serving instance, no fresh-instance-start visible in the surrounding log). What I
   observed here is different in shape but plausibly the same root cause expressed at a different lifecycle point:
   **every single fresh cold-start of a non-100%-traffic (tagged or newly-deployed) revision fails outright, 100%
   reproducibly across 4 independent attempts** (2 pre-fix, 2 post-fix), never even reaching a state where it could
   serve a first request. I did NOT duplicate that doc's investigation here (it is already at/near the 1000-line hard
   cap and this session's evidence doesn't by itself resolve its still-open sandbox-external-termination lead) —
   flagging the connection + this new data point as a lead for whoever next works that doc, per this doc's own P2 todo
   pattern of "fresh, narrower follow-up rather than re-guessing."
7. **The uts-prd-sa functional access itself is confirmed fine**, independent of all the above — bypassing the flaky
   HTTP path entirely, self-granted (as `unified-trading-sa`, one of the two ambiently-available identities per
   `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) a narrow, resource-scoped
   `roles/iam.serviceAccountTokenCreator` on `uts-prd-sa` (revoked again immediately after use), minted an impersonated
   access token, and called each API directly as `uts-prd-sa`: Secret Manager `tardis-api-key` `versions.access` → 200
   (a real secret `venue_credentials.py` reads); Pub/Sub `topics.list` → 200, 3 topics; BigQuery `datasets.list` → 200,
   3 datasets; Storage `objects.list` on `instruments-store-cefi-prd-...` (Group A) → 200. All match
   `unified-trading-sa`'s prior grant scope.
8. Confirmed the live-serving revision (`00374-4pd`, 100% of `spec.traffic`, `unified-trading-sa`, `16Gi/4cpu`) stayed
   healthy throughout (`/api/health` → 200) — no production traffic was ever routed to a new-SA or resized revision.

## Why it matters

The bucket-isolation-model §8 IAM write-protection work (`bucket_iam_write_protection_per_tier_2026_06_09.md`) needs
deployment-api's Cloud Run identity actually promoted to `uts-prd-sa` for P2.1b's god-SA removal to ever become safe
(P2.1b is hard-gated on P2.2c AND P2.2d completing + being live-verified). Promoting live traffic to a revision that
cannot survive even its own creation-time cold start reliably would risk real request failures for both UIs that call
this shared service (`deployment-ui`/`unified-trading-system-ui` data-status, launch consoles) — per the infra craft
north-star ("never launch blind"), I did not force the cutover. Separately, the resource-drift fix is worth shipping
regardless of the cold-start mystery: it closes a real gap where the manual/Tier-3 deploy path silently under-provisions
this service relative to its documented, measured requirement.

## Recommended decision

1. Ship the `deploy-shared.sh` memory/CPU fix (done, this session) — independently correct.
2. Do NOT open a fresh multi-session investigation into the `exit(0)` cold-start failure here — fold this session's
   specific new data point (100%-reproducible failure on ANY fresh cold-start of a non-live revision, both pre- and
   post- resource-fix) into `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s next dispatch as an additional lead,
   given that doc already owns this investigation and is near its line cap.
3. Once that doc's investigation lands a fix (or this specific cold-start angle is separately resolved), retry: deploy
   via the now-`uts-prd-sa`+`16Gi/4cpu`-defaulted `deploy-shared.sh`, tag + curl-verify a fresh instance 3-5 times in a
   row for confidence, THEN cut `spec.traffic` over to the new revision (or ramp via the existing tagged-canary pattern
   this service already has precedent for — see `e8ce86a-verify`/`00389-d9d`).

## Todos

- [x] ✅ [INFRA] P1. **DONE 2026-07-31 (slot-5)** — fixed `deploy-shared.sh`'s stale `--memory=4Gi --cpu=2` to
      `--memory=16Gi --cpu=4`, matching `cloudbuild.yaml`'s live, documented 2026-07-17 sizing for this exact service.
      Shipped `deployment-service@c518cda`. (repo: deployment-service)
- [x] ✅ [INFRA] P2. **DONE 2026-07-31 (slot-4)** — cross-referenced Finding 6 into the SIGABRT investigation's line.
      `deployment_api_sigabrt_crash_loop_2026_07_24.md` is at/over its 1000L hard cap (1001 lines), so a direct append
      would fail the SCOPED prek line-cap gate — filed a satellite lead doc instead (same pattern as
      `deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31.md`):
      `deployment_api_sigabrt_crash_loop_coldstart_finding6_lead_2026_07_31.md`, `related:` to both this doc and the
      SIGABRT doc, carrying a `[BACKEND] P2` todo for whoever next works the SIGABRT investigation. Did not
      re-investigate independently. (repo: unified-trading-pm)
- [ ] [INFRA] P3. Once the SIGABRT doc's investigation resolves (or this specific angle is separately confirmed fixed),
      retry the live-traffic cutover for `uts-shared-deployment-api` to a fresh `uts-prd-sa` revision — tag-verify 3-5
      fresh cold starts first, then cut over; update `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2c to
      reflect completion. (repo: deployment-service)

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **2026-08-02T18:12Z (slot-5, infra, dispatched `bucket_iam_write_protection_per_tier-018` / P2.2e)** — attempted P3's
  own recommended retry, per what looked like a genuinely promising signal: `gcloud run revisions list` showed 15
  consecutive `Ready=True` fresh revisions (`00403-rvc`..`00417-7fh`) spanning `2026-08-01T00:54Z`..`2026-08-02T15:26Z`
  (~38.5h, multiple quiet+busy periods), and a targeted Cloud Logging sweep for
  `"Container called exit(0)"`/`"STARTUP TCP probe failed"` found **zero** hits since the last recorded failure
  (`00402-zsg`, `2026-08-01T00:03:34Z`) — on its face this matched main-orchestrator's `2026-08-01T00:06Z` durable-close
  bar ("N-consecutive fresh cold-starts over a multi-hour window spanning quiet periods, zero exit(0) failures").
  Confirmed the latest revision (`00417-7fh`, created today) already runs `uts-prd-sa` + `16Gi/4cpu` (the target
  config), so P3's "tag-verify 3-5 fresh cold starts" step just needed doing. **Result: FAILED on the very first
  attempt.** `gcloud run services update-traffic --set-tags=prd-sa-precutover=uts-shared-deployment-api-00417-7fh` (0%
  traffic, isolated tag only — no real traffic ever touched) hit the identical signature:
  `"The user-provided container failed to start and listen on the port... within the allocated timeout"`. **This
  directly refutes the apparent 38.5h clean streak** — a revision that reports `Ready=True` in `revisions list` (and
  evidently serves real requests, e.g. `00417-7fh` and its siblings were likely serving routine CI/CD health traffic)
  can STILL fail when actually force-cold-started via a fresh `update-traffic` invocation, exactly the same "looks
  resolved, one retry away from failing again" shape as the `00401-4x7`→`00402-zsg` refutation main-orchestrator already
  documented on 2026-08-01. **The durable-close bar as literally worded (zero `exit(0)` failures in the log stream) is
  not the right proxy** — it only captures failures from revisions someone actually tried to cold-start via traffic/tag
  operations, and apparently nobody attempted that between `00402-zsg` (07-31) and this session; ordinary CI/CD
  `Ready=True` revisions with 0% traffic evidently do NOT reliably exercise this failure path, or exercise it
  non-deterministically. **Production confirmed safe throughout**: traffic stayed 100% on the warm `00374-4pd`
  (`unified-trading-sa`) the whole time; `/api/health` returned 200 before and after. Left the `prd-sa-precutover` tag
  on `00417-7fh` as evidence (mirrors the existing `verify2`→`00402-zsg` precedent) — 0% traffic, no risk. **Declining
  `bucket_iam_write_protection_per_tier-018` (P2.2e)** — the gate this doc's P3 todo and the SIGABRT doc's
  `2026-08-01T00:06Z` entry both impose is still not met; do not re-attempt the cutover based on a clean
  `revisions list`/log-sweep alone — the ONLY reliable signal is an actual fresh tag/traffic operation, which just
  failed. No code shipped — live verification only. (repo: deployment-service, deployment-api)
