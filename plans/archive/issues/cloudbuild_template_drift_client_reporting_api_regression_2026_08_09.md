---
doc_type: issue
title:
  cloudbuild-api-template.yaml drift regression — client-reporting-api now 4 markers > baseline 3, blocking quickmerge
  fleet-wide
summary: >-
  scripts/quality_gates/check_cloudbuild_template_drift.py (a hard post-gate in quality-gates.sh, blocking on every
  unified-trading-pm commit regardless of that commit's own diff) started failing on client-reporting-api's
  cloudbuild.yaml carrying content its mapped template (cloudbuild-api-template.yaml) does not — measured 4 drift
  marker(s) vs baseline 3 (cloudbuild_template_drift_baseline.yaml). The new marker is a dropped step arg:
  `quality-gates::set -e` / a `docker run --rm --entrypoint "" -e CLOUD_BUILD=true -e CLOUD_MOCK_MODE=true ...` block.
  client-reporting-api's local clone is confirmed at the same commit as origin/live-defi-rollout (not a stale-clone
  false positive) — this is a genuine, currently-standing regression, not a transient race. Blocked an unrelated
  unified-trading-pm commit (plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md's own P2
  structural-fix dispatch) from shipping via quickmerge's re-gate step — same class of "corpus-wide ambient check
  attributes someone else's drift to whoever happens to be pushing" problem that issue documents, just for a check
  outside run_hygiene_sweep.sh's scope (this one's a quality-gates.sh post-gate, checked against sibling-repo clones on
  disk, not the plans corpus).
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, client-reporting-api]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, template-drift, ratchet, quickmerge-blocker]
related:
  [
    /plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
    /plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md,
  ]
created: 2026-08-09
author: backend_engineer (slot 7)
source: >-
  Discovered live 2026-08-09 while shipping the plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity P2
  structural-fix dispatch — quickmerge's re-gate step failed on this unrelated regression.
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: client-reporting-api@9b28914 (slot-17) + unified-trading-pm@51808a4a6e (slot-17), see Progress Log
last_updated: 2026-08-09
locked_since:
---

> **🟢 ARCHIVED 2026-08-09 — RESOLVED.** The single todo is done: `client-reporting-api@9b28914` +
> `unified-trading-pm@51808a4a6e` (both slot-17) forward-ported the `_RUN_INIMAGE_QG` guard into both the template and
> the repo's own `cloudbuild.yaml`, landing before this dispatch reached the todo. Answer to the "Recommended decision"
> below was (a) — universal, forward-ported into the template — not (b) a baseline re-ratchet. Verified live:
> `check_cloudbuild_template_drift.py` reports `client-reporting-api (cloudbuild-api-template.yaml): 3 (== baseline)`. 0
> open todos, unlocked.

# cloudbuild-api-template.yaml drift regression — client-reporting-api

## What was found

`check_cloudbuild_template_drift.py` (hard post-gate, `quality-gates.sh`) failed on `client-reporting-api`'s
`cloudbuild.yaml` carrying content `cloudbuild-api-template.yaml` does not:

```
[FAIL] client-reporting-api (cloudbuild-api-template.yaml): 4 drift marker(s) > baseline 3. New/over-baseline marker(s): step arg dropped: quality-gates::set -e
docker run --rm \
  --entrypoint "" \
  -e CLOUD_BUILD=true \
  -e CLOUD_MOCK_MODE=true \
  -e GCP_PROJECT_ID=$PROJECT_ID \
  asia-nort...
```

Confirmed genuine (not a stale-clone false positive): `client-reporting-api`'s local sibling clone in this slot is at
`b75b798d952011429eb4875dee01f7c88ad2b410`, identical to `origin/live-defi-rollout`'s tip for that repo at check time.

## Why it matters

This check is a **hard, blocking post-gate inside `quality-gates.sh`**, which every `unified-trading-pm` commit runs
(via Pass-1 QG and quickmerge's re-gate) regardless of whether that commit touches `client-reporting-api` or any Cloud
Build config at all — it scans EVERY sibling repo's `cloudbuild.yaml` against its mapped template on every run. A
regression here blocks the entire fleet's `unified-trading-pm` commits, not just work in the affected repo — the exact
"ambient corpus-wide state blocks an unrelated commit" shape
`plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` is about, just for a check outside that
doc's `run_hygiene_sweep.sh` scope.

## Recommended decision

Either (a) forward-port the dropped `quality-gates` mock-mode docker-run step into
`configs/cloudbuild-api-template.yaml` if it's meant to be universal, or (b) if it's genuinely
`client-reporting-api`-specific customization, re-baseline via
`python3 scripts/quality_gates/check_cloudbuild_template_drift.py --update-baseline` after confirming (a) is not the
right call — needs someone with `client-reporting-api` Cloud Build context to judge which, so filing rather than
guessing.

## Todos

- [x] ✅ [DEVOPS] P2. Diagnose the dropped `quality-gates::set -e` / `CLOUD_MOCK_MODE=true` docker-run step in
      `client-reporting-api/cloudbuild.yaml` vs `configs/cloudbuild-api-template.yaml` — forward-port into the template
      if universal, or `--update-baseline` if genuinely repo-specific (with a Progress Log reason). Repo:
      unified-trading-pm (`scripts/quality_gates/check_cloudbuild_template_drift.py`,
      `configs/cloudbuild-api-template.yaml`), client-reporting-api (`cloudbuild.yaml`). —
      unified-trading-pm@51808a4a6e + client-reporting-api@9b28914 (slot-17), see Progress Log.

## Progress log

- 2026-08-09 (backend_engineer, slot 7): Found while shipping an unrelated fix (quickmerge's re-gate step blocked on
  this). Declared a `qg_red` repo-blocker for `unified-trading-pm` per RULES.md § 4b rather than chasing a fix myself
  (outside this dispatch's craft/scope — needs Cloud Build domain judgment on template-vs-repo intent). Filed here so
  the fix is tracked, not just observed.
- 2026-08-09 (devops worker, slot 13, dispatched to the [DEVOPS] P2 todo): decision was already made and shipped by
  slot-17 before this dispatch landed — answer was (a), universal: `unified-trading-pm@51808a4a6e` forward-ported the
  `_RUN_INIMAGE_QG` guard into `configs/cloudbuild-api-template.yaml`'s `quality-gates` step, and
  `client-reporting-api@9b28914` forward-ported the same guard into its own `cloudbuild.yaml` (superseding an
  intermediate `client-reporting-api@b75b798` revert of an earlier accidental drift of the same guard). Both commits
  confirmed on `origin/live-defi-rollout` via `git merge-base --is-ancestor` from this slot's fresh-pulled clones.
  Re-ran `python3 scripts/quality_gates/check_cloudbuild_template_drift.py` live:
  `client-reporting-api (cloudbuild-api-template.yaml): 3 (== baseline)` — `[OK]`, drift cleared, no baseline re-ratchet
  needed (was option (a), not (b)). No further code change required; closing this todo and archiving per the 6-step
  ritual (0 open todos, unlocked).
