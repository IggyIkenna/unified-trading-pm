---
doc_type: plan
title: DeFi satellite AO batch 18 — extraction from the 2026-08-19 /ag-closeout-audit defi run
summary: >-
  Satellite-batch extraction from the 2026-08-19 /ag-closeout-audit defi run's Phase 1 classification (99 AG-primary
  docs audited via a Workflow, one agent per doc, against all 30 active defi covering plans). 65 docs verdicted
  orphaned (59 orphaned_never_touched + 6 orphaned_partial_coverage); of those, 9 conflict-cleared bounded items from
  8 source docs are extracted here. The remaining ~56 orphaned docs stay untouched: ~23 are already self-dispatching
  (assigned_vm: planning, feeding the AO backlog directly off their own checkboxes — no batch item needed), and the
  rest are genuinely operator/design/human/time-gated, most already reconfirmed correctly-NA across 5+ prior
  na-eligibility-audit rounds each (see the parked-findings doc for the full breakdown). Every extracted item
  conflict-checked (§3 protocol) against every active defi covering doc, including batch14's still-draft Todos (5 of
  the original 14 shortlisted candidates were already extracted there and are excluded here to avoid duplication) and
  batch11/2's own Deferred/conflict-check sections.
status: draft
nature: process
asset_group: [defi]
stage: [data, strategy]
repos:
  [
    market-tick-data-service,
    features-service,
    strategy-service,
    instruments-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-18, ag-closeout-audit]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19_finalize.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_19.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md,
    /plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    /plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_19.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_18.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/defi_live_poller_phased_build_2026_08_15.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: medium
thinking_tier: high
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_19.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
source: >-
  `/ag-closeout-audit defi` (2026-08-19, dispatch agt-fa5ded, slot 28, ag_closeout_auditor). 99 AG-primary candidate
  docs classified via a Workflow (one agent per doc, effort:medium) against the 30-doc active covering-plan set
  (generate_ag_closeout_audit_candidates.py --tranche defi). Every extracted item cleared the shared conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) against every active defi
  covering doc. Per-item Source: citations below point at the exact originating doc + todo.
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 18 — 2026-08-19

## Todos

- [ ] [SCRIPT] P1. **Verify the `bounded_freshness_warmup()` fix (market-tick-data-service@4925f88d73) actually
      resolves the `lending_indices` Cloud Run Job OOM/timeout**, now that a fresh MTDS Cloud Build image has had time
      to redeploy it — run `gcloud run jobs execute` for the affected job, confirm it completes without the prior
      OOM/timeout signature, and record the result (pass or genuine-recurrence) back into the source doc. Repo:
      market-tick-data-service. Source: `plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`
      (sole remaining open item). Done when: the job run's outcome is confirmed with cited evidence (log excerpt or
      `gcloud run jobs executions describe` output) and the source doc's checkbox is updated to match.
- [ ] [DATA] P1. **Build the 5 missing MTDS chain-field collectors** (ltv, liquidation_threshold, reward_rate,
      flash_loan_liquidity, health-factor — 5 protocol-specific on-chain data sources) and recompute the 5 currently
      feature-less on-chain feature groups that depend on them. Repos: market-tick-data-service, features-service.
      Source: `plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` (sole open
      [DATA] P0 todo). Done when: all 5 collectors are wired and capturing, the 5 dependent feature groups recompute
      with non-empty output, and quality-gates.sh is green on both repos.
- [ ] [SCRIPT] P2. **Wire a `defi_collection_scheduler.tf` Cloud Scheduler entry for the `native_staking_rates`
      aggregate feature**, mirroring the existing `collect-eigenlayer-rewards` cron's shape exactly (same trigger
      cadence pattern, same handler wiring convention). Repo: deployment-service (or wherever
      `defi_collection_scheduler.tf` lives — confirm path first). Source:
      `plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_19.md` (its own report: "the doc's only genuinely
      defi-scoped, AO-eligible remaining item"), cross-ref `plans/active/defi_migration_audit_log_2026_07_24.md`. Done
      when: the Terraform entry exists, applies cleanly, and the cron fires on schedule (verified via one live
      trigger or a `terraform plan` diff review).
- [ ] [SCRIPT] P1. **Build the operator-ruled "Option B" true-native-staking-return metric** (FX-noise-isolated, Hard
      Rule #5 holding-based formula) for `carry_staked_basis`'s STAKING leg — requires a new per-position
      entry-spot-price anchor. The operator ruling (2026-07-29, direct answer, cited in the source doc's own `##
      Todos` section) POST-DATES `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s 2026-07-26 conflict-check note
      that called this "a two-part semantic fork requiring an OPERATOR decision" — the decision has since been made;
      only the build remains. Repo: strategy-service. Source:
      `plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` (sole open Todos item,
      "RULED 2026-07-29 (operator direct answer) — Option B... Not yet started"). Done when: the metric is
      implemented per the ruled formula, unit-tested, and the source doc's checkbox is flipped with the
      implementation SHA cited.
- [ ] [DATA] P2. **Migrate `dex_swaps` → `dex_pool_swaps` content** for the 22 of 24 (venue, chain) pairs still
      carrying legacy-only historical dates (up to 84% on SUSHISWAP_V3/ARBITRUM) — a real content migration, not a
      rename. Run the standard five-part GCS delete-safety proof
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) before any legacy-path delete step; the recent
      2025-07-27..2025-08-06+ gap sub-cluster was already root-caused and closed separately (does not resolve this
      broader migration). Repos: market-tick-data-service, unified-trading-library. Source:
      `plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` (sole open [DATA] P2
      todo). Done when: all 22 pairs read from the canonical `dex_pool_swaps` path with matching row counts, the
      five-part delete-safety proof is filed, and the legacy `dex_swaps` objects are removed only after that proof
      passes.
- [ ] [OPERATOR] P3. **Verify the 4 `*-test-*` DeFi buckets are still genuinely empty, then delete them** (a
      capture_status/GCS-delete action — requires the five-part GCS delete-safety proof
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` before any `gcs_delete_object` call, per CLAUDE.md's
      delete-safety gating rule). This is the narrow actionable slice the source doc's own item 6 was rescoped to on
      2026-08-16. Source: `plans/active/defi_migration_audit_log_2026_07_24.md` item 6 (line ~672). Done when: fresh
      emptiness is confirmed for all 4 buckets, the delete-safety proof is filed, and the buckets are removed (or the
      todo is re-parked with a cited reason if any bucket is no longer empty).
- [ ] [DATA] P3. **Re-verify whether the cefi+tradfi G4 apply-complete coupling condition for Era-B legacy retirement
      is now genuinely satisfied** (a 2026-08-19 flag already in the source doc notes it "now appears satisfied and
      needs re-verification") — if confirmed, proceed with the Era-B legacy retirement itself; if not, re-park with
      the current blocking state cited. Repos: unified-api-contracts, market-tick-data-service. Source:
      `plans/active/defi_migration_audit_log_2026_07_24.md` item 2 (line ~155). Done when: the cefi+tradfi G4 status
      is confirmed with a cited source, and either the retirement is executed or the todo is re-parked with the
      genuine current blocker named.
- [ ] [DOCS] P3. **Author the 2 missing paired finalize plans** for `defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md`
      and `defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` (both already `assigned_vm: planning` / self-dispatching,
      neither has a finalize companion — `task_template.md` §4's finalize-plan-coverage rule), and resolve the live-infra
      ambiguity note on `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`'s coverage-gap claim. Repo:
      unified-trading-pm. Source: `plans/active/issues/plan_reconciler_findings_defi_2026_08_18.md`. Done when: both
      finalize plans exist with `depends_on` + `gate_on_depends: true` pointing at their batch, pass
      `check_frontmatter_schema.py`, and the live-infra ambiguity is resolved with a cited answer.
- [ ] [DATA] P3. **Pull a real per-chain TVL snapshot to confirm/re-sequence the Tranche 3/4 build ordering** for the
      DeFi live-poller phased build — the doc's own 2026-08-17 Progress Log entry confirms this follow-up is still
      open and unchanged. This is scoped narrowly to the TVL-ordering check only; the Tranches 1-4 real-connector
      builds themselves (~37 venues) are NOT extracted here — see this batch's Deferred section, they need their own
      dedicated `defi_live_poller_ao_dispatch_batch2` plan, not a single batch-18 line item. Repo:
      market-tick-data-service. Source: `plans/active/defi_live_poller_phased_build_2026_08_15.md` ("Follow-up
      todos" section). Done when: a fresh TVL snapshot is pulled and the Tranche 3/4 ordering is confirmed or
      corrected in the source doc.

## Deferred — not extracted this batch

- **`defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md`** — all 6 open todos are the scoping pass itself (re-run
  CF-2/CF-3 checks, determine legacy-vs-canonical path shapes, size the work). `defi_satellite_ao_dispatch_batch11_2026_08_09.md`
  already assessed and declined this exact doc for the identical reason ("none is a bounded fact yet, per the doc's
  own dispatch-scope-eligibility self-assessment") — re-confirmed unchanged today. Non-batchable-taxonomy: too-large/
  needs-its-own-scoping-pass. Re-check next batch only if the doc's own scoping work advances.
- **`defi_migration_audit_log_2026_07_24.md` items 3-4 (FOLD-3 orphan data_types, DeFi collection-gaps retag)** —
  `defi_satellite_ao_dispatch_batch16_2026_08_17.md` already assessed both and explicitly declined extraction,
  flagging that the doc's own premise needs rewording/correcting before either can be cleanly extracted. Unchanged
  today. Non-batchable-taxonomy: needs a doc-correction pass first, not a re-triage.
- **`defi_migration_audit_log_2026_07_24.md` item 5 (OPERATOR aggregator-routes bucket-target decision)** and item 1
  (GATE C v9 explicit-apply) — item 1's only citation anywhere is inside `defi_instruments_store_v9_gate_c_apply_write_2026_08_16.md`,
  itself still `status: draft` (not yet operator-approved) — drafting a second, duplicate extraction here would race
  that already-drafted plan once it ships. Non-batchable-taxonomy: operator-gated (item 5) / already-drafted-elsewhere
  pending approval (item 1).
- **`defi_live_poller_phased_build_2026_08_15.md` Tranches 1-4** (~37 DeFi venue live-connector builds) — genuinely
  substantial, multi-week engineering scope, not a single bounded todo. **Recommendation for the operator**: this
  needs its own dedicated `defi_live_poller_ao_dispatch_batch2_<date>.md` + finalize pair (mirroring how Tranche 0
  became `defi_live_poller_ao_dispatch_batch1_2026_08_16.md`, now archived), scoped per-venue or in small venue
  groups, not folded into a satellite batch. Non-batchable-taxonomy: too-large-for-a-batch-todo.
- **`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`** (~88 open todos) and
  **`elysium_carveout_stubbed_strategy_service_2026_08_12.md`** — both repeatedly reconfirmed correctly `assigned_vm:
  NA` by 3+ independent na-eligibility-audit passes each (client-delivery/disclosure-sensitive judgment work, capital-
  budget/custody-architecture design). Not re-triaged here; see the parked-findings doc for the full citation trail.
  Non-batchable-taxonomy: genuinely human-only.
- The remaining ~48 orphaned docs (of 65 total classified this run) carry ONLY operator/design/human/time-gated
  remaining work, each already independently reconfirmed correctly-NA by 3-8+ prior na-eligibility-audit rounds. Full
  per-doc breakdown (verdict + citation trail) is in `plans/active/issues/ag_closeout_audit_defi_parked_2026_08_19.md`
  — not re-listed here to avoid this batch doc breaching its line cap with non-actionable content.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, defi tranche, dispatch agt-fa5ded, slot 28)**: drafted from the `/ag-closeout-audit
  defi` Phase 1 classification (99 docs via Workflow, 65 orphaned). Of an initial 14-item shortlist assembled from the
  orphaned set (docs whose remaining work read as bounded and not explicitly operator/design/human-tagged), 5 were
  found already extracted into `defi_satellite_ao_dispatch_batch14_2026_08_16.md` (still `status: draft`, pending
  operator approval — `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`,
  `instruments_service_defi_golden_red_capability_drift_2026_08_14.md`,
  `dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md`,
  `mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md`, and the wiring items from
  `pendle_venue_onboarding_2026_08_16.md`) and excluded here to avoid duplication. 9 items cleared the conflict-check
  cleanly and are extracted above. `status: draft` per the skill's safety rail — flipping to `active` is an operator
  decision, not made here.

**Codex SSOTs**: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, `plans/active/task_template.md` §4.
