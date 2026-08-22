---
doc_type: plan
title:
  DeFi satellite AO batch 14 — bounded-item extraction from the 2026-08-16 /ag-closeout-audit defi orphan sweep
summary: >-
  Satellite-batch extraction from `/ag-closeout-audit defi`'s 2026-08-16 run (27 never-cited candidate docs deep-
  classified via a Workflow, one agent per doc — 12 exclude_cross_cutting, 14 orphaned_never_touched, 1
  archivable_after_planned_work). Of the 14 genuine defi orphans, 8 carry conflict-clear, worker-determinable bounded
  items — including one that is currently keeping `market-tick-data-service` `quality-gates.sh` RED
  (`mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md`'s hardcoded-URL finding) and one whose
  fleet-wide block is only suppressed via `xfail(strict=False)`, not actually fixed
  (`instruments_service_defi_golden_red_capability_drift_2026_08_14.md`). Conflict-checked against every active defi
  covering doc (consolidated closeout + satellite batch2/6/9/11 + finalize pairs + the 4 new 2026-08-15/16 named
  dispatch docs + solana_dex_pool_swaps_indexer + strategy_service_centralization_fixes + track01/track5) — zero
  collisions found (every extracted item had zero prior citations anywhere in that set, confirmed per-doc by the
  Phase-1 Workflow). The other 6 orphaned docs are genuinely non-batchable this round: 5 operator/design-gated
  (relaunch-vs-wait judgment, a credential-ask, a strategy-domain venue-universe inclusion call, an adapter-family
  delete-vs-wire fate call, and an annualization-noise smoothing methodology call touching a live liquidation-risk
  calc) and 1 time/dependency-gated (a close-out condition waiting on a different doc's dispatcher-wiring work). One
  further orphan (`karak_decommission_2026_08_16.md`, ~30 items) is deliberately excluded even from the Deferred
  section below — the operator already explicitly ruled it a Human (non-AO) plan.
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    market-data-processing-service,
    market-tick-data-service,
    deployment-service,
    instruments-service,
    execution-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-14, orphan-extraction, ag-closeout-audit]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md,
    /plans/active/issues/dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md,
    /plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md,
    /plans/archive/2026_08/issues/defi_dex_pool_density_drop_pool_level_followup_2026_08_14.md,
    /plans/active/issues/pendle_venue_onboarding_2026_08_16.md,
    /plans/active/issues/dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md,
    /plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
depends_on: []
source: >-
  `/ag-closeout-audit defi` (2026-08-16, slot 19, dispatch agt-952290) Phase 1 Workflow deep-classification of the 27
  never-cited AG-primary candidate docs (`generate_ag_closeout_audit_candidates.py --tranche defi`: 94 members, 29
  covering docs, 27 never-cited). Every item below cleared the shared conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) against every active defi
  covering doc. Per-item Source: citations below point at the exact originating doc.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 14 — 2026-08-16

Extracted from the 2026-08-16 `/ag-closeout-audit defi` run's 14 `orphaned_never_touched` docs (of 27 never-cited
candidates deep-classified). Every todo below cleared the shared conflict-check
([`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
§3) against `defi_consolidated_closeout_2026_07_18.md` and every active satellite/AO-dispatch batch
(batch2/6/9/11 + finalize pairs, `defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16`,
`defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16`, `defi_live_poller_ao_dispatch_batch1_2026_08_16`,
`defi_operator_ruling_ao_dispatch_2026_08_15`, `solana_dex_pool_swaps_indexer_2026_08_08`,
`strategy_service_centralization_fixes_2026_08_16`, `defi_track01_per_instrument_and_canon_id_2026_07_24`,
`defi_track5_coverage_mvp_backfill_2026_07_24`) — the Phase-1 Workflow's per-doc agents each independently confirmed
zero citations of their target doc anywhere in that set before returning an `orphaned_never_touched` verdict, so no
separate re-grep was needed to establish "no overlap" for these 8 items.

## Todos

- [ ] [CODE] P1. **Route MTDS's hardcoded Morpho URL through the UAC registry.**
      `market_tick_data_service/cli/handlers/_oracle_prices_constants.py:556`'s `_MORPHO_BLUE_API_URL` is a bare
      `https://blue-api.morpho.org/graphql` literal; route it through `get_evm_protocol_rest_url("morpho")` from
      `unified_api_contracts.registry`, matching the pattern every other EVM-protocol REST endpoint in that file
      already uses. This is the sole remaining reason `market-tick-data-service`'s `quality-gates.sh` bare-literal
      scanner is red (the doc's sibling sports-contract-regression finding is already resolved+verified). Repo:
      market-tick-data-service. Source: `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/active/issues/mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md` todo 1. Done when:
      the literal is gone, `get_evm_protocol_rest_url("morpho")` is used instead, and MTDS `quality-gates.sh` is
      green on this finding.
- [ ] [SCRIPT] P1. **Reconcile + regenerate the defi expected-universe golden; scope the regen tool per-asset-group.**
      `instruments-service`'s `defi.json` golden has been stale since 2026-08-08 relative to the AAVE_V3 rewards
      question: `unified-api-contracts@9e44d861` (2026-08-09) removed AAVE_V3 rewards, then
      `unified-api-contracts@6a001ea4` (2026-08-11) deliberately re-declared them — determine which side is
      currently correct against live UAC state, then lockstep-regenerate `defi.json` to match. The fleet-wide
      quickmerge block this caused is currently only suppressed via `pytest.mark.xfail(strict=False)` on
      `test_expected_universe_golden.py`'s `[defi]` case (commit `da6e556e`), not actually fixed — remove the xfail
      once the golden is reconciled. Separately, scope `regenerate_expected_universe_golden.py` to accept
      `--asset-group` so a future single-AG regen doesn't carry fleet-wide (incl. tradfi near-miss) blast radius.
      Repo: instruments-service. Source: `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md` todos 1 and 2
      (**corrected 2026-08-18, plan_reconciler**: that doc's Todos section has only 2 items, not 3 — was "todos 1
      and 3"). Done
      when: `defi.json` matches the current UAC AAVE_V3 declaration, the `xfail` suppression is removed with the
      real test passing, and `regenerate_expected_universe_golden.py --asset-group defi` regenerates only the defi
      golden.
- [ ] [DATA] P2. **Relaunch the legacy-fold VM with the fixed worker count; investigate the lock-reclaim gap.**
      **Safe-idempotent (added 2026-08-18, plan_reconciler, re-flagging a prior reconciler's untagged-VM-launch
      finding)**: standard SPOT backfill VM relaunch — resumes from measured progress per
      `/codex/05-infrastructure/spot-vms-for-backfill.md`, deletes no data, preemption-safe by design; no
      `[OPERATOR]` gate needed. Relaunch the `backfill-defi-legacy-datatype-fold-*` VM with `--workers 12` (the fix
      for the prior OOM/zombie run); if a repeat zero-heartbeat zombie recurs, capture the VM's serial console output
      before any further remediation; separately investigate the observed ~70-minute `consolidator.lock` reclaim gap
      during the prior run. Repo: deployment-service. Source: `defi_satellite_ao_dispatch_batch14_2026_08_16.md`
      extracted from `plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`. Done
      when: the fold VM completes cleanly (or a captured serial-console zombie repro exists to escalate) and the
      lock-reclaim-gap investigation's root cause is documented.
- [ ] [BACKEND] P2. **Add an internal per-shard timeout bound to the MDPS per-date subprocess.**
      The `mdps-defi-2022` DP-VM-001 single-date hang had no timeout below the launcher's outer
      `STALL_TIMEOUT_SEC` — add an internal per-date subprocess timeout so a single stuck date fails fast instead of
      hanging the whole shard. Repo: market-data-processing-service. Source:
      `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/active/issues/dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md` (BACKEND item only —
      the doc's separate OPERATOR relaunch-vs-wait decision is deferred below, not extracted here). Done when: the
      per-date subprocess enforces an internal timeout shorter than the launcher's outer stall timeout, verified
      against a live or simulated slow-date run.
- [ ] [DIAG] P2. **Align the DeFi staleness-alert budget with the manifest-consolidator lock TTL.**
      `market-data-tick-defi-prd`'s staleness-alert budget is hardcoded at 3600s while
      `CONSOLIDATOR_LOCK_TTL_SECONDS=9000s` — diagnose which value is actually correct given the two systems' real
      timing relationship (the lock TTL governs how long a legitimate consolidator run may hold the lock; the
      staleness alert should not fire inside that window), align the mismatched constant across every consumer
      (MDPS preflight, fleet monitor), then re-verify the doc's 2 named sibling docs' closability now that this is
      resolved. Repos: market-data-processing-service, deployment-service. Source:
      `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/active/issues/dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md`. Done when:
      the staleness-alert budget and the lock TTL are consistent across every consumer, with the sibling docs'
      closability re-verdicted with citations.
- [ ] [DIAG] P2. **Run the DEX-pool density-drop census.**
      Census distinct tracked pool/instrument ids per venue for `dex_pool_state`/`dex_pool_swaps` — known-good
      window vs the recent window — and check the drop against the named venue retirement's actual pool-removal
      scope to classify each drop as retirement-explained vs unexplained. Repo: instruments-service. Source:
      `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/archive/2026_08/issues/defi_dex_pool_density_drop_pool_level_followup_2026_08_14.md`. Done when: the census
      produces a per-venue density-drop table with each drop classified retirement-explained vs unexplained.
- [ ] [BACKEND] P2. **Wire the Pendle venue's execution-service dispatch + UAC SIT invariant registration.**
      Resolve the `pendle_markets` config, wire `PendleConnector` into `DeFiAdapter`'s `_dispatch_defi_operation`
      dispatch table, and add `pendle` to the UAC SIT invariant's `DEFI_VENUE_TO_CONNECTOR_CLASS` and
      `DEFI_VENUE_TO_GATE_MARKER` maps (internally sequential within this one todo — config must resolve before the
      dispatch wiring can be verified end-to-end). Repos: execution-service, unified-api-contracts. Source:
      `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/active/issues/pendle_venue_onboarding_2026_08_16.md` (the 2 [P2] wiring items + the `pendle_markets`
      config item — the doc's separate P3 "decide archetype venue_universe inclusion" strategy-domain call is
      deferred below, not extracted here). Done when: `DeFiAdapter` dispatches a Pendle operation through
      `PendleConnector` end-to-end and the UAC SIT invariant passes with `pendle` registered.
- [ ] [DATA] P3. **Re-run the LST yields 30-day backfill.**
      Re-run `backfill_lst_yields_30day.sh` for the 2026-04-20..2026-05-19 window (or a re-scoped clean window if
      that one has since gone stale) — now unblocked on the manifest-consolidator/HYPERLIQUID `perp_funding` side
      per the doc's own 2026-08-14 re-check. Repo: market-tick-data-service. Source:
      `defi_satellite_ao_dispatch_batch14_2026_08_16.md` extracted from
      `plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md`
      todo 3. Done when: the backfill run completes and the target window's `lst_yields`/`lst_native_rates` rows are
      manifest-verified.

## Not extracted this batch — non-batchable taxonomy

**Operator-gated** (a genuine judgment/design call, or a credential only a human holds — no amount of re-triage
resolves these; re-check after the next operator ruling or credential grant):

- `dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md` — `[OPERATOR] P1` relaunch-vs-wait decision
  for the 2022-12-13 partial-data date (a business call on data completeness vs relaunch cost, distinct from the
  BACKEND item extracted above).
- `exec_tenderly_2026_08_15.md` — `[OPERATOR] P3` provision a Tenderly fork RPC endpoint + API key (credential-ask;
  once obtained, `un-skip test_tenderly_fork_full_cycle` becomes a normal bounded todo for a future batch).
- `pendle_venue_onboarding_2026_08_16.md` — P3 "decide archetype `venue_universe` inclusion" for Pendle — a
  strategy-domain judgment call on which archetypes should include the venue, distinct from the wiring items
  extracted above.
- `defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md` — `[OPERATOR] P2` decide fate
  (delete-as-dead-code vs wire-a-real-consumer) for 6 unused LST adapter classes — reaffirmed "not bounded" by the
  doc's own prior round9-reclassify audit; no new information changes that this round.
- `onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md` — `[DESIGN] P1` decide + implement the
  `staking_apy_bps` annualization-noise fix — multiple defensible smoothing/clamp approaches exist (rolling window,
  winsorize, historical cap) and the value feeds a live liquidation-risk-adjacent calc (`CARRY_STAKED_BASIS`'s
  `net_carry`, per the source doc's own 2026-08-09 retag to P1) — a methodology call, not a mechanical fix; picking
  wrong risks a real financial-calc regression.

**Time/dependency-gated** (re-check next round — the actual trigger condition may have cleared by then):

- `uac_kamino_venue_reachability_cascade_regression_2026_08_15.md` — **RESOLVED + ARCHIVED 2026-08-18** (`/plan-reconcile
  uac_master`): `kamino`/`morpho` left the reachability baseline `unified-api-contracts@9b982906` (2026-08-17); moved to
  `/plans/archive/issues/uac_kamino_venue_reachability_cascade_regression_2026_08_15.md`. No further re-check needed.

**Too-large-or-risky-for-a-batch-todo** (a live, multi-phase, actively-gated doc in its own right — needs its own
dedicated pass, not a single extracted todo):

- `solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md` — itself a `status: draft` multi-section plan
  with active economics (§A) and schema-mapping (§A.3) gates still open as of 2026-08-15, plus registry/
  execution-service/instruments-service/strategy-service/docs sections gated behind those two — folding any single
  item into this batch risks colliding with its own in-flight gate state.

**Excluded — explicit operator ruling, not tracked in this Deferred section** (nothing to re-check; the operator
already decided):

- `karak_decommission_2026_08_16.md` — orphaned (nothing currently covers its ~30 open items), but the doc's own
  Progress Log records an explicit operator "Human" plan-destination ruling (`assigned_vm: NA`, "Not yet executed —
  scoped only, per operator's 'Human' plan-destination ruling"). Per CLAUDE.md's "Plan destination — ASK BEFORE
  CREATING" HARD RULE, this doc's own disposition already answers that question for its content; drafting any of its
  items into an AO batch would override a standing operator decision. Reported in the Phase 2 audit report, not
  drafted here.

## Progress Log

- 2026-08-16 (scheduled `ag_closeout_auditor`, tranche=defi, slot 19, dispatch agt-952290 — `/ag-closeout-audit
  defi` Phase 3): drafted `status: draft` per the skill's safety rail — awaiting operator approval to flip `active`.
  8 conflict-clear todos extracted from 8 of the run's 14 `orphaned_never_touched` docs; 5 operator-gated + 1
  time-gated + 1 too-large-or-risky deferred with citations; 1 further orphan (`karak_decommission`) excluded
  entirely per a standing explicit operator ruling. Paired with
  `defi_satellite_ao_dispatch_batch14_2026_08_16_finalize.md` (`status: active`, gated via `depends_on` +
  `gate_on_depends: true`) in the same turn.
- **ag-closeout-audit 2026-08-21 (defi tranche, Phase 2 sweep)**: re-verified per the parked doc's "2 batch plans
  stuck status: draft for days" hygiene flag. Content still current (spot-checked against source docs' own
  2026-08-20/21 Progress Log entries, no drift found). Per this doc's own Progress Log entry above, flipping
  `status: draft` -> `active` is explicitly an operator decision, not a hygiene fix — not made here. Flagging for
  operator attention: this batch has sat `status: draft` since 2026-08-16 (5 days) despite being fully
  conflict-checked and ready to dispatch.
