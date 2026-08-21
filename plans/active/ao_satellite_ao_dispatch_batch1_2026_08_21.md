---
doc_type: plan
title: ao satellite AO dispatch batch 1 — 2026-08-21
summary: >-
  Extraction batch from the ao tranche's 2026-08-21 /na-eligibility-audit run (batch 1 of 3 sub-batches). 1
  conflict-cleared, bounded/deterministic todo pulled from 1 source doc (RECLASSIFY_SPLIT). The source doc
  (`account_failover_ignores_overage_rejected_2026_08_18.md`) has 2 open items: this one (an investigation with a
  stated done-when — measure whether the review role's persistent loop burns overage budget faster than rotation
  replenishes it) and a separate `[OPERATOR]` immediate-remediation decision (top up the account vs. accept it
  unusable until the 2026-08-23 weekly reset) — the source doc stays `assigned_vm: NA` for that item, unaffected by
  this extraction. This item was NOT captured by the source doc's own prior 2026-08-19 na-eligibility-audit pass,
  which extracted 3 of 4 remaining items but described the 4th (this one) as the "sole remaining item" alongside
  it without actually extracting it — a real undercount this batch corrects.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao, ao-dispatch, satellite-batch, na-eligibility-audit, account-failover, overage]
related:
  [
    /plans/active/issues/account_failover_ignores_overage_rejected_2026_08_18.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
effort: low
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/account_failover_ignores_overage_rejected_2026_08_18.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-21 ao-tranche /na-eligibility-audit run (sub-batch 1 of 3, autonomous worker). `status:
  active` from the start (not draft) per the skill's no-double-gate ruling — na-eligibility-audit's own
  RECLASSIFY_SPLIT verdict + conflict-check IS the authorization to dispatch (unlike /ag-closeout-audit's batches,
  which stay draft pending separate operator approval).
---

# ao satellite AO dispatch batch 1 — 2026-08-21

> Extracted from `account_failover_ignores_overage_rejected_2026_08_18.md`'s 4th todo (the review-role
> overage-burn-rate investigation). The item is bounded — pull real activity-log data for the review role's account
> assignment/usage pattern and compare against the pool's replenishment rate, a measurement task with a stated
> either/or "done when," not an open design call — unlike the doc's OTHER remaining item (the `[OPERATOR]`
> immediate-remediation decision on `sub-b-iggy2london`), which stays exactly where it is.

## Todos

- [ ] [BACKEND] P3. Check whether the review role's persistent loop burns through its assigned account's overage
      budget faster than rotation replenishes it — alternate/complementary hypothesis to the pool-exclusion fix
      already shipped via `ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 8. Pull real activity-log data
      (`account_rotation_*`/`overage_status` events) for the review role's account-assignment history over a
      representative recent window and compare its overage-exhaustion rate against ordinary worker-role accounts
      sharing the same pool. Source: `plans/active/issues/account_failover_ignores_overage_rejected_2026_08_18.md`
      (4th todo, `[BACKEND] P3`). Repo: agent-orchestrator. Done when: a dated finding states whether review's burn
      rate is meaningfully higher than other roles' — if confirmed, name the concrete follow-up (e.g. review gets
      its own rotation cadence); if not, close it as noise with the comparison numbers cited.

## Progress Log

- **na-eligibility-audit 2026-08-21 (ao tranche, sub-batch 1 of 3)**: drafted this batch from the one bounded
  AO-eligible item found on `account_failover_ignores_overage_rejected_2026_08_18.md` during a full end-to-end
  re-read — the doc's OTHER open item (the `[OPERATOR]` immediate-remediation decision) is genuinely operator-gated
  and stays put. Conflict-checked: grepped `plans/active/` for "review role...burn"/"burns through...overage"/
  "review...persistent loop" — the only hit (`review_agent_evidence_gated_write_capability_2026_08_09.md`) concerns
  an unrelated write-capability burn-in gate, not this account-overage question; no genuine overlap found. Source
  doc's own checkbox flipped at authoring time to cite this batch, mirroring the doc's own established convention
  for its 3 prior extractions (items 7-9 in `ao_satellite_ao_dispatch_batch25_2026_08_19.md`).
