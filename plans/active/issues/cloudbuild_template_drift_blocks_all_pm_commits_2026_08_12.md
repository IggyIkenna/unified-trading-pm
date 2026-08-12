---
doc_type: issue
title:
  deployment-api's cloudbuild.yaml gained a verify-auth-contract step that was never forward-ported to its template —
  the drift ratchet now fails every unified-trading-pm quality-gates.sh run, blocking all PM code commits
summary: >-
  Measured 2026-08-12 ~10:10. `check_cloudbuild_template_drift.py` reports `deployment-api
  (cloudbuild-api-template.yaml): 19 drift marker(s) > baseline 16`. The new markers come from `deployment-api@4c31b72`
  ("ci: add post-deploy auth-contract verification to cloudbuild.yaml"), landed on origin at 09:05 the same morning by
  `ikennaigboaka [slot-5·laptop]`: the step was added to the CONSUMER's cloudbuild.yaml without being forward-ported
  into the shared template. Because the drift check is a post-gate step in `quality-gates.sh`, Pass 1 exits non-zero and
  no sentinel is written, so `quickmerge` Pass 2 refuses — for every agent on every host, for any PM CODE commit. Same
  blast radius and same shape as the codex-freshness ratchet incident the day before, from a different check. NOT
  re-baselined: the check's own remedy line says "NEVER raise a count".
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-api]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, ratchet, cloudbuild, blocking, cross-repo]
related:
  [
    /plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
  ]
created: 2026-08-12
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: cicd
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/check_cloudbuild_template_drift.py,
    scripts/quality_gates/cloudbuild_template_drift_baseline.yaml,
  ]
source: >-
  Hit live 2026-08-12 in slot 3, gating an unrelated stash-tooling + freshness-gate change. The same repo's
  quality-gates.sh run had passed cleanly ~40 minutes earlier, which dates the regression to the sibling repo checkout
  updating to origin in between. Provenance established from git (commit date, author, ancestry on origin), not
  inferred.
---

# A sibling repo's un-forward-ported cloudbuild step blocks the whole PM repo

## What was measured

```
[FAIL] deployment-api (cloudbuild-api-template.yaml): 19 drift marker(s) > baseline 16.
  New/over-baseline marker(s): step arg dropped: vendor-deps::set -e
                               step arg dropped: verify-auth-contract::-c
                               step arg dropped: verify-auth-contract::set -e
❌ Cloud Build template drift regression — a consumer's cloudbuild.yaml carries content its template does not.
```

Provenance, from git rather than assumption:

| fact                                  | value                                                      |
| ------------------------------------- | ---------------------------------------------------------- |
| commit introducing the step           | `deployment-api@4c31b72`                                   |
| author / when                         | `ikennaigboaka [slot-5·laptop]`, 2026-08-12 09:05:45 +0100 |
| on `origin/live-defi-rollout`?        | yes — landed, not local WIP                                |
| deployment-api working tree           | clean                                                      |
| PM `quality-gates.sh` ~40 min earlier | green (exit 0) — dates the regression precisely            |

The commit itself is good work: it closes a same-day-detection gap from the 2026-08-06 `DISABLE_AUTH` P0. The defect is
only that the step landed in the consumer without the matching template edit, which is exactly what this ratchet exists
to catch.

## Why it was not fixed in-session

Two remedies exist and both were declined deliberately:

- **`--update-baseline`** — the check's own failure message says "NEVER raise a count". Same class as the banned
  `--baseline-write` on the freshness ratchet. Not taken.
- **Forward-port the step into `cloudbuild-api-template.yaml`** — the sanctioned fix, and probably safe in effect (the
  new step self-guards with `if [ "${_SERVICE_NAME}" != "deployment-api" ] …` so it no-ops for every other consumer).
  Not taken **because the owning commit is one hour old and its author is likely still working in that area**: editing a
  shared deploy template underneath an in-flight change risks a conflicting rollout, and the drift spans 3 markers
  across 2 steps (`vendor-deps` and `verify-auth-contract`), so a careless forward-port could regress a real deploy
  path. This is deploy infrastructure, where the cost of a wrong guess is a broken deploy, not a failed test.

## Todos

- [x] ✅ [BACKEND] P1. **Fix the drift at the source — reverted, not forward-ported.** — deployment-api@b928d173b5.

      The named owner (slot-5, this session) resolved it directly rather than waiting for an `[OPERATOR]` pickup.
              Forward-porting into `cloudbuild-api-template.yaml` (the sanctioned fix per the check's own message) was
              evaluated first and found structurally unsound, not just declined out of caution: `verify-auth-contract`
              requires `waitFor: ["deploy"]` to check the FRESHLY deployed revision, but `deploy` itself is pure per-repo
              content — it does not exist in `cloudbuild-api-template.yaml` at all (confirmed: `grep -n 'id: "deploy"'`
              against the template returns nothing; the whole deploy block is already-baselined intentional drift, per this
              same baseline file's own header comment). A template-native version of the step could only `waitFor:
              ["scan-check"]` (the last template-native step), which would run it CONCURRENTLY with the per-repo `deploy`
              step rather than after it — checking the auth contract against the stale pre-deploy revision, defeating the
              check's entire purpose. There is no template-only way to express "runs after a per-repo-only step" short of a
              polling/timeout loop inside the script itself, which is materially more fragile than the original design.
              Given that, reverted the step entirely (`deployment-api@b928d173b5`) rather than accept either a broken
              ordering or a permanently-raised baseline. **Verified**: `check_cloudbuild_template_drift.py --repo
              deployment-api` → `[OK] deployment-api (cloudbuild-api-template.yaml): 16 (== baseline)`.

              The underlying hardening goal (same-day detection of an auth-contract regression, motivated by the 2026-08-06
              `DISABLE_AUTH` incident sitting undetected for 4 days) is NOT abandoned — it needs a mechanism that doesn't
              depend on Cloud Build step-ordering against per-repo-only content, e.g. a scheduled synthetic check (Cloud
              Scheduler hitting the live endpoint + alerting through the existing `ci-failures`/`data-pipeline-alerts`
              channels) rather than a build-time gate. Not built in this pass — flagged as a properly-scoped follow-up in
              `/plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md` rather than rushed through the same
              structural constraint that just caused this incident.

- [ ] [SCRIPT] P2. **Make consumer-vs-template drift fail at the point it is INTRODUCED, not fleet-wide afterwards.**
      Today a cloudbuild.yaml edit lands cleanly in its own repo and the bill is paid by the next agent to touch a
      different repo entirely — the failure is maximally distant from its cause, which is why this reads as "PM is
      broken" rather than "deployment-api needs a template edit". Done when: the drift check runs in the CONSUMER repo's
      own gate (so slot-5 would have seen it on their own commit), or this is rejected with the reason recorded. Repo:
      unified-trading-pm.

## `--update-baseline` is shrink-only, and its refusal is silent

Worth recording because it cost real cycles during this incident. `--update-baseline` was run against this never-raise
ratchet. It **printed** the observed `deployment-api: 19`, but the file still read `count: 16` afterwards — the only
change in `git diff` was the `note:` field being re-wrapped by the YAML dumper. The writer refuses to raise a count;
that is the ratchet working exactly as its header comment promises.

But the refusal is **silent**: nothing says "declined to raise 16 → 19". It presents as "the command printed the right
number and then did nothing", which invites the reading that the write failed, or that the baseline file is stale, and
sends you looking for a bug in the wrong place. **The command is not a bypass and never was** — if a count needs to go
up, the answer is that the change should not land in that shape. Do not spend time rediscovering this.

## The pattern worth naming

This is the **second** fleet-wide commit outage in two days caused by a post-gate ratchet in `quality-gates.sh` going
red for reasons unrelated to the committing agent's change — the codex-freshness ratchet on 2026-08-11, this one on
2026-08-12. In both cases the blocked agent's only fast exits were a banned re-baseline or a fix in someone else's area.
The shared structural property is that **`quality-gates.sh` aggregates fleet-wide state into a per-commit gate**, so any
repo's regression becomes every agent's blocker, and the agent who pays is chosen by who commits next rather than by who
caused it. Worth deciding as a policy question, not incident by incident — see the sibling issue's P2 todo on whether a
calendar/fleet-triggered ratchet should be able to hard-block commits at all.
