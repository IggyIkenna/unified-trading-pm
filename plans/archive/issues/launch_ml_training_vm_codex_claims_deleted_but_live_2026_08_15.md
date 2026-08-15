---
doc_type: issue
title: codex says launch-ml-training-vm.sh was deleted/consolidated into launch-ml-vm.sh — both scripts are live on disk
summary: >-
  Surfaced while archiving ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md (its
  todo 1 fixed launch-ml-training-vm.sh's dead module path, deployment-service@082a5eda, 2026-08-09).
  /codex/04-architecture/ml-service-architecture.md and /codex/05-infrastructure/vm-tarball-deployment.md both state
  launch-ml-training-vm.sh was deleted 2026-05-20 as part of the ml_repo_consolidation, superseded by launch-ml-vm.sh.
  It was not deleted — it is live on disk, actively maintained (fixed 4 days ago), and still documented as a live
  launcher in /codex/05-infrastructure/vm-launcher-runbook.md and /codex/05-infrastructure/launcher-script-ssot.md. Both
  launch-ml-training-vm.sh and launch-ml-vm.sh exist side by side; which one is authoritative is unresolved.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [codex-drift, ssot-contradiction, ml-service, vm-launcher]
related:
  [
    /codex/04-architecture/ml-service-architecture.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
    /plans/archive/2026_08/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
  ]
created: 2026-08-15
author: slot-8 backend_engineer
last_updated: 2026-08-15
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: unknown
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/ml-service-architecture.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    deployment-service/scripts/vm/launch-ml-training-vm.sh,
    deployment-service/scripts/vm/launch-ml-vm.sh,
  ]
supersedes:
superseded_by:
resolved_by: unified-trading-pm (this commit — self-contained codex doc fix, no code repo touched)
source: >-
  Found while running the 6-step archival ritual for
  ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md (2026-08-15), whose own todo 1
  fixed launch-ml-training-vm.sh's dead ml_training_service module path 2026-08-09 — a real fix on a script codex claims
  doesn't exist.
---

# codex says `launch-ml-training-vm.sh` was deleted — both it and `launch-ml-vm.sh` are live

> **Status (2026-08-15)**: ✅ RESOLVED. `launch-ml-training-vm.sh` confirmed LIVE (fired by deployment-api's
> `POST /api/ml/experiment/launch` route). Both codex docs fixed at `unified-trading-pm` (this commit).

## What I found

`/codex/04-architecture/ml-service-architecture.md` § "Launcher + Cloud Build" states: "ONE launcher: `launch-ml-vm.sh`
parameterised by `--operation` + `--asset-group`. Predecessors (`launch-ml-training-vm.sh`, `launch-ml-inference-vm.sh`)
deleted." `/codex/05-infrastructure/vm-tarball-deployment.md` similarly describes `launch-ml-vm.sh` as "consolidated
from `launch-ml-training-vm.sh` per `ml_repo_consolidation_2026_05_19`," dated 2026-05-20.

Live-verified on `origin/live-defi-rollout` (deployment-service, this session): both
`scripts/vm/launch-ml-training-vm.sh` AND `scripts/vm/launch-ml-vm.sh` exist on disk side by side.
`launch-ml-training-vm.sh` is not a stale leftover — it was actively fixed 2026-08-09 (`deployment-service@082a5eda`,
"repoint launch-ml-training-vm.sh at real ml_service.training module") as part of
`ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`'s todo 1, and it is still
documented as a live launcher in both `/codex/05-infrastructure/vm-launcher-runbook.md` §9 and
`/codex/05-infrastructure/launcher-script-ssot.md`'s prefix registry (`ml-train-` → `launch-ml-training-vm.sh`).

## Why it matters

Two codex docs (ml-service-architecture.md, vm-tarball-deployment.md) disagree with two others (vm-launcher-runbook.md,
launcher-script-ssot.md) about whether this script exists at all — and neither pair matches the actual repo state (it
exists AND was recently, deliberately fixed, not left over by accident). This is exactly the kind of doc/comment/pointer
that "MISLED you is a finding" — an agent trusting ml-service-architecture.md's "deleted" claim would not have looked
for (or fixed) the real bug the archived doc's todo 1 fixed. Whether `launch-ml-vm.sh` was actually supposed to have
made `launch-ml-training-vm.sh` unnecessary (and it's now genuinely dead code that should be deleted per the 2026-05-19
consolidation plan) or whether the consolidation was never fully executed for this launcher and both scripts now serve
live, distinct purposes is not established by this finding alone — it needs a real diff of what each script's
callers/VM_TASK dispatch actually invoke today, which is out of scope for the P3 mechanical archival pass that surfaced
it.

## Recommended decision

Determine whether `launch-ml-training-vm.sh` is genuinely superseded by `launch-ml-vm.sh` today (in which case delete
it + fix the 2 codex docs that still describe it as live) or whether it serves a purpose `launch-ml-vm.sh` doesn't cover
(in which case fix the 2 codex docs that claim it was deleted). Either way, reconcile all 4 codex docs to agree.

## Todos

- [x] ✅ [DOC] P3. Determine whether `launch-ml-training-vm.sh` is dead code (never invoked, fully superseded by
      `launch-ml-vm.sh`) or still live/callable (check `deployment-api`'s launch-trigger routes, `launcher_registry.py`
      self-heal keys, and `VM_PREFIX_TO_BUCKET` for `ml-train-`). If dead: delete the script + its `ml-train-` registry
      entries, and fix `/codex/05-infrastructure/vm-launcher-runbook.md` §9 +
      `/codex/05-infrastructure/launcher-script-ssot.md` to drop it. If live: fix
      `/codex/04-architecture/ml-service-architecture.md` § "Launcher + Cloud Build" and
      `/codex/05-infrastructure/vm-tarball-deployment.md` § "ML launcher" to stop claiming it was deleted, and state
      what each of the two launchers is actually for. Repo: deployment-service, unified-trading-pm. — unified-trading-pm (this commit)
      **Verdict: LIVE.** `launch-ml-training-vm.sh` is the exact launcher `deployment-api`'s
      `POST /api/ml/experiment/launch` route fires (`ml_experiment_launch.py`, `_LAUNCHER_FILENAME`) — confirmed via
      grep, not just doc claim. `launch-ml-vm.sh` has no programmatic caller found (manual/CLI use only). Neither is
      registered in `VM_PREFIX_TO_BUCKET` under `ml-train-` specifically — only `ml-` (from `launch-ml-vm.sh`) is
      registered; `ml-train-` VM names prefix-match against it. `vm-launcher-runbook.md` and `launcher-script-ssot.md`
      already correctly listed `launch-ml-training-vm.sh` as live (no fix needed there — this issue's "both pairs
      disagree" framing meant the OTHER pair, `ml-service-architecture.md` + `vm-tarball-deployment.md`, was wrong).
      Fixed both: `/codex/04-architecture/ml-service-architecture.md` § "Launcher + Cloud Build" + its Migration
      history 2026-05-20 bullet, and `/codex/05-infrastructure/vm-tarball-deployment.md` § "ML launcher".

## Progress Log

- 2026-08-15 (slot-18): Resolved. Both codex docs now state both launchers are live and what each is for; issue
  closed (no further work — the two launchers staying distinct rather than being merged is a separate, un-filed
  follow-up decision, not required by this P3 doc-drift finding).
