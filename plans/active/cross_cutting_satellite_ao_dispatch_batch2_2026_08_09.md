---
doc_type: plan
title:
  Cross-cutting satellite AO batch 2 — instruments_master bounded residuals extracted from the 2026-08-09
  satellite-batch-extraction sweep
summary: >-
  Second AO-dispatch batch for the cross-cutting tranche, produced by a satellite-batch-extraction pass (mirroring
  `/ag-closeout-audit`'s pattern) over the 27 `assigned_vm: NA` cross-cutting docs that did NOT qualify for a whole-doc
  RECLASSIFY flip earlier the same day. Unlike a whole-doc flip, this pulls out only the specific bounded,
  worker-determinable items from 5 `instruments_master` source docs —
  `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (7 items),
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (5 items),
  `instruments_completion_tracker_2026_07_06.md` (4 items),
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (4 items),
  `mvp_scope_catalogue_tagging_2026_06_08.md` (1 item), and `is_catalogue_g1_root_audit_log_2026_07_24.md` (1 item) —
  leaving every genuinely gated item (design/sourcing decisions, whole-corpus single-walk migrations, whole-bucket
  destroys, `[OPERATOR]`-tagged items) untouched in its source doc. One candidate item (a `_bucket_for`
  prediction-bucket fix in the CF-canonicalization doc) was found already shipped (`instruments-service@0975de10`, cited
  in `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`) with only a stale un-flipped checkbox — left alone for
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md`'s existing source-doc reconciliation todo rather
  than re-extracted here. One item (`mvp_scope_catalogue_tagging_2026_06_08.md`'s real-data MVP-toggle verify) was
  dropped on a confirmed conflict — it duplicates an already-open todo inside the active
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    deployment-api,
    deployment-ui,
    unified-api-contracts,
    ml-service,
    unified-trading-library,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, instruments-master]
related:
  [
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.5
estimate_calibrated_ai_days: 4.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Satellite-batch-extraction sweep 2026-08-09 (8 parallel classification agents over the cross-cutting tranche's 27
  RECLASSIFY-non-qualifying NA docs), mirroring `/ag-closeout-audit`'s satellite-batch pattern per operator instruction
  — pulled bounded, worker-determinable items out of otherwise-gated docs rather than flipping whole docs.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 2 (instruments_master) — bounded-item extraction

> **Status: active** (operator-dispatched satellite-batch-extraction run, not a skill draft). All 22 todos below are
> same-priority-independent and touch distinct files/repos — no `sequential`/`gate_on_depends` needed. Each todo cites
> its source doc; do NOT flip the source doc's own checkbox directly — this batch's finalize twin
> (`cross_cutting_satellite_ao_dispatch_batch2_2026_08_09_finalize.md`) reconciles every source doc once this batch is
> done.

## Todos

- [ ] [INFRA] P0. Wire observability (§0.5 of the source doc) for every TradFi/sports/prediction instruments/MTDS
      backfill VM + roll-up job — register each as a classified `DeploymentTarget` via `ServiceBootstrap` +
      `log_event` + heartbeat, mirroring the already-shipped + prod-verified cefi pattern (cited as GATE-G2 evidence in
      the source doc), so each appears click-through-able in the `/deployments` BATCH tab. Repo: instruments-service,
      market-tick-data-service, deployment-service. Source: `instruments_foundation_phase0_cross_cutting_2026_07_24.md`
      (Phase-0 item 1). Done when: TradFi/sports/ prediction backfill VMs + roll-up jobs are click-through-able in
      `/deployments`, verified via `/api/deployments/inventory`, same evidence bar as cefi's cited GATE-G2 verification.
- [ ] [BACKEND] P0. Surface the already-shipped Honest-Coverage v2 layered-coverage fields
      (`layer1_completeness_pct`/`instrument_gates_download`/`denominator_complete`, `schema_version==2`, producer
      already live) through deployment-api and deployment-ui — today there are 0 grep hits for those field names in
      either repo. Repo: deployment-api, deployment-ui. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 2). Done when: deployment-api exposes
      the 3 named fields per asset_group/venue; deployment-ui renders the two-layer number (Layer-2 visually gated on
      Layer-1); a synthetic-gap test fixture proves the correct layer drags down; `pw:L2 ✓` + a regression spec per the
      playwright gate.
- [ ] [SCRIPT] P0. Build the captured∩expected KEY-OVERLAP verification-discipline gate (per-(instrument, day) overlap
      of captured vs. expected, never a raw VM-exit-code/row-count proxy) that would have caught the 2026-06-24 DeFi
      silent-stall class. Repo: instruments-service. Source: `instruments_foundation_phase0_cross_cutting_2026_07_24.md`
      (Phase-0 item 7). Done when: a script/gate computes the `expected_unattempted`-drop /
      captured∩expected-overlap-climb as the wired backfill-completion verdict, cross-checked against `run.log`
      `exit_code`, and demonstrably fails on a synthetic "exit 0 but empty" fixture.
- [ ] [SCRIPT] P0. Run the silent-cap source audit + `FetchEvidence`/`UnprovenHonestAbsenceError` paging sweep across
      every data source (find + fix any REST page-limit/top-N-snapshot/free-tier-window cap that silently truncates,
      mirroring the already-shipped Graph `skip<=5000`-to-cursor fix). Repo: instruments-service,
      market-tick-data-service. Source: `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 8).
      Done when: every source's page/snapshot/window cap is enumerated and checked; any found cap is fixed to page past
      it; the keystone `FetchEvidence` gate stays green fleet-wide.
- [ ] [DATA] P1. Register the TradFi Databento cost/entitlement-boundary case (~241k cells beyond the free window) in
      the already-shipped `COVERAGE_EXCLUSIONS` registry, using the already-shipped
      `EmptyConfirmedReason.EXPECTED_UPSTREAM_OUT_OF_BOUNDS` reason class — the mechanism exists, this one
      already-quantified case is simply unregistered. Repo: unified-api-contracts. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 10). Done when: `COVERAGE_EXCLUSIONS`
      carries a TradFi entry with a valid `evidence_uri` + re-runnable `evidence_probe`; the ~241k cells report
      `EXPECTED_UPSTREAM_OUT_OF_BOUNDS` instead of a plain gap.
- [ ] [INFRA] P0. Rebuild the IS daily-definition producer for TradFi/sports/prediction, mirroring the already-shipped
      and prod-verified cefi + defi producers (24/53 venues verified) — the tradfi child plan confirms
      tradfi/sports/prediction currently have NO prod daily producer at all. Repo: instruments-service. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 12). Done when: TradFi/sports/prediction
      each have a verified prod daily producer, confirmed via a dated venue-count run log matching the cefi/defi
      evidence bar.
- [ ] [CODE] P1. Build the granularity-aware catalogue producer for prediction (per-cqg grain) and sports (per-league
      vs. per-fixture grain), mirroring the already-shipped shape-aware producer for cefi/tradfi/defi
      (`instruments-service@6ea46565`). Repo: instruments-service. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 13). Done when: prediction and sports
      each have a granularity-aware catalogue producer; per-asset_group `_enumerate_v2_*` is verified to emit
      `expected_unattempted` against the real universe for all 5 asset_groups.
- [ ] [INFRA] P2. Move the research availability index off the legacy `perp-funding`/`lst-rates` buckets onto their
      `-prd-` twins — add the 4 named `manifest_consolidator_buckets` Terraform entries + IAM, repoint
      `record_research_perp_ctx_manifest.py`'s `INDEX_BUCKET` via `resolve_bucket_name`, one-shot seed-copy the legacy
      `_index` to the `-prd-` twins, verify post-copy freshness. Repo: deployment-service, instruments-service. Source:
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (steps 1-4 of the 5-step item; step 5, a future
      delete, is out of scope here). Done when: the 4 Terraform entries + IAM bindings land; `INDEX_BUCKET` resolves via
      `resolve_bucket_name`; the legacy `_index` is seeded onto both `-prd-` twins; freshness on each bucket is under
      the staleness threshold.
- [ ] [DATA] P3. Verify-then-delete the ~122 genuinely-legacy-only TradFi stragglers in
      `market-data-tick-tradfi-prd-central-element-323112` — named bucket, TWIN-VERIFIED-SAFE-only scope, GCS
      soft-delete retention already confirmed >= 604800s (reversibility-verified per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — no `[OPERATOR]` tag needed). Repo:
      instruments-service. Source: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (L627 item). Done
      when: the delete-list is spot-checked against the twin-verify parquet; `gcs_delete_object` runs on the confirmed
      TWIN-VERIFIED-SAFE set only; a post-delete scan shows 0 objects deleted without a verified twin.
- [ ] [DATA] P1. Confirm or resume the KRAKEN-SPOT/KRAKEN-FUTURES 6-year instruments-service backfill (F1) — it was
      reported RUNNING with an ETA of ~1h as of 2026-06-18/19 and the checkbox was never revisited; check the manifest
      for KRAKEN-SPOT/FUTURES coverage 2020-01-01→present before assuming it's still running. Repo: instruments-service.
      Source: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (F1 item). Done when: a fresh manifest
      scan confirms KRAKEN-SPOT/FUTURES coverage reaches the present day (flip with that evidence), or, if the backfill
      genuinely stalled, it is resumed to completion.
- [ ] [CODE] P2. Unify TradFi's two disagreeing options encodings (`instrument_type=options_chain` vs.
      `data_type=options_chain` + blank `instrument_type`) and stamp `instrument_type` on the ~182k blank-type cells
      this produces — a pure typing/normalization fix, not a data-gap judgment call. Repo: instruments-service. Source:
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (F6 item). Done when: a fresh manifest count
      shows 0 blank-`instrument_type` cells remaining among the previously-182k population.
- [ ] [INFRA] P1. Delete the legacy GCS duplicate objects in `market-data-tick-cefi-prd-central-element-323112`
      (cefi-only today, ~1.08M objects / ~9.98TB) — restricted to `gcs_describe_object`-verified bare-canonical-twin
      objects only, GCS soft-delete retention already confirmed >= 604800s (reversibility-verified per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a). **Flagging scale for extra operator awareness
      even though this clears the stated bar** — this is the largest single delete in this batch; a worker picking this
      up should re-confirm the twin-verify output immediately before running, not trust a stale prior pass. Repo:
      instruments-service. Source: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (Phase D item).
      Done when: the per-cefi delete-list is freshly spot-checked against twin-verify output; `gcs_delete_object` runs
      (in-region VM, workers=32) on the confirmed bare-twin population only; a post-delete scan shows 0 objects deleted
      lacking a verified canonical twin.
- [ ] [BACKEND] P2. P2b-2 — wire the models data-status coverage consumer: extend the already-shipped
      `scope=mvp|could_exist|all` pattern (`deployment-api@3390c98`) to ml-service model output, reading the
      already-shipped `is_model_mvp()` predicate (`unified-api-contracts@0fb9821b`). Both design sub-questions this item
      was previously blocked on are resolved per the source doc's own inline 2026-08-08 note: `TrainingGridConfig`
      (`ml-service/ml_service/training/app/core/config_loader.py`) is the could-exist bound;
      `ModelRegistry.list_models()` (`unified_trading_library/ml/model_registry.py`) is already the live trained-model
      write path. Repo: deployment-api, ml-service, unified-api-contracts. Source:
      `mvp_scope_catalogue_tagging_2026_06_08.md` (P2b-2 item). Done when: a new/extended endpoint carries a
      `scope=mvp|could_exist|all` param over ml-service model output, filtering via `is_model_mvp()` with
      `TrainingGridConfig` as the could-exist universe and `ModelRegistry.list_models()` as the captured set; a parity
      test asserts `mvp <= could_exist <= all` monotonicity (mirroring `test_route_venue_year_coverage_scope.py`).
- [ ] [CODE] P1. Fix `_fetch_earliest_funding_date` (instruments-service `cefi/aster.py`) to exclude the synthetic
      pre-launch placeholder funding rows (flat `0.0001` rate) before deriving `available_from_datetime` — these rows
      currently pull ASTER's stamped genesis date earlier than the true launch. Repo: instruments-service. Source:
      `instruments_completion_tracker_2026_07_06.md` (Stage-2 ASTER genesis item). Done when: the fix excludes synthetic
      placeholder rows before deriving `available_from_datetime`; a regression test asserts ASTER genesis no longer
      stamps a pre-2023-07-22 date from placeholder rows.
- [ ] [REVIEW] P1. Reconcile ASTER's two disagreeing missing-date counts: the manifest cell-presence view reports 0
      missing dates for a venue+window where the live turbo API reports 11 missing / 1,071 expected for the SAME
      venue+window — determine whether this is a methodology difference between the two code paths or a real bug, and
      document the recommended trusted count. Repo: instruments-service. Source:
      `instruments_completion_tracker_2026_07_06.md` (Stage-2/3 ASTER count-discrepancy item). Done when: the root cause
      of the 0-vs-11 discrepancy is identified and documented with a recommendation for which count the Stage-3
      re-measure should trust.
- [ ] [CODE] P1. Add a build-time exclusion filter to `build_instrument_catalogue.py`'s `build_catalogue_dataframe` so
      `venue=ICE`, `venue=CBOE AND instrument_type IN (OPTION, SPOT_PAIR)`, and the 2 VIX-cash `INDEX` instrument ids
      are excluded from every future catalogue rebuild — mirrors an already-executed one-off purge, making it permanent.
      Repo: instruments-service. Source: `instruments_completion_tracker_2026_07_06.md` (Stage-1 catalogue-purge item).
      Done when: the filter lands; a fresh `build_instrument_catalogue` run excludes those rows.
- [ ] [SCRIPT] P1. Widen the systemic unregistered-handler audit to the adapter-factory layer: diff every DeFi
      protocol/adapter handler class registered in `factory.py` against `cli/main.py` + `deployment-service/scripts/vm/`
      invocation sites, classify each as built-but-unwired vs. genuinely-not-built (mirroring the already-fixed
      Deribit/Renzo precedent), and register+test-fix the built-but-unwired ones. Repo: instruments-service. Source:
      `instruments_completion_tracker_2026_07_06.md` (Stage-6 systemic-handler-audit item). Done when: every DeFi
      protocol/adapter in `factory.py` is checked against its dispatcher/invocation sites; built-but-unwired handlers
      get register+test fixes; genuinely-not-built ones are filed as new issue docs (not built here).
- [ ] [CODE] P1. CF-5 — make instruments-service writers (non-sports asset_groups) emit typed `EmptyConfirmedReason`
      enum values at every empty-write call site, and route genuine fetch-failures to `attempted_failed` rather than
      `empty_confirmed` (the CF-11 swallow-sweep target). Repo: instruments-service. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (CF-5 item). Done when: non-sports-asset_group
      writers route genuine fetch-failures to `attempted_failed`, not `empty_confirmed`, and emit typed
      `EmptyConfirmedReason` values at every write call site; a regression test covers both.
- [ ] [REVIEW] P2. Land the bar-edge fallback-to-open fix — the source doc's own text claims it was committed as
      `instruments-service@20a92886`, but that SHA does NOT resolve to a real commit in any local clone (verified
      2026-08-09) — treat the "already committed" claim as unverified, not fact: re-derive whether the fix (raise
      on unsupported timeframe instead of silently falling to the open edge, in `ccxt_adapter.py` and any sibling
      adapter) actually exists on `live-defi-rollout` today; if not, (re)implement it. Repo: instruments-service.
      Source: `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (bar-edge-fallback item). Done when: IS
      `quality-gates.sh` is confirmed green (or RB-d3bb9020's current status is re-verified); the fix is confirmed
      present with a REAL, resolvable commit SHA cited (or freshly implemented + committed); if still blocked, the
      checkbox is left open with a freshly-dated status note
      (not silently re-committed).
- [ ] [CODE] P3. Swap the hand-maintained MTDS `_instruments_metadata.py` venue-prefix-map mirror for a direct import of
      UAC's `VENUE_PREFIX_TO_PROTOCOL` (removing the duplicate mapping); also fix the stale comment in
      `unified-trading-system-ui/lib/types/defi.ts` naming the already-deleted `CANONICAL_VENUE_TO_ADAPTER`. Repo:
      market-tick-data-service, unified-trading-system-ui. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (prefix-map-mirror item). Done when:
      `_instruments_metadata.py` imports `VENUE_PREFIX_TO_PROTOCOL` from `unified-api-contracts` instead of a
      hand-mirror; the stale UI comment is corrected.
- [ ] [SCRIPT] P3. Cloud-agnostic + hygiene sweep of instruments-service's script tier: replace ~60 scripts' direct
      `google.cloud`/`boto3` imports with `get_storage_client()`, replace ~30 inline legacy bucket-name literals with
      `resolve_bucket_name`, and replace the hardcoded `/tmp/` in `enumerate_expected_universe.py` with
      `tempfile.gettempdir()` — all three map directly to existing QG-enforced bans. Repo: instruments-service. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (script-tier cleanup item). Done when: zero
      direct `google.cloud`/`boto3` imports and zero inline legacy bucket literals remain in instruments-service
      scripts; the named `/tmp/` hardcode is replaced; `quality-gates.sh` green.
- [ ] [DATA] P2. G1.run-full-history — extend the bounded-window `expected_unattempted` seed to the full 2018-to-today
      per-instrument universe (~190M rows fleet-wide), per the operator's unconditional 2026-08-08 approval (NA-corpus
      blocker digest round 5, id=53 — "approved, yes, extend to full history"; no fresh `[OPERATOR]` gate needed, cite
      this ruling). Additive-only (seeds `expected_unattempted` rows, never touches captured data), mirroring the
      already-successful `G1.run-bounded` precedent. **Run the `--dry-run` sizing check FIRST and report the actual
      per-asset_group row counts before any `--apply-write`** — do not proceed to apply-write if the dry-run count is a
      surprise multiple of the 2026-06-19 ~190M estimate; treat that as a stop-and-report condition, not a green light.
      Repo: instruments-service. Source: `is_catalogue_g1_root_audit_log_2026_07_24.md` (G1.run-full-history item). Done
      when: per-asset_group `--dry-run` sizing checks land in the expected ballpark; `--apply-write` runs on VM(s) per
      the vm-launcher-runbook (SPOT); post-run verification shows `expected_unattempted` counts in range with captured
      rows preserved and the consolidator green.

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility",
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, `/codex/05-infrastructure/vm-launcher-runbook.md`.

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep (8 parallel classification agents over the
  cross-cutting tranche's 27 non-qualifying NA docs). 22 items extracted from 6 `instruments_master` source docs. 1
  conflict found and resolved (a `_bucket_for` prediction-bucket fix already shipped via `instruments-service@0975de10`
  — left for the existing `batch1_finalize` reconciliation rather than re-extracted); 1 item dropped on a confirmed
  conflict with an already-open todo in `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`.
