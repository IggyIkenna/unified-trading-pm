---
doc_type: plan
title:
  UI satellite AO batch 3 — observability_master bounded meta/doc items extracted from artifact_pipeline_observability,
  round11 2026-08-09 sweep
summary: >-
  Third AO-dispatch batch for the ui tranche, produced by the round11 2026-08-09 RECLASSIFY + satellite-extraction
  sweep. Pulls 3 pure meta/doc/investigation items out of `artifact_pipeline_observability_2026_07_17.md`
  (`observability_master`) — the SAME kind of item `ui_satellite_ao_dispatch_batch1_2026_08_06.md` already validated as
  safe to extract from this exact doc (it pulled 2 meta/doc-only items, both since shipped, while explicitly declining
  every implementation-shaped item as collision risk against the doc's dense, live, operator-reviewed in-flight build).
  This batch follows that same established distinction: (1) file the tarball-bucket-resolution issue doc, (2) check +
  report AR/ECR native vulnerability-scan status, (3) correct a misattributed VM origin in a sibling issue doc. All 3
  are read/report/file actions, not changes to the live artifact-pipeline build — none touch the 7 implementation-shaped
  items (snapshot worker, CloudBuildsTab retirement, tarball-lane display, fleet-wide SHA-pinning, "built but never
  deployed" latency, deploy-churn signal) that stay explicitly deferred per batch 1's precedent.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer]
tags:
  [
    ui,
    ao-dispatch,
    close-out,
    batch-3,
    satellite-docs,
    observability-master,
    artifact-pipeline,
    deployment-observability,
  ]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
source: >-
  round11 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting + ui tranches, largest 2 of 10) —
  applies the exact meta-vs-implementation distinction `ui_satellite_ao_dispatch_batch1_2026_08_06.md` already
  established for this same source doc, extending it to 3 more items of the same kind that batch1 did not cover.
assigned_role: infra
effort: low
sequential: false
drift_direction: advance-docs
---

# UI satellite AO batch 3 (observability_master) — bounded meta/doc-item extraction

> **Status: active.** All 3 todos below are same-priority-independent and touch distinct files — no
> `sequential`/`gate_on_depends` needed.

## Todos

- [ ] [REVIEW] P3. **File the deployment-bucket-resolution issue doc.** Source:
      `artifact_pipeline_observability_2026_07_17.md`'s `[REVIEW] P3` "Issue doc — the whole VM tarball path bypasses
      `resolve_bucket_name()`" todo. File a single issue doc (`plans/active/issues/`) combining: (a) the VM tarball
      deployment path's `resolve_bucket_name()` bypass, and (b) the two-point AWS-lane breakage the source doc's own
      text names alongside it. Read/write/investigation only — no code change to the live artifact/tarball pipeline.
      Done when: the issue doc exists with both points captured, findings-triage tagged per the standard rule (in-file
      fix / adjacent-plan fix / new issue). Repo: unified-trading-pm.
- [ ] [INFRA] P3. **Check + report AR/ECR native vulnerability-scan status.** Source: same doc's `[INFRA] P3` "(stretch
      — optional) Image vulnerability-scan status" todo — "never itself investigated, only ever noted as remaining."
      Check whether Artifact Registry (GCP) and ECR (AWS) native vulnerability scanning is enabled on the images this
      pipeline builds, and report current status (enabled/disabled, findings summary if enabled) back into the source
      doc's Progress Log. Read-only investigation — no infra change unless the finding itself is a trivial config flip
      explicitly scoped as part of this todo's done-when. Done when: a concrete enabled/disabled status + any findings
      summary is recorded. Repo: deployment-service.
- [ ] [SCRIPT] P3. **Correct the misattributed VM origin** in
      `issues/deployment_service_qg_red_qg_snapshot_launcher_live_vm_flake_2026_07_27.md`. Source: same doc's
      `[SCRIPT] P3` todo naming this specific correction. Re-verify the VM origin attributed in that issue doc against
      current evidence (launcher logs / VM metadata / commit history) and correct it if wrong, citing the corrected
      evidence. Done when: the issue doc's VM-origin claim is verified accurate or corrected with cited evidence. Repo:
      unified-trading-pm.

## Codex SSOTs

`/codex/05-infrastructure/vm-tarball-deployment.md` (the tarball path this batch's issue-doc todo investigates).

## Progress Log

- **2026-08-09**: Batch authored via the round11 cross-cutting+ui RECLASSIFY + satellite-extraction sweep. 3 items
  extracted from `artifact_pipeline_observability_2026_07_17.md` (`observability_master`), following the exact
  meta-vs-implementation-shaped distinction `ui_satellite_ao_dispatch_batch1_2026_08_06.md` already established for this
  same source doc (batch1 pulled 2 meta/doc items and explicitly declined every implementation-shaped item as collision
  risk against the doc's live, dense, operator-reviewed in-flight build). Conflict-checked against
  `ui_satellite_ao_dispatch_batch1_2026_08_06.md` and `batch2_2026_08_08.md` (both grepped clean for these 3 items). The
  7 implementation-shaped items batch1 already declined remain declined here too — not re-litigated.
