---
doc_type: plan
title:
  AO consolidated close-out (2026-08 cycle) — active coordinator for agent-orchestrator-internal findings created after
  the 2026-07 tranche was archived
summary: >-
  The `ao` topic tranche's consolidated close-out was archived on 2026-07-30
  (/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md plus its finalize sibling), but `ao`-tagged work did
  not stop: 115 docs under plans/active still carry asset_group [ao] as of 2026-08-12. That left the tranche with no
  ACTIVE coordinator, and the gap is machine-visible — `check_ag_closeout_linkage` resolves an `[ao]` doc by finding a
  mention in an `ao_consolidated_*` plan across plans/active AND plans/archive, so any `ao` finding created after the
  archived doc stopped being edited is an orphan by construction, and cannot be committed. This plan is that active
  coordinator for the 2026-08 cycle. It deliberately does NOT re-triage the 115 inherited docs (that is todo 1, not a
  claim); it opens the tranche, adopts the findings already blocked on it, and records the structural lesson that a
  tranche whose coordinator is archived while its work continues will silently block commits.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao, close-out, consolidation, plan-hygiene, ag-closeout-linkage]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
# Declared explicitly rather than inherited: todo 1 (re-triage 115 inherited [ao] docs) is a
# judgment-heavy classification pass, not mechanical work, and the role default would under-serve it.
effort: high
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
source: >-
  Opened 2026-08-12 from a measured blockage, not a planning exercise: three peer issue docs had sat UNTRACKED in slot 3
  for up to 10 days because check_ag_closeout_linkage refused them, and diagnosis showed the `ao` tranche's only
  coordinator was archived. Operator decision the same day was to fix the structural gap (open an active tranche doc)
  rather than route around it by retargeting the docs to a tranche they do not belong to.
---

# The `ao` tranche outlived its close-out doc

## What was measured (2026-08-12)

| fact                                                                      | value                                                      |
| ------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `ao` coordinator in `plans/active`                                        | none, before this plan                                     |
| `ao` coordinators in `plans/archive/2026_07`                              | 2 (the 07-25 doc + its 07-30 finalize sibling)             |
| docs under `plans/active` still tagged `asset_group: [ao]`                | 115                                                        |
| dirs `check_ag_closeout_linkage` searches for an `ao_consolidated_*` plan | `plans/active`, `plans/archive`                            |
| consequence                                                               | any post-archive `ao` finding is an orphan → uncommittable |

The linkage check is not wrong to search the archive — an archived tranche legitimately still explains its own
historical findings. The defect is the combination: **archiving a coordinator does not retire the topic**, so the
tranche kept producing findings that nothing active could adopt. The failure surfaces far from its cause, as a
plan-hygiene refusal on an unrelated commit, which is why it sat undiagnosed for 10 days.

## Adopted findings

Docs blocked on this tranche's absence, adopted here so they can be committed:

- `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03` — an operator-ruling citation with no traceable
  source. Tagged `[ao]` (it is about how a worker sourced a ruling), despite the `tradfi_` filename prefix, which is
  itself a naming trap worth noting: **the filename prefix is not the asset group**, and reading it as one is what made
  this doc look like it belonged to the tradfi tranche.
- `ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02` — already mentioned by the ARCHIVED tranche
  doc, so it resolves today, but it is an `ao` finding with open todos and belongs to the active cycle. Adopted so it
  does not depend on an archived doc remaining unchanged forever.

## Todos

- [ ] [INFRA] P2. **Re-triage the 115 inherited `plans/active` docs tagged `[ao]`.** This plan opens the tranche; it has
      NOT classified them. Some are genuinely open `ao` work, many are `ao_satellite_ao_dispatch_batch*` docs that are
      likely closeable in bulk. Done when: each is either linked into this plan's Sources, retagged to the tranche it
      actually belongs to, or archived. Repo: unified-trading-pm.
- [ ] [INFRA] P2. **Adopt the two findings above into a Sources section with per-doc disposition.** Done when: each
      names its resolution path (folded-in / AO-scope / operator-gated), per the issue-doc lifecycle rule in
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. **Make an archived-coordinator tranche detectable before it blocks a commit.** Today the only signal
      is a refused commit on an unrelated change. Options: have the ag-closeout hygiene sweep WARN when an asset group
      has live docs but no ACTIVE coordinator, or have `check_ag_closeout_linkage`'s failure message say "the only
      `ao_consolidated_*` match is archived — the tranche may need reopening" instead of the generic "no path". The
      second is nearly free and turns a 10-day diagnosis into a one-line read. Done when: one is implemented, or both
      are rejected with the reason recorded. Repo: unified-trading-pm.
- [ ] [INFRA] P3. **Decide the tranche-reopening convention and write it down.** This plan invented one (open a
      `<ag>_consolidated_closeout_<new-date>.md` for the new cycle, leave the archived one untouched). It is not
      recorded anywhere as the convention, so the next person to hit this will invent a different one — most likely
      editing the archived doc, which is worse. Done when:
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` states what to do when an archived tranche
      produces new findings. Repo: unified-trading-pm.
- [ ] [INFRA] P3. **Check whether the other archived tranches have the same latent gap.** `ao` was found by accident.
      Any tranche whose coordinator is archived while its asset group still has active docs is one commit away from the
      same block. Done when: every asset group is confirmed to have either an active coordinator or genuinely zero
      active docs. Repo: unified-trading-pm.

## Provenance note

The blockage this plan resolves was itself mis-recorded before it was understood. It was written down as "no
`ao_consolidated_closeout` plan exists", which was false — two exist, both archived. The corrected statement is that
none was ACTIVE. The distinction mattered: the false version implied the tranche had never been closed out, the true one
shows it was closed out and then kept producing work. Recorded here because the wrong version was believed long enough
to shape a plan.
