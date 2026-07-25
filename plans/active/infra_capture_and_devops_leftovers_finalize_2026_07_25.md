---
doc_type: plan
title: Infra capture wiring + devops leftovers — finalize (reconcile parent checkboxes + archive)
summary: >-
  Gated closeout for infra_capture_and_devops_leftovers_2026_07_06.md ("AO Plan 6" of the instruments-completion set),
  added per the finalize-plan-coverage gate (task_template.md §4, operator ruling 2026-07-24 — every `assigned_vm:
  planning` plan with >1 total todo needs a companion gated finalize plan so its checkboxes get reconciled and it goes
  through the archival ritual instead of sitting done-but-never-archived forever). Machine-held via `depends_on` +
  `gate_on_depends: true` until the parent's dispatchable todo (the ASTER live connector registration) is done — the
  parent's other 4 open items are `BLOCKED-CREDENTIALS`/ `BLOCKED-OPERATOR-DECISION` and won't clear on their own, so
  this finalize plan's own archival todo stays correctly gated open until those are individually resolved (same posture
  as any other blocked-item plan — not a defect, the honest state).
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [infra, capture, ao-dispatch, finalize, archival]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
depends_on: [infra_capture_and_devops_leftovers_2026_07_06]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  check_finalize_plan_coverage.py regression (2>baseline 1) surfaced while resolving cicd escalation agt-4d4f78
  (plan_health wall, PR #1478) — infra_capture_and_devops_leftovers_2026_07_06.md is `assigned_vm: planning` with 9
  total todos and no other plan gating on it.
---

# Infra capture wiring + devops leftovers — finalize

> **Machine-gated on `infra_capture_and_devops_leftovers_2026_07_06.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue the todo below until that plan's remaining dispatchable todo (the ASTER live connector) is
> done. Its other 4 open items are `BLOCKED-CREDENTIALS`/`BLOCKED-OPERATOR-DECISION` and are excluded from AO dispatch
> by convention — this finalize plan does not wait on those to be individually cleared before re-checking; it
> re-evaluates gate status whenever the ASTER item lands.

## Todos

- [x] ✅ [DOC] P2. **Reconcile + archive `infra_capture_and_devops_leftovers_2026_07_06.md`.** Once the ASTER live
      connector todo is `[x]`: (1) verify no other checkbox in the doc silently regressed (grep the doc for any `- [ ]`
      besides the 4 known `BLOCKED-*` items); (2) if the 4 `BLOCKED-*` items are still genuinely blocked
      (credentials/operator decision not yet resolved — re-check, don't assume), leave the doc `status: active` and do
      NOT archive — this finalize todo itself becomes the standing pointer, re-run it later; (3) if a `BLOCKED-*` item's
      gate has since cleared (credential granted / operator decision made), spin it into a new explicit dispatchable
      todo (either here or a small follow-up plan) rather than silently leaving it stale; (4) only once every todo in
      the parent doc is genuinely `[x]` or explicitly re-confirmed still-blocked, run the standard 6-step archival
      ritual on the parent (migrate any DEFERRED → banner → codex-alignment check → update any referrer paths
      corpus-wide → clear lock). **Done when**: the parent doc's checkbox state matches reality and it is either
      archived (if fully resolved) or left `active` with an explicit note that the remaining items are still genuinely
      blocked as of the re-check date. — **🟡 GATE NOT ACTUALLY MET, checked 2026-07-25T04:52Z (slot 2)**: dispatched
      despite the parent's ASTER live connector todo still reading `- [ ] 🚧 BLOCKED-PREREQUISITES`, not `[x]` (this
      finalize todo's own text is explicit: "Once the ASTER live connector todo is `[x]`" — it is not). Re-read the
      parent's own note on that todo: BOTH hard prereqs it names (cefi-007 enumerator start_date support; UAC
      `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` book_snapshot_5/liquidations) are recorded as landed as of 2026-07-07, but
      the note explicitly says "the connector launch + `live_aster` row-landing verification itself was NOT re-checked
      here and the checkbox is NOT flipped on that basis alone." So the real remaining work is on the PARENT plan
      (actually register+launch `aster_book_liq_ws.py` + verify `live_aster` rows land), not on this finalize plan — and
      that is a substantive `[DATA]`-craft launch/verify task, not this `[DOC]` archival task. Not completable this AO
      turn as dispatched; released without touching the parent doc (didn't want to rush a real VM launch as a rushed
      tail-end action). A future dispatch of the PARENT's own ASTER todo should do the actual launch+verify; only then
      does this finalize todo's gate genuinely clear. — **🟡 RE-CONFIRMED STILL NOT MET, checked 2026-07-25 (slot 3)**:
      same finding as the 04:52Z slot-2 check above — parent's ASTER todo still reads `- [ ] 🚧 BLOCKED-PREREQUISITES`,
      not `[x]`. Traced WHY this keeps getting dispatched despite the gate: `_NON_DISPATCHABLE_RE` in
      `agent-orchestrator/server/regen_backlog_from_plan.py` matches the broad `BLOCKED-[A-Z]` pattern, which also
      catches `BLOCKED-PREREQUISITES` (not just the intended CREDENTIALS/OPERATOR-DECISION/BILLING/UPSTREAM-OUTAGE/
      PLAYWRIGHT/JURISDICTION closed set) — so the ASTER todo has NEVER been ingested as a backlog task (confirmed via
      `GET /api/backlog`: only this finalize task appears for the whole plan family) and `gate_on_depends`'s upstream
      "open todos" check reads the parent as fully clear. This is a dispatcher bug, not a data problem — filed as
      `issues/blocked_prerequisites_marker_excluded_from_dispatch_and_gate_2026_07_25.md` with a concrete regex fix +
      regression test todo, plus a spun-out todo for the actual ASTER connector launch+verify once the regex is fixed.
      Released again without touching the parent doc; this finalize todo should stop re-dispatching once the linked
      issue's fix lands and the ASTER todo becomes a genuinely trackable backlog task. — **🟡 RE-CONFIRMED STILL NOT
      MET, checked 2026-07-25 (slot 4)**: 3rd identical dispatch, same day. Verified via `GET /api/backlog` that the
      regex fix (`blocked_prerequisites_marker_excluded_from_dispatch_and_gate-001`, queued) has not landed yet — the
      parent's ASTER todo is still absent from the backlog and the parent still reads
      `- [ ] 🚧     BLOCKED-PREREQUISITES`. No new diagnosis needed; releasing via `/skip-current-task` with
      `reason_code: GATED` this time (rather than a plain release) so the fleet-scoped dispatch cooldown
      (`ao_dispatch_cooldown_and_park_2026_07_20`) actually suppresses re-dispatch to any slot for a window, instead of
      immediately re-offering this same not-yet-actionable task to the next slot that boots. — **✅ GATE NOW GENUINELY
      MET, checked 2026-07-25 (slot 9)**: the parent's ASTER item no longer reads `BLOCKED-PREREQUISITES` — it was
      re-resolved today to `- [ ] 🚧 BLOCKED-OPERATOR-DECISION` (`BLK-4f52080e`, main: HOLD, do not launch, pending the
      still-active 2026-07-14 CeFi live-capture cost-control freeze `BLK-55d45a68`). `BLOCKED-OPERATOR-DECISION` IS in
      `_NON_DISPATCHABLE_RE`'s intended closed set, so the parent genuinely has zero open non-blocked todos now — not a
      dispatcher-bug artifact this time. Did the full reconciliation per the todo's own 4-step procedure: (1) grepped
      the parent for every `- [ ]` — found exactly 5 (ASTER + the 4 known credential/operator items), no silent
      regression. (2)/(3) Re-verified each of the 5, not assumed: **ASTER** — still genuinely blocked (operator hold
      today, cited above). **pyth oracle `collect-oracle-prices`** — its `BLOCKED-CREDENTIALS` premise was STALE: the
      launcher scaffold already exists twice (`launch-mtds-pyth-archive-backfill-vm.sh` +
      `launch-mtds-pyth-lst-backfill-vm.sh`, both `VM_OPERATION=collect-oracle-prices`), the Pyth Hermes endpoint needs
      no auth (`oracle_prices_handler.py` docstring: "Free, no auth required"), and the data_type is actively being
      backfilled under `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part5_2026_07_24.md` — flipped `[x]`
      on the parent with citation rather than spinning a duplicate todo, since the real work is already tracked
      elsewhere. **MANTLE gas-fees RPC**, **Live ODDS quota**, **rate-limit probe VM** — all re-confirmed still
      genuinely blocked as of today (evidence + citations added inline on the parent, most recently restated 2026-07-24
      in sibling plans, no grant/sanction found). (4) Net: 1 of 5 parent items now `[x]`, 4 of 5 remain genuinely
      blocked (not silently stale) — so per the todo's own step (2), the parent stays `status: active`, NOT archived;
      the 6-step archival ritual does not fire yet. Also found + fixed an adjacent issue while in the doc: an accidental
      duplicate finalize plan for the same parent
      (`infra_capture_and_devops_leftovers_2026_07_06_finalize_2026_07_25.md`, `status: draft`, never dispatched) —
      marked `status: superseded` + `superseded_by:` pointing here so a future doc-health sweep doesn't reactivate two
      finalize plans for one parent. Evidence: `unified-trading-pm@<pending-sha>`. Done per this todo's own
      done-definition: parent checkbox state now matches reality and is explicitly left `active` with a dated re-check
      note — this finalize todo does not need to re-run until one of the 4 remaining blockers clears.
