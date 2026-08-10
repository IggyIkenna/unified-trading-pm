---
doc_type: plan
title:
  Cross-cutting satellite AO batch 12 — 7 bounded NICE-TO-HAVE residuals extracted from
  carry_strategy_ensemble_productionization + features_service_e2e_pipeline_test, round12 2026-08-10 sweep
summary: >-
  Twelfth AO-dispatch batch for the cross-cutting tranche, produced by the 2026-08-10 daily /ag-closeout-audit run's
  Phase 1 Workflow (36 agents classifying every uncited orphan candidate). Of 21 genuinely-orphaned docs found, exactly
  2 carried real, conflict-clear, bounded AO-eligible work: 5 NICE-TO-HAVE engineering follow-ups from
  `carry_strategy_ensemble_productionization_2026_07_24.md` (a rank-allocator archetype, a UI wizard entry, a daily-cron
  scheduler wire-up, a ruff cleanup, and an asset-class filter) and 2 items from
  `features_service_e2e_pipeline_test_2026_05_26.md` (an MDPS BITGET-FUTURES backfill retry now that its blocking
  VM-launch bug is fixed, and a Phase-B CeFi MDPS top-up + delta_one funding_oi/realized_vol verification). Conflict-
  checked against all 4 currently-active cross-cutting batches (batch1b/2/6/11) — zero file/title overlap.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    unified-api-contracts,
    strategy-service,
    unified-trading-system-ui,
    deployment-service,
    e2e-testing,
    market-data-processing-service,
    features-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-12, satellite-docs, strategy-master, features-and-ml-master]
related:
  [
    /plans/active/carry_strategy_ensemble_productionization_2026_07_24.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch12_2026_08_10_finalize.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.6
estimate_calibrated_ai_days: 1.28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/carry_strategy_ensemble_productionization_2026_07_24.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
source: >-
  /ag-closeout-audit cross-cutting run 2026-08-10 (ag_closeout_auditor scheduled worker, dispatch agt-9f1dca, slot 30).
  Phase 1 Workflow (36 agents) classified the tranche's uncited orphan candidates; exactly 2 docs carried genuine
  bounded, conflict-clear AO-eligible work (of 21 total genuinely-orphaned docs found — see
  ag_closeout_audit_cross_cutting_parked_2026_08_10.md for the full breakdown). Conflict-checked against all 4
  currently-active cross-cutting batches' open todos (batch1b, batch2, batch6, batch11 — zero title/file overlap) and
  against the source docs' own coverage notes before extraction. **Status: draft** pending operator approval to dispatch
  per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 12 — bounded-item extraction

> **Status: draft.** Not ingested/dispatched until an operator flips this to `active` (CLAUDE.md "Plan destination — ASK
> BEFORE CREATING" HARD RULE — a skill-drafted batch needs the same explicit approval as a hand-authored one). All 7
> todos below are same-priority-independent and touch distinct files/repos — no `sequential`/`gate_on_depends` needed
> once active.

## Todos

- [ ] [STRATEGY] P3. **Add the `CarryFundingDispersionRankAllocator` + `CARRY_FUNDING_DISPERSION_RANK`
      AllocatorArchetype** so the cross-sectional funding-dispersion rank is computed inside strategy-service instead of
      arriving as the upstream `funding_rank_pct` feature. Model on the existing per-instrument
      `CarryFundingDispersionEngine` (`strategy_service/engine/strategies/v2/carry_and_yield/funding_dispersion.py`,
      already shipped `strategy-service@6b285fad`). **Repo: unified-api-contracts + strategy-service.** Source:
      `carry_strategy_ensemble_productionization_2026_07_24.md` (line 121-124). **Done when**: the new allocator
      archetype is registered end-to-end (UAC enum + leg-spec seed + `ARCHETYPE_TO_FAMILY` + strategy-service allocator
      implementation + unit test), `quality-gates.sh` green, shipped via quickmerge.
- [ ] [UI] P3. **Surface `CARRY_FUNDING_DISPERSION` in the strategy wizard/catalog.** Add `CARRY_FUNDING_DISPERSION` to
      `STRATEGY_ARCHETYPES_V2` + `ARCHETYPE_TO_FAMILY` (CARRY_AND_YIELD) in
      `unified-trading-system-ui/lib/architecture-v2/enums.ts`, bump `enums.test.ts`'s `toHaveLength(18)` → 19,
      regenerate `lib/registry/ui-reference-data.json` via
      `unified-api-contracts/scripts/generate_ui_reference_data.py`. **Playwright gate applies — no tick without
      `[UI]` + `pw:L2 ✓` + a cited regression spec** (per CLAUDE.md's UI testing rule). **Repo:
      unified-trading-system-ui (+ UAC generator).** Source: `carry_strategy_ensemble_productionization_2026_07_24.md`
      (line 125-135). **Done when**: the archetype appears in the wizard/catalog, `enums.test.ts` passes at length 19,
      and a Playwright regression spec covers it green.
- [ ] [INFRA] P3. **Wire the DAILY recurrence for the funding-ensemble paper VM.** The paper VM
      (`launch-funding-ensemble-paper-cron-vm.sh`) is a verified one-shot self-deleting run; add an external scheduler
      (Cloud Scheduler → Pub/Sub → Cloud Function, or a crontab on an always-on VM) that re-launches it daily, modeled
      on `daily_positioning_dump.sh`. **Repo: deployment-service.** Source:
      `carry_strategy_ensemble_productionization_2026_07_24.md` (line 187-190). **Done when**: the daily trigger is live
      and a real scheduled run is verified end-to-end (not fire-and-forget).
- [ ] [INFRA] P3. **Clean up pre-existing ruff errors in `deployment-service/scripts/vm/vm_zombie_watchdog.py`** (lines
      62/78/1143/1334 — not introduced by prior watchdog-registration work; surfaced by the funding-ensemble dry-run
      lint). **Repo: deployment-service.** Source: `carry_strategy_ensemble_productionization_2026_07_24.md` (line
      191-194). **Done when**: `deployment-service`'s `quality-gates.sh` lint stage is green on this file, no new
      ratchet regressions.
- [ ] [STRATEGY] P2. **Add an asset-class filter for the live broad universe.** The top-volume perp universe now
      surfaces tokenized equity/commodity perps (CRCL/INTC/MRVL/MU/SKHYNIX/SNDK/XAG/XAUT) alongside crypto; add an
      optional crypto-only gate (or a UAC asset-class tag) so the carry book can exclude non-crypto underlyings when
      desired. **Repo: e2e-testing → unified-api-contracts (asset-class registry).** Source:
      `carry_strategy_ensemble_productionization_2026_07_24.md` (line 308-312). **Done when**: the filter is wired into
      `funding_reversion_crossvenue_book.py`'s universe construction, defaults preserve current behavior, and a test
      covers the crypto-only exclusion.
- [ ] [DATA] P2. **Retry the previously-blocked MDPS 1h BITGET-FUTURES backfill (2026-04-20..04-30).** The VM-launch bug
      that blocked it is fixed (`deployment-service@49b50814`, 2026-08-09); relaunch via `launch-mdps-backfill-vm.sh`
      (the `--timeframes`-scoped fix `deployment-service@8f1feb4eb9e4` is already live) and confirm it runs to
      completion this time — manifest-verified rows, not fire-and-forget. **Repo: market-data-processing-service.**
      Source: `features_service_e2e_pipeline_test_2026_05_26.md` (line 737-740). **Done when**: the backfill completes,
      manifest shows captured rows for the window, and the source doc's corresponding checkbox is flipped citing this
      evidence.
- [ ] [INFRA] P0. **Phase B — short CeFi MDPS top-up + delta_one funding_oi/realized_vol verification.** First re-check
      whether `data_completion_cefi_2026_07_15.md`'s already-delivered CeFi candles (it delivers ~2x the original MDPS
      top-up ask per the source doc's own 2026-07-27 note) already yield delta_one-computable
      `funding_oi`/`realized_vol_20@1h` fields — if so, skip the MDPS run and go straight to the delta_one
      compute+read-back verification; if not, run ~2-3 days of MDPS over the perp venues (read raw tick from
      `market-data-tick-cefi-prd`, write to a `-test` bucket via `MDPS_OUTPUT_BUCKET_{CAT}`) first, then compute
      delta_one `funding_oi`+`returns`(`realized_vol_20`)@1h → `-test` bucket → read-back, mirroring the recipe already
      proven in this source doc's own Phases 0.5/2/4. **Repos: market-data-processing-service + features-service.**
      Source: `features_service_e2e_pipeline_test_2026_05_26.md` (line 711-716). **Done when**: the delta_one
      `funding_oi`/`realized_vol_20@1h` fields are confirmed present and correct (either via the existing CeFi candles
      or a fresh top-up), read-back verified against the `-test` bucket, and the source doc's checkbox is flipped citing
      the evidence either way.

## Progress Log
