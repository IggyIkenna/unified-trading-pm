---
doc_type: plan
title: Redemption Wallet-Transfer Execution — Finalize
summary:
  Gated finalize plan for redemption_wallet_transfer_execution_2026_08_20 — reconciles evidence and runs the 6-step
  archival ritual once every todo in the source plan is done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [fund-administration-service, execution-service]
scope: [engineer]
tags: [fund-administration, redemption, client-isolation, finalize, archival]
related:
  [
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: client_isolation_and_governance_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [redemption_wallet_transfer_execution_2026_08_20]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: companion finalize plan per task_template.md §4 STRICT rule, 2026-08-20
context_scope:
  [
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Redemption Wallet-Transfer Execution — Finalize

**Why this doc exists**: `task_template.md`'s STRICT rule requires a gated finalize companion for every
`assigned_vm: planning` plan — this reconciles the source plan's evidence and runs the archival ritual so the source
plan doesn't sit `active` with zero open todos.

## Todos

- [x] [REVIEW] P1. Reconcile every completed todo in `redemption_wallet_transfer_execution_2026_08_20.md` against its
  cited evidence (commit SHA, test name) — re-verify each cited commit actually exists and contains the claimed
  change. Done-when: every `[x]` todo's evidence is independently re-confirmed, or a discrepancy is logged and routed
  back to a new todo. — All 8 cited commit SHAs independently re-verified via `git cat-file -e` +
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout` across all three repos (fund-administration-service:
  90603d94a7, ccc751c, af9d292, a1b8934, b877fa8775; execution-service: 6d43020e, d8bae52a;
  unified-api-contracts: 040c871c) — zero discrepancies, every SHA exists and lands on origin. Every cited test name
  (`test_grace_period_handler_keeps_multi_client_withdrawals_isolated`,
  `test_crashed_tick_does_not_double_withdraw_on_retry`, `test_rejected_aml_at_expiry_does_not_pay_out`,
  `test_treasury_ledger_source_wallet_isolated_across_funds_in_one_tick`, `test_transfer_adapter_client_isolation`,
  `TestWithdrawalIdempotency`) confirmed present via grep in the cited test files.

- [x] [REVIEW] P1. Check whether the treasury-wallet-id audit todo (P2 in the source plan) surfaced a real follow-up
  fix rather than a "confirmed safe" finding — if so, spin it into a new tracked todo/plan rather than letting it sit
  as an unactioned finding. — **Yes, it surfaced a real follow-up**: the flat `treasury_wallet_id` default was
  confirmed safe for actual fund MOVEMENT (never consulted by the real transfer path) but flagged a genuine ledger-
  attribution limitation. Not left unactioned: already spun into the source plan's own todo 6
  (`resolve_treasury_source_wallet_id`), shipped `fund-administration-service@b877fa8775` — not a separate
  new plan/todo needed.

- [x] [DOC] P2. Run the 6-step archival ritual on `redemption_wallet_transfer_execution_2026_08_20.md` once every one
  of its todos is `[x]` and unlocked: dated archive folder move, exact-successor banner, corpus-wide referrer-path
  fixup. Done-when: `git mv` lands the source plan into `plans/archive/2026_08/` and `run_hygiene_sweep.sh` shows zero
  broken referrers to its old path. — Codex-alignment step done first: added the new `FundTransferContext.client_id`
  enforcement mechanism + idempotency + treasury-wallet-derivation invariants to
  `/codex/04-architecture/client-funds-isolation.md`'s code-level-invariants table (this plan's durable contract now
  lives in codex, not only in the archived plan). `git mv` + banner + referrer fixup follow in this same commit.

## Progress Log

- **2026-08-20**: Finalize plan authored alongside its source plan per the STRICT companion-finalize-plan rule.
- **2026-08-20**: [operator's interactive main session, `/autonomous`] All 3 todos done — evidence independently
  re-verified (zero discrepancies), treasury-wallet-id follow-up confirmed already folded into the source plan,
  codex updated (`client-funds-isolation.md`), source plan + this finalize doc archived to `plans/archive/2026_08/`.
