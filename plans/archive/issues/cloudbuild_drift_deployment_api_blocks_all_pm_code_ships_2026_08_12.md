---
doc_type: issue
title: deployment-api cloudbuild drift (19 > baseline 16) fails PM quality-gates, blocking every PM CODE ship fleet-wide
summary: >-
  Two steps (vendor-deps, verify-auth-contract) exist in deployment-api/cloudbuild.yaml but not in its mapped template
  configs/cloudbuild-api-template.yaml, putting the drift ratchet at 19 markers against a baseline of 16. The ratchet is
  a PM post-gate, so quality-gates.sh exits 1 for anyone in unified-trading-pm — which means no PM code can be shipped
  via quickmerge (no .qg_last_passed_sha sentinel is written) regardless of what they changed. Doc ships are unaffected
  (safe-doc-push runs prek, not the full gate). Both steps are guarded with `if _SERVICE_NAME != deployment-api then
  skip`, which is the tell that they were AUTHORED FOR THE SHARED TEMPLATE and landed in the consumer by mistake — a
  per-repo file that only ever runs for one service does not need a service-name guard. So the correct fix is
  forward-porting, NOT re-baselining.
status: superseded
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-api, client-reporting-api]
scope: [engineer]
tags: [ci-cd, cloudbuild, quality-gates, drift-ratchet, ship-blocker]
related:
  [
    /plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
    /plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops_engineer
drift_direction: advance-code
resolved_by: deployment-api@b928d173b5
locked_by:
locked_since:
supersedes:
superseded_by: cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12
source: >-
  Hit 2026-08-12 while trying to ship the codex-doc-freshness warn-with-digest change. Blocked two separate ship
  attempts on two different days with no content overlap between them.
depends_on: []
context_scope:
  [
    unified-trading-pm/scripts/quality_gates/check_cloudbuild_template_drift.py,
    unified-trading-pm/configs/cloudbuild-api-template.yaml,
    deployment-api/cloudbuild.yaml,
  ]
---

# deployment-api cloudbuild drift blocks every PM code ship

> **⚠️ SUPERSEDED 2026-08-12 — do not action the todos below.** This is one of THREE issue docs filed the same day for
> the same incident (`deployment-api@4c31b72`, drift `19 > 16`). SSOT is
> `/plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`; the incident was resolved by
> `deployment-api@b928d173b5`.
>
> **Your central argument was half-right, and the SSOT records both halves.** You argued the `_SERVICE_NAME` guard
> proves these steps were authored for the shared template, so the fix is forward-porting and NOT `--update-baseline`.
> That is correct about INTENT. It is not achievable for `verify-auth-contract`, which needs `waitFor: ["deploy"]` and
> `deploy` is per-repo-only content absent from the template — so a template-native version would race the deploy it
> exists to verify. Authored for the template, not expressible in it; hence the revert. Your `[DEVOPS] P1` is closed by
> that revert, and your `[SCRIPT] P2` (stale SSOT pointer) shipped in `unified-trading-pm@2b4bee96d3`.
>
> **Two corrections.** (1) `vendor-deps` was never new — it is pre-existing intentional drift named in the baseline
> file's own header, and it showed up in the failure output only because that output is a positional slice, not a real
> diff. The two-step table below overstates the incident by one step. (2) Still-live and carried forward to the SSOT:
> the `_RUN_INIMAGE_QG` template/consumer divergence, and "make a foreign post-gate failure legible at the point of
> blocking".

## Impact — this is not a deployment-api problem, it is a fleet ship-blocker

The drift ratchet is a **post-gate inside unified-trading-pm's `quality-gates.sh`**. When it fails, the gate exits 1 and
never writes `.qg_last_passed_sha`. `quickmerge.sh` verifies that sentinel equals HEAD before it will commit. So:

- **Nobody can ship PM CODE** — the failure is in another repo's build file and has nothing to do with the change in
  hand. Measured: it blocked a bats-hermeticity change and a codex-freshness change on separate days.
- **Doc ships still work** — `safe-doc-push.sh` runs prek, not the full gate. This is why the blockage is easy to miss:
  the doc traffic keeps flowing while code traffic is dead.

## Measurement (2026-08-12)

`check_cloudbuild_template_drift.py`: `deployment-api (cloudbuild-api-template.yaml): 19 drift marker(s) > baseline 16`.
**15 of the other 16 consumers sit exactly at baseline**, so this is one genuinely new drift, not ambient decay.

The three over-baseline markers come from two steps present in `deployment-api/cloudbuild.yaml` and **absent from the
template entirely** (`grep -c` in the template returns 0 for both):

| step                   | consumer line | in template? |
| ---------------------- | ------------- | ------------ |
| `vendor-deps`          | 79            | ❌ absent    |
| `verify-auth-contract` | 543           | ❌ absent    |

## Why the fix is forward-port, NOT `--update-baseline`

The checker offers re-baselining for "intentional per-repo customization". **This does not qualify**, and the evidence
is in the steps themselves — both open with a service-name guard:

```bash
if [ "${_SERVICE_NAME}" != "deployment-api" ]; then
  echo "vendor-deps: ${_SERVICE_NAME} has no vendored sibling deps — skipping"
```

A file that only ever runs for `deployment-api` has no reason to check whether it is `deployment-api`. That guard only
makes sense in a **shared template** evaluated by several services. These steps were written for the template and landed
in the consumer instead — precisely the hand-edit-the-generated-copy failure the workspace bans for `.github/**`
workflows, and precisely what this ratchet exists to catch. Re-baselining would bless it and delete the signal.

## What makes this NOT a 30-minute mechanical fix (why it is being handed off, not guessed at)

Forward-porting is more than pasting two steps:

1. **The template has no `_DEPLOY` substitution.** `verify-auth-contract` guards on `[ "${_DEPLOY}" != "true" ]`, but
   the template's `substitutions:` block defines `_SERVICE_NAME`, `_REGISTRY_REPO`, `_BRANCH`, `_RUN_INIMAGE_QG` — and
   no `_DEPLOY`. The consumer defines `_DEPLOY: "false"`. Adding the step without the substitution changes what
   `client-reporting-api` (the template's other consumer) resolves at build time.
2. **`waitFor` placement decides what the next rollout regenerates.** `rollout-cloudbuild.py --apply` regenerates each
   consumer FROM the template. If the forward-ported steps sit at different positions or carry different `waitFor` edges
   than deployment-api's current file, the next rollout silently reorders deployment-api's build graph (`vendor-deps`
   currently has `waitFor: ["-"]`, and `build` depends on it via
   `waitFor: ["pull-base-image", "ensure-repo", "fetch-ui", "vendor-deps"]`).
3. **`_RUN_INIMAGE_QG` already diverges** between template (`"false"`) and consumer (`"true"`), with opposite rationales
   written in each file's comments. Whoever does this should decide that too rather than leave a second latent drift.

Getting 1–3 wrong breaks deployment-api's deploys, so it needs someone who owns that build — not a passer-by unblocking
themselves.

## Todos

- [ ] [DEVOPS] P1. **Forward-port `vendor-deps` + `verify-auth-contract` into
      `unified-trading-pm/configs/cloudbuild-api-template.yaml`**, including a `_DEPLOY` substitution, at positions and
      with `waitFor` edges that make `rollout-cloudbuild.py --apply` regenerate deployment-api's current build graph
      byte-for-byte. Done-when: `check_cloudbuild_template_drift.py` reports deployment-api at or below 16 **and** a
      `--dry-run` rollout shows no change to deployment-api/cloudbuild.yaml.
- [ ] [DEVOPS] P2. Reconcile `_RUN_INIMAGE_QG` (template `"false"` vs consumer `"true"`, each with a contradictory
      justification comment) — decide which is right and make the other follow, rather than leaving a latent drift the
      ratchet has already absorbed.
- [ ] [SCRIPT] P2. **Fix the checker's stale SSOT pointer.** `check_cloudbuild_template_drift.py`'s remedy text cites
      `plans/active/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md`, which is
      ARCHIVED (`plans/archive/issues/…`). It sent me to a path that does not exist while diagnosing a live blocker.
      Point it at the archive path, or at this doc. (Blocked on todo 1 only because the checker lives in PM and PM code
      cannot ship until the drift clears — which is itself the point.)
- [ ] [SCRIPT] P3. **Make a foreign post-gate failure legible at the point of blocking.** The gate reports
      `cloudbuild-template-drift` with no indication that the offending content is in a DIFFERENT repo and unrelated to
      the change being shipped. A line naming the owning repo would have saved two separate diagnoses on two days.

## Progress Log

- 2026-08-12 — Filed while blocked shipping the codex-freshness warn-with-digest change. Diagnosed rather than routed
  around: declined `--update-baseline` because the service-name guards prove the steps belong in the template, and
  declined a blind forward-port because the missing `_DEPLOY` substitution plus `waitFor` placement decide what the next
  rollout does to deployment-api's build graph. Also resolved (separately) a conflict-markers failure in the same gate
  run — a peer's `tradfi_canonical_path_migration_design_2026_07_19.md` left with markers after a `pull.autostash`
  collision; both sides were byte-identical after whitespace normalisation, so resolution was lossless.
