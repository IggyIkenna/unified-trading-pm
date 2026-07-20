---
doc_type: issue
title: >-
  rollout-cloudbuild.py was a loaded gun — the PM cloudbuild template was BEHIND all 19 consumer repos, so running the
  documented rollout would have silently reverted two production fixes fleet-wide
summary: >-
  scripts/propagation/rollout-cloudbuild.py overwrites every repo's cloudbuild.yaml from
  configs/cloudbuild-*-template.yaml. MEASURED 2026-07-20 - the template was MISSING two fixes that every service repo
  carries - (1) the AUTHENTICATED `--unshallow` fetch with `secretEnv: [GH_PAT]` + `availableSecrets`, without which
  Cloud Build's shallow UNAUTH clone leaves git describe unable to see the v-tag and hatch-vcs fails inside the docker
  build; (2) the `VERSION="0.0.0.dev0"` fallback, which is both PEP440-valid and docker-tag-safe where the template's
  bare short-sha fallback is neither. A dry-run showed 19 files would be rewritten and a real render of
  market-tick-data-service dropped both fixes. The template is now forward-ported so a rollout is safe; the remaining
  gap is that NOTHING detects template-vs-repo drift, so the same trap can reopen the moment a repo fixes something the
  template does not learn.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, fleet-rollout, template-drift, blast-radius]
related:
  [
    cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md,
    uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-20 while root-causing the cloud-build-failure-watcher alerts; the template fix was shipped in the
    same session, the drift DETECTION is what remains",
  ]
locked_by:
locked_since:
resolved_by:
---

# The rollout tool would have regressed the fleet

## What was measured

`scripts/propagation/rollout-cloudbuild.py --dry-run` → **19 files would be rewritten**. Rendering
`market-tick-data-service` for real produced a **73-line diff** against the live file, and the diff was not cosmetic —
it DROPPED:

| Fix present in every repo, absent from the template                              | Consequence of the rollout                                                                                                                        |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `secretEnv: ["GH_PAT"]` + authenticated `--unshallow` fetch + `availableSecrets` | Cloud Build's shallow + UNAUTH clone leaves `git describe` unable to see the v-tag → hatch-vcs "unable to detect version" inside the docker build |
| `VERSION="0.0.0.dev0"` fallback                                                  | The template's bare short-sha fallback is NOT PEP440-valid; the live comment records that `+local` is also invalid as a docker tag                |

Both are documented in-file in the repos with the incident that motivated them. The template had learned neither.
Verified the pattern is fleet-wide, not one repo: `instruments-service`, `features-service`, `execution-service`,
`strategy-service` all carry `unshallow` and `0.0.0.dev0`; the template carried zero.

This is precisely the rule-11 anti-pattern — "shipped, looked done locally, broke the fleet" — except the gun was
already loaded and pointed, waiting for anyone to run the documented rollout command.

## Fixed in this session

- **Forward-ported** both fixes into `configs/cloudbuild-service-template.yaml`, so a render is now equivalent to the
  live files. Re-verified by rendering MTDS again: `secretEnv`/`unshallow`/`0.0.0.dev0`/ `availableSecrets` all
  preserved 1:1, diff down from 73 lines to only the additive guard below.
- **Added a fail-fast empty-tag guard** to the same template. `SHORT_SHA` is a Cloud Build built-in populated ONLY for
  repoSource (trigger) builds; a manual `gcloud builds submit` uses a storageSource and leaves it empty, and
  `substitutionOption: ALLOW_LOOSE` passes the empty value straight through — so the tag becomes `<svc>:` and docker
  dies with `invalid reference format` / exit 125 six steps in. MEASURED: that is exactly what build `7c7aedaf`
  (market-tick-data-service, 12:28Z) did. The guard now falls back SHORT_SHA → VERSION (so a manual submit RECOVERS
  rather than failing) and hard-fails with a diagnostic naming the empty variable only when both are genuinely
  unresolvable.
- The guard's prose comments carry **no bare dollar-prefixed names** — the substitution validator scans comment lines
  inside a bash block, which caused a documented double-rejection on 2026-06-10.

## What remains — the actual gap

**Nothing detects template-vs-repo drift.** The forward-port fixes today's divergence but not the mechanism: the next
time a repo fixes something the template does not learn, the rollout tool is re-armed and the next person to run it
silently regresses the fleet again.

## Todos

- [ ] [DEVOPS] P1. Add a drift check that renders each template and diffs it against every consumer's committed
      `cloudbuild.yaml`, failing (or loudly warning) when a repo carries content the template does not. Wire it into
      PM's `quality-gates.sh` so the divergence surfaces at gate time, not at rollout time.
- [ ] [DEVOPS] P2. Make `rollout-cloudbuild.py` refuse to write a file whose live content contains markers absent from
      the rendered output (a "would drop content" guard), so the tool cannot regress a repo even if the drift check is
      bypassed. Default to `--dry-run` and require an explicit `--apply`.
- [ ] [DEVOPS] P2. Roll the empty-tag guard out to the 19 consumer repos once the drift check exists (each needs its own
      repo QG + quickmerge). Not urgent: the per-repo copies already carry the important fixes, and the guard only
      changes behaviour for manual `gcloud builds submit`, which is not the normal path.
- [ ] [DEVOPS] P3. Reconcile the same question for the other templates (`cloudbuild-api-template.yaml`, `-ui-`,
      `-infra-`, `-sit-`) — this session only measured and fixed the SERVICE template.

## Progress Log

- **2026-07-20** — Found while root-causing the `cloud-build-failure-watcher` alerts. Three things shipped together: the
  template forward-port, the empty-tag guard, and the watcher's misclassification fix (see the
  `cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md` lineage). During investigation I rendered MTDS's
  file twice to measure the diff and restored it from git both times — verified byte-identical to its pre-write state,
  and the repo's foreign dirty WIP was never touched.
