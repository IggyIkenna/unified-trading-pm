---
doc_type: plan
title: Finalize — DeFi satellite AO batch 17 close-out
summary: >-
  Gated finalize companion for defi_satellite_ao_dispatch_batch17_2026_08_18.md — re-verifies each of the 2 todos'
  reported findings against the source doc's own citations, folds any newly-confirmed gap back into
  mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md, then archives both docs per
  plan-completion-and-archival-discipline once every todo is done.
status: complete
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, finalize, batch-17, archival, mev]
related:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch17_2026_08_18.md,
    /plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: quant_dev
effort: low
thinking_tier: mechanical
depends_on: [defi_satellite_ao_dispatch_batch17_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch17_2026_08_18.md,
    /plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  na-eligibility-audit 2026-08-18 — every AO-dispatched satellite batch needs a gated finalize companion
  (/plans/active/task_template.md §4).
drift_direction: advance-code
---

> **🟢 COMPLETE 2026-08-20 — ARCHIVED.** The REVIEW todo (independent re-verification of both batch17 findings) landed
> 2026-08-20; the archival todo completed in this commit — `defi_satellite_ao_dispatch_batch17_2026_08_18.md` and this
> finalize doc moved to `plans/archive/2026_08/`, corpus referrers repointed, active index + inventory regenerated.

# Finalize — DeFi satellite AO batch 17 close-out

Machine-held (`gate_on_depends: true`) until every todo in `defi_satellite_ao_dispatch_batch17_2026_08_18.md` is done.
Do not start manually before then.

## Todos

- [x] ✅ [REVIEW] P2. Re-verify both of batch17's todos' reported findings independently (don't trust the batch doc's own
      checkbox alone) — for the Tenderly call-site confirmation, re-grep the 3 MEV engine files directly; for the
      `liquidation_bundle.py:265-267` default-behavior confirmation, re-read the exact lines against current code
      (they may have moved). Correct any mis-citation found in the batch doc itself. Fold whatever was actually found
      back into `mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`'s own text (e.g. if the Tenderly
      call is confirmed absent, that doc's todo 1 should note the confirmed gap rather than staying an open question;
      if the default is confirmed `None`/raising, note that against todos 3/5 which depend on knowing it). Done-when:
      both todos independently re-verified with cited evidence, source doc updated to reflect what was found.
      **DONE 2026-08-20 (slot-7 review, re-verified against current code):** (1) Tenderly call-site CONFIRMED ABSENT —
      3 MEV engines import only `unified_api_contracts.internal` + sibling `strategy_service` modules (zero
      Tenderly/simulate/gate_or_advise refs); `gate_or_advise()` has zero production callers; `simulate_bundle()`'s only
      production caller is `gate_or_advise` (`tenderly.py:484`); `matching_engine.py` names Tenderly only in docstrings +
      raises `NotImplementedError` for EVM DeFi legs. (2) default behavior CONFIRMED — `_candidate_from_features` moved to
      `liquidation_bundle.py:271-303` (was 265-269): `.get(id_key)` no-default → `None` → `on_tick()` continues. Two
      corrections folded into the source doc: `liq_candidate_health_factor_<id>` is NOT a feature key (margin-health-cache-
      derived), and §"Bundle-simulation" flipped "Not confirmed"→"Confirmed absent". Batch doc "265-269" line range noted stale.
- [x] ✅ [DOC] P2. Once every batch17 todo + the REVIEW todo above are done: run the standard 6-step
      plan-completion-and-archival-discipline ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `defi_satellite_ao_dispatch_batch17_2026_08_18.md` and this finalize doc itself — archive both to
      `plans/archive/2026_08/`, fix every corpus referrer path. Done-when: `regenerate_active_plan_inventory.py` shows
      zero orphan referrers to the archived paths.
      **DONE 2026-08-20 (slot-7):** both docs archived to `plans/archive/2026_08/`; referrers repointed
      (`mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md` related+source; source issue doc extraction
      notes); active index + inventory regenerated. Two na-eligibility incident-narrative docs intentionally left
      untouched — their `batch17` references recount a retracted same-name draft (deleted pre-commit), not the
      archived live plan.

## Progress Log

- **2026-08-18 (na-eligibility-audit, defi tranche, dispatch agt-2c8a26)**: finalize plan authored alongside batch17's
  draft, per `task_template.md`'s finalize-plan-coverage rule.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-20 (slot-7 review)**: REVIEW todo done — both batch17 findings independently re-verified + CONFIRMED; two
  corrections folded into `mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` (health_factor not a
  feature key; Tenderly "confirmed absent"). Archival todo (todo 2) remains open — not this pass's scope.
- **2026-08-20 (slot-7)**: archival todo (todo 2) DONE — 6-step ritual completed. Both docs archived to
  `plans/archive/2026_08/` (COMPLETE banners; `superseded_by` on batch17 → the two open MEV issue docs); referrers
  repointed in `mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md` (related+source) and the source
  issue doc's extraction notes; `regenerate_active_plan_inventory.py` + `regenerate_active_plan_index.py` re-run —
  zero orphan referrers to the archived paths in the active corpus.
