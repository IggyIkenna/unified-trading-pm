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
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta, data]
repos: [deployment-service, unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-6, satellite-docs, infrastructure-master, honest-coverage, vm-launcher, workflow-templates]
related:
  [
    /plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md,
    /plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch6_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
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

> **Status: active.** All 3 todos below are same-priority-independent and touch distinct files — no
> `sequential`/`gate_on_depends` needed.

## Todos

- [ ] [INFRA] P3. **Harden `honest-coverage-daily-launcher` to verify VM terminal state, not just "VM launched".**
      Source: `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (its 3rd `[INFRA] P3` todo). The Cloud Run
      Job launcher (`deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` +/or the owning Cloud Run Job
      code) currently reports success once the `instances.insert` API call for the VM succeeds — it never polls the
      VM's own output object (`gs://central-element-323112-honest-coverage/<date>/coverage.json`) or checks for a
      terminal exit signal, so a VM that OOM-kills 2 minutes after boot (as this exact class did 3 consecutive days,
      08-06/07/09) is invisibly reported as a successful launcher run. Add a post-launch verification step: poll for
      the expected output object (or a `_SUCCESS`/exit-code marker) for up to N minutes after VM launch; if absent,
      alert (page) instead of silently reporting Cloud Run Job success. Mirrors the "no fire-and-forget" pattern
      `/codex/05-infrastructure/vm-launcher-runbook.md` already states for direct operator VM launches, applied here
      one level removed (a launcher-of-a-launcher). Done when: the launcher's own reported status reflects the VM's
      real terminal state, verified by simulating (or re-triggering, if the same OOM class is still live) a failed run
      and confirming the launcher does NOT report blind success. Repo: deployment-service.
- [ ] [INFRA] P3. **Fix the `honest-coverage-daily` VM's stale metadata `TASK=features-backfill` self-label.** Source:
      `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` (its 4th `[INFRA] P3` todo — the doc's own text
      calls this "the only unambiguously bounded item"). The VM instance metadata sets `TASK=features-backfill` (a
      stale/generic launcher-template default) instead of an honest-coverage-specific label — cosmetic today, but
      would mislead a future log-grep-by-TASK debugging session. Fix the metadata-setting call in
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` (or whichever shared VM-metadata helper it
      delegates to) to set an accurate `TASK=` value for this launcher specifically. Done when: a fresh VM launch
      (or a `gcloud compute instances describe` on the next natural daily fire) shows the corrected `TASK=` metadata
      value. Repo: deployment-service.
- [ ] [SCRIPT] P3. **Add a template-content lint pre-flight to `rollout-workflow-templates.sh`.** Source:
      `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md` (its remaining `[SCRIPT] P3`
      todo). `prettier --write` deterministically mangles a bare `{{PLACEHOLDER}}` YAML flow-mapping-shaped token
      (root-caused + fixed for `{{RUNS_ON}}` → `__RUNS_ON__` in this same doc's own resolution) — the residual risk is
      any FUTURE placeholder token in one of the still-flat-copy templates suffering the same silent mangling and
      shipping broken to every consuming repo before anyone notices (surfaces only later as a red
      `quality-gates-v2`). Add a lightweight pre-flight check to `scripts/workflow-templates/rollout-workflow-templates.sh`
      (or `check-action-pins.py`'s pre-flight pass) that `yaml.safe_load`s each flat-copy template AFTER prettier would
      run on it (i.e. after the pre-commit hook's own formatting pass, or by invoking prettier on a scratch copy and
      parsing the result), failing the rollout script's own pre-flight if any template fails to parse — so a future
      prettier-mangled placeholder is caught at rollout time, not after propagating to every consuming repo. **Scale
      note** (per the source doc's own 2026-08-08 correction): the blast radius for this specific check is now just
      `image-build-gate.yml` + `notify-slack.yml` + `staging-lock-check.yml` + `quality-gates-v2.yml.tmpl` — the other
      5 of the original 9 templates were converted to `unified-trading-ci`-hosted `workflow_call` stubs by a separate,
      larger dedup effort and no longer flow through this rollout mechanism. Done when: the pre-flight check is wired
      into the rollout script, verified to catch a deliberately-reintroduced mangled placeholder in a scratch test, and
      the 4 still-flat templates all pass it cleanly today. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md` (no-fire-and-forget principle), `/codex/08-workflows/ci-cd-flow.md`
(workflow templates / quickmerge gate set).

## Progress Log

- **2026-08-09**: Batch authored via the round9 cross-cutting RECLASSIFY + satellite-extraction sweep. 3 items
  extracted from 2 `infrastructure_master` source docs — the surrounding whole-doc RECLASSIFY bar stayed unmet in both
  cases (genuinely operator-gated/investigation-shaped sibling items remain), but these 3 are individually bounded and
  worker-determinable, so extracted per the per-item satellite-extraction path.
