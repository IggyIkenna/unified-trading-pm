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
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, fleet-rollout, template-drift, blast-radius]
related:
  [
    /plans/archive/issues/cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md,
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
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

- [x] ✅ [DEVOPS] P1. **DONE 2026-07-28 (slot-13, infra)** — delivered standalone
      `scripts/quality_gates/check_cloudbuild_template_drift.py`: renders every `configs/cloudbuild-*-template.yaml` via
      `rollout-cloudbuild.py`'s own `generate_cloudbuild()` and diffs each render against the matching consumer's
      committed `cloudbuild.yaml` via the same `find_dropped_markers()` the rollout tool's would-drop-content guard
      uses, with a shrinking-ratchet baseline (`cloudbuild_template_drift_baseline.yaml`, seeded 2026-07-28 at the
      fleet's real per-repo counts). **Deliberately NOT wired into `scripts/quality-gates.sh`** — that wiring is its own
      gated finalize-plan todo (`ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`), same pattern as the
      `check_no_swallowed_credential_fetch.py` checker shipped alongside it. unified-trading-pm@(this commit — see
      plan). `tests/unit/test_check_cloudbuild_template_drift.py` (14 cases) proves a synthetic template-lags-repo case
      fails at a seeded baseline, plus the API-template path (not just SERVICE).
- [x] ✅ [DEVOPS] P2. **DONE 2026-07-28 (slot-9, infra)** — `rollout-cloudbuild.py` refuses to write a file whose live
      content contains markers absent from the rendered output; default flipped to `--dry-run`, write requires
      `--apply`. unified-trading-pm@ddf0b89f4. Full details + the drift measurement below in the Progress Log; also
      recorded on `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` item 5.
- [ ] [DEVOPS] P2. Roll the empty-tag guard out to the 19 consumer repos once the drift check exists (each needs its own
      repo QG + quickmerge). Not urgent: the per-repo copies already carry the important fixes, and the guard only
      changes behaviour for manual `gcloud builds submit`, which is not the normal path.
- [x] ✅ [DEVOPS] P3. **DONE 2026-07-28 (slot-13, infra)** — the new drift checker covers ALL FIVE templates, not just
      SERVICE (see the per-template measurement in the Progress Log below): `-api-`, `-ui-`, `-infra-`, `-sit-` are now
      all measured, matching the checker's default scope (every consumer `rollout-cloudbuild.py --apply` would touch).

## Progress Log

- **2026-07-20** — Found while root-causing the `cloud-build-failure-watcher` alerts. Three things shipped together: the
  template forward-port, the empty-tag guard, and the watcher's misclassification fix (see the
  `cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md` lineage). During investigation I rendered MTDS's
  file twice to measure the diff and restored it from git both times — verified byte-identical to its pre-write state,
  and the repo's foreign dirty WIP was never touched.
- **2026-07-28** — Shipped the P2 "would drop content" guard (unified-trading-pm@ddf0b89f4). While proving it against
  the real fleet (`--dry-run`, no `--apply`), measured that the drift has grown well past the single 2026-07-20
  near-miss: **15 of 19 consumers now carry content the SERVICE template does not** — not cosmetic, whole steps (MTDS's
  `stage-workspace-deps`/`image-import-smoke` dep-skew guard; deployment-api's
  `vendor-deps`/`deploy`/`redeploy-monitor-jobs`; a `fetch-tags`/`operability-probe` pair now on most service repos).
  Only `deployment-ui`, `e2e-testing`, `system-integration-tests`, `unified-trading-system-ui` render clean. The new
  guard means `rollout-cloudbuild.py --apply` would now correctly REFUSE all 15 instead of silently overwriting them —
  the disaster this issue exists to prevent is now structurally blocked — but it also means the P1 drift-checker todo
  above is more urgent than when it was filed: at this scale a human diffing repo-by-repo before every template touch
  doesn't scale, and the P3 (other templates) is still entirely unmeasured. Not fixing the drift itself here — out of
  this todo's scope (it only had to make the tool incapable of regressing a repo, which it now is).
- **2026-07-28 (slot-13, infra)** — Shipped `check_cloudbuild_template_drift.py`, closing P1 + P3. Per-template
  measurement (consumers carrying content their mapped template does not / total consumers mapped to that template —
  matches the earlier 15/19 fleet-wide figure exactly):

  | Template                           | Drifted / Total | Notes                                                                                                                         |
  | ---------------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------- |
  | `cloudbuild-service-template.yaml` | 12 / 12         | Every service consumer carries content the template lacks.                                                                    |
  | `cloudbuild-api-template.yaml`     | 2 / 2           | `client-reporting-api` (5), `deployment-api` (26 — `deploy`/`vendor-deps`/`redeploy-monitor-jobs`/`operability-probe` steps). |
  | `cloudbuild-infra-template.yaml`   | 1 / 1           | `ibkr-gateway-infra` (4) — `fetch-tags` guard the infra template never learned.                                               |
  | `cloudbuild-sit-template.yaml`     | 0 / 2           | `e2e-testing`, `system-integration-tests` render CLEAN.                                                                       |
  | `cloudbuild-ui-template.yaml`      | 0 / 2           | `deployment-ui`, `unified-trading-system-ui` render CLEAN.                                                                    |

  All 15 drifted repos' counts are seeded into `cloudbuild_template_drift_baseline.yaml` (shrinking ratchet — never
  fixed here, intentionally baselined per the todo's own instruction). The checker fails the moment a repo's drift count
  grows PAST its seeded baseline (a template falling further behind), verified against a synthetic template-lags-repo
  case in the unit tests. Standalone only — wiring into `quality-gates.sh` stays in the finalize plan per this doc's P1.
