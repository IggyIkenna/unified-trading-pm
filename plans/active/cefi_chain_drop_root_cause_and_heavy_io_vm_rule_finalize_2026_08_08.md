---
doc_type: plan
title: CeFi Surface-C chain-drop residual — finalize (verify resume sequence + archive)
summary: >-
  Gated closeout for the retroactive reclassification of
  issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md (NA → planning, 2026-08-08 na-eligibility-audit
  round7 RECLASSIFY sweep). Machine-held via depends_on + gate_on_depends: true until that doc's sole open todo (resume
  the paused `cefi-late-renames` migration: apply the 2,962-object zero-collision safe residual across 4 venues,
  loop-until-dry full-range verification, final 4-surface re-proof, archive) is done. Re-verifies every leg of that
  resume sequence actually ran on real infra with cited evidence, then archives the source doc (and its parent
  `cefi_consolidated_closeout_2026_07_18.md` if that doc is ALSO genuinely fully done at that point — verify at finalize
  time, do not assume).
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos: [instruments-service, market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, manifest, chain-drop, vm, ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
depends_on: [cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24]
gate_on_depends: true
source: >-
  Authored alongside the 2026-08-08 na-eligibility-audit round7 RECLASSIFY sweep's flip of
  issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md (NA → planning), per
  plans/active/task_template.md §4's finalize-plan-coverage rule and the retroactive-reclassification naming convention
  in /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §1(b).
context_scope:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
    market-tick-data-service/scripts/verify_cefi_canonical_4surface_2026_07_20.py,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# CeFi Surface-C chain-drop residual — finalize

> **🔒 GATED, not draft.** `depends_on: [cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24]` +
> `gate_on_depends: true` holds every todo below until that doc's sole open P1 todo (the multi-step resume sequence) is
> `done`. Authored `status: active` (not `draft`) per the established no-double-gate precedent — the gate mechanism
> already machine-holds this plan regardless of the source doc's own status.

## Todos

- [ ] [REVIEW] P1. **Verify every leg of the resume sequence actually ran on real infra, with evidence — not just that
      the source doc's checkbox flipped.** Confirm, in order: (1) the manifest-consolidator cron was verified `PAUSED`
      before any apply (`gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-cefi-cron`); (2) all
      4 sequential venue-scoped `cefi-late-renames` applies (EXTENDED-STARKNET 704 / LIGHTER-ZKSYNC 177 / BYBIT-SPOT
      1561 / COINBASE-FUTURES 520) completed with 0 errors over the full `2025-11-01..2026-07-24` range — cite each VM
      name + its terminal log line; (3) the cron was resumed and verified `ENABLED` after; (4) the loop-until-dry
      full-range verifier ran 2 CONSECUTIVE clean passes (confirming `colon_wire`'s actual disposition along the way,
      per the source doc's Finding 9 note not to assume subsumption); (5) `verify_cefi_canonical_4surface_2026_07_20.py`
      ran as the final done-state re-proof and passed. **Done when**: all 5 legs are cited with evidence (VM name/log
      line, `gcloud` output, or script exit code) and none is taken on the source doc's word alone.
- [ ] [DOC] P2. **Archive `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`, and its parent
      `cefi_consolidated_closeout_2026_07_18.md` ONLY IF that parent is also genuinely fully done at this point**
      (re-check the parent's own open todos and line-cap status directly — do not assume from this doc's stale "line-cap
      already resolved" note alone). If the parent still carries open work, archive only this doc with a pointer back to
      the parent for any residual context. Run the standard 6-step ritual for whichever doc(s) archive: banner → grep
      every corpus referrer and repoint to the archived path → clear `locked_by` → `git mv` to `plans/archive/2026_08/`.
      **Done when**: the archived doc(s) are moved, every corpus referrer resolves, and `check_reference_paths.py` has
      not regressed.

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md` — `cefi-late-renames` VM category, drain-gate discipline
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — reversibility-verified rename/delete precedent this
  reclassification relied on
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — retroactive-reclassification naming
  shape (b) this finalize doc follows
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual

## Progress Log

- **2026-08-08** — Drafted alongside the na-eligibility-audit round7 RECLASSIFY flip of
  `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`. Authored `status: active` per the established
  no-double-gate precedent; `gate_on_depends: true` already machine-holds every task here until the source doc's sole
  remaining todo is done.
- **context-scout 2026-08-15**: populated/refreshed context_scope (4 entries) — the depended-on source issue doc, the
  VM-launcher runbook, and the 2 scripts this doc's own todo 1 names directly (`launch-canonical-migration-vm.sh`,
  `verify_cefi_canonical_4surface_2026_07_20.py`).
