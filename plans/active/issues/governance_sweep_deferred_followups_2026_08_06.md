---
doc_type: issue
title: >-
  Follow-ups from the 2026-08-06 interactive governance sweep — NA-reclassification pass, stale-tag cleanup, and
  operator-owned items not yet actioned
summary: >-
  A single interactive session (2026-08-06) audited the full operator-decision backlog across the active corpus:
  activated all 16 pending AO-dispatch draft batches (6 clean-as-drafted, 4 resolved via fresh operator rulings on their
  own blockers, 6 fixed for stale content then activated), and ruled on all 63 live [OPERATOR]-tagged decisions the
  corpus carried (4 P0, 23 P1, 27 P2, 5 P3) via a Workflow-based triage (29 agents) + a refresh pass (8 agents) that
  re-verified everything against the just-shipped activations before asking anything twice. Live-verified one operator
  instruction before executing it (github_actions_operator_gated_followups' "close 52 false cassette-drift issues"
  claim) and found it factually wrong — all 18 currently-open issues show real, persistent 19-day-old schema drift, not
  false positives — corrected the doc instead of closing real evidence. Resolved 4 genuine git conflicts against
  concurrent same-day AO sessions working the same docs, keeping whichever side represented more-complete actual work
  rather than blindly picking one. This doc captures what the sweep surfaced but did NOT finish: the reclassification
  pass it was building toward, a bookkeeping cleanup, and every item that stayed genuinely operator-owned
  (business/live-trading/policy decisions with no default I should apply).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [governance-sweep, operator-decisions, na-eligibility, plan-hygiene, follow-up]
related:
  [
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-06
author: interactive session (governance sweep)
last_updated: "2026-08-06"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: review
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive governance-sweep session, 2026-08-06 — operator-directed full pass over the AO-dispatch draft-batch
  backlog and the entire live [OPERATOR]-decision corpus, requested explicitly ("check for operator blocking stuff...
  let's pick these all up and use answers to unlock more on the 1.3k tasks sitting outside AO").
context_scope:
  [/cursor-configs/skills/na-eligibility-audit/SKILL.md, /scripts/plan-hygiene/generate_na_doc_tranche_inventory.py]
---

# Governance sweep 2026-08-06 — deferred follow-ups

## Todos

- [ ] [SCRIPT] P1. **Run the NA-eligibility-style reclassification pass this sweep's rulings unlock.** Every P0-P3
      ruling this session made (see the session's governance report) potentially clears the blocker on one or more
      `assigned_vm: NA` docs — e.g. any NA doc whose sole open item was gated on a decision that's now RULED should be
      re-evaluated for `NA → planning`. Re-run (or hand-drive) `/na-eligibility-audit` across the 9 tranches with this
      session's rulings as fresh input, prioritizing docs that cite any of the 58 docs this sweep edited. **Done when**:
      a fresh `check_na_corpus_ratchet.py` count is recorded showing the NA-corpus delta from this pass, and each
      reclassified doc's `assigned_vm` flip is committed with a citation back to the specific ruling that unblocked it.
- [ ] [SCRIPT] P2. **Clean up the 16 STALE_OR_RESOLVED `[OPERATOR]` tags this sweep's triage found but did not fix.**
      The governance-sweep Workflow (29 agents) classified 16 open `[OPERATOR]`/`BLOCKED-OPERATOR` items as "already
      resolved elsewhere, checkbox/tag never flipped" — a bookkeeping gap, not a live decision. List:
      `cefi_track7_candle_namespace_residual_2026_07_25.md`, `defi_consolidated_closeout_2026_07_18.md`,
      `l2_book_microstructure_capture_2026_07_13.md`,
      `issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`,
      `issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`,
      `issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md`,
      `issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`,
      `issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`,
      `issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`,
      `issues/delta_one_get_captured_instruments_blank_id_perp_funding_2026_07_30.md`,
      `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`,
      `issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`,
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md`,
      `issues/sports_g1_noise_population_mismatch_and_scope_bug_2026_07_27.md`,
      `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`,
      `issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`. For each: verify the stated resolution still holds
      (state may have drifted since the triage read), then flip the checkbox/tag citing the resolving commit/doc. **Done
      when**: all 16 carry a flipped checkbox or an explicit "still genuinely open, triage was wrong" correction,
      whichever the fresh check finds.
- [ ] [OPERATOR] P2. **aws_codebuild_terraform_import_pending_2026_07_22.md's D1-D4 rows still need your own read** —
      this sweep ruled the provider-pin sub-question (v5-align, recommended) but explicitly did not fabricate answers to
      the IAM-policy-drift-specific D1-D4 rows without reading them directly. (repo: unified-trading-pm)
- [ ] [OPERATOR] P2. **daily_trading_analyst_llm_job_design_2026_07_29.md needs the actual escalation-N number** — how
      many days a finding may recur unremediated before its severity escalates, and the initial severity assignment. A
      genuine business-risk-tolerance parameter, not something this sweep should invent. Suggested starting point if
      useful: N=3 days. (repo: unified-trading-pm)
- [ ] [OPERATOR] P3. **sports_predictions_live_mode_activation_readiness_2026_07_21.md's final live-trading go-ahead is
      deliberately still open** — real-money live trading, reserved for your own explicit sign-off per the workspace's
      live-trading-activation HARD RULE, not defaulted by this sweep regardless of how many adjacent items got resolved.
      Review the full Groups A-H readiness ladder directly before deciding. (repo: unified-trading-pm)
- [ ] [OPERATOR] P0. **ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md's fork-PR-approval setting
      needs a manual click, no safe API path exists.** `unified-trading-pm` is public with 8 self-hosted runners; the
      operator already ruled "require approval for fork PRs" (option a) this session, but the actual GitHub setting
      (Settings → Actions → General → "Fork pull request workflows from outside collaborators" → "Require approval for
      all outside collaborators") has no documented REST endpoint — checked live 2026-08-06 against
      `actions/permissions`, `actions/permissions/workflow`, and `actions/required-workflows`, none expose it. This is
      the actual code-execution security gate, still open. (repo: unified-trading-pm, GitHub settings only)
- [ ] [DIAG] P2. **Verify the exact CME `instrument_id` string format before implementing
      tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md's ruled fix.** The operator approved option A
      (make `_resolve_spot_perp` asset-group-aware) and the standard CME FX underlying codes (6A/6B/6C/6E/6J) are
      well-known, but this sweep did not verify the codebase's actual internal `instrument_id` string shape for CME
      FUTURE contracts against the live catalogue — confirm before coding, don't assume the OKX-FUTURES `@LIN`/`@INV`
      marker shape carries over unchanged. (repo: instruments-service)
- [ ] [DOCS] P3. **Human line-cap trim of `data_completion_defi_2026_07_15.md`** (sits at the 1000L hard cap) needed
      before `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md`'s 2 dropped context_scope entries can
      be restored — this needs editorial judgment about what to cut/split from a 1000-line doc, which this sweep
      deliberately did not attempt blind. (repo: unified-trading-pm)

## Not blocking, informational

The following are already RULED + AO-dispatchable from this sweep (not blocked on anything further from an operator) but
were not personally executed by the sweep itself — real infra mutations (VM launches, GCS deletes, IAM changes,
terraform applies) that need their own careful individual execution + evidence capture, which is a substantially
different task than writing the ruling:

- `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.1b (god-SA `objectAdmin` removal) — approved, live evidence
  already gathered (P2.2e done, P2.3 test passed), execution is a real fleet-wide-blast-radius terraform apply.
- `defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md` (R3 relaunch) — approved, unblocks the DeFi catalogue + 4
  paused collectors.
- `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` — all 5 phases approved including the Phase 4
  delete (gated on a fresh soft-delete-retention check at execution time, per the doc's own updated text).
- `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` — non-SPOT/day-chunked execution approach approved.
- `deribit_combo_perpetual_partition_move_2026_07_21.md` — the ~15,119-row production data MOVE is signed off.
- Several smaller `[CODE]`/`[INFRA]`/`[SCRIPT]` rulings across the P1/P2 batch — see each doc's own `RULED 2026-08-06`
  annotation for specifics.

## Progress Log

- **2026-08-06 (interactive governance sweep)**: filed at session end (context ~81%, /pre-compact checkpoint) to make
  sure the reclassification pass this sweep was explicitly building toward, plus the lower-priority bookkeeping and
  every genuinely operator-owned item, survive as tracked work rather than only existing in chat.
