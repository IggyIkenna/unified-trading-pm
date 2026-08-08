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

- [ ] [SCRIPT] P1. **Add a QG gate that reports the disk-vs-backlog todo delta per AO-dispatched doc, and
      ratchet it down.** PM-side gate code fully built, tested, wired, and PUSHED: unified-trading-pm@bcd6aaaa5. The
      one remaining piece — `agent-orchestrator/scripts/plan_hygiene/dump_dispatchable_todos.py` (agent-orchestrator@
      3d4abba, committed but NOT YET PUSHED) — is blocked behind a pre-existing, unrelated QG red on
      `live-defi-rollout` (`worker_liveness`/`context_lifecycle` test failures, verified not caused by this change;
      see `/plans/active/issues/ao_worker_liveness_context_lifecycle_qg_red_2026_08_08.md`, repo-blocker declared).
      Without this file present, `check_ao_dispatch_gap.py` degrades to a silent no-op (its own designed fallback
      when the AO sibling/wrapper is absent) — so the gate is NOT yet actually enforcing anything in production.
      Leave this checkbox open until agent-orchestrator@3d4abba lands via quickmerge once the repo is green again;
      re-verify the gate fires for real (not the no-op path) before flipping to done. Shipped
      `scripts/quality_gates/check_ao_dispatch_gap.py` (PM) which imports regen's REAL `_parse_open_todos` via a
      subprocess into agent-orchestrator's own `.venv` (new
      `agent-orchestrator/scripts/plan_hygiene/dump_dispatchable_todos.py` wrapper — no parser change) rather than
      re-implementing the marker regex a fifth time. Per-todo (not gap-count) classification: an excluded disk todo is
      DECLARED if its own continuation block carries a
      `BLOCKED-<token>`/`[OPERATOR]`/`blocked on`/`DEFERRED-BY-DESIGN`/`stretch, optional` marker not itself disclaimed
      by a nearby negation phrase (the sports-Betfair "Do NOT mark this BLOCKED-CREDENTIALS" shape — an 80-char
      proximity window, not a whole-block search, after a whole-block version false-positived on an unrelated "not
      blocking paper" phrase in a real corpus doc), else ACCIDENTAL. Wired into `scripts/quality-gates.sh` (guarded on
      `WORKSPACE_ROOT`, same no-op-when-siblings-absent shape as the repo-docs-ssot gate). 7 unit tests in
      `test_check_ao_dispatch_gap.py` cover all 4 known trigger shapes (resolved retag, unrecognized-token variant,
      marker-then-resolution word order, negated-marker mention) plus the description-extraction parity and a
      live-corpus smoke test — all pass. **MEASURED live run (2026-08-08, 287 assigned_vm:planning docs checked — corpus
      has moved since this doc's original 551/504/47/37/14 snapshot earlier the same day, expected on a fast-moving
      fleet)**: **0 accidental** exclusions, **24 zero-dispatchable docs**. Baseline seeded at
      `max_accidental_exclusions: 0` / `max_zero_dispatchable_docs: 24` (`ao_dispatch_gap_baseline.yaml`) — a future
      accidental exclusion now fails the gate immediately rather than hiding indefinitely. Zero accidental means every
      currently-excluded todo in the live corpus is genuinely declared (verified by direct read on one spot-check,
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s 3/3 — all live
      BLOCKED-OPERATOR-DECISION/BLOCKED-CREDENTIALS/DEFERRED-BY-DESIGN markers), consistent with the four prior
      regex-widening fixes plus this same doc's own same-day sports-Betfair rewrite having already closed the accidental
      cases that existed. The 24 zero-dispatchable docs are the "louder finding" this todo asked for — filed as
      `/plans/active/issues/ao_zero_dispatchable_planning_docs_triage_2026_08_08.md` (one bounded triage todo per
      findings-closure convention, RULES.md §4.5) rather than hand-triaged here, since determining
      mis-tagged-vs-finished for 24 docs is real per-doc judgment work outside this task's scope. The `server.py:239`
      comment fold-in was already fixed by another worker earlier the same day (confirmed current text at
      `server/server.py:245-248` cites the real 300s production override, not the stale "every 6h") — no action needed.

## Progress Log

- **2026-08-08 (slot 3, interactive)** — Filed. Measured with regen's own `_parse_open_todos` against the live
  `plans/active/` corpus, not a re-implemented regex, so the numbers are the parser's own verdict. The sports P3 Betfair
  todo was fixed in the same session and re-verified 15/15; the other 46 are untouched and deliberately left for the
  gate to classify rather than hand-triaged now — hand-triage without a gate is what let the previous three fixes
  regress. Filed as a NEW doc rather than folded into
  `/plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` because that doc is
  `assigned_vm: NA` (human-owned) and folding a dispatchable todo into it would have made this undispatchable too — the
  exact failure mode being reported. Kept to a single open todo so the finalize-coverage single-todo carve-out applies.
- **2026-08-08 (slot-24)** — Built, tested, and pushed the PM-side gate (see checkbox above for full detail):
  unified-trading-pm@bcd6aaaa5. The AO-side wrapper (agent-orchestrator@3d4abba) is committed but blocked from
  shipping by a pre-existing, unrelated QG red on that repo (`/plans/active/issues/
  ao_worker_liveness_context_lifecycle_qg_red_2026_08_08.md`) — without it the gate silently no-ops rather than
  actually enforcing, so the checkbox stays open and the doc stays active (not archived) until AO ships and the gate
  is re-verified live. Not a blocked-question — this is a wait-on-a-shared-repo-fix, handled via the repo-blocker
  mechanism (RULES.md §4b), no operator input needed.
