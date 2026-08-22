---
doc_type: issue
title: na-eligibility-audit defi tranche 2026-08-16 — consolidated operator questions, credential asks, and carry-forward MISCLASSIFIED_LIKELY_AO_ELIGIBLE list
summary: >-
  Phase 1b consolidation artifact for the 2026-08-16 /na-eligibility-audit defi run (52 docs classified, 40
  defi-owned). Not a work item itself — a batchable index of the DISTINCT operator-decision and credential asks
  found across the tranche, plus the MISCLASSIFIED_LIKELY_AO_ELIGIBLE items still genuinely unresolved after this
  run's own RECLASSIFY pass (several were independently resolved this run and are excluded, noted below).
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, na-eligibility-audit, operator-questions, credential-ask, misclassified-carry-forward]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-16
last_updated: 2026-08-17
# was: defi_master (epic-assignment audit 2026-08-19) -- doc is a na-eligibility-audit
parent_epic: plan_hygiene_master
  # Phase 1b consolidation run report (operator-questions index + MISCLASSIFIED carry-forward list) over the defi
  # tranche, not defi asset-group content itself -- same class as plan_reconciler_findings_cefi_2026_08_16.md's
  # already-corrected retag
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  /na-eligibility-audit defi (2026-08-16, dispatch agt-354c08, slot 27) — Phase 1b consolidation across all 52
  classified docs (40 defi-owned + 12 report-only from other tranches).
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
  ]
---

> **SUPERSEDED 2026-08-17** by
> [`na_eligibility_audit_defi_blocks_2026_08_17.md`](/plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_17.md)
> — that doc carries the fresh Phase-1b consolidation for today's run, including this doc's still-genuinely-open
> carry-forward items re-assessed. Kept here (not archived) as the historical record for this specific run; archival
> deferred to a dedicated hygiene pass.

# na-eligibility-audit defi tranche 2026-08-16 — blocks + carry-forward index

## Operator questions (deduped by distinct ask, not one row per doc)

1. **Elysium delivery decisions (9 distinct asks, one doc)** —
   `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`: carry-archetype attestations, real risk
   thresholds for `carry_staked_basis.yaml`, ClearLoop modelling (explicit vs opaque-behind-Copper), a falsifiable
   "does everything we need" checklist for strategy-service, disclosure-repo inventory scope, transfer mechanism
   (snapshot/mirror/time-boxed grant), accompanying documentation scope, SLA reissue/side-letter for the 30-day
   term, commercial/IP treatment of client-contributed research. Operator-driven, in-progress; not batchable into
   an AO todo per this doc's own governing HARD RULE (no client-artefact content without operator escalation).
2. **DeFi leverage archetypes health-factor fix shape** —
   `defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`: pick (a) thin in-process/client-callable
   path into `DeFiHealthAggregator`/`positions_health`, or (b) a shared helper — blocks the P0 fix + the P2
   mode-aware-dispatch design.
2b. **DeFi adapter unused-LST-family fate** — `defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md`:
    delete-as-dead-code vs wire-a-real-consumer for 6 unused LST adapter classes (RenzoAdapter/PufferAdapter/
    RocketPoolAdapter/SolblazeAdapter/LidoAdapter/EtherFiAdapter). Reaffirmed unbounded on prior rounds too.
3. **DeFi migration-log operator items (3, one doc)** — `defi_migration_audit_log_2026_07_24.md`: fold 3 orphan
   data_types into dedicated buckets (superseded by the retired-dedicated-bucket-architecture finding — likely
   moot, needs a scoping re-read before dispatch), resolve the aggregator-routes bucket target before its 9th
   migrator spec is ever `--apply`'d, delete the 4 empty `*-test-*` DeFi buckets (destructive, sign-off required).
4. **Balancer historical backfill decision** — `defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md`:
   backfill historical BALANCER `dex_pool_state` days with corrected `tvl_usd`/`volume_usd`/`fees_usd`/
   `fee_rate_bps` values, or accept the gap.
5. **Pendle venue-universe inclusion** — `pendle_venue_onboarding_2026_08_16.md`: which strategy archetypes should
   include Pendle (currently absent from all `venue_universe`s) — a strategy-domain call, distinct from the
   wiring items `defi_satellite_ao_dispatch_batch14_2026_08_16.md` already extracted.
6. **DP-VM-001 relaunch-vs-wait** — `dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md`: relaunch
   vs accept-partial-data for the 2022-12-13 MDPS candle coverage gap (a business call on completeness vs cost).
7. **Data-correctness sign-off** — `data_completion_defi_2026_07_15.md` G4: promote-to-live-wallet HUMAN-ONLY
   hard-stop (standing, expected).
8. **Physical zero-row absence-marker parquets** — `defi_consolidated_closeout_2026_07_18.md`: decide whether DeFi
   writers should stop emitting them (architecture call).
9. **Non-defi-owned, reported only** (cefi/cross-cutting tranches own these — surfaced here because this run's
   hunters also read them per the multi-tranche membership overlap): reconciliation cadence for 58 remaining
   findings (`adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`); governance-parameters
   poller wiring (`defi_adapter_dead_code_audit_2026_07_24.md`); liquidation-candidate feed feature-naming +
   3-repo scoping (`defi_catalog_engine_config_key_contract_drift_2026_07_23.md`); live catalogue-provider wiring
   for DEFI/TRADFI/PREDICTION (`uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`); 2 unresolved producer
   classifications (`dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`); MDPS fleet-monitor cron re-enable +
   historical scope (`mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`, cefi-owned).

## Credential/access asks (2)

- **Tenderly fork RPC + API key** (`exec_tenderly_2026_08_15.md`) — unblocks `test_tenderly_fork_full_cycle`;
  already noted by `defi_satellite_ao_dispatch_batch14_2026_08_16.md`'s Deferred section as credential-gated.
- **TARDIS_API_KEY** (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`, cefi-owned) — needed to verify OKX
  options wiring end-to-end.

## MISCLASSIFIED_LIKELY_AO_ELIGIBLE — carry-forward for the NEXT defi run only (already-resolved items excluded)

Per the skill's close-the-loop rule, every `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` tag from this run is a mandatory
Phase-1 input for the next `/na-eligibility-audit defi` run. **Excluded from the list below because this run
already resolved them** (independently promoted to a full RECLASSIFY verdict, then either applied or found
covered by `defi_satellite_ao_dispatch_batch14_2026_08_16.md`): the `defi_dex_pool_density_drop_...` census, the
`defi_lst_yields_backfill_...` re-run, the `mtds_qg_red_morpho_...` URL fix, the
`instruments_service_defi_golden_red_...` --asset-group scoping, and `defi_collateral_sizing_...`'s codex-doc-update
(→ `defi_satellite_ao_dispatch_batch15_2026_08_16.md`).

**New finding this run**: `pendle_venue_onboarding_2026_08_16.md`'s 2 MISCLASSIFIED items ("wire PendleConnector
into DeFiAdapter's dispatch table", "add pendle to DEFI_VENUE_TO_CONNECTOR_CLASS/DEFI_VENUE_TO_GATE_MARKER") are
ALSO already covered verbatim by `defi_satellite_ao_dispatch_batch14_2026_08_16.md` todo 7 — not applied here
(the source doc's own hunter did not promote it to a doc-level RECLASSIFY verdict this run, so no citation marker
was written on the source doc itself). The next run should add a citation marker on `pendle_venue_onboarding_2026_08_16.md`
pointing at batch14, same treatment as the 4 docs above.

Still genuinely open, for the next run to re-assess against the primary RECLASSIFY bar:

- `defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`: fix the misleading
  `_process_health_factor()` docstring (`features-service/.../orchestrator.py:621-623`) — likely bounded/mechanical.
- `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (cefi-owned): update a mockup tooltip
  explanation.
- `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` (cefi-owned, 1 item remaining): re-derive the "four
  preemptions" narrative from raw logs. **CORRECTED 2026-08-17 (plan_reconciler)**: the other 2 originally-listed
  items — migrating `RelaunchStalledVm`'s budget to `ShardedState`, and the watchdog's swallowed pip-install
  failures — are both DONE (`deployment-service@6f2f8e02bf`, QG green before ship; verified live via
  `git show 6f2f8e02bf:scripts/recovery/relaunch_stalled_vm.py | grep -c ShardedState` = 4), per that source doc's
  own later Progress Log content which this carry-forward list hadn't picked up.
- `solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md`: auto-escalate repeat-skip tasks to a
  durable park after N repeats.
- `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` (9 items): deliberately NOT promoted —
  see this doc's own dated marker; the client-SLA/HTML-artefact operator-escalation HARD RULE argues for keeping
  these in the operator-supervised NA context even though individually they read bounded.
- `lst_rate_honest_coverage_2026_07_21.md`: regenerate catalogue + expected universe (`build_instrument_catalogue.py`
  + `enumerate_expected_universe.py` v2).
- `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned) and
  `instruments_docs_audit_outstanding_items_2026_07_08.md` (cefi-owned): already covered by
  `defi_satellite_ao_dispatch_batch14_2026_08_16.md` (former) or independently RECLASSIFY_SPLIT-eligible (latter)
  per this run's own hunters — owning tranche's job to apply, reported not actioned here.
- `defi_migration_audit_log_2026_07_24.md` (2 items, lines ~284/627): already carried forward via this run's own
  dated marker on that doc directly (SOURCE_PRIORITY Solana mis-attribution items — precondition text needs
  re-verification against the retired-dedicated-bucket-architecture finding before a confident extraction).
- `defi_consolidated_closeout_2026_07_18.md`: wire remaining zero-capture protocols (Solana ORCA/RAYDIUM swap
  indexer) — held under the doc's own frontmatter `depends_on`+`gate_on_depends` gate regardless.

## Progress Log

- **2026-08-16 (na-eligibility-audit, defi tranche, dispatch agt-354c08)**: drafted as the Phase 1b consolidation
  artifact for this run's 52-doc classification pass (40 defi-owned). See
  `defi_consolidated_closeout_2026_07_18.md` for the tranche's own AG closeout tracker.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-21 (dedup verification pass)**: attempted to formalize the doc's own prose `SUPERSEDED 2026-08-17` banner
  into `status: superseded` frontmatter — reverted: `check_terminal_status_archived.py` (pre-commit `plan-hygiene`
  hook) treats `status: superseded` as unconditionally TERMINAL for an issue doc and requires it to already be
  `git mv`'d to `plans/archive/`, which contradicts this doc's own banner ("Kept here, not archived... archival
  deferred to a dedicated hygiene pass"). No open `- [ ]` todos exist in this doc either way (Phase 1b consolidation
  report, not checkbox-tracked) — nothing for the dedup counter to gain from the frontmatter change regardless.
  Flagging for archive instead (see FLAG-FOR-ARCHIVE note): content-superseded, 0 open todos, successor confirmed
  present and `status: open` (active) — an operator/hygiene-pass archival (not a self-archive here, per this session's
  scope) would let `status: superseded` land cleanly alongside the `git mv`.
