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

**RESOLVED 2026-08-09.** The sibling S1-a/S1-b A/B/C decision this doc's "fold into" framing depended on was
declassified 2026-08-08 (round5-cefi-question-resolution, `mdps_features_deadcode_consolidation_2026_07_20.md`) —
neither item here was actually a business/spend judgment, credential gate, or reversibility-failed destroy, so the
"operator/architect call" framing no longer held. Both items were extracted verbatim into
`cefi_satellite_ao_dispatch_batch15_2026_08_09.md` and shipped independently (see Todos above) rather than folded into
the sibling doc's own decision thread — todo 1 needed no A/B/C fold-in at all (a direct module-path repoint), and todo
2's own verification determined the sibling's keep/delete precedent doesn't apply (no consolidated launcher covers its
3-step chunked sequencing), so it was fixed in place on its own merits.

## Todos

- [x] ✅ 1. [SCRIPT] P2. **`launch-ml-training-vm.sh`'s dead `ml_training_service` module path fixed.** —
      deployment-service@082a5eda (verified reachable on `origin/live-defi-rollout`, landed 2026-08-09 via
      `cefi_satellite_ao_dispatch_batch15_2026_08_09.md` todo 1). Repointed `ML_CMD` to `python -m ml_service.training`
      (verified importable), set `VM_SERVICE=ml_service`, removed the dead `ml_training_service` metadata + stale
      Phase-B-pending comments; `quality-gates.sh` green. No longer gated on the sibling S1-a A/B/C decision — that
      decision was declassified 2026-08-08 (round5-cefi-question-resolution) and this item was extracted + dispatched
      through the resolved framing, not folded into a still-open sibling decision.
- [x] ✅ 2. [SCRIPT] P2. **`launch-prediction-pipeline-vm.sh`'s dead pre-consolidation feature-service import paths
      fixed.** — deployment-service@03b10e46 (verified reachable on `origin/live-defi-rollout`, landed 2026-08-09 via
      `cefi_satellite_ao_dispatch_batch15_2026_08_09.md` todo 2). Determined `launch-features-vm.sh` does NOT cover this
      launcher's 3-step MDPS→cross_instrument→delta_one chunked sequencing (no MDPS candle-derivation step, no per-stage
      differential date windowing) — fixed in place rather than folding into the S1-a delete decision: repointed the
      packaged `REPOS`/`uv pip install` loop, the embedded import-verify step, and the STAGE 2/3 runtime CLI invocations
      to the consolidated `features-service` package/dispatcher; verified both import paths resolve live and
      `quality-gates.sh` is green. Same sibling A/B/C decision context as todo 1 above — resolved 2026-08-08, this item
      was fixed on its own merits (not a keep/delete fold-in) once verification showed no consolidated equivalent covers
      its sequencing.
- [ ] [DOC] P3. **Archive this doc via the 6-step ritual**
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) now that both substantive todos above are
      done and unlocked — this doc has 7 active corpus referrers that a genuine archival needs to repoint in the same
      commit, out of scope for a plain checkbox-reconciliation pass:
      `plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`,
      `plans/active/cefi_satellite_ao_dispatch_batch12_2026_08_09.md`,
      `plans/active/issues/ag_closeout_audit_defi_parked_2026_08_08.md`,
      `plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
      `plans/active/cefi_satellite_ao_dispatch_batch15_2026_08_09.md`,
      `plans/active/cefi_satellite_ao_dispatch_batch15_2026_08_09_finalize.md`, `plans/active/INDEX.md`. **Done when**:
      doc moved to `plans/archive/2026_08/`, every listed referrer repointed, `run_hygiene_sweep.sh` green.

## Progress Log

- **context-scout 2026-08-06**: populated context_scope (4 entries — added the doc's own two named launcher scripts,
  `launch-ml-training-vm.sh` and `launch-prediction-pipeline-vm.sh`, alongside the pre-existing S1-a sibling issue and
  the vm-launcher-runbook codex SSOT).
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid (first pass, no prior marker) — the
  doc's own text states the correct fix needs a design call this P3 mechanical-deletion todo didn't scope; both open
  items redirect to the same still-open A/B/C decision pending in `mdps_features_deadcode_consolidation_2026_07_20.md`
  (independently verified: that doc is still `status: open`, unlocked, todos unchecked).
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi tranche)**: this doc's own gate (the sibling A/B/C
  decision in `mdps_features_deadcode_consolidation_2026_07_20.md`) was declassified 2026-08-08
  (round5-cefi-question-resolution — applying `task_template.md` finding U's positive test, neither item is a
  business/spend judgment, a credential gate, nor a whole-bucket destroy/failed reversibility check, so the prior
  "operator/architect call" framing no longer holds). `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` (drafted the
  same day, extracting the sibling S1-a item) independently flagged this doc's own cross-reference as stale and "out of
  this todo's stated single-file scope... flagging for whoever next touches that doc." Conflict-checked clean (grepped
  `plans/active/` for both named launcher files — only this doc and an unrelated Class-B stall-kill finding reference
  them). Both items extracted verbatim into `cefi_satellite_ao_dispatch_batch15_2026_08_09.md` (`status: active`,
  `assigned_vm: planning`) + its gated finalize twin. This doc's own `assigned_vm` stays `NA` — per the established
  corpus convention (see `mdps_features_deadcode_consolidation_2026_07_20.md`'s own S1-a extraction), the satellite
  batch is the live AO-dispatch surface; this doc becomes a historical redirect once its batch lands.
- **finalize-reconciliation 2026-08-09** (`cefi_satellite_ao_dispatch_batch15_2026_08_09_finalize.md` todo 1): both
  `cefi_satellite_ao_dispatch_batch15_2026_08_09.md` todos landed (deployment-service@082a5eda,
  deployment-service@03b10e46) — both SHAs independently verified `git merge-base --is-ancestor`-reachable on
  `origin/live-defi-rollout` before citing. Replaced the redirect-only "EXTRACTED — see that doc" pointers above with
  real `[x]` checkboxes citing the verified commits + evidence directly in this doc, and updated the "Recommended
  decision" section's stale "fold into the same A/B/C decision already open for S1-a" framing to state the decision
  resolved 2026-08-08 (round5-cefi-question-resolution) and both items shipped independently via batch15. **Remaining
  open count: 1** (a new todo 3, filed as a follow-up rather than skipped — archiving this doc needs a corpus-referrer
  sweep across 7 active referrers, out of this reconciliation pass's scope). Doc's own substantive work (todos 1-2) is
  fully resolved; `status` stays `open` pending todo 3's archival sweep.
