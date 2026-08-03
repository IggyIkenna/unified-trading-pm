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
    /plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
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
context_scope: [scripts/propagation/rollout-cloudbuild.py, configs/cloudbuild-service-template.yaml, scripts/quality_gates/check_cloudbuild_template_drift.py, /plans/archive/issues/cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md, /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md, /codex/08-workflows/ci-cd-flow.md, /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md]
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
- [ ] [DEVOPS] P2. **Roll the empty-tag guard out to the 19 consumer repos — RE-SCOPED 2026-08-02 per operator ruling
      into two explicit, ordered steps.** The original one-line wording ("roll the guard out once the drift check
      exists") assumed a clean `rollout-cloudbuild.py --apply` sweep. That mechanism no longer exists: the
      would-drop-content guard shipped 2026-07-28 (`unified-trading-pm@ddf0b89f4`) now correctly REFUSES 15 of the 19
      consumers, so an `--apply` sweep would simply decline most of the fleet. Do the steps in order — step 2 is not
      startable for a repo until step 1 has cleared that repo.
  1. **Resolve the per-repo drift first.** Ground truth is
     `scripts/quality_gates/cloudbuild_template_drift_baseline.yaml` (seeded 2026-07-28): **15 of 19 consumers carry
     content their mapped template does not** — `deployment-api` (26), `strategy-service` (13), `features-service` (12),
     `alerting-service` (10), `execution-service` (10), `greeks-service` (10), `batch-live-reconciliation-service` (9),
     `ml-service` (9), `trading-agent-service` (9), `market-tick-data-service` (8), `instruments-service` (7),
     `fund-administration-service` (6), `market-data-processing-service` (6), `client-reporting-api` (5),
     `ibkr-gateway-infra` (4). The 4 clean ones are `deployment-ui`, `e2e-testing`, `system-integration-tests`,
     `unified-trading-system-ui`. **Re-measure before trusting those numbers**
     (`check_cloudbuild_template_drift.py --show`) — the baseline is a snapshot, not a live read. For each drifted repo,
     classify every reported marker into exactly one bucket and act on it: (a) **forward-portable** — belongs in
     `configs/cloudbuild-*-template.yaml`, port it so the render stops dropping it; (b) **intentional permanent per-repo
     divergence** (deployment-api's `vendor-deps`/`deploy`/`redeploy-monitor-jobs` steps are the archetype the baseline
     comment already names) — leave it in the repo and record WHY in the baseline comment; (c) **stale repo-local
     content** — delete it from the repo. Ratchet the baseline DOWN for every marker resolved under (a) or (c); never
     raise a count.
  2. **Then apply the guard.** For every repo whose step-1 classification leaves it renderable, land the fail-fast
     empty-tag guard (`SHORT_SHA` → `VERSION` fallback, hard-failing with a diagnostic only when both are genuinely
     unresolvable — the guard already lives in `configs/cloudbuild-service-template.yaml`). For a category-(b) repo
     where a full render is deliberately not wanted, hand-apply just the guard hunk instead of running the rollout tool
     against it. Each repo needs its own `quality-gates.sh` + its own quickmerge. Prove at least ONE repo end-to-end: a
     manual `gcloud builds submit` (storageSource, so `SHORT_SHA` is empty) must recover via the `VERSION` fallback
     instead of dying with `invalid reference format` / exit 125 — cite the build id.

  Still not urgent in the original sense (the per-repo copies already carry the important fixes, and the guard only
  changes behaviour for manual `gcloud builds submit`), but step 1 is now the real work and it is worth doing on its own
  merits: 15 repos silently diverging from their template is the exact condition this issue exists to prevent recurring.
  The AO-dispatchable copy of this todo lives in `/plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md` (todo 1)
  — this doc stays `assigned_vm: NA`; flip this checkbox from there.

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

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).

- **2026-08-02 (operator ruling executed)** — The sole open `[DEVOPS] P2` todo was RE-SCOPED into two explicit ordered
  steps (resolve the per-repo drift, then apply the guard), per an operator ruling naming exactly that split. This is
  the re-scope the 2026-07-30 na-eligibility-audit verdict below asked for ("Re-scope the todo to name the mechanism and
  it becomes a clean RECLASSIFY") — the mechanism is now named, so the todo is bounded and worker-determinable. **This
  doc deliberately stays `assigned_vm: NA`**: rather than flipping this issue doc's own dispatch target, the bounded
  work was extracted into `/plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1 (the standard
  `/ag-closeout-audit` extraction pattern — source doc stays NA, the batch plan carries the dispatchable copy). No code
  shipped in this change; the 15/19 drift figures quoted in the re-scoped todo were re-verified against
  `scripts/quality_gates/cloudbuild_template_drift_baseline.yaml` at the time of writing (19 consumers listed, 15 with a
  non-zero count) and the batch-5 todo instructs its worker to re-measure live before acting on them.
- **context-scout 2026-08-03**: populated/refreshed context_scope (7 entries).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — closest-to-eligible candidate in this
tranche, held back on a genuine scope ambiguity rather than a conflict. The sole open todo ("roll the empty-tag guard
out to the 19 consumer repos once the drift check exists") has had its gate met (the drift checker shipped 2026-07-28)
and is unclaimed by either ci batch. But this doc's OWN 2026-07-28 Progress Log entry measured that **15 of 19 consumers
now carry content the SERVICE template does not**, and the would-drop-content guard shipped the same day means
`rollout-cloudbuild.py --apply` now correctly REFUSES all 15 — so the rollout mechanism the todo implies no longer
works, and its replacement (hand-apply per repo vs. resolve the drift first) is undecided. Not determinable by a worker
alone as currently written. **Re-scope the todo to name the mechanism and it becomes a clean RECLASSIFY.**

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **KEEP-NA, valid — the 2026-07-30 verdict's own
condition was met, and it resolved AWAY from a reclassification, not toward one.** The re-scope that verdict asked for
landed the same day (the operator-ruled two-ordered-step rewrite recorded in this doc's Progress Log), but the bounded
work was extracted into `/plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1 rather than by flipping
this doc's own `assigned_vm`. Verified live: that batch plan exists, carries `assigned_vm: planning`, and its todo 1 is
the re-scoped guard rollout. This doc's sole open checkbox already cites the extraction in its own text ("The
AO-dispatchable copy of this todo lives in … — this doc stays `assigned_vm: NA`; flip this checkbox from there"), so the
citation is correct and no hygiene fix is needed. Flipping `assigned_vm` here now would open a SECOND dispatch path to
the identical fleet-wide rollout — Phase-1 citation class (a), a body sentence redirecting work to a different doc.
