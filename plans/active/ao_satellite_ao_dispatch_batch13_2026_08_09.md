---
doc_type: plan
title:
  AO satellite AO batch 13 — continue the unsourced-operator-ruling-citation ratchet 53→0
  (agent_operating_framework_master epic)
summary: >-
  THIRTEENTH AO-dispatch batch for the `ao` topic tranche — a single-item satellite extraction from
  `operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`, produced by the same 2026-08-09 `/ag-closeout-audit
  ao` Phase 1 run as `ao_satellite_ao_dispatch_batch12_2026_08_09.md`. Split into its own batch rather than folded into
  batch12 because its source doc's `parent_epic` is `agent_operating_framework_master` (doc/plan-hygiene tooling), not
  `orchestrator_master` (the AO service itself) — per the naming-and-conflict-check SSOT's grouping rule, `parent_epic`
  is the clean axis for which batch an item belongs to (batch11 precedent). The extracted item continues ratcheting
  `check_plan_operator_ruling_evidence.py`'s `unsourced_ruling_baseline` from 53 toward 0 — the source doc's own
  2026-08-09 session already fixed 20 of the original 76 (fully verified, cited sources); the remaining 53 need the same
  per-entry verify-or-escalate treatment.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-13, satellite-docs, satellite-extraction, plan-hygiene]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch13_finalize_2026_08_09.md,
    /plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md,
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md,
    scripts/quality_gates/check_plan_operator_ruling_evidence.py,
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
  ]
source: >-
  `/ag-closeout-audit ao` Phase 1 run, 2026-08-09 (autonomous, scheduled dispatch `agt-41d860`, slot 10) — see
  `ao_satellite_ao_dispatch_batch12_2026_08_09.md`'s Progress Log for the shared provenance/conflict-check context; this
  item was independently flagged bounded/conflict-clear (zero hits across all 24 prior covering plans) before being
  split out on `parent_epic` grounds.
---

# AO satellite AO batch 13

> **`status: draft`** — pending operator approval, same convention as batch5-12: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

`operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md` carries 2 todos: the first (`[SCRIPT] P2`, making a
ratchet-raise loud rather than silent) is already `[x]` done. The second is the actual ratchet-continuation ask —
verify-or-escalate the remaining 53 unsourced-ruling citations, the same bounded, worker-determinable, no-remaining-
judgment-call shape as the 20 the source doc's own same-day session already closed. Split into its own batch (rather
than folded into `ao_satellite_ao_dispatch_batch12_2026_08_09.md`) solely because its source doc's
`parent_epic: agent_operating_framework_master` differs from batch12's `orchestrator_master` group — per
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2, `parent_epic` (not `asset_group`) is
the grouping axis. A 1-item batch is sanctioned by `task_template.md` §4 ("Fewer is fine; group RELATED items") and has
direct precedent (`ao_satellite_ao_dispatch_batch9_2026_08_08.md`, `ao_satellite_ao_dispatch_batch11_2026_08_09.md`,
both also 1 todo).

## Rules for every worker on this plan

- **Never invent a plausible citation.** Per the source doc's own text: a ruling recorded only in a chat session with no
  durable home, or a named-but-unverifiable source doc, must be recorded as genuinely unrecorded and escalated to the
  operator — not closed by guessing. This is the exact failure mode `check_plan_operator_ruling_evidence.py` exists to
  catch.
- Do not edit the source doc's checkbox beyond appending your evidence when done — the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch13_finalize_2026_08_09.md`) reconciles evidence back into the source
  doc.

## Todos

- [ ] [SCRIPT] P2. **Keep ratcheting `check_plan_operator_ruling_evidence.py`'s `unsourced_ruling_baseline` from 53
      → 0.** Run
      `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py --only plans/active/*.md plans/active/issues/*.md`
      to enumerate the remaining violations. For each: verify whether a traceable operator-ruling source genuinely
      exists (apply the doc's own 3-class method: cite-in-window / reword-non-ruling-phrasing / fix a genuine
      autonomous-vs-operator mislabel) and fix it, or — if genuinely unrecoverable — record it explicitly as genuinely
      unrecorded and escalate to the operator rather than inventing a citation. Regenerate the baseline via
      `--baseline-write` (never hand-edited). **Done when**: `unsourced_ruling_baseline` reaches 0, or every remaining
      entry is recorded in this todo's evidence as genuinely unrecorded and escalated. Source:
      `/plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md:103` (its `[SCRIPT] P2`
      item). Repo: unified-trading-pm.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored by the same `/ag-closeout-audit ao` Phase 1/3 pass as
  `ao_satellite_ao_dispatch_batch12_2026_08_09.md` (dispatch `agt-41d860`, slot 10). Conflict-check: grepped all 24
  prior covering plans for `unsourced_ruling_baseline`/`check_plan_operator_ruling_evidence` — zero hits outside the
  source doc's own self-references and the already-resolved
  `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` (cited by the source doc as the origin of this
  gate, not a competing claim on this ratchet-continuation work). Clear to extract. Split into its own batch solely on
  `parent_epic` grounds (see "Why this plan exists" above).
