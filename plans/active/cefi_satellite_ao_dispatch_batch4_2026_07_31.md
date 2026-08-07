---
doc_type: plan
title: CeFi satellite AO batch 4 — iterative-drain extraction over the batch3 orphan residual
summary: >-
  Fourth AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-07-31 (scheduled autonomous
  dispatch, tranche=cefi). Phase 0 re-derived the covering-plan set via `generate_ag_closeout_audit_candidates.py` (101
  cefi-tagged AG-primary docs total; 14 real covering docs; 30 "never cited in any covering doc" near-certain orphan
  candidates prioritized for full Phase 1 deep-read per the pre-filter's own design — the 71 already cited somewhere or
  self-dispatched were not individually re-read this run). Phase 1 classified all 30 via a Workflow (one agent per doc,
  all 16 covering docs incl. batch3 + its finalize passed as context): 2 archivable_now, 6 exclude_cross_cutting
  (mistagged or primarily another AG's/cross-cutting concern), 22 orphaned_never_touched (10 of which are AO-eligible
  bounded work, 12 are genuinely operator-gated/design/research judgment calls per the dispatch-scope-eligibility test).
  Phase 3 conflict-checked all 10 AO-eligible candidates against batch3's own todos + Deferred sections (zero overlap)
  and against each other (zero file collisions); 7 cleared into todos below, 3 parked in Deferred with their blocking
  class named (one genuine cross-tranche conflict, one operator-gated step, one too-large/risky-for-a-batch-todo bundle
  needing delete-safety verification this run could not complete).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    deployment-service,
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-4, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-07"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.7
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-31 (scheduled autonomous dispatch, agent-orchestrator slot 4, tranche=cefi) —
  Phase 0 used `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche cefi` for the covering-doc +
  never-cited candidate pre-filter, Phase 1 ran a `Workflow` (30 parallel agents, one per never-cited candidate, retried
  5 that errored/returned placeholder output on first pass), Phase 3 conflict-checked every AO-eligible candidate
  against batch3's todos/Deferred sections and against each other before drafting.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
---

# CeFi satellite AO batch 4 — iterative-drain extraction

> **Status: active — operator-approved 2026-08-06, dispatching.** Per CLAUDE.md's plan-destination HARD RULE and the
> ag-closeout-audit skill's autonomous-mode guidance, a skill-drafted AO batch is never auto-flipped to `active`. This
> run was a scheduled autonomous dispatch (no operator present), so the flip is explicitly reserved for operator review.
> Flip this frontmatter's `status` to `active` only after that review.

> **Cross-todo file-collision check: PASS.** The 7 todos touch, respectively: (1) a market-tick-data-service audit
> script + `market-data-processing-service` verification scope; (2) a `gcloud storage ls` check (read-only) + checkbox
> edits in two other docs (`infra_capture_and_devops_leftovers_2026_07_06.md`,
> `issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md`); (3) `unified-trading-library`'s
> `DeploymentsRegistry.get()` module + `deployment-service`'s `reap_stale()` sweep; (4) `unified-trading-library`'s
> `providers/gcp.py` (`_GCS_RETRY`, `list_blobs()`) — same repo as todo 3 but a different module/file, no overlap; (5)
> `issues/legacy_bucket_dual_write_decommission_2026_07_24.md` doc edit + a new one-off MTDS manifest-comparison script;
> (6) MTDS's Tardis per-symbol runner (byte-budget admission control) + a `deployment-service` launcher-script audit
> (cefi-scoped items only — the doc's sports-scoped item 3 is explicitly excluded, see Deferred); (7) MTDS's writer
> stamping `batch_tardis` on non-Tardis venues — a different MTDS module than todo 6's runner/launcher work. Safe to
> dispatch concurrently.

## Todos

- [x] ✅ [SCRIPT] P1. **Extend BYBIT futures_chain shape-2 duplicate verification to the full audited scope — DONE
      `market-tick-data-service@1a32b6e7`.** Full-scope audit run 2026-08-06 (slot 13) across all 546 scope days
      (2023-04-05 → 2025-09-23), 1,114 flat objects. Results: 490 duplicate (44%), 290 not_duplicate (26%), 334
      no_counterpart (30%). Audit parquet:
      `_index/audit/bybit_futures_chain_shape2_duplicate_verify_2026_07_13.parquet`. Source doc
      `issues/bybit_futures_chain_write_shape_2026_07_13.md` P1 flipped, Progress Log updated. The 5-day sample's "all
      duplicates" was a sampling artifact; 56% of shape-2 objects carry unique/orphan data.

- [x] ✅ [DATA] P2. **Re-check ASTER + spot-check 2 other venues for post-relaunch live data landing.** Run the cited
      `gcloud storage ls gs://market-data-tick-cefi-prd-central-element-323112/pipeline_mode=live_aster/...` check for
      day=2026-07-30 (well past the 13:30Z UTC threshold as of today). If rows landed: flip
      `infra_capture_and_devops_leftovers_2026_07_06.md`'s verification-half checkbox and archive
      `issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md`, both citing this check. If rows did NOT
      land: file a fresh investigation, do not silently re-park. Then spot-check HYPERLIQUID and BINANCE-FUTURES the
      same way (read-only `gcloud storage ls`, no writes/deletes). Source:
      `/plans/archive/2026_08/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md`. **Done when**: all 3
      venues checked, dependent-doc checkboxes flipped or a new bug filed, with the exact `gcloud` output cited as
      evidence. — **DONE 2026-08-07 (slot 12)**: all 3 venues checked with exact output — ASTER (`live_aster`),
      HYPERLIQUID (`live_hyperliquid`), BINANCE-FUTURES (`live_binance`) all return **zero objects** at the cited
      `raw_tick_data/.../pipeline_mode=live_*` path for day=2026-07-30 + 08-05 + 08-06
      (`ERROR: ... matched no objects`), and zero `live_*` anywhere in the tick bucket (only `batch_*` modes). **Rows
      did NOT land → fresh investigation filed (not re-parked)**:
      `plans/active/issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md`. Root cause:
      capture + event-log WARM tier are healthy (30,486 cefi warm objects flowing to
      `central-element-323112-events/live-events/warm/cefi/*`); the cited `raw_tick_data/live_*` path is a retired
      legacy surface; the real bug is the **cold-tier `live-event-log-compactor` OOM** (512Mi, killed on the
      `(cefi,     book_snapshot_5)` shard with 1,497 warm files, failing daily since 2026-08-01 →
      `live-events/cold/cefi/**` empty). Source-doc todos 1-2 flipped citing this run (infra plan's ASTER checkbox
      intentionally NOT flipped — its "live_aster rows landing daily" gate now reads against the warm/cold event-log
      surface per the new issue doc's P2 todo). New bug has 3 actionable todos (compactor OOM fix, cold backfill,
      legacy-path doc retiement).

- [x] ✅ [BACKEND] P2. **Widen `DeploymentsRegistry.get()`'s except clause + investigate the false `vm_not_running`
      reap.** In `unified-trading-library`, degrade-to-None on real `google.api_core` `NotFound`/`Forbidden`/404
      (mirroring the already-shipped `_read_true_exit_code` idiom), with a regression test. Separately, investigate why
      `deployment-service`'s `reap_stale()` sweep excluded a genuinely-RUNNING VM from `running_vm_names` at
      2026-07-31T05:46:53Z (Finding 3) — fix + test, or confirm unreproducible one-off with cited evidence. Source:
      `issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md`. **Done when**:
      both fixes ship with regression tests and QG green, or the reap finding is confirmed unreproducible with cited
      evidence and the source doc's checkboxes are flipped accordingly. — **SHIPPED**:
      `unified-trading-library@89eabac2` (widen `get()` to real-GCS `NotFound`/`Forbidden`/404 via `exc_name`
      string-match idiom + regression test `test_get_falls_through_to_archive_on_real_gcs_not_found` with a
      `google.api_core.exceptions.NotFound`-raising storage fake) + `deployment-service@4ee514e` (root cause:
      `_list_running_vms()` collapsed a GCE list-API failure/timeout into `[]` → `reap_stale(running_vm_names={})` read
      as "no VMs running" → every stale-heartbeat active entry reaped `vm_not_running`; fix returns `None` on
      census-unavailable → caller passes `running_vm_names=None` → heartbeat-age-only fallback; regression tests
      `test_list_running_vms_returns_none_on_timeout` +
      `test_main_exit_code_mode_census_unavailable_no_false_vm_not_running_reap`). Both QG green (UTL Pass-1 verified
      `89eabac2`; deployment-service Pass-1 GREEN 220s, sentinel `4ee514e`), both verified on
      `origin/live-defi-rollout`. Source-doc items 1-2 flipped. Sibling finding (deployment-api's two `reap_stale()`
      callers share the empty-set bug) filed `issues/deployment_api_reaper_empty_set_over_reap_sibling_2026_08_06.md`.

- [x] ✅ [BACKEND] P2. **Widen `unified-trading-library`'s `_GCS_RETRY` predicate for connection-level transient errors
      — DONE unified-trading-library@f135d4fd8.** `_GCS_RETRY` now uses the GCS SDK's `DEFAULT_RETRY` predicate
      (429/503/5xx + ConnectionError/SSLError/ProtocolError/timeouts) via `DEFAULT_RETRY.with_deadline(600.0)` — the
      prior 429/503-only predicate dropped exactly the connection errors behind shard 13's SSL-EOF/connection-reset
      death; `GCSStorageClient.list_blobs()` gained `timeout=600` for defense-in-depth. Regression tests assert
      ConnectionResetError / urllib3 SSLError / ProtocolError are retried and a non-retryable ValueError propagates
      immediately. QG green (sentinel `f135d4fd8`), 35/35 cloud_interface unit tests pass. Source doc
      `issues/cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md` checkbox flipped
      citing this run.

- [ ] [DATA] P2. **Legacy-bucket 3-part reconciliation bundle.** (a) Update
      `issues/legacy_bucket_dual_write_decommission_2026_07_24.md` lines 123-154 to reflect that cefi's legacy bucket is
      already deleted (bounded doc edit). (b) Check for any additional cefi legacy backup beyond the ~136MB snapshot
      already found (bounded investigation, read-only). (c) Run a proper CF-11 normalization-aware comparison between
      the pre-migration snapshot manifest and the current `-prd` manifest in market-tick-data-service (the false-phantom
      bug that previously blocked this is confirmed fixed). Source:
      `issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`. **Done when**: all 3 sub-items complete, the
      CF-11 comparison result is recorded, and the source doc's 3 open checkboxes are flipped citing this run.

- [ ] [DATA] P2. **CEFI-scoped items from the mtds backfill-VM memory-hang investigation.** Three of this doc's four
      open items are cefi-scoped (the fourth, retained-memory root-cause in the sports `odds_api` download path, is
      explicitly SPORTS-scoped and excluded here — leave for the sports tranche): (i) wire real byte-budget admission
      control (`max_in_flight_bytes`/`estimated_bytes`) into the CEFI Tardis per-symbol runner in
      market-tick-data-service; (ii) audit every other `launch-mtds-*-backfill-vm.sh` launcher in deployment-service for
      the same `e2-standard-4` under-provisioned default; (iii) consider an adaptive/smaller default `--chunk-size` for
      recent-history chunks. Source: `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`. **Done when**: all
      3 cefi-scoped items ship with QG green, and the source doc's corresponding checkboxes are flipped citing this run
      (leave the sports-scoped 4th item untouched for its own tranche).

- [ ] [DIAG] P2. **Find + fix the WRITER stamping `batch_tardis` on non-Tardis on-chain CeFi venues.** Root-cause and
      fix the writer-side bug in market-tick-data-service that stamps `pipeline_mode=batch_tardis` on
      EXTENDED-STARKNET/LIGHTER-ZKSYNC/PACIFICA-SOLANA objects that were never captured via Tardis. This is a code-only
      investigation + fix — it does NOT include the 2 prod-GCS lane re-partitions or the quarantine registration from
      the same source doc (both deferred below; the re-partitions need de-dup MERGE safety-verification this run could
      not complete, and quarantine registration has already been twice-ruled human-only). Source:
      `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` (partial — item 4 of 4 only). **Done when**:
      the writer bug is root-caused, fixed, QG green, and the source doc's item 4 closure action is checked off citing
      the fix (items 1-3 stay open, see that doc's own Deferred note here).

## Deferred — BLOCKED-OPERATOR-DECISION (a genuine conflict, parked not guessed)

- **`issues/estate_orphan_assessment_2026_07_21.md` todo 6 (checkpoint/batch `record_cells()` calls in
  `backfill_orphan_class_e.py --apply`) — contested boundedness across three tranches.** cefi's 2026-07-30
  na-eligibility-audit ruled KEEP-NA ("correctness-sensitive... not a rushed patch"); defi's independent 2026-07-30 pass
  ruled RECLASSIFY ("bounded... safe cut-point spelled out in-doc"); sports conceded boundedness but declined ownership.
  The integrator reverted a contested auto-merged flip back to NA, leaving an explicit unresolved
  "Operator/next-toucher: rule on todo 6's boundedness" note in the source doc (line 549). Not drafted here — this is a
  genuine cross-tranche disagreement on the SAME todo's AO-eligibility, not a bounded item this run can resolve by
  evidence alone.

## Deferred — operator-gated

- **`issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`.** Item 1 is explicitly tagged
  `[OPERATOR]` (confirm/trigger a fresh `deployment-api` build+deploy so the live Cloud Run monitor image picks up
  commit `09a2374`, which fixes a cross-asset-group false-paging bug on early SPOT preemptions — done-when is
  machine-checkable, `UPDATE_TIME` after `2026-07-31T08:06:31Z` + a named passing test). Item 2 (relaunch shard 24) is
  gated on item 1 landing. Not drafted here; re-check once the operator confirms the deploy. **Partial re-check
  2026-08-02 (ag-closeout-audit, tranche=cefi, slot 8)**: live
  `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api --include-tags --sort-by=~UPDATE_TIME --limit=1`
  shows the `:latest` tag's `UPDATE_TIME=2026-08-02T15:23:00`, clearing the first sub-condition (after
  `2026-07-31T08:06:31Z`). The second sub-condition (`test_sweep_early_preemption_no_marker_falls_back_to_op_checker`
  confirmed passing on that specific build) was NOT verified this run — confirming it requires checking the deployed
  build's test provenance, not just the image timestamp. Still gated pending that second confirmation; not drafted as a
  batch7 candidate yet.

## Deferred — too-large-or-risky-for-a-batch-todo

- **`issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` items 1-3 (of 4).** Items 1-2 are prod-GCS lane
  re-partitions (EXTENDED-STARKNET and LIGHTER-ZKSYNC batch_tardis→their real pipeline_mode) requiring de-dup MERGE
  semantics against what the source doc's own prior audit calls "a live split-brain" — this needs a fresh
  `gcs_bucket_soft_delete_retention_seconds()` reversibility check + live-state re-verification this run could not
  complete safely from a Phase-1 doc read alone (CLAUDE.md's delete-safety HARD RULE, path (c)). Item 3 (register
  PACIFICA-SOLANA in the fail-hard quarantine set) has already been twice-ruled human/NA by independent audits
  (`cefi_4surface_migration_execution_log_2026_07_24.md`'s own 2026-07-30 na-eligibility-audit note, and
  `cefi_consolidated_native_ao_extract_2026_07_25.md` lines 375-378: "kept human, not drafted... needs human
  disambiguation") — not re-litigated here. Needs its own dedicated session with delete-safety verification, not a batch
  slot. Item 4 (writer-source fix) is drafted above; items 1-3 stay open in the source doc.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated via the companion
`cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md` (`depends_on` + `gate_on_depends: true`), mirroring the
batch1/batch2/batch3 finalize pattern.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this batch's
  finalize plan executes.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded-vs-judgment-call test applied to every Phase-1/Phase-3 verdict above.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  this batch's Phase 3 ran before drafting.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3a — the reversibility bar the too-large-or-risky
  Deferred item above did not clear this run.

## Progress Log

- **context-scout 2026-08-07**: populated context_scope (4 entries) — the companion finalize gate, the batch-naming +
  dispatch-scope-eligibility codex SSOTs already cited in this doc's own "Codex SSOTs" section above, and the parent
  cefi consolidated-closeout hub. Genuinely code-free per this skill's dispatch-batch-coordinator exemption — every open
  todo already carries its own inline `Source:` pointer to the actual issue doc it targets.
