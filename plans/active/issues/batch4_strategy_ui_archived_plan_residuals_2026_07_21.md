---
doc_type: issue
title: Batch-4 archived-plan (strategy/UI) residual open items — successor mapping + verification gaps
summary: >-
  Plan-discipline audit of 5 archived strategy/UI plans (part of the batch-4 P3 sweep in
  pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md) whose residual `- [ ] ` items don't have an obvious
  1:1 active-plan owner. Two are HUMAN-gated confirmations pending operator sign-off; three have code that appears to
  have shipped since the plan was archived but the specific residual checkboxes were never verified/flipped or split
  across multiple current owners.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-discipline, governance, strategy, ui, dart, mtds]
related: []
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
resolved_by:
locked_by:
source: [pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

Auditing 5 of the 8 archived strategy/UI plans in the batch-4 sweep, none of their residual open `- [ ]` items has a
clean, verifiable, single active-plan successor — each needs a distinct follow-up:

## 1. `plans/archive/leveraged_leg_controller_2026_05_01.plan.md` (2 open items)

- Phase A/B/C formal unit tests (holding_wallet override precedence, Solana inner-instruction walk, L2 book shape
  projection) — currently smoke-tested only via the surrounding chain, plan itself calls this "recommended next session"
  but no session picked it up.
- features-onchain-service Docker image rebuild so the Cloud Run cron picks up the Phase B inner-instruction walker —
  operator/deployment-side, not a code change.

No active plan references either item today (grepped `holding_wallet`, `inner-instruction`, `LST reward` across
`plans/active/`).

## 2. `plans/archive/transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.plan.md` (2 open items)

Both are `[HUMAN] P2` gates: (a) post-merge validation re-run of the TM backfill VM comparing cold vs warm-cache
wall-clock, (b) approving `[unlock-plan]` once (a) confirms the cache-hit speedup. Neither can be honestly checked off
by an agent — they require an operator to actually run the comparison and sign off. Per the parent issue doc's own note,
these need "operator confirmation ... before checking them off" — I have no evidence either happened, so I'm not
fabricating a checkmark.

## 3. `plans/archive/ui_quality_gates_parity_2026_03_16.plan.md` (25 open items)

Phase 1-2 SSOT artifacts this plan proposed (`scripts/quality-gates-base/base-ui.sh`,
`scripts/quality-gates-base/eslint.config.base.js`) **already exist in the repo today** — the core hardening shipped,
just not via this plan's tracked commits, and the checkboxes were never flipped.
`codex/06-coding-standards/ui-testing-layers.md` is now the living UI-testing SSOT (post-dates this plan by 4 months).
But the granular residual items (any-type cleanup, console.log removal, per-UI test-depth floors, coverage-exclusion
audit, cursor rule, codex doc) can't be trusted as done-by-osmosis without re-auditing against current UI repos — 4
months of drift is too long to blind-close.

## 4. `plans/archive/combo_bundle_aggregation_2026_04_30.plan.md` (16 open items)

The core writer-side bundling **shipped in code**:
`market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py:256` —
`_UNDERLYING_PARTITIONED_TYPES` includes `"combo"` with an inline comment confirming "Now bundle by underlying (one
combos.parquet per (date, data_type, underlying))". But the migration-script items (`rebundle_combo_parquets.py`,
dry-run, cutover, reader-compat-shim removal, manifest reconciler for stale per-combo rows) have no evidence of having
run — `tradfi_consolidated_closeout_2026_07_18.md` (active) already tracks adjacent combo/manifest defects (1,154,976
tick-side `UD_*` manifest combos) and is the natural current owner to fold this residual verification into, but I did
not find explicit confirmation the 2026-04-30 migration itself ran.

## 5. `plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md` (67 open items, genuinely mixed

domain)

Frontmatter declares `superseded_by: marketing_site_three_route_consolidation_2026_04_26.md` (active, `plans/ai/`),
which is real and does own the client-onboarding/questionnaire/FOMO-funnel work streams (A + B early phases). But the
plan's tail (Phase 9: `archetype_capability.py` VOL/MARKET_MAKING/PORTFOLIO archetype additions, `bespoke_capable`
field, admin-assignment model) is a completely different domain — strategy archetype-capability taxonomy — which is
owned today by `plans/active/capability_wizard_and_manifest_2026_06_11.md` (active; its `ARCHETYPE_CAPABILITY_REGISTRY`
extraction work directly overlaps). A single successor reference would misrepresent one of the two halves, so this needs
a real owner audit of which of the 67 items landed under which of the two active plans before either can be honestly
closed.

# Why it matters

These are the checker's `C-archive-no-successor` violations — the archived plans have DEFERRED/out-of-scope language but
no successor reference, so `check_plan_discipline.py` counts them against the ratchet. A banner naming a wrong or
partial successor would be false documentation (worse than the missing banner); a generic "not applicable" banner would
be fabricated completion for these 5 (none has zero open items). Real closure needs the todos below actioned.

# Recommended decision

Add the `## Deferred work — migrated to:` banner on each of the 5 source plans pointing at this issue doc (accurate —
this doc is where the real follow-up now lives), then work the todos below to resolve them properly, at which point this
issue doc can point to whichever plan actually ends up owning each thread.

## Todos

- [ ] [SCRIPT] P3. Write Phase A/B/C formal unit tests for `LeveragedLegController`'s holding_wallet override
      precedence, Solana inner-instruction walk, and L2 book shape projection (currently only smoke-tested via the
      surrounding chain) — see `plans/archive/leveraged_leg_controller_2026_05_01.plan.md` § "Outstanding". (repo:
      features-onchain-service)
- [ ] [HUMAN] P3. Rebuild + push the features-onchain-service Docker `:latest` image so the LST-seasonal-rewards Cloud
      Run cron picks up the Phase B inner-instruction walker before the cron is (re-)enabled. (repo:
      features-onchain-service)
- [ ] [HUMAN] P3. Run the TM backfill VM post-merge validation (cold vs warm-cache wall-clock comparison,
      `launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2025-06-01 2025-06-14`) and confirm ≥80% speedup; only
      then approve the `[unlock-plan]` on
      `plans/archive/transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.plan.md`. (repo:
      instruments-service)
- [ ] [DOCS] P3. Re-audit `ui_quality_gates_parity_2026_03_16.plan.md`'s 25 residual items against the CURRENT state of
      `codex/06-coding-standards/ui-testing-layers.md` + the 11 consumer UI repos (any-type violations, console.log
      usage, per-UI test-depth floors, coverage-exclusion comments, cursor rule, codex doc) — the SSOT artifacts
      (base-ui.sh, eslint.config.base.js) already shipped but the granular items were never verified. (repo:
      unified-trading-system-ui)
- [ ] [SCRIPT] P3. Verify whether the CME combo-parquet migration (`rebundle_combo_parquets.py` dry-run + production
      cutover + reader-compat-shim removal + manifest reconciler for stale per-combo rows) from
      `combo_bundle_aggregation_2026_04_30.plan.md` actually ran — the writer-side bundling shipped
      (`symbol_rules.py:256`) but the historical re-bundle + cleanup steps have no found evidence. Fold into
      `tradfi_consolidated_closeout_2026_07_18.md` if still outstanding. (repo: market-tick-data-service)
- [ ] [DOCS] P3. Split `dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`'s 67 residual items between
      `marketing_site_three_route_consolidation_2026_04_26.plan.md` (onboarding/questionnaire/FOMO funnel, Phases 0-8)
      and `capability_wizard_and_manifest_2026_06_11.md` (Phase 9 archetype-capability taxonomy) — name each item's real
      owner (or a fresh issue doc for whatever lands in neither) instead of a single blanket successor. (repo:
      unified-trading-pm)
