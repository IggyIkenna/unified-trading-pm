---
doc_type: plan
title: Citadel paper⟷batch⟷live reconciliation — satellite AO batch 2 (2 conflict-clear infra items found while shipping P2.7.4)
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-19 /na-eligibility-audit sweep (slot 30,
  na_eligibility_auditor, dispatch agt-dc3dbe) — 2 conflict-cleared, bounded/deterministic infra items pulled from
  `citadel_paper_batch_live_reconciliation_2026_06_19.md`'s Phase 7 register (RECLASSIFY per-todo split). Both items
  (P2.7.4b terraform-state reconcile, P2.7.5 wire ledger-roots + cron trigger) were found 2026-08-18 while
  live-deploying the P2.7.4 fix and were never assessed by any prior na-eligibility-audit pass on this doc. Conflict-
  checked against the archived `citadel_satellite_ao_dispatch_batch1_2026_08_08.md` + its finalize (read directly —
  neither mentions terraform, blrs_daily_determinism, or ledger_root), the cross-cutting consolidated closeout, and
  every active satellite batch corpus-wide — no item here duplicates ground an existing dispatched todo already
  claims. The source doc's own `assigned_vm: NA` stays unchanged (P2.7.3's permanent live-wallet hard-stop still
  justifies it).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, strategy-service]
scope: [engineer]
tags: [reconciliation, paper-trading, determinism, ao-dispatch, satellite-batch, na-eligibility-audit, citadel, terraform]
related:
  [
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/epics/batch_live_symmetry_master.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: infra
effort: medium
drift_direction: advance-infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf,
    strategy-service/strategy_service/cli/handlers/batch_rerun.py,
  ]
source: >-
  /na-eligibility-audit cross-cutting tranche, dispatch agt-dc3dbe, slot 30, 2026-08-19. Each item's own Source:
  line below names the exact source doc + todo it was extracted from.
---

# Citadel paper⟷batch⟷live reconciliation — satellite AO batch 2

## From `citadel_paper_batch_live_reconciliation_2026_06_19.md`

- [x] ✅ [INFRA] P2. **Reconcile terraform state for `blrs_daily_determinism_job` before the next real `tofu apply` of
      this module.** `tofu plan -target=module.blrs_daily_determinism_job` shows the resource as untracked ("1 to
      add") — this module's state is stale/missing relative to the live job, which was hotfixed out-of-band via
      `gcloud run jobs update` for P2.7.4 and likely originally created by a different deploy path than a plain
      `tofu apply` from this checkout. An untargeted `tofu apply` of `terraform/gcp/` before this is reconciled
      could try to recreate or otherwise diverge from the gcloud-applied live spec. Import the live resource into
      state (`tofu import` or the equivalent `-refresh-only` reconciliation). Repo: deployment-service. Done when: a
      subsequent full `tofu plan` for this directory shows no unexpected diff. Source:
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` item P2.7.4b.
- [ ] [INFRA] P2. **Wire `paper_ledger_root`/`batch_ledger_root` + a batch-rerun trigger stage into the
      `blrs-daily-determinism` cron.** `ReconConfig.paper_ledger_root`/`batch_ledger_root` default `""` and nothing
      in `paper_week_determinism_scheduler.tf` ever populates them, so `--operation daily-determinism` currently
      runs as a permanent (correct, honest) no-op — it never actually reconciles. Needs: (1) a stage that triggers
      strategy-service's existing `batch-rerun` CLI op (`cli/handlers/batch_rerun.py`, proven ε=0 — P2.7.2/P9.B)
      against the prior day's paper run to produce "run B"'s ledger, and (2) a mechanism (wrapper script or Cloud
      Scheduler body override, since the run_id isn't known at `tofu apply` time) to resolve "yesterday's paper
      run_id" and inject both ledger roots as env vars into the daily-determinism job. Repo: deployment-service +
      strategy-service. Done when: the cron's own log shows a real (non-no-op) reconciliation result. Source:
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` item P2.7.5.

## Progress Log

- **2026-08-19**: drafted by na-eligibility-audit (cross-cutting tranche, dispatch agt-dc3dbe, slot 30). Both items
  conflict-checked clear against the archived batch1 + finalize, the consolidated closeout, and every active
  satellite batch corpus-wide.
- **context-scout 2026-08-19**: populated context_scope (4 entries) — added the two source-code targets each item's
  own text names (the terraform module and the strategy-service CLI handler).
- **2026-08-20**: persisted a targeted `tofu apply -refresh-only -target=module.blrs_daily_determinism_job`
  against the production GCS state. Verified the live resource identity and hotfixed `daily-determinism` command;
  the post-refresh targeted plan reports **No changes**. An untargeted full plan still reports unrelated existing
  drift (`4 to add, 63 to change`), so no broad apply was run.
