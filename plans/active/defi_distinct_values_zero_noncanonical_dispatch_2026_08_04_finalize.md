---
doc_type: plan
title: DeFi distinct-values zero-non-canonical dispatch — finalize
summary: >-
  Gated closeout for defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md — machine-held via depends_on +
  gate_on_depends until every todo in that plan is done. Reconciles the plan's own checkboxes (self-contained, not a
  batch extraction from other source docs) against LIVE state (the source doc itself warns every "in progress" line
  needs a live git-log/manifest check, not blind trust), re-checks whether any deferred item's gate has since cleared,
  and runs the standard 6-step archival ritual once fully done.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, canonicalisation, close-out, finalize]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-17"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_distinct_values_zero_noncanonical_dispatch_2026_08_04]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/active/issues/defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn the plan was reclassified assigned_vm: NA -> planning by a /na-eligibility-audit full-sweep run
  2026-08-13 (every open todo was bounded/deterministic). Ships status: active (not draft) per the /ag-closeout-audit
  skill's 2026-07-30 finding: gate_on_depends already machine-holds every task until the plan's own todos are done, so a
  second draft-gate is a redundant, easy-to-forget manual flip.
---

# DeFi distinct-values zero-non-canonical dispatch — finalize

> **Machine-gated on `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that plan is `done`.

## Todos

- [ ] [REVIEW] P2. Reconcile every completed todo in `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` —
      the doc explicitly says every "in progress" line needs a LIVE status check (git log / manifest read), not to be
      trusted at face value; re-verify each "done" claim against a real commit sha and re-run the axis's
      zero-non-canonical check (venues / chains / instrument_types / data_types) rather than trusting the checkbox
      alone. Re-check any deferred item's gate. Done when: every checkbox is verified evidence-backed against live
      corpus state, and every axis is confirmed zero non-canonical (not merely a reduced count).
- [ ] [REVIEW] P2. Once the source plan has zero open todos and the reconciliation above is clean, run the standard
      6-step archival ritual on `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`, then archive this
      finalize plan too. Done when: the source plan and this finalize plan are both under `plans/archive/`, and
      `regenerate_active_plan_inventory.py` reports zero orphan referrers to either.

## Progress Log

- **context-scout 2026-08-15**: re-verified context_scope, no change needed (4 entries).
- **2026-08-17 (slot-4, backend_engineer, review-craft dispatch) — reconciliation performed, todo 1 checkbox NOT
  flipped: source plan's 3 checked-off todos are evidence-backed for their own scoped claims, but the finalize plan's
  own bar ("every axis confirmed zero non-canonical, not merely a reduced count") is genuinely NOT met.**
  - **Commit-sha verification (source plan lines 221/245/254)**: all 3 cited shas exist and match their claimed
    subjects — `market-tick-data-service@5e456d0d` ("correct POOL retirement twin-match key scheme + fold no-twin
    rows"), `@bf712ddb` ("retire legacy rate_indices captured rows to canonical lending_indices"), `@9f5868e5`
    ("retire remaining CURVE dex_pool_fees rows"); `instruments-service@4bb2164e` (coverage.json writer-crash fix),
    `@1e82416a` (blank-instrument_type panel fix), `@552c5768` (EIGENLAYER spot_pair purge). No stale/fabricated
    citations found.
  - **Live axis re-check (2026-08-17/coverage.json, `generated_at: 2026-08-17T00:49:33Z`, `partial: false`, fetched
    directly via `unified_trading_library.get_storage_client`, not read from a cached rollup)**:
    - `rate_indices` and `dex_pool_fees` data_types: **absent (0 captured)** — matches the todo-1 claim, holds today.
    - Uppercase `instrument_type=POOL`: absent from this rollup's `by_venue_instrument_type` aggregation — but this
      does NOT mean the axis is genuinely clean: `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` (open,
      P0) independently measured **1,643,557 captured uppercase-`POOL` rows live as of 2026-08-17** via a direct
      manifest probe (not this rollup) — the coverage.json aggregation apparently case-folds this specific axis
      (the source doc's own "silenced by a comparison-exception" note), so it under-reports here. Deferring to that
      doc's own root-cause chain (a live `market-data-processing-service` writer defect, fix shipped
      `@94215e9cd9`, NOT yet confirmed live) rather than duplicating it.
    - **`dex_pools` data_type: 454,014 captured** (not zero) — matches the already-tracked 2026-08-12 regrowth
      finding in `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` (a manifest rebuild
      re-registered the 2026-08-05-retired rows). Still open there, `assigned_vm: NA` (judgment-heavy).
    - **`dex_swaps` data_type: 3,454,808 captured** (not zero) — the source plan's own row 4/todo explicitly scopes
      this OUT as "separately tracked open migration", consistent with `defi_legacy_data_type_names_manifest_
      migration_scope_2026_08_04.md`'s still-open `[DATA] P2` todo (real content migration, gated on root-causing a
      multi-venue gap cluster + a five-part delete-safety proof — genuinely not a quick fix).
    - **22 composite `PROTOCOL-CHAIN` venues** (BALANCER-\*/CURVE-\*/UNISWAP_V3-\*/etc.): all still present with real
      `captured` counts, consistent with the source plan's own item-3 disposition ("RESOLVED — false alarm, not a
      bug": legitimate MDPS `processed_candles/`-layer data under a different path convention MTDS cannot fold from,
      cross-repo/operator-gated open question, not fixable within this dispatch's scope).
    - **New finding**: `KAMINO_LENDING` regrew to `captured=80` (was 0 as of 2026-08-05/07) and `BLAZESTAKE` regrew
      to `captured=1` (was 0 as of 2026-08-06) — small-scale instances of the same capture_status-flip-retirement-
      undone-by-rebuild/writer recurrence already confirmed for `dex_pools`/`POOL`. Not previously tracked; filed
      `/plans/active/issues/defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md` (P3, NA).
  - **Verdict**: todo 1's own done-when ("every axis confirmed zero non-canonical, not merely a reduced count") is
    NOT satisfied — `dex_pools` (454K), `dex_swaps` (3.46M), uppercase `POOL` (1.64M, per the sibling doc), and the
    new small `KAMINO_LENDING`/`BLAZESTAKE` regrowth are all real, live, currently non-canonical. Every one of these
    is already correctly tracked in its own open issue doc (2 pre-existing + 1 filed this session), each
    appropriately gated (`assigned_vm: NA`, judgment-heavy) rather than silently sitting undocumented. **Checkbox
    NOT flipped** — flipping it would be a false-done claim per this workspace's evidence-gated completion rule.
    Todo 2 (archival) stays correctly blocked on todo 1. This finalize plan stays `active`; re-attempt the
    reconciliation once the tracked blockers (dex_swaps migration, POOL-uppercase writer-fix live-confirmation,
    dex_pools regrowth) actually clear.
- **2026-08-17 (slot-12, backend_engineer, review-craft dispatch) — redispatched same day, re-verified, no change:
  independently confirmed all 3 blocking issue docs (`defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`,
  `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`,
  `defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md`) are still `status: open`. Nothing new to
  execute within this reconciliation task's own scope — the axes stay genuinely non-canonical and each blocker is
  correctly gated (`assigned_vm: NA`, judgment-heavy) elsewhere, not fixable inline here. No checkbox change.
  Released as GATED (not a genuine blocker — this task's own done-when condition simply isn't met yet).
- **context-scout 2026-08-17**: refreshed context_scope (6 entries) -- dropped `commit-push-flip-rule.md` (a
  workspace-universal rule already covered by SUB_AGENT_MANDATORY_RULES.md, not doc-specific) and added the 3
  concrete blocking issue docs the 2026-08-17 reconciliation entries above name as the actual live blockers on this
  finalize's own done-when condition; kept the source plan, archival-discipline codex, and canonical-naming SSOT.
