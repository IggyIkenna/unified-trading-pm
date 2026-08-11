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
last_updated: "2026-08-11"
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
context_scope:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /scripts/quality_gates/check_finalize_plan_coverage.py,
    /plans/active/task_template.md,
    /plans/archive/issues/finalize_plan_coverage_regression_2_plans_2026_07_25.md,
  ]
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

> **✅ ARCHIVED 2026-08-11 (slot 16, data_engineering) — parent fully resolved, coverage gate clean, both docs archived
> together.** All 9 parent checkboxes are now `[x]` (rate-limit probe RETIRED 2026-08-11, ASTER verified 2026-08-09,
> Live-ODDS resolved 2026-08-08, all prior items done by 2026-08-02). `check_finalize_plan_coverage.py` reads 0 violations
> at baseline 0 — the 2026-07-26 coverage-gate concern is resolved. This finalize plan served its purpose as the parent's
> standing re-check pointer across 4 reconciliation passes (2026-07-25 ×3, 2026-08-02, 2026-08-11); both docs now move to
> `/plans/archive/2026_08/` together, satisfying the original gate ("only once every todo in the parent doc is genuinely
> `[x]`"). All referrers updated corpus-wide — see the final Progress Log entry below.

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
      note — this finalize todo does not need to re-run until one of the 4 remaining blockers clears. — **🟡 RE-VERIFIED
      2026-07-26 — still correctly `[x]`; parent's 4 items still genuinely blocked (no change found); THIS FINALIZE PLAN
      MUST NOT BE ARCHIVED YET.** Full task-description re-check confirmed nothing regressed and no blocker cleared (see
      the doc-level banner above for citations). Separately discovered: archiving this doc right now (moving it to
      `plans/archive/`) would itself regress `scripts/quality_gates/check_finalize_plan_coverage.py` from baseline 1 to
      2 — empirically verified by temporarily removing the file from `plans/active/` and re-running the checker, then
      restoring it — because this doc is currently the parent's ONLY `depends_on`+`gate_on_depends: true` coverage and
      the parent (9 total todos) is not exempt via the single-todo carve-out. That is a hard `quality-gates.sh`
      post-gate failure (`exit 1`), not a soft warning, and would block every future `unified-trading-pm` plan-doc
      commit. So per this task's own done-when clause ("archived if fully resolved, or left `active` with an explicit
      note the remaining items are still genuinely blocked") the correct outcome this cycle is: leave this doc
      `status: active`, un-archived, in `plans/active/`, with this note as the explicit record of why. No files moved,
      no referrer paths touched (the doc did not move). Re-run only once the parent's remaining 4 items clear or the
      coverage-gate design changes.

- [x] ✅ [DOC] P2. **Reconciliation COMPLETE 2026-08-11 (slot 16, data_engineering) — ALL 9 parent checkboxes now `[x]`,
      archival executed.** All 3 remaining items from the 2026-08-02 check have since resolved: **rate-limit-probe VM** —
      RETIRED 2026-08-11 (operator): superseded, closing as won't-do (the real solution already shipped via Tardis
      1-concurrent-VM hard cap + boot-disk sizing; see
      `/plans/active/issues/rate_limit_probe_vm_authorized_no_design_spec_2026_08_09.md` and parent line 324).
      **Live-ODDS second-source scaffold** — RESOLVED 2026-08-08 (slot 10): api_football live odds was STRUCK per operator
      decision B (conflicts with 2026-06-24 wipe ruling); the live odds_api VM confirmed healthy (running, continuous
      `ManifestWriter` shard updates through 2026-08-08T17:23Z). See parent line 305.
      **ASTER live-data-landing verification** — DONE 2026-08-09 (slot 6): SSH'd the current consolidated VM, confirmed
      both `live-aster-book-snapshot-5.log` and `live-aster-liquidations.log` actively writing `ManifestWriter` shard
      updates; cross-checked warm event-log tier shows objects timestamped within minutes. See parent line 79.
      **Parent checkbox count: 9/9 done** (up from 6/9 at the 2026-08-02 check). **`check_finalize_plan_coverage.py`
      baseline now 0** (the `deployment_registry_firestore_p0_unblock_2026_07_14.md` violation that blocked archival in
      2026-07-26 has since resolved). Since the parent is fully done AND the coverage gate is clean, the 6-step archival
      ritual fires on BOTH this finalize plan and its parent together. Archiving to
      `/plans/archive/2026_08/` this same session — see Progress Log below for the full 6-step evidence.
      — `unified-trading-pm@<pending-sha>`

## Progress Log

- **2026-08-11 (slot 16, data_engineering) — FINAL RECONCILIATION: ALL 9 PARENT CHECKBOXES `[x]`, ARCHIVAL EXECUTED.**
  Parent state: every checkbox now genuinely resolved. The 3 items still open at the 2026-08-02 check (rate-limit-probe,
  Live-ODDS second-source, ASTER live-data) have all since cleared — see todo 2's checkbox annotation above for per-item
  dates + evidence. `check_finalize_plan_coverage.py` baseline = 0 (the `deployment_registry_firestore_p0_unblock`
  violation that blocked archival in 2026-07-26 has since resolved). **6-step archival ritual run on both docs**: (1) no
  DEFERRED items to migrate; (2) archival banners added to both; (3) codex check — no new contracts established, purely
  wiring/verification work; (4) CLAUDE.md unchanged; (5) referrer paths updated corpus-wide (INDEX.md entries removed,
  `instruments_master.md` links repointed, `cross_cutting_consolidated_closeout`, `instruments_completion_tracker`,
  `cross_cutting_satellite_ao_dispatch_batch1_finalize`, and issue docs with `/plans/active/` path references all
  repointed to `/plans/archive/2026_08/`); (6) `git mv` both docs. This finalize plan's 2-year, 4-pass standing watch is
  closed.
  originally-named 4 `BLOCKED-*` items, MANTLE paid-RPC fully cleared and the Live-ODDS quota decision-component cleared
  (2 of 4 blocker-framings resolved) — flipped/updated on the parent with citations (checkbox count 5/9 → 6/9). **3
  checkboxes remain open** (not 2): rate-limit-probe VM sanction (unchanged, still gated), Live-ODDS second-source
  scaffold (no longer decision-gated, but still unwired — plain execution todo now, owned by the sibling sports plan),
  and ASTER live-data-landing verification (also logged a new finding there re: 3 days of zero rows + an unexplained VM
  replacement). Archival ritual NOT run; both docs stay `active`. Full detail on this todo's own checkbox above and the
  parent's matching Progress Log entry.
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (6 entries).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
