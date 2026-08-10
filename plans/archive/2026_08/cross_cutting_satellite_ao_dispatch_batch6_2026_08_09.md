---
doc_type: plan
title:
  Cross-cutting satellite AO batch 6 — infrastructure_master bounded residuals (honest-coverage VM launcher hardening +
  workflow-template lint) extracted from the round9 2026-08-09 sweep
summary: >-
  Sixth AO-dispatch batch for the cross-cutting tranche, produced by the round9 2026-08-09 RECLASSIFY +
  satellite-extraction sweep (a follow-up to yesterday's 4-batch pass, run because 5 Slack alerting webhooks + a
  DeepSeek GSM secret landed today). Pulls 3 bounded items out of 2 source docs, both `infrastructure_master`: 2 from
  `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (harden the `honest-coverage-daily` launcher to verify
  VM terminal state instead of "VM launched ⇒ success"; fix a stale VM metadata label) and 1 from
  `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md` (a template-content lint pre-flight
  check in `rollout-workflow-templates.sh`). None trace to the new webhook/DeepSeek facts specifically — these are
  pre-existing bounded engineering items each source doc's own history left un-actioned pending a whole-doc RECLASSIFY
  bar that a genuinely operator-gated sibling item (immediate machine-type-bump decision; the promote-PR
  non-supersession investigation) kept from clearing.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta, data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer]
tags:
  [
    cross-cutting,
    ao-dispatch,
    close-out,
    batch-6,
    satellite-docs,
    infrastructure-master,
    honest-coverage,
    vm-launcher,
    workflow-templates,
  ]
related:
  [
    /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md,
    /plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch6_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md,
    /plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
source: >-
  round9 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting tranche, largest of 10) — a follow-up
  to yesterday's 4-batch (2/1b/4/5) sweep, checking whether newly-landed facts (5 Slack webhooks + a DeepSeek GSM
  secret) unblock more docs; these 3 items were already-bounded and unrelated to those facts, found via a full re-read
  of every candidate doc.
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 6 (infrastructure_master) — bounded-item extraction

> **ARCHIVED 2026-08-10** — All 3 todos shipped and verified (todo 1 reconciliation by slot 7, review): todo 1
> `deployment-service@b44166be`, todo 2 `deployment-service@10df4a3c7`, todo 3 `unified-trading-pm@92ab939583`
> (corrected from the batch's own mis-cited `8a7b1860a0` in the finalize todo 1, verified on origin). Closed out by
> `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch6_2026_08_09_finalize.md`. Both source docs'
> checkboxes reconciled there; neither source doc reached 0 open todos, so neither was archived here. No Deferred items.

## Todos

- [x] ✅ [INFRA] P3. **Harden `honest-coverage-daily-launcher` to verify VM terminal state, not just "VM launched".** —
      deployment-service@b44166be. Source: `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (its 3rd
      `[INFRA] P3` todo). The Cloud Run Job launcher
      (`deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh`) previously reported success once the
      `instances.insert` API call for the VM succeeded — it never polled the VM's own output object
      (`gs://central-element-323112-honest-coverage/<date>/coverage.json`) or checked for a terminal exit signal, so a
      VM that OOM-kills 2 minutes after boot (as this exact class did 3 consecutive days, 08-06/07/09) was invisibly
      reported as a successful launcher run. Fixed by adding `lc_poll_for_terminal_state` to
      `scripts/vm/lib/launcher_common.sh`: polls (default 20min window, 30s interval) for the expected output object to
      be freshly written after launch; returns FAILURE fast if the VM disappears (self-deleted via
      `VM_SHUTDOWN_ON_COMPLETION`) without ever writing it, or on timeout if it's still running past the window —
      mirrors the "no fire-and-forget" pattern `/codex/05-infrastructure/vm-launcher-runbook.md` states for direct
      operator VM launches, applied one level removed (a launcher-of-a-launcher). The launcher now exits non-zero on
      FAILURE/TIMEOUT instead of returning immediately after launch; `honest-coverage-daily-launcher`'s Cloud Run Job
      `timeout_seconds` bumped 300s → 1500s (`terraform/gcp/honest_coverage_scheduler.tf`) to cover the new poll window
      — a non-zero exit already surfaces as `failed` in the existing deployment-observability Cloud Run Job status
      surface (exit_code badge + 3-layer out-of-band deadman monitoring,
      `/codex/05-infrastructure/deployment-observability.md`), so no new alerting plumbing was needed. Done-when
      verified via 3 new unit tests in `tests/unit/test_vm_launcher_scripts.py::TestLcPollForTerminalState` (stubbed
      `gcloud`, no real GCE VM launched): fresh-output ⇒ SUCCESS, VM-gone-with-no-output ⇒ immediate FAILURE (does NOT
      wait the full window, does NOT report blind success), window-elapsed-while-still-running ⇒ TIMEOUT FAILURE. All
      225 tests in the file pass; full `quality-gates.sh` green. Repo: deployment-service.
- [x] ✅ [INFRA] P3. **Fix the `honest-coverage-daily` VM's stale metadata `TASK=features-backfill` self-label.**
      Source: `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (its 4th `[INFRA] P3` todo — the doc's own
      text calls this "the only unambiguously bounded item"). The VM instance metadata sets `TASK=features-backfill` (a
      stale/generic launcher-template default) instead of an honest-coverage-specific label — cosmetic today, but would
      mislead a future log-grep-by-TASK debugging session. Fix the metadata-setting call in
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` (or whichever shared VM-metadata helper it
      delegates to) to set an accurate `TASK=` value for this launcher specifically. Done when: a fresh VM launch (or a
      `gcloud compute instances describe` on the next natural daily fire) shows the corrected `TASK=` metadata value.
      Repo: deployment-service. — deployment-service@10df4a3c7 (the `TASK=features-backfill` label was NOT accidental
      staleness — code comments confirmed `VM_TASK=measure-honest-coverage` had no dedicated dispatch branch in
      `setup-data-pipeline-vm.sh`, so it borrowed `features-backfill`'s branch, which reads `VM_BACKFILL_CMD` verbatim,
      to avoid falling through to the generic `--operation` CLI dispatch that rejects `--asset-group=all`. Root fix:
      added a dedicated `elif [[ "$VM_TASK" == "measure-honest-coverage" ]]` branch to `setup-data-pipeline-vm.sh`
      mirroring the existing `datapoint-validation`/`orphan-sweep` pattern (same `VM_BACKFILL_CMD`-verbatim dispatch
      shape, same `instruments` workspace `cd`), then switched `launch-measure-honest-coverage-vm.sh`'s
      `METADATA="VM_TASK=..."` to the accurate value. Verified: bash syntax check on both files, full `quality-gates.sh`
      green (395s), `git merge-base --is-ancestor` confirmed on origin. Done-when is satisfied on the launcher-script
      side; the "next natural daily fire" VM-metadata confirmation happens automatically at the 00:30 UTC
      `honest-coverage-daily` Cloud Scheduler trigger — no separate action needed since `create-code-tarballs.sh`
      already auto-publishes the launcher script per its own header comment).
- [x] ✅ [SCRIPT] P3. **Add a template-content lint pre-flight to `rollout-workflow-templates.sh`.** Source:
      `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md` (its remaining `[SCRIPT] P3`
      todo). `prettier --write` deterministically mangles a bare `{{PLACEHOLDER}}` YAML flow-mapping-shaped token
      (root-caused + fixed for `{{RUNS_ON}}` → `__RUNS_ON__` in this same doc's own resolution) — the residual risk is
      any FUTURE placeholder token in one of the still-flat-copy templates suffering the same silent mangling and
      shipping broken to every consuming repo before anyone notices (surfaces only later as a red `quality-gates-v2`).
      Add a lightweight pre-flight check to `scripts/workflow-templates/rollout-workflow-templates.sh` (or
      `check-action-pins.py`'s pre-flight pass) that `yaml.safe_load`s each flat-copy template AFTER prettier would run
      on it (i.e. after the pre-commit hook's own formatting pass, or by invoking prettier on a scratch copy and parsing
      the result), failing the rollout script's own pre-flight if any template fails to parse — so a future
      prettier-mangled placeholder is caught at rollout time, not after propagating to every consuming repo. **Scale
      note** (per the source doc's own 2026-08-08 correction): the blast radius for this specific check is now just
      `image-build-gate.yml` + `notify-slack.yml` + `staging-lock-check.yml` + `quality-gates-v2.yml.tmpl` — the other 5
      of the original 9 templates were converted to `unified-trading-ci`-hosted `workflow_call` stubs by a separate,
      larger dedup effort and no longer flow through this rollout mechanism. Done when: the pre-flight check is wired
      into the rollout script, verified to catch a deliberately-reintroduced mangled placeholder in a scratch test, and
      the 4 still-flat templates all pass it cleanly today. Repo: unified-trading-pm. — unified-trading-pm@8a7b1860a0

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md` (no-fire-and-forget principle), `/codex/08-workflows/ci-cd-flow.md`
(workflow templates / quickmerge gate set).

## Progress Log

- **2026-08-09**: Batch authored via the round9 cross-cutting RECLASSIFY + satellite-extraction sweep. 3 items extracted
  from 2 `infrastructure_master` source docs — the surrounding whole-doc RECLASSIFY bar stayed unmet in both cases
  (genuinely operator-gated/investigation-shaped sibling items remain), but these 3 are individually bounded and
  worker-determinable, so extracted per the per-item satellite-extraction path.
