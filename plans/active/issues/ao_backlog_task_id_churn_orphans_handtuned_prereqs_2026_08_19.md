---
doc_type: issue
title: AO backlog task-id churn silently orphans hand-tuned `prereqs.prerequisites` gates — the exact re-dispatch waste `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` was fixed for still recurs via a different mechanism
summary: >-
  A backlog task's `id` is a hash derived (at least in part) from its plan-doc content/title, not a stable identity —
  observed directly on `sports_batch_odds_api_capture_outage_recurrence_check`: the 2026-08-09 slot-4 session attached
  `prereqs.prerequisites: [sports_odds_backfill_chain_converged_to_target_range]` (value `false`) to task id
  `...-9d92e47b666d` specifically to stop this exact todo re-dispatching until an owning campaign converges. By
  2026-08-19 the live task id was `...-bbab759cd4a7` (confirmed via `GET /api/backlog`) — a different id for the same
  plan checkbox — and its `prereqs.prerequisites` field in the live `agent-orchestrator/data/config/backlog.yaml` reads
  `[]` (confirmed via a direct read of the root clone's gitignored `data/config/backlog.yaml`, line ~28509). The gate
  never fired; the task re-dispatched at least 3 more times after 2026-08-09 (slots 25 2026-08-09, 31 2026-08-19T05:57Z,
  33/this session 2026-08-19T19:48Z) each doing a genuinely unproductive re-verification with zero new information to
  act on between the 05:57Z and 19:48Z checks specifically (fresh census: 277/2266 missing days, byte-identical to the
  05:57Z reading). This is the SAME class of waste `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` fixed
  (hand-tuned dispatch config silently reverting), but via a different root mechanism — that fix made the VALUE survive
  a regen tick; it does not make the task ID itself stable, so a hand-tuned field keyed to one id is orphaned the
  moment the id changes for any reason (title text edit, doc content change feeding the id hash, etc.).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao, backlog, prerequisites, dispatch, task-id, regression, findings]
related:
  [
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
  ]
created: 2026-08-19
author: slot-33 (review-role session, dispatched a data_engineering task)
source: ["sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md re-dispatch churn, observed live 2026-08-19"]
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    /plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    market-tick-data-service/scripts/sports/census_odds_api_gap_verify_2026_08_02.py,
  ]
supersedes:
superseded_by:
resolved_by:
---

# AO backlog task-id churn orphans hand-tuned `prereqs.prerequisites` gates

## What I found

While working `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s item 1 (dispatched to slot 33,
2026-08-19T19:45Z), confirmed via `GET /api/backlog` that the live task id is
`sports_batch_odds_api_capture_outage_recurrence_check-bbab759cd4a7`. The doc's own Progress Log records that on
2026-08-09 (slot 4) a worker deliberately created condition `sports_odds_backfill_chain_converged_to_target_range`
(`false`) and attached it as a `prereqs.prerequisites` entry on task id `...-9d92e47b666d` specifically to stop
AO from re-dispatching this todo until the owning `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`
campaign converges — exactly the RULES.md §4 "park a task" recipe.

Direct read of `agent-orchestrator/data/config/backlog.yaml` (root clone; gitignored server-runtime data, not
git-tracked, so this file only exists meaningfully on the host actually running the server — confirmed via
`git check-ignore -v`) shows the CURRENT task entry `sports_batch_odds_api_capture_outage_recurrence_check-bbab759cd4a7`
carries `prereqs.prerequisites: []` — empty. The `-9d92e47b666d` id no longer exists in the live backlog at all. The
gate was never orphaned by a regen-tick REVERT (the bug `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` fixed);
it was orphaned because the task's OWN identity changed out from under the hand-tuned attachment.

Consequence, confirmed via `GET /api/backlog` history + this doc's Progress Log: the same "re-verify, find nothing new,
skip GATED" cycle repeated at least 3 times after the gate was supposedly set (2026-08-09 slot 25, 2026-08-19T05:57Z
slot 31, 2026-08-19T19:48Z slot 33/this session) — each burning a full worker dispatch to re-run the same manifest
census and VM check with a byte-identical result (277/2266 missing days, unchanged between the 05:57Z and 19:48Z
checks specifically — confirmed by re-running `census_odds_api_gap_verify_2026_08_02.py` fresh this session).

## Why it matters

Any worker or main-agent session that follows RULES.md §4's own documented "park a task" recipe to stop wasteful
re-dispatch is silently defeated the next time the task's plan doc changes enough to shift its derived id (which,
per the observed cadence here, is roughly every dispatch on a doc this actively edited) — the parking recipe looks
like it worked (the API call succeeds, the yaml write lands) but provides zero actual protection going forward. This
generalizes beyond this one sports todo: ANY hand-tuned `target_slot`/`affinity`/`priority_override`/
`prereqs.prerequisites` tuning documented in RULES.md §4 is subject to the same silent-orphan failure mode whenever
the owning task's id churns.

## Recommended decision

Two independent fixes worth considering (not mutually exclusive; scoping left to whoever picks this up, hence
`assigned_vm: NA` — this needs a design call, not just a mechanical patch):

1. **Stabilize the task id** — derive it from something that doesn't change on ordinary text edits to the doc (e.g.
   the plan path + a stable per-checkbox anchor/ordinal, not a content hash of the title), so hand-tuned yaml
   attachments survive doc edits.
2. **Re-target on regen instead of dropping** — when `regen_backlog_from_plan.py` retires an old task id and mints a
   new one for what is recognizably "the same" checkbox (same `plan_ref` + same ordinal position, or a fuzzy-match on
   title prefix), carry forward any `prereqs`/`target_slot`/`priority_override` tuning from the retired id to the new
   one instead of leaving the new id with defaults.

Either fix belongs in `agent-orchestrator/server/regen_backlog_from_plan.py` (or wherever task ids are minted) —
`assigned_vm: NA` per the "ask before creating" default; an operator/main-agent call on whether this is worth an
AO-dispatched fix or a human one.

## Todos

- [ ] [INFRA] P2. Design + implement one of the two fixes above in `agent-orchestrator/server/regen_backlog_from_plan.py`
      (or the task-id-minting code it calls) so hand-tuned `prereqs`/`target_slot`/`priority_override` survive a task-id
      change across regen ticks. (repo: agent-orchestrator)
- [ ] [INFRA] P3. Re-attach `prereqs.prerequisites: [sports_odds_backfill_chain_converged_to_target_range]` to the
      CURRENT `sports_batch_odds_api_capture_outage_recurrence_check-bbab759cd4a7` task id in
      `agent-orchestrator/data/config/backlog.yaml` (root-clone/server-host edit — needs main-agent or operator write
      access, out of scope for a regular worker session) as an immediate mitigation while the structural fix above is
      pending, so this specific todo stops re-dispatching on every regen tick until
      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` reports convergence. (repo: agent-orchestrator)

## Progress Log

**2026-08-19 (slot 33, dispatched as review-role, task assigned_role=data_engineering)** — Found while working
`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` item 1. Confirmed the orphaned-gate mechanism via
`GET /api/backlog` (id churn) + a direct read-only inspection of the root clone's `data/config/backlog.yaml` (empty
`prereqs.prerequisites` on the live id). Re-ran the authoritative gap census fresh — 277/2266 missing days, unchanged
from the 2026-08-19T05:57Z reading (slot 31), confirming zero new information was available to act on this dispatch.
Filed this issue doc rather than hand-editing the root-clone `backlog.yaml` myself (out of scope for a worker session
per RULES.md §4, which scopes backlog-yaml tuning to main agent + operator). Skipping the sports todo's task with
`reason_code: GATED` per worker.md §4c.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
