---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 18 — 2026-08-19
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-19 /na-eligibility-audit sweep (slot 30,
  na_eligibility_auditor, dispatch agt-dc3dbe) — 10 conflict-cleared, bounded/deterministic items pulled from 2
  source docs (RECLASSIFY per-todo split each). 3 items (latency measurement, a preflight_gate code-read, a
  dead-doc-reference cleanup) from `execution_delta_proxy_repricer_generalization_2026_08_18.md` — pure
  read/measure/cleanup tasks independent of that doc's 11 unresolved operator judgment calls, touching no
  live-execution behavior. 7 items from `plan_reconciler_findings_cross_cutting_2026_08_18.md`'s own "Plans not
  reached" section — bounded doc-hygiene fact-corrections (dangling refs, stale counts, frontmatter copy-paste
  leftovers, citation backfills), several with the correct value already grep-verified in-doc by the filing run.
  Each item cites its exact source doc + todo; the source docs' own extracted checkboxes are flipped with a
  citation in the same audit pass, not deferred to this batch's finalize. Conflict-checked against every active
  planning doc in the relevant parent_epics, the cross-cutting consolidated closeout, every satellite batch
  corpus-wide (incl. reading batch13's own finalize plan directly, since its stated convention is to defer
  source-doc reconciliation there), and the archived citadel batch1 — no item here duplicates ground an existing
  dispatched todo already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, doc-hygiene, execution-architecture]
related:
  [
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: worker
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_18.md,
    execution-service/execution_service/engine/risk/preflight_gate.py,
    strategy-service/strategy_service/risk/core/exposure_aggregator.py,
  ]
source: >-
  /na-eligibility-audit cross-cutting tranche, dispatch agt-dc3dbe, slot 30, 2026-08-19. Each item's own Source:
  line below names the exact source doc + todo it was extracted from.
---

# cross-cutting satellite AO dispatch batch 18

## From `execution_delta_proxy_repricer_generalization_2026_08_18.md`

- [x] ✅ [REVIEW] P2. **Measure this deployment's real `EventTransport`/Pub/Sub round-trip latency** before permanently
      ruling out the delta-proxy-repricer pattern for `BACKRUN`/`LIQUIDATION_BUNDLE` — today's "12s block budget is
      generous enough" is reasoned, not measured. Done when: a real measured number is on record, compared against
      the 12s budget. Source: `execution_delta_proxy_repricer_generalization_2026_08_18.md` item at line 345.
      **DONE 2026-08-19 (slot 14)** — measured via `unified-trading-library@418ce99c`
      (`scripts/measure_event_transport_latency.py`; ephemeral topic + `-reader` sub on `central-element-323112`, no
      production topic / warm-GCS sink touched; n=20 × 2 runs). `PubSubTransport` publish→receive round-trip:
      median ~2.2–2.7s, p95 ~4.7–5.0s, max ~4.9–5.0s → ~18% of the 12s budget at median, ~39–42% at p95/max.
      Raw Pub/Sub publish→pull with persistent clients: median ~1.2s, p95 ~3.1s (publish itself ~40ms; the
      `GcpPubSubMessageBus` per-call client construction adds ~1s). **Verdict: "12s block budget is generous enough"
      is NOT borne out at the tail** — the seam alone consumes up to ~40% of the window before strategy detection /
      execution / relay are counted. Also confirmed: production `persist-*` topics carry only `warm-sink-*` GCS push
      subscriptions — no `-reader` pull subscriptions exist, so `PubSubTransport.read()` fails against them today.
      Follow-up tracked in `execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [x] ✅ [REVIEW] P2. **Confirm whether execution-service's `engine/risk/preflight_gate.py` reads strategy-service's
      real `ExposureAggregator`-computed net/effective exposure**, or maintains an independent view — a pure
      code-read fact-finding task (does it call ExposureAggregator or not), distinct from the normative "should it"
      judgment call the source doc leaves open. Done when: a definite yes/no is on record, evidenced by the code
      read. Source: `execution_delta_proxy_repricer_generalization_2026_08_18.md` item at line 363. **ANSWER: NO —
      preflight_gate.py does NOT read strategy-service's ExposureAggregator (0 repo-wide hits for
      ExposureAggregator/exposure_aggregator); same-named `gross_exposure_usd`/`net_exposure_usd` ctx keys are
      caller-supplied `account_state` only, and the sole prod call-site (`engine/orchestrator.py:246`) passes no
      `account_state` → unpopulated on the live path. Resolved 2026-08-19 (slot 7) — see Progress Log.**
- [ ] [AGENT] P3. **Resolve the dead `feedback_market_making_reference_price_model.md` reference** cited by both
      `vol_trading/options.py` (strategy-service) and `quote_maintenance.py` (execution-service)'s docstrings —
      confirmed not to exist anywhere in `unified-trading-pm`. Repoint both docstrings to
      `execution_delta_proxy_repricer_generalization_2026_08_18.md` (the closest real record of this design) since
      authoring a new standalone memo pre-design would be premature. Done when: both docstrings cite a real,
      existing path. Source: `execution_delta_proxy_repricer_generalization_2026_08_18.md` item at line 366.

## From `plan_reconciler_findings_cross_cutting_2026_08_18.md`

- [x] ✅ [DOC] P2. **`instruments_foundation_completeness_2026_06_24.md`** — repoint 2 dangling refs
      (`defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md` and
      `sports_fixture_completeness_oracle_2026_06_24.md`, both moved to `plans/archive/2026_06/`, cited at 3
      separate locations in this doc) + refresh the stale Phase-0 rolling-status table (claims 11 open, actual 6 —
      correct value already grep-verified against `instruments_foundation_phase0_cross_cutting_2026_07_24.md` by
      the filing plan_reconciler run). Multi-location edit in a large umbrella doc. Done when: both refs resolve to
      real paths and the rolling-status table reads 6. Source: `plan_reconciler_findings_cross_cutting_2026_08_18.md`
      "Plans not reached" item 1.
      **DONE 2026-08-20** — repointed all target-doc occurrences to `/plans/archive/2026_06/` and verified the Phase-0 child has 6 open todos.
- [x] ✅ [DOC] P3. ~~**`ag_closeout_audit_cross_cutting_parked_2026_08_08.md`** — its own 2026-08-16 "5 archived/6
      active" summary doesn't match its own itemized list immediately above it~~ — **SUPERSEDED 2026-08-19
      (ag-closeout-audit cross-cutting reconciliation pass)**: rather than re-counting a now-stale snapshot, this
      run verified all 13 mistag targets + the 1 orphan directly against live state, flipped every resulting todo,
      and archived this doc along with its 3 siblings (`_08_01`, `_08_06`, `_08_07.md`). The count-mismatch this
      item asked about no longer applies — there is no remaining "active" member of this doc family post-archival.
- [ ] [DOC] P3. **`is_catalogue_g1_root_audit_log_2026_07_24.md`** — `repos:` frontmatter lists 6 repos
      (agent-orchestrator, batch-live-reconciliation-service, deployment-api, deployment-service, deployment-ui,
      e2e-testing), none of which the doc's actual content touches (it's entirely instruments-service + UAC,
      neither currently listed) — copy-paste leftover from the 2026-07-24 extraction split. Correct the `repos:`
      list to match the doc's real content. Done when: `repos:` reads `[instruments-service, unified-api-contracts]`
      (or whatever the doc's actual content confirms). Source:
      `plan_reconciler_findings_cross_cutting_2026_08_18.md` "Plans not reached" item 4.
- [ ] [DIAG] P3. **`data_pipeline_e2e_milestones_gate_2026_07_24.md`** — a Deferred-work-table row still marked "IN
      PROGRESS" for the "Operator-requested broader audit pass, part 3" relay/triage step, whose stated completion
      condition (5 `/data-pipeline-reconciliation` reports, one per AG) has been met for 3+ weeks (all 5 exist at
      `plans/audit/results/data_pipeline_reconciliation_{defi,cefi,sports,prediction,tradfi}_2026_07_24.md`,
      361-495 lines each). Check whether the relay/triage step actually happened, update the row either way. Done
      when: a definite verdict (happened vs. didn't) is on record in the row. Source:
      `plan_reconciler_findings_cross_cutting_2026_08_18.md` "Plans not reached" item 5.
- [ ] [DOC] P3. **`live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`** — a stale inline YAML comment
      references a status/lock state that changed 2026-08-10/12; superseded in practice by the doc's later
      `archive_exempt: true` but still misleading to a reader. Correct or remove the stale comment. Done when: no
      comment in the doc references the pre-2026-08-10/12 status/lock state. Source:
      `plan_reconciler_findings_cross_cutting_2026_08_18.md` "Plans not reached" item 8.
- [ ] [DOC] P3. **`slot_collision_guard_bats_fails_open_under_host_load_2026_08_15.md`** — its na-eligibility-audit
      2026-08-17 Progress Log entry over-counted open items by 1 (described an already-`[x]` item as still open).
      Doesn't affect dispatch (assigned_vm already correct) — pure Progress Log text correction. Done when: the
      2026-08-17 marker's open-item count matches a fresh grep. Source:
      `plan_reconciler_findings_cross_cutting_2026_08_18.md` "Plans not reached" item 9.
- [ ] [DOC] P3. **`prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`** — 2 "DONE"/"shipped" Progress Log
      claims (the 2026-08-15 "Re-opened" and "Resolved... cicd escalation agt-f4b815" entries) cite a literal
      unfilled `<pending>` placeholder instead of a real commit sha. Identify which of several nearby commits (per
      `git log`) is the real one, backfill the citation. Done when: both entries cite a real, reachable commit sha.
      Source: `plan_reconciler_findings_cross_cutting_2026_08_18.md` "Plans not reached" item 10.

## Progress Log

- **2026-08-19**: drafted by na-eligibility-audit (cross-cutting tranche, dispatch agt-dc3dbe, slot 30). All 10
  items conflict-checked clear (see this doc's own `summary:` for surfaces checked).
- **context-scout 2026-08-19**: refreshed context_scope (4 entries) — added the two real code targets for the
  "does preflight_gate read ExposureAggregator" fact-finding todo
  (`execution-service/execution_service/engine/risk/preflight_gate.py`,
  `strategy-service/strategy_service/risk/core/exposure_aggregator.py`); the 7 doc-hygiene items from
  `plan_reconciler_findings_cross_cutting_2026_08_18.md` each fully name their own single target doc inline, so no
  further per-item entries added (would exceed the curated-list budget for marginal value).
- **2026-08-19 (slot 7, batch item 2 DONE)**: confirmed by direct code read — execution-service's
  `engine/risk/preflight_gate.py` does NOT read strategy-service's `ExposureAggregator`. Evidence: (1) repo-wide
  `rg` for `ExposureAggregator|exposure_aggregator` in execution-service = zero hits; (2) the module imports are
  UAC (`unified_api_contracts.risk`) + UTL (`risk_preflight`/`RuleEvalContext`) + execution-service-internal only —
  no strategy-service import; (3) `gross_exposure_usd`/`net_exposure_usd` are `RuleEvalContext` keys populated
  solely from an optional `account_state` dict (`_copy_account_state_into_ctx`), and the sole production call-site
  (`execution_service/engine/orchestrator.py:246` `execute_instruction`) calls `run_risk_preflight` with NO
  `account_state` — so on the live path those keys are unpopulated and `MaxGrossExposureTrigger`/
  `MaxNetExposureTrigger` rules are dropped by `_can_evaluate` (silently skipped, not independently computed). It
  maintains an independent (caller-supplied, live-unpopulated) view; the two services' same-named fields are a
  dual-path shape with no verified single source of truth. Confirms the source issue doc's own judgment-call-10
  resolution (execution_delta_proxy_repricer_generalization_2026_08_18.md).
- **2026-08-19 (slot 14)**: item 1 (EventTransport/Pub/Sub round-trip latency measurement) DONE — see the checkbox
  annotation for full measured numbers + comparison vs the 12s block budget. Shipped
  `unified-trading-library@418ce99c` (`scripts/measure_event_transport_latency.py`, ephemeral topic + `-reader` sub
  on `central-element-323112`). Two subsidiary findings recorded in
  `execution_delta_proxy_repricer_generalization_2026_08_18.md`: (a) no `-reader` pull subscriptions are
  provisioned on production topics — `PubSubTransport.read()` fails there today; (b) the "12s budget is generous
  enough" claim is NOT borne out at the tail (~39–42% of budget consumed at p95/max by the seam alone, before
  strategy detection / execution / relay are counted).
