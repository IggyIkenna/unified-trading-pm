---
doc_type: plan
title: Infra satellite AO batch 3 — finalize (reconcile source-doc checkboxes, do NOT archive either source)
summary: >-
  Gated closeout for infra_satellite_ao_dispatch_batch3_2026_07_30.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24; machine-enforced by
  scripts/quality_gates/check_finalize_plan_coverage.py, which is at baseline 0 — a 2-todo assigned_vm:planning plan
  without a gated twin is a hard regression, not a warning). Once both batch todos are done, reconciles the
  corresponding checkbox back into each source doc. Unusually for a finalize plan, the expected outcome is that NEITHER
  source doc becomes archivable — both were partial carve-outs and both keep judgment-gated todos at assigned_vm: NA —
  so this plan's main job is to flip accurately and then explicitly NOT archive, rather than to run the 6-step ritual on
  the sources. It does run the ritual on the batch pair itself.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, finalize, batch-3, plan-hygiene]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/active/issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md,
    /plans/active/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch3_2026_07_30]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/active/issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md,
    /plans/active/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch by `/ag-closeout-audit infra` (2026-07-30), per the standing
  finalize-plan-coverage rule (every ≥2-todo assigned_vm:planning plan needs a gated finalize twin).
---

# Infra satellite AO batch 3 — finalize

> **ARCHIVED 2026-08-07** — Both todos done. Parent batch (`infra_satellite_ao_dispatch_batch3_2026_07_30.md`) and this
> finalize plan archived together. G1 re-check: still gated by infra batch6's active base-service.sh claim. G3 re-check:
> already shipped by `deployment-ui@fecd67c`. Stop-iterating verdict re-confirmed. See Progress Log for full evidence.

## Todos

- [x] ✅ [DOC] P2. **Reconcile both source docs' checkboxes — and deliberately do NOT archive either.** Once the parent
      batch's 2 todos are `[x]`: (1) in
      `issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md`, close the first
      `[SCRIPT] P2` item (the `--dry-run` gating fix) citing the parent todo's actual commit sha — **re-verify the sha
      exists** (`git show --stat <sha>`), do not trust the batch doc's own copy of the evidence line; (2) in
      `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md`, close its first two `[BACKEND] P3` items (the
      two diagnostics) citing the recorded verdict, and if that verdict makes exactly one answer to todo 3 provably
      right, annotate todo 3 with the recommendation **without** closing it; (3) confirm each source doc still has
      genuine open todos and therefore stays `status: open`, `assigned_vm: NA` — expected residual is 2 items in the
      gitignore doc (template reconciliation + its gated `[VERIFY] P3`) and 1 in the git-health doc (the field-design
      fork). **If either doc unexpectedly reaches zero open todos, that is a real archival candidate** and gets the full
      6-step ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), not just a checkbox flip.
      **Done when**: each of the 4 extracted checkboxes is closed with a re-verified sha or explicitly left open with a
      re-confirmed reason, and each source doc's `status`/`assigned_vm` matches its actual residual.
- [x] ✅ [DOC] P2. **Re-check the parent's Deferred table, then archive the batch pair.** (1) Re-test the two
      ruled-but-gated clusters the parent recorded as still-blocked — G1 (`base-service.sh`/`base-library.sh`
      serialization, entry #36) and G3 (`DataStatusTab.tsx` sequencing, entry #35): if
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s `base-service.sh` sub-item and
      `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s todos 1/11 have landed, and
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[INFRA] P2` part (B) has landed, those items are
      newly conflict-clear — **file them as a tracked follow-up todo/plan rather than executing them here** (this is a
      finalize plan, not an extraction vehicle). If still gated, record the re-measured state so the next reader does
      not re-derive it. (2) Re-test the parent's stop-iterating verdict: re-run
      `generate_ag_closeout_audit_candidates.py --tranche infra` and confirm the never-cited-orphan set is still purely
      non-batchable; if a new orphan with bounded work has appeared, say so explicitly (that is the one condition that
      would justify a batch4). (3) Run the standard 6-step archival ritual on the parent batch and on THIS plan. **Done
      when**: the Deferred re-check is recorded with measured evidence (not assumption), the stop-iterating verdict is
      either re-confirmed or explicitly retracted, and both plans of the pair are archived with every corpus-wide
      referrer path fixed.

## Progress Log

- **2026-08-07 (slot 10) — todo 1 done. unified-trading-pm@08cfee7f7.** Reconciled all 4 extracted checkboxes: (1)
  `gitignore_sync…` item 1: already `[x]` @ `78a3740bf` — re-verified SHA exists (`git show --stat`), correct. (2)
  `git_health…` item 1: closed `[x] ✅` — verdict (i) REFUTED (fresh `reported_at` per cron run); citing
  `unified-trading-pm@594aea342` where verdict was recorded. (3) `git_health…` item 2: closed `[x] ✅` — verdict (ii)
  REFUTED (aggregation surfaces per-repo values, not collapsed-global); citing same `594aea342`. (4) `git_health…` item
  3: explicitly left open `[ ]` — annotated with bugfix recommendation (per-repo `_read_repo_dirty_ticks` lookup instead
  of host-wide aggregate); implementation out of scope, requires AO QG. Both source docs retain `status: open`,
  `assigned_vm: NA`: gitignore doc has 2 open items (template reconciliation + gated VERIFY), git_health doc has 1 open
  item (field-design fork). Neither is archivable. Neither was archived.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (4 entries) — finalize gate, code-free by design.
- **2026-08-07 (slot 13) — todo 2 done. Both plans archived.** Deferred re-check (measured live, not assumed): **G1**
  (`base-service.sh`/`base-library.sh` serialization): The two named blocking conditions are now met —
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s `[BACKEND] P3` is `[x]` done;
  `ci_satellite_ao_dispatch_batch2_2026_07_29.md` is fully archived (todos 1 and 11 both `[x]`). However, a NEW active
  claim exists: `infra_satellite_ao_dispatch_batch6_2026_08_02.md` has an open `[INFRA] P3` touching `base-service.sh`
  (re-verified via `rg`). Under the serialized-resource ruling (one owning plan at a time), G1 remains **GATED** —
  re-check once infra batch6's `base-service.sh` todo is done. **G3** (`DataStatusTab.tsx` `DATA_PIPELINE_SERVICES`):
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[INFRA] P2` part (B) is `[x]` done. No competing batch
  claims on `DataStatusTab.tsx`. Re-checked live: `deployment-ui@fecd67c` (2026-08-06) already updated
  `DATA_PIPELINE_SERVICES` with FOLD A names + strategy-service + ml-service — the G3 work is **already shipped**. No
  follow-up needed. **Stop-iterating re-check**: `generate_ag_closeout_audit_candidates.py --tranche infra` now reports
  47 members / 13 covering docs / 4 never-cited orphans (vs. 32/7/6 at 2026-07-30). All 4 new orphans assessed: (a)
  `ci_pipeline_speed_and_cost_redesign_2026_08_05.md` — design plan, design-preference-gated; not batchable. (b)
  `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` — actively BLOCKED
  (event-timing/operation-gated); not batchable. (c)
  `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` — `[DESIGN] P2` requires a design
  decision first; not batchable. (d) `self_hosted_runner_public_repo_revert_2026_08_05.md` — item 20 is measurement-only
  (read billing metrics, update doc; no code change); borderline AO-eligible but gates on a "longer-window measurement"
  — does not justify a batch4. Stop-iterating verdict **re-confirmed**: no new orphan with bounded code/plan-change work
  has appeared. **6-step ritual**: (1) all deferred items tracked in batch1's Deferred section (batch1 at 1000-line hard
  cap — G1 new gate noted here only); G3 already shipped; (2) archived banners added; (3) no codex contracts changed;
  (4) no CLAUDE.md updates; (5) corpus-wide referrers updated below; (6) both plans moved to `plans/archive/2026_08/`.
