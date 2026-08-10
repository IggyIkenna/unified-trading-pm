---
doc_type: issue
title: >-
  VM tarball deployment path (GCP) still bypasses resolve_bucket_name() and hardcodes
  deployment-scripts-central-element-323112 across 21+ scripts — the two AWS-lane bucket bugs this was to be combined
  with are ALREADY FIXED (2026-08-07/08), not open
summary: >-
  Filed per artifact_pipeline_observability_2026_07_17.md's Phase-6 `[REVIEW] P3` stretch todo, which asked for one
  combined issue doc covering (a) the VM tarball path's `resolve_bucket_name()` bypass and (b) the "two-point AWS-lane
  breakage" it names alongside it. Live re-verification 2026-08-09: (a) is CONFIRMED still open — neither
  `setup-data-pipeline-vm.sh` nor `create-code-tarballs.sh` calls `resolve_bucket_name()`; both, plus 19 sibling
  launcher scripts, still hardcode the literal `deployment-scripts-central-element-323112`. (b) — the two AWS-lane bugs
  (#4 freeze-deferred-replay filter, #7 AWS tarball launcher 404 bucket), tracked in
  `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` — are BOTH already shipped
  (`unified-trading-pm@b87cc06fcf` and `deployment-service@61cf93f44`, 2026-08-07), re-confirmed live in this doc's own
  investigation. So this doc records (a) as new open work and (b) as closed-prior context only, rather than duplicating
  already-tracked-and-shipped fixes.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, gcs, bucket-resolution, tarballs, vm-launchers, deployment-observability]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/ui_satellite_ao_dispatch_batch3_2026_08_09.md,
    /plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
author: unknown
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "artifact_pipeline_observability_2026_07_17.md Phase 6 [REVIEW] P3 stretch todo, dispatched via
    ui_satellite_ao_dispatch_batch3_2026_08_09.md todo 1",
  ]
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/scripts/vm/create-code-tarballs.sh,
  ]
---

# Deployment bucket resolution gaps — VM tarball path (GCP) still bypasses resolve_bucket_name()

## What I found

### (a) VM tarball path bypasses `resolve_bucket_name()` (GCP) — CONFIRMED, still open

Live-verified 2026-08-09 against `deployment-service` HEAD:

- `scripts/vm/setup-data-pipeline-vm.sh:47` — `CODE_BUCKET="${CODE_BUCKET:-deployment-scripts-central-element-323112}"`
- `scripts/vm/create-code-tarballs.sh:46` — `DEFAULT_BUCKET="deployment-scripts-central-element-323112"`
- Neither file (nor any other file in `scripts/vm/`) calls `resolve_bucket_name()` —
  `grep -n "resolve_bucket_name" scripts/vm/setup-data-pipeline-vm.sh scripts/vm/create-code-tarballs.sh` returns
  nothing.
- The literal `deployment-scripts-central-element-323112` is duplicated across **21 `.sh` files** under
  `deployment-service/scripts/vm/` (measured via
  `grep -rl "deployment-scripts-central-element-323112" deployment-service/scripts --include="*.sh" | wc -l` = 21),
  including `setup-cefi-live-consolidated-vm.sh`, `vm_instruments_backfill.sh`, `vm_mtds_backfill.sh`, and multiple
  `launch-*-vm.sh` entrypoints. The source plan's own citation said "~48 launchers" (unverified count, possibly spanning
  other repos/file shapes not re-checked here) — this doc's 21-file figure is the live re-measurement against
  `deployment-service` `.sh` files specifically, not a refutation of the larger estimate.
- This contradicts the workspace storage-code hard rule (CLAUDE.md § "Writing STORAGE code": every bucket via
  `resolve_bucket_name(...)`, never inline `gs://`/hardcoded bucket literals) and the codex bucket-isolation-model
  SSOT's description of how bucket names should be resolved.
- **No live incident today** — single bucket, single GCP project, works as-is. This is a maintainability/consistency gap
  (a bucket rename or multi-project migration would require manually chasing 21+ files instead of one central resolver),
  not an active defect.
- Read/investigation only in this pass — no code change made, per this todo's own scope.

### (b) "Two-point AWS-lane breakage" — BOTH ALREADY FIXED, not open work

The plan's Phase-6 todo asked to combine (a) with "the two-point AWS-lane breakage" it names alongside it. That breakage
is `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`'s #4 and #7, and live re-verification
2026-08-09 confirms **both are already shipped**, predating this doc:

- **#4 — AWS freeze-deferred builds never replay.** SHIPPED 2026-08-07, `unified-trading-pm@b87cc06fcf`. Live-verified
  today: `.github/workflows/freeze-deferred-build-replay.yml:119` and `:201` both match
  `(.name | startswith("deferred-build-")) or (.name | startswith("deferred-aws-build-"))` — the widened filter is live.
- **#7 — AWS tarball launcher pointed at a nonexistent bucket.** SHIPPED 2026-08-07, `deployment-service@61cf93f44`.
  Live-verified today: `scripts/vm/lib/aws_ec2_launch_lib.sh:236`, `:289`, `:388` all resolve to
  `uts-prod-deployment-state` (matching the uploader's real target), not the old 404
  `unified-trading-deployment-scripts-<account>` bucket.

Both todos in the source issue doc are already `[x]` closed. No new work is filed here for (b) — it is recorded only so
this doc's own "combine (a) and (b)" instruction is answered honestly rather than silently dropped.

## Why it matters

- (a) is a real, standing violation of the workspace's own bucket-resolution convention, but low urgency (single bucket,
  single project, no active breakage). Worth fixing opportunistically, not urgently.
- (b) needed no action — filing it here purely closes the loop on the plan's own combined-doc instruction; the
  underlying fixes were already tracked, shipped, and verified by their own issue doc.

## Recommended decision

Findings triage (CLAUDE.md § "Findings triage"): (a) is a new, small, deterministic-outcome fix (swap a hardcoded
literal default for a `resolve_bucket_name(...)` call in ~21 identifiable files) — AO-eligible, filed as a todo below.
(b) needs no todo — already resolved and independently tracked/closed in its own issue doc.

## Todos

- [x] ✅ [INFRA] P3. Migrate the VM tarball deployment path's hardcoded `deployment-scripts-central-element-323112`
      bucket-name default to resolve via the B-011 canonical bash form (`deployment-scripts-${PROJECT}` /
      `-${PROJECT_ID}`, per /codex/05-infrastructure/vm-tarball-deployment.md — the bash-side equivalent of the
      storage-code `resolve_bucket_name(...)` rule; `resolve_bucket_name()` is Python-only and the yaml SSOT has no
      `deployment-scripts` kind, and `setup-data-pipeline-vm.sh` needs the bucket before UTL is installed), across all
      23 files found by the re-run grep (2026-08-09 measured 21; re-measured 2026-08-10 at fix time = 23, the set
      shifted: `vm_heartbeat_sidecar.sh` + `vm_instruments_reference.sh` were not in the original 21-file list),
      starting with `setup-data-pipeline-vm.sh:47` and `create-code-tarballs.sh:46`. Repo: deployment-service. —
      deployment-service@f8d3312d
- [ ] [INFRA] P3. Extend the deployment-bucket resolution migration to the remaining NON-`.sh` / cross-repo hardcoded
      `deployment-scripts-central-element-323112` occurrences surfaced by the 2026-08-10 cross-repo scan:
      deployment-service `.github/workflows/sync-vm-scripts-to-gcs.yml:46` (`BUCKET:` env) +
      `runbooks/tarball_cleanup_maintenance.md` + `scripts/vm/README.md`; e2e-testing
      `scripts/common/{vm_prediction_backfill,vm_instruments_backfill,vm_setup_and_run,vm_fss_features,vm_mdps_reprocess,vm_instruments_reference,vm_mtds_backfill}.sh` +
      `scripts/prediction/setup-backfill-vm.sh`; market-tick-data-service
      `scripts/{analyze_shard_memory,migrate_cefi_v2}.py` +
      `scripts/sports/league_id_relocation/manifest_swap_2026_07_22.py` +
      `scripts/sports/k1k2_casing_revert_2026_07_27/manifest_swap_casing_revert_2026_07_27.py`. Repo:
      deployment-service, e2e-testing, market-tick-data-service.

## Progress Log

- **2026-08-09** — Filed (`ui_satellite_ao_dispatch_batch3_2026_08_09.md` todo 1). Live re-verified both halves of the
  source plan's combined-doc ask: (a) resolve_bucket_name() bypass CONFIRMED still open (21 files, live grep); (b) the
  two AWS-lane bugs it was to be combined with are BOTH already shipped 2026-08-07/08 (`unified-trading-pm@b87cc06fcf`,
  `deployment-service@61cf93f44`) — re-confirmed live against current workflow/script content, not just read from the
  prior issue doc's own claim. Filed one new todo for (a); no new todo for (b).
- **2026-08-10** — Todo 1 code COMPLETE but SHIP-PENDING. Migrated all 23 `scripts/vm/*.sh` hardcoded
  `deployment-scripts-central-element-323112` occurrences (re-grep at fix time = 23 files, up from the 2026-08-09
  measure of 21 — `vm_heartbeat_sidecar.sh` + `vm_instruments_reference.sh` were not in the original list) to the B-011
  canonical bash form `deployment-scripts-${PROJECT}`/`-${PROJECT_ID}`: VM-side scripts (`setup-data-pipeline-vm.sh`,
  `setup-cefi-live-consolidated-vm.sh`, `setup-prediction-live-consolidated-vm.sh`, `vm_heartbeat_sidecar.sh`,
  `vm_{mtds,instruments,instruments_reference}_backfill.sh`) derive PROJECT/PROJECT_ID from GCE metadata (fallback =
  prod project id); `create-code-tarballs.sh` / `launch-strategy-test-vm.sh` from env with prod default; the remaining
  launchers reuse their existing `PROJECT="central-element-323112"` var. No live behavior change (all forms resolve to
  the same bucket). Verification: `grep -rl "deployment-scripts-central-element-323112" scripts --include="*.sh"` = 0
  files, `bash -n` clean on all 156 derived-form launchers. Committed locally as `deployment-service@f979b809` but **NOT
  shipped** — Pass-1 QG is RED for a PRE-EXISTING reason: 11 `test_dp_recovery_actuators.py` failures (PAGE vs SUCCEEDED
  on preemption-relaunch pin resolution) introduced by peer dp-monitors commits `49cb5de6`/`2f077c97`/etc. landing
  between the last green sentinel `8a033d44` and LDR head `1717d294`. Verified not mine (actuator only checks
  launcher-file existence, never reads .sh content; tests mock run_launcher). Repo-blocker declared; issue filed
  (`dp_recovery_actuator_tests_regression_2026_08_10.md`). Cross-repo scan surfaced related hardcoded literals in
  e2e-testing (8 .sh copies), market-tick-data-service (4 .py), and deployment-service's non-.sh surfaces (workflow
  env + runbook/README) — filed as follow-up todo 2 above.
- **2026-08-10** — Todo 1 SHIPPED: `deployment-service@f8d3312d` (rebased SHA; originally `f979b809`). The pre-existing
  QG red (11 `test_dp_recovery_actuators.py` failures) was fixed by the fleet via escalation `agt-acb0ed` +
  `c472a818 fix(dp-monitors): force disk-path budget in dp_recovery actuator tests` (a test-environment/budget-path fix,
  not a logic regression). Rebased onto the fixed LDR head, Pass-1 QG re-ran GREEN (sentinel == HEAD), shipped via
  quickmerge agent mode (strict-quickmerge hook passed, `f8d3312d` on origin). Verified on origin; literal count in
  `scripts --include="*.sh"` = 0, `bash -n` clean on all 156 derived-form launchers. Follow-up todo 2 (non-.sh /
  cross-repo occurrences) remains open.
