---
doc_type: issue
title: "47 open todos in active AO plans are silently absent from the backlog — nothing reports the gap"
summary: >-
  MEASURED 2026-08-08 across every assigned_vm: planning doc in plans/active/ (+ issues/): 551 open todos on disk, 504
  parsed into the backlog by regen's own _parse_open_todos — 47 todos across 37 docs will NEVER dispatch, and no gate,
  sweep or dashboard reports it. 14 of the 37 parse to ZERO dispatchable todos, so the doc is an active AO plan that AO
  will never touch at all. Some of the 47 are legitimately blocked (a live BLOCKED-<token> is a deliberate
  non-dispatch); the defect is that intentional and accidental are indistinguishable from outside the parser. Found
  while verifying the sports taxonomy chain: its P3 Betfair todo was dropped because the sentence FORBIDDING the marker
  ("Do NOT mark this BLOCKED-CREDENTIALS") contained the marker — the todo's own text asserted it was fully
  AO-completable with no operator step.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, plan-hygiene, dispatch, false-progress, findings-triage, quality-gates]
related:
  [
    /plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md,
    /plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
  ]
created: 2026-08-08
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
source: "slot-3 interactive, 2026-08-08 — verifying that the 8 sports taxonomy plans were fully AO-dispatched"
depends_on: []
---

# Silently non-dispatchable todos have no visibility gate

## What I found

`_parse_open_todos` (`agent-orchestrator/server/regen_backlog_from_plan.py`) deliberately excludes a todo whose
continuation block asserts a live `BLOCKED-<token>` state or a permanent stretch/deferred marker — correct behaviour on
its own terms: a worker cannot work a todo that waits on a human. The excluded todo "stays visible in the plan, just not
in the backlog" (its docstring).

The problem is the second half of that sentence. **Nothing anywhere reports the delta.** The plan renders a live
`- [ ]`. `regenerate_active_plan_inventory.py` counts it. The plan's own progress fraction counts it. The operator
reading the plan sees tracked work. AO will never dispatch it, and no gate, hygiene sweep, or dashboard says so.

MEASURED 2026-08-08, running regen's OWN parser against every `assigned_vm: planning` doc in `plans/active/` and
`plans/active/issues/`:

- **551** open todos on disk
- **504** parsed into the backlog
- **47 silently dropped, across 37 docs**
- **14 of those 37 parse to ZERO** — an `active`, `assigned_vm: planning` doc that AO will never touch at all

Worst offenders: `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` (1 of 6 dispatchable),
`prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (0 of 3), `ci_satellite_ao_dispatch_batch6_2026_08_08.md` (9 of
11), `infra_capture_and_devops_leftovers_2026_07_06.md` (1 of 3), `sports_closeout_track_s2_foldin_2026_07_25.md` (3 of
5).

**Not every one of the 47 is a bug.** A genuinely credential-blocked todo SHOULD be excluded. The defect is that from
outside the parser, deliberate and accidental exclusion are indistinguishable — so the accidental ones survive
indefinitely.

## The trigger shape that found this

`/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`'s Betfair Exchange scaffold todo was authored 2026-08-08 with
text explicitly stating it was **"Fully AO-completable with no operator step"**, buildable **"credential-free"**, and
ending: _"Do NOT mark this `BLOCKED-CREDENTIALS` — the credential ask is a separate, already-tracked item and must not
gate the scaffold."_ That final sentence made the todo permanently non-dispatchable: `_has_live_blocked_token` scans the
whole block, and "Do NOT mark this" is not one of the resolution prefixes `_STALE_MARKER_PREFIX_RE` recognises (`was` /
`no longer` / `retagged from` / `previously`). The todo never entered the backlog from authoring until it was rewritten
2026-08-08 (`unified-trading-pm@a134a45948`), verified before/after with regen's real parser (14/15 -> 15/15).

This is the **fourth** distinct trigger shape for the same underlying bug class, after
`/plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` (27 todos across 21 files,
resolution note restating the old marker),
`/plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`, and
`defi_batch8_finalize_gate_bypass_missing_upstream_task_2026_08_02.md` (marker-then-resolution word order). Each was
fixed by widening the regex's escape hatches. **Widening the regex has not converged in four attempts** — the class
needs a detector, not a fifth prefix.

## Why it matters

This is silent false progress at corpus scale, and it is invisible in exactly the direction that matters: a plan looks
alive and tracked while its work is unreachable. The 14 zero-dispatchable docs are the acute case — they consume plan
inventory, satisfy "is this tracked?" checks, and produce nothing. It also defeats `gate_on_depends`: a downstream plan
gated on an upstream whose remaining todos are all silently excluded will read the upstream as finished-and-pruned (see
`_wire_gate_on_depends_prereqs`' own ambiguity note) and false-open.

## Recommended decision

- [x] ✅ [SCRIPT] P1. **Add a QG gate that reports the disk-vs-backlog todo delta per AO-dispatched doc, and ratchet it
      down.** Import regen's real `_parse_open_todos` (never a re-implemented regex — the whole point is that the parser
      IS the oracle) and compare, per doc, against the count of `^- [ ]` lines. For every delta, require the plan to
      DECLARE the exclusion: an excluded todo must carry an explicit `[BLOCKED]`-style tag or a stated blocked-on line,
      so a deliberate hold reads as deliberate and an accidental one fails the gate. Baseline at the measured 47 and
      ratchet DOWN — do not widen `_STALE_MARKER_PREFIX_RE` again as the fix; four successive widenings (2026-07-28,
      07-29, 08-02, 08-08) have not converged, because the failure is that exclusion is unreported, not that the regex
      is too narrow. Also emit the 14 zero-dispatchable docs as their own louder finding: an `active`,
      `assigned_vm: planning` doc with zero dispatchable todos is either mis-tagged or finished, never correct as-is.
      **Done when**: the gate is wired into `scripts/quality-gates.sh` with a baseline YAML, its own unit test covering
      the four known trigger shapes, and a MEASURED report of the 47 split into declared-intentional vs accidental —
      with the accidental ones either fixed or filed. Repo: unified-trading-pm (gate), agent-orchestrator (parser import
      path only, no parser change required). **Fold in while you are in that file** (found 2026-08-08, same session, too
      small for its own doc): `agent-orchestrator/server/server.py:239` comments the plan-regen loop as running "every
      6h", but `PlanRegenLoop` is constructed with no `interval_seconds` so it takes
      `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS = 1800` (30 min) unless `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` overrides
      it on the VM. Read the VM's live env, then correct the comment to the real value — a wrong cadence in the comment
      directly misleads anyone reasoning about how long a plan edit takes to reach the backlog, which is this issue's
      whole subject.

## Progress Log

- **2026-08-08 (slot 3, interactive)** — Filed. Measured with regen's own `_parse_open_todos` against the live
  `plans/active/` corpus, not a re-implemented regex, so the numbers are the parser's own verdict. The sports P3 Betfair
  todo was fixed in the same session and re-verified 15/15; the other 46 are untouched and deliberately left for the
  gate to classify rather than hand-triaged now — hand-triage without a gate is what let the previous three fixes
  regress. Filed as a NEW doc rather than folded into
  `/plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` because that doc is
  `assigned_vm: NA` (human-owned) and folding a dispatchable todo into it would have made this undispatchable too — the
  exact failure mode being reported. Kept to a single open todo so the finalize-coverage single-todo carve-out applies.

- **2026-08-08 (slot 21, infra)** — ✅ Shipped. `agent-orchestrator/server/dispatch_visibility_report.py` (new, additive
  — imports `_parse_open_todos`/`_plan_contributes_briefs` from `regen_backlog_from_plan.py` unchanged, no parser
  change) walks every `assigned_vm: planning` doc and diffs the real parser's dispatchable set against the raw `- [ ]`
  count, classifying every excluded todo `declared` (a live BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker that opens
  its own physical line) vs `accidental` (the marker is merely present in a longer sentence — the Betfair shape, and the
  class four prior regex widenings never converged on).
  `unified-trading-pm/scripts/quality_gates/ check_ao_dispatch_visibility_gate.py` shells out to it
  (agent-orchestrator's own `.venv`, since this repo's environment lacks its pydantic et al. deps) and ratchets two axes
  against `ao_dispatch_visibility_baseline.yaml`. Wired into `scripts/quality-gates.sh` (guarded on `WORKSPACE_ROOT`,
  same no-op-without-siblings convention as `check_repo_docs_ssot.py`). Unit tests:
  `agent-orchestrator/tests/test_dispatch_visibility_report.py` covers all four known trigger shapes (2 already-fixed
  stale-marker shapes stay zero-delta; BLOCKED-PREREQUISITES documented as a different, separately-tracked bug direction
  outside this gate's scope; the Betfair shape reproduces excluded+accidental) plus declared-marker positive controls
  and the zero-dispatchable-doc case (8 tests, all green);
  `unified-trading-pm/scripts/quality_gates/test_check_ao_dispatch_visibility_gate.py` covers the ratchet/summary
  arithmetic (4 tests, all green, no sibling-repo dependency). MEASURED run against the live corpus (today, post the
  Betfair fix and ~1 month of further plan authoring): 246 AO-dispatched docs, 642 disk-open / 597 backlog-open, 45
  excluded (18 declared / 27 accidental), 24 zero-dispatchable docs — baseline seeded at 27/24. The fold-in
  (`server.py:239` cadence comment) was already corrected in a prior session (verified live: the comment now correctly
  states 30min/`ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS`, not "every 6h"). The 27 accidental exclusions are filed, not
  hand-fixed here (same precedent this issue's own filing set) —
  `/plans/archive/2026_08/issues/ao_dispatch_visibility_gate_accidental_exclusions_2026_08_08.md` (archived 2026-08-09,
  all 27 todos resolved), one todo per doc. Evidence: agent-orchestrator@d4f4947d0 (report module + tests),
  unified-trading-pm@fb70812a8 (gate + baseline + quality-gates.sh wiring, both landed on live-defi-rollout).
