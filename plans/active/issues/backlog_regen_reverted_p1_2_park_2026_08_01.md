---
doc_type: issue
title:
  "Backlog regen appeared to revert a manual park on `live_event_log_warm_sink_recovery_and_cold_compaction-011`
  (P1.2) — task re-dispatched to slot 12 despite unmet preconditions; traced and CLOSED as a one-time process gap,
  NOT a recurrence of `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` (see summary)"
summary: >-
  On 2026-07-31 (~22:20Z) main answered BLK-085fef5e (Option A) and manually parked backlog task
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` ([DATA] P1.2 in
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`) after 3 workers (slot-14, slot-8, slot-6) had
  already churned on it with zero possible progress — set `priority: 999` + `priority_override: true` + a false gating
  prerequisite `p1-2-preconditions-met`, per the plan's own Progress Log. At `2026-08-01T00:55:27Z` (~2h35m later) the
  task was dispatched to slot 12 anyway: live `GET /api/backlog` shows `priority: 20` (the plan-derived value, not 999)
  and the raw `data/config/backlog.yaml` entry shows `prereqs.prerequisites: []` (empty — the `p1-2-preconditions-met`
  attachment is gone). Both preconditions remain unmet regardless (only ~3h45m elapsed since the P1.1 redeploy
  `2026-07-31T21:14Z`, vs the required 24h; no paper run confirmed per the sibling issue doc below), so this is a live
  recurrence of the exact bug class `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` was supposed to have fixed
  (`agent-orchestrator@8dd5763`) — the fix either doesn't cover this code path or has regressed.
  **CORRECTED (this doc's own later investigation, todo 2, DONE)**: determined to be a one-time process gap (an
  intended manual-park edit that never actually happened), NOT a code regression of
  `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` — the title's "recurrence of..." framing above is disproven;
  see the Todos section for the resolved finding.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-04 (ag-closeout-audit ao tranche run) -- was [cross-cutting]. Genuinely AO backlog/park
  # mechanism content (agent-orchestrator's own regen/dispatch code), not cross-AG.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, regression, park, prerequisites, plan-regen, fleet-churn]
related:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
  ]
created: "2026-08-01"
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
drift_direction: none
assigned_role: infra
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found 2026-08-01 (slot 12) on /boot dispatch: task returned with `dispatch_reason: "resume"` / `already_in_progress:
  true` for a todo the plan's own Progress Log records as parked by main just ~2h35m earlier. Cross-checked `GET
  /api/backlog` (priority=20) and the live `data/config/backlog.yaml` entry (read-only, root `agent-orchestrator` clone)
  directly (`prereqs.prerequisites: []`), and independently re-verified the time-gate precondition is still unmet
  (~3h45m of the required 24h elapsed).
context_scope: [/plans/archive/issues/p1_2_backlog_hand_park_did_not_persist_2026_07_31.md, /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md, /plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md, agent-orchestrator/server/regen_backlog_from_plan.py, agents/RULES.md]
---

# Backlog regen reverted the manual park on P1.2 — recurrence of a previously-fixed bug class

## What I found

`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s `[DATA] P1.2` todo (the
`paper(W)==batch-rerun(W)` determinism recheck for BINANCE-FUTURES/ASTER/OKX-FUTURES) was manually parked by main on
2026-07-31 after this exact scenario had already churned through 3 workers in ~90 minutes with zero possible progress
(both preconditions — a 24h accumulation window since the `2026-07-31T21:14Z` P1.1 redeploy, and an active paper run
trading these 3 venues — were, and remain, unmet). Main's answer to `/blocked` (**BLK-085fef5e**, logged in the plan's
Progress Log) was Option A: set `priority: 999` + `priority_override: true` on backlog task
`live_event_log_warm_sink_recovery_and_cold_compaction-011`, plus a false gating prerequisite `p1-2-preconditions-met`,
so the fleet stops churning on it until both preconditions are genuinely met.

At `2026-08-01T00:55:27Z` this worker (slot 12) received this exact task on `/boot` (`dispatch_reason: "resume"`,
`already_in_progress: true`). Live-checked:

- `GET http://localhost:8765/api/backlog` → the task's entry shows `"priority": 20`, not `999`.
- The live `data/config/backlog.yaml` (read-only — root `agent-orchestrator` clone, the process cwd of the actual
  running `uvicorn server.server:app` — PID confirmed via `/proc/<pid>/cwd`) entry for
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` shows `prereqs.prerequisites: []` (empty) — the
  `p1-2-preconditions-met` attachment is gone.
- Independently re-verified both underlying preconditions are STILL unmet regardless of the park state: only ~3h45m have
  elapsed since the `2026-07-31T21:14Z` P1.1 redeploy (need 24h, clears ~`2026-08-01T21:14Z`), and no paper run trading
  these venues has been confirmed to exist (see the sibling issue doc, which found this may be a standing gap, not just
  a timing one).

This is a live recurrence of `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` — the exact bug class
`agent-orchestrator@8dd5763` was supposed to have fixed (hand-tuned `priority_override` + `prereqs.prerequisites`
silently dropped by a regen tick). Either that fix does not cover whatever regen code path ran between
`~2026-07-31T22:20Z` (when main applied the park) and `2026-08-01T00:55:27Z` (this dispatch), or it has regressed.

## Why it matters

Without a fix, EVERY worker who gets dispatched this task will re-discover the exact same two unsatisfiable
preconditions main already ruled on — pure fleet churn, the precise failure mode the original park was created to stop.
This is now the 4th worker touched by this todo in <24h (slot-14, slot-8, slot-6, now slot-12) purely because the park
did not stick, and it will keep recurring every regen tick until the underlying regen-code gap is fixed, not just
re-applied by hand again.

## Recommended decision

- [x] ✅ [OPERATOR] P0. Re-apply the park on backlog task `live_event_log_warm_sink_recovery_and_cold_compaction-011`:
      `priority: 999` + `priority_override: true` + `prereqs.prerequisites: [p1-2-preconditions-met]` in
      `agent-orchestrator/data/config/backlog.yaml` (root clone — requires main/operator-level write access; a
      dispatched worker's slot-scope rules forbid editing root clones), and confirm
      `POST /api/prerequisites/p1-2-preconditions-met {"value": false, "set_by": "main"}` is (re-)set false. Verify it
      actually stuck after the next `PlanRegenLoop` tick / `POST /api/backlog/regen` (not just `/reload`), per the exact
      verification recipe in `unified-trading-pm/agents/RULES.md` § 4. — **ALREADY APPLIED — closed 2026-08-06 by
      operator ruling during `/plan-reconcile ao`.** The sibling doc
      `/plans/archive/issues/p1_2_backlog_hand_park_did_not_persist_2026_07_31.md:169` recorded the park as applied and
      holding on 2026-08-05 (slot 8) citing a live `/api/backlog` read
      (`priority: 999, status: queued, dispatched_to: null`); this doc's checkbox was simply never reconciled against
      it. This run's own read-only `check-ao-backlog-status.sh` pass confirmed task `-011` is
      `status=queued dispatched_to=None` (that script prints `tier`, not `priority`, so it neither confirms nor refutes
      the 999 override — the operator ruled to trust the sibling doc's direct read).
- [x] ✅ [AO] P1. **ALREADY ANSWERED (found 2026-08-04, `/ag-closeout-audit ao`) — cited, not re-derived.** Root-cause
      why the `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` fix (`agent-orchestrator@8dd5763`) did not prevent
      this reversion: `p1_2_backlog_hand_park_did_not_persist_2026_07_31.md` independently investigated this EXACT same
      incident (same task, same window) and confirmed via `journalctl -u orchestrator.service` that the only two API
      calls in the window were `POST /api/prerequisites/p1-2-preconditions-met` (sets the condition value only) and
      `POST /api/backlog/reload` (re-reads disk, never writes) — **the actual `backlog.yaml` file edit that sets
      `priority`/`priority_override`/`prereqs.prerequisites` was never performed at all.** A static read of
      `_reconcile_task_fields()` additionally confirmed `prereqs.prerequisites` has no revert code path, ruling out a
      `backlog_regen_drops_handtuned_prereqs`-class regression. **This is a one-time process gap (an intended edit that
      didn't happen), not a code defect** — no fix or regression test is warranted; the code path is sound. See that
      doc's own Progress Log for the full evidence trail.
- [ ] [SCRIPT] P2. Consider a standing assertion (hygiene sweep or a lightweight periodic check) that flags any backlog
      entry whose plan-todo text starts with "**⏸ PARKED" but whose live `priority` != 999 or `priority_override` !=
      true — this exact drift is otherwise silent until a worker happens to notice and file a doc like this one (repo:
      agent-orchestrator or unified-trading-pm, whichever owns the hygiene-sweep surface for this check).

## Progress Log

**na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: All 3 remaining open items are genuinely
judgment/operator-gated or touch live dispatch-critical-path machinery whose fix scope is not yet fully determined; none
are stale, duplicated elsewhere, or moot, so NA remains the correct home for the whole doc.

**na-eligibility-audit 2026-08-03 (reclassify pass)**: KEEP-NA, valid — **correction to the 2026-08-01 entry above: item
1 and item 2 are in fact substantially duplicated by a sibling doc, not "duplicated nowhere."**
`plans/archive/issues/p1_2_backlog_hand_park_did_not_persist_2026_07_31.md` (`assigned_vm: planning`, already
dispatched) investigates the SAME `BLK-085fef5e` park-does-not-persist incident on this SAME backlog task one dispatch
cycle earlier, and reached a conclusive root-cause via `journalctl` + a static read of `_reconcile_task_fields()`:
**this is NOT a `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`-class code regression** — the park was never
actually WRITTEN to `backlog.yaml` in the first place (only the prerequisite condition + a `/reload` were called, no
file edit), so item 2's "root-cause why the fix did not prevent this reversion / ship a fix + regression test" premise
(assuming a code-level revert) is likely moot — there is nothing in `regen_backlog_from_plan.py` that strips
`prereqs.prerequisites` from a still-current task (verified independently twice in that sibling doc). Item 1 ("re-apply
the park") duplicates that sibling doc's own still-open `[OPERATOR] P1` todo #3 verbatim (same task, same fix). **Not
reclassified** — the sibling is itself still open pending the same `[OPERATOR]` action, so this is a CONFLICT (duplicate
claim), not a stale/moot item to silently drop: whoever performs the sibling's `[OPERATOR]` re-park action resolves both
docs' item-1 asks in one edit, and should close item 2 here as NOT-A-REGRESSION per the sibling's evidence unless a
fresh read of the live `backlog.yaml`/orchestrator log at that time shows this occurrence's edit DID land and then got
reverted (a genuinely new, distinct finding the sibling doc did not have). Item 3 (a standing hygiene assertion for
parked-but-not-actually-999 drift) is NOT duplicated by the sibling and remains a distinct, genuinely-open ask.
`assigned_vm` unchanged (NA) — this is a citation/conflict finding, not a reclassification.

- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added
  `p1_2_backlog_hand_park_did_not_persist_2026_07_31.md` as the first entry: that sibling doc already reached a
  conclusive root-cause (this is NOT a `backlog_regen_drops_handtuned_prereqs`-class regression) and this doc's item 1
  duplicates its still-open `[OPERATOR]` todo verbatim — a worker must read it before acting here.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-verified against current state
  (only 2 open items now; item 2 was closed today by the same-day `/ag-closeout-audit ao` run, citing the sibling doc's
  root-cause, consistent with the 2026-08-03 marker's own prediction that item 2's premise was "likely moot"). Item 1
  ([OPERATOR] P0, re-apply the park) stays a genuine operator-only backlog.yaml write and remains a duplicate claim
  against `p1_2_backlog_hand_park_did_not_persist_2026_07_31.md`'s own still-open `[OPERATOR]` todo (also independently
  listed operator-gated by batch6). Item 3 ([SCRIPT] P2, "consider a standing assertion...") remains an unscoped design
  fork — repo ownership (agent-orchestrator vs. unified-trading-pm) and mechanism (hygiene sweep vs. periodic check)
  both undecided; also independently declined by batch6 as "an unscoped design fork." Not reclassified.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-affirmed. Sole open item ([SCRIPT] P2, standing park-drift
  hygiene assertion) remains an unscoped design fork (repo ownership + mechanism both undecided), matching the
  2026-08-04 verdict and batch6's independent same-day classification. No content drift since the last marker.

- **2026-08-09 (slot 20, data_engineering, cross-referencing new evidence — no reclassification, out of craft scope)**:
  Flagging fresh evidence relevant to this doc's still-open item 3 ([SCRIPT] P2, standing park-drift hygiene assertion).
  `/plans/active/issues/cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete_2026_08_08.md`'s Progress
  Log records the SAME `already_in_progress: true` / `dispatch_reason: "resume"` bypass pattern this doc investigates —
  but that task was parked via the sanctioned `POST /api/backlog/{task_id}/park` API (`auto_park.manual_park`), a
  DIFFERENT code path than the `backlog.yaml` hand-edit case this doc's item 2 already root-caused ("the park was never
  actually WRITTEN to disk"). It has now recurred 3 consecutive dispatches (slots 19→29→20) against a park that DID
  persist (`GET /api/backlog/parked` confirms `reason_code: "PARKED"` each time) — so whatever causes the `resume`
  bypass here is not explained by that prior root-cause. Not reclassifying this doc (still a genuine unscoped design
  fork per the last 3 audit passes) — leaving this as a pointer for whoever eventually scopes item 3, since it's now
  evidence the bug class spans both the hand-edit AND the API-park mechanisms.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open item ([SCRIPT] P2, standing park-drift hygiene assertion) remains an unscoped design fork
  (repo ownership agent-orchestrator-vs-unified-trading-pm AND mechanism hygiene-sweep-vs-periodic-check both
  undecided), matching every prior pass and batch6's independent same-day classification. New 2026-08-09 evidence
  (cross-referenced in this doc, not reclassifying) shows the bug class now spans both the hand-edit AND
  sanctioned-API-park mechanisms — widening the eventual fix's scope, not narrowing today's classification.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:086d99f24bbc2f5b]: KEEP-NA, valid — sole remaining item is an unscoped design fork (repo ownership + mechanism undecided), independently re-verified across 5 prior audit passes.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item (a standing park-drift hygiene assertion) remains an unscoped design fork (repo ownership + mechanism both undecided); unchanged since 2026-08-17.
