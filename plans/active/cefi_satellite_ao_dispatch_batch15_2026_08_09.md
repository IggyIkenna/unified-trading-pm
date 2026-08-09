---
doc_type: plan
title: CeFi satellite AO batch 15 — item-level extraction (infrastructure_master group, stale launcher module paths)
summary: >-
  Fifteenth AO-dispatch batch for cefi, drafted from the round-11 RECLASSIFY + satellite-extraction sweep (cefi +
  prediction tranches, 2026-08-09). Both items are pulled verbatim from
  `issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`, which self-labelled its
  own 2 todos as gated on "the same A/B/C decision already pending for S1-a" in the sibling doc
  `issues/mdps_features_deadcode_consolidation_2026_07_20.md`. That gate is now cleared: the
  round5-cefi-question-resolution (2026-08-08) declassified S1-a/S1-b/S1-c from `[OPERATOR]` per `task_template.md`
  finding U's positive test (neither a business/spend judgment, a credential gate, nor a whole-bucket destroy/failed
  reversibility check — ordinary dead-code cleanup + registry hygiene), and
  `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` (drafted today) already extracted S1-a itself while explicitly
  flagging that this doc's own cross-reference to "the same A/B/C decision" is stale (predates the declassification) and
  its 2 items target 2 DIFFERENT launchers, out of batch12's own single-file scope — "flagging for whoever next touches
  that doc." This batch is that follow-through.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-15, satellite-docs, item-level-extraction, na-audit, dead-code, vm-launcher]
related:
  [
    /plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/cefi_satellite_ao_dispatch_batch12_2026_08_09.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: high
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Round-11 RECLASSIFY + satellite-extraction sweep (cefi + prediction tranches, 2026-08-09) — a targeted re-check of
  docs that already carry a KEEP-NA marker written by a staleness-only check, never re-assessed against the full set of
  precedents accumulated since (D16, S5.1 tiering, escalation-N, reversibility-qualified deletes, Option B retirement,
  and — decisive here — the round5-cefi-question-resolution declassification of the S1-a/b/c launcher keep/delete
  question).
context_scope:
  [
    /plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    deployment-service/scripts/vm/launch-ml-training-vm.sh,
    deployment-service/scripts/vm/launch-prediction-pipeline-vm.sh,
    deployment-service/scripts/vm/launch-features-vm.sh,
  ]
---

# CeFi satellite AO batch 15 — item-level extraction (infrastructure_master group)

> **Status: ACTIVE.** Conflict-checked 2026-08-09 — grepped `plans/active/*.md` + `plans/active/issues/*.md` for
> `launch-ml-training-vm.sh` and `launch-prediction-pipeline-vm.sh`: the only hits are this batch's own source doc
> (`ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`) and
> `vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md` (a wholly different finding — Class-B stall-kill-timeout gap,
> not the stale-module-path defect this batch fixes; no todo there targets either file). No active
> `assigned_vm: planning` plan under any `parent_epic` claims either launcher for this defect class. **Cross-todo
> file-collision check**: todo 1 edits `launch-ml-training-vm.sh` (+ possibly `setup-data-pipeline-vm.sh` if the Phase-B
> branch path is chosen); todo 2 edits `launch-prediction-pipeline-vm.sh`. No file overlap between the two todos
> themselves.

## Todos

- [x] ✅ [SCRIPT] P2. **Fix `launch-ml-training-vm.sh`'s dead `ml_training_service` module path.** —
      deployment-service@082a5eda. Repointed `ML_CMD` to `python -m ml_service.training` (verified importable via
      `uv run python -c "import ml_service.training"`), set `VM_SERVICE=ml_service` in the assembled metadata, removed
      the dead `ml_training_service` value + stale Phase-B-pending comments. `--dry-run` confirms the assembled command;
      `quality-gates.sh` green. Verify `ml-service`'s actual training CLI surface (`ml-service/ml_service/training/` +
      its `cli`/entrypoint) against `launch-ml-training-vm.sh`'s assembled
      `--operation/--instruments/--target-types/--timeframes/--start-date/--end-date` args; either rewrite the launcher
      to call the real entrypoint directly (`python -m ml_service.training ...` or whatever it turns out to be) or build
      the `setup-data-pipeline-vm.sh` `VM_TASK=ml-training` Phase B branch the script's own header comments already
      describe as the intended fix — then set `VM_SERVICE=ml_service` and delete the dead `ml_training_service` metadata
      value + its stale `SERVICE_TARBALLS` remnants. Repo: deployment-service. Source:
      `issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` todo 1 (verbatim).
      **Done when**: `launch-ml-training-vm.sh` invokes a real, importable module (confirmed via
      `python -c "import <module>"` against the actual `ml-service` package, not just a launcher-script edit), no
      `ModuleNotFoundError` on a live/test invocation, and `quality-gates.sh` is green on both touched repos.
- [ ] [SCRIPT] P2. **Fix `launch-prediction-pipeline-vm.sh`'s dead pre-consolidation feature-service import paths.**
      Determine whether `launch-features-vm.sh --feature-family cross_instrument|delta_one --asset-group PREDICTION`
      (the consolidated launcher, already the correct target for the sibling S1-a defect per the
      round5-cefi-question-resolution declassification) covers this launcher's own 3-step
      MDPS→cross_instrument→delta_one chunked sequencing; if yes, fold this launcher into the same keep/delete decision
      already applied to S1-a (delete + repoint any registry/self-heal binding) — this is ordinary dead-code cleanup per
      the same declassification, not a fresh operator question; if no (the chunking has no consolidated equivalent), fix
      the embedded
      `python3 -c "from features_cross_instrument_service.cli.main import main; ...; from features_delta_one_service.cli.main import main; ..."`
      import-verify step in place to use `features_service.cross_instrument` / `features_service.delta_one` (the real
      post-consolidation subpackage paths). Repo: deployment-service. Source:
      `issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` todo 2 (verbatim).
      **Done when**: `launch-prediction-pipeline-vm.sh` either no longer exists (folded into `launch-features-vm.sh`,
      with every referrer/registry entry repointed) or its embedded import-verify step succeeds against a real
      `python -c` check of the actual `features-service` package, and `quality-gates.sh` is green.

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md` — launcher registry + dead-code conventions.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol.

## Progress Log

- **2026-08-09** — drafted via the round-11 RECLASSIFY + satellite-extraction sweep (cefi + prediction tranches). Both
  items were sitting `assigned_vm: NA` in
  `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` under a self-cited gate ("fold
  into the same A/B/C decision already open for S1-a") that `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` (drafted
  the same day, extracting the S1-a item itself) already flagged as stale — the underlying A/B/C question was
  declassified 2026-08-08 (round5-cefi-question-resolution), and batch12 explicitly named this doc's 2 items as "out of
  this todo's stated single-file scope" and "flagging for whoever next touches that doc." This batch is that
  follow-through: extracted both items verbatim, conflict-checked clean (no other active plan claims either launcher for
  this defect), `status: active` (not draft — the gating question is resolved, nothing left to hold this batch back).
