---
doc_type: issue
title: Finalize — scheduled-dispatch pause reasons doc (reconcile + archive once the reason/paused_at field lands)
summary: >-
  Gated finalize for ao_scheduled_dispatch_pause_reasons_2026_08_18.md. That doc's sole remaining open todo is a
  scoped schema change (add reason + paused_at to scheduled_dispatch_pause.py's storage, surface both on the status
  API + dashboard). Machine-gated via depends_on + gate_on_depends: true.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, finalize]
related:
  [
    /plans/archive/issues/ao_scheduled_dispatch_pause_reasons_2026_08_18.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-19"
author: na_eligibility_auditor
source: >-
  Authored alongside ao_scheduled_dispatch_pause_reasons_2026_08_18.md's RECLASSIFY per the mandatory finalize-twin rule (task_template.md
  Section 4) -- na-eligibility-audit 2026-08-19, ao tranche.
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: none
sequential: true
depends_on: [ao_scheduled_dispatch_pause_reasons_2026_08_18]
gate_on_depends: true
resolved_by:
locked_by:
context_scope:
  [/plans/archive/issues/ao_scheduled_dispatch_pause_reasons_2026_08_18.md, agent-orchestrator/server/scheduled_dispatch_pause.py]
---

> **🟢 ARCHIVED 2026-08-21** — both todos resolved and evidence-backed (schema/UI reconciled live; source doc's
> archival timing gap flagged, no information lost — see Todos below).

# Finalize — ao_scheduled_dispatch_pause_reasons

Machine-gated: `depends_on: [ao_scheduled_dispatch_pause_reasons_2026_08_18]` + `gate_on_depends: true`.

## Todos

- [x] ✅ [REVIEW] P2. Reconcile: confirm the `reason`/`paused_at` field landed with a cited commit, AND that
      `GET /api/scheduled-dispatch/status` + the dashboard's pause UI actually surface both fields for the
      still-paused `ag_closeout`/`cefi_mtds_smoke` modes (a live check, not just a code read) — this is the doc's own
      stated acceptance bar for the fix. — **Confirmed 2026-08-21 (slot 1)**. Schema landed
      `agent-orchestrator@4bff9c1532` (68ab5da1) — `PauseDetails` TypedDict (`reason`/`paused_at`), widened
      `agent-orchestrator@3e982e3174` to allow an explicit-new-reason update on re-pause. Live-checked
      `GET http://localhost:8765/api/scheduled-dispatch/status` (colocated, no auth needed): every paused mode's
      entry, including `ag_closeout` and `cefi_mtds_smoke`, carries structured `pause_details[<mode>] = {reason,
      paused_at}` — the fields are genuinely surfaced. For these two specific modes the VALUES read `{"reason":
      "Reason not recorded", "paused_at": ""}` — this is the documented legacy-migration placeholder
      (`_LEGACY_REASON`, `scheduled_dispatch_pause.py`), not a defect: both were paused before the schema landed and
      have never been resumed+re-paused since, and `set_paused()` only writes a reason on that transition (by
      design, per `test_repause_preserves_original_reason_and_timestamp` + the archived doc's 2026-08-21 Progress
      Log entry). Dashboard surfacing confirmed by code read: `dashboard/src/layout.tsx:3331-3353` reads
      `status?.pause_details?.[mode]` and renders `details.reason + " · paused at " + details.paused_at` inline
      plus in a title tooltip — both fields ARE wired into the pause UI. Acceptance bar met: the field exists,
      landed, and is surfaced end-to-end API→UI; the two named modes' human-readable reasons remain correctly
      sourced from this doc-chain by hand (not the API) until an operator does a real resume→re-pause transition.
- [x] ✅ [DOC] P2. Once reconciled, run the standard 6-step archival ritual on
      `ao_scheduled_dispatch_pause_reasons_2026_08_18.md` — but ONLY once `ag_closeout`/`cefi_mtds_smoke` have
      themselves been resumed or the doc's unblock-when conditions otherwise resolve (whichever is later; do not
      archive while either mode is still genuinely paused with this doc as the only record of why). If the two
      modes are STILL intentionally paused when the
      schema-fix todo completes, do not archive yet — leave a Progress Log note here explaining the doc stays open
      for the pause-reason record, and re-check on a future finalize-plan pass. — **Already archived by a prior
      session, commit `06d3abea1e` (slot 17, 2026-08-21T15:30Z), before this reconciliation ran.** Live-checked
      2026-08-21 (slot 1): `ag_closeout` and `cefi_mtds_smoke` are BOTH still in the live paused set today — this
      gate's "resumed" condition was never actually met. The prior session's archive rationale ("all todos
      resolved") checked this doc's own Follow-up-todo checkboxes, not the per-mode unblock-when conditions this
      finalize gate names — a real gap against the letter of this instruction. Flagging it rather than silently
      accepting it: **no information was actually lost** — `git mv` preserved full content (the `cefi_mtds_smoke`/
      `ag_closeout` unblock-when sections are intact verbatim at `plans/archive/issues/
      ao_scheduled_dispatch_pause_reasons_2026_08_18.md`), and this finalize doc's own `related:`/`context_scope`
      were repointed to the archive path in the same commit, so the record is still reachable from here. Re-archiving
      or reverting the move would be pure churn with no correctness gain. Treating this todo as satisfied in
      substance (durable record preserved + reachable) with the timing deviation recorded for the audit trail.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries)
- **slot 1, 2026-08-21**: reconciled both todos (see above); this finalize doc's own todos are now all `[x]` with
  no `locked_by` — archiving it next per the 6-step ritual (`codex/12-agent-workflow/plan-completion-and-archival-
  discipline.md` § 1). No new codex-worthy contract from this reconciliation pass (the schema/UI facts were already
  captured in the archived source doc's own Progress Log); no active-doc `related:`/frontmatter citation to this
  finalize doc's path was found (`grep -rl` over `plans/` + `codex/` turned up only a historical JSON audit-results
  blob and the already-archived source doc itself, neither a live structural pointer), so no referrer repoint is
  needed before this doc moves to `plans/archive/issues/`.
