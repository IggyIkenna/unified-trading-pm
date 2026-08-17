---
doc_type: plan
title: cefi satellite AO dispatch batch 21 — 2026-08-17
summary: >-
  Extraction batch from the cefi tranche's 2026-08-17 /na-eligibility-audit run — 2 conflict-cleared,
  bounded/deterministic todos pulled from 2 source docs (RECLASSIFY_SPLIT bounded items; each source doc's
  remaining open items stay assigned_vm: NA and are unaffected). Each todo cites its exact source doc; this run
  flipped the extracted checkbox in each source doc at authoring time to cite this batch, matching the
  na-eligibility-audit skill's Phase 3 "per-todo split" extraction mechanics. Conflict-checked against every
  existing active batch/finalize plan for this tranche (incl. batch20), the cefi consolidated-closeout docs, and
  every other active assigned_vm:planning doc via the shared four-surface protocol before drafting — no item here
  duplicates ground an existing dispatched todo already claims. A third RECLASSIFY_SPLIT candidate found in this
  same run (`issues/cloud_interface_list_blobs_stale_read_misled_vm_stall_diagnosis_2026_08_15.md`) is deliberately
  NOT included here — that doc's owning tranche is `infra` (parent_epic infrastructure_master routes there per the
  primary-owner rule), not `cefi`; only the owning tranche may extract from or write to a shared doc.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
    /plans/active/issues/dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-17 cefi-tranche /na-eligibility-audit run (autonomous, dispatch agt-af111e). status:
  active from the start (not draft) per the skill's 2026-08-10 no-double-gate ruling — na-eligibility-audit's own
  RECLASSIFY verdict + conflict-check IS the authorization to dispatch (unlike /ag-closeout-audit's batches, which
  stay draft pending separate operator approval).
---

# cefi satellite AO dispatch batch 21 — 2026-08-17

> Every todo below was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call)
> by the 2026-08-17 cefi-tranche na-eligibility-audit run and conflict-checked against every existing active
> batch/finalize plan in this tranche (incl. batch20), the consolidated-closeout docs, and the wider active corpus
> before being drafted here. Each source doc's OWN checkbox for the extracted item was flipped at authoring time
> citing this batch; the source doc's remaining (non-extracted) items stay `assigned_vm: NA`.

## Todos

- [x] ✅ [SCRIPT] P2. Confirm the `alerting-service` dedup fix (`attempted_age_hours` + generic `*_age_*` suffix
      exclusion added to `AlertDeduplicator`, shipped `alerting-service@cd60a3e595`) reached the live
      `dp-alerting-subscriber` Cloud Run revision: (1) confirm the sha (or later) is an ancestor of `origin/main`,
      (2) confirm a fresh Cloud Build ran against that content, (3) confirm
      `dp-alerting-subscriber`'s `status.latestReadyRevisionName` is that fresh revision AND carries 100% traffic
      (`gcloud run services describe`). Source: `plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`
      item 2. Done-when: all 3 conditions confirmed with cited evidence (commit ancestry, Cloud Build id, traffic
      split), or a fresh Cloud Build is triggered and its result cited if propagation hadn't happened yet.
      **Done — all 3 confirmed 2026-08-17**: (1) content-on-main match (ancestry inconclusive as expected, squash
      merge); (2) Cloud Build `821c691f-8da4-426e-b7b1-9d0614097064` SUCCESS `00:48:57Z`; (3)
      `dp-alerting-subscriber-00103-zhw` @ 100% traffic, container-content-verified via `docker pull`+extract.
      Evidence: cloudbuild=821c691f-8da4-426e-b7b1-9d0614097064. Deploy
      chain is clean — but live behavior is STILL broken (cooldown violated as of 07:06Z, ~6h15m post-deploy), a
      SEPARATE unresolved defect filed as
      `plans/active/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md` (P1, 2 new todos).
- [ ] [DATA] P3. Annotate
      `market-tick-data-service/scripts/migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py` (still present,
      not yet deleted per its own `# Delete-when:` header) with a pointer to
      `dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md`'s finding, so a future
      reader doesn't trust the script's "any row carrying this error_reason shares the same defect" docstring claim
      at face value — it's known-incomplete (the doc's live-vs-batch analysis found the live capture path also
      legitimately emits the same `error_reason`). Source:
      `plans/active/issues/dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md` item 3.
      Done-when: the script's docstring/header carries a comment pointing at the finding doc's path.

## Progress Log

- **na-eligibility-audit 2026-08-17 (cefi tranche, dispatch agt-af111e)**: drafted this batch from 2 conflict-cleared
  RECLASSIFY_PER_TODO_SPLIT candidates found during the 2026-08-17 cefi-tranche Phase 1 classification pass (19
  in-scope docs read end-to-end via a 5-agent Workflow fan-out). Both source docs' own checkboxes flipped to cite
  this batch at authoring time. A third RECLASSIFY_SPLIT candidate (`cloud_interface_list_blobs_stale_read_misled_vm_stall_diagnosis_2026_08_15.md`)
  was found but excluded — owning tranche is `infra`, not `cefi`, per the Phase-0 primary-owner rule; reported to
  that tranche's own audit instead of acted on here.
- **2026-08-17 (slot 18, backend_engineer craft, task cefi_satellite_ao_dispatch_batch21-5517a0a936a2)**: item 1
  closed — all 3 deploy-chain conditions confirmed (content-on-main, Cloud Build `821c691f-8da4-426e-b7b1-9d0614097064`,
  live revision `dp-alerting-subscriber-00103-zhw` @ 100% traffic, container-content-verified). Residual finding (fix
  deployed but live behavior still violates the cooldown) filed separately:
  `plans/active/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md`.
