---
doc_type: issue
title:
  "na-eligibility-audit and ag-closeout-audit's populations are NOT disjoint as documented —
  generate_ag_closeout_audit_candidates.py has no assigned_vm:NA exclusion, so a draft ag-closeout-audit batch can
  independently claim the exact same content an na-eligibility-audit run is evaluating"
summary: >-
  Found while running `/na-eligibility-audit ci` (2026-07-31, autonomous, dispatch agt-1afa0f, role
  na_eligibility_auditor, slot 3). `cursor-configs/skills/na-eligibility-audit/SKILL.md` states as a design premise: "An
  assigned_vm: NA, status: active/open doc is by definition not orphaned — /ag-closeout-audit correctly never touches
  it." This is FALSE against the actual implementation. `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`
  (lines ~213-227) filters candidates purely by tranche membership (`asset_group`/`parent_epic`) — it reads
  `assigned_vm` only to compute a `self_dispatched` flag (used to exclude a doc from the "never_cited" orphan bucket
  when it's `planning`+active), but never excludes `assigned_vm: NA` docs from the candidate population at all. A
  never-cited `assigned_vm: NA` doc is therefore treated as a genuine orphan and can be extracted into a fresh
  `ag-closeout-audit` satellite batch — the exact same content an `na-eligibility-audit` run might independently verdict
  RECLASSIFY for. Measured impact today: of 11 `ci`-tranche docs this run classified, 3
  (`deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md`,
  `uv_bootstrap_fallback_test_structural_anchor_stale_2026_07_30.md`, and 2 of 5 items in
  `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`) were already independently extracted,
  same-day, into the sibling `/ag-closeout-audit ci` skill's draft `ci_satellite_ao_dispatch_batch4_2026_07_31.md` —
  caught only because this run happened to cross-check that draft manually before finalizing verdicts; nothing in either
  skill's own procedure currently requires that check.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, na-eligibility-audit, ag-closeout-audit, ssot-contradiction, conflict-check, plan-hygiene]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/issues/deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md,
    /plans/active/issues/uv_bootstrap_fallback_test_structural_anchor_stale_2026_07_30.md,
    /plans/active/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md,
    scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
  ]
created: 2026-07-31
last_updated: "2026-07-31"
parent_epic: agent_operating_framework_master
priority: P2
source: >-
  /na-eligibility-audit ci skill run 2026-07-31 (autonomous, scheduled dispatch agt-1afa0f, role na_eligibility_auditor,
  slot 3) — Phase 2 conflict-check prep, cross-checking a same-day draft ag-closeout-audit batch before finalizing
  RECLASSIFY-adjacent verdicts.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: correct-codex
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# na-eligibility-audit / ag-closeout-audit population overlap

## What I found

Running `/na-eligibility-audit ci` (Phase 2 conflict-check prep), I checked whether any same-day
`ci_satellite_ao_dispatch_batch*.md` draft already claimed content from the 11 `assigned_vm: NA` docs this run had in
scope — a due-diligence step, not something either skill's procedure currently mandates. It found real overlap: 3 of the
11 docs were already cited as `Source:` in `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (a same-day
`/ag-closeout-audit ci` draft), each with a freshly-drafted extraction todo carrying the doc's exact content.

Traced the root cause to `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`:

```python
assigned_vm = fm.get("assigned_vm")
# a doc that is itself assigned_vm:planning + status:active/open IS its own dispatch vehicle --
# it does not need external citation elsewhere to be "covered" (it covers itself). Only a
# self-dispatched doc's absence of ANY covering AND non-self-dispatched status is a true orphan
# signal.
self_dispatched = assigned_vm == "planning" and status in ("active", "open")

candidates.append({... "assigned_vm": assigned_vm, ...})
```

`assigned_vm` is read ONLY to compute `self_dispatched` (used downstream to decide whether a `planning`-assigned doc
needs external citation to count as "covered"). There is no branch anywhere in this function — nor in the tranche
membership filter above it — that excludes `assigned_vm: NA` docs from the candidate population. A never-cited NA doc
reads as `never_cited=True, self_dispatched=False` — identical to a genuinely-unowned orphan — and is drafted into the
next satellite batch exactly like one.

This directly contradicts `cursor-configs/skills/na-eligibility-audit/SKILL.md`'s stated design premise: "Where that
skill asks 'is anything uncovered?', this skill asks a different question about a DIFFERENT, disjoint population... An
`assigned_vm: NA`, `status: active/open` doc is by definition not orphaned — `/ag-closeout-audit` correctly never
touches it." That sentence describes intent, not the shipped behavior.

## Why it matters

The two skills run on independent schedules (`na-eligibility-auditor.timer` odd hours :30, `ag-closeout-auditor.timer`
even hours :30 — deliberately offset specifically to avoid a same-hour 18-slot demand spike, per
`na-eligibility-audit/SKILL.md`'s own "Scheduled cadence" section) and neither currently cross-checks the other's output
before finalizing a verdict. The failure mode this enables: `na-eligibility-audit` flips an NA doc's `assigned_vm` to
`planning` (RECLASSIFY) at the same time `ag-closeout-audit` independently extracts the identical content into a NEW
satellite doc — two dispatchable paths to the same fix, risking two workers implementing it twice, or one worker's work
silently orphaning the other's todo. Today's run avoided this only because it happened to manually grep the current
draft batch before finalizing — not because either skill's documented procedure requires it. As the corpus and
scheduled-run cadence scale, an unlucky same-day pair (an active na-eligibility-audit RECLASSIFY landing between an
ag-closeout-audit batch's draft and its activation) becomes a matter of when, not if.

## Recommended decision

Two independent questions, not one:

**(1) Should `ag-closeout-audit`'s candidate population actually exclude `assigned_vm: NA` docs** (making the SKILL.md
claim true), **or is including them intentional** (an NA doc that's never cited anywhere might genuinely be a
mis-tracked orphan `na-eligibility-audit` alone wouldn't catch, since NA doesn't guarantee "referenced by an active
plan")? I don't have enough context on the original design intent to rule this — it's a genuine design call, not a bug I
should silently "fix" by adding a filter.

**(2) Regardless of (1), the conflict-check protocol should explicitly require checking the other skill's DRAFT output —
not just currently-active planning docs.** `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
§ 3 currently enumerates 3 surfaces: (a) active `assigned_vm: planning` plans in the same `parent_epic`; (b) sibling
batch/finalize docs drafted in the SAME run; (c) the tranche's own consolidated-closeout digest. None of these covers "a
draft batch from the OTHER skill's prior run" — exactly what caught today's 3 overlaps. This part is a low-risk,
mechanical addition (not a judgment call) and I'd recommend it regardless of how (1) resolves:

- [ ] [DOC] P2. Add a 4th conflict-check surface to
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3: "(d) any `status: draft`
      `{ag}_satellite_ao_dispatch_batch{N}_*.md` for the same tranche, from EITHER skill's prior run (not just the same
      run) — grep its `Source:`/`## Deferred`/`## Already covered` citations for the candidate doc's path before
      finalizing a RECLASSIFY or drafting a new extraction." Update both `na-eligibility-audit/SKILL.md` and
      `ag-closeout-audit/SKILL.md` to reference the new surface explicitly (the former's Phase 2, the latter's own Phase
      3 conflict-check) rather than leaving it to be independently rediscovered per run.
- [ ] [OPERATOR] P3. **RETAGGED (na-eligibility-audit 2026-07-31, was `[SCRIPT]`)** — decide question (1) above
      (operator or design-owning agent), then either (a) add an `assigned_vm != "NA"` guard to
      `generate_ag_closeout_audit_candidates.py`'s candidate filter and correct nothing else (SKILL.md's claim becomes
      true), or (b) correct `na-eligibility-audit/SKILL.md`'s "disjoint population" / "`/ag-closeout-audit` correctly
      never touches it" claim to describe the actual (non-disjoint) boundary, making the 4th conflict-check surface
      above load-bearing rather than defense-in-depth. Retagged because this is a genuine design call, not bounded
      worker-determinable work. **Duplicate-decision note**: this is the SAME underlying question as
      `plans/active/issues/ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md`'s own open
      `[OPERATOR] P1 BLOCKED-OPERATOR-DECISION` todo (its Finding 2 — whether an `assigned_vm: NA` doc can be an orphan
      candidate at all). Whoever rules on either should resolve both in the same pass; do not answer twice
      independently.

## What I did NOT do

Did not modify `generate_ag_closeout_audit_candidates.py` or the SKILL.md disjointness claim myself — question (1) is a
genuine design call outside a single audit run's scope to resolve unilaterally, and I'm not the `ag-closeout-audit`
skill's owner. Did not flip `assigned_vm` on any of the 3 overlapping docs — see each doc's own
`## na-eligibility-audit verdict` section (2026-07-31 entries) for the per-doc KEEP-NA-STALE reasoning that avoided the
duplicate-dispatch risk this run.

## Progress Log

- **na-eligibility-audit 2026-07-31** (tranche=cross-cutting, dispatch agt-845699): RECLASSIFY (partial) →
  `assigned_vm: NA → planning` (in place, name unchanged). Todo 1 (add the 4th conflict-check surface to the codex
  SSOT + both SKILL.md files) is bounded, mechanical, and explicitly stated by this doc's own author as valuable
  "regardless of how (1) resolves" — left open, now dispatches. Todo 2 (decide the NA-exclusion design question)
  retagged `[SCRIPT]→[OPERATOR]` and cross-referenced against
  `ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md`'s own already-open, already-active
  `[OPERATOR]` decision on the same underlying question (found by this audit's own conflict-check — see that todo's
  note). Conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) on todo 1:
  grepped for any existing claim on "4th conflict-check surface" / cross-skill draft-batch checking anywhere in the
  active corpus — zero hits besides this doc itself. Also checked every `status:active`+`assigned_vm:planning` doc under
  `parent_epic:agent_operating_framework_master` (18 docs) for a competing claim — none. CLEARED.
