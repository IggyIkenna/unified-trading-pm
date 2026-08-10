---
doc_type: plan
title: Infra satellite AO dispatch batch 13 — finalize (reconcile source-doc checkbox + archive the batch)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch13_2026_08_09.md`, per the finalize-plan-coverage gate
  (task_template.md §4). Once the batch's single todo is done, reconciles the corresponding item back into
  `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` (flip its todo 2),
  then archives ONLY the batch pair itself — the source doc is NOT an archival candidate (its todos 1 and 3 stay open,
  gated on an operator credential/emulator decision and on both prior items respectively).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, finalize, batch-13, ui, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
effort: medium
sequential: true
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
depends_on: [infra_satellite_ao_dispatch_batch13_2026_08_09]
gate_on_depends: true
source: >-
  Paired with `infra_satellite_ao_dispatch_batch13_2026_08_09.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule (every AO batch plan needs a paired gated finalize).
---

# Infra satellite AO batch 13 — finalize

> **`status: active`, but machine-gated** (`depends_on` + `gate_on_depends: true`) — per the no-double-gate ruling, the
> finalize twin stays `active` even while its parent batch (`infra_satellite_ao_dispatch_batch13_2026_08_09.md`) is
> `status: draft`; the dispatcher will not queue the todo below until that plan's single todo is `done`.

Machine-held via `depends_on` + `gate_on_depends: true` until batch13's one todo is done — this plan can never dispatch
early, regardless of whether the batch is `draft` or `active` at the time.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile
      `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`'s todo 2.**
      Once batch13's todo ships, flip that source doc's matching `- [ ]` checkbox to `[x]`, citing the batch13 commit
      SHA. **Do NOT archive the source doc** — confirm its todo 1 (Firebase Admin credential/emulator decision) and todo
      3 (re-run gated on both 1 and 2) are still genuinely open before concluding anything about archival eligibility;
      the source doc stays active with 2 open items regardless of batch13's outcome. (repo: unified-trading-pm) — done.
      Verified `unified-trading-system-ui@1c59c624` against the live commit, flipped the source doc's todo 2, confirmed
      todos 1 and 3 remain genuinely open (source doc stays active, not archived).
- [ ] [DOC] P3. **Archive both `infra_satellite_ao_dispatch_batch13_2026_08_09.md` and
      `infra_satellite_ao_dispatch_batch13_finalize_2026_08_09.md`** once the reconciliation above is verified — run the
      standard 6-step archival ritual (`git mv` to `plans/archive/2026_08/`, fix every corpus referrer path, confirm
      `check_ag_closeout_linkage.py` and `regenerate_active_plan_inventory.py` both stay clean). Do this as a SEPARATE
      commit from the checkbox-flip commit above (never combine a flip + `git mv` in one commit —
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). (repo: unified-trading-pm)

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4

## Progress Log

- **2026-08-09** — Drafted alongside `infra_satellite_ao_dispatch_batch13_2026_08_09.md` during the round-9
  infra-tranche combined RECLASSIFY+satellite-extraction sweep. Set `status: active` per the no-double-gate ruling (its
  own `depends_on`+`gate_on_depends: true` on the still-`draft` parent already prevents early dispatch).
- **2026-08-10 (slot-8)** — Todo 1 (reconcile) done: batch13's todo shipped (`unified-trading-system-ui@1c59c624`),
  verified against the live commit content, and the source issue doc's todo 2 flipped citing that SHA; confirmed the
  source doc's todos 1 and 3 remain genuinely open, so it stays active (not archived). Todo 2 (archive the batch pair)
  not yet done — separate commit per the no-combine-flip-and-git-mv rule.
