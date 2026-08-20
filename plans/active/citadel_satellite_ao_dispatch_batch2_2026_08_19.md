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
last_updated: "2026-08-20"
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
    /plans/active/issues/blrs_daily_determinism_ledger_root_wiring_scope_2026_08_20.md,
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
      **⚠️ PREMISE CORRECTED 2026-08-20 (AO slot-8) — READ BEFORE STARTING**: clause (1) above is false as written.
      There is NO `batch-rerun` CLI op — `strategy_service/cli/service_entry.py`'s `_OPERATIONS` registry has no such
      key, and `cli/handlers/batch_rerun.py` exposes only the library function `rerun_from_manifest()`. That op must be
      ADDED to strategy-service before any terraform stage can call it. The paper `run_id` is also not derivable from
      the date (`_gen_run_id()` carries a uuid4 suffix), so it must be resolved by listing the client's runs at job
      runtime. True scope is 2-3 repos plus a deploy-and-observe cycle (the Done-when needs a real cron execution after
      the image ships), not the `est_hours: 1.0` single checkbox this item implies. Split into 5 tracked todos +
      the open (a)/(b) design decision in
      `/plans/active/issues/blrs_daily_determinism_ledger_root_wiring_scope_2026_08_20.md` — work those, not this line.

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
- **2026-08-20** (AO worker slot-8, dispatch `citadel_satellite_ao_dispatch_batch2-2444fa0c8907`): picked up the P2.7.5
  ledger-root wiring item and found its stated premise FALSE — there is no `batch-rerun` CLI operation to trigger
  (`_OPERATIONS` in `strategy_service/cli/service_entry.py` registers only backtest/trade/seed-lifecycle/risk-monitor/
  position-recon/pnl-attribution/paper-run/paper-stream; `batch_rerun.py` is a library module). Also measured that
  `_gen_run_id()` emits a uuid4 suffix, so the paper run_id cannot be derived from the date and must be resolved by
  listing the client's runs at runtime. Measured the live baseline rather than assuming it: Stage B execution
  `uts-prod-blrs-daily-determinism-n9kxd` (2026-08-20T02:30:50Z, success) logs `paper_ledger_root/batch_ledger_root
  unset — no run to reconcile (honest no-op)`, while Stage A `uts-prod-paper-engine-run-wclvk` (02:05:07Z) writes a real
  run (`paper-20260820020050-f370fbe9`, run_manifest + 3 InstructionLedger fills) — so the input data exists nightly and
  only the rerun + root injection are missing. **The item was NOT completed**: its true scope is 2-3 repos (add the CLI
  op, add a UTL run-resolver, add the terraform stage) plus a deploy-and-observe cycle to satisfy its own Done-when, and
  it leaves a genuine (a)/(b) design choice for how the roots reach Stage B. Filed
  `/plans/active/issues/blrs_daily_determinism_ledger_root_wiring_scope_2026_08_20.md` with 5 tracked todos + that
  decision, annotated the P2.7.5 line above, and corrected the identical false claim in the terraform module's own
  Stage-B comment. Checkbox deliberately left unticked.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries) — added the new
  `blrs_daily_determinism_ledger_root_wiring_scope_2026_08_20.md` issue doc, the redirect target the P2.7.5 line's
  own premise-correction note names ("work those, not this line").
