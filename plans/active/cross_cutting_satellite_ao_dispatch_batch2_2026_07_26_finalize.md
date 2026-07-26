---
doc_type: plan
title: Cross-cutting satellite AO batch 2 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 14 todos are done. Reconciles each named source doc's checkboxes independently, then
  re-checks batch 2's own Deferred items (3 conflict-gated, 7 operator-gated, 3 time-gated, 9 needs-own-triage-pass),
  actions the two membership/classification findings this audit raised, and archives the batch via the standard 6-step
  ritual.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch2_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-07-26, per task_template.md § 4's finalize-plan-coverage rule —
  every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 2 — finalize

> **Status: draft** — flips to `active` only when its parent batch does. **Machine-gated on
> [`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md)**
> (`depends_on` + `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 14 of that plan's
> todos are `done`. `sequential: true` because todo 2 needs todo 1's reconciliation finished, and todo 4 (archival) must
> run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile every named source doc's checkboxes.** Batch 2's 14 todos cite ~22 distinct source docs
      (each todo's text ends with `Source:` / `Sources:`). For each: flip the corresponding checkbox or section, citing
      the batch commit that shipped it — verify the commit actually exists before citing it. Several batch-2 todos flip
      a source checkbox as **already-landed with re-verification evidence rather than newly-shipped** (the dp-audit
      image-default and `--reclassify-apply` terraform halves, the alerting-subscriber Cloud-Run code ship, the
      `lifecycle-events-sub` terraform codification) — preserve that distinction in the evidence text; do not restate
      them as work this batch performed. After flipping, re-check each source doc for 0 remaining open items (checkbox
      AND prose-form) and only then consider flipping its `status` to `resolved`. **Done when**: every cited source
      checkbox is flipped with verified evidence and no doc's `status` was advanced past what its remaining items
      support.
- [ ] [REVIEW] P1. **Re-check batch 2's own Deferred items now that time has passed and its todos have landed.** For
      each of the 3 conflict-gated, 7 operator-gated, 3 time-gated and 9 needs-own-triage-pass entries: re-read the
      specific gating ground and decide whether it has cleared. Route each to exactly one of — ready for a batch 3 (note
      it), still genuinely gated (re-confirm with fresh evidence), or belongs to another tranche (name that tranche).
      Three specific re-checks are cheap and high-yield: (a) has `defi_satellite_ao_dispatch_batch2_2026_07_26`'s
      finalize resolved the `defi_collateral_sizing…` retag, which would unblock its 4 todos; (b) has the tradfi
      finalize's own re-check cleared the `phantom_captures_tradfi_2026_06_28.md` double-claim; (c) is
      `issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (infra-claimed) resolved, which would unblock the
      vcrpy `--ignore-vuln` drop. **Do NOT re-surface an operator question already asked** — decisions #10 and #11 in
      `issues/autonomous_session_operator_decisions_2026_07_25.md` and the two parked in this audit's own report are
      already queued. **Done when**: every Deferred entry carries a dated re-verification verdict with one of the three
      routings named.
- [ ] [DOC] P2. **Action the two membership/classification findings this audit raised.** (1) **The tranche-membership
      gap.** batch1's Phase-1 scope was 59 docs against a real membership of 142 (104 non-peer-claimed), which is why
      the closeout's Tracks 16-24 went almost entirely un-triaged — those Tracks were added by the 2026-07-25
      corpus-wide sweep AFTER batch1's candidate corpus had been scoped from the earlier 68-doc epic filter. Record this
      in `cross_cutting_consolidated_closeout_2026_07_25.md`'s Progress Log so the next `/ag-closeout-audit` derives
      membership from the closeout's Track/Sources lists UNION the epic filter, not the epic filter alone, and consider
      a one-line note in the skill's cross-cutting membership section. (2) **The
      `sports_prediction_mvp_writetime_precompute` ownership question.**
      `sports_satellite_ao_dispatch_batch6_2026_07_26.md` parked it as "falls through every tranche's audit …
      `cross-cutting`'s audit will not pick it up either", recommending reassignment to `infra`. That premise is
      **measurably wrong**: the skill's cross-cutting rule admits a doc by the epic filter **OR** explicit membership in
      the closeout's Tracks, and this doc is the sole Source of **Track 23 — Manifest schema bump: write-time MVP
      precompute**, so cross-cutting does pick it up (this audit found it that way). Reply to that parked item with this
      evidence rather than retagging to `infra`; if the operator still prefers `infra`, Track 23 must be removed from
      the cross-cutting closeout in the same change so the doc is not double-claimed. **Done when**: the membership note
      is in the closeout's Progress Log, the sports batch6 parked item carries the Track-23 correction, and no doc ends
      up claimed by two tranches.
- [ ] [DOC] P1. **Archive `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`** via the standard 6-step ritual:
      migrate any still-Deferred item to a tracked todo elsewhere (todo 2 above should have routed all 22 — verify none
      silently vanishes) → add the archive banner → run the codex-alignment check (this batch introduces no new durable
      contract; confirm that is still true, noting that the UTL writer-side canonical-path assert DOES tighten a writer
      invariant documented in `/codex/02-data/availability-manifest-and-data-status.md`, so re-read that doc before
      concluding no update is needed) → grep the corpus for every referrer of this batch or this finalize and fix each
      path → confirm `locked_by` is empty on both (it is). **Done when**: both docs are in `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports
      0 hard failures and 0 orphans.
