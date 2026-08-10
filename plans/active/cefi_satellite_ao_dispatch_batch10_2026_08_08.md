---
doc_type: plan
title: CeFi satellite AO batch 10 — full-corpus closeout-completeness re-audit
summary: >-
  Tenth AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-08-08 (scheduled autonomous
  dispatch, tranche=cefi, slot 8, dispatch agt-6bc9c4). Unlike batch9 (a narrow 5-doc "never-cited + linkage-gap delta"
  run), this run did a FULL Phase 0.3 corpus sweep via `generate_ag_closeout_audit_candidates.py --tranche cefi`: 68
  AG-primary candidates (8 covering docs: consolidated closeout, 4-surface migration log, deribit-bundle verification
  pair, batch9 + finalize (still active, not yet done), track2 pair — batches 1-8 + track7/misc-audits/migration-cutover
  children are archived/done, no longer covering). Phase 0.3's Orthogonality HARD CHECK found + fixed 2 genuine
  single-AG-mistagged-as-dual-AG docs this run (`cefi_ml_directional_continuous_live_2026_06_20.md` and
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`, both `[cefi, defi]` → `[cefi]`, parent_epic:cefi_master
  confirms cefi ownership, zero genuine DeFi content in either — both now correctly included in this run's deep audit).
  23 candidates were deterministically excluded (genuine peer-AG marker, 3+ AGs or a different epic's mistag not cefi's
  to fix). 45 were deep-audited via a `Workflow` (one agent per doc, all 8 covering docs passed as context; 2 agents
  needed a manual foreground retry after StructuredOutput failures, all 45 landed). Verdicts: 32 orphaned_never_touched,
  6 orphaned_partial_coverage (38 orphaned total — this tranche's residual backlog is real and larger than recent
  batches because this is the first FULL re-sweep in several batches, not a narrower delta), 4
  archivable_after_planned_work (already fully claimed by batch9/track2's own open todos), 2 archivable_now (all-[x],
  but both carry `locked_by: live-defi-rollout` — archival needs a human unlock, NOT performed by this run), 1
  exclude_cross_cutting (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` — cefi portion fully resolved,
  residual is genuinely cross-AG infra). Phase 3 conflict-checked all 7 initially-AO-eligible candidates against the
  full covering set — found ONE genuine conflict (`deribit_combo_perpetual_partition_move_2026_07_21.md`'s `--apply`
  step is explicitly operator-gated per `cefi_4surface_migration_execution_log_2026_07_24.md`'s Deferred item 7 + its
  own /autonomous DELTA ruling — reclassified operator_gated, NOT drafted here) — 6 todos below, zero further conflicts.
  The remaining 32 non-batchable orphaned docs are in the Deferred sections by taxonomy (19 operator_gated, 6
  human_only, 3 conflict_gated, 4 time_gated).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-trading-pm,
    deployment-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-api-contracts,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-10, satellite-docs, iterative-drain, full-corpus-resweep]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch9_2026_08_07.md,
    /plans/active/cefi_satellite_ao_dispatch_batch9_2026_08_07_finalize.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md,
    /plans/archive/2026_08/issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md,
    /plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-08-08 (scheduled autonomous dispatch, agent-orchestrator slot 8, dispatch
  agt-6bc9c4, tranche=cefi). Phase 0 used `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche cefi`
  (68 members, 8 covering, full corpus sweep — not a delta run) + `check_ag_closeout_linkage.py` (2 cefi-tagged
  linkage-orphans, both pre-existing/resolved by the deep audit's own verdicts). Phase 1 ran a `Workflow` (45 agents
  over the full deep-audit candidate set), each reading its doc in full (incl. dated sections) and grepping all 8
  covering docs for citations. Phase 3 conflict-checked every initially-AO-eligible candidate against the full covering
  set via targeted greps on each candidate's stated target files.
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch9_2026_08_07.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# CeFi satellite AO batch 10 — full-corpus closeout-completeness re-audit

> **Status: ACTIVE — operator-approved 2026-08-08.** A fresh conflict-check re-verified Phase 3's original clearance
> before dispatch (see the Progress Log entry below). The paired finalize plan was already `active` from the start —
> `gate_on_depends: true` machine-holds it until this batch's todos are done, no double gate (2026-07-30 ruling).
>
> **Cross-todo file-collision check: PASS.** The 6 todos touch, respectively: (1) this plan's own source doc's status
> text (no code); (2) a read-only investigation + the source issue doc's Findings section (no code unless a merge is
> recommended, which stays out-of-scope per the todo text); (3) GCS run.log read + the source issue doc's Relaunch todo
> text; (4) `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py` + the 2 source issue docs' checkbox
> text; (5) `deployment-service` (VM heartbeat status-field logic) + `market-tick-data-service`'s `aster_book_liq_ws.py`
> (`_publish_boundary_event`); (6) `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`. No file
> is edited by more than one todo.
>
> **Every claim below was re-verified against live corpus/code state on 2026-08-08** by the Phase-1 agents (each read
> its target doc in full, including dated sections, and confirmed zero covering-doc citations via direct greps against
> all 8 covering docs).

## Todos

- [x] ✅ [DOC] P1. **DONE 2026-08-08.** Read the archived gate doc's conclusion in full: CF-11's normalization-aware
      comparison found 59,488/96,338 eligible legacy cells not covered in current `-prd`, decomposing entirely into
      pre-canonical-era 2019+ data, pre-CF-11 empty-itype/dtype ghost rows, and already-tracked Era-B chain-form rows —
      no residual gap. Flipped Phase C in `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` to
      DONE-BY-FAIT-ACCOMPLI citing CF-11's actual conclusion (option (a) — no genuine residual gap found on closer
      reading). Source: `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (Phase C).
- [x] ✅ **DONE 2026-08-09.** [DATA] P2. **Read-only investigate the ~1104 genuine HYPERLIQUID(660)/ASTER(444)
      wire-vs-canonical filename collisions on the 6 flagged dates** (2025-11-01, 2025-11-02, 2026-01-01, 2026-01-02,
      2026-01-03, 2026-07-11) named in `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding
      8/10. Sample-compare row counts / capture-time ranges / tick content per colliding pair to determine whether one
      capture is a strict subset of the other. **Audit only — do NOT rename/delete/merge anything.** Source:
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` (Finding 8/10). **Done when**: each sampled
      pair is classified subset-confirmed (recommend a safe merge path, but do not execute it) or
      genuinely-distinct-content (recommend permanent leave-as-is), with results appended to the issue doc's Findings —
      or the sample proves inconclusive and is escalated to the operator for a decision, with the evidence attached.
      **DONE**: re-ran the shipped script's own discovery/resolve logic (read-only, no downloads) for the 6 dates × 2
      venues — live population is now 522 candidates (not 1104; `2025-11-01`/`02` show zero today, a corpus-drift fact
      flagged in the finding). Sample-compared 26 pairs (all 9 HYPERLIQUID candidates + a diverse ASTER sample): **0/26
      are genuinely-distinct content** once `symbol`/`instrument_type`-casing/`available_at` label-convention columns
      are normalized — 23 identical_content, 3 subset_confirmed (old wire-form ⊆ new canonical, ASTER `trades` truncated
      at exactly 1000 rows). Recommends a safe automated fix (extend `_confirm_would_patch_duplicate`'s exclusion set)
      rather than the prior "leave as-is forever" default. Evidence:
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 11 (2026-08-09), same commit as
      this checkbox flip.
- [x] ✅ [DATA] P2. **Check the terminal state of VM `mdps-backfill-cefi-20260807-130321` and re-run the per-cell
      symbol-count bundle audit** against the 84 targeted (6 BYBIT + 6 DERIBIT day) cells named in
      `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md`. If the VM was preempted again, relaunch (SPOT
      default, per the vm-launcher runbook); if it completed, confirm the 112-cell OK state directly against
      GCS/manifest evidence. Source: `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` (Relaunch todo).
      **Done when**: the doc's Relaunch todo cites either a passing 84+-cell audit result with fresh evidence, or a
      documented further-relaunch action with a new VM id and launch timestamp — not just a stale RUNNING timestamp.
      **DONE**: VM confirmed preempted at T+1h46m (gcloud op `systemevent-1786114166437`). Ran a fresh 126-path per-cell
      audit — BYBIT still PARTIAL on all 6 target days. Root-caused + fixed the reason 2 relaunches never actually fixed
      it: `--force` was silently dropped when MDPS spawns per-date subprocesses
      (`market-data-processing-service@e9f9819`, see `issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`
      for the cross-cutting writeup). A 3rd VM (`mdps-backfill-cefi-20260808-095136`, launched 2026-08-08T08:57:08Z,
      pre-fix, same wrong full-range scope, confirmed alive) is currently running — documented + a new per-day-scoped
      relaunch todo added to the Track-7 doc for once it terminates. Evidence:
      `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` § "2026-08-08 84-cell audit" +
      unified-trading-pm@<sha>, market-data-processing-service@e9f9819.
- [x] ✅ [SCRIPT] P3. **DONE 2026-08-10 (slot-32)** — **Remove `BINANCE-DELIVERY` from `VENUES_BY_ASSET_GROUP["cefi"]`**
      in `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py` to stop the daily zombie cron (704
      wasted `attempted_failed`/`empty_confirmed` rows/day). The venue was deliberately excluded from MVP scope by
      operator decision #3 (2026-06-27, `mvp_scope.py` v10) — this todo does not reopen that decision, it only stops the
      forward/cron pipeline from continuing to iterate a venue that's already MVP-excluded (code wiring, symbol_rules,
      and the Tardis adapter all stay intact for a future MVP re-add). Source:
      `issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md` (P3 BINANCE-DELIVERY item) +
      `issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md` (duplicate todo, keep both docs' checkboxes
      in sync). **Done when**: the venue is removed from the cefi iteration list, `quality-gates.sh` is green, and a
      fresh manifest check on the next cron cycle confirms no new BINANCE-DELIVERY `attempted_failed` rows are written.
      **DONE**: venue removed from `VENUES_BY_ASSET_GROUP["cefi"]` AND `tardis_to_venue`/`all_tardis_exchanges` (the
      forward-poll's actual iteration source — the group removal alone would not stop the attempts, bare-OKX
      precedent) + `VENUE_DATA_TYPE_CAPABILITIES`; QG green (12,637 passed); wiring kept for re-enable. Evidence:
      `unified-api-contracts@56db28e6` (verified ancestor of `origin/live-defi-rollout`, current tip) — source issue doc
      archived 2026-08-10 (`plans/archive/2026_08/issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md`).
- [ ] [INFRA] P3. **Fix the LONG_LIVED_LIVE VM heartbeat status field so it transitions past `"starting"`** once boot
      completes, and root-cause + fix the `_publish_boundary_event` exception for `ASTER:PERPETUAL:1000LUNC-USDT@LIN`
      seen after `_record_empty_window` succeeds (both from
      `issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`'s Open Questions). Source:
      `issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`. **Done when**: the heartbeat
      status field reflects real VM state post-boot (verified via a live VM's heartbeat blob) AND the
      `_publish_boundary_event` exception is root-caused with either a fix shipped or a documented non-issue verdict,
      both with `quality-gates.sh` green.
- [ ] [SCRIPT] P3. **Fix the confusing `FORCE="${FORCE:-250}"` default** in
      `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (line ~61) to
      `FORCE="${FORCE:-false}"` — a copy-paste artifact from the adjacent `DRY_RUN` default; harmless today (only the
      literal string `"true"` triggers `VM_FORCE=true` downstream) but reads as a bug. **Safe-idempotent justification
      (no `[OPERATOR]` tag needed)**: this todo edits ONE default-value line in the script's own source and does not
      execute/launch the script — no VM is started, no GCS object is touched, by this todo. Source:
      `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (line 718, flagged as an unclaimed candidate in
      the 2026-08-07 na-eligibility-audit entry). **Done when**: the default reads `false`, existing tests (if any
      target this script) still pass, `quality-gates.sh --no-fix` is green, and the source doc's P3 checkbox is flipped
      citing the commit.

## Deferred — BLOCKED-OPERATOR-DECISION (conflict, needs explicit ruling)

- **`issues/deribit_combo_perpetual_partition_move_2026_07_21.md`** — the `--apply` DERIBIT combo partition-move
  (15,119-row data MOVE) was initially flagged AO-eligible by this run's Phase 1, but Phase 3's conflict-check found a
  standing, dated, explicit operator ruling that overrides it: `cefi_4surface_migration_execution_log_2026_07_24.md`
  Deferred-work item 7 states "The `--apply` partition-move still needs explicit operator sign-off... do not start that
  without a SEPARATE future review," reaffirmed in that same doc's `/autonomous` DELTA (operator explicitly scoped
  "Proceed with P1 prep now" as covering ONLY the prep work, not the apply step). **Needs the operator to run that
  separate future review before this can be dispatched.** Not drafted here.

## Deferred — operator-gated

- **`crypto_alpha_research_2026_07_24.md`** — 23 remaining items, dominated by operator trading-judgment (book-sizing
  decisions, which legs/weights, whether to ship the short sleeve). Not a worker-determinable outcome.
- **`issues/bybit_futures_chain_write_shape_2026_07_13.md`** — delete-or-not for 490 confirmed-duplicate objects, gated
  on an operator decision per the workspace's GCS-delete-safety protocol.
- **`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`** — G1/G4 explicitly require operator ruling/sign-off; not
  worker-executable.
- **`issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`** — item 1 is `[OPERATOR]`-tagged
  by its own author (no safe deterministic rebuild command identified for a live UI-serving prod Cloud Run service).
- **`issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md`** — items 1/3 remain (item 2 is
  already covered by an active in-flight batch9 todo); item 1 is `[OPERATOR]`-tagged (deployment-api redeploy
  confirmation), item 3 is time-gated (serial-console capture, see below — listed once, under operator here since it's
  the doc's dominant remaining gate).
- **`issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`** — remaining item(s)
  need an operator decision on catalogue-orphan disposition; not a checkable-fact audit.
- **`issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`** — a Tardis credential/billing entitlement
  upgrade, or alternatively an operator judgment call accepting reduced scope; neither is worker-bounded.
- **`issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md`** — the shipped fix's residual todo
  is an operator sign-off/verification step, not further code work.
- **`issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md`** — **RESOLVED + ARCHIVED 2026-08-09**: re-verified
  the HYPERLIQUID VMs are no longer running (live `aws ec2 describe-instances` returns zero results, consistent with
  both multi-year backfills having completed since the 08-04 confirmation); closed and moved to
  `/plans/archive/2026_08/issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md`.
- **`issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`** — near-fully [x] (946 lines, ~50 todos almost all done); the
  residual prose item is operator-judgment-gated, not a fresh worker task.
- **`issues/fail_hard_canonical_enforcement_design_2026_07_20.md`** — `[DESIGN] P1` item is an undecided
  architecture/design call (reconciling two id-derivation paths, a new column-value gate, a new on-disk convention).
- **`/plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md`** — RESOLVED + archived
  2026-08-09 (superseded this listing; see that doc's finalize plan). The `[DECISION]` was ruled by the operator
  2026-08-08 ("start it, conditionally"); the follow-on completeness gate is now tracked in
  `/plans/active/issues/cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete_2026_08_08.md`.
- **`issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md`** — `[OPERATOR]`-tagged, explicitly needs a
  decision among 3 named options before implementation.
- **`issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`** — all 3 items human-gated (operator's own
  exchange-side API-key login; the other 2 are undecided design/priority calls).
- **`issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`** — both items gated per two
  independent dated na-eligibility-audit entries (07-30, 07-08 reaffirmed).
- **`issues/upbit_cefi_data_gap_may_2026_2026_08_04.md`** — `[OPERATOR]`/`BLOCKED-CREDENTIALS`: needs a Tardis
  full-access API key, a human/operator action per the external-data-always-available rule.
- **`l2_book_microstructure_capture_2026_07_13.md`** — todo 5 needs an operator authorization decision (greenlight a new
  MDPS column-pipeline extension plan); todo 7's remaining core work is similarly judgment-gated.
- **`issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`** — 3 items are prod-GCS re-partition/merge
  mutations against a documented live split-brain; delete-safety-protocol-gated, human/operator supervision required.

## Deferred — human-only (design/judgment, no operator ruling will make it bounded)

- **`cefi_ml_directional_continuous_live_2026_06_20.md`** — (1) the ≥7-continuous-day live-capital cutover gate is a
  named PERMANENT human-only hard-stop (wallet keys, kill-switch arming for real capital); (2) the 2-year config-grid
  backtest run is an operator-scheduling action (~8-12h VM run); (3) the "volume as a first-class feature" research item
  is deferred pending an untracked predecessor.
- **`aster_and_cefi_rolling_adv_feature_2026_07_21.md`** — Phase 3's core item needs "a design conversation on where in
  the strategy pipeline this cap applies and what the % ceiling should be" (explicitly not yet scoped); the stretch item
  is an explicit "consider whether" judgment call.
- **`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`** — 11 of 22 open items are `[DESIGN]`/`[RESEARCH]`
  strategy-archetype and hedge-venue judgment calls (equity basis/dispersion sizing, hedge-venue choice).
- **`issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`** — an undecided architecture choice (range-loop vs.
  cache); 5 independent na-eligibility-audit passes (07-30 through 08-07) all reach the same KEEP-NA verdict.
- **`issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`** — 2 self-declared
  design/maintainer-judgment calls (choosing between two engineering approaches for the schema contract).
- **`issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27.md`** — the root-cause item is open-ended
  investigation into an untraced adapter/code path with no stated done-when beyond "find the bug."

## Deferred — conflict-gated (already claimed by another active doc — re-check next batch)

- **`data_completion_cefi_2026_07_15.md`** — remaining ground is the parent M-1 coordinator hub's own in-flight content
  (`data_completion_to_100_all_ag_2026_06_21.md`); drafting here would race that active claim.
- **`issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md`** — the
  shard-16-class OOM root-cause + shard 42/18 relaunch-budget decisions are already claimed by two other active,
  non-covering-set sibling issue docs.
- **`issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`** — the underlying outcome (relaunch N named
  dead shards, verify, delete a script) is itself bounded, but a new batch todo would conflict with an already-active
  claim on the same ground — re-check whether that claim has shipped/superseded before batch11.

## Deferred — time-gated

- **`issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`** — P3 work is gated behind an unmet AO
  backlog condition (`cefi-recapture-sweep-complete`); re-check once that condition flips.
- **`issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`** — structurally a
  bounded infra task, but this doc has already dispatched several rounds of the identical VM-relaunch shape this
  session; re-check its own latest dated section before drafting a round-4 todo (avoid redundant relaunch churn).
- **`issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`** — gated on a genuine Track-2
  (or any Tardis-venue) backfill VM actually being live at check time; not forceable.
- **`issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`** — textbook elapsed-real-time gate on the
  genuinely-running 2026-08-06 ON_DEMAND VM (~2769-day span, 6th attempt after 5 prior deaths); re-check on terminal
  state, do not force.

## Archivable — reported, NOT actioned this run (locked, needs human unlock)

- **`issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`** — all 3 todos `[x]` with dated evidence, zero remaining
  prose work. Carries `locked_by: live-defi-rollout` — per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, a locked plan's archival needs a human unlock;
  this run does not unlock autonomously. **Ask the operator**: "cefi_coinbase_cde_urdi_zero_records is fully done —
  unlock for archival?"
- **`issues/cefi_universe_capture_rule_2026_06_23.md`** — every checkbox across all sections `[x]` with shipped
  SHAs/prod-verified evidence through 2026-08-05. Same `locked_by: live-defi-rollout` situation — same ask.

## Archivable-after-planned-work (informational — already claimed, no batch action needed)

- **`issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md`** — fully claimed by batch9's todo 1
  (in flight).
- **`issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`** — fully claimed by
  `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`.
- **`issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`** — fully claimed by
  batch9's todo 3 (in flight).
- **`issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md`** — fully claimed by
  batch9's Reconciliation section (carried, re-verified unchanged).

## Cross-tranche / excluded (informational — out of cefi scope, not drafted here)

- **`issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`** — `exclude_cross_cutting`: the original CeFi
  (Tardis) MTDS backfill OOM incident is fully resolved+verified; the residual is genuinely cross-AG infra, not
  cefi-specific. No cefi write.
- **23 candidates deterministically excluded at Phase 0.3** (peer-AG marker present — 18 span 3+ AGs generically, 3 are
  owned by a different tranche via `parent_epic` (`defi_pipeline_e2e_and_coverage_validation` → defi_master,
  `canonical_path_oracle_blind_to_filename_stem` + `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp` →
  infrastructure_master), 1 (`prediction_capture_incident_remediation_2026_07_06.md`) is a genuine cefi+prediction
  cross-contamination bug with ambiguous parent_epic ownership). Full list in this run's Phase 0 output, not repeated
  here to keep this plan under the line cap — see the Progress Log entry below for the pointer.

## Orthogonality fixes shipped this run (informational)

- **`cefi_ml_directional_continuous_live_2026_06_20.md`**: `asset_group` corrected `[cefi, defi]` → `[cefi]` — doc's own
  provenance note says "Distinct from the rules-based DeFi carry family," zero DeFi content, parent_epic:cefi_master.
- **`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`**: `asset_group` corrected `[cefi, defi]` → `[cefi]` —
  100% CeFi content (Binance/OKX/Bybit), the "DEFI" hits were the Binance margin-asset enum value and the
  `live-defi-rollout` branch name, not the DeFi asset group; parent_epic:cefi_master.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — §3 conflict-check protocol this
  batch's Phase 3 ran (shared with `/na-eligibility-audit`); the deribit-combo reclassification above is exactly the
  "resolve by logic, do not draft a competing todo" path this protocol prescribes.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded/checkable test applied to each candidate.
- `plans/PLAN_FORMAT.md` — `status: draft` semantics (this batch dispatched 2026-08-08 on operator approval).
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the locked-plan-archival-needs-human-unlock
  rule applied to the 2 "Archivable — reported, NOT actioned" docs above.

## Progress Log

- **2026-08-08** — drafted by the `/ag-closeout-audit` cefi run (slot 8, dispatch agt-6bc9c4). Full Phase 0.3 corpus
  sweep (68 candidates, first full re-sweep in several batches — batch9 was a narrower delta run), 45 deep-audited via
  Workflow, 38 orphaned total, 6 AO-eligible after Phase 3's conflict-check reclassified 1 candidate
  (`deribit_combo_perpetual_partition_move`) to operator_gated. Full per-doc verdict data (all 68 candidates, including
  the 23 deterministically-excluded list and each orphaned doc's full one-paragraph reasoning) is retained in this run's
  Workflow journal (`wf_0163b57f-8da`, transcript dir under the slot-8 session) — not duplicated into this plan to stay
  under the line cap; cite the journal or re-run `/ag-closeout-audit cefi` for a fresh full accounting.
- **2026-08-08 (re-confirmation pass)** — a second `/ag-closeout-audit cefi` dispatch (slot 13, dispatch agt-2d0648)
  landed for this same tranche the same calendar day. Per the iterative-drain methodology's "re-check before fresh
  triage" step: verified via `git log --since="2026-08-08 01:18:04"` that the only intervening cefi-touching commit is
  the disjoint `/na-eligibility-audit` cefi pass (`1512cf1b7`, 02:09 UTC, a different skill/question over the
  `assigned_vm:NA` population) — its 3 edits (`bybit_futures_chain_write_shape_2026_07_13.md`,
  `fail_hard_canonical_enforcement_design_2026_07_20.md`, `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`)
  leave every one of this batch's Deferred/excluded verdicts above unchanged (still operator-gated / still design-gated
  / still `exclude_cross_cutting` respectively — the new PROGRESS.json-upload todo added to the third doc is genuine
  bounded work but is cross-cutting/infra-owned, not cefi's). Re-ran the Orthogonality HARD CHECK (full 9-tranche peer
  set): 2 `cefi`+`cross-cutting` dual-tag hits found, both `plans/archive/` with `status: complete`/`resolved` — no live
  mistag. Given zero material corpus change, did NOT re-run the 45-agent Phase 1 Workflow (would reproduce this batch's
  own verdicts at full cost) or draft a batch11 — this batch remains the current, correct, not-yet-operator-reviewed
  candidate. **Operational note (not investigated further, out of cefi-tranche scope)**:
  `install-ag-closeout-auditor-timer.sh` documents a per-tranche "already dispatched successfully today" guard
  (`scheduled-job-already-ran.py --list-done-tranches`) meant to stop exactly this same-tranche-same-day re-fire; worth
  a look by whoever owns `ao`-tranche scheduling if the pattern recurs.
- **2026-08-08 (operator approval)**: flipped `status: draft` → `active` after a fresh conflict-check re-verified Phase
  3's original clearance: (a) no `cefi_master` sibling batch drafted after this one exists (batch9 remains the only
  other active cefi batch, already accounted for in this doc's own drafting); (b) no new active
  `parent_epic: cefi_master` claim on any of the 6 todos' target files/mechanisms found; (c)
  `cefi_consolidated_closeout` unchanged since this batch's drafting. `locked_by` unset. **Independently corroborated**:
  the same-day re-confirmation pass immediately above reached the identical zero-material-change conclusion via its own
  independent method (fresh git-log diff since drafting + a full 9-tranche Orthogonality re-check), reinforcing this
  flip's basis. **Two informational, non-blocking findings surfaced by this operator-approval re-check, outside the
  formal 3-surface protocol's scope (cross-`parent_epic`) so not treated as conflicts**: (1) todo 3's target VM
  `mdps-backfill-cefi-20260807-130321` is ALSO named in an open `[SCRIPT] P1` todo in
  `infra_health_audit_findings_fix_2026_08_07.md` (`parent_epic: observability_master`, `assigned_vm: NA`) — that todo's
  payload (verify the launcher's preemption-recovery contract fired, fix fleet-wide if not) is complementary rather than
  duplicative of this todo's payload (relaunch if needed, then run the per-cell audit), and the two are
  order-independent, so left as-is rather than deferred — flagging for visibility only. (2) todo 4's source doc
  `issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md` is itself `assigned_vm: planning`/`status: open`
  (already independently AO-dispatchable), same underlying fix as this todo — the doc's own text already anticipates
  this ("keep both docs' checkboxes in sync"), so not a new conflict, just noting the two-doors-to-one-fix shape
  explicitly. Dispatching.
