---
doc_type: issue
title: >-
  Additional lead for deployment_api_sigabrt_crash_loop_2026_07_24.md: a 100%-reproducible fresh-cold-start
  `exit(0)`+STARTUP-probe failure on non-live uts-shared-deployment-api revisions, surfaced separately while wiring
  uts-prd-sa
summary: >-
  Cross-referencing Finding 6 of `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`
  (slot-5, executing `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2c) into this SIGABRT investigation's line,
  per that doc's own P2 todo. While live-verifying `deployment-api`'s Cloud Run identity change to `uts-prd-sa`, every
  fresh cold start of a NON-100%-traffic (tagged or newly-deployed) revision of `uts-shared-deployment-api` failed 100%
  reproducibly across 4 independent attempts (2 before, 2 after fixing an unrelated `deploy-shared.sh` resource-sizing
  drift from 4Gi/2cpu to the documented 16Gi/4cpu) with the identical signature: `WARNING Container called exit(0)`
  immediately followed by `ERROR Default STARTUP TCP probe failed ... The instance was not started.` — no application
  stdout/stderr precedes it. Both the old SA (`unified-trading-sa`) and the new SA (`uts-prd-sa`) failed identically at
  a given resource size, so SA identity is not the driving variable; the memory/CPU fix was real (worth keeping) but not
  sufficient on its own. This resembles this doc's own SIGABRT (signal 6) crash-loop but was observed at a DIFFERENT
  lifecycle point: this doc's investigation is scoped to the ALWAYS-WARM, 100%-traffic revision (an intermittent runtime
  crash on an already-serving instance), while the new data point is a 100% failure rate on a fresh cold start of a
  non-live revision that never reaches a state where it can serve a first request. Not independently investigated
  further here, per that doc's ownership of the mechanism — filed as a satellite lead doc because the SIGABRT doc is
  at/over its 1000L hard cap (1001 lines), so a direct append would fail the SCOPED prek line-cap gate on any commit
  touching that file.
status: resolved
nature: issue
asset_group: [ui]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [engineer]
tags: [cloud-run, cold-start, sigabrt, crash-loop, observability, lead]
related:
  [
    /plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md,
    /plans/active/issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
source: >-
  Surfaced 2026-07-31 (slot-4, infra) executing the P2 cross-reference todo in
  `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`, itself filed 2026-07-31 (slot-5,
  infra) while executing `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2c.
resolved_by: "slot-14 2026-07-31T22:20Z, folded into deployment_api_sigabrt_crash_loop_2026_07_24.md's [INFRA] P0 todo"
locked_by:
locked_since:
depends_on: []
---

> **🟢 RESOLVED / ARCHIVED 2026-07-31 — this doc's one todo is done and folded into
> `/plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md`'s open `[INFRA] P0` cold-container todo (slot
> 14, 2026-07-31T22:20Z). No further action here — see that doc for the live investigation.**

# Additional lead for the SIGABRT crash-loop investigation: reproducible fresh-cold-start failure on non-live revisions

## What I found

(cross-reference only — full detail lives in the source doc.)

`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`'s Finding 6 (that doc's
`## What I found`, items 4-6) reports: while live-verifying `deployment-api`'s Cloud Run identity change to `uts-prd-sa`
(executing `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2c), every fresh cold start of a NON-100%-traffic
(tagged or newly-deployed) revision of `uts-shared-deployment-api` failed 100% reproducibly across 4 independent
attempts (2 pre-fix, 2 post-fix of an unrelated `deploy-shared.sh` resource-sizing drift — 4Gi/2cpu -> 16Gi/4cpu) with
the identical signature:

```
WARNING Container called exit(0)
ERROR Default STARTUP TCP probe failed 1 time consecutively... The instance was not started.
```

No application stdout/stderr precedes it. Both SA identities (old `unified-trading-sa` and new `uts-prd-sa`) failed
identically at a given resource size — SA is not the driving variable. The memory/CPU fix (4Gi/2cpu -> 16Gi/4cpu,
matching `cloudbuild.yaml`'s documented 2026-07-17 sizing) was real and worth keeping but was NOT sufficient on its own
to prevent this failure.

## Why it matters for this investigation

`deployment_api_sigabrt_crash_loop_2026_07_24.md` has exhaustively investigated an `Uncaught signal: 6` (SIGABRT)
crash-loop scoped to the ALWAYS-WARM, 100%-traffic revision — an intermittent RUNTIME crash on an already-serving
instance, with no fresh-instance-start visible in the surrounding log. The new data point above is shaped differently (a
100%-reproducible failure on ANY fresh cold start of a non-live/tagged revision, never even reaching a state where it
could serve a first request) but is plausibly the SAME root cause expressed at a different point in the container
lifecycle (startup vs. steady-state). Not independently investigated here — flagging as an additional lead for whoever
next works the SIGABRT doc, per that doc's own pattern of "fresh, narrower follow-up rather than re-guessing." That doc
is at/over its 1000-line hard cap (`check_line_caps.sh`, `PLAN_HARD_CAP=1000`), so this lead is filed as a satellite doc
rather than appended directly (a direct append would fail the SCOPED prek line-cap gate on any commit touching that
file) — same pattern already used for `deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31.md`.

## Recommended next step

Whoever next picks up `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s investigation: read this doc's
cross-referenced source (`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`) findings
4-6 as an additional data point — specifically whether the cold-start `exit(0)`+STARTUP-probe failure and the
always-warm SIGABRT share a common trigger (e.g. a resource/memory threshold effect, a signal-handler / exec'd-
subprocess interaction that also manifests at container start, or a sandbox-external-termination independent of request
volume).

## Todos

- [x] ✅ [BACKEND] P2. Read `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md` Finding
      6 (100%-reproducible fresh-cold-start `exit(0)`+STARTUP-probe failure on non-live revisions) as an additional lead
      when next working `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s SIGABRT investigation — determine whether it
      shares the same root cause as the always-warm signal-6 crash, or is a distinct failure mode. (repo:
      deployment-api) — **DONE 2026-07-31T22:20Z (slot 14, infra)**: read + folded in via a new dated entry directly on
      `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s open `[INFRA] P0` cold-container todo. Independently
      corroborates this doc's own "SA identity is not the driving variable" finding: fixed BOTH the project-role gap AND
      a separately-found empty SA-level Cloud Run Service Agent `tokenCreator` binding on `uts-prd-sa`, retested, zero
      effect on the failure. Went further via a scoped diagnostic log sink (bypasses the project's `_Default`
      severity-exclusion for just this service): the failing container emits ZERO output ever, before gunicorn's own
      first log line, while a concurrent canary logs fine in the same window — narrows the shared mechanism to the
      container-exec layer for this resource profile, not IAM/SA identity, not the app. Filed a fresh `[INFRA]`
      follow-up on the SIGABRT doc carrying this forward (test lighter resource profile / gen2, or escalate to Google
      Cloud Support). This satellite doc's own scope is now fully folded in — no further action needed here.
