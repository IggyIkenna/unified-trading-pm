---
doc_type: plan
title: TradFi satellite AO batch 9 — finalize (reconcile 2 source docs + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch9_2026_08_09.md — machine-held via depends_on + gate_on_depends:
  true until both of that plan's todos are done. Reconciles the 2 source docs (flip/cite the item each batch9 todo
  closed), re-checks the 3 not-extracted items for whether any blocking condition has since cleared (notably the
  residual 2-leg catalogue purge, which needs its own fresh operator confirmation), then archives batch9 via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-17"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
  ]
depends_on: [tradfi_satellite_ao_dispatch_batch9_2026_08_09]
gate_on_depends: true
source: >-
  Targeted satellite-batch extraction (2026-08-09), per task_template.md §4's finalize-plan-coverage rule.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 9 — finalize

**status: active — gated on batch9's 2 todos via `depends_on` + `gate_on_depends: true`.**

## Todos

- [ ] [REVIEW] P1. **Source-doc reconciliation**: confirm both source docs show their corresponding item closed —
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s ICE-Databento parquet GCS-cleanup todo, and
      `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s MDPS-ohlcv-aggregator
      `[DESIGN]` todo — either flipped `[x]` with the batch9 commit citation, or annotated with a pointer to it. Repo:
      unified-trading-pm. Done when: both source docs' items are closed-by-citation with no orphaned "still looks open"
      gap.
- [ ] [DOC] P2. **Re-check the residual 2-leg tradfi catalogue purge** (NASDAQ/NYSE mis-classified `SPOT_PAIR` rows +
      the 12 cefi-singles' EQUITY rows, `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`) for whether the
      operator has since given it the same explicit confirmation the ICE-parquet item got — if so, it becomes a clean
      batch10 candidate. Repo: unified-trading-pm. Done when: an explicit still-held / cleared verdict is recorded.
- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): confirm todo 2's verdict is recorded, add
      the archived-banner cross-reference, run the post-phase codex audit, confirm no new CLAUDE.md contract is owed,
      update every corpus referrer, `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch9 is
      at its archived path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside batch9,
  `status: active`, gated via `depends_on` + `gate_on_depends: true`. No work started — waiting on batch9's dispatch
  - completion.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
