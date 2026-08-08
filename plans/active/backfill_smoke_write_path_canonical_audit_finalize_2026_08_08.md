---
doc_type: plan
title: Backfill-smoke write-path canonical audit — finalize (doc-comment correction + archive)
summary: >-
  Gated closeout for the retroactive reclassification of
  issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md (NA → planning, 2026-08-08 na-eligibility-audit
  round7 RECLASSIFY sweep). Machine-held via depends_on + gate_on_depends: true until that doc's sole remaining open
  todo (correcting 3 in-repo comments that wrongly assert the instruments-service instrument_availability writer
  emits the hive layout, when the audit's own §3b proved it emits the flat day=/venue= shape) is done. Re-verifies
  the shipped correction against the actual code shape at execution time (the writer may itself have been
  canonicalized in the interim — check both directions, don't assume the doc's 2026-07-20 finding is still current),
  then archives the source doc via the standard 6-step ritual once genuinely zero open work remains.
status: active
nature: process
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, canonical, gcs-paths, ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: [backfill_smoke_write_path_canonical_audit_2026_07_20]
gate_on_depends: true
source: >-
  Authored alongside the 2026-08-08 na-eligibility-audit round7 RECLASSIFY sweep's flip of
  issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md (NA → planning), per
  plans/active/task_template.md §4's finalize-plan-coverage rule and the retroactive-reclassification naming
  convention in /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §1(b).
context_scope:
  [
    /plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md,
    /codex/02-data/non-canonical-path-inventory.md,
    instruments-service/instruments_service/engine/orchestrator/writers.py,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Backfill-smoke write-path canonical audit — finalize

> **🔒 GATED, not draft.** `depends_on: [backfill_smoke_write_path_canonical_audit_2026_07_20]` +
> `gate_on_depends: true` holds every todo below until that doc's sole open todo (the doc-comment correction) is
> `done`. Authored `status: active` (not `draft`) per the established no-double-gate precedent — the gate mechanism
> already machine-holds this plan regardless of the source doc's own status.

## Todos

- [ ] [REVIEW] P2. **Verify the doc-comment correction shipped as specified, re-checking against the actual code
      shape at execution time.** Confirm all 3 named locations (`instrument_availability_paths.py:1-23`'s
      re-homed-to-hive docstring claim, `instructions-service/docs/DEFI_INSTRUMENTS.md:642`, and
      `repair_tradfi_instrument_type_counts_2026_07_17.py:21`) now accurately describe what the live
      `instrument_availability` writer actually emits. **Two possible outcomes, check both**: (a) the writer is
      STILL flat (`day=/venue=`, per the source doc's original §3b finding) — the 3 comments should now say so; (b)
      the writer was independently canonicalized to hive in the interim (a sibling migration/fix landed since
      2026-07-20) — in that case the comments were arguably right all along and the fix is to note the source doc's
      finding as superseded-by-events, not to rewrite the comments to describe a now-stale flat shape. Cite the
      shipping commit + which outcome applies. **Done when**: all 3 locations are verified accurate against the
      live code, one way or the other, with the commit cited.
- [ ] [DOC] P3. **Archive `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`** via the standard 6-step
      ritual once todo 1 confirms zero open items remain in its body (Todos 1/2/4/5/6 are already `[x]`; todo 3 is
      the only remaining item, gated on the above): migrate any still-open follow-up to a tracked todo → add the
      archive banner → grep the corpus for every referrer of this doc's filename and repoint each to the archived
      path → clear `locked_by` (already empty) → move to `plans/archive/2026_08/issues/`. **Done when**: the doc is
      archived, every corpus referrer resolves, and `check_reference_paths.py` has not regressed.

## Codex SSOTs

- `/codex/02-data/non-canonical-path-inventory.md` — canonical-grammar ledger this audit's findings feed
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — retroactive-reclassification
  naming shape (b) this finalize doc follows
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual

## Progress Log

- **2026-08-08** — Drafted alongside the na-eligibility-audit round7 RECLASSIFY flip of
  `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`. Authored `status: active` per the established
  no-double-gate precedent; `gate_on_depends: true` already machine-holds every task here until the source doc's
  sole remaining todo is done.
