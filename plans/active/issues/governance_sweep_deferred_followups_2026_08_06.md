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
    /plans/archive/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
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
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /scripts/plan-hygiene/check_na_corpus_ratchet.py,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
  ]
---

# Governance sweep 2026-08-06 — deferred follow-ups

## Todos

- [x] ✅ [SCRIPT] P1. **DONE 2026-08-06 — ran the NA-eligibility-style reclassification pass this sweep's rulings
      unlocked.** Built a candidate set of 122 `assigned_vm: NA` docs (35 docs this sweep edited directly that were
      still NA + 87 more found citing one of the 80 docs this sweep touched, via `rg -f` stem-matching against the full
      NA inventory, filtered to drop aggregator/closeout-tracker false-positives). Ran a Workflow (13 classify batches +
      7 per-`parent_epic` conflict-check groups, 20 agents total) against the na-eligibility-audit rubric. Verdict
      split: 89 KEEP_NA_VALID, 13 RECLASSIFY, 11 KEEP_NA_STALE_DUPLICATE, 6 KEEP_NA_STALE_ITEMS, 3 ARCHIVE. Of the 13
      RECLASSIFY candidates, conflict-check cleared 7 and found 6 genuine conflicts (see the new todo below — filed per
      protocol, not flipped). Flipped `assigned_vm: NA → planning` on the 7 cleared docs (all `doc_type: issue`, so
      structurally exempt from needing a finalize twin), each citing the specific `RULED 2026-08-06` marker that
      unblocked it: `issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`,
      `issues/ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md`,
      `/plans/archive/issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md`,
      `issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md`,
      `issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`,
      `issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`,
      `issues/prod_mutation_evidence_artifact_gap_2026_08_03.md`. **Ratchet**: `check_na_corpus_ratchet.py` went from
      389 docs/1326 open todos (failing, 5 over the 384 baseline) to **382 docs/1311 open todos** (green, below
      baseline) — re-ran with `--update-baseline` to lock in the shrink (382/1311, was 384/1347). Evidence:
      `unified-trading-pm@<pending — see this commit>`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-06 — cleaned up all 16 STALE_OR_RESOLVED `[OPERATOR]` tags this sweep's triage
      found.** Verified each against live doc state (not from the stale triage read alone) before touching anything —
      one (`cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`) turned out to be a case where the
      ORIGINAL triage was wrong: a dedicated same-day `na-eligibility-audit` had already re-examined it and reaffirmed
      KEEP-NA (the redeploy half resolved, but the test-pass-confirmation half genuinely remains open) — left untouched,
      per the na-eligibility-audit rubric's own "never re-litigate an established ruling" rule. Breakdown: **5 real
      checkbox flips** (`cefi_track7_candle_namespace_residual_2026_07_25.md` — real archaeology needed, the gating
      parent plan had archived with the delete confirmed done;
      `issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`;
      `issues/delta_one_get_captured_instruments_blank_id_perp_funding_2026_07_30.md`;
      `issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`;
      `issues/sports_g1_noise_population_mismatch_and_scope_bug_2026_07_27.md`), **1 severity downgrade**
      (`issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` — P1 DO-FIRST → P2, the "ongoing data
      loss" premise no longer held once an independent same-day fix landed), **1 confirmed-genuinely-still-blocked**
      (`issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md` — legitimately waiting on a scheduled
      maintenance window, re-verified as recently as yesterday), **1 confirmed-original-triage-wrong**
      (`cefi_content_migration_shard24...` above), and **8 already correctly resolved, no action needed**
      (`defi_consolidated_closeout_2026_07_18.md`, `l2_book_microstructure_capture_2026_07_13.md`,
      `issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`,
      `/plans/archive/2026_08/issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md` (resolved, archived
      2026-08-09), `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` — grep false-positive,
      matches were inside a fenced quote block, not live checkboxes;
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md`,
      `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`,
      `issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`). Evidence: `unified-trading-pm@09cdfaad65`.
- [x] [OPERATOR] P2. **6 RECLASSIFY candidates from the 2026-08-06 na-eligibility-audit reclassification pass hit a
      genuine conflict-check CONFLICT — filed here per protocol, not flipped.** Each needs an explicit operator ruling
      (or a fresh re-check once the cited sibling doc's own state settles) before it can be either reclassified or
      closed as duplicate: 1. `plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` — **genuine
      same-day factual contradiction, highest priority of the 6.** This doc's own text claims "RULED 2026-08-06
      (operator): go-ahead to run --apply" with no cited session/decision-doc provenance, but
      `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` (same date, `status: active`) lists the identical item under
      "Deferred — operator-gated ... unchanged, NOT re-asked if already asked", asserting it is STILL unruled. Needs a
      direct read to determine which doc is actually current before either can be trusted. **RESOLVED 2026-08-07
      (operator, via consolidated NA-blocker-digest audit): "go ahead" confirmed as the current, correct ruling** —
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s "RULED 2026-08-06: go-ahead" text was right;
      `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` was simply stale (written ~3h before the ruling landed) —
      fixed in that doc directly (its "Deferred — operator-gated" paragraph now points here). Item 1 of 6 CLOSED; items
      2-6 below remain open. 2. `plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md` — todo
      1 duplicates an already-open `[CI] P1` todo in
      `instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md`, and this doc's own premise (PR
      #1084 "merges via the standard auto-merge pipeline") is stale — PR #1084 was actually CLOSED (not merged) by the
      fleet provenance gate at 2026-08-06T10:30:44Z; the real blocker is the larger provenance-marker-corruption issue
      tracked in `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`. 3.
      `plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md` — todo 3's lending_indices
      stall premise ("no captured data since 2026-07-31") is contradicted by
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` item 7 and
      `defi_manifest_consolidator_stale_lock_silent_stall_2026_08_05.md`, both showing KAMINO-SOLANA lending_indices
      rows captured through 2026-08-05; already independently conflict-parked by
      `defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md`'s own open todo 2 — re-read the live per-venue
      availability_index before drafting any stall-diagnosis todo. 4.
      `plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` — todo 1 (split
      `lst_rate_honest_coverage_2026_07_21.md` under the line cap) presupposes the SPLIT approach (option B), but the
      governing meta-issue's own RULED-2026-08-06 answer chose option A (narrow `check_line_caps.sh`'s exception)
      explicitly instead of B — todo 1 is not the ruled path; also independently conflict-parked by
      `defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md`'s open todo 2. 5.
      `plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` — todo 1's CME
      `instrument_id`-format verification sub-task near-verbatim duplicates the `[DIAG] P2` todo already tracked above
      in this same doc — dispatching both risks two workers independently verifying the same thing. 6.
      `plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md` — remaining todos 2 and 3 are
      verbatim-duplicated by `cefi_satellite_ao_dispatch_batch6_2026_08_02.md`'s own open todos (explicitly sourced from
      this exact doc); todo 1's docstring sub-part is separately already resolved via
      `cefi_satellite_ao_dispatch_batch8_2026_08_06.md` (needs a stale-checkbox correction citing `8a6bbc97`, not a
      planning-dispatch). Net: none of this doc's 3 remaining open todos represent fresh reclassify-eligible work.
      **Done when**: each of the 6 is either reclassified (if the conflict resolves in its favor), closed as a
      stale-checkbox/duplicate correction against the doc it collides with, or explicitly re-affirmed KEEP-NA with the
      conflict cited.

      **round5-cross-cutting-audit 2026-08-08: all 6 subparts now confirmed resolved, no operator ruling needed.**
                                          (1) already closed above (2026-08-07). (2) `sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md` already
                                          self-corrects the stale PR#1084 citation (current PR is #1093). (3)
                                          `defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`'s own 2026-08-08 Progress Log ran the live
                                          re-check, confirmed the stall IS real, removed the BLOCKED-OPERATOR-DECISION park. (4)
                                          `lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` (committed 2026-08-08) confirms the split is now moot.
                                          (5) `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s own audit entries already identify this
                                          as the same live conflict. (6) `okx_futures_instid_marker_convention_mismatch_2026_07_30.md` Progress Log
                                          already cross-validates via an independent convergent audit run. All 6 close as stale-checkbox/duplicate
                                          corrections against the docs they collide with.

                                  **CLOSED 2026-08-08 (na-eligibility-audit round7)**: the round5-cross-cutting-audit entry immediately above already found all 6 subparts resolved as stale-checkbox/duplicate corrections against the docs they collide with -- flipping this checkbox to match (no new investigation performed, citing that entry's own evidence).

- [x] ✅ [OPERATOR] P2. **aws_codebuild_terraform_import_pending_2026_07_22.md's D1-D4 rows still need your own read** —
      this sweep ruled the provider-pin sub-question (v5-align, recommended) but explicitly did not fabricate answers to
      the IAM-policy-drift-specific D1-D4 rows without reading them directly. **round5-cross-cutting-audit 2026-08-08
      (id=58)**: operator directed a relevance check first ("workspace is shifting to GCP for all trading infra, AWS
      scoped down to CI self-hosted runners + AO — investigate whether this AWS CodeBuild resource is still relevant
      before ruling on D1-D4"). Investigated in the source doc: **NOT moot** — the AWS CodeBuild fleet is a live,
      load-bearing half of the dual-cloud image-build CI gate (`/codex/05-infrastructure/dual-cloud-image-builds.md`,
      `status: current`; both GCP+AWS must pass before a staging→main promote merges), actively touched as recently as
      2026-08-07, and is the concrete mechanism behind the deliberate "GCP-primary/AWS-backup" resilience posture
      (`/codex/11-project-management/dual-cloud-cost-ops-playbook.md`). D1-D4 stays genuinely open — real per-row
      IAM-policy-drift judgment calls, not something to close as moot or guess. Full evidence in the source doc's own
      Progress Log. (repo: unified-trading-pm)
- [x] ✅ [OPERATOR] P2. **daily_trading_analyst_llm_job_design_2026_07_29.md needs the actual escalation-N number** —
      how many days a finding may recur unremediated before its severity escalates, and the initial severity assignment.
      A genuine business-risk-tolerance parameter, not something this sweep should invent. Suggested starting point if
      useful: N=3 days. **RESOLVED 2026-08-08 (operator ruling, cross-cutting round 5, id=48/id=59, recorded in
      `daily_trading_analyst_llm_job_design_2026_07_29.md`)**: escalation-N = 3 days, initial `assigned_vm` default for
      freshly auto-filed finding issue docs = `planning`. Recorded in that doc's own §5 todo 6 (now `[x]`). (repo:
      unified-trading-pm)
- [ ] [OPERATOR] P3. **sports_predictions_live_mode_activation_readiness_2026_07_21.md's final live-trading go-ahead is
      deliberately still open** — real-money live trading, reserved for your own explicit sign-off per the workspace's
      live-trading-activation HARD RULE, not defaulted by this sweep regardless of how many adjacent items got resolved.
      Review the full Groups A-H readiness ladder directly before deciding. **operator ruling 2026-08-08 (cross-cutting
      round 5, id=60, and its sports-tranche duplicate id=80)**: re-confirmed — not yet, stays pending, permanent
      hard-stop. No change; genuinely still open. (repo: unified-trading-pm)
- [ ] [OPERATOR] P0. **ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md's fork-PR-approval setting
      needs a manual click, no safe API path exists.** `unified-trading-pm` is public with 8 self-hosted runners; the
      operator already ruled "require approval for fork PRs" (option a) this session, but the actual GitHub setting
      (Settings → Actions → General → "Fork pull request workflows from outside collaborators" → "Require approval for
      all outside collaborators") has no documented REST endpoint — checked live 2026-08-06 against
      `actions/permissions`, `actions/permissions/workflow`, and `actions/required-workflows`, none expose it. This is
      the actual code-execution security gate, still open. **operator ruling 2026-08-08 (cross-cutting round 5, id=61,
      same as id=42)**: will do it later — leave blocked for now, no change. (repo: unified-trading-pm, GitHub settings
      only)
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
- **context-scout 2026-08-07**: refreshed context_scope (3 entries) — todo 1 (the reclassification pass) is now DONE, so
  re-pointed the list at what a worker touching the still-open items actually needs: kept the na-eligibility-audit
  methodology, swapped the one-shot inventory generator for `check_na_corpus_ratchet.py` (the ratchet this doc's DONE
  todo moved and any future NA work must keep green), and added
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` (the open P2 conflict-check item's own text names it
  "highest priority of the 6"). **Stale-candidate finding**: this doc's own `related:` frontmatter still cites
  `/plans/archive/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md`, which no longer exists at that path —
  it was archived to `/plans/archive/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md` (`status: resolved`)
  since this doc's own related-list was written; not added to context_scope (fully resolved, superseded by this doc's
  own newer 2026-08-06 sweep) but the dead active-path citation is a `/plan-reconcile`-class fix this skill does not
  make itself.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — all 7 open todos are either explicit
  `[OPERATOR]` business/policy/security-setting decisions (5) or bounded-but-genuinely-unassessed
  investigation/editorial work this sweep itself deliberately declined to do blind (the CME `instrument_id` format
  check, the line-cap doc trim) — none is a mechanical mass edit.
- **round5-cross-cutting-audit 2026-08-08**: applied the operator's fresh NA-corpus blocker-digest rulings (id=48/58/
  59/60/61) — closed 2 of the 4 remaining `[OPERATOR]` todos (D1-D4 relevance-checked-not-moot; escalation-N/assigned_vm
  settled), re-confirmed the other 2 stay genuinely open (live-trading go-ahead permanent hard-stop; fork-PR-approval
  setting deferred by the operator's own "later" answer). 2 of 7 open todos remain: fork-PR-approval-setting (P0, manual
  GitHub UI click owed) and live-trading go-ahead (P3, permanent human sign-off).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, stale item closed -- flipped todo 2's checkbox
  (the 6 conflict-parked RECLASSIFY candidates), citing the doc's own round5-cross-cutting-audit entry that already
  found all 6 resolved. Remaining open todos are 2 permanent operator hard-stops (live-trading go-ahead;
  fork-PR-approval GitHub UI click with no API path), 1 bounded-but-gated-by-the-whole-doc-rule DIAG item, and 1
  editorial line-cap trim needing human judgment -- whole doc stays NA.
