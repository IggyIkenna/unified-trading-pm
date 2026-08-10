---
doc_type: plan
title: AO satellite AO batch 18 — post-window DeepSeek A/B analysis close-out
summary: >-
  EIGHTEENTH AO-dispatch batch for the `ao` topic tranche — a full-tranche `/na-eligibility-audit ao` re-sweep,
  2026-08-10, group 3. `deepseek_flash_ab_routing_test_2026_08_05.md`'s 24h monitoring window (target: 2026-08-06 20:41
  UTC) has long since closed — today is 2026-08-10 — so its 4 remaining open items (post-window cost pull,
  completion-quality audit, review-coverage check, final writeup) are no longer time-gated; each carries a stated
  done-when and none require a production routing change (the routing itself already shipped and is stable), unlike the
  plan's original "operator wants to review a live production routing change" NA rationale which the doc's own history
  shows no longer blocks per-item extraction (5 other items on the same doc were already extracted to batch12).
  **Note**: this batch originally also planned to extract `ao_open_issues_consolidated_close_out_2026_07_17.md`'s item
  807 (plan_reconciler end-to-end proof) — dropped from scope after finding, mid-authoring, that a CONCURRENT session
  had already fully closed that exact item via `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4 (checked `[x]`
  2026-08-10, real evidence: 20 completed reconcile runs, R1/R2 both answered) — extracting it here would have
  duplicated already-done work. See that batch's own finalize plan for the pending checkbox-reconciliation step; not
  this batch's concern.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-18, satellite-docs, satellite-extraction, deepseek]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch18_finalize_2026_08_10.md,
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.32
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
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  `/na-eligibility-audit ao` full-tranche sweep, group 3, 2026-08-10. Conflict-check: grepped every `status:
  draft`/`active` `ao_satellite_ao_dispatch_batch*` (1-17) + finalizes for `deepseek_flash_ab_routing_test` post-window
  comparison — batch12 cites `deepseek_flash_ab_routing_test_2026_08_05.md` but only for its ALREADY-extracted todos
  2/4/12a/17b/25 (do NOT re-touch those here). No overlap found for todos 9/10/11/13. (A second candidate item,
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s item 807, was found already covered by a concurrent session's
  `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4 mid-authoring — dropped from this batch, see summary.)
---

# AO satellite AO batch 18

> **`status: draft`** — pending operator approval, same convention as batch5-17: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved.

## Why this plan exists

`deepseek_flash_ab_routing_test_2026_08_05.md` has 5 open items already extracted to
`ao_satellite_ao_dispatch_batch12_2026_08_09.md` (todos 2, 4, 12a, 17b, 25). Its remaining 5 open items are todo 8 (a
24h-elapsed monitoring-window time-gate — no longer a live gate, folded into todo 9 below as context, not extracted
separately since it has no independent action) and todos 9/10/11/13 (post-window cost comparison, completion-quality
audit, review-coverage verification, final writeup+archive) — each has a concrete done-when and is read-only
analysis/writeup, not a live production routing change (the change itself already shipped in the doc's own todos
1-7/14-24). Prior audits (round9 2026-08-09 and earlier) kept the whole doc NA on the rationale that it's "a live
production routing change the operator wants to review" — but that rationale describes the ORIGINAL routing change, not
these follow-on analysis items, and the doc's own history already shows per-item extraction is the established pattern
here (5 items already extracted this way).

## Rules for every worker on this plan

- **Do not edit the source doc's other remaining checkboxes** beyond appending your evidence line to the todo you
  executed. The paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch18_finalize_2026_08_10.md`)
  reconciles evidence back into the source doc.
- The 4 sub-items below are NOT file-disjoint from each other (all write into
  `deepseek_flash_ab_routing_test_2026_08_05.md`'s own Progress Log) — run them as ONE sequential todo, not 4 separate
  dispatches.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM — read-only queries against the live
  orchestrator VM's `state.db` only.

## Todos

- [x] ✅ [REVIEW] P1. **DeepSeek flash-vs-pro post-window analysis + writeup (4-part sequential chain, all writing into
      the same source doc).** Source: `/plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md` todos 9, 10,
      11, 13. (a) **Pull the post-window comparison** (todo 9): real `$/task`, `$/plan`, avg turn count, avg total
      tokens/task for pro vs flash over the full monitoring window (now closed, target was `2026-08-06 20:41 UTC`,
      individually and aggregated — compute whether flash's per-token discount beats pro once turn-count is priced in,
      not just headline `$/task`. Expect unequal sample sizes between pools (documented ratio-skew finding in the doc's
      own Progress Log) — report as-is, don't force balance. (b) **Completion-quality audit** (todo 10): Layer 1 (cheap)
      — for every task in each pool, check whether it was later `/reopen`'d and whether its promoted commit's
      `quality-gates-v2` run was green. Layer 2 (the one that matters) — pull a stratified sample of ~15-20 completed
      todos from EACH pool, matched by plan/`estimate_class`, and independently review the actual diff (a fresh agent or
      operator, no stake in the outcome, exactly as the doc's own text allows) — correct/needs-rework/broken per item,
      not just an aggregate percentage. (c) **Review-coverage verification** (todo 11): pull the review agent's own
      activity/chat history for the monitoring window, count how many completed todos it actually touched vs. the total
      completed count — if coverage is a small fraction, note that Layer 2 above is doing the real work, not a backstop.
      (d) **Final writeup + archive** (todo 13): write the verdict (keep flash / drop it / use it only for a specific
      task class) into the source doc's Progress Log with the real numbers cited from (a)-(c), then run the standard
      6-step archival ritual on that doc IF it reaches zero open todos (it has other closed items already; confirm none
      of todos 2/4/12a/17b/25's extractions in batch12 are still open before archiving). **Done when**: all 4 sub-items'
      evidence is recorded in the source doc's own Progress Log with real numbers/verdicts cited (not placeholders), and
      the source doc is archived if genuinely at zero open todos. Repo: unified-trading-pm (analysis + doc-writeup only,
      read-only queries against the live orchestrator VM's `state.db`). — `unified-trading-pm@79e653a7a0`: all 4
      sub-items written into the source doc's Progress Log with real numbers (flash ~13.7% cheaper/task, ~7.4%
      cheaper/plan despite ~68% more turns, because its blended $/M-tokens is ~2.6x cheaper; Layer-1 reopen-rate pro
      1.6% vs flash 6.4%; Layer-2 51-item matched-plan diff sample 0 defects either pool; review-agent real coverage
      ~1.6% of fleet completions with one concrete miss found). Verdict: KEEP FLASH. **NOT archived** — todo 25's
      batch12 extraction is still open, per this todo's own gating condition.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-10 (ao full-tranche NA-eligibility sweep, group 3)**: Authored after a per-doc re-read of 26 `ao`-tranche
  docs. This item was previously time-gated (todos 9/10/11/13, gate long since cleared) — this batch is that bounded
  pull + writeup, not new judgment work. Conflict-checked against every `status: draft`/`active`
  `ao_satellite_ao_dispatch_batch*` (1-17) + finalizes — no overlap found. A second originally-planned item (item 807 of
  `ao_open_issues_consolidated_close_out_2026_07_17.md`) was dropped mid-authoring after discovering a concurrent
  session (`ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4) had already fully closed it the same day — see this
  doc's own summary for detail.
