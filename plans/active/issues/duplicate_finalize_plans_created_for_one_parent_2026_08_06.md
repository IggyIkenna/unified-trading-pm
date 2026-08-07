---
doc_type: issue
title:
  "Two gated finalize plans were created for the SAME parent on the same day, each justified by 'no companion gated
  finalize plan exists' — nothing makes the finalize-plan remediation path idempotent, so both would have gone
  dispatchable on one tick and raced the identical 6-step archival"
summary: >-
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md` and `..._finalize_2026_07_31.md` (note
  the near-duplicate filename) were both created 2026-07-31 against the same parent, both carrying `depends_on:
  [live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31]`, `gate_on_depends: true` and `status: active`.
  Once the parent's last todos cleared, BOTH became dispatchable on the same tick and would have run the identical
  6-step archival — a file move plus a corpus-wide referrer fixup — concurrently against one target. De-raced 2026-08-06
  (BLK-5eeacb63, operator-ruled): the date-suffixed one is now `status: superseded` with a banner, after its `[REVIEW]`
  evidence-verification todo — which the survivor did NOT carry — was ported across so nothing was dropped. This issue
  tracks only the REMAINING root cause. Note the checker itself is NOT at fault, contrary to the first reading:
  `check_finalize_plan_coverage.py::_gated_slugs` correctly collects every slug named in some other plan's `depends_on`
  + `gate_on_depends: true`, so a parent that already has a finalize plan is not re-flagged. The gap is in the
  REMEDIATION path — whatever creates a finalize plan in response to a flagged violation has no idempotency guard and no
  create-time collision check, so two responders (plausibly two agents acting on the same violation the same day —
  same-day creation is verified, concurrency is inferred, not proven) each wrote a plan whose own stated justification
  was already false when written.
status: open
nature: issue
asset_group: [cross-cutting]
scope: [engineer]
stage: [meta]
repos: [unified-trading-pm]
tags: [plan-hygiene, quality-gates, finalize-plans, idempotency, archival]
related:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P3
parent_epic: orchestrator_master
source:
  "daily plan-reconcile (slot 2, agt-4fdce1) raised it as BLK-5eeacb63; answered + de-raced by the operator's
  interactive session 2026-08-06"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Duplicate finalize plans for one parent — the remediation path is not idempotent

## Todos

- [ ] [INFRA] P3. **Make finalize-plan creation idempotent at the point of creation.** Before writing a new
      `<parent>_finalize*.md`, re-derive `check_finalize_plan_coverage.py::_gated_slugs()` over the CURRENT corpus and
      refuse if the parent is already gated by an existing finalize plan — regardless of that plan's filename shape. The
      two colliding files differ only by a redundant `_2026_07_31` suffix, so any guard keyed on the exact expected
      filename would have missed this; key it on the `depends_on` relationship, which is the real contract.

- [ ] [INFRA] P3. **Add a corpus-wide duplicate-gate detector to the hygiene sweep.** Flag any parent slug named in the
      `depends_on` of MORE THAN ONE `gate_on_depends: true` plan. This is cheap (the sweep already parses every plan's
      frontmatter for `_gated_slugs`), it catches the collision at rest instead of at dispatch time, and it would have
      surfaced this pair on 2026-07-31 rather than a week later via a worker's blocked question. Report it the same way
      the orphan count is reported — a non-zero count is review-blocking.

- [ ] [DOC] P3. **Sweep the corpus once for other duplicate gates.** Run the detector from todo 2 over `plans/active/`
      and de-race any other parent found with >1 gated finalize plan, using the same procedure applied here: port any
      todo unique to the loser into the survivor FIRST, then set `superseded_by`/`supersedes` + a dated banner. Report
      the count found — if it is zero, this pair was a one-off and todo 1's guard is belt-and-braces.

## Progress Log

### 2026-08-06 — filed after de-racing the live pair

The immediate race is resolved (see the survivor's `supersedes:` and the loser's banner). Verified before superseding
that the two plans were NOT equivalent — the loser carried a `[REVIEW]` todo requiring each parent checkbox to cite real
evidence (`terraform plan`/`apply` output, `gcloud pubsub subscriptions list` count, `gcloud run jobs describe` output,
epsilon=0 determinism report path) that the survivor lacked entirely; blindly superseding the "extra" plan would have
silently dropped that check. That asymmetry is the reason todo 3 above insists on porting-before-superseding rather than
just picking a winner by filename.

### 2026-08-07 — na-eligibility-audit

RECLASSIFY `assigned_vm: NA` → `planning` — never previously assessed. All 3 open todos are bounded, mechanical
plan-hygiene engineering (a create-time idempotency guard keyed on `depends_on`, a corpus-wide duplicate-gate detector,
one sweep-and-fix pass reusing the same de-race procedure already proven on this exact pair) with no open design call.
Conflict-check clear: grepped all 9 active `assigned_vm: planning` docs in `orchestrator_master` — the 6 hits were all
just `check_finalize_plan_coverage.py` cited as boilerplate in unrelated AO-batch finalize plans' own Codex-SSOTs
sections, not competing claims on the idempotency-guard/detector work. `assigned_role: infra` and `estimate_class:
refactor` were already set correctly at authoring time — no changes needed there. Issue doc — structurally exempt from
the finalize-plan-coverage requirement.
