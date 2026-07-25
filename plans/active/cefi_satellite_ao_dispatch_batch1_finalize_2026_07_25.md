---
doc_type: plan
title: CeFi satellite AO batch 1 — finalize (reconcile source docs + resolve excluded items + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 33 of that plan's todos are done. Mirrors the tradfi batch1_finalize / prediction batch1_finalize
  pattern (reconcile each of the 21 distinct source docs' checkboxes independently), plus 2 batch1-specific additions:
  re-check the 3 too-large-doc exclusions for whether they are now scoped enough for a batch2 pass, and re-verify the 1
  cross-doc live-conflict exclusion (LATE colliding-venue renames) has actually landed via its own live session before
  spinning it into a fresh todo.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi satellite AO batch 1 — finalize

> **Machine-gated on `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 33 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P2. **Reconcile all 21 distinct source docs' checkboxes.** For each of
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 33 now-done todos: flip the corresponding checkbox/section in
      its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-1 commit(s) that shipped
      it — verify the actual shipped commit exists before citing it. The 21 source docs:
      `aster_and_cefi_rolling_adv_feature_2026_07_21.md`, `data_completion_cefi_2026_07_15.md` (5 todos),
      `issues/aster_mtds_failure_count_regression_2026_07_07.md`,
      `issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`,
      `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`,
      `issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md` (2 todos),
      `issues/bybit_futures_chain_write_shape_2026_07_13.md`,
      `issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`,
      `issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md` (2 todos),
      `issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`,
      `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`,
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md` (3 todos),
      `issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`,
      `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (2 todos),
      `issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md` (3 todos),
      `issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md`,
      `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md` (2 todos),
      `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`,
      `issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`,
      `issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`,
      `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`. For each: after flipping,
      re-check whether it now has 0 open todos remaining. Only flip a doc's `status` to `resolved` if it genuinely
      reaches 0 open todos (checkbox AND prose-form). **Done when**: all 21 source docs' corresponding
      checkboxes/sections are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped
      to `status: resolved`.
- [ ] [REVIEW] P2. **Re-check the 3 too-large-doc exclusions for a batch2 pass.** For each of
      `cefi_4surface_migration_execution_log_2026_07_24.md`,
      `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`, and
      `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` (all flagged
      `doc_too_large_or_risky_for_batch: true` at batch-1 triage time): re-read the doc's current state — has its
      fast-moving live-migration activity (Track 1 dedup / LATE renames / Surface C v2 apply for the first doc; the
      OOM-outage investigation gating the second doc's design fork; the sibling-doc cross-correction for the third doc)
      settled enough that a fresh, precisely-scoped triage pass could now safely extract AO-eligible work? If yes,
      recommend and scope a `cefi_satellite_ao_dispatch_batch2` candidate item per doc with a concrete done-when; if no,
      record why it's still too volatile and re-check again at the next batch cycle. **Done when**: each of the 3 docs
      has an explicit settled-vs-still-volatile verdict recorded, with a scoped batch2 candidate item for any doc found
      settled.
- [ ] [DIAG] P2. **Re-verify the LATE colliding-venue renames exclusion.** Re-read
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` and
      `cefi_4surface_migration_execution_log_2026_07_24.md` for the current state of the Range A/B/C `--apply` LATE
      colliding-venue rename passes (excluded from batch-1 on evidence they were "actively in progress via a live
      human-directed /autonomous session" as of 2026-07-25). If all 3 ranges have landed cleanly (rc=0, zero new
      STOP-ON-SURPRISE collisions beyond the 6 pre-known excluded dates) and the follow-up full-range verification
      dry-run has run, mark this item DONE with the evidence citation and do NOT spin a fresh todo. If the live session
      stalled or was never actually running, extract the original todo (execute the 3 `--apply` passes + final
      verification dry-run) into a new tracked `cefi_satellite_ao_dispatch_batch2` candidate. **Done when**: a
      definitive landed-vs-still-pending verdict for the Range A/B/C migration is recorded with evidence (VM
      run.log/manifest citation), and either the item is marked DONE or a scoped batch2 candidate is created.
- [ ] [DOC] P3. **Archive `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todos 2 and 3
      above should have already resolved the too-large-doc and LATE-renames exclusions — verify none remain untracked) →
      add the archive banner → run the codex-alignment check → grep the corpus for every referrer of
      `cefi_satellite_ao_dispatch_batch1_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
