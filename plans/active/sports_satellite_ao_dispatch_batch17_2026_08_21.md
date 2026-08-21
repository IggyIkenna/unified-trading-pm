---
doc_type: plan
title: Sports satellite AO batch 17 — ag-closeout-audit Phase 3 residual extraction (2026-08-21)
summary: >-
  Seventeenth AO-dispatch batch for sports, drafted by the 2026-08-21 `/ag-closeout-audit sports` Phase 2/3 sweep
  (per `plans/active/issues/ag_closeout_audit_sports_parked_2026_08_21.md`, itself produced by the tranche's
  2026-08-21 Phase 1 triage, 82 candidates). Of the 17-row orphan table, this batch extracts the ONE item that
  re-verified as genuinely bounded/AO-eligible and conflict-clear: the batch historical odds-fetch path's
  missing quota-exhaustion stop condition, from `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`
  todo 1. Every other orphan-table row was re-checked directly (not trusted from the parked doc's one-line summary)
  and confirmed operator-gated, time-gated, already self-dispatched (`assigned_vm: planning` on the source doc
  itself), design-needed, or genuinely LOCAL/human-only by declared scope — see the source parked doc's updated
  orphan table for the per-row disposition. `status: draft` / `assigned_vm: NA` — this needs explicit operator
  review before dispatch, per this session's own dispatch instructions (not the usual no-double-gate posture other
  same-day sports batches use).
status: draft
nature: process
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-17, satellite-docs, ag-closeout-audit, dp-live-004]
related:
  [
    /plans/active/issues/dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md,
    /plans/active/issues/live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: sports_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /ag-closeout-audit sports (2026-08-21, sub-agent authoring session) Phase 3, per
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §3's shared conflict-check protocol
  and task_template.md's dispatch-scope eligibility test. Source triage:
  /plans/archive/issues/ag_closeout_audit_sports_parked_2026_08_21.md (archived 2026-08-21, fully processed).
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
  ]
---

# Sports satellite AO batch 17 — ag-closeout-audit Phase 3 residual extraction (2026-08-21)

## Conflict-check findings

Read `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` end-to-end and grepped every
active `plans/active/*.md` / `plans/active/issues/*.md` doc for the batch-historical-quota-stop action's own naming
(`odds_api_adapter.py::_run_league_fetch_loop`, "exhausted quota", "credits_exhausted") — no other active doc claims
this exact fix. The sibling doc `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md` covers the
SAME incident but only the already-shipped `upstream_failure_reason()` connector fix and the `[OPERATOR]` credential
ask — it does not name the batch-path quota-stop gap, so no overlap. The source doc's own second non-operator todo
(provision-check the live sink topic before a producer launches) was re-verified NOT extractable this pass: its
incident-specific instance is already fixed by `sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`'s
Phase-0 work (`deployment-service@cc9974d07e` + `terraform apply`), and the narrower standing-guard ask it leaves
behind has no concretely scoped implementation target yet — left open on the source doc, not batched. The `[OPERATOR]`
credential top-up/relaunch ask stays correctly excluded (genuine spend/access decision).

Todo 1 below carries no `[OPERATOR]` tag and no design/judgment fork — it is a bounded, worker-determinable outcome
per `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility": add a
terminal-on-401 stop condition to one named function, with a stated done-when.

## Todos

- [ ] [CODE] P1. **Make the batch historical odds-fetch path stop on an exhausted `odds-api-key` quota instead of
      looping 401s forever.** `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py::_run_league_fetch_loop`
      (lines ~855-862) only trips its `credits_exhausted` stop on a body containing `OUT_OF_USAGE_CREDITS` or a
      present `x-requests-remaining` header — the historical (`v4/historical/...`) endpoint's 401 response provides
      neither, so a dead/exhausted shared key is never detected and the loop keeps re-hammering the API across every
      remaining date, re-draining any key that gets topped up within hours. Add: treat a bare HTTP 401 on the
      historical endpoint as terminal (record the current date `attempted_failed` with a classified venue error, then
      break the date loop) — mirroring how the live WS path already classifies a dead key via
      `upstream_failure_reason()` (`market-tick-data-service@40b9b624`, already shipped). Add a regression test
      asserting a bare-401-no-remaining-header response stops the loop after recording one `attempted_failed` date,
      not silently continuing. `quality-gates.sh --no-fix` green before commit; ship via quickmerge. Source:
      `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` follow-up todo 1 (repo:
      market-tick-data-service). Done when: the stop condition is added with a passing regression test, and the
      source doc's own todo 1 checkbox is flipped with the shipped commit cited as evidence.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the shared conflict-check
  protocol applied to the todo above
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — the underlying honest-absence/classified-error
  discipline this fix extends from the live path to the batch path

## Progress Log

- **2026-08-21 (ag-closeout-audit sports, sub-agent Phase 2/3 sweep)**: authored from the 2026-08-21 Phase-1 parked
  orphan table's near-duplicate-pair row
  (`dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` +
  `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md`). Every other orphan-table row was
  re-read directly this session and found NOT extractable (operator-gated / time-gated / already self-dispatched /
  design-needed / genuinely LOCAL-by-design) — see the parked doc's updated table for the per-row disposition. This
  is the sole net-new bounded item this pass surfaced. **Status left `draft`** per this session's explicit dispatch
  instructions (needs operator review before activation) — NOT the no-double-gate posture some earlier same-day
  sports batches used.
