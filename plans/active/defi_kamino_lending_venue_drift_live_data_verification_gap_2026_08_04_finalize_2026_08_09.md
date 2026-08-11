---
doc_type: plan
title: >-
  defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for issues/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md — machine-held via
  depends_on + gate_on_depends: true until the source doc's sole remaining item (the bounded read_availability_index
  re-check for residual venue=KAMINO_LENDING rows in the ~15h 2026-08-05T17:42Z -> 2026-08-06T08:29Z accumulation
  window, plus a conditional idempotent retire-script re-run) is done. Reconciles the source doc's own checkbox once
  shipped (citing fresh manifest evidence), then archives it via the standard 6-step ritual once fully closed. Authored
  2026-08-09 as part of the na-eligibility-audit defi-tranche RECLASSIFY sweep, per task_template.md's
  finalize-plan-coverage rule (every assigned_vm:planning doc needs a companion gated finalize plan).
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04]
gate_on_depends: true
source: >-
  na-eligibility-audit defi tranche, 2026-08-09 —
  issues/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md was reclassified assigned_vm:NA ->
  planning after the "stale-check-defi-tranche 2026-08-09" Progress Log entry content-verified the blocking precondition
  (code fix reaching `main`) was actually satisfied since 2026-08-06T08:29:26Z (`f706456a`), two days earlier than the
  2026-08-07 audit believed (that audit's ancestry-based check false-negatived under this repo's `ldr_main`
  non-fast-forward promotion model). What remains is a single bounded, worker-determinable read_availability_index
  re-check + conditional idempotent retire; conflict-checked clean against currently-active AO plans in parent_epic
  manifest_master, the defi consolidated-closeout doc, and the two prior descriptive citations
  (defi_satellite_ao_dispatch_batch10_2026_08_06.md's stale archivable_now list entry,
  ag_closeout_audit_defi_parked_2026_08_07.md Finding 6's superseded "mark for re-check" recommendation). This finalize
  doc closes the finalize-plan-coverage gate the reclassification itself triggered.
assigned_role: data_engineering
effort: high
drift_direction: none
context_scope:
  [
    /plans/active/issues/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/one_offs/retire_kamino_lending_legacy_venue_2026_08_05.py,
  ]
---

# defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04 — finalize

## Todos

- [x] ✅ [DATA] P3. **Reconcile — DONE (slot 17, 2026-08-09).** The bounded, column-pruned
      `read_availability_index(bucket, columns=["venue","date","chain","data_type","instrument_type","capture_status", "attempted_at","written_at"], filters=[("date",">=","2026-08-05")])`
      check was executed by slot 17 on 2026-08-09 (memory-bounded via `run-bounded-analysis.sh --mem-cap 4G`). Row-group
      pushdown on `date>=2026-08-05` returned 399,456 rows; case-insensitive `venue=="KAMINO_LENDING"` match found 113
      rows — all `date=2026-08-05`, all already `capture_status=attempted_failed` (the 2026-08-05 retire run's own
      output). **Zero rows with `date=2026-08-06`** and **zero `capture_status=="captured"` rows** anywhere in the
      `date>=2026-08-05` slice. The source doc's `[DATA] P2` todo was already flipped by slot 17 with this evidence. No
      `retire_kamino_lending_legacy_venue_2026_08_05.py --apply` re-run was needed. — **0 rows, verified 2026-08-09
      (slot 17).**
- [ ] [DOC] P3. **Archive.** Run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md` once todo 1 confirms it is fully
      closed — dated archive folder, exact-successor banner, corpus-wide referrer fixup (this finalize doc,
      `defi_consolidated_closeout_2026_07_18.md` if it cites this doc,
      `defi_satellite_ao_dispatch_batch10_2026_08_06.md`'s stale list entry, and
      `ag_closeout_audit_defi_parked_2026_08_07.md` Finding 6). Then archive this finalize plan itself in the same pass.
      **Done when**: the source doc and this finalize plan are both under `plans/archive/`, and
      `check_reference_paths.py` shows zero new broken referrers.

## Progress Log

- **2026-08-09**: authored alongside the source doc's `assigned_vm: NA -> planning` reclassification
  (na-eligibility-audit defi tranche run).
- **2026-08-11 (slot 9)**: todo 1 flipped — the reconcile was already executed by slot 17 on 2026-08-09 (0 rows needing
  remediation; see source doc Progress Log for full evidence). No re-run of
  `retire_kamino_lending_legacy_venue_2026_08_05.py` was needed. Proceeding to archival (todo 2).
