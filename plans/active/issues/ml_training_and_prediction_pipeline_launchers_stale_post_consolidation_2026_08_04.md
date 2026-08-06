---
doc_type: issue
title:
  launch-ml-training-vm.sh and launch-prediction-pipeline-vm.sh invoke stale pre-consolidation module paths — surfaced
  while deleting the 8 stale features_*_service/ml_*_service SERVICE_TARBALLS keys
summary: >-
  Grep-then-read-verified while shipping `infra_satellite_ao_dispatch_batch2_2026_07_27.md` #5 (delete 8 stale
  `features_*_service` keys + adjacently fix stale `ml_*_service` keys in `setup-data-pipeline-vm.sh`'s
  SERVICE_TARBALLS). Two live (non-deprecated) launchers still reference module/service names that no longer exist post
  `features_repo_consolidation_2026_05_08.md`: (1) `launch-ml-training-vm.sh` sets `VM_SERVICE=ml_training_service` and
  builds `VM_BACKFILL_CMD="python -m ml_training_service ..."` — no such Python package exists anywhere in the workspace
  (only `ml_service.training` as a submodule of the consolidated `ml-service` repo), and `SERVICE_TARBALLS` never had
  (and now definitely doesn't have) a `ml_training_service` key mapping to a real tarball, so this launcher is currently
  non-functional end-to-end. (2) `launch-prediction-pipeline-vm.sh`'s embedded VM user-data script verifies `from
  features_cross_instrument_service.cli.main import main` and `from features_delta_one_service.cli.main import main` —
  both pre-consolidation top-level package names; only `features_service.cross_instrument` /
  `features_service.delta_one` exist as subpackages of the consolidated `features-service` repo now. This is the SAME
  bug class already tracked as S1-a (`launch-prediction-features-vm.sh`) in
  `mdps_features_deadcode_consolidation_2026_07_20.md` todo 1, but that todo does not name
  `launch-prediction-pipeline-vm.sh` — a distinct file with the same defect.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [dead-code, stale-launcher, vm-launcher, consolidation, features, ml-training, prediction]
related:
  [
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch2_2026_07_27.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-04
author: unknown
last_updated: 2026-08-04
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-ml-training-vm.sh,
    deployment-service/scripts/vm/launch-prediction-pipeline-vm.sh,
  ]
supersedes:
superseded_by:
resolved_by:
source: >-
  Surfaced 2026-08-04 while shipping infra_satellite_ao_dispatch_batch2_2026_07_27.md #5 (delete 8 stale
  features_*_service SERVICE_TARBALLS keys in deployment-service/scripts/vm/setup-data-pipeline-vm.sh; verifying no live
  launcher still set VM_SERVICE to any deleted key surfaced these two separate, unrelated-to-the-deletion, pre-existing
  bugs).
---

# `launch-ml-training-vm.sh` + `launch-prediction-pipeline-vm.sh` — stale post-consolidation module paths

## What I found

While confirming no live launcher still sets `VM_SERVICE` to any of the 8 deleted stale `features_*_service` keys (or
the 2 deleted `ml_*_service` keys) before removing them from `setup-data-pipeline-vm.sh`'s `SERVICE_TARBALLS` /
`TARBALL_DIRS` / `MTDS_DEPENDENT_SERVICES`, I found two unrelated-but-same-class pre-existing bugs neither caused nor
fixed by that deletion (verified: removing the already-dead `ml_training_service` key does not change either launcher's
already-broken end state — see "Why it matters" below):

1. **`deployment-service/scripts/vm/launch-ml-training-vm.sh`** (header: `Lifecycle: permanent`, no deprecation note)
   sets `METADATA="${METADATA},VM_SERVICE=ml_training_service"` (line ~172) and builds
   `ML_CMD="python -m ml_training_service ..."` (line ~154). Grepped the full workspace: no `ml_training_service` Python
   package exists anywhere — only `ml-service/ml_service/training/` (a submodule of the consolidated `ml-service` repo).
   The script's own comments (lines ~145-153) already acknowledge this is a stopgap: "Phase B will add a dedicated
   `elif [[ "$VM_TASK" == "ml-training" ]]` branch to setup-data-pipeline-vm.sh that maps the clean ml-training CLI
   directly. For now, VM_BACKFILL_CMD is the cleanest seam that already exists." That Phase B was never done.
   `SERVICE_TARBALLS` never had a working `ml_training_service` entry either (the key existed pre-deletion but pointed
   at `ml-training-service-code`, a tarball `create-code-tarballs.sh` no longer builds per its own comment: "no such
   repos/tarballs exist anymore").
2. **`deployment-service/scripts/vm/launch-prediction-pipeline-vm.sh`** (header: no deprecation note, described as
   launching the "full PREDICTION pipeline") embeds a VM startup script that runs
   `python3 -c "from features_cross_instrument_service.cli.main import main; ...; from features_delta_one_service.cli.main import main; ..."`
   under `set -euo pipefail`. Both `features_cross_instrument_service` and `features_delta_one_service` are
   pre-`features_repo_consolidation_2026_05_08` top-level package names; the consolidated `features-service` repo only
   exposes these as `features_service.cross_instrument` / `features_service.delta_one` subpackages now. This is the
   exact same bug class already tracked as S1-a in
   `plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md` todo 1 for the sibling
   `launch-prediction-features-vm.sh` (which is explicitly DEPRECATED-but-preserved and already awaiting an operator
   A/B/C keep/delete decision) — but that todo names only `launch-prediction-features-vm.sh`, not
   `launch-prediction-pipeline-vm.sh`.

## Why it matters

Neither launcher can currently succeed end-to-end: (1) fails at `python -m ml_training_service` with
`ModuleNotFoundError` regardless of whether the tarball ever lands; (2) fails at its own `set -e`-gated import-verify
step with `ModuleNotFoundError` before it ever reaches the actual feature computation. Both predate today's
SERVICE_TARBALLS cleanup and are unaffected by it either way — a preempted/relaunched VM using either launcher was
already failing before today, and still fails after (verified: deleting the dead `ml_training_service` /
`features_cross_instrument_service`-adjacent keys only changes which failure path is hit — "no SERVICE_TARBALLS match,
falls to install-all-tarballs WARNING branch" vs "SERVICE_TARBALLS match on a tarball that was already silently
un-buildable" — not whether the launcher ultimately succeeds). Not fixing inline because the correct fix needs a design
call this P3 mechanical-deletion todo didn't scope: for (1), either build the Phase B `setup-data-pipeline-vm.sh`
`VM_TASK=ml-training` branch the script's own comments describe, or rewrite `launch-ml-training-vm.sh` to shell out to
`ml_service`'s actual training CLI (needs verifying its argparse surface matches
`--operation/--instruments/--target-types/--timeframes`); for (2), same A/B/C keep/delete/repoint decision already
pending for the sibling S1-a launcher likely applies, but needs its own verification (does
`launch-features-vm.sh --feature-family cross_instrument`/`delta_one` cover this pipeline's chunked MDPS→features
sequencing, or was `launch-prediction-pipeline-vm.sh` never superseded because its 3-step MDPS+cross_instrument+
delta_one sequencing has no consolidated equivalent yet).

## Recommended decision

Operator/main to fold into the same A/B/C decision already open for S1-a/S1-b in
`mdps_features_deadcode_consolidation_2026_07_20.md`, or triage separately — recommend (A) extend that doc's existing
decision to cover both new launchers found here (same root cause, same consolidated-launcher-coverage question), since
splitting into a third parallel decision thread on the same theme adds coordination overhead for no benefit.

## Todos

- [ ] 1. [SCRIPT] P2. Verify `ml_service`'s actual training CLI surface (`ml-service/ml_service/training/` +
      `ml-service/ml_service/cli` or equivalent) against `launch-ml-training-vm.sh`'s assembled
      `--operation/--instruments/--target-types/--timeframes/--start-date/--end-date` args; either rewrite the launcher
      to call it directly (`python -m ml_service.training ...` or whatever the real entrypoint is) or build the
      `setup-data-pipeline-vm.sh` `VM_TASK=ml-training` Phase B branch the script's own header describes, then set
      `VM_SERVICE=ml_service` and delete the dead `ml_training_service` metadata value. Repo: deployment-service.
- [ ] 2. [SCRIPT] P2. Determine whether
      `launch-features-vm.sh --feature-family cross_instrument|delta_one     --asset-group PREDICTION` (the consolidated
      launcher) covers `launch-prediction-pipeline-vm.sh`'s 3-step MDPS→cross_instrument→delta_one chunked sequencing;
      if yes, fold this launcher into the same S1-a keep/delete decision in
      `mdps_features_deadcode_consolidation_2026_07_20.md` and repoint/delete; if no (chunking logic has no consolidated
      equivalent), fix its embedded import-verify to use
      `features_service.cross_instrument`/`features_service.delta_one` in place. Repo: deployment-service.

## Progress Log

- **context-scout 2026-08-06**: populated context_scope (4 entries — added the doc's own two named launcher scripts,
  `launch-ml-training-vm.sh` and `launch-prediction-pipeline-vm.sh`, alongside the pre-existing S1-a sibling issue and
  the vm-launcher-runbook codex SSOT).
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid (first pass, no prior marker) — the
  doc's own text states the correct fix needs a design call this P3 mechanical-deletion todo didn't scope; both open
  items redirect to the same still-open A/B/C decision pending in `mdps_features_deadcode_consolidation_2026_07_20.md`
  (independently verified: that doc is still `status: open`, unlocked, todos unchecked).
